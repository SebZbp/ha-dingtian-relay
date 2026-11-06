# Board discovery and monitoring

Tracker: beads feature `dingtian-8ux.1` under epic `dingtian-8ux` (label `ready-for-agent`)

Phase 1 of 2. Phase 2 is `docs/specs/loads.md`.

## Problem Statement

The home owner has three Dingtian Boards (serials 22333, 47195, 47196) that drive the house's lights and the valves of the heating circuits. In Home Assistant they exist only as three hand-written YAML packages of about 720 lines each, almost all duplicated or commented out. None of their entities belongs to a device, so there is no single place to see a Board: whether it is online, its IP, MAC, serial, hardware and software versions, or the state of its Outputs and Inputs. Adding a Board means copying a YAML file and search-and-replacing its serial. A firmware update, a new Board or a Board going offline can only be noticed by reading MQTT topics by hand.

## Solution

A custom integration, built on HA's existing MQTT integration, turns every Dingtian Board into one HA device. When a Board publishes on MQTT, HA shows a discovery card that offers "Dingtian" followed by its serial as the name and lets the home owner choose an area, or Ignore the Board. Once added, the Board's device shows:
- one switch per Output and one binary sensor per Input, in the numbers the Board reports;
- All on and All off buttons;
- its serial, hardware and software versions in the device info;
- its IP, MAC and availability as diagnostic entities.

When the Board's firmware changes, the device's software version follows on its own. A diagnostics download gives everything the integration knows about the Board, including anything it doesn't recognise. Assigning Loads to Outputs is phase 2. In this phase each Output is a plain switch on its Board.

## User Stories

1. As a home owner, I want a newly connected Board to appear as a discovery card in HA, so that I don't have to write YAML to add it.
2. As a home owner, I want the discovery card to show the Board's serial, so that I know which physical Board I'm adding.
3. As a home owner, I want the discovery card to suggest "Dingtian" followed by the serial as a name I can change, so that a neutral default exists but I can name it after its location.
4. As a home owner, I want to choose the Board's area on the discovery card, so that it lands in the right room without a second step.
5. As a home owner, I want to Ignore a discovered Board with HA's native Ignore, so that a Board I don't want in HA stops being offered.
6. As a home owner, I want to bring an ignored Board back from HA's ignored list, so that ignoring is never permanent.
7. As a home owner, I want each Board to be a separate integration entry, so that I can reload, disable or remove one Board without touching the others.
8. As a home owner, I want the same Board never to be offered twice, so that I can't add duplicates.
9. As a home owner, I want each Board to appear as one HA device, so that everything about it is in one place.
10. As a home owner, I want the device to show the manufacturer, the serial number, the hardware version and the software version, so that I can identify the Board without opening its web page.
11. As a home owner, I want the device's software version to update by itself when the Board reports a new one, so that it stays correct after a firmware upgrade.
12. As a home owner, I want a firmware upgrade to leave my entities, entity_ids and automations untouched, so that upgrading is not risky on the HA side.
13. As a home owner, I want the Board's IP address as a diagnostic entity, so that I can find its web page.
14. As a home owner, I want the Board's MAC address as a diagnostic entity, so that I can match it with my router's DHCP leases.
15. As a home owner, I want a diagnostic entity that shows whether the Board is online, so that I can alert on a Board going offline.
16. As a home owner, I want every entity of a Board to become unavailable when the Board goes offline, so that I never act on a stale state.
17. As a home owner, I want one switch per Output, so that I can see and change each Output from HA.
18. As a home owner, I want the number of Output switches to match what the Board reports, so that 2-, 4-, 8-, 16- and 32-Output Boards all work.
19. As a home owner, I want an Output switch to show the state the Board reports, not the state HA last asked for, so that the display is the truth.
20. As a home owner, I want turning an Output switch on or off to change the physical relay within a second, so that HA control feels direct.
21. As a home owner, I want an Output changed from the Board's web page or by its Inputs to show the new state in HA, so that HA stays in sync with changes made elsewhere.
22. As a home owner, I want Outputs to be named by their number ("Output 3") by default, so that unnamed Outputs are still unambiguous.
23. As a home owner, I want to rename an Output or change its entity_id with HA's standard entity settings, so that I can label it before phase 2 exists.
24. As a home owner, I want one binary sensor per Input, in the number the Board reports, so that I can see the state of each Input.
25. As a home owner, I want an Input to show its logical state (on/off) as the Board reports it, so that I don't have to think about electrical HIGH/LOW levels.
26. As a home owner, I want an All on button on each Board, so that I can turn every Output of that Board on at once.
27. As a home owner, I want an All off button on each Board, so that I can turn every Output of that Board off at once.
28. As a home owner, I want to press All on and All off from an automation or script, so that I can use them in scenes such as "leaving home".
29. As a home owner, I want All on and All off to be buttons rather than a switch, so that there is no "all" state that would misrepresent mixed Outputs.
30. As a home owner, I want to download diagnostics for a Board, so that I can see everything the integration knows about it.
31. As a home owner, I want the diagnostics to include the last value seen on every topic of the Board, including topics the integration doesn't use, so that a firmware change can be analysed like a capture.
32. As a home owner, I want topics and payloads the integration doesn't recognise to be logged at debug level, so that I can turn on logging to investigate without being flooded by default.
33. As a home owner, I want an entry to retry by itself when MQTT isn't ready at HA start, so that a slow broker doesn't leave a Board broken until I reload.
34. As a home owner, I want reloading a Board's entry not to duplicate its subscriptions, so that a reload never doubles commands or states.
35. As a home owner, I want removing a Board's entry to stop all its MQTT traffic handling, so that nothing is left behind.
36. As a home owner, I want each entity of a Board to keep a stable identity built from the Board's serial and the Output or Input number, so that renames and the later migration from YAML keep working.
37. As a home owner, I want the integration and the old YAML packages to be able to run side by side, so that I can migrate one Board at a time later.
38. As a home owner, I want to install the integration through HACS, so that updates work like my other custom integrations.
39. As a home owner, I want every card, menu and entity name to have proper UI texts, so that nothing shows a raw translation key.
40. As a maintainer, I want CI to run hassfest, HACS validation and the tests on every push, so that broken manifests or strings are caught before a release.
41. As a maintainer, I want a test that rejects angle brackets in UI strings, so that the INVALID_TAG error seen in Edisio can't come back.
42. As a maintainer, I want a test that the manifest and pyproject versions match, so that releases are numbered consistently.
43. As a maintainer, I want a deploy script that backs up the deployed integration, copies the new files with `cp -f`, and reminds me to fully restart HA, so that testing on the real house is repeatable and safe.

## Implementation Decisions

- **Transport (ADR-0001)**: MQTT only, through HA's MQTT integration. No HTTP, no Modbus, no extra Python requirements. The integration depends on `mqtt`.
- **Topic contract** (from the 2026-11-06 capture, `docs/research/mqtt-capture-2026-11-06.md`): Boards publish under `dingtian/relay<serial>/out/…`:
  - `sn`, `relay_cnt`, `input_cnt`, `ip`, `mac`, `sw_version`, `hw_version`, `lwt_availability` (`online`/`offline`);
  - `r<n>` and `i<n>` (`ON`/`OFF`).

  Commands go to `dingtian/relay<serial>/in/r<n>` (`ON`/`OFF`), and All on / All off to `…/in/control` as the JSON lines the YAML uses today. The duplicate JSON topics (`relay<n>`, `input<n>`) are ignored because `i<n>` already carries the logical Input state. Nothing is retained.
- **Discovery**: the manifest declares an MQTT discovery topic on the Boards' `sn` topic, and the config flow handles MQTT discovery. The serial is the flow's unique_id, so duplicates and Ignore work natively. The card has an editable name (default "Dingtian" followed by the serial) and an optional area. Manual setup is not offered in this phase.
- **Config entry**: one per Board (ADR-0001). It stores the serial and the topic base. VERSION 1 is set from the start and a migration hook is in place.
- **Board model module**: one module owns a Board's live state. It subscribes to the Board's topics, parses payloads, keeps the last value of every topic for diagnostics, publishes commands, and notifies entities. Entities read from it and never touch MQTT themselves. Every subscription is removed on unload. Setup raises "not ready" when MQTT isn't available.
- **Output and Input count**: taken from `relay_cnt` and `input_cnt`. Entities are created once the counts are known, with 8 as the fallback if a count hasn't arrived after a short wait. A count that grows later adds entities. Removing entities when a count shrinks is out of scope.
- **Entities** (all with `has_entity_name`):
  - Output switch: unique_id built from the serial and `output_<n>`.
  - Input binary sensor: from the serial and `input_<n>`.
  - All on and All off buttons.
  - Diagnostic entities: IP sensor, MAC sensor, and a connectivity binary sensor for availability.
- **Device info**: manufacturer "Dingtian", the serial as `serial_number`, `hw_version` and `sw_version` updated in the device registry whenever the Board publishes a different value, and the IP as a configuration URL.
- **Availability**: driven by `lwt_availability`. Every entity of the Board follows it.
- **Diagnostics download**: config entry data, counts, the last payload and timestamp per topic, and the unrecognised topics.
- **Logging**: debug level under the integration's logger. No warnings for unrecognised topics.
- **Translations**: `strings.json` plus the `en` translation from the first commit, as in Edisio.
- **Repo scaffold**: uv project, HACS metadata, GitHub Actions (hassfest, HACS validation, pytest), and a deploy script, following `docs/research/edisio-retro.md`.

## Testing Decisions

- **One seam: HA itself with a mocked MQTT broker** (pytest-homeassistant-custom-component's MQTT mock). Tests feed in Board messages exactly as captured, drive the config flow through HA's flow API, and check only what the home owner sees: entity states and attributes, the device registry, the entity registry, discovery flows, and the MQTT messages published to the Board.
- Good tests describe behaviour ("a Board that publishes `relay_cnt` 4 gets 4 Output switches"), not internals. The Board model module is not tested directly. It is covered through the seam.
- Covered:
  - discovery card and its fields;
  - Ignore and duplicate refusal;
  - entity creation from the counts, and the fallback;
  - state updates from `r<n>`/`i<n>`;
  - switch commands;
  - All on / All off payloads;
  - availability, and the SW version update in the device registry;
  - unload and reload without duplicate subscriptions;
  - not-ready retry;
  - diagnostics content;
  - the strings test (no angle brackets) and the version-sync test.
- Prior art: the Edisio repo's flow and options tests (plain pytest against a minimal HA) for the shape of the scenarios. This repo uses pytest-homeassistant-custom-component instead, for its MQTT mock.

## Out of Scope

- Loads, Attached Loads and Virtual Loads, and the options flow (phase 2, `docs/specs/loads.md`).
- Jogging, delay and interlock modes.
- Firmware updates from HA.
- HTTP and Modbus access to Boards.
- Adding a Board by hand without discovery.
- Removing entities when a Board reports fewer Outputs or Inputs.
- Migrating the three existing YAML packages. That is done later in the HA config, Board by Board.

## Further Notes

- **Open, `needs-info` ticket `dingtian-8ux.1.9`**: nothing is retained, so after an HA restart an Output's state is unknown until the Board publishes again. Before the state-after-restart behaviour is final, it must be checked on a real Board how often it republishes its full state, whether a command asks it to, and whether `lwt_availability` is retained. If no refresh command exists, the fallback is to show "unknown" until the next publish, never a restored state.
- Sizing note for migration: Board 22333 drives lights 1–8, Board 47195 drives 8 lights (its Outputs 7 and 8 have crossed names today), and Board 47196 drives 7 heating valves used by Versatile Thermostat plus one unused Output.
