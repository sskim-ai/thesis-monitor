# Thesis Monitor — Bounded Semantic Single-Source Convergence Repair

## 0. Task identity

Suggested work-instruction filename:

```text
20260914-bounded-semantic-single-source-convergence-repair.md
```

Suggested result bundle:

```text
thesis-monitor-20260914-bounded-semantic-single-source-convergence-repair-report.zip
```

Master-workflow phase:

```text
M12BI — Fresh / Monitored Semantic Single-Source Convergence Repair
         A. Freeze M12BH audit evidence
         B. Route the active fresh/new-issuer post-model core path through canonical semantic services
         C. Preserve fresh-specific ownership/domain/unknown checks only as additive thin-adapter checks
         D. Remove proof-critical ticker-specific duplicate hard semantics
         E. Seal/remove independently re-derived BusinessDelta fallback on proof-critical paths
         F. Route fresh proof readiness through canonical finalization readiness policy
         G. Re-run the unchanged 40-case cross-path golden corpus
         H. Offline re-audit existing frozen fresh/new-issuer outputs under canonical services
         I. Offline re-audit M12BD fictional proof under the converged semantic orchestrator
         J. STOP after deterministic convergence proof; no model calls and no shadow in this task
```

This task is the direct result of M12BH.

The user suspected that semantic work previously completed for fresh/new issuers
was not actually shared by the monitored/shadow path.

M12BH proved the inverse architectural fact:

```text
the monitored/shadow path is already using the current canonical services,

while the active fresh/new-issuer post-model proof path bypasses many of them.
```

Therefore repeated semantic repairs happened because two proof-critical paths
did not share one semantic source of truth.

M12BI must fix THAT architecture.

Do NOT add another phrase-level regex unless the canonical service itself
fails an existing deterministic corpus case.

Do NOT run model calls in M12BI.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260914-fresh-vs-monitored-semantic-single-source-convergence-audit-conditional-full-shadow-report.zip
```

Verified SHA-256:

```text
de08d844d261e3ddab98e24aa5f34e038729909d894dabd624a005d90d3f9655
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
artifact_count = 73

ZIP entries =
73 indexed payloads
+ artifact-index.json
= 74

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12BH authoritative convergence decision

M12BH:

```text
semantic_convergence_audit_status =
CONVERGENCE_DEBT_PRESENT

decision =
STOP_BEFORE_SHADOW

next_scope =
BOUNDED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_REPAIR
```

No network gate ran.

No model call ran.

No shadow generation ran.

This was correct.

---

# 3. M12BH quantitative findings

Reported:

```text
semantic_contract_family_count = 13

canonical_shared_service_count = 23

thin_adapter_count = 33

canonical_bypass_count = 10

proof_critical_bypass_count = 10

legacy_duplicate_divergent_count = 2

legacy_duplicate_equivalent_count = 1

proof_critical_duplicate_semantic_engine_count = 3

golden_corpus_case_count = 40

canonical_fixture_pass_count = 40

golden_corpus_cross_path_divergence_count = 40
```

Important:

```text
canonical_fixture_failure_count = 0
```

The canonical semantic services themselves passed the corpus.

The divergence is a CONSUMER COVERAGE problem,
not evidence that the canonical services are wrong.

---

# 4. Fresh/new-issuer active entrypoints

M12BH mapped:

```text
new_issuer_final_freeze_ownership_proof.execute

new_issuer_holdout_selection_ownership_proof.execute

new_issuer_holdout_selection_ownership_proof.execute_run

fresh_issuer_ownership_proof_transport_risk_carried.execute
```

Latest core post-model validator:

```text
new_issuer_holdout_selection_ownership_proof.core_partial_audit
```

Current fresh post-model audit checks only a subset such as:

```text
evidence domains

reference identity

material anchor/domain ownership

unknown treatment.
```

It does NOT call the full canonical semantic stack.

This is the primary convergence defect.

---

# 5. Monitored/shadow canonical path

M12BH mapped monitored monolithic / Stage-1 through:

```text
business_delta_evidence_capability_m12ai

→ main_integration_two_stage_directional_m12ae_r2_runtime

→ directional_financial_context_m12g._audit_core_batch_with_grounding

→ directional_financial_context_m12._audit_core_batch
```

Canonical services include:

```text
validate_directional_financial_semantics

validate_qtd_ytd_conflict_semantics

validate_business_delta_candidate

validate_market_expectation_candidate

validate_working_capital_checkpoint_bindings

validate_configured_signal_field_ownership
```

plus canonical evidence-view builders.

M12BI should converge the fresh post-model path TO this semantic service layer.

Do not copy M12 script regexes into fresh code.

---

# 6. Canonical semantic families blocked by the fresh bypass

M12BH found the fresh path bypasses proof-critical canonical semantics for:

```text
financial temporal role

FCF identity/currentness

net-debt temporal completeness

working-capital typed grounding

financial-sector framework semantics

configured-signal lifecycle

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

QTD/YTD period semantics

proof/finalizer hard-semantic vs diagnostic readiness policy.
```

These ten families must no longer be silently skipped by the active fresh path.

---

# 7. Canonical ownership map — preserve

Use the canonical modules already identified by M12BH.

## Financial temporal / FCF / net debt

```text
app/services/directional_financial_context_service.py
```

Canonical functions include:

```text
financial_claim_role

financial_claim_requires_current_evidence

current_fulfillment_polarity

fcf_temporal_claim_spans

fcf_temporal_claim_role

classify_ppe_proxy_fcf_claims

validate_directional_financial_semantics.
```

## Working capital

```text
app/services/working_capital_checkpoint_binding_service.py
```

Canonical:

```text
build_working_capital_checkpoint_binding_view

validate_working_capital_checkpoint_bindings.
```

## Financial-sector framework

```text
app/services/financial_framework_claim_service.py
```

Canonical:

```text
candidate_financial_framework_claims

framework_reference_is_application.
```

## Configured signals

```text
app/services/configured_signal_evidence_service.py
```

Canonical:

```text
build_configured_signal_evidence_view

validate_configured_signal_field_ownership.
```

## Business delta

```text
app/services/business_delta_evidence_service.py
```

Canonical:

```text
build_business_delta_evidence_view

validate_business_delta_candidate.
```

## Market expectations

```text
app/services/market_expectation_evidence_service.py
```

Canonical:

```text
build_market_expectation_evidence_view

validate_market_expectation_candidate.
```

## Finalization readiness

```text
scripts/finalization_readiness_policy.py
```

Canonical:

```text
evaluate_finalization_readiness.
```

Do not create second implementations of these semantics.

---

# 8. Preferred architecture: one reusable canonical core semantic orchestrator

Create or extract one reusable orchestration layer such as:

```text
app/services/directional_core_semantic_audit_service.py
```

or an equivalent repository-appropriate module.

Purpose:

```text
given:
- canonical/owned evidence context
- candidate core
- applicable semantic views
- lifecycle applicability metadata

return:
one canonical hard-semantic audit result
```

It should orchestrate existing services.

It must NOT reimplement their semantics.

Suggested result contract:

```text
DirectionalCoreSemanticAudit
```

with fields such as:

```text
financial_semantics

qtd_ytd_semantics

configured_signal_semantics

working_capital_semantics

business_delta_semantics

market_expectation_semantics

financial_sector_claim_semantics

hard_errors

status

semantic_service_versions / identities.
```

Exact shape may follow repository conventions.

---

# 9. Orchestrator must be semantic-only, not fresh-specific

Do NOT name the canonical service:

```text
fresh_semantic_audit
```

or:

```text
monitored_semantic_audit.
```

It must serve both.

Desired consumers:

```text
fresh/new-issuer post-model path

monitored monolithic audit

monitored Stage-1 audit

shadow audit

offline replay / proof harness.
```

Migration may happen incrementally,
but the service itself must not encode path-specific meaning.

---

# 10. Thin path adapters are allowed

Different paths may have different packet/container types.

Allowed:

```text
fresh packet → canonical semantic audit input adapter

monitored packet → canonical semantic audit input adapter.
```

The adapter may map:

```text
field names

alias catalog

owned evidence container

lifecycle mode

applicable field paths

report formatting.
```

The adapter may NOT re-derive:

```text
temporal role

FCF identity

net-debt completeness

WC grounding validity

configured-signal fulfillment

business-delta eligibility/direction

expectation independence

financial-sector framework application.
```

---

# 11. Fresh evidence adapter contract

Audit actual fresh input structures before implementation.

Build a deterministic adapter from:

```text
new_issuer_holdout_selection_ownership_proof.load_inputs
```

and the frozen fresh candidate/evidence artifacts
into the canonical service input shapes.

Required:

```text
every candidate evidence ref resolves to the same evidence identity

no synthetic evidence values

no provider fetch

no inferred FCF/net-debt/WC values

no post-hoc candidate mutation.
```

If a canonical service requires a concept the fresh packet truly does not own:

```text
return explicit NOT_APPLICABLE / empty canonical view
according to that service's lifecycle contract.
```

Do NOT silently skip the service.

---

# 12. Lifecycle applicability must be explicit

Fresh/new issuer and monitored issuer do not have identical lifecycle state.

Examples:

```text
fresh issuer may have no stored configured signals

fresh initial analysis may not have a monitored baseline

fresh path may lack a historical thesis delta baseline.
```

M12BI must create an explicit applicability matrix.

For each semantic family:

```text
APPLICABLE

NOT_APPLICABLE_BY_LIFECYCLE

APPLICABLE_WITH_EMPTY_VIEW

UNSUPPORTED_INPUT_ERROR.
```

Do not equate:

```text
not applicable
```

with:

```text
validator omitted.
```

---

# 13. Fresh configured-signal behavior

If fresh/new issuer has no configured monitoring signals:

```text
ConfiguredSignalEvidenceView
must be an explicit empty / not-applicable canonical result.
```

Expected:

```text
no current-driver violation

no false fulfillment

no synthetic configured signal.
```

If the fresh proof fixture intentionally contains configured signals:

```text
use the canonical configured-signal service.
```

Never infer lifecycle from free text.

---

# 14. Fresh BusinessDelta behavior

Do NOT blindly impose monitored daily-delta semantics on a true Initial Analysis lifecycle.

First inspect the actual fresh core schema and proof semantics.

Required decision:

```text
if business_thesis_change field exists and is decision-active:
    route it through BusinessDeltaEvidenceView with explicit lifecycle mode

elif field is not applicable for Initial Analysis:
    mark NOT_APPLICABLE_BY_LIFECYCLE and prove it cannot affect readiness

else:
    STOP
    FRESH_BUSINESS_DELTA_LIFECYCLE_CONTRACT_AMBIGUOUS.
```

Do not silently bypass.

Do not create fake baseline evidence.

---

# 15. Fresh MarketExpectation behavior

If fresh candidates contain market-expectation context:

```text
build MarketExpectationEvidenceView
and validate independence/material-anchor eligibility canonically.
```

Expected:

```text
context-only expectation
does not become independent material anchor.
```

No fresh-specific alternative expectation semantics.

---

# 16. Fresh working-capital grounding

If selected typed WC evidence exists and a fresh candidate claims:

```text
inventory

receivables

payables

generic working capital
```

in a checkpoint field owned by that schema:

```text
use the same canonical claim-local typed grounding validator.
```

No candidate-global grounding.

No narrative-only substitution.

No automatic direction.

---

# 17. Fresh financial semantics

Fresh path must consume canonical:

```text
financial temporal role

FCF current/prospective semantics

FCF requirement semantics

PPE-proxy semantics

net-debt completeness

financial-sector framework semantics

QTD/YTD conflict semantics.
```

No partial replacement based only on domain/ref/anchor checks.

---

# 18. Preserve fresh-specific ownership/domain checks

`core_partial_audit` may contain useful checks that are NOT duplicated canonical semantics:

```text
required evidence domain ownership

holdout selection ownership

unknown-treatment requirements

fresh-specific exposure / source constraints.
```

These may remain.

But refactor them as:

```text
fresh-specific additive audit
```

after/beside the canonical semantic audit.

Final fresh hard errors should be conceptually:

```text
canonical semantic hard errors

+

fresh-specific ownership/domain hard errors.
```

Do not let fresh-specific checks replace the canonical stack.

---

# 19. Replace fresh core_partial_audit semantics, not its useful interface necessarily

You may preserve the function name:

```text
core_partial_audit
```

for compatibility,
but its proof-critical semantic result must delegate to the canonical orchestrator.

Required audit field:

```text
canonical_semantic_audit_consumed = true.
```

If the name remains,
document that it is now:

```text
canonical semantic audit + fresh-specific partial ownership checks.
```

No hidden old semantics.

---

# 20. Fresh execute_run hard gate

`new_issuer_holdout_selection_ownership_proof.execute_run`
must hard-stop candidate acceptance on:

```text
canonical semantic audit hard failure
```

in addition to fresh-specific hard failures.

Do not merely write a report and continue.

This is proof-critical.

---

# 21. Fresh final-freeze path

`new_issuer_final_freeze_ownership_proof.execute`
delegates to the holdout run.

Require a provenance assertion:

```text
fresh final-freeze accepted core
was canonical-semantic-audited.
```

No bypass at final freeze.

If the final-freeze wrapper can load a preexisting candidate:

```text
verify the canonical semantic audit receipt/hash for that candidate.
```

Do not trust legacy fresh acceptance without audit identity.

---

# 22. Transport-risk-carried fresh path

Audit:

```text
fresh_issuer_ownership_proof_transport_risk_carried.execute
```

M12BH shows it delegates into the same fresh execute path.

Require:

```text
no independent semantic bypass.
```

Transport-only wrappers may carry audit receipts,
but may not reclassify semantics.

---

# 23. Proof duplicate #1: `_case_semantic_errors`

M12BH found:

```text
scripts/directional_financial_context_m12.py
_case_semantic_errors
```

classification:

```text
LEGACY_DUPLICATE_DIVERGENT
```

proof-critical.

It independently adds ticker-specific hard semantic errors.

M12BI must remove its role as an independent semantic engine.

Preferred:

```text
fixture-specific assertions inspect canonical audit outputs
and fixture identities

not raw candidate text to re-derive financial semantics.
```

---

# 24. `_case_semantic_errors` migration principle

A fictional fixture may assert:

```text
selected canonical typed evidence is used

expected semantic violation count is zero/nonzero

fixture-required evidence family is present

canonical audit role equals expected role.
```

It must NOT independently decide:

```text
FCF misuse

net-debt validity

WC validity

sector framework validity

temporal role
```

via raw text regex.

If a fixture's purpose is already fully covered by canonical validators:

```text
retire that duplicate assertion.
```

---

# 25. Proof duplicate #2: `_fic_fin_05_hard_errors`

M12BH found:

```text
scripts/boundary_band_application_scope_m12aa.py
_fic_fin_05_hard_errors
```

classification:

```text
LEGACY_DUPLICATE_DIVERGENT.
```

M12BI must replace its independent financial semantic decisions
with assertions over canonical audit results.

Do NOT preserve a special FIC-FIN-05 semantic engine.

Boundary fixture-specific decision diagnostics may remain,
but financial validity belongs to canonical services.

---

# 26. Proof helper `_framework_role_audit`

M12BH classified:

```text
_framework_role_audit
```

as:

```text
THIN_ADAPTER_TO_CANONICAL_SERVICE
```

because it delegates to:

```text
candidate_financial_framework_claims.
```

Preserve this pattern.

Use it as the model for acceptable proof adapters.

---

# 27. BusinessDelta legacy fallback

M12BH found:

```text
scripts/business_delta_alias_balance_confidence_m12z.py
business_delta_audit
```

contains an independently derived fallback
when a canonical view is not supplied.

Classification:

```text
LEGACY_DUPLICATE_EQUIVALENT

proof_critical = true

current_path_participation = false.
```

This is driftable convergence debt.

---

# 28. Seal/remove BusinessDelta fallback on proof-critical paths

Preferred:

```text
proof-critical business_delta_audit requires
BusinessDeltaEvidenceView / canonical owned input.
```

If missing:

```text
FAIL
CANONICAL_BUSINESS_DELTA_VIEW_REQUIRED.
```

Do not silently rederive from raw text.

If a legacy non-proof caller truly requires compatibility:

```text
isolate it behind an explicit NON_PROOF legacy compatibility path
with no use in readiness/shadow/fresh proof.
```

Required:

```text
proof_critical_fallback_participation_count = 0.
```

---

# 29. Proof readiness convergence

M12BH found the fresh completion uses separate run gates
instead of canonical:

```text
evaluate_finalization_readiness.
```

M12BI must converge semantic readiness.

Fresh proof may still own fresh-specific gates:

```text
transport success

holdout ownership

source completeness

artifact integrity.
```

But objective semantic readiness should consume
the same canonical hard-vs-diagnostic readiness policy.

---

# 30. Fresh readiness adapter

Build a thin adapter from fresh audit outputs to canonical readiness inputs.

It must preserve current policy:

```text
hard semantic failure → blocking

core mutation → blocking

invalid ref → blocking

runtime/schema failure → blocking

valid decision variance → diagnostic only.
```

Do not resurrect old exact-enum stability requirements.

---

# 31. Do not change model-facing prompts/schemas in M12BI

Target architecture:

```text
post-model semantic convergence only.
```

Expected:

```text
model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

Stage-1/Stage-2 monitored prompt change = 0

fresh model prompt change = 0

fresh model schema change = 0

final user schema change = 0.
```

If convergence requires model-facing changes:

```text
STOP
MODEL_FACING_CONVERGENCE_SCOPE_EXPANSION_REQUIRED.
```

Do not mix that into M12BI.

---

# 32. No model calls in M12BI

Required:

```text
fresh model calls = 0

fictional model calls = 0

shadow model calls = 0

network gate attempts = 0.
```

All proof is deterministic/offline.

This task must finish even if network is unavailable.

---

# 33. Re-run the exact unchanged 40-case golden corpus

Use the exact M12BH corpus.

Do not alter expected outcomes.

Required:

```text
case_count = 40

canonical fixture pass = 40

cross-path divergence = 0.
```

Every applicable path must consume canonical semantic identity.

For non-applicable lifecycle cases:

```text
explicit NOT_APPLICABLE result
```

must match the applicability matrix.

Do not count an intentional N/A as divergence.

---

# 34. Golden corpus must include service provenance

For every path/case report:

```text
case id

semantic family

applicability

canonical service module/function

adapter module/function

semantic service version/hash

result

hard errors

provenance status.
```

Required:

```text
proof_critical_legacy_duplicate_participation = false.
```

---

# 35. Fresh historical offline replay

Locate the latest COMPLETE fresh/new-issuer frozen proof artifacts
used by the active fresh entrypoint.

Do NOT make new model calls.

Replay its existing model outputs through:

```text
canonical semantic orchestrator

fresh-specific ownership/domain checks

canonical readiness policy.
```

Report:

```text
candidate count

previously accepted count

canonical semantic PASS count

canonical semantic FAIL count

fresh-specific hard fail count

readiness status.
```

Do not rewrite candidates.

---

# 36. Handling newly discovered fresh historical failures

If canonical convergence exposes a historical fresh candidate
that should have failed:

```text
do NOT weaken canonical services.
```

Record:

```text
historical_fresh_acceptance_regression_found = true
```

and classify exact root cause.

Because no production action is authorized,
the result is an audit finding.

Do not rerun models in M12BI.

---

# 37. M12BD fictional offline re-audit

Re-run the complete frozen M12BD formal proof
through the converged orchestrator.

Expected:

```text
Stage 1 = 24 / 24 PASS

Stage 2 = 24 / 24 PASS

final compositions = 24 / 24 PASS

aggregate finalization = PASS

hard semantic failures = 0

core mutation = 0.
```

If not:

```text
STOP
CANONICAL_ORCHESTRATOR_REGRESSION.
```

Do not weaken semantics.

---

# 38. Monitored/shadow regression

Existing monitored/shadow behavior should remain semantically identical.

Required:

```text
monolithic hard audit output equality = PASS

Stage-1 hard audit output equality = PASS

Stage-2 applicable audit equality = PASS

shadow canonical service identity unchanged.
```

No new wrapper semantics.

---

# 39. Canonical semantic call provenance

For each proof-critical consumer produce:

```text
consumer

semantic family

canonical service called?

thin adapter only?

independent semantic derivation present?

hard decision source.
```

Acceptance:

```text
fresh proof:
no bypass

monitored:
no bypass

shadow:
no bypass

offline replay:
no bypass.
```

---

# 40. Duplicate semantic engine acceptance

At M12BI completion require:

```text
legacy_duplicate_divergent_count = 0

proof_critical_bypass_count = 0

proof_critical_duplicate_semantic_engine_count = 0.
```

Preferred:

```text
legacy_duplicate_equivalent_count = 0
```

If a NON-PROOF compatibility fallback remains:

```text
report separately

proof_critical_participation = false.
```

It must not block convergence if physically isolated from proof-critical paths,
but document deprecation/removal recommendation.

---

# 41. Convergence status target

Target:

```text
SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED.
```

Family statuses should be:

```text
CONVERGED
```

or:

```text
CONVERGED_WITH_THIN_ADAPTER
```

where appropriate.

No:

```text
BLOCKED_BY_FRESH_CANONICAL_BYPASS

BLOCKED_BY_FIXTURE_DUPLICATE

BLOCKED_BY_DRIFTABLE_FALLBACK.
```

---

# 42. No shadow in this task

Even if convergence is fully clean:

```text
DO NOT run the monitored shadow in M12BI.
```

Reason:

```text
M12BI is the bounded convergence repair requested by M12BH.
```

Next task should independently authorize a clean shadow
under the converged semantic architecture.

This keeps causal proof clear.

---

# 43. Next scope if convergence succeeds

Required:

```text
next_scope =
RETRY_FULL_SHADOW_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE
```

Not yet:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW...
```

The full monitored compatibility cohort is still required first.

---

# 44. Next scope if convergence fails

If any proof-critical bypass or divergent duplicate remains:

```text
next_scope =
CONTINUE_BOUNDED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_REPAIR
```

with the smallest unresolved family/path.

Do not go back to lexical micro-patches.

---

# 45. Local-only / production firewall

M12BI is LOCAL-ONLY.

Required:

```text
model calls = 0

network gate attempts = 0

provider source fetches = 0

production DB mutations = 0

monitoring registrations = 0

monitoring stops = 0

assessment persistence mutations = 0

warning mutations = 0

notification queue writes = 0

production sends = 0

remote pushes = 0

raw model artifact remote pushes = 0

main branch mutations = 0

main merges = 0

deployments = 0

scheduler mutation = 0

automatic monitoring resume = 0.
```

Monitoring schedules remain paused.

---

# 46. Required root-cause / architecture artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bi-scope-freeze

04-m12bh-convergence-debt-freeze

05-fresh-postmodel-bypass-reproduction

06-fresh-semantic-applicability-matrix

07-canonical-core-semantic-orchestrator-options

08-canonical-core-semantic-orchestrator-decision

09-fresh-owned-evidence-adapter-contract

10-fresh-specific-additive-audit-contract

11-fresh-execute-run-hard-gate-contract

12-fresh-final-freeze-audit-provenance-contract.
```

---

# 47. Required duplicate-removal artifacts

Produce:

```text
13-case-semantic-errors-duplicate-audit

14-case-semantic-errors-migration-decision

15-fic-fin-05-hard-errors-duplicate-audit

16-fic-fin-05-hard-errors-migration-decision

17-business-delta-fallback-audit

18-business-delta-proof-critical-fallback-seal-decision

19-proof-readiness-convergence-audit

20-fresh-readiness-thin-adapter-contract.
```

---

# 48. Required ownership / call-graph artifacts

Produce:

```text
21-semantic-contract-ownership-map-after

22-semantic-consumer-call-graph-after

23-proof-critical-bypass-scan-after

24-proof-critical-duplicate-semantic-engine-scan-after

25-semantic-service-provenance-manifest.
```

---

# 49. Required golden corpus artifacts

Produce:

```text
26-semantic-golden-corpus-manifest-unchanged

27-fcf-golden-corpus-cross-path-results

28-netdebt-golden-corpus-cross-path-results

29-working-capital-golden-corpus-cross-path-results

30-financial-sector-golden-corpus-cross-path-results

31-configured-signal-golden-corpus-cross-path-results

32-business-delta-golden-corpus-cross-path-results

33-market-expectation-golden-corpus-cross-path-results

34-cross-path-golden-corpus-equality-summary-after.
```

Required:

```text
40 cases

0 unexplained divergence.
```

---

# 50. Required offline replay artifacts

Produce:

```text
35-latest-fresh-proof-artifact-identity

36-latest-fresh-output-canonical-offline-reaudit

37-latest-fresh-readiness-canonical-offline-replay

38-m12bd-fictional-proof-identity-freeze

39-m12bd-canonical-offline-reaudit

40-monitored-semantic-regression-equality

41-shadow-semantic-service-identity-regression.
```

---

# 51. Required regression freeze artifacts

Produce:

```text
42-m12bg-fcf-requirement-freeze

43-m12bf-frozen-layout-freeze

44-m12be-active-universe-identity-freeze

45-m12bd-stage2-wc-binding-freeze

46-m12bd-optional-audit-coverage-freeze

47-m12bc-context-finalizer-freeze

48-m12bb-stage1-wc-binding-freeze

49-m12ba-financial-sector-replacement-verb-freeze

50-m12az-fcf-local-temporal-scope-freeze

51-m12ay-configured-fcf-support-freeze

52-m12at-configured-signal-field-ownership-freeze

53-m12ap-market-expectation-independence-freeze

54-m12ao-business-delta-convergence-freeze

55-adr-security-basis-freeze

56-two-stage-core-immutability-freeze.
```

---

# 52. Required model-facing no-change artifacts

Produce:

```text
57-fresh-model-prompt-semantic-hash-freeze

58-fresh-model-schema-semantic-hash-freeze

59-monitored-model-prompt-semantic-hash-freeze

60-monitored-model-schema-semantic-hash-freeze

61-final-user-schema-hash-freeze

62-model-facing-no-change-decision.
```

Expected:

```text
NO_MODEL_FACING_SEMANTIC_CHANGE.
```

If not:

```text
STOP
MODEL_FACING_CONVERGENCE_SCOPE_EXPANSION_REQUIRED.
```

---

# 53. Required deterministic tests

Produce:

```text
63-canonical-orchestrator-unit-tests

64-fresh-adapter-unit-tests

65-proof-duplicate-removal-tests

66-business-delta-fallback-seal-tests

67-readiness-adapter-tests

68-40-case-cross-path-golden-corpus-tests

69-fresh-historical-offline-replay-tests

70-m12bd-fictional-offline-replay-tests

71-monitored-regression-equality-tests

72-focused-test-results

73-full-local-test-results

74-ruff-and-diff-results

75-hosted-ci-portability-observation.
```

No model calls.

---

# 54. Required convergence decisions

Produce:

```text
76-financial-temporal-role-convergence-decision

77-fcf-convergence-decision

78-netdebt-convergence-decision

79-working-capital-convergence-decision

80-financial-sector-convergence-decision

81-configured-signal-convergence-decision

82-business-delta-convergence-decision

83-market-expectation-convergence-decision

84-qtd-ytd-convergence-decision

85-proof-readiness-convergence-decision

86-semantic-single-source-convergence-final-decision.
```

---

# 55. Required completion artifacts

Produce:

```text
87-existing-fresh-proof-impact-summary

88-existing-monitored-impact-summary

89-shadow-retry-readiness-decision

90-fresh-real-proof-readiness-decision

91-final-main-merge-readiness-note

92-production-no-change

93-schedule-pause-observation

94-remote-push-prohibition-audit

95-master-workflow-update

96-program-completion.
```

---

# 56. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bh_semantic_convergence_status
m12bh_proof_critical_bypass_count
m12bh_legacy_duplicate_divergent_count
m12bh_legacy_duplicate_equivalent_count
m12bh_golden_corpus_cross_path_divergence_count

canonical_core_semantic_orchestrator_contract_version

fresh_semantic_applicability_matrix_status

fresh_postmodel_canonical_audit_enabled
fresh_final_freeze_canonical_audit_provenance_enabled

case_semantic_errors_independent_hard_semantics_count_after
fic_fin_05_independent_hard_semantics_count_after

business_delta_proof_critical_fallback_participation_count_after

fresh_readiness_canonical_policy_enabled

semantic_contract_family_count

canonical_shared_service_count_after
thin_adapter_count_after
legacy_duplicate_equivalent_count_after
legacy_duplicate_divergent_count_after
proof_critical_bypass_count_after
proof_critical_duplicate_semantic_engine_count_after

golden_corpus_case_count
golden_corpus_canonical_failure_count
golden_corpus_cross_path_divergence_count_after

financial_temporal_role_convergence_status
fcf_convergence_status
netdebt_convergence_status
working_capital_convergence_status
financial_sector_convergence_status
configured_signal_convergence_status
business_delta_convergence_status
market_expectation_convergence_status
qtd_ytd_convergence_status
proof_readiness_policy_convergence_status

latest_fresh_historical_candidate_count
latest_fresh_historical_previous_accepted_count
latest_fresh_historical_canonical_pass_count
latest_fresh_historical_canonical_fail_count
latest_fresh_historical_fresh_specific_fail_count
latest_fresh_historical_readiness_status

m12bd_offline_reaudit_status

fresh_model_prompt_semantic_change_count
fresh_model_schema_semantic_change_count
monitored_model_prompt_semantic_change_count
monitored_model_schema_semantic_change_count
final_user_schema_change_count

fresh_model_calls = 0
fictional_model_calls = 0
shadow_model_calls = 0
network_gate_attempts = 0

provider_source_fetches = 0

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

remote_push_count
raw_model_artifact_remote_push_count

main_branch_mutations
main_merges
deployments

scheduler_mutation_count
automatic_monitoring_resume

semantic_single_source_convergence_status

shadow_retry_readiness

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Anything unmeasured:

```text
NOT_MEASURED.
```

---

# 57. Expected clean completion

Target:

```text
semantic_single_source_convergence_status =
SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED

proof_critical_bypass_count_after = 0

legacy_duplicate_divergent_count_after = 0

proof_critical_duplicate_semantic_engine_count_after = 0

golden_corpus_cross_path_divergence_count_after = 0

m12bd_offline_reaudit_status = PASS

shadow_retry_readiness =
READY_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE

fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY

next_scope =
RETRY_FULL_SHADOW_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE.
```

No model calls in this task.

---

# 58. Historical fresh failure handling

If previously accepted fresh outputs fail canonical audit:

Do NOT weaken canonical semantics.

Report:

```text
candidate

old acceptance reason

new canonical hard error

semantic family

whether current production state was affected

whether only proof history is affected.
```

M12BI is local/offline.

No persistence correction.

No production mutation.

The next task may decide whether a fresh formal proof must be regenerated later.

---

# 59. Failure handling

## A. Fresh adapter cannot construct canonical audit inputs without semantic invention

```text
STOP
FRESH_CANONICAL_INPUT_ADAPTER_CONTRACT_INCOMPLETE.
```

Do not fake data.

## B. Business-delta lifecycle for fresh analysis is ambiguous

```text
STOP
FRESH_BUSINESS_DELTA_LIFECYCLE_CONTRACT_AMBIGUOUS.
```

No delta re-derivation.

## C. Canonical orchestrator changes monitored audit results

```text
STOP
CANONICAL_ORCHESTRATOR_MONITORED_REGRESSION.
```

## D. Removing proof duplicate causes a canonical fixture gap

```text
STOP
CANONICAL_SERVICE_FIXTURE_COVERAGE_GAP.
```

The gap must be fixed in the canonical service,
not restored in a fixture helper.

## E. Golden corpus still diverges

```text
next_scope =
CONTINUE_BOUNDED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_REPAIR
```

with exact unresolved path/family.

## F. Convergence succeeds

Do NOT run shadow in M12BI.

Next:

```text
RETRY_FULL_SHADOW_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE.
```

---

# 60. Final task principle

M12BH proved the systemic issue the user suspected.

The problem was not that monitored/shadow lacked all of the recent semantic work.

It was that:

```text
monitored/shadow had become the path using the canonical semantic services,

while the active fresh/new-issuer proof path still used an older partial audit
that bypassed those canonical services.
```

At the same time, proof harnesses still contained a few independent hard-semantic helpers.

The correct M12BI repair is therefore architectural:

```text
one canonical post-model semantic orchestrator

→ fresh path becomes a thin adapter to it

→ monitored/shadow continue using the same services

→ proof fixtures assert canonical audit outputs instead of re-parsing candidate text

→ BusinessDelta fallback is removed/sealed from proof-critical callers

→ semantic readiness uses one hard-vs-diagnostic policy

→ the unchanged 40-case corpus becomes cross-path identical

→ historical frozen outputs are re-audited offline

→ no model call and no shadow yet

→ only after deterministic convergence is proven,
   retry the complete monitored shadow under the unified semantics.
```

Do NOT:

```text
add another fresh-only regex

add another monitored-only regex

copy canonical code into wrappers

make fresh path the new canonical service

make monitored path blindly mimic fresh outputs

weaken canonical validators to preserve historical fresh acceptance

post-hoc edit model candidates

run model calls

run network preflight

run shadow

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring.
```

The goal is not to make two implementations agree.

The goal is to have only one proof-critical implementation of each semantic rule.
