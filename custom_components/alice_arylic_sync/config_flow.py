"""Config flow: pick the Alice and Arylic players in the UI; every tuning
parameter lives in the options flow (the integration's Configure dialog)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALICE_ENTITY,
    CONF_ARYLIC_ENTITIES,
    DEFAULTS,
    DOMAIN,
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
    OPT_STEPS,
    OPT_STOP_FADE_FLOOR,
    OPT_STOP_STEP_DELAY_MS,
    OPT_STOP_STEPS,
    OPT_SYNC_OFFSET,
    OPT_TRACK_URI_PREFIX,
)


def _volume_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=1, step=0.01, mode=selector.NumberSelectorMode.SLIDER
        )
    )


def _number(min_: float, max_: float, step: float, unit: str | None = None) -> selector.NumberSelector:
    config = selector.NumberSelectorConfig(
        min=min_, max=max_, step=step, mode=selector.NumberSelectorMode.BOX
    )
    # unit_of_measurement must be absent (not None) when there is no unit —
    # the selector schema rejects None values.
    if unit is not None:
        config["unit_of_measurement"] = unit
    return selector.NumberSelector(config)


class AliceArylicSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup: choose the players (one or more outputs = multi-room)."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            outputs: list[str] = user_input[CONF_ARYLIC_ENTITIES]
            if not outputs:
                errors["base"] = "no_outputs"
            elif user_input[CONF_ALICE_ENTITY] in outputs:
                errors["base"] = "same_entity"
            elif not self.hass.services.has_service("music_assistant", "play_media"):
                errors["base"] = "music_assistant_missing"
            else:
                unique_id = "__".join(
                    [user_input[CONF_ALICE_ENTITY], *sorted(outputs)]
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=self._make_title(user_input), data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ALICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player")
                ),
                vol.Required(CONF_ARYLIC_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player",
                        integration="music_assistant",
                        multiple=True,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    def _make_title(self, user_input: dict[str, Any]) -> str:
        def name(entity_id: str) -> str:
            state = self.hass.states.get(entity_id)
            return state.name if state else entity_id

        outputs = " + ".join(name(e) for e in user_input[CONF_ARYLIC_ENTITIES])
        return f"{name(user_input[CONF_ALICE_ENTITY])} → {outputs}"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return AliceArylicSyncOptionsFlow()


class AliceArylicSyncOptionsFlow(config_entries.OptionsFlow):
    """All tuning parameters."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = {**DEFAULTS, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(OPT_SYNC_OFFSET, default=current[OPT_SYNC_OFFSET]): _number(
                    -10, 30, 0.1, "s"
                ),
                vol.Required(OPT_HANDOFF_DELAY, default=current[OPT_HANDOFF_DELAY]): _number(
                    0, 600, 1, "s"
                ),
                vol.Required(OPT_STEPS, default=current[OPT_STEPS]): _number(2, 50, 1),
                vol.Required(OPT_HEADSTART_MS, default=current[OPT_HEADSTART_MS]): _number(
                    0, 2000, 10, "ms"
                ),
                vol.Required(OPT_ALICE_GAP_MS, default=current[OPT_ALICE_GAP_MS]): _number(
                    0, 2000, 10, "ms"
                ),
                vol.Required(OPT_ARYLIC_FLOOR, default=current[OPT_ARYLIC_FLOOR]): _volume_selector(),
                vol.Required(OPT_ARYLIC_TARGET, default=current[OPT_ARYLIC_TARGET]): _volume_selector(),
                vol.Required(
                    OPT_ALICE_END_VOLUME, default=current[OPT_ALICE_END_VOLUME]
                ): _volume_selector(),
                vol.Required(
                    OPT_STOP_FADE_FLOOR, default=current[OPT_STOP_FADE_FLOOR]
                ): _volume_selector(),
                vol.Required(
                    OPT_ALICE_RESTORE_VOLUME, default=current[OPT_ALICE_RESTORE_VOLUME]
                ): _volume_selector(),
                vol.Required(OPT_STOP_STEPS, default=current[OPT_STOP_STEPS]): _number(
                    1, 40, 1
                ),
                vol.Required(
                    OPT_STOP_STEP_DELAY_MS, default=current[OPT_STOP_STEP_DELAY_MS]
                ): _number(0, 1000, 10, "ms"),
                vol.Required(
                    OPT_PLAY_WAIT_TIMEOUT, default=current[OPT_PLAY_WAIT_TIMEOUT]
                ): _number(1, 60, 1, "s"),
                vol.Required(
                    OPT_BUFFER_WAIT_TIMEOUT, default=current[OPT_BUFFER_WAIT_TIMEOUT]
                ): _number(0, 30, 1, "s"),
                vol.Required(
                    OPT_REGROUP_EACH_TRACK,
                    default=current[OPT_REGROUP_EACH_TRACK],
                ): selector.BooleanSelector(),
                vol.Required(
                    OPT_SEEK_EACH_OUTPUT,
                    default=current[OPT_SEEK_EACH_OUTPUT],
                ): selector.BooleanSelector(),
                vol.Required(
                    OPT_REDIRECT_VOLUME,
                    default=current[OPT_REDIRECT_VOLUME],
                ): selector.BooleanSelector(),
                vol.Required(
                    OPT_TRACK_URI_PREFIX, default=current[OPT_TRACK_URI_PREFIX]
                ): selector.TextSelector(),
                vol.Required(OPT_MEDIA_TYPE, default=current[OPT_MEDIA_TYPE]): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
