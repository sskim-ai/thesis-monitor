# Thesis Monitor — Typed Financial Delta Direction-Hint Propagation + Full Fictional Reproof + Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-typed-financial-delta-direction-hint-propagation-fictional-reproof-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-typed-financial-delta-direction-hint-propagation-fictional-reproof-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AJ — Integrated-Main Business-Delta Direction Semantics
         A. Preserve M12AI BusinessDeltaEvidenceCapability architecture
         B. Propagate safe typed financial comparison directions
         C. Repair partial-hint mixed-evidence contradiction logic
         D. Full 8 × 3 two-stage fictional reproof
         E. Full active-monitored same-packet shadow comparison
         F. Combined boundary / delta-materiality / holder policy decision
```

M12AI successfully implemented the intended pre-model business-delta capability architecture:

```text
UNCHANGED_ONLY
AI_JUDGMENT
INPUT_AMBIGUOUS
```

and dynamic per-ticker business_thesis_change schemas.

The architecture itself is not the current blocker.

M12AI stopped on the first fictional Stage 1 model call because
a verified typed financial comparison was correctly classified as
eligible observed change evidence,
but its safe change direction was not propagated into the
BusinessDeltaEvidenceView.

This caused the post-model validator to reject an otherwise grounded
mixed-evidence `WEAKENED` judgment.

M12AJ must fix the smallest failing contract without weakening:

```text
UNCHANGED_ONLY gating

eligible-change evidence requirements

current financial semantic safety

business-delta absolute-state prohibition

two-stage Core → Stance architecture
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-business-delta-evidence-capability-gate-fictional-reproof-full-monitored-shadow-report.zip
```

Verified SHA-256:

```text
1b50214ac313dcae0ba9241248eeb55c659cdf17d18aca6b59f7aebf00f8154c
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 114
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

The ZIP contains:

```text
114 indexed payloads
+ artifact-index.json
= 115 entries
```

Recompute independently before trusting the bundle.

---

# 2. M12AI completion status

M12AI status:

```text
BLOCKED
```

Stop:

```text
fictional run-1 / Stage 1 / context-01
```

Actual proof-critical model calls:

```text
1
```

Model:

```text
gpt-5.6-sol / xhigh
```

The model transport succeeded:

```text
returncode = 0
output exists = true
schema rows = 4 / 4 PASS
semantic rows = 3 / 4 PASS
timeout = 0
orphan = 0
wrapper retry = 0
```

Failing ticker:

```text
FIC-FIN-02
```

Failure:

```text
BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE
```

Monitored shadow:

```text
NOT RUN
```

Do not reuse or selectively continue the stopped fictional generation.

---

# 3. DNS pre-model preflight note

M12AI retained one earlier sandbox preflight receipt where DNS was unavailable.

That attempt:

```text
stopped before spawning a model
```

and is NOT an additional proof-critical model call.

The subsequent network-ready attempt completed normally.

M12AJ must preserve normal network-readiness checks,
but must not treat the DNS preflight artifact as a model-runtime regression.

No timeout/retry policy change.

---

# 4. M12AI architecture — freeze successful

Preserve:

```text
business-delta-evidence-capability-v1

UNCHANGED_ONLY

AI_JUDGMENT

INPUT_AMBIGUOUS

dynamic per-ticker business_thesis_change enum

explicit business-delta evidence view

post-model business-delta override count = 0
```

M12AI offline result:

```text
003690 capability = UNCHANGED_ONLY
```

and the previous unsupported `STRENGTHENED`
is structurally impossible under the new schema.

Do not revert the capability gate.

---

# 5. M12AI capability examples — freeze

M12AI classified the fictional cohort before generation.

Examples:

```text
FIC-FIN-03 = UNCHANGED_ONLY

FIC-FIN-05 = UNCHANGED_ONLY

FIC-FIN-07 = UNCHANGED_ONLY

FIC-FIN-08 = UNCHANGED_ONLY
```

and cases with valid observed comparison/event evidence as:

```text
AI_JUDGMENT
```

including:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-04
FIC-FIN-06
```

Do not derive capability from prior model outputs.

Capability remains input-evidence-derived.

---

# 6. Exact M12AI FIC-FIN-02 evidence

FIC-FIN-02 contains verified mixed observed evidence.

## E01

```text
metric =
ocf_less_ppe_capex

semantic category =
CASH_CONVERSION

period =
YTD 2026-06-30

current value =
-20

prior-year comparable value =
55

comparison kind =
prior_year_comparable

quality =
verified

statement =
"Safely derived OCF less PPE acquisition cash outflow ...
 is lower than the prior-year comparable period."
```

Economic/typed comparison direction:

```text
WEAKENED
```

for cash conversion.

## E08

```text
metric =
operating_cash_flow

semantic category =
CASH_CONVERSION

current value =
40

prior-year comparable value =
100

comparison kind =
prior_year_comparable

quality =
verified

statement =
"Reported operating cash flow ...
 is lower than the prior-year comparable period."
```

Safe typed comparison direction:

```text
WEAKENED
```

## E10

```text
statement =
"Comparable-period sales and accounting profit improved."
```

Safe explicit direction:

```text
STRENGTHENED
```

## E04

```text
metric =
inventory

semantic category =
WORKING_CAPITAL

current =
240

prior-year-end =
150
```

This is valid observed change evidence.

But:

```text
higher inventory
```

is NOT universally equivalent to:

```text
WEAKENED
```

or:

```text
STRENGTHENED
```

without additional business context.

Therefore E04 should remain:

```text
direction unspecified
```

unless a separate safe contract proves otherwise.

---

# 7. Exact M12AI capability-view defect

M12AI correctly produced:

```text
eligible_change_refs =
E01
E04
E08
E10
```

but model-facing direction hints contained only:

```text
E10 → STRENGTHENED
```

Missing:

```text
E01 → WEAKENED

E08 → WEAKENED
```

Root cause recorded in M12AI:

```text
ELIGIBLE_TYPED_CASH_CONVERSION_COMPARISON_DIRECTION_HINT_NOT_PROPAGATED_TO_CAPABILITY_VIEW
```

The current implementation derives:

```text
supported_change_directions
```

primarily from free-text `_explicit_direction_hints(statement)`.

That function does not safely encode typed comparison polarity.

Do NOT solve this by globally treating:

```text
"higher" = STRENGTHENED
"lower" = WEAKENED
```

because working-capital and other metrics are not universally monotonic.

---

# 8. Exact model output was economically grounded

FIC-FIN-02 Stage 1 selected:

```text
business_thesis_change =
WEAKENED
```

Business-thesis context cited:

```text
E06 baseline thesis

E01 weakened cash conversion

E10 improved operating evidence
```

Text:

```text
"수요와 회계 이익은 양호하지만
 성장의 현금 전환이 비교 기간보다 약해져
 기존 논거가 약화됐다."
```

The output explicitly recognized:

```text
positive operating counterevidence
+
negative cash-conversion change
```

It did not ignore E10.

The candidate is a legitimate mixed-evidence economic judgment
if E01's typed direction is correctly represented.

Do not change the fixture to force another answer.

---

# 9. Current validator false contradiction

Current post-model logic conceptually gathers:

```text
supported_change_directions
```

from selected eligible refs.

Because only E10 had a propagated hint:

```text
supported = {STRENGTHENED}
```

Observed:

```text
WEAKENED
```

was rejected.

With correct typed propagation:

```text
E01 → WEAKENED
E10 → STRENGTHENED
```

the selected evidence supports BOTH directions.

Then:

```text
WEAKENED
```

is not a contradiction.

This does NOT force WEAKENED.

AI still owns materiality.

---

# 10. Primary repair — typed financial direction semantics

Add a deterministic helper/contract for:

```text
verified typed financial comparisons
```

that derives a SAFE directional hint from:

```text
metric

semantic category

current typed value

comparison typed value

comparison kind

quality

period comparability
```

Do not infer typed direction from English/Korean prose
when numeric typed comparison data are available.

Suggested internal contract:

```text
financial-comparison-direction-v1
```

or equivalent.

---

# 11. Safe polarity registry

Use an explicit bounded polarity registry.

At minimum M12AJ MUST support:

```text
operating_cash_flow

ocf_less_ppe_capex
```

Semantics:

```text
higher comparable value → STRENGTHENED-supporting

lower comparable value → WEAKENED-supporting

equal → no directional hint
```

only when:

```text
quality = verified

comparison exists

comparison kind is valid

periods are safely comparable
```

Do not extrapolate from incomplete or stale numeric data.

---

# 12. No unsafe universal polarity

Do NOT automatically assign direction for every typed metric.

Examples that require caution/context:

```text
inventory

receivables

working-capital balances

capex

non-operating financial effects

some cash balances

some sector-specific regulatory metrics
```

For these:

```text
eligible observed change evidence
```

may exist while:

```text
supported_change_directions = []
```

That is allowed.

Eligibility and direction polarity are separate concepts.

---

# 13. Optional safe metrics review

M12AJ may review whether other already-supported financial metrics
have an unambiguous polarity contract.

Examples that MAY be safely added only if existing domain semantics/tests support them:

```text
revenue

operating_income / operating_profit

operating_margin

ROIC / ROE

complete comparable net debt
```

But:

```text
do not broaden merely for completeness.
```

Every added metric requires:

```text
explicit polarity rationale

positive fixture

negative fixture

equal/no-change fixture

period/comparability safety
```

The smallest required fix is cash conversion.

---

# 14. Net-debt polarity safety

If net debt is considered for direction hints:

Require:

```text
complete comparable net-debt evidence

same security/currency/accounting basis

safe period comparison
```

Then a lower net-debt burden may support STRENGTHENED
and a higher burden may support WEAKENED.

Do NOT infer from:

```text
partial debt

total liabilities

provider multiple back-solving

ADR denominator reconstruction
```

If any comparability is unsafe:

```text
no hint
```

or:

```text
INPUT_AMBIGUOUS
```

according to existing contracts.

---

# 15. Typed direction must be canonical

Direction must be derived from the canonical typed financial object,
not separately from:

```text
alias statement prose

rendered Korean wording

rendered English wording
```

Then alias/model view should project that canonical result.

Required:

```text
canonical typed direction
→ BusinessDeltaEvidenceItem.supported_change_directions
→ BusinessDeltaEvidenceView.eligible_change_direction_hints
```

one source of truth.

---

# 16. Capability view propagation invariant

For every eligible evidence item:

```text
item.supported_change_directions
```

and model-facing:

```text
eligible_change_direction_hints[alias]
```

must agree exactly whenever directions are non-empty.

Required audit:

```text
direction_hint_projection_mismatch_count = 0
```

Do not independently recompute direction during rendering.

---

# 17. Mixed-evidence semantics

The capability view may contain:

```text
positive eligible change evidence

negative eligible change evidence

direction-unspecified eligible change evidence
```

This is expected.

AI may choose:

```text
STRENGTHENED
UNCHANGED
WEAKENED
UNRESOLVED
```

according to materiality and thesis relevance.

Direction hints are:

```text
support/consistency metadata
```

not deterministic output labels.

---

# 18. Changed-state validation rule

For:

```text
STRENGTHENED
```

or:

```text
WEAKENED
```

preserve:

```text
at least one selected eligible observed-change ref is required.
```

If one or more selected eligible refs have safe directional hints:

```text
the observed changed state must be supportable
by at least one selected eligible ref
OR
the selected eligible set must include a genuinely direction-unspecified ref
whose semantics allow AI directional judgment.
```

Do not reject merely because another selected eligible ref
supports the opposite direction.

Counterevidence is allowed.

---

# 19. Hard contradiction should require complete contradiction

A hard:

```text
BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE
```

should be issued only when the selected eligible evidence
provides enough safe direction information to prove contradiction.

Preferred rule:

```text
If every selected eligible ref that can support a changed state
has a known safe direction,
and none supports the observed direction,
then reject.
```

If selected eligible evidence includes:

```text
a direction-unspecified but valid observed-change item
```

the validator cannot claim deterministic contradiction solely from
other opposite hints.

This is important for:

```text
inventory / receivables / context-dependent operational changes.
```

Do not turn unknown direction into positive or negative automatically.

---

# 20. Direction-unspecified evidence still requires observed change lineage

A ref with:

```text
supported_change_directions = []
```

may participate in AI_JUDGMENT only if it is already:

```text
ELIGIBLE_OBSERVED_CHANGE
```

It must have safe observed-change/baseline lineage.

Do not use:

```text
current single-point fact

stored thesis

market expectation

configured signal

price/timing/supply
```

as an unspecified-direction escape hatch.

---

# 21. UNRESOLVED validation

Preserve the M12AI principle:

```text
UNRESOLVED requires actual eligible change ambiguity/conflict.
```

Valid examples:

```text
selected safe positive and safe negative delta evidence

selected observed-change evidence with materially direction-unspecified semantics

baseline comparability conflict already admitted by the gate
```

No evidence remains:

```text
UNCHANGED_ONLY
```

not UNRESOLVED.

---

# 22. FIC-FIN-02 exact offline repair expectation

Before any model call,
rebuild the exact M12AI FIC-FIN-02 capability view.

Expected:

```text
capability =
AI_JUDGMENT

eligible refs =
E01
E04
E08
E10
```

Required direction hints:

```text
E01 → WEAKENED

E08 → WEAKENED

E10 → STRENGTHENED
```

Expected for E04:

```text
no automatic direction
```

unless a separately proven working-capital polarity contract exists.

---

# 23. Exact M12AI output offline revalidation

Revalidate the exact stopped Stage 1 candidate:

```text
business_thesis_change =
WEAKENED

selected context refs =
E06
E01
E10
```

Expected result after repair:

```text
business-delta capability validation = PASS
```

because:

```text
E01 supports WEAKENED

E10 supports STRENGTHENED

mixed evidence is allowed

E06 is baseline context
```

Do not rewrite the model output.

The historical M12AI result remains a stopped generation.

This is an offline repair proof only.

---

# 24. FIC-FIN-01 typed cash-conversion regression

FIC-FIN-01 has typed cash-conversion comparisons where:

```text
OCF higher than prior comparable

OCF less PPE acquisition cash outflow higher than prior comparable
```

Required direction hints:

```text
STRENGTHENED
```

even if separate prose evidence also supports strengthening.

This proves typed propagation is not one-sided.

---

# 25. Working-capital non-forcing fixture

Use FIC-FIN-02 E04 or an equivalent deterministic fixture:

```text
inventory 240
vs
prior year-end 150
```

Expected:

```text
ELIGIBLE_OBSERVED_CHANGE

direction hint =
NONE
```

unless additional typed context proves whether the change
is economically favorable or unfavorable.

Do not map:

```text
higher inventory → WEAKENED
```

universally.

---

# 26. Cash-conversion deterministic fixtures

At minimum:

## DIR-CASH-01

```text
OCF current 180
prior comparable 110
verified
→ STRENGTHENED
```

## DIR-CASH-02

```text
OCF current 40
prior comparable 100
verified
→ WEAKENED
```

## DIR-CASH-03

```text
OCF current 100
prior comparable 100
→ no direction hint
```

## DIR-CASH-04

```text
OCF less PPE current 130
prior comparable 70
verified
→ STRENGTHENED
```

## DIR-CASH-05

```text
OCF less PPE current -20
prior comparable 55
verified
→ WEAKENED
```

## DIR-CASH-06

```text
unverified comparison
→ no safe direction / existing ambiguous policy
```

---

# 27. Period/comparability fixtures

Do not derive polarity if period comparison is unsafe.

At minimum:

```text
QTD vs prior QTD comparable → eligible

YTD vs prior YTD comparable → eligible

point-in-time vs valid prior point-in-time → potentially eligible by metric contract

QTD vs YTD → no safe directional hint

incomparable duration → no safe directional hint

currency/security/accounting basis mismatch → no safe directional hint
```

Preserve existing QTD/YTD and ADR/security safety.

---

# 28. Text-hint fallback remains bounded

For non-typed controlled/events:

```text
explicit textual improve/deteriorate hints
```

may remain.

But typed financial evidence must prefer:

```text
typed numeric/semantic direction
```

over free-text parsing.

Do not add generic:

```text
higher/lower
```

to `_explicit_direction_hints`
as the primary fix.

---

# 29. Business-delta capability itself should not change

After direction-hint repair,
the following must remain identical to M12AI
for the same frozen fictional inputs:

```text
capability

eligible_change_refs

baseline_context_refs

ambiguous_change_refs

allowed_business_thesis_changes
```

Only:

```text
eligible_change_direction_hints
```

should change for the affected typed comparisons.

Required:

```text
capability_classification_change_count = 0
```

unless an independently documented bug is found.

Do not broaden scope.

---

# 30. Dynamic schema remains unchanged

Preserve:

```text
UNCHANGED_ONLY → ["UNCHANGED"]

AI_JUDGMENT →
["STRENGTHENED","UNCHANGED","WEAKENED","UNRESOLVED"]

INPUT_AMBIGUOUS → pre-model hard stop
```

No post-model override.

No scorecard.

No majority vote.

---

# 31. Model-facing direction view change requires new proof

Although the candidate schema capability does not change,
the model-facing business-delta direction view changes.

Therefore:

```text
a NEW full fictional generation is required.
```

Do not resume M12AI.

Do not reuse M12AI run-1 Stage 1 output
as part of formal proof.

---

# 32. Proof-critical model/runtime

Use:

```text
gpt-5.6-sol / xhigh
```

Runtime:

```text
MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second watchdog

wrapper auto-retry = 0

batch split = 0
```

No Astra.

No fallback.

No timeout increase.

---

# 33. Full fictional reproof topology

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

Three repetitions:

```text
Stage 1 = 6 calls

Stage 2 = 6 calls

total = 12 calls

final outputs = 24
```

No judge calls.

---

# 34. Fictional stop policy

Stop only for:

```text
runtime/schema hard failure

invalid evidence identity

objective financial semantic failure

business-delta capability/schema violation

business-delta proven direction contradiction

price/technical/supply Core contamination

Stage 2 core mutation
```

Do NOT stop for:

```text
valid mixed evidence

same-direction calibration variance

primary threshold variance

valid AI_JUDGMENT materiality variance

new-buyer variance

holder variance

confidence variance
```

Collect all 24 outputs if hard gates pass.

---

# 35. Fictional acceptance — direction propagation

Across all fictional inputs require:

```text
typed_direction_eligible_item_count

typed_direction_hint_count

typed_direction_projection_mismatch_count = 0

unsafe_metric_auto_direction_count = 0

business_delta_capability_violation_count = 0
```

FIC-FIN-02 must no longer false-reject
a grounded `WEAKENED` mixed-evidence judgment
solely because cash-conversion direction metadata disappeared.

---

# 36. FIC-FIN-06 remains materiality test

Do not force:

```text
STRENGTHENED
```

or:

```text
UNCHANGED
```

for FIC-FIN-06.

If eligible observed improvement exists,
the AI must judge whether the improvement
materially validates the stored investment logic.

Any remaining variation after evidence-direction repair is:

```text
BUSINESS_DELTA_MATERIALITY_AMBIGUITY
```

not evidence-surface propagation failure.

---

# 37. FIC-FIN-05 / FIC-FIN-08 remain diagnostic

Do not change:

```text
primary boundary policy

holder policy
```

in M12AJ.

Collect:

```text
FIC-FIN-05 primary direction stability

FIC-FIN-08 holder stability
```

for later combined policy review.

---

# 38. Monitored shadow authorization

If fictional generation has:

```text
12 / 12 model calls complete

24 / 24 schema-valid final outputs

zero objective hard semantic failure

zero business-delta capability violation

zero core mutation
```

then run the full active-monitored shadow.

Do NOT require perfect decision-material stability.

Existing monitored names are exposed diagnostics.

---

# 39. Active monitored universe

Re-enumerate active monitored stocks read-only at shadow start.

Last verified reference count:

```text
22
```

Use actual current active list.

No registration/stop mutation.

---

# 40. Frozen same-packet shadow

For each active ticker:

```text
one reproducible local packet

same packet hash for:
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

# 41. Shadow topology

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

No fresh unseen names.

---

# 42. Same delta view across architecture paths

For each monitored ticker,
monolithic and Stage 1 must receive semantically identical:

```text
BusinessDeltaEvidenceCapability

eligible_change_refs

baseline_context_refs

eligible_change_direction_hints
```

Required:

```text
monolithic_stage1_delta_view_equality = PASS
```

This is essential for interpreting architecture differences.

---

# 43. Shadow hard-stop policy

Stop only for:

```text
runtime/schema failure

packet hash mismatch

invalid evidence identity

objective financial semantic failure

business-delta capability violation

proven business-delta direction contradiction

price/technical/supply Core contamination

financial-sector framework misuse

ADR/security-basis violation

Stage 2 core mutation

production-side-effect attempt
```

Do not stop for architecture decision differences.

Collect the cohort.

---

# 44. Shadow comparison taxonomy

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

Delta-specific sublabels:

```text
DELTA_UNCHANGED_ONLY

DELTA_AI_JUDGMENT

DELTA_MATERIALITY_DIFFERENCE

DELTA_EVIDENCE_SELECTION_DIFFERENCE

DELTA_DIRECTION_HINT_DIFFERENCE
```

---

# 45. Real delta-direction audit

For monitored `AI_JUDGMENT` names,
report:

```text
eligible typed comparison refs

safe propagated direction hints

direction-unspecified eligible refs

monolithic selected delta refs

Stage 1 selected delta refs

business_thesis_change
```

This will show whether the fictional FIC-FIN-02 issue
also matters in real monitored packets.

---

# 46. No automatic direction for working capital

In real shadow names,
do not auto-label:

```text
inventory increase

receivables increase

working-capital increase
```

as strengthened/weakened
unless an already-frozen safe semantic contract explicitly supports it.

The AI may interpret direction from business context
when the observed-change lineage is valid.

The deterministic layer must not invent that economic judgment.

---

# 47. Existing successful repairs remain frozen

Preserve:

```text
price/timing monitoring ownership

financial risk temporal scope

conditional/prospective net-debt scope

financial-sector contrastive exclusion

QTD/YTD semantics

WC grounding

debt completeness

ADR/security basis

business-delta absolute-state prohibition

two-stage Core → Stance ownership
```

No reopening.

---

# 48. Main integration remains frozen

Do not:

```text
fetch/merge newer main

merge integration branch into main
```

Run on current integrated-main lineage.

Final main merge remains blocked.

---

# 49. Production side-effect firewall

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

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Schedules remain paused.

---

# 50. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12aj-scope-freeze

04-integrated-main-lineage-freeze

05-m12ai-fic-fin-02-failure-reproduction

06-fic-fin-02-typed-comparison-forensic

07-current-direction-hint-derivation-code-audit

08-direction-hint-projection-root-cause

09-safe-financial-metric-polarity-review

10-direction-hint-architecture-decision
```

---

# 51. Required typed-direction artifacts

Produce:

```text
11-financial-comparison-direction-contract

12-safe-polarity-registry

13-cash-conversion-polarity-contract

14-unsafe-context-dependent-metric-contract

15-typed-direction-derivation-service

16-direction-hint-projection-contract

17-model-view-direction-hint-equality-proof

18-mixed-evidence-direction-validation-contract

19-direction-unspecified-evidence-contract

20-unresolved-mixed-direction-contract
```

---

# 52. Required exact replay artifacts

Produce:

```text
21-fic-fin-02-capability-view-before-after

22-fic-fin-02-exact-m12ai-output-offline-revalidation

23-fic-fin-01-positive-cash-conversion-direction-replay

24-working-capital-non-forcing-replay

25-m12ai-capability-classification-nonchange-proof
```

---

# 53. Required deterministic fixtures

Produce at minimum:

```text
26-cash-conversion-direction-fixtures

27-period-comparability-direction-fixtures

28-mixed-positive-negative-evidence-fixtures

29-partial-direction-hint-fixtures

30-direction-unspecified-observed-change-fixtures

31-current-business-delta-validator-regression

32-unchanged-only-schema-regression
```

---

# 54. Test gate before model calls

Require:

```text
latest result integrity PASS

FIC-FIN-02 exact offline revalidation PASS

E01 → WEAKENED

E08 → WEAKENED

E10 → STRENGTHENED

E04 direction unspecified

capability classification unchanged

dynamic schema unchanged

no unsafe metric polarity

direction projection mismatch = 0

prior business-delta regressions PASS

financial semantic regressions PASS

temporal-scope regressions PASS

monitoring ownership regressions PASS

two-stage ownership regressions PASS

focused tests PASS

full local tests PASS

ruff PASS

git diff --check PASS

production firewall PASS

runner = gpt-5.6-sol / xhigh
```

---

# 55. Required fictional model artifacts

Produce:

```text
33-fictional-generation-manifest

34-fictional-delta-capability-manifest

35-fictional-direction-hint-manifest

36-stage1-run1-context01

37-stage1-run1-context02

38-stage2-run1-context01

39-stage2-run1-context02

40-stage1-run2-context01

41-stage1-run2-context02

42-stage2-run2-context01

43-stage2-run2-context02

44-stage1-run3-context01

45-stage1-run3-context02

46-stage2-run3-context01

47-stage2-run3-context02

48-fictional-hard-semantic-audit

49-fictional-business-delta-capability-audit

50-fictional-business-delta-direction-audit

51-fictional-business-delta-materiality-audit

52-fictional-primary-direction-stability

53-fictional-new-buyer-stability

54-fictional-holder-stability

55-fictional-core-immutability-audit

56-fictional-runtime-audit

57-fictional-shadow-gate-decision
```

---

# 56. Required monitored shadow artifacts

If artifact 57 authorizes shadow, produce:

```text
58-task-start-active-monitored-universe

59-shadow-packet-inventory

60-shadow-packet-hash-manifest

61-shadow-delta-capability-manifest

62-shadow-direction-hint-manifest

63-shadow-batching-manifest

64-shadow-monolithic-model-artifacts

65-shadow-stage1-model-artifacts

66-shadow-stage2-model-artifacts

67-shadow-final-composition-artifacts

68-shadow-per-ticker-comparison

69-shadow-business-delta-capability-audit

70-shadow-business-delta-direction-audit

71-shadow-core-direction-differences

72-shadow-business-delta-differences

73-shadow-new-buyer-differences

74-shadow-holder-differences

75-shadow-same-direction-calibration-differences

76-shadow-expected-contract-corrections

77-shadow-potential-architecture-regressions

78-shadow-unresolved-review-required

79-shadow-financial-sector-audit

80-shadow-adr-security-basis-audit

81-shadow-cyclical-valuation-audit

82-shadow-core-immutability-audit

83-shadow-runtime-audit

84-shadow-aggregate-summary

85-shadow-architecture-decision
```

Preserve raw model artifacts.

---

# 57. Required combined diagnostics

If full shadow completes, produce:

```text
86-fic-fin-05-vs-monitored-primary-boundary-analogs

87-fic-fin-06-vs-monitored-delta-materiality-analogs

88-fic-fin-08-vs-monitored-holder-analogs

89-real-typed-delta-direction-lessons

90-combined-fictional-monitored-root-cause-summary

91-next-bounded-policy-decision
```

---

# 58. Fresh-real readiness

At M12AJ completion:

```text
fresh_real_proof_readiness = NOT_READY
```

even if fictional and shadow both complete.

Reason:

```text
the project still needs one bounded
boundary / delta-materiality / holder policy review
using the complete clean monitored cohort.
```

Do not start a fresh unseen cohort inside M12AJ.

---

# 59. Final main merge / production

Always:

```text
final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

No main merge.

No deployment.

No monitoring resume.

---

# 60. Failure handling

## A. Typed cash-conversion polarity cannot be derived safely

```text
next_scope =
TYPED_FINANCIAL_COMPARISON_DIRECTION_ARCHITECTURE_REVIEW
```

No model calls.

## B. Repair changes capability classification

```text
STOP
BUSINESS_DELTA_CAPABILITY_SCOPE_DRIFT
```

unless independently justified.

## C. Direction-unspecified evidence creates false accepts

```text
next_scope =
BUSINESS_DELTA_PARTIAL_DIRECTION_VALIDATION_REVIEW
```

## D. Full fictional hard semantics fail

Do not run monitored shadow.

Use the smallest failing contract.

## E. Full shadow shows architecture regressions

```text
next_scope =
TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW
```

## F. Full shadow completes cleanly

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

using the full fictional + monitored evidence.

---

# 61. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch

latest_result_zip_sha256
latest_result_integrity

business_delta_direction_root_cause

financial_comparison_direction_contract_version

safe_polarity_metric_count

cash_conversion_direction_hint_count

direction_unspecified_eligible_count

direction_hint_projection_mismatch_count

unsafe_metric_auto_direction_count

capability_classification_change_count

m12ai_fic_fin_02_offline_revalidation_status

fic_fin_02_e01_direction_hints
fic_fin_02_e08_direction_hints
fic_fin_02_e10_direction_hints
fic_fin_02_e04_direction_hints

post_model_business_delta_override_count

fixed_business_delta_score_rule_count
delta_majority_vote_rule_count
delta_evidence_count_threshold_rule_count

fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total

fictional_output_count

fictional_business_delta_capability_violation_count
fictional_business_delta_direction_violation_count
fictional_business_delta_materiality_variance_subject_count

fictional_primary_direction_unstable_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count

task_start_active_monitor_count
task_start_active_monitor_tickers

shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count

shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count

shadow_business_delta_capability_violation_count
shadow_business_delta_direction_violation_count

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

shadow_core_mutation_after_stance_count

price_confirmation_core_leak_count
price_risk_reward_core_leak_count
supply_core_leak_count
timing_fact_loss_count

conditional_netdebt_false_reject_count
prospective_netdebt_false_reject_count
current_unsupported_netdebt_false_accept_count

provider_source_fetches

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

main_branch_mutations
main_merges
deployments

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

investment_judgment_model_target
investment_judgment_reasoning_effort

focused_test_result
full_test_result
ruff_result
git_diff_check

fictional_shadow_gate_status
two_stage_shadow_compatibility_classification

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 62. Artifact integrity

Freeze all artifacts before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 63. Final task principle

M12AI's main architectural idea was correct:

```text
separate absolute Core evidence
from evidence that is even capable of proving thesis change.
```

The stopped first call exposed a smaller second-order defect:

```text
typed financial comparisons were recognized as eligible change evidence

but their safe direction semantics were not propagated

→ only prose-positive E10 carried a hint

→ verified negative cash-conversion E01/E08 had no hint

→ grounded mixed-evidence WEAKENED was falsely rejected.
```

The correct M12AJ flow is:

```text
preserve the BusinessDeltaEvidenceCapability gate

→ derive safe direction from canonical typed financial comparisons

→ keep context-dependent metrics direction-unspecified

→ project typed direction into the model-facing delta view

→ make contradiction validation aware of legitimate mixed/partial-direction evidence

→ offline revalidate the exact stopped FIC-FIN-02 output

→ start a brand-new full 8 × 3 fictional generation

→ if hard semantics pass, run the full active-monitored same-packet shadow

→ only after a complete clean cohort,
   review the remaining true boundary / materiality / holder policy issues
```

Do NOT:

```text
revert the delta capability gate

add "higher/lower" as a universal text heuristic

force inventory increase to WEAKENED

force FIC-FIN-02 to WEAKENED

majority-vote outputs

post-hoc rewrite business_thesis_change

resume the stopped M12AI generation

refresh providers

merge into main

start fresh unseen proof

return to Astra

resume production monitoring
```

Carry the direction of typed evidence as typed data,
and leave economic materiality to the model.
