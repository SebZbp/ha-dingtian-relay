"""The Dingtian Relay integration: one config entry per Board, over MQTT."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import LOGGER


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.debug("Setting up entry %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.debug("Unloading entry %s", entry.entry_id)
    return True
