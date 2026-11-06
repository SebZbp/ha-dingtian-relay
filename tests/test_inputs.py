"""Each Input of a Board is a binary sensor showing its logical state."""
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .test_outputs import _add_board, _publish


def _input_ids(hass: HomeAssistant) -> list[str]:
    return sorted(s.entity_id for s in hass.states.async_all("binary_sensor"))


async def test_board_reporting_three_inputs_gets_three_binary_sensors(hass, mqtt_mock):
    await _add_board(hass)

    await _publish(hass, "input_cnt", "3")

    assert _input_ids(hass) == [
        "binary_sensor.dingtian_47196_input_1",
        "binary_sensor.dingtian_47196_input_2",
        "binary_sensor.dingtian_47196_input_3",
    ]


async def test_input_is_unknown_until_reported_then_follows_logical_state(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "input_cnt", "2")
    assert hass.states.get("binary_sensor.dingtian_47196_input_1").state == "unknown"

    await _publish(hass, "i1", "ON")
    await _publish(hass, "i2", "OFF")
    assert hass.states.get("binary_sensor.dingtian_47196_input_1").state == "on"
    assert hass.states.get("binary_sensor.dingtian_47196_input_2").state == "off"

    await _publish(hass, "i1", "OFF")
    assert hass.states.get("binary_sensor.dingtian_47196_input_1").state == "off"


async def test_json_input_topics_are_ignored(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "input_cnt", "2")

    await _publish(hass, "input1", '{"idx":"1","status":"HIGH"}')
    await _publish(hass, "input9", '{"idx":"9","status":"HIGH"}')

    assert hass.states.get("binary_sensor.dingtian_47196_input_1").state == "unknown"
    assert len(_input_ids(hass)) == 2


async def test_inputs_have_numbered_names_and_stable_unique_ids(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "input_cnt", "2")

    assert (
        hass.states.get("binary_sensor.dingtian_47196_input_2").name
        == "Dingtian 47196 Input 2"
    )
    entity = er.async_get(hass).async_get("binary_sensor.dingtian_47196_input_2")
    assert entity.unique_id == "47196_input_2"
    device = dr.async_get(hass).async_get_device(identifiers={("dingtian", "47196")})
    assert entity.device_id == device.id


async def test_a_larger_count_later_adds_binary_sensors(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "input_cnt", "2")
    await _publish(hass, "i1", "ON")

    await _publish(hass, "input_cnt", "4")

    assert len(_input_ids(hass)) == 4
    assert hass.states.get("binary_sensor.dingtian_47196_input_1").state == "on"


async def test_eight_binary_sensors_when_the_count_never_arrives(hass, mqtt_mock, freezer):
    await _add_board(hass)
    assert _input_ids(hass) == []

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(_input_ids(hass)) == 8


async def test_a_count_arriving_after_the_fallback_still_adds_binary_sensors(
    hass, mqtt_mock, freezer
):
    await _add_board(hass)
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    await _publish(hass, "input_cnt", "16")

    assert len(_input_ids(hass)) == 16
