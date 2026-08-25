# thesis-monitor — 2026-08-25 KR Afternoon Natural Canary + Market Data Review

## Metadata

- Task type: `ONE_SHOT_READ_ONLY_KR_AFTERNOON_NATURAL_REVIEW`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Recommended review start: `17:10 KST`
- Read-only terminal wait hard stop: `17:40 KST`
- Repository: `sskim-ai/thesis-monitor`
- Open Research production integration: `0`
- Production Assist governance: `OFF`
- Existing Pilot: `enabled`, unchanged
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Expected current production main / operating

`b6ed8aaaf115bdae9c62b2c18eef7b8e61fa036f`

Resolve the actual latest safe `origin/main` and operating SHA before the review.

### Current Common AI Core / Canary state

```text
COMMON_AI_CORE_V1 = INTEGRATED_CANARY_PENDING_NATURAL

FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_NATURAL

FREE_ANALYST_ADAPTIVE_FULL = OFF

canary limit:
market digest <= 1
stock messages <= 2
total <= 3

Open Research production integration = 0
Trade AR user-visible = OFF_PENDING_NATURAL_PROOF
Inventory mode = SELECTIVE_INVENTORY
Phase 9.0E = SELECTIVE_CURRENT_FORMAL_FULL_FCF
```

The primary goal today is to capture the **first naturally user-visible KR Free Analyst + Adaptive canary proof** and, in the same read-only review, capture the KR market data needed to understand the quality of that packet.

---

# 0. Objective

This review must answer four questions.

## A. Did KR production complete naturally and safely?

```text
KR production packet
→ final selection
→ Telegram
→ receipt / exactly-once
```

## B. Did the Free Analyst + Adaptive canary actually reach the user safely?

```text
eligible candidates
→ max 3 selected
→ actual delivered canary messages
→ hard validation / runtime quality
```

## C. Was the underlying KR market data complete and correctly interpreted?

Focus on:

```text
price / index
market breadth
investor flow
Inventory / FCF
valuation / RR
macro temporal state
KRX 16:05 publication readiness
```

## D. If KR canary passes, can the system remain armed unchanged for the next US natural canary?

No full-cohort expansion.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-kr-afternoon-natural-canary-and-market-data-review.md`

Before execution:

```bash
git fetch origin
git status
git rev-parse origin/main
```

Then:

1. verify actual main / operating SHA
2. verify canary state is still armed
3. commit/push this instruction as a docs-only instruction commit
4. record instruction commit SHA
5. create a dedicated review branch:
   `codex/20260825-kr-afternoon-natural-canary-review`
6. do not merge review reports into runtime main automatically
7. no force push / history rewrite

---

# 2. Optional one-shot scheduling

If a supported Codex one-shot task can be registered before `17:10 KST`, use:

`20260825-1710-kr-afternoon-natural-canary-review`

If task registration fails or times out:

- do not create a cron workaround
- do not rerun production
- manual read-only execution of this instruction after `17:10 KST` is allowed
- record the tooling issue separately as P2 unless it affects production correctness

---

# 3. Hard prohibitions

Do NOT:

- manually run KR production
- manually run KR backup
- manually send Telegram
- manually recollect provider data to recreate the natural packet
- mutate production DB
- mutate receipts
- mutate notificationdelivery rows
- mutate assessments
- mutate warnings
- mutate investment-logic versions
- mutate Pilot
- change schedules
- enable full Free Analyst mode
- change canary limits
- enable Open Research
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change Macro temporal policy
- change KRX publication schedule
- change price/RR or valuation logic

Only exception:
if an actually delivered canary message has a P0 hard incident, use the already-supported canary kill switch.

---

# 4. Terminal-state rule

At review start inspect:

- KR primary natural run
- KR backup
- immutable packet
- delivery receipt
- KRX 16:05 observation
- canary selector artifact

If all required natural roles are terminal:
proceed.

If not:
- wait read-only
- recheck without triggering anything
- hard stop at `17:40 KST`

If still nonterminal:

```text
REVIEW_STATE = DEFERRED_NONTERMINAL
```

and still produce the ZIP with all available evidence.

---

# Part I — Production and Canary Natural Proof

# 5. Operating-state preflight

Record exact:

```text
main SHA
origin/main SHA
operating SHA
API health
worktree cleanliness

Production Assist governance
Pilot
Free Analyst Adaptive canary state
Free Analyst full mode
canary max total / market / stock
Open Research production state
Inventory mode
Trade AR state
Phase 9.0E mode
```

Expected:

```text
Production Assist governance = OFF
Pilot = unchanged
Canary = ENABLED_PENDING_NATURAL
Full mode = OFF
Open Research = 0
Trade AR = OFF
```

Any unexpected control-plane drift must be classified before reviewing the messages.

---

# 6. Canonical KR natural packet

Identify the exact first eligible KR natural packet after canary activation.

Record:

```text
run_id
packet_id
assessment_date
scheduled_at
actual_start
packet_created_at
terminal_at
primary / backup ownership
expected message count
actual final message count
receipt ref
```

If no eligible natural packet exists today:
set:

`KR_FREE_ANALYST_CANARY_NATURAL = NOT_OBSERVED`

Do not force one.

---

# 7. Exact actual sent bundle

Create:

`docs/reports/20260825-kr-natural-sent-message-bundle.md`

Include exact actual:

- KR market digest
- all stock messages
- sent order
- packet ID
- final delivery mode per slot
- send time
- receipt ref

No destination IDs or secrets.

---

# 8. Per-message final-selection audit

For every expected message slot record:

```text
slot
ticker / market digest
Free Analyst generated?
synthesis validator result
Adaptive Renderer result
selected renderer
canary eligible?
canary selected?
hard validator result
runtime-quality result
fallback reason
final delivery mode
receipt ref
```

Hard invariant:

```text
exactly one final delivery mode per slot
```

---

# 9. Canary count gate

Hard targets:

```text
market digest AI-assisted <= 1
stock AI-assisted <= 2
total AI-assisted <= 3
```

Record:

```text
KR_AI_ASSISTED_DELIVERED
KR_MARKET_AI_ASSISTED
KR_STOCK_AI_ASSISTED
```

If canary exceeds the configured limit:
P1, disable canary after evidence capture.

---

# 10. Exact canary message audit

For every actually delivered canary message record:

```text
exact text
renderer
analysis support refs
Fact / relation refs
hard-validation result
runtime-quality result
delivery timestamp
receipt ref
```

Also render/reference the deterministic fallback for comparison, but do not send it.

---

# 11. Canary hard-safety targets

Across actually delivered canary messages:

```text
Fact mismatch = 0
Unsupported numeric = 0
Unsupported causality = 0
Temporal violation = 0
Trade AR leak = 0
Broad AR leak = 0
AP leak = 0
Hidden arithmetic = 0
External unsourced facts = 0
Material information loss = 0
Directional relation error = 0
```

Any actually delivered violation in these categories is a hard canary incident.

---

# 12. Canary runtime-quality audit

Count in the delivered canary messages:

```text
price particle / grammar errors
repeated price sentences
generic synthesis repetition
duplicate next-check / Unknown
template skeleton recurrence
unnecessary numeric recitation
```

Set:

```text
CANARY_RUNTIME_QUALITY = PASS / FAIL
```

The authoritative runtime-quality gate must have passed for every delivered canary message.

A candidate that failed quality but was not delivered is not a natural canary failure; record it as candidate-level P2/P1 as appropriate.

---

# 13. Human usefulness review

For each delivered canary message compare against its deterministic fallback.

Classify:

```text
MATERIAL_IMPROVEMENT
NO_MEANINGFUL_CHANGE
WORSE
```

Explain briefly:
- what the AI selected as most important
- whether it connected evidence to the investment logic
- whether it preserved uncertainty
- whether Adaptive compression was appropriate

Do not require every canary message to be an improvement.

---

# 14. Production delivery integrity

Hard targets:

```text
actual delivered = expected
duplicates = 0
orphans = 0
packetless intents = 0
receipt integrity = PASS
exactly_once = PASS
```

Set:

`KR_PRODUCTION_NATURAL = LIVE_PASS / FAIL`

---

# Part II — KR Structured Market Data Review

# 15. KRX 16:05 publication / role-target observation

Inspect the exact natural `16:05` KRX observation.

Record:

```text
observation_id
scheduled_at
actual_at
role target
target XKRX trading date
HTTP status
provider dates returned
raw row count
eligible row count
readiness
promotability
raw refs / SHA
terminal state
```

Set:

```text
KRX_1605_ROLE_TARGET_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

KRX_1605_PUBLICATION_READINESS =
<actual supported state>
```

A correct role target may PASS even when the provider is still publication-pending.

Do not manually refetch to manufacture same-day readiness.

---

# 16. KR index data

Capture actual packet/provider values for:

```text
KOSPI close
KOSPI return / basis as actually supplied
KOSDAQ close
KOSDAQ return / basis as actually supplied
```

If an index value is unavailable:
report Unknown.

Do not infer a market-wide regime from the headline index alone.

---

# 17. Market breadth

Capture structured breadth where actually available:

```text
advancers
decliners
unchanged
KOSPI breadth
KOSDAQ breadth
large-cap vs mid/small-cap relative behavior
sector returns
top index contribution concentration
```

Do not create fields from web search in this natural-data review.

If the production/structured provider does not supply breadth:
set:

`KR_MARKET_BREADTH = NOT_OBSERVED`

and list the exact structured-data gap for the future KR adapter.

This is a data-acquisition finding, not automatically a production failure.

---

# 18. Market-wide investor flow

Capture only actual structured data.

If supported:

```text
foreign market-wide net flow
institution market-wide net flow
retail market-wide net flow
other participant categories where supported
basis:
  quantity / value
market scope
as_of_date
```

Do not compare:
- stock-level quantity
to
- market-wide monetary value

unless compatible units exist.

Do not recreate any concentration ratio unless all exact compatible inputs are available.

---

# 19. Stock-level investor-flow audit

For every monitored KR stock capture:

```text
as_of_date

1D:
foreign
institution
retail
other corporation
other foreign
other supported categories

5D:
same categories where available

20D:
same categories where available

foreign holding ratio if available
primary signal
signal basis window
quality / score only where contractually meaningful
```

Hard targets:

```text
full participant reconciliation errors = 0
residual-derived participant claims = 0
unsupported absorber attribution = 0
institution double count = 0
timeless mixed-window attribution = 0
```

---

# 20. Investor-flow message audit

For each actual user-visible stock message verify:

- 1D/5D/20D windows are not blurred together
- `주요 3주체` wording is used only where approved
- additional participant categories do not disappear into invented residual labels
- positioning is not treated as business-thesis change
- flow date is explicit/appropriate if stale

Set:

`KR_INVESTOR_FLOW_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

---

# 21. Concentration / large-cap flow data

Where compatible structured values exist, calculate deterministically:

```text
top-N flow concentration
top-N index contribution concentration
```

Requirements:
- same unit
- same market scope
- same date
- same participant definition

If not compatible:
Unknown.

Do not let AI calculate it.

---

# Part III — Company Financial / Price / Valuation Context

# 22. Inventory user-visible natural proof

For every stock record:

```text
Inventory eligible?
selected / suppressed
suppression reason
context ID
Fact IDs
relation ID
balance date
comparison basis
actual delivered wording
```

Set:

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

LIVE_PASS requires at least one actual delivered Inventory enrichment with:
- total Inventory semantic
- correct PIT / period
- correct directional relation
- no unsupported demand / oversupply claim
- no Inventory Days / CCC
- no hidden FCF inference

If no Inventory selected:
`NOT_OBSERVED`.

---

# 23. Trade AR canary / user-visible guard

Inspect Phase 9.1D exact Trade AR canary.

Record:

```text
exact Trade AR context selected?
relation vs Revenue
PIT/freshness
numeric binding
production influence
```

Hard user-visible targets:

```text
Trade AR enrichment = 0
Broad AR enrichment = 0
AP enrichment = 0
```

Set:

`TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

Do not enable Trade AR.

---

# 24. Phase 9.0E cash-flow regression

For every rendered FCF context record:

```text
ticker
Fact ID
period
scope
currency
current-formal state
baseline consistency
actual wording
```

Hard targets:

```text
period mismatch = 0
scope mismatch = 0
duplicate exact FCF number = 0
working-capital-driven FCF inference = 0
valuation auto-change = 0
```

Set:

`PHASE_9_0E_KR_REGRESSION = PASS / FAIL / NOT_OBSERVED`

---

# 25. FCF / Inventory coexistence

For names where both are available, verify the existing redundancy/priority rule.

Allowed:

```text
FCF shown / Inventory suppressed
Inventory shown / FCF suppressed
one integrated cautious sentence
```

Reject:
- duplicate accounting blocks
- incompatible periods
- contradictory interpretation
- unsupported causal connection

---

# 26. Price / RR data

For every monitored stock capture actual supported:

```text
current price
price_as_of
support zone if available
resistance zone if available
confirmation state
invalidation state
RR if supported
```

Hard targets:

```text
fabricated levels = 0
current-price ownership error = 0
unsupported target/stop = 0
```

Do not generate RSI/MACD unless actually supplied.

---

# 27. Valuation

For each stock record only safely available:

```text
PER
PBR
fPER
fPBR
historical position
basis / period caveat
```

Hard targets:

```text
denominator reverse-engineering = 0
security-basis error = 0
current-vs-history ownership error = 0
working-capital-driven valuation mutation = 0
```

---

# Part IV — Macro / Message Semantics

# 28. Macro temporal natural proof

For every macro item used in the KR market digest or stock messages record:

```text
metric
observation date
retrieval date
temporal role
important_change eligibility
today_signal eligibility
actual wording
```

Hard targets:

```text
false-current claims = 0
legacy missing temporal metadata defaulted current = 0
reference-only data creating today_signal = 0
```

Set:

`MACRO_TEMPORAL_KR_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

---

# 29. KR market digest quality

Review the actual digest for:

- domestic structured data presence
- KOSPI / KOSDAQ distinction
- market breadth if available
- investor flow if available
- no false-current macro claims
- no US/global context overwhelming actual KR evidence
- clear data caution when domestic structured evidence is unavailable

Do NOT implement KR Market Digest localization in this review.

Instead set:

```text
KR_MARKET_DIGEST_DOMESTIC_DATA =
SUFFICIENT / PARTIAL / INSUFFICIENT
```

and list missing structured fields.

This defines the later KR-specific adapter work.

---

# 30. Open Research exclusion

This canary review must remain independent of Open Research.

Hard targets in delivered canary messages:

```text
research evidence refs = 0
Event Attribution refs = 0
fresh web claims = 0
```

Set:

`OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`

---

# Part V — Natural Canary Decision

# 31. KR canary gate

Set:

`KR_FREE_ANALYST_CANARY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

LIVE_PASS requires:

```text
at least 1 actual canary message delivered
AI-assisted total <= 3
hard safety errors = 0
runtime-quality delivered errors = 0
delivery integrity PASS
exactly_once PASS
fallback reachable
Open Research leakage = 0
```

If eligible canary candidates exist but none were delivered unexpectedly:
P1 unless explained by supported control-plane behavior.

---

# 32. Hard-incident kill switch

If an actually delivered canary has:

- wrong fact/number/period
- wrong directional relation
- unsupported causality
- temporal violation
- Trade AR leak
- hidden external fact
- duplicate/exactly-once failure

then immediately:

```text
FREE_ANALYST_ADAPTIVE_CANARY = DISABLED
```

Record:
- before/after control-plane state
- incident slot
- exact reason

Normal deterministic production remains enabled.

---

# 33. State after KR PASS

If KR natural canary = LIVE_PASS:

```text
COMMON_AI_CORE_V1 =
CANARY_KR_LIVE_PASS_PENDING_US

FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_US_NATURAL

FREE_ANALYST_ADAPTIVE_FULL =
OFF
```

Keep limits unchanged.

Do not expand cohort.

Next proof:
next eligible US natural canary.

---

# 34. State if no KR canary observed

If the packet is valid but selector had no eligible canary messages:

```text
KR_FREE_ANALYST_CANARY_NATURAL = NOT_OBSERVED
```

Do not call failure unless there was an eligibility/control-plane defect.

Document why no message qualified.

---

# 35. Required reports

Create:

1. `docs/reports/20260825-kr-afternoon-operating-state.md`
2. `docs/reports/20260825-kr-natural-production-review.md`
3. `docs/reports/20260825-kr-natural-sent-message-bundle.md`
4. `docs/reports/20260825-kr-free-analyst-canary-selection-audit.md`
5. `docs/reports/20260825-kr-free-analyst-canary-natural-proof.md`
6. `docs/reports/20260825-kr-free-analyst-canary-message-comparison.md`
7. `docs/reports/20260825-kr-canary-delivery-integrity.md`
8. `docs/reports/20260825-krx-1605-publication-review.md`
9. `docs/reports/20260825-kr-market-breadth-data-review.md`
10. `docs/reports/20260825-kr-investor-flow-natural-review.md`
11. `docs/reports/20260825-kr-inventory-fcf-natural-review.md`
12. `docs/reports/20260825-kr-price-valuation-natural-review.md`
13. `docs/reports/20260825-kr-macro-temporal-natural-review.md`
14. `docs/reports/20260825-kr-market-digest-domestic-data-review.md`
15. `docs/reports/20260825-kr-afternoon-canary-gates.md`
16. `docs/reports/20260825-kr-afternoon-canary-artifact-index.md`
17. `docs/reports/20260825-kr-afternoon-canary-summary.json`

---

# 36. Exact market-data table

Create:

`docs/reports/20260825-kr-afternoon-market-data-table.md`

Include actual available structured values for:

```text
Index:
KOSPI
KOSDAQ

Breadth:
advancers
decliners
unchanged
sector / size breadth where available

Market flow:
foreign
institution
retail
other supported categories

Per monitored ticker:
close/current price
1D / 5D / 20D participant flows
foreign holding ratio
Inventory relation if selected
FCF if selected
PER / PBR / fPER / fPBR where safe
RR / support / resistance where supplied
canary selected?
renderer
final delivery mode
```

Use `Unknown / Not observed` instead of fabricated values.

---

# 37. Gate report

Create:

`docs/reports/20260825-kr-afternoon-canary-gates.md`

Must include:

```text
REVIEW_STATE =
COMPLETE / DEFERRED_NONTERMINAL

KR_PRODUCTION_NATURAL =
LIVE_PASS / FAIL

KR_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

KR_AI_ASSISTED_DELIVERED = ...
KR_MARKET_AI_ASSISTED = ...
KR_STOCK_AI_ASSISTED = ...

CANARY_RUNTIME_QUALITY =
PASS / FAIL / NOT_OBSERVED

DUPLICATES = ...
ORPHANS = ...
EXACTLY_ONCE = ...
RECEIPT_INTEGRITY = ...

FACT_MISMATCH = ...
UNSUPPORTED_NUMERIC = ...
UNSUPPORTED_CAUSALITY = ...
TEMPORAL_VIOLATIONS = ...
TRADE_AR_LEAK = ...
HIDDEN_ARITHMETIC = ...
EXTERNAL_UNSOURCED_FACTS = ...
MATERIAL_INFORMATION_LOSS = ...

KRX_1605_ROLE_TARGET_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

KRX_1605_PUBLICATION_READINESS = ...

KR_MARKET_BREADTH =
PASS / PARTIAL / NOT_OBSERVED / FAIL

KR_INVESTOR_FLOW_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

INVENTORY_USER_VISIBLE_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

TRADE_AR_NATURAL_PROOF =
LIVE_PASS / FAIL / NOT_OBSERVED

PHASE_9_0E_KR_REGRESSION =
PASS / FAIL / NOT_OBSERVED

MACRO_TEMPORAL_KR_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

KR_MARKET_DIGEST_DOMESTIC_DATA =
SUFFICIENT / PARTIAL / INSUFFICIENT

OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

COMMON_AI_CORE_V1 =
CANARY_KR_LIVE_PASS_PENDING_US /
INTEGRATED_CANARY_PENDING_NATURAL /
INTEGRATION_FAIL

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

---

# 38. NEXT_ACTION policy

### KR canary LIVE_PASS

```text
NEXT_ACTION =
WAIT_FOR_US_FREE_ANALYST_NATURAL_CANARY
```

### KR canary FAIL

```text
NEXT_ACTION =
FREE_ANALYST_CANARY_BOUNDED_REPAIR
```

and disable canary on hard incident.

### KR canary NOT_OBSERVED

```text
NEXT_ACTION =
WAIT_FOR_NEXT_ELIGIBLE_KR_NATURAL_CANARY
```

unless the reason is a control-plane defect.

### Domestic market-data gaps are material but canary passes

Keep natural canary PASS and add:

```text
P2/P1 data-adapter backlog:
KR_MARKET_STRUCTURED_ADAPTER
```

Do not mix that implementation into this review.

---

# 39. Result ZIP

Create:

`20260825-kr-afternoon-natural-canary-and-market-data-review-bundle.zip`

Include all sanitized reports.

Compute/report SHA-256.

---

# 40. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
REVIEW_BRANCH = ...
REPORT_COMMIT = ...

REVIEW_STATE = ...

MAIN = ...
OPERATING = ...
CANARY_STATE = ...
FULL_MODE = OFF

KR_PRODUCTION_NATURAL = ...
KR_FREE_ANALYST_CANARY_NATURAL = ...

KR_AI_ASSISTED_DELIVERED = ...
KR_MARKET_AI_ASSISTED = ...
KR_STOCK_AI_ASSISTED = ...

CANARY_RUNTIME_QUALITY = ...

DUPLICATES = ...
ORPHANS = ...
EXACTLY_ONCE = ...
RECEIPT_INTEGRITY = ...

FACT_MISMATCH = ...
UNSUPPORTED_NUMERIC = ...
UNSUPPORTED_CAUSALITY = ...
TEMPORAL_VIOLATIONS = ...
TRADE_AR_LEAK = ...
HIDDEN_ARITHMETIC = ...
EXTERNAL_UNSOURCED_FACTS = ...
MATERIAL_INFORMATION_LOSS = ...

KRX_1605_ROLE_TARGET_NATURAL = ...
KRX_1605_PUBLICATION_READINESS = ...

KR_MARKET_BREADTH = ...
KR_INVESTOR_FLOW_NATURAL = ...
INVENTORY_USER_VISIBLE_NATURAL = ...
TRADE_AR_NATURAL_PROOF = ...
PHASE_9_0E_KR_REGRESSION = ...
MACRO_TEMPORAL_KR_NATURAL = ...
KR_MARKET_DIGEST_DOMESTIC_DATA = ...

COMMON_AI_CORE_V1 = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

PRODUCTION_MUTATION_FROM_REVIEW = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_PRODUCTION_TASK = 0
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 41. Severity

## P0

- wrong delivered fact / number / period
- wrong directional relation
- unsupported causal claim delivered
- temporal violation delivered
- Trade AR / broad AR / AP leak
- hidden external fact
- hidden arithmetic
- duplicate Telegram
- receipt / exactly-once failure
- full mode accidentally enabled
- Open Research accidentally activated
- production mutation from review

## P1

- canary exceeds max cohort
- runtime-quality rejected message delivered
- per-message fallback breaks packet completion
- non-selected slots fail to deliver
- investor-flow attribution regression
- common KR packet adapter regression
- canary kill switch unavailable

## P2

- no canary candidate selected naturally
- some AI messages show no material improvement
- KRX same-day provider publication still pending
- market breadth not available from structured provider
- KR digest domestic-data insufficiency
- harmless generic synthesis candidate rejected before delivery
- one-shot review automation tooling issue

---

# 42. Final principle

Today’s KR review is both:

```text
the first user-visible Common AI Core canary proof
```

and:

```text
a structured KR market-data inventory
```

Do not mix in Open Research.

The review should tell us:

1. Did Free Analyst + Adaptive actually reach the KR user safely?
2. Which exact messages were selected and why?
3. Did exactly-once remain intact for the whole packet?
4. Are KR investor-flow semantics still correct?
5. Did Inventory / FCF / valuation / RR remain safe?
6. Was the KRX 16:05 target correct and was publication ready?
7. Do we have enough domestic breadth / market-wide flow data for a strong KR market digest?
8. If not, which market-specific structured adapter fields are missing?
9. Can we keep the same canary armed unchanged for the next US natural run?

If KR canary passes, do not expand it.
Keep the same bounded configuration and move to the US natural proof.
