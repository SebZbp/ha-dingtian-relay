"""Config flow: a Board announcing its serial on MQTT becomes a discovery card."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import AreaSelector
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import CONF_AREA, CONF_SERIAL, CONF_TOPIC_BASE, DOMAIN, LOGGER


class DingtianConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    _serial: str
    _topic_base: str

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> ConfigFlowResult:
        serial = str(discovery_info.payload).strip()
        if not serial:
            return self.async_abort(reason="invalid_serial")
        LOGGER.debug("Board %s announced itself on %s", serial, discovery_info.topic)
        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured()
        self._serial = serial
        # "dingtian/relay<serial>/out/sn" -> "dingtian/relay<serial>"
        self._topic_base = discovery_info.topic.rsplit("/out/", 1)[0]
        self.context["title_placeholders"] = {"name": f"Dingtian {serial}"}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        default_name = f"Dingtian {self._serial}"
        if user_input is not None:
            data = {CONF_SERIAL: self._serial, CONF_TOPIC_BASE: self._topic_base}
            if user_input.get(CONF_AREA):
                data[CONF_AREA] = user_input[CONF_AREA]
            return self.async_create_entry(
                title=user_input.get("name") or default_name, data=data
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=default_name): str,
                    vol.Optional(CONF_AREA): AreaSelector(),
                }
            ),
            description_placeholders={"serial": self._serial},
        )
