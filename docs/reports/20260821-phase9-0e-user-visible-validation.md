# Phase 9.0E User-Visible Validation

## Replay

- Run-30 SELECTIVE replay: selected `9/13`; AI/fallback parity PASS.
- Archive AI preview: semantic PASS; final language PASS; runtime quality PASS.
- Cash-flow binding: automatic `9`, manual `0`, rejected `0`, unresolved `0`.
- Repeated substantive sentences `0`; repeated template skeletons `0`.
- Same numeric Fact used three or more times `0`; exact FCF owner is `business_earnings`.
- Run-29 KR negative replay: cash-flow selection/injection `0/7`.
- OFF replay: cash-flow selection/injection `0/13`.

## Semantic Controls

Fixtures reject future/stale or non-current formal use, OCF-only exposure, incomplete lineage,
non-PPE CAPEX scope, period/entity/basis/currency mismatch, wrong numeric owner, missing fiscal/YTD
label, management-FCF mislabel, resolved missing-FCF Unknown, FCF valuation ownership, FCF yield or
per-share metrics, ROIC/CCC/DSO/DPO, and suppressed-context Fact use.

Fixtures allow issuer-level foreign-currency FCF, positive/negative FCF, non-calendar fiscal labels,
and unrelated legacy ROIC prose when cash-flow user-visible context is suppressed. Missing remains
missing; no zero or security currency is synthesized.

## Baseline Consistency

AI and fallback audit the same core thesis, assessment summary, and warning groups. TSLA suppresses
four claim occurrences from the one Phase 9.0D.1 root family. Cross-path suppression identity
mismatches are `0`; unresolved baseline conflicts suppress user-visible enrichment.

## Tests

- Phase 9.0E and related AI/fallback/canary focused suite: `396 passed`.
- Full pytest: `1264 passed`, one upstream Starlette deprecation warning.
- Ruff full repository: PASS.
- `git diff --check`: PASS.
- Investment Knowledge v3 SHA: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Chart Knowledge v1 SHA: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.
- Public Action: `0.4.5`; operationId: `20/20` unique; output schema: `4`.
- Implementation SHA: `cf3194981124de2a6f85fbe81b145ef06e1db08d`.
- Implementation Actions run: `32443322364` (exact result recorded before promotion).

No validator threshold is relaxed. Public Action, schema, fallback exactly-once ownership, four AI
task definitions, KRX telemetry, DB schema, Pilot, and Production Assist are unchanged.

