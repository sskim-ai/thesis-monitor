# M12CH Frozen-Contract New Full22 Reproof

## Result

- Outcome: `M12CH_FROZEN_CONTRACT_FULL22_REPROOF_PASS`
- Generation: `20260917-uskr22-m12ch-20260917T000529Z-65611727332a`
- Evidence assessment date: `2026-09-15`
- Fresh generation: yes
- Current-market collection: no
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Message-model contract readiness: `FULL22_REPROVEN_LOCAL_ONLY`
- Deployment readiness: `NO_BY_PHASE_BOUNDARY`

## Repository Freeze

- Required runtime base: `1e0d81695ce0982827a35a58b5123dfb86e066cc`
- Work-instruction commit: `fa0b645cdc2c84c201ba7d46b3d60027f15e4861`
- Harness freeze commit: `65611727332a4198c24eba0fb1a0f41f382bbf3d`
- Runtime tree SHA-256: `f66f345e3d49ab21d169acd056330342f1609a6c7738020fca1fbc7710b86263`
- Runtime source drift: `0`
- Formal summary SHA-256: `86b70166df85f2e4cd6fbe50b5c2b432c9ad406b2089c49db1209adbe88a41c0`
- Application/runtime/config semantic changes: `0`

The strict package verifier passed 35 package payloads, 11 source bundles, and
1,455 source payloads. The frozen US packet retained whole-file SHA-256
`2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228`;
the KR packet retained
`819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597`.

## Premodel Gate

- Package/base/runtime freeze: PASS
- Full packet and subject-order binding: PASS, US14 + KR8
- Planned call topology: PASS, 16 calls
- Independent Core to finalizer to service-reader/native-consumer control: PASS
- Focused premodel regression: PASS
- Signed-in Codex CLI configuration: PASS without a model probe
- External model calls before formal generation: `0`

Eight historical M12CE unbound Stage-2 schema hashes differ from the current
base because the current contract defers the atomic-claim enum until a new Core
exists. That unbound control is not sent to the model. Core model-facing hashes
matched, and every actual bound Stage-2 prompt/schema/catalog was frozen after
its new Core and before its Stage-2 call. Actual model-facing contract drift was
`0`.

Two setup diagnostics stopped before any model call: one used a package folder
that had been polluted by analysis-only extracted subdirectories, and one
incorrectly treated the historical unbound schema control as model-visible.
Both proof-harness issues were corrected, recommitted, and fully retested before
the formal generation began.

## Formal Full22

| Boundary | Result |
|---|---:|
| Planned / started / completed / usable calls | 16 / 16 / 16 / 16 |
| Fundamental Core accepted | 22 / 22 |
| Raw Stage-2 contract accepted | 22 / 22 |
| Materialized Stage-2 candidates | 22 / 22 |
| Semantically accepted Stage-2 candidates | 22 / 22 |
| Accepted plans finalized | 22 / 22 |
| Rendered blocks | 22 / 22 |
| Composed shadow messages | 22 / 22 |
| Native readbacks | 22 / 22 |
| Independent Core references | 22 / 22 |

US finished 14/14 and KR finished 8/8. Every Core-stage response was frozen
separately before Stage-2. Finalization and readback used independently loaded
Core freeze files rather than the Core copies embedded in tested Stage-2 output.

## Contract Safety

All of the following counts were zero:

- model-authored `as_of`
- model-authored `provenance_status`
- exact-ref violations
- provenance projection violations
- maturity atomic-identity failures
- Stage-2-owned exact numeric violations
- Stage-2-owned unsupported metric failures
- preconfirmation contract failures
- wrapper retries, fallback, judge, repair, schema repair, candidate repair
- selective or per-ticker reruns
- prior-output reuse or cross-generation stitching

Raw Stage-2 remained `v2-accepted-stage2-model-output-v2`. Runtime
normalization remained `stage2-maturity-as-of-deterministic-v2`, using
`LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE` and
`MAX_CONCRETE_OWNED_DATES`.

## Observed Decisions

These are newly generated observations, not expected-label assertions:

| Market | Ticker | Decision | Maturity | New buyer | Holder |
|---|---|---|---|---|---|
| US | CORZ | HOLD | MIXED | WAIT | REVIEW |
| US | CPNG | HOLD | MIXED | WAIT | REVIEW |
| US | CRCL | SELL | MIXED | AVOID | REVIEW |
| US | GOOGL | BUY | PARTIAL | WAIT | HOLDABLE |
| US | HUT | SELL | EARLY | AVOID | REVIEW |
| US | IBM | HOLD | MIXED | WAIT | HOLDABLE |
| US | MU | BUY | PARTIAL | WAIT | HOLDABLE |
| US | RXRX | SELL | MIXED | AVOID | REVIEW |
| US | SKHY | HOLD | MIXED | WAIT | REVIEW |
| US | SNDK | HOLD | MIXED | WAIT | REVIEW |
| US | TSLA | SELL | MIXED | AVOID | REVIEW |
| US | TSM | HOLD | MIXED | WAIT | HOLDABLE |
| US | WRD | HOLD | MIXED | WAIT | REVIEW |
| US | WULF | SELL | MIXED | AVOID | REVIEW |
| KR | 000660 | SELL | MIXED | AVOID | REVIEW |
| KR | 003690 | BUY | PARTIAL | WAIT | HOLDABLE |
| KR | 005490 | HOLD | MIXED | WAIT | REVIEW |
| KR | 005930 | HOLD | MIXED | WAIT | REVIEW |
| KR | 010120 | HOLD | PARTIAL | WAIT | HOLDABLE |
| KR | 012450 | BUY | PARTIAL | WAIT | HOLDABLE |
| KR | 047810 | HOLD | MIXED | WAIT | REVIEW |
| KR | 086280 | SELL | MIXED | AVOID | REVIEW |

Distribution: BUY 4, HOLD 11, SELL 7. No prior-generation answer was used as
an expected label.

## Validation

- Proof-critical focused: `306 passed, 1 skipped`
- Full pytest: `4,154 passed, 63 skipped, 2 warnings`
- Treasury frozen suite: `79 passed, 2 warnings`
- Kiwoom frozen suite: `70 passed`
- Ruff: PASS
- `git diff --check`: PASS

The full-suite increase from the R4-R1 baseline of 4,151 passes is exactly the
three new proof-harness tests. Skip count is unchanged at 63.

## Safety And Completion Layers

- Closed designs and repairs: `CARRIED_FORWARD_AT_DOCUMENTED_SCOPE`
- Offline acceptance: `PASS`
- Offline operations: `PASS`
- Fresh Full22: `PASS`
- Deployment authorization: `NOT_AUTHORIZED`
- Production DB/assessment/warning/notification mutations: `0`
- Production sends: `0`
- Scheduler changes: `0`
- Main merges, deployments, remote pushes: `0`

The existing at-least-once crash-after-send/before-cursor limitation remains
documented. Kiwoom gateway verification, current US/KR market smoke, independent
human comparison, and any deployment decision remain later Chat-controlled
steps.
