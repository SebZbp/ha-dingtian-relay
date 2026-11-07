# Board state republish: Board 22333, 2026-11-07

Source: two diagnostics downloads of the same Board (serial 22333, firmware V3.1.2178A, hardware V3.6J) taken 13 minutes apart, with no action on the Board in between. MAC and IP are not reproduced here.

## Findings
- **The Board republishes its full state on its own, every 13 minutes.** Every `r<n>`, `i<n>`, `relay<n>`, `input<n>`, `ip`, `mac`, `sn`, `input_cnt`, `relay_cnt` and `lwt_availability` topic carries a timestamp of 12:49:11 in the first download and 13:02:11 in the second (UTC). The whole burst lasts about one second, in a fixed order: `lwt_availability`, `r1`..`r8`, `i1`..`i8`, `relay<n>`, `input<n>`, then `ip`, `mac`, `sn`, `input_cnt`, `relay_cnt`.
- **`lwt_availability` is republished with `online` in every burst.** This is how a Board announces itself on connecting, so the Board may be reconnecting to the broker every 13 minutes. Not yet checked: whether `offline` appears briefly in between, which would make every entity flicker unavailable.
- **`sw_version` and `hw_version` are not part of the burst.** Both were last seen at 11:37:00, which is when HA started, 72 minutes before the first download. They may be retained, or the Board may send them only when a client connects. Not yet distinguished.
- **No unrecognised topics** (`unrecognised` is empty in both downloads).

## Consequence
After an HA restart, an Output shows "unknown" for up to 13 minutes, until the next burst. Nothing is retained for `r<n>`, so HA cannot read it back on subscribing.

## Still open
- Is there a command that makes the Board publish its state at once? If so, the integration can send it on startup and the wait disappears.
- Is `lwt_availability` retained, and does it go `offline` between bursts?
- Are `sw_version` and `hw_version` retained?
