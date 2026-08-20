# Phase 9.0C Complete Report Bundle

# Phase 9.0C Comparable-Period Audit

- Safe metric relations: `25`
- Contexts with at least one safe comparison: `9`
- Suppressed comparison attempts: `11`
- Mixed YTD/FY or unequal-duration comparisons used: `0`
- Percentage growth generated: `0`

Relations are sign-aware (`positive higher/lower`, `negative less/more negative`, and sign transitions) and never produce a backend good/bad verdict.


---

# Phase 9.0C Freshness Audit

No day-count threshold is introduced. Freshness is period alignment against Phase 9.0A official formal evidence and newer validated preliminary periods.

| State | Count |
|---|---:|
| CURRENT_FORMAL | 10 |
| FORMAL_LAGGING_PROVISIONAL | 2 |
| STALE_FORMAL | 0 |
| FORMAL_ALIGNMENT_UNAVAILABLE | 0 |
| BLOCKED | 7 |
| NOT_APPLICABLE | 1 |

| Ticker | Industry | Canonical | Freshness | Usage | Rendered | Suppression |
|---|---|---|---|---|---|---|
| 000660 | memory_semiconductor | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 003690 | insurance_reinsurance | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NO | financial_industry_not_applicable |
| 005490 | steel_materials | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 005930 | memory_semiconductor | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 010120 | industrial_epc | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 012450 | aerospace_epc | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 086280 | transport_logistics | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| CORZ | hpc_data_center | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| CRCL | general_non_financial | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| GOOGL | cloud_platform_software | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| HUT | hpc_data_center | PARTIAL | CURRENT_FORMAL | OCF_ONLY_CONTEXT | YES | - |
| IBM | cloud_platform_software | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| MU | memory_semiconductor | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| RXRX | biotech | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| SKHY | memory_semiconductor | BLOCKED | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| SNDK | memory_semiconductor | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| TSLA | automotive | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| TSM | memory_semiconductor | ELIGIBLE | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO | newer_provisional_period_not_cash_flow_aligned |
| WRD | general_non_financial | ELIGIBLE | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO | newer_provisional_period_not_cash_flow_aligned |
| WULF | hpc_data_center | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |

TSM and WRD remain `LATEST_FORMAL_CONTEXT_ONLY` because a later preliminary period exists. They are not rendered as current. KR period-context cases and SKHY remain blocked; Korean Re remains not applicable.


---

# Phase 9.0C Industry Reasoning Audit

- Shadow prose rendered: `10` subjects
- Full FCF context: `9`
- OCF-only context: `1`
- Cash-flow numeric triples rendered: `0`
- Automatic thesis/valuation changes: `0`

Cloud/platform, software/services, memory, HPC/data-center, biotech, automotive, stablecoin-platform, and OCF-only project contexts use separate economic mechanisms. Negative biotech FCF remains cash-burn evidence without inferred runway; HPC build-out FCF is not mislabeled as operating cash burn; memory FCF is not promoted to permanent cycle quality.


---

# Phase 9.0C Point-in-Time Audit

Contract: `cash-flow-shadow-consumption-v1`. Replay cutoff: `2026-08-20`.

- Canonical facts inspected: `606`
- Future-filing facts consumed: `0`
- Point-in-time exclusions: `0`
- Missing source-date facts consumed: `0`
- Derived facts with unavailable PIT inputs consumed: `0`

Source availability is the official filing date, never the Phase 9.0B canonicalization time. Synthetic future-filing and missing-input controls are covered by the focused test suite.


---

# Phase 9.0C Readiness

- Open P0: `0`
- Open P1: `0`
- PIT/freshness/comparison/numeric/semantic/runtime-quality gates: `PASS`
- User-visible diff: `0`
- KR OpenDART period recovery priority: `MEDIUM`
- CCC: `DEFERRED`
- Standard ROIC: `DEFERRED`

`PHASE_9_0D_READY = YES`

`PHASE_9_0D_SCOPE = SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY`


---

# Phase 9.0C Shadow AI Preview

Archive-only candidate derived from the repaired run-28/run-29 baselines plus the cash-flow sidecar. Telegram send: `0`.

| Ticker | Freshness | Usage | Human result | Primary Fact |
|---|---|---|---|---|
| 000660 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 003690 | NOT_APPLICABLE | NOT_APPLICABLE | MINOR_IMPROVEMENT | - |
| 005490 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 005930 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 010120 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 012450 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 086280 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| CORZ | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:1b8f3742f33dd3b66f8f7673 |
| CRCL | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:402041c63553616360d17391 |
| GOOGL | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:ddb47708bf7d36a4c0b0c7d2 |
| HUT | CURRENT_FORMAL | OCF_ONLY_CONTEXT | MINOR_IMPROVEMENT | cashflow-reported:d046f43a5cbb928c6aa1fdd1 |
| IBM | CURRENT_FORMAL | FULL_FCF_CONTEXT | MINOR_IMPROVEMENT | cashflow:a158304539a9269c66f6d2cb |
| MU | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:96e9c3b873f3678d4dec0ff3 |
| RXRX | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:498c289d4304c0822d861ec3 |
| SKHY | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| SNDK | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:1b8db0b46c63ae9369231151 |
| TSLA | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:68666c261434dab50ab88a8d |
| TSM | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | MINOR_IMPROVEMENT | cashflow:f5f8d7130aaff3c4a0f0a2a1 |
| WRD | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO_MEANINGFUL_CHANGE | cashflow:46c15133a15f9cb2c4b839c1 |
| WULF | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:6fd003ea029e4d7b03f681f3 |

## Numeric And Semantic Safety

- Automatic cash-flow bindings: `10`
- Manual/rejected/unresolved: `0/0/0`
- Semantic validation errors: `0`
- Status delta candidates: `0`; persisted: `0`

## Message Quality

- Run-28 baseline hard checks: `True`
- Run-28 enriched hard checks: `True`
- Run-29 negative-control hard checks: `True`
- Average stock-message length change: `3.66%`

The bounded increase comes from 10 selectively rendered contexts, not a 20-stock numeric dump.
Substantive repetition, typed skeleton repetition, generic Unknown, and generic next-check counts
remain zero; no subject is classified `DEGRADED`.


---

# Phase 9.0C Shadow Before / After

Boundary: archive-only. Production packet and Telegram output remain unchanged.

## 003690 - MINOR_IMPROVEMENT

**Before**

2026년 2분기 연결 기준 영업이익 1,750억원만 기간·연결 기준이 확인된 금액으로 표시합니다. 비교 가능한 매출·마진과 현금흐름이 없어 언더라이팅 수익성의 방향은 확정하지 않습니다.

**After**

2026년 2분기 연결 기준 영업이익 1,750억원만 기간·연결 기준이 확인된 금액으로 표시합니다. 비교 가능한 매출·마진과 현금흐름이 없어 언더라이팅 수익성의 방향은 확정하지 않습니다.

**Unknown after**

합산비율, 자기자본이익률과 자본적정성의 동행은 여전히 미확인입니다.

## CORZ - MATERIAL_IMPROVEMENT

**Before**

2026년 2분기 매출 $164.2M; 코로케이션 매출이 대규모 투자 이후 현금창출로 이어지는지를 확인해야 하며, 비교 성장률과 OCF·CAPEX·FCF가 안전하게 연결되지 않아 성장의 질은 미확인입니다.

**After**

2026년 2분기 매출 $164.2M; 2026 회계연도 상반기 누계 잉여현금흐름(OCF-PPE CAPEX 기준)은 $-723.3M로 음수입니다. build-out 재투자를 사업 실패로 자동 해석하지 않고 코로케이션 가동·청구, 자금조달을 함께 확인하며, 전년 비교기간보다 적자 폭이 커졌고 OCF와 PPE 재투자의 기여를 나눠 봐야 합니다.

**Unknown after**

가동 전력의 청구 전환, 코로케이션 마진과 희석 경로는 여전히 미확인입니다.

## CRCL - MATERIAL_IMPROVEMENT

**Before**

2026년 1분기 매출 $41.62M; 이 매출만으로 준비금 수익, 비이자 매출, 수익배분과 FCF의 질을 확정할 수 없습니다.

**After**

2026 회계연도 상반기 누계 잉여현금흐름(OCF-PPE CAPEX 기준)은 $528.12M로 양수입니다. 준비금 수익과 비이자 플랫폼 수익의 현금전환을 분리해 확인하며, 전년 비교기간보다 늘었지만 이를 구조적 개선으로 자동 확정하지 않습니다. 기존 손익 문맥과 기간이 달라 매출·마진 변화와 직접 연결하지 않습니다.

**Unknown after**

USDC 점유율, 비이자 수익과 수익배분의 지속성은 여전히 미확인입니다.

## GOOGL - MATERIAL_IMPROVEMENT

**Before**

Search monetization, Cloud 성장·마진, CAPEX와 FCF의 변화는 제공된 실적만으로 확정할 수 없습니다.

**After**

2026 회계연도 상반기 누계 잉여현금흐름(OCF-PPE CAPEX 기준)은 $4.26B로 양수입니다. AI·Cloud 투자 회수는 Cloud 성장과 마진을 함께 봐야 하며, 전년 비교기간보다 줄었지만 OCF와 재투자 변화를 분리해야 합니다.

**Unknown after**

Cloud 성장·마진과 AI 투자 회수의 지속성은 여전히 미확인입니다.

## HUT - MINOR_IMPROVEMENT

**Before**

새로운 해석 가능한 실적 숫자가 없어 제한 없는 현금, 프로젝트 투자, OCF와 FCF의 변화를 확정할 수 없습니다.

**After**

2026 회계연도 상반기 누계 영업현금흐름은 $-32.84M로 확인되지만 검증된 PPE 취득 현금지출이 없어 잉여현금흐름은 계산하지 않습니다. 계약 가동·NOI와 프로젝트 자금조달을 함께 확인해야 합니다. 기존 손익 문맥과 기간이 달라 매출·마진 변화와 직접 연결하지 않습니다.

**Unknown after**

제한 현금과 자유현금, 프로젝트별 투자와 모회사 지분 투입의 구분이 부족합니다.

## IBM - MINOR_IMPROVEMENT

**Before**

2026년 2분기 매출 $17.16B; 이 실적은 Software·Consulting의 질과 FCF 개선을 함께 확인해야 의미가 커집니다.

**After**

2026년 2분기 매출 $17.16B; 2026 회계연도 상반기 누계 PPE-only 잉여현금흐름은 $7.3B로 양수입니다. 회사 정의 FCF와 혼동하지 않고 Software·Consulting 전환과 함께 해석하며, 전년 비교기간보다 늘었지만 이를 구조적 개선으로 자동 확정하지 않습니다.

**Unknown after**

AI 관련 매출의 수익성, Consulting backlog 전환과 증분 ROIC가 미확인입니다.

## MU - MATERIAL_IMPROVEMENT

**Before**

2026년 3분기 매출 $41.46B; 이 실적은 DRAM·NAND ASP, HBM 믹스, CAPEX와 FCF를 함께 보지 않으면 사이클 이익의 질을 확정할 수 없습니다.

**After**

2026년 3분기 매출 $41.46B; 2026 회계연도 3분기 누계 PPE 재투자 후 잉여현금흐름은 $26.1B로 양수입니다. ASP·HBM 믹스·재고 사이클과 CAPEX 시점을 분리해 지속성을 판단하며, 전년 비교기간보다 늘었지만 이를 구조적 개선으로 자동 확정하지 않습니다.

**Unknown after**

ASP·HBM 믹스·재고와 사이클 현금창출의 지속성은 여전히 미확인입니다.

## RXRX - MATERIAL_IMPROVEMENT

**Before**

2026년 2분기 매출 $7.67M; 이 매출만으로 임상 진행·파트너 지급과 현금소진을 판단할 수 없습니다.

**After**

2026년 2분기 매출 $7.67M; 2026 회계연도 상반기 누계 잉여현금흐름(OCF-PPE CAPEX 기준)은 $-187.35M로 음수이며 현금소진 근거로만 사용합니다. 보유현금·milestone·조달 근거 없이 runway를 계산하지 않으며, 전년 비교기간보다 적자 폭이 줄었지만 현금소진이 끝났다는 뜻은 아닙니다.

**Unknown after**

임상 일정·milestone·보유현금과 추가 조달 필요 시점은 여전히 미확인입니다.

## SNDK - MATERIAL_IMPROVEMENT

**Before**

2026년 연간 매출 $20.25B; 이 매출만으로 NAND ASP·데이터센터 매출·재고와 FCF의 동행을 확정할 수 없습니다.

**After**

2026년 연간 매출 $20.25B; 2026 회계연도 연간 PPE 재투자 후 잉여현금흐름은 $11.49B로 양수입니다. NAND ASP·데이터센터 수요·재고와 설비투자 시점을 분리해 지속성을 판단하며, 비교 가능한 전년 현금흐름 없이 단일기간 수치만으로 구조 변화를 확정하지 않습니다.

**Unknown after**

NAND ASP·데이터센터 수요·재고와 사이클 현금창출의 지속성은 여전히 미확인입니다.

## TSLA - MATERIAL_IMPROVEMENT

**Before**

자동차 가격·믹스, 영업마진, 재고, CAPEX와 FCF의 질을 확정할 수 없습니다.

**After**

2026 회계연도 상반기 누계 PPE 재투자 후 잉여현금흐름은 $352M로 양수입니다. 자동차 마진과 성장투자 회수를 함께 보고 단일 현금흐름으로 신사업 논리를 무효화하지 않으며, 전년 비교기간보다 줄었지만 OCF와 재투자 변화를 분리해야 합니다.

**Unknown after**

자동차 마진·재고와 성장투자 회수 속도는 여전히 미확인입니다.

## TSM - MINOR_IMPROVEMENT

**Before**

2026년 2분기 매출 NT$1.27T; 2026년 2분기 영업이익 NT$766.6B; 2026년 2분기 영업이익률 60.3%; TWD 기준의 잠정 매출·영업이익·마진은 확인되지만 OCF·CAPEX·FCF·재고·ROIC를 증명하지 않으며 미국 상장 증권 가격과 환산하지 않습니다.

**After**

2026년 2분기 매출 NT$1.27T; 2026년 2분기 영업이익 NT$766.6B; 2026년 2분기 영업이익률 60.3%; TWD 기준의 잠정 매출·영업이익·마진은 확인되지만 OCF·CAPEX·FCF·재고·ROIC를 증명하지 않으며 미국 상장 증권 가격과 환산하지 않습니다.

**Unknown after**

최신 잠정 실적 기간과 정렬되는 정식 OCF·PPE CAPEX·FCF가 없어 첨단공정 수요·마진과 투자 회수의 현재 방향은 아직 판단하지 않습니다.

## WULF - MATERIAL_IMPROVEMENT

**Before**

HPC lease 매출, 가동 전력, EBITDA, OCF·CAPEX·FCF와 희석 변화를 확정할 수 없습니다.

**After**

HPC lease 매출, 가동 전력, EBITDA, OCF·CAPEX·FCF와 희석 변화를 확정할 수 없습니다; 2026 회계연도 상반기 누계 잉여현금흐름(OCF-PPE CAPEX 기준)은 $-1.53B로 음수입니다. build-out 재투자를 사업 실패로 자동 해석하지 않고 HPC lease 가동 전력·청구, 자금조달을 함께 확인하며, 전년 비교기간보다 적자 폭이 커졌고 OCF와 PPE 재투자의 기여를 나눠 봐야 합니다.

**Unknown after**

가동·건설 전력의 lease 매출 전환과 남은 자금조달·희석 경로는 여전히 미확인입니다.


---

# Phase 9.0C Unknown-Resolution Audit

- Generic cash-flow Unknowns before: `17`
- Resolved: `8`
- Still valid: `8`
- Suppressed as not applicable: `1`
- Fresh FCF plus contradictory missing claim: `0`
- Wrongly suppressed blocked-case Unknowns: `0`

Eligible current facts move the question to industry-specific durability. OCF-only cases identify the missing PPE-CAPEX basis. Lagging formal cases ask for cash flow aligned to the newer preliminary period. Insurance does not repeat generic enterprise FCF as an Unknown.


---

# Phase 9.0C Validation

- PIT/freshness/comparison shadow validators: PASS
- Cash-flow numeric binding: `10` automatic; manual/rejected/unresolved `0/0/0`
- Run-28 archive shadow runtime quality: `PASS`
- Run-29 KR blocked negative control: `PASS`; cash-flow numeric injection `0`
- User-visible packet/prompt/renderer/Public Action/fallback diff: `0`
- Public Action `0.4.5`; schema `4`; CCC/ROIC remain deferred
- Canonical-core plus shadow focused suite: `84 passed`
- Full pytest: `1213 passed`, one existing Starlette/httpx deprecation warning
- Ruff / `git diff --check`: `PASS / PASS`
- Knowledge checksums / documentation links / Public Action / operationId 20/20: `PASS`
- Production packet/API/job imports of the Phase 9.0C service: `0`
- Exact final-SHA Actions Test/Lint: required before main promotion; resolved from GitHub Actions
