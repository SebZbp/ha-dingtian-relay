"""A Board that publishes its serial on MQTT is offered, ignored or added once."""
from homeassistant.config_entries import SOURCE_IGNORE, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
)


async def _announce(hass: HomeAssistant, serial: str = "47196") -> None:
    async_fire_mqtt_message(hass, f"dingtian/relay{serial}/out/sn", serial)
    await hass.async_block_till_done(wait_background_tasks=True)


def _flows(hass: HomeAssistant):
    return hass.config_entries.flow.async_progress_by_handler("dingtian")


async def test_board_serial_on_mqtt_raises_a_discovery_card(hass, mqtt_mock):
    await _announce(hass)

    [flow] = _flows(hass)
    assert flow["context"]["unique_id"] == "47196"
    result = await hass.config_entries.flow.async_configure(flow["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"]["serial"] == "47196"
    schema = result["data_schema"].schema
    name_key = next(k for k in schema if k == "name")
    assert name_key.default() == "Dingtian 47196"
    assert any(k == "area" for k in schema)


async def test_confirming_creates_entry_and_device_in_chosen_area(hass, mqtt_mock):
    area = ar.async_get(hass).async_create("Technical room")
    await _announce(hass)
    [flow] = _flows(hass)

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {"name": "BP Technique", "area": area.id}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "BP Technique"
    [entry] = hass.config_entries.async_entries("dingtian")
    assert entry.version == 1
    assert entry.unique_id == "47196"
    assert entry.state is ConfigEntryState.LOADED
    device = dr.async_get(hass).async_get_device(identifiers={("dingtian", "47196")})
    assert device.manufacturer == "Dingtian"
    assert device.serial_number == "47196"
    assert device.name == "BP Technique"
    assert device.area_id == area.id


async def test_area_is_optional(hass, mqtt_mock):
    await _announce(hass)
    [flow] = _flows(hass)

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {"name": "Dingtian 47196"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    device = dr.async_get(hass).async_get_device(identifiers={("dingtian", "47196")})
    assert device.area_id is None


async def test_board_already_added_is_not_offered_again(hass, mqtt_mock):
    MockConfigEntry(
        domain="dingtian", unique_id="47196", data={"serial": "47196"}
    ).add_to_hass(hass)

    await _announce(hass)

    assert _flows(hass) == []


async def test_repeated_announcements_keep_a_single_card(hass, mqtt_mock):
    await _announce(hass)
    await _announce(hass)

    assert len(_flows(hass)) == 1


async def test_ignored_board_is_not_offered_until_unignored(hass, mqtt_mock):
    result = await hass.config_entries.flow.async_init(
        "dingtian",
        context={"source": SOURCE_IGNORE},
        data={"unique_id": "47196", "title": "Dingtian 47196"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    await _announce(hass)
    assert _flows(hass) == []

    [ignored] = hass.config_entries.async_entries("dingtian")
    await hass.config_entries.async_remove(ignored.entry_id)
    await hass.async_block_till_done()
    await _announce(hass)
    assert len(_flows(hass)) == 1


async def test_serial_payload_with_whitespace_is_accepted(hass, mqtt_mock):
    async_fire_mqtt_message(hass, "dingtian/relay22333/out/sn", " 22333\n")
    await hass.async_block_till_done()

    [flow] = _flows(hass)
    assert flow["context"]["unique_id"] == "22333"
