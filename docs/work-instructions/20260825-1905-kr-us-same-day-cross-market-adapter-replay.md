# thesis-monitor — 2026-08-25 KR + US Same-Day Cross-Market Adapter Replay
## Immutable Natural Packets + Current Common AI / Market Adapter Code, No Delivery

## Metadata

- Task type: `SAME_DAY_CROSS_MARKET_NON_DELIVERY_REPLAY`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: approximately `19:05 KST`
- Repository: `sskim-ai/thesis-monitor`
- Production mutation: `PROHIBITED`
- Telegram send: `PROHIBITED`
- Open Research production integration: `0`
- Production Research Connector: `NOT_AVAILABLE / BLOCKED_CONNECTOR`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Expected current production main / operating

`c7816ca`

Resolve and record the exact full SHA for current `origin/main` and operating before execution.

### Current architecture state

```text
COMMON_AI_CORE_V1
= integrated canary architecture

Free Analyst + Adaptive Renderer
= production-integrated

Free Analyst full mode
= OFF

Free Analyst bounded canary
= still armed under existing control plane

Structured Market Adapter
= DEPLOYED_PENDING_NATURAL

Open Research production integration
= 0

Open Research live canary
= BLOCKED_CONNECTOR
```

### Required immutable evidence

US natural packet:
`2026-08-25-us-run-37-7e04812311c2`

KR natural packet:
use the exact immutable `2026-08-25` KR afternoon natural packet reviewed in the KR canary/market-data review.

Do not substitute a newly recollected packet for either mandatory replay baseline.

---

# 0. Objective

Do not wait until the next market session merely to validate code correctness.

Use today’s two actual natural production packets:

```text
US morning natural packet
+
KR afternoon natural packet
```

and replay them through the **current latest code**:

```text
immutable packet
→ current valuation/numeric-ref repairs
→ current KR/US structured Market Adapter
→ Free Analyst
→ Synthesis Validator
→ Adaptive Renderer
→ existing hard validators
→ canary selector simulation
→ shadow would-send message
```

The review must answer:

1. Does the current common Market Adapter work safely for both KR and US?
2. Does the repaired KR valuation path now reach Free Analyst/Adaptive?
3. Does the US adapter preserve session/macro semantics and fail closed on unavailable breadth/flow?
4. Does the same common AI reasoning schema work on both markets without a market-specific reasoning fork?
5. Are the replayed messages actually better/useful relative to today’s real sent messages?
6. What remains only a natural delivery proof versus what is already code-correctness PASS?

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-1905-kr-us-same-day-cross-market-adapter-replay.md`

Before execution:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify exact latest safe main/operating SHA
2. verify both immutable packets exist
3. commit/push this instruction as a docs-only instruction commit
4. record instruction path / commit SHA / version
5. create a dedicated replay branch:
   `codex/20260825-kr-us-same-day-adapter-replay`
6. no force push / no history rewrite
7. do not merge replay-only reports into runtime main automatically

---

# 2. Hard prohibitions

Do NOT:

- manually run US production
- manually run KR production
- manually run backup jobs
- send Telegram
- mutate production DB
- mutate receipts
- mutate notificationdelivery
- mutate assessments
- mutate warnings
- mutate investment-logic versions
- mutate Pilot
- change schedules
- change canary limits
- enable Free Analyst full mode
- enable Open Research
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change Macro temporal policy
- alter KRX/night-futures schedules
- patch the immutable packets
- overwrite today’s actual sent-message evidence
- call paid APIs
- invent missing market breadth/flow data

---

# 3. Evidence classes must remain separate

Use three evidence classes.

## A. Immutable natural evidence

The exact packet and actual final message produced naturally today.

```text
US_NATURAL_IMMUTABLE
KR_NATURAL_IMMUTABLE
```

## B. Current-code replay

Same immutable packet, current latest code, no provider recollection.

```text
CURRENT_CODE_REPLAY
```

## C. Optional supplemental same-day collection

Only if a new Market Adapter field cannot be evaluated from stored natural evidence.

```text
SUPPLEMENTAL_SAME_DAY_COLLECTION
```

Never mix C into A.

Every report must clearly label the evidence class.

---

# 4. No provider recollection for mandatory acceptance

The mandatory acceptance replay must first use only immutable stored evidence.

This determines:

- adapter compatibility
- common schema compatibility
- valuation-ref repair
- AI/Adaptive compatibility
- message correctness

Do not recollect providers merely because a field is Unknown.

Unknown is a valid fail-closed outcome.

---

# 5. Optional supplemental collection

Only after the immutable replay is complete, supplemental collection may be performed if:

- the current adapter explicitly requires a structured field
- that field was not captured in the natural packet/archive
- a supported free/official provider exists
- collection can be clearly labeled as later same-day evidence

Record:

```text
supplemental_cutoff_kst
provider
target session/date
fields requested
fields returned
source refs
```

Do not use supplemental values to rewrite today’s natural message history.

Do not call this natural proof.

---

# Part I — Repository / Runtime State

# 6. Current operating state

Record:

```text
main SHA
origin/main SHA
operating SHA
API health
worktree cleanliness

Production Assist governance
Pilot
Free Analyst canary state
Free Analyst full mode
canary limits
Open Research production state
Trade AR state
Inventory mode
Phase 9.0E mode
Structured Market Adapter state
```

Expected:

```text
full mode = OFF
Open Research production = 0
Trade AR user-visible = OFF
```

Do not modify these states during replay.

---

# Part II — US Immutable Replay

# 7. US immutable packet identity

Use exactly:

`2026-08-25-us-run-37-7e04812311c2`

Record:

```text
packet SHA/ref
assessment date
market session
packet created_at
actual sent message bundle ref
receipt ref
```

---

# 8. US Market Adapter input/output

Run the current US structured Market Adapter against the immutable packet and stored structured evidence.

Record normalized output for:

```text
indices:
SPY / S&P context if supplied
QQQ / Nasdaq context if supplied
IWM / Russell context if supplied
SOXX / semiconductor context if supplied

breadth:
advancers
decliners
unchanged
availability

sector:
available sector facts/proxies

session:
premarket
regular
after-hours
as applicable

market flow:
only supported structured fields

macro:
reuse existing canonical temporal facts
```

Hard rules:

```text
missing breadth → Unknown
missing US participant flow → Unknown
no KR-style foreign/institution/retail invention
no duplicate macro temporal facts with conflicting role
```

Set:

`US_MARKET_ADAPTER_REPLAY = PASS / PARTIAL / FAIL`

`PARTIAL` is acceptable if unavailable fields remain Unknown.

---

# 9. US deterministic adapter relations

Audit any adapter-derived relations.

Examples where actually supported:

```text
QQQ vs SPY relative move
SOXX vs broad market relative move
IWM vs large-cap relative move
```

For every relation preserve:

```text
formula
inputs
source refs
session/date
unit
result
```

Hard targets:

```text
hidden arithmetic = 0
unit conflicts = 0
session mismatch = 0
```

---

# 10. US Free Analyst + Adaptive replay

Run all US expected messages through:

```text
current packet
+ normalized US market context
→ Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ existing hard validators
```

Record:

```text
Free Analyst generated
support validation
selected renderer
hard validation
runtime quality
final replay message
fallback reason if any
```

Target:

```text
Fact mismatch = 0
Unsupported numeric = 0
Unsupported causality = 0
Temporal violations = 0
Hidden arithmetic = 0
External unsourced facts = 0
Trade AR leak = 0
Material information loss = 0
```

---

# 11. US actual-vs-replay message comparison

For each US slot compare:

```text
ACTUAL_NATURAL_SENT_MESSAGE
CURRENT_CODE_REPLAY_MESSAGE
DETERMINISTIC_FALLBACK_REFERENCE
```

Classify:

```text
MATERIAL_IMPROVEMENT
NO_MEANINGFUL_CHANGE
WORSE
```

Explain:
- what Market Adapter added
- what Free Analyst changed
- whether the added context was material
- whether Unknowns were preserved

Do not require every message to improve.

---

# 12. US canary simulation

Using the current existing canary selector:

```text
market <= 1
stock <= 2
total <= 3
```

Simulate what would be selected from this immutable US run now.

No delivery.

Record:

```text
eligible messages
selected messages
renderer
selection reasons
runtime quality
```

Hard target:
selected <= 3.

---

# Part III — KR Immutable Replay

# 13. KR immutable packet identity

Use the exact `2026-08-25` KR afternoon natural production packet from the completed review.

Record:

```text
run_id
packet_id
packet SHA/ref
assessment date
packet created_at
actual sent fallback bundle ref
receipt ref
```

Do not use a newly collected KR packet.

---

# 14. Verify KR valuation repair

Replay the exact previously failing SK hynix candidate path.

Required:

```text
previous valuation numeric-ref errors = 2
current errors = 0

s000660_val_pbr or current equivalent
→ resolvable / declared

s000660_val_hist_pb or current equivalent
→ resolvable / declared
```

Confirm:
- current PBR ownership
- historical PBR ownership
- security/denominator basis
- no wildcard ref allowance

Set:

`KR_VALUATION_REPLAY = PASS / FAIL`

---

# 15. KR Market Adapter input/output

Run the current KR structured Market Adapter against the immutable natural evidence.

Record normalized output:

```text
KOSPI
KOSDAQ

breadth:
advancers
decliners
unchanged

sector / size context

market-wide flow:
foreign
institution
retail
other supported categories
unit
market scope
as_of

stock-level flow:
preserve canonical 1D / 5D / 20D semantics

KRX publication/readiness metadata
```

If today’s stored evidence does not contain a field:
Unknown.

Hard rules:

```text
no default zero
no US overnight proxy relabeled as KR local breadth
no stock quantity / market-wide KRW mixed calculation
no invented market-wide participant flow
```

Set:

`KR_MARKET_ADAPTER_REPLAY = PASS / PARTIAL / FAIL`

---

# 16. KR market-context value-add

The prior KR review found domestic structured context insufficient.

Determine whether the current adapter changes that with actual stored evidence.

Set:

```text
KR_MARKET_DIGEST_DOMESTIC_DATA_REPLAY =
SUFFICIENT / PARTIAL / INSUFFICIENT
```

List exact remaining data gaps, such as:

```text
KOSPI/KOSDAQ missing
breadth missing
sector/size missing
market-wide flow missing
index contribution missing
```

Do not convert data gaps into a core-adapter failure if fail-closed behavior is correct.

---

# 17. KR investor-flow regression

For all monitored KR names confirm:

```text
1D / 5D / 20D participant windows preserved
full participant reconciliation = PASS
residual-derived participant claims = 0
unsupported absorber attribution = 0
institution double count = 0
timeless mixed-window statement = 0
```

Set:

`KR_INVESTOR_FLOW_REPLAY = PASS / FAIL`

---

# 18. KR Inventory / Trade AR / FCF regression

Confirm:

```text
Inventory total semantic
directional relation binding
PIT/date
no demand/oversupply overclaim

Trade AR user-visible = 0
Broad AR = 0
AP = 0

FCF period/scope
no hidden causal connection
```

Set:

```text
KR_INVENTORY_REPLAY = PASS / NOT_OBSERVED / FAIL
TRADE_AR_USER_VISIBLE_REPLAY = 0
PHASE_9_0E_KR_REPLAY = PASS / NOT_OBSERVED / FAIL
```

---

# 19. KR Macro temporal regression

For all macro context actually used:

```text
CURRENT stays current
PRIOR_SESSION stays prior-session
REFERENCE stays reference
reference-only today_signal = 0
false-current claims = 0
```

Set:

`KR_MACRO_TEMPORAL_REPLAY = PASS / FAIL`

---

# 20. KR Free Analyst + Adaptive replay

Run all expected KR messages through:

```text
repaired packet
+ normalized KR market context
→ Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ existing hard validators
```

Target:
all message slots reach a safe terminal output.

Record per slot:

```text
Free Analyst generated
support validation
renderer
hard validation
runtime quality
replay output
fallback reason
```

---

# 21. KR actual-vs-replay message comparison

Today’s actual natural delivery was fallback 8/8.

Compare:

```text
ACTUAL_NATURAL_FALLBACK
CURRENT_CODE_FREE_ANALYST_REPLAY
DETERMINISTIC_FALLBACK_REFERENCE
```

For each message classify:

```text
MATERIAL_IMPROVEMENT
NO_MEANINGFUL_CHANGE
WORSE
```

This is especially important because the current code should now pass the valuation prerequisite that blocked the actual canary.

---

# 22. KR canary simulation

Simulate the existing canary selector on the immutable KR packet.

Hard limits:

```text
market <= 1
stock <= 2
total <= 3
```

Record:

```text
eligible count
selected count
selected slots
renderer
selection reason
runtime quality
```

Target:
at least one candidate if the repaired prerequisite now permits it, unless legitimate quality/no-value rules suppress all.

If zero selected:
explain exactly why.

---

# Part IV — Cross-Market Common-Core Proof

# 23. Common normalized schema audit

Compare the normalized KR and US Market Adapter outputs.

Hard target:

```text
same common top-level schema
market-specific availability differences only
no separate KR/US Free Analyst reasoning fork
```

Allowed market-specific differences:
- session vocabulary
- source provider
- investor-flow taxonomy
- breadth availability
- sector/index identifiers

Set:

`KR_US_REASONING_SCHEMA_COMMON = PASS / FAIL`

---

# 24. Common Market Adapter cross-market gate

Set:

```text
COMMON_MARKET_ADAPTER_CROSS_MARKET_REPLAY =
PASS / PARTIAL / FAIL
```

### PASS

Both markets fully populate the fields required by their configured v1 adapter and all validation passes.

### PARTIAL

Common contract/validation pass, but one or both markets have unavailable structured fields that remain Unknown.

### FAIL

Wrong semantic, unit, time, entity, or unsafe defaulting.

A safe PARTIAL is an acceptable architecture result.

---

# 25. Cross-market hard safety

Hard targets across both replays:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0
```

---

# 26. Open Research must remain excluded

Do not use the Open Research shadow sidecar for the mandatory production-path replay.

Set:

```text
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE
```

Optionally include an already-existing research-enhanced shadow message as a separate comparison appendix, but do not blend it with the structured-adapter acceptance gate.

---

# Part V — Optional Supplemental Same-Day Structured Collection

# 27. Supplemental collection decision

After the immutable replay, set:

```text
SUPPLEMENTAL_COLLECTION_REQUIRED =
YES / NO
```

Use YES only if:
- a specific adapter field cannot be tested from archive
- a free/structured provider is already supported
- same-day session data can still be queried without ambiguity

Examples:
- KR KOSPI/KOSDAQ close not archived
- market breadth provider exists but was not captured
- US sector/index context provider supports today’s completed session

Do not use supplemental collection merely to make PARTIAL become PASS.

---

# 28. Supplemental result treatment

If performed:

```text
IMMUTABLE_REPLAY
```

and

```text
SUPPLEMENTAL_CURRENT_STATE
```

must be separate report sections.

Supplemental results may answer:
“Can the adapter ingest this field now?”

They cannot answer:
“Was this field naturally present in today’s production packet?”

---

# Part VI — Decision

# 29. Code-correctness vs natural-proof split

Report separately:

```text
CODE_CORRECTNESS =
PASS / PARTIAL / FAIL

NATURAL_LIVE_PROOF =
PENDING / existing state
```

A replay PASS can close:
- valuation repair compatibility
- adapter semantics
- Free Analyst compatibility
- Adaptive compatibility
- common schema

It cannot close:
- scheduler use of the new adapter
- actual user-visible delivery under the new adapter
- new receipt lifecycle under the new selected message

---

# 30. Expected statuses if replay is clean

A healthy result should look like:

```text
KR_VALUATION_REPLAY = PASS

US_MARKET_ADAPTER_REPLAY =
PASS or safe PARTIAL

KR_MARKET_ADAPTER_REPLAY =
PASS or safe PARTIAL

KR_US_REASONING_SCHEMA_COMMON = PASS

COMMON_MARKET_ADAPTER_CROSS_MARKET_REPLAY =
PASS or PARTIAL

US_FREE_ANALYST_REPLAY = PASS
KR_FREE_ANALYST_REPLAY = PASS

US_ADAPTIVE_REPLAY = PASS
KR_ADAPTIVE_REPLAY = PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Natural statuses remain pending until actual scheduled runs exercise the current code.

---

# 31. NEXT_ACTION policy

If cross-market replay has P0/P1:
`NEXT_ACTION = BOUNDED_REPAIR`

If replay passes/partial safely and KR domestic data remains insufficient:
`NEXT_ACTION = WAIT_FOR_US_STRUCTURED_ADAPTER_NATURAL_CANARY`
with:
`KR_STRUCTURED_DATA_ACQUISITION_BACKLOG`

If replay passes and both adapters are sufficiently populated:
`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_MARKET_ADAPTER_CANARY`

Do not start Open Research production integration in this replay task.

---

# 32. Required reports

Create:

1. `docs/reports/20260825-kr-us-same-day-replay-registration.md`
2. `docs/reports/20260825-us-run37-current-code-adapter-replay.md`
3. `docs/reports/20260825-us-run37-market-adapter-context.md`
4. `docs/reports/20260825-us-run37-message-comparison.md`
5. `docs/reports/20260825-us-run37-canary-simulation.md`
6. `docs/reports/20260825-kr-afternoon-current-code-adapter-replay.md`
7. `docs/reports/20260825-kr-afternoon-valuation-repair-replay.md`
8. `docs/reports/20260825-kr-afternoon-market-adapter-context.md`
9. `docs/reports/20260825-kr-afternoon-message-comparison.md`
10. `docs/reports/20260825-kr-afternoon-canary-simulation.md`
11. `docs/reports/20260825-kr-us-common-schema-audit.md`
12. `docs/reports/20260825-kr-us-market-adapter-cross-market-gates.md`
13. `docs/reports/20260825-kr-us-market-data-gap-inventory.md`
14. `docs/reports/20260825-kr-us-same-day-replay-artifact-index.md`
15. `docs/reports/20260825-kr-us-same-day-replay-summary.json`

If supplemental collection occurs:
16. `docs/reports/20260825-kr-us-supplemental-same-day-collection.md`

---

# 33. Exact message benchmark

Create:

`docs/reports/20260825-kr-us-same-day-message-benchmark.md`

For every message include as applicable:

```text
ACTUAL_NATURAL_MESSAGE
CURRENT_CODE_REPLAY
DETERMINISTIC_FALLBACK
CANARY_ELIGIBLE
CANARY_SELECTED
ADAPTIVE_RENDERER
QUALITY_CLASSIFICATION
```

No Open Research production message.

---

# 34. Data-gap inventory

Create:

`docs/reports/20260825-kr-us-market-data-gap-inventory.md`

Separate:

## KR

```text
index
breadth
sector
size
market-wide flow
index contribution
publication timing
```

## US

```text
breadth
equal-weight
sector breadth
market-wide flow
session context
```

For each:

```text
available?
provider?
structured?
natural packet captured?
adapter supports?
user-visible value-add?
next acquisition action?
```

Do not mark unavailable free data as an engineering failure.

---

# 35. Gate report

Create:

`docs/reports/20260825-kr-us-market-adapter-cross-market-gates.md`

Must include:

```text
REPLAY_STATE =
COMPLETE / FAIL / DEFERRED

CURRENT_MAIN = ...
OPERATING = ...

KR_VALUATION_REPLAY =
PASS / FAIL

US_MARKET_ADAPTER_REPLAY =
PASS / PARTIAL / FAIL

KR_MARKET_ADAPTER_REPLAY =
PASS / PARTIAL / FAIL

KR_MARKET_DIGEST_DOMESTIC_DATA_REPLAY =
SUFFICIENT / PARTIAL / INSUFFICIENT

US_FREE_ANALYST_REPLAY =
PASS / FAIL

KR_FREE_ANALYST_REPLAY =
PASS / FAIL

US_ADAPTIVE_REPLAY =
PASS / FAIL

KR_ADAPTIVE_REPLAY =
PASS / FAIL

US_CANARY_SIMULATED_SELECTED = ...
KR_CANARY_SIMULATED_SELECTED = ...

KR_US_REASONING_SCHEMA_COMMON =
PASS / FAIL

COMMON_MARKET_ADAPTER_CROSS_MARKET_REPLAY =
PASS / PARTIAL / FAIL

FACT_MISMATCH = ...
UNSUPPORTED_NUMERIC = ...
UNSUPPORTED_CAUSALITY = ...
TEMPORAL_VIOLATIONS = ...
TRADE_AR_LEAK = ...
HIDDEN_ARITHMETIC = ...
EXTERNAL_UNSOURCED_FACTS = ...
MATERIAL_INFORMATION_LOSS = ...
MARKET_CONTEXT_UNIT_CONFLICT = ...
MARKET_CONTEXT_DEFAULT_ZERO = ...

SUPPLEMENTAL_COLLECTION_REQUIRED =
YES / NO

OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE

CODE_CORRECTNESS =
PASS / PARTIAL / FAIL

NATURAL_LIVE_PROOF =
PENDING / existing status

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

---

# 36. Machine-readable summary

Create:

`docs/reports/20260825-kr-us-same-day-replay-summary.json`

Recommended structure:

```text
repository
immutable_evidence
us
kr
valuation_repair
market_adapter
free_analyst
adaptive_renderer
canary_simulation
cross_market_schema
safety
supplemental
data_gaps
natural_proof
next_action
```

---

# 37. Mandatory ZIP

Create:

`20260825-kr-us-same-day-cross-market-adapter-replay-bundle.zip`

Include all sanitized reports and exact message benchmarks.

Compute/report SHA-256.

---

# 38. Validation

Run at minimum:

```text
focused replay tests PASS
relevant adapter tests PASS
Free Analyst/Adaptive regression PASS
valuation ref regression PASS
Ruff PASS
git diff --check PASS
```

If this task contains no runtime code changes:
a full pytest rerun is optional if the current main’s full suite and Actions already passed after the adapter deployment, but record the exact existing validation evidence.

If any code change is made during replay:
full pytest + Actions are mandatory before considering the replay result final.

---

# 39. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
REVIEW_BRANCH = ...
REPORT_COMMIT = ...

CURRENT_MAIN = ...
OPERATING = ...

US_PACKET = 2026-08-25-us-run-37-7e04812311c2
KR_PACKET = ...

KR_VALUATION_REPLAY = ...

US_MARKET_ADAPTER_REPLAY = ...
KR_MARKET_ADAPTER_REPLAY = ...

KR_MARKET_DIGEST_DOMESTIC_DATA_REPLAY = ...

US_FREE_ANALYST_REPLAY = ...
KR_FREE_ANALYST_REPLAY = ...

US_ADAPTIVE_REPLAY = ...
KR_ADAPTIVE_REPLAY = ...

US_CANARY_SIMULATED_SELECTED = ...
KR_CANARY_SIMULATED_SELECTED = ...

KR_US_REASONING_SCHEMA_COMMON = ...
COMMON_MARKET_ADAPTER_CROSS_MARKET_REPLAY = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0

SUPPLEMENTAL_COLLECTION_REQUIRED = ...
SUPPLEMENTAL_COLLECTION_PERFORMED = ...

CODE_CORRECTNESS = ...
NATURAL_LIVE_PROOF = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

PRODUCTION_MUTATION = 0
TELEGRAM_SEND = 0
MANUAL_PRODUCTION_TASK = 0
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. Severity

## P0

- wrong Fact / number / period
- wrong market identity
- wrong session semantics
- mixed-unit market context
- fabricated breadth / flow
- hidden arithmetic
- Trade AR leak
- temporal violation
- production mutation
- Telegram send

## P1

- valuation ref repair still blocks KR AI path
- KR/US common schema diverges
- adapter silently defaults unavailable data to zero
- adapter converts US into KR participant-flow semantics
- Free Analyst cannot consume one market
- Adaptive Renderer loses a material boundary
- canary selector exceeds configured limits

## P2

- safe PARTIAL due unavailable breadth
- KR market-wide flow unavailable
- US daily participant flow unsupported
- KRX same-day publication pending
- adapter context adds no material value to a quiet message
- supplemental collection not necessary / not available

---

# 41. Final principle

This replay is intended to compress a full day of waiting into a same-day code-correctness proof.

Use:

```text
today’s actual US natural packet
+
today’s actual KR natural packet
+
current code
```

to verify the cross-market architecture now.

The clean separation is:

```text
Replay
= code correctness / schema / message quality

Next natural run
= scheduler / actual selected-message delivery / receipt proof
```

Do not confuse them, but do not wait for the second when the first can be proven tonight.
