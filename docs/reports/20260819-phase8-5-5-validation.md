# Phase 8.5.5 Validation

Date: 2026-08-19  
Branch: `codex/phase-8-5-5-natural-reasoning-ownership-repair`  
Base: `c6481d145ccc1583feaf6f6de7d005e774d56933`

## Scope

Phase 8.5.5 repairs reasoning ownership and repeated run-27 prose. It does not change numeric
calculations, RR formulas, support/resistance, fallback delivery, Scheduled Tasks, Telegram, Pilot,
DB schema, Knowledge, Phase 8.3, KRX experimental code, or Cash Flow features.

## Contract Results

| Gate | Result |
|---|---|
| domestic/non-depositary depositary prose | PASS, candidate suppressed and false-positive regex closed |
| verified depositary fixture | PASS, legitimate ratio prose remains eligible |
| `chart_risk_reward` industry ownership | PASS, 0 |
| price-context RR use | PASS when packet role authorizes it |
| POSCO industry framework | PASS, `steel_materials_valuation` retained |
| Hyundai Glovis industry framework | PASS, `shipping_transport_valuation` retained |
| Korean Re industry framework | PASS, `insurance_reinsurance_valuation` retained |
| run-27 full validator | PASS, 0 errors |
| numeric binding | PASS, automatic 117; manual/rejected/unresolved 0 |
| runtime message quality | PASS with existing thresholds |
| final rendered language | PASS |
| receipt verification | PASS |

## Regression

Focused tests cover domestic common, verified non-depositary, verified depositary, unknown and
conflict identity states; framework role mismatch and price-context controls; runtime specificity
ownership; current-price context; and run-27 replay. Full regression includes Phase 8.5.4.x night
futures, PBR ownership, CORZ typed valuation, fallback context parity, RR overlap, receipt, archive,
and exactly-once behavior.

## Command Validation

| Check | Result |
|---|---|
| Focused ownership/runtime/night-futures suite | 276 passed |
| Documentation plus core service suite | 177 passed |
| Full pytest | 1,084 passed, one third-party deprecation warning |
| Ruff | PASS |
| `git diff --check` | PASS |
| project-state JSON | PASS |
| relative documentation links | 0 broken |
| Investment Knowledge checksum parity | PASS, `559ad45e...` across 3 files |
| Chart Knowledge checksum parity | PASS, `beee6455...` across 2 files |
| Public Action | `0.4.5` |
| operationId | 20/20 unique |

Implementation SHA `2ac9091d2865727194d6cf5ae63c73fe0c1cc5e0` passed GitHub Actions run
`32234428454`, including Test and Lint. It was promoted to main and the clean operating checkout by
linear fast-forward. The API restart passed `/health`, and 276 operating smoke tests passed. All
four Scheduled Tasks remained ACTIVE at 08:15/08:30/16:15/16:55 KST with zero configuration change
and zero manual run.

## Safety

Manual Telegram 0; Scheduled Task execution/configuration 0/0; Pilot mutation 0; DB migration and
mutation 0; original run-27 archive/receipt rewrite 0; Production Assist OFF.

Retrospective replay does not close Natural AI-Assisted Delivery. The post-promotion state remains
`WAIT_FOR_NEXT_NATURAL_US_KR_PROOF`.
