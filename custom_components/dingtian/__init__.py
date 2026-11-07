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
    serial = entry.data[CONF_SERIAL]
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
    entry.async_on_unload(
        board.async_add_listener(lambda: _sync_device(hass, entry, board))
    )
    await board.async_start()
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        # Setup failed after the subscription and timer exist: tear them down.
        board.async_stop()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[Board]) -> bool:
    LOGGER.debug("Unloading entry %s", entry.entry_id)
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.async_stop()
    return unloaded


def _sync_device(hass: HomeAssistant, entry: ConfigEntry[Board], board: Board) -> None:
    """Copy the versions and IP the Board published into its device."""
    registry = dr.async_get(hass)
    device = registry.async_get_device(identifiers={(DOMAIN, board.serial)})
    if device is None:
        return
    changes: dict[str, str] = {}
    if board.hw_version and board.hw_version != device.hw_version:
        changes["hw_version"] = board.hw_version
    if board.sw_version and board.sw_version != device.sw_version:
        changes["sw_version"] = board.sw_version
    url = f"http://{board.ip}" if board.ip else None
    if url and url != device.configuration_url:
        changes["configuration_url"] = url
    if changes:
        LOGGER.debug("Board %s: device registry update %s", board.serial, changes)
        registry.async_update_device(device.id, **changes)
