# thesis-monitor — Structured Autonomy Decision V2 Shadow Refinement
## Preserve model judgment autonomy while enforcing a consistent investment-reasoning structure
## Refine dual entry modes, holder price review zones, accepted-plan authority, HOLD lean-flip guards, and sector-aware Unknown handling
## Re-run frozen US14 shadow experiment before any production promotion

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Baseline source packet: `2026-09-03-us-run-53-055ae8ea01f6`
- Baseline cohort: US/foreign 14
- Prior shadow experiment verdict: `PROMISING`
- Prior shadow distribution: `BUY 0 / HOLD 10 / SELL 4`
- Prior material label differences vs independent reference:
  - MU: Codex HOLD vs reference BUY
  - RXRX: Codex SELL vs reference HOLD
  - WRD: Codex HOLD vs reference SELL
- Task class:
  `SHADOW_DECISION_REFINEMENT + MESSAGE_SEMANTIC_OWNERSHIP + STRUCTURED_AUTONOMY`
- Production Assist: preserve `OFF`
- Production decision mutation: `0`
- Production accepted-plan mutation: `0`
- Production notification mutation: `0`
- Production recipient send: `0`
- Main merge: `0` unless explicitly approved after review
- Fresh data collection: `0`

This task does not promote the experimental decision structure to production.

---

# 1. Core design principle — structured autonomy, not mechanical scoring

The purpose is NOT to turn investment judgment into a fixed numerical formula.

The purpose is:

```text
give the model a stable reasoning structure,
require evidence-backed outputs,
and express the model's final directional synthesis in a coarse BUY:SELL balance.
```

Hard rules:

```text
FIXED_FACTOR_WEIGHTING = 0
SUBSCORE_SUMMATION_FORMULA = 0
UNIVERSAL_SECTOR_AGNOSTIC_SCORECARD = 0
BALANCE_AS_PROBABILITY = 0
```

Forbidden examples:

```text
business quality = 30 points
valuation = 20 points
price = 20 points
macro = 10 points
sum >= 70 => BUY
```

Required approach:

```text
Fact
→ interpret business / earnings
→ interpret market expectations
→ interpret valuation
→ interpret price / timing
→ interpret risks
→ synthesize BUY drivers and SELL drivers
→ model independently chooses directional balance
→ deterministic label derives from balance
```

The model retains judgment over:
- which facts matter most
- sector-specific importance
- evidence quality
- asymmetry
- confirmation cost
- risk interaction
- whether price/timing should materially affect current actionability

The system constrains:
- reasoning order
- evidence provenance
- unsupported-number generation
- label consistency
- semantic ownership
- change diagnostics

---

# 2. Directional balance contract

Directional balance remains a coarse representation of the final synthesis.

Required:

```text
BUY + SELL = 10
increments = 0.5
```

Examples:

```text
6.5 : 3.5
6.0 : 4.0
5.5 : 4.5
5.0 : 5.0
4.5 : 5.5
4.0 : 6.0
```

Label:

```text
BUY if buy >= 6.0
SELL if sell >= 6.0
HOLD otherwise
```

The model must NOT derive the balance from fixed factor weights.

Instead:

```text
balance = coarse final judgment after qualitative synthesis
```

Required candidate explanation:

```text
top BUY drivers
top SELL drivers
which evidence dominated the final balance
what uncertainty prevented a stronger balance
```

This is an output explanation, not hidden chain-of-thought.

---

# 3. Preserve factor independence

The following remain separate contexts:

```text
business_thesis_change
earnings_estimate_context
market_expectation_context
valuation_context
price_timing_context
risk_context
```

Do not collapse them into one score.

Examples:

```text
strong business + expensive price
→ HOLD can be correct

weak business + very depressed expectations
→ HOLD can be correct

strong business + attractive valuation + favorable price
→ BUY can be correct
```

Price/timing must not automatically modify business thesis state.

---

# 4. Sector-aware judgment and Unknown handling

Codex must interpret evidence in sector context.

General rule:

```text
industry-normal characteristic
!= automatic negative evidence
```

Examples:
- biotech cash burn is not automatically SELL evidence
- memory low forward PER near cycle peak is not automatically BUY evidence
- banks/insurers require sector-appropriate capital/earnings metrics
- ADR/security-basis limitations reduce certainty rather than inviting unsafe calculations

Unknown rule:

```text
Unknown != SELL evidence
```

Unknown should normally affect:

```text
confidence
decision strength
need-for-confirmation
```

rather than directional balance directly.

Exception:
Unknown may be directionally negative only when the absence itself is economically meaningful and explicitly supported, e.g.:
- required financing visibility missing while runway is demonstrably short
- promised customer conversion data repeatedly absent after stated milestone
- legally required disclosure missing or delayed in a material way

Hard:

```text
UNKNOWN_AUTOMATIC_SELL_PENALTY = 0
SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_SELL_PENALTY = 0
```

For biotech specifically:
do not use generic burn/negative FCF as decisive SELL evidence unless paired with a deterioration signal such as:
- worsening runway
- financing stress
- failed clinical milestones
- partner withdrawal
- repeated unfavorable trial evidence
- significantly worse-than-expected burn

---

# 5. New-buyer view — dual entry mode

The prior shadow experiment showed that valid differences often came from:

```text
support/pullback entry
vs
breakout/confirmation entry
```

Do not force the model to choose only one numeric entry concept.

New schema:

```json
{
  "stance": "ATTRACTIVE|WAIT|AVOID",
  "summary": "",
  "pullback_entry_zone_low": null,
  "pullback_entry_zone_high": null,
  "pullback_entry_basis": [],
  "breakout_confirmation_level": null,
  "breakout_confirmation_basis": [],
  "preferred_entry_mode": "PULLBACK|CONFIRMATION|BOTH|NONE",
  "preferred_entry_reason": ""
}
```

Repository-native equivalents allowed.

Required behavior:

```text
if both are supported:
preserve both

if only support is supported:
show pullback only

if only confirmation is supported:
show confirmation only

if neither is safely supported:
show neither
```

Do not fabricate a support entry solely because a confirmation level exists.
Do not fabricate a confirmation level solely because support exists.

---

# 6. New-buyer price-zone safety

Allowed numeric bases:
- verified dynamic support
- verified structural support
- registered support
- verified resistance recovery / breakout confirmation
- valuation + price structure overlap when safely supported

Forbidden:
- arbitrary percentage discount
- round-number target
- invented technical level
- unsupported Fibonacci
- provider multiple reverse-engineering

Required:

```text
UNSUPPORTED_PULLBACK_ZONE = 0
UNSUPPORTED_CONFIRMATION_LEVEL = 0
```

---

# 7. Holder view

Holder view remains generic and does not use personal cost basis.

Schema:

```json
{
  "stance": "HOLDABLE|REVIEW|REDUCE",
  "summary": "",
  "upside_trim_zone_low": null,
  "upside_trim_zone_high": null,
  "upside_trim_basis": [],
  "downside_review_level": null,
  "downside_review_basis": [],
  "business_invalidation_condition": ""
}
```

Meaning:

```text
upside trim zone
= reassess valuation/expectations/earnings at this price region
!= automatic sell target
```

Downside review remains separate from upside trim.

No invented stop-loss.

---

# 8. Accepted-plan semantic ownership

The prior shadow messages showed a risk of contradictory wording such as:

```text
top block:
business logic weakened

legacy/detail body:
investment logic maintained
```

Fix semantic ownership.

The accepted shadow plan must be the ONLY authority for judgment-bearing language:

```text
decision
directional balance
business thesis state
core judgment
new-buyer view
holder view
re-evaluation conditions
```

The detailed factual body may own:

```text
company facts
business/earnings facts
market expectations evidence
price structure facts
valuation facts
supply/positioning facts
data caveats
next checkpoints
```

It must NOT independently render a conflicting judgment state.

Hard:

```text
DUPLICATE_JUDGMENT_AUTHORITY = 0
CONTRADICTORY_THESIS_STATE_LINES = 0
```

Implementation options:
- remove legacy judgment-bearing lines from the detail renderer
- or source them directly from accepted plan

Do not maintain two independent judgment sources.

---

# 9. HOLD lean state

Because HOLD can hide meaningful directional differences, derive:

```text
BUY_LEAN
NEUTRAL
SELL_LEAN
```

Suggested deterministic mapping:

```text
BUY_LEAN:
buy = 5.5 and sell = 4.5

NEUTRAL:
5.0 : 5.0

SELL_LEAN:
4.5 : 5.5
```

For BUY/SELL labels, lean state may be omitted or mapped naturally.

This is not a new score.
It is a derived descriptor of the existing balance.

---

# 10. HOLD lean-flip diagnostic

A HOLD label can remain unchanged while direction reverses.

Example:

```text
prior 5.5 : 4.5 HOLD
current 4.5 : 5.5 HOLD
```

This must NOT be treated as "no meaningful change."

Record:

```text
lean_flip = true
```

when:

```text
BUY_LEAN ↔ SELL_LEAN
```

even if label remains HOLD.

Required diagnostic fields:

```text
prior_label
prior_balance
prior_lean
current_candidate_label
current_candidate_balance
current_candidate_lean
accepted_label
accepted_balance
accepted_lean
lean_flip
evidence_delta_summary
```

Hard:

```text
HOLD_LEAN_FLIP_INVISIBLE = 0
```

---

# 11. Same-evidence drift

Keep existing same-evidence drift diagnostics.

For same evidence fingerprint:

```text
balance delta <= 0.5
→ minor

balance delta = 1.0
→ moderate

balance delta >= 1.5
→ material
```

Additionally:

```text
BUY_LEAN ↔ SELL_LEAN
```

is always review-worthy even if total balance distance is only 1.0.

No production majority voting.

Production architecture remains conceptually:

```text
one fresh candidate
→ adjudication if needed
→ one accepted plan
```

Repeated executions remain diagnostics only.

---

# 12. Fresh-candidate independence

Prior accepted state must not anchor fresh judgment.

Required order:

```text
1. generate fresh business/expectation/valuation/price/risk interpretation
2. generate BUY/SELL drivers
3. generate fresh balance
4. derive fresh label
5. freeze fresh candidate
6. only then compare against prior accepted
7. adjudicate if needed
```

Hard:

```text
PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE = 0
```

---

# 13. Re-evaluation / adjudication triggers

Adjudication should be required when any of:

```text
label changes
balance delta >= 1.0
BUY_LEAN ↔ SELL_LEAN
same-evidence material drift
business thesis invalidation candidate
material valuation-context change
material price-rule state change
```

Do not adjudicate every stock by default if native architecture supports selective adjudication safely.

---

# 14. Message renderer V2 shadow format

Target user-facing structure:

```text
🏢 Company(TICKER)

🧠 AI 분석 판단: HOLD
판단 균형: BUY 5.5 : SELL 4.5
판단 방향: BUY 쪽 HOLD
판단 확신도: 중간

🎯 핵심 판단
• ...

🆕 신규진입 관점
• 현재 관점: WAIT
• 눌림 진입 검토: $...
• 추세 확인 가격: $...
• 현재 선호: 눌림 / 확인 / 둘 다 / 없음
• 이유: ...

💼 보유자 관점
• 현재 관점: HOLDABLE / REVIEW / REDUCE
• 상방 매도·축소 검토: $...
• 하방 재점검: $...
• 기업가치 무효화 조건: ...

🔄 재평가 조건
• BUY 쪽: ...
• SELL 쪽: ...

[detail body]
사업/실적 사실
시장 기대
가격 구조
Valuation
수급 if available
데이터 주의
다음 확인
```

If a numeric field is unavailable, omit it cleanly.

No blank placeholder sections.

---

# 15. Language rules

Use:

```text
진입 검토 구간
추세 확인 가격
매도·축소 검토 구간
하방 재점검
기업가치 무효화 조건
```

Avoid implying:
- guaranteed target
- mandatory sell
- stop-loss order
- probability from balance

Required:

```text
MANDATORY_TRADE_LANGUAGE = 0
```

---

# 16. Phase A — implementation in shadow namespace

Implement the refined decision contract and renderer only in shadow/test paths.

Production authoritative behavior must remain unchanged.

Required:
- temporary/shadow schemas
- validation rules
- semantic ownership
- lean derivation
- dual entry support
- sector/Unknown policy

No production main merge.

---

# 17. Phase B — frozen US14 shadow rerun

Use exact frozen run-53 evidence again:

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

No fresh data.

Use signed-in Codex path consistent with the prior shadow experiment.

Required:

```text
FROZEN_EVIDENCE_COUNT = 14
FRESH_FACT_COLLECTION = 0
MODEL_REACHED = PASS
CANDIDATE_COUNT = 14
VALIDATED_COUNT = 14
```

---

# 18. Phase C — compare against prior shadow run

Compare refined run to prior shadow experiment.

Per ticker compare:
- decision
- balance
- lean
- business thesis context
- new-buyer stance
- pullback zone
- confirmation level
- preferred entry mode
- holder stance
- trim zone
- downside review
- message consistency

Special attention:

```text
MU
RXRX
WRD
CPNG
SNDK
```

Reason:
- prior label disagreements
- prior balance-direction disagreements
- sector/Unknown sensitivity
- support vs confirmation divergence

Do not force convergence.

---

# 19. Phase D — RXRX sector-aware audit

For RXRX, explicitly audit whether the prior SELL decision relied on:

```text
generic biotech cash burn
negative FCF
dilution risk
```

without evidence of deterioration.

Classify each SELL driver:

```text
SECTOR_NORMAL
DETERIORATION_SIGNAL
STRUCTURAL_RISK
UNKNOWN
```

If the decision remains SELL, document the evidence that makes it more than normal biotech-stage risk.

No prompt tuning after seeing the result in the same run.

---

# 20. Phase E — MU cycle-aware audit

For MU, ensure:
- low forward PER alone cannot drive BUY
- high PBR / cycle position / high expectations are considered
- HBM demand, FCF, confirmation, and cycle risk are interpreted together

Do not hardcode MU-specific rules.
Implement via memory/semiconductor sector reasoning contract where appropriate.

---

# 21. Phase F — WRD uncertainty audit

For WRD, determine whether missing valuation/unit-economics certainty should:

```text
reduce confidence
```

or:

```text
increase SELL balance
```

Unknown alone must not automatically produce SELL.

If HOLD remains, explain why.
If SELL emerges, require deterioration evidence or clearly asymmetric downside.

---

# 22. Validation

Required validation layers:

```text
schema
balance sum/increments
deterministic label
lean derivation
evidence provenance
numeric provenance
valuation safety
price-zone provenance
entry-mode consistency
holder-zone semantics
sector-aware Unknown handling
accepted-plan semantic ownership
message contradiction scan
identity/language
```

Hard:

```text
VALIDATION_PASS_COUNT = 14
UNSUPPORTED_PRICE_NUMERIC = 0
MESSAGE_INTERNAL_CONTRADICTION = 0
```

---

# 23. Message quality gates

For each ticker check:

```text
decision and balance consistent
lean text consistent
new-buyer stance understandable
pullback/confirmation distinction clear
holder trim not rendered as mandatory sell
downside review separate
no conflicting thesis-state lines
no duplicated judgment paragraphs
detail body factual rather than judgment-duplicating
```

Overall classify:

```text
READY_STYLE
NEEDS_MINOR_EDIT
NEEDS_STRUCTURAL_EDIT
```

---

# 24. Required reports

Create:

1. `docs/reports/20260903-structured-autonomy-contract.md`
2. `docs/reports/20260903-sector-aware-unknown-policy.md`
3. `docs/reports/20260903-dual-entry-mode-contract.md`
4. `docs/reports/20260903-holder-price-review-contract.md`
5. `docs/reports/20260903-accepted-plan-semantic-ownership.md`
6. `docs/reports/20260903-hold-lean-and-drift-guard.md`
7. `docs/reports/20260903-us14-refined-shadow-candidates.md`
8. `docs/reports/20260903-us14-refined-shadow-validation.md`
9. `docs/reports/20260903-us14-refined-shadow-messages.md`
10. `docs/reports/20260903-us14-refined-vs-prior-shadow.md`
11. `docs/reports/20260903-rxrx-sector-aware-audit.md`
12. `docs/reports/20260903-mu-cycle-aware-audit.md`
13. `docs/reports/20260903-wrd-uncertainty-audit.md`
14. `docs/reports/20260903-structured-autonomy-shadow-verdict.md`
15. `docs/reports/20260903-structured-autonomy-artifact-index.md`

Machine-readable:
- `20260903-refined-shadow-decisions.json`
- `20260903-refined-price-entry-holder-views.json`
- `20260903-refined-vs-prior-shadow.json`
- `20260903-structured-autonomy-proof.json`

Exact message files:
- one UTF-8 `.txt` per ticker
- one combined preview

---

# 25. Required gates

Set exactly:

```text
FIXED_FACTOR_WEIGHTING =
0 / NONZERO

SUBSCORE_SUMMATION_FORMULA =
0 / NONZERO

UNIVERSAL_SECTOR_AGNOSTIC_SCORECARD =
0 / NONZERO

BALANCE_AS_PROBABILITY =
0 / NONZERO

UNKNOWN_AUTOMATIC_SELL_PENALTY =
0 / NONZERO

SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_SELL_PENALTY =
0 / NONZERO

UNSUPPORTED_PULLBACK_ZONE =
0 / NONZERO

UNSUPPORTED_CONFIRMATION_LEVEL =
0 / NONZERO

DUPLICATE_JUDGMENT_AUTHORITY =
0 / NONZERO

CONTRADICTORY_THESIS_STATE_LINES =
0 / NONZERO

HOLD_LEAN_FLIP_INVISIBLE =
0 / NONZERO

PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE =
0 / NONZERO

MANDATORY_TRADE_LANGUAGE =
0 / NONZERO

FROZEN_EVIDENCE_COUNT =
14 / OTHER

FRESH_FACT_COLLECTION =
0 / NONZERO

MODEL_REACHED =
PASS / FAIL

CANDIDATE_COUNT =
14 / OTHER

VALIDATION_PASS_COUNT =
14 / OTHER

UNSUPPORTED_PRICE_NUMERIC =
0 / NONZERO

MESSAGE_INTERNAL_CONTRADICTION =
0 / NONZERO

PRODUCTION_ACCEPTED_STATE_MUTATION =
0 / NONZERO

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

REFINED_MESSAGE_STYLE =
READY_STYLE /
NEEDS_MINOR_EDIT /
NEEDS_STRUCTURAL_EDIT

REFINED_STRUCTURE_VERDICT =
PROMISING /
MIXED /
NOT_READY
```

---

# 26. Completion response

Return:

```text
SOURCE_PACKET =
...

MODEL/RUNTIME =
...

STRUCTURED_AUTONOMY =
PASS/FAIL
fixed weighting = 0/...
formulaic scoring = 0/...

US14_REFINED_DECISIONS =
ticker / label / balance / lean / new-buyer / pullback / confirmation / preferred mode / holder / trim / downside review

DISTRIBUTION =
...

PRIOR_SHADOW_COMPARISON =
label changes ...
balance changes ...
lean flips ...
entry-mode differences ...

SPECIAL_AUDITS =
RXRX ...
MU ...
WRD ...

SEMANTIC_OWNERSHIP =
PASS/FAIL

MESSAGE_QUALITY =
...

REFINED_STRUCTURE_VERDICT =
...

PRODUCTION_MUTATION = 0
PRODUCTION_SEND = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 27. Mandatory completion ZIP

Create:

`20260903-structured-autonomy-decision-v2-shadow-refinement-bundle.zip`

Include:
- exact work instructions
- implementation diff
- schema/validator changes
- shadow candidates
- price/entry/holder artifacts
- 14 exact rendered messages
- combined preview
- special audits
- prior comparison
- JSON
- artifact index
- secret scan

Exclude:
- credentials
- auth/session tokens
- production recipient IDs
- hidden chain-of-thought
- state DB contents

Compute SHA-256.

---

# 28. Final principle

The decision system should be:

```text
structured enough to be consistent,
free enough to remain intelligent.
```

The numerical balance is a compact representation of judgment.

It is not the judgment engine itself.

Do not replace sector-aware qualitative reasoning with a universal formula.
