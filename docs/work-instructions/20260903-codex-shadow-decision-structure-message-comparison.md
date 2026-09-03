# thesis-monitor — Codex Shadow Decision-Structure / Message Comparison
## Temporarily apply the proposed decision structure to frozen US run-53 evidence
## Generate real Codex judgments and production-style messages
## Compare only AFTER generation against the independent reference manual view
## No production decision/state mutation

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Source packet: `2026-09-03-us-run-53-055ae8ea01f6`
- Source cohort: US/foreign 14
- Task class: `BLIND_SHADOW_DECISION_EXPERIMENT + MESSAGE_RENDERING_COMPARISON`
- Production Assist: preserve `OFF`
- Production decision mutation: `0`
- Production accepted-plan mutation: `0`
- Production assessment mutation: `0`
- Production packet mutation: `0`
- Main merge: `0`
- Natural scheduler mutation: `0`
- Production recipient send: `0`
- Dedicated TEST recipient send: optional only after all shadow gates PASS
- Fresh market/company data collection: `0`
- Night-futures module: out of scope
- Personal cost basis / portfolio weight: not used

This task is exploratory.

Do NOT promote this temporary decision structure to production in this task.

---

# 1. Purpose

We want to answer:

```text
If Codex receives the same run-53 company/evidence/price-structure data
and uses the proposed decision structure,
what BUY/HOLD/SELL, BUY:SELL balance,
new-buyer view, holder view,
entry zone, and trim/sell-review zone does it independently produce?
```

Then:

```text
How does that independent Codex result compare with the separate reference
manual analysis prepared outside Codex?
```

The experiment is meaningful only if Codex does NOT see the manual reference before its judgments are frozen.

---

# 2. Blind experiment design

Mandatory two-phase design:

```text
PHASE 1 — BLIND GENERATION
Codex sees:
- canonical run-53 evidence
- decision contract
- price-structure facts
- valuation/expectations/business evidence
- generic message schema

Codex does NOT see:
- reference manual BUY/HOLD/SELL labels
- reference manual directional balances
- reference entry zones
- reference trim zones
- reference rationale text

Freeze:
- candidate artifacts
- accepted shadow artifacts
- final rendered messages
- fingerprints

PHASE 2 — COMPARISON
Only after Phase 1 artifacts are immutable:
load the reference manual view
and compare.
```

Hard:

```text
REFERENCE_MANUAL_VIEW_VISIBLE_DURING_GENERATION = 0
```

---

# 3. Source lock

Use the exact frozen run-53 stock evidence.

Reference cohort:

```text
CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Required:

```text
RUN53_FROZEN_COHORT_COUNT = 14
FRESH_FACT_COLLECTION = 0
POST_RUN53_FACT_LEAKAGE = 0
```

Use packet-owned:
- business/evidence
- market expectations
- valuation
- price/current close
- Price Structure
- support/resistance
- stored price rules
- technical context where safe
- macro only where actually transmitted

Do not fetch new prices/news/earnings.

---

# 4. Proposed common decision structure

Codex must reason in this order:

```text
Fact
→ business / earnings thesis
→ market expectations
→ valuation
→ price / timing
→ risks
→ BUY drivers
→ SELL drivers
→ directional balance
→ deterministic BUY/HOLD/SELL
→ new-buyer view
→ holder view
→ price zones if safely derivable
```

Prior accepted decision may be used only after the fresh shadow judgment is produced, for delta/adjudication diagnostics.

It must NOT anchor the fresh directional balance.

Hard:

```text
PRIOR_ACCEPTED_USED_TO_ANCHOR_FRESH_BALANCE = 0
```

---

# 5. Directional balance

Required:

```text
BUY balance + SELL balance = 10
```

Use 0.5 increments only.

Label derivation:

```text
BUY if BUY >= 6.0
SELL if SELL >= 6.0
HOLD otherwise
```

Examples:

```text
6.5 : 3.5 → BUY
6.0 : 4.0 → BUY
5.5 : 4.5 → HOLD
5.0 : 5.0 → HOLD
4.5 : 5.5 → HOLD
4.0 : 6.0 → SELL
```

The balance is not probability.

No fixed universal factor weights.

Hard:

```text
FIXED_FACTOR_WEIGHTED_SCORE = 0
BALANCE_PROBABILITY_LANGUAGE = 0
BALANCE_SUM_INVALID = 0
```

---

# 6. Separate business quality from current decision

Codex must separately classify:

```text
business_thesis_change
market_expectation_context
valuation_context
price_timing_context
```

A strong company may still be HOLD because current price/timing is unattractive.

A weak price structure must not automatically mark the business thesis as weakened.

Required:

```text
PRICE_TIMING_AUTOMATICALLY_CHANGES_BUSINESS_THESIS = 0
```

---

# 7. New-buyer view

Every stock receives:

```text
new_buyer_view
```

Question:

```text
Would a new observer want to initiate a position at or near the current price?
```

Must consider:
- current valuation
- current expectations
- current price
- nearest support
- nearest resistance
- major structural support/resistance
- confirmation price/rule if configured
- distance to invalidation/warning if relevant
- business/earnings evidence

Suggested shadow fields:

```json
{
  "stance": "ATTRACTIVE|WAIT|AVOID",
  "summary": "",
  "entry_zone_low": null,
  "entry_zone_high": null,
  "entry_type": "SUPPORT|BREAKOUT_CONFIRMATION|NONE",
  "entry_basis": [],
  "confirmation_condition": ""
}
```

Repository-native equivalents are allowed.

---

# 8. Entry-zone safety

Codex may produce an entry-price zone ONLY when the packet has sufficient verified price structure.

Valid bases include:

```text
verified support zone
overlapping support structures
registered support
verified confirmation/breakout level
valuation + support overlap
```

Forbidden:

```text
arbitrary discount from current price
round-number target
invented Fibonacci
unsupported technical level
provider multiplier
```

Hard:

```text
UNSUPPORTED_ENTRY_ZONE = 0
```

If support is broken and the rational new-buyer condition is a recovery/breakout, Codex may use:

```text
entry_type = BREAKOUT_CONFIRMATION
```

rather than fabricate a lower support entry.

---

# 9. Holder view

Every stock receives:

```text
holder_view
```

No user cost basis.

Question:

```text
Assuming an investor already holds the stock,
is the current investment logic still holdable,
and where should upside trimming / downside review be considered?
```

Suggested fields:

```json
{
  "stance": "HOLDABLE|REVIEW|REDUCE",
  "summary": "",
  "trim_zone_low": null,
  "trim_zone_high": null,
  "trim_basis": [],
  "downside_review_level": null,
  "downside_review_basis": [],
  "invalidation_condition": ""
}
```

---

# 10. Trim / sell-review zone semantics

Do NOT interpret:

```text
trim_zone
```

as:

```text
automatic sell target
```

It means:

```text
a price region where the holder should reassess valuation,
expectations, and updated earnings before deciding whether to trim.
```

Valid bases:
- verified major resistance
- historical/structural resistance
- valuation becomes clearly stretched at the same price region
- stored warning/price rule
- current business evidence no longer justifies multiple expansion

If earnings estimates rise materially, reaching the zone does not mandate selling.

Required:

```text
TRIM_ZONE_RENDERED_AS_MANDATORY_SELL = 0
```

---

# 11. Downside review remains separate

Do not mix:

```text
upside trim zone
```

with:

```text
downside warning / invalidation
```

If packet contains verified warning/invalidation rules, holder view may show them separately.

No invented stop-loss.

Hard:

```text
INVENTED_STOP_LOSS = 0
```

---

# 12. Price-structure calculation

For every ticker, create a compact structured price map before the AI judgment:

```text
current close
nearest support
nearest resistance
major support
major resistance
registered support
confirmation
warning
invalidation
distance current→support
distance current→resistance
```

Only include facts that exist.

Do not manufacture missing levels.

Store a `price_map_fingerprint`.

---

# 13. Price/timing interpretation

Codex must explicitly reason about:

```text
current price relative to support/resistance
```

Examples:

```text
near support + attractive valuation
→ helps BUY balance

immediately below resistance
→ reduces new-entry attractiveness

confirmation already achieved
→ helps price/timing evidence

warning/invalidation breached
→ weakens holder price context
```

But price alone does not own fundamental thesis changes.

---

# 14. Temporary shadow candidate schema

Use a temporary/shadow schema; do not migrate production authoritative schema in this experiment.

Required fields:

```json
{
  "ticker": "",
  "decision": "BUY|HOLD|SELL",
  "directional_balance": {"buy": 0.0, "sell": 0.0},
  "business_thesis_change": "",
  "market_expectation_context": "",
  "valuation_context": "",
  "price_timing_context": "",
  "buy_drivers": [],
  "sell_drivers": [],
  "core_judgment": "",
  "new_buyer_view": {},
  "holder_view": {},
  "reevaluation_up": [],
  "reevaluation_down": [],
  "evidence_refs": []
}
```

---

# 15. Blind Codex generation

Run the actual signed-in Codex model path in a non-production shadow namespace.

Use:
- same model/runtime configuration as production where feasible
- same evidence packet
- same numeric/semantic validators
- same valuation safety
- same technical safety

No pre-baked response.

Required:

```text
SHADOW_MODEL_REACHED = PASS
SHADOW_CANDIDATE_COUNT = 14
```

---

# 16. Shadow validation

Validate:

```text
schema
balance
evidence refs
numeric provenance
semantic provenance
valuation
price-zone provenance
entry/trim basis
technical safety
identity/language
```

Any unsafe price zone must be removed or converted to `null`, not guessed.

Required:

```text
SHADOW_VALIDATION_PASS_COUNT = 14
UNSUPPORTED_ENTRY_ZONE = 0
UNSUPPORTED_TRIM_ZONE = 0
```

---

# 17. Shadow adjudication

The purpose is primarily independent judgment.

For Phase 1, create:

```text
fresh shadow accepted artifact
```

from the fresh candidate and the generic adjudication contract.

The adjudicator may see prior accepted state only after fresh candidate/balance is frozen.

Record:
- prior accepted
- fresh shadow candidate
- adjudication
- shadow accepted

Do not write production accepted state.

Hard:

```text
PRODUCTION_ACCEPTED_STATE_MUTATION = 0
```

---

# 18. Production-style renderer

Render each shadow accepted decision with the proposed user-facing format.

Required template:

```text
🏢 Company(TICKER)

🧠 AI 분석 판단: HOLD
판단 균형: BUY 5.5 : SELL 4.5
판단 확신도: ...

🎯 핵심 판단
• ...

🆕 신규진입 관점
• ...
• 진입 검토 구간: ...
or
• 진입 검토 구간: 현재 설정하지 않음
• 진입 조건: ...

💼 보유자 관점
• ...
• 매도·축소 검토 구간: ...
or
• 검증된 가격구간 부족으로 숫자 제시 보류
• 하방 재점검: ... if safely supported

🔄 재평가 조건
• BUY 쪽: ...
• SELL 쪽: ...
```

The removed order/auto-trading disclaimer must remain absent.

---

# 19. Detailed existing body

After the new decision block, append the existing production stock body:

```text
투자 논리
구조적 위험
시장 기대
사업·실적 if applicable
핵심 감시
현재 가격 구조
등록 가격 규칙
수급 if available
Valuation
데이터 주의
다음 확인
```

Do not duplicate the same sentence verbatim across the new block and legacy/detail body.

Set message-quality checks.

---

# 20. Exact message artifacts

Create one exact UTF-8 message file per ticker:

```text
CORZ.txt
CPNG.txt
...
WULF.txt
```

and one combined:

```text
20260903-us14-shadow-decision-message-preview.md
```

These are mandatory even if Telegram test send is skipped.

---

# 21. Optional dedicated TEST-recipient send

Only after all 14 final shadow messages PASS:

the task MAY use the existing dedicated TEST recipient and real Telegram transport.

Never production recipient.

If used:

```text
14 stock messages only
```

No market message is required for this comparison experiment.

Hard:

```text
PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT = 0
```

---

# 22. Freeze Phase-1 artifacts

Before loading the manual comparison reference, record:

```text
generation timestamp
candidate SHA
shadow accepted SHA
rendered message SHA
price-map fingerprint
evidence fingerprint
```

Set:

```text
PHASE1_ARTIFACTS_FROZEN = PASS
```

Only then begin Phase 2.

---

# 23. Phase-2 reference manual view

The following reference is comparison-only.

It MUST NOT be supplied to the Codex generation/adjudication prompt.

Reference view:

```text
CORZ
decision HOLD
balance 4.5:5.5
new-buyer: WAIT; recovery/confirmation around 17.45~18.38
holder trim-review: 17.45~18.38

CPNG
HOLD
5.5:4.5
entry 15.45~15.70
trim-review 16.51~17.16

CRCL
HOLD
5.0:5.0
entry 82.0~86.5
trim-review unavailable

GOOGL
HOLD
4.5:5.5
entry support-style 312~322 OR confirmation-style recovery around 354
trim-review 344~354

HUT
SELL
3.0:7.0
new entry: avoid / require recovery
trim-review 84~90

IBM
HOLD
5.5:4.5
entry 228~235
trim-review 237~250

MU
BUY
6.5:3.5
entry support-style 868~912 OR trend confirmation above ~950
trim-review 1231~1279

RXRX
HOLD
5.0:5.0
entry 3.37~3.47
trim-review 3.58~3.68

SKHY
HOLD
5.0:5.0
entry 147~151
trim-review 175~182

SNDK
HOLD
4.5:5.5
entry registered support ~1100~1125 or deeper dynamic support ~923~1073
trim-review 2316~2393

TSLA
SELL
2.5:7.5
entry only if business confirmation improves; price review around 335~341
trim-review 359~383

TSM
HOLD
5.5:4.5
entry 407~414
trim-review 432~440

WRD
SELL
3.5:6.5
entry only after recovery around 5.90~6.15
trim-review 5.91~6.15
downside review around 5.30 if supported

WULF
SELL
2.5:7.5
entry only after recovery around 16.2~16.8
trim-review 15.55~16.46
downside review/invalidation around 14.80 if supported
```

This reference is not authoritative truth.
It is an independent comparator.

---

# 24. Comparison metrics

For every ticker compare:

```text
decision label
buy balance
sell balance
new-buyer stance
entry type
entry zone
holder stance
trim zone
downside review
business-thesis interpretation
valuation interpretation
price/timing interpretation
top BUY drivers
top SELL drivers
```

---

# 25. Label / balance comparison

Record:

```text
label_match = true/false
buy_balance_delta = abs(Codex buy - reference buy)
```

Classify:

```text
BALANCE_NEAR       <= 0.5
BALANCE_MODERATE   = 1.0
BALANCE_MATERIAL   >= 1.5
```

Do not declare one model correct solely because it matches.

---

# 26. Price-zone comparison

For two numeric zones A/B, compare:

```text
overlap?
lower-bound delta %
upper-bound delta %
same underlying price structure?
```

Classify:

```text
SAME_ZONE
OVERLAPPING_ZONE
DIFFERENT_BUT_SAME_BASIS
DIFFERENT_BASIS
ONE_SIDE_WITHHELD
```

A Codex zone that is more conservative but supported is not automatically an error.

---

# 27. Reasoning-difference taxonomy

For each material difference choose one or more:

```text
BUSINESS_EVIDENCE_WEIGHT
EARNINGS_FCF_WEIGHT
MARKET_EXPECTATION_WEIGHT
VALUATION_WEIGHT
PRICE_TIMING_WEIGHT
RISK_WEIGHT
TECHNICAL_CONTEXT_WEIGHT
PRICE_ZONE_DERIVATION
EVIDENCE_AVAILABILITY
OTHER
```

This is summary attribution, not hidden chain-of-thought.

---

# 28. Most important comparison question

For every disagreement answer:

```text
Did Codex use a different verified fact,
or did it interpret the same facts differently?
```

Classify:

```text
DIFFERENT_FACT_SURFACE
SAME_FACT_DIFFERENT_INTERPRETATION
```

This is essential for deciding whether the production decision contract needs further work.

---

# 29. Entry/trim quality audit

Independently of reference agreement, assess Codex zones:

```text
SUPPORTED
TOO_WIDE
TOO_NARROW
NOT_ACTIONABLE
TARGET_LIKE_OVERREACH
UNSUPPORTED
```

No zone passes merely because the reference has the same number.

---

# 30. Message-quality comparison

For every Codex message score qualitatively:

```text
decision clarity
balance usefulness
new-buyer usefulness
holder usefulness
price-zone clarity
duplication
verbosity
internal consistency
```

Classify overall:

```text
READY_STYLE
NEEDS_MINOR_EDIT
NEEDS_STRUCTURAL_EDIT
```

---

# 31. No production decision tuning

Do not modify the model/prompt after seeing the comparison in this task.

The purpose is measurement.

If Codex differs materially:

```text
report
```

Do not iteratively tune it to match the reference.

Hard:

```text
POST_COMPARISON_PROMPT_TUNING = 0
```

---

# 32. Required reports

Create:

1. `docs/reports/20260903-shadow-decision-experiment-source-lock.md`
2. `docs/reports/20260903-shadow-decision-contract.md`
3. `docs/reports/20260903-shadow-price-map.md`
4. `docs/reports/20260903-shadow-entry-zone-contract.md`
5. `docs/reports/20260903-shadow-holder-trim-zone-contract.md`
6. `docs/reports/20260903-shadow-candidates.md`
7. `docs/reports/20260903-shadow-validation.md`
8. `docs/reports/20260903-shadow-adjudication-accepted.md`
9. `docs/reports/20260903-shadow-message-quality.md`
10. `docs/reports/20260903-shadow-exact-message-index.md`
11. `docs/reports/20260903-shadow-vs-reference-label-balance-comparison.md`
12. `docs/reports/20260903-shadow-vs-reference-price-zone-comparison.md`
13. `docs/reports/20260903-shadow-vs-reference-reason-differences.md`
14. `docs/reports/20260903-shadow-vs-reference-message-comparison.md`
15. `docs/reports/20260903-shadow-decision-structure-verdict.md`
16. `docs/reports/20260903-shadow-decision-artifact-index.md`

Machine-readable:

```text
docs/reports/20260903-shadow-decisions.json
docs/reports/20260903-shadow-price-zones.json
docs/reports/20260903-shadow-reference-comparison.json
docs/reports/20260903-shadow-experiment-proof.json
```

Exact message artifacts:
```text
docs/reports/messages/CORZ.txt
...
docs/reports/messages/WULF.txt
docs/reports/20260903-us14-shadow-decision-message-preview.md
```

---

# 33. Required gates

Set exactly:

```text
RUN53_SOURCE_PACKET =
2026-09-03-us-run-53-055ae8ea01f6

RUN53_FROZEN_COHORT_COUNT =
14 / OTHER

FRESH_FACT_COLLECTION =
0 / NONZERO

POST_RUN53_FACT_LEAKAGE =
0 / NONZERO

REFERENCE_MANUAL_VIEW_VISIBLE_DURING_GENERATION =
0 / NONZERO

PRIOR_ACCEPTED_USED_TO_ANCHOR_FRESH_BALANCE =
0 / NONZERO

FIXED_FACTOR_WEIGHTED_SCORE =
0 / NONZERO

BALANCE_PROBABILITY_LANGUAGE =
0 / NONZERO

BALANCE_SUM_INVALID =
0 / NONZERO

PRICE_TIMING_AUTOMATICALLY_CHANGES_BUSINESS_THESIS =
0 / NONZERO

UNSUPPORTED_ENTRY_ZONE =
0 / NONZERO

UNSUPPORTED_TRIM_ZONE =
0 / NONZERO

TRIM_ZONE_RENDERED_AS_MANDATORY_SELL =
0 / NONZERO

INVENTED_STOP_LOSS =
0 / NONZERO

SHADOW_MODEL_REACHED =
PASS / FAIL

SHADOW_CANDIDATE_COUNT =
14 / OTHER

SHADOW_VALIDATION_PASS_COUNT =
14 / OTHER

PRODUCTION_ACCEPTED_STATE_MUTATION =
0 / NONZERO

COMMON_ORDER_DISCLAIMER_OCCURRENCE =
0 / NONZERO

PHASE1_ARTIFACTS_FROZEN =
PASS / FAIL

REFERENCE_LABEL_MATCH_COUNT =
...

REFERENCE_BALANCE_NEAR_COUNT =
...

REFERENCE_BALANCE_MODERATE_COUNT =
...

REFERENCE_BALANCE_MATERIAL_COUNT =
...

ENTRY_ZONE_SAME_OR_OVERLAP_COUNT =
...

TRIM_ZONE_SAME_OR_OVERLAP_COUNT =
...

SUPPORTED_CODEX_ENTRY_ZONE_COUNT =
...

SUPPORTED_CODEX_TRIM_ZONE_COUNT =
...

POST_COMPARISON_PROMPT_TUNING =
0 / NONZERO

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT =
0 / NONZERO

SHADOW_MESSAGE_STYLE =
READY /
NEEDS_MINOR_EDIT /
NEEDS_STRUCTURAL_EDIT

SHADOW_DECISION_STRUCTURE_VERDICT =
PROMISING /
MIXED /
NOT_READY
```

---

# 34. Completion response

Return:

```text
SOURCE_PACKET =
...

MODEL/RUNTIME =
...

SHADOW_DECISIONS =
CORZ label / BUY:SELL / new-buyer / entry / holder / trim ...
CPNG ...
CRCL ...
GOOGL ...
HUT ...
IBM ...
MU ...
RXRX ...
SKHY ...
SNDK ...
TSLA ...
TSM ...
WRD ...
WULF ...

DISTRIBUTION =
BUY ...
HOLD ...
SELL ...

REFERENCE_COMPARISON =
label matches ...
balance near/moderate/material ...
entry overlap ...
trim overlap ...

MATERIAL_DIFFERENCES =
ticker / Codex / reference / fact-surface-vs-interpretation / difference type ...

MESSAGE_QUALITY =
...

SHADOW_DECISION_STRUCTURE_VERDICT =
...

PRODUCTION_MUTATIONS = 0
PRODUCTION_SEND = 0

ZIP = ...
ZIP_SHA256 = ...
```

Also surface the combined exact message preview file prominently.

---

# 35. Mandatory completion ZIP

Create:

`20260903-codex-shadow-decision-structure-message-comparison-bundle.zip`

Include:
- exact instruction
- track instructions
- source-lock evidence
- price maps
- shadow candidates
- validation
- shadow adjudication/accepted
- exact 14 rendered messages
- combined preview
- optional TEST-recipient receipts
- blind reference-comparison reports
- JSON
- artifact index

Exclude:
- production recipient IDs
- TEST recipient ID
- auth/session tokens
- credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 36. Final principle

This is an A/B-style judgment comparison, not a production tuning exercise.

Codex must judge first.

The independent reference is revealed only after Codex output is frozen.

The useful result is not simply:

```text
"same" or "different"
```

but:

```text
where does Codex differ,
is the difference caused by a different fact surface or different interpretation,
and are its entry/trim zones actually supported by the verified price structure?
```

Do not modify production based on this experiment until the comparison is reviewed.
