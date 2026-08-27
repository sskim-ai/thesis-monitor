# KR Price Structure Repair Validation

## Lineage

| Item | SHA / Result |
| --- | --- |
| Exact instruction | `0a8dae7eeca7126844094f0aebcc7a7df0bea606` |
| Base | `43731f015901b96e2dee3af009b9e1d074382349` |
| Track A | `da82d89c2e1c3bc125442128da1573d532263d74` |
| Track B | `83f3d643bc2cb40d9039c1d965647d01a43769e2` |
| Integrated code | `04fb7ad7646a55e03000134f50b3f402a6c49c87` |
| Implementation Actions | run `33076166012`, Test/Lint PASS |

## Verification

| Gate | Result |
| --- | --- |
| Focused cash/price-structure suite | `109 passed` |
| Persistent documentation suite | `8 passed` |
| Full pytest | `1795 passed` |
| Full Ruff | PASS |
| `git diff --check` | PASS |
| Seven-ticker current replay | PASS |
| Current proximity validator | `7/7`, errors `0` |
| Old 000660 negative control | `FAIL_AS_EXPECTED` |
| Daily provider contract | `7/7 PARTIAL/provider_limit` |
| Synthetic/fallback daily bars | `0` |
| Look-ahead / partial-bar pivots | `0 / 0` |
| Local API health | PASS |

Full pytest emitted one upstream Starlette deprecation warning and no test failures.

## Compatibility

| Gate | Result |
| --- | --- |
| Investment Knowledge v3.1 | `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312` |
| Chart Knowledge v1 | `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5`, unchanged |
| Output schema | `4`, unchanged |
| operationId | `20/20` unique |
| KR TOP3 sector code diff | `0` |
| US Price Structure code diff | `0` |
| US market digest code diff | `0` |
| Runtime user-visible diff | `0` |

## Safety

Telegram sends, manual tasks, DB mutations, assessment mutations, archive rewrites, and feature
flag changes are all zero. `kr_market_sector_top3_enabled`, `kr_price_structure_v3_enabled`, and
Production Assist remain false. No operating promotion or service restart is authorized by this
repair.

## Result

`CODE_CORRECTNESS = PASS`

`KR_PRICE_STRUCTURE_REPAIR = REPLAY_PASS_READY_FOR_PREENABLE`

`OPEN_P0 = 0`

`OPEN_MATERIAL_P1 = 0`

`NEXT_ACTION = RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT`
