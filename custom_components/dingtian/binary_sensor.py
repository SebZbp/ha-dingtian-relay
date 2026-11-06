"""Input binary sensors: one per Input the Board reports."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .board import Board
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Board], async_add_entities: AddEntitiesCallback
) -> None:
    board = entry.runtime_data
    added = 0

    @callback
    def add_missing_inputs() -> None:
        nonlocal added
        count = board.input_count or 0
        if count > added:
            async_add_entities(
                InputBinarySensor(board, number) for number in range(added + 1, count + 1)
            )
            added = count

    add_missing_inputs()
    entry.async_on_unload(board.async_add_listener(add_missing_inputs))


class InputBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, board: Board, number: int) -> None:
        self._board = board
        self._number = number
        self._attr_name = f"Input {number}"
        self._attr_unique_id = f"{board.serial}_input_{number}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, board.serial)})

    @property
    def is_on(self) -> bool | None:
        return self._board.input_is_on(self._number)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))
