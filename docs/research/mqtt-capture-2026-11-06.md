# MQTT capture: Board 47195, 2026-11-06 20:15

Captured with HA's MQTT "Listen to a topic" on `dingtian/relay47195/#`. Every message had QoS 0 and **Retain: false**.

| Topic (under `dingtian/relay47195/out/`) | Payload seen |
|---|---|
| `relay_cnt` | `8` |
| `input_cnt` | `8` |
| `sn` | `47195` (matches the topic) |
| `mac` | `xx:xx:xx:xx:xx:xx` (redacted) |
| `ip` | `192.168.x.x` (redacted) |
| `r1`…`r8` | `ON` / `OFF` |
| `relay1`…`relay8` | `{"idx":"1","status":"ON"}` |
| `i1`…`i8` | `OFF` |
| `input1`…`input8` | `{"idx":"1","status":"HIGH"}` |

## Observations
- Each Board publishes the number of its Outputs (`relay_cnt`) and Inputs (`input_cnt`).
- The serial in the topic is the Board's `sn`.
- Every Output and Input is published twice: as plain `ON`/`OFF` (`rN`, `iN`) and as JSON (`relayN`, `inputN`).
- Input polarity: `i1` = `OFF` while `input1` = `HIGH` at the same moment. The plain topic is already the logical state and the JSON one is the electrical level, so the plain one is the one to use.
- `sw_version`, `hw_version` and `lwt_availability` were not in the visible part of the capture. They are known from the YAML packages.

## Open (needs-info)
- Nothing is retained. How often does the Board republish its full state, and is there a command that asks it for its state? This decides what an Output shows right after an HA restart.
- Is `lwt_availability` retained (as an LWT normally is)?
