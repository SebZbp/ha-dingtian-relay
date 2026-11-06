"""Output switches: one per Output the Board reports."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    def add_missing_outputs() -> None:
        nonlocal added
        count = board.output_count or 0
        if count > added:
            async_add_entities(
                OutputSwitch(board, number) for number in range(added + 1, count + 1)
            )
            added = count

    add_missing_outputs()
    entry.async_on_unload(board.async_add_listener(add_missing_outputs))


class OutputSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, board: Board, number: int) -> None:
        self._board = board
        self._number = number
        self._attr_name = f"Output {number}"
        self._attr_unique_id = f"{board.serial}_output_{number}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, board.serial)})

    @property
    def is_on(self) -> bool | None:
        return self._board.output_is_on(self._number)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._board.async_set_output(self._number, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._board.async_set_output(self._number, False)
