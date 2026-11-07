"""The Board model: the live state of one Dingtian Board.

One Board owns every MQTT subscription of its config entry. It keeps the last
value seen on every topic under ``<topic_base>/out/`` (recognised or not, for
diagnostics), parses the topics it knows, publishes commands, and tells
listeners (entities) when something changed. Entities read from the Board and
never touch MQTT themselves.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components import mqtt
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import COUNT_FALLBACK, COUNT_WAIT_SECONDS, LOGGER

_OUTPUT_TOPIC = re.compile(r"r(\d+)")
_INPUT_TOPIC = re.compile(r"i(\d+)")
# Kept in the per-topic store but not parsed: the serial (used for discovery)
# and the JSON duplicates of r<n>/i<n>. Not "unrecognised", not logged.
_KNOWN_IGNORED_TOPIC = re.compile(r"sn|relay\d+|input\d+")

# Count topics and the Board attribute each one fills.
_COUNT_TOPICS = {"relay_cnt": "_output_count", "input_cnt": "_input_count"}

# Topics whose payload is kept as text on the Board, and the attribute for each.
_TEXT_TOPICS = {
    "ip": "ip",
    "mac": "mac",
    "hw_version": "hw_version",
    "sw_version": "sw_version",
}


@dataclass(frozen=True, slots=True)
class TopicValue:
    """The last payload seen on one topic, and when."""

    payload: str
    received: datetime


class Board:
    """Live state of one Board, fed by MQTT."""

    def __init__(self, hass: HomeAssistant, serial: str, topic_base: str) -> None:
        self.hass = hass
        self.serial = serial
        self.topic_base = topic_base
        # Last value per topic, keyed by the topic below "<base>/out/".
        self.topic_values: dict[str, TopicValue] = {}
        # Topics whose last message the Board model did not understand.
        self.unrecognised: set[str] = set()
        self._outputs: dict[int, bool] = {}
        self._output_count: int | None = None
        self._inputs: dict[int, bool] = {}
        self._input_count: int | None = None
        # Identity and health, as published by the Board; None until seen.
        self._lwt: str | None = None
        self.ip: str | None = None
        self.mac: str | None = None
        self.hw_version: str | None = None
        self.sw_version: str | None = None
        self._listeners: list[CALLBACK_TYPE] = []
        self._unsubscribe: CALLBACK_TYPE | None = None
        self._cancel_count_wait: CALLBACK_TYPE | None = None

    # -- lifecycle ---------------------------------------------------------

    async def async_start(self) -> None:
        """Subscribe to everything the Board publishes."""
        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, f"{self.topic_base}/out/#", self._handle_message
        )
        self._cancel_count_wait = async_call_later(
            self.hass, COUNT_WAIT_SECONDS, self._count_wait_over
        )

    @callback
    def async_stop(self) -> None:
        """Remove every subscription and listener."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        if self._cancel_count_wait is not None:
            self._cancel_count_wait()
            self._cancel_count_wait = None
        self._listeners.clear()

    @callback
    def _count_wait_over(self, _now: datetime) -> None:
        """No relay_cnt after the short wait: assume the usual 8 Outputs."""
        self._cancel_count_wait = None
        for topic, attribute in _COUNT_TOPICS.items():
            if getattr(self, attribute) is None:
                LOGGER.debug(
                    "Board %s: no %s, assuming %s", self.serial, topic, COUNT_FALLBACK
                )
                setattr(self, attribute, COUNT_FALLBACK)
                self._notify()

    # -- state ---------------------------------------------------------------

    @property
    def output_count(self) -> int | None:
        """Number of Outputs, or None while it is not known yet."""
        return self._output_count

    @property
    def available(self) -> bool:
        """False only once the Board has said it is offline."""
        return self._lwt != "offline"

    @property
    def online(self) -> bool | None:
        """True/False as the Board reported in lwt_availability, None until then."""
        return None if self._lwt is None else self._lwt == "online"

    def output_is_on(self, number: int) -> bool | None:
        """State the Board reported for an Output, None until it did."""
        return self._outputs.get(number)

    @property
    def input_count(self) -> int | None:
        """Number of Inputs, or None while it is not known yet."""
        return self._input_count

    def input_is_on(self, number: int) -> bool | None:
        """Logical state the Board reported for an Input, None until it did."""
        return self._inputs.get(number)

    @callback
    def async_add_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Call ``listener`` whenever the Board's state changes."""
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    # -- commands --------------------------------------------------------------

    async def async_set_output(self, number: int, on: bool) -> None:
        """Command an Output. The state shown only changes when the Board reports."""
        await mqtt.async_publish(
            self.hass, f"{self.topic_base}/in/r{number}", "ON" if on else "OFF"
        )

    async def async_set_all_outputs(self, on: bool) -> None:
        """Command every Output at once (All on / All off)."""
        count = self._output_count
        if not count:
            raise HomeAssistantError("The number of Outputs is not known yet")
        status = "ON" if on else "OFF"
        payload = " ".join(
            json.dumps(
                {"type": "ON/OFF", "idx": str(n), "status": status, "time": "0", "pass": "0"},
                separators=(",", ":"),
            )
            for n in range(1, count + 1)
        )
        await mqtt.async_publish(self.hass, f"{self.topic_base}/in/control", payload)

    # -- incoming messages -------------------------------------------------------

    @callback
    def _handle_message(self, message: mqtt.ReceiveMessage) -> None:
        prefix = f"{self.topic_base}/out/"
        if not message.topic.startswith(prefix):
            return
        topic = message.topic[len(prefix) :]
        payload = (
            message.payload
            if isinstance(message.payload, str)
            else message.payload.decode(errors="replace")
        ).strip()
        self.topic_values[topic] = TopicValue(payload, dt_util.utcnow())

        if _KNOWN_IGNORED_TOPIC.fullmatch(topic):
            self.unrecognised.discard(topic)
            return
        if not self._parse(topic, payload):
            self.unrecognised.add(topic)
            LOGGER.debug("Board %s: ignoring %s = %r", self.serial, topic, payload)
            return
        self.unrecognised.discard(topic)
        self._notify()

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _parse(self, topic: str, payload: str) -> bool:
        """Update state from a known topic; False when the topic is not used."""
        if attribute := _COUNT_TOPICS.get(topic):
            if not payload.isdigit():
                return False
            setattr(self, attribute, max(getattr(self, attribute) or 0, int(payload)))
            return True
        if (match := _INPUT_TOPIC.fullmatch(topic)) and payload in ("ON", "OFF"):
            self._inputs[int(match.group(1))] = payload == "ON"
            return True
        if topic == "lwt_availability" and payload in ("online", "offline"):
            self._lwt = payload
            return True
        if topic in _TEXT_TOPICS and payload:
            setattr(self, _TEXT_TOPICS[topic], payload)
            return True
        if (match := _OUTPUT_TOPIC.fullmatch(topic)) and payload in ("ON", "OFF"):
            self._outputs[int(match.group(1))] = payload == "ON"
            return True
        return False

