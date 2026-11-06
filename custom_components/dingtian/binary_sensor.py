"""Diagnostic connectivity sensor: whether the Board is online."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .board import Board
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Board], async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([BoardConnectivity(entry.runtime_data)])


class BoardConnectivity(BinarySensorEntity):
    """Stays available when the Board is offline: it is what reports that."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, board: Board) -> None:
        self._board = board
        self._attr_unique_id = f"{board.serial}_connectivity"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, board.serial)})

    @property
    def is_on(self) -> bool | None:
        return self._board.online

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))
