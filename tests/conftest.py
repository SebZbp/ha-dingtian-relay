from pathlib import Path

import custom_components
import pytest

# pytest-homeassistant-custom-component ships its own `custom_components`
# package (testing_config). Add this repo's folder so HA finds our integration.
_REPO_COMPONENTS = str(Path(__file__).parent.parent / "custom_components")
if _REPO_COMPONENTS not in custom_components.__path__:
    custom_components.__path__.append(_REPO_COMPONENTS)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let HA load custom_components/dingtian in every test."""
