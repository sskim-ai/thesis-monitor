# thesis-monitor — US Night Futures Friday→Saturday Contract Audit + Natural AI Validator Repair
## Integrated bounded repair from the 2026-08-29 US morning natural run
## Fix only what the evidence proves
## Do not reopen already-passing US market data / deterministic delivery

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `US_NIGHT_FUTURES_FRIDAY_SATURDAY_AND_AI_VALIDATOR_REPAIR`
- Task class: `DATA_CONTRACT_AUDIT + AI_OWNERSHIP_REPAIR + FROZEN_NATURAL_REPLAY`
- Production mutation: `0`
- Production Telegram send during repair: `0`
- Scheduler mutation: `0`
- DB / assessment mutation: `0`
- Production Assist: preserve `OFF`
- US Price Structure: preserve current state
- KR Price Structure: preserve current state

Latest source bundle:

`20260829-us-morning-market-data-extraction-and-message-review-bundle.zip`

Source-supported lineage:

```text
Base SHA:
104b0a04d326e66178c9f432798fdeb6cf82a85a

Work-instruction commit:
428836d4a997a10eb7dd1d1935acdea8ea469b54

Evidence implementation:
7fc982ecce30a0af261dcda198ef50280e707531

Final main / origin/main / operating:
3cc91234ef88c655df981b0366a17045c95983f3
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual origin/main
resolve actual operating checkout
confirm 3cc912... or safe linear descendant
```

---

# 1. Source-supported current state

Natural US run:

```text
monitor run ID = 45
packet ID = 2026-08-29-us-run-45-0e9c491532df
route delivered = DETERMINISTIC_PRODUCTION_RENDERER
delivery = 14/14
rejected AI sent = false
market evidence parity = PASS
```

Market data is already closed:

```text
SPY -0.23%
QQQ -0.65%
IWM -1.35%
SOXX -3.20%
RSP -0.34%

strongest:
XLC +1.42%
XLY +1.15%
XLE +0.63%

weakest:
XLK -1.55%
XLU -1.04%
XLI -0.93%
```

Do not redesign or re-litigate those already-passing market facts in this task.

---

# 2. Two remaining work items

## A. Korea night futures Friday→Saturday acquisition/session contract

The canonical gate was safe but never received the expected current row.

Source evidence:

```text
execution = 2026-08-29 08:27 KST
latest completed US session = 2026-08-28
next relevant KR regular session = 2026-08-31
expected night-futures session = 2026-08-29
```

Four production-gate attempts:

```text
08:06 → returned 2026-08-28
08:10 → returned 2026-08-28
08:15 → returned 2026-08-28
08:20 → returned 2026-08-28
```

All four:

```text
STALE_PRIOR_SESSION_PRESENT
ready = false
```

Current user-facing omission was safe.

The unresolved question is upstream/session-contract ownership.

## B. Natural AI full-stock validation P1

Primary AI candidate:

```text
REJECTED
37 errors
```

Backup AI candidate:

```text
REJECTED
4 errors
```

Deterministic delivery was safe and exactly once.

This is the only source-bundle classified material P1.

---

# 3. Hard scope boundaries

Do NOT:

```text
weaken validators
whitelist arbitrary free-form AI numbers
allow rejected AI to send
change deterministic production delivery semantics
change current market index/sector evidence selection
change Price Structure numeric calculation
change KR production scheduler
```

Do:

```text
fix source/semantic ownership
fix prompt/input contracts
fix canonical fact/occurrence mapping where evidence supports it
preserve fail-closed behavior
```

---

# 4. Work split

```text
Track A
Night-futures Friday→Saturday acquisition/session audit

Track B
US natural full-stock AI validator repair

Track C
Run-45 integrated frozen replay
+ dedicated test-sink proof
+ readiness
```

Tracks A and B may run in parallel.

Track C starts only after A/B deterministic tests pass.

Recommended branches:

```text
codex/night-futures-friday-saturday-audit
codex/us-natural-ai-validator-repair
codex/run45-integrated-reproof
```

---

# 5. Track A — exact question to answer

Determine which statement is true:

```text
CASE 1
The authoritative/raw source had a Friday-night/Saturday-morning observation
but thesis-monitor failed to acquire/normalize it.

CASE 2
The source labels that overnight session with 2026-08-28
rather than 2026-08-29.

CASE 3
The source does not publish/provide the expected Friday→Saturday observation
at Saturday-morning query time.

CASE 4
A provider cache/publication delay prevented the current observation.

CASE 5
Another documented source-contract behavior explains the mismatch.
```

Do not assume `2026-08-29` is correct merely because the current resolver expects it.

Do not assume `2026-08-28` is stale merely because its date is earlier.

First establish source-date semantics.

---

# 6. Track A — raw evidence preservation

Capture the raw response before normalization for both:

```text
KOSPI200 night futures
KOSDAQ150 night futures
```

Required raw metadata:

```text
provider/source
request timestamp KST
request parameters
raw date/session field names
raw date/session values
raw level
raw return/change
publication timestamp if exposed
cache age / response-age metadata if exposed
```

Exclude secrets/auth headers from reports.

Hard:

```text
RAW_NIGHT_FUTURES_RESPONSE_CAPTURED = PASS
```

---

# 7. Track A — official/provider contract audit

Trace the documented meaning of fields such as repository-native equivalents of:

```text
BAS_DD
night_bas_dd
session_date
trade_date
end_date
```

Determine whether the date refers to:

```text
session start date
session end date
business/trade date
publication date
underlying regular-session date
```

Use provider documentation / existing official source contract in the repository.

If documentation is insufficient:

mark:

```text
SOURCE_DATE_SEMANTICS = UNKNOWN
```

and do not guess.

---

# 8. Track A — cross-day historical controls

Audit at least three real historical overnight transitions if retained evidence permits:

```text
ordinary weekday → next weekday
Thursday → Friday
Friday → Saturday
```

Use real source observations only.

Compare:

```text
raw source date
canonical normalized date
next KR regular session
query time
```

Goal:

identify whether Friday→Saturday is a special edge case or normal source convention.

Hard:

```text
NIGHT_FUTURES_HISTORICAL_SESSION_MAPPING_AUDIT = PASS
```

or `PARTIAL_SAFE` if source retention is incomplete.

---

# 9. Track A — acquisition vs normalization separation

Explicitly separate:

```text
source has observation?
↓
provider adapter captured it?
↓
normalizer assigned correct canonical session?
↓
canonical gate selected correct session?
↓
renderer visibility?
```

Set one root cause:

```text
UPSTREAM_NOT_PUBLISHED
PROVIDER_ACQUISITION_LOSS
SOURCE_DATE_CONVENTION_MISMATCH
NORMALIZER_SESSION_MAPPING_BUG
CACHE_PUBLICATION_DELAY
UNKNOWN
```

Do not repair the renderer if the defect is upstream.

---

# 10. Track A — acceptable repairs

## If `PROVIDER_ACQUISITION_LOSS`

Repair the smallest adapter/acquisition path.

## If `SOURCE_DATE_CONVENTION_MISMATCH`

Fix normalization so the canonical overnight session reflects the economic session correctly.

Preserve raw source date separately.

## If `NORMALIZER_SESSION_MAPPING_BUG`

Fix resolver/calendar logic generically, including Friday→Saturday tests.

## If `CACHE_PUBLICATION_DELAY`

Use the existing bounded polling/freshness policy.
Do not increase polling indefinitely.

## If `UPSTREAM_NOT_PUBLISHED`

No fake repair.
Document safe omission as source limitation.

Do not use unofficial synthetic substitutes.

---

# 11. Track A — renderer remains fail-closed

Regardless of root cause:

```text
wrong/stale/unresolved night session
→ no user-facing night-futures section
```

Hard:

```text
STALE_NIGHT_FUTURES_VISIBLE = 0
RAW_SUMMARY_NIGHT_FUTURES_BYPASS = 0
```

---

# 12. Track A — positive render proof

If a real current-safe Friday→Saturday observation can be reconstructed/obtained under the corrected contract:

render the exact historical/current message section:

```text
🌙 한국 야간선물
• KOSPI200 야간선물 ...
• KOSDAQ150 야간선물 ...
```

using real source facts.

If no real current-safe observation exists:

do not fabricate one.

Set:

```text
FRIDAY_SATURDAY_NIGHT_FUTURES_POSITIVE_PROOF =
PASS / NOT_OBSERVED / FAIL
```

---

# 13. Track B — primary AI 37-error inventory

Freeze the exact run-45 primary error list.

Required categories:

## 13.1 Unknown monitoring fact IDs

```text
CORZ:
monitoring:risk_reward_transition
interpretation monitoring:risk_reward_transition

WULF:
monitoring:risk_reward_transition
interpretation monitoring:risk_reward_transition
```

Required decision per fact ID:

```text
canonical fact exists but registry/input omitted
or
non-canonical hallucinated/legacy ID
```

If canonical:
repair registry/input ownership.

If non-canonical:
remove from AI input/output contract.

Do not blindly add allowlist entries.

---

# 14. Track B — financial-quality denied valuation fact use

Primary errors include:

```text
CRCL:financial_quality_denied_fact_used:valuation:current
SNDK:financial_quality_denied_fact_used:valuation:current
```

Trace:

```text
why valuation:current was denied
what candidate text attempted to use it
which upstream field exposed it
```

Correct behavior:

```text
denied fact
→ AI must not use it
```

Do not weaken financial-quality gating.

Hard:

```text
FINANCIAL_QUALITY_DENIED_FACT_AI_USE = 0
```

---

# 15. Track B — inventory ownership failures

Primary errors for MU and TSLA:

```text
inventory_relation_not_declared
inventory_business_owner_fact_missing
inventory_primary_numeric_claim_count
inventory_label_missing
inventory_numeric_ownership_count
```

Determine whether inventory facts are:

```text
genuine canonical business facts with missing ownership metadata
or
AI-generated unsupported inventory claims
```

If genuine:

repair structured ownership:

```text
business owner
relation
label
numeric fact refs
units
period
```

If unsupported:

remove inventory claims from AI candidate/input.

Do not let prose invent inventory numerics.

Hard:

```text
UNOWNED_INVENTORY_NUMERIC_VISIBLE = 0
```

---

# 16. Track B — valuation numeric occurrence coverage

Primary errors include uncovered embedded numerics in `valuation_analysis.text`.

Affected evidence includes:

```text
CRCL
- 현재 PBR 6.78배
- 시장 예상 fPER 87.86배

GOOGL
- 현재 PER 12.42배
- 시장 예상 fPER 19.29배

HUT
- 현재 PBR 6.48배
- 시장 예상 fPER 134.61배

IBM
- 현재 PER 14.23배
- 시장 예상 fPER 17.35배

MU
- interpretation occurrence "30"
- 현재 PER 19.07배
- 현재 PBR 10.46배

RXRX
- 현재 PBR 1.95배
- PBR 역사적 백분위 15.6%

SNDK
- 현재 PBR 13.78배
- 시장 예상 fPER 6.5배

TSLA
- 현재 PER 181.64배
- 현재 PBR 15.86배

WULF
- 현재 PBR 52배
- PBR 역사적 백분위 100%
```

Also:

```text
TSM: valuation_interpretation_unknown_occurrence_uncovered
WRD: valuation_interpretation_unknown_occurrence_uncovered
```

Do NOT solve by marking the entire free-form `valuation_analysis.text` as numerically trusted.

Preferred repair:

```text
structured valuation facts
→ fact IDs / fields / units / basis / period
→ renderer/AI references structured values
→ occurrence registry covers selected values
```

Opaque free-form text should not become the authoritative numeric source.

Hard:

```text
FREEFORM_VALUATION_TEXT_AS_NUMERIC_AUTHORITY = 0
```

---

# 17. Track B — attribution / basis safety

Valuation repair must preserve:

```text
currency
security basis
ADR/ordinary share basis
EPS/BVPS denominator basis
period
provider attribution
```

Do not infer missing per-share denominators.

Do not calculate PER/PBR from unsupported raw totals.

Hard:

```text
VALUATION_SECURITY_BASIS_CONFLICT = 0
VALUATION_CURRENCY_CONFLICT = 0
VALUATION_UNVERIFIED_DENOMINATOR_USE = 0
```

---

# 18. Track B — backup AI 4-error inventory

Freeze exact backup errors:

```text
market_review:evidence_utilization:CORE_MARKET_SLOT_UNCONSUMED
market_review:evidence_utilization:SELECTED_RSP_SLOT_UNCONSUMED
market_review:evidence_utilization:SELECTED_SECTOR_DISPERSION_UNCONSUMED
market_review:framework_not_allowed:hyperscaler_capex_transmission
```

These must be repaired without relaxing evidence-utilization or framework allowlist gates.

---

# 19. Track B — backup market-evidence consumption

The backup candidate must consume the same selected shared plan as the production renderer.

Required slots:

```text
CORE_MARKET
PARTICIPATION_STYLE / RSP
SECTOR_DISPERSION
```

If selected:

backup must either:

```text
use them
or
explicitly receive a plan state that they are not selected
```

Do not let backup silently discard selected market evidence.

Hard:

```text
BACKUP_SELECTED_MARKET_EVIDENCE_UNCONSUMED = 0
```

---

# 20. Track B — framework allowlist

The backup used:

```text
hyperscaler_capex_transmission
```

and failed:

```text
framework_not_allowed
```

Determine:

```text
is this a legitimate canonical framework that should be declared?
or
did backup invent/use an unsupported framework name?
```

If canonical:
add through the proper structured framework registry with ownership and tests.

If unsupported:
replace/remove it from prompt/candidate generation.

Do NOT just add the literal string to an allowlist without semantic ownership.

Hard:

```text
UNOWNED_FRAMEWORK_ALLOWLIST_ENTRY_ADDED = 0
```

---

# 21. Track B — validator stays strict

Required negative controls:

```text
unknown fact ID
→ FAIL

financial-quality denied fact
→ FAIL

unowned inventory numeric
→ FAIL

uncovered valuation numeric occurrence
→ FAIL

selected market evidence omitted by backup
→ FAIL

unsupported framework
→ FAIL
```

The goal is:

```text
valid AI candidate
```

not:

```text
weaker validator
```

Hard:

```text
VALIDATOR_RELAXATION = 0
```

---

# 22. Track B — candidate construction hierarchy

Prefer repairs in this order:

```text
1. canonical structured fact ownership
2. prompt/input selection
3. deterministic renderer/AI handoff
4. occurrence registry
5. validator only if validator semantics are proven wrong
```

Do not start by patching validator allowlists.

---

# 23. Track C — frozen run-45 replay

Use:

```text
run 45
packet 2026-08-29-us-run-45-0e9c491532df
```

Read-only.

Reconstruct:

```text
primary AI full-stock candidate
primary validation

backup AI candidate
backup validation

deterministic candidate
```

No production send.

Expected after repair:

```text
PRIMARY_AI_VALIDATION_ERRORS = 0
BACKUP_AI_VALIDATION_ERRORS = 0
```

or, if a path remains intentionally ineligible:

document the exact safe ineligibility and ensure it is not classified as a material P1.

---

# 24. Track C — 13-stock full candidate proof

Use the actual run-45 stock universe.

The source bundle reports 13 stock deliveries.

For each ticker report:

```text
AI candidate validation
valuation fact ownership
inventory ownership where applicable
Price Structure preservation
current quote / structure close
deterministic parity
```

Hard:

```text
US13_AI_FULL_STOCK_VALIDATION = PASS
```

---

# 25. Track C — Price Structure isolation

Do not regress the already-deployed:

```text
near support/resistance
price-anchored major structural S/R
completed Bollinger
provisional Bollinger
current quote vs regular-close structure label
```

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF_FROM_CANONICAL = 0
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
PROVISIONAL_BOLLINGER_AUTHORITY_LEAK = 0
```

---

# 26. Track C — market-message isolation

Run-45 delivered market message evidence parity already passed.

Do not redesign it in this task.

Verify:

```text
SPY/QQQ/IWM/SOXX/RSP unchanged for frozen session
sector selected facts unchanged
RSP semantics unchanged
macro temporal safety unchanged
```

The only potential market-message change allowed is:

```text
night-futures section
```

IF Track A proves the old session contract was wrong and a real current-safe fact should have been visible.

---

# 27. Track C — exact before/after report

Create a before/after table:

```text
component
before state
root cause
repair
after state
validator result
```

At minimum:

```text
night futures
CORZ
CRCL
GOOGL
HUT
IBM
MU
RXRX
SNDK
TSLA
TSM
WRD
WULF
backup market evidence
backup framework
```

---

# 28. Track C — dedicated test sink

After frozen replay PASS:

use the existing dedicated non-production test sink.

Send:

```text
1 US market message
all current monitored US/foreign stock messages
```

Use the repaired candidate path that production would select.

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 29. Test-sink exact payload proof

For every test message:

```text
rendered
outbound
received
```

must match.

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
```

---

# 30. AI route proof

If the repaired AI candidate is valid under current production policy:

prove that the test path actually selects it.

Record:

```text
route
primary validator result
backup validator result
fallback eligibility
```

Do not choose AI merely because it looks better.

Hard:

```text
REJECTED_AI_SENT = 0
```

---

# 31. Night-futures test behavior

If Track A concludes a real current-safe 2026-08-29 economic session existed:

the frozen 2026-08-29 morning market candidate should show the corrected canonical section.

If Track A concludes the upstream source genuinely did not publish a current-safe observation:

the frozen candidate should continue to omit it.

Both may be PASS depending on evidence.

Do not force display.

---

# 32. No production mutation

This task ends at:

```text
repair
frozen replay
test sink
readiness
```

Do not manually rerun production US morning delivery.

The natural 14/14 run already completed safely.

Deployment of a code repair is permitted only after all gates pass through normal operating promotion.

---

# 33. Operating promotion

Promote only if:

```text
Track A contract root cause resolved
Track B AI validation P1 closed
run-45 frozen replay PASS
US13 PASS
test sink PASS
P0 = 0
material P1 = 0
```

If Track A concludes safe omission due upstream limitation:

that is still a resolved contract outcome.

---

# 34. Post-deploy smoke

Read-only verify:

```text
night-futures gate
US market renderer
US 13/current monitored stock AI candidate validation
deterministic fallback
Price Structure
valuation ownership
```

No production Telegram send.

---

# 35. Required reports

Create:

1. `docs/reports/20260829-night-futures-friday-saturday-root-cause.md`
2. `docs/reports/20260829-night-futures-raw-source-contract.md`
3. `docs/reports/20260829-night-futures-historical-session-mapping.md`
4. `docs/reports/20260829-night-futures-repair-or-source-limitation.md`
5. `docs/reports/20260829-run45-primary-ai-validation-root-cause.md`
6. `docs/reports/20260829-run45-primary-ai-error-inventory.md`
7. `docs/reports/20260829-valuation-numeric-ownership-repair.md`
8. `docs/reports/20260829-inventory-fact-ownership-repair.md`
9. `docs/reports/20260829-monitoring-fact-id-ownership-repair.md`
10. `docs/reports/20260829-run45-backup-ai-validation-root-cause.md`
11. `docs/reports/20260829-backup-market-evidence-and-framework-repair.md`
12. `docs/reports/20260829-run45-frozen-replay.md`
13. `docs/reports/20260829-us13-ai-validation.md`
14. `docs/reports/20260829-run45-before-after.md`
15. `docs/reports/20260829-us-ai-test-delivery.md`
16. `docs/reports/20260829-us-ai-exact-test-messages.md`
17. `docs/reports/20260829-us-ai-price-structure-parity.md`
18. `docs/reports/20260829-us-night-ai-integrated-readiness.md`
19. `docs/reports/20260829-us-night-ai-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-night-futures-friday-saturday.json
docs/reports/20260829-run45-ai-validation.json
docs/reports/20260829-us-night-ai-integrated-readiness.json
```

---

# 36. Required gates

Set exactly:

```text
NIGHT_FUTURES_ROOT_CAUSE =
UPSTREAM_NOT_PUBLISHED /
PROVIDER_ACQUISITION_LOSS /
SOURCE_DATE_CONVENTION_MISMATCH /
NORMALIZER_SESSION_MAPPING_BUG /
CACHE_PUBLICATION_DELAY /
OTHER /
UNKNOWN

RAW_NIGHT_FUTURES_RESPONSE_CAPTURED =
PASS / FAIL

SOURCE_DATE_SEMANTICS =
START_DATE /
END_DATE /
BUSINESS_DATE /
PUBLICATION_DATE /
OTHER /
UNKNOWN

NIGHT_FUTURES_HISTORICAL_SESSION_MAPPING_AUDIT =
PASS / PARTIAL_SAFE / FAIL

FRIDAY_SATURDAY_NIGHT_FUTURES_POSITIVE_PROOF =
PASS / NOT_OBSERVED / FAIL

STALE_NIGHT_FUTURES_VISIBLE =
0 / NONZERO

RAW_SUMMARY_NIGHT_FUTURES_BYPASS =
0 / NONZERO

RUN45_PRIMARY_AI_ERROR_COUNT_BEFORE =
37

RUN45_BACKUP_AI_ERROR_COUNT_BEFORE =
4

UNKNOWN_MONITORING_FACT_ID_USE =
0 / NONZERO

FINANCIAL_QUALITY_DENIED_FACT_AI_USE =
0 / NONZERO

UNOWNED_INVENTORY_NUMERIC_VISIBLE =
0 / NONZERO

FREEFORM_VALUATION_TEXT_AS_NUMERIC_AUTHORITY =
0 / NONZERO

VALUATION_SECURITY_BASIS_CONFLICT =
0 / NONZERO

VALUATION_CURRENCY_CONFLICT =
0 / NONZERO

VALUATION_UNVERIFIED_DENOMINATOR_USE =
0 / NONZERO

BACKUP_SELECTED_MARKET_EVIDENCE_UNCONSUMED =
0 / NONZERO

UNOWNED_FRAMEWORK_ALLOWLIST_ENTRY_ADDED =
0 / NONZERO

VALIDATOR_RELAXATION =
0 / NONZERO

RUN45_PRIMARY_AI_ERROR_COUNT_AFTER =
...

RUN45_BACKUP_AI_ERROR_COUNT_AFTER =
...

PRIMARY_AI_VALIDATION =
PASS / REJECTED_SAFE / FAIL

BACKUP_AI_VALIDATION =
PASS / REJECTED_SAFE / FAIL

US13_AI_FULL_STOCK_VALIDATION =
PASS / FAIL

PRICE_STRUCTURE_NUMERIC_DIFF_FROM_CANONICAL =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

PROVISIONAL_BOLLINGER_AUTHORITY_LEAK =
0 / NONZERO

TEST_MESSAGE_COUNT =
...

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

REJECTED_AI_SENT =
0 / NONZERO

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_NIGHT_FUTURES_CONTRACT =
RESOLVED /
SOURCE_LIMITATION_SAFE /
FAIL

US_AI_VALIDATOR_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_TO_DEPLOY /
FAIL

US_20260829_INTEGRATED_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_TO_DEPLOY /
FAIL
```

---

# 37. PASS rule — night futures

PASS if either:

## Repair case

```text
root cause proven
smallest contract/acquisition repair applied
historical mapping tests PASS
current/frozen positive proof PASS where real data exists
no stale visibility
```

or:

## Source limitation case

```text
upstream non-publication/source convention proven
safe omission contract documented
no false "current" claim
no raw-summary bypass
```

Do not mark FAIL merely because the source legitimately cannot provide a Friday→Saturday current row.

---

# 38. PASS rule — AI validator P1

Require:

```text
no unknown monitoring fact ID use
no denied financial-quality fact use
inventory numerics owned or omitted
valuation numerics structured/covered
no security/currency/denominator conflict
backup consumes selected market evidence
backup framework ownership valid
validators unchanged in strictness
US13 candidate validation PASS
rejected AI never sent
```

Preferred target:

```text
RUN45_PRIMARY_AI_ERROR_COUNT_AFTER = 0
RUN45_BACKUP_AI_ERROR_COUNT_AFTER = 0
```

If a candidate remains safely rejected for a genuinely unsupported fact:

the task may only close P1 if the unsupported path is intentionally excluded from production AI eligibility and no repeated validation-failure loop remains.

Document this explicitly.

---

# 39. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RUN45_PACKET =
2026-08-29-us-run-45-0e9c491532df

NIGHT_FUTURES_ROOT_CAUSE = ...
SOURCE_DATE_SEMANTICS = ...
RAW_NIGHT_FUTURES_RESPONSE_CAPTURED = ...
NIGHT_FUTURES_HISTORICAL_SESSION_MAPPING_AUDIT = ...
FRIDAY_SATURDAY_NIGHT_FUTURES_POSITIVE_PROOF = ...

KOSPI200_FRIDAY_SATURDAY_CONTRACT = ...
KOSDAQ150_FRIDAY_SATURDAY_CONTRACT = ...

RUN45_PRIMARY_AI_ERROR_COUNT_BEFORE = 37
RUN45_PRIMARY_AI_ERROR_COUNT_AFTER = ...

RUN45_BACKUP_AI_ERROR_COUNT_BEFORE = 4
RUN45_BACKUP_AI_ERROR_COUNT_AFTER = ...

PRIMARY_AI_VALIDATION = ...
BACKUP_AI_VALIDATION = ...

PRIMARY_ERROR_CLASS_RESULTS =
- monitoring fact IDs: ...
- financial-quality denied facts: ...
- inventory ownership: ...
- valuation occurrences: ...
- valuation unknown occurrences: ...

BACKUP_ERROR_CLASS_RESULTS =
- core market consumption: ...
- RSP consumption: ...
- sector dispersion consumption: ...
- framework ownership: ...

UNKNOWN_MONITORING_FACT_ID_USE = 0
FINANCIAL_QUALITY_DENIED_FACT_AI_USE = 0
UNOWNED_INVENTORY_NUMERIC_VISIBLE = 0
FREEFORM_VALUATION_TEXT_AS_NUMERIC_AUTHORITY = 0

BACKUP_SELECTED_MARKET_EVIDENCE_UNCONSUMED = 0
UNOWNED_FRAMEWORK_ALLOWLIST_ENTRY_ADDED = 0
VALIDATOR_RELAXATION = 0

US13_AI_FULL_STOCK_VALIDATION = ...

PRICE_STRUCTURE_NUMERIC_DIFF_FROM_CANONICAL = 0
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
PROVISIONAL_BOLLINGER_AUTHORITY_LEAK = 0

TEST_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
REJECTED_AI_SENT = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_NIGHT_FUTURES_CONTRACT =
RESOLVED /
SOURCE_LIMITATION_SAFE /
FAIL

US_AI_VALIDATOR_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_TO_DEPLOY /
FAIL

US_20260829_INTEGRATED_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
READY_TO_DEPLOY /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_RUN /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. Mandatory completion ZIP

Create:

`20260829-us-night-futures-friday-saturday-and-ai-validator-repair-bundle.zip`

Include:

```text
exact master instruction
all track instructions
night-futures raw source evidence
night-futures source-date contract
historical mapping audit
night-futures repair/source-limitation conclusion
run-45 primary error inventory
run-45 backup error inventory
valuation ownership evidence
inventory ownership evidence
monitoring fact-ID ownership evidence
backup market-plan/framework evidence
run-45 frozen replay
US13 validation
before/after matrix
test-sink delivery
exact test messages
Price Structure parity
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw Telegram IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 41. Final principle

Two different questions must be answered correctly:

```text
Why did the night-futures source never produce the session we expected?
```

and:

```text
Why did valid production AI candidates fail strict ownership validation?
```

Do not solve either by hiding the evidence or weakening the safety gate.

Fix the contract at the layer that actually owns the defect.
