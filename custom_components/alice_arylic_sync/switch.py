"""Enable/disable switch for the sync (and a place to see its status)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import AliceArylicConfigEntry
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AliceArylicConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([SyncEnabledSwitch(entry)])


class SyncEnabledSwitch(SwitchEntity, RestoreEntity):
    """Turns the Alice -> Arylic sync on or off without removing the entry."""

    _attr_has_entity_name = True
    _attr_translation_key = "sync_enabled"
    _attr_icon = "mdi:swap-horizontal-bold"

    def __init__(self, entry: AliceArylicConfigEntry) -> None:
        self._controller = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_sync_enabled"
        self._attr_is_on = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="alice-arylic-sync",
            model="Alice ↔ Arylic Smooth Sync",
            configuration_url="https://github.com/OzodbekNormamatov-git/alice-arylic-sync",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"
        self._controller.enabled = bool(self._attr_is_on)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "alice_entity": self._controller.alice_entity,
            "arylic_entities": self._controller.arylic_entities,
            "last_run": self._controller.last_run,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self._controller.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self._controller.enabled = False
        # Also abort a handoff/stop already in flight (matches
        # automation.turn_off semantics, which stops the current run).
        self._controller.async_cancel()
        self.async_write_ha_state()
