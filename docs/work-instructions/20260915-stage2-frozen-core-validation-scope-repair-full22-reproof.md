# Thesis Monitor — Stage-2 Frozen-Core Validation Scope Repair + New Full 22 Reproof

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-stage2-frozen-core-validation-scope-repair-full22-reproof.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-stage2-frozen-core-validation-scope-repair-full22-reproof-report.zip
```

Master-workflow phase:

```text
M12BW — Stage-2 Frozen-Core Ownership Repair
         A. Freeze successful FUNDAMENTAL_CORE exact-ref fidelity
         B. Freeze successful Stage-2 exact-ref fidelity
         C. Freeze successful post-confirmation maturity contract
         D. Reproduce the exact GOOGL Stage-2 ROIC false reject
         E. Separate immutable frozen-core validation ownership from Stage-2-owned validation
         F. Preserve hard unsupported-metric checks on NEW Stage-2-owned prose
         G. Clarify the Stage-2 prompt so "copy frozen core exactly" does not conflict with
            "do not introduce unsupported ROIC"
         H. Add positive/negative ownership fixtures
         I. Run full deterministic regression
         J. Create a NEW complete US14 + KR8 proof generation
         K. Run the full 22-subject proof from call 1
         L. No fallback / judge / repair / selective rerun
         M. If clean, freeze the recovered historical Kiwoom plan as the next scope
         N. Do NOT reintegrate/deploy night futures in M12BW
```

This is a bounded VALIDATION OWNERSHIP repair.

It is NOT:

```text
a ROIC semantic relaxation

a GOOGL-specific exception

a new financial metric calculation

a new decision policy

a night-futures implementation task.
```

The exact problem is that Stage-2 currently revalidates immutable Stage-1 core prose
with Stage-2-only unsupported-metric rules, even after the frozen core has already passed
the canonical Stage-1 audit and exact core hash/immutability checks.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260915-stage2-exact-ref-fidelity-full22-reproof-mandatory-historical-kiwoom-recovery-report.zip
```

Verified SHA-256:

```text
1a5831c9950567894f553ff5c7bc9c7f1cfa718a0d44064859e8fc3c52a42f02
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
indexed payloads = 142

actual indexed payloads = 142

missing = 0

extra = 0

hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Recompute independently.

---

# 2. M12BV repository/result baseline

M12BV implementation branch:

```text
codex/20260915-m12bv-stage2-exact-ref-fidelity-kiwoom-recovery
```

Implementation head:

```text
3f4129cc06a2b444040e271c7181097ae45f4edf
```

Base deployed/main reference:

```text
9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479.
```

Deterministic gate:

```text
focused =
30 passed; broader focused 133 passed

full local =
3993 passed, 63 skipped, 1 warning

Ruff =
PASS

git diff --check =
PASS.
```

Start from the intended integration line containing M12BS/M12BT/M12BU/M12BV.

Do not drop recovered Kiwoom artifacts or exact-ref repairs.

---

# 3. M12BV successful exact-ref repairs — freeze

FUNDAMENTAL_CORE:

```text
fundamental-core-exact-ref-fidelity-v1

valid count =
14 / 14 US in the completed core phase

exact-ref violations =
0

fabricated refs =
0.
```

Stage-2:

```text
stage2-exact-ref-fidelity-v1

shared contract =
model-output-exact-ref-fidelity-v1

Stage-2 exact-ref violations =
0

Stage-2 fabricated refs =
0

cross-subject ownership failures =
0.
```

Maximum Stage-2 ref catalog:

```text
152 refs / batch
```

Maximum Stage-2 schema size:

```text
57042 bytes
```

No observed schema limit exceeded.

Do NOT reopen exact-ref fidelity in M12BW.

---

# 4. M12BV first hard failure — freeze

Track-A result:

```text
FULL22_REPROOF_NEW_HARD_FAILURE.
```

First failure:

```text
ticker =
GOOGL

stage =
Stage-2 / PRICE_TIMING

batch =
US batch-02

error =
unsupported_metric_or_inference

match =
ROIC.
```

Exact rejected paths:

```text
$.holder_axis.reason.text

$.sell_drivers[1].text.
```

Exact text:

```text
"Search·Cloud 성장축은 보유 근거가 되지만,
 AI CAPEX가 FCF와 ROIC의 구조적 악화로 이어지는지는 계속 점검해야 한다."

"대규모 AI CAPEX에도 FCF와 ROIC가 구조적으로 악화되면
 핵심 논리가 무효화될 수 있다."
```

---

# 5. Critical forensic fact: Stage-2 did NOT invent those ROIC claims

The two rejected fields are part of the frozen FUNDAMENTAL_CORE.

The Stage-2 prompt explicitly required:

```text
Copy every frozen core field exactly.
```

The frozen GOOGL core already contained the exact two ROIC sentences.

FUNDAMENTAL_CORE result:

```text
decision =
BUY

directional_balance =
6.0 / 4.0

holder =
HOLDABLE

fundamental_core_sha256 =
10e665a35a23f96f42fd5b90c7af21309d4bc9a7f1bf4dc7144deaea191dc9cb.
```

That core passed the Stage-1 canonical audit.

Therefore Stage-2:

```text
did not create a new ROIC inference

did not mutate the core

did not alter the holder field

did not alter the sell driver.
```

It copied the already-validated frozen core as required.

---

# 6. Current contract contradiction

The Stage-2 prompt currently contains BOTH:

```text
A. Copy every frozen core field exactly.

B. Do not state or infer ROIC.
```

If the frozen, canonically accepted core legitimately contains
a prospective / stored-thesis ROIC condition,
these instructions conflict.

Likewise, the Stage-2 unsupported-metric validator currently scans
immutable copied core fields as though they were newly generated Stage-2 claims.

This is a validation ownership error.

---

# 7. Root-cause classification

Freeze:

```text
STAGE2_REVALIDATES_IMMUTABLE_FROZEN_CORE_WITH_STAGE2_OWNED_UNSUPPORTED_METRIC_RULES.
```

This is NOT:

```text
UNSUPPORTED_CURRENT_ROIC_CLAIM

GOOGL_SPECIFIC_ROIC_EXCEPTION

CORE_VALIDATOR_BYPASS

ROIC_METRIC_CALCULATION_REQUEST

MODEL_COPY_FAILURE.
```

Do not solve by allowing arbitrary ROIC claims.

---

# 8. Canonical validation ownership principle

The pipeline must have one owner for each claim.

## FUNDAMENTAL_CORE-owned fields

Examples:

```text
decision

directional_balance

buy_drivers

sell_drivers

balance_summary

confidence

decisive_reason

holder_axis.
```

These fields are:

```text
generated by FUNDAMENTAL_CORE

canonically audited by FUNDAMENTAL_CORE validator

frozen by fundamental_core_sha256

copied exactly into Stage-2

protected by core immutability validation.
```

Stage-2 must NOT reinterpret or semantically reclassify these fields.

---

# 9. Stage-2-owned fields

Stage-2 remains responsible for NEW fields such as applicable:

```text
timing

timing_basis

market_expectation

pricing_requirement

driver_maturity

overall_maturity

asymmetry

confirmation_cost

preconfirmation_error_cost

new_buyer_axis

preconfirmation_buy

post_confirmation_hold

upgrade / downgrade conditions where Stage-2 owns them

Stage-2 scenarios / opposing evidence

adjudication fields.
```

Use actual schema ownership.

Stage-2 hard validators remain fully active on these fields.

---

# 10. Frozen-core trust preconditions

Stage-2 may trust the frozen core ONLY if all are true:

```text
1. FUNDAMENTAL_CORE schema validation PASS

2. FUNDAMENTAL_CORE canonical semantic audit PASS

3. fundamental_core_sha256 matches exactly

4. every frozen-core field in Stage-2 candidate equals the frozen core exactly

5. no core mutation detected.
```

If any precondition fails:

```text
Stage-2 candidate hard FAIL.
```

No semantic trust without verified immutable identity.

---

# 11. Validation scope implementation

Refactor the Stage-2 unsupported-metric/inference validator so it receives
or deterministically derives a field-ownership scope.

Preferred conceptual contract:

```text
validate_preconfirmation_stage2_owned_semantics(...)
```

rather than validating the entire combined candidate as newly authored.

Possible implementation styles:

```text
A. Project candidate into Stage-2-owned fields before unsupported-metric scan.

B. Pass excluded immutable-core JSON paths to the scanner.

C. Tag field ownership in schema/service and audit only Stage-2-owned claims.
```

Choose the smallest architecture-consistent option.

Do NOT create ticker-specific exclusions.

---

# 12. Immutable core exclusion must be exact, not broad

Do NOT exclude:

```text
all holder-like text

all sell-driver-like text

all ROIC mentions

all top-level candidate fields.
```

Exclude ONLY the exact frozen-core-owned fields that:

```text
have verified hash identity
and exact-copy equality.
```

A mutated/additional claim in those paths must still fail via core-immutability validation.

---

# 13. Stage-2 unsupported ROIC remains hard

New Stage-2-owned prose must still reject unsupported:

```text
ROIC

CCC

DSO

DPO

runway months

FCF yield

per-share FCF

EV/FCF

P/FCF
```

according to the existing contract.

No relaxation.

Example:

```text
new_buyer_axis.reason.text =
"ROIC가 25%로 올라가면 진입한다."
```

without safe evidence:

```text
hard FAIL.
```

---

# 14. Prospective core condition remains owned by core validator

The GOOGL frozen core's:

```text
"AI CAPEX가 FCF와 ROIC의 구조적 악화로 이어지는지..."
```

is a previously validated core-held future risk/invalidation condition.

M12BW does NOT need to reinterpret its ROIC semantics.

Stage-1 canonical validation already owns that decision.

If there is a concern that Stage-1 itself should reject this:
that would require a separate Stage-1 proof.

M12BV shows the current core audit accepted it.

Do not silently reverse that result inside Stage-2.

---

# 15. Stage-2 prompt clarification

Replace the contradictory blanket wording with a scoped rule equivalent to:

```text
Do not introduce or infer ROIC, CCC, DSO, DPO, runway months,
FCF yield, per-share FCF, EV/FCF, or P/FCF in Stage-2-owned fields.

Frozen FUNDAMENTAL_CORE fields must still be copied exactly,
including any already-validated prospective thesis conditions they contain.

Do not modify frozen core text merely to satisfy Stage-2 metric restrictions.
```

Keep the rule concise.

Do not encourage new ROIC use.

---

# 16. No frozen-core sanitization

Forbidden:

```text
remove "ROIC" from copied core

replace ROIC with generic profitability

edit holder reason

edit sell driver

regenerate Stage-1 core just to avoid the token

post-process core text before Stage-2.
```

Frozen core identity must remain exact.

---

# 17. GOOGL exact positive replay

Offline replay the exact M12BV GOOGL combined Stage-2 candidate
under the corrected ownership-scoped validator.

Expected:

```text
core hash =
PASS

core exact copy =
PASS

core mutation =
0

Stage-2-owned unsupported metric occurrence =
0

combined Stage-2 semantic status =
PASS
```

assuming no other error exists.

Do not edit the output.

This is a deterministic validator-scope replay.

---

# 18. Negative fixture: Stage-2-owned ROIC

Construct a candidate with valid immutable core
but add unsupported ROIC to a Stage-2-owned field, e.g.:

```text
new_buyer_axis.reason

timing_basis

pricing_requirement

scenario text
```

Expected:

```text
unsupported_metric_or_inference

hard FAIL.
```

This proves the repair is not a ROIC whitelist.

---

# 19. Negative fixture: mutated core ROIC

Take a valid frozen core and alter:

```text
holder_axis.reason.text
```

to insert a new unsupported ROIC claim.

Expected:

```text
core immutability / hash mismatch hard FAIL
```

before any frozen-core trust applies.

Do not let ownership exclusion hide mutation.

---

# 20. Positive fixture: copied frozen core prospective metric

A frozen core that already passed Stage-1 canonical audit contains a prospective
thesis condition mentioning ROIC.

Stage-2 copies it exactly.

Expected:

```text
Stage-2 does not re-run unsupported-metric inference on that immutable field.
```

Stage-2-owned fields remain clean.

PASS.

---

# 21. Positive fixture: clean core + clean Stage-2

Normal candidate:

```text
no unsupported Stage-2 metric
```

PASS unchanged.

No regression.

---

# 22. Ownership inventory

Produce a machine-readable list:

```text
field_path

owner_stage

frozen_at_stage2?

stage2_semantic_validator_applies?

immutability_validator_applies?

notes.
```

Cover the complete combined Stage-2 candidate schema.

No ad hoc GOOGL-only logic.

---

# 23. No duplicate semantic engine

Do NOT build a second ROIC classifier.

Reuse the existing unsupported metric validator,
but feed it only the fields it owns.

This is a validation scope repair,
not a semantic implementation fork.

---

# 24. Preserve exact-ref fidelity

Do not change:

```text
model-output-exact-ref-fidelity-v1

fundamental-core-exact-ref-fidelity-v1

stage2-exact-ref-fidelity-v1.
```

Required regression:

```text
fabricated ref count = 0

exact-ref violation count = 0.
```

---

# 25. Preserve post-confirmation maturity

Do not change:

```text
post_confirmation_hold=true
⇒ overall_maturity=CONFIRMED.
```

Required regression:

```text
maturity conflict count = 0.
```

---

# 26. Preserve three-axis / core-timing / expectation-valuation contracts

Do not change:

```text
three-axis renderer

REVIEW copy

price/timing core ownership

holder fundamental ownership

expectation/valuation overlap classifier.
```

Required regression:

```text
price timing core mutation = 0

price timing holder mutation = 0

duplicate expectation/valuation anchor = 0.
```

---

# 27. Deterministic pre-model gate

Before external model calls:

run:

```text
new ownership-scope validator tests

exact GOOGL replay

Stage-2-owned ROIC negative fixture

mutated frozen-core negative fixture

exact-ref regressions

post-confirmation maturity regressions

three-axis regressions

core/timing regressions

expectation/valuation regressions

BusinessDelta regressions

full local pytest

Ruff

git diff --check.
```

All PASS.

---

# 28. Model-facing change classification

Expected:

```text
Stage-2 prompt semantic hash =
changed

Stage-2 schema =
unchanged

FUNDAMENTAL_CORE prompt =
unchanged

FUNDAMENTAL_CORE schema =
unchanged

canonical semantic classification logic =
unchanged

Stage-2 validation scope/orchestration =
changed

exact-ref contracts =
unchanged

Persistence V2 =
unchanged.
```

Report actual hashes.

---

# 29. Frozen 22-subject packets

Use the exact monitored packets:

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

No packet mutation.

---

# 30. New complete proof generation mandatory

Because Stage-2 prompt/validation ownership contract changes:

create a NEW full proof generation.

Do NOT reuse:

```text
M12BV core outputs

M12BV Stage-2 outputs

M12BU/M12BT/M12BS outputs.
```

Run complete architecture from call 1.

No stitching.

---

# 31. Full call plan

Derive the exact complete call plan from the current harness.

Recent expected total:

```text
16 model calls.
```

Freeze before call 1:

```text
ordinal

market

stage

batch

tickers

prompt hash

schema hash

ref-catalog hash

core-ownership-contract hash where applicable.
```

---

# 32. Model configuration

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No repair call.

No selective rerun.

No per-ticker retry.

---

# 33. Proof stop policy

Preserve formal no-repair policy.

If a new:

```text
runtime

schema

exact-ref

semantic

ownership

core-mutation
```

hard failure appears:

record and stop according to current harness policy.

Do not patch/rerun in M12BW.

---

# 34. Full 22 PASS criteria

Require:

```text
22 / 22 subjects represented

FUNDAMENTAL_CORE schema valid = 22

FUNDAMENTAL_CORE semantic valid = 22

FUNDAMENTAL_CORE exact-ref violation = 0

Stage-2 schema valid = 22

Stage-2 semantic valid = 22

Stage-2 exact-ref violation = 0

Stage-2 fabricated refs = 0

frozen-core revalidation false-positive count = 0

Stage-2-owned unsupported metric failure count = 0

post-confirmation maturity conflicts = 0

final composition valid = 22

BusinessDelta hard failure = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchor = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

fallback / judge / repair / selective rerun = 0.
```

No target direction distribution.

---

# 35. GOOGL required dossier

Report:

```text
frozen core decision

frozen core hash

frozen core exact-copy status

overall direction

new-buyer stance

holder stance

market expectation

valuation

overall maturity

price/timing core-anchor count

expectation/valuation overlap class

Stage-2-owned unsupported metric occurrences

frozen-core-only unsupported-metric occurrences.
```

Required:

```text
frozen core exact-copy = PASS

Stage-2-owned unsupported occurrences = 0.
```

GOOGL may be BUY/HOLD/SELL if independently justified.

No target enum.

---

# 36. RXRX required regression

Require:

```text
fabricated ref count = 0

exact ref ownership PASS.
```

No expected direction.

---

# 37. CORZ required regression

Require:

```text
fabricated Stage-2 ref count = 0

post-confirmation maturity conflict = 0.
```

No expected direction.

---

# 38. Three-axis local render

After a clean proof:

render all 22 locally.

Require:

```text
종합 방향 visible = 22

신규 관찰자 visible = 22

보유자 visible = 22

REVIEW user copy safe

mechanical stance mapping = 0.
```

No deployment.

---

# 39. Historical Kiwoom recovery — freeze as completed

M12BV TRACK B is COMPLETE.

Do NOT repeat the full search in M12BW.

Recovered final implementation:

```text
commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

subject =
fix: stabilize structured checkpoints and night futures
```

Recovered code/fixture/tests:

```text
app/services/krx_night_session_contract_service.py

fixtures/20260905-kiwoom-kospi200-night-futures-fixture.json

tests/test_krx_night_session_contract_service.py.
```

Current file hashes match the historical final implementation.

This means:

```text
the code still exists in the current tree.
```

Do NOT search for it again.

---

# 40. Historical 9/1 sample — freeze

Actual preserved KOSPI200 night-futures sample:

```text
business date =
2026-09-01

contract =
202609

open =
1061.0

high =
1061.4

low =
1031.3

close =
1040.5

volume =
30651

session =
NIGHT.
```

Reproduction:

```text
NORMALIZATION_ONLY_PASS.
```

Normalized instrument:

```text
XKRX:KOSPI200:FUTURES.
```

---

# 41. Historical 9/2 sample — freeze

```text
business date =
2026-09-02

contract =
202609

open =
1023.0

high =
1048.35

low =
1020.25

close =
1043.6

volume =
22676

session =
NIGHT.
```

Reproduction:

```text
NORMALIZATION_ONLY_PASS.
```

---

# 42. Historical 9/3 sample — freeze

```text
business date =
2026-09-03

contract =
202609

open =
1030.95

high =
1052.45

low =
1020.75

close =
1049.05

volume =
26252

session =
NIGHT.
```

Reproduction:

```text
NORMALIZATION_ONLY_PASS.
```

---

# 43. Historical parser scope — freeze

Contract:

```text
krx-night-futures-session-quote-v1.
```

Historical 9/1-9/3 rows safely own:

```text
contract_month

instrument

session_type

session_business_date

open

high

low

close

volume.
```

They do NOT safely own:

```text
as_of_timestamp

reference_or_settlement_basis

change

change_percent

session_status_at_observation.
```

Do not fabricate these when reintegrating.

---

# 44. Historical instrument scope — freeze

Recovered actual Kiwoom fixture scope:

```text
KOSPI200 night futures =
FOUND

KOSDAQ150 actual Kiwoom fixture =
NOT FOUND

US futures in historical Kiwoom scope =
NOT FOUND.
```

Therefore next reintegration must:

```text
support KOSPI200 first

keep KOSDAQ150 fail-closed

resolve US futures separately.
```

Do not claim old code covered both indices.

---

# 45. Historical live source/auth — freeze

Recovered historical transport:

```text
Windows Kiwoom OpenAPI+ authenticated gateway

endpoint =
/v1/night-futures/capabilities

source authentication required =
true

consumer data scope =
read-only market data

account/order data required by consumer =
false.
```

Desired future permission:

```text
read-only quote access only.
```

No order/trading calls.

---

# 46. Historical disconnect root cause — freeze

M12BV result:

```text
CODE_STILL_EXISTS_NOT_WIRED

classifications:
TEST_ONLY_PATH
NO_LEADING_MARKET_ADAPTER.
```

Important:

```text
clean-history integration did NOT remove a prior production wiring.

The historical final implementation was never wired into
leading_market_snapshot_service in production.
```

Do not describe this as a merge omission.

The missing work is current-pipeline adapter wiring.

---

# 47. Reuse decision — freeze

M12BV:

```text
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER.
```

Reasons:

```text
typed contract survives

fixture survives

tests survive

9/1-9/3 rows reproduce deterministically

no current production provider/live transport adapter is wired

LeadingMarketSnapshot does not yet own PRIOR_NIGHT_CLOSE reference basis.
```

---

# 48. Current LeadingMarketSnapshot mapping — freeze

Recovered mapping plan:

```text
instrument_id =
DIRECT XKRX:KOSPI200:FUTURES

current_price =
DIRECT last

provider =
DIRECT source

source_timezone =
Asia/Seoul

session_id =
adapter from contract_month + session_business_date + NIGHT

freshness =
deterministic adapter required

as_of =
only direct when a fully typed quote owns observed_at

change_pct =
only direct when PRIOR_NIGHT_CLOSE basis is genuinely owned.
```

If reference/header basis is ambiguous:

```text
suppress change/change_pct.
```

Do not invent comparison basis.

---

# 49. Next task after M12BW PASS

Required:

```text
next_scope =
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

That task should:

```text
reuse the recovered existing KOSPI200 contract/service

implement the read-only current Kiwoom gateway adapter

wire it into LeadingMarketSnapshot

map current typed quote safely

extend PRIOR_NIGHT_CLOSE basis only if current live source explicitly owns it

otherwise show level/session without fabricated change

keep KOSDAQ150 unavailable until actual source proof

resolve US index futures separately through a safe source decision

run final market-message smoke

deploy only after all message contracts pass.
```

Do not implement this inside M12BW.

---

# 50. Deployment remains blocked

M12BW does NOT deploy.

Even after clean 22 reproof:

```text
message_model_contract_readiness =
READY

deployment_readiness =
NOT_READY_PENDING_NIGHT_FUTURES_REINTEGRATION.
```

No main merge.

No deploy.

No scheduler resume.

---

# 51. Production firewall

Throughout M12BW:

```text
production DB mutations = 0

assessment production writes = 0

warning production mutations = 0

notification queue writes = 0

production sends = 0

scheduler mutation = 0

monitoring registration/stop = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

remote raw-model push = 0.
```

External model calls for the frozen 22 reproof are allowed.

---

# 52. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bw-scope-freeze

04-m12bv-track-a-failure-freeze

05-googl-frozen-core-stage2-failure-forensic

06-combined-stage2-field-ownership-inventory

07-stage2-validator-current-scope-audit

08-stage2-frozen-core-trust-contract

09-stage2-validator-scope-repair-decision.
```

---

# 53. Required implementation artifacts

Produce:

```text
10-stage2-owned-field-projection-implementation

11-stage2-unsupported-metric-scope-implementation

12-stage2-prompt-scope-clarification

13-frozen-core-exact-copy-positive-fixture

14-stage2-owned-roic-negative-fixture

15-mutated-core-roic-negative-fixture

16-clean-stage2-regression-fixture

17-exact-googl-old-output-offline-replay

18-no-roic-whitelist-proof.
```

---

# 54. Required deterministic tests

Produce:

```text
19-focused-stage2-ownership-tests

20-exact-ref-regressions

21-postconfirmation-regressions

22-three-axis-core-timing-expectation-regressions

23-business-delta-regressions

24-full-local-test-result

25-ruff-diff-result

26-model-facing-hash-manifest.
```

---

# 55. Required full reproof artifacts

Produce:

```text
27-frozen-22-input-identity-manifest

28-new-full-reproof-generation-manifest

29-full-reproof-call-plan

30-fundamental-core-model-artifacts

31-stage2-model-artifacts

32-fundamental-core-schema-semantic-audit

33-stage2-schema-audit

34-exact-ref-fidelity-audit

35-frozen-core-immutability-audit

36-stage2-owned-unsupported-metric-audit

37-postconfirmation-maturity-audit

38-price-timing-immutability-audit

39-expectation-valuation-audit

40-business-delta-audit

41-canonical-semantic-audit

42-final-composition-audit

43-per-ticker-result-matrix

44-googl-postrepair-dossier

45-rxrx-regression-dossier

46-corz-regression-dossier

47-three-axis-render-audit

48-full22-reproof-decision.
```

---

# 56. Required Kiwoom freeze artifacts

Do NOT rerun historical search.

Produce compact frozen handoff artifacts from M12BV:

```text
49-recovered-kiwoom-implementation-freeze

50-recovered-20260901-sample-freeze

51-recovered-20260902-sample-freeze

52-recovered-20260903-sample-freeze

53-recovered-kiwoom-auth-contract-freeze

54-leading-market-adapter-mapping-freeze

55-night-futures-next-scope-freeze.
```

---

# 57. Required final decisions

Produce:

```text
56-stage2-validation-ownership-repair-decision

57-message-model-contract-readiness

58-deployment-readiness

59-next-scope-decision

60-master-workflow-update

61-program-completion.
```

---

# 58. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bv_failure_ticker
m12bv_failure_error
m12bv_failure_paths
m12bv_failure_texts

stage2_frozen_core_ownership_contract_version

frozen_core_field_count
stage2_owned_field_count

exact_old_googl_replay_status
exact_old_googl_core_hash_match
exact_old_googl_core_copy_match
exact_old_googl_stage2_owned_unsupported_occurrence_count

stage2_owned_roic_negative_fixture_status
mutated_core_roic_negative_fixture_status

stage2_prompt_semantic_change_count
stage2_schema_change_count
fundamental_core_prompt_change_count
fundamental_core_schema_change_count
canonical_semantic_classifier_change_count
stage2_validation_scope_change_count
exact_ref_contract_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
persistence_v2_contract_change_count

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

fundamental_core_schema_valid_count
fundamental_core_semantic_valid_count
fundamental_core_exact_ref_violation_count

stage2_schema_valid_count
stage2_semantic_valid_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count

frozen_core_revalidation_false_positive_count
stage2_owned_unsupported_metric_failure_count

postconfirmation_maturity_conflict_count
final_composition_valid_count

canonical_semantic_failure_count
business_delta_hard_failure_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
core_mutation_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

three_axis_visible_count
three_axis_missing_count

googl_overall_direction
googl_new_buyer
googl_holder
googl_frozen_core_hash_match
googl_stage2_owned_unsupported_metric_count
googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class

rxrx_fabricated_ref_count

corz_overall_direction
corz_overall_maturity
corz_post_confirmation_hold
corz_fabricated_ref_count

historical_kiwoom_final_commit
historical_kiwoom_reuse_decision
historical_20260901_reproduction
historical_20260902_reproduction
historical_20260903_reproduction
historical_kospi200_scope
historical_kosdaq150_scope
historical_us_futures_scope
historical_readonly_auth_requirement
historical_disconnect_root_cause

message_model_contract_readiness
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

Use:

```text
NOT_MEASURED
NOT_APPLICABLE
```

where appropriate.

Do not substitute zero for unknown.

---

# 59. Expected clean outcome

If the ownership repair and reproof pass:

```text
top_level_result =
STAGE2_FROZEN_CORE_VALIDATION_SCOPE_REPAIR_FULL22_PASS

fundamental_core_semantic_valid_count = 22

fundamental_core_exact_ref_violation_count = 0

stage2_semantic_valid_count = 22

stage2_exact_ref_violation_count = 0

stage2_fabricated_ref_count = 0

frozen_core_revalidation_false_positive_count = 0

stage2_owned_unsupported_metric_failure_count = 0

postconfirmation_maturity_conflict_count = 0

final_composition_valid_count = 22

canonical_semantic_failure_count = 0

business_delta_hard_failure_count = 0

price_timing_core_mutation_count = 0

price_timing_holder_mutation_count = 0

expectation_valuation_duplicate_anchor_count = 0

core_mutation_count = 0

three_axis_visible_count = 22

message_model_contract_readiness =
READY

deployment_readiness =
NOT_READY_PENDING_NIGHT_FUTURES_REINTEGRATION

next_scope =
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

Do not force decision enums.

---

# 60. Failure handling

## A. Exact GOOGL old output still fails only because frozen-core ROIC is rescanned

```text
STOP
STAGE2_FROZEN_CORE_SCOPE_REPAIR_INCOMPLETE.
```

No model calls.

## B. Stage-2-owned ROIC negative fixture passes

```text
STOP
STAGE2_UNSUPPORTED_METRIC_GUARD_WEAKENED.
```

No model calls.

## C. Mutated frozen core bypasses validation

```text
STOP
FROZEN_CORE_IMMUTABILITY_TRUST_BROKEN.
```

No model calls.

## D. New hard failure in full reproof

No repair inside M12BW.

Record it.

Do not selectively rerun.

## E. Full 22 clean

Proceed next only to recovered Kiwoom reintegration / final message smoke.

No deployment in M12BW.

---

# 61. Final task principle

M12BV proved:

```text
FUNDAMENTAL_CORE exact-ref fidelity works

Stage-2 exact-ref fidelity works

historical Kiwoom night-futures implementation is recovered.
```

The model reproof did NOT fail because GOOGL invented a new ROIC claim.

It failed because:

```text
Stage-2 copied the already validated immutable core exactly,

then the Stage-2 validator re-scanned those frozen core fields
with a Stage-2 unsupported-metric rule.
```

The correct repair is:

```text
verify core audit + hash + exact copy

→ trust immutable core fields as Stage-1-owned

→ validate only newly authored Stage-2 fields with Stage-2 unsupported-metric rules

→ keep core immutability hard

→ keep unsupported new ROIC hard

→ run a brand-new complete 22-subject proof.
```

Separately, historical Kiwoom recovery is DONE:

```text
final commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

KOSPI200 9/1-9/3 data =
reproduced

reuse decision =
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

root cause =
CODE_STILL_EXISTS_NOT_WIRED.
```

Do NOT search again.

After M12BW passes,
the next task should wire that recovered implementation into the current
LeadingMarketSnapshot / market-message pipeline with read-only quote semantics.

Do NOT:

```text
whitelist GOOGL

relax ROIC globally

sanitize frozen core text

rerun the historical Kiwoom search

build a new KR night-futures connector from scratch

claim KOSDAQ150 historical coverage

claim US futures historical coverage

merge/deploy

resume automation.
```
