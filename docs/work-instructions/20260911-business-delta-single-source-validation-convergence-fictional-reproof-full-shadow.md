# Thesis Monitor — Business-Delta Single-Source Validation Convergence + Full Fictional Reproof + Full Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-business-delta-single-source-validation-convergence-fictional-reproof-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-business-delta-single-source-validation-convergence-fictional-reproof-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AO — Integrated-Main Business-Delta Validator Convergence
         A. Freeze successful M12AN PPE-proxy / FCF repair
         B. Reproduce FIC-FIN-06 duplicate business-delta semantics
         C. Make BusinessDeltaEvidenceView the single source of truth
         D. Remove post-model re-derivation of eligibility/direction from raw prose
         E. Start a NEW full 8 × 3 two-stage fictional proof
         F. If hard gates pass, run NEW full active-monitored same-packet shadow
         G. Produce final boundary / delta-materiality / holder policy handoff
```

M12AN successfully solved both intended PPE-proxy / FCF defects:

```text
1. NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE
2. MODEL_FACING_PROXY_METADATA_MISLABEL
```

M12AN selected:

```text
BRANCH_B_METADATA_AND_VALIDATOR
```

and correctly changed the model-facing PPE-only cash-conversion projection:

```text
before:
label = cash_flow_fcf_ppe
metric_refs = ["FCF"]

after:
label = cash_conversion_ocf_less_ppe
metric_refs = []
```

while preserving canonical:

```text
financial_semantics.metric = ocf_less_ppe_capex
```

It also made explicit `not FCF` disclaimers safe while retaining hard failure
for affirmative PPE-proxy-as-FCF claims.

Because Branch B changed the model-facing evidence surface,
M12AN correctly started a NEW full fictional proof.

That new proof stopped after two Stage-1 calls because FIC-FIN-06 exposed
a separate pre-existing architecture inconsistency:

```text
BusinessDeltaEvidenceCapability / BusinessDeltaEvidenceView:
E03 trade receivables increase → eligible observed change, direction unspecified
E04 inventory increase → eligible observed change, direction unspecified
E09 operating improvement → eligible observed change, STRENGTHENED

legacy post-model business_delta validator:
E03 → STRENGTHENED
E04 → STRENGTHENED
E09 → STRENGTHENED
E06 baseline thesis → incorrectly treated as delta-eligible context
```

The model output:

```text
business_thesis_change = UNRESOLVED
```

was therefore accepted by the new capability validator
but rejected by the legacy business-delta audit as:

```text
UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA
```

This is not a model-quality failure.

It is:

```text
DUPLICATE_BUSINESS_DELTA_SEMANTICS_WITH_CONFLICTING_SOURCES_OF_TRUTH
```

M12AO must converge these paths before any new proof.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-ppe-only-cash-conversion-fcf-claim-polarity-label-safety-full-shadow-report.zip
```

Verified SHA-256:

```text
259e2ed2a2846370be95f68e5b499dd438a1ff98e8b5bc39b305a16bfecf0412
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent ZIP verification:

```text
entries = 161

indexed payloads = 160

artifact hash mismatch = 0
artifact size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12AN status

M12AN status:

```text
BLOCKED_AT_FICTIONAL_HARD_GATE
```

New fictional generation:

```text
20260911-m12ai-fictional-20260911T120652Z-deb9e777a18e
```

Model contract:

```text
gpt-5.6-sol / xhigh
1800-second finite watchdog
wrapper retry = 0
```

Actual calls:

```text
planned = 12
completed = 2

evaluated Stage-1 rows = 8
PASS = 7
FAIL = 1

Stage-2 calls = 0
shadow calls = 0

timeout = 0
orphan = 0
wrapper retry = 0
```

Failing subject:

```text
FIC-FIN-06
```

Failure:

```text
UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA
```

Do not reuse or continue this stopped generation.

---

# 3. M12AN PPE-proxy / FCF repair — freeze successful

M12AN root-cause split:

```text
NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE = confirmed

MODEL_FACING_PROXY_METADATA_MISLABEL = confirmed
```

Selected branch:

```text
BRANCH_B_METADATA_AND_VALIDATOR
```

Freeze:

```text
cash_conversion_ocf_less_ppe

metric_refs = []

financial_semantics.metric = ocf_less_ppe_capex

ppe_only_not_management_defined_fcf limitation

explicit not-FCF disclaimer safety

affirmative proxy-as-FCF hard failure
```

M12AN exact TSLA replay:

```text
PASS

affirmative_proxy_as_fcf_violation_count = 0

explicit_not_fcf_disclaimer_count = 1

partial_capex_called_fcf_count = 0
```

Context-05 historical replay:

```text
4 / 4 PASS
```

PPE-proxy fixtures:

```text
negative = 5 / 5 PASS
positive = 5 / 5 PASS
English/Korean negation = PASS
```

Do not reopen this contract in M12AO.

---

# 4. Stage-2 Korean lexical repair — freeze

Preserve M12AM:

```text
stage2-language-contamination-v2

real "주가" language blocked

"수주가 / 발주가" false positives eliminated
```

No Stage-2 lexical changes in M12AO.

---

# 5. Monitoring ownership / temporal scope — freeze

Preserve:

```text
price confirmation / risk-reward transitions excluded from Directional Core

Timing fact retention

prospective risk vs current financial claim temporal-scope contract

conditional net-debt safety

financial-sector contrastive exclusion

QTD/YTD safety

WC grounding

debt completeness

ADR/security basis
```

No changes.

---

# 6. Two-stage architecture — freeze

Preserve:

```text
Stage 1 = Core Economic Judgment

Stage 2 = Fundamental Stance

deterministic composer

Stage 1 stance fields = 0

Stage 2 writable core fields = 0

core snapshot hash

post-compose core immutability

final external schema compatibility
```

No architecture redesign.

---

# 7. Exact M12AN FIC-FIN-06 candidate

M12AN Stage-1 FIC-FIN-06 output:

```text
overall_direction =
HOLD 5.5:4.5 BUY_LEAN

directional_confidence =
LOW

business_thesis_change =
UNRESOLVED
```

Business-thesis context:

```text
"영업 성장은 강화 신호지만
 재고와 매출채권의 동반 증가는 그 질을 모호하게 해
 논지 변화가 아직 해소되지 않았다."
```

Core judgment:

```text
"매출과 영업이익 증가는 긍정적이지만
 운전자본 확대의 수요 질과 회수 시점이 확인되지 않아
 긍정 기울기에 그친다."
```

This is a coherent materiality/quality judgment.

The hard stop came from validator disagreement,
not from missing evidence identity.

---

# 8. Authoritative M12AN BusinessDeltaEvidenceView for FIC-FIN-06

Model-facing view:

```text
capability =
AI_JUDGMENT

baseline_context_refs =
[E06]

eligible_change_refs =
[E03, E04, E09]

eligible_change_direction_hints =
{
  E09: [STRENGTHENED]
}
```

Therefore:

```text
E03 trade receivables increase =
ELIGIBLE_OBSERVED_CHANGE
DIRECTION_UNSPECIFIED

E04 inventory increase =
ELIGIBLE_OBSERVED_CHANGE
DIRECTION_UNSPECIFIED

E09 sales + operating profit increase =
ELIGIBLE_OBSERVED_CHANGE
STRENGTHENED

E06 stored business thesis =
BASELINE_CONTEXT_ONLY
NOT DELTA-EVIDENCE
```

This is the intended contract.

---

# 9. Conflicting legacy post-model audit

The legacy `business_delta` audit independently reconstructed evidence semantics
and produced:

```text
E03:
delta_evidence_eligible = true
supported_directions = [STRENGTHENED]

E04:
delta_evidence_eligible = true
supported_directions = [STRENGTHENED]

E06:
delta_evidence_eligible = true
supported_directions = []

E09:
delta_evidence_eligible = true
supported_directions = [STRENGTHENED]
```

It then concluded:

```text
supported_change_directions =
[STRENGTHENED]

observed =
UNRESOLVED

→ UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA
```

This directly contradicts the pre-model capability architecture.

---

# 10. Root cause

Freeze the root cause as:

```text
LEGACY_BUSINESS_DELTA_VALIDATOR_REDERIVES
ELIGIBILITY_AND_DIRECTION_FROM_RAW_EVIDENCE_TEXT
INSTEAD_OF_CONSUMING_CANONICAL_BUSINESS_DELTA_EVIDENCE_VIEW
```

The exact implementation may have multiple helpers,
but the architectural defect is:

```text
two independent semantic engines decide:
- whether a ref is delta-eligible
- whether a ref supports STRENGTHENED / WEAKENED / unspecified
```

They have drifted.

M12AO must establish one authoritative semantic source.

---

# 11. Single-source-of-truth principle

The authoritative object must be:

```text
BusinessDeltaEvidenceView
```

or its canonical internal precursor.

It owns:

```text
capability

allowed_business_thesis_changes

baseline_context_refs

eligible_change_refs

eligible_change_direction_hints

direction-unspecified eligible refs

excluded_change_refs

exclusion reasons
```

Every downstream business-delta validator must CONSUME this result.

No downstream validator may independently derive
eligibility/direction from raw statement text.

---

# 12. Architectural options

Evaluate before implementation.

## Option A — patch legacy validator heuristics

Example:

```text
stop mapping "higher" to STRENGTHENED
special-case inventory/receivables
```

Reject as primary architecture.

It leaves duplicate sources of truth.

## Option B — delete legacy audit entirely

Potentially unsafe if it also performs:

```text
alias/canonical resolution

selected-ref validation

changed-state grounding

absolute-state-to-delta detection
```

Do not delete blindly.

## Option C — refactor legacy audit to consume canonical delta view

Preferred.

Keep useful post-model checks,
but their semantic inputs come from the frozen canonical view.

Select exactly one architecture.

Preferred:

```text
CANONICAL_BUSINESS_DELTA_VIEW_CONSUMED_BY_POST_MODEL_VALIDATION
```

---

# 13. Preserve useful post-model responsibilities

The post-model validator may still enforce:

```text
selected refs exist

aliases resolve to canonical refs

selected delta refs belong to the same ticker

observed enum is allowed by capability

STRENGTHENED/WEAKENED uses at least one eligible observed-change ref

UNCHANGED_ONLY cannot emit changed/UNRESOLVED states

UNRESOLVED has actual eligible ambiguity/uncertainty support

configured/baseline/current-single-point refs alone cannot prove delta

price/timing/supply cannot prove business delta
```

But it must obtain:

```text
eligibility

baseline role

direction hints

direction-unspecified status
```

from the canonical view.

---

# 14. Remove post-model raw-text direction re-derivation

Forbidden after M12AO:

```text
post-model validator reads:
"higher than prior year-end"

and independently converts it to:
STRENGTHENED
```

Likewise it must not convert:

```text
"lower"
"increased"
"decreased"
"improved"
"deteriorated"
```

to a direction independently
when the canonical view has already classified the ref.

Text interpretation belongs in the canonical evidence-view builder,
where typed semantics and bounded event rules are available.

---

# 15. Canonical direction semantics — freeze

Preserve M12AJ:

```text
operating_cash_flow comparable:
higher → STRENGTHENED-supporting
lower → WEAKENED-supporting

ocf_less_ppe_capex comparable:
higher → STRENGTHENED-supporting
lower → WEAKENED-supporting
```

Preserve:

```text
inventory
receivables
working-capital balance changes
→ direction unspecified by default
```

unless a separate already-frozen safe metric contract says otherwise.

No universal:

```text
higher = STRENGTHENED
lower = WEAKENED
```

rule.

---

# 16. Baseline-context semantics

Refs in:

```text
baseline_context_refs
```

may be selected in:

```text
business_thesis_context
```

to explain what the thesis is.

They do NOT count as:

```text
eligible observed delta evidence.
```

For FIC-FIN-06:

```text
E06
```

must remain:

```text
BASELINE_CONTEXT_ONLY
```

in both pre-model and post-model audits.

No legacy control-fixture exception may make it delta-eligible.

---

# 17. Changed-state validation

When capability:

```text
AI_JUDGMENT
```

and observed:

```text
STRENGTHENED
or
WEAKENED
```

require:

```text
at least one selected ref in eligible_change_refs.
```

Direction contradiction may be declared ONLY if:

```text
all selected eligible observed-change refs
that could support the changed judgment
have known safe directions,

and none supports the observed direction,

and there is no selected direction-unspecified observed-change ref
whose materiality can legitimately be AI-interpreted.
```

Counterevidence is allowed.

---

# 18. Direction-unspecified evidence

A selected ref may be:

```text
eligible observed change

supported direction = unspecified
```

Examples:

```text
inventory increase

receivables increase

context-dependent working-capital movement
```

This means:

```text
the change occurred,
but deterministic code does not know whether
it strengthens or weakens the investment logic.
```

AI may use business context to interpret materiality.

The post-model validator must not replace that uncertainty
with a generic lexical polarity.

---

# 19. UNRESOLVED validation

For capability:

```text
AI_JUDGMENT
```

UNRESOLVED may be valid when selected eligible observed-change evidence has:

```text
conflicting known directions

or

one or more direction-unspecified observed-change items
whose economic interpretation remains genuinely unresolved

or

safe baseline/comparability conflict already represented by the canonical view.
```

UNRESOLVED must NOT be allowed when:

```text
capability = UNCHANGED_ONLY
```

or when no eligible observed change exists.

---

# 20. Exact FIC-FIN-06 M12AN replay

After convergence,
offline revalidate the exact stopped M12AN candidate.

Expected canonical evidence roles:

```text
E03 =
eligible observed change
direction unspecified

E04 =
eligible observed change
direction unspecified

E06 =
baseline context only

E09 =
eligible observed change
STRENGTHENED
```

Observed:

```text
UNRESOLVED
```

Expected:

```text
business_delta capability audit = PASS

legacy/converged post-model business_delta audit = PASS

UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA = 0
```

Do not rewrite the candidate.

---

# 21. Exact M12AJ FIC-FIN-02 replay

Revalidate the earlier mixed-evidence case:

```text
E01 cash conversion → WEAKENED

E08 OCF → WEAKENED

E10 operating improvement → STRENGTHENED

E04 inventory → direction unspecified
```

A model output:

```text
WEAKENED
```

must remain valid.

A model output:

```text
UNRESOLVED
```

may also be valid if selected mixed evidence
and materiality prose support unresolved interpretation.

Do not freeze a target.

---

# 22. 003690 absolute-state regression

Revalidate the known monitored failure case.

If packet capability:

```text
UNCHANGED_ONLY
```

and only:

```text
stored thesis / configured context
```

exists,

then:

```text
STRENGTHENED
```

must remain structurally impossible / hard invalid.

The convergence repair must NOT weaken M12AI's original safety gain.

---

# 23. FIC-FIN-05 UNCHANGED_ONLY regression

For FIC-FIN-05:

```text
capability = UNCHANGED_ONLY
```

must remain.

No legacy validator path may turn:

```text
high debt / thin cash absolute state
```

into:

```text
WEAKENED.
```

Absolute negative state is not business delta.

---

# 24. FIC-FIN-06 historical outputs

M12AK formal proof produced:

```text
STRENGTHENED ×3
```

for FIC-FIN-06.

M12AN stopped output produced:

```text
UNRESOLVED
```

Both may be semantically allowable under:

```text
AI_JUDGMENT
```

if grounded in the same eligible observed-change set.

Do NOT target one exact state in M12AO.

The new full proof measures materiality stability honestly.

---

# 25. Eliminate duplicate direction fields in audit reports

After convergence,
post-model reports should not show one ref with:

```text
canonical view direction = unspecified

legacy linked_evidence direction = STRENGTHENED
```

Required:

```text
business_delta_semantic_projection_mismatch_count = 0
```

For every ref,
report one canonical role/direction source.

---

# 26. Preferred audit row structure

Each selected business-delta evidence row should expose:

```text
alias

canonical_ref

canonical_delta_role:
  BASELINE_CONTEXT
  ELIGIBLE_OBSERVED_CHANGE
  EXCLUDED

supported_change_directions:
  [STRENGTHENED]
  [WEAKENED]
  []

direction_semantics:
  KNOWN_SAFE
  DIRECTION_UNSPECIFIED
  NOT_APPLICABLE

source =
BusinessDeltaEvidenceView
```

No independent reclassification.

---

# 27. Alias/canonical resolution remains hard

Do not weaken:

```text
alias resolution failure

cross-ticker ref

unknown ref

wrong catalog identity
```

These remain hard semantic failures.

The repair only changes where business-delta role/direction semantics come from.

---

# 28. Model-facing view remains unchanged

M12AO should NOT change the model-facing business-delta view
unless a separate bug is found.

Preferred:

```text
business_delta_view_hashes unchanged
```

The model already received the intended evidence roles.

This is a POST-MODEL validator convergence task.

Required default:

```text
model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

business_delta_model_view_change_count = 0
```

---

# 29. M12AN Branch-B evidence projection remains changed

Do not revert:

```text
cash_conversion_ocf_less_ppe

metric_refs = []
```

This model-facing change still invalidates reuse of the older M12AK proof
for the current branch.

Therefore after M12AO validator convergence:

```text
a NEW full fictional proof is still mandatory.
```

---

# 30. Business-delta convergence fixtures

At minimum:

## DELTA-CONV-01

```text
canonical view:
inventory increase = eligible, direction unspecified

legacy/post-model audit:
must also report direction unspecified
```

## DELTA-CONV-02

```text
canonical view:
receivables increase = eligible, direction unspecified

post-model:
same
```

## DELTA-CONV-03

```text
stored thesis = baseline context only

post-model:
must not mark delta-eligible
```

## DELTA-CONV-04

```text
OCF lower comparable = WEAKENED

post-model:
same
```

## DELTA-CONV-05

```text
operating improvement explicit event = STRENGTHENED

post-model:
same
```

## DELTA-CONV-06

```text
UNCHANGED_ONLY + observed STRENGTHENED
→ FAIL
```

## DELTA-CONV-07

```text
AI_JUDGMENT
positive known + direction-unspecified observed change
observed UNRESOLVED
→ potentially valid, not deterministic contradiction
```

## DELTA-CONV-08

```text
AI_JUDGMENT
all selected eligible known directions = STRENGTHENED
observed WEAKENED
no unspecified eligible ref
→ FAIL
```

---

# 31. Cross-path semantic equality

For every ticker/subject,
before model call freeze:

```text
BusinessDeltaEvidenceView
```

After model output,
the validator must reference the SAME object or deterministic serialization.

Required:

```text
pre_model_delta_view_sha256
=
post_model_validator_delta_view_sha256
```

or equivalent object identity/provenance proof.

Do not reconstruct from the prompt string.

---

# 32. No post-hoc model mutation

Required:

```text
post_model_business_delta_override_count = 0
```

The validator either:

```text
accepts
or
rejects
```

the model output.

It never rewrites:

```text
UNRESOLVED → STRENGTHENED
STRENGTHENED → UNCHANGED
```

---

# 33. No score / vote / count thresholds

Required zero:

```text
fixed_business_delta_score_rule_count

delta_majority_vote_rule_count

delta_evidence_count_threshold_rule_count

direction_hint_vote_rule_count
```

One strong eligible observed change can matter.

The model judges materiality.

---

# 34. Full deterministic gate

Before new model calls require:

```text
latest ZIP integrity PASS

M12AN PPE-proxy FCF fixtures PASS

TSLA exact replay PASS

Stage-2 Korean lexical regressions PASS

monitoring ownership regressions PASS

financial temporal-scope regressions PASS

business-delta capability regressions PASS

FIC-FIN-06 exact M12AN replay PASS

FIC-FIN-02 mixed-direction replay PASS

003690 UNCHANGED_ONLY regression PASS

FIC-FIN-05 absolute-state-to-delta regression PASS

pre/post delta-view identity PASS

business_delta_semantic_projection_mismatch_count = 0

focused tests PASS

full local tests PASS

ruff PASS

git diff --check PASS

production firewall PASS

model target = gpt-5.6-sol / xhigh
```

No model calls before this gate.

---

# 35. NEW full fictional proof required

Create:

```text
NEW generation ID
```

Do not reuse M12AN partial outputs.

Frozen subjects:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08
```

Topology:

```text
3 repetitions

2 contexts / repetition

4 subjects / context

Stage 1 calls = 6

Stage 2 calls = 6

total calls = 12

final outputs = 24
```

No judge calls.

---

# 36. Fictional hard-stop policy

Hard stop only for:

```text
runtime/schema failure

invalid evidence identity

financial semantic hard failure

PPE-proxy-as-FCF true violation

business-delta capability violation

business-delta proven canonical-direction contradiction

pre/post delta-view mismatch

price/technical/supply Core contamination

Stage-2 actual contamination

core mutation

aggregate finalization failure
```

Do NOT stop for:

```text
valid AI_JUDGMENT materiality variance

primary threshold variance

new-buyer variance

holder variance

confidence variance
```

Collect all 24 outputs if hard gates pass.

---

# 37. Fictional acceptance

Require:

```text
12 / 12 model calls complete

24 / 24 Stage-1 rows hard PASS

24 / 24 Stage-2 rows hard PASS

24 final compositions

aggregate finalization PASS

business-delta capability violations = 0

business-delta semantic projection mismatch = 0

business-delta proven direction contradiction = 0

PPE-proxy safety failure = 0

not-FCF disclaimer false reject = 0

Stage-2 lexical false positive = 0

financial hard semantic failure = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0
```

Decision-material instability does not block shadow.

---

# 38. Fictional diagnostic reporting

Report for every subject:

```text
overall direction values

balance values

business_thesis_change values

new-buyer values

holder values

confidence values
```

Specifically classify:

```text
FIC-FIN-02:
delta materiality / mixed-evidence behavior

FIC-FIN-05:
primary HOLD/SELL boundary

FIC-FIN-06:
positive operating-change materiality

FIC-FIN-08:
holder HOLDABLE/REVIEW boundary
```

Do not repair them in the same task.

---

# 39. Shadow authorization

If formal fictional hard gates pass:

```text
run full active-monitored shadow.
```

Do NOT require perfect fictional decision-material stability.

The monitored universe is an exposed compatibility cohort.

---

# 40. Active monitored universe

Re-enumerate active monitored stocks read-only at shadow start.

Last verified reference:

```text
22 names
```

Use actual task-start active set.

No registration/stop mutation.

---

# 41. Same-packet shadow

For each active ticker:

```text
one reproducible local packet
```

Same packet hash feeds:

```text
monolithic

Stage 1

Stage 2 evidence context
```

No provider refresh.

Required:

```text
provider_source_fetches = 0
```

---

# 42. Same canonical delta view across monolithic and Stage 1

For each ticker:

```text
monolithic BusinessDeltaEvidenceView
=
Stage 1 BusinessDeltaEvidenceView
```

Required semantic equality:

```text
capability

baseline_context_refs

eligible_change_refs

eligible_change_direction_hints

direction-unspecified eligible refs

excluded refs
```

No architecture comparison is valid otherwise.

---

# 43. Shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total = 3 × context_count
```

At N=22:

```text
18 calls
```

No repetitions.

No fresh unseen issuers.

---

# 44. Shadow hard-stop policy

Hard stop only for:

```text
runtime/schema hard failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

financial semantic hard failure

true PPE-proxy-as-FCF attribution

business-delta capability violation

business-delta canonical projection mismatch

business-delta proven direction contradiction

price/technical/supply Core contamination

Stage-2 actual contamination

financial-sector framework misuse

ADR/security-basis violation

core mutation

production-side-effect attempt

aggregate finalization failure
```

Do not stop because monolithic and two-stage decisions differ.

Collect the cohort.

---

# 45. Shadow comparison taxonomy

Use:

```text
NO_DECISION_MATERIAL_CHANGE

SAME_DIRECTION_CALIBRATION_CHANGE

PRIMARY_DIRECTION_CHANGE

BUSINESS_DELTA_CHANGE

NEW_BUYER_STANCE_CHANGE

HOLDER_STANCE_CHANGE

MULTI_FIELD_DECISION_CHANGE

EXPECTED_CONTRACT_CORRECTION

POTENTIAL_ARCHITECTURE_REGRESSION

OTHER_REVIEW_REQUIRED
```

Delta sublabels:

```text
DELTA_UNCHANGED_ONLY

DELTA_AI_JUDGMENT

DELTA_MATERIALITY_DIFFERENCE

DELTA_EVIDENCE_SELECTION_DIFFERENCE

DELTA_DIRECTION_INTERPRETATION_DIFFERENCE
```

Neither path is automatically ground truth.

---

# 46. Real AI_JUDGMENT delta audit

For every monitored ticker with:

```text
capability = AI_JUDGMENT
```

report:

```text
eligible observed delta refs

known safe direction hints

direction-unspecified refs

monolithic selected refs

Stage 1 selected refs

monolithic business_thesis_change

Stage 1 business_thesis_change

materiality explanation
```

This will finally distinguish:

```text
architecture difference
from
delta evidence-surface bugs.
```

---

# 47. Partial previous shadow results are diagnostic only

Do not stitch:

```text
M12AL
M12AM
```

partial shadow outputs into the new formal cohort.

They may be used to:

```text
cross-check reporting

anticipate adjacent-threshold examples

verify repaired hard-gate cases
```

but not for aggregate statistics.

---

# 48. Combined policy handoff

If the full new shadow completes,
use:

```text
new formal fictional proof

+

complete monitored shadow
```

for the next bounded policy review.

Required focus:

```text
1. primary adjacent threshold policy
   HOLD 5.5 ↔ BUY/SELL 6.0

2. business-delta materiality
   mixed positive / negative / direction-unspecified observed change

3. holder HOLDABLE ↔ REVIEW boundary

4. new-buyer stance differences
   especially where core direction is identical
```

Expected next scope if no hard architecture regression:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

---

# 49. Remote / main / production policy

M12AO is LOCAL-ONLY.

Required:

```text
remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Do not ask for GitHub push authorization.

No main merge.

No deployment.

Schedules remain paused.

---

# 50. Production side-effect firewall

Required:

```text
model_calls_real_fresh_unseen = 0

provider_source_fetches = 0

production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

assessment_persistence_mutations = 0

warning_mutations = 0

notification_queue_writes = 0

production_sends = 0
```

---

# 51. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ao-scope-freeze

04-integrated-main-lineage-freeze

05-m12an-fic-fin-06-failure-reproduction

06-pre-model-business-delta-view-forensic

07-legacy-business-delta-audit-forensic

08-business-delta-dual-semantics-root-cause

09-post-model-validator-responsibility-map

10-single-source-of-truth-architecture-decision
```

---

# 52. Required convergence artifacts

Produce:

```text
11-canonical-business-delta-view-contract

12-post-model-business-delta-validator-contract-v2

13-baseline-context-role-contract

14-direction-unspecified-observed-change-contract

15-changed-state-grounding-contract

16-unresolved-state-grounding-contract

17-canonical-direction-contradiction-contract

18-pre-post-delta-view-identity-contract

19-business-delta-audit-row-contract
```

---

# 53. Required exact replay artifacts

Produce:

```text
20-m12an-fic-fin-06-exact-offline-replay

21-m12aj-fic-fin-02-mixed-evidence-replay

22-m12ah-003690-absolute-state-regression

23-fic-fin-05-unchanged-only-regression

24-fic-fin-06-historical-strengthened-replay

25-business-delta-semantic-projection-mismatch-audit
```

---

# 54. Required deterministic fixtures

Produce:

```text
26-business-delta-convergence-fixtures

27-direction-unspecified-validation-fixtures

28-unresolved-validation-fixtures

29-known-direction-contradiction-fixtures

30-baseline-context-only-fixtures

31-alias-canonical-identity-regressions

32-unchanged-only-dynamic-schema-regressions
```

At minimum cover DELTA-CONV-01 through DELTA-CONV-08.

---

# 55. Required semantic freezes

Produce:

```text
33-ppe-proxy-fcf-safety-freeze

34-stage2-korean-lexical-freeze

35-monitoring-transition-ownership-freeze

36-financial-temporal-scope-freeze

37-two-stage-ownership-freeze

38-price-timing-renderer-no-change
```

---

# 56. Required test gate

Produce:

```text
39-focused-test-results

40-full-local-test-results

41-ruff-and-diff-results

42-hosted-ci-portability-observation

43-new-fictional-model-call-gate
```

No model calls before artifact 43 PASS.

---

# 57. Required NEW fictional artifacts

Produce:

```text
44-fictional-generation-manifest

45-fictional-delta-capability-manifest

46-fictional-direction-hint-manifest

47-stage1-run1-context01

48-stage1-run1-context02

49-stage2-run1-context01

50-stage2-run1-context02

51-stage1-run2-context01

52-stage1-run2-context02

53-stage2-run2-context01

54-stage2-run2-context02

55-stage1-run3-context01

56-stage1-run3-context02

57-stage2-run3-context01

58-stage2-run3-context02

59-fictional-context-hard-semantic-audit

60-fictional-business-delta-convergence-audit

61-fictional-ppe-proxy-fcf-safety-audit

62-fictional-stage2-language-audit

63-fictional-final-composition-audit

64-fictional-aggregate-finalization-audit

65-fictional-primary-direction-diagnostic

66-fictional-business-delta-materiality-diagnostic

67-fictional-new-buyer-diagnostic

68-fictional-holder-diagnostic

69-fictional-core-immutability-audit

70-fictional-runtime-audit

71-fictional-shadow-gate-decision
```

---

# 58. Required shadow setup artifacts

If artifact 71 authorizes shadow:

```text
72-task-start-active-monitored-universe

73-shadow-packet-inventory

74-shadow-packet-hash-manifest

75-shadow-delta-capability-manifest

76-shadow-direction-hint-manifest

77-shadow-frozen-context-manifest

78-shadow-batching-manifest

79-shadow-model-call-gate
```

---

# 59. Required full shadow artifacts

Produce:

```text
80-shadow-monolithic-model-artifacts

81-shadow-stage1-model-artifacts

82-shadow-stage2-model-artifacts

83-shadow-context-hard-semantic-audit

84-shadow-business-delta-convergence-audit

85-shadow-ppe-proxy-fcf-safety-audit

86-shadow-stage2-language-audit

87-shadow-final-composition-audit

88-shadow-aggregate-finalization-audit

89-shadow-per-ticker-comparison

90-shadow-core-direction-differences

91-shadow-business-delta-differences

92-shadow-new-buyer-differences

93-shadow-holder-differences

94-shadow-same-direction-calibration-differences

95-shadow-expected-contract-corrections

96-shadow-potential-architecture-regressions

97-shadow-unresolved-review-required

98-shadow-financial-sector-audit

99-shadow-adr-security-basis-audit

100-shadow-cyclical-valuation-audit

101-shadow-core-immutability-audit

102-shadow-runtime-audit

103-shadow-aggregate-summary

104-shadow-architecture-decision
```

Preserve raw model artifacts locally.

No remote push.

---

# 60. Required combined diagnostics

If full shadow completes:

```text
105-fic-fin-05-vs-monitored-primary-boundary-analogs

106-fic-fin-02-vs-monitored-delta-materiality-analogs

107-fic-fin-06-vs-monitored-positive-delta-analogs

108-fic-fin-08-vs-monitored-holder-analogs

109-new-buyer-monolithic-vs-two-stage-analogs

110-real-business-delta-materiality-lessons

111-combined-fictional-monitored-root-cause-summary

112-next-bounded-policy-decision
```

---

# 61. Required completion artifacts

Produce:

```text
113-business-delta-validator-convergence-success-decision

114-ppe-proxy-fcf-safety-preservation-decision

115-new-fictional-proof-success-decision

116-full-shadow-completion-decision

117-existing-monitored-impact-summary

118-two-stage-shadow-compatibility-decision

119-fresh-real-proof-readiness-decision

120-final-main-merge-readiness-note

121-production-no-change

122-schedule-pause-observation

123-remote-push-prohibition-audit

124-master-workflow-update

125-program-completion
```

---

# 62. Full fictional acceptance

Require:

```text
12 / 12 model calls complete

24 / 24 Stage-1 rows hard PASS

24 / 24 Stage-2 rows hard PASS

24 final compositions

aggregate finalization PASS

business-delta capability violations = 0

business-delta semantic projection mismatches = 0

business-delta proven canonical-direction contradictions = 0

PPE-proxy FCF violations = 0

not-FCF disclaimer false rejects = 0

Stage-2 language false positives = 0

financial hard semantic failures = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0
```

Decision-material variance does not block shadow.

---

# 63. Full shadow acceptance

Require:

```text
all planned calls complete

all active tickers represented once

aggregate finalization PASS

business-delta semantic projection mismatch = 0

true business-delta contradiction = 0

true PPE-proxy-as-FCF violation = 0

not-FCF disclaimer false reject = 0

Stage-2 actual contamination = 0

Stage-2 lexical false positive = 0

invalid refs = 0

financial hard semantic failure = 0

price/technical/supply Core contamination = 0

financial-sector misuse = 0

ADR/security-basis failure = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0

production side effects = 0
```

Architecture decision differences are measured, not hard failures.

---

# 64. Fresh-real / main / production readiness

At M12AO completion:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

Even if fictional and shadow complete.

The next bounded policy review must consume the full clean cohort first.

No fresh unseen proof in M12AO.

---

# 65. Failure handling

## A. Exact FIC-FIN-06 UNRESOLVED still false-rejects

```text
next_scope =
BUSINESS_DELTA_VALIDATOR_ARCHITECTURE_REVIEW
```

Do not model-call.

## B. Convergence weakens 003690/FIC-FIN-05 absolute-state safety

```text
STOP
BUSINESS_DELTA_CONVERGENCE_TOO_PERMISSIVE
```

## C. PPE-proxy FCF regressions appear

```text
STOP
PPE_PROXY_FCF_SAFETY_REGRESSION
```

## D. New fictional hard semantic failure

Do not run shadow.

Use smallest failing contract.

## E. Full shadow completes cleanly

Expected next scope:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

## F. Full shadow shows systematic architecture regression

Use the appropriate bounded compatibility review.

---

# 66. Program-completion fields

Include at least:

```text
base_integration_head_sha

integration_branch

latest_result_zip_sha256
latest_result_integrity

business_delta_dual_semantics_root_cause

business_delta_validator_contract_version

business_delta_single_source_of_truth_enabled

legacy_raw_text_direction_rederivation_count

legacy_raw_text_eligibility_rederivation_count

business_delta_semantic_projection_mismatch_count

pre_post_delta_view_identity_mismatch_count

m12an_fic_fin_06_offline_replay_status

m12aj_fic_fin_02_offline_replay_status

m12ah_003690_regression_status

fic_fin_05_unchanged_only_regression_status

post_model_business_delta_override_count

fixed_business_delta_score_rule_count
delta_majority_vote_rule_count
delta_evidence_count_threshold_rule_count

ppe_proxy_label
ppe_proxy_metric_refs
ppe_proxy_fcf_safety_regression_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
business_delta_model_view_change_count

investment_judgment_model_target
investment_judgment_reasoning_effort

fictional_generation_id

fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total

fictional_stage1_row_count
fictional_stage2_row_count
fictional_final_composition_count

fictional_business_delta_capability_violation_count
fictional_business_delta_semantic_projection_mismatch_count
fictional_business_delta_direction_contradiction_count

fictional_ppe_proxy_fcf_violation_count
fictional_not_fcf_disclaimer_false_reject_count

fictional_primary_direction_unstable_subject_count
fictional_business_delta_materiality_variance_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count

fictional_core_mutation_count

fictional_runtime_timeout_count
fictional_runtime_orphan_count
fictional_wrapper_retry_count

task_start_active_monitor_count
task_start_active_monitor_tickers

shadow_generation_id

shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count

shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status

shadow_business_delta_semantic_projection_mismatch_count
shadow_business_delta_direction_contradiction_count

shadow_ppe_proxy_fcf_violation_count
shadow_not_fcf_disclaimer_false_reject_count

shadow_stage2_language_contamination_count
shadow_stage2_language_false_positive_count

shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count

shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count

shadow_financial_sector_framework_failure_count
shadow_adr_security_basis_failure_count
shadow_cyclical_valuation_framework_failure_count

shadow_core_mutation_after_stance_count

provider_source_fetches

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

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

two_stage_shadow_compatibility_classification

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
artifact_secret_scan_failure_count
```

Anything unmeasured:

```text
NOT_MEASURED
```

---

# 67. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0
```

Report final ZIP SHA-256.

Do not push raw/report artifacts to GitHub.

---

# 68. Final task principle

M12AN correctly fixed the PPE-only cash-conversion / FCF safety layer.

The new FIC-FIN-06 stop exposed a different architectural inconsistency:

```text
pre-model canonical business-delta view:
inventory / receivables increases
= observed change, direction unspecified

legacy post-model audit:
re-read "higher than prior year-end"
= STRENGTHENED

pre-model:
stored thesis E06
= baseline context only

legacy post-model:
E06
= delta-eligible
```

The model then produced:

```text
UNRESOLVED
```

for:

```text
positive operating improvement
+
working-capital changes whose quality is not deterministically known.
```

The new capability validator accepted that judgment.

The old validator rejected it.

The correct next flow is:

```text
make BusinessDeltaEvidenceView the single source of truth

→ preserve post-model hard validation,
   but make it consume canonical roles/directions

→ remove raw-text semantic re-derivation

→ prove exact FIC-FIN-06 UNRESOLVED now passes

→ prove 003690 / FIC-FIN-05 absolute-state safety remains strict

→ preserve the M12AN PPE-proxy / FCF metadata + disclaimer fixes

→ start a brand-new full 8 × 3 fictional proof

→ if hard gates pass,
   start a brand-new full active-monitored shadow

→ finally use the complete clean fictional + monitored cohort
   for the real boundary / delta-materiality / holder policy review.
```

Do NOT:

```text
make inventory increase automatically negative or positive

target FIC-FIN-06 to STRENGTHENED or UNRESOLVED

weaken UNCHANGED_ONLY

delete alias/ref validation

post-hoc rewrite model delta output

revert the FCF metadata repair

resume the stopped M12AN generation

stitch partial shadow generations

majority-vote prior outputs

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring
```

One semantic object must define what business-delta evidence means.
