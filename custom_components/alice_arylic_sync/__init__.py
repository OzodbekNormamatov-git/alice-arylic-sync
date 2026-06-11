"""Alice <-> Arylic Sync: hand music off from a Yandex Station to an Arylic
speaker (via Music Assistant) with a smooth, stepped crossfade."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import CONF_ALICE_ENTITY, CONF_ARYLIC_ENTITY
from .controller import SyncController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH]

type AliceArylicConfigEntry = ConfigEntry[SyncController]


async def async_setup_entry(hass: HomeAssistant, entry: AliceArylicConfigEntry) -> bool:
    """Set up one Alice -> Arylic pair from a config entry."""
    controller = SyncController(hass, entry)
    entry.runtime_data = controller

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass,
            [entry.data[CONF_ALICE_ENTITY], entry.data[CONF_ARYLIC_ENTITY]],
            _make_registry_listener(hass, entry),
        )
    )

    # Forward platforms FIRST: the switch restores the previous enabled/disabled
    # state in async_added_to_hass, and the Alice listener must not start
    # handing off before that restore lands.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.async_start()
    return True


@callback
def _make_registry_listener(hass: HomeAssistant, entry: AliceArylicConfigEntry):
    """Track entity_id renames/removals of the configured players."""

    @callback
    def _registry_updated(event: Event) -> None:
        data = event.data
        if data["action"] == "remove":
            _LOGGER.warning(
                "Entity %s was removed; the '%s' pair will not work until you "
                "re-add the integration with existing players",
                data["entity_id"],
                entry.title,
            )
            return
        if data["action"] != "update" or "old_entity_id" not in data:
            return
        old_id, new_id = data["old_entity_id"], data["entity_id"]
        new_data = {
            key: (new_id if value == old_id else value)
            for key, value in entry.data.items()
        }
        if new_data == dict(entry.data):
            return
        _LOGGER.info("Entity %s renamed to %s — updating the pair", old_id, new_id)
        # The update listener reloads the entry, rebinding all listeners.
        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            unique_id=f"{new_data[CONF_ALICE_ENTITY]}__{new_data[CONF_ARYLIC_ENTITY]}",
        )

    return _registry_updated


async def _async_update_listener(hass: HomeAssistant, entry: AliceArylicConfigEntry) -> None:
    """Reload the entry when options or entry data change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AliceArylicConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
    return unload_ok
