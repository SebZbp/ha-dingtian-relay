"""All on / All off buttons: one pair per Board."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .board import Board
from .entity import BoardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Board], async_add_entities: AddEntitiesCallback
) -> None:
    board = entry.runtime_data
    async_add_entities(
        [
            AllOutputsButton(board, "all_on", "All on", True),
            AllOutputsButton(board, "all_off", "All off", False),
        ]
    )


class AllOutputsButton(BoardEntity, ButtonEntity):
    def __init__(self, board: Board, key: str, name: str, on: bool) -> None:
        super().__init__(board)
        self._on = on
        self._attr_name = name
        self._attr_unique_id = f"{board.serial}_{key}"

    async def async_press(self) -> None:
        await self._board.async_set_all_outputs(self._on)
