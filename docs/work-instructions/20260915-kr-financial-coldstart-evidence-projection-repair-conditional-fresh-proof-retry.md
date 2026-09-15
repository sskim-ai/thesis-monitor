# Thesis Monitor — KR Financial Cold-Start Evidence Projection Repair + Conditional Fresh-Unseen Proof Retry

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-kr-financial-coldstart-evidence-projection-repair-conditional-fresh-proof-retry.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-kr-financial-coldstart-evidence-projection-repair-conditional-fresh-proof-retry-report.zip
```

Master-workflow phase:

```text
M12BP — KR Financial Cold-Start Input Repair
         A. Freeze M12BO pre-model stop evidence
         B. Audit the generic KR financial cold-start classification/readiness path
         C. Repair financial-holding specialized-framework classification where objectively owned
         D. Project sector-appropriate current operating evidence from official free sources
         E. Do NOT require industrial-company revenue for a valid financial-sector packet
         F. Preserve fail-closed regulatory-capital semantics; never fabricate K-ICS/CET1/etc.
         G. Prove nonfinancial companies are not accidentally reclassified
         H. Re-run the six failed KR-financial candidates pre-model
         I. If the KR financial slot becomes objectively fillable, rerun the full M12BO
            deterministic unseen selection from scratch using the same salt and exclusions
         J. Freeze a complete 12-subject cohort only after all twelve slots are filled
         K. Then conditionally run the fresh-unseen canonical proof
         L. If fresh proof passes, stop at explicit final merge/cutover approval gate
```

This task addresses ONE bounded input-contract gap discovered before any M12BO model call.

It is NOT a semantic-rule repair.

Do NOT reopen:

```text
directional-core-semantic-audit-v1

FCF semantics

net-debt semantics

working-capital grounding

financial-sector model-output semantics

ConfiguredSignalEvidenceView

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

holder / new-buyer / primary-boundary policy

Persistence V2.
```

Do NOT add a candidate-specific exception such as:

```text
if ticker == "000810": pass
```

The repair must be generic for KR financial issuers.

---

# 1. Authoritative latest result

Authoritative result bundle:

```text
thesis-monitor-20260914-new-fresh-unseen-real-proof-canonical-integrated-pipeline-report.zip
```

Verified SHA-256:

```text
a05f115fde647f9d43abac99b8e0bc935d2b10e06f3882e310775a4cb9e9abe8
```

Recompute independently.

Sidecar must match exactly.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent archive result:

```text
artifact_count = 143

ZIP entries =
143 indexed payloads
+ artifact-index.json
= 144

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0.
```

Recompute independently.

---

# 2. M12BO authoritative stop state

M12BO:

```text
status = STOP_BEFORE_MODEL

top_level_fresh_proof_result =
FRESH_UNSEEN_PREMODEL_CONTRACT_GAP

fresh_target_subject_count = 12

fresh_selected_subject_count = 11

fresh_kr_subject_count = 5

fresh_us_subject_count = 6

fresh_financial_subject_count = 1

model_calls_started = 0

model_calls_completed = 0

planned_model_call_count = 0

post_freeze_subject_replacement_count = 0.
```

No complete subject freeze was created.

Therefore:

```text
there is no frozen 11-subject cohort to preserve.
```

The full deterministic selection must be rerun after the bounded input repair.

---

# 3. M12BO 11 provider-ready subjects — diagnostic only

M12BO found these eleven provider-ready unseen candidates:

```text
BAC
000270
GM
018260
INTU
004170
SBUX
207940
ABBV
096770
SLB.
```

They were NOT a frozen final cohort.

Do not hard-code them into M12BP.

After the repair:

```text
re-run the original deterministic selection
with the same selection salt / candidate slots / seen-subject exclusions.
```

If provider/source state has objectively changed,
the deterministic result may change.

No manual preservation or substitution.

---

# 4. Exact missing slot

Unfilled slot:

```text
market =
kr

sector_bucket =
financial

slot =
1.
```

Six candidates were attempted:

```text
138930 — BNK금융지주

139130 — iM금융지주

000810 — 삼성화재해상보험

316140 — 우리금융지주

086790 — 하나금융지주

032830 — 삼성생명.
```

All six:

```text
identity/security = available

EARNINGS_FINANCIAL_CURRENT = available

provider attempted = true

directional_model_eligible = false.
```

No model output influenced this failure.

---

# 5. Exact current failure pattern — financial holdings

Affected:

```text
138930
139130
316140
086790.
```

Observed profile pattern:

```text
official_industry_code =
64992

company/legal name contains a financial-holding identity
e.g. 금융지주

current analysis_framework =
standard_operating_company

official taxonomy_key =
null

source_sufficiency =
SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY

source error =
validated_current_opendart_revenue_unavailable

missing family =
BUSINESS_CURRENTORSECTOR_OPERATING_CURRENT.
```

The four issuers are currently evaluated through an industrial-company-style
revenue readiness path despite being financial holding companies.

This is the first bounded root-cause candidate.

---

# 6. Important negative control for code 64992

Do NOT map every issuer with:

```text
official_industry_code == 64992
```

to a financial-specialized framework.

M12BO also observed examples such as:

```text
009540 — HD한국조선해양
```

whose OpenDART official industry code may also appear as `64992`
while the economic business is not a bank/insurer financial institution.

Therefore:

```text
64992 alone is NOT sufficient.
```

Classification must require a stronger authoritative issuer/business identity.

Acceptable identity signals may include, after code audit:

```text
official legal/company name semantics such as 금융지주

official profile/business classification already owned by the provider

existing canonical issuer taxonomy

financial-statement/account pattern that unambiguously identifies a financial institution.
```

Do not classify from candidate slot alone.

Do not classify from model text.

---

# 7. Exact current failure pattern — insurers

Affected:

```text
000810 — 삼성화재해상보험

032830 — 삼성생명.
```

Observed:

```text
analysis_framework =
bank_or_insurer

financial_specialized_framework =
true

identity/security =
available

EARNINGS_FINANCIAL_CURRENT =
available

directional_model_eligible =
false

missing family =
REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT

source error =
validated_current_opendart_revenue_unavailable.
```

This shows insurer taxonomy is already recognized.

The missing part is:

```text
sector-appropriate current evidence projection.
```

Do NOT solve this by inventing a generic revenue value.

---

# 8. Root-cause question

Audit the real implementation in:

```text
app/services/coldstart_fundamental_enrichment_service.py
```

plus current OpenDART enrichment/assembly helpers.

Determine separately:

```text
A. KR financial-holding identity classification gap

B. KR financial current sector-operating evidence projection gap

C. any overly generic industrial revenue readiness prerequisite.
```

Do not assume all three require code changes.

Document actual functions/branches.

---

# 9. Generic architecture target

The cold-start source sufficiency contract should distinguish:

```text
STANDARD_OPERATING_COMPANY

ASSET_HEAVY_CYCLICAL

BANK_OR_INSURER / existing financial-specialized framework.
```

For a financial-specialized issuer:

```text
validated industrial revenue
must NOT be the only way to establish current business/sector operating evidence.
```

A financial issuer may be directionally research-ready when it owns:

```text
IDENTITY_SECURITY

EARNINGS_FINANCIAL_CURRENT

and

one or more safe current sector-operating / regulatory-capital evidence families
appropriate to that financial subtype.
```

No model semantic change.

---

# 10. Financial-holding specialized classification

For KR financial holding companies,
design the smallest generic identity rule.

Preferred evidence hierarchy:

```text
1. existing canonical provider taxonomy / official profile classification

2. official OpenDART legal/company identity + official industry classification

3. deterministic financial-statement/account evidence confirming
   the financial-institution framework.
```

Do NOT use:

```text
candidate slot

expected sector

ticker allowlist

price behavior

model output.
```

If using a Korean-name signal:

```text
금융지주
```

combine it with authoritative OpenDART identity/profile evidence.

Add negative controls so ordinary holding/industrial issuers are not captured.

---

# 11. Do not rename the canonical framework casually

If the repository currently uses:

```text
AnalysisFramework.BANK_INSURER
```

as the generic financial-specialized framework,
it is acceptable to classify a financial holding company into that existing
proof-safe framework if that is what current validators/prompts expect.

Do NOT rename the enum or model-facing framework merely for aesthetics.

A rename would expand scope and could require reproof.

If the framework is genuinely semantically incapable of representing
financial holding companies:

```text
STOP
FINANCIAL_FRAMEWORK_ENUM_SCOPE_GAP
```

and report the required bounded model-facing change.

Default expectation:

```text
reuse the current financial-specialized framework.
```

---

# 12. Sector-operating evidence — principle

Introduce/repair a typed:

```text
SECTOR_OPERATING_CURRENT
```

projection for financial-specialized cold-start packets.

This is an EVIDENCE FAMILY classification.

It must not:

```text
pretend every metric is revenue

pretend an insurer metric is a bank metric

pretend regulatory capital exists when it does not

convert operating income into sales

derive ratios from incomplete denominators.
```

Store the actual official account/metric identity.

---

# 13. Safe source requirement

Use only current supported FREE official/provider sources.

For KR financial candidates:

```text
OpenDART / already supported official financial-statement interfaces
```

are preferred.

No paid API.

No manual web scraping workaround.

No hard-coded financial numbers.

No copied analyst estimates.

---

# 14. Sector-operating metric discovery

Audit the actual official statement rows returned for the six failed issuers.

Build a diagnostic inventory containing:

```text
ticker

issuer id

report period

statement type

account id if available

account name

amount

currency

current/comparative period identity

consolidated/separate basis if available.
```

Do NOT package secrets.

Use this inventory to determine which current accounts can safely satisfy
`SECTOR_OPERATING_CURRENT`.

---

# 15. Financial holding candidate metrics

For financial holding / bank-group issuers,
candidate account families may include only OFFICIALLY OBSERVED and semantically
appropriate items such as:

```text
영업수익 / operating revenue

이자수익 / interest income

순이자이익 / net interest income

수수료-related operating income

or another existing canonical bank operating metric.
```

This list is illustrative, not an instruction to fabricate aliases.

The repository code audit and actual OpenDART rows control.

Do not define:

```text
generic revenue
```

unless the official account itself is a valid revenue/operating-revenue concept
and the evidence projection preserves its financial-sector meaning.

---

# 16. Insurer candidate metrics

For insurers,
candidate sector-operating evidence may include only officially observed,
current, subtype-appropriate metrics such as:

```text
보험수익 / insurance revenue

insurance service result

underwriting / insurance operating result

or another existing canonical insurance operating metric.
```

Again:

```text
only if actually returned and safely identified.
```

Do not force a bank metric onto insurers.

---

# 17. Regulatory capital — no fabrication

Current readiness allows:

```text
REGULATORY_CAPITAL_CURRENT
OR
SECTOR_OPERATING_CURRENT.
```

Preserve the OR.

Do NOT fabricate regulatory capital from balance-sheet equity.

Do NOT infer:

```text
K-ICS

RBC

CET1

BIS ratio

capital adequacy
```

from unrelated statement values.

If an official current regulatory-capital metric is already available through a
supported provider, it may be projected with exact source identity.

Otherwise use safe sector-operating evidence if available.

If neither exists:

```text
remain SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY.
```

---

# 18. Current-period validity

A sector-operating metric may satisfy readiness only if:

```text
current enough under the existing cold-start freshness contract

period identity is known

statement basis is known enough for safe use

amount parses safely

currency is known or inherited from the official statement contract.
```

Do not use an old arbitrary annual metric merely to make the slot pass.

Preserve source/as-of dates.

---

# 19. Consolidated/separate basis

For financial holding companies,
prefer the existing repository policy for:

```text
consolidated vs separate financial statements.
```

Do not mix:

```text
holding-company separate statements
```

with:

```text
group consolidated operating metrics
```

without explicit basis.

If the current cold-start service already prioritizes consolidated statements,
preserve that behavior.

If basis is ambiguous:

```text
fail closed.
```

---

# 20. Evidence-family payload

For every projected financial sector-operating fact,
preserve at least:

```text
metric family

original official account identity

human-readable label

amount

currency

period

basis

source/provider

source as-of / filing identity.
```

Do not overwrite the original account name with a generic industrial label.

---

# 21. Model-facing projection

The deterministic base context may tell the model:

```text
this is a financial-sector operating metric
```

using existing financial-specialized framing.

It must NOT say:

```text
revenue grew
```

unless that exact meaning is supported.

It must NOT call:

```text
regulatory capital
```

unless an actual regulatory-capital metric exists.

No financial semantic overclaim.

---

# 22. Source sufficiency logic

Repair the sufficiency gate so:

### Standard operating company
Preserve existing rule.

### Financial-specialized company
Require:

```text
IDENTITY_SECURITY

EARNINGS_FINANCIAL_CURRENT

and one of:
  SECTOR_OPERATING_CURRENT
  REGULATORY_CAPITAL_CURRENT
```

plus all existing packet validation requirements.

Do not require:

```text
validated_current_opendart_revenue
```

as an independent mandatory condition for financial-specialized issuers.

---

# 23. Error-code behavior

Replace the misleading financial-sector failure:

```text
validated_current_opendart_revenue_unavailable
```

with an accurate subtype/source reason when relevant.

Examples:

```text
current_financial_sector_operating_evidence_unavailable

current_regulatory_capital_evidence_unavailable
```

or repository-equivalent typed codes.

Do not hide the original provider/source diagnostic.

---

# 24. Exact six-candidate replay

After repair, rerun the six exact M12BO failed KR financial candidates:

```text
138930
139130
000810
316140
086790
032830.
```

This is a pre-model provider/input replay.

Report per ticker:

```text
official profile identity

analysis framework before / after

evidence families before / after

current financial metric identities

source sufficiency

directional model eligibility

packet validation errors

packet hash if eligible.
```

No model calls during this replay.

---

# 25. Repair acceptance — classification coverage

Deterministic fixture coverage must include:

```text
financial holding positive

insurance positive

nonfinancial 64992 negative control

ordinary industrial negative control.
```

Expected:

```text
financial holding is not blocked merely by missing industrial revenue

insurer can use safe sector-operating evidence if available

nonfinancial holding/company is not reclassified as financial.
```

---

# 26. Live/provider acceptance

The live/provider replay does NOT need all six to become eligible.

It must show:

```text
the generic contract works
```

and at minimum make the KR financial slot objectively fillable
if current official data supports any of the six candidates.

Required before full M12BO retry:

```text
at least one eligible unseen KR financial candidate
with financial-specialized framework
and safe current sector/regulatory evidence.
```

Preferred diagnostic:

```text
at least one financial-holding candidate
and
at least one insurer candidate
are evaluated correctly,
whether READY or LIMITED for source-specific reasons.
```

Do not lower sufficiency merely to hit this target.

---

# 27. No candidate-specific waiver

Forbidden:

```text
allow 000810 despite missing family

allow first financial slot candidate anyway

treat EARNINGS_FINANCIAL_CURRENT alone as sufficient

mark missing metric as unknown but still READY

use company-name allowlist to bypass source evidence.
```

Identity classification and evidence sufficiency are separate.

Both must pass.

---

# 28. Regression — nonfinancial cold start

Re-run representative current fixtures for:

```text
standard operating company

asset-heavy/cyclical

technology

consumer/service

healthcare

energy/materials.
```

Required:

```text
no readiness broadening from financial repair

no revenue rule weakening for nonfinancials

no packet semantic hash changes unrelated to financial projection.
```

---

# 29. Regression — monitored path

M12BP must not alter:

```text
monitored semantic services

M12BJ shadow outputs

Persistence V2.
```

Run relevant regression tests.

No monitored model calls.

No monitored re-shadow.

---

# 30. Regression — canonical semantic hashes

Expected:

```text
model prompt semantic change count = 0

model schema semantic change count = 0

canonical semantic service change count = 0

decision-policy change count = 0

Persistence V2 contract change count = 0.
```

Cold-start financial evidence projection may change deterministic input packet content
for affected KR financial issuers.

That is the intended bounded input change.

---

# 31. Model-call gate

NO fresh model call is allowed until all are true:

```text
focused repair tests PASS

six-candidate replay complete

nonfinancial controls PASS

at least one KR financial candidate objectively eligible

no model-facing semantic/schema change

production firewall PASS.
```

If not:

```text
STOP_BEFORE_MODEL
KR_FINANCIAL_COLDSTART_REPAIR_INCOMPLETE.
```

---

# 32. M12BO selection retry

Because M12BO:

```text
created no complete subject freeze

started zero model calls,
```

after the repair gate passes:

```text
rerun the FULL original M12BO selection from scratch.
```

Preserve:

```text
same TARGET_TOTAL = 12

same 6 KR / 6 US balance

same sector slots

same candidate pool unless the pool itself is proven invalid

same selection salt:
M12BO-20260914-FRESH-UNSEEN-V1

same seen-subject registry contract.
```

Do not manually preserve the prior eleven.

---

# 33. Seen registry on retry

Rebuild the project-wide seen-subject registry at retry time.

Important:

The prior M12BO pre-model run created:

```text
no model artifacts
```

for the eleven selected candidates.

Therefore being “selected but never modeled” in the failed M12BO attempt
must NOT automatically mark them as prior fresh model subjects.

However:

```text
the M12BO report itself is historical proof metadata.
```

Ensure the registry contract distinguishes:

```text
MODELED/DECIDED PRIOR SUBJECT
```

from:

```text
PREMODEL_CANDIDATE_ONLY.
```

Do not accidentally exclude all eleven merely because their tickers appear in
the M12BO preflight report.

This is a required regression fixture.

---

# 34. Seen-registry safety

Still exclude:

```text
active monitored subjects

historical fresh/new-issuer subjects that reached model decision artifacts

historical failed fresh 16

fictional subjects from real selection.
```

Do not loosen unseen integrity.

---

# 35. Complete 12-subject freeze

If and only if all twelve slots are filled:

create a NEW:

```text
fresh-unseen-subject-freeze-manifest.
```

Required:

```text
selected_count = 12

6 KR

6 US

2 financial subjects total
  at least 1 KR
  at least 1 US

all required sector buckets filled.
```

After freeze:

```text
subject replacement = 0.
```

---

# 36. Persistence applicability — preserve M12BO result

M12BO already determined:

```text
CANONICAL_RECEIPT_NOT_APPLICABLE_UNTIL_EXPLICIT_MONITORING_REGISTRATION.
```

Reason:

```text
explicit monitoring registration owns watchlist and thesis-version identity.
```

Freeze this unless repository code changed materially.

Do NOT fabricate:

```text
thesis_version = 1

watchlist item

monitoring registration.
```

Fresh proof needs no persistence receipt pre-monitoring.

---

# 37. Fresh proof retry — same core contract

After a complete 12-subject freeze,
run the M12BO proof contract.

Use:

```text
gpt-5.6-sol / xhigh.
```

No Astra.

No fallback.

No judge.

No selective rerun.

No post-hoc output edit.

One frozen attempt per planned context/stage.

---

# 38. Complete cohort even on candidate semantic failure

As in M12BO:

candidate-specific hard semantic failures should be recorded
and the remaining frozen cohort completed where infrastructure remains safe.

Do NOT:

```text
replace a failed subject

drop it from denominator

patch and rerun inside the same proof.
```

Top-level PASS still requires:

```text
12 / 12 accepted.
```

---

# 39. Fresh canonical path

Use the active fresh/new-issuer canonical path after M12BI.

Every candidate:

```text
canonical single-source semantic audit

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

applicable financial/WC/sector checks

final composition

core immutability.
```

No old fresh-only semantic fallback.

---

# 40. KR financial fresh proof — special evidence audit

For the selected KR financial subject,
produce an explicit audit:

```text
classification basis

financial-specialized framework identity

sector-operating/regulatory evidence used

official account names

period/basis/currency

no industrial revenue requirement

no fabricated regulatory capital

no generic revenue relabeling

model-facing evidence text

semantic audit result.
```

This proves the input repair did not create a false semantic shortcut.

---

# 41. Fresh proof PASS gates

Require:

```text
12 / 12 frozen packets valid

all planned model calls complete

12 / 12 schema-valid

12 / 12 canonical semantic PASS

12 / 12 final composition PASS

BusinessDelta hard failures = 0

financial semantic hard failures = 0

WC hard failures = 0

financial-sector hard failures = 0

expectation hard failures = 0

security-basis hard failures = 0

Stage-2 contamination = 0

core mutation = 0

canonical bypass = 0

legacy duplicate participation = 0

Initial Analysis lifecycle violations = 0

post-freeze replacement = 0

selective reruns = 0

production side effects = 0.
```

No decision-distribution target.

---

# 42. Production firewall

Required throughout:

```text
production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

watchlist_mutations = 0

production_thesis_version_mutations = 0

assessment_production_writes = 0

warning_production_mutations = 0

notification_production_queue_writes = 0

production_sends = 0

remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

scheduler_mutation_count = 0

automatic_monitoring_resume = 0.
```

V2 production gates remain disabled.

---

# 43. Provider policy

Use only supported FREE providers.

No paid dependency.

Report source counts.

No provider data fabrication.

No source-quality downgrade to force readiness.

---

# 44. Network failure before model call 1

If 12 subjects are frozen but model network is unavailable before call 1:

```text
preserve the frozen 12-subject identity

model_calls_started = 0

next_scope =
RETRY_SAME_FROZEN_FRESH_COHORT_WHEN_NETWORK_READY.
```

Do not reselect.

---

# 45. Network/runtime failure after model calls start

No selective retry.

Report incomplete proof.

Do not merge old/new generations.

No repair mixed into proof.

---

# 46. If KR financial repair still cannot fill the slot

If after the generic repair:

```text
no safe current sector/regulatory evidence
exists for any eligible unseen KR financial candidate
```

then:

```text
STOP_BEFORE_MODEL

top_level_result =
KR_FINANCIAL_PROVIDER_COVERAGE_LIMIT_CONFIRMED
```

and document:

```text
which official free-source evidence is unavailable

whether another supported free provider path exists

whether the proof cohort sector requirement itself must be revised.
```

Do NOT weaken the evidence requirement.

Do NOT silently replace KR financial with another sector.

---

# 47. No artificial cohort-requirement relaxation

The current proof requires a KR financial subject
to exercise the financial-specialized path.

Do not remove this requirement merely because the source is harder.

Only a later explicit workflow decision may change proof coverage.

M12BP should first exhaust the safe existing free-source projection path.

---

# 48. Main merge readiness after full fresh proof PASS

If and only if the CONDITIONAL fresh proof completes 12/12:

```text
final_main_merge_readiness =
READY_FOR_EXPLICIT_USER_APPROVAL.
```

Do not merge.

Production remains:

```text
NOT_READY_PENDING_EXPLICIT_CUTOVER_APPROVAL.
```

---

# 49. Next scope after full PASS

Required:

```text
next_scope =
FINAL_MAIN_MERGE_AND_PRODUCTION_CUTOVER_APPROVAL_GATE.
```

This requires separate explicit user approval.

No automatic cutover.

---

# 50. Next scope after input repair PASS but fresh proof FAIL

Choose one bounded scope from actual evidence:

```text
BOUNDED_FRESH_MODEL_CONTRACT_COMPLIANCE_REPAIR

BOUNDED_CANONICAL_SEMANTIC_ENGINE_REPAIR

BOUNDED_FRESH_INPUT_PACKET_REPAIR

NETWORK_RETRY_SAME_FROZEN_COHORT.
```

No mixed repair.

---

# 51. Required root-cause artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bp-scope-freeze

04-m12bo-premodel-stop-freeze

05-kr-financial-six-candidate-failure-reproduction

06-kr-financial-coldstart-call-graph

07-kr-financial-profile-taxonomy-audit

08-kr-financial-statement-account-inventory

09-financial-holding-classification-options

10-financial-holding-classification-decision

11-sector-operating-evidence-projection-options

12-sector-operating-evidence-projection-decision

13-financial-source-sufficiency-contract-after.
```

---

# 52. Required implementation artifacts

Produce:

```text
14-kr-financial-profile-classification-implementation

15-kr-financial-sector-operating-projection-implementation

16-kr-financial-source-sufficiency-implementation

17-financial-source-error-code-update

18-nonfinancial-negative-control-proof

19-financial-holding-positive-fixture

20-insurer-positive-fixture

21-no-regulatory-capital-fabrication-proof

22-no-generic-revenue-relabeling-proof.
```

---

# 53. Required pre-model replay artifacts

Produce:

```text
23-six-candidate-provider-replay

24-six-candidate-before-after-matrix

25-kr-financial-slot-fillability-decision

26-nonfinancial-coldstart-regression

27-monitored-semantic-regression

28-model-semantic-schema-hash-freeze

29-production-firewall-model-call-gate.
```

No model call before artifact 29 PASS.

---

# 54. Required conditional fresh selection artifacts

If the gate passes:

```text
30-retry-current-active-monitor-universe

31-retry-project-wide-seen-subject-registry

32-premodel-only-prior-attempt-seen-registry-regression

33-retry-candidate-universe-manifest

34-retry-provider-readiness

35-retry-sector-slot-eligibility

36-retry-selection-ranking

37-retry-fresh-unseen-subject-freeze

38-retry-selection-fairness

39-retry-no-post-freeze-replacement.
```

---

# 55. Required conditional proof artifacts

If a complete 12-subject freeze exists:

```text
40-retry-fresh-provider-source-manifest

41-retry-fresh-company-profile-manifest

42-retry-fresh-earnings-manifest

43-retry-fresh-event-evidence-manifest

44-retry-fresh-current-snapshot-manifest

45-retry-fresh-security-basis-manifest

46-retry-fresh-evidence-view-manifest

47-retry-fresh-packet-inventory

48-retry-fresh-packet-hash-manifest

49-retry-fresh-frozen-context-manifest

50-retry-fresh-model-call-plan

51-retry-fresh-model-network-readiness

52-retry-fresh-stage1-model-artifacts

53-retry-fresh-stage2-model-artifacts

54-retry-fresh-canonical-service-provenance

55-retry-fresh-business-delta-audit

56-retry-fresh-financial-semantics-audit

57-retry-fresh-working-capital-audit

58-retry-fresh-financial-sector-audit

59-retry-kr-financial-input-projection-audit

60-retry-fresh-market-expectation-audit

61-retry-fresh-direction-timing-audit

62-retry-fresh-security-basis-audit

63-retry-fresh-stage2-contamination-audit

64-retry-fresh-core-immutability-audit

65-retry-fresh-final-composition-audit

66-retry-fresh-initial-analysis-lifecycle-audit

67-retry-fresh-final-subject-matrix.
```

---

# 56. Required decisions

Produce:

```text
68-kr-financial-coldstart-repair-decision

69-fresh-unseen-proof-retry-decision

70-main-merge-readiness-decision

71-production-readiness-decision

72-next-scope-decision

73-master-workflow-update

74-program-completion.
```

---

# 57. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bo_status
m12bo_model_calls_started
m12bo_selected_subject_count
m12bo_unfilled_slot

kr_financial_failed_candidate_count
kr_financial_failed_candidates

financial_holding_candidate_count
insurer_candidate_count

financial_holding_classification_contract
financial_sector_operating_projection_contract

financial_holding_fixture_status
insurer_fixture_status
nonfinancial_64992_negative_control_status

regulatory_capital_fabrication_count
generic_revenue_relabel_count

six_candidate_replay_count
six_candidate_directional_ready_count
six_candidate_ready_tickers

kr_financial_slot_fillability_status

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_service_change_count
decision_policy_change_count
persistence_v2_contract_change_count

retry_seen_registry_status
premodel_prior_attempt_false_exclusion_count

retry_selected_subject_count
retry_selected_tickers
retry_kr_subject_count
retry_us_subject_count
retry_financial_subject_count

post_freeze_subject_replacement_count

planned_model_call_count
model_calls_started
model_calls_completed
wrapper_retry_count
fallback_model_call_count
judge_call_count
selective_rerun_count

fresh_schema_valid_count
fresh_canonical_semantic_pass_count
fresh_canonical_semantic_fail_count
fresh_final_composition_pass_count
fresh_accepted_count

fresh_business_delta_hard_failure_count
fresh_financial_semantic_hard_failure_count
fresh_working_capital_hard_failure_count
fresh_financial_sector_hard_failure_count
fresh_market_expectation_hard_failure_count
fresh_security_basis_hard_failure_count
fresh_stage2_contamination_count
fresh_core_mutation_count

proof_critical_canonical_bypass_count
legacy_duplicate_semantic_participation_count

fresh_persistence_applicability

paid_provider_dependency_count

production_db_mutations
monitoring_registrations
monitoring_stops
watchlist_mutations
production_thesis_version_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends

v2_production_writer_enabled
v2_production_read_preference_enabled
v2_production_warning_enabled
v2_production_outbox_delivery_enabled

remote_push_count
raw_model_artifact_remote_push_count
main_branch_mutations
main_merges
deployments
scheduler_mutation_count
automatic_monitoring_resume

top_level_result

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

Anything genuinely unavailable:

```text
NOT_MEASURED
```

with reason.

---

# 58. Expected bounded-repair success before model proof

Expected if the input repair works:

```text
kr_financial_slot_fillability_status =
PASS

regulatory_capital_fabrication_count = 0

generic_revenue_relabel_count = 0

nonfinancial_64992_negative_control_status = PASS

model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

canonical_semantic_service_change_count = 0.
```

Then rerun full deterministic selection.

---

# 59. Expected final clean result

If the conditional fresh proof also passes:

```text
top_level_result =
FRESH_UNSEEN_CANONICAL_PROOF_PASS_AFTER_BOUNDED_INPUT_REPAIR

retry_selected_subject_count = 12

fresh_schema_valid_count = 12

fresh_canonical_semantic_pass_count = 12

fresh_canonical_semantic_fail_count = 0

fresh_final_composition_pass_count = 12

fresh_accepted_count = 12

post_freeze_subject_replacement_count = 0

wrapper_retry_count = 0

fallback_model_call_count = 0

judge_call_count = 0

selective_rerun_count = 0

proof_critical_canonical_bypass_count = 0

legacy_duplicate_semantic_participation_count = 0

production_db_mutations = 0

monitoring_registrations = 0

warning_production_mutations = 0

notification_production_queue_writes = 0

production_sends = 0

fresh_real_proof_readiness =
PROOF_COMPLETE

final_main_merge_readiness =
READY_FOR_EXPLICIT_USER_APPROVAL

production_readiness =
NOT_READY_PENDING_EXPLICIT_CUTOVER_APPROVAL

next_scope =
FINAL_MAIN_MERGE_AND_PRODUCTION_CUTOVER_APPROVAL_GATE.
```

Do NOT force this result.

---

# 60. Failure handling

## A. Financial-holding classification requires a ticker allowlist

```text
STOP
GENERIC_FINANCIAL_IDENTITY_CONTRACT_NOT_SOLVED.
```

No model calls.

## B. Sector-operating projection requires fabricated aliases/numbers

```text
STOP
KR_FINANCIAL_OFFICIAL_SOURCE_PROJECTION_NOT_SAFE.
```

No model calls.

## C. Insurer/bank regulatory capital unavailable

This is NOT automatically fatal if:

```text
safe current SECTOR_OPERATING_CURRENT exists.
```

If neither exists:

remain source-limited.

## D. No KR financial candidate becomes safe/provider-ready

```text
STOP_BEFORE_MODEL

top_level_result =
KR_FINANCIAL_PROVIDER_COVERAGE_LIMIT_CONFIRMED.
```

No proof-coverage relaxation.

## E. Repair changes model prompt/schema or canonical semantic rules

```text
STOP
INPUT_REPAIR_SCOPE_EXPANSION_REQUIRES_REPROOF_PLAN.
```

Do not mix repair and proof.

## F. Full selection succeeds but network fails before model call 1

Freeze the 12 subjects.

```text
next_scope =
RETRY_SAME_FROZEN_FRESH_COHORT_WHEN_NETWORK_READY.
```

## G. Fresh candidate semantic failure after calls begin

Complete cohort where safe.

No patch/retry.

Top-level proof fails.

Choose bounded next scope from evidence.

---

# 61. Local/production boundary

Provider/model calls are allowed only after the bounded pre-model gate passes.

Production mutations are never allowed.

Use:

```text
FREE providers only

local proof artifacts

temporary local storage only where already supported.
```

No paid dependency.

No production migration.

No monitoring registration.

---

# 62. Artifact integrity

Before final report ZIP:

```text
all artifacts frozen

hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Report ZIP SHA-256.

Do not push raw model artifacts remotely.

---

# 63. Final task principle

M12BO did NOT fail at model reasoning.

It stopped before model call 1 because:

```text
11 / 12 slots were objectively provider-ready,

but the KR financial slot could not be filled.
```

The six KR financial candidates already had:

```text
identity/security

current earnings/financial evidence.
```

What failed was the cold-start financial-sector input contract:

```text
financial holding companies were not consistently recognized
as financial-specialized issuers,

and financial issuers did not receive a safe current
sector-operating/regulatory evidence projection,

while the source gate still surfaced an industrial-style
"current revenue unavailable" failure.
```

The correct M12BP flow is:

```text
repair the GENERIC KR financial cold-start identity/evidence projection

→ never fabricate regulatory capital

→ never relabel arbitrary financial metrics as industrial revenue

→ prove financial-holding + insurer fixtures

→ prove nonfinancial negative controls

→ replay all six failed candidates pre-model

→ if a safe KR financial candidate becomes eligible,
   rerun the FULL deterministic M12BO selection from scratch

→ freeze exactly 12 subjects

→ run the fresh canonical proof once

→ if 12/12 pass,
   stop at explicit user merge/cutover approval.
```

Do NOT:

```text
patch a ticker

drop the KR financial requirement

use EARNINGS_FINANCIAL_CURRENT alone

weaken source sufficiency

reuse the prior eleven as a manually frozen cohort

treat premodel-only ticker mentions as prior modeled subjects

change semantic validators

change decision policy

change Persistence V2

fabricate thesis_version

register monitoring

merge main

deploy

enable V2 production gates.
```
