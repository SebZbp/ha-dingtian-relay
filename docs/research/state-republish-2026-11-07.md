# Board state republish: Board 22333, 2026-11-07

Source: two diagnostics downloads of the same Board (serial 22333, firmware V3.1.2178A, hardware V3.6J) taken 13 minutes apart, with no action on the Board in between. MAC and IP are not reproduced here.

## Findings
- **The Board republishes its full state on its own, every 13 minutes.** Every `r<n>`, `i<n>`, `relay<n>`, `input<n>`, `ip`, `mac`, `sn`, `input_cnt`, `relay_cnt` and `lwt_availability` topic carries a timestamp of 12:49:11 in the first download and 13:02:11 in the second (UTC). The whole burst lasts about one second, in a fixed order: `lwt_availability`, `r1`..`r8`, `i1`..`i8`, `relay<n>`, `input<n>`, then `ip`, `mac`, `sn`, `input_cnt`, `relay_cnt`.
- **`lwt_availability` is republished with `online` in every burst.** This is how a Board announces itself on connecting, so the Board may be reconnecting to the broker every 13 minutes. Not yet checked: whether `offline` appears briefly in between, which would make every entity flicker unavailable.
- **`sw_version` and `hw_version` are not part of the burst.** Both were last seen at 11:37:00, which is when HA started, 72 minutes before the first download. They may be retained, or the Board may send them only when a client connects. Not yet distinguished.
- **No unrecognised topics** (`unrecognised` is empty in both downloads).

## Third download (13:06 UTC)
- `hw_version` and `sw_version` arrived at 13:06:32, and a full burst followed at 13:06:41, nine seconds later. The burst is off the 13-minute cycle (the next one was due at 13:15:11), and 13:06:32 is the same kind of moment as 11:37:00, when HA started.
- **Hypothesis:** the versions arrive at once whenever the integration subscribes (retained messages), and the Board sends a full burst shortly after something happens at HA's end. Two HA starts or reloads, 9 seconds between versions and burst, would make the wait after a restart about 10 seconds instead of 13 minutes.
- **Not confirmed:** it is not known whether HA was restarted or the entry reloaded at 13:06 UTC, and the burst at the 11:37 start was overwritten before the first download. A reload of the entry while watching `r<n>` timestamps would confirm or refute this.

## Confirmed (user, 2026-11-07)
HA was restarted at about 13:06:32 UTC and diagnostics were downloaded as soon as the device was available. So the full burst arrives about 9 seconds after HA starts. **After an HA restart, Outputs and Inputs are known within about 10 seconds**, without any refresh command from the integration. The Board keeps republishing every 13 minutes regardless. What prompts the burst after a restart (HA's birth message, or the new subscription) is not known and does not matter for the integration.

## Consequence if the Board did not respond to a restart (not the case)
After an HA restart, an Output shows "unknown" for up to 13 minutes, until the next burst. Nothing is retained for `r<n>`, so HA cannot read it back on subscribing.

## Still open
- Refresh command: not needed, since the Board already publishes about 10 seconds after a restart.
- Is `lwt_availability` retained, and does it go `offline` between bursts?
- Are `sw_version` and `hw_version` retained? (Probably yes: they arrive at the same instant as the subscription.)
- Does the Board send a burst shortly after HA (re)subscribes, and what triggers it?
