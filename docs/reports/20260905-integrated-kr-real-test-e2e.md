# Integrated KR Real TEST E2E

The integrated branch ran the real KR claim, signed-in Codex CLI, bounded batch/subject repair, heartbeat, fencing, finalizer, delivery adapter, and Telegram transport against an isolated SQLite copy and the dedicated non-production TEST sink.

| Gate | Result |
|---|---|
| Packet | `2026-09-04-kr-run-56-6a9ef43bb878` |
| Model / effort | `gpt-5.6-sol / xhigh` |
| V2 ready | `8/8` |
| Candidate / accepted | `9/9` including market |
| Lease renewals / fencing | `24 / PASS` |
| Healthy backup | `SAFE_NOOP_PRIMARY_ACTIVE` |
| Validator | `completed` |
| TEST market / explicit V2 stocks | `1 / 8` |
| Pilot / fallback / duplicate | `0 / 0 / 0` |
| UnknownIssuer | `0` |
| Production recipient / DB / scheduler | `0 / 0 / 0` |

The natural-proof test gate and existing KR accounting/valuation safety gates pass. No raw recipient identifier is stored. The earlier exploratory run was interrupted before delivery after exposing a source-ref naming ambiguity; its target rows remained unsent. This final run uses the repaired source-root contract.
