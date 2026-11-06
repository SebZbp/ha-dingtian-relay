"""A Board shows whether it is online, its network identity and its versions."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
)

BASE = "dingtian/relay47196"


async def _add_board(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain="dingtian",
        unique_id="47196",
        title="Dingtian 47196",
        data={"serial": "47196", "topic_base": BASE},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _publish(hass: HomeAssistant, topic: str, payload: str) -> None:
    async_fire_mqtt_message(hass, f"{BASE}/out/{topic}", payload)
    await hass.async_block_till_done()


def _device(hass: HomeAssistant):
    return dr.async_get(hass).async_get_device(identifiers={("dingtian", "47196")})


async def test_every_entity_follows_the_boards_online_state(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")
    await _publish(hass, "r1", "ON")
    await _publish(hass, "lwt_availability", "online")
    assert hass.states.get("switch.dingtian_47196_output_1").state == "on"

    await _publish(hass, "lwt_availability", "offline")
    assert hass.states.get("switch.dingtian_47196_output_1").state == "unavailable"
    assert hass.states.get("switch.dingtian_47196_output_2").state == "unavailable"
    assert hass.states.get("sensor.dingtian_47196_ip_address").state == "unavailable"

    await _publish(hass, "lwt_availability", "online")
    assert hass.states.get("switch.dingtian_47196_output_1").state == "on"


async def test_connectivity_sensor_shows_online_and_offline(hass, mqtt_mock):
    await _add_board(hass)
    entity_id = "binary_sensor.dingtian_47196_connectivity"

    await _publish(hass, "lwt_availability", "online")
    assert hass.states.get(entity_id).state == "on"
    assert hass.states.get(entity_id).attributes["device_class"] == "connectivity"

    await _publish(hass, "lwt_availability", "offline")
    assert hass.states.get(entity_id).state == "off"

    entry = er.async_get(hass).async_get(entity_id)
    assert entry.entity_category == er.EntityCategory.DIAGNOSTIC


async def test_ip_and_mac_are_diagnostic_sensors(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "ip", "192.168.1.50")
    await _publish(hass, "mac", "aa:bb:cc:dd:ee:ff")

    registry = er.async_get(hass)
    ip = "sensor.dingtian_47196_ip_address"
    mac = "sensor.dingtian_47196_mac_address"
    assert hass.states.get(ip).state == "192.168.1.50"
    assert hass.states.get(mac).state == "aa:bb:cc:dd:ee:ff"
    for entity_id in (ip, mac):
        assert registry.async_get(entity_id).entity_category == er.EntityCategory.DIAGNOSTIC

    await _publish(hass, "ip", "192.168.1.51")
    assert hass.states.get(ip).state == "192.168.1.51"


async def test_device_carries_versions_and_configuration_url(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "hw_version", "3.2")
    await _publish(hass, "sw_version", "1.0.4")
    await _publish(hass, "ip", "192.168.1.50")

    device = _device(hass)
    assert device.hw_version == "3.2"
    assert device.sw_version == "1.0.4"
    assert device.configuration_url == "http://192.168.1.50"
    assert device.serial_number == "47196"


async def test_firmware_change_updates_version_and_keeps_entities(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")
    await _publish(hass, "sw_version", "1.0.4")
    registry = er.async_get(hass)
    before = sorted(e.entity_id for e in registry.entities.values())

    await _publish(hass, "sw_version", "1.1.0")

    assert _device(hass).sw_version == "1.1.0"
    assert sorted(e.entity_id for e in registry.entities.values()) == before
