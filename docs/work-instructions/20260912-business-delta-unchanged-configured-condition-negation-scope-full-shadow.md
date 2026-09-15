# Thesis Monitor — Business-Delta UNCHANGED / Configured-Condition Negation Scope + New Full Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260912-business-delta-unchanged-configured-condition-negation-scope-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260912-business-delta-unchanged-configured-condition-negation-scope-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AS — Integrated-Main Business-Delta UNCHANGED Claim Scope
         A. Freeze successful M12AR FCF claim-scope repair
         B. Reproduce exact SNDK UNCHANGED false reject
         C. Replace naive thesis-change substring matching with clause/claim polarity
         D. Preserve true fulfilled-change hard failures
         E. Offline re-audit M12AQ formal fictional proof
         F. Start a NEW full active-monitored same-packet shadow
         G. Complete compatibility cohort
         H. Hand off to boundary / delta-materiality / holder policy review
```

M12AR successfully repaired the intended IBM PPE-proxy / FCF claim-evidence scope problem.

The exact IBM historical candidate now passes with:

```text
candidate_global_proxy_leak_count = 0

true_proxy_as_fcf_violation_count = 0

configured_fcf_condition_count = 2

unconfirmed_fcf_summary_count = 1

financial semantic status = PASS
```

M12AR also offline re-audited the full M12AQ fictional proof and authorized reuse:

```text
formal_fictional_reuse_status = REUSE_AUTHORIZED

Stage 1 rows = 24
Stage 2 rows = 24
final financial semantic re-audit = PASS
```

The NEW monitored shadow then progressed beyond the old IBM failure boundary.

It stopped at:

```text
context-05 / Stage 1 / SNDK
```

after:

```text
14 / 18 planned shadow model calls
14 / 14 transport PASS
13 semantic PASS calls before stop
timeout = 0
orphan = 0
wrapper retry = 0
```

The only hard stop:

```text
BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE
```

on an SNDK candidate whose actual meaning was:

```text
no meaningful observed thesis change has been confirmed.
```

This is a deterministic business-delta claim-scope / negation false reject.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow-report.zip
```

Verified SHA-256:

```text
97b94a2cfd2deb7bfcfa74508eba16815d2dff74f287886545a9e3970db09456
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
artifact_count = 294
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

ZIP entries:

```text
294 indexed payloads
+ artifact-index.json
= 295
```

Recompute independently.

---

# 2. M12AR status

M12AR program status:

```text
BLOCKED_AFTER_14_OF_18_SHADOW_CALLS
```

Failure:

```text
failed_ticker = SNDK
failed_validator = post-model-business-delta-validator-v2
failed_error = BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE

root_cause_classification =
BUSINESS_DELTA_CONFIGURED_CONDITION_NEGATION_SCOPE_FALSE_REJECT
```

Safety:

```text
provider_source_fetches = 0

production sends = 0

remote push = 0

raw-model-artifact remote push = 0

main mutations = 0

main merge = 0

deployment = 0
```

Do not resume or stitch the stopped shadow generation.

---

# 3. M12AR FCF claim-scope repair — freeze successful

Preserve:

```text
claim-local / evidence-local FCF validation

Stage-2 confirmation condition
↔ confirmation_business_condition_refs

Stage-2 invalidation condition
↔ business_invalidation_condition_refs

no candidate-global PPE-proxy contamination

unsupported current FCF hard safety

explicit not-FCF disclaimer safety

direct OCF-PPE → FCF mislabel hard failure
```

M12AR exact IBM replay:

```text
PASS
```

The previous IBM hard-stop boundary:

```text
context-04 Stage 2
```

also passed in the new shadow.

Do not reopen FCF semantics in M12AS.

---

# 4. M12AQ formal fictional proof remains authoritative

M12AR did not change model-facing semantics.

Formal fictional reuse:

```text
REUSE_AUTHORIZED
```

M12AQ formal proof remains:

```text
12 / 12 fictional model calls complete

24 / 24 Stage-1 rows hard PASS

24 / 24 Stage-2 rows hard PASS

24 final compositions

aggregate finalization PASS

financial-sector false reject = 0

market-expectation anchor violation = 0

business-delta semantic projection mismatch = 0

PPE-proxy FCF violation = 0

Stage-2 lexical false positive = 0

core mutation = 0
```

M12AS should not rerun fictional models
if the repair remains post-model-validator-only
and offline re-audit preserves all formal rows.

---

# 5. Exact SNDK frozen delta capability

For SNDK, the frozen model-facing business-delta view says:

```text
capability =
UNCHANGED_ONLY

allowed_business_thesis_changes =
["UNCHANGED"]

eligible_change_refs =
[]

eligible_change_direction_hints =
{}

baseline_context_refs include:
configured strengthen/weaken/invalidation conditions

excluded current single-point refs remain non-delta
```

Therefore the model correctly emitted:

```text
business_thesis_change =
UNCHANGED
```

This is NOT a capability violation.

---

# 6. Exact SNDK Stage-1 thesis-context text

The candidate said:

```text
"AI 데이터센터 수요와 장기계약이 기존 논리의 중심이며,
 제시된 강화·약화 조건은 의미 있는 관찰 변화로 확정되지 않았다."
```

Semantic structure:

```text
CURRENT THESIS BASELINE:
AI data-center demand + long-term contracts remain the thesis center

CONFIGURED CONDITIONS:
strengthen / weaken conditions exist

OBSERVATION STATUS:
those configured conditions have NOT been confirmed as meaningful observed change
```

The text explicitly denies current thesis change.

It does NOT assert:

```text
the thesis strengthened

the thesis weakened

a strengthen condition was fulfilled

a weaken condition was fulfilled.
```

Expected:

```text
UNCHANGED context = PASS
```

---

# 7. Exact validator defect

Current code checks, for `UNCHANGED_ONLY`:

```text
if _CURRENT_THESIS_CHANGE_ASSERTION.search(text)
or _CONFIGURED_CONDITION_FULFILLED.search(text):
    BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE
```

Current regex includes patterns equivalent to:

```text
논리 ... 강화|약화

강화|약화 ... 논리
```

within a bounded character window.

Therefore the SNDK sentence:

```text
"기존 논리의 중심이며,
 제시된 강화·약화 조건은
 의미 있는 관찰 변화로 확정되지 않았다."
```

is falsely matched because:

```text
"논리"
and later
"강화·약화"
```

occur near each other.

The regex ignores:

```text
configured-condition role

clause boundaries

explicit non-fulfillment / negation
```

This is the root cause to repair.

---

# 8. Root-cause classification

Freeze the primary root cause as:

```text
CURRENT_THESIS_CHANGE_ASSERTION_LEXICAL_WINDOW
CROSSES_INTO_CONFIGURED_CONDITION_NONFULFILLMENT_CLAUSE
```

or the exact code-audited equivalent.

This is not:

```text
a model prompt problem

a BusinessDeltaEvidenceView problem

a dynamic schema problem

a changed-state grounding problem.
```

Do not reopen those layers.

---

# 9. Correct validation question

For:

```text
business_thesis_change = UNCHANGED
```

the post-model validator should ask:

```text
Does the candidate nevertheless AFFIRM
that the thesis materially strengthened/weakened
or that a configured condition is currently fulfilled?
```

It should NOT ask:

```text
Does the text merely contain words
"논리", "강화", or "약화" near each other?
```

This is a claim-polarity / fulfillment-scope problem.

---

# 10. Add a bounded thesis-change claim classifier

Preferred internal roles:

```text
CURRENT_CHANGE_ASSERTION

CONFIGURED_CONDITION_REFERENCE

EXPLICIT_NO_OBSERVED_CHANGE

CONFIGURED_CONDITION_NOT_FULFILLED

CURRENT_CONDITION_FULFILLED

BASELINE_THESIS_DESCRIPTION

UNKNOWN_OR_AMBIGUOUS
```

Exact names may differ.

Use it only where necessary for:

```text
UNCHANGED-context consistency.
```

Do not build a second BusinessDeltaEvidenceView.

---

# 11. Field scope

The primary field under review is:

```text
business_thesis_context.text
```

Do not automatically scan the entire candidate as one string.

Other fields already have separate semantic responsibilities.

If another field explicitly says:

```text
"논리가 강화됐다"
```

while `business_thesis_change=UNCHANGED`,
that may be a separate consistency violation,
but M12AS should first preserve existing field contracts.

Do not broaden into a full-document Korean NLP rewrite.

---

# 12. Configured-condition references are legal in UNCHANGED context

Examples that MUST PASS:

```text
"강화·약화 조건은 아직 충족되지 않았다."

"제시된 강화 조건은 의미 있는 관찰 변화로 확정되지 않았다."

"약화 조건은 현재 확인되지 않았다."

"strengthen/weaken conditions remain unfulfilled."

"the configured strengthening condition has not been met."

"the weakening condition remains unconfirmed."
```

The words:

```text
강화
약화
strengthen
weaken
```

are not themselves change assertions
when they name configured conditions.

---

# 13. Explicit no-change statements are legal

PASS:

```text
"의미 있는 논리 변화는 확인되지 않았다."

"기존 투자 논리는 유지된다."

"현재까지 논리 강화나 약화가 확인되지 않았다."

"no material thesis change has been observed."

"the thesis has neither strengthened nor weakened on supplied evidence."
```

These should be classified:

```text
EXPLICIT_NO_OBSERVED_CHANGE
```

or equivalent.

---

# 14. True current change assertions remain hard failures

When final enum is:

```text
UNCHANGED
```

the following MUST still fail:

```text
"투자 논리가 강화됐다."

"현재 논리가 약화됐다."

"자사주 소각으로 논리가 강화되었다."

"영업 악화로 투자 논리가 약화됐다."

"the thesis has strengthened."

"the thesis weakened materially."
```

Expected:

```text
BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE
```

Do not weaken this safety.

---

# 15. Fulfilled configured conditions remain hard failures

If the candidate says:

```text
"강화 조건이 충족됐다."

"약화 조건이 확인됐다."

"configured strengthening condition has been met."

"the weakening condition is fulfilled."
```

while the final delta is:

```text
UNCHANGED
```

that must still fail unless a very specific schema contract says
fulfillment can be immaterial.

Default frozen project contract:

```text
an asserted fulfilled thesis-change condition
is inconsistent with UNCHANGED
unless explicitly qualified as immaterial/non-thesis-changing.
```

Do not silently accept fulfilled conditions.

---

# 16. Negation / non-fulfillment must be local

Do NOT implement:

```text
if text contains "않았다" → safe.
```

Example:

```text
"논리가 강화되지 않은 것은 아니고 실제로 강화됐다."
```

must FAIL.

Example:

```text
"약화 조건이 충족되지 않은 것은 아니며 이미 확인됐다."
```

must FAIL.

Use bounded clause polarity.

---

# 17. Configured-condition mention + current assertion

Example:

```text
"강화 조건은 존재하며,
 실제로 이번 실적으로 논리가 강화됐다."
```

Expected:

```text
FAIL
```

The configured-condition mention does not immunize
a separate current change assertion.

---

# 18. Baseline + configured-condition + no-change

Exact SNDK-style structure:

```text
"AI 데이터센터 수요와 장기계약이 기존 논리의 중심이며,
 제시된 강화·약화 조건은 의미 있는 관찰 변화로 확정되지 않았다."
```

Expected:

```text
BASELINE_THESIS_DESCRIPTION
+
CONFIGURED_CONDITION_NOT_FULFILLED
+
EXPLICIT_NO_OBSERVED_CHANGE

→ PASS with UNCHANGED
```

This is the critical positive fixture.

---

# 19. English parity

Support equivalent English patterns.

PASS:

```text
"AI demand remains central to the thesis,
 while the configured strengthen/weaken conditions
 have not been confirmed as observed change."
```

FAIL:

```text
"the thesis has strengthened,
 although some configured conditions remain unconfirmed."
```

Do not make the repair Korean-only.

---

# 20. Prefer structural evidence-role context

When the selected refs in `business_thesis_context`
are all:

```text
baseline_context_refs
```

and the capability is:

```text
UNCHANGED_ONLY
```

this is a strong contextual signal that words like:

```text
강화 조건
약화 조건
```

may be naming configured baseline conditions.

But:

```text
evidence role alone
must not override explicit current change wording.
```

Text polarity remains authoritative for what the model actually claims.

---

# 21. Do not use raw lexical proximity as final truth

After M12AS, forbid a validator design where:

```text
논리 within N chars of 강화/약화
```

alone proves:

```text
CURRENT_CHANGE_ASSERTION.
```

Lexical patterns may assist,
but final classification must account for:

```text
condition nouns

fulfillment predicates

negation / non-confirmation

clause structure
```

No ticker-specific exceptions.

---

# 22. Exact M12AR SNDK offline replay

After repair,
revalidate the exact preserved SNDK Stage-1 candidate.

Required:

```text
capability =
UNCHANGED_ONLY

observed =
UNCHANGED

business_thesis_context claim role =
EXPLICIT_NO_OBSERVED_CHANGE
and/or
CONFIGURED_CONDITION_NOT_FULFILLED

BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE =
0

post-model business-delta status =
PASS
```

Do not rewrite the model output.

---

# 23. Context-05 Stage-1 offline replay

Revalidate all preserved context-05 Stage-1 rows:

```text
SKHY
SNDK
TSLA
TSM
```

Expected:

```text
4 / 4 PASS
```

unless an independent genuine hard violation exists.

M12AR SNDK is the only known failure.

---

# 24. 003690 regression

Preserve the original absolute-state-to-delta safety.

Example known class:

```text
stored favorable thesis context
+
business_thesis_change = STRENGTHENED
without eligible observed change
```

must remain impossible / hard invalid.

Do not confuse:

```text
allowing words "강화 조건"
```

with:

```text
allowing unsupported STRENGTHENED.
```

The dynamic enum/capability already protects this.

---

# 25. FIC-FIN-05 regression

For:

```text
UNCHANGED_ONLY
```

absolute negative current state:

```text
high debt
thin cash
```

must still NOT imply:

```text
WEAKENED
```

without observed baseline change.

Preserve.

---

# 26. True fulfilled-condition fixture

Add:

```text
capability = UNCHANGED_ONLY
observed = UNCHANGED

text =
"기존 논리는 유지되지만 강화 조건이 충족됐다."
```

Expected:

```text
FAIL
```

because the context asserts fulfilled change condition
despite UNCHANGED.

If project semantics later decide that some fulfilled signal
can be immaterial,
that belongs to a separate policy task.

Do not solve that here.

---

# 27. Mandatory fixtures

At minimum:

## DELTA-UNCH-P01

```text
"강화·약화 조건은 아직 충족되지 않았다."
→ PASS
```

## DELTA-UNCH-P02

```text
"제시된 강화·약화 조건은 의미 있는 관찰 변화로 확정되지 않았다."
→ PASS
```

## DELTA-UNCH-P03

```text
"기존 논리는 유지되며 현재까지 강화나 약화는 확인되지 않았다."
→ PASS
```

## DELTA-UNCH-P04

```text
"configured strengthening condition has not been met."
→ PASS
```

## DELTA-UNCH-N01

```text
"논리가 강화됐다."
→ FAIL
```

## DELTA-UNCH-N02

```text
"논리가 약화됐다."
→ FAIL
```

## DELTA-UNCH-N03

```text
"강화 조건이 충족됐다."
→ FAIL
```

## DELTA-UNCH-N04

```text
"약화 조건이 확인됐다."
→ FAIL
```

## DELTA-UNCH-N05

```text
"강화 조건은 아직 미확인이라고 했지만 실제 논리는 강화됐다."
→ FAIL
```

## DELTA-UNCH-N06

```text
"강화되지 않은 것은 아니고 이미 강화됐다."
→ FAIL
```

---

# 28. BusinessDeltaEvidenceView remains the single source of evidence semantics

M12AS must NOT add a second evidence-role engine.

Preserve:

```text
capability

allowed enum

baseline_context_refs

eligible_change_refs

direction hints

excluded refs
```

The new classifier only determines:

```text
what the model text claims about current thesis change.
```

It does not reclassify evidence.

Required:

```text
business_delta_semantic_projection_mismatch_count = 0

pre_post_delta_view_identity_mismatch_count = 0

legacy_raw_text_eligibility_rederivation_count = 0

legacy_raw_text_direction_rederivation_count = 0
```

---

# 29. No model-facing changes by default

Preferred:

```text
model prompt semantic change count = 0

model schema semantic change count = 0

BusinessDeltaEvidenceView change count = 0

MarketExpectationEvidenceView change count = 0

financial evidence projection change count = 0
```

This should be a post-model consistency-validator repair only.

If model-facing semantics change unexpectedly:

```text
STOP
FORMAL_FICTIONAL_REPROOF_REQUIRED
```

Do not proceed to shadow in the same task.

---

# 30. M12AQ formal fictional proof reuse

If only post-model UNCHANGED claim-scope validation changes:

Offline re-audit:

```text
24 Stage-1 rows
24 Stage-2 rows
24 final compositions
```

Required:

```text
all remain hard PASS

no new business-delta false accept

no new business-delta false reject

financial-sector PASS

expectation independence PASS

PPE/FCF PASS

Stage-2 lexical PASS

core mutation = 0
```

Then:

```text
formal_fictional_reuse_status = REUSE_AUTHORIZED
```

Do not rerun fictional models unnecessarily.

---

# 31. Freeze all completed prior repairs

Re-run regression suites for:

```text
M12AR IBM FCF claim scope

M12AQ financial-sector exclusion connective

M12AP MarketExpectationEvidenceView

M12AO business-delta single-source convergence

M12AN PPE-proxy label + not-FCF safety

M12AM Stage-2 Korean lexical matcher

M12AG price/timing evidence ownership

M12AH financial temporal scope

QTD/YTD

WC grounding

debt completeness

ADR/security basis

two-stage core immutability
```

No regressions.

---

# 32. New full shadow required

M12AR shadow stopped after 14 model calls
and validator code will change after those outputs.

Therefore:

```text
do NOT resume M12AR

do NOT stitch contexts 01-04 with new context-05/06

do NOT reuse partial output as formal M12AS compatibility data
```

Start:

```text
NEW shadow generation ID

NEW monolithic outputs

NEW Stage-1 outputs

NEW Stage-2 outputs

NEW invocation IDs
```

for all active monitored names.

---

# 33. Active monitored universe

Re-enumerate active monitored stocks read-only at shadow start.

Last verified reference:

```text
22 names
```

Use the actual task-start active set.

No registration/stop mutation.

---

# 34. Same-packet contract

For every active ticker:

```text
one reproducible local packet
```

Exact same packet hash feeds:

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

# 35. Shadow topology

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
18 model calls
```

No repetitions.

No fresh unseen issuers.

---

# 36. Shadow hard-stop policy

Hard stop only for:

```text
runtime/schema failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

objective financial semantic failure

true PPE-proxy-as-FCF violation

unsupported current FCF claim

business-delta capability violation

true business-delta current-change inconsistency

business-delta canonical direction contradiction

market-expectation anchor-eligibility violation

financial-sector framework misuse/exclusion false reject

price/technical/supply Core contamination

Stage-2 actual contamination

ADR/security-basis violation

core mutation

production side-effect attempt

aggregate finalization failure
```

Do NOT hard-stop on:

```text
configured strengthen/weaken condition mentioned as unfulfilled

explicit statement that no meaningful thesis change was observed.
```

---

# 37. Shadow UNCHANGED claim-scope audit

For every row where:

```text
business_thesis_change = UNCHANGED
```

record:

```text
business_thesis_context text

context refs

claim roles

current-change assertion count

configured-condition reference count

configured-condition fulfilled count

configured-condition unfulfilled count

explicit no-observed-change count

validation result
```

This is essential to prove the repair is neither too strict nor too permissive.

---

# 38. Shadow comparison taxonomy

Use existing compatibility taxonomy:

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

Neither monolithic nor two-stage is automatically ground truth.

---

# 39. Full compatibility goal

M12AS must finally produce:

```text
one final comparison row per active monitored ticker

full aggregate finalization PASS

all decision-material differences reviewed
```

Do not perform boundary/delta/holder policy repair mid-generation.

Complete the cohort first.

---

# 40. Policy handoff after complete shadow

If full shadow completes without systematic architecture regression:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

Use:

```text
M12AQ formal fictional proof
+
M12AS complete monitored shadow
```

Focus:

```text
1. adjacent primary direction differences

2. FIC-FIN-02 / FIC-FIN-06 business-delta materiality

3. FIC-FIN-08 holder HOLDABLE/REVIEW boundary

4. new-buyer stance differences with stable core

5. whether expectation-independence restrictions reduced
   previous threshold differences
```

---

# 41. Local-only / production firewall

M12AS is LOCAL-ONLY.

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

remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Do not ask for GitHub push authorization.

Monitoring schedules remain paused.

---

# 42. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12as-scope-freeze

04-integrated-main-lineage-freeze

05-m12ar-sndk-failure-reproduction

06-unchanged-context-regex-code-audit

07-sndk-clause-polarity-forensic

08-configured-condition-negation-scope-root-cause

09-unchanged-claim-classifier-options

10-unchanged-claim-classifier-decision
```

---

# 43. Required classifier artifacts

Produce:

```text
11-business-delta-unchanged-claim-contract-v2

12-current-thesis-change-assertion-contract

13-configured-condition-reference-contract

14-configured-condition-fulfillment-contract

15-configured-condition-nonfulfillment-contract

16-explicit-no-observed-change-contract

17-local-negation-scope-contract

18-english-korean-parity-contract
```

---

# 44. Required exact replay / fixture artifacts

Produce:

```text
19-m12ar-sndk-exact-offline-replay

20-m12ar-context05-stage1-four-row-replay

21-003690-absolute-state-regression

22-fic-fin-05-unchanged-only-regression

23-unchanged-configured-condition-positive-fixtures

24-unchanged-true-change-negative-fixtures

25-double-negation-negative-fixtures
```

---

# 45. Required frozen-regression artifacts

Produce:

```text
26-m12ar-fcf-claim-scope-freeze

27-m12aq-financial-sector-scope-freeze

28-m12ap-expectation-independence-freeze

29-m12ao-business-delta-view-freeze

30-m12an-ppe-proxy-label-freeze

31-m12am-stage2-lexical-freeze

32-monitoring-transition-ownership-freeze

33-financial-temporal-scope-freeze

34-qtd-ytd-wc-debt-safety-freeze

35-adr-security-basis-freeze

36-two-stage-ownership-freeze

37-price-timing-renderer-no-change
```

---

# 46. Required semantic-hash / fictional-reuse artifacts

Produce:

```text
38-model-prompt-semantic-hash-freeze

39-model-schema-semantic-hash-freeze

40-evidence-projection-semantic-hash-freeze

41-business-delta-view-semantic-hash-freeze

42-expectation-view-semantic-hash-freeze

43-two-stage-semantic-hash-freeze

44-m12aq-fictional-24-row-business-delta-reaudit

45-formal-fictional-proof-reuse-decision
```

Artifact 45 may be:

```text
REUSE_AUTHORIZED
```

only if model-facing semantics are unchanged
and all formal rows remain hard PASS.

Otherwise:

```text
STOP
FULL_FICTIONAL_REPROOF_REQUIRED
```

---

# 47. Required deterministic test gate

Produce:

```text
46-focused-test-results

47-full-local-test-results

48-ruff-and-diff-results

49-hosted-ci-portability-observation

50-new-shadow-model-call-gate
```

No shadow model calls before artifact 50 PASS.

---

# 48. Required NEW shadow setup artifacts

Produce:

```text
51-shadow-generation-manifest

52-task-start-active-monitored-universe

53-shadow-packet-inventory

54-shadow-packet-hash-manifest

55-shadow-delta-view-manifest

56-shadow-expectation-view-manifest

57-shadow-frozen-context-manifest

58-shadow-batching-manifest
```

Use a NEW generation ID.

---

# 49. Required raw shadow artifacts

For every context preserve locally:

```text
monolithic prompt/schema/raw output/receipt/log/run document

Stage-1 prompt/schema/raw output/receipt/log/run document

Stage-2 prompt/schema/raw output/receipt/log/run document
```

No remote push.

---

# 50. Required full shadow analysis artifacts

Produce:

```text
59-shadow-context-hard-semantic-audit

60-shadow-business-delta-unchanged-claim-scope-audit

61-shadow-fcf-claim-scope-audit

62-shadow-financial-sector-scope-audit

63-shadow-market-expectation-independence-audit

64-shadow-business-delta-convergence-audit

65-shadow-stage2-language-audit

66-shadow-final-composition-audit

67-shadow-aggregate-finalization-audit

68-shadow-per-ticker-comparison

69-shadow-core-direction-differences

70-shadow-business-delta-differences

71-shadow-new-buyer-differences

72-shadow-holder-differences

73-shadow-same-direction-calibration-differences

74-shadow-expected-contract-corrections

75-shadow-potential-architecture-regressions

76-shadow-unresolved-review-required

77-shadow-adr-security-basis-audit

78-shadow-cyclical-valuation-audit

79-shadow-core-immutability-audit

80-shadow-runtime-audit

81-shadow-aggregate-summary

82-shadow-architecture-decision
```

---

# 51. Required combined diagnostics

If full shadow completes:

```text
83-fic-fin-05-vs-monitored-primary-boundary-analogs

84-expectation-independence-vs-primary-threshold-analysis

85-fic-fin-02-vs-monitored-delta-materiality-analogs

86-fic-fin-06-vs-monitored-positive-delta-analogs

87-fic-fin-08-vs-monitored-holder-analogs

88-new-buyer-monolithic-vs-two-stage-analogs

89-real-business-delta-unchanged-language-lessons

90-combined-fictional-monitored-root-cause-summary

91-next-bounded-policy-decision
```

---

# 52. Required completion artifacts

Produce:

```text
92-business-delta-unchanged-scope-repair-success-decision

93-formal-fictional-proof-reuse-success-decision

94-full-shadow-completion-decision

95-existing-monitored-impact-summary

96-two-stage-shadow-compatibility-decision

97-fresh-real-proof-readiness-decision

98-final-main-merge-readiness-note

99-production-no-change

100-schedule-pause-observation

101-remote-push-prohibition-audit

102-master-workflow-update

103-program-completion
```

---

# 53. Shadow acceptance criteria

Require:

```text
all planned shadow calls complete

all active tickers represented exactly once

aggregate finalization PASS

business-delta UNCHANGED false reject count = 0

true UNCHANGED/current-change inconsistency false accept count = 0

configured-condition-nonfulfillment false reject count = 0

business-delta semantic projection mismatch = 0

business-delta true direction contradiction = 0

true PPE-proxy-as-FCF violation = 0

configured FCF false reject = 0

financial-sector exclusion false reject = 0

financial-sector true misuse = 0

market-expectation anchor violation = 0

Stage-2 actual contamination = 0

invalid refs = 0

ADR/security-basis failure = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0

production side effects = 0
```

Investment-decision differences are measured,
not hard failures.

---

# 54. Fresh-real / main / production readiness

At M12AS completion:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

Even if full shadow completes.

The next bounded policy review must consume the completed cohort first.

No fresh unseen proof inside M12AS.

---

# 55. Failure handling

## A. Exact SNDK sentence still false-rejects

```text
next_scope =
BUSINESS_DELTA_CLAIM_POLARITY_ARCHITECTURE_REVIEW
```

No model calls.

## B. Repair allows actual "논리가 강화됐다" with UNCHANGED

```text
STOP
BUSINESS_DELTA_UNCHANGED_REPAIR_TOO_PERMISSIVE
```

## C. Repair weakens fulfilled configured-condition detection

```text
STOP
CONFIGURED_CONDITION_FULFILLMENT_REGRESSION
```

## D. Model-facing semantic hashes change

```text
STOP
FULL_FICTIONAL_REPROOF_REQUIRED
```

## E. Full shadow completes cleanly

Expected:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

## F. Full shadow reveals systematic architecture regression

Use the smallest bounded compatibility-review scope.

---

# 56. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch

latest_result_zip_sha256
latest_result_integrity

m12ar_failure_ticker
m12ar_failure_error

unchanged_claim_scope_root_cause

business_delta_unchanged_claim_contract_version

current_change_assertion_count

configured_condition_reference_count
configured_condition_fulfilled_count
configured_condition_unfulfilled_count
explicit_no_observed_change_count

unchanged_false_reject_count
unchanged_true_change_false_accept_count

m12ar_sndk_exact_replay_status

business_delta_semantic_projection_mismatch_count
pre_post_delta_view_identity_mismatch_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
business_delta_view_change_count
expectation_view_change_count
financial_semantic_change_count
two_stage_semantic_change_count

formal_fictional_reuse_status
fictional_offline_reaudit_failure_count

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

shadow_business_delta_unchanged_false_reject_count
shadow_business_delta_current_change_false_accept_count
shadow_configured_condition_unfulfilled_false_reject_count

shadow_business_delta_semantic_projection_mismatch_count
shadow_business_delta_direction_contradiction_count

shadow_ppe_proxy_fcf_violation_count
shadow_configured_fcf_false_reject_count

shadow_financial_sector_exclusion_false_reject_count
shadow_financial_sector_true_misuse_count

shadow_expectation_anchor_violation_count
shadow_expectation_view_projection_mismatch_count

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

Anything not measured:

```text
NOT_MEASURED
```

---

# 57. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

Do not push report/raw artifacts to GitHub.

---

# 58. Final task principle

M12AR's intended FCF claim-scope repair worked.

The next stop is narrower and unrelated:

```text
SNDK capability = UNCHANGED_ONLY

model output = UNCHANGED

model text =
"configured strengthen/weaken conditions
 have NOT been confirmed as meaningful observed change"

validator sees:
"논리 ... 강화·약화"
inside a character window

and falsely concludes:
the context asserts thesis change.
```

The correct M12AS flow is:

```text
preserve BusinessDeltaEvidenceView

→ keep UNCHANGED_ONLY dynamic schema

→ replace naive lexical proximity with
   bounded claim/fulfillment/negation classification

→ recognize configured conditions as configured conditions

→ recognize explicit non-fulfillment / no-observed-change wording

→ keep true "thesis strengthened/weakened" assertions hard-failing

→ offline replay the exact SNDK candidate

→ re-audit the formal fictional proof

→ if model-facing semantics are unchanged,
   reuse the formal fictional proof

→ start a completely NEW full monitored shadow

→ finally complete the 22-name compatibility cohort

→ then move to the real
   boundary / delta-materiality / holder policy review.
```

Do NOT:

```text
allow unsupported STRENGTHENED/WEAKENED

weaken UNCHANGED_ONLY

whitelist only the exact SNDK sentence

treat every "않았다" as safe

add another model prompt paragraph

resume/stitch the stopped M12AR shadow

rerun fictional models unnecessarily

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring
```

Mentioning a strengthen/weaken condition
is not the same thing as saying the thesis strengthened or weakened.
