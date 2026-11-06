# Loads

Tracker: beads feature `dingtian-8ux.2` under epic `dingtian-8ux` (label `ready-for-agent`)

Phase 2 of 2. Builds on `docs/specs/board-discovery-and-monitoring.md`.

## Problem Statement

After phase 1, every Output is a plain switch called "Output 3" on its Board's device. That isn't how the home owner thinks about the house. Output 1 of Board 47196 is the valve of the kitchen heating circuit, which a Versatile Thermostat drives. Output 3 of Board 22333 is the "Lumière périphérique cuisine" light. Today that meaning lives in YAML names, in a duplicated switch/light definition per relay, and in the home owner's memory. Nothing links a heating valve to its thermostat or a light to its room, and changing what an Output drives means editing YAML and restarting.

## Solution

From the Board's options, the home owner gives any Output a Load: the real-world thing it drives. A Load has a name, a type (switch or light) and an entity_id. It is one of two kinds:
- **Attached Load**: its entity joins an existing HA device, such as the "Chauffage Cuisine" thermostat, so the valve shows up next to the thermostat that drives it.
- **Virtual Load**: the integration creates a device for it, with its own name and area, connected to the Board.

A Load can be edited or removed at any time. Removing it turns the Output back into a plain switch on its Board. Heating valves stay switches so Versatile Thermostat can keep driving them.

## User Stories

1. As a home owner, I want a menu in each Board's options with Assign a Load, Edit a Load and Remove a Load, so that I manage everything about a Board's Outputs from one place.
2. As a home owner, I want to pick which Output to assign, seeing each Output's number and current state, so that I choose the right relay.
3. As a home owner, I want only Outputs without a Load to be offered for assignment, so that I can't give one Output two Loads.
4. As a home owner, I want to give a Load a name, so that the entity reads "Vanne chauffage cuisine" instead of "Output 1".
5. As a home owner, I want to choose whether a Load is a switch or a light, so that lights behave as lights in HA (voice assistants, light cards, area "turn off the lights").
6. As a home owner, I want heating valves to be switches, so that Versatile Thermostat can use them as underlying switches.
7. As a home owner, I want to set a Load's entity_id when I assign it, so that I can reuse an existing entity_id (`switch.circuit_chauffage_1`, `light.dingtian_light_3`) and my automations, dashboards and thermostats keep working.
8. As a home owner, I want a clear error if the entity_id I type is already used, so that I know to remove the old YAML entity first.
9. As a home owner, I want to choose whether a Load is Attached to an existing device or is a Virtual Load, so that both cases work from the same menu.
10. As a home owner, I want to pick the device for an Attached Load from HA's device picker, so that I don't need to know any IDs.
11. As a home owner, I want an Attached Load's entity to show up on that device's page, so that a thermostat's page shows the valve it drives.
12. As a home owner, I want an Attached Load to take its area from the device it joins, so that I don't set the area twice.
13. As a home owner, I want a Virtual Load to get its own device with the Load's name, so that a light or valve with no other device still has a place in HA.
14. As a home owner, I want to set the area of a Virtual Load, so that "Lumière garage" lands in the Garage area.
15. As a home owner, I want a Virtual Load's device to show it is connected via its Board, so that I can go from the Load to the Board and back.
16. As a home owner, I want a Load's entity to say which Board and which Output drive it, so that I can find the physical relay when something breaks.
17. As a home owner, I want a Load's entity to show the state the Board reports and to command the Output, so that it behaves exactly like the plain Output switch did.
18. As a home owner, I want a Load to become unavailable when its Board goes offline, so that thermostats and automations don't act on a stale state.
19. As a home owner, I want to edit a Load's name, type, entity_id, kind, target device or area, so that I can fix mistakes without removing and recreating it.
20. As a home owner, I want to move a Load from one device to another, so that I can fix a wrong attachment.
21. As a home owner, I want to remove a Load, so that its Output goes back to being a plain switch on its Board.
22. As a home owner, I want to be asked to confirm before a Load is removed, so that I don't break a thermostat by accident.
23. As a home owner, I want a Load to survive HA restarts, integration reloads and Board firmware upgrades, so that I configure it once.
24. As a home owner, I want an Attached Load to fall back to its Board's device if the device it joined is deleted, so that the Output never disappears.
25. As a home owner, I want to change a Load's icon (e.g. a valve icon) through HA's standard entity settings, so that the integration doesn't need its own icon picker.
26. As a home owner, I want the Board's diagnostics to list every Output with its Load (name, type, kind, device, entity_id), so that I can see the whole mapping of a Board at once.
27. As a home owner, I want the Board's device page to show its Virtual Loads as connected devices, so that I can see from the Board what it drives.
28. As a home owner, I want a Board whose Outputs all have Loads to keep its Inputs, All on / All off buttons and diagnostic entities, so that the Board view stays complete.
29. As a home owner, I want All on and All off to act on every Output whether or not it has a Load, so that their meaning doesn't change.
30. As a home owner, I want to assign Loads for the three existing Boards, one Board at a time, while the other Boards still run on YAML, so that I can migrate gradually.

## Implementation Decisions

- **Options flow**: a menu on each Board entry with Assign a Load, Edit a Load and Remove a Load, following the Edisio options flow pattern (menu, then steps).
  - Assign: pick a free Output, then the kind (Attached or Virtual), then the name, type (switch or light), entity_id, and either the target device (Attached) or the area (Virtual).
  - Edit: pick a Load, then the same fields pre-filled.
  - Remove: pick a Load, then confirm.
- **Storage**: Loads live in the Board entry's options, keyed by Output number. Each holds name, type, kind, target device id (Attached) and area (Virtual). Changing options reloads the entry.
- **One entity per Output**: an Output is exposed by exactly one entity at a time. Without a Load, it's the plain Output switch from phase 1. With a Load, it's the Load entity in the Load's type, and the plain Output switch is removed from the entity registry. Removing a Load restores the plain Output switch. Load entity unique_ids are built from the serial, `load_<n>` and the type, so a type change creates a fresh entity that is then given the requested entity_id.
- **entity_id**: applied through the entity registry after creation. The flow validates that the requested entity_id is free and in the right domain for the type.
- **Attached Load (ADR-0002)**: the entity joins the target device the way `switch_as_x` does. The integration listens for device removals. When a target device is removed, the Load entity moves to the Board's device and the event is logged at debug level.
- **Virtual Load**: a device per Load, identified by the serial and `load_<n>`, named after the Load, in the chosen area, with `via_device` set to the Board's device.
- **Load entity attributes**: Board serial and Output number.
- **Heating valves (ADR-0003)**: no `valve` type. Valves are switch Loads. The icon is left to HA's entity settings.
- **Board model**: unchanged from phase 1. Load entities read Output state from it and send commands through it like plain Output switches. All on / All off are unaffected.
- **Diagnostics**: extended with the Load of every Output.

## Testing Decisions

- Same single seam as phase 1: HA with a mocked MQTT broker. Tests drive the options flow through HA's flow API, then check the entity registry (domain, entity_id, unique_id, device), the device registry (Virtual Load devices, `via_device`, areas), entity states, and the MQTT commands sent when a Load entity is switched.
- Covered:
  - assign Attached and Virtual Loads, as switch and as light;
  - entity_id reuse and the conflict error;
  - edit every field, including a type change and moving to another device;
  - removal restoring the plain Output switch;
  - the fallback when an Attached Load's target device is deleted;
  - persistence across reload;
  - availability following the Board;
  - diagnostics content;
  - a Versatile-Thermostat-like case: an Attached switch Load keeps a given entity_id and commands the Output.
- Prior art: phase 1 tests in this repo, and the Edisio options-flow tests (add / edit / remove) for scenario shape.

## Out of Scope

- A `valve` entity type, until Versatile Thermostat accepts it (ADR-0003).
- Loads on Inputs.
- One Load driven by several Outputs, or one Output driving several Loads.
- Jogging, delay and interlock modes.
- Removing the YAML packages and moving the existing entity_ids. That is done later in the HA config, using story 7.

## Further Notes

- Possible later addition: an HA repair issue when an Attached Load falls back to its Board, instead of only a debug log.
- Migration reminders: on Board 47195 the names of Outputs 7 and 8 are crossed today, and Board 47196 has `switch.dcircuit_chauffage_4` (typo), which is referenced by a Versatile Thermostat. Fix both when assigning their Loads.
