# thesis-monitor — Validator P1 + KRX Night Futures Data + Structured Autonomy Stability Repair
## Close the 20/22 future-checkpoint failures generically
## Fix LEAF logical-condition schema conformance deterministically
## Add KOSPI200 night-futures as a first-class session-aware market input
## Re-run a completely fresh US14+KR8 generation and clean A/B/C
## Keep blind-review disagreement diagnostic only, never a target-label oracle

---

# 0. Purpose

This task has three separate goals:

```text
A. Validator correctness
   - Run A/B 20/22 future-checkpoint false rejects
   - Run C logical LEAF schema failure

B. Market-data completeness
   - correctly acquire and represent KRX KOSPI200 night futures
   - preserve night-session date/reference/contract semantics

C. Structured Autonomy stability
   - fresh first 22/22
   - A/B/C 22/22 each
   - diagnose judgment behavior without tuning to prior blind labels
```

Do not blur these three goals into one generic "make tests pass" task.

---

# 1. Current production baseline

Previously integrated production lineage reported:

```text
main / operating SHA =
d18e68b1e944d7749d093b08797fcd9498412680

operating model =
gpt-5.6-sol

operating reasoning effort =
xhigh
```

Verify current main and operating SHAs at task start.
Do not assume the above is still current.

The latest blind-review reveal was a data/review operation.
Do not infer production code changes from it.

---

# 2. Structured Autonomy previous generation

Previous fresh generation ID:

```text
20260905-uskr22-blind-20260905T082245Z-e82aa2b9742a
```

Fresh-first:

```text
validated = 22/22
```

A/B/C stability did not complete.

Observed:

```text
Run A = 20/22
Run B = 20/22
Run C = interrupted by schema-invalid logical condition
```

No request/quota/rate-limit root cause was established.

Do not treat the number 20 as an API request ceiling.

---

# 3. P1-A — future-checkpoint semantic ownership

Observed false rejects:

```text
Run A:
MU
005490

Run B:
GOOGL
005490
```

Common pattern:

```text
the evidence actually owns the relevant metric
+
the claim refers to a future checkpoint / future validation condition
+
the validator re-parses natural-language temporal grammar
+
valid evidence-backed wording is rejected
```

This is a semantic-ownership defect.

Do NOT fix it by adding:
- Korean ending regex
- exact phrases
- ticker exceptions
- per-company vocabulary
- global threshold weakening

---

# 4. Future-checkpoint target architecture

The source/claim metadata should own:

```text
claim_type
metric_refs
time_scope
checkpoint_kind
direction
evidence_refs
```

Suggested semantics:

```text
time_scope =
CURRENT /
HISTORICAL /
FUTURE_CHECKPOINT

checkpoint_kind =
VALIDATION /
STRENGTHEN /
WEAKEN /
INVALIDATION /
REASSESSMENT
```

The prose may use natural Korean or English.

The validator should verify the structured relationship,
not reverse-engineer temporal meaning from sentence endings.

---

# 5. Future-checkpoint hard-safety rules

A future checkpoint is allowed only if:

```text
referenced metric exists in eligible source evidence
AND
same subject
AND
same generation
AND
semantic direction is permitted
AND
claim does not fabricate a current observed value
```

Examples:

```text
"향후 ROIC가 악화되는지 확인"
→ valid if ROIC is an owned checkpoint metric

"현재 ROIC가 8%로 악화됐다"
→ invalid if current ROIC value is not evidenced
```

Unknown remains Unknown.

Do not convert a missing current metric into directional SELL evidence.

---

# 6. P1-B — logical LEAF schema conformance

Run C failed on a logical-condition shape equivalent to:

```text
type = LEAF
children != empty
```

This is a schema/conformance defect.

The semantic model already distinguishes:
- LEAF
- ANY_OF
- ALL_OF
- other explicitly supported operators

A LEAF must not own child expressions.

---

# 7. Logical-condition canonicalization

Preferred deterministic rule:

```text
LEAF:
  leaf_ref required
  children forbidden

ANY_OF / ALL_OF:
  children required
  leaf_ref forbidden unless schema explicitly supports it
```

Do not silently delete semantically meaningful children from malformed output
just to make it validate.

Allowed repair behavior:

```text
if intended structure can be proven from structured source refs:
    canonicalize deterministically
else:
    reject with typed schema error
```

No prose conjunction parsing as the primary fix.

---

# 8. Logical schema generation constraint

Improve the writer/schema contract so invalid shapes are prevented upstream.

Required:
- model schema only permits valid discriminated-union shapes
- serializer preserves the union
- parser error identifies operator and invalid field
- no cross-condition branch mixing
- no cross-ticker refs

Regression fixtures:

```text
LEAF + leaf_ref + no children = PASS
LEAF + children = FAIL
ANY_OF + >=2 valid children = PASS
ANY_OF + missing children = FAIL
ALL_OF + valid children = PASS
```

---

# 9. P1-C — KRX KOSPI200 night futures as first-class data

KRX officially supports KOSPI200 futures night trading.

Official session:

```text
night session =
18:00 KST
to
06:00 KST next calendar day
```

Order acceptance starts earlier, but market-data session semantics should be based
on the actual trading session unless the provider explicitly exposes auction state.

Do not model this as a generic overseas future.

It is a KRX domestic derivative night session.

---

# 10. Verified human acceptance fixture — Kiwoom screenshot

User-provided Kiwoom screenshots show:

```text
instrument =
KOSPI200 Futures

contract =
202609

night-session business date =
2026-09-04

open =
1055.65

high =
1097.65

low =
1043.85

close / last =
1093.90

volume =
32666

header change =
+41.40

header change pct =
+3.93%
```

Independent external quote cross-check matched:

```text
Sep 2026 KOSPI200 Futures
price = 1093.90
change = +41.40
change pct = +3.93%
high = 1097.65
low = 1043.85
```

This fixture is acceptance evidence only.

Do NOT hardcode 1093.90 into production logic.

---

# 11. Important dual-reference discovery

The screenshots prove that two valid percentage changes can coexist.

For the 2026-09-04 night session:

```text
night last =
1093.90

header reference =
1052.50

1093.90 - 1052.50 =
+41.40

+41.40 / 1052.50 =
+3.93%
```

But the prior night-session close shown in the daily series is:

```text
2026-09-03 night close =
1049.05
```

So:

```text
1093.90 - 1049.05 =
+44.85

+44.85 / 1049.05 =
+4.28%
```

Therefore:

```text
+3.93%
and
+4.28%
```

are NOT automatically conflicting data.

They use different reference bases.

---

# 12. Never infer reference basis from arithmetic alone

Production must preserve an explicit field such as:

```text
change_reference_type
change_reference_price
```

Possible values:

```text
REGULAR_SESSION_CLOSE
OFFICIAL_BASE_PRICE
PRIOR_NIGHT_CLOSE
PROVIDER_REFERENCE
UNKNOWN
```

If the provider does not explicitly identify the basis:

```text
reference_type = UNKNOWN
```

Do not label a computed base as "official" simply because arithmetic matches.

---

# 13. Night-futures canonical data contract

Create or extend a typed market-data contract.

Recommended fields:

```json
{
  "instrument_id": "...",
  "instrument_type": "KOSPI200_FUTURES",
  "contract_month": "202609",
  "session_type": "NIGHT",
  "session_business_date": "2026-09-04",
  "session_start_kst": "2026-09-04T18:00:00+09:00",
  "session_end_kst": "2026-09-05T06:00:00+09:00",
  "observed_at": "...",
  "market_state": "OPEN|CLOSED",
  "open": 1055.65,
  "high": 1097.65,
  "low": 1043.85,
  "last": 1093.90,
  "volume": 32666,
  "change": 41.40,
  "change_pct": 3.93,
  "change_reference_type": "...",
  "change_reference_price": 1052.50,
  "prior_night_close": 1049.05,
  "night_close_to_night_close_pct": 4.28,
  "source": "...",
  "source_quality": "...",
  "is_delayed": null,
  "stale_reason": null
}
```

Exact field names may follow repository conventions.

---

# 14. Cross-midnight business-date semantics

The night session spans two calendar dates.

For the screenshot fixture:

```text
session business date =
2026-09-04

calendar end =
2026-09-05 06:00 KST
```

Do not relabel the session as 2026-09-05 merely because it finishes after midnight.

Preserve both:
- session_business_date
- actual timestamp

This prevents duplicate/missing daily bars.

---

# 15. Weekend / holiday state

At 2026-09-05 Saturday night:

```text
market_state = CLOSED
```

There is no live KRX night-session tick.

The latest available value remains the completed 2026-09-04 night session.

User-facing wording must be:

```text
최근 야간선물 종가
최근 야간 세션
9/4 야간 세션 기준
```

or equivalent.

Do NOT say:

```text
현재 실시간 야간선물
```

when the market is closed.

---

# 16. Historical acceptance fixtures from screenshots

Use these only as validation fixtures:

```text
2026-08-28:
O 1068.00
H 1086.30
L 1061.70
C 1064.20
V 23973

2026-08-31:
O 1067.00
H 1072.45
L 1053.80
C 1064.50
V 22349

2026-09-01:
O 1061.00
H 1061.40
L 1031.30
C 1040.50
V 30651

2026-09-02:
O 1023.00
H 1048.35
L 1020.25
C 1043.60
V 22676

2026-09-03:
O 1030.95
H 1052.45
L 1020.75
C 1049.05
V 26252

2026-09-04:
O 1055.65
H 1097.65
L 1043.85
C 1093.90
V 32666
```

Do not convert screenshot fixtures into the permanent provider.

---

# 17. Production source discovery first

Before adding any new network dependency, inspect the repository.

Determine whether an approved existing provider already exposes:
- KRX night futures
- Kiwoom/OpenAPI derivatives quotes
- KRX derivatives data
- another licensed/approved feed

Required report:

```text
CURRENT_NIGHT_FUTURES_PROVIDER =
...

CURRENT_PROVIDER_SUPPORT =
FULL / PARTIAL / NONE

NEW_EXTERNAL_DEPENDENCY_REQUIRED =
YES / NO
```

Do not scrape an interactive website as the default production feed.

The public external quote used in this task is a cross-check,
not automatic production-provider approval.

---

# 18. Source hierarchy

Preferred production hierarchy:

```text
1. existing approved broker/exchange data path
2. approved KRX/market-data path
3. approved licensed fallback
```

Screenshot/manual input:

```text
test fixture only
```

Public webpage quote:

```text
cross-check / diagnostics only
unless separately approved for production ingestion
```

---

# 19. Contract identity and expiry

Always preserve the exact contract.

For the current fixture:

```text
KOSPI200 202609
```

Do not store only:

```text
"KOSPI200 futures"
```

without contract identity.

Near expiry:
- front contract may roll
- basis may change
- volume/open interest migrates

Do not compare different contract months as one uninterrupted raw series
without an explicit continuous-contract methodology.

---

# 20. Roll safety

Required fields:

```text
contract_month
last_trading_date if known
days_to_expiry if safely derivable
roll_state
```

If a daily comparison crosses a contract roll:

```text
RAW_RETURN_ACROSS_DIFFERENT_CONTRACTS =
FORBIDDEN
```

unless explicitly adjusted.

---

# 21. Market-brief interpretation

Night futures are:

```text
market/timing/positioning context
```

They are NOT:
- company fundamental evidence
- earnings evidence
- direct proof of next-day spot return

Allowed market interpretation:

```text
"최근 야간 KOSPI200 선물이 정규 기준 대비 강하게 상승했다."
```

Not allowed:

```text
"다음 KOSPI200 현물은 +3.93% 상승한다."
```

---

# 22. Individual-stock use

Night futures alone must not strengthen/weaken a company investment logic.

It may affect:
- short-term market context
- timing
- opening-gap risk
- broad beta context

It must NOT alone change:
- business thesis status
- earnings estimate
- valuation
- invalidation status

This follows the same principle as supply/positioning.

---

# 23. Market message rendering

When current session is OPEN:

```text
🌙 KOSPI200 야간선물
1,0xx.xx
기준 대비 ±x.xx%
```

When CLOSED:

```text
🌙 최근 KOSPI200 야간선물
9/4 야간 세션 종가 1,093.90
기준 대비 +3.93%
```

Only render:
- reference basis
- contract month
- as-of/session date

when known.

Do not overload the message with raw OHLCV unless relevant.

---

# 24. Data-quality rules

Fail/omit rather than fabricate if:

```text
contract unknown
session date unknown
price stale but rendered as live
reference basis misidentified
cross-contract comparison
currency/unit mismatch
```

A missing night-futures field does not make the entire market briefing fail
unless the product explicitly requires it.

Prefer:

```text
night_futures.available = false
```

over invented values.

---

# 25. PHASE D — completely fresh US14 + KR8 generation

After P1-A and P1-B repairs:

Create a NEW generation.

Do not reuse:
- previous fresh-first candidates
- A/B candidates
- partial C candidates
- prior AI labels
- external reviewer labels

Use production-equivalent:

```text
gpt-5.6-sol / current operating reasoning effort
```

Resolve exact runtime config at execution time.

---

# 26. Fresh-first gate

Required:

```text
FRESH_FIRST_VALIDATED = 22/22
```

If not:

```text
STOP
```

No selective ticker rerun.

No prompt edit after seeing failed tickers.

No label targeting.

---

# 27. Clean A/B/C gate

Only after fresh first 22/22:

```text
A = 22/22
B = 22/22
C = 22/22
```

Same:
- data
- schema
- model
- effort
- validator
- renderer contract

No cross-run visibility.

No majority voting.

---

# 28. Required validator proof

Explicitly report:

```text
RUN_A_FUTURE_CHECKPOINT_FALSE_REJECT = 0
RUN_B_FUTURE_CHECKPOINT_FALSE_REJECT = 0

LEAF_CHILD_SHAPE_FAILURE = 0

FUTURE_CHECKPOINT_KOREAN_REGEX_ADDED = 0
TICKER_EXCEPTION_ADDED = 0
GLOBAL_SEMANTIC_THRESHOLD_WEAKENED = 0

HARD_SAFETY_TRUE_POSITIVE_REGRESSION = 0
```

---

# 29. Prior blind review is diagnostic only

Previous independent blind comparison found:
- no BUY↔SELL direct reversal
- AI tended to keep a wider HOLD basin
- new-buyer WAIT appeared frequently
- some cases showed strong separation between business direction and entry timing

Do NOT turn these observations into desired labels.

The external reviewer is not ground truth.

---

# 30. Diagnostic themes for the new cohort

Observe, do not tune:

```text
HOLD basin width

new-buyer WAIT frequency

Unknown handling

high-expectation / high-valuation names

cyclical valuation weighting

ADR/security-basis uncertainty

business quality vs entry timing separation

holder REVIEW vs HOLDABLE separation
```

No target frequency.

No minimum ATTRACTIVE count.

No desired BUY/HOLD/SELL distribution.

---

# 31. Prior disagreement cases are regression observations only

Previous notable differences may be reviewed after the new generation is frozen.

Examples include:
- speculative/high-valuation names
- memory-cycle names
- ADR/security-basis cases
- BUY + WAIT separation cases

Do not encode expected labels for:
CRCL, HUT, SNDK, WRD, GOOGL, MU, TSM, 012450, 000660, or any other ticker.

---

# 32. Stability classification

After clean A/B/C:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Boundary movement such as:

```text
5.5:4.5 ↔ 6.0:4.0
```

may be legitimate if action context remains coherent.

Do not treat every threshold crossing as architecture failure.

---

# 33. Night-futures tests

Required unit/contract tests:

```text
session 18:00 → 06:00 cross-midnight

Saturday/holiday CLOSED state

session_business_date preserved

same-session OHLCV

header reference pct vs prior-night-close pct are distinct

unknown reference type remains UNKNOWN

contract-month identity preserved

cross-roll raw return blocked

stale quote cannot render as live
```

Acceptance fixture:

```text
202609 / 2026-09-04 night

last = 1093.90
high = 1097.65
low = 1043.85
volume = 32666
```

---

# 34. Current fixture arithmetic tests

Test:

```text
1093.90 - 1052.50 = 41.40

41.40 / 1052.50
≈ 3.93%
```

and separately:

```text
1093.90 - 1049.05 = 44.85

44.85 / 1049.05
≈ 4.28%
```

Required:

```text
DUAL_REFERENCE_FALSE_CONFLICT = 0
```

---

# 35. Market-message shadow test

Generate a deterministic market-message shadow using the fixture.

Expected semantics:

```text
market is closed
latest completed night session is identified
202609 contract identified
1093.90 rendered
+3.93% rendered only with its correct/known reference semantics
not labeled live
not interpreted as guaranteed spot move
```

Do not send to production in this validation phase.

---

# 36. Natural-proof relationship

KR/US explicit-V2 natural proof remains an infrastructure gate.

Night-futures feature correctness is a separate market-data gate.

Structured Autonomy promotion is a decision-quality gate.

Report independently:

```text
INFRA_NATURAL_PROOF
NIGHT_FUTURES_DATA_READINESS
STRUCTURED_AUTONOMY_READINESS
```

Do not collapse them.

---

# 37. Production mutation policy

Repair branch may modify code/tests.

But before production merge, require:
- full tests
- data-contract proof
- fresh 22 + A/B/C proof
- no hard-safety regression

Do not send model shadow decisions to production users.

Night-futures shadow rendering must not be sent until approved.

---

# 38. Required reports

Create:

1. `docs/reports/20260905-future-checkpoint-root-cause.md`
2. `docs/reports/20260905-future-checkpoint-structured-ownership-contract.md`
3. `docs/reports/20260905-logical-leaf-schema-root-cause.md`
4. `docs/reports/20260905-logical-condition-discriminated-union-contract.md`
5. `docs/reports/20260905-night-futures-provider-discovery.md`
6. `docs/reports/20260905-krx-night-futures-session-contract.md`
7. `docs/reports/20260905-night-futures-reference-basis-contract.md`
8. `docs/reports/20260905-night-futures-roll-and-staleness-contract.md`
9. `docs/reports/20260905-night-futures-kiwoom-fixture-proof.md`
10. `docs/reports/20260905-night-futures-market-message-shadow.md`
11. `docs/reports/20260905-fresh-uskr22-first.md`
12. `docs/reports/20260905-run-a.md`
13. `docs/reports/20260905-run-b.md`
14. `docs/reports/20260905-run-c.md`
15. `docs/reports/20260905-abc-stability.md`
16. `docs/reports/20260905-judgment-diagnostic-audit.md`
17. `docs/reports/20260905-promotion-readiness.md`
18. `docs/reports/20260905-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 39. Machine-readable proofs

Create:

```text
future-checkpoint-proof.json
logical-leaf-schema-proof.json
night-futures-provider-proof.json
night-futures-session-proof.json
night-futures-reference-proof.json
night-futures-fixture-proof.json
fresh-first.json
run-a.json
run-b.json
run-c.json
abc-stability.json
promotion-readiness.json
```

---

# 40. Required gates

```text
CURRENT_MAIN_SHA =
...

CURRENT_OPERATING_SHA =
...

CURRENT_MODEL =
...

CURRENT_REASONING_EFFORT =
...

FUTURE_CHECKPOINT_PRIMARY_OWNER =
STRUCTURED_METADATA / OTHER

FUTURE_CHECKPOINT_FALSE_REJECT_A =
0 / NONZERO

FUTURE_CHECKPOINT_FALSE_REJECT_B =
0 / NONZERO

FUTURE_CHECKPOINT_KOREAN_REGEX_ADDED =
0 / NONZERO

LOGICAL_CONDITION_SCHEMA =
DISCRIMINATED_UNION / OTHER

LEAF_CHILD_SHAPE_FAILURE =
0 / NONZERO

TICKER_EXCEPTION_ADDED =
0 / NONZERO

CURRENT_NIGHT_FUTURES_PROVIDER =
...

CURRENT_PROVIDER_SUPPORT =
FULL / PARTIAL / NONE

NEW_EXTERNAL_DEPENDENCY_REQUIRED =
YES / NO

NIGHT_FUTURES_SESSION_CROSS_MIDNIGHT =
PASS / FAIL

NIGHT_FUTURES_BUSINESS_DATE =
PASS / FAIL

NIGHT_FUTURES_MARKET_CLOSED_STALENESS =
PASS / FAIL

NIGHT_FUTURES_CONTRACT_IDENTITY =
PASS / FAIL

NIGHT_FUTURES_ROLL_SAFETY =
PASS / FAIL

NIGHT_FUTURES_REFERENCE_BASIS =
PASS / FAIL

DUAL_REFERENCE_FALSE_CONFLICT =
0 / NONZERO

KIWOOM_FIXTURE_LAST_1093_90 =
PASS / FAIL

KIWOOM_FIXTURE_HIGH_1097_65 =
PASS / FAIL

KIWOOM_FIXTURE_LOW_1043_85 =
PASS / FAIL

KIWOOM_FIXTURE_VOLUME_32666 =
PASS / FAIL

NIGHT_FUTURES_SHADOW_MESSAGE =
PASS / FAIL

FRESH_EXPERIMENT_GENERATION =
PASS / FAIL

OLD_CANDIDATE_REUSE =
0 / NONZERO

FRESH_FIRST_VALIDATED =
22 / OTHER

RUN_A_VALIDATED =
22 / OTHER

RUN_B_VALIDATED =
22 / OTHER

RUN_C_VALIDATED =
22 / OTHER

STABLE_COUNT =
...

BOUNDARY_UNCERTAINTY_COUNT =
...

UNSTABLE_COUNT =
...

HARD_SAFETY_TRUE_POSITIVE_REGRESSION =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

INFRA_NATURAL_PROOF =
PASS / FAIL / PENDING

NIGHT_FUTURES_DATA_READINESS =
READY_FOR_PRODUCTION_REVIEW /
NEEDS_MORE_REPAIR /
NOT_READY

STRUCTURED_AUTONOMY_READINESS =
READY_FOR_PRODUCTION_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_READY

MAIN_MERGE =
0 / 1
```

---

# 41. Stop conditions

Stop if the future-checkpoint fix requires ticker-specific grammar.

Stop if the LEAF fix silently drops semantic children without proof.

Stop if night-session values are stored without contract month.

Stop if the system cannot distinguish:
- session business date
- calendar timestamp

Stop if `+3.93%` and `+4.28%` are treated as conflicting solely because
reference semantics are missing.

Stop if a Saturday/holiday last quote is rendered as live.

Stop if a public webpage is silently introduced as a production scraper
without approval.

Stop A/B/C if fresh first != 22/22.

Do not retune judgments to match the previous ChatGPT blind review.

---

# 42. Completion response

Return:

```text
VALIDATOR P1 =
future-checkpoint root cause
repair ownership
A/B regression

LOGICAL SCHEMA =
LEAF root cause
discriminated union
C regression

NIGHT FUTURES =
provider
instrument/contract
session semantics
reference semantics
staleness
roll safety

KIWOOM FIXTURE =
202609
2026-09-04
O/H/L/C/V
header change
reference basis state

FRESH FIRST =
...

A/B/C =
...

STABILITY =
...

JUDGMENT DIAGNOSTICS =
...

FULL TESTS =
...

INFRA NATURAL PROOF =
...

NIGHT FUTURES READINESS =
...

STRUCTURED AUTONOMY READINESS =
...

MAIN =
...

REPORT ZIP =
...
SHA256 =
...
```

---

# 43. Final principle

Do not solve language semantics with more language regex.

Do not solve market-data ambiguity with arithmetic guesses.

The system should know:

```text
what fact it owns
what metric it owns
what logical condition it owns
what futures contract it owns
what session the quote belongs to
what timestamp it belongs to
what comparison basis produced the percentage
```

Then let AI interpret only the meaning that those structured facts safely support.
