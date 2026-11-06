"""Diagnostic sensors: the Board's IP and MAC address."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .board import Board
from .entity import BoardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Board], async_add_entities: AddEntitiesCallback
) -> None:
    board = entry.runtime_data
    async_add_entities(
        [BoardText(board, "ip", "IP address"), BoardText(board, "mac", "MAC address")]
    )


class BoardText(BoardEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, board: Board, attribute: str, name: str) -> None:
        super().__init__(board)
        self._attribute = attribute
        self._attr_name = name
        self._attr_unique_id = f"{board.serial}_{attribute}"

    @property
    def available(self) -> bool:
        return self._board.available

    @property
    def native_value(self) -> str | None:
        return getattr(self._board, self._attribute)
