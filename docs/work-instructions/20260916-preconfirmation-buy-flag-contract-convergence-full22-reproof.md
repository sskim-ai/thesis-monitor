# Thesis Monitor — Pre-Confirmation BUY Flag Contract Convergence + New Full22 Reproof

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-preconfirmation-buy-flag-contract-convergence-full22-reproof.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-preconfirmation-buy-flag-contract-convergence-full22-reproof-report.zip
```

Master-workflow phase:

```text
M12CA — Pre-Confirmation BUY Contract Convergence
         A. Freeze all successful M12BZ polarity/atomic-claim work
         B. Freeze all prior exact-ref / typed-string / batch-identity / ownership repairs
         C. Reproduce the exact GOOGL preconfirmation_buy_flag_missing failure
         D. BEFORE writing a repair, audit the historical 2026-08-30
            Pre-Confirmation Asymmetry V2 implementation and accepted-ownership path
         E. Determine the exact semantic invariant for pre_confirmation_buy
         F. Keep pre_confirmation_buy independent from new_buyer_axis
         G. Preserve the valid three-axis combination:
            overall BUY + new-buyer WAIT + holder HOLDABLE
         H. Align prompt/schema/validator with the historical canonical contract
         I. Add generic positive/negative fixtures
         J. Run full deterministic regression
         K. Create a NEW full US14 + KR8 generation from call 1
         L. Run the complete proof with no retry/fallback/judge/repair/selective rerun
         M. Re-run local market-context regressions without changing their contracts
         N. Do NOT merge/deploy in M12CA
```

This is a bounded model-contract convergence task.

Do NOT solve it by:

```text
forcing GOOGL to BUY

forcing new_buyer_axis=ATTRACTIVE

turning pre_confirmation_buy into an entry instruction

post-processing false → true

special-casing ticker GOOGL

weakening the existing hard validator.
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260916-maturity-polarity-single-source-convergence-full22-reproof-final-market-context-handoff-report.zip
```

Verified SHA-256:

```text
bd13d6c9d4adb948bcd400dab53bb93d51ffd00b1d6f84545173d8a8720c5864
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
indexed payloads = 158

ZIP entries =
158 indexed payloads
+ artifact-manifest.json
= 159

missing = 0

extra = 0

hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Recompute before work.

---

# 2. M12BZ authoritative repository state

Implementation branch:

```text
codex/20260916-m12bz-maturity-polarity-single-source-convergence
```

Implementation SHA:

```text
60a267c475f89fd39c051266b0e458c468a20184
```

Latest local documentation SHA:

```text
29878d2ecc5ff96add09b25fb7fe0fb2b216b43e
```

M12BZ base local proof lineage:

```text
820593cbf97e50e4e303359b4f36cc0e5b54c91f
```

The branch remains local-only.

Required:

```text
main merge = 0

deployment = 0

remote push = 0.
```

Do not start from an older M12BY/M12BX branch.

---

# 3. M12BZ deterministic baseline — freeze

M12BZ succeeded in the intended polarity convergence.

Contracts now frozen successful:

```text
decision-evidence-polarity-v1

stage2-maturity-polarity-adapter-v1

maturity-atomic-claim-identity-v1

fundamental-core-batch-identity-v1

fundamental-core-exact-ref-fidelity-v1

stage2-exact-ref-fidelity-v1

model-output-exact-ref-fidelity-v1

stage2-frozen-core-ownership-v1

postconfirmation-hold-maturity-v1.
```

Deterministic tests:

```text
focused =
128 PASS

wider =
164 PASS

full =
4044 PASS
63 skipped
2 warnings

Ruff =
PASS

git diff --check =
PASS.
```

Do not reopen those repairs.

---

# 4. M12BZ model proof state

Generation:

```text
20260916-uskr22-m12bz-20260916T003454Z-60a267c475f8
```

Planned calls:

```text
16
```

Started/completed/usable:

```text
7 / 7 / 7.
```

US FUNDAMENTAL_CORE:

```text
14 / 14 PASS.
```

Stage-2 before terminal failure:

```text
schema valid =
6

semantic valid =
5.
```

No retry/fallback/judge/repair/selective rerun occurred.

Do not resume or stitch this generation.

---

# 5. Polarity convergence — freeze as solved

M12BZ result:

```text
historical polarity contract =
decision-evidence-polarity-v1

historical implementation commit =
86b9fc44006c45431ccc1822131df3b4a74eb1ca

reuse classification =
CANONICAL_POLARITY_SERVICE_REQUIRES_THIN_STAGE2_ADAPTER

atomic identity =
maturity-atomic-claim-identity-v1.
```

Result counts:

```text
maturity atomic identity failures = 0

same atomic claim overlap = 0

unproven source overlap = 0

valid mixed-parent source overlap = 1

free-form polarity classifier count = 0.
```

CORZ old raw source overlap no longer fails.

Do NOT reopen maturity-polarity semantics in M12CA.

---

# 6. Exact M12BZ blocker

Ticker:

```text
GOOGL
```

Stage:

```text
US Stage-2 batch 2
model-call ordinal 7.
```

Hard error:

```text
preconfirmation_buy_flag_missing.
```

The raw candidate passed:

```text
schema

exact-ref fidelity

typed-date contract

maturity atomic identity

frozen-core ownership.
```

The semantic validator alone rejected it.

---

# 7. Exact GOOGL candidate — freeze

Fundamental core:

```text
overall decision =
BUY

directional balance =
BUY 6.0 / SELL 4.0

holder =
HOLDABLE.
```

Stage-2:

```text
overall maturity =
PARTIAL

asymmetry =
FAVORABLE

pricing requirement =
BASE_CASE_REQUIRED

confirmation cost =
MEDIUM

preconfirmation error cost =
MEDIUM

timing =
UNFAVORABLE

new buyer =
WAIT

pre_confirmation_buy =
false

preconfirmation_buy_explanation =
null.
```

The existing semantic validator returned:

```text
preconfirmation_buy_flag_missing.
```

This is the exact contract gap to resolve.

---

# 8. Critical three-axis principle

The intended user-facing dimensions are independent.

A valid state may be:

```text
종합 방향 =
BUY

신규 관찰자 =
WAIT

보유자 =
HOLDABLE.
```

This is not contradictory.

Interpretation:

```text
the company/fundamental valuation direction can be BUY,

while a new investor may still WAIT because entry/timing/confirmation conditions
are not favorable,

and an existing holder can remain HOLDABLE because the fundamental holding thesis
is not impaired.
```

M12CA must preserve this.

---

# 9. pre_confirmation_buy is NOT new_buyer_axis

Do NOT equate:

```text
pre_confirmation_buy = true
```

with:

```text
new_buyer_axis = ATTRACTIVE.
```

They answer different questions.

The likely historical role of `pre_confirmation_buy` is a lifecycle/decision-engine flag describing
an analytical BUY before full confirmation.

The exact historical contract must be verified before implementation.

---

# 10. Historical pre-confirmation architecture already exists

Repository workflow records:

```text
Pre-Confirmation Asymmetry Decision Engine V2

work-instruction commit =
46bdf4c

implementation =
c0c9139babb06ead11112aea072a67ef364a9b22.
```

Historical result:

```text
20 canonical packets

BUY 2 / HOLD 14 / SELL 4

003690 and GOOGL =
pre-confirmation BUY candidates

all 20 candidates/messages =
PASS.
```

Historical adjudication:

```text
003690 =
keep v1

GOOGL =
keep v2 pre-confirmation BUY

HUT =
keep v2

RXRX =
keep v2

SNDK =
keep v1.
```

Later accepted-decision ownership recorded:

```text
GOOGL remains the sole accepted pre-confirmation BUY.
```

This historical architecture must be audited BEFORE writing a new flag rule.

---

# 11. Accepted-decision ownership history

Historical accepted ownership:

```text
v2-accepted-decision-ownership-v1
```

Implementation lineage includes:

```text
f55605189ee0179ab4af7030b94d79d706ed32a8
```

and related accepted runtime work.

Audit whether:

```text
pre_confirmation_buy

preconfirmation_buy_explanation
```

are already owned/validated there.

Do NOT create a parallel contract if one already exists.

---

# 12. Required provenance audit

Search current code and Git history for:

```text
pre_confirmation_buy

preconfirmation_buy_flag_missing

preconfirmation_buy_explanation

PreconfirmationDecisionCandidate

Pre-Confirmation Asymmetry

preconfirmation-asymmetry-decision-engine-v2

v2-accepted-decision-ownership-v1.
```

Record:

```text
historical file/function

current file/function

historical invariant

current invariant

prompt rule

schema rule

hard validator rule

renderer/accepted-plan consumers

whether the current M12BZ Stage-2 prompt expresses the invariant.
```

---

# 13. Required reuse classification

Choose exactly one BEFORE code changes:

```text
HISTORICAL_PRECONFIRMATION_CONTRACT_ALREADY_CANONICAL_BUT_PROMPT_BYPASSED

HISTORICAL_PRECONFIRMATION_CONTRACT_REQUIRES_THIN_STAGE2_ADAPTER

CURRENT_VALIDATOR_AND_HISTORICAL_CONTRACT_CONFLICT

HISTORICAL_CONTRACT_OBSOLETE_OR_INCOMPATIBLE.
```

Do not write a new semantic rule until this classification is evidence-backed.

---

# 14. Determine the exact invariant

Audit which combination actually requires:

```text
pre_confirmation_buy = true.
```

Possible factors include:

```text
decision = BUY

overall_maturity != CONFIRMED

pre-confirmation evidence maturity

pricing requirement

asymmetry

confirmation cost

preconfirmation error cost.
```

Do not guess the formula.

Recover it from the historical implementation/tests.

---

# 15. Expected likely semantic meaning — not an instruction to force it

Historical naming strongly suggests:

```text
pre_confirmation_buy = true
```

means:

```text
the analytical overall decision is BUY
even though the evidence state is not fully confirmed.
```

If code evidence confirms this:

GOOGL M12BZ:

```text
decision = BUY

overall_maturity = PARTIAL
```

would require:

```text
pre_confirmation_buy = true.
```

But implement this ONLY after historical code/test confirmation.

---

# 16. Confirmed BUY semantics

Audit whether a fully confirmed BUY should be:

```text
pre_confirmation_buy = false
```

or whether the flag has another meaning.

Do not infer from the field name alone.

Add fixtures based on actual historical contract.

---

# 17. Non-BUY semantics

Audit and preserve whether:

```text
HOLD / SELL
```

must always use:

```text
pre_confirmation_buy = false.
```

If historical contract says yes:

make it explicit in prompt/hard validator.

Do not create a BUY flag for HOLD/SELL.

---

# 18. Explanation ownership

Audit when:

```text
preconfirmation_buy_explanation
```

must be:

```text
non-null
```

and when it must be:

```text
null.
```

Expected design principle if historically supported:

```text
flag true
→ explanation required

flag false
→ explanation null.
```

But confirm from code.

---

# 19. Explanation must not become an entry instruction

If explanation is required,
it should explain:

```text
why the fundamental/economic BUY is acceptable before full confirmation
```

using:

```text
business evidence

valuation

market expectation

asymmetry / confirmation-cost economics.
```

It must NOT say:

```text
buy now

enter immediately

price confirmation reached

technical support means buy.
```

Entry timing remains owned by:

```text
new_buyer_axis

timing

price view.
```

---

# 20. Preserve GOOGL BUY + WAIT possibility

Hard regression:

```text
overall decision = BUY

pre_confirmation_buy = true

new_buyer_axis = WAIT

holder = HOLDABLE
```

must be allowed if the historical preconfirmation contract and evidence justify it.

Do NOT mechanically turn:

```text
pre_confirmation_buy=true
```

into:

```text
new_buyer=ATTRACTIVE.
```

This is a critical M12CA acceptance fixture.

---

# 21. Preserve BUY + unfavorable timing possibility

Likewise:

```text
overall BUY

timing UNFAVORABLE

new buyer WAIT
```

may remain valid.

This is precisely why the system has three axes.

Price/timing cannot erase the fundamental BUY.

---

# 22. Do not use price confirmation as fundamental confirmation

Configured price confirmation such as:

```text
GOOGL $375
```

is:

```text
entry / price confirmation.
```

It is NOT automatically the confirmation referred to by:

```text
pre_confirmation_buy.
```

Audit historical semantics.

Do not create a hidden dependency:

```text
price not confirmed → pre_confirmation_buy=false.
```

unless historical code explicitly owns that semantics,
which would conflict with the newer core/timing separation and require a separate policy review.

---

# 23. Prompt contract repair

After historical audit,
make the Stage-2 prompt state the recovered invariant explicitly.

Do not write a ticker example.

Do not force a direction.

Prompt should distinguish:

```text
overall BUY lifecycle flag

new-buyer timing stance

holder stance.
```

---

# 24. Schema capability audit

Determine whether the current structured-output schema can express the cross-field invariant.

If supported safely:

encode it structurally.

If unsupported:

use:

```text
explicit prompt contract

+
existing hard semantic validator.
```

Do not use unsupported JSON Schema conditionals.

This mirrors the prior post-confirmation maturity strategy.

---

# 25. Existing hard validator stays authoritative

Do NOT weaken:

```text
preconfirmation_buy_flag_missing
```

if historical contract confirms it.

The model should emit the valid flag itself.

No post-processing repair.

---

# 26. Old GOOGL output replay

Replay the exact M12BZ GOOGL output.

Expected:

```text
still INVALID.
```

Required:

```text
candidate modified = false

flag auto-rewrite = false

repair call = false.
```

The old output is forensic evidence.

---

# 27. Positive fixtures

Build generic fixtures from the recovered contract.

Likely required fixture classes include:

## PCB-P01

Pre-confirmation analytical BUY:

```text
decision BUY

not-fully-confirmed maturity

flag true

valid explanation
```

→ PASS if historical contract confirms.

## PCB-P02

Fully confirmed BUY:

use the historically correct flag/explanation behavior.

## PCB-P03

```text
overall BUY

new_buyer WAIT

holder HOLDABLE
```

→ PASS when other evidence is valid.

## PCB-P04

HOLD / SELL normal cases under historical correct flag behavior.

---

# 28. Negative fixtures

At minimum, if supported by the recovered contract:

## PCB-N01

```text
pre-confirmation BUY
flag false
```

→ `preconfirmation_buy_flag_missing`.

## PCB-N02

```text
flag true
explanation null
```

→ hard FAIL.

## PCB-N03

```text
non-BUY
flag true
```

→ hard FAIL if historical contract forbids.

## PCB-N04

```text
pre_confirmation_buy=true
```

causes a mechanical change:

```text
new_buyer WAIT → ATTRACTIVE
```

→ regression FAIL.

## PCB-N05

price confirmation alone sets/clears the fundamental preconfirmation flag

→ regression FAIL.

---

# 29. Historical GOOGL fixture

Locate the historical accepted GOOGL pre-confirmation BUY artifact if available.

Record:

```text
decision

overall maturity

pricing requirement

asymmetry

confirmation cost

preconfirmation error cost

pre_confirmation_buy

explanation

new-buyer equivalent if historical schema had one.
```

Use this as a key provenance fixture.

Do not rebuild it from memory.

---

# 30. Historical 003690 contrast fixture

Because 003690 was also a raw pre-confirmation BUY candidate
but adjudication kept v1:

audit it as a contrast.

The preconfirmation flag describes the raw V2 analytical state,
not automatically the final accepted decision.

Do not conflate:

```text
candidate lifecycle flag
```

with:

```text
accepted-plan ownership after adjudication.
```

---

# 31. Freeze all M12BZ successful contracts

Do NOT change:

```text
decision-evidence-polarity-v1

stage2-maturity-polarity-adapter-v1

maturity-atomic-claim-identity-v1

fundamental-core-batch-identity-v1

exact-ref fidelity

Stage-2 typed strings/dates

frozen-core ownership

postconfirmation hold maturity

three-axis renderer

core vs price/timing

expectation/valuation overlap

BusinessDelta

Persistence V2

KR financial cold-start.
```

---

# 32. Deterministic pre-model gate

Before model calls:

run:

```text
historical preconfirmation provenance audit

historical GOOGL preconfirmation fixture

003690 contrast fixture

preconfirmation flag positive/negative tests

BUY+WAIT+HOLDABLE three-axis fixture

price-confirmation independence fixture

historical polarity regressions

batch-identity regressions

exact-ref regressions

Stage-2 typed/date regressions

frozen-core regressions

postconfirmation maturity regressions

three-axis/core-timing/expectation regressions

BusinessDelta regressions

full local pytest

Ruff

git diff --check.
```

All PASS.

---

# 33. Model-facing change classification

Expected:

```text
Stage-2 prompt semantic change =
yes

Stage-2 schema =
only if supported/required

Stage-2 hard semantic rule =
prefer unchanged if already canonical

Fundamental Core =
unchanged

polarity adapter =
unchanged

typed contracts =
unchanged

decision policy =
unchanged

Persistence V2 =
unchanged.
```

If the task requires changing the definition of BUY/HOLD/SELL or new-buyer stance:

```text
STOP
PRECONFIRMATION_REPAIR_EXPANDED_INTO_DECISION_POLICY_CHANGE.
```

---

# 34. Frozen 22 inputs

Use exact frozen packets:

US:

```text
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
WULF.
```

KR:

```text
000660
003690
005490
005930
010120
012450
047810
086280.
```

Packet SHAs:

```text
US =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

No provider refetch.

No packet semantic mutation.

---

# 35. New full proof generation

Because the model-facing Stage-2 contract changes:

create a NEW generation.

Do NOT reuse/stitch:

```text
M12BZ

M12BY

M12BX

or any earlier partial output.
```

Run from call 1.

Expected complete topology remains derived from the harness
(recently 16 calls).

Freeze before first call.

---

# 36. Model configuration

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No model repair.

No selective rerun.

No ticker retry.

---

# 37. Full22 PASS criteria

Require:

```text
22 / 22 subjects represented

all required calls complete

Fundamental Core batch/identity PASS

Fundamental Core schema/semantic PASS = 22

Fundamental Core exact-ref violations = 0

Stage-2 schema/semantic PASS = 22

preconfirmation flag contract failures = 0

preconfirmation explanation contract failures = 0

mechanical preconfirmation→new-buyer mapping count = 0

price-confirmation→fundamental-preconfirmation contamination = 0

maturity atomic identity failures = 0

same atomic claim overlap = 0

unproven source overlap = 0

Stage-2 typed/date violations = 0

exact-ref violations/fabricated refs = 0

frozen-core false positives = 0

postconfirmation maturity conflicts = 0

final composition valid = 22

BusinessDelta failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchors = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

fallback/judge/repair/selective rerun = 0.
```

No decision distribution target.

---

# 38. Required GOOGL dossier

Report:

```text
overall direction

directional balance

overall maturity

pre_confirmation_buy

preconfirmation_buy_explanation

new_buyer stance

holder stance

timing

pricing requirement

asymmetry

confirmation cost

preconfirmation error cost

price confirmation status

preconfirmation semantic validator result.
```

Required:

```text
no contract error.
```

No forced BUY/HOLD/SELL.

---

# 39. Required three-axis proof

If GOOGL or another subject has:

```text
overall BUY

new buyer WAIT
```

that must remain allowed.

The renderer must show:

```text
종합 방향

신규 관찰자

보유자
```

separately.

Required after full proof:

```text
three_axis_visible_count = 22

mechanical_stance_mapping_count = 0.
```

---

# 40. Market context — freeze successful

Do NOT modify market-context contracts in M12CA.

Kiwoom:

```text
historical commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

KOSPI200 9/1–9/3 replay =
PASS

LeadingMarketSnapshot adapter =
PASS

KOSDAQ150 =
UNAVAILABLE_NOT_YET_PROVEN.
```

Treasury:

```text
historical final commit =
4407cd11a78579e11681b503b2d4e72ee3c3d60f

provider =
FRED

nominal =
DGS3 / DGS5 / DGS10 / DGS30

real =
DFII10

breakeven =
T10YIE

daily parser/render/bp/as-of =
PASS.
```

Re-run local regressions only.

---

# 41. Kiwoom gateway — freeze current gap

Required current config names:

```text
KIWOOM_GATEWAY_URL

KIWOOM_GATEWAY_API_KEY

KIWOOM_GATEWAY_TIMEOUT_SECONDS
```

Current:

```text
URL configured =
false

API key configured =
false

live capability call =
0

live quote call =
0

order/modify/cancel =
0/0/0.
```

Do not request or expose secret values in artifacts.

Do not configure the gateway inside M12CA unless the user/operator separately supplies
the environment in the execution system.

---

# 42. No deployment in M12CA

M12CA proves the final model/message contract first.

Required:

```text
main merge = 0

deployment = 0

scheduler resume = 0

real send = 0.
```

If full22 PASS:

```text
message_model_contract_readiness =
READY.
```

Then:

```text
if Kiwoom gateway is configured:
  next_scope =
  FINAL_DEPLOY_CURRENT_US_KR_MARKET_AND_TICKER_MESSAGE_SMOKE_WITH_NIGHT_FUTURES_AND_TREASURY_CURVE

else:
  next_scope =
  KIWOOM_READONLY_GATEWAY_CONFIGURATION_AND_FINAL_MESSAGE_SMOKE.
```

---

# 43. Production firewall

Required throughout:

```text
production DB mutations = 0

assessment writes = 0

warning mutations = 0

notification queue writes = 0

production sends = 0

monitoring registrations = 0

monitoring stops = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

remote raw model artifact push = 0.
```

---

# 44. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ca-scope-freeze

04-m12bz-failure-freeze

05-googl-preconfirmation-failure-forensic

06-historical-preconfirmation-engine-provenance

07-historical-googl-preconfirmation-fixture

08-historical-003690-preconfirmation-contrast

09-current-preconfirmation-validator-audit

10-current-stage2-prompt-preconfirmation-audit

11-preconfirmation-contract-reuse-classification

12-preconfirmation-invariant-decision.
```

---

# 45. Required implementation/tests

Produce:

```text
13-stage2-preconfirmation-prompt-implementation

14-stage2-preconfirmation-schema-implementation-or-not-required

15-preconfirmation-positive-fixtures

16-preconfirmation-negative-fixtures

17-buy-wait-holdable-independence-fixture

18-price-confirmation-independence-fixture

19-old-googl-output-offline-replay

20-no-candidate-auto-repair-proof

21-historical-preconfirmation-regression-suite

22-polarity-regressions

23-batch-identity-regressions

24-exact-ref-regressions

25-stage2-typed-contract-regressions

26-frozen-core-postconfirmation-regressions

27-three-axis-core-timing-expectation-regressions

28-business-delta-regressions

29-full-local-test-result

30-ruff-diff-result

31-model-facing-hash-manifest.
```

---

# 46. Required full22 proof artifacts

Produce:

```text
32-frozen22-input-identity-manifest

33-new-full22-generation-manifest

34-full22-call-plan

35-fundamental-core-model-artifacts

36-stage2-model-artifacts

37-preconfirmation-flag-audit

38-preconfirmation-three-axis-independence-audit

39-fundamental-core-batch-identity-audit

40-exact-ref-fidelity-audit

41-stage2-typed-contract-audit

42-maturity-polarity-audit

43-frozen-core-ownership-audit

44-postconfirmation-maturity-audit

45-price-timing-immutability-audit

46-expectation-valuation-audit

47-business-delta-audit

48-canonical-semantic-audit

49-final-composition-audit

50-per-ticker-result-matrix

51-googl-preconfirmation-dossier

52-corz-rxrx-skhy-ibm-regression-dossier

53-three-axis-render-audit

54-full22-reproof-decision.
```

---

# 47. Required market-context freeze artifacts

Produce:

```text
55-kiwoom-restoration-regression

56-treasury-restoration-regression

57-market-time-layer-regression

58-market-context-fundamental-ownership-negative-tests

59-kiwoom-gateway-config-status.
```

No live call required if gateway remains unavailable.

---

# 48. Required final decisions

Produce:

```text
60-preconfirmation-contract-convergence-decision

61-message-model-contract-readiness

62-market-context-readiness

63-deployment-readiness

64-next-scope-decision

65-master-workflow-update

66-program-completion.
```

---

# 49. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bz_failure_ticker
m12bz_failure_error

historical_preconfirmation_contract
historical_preconfirmation_work_instruction_commit
historical_preconfirmation_implementation_commit
historical_preconfirmation_service_present
historical_googl_preconfirmation_fixture_found
historical_003690_preconfirmation_fixture_found

preconfirmation_reuse_classification
preconfirmation_flag_invariant
preconfirmation_explanation_invariant

preconfirmation_flag_mechanical_newbuyer_mapping_count
price_confirmation_preconfirmation_contamination_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_policy_change_count

focused_test_result
full_test_result
ruff_result
git_diff_check

frozen_us_packet_sha
frozen_kr_packet_sha
frozen_ticker_count

new_reproof_generation_id
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output

fundamental_core_valid_count
stage2_schema_valid_count
stage2_semantic_valid_count

preconfirmation_flag_failure_count
preconfirmation_explanation_failure_count
preconfirmation_three_axis_violation_count

maturity_atomic_identity_failure_count
maturity_same_atomic_claim_overlap_count
maturity_unproven_source_overlap_count

stage2_typed_contract_violation_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count
stage2_noncanonical_date_count

frozen_core_revalidation_false_positive_count
postconfirmation_maturity_conflict_count

final_composition_valid_count

business_delta_hard_failure_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
core_mutation_count

canonical_bypass_count
legacy_duplicate_semantic_participation_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

three_axis_visible_count
three_axis_missing_count
mechanical_stance_mapping_count

googl_overall_direction
googl_directional_balance
googl_overall_maturity
googl_pre_confirmation_buy
googl_new_buyer
googl_holder
googl_timing

corz_regression_status
rxrx_regression_status
skhy_regression_status
ibm_regression_status

kiwoom_adapter_status
kiwoom_gateway_configured
treasury_local_regression_status

message_model_contract_readiness
market_context_readiness
deployment_readiness

production_db_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends
scheduler_mutation_count
automatic_monitoring_resume

main_merges
deployments
remote_push_count
raw_model_artifact_remote_push_count

top_level_result
next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Use explicit NOT_* values when not measured.

---

# 50. Expected clean result

If the historical contract is recovered and full proof passes:

```text
top_level_result =
PRECONFIRMATION_BUY_CONTRACT_CONVERGENCE_FULL22_PASS

fundamental_core_valid_count = 22

stage2_semantic_valid_count = 22

preconfirmation_flag_failure_count = 0

preconfirmation_explanation_failure_count = 0

preconfirmation_three_axis_violation_count = 0

maturity_atomic_identity_failure_count = 0

same atomic claim overlap = 0

typed-contract violations = 0

exact-ref violations = 0

postconfirmation maturity conflicts = 0

final_composition_valid_count = 22

BusinessDelta failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchor = 0

core mutation = 0

canonical bypass = 0

three_axis_visible_count = 22

message_model_contract_readiness =
READY

market_context_readiness =
LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
or
LIVE_READ_ONLY_PASS
```

Do not force GOOGL's enum.

---

# 51. Failure handling

## A. Historical contract already has the invariant

Reuse it.

Do NOT implement a second preconfirmation engine.

## B. Historical contract and current validator conflict

Stop before model calls:

```text
CURRENT_VALIDATOR_AND_HISTORICAL_PRECONFIRMATION_CONTRACT_CONFLICT.
```

Produce a bounded design decision.

## C. Cross-field schema conditional unsupported

Use:

```text
prompt + hard validator.
```

Do not fake schema enforcement.

## D. GOOGL old output replay becomes valid without changing candidate

That would imply the hard validator was weakened.

STOP unless historical contract proves validator was wrong.

## E. New full22 hard failure

No hotfix inside M12CA.

Choose the smallest bounded next contract scope.

## F. Full22 PASS

Do not deploy.

Move to Kiwoom gateway configuration/final smoke as appropriate.

---

# 52. Final task principle

M12BZ solved the prior maturity-polarity problem by reusing existing architecture.

The new failure is:

```text
GOOGL overall BUY
+
PARTIAL maturity
+
pre_confirmation_buy=false
+
new buyer WAIT
→ preconfirmation_buy_flag_missing.
```

This must NOT be misread as:

```text
BUY requires ATTRACTIVE.
```

The intended three-axis design explicitly allows:

```text
fundamental BUY

new-buyer WAIT

holder HOLDABLE.
```

The correct M12CA sequence is:

```text
recover the historical Pre-Confirmation Asymmetry V2 contract

→ determine the exact lifecycle invariant for pre_confirmation_buy

→ reuse that canonical contract

→ keep the flag separate from entry timing

→ keep price confirmation separate from business confirmation

→ do not post-process model output

→ run a wholly new full22 proof

→ render all three axes

→ only after 22/22 proof, proceed to Kiwoom gateway configuration
   and the final deploy/current-message smoke.
```
