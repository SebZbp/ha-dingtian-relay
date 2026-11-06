# Dingtian Relay

Home Assistant integration that turns Dingtian relay boards into HA devices, and lets each relay contact be presented as the real-world thing it drives, such as a heating circuit or a light.

## Language

**Board**:
One physical Dingtian relay board on the network, identified by its serial number (e.g. `47196`); it appears as one HA device.
_Avoid_: Relay, module, controller, relay board (in prose, "Board" alone)

**Output**:
One relay contact on a Board, numbered from 1 (e.g. Output 3 of Board 47196). It is either on or off.
_Avoid_: Relay, switch, channel, r1

**Input**:
One digital input on a Board, numbered from 1. It reports on or off and drives nothing by itself.
_Avoid_: Sensor, i1

**All on** / **All off**:
A single command that turns every Output of one Board on, or off, at once.
_Avoid_: Master switch, switch all

**Load**:
The real-world thing an Output drives, such as the valve of the "Chauffage cuisine" heating circuit or the "Lumière hall d'entrée" light. An Output has at most one Load; an Output without a Load is just an Output of its Board.
_Avoid_: Circuit (a kind of Load, not the concept), mapping, target

**Attached Load**:
A Load that is an existing HA device from another integration, such as the "Chauffage Cuisine" thermostat; the Output joins that device.
_Avoid_: Linked device

**Virtual Load**:
A Load that has no device of its own elsewhere, so the integration creates one for it, with its own name and area.
_Avoid_: Fake device, dummy device, helper
