# Run-27 Natural Reasoning Root Cause

Date: 2026-08-19  
Packet: `2026-08-19-kr-run-27-63a064e837ff`  
Market/policy/schema: `kr` / `daily-review-v3.10` / `4`

## Immutable Outcome

The AI candidate was not sent. Deterministic fallback sent 8/8 at
`2026-08-19T17:10:01.680736+09:00`, with zero pending and no duplicate. The archived validation state
is `quality_rejected`; fallback eligibility was preserved. Pilot v3 records this session as sent by
`deterministic_fallback` and not counted as an AI Pilot success. Original packet, output, fallback,
delivery, receipt, DB, and Pilot records were read-only during this repair.

The initial hard errors were:

```text
003690:unverified_depositary_ratio_described_as_verified:price_positioning.new_observer_view
005490:framework_not_allowed:chart_risk_reward
086280:framework_not_allowed:chart_risk_reward
```

After the bounded correction removed those three errors, the runtime quality gate still rejected
two substantive repetitions and four repeated skeletons.

## Korean Re

The exact rejected span was:

> 신규 관찰자는 가까운 저항을 추격하기보다 동적 지지 반응과 합산비율·자기자본이익률 확인이 함께 나타날 때 새 자금의 비대칭을 판단합니다.

This was not depositary prose. Canonical identity is `verified_non_depositary`, security type
`common_stock`, and depositary-ratio state `not_applicable`. The old expression allowed the
depositary qualifier to be optional, so `합산비율 ... 확인` falsely matched the depositary-ratio
rule. The repair requires an explicit ADR, ADS, or depositary term. Candidate selection also now
suppresses depositary reasoning for domestic/non-depositary securities. Verified ADR fixtures retain
valid ratio reasoning.

Classification: `SECURITY_REASONING_OWNERSHIP` plus validator false positive.

## POSCO And Hyundai Glovis

Both raw drafts placed `chart_risk_reward` in `frameworks_used`. Their packet price structures had
overlapping support/resistance, so RR was unavailable and `chart_risk_reward` was not an authorized
required framework. The draft nevertheless promoted it alongside the real industry framework.

The repaired ownership is:

| Subject | Investment/industry owner | Price owner | Result |
|---|---|---|---|
| POSCO Holdings | `steel_materials_valuation` | `price_ohlcv`; RR unavailable | remove `chart_risk_reward` |
| Hyundai Glovis | `shipping_transport_valuation` | `price_ohlcv`; RR unavailable | remove `chart_risk_reward` |

`chart_risk_reward` remains legal only as packet-authorized `price_context`; it was not added to an
industry allowlist. Classification: `FRAMEWORK_OWNERSHIP`.

## Repetition

The raw candidate repeated a three-line numeric supply skeleton across all seven subjects, and four
subjects rendered malformed `<numeric>는입니다` predicates. It also copied these substantive
candidates across three subjects each:

- `손익 항목의 금액별 기간·연결 기준이 확인되지 않아 금액과 성장률을 표시하지 않습니다.`
- `재고·CAPEX 이후 FCF·ROIC`

The repair publishes candidate owner and specificity metadata, puts each subject-specific supply
relationship before its six canonical flow values, removes postpositions only where the authored
predicate already supplies `입니다`, and suppresses cross-subject generic candidates before prose.
It does not use synonym substitution or change the quality threshold.

## Replay Result

- full semantic validator: PASS, 0 errors;
- numeric binding: 117 automatic, 0 manual, 0 rejected, 0 unresolved;
- typed valuation: PASS;
- substantive repetitions: 2 -> 0;
- maximum identical substantive sentence: 3 -> 0;
- template skeleton repetitions: 4 -> 0;
- generic methodology repetitions: 0 -> 0;
- runtime quality receipt: PASS and cryptographically verified;
- average stock message length: 1,410.14 -> 1,377.14 characters (-2.34%).

This is retrospective evidence only. Natural AI-Assisted Delivery remains `PARTIAL`.

## Additional Read-Only Findings

Hanwha Aerospace fallback RR is 0.03x from canonical current price and selected chart structure. It
is mathematically valid, not an overlap artifact. Its weak decision meaning may justify a future
qualitative RR interpretation contract, but no threshold or RR formula changed here.

The KR market digest remains dependent on available global macro context and lacks operating KRX
breadth. That is a separate persistent gap; no market feature was added.

