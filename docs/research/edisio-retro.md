# Retro: lessons from building ha-edisio-integration

Source: Claude Code sessions in `~/code/ha-edisio-integration` and `/Volumes/config` (May–Nov 2026) and the repo's git history. Collected 2026-11-06 to keep the Dingtian integration consistent with it.

## Workflow that worked
- Grill (numbered questions, each with a recommendation), then a spec in `docs/specs/<slug>.md`, then a beads epic with child tickets (`bd dep` for blockers, `needs-info` for unknowns), then implement, PR, merge.
- One branch and one git worktree per feature. PR bodies written with `/mattpocock-skills:pr`.
- `CONTEXT.md` is a strict glossary. Specs, code and commits use its terms.
- A PreToolUse hook runs `bd sync` before any bd state change.
- Approval: no commit or push without the user's OK, and no change to `/Volumes/config` without validation.
- Deploy to test before merging:
  - Back up the deployed folder.
  - Copy with `cp -f` per file (`rsync` fails on the Samba share).
  - Fully restart HA (a reload keeps old Python modules), then refresh the browser after a strings change.
  - The user tests on real hardware, then the branch merges.
- Release: bump `manifest.json`, merge to main, tag from main only, `gh release`.

## User preferences
- Device names such as "BP <room>" are typed by the user. The code default stays neutral.
- Manage everything from one options-flow menu (add / edit / remove). Use HA's native Ignore on discovery cards, not custom UI.
- Hardware captures are the source of truth: no assumed protocol mappings.
- Proper debug-level logging that can be switched on through the logger level. No temporary WARNING logs.
- Releases happen only when explicitly asked.

## Pitfalls → rules
| Pitfall | Rule |
|---|---|
| Missing `translations/`, options-flow 500s | Scaffold `strings.json` + `translations/en.json` from day one |
| `<…>` in UI strings → INVALID_TAG; came back from an unmerged fix branch | No angle brackets in strings (enforce with a test); merge fix branches promptly |
| Reloads stacked readers | Tear down every connection/subscription on unload |
| Lost connection never recovered; missing at boot never retried | Reconnect with backoff; raise `ConfigEntryNotReady`; expose a connection diagnostic |
| Unstable identifiers needed a config-entry migration | Stable unique_ids from day one; set config entry VERSION and `async_migrate_entry` early |
| One action fired several events | Debounce where the source repeats |
| Stale local main, tag on non-main branch | Compare against `origin/main`; tag only after merge |

## HA patterns adopted
- Discovery flow per device with a per-device unique_id. The card shows the model and an optional name and area, and supports native Ignore.
- Options flow uses `async_show_menu`: Add / Edit (name, entity IDs, area) / Remove.
- DeviceInfo has manufacturer, model, `serial_number` and `via_device`.
- Entities use `has_entity_name`, stable unique_ids, `RestoreEntity` where useful, and diagnostic entity categories.
- Gaps: no `diagnostics.py`, no CI (hassfest / HACS), and the pyproject version was never synced.
