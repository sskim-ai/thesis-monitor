# Phase 7 Stateful Monitoring and Peer Valuation Validation

Date: 2026-08-14  
Base: `aeae616cda18bd610a7da1ea2fbcf2eb349d883d`  
Policy: `daily-review-v3.8`  
Output schema: 4  
OHLCV: `ohlcv-structure-v2`

## Existing Persistence Audit

| Field | Before storage | After storage |
|---|---|---|
| Current price | `ThesisAssessment.price_context.decision` | Same canonical field plus monitoring snapshot |
| Registered confirmation/support/warning/invalidation | `InvestmentThesis.price_rules` | Preserved; lifecycle/relevance copied into snapshot |
| Dynamic support/resistance | `price_context.chart.structure.zones` | Stable selected zone snapshot plus original chart audit |
| Dynamic RR/invalidation/chart state | `price_context.chart.structure` | Current/previous/delta summary plus original chart audit |
| 1d/5d/20d supply | `price_context.supply` | Raw values preserved plus derived horizon states |
| Current and forward valuation | `valuation_snapshot` | Raw snapshot preserved plus monitoring valuation state |
| Historical percentiles | `valuation_snapshot` | Current/previous percentile delta added |
| Peer valuation | Not available | Fail-closed peer state and full inclusion/exclusion audit |
| Market expectations | `market_expectation_assessment` | Current state copied for one-packet interpretation |
| Macro impact | `valuation_context` / macro impact rows | Selected current effect copied into monitoring state |
| AI packet/chart/Telegram | Pilot archive | Unchanged; new packet includes monitoring state |

No raw OHLCV bars are duplicated. The durable object is stored backward-compatibly under
`ThesisAssessment.price_context.monitoring_state`, so no migration or Public Action change is needed.
`getThesisAssessmentHistory` already reads `PriceContext`, and regression tests prove the state and
delta survive that read path. The retrospective did not backfill the live 2026-08-14 DB.

## Price State Lifecycle

Hyundai Glovis regression:

| Date | Close | Confirmation state | PER | PBR | PER percentile | PBR percentile |
|---|---:|---|---:|---:|---:|---:|
| 2026-08-12 | 199,700 | not reached | 9.7184 | 1.4469 | 88.0 | 86.2 |
| 2026-08-13 | 204,500 | crossed | 9.9520 | 1.4817 | 90.0 | 88.1 |
| 2026-08-14 | 211,000 | holding above | 10.2683 | 1.5288 | 92.8 | 91.6 |

The confirmation crossing is dated 2026-08-13. It is a transition reference, not an automatic
support. The original 176,000~180,000 support remains in thesis history but is
`superseded_for_current_structure` in the 8/14 user context.

## Dynamic Price Structure

For Hyundai Glovis on the immutable 8/14 close:

| Item | Deterministic result |
|---|---|
| Current price | 211,000 KRW |
| Active support | 197,803.342808~210,196.657192, Weekly, Medium |
| Active resistance | 223,397.262374~230,602.737626, Daily, Medium |
| Current-price RR | 0.466189 |
| Chart invalidation | 184,407.225784, Weekly support scenario |
| Chart state | WAIT, Medium confidence; rendered as price context, not a command |
| Registered confirmation | 200,000, holding above, transition reference |

The target is the nearest eligible resistance lower bound. The registered 176,000 invalidation is
not used as chart invalidation or to improve RR.

## Supply

Hyundai Glovis verified supply:

| Horizon | Foreign | Institution | State |
|---|---:|---:|---|
| 1 day | +10,613 | +18,617 | joint buying |
| 5 days | +124,950 | -115,230 | mixed |
| 20 days | +174,664 | +218,751 | joint buying |

The derived transition is `short_term_divergence`: medium-term joint accumulation remains, while
recent institutional positioning weakened. Raw values remain authoritative.

## Peer Valuation

Provider inventory:

| Source | Status |
|---|---|
| Broad KR point-in-time peer valuation | unavailable |
| Broad US point-in-time peer valuation | unavailable |
| Same-date active monitored assessments | available, limited |
| Forward P/E, EV/EBITDA, FCF yield, ROE peer series | unavailable |

The limited provider groups by verified taxonomy, then industry, then sector, within the same
geography. It requires at least three peers excluding the company and validates positive EPS/BVPS,
metric status, security/share basis, same-date price, and non-future denominator filing. Biotech P/E
is not forced. Median is primary;
mean, interquartile bounds, sample count, included peers, and exclusions are audit metadata.

On 2026-08-14 there were 20 active final assessments and zero peer states met the full metric
contract. Hyundai Glovis therefore has no peer median or premium. No web value or invented industry
average was added.

## Historical Percentile

The validator rejects forms such as `92.8% 고평가`. The compact supported meaning is:

> PER 92.8백분위는 현재 PER가 비교 가능한 과거 관측치의 약 92.8%보다 높은 수준이라는
> 뜻이지, 92.8% 고평가됐다는 뜻은 아닙니다.

Historical rank, current absolute multiple, and peer-relative valuation remain distinct dimensions.

## Hyundai Glovis Before / After

Before price/supply/valuation excerpt:

> 현재가 211,000원은 상향 확인 가격 200,000원 위지만 가까운 저항과 불리한 차트
> 손익비 때문에 관망 상태다. 당일과 20일 공동 순매수는 우호적이다. 현재 PER 10.27배,
> PBR 1.53배, PER/PBR 역사적 백분위 92.8%/91.6%다.

Problems: no dynamic level numbers, no RR number, 5-day institutional divergence omitted,
confirmation remained the primary level, percentile meaning was unexplained, and peer availability
was unstated.

After dry-run:

> 현재가 211,000원입니다. 200,000원 확인선은 8월 13일 상향 돌파됐고 현재는 돌파
> 여부보다 안착과 재시험이 핵심입니다. 가장 가까운 유효 지지는 197,803~210,197원,
> 저항은 223,397~230,603원이며 현재가 RR은 약 0.47배입니다. 20일 외국인
> +174,664주와 기관 +218,751주는 공동 순매수지만, 최근 5일은 외국인 +124,950주와
> 기관 -115,230주로 엇갈립니다. PER 10.27배와 PBR 1.53배는 자체 역사
> 92.8·91.6백분위지만 broad peer 표본은 없어 상대 premium을 만들지 않았습니다.

The exact archive-only rendered message is stored in
`data/ai_review/pilot/retrospectives/2026/08/2026-08-14-kr-phase7-stateful-monitoring-v38/rendered-dry-run.md`.

## SK hynix Regression

SK hynix retains the memory framework and modeled-versus-consensus distinction. Current price is
1,645,000 KRW and the 1,550,000 confirmation is holding above after the 8/13 crossing. No valid
Strong/Medium dynamic support exists, so chart invalidation and RR remain unavailable; the registered
support is not substituted. The nearest Medium resistance is monthly
2,918,470.825014~3,055,529.174986 and is not treated as a near-term target.

Supply is explicitly time-separated: 1-day mixed, 5-day joint buying, and 20-day joint selling.
Valuation remains PER 7.1988, PBR 7.0920, modeled fPER 16.3778, and PBR historical percentile 93.9.
The review therefore does not reduce the memory-cycle argument to low trailing P/E.

## Persistence Proof

Regression coverage creates consecutive final assessments, persists each monitoring snapshot, and
reads it through `assessment_to_read`. It verifies current and previous historical percentiles,
dynamic support, registered-rule preservation, confirmation transition, supply transition, and
state delta. A targeted replay reuses all active same-date final assessments for peers and cannot
overwrite a valid peer snapshot with a one-ticker sample.

## Safety And Versions

- Policy: `daily-review-v3.8`
- Output schema: 4, unchanged
- OHLCV: `ohlcv-structure-v2`, unchanged
- Investment Knowledge: 3.0, unchanged
- Chart Knowledge: 1.0, unchanged
- Public Action: 0.4.5, 20/20 operationIds, unchanged
- DB migration: none
- Production Assist: disabled
- Retrospective Telegram: not sent
- Retrospective Pilot count: not incremented
- Existing Pilot v3 count: KR 1/5, US 0/5

## Active Universe Smoke

A temporary copy of the operating database was used; the production database was not changed.

| Market | Active packet stocks | Monitoring state | Price grounding requirements | Unsupported numeric semantics |
|---|---:|---:|---:|---:|
| KR | 7 | 7/7 | 22 | 0 |
| US | 13 | 13/13 | 45 | 0 |

Both packets identify `daily-review-v3.8`, output schema 4, and `ohlcv-structure-v2`. No live peer
fact was emitted because the minimum comparable sample did not pass.

## Validation

- `pytest -q`: 615 passed, one upstream Starlette deprecation warning
- focused Phase 7 tests: 115 passed
- Ruff: passed
- `git diff --check`: passed
- Skill quick validation: passed
- Investment Knowledge parity: three copies at
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge parity: two copies at
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: 0.4.5, 20/20 unique operationIds
- Scheduled Tasks: US 08:15/08:30 and KR 16:15/16:55, all ACTIVE on v3.8

## Remaining Gaps

- No broad point-in-time KR/US peer valuation provider exists.
- The limited active-universe provider produced no qualifying live peer metric on 2026-08-14.
- Historical assessments are not automatically backfilled; Phase 7 takes effect on new final runs.
