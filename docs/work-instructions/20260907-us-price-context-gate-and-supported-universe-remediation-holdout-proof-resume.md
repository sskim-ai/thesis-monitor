# Thesis Monitor — US Price-Context Gate & Supported-Universe Remediation + Holdout Proof Resume

## 0. Task identity

Suggested work-instruction filename:

```text
20260907-us-price-context-gate-and-supported-universe-remediation-holdout-proof-resume.md
```

Suggested result bundle:

```text
thesis-monitor-20260907-us-price-context-gate-supported-universe-remediation-holdout-proof-resume-report.zip
```

This task follows the second bounded US source-coverage attempt.

The prior task successfully repaired the generic US bank/insurer sector-family mapping for JPM and proved the repair with generic tests.

It did **not** obtain US4 because:

```text
NVDA = PASS
JPM  = PASS after generic mapping repair
WMT  = FAIL: PRICE_CONTEXT unavailable
BRK-B = FAIL: sector mapping resolved, then PRICE_CONTEXT unavailable
MSFT = PASS

source-sufficient US = 3 / 4
```

and:

```text
expanded US reserve count = 0
canonical supported unexposed US universe exhausted = 1
```

The current blocker is therefore no longer the original fundamental-family mapping gap.

The current blocker is:

```text
US price-context readiness / gating
+
insufficient breadth of the canonical supported unexposed US candidate universe
```

This task must address those generically and safely before any real holdout model call.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260907-bounded-us-source-coverage-remediation-holdout-proof-resume-report.zip
```

Verified ZIP SHA-256:

```text
b37b059a90dc55c023f9a586681f41d8e67a1cc45d90f83a4453971c8a0ec434
```

The paired checksum file contains the same hash.

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest result integrity:

```text
artifact_count = 135
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
artifact_secret_scan_failure_count = 0

full_tests = PASS
ruff = PASS
diff_check = PASS
```

Latest repository provenance:

```text
base_sha =
f9e26b722477543110e7bd4cc61f4eaef5a0809b

work_instruction_commit =
501353055b04950e69881b8fd325d3d2e09b7a37

implementation_commit =
4fab25026d4c3a176d3ee7f41c777865410614ea

final_head_sha =
4fab25026d4c3a176d3ee7f41c777865410614ea

branch =
codex/20260907-bounded-us-source-coverage-remediation-holdout-proof-resume
```

Do not assume current HEAD remains unchanged.

---

# 2. Closed items — do not reopen without contradictory evidence

The following are closed:

```text
runner↔adapter codex_bin defect = CLOSED

generic US bank/insurer sector-family mapping root cause =
CONFIRMED

generic mapping repair applied = 1

ticker_specific_source_exception_count = 0

bank/insurer focused tests = PASS
11 passed

JPM post-repair source sufficiency = PASS
```

The generic mapping repair added legitimate:

```text
SECTOR_OPERATING_CURRENT
```

coverage from official us-gaap sector evidence.

Do not remove, weaken, or ticker-specialize that repair.

---

# 3. Current exact US state

Original deterministic order remains:

```text
1 NVDA
2 JPM
3 WMT
4 BRK-B
5 MSFT
```

Post-remediation:

```text
NVDA  = PASS
JPM   = PASS
WMT   = FAIL
BRK-B = FAIL
MSFT  = PASS
```

Selected pre-model US set currently:

```text
NVDA
JPM
MSFT
```

Required target:

```text
4
```

Current:

```text
3
```

No final US4 exists yet.

No final new 16-issuer holdout exists yet.

---

# 4. Current WMT facts

Latest forensic result:

```text
symbol_normalization = PASS
security_identity = PASS

base wrapper identity = success
base wrapper OHLCV = success
technical_context = UNAVAILABLE

raw_latest_available_bar = UNAVAILABLE
current_price_propagation =
NOT_REACHED_NO_DAILY_BAR

price_date = UNAVAILABLE

provider_http_502_observation_count = 108

wmt_price_context_root_cause =
PROVIDER_SOURCE_ABSENCE

canonical_price_basis_available = 0

repair_applied = 0
decision =
LEAVE_SOURCE_INSUFFICIENT_USE_PRECOMMITTED_ORDER
```

Validation errors:

```text
current_price_unavailable
price_as_of_unavailable
technical_context_not_safe:UNAVAILABLE
```

Do not fabricate a last price from a stale or unavailable bar.

---

# 5. Current BRK-B facts

The generic sector-family repair succeeded semantically:

```text
SECTOR_OPERATING_CURRENT present = 1
```

but BRK-B still failed because:

```text
PRICE_CONTEXT unavailable

current_price_unavailable
price_as_of_unavailable
technical_context_not_safe:UNAVAILABLE
```

Latest result did not perform the same dedicated price-context forensic for BRK-B that it performed for WMT.

Therefore BRK-B price failure must be independently diagnosed in this task.

Do not assume BRK-B has the same root cause as WMT.

Possible hypotheses may include:

```text
share-class symbol normalization
provider-specific symbol alias
provider source absence
safe price propagation gap
stale/insufficient bars
security-basis block
```

These are hypotheses only until proven.

---

# 6. Current reserve-universe blocker

Latest reserve policy reported:

```text
canonical_supported_unexposed_us_count = 5

original ranks =
NVDA
JPM
WMT
BRK-B
MSFT

reserve_extension_count = 0

zero_extension_reason =
CANONICAL_SUPPORTED_UNEXPOSED_UNIVERSE_EXHAUSTED
```

This means the current candidate-universe mechanism can produce no additional unseen supported US reserve after the original five.

Do not manually add a favorite ticker.

The supported-universe limitation itself must be audited.

---

# 7. KR state — preserve, do not redo the diagnostic

Historical KR source target remains:

```text
PASS
12 / 12 selected
```

Preserved KR12:

```text
142210
060900
002680
035420
216050
100700
001530
487580
038870
342870
060230
415380
```

Do not rerun the full KR source-coverage discovery merely because US remains blocked.

A fresh combined source generation may revalidate these issuers only after US4 is obtained.

---

# 8. Experiment/model state

Because US target failed pre-model:

```text
new_holdout_cohort = []
fresh_combined_source_generation = NOT_CREATED
fresh_combined_source_lock = NOT_CREATED

FIRST = NOT_RUN
A = NOT_RUN
B = NOT_RUN
C = NOT_RUN

real_holdout_model_invocation_count = 0
real_holdout_subject_output_count = 0

holdout_output_exposure_state = UNEXPOSED
holdout_retirement_state = NOT_CREATED

ownership_generalization_verdict = NOT_MEASURED
```

The candidate set remains unexposed to the real ownership model.

---

# 9. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

If unexplained semantic drift exists in:

```text
Directional Core
Price-Timing
renderer/action ownership
DecisionEvidencePacket semantics
source-sufficiency policy
prompt/schema
model/context construction
ContinuationTransportAdapter
transport lifecycle
timeout ownership
```

then:

```text
STOP
UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT
```

Do not reset, merge, cherry-pick, or silently discard unrelated work.

---

# 10. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then modify bounded source/universe tooling.

---

# 11. Allowed mutation surface

Allowed only when generic root cause is proven:

```text
US price symbol normalization / aliasing
US price-provider safe fallback already supported by repository architecture
US current-price/technical-context propagation bug
cold-start packet readiness orchestration when implementation contradicts existing conditional-price semantics
canonical supported US security-universe construction
experiment-only candidate universe / reserve tooling
tests and fixtures for the above
report tooling
```

Preferred:

```text
generic provider/security-class behavior
not ticker-specific exceptions
```

---

# 12. Forbidden mutations

Do not change:

```text
Directional Core ownership
Price-Timing ownership
renderer/action ownership

BUY/HOLD/SELL thresholds
BUY:SELL balance semantics
HOLD lean semantics
new-buyer/holder transition semantics

fundamental source-sufficiency families
to make a candidate pass

accounting attribution
numeric provenance
ADR/security basis
official provisional earnings safety

model
reasoning effort

ContinuationTransportAdapter canonical contract
transport topology
timeout value
timeout ownership

production DB
scheduler
Telegram
monitoring registration
live V2 / Structured Autonomy
Night Futures
```

Do not add:

```text
if ticker == "WMT"
if ticker == "BRK-B"
```

or equivalent production exceptions.

Required:

```text
ticker_specific_source_exception_count = 0
```

---

# 13. Phase A — Audit the price-context gate itself

Before fixing providers or expanding the universe, identify the exact contract that causes:

```text
current_price_unavailable
price_as_of_unavailable
technical_context_not_safe:UNAVAILABLE
```

to make:

```text
coldstart packet_created = false
source_pipeline_status =
SECURITY_OR_ACCOUNTING_BASIS_BLOCK
```

For the current architecture, distinguish three concepts:

```text
FUNDAMENTAL_DIRECTIONAL_SOURCE_SUFFICIENCY

PRICE_TIMING_INPUT_READINESS

FULL_END_TO_END_HOLDOUT_READINESS
```

These must not be silently assumed to be identical.

## 13.1 Questions to answer from current code/contracts

Determine:

1. Is safe current price explicitly required by the canonical DecisionEvidencePacket schema?
2. Is safe technical context explicitly required for Directional Core invocation?
3. Is price/technical context conditional/optional in the canonical investment framework?
4. Does Price-Timing already define a safe `UNAVAILABLE` path?
5. Is `SECURITY_OR_ACCOUNTING_BASIS_BLOCK` being used for a pure price-readiness failure?
6. Is packet assembly rejecting an otherwise fundamentally sufficient issuer before stage ownership can apply?
7. Is this behavior an intentional source-sufficiency policy or an implementation coupling bug?

Required classification:

```text
PRICE_CONTEXT_GATE_CLASSIFICATION =
INTENTIONAL_FULL_PIPELINE_REQUIREMENT /
IMPLEMENTATION_OVERCOUPLING /
SCHEMA_REQUIREMENT /
UNRESOLVED
```

Do not modify the gate until this classification is supported.

---

# 14. Conditional-price semantic constraint

The system's public investment semantics treat price/technical analysis as conditional:

```text
if actual price context exists
→ use it

if price/technical context does not exist
→ do not invent technical indicators/support/resistance/targets
```

This does not automatically prove that the experiment's full end-to-end holdout may accept a price-unready issuer.

Reconcile current implementation against the actual repository contract.

If implementation already has an intended `UNAVAILABLE` Price-Timing path but packet assembly prevents reaching it, that may be an implementation bug.

If the full ownership experiment intentionally requires price-ready subjects, preserve that policy.

Do not reinterpret policy merely to fill US4.

---

# 15. Gate repair authorization boundary

A gate repair is allowed in this task only if:

```text
existing schema/contracts already permit the unavailable-price state
AND
current rejection is proven to be implementation overcoupling
AND
repair does not weaken fundamental source sufficiency
AND
repair does not fabricate price data
AND
Price-Timing still receives an explicit safe unavailable state
```

Then repair generically.

Required tests:

```text
fundamentally sufficient + price available
fundamentally sufficient + price unavailable
fundamentally insufficient + price available
price unavailable cannot produce technical claims
Price-Timing unavailable path cannot mutate Directional Core
```

If policy/schema semantics themselves must change:

```text
STOP
SOURCE_SUFFICIENCY_POLICY_CHANGE_REQUIRED
```

Do not make that semantic change inside this task.

Proceed only with provider/universe remediation.

---

# 16. Phase B — BRK-B price-context forensic

Perform the dedicated BRK-B price forensic that was missing previously.

Inspect:

```text
canonical security identity
share class
ticker normalization
provider-specific requested symbol(s)
raw provider responses
HTTP status / provider error
daily-bar count
latest bar if any
latest bar date
market/session freshness
safe current-price propagation
technical-context validator
security-basis validator
packet assembler
```

Explicitly compare common share-class representations only through supported repository/provider rules, such as possible provider formats.

Do not invent or brute-force arbitrary public symbols unless the repository already supports a provider alias strategy.

Required classification:

```text
BRKB_PRICE_CONTEXT_ROOT_CAUSE =
PROVIDER_SYMBOL_ALIAS_GAP /
PROVIDER_SOURCE_ABSENCE /
SAFE_PRICE_PROPAGATION_GAP /
STALE_OR_INSUFFICIENT_OHLCV /
SECURITY_BASIS_BLOCK /
OTHER_CONFIRMED /
UNRESOLVED
```

---

# 17. BRK-B repair rule

If a generic provider/share-class alias mapping is confirmed:

```text
repair generically for the security/share-class pattern
```

not for BRK-B alone.

Tests should cover:

```text
positive class-B/common-share alias fixture
ordinary single-class ticker unaffected
wrong alias rejected
security identity preserved
price currency/basis preserved
```

Do not let a provider alias change issuer/security identity.

If provider source is genuinely unavailable:

```text
leave BRK-B price-unready
```

and rely on expanded deterministic reserve universe.

---

# 18. Phase C — WMT source resilience audit

WMT produced:

```text
108 HTTP 502 observations
```

with no safe latest daily bar.

Determine whether those 502s came from:

```text
one canonical provider
multiple canonical providers
same endpoint repeatedly
session/cache layer
provider wrapper retries
```

Report:

```text
provider identities
request counts
HTTP status counts
retry behavior
fallback behavior
cache behavior
```

Do not expose secrets.

Required classification:

```text
WMT_PRICE_SOURCE_RESILIENCE =
SINGLE_PROVIDER_OUTAGE /
MULTI_PROVIDER_UNAVAILABLE /
FALLBACK_NOT_CONFIGURED /
FALLBACK_CONFIGURED_BUT_FAILED /
OTHER_CONFIRMED /
UNRESOLVED
```

---

# 19. WMT fallback repair boundary

A fallback repair is allowed only if the repository already contains another canonical safe price/OHLCV provider path whose:

```text
security identity
currency
price date
bar semantics
```

are validated.

Do not add an ad-hoc external source in this task merely for WMT.

Do not derive current price from stale bars.

If no safe canonical fallback exists:

```text
leave WMT insufficient
```

The goal is not to force WMT into the holdout.

---

# 20. Phase D — Audit canonical supported US universe construction

Explain why:

```text
canonical_supported_unexposed_us_count = 5
```

after an exposure/exclusion registry of 70 issuers.

Identify:

```text
source of canonical US security universe
universe row count before exposure filtering
eligibility filters
supported-security filters
market/exchange filters
security-type filters
identity-provider filters
price-provider filters if any
source-provider filters if any
exposure exclusions
deduplication behavior
```

Required report:

```text
us-supported-universe-funnel.json
```

with counts at every filter step.

Do not merely report final count 5.

---

# 21. Supported-universe root-cause classification

Classify the five-name universe limit as:

```text
INTENTIONAL_SUPPORTED_UNIVERSE_BOUNDARY
STALE_OR_INCOMPLETE_SECURITY_MASTER
OVERRESTRICTIVE_PROVIDER_INTERSECTION
OVERRESTRICTIVE_PRICE_READINESS_FILTER
OVERRESTRICTIVE_SOURCE_READINESS_FILTER
EXPOSURE_REGISTRY_DOMINATES_UNIVERSE
OTHER_CONFIRMED
UNRESOLVED
```

Multiple classifications may apply if supported.

Do not expand the universe before knowing which filter creates the bottleneck.

---

# 22. Generic US universe expansion authorization

Expansion is allowed only through a canonical repository-supported security universe/security master.

Acceptable generic expansion classes include, when already supported:

```text
additional US listed common equities
additional canonical SEC-identified issuers
additional supported exchanges
additional supported share classes
```

provided:

```text
identity can be validated
market = us
security type is allowed by existing contracts
issuer is absent from prior-real-issuer exposure registry
```

Do not:

```text
scrape arbitrary tickers
hand-pick issuers
include unsupported OTC securities
include funds when issuer-thesis framework expects operating companies
include ADR/security types without existing basis support
```

unless existing canonical contracts already allow them.

---

# 23. Universe expansion must be outcome-independent

Before source-sufficiency evaluation of any newly available issuer, produce:

```text
expanded-canonical-us-universe.json
expanded-us-reserve-policy-v2.json
```

The reserve ordering must be deterministic and frozen first.

Use the existing selection salt lineage:

```text
20260907-new-issuer-holdout-selection-ownership-proof-v1
```

or a documented deterministic derivative that does not depend on source/model outcomes.

Record:

```text
expanded universe count
post-exclusion count
reserve count
reserve ordering
selection rule
selection rule hash
exclusion registry hash
```

Do not order candidates by expected data quality after seeing results.

---

# 24. Minimum reserve objective

The previous task intended:

```text
additional reserve budget: 8–20
```

but obtained zero.

After canonical-universe remediation, target at least:

```text
8 deterministic unseen US reserve candidates
```

if the supported universe permits.

If fewer than eight exist but at least one exists, preserve the actual count and explain the remaining canonical limitation.

The task does not fail solely because reserve count is below eight if US4 can be obtained safely.

---

# 25. Phase E — Re-evaluate original five after bounded fixes

Re-evaluate in original order:

```text
1 NVDA
2 JPM
3 WMT
4 BRK-B
5 MSFT
```

using the repaired pipeline snapshot.

No model call.

For each report:

```text
fundamental directional sufficiency
price-timing readiness
full end-to-end holdout readiness
packet created
packet hash
failure reason
provider provenance
```

Do not collapse the three readiness states into one boolean if the gate audit proves they are semantically distinct.

---

# 26. Select US4 deterministically

Final US4 selection must remain:

```text
first four FULL_END_TO_END_HOLDOUT_READY issuers
in original ranks 1–5
followed by the frozen expanded reserve order
```

If the canonical contract permits price-unavailable subjects as full proof subjects, use that contract consistently.

Do not change the rule after seeing which names pass.

Stop candidate evaluation once four eligible US issuers are obtained.

No model call yet.

---

# 27. If fewer than US4 remain

If bounded provider/gate/universe remediation still yields:

```text
US full-ready count < 4
```

then:

```text
STOP PRE-MODEL
```

Report the dominant blocker:

```text
US_PRICE_PROVIDER_COVERAGE_BLOCKED
US_SECURITY_UNIVERSE_BLOCKED
US_PRICE_GATE_POLICY_BLOCKED
US_GENERAL_SOURCE_COVERAGE_BLOCKED
```

Do not rerun KR diagnostic.

Do not relax standards.

---

# 28. KR preservation and fresh combined generation

If US4 is obtained:

Use the preserved KR12:

```text
142210
060900
002680
035420
216050
100700
001530
487580
038870
342870
060230
415380
```

Then create a **fresh combined 16-issuer source generation**.

This is final source-freeze validation, not a rerun of KR discovery.

If a KR issuer fails because source state materially changed, use only the already precommitted historical KR reserve order and objective pre-model replacement.

No model call until US4 + KR12 are freshly source-ready and locked.

---

# 29. Final source lock

After fresh combined generation:

Produce:

```text
ordered issuer manifest
per-issuer packet hashes
source identity audit
source sufficiency/readiness audit
new aggregate source lock
new-holdout-precommit.json
```

Precommit must contain:

```text
US4
KR12
context grouping
source generation ID
source lock
packet hashes

prompt/schema identities
model
reasoning effort
timeout
timeout owner count
batch semantics
transport topology

per-context evidence preservation
per-context semantic audits
FIRST/A/B/C stop rules
```

After precommit:

```text
cohort mutation = 0
source mutation = 0
context grouping mutation = 0
```

---

# 30. Freeze gate

Before real model call:

```text
all final issuers absent from prior-real exposure registry

fundamental source readiness = PASS
required full-pipeline readiness = PASS under frozen contract
identity = PASS

architecture semantic drift = 0
prompt semantic drift = 0
schema semantic drift = 0
model semantic input drift = 0
transport topology mutation = 0

model = gpt-5.6-sol
reasoning_effort = xhigh
batch semantics = MODEL_CONTEXT_COUPLED
shared context size = 4
timeout = 1800
timeout owner count = 1
```

Required:

```text
REAL_HOLDOUT_MODEL_CALLS_BEFORE_FINAL_FREEZE = 0
```

---

# 31. Real proof execution

Only after the freeze gate:

```text
FIRST
→ FIRST ownership/renderer/hard-safety gates
→ A
→ A gates
→ B
→ B gates
→ C
→ C gates
```

At the first hard failure:

```text
STOP
```

No later run.

No automatic retry.

No selective continuation.

No timeout increase.

---

# 32. Per-context evidence preservation

After each successful context, before the next:

```text
persist exact raw output
stdout
stderr/log or safe redacted derivative
transport receipt
exact prompt
exact schema
subject mapping

hash all artifacts
secret scan
reopen verification
```

If preservation fails:

```text
STOP
```

Successful output still counts as holdout exposure.

---

# 33. Per-context Directional Core audit

After each successful Directional shared context:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
```

If hard violation:

```text
STOP
REVEALED_FOR_ARCHITECTURE_TUNING
RETIRED_FOR_ARCHITECTURE_REPAIR
```

No same-cohort hotfix.

---

# 34. FIRST run-level hard gates

Before A:

```text
first_ownership_gate_status = PASS
first_renderer_gate_status = PASS
first_hard_safety_gate_status = PASS
```

Required invariants remain:

```text
TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0

PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0

PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0

KNOWN_HARD_SAFETY_REGRESSION = 0
```

along with the Directional invariants above.

---

# 35. Historical stall handling

If a materially similar silent 1,800-second stall recurs:

```text
HISTORICAL_STALL_PATTERN_RECURRED = 1
```

Preserve diagnostics.

Retry:

```text
0
```

Next scope:

```text
BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR
```

Do not call the prior historical stall "fixed."

---

# 36. Stability/generalization

Use only valid completed FIRST/A/B/C runs that passed their own gates.

Directional Core and Price-Timing stability:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

using existing canonical thresholds.

If insufficient completed valid runs:

```text
NOT_MEASURED
```

---

# 37. Production no-change

Required:

```text
main_merge = 0
production_db_mutation = 0
production_scheduler_change = 0
production_telegram_send = 0
monitoring_registration_calls = 0
live_structured_autonomy_activation = 0
live_v2_change = 0
night_futures_code_mutation = 0
night_futures_decision_packet_injection = 0
```

Do not alter existing US/KR daily monitoring production behavior.

---

# 38. Monitoring Bootstrap remains out of scope

Only after full proof success:

```text
readiness =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW

next_scope =
Monitoring Bootstrap Integration Review
```

Do not start bootstrap here.

---

# 39. Required root-cause/remediation artifacts

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-current-us-readiness-baseline

04-price-context-gate-contract-audit
05-price-context-gate-classification
06-price-context-gate-remediation-decision
07-price-context-gate-tests-if-any

08-brkb-price-context-forensic
09-brkb-price-remediation-decision
10-brkb-price-remediation-diff-if-any

11-wmt-price-provider-resilience-audit
12-wmt-price-fallback-decision
13-wmt-price-remediation-diff-if-any

14-us-supported-universe-funnel
15-us-supported-universe-root-cause
16-expanded-canonical-us-universe
17-expanded-us-reserve-policy-v2
18-expanded-us-reserve-manifest-v2

19-us-original-five-readiness-reevaluation
20-us-expanded-reserve-coverage-audit
21-final-us-target-decision

22-kr-pass-preservation
```

---

# 40. Required proof-resume artifacts if US4 succeeds

Additionally:

```text
23-final-us4-selection
24-final-kr12-selection
25-fresh-combined-source-generation
26-combined-source-readiness-audit
27-combined-source-identity-audit
28-new-source-lock
29-new-holdout-precommit

30-architecture-semantic-freeze
31-prompt-schema-freeze
32-model-context-freeze
33-transport-topology-freeze
34-holdout-unseen-gate
35-live-workload-coexistence-audit

36-first-execution-summary
37-first-context-artifact-manifest
38-first-context-partial-semantic-audits
39-first-ownership-gate
40-first-renderer-gate
41-first-hard-safety-gate

42-run-a-execution-summary
43-run-a-context-artifact-manifest
44-run-a-context-partial-semantic-audits
45-run-a-ownership-gate
46-run-a-renderer-gate
47-run-a-hard-safety-gate

48-run-b-execution-summary
49-run-b-context-artifact-manifest
50-run-b-context-partial-semantic-audits
51-run-b-ownership-gate
52-run-b-renderer-gate
53-run-b-hard-safety-gate

54-run-c-execution-summary
55-run-c-context-artifact-manifest
56-run-c-context-partial-semantic-audits
57-run-c-ownership-gate
58-run-c-renderer-gate
59-run-c-hard-safety-gate

60-holdout-exposure-retirement-state
61-core-stability
62-timing-stability
63-ownership-generalization
64-renderer-ownership-proof
65-hard-safety-regression
66-production-no-change
67-night-futures-no-change
68-monitoring-bootstrap-next-handoff
69-program-completion
```

If US4 remains blocked, later proof artifacts are:

```text
NOT_RUN
```

not fabricated.

---

# 41. Required program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

price_context_gate_classification
price_context_gate_repair_applied
source_sufficiency_policy_changed

brkb_price_context_root_cause
brkb_price_repair_applied

wmt_price_source_resilience
wmt_price_repair_applied

canonical_us_universe_pre_filter_count
canonical_us_universe_post_exposure_count
canonical_supported_unexposed_us_count_before
canonical_supported_unexposed_us_count_after

supported_universe_root_cause
supported_universe_expansion_applied

expanded_us_reserve_count
expanded_us_reserve_policy_hash

us_original_five_full_ready_count
us_extended_reserve_attempt_count
us_full_ready_count
us_source_target_status

kr_historical_target_status
kr_diagnostic_rerun_count

final_us4
final_kr12
fresh_combined_source_generation_id
fresh_combined_source_lock

real_holdout_model_calls_before_final_freeze

model
reasoning_effort
model_timeout_seconds
model_timeout_owner_count
batch_semantics
shared_context_subject_count

architecture_semantic_drift
prompt_semantic_drift
schema_semantic_drift
model_semantic_input_drift
transport_topology_mutation
timeout_increase_this_task

holdout_output_exposure_state
holdout_semantic_revelation_state
holdout_retirement_state

real_holdout_model_invocation_count
real_holdout_subject_output_count

context_evidence_preservation_failure_count
per_context_semantic_failure_count
transport_timeout_count
transport_retry_count
historical_stall_pattern_recurred

run_results.first
run_results.a
run_results.b
run_results.c

first_ownership_gate_status
first_renderer_gate_status
first_hard_safety_gate_status

run_a_ownership_gate_status
run_a_renderer_gate_status
run_a_hard_safety_gate_status

run_b_ownership_gate_status
run_b_renderer_gate_status
run_b_hard_safety_gate_status

run_c_ownership_gate_status
run_c_renderer_gate_status
run_c_hard_safety_gate_status

ownership_generalization_verdict
ownership_proof_completion_state

ticker_specific_source_exception_count

main_merge
production_db_mutation
production_scheduler_change
production_telegram_send
monitoring_registration_calls
live_structured_autonomy_activation
live_v2_change
night_futures_code_mutation

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

readiness
stop_reason
next_scope
```

Unmeasured fields remain:

```text
NOT_MEASURED
```

---

# 42. Decision matrix

## Case A — gate is implementation overcoupling

If existing contracts already allow safe unavailable price/timing state:

```text
repair implementation generically
```

Do not change fundamental source-sufficiency policy.

Re-evaluate original five and reserves.

## Case B — gate is intentional

Preserve it.

Do not weaken it.

Solve US4 through valid price/provider coverage and expanded unseen universe.

## Case C — BRK-B generic share-class price alias bug

Repair generically.

No ticker exception.

## Case D — WMT provider outage with no canonical safe fallback

Leave WMT insufficient.

Use deterministic reserve.

## Case E — supported universe is artificially incomplete

Expand through canonical repository security master.

Freeze reserve ordering before source evaluation.

## Case F — supported universe is intentionally only five

Do not invent a new universe.

If price-ready US4 cannot be obtained:

```text
STOP
US_SECURITY_UNIVERSE_BLOCKED
```

Recommend a separately authorized security-universe capability expansion.

## Case G — US4 obtained

Build fresh US4 + KR12 source generation and resume FIRST/A/B/C.

## Case H — full ownership proof succeeds

Only then move to:

```text
Monitoring Bootstrap Integration Review
```

---

# 43. Artifact integrity

Final artifact index:

```text
relative path
SHA-256
byte size
artifact class
market
candidate/run/stage/context
secret-scan status
```

Required:

```text
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
artifact_secret_scan_failure_count = 0
```

Report final ZIP SHA-256.

---

# 44. Final task principle

The previous work solved the fundamental-family blocker enough to turn JPM into a valid candidate.

The remaining US problem is now visible:

```text
price readiness for WMT/BRK-B
+
no deterministic unseen reserve beyond the original five
```

Do not respond by weakening source sufficiency.

First determine whether price readiness is:

```text
a true full-pipeline requirement
or
an implementation overcoupling
```

Then diagnose BRK-B's share-class price path and WMT's provider resilience.

In parallel, explain why the canonical unseen supported US universe contains only five names and expand it only through an existing canonical security master.

The desired end state is not:

```text
make WMT or BRK-B pass at any cost
```

It is:

```text
at least four deterministic unseen US issuers
that satisfy the frozen full-pipeline contract
without fabricated evidence
```

Then combine them with the already adequate KR12, freeze a new source lock, and finally measure the ownership architecture.

Measure the gate.

Measure the universe.

Repair only generic implementation gaps.

Then resume the proof.
