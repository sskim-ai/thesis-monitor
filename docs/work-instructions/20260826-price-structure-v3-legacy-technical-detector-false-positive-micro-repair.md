# thesis-monitor — Price Structure v3 Legacy Technical Detector False-Positive Micro Repair
## Fix `Recursion` → `RSI` substring suppression
## Token / semantic-field scoped detection + protected message structure
## Final bounded repair before selective production enablement
## No calculation-engine changes; no live enablement in this task

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_LEGACY_TECHNICAL_DETECTOR_FALSE_POSITIVE_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_RENDERER_P1_REPAIR`
- Source policy: `FREE_ONLY`
- Current v3 state: `INTEGRATED_READY_NOT_ARMED`
- Production Assist: preserve `OFF`
- Trade AR: preserve `OFF`
- Open Research production integration: preserve `0`
- User-visible production mutation: `0`
- Telegram send: `0`
- Manual scheduled task: `0`
- DB / official assessment mutation: `0`
- Public Action / operationId / schema: preserve current values

### Required base

Latest reported safe final/main/operating:

`a4c6713649137180e0b37a4eb42ae6b35f07423c`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous renderer integration result

```text
Instruction:
2ac7eaaede9cb8d9047173bbec5f2bd99c665573

Implementation:
4246efb4f8afa3516402d1df7864967c177ac6e7

Final/main/operating:
a4c6713649137180e0b37a4eb42ae6b35f07423c

PRICE_STRUCTURE_V3_RENDERER_INTEGRATION =
INTEGRATED_READY_NOT_ARMED

PRODUCTION_ENABLEMENT_READY = YES

Full pytest = 1717 passed
Runtime-visible diff = 0
Production Assist = OFF
```

### Newly discovered exact-message defect

The immutable renderer bundle contains this exact RXRX diff:

```diff
--- RXRX-before
+++ RXRX-after
@@
-🏢 Recursion Pharmaceuticals(RXRX)
-
 투자 논리: 유지 · 오늘 중요한 신규 변화 없음
```

The company header was suppressed.

The most likely root cause to verify is a case-insensitive substring detector such as:

```text
"rsi" in text.lower()
```

because:

```text
Recursion
   rsi
```

contains the character sequence `rsi`.

Do not assume the exact code path until audited, but treat this as a material renderer P1.

---

# 0. Objective

Fix legacy-technical-prose detection so that:

```text
actual technical terms
→ can be detected

ordinary words containing those letter sequences
→ are never detected solely by substring

company name / ticker / header / section title
→ cannot be suppressed by legacy technical filtering
```

Then re-run all 20 exact candidate messages and prove:

```text
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
NON_TECHNICAL_PROSE_SUPPRESSED = 0
```

while preserving the intended MU stale technical-prose suppression.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-price-structure-v3-legacy-technical-detector-false-positive-micro-repair.md`

Then:

1. `git fetch origin`
2. verify clean worktree
3. resolve latest safe main/operating SHA
4. commit this exact instruction docs-only
5. create branch:

`codex/price-structure-v3-legacy-detector-false-positive-repair`

6. use latest safe main as base
7. no force push/history rewrite
8. remain shadow-only
9. do not enable production in this task

---

# 2. Hard prohibitions

Do NOT:

- change SR calculations
- change Fib calculations
- change wave selection
- change family consensus
- change confluence eligibility
- change nearest/major ranking
- change OHLCV acquisition
- weaken stale legacy technical suppression globally
- whitelist RXRX by ticker only
- hard-code `Recursion` as a special exception
- remove all RSI/MACD detection
- suppress business/fundamental prose to make tests pass
- modify stored price rules
- enable live renderer
- send Telegram
- manually execute scheduled tasks
- mutate DB / assessment state

---

# 3. Root-cause audit — mandatory

Trace the exact suppression path:

```text
message block / line / sentence
→ legacy technical classifier
→ technical term detector
→ suppression decision
→ renderer output
```

Record:

```text
input text
field/section identity
matched detector
matched token/pattern
classification
suppression reason
```

For RXRX prove why:

```text
🏢 Recursion Pharmaceuticals(RXRX)
```

was classified/suppressed.

Set:

`RXRX_HEADER_FALSE_POSITIVE_ROOT_CAUSE = PASS / FAIL`

---

# 4. Detector ownership

Legacy technical detection must be **semantic-field aware**.

Do not run a generic free-form substring suppressor across the entire rendered message.

At minimum distinguish:

```text
PROTECTED_STRUCTURAL_FIELD
BUSINESS_PROSE
TECHNICAL_PROSE_CANDIDATE
STORED_PRICE_RULE
CURRENT_V3_PRICE_STRUCTURE
VALUATION_PROSE
OTHER
```

Only intended candidate fields may be evaluated for legacy technical suppression.

---

# 5. Protected structural fields — never suppress by technical keyword detector

At minimum protect:

```text
company header
company name
ticker
market/security label
section headings
investment logic status line
structural risk line
market expectation line
price section heading
valuation heading
next-check heading
```

The technical suppressor may not delete them even if their text happens to contain indicator-like letter sequences.

Hard target:

`PROTECTED_FIELD_SUPPRESSED = 0`

---

# 6. Technical indicator lexical policy

For lexical indicator detection, use proper token/word-boundary semantics.

At minimum:

```text
RSI
MACD
OHLCV
Bollinger
ATR
EMA
SMA
```

where relevant to current legacy policy.

Do not match these as arbitrary substrings inside ordinary words.

Examples:

```text
"RSI 72"              → indicator token
"RSI가 과열"           → indicator token
"MACD histogram"      → indicator token
"OHLCV 기준"           → technical token

"Recursion"           → NOT RSI
"version"             → NOT RSI
"conversion"          → NOT RSI
"macdonald"           → NOT MACD
```

Case handling must preserve token semantics.

---

# 7. Word-boundary implementation caveat

Do not blindly depend on ASCII `\b` if Korean postpositions are attached.

Valid technical forms may include:

```text
RSI가
RSI는
MACD가
OHLCV를
```

Use a robust token rule such as:

```text
indicator acronym
followed by:
  whitespace
  punctuation
  number
  Korean postposition boundary
  end-of-string
```

and suitable preceding boundary.

Document the implemented lexical contract.

---

# 8. Semantic-field-first policy

Lexical matching alone is insufficient.

Preferred pipeline:

```text
1. determine whether text is in a field eligible for legacy technical suppression
2. then apply technical token recognition
3. then apply freshness/redundancy policy
4. then suppress only the technical clause/sentence
```

Do not classify the entire rendered message from global keyword scanning.

---

# 9. Clause-level suppression

If a mixed sentence contains:

```text
business claim + stale technical clause
```

remove only the technical clause/sentence where safe.

Do not delete:

```text
company identity
business facts
earnings facts
valuation facts
risk facts
next-check facts
```

Hard targets:

```text
BUSINESS_FACT_CHANGED_BY_LEGACY_SUPPRESSION = 0
NON_TECHNICAL_CLAUSE_REMOVED = 0
```

---

# 10. RXRX mandatory negative control

Input must include:

```text
🏢 Recursion Pharmaceuticals(RXRX)
```

Expected:

```text
header preserved exactly
```

Set:

```text
RXRX_COMPANY_HEADER_PRESERVED = PASS
RXRX_FALSE_RSI_MATCH = 0
```

No ticker-specific whitelist.

---

# 11. Additional lexical negative controls

Add tests for ordinary words that contain indicator-like character sequences.

At minimum:

```text
Recursion
recursion
conversion
version
diversion
precision
decision
```

and any real company names / user-visible strings found in the 20-stock universe that contain
technical-acronym substrings.

Expected:

```text
false technical match = 0
```

---

# 12. Full company-header negative-control audit

For all 20 current monitored subjects, render the exact company header and run the detector.

Required:

```text
20/20 company headers preserved
20/20 company names preserved
20/20 tickers preserved
```

If current universe differs:
use actual current universe and report exact count/diff.

Hard targets:

```text
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
COMPANY_NAME_CHANGED_BY_LEGACY_SUPPRESSION = 0
TICKER_CHANGED_BY_LEGACY_SUPPRESSION = 0
```

---

# 13. Section-heading negative controls

Verify all canonical headings survive:

```text
🏢
🎯 핵심
📈 사업·실적
👁 핵심 감시
💰 가격
📐 현재 가격 구조
🧭 기존 등록 가격 규칙
📐 Valuation
📌 다음 확인
```

where present.

Hard target:

`SECTION_HEADING_SUPPRESSED = 0`

---

# 14. MU positive suppression control

The previous renderer repair intentionally removed stale legacy technical prose such as:

```text
2026-08-12 OHLCV 기준 ...
MACD ...
MACD histogram ...
```

while current v3 was based on the latest completed US session.

This behavior must remain.

Set:

```text
MU_STALE_LEGACY_TECHNICAL_SUPPRESSION = PASS
```

Do not fix RXRX by disabling the suppression feature.

---

# 15. Positive technical-token tests

Must still detect:

```text
RSI 72
RSI가 70을 상회
MACD histogram 둔화
MACD가 0선 아래
2026-08-12 OHLCV 기준
Bollinger 상단
ATR 확대
```

when they appear in eligible legacy-technical fields.

Set:

`REAL_TECHNICAL_TOKEN_DETECTION = PASS`

---

# 16. Freshness/redundancy policy unchanged

This repair does not redefine stale legacy prose policy.

Keep:

```text
current-session v3 active
+
older/redundant technical prose
→ suppress

current-session valid nonredundant indicator prose
→ may remain if existing policy permits
```

Only false-positive detection changes.

---

# 17. Current SR / stored rule ownership must not regress

Preserve previous PASS behavior:

```text
CURRENT_SR_STORED_RULE_SEPARATION = PASS
UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0
```

Mandatory controls:

```text
SNDK
MU
TSM
```

---

# 18. Fib range rendering must not regress

Preserve:

```text
SK hynix major structural resistance
vs
Fib/SR confluence extended range
```

The material Fib range must remain visible.

Hard targets:

```text
SK_HYNIX_FIB_RANGE_RENDER = PASS
MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0
```

---

# 19. SR-only safety must not regress

Preserve:

```text
TSLA SR-only
unstable Fib omitted
```

Hard target:

`TSLA_UNSTABLE_FIB_REINTRODUCED = 0`

---

# 20. 012450 family rendering must not regress

Preserve the prior fixed:

```text
012450 family PASS
```

Hard target:

`012450_FAMILY_RENDER_REGRESSION = 0`

---

# 21. Message-structure invariant

For each of 20 candidate messages, compare before/after repair.

The only intended difference should be:

```text
previously false-suppressed nontechnical text restored
```

plus any detector audit metadata.

No unrelated prose rewrite.

---

# 22. Exact structural invariants per message

At minimum compare:

```text
company header present
investment logic line present
structural risk line present if baseline has it
market expectation line present if baseline has it
core section present
business/earnings section present
watch section present
price section present
current price structure present if eligible
stored rule section present if applicable
valuation section present
next-check section present
```

Report missing/added structural components.

Hard target:

`UNINTENDED_MESSAGE_STRUCTURE_CHANGE = 0`

---

# 23. Nontechnical suppression audit

Create:

`NON_TECHNICAL_SUPPRESSION_AUDIT`

For every removed line/clause in all 20 after messages:

```text
text_ref
original text
classification
technical token refs
freshness
suppression reason
```

Every suppressed fragment must be explainable as valid legacy technical prose.

Hard target:

`UNEXPLAINED_SUPPRESSED_FRAGMENT = 0`

---

# 24. False-positive detector audit

For every line classified technical:

record:

```text
matched_term
match_span
token_boundary_type
semantic field
technical context evidence
```

Any match occurring only because letters appear inside a larger ordinary word is a failure.

Hard target:

`SUBSTRING_ONLY_TECHNICAL_MATCH = 0`

---

# 25. Company/entity preservation audit

Search exact before/after messages for:

```text
company name
ticker
security/ADR label if present
```

Hard target:

`ENTITY_LABEL_LOSS = 0`

---

# 26. Full current-data exact-message replay

Use safe current completed sessions.

At 2026-08-26 KST expected:

```text
KR = 2026-08-26 completed session
US = 2026-08-25 completed session
```

If execution occurs later:
resolve latest completed session dynamically.

Do not use partial US 2026-08-26 bar as complete.

---

# 27. Full universe exact-message artifact

Create:

`docs/reports/20260826-v3-legacy-detector-exact-candidate-messages.json`

Per stock:

```text
before_repair_message
after_repair_message
exact_diff

company_header_before
company_header_after

suppressed_fragments_before
suppressed_fragments_after

technical_matches
false_positive_matches

message eligibility
```

---

# 28. Required RXRX exact diff

Create an explicit report showing:

```text
before broken renderer
after repaired renderer
```

Expected semantic diff:

```diff
+🏢 Recursion Pharmaceuticals(RXRX)
+
 투자 논리: 유지 · 오늘 중요한 신규 변화 없음
```

with all intended prior renderer improvements preserved.

---

# 29. Message-quality review

Human-review all 20.

Questions:

```text
Is company identity intact?
Was any ordinary prose accidentally removed?
Are actual stale technical sentences still suppressed?
Is there only one current technical narrative?
Are current SR/stored rules still separated?
Is Fib range preserved where material?
```

Classify:

```text
PASS
SAFE_BUT_MINOR
FAIL
```

Hard target:

`FAIL_COUNT = 0`

---

# 30. Regression counters

Preserve prior rollout cohort unless a new real safety defect appears.

Expected previous:

```text
KR:
ELIGIBLE = 6
ELIGIBLE_SR_ONLY = 1
BLOCKED = 0

US:
ELIGIBLE = 4
ELIGIBLE_SR_ONLY = 9
BLOCKED = 0
```

Hard target:

`MESSAGE_ELIGIBILITY_REGRESSION = 0`

---

# 31. Numeric/calculation parity

This task is renderer classifier only.

Hard targets:

```text
RAW_SR_VALUE_CHANGED = 0
RAW_FIB_VALUE_CHANGED = 0
SR_ELIGIBILITY_CHANGED = 0
FIB_ELIGIBILITY_CHANGED = 0
CROSS_TIMEFRAME_RANKING_CHANGED = 0
```

---

# 32. Business/fundamental parity

Hard targets:

```text
BUSINESS_FACT_CHANGED_BY_LEGACY_SUPPRESSION = 0
BUSINESS_THESIS_CHANGED_BY_LEGACY_SUPPRESSION = 0
VALUATION_FACT_CHANGED_BY_LEGACY_SUPPRESSION = 0
NEXT_CHECK_CHANGED_BY_LEGACY_SUPPRESSION = 0
```

Restoring the RXRX company header is not a business-thesis change.

---

# 33. Stored-price-rule parity

Hard targets:

```text
STORED_PRICE_RULE_DATA_MUTATION = 0
STORED_PRICE_RULE_RENDER_REGRESSION = 0
CURRENT_SR_STORED_RULE_SEPARATION_REGRESSION = 0
```

---

# 34. Numeric provenance safety

Hard targets:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNREGISTERED_STORED_PRICE_RULE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

---

# 35. Temporal/security safety

Hard targets:

```text
WRONG_SESSION_DATA = 0
LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0
```

---

# 36. Production isolation

Hard targets:

```text
CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
PRODUCTION_FLAG_CHANGE = 0
```

No enablement here.

---

# 37. Focused tests — lexical false positives

Required:

```text
Recursion → false
recursion → false
conversion → false
version → false
precision → false
decision → false
```

for RSI detection.

Add analogous false-positive controls for other indicator acronyms if current implementation uses
substring matching.

---

# 38. Focused tests — Korean-attached technical tokens

Required positive detection:

```text
RSI가
RSI는
MACD가
OHLCV를
```

within eligible technical fields.

Required false detection:

```text
ordinary Korean/English text containing indicator letters internally
```

---

# 39. Focused tests — protected fields

Feed indicator-like strings into protected structural fields.

Expected:

```text
never suppressed by legacy technical policy
```

unless a separate renderer rule intentionally owns that field.

Examples:

```text
company_name = "Recursion Pharmaceuticals"
header = "🏢 Recursion Pharmaceuticals(RXRX)"
ticker = "RXRX"
```

---

# 40. Focused tests — MU positive control

Input stale MU technical prose.

Expected:

```text
stale technical sentence suppressed
business/fundamental message retained
```

---

# 41. Focused tests — exact message structure

Required:

```text
RXRX header restored
all 20 headers preserved
all section headings preserved
no unexpected blank first section
```

---

# 42. Required architecture/policy docs

Create/update:

1. `docs/architecture/LEGACY_TECHNICAL_TOKEN_DETECTION.md`
2. `docs/architecture/RENDERER_PROTECTED_STRUCTURAL_FIELDS.md`
3. update `LEGACY_TECHNICAL_PROSE_SUPPRESSION.md`
4. update `PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md`
5. update `PRICE_STRUCTURE_V3_SHADOW_POLICY.md`

---

# 43. Required reports

Create:

1. `docs/reports/20260826-v3-legacy-detector-false-positive-root-cause.md`
2. `docs/reports/20260826-v3-legacy-token-boundary-policy.md`
3. `docs/reports/20260826-v3-protected-structural-field-audit.md`
4. `docs/reports/20260826-v3-rxrx-header-regression.md`
5. `docs/reports/20260826-v3-legacy-detector-full-universe.md`
6. `docs/reports/20260826-v3-nontechnical-suppression-audit.md`
7. `docs/reports/20260826-v3-legacy-detector-exact-message-diff.md`
8. `docs/reports/20260826-v3-legacy-detector-message-quality.md`
9. `docs/reports/20260826-v3-legacy-detector-safety-parity.md`
10. `docs/reports/20260826-v3-legacy-detector-readiness.md`
11. `docs/reports/20260826-v3-legacy-detector-artifact-index.md`

Recommended:

`docs/reports/20260826-v3-legacy-detector-readiness.json`

---

# 44. Gates

Set exactly:

```text
RXRX_HEADER_FALSE_POSITIVE_ROOT_CAUSE =
PASS / FAIL

LEGACY_TECHNICAL_TOKEN_POLICY =
PASS / FAIL

SEMANTIC_FIELD_SCOPED_DETECTION =
PASS / FAIL

PROTECTED_STRUCTURAL_FIELDS =
PASS / FAIL

RXRX_COMPANY_HEADER_PRESERVED =
PASS / FAIL

RXRX_FALSE_RSI_MATCH =
0 / NONZERO

COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

COMPANY_NAME_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

TICKER_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

SECTION_HEADING_SUPPRESSED =
0 / NONZERO

PROTECTED_FIELD_SUPPRESSED =
0 / NONZERO

SUBSTRING_ONLY_TECHNICAL_MATCH =
0 / NONZERO

NON_TECHNICAL_PROSE_SUPPRESSED =
0 / NONZERO

NON_TECHNICAL_CLAUSE_REMOVED =
0 / NONZERO

UNEXPLAINED_SUPPRESSED_FRAGMENT =
0 / NONZERO

UNCLASSIFIED_TECHNICAL_PRICE_PROSE =
0 / NONZERO

REAL_TECHNICAL_TOKEN_DETECTION =
PASS / FAIL

MU_STALE_LEGACY_TECHNICAL_SUPPRESSION =
PASS / FAIL

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 =
0 / NONZERO

SK_HYNIX_FIB_RANGE_RENDER =
PASS / FAIL

CURRENT_SR_STORED_RULE_SEPARATION =
PASS / FAIL

TSLA_UNSTABLE_FIB_REINTRODUCED =
0 / NONZERO

012450_FAMILY_RENDER_REGRESSION =
0 / NONZERO

UNINTENDED_MESSAGE_STRUCTURE_CHANGE =
0 / NONZERO

ENTITY_LABEL_LOSS =
0 / NONZERO

MESSAGE_ELIGIBILITY_REGRESSION =
0 / NONZERO

FAIL_COUNT =
0 / NONZERO

RAW_SR_VALUE_CHANGED =
0 / NONZERO

RAW_FIB_VALUE_CHANGED =
0 / NONZERO

BUSINESS_FACT_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

BUSINESS_THESIS_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

CURRENT_RUNTIME_VISIBLE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_LEGACY_DETECTOR_REPAIR =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 45. Hard safety targets

```text
RXRX_FALSE_RSI_MATCH = 0

COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
COMPANY_NAME_CHANGED_BY_LEGACY_SUPPRESSION = 0
TICKER_CHANGED_BY_LEGACY_SUPPRESSION = 0
SECTION_HEADING_SUPPRESSED = 0
PROTECTED_FIELD_SUPPRESSED = 0

SUBSTRING_ONLY_TECHNICAL_MATCH = 0
NON_TECHNICAL_PROSE_SUPPRESSED = 0
NON_TECHNICAL_CLAUSE_REMOVED = 0
UNEXPLAINED_SUPPRESSED_FRAGMENT = 0

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0

SK_HYNIX_FIB_RANGE_RENDER = PASS
CURRENT_SR_STORED_RULE_SEPARATION = PASS
TSLA_UNSTABLE_FIB_REINTRODUCED = 0
012450_FAMILY_RENDER_REGRESSION = 0

RAW_SR_VALUE_CHANGED = 0
RAW_FIB_VALUE_CHANGED = 0

AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0

BUSINESS_FACT_CHANGED_BY_LEGACY_SUPPRESSION = 0
BUSINESS_THESIS_CHANGED_BY_LEGACY_SUPPRESSION = 0

LOOKAHEAD_LEAK = 0
SECURITY_BASIS_CONFLICT = 0

CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
PRODUCTION_FLAG_CHANGE = 0
```

---

# 46. Readiness

Set:

```text
PRICE_STRUCTURE_V3_LEGACY_DETECTOR_REPAIR =
INTEGRATED_READY_NOT_ARMED
```

and:

```text
PRODUCTION_ENABLEMENT_READY = YES
```

only if:

```text
RXRX header restored
all 20 entity headers/names/tickers preserved
no substring-only technical match
real RSI/MACD/OHLCV detection still works
MU stale technical prose still suppressed
no nontechnical prose removed
no message structure regression
SK hynix/SNDK/TSM ownership renderer remains safe
TSLA unstable Fib remains omitted
012450 remains safe
raw numerics unchanged
P0 = 0
material P1 = 0
```

---

# 47. Expected next action

If PASS:

```text
NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT
```

No additional renderer cleanup should be inserted unless this repair finds a new material defect.

---

# 48. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RXRX_HEADER_FALSE_POSITIVE_ROOT_CAUSE = ...
RXRX_FALSE_MATCHED_TERM = ...
RXRX_FALSE_MATCHED_SPAN = ...

LEGACY_TECHNICAL_TOKEN_POLICY = ...
SEMANTIC_FIELD_SCOPED_DETECTION = ...
PROTECTED_STRUCTURAL_FIELDS = ...

RXRX_COMPANY_HEADER_BEFORE = ...
RXRX_COMPANY_HEADER_AFTER = ...
RXRX_COMPANY_HEADER_PRESERVED = ...
RXRX_FALSE_RSI_MATCH = 0

COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
COMPANY_NAME_CHANGED_BY_LEGACY_SUPPRESSION = 0
TICKER_CHANGED_BY_LEGACY_SUPPRESSION = 0
SECTION_HEADING_SUPPRESSED = 0
PROTECTED_FIELD_SUPPRESSED = 0

SUBSTRING_ONLY_TECHNICAL_MATCH = 0
NON_TECHNICAL_PROSE_SUPPRESSED = 0
NON_TECHNICAL_CLAUSE_REMOVED = 0
UNEXPLAINED_SUPPRESSED_FRAGMENT = 0

REAL_TECHNICAL_TOKEN_DETECTION = ...
MU_STALE_LEGACY_TECHNICAL_SUPPRESSION = ...
STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0

SK_HYNIX_FIB_RANGE_RENDER = ...
CURRENT_SR_STORED_RULE_SEPARATION = ...
TSLA_UNSTABLE_FIB_REINTRODUCED = 0
012450_FAMILY_RENDER_REGRESSION = 0

FULL_UNIVERSE_MESSAGE_COUNT = ...
ENTITY_LABEL_LOSS = 0
UNINTENDED_MESSAGE_STRUCTURE_CHANGE = 0
MESSAGE_ELIGIBILITY_REGRESSION = 0
FAIL_COUNT = 0

RAW_SR_VALUE_CHANGED = 0
RAW_FIB_VALUE_CHANGED = 0

BUSINESS_FACT_CHANGED_BY_LEGACY_SUPPRESSION = 0
BUSINESS_THESIS_CHANGED_BY_LEGACY_SUPPRESSION = 0

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0

CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
PRODUCTION_FLAG_CHANGE = 0

PRICE_STRUCTURE_V3_LEGACY_DETECTOR_REPAIR = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

EXACT_MESSAGE_ARTIFACT = ...
ZIP = ...
ZIP_SHA256 = ...
```

---

# 49. Mandatory completion ZIP

Create:

`20260826-price-structure-v3-legacy-technical-detector-false-positive-micro-repair-bundle.zip`

Include:

- exact instruction
- root-cause report
- token-boundary policy
- protected-field audit
- RXRX exact regression
- full-universe audit
- nontechnical-suppression audit
- exact message diff
- message quality
- safety parity
- readiness
- exact candidate-message JSON
- artifact index

Never include:
- secrets
- auth headers
- account identifiers
- hidden chain-of-thought

Compute/report SHA-256.

---

# 50. Severity

## P0

- company/security identity changed in a live message
- wrong price/security/currency
- raw SR/Fib changed
- unstable Fib reintroduced
- business thesis changed by renderer
- shadow/live mutation leak

## P1

- company header/name/ticker suppressed
- ordinary word matched only because it contains `rsi`/`macd`/other acronym characters
- section heading suppressed
- nontechnical prose removed
- stale technical prose suppression disabled globally
- MU stale technical duplication returns
- message structure silently loses a section
- readiness validator still cannot detect structural line loss

## P2

- exact token regex implementation style
- heading whitespace differences
- minor nonsemantic formatting differences

---

# 51. Final principle

The legacy technical suppressor must answer:

```text
"Is this an actual technical statement in a field eligible for suppression?"
```

not:

```text
"Do these characters occur anywhere in the text?"
```

Therefore:

```text
Recursion
≠ RSI

conversion
≠ RSI

company identity
≠ technical prose
```

Detection should be:

```text
semantic field first
→ token boundary second
→ freshness/redundancy third
→ clause-level suppression last
```

Once this passes, proceed directly to bounded selective production enablement.
