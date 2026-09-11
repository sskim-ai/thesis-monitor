# Thesis Monitor — Monitoring-Transition Ownership + Conditional Net-Debt Scope + Full Monitored Shadow Rerun

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-monitoring-transition-ownership-conditional-netdebt-scope-and-full-shadow-rerun.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-monitoring-transition-ownership-conditional-netdebt-scope-full-shadow-rerun-report.zip
```

Master-workflow phase:

```text
M12AG — Integrated-Main Evidence-Ownership Repair
         A. Price/Technical Monitoring Transition Ownership Repair
         B. Business-Delta Fundamental-Evidence Boundary Repair
         C. Conditional / Configured Net-Debt Claim Scope Repair
         D. Full 22-Name Monitored Shadow Rerun
         E. Combined Fictional + Monitored Diagnostic Decision
```

This task begins after M12AF.

M12AF did not reach a two-stage compatibility comparison.

The first monitored shadow context stopped after the monolithic control because three of four rows failed objective semantic validation.

The important new forensic result is that the failures are NOT one homogeneous model-quality problem.

They expose two different deterministic evidence/validator defects:

```text
1. 003690 / 005930:
price-structure monitoring transitions entered Directional Core
under a fundamental-looking evidence domain.

2. 005490:
a configured future weakening condition
"FCF 감소와 순부채 증가가 동반"
was treated as if the model had asserted current incomplete net debt.
```

M12AG must fix these deterministic ownership/scope issues first,
then rerun the monitored shadow generation from a completely NEW generation.

Do not continue or stitch M12AF context-01.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-integrated-main-monitored-shadow-diagnostic-boundary-delta-review-report.zip
```

Verified SHA-256:

```text
8ce4c2c37ecb488b1574502c71d2b1c8f307243106a9ec6b2ccb48d8705dfcb0
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest bundle:

```text
active monitored count = 22

packet available count = 22

packet unavailable count = 0

packet mismatch count = 0

planned shadow contexts = 6

planned shadow model calls = 18

attempted contexts = 1

completed model calls = 1

monolithic output tickers = 4

monolithic semantic PASS = 1

monolithic semantic FAIL = 3

two-stage comparison complete tickers = 0
```

M12AF transport:

```text
PASS
```

The failure was semantic/validation.

---

# 2. Integrated-main / two-stage architecture remains frozen

M12AG runs on the existing integrated-main branch lineage created by M12AE-R2/M12AF.

Do NOT:

```text
merge a newer main

merge integration branch into main

redesign two-stage Core → Stance architecture

change Stage 1 / Stage 2 field ownership

change holder/new-buyer contracts

change Directional thresholds
```

At task start record:

```text
integration_branch
integration_head_sha
working_tree_state
```

Verify the integrated baseline remains the M12AE-R2/M12AF lineage.

If not:

```text
STOP
UNEXPLAINED_M12AG_INTEGRATION_DRIFT
```

---

# 3. Proof-critical model/runtime — frozen

Use:

```text
model = gpt-5.6-sol
reasoning = xhigh
```

Runtime:

```text
MODEL_CONTEXT_COUPLED
up to 4 subjects/context
1800-second watchdog
wrapper auto-retry = 0
batch split = 0
```

No Astra.

No fallback.

No timeout change.

---

# 4. M12AF current monitored universe — frozen reference

M12AF successfully resolved the task-start active monitored universe:

```text
22 names
8 KRX
14 US
```

Tickers:

```text
000660
003690
005490
005930
010120
012450
047810
086280

CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

M12AG must re-enumerate active monitored names read-only at task start.

If the list differs:

```text
record the diff
use the current task-start active universe
```

Do not mutate monitoring membership.

---

# 5. M12AF frozen packets — do not refresh providers

M12AF successfully froze local packets for all 22 names.

Contract:

```text
LATEST_COMPLETE_ARCHIVED_LOCAL_AI_REVIEW_PACKET

one frozen single-stock projection per ticker

same packet for monolithic / Stage 1 / Stage 2

provider_source_fetches = 0
```

M12AG may reuse the M12AF source packet lineage
only if packet identity remains reproducible.

At rerun freeze a NEW shadow generation and compute:

```text
shadow_packet_sha256
```

again for every ticker.

Do not refresh external providers.

---

# 6. Failure 1 — 003690 business-delta claim

M12AF monolithic output:

```text
ticker = 003690

overall direction =
BUY 6.0:4.0

business_thesis_change =
STRENGTHENED
```

Model explanation included:

```text
"운영 모니터링이 재확인 구간을 지켰고
자기주식 소각이 주당가치와 자본배분 논리를 보강했다."
```

Cited:

```text
E19
E20
```

E19 in the model-facing core catalog:

```text
domain =
SECTOR_OPERATING_CURRENT

category =
earnings_quality

label =
monitoring_transition

statement =
{
  current_state: retest_held,
  previous_state: retest_in_progress,
  transition: retest_in_progress_to_retest_held
}
```

This classification is wrong.

---

# 7. 003690 E19 is actually price-structure state

The frozen source packet shows:

```text
fact_id =
monitoring:confirmation_transition
```

and the underlying monitoring state is:

```text
current.price_structure.registered_rule_state.confirmation

current state =
retest_held

previous state =
retest_in_progress

price =
14300

crossed_at =
2026-09-01
```

This is:

```text
PRICE / CHART CONFIRMATION STATE
```

not:

```text
business operating confirmation.
```

It must NOT enter Directional Core as:

```text
SECTOR_OPERATING_CURRENT
earnings_quality
```

and it must NOT support:

```text
STRENGTHENED
WEAKENED
BUY/HOLD/SELL core
```

This is an evidence ownership/routing bug.

---

# 8. Failure 2 — 005930 business-delta/core contamination

M12AF 005930 output:

```text
overall direction =
HOLD 4.5:5.5 SELL_LEAN

business_thesis_change =
UNRESOLVED
```

It cited:

```text
E01 =
monitoring:confirmation_transition

E36 =
monitoring:risk_reward_transition
```

as core/business evidence.

M12AF model-facing aliases:

```text
E01:
domain = SECTOR_OPERATING_CURRENT
category = earnings_quality
label = monitoring_transition

E36:
domain = SECTOR_OPERATING_CURRENT
category = earnings_quality
label = monitoring_metric_transition
```

Both mappings are ownership violations.

---

# 9. 005930 transition facts are price/timing facts

Frozen source packet:

## E01 source

```text
monitoring:confirmation_transition

current_state =
holding_above

previous_state =
crossed

transition =
crossed_to_holding_above
```

Underlying source:

```text
price_structure.registered_rule_state.confirmation
```

## E36 source

```text
monitoring:risk_reward_transition

change_state =
deteriorated

current_ratio =
0.225714

previous_ratio =
0.649983
```

Underlying source:

```text
price_structure.risk_reward
```

These are explicitly:

```text
PRICE / TECHNICAL / ENTRY-RISK-REWARD
```

not business fundamentals.

They belong to:

```text
Price-Timing
or timing-only/shadow telemetry
```

not Directional Core.

---

# 10. Ownership invariant — hard freeze

Reassert project architecture:

```text
Price / technical / supply / chart risk-reward
cannot alter:

- Directional BUY/HOLD/SELL
- Directional balance / lean
- business_thesis_change
- business invalidation
- fundamental new-buyer stance
- fundamental holder stance
```

Price-Timing may make:

```text
new-entry timing more conservative
holder price-review pressure
```

only under the existing downstream ownership contract.

M12AG must restore this invariant for monitored archived packet projection.

---

# 11. Monitoring transition source taxonomy

Create a source-aware taxonomy.

At minimum:

```text
PRICE_CONFIRMATION_TRANSITION

PRICE_RISK_REWARD_TRANSITION

PRICE_SUPPORT_RESISTANCE_TRANSITION

SUPPLY_FLOW_TRANSITION

FUNDAMENTAL_BUSINESS_TRANSITION

FUNDAMENTAL_FINANCIAL_TRANSITION

UNKNOWN_MONITORING_TRANSITION
```

Do not classify based only on:

```text
fact_type = monitoring_transition
```

or:

```text
label contains "confirmation".
```

Use source lineage / canonical fact id / underlying monitoring-state path.

---

# 12. Canonical source ownership for known facts

At minimum freeze:

```text
monitoring:confirmation_transition
from price_structure.registered_rule_state.confirmation
→ PRICE_TIMING_ONLY

monitoring:risk_reward_transition
from price_structure.risk_reward
→ PRICE_TIMING_ONLY
```

These must not enter the Core alias catalog.

They may enter the Timing alias catalog
only if the current Price-Timing contract supports them.

If not consumed by Timing:

```text
exclude from model-facing core/timing
and retain as audit telemetry.
```

Do not force consumption.

---

# 13. Supply ownership remains separate

Likewise:

```text
supply/investor-flow transitions
```

must never be relabeled as fundamental operating transitions.

Preserve existing supply ownership.

M12AG must audit that the monitoring-transition fix
does not accidentally move supply facts into Core.

---

# 14. Business-delta evidence eligibility

For:

```text
STRENGTHENED
WEAKENED
```

supporting evidence must be:

```text
fundamental business/financial change evidence
```

Examples:

```text
same-period revenue/operating improvement

cash-conversion deterioration/improvement

debt/liquidity deterioration

customer/order change

margin change

structural competitive change

capital allocation/business event
when genuinely new relative to baseline
```

NOT:

```text
price confirmation

chart support/retest

risk-reward ratio

investor flow

technical state
```

Business delta remains a fundamental change assessment.

---

# 15. M12AF 003690 implication after ownership fix

Do NOT pre-force:

```text
UNCHANGED
```

for 003690.

After price E19 is removed from Core,
the model may still have other legitimate change evidence.

For example M12AF cited:

```text
E20 stored thesis text mentioning 2026 self-share cancellation
```

But M12AG must distinguish:

```text
current stored thesis context
vs
new change evidence relative to baseline.
```

If no supplied baseline/change fact exists:

```text
STRENGTHENED is unsupported.
```

Do not treat a favorable absolute/current thesis statement as delta evidence.

---

# 16. M12AF 005930 implication after ownership fix

Remove:

```text
price confirmation E01
risk-reward E36
```

from Directional Core.

Then business_thesis_change must be derived only from
remaining fundamental change evidence.

Do NOT pre-force:

```text
UNCHANGED
WEAKENED
STRENGTHENED
```

until the remaining packet is audited.

`UNRESOLVED` should be allowed only under the frozen business-delta contract
if genuinely conflicting/incomplete fundamental change evidence supports that state.

Do not let price signals create the conflict.

---

# 17. Failure 3 — 005490 net-debt claim false reject

M12AF 005490:

```text
overall direction =
HOLD 5.0:5.0

business_thesis_change =
UNCHANGED
```

The financial semantic validator failed:

```text
net_debt_claim_without_complete_net_debt_evidence
```

because the candidate said in:

```text
business_reevaluation_down
```

the conditional sentence:

```text
"현금창출 감소와 순부채 증가가 함께 나타나면
투자 회수 논리가 약해진다."
```

and cited E01.

This is not a current-state assertion.

---

# 18. 005490 E01 is a configured weakening condition

Frozen model-facing E01:

```text
domain =
STRUCTURAL_RISK

label =
논리 약화 조건

statement =
"FCF 감소와 순부채 증가가 동반"
```

This is a stored/configured conditional signal.

It means:

```text
IF future/verified FCF deterioration
AND net-debt increase occur,
the thesis weakens.
```

It does NOT mean:

```text
net debt is currently high

net debt currently increased

current net debt equals X
```

The validator conflated:

```text
CONFIGURED_CONDITIONAL_CHECK
```

with:

```text
CURRENT_NET_DEBT_ASSERTION.
```

---

# 19. Net-debt claim-role taxonomy

Add a bounded claim role classification.

At minimum:

```text
CURRENT_STATE_ASSERTION

CURRENT_DIRECTIONAL_BASIS

CURRENT_NUMERIC_CLAIM

CONFIGURED_CONDITIONAL_CHECK

FUTURE_REEVALUATION_CONDITION

INVALIDATION_CONDITION

UNKNOWN_OR_AMBIGUOUS
```

Complete net-debt evidence is required for:

```text
CURRENT_STATE_ASSERTION

CURRENT_DIRECTIONAL_BASIS

CURRENT_NUMERIC_CLAIM
```

It is NOT automatically required merely to mention net debt inside:

```text
CONFIGURED_CONDITIONAL_CHECK

FUTURE_REEVALUATION_CONDITION

INVALIDATION_CONDITION
```

provided the candidate does not assert the condition is currently met.

---

# 20. Configured signal vs fulfilled signal

Hard distinction:

```text
configured signal =
what WOULD strengthen/weaken/invalidate the investment logic

fulfilled signal =
evidence that the condition HAS occurred now
```

A configured signal must not become:

```text
today's directional evidence
business delta
warning
```

without supplied current evidence.

This applies beyond net debt.

Examples:

```text
"if gross margin falls below X"
does not mean margin has fallen.

"if net debt rises"
does not mean net debt rose.

"if customer concentration worsens"
does not mean concentration worsened.
```

Preserve this generic lifecycle distinction.

---

# 21. Conditional net-debt negative controls

Still FAIL:

```text
"순부채가 증가했다."
without complete net-debt evidence.

"순부채 부담이 현재 SELL 근거다."
without complete net-debt evidence.

material_directional_anchor_basis
uses unsupported net-debt current claim.

configured signal is explicitly described as fulfilled
without current evidence.
```

No false immunity from being sourced from a stored risk signal.

---

# 22. Conditional net-debt positive controls

PASS:

```text
"순부채 증가가 확인되면 논리가 약화된다."

"FCF 감소와 순부채 증가가 함께 나타나면 재평가한다."

"순부채가 늘어나는 경우가 무효화 조건이다."
```

when:

```text
wording is conditional/future/configured

no current fulfilled assertion is made.
```

No numeric net debt may be invented.

---

# 23. Directional prompt change should be unnecessary

Preferred repair locations:

```text
DecisionEvidencePacket / OwnedEvidencePacket source ownership routing

business-delta evidence eligibility validator

financial semantic claim-role validator
```

Default:

```text
model-facing Directional prompt change count = 0
```

Do not teach the model another long list of special cases
if deterministic ownership/scope can solve the issue.

If a prompt change is claimed necessary:

```text
STOP
document why deterministic evidence ownership is insufficient.
```

---

# 24. Monolithic and two-stage must receive the same corrected Core evidence surface

After ownership repair:

```text
monolithic control Core catalog

two-stage Stage 1 Core catalog
```

must both exclude price/timing-only transitions identically.

This is essential for same-packet architecture comparison.

Required per ticker:

```text
monolithic_core_catalog_sha256
two_stage_core_catalog_sha256

semantic evidence-set equality =
PASS
```

Prompt formats may differ,
but the permitted fundamental evidence identities must match.

---

# 25. Timing evidence may remain available downstream

Do not delete price transitions from the packet.

Preferred:

```text
retain canonical facts

route to Timing-only ownership
or audit telemetry

exclude from Directional Core catalog
```

This preserves downstream Price-Timing capability.

No production price/timing semantics change.

---

# 26. Source-ownership deterministic fixtures

At minimum:

## OWN-01

```text
monitoring:confirmation_transition
lineage = price_structure.registered_rule_state.confirmation
→ not Core
```

## OWN-02

```text
monitoring:risk_reward_transition
lineage = price_structure.risk_reward
→ not Core
```

## OWN-03

```text
fundamental same-period operating transition
→ Core eligible
```

## OWN-04

```text
supply transition
→ not Core
```

## OWN-05

```text
unknown monitoring transition with no trusted lineage
→ fail closed / no Core promotion
```

---

# 27. Business-delta deterministic fixtures

At minimum:

## DELTA-REAL-01

```text
price confirmation improved only
→ cannot support STRENGTHENED
```

## DELTA-REAL-02

```text
risk-reward deteriorated only
→ cannot support WEAKENED
```

## DELTA-REAL-03

```text
current favorable thesis statement only
→ does not establish STRENGTHENED
```

## DELTA-REAL-04

```text
same-period operating improvement
→ STRENGTHENED may be supported
```

## DELTA-REAL-05

```text
fundamental positive + negative change evidence conflict
→ UNRESOLVED may be supported
```

if `UNRESOLVED` is part of the current frozen enum/contract.

---

# 28. Net-debt conditional-scope deterministic fixtures

At minimum:

```text
NET-01 current unsupported net debt claim → FAIL

NET-02 current unsupported net debt directional basis → FAIL

NET-03 conditional future net-debt increase check → PASS

NET-04 configured weakening condition → PASS

NET-05 conditional text + current claim elsewhere → FAIL

NET-06 current complete net-debt typed evidence + supported assertion → PASS
```

---

# 29. Exact M12AF context-01 offline replay

Before new model calls,
replay the exact M12AF outputs through the repaired deterministic audits.

Expected:

## 005490

```text
net_debt_claim_without_complete_net_debt_evidence =
0
```

because the net-debt mention is a future/configured weakening condition.

## 003690

The old raw output may STILL fail business-delta semantics
because it used price confirmation E19 as supporting evidence.

Do not retroactively relabel that model output PASS.

Instead classify:

```text
HISTORICAL_MODEL_OUTPUT_USED_NOW-FORBIDDEN_CORE_EVIDENCE
```

## 005930

Likewise old raw output may remain invalid because E01/E36 were price/timing evidence.

This historical replay proves:

```text
validator repair is scoped correctly
and ownership repair changes future input availability.
```

Do not rewrite historical output.

---

# 30. Fictional regression non-impact proof

The ownership repair targets real monitored archived transition source classes.

Before rerunning model calls:

```text
rebuild all 8 frozen fictional Stage 1 input evidence surfaces.
```

Required:

```text
fictional Stage 1 evidence identity sets =
byte/semantic equivalent to M12AE-R2
```

If all fictional model-facing Stage 1 inputs are unchanged:

```text
do NOT rerun the 12-call fictional canary in M12AG.
```

Reuse M12AE-R2 fictional architecture/hard-semantic proof
for non-affected source classes.

If any fictional Stage 1 prompt/evidence identity changes:

```text
STOP
M12AG_FICTIONAL_INPUT_DRIFT_REQUIRES_REPROOF
```

Next scope must include a new fictional proof.

This avoids unnecessary model calls.

---

# 31. Shadow rerun authorization

If deterministic repair passes
and fictional non-impact proof passes:

```text
run a completely NEW monitored shadow generation.
```

Do not resume M12AF.

Do not reuse its context-01 outputs as comparison data.

Use current task-start active monitored universe.

One monolithic + one Stage 1 + one Stage 2 comparison per ticker.

---

# 32. Full shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total shadow calls = 3 × context_count
```

At 22 names:

```text
18 calls
```

No repetitions.

No judge calls.

No fresh unseen issuers.

---

# 33. Shadow hard-stop policy

Stop only for:

```text
runtime/schema hard failure

same-packet mismatch

invalid evidence identity

objective financial semantic failure under the corrected contracts

Stage 2 core mutation

production side-effect attempt
```

Do NOT stop merely because monolithic and two-stage decisions differ.

Architecture differences must be collected across the full monitored cohort.

---

# 34. Monolithic control after ownership repair

The frozen monolithic control PROMPT CONTRACT remains the same.

But its permitted Core evidence catalog changes due to corrected ownership routing.

Therefore record a new:

```text
m12ag_monolithic_core_evidence_contract_sha256
```

Do not falsely claim byte-for-byte prompt equality with M12AF.

The semantics changed intentionally only by:

```text
removing Timing-owned monitoring transitions from Core.
```

No stance or ordinal contract change.

---

# 35. Same-packet architecture comparison remains valid

For every ticker:

```text
one frozen packet hash
```

feeds both architecture paths.

Within that packet:

```text
Core evidence ownership rules
must be identical
for monolithic and Stage 1.
```

Stage 2 receives:

```text
same fundamental evidence catalog
+
frozen Stage 1 core.
```

No provider refresh.

---

# 36. Shadow comparison taxonomy — preserve

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

NOT_COMPARABLE_PACKET_UNAVAILABLE

NOT_COMPARABLE_PACKET_MISMATCH
```

Do not assume monolithic control is ground truth.

Do not assume two-stage is ground truth.

---

# 37. Expected correction after ownership repair

If a monolithic/two-stage output differs from historical monitoring because
price/technical transitions no longer contaminate Core:

```text
label the difference relative to historical output as:
EXPECTED_OWNERSHIP_CORRECTION
```

But within the M12AG same-packet comparison,
both monolithic and two-stage receive the same corrected ownership,
so such differences should not arise merely from control-vs-two-stage architecture.

---

# 38. Special monitored reviews

## 003690

Verify:

```text
price confirmation transition absent from Core

insurance framework preserved

business delta based only on fundamental change evidence
```

## 005930

Verify:

```text
price confirmation and risk-reward transitions absent from Core

HBM/business evidence remains

business delta no longer uses chart/risk-reward state
```

## 005490

Verify:

```text
configured "FCF 감소 + 순부채 증가" weakening condition
may appear in reevaluation_down
without current net-debt completeness false reject

but is not treated as currently fulfilled.
```

## SKHY

Preserve ADR/security-basis safety.

---

# 39. Price-Timing non-regression

Because monitoring price transitions are re-routed,
audit Timing ownership.

Required:

```text
no timing-owned fact lost from packet canonical evidence

no Directional Core contamination

Price-Timing current deterministic tests PASS
```

Do not require Price-Timing AI to use every re-routed transition.

Ownership availability is sufficient.

---

# 40. Source-sufficiency / lifecycle no-change

Required:

```text
source_sufficiency_semantic_change_count = 0

monitoring_lifecycle_semantic_change_count = 0

warning_semantic_change_count = 0

notification_semantic_change_count = 0
```

Do not change warning lifecycle.

Do not turn configured signal into fulfilled warning.

---

# 41. Production side-effect firewall

Required:

```text
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

# 42. Main integration remains frozen

Do not merge newer main.

Do not merge integration branch into main.

M12AG works on the current integrated branch lineage.

Final main merge remains blocked.

---

# 43. Required artifacts — provenance / forensic

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ag-scope-freeze

04-integrated-main-lineage-freeze

05-m12af-context01-failure-reproduction

06-003690-price-confirmation-lineage-forensic

07-005930-price-confirmation-lineage-forensic

08-005930-risk-reward-lineage-forensic

09-monitoring-transition-domain-misclassification-root-cause

10-005490-conditional-netdebt-false-reject-forensic

11-netdebt-claim-role-root-cause
```

---

# 44. Required ownership repair artifacts

Produce:

```text
12-monitoring-transition-source-taxonomy

13-price-confirmation-ownership-contract

14-price-risk-reward-ownership-contract

15-supply-transition-ownership-freeze

16-core-vs-timing-routing-before-after

17-monolithic-core-catalog-before-after

18-two-stage-stage1-core-catalog-before-after

19-core-catalog-semantic-equality-proof
```

---

# 45. Required business-delta artifacts

Produce:

```text
20-business-delta-fundamental-evidence-eligibility-contract

21-price-transition-delta-negative-controls

22-fundamental-transition-delta-positive-controls

23-003690-post-routing-delta-evidence-audit

24-005930-post-routing-delta-evidence-audit
```

No model result should be pre-forced.

---

# 46. Required net-debt scope artifacts

Produce:

```text
25-netdebt-claim-role-contract

26-configured-vs-fulfilled-signal-contract

27-netdebt-conditional-positive-fixtures

28-netdebt-current-assertion-negative-fixtures

29-005490-exact-offline-replay
```

---

# 47. Required regression artifacts

Produce:

```text
30-m12af-historical-output-replay

31-fictional-stage1-input-nonimpact-proof

32-price-timing-ownership-regression

33-financial-hard-semantic-regressions

34-business-delta-regressions

35-source-sufficiency-no-change

36-monitoring-lifecycle-no-change

37-warning-notification-no-change
```

If artifact 31 finds fictional input drift:

```text
STOP
NO SHADOW MODEL CALLS
```

---

# 48. Required deterministic validation artifacts

Produce:

```text
38-focused-test-results

39-full-local-test-results

40-ruff-and-diff-results

41-hosted-ci-portability-observation

42-shadow-model-call-gate
```

No model calls before artifact 42 PASS.

---

# 49. Required full shadow artifacts

If gate passes:

```text
43-shadow-generation-manifest

44-task-start-active-monitored-universe

45-shadow-packet-inventory

46-shadow-packet-hash-manifest

47-shadow-batching-manifest

48-shadow-monolithic-model-artifacts

49-shadow-stage1-model-artifacts

50-shadow-stage2-model-artifacts

51-shadow-final-composition-artifacts

52-shadow-per-ticker-comparison

53-shadow-core-direction-differences

54-shadow-business-delta-differences

55-shadow-new-buyer-differences

56-shadow-holder-differences

57-shadow-same-direction-calibration-differences

58-shadow-expected-contract-corrections

59-shadow-potential-architecture-regressions

60-shadow-unresolved-review-required

61-shadow-financial-sector-audit

62-shadow-adr-security-basis-audit

63-shadow-cyclical-valuation-audit

64-shadow-core-immutability-audit

65-shadow-runtime-audit

66-shadow-aggregate-summary

67-shadow-architecture-decision
```

Preserve raw prompt/schema/output/receipt/log/run documents.

---

# 50. Required combined diagnostics

Produce:

```text
68-fic-fin-05-vs-monitored-leverage-analogs

69-fic-fin-06-vs-monitored-fundamental-delta-analogs

70-fic-fin-08-vs-monitored-holder-analogs

71-business-delta-real-packet-lessons

72-combined-fictional-monitored-root-cause-summary

73-next-bounded-repair-decision
```

---

# 51. Fresh-real readiness remains blocked

M12AG is still a diagnostic/repair shadow task.

At completion:

```text
fresh_real_proof_readiness = NOT_READY
```

even if shadow compatibility is clean.

Reason:

```text
the next semantic/policy decision
must incorporate the completed monitored shadow evidence.
```

Do not start fresh unseen proof here.

---

# 52. Final main merge remains blocked

Always:

```text
final_main_merge_readiness = NOT_READY
```

in M12AG.

No merge into main.

No deployment.

---

# 53. Failure handling

## A. Ownership routing cannot distinguish price vs fundamental transition

```text
next_scope =
MONITORING_EVIDENCE_LINEAGE_ARCHITECTURE_REVIEW
```

No model calls.

## B. 005490 conditional net-debt scope cannot be resolved generically

```text
next_scope =
FINANCIAL_CLAIM_TEMPORAL_SCOPE_ARCHITECTURE_REVIEW
```

## C. Fictional inputs drift due ownership repair

```text
next_scope =
FULL_FICTIONAL_REPROOF_AFTER_OWNERSHIP_ROUTING_CHANGE
```

No monitored shadow.

## D. Shadow has potential architecture regressions

```text
next_scope =
TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW
```

## E. Shadow shows systematic business-delta changes

```text
next_scope =
BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW_ON_INTEGRATED_MAIN
```

## F. Shadow is clean except synthetic boundary cases

```text
next_scope =
DECISION_BOUNDARY_AND_DELTA_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

Use full shadow evidence.

---

# 54. Program-completion fields

Include at least:

```text
base_integration_head_sha

integration_branch

latest_result_zip_sha256
latest_result_integrity

monitoring_transition_ownership_root_cause

price_confirmation_core_leak_count_before
price_confirmation_core_leak_count_after

price_risk_reward_core_leak_count_before
price_risk_reward_core_leak_count_after

supply_core_leak_count_after

business_delta_price_evidence_violation_count

netdebt_claim_role_root_cause
conditional_netdebt_false_reject_count
current_unsupported_netdebt_false_accept_count

m12af_003690_historical_replay_status
m12af_005930_historical_replay_status
m12af_005490_historical_replay_status

fictional_stage1_input_drift_count

investment_judgment_model_target
investment_judgment_reasoning_effort

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

shadow_runtime_timeout_count
shadow_runtime_capacity_failure_count
shadow_runtime_orphan_count
shadow_wrapper_retry_count

shadow_financial_sector_framework_failure_count
shadow_adr_security_basis_failure_count
shadow_cyclical_valuation_framework_failure_count

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

two_stage_shadow_compatibility_classification

fic_fin_05_combined_diagnostic_classification
fic_fin_06_combined_diagnostic_classification
fic_fin_08_combined_diagnostic_classification

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

Anything not measured:

```text
NOT_MEASURED
```

---

# 55. Artifact integrity

Freeze all artifacts before final index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 56. Final task principle

M12AF did not demonstrate that the two-stage architecture regressed
three of the first four monitored stocks.

It demonstrated that the frozen monolithic control itself
was being fed / validated incorrectly for real archived monitoring packets.

The key findings are:

```text
003690:
a PRICE confirmation/retest transition
was mislabeled as SECTOR_OPERATING_CURRENT
and used to support STRENGTHENED.

005930:
PRICE confirmation and PRICE risk-reward transitions
were mislabeled as fundamental operating evidence
and entered core/delta reasoning.

005490:
a configured future weakening condition
mentioning "net debt increase"
was incorrectly treated as a current incomplete-net-debt assertion.
```

These are deterministic ownership/scope defects.

The correct next flow is:

```text
route price/chart monitoring transitions out of Directional Core

→ restrict business-delta evidence to fundamental change evidence

→ distinguish configured future net-debt checks
  from current net-debt assertions

→ prove fictional inputs are unaffected

→ rerun the entire 22-name same-packet shadow from a new generation

→ only then compare monolithic vs two-stage architecture impact

→ use the completed real monitored compatibility evidence
  to choose the next semantic boundary/delta/holder repair
```

Do NOT:

```text
teach the model to reinterpret price confirmation as fundamental

map chart risk-reward deterioration to WEAKENED

remove the underlying price transition facts from the packet

allow unsupported current net-debt claims

treat a configured weakening condition as currently fulfilled

resume the stopped M12AF generation

refresh providers

merge into main

start fresh unseen proof

return to Astra

resume production monitoring
```

Fix evidence ownership first.
Then measure architecture compatibility on the actual monitored universe.
