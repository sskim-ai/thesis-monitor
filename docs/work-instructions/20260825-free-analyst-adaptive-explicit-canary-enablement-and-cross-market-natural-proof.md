# thesis-monitor — Free Analyst + Adaptive Renderer Explicit Canary Enablement & Cross-Market Natural Proof

## Metadata

- Workstream: `COMMON_AI_CORE_V1_CANARY`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: `2026-08-25 12:36 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `EXPLICIT_CANARY_ENABLEMENT + NATURAL_PROOF`
- Open Research production integration: `OUT_OF_SCOPE`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Current expected production main / operating

`cd0fb79a6925d75029debb24f00d1a4c7495aa75`

Resolve the actual latest safe `origin/main` and operating SHA before execution.

### Completed integration state

```text
PRODUCTION_ASSIST_CONTROL_PLANE = B
Production Assist governance = OFF
Pilot = enabled, unchanged

FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = PASS
US run-37 Free Analyst = 14/14
US run-37 Adaptive Renderer = 14/14
KR immutable replay = 8/8 PASS

hard safety errors = 0
new-path price-particle errors = 0
new-path repeated-price errors = 0

COMMON_AI_CORE_V1 = INTEGRATED_READY_NOT_ARMED

Free Analyst Adaptive enabled = false/current
Open Research production integration = 0

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Known P2:
- broad-cohort generic synthesis repetition: 2 cases
- full-cohort mode intentionally disabled

### Goal

Explicitly arm the already-integrated Free Analyst + Adaptive Renderer **limited production canary** without enabling full cohort.

Then collect natural user-visible proof on:
1. the first eligible naturally scheduled KR production run after activation
2. the next eligible naturally scheduled US production run after activation

No manual production runs.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-free-analyst-adaptive-explicit-canary-enablement-and-cross-market-natural-proof.md`

Before any control-plane change:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main / operating SHA
2. verify `COMMON_AI_CORE_V1 = INTEGRATED_READY_NOT_ARMED`
3. verify `PRODUCTION_ASSIST_CONTROL_PLANE = B`
4. commit/push this exact instruction as a docs-only instruction commit
5. record instruction path / commit SHA / version
6. create a dedicated canary-review branch
7. if canary configuration is repo-managed, apply the smallest config-only diff and promote cleanly
8. if canary configuration is runtime control-plane state, use the supported control-plane operation and record before/after state
9. no force push / history rewrite

Recommended branch:

`codex/free-analyst-adaptive-explicit-canary`

---

# 1. Scope

This task may:

- explicitly enable the existing bounded Free Analyst + Adaptive canary
- set/confirm canary limits
- collect natural KR and US canary proof
- disable the canary automatically on a hard incident
- create reports

This task must NOT:

- enable full Free Analyst cohort
- integrate Open Research
- enable Event Attribution
- enable Trade AR
- change Inventory logic
- change Phase 9.0E
- change Macro temporal logic
- change price/RR logic
- change valuation logic
- alter production schedules
- manually run KR/US production
- manually send Telegram
- change Pilot
- change Production Assist governance state
- weaken any validator

---

# 2. Preflight control-plane audit

Before arming, record exact current values for:

```text
Production Assist governance
Pilot
Free Analyst Adaptive enabled/mode
canary max per run
market digest max
stock-message max
full cohort mode
kill switch
fallback mode
Open Research production state
Trade AR state
Inventory mode
Phase 9.0E mode
```

Hard preconditions:

```text
Production Assist governance = unchanged from current approved state
Pilot = unchanged
full Free Analyst mode = OFF
Open Research production integration = 0
Trade AR user-visible = OFF
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

If any precondition is false:
do not arm.
Set `CANARY_ENABLEMENT = BLOCKED_PRECONDITION`.

---

# 3. Re-run current canary simulation before activation

Using the already integrated production path and immutable packets, re-run the canary selector simulation once.

Required:

```text
candidate selection <= 3
market digest <= 1
stock messages <= 2
all selected candidates:
  Free Analyst PASS
  synthesis validator PASS
  Adaptive Renderer PASS
  hard validators PASS
  runtime-quality PASS
  material information loss = 0
```

Known prior simulation selected 3.

Do not require the same exact ticker/message selection if the deterministic selector legitimately changes due to code/config state.

No ticker hard-coding.

---

# 4. Explicit canary state

Arm the supported canary state, repository-equivalent to:

```text
FREE_ANALYST_ADAPTIVE_CANARY = ENABLED_PENDING_NATURAL
FREE_ANALYST_ADAPTIVE_FULL = OFF
```

Maximum per natural production run:

```text
market digest <= 1
stock messages <= 2
total AI-assisted user-visible messages <= 3
```

All other slots use the existing current production path / deterministic fallback.

Do not alter `Production Assist governance = OFF` if current control-plane design supports the canary independently, as already classified by Branch B.

---

# 5. Independent kill switch

Verify before activation that a supported kill switch exists and works in simulation/config validation.

Required rollback target:

```text
FREE_ANALYST_ADAPTIVE_CANARY = DISABLED
```

Rollback must:

- preserve normal production delivery
- preserve deterministic fallback
- not disable Pilot
- not alter stored investment logic
- not alter receipts from already completed runs
- not require schema change

Do not trigger the kill switch merely as a destructive live test.

Use config/control-plane validation or safe simulation.

---

# 6. Canary selection contract

A message is canary-eligible only if all are true:

```text
Free Analyst generated = YES
synthesis support validation = PASS
Adaptive Renderer = PASS
all hard validators = PASS
runtime quality = PASS
material information loss = 0
claim provenance complete = YES
research dependency = NO
Trade AR user-visible dependency = NO
receipt ownership unambiguous = YES
```

If any condition fails:
that slot must use current production/fallback.

---

# 7. Canary selector must remain deterministic

Do not add an LLM call to choose canary messages.

Selection must be auditable.

Persist per slot:

```text
eligible
selected
renderer
selection_reason
rejection_reason
runtime_quality
final_delivery_mode
```

No ticker hard-coding.

---

# 8. Existing P2 repetition guard

The known broad-cohort generic-synthesis repetition is P2 because full mode is OFF.

For canary selection:

- a candidate with scoped runtime-quality PASS may be selected
- a candidate with the known repetition issue must not be selected if runtime-quality rejects it
- do not weaken the repetition validator
- do not implement a broad prompt rewrite in this task

Report whether P2 repetition appeared in:
- candidate pool
- selected canary messages
- delivered messages

Hard target for selected/delivered canary:

`material repetition error = 0`

---

# 9. No Open Research dependency

Every canary candidate must be generated from the standard verified production packet only.

Hard target:

```text
Open Research imports in canary runtime path = 0
web/news search calls = 0
research sidecar required = 0
```

Open Research remains a separate future integration.

---

# 10. First eligible KR natural run

After activation, do not manually run anything.

Observe the first naturally scheduled KR production run that is eligible after the canary is armed.

At review time record:

```text
run_id
packet_id
scheduled_at
actual_start
actual_terminal
expected messages
actual delivered messages
AI-assisted canary slots
current/fallback slots
receipt refs
```

If today’s KR production slot is already past or becomes ineligible:
do not force it.
Use the next eligible natural KR run.

---

# 11. KR canary acceptance

For every actually delivered KR canary message record:

```text
slot
ticker / market digest
selected renderer
Free Analyst support refs
hard validator result
runtime-quality result
actual exact message
delivery timestamp
receipt ref
```

Hard targets:

```text
AI-assisted delivered <= 3
market digest AI <= 1
stock AI <= 2

Fact mismatch = 0
Unsupported numeric = 0
Unsupported causality = 0
Temporal violation = 0
Trade AR leak = 0
Hidden arithmetic = 0
External unsourced facts = 0
Material information loss = 0
Runtime-quality hard failure delivered = 0
```

Packet targets:

```text
expected delivery count complete
duplicates = 0
orphans = 0
receipt integrity = PASS
exactly once = PASS
```

Set:

```text
KR_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED
```

---

# 12. KR natural message comparison

For every canary slot create:

```text
ACTUAL_DELIVERED_CANARY
DETERMINISTIC_FALLBACK_REFERENCE
```

Optionally include:
- non-delivered Direct
- non-delivered Hybrid

Human review:

```text
MATERIAL_IMPROVEMENT
NO_MEANINGFUL_CHANGE
WORSE
```

Do not treat `NO_MEANINGFUL_CHANGE` as failure if safety is intact.

---

# 13. KR hard-incident rollback

Immediately disable the canary if an actually delivered canary message has any of:

- wrong Fact / number / period
- wrong direction relation
- unsupported causal conclusion
- temporal violation
- Trade AR/broad AR/AP leak
- hidden external fact
- receipt/exactly-once issue
- duplicate delivery

Then:

```text
FREE_ANALYST_ADAPTIVE_CANARY = DISABLED
KR_FREE_ANALYST_CANARY_NATURAL = FAIL
```

Normal deterministic production must remain active.

Do not wait for US proof after a hard incident.

---

# 14. After KR LIVE_PASS

If KR canary = LIVE_PASS:

- keep canary limit unchanged
- do not expand beyond 3
- do not enable full mode
- keep canary armed for the next eligible US natural production run
- do not change selector thresholds
- do not enable Open Research

Set interim state:

```text
COMMON_AI_CORE_V1 =
CANARY_KR_LIVE_PASS_PENDING_US
```

---

# 15. Next eligible US natural run

Observe the next naturally scheduled US production run after the canary remains safely armed.

Do not manually run US production.

Record the same lifecycle metadata as KR.

---

# 16. US canary acceptance

For every delivered US canary message verify the same hard safety targets as KR.

Also explicitly re-check prior US repairs:

```text
directional relation binding = PASS
FCF fiscal/YTD/FY identity = PASS
current-price RR ownership = PASS
Macro temporal = PASS
Inventory relation semantics = PASS
```

Set:

```text
US_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED
```

---

# 17. Cross-market completion gate

Set:

```text
FREE_ANALYST_ADAPTIVE_CANARY_CROSS_MARKET =
LIVE_PASS / PARTIAL_PASS / FAIL
```

### LIVE_PASS

Requires:

```text
KR natural canary = LIVE_PASS
US natural canary = LIVE_PASS

both markets:
exactly once = PASS
duplicates/orphans = 0
hard safety errors = 0
runtime-quality delivered errors = 0
fallback reachable = YES
```

### PARTIAL_PASS

One market LIVE_PASS, the other not yet observed.

### FAIL

Any delivered hard canary regression.

---

# 18. Common AI Core v1 status

State progression:

```text
before:
INTEGRATED_READY_NOT_ARMED

after arm, before natural proof:
INTEGRATED_CANARY_PENDING_NATURAL

after KR only PASS:
CANARY_KR_LIVE_PASS_PENDING_US

after KR + US PASS:
CANARY_CROSS_MARKET_LIVE_PASS
```

Do not call full cohort complete.

---

# 19. Full mode remains off

Even after cross-market LIVE_PASS:

```text
FREE_ANALYST_ADAPTIVE_FULL = OFF
```

No automatic cohort expansion.

A separate decision/instruction is required for:
- wider cohort
- full mode
- Open Research integration

---

# 20. Existing current/fallback slots

For every non-canary slot verify:

- normal message still delivered
- packet completion intact
- no duplicate selector output
- no receipt mismatch

A canary feature must not reduce coverage for the other messages.

---

# 21. Per-message final-selection audit

For every message in the natural run create:

```text
slot
Free Analyst generated?
canary eligible?
canary selected?
selected renderer
hard validation
runtime-quality
fallback reason
final delivery mode
receipt ref
```

Target:
exactly one final delivery mode per slot.

---

# 22. Delivery integrity

Hard invariant:

```text
one packet
→ one final selected message per expected slot
→ one packet-bound delivery intent
→ one receipt lifecycle
```

No AI and fallback dual-send.

No packetless delivery.

---

# 23. Runtime-quality natural audit

Specifically count in actual canary messages:

```text
price particle / grammar errors
repeated price sentences
generic synthesis repetition
duplicate next-check / Unknown
template skeleton recurrence
```

Set:

```text
CANARY_RUNTIME_QUALITY =
PASS / FAIL
```

P2 prose imperfection may be logged if not material, but any message that failed the authoritative runtime-quality gate must not have been delivered as canary.

---

# 24. No research-related claims

Search all delivered canary text/provenance for evidence of Open Research leakage.

Hard target:

```text
research evidence refs = 0
web-derived claims = 0
Event Attribution refs = 0
```

---

# 25. Kill-switch drill after natural PASS — non-destructive

After at least one natural LIVE_PASS, verify rollback readiness without unnecessarily interrupting a scheduled run.

Preferred:
- validate config transition in a non-production simulation/staged control-plane check

Do not toggle live canary off/on just for demonstration if doing so risks a scheduled run.

Record:
- expected command/config change
- expected state
- recovery time
- no schema dependency

---

# 26. Optional canary pause between KR and US

Do NOT pause by default after KR PASS.

Pause only if:
- material P1/P0 is found
- unexpected delivery behavior
- canary selected a message that should have failed quality
- control-plane drift

If paused:
report reason.

---

# 27. Open Research status

Keep:

```text
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
OPEN_RESEARCH_ENABLED_IN_PRODUCTION = false
```

Do not use today’s canary result as implicit approval to enable research.

---

# 28. Future next step after cross-market PASS

If cross-market canary LIVE_PASS and P0/P1 = 0:

Recommended next major task:

`OPEN_RESEARCH_SELECTIVE_PRODUCTION_INTEGRATION`

Do not expand Free Analyst full cohort and Open Research simultaneously.

Open Research should remain separately kill-switchable.

---

# 29. Full validation before canary arming

Required before control-plane activation:

```text
focused canary tests PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action unchanged
operationId 20/20 unique
schema unchanged
API health PASS
worktrees clean
```

If no code diff is needed:
still run appropriate smoke/focused validation of current main.

---

# 30. Required focused tests

Confirm existing tests or add minimal tests for:

- canary max total 3
- market digest max 1
- stock max 2
- deterministic selection
- no ticker hard-code
- runtime-quality eligibility
- hard-validator eligibility
- full mode stays off
- Open Research excluded
- Trade AR excluded
- fallback on candidate failure
- exactly-one final selection
- kill switch
- Branch-B control-plane behavior
- non-selected slot delivery unaffected

Do not add broad feature work.

---

# 31. Required reports — enablement

Create:

1. `docs/reports/20260825-free-analyst-canary-control-plane-preflight.md`
2. `docs/reports/20260825-free-analyst-canary-simulation.md`
3. `docs/reports/20260825-free-analyst-canary-enablement.md`
4. `docs/reports/20260825-free-analyst-canary-kill-switch-readiness.md`

---

# 32. Required reports — KR natural

Create after first eligible KR run:

5. `docs/reports/20260825-free-analyst-kr-canary-natural-review.md`
6. `docs/reports/20260825-free-analyst-kr-canary-sent-message-bundle.md`
7. `docs/reports/20260825-free-analyst-kr-canary-selection-audit.md`
8. `docs/reports/20260825-free-analyst-kr-canary-delivery-integrity.md`

If the first eligible KR run occurs on a later date:
use the actual date in filenames and cross-reference this instruction.

---

# 33. Required reports — US natural

Create after next eligible US run:

9. `docs/reports/<actual-date>-free-analyst-us-canary-natural-review.md`
10. `docs/reports/<actual-date>-free-analyst-us-canary-sent-message-bundle.md`
11. `docs/reports/<actual-date>-free-analyst-us-canary-selection-audit.md`
12. `docs/reports/<actual-date>-free-analyst-us-canary-delivery-integrity.md`

---

# 34. Required combined reports

13. `docs/reports/20260825-common-ai-core-v1-canary-gates.md`
14. `docs/reports/20260825-common-ai-core-v1-canary-artifact-index.md`
15. `docs/reports/20260825-common-ai-core-v1-canary-summary.json`

If final US proof occurs later:
update/finalize the cross-market report with the actual terminal date.

---

# 35. Exact sent-message bundle

For every actual natural canary run, preserve exact user-visible delivered text for canary slots.

Include:

```text
slot
renderer
actual message
deterministic fallback reference
delivery time
receipt ref
```

No Telegram destination IDs.

---

# 36. Canary gate report

`docs/reports/20260825-common-ai-core-v1-canary-gates.md`

Must contain:

```text
CANARY_ENABLEMENT =
PASS / BLOCKED_PRECONDITION / FAIL

FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_NATURAL /
DISABLED /
BLOCKED

FREE_ANALYST_ADAPTIVE_FULL = OFF

KR_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

US_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

FREE_ANALYST_ADAPTIVE_CANARY_CROSS_MARKET =
LIVE_PASS / PARTIAL_PASS / FAIL

CANARY_RUNTIME_QUALITY =
PASS / FAIL / NOT_OBSERVED

KR_AI_ASSISTED_DELIVERED = ...
US_AI_ASSISTED_DELIVERED = ...

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

OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

COMMON_AI_CORE_V1 =
INTEGRATED_CANARY_PENDING_NATURAL /
CANARY_KR_LIVE_PASS_PENDING_US /
CANARY_CROSS_MARKET_LIVE_PASS /
INTEGRATION_FAIL

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

---

# 37. Next-action policy

### If KR FAIL
```text
NEXT_ACTION = FREE_ANALYST_CANARY_BOUNDED_REPAIR
```
Disable canary.

### If KR PASS, US not yet observed
```text
NEXT_ACTION = WAIT_FOR_US_FREE_ANALYST_NATURAL_CANARY
```

### If KR + US PASS
```text
NEXT_ACTION = OPEN_RESEARCH_SELECTIVE_PRODUCTION_INTEGRATION
```

### If only P2 remains
Do not block next major phase unless P2 affects material user quality.

---

# 38. Result ZIPs

After enablement + KR proof, create an interim ZIP:

`20260825-free-analyst-adaptive-canary-interim-bundle.zip`

After US natural proof, create final:

`20260825-free-analyst-adaptive-cross-market-canary-bundle.zip`

If US occurs on a later date, retaining the instruction date in the bundle name is acceptable if the report clearly states actual observation date.

Compute/report SHA-256 for each.

---

# 39. Completion response — enablement / KR stage

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
CONFIG_OR_IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...

PRODUCTION_ASSIST_CONTROL_PLANE = B
PRODUCTION_ASSIST_GOVERNANCE = OFF
PILOT = unchanged

CANARY_ENABLEMENT = ...
FREE_ANALYST_ADAPTIVE_CANARY = ...
FREE_ANALYST_ADAPTIVE_FULL = OFF

CANARY_MAX_TOTAL = 3
CANARY_MAX_MARKET = 1
CANARY_MAX_STOCK = 2

KR_FREE_ANALYST_CANARY_NATURAL = ...
KR_AI_ASSISTED_DELIVERED = ...
KR_EXPECTED_MESSAGES = ...
KR_ACTUAL_MESSAGES = ...

DUPLICATES = ...
ORPHANS = ...
EXACTLY_ONCE = ...
RECEIPT_INTEGRITY = ...

FACT_MISMATCH = ...
UNSUPPORTED_CAUSALITY = ...
TEMPORAL_VIOLATIONS = ...
TRADE_AR_LEAK = ...
RUNTIME_QUALITY = ...

COMMON_AI_CORE_V1 = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

INTERIM_ZIP = ...
INTERIM_ZIP_SHA256 = ...
```

---

# 40. Completion response — final US / cross-market stage

Return:

```text
US_FREE_ANALYST_CANARY_NATURAL = ...
US_AI_ASSISTED_DELIVERED = ...
US_EXPECTED_MESSAGES = ...
US_ACTUAL_MESSAGES = ...

FREE_ANALYST_ADAPTIVE_CANARY_CROSS_MARKET = ...

DUPLICATES = 0
ORPHANS = 0
EXACTLY_ONCE = PASS
RECEIPT_INTEGRITY = PASS

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0

CANARY_RUNTIME_QUALITY = ...

COMMON_AI_CORE_V1 =
CANARY_CROSS_MARKET_LIVE_PASS

FREE_ANALYST_ADAPTIVE_FULL = OFF
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
OPEN_RESEARCH_SELECTIVE_PRODUCTION_INTEGRATION

FINAL_ZIP = ...
FINAL_ZIP_SHA256 = ...
FINAL_REPORT_COMMIT = ...
```

---

# 41. Severity

## P0

- wrong delivered Fact/number/period
- directional relation wrong
- unsupported causal claim delivered
- temporal violation delivered
- Trade AR/broad AR/AP leak
- hidden external fact
- hidden arithmetic accepted
- duplicate Telegram
- receipt / exactly-once regression
- full mode accidentally enabled
- Open Research accidentally activated
- Production Assist governance bypass

## P1

- per-message fallback fails
- canary exceeds max cohort
- runtime-quality rejected message still delivered
- selector becomes nondeterministic
- common KR/US path diverges
- non-selected production slots fail to deliver
- kill switch unavailable

## P2

- harmless style preference
- some canary messages show no material improvement
- generic synthesis repetition rejected before delivery
- canary only exercises one renderer naturally
- report polish

---

# 42. Final principle

This task is not another AI-development phase.

The Common AI Core code is already integrated.

This task proves the final production behavior:

```text
verified packet
→ Free Analyst
→ synthesis validation
→ Adaptive Renderer
→ hard validation
→ at most 3 user-visible canary messages

all other slots
→ current safe production path

any AI failure
→ deterministic fallback
```

Success means the common AI reasoning engine has crossed the final boundary from replay-safe to naturally user-visible, first in KR and then in US, without expanding full cohort and without activating Open Research.
