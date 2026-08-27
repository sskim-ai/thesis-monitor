# thesis-monitor — KR Afternoon Natural Market Data Review + Reproof
## Target: 2026-08-27 completed Korean session
## Read-only natural production proof after KR local-first / numeric-registry repair

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_AFTERNOON_NATURAL_MARKET_DATA_REVIEW_AND_REPROOF`
- Task class: `READ_ONLY_NATURAL_PRODUCTION_REPROOF`
- Target market: `KR`
- Target completed regular session: `2026-08-27`
- Latest reported final/main/operating entering this review:
  `a1fb1a7006109f8699e03997662bde27db5ad464`
- Current KR repair state:
  `REPLAY_PASS_NATURAL_REPROOF_PENDING`
- Current US repair state:
  `REPLAY_PASS_NATURAL_REPROOF_PENDING`
- Price Structure v3:
  `INTEGRATED_READY_NOT_ARMED`
- Price Structure Track C:
  `DO_NOT_START`
- Production Assist:
  preserve `OFF`
- Manual Telegram send:
  `0`
- Manual scheduled task:
  `0`
- DB mutation:
  `0`
- Official assessment mutation:
  `0`

Resolve actual latest clean `origin/main` and operating SHA first.
If main has advanced through safe report/US-repair commits, record the exact lineage.

This task must not change runtime behavior.

---

# 1. Purpose

This task answers:

```text
Did today's 2026-08-27 Korean close natural message:
1. use the correct completed KR session,
2. collect the full Kiwoom local-market dataset,
3. render KR local-first evidence correctly after the repair,
4. pass the numeric semantic registry / AI eligibility gate,
5. preserve flow reconciliation fail-closed rules,
6. deliver exactly once,
7. avoid Price Structure v3 leakage?
```

This is a read-only proof task.

If a material defect is found:

```text
REPORT
CLASSIFY
STOP
```

Do not repair it in this task.

---

# 2. Natural-run requirement

Find the naturally scheduled KR afternoon/close run that should summarize:

`2026-08-27`

Do NOT manually trigger it.

Collect:

```text
scheduled task identity
configured schedule
natural start KST
natural completion KST
run ID
producer SHA
operating SHA
target session
packet ID
packet created_at
packet ready_at
AI eligibility
route = AI / deterministic_fallback
delivery IDs
receipt IDs
```

If the natural run did not occur:

```text
KR_AFTERNOON_NATURAL = NOT_OBSERVED
```

and STOP.

No synthetic live proof.

---

# 3. Correct target-session gate

Natural packet must represent:

```text
market = KR
target completed session = 2026-08-27
```

Reject:

```text
2026-08-26 prior packet
incomplete 2026-08-27 intraday packet
wrong-session stale data
```

Hard:

```text
KR_TARGET_SESSION = 2026-08-27
KR_COMPLETED_SESSION = PASS
WRONG_TARGET_SESSION_PACKET = 0
```

---

# 4. Exactly-once / packet integrity

Collect:

```text
packet count
intent count
delivery count
receipt count
attempt_count
duplicate count
orphan count
unowned retry count
last error
```

Hard:

```text
KR_PACKET_INTEGRITY = PASS
KR_EXACTLY_ONCE = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```

---

# 5. Exact natural message

Return the exact persisted natural KR digest.

Compare:

```text
persisted payload
delivery payload
receipt-linked payload
```

Hard:

```text
KR_EXACT_MESSAGE_PAYLOAD_MATCH = PASS
```

Do not paraphrase in the evidence report; include exact payload separately.

---

# 6. ka20001 — canonical KOSPI / KOSDAQ index + breadth

For both KOSPI and KOSDAQ collect exact same-session:

```text
close
change
return_pct

advance
decline
unchanged

eligible issue count if available
listed issue count if available
```

Backend-owned deterministic derived metrics may include:

```text
advance share
decline share
A/D ratio
net advancers
```

AI must not calculate these.

Canonical breadth source:

`Kiwoom ka20001`

External/web values are cross-check only.

Hard:

```text
KIWOOM_KA20001 = PASS
KOSPI_BREADTH = PASS
KOSDAQ_BREADTH = PASS
KR_BREADTH_SEMANTICS = PASS
AI_DERIVED_BREADTH_NUMERIC = 0
```

---

# 7. Breadth interpretation

The message must distinguish:

```text
index return
vs
breadth
```

Do not infer one from the other.

Hard:

```text
INDEX_RETURN_AS_BREADTH = 0
BREADTH_AS_INDEX_RETURN = 0
```

---

# 8. ka20003 — size/style / sector structure

Collect same-session structured fields supported by the current integration.

At minimum:

```text
KOSPI large-cap
KOSPI mid-cap
KOSPI small-cap
```

and safe supported:

```text
KOSDAQ size/style
sector index / sector leader-laggard
```

For each:

```text
name
return_pct if backend-owned
advance
decline
unchanged if provided
state
source
```

Hard:

```text
KIWOOM_KA20003 = PASS / PARTIAL_SAFE
KR_SIZE_STYLE_CONTEXT = PASS / PARTIAL_SAFE
```

Do not call sector-index return the same thing as sector component breadth.

Hard:

`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`

---

# 9. Sector breadth numeric registry — natural reproof

For today's natural packet, collect:

```text
TOTAL_NUMERIC_PATHS
SUPPORTED_CANONICAL_PATHS
REGISTERED_SUPPORTED_PATHS
INTERNAL_ONLY_PATHS
UNSUPPORTED_PATHS
DUPLICATE_ALIAS_PATHS
```

Expected safety:

```text
SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
WILDCARD_REGISTRY_BYPASS = 0
```

Do not require all internal-only paths to be prose eligible.

Hard:

```text
NUMERIC_GATE = PASS
```

If AI is still ineligible, identify the actual separate blocking gate.

---

# 10. AI readiness / route

Record:

```text
ready_for_ai
numeric gate
all other eligibility gates
route = AI / deterministic_fallback
AI selected evidence refs if used
```

Fallback is not automatically a failure.

Hard:

```text
UNEXPLAINED_AI_INELIGIBILITY = 0
```

---

# 11. ka10051 — aggregate market participant flow

For KOSPI and KOSDAQ collect:

```text
foreign
institution
retail
```

Canonical raw scale:

`100M_KRW`

Normalize only through backend-owned deterministic conversion.

Recommended display unit:

`bn KRW`

Record both raw and normalized.

Hard:

```text
KIWOOM_KA10051 = PASS
KA10051_AGGREGATE_FLOW_OWNER = PASS
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0
```

---

# 12. ka10066 — full stock-level participant flow pagination

For each market:

```text
KOSPI
KOSDAQ
```

collect:

```text
page count
row count
duplicate row count
pagination complete
source session
```

Canonical raw scale:

`1M_KRW`

Hard:

```text
KOSPI_KA10066_PAGINATION = PASS
KOSDAQ_KA10066_PAGINATION = PASS
KA10066_DUPLICATE_ROWS = 0
```

---

# 13. ka10051 ↔ ka10066 reconciliation

For each market and participant compare:

```text
ka10051 aggregate flow
vs
sum of fully paginated ka10066
```

Use the existing canonical tolerance.

Do not widen tolerance.

Report:

```text
aggregate
summed stock-level
absolute difference
relative difference
status
```

Expected status may remain:

`UNRESOLVED_BASIS_OR_TAXONOMY`

if today's data does not reconcile.

Do NOT inherit yesterday's status automatically.
Recompute today.

Hard:

```text
RECONCILIATION_TOLERANCE_WIDENED = 0
KA10066_PROMOTED_AS_AGGREGATE_OWNER = 0
```

---

# 14. Concentration gate

Only if reconciliation passes for a market/participant pair may concentration be computed/shown.

If reconciliation does not pass:

```text
BLOCKED_RECONCILIATION
```

No concentration prose.

Hard:

```text
UNRECONCILED_CONCENTRATION_PROSE = 0
AI_DERIVED_CONCENTRATION = 0
```

---

# 15. KRX secondary cross-provider

Check whether exact-session 2026-08-27 KRX/public official secondary data is available.

If yes:
compare only safely comparable fields.

If not:

```text
KRX_CROSS_PROVIDER = PUBLICATION_PENDING
```

Do not inject stale KRX data.

Hard:

```text
STALE_KRX_INJECTION = 0
CROSS_PROVIDER_CONFLICT_SILENTLY_RESOLVED = 0
```

---

# 16. KR local-first digest — natural reproof

The repaired KR digest should use same-session Korean local evidence before prior/global context.

Canonical evidence hierarchy:

```text
1. KOSPI / KOSDAQ direction
2. KOSPI / KOSDAQ breadth
3. foreign / institution / retail aggregate flow
4. size/style context
5. material same-session sector context
6. KR FX
7. prior/global macro as secondary
```

The exact message does not need every field.

But it must not again reduce Korea to FX while prior US/global context dominates.

Hard:

```text
KR_LOCAL_FIRST_DIGEST = PASS
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
MATERIAL_KR_LOCAL_EVIDENCE_LOSS = 0
```

---

# 17. Minimum local evidence consumption

The final KR digest must materially consume:

```text
KOSPI/KOSDAQ direction
breadth
aggregate participant flow
```

Size/sector may be omitted safely if length/materiality budget justifies it.

Hard:

```text
KOSPI_KOSDAQ_DIRECTION_USED = PASS
KR_BREADTH_USED = PASS
KR_AGGREGATE_FLOW_USED = PASS
KR_SIZE_CONTEXT_USED = PASS / OMITTED_SAFE
KR_SECTOR_CONTEXT_USED = PASS / OMITTED_SAFE
```

---

# 18. Same-session sector usage

If material same-session sector leaders/laggards exist:
the digest may select a bounded subset.

Do not dump every sector.

Classify material sector facts:

```text
MESSAGE_USED
MESSAGE_OMITTED_SAFE
MESSAGE_OMITTED_MATERIAL_LOSS
```

Hard:

`KR_SECTOR_MATERIAL_INFORMATION_LOSS = 0`

---

# 19. AI/fallback local-first parity

Create a read-only deterministic fallback candidate using the exact same packet.

If natural route = AI:
compare AI vs fallback.

If natural route = fallback:
create the safe AI replay candidate if allowed by existing bounded replay tooling.

Both must preserve:

```text
KR local-first hierarchy
numeric provenance
reconciliation/concentration boundary
temporal/source ownership
```

Exact prose need not match.

Hard:

```text
AI_FALLBACK_LOCAL_FIRST_PARITY = PASS
AI_FALLBACK_NUMERIC_SAFETY_PARITY = PASS
```

---

# 20. KR FX and global context

Collect:

```text
USD/KRW
observation date
session basis
temporal role
```

Hard:

```text
KR_FX_ONLY_DIGEST_WITH_LOCAL_MARKET_AVAILABLE = 0
FX_SESSION_BASIS_CONFLICT = 0
GLOBAL_CONTEXT_DOMINATES_KR_LOCAL = 0
STALE_GLOBAL_CONTEXT_AS_CURRENT_KR = 0
```

Prior US/global context may remain secondary only.

---

# 21. Exact message evidence-utilization matrix

Create a row for every material input family:

```text
KOSPI direction
KOSDAQ direction
KOSPI breadth
KOSDAQ breadth
KOSPI foreign flow
KOSPI institution flow
KOSPI retail flow
KOSDAQ foreign flow
KOSDAQ institution flow
KOSDAQ retail flow
size/style
sector
KR FX
global macro
```

Classify:

```text
MESSAGE_USED
MESSAGE_OMITTED_SAFE
MESSAGE_OMITTED_MATERIAL_LOSS
```

Hard:

```text
KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
```

---

# 22. Price Structure v3 leak check

Price Structure v3 remains:

`INTEGRATED_READY_NOT_ARMED`

Therefore today's KR afternoon message must not expose the new current SR/Fib renderer.

Hard:

```text
V3_PRICE_STRUCTURE_LEAK = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
```

---

# 23. Business investment-logic isolation

Market flow / breadth / sector movement alone must not change stored business investment logic.

Hard:

```text
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
BUSINESS_THESIS_MUTATION_FROM_REVIEW = 0
```

---

# 24. Public/secondary cross-check

Use production Kiwoom data as canonical.

Use official/public web only as secondary cross-check.

If external breadth differs from ka20001:
record discrepancy but do not overwrite ka20001.

Hard:

`CANONICAL_KIWOOM_OVERWRITTEN_BY_WEB = 0`

---

# 25. Data completeness matrix

Create machine-readable matrix with:

```text
fact family
source
target session
actual observation date
raw value
normalized value
semantic type
state
packet present
AI evidence present
fallback evidence present
message used
cross-check status
```

This is the core data-extraction deliverable.

---

# 26. Required reports

Create:

1. `docs/reports/20260827-kr-afternoon-natural-run-identity.md`
2. `docs/reports/20260827-kr-afternoon-exactly-once.md`
3. `docs/reports/20260827-kr-afternoon-ka20001-index-breadth.md`
4. `docs/reports/20260827-kr-afternoon-ka20003-size-sector.md`
5. `docs/reports/20260827-kr-afternoon-ka10051-aggregate-flow.md`
6. `docs/reports/20260827-kr-afternoon-ka10066-pagination.md`
7. `docs/reports/20260827-kr-afternoon-flow-reconciliation.md`
8. `docs/reports/20260827-kr-afternoon-concentration-eligibility.md`
9. `docs/reports/20260827-kr-afternoon-sector-numeric-registry.md`
10. `docs/reports/20260827-kr-afternoon-ai-readiness.md`
11. `docs/reports/20260827-kr-afternoon-krx-cross-provider.md`
12. `docs/reports/20260827-kr-afternoon-local-first-reproof.md`
13. `docs/reports/20260827-kr-afternoon-ai-fallback-parity.md`
14. `docs/reports/20260827-kr-afternoon-exact-message.md`
15. `docs/reports/20260827-kr-afternoon-evidence-utilization.md`
16. `docs/reports/20260827-kr-afternoon-message-quality.md`
17. `docs/reports/20260827-kr-afternoon-safety-parity.md`
18. `docs/reports/20260827-kr-afternoon-natural-reproof-readiness.md`
19. `docs/reports/20260827-kr-afternoon-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-kr-afternoon-data-completeness-matrix.json
docs/reports/20260827-kr-afternoon-natural-reproof-readiness.json
```

---

# 27. Required gates

Set exactly:

```text
KR_AFTERNOON_NATURAL =
LIVE_PASS /
MATERIAL_P1_FOUND_STOP /
P0_FOUND_STOP /
NOT_OBSERVED

KR_TARGET_SESSION =
2026-08-27

KR_COMPLETED_SESSION =
PASS / FAIL

KR_PACKET_INTEGRITY =
PASS / FAIL

KR_EXACTLY_ONCE =
PASS / FAIL

DUPLICATE_DELIVERY =
0 / NONZERO

ORPHAN_DELIVERY =
0 / NONZERO

KR_EXACT_MESSAGE_PAYLOAD_MATCH =
PASS / FAIL

KIWOOM_KA20001 =
PASS / PARTIAL_SAFE / FAIL

KOSPI_BREADTH =
PASS / FAIL

KOSDAQ_BREADTH =
PASS / FAIL

KR_BREADTH_SEMANTICS =
PASS / FAIL

INDEX_RETURN_AS_BREADTH =
0 / NONZERO

KIWOOM_KA20003 =
PASS / PARTIAL_SAFE / FAIL

KR_SIZE_STYLE_CONTEXT =
PASS / PARTIAL_SAFE / FAIL

SECTOR_RETURN_AS_SECTOR_BREADTH =
0 / NONZERO

TOTAL_NUMERIC_PATHS = ...
SUPPORTED_CANONICAL_PATHS = ...
REGISTERED_SUPPORTED_PATHS = ...
INTERNAL_ONLY_PATHS = ...
UNSUPPORTED_PATHS = ...

SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP =
0 / NONZERO

UNKNOWN_NUMERIC_SEMANTIC_REGISTERED =
0 / NONZERO

WILDCARD_REGISTRY_BYPASS =
0 / NONZERO

NUMERIC_GATE =
PASS / FAIL

READY_FOR_AI =
true / false

ROUTE =
AI / deterministic_fallback

UNEXPLAINED_AI_INELIGIBILITY =
0 / NONZERO

KIWOOM_KA10051 =
PASS / FAIL

KA10051_AGGREGATE_FLOW_OWNER =
PASS / FAIL

KOSPI_KA10066_PAGINATION =
PASS / FAIL

KOSDAQ_KA10066_PAGINATION =
PASS / FAIL

KA10066_DUPLICATE_ROWS =
0 / NONZERO

KOSPI_RECONCILIATION =
PASS /
UNRESOLVED_BASIS_OR_TAXONOMY /
FAIL

KOSDAQ_RECONCILIATION =
PASS /
UNRESOLVED_BASIS_OR_TAXONOMY /
FAIL

RECONCILIATION_TOLERANCE_WIDENED =
0 / NONZERO

UNRECONCILED_CONCENTRATION_PROSE =
0 / NONZERO

KRX_CROSS_PROVIDER =
PASS /
PUBLICATION_PENDING /
PARTIAL_SAFE /
FAIL

STALE_KRX_INJECTION =
0 / NONZERO

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

PRIOR_US_BODY_REUSED_AS_KR_PRIMARY =
0 / NONZERO

GLOBAL_CONTEXT_DOMINATES_KR_LOCAL =
0 / NONZERO

KR_FX_ONLY_DIGEST_WITH_LOCAL_MARKET_AVAILABLE =
0 / NONZERO

AI_FALLBACK_LOCAL_FIRST_PARITY =
PASS / FAIL

AI_FALLBACK_NUMERIC_SAFETY_PARITY =
PASS / FAIL

KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS =
0 / NONZERO

KR_SECTOR_MATERIAL_INFORMATION_LOSS =
0 / NONZERO

V3_PRICE_STRUCTURE_LEAK =
0 / NONZERO

PRICE_STRUCTURE_RUNTIME_ARMED =
0 / NONZERO

MARKET_FLOW_AS_FUNDAMENTAL_CHANGE =
0 / NONZERO

BUSINESS_THESIS_MUTATION_FROM_REVIEW =
0 / NONZERO

PRODUCTION_MUTATION_FROM_REVIEW =
0 / NONZERO

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
```

---

# 28. Natural reproof PASS rule

Set:

```text
KR_AFTERNOON_NATURAL = LIVE_PASS
```

only if:

```text
natural run observed
target session = 2026-08-27
exactly once
ka20001 index/breadth valid
ka20003 size/sector safe
ka10051 aggregate flow valid
ka10066 pagination complete
reconciliation re-evaluated today
unreconciled concentration blocked
numeric registry complete for supported canonical paths
AI readiness explained
KR local-first digest PASS
material local evidence loss = 0
exact payload match PASS
no Price Structure v3 leak
P0 = 0
material P1 = 0
```

Then:

```text
NATURAL_KR_REPROOF = PASS
```

and the master gate may move:

```text
PRICE_STRUCTURE_TRACK_C = READY_TO_START
```

only if all other master prerequisites are also satisfied.

This task itself must NOT start or arm Track C.

---

# 29. Failure rule

If a material issue is found:

```text
KR_AFTERNOON_NATURAL = MATERIAL_P1_FOUND_STOP
```

or:

```text
P0_FOUND_STOP
```

Return exact failing data family, packet path, AI/fallback path, exact message symptom and severity.

Do not repair.

Next action:

```text
BOUNDED_KR_MARKET_REPAIR
```

---

# 30. Completion response

Return:

```text
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

NATURAL_RUN_ID = ...
TARGET_SESSION = 2026-08-27
PACKET_ID = ...
PACKET_READY_AT = ...
ROUTE = ...

KR_PACKET_INTEGRITY = ...
KR_EXACTLY_ONCE = ...
KR_EXACT_MESSAGE_PAYLOAD_MATCH = ...

KOSPI_CLOSE = ...
KOSPI_RETURN = ...
KOSPI_ADVANCE = ...
KOSPI_DECLINE = ...
KOSPI_UNCHANGED = ...
KOSPI_AD_RATIO = ...

KOSDAQ_CLOSE = ...
KOSDAQ_RETURN = ...
KOSDAQ_ADVANCE = ...
KOSDAQ_DECLINE = ...
KOSDAQ_UNCHANGED = ...
KOSDAQ_AD_RATIO = ...

KOSPI_SIZE_CONTEXT = ...
KOSDAQ_SIZE_CONTEXT = ...

KOSPI_SECTOR_LEADERS = ...
KOSPI_SECTOR_LAGGARDS = ...
KOSDAQ_SECTOR_LEADERS = ...
KOSDAQ_SECTOR_LAGGARDS = ...

RUN_NUMERIC_TOTAL = ...
RUN_SUPPORTED_CANONICAL = ...
RUN_REGISTERED_SUPPORTED = ...
RUN_INTERNAL_ONLY = ...
RUN_UNSUPPORTED = ...

NUMERIC_GATE = ...
READY_FOR_AI = ...
OTHER_AI_BLOCKING_GATES = ...

KOSPI_FOREIGN_FLOW = ...
KOSPI_INSTITUTION_FLOW = ...
KOSPI_RETAIL_FLOW = ...

KOSDAQ_FOREIGN_FLOW = ...
KOSDAQ_INSTITUTION_FLOW = ...
KOSDAQ_RETAIL_FLOW = ...

KOSPI_KA10066_PAGES = ...
KOSPI_KA10066_ROWS = ...
KOSDAQ_KA10066_PAGES = ...
KOSDAQ_KA10066_ROWS = ...

KOSPI_RECONCILIATION = ...
KOSDAQ_RECONCILIATION = ...
UNRECONCILIATED_CONCENTRATION_PROSE = 0

KRX_CROSS_PROVIDER = ...

KR_LOCAL_FIRST_DIGEST = ...
KOSPI_KOSDAQ_DIRECTION_USED = ...
KR_BREADTH_USED = ...
KR_AGGREGATE_FLOW_USED = ...
KR_SIZE_CONTEXT_USED = ...
KR_SECTOR_CONTEXT_USED = ...

AI_FALLBACK_LOCAL_FIRST_PARITY = ...
AI_FALLBACK_NUMERIC_SAFETY_PARITY = ...

KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
KR_SECTOR_MATERIAL_INFORMATION_LOSS = 0

V3_PRICE_STRUCTURE_LEAK = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0

PRODUCTION_MUTATION_FROM_REVIEW = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_AFTERNOON_NATURAL =
LIVE_PASS /
MATERIAL_P1_FOUND_STOP /
P0_FOUND_STOP /
NOT_OBSERVED

NATURAL_KR_REPROOF =
PASS /
PENDING /
FAIL

PRICE_STRUCTURE_TRACK_C =
READY_TO_START /
DO_NOT_START

NEXT_ACTION =
REVIEW_MASTER_GATES /
WAIT_FOR_NEXT_NATURAL_KR_CLOSE /
BOUNDED_KR_MARKET_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 31. Mandatory completion bundle

Create:

`20260827-kr-afternoon-natural-market-data-review-and-reproof-bundle.zip`

Include:

```text
exact instruction
natural run identity
exactly-once
ka20001 index/breadth
ka20003 size/sector
ka10051 aggregate flow
ka10066 pagination
reconciliation
concentration eligibility
numeric registry
AI readiness
KRX cross-provider
local-first reproof
AI/fallback parity
exact message
evidence utilization
message quality
safety parity
data completeness JSON
readiness JSON
artifact index
```

Do not include secrets, auth headers, account identifiers, private tokens, or hidden chain-of-thought.

Compute SHA-256.

---

# 32. Final principle

Today's Korean afternoon review must prove:

```text
2026-08-27 completed Korean session
→ current Kiwoom index/breadth
→ current local participant flow
→ current size/sector structure
→ safe numeric registry
→ reconciliation-aware concentration boundary
→ KR local-first digest
→ one exact natural message
```

Not:

```text
KR FX + prior US/global context
→ generic market summary
```

And until Price Structure Track C is explicitly armed:

```text
SR/Fib v3 current-price-structure block
must remain invisible.
```
