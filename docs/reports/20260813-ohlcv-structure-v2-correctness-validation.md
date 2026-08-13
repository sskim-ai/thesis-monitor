# OHLCV Structure v2 Correctness Validation

Date: 2026-08-13 KST
Base: `5ff750b7645b53da582d9e7ffcaeac3bec80ca38`
Structure algorithm: `ohlcv-structure-v2`
AI policy: `daily-review-v3.5`
Output schema: `3`

## Scope and invariants

This phase corrects four existing calculation contracts without adding a new chart feature:

1. Major Swing and raw-bar index alignment
2. True higher-timeframe zone scoring
3. Invalidation timeframe basis
4. Major Base and Breakout Start confidence

The following boundaries remain unchanged:

- Local Pivot is not a Major Swing input.
- Chart invalidation does not mutate thesis invalidation.
- Chart state is not a buy or sell command.
- Adjusted technical price is not mixed with unadjusted historical valuation price.
- Production Assist remains disabled.

## 1. Canonical index alignment

### Before

`detect_major_swings()` truncated and normalized its own lookback, while anchor selection normalized the full raw input again. A swing index from a 156-week slice could therefore be compared with a 300-week coordinate system.

### After

`NormalizedBarSeries` owns the canonical timeframe array, source count, actual lookback count, date bounds, and price basis. Major Swing detection, anchor selection, Elliott, and Fibonacci consume the same object. Every swing and anchor is checked against:

`canonical_bars[index].date == recorded_date`

Regression result:

| Input | Canonical analysis | Result |
|---|---:|---|
| 300 weekly bars | 156 weekly bars | All swing and anchor index/date pairs aligned |

Live correction: TSLA Breakout Start moved from the offset date `2026-04-05` to the canonical weekly date `2025-04-06`. Its recent major high remains `2026-05-10`.

## 2. Higher-timeframe hierarchy

Only actual higher timeframes contribute to the score:

| Zone | Overlap | Score |
|---|---|---:|
| Daily | Weekly | 2 |
| Daily | Monthly | 2 |
| Daily | Weekly + Monthly | 3 |
| Weekly | Daily | 0 |
| Weekly | Monthly | 2 |
| Monthly | Daily | 0 |
| Monthly | Weekly | 0 |

Lower-timeframe overlap is retained as audit metadata and never added to the higher-timeframe score.

Live impact across 20 active companies:

- 19 companies had at least one corrected zone score.
- 277 zones changed score or strength.
- 15 zones changed Strong to Medium.
- 66 zones changed Medium to Weak.
- 2 zones changed Weak to Medium after corrected Fibonacci overlap.
- No live chart state changed.

## 3. Invalidation and RR basis

| Nearest meaningful support | Invalidation contract | RR |
|---|---|---|
| Daily | Daily ATR and 1.0% buffer | Allowed |
| Weekly | Weekly ATR and 1.5% buffer | Allowed |
| Monthly | `monthly_invalidation_contract_undefined` | Withheld |

The selector preserves the nearest Strong/Medium support. It does not skip a monthly support to find a farther daily or weekly support. When monthly invalidation is unavailable, RR is also unavailable because downside cannot be verified.

No live company had a nearest qualifying monthly support in this smoke. The fail-closed behavior and no-skip rule are covered by dedicated fixtures. WRD changed from RR available to withheld because corrected zone scoring removed its qualifying support, not because of the monthly rule.

## 4. Anchor confidence

### Major Base

The current prompt does not define deterministic thresholds for proving a long decline or sideways pre-base regime. This phase therefore uses the conservative contract:

- Rise threshold and prior-major-high break can select the anchor.
- `pre_base_regime_unverified` caps confidence at Medium.
- High confidence requires a future explicit pre-base regime contract.

Thirteen live Major Base anchors changed from High to Medium.

### Breakout Start

The price condition remains a weekly close above the previous 20-week highest close. Historical volume is checked against the previous 20-week average:

- Ratio at least 1.2: `volume_confirmed`, High
- Ratio available but below 1.2: `volume_not_confirmed`, Medium
- Historical volume unavailable: `volume_unknown`, anchor retained, Medium

Live results: 5 confirmed, 13 not confirmed, 1 without a breakout anchor, and 1 without enough Major Swing structure. The volume-unknown fail-closed path is covered by a fixture.

Every anchor now records type, timeframe, index, date, price, confidence, source, selection reasons, and blocking unknowns.

## 5. Fibonacci and Elliott

Fibonacci validates every anchor index/date before calculation. A mismatch produces `anchor_index_mismatch` and no Fibonacci set.

- High confidence: core use allowed.
- Medium confidence: context use allowed, never a sole core reason.
- Low confidence: audit only and excluded from AI facts.

Thirteen long-term Fibonacci sets changed from High to Medium with their Major Base. TSLA's breakout Fibonacci low date changed from `2026-04-05` to `2025-04-06`. Elliott continues to use Major Swings only, remains tentative, and low-confidence counts remain outside the AI core judgment.

## 6. Active-universe before and after

Active universe discovered dynamically: 20 companies, 7 KR and 13 US.

| Capability | v1 | v2 |
|---|---:|---:|
| Major Swing available | 19 | 19 |
| Fibonacci available | 17 | 17 |
| Invalidation available | 16 | 15 |
| RR available | 16 | 15 |
| Chart state available | 20 | 20 |

v2 state distribution: WAIT 17, HOLD 2, SUPPORT_ENTRY 1. No ticker-specific override or active-universe count was added.

## 7. SK hynix validation

SK hynix (`000660`) was regenerated from live adjusted OHLCV and the existing deterministic assessment.

| Field | Phase 5 | Phase 5.1 |
|---|---|---|
| Major Base | 2024-08-05, High | 2024-08-05, Medium, pre-base regime unverified |
| Breakout Start | 2025-04-14, Medium | 2025-04-14, Medium, volume ratio 1.07973 |
| First Higher-Low | 2025-04-14, High | 2025-04-14, High |
| Canonical indexes | Not exposed | Base 50, breakout/HL 86, major high 116 |
| Long-term Fibonacci | High | Medium, context only |
| Invalidation | Unavailable | Unavailable, qualifying support absent |
| RR | Unavailable | Unavailable, invalidation unavailable |
| Chart state | WAIT / Medium | WAIT / Medium, distribution |

The AI-assisted dry-run passed with 27 grounded numeric claims and no quantitative-grounding flags. The exact rendered artifact is in `20260813-000660-ohlcv-structure-v2-dry-run.md`.

## 8. Validation

- Full pytest: 572 passed, 1 external Starlette deprecation warning
- Focused structure, client, AI, and delivery tests: 117 passed
- Ruff: passed
- `git diff --check`: passed
- Investment Knowledge v3: unchanged, SHA-256 `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1: unchanged, SHA-256 `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: version 0.4.5, operationId 20/20
- DB migration: none
- Deterministic assessment and Telegram delivery: no mutation during validation

## Remaining gap

The pre-base decline/sideways regime remains explicitly unverified, so Major Base confidence is capped at Medium. Defining that regime requires a separate reviewed deterministic contract. Production Assist remains disabled, and the five-trading-day Pilot count must begin only after v2 deployment, task update, and final live gates pass.
