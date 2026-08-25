# Kiwoom Live Probe

## Result

`KIWOOM_LIVE_PROBE = PASS`

- Session: `2026-08-25`
- Observed: `2026-08-25T23:15:38.856491+09:00`
- Source payload SHA-256: `44665b1b28dc8998066f12a58e01e5b29e6a812cfd208f9658617aba2b377818`
- Final deterministic collection: `42` requests,
  `42` successes, `0` failures,
  `0` retries.
- Whole task read-only live activity: 94 successful HTTP requests, including four OAuth requests
  and 90 TR requests; provider failure 0 and cache hit 0.

The 94-call total includes the initial contract probe (40), a separate historical-session proof
(3), an eight-TR local normalization attempt plus token (9), and the final evidence collection
(42). The local failed attempt was an aggregate identity normalization error after successful
provider responses; no invalid output was promoted.

No account, order, Telegram, Scheduled Task, Pilot, or DB mutation call was made.
