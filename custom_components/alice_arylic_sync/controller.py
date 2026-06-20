"""The sync engine: watches the Alice (Yandex Station) player and drives one or
more Arylic (Music Assistant) players — smooth handoff on start, smooth
stop/restore on stop.

Multi-room: when several outputs are configured, they are joined into a Music
Assistant group (leader = the first one) so every room plays the same track in
perfect sync; volume steps go to all outputs in a single service call.

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
    CONF_ARYLIC_ENTITIES,
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
    OPT_REDIRECT_VOLUME,
    OPT_REGROUP_EACH_TRACK,
    OPT_SEEK_EACH_OUTPUT,
    OPT_SKIP_SEEK,
    OPT_STEPS,
    OPT_STOP_CONFIRM_DELAY,
    OPT_STOP_FADE_FLOOR,
    OPT_STOP_STEP_DELAY_MS,
    OPT_STOP_STEPS,
    OPT_SYNC_OFFSET,
    OPT_TRACK_URI_PREFIX,
    STOP_STATES,
)

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL = 0.25

# States in which an output cannot take part in a run (so the leader fails over
# to the next usable output instead of breaking grouping/play/seek for everyone).
UNAVAILABLE_STATES = (None, "unavailable", "unknown")

# MediaPlayerEntityFeature.GROUPING — the supported_features bit a player sets
# when it can be grouped via media_player.join. Read it up front so we can warn
# precisely instead of letting join fail with "not supported by ...".
FEATURE_GROUPING = 524288


def _safe_float(value: Any, default: float) -> float:
    """float() with a default only for None/unconvertible — 0.0 stays 0.0
    (matches the Jinja `| float(default)` filter the blueprints use)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class SyncController:
    """Drives one Alice -> Arylic(s) pair."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.alice_entity: str = entry.data[CONF_ALICE_ENTITY]
        self.arylic_entities: list[str] = list(entry.data[CONF_ARYLIC_ENTITIES])
        # The leader receives play/seek; in a group the members follow it.
        self.leader: str = self.arylic_entities[0]
        self.enabled: bool = True
        self.last_run: str | None = None
        self._unsub: Callable[[], None] | None = None
        self._task: asyncio.Task | None = None
        self._vol_task: asyncio.Task | None = None
        # The last volume WE wrote to Alice, to tell our crossfade writes apart
        # from a user's spoken "louder/quieter".
        self._alice_volume_we_set: float | None = None
        self._last_redirect: float = 0.0
        # The track we last handed off to the outputs. A voice command to the
        # Station drops it out of 'playing' and back (often re-reporting the same
        # track); without this we'd treat that as a fresh start and reset the
        # outputs to floor on every spoken command.
        self._handoff_content_id: str | None = None
        # True only while a smooth_stop sits in its confirm-delay debounce: the
        # stop has not touched any volume yet, so it must NOT block a "louder"
        # redirect spoken during that window.
        self._stop_pending: bool = False

    # ---------- lifecycle ----------

    async def async_start(self) -> None:
        """Start listening to the Alice player."""
        for entity_id in (self.alice_entity, *self.arylic_entities):
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
        if self._vol_task is not None and not self._vol_task.done():
            self._vol_task.cancel()
        self._vol_task = None

    @callback
    def async_cancel(self) -> None:
        """Abort the run in progress (used when the Sync switch turns off).

        Deliberately does NOT forget the handed-off track: the outputs keep
        playing while disabled, so on re-enable the same track is still
        recognised as handed off. Clearing it here would leave it None while the
        outputs play on, and the next voice-command blip would then re-run the
        whole handoff."""
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

    async def _set_volume(self, entity_ids: str | list[str], volume: float) -> None:
        """One service call — multiple outputs change volume in the same step."""
        level = round(min(1.0, max(0.0, volume)), 3)
        await self.hass.services.async_call(
            "media_player",
            "volume_set",
            {"volume_level": level},
            target={"entity_id": entity_ids},
            blocking=True,
        )
        # Remember the volume WE set on Alice so the redirect handler can tell a
        # user's "louder/quieter" apart from our own crossfade writes.
        if entity_ids == self.alice_entity:
            self._alice_volume_we_set = level

    def _available_outputs(self) -> list[str]:
        """Outputs that are not None/unavailable/unknown — the only ones worth
        targeting. Used so one dropped room never aborts a write to the rest."""
        return [
            entity_id
            for entity_id in self.arylic_entities
            if self._state(entity_id) not in UNAVAILABLE_STATES
        ]

    def _effective_leader(self) -> str:
        """The first output that is actually available, so an offline
        arylic_entities[0] does not break grouping/play/seek/pause for every
        room (there was no failover before). Falls back to the configured first
        output when nothing looks available, so behaviour is unchanged when all
        is well."""
        for entity_id in self.arylic_entities:
            if self._state(entity_id) not in UNAVAILABLE_STATES:
                return entity_id
        return self.arylic_entities[0]

    async def _set_outputs_volume(self, volume: float) -> None:
        """Set the same volume on every AVAILABLE output, fault-isolated.

        The crossfade and floor-set used ONE blocking volume_set targeting the
        whole list, so a single unavailable/rejecting output raised and aborted
        the rest of the fade — stranding the good rooms mid-ramp and leaving
        Alice not fully faded. Per-entity gather(return_exceptions=True) keeps a
        bad room from taking the others down; the concurrent calls still land
        together within a step."""
        results = await asyncio.gather(
            *(self._set_volume(entity_id, volume) for entity_id in self._available_outputs()),
            return_exceptions=True,
        )
        failed = [r for r in results if isinstance(r, Exception)]
        if failed:
            _LOGGER.debug("%d output volume write(s) failed this step (continuing)", len(failed))

    def _output_switched(self, entity_id: str, pre_play_content: dict[str, Any]) -> bool:
        """True once an output has moved to the freshly handed-off track: it is
        playing AND either its content id changed from the pre-play snapshot or
        its position reset near the start. Lets the seek wait for a member to
        actually follow the leader instead of passing on a stale 'playing' from
        the previous track. Bounded by the play-wait timeout at the call site, so
        a player that never reports a usable content id simply times out as
        before rather than hanging."""
        if self._state(entity_id) != "playing":
            return False
        if self._attr(entity_id, "media_content_id") != pre_play_content.get(entity_id):
            return True
        return _safe_float(self._attr(entity_id, "media_position"), 999.0) <= 2.0

    def _supports_grouping(self, entity_id: str) -> bool | None:
        """True/False from the GROUPING feature bit, or None when the player
        does not expose supported_features — then we don't pre-judge and let the
        join attempt (and its warn-on-failure path) decide."""
        features = self._attr(entity_id, "supported_features")
        if features is None:
            return None
        try:
            return bool(int(features) & FEATURE_GROUPING)
        except (TypeError, ValueError):
            return None

    async def _ensure_group(self, force: bool = False) -> None:
        """Join all outputs into one Music Assistant group (leader first).

        Skipped when there is a single output or every member is already in
        the leader's group. Members that are unavailable or that explicitly do
        NOT advertise the grouping feature are dropped up front with a precise
        warning (instead of letting join fail or silently parking them). NOTE:
        the join service only raises for leader-side problems — members Music
        Assistant cannot sync are skipped SILENTLY on the server side, so after
        joining we poll group_members and warn about rooms left out."""
        members = [e for e in self.arylic_entities if e != self.leader]
        if not members:
            return
        joinable: list[str] = []
        for member in members:
            if self._state(member) in UNAVAILABLE_STATES:
                _LOGGER.warning("Output %s is unavailable — left out of the group", member)
                continue
            if self._supports_grouping(member) is False:
                _LOGGER.warning(
                    "Output %s does not support grouping (media_player.join) — "
                    "left out of the group; play it through a Music Assistant "
                    "sync group instead",
                    member,
                )
                continue
            joinable.append(member)
        if not joinable:
            return
        current = set(self._attr(self.leader, "group_members") or [])
        if set(joinable) <= current and not force:
            return
        try:
            await self.hass.services.async_call(
                "media_player",
                "join",
                {"group_members": joinable},
                target={"entity_id": self.leader},
                blocking=True,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Could not group %s with %s (the leader rejected the join) — "
                "continuing with the leader only",
                joinable,
                self.leader,
            )
            return
        # Grouping lands asynchronously (protocol sync can take seconds).
        joined = await self._wait_for(
            lambda: set(joinable)
            <= set(self._attr(self.leader, "group_members") or []),
            5.0,
        )
        if not joined:
            grouped = set(self._attr(self.leader, "group_members") or [])
            missing = [e for e in joinable if e not in grouped]
            _LOGGER.warning(
                "Output(s) %s could not be grouped with %s — Music Assistant "
                "skipped them (provider cannot sync with the leader, or the "
                "player is unavailable); those rooms will stay silent. Tip: "
                "create a Universal Group in Music Assistant and select it as "
                "the single output instead",
                missing,
                self.leader,
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

        # Log meaningful transitions only — a playing media_player refreshes
        # media_position roughly once a second, and logging those would bury the
        # state/content/volume changes that actually matter for diagnosis.
        if old is None or (
            old.state != new.state
            or old.attributes.get("media_content_id")
            != new.attributes.get("media_content_id")
            or old.attributes.get("volume_level") != new.attributes.get("volume_level")
        ):
            _LOGGER.debug(
                "alice change: state %s->%s vol %s->%s content %s->%s (handed off: %s)",
                old.state if old else None,
                new.state,
                old.attributes.get("volume_level") if old else None,
                new.attributes.get("volume_level"),
                old.attributes.get("media_content_id") if old else None,
                new.attributes.get("media_content_id"),
                self._handoff_content_id,
            )

        if self._is_volume_redirect(old, new):
            _LOGGER.debug(
                "Volume redirect: alice %s -> %s",
                old.attributes.get("volume_level") if old else None,
                new.attributes.get("volume_level"),
            )
            self._schedule_volume(old, new)
            return

        if self._is_handoff_trigger(old, new):
            _LOGGER.debug("Handoff trigger: %s", new.attributes.get("media_content_id"))
            self._schedule(self._handoff(), "handoff")
        elif self._is_stop_trigger(old, new):
            _LOGGER.debug("Stop trigger: alice %s -> %s", old.state, new.state)
            self._schedule(self._smooth_stop(), "smooth_stop")

    def _is_handoff_trigger(self, old: State | None, new: State) -> bool:
        """Music started or the track changed on Alice.

        Crucially NOT a fresh start: a voice command to the Station ("louder",
        "what's the weather") makes it blip out of 'playing' and back, usually
        re-reporting the SAME track. Re-running the handoff then would slam the
        outputs back to the floor volume and crossfade them up again on every
        spoken word (the reported "outputs drop to 6 then climb to 16, never
        higher" symptom, and Alice briefly audible during the crossfade). So if
        we have already handed off this exact track and the outputs are still
        playing it, treat the (re)entry as a resume, not a new track."""
        if new.state != "playing":
            return False
        if new.attributes.get("media_content_type") != "music":
            return False
        content_id = new.attributes.get("media_content_id")
        if content_id in INVALID_CONTENT_IDS:
            return False
        outputs_playing = any(
            self._state(e) == "playing" for e in self.arylic_entities
        )
        if content_id == self._handoff_content_id and outputs_playing:
            return False
        if old is None or old.state != "playing":
            return True
        return old.attributes.get("media_content_id") != content_id

    def _is_stop_trigger(self, old: State | None, new: State) -> bool:
        """MUSIC stopped on Alice while any output is playing (echoes the
        blueprint conditions: don't react to voice answers/news/alarms ending,
        and don't touch the outputs if none of them is playing)."""
        if old is None or old.state != "playing":
            return False
        if new.state not in STOP_STATES:
            return False
        if old.attributes.get("media_content_type") != "music":
            return False
        return any(self._state(e) == "playing" for e in self.arylic_entities)

    def _music_resumed(self) -> bool:
        """True when Alice is playing music again while an output is still
        playing — used to tell a transient voice-command blip from a real stop,
        both in the stop debounce and partway through the stop fade."""
        alice = self.hass.states.get(self.alice_entity)
        return (
            alice is not None
            and alice.state == "playing"
            and alice.attributes.get("media_content_type") == "music"
            and alice.attributes.get("media_content_id") not in INVALID_CONTENT_IDS
            and any(self._state(e) == "playing" for e in self.arylic_entities)
        )

    # ---------- volume redirect (Alice command -> outputs) ----------

    def _is_volume_redirect(self, old: State | None, new: State) -> bool:
        """True when the user changed Alice's volume while music is handed off
        (Alice muted, outputs playing). Then "louder/quieter" spoken to Alice
        should move the OUTPUTS, not the silent Station."""
        if not bool(self._opt(OPT_REDIRECT_VOLUME)):
            return False
        if old is None or new.state != "playing":
            return False
        # Only in handoff-to-silence setups; in true multi-room (Alice stays
        # audible) a volume change on Alice is genuinely meant for Alice.
        if float(self._opt(OPT_ALICE_END_VOLUME)) > 0.15:
            return False
        if new.attributes.get("media_content_type") != "music":
            return False
        # A handoff or a CONFIRMED stop in progress owns Alice's volume — don't
        # interfere. But a stop still in its confirm-delay debounce
        # (_stop_pending) has not touched anything yet, so a "louder" spoken in
        # that window must still reach the outputs.
        if (
            self._task is not None
            and not self._task.done()
            and not self._stop_pending
        ):
            return False
        # Anti-loop: if a player re-asserts its level right after we snap Alice
        # back, don't ping-pong. Distinct voice commands are >1s apart anyway.
        if time.monotonic() - self._last_redirect < 0.8:
            return False
        if not any(self._state(e) == "playing" for e in self.arylic_entities):
            return False
        old_vol_raw = old.attributes.get("volume_level")
        new_vol_raw = new.attributes.get("volume_level")
        if old_vol_raw is None or new_vol_raw is None:
            return False
        old_vol = _safe_float(old_vol_raw, 0.0)
        new_vol = _safe_float(new_vol_raw, 0.0)
        if abs(new_vol - old_vol) < 0.005:
            return False
        # Ignore the echo of a volume WE just wrote to Alice.
        if (
            self._alice_volume_we_set is not None
            and abs(new_vol - self._alice_volume_we_set) < 0.01
        ):
            return False
        return True

    def _schedule_volume(self, old: State, new: State) -> None:
        if self._vol_task is not None and not self._vol_task.done():
            self._vol_task.cancel()
        self._vol_task = self.entry.async_create_background_task(
            self.hass, self._redirect_volume(old, new), name="alice_arylic_sync volume"
        )

    async def _redirect_volume(self, old: State, new: State) -> None:
        """Apply Alice's volume delta to every output, then snap Alice back to
        its muted handoff level so the Station stays silent."""
        self._last_redirect = time.monotonic()
        try:
            end_volume = float(self._opt(OPT_ALICE_END_VOLUME))
            old_vol = _safe_float(old.attributes.get("volume_level"), 0.0)
            new_vol = _safe_float(new.attributes.get("volume_level"), 0.0)
            delta = new_vol - old_vol
            await asyncio.gather(
                *(
                    self._set_volume(
                        entity_id,
                        _safe_float(self._attr(entity_id, "volume_level"), 0.0) + delta,
                    )
                    for entity_id in self._available_outputs()
                ),
                # One failing output must not cancel the siblings or block the
                # Alice snap-back below (which keeps the Station silent).
                return_exceptions=True,
            )
            await self._set_volume(self.alice_entity, end_volume)
            _LOGGER.debug(
                "Redirected Alice volume %.3f->%.3f (delta %.3f) to outputs %s",
                old_vol,
                new_vol,
                delta,
                self.arylic_entities,
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Volume redirect failed")

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
        # Remember the track we're committing to hand off BEFORE the (blocking,
        # possibly multi-second) play_media, so a voice-command blip landing
        # mid-handoff is recognised as a resume of THIS track, not a re-trigger
        # of the whole handoff. The _is_handoff_trigger guard also requires
        # outputs_playing, so a handoff that never starts the outputs cannot
        # wrongly suppress a later real start.
        self._handoff_content_id = content_id

        floor = float(self._opt(OPT_ARYLIC_FLOOR))
        target = float(self._opt(OPT_ARYLIC_TARGET))
        end_volume = float(self._opt(OPT_ALICE_END_VOLUME))
        steps = max(1, int(self._opt(OPT_STEPS)))
        headstart = int(self._opt(OPT_HEADSTART_MS)) / 1000
        gap = int(self._opt(OPT_ALICE_GAP_MS)) / 1000
        alice_start_volume = _safe_float(alice.attributes.get("volume_level"), 0.5)

        # 0a) Leader failover: pick the effective leader fresh each run as the
        #     first AVAILABLE output, so an offline configured leader
        #     (arylic_entities[0]) no longer breaks grouping/play/seek/pause for
        #     every room. If nothing is available, there is nothing to play to.
        self.leader = self._effective_leader()
        if not self._available_outputs():
            _LOGGER.warning("No Arylic output is available — skipping handoff")
            return

        # 0b) Multi-room: make sure all outputs are in one synced group. Force a
        #    re-join on a cold start (leader not already playing: first play, or
        #    after a stop/pause) and when the user opted to regroup every track.
        #    Music Assistant can quietly loosen a group across a stop while
        #    'group_members' still lists every speaker — that stale state is what
        #    let rooms drift apart on the second track / after replay, because
        #    the old code skipped the re-join.
        leader_cold = self._state(self.leader) != "playing"
        await self._ensure_group(
            force=leader_cold or bool(self._opt(OPT_REGROUP_EACH_TRACK))
        )

        # 1) All outputs to floor volume (fault-isolated), then start the same
        #    track via Music Assistant on the leader (the group follows it).
        #    Snapshot each output's content id FIRST so step 2 can tell when a
        #    member actually switches to the new track (not just stays 'playing'
        #    on the previous one).
        pre_play_content = {
            entity_id: self._attr(entity_id, "media_content_id")
            for entity_id in self.arylic_entities
        }
        await self._set_outputs_volume(floor)
        await self.hass.services.async_call(
            "music_assistant",
            "play_media",
            {
                "media_id": f"{self._opt(OPT_TRACK_URI_PREFIX)}{content_id}",
                "media_type": str(self._opt(OPT_MEDIA_TYPE)),
            },
            target={"entity_id": self.leader},
            blocking=True,
        )

        # 2) Wait until EVERY output has actually SWITCHED to the new track — not
        #    just reports 'playing'. A member still 'playing' the PREVIOUS track
        #    (warm group, track change) would pass a state-only gate instantly,
        #    so the seek would fire before it follows the leader and it lags by
        #    seconds (the "rooms drift" symptom). We detect the switch by the
        #    member's content id changing from the pre-play snapshot, or its
        #    position resetting near 0 (a fresh-cold output that was not playing
        #    changes content id immediately). Bounded by the play-wait timeout;
        #    any output that never switches is logged and left behind, not blocked
        #    on forever.
        if not await self._wait_for(
            lambda: all(self._output_switched(e, pre_play_content) for e in self.arylic_entities),
            float(self._opt(OPT_PLAY_WAIT_TIMEOUT)),
        ):
            stragglers = [
                e for e in self.arylic_entities if not self._output_switched(e, pre_play_content)
            ]
            _LOGGER.debug("Outputs not on the new track before seek (continuing): %s", stragglers)

        # 3+4) Seek to Alice's current second and wait for the player to accept
        #      the new position — UNLESS skip_seek is on. Some Arylic/LinkPlay
        #      firmwares abort the stream on a Music Assistant seek (HA core
        #      #136905: progress resets to 0:00, the stream aborts with code 255
        #      and MA needs a restart). On those, skip the seek entirely and let
        #      the track play from the start, with Sync offset as the only lever.
        if bool(self._opt(OPT_SKIP_SEEK)):
            _LOGGER.debug("Seek skipped (skip_seek enabled) — outputs play from the start")
        else:
            # By default only the leader is seeked and a real Music Assistant sync
            # group follows it. With "seek every output" enabled, all outputs are
            # seeked in one call — for speakers MA cannot sample-sync, where the
            # leader's seek would otherwise not propagate to the others.
            seek_each = bool(self._opt(OPT_SEEK_EACH_OUTPUT))
            seek_targets: str | list[str] = self.arylic_entities if seek_each else self.leader
            pos_updated_before = self._attr(self.leader, "media_position_updated_at")
            seek_target = self._compute_seek_target()
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "media_seek",
                    {"seek_position": seek_target},
                    target={"entity_id": seek_targets},
                    blocking=True,
                )
            except Exception:  # noqa: BLE001 - some players reject seek; carry on unsynced
                _LOGGER.debug("media_seek failed on %s, continuing", seek_targets)

            # Wait until the leader pushes a post-seek position update (it accepted
            # the new position). Some integrations skip updates for small jumps —
            # then the timeout applies. The short sleep below covers re-buffering.
            await self._wait_for(
                lambda: (
                    self._state(self.leader) == "playing"
                    and self._attr(self.leader, "media_position_updated_at")
                    != pos_updated_before
                    and float(self._attr(self.leader, "media_position") or 0)
                    >= seek_target - 2
                ),
                float(self._opt(OPT_BUFFER_WAIT_TIMEOUT)),
            )
        await asyncio.sleep(0.4)

        # 4b) Drift guard + diagnostics: if a room is still seconds away from the
        #     leader, the players are not staying sample-synced. Surface it with
        #     an actionable hint; positions are logged at DEBUG for tuning.
        self._warn_on_drift()

        # 5) Stepped crossfade, outputs leading: each step every AVAILABLE output
        #    goes up together (fault-isolated), head-start pause, then Alice down.
        #    Re-evaluating availability per step means a room that drops out mid
        #    fade is skipped instead of aborting the whole crossfade.
        for i in range(1, steps + 1):
            arylic_vol = min(target, floor + (target - floor) / steps * i)
            await self._set_outputs_volume(arylic_vol)
            await asyncio.sleep(headstart)
            alice_vol = max(end_volume, alice_start_volume - (alice_start_volume - end_volume) / steps * i)
            await self._set_volume(self.alice_entity, alice_vol)
            await asyncio.sleep(gap)

    def _warn_on_drift(self) -> None:
        """Log post-sync positions; warn if any room is >2.5s off the leader."""
        members = [e for e in self.arylic_entities if e != self.leader]
        if not members:
            return
        positions = {
            entity_id: _safe_float(self._attr(entity_id, "media_position"), 0.0)
            for entity_id in self.arylic_entities
        }
        _LOGGER.debug(
            "post-sync leader=%s group_members=%s positions=%s",
            self.leader,
            self._attr(self.leader, "group_members"),
            positions,
        )
        leader_pos = positions[self.leader]
        drifted = [
            entity_id
            for entity_id in members
            if self._state(entity_id) == "playing"
            and abs(positions[entity_id] - leader_pos) > 2.5
        ]
        if drifted:
            _LOGGER.warning(
                "Output(s) %s are >2.5s out of sync with the leader %s. These "
                "players likely cannot be sample-accurately synced by Music "
                "Assistant. Fixes: (1) enable 'Seek every output' in the "
                "integration's Configure dialog, or (2) create ONE Music "
                "Assistant Sync group from these speakers and select that single "
                "group as the output.",
                drifted,
                self.leader,
            )

    def _compute_seek_target(self) -> int:
        pos = float(self._attr(self.alice_entity, "media_position") or 0)
        updated_at = self._attr(self.alice_entity, "media_position_updated_at")
        offset = float(self._opt(OPT_SYNC_OFFSET))
        if updated_at is not None:
            elapsed = (dt_util.utcnow() - updated_at).total_seconds()
            pos += elapsed
        return max(0, int(pos + offset))

    # ---------- smooth stop ----------

    async def _restore_outputs(self, start_volumes: dict[str, float]) -> None:
        """Put every available output back to the volume it had before the stop
        fade — used when music resumes mid-stop so we abort without silencing it.

        Fault-isolated (return_exceptions=True): a single rejecting/unavailable
        room must NOT propagate out, because that would skip the caller's
        'restore outputs, keep the handoff' return and fall through to clearing
        _handoff_content_id and bumping Alice to the restore volume — the exact
        opposite of the intended abort. (The two sibling gathers are already
        fault-isolated; this is the third.)"""
        available = set(self._available_outputs())
        await asyncio.gather(
            *(
                self._set_volume(entity_id, start)
                for entity_id, start in start_volumes.items()
                if entity_id in available
            ),
            return_exceptions=True,
        )

    async def _smooth_stop(self) -> None:
        if not self.enabled:
            return
        # Debounce: a voice command to the Station ("louder", "what's the
        # weather") briefly drops music out of 'playing' and back. Without this,
        # that blip looks like a real stop — we would fade the outputs down and
        # pause them, then the resume would re-run the full handoff (outputs slam
        # to floor and crossfade up, Alice briefly audible) on every spoken word.
        # So wait, then re-check: if music is back and the outputs are still
        # playing, it was a transient blip — leave the handoff untouched.
        confirm_delay = float(self._opt(OPT_STOP_CONFIRM_DELAY))
        if confirm_delay > 0:
            # _stop_pending lets a "louder" redirect through during this window
            # (the stop owns nothing yet). Cleared in finally so a cancel mid-
            # sleep (a new trigger / switch off) cannot strand it True.
            self._stop_pending = True
            try:
                await asyncio.sleep(confirm_delay)
            finally:
                self._stop_pending = False
            if not self.enabled:
                return
            if self._music_resumed():
                _LOGGER.debug(
                    "Stop ignored: music resumed within the confirm delay "
                    "(transient voice-command blip) — handoff kept"
                )
                return

        # Leader failover (same as handoff): use the first available output as
        # the group's pause anchor, so an offline configured leader does not
        # leave the group playing after a stop.
        self.leader = self._effective_leader()

        fade_floor = float(self._opt(OPT_STOP_FADE_FLOOR))
        steps = max(1, int(self._opt(OPT_STOP_STEPS)))
        step_delay = int(self._opt(OPT_STOP_STEP_DELAY_MS)) / 1000
        # Each room keeps its OWN volume in an MA group — fade every output
        # along its own curve, so a room the user turned down never jumps up.
        start_volumes = {
            entity_id: _safe_float(self._attr(entity_id, "volume_level"), 0.35)
            for entity_id in self.arylic_entities
        }

        try:
            # 1) Fade all outputs down to the floor together (per-entity curve,
            #    concurrent within each step so the rooms stay in lockstep).
            for i in range(1, steps + 1):
                # A late blip, or the user replaying the same track, can resume
                # music partway through the fade. Abort: restore the outputs to
                # where they were and keep the handoff, rather than pausing them
                # into silence while Alice plays on.
                if self._music_resumed():
                    await self._restore_outputs(start_volumes)
                    _LOGGER.debug(
                        "Stop aborted mid-fade: music resumed — outputs restored, "
                        "handoff kept"
                    )
                    return
                await asyncio.gather(
                    *(
                        self._set_volume(
                            entity_id,
                            max(fade_floor, start - (start - fade_floor) / steps * i),
                        )
                        for entity_id, start in start_volumes.items()
                    )
                )
                await asyncio.sleep(step_delay)

            # Final guard: music can resume in the gap between the last fade step
            # and the pause — abort the same way rather than silencing it.
            if self._music_resumed():
                await self._restore_outputs(start_volumes)
                _LOGGER.debug(
                    "Stop aborted before pause: music resumed — outputs restored, "
                    "handoff kept"
                )
                return

            # 2) Pause EVERY configured output individually. The leader's pause
            #    covers the MA group, but group_members can be stale-HIGH —
            #    listing a room that has actually left the group, which the
            #    leader's pause then does NOT reach, leaving it playing music
            #    after a "stop" (the classic stale-membership bug). Pausing each
            #    output is idempotent for grouped members and the only way to
            #    guarantee a room that silently dropped out is stopped. One
            #    failing player must not stop the rest.
            to_pause = [self.leader, *(e for e in self.arylic_entities if e != self.leader)]
            for entity_id in to_pause:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "media_pause",
                        {},
                        target={"entity_id": entity_id},
                        blocking=True,
                    )
                except Exception:  # noqa: BLE001
                    _LOGGER.warning("media_pause failed on %s, continuing", entity_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOGGER.exception("Stop fade failed — restoring Alice volume anyway")

        # The stop is confirmed real and the outputs are now paused, so a later
        # play (even of the same track) must re-handoff: forget the handed-off
        # track. Cleared here (after the pause) rather than at the top so a
        # same-track resume mid-fade does not strand this as None while the
        # outputs are still playing.
        self._handoff_content_id = None

        # 3) Restore Alice's volume (always reached unless cancelled).
        await self._set_volume(self.alice_entity, float(self._opt(OPT_ALICE_RESTORE_VOLUME)))
