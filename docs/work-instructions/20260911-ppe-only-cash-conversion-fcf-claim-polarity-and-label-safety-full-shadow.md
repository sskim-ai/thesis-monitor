# Thesis Monitor — PPE-Only Cash-Conversion / FCF Claim Polarity + Label Safety + Full Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-ppe-only-cash-conversion-fcf-claim-polarity-and-label-safety-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-ppe-only-cash-conversion-fcf-claim-polarity-label-safety-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AN — Integrated-Main PPE-Only Cash-Conversion Safety
         A. Freeze successful M12AM Stage-2 lexical repair
         B. Reproduce exact TSLA Stage-1 FCF-proxy false positive
         C. Separate output-claim polarity from model-facing evidence-label safety
         D. Repair the smallest valid layer
         E. Reprove fictional only if model-facing evidence changes
         F. Start a NEW full active-monitored shadow generation
         G. Complete compatibility and policy-handoff diagnostics
```

M12AM successfully fixed the Korean Stage-2 lexical false positive.

The new monitored shadow progressed much farther:

```text
planned calls = 18

completed calls = 14

monolithic calls = 5

Stage 1 calls = 5

Stage 2 calls = 4

completed final compositions = 16

Stage-2 language contamination = 0

Stage-2 language false positive = 0

Stage-2 timing/supply ref contamination = 0

core mutation = 0

timeout = 0
orphan = 0
wrapper retry = 0
```

The generation then hard-stopped at:

```text
context-05 / Stage 1 / TSLA
```

with:

```text
ppe_only_cash_conversion_proxy_called_fcf
```

The exact TSLA candidate did NOT affirmatively call the PPE-only proxy FCF.

It explicitly wrote:

```text
"유형자산 취득 현금지출 차감 후 남는 현금은 제한적이다."

"영업현금흐름은 양수지만
 유형자산 취득 현금지출 차감 후 현금 여력이 제한적이다."

and in unknown_treatments:

"유형자산 취득 현금지출 차감 지표는
 현금 전환 대용치이며
 관리 기준 잉여현금흐름이 아니다."
```

That final sentence is a safety disclaimer:

```text
NOT FCF
```

not an FCF attribution.

M12AN must repair this generically without weakening the hard rule:

```text
OCF - PPE acquisition cash outflow
is NOT management-defined/free cash flow.
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-stage2-korean-lexical-contamination-boundary-repair-new-full-shadow-report.zip
```

Verified SHA-256:

```text
58e40117983d6ea700fd3b1de9c11d5dd33ad716936be1008e8579ab369d13d8
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent ZIP verification:

```text
entries = 247

indexed payloads = 246

artifact hash mismatch = 0

artifact size mismatch = 0

secret scan failure = 0
```

Recompute independently.

---

# 2. M12AM status

M12AM status:

```text
BLOCKED
```

Failure:

```text
failure_call_ordinal = 14

failure_context = context-05

failure_stage = stage1

failure_ticker = TSLA

failure_error =
ppe_only_cash_conversion_proxy_called_fcf
```

Generation:

```text
20260911-m12ai-shadow-20260911T100629Z-515dea40d047
```

Do NOT resume or stitch this generation.

---

# 3. M12AM Stage-2 lexical repair — freeze successful

M12AM successfully repaired:

```text
"주가" false positive inside "수주가"
```

Contract:

```text
stage2-language-contamination-v2
```

Measured:

```text
substring rules before = 10
substring rules after = 0

047810 exact replay = PASS

context-01 Stage-2 historical re-audit = 4 / 4 PASS

context-02 Stage-2 historical re-audit = 4 / 4 PASS

Korean price negative fixtures = 8 / 8 PASS

수주/발주 positive fixtures = 5 / 5 PASS

ambiguous lexeme fixtures = 3 / 3 PASS

new shadow Stage-2 language contamination = 0

new shadow Stage-2 false positive = 0
```

Do not reopen this matcher in M12AN.

---

# 4. M12AK formal fictional proof remains the current formal proof

M12AM reused the M12AK formal fictional proof.

Reuse status:

```text
REUSE_AUTHORIZED
```

Do not rerun fictional models by default.

Whether M12AN must rerun fictional proof depends on whether
the repair changes the model-facing financial evidence surface.

This task explicitly defines both branches.

---

# 5. Exact TSLA canonical financial evidence

TSLA selected:

```text
E27 =
reported operating cash flow

E35 =
derived OCF less PPE acquisition cash outflow
```

E35 model-facing metadata in M12AM:

```text
alias =
E35

domain =
EARNINGS_FINANCIAL_CURRENT

label =
cash_flow_fcf_ppe

metric_refs =
["FCF"]

statement =
"Safely derived OCF less PPE acquisition cash outflow
 for YTD ending 2026-06-30."

financial_semantics.metric =
ocf_less_ppe_capex

semantic_category =
CASH_CONVERSION

evidence_status =
DERIVED_SAFE

quality =
verified

limitations include =
ppe_only_not_management_defined_fcf
```

Canonical numeric value:

```text
352,000,000 USD
```

The canonical semantic metric is:

```text
ocf_less_ppe_capex
```

not:

```text
management-defined FCF.
```

---

# 6. Exact TSLA Stage-1 model usage

The candidate used E35 as:

```text
"유형자산 투자 후 현금 여력이 제한적"

"유형자산 취득 현금지출 차감 후 남는 현금"

"영업현금흐름 대부분을 소모하는 유형자산 투자"

"유형자산 취득 현금지출 차감 후 현금 여력"
```

These descriptions are semantically acceptable.

The candidate also explicitly said:

```text
"유형자산 취득 현금지출 차감 지표는
 현금 전환 대용치이며
 관리 기준 잉여현금흐름이 아니다."
```

This is the opposite of:

```text
"this metric is FCF."
```

---

# 7. Monolithic same-packet control is important forensic evidence

The context-05 monolithic TSLA output selected the SAME E35 evidence
and passed the financial semantic validator.

Its language included:

```text
"설비취득 현금지출 차감 후 현금창출"

"잔여 현금창출 여력이 얇다"

"영업현금의 대부분이 설비취득 지출에 흡수"
```

It did NOT include the explicit phrase:

```text
"잉여현금흐름이 아니다"
```

This strongly suggests the current hard stop is caused by
the Stage-1 disclaimer text being lexically treated as an FCF claim,
not merely by E35 being selected.

M12AN must verify this directly in code.

Do not assume.

---

# 8. Required root-cause split

Before repair classify the failure into one or both:

```text
A. NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE

B. MODEL_FACING_PROXY_METADATA_MISLABEL
```

Definitions:

## A — NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE

The validator sees:

```text
"잉여현금흐름"
or
"FCF"
```

inside:

```text
"not FCF"
"아니다"
"라고 부르지 않는다"
```

and incorrectly counts an affirmative proxy-as-FCF claim.

## B — MODEL_FACING_PROXY_METADATA_MISLABEL

The projected evidence itself exposes:

```text
label = cash_flow_fcf_ppe

metric_refs = ["FCF"]
```

even though canonical metric semantics explicitly say:

```text
ocf_less_ppe_capex
ppe_only_not_management_defined_fcf
```

This is a model-facing naming safety smell.

The two issues must be reported separately.

---

# 9. FCF claim-role contract

Add or refine a bounded FCF claim-role classifier.

Suggested roles:

```text
AFFIRMATIVE_FCF_ATTRIBUTION

NUMERIC_FCF_ATTRIBUTION

PROXY_AS_FCF_ATTRIBUTION

PROXY_DESCRIPTIVE_CASH_CONVERSION

EXPLICIT_NOT_FCF_DISCLAIMER

UNKNOWN_OR_AMBIGUOUS
```

Exact names may differ.

---

# 10. Hard failure cases

A PPE-only proxy must still FAIL if used as:

```text
"FCF is 352 million"

"free cash flow is 352 million"

"잉여현금흐름은 3.52억 달러다"

"이 지표가 FCF다"

"OCF-PPE 기준 FCF"

"FCF가 양수다"
```

when the only supporting evidence is:

```text
ocf_less_ppe_capex
```

and no actual management-defined/full FCF source exists.

Hard error remains:

```text
ppe_only_cash_conversion_proxy_called_fcf
```

or equivalent.

---

# 11. Safe descriptive cases

The PPE-only proxy may safely be described as:

```text
"OCF less PPE acquisition cash outflow"

"유형자산 취득 현금지출 차감 후 남는 현금"

"유형자산 취득 후 잔여 현금 대용치"

"cash-conversion proxy after PPE acquisition cash outflow"

"영업현금흐름 대비 유형자산 취득 부담"
```

These are not FCF claims.

---

# 12. Explicit disclaimer must be safe

The following must be allowed:

```text
"관리 기준 잉여현금흐름이 아니다."

"FCF가 아니다."

"free cash flow가 아니다."

"should not be called FCF."

"is not management-defined free cash flow."

"this is a cash-conversion proxy, not FCF."
```

when:

```text
the candidate does not make an affirmative FCF attribution elsewhere.
```

A safety disclaimer must not create the exact semantic violation
it is trying to avoid.

---

# 13. Negation must be local to the FCF claim

Do NOT make the rule:

```text
if sentence contains "아니다" → safe.
```

Example:

```text
"FCF가 352m인 것은 아니다,
 하지만 사실상 FCF로 본다."
```

must still FAIL.

Likewise:

```text
"not GAAP FCF, but our FCF is 352m"
```

may still contain an affirmative attribution.

Use bounded clause/claim scope.

---

# 14. Field-role behavior

The validator may scan all candidate-owned prose,
including:

```text
unknown_treatments.summary
```

because factual mislabeling should not be allowed anywhere.

Do NOT simply exclude:

```text
unknown_treatments
```

from financial semantic validation.

Instead correctly classify:

```text
EXPLICIT_NOT_FCF_DISCLAIMER.
```

This preserves safety.

---

# 15. Exact M12AM TSLA offline replay

After repair,
revalidate the exact Stage-1 TSLA candidate.

Expected:

```text
selected PPE-only proxy refs =
E35

affirmative proxy-as-FCF claim count =
0

explicit not-FCF disclaimer count >= 1

partial_capex_called_fcf_count =
0

financial semantic status =
PASS
```

All other M12AM TSLA semantics must remain unchanged.

Do not rewrite the output.

---

# 16. Context-05 Stage-1 offline replay

Revalidate all four preserved context-05 Stage-1 candidates:

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

if no separate real semantic violation is found.

Also revalidate the context-05 monolithic output.

Expected:

```text
4 / 4 PASS
```

No regression.

---

# 17. PPE proxy negative fixtures

At minimum:

## FCF-PPE-N01

```text
PPE-only proxy:
"FCF is 352m"
→ FAIL
```

## FCF-PPE-N02

```text
"잉여현금흐름은 352m"
→ FAIL
```

## FCF-PPE-N03

```text
"OCF-PPE를 FCF로 본다"
→ FAIL
```

## FCF-PPE-N04

```text
"not FCF, but 사실상 FCF다"
→ FAIL
```

## FCF-PPE-N05

```text
PPE-only proxy selected in a field
with numeric FCF attribution elsewhere
→ FAIL
```

---

# 18. PPE proxy positive fixtures

At minimum:

## FCF-PPE-P01

```text
"유형자산 취득 현금지출 차감 후 남는 현금"
→ PASS
```

## FCF-PPE-P02

```text
"현금 전환 대용치이며 관리 기준 잉여현금흐름이 아니다"
→ PASS
```

## FCF-PPE-P03

```text
"cash-conversion proxy, not free cash flow"
→ PASS
```

## FCF-PPE-P04

```text
"OCF less PPE acquisition cash outflow is positive"
→ PASS
```

## FCF-PPE-P05

```text
"영업현금흐름 대부분을 유형자산 취득이 소모한다"
→ PASS
```

when evidence supports the relationship.

---

# 19. Input metadata safety audit

Separately audit:

```text
label = cash_flow_fcf_ppe

metric_refs = ["FCF"]
```

against the frozen rule:

```text
OCF-PPE is not called FCF.
```

Answer explicitly:

```text
Is this metadata model-facing?

Can it cause the model to interpret the proxy as FCF?

Does it violate the project's evidence-label safety contract?
```

Do not silently ignore it.

---

# 20. Branch A — output-validator-only repair

Use Branch A only if forensic proof shows:

```text
the hard stop is caused solely by
NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE
```

and model-facing metadata is judged:

```text
not semantically misleading under the existing projection contract
or not actually model-facing in the relevant path.
```

Then:

```text
repair validator claim polarity/negation only

do not change prompts

do not change schemas

do not change evidence labels/metric_refs

offline re-audit formal fictional outputs

reuse M12AK formal fictional proof if all re-audits PASS

start NEW full monitored shadow
```

---

# 21. Branch B — model-facing metadata repair

Use Branch B if the audit concludes:

```text
cash_flow_fcf_ppe
or
metric_refs=["FCF"]
```

is a semantically unsafe model-facing representation of:

```text
ocf_less_ppe_capex.
```

Then repair the projection generically.

Preferred semantic naming:

```text
cash_conversion_ocf_less_ppe
```

or another non-FCF name aligned with repository conventions.

Do NOT expose the derived proxy as:

```text
FCF
```

in label or metric tags.

The canonical typed metric remains:

```text
ocf_less_ppe_capex
```

---

# 22. Branch B metric_refs rule

If `metric_refs` is model-facing,
do NOT retain:

```text
["FCF"]
```

for the PPE-only proxy.

Use only existing safe canonical metric identifiers
supported by the repository.

Do NOT invent a new metric tag solely for display
unless the schema already supports it.

If no safe existing metric-ref vocabulary exists:

```text
empty metric_refs
+
financial_semantics.metric = ocf_less_ppe_capex
```

is preferable to a false FCF tag.

Document the chosen contract.

---

# 23. Branch B requires NEW fictional formal proof

Any model-facing evidence label/tag change invalidates reuse of M12AK
for the affected evidence surface.

Therefore Branch B must run:

```text
NEW full 8 × 3 two-stage fictional proof

Stage 1 calls = 6

Stage 2 calls = 6

total = 12

final outputs = 24
```

before monitored shadow.

Do not rely only on offline re-audit.

---

# 24. Branch A fictional reuse gate

If Branch A is selected,
model-facing hashes must remain unchanged.

Offline re-audit:

```text
all 24 M12AK Stage-1 rows

all 24 M12AK Stage-2 rows

all final compositions
```

with the repaired financial semantic validator.

Required:

```text
new false accept = 0

new false reject = 0

historical hard PASS rows remain PASS

exact TSLA historical row becomes PASS
```

Note:

TSLA M12AM row is monitored shadow,
not part of the M12AK fictional formal proof.

---

# 25. Branch B fictional proof stop policy

If Branch B runs a new fictional proof,
hard stop only for:

```text
runtime/schema failure

invalid evidence identity

objective financial semantic failure

business-delta capability violation

business-delta proven direction contradiction

price/technical/supply Core contamination

Stage-2 actual contamination

core mutation

aggregate finalization failure
```

Do not stop for valid decision-material variance.

---

# 26. Evidence projection regression audit

Whether Branch A or B,
re-audit every packet containing:

```text
ocf_less_ppe_capex
```

for:

```text
canonical semantics

limitations

model-facing label

metric refs

validator interpretation
```

Do not make TSLA-specific code.

Known monitored packets containing related PPE proxy labels
must be enumerated.

---

# 27. M12AM observed proxy-label footprint

The M12AM shadow packet set contains multiple names
with the legacy label:

```text
cash_flow_fcf_ppe
```

including multiple US monitored packets.

Therefore any Branch B repair is cross-company,
not TSLA-specific.

Report:

```text
affected packet/ticker count

before labels

after labels
```

No hard-coded ticker exceptions.

---

# 28. No FCF reconstruction

Preserve:

```text
OCF - PPE acquisition cash outflow
is not management-defined FCF

do not infer missing non-PPE capex

do not reconstruct FCF from incomplete capex

do not call the proxy FCF

do not invent management-defined FCF
```

This remains a hard safety contract.

---

# 29. Stage-2 lexical repair no-change

M12AM language matcher is frozen.

Required after M12AN:

```text
M12AL 047810 exact replay = PASS

real "주가" negative controls = PASS

수주/발주 positive controls = PASS

Stage-2 language semantic change count = 0
```

Do not reopen.

---

# 30. Monitoring-transition / temporal-scope / delta gates no-change

Preserve:

```text
price/timing ownership repair

financial risk temporal-scope repair

BusinessDeltaEvidenceCapability

typed financial direction hints

dynamic business-delta schema

business-delta validators
```

No semantic changes.

---

# 31. Full shadow must be a NEW generation

M12AM stopped after 14 calls.

Validator/projection code will change after those outputs.

Therefore:

```text
do NOT resume M12AM

do NOT stitch contexts 01-04 with new contexts 05-06

do NOT reuse partial outputs as formal M12AN shadow results
```

Start:

```text
NEW shadow generation ID

NEW invocation IDs

NEW model outputs
```

for all active monitored names.

---

# 32. Active monitored universe

At new shadow start,
re-enumerate active monitored names read-only.

Last verified M12AM set:

```text
22 names
```

Use actual current set.

No registration/stop mutation.

---

# 33. Same-packet shadow contract

For every active ticker:

```text
one reproducible local frozen packet
```

Same packet hash feeds:

```text
monolithic

Stage 1

Stage 2
```

No provider refresh.

Required:

```text
provider_source_fetches = 0
```

---

# 34. Full shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic = context_count

Stage 1 = context_count

Stage 2 = context_count

total = 3 × context_count
```

At N=22:

```text
18 calls
```

No repetitions.

No fresh unseen issuers.

---

# 35. Shadow hard-stop policy

Hard stop only for:

```text
runtime/schema failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

objective financial semantic failure

true PPE-proxy-as-FCF attribution

business-delta capability violation

business-delta proven direction contradiction

price/technical/supply Core contamination

Stage-2 actual language/evidence contamination

financial-sector framework misuse

ADR/security-basis violation

core mutation

production-side-effect attempt

aggregate finalization failure
```

Do not stop for architecture decision differences.

---

# 36. Full shadow comparison

If all contexts complete,
produce one row per active ticker comparing:

```text
overall_direction

directional_balance

hold_lean

directional_confidence

business_thesis_change

new-buyer stance

holder stance

selected fundamental evidence

major Unknowns
```

Classify with the frozen compatibility taxonomy.

---

# 37. Partial M12AM outputs are diagnostic only

M12AM reached:

```text
16 completed final compositions
```

before context-05 Stage-1 hard stop.

These partial results may be used only to:

```text
anticipate comparison categories

test reporting code

cross-check the NEW shadow for major inconsistencies
```

They are NOT formal compatibility results.

Do not majority-vote across M12AL/M12AM generations.

---

# 38. Important partial diagnostic signal

The partial M12AM cohort already showed multiple
same-packet monolithic/two-stage adjacent-threshold differences.

Examples in the first 16 completed names include:

```text
010120:
monolithic BUY 6.0
vs
two-stage HOLD 5.5 BUY_LEAN

047810:
monolithic HOLD 5.5 SELL_LEAN
vs
two-stage SELL 6.0

086280:
monolithic HOLD 5.5 SELL_LEAN
vs
two-stage SELL 6.0

RXRX:
monolithic HOLD 5.5 SELL_LEAN
vs
two-stage SELL 6.0
```

Other names show holder/calibration differences.

These are:

```text
INCOMPLETE_DIAGNOSTIC_ONLY.
```

Do not repair boundary policy in M12AN.

Full shadow completion is required first.

---

# 39. Combined policy handoff after full shadow

If shadow completes,
use:

```text
M12AK formal fictional proof

+

M12AN complete monitored shadow
```

to hand off:

```text
primary adjacent-threshold policy

business-delta materiality policy

holder HOLDABLE/REVIEW policy

new-buyer stance architecture differences
```

Expected next scope if no hard architecture regression:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

---

# 40. Remote / main / production policy

M12AN is LOCAL-ONLY.

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

---

# 41. Production side-effect firewall

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

Schedules remain paused.

---

# 42. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12an-scope-freeze

04-integrated-main-lineage-freeze

05-m12am-tsla-failure-reproduction

06-tsla-e35-canonical-financial-forensic

07-tsla-stage1-fcf-claim-span-forensic

08-tsla-monolithic-vs-stage1-same-e35-comparison

09-financial-semantic-fcf-matcher-code-audit

10-proxy-label-model-facing-audit

11-root-cause-split-decision
```

---

# 43. Required FCF-claim artifacts

Produce:

```text
12-fcf-claim-role-contract

13-explicit-not-fcf-disclaimer-contract

14-affirmative-fcf-attribution-contract

15-ppe-proxy-descriptive-language-contract

16-local-negation-scope-contract

17-cross-field-affirmative-override-control
```

---

# 44. Required label-safety artifacts

Produce:

```text
18-ppe-proxy-model-facing-label-safety-decision

19-ppe-proxy-metric-refs-safety-decision

20-affected-proxy-packet-inventory

21-branch-a-or-branch-b-decision
```

Artifact 21 must select exactly:

```text
BRANCH_A_VALIDATOR_ONLY

or

BRANCH_B_METADATA_AND_VALIDATOR
```

No ambiguous hybrid.

---

# 45. Required replay/fixture artifacts

Produce:

```text
22-m12am-tsla-exact-stage1-replay

23-m12am-context05-stage1-four-row-replay

24-m12am-context05-monolithic-four-row-regression

25-ppe-proxy-negative-fixtures

26-ppe-proxy-positive-fixtures

27-english-korean-fcf-negation-fixtures
```

---

# 46. Branch A non-impact artifacts

If Branch A:

```text
28-model-prompt-semantic-hash-freeze

29-model-schema-semantic-hash-freeze

30-evidence-projection-hash-freeze

31-business-delta-semantic-hash-freeze

32-two-stage-semantic-hash-freeze

33-formal-fictional-offline-financial-reaudit

34-formal-fictional-proof-reuse-decision
```

Artifact 34 must be:

```text
REUSE_AUTHORIZED
```

before shadow.

---

# 47. Branch B fictional reproof artifacts

If Branch B:

```text
28b-proxy-evidence-projection-before-after

29b-fictional-proxy-surface-impact

30b-fictional-generation-manifest

31b-stage1-run1-context01
...
all 12 Stage1/Stage2 calls
...
42b-fictional-hard-semantic-audit

43b-fictional-ppe-proxy-safety-audit

44b-fictional-business-delta-audit

45b-fictional-core-immutability-audit

46b-fictional-aggregate-finalization

47b-fictional-shadow-gate-decision
```

Use the existing standard 8 × 3 / 12-call topology.

Do not abbreviate proof.

---

# 48. Required tests before shadow

Regardless of branch:

```text
exact TSLA replay PASS

context-05 Stage1 4/4 PASS

context-05 monolithic 4/4 PASS

affirmative proxy-as-FCF negatives still FAIL

explicit not-FCF disclaimers PASS

no unsupported FCF numeric attribution false accept

Stage-2 lexical regressions PASS

financial temporal-scope regressions PASS

monitoring ownership regressions PASS

business-delta regressions PASS

two-stage ownership regressions PASS

focused tests PASS

full local tests PASS

ruff PASS

git diff --check PASS

production firewall PASS

model target = gpt-5.6-sol / xhigh
```

Then:

```text
Branch A:
formal fictional proof reuse must be authorized

Branch B:
new fictional formal proof must PASS
```

---

# 49. Required NEW shadow artifacts

Produce:

```text
48-shadow-generation-manifest

49-task-start-active-monitored-universe

50-shadow-packet-inventory

51-shadow-packet-hash-manifest

52-shadow-delta-capability-manifest

53-shadow-direction-hint-manifest

54-shadow-frozen-context-manifest

55-shadow-batching-manifest

56-shadow-monolithic-model-artifacts

57-shadow-stage1-model-artifacts

58-shadow-stage2-model-artifacts

59-shadow-context-hard-semantic-audit

60-shadow-ppe-proxy-fcf-safety-audit

61-shadow-stage2-language-audit

62-shadow-final-composition-audit

63-shadow-aggregate-finalization-audit

64-shadow-per-ticker-comparison

65-shadow-core-direction-differences

66-shadow-business-delta-differences

67-shadow-new-buyer-differences

68-shadow-holder-differences

69-shadow-same-direction-calibration-differences

70-shadow-expected-contract-corrections

71-shadow-potential-architecture-regressions

72-shadow-unresolved-review-required

73-shadow-financial-sector-audit

74-shadow-adr-security-basis-audit

75-shadow-cyclical-valuation-audit

76-shadow-core-immutability-audit

77-shadow-runtime-audit

78-shadow-aggregate-summary

79-shadow-architecture-decision
```

---

# 50. Required combined diagnostics

If full shadow completes:

```text
80-fic-fin-05-vs-monitored-primary-boundary-analogs

81-fic-fin-02-vs-monitored-delta-materiality-analogs

82-fic-fin-06-vs-monitored-positive-delta-analogs

83-fic-fin-08-vs-monitored-holder-analogs

84-new-buyer-monolithic-vs-two-stage-analogs

85-real-architecture-compatibility-lessons

86-combined-fictional-monitored-root-cause-summary

87-next-bounded-policy-decision
```

---

# 51. Required completion artifacts

Produce:

```text
88-ppe-proxy-fcf-safety-repair-success-decision

89-fictional-proof-reuse-or-reproof-decision

90-full-shadow-completion-decision

91-existing-monitored-impact-summary

92-two-stage-shadow-compatibility-decision

93-fresh-real-proof-readiness-decision

94-final-main-merge-readiness-note

95-production-no-change

96-schedule-pause-observation

97-remote-push-prohibition-audit

98-master-workflow-update

99-program-completion
```

---

# 52. Shadow acceptance

Require:

```text
all planned shadow calls complete

one final comparison row per active ticker

aggregate finalization PASS

true PPE-proxy-as-FCF violation count = 0

not-FCF disclaimer false reject count = 0

invalid refs = 0

financial hard semantic failures = 0

business-delta capability violations = 0

business-delta direction contradictions = 0

price/technical/supply Core contamination = 0

Stage-2 actual contamination = 0

financial-sector misuse = 0

ADR/security basis failure = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0

production side effects = 0
```

Decision differences are measured,
not hard failures.

---

# 53. Fresh-real / main / production readiness

At M12AN completion:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

Even if shadow completes.

The next bounded policy review must consume the full shadow first.

No fresh unseen proof in M12AN.

---

# 54. Failure handling

## A. Exact TSLA disclaimer still false-rejects

```text
next_scope =
FINANCIAL_CLAIM_NEGATION_SCOPE_ARCHITECTURE_REVIEW
```

## B. Repair lets affirmative proxy-as-FCF claims pass

```text
STOP
FCF_SAFETY_REPAIR_TOO_PERMISSIVE
```

## C. Model-facing proxy metadata is unsafe

Use Branch B.

Do not suppress the audit to preserve proof reuse.

## D. Branch B fictional proof fails

Do not run shadow.

Use smallest failing contract.

## E. Full shadow completes

Expected next scope:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

## F. Full shadow reveals systematic architecture regressions

Use the appropriate bounded compatibility review instead.

---

# 55. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch

latest_result_zip_sha256
latest_result_integrity

m12am_failure_ticker
m12am_failure_error

ppe_proxy_root_cause

negated_fcf_disclaimer_false_positive_confirmed

model_facing_proxy_metadata_mislabel_confirmed

ppe_proxy_label_before
ppe_proxy_label_after

ppe_proxy_metric_refs_before
ppe_proxy_metric_refs_after

ppe_proxy_claim_contract_version

explicit_not_fcf_disclaimer_count

affirmative_proxy_as_fcf_violation_count

not_fcf_disclaimer_false_reject_count

branch_selected

model_prompt_semantic_change_count
model_schema_semantic_change_count
evidence_projection_semantic_change_count
financial_semantic_change_count
business_delta_semantic_change_count
two_stage_semantic_change_count
stage2_language_semantic_change_count

formal_fictional_reuse_status
new_fictional_reproof_run

fictional_model_calls_total
fictional_hard_semantic_failure_count

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

shadow_true_ppe_proxy_as_fcf_violation_count
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

shadow_runtime_timeout_count
shadow_runtime_orphan_count
shadow_wrapper_retry_count

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

# 56. Artifact integrity

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

# 57. Final task principle

M12AM's Stage-2 lexical repair worked.

The next hard stop is different:

```text
TSLA Stage 1 correctly described
OCF less PPE acquisition cash outflow
as a cash-conversion proxy,

then explicitly said:

"it is NOT management-defined free cash flow."

The financial semantic validator counted
the disclaimer's FCF words as if they were
an affirmative FCF attribution.
```

At the same time,
the model-facing evidence metadata still contains:

```text
cash_flow_fcf_ppe

metric_refs=["FCF"]
```

for a canonical metric that explicitly says:

```text
ocf_less_ppe_capex

ppe_only_not_management_defined_fcf.
```

Therefore the correct next flow is:

```text
separate claim polarity from lexical mention

→ make explicit "not FCF" disclaimers safe

→ keep affirmative FCF attribution hard-failing

→ independently audit whether model-facing proxy labels/tags
   themselves violate the OCF-PPE-not-FCF contract

→ if only validator changes:
   offline re-audit and reuse formal fictional proof

→ if model-facing metadata changes:
   run a new full fictional formal proof

→ in either valid branch:
   start a completely new full monitored shadow generation

→ complete all active monitored comparisons

→ finally hand off to the true
   boundary / delta-materiality / holder policy review
```

Do NOT:

```text
remove the FCF safety validator

treat OCF-PPE as management-defined FCF

hard-code TSLA

ignore unsafe model-facing metadata merely to preserve proof reuse

exclude unknown_treatments from semantic validation

resume/stitch the stopped M12AM generation

majority-vote prior shadow generations

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring
```

A statement that says "this is not FCF"
must not be punished for using the words "FCF."
