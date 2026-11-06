"""Shared base for every entity of a Board."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .board import Board
from .const import DOMAIN


class BoardEntity(Entity):
    """Belongs to the Board's device and re-renders whenever the Board changes.

    List it before the platform class: ``class X(BoardEntity, SwitchEntity)``.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, board: Board) -> None:
        self._board = board
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, board.serial)})

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))
