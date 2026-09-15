# Thesis Monitor — Bounded US Source Coverage Remediation & New Holdout Proof Resume

## 0. Task identity

Suggested work-instruction filename:

```text
20260907-bounded-us-source-coverage-remediation-and-holdout-proof-resume.md
```

Suggested result bundle:

```text
thesis-monitor-20260907-bounded-us-source-coverage-remediation-holdout-proof-resume-report.zip
```

This task follows the completed dual-market diagnostic.

The dual-market diagnostic succeeded at its intended purpose:

```text
US and KR were both diagnosed completely
```

and established:

```text
DUAL_MARKET_SOURCE_STATUS = US_FAIL_KR_PASS
```

The current task must therefore be **US-remediation-first**.

KR source diagnostics must not be repeated unnecessarily.

The task may resume the new 16-issuer ownership proof only after:

```text
US target = PASS
AND
fresh combined 16-issuer source generation = PASS
AND
all freeze gates = PASS
```

The task is NOT:

- a broad source-sufficiency relaxation task;
- a ticker-specific exception task;
- a model/prompt/architecture redesign;
- a transport redesign;
- a timeout-increase task;
- a production activation task;
- a Monitoring Bootstrap task.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof-report.zip
```

Verified local ZIP SHA-256:

```text
e3f25cd718b97a178f6490533cecb7bfd48453377a743d7329b6396b0fc280fa
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

The result contains:

```text
artifact_count = 124
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
artifact_secret_scan_failure_count = 0

full_tests = PASS
ruff = PASS
diff_check = PASS
```

Latest repository/result provenance:

```text
base_sha =
cdc48a903d86f208e7af71c08b56dbceaf83de89

work_instruction_commit =
c28e723bce23bde43458ac7444c53ee4e5526cd7

implementation_commit =
f3dbc139e5d5500194abfddba3dad9d5014135f6

final_head_sha =
f3dbc139e5d5500194abfddba3dad9d5014135f6

branch =
codex/20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof
```

Do not assume current HEAD is unchanged.

---

# 2. Latest measured market state

## 2.1 US

```text
target = 4
attempted = 5
source_sufficient = 2
source_insufficient = 3

pipeline_coverage_gap = 2
source_absence = 1
unknown_failure = 0

US_SOURCE_TARGET_STATUS = FAIL
```

Eligible US subjects:

```text
NVDA
MSFT
```

Their diagnostic packet hashes were:

```text
NVDA
3dd1d47d0c9f721f1d27ab974bb733dee668c374bd0cf054bcdbc71e8078c002

MSFT
b8d22c68e4a7ee8acecd98ef5df93e7d34cacf75c933d44635b085a241bae57d
```

These hashes are historical diagnostic facts.

They are not yet a final combined-holdout source lock.

## 2.2 KR

```text
target = 12
attempted = 13
source_sufficient = 12
source_insufficient = 1

pipeline_coverage_gap = 0
source_absence = 1
unknown_failure = 0

KR_SOURCE_TARGET_STATUS = PASS
```

The source-sufficient KR set is:

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

The single failed initial KR candidate was:

```text
094800 맵스리얼티
```

with:

```text
EARNINGS_CONTEXT_INSUFFICIENT
OFFICIAL_FINANCIAL_SOURCE_UNAVAILABLE
REQUIRED_FUNDAMENTAL_DOMAIN_INSUFFICIENT
```

and was replaced by the first deterministic reserve:

```text
415380 스튜디오삼익
```

Do not reopen KR normalization/source remediation based on this result.

KR coverage is currently adequate.

---

# 3. Exact US failures

## 3.1 JPM

```text
ticker = JPM
CIK = 0000019617

framework =
bank_or_insurer

profile = PASS
SEC companyfacts = PASS
earnings context = PASS
official financial = PASS

raw_required_domain_evidence_present = true

missing required family =
REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT

failure_class =
PIPELINE_COVERAGE_GAP

failure_reason_codes =
NORMALIZATION_OR_MAPPING_GAP
REQUIRED_FUNDAMENTAL_DOMAIN_INSUFFICIENT

assembler_or_normalization_gap_suspected = true
true_source_absence_suspected = false
```

## 3.2 BRK-B

```text
ticker = BRK-B
CIK = 0001067983

framework =
bank_or_insurer

profile = PASS
SEC companyfacts = PASS
earnings context = PASS
official financial = PASS

raw_required_domain_evidence_present = true

missing required family =
REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT

failure_class =
PIPELINE_COVERAGE_GAP

failure_reason_codes =
NORMALIZATION_OR_MAPPING_GAP
REQUIRED_FUNDAMENTAL_DOMAIN_INSUFFICIENT

assembler_or_normalization_gap_suspected = true
true_source_absence_suspected = false
```

JPM and BRK-B share the same canonical missing-family signature.

This is evidence of a potentially generic US `bank_or_insurer` normalization/sector-family coverage gap.

Do not implement ticker-specific JPM or BRK-B exceptions.

## 3.3 WMT

```text
ticker = WMT
CIK = 0000104169

framework =
standard_operating_company

profile = PASS
SEC companyfacts = PASS
earnings context = PASS
official financial = PASS

base identity = success
base OHLCV = success

technical_context = UNAVAILABLE
current_price_unavailable
price_as_of_unavailable

failure_class =
SOURCE_ABSENCE

failure_domains =
PRICE_CONTEXT

failure_reason_codes =
SOURCE_FETCH_SUCCEEDED_PACKET_ASSEMBLY_FAILED
VALIDATION_FAILURE

source_pipeline_status =
SECURITY_OR_ACCOUNTING_BASIS_BLOCK
```

The combination:

```text
base OHLCV = success
but current price / price_as_of / safe technical context = unavailable
```

must be forensically explained before any WMT-specific source remediation.

Do not assume that successful OHLCV automatically authorizes deriving a current price from the last bar.

Use only an already-canonical supported path if one exists.

---

# 4. Current experiment state

Because US failed before final freeze:

```text
new_holdout_cohort = []
new_source_generation_id = NOT_CREATED
new_source_lock = NOT_CREATED

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

Therefore no new real issuer was model-exposed by the dual-market task.

The existing candidate-selection process remains pre-model.

---

# 5. Prior-real-issuer exclusion state

Latest dual-market result recorded:

```text
prior_real_issuer_exposure_registry_count = 61
new_holdout_exclusion_count = 70
```

Preserve the exact exclusion registry from the latest result unless new historical evidence proves an omission.

Do not shrink the exclusion set.

Previously retired and consumed issuers remain forbidden as unseen proof subjects.

---

# 6. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare current code with the latest result implementation state.

If unexplained semantic drift exists in:

```text
Directional Core
Price-Timing
renderer/action ownership
DecisionEvidencePacket
source-sufficiency semantics
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

# 7. Work-instruction commit first

Commit this instruction before source-pipeline remediation.

Record:

```text
new_work_instruction_commit
```

Only then modify implementation.

---

# 8. Allowed mutation surface

Allowed only where root-cause evidence supports it:

```text
US official-source normalization/mapping coverage
US bank_or_insurer sector/regulatory-family mapping
US price-context assembly or safe provider propagation
experiment-only US reserve-selection tooling
tests and fixtures for the above
source-coverage report tooling
existing experiment evidence preservation tooling
```

Strong preference:

```text
generic semantic mapping
not ticker-specific exception
```

No change to investment decision ownership semantics.

---

# 9. Forbidden changes

Do not change:

```text
Directional Core ownership
Price-Timing ownership
renderer/action ownership

BUY/HOLD/SELL thresholds
BUY:SELL balance semantics
HOLD lean semantics
new-buyer or holder transition semantics

source-sufficiency required families
merely to make candidates pass

DecisionEvidencePacket meaning
production market enum

accounting attribution safety
numeric provenance safety
ADR/security-basis safety
official provisional earnings safety

model
reasoning effort

ContinuationTransportAdapter canonical contract
transport topology
timeout ownership
timeout value

production DB
production scheduler
production Telegram
monitoring registration
live V2/Structured Autonomy
Night Futures
```

Do not weaken:

```text
REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT
```

into an empty or identity-only family.

Do not declare WMT price context safe without a canonical price basis.

---

# 10. Phase A — JPM/BRK-B generic root-cause proof

Before code changes, inspect the exact supported SEC source payloads used by the latest source diagnostic.

For both JPM and BRK-B identify:

```text
which raw source concepts triggered
raw_required_domain_evidence_present = true

concept/tag identity
taxonomy
period
value type
filing provenance
whether standard or custom tag
current-period suitability
```

Then inspect current canonical mapping logic and explain why those concepts did not satisfy:

```text
REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT
```

Required classification:

```text
US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED
```

or:

```text
US_BANK_INSURER_MAPPING_ROOT_CAUSE_NOT_CONFIRMED
```

If not confirmed:

```text
do not patch mapping
```

Proceed to deterministic reserve expansion instead.

---

# 11. Framework classification audit

Because both JPM and BRK-B currently route to:

```text
bank_or_insurer
```

validate independently whether the framework classification is correct under the current canonical classification rules.

Required fields:

```text
ticker
canonical framework
classification evidence
classification rule
classification correct = 0/1/UNKNOWN
```

Do not change framework classification solely to avoid a missing-family gate.

If framework classification is wrong for a general class of issuers:

```text
STOP
```

unless the correction is clearly generic, bounded, and covered by existing semantic taxonomy.

Do not add a BRK-B-only framework override.

---

# 12. Generic mapping repair rule

A source mapping may be added only if all are true:

```text
raw official evidence is actually present
semantic meaning matches the canonical required family
period/currentness is compatible
provenance is preserved
mapping is generic across the appropriate issuer/framework class
tests prove no unrelated family contamination
```

For bank/insurer coverage, prefer:

```text
REGULATORY_CAPITAL_CURRENT
```

when true regulatory-capital evidence exists.

Otherwise:

```text
SECTOR_OPERATING_CURRENT
```

may satisfy the `OR` family only when the mapped metric is a legitimate current sector-operating measure under existing semantics.

Do not map ordinary revenue/net income merely to satisfy a sector-specific family.

Do not infer values from unrelated totals.

---

# 13. JPM/BRK-B remediation tests

If a generic mapping repair is justified:

Add tests covering:

```text
positive JPM-like bank fixture
positive BRK-B-like insurer fixture
negative standard operating company fixture
stale-period rejection
wrong-taxonomy rejection if applicable
missing-provenance rejection
```

Prefer fictional/minimal fixtures for regression tests.

Do not make production logic depend on ticker strings.

Required:

```text
ticker_specific_source_exception_count = 0
```

---

# 14. Phase B — WMT price-context forensic

Before changing price-context behavior, prove the exact path behind:

```text
base OHLCV = success
technical_context = UNAVAILABLE
current_price_unavailable
price_as_of_unavailable
```

Inspect:

```text
symbol normalization
security identity
provider result
raw/latest available bar
price date
market session freshness
security/accounting basis validator
technical-context validator
current-price propagation
packet assembler
```

Classify:

```text
WMT_PRICE_CONTEXT_ROOT_CAUSE =
PROVIDER_SOURCE_ABSENCE /
SYMBOL_NORMALIZATION_GAP /
SAFE_PRICE_PROPAGATION_GAP /
SECURITY_BASIS_BLOCK /
STALE_OR_INSUFFICIENT_OHLCV /
OTHER_CONFIRMED /
UNRESOLVED
```

Do not guess.

---

# 15. WMT remediation rule

If the root cause is a generic pipeline bug and repair can be made without weakening price safety:

```text
repair generically
```

Examples of potentially acceptable repair classes only if already compatible with canonical semantics:

```text
correct supported symbol normalization
correct dropped current-price field propagation
correct safe latest-price extraction already used elsewhere
correct false security-basis mismatch
```

Do not create a new economic assumption.

Do not fabricate current price from stale or insufficient bars.

If the source is genuinely unavailable:

```text
leave WMT insufficient
```

and use a precommitted deterministic reserve instead.

---

# 16. Phase C — Precommit expanded US reserve policy

Before re-evaluating any new US candidate beyond the original five, create:

```text
expanded-us-reserve-policy.json
```

Use the same selection salt/rule lineage as the previous policy:

```text
20260907-new-issuer-holdout-selection-ownership-proof-v1
```

and the existing supported-security universe/exclusion registry.

The extension must be deterministic and outcome-independent.

Exclude:

```text
NVDA
JPM
WMT
BRK-B
MSFT
```

from the newly generated reserve extension because they already occupy ranks 1-5.

Generate a bounded additional reserve sequence before any new candidate source evaluation.

Recommended additional reserve budget:

```text
at least 8
at most 20
```

unless the existing canonical selector defines another bounded amount.

Record:

```text
reserve_extension_count
reserve_order
selection rule hash
exclusion registry hash
```

Do not choose reserves manually based on expected source quality.

---

# 17. Preserve original candidate order

The original US order remains historically:

```text
1 NVDA
2 JPM
3 WMT
4 BRK-B
5 MSFT
```

After remediation, re-evaluate these candidates under the repaired generic pipeline.

Final US selection rule:

```text
first four source-sufficient unique issuers
in original ranks 1-5 followed by
the newly precommitted deterministic reserve extension
```

This preserves outcome-independent ordering.

Do not move MSFT ahead of earlier candidates merely because it already passed.

---

# 18. Re-evaluate original US five

After bounded remediation:

Evaluate:

```text
NVDA
JPM
WMT
BRK-B
MSFT
```

under the same current pipeline snapshot.

No model call.

For each report:

```text
pre-remediation status
post-remediation status
changed reason
source provenance
source family coverage
packet status
packet hash
price status
validation errors
```

Required classification per failed-to-pass transition:

```text
GENERIC_REPAIR_RESOLVED
STILL_TRUE_SOURCE_ABSENCE
STILL_PIPELINE_COVERAGE_GAP
NEW_VALIDATION_FAILURE
```

---

# 19. Use deterministic extended reserves only if needed

If fewer than four of the original five are source-sufficient:

Evaluate the precommitted extended reserves in order.

Stop source evaluation when:

```text
four US source-sufficient issuers obtained
```

or:

```text
bounded reserve extension exhausted
```

No model call.

Do not evaluate extra issuers after the US target has been reached merely to cherry-pick a preferred cohort.

---

# 20. US remediation success gate

Required:

```text
US_SOURCE_TARGET_STATUS =
PASS
```

with:

```text
source_sufficient_us_count >= 4
```

If still fewer than four:

```text
STOP
```

No final holdout.

No model call.

Produce the next blocker classification.

---

# 21. KR preservation rule during US remediation

Do not rerun the complete KR source-coverage diagnostic while fixing US.

Historical KR target remains:

```text
PASS 12/12
```

Preserve the selected KR identities:

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

Preserve prior KR source-coverage evidence as historical diagnostic proof.

Only after US passes may the task build the final fresh combined source generation.

---

# 22. Fresh combined source generation after US PASS

After US source target is satisfied, create a **new combined 16-issuer source generation** using:

```text
final selected US4
+
preserved selected KR12
```

This is not a repeat of the KR diagnostic.

It is the source freeze for the actual ownership proof.

Use the frozen canonical source pipeline.

Produce:

```text
combined source generation ID
ordered issuer manifest
per-issuer packet hashes
identity audit
source-sufficiency audit
aggregate source lock
```

No model call yet.

---

# 23. Fresh combined-source failure handling

During final combined generation, any issuer may fail due to a genuinely changed source state.

## 23.1 US issuer fails

Use the already precommitted deterministic US reserve extension if objective replacement is necessary and still pre-model.

## 23.2 KR issuer fails

Use the existing frozen KR reserve order from the previous dual-market policy:

```text
036560
417790
246250
003920
007110
284740
475960
051500
003490
073560
044380
030960
118000
475560
484590
001720
151860
014160
071950
133750
307180
380540
080420
049070
002450
008370
031440
046890
005830
128820
054050
052220
001520
063440
023150
```

Note:

```text
415380
```

is already selected and must not be reused as reserve.

Replacement remains objective and pre-model only.

If the combined source generation cannot reach:

```text
US4 + KR12
```

stop before model execution.

---

# 24. Final source lock and precommit

If fresh combined source generation passes:

Create:

```text
new source lock
new-holdout-precommit.json
```

Include:

```text
ordered 16 issuers
US4/KR12 market mix
selection-policy hashes
prior-exposure-registry hash
per-issuer packet hashes
source generation ID
aggregate source lock

prompt/schema identities
model
reasoning effort
batch semantics
context grouping
timeout
timeout owner count
transport topology identity

per-context artifact preservation policy
per-context semantic-audit policy
FIRST/A/B/C stop rules
```

Once written:

```text
cohort mutation = 0
source mutation = 0
context grouping mutation = 0
```

---

# 25. Freeze gate before real model

Prove:

```text
all final issuers absent from prior-real-issuer exposure registry

source sufficiency = PASS
identity = PASS

architecture semantic drift = 0
prompt semantic drift = 0
schema semantic drift = 0
model semantic input drift = 0
transport topology mutation = 0

model = gpt-5.6-sol
reasoning_effort = xhigh
batch semantics = MODEL_CONTEXT_COUPLED
shared context subject count = 4
timeout = 1800
timeout owner count = 1
```

Do not increase timeout.

Do not rerun historical fictional transport probes if shared transport semantics remain unchanged.

---

# 26. Model execution permission

Real model execution is allowed only when:

```text
US_SOURCE_TARGET_STATUS = PASS
AND
FRESH_COMBINED_KR_TARGET_STATUS = PASS
AND
FINAL_SOURCE_LOCK_CREATED = 1
AND
PRECOMMIT_FREEZE = PASS
```

Required invariant:

```text
REAL_HOLDOUT_MODEL_CALLS_BEFORE_FINAL_FREEZE = 0
```

---

# 27. Per-context exact evidence preservation

After every successful context, before the next context:

```text
persist exact raw output
persist stdout
persist stderr/log or safe redacted derivative
persist transport receipt
persist exact prompt
persist exact schema
persist generation/run/stage/batch/subject mapping

compute SHA-256
compute byte size
secret scan
reopen verification
```

Required:

```text
CONTEXT_EVIDENCE_PRESERVATION = PASS
```

If preservation fails:

```text
STOP
```

Do not expose the next context.

---

# 28. Per-context Directional Core early gate

After every successful Directional Core shared context:

```text
schema validity

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
```

If hard semantic failure:

```text
STOP
```

Do not expose later contexts.

No same-cohort hotfix.

---

# 29. FIRST transport failure behavior

No:

```text
automatic retry
selective continuation
batch split
timeout increase
same-task transport repair
```

If failure occurs after partial output:

```text
holdout_output_exposure_state =
PARTIALLY_EXPOSED

holdout_retirement_state =
RETIRED_PARTIAL_EXPOSURE

future_unseen_holdout_reuse_allowed = 0
```

Do not retry the cohort.

If another silent 1,800-second stall materially matches the historical pattern:

```text
HISTORICAL_STALL_PATTERN_RECURRED = 1
```

Next scope:

```text
BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR
```

---

# 30. FIRST run-level gates

After complete FIRST and before A:

Required hard invariants:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0

PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0

KNOWN_HARD_SAFETY_REGRESSION = 0
```

Required:

```text
first_ownership_gate_status = PASS
first_renderer_gate_status = PASS
first_hard_safety_gate_status = PASS
```

Only then run A.

---

# 31. A / B / C

Run:

```text
FIRST
→ gates
→ A
→ gates
→ B
→ gates
→ C
→ gates
```

At the first hard execution/semantic/renderer/safety failure:

```text
STOP
```

No later run.

Per-context evidence preservation and early Directional audit remain active in A/B/C.

---

# 32. Stability/generalization

Use only valid completed runs that passed their own hard gates.

Directional Core:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Price-Timing:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Do not redefine thresholds after outputs.

If insufficient valid repeated runs:

```text
NOT_MEASURED
```

---

# 33. Production no-change

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

This task must not alter the existing US/KR daily monitoring production behavior.

---

# 34. Monitoring Bootstrap remains out of scope

Only after complete ownership proof success may:

```text
next_scope =
Monitoring Bootstrap Integration Review
```

Do not implement Monitoring Bootstrap here.

---

# 35. Required remediation artifacts

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-current-us-failure-baseline

04-jpm-raw-sector-evidence
05-brkb-raw-sector-evidence
06-us-bank-insurer-framework-classification-audit
07-us-bank-insurer-mapping-root-cause
08-us-bank-insurer-remediation-diff
09-us-bank-insurer-remediation-tests

10-wmt-price-context-forensic
11-wmt-price-remediation-decision
12-wmt-price-remediation-diff-if-any

13-expanded-us-reserve-policy
14-expanded-us-reserve-manifest

15-us-post-remediation-coverage-audit
16-us-post-remediation-failure-detail
17-us-target-decision

18-kr-pass-preservation
```

---

# 36. Required proof-resume artifacts if US passes

If US passes, additionally produce:

```text
19-final-us4-selection
20-final-kr12-selection
21-fresh-combined-source-generation
22-combined-source-sufficiency-audit
23-combined-source-identity-audit
24-new-source-lock
25-new-holdout-precommit

26-architecture-semantic-freeze
27-prompt-schema-freeze
28-model-context-freeze
29-transport-topology-freeze
30-holdout-unseen-gate
31-live-workload-coexistence-audit

32-first-execution-summary
33-first-context-artifact-manifest
34-first-context-partial-semantic-audits
35-first-ownership-gate
36-first-renderer-gate
37-first-hard-safety-gate

38-run-a-execution-summary
39-run-a-context-artifact-manifest
40-run-a-context-partial-semantic-audits
41-run-a-ownership-gate
42-run-a-renderer-gate
43-run-a-hard-safety-gate

44-run-b-execution-summary
45-run-b-context-artifact-manifest
46-run-b-context-partial-semantic-audits
47-run-b-ownership-gate
48-run-b-renderer-gate
49-run-b-hard-safety-gate

50-run-c-execution-summary
51-run-c-context-artifact-manifest
52-run-c-context-partial-semantic-audits
53-run-c-ownership-gate
54-run-c-renderer-gate
55-run-c-hard-safety-gate

56-holdout-exposure-retirement-state
57-core-stability
58-timing-stability
59-ownership-generalization
60-renderer-ownership-proof
61-hard-safety-regression
62-production-no-change
63-night-futures-no-change
64-monitoring-bootstrap-next-handoff
65-program-completion
```

If US remains blocked, all proof-resume artifacts must be marked:

```text
NOT_RUN
```

not fabricated.

---

# 37. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

jpm_framework_classification_status
brkb_framework_classification_status

jpm_mapping_root_cause
brkb_mapping_root_cause

generic_us_bank_insurer_mapping_repair_applied
ticker_specific_source_exception_count

wmt_price_context_root_cause
wmt_price_repair_applied

expanded_us_reserve_policy_hash
expanded_us_reserve_count

us_original_five_attempted
us_original_five_post_repair_pass_count
us_extended_reserve_attempt_count
us_source_sufficient_count
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

Anything not measured:

```text
NOT_MEASURED
```

---

# 38. Decision matrix

## A. Generic bank/insurer mapping repair gives enough US coverage

If:

```text
US source-sufficient >= 4
```

proceed to fresh combined source generation and ownership proof.

WMT does not need to be forced through if four earlier/precommitted candidates satisfy the target.

## B. Mapping repair insufficient, deterministic reserves fill target

Proceed to combined source generation.

This is valid because reserve order was frozen before evaluation.

## C. US remains below four

Stop pre-model.

Classify whether remaining blockers are:

```text
US_BANK_INSURER_MAPPING_UNRESOLVED
US_PRICE_SOURCE_COVERAGE_BLOCKED
US_GENERAL_SOURCE_COVERAGE_BLOCKED
```

Do not rerun KR diagnostics.

## D. Combined fresh source generation fails on KR

Use only the prior precommitted KR reserve order and objective pre-model replacement.

If KR12 cannot be restored:

```text
STOP
NOT_READY_KR_SOURCE_REFRESH_BLOCKED
```

## E. Full proof succeeds

Only then:

```text
readiness =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW

next_scope =
Monitoring Bootstrap Integration Review
```

---

# 39. Artifact integrity

Final artifact index must include:

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

Report final result ZIP SHA-256.

---

# 40. Final task principle

The dual-market diagnostic has already answered the market question:

```text
KR coverage is adequate.
US coverage is the blocker.
```

The US failure is not one monolithic problem.

It is currently:

```text
2 generic-looking sector-family mapping gaps
+
1 price-context/source gap
```

Therefore the correct next sequence is:

```text
prove root cause
→ repair only generic supported gaps
→ precommit deterministic extra reserves
→ obtain US4 without weakening source sufficiency
→ build fresh US4 + KR12 source lock
→ run frozen ownership proof
```

Not:

```text
relax source sufficiency
```

Not:

```text
hardcode JPM / BRK-B / WMT exceptions
```

Not:

```text
rerun KR diagnostics every time US changes
```

And not:

```text
call the model before both markets are source-sufficient and source-locked
```

Fix coverage generically.

Then measure the frozen investment architecture.
