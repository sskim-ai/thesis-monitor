# Thesis Monitor — PPE-Proxy / FCF Claim-Evidence Scope Binding + New Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AR — Integrated-Main FCF Claim-Scope Compliance
         A. Freeze successful M12AQ fictional formal proof
         B. Reproduce exact IBM Stage-2 PPE-proxy/FCF false-positive candidate
         C. Separate claim-local proxy use from unrelated FCF conditions
         D. Bind financial claim text to the correct local evidence-ref scope
         E. Preserve true OCF-PPE→FCF hard failures
         F. Offline re-audit M12AQ fictional proof
         G. Start a NEW full active-monitored same-packet shadow
         H. Complete compatibility and policy-review handoff
```

M12AQ successfully repaired the target financial-sector exclusion-connective bug
and produced a complete clean formal fictional proof.

M12AQ formal fictional result:

```text
Stage 1 calls = 6 / 6
Stage 2 calls = 6 / 6
total fictional calls = 12 / 12

Stage 1 rows = 24 / 24 hard PASS
Stage 2 rows = 24 / 24 hard PASS
final compositions = 24
aggregate finalization = PASS

financial-sector exclusion false reject = 0
financial-sector true misuse = 0
replacement-predicate backward leak = 0

market-expectation anchor violation = 0
market-expectation projection mismatch = 0

business-delta semantic projection mismatch = 0
business-delta direction contradiction = 0

PPE-proxy FCF violation = 0
Stage-2 lexical false positive = 0

core mutation = 0
timeout = 0
orphan = 0
wrapper retry = 0
```

The monitored shadow then progressed to:

```text
12 / 18 planned model calls
```

and stopped at:

```text
context-04 / Stage 2 / IBM
```

with:

```text
ppe_only_cash_conversion_proxy_called_fcf
```

Independent forensic review shows that this hard stop must be re-audited carefully.

IBM's composed candidate contains a legitimate PPE-only cash-conversion proxy
in Stage 1, but the Stage-2 FCF language is not clearly an attribution of that proxy.

The current validator contains a candidate-global fallback:

```text
candidate_uses_ppe_proxy = true
```

and then treats ANY FCF wording elsewhere in the candidate as proxy-applicable:

```text
proxy_applies =
    "ocf_less_ppe_capex" in local_metrics
    OR
    (candidate_uses_ppe_proxy AND FCF term appears in this text)
```

This can contaminate an unrelated FCF claim/condition
merely because the candidate used an OCF-PPE proxy somewhere else.

M12AR must make the safety contract claim-local / evidence-scoped.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260912-financial-sector-exclusion-connective-scope-fictional-reproof-full-shadow-report.zip
```

Verified SHA-256:

```text
203d6740db374e17b6d4c16de38abf65d77eacff36966cbe13c82a4b31f017d2
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 508
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

ZIP entries:

```text
508 indexed payloads
+ artifact-index.json
= 509 entries
```

Recompute independently.

---

# 2. M12AQ provenance / local-only policy

Reported:

```text
phase = M12AQ

branch =
codex/20260912-financial-sector-exclusion-scope-m12aq

base integration head =
44180820ef4cfcd094210acd004c4f772454713e

final local head =
7bffe4116862d5179458061d75de5857f7a4b8c2
```

At task start record actual:

```text
branch
HEAD
working tree
remote tracking state
```

This task is LOCAL-ONLY.

Required:

```text
remote_push_count = 0
raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0
main_merges = 0

deployments = 0
automatic_monitoring_resume = 0
```

Do not request GitHub push authorization.

---

# 3. M12AQ financial-sector repair — freeze successful

M12AQ formal fictional proof:

```text
financial-sector exclusion false reject = 0

financial-sector true misuse = 0

replacement-predicate backward leak = 0
```

Actual monitored insurance control:

```text
003690

monolithic = PASS
Stage 1 = PASS
Stage 2 = PASS

generic framework leak = 0
framework application count = 0
```

Do not reopen:

```text
X 대신 Y

X이/가 아니라 Y

X이 아닌 Y

X보다는 Y

X를 배제하고 Y를 본다

coordinated excluded framework object scope

replacement-clause scope
```

M12AR is NOT a financial-sector scope task.

---

# 4. M12AQ MarketExpectationEvidenceView — freeze successful

Preserve:

```text
INDEPENDENT_DIRECTIONAL_SUPPORT

CONDITIONAL_CONTEXT_ONLY

INDEPENDENCE_UNKNOWN

ALREADY_REFLECTED_OR_COUNTERWEIGHT
where supported
```

Formal proof:

```text
context-only expectation material-anchor violation = 0

dominant-evidence violation = 0

expectation projection mismatch = 0

pre/post expectation-view identity mismatch = 0
```

No expectation semantic changes.

---

# 5. Business-delta convergence — freeze successful

Preserve:

```text
BusinessDeltaEvidenceView
as single semantic source

post-model validator consumes canonical view

legacy raw-text eligibility re-derivation = 0

legacy raw-text direction re-derivation = 0

business-delta semantic projection mismatch = 0

pre/post delta-view identity mismatch = 0
```

No business-delta changes.

---

# 6. M12AN PPE-proxy metadata repair — freeze successful

Preserve the repaired model-facing PPE-only proxy representation:

```text
label =
cash_conversion_ocf_less_ppe

metric_refs =
[]

canonical metric =
ocf_less_ppe_capex

limitation =
ppe_only_not_management_defined_fcf
```

Do NOT revert to:

```text
cash_flow_fcf_ppe

metric_refs=["FCF"]
```

The model-facing proxy itself is no longer mislabeled.

---

# 7. Exact M12AQ shadow stop

Shadow generation:

```text
20260911-m12ai-shadow-20260912T060208Z-a7b0db467141
```

Planned:

```text
18 model calls
```

Completed:

```text
12 model calls

transport PASS = 12
semantic PASS calls = 11
semantic FAIL calls = 1

timeout = 0
orphan = 0
wrapper retry = 0
```

Failure:

```text
context-04
Stage 2
ticker = IBM

contract =
directional-financial-semantic-validator-v1

error =
ppe_only_cash_conversion_proxy_called_fcf
```

Unattempted after hard stop:

```text
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Do not resume or stitch this generation.

---

# 8. IBM Stage-1 PPE-only proxy use

IBM's frozen Stage-1 core correctly uses:

```text
E27

label =
cash_conversion_ocf_less_ppe

financial_semantics.metric =
ocf_less_ppe_capex

value =
7,305,000,000 USD YTD

limitations include:
ppe_only_not_management_defined_fcf
```

Stage-1 language describes it as:

```text
"누적 영업현금흐름과 유형자산 취득 현금유출을 뺀 현금전환 대용치"

"누적 현금창출"

"같은 현금흐름 축에 집중"
```

This is valid proxy usage.

It does NOT itself call E27 FCF.

Stage 1 passed.

---

# 9. IBM also has configured FCF business conditions

The same IBM packet contains separate NON-PROXY configured thesis signals.

Examples:

```text
E30
STRUCTURAL_RISK / 무효화 조건

"Software·AI 성장에도
 전사 매출과 FCF가 장기간 정체 또는 감소"
```

and:

```text
E31
BUSINESS_CURRENT / 논리 강화 조건

"FCF 성장률 재가속과 부채 관리 개선"
```

These refs refer to the business concept:

```text
FCF
```

as a future/configured strengthen/invalidation condition.

They are NOT the canonical PPE-only proxy E27.

They must not be automatically merged with E27
merely because the same candidate contains both concepts.

---

# 10. Exact IBM Stage-2 FCF language

Stage 2 includes:

```text
fundamental_new_buyer.confirmation_business_condition:

"소프트웨어 성장 가속과 AI 계약 매출이 전사 성장으로 이어지고
 FCF 재가속과 부채 관리 개선이 함께 확인되어야 한다."
```

with refs including:

```text
E31
```

and:

```text
fundamental_holder.business_invalidation_condition:

"소프트웨어·AI 성장에도
 전사 매출과 FCF가 장기간 정체·감소하거나
 인수 후 ROIC가 구조적으로 악화되면
 보유 근거가 훼손된다."
```

with refs including:

```text
E30
E38
```

New-buyer summary also says:

```text
"전사 성장과 FCF 가속,
 AI 계약의 매출·마진 기여가 아직 확인되지 않았다."
```

These are:

```text
future / confirmation / invalidation / not-yet-confirmed business conditions
```

not a statement that:

```text
E27 OCF-PPE is FCF.
```

---

# 11. Current validator root cause to verify

Current financial semantic validator computes conceptually:

```text
candidate_uses_ppe_proxy =
    ANY claim anywhere in candidate
    cites ocf_less_ppe_capex
```

Then for EACH claim row:

```text
proxy_applies =
    local row cites ocf_less_ppe_capex
    OR
    (
        candidate_uses_ppe_proxy
        AND
        this unrelated row contains FCF terminology
    )
```

This makes the proxy scope:

```text
candidate-global
```

instead of:

```text
claim-local / evidence-local.
```

Primary expected root cause:

```text
CANDIDATE_GLOBAL_PPE_PROXY_SCOPE_LEAKS_INTO_UNRELATED_FCF_CLAIMS
```

Freeze the actual root cause from code.

---

# 12. Secondary claim-row scope issue to audit

Current generic financial `_claim_rows(...)`
must also be audited for Stage-2 field/ref pairing.

Stage-2 schema has pairs such as:

```text
confirmation_business_condition
confirmation_business_condition_refs

business_invalidation_condition
business_invalidation_condition_refs
```

A correct financial claim extractor must bind these text fields
to their own sibling ref arrays.

Do not assume generic:

```text
evidence_refs
```

covers them.

The existing QTD/YTD `_period_claim_rows(...)` already supports these explicit pairs.

Audit whether financial semantic `_claim_rows(...)`
does the same.

If not, this is part of the root cause.

---

# 13. One canonical financial claim-row extractor

Preferred architecture:

```text
FinancialClaimRow
```

or equivalent internal representation.

Each row should carry at least:

```text
field_path

text

bound_evidence_refs

field_semantic_role
```

Potential field roles:

```text
CURRENT_CORE_CLAIM

FUTURE_REEVALUATION_CONDITION

STANCE_CONFIRMATION_CONDITION

STANCE_INVALIDATION_CONDITION

STANCE_SUMMARY

RISK_CONTEXT

UNKNOWN
```

Exact names may differ.

Do not add user-facing schema.

---

# 14. Claim-local evidence binding

For standard fields:

```text
text
+
evidence_refs
```

bind as today.

For Stage 2:

```text
confirmation_business_condition
↔
confirmation_business_condition_refs
```

and:

```text
business_invalidation_condition
↔
business_invalidation_condition_refs
```

must be explicit claim/ref pairs.

No candidate-global evidence inheritance.

---

# 15. Summary fields

Stage-2 summaries have no direct evidence-ref array.

Do NOT automatically bind:

```text
every financial ref anywhere in the candidate
```

to a summary.

A summary may reference a business concept such as:

```text
FCF growth
```

without thereby relabeling every selected cash-conversion proxy.

If the summary makes a current numeric or explicit proxy-equivalence claim,
validate that claim under separate current-claim safety rules.

Do not use candidate-global proxy presence as proof of attribution.

---

# 16. PPE-proxy FCF safety contract — revised scope

A hard:

```text
ppe_only_cash_conversion_proxy_called_fcf
```

must require one of the following:

## A. Direct evidence-bound mislabel

The claim's bound refs include:

```text
ocf_less_ppe_capex
```

and the text calls that evidence:

```text
FCF
free cash flow
잉여현금흐름
or canonical FCF equivalent
```

affirmatively / numerically.

## B. Explicit proxy-equivalence language

The text itself says:

```text
OCF-PPE is FCF

the cash-conversion proxy is FCF

사실상 FCF

FCF로 본다
```

even if refs are absent.

## C. Numeric proxy laundering

If supported safely by existing architecture:

```text
an unqualified numeric FCF claim
matches/depends on the PPE-only proxy value
without actual FCF evidence.
```

Do not implement brittle numeric matching
unless already available safely.

The minimum required fix is A + B.

---

# 17. Candidate-global proxy presence is insufficient

The following must NOT by itself cause a failure:

```text
candidate contains a valid OCF-PPE proxy use in Stage 1

AND

another field discusses FCF as:
- future confirmation condition
- invalidation condition
- configured signal
- not-yet-confirmed business metric
```

This is exactly the IBM case.

Required:

```text
candidate_global_proxy_scope_fallback_count_after = 0
```

for unqualified unrelated FCF wording.

---

# 18. Explicit proxy mislabel remains hard

Still FAIL:

```text
E27 = ocf_less_ppe_capex

claim:
"FCF는 73.05억달러다."
```

when E27 is the supporting ref.

Still FAIL:

```text
"OCF-PPE를 FCF로 본다."
```

Still FAIL:

```text
"이 현금전환 대용치가 사실상 FCF다."
```

No weakening.

---

# 19. Safe configured FCF conditions

PASS:

```text
configured strengthening condition:
"FCF 성장률 재가속이 확인되면 긍정적이다."
```

when supported by the configured strengthen signal.

PASS:

```text
configured invalidation:
"전사 매출과 FCF가 장기간 정체·감소하면 논리가 훼손된다."
```

when supported by configured invalidation evidence.

These are not current fulfilled claims.

Preserve the configured-vs-fulfilled lifecycle distinction.

---

# 20. Safe unconfirmed FCF summary

PASS:

```text
"FCF 가속은 아직 확인되지 않았다."
```

or equivalent:

```text
"FCF 재가속 확인이 필요하다."
```

when it is a stance confirmation gap / uncertainty statement
and it is not presented as the PPE proxy.

Do not treat the mere acronym FCF as proxy attribution.

---

# 21. Current FCF claim safety

Do NOT create an unsafe gap.

Examples:

```text
"현재 FCF는 7.305bn이다."

"FCF가 현재 양수다."

"FCF가 증가했다."
```

must not be silently accepted merely because
the claim does not directly cite the proxy.

Audit existing current-FCF evidence safety.

If the repository has no safe typed/official FCF evidence contract,
current unqualified FCF claims without proper support
should fail under a generic unsupported/current-FCF rule
or remain conservatively blocked.

Do NOT use unrelated candidate-global PPE proxy presence
as the implementation shortcut.

Separate:

```text
unsupported current FCF claim
```

from:

```text
PPE proxy mislabeled as FCF.
```

---

# 22. FCF claim roles

Preserve / refine roles:

```text
AFFIRMATIVE_FCF_ATTRIBUTION

NUMERIC_FCF_ATTRIBUTION

PROXY_AS_FCF_ATTRIBUTION

PROXY_DESCRIPTIVE_CASH_CONVERSION

EXPLICIT_NOT_FCF_DISCLAIMER

UNKNOWN_OR_AMBIGUOUS
```

Add only if needed:

```text
PROSPECTIVE_OR_CONFIGURED_FCF_CONDITION

UNCONFIRMED_FCF_REQUIREMENT
```

or represent those through field semantic role.

Do not create duplicate semantic engines.

---

# 23. Temporal role matters

The same text fragment:

```text
FCF growth
```

means different things in:

```text
current core judgment

future reevaluation condition

new-buyer confirmation condition

holder invalidation condition

summary of an unconfirmed requirement
```

Use field role + evidence binding.

Do not classify solely from token presence.

---

# 24. Exact IBM offline replay

After repair,
revalidate the exact preserved M12AQ IBM final candidate.

Required:

```text
IBM Stage-1 proxy use =
valid OCF-PPE cash-conversion usage

IBM Stage-2 FCF configured conditions =
not treated as proxy attribution

candidate-global proxy scope leakage = 0

ppe_only_cash_conversion_proxy_called_fcf = 0

financial semantic status = PASS
```

All other IBM hard semantic audits must remain PASS.

Do not rewrite the model output.

---

# 25. IBM claim-scope audit

Produce a row for every IBM FCF/proxy-related claim:

```text
field_path

text

field_semantic_role

bound refs

bound canonical metrics / evidence types

FCF claim role

PPE-proxy applies to this claim?
true/false

validation result
```

This must prove exactly why each IBM FCF phrase is or is not proxy-related.

---

# 26. M12AM TSLA regression

Re-run the exact M12AM TSLA Stage-1 candidate.

Expected:

```text
"현금 전환 대용치이며
 관리 기준 잉여현금흐름이 아니다."
→ PASS
```

Affirmative proxy-as-FCF negatives must remain FAIL.

No regression of M12AN.

---

# 27. PPE-proxy direct-mislabel negative fixtures

At minimum:

## FCF-SCOPE-N01

```text
local refs = [ocf_less_ppe_capex]
text = "FCF is positive."
→ FAIL
```

## FCF-SCOPE-N02

```text
local refs = [ocf_less_ppe_capex]
text = "잉여현금흐름은 352m이다."
→ FAIL
```

## FCF-SCOPE-N03

```text
no refs
text = "OCF-PPE를 FCF로 본다."
→ FAIL
```

## FCF-SCOPE-N04

```text
proxy claim + "not FCF, but 사실상 FCF다"
→ FAIL
```

---

# 28. Unrelated-FCF positive fixtures

At minimum:

## FCF-SCOPE-P01

```text
candidate uses OCF-PPE proxy elsewhere

new-buyer condition:
"FCF 성장률 재가속이 확인되어야 한다."

refs = configured FCF strengthen condition

→ PASS
```

## FCF-SCOPE-P02

```text
candidate uses OCF-PPE proxy elsewhere

holder invalidation:
"FCF가 장기간 정체·감소하면 보유 논리가 훼손된다."

refs = configured FCF invalidation condition

→ PASS
```

## FCF-SCOPE-P03

```text
candidate uses OCF-PPE proxy elsewhere

summary:
"FCF 가속은 아직 확인되지 않았다."

→ PASS as unconfirmed requirement
```

## FCF-SCOPE-P04

```text
OCF-PPE described as cash-conversion proxy
without FCF label
→ PASS
```

## FCF-SCOPE-P05

```text
"this proxy is not management-defined FCF"
→ PASS
```

---

# 29. Cross-field isolation fixture

Construct:

```text
field A:
refs=[ocf_less_ppe_capex]
text="OCF less PPE is positive."

field B:
refs=[configured FCF condition]
text="FCF growth must reaccelerate."

Expected:
A = safe proxy description
B = safe independent/configured FCF concept
candidate = PASS
```

Then:

```text
field A:
refs=[ocf_less_ppe_capex]
text="FCF is positive."

field B:
safe unrelated configured FCF condition

Expected:
candidate = FAIL due field A only
```

This is the core M12AR contract.

---

# 30. Claim-row extraction fixtures

At minimum:

```text
generic text + evidence_refs
→ refs correctly bound

confirmation_business_condition
+ confirmation_business_condition_refs
→ refs correctly bound

business_invalidation_condition
+ business_invalidation_condition_refs
→ refs correctly bound

summary with no refs
→ no candidate-global evidence binding

nested arrays / text claims
→ field paths stable
```

No ref leakage between sibling fields.

---

# 31. Period validator non-regression

If claim-row extraction is refactored/shared,
ensure QTD/YTD period semantics remain unchanged.

Existing `_period_claim_rows(...)` behavior must remain valid.

Do not introduce:

```text
QTD/YTD false reject

QTD/YTD false accept
```

by unifying extractors.

---

# 32. MarketExpectationEvidenceView no-change

Required:

```text
expectation model view change count = 0

context-only expectation anchor violation count = 0

expectation projection mismatch count = 0

pre/post expectation-view identity mismatch count = 0
```

M12AR is not an expectation task.

---

# 33. Business-delta no-change

Required:

```text
business-delta model view unchanged

semantic projection mismatch = 0

pre/post delta-view identity mismatch = 0

legacy raw-text re-derivation = 0
```

No delta changes.

---

# 34. Financial-sector exclusion no-change

Re-run exact M12AP FIC-FIN-08 sentence:

```text
"보험사이므로 산업회사식 순부채와 운전자본 틀을 배제하고
 인수 규율과 규제자본을 중심으로 본다."
```

Expected:

```text
PASS

application_count = 0

false reject = 0
```

Re-run 003690 monitored negative control offline if preserved.

---

# 35. Stage-2 lexical no-change

Preserve:

```text
"주가" contamination detection

"수주가 / 발주가" clean handling
```

No changes.

---

# 36. Model-facing semantic hash policy

Preferred M12AR repair:

```text
financial validator / claim-row extractor only
```

No:

```text
prompt change

model schema change

evidence projection change

BusinessDeltaEvidenceView change

MarketExpectationEvidenceView change

Stage-1/Stage-2 ownership change
```

If all model-facing hashes remain unchanged:

```text
reuse M12AQ formal fictional model proof
after offline re-audit.
```

Do NOT rerun fictional models unnecessarily.

If any model-facing semantic hash changes:

```text
STOP
FORMAL_FICTIONAL_REPROOF_REQUIRED
```

and create a separate whole-proof scope.

Do not silently mix.

---

# 37. Offline re-audit of M12AQ formal fictional proof

Revalidate:

```text
24 Stage-1 rows

24 Stage-2 rows

24 final compositions
```

under the repaired FCF claim-scope validator.

Required:

```text
all 24 / 24 remain hard PASS

PPE-proxy FCF false reject = 0

true PPE-proxy-as-FCF negative controls still FAIL

financial-sector scope PASS

expectation independence PASS

business-delta convergence PASS

Stage-2 lexical PASS

core mutation = 0
```

Then set:

```text
formal_fictional_reuse_status = REUSE_AUTHORIZED
```

This is an offline validator re-audit,
not a new model proof.

---

# 38. Shadow must be a NEW generation

M12AQ shadow stopped after 12 model calls
and validator code will change afterward.

Therefore:

```text
do NOT resume M12AQ shadow

do NOT stitch contexts 01-03 with new contexts 04-06

do NOT reuse partial rows as formal M12AR compatibility data
```

Start:

```text
NEW shadow generation ID

NEW monolithic outputs

NEW Stage-1 outputs

NEW Stage-2 outputs

NEW invocation IDs
```

for the full active monitored universe.

---

# 39. Active monitored universe

Re-enumerate active monitored names read-only at shadow start.

Last verified reference:

```text
22 active monitored stocks
```

Use actual current task-start set.

No monitoring registration/stop mutations.

---

# 40. Same-packet shadow contract

For each active ticker:

```text
one reproducible local frozen packet
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

# 41. Full shadow topology

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

# 42. Shadow hard-stop policy

Hard stop only for:

```text
runtime/schema hard failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

true objective financial semantic failure

true PPE-proxy-as-FCF attribution

unsupported current FCF claim under the frozen current-claim contract

business-delta capability/direction violation

market-expectation anchor-eligibility violation

financial-sector framework misuse / exclusion false reject

price/technical/supply Core contamination

Stage-2 actual language/evidence contamination

ADR/security-basis violation

core mutation

production side-effect attempt

aggregate finalization failure
```

Do NOT hard-stop on a claim merely because:

```text
candidate uses PPE proxy somewhere else
+
unrelated configured FCF condition exists elsewhere.
```

---

# 43. Shadow FCF scope audit

For every candidate containing BOTH:

```text
ocf_less_ppe_capex
and
FCF terminology
```

report:

```text
ticker

proxy-use claim paths

FCF claim paths

claim-local refs

field semantic role

whether each FCF claim is:
- proxy attribution
- configured/future FCF condition
- unconfirmed requirement
- current supported FCF claim
- current unsupported FCF claim
- not-FCF disclaimer

hard result
```

This is essential to prove the fix is not over-permissive.

---

# 44. Special IBM acceptance

In the NEW shadow,
if IBM produces semantically equivalent content:

```text
OCF-PPE proxy used as cash-conversion evidence

plus

FCF reacceleration confirmation condition

plus

FCF stagnation invalidation condition
```

it should PASS when:

```text
no field calls the PPE proxy FCF

configured FCF conditions use their own business-condition refs

no unsupported current FCF numeric/state assertion is made.
```

Do not force IBM direction/stance values.

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

Neither monolithic nor two-stage path is automatically ground truth.

---

# 46. Full compatibility goal

M12AR must finally complete:

```text
all active monitored names

monolithic vs two-stage
same-packet comparison

one final row per ticker

aggregate finalization PASS
```

Do not add boundary/delta/holder policy changes mid-generation.

The current priority is obtaining the complete clean compatibility cohort.

---

# 47. Formal fictional diagnostic context — preserve

M12AQ formal proof currently shows:

```text
primary direction unstable subjects = 0

FIC-FIN-05:
HOLD / HOLD / HOLD

new-buyer:
WAIT / WAIT / WAIT

holder:
REVIEW / REVIEW / REVIEW

business delta:
UNCHANGED / UNCHANGED / UNCHANGED
```

Business-delta materiality variance remains:

```text
FIC-FIN-02:
UNRESOLVED / WEAKENED / UNRESOLVED

FIC-FIN-06:
STRENGTHENED / STRENGTHENED / UNRESOLVED
```

Holder variance remains:

```text
FIC-FIN-08:
HOLDABLE / REVIEW / HOLDABLE
```

Do not repair these in M12AR.

They are the next policy-review inputs after full shadow completion.

---

# 48. Partial M12AQ shadow remains diagnostic only

M12AQ completed 12 / 18 calls.

Do not use those partial outputs as the formal compatibility cohort.

They may be preserved only for:

```text
failure forensic

IBM exact replay

reporting regression checks
```

No majority voting or cross-generation stitching.

---

# 49. Next policy handoff

If full M12AR shadow completes without systematic architecture regression:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

Use:

```text
M12AQ formal fictional proof
+
M12AR complete monitored shadow
```

Focus:

```text
1. remaining adjacent directional boundary behavior in real monitored names

2. FIC-FIN-02 / FIC-FIN-06 business-delta materiality

3. FIC-FIN-08 HOLDABLE / REVIEW holder boundary

4. new-buyer stance differences with stable core

5. whether MarketExpectationEvidenceView reduced prior threshold crossings
```

Do not perform that policy repair inside M12AR.

---

# 50. Remote / main / production policy

M12AR is LOCAL-ONLY.

Required:

```text
remote_push_count = 0
raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0
main_merges = 0

deployments = 0
automatic_monitoring_resume = 0
```

Do not ask for GitHub push permission.

---

# 51. Production side-effect firewall

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

Monitoring schedules remain paused.

---

# 52. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ar-scope-freeze

04-integrated-main-lineage-freeze

05-m12aq-ibm-stage2-failure-reproduction

06-ibm-ppe-proxy-evidence-forensic

07-ibm-configured-fcf-signal-forensic

08-financial-claim-row-extractor-code-audit

09-candidate-global-proxy-scope-root-cause

10-stage2-condition-ref-binding-audit

11-fcf-claim-scope-architecture-options

12-fcf-claim-scope-architecture-decision
```

---

# 53. Required claim-scope artifacts

Produce:

```text
13-financial-claim-row-contract-v2

14-stage2-confirmation-ref-binding-contract

15-stage2-invalidation-ref-binding-contract

16-summary-no-global-ref-inheritance-contract

17-ppe-proxy-claim-local-scope-contract

18-configured-fcf-condition-contract

19-current-fcf-claim-safety-contract

20-proxy-equivalence-hard-failure-contract

21-cross-field-proxy-isolation-contract
```

---

# 54. Required exact replay artifacts

Produce:

```text
22-m12aq-ibm-exact-stage2-offline-replay

23-m12aq-context04-stage2-four-row-replay

24-m12am-tsla-not-fcf-regression

25-m12an-ppe-proxy-negative-regressions

26-ibm-fcf-claim-scope-table
```

Expected IBM exact replay:

```text
PASS

ppe_only_cash_conversion_proxy_called_fcf = 0

candidate-global proxy leakage = 0
```

unless a separate genuine unsupported current FCF claim is proven.

If so:
report that exact claim separately.

---

# 55. Required fixtures

Produce:

```text
27-ppe-proxy-direct-mislabel-negative-fixtures

28-unrelated-configured-fcf-positive-fixtures

29-cross-field-ppe-fcf-isolation-fixtures

30-stage2-condition-ref-binding-fixtures

31-current-unsupported-fcf-negative-fixtures

32-not-fcf-disclaimer-regressions

33-period-claim-row-regressions
```

At minimum include FCF-SCOPE-N01 through N04
and FCF-SCOPE-P01 through P05.

---

# 56. Required frozen-regression artifacts

Produce:

```text
34-financial-sector-exclusion-freeze

35-market-expectation-evidence-view-freeze

36-business-delta-convergence-freeze

37-ppe-proxy-model-facing-label-freeze

38-stage2-korean-lexical-freeze

39-monitoring-transition-ownership-freeze

40-financial-temporal-scope-freeze

41-qtd-ytd-wc-debt-safety-freeze

42-adr-security-basis-freeze

43-two-stage-ownership-freeze

44-price-timing-renderer-no-change
```

---

# 57. Required semantic-hash / fictional reuse artifacts

Produce:

```text
45-model-prompt-semantic-hash-freeze

46-model-schema-semantic-hash-freeze

47-evidence-projection-semantic-hash-freeze

48-business-delta-semantic-hash-freeze

49-expectation-semantic-hash-freeze

50-two-stage-semantic-hash-freeze

51-m12aq-fictional-24-row-financial-reaudit

52-formal-fictional-proof-reuse-decision
```

Artifact 52 may be:

```text
REUSE_AUTHORIZED
```

only if no model-facing semantic hash changed
and all 24 formal rows remain hard PASS.

Otherwise:

```text
STOP
FULL_FICTIONAL_REPROOF_REQUIRED
```

Do not run shadow in the same task after unplanned model-facing drift.

---

# 58. Required deterministic tests

Produce:

```text
53-focused-test-results

54-full-local-test-results

55-ruff-and-diff-results

56-hosted-ci-portability-observation

57-new-shadow-model-call-gate
```

No shadow model calls before artifact 57 PASS.

---

# 59. Required NEW shadow setup artifacts

Produce:

```text
58-shadow-generation-manifest

59-task-start-active-monitored-universe

60-shadow-packet-inventory

61-shadow-packet-hash-manifest

62-shadow-delta-view-manifest

63-shadow-expectation-view-manifest

64-shadow-frozen-context-manifest

65-shadow-batching-manifest
```

Use a NEW generation ID.

---

# 60. Required raw shadow artifacts

For every context preserve locally:

```text
monolithic:
prompt
schema
raw output
receipt
transport log
run document

Stage 1:
prompt
schema
raw output
receipt
transport log
run document

Stage 2:
prompt
schema
raw output
receipt
transport log
run document
```

No remote push.

---

# 61. Required full shadow analysis artifacts

Produce:

```text
66-shadow-context-hard-semantic-audit

67-shadow-fcf-claim-scope-audit

68-shadow-ppe-proxy-safety-audit

69-shadow-financial-sector-scope-audit

70-shadow-market-expectation-independence-audit

71-shadow-business-delta-convergence-audit

72-shadow-stage2-language-audit

73-shadow-final-composition-audit

74-shadow-aggregate-finalization-audit

75-shadow-per-ticker-comparison

76-shadow-core-direction-differences

77-shadow-business-delta-differences

78-shadow-new-buyer-differences

79-shadow-holder-differences

80-shadow-same-direction-calibration-differences

81-shadow-expected-contract-corrections

82-shadow-potential-architecture-regressions

83-shadow-unresolved-review-required

84-shadow-adr-security-basis-audit

85-shadow-cyclical-valuation-audit

86-shadow-core-immutability-audit

87-shadow-runtime-audit

88-shadow-aggregate-summary

89-shadow-architecture-decision
```

---

# 62. Required combined diagnostics

If full shadow completes:

```text
90-fic-fin-05-vs-monitored-primary-boundary-analogs

91-expectation-independence-vs-primary-threshold-analysis

92-fic-fin-02-vs-monitored-delta-materiality-analogs

93-fic-fin-06-vs-monitored-positive-delta-analogs

94-fic-fin-08-vs-monitored-holder-analogs

95-new-buyer-monolithic-vs-two-stage-analogs

96-real-fcf-proxy-scope-lessons

97-combined-fictional-monitored-root-cause-summary

98-next-bounded-policy-decision
```

---

# 63. Required completion artifacts

Produce:

```text
99-fcf-claim-scope-repair-success-decision

100-formal-fictional-proof-reuse-success-decision

101-full-shadow-completion-decision

102-existing-monitored-impact-summary

103-two-stage-shadow-compatibility-decision

104-fresh-real-proof-readiness-decision

105-final-main-merge-readiness-note

106-production-no-change

107-schedule-pause-observation

108-remote-push-prohibition-audit

109-master-workflow-update

110-program-completion
```

---

# 64. Shadow acceptance

Require:

```text
all planned shadow calls complete

all active tickers represented exactly once

aggregate finalization PASS

candidate-global PPE proxy scope leakage = 0

true PPE-proxy-as-FCF violations = 0

configured/future FCF false rejects = 0

unsupported current FCF false accepts = 0

not-FCF disclaimer false rejects = 0

financial-sector exclusion false rejects = 0

financial-sector true misuse = 0

market-expectation anchor violations = 0

expectation view mismatches = 0

business-delta semantic projection mismatch = 0

business-delta true direction contradiction = 0

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

# 65. Fresh-real / main / production readiness

At M12AR completion:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

Even if the full shadow completes.

The next task should consume the complete clean cohort for:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

No fresh unseen proof inside M12AR.

---

# 66. Failure handling

## A. Exact IBM candidate has a genuine direct proxy-as-FCF attribution

If code/evidence audit proves that:

```text
IBM FCF language is actually bound to E27
```

rather than E30/E31/configured conditions:

```text
keep the hard FAIL
next_scope =
STAGE2_FCF_CONDITION_EVIDENCE_GROUNDING_REVIEW
```

Do not weaken the validator.

## B. Candidate-global fallback is required to catch other true violations

Do not preserve it unchanged.

Design a claim-local replacement
and prove the negative fixtures.

If impossible:

```text
next_scope =
FINANCIAL_CLAIM_EVIDENCE_SCOPE_ARCHITECTURE_REVIEW
```

No model calls.

## C. Repair lets direct OCF-PPE→FCF misuse pass

```text
STOP
FCF_SCOPE_REPAIR_TOO_PERMISSIVE
```

## D. Repair changes model-facing semantics

```text
STOP
FULL_FICTIONAL_REPROOF_REQUIRED
```

Do not reuse M12AQ formal proof.

## E. Full shadow completes cleanly

Expected:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

## F. Full shadow shows systematic architecture regressions

Use the appropriate bounded compatibility review instead.

---

# 67. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch

latest_result_zip_sha256
latest_result_integrity

m12aq_failure_ticker
m12aq_failure_error

fcf_scope_root_cause

financial_claim_row_contract_version

candidate_global_ppe_proxy_scope_fallback_count_before
candidate_global_ppe_proxy_scope_fallback_count_after

stage2_confirmation_ref_binding_enabled
stage2_invalidation_ref_binding_enabled

ibm_exact_replay_status

ibm_proxy_claim_path_count
ibm_configured_fcf_condition_count
ibm_unconfirmed_fcf_summary_count

ibm_true_proxy_as_fcf_violation_count
ibm_candidate_global_proxy_leak_count

unsupported_current_fcf_false_accept_count
configured_fcf_false_reject_count

ppe_proxy_fcf_safety_regression_count
not_fcf_disclaimer_false_reject_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
evidence_projection_semantic_change_count
business_delta_semantic_change_count
expectation_semantic_change_count
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

shadow_candidate_global_proxy_leak_count

shadow_true_ppe_proxy_as_fcf_violation_count
shadow_configured_fcf_false_reject_count
shadow_unsupported_current_fcf_false_accept_count

shadow_financial_sector_exclusion_false_reject_count
shadow_financial_sector_true_misuse_count

shadow_expectation_anchor_violation_count
shadow_expectation_view_projection_mismatch_count

shadow_business_delta_semantic_projection_mismatch_count
shadow_business_delta_direction_contradiction_count

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

# 68. Artifact integrity

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

# 69. Final task principle

M12AQ finally produced a complete clean formal fictional proof.

The next hard stop occurs only in the real monitored shadow:

```text
IBM Stage 1:
uses a valid OCF-PPE cash-conversion proxy.

IBM Stage 2:
talks about FCF reacceleration / FCF stagnation
as configured future business conditions.

current validator:
because the candidate uses the PPE proxy ANYWHERE,
treats FCF wording ANYWHERE ELSE
as if it might be the proxy mislabeled as FCF.
```

That scope is too broad.

The correct M12AR flow is:

```text
preserve the hard rule:
OCF-PPE is not FCF

→ bind each financial claim to its own evidence scope

→ bind Stage-2 condition text to its own condition refs

→ stop candidate-global PPE proxy taint from leaking into unrelated FCF conditions

→ keep explicit OCF-PPE→FCF attribution hard-failing

→ keep unsupported current FCF claims conservatively controlled

→ offline re-audit the complete M12AQ fictional proof

→ if model-facing semantics are unchanged,
   reuse that formal proof

→ start a completely new full 22-name monitored shadow

→ finally obtain the complete clean compatibility cohort

→ then move to the actual boundary / delta-materiality / holder policy review
```

Do NOT:

```text
turn OCF-PPE into FCF

ban the term FCF everywhere

remove FCF safety validation

allow current unsupported FCF claims

inherit every financial ref in the candidate into every summary

resume the stopped M12AQ shadow

stitch partial shadow generations

rerun fictional models unnecessarily

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring
```

A valid cash-conversion proxy in one field
must not contaminate an unrelated FCF business condition in another field.
