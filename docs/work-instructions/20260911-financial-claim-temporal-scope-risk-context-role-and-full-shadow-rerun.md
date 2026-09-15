# Thesis Monitor — Financial Claim Temporal Scope + Risk-Context Role + Full Monitored Shadow Rerun

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-financial-claim-temporal-scope-risk-context-role-and-full-shadow-rerun.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-financial-claim-temporal-scope-risk-context-full-shadow-rerun-report.zip
```

Master-workflow phase:

```text
M12AH — Integrated-Main Financial Claim Temporal Scope
         A. Generic Prospective-Risk vs Current-State Classification
         B. Risk-Context Field Semantics Repair
         C. Current-Net-Debt Safety Preservation
         D. Existing Fictional Output Offline Re-Audit
         E. Full 22-Name Monitored Shadow Rerun
```

M12AG successfully fixed:

```text
price/chart monitoring transition leakage into Directional Core

business-delta use of price confirmation / risk-reward transitions

configured explicit conditional net-debt false reject
```

but the new full shadow generation stopped after its first monolithic context
because of a narrower generic temporal-scope problem.

The model wrote for `005490`:

```text
risk_context.text =
"현금창출과 순부채의 동반 악화,
 투자 대비 자본효율 하락,
 희석 확대가 핵심 위험이다."
```

The validator treated this as:

```text
CURRENT_DIRECTIONAL_BASIS
```

because:

```text
risk_context
```

is currently included in the generic current-direction field list
and the sentence has no explicit `if/when/하면/경우` marker.

But the supporting evidence was:

```text
E01 STRUCTURAL_RISK / 논리 약화 조건
"FCF 감소와 순부채 증가가 동반"

E17 STRUCTURAL_RISK / 논리 약화 조건
"CAPEX 증가에도 ROIC가 하락"

E25 STRUCTURAL_RISK / 논리 약화 조건
"전환·희석 가능 주식수가 의미 있게 증가"
```

These are configured/prospective risk conditions,
not evidence that those conditions are currently fulfilled.

M12AH must solve this generically without weakening
unsupported-current-net-debt controls.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-monitoring-transition-ownership-conditional-netdebt-scope-full-shadow-rerun-report.zip
```

Verified SHA-256:

```text
ab4fbdb9c58d8b6e329ef4e8ee8ca4d5cc9f6d34e38ed7cd5ef68cd384870fb3
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 144
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

The ZIP contains:

```text
144 indexed payloads
+ artifact-index.json
= 145 entries
```

Recompute before trusting the bundle.

---

# 2. M12AG completion status

M12AG stopped:

```text
status =
STOPPED_OBJECTIVE_SEMANTIC_HARD_FAILURE

stop =
context-01 / monolithic / 005490
```

Runtime:

```text
planned shadow calls = 18
completed = 1
not run = 17

monolithic output tickers = 4
semantic PASS = 3
semantic FAIL = 1

Stage 1 calls = 0
Stage 2 calls = 0

timeout = 0
capacity failure = 0
orphan = 0
wrapper retry = 0
```

Partial first-context semantic result:

```text
000660 PASS
003690 PASS
005490 FAIL
005930 PASS
```

Do not infer any two-stage compatibility result from M12AG.

---

# 3. M12AG ownership repair — freeze successful

M12AG measured:

```text
price confirmation Core leaks:
before = 4
after = 0

price risk-reward Core leaks:
before = 3
after = 0

supply Core leaks after = 0

business-delta price-evidence violations = 0

Timing canonical fact loss = 0
```

The following lineage is now frozen:

```text
monitoring:confirmation_transition
from price_structure.registered_rule_state.confirmation
→ TECHNICAL_STATE / Timing-owned

monitoring:risk_reward_transition
from price_structure.risk_reward
→ RISK_REWARD_PRICE / Timing-owned
```

Do not reopen ownership routing in M12AH.

---

# 4. M12AG explicit conditional contract — freeze successful

M12AG added roles:

```text
CURRENT_STATE_ASSERTION

CURRENT_DIRECTIONAL_BASIS

CURRENT_NUMERIC_CLAIM

CONFIGURED_CONDITIONAL_CHECK

FUTURE_REEVALUATION_CONDITION

INVALIDATION_CONDITION

UNKNOWN_OR_AMBIGUOUS
```

and proved:

```text
explicit future/configured conditional net-debt claims PASS

unsupported current net-debt claims still FAIL

conditional wording does not immunize a separate current fulfilled claim
```

Current unsupported net-debt false accepts:

```text
0
```

Do not weaken these controls.

---

# 5. M12AG exact 005490 failure

New M12AG monolithic output:

```text
ticker = 005490

overall direction =
HOLD 5.0:5.0

business thesis change =
UNCHANGED

new buyer =
WAIT

holder =
HOLDABLE
```

The only objective hard failure was:

```text
net_debt_claim_without_complete_net_debt_evidence
```

on:

```text
risk_context.text
```

Sentence:

```text
"현금창출과 순부채의 동반 악화,
 투자 대비 자본효율 하락,
 희석 확대가 핵심 위험이다."
```

The same output also had an explicitly conditional `business_reevaluation_down`:

```text
"현금창출 감소와 순부채 증가가 동반되거나
 투자 확대에도 자본효율이 하락하면
 하향 재평가한다."
```

The explicit conditional path is not the remaining problem.

The remaining problem is:

```text
nominalized prospective risk language
inside risk_context.
```

---

# 6. Root cause in current validator

Current code conceptually does:

```text
if explicit conditional language:
    conditional/future role
elif numeric:
    current numeric role
elif field path in CURRENT_DIRECTION_PATHS:
    current directional basis
...
```

And:

```text
risk_context
```

is included in:

```text
CURRENT_DIRECTION_PATHS
```

Therefore any net-debt phrase in `risk_context`
without explicit conditional tokens becomes current by default.

This conflates two valid `risk_context` uses:

```text
A. fulfilled/current risk state

B. prospective risk scenario / risk inventory
```

M12AH must separate them.

---

# 7. Risk-context semantics

`risk_context` is NOT equivalent to:

```text
sell_driver

material_directional_anchor_basis

core_investment_judgment
```

It may contain:

```text
current confirmed fundamental risks

or

prospective conditions that would weaken the investment logic
```

Examples:

## Current

```text
"순부채가 이미 증가해 재무 부담이 커졌다."

"높은 순부채 부담이 현재 핵심 위험이다."

"순부채 증가로 현금흐름 방어력이 약화됐다."
```

These require current evidence.

## Prospective risk inventory

```text
"현금창출 감소와 순부채 증가가 핵심 위험이다."

"FCF 감소와 순부채 증가의 동반 발생이 주요 위험이다."

"투자 확대와 순부채 증가가 겹치는 경우가 핵심 리스크다."
```

When supported only by configured weakening/invalidation conditions
and no current fulfillment assertion is made,
these are not current-state claims.

---

# 8. Add a generic prospective-risk role

Preferred additive role:

```text
PROSPECTIVE_RISK_SCENARIO
```

Exact name may differ.

The role means:

```text
The text names a risk event/state that would matter if it occurs,
but does not assert that it has occurred now.
```

This role:

```text
does NOT require current complete net-debt evidence merely for mentioning net debt

does NOT establish a current negative Directional anchor

does NOT establish business_thesis_change

does NOT mark a configured warning as fulfilled
```

It is descriptive risk inventory.

---

# 9. Temporal role must use three inputs

Do not classify from words alone.

Use:

```text
1. field semantic role

2. evidence provenance / source role

3. linguistic fulfillment markers
```

The classifier should answer:

```text
Is this financial claim:
- current/fulfilled,
- prospective/configured,
- or unresolved?
```

No one signal should dominate universally.

---

# 10. Field-role contract

Freeze path behavior.

## Always current-direction fields

At minimum:

```text
buy_drivers

sell_drivers

dominant_evidence

core_investment_judgment

material_directional_anchor_basis
```

A net-debt application in these fields requires current complete evidence,
unless the actual text is clearly quoting a future condition
and the schema meaning permits such content.

Prefer rejecting prospective-only content from these fields
rather than granting broad exemptions.

## Explicit future fields

At minimum:

```text
business_reevaluation_up

business_reevaluation_down

business_invalidation_condition
```

Conditional/configured language may be prospective.

## Mixed field

```text
risk_context
```

must be classified by fulfillment + provenance.

Do not put `risk_context` in a blanket current-direction list.

---

# 11. Evidence-provenance contract

For a claim in `risk_context`,
supporting refs matter.

Configured/prospective evidence classes include:

```text
STRUCTURAL_RISK / 논리 약화 조건

STRUCTURAL_RISK / 무효화 조건

stored strengthen/weaken/invalidation signal definitions

other explicitly configured future checks
```

Current/fulfilled evidence classes include:

```text
typed current financial evidence

same-period current financial comparisons

current company events/facts

confirmed current debt/liquidity facts

fulfilled monitoring fundamental transitions
```

A configured signal alone cannot prove current fulfillment.

---

# 12. Prospective-risk safe classification

A `risk_context` claim may be:

```text
PROSPECTIVE_RISK_SCENARIO
```

only if all are true:

```text
1. the wording does not contain a current fulfillment assertion

2. the wording does not make a current numeric financial claim

3. the cited net-debt-related support is configured/prospective risk evidence
   rather than current incomplete financial evidence

4. the text describes risk exposure/event/scenario,
   not current magnitude/state

5. the same candidate does not use the claim elsewhere
   as a current directional anchor
```

If uncertain:

```text
UNKNOWN_OR_AMBIGUOUS
```

and fail closed where current evidence would be required.

---

# 13. Current-fulfillment markers

Preserve/enhance detection for current fulfilled statements.

Korean examples:

```text
현재
이미
지금

증가했다
늘었다
상승했다
악화됐다
악화되었다
높아졌다
발생했다
나타났다
확인됐다
확인되었다

~로 인해
~때문에
~에 따라
```

when these grammatically assert the financial state occurred.

Examples:

```text
"순부채가 증가해 부담이 커졌다."

"순부채 증가로 재무 안정성이 약화됐다."

"현재 순부채 부담이 높다."
```

These remain current claims.

Do not rely only on exact token lists;
use bounded clause/aspect structure where needed.

---

# 14. Nominalized prospective-risk patterns

Support structures such as:

```text
X 감소와 Y 증가가 핵심 위험이다

X 악화·Y 증가의 동반 발생이 리스크다

Y 증가 위험

Y 증가 가능성

Y가 늘어나는 상황

Y 증가와 X 감소가 겹치는 경우
```

BUT do not blindly classify all noun phrases as prospective.

For example:

```text
"높은 순부채가 핵심 위험이다."
```

is a current-state magnitude assertion.

And:

```text
"순부채 증가는 이미 확인된 핵심 위험이다."
```

is current fulfillment.

---

# 15. English support

The architecture must remain language-generic enough for US monitored names.

Prospective:

```text
"weaker cash generation alongside rising net debt is a key risk"

"the risk of net debt increasing while FCF weakens"

"higher leverage would weaken the thesis"
```

Current:

```text
"net debt has increased"

"net debt is currently high"

"higher net debt is weighing on financial resilience"

"net debt rose and is now a key negative anchor"
```

Do not make Korean-only semantics.

---

# 16. Numeric claims

Preserve:

```text
current numeric net-debt claims require complete evidence.
```

Explicit conditional numeric thresholds may remain prospective:

```text
"if net debt / EBITDA exceeds 3x, reevaluate"
```

This is not a current 3x assertion.

Do not reverse the current conditional-before-numeric safety ordering.

---

# 17. Current directional use overrides prospective label

Even if `risk_context` wording is prospective,
the same net-debt concept must require current evidence
if candidate fields use it as:

```text
sell driver

dominant evidence

core judgment

material anchor

current business delta support
```

Example:

```text
risk_context:
"순부채 증가가 핵심 위험"

sell_driver:
"순부채가 높아 SELL"
```

Result:

```text
FAIL
```

No risk-context exemption may immunize the current claim elsewhere.

---

# 18. Current fulfillment inside risk_context

`risk_context` itself can contain current claims.

Example:

```text
"순부채가 이미 증가했고 현금 버퍼가 얇아진 점이 핵심 위험이다."
```

This is:

```text
CURRENT_STATE_ASSERTION
or
CURRENT_DIRECTIONAL_BASIS
```

and requires complete current evidence.

Do not make all `risk_context` prospective.

---

# 19. Configured source does not override explicit current assertion

If supporting evidence is only a configured weakening condition,
but the model writes:

```text
"순부채가 증가했다."
```

the claim is current and unsupported.

Result:

```text
FAIL
```

Evidence provenance can support a prospective interpretation,
not rewrite explicit current tense.

---

# 20. Mixed current + prospective sentence

Example:

```text
"현재 현금창출이 약하고, 순부채가 더 증가하는 경우가 핵심 위험이다."
```

This contains:

```text
current FCF assertion
+
prospective net-debt scenario
```

Classify claim components separately if needed.

Do not assign one temporal role to the entire sentence
when material financial concepts have different scopes.

If component-level parsing is too broad for M12AH,
fail closed rather than incorrectly exempting a current claim.

---

# 21. Preferred architecture level

Preferred fix:

```text
generic financial claim temporal-scope classifier
```

rather than:

```text
a POSCO-specific exception

a "핵심 위험이다" whitelist

a net-debt-only regex patch
```

The role logic should be usable for other financial frameworks such as:

```text
cash deterioration

debt increase

inventory build

receivables deterioration

cash conversion weakness
```

when the same current-vs-prospective distinction arises.

Do not broaden into a complete NLP parser rewrite.

---

# 22. No model prompt change by default

Preferred:

```text
Directional prompt change count = 0

Stage 1 prompt change count = 0

Stage 2 prompt change count = 0
```

The model's sentence is semantically acceptable as risk inventory.

The validator should understand it.

If prompt changes are claimed necessary:

```text
STOP
explain why deterministic temporal-role classification cannot solve it.
```

---

# 23. Exact M12AG 005490 replay — required

Replay the exact M12AG output.

Expected:

## risk_context

Text:

```text
"현금창출과 순부채의 동반 악화,
 투자 대비 자본효율 하락,
 희석 확대가 핵심 위험이다."
```

Supporting evidence:

```text
E01 / E17 / E25
all configured STRUCTURAL_RISK weakening conditions
```

Expected net-debt temporal role:

```text
PROSPECTIVE_RISK_SCENARIO
```

Expected:

```text
net_debt_claim_without_complete_net_debt_evidence = 0
```

## business_reevaluation_down

Expected:

```text
FUTURE_REEVALUATION_CONDITION
```

No current net-debt error.

---

# 24. M12AG partial outputs re-audit

Re-audit all four context-01 monolithic outputs under the new classifier.

Expected:

```text
000660 PASS

003690 PASS

005490 PASS
if no separate current unsupported claim exists

005930 PASS
```

Do not rewrite model outputs.

If 005490 still has another legitimate current unsupported net-debt claim:

```text
STOP
document exact field/path/text/evidence.
```

---

# 25. Hard negative fixtures

At minimum:

## TEMP-N01

```text
risk_context:
"현재 순부채 부담이 높다."
no complete evidence
→ FAIL
```

## TEMP-N02

```text
risk_context:
"순부채가 증가했다."
no complete evidence
→ FAIL
```

## TEMP-N03

```text
sell_driver:
"순부채가 높아 SELL 근거다."
no complete evidence
→ FAIL
```

## TEMP-N04

```text
risk_context prospective text
+
sell_driver current unsupported claim
→ FAIL
```

## TEMP-N05

```text
configured risk evidence
+
model rewrites it as current fulfilled fact
→ FAIL
```

## TEMP-N06

```text
"높은 순부채가 핵심 위험이다."
without complete evidence
→ FAIL
```

---

# 26. Positive fixtures

At minimum:

## TEMP-P01

```text
risk_context:
"현금창출 감소와 순부채 증가가 핵심 위험이다."

support =
configured weakening conditions only

no current claim elsewhere

→ PASS / PROSPECTIVE_RISK_SCENARIO
```

## TEMP-P02

```text
"현금창출 악화와 순부채 증가의 동반 발생이 주요 리스크다."
→ prospective
```

## TEMP-P03

```text
"순부채 증가 위험을 모니터링한다."
→ prospective
```

## TEMP-P04

```text
"if FCF weakens while net debt rises, the thesis should be reevaluated"
→ future condition
```

## TEMP-P05

```text
current complete net-debt evidence
+
"현재 순부채가 증가했다"
→ supported current claim PASS
```

## TEMP-P06

```text
explicit future numeric threshold
"if net debt / EBITDA exceeds 3x"
→ prospective threshold, not current numeric assertion
```

---

# 27. Unknown / ambiguous fixtures

Examples:

```text
"순부채 증가가 부담이다."

"net debt growth is a concern."
```

without clear provenance/tense.

Do not automatically exempt.

Use:

```text
UNKNOWN_OR_AMBIGUOUS
```

unless configured-risk provenance and field semantics
make the prospective role sufficiently clear.

Fail closed for current-evidence requirements where unresolved.

---

# 28. Provenance conflict fixture

Example:

```text
risk_context text looks prospective

but support includes:
- configured weakening condition
- current partial net-debt event
```

If the current event is incomplete/unsafe
and the candidate implies current fulfillment:

```text
FAIL
```

Do not let one configured ref launder an unsafe current ref.

---

# 29. Business-delta no-change

M12AH must not alter:

```text
business-delta eligibility semantics

price/timing evidence ownership

absolute-state-to-delta rules

alias/canonical resolution
```

Required:

```text
business_delta_semantic_change_count = 0
```

The current task is financial claim temporal scope only.

---

# 30. Price/Timing ownership no-change

M12AG ownership repair remains authoritative.

Required:

```text
price_confirmation_core_leak_count = 0

price_risk_reward_core_leak_count = 0

supply_core_leak_count = 0

timing_fact_loss_count = 0
```

Do not move Timing facts back into Core.

---

# 31. Fictional offline re-audit

M12AG proved:

```text
fictional Stage 1 input drift = 0
```

M12AH changes only deterministic validation,
not model-facing input/prompt/schema.

Therefore:

```text
do not rerun fictional model calls
```

if all are true:

```text
all 24 M12AE-R2 fictional outputs can be re-audited offline

new validator introduces no new false accept/reject

fictional input hashes remain unchanged

two-stage schemas/prompts remain unchanged
```

Create:

```text
fictional_temporal_scope_reaudit
```

If any fictional output changes objective semantic status unexpectedly:

```text
STOP
FULL_FICTIONAL_REPROOF_REQUIRED
```

---

# 32. Existing current-current safety corpus re-audit

Re-run all prior financial semantic regression fixtures:

```text
M12/M12R QTD/YTD

M12C/M12D WC grounding

debt completeness

FCF labeling

prior-year-end vs YoY

normalized earnings

financial-sector framework scope

conditional net-debt fixtures

ADR/security-basis where applicable
```

No new false accepts.

---

# 33. Shadow rerun must be a new generation

If deterministic gate passes:

```text
start a completely NEW monitored shadow generation.
```

Do not resume M12AG.

Do not stitch its context-01 outputs.

New generation must recreate:

```text
task-start active universe

frozen packet hashes

all contexts

all invocation IDs
```

No selective retry.

---

# 34. Active monitored universe

At task start re-enumerate active monitored stocks read-only.

Last verified M12AG set:

```text
22 names

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

Use actual task-start universe.

Do not mutate registrations.

---

# 35. Frozen packet contract

Use one local reproducible packet per ticker.

Required:

```text
provider_source_fetches = 0
```

The same packet hash must feed:

```text
monolithic control

Stage 1

Stage 2 evidence/citation context
```

No external refresh.

No stale-vs-fresh mixing.

---

# 36. Full shadow topology

For N active stocks:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total calls = 3 × context_count
```

At N=22:

```text
18 planned calls
```

No repetitions.

No judge calls.

No fresh unseen companies.

---

# 37. Shadow stop policy

Hard stop only for:

```text
runtime/schema hard failure

packet hash mismatch

invalid evidence identity

objective financial semantic failure

business-delta unsupported-change violation

financial-sector framework misuse

ADR/security-basis violation

Stage 2 core mutation

production-side-effect attempt
```

Do NOT stop for:

```text
monolithic vs two-stage direction difference

balance difference

business-delta difference

new-buyer difference

holder difference
```

Those must be collected across the complete cohort.

---

# 38. Shadow comparison taxonomy — preserve

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

No majority vote.

No control-path supremacy assumption.

---

# 39. Special 005490 acceptance

For new 005490 monolithic/Stage 1 outputs:

Allowed:

```text
risk_context may summarize
"FCF 감소 + 순부채 증가"
as a prospective key risk.
```

Not allowed:

```text
claiming current net debt rose/is high
without complete current evidence.
```

Required:

```text
prospective_netdebt_risk_claim_count >= 0

unsupported_current_netdebt_claim_count = 0

conditional/prospective false reject = 0
```

Do not force Directional output.

---

# 40. Special 003690 / 005930 acceptance

Require:

```text
price confirmation transitions absent from Core

price risk-reward transitions absent from Core

business delta supported only by fundamental change evidence

Timing facts retained
```

No regression from M12AG.

---

# 41. Financial-sector / ADR / cyclical audits

Preserve:

```text
003690 insurance framework safety

SKHY ADR/security-basis safety

memory/material cyclical valuation framework safety
```

Any objective basis violation is a hard stop.

---

# 42. Two-stage architecture remains frozen

M12AH must NOT modify:

```text
Stage 1/Stage 2 ownership

core hash contract

final composer

final external Directional schema

holder contract

new-buyer contract

Directional thresholds

decision-material stability policy
```

The task is not a two-stage redesign.

---

# 43. Production side-effect firewall

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

Monitoring schedules remain paused.

---

# 44. Main integration remains frozen

Do not:

```text
merge newer main

merge integration branch into main
```

M12AH runs on the current integrated-main lineage.

Final main merge remains blocked.

---

# 45. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ah-scope-freeze

04-integrated-main-lineage-freeze

05-m12ag-005490-failure-reproduction

06-current-financial-claim-role-code-audit

07-risk-context-current-path-root-cause

08-005490-evidence-provenance-audit

09-current-vs-prospective-field-role-map

10-temporal-scope-architecture-decision
```

---

# 46. Required temporal-scope artifacts

Produce:

```text
11-financial-claim-temporal-role-contract-v2

12-prospective-risk-scenario-contract

13-risk-context-mixed-field-contract

14-current-fulfillment-marker-contract

15-evidence-provenance-temporal-contract

16-mixed-current-prospective-claim-policy

17-korean-temporal-scope-fixtures

18-english-temporal-scope-fixtures
```

---

# 47. Required safety regression artifacts

Produce:

```text
19-current-netdebt-hard-negative-fixtures

20-prospective-netdebt-positive-fixtures

21-ambiguous-netdebt-fail-closed-fixtures

22-configured-source-current-rewrite-negative-control

23-current-complete-netdebt-positive-control

24-conditional-numeric-threshold-control

25-cross-field-current-override-control
```

---

# 48. Required exact replay artifacts

Produce:

```text
26-m12ag-005490-exact-output-replay

27-m12ag-context01-four-row-reaudit

28-m12ag-explicit-conditional-regression

29-m12af-historical-005490-replay

30-prior-netdebt-safety-corpus-reaudit
```

---

# 49. Required non-impact artifacts

Produce:

```text
31-business-delta-no-change-proof

32-price-timing-ownership-no-change-proof

33-two-stage-architecture-no-change-proof

34-model-prompt-schema-no-change-proof

35-fictional-input-hash-nonimpact-proof

36-fictional-24-output-temporal-reaudit
```

If artifact 36 is not PASS:

```text
STOP
NO SHADOW MODEL CALLS
```

---

# 50. Required deterministic tests

Produce:

```text
37-focused-test-results

38-full-local-test-results

39-ruff-and-diff-results

40-hosted-ci-portability-observation

41-shadow-model-call-gate
```

Gate requires:

```text
exact M12AG 005490 replay PASS

all current unsupported net-debt negative controls PASS

all prospective-risk positive controls PASS

ambiguous cases fail closed

business-delta unchanged

price/Timing ownership unchanged

fictional re-audit PASS

production firewall PASS

model = gpt-5.6-sol / xhigh
```

---

# 51. Required full shadow artifacts

If gate passes:

```text
42-shadow-generation-manifest

43-task-start-active-monitored-universe

44-shadow-packet-inventory

45-shadow-packet-hash-manifest

46-shadow-batching-manifest

47-shadow-monolithic-model-artifacts

48-shadow-stage1-model-artifacts

49-shadow-stage2-model-artifacts

50-shadow-final-composition-artifacts

51-shadow-per-ticker-comparison

52-shadow-core-direction-differences

53-shadow-business-delta-differences

54-shadow-new-buyer-differences

55-shadow-holder-differences

56-shadow-same-direction-calibration-differences

57-shadow-expected-contract-corrections

58-shadow-potential-architecture-regressions

59-shadow-unresolved-review-required

60-shadow-financial-temporal-scope-audit

61-shadow-financial-sector-audit

62-shadow-adr-security-basis-audit

63-shadow-cyclical-valuation-audit

64-shadow-core-immutability-audit

65-shadow-runtime-audit

66-shadow-aggregate-summary

67-shadow-architecture-decision
```

Preserve every model call's:

```text
prompt
schema
raw output
receipt
transport log
run document
```

---

# 52. Combined diagnostic artifacts

If full shadow completes:

```text
68-fic-fin-05-vs-monitored-leverage-analogs

69-fic-fin-06-vs-monitored-fundamental-delta-analogs

70-fic-fin-08-vs-monitored-holder-analogs

71-real-monitoring-temporal-scope-lessons

72-combined-fictional-monitored-root-cause-summary

73-next-bounded-repair-decision
```

Do not preselect the next semantic repair before seeing full shadow.

---

# 53. Shadow runtime acceptance

Require:

```text
all planned calls complete

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0
```

If a model transport hard-fails:

```text
STOP generation
```

No selective retry/stitching.

---

# 54. Shadow hard semantic acceptance

Across completed monitored outputs require zero:

```text
invalid evidence refs

financial grounding failure

unsupported current net-debt false accept

prospective/configured net-debt false reject

business-delta unsupported change

price/technical/supply Core contamination

financial-sector framework misuse

ADR/security-basis violation

Stage 2 core mutation

ticker mismatch
```

Only then architecture differences are interpretable.

---

# 55. Fresh-real readiness remains blocked

At M12AH completion:

```text
fresh_real_proof_readiness = NOT_READY
```

even if full shadow completes cleanly.

Reason:

```text
M12AH's purpose is to finally obtain
a complete existing-monitored compatibility sample.
```

Use that completed sample to choose the next bounded
boundary/delta/holder policy task.

Do not start fresh unseen proof here.

---

# 56. Final main merge remains blocked

Always:

```text
final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

No main merge.

No deployment.

No monitoring resume.

---

# 57. Failure handling

## A. Exact 005490 risk sentence cannot be safely classified prospectively

```text
next_scope =
FINANCIAL_RISK_CONTEXT_SCHEMA_ARCHITECTURE_REVIEW
```

No model calls.

## B. Current unsupported net-debt false accepts appear

```text
STOP
TEMPORAL_SCOPE_REPAIR_TOO_PERMISSIVE
```

No model calls.

## C. Fictional semantic status changes unexpectedly

```text
next_scope =
FULL_FICTIONAL_REPROOF_AFTER_TEMPORAL_SCOPE_CHANGE
```

## D. Full shadow reveals architecture regressions

```text
next_scope =
TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW
```

## E. Full shadow is clean but fictional boundary/delta/holder cases remain

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

using the complete shadow evidence.

## F. Shadow shows systematic business-delta differences

```text
next_scope =
BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW_ON_INTEGRATED_MAIN
```

## G. Shadow shows systematic stance differences

```text
next_scope =
FUNDAMENTAL_STANCE_STAGE_COMPATIBILITY_REVIEW_ON_INTEGRATED_MAIN
```

---

# 58. Program-completion fields

Include at least:

```text
base_integration_head_sha

integration_branch

latest_result_zip_sha256
latest_result_integrity

financial_temporal_scope_root_cause

financial_claim_role_contract_version

prospective_risk_scenario_role_enabled

risk_context_blanket_current_path_removed

risk_context_current_claim_detection_count

risk_context_prospective_claim_detection_count

conditional_netdebt_false_reject_count

prospective_netdebt_false_reject_count

current_unsupported_netdebt_false_accept_count

ambiguous_netdebt_fail_closed_count

m12ag_005490_exact_replay_status

m12ag_context01_reaudit_pass_count
m12ag_context01_reaudit_fail_count

business_delta_semantic_change_count

price_confirmation_core_leak_count
price_risk_reward_core_leak_count
supply_core_leak_count
timing_fact_loss_count

directional_prompt_change_count
stage1_prompt_change_count
stage2_prompt_change_count
schema_change_count

fictional_input_drift_count
fictional_output_reaudit_failure_count

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

shadow_current_netdebt_failure_count
shadow_prospective_netdebt_false_reject_count

shadow_financial_sector_framework_failure_count
shadow_adr_security_basis_failure_count
shadow_cyclical_valuation_framework_failure_count

shadow_core_mutation_after_stance_count

shadow_runtime_timeout_count
shadow_runtime_capacity_failure_count
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

# 59. Artifact integrity

Freeze all artifacts before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 60. Final task principle

M12AG successfully fixed the first real-packet ownership defect.

The new remaining failure is narrower:

```text
"현금창출 감소와 순부채 증가가 동반되면 재평가"
→ correctly recognized as future conditional

but

"현금창출과 순부채의 동반 악화가 핵심 위험"
→ incorrectly treated as a current fulfilled net-debt state
because it sits in risk_context.
```

The correct repair is not:

```text
allow all net-debt mentions in risk_context

or

require the model to always write "if"
```

The correct repair is:

```text
recognize that risk_context is a mixed semantic field

→ classify current fulfilled risk separately from prospective risk scenario

→ use evidence provenance plus linguistic fulfillment markers

→ preserve fail-closed treatment for ambiguous/current unsupported claims

→ keep current Directional anchors strict

→ offline re-audit prior fictional outputs

→ then restart the complete 22-name shadow from a new generation
```

Do NOT:

```text
add a POSCO-specific exception

whitelist "핵심 위험이다"

weaken current net-debt completeness safety

move price monitoring facts back into Core

change business-delta semantics

change Stage 1/Stage 2 architecture

resume M12AG partial generation

refresh providers

merge into main

start fresh unseen proof

return to Astra

resume production monitoring
```

Model risk inventory correctly,
without confusing "a risk to watch" with "a condition already true."
