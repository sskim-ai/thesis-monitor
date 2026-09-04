# 2026-09-04 US Live-Path E2E Success

The proof used the real US production entrypoint, packet builder output, claim/lease state machine, signed-in ChatGPT-bundled Codex CLI, V2 validator/finalizer, delivery adapter, and a dedicated non-production TEST sink. The database was an isolated copy under `/tmp`; production state was not mutated.

The first attempt completed the real xhigh model and validation path but the runtime quality gate stopped delivery before Telegram because valid structured numeric/transition templates were counted as substantive repetition. This was fail-closed: TEST sends were `0/15`. A bounded typed-template repair was committed, the exact accepted artifact was revalidated, and delivery resumed without a model rerun.

| Gate | Result |
|---|---|
| Packet | `2026-09-04-us-run-55-54cd536c6e4d` |
| Source ready | `15/15` |
| Primary claim acquired | `PASS` |
| Lease renewals | `444` |
| Backup while primary healthy | `SAFE_NOOP_PRIMARY_ACTIVE` |
| Signed-in xhigh stock results | `14/14` |
| Candidate | market `1` + stocks `14` |
| Final validation | `PASS` |
| TEST AI market sent | `1` |
| TEST AI stocks sent | `14` |
| TEST fallback sent | `0` |
| TEST duplicate sent | `0` |
| Production recipient sent | `0` |

A duplicate probe re-entered the same production delivery API. It failed closed on the persisted receipt/payload mismatch and sent zero additional messages. Raw TEST and production recipient IDs are not stored; only non-reversible aliases were audited, with collision count zero.
