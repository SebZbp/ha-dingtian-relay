"""The scaffold's guard rails: HA loads the integration, strings are safe, versions agree."""
import json
import tomllib
from pathlib import Path

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

ROOT = Path(__file__).parent.parent
COMPONENT = ROOT / "custom_components" / "dingtian"


async def test_integration_sets_up_and_unloads_cleanly(hass, mqtt_mock):
    entry = MockConfigEntry(domain="dingtian", data={}, title="Dingtian")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)


def test_ui_strings_have_no_angle_brackets():
    for name in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / name).read_text())
        for text in _strings(data):
            assert "<" not in text and ">" not in text, f"{name}: {text!r}"


def test_manifest_and_pyproject_versions_match():
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert manifest["version"] == pyproject["project"]["version"]


def test_manifest_declares_mqtt_dependency_and_hacs_metadata_exists():
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    assert manifest["domain"] == "dingtian"
    assert manifest["config_flow"] is True
    assert "mqtt" in manifest["dependencies"]
    assert (ROOT / "hacs.json").exists()
