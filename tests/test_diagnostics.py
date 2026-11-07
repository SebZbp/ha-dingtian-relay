"""A diagnostics download gives everything known about a Board."""
import logging

from homeassistant.setup import async_setup_component

from .test_outputs import BASE, _add_board, _publish


async def _download(hass, hass_client, entry) -> dict:
    assert await async_setup_component(hass, "diagnostics", {})
    client = await hass_client()
    response = await client.get(f"/api/diagnostics/config_entry/{entry.entry_id}")
    assert response.status == 200
    return (await response.json())["data"]


async def test_diagnostics_list_every_topic_with_last_payload_and_counts(
    hass, hass_client, mqtt_mock
):
    entry = await _add_board(hass)
    await _publish(hass, "relay_cnt", "4")
    await _publish(hass, "input_cnt", "2")
    await _publish(hass, "r1", "ON")
    await _publish(hass, "firmware_codename", "x7")

    data = await _download(hass, hass_client, entry)

    assert data["entry"]["data"] == {"serial": "47196", "topic_base": BASE}
    assert data["output_count"] == 4
    assert data["input_count"] == 2
    assert data["topics"]["r1"]["payload"] == "ON"
    assert data["topics"]["firmware_codename"]["payload"] == "x7"
    assert data["topics"]["r1"]["received"]


async def test_unrecognised_topics_and_payloads_are_listed_and_only_debug_logged(
    hass, hass_client, mqtt_mock, caplog
):
    entry = await _add_board(hass)
    caplog.set_level(logging.DEBUG)
    await _publish(hass, "mystery", "42")
    await _publish(hass, "r1", "SIDEWAYS")
    await _publish(hass, "r2", "ON")

    data = await _download(hass, hass_client, entry)

    assert data["unrecognised"] == {"mystery": "42", "r1": "SIDEWAYS"}
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("mystery" in r.getMessage() for r in caplog.records)


async def test_input_count_falls_back_like_output_count(hass, hass_client, mqtt_mock):
    from datetime import timedelta

    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    entry = await _add_board(hass)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()

    data = await _download(hass, hass_client, entry)

    assert data["output_count"] == 8
    assert data["input_count"] == 8


async def test_sn_and_duplicate_json_topics_are_known_not_unrecognised(
    hass, hass_client, mqtt_mock, caplog
):
    entry = await _add_board(hass)
    caplog.set_level(logging.DEBUG)
    await _publish(hass, "sn", "47196")
    await _publish(hass, "relay1", '{"type":"relay"}')
    await _publish(hass, "input3", '{"type":"input"}')

    data = await _download(hass, hass_client, entry)

    assert data["unrecognised"] == {}
    assert data["topics"]["sn"]["payload"] == "47196"
    assert data["topics"]["relay1"]["payload"] == '{"type":"relay"}'
    assert data["topics"]["input3"]["payload"] == '{"type":"input"}'
    assert not [r for r in caplog.records if "ignoring" in r.getMessage()]
