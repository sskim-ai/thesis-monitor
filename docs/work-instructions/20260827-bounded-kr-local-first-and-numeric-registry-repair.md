# thesis-monitor — BOUNDED_KR_LOCAL_FIRST_AND_NUMERIC_REGISTRY_REPAIR
## KR local-first digest consumption + sector breadth numeric registry completeness
## Immutable run-40 replay + next natural KR close reproof
## Price Structure v3 remains NOT ARMED

## 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `BOUNDED_KR_LOCAL_FIRST_AND_NUMERIC_REGISTRY_REPAIR`
- Task class: `BOUNDED_MATERIAL_P1_REPAIR`
- Source policy: preserve current production source policy
- Target historical packet: `2026-08-26-kr-run-40-706bc3003536`
- Latest reported final/main/operating base: `95553b931150f4dd61573888e9fa94198eb43041`
- Prior master instruction: `e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d`
- Prior Track A implementation: `505a3a2c63390c683323192b7ca516513dfe7a24`
- Prior Track B report: `f089ebe1bd2f47612b36a3093ed57f35f39bf67f`
- Current master status: `BOUNDED_REPAIR_REQUIRED`
- Open P0: `0`
- Open material P1: `2`
- Track C / Price Structure selective enablement: `DO_NOT_START`
- Price Structure v3: `INTEGRATED_READY_NOT_ARMED`
- Production Assist: preserve `OFF`

Resolve actual latest clean `origin/main` and operating SHA before implementation. If main has advanced
only through CI/report-only commits, use the latest safe linear descendant and record the lineage.

---

# 1. Source-supported defect statement

The 2026-08-26 natural KR run proved acquisition, persistence, delivery and exactly-once behavior,
but exposed two material P1 defects.

## P1-A — KR local market evidence was present but not consumed by the digest

Active packet evidence included:

```text
KOSPI / KOSDAQ close and return
KOSPI / KOSDAQ breadth
foreign / institution / retail aggregate market flow
KOSPI size context
same-session sector context
KR close FX
```

The sent `__DAILY_DIGEST_KR__` used KR FX but omitted the same-session index/breadth/flow/size/sector
evidence and reused prior US macro/price context as the primary body.

This is downstream evidence-utilization loss, not provider absence.

## P1-B — sector breadth numeric semantic registry was incomplete

Run-40 packet snapshots showed:

```text
numeric entries = 1,961
registered      = 1,583
unsupported     = 378
```

The 378 unsupported paths were sector breadth count paths.

Result:

```text
ready_for_ai = false
```

for all three run-40 packet snapshots.

Deterministic fallback remained safe, but the natural AI path could not become eligible.

---

# 2. Frozen run-40 validation controls

Use the immutable packet as the canonical regression fixture.

Packet:

`2026-08-26-kr-run-40-706bc3003536`

Natural delivery route:

`deterministic_fallback`

Natural delivery:

```text
8/8 delivered
duplicate = 0
orphan = 0
```

The original natural packet/message must not be rewritten.

Replay produces new test/report artifacts only.

---

# 3. Canonical KR market evidence from run-40

These values are frozen replay controls, not values to hard-code into production logic.

## KOSPI breadth

```text
advance   = 585
decline   = 275
unchanged = 47
eligible  = 907
listed    = 944
advance share = 68.0233%
A/D ratio     = 2.1273
net advancers = +310
```

## KOSDAQ breadth

```text
advance   = 907
decline   = 708
unchanged = 111
eligible  = 1,726
listed    = 1,824
advance share = 56.1610%
A/D ratio     = 1.2811
net advancers = +199
```

## KOSPI size context

```text
Large  +0.93%   70 / 28 / 2
Mid    +1.69%  148 / 41 / 6
Small  +0.70%  305 / 162 / 31
```

## Safe same-session sector examples

```text
KOSPI leaders:
Insurance +5.88%
Construction +5.68%
Utilities +5.06%

KOSPI laggards:
Transport/Warehouse -2.66%
Transport Equipment/Parts -1.87%
Metals -1.85%

KOSDAQ leaders:
Metals +2.87%
Entertainment/Culture +2.30%
Construction +2.27%

KOSDAQ laggards:
Telecom -0.93%
Machinery/Equipment -0.89%
Chemicals -0.65%
```

Sector-index return and sector component breadth must remain distinct semantic types.

## Aggregate market flow — canonical owner `ka10051`

Raw unit:

`100M_KRW`

Normalized display control:

```text
KOSPI:
Foreign     +111.5bn KRW
Institution +818.1bn KRW
Retail    -2,503.0bn KRW

KOSDAQ:
Foreign     -129.6bn KRW
Institution -108.7bn KRW
Retail      +233.3bn KRW
```

These are market participation facts, not company fundamentals and not investment-logic state changes.

---

# 4. Reconciliation state — MUST remain fail-closed

The current run-40 reconciliation between `ka10051` aggregate flow and full-pagination `ka10066`
is unresolved for all six market/actor pairs.

Canonical status:

`UNRESOLVED_BASIS_OR_TAXONOMY`

Do not change tolerance.

Do not relabel the source basis.

Do not force reconciliation to PASS.

Therefore:

```text
ka10051 = aggregate-flow owner
ka10066 = not eligible for concentration prose
```

Hard:

```text
UNRECONCILED_CONCENTRATION_PROSE = 0
RECONCILIATION_TOLERANCE_WIDENED = 0
KA10066_PROMOTED_AS_AGGREGATE_OWNER = 0
```

---

# 5. Work split

This work MUST be splittable.

Recommended:

```text
Track A
KR local-first deterministic/shared digest consumption

Track B
KR sector breadth numeric semantic registry completeness

Track C
integration replay of immutable run-40 packet
+ readiness decision
+ next natural KR reproof
```

Tracks A and B may run in parallel if they use separate worktrees and do not edit the same ownership
surface.

Track C starts only after A and B are merged/rebased onto the same latest safe main.

Recommended branches:

```text
codex/kr-local-first-digest-consumption-repair
codex/kr-sector-breadth-numeric-registry-repair
codex/kr-run40-integration-replay
```

---

# 6. Track A — KR local-first digest consumption

The KR afternoon digest must consume same-session Korean local market evidence before prior/global
context.

Required semantic priority:

```text
1. KOSPI / KOSDAQ direction
2. KOSPI / KOSDAQ breadth
3. foreign / institution / retail aggregate flow
4. size/style context
5. material same-session sector context
6. KR close FX
7. prior/global macro context only as secondary context
```

Do not mechanically print every field.

The renderer should select material facts while preserving this ownership order.

---

# 7. Local-first is not "KR-only"

Prior US/global context may remain when useful.

But it must be:

```text
secondary
temporally qualified
non-duplicative
```

It must not replace available same-session KR market structure.

Hard:

```text
KR_LOCAL_EVIDENCE_AVAILABLE_BUT_OMITTED_AS_PRIMARY = 0
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
```

---

# 8. Required KR digest interpretation boundaries

The digest must distinguish:

```text
index direction
breadth
participant flow
sector/size
macro/FX
```

Do not collapse:

```text
KOSDAQ near-flat index
```

into:

```text
weak breadth
```

because run-40 breadth was positive.

Do not convert:

```text
institutional/foreign flow
```

into:

```text
fundamental thesis strengthened/weakened
```

Hard:

`MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0`

---

# 9. Deterministic fallback and AI must share the same KR evidence hierarchy

Do not repair only the natural deterministic fallback while leaving the AI evidence owner different.

Required shared ownership contract:

```text
same-session KR local facts
→ canonical evidence object
→ deterministic renderer
→ AI evidence packet
```

AI may interpret, but must not calculate unsupported numbers.

Hard:

`AI_FALLBACK_KR_EVIDENCE_OWNERSHIP_DIVERGENCE = 0`

---

# 10. Digest materiality

At minimum the run-40 replay must surface enough local evidence to make the message materially
different from the broken natural digest.

Expected semantic content, not exact wording:

```text
KOSPI and KOSDAQ did not move identically
breadth was positive in both
KOSPI institution buying was strong
KOSDAQ foreign/institution flow was negative while retail was positive
mid-cap KOSPI strength and material sector leadership existed
```

No hard-coded prose.

Use packet evidence.

---

# 11. Sector selection policy

Sector output must be bounded.

Do not dump all sector rows.

Use only:

```text
same-session
supported semantic type
non-empty listed universe
material leader/laggard context
```

Keep:

```text
sector index return
sector component breadth
```

separately labeled.

Hard:

`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`

---

# 12. Track B — numeric semantic registry completeness

Audit the exact 378 unsupported run-40 numeric paths.

Produce a machine-readable inventory grouped by:

```text
field-path pattern
market
sector
semantic type
unit
scope
source
count
```

Before registration, classify each path as:

```text
SUPPORTED_CANONICAL
INTERNAL_ONLY
UNSUPPORTED
DUPLICATE_ALIAS
```

Only `SUPPORTED_CANONICAL` paths may become prose/AI registered.

---

# 13. No broad wildcard registration

Do NOT fix:

```text
378 unsupported
```

by blindly allowing:

```text
sector.*
breadth.*
*.count
```

The registry must encode semantic ownership.

Required per registered numeric path:

```text
canonical semantic
unit
market scope
sector scope
session basis
source owner
prose eligibility
comparison eligibility
```

Hard:

```text
WILDCARD_REGISTRY_BYPASS = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
```

---

# 14. Sector breadth count semantic types

Where actually present and supported, register counts as distinct semantics such as:

```text
ADVANCE_COUNT
DECLINE_COUNT
UNCHANGED_COUNT
ELIGIBLE_ISSUE_COUNT
LISTED_ISSUE_COUNT
```

Do not infer names blindly; map to the repository's existing canonical semantic enum/types.

Do not treat counts as:

```text
return_pct
price
flow
```

Hard:

`SECTOR_BREADTH_COUNT_SEMANTIC_MISLABEL = 0`

---

# 15. Derived ratios

If the backend already owns deterministic derivation for:

```text
advance share
decline share
A/D ratio
net advancers
```

preserve that ownership.

Do not let AI derive them.

Do not add new derived numerics unless the existing production contract already supports them.

Hard:

`AI_DERIVED_BREADTH_NUMERIC = 0`

---

# 16. Numeric registry success criterion

For the frozen run-40 packet:

```text
all supported canonical numeric paths must register
unsupported paths must remain fail-closed
```

The target is NOT necessarily:

```text
1,961 / 1,961 prose-eligible
```

The target is:

```text
supported canonical paths = 100% registered
unsupported/internal-only paths = correctly excluded
```

Report both:

```text
TOTAL_NUMERIC_PATHS
SUPPORTED_CANONICAL_PATHS
REGISTERED_SUPPORTED_PATHS
INTERNAL_ONLY_PATHS
UNSUPPORTED_PATHS
DUPLICATE_ALIAS_PATHS
```

Hard:

`SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0`

---

# 17. AI readiness

After Track B repair, replay the exact packet-generation/numeric gate.

Expected if all other pre-existing gates pass:

```text
ready_for_ai = true
```

If another legitimate gate blocks AI:

do not force true.

Report:

```text
NUMERIC_GATE = PASS
FINAL_AI_READY = true/false
OTHER_BLOCKING_GATES = [...]
```

Hard:

`NUMERIC_REGISTRY_FALSE_POSITIVE_AI_READY = 0`

---

# 18. Preserve production fail-closed behavior

Unknown future numeric paths must remain blocked.

Add a negative control with a synthetic unsupported sector numeric path.

Expected:

```text
registry rejects
ready_for_ai affected according to existing policy
no prose exposure
```

---

# 19. Track C — immutable run-40 integration replay

After A+B merge, replay:

`2026-08-26-kr-run-40-706bc3003536`

No mutation.

No manual Telegram.

No manual scheduler execution.

No DB/assessment writes.

Generate:

```text
broken natural digest
Track-A-only candidate
Track-B-only numeric-gate result
A+B integrated candidate
exact diff
evidence utilization map
numeric registry map
AI/fallback candidate parity
```

---

# 20. Replay local-first hard gates

Set:

```text
KR_LOCAL_FIRST_DIGEST = PASS
KOSPI_KOSDAQ_DIRECTION_USED = PASS
KR_BREADTH_USED = PASS
KR_AGGREGATE_FLOW_USED = PASS
KR_SIZE_CONTEXT_USED = PASS/OMITTED_SAFE
KR_SECTOR_CONTEXT_USED = PASS/OMITTED_SAFE
KR_FX_CONTEXT = PASS/OMITTED_SAFE

MATERIAL_KR_LOCAL_EVIDENCE_LOSS = 0
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
```

Size/sector may be safely omitted only if the digest has already reached a bounded materiality/length
limit and the evidence-utilization report explicitly justifies the omission.

Index/breadth/aggregate-flow must not all disappear again.

---

# 21. Replay numeric hard gates

Set:

```text
RUN40_NUMERIC_TOTAL = ...
RUN40_SUPPORTED_CANONICAL = ...
RUN40_REGISTERED_SUPPORTED = ...
RUN40_INTERNAL_ONLY = ...
RUN40_UNSUPPORTED = ...

SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
WILDCARD_REGISTRY_BYPASS = 0

NUMERIC_GATE = PASS
```

Do not hide remaining intentionally unsupported fields.

---

# 22. AI/fallback parity replay

If the repaired packet becomes AI-eligible:

run the bounded existing AI replay/canary path.

Compare against deterministic candidate.

Required parity is semantic/safety parity, not identical prose.

Both must preserve:

```text
KR local-first hierarchy
same source/session ownership
no unsupported numeric
no concentration
no market-flow-as-fundamental
no stale/global context dominance
```

Hard:

```text
AI_FALLBACK_LOCAL_FIRST_PARITY = PASS
AI_FALLBACK_NUMERIC_SAFETY_PARITY = PASS
```

---

# 23. Reconciliation/concentration regression

Replay must confirm:

```text
KOSPI reconciliation = UNRESOLVED_BASIS_OR_TAXONOMY
KOSDAQ reconciliation = UNRESOLVED_BASIS_OR_TAXONOMY
```

unless the input packet itself differs—which it must not for immutable run-40.

Therefore:

```text
KOSPI concentration = BLOCKED_RECONCILIATION
KOSDAQ concentration = BLOCKED_RECONCILIATION
```

Hard:

`UNRECONCILED_CONCENTRATION_PROSE = 0`

---

# 24. KRX/publication boundary

Preserve existing KRX exact-session publication boundary.

If exact-session KRX secondary data was publication-pending in the replay fixture:

keep:

`PUBLICATION_PENDING`

Do not inject stale KRX data to improve the message.

Hard:

`STALE_KRX_INJECTION = 0`

---

# 25. Price Structure isolation

This repair must not touch Price Structure v3.

Hard:

```text
PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_V3_RUNTIME_ARMED = 0
V3_PRICE_STRUCTURE_LEAK_IN_KR_DIGEST = 0
```

Keep:

`PRICE_STRUCTURE_V3 = INTEGRATED_READY_NOT_ARMED`

Track C from the previous master remains:

`DO_NOT_START`

until this repair closes and natural KR reproof passes.

---

# 26. US Track A isolation

Do not reopen US Track A.

Preserve:

`REPLAY_PASS_NATURAL_REPROOF_PENDING`

US natural reproof may continue independently.

Hard:

`US_TRACK_A_CODE_DIFF = 0`

---

# 27. Exactly-once / production safety

Replay:

```text
Telegram send = 0
manual scheduled task = 0
DB mutation = 0
official assessment mutation = 0
```

Historical run-40 evidence must remain:

```text
delivery 8/8
duplicate 0
orphan 0
```

Do not mutate historical deliveries.

---

# 28. Focused tests — Track A

Add tests for:

```text
local KR evidence available + global context available
→ KR local evidence owns primary digest

KOSPI positive / KOSDAQ flat or negative
→ separate index interpretation

positive breadth + flat index
→ breadth remains positive

aggregate flow present
→ safely surfaced

size/sector present
→ optional bounded material use

global context present
→ secondary only

no local evidence
→ existing safe fallback behavior
```

---

# 29. Focused tests — Track B

Add tests for:

```text
supported sector advance count
supported sector decline count
supported unchanged count
supported eligible/listed count

wrong semantic type
unknown future count path
duplicate alias
internal-only numeric
```

Expected:

```text
supported → canonical registry
unsupported → fail-closed
```

---

# 30. Full regression

Required:

```text
focused Track A tests
focused Track B tests
combined KR market-message tests
numeric provenance tests
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
```

Do not change public Action solely for this repair.

---

# 31. Documentation

Create/update architecture docs:

```text
docs/architecture/KR_LOCAL_FIRST_MARKET_DIGEST.md
docs/architecture/KR_SECTOR_BREADTH_NUMERIC_SEMANTICS.md
docs/architecture/NUMERIC_SEMANTIC_REGISTRY.md
```

Document:

```text
evidence ownership
local-first priority
sector return vs breadth separation
numeric registry scope
fail-closed unknown paths
AI/fallback parity
```

---

# 32. Required reports

Create:

1. `docs/reports/20260827-kr-local-first-root-cause.md`
2. `docs/reports/20260827-kr-local-first-evidence-ownership.md`
3. `docs/reports/20260827-kr-run40-before-after-digest.md`
4. `docs/reports/20260827-kr-run40-evidence-utilization.md`
5. `docs/reports/20260827-kr-sector-breadth-registry-root-cause.md`
6. `docs/reports/20260827-kr-sector-breadth-378-path-inventory.md`
7. `docs/reports/20260827-kr-sector-breadth-registry-after.md`
8. `docs/reports/20260827-kr-run40-ai-readiness.md`
9. `docs/reports/20260827-kr-ai-fallback-parity.md`
10. `docs/reports/20260827-kr-reconciliation-concentration-regression.md`
11. `docs/reports/20260827-kr-market-message-safety-parity.md`
12. `docs/reports/20260827-kr-bounded-repair-readiness.md`
13. `docs/reports/20260827-kr-bounded-repair-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-kr-sector-breadth-378-path-inventory.json
docs/reports/20260827-kr-bounded-repair-readiness.json
```

---

# 33. Repair readiness gates

Set exactly:

```text
KR_LOCAL_FIRST_ROOT_CAUSE =
PASS / FAIL

KR_LOCAL_FIRST_EVIDENCE_OWNERSHIP =
PASS / FAIL

KR_LOCAL_FIRST_DIGEST =
PASS / FAIL

KOSPI_KOSDAQ_DIRECTION_USED =
PASS / FAIL

KR_BREADTH_USED =
PASS / FAIL

KR_AGGREGATE_FLOW_USED =
PASS / FAIL

KR_SIZE_CONTEXT_USED =
PASS / OMITTED_SAFE / FAIL

KR_SECTOR_CONTEXT_USED =
PASS / OMITTED_SAFE / FAIL

MATERIAL_KR_LOCAL_EVIDENCE_LOSS =
0 / NONZERO

PRIOR_US_BODY_REUSED_AS_KR_PRIMARY =
0 / NONZERO

MARKET_FLOW_AS_FUNDAMENTAL_CHANGE =
0 / NONZERO

SECTOR_RETURN_AS_SECTOR_BREADTH =
0 / NONZERO

RUN40_NUMERIC_TOTAL =
...

RUN40_SUPPORTED_CANONICAL =
...

RUN40_REGISTERED_SUPPORTED =
...

RUN40_INTERNAL_ONLY =
...

RUN40_UNSUPPORTED =
...

SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP =
0 / NONZERO

UNKNOWN_NUMERIC_SEMANTIC_REGISTERED =
0 / NONZERO

WILDCARD_REGISTRY_BYPASS =
0 / NONZERO

SECTOR_BREADTH_COUNT_SEMANTIC_MISLABEL =
0 / NONZERO

AI_DERIVED_BREADTH_NUMERIC =
0 / NONZERO

NUMERIC_GATE =
PASS / FAIL

FINAL_AI_READY =
true / false

AI_FALLBACK_LOCAL_FIRST_PARITY =
PASS / FAIL / NOT_RUN

AI_FALLBACK_NUMERIC_SAFETY_PARITY =
PASS / FAIL / NOT_RUN

UNRECONCILED_CONCENTRATION_PROSE =
0 / NONZERO

RECONCILIATION_TOLERANCE_WIDENED =
0 / NONZERO

STALE_KRX_INJECTION =
0 / NONZERO

PRICE_STRUCTURE_V3_CODE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_RUNTIME_ARMED =
0 / NONZERO

US_TRACK_A_CODE_DIFF =
0 / NONZERO

TELEGRAM_SEND =
0 / NONZERO

MANUAL_TASK =
0 / NONZERO

DB_MUTATION =
0 / NONZERO

OFFICIAL_ASSESSMENT_MUTATION =
0 / NONZERO

CODE_CORRECTNESS =
PASS / FAIL

KR_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
FAIL
```

---

# 34. Replay PASS state

If all code/replay gates pass:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

KR_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING

TRACK_C =
DO_NOT_START

PRICE_STRUCTURE_V3 =
INTEGRATED_READY_NOT_ARMED
```

Do not reopen Track C yet.

---

# 35. Natural KR reproof

After repaired code is on operating main:

wait for the next naturally scheduled eligible KR afternoon/close run.

Do NOT manually trigger it.

Read-only collect:

```text
run ID
target completed session
packet ID
packet ready time
AI eligibility
route: AI / fallback
delivery IDs
receipt IDs
exact digest
duplicates/orphans
```

---

# 36. Natural reproof gates

The first natural post-repair KR digest must prove:

```text
same-session KR local evidence primary
index/breadth/aggregate flow available and materially used
size/sector used or safely omitted
numeric gate correctly classified
no unsupported numeric prose
no concentration if reconciliation unresolved
no stale KRX injection
exactly once
```

Hard:

```text
NATURAL_KR_LOCAL_FIRST = PASS
NATURAL_KR_MATERIAL_EVIDENCE_LOSS = 0
NATURAL_KR_UNSUPPORTED_NUMERIC = 0
NATURAL_KR_UNRECONCILED_CONCENTRATION = 0
NATURAL_KR_DUPLICATE = 0
NATURAL_KR_ORPHAN = 0
```

---

# 37. Reopening Price Structure Track C

Only after natural KR reproof:

```text
NATURAL_KR_LOCAL_FIRST = PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

may the master gate change to:

```text
TRACK_C = READY_TO_START
```

Price Structure is still not automatically armed by this repair.

Its enablement remains a separate explicit task.

---

# 38. Stop conditions

Stop and return `BOUNDED_REPAIR_REQUIRED` if any of:

```text
same-session local evidence still absent from digest
registry fixes supported paths by unsafe wildcard
unknown paths become prose-eligible
AI computes breadth numerics
concentration prose appears despite unresolved reconciliation
historical run-40 packet/delivery mutated
Price Structure becomes armed
US Track A code changes
new P0
new material P1
```

---

# 39. Severity

## P0

- wrong session data rendered as current
- unsupported numeric appears as authoritative market fact
- duplicate live delivery
- mutation of historical run-40 production evidence
- Price Structure accidentally armed

## P1

- KR local evidence still omitted as primary body
- US/global body still dominates despite complete KR packet
- any supported canonical sector breadth path remains unregistered
- unknown numeric is made eligible by broad wildcard
- AI readiness still blocked solely by numeric registry incompleteness
- sector return mislabeled as breadth
- unreconciled concentration prose emitted
- AI/fallback local-first ownership diverges materially

## P2

- bounded wording differences
- optional size/sector omitted for justified length/materiality
- natural reproof pending after replay PASS
- unrelated provider publication pending

---

# 40. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

INTEGRATION_BRANCH = ...
INTEGRATION_SHA = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RUN40_PACKET =
2026-08-26-kr-run-40-706bc3003536

KR_LOCAL_FIRST_ROOT_CAUSE = ...
KR_LOCAL_FIRST_EVIDENCE_OWNERSHIP = ...
KR_LOCAL_FIRST_DIGEST = ...

KOSPI_KOSDAQ_DIRECTION_USED = ...
KR_BREADTH_USED = ...
KR_AGGREGATE_FLOW_USED = ...
KR_SIZE_CONTEXT_USED = ...
KR_SECTOR_CONTEXT_USED = ...

MATERIAL_KR_LOCAL_EVIDENCE_LOSS = 0
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0

RUN40_NUMERIC_TOTAL = ...
RUN40_SUPPORTED_CANONICAL = ...
RUN40_REGISTERED_SUPPORTED = ...
RUN40_INTERNAL_ONLY = ...
RUN40_UNSUPPORTED = ...

SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
WILDCARD_REGISTRY_BYPASS = 0
SECTOR_BREADTH_COUNT_SEMANTIC_MISLABEL = 0
AI_DERIVED_BREADTH_NUMERIC = 0

NUMERIC_GATE = ...
FINAL_AI_READY = ...
OTHER_BLOCKING_GATES = ...

AI_FALLBACK_LOCAL_FIRST_PARITY = ...
AI_FALLBACK_NUMERIC_SAFETY_PARITY = ...

KOSPI_RECONCILIATION = ...
KOSDAQ_RECONCILIATION = ...
UNRECONCILED_CONCENTRATION_PROSE = 0

PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_V3_RUNTIME_ARMED = 0
US_TRACK_A_CODE_DIFF = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...

TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
FAIL

NATURAL_KR_REPROOF =
PENDING /
PASS /
FAIL

TRACK_C =
DO_NOT_START /
READY_TO_START

PRICE_STRUCTURE_V3 =
INTEGRATED_READY_NOT_ARMED

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_CLOSE /
BOUNDED_REPAIR /
PREPARE_TRACK_C_AFTER_EXPLICIT_INSTRUCTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 41. Mandatory completion bundle

Create:

`20260827-bounded-kr-local-first-and-numeric-registry-repair-bundle.zip`

Include:

```text
exact work instruction
Track A/B/C implementation notes
all required reports
378-path inventory JSON
readiness JSON
exact run-40 before/after digest
test/CI summary
artifact index
```

Exclude:

```text
secrets
auth headers
account identifiers
private tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 42. Final operating principle

The KR afternoon digest must answer:

```text
What happened in Korea in the completed Korean session?
```

before it answers:

```text
What did the prior US/global environment look like?
```

And the numeric registry must answer:

```text
What does this exact number mean, who owns it, and is it safe for prose?
```

not:

```text
Does its path happen to match a broad wildcard?
```

Repair these two ownership failures, prove them on immutable run-40, then wait for one natural KR
close before reopening Price Structure Track C.
