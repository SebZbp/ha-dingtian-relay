"""All on / All off are buttons that command every Output of a Board at once."""
import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .test_outputs import BASE, _add_board, _publish


def _expected(status: str, count: int) -> str:
    # Same payload the old YAML packages send: one JSON object per Output,
    # separated by a space (YAML folds the line breaks).
    return " ".join(
        f'{{"type":"ON/OFF","idx":"{n}","status":"{status}","time":"0","pass":"0"}}'
        for n in range(1, count + 1)
    )


async def _press(hass, entity_id: str) -> None:
    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )


async def test_all_on_and_all_off_are_buttons_not_switches(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "4")

    assert hass.states.get("button.dingtian_47196_all_on") is not None
    assert hass.states.get("button.dingtian_47196_all_off") is not None
    assert not [s for s in hass.states.async_all("switch") if "all" in s.entity_id]
    registry = er.async_get(hass)
    assert registry.async_get("button.dingtian_47196_all_on").unique_id == "47196_all_on"
    assert registry.async_get("button.dingtian_47196_all_off").unique_id == "47196_all_off"


async def test_pressing_all_on_commands_every_output(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "4")
    mqtt_mock.async_publish.reset_mock()

    await _press(hass, "button.dingtian_47196_all_on")

    mqtt_mock.async_publish.assert_called_once_with(
        f"{BASE}/in/control", _expected("ON", 4), 0, False
    )


async def test_pressing_all_off_commands_every_output(hass, mqtt_mock):
    await _add_board(hass)
    await _publish(hass, "relay_cnt", "2")
    mqtt_mock.async_publish.reset_mock()

    await _press(hass, "button.dingtian_47196_all_off")

    mqtt_mock.async_publish.assert_called_once_with(
        f"{BASE}/in/control", _expected("OFF", 2), 0, False
    )


async def test_pressing_before_the_output_count_is_known_publishes_nothing(
    hass, mqtt_mock
):
    await _add_board(hass)
    mqtt_mock.async_publish.reset_mock()

    with pytest.raises(HomeAssistantError):
        await _press(hass, "button.dingtian_47196_all_on")

    mqtt_mock.async_publish.assert_not_called()
