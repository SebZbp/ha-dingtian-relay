"""Binary sensors: one per Input, plus the diagnostic connectivity sensor."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .board import Board
from .entity import BoardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Board], async_add_entities: AddEntitiesCallback
) -> None:
    board = entry.runtime_data
    async_add_entities([BoardConnectivity(board)])
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


class InputBinarySensor(BoardEntity, BinarySensorEntity):
    def __init__(self, board: Board, number: int) -> None:
        super().__init__(board)
        self._number = number
        self._attr_name = f"Input {number}"
        self._attr_unique_id = f"{board.serial}_input_{number}"

    @property
    def available(self) -> bool:
        return self._board.available

    @property
    def is_on(self) -> bool | None:
        return self._board.input_is_on(self._number)


class BoardConnectivity(BoardEntity, BinarySensorEntity):
    """Stays available when the Board is offline: it is what reports that."""

    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, board: Board) -> None:
        super().__init__(board)
        self._attr_unique_id = f"{board.serial}_connectivity"

    @property
    def is_on(self) -> bool | None:
        return self._board.online
