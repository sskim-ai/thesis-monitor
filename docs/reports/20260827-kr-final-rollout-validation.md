# KR Final Rollout Validation

## Lineage

| Item | SHA / Result |
| --- | --- |
| Supplied ZIP SHA-256 | `02a36422f52f1558b5eaac5d7b3803ebe01560842b1978e4db5922b7f88ee496` |
| Exact instruction commit | `9f37cfad97487876d6dfa63c03750f4dab664dbf` |
| Base / previous final main | `0ede6a0eb3335371322d1f7921b350d07f669f9a` |
| Track A evidence | `05b57901f7cf25086b580510aac6a6e72329cdfc` |
| Track A Actions | run `33085141564`, Test/Lint PASS |
| Previous and current operating | `43731f015901b96e2dee3af009b9e1d074382349` |

The four committed instruction files are byte-identical to the supplied archive entries. Track B
and Track C did not start because Track A could not prove an available dedicated test sink.

## Verification

| Gate | Result |
| --- | --- |
| Focused documentation/sink suites | `14 passed` |
| Full pytest | `1803 passed`, one upstream Starlette warning |
| Full Ruff | PASS |
| `git diff --check` | PASS |
| Project-state JSON | PASS |
| Readiness/delivery/per-ticker JSON | PASS |
| Required Markdown reports | `18/18` |
| Required machine-readable reports | `3/3` |
| Runtime module diff | `0` |
| User-visible behavior diff | `0` |

## Compatibility

| Gate | Result |
| --- | --- |
| Investment Knowledge v3.1 | `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312` |
| Chart Knowledge v1 | `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5`, unchanged |
| Output schema | `4`, unchanged |
| operationId | `20/20` unique |
| Local API `/health` | PASS (`status=ok`) |
| OHLCV provider data request | `NOT_RUN_TRACK_A_BLOCKED` |

## Safety

Current settings preserve `kr_market_sector_top3_enabled=false`,
`kr_price_structure_v3_enabled=false`, AI review mode `shadow`, and Production Assist OFF. The
operating worktree is clean at `43731f015901b96e2dee3af009b9e1d074382349`.

Provider requests, Telegram sends, production delivery intents, manual production tasks, service
restarts, feature-flag writes, operating promotion, Pilot/DB/assessment mutations, and archive
rewrites are all zero.

## Result

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 1
KR_FINAL_PREENABLE = BLOCKED
KR_FINAL_PREENABLE_DETAIL = BLOCKED_NO_TEST_SINK
KR_ROLLOUT = NOT_ENABLED
NEXT_ACTION = CONFIGURE_APPROVED_DEDICATED_TEST_SINK_AND_RERUN_TRACK_A
```
