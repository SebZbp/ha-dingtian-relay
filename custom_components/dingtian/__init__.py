"""The Dingtian Relay integration: one config entry per Board, over MQTT."""
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .board import Board
from .const import (
    CONF_AREA,
    CONF_SERIAL,
    CONF_TOPIC_BASE,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    PLATFORMS,
)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migration hook. Only VERSION 1 exists so far; later versions migrate here."""
    LOGGER.debug("Entry %s is at version %s", entry.entry_id, entry.version)
    return entry.version == 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Board]) -> bool:
    LOGGER.debug("Setting up entry %s", entry.entry_id)
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT is not available")
    serial = entry.data.get(CONF_SERIAL)
    if serial:
        registry = dr.async_get(hass)
        is_new = registry.async_get_device(identifiers={(DOMAIN, serial)}) is None
        device = registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, serial)},
            manufacturer=MANUFACTURER,
            serial_number=serial,
            name=entry.title,
        )
        # The area chosen on the discovery card applies once; later changes in
        # the device registry are the user's and must survive reloads.
        if is_new and entry.data.get(CONF_AREA):
            registry.async_update_device(device.id, area_id=entry.data[CONF_AREA])
    board = Board(
        hass, serial, entry.data.get(CONF_TOPIC_BASE) or f"dingtian/relay{serial}"
    )
    entry.runtime_data = board
    await board.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[Board]) -> bool:
    LOGGER.debug("Unloading entry %s", entry.entry_id)
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.async_stop()
    return unloaded
