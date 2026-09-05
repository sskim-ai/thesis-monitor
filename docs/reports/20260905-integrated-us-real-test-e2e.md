# Integrated US Real TEST E2E

The integrated branch ran the production-equivalent US claim path against an isolated SQLite copy and the dedicated non-production TEST sink. Signed-in Codex CLI produced and accepted all 14 stock decisions with `gpt-5.6-sol / xhigh` while heartbeat and fencing remained intact.

The first finalization stopped before delivery because the immutable Run-57 daily candidate contained two legacy valuation sentences whose prose no longer matched their structured exact spans. The bounded repair restored only the uniquely identified canonical spans for RXRX and WULF. An offline replay then passed with zero errors. A same-claim continuation reused the accepted 14-subject receipt and performed no model rerun.

| Gate | Result |
|---|---|
| Packet | `2026-09-05-us-run-57-1fbbf143dbc5` |
| Model / effort | `gpt-5.6-sol / xhigh` |
| V2 ready / accepted | `14/14` |
| Lease renewals / fencing | `58 / PASS` |
| Continuation | `SAME_CLAIM_AFTER_PRE_SEND_VALIDATOR_REPAIR` |
| Full model rerun during continuation | `0` |
| Validator | `completed` |
| TEST market / explicit V2 stocks | `1 / 14` |
| Compatibility / pilot / fallback / duplicate | `0 / 0 / 0 / 0` |
| TLS UnknownIssuer | `0` |
| Production recipient / DB / scheduler | `0 / 0 / 0` |

The natural-proof test gate passes. The TEST sink differs from production; no raw recipient identifier is stored in the artifact.
