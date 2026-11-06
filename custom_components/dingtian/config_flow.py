"""Config flow. Board discovery arrives in a later ticket; nothing to set up yet."""
from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN


class DingtianConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
