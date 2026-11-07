"""Each Output of a Board is a switch that shows what the Board reports."""
from datetime import timedelta

from unittest.mock import patch

import pytest
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_fire_time_changed,
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


def _output_ids(hass: HomeAssistant) -> list[str]:
    return sorted(s.entity_id for s in hass.states.async_all("switch"))


async def test_board_reporting_four_outputs_gets_four_switches(hass, mqtt_mock):
    await _add_board(hass)

    await _publish(hass, "relay_cnt", "4")

    assert _output_ids(hass) == [
        "switch.dingtian_47196_output_1",
        "switch.dingtian_47196_output_2",
        "switch.dingtian_47196_output_3",
        "switch.dingtian_47196_output_4",
    ]


async def test_switch_is_unknown_until_the_board_publishes_its_state(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")

    assert hass.states.get("switch.dingtian_47196_output_1").state == "unknown"

    await _publish(hass, "r1", "ON")
    await _publish(hass, "r2", "OFF")
    assert hass.states.get("switch.dingtian_47196_output_1").state == "on"
    assert hass.states.get("switch.dingtian_47196_output_2").state == "off"

    await _publish(hass, "r1", "OFF")
    assert hass.states.get("switch.dingtian_47196_output_1").state == "off"


async def _call(hass, service: str, entity_id: str) -> None:
    await hass.services.async_call(
        "switch", service, {"entity_id": entity_id}, blocking=True
    )


async def test_turning_a_switch_on_and_off_commands_the_board(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "4")
    mqtt_mock.async_publish.reset_mock()

    await _call(hass, "turn_on", "switch.dingtian_47196_output_3")
    mqtt_mock.async_publish.assert_called_once_with(f"{BASE}/in/r3", "ON", 0, False)

    mqtt_mock.async_publish.reset_mock()
    await _call(hass, "turn_off", "switch.dingtian_47196_output_3")
    mqtt_mock.async_publish.assert_called_once_with(f"{BASE}/in/r3", "OFF", 0, False)


async def test_switch_shows_the_board_state_not_the_command(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "1")
    await _publish(hass, "r1", "OFF")

    await _call(hass, "turn_on", "switch.dingtian_47196_output_1")

    assert hass.states.get("switch.dingtian_47196_output_1").state == "off"


async def test_json_relay_topics_are_ignored(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")

    await _publish(hass, "relay1", '{"idx":"1","status":"ON"}')
    await _publish(hass, "relay9", '{"idx":"9","status":"ON"}')

    assert hass.states.get("switch.dingtian_47196_output_1").state == "unknown"
    assert len(_output_ids(hass)) == 2


async def test_outputs_have_numbered_names_and_stable_unique_ids(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")

    assert hass.states.get("switch.dingtian_47196_output_2").name == "Dingtian 47196 Output 2"
    registry = er.async_get(hass)
    entity = registry.async_get("switch.dingtian_47196_output_2")
    assert entity.unique_id == "47196_output_2"
    device = dr.async_get(hass).async_get_device(identifiers={("dingtian", "47196")})
    assert entity.device_id == device.id

    registry.async_update_entity(entity.entity_id, name="Lumiere hall")
    await hass.async_block_till_done()
    assert hass.states.get("switch.dingtian_47196_output_2").name.endswith("Lumiere hall")
    assert registry.async_get(entity.entity_id).unique_id == "47196_output_2"


async def test_a_larger_count_later_adds_switches(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")
    await _publish(hass, "r1", "ON")

    await _publish(hass, "relay_cnt", "4")

    assert len(_output_ids(hass)) == 4
    assert hass.states.get("switch.dingtian_47196_output_1").state == "on"


async def test_eight_switches_when_the_count_never_arrives(hass, mqtt_mock, freezer):
    await _add_board(hass)
    assert _output_ids(hass) == []

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(_output_ids(hass)) == 8


async def test_a_count_arriving_after_the_fallback_still_adds_switches(hass, mqtt_mock, freezer):
    await _add_board(hass)
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    await _publish(hass, "relay_cnt", "16")

    assert len(_output_ids(hass)) == 16


@pytest.fixture
def active_subscriptions():
    """Topics currently subscribed through HA's MQTT integration (spy)."""
    active: list[str] = []
    real = mqtt.async_subscribe

    async def spy(hass, topic, *args, **kwargs):
        unsubscribe = await real(hass, topic, *args, **kwargs)
        active.append(topic)

        def remove():
            active.remove(topic)
            unsubscribe()

        return remove

    with patch("homeassistant.components.mqtt.async_subscribe", spy):
        yield active


async def test_reload_does_not_duplicate_subscriptions_and_unload_removes_them(
    hass, mqtt_mock, active_subscriptions
):
    entry = await _add_board(hass)
    assert len(active_subscriptions) == 1

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(active_subscriptions) == 1

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert active_subscriptions == []


async def test_setup_retries_when_mqtt_is_not_available(hass):
    entry = await _add_board(hass)

    assert entry.state is ConfigEntryState.SETUP_RETRY
