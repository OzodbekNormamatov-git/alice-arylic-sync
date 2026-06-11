"""The sync engine: watches the Alice (Yandex Station) player and drives the
Arylic (Music Assistant) player — smooth handoff on start, smooth stop/restore
on stop.

Handoff and stop share ONE task slot: a new trigger in either direction cancels
the run in progress. This deliberately goes beyond the blueprints' per-automation
'mode: restart' — the two separate blueprint automations could run concurrently
and fight over volumes; here a stop cancels a running handoff and vice versa."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ALICE_ENTITY,
    CONF_ARYLIC_ENTITY,
    DEFAULTS,
    INVALID_CONTENT_IDS,
    OPT_ALICE_END_VOLUME,
    OPT_ALICE_GAP_MS,
    OPT_ALICE_RESTORE_VOLUME,
    OPT_ARYLIC_FLOOR,
    OPT_ARYLIC_TARGET,
    OPT_BUFFER_WAIT_TIMEOUT,
    OPT_HANDOFF_DELAY,
    OPT_HEADSTART_MS,
    OPT_MEDIA_TYPE,
    OPT_PLAY_WAIT_TIMEOUT,
    OPT_STEPS,
    OPT_STOP_FADE_FLOOR,
    OPT_STOP_STEP_DELAY_MS,
    OPT_STOP_STEPS,
    OPT_SYNC_OFFSET,
    OPT_TRACK_URI_PREFIX,
    STOP_STATES,
)

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL = 0.25


def _safe_float(value: Any, default: float) -> float:
    """float() with a default only for None/unconvertible — 0.0 stays 0.0
    (matches the Jinja `| float(default)` filter the blueprints use)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class SyncController:
    """Drives one Alice -> Arylic pair."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.alice_entity: str = entry.data[CONF_ALICE_ENTITY]
        self.arylic_entity: str = entry.data[CONF_ARYLIC_ENTITY]
        self.enabled: bool = True
        self.last_run: str | None = None
        self._unsub: Callable[[], None] | None = None
        self._task: asyncio.Task | None = None

    # ---------- lifecycle ----------

    async def async_start(self) -> None:
        """Start listening to the Alice player."""
        for entity_id in (self.alice_entity, self.arylic_entity):
            if self.hass.states.get(entity_id) is None:
                _LOGGER.warning(
                    "Configured entity %s not found — the sync will not work "
                    "until it exists",
                    entity_id,
                )
        self._unsub = async_track_state_change_event(
            self.hass, [self.alice_entity], self._alice_changed
        )

    async def async_shutdown(self) -> None:
        """Stop listening and cancel any run in progress."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._cancel_running()

    def _cancel_running(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None

    @callback
    def async_cancel(self) -> None:
        """Abort the run in progress (used when the Sync switch turns off)."""
        self._cancel_running()

    def _schedule(self, coro: Any, name: str) -> None:
        self._cancel_running()
        self._task = self.entry.async_create_background_task(
            self.hass, self._run(coro, name), name=f"alice_arylic_sync {name}"
        )

    async def _run(self, coro: Any, name: str) -> None:
        try:
            await coro
            self.last_run = name
        except asyncio.CancelledError:
            _LOGGER.debug("%s cancelled (new trigger arrived)", name)
            raise
        except Exception:
            _LOGGER.exception("Error during %s", name)

    # ---------- option / state helpers ----------

    def _opt(self, key: str) -> Any:
        return self.entry.options.get(key, DEFAULTS[key])

    def _state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def _attr(self, entity_id: str, attr: str) -> Any:
        state = self.hass.states.get(entity_id)
        return state.attributes.get(attr) if state else None

    async def _wait_for(self, cond: Callable[[], bool], timeout: float) -> bool:
        """Poll until cond() is true or the timeout passes (never raises)."""
        deadline = time.monotonic() + max(0.0, timeout)
        while time.monotonic() < deadline:
            try:
                if cond():
                    return True
            except Exception:  # noqa: BLE001 - attribute soup must not kill the run
                pass
            await asyncio.sleep(POLL_INTERVAL)
        return False

    async def _set_volume(self, entity_id: str, volume: float) -> None:
        await self.hass.services.async_call(
            "media_player",
            "volume_set",
            {"volume_level": round(min(1.0, max(0.0, volume)), 3)},
            target={"entity_id": entity_id},
            blocking=True,
        )

    # ---------- triggers ----------

    @callback
    def _alice_changed(self, event: Event[EventStateChangedData]) -> None:
        if not self.enabled:
            return
        old: State | None = event.data["old_state"]
        new: State | None = event.data["new_state"]
        if new is None or new.state in ("unknown", "unavailable"):
            return

        if self._is_handoff_trigger(old, new):
            _LOGGER.debug("Handoff trigger: %s", new.attributes.get("media_content_id"))
            self._schedule(self._handoff(), "handoff")
        elif self._is_stop_trigger(old, new):
            _LOGGER.debug("Stop trigger: alice %s -> %s", old.state, new.state)
            self._schedule(self._smooth_stop(), "smooth_stop")

    def _is_handoff_trigger(self, old: State | None, new: State) -> bool:
        """Music started or the track changed on Alice."""
        if new.state != "playing":
            return False
        if new.attributes.get("media_content_type") != "music":
            return False
        content_id = new.attributes.get("media_content_id")
        if content_id in INVALID_CONTENT_IDS:
            return False
        if old is None or old.state != "playing":
            return True
        return old.attributes.get("media_content_id") != content_id

    def _is_stop_trigger(self, old: State | None, new: State) -> bool:
        """MUSIC stopped on Alice while Arylic is playing (echoes the blueprint
        conditions: don't react to voice answers/news/alarms ending, and don't
        touch Arylic if it isn't playing)."""
        if old is None or old.state != "playing":
            return False
        if new.state not in STOP_STATES:
            return False
        if old.attributes.get("media_content_type") != "music":
            return False
        return self._state(self.arylic_entity) == "playing"

    # ---------- handoff (start) ----------

    async def _handoff(self) -> None:
        if not self.enabled:
            return
        delay = float(self._opt(OPT_HANDOFF_DELAY))
        if delay > 0:
            await asyncio.sleep(delay)
            if not self.enabled:
                return

        # Re-validate ALL trigger conditions: with a start delay the content
        # may have changed during the sleep (e.g. music -> voice answer).
        alice = self.hass.states.get(self.alice_entity)
        if alice is None or alice.state != "playing":
            return
        if alice.attributes.get("media_content_type") != "music":
            return
        content_id = alice.attributes.get("media_content_id")
        if content_id in INVALID_CONTENT_IDS:
            return

        floor = float(self._opt(OPT_ARYLIC_FLOOR))
        target = float(self._opt(OPT_ARYLIC_TARGET))
        end_volume = float(self._opt(OPT_ALICE_END_VOLUME))
        steps = max(1, int(self._opt(OPT_STEPS)))
        headstart = int(self._opt(OPT_HEADSTART_MS)) / 1000
        gap = int(self._opt(OPT_ALICE_GAP_MS)) / 1000
        alice_start_volume = _safe_float(alice.attributes.get("volume_level"), 0.5)

        # 1) Arylic to floor volume, start the same track via Music Assistant.
        await self._set_volume(self.arylic_entity, floor)
        await self.hass.services.async_call(
            "music_assistant",
            "play_media",
            {
                "media_id": f"{self._opt(OPT_TRACK_URI_PREFIX)}{content_id}",
                "media_type": str(self._opt(OPT_MEDIA_TYPE)),
            },
            target={"entity_id": self.arylic_entity},
            blocking=True,
        )

        # 2) Wait until Arylic reports playing.
        await self._wait_for(
            lambda: self._state(self.arylic_entity) == "playing",
            float(self._opt(OPT_PLAY_WAIT_TIMEOUT)),
        )

        # 3) Seek Arylic to Alice's current second (+ sync offset, clamped >= 0).
        pos_updated_before = self._attr(self.arylic_entity, "media_position_updated_at")
        seek_target = self._compute_seek_target()
        try:
            await self.hass.services.async_call(
                "media_player",
                "media_seek",
                {"seek_position": seek_target},
                target={"entity_id": self.arylic_entity},
                blocking=True,
            )
        except Exception:  # noqa: BLE001 - some players reject seek; carry on unsynced
            _LOGGER.debug("media_seek failed on %s, continuing", self.arylic_entity)

        # 4) Wait until the player pushes a post-seek position update (it accepted
        #    the new position). Some integrations skip updates for small jumps —
        #    then the timeout applies. The short sleep covers re-buffering.
        await self._wait_for(
            lambda: (
                self._state(self.arylic_entity) == "playing"
                and self._attr(self.arylic_entity, "media_position_updated_at")
                != pos_updated_before
                and float(self._attr(self.arylic_entity, "media_position") or 0)
                >= seek_target - 2
            ),
            float(self._opt(OPT_BUFFER_WAIT_TIMEOUT)),
        )
        await asyncio.sleep(0.4)

        # 5) Stepped crossfade, Arylic leading: each step Arylic up first,
        #    head-start pause, then Alice down.
        for i in range(1, steps + 1):
            arylic_vol = min(target, floor + (target - floor) / steps * i)
            await self._set_volume(self.arylic_entity, arylic_vol)
            await asyncio.sleep(headstart)
            alice_vol = max(end_volume, alice_start_volume - (alice_start_volume - end_volume) / steps * i)
            await self._set_volume(self.alice_entity, alice_vol)
            await asyncio.sleep(gap)

    def _compute_seek_target(self) -> int:
        pos = float(self._attr(self.alice_entity, "media_position") or 0)
        updated_at = self._attr(self.alice_entity, "media_position_updated_at")
        offset = float(self._opt(OPT_SYNC_OFFSET))
        if updated_at is not None:
            elapsed = (dt_util.utcnow() - updated_at).total_seconds()
            pos += elapsed
        return max(0, int(pos + offset))

    # ---------- smooth stop ----------

    async def _smooth_stop(self) -> None:
        if not self.enabled:
            return
        fade_floor = float(self._opt(OPT_STOP_FADE_FLOOR))
        steps = max(1, int(self._opt(OPT_STOP_STEPS)))
        step_delay = int(self._opt(OPT_STOP_STEP_DELAY_MS)) / 1000
        start_volume = _safe_float(self._attr(self.arylic_entity, "volume_level"), 0.35)

        # 1) Fade Arylic down to the floor.
        for i in range(1, steps + 1):
            vol = max(fade_floor, start_volume - (start_volume - fade_floor) / steps * i)
            await self._set_volume(self.arylic_entity, vol)
            await asyncio.sleep(step_delay)

        # 2) Pause Arylic.
        await self.hass.services.async_call(
            "media_player",
            "media_pause",
            {},
            target={"entity_id": self.arylic_entity},
            blocking=True,
        )

        # 3) Restore Alice's volume.
        await self._set_volume(self.alice_entity, float(self._opt(OPT_ALICE_RESTORE_VOLUME)))
