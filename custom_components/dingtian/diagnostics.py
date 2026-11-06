"""Diagnostics download: everything the integration knows about a Board."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .board import Board


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry[Board]
) -> dict[str, Any]:
    """Entry data, counts, the last payload per topic and what is not recognised.

    The MQTT broker's credentials live in the MQTT entry, which is not part of
    this entry's data, so they are never included.
    """
    board = entry.runtime_data
    return {
        "entry": {
            "title": entry.title,
            "unique_id": entry.unique_id,
            "data": dict(entry.data),
        },
        "output_count": board.output_count,
        "input_count": board.input_count,
        "topics": {
            topic: {"payload": value.payload, "received": value.received.isoformat()}
            for topic, value in sorted(board.topic_values.items())
        },
        "unrecognised": {
            topic: board.topic_values[topic].payload
            for topic in sorted(board.unrecognised)
        },
    }
