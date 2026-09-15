# Thesis Monitor — Fundamental-Core Batch Completeness / Identity Closure + Full22 Reproof + Market-Context Final Readiness

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-fundamental-core-batch-completeness-identity-closure-full22-reproof-market-context-final-readiness.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-fundamental-core-batch-completeness-identity-closure-full22-reproof-market-context-final-readiness-report.zip
```

Master-workflow phase:

```text
M12BY — Two Independent Tracks

TRACK A — FUNDAMENTAL_CORE batch/identity contract closure
  A1. Freeze all successful Stage-2 typed-contract work from M12BX
  A2. Reproduce the exact GOOGL/HUT/IBM batch omission
  A3. Audit every FUNDAMENTAL_CORE batch/identity field, not only ticker count
  A4. Structurally close expected batch cardinality where supported
  A5. Structurally close ticker/packet/claim/date/market identity domains where deterministic
  A6. Preserve hard exact-set / duplicate / missing / extra preflight validation
  A7. Add prompt contract: exactly one core per supplied ticker, no omission, no duplicate
  A8. Add positive/negative completeness/identity fixtures
  A9. Run full deterministic regression
  A10. Create a NEW complete US14 + KR8 proof generation
  A11. Run the complete architecture from call 1
  A12. No fallback / judge / repair / selective rerun

TRACK B — Market-context final readiness
  B1. Freeze the already successful Kiwoom KOSPI200 local reintegration
  B2. Freeze the already successful historical US Treasury restoration
  B3. Verify current code still renders Treasury 3Y/5Y/10Y/30Y + 10Y real + 10Y breakeven safely
  B4. Verify KOSPI200 night-futures adapter still passes 9/1–9/3 fixtures
  B5. Audit whether a configured authenticated READ-ONLY Kiwoom night gateway is now available
  B6. If available, perform ONE read-only quote/capability smoke; order calls remain forbidden
  B7. If unavailable, report exact runtime/config gap without exposing secrets
  B8. Do NOT deploy in M12BY
```

TRACK B runs independently after deterministic tests are green,
even if TRACK A model reproof later fails.

Do not let another model-proof blocker erase the already-restored
night-futures / Treasury work.

---

# 1. Authoritative latest result

Authoritative result bundle:

```text
thesis-monitor-20260916-stage2-typed-contract-closure-full22-reproof-market-context-restoration-report.zip
```

Verified SHA-256:

```text
83cd763078b5a3bb4a50bc3245821c2593899e3667bb109645c844d4464b8fbd
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
artifact_count = 135

ZIP entries =
135 indexed payloads
+ artifact-manifest.json
= 136

missing = 0

extra = 0

hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Recompute before work.

---

# 2. M12BX authoritative summary

Repository:

```text
implementation branch =
codex/20260916-m12bx-stage2-typed-contract-market-context-restoration

implementation head =
eb24f37155fca38c5e993678b0d7261971c9a354

base main =
9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479.
```

Deterministic tests:

```text
focused =
156 PASS

full local =
4022 PASS
63 skipped
2 warnings

Ruff =
PASS

git diff --check =
PASS.
```

Top-level:

```text
M12BX_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY.
```

Per-track:

```text
TRACK A =
FULL22_REPROOF_NEW_HARD_FAILURE

TRACK B =
KIWOOM_KOSPI200_LOCAL_REINTEGRATION_PASS

TRACK C =
US_TREASURY_CURVE_RESTORATION_PASS.
```

---

# 3. Stage-2 typed-contract closure — freeze successful

M12BX performed the requested broad typed-string audit.

Results:

```text
Stage-2 total string fields =
50

genuine free-text fields =
6

typed string fields =
44

unknown typed strings =
0

typed-but-free-string gaps before =
8

typed-but-free-string gaps after =
0

ISO-date fields =
2

closed-enum fields =
30

exact-catalog-ID fields =
4

other typed-string fields =
8

required concrete-date unsatisfiable count =
0.
```

Contract:

```text
driver_maturity.as_of =
CONCRETE_YYYY_MM_DD_SAME_ROW_CITED_REF_OWNED

symbolic "latest" allowed =
false.
```

Do NOT reopen Stage-2 typed-string closure in M12BY.

---

# 4. M12BX model reproof blocker — exact reproduction

New generation:

```text
20260916-uskr22-m12bx-20260915T164818Z-eb24f37155fc
```

Planned calls:

```text
16.
```

Started/completed/usable:

```text
2 / 2 / 2.
```

The stop occurred in:

```text
US FUNDAMENTAL_CORE batch 2.
```

Expected tickers:

```text
GOOGL
HUT
IBM.
```

Returned tickers:

```text
GOOGL
HUT.
```

Missing:

```text
IBM.
```

Returned core count:

```text
2
```

expected:

```text
3.
```

No unexpected ticker was returned.

Failure:

```text
preflight_fundamental_core_scope_mismatch:2.
```

Root cause classification:

```text
FUNDAMENTAL_CORE_BATCH_CARDINALITY_AND_TICKER_IDENTITY_NOT_STRUCTURALLY_CLOSED.
```

The preflight exact-set validator correctly failed closed.

Do NOT weaken it.

---

# 5. Raw output proves this is omission, not semantic rejection

The returned GOOGL and HUT cores are schema-parseable.

The model simply omitted IBM from the output array.

Current schema for `cores`:

```json
{
  "type": "array",
  "minItems": 1,
  "maxItems": 20,
  "items": {
    "$ref": "#/$defs/AcceptedV2FundamentalCoreCandidate"
  }
}
```

Current ticker field:

```text
type = string
```

without a batch-specific closed enum.

Therefore a two-item output for a three-subject batch is structurally valid,
and only the post-schema preflight catches the omission.

M12BY must close this class generically.

---

# 6. Do NOT patch IBM

Forbidden:

```text
special-case IBM

retry IBM alone

append a synthetic IBM core

run a judge to fill IBM

change the batch after output

accept 2/3 as partial success.
```

The repair must apply to every FUNDAMENTAL_CORE batch.

---

# 7. FUNDAMENTAL_CORE complete identity inventory

Audit all model-generated identity/scope fields in the current FUNDAMENTAL_CORE schema.

At minimum:

```text
top-level contract

packet_id

claim_id

market

assessment_date

cores array cardinality

cores[].ticker.
```

Also audit any other:

```text
batch id

schema version

source identity

stage identity

hash/catalog identity
```

that the model is currently expected to copy.

Produce:

```text
JSON path

current schema

expected deterministic value/domain

model-visible source

can be schema-closed?

hard validator exists?

prompt rule exists?

repair decision.
```

Do not limit the audit to `cores`.

---

# 8. Batch cardinality contract

For every model call with N expected subjects,
the model-facing schema should require:

```text
cores length == N
```

using supported structural constraints.

Preferred:

```text
minItems = N

maxItems = N.
```

Run a structured-output capability test proving dynamic equal min/max is supported.

Do not hard-code:

```text
3
```

globally because some frozen batches contain:

```text
2
```

subjects.

Generate the schema per batch.

---

# 9. Exact ticker-domain contract

For each batch:

```text
cores[].ticker
```

must be restricted to the exact expected ticker set.

Preferred:

```text
enum = expected_batch_tickers.
```

Examples:

Batch 2:

```text
["GOOGL", "HUT", "IBM"].
```

Do not permit arbitrary ticker strings.

---

# 10. Exact set still requires a hard validator

Even with:

```text
length = N

ticker enum = expected set,
```

the model could theoretically return:

```text
GOOGL
GOOGL
HUT
```

and still have N items.

Therefore preserve/enforce hard preflight:

```text
returned ticker set == expected ticker set

duplicate ticker count = 0

missing ticker count = 0

extra ticker count = 0.
```

Do not rely on schema alone.

---

# 11. Candidate order — prompt-level unless safely structural

Preferred prompt rule:

```text
Emit exactly one core for every supplied ticker,
in the same order as FUNDAMENTAL_CORE_CONTEXT.
Do not omit, duplicate, replace, or reorder subjects.
```

If the current structured-output subset safely supports fixed-position tuple/prefix schemas
with a ticker const per position, audit that option.

However:

```text
do NOT introduce unsupported prefixItems/conditionals merely for ordering.
```

Exact set + duplicate/missing validator remains authoritative.

Order mismatch may be:

```text
hard fail
```

only if current downstream architecture genuinely depends on stable order.

Do not invent a new ordering requirement if ticker-keyed composition is already safe.

---

# 12. Top-level deterministic identity closure

The current prompt supplies:

```text
FUNDAMENTAL_CORE_IDENTITY
```

with deterministic values such as:

```text
contract

packet_id

claim_id

market

assessment_date.
```

Audit whether each should be model-generated at all.

If the output contract must include them:

prefer one-element enums / const-equivalent supported forms.

Examples:

```text
contract enum = ["v2-accepted-fundamental-core-v1"]

packet_id enum = [current packet_id]

claim_id enum = [current claim_id]

market enum = [current market only]

assessment_date enum = [current assessment_date].
```

Do not leave deterministic identity fields as arbitrary strings.

---

# 13. Do not overclose semantic/narrative fields

The batch/identity audit must NOT constrain:

```text
decision

directional balance

confidence

holder stance

buy/sell driver prose

decisive reason prose

evidence-driven rationale
```

beyond their existing contracts.

This is not a decision-policy repair.

---

# 14. Exact evidence refs remain frozen

Do NOT change:

```text
fundamental-core-exact-ref-fidelity-v1

stage2-exact-ref-fidelity-v1

model-output-exact-ref-fidelity-v1.
```

Required regression:

```text
fabricated ref count = 0

exact-ref violation count = 0.
```

---

# 15. Stage-2 typed contract remains frozen

Do NOT change the successful M12BX typed closure.

Required regression:

```text
typed_free_string_gap_count = 0

noncanonical date count = 0

symbolic date fabrication count = 0.
```

---

# 16. Frozen-core ownership remains frozen

Do NOT change:

```text
stage2-frozen-core-ownership-v1.
```

Required:

```text
frozen-core revalidation false positive count = 0.
```

---

# 17. Post-confirmation maturity remains frozen

Do NOT change:

```text
post_confirmation_hold=true
⇒
overall_maturity=CONFIRMED.
```

Required:

```text
conflict count = 0.
```

---

# 18. Three-axis / core-timing / expectation-valuation remain frozen

Preserve:

```text
종합 방향 / 신규 관찰자 / 보유자

REVIEW safe user copy

price/timing cannot mutate fundamental core

price/timing cannot create holder fundamental stance

expectation/valuation shared evidence cannot be double-counted.
```

No further policy change in M12BY.

---

# 19. Exact batch-2 old output replay

Replay the exact M12BX batch-2 output under the repaired schema.

Expected:

```text
2 returned cores for expected 3

→ SCHEMA/CARDINALITY FAIL.
```

Do not add IBM.

Do not modify output.

---

# 20. Positive cardinality fixtures

At minimum:

## FCB-P01

```text
expected = 3
returned = 3
unique exact tickers
→ PASS.
```

## FCB-P02

```text
expected = 2
returned = 2
unique exact tickers
→ PASS.
```

## FCB-P03

Exact top-level identity values:

```text
→ PASS.
```

---

# 21. Negative cardinality / identity fixtures

At minimum:

## FCB-N01

```text
expected = 3
returned = 2
→ schema cardinality FAIL.
```

## FCB-N02

```text
expected = 3
returned = 4
→ schema cardinality FAIL.
```

## FCB-N03

```text
expected = [A,B,C]
returned = [A,A,B]
→ duplicate/set validator FAIL.
```

## FCB-N04

```text
ticker = unrelated D
→ ticker enum/schema FAIL.
```

## FCB-N05

Wrong packet_id

```text
→ schema/identity FAIL.
```

## FCB-N06

Wrong claim_id

```text
→ schema/identity FAIL.
```

## FCB-N07

Wrong assessment_date

```text
→ schema/identity FAIL.
```

## FCB-N08

Wrong market

```text
→ schema/identity FAIL.
```

No auto-correction.

---

# 22. Full identity-domain gap target

After deterministic closure:

```text
fundamental_core_batch_identity_free_string_gap_count = 0
```

for proof-critical deterministic identity/scope fields.

Do not count narrative fields.

---

# 23. Model-facing change scope

Expected M12BY Track-A changes:

```text
FUNDAMENTAL_CORE dynamic schema =
changed

FUNDAMENTAL_CORE prompt =
small clarification possible

FUNDAMENTAL_CORE semantic decision logic =
unchanged

Stage-2 prompt/schema =
unchanged from M12BX

canonical semantic validators =
unchanged

exact-ref contracts =
unchanged

three-axis =
unchanged

Persistence V2 =
unchanged.
```

Any decision-policy or canonical semantic classifier change:

```text
STOP
BATCH_COMPLETENESS_REPAIR_EXPANDED_INTO_SEMANTIC_POLICY_CHANGE.
```

---

# 24. Deterministic pre-model gate

Before external model calls:

run:

```text
batch cardinality capability tests

ticker enum tests

top-level identity closure tests

exact M12BX batch-2 replay

duplicate/missing/extra preflight tests

exact-ref regressions

Stage-2 typed-string regressions

frozen-core ownership regressions

post-confirmation regressions

three-axis/core-timing/expectation regressions

BusinessDelta regressions

full local pytest

Ruff

git diff --check.
```

All PASS.

---

# 25. Frozen 22 monitored inputs

Use the exact frozen packets:

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

Frozen packet SHAs:

```text
US =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

No provider refetch.

No packet semantic mutation.

---

# 26. New full proof generation mandatory

Because FUNDAMENTAL_CORE model-facing schema changes:

create a NEW full generation.

Do NOT reuse:

```text
M12BX core outputs

M12BW/M12BV/M12BU outputs.
```

Run the complete architecture from call 1.

No stitching.

---

# 27. Full call-plan freeze

Derive exact plan from the current harness.

Recent expected:

```text
16 calls.
```

Before call 1 freeze:

```text
ordinal

market

stage

batch

expected tickers

expected subject count

prompt hash

schema hash

ticker-domain hash

identity-contract hash

ref-catalog hash

typed-contract hash.
```

Dynamic Stage-2 prompts remain generated from the new valid cores
under existing architecture.

---

# 28. Model configuration

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No repair.

No selective rerun.

No per-ticker retry.

---

# 29. Formal no-repair proof policy

If a new hard:

```text
runtime

schema

batch completeness

identity

exact ref

typed string

semantic

ownership

core mutation
```

failure occurs:

record it.

Do not patch/rerun in M12BY.

---

# 30. Full22 PASS criteria

Require:

```text
22 / 22 subjects represented

all required calls complete

FUNDAMENTAL_CORE expected batch cardinality PASS for every batch

FUNDAMENTAL_CORE ticker exact-set PASS for every batch

FUNDAMENTAL_CORE duplicate ticker count = 0

FUNDAMENTAL_CORE missing ticker count = 0

FUNDAMENTAL_CORE extra ticker count = 0

FUNDAMENTAL_CORE top-level identity mismatch = 0

FUNDAMENTAL_CORE schema valid = 22

FUNDAMENTAL_CORE semantic valid = 22

FUNDAMENTAL_CORE exact-ref violations = 0

Stage-2 schema valid = 22

Stage-2 semantic valid = 22

Stage-2 typed contract violations = 0

Stage-2 exact-ref violations = 0

fabricated refs = 0

noncanonical dates = 0

symbolic date fabrication = 0

frozen-core revalidation false positives = 0

post-confirmation maturity conflicts = 0

final compositions = 22

BusinessDelta failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchors = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

fallback/judge/repair/selective rerun = 0.
```

No target direction distribution.

---

# 31. Required regression dossiers

## IBM

Report:

```text
expected batch membership

returned batch membership

core generated?

schema valid?

semantic valid?
```

Require:

```text
IBM present exactly once.
```

No target direction.

## GOOGL

Require:

```text
price/timing core anchor = 0

expectation/valuation duplicate anchor = 0.
```

No target direction.

## SKHY

Require:

```text
all driver_maturity.as_of values concrete/canonical

noncanonical dates = 0.
```

## RXRX / CORZ

Require:

```text
fabricated refs = 0

CORZ maturity conflict = 0.
```

---

# 32. Three-axis local render

After clean full proof:

```text
overall direction visible = 22

new-buyer visible = 22

holder visible = 22

REVIEW copy safe

mechanical mapping = 0.
```

No deployment in M12BY.

---

# 33. TRACK B — Kiwoom local restoration is frozen successful

Do NOT redo historical search.

Freeze:

```text
historical commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

reuse decision =
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

adapter =
krx-night-leading-market-adapter-v1

9/1 replay =
PASS

9/2 replay =
PASS

9/3 replay =
PASS

KOSPI200 night message render =
PASS_LOCAL

KOSDAQ150 historical support =
UNAVAILABLE_NOT_YET_PROVEN.
```

Do not claim KOSDAQ150.

---

# 34. Kiwoom reference-basis safety — freeze

Historical samples own:

```text
OHLCV / contract / business date / NIGHT session.
```

They do NOT inherently own a safe change basis.

M12BX correctly suppressed change_pct in all 3 historical adapter replays
when basis was unavailable:

```text
suppressed_without_basis_count = 3.
```

Preserve this.

No fabricated percentage.

---

# 35. Kiwoom live read-only gateway audit

Current M12BX environment:

```text
host = macOS

authenticated Windows Kiwoom gateway =
false

read calls =
0

order calls =
0.
```

M12BY should check whether a configured gateway is now available
through the existing documented integration contract.

Do not search for or print credentials.

Report only:

```text
gateway configured? yes/no

endpoint/transport type without secret query values

capability endpoint reachable? yes/no

read-only quote capability available? yes/no

order capability invoked? MUST be no.
```

---

# 36. Kiwoom read-only authorization scope

If a configured authenticated gateway exists,
M12BY is authorized to perform:

```text
ONE capability/read-only quote smoke
```

for KOSPI200 night futures.

It is NOT authorized to:

```text
place order

modify order

cancel order

read/modify portfolio for the smoke

perform account trading action.
```

Required:

```text
order call count = 0.
```

If gateway absent:

report:

```text
LIVE_KIWOOM_NIGHT_GATEWAY_UNAVAILABLE
```

without weakening code.

---

# 37. TRACK C — Treasury restoration is frozen successful

Historical final implementation:

```text
commit =
4407cd11a78579e11681b503b2d4e72ee3c3d60f

timestamp =
2026-09-02T19:23:58+09:00

provider =
FRED.
```

Historical nominal series:

```text
DGS3

DGS5

DGS10

DGS30.
```

This confirms the user's recalled:

```text
5Y / 10Y / 30Y
```

and also shows:

```text
3Y was historically included too.
```

Direct companion series:

```text
DFII10 = 10Y real yield

T10YIE = 10Y breakeven inflation.
```

Do NOT synthesize real yield.

---

# 38. Treasury local adapter — freeze

Current local restoration files:

```text
app/macro/providers/fred.py

app/services/market_intelligence_service.py

app/services/us_full_message_service.py.
```

Source contract:

```text
frequency =
daily

intraday claim allowed =
false

previous basis =
previous valid same-series observation

missing interpolation =
false.
```

Preserve.

---

# 39. Treasury bp-change contract — freeze

Formula:

```text
change_bp =
(current_pct - previous_valid_same_series_pct) * 100.
```

Current test:

```text
PASS

double-multiply count =
0.
```

Do not alter units.

---

# 40. Treasury message contract — freeze

Local message already renders:

```text
미국채 3Y

미국채 5Y

미국채 10Y

미국채 30Y

10Y 실질금리

10Y 기대인플레이션
```

with individual observation dates and bp changes.

Required:

```text
latest available daily observation
```

not:

```text
live intraday.
```

Different series may have different observation dates.

Do not synthesize one shared timestamp.

---

# 41. Market-context time layers — freeze

Current local contract order:

```text
1. COMPLETED_SESSION
2. DAILY_RATES_AND_INFLATION
3. CURRENT_LEADING_OR_NIGHT
4. INTERPRETATION
5. NEXT_CHECK.
```

Required:

```text
common timestamp synthesis = false.
```

Do not mix Treasury daily dates with live/night futures time.

---

# 42. Local market-context regressions

M12BY must rerun:

```text
Kiwoom 9/1 adapter replay

Kiwoom 9/2 adapter replay

Kiwoom 9/3 adapter replay

KOSPI200 night render

Treasury direct-series parser

Treasury 3Y/5Y/10Y/30Y render

DFII10/T10YIE render

bp-change unit tests

Treasury as-of/freshness tests

completed-session vs rates vs leading-market layering tests

market timing → BusinessDelta negative tests

market timing → holder fundamental negative tests.
```

No model calls required for these tests.

---

# 43. Market-context readiness decision

Choose independently:

```text
LOCAL_MARKET_CONTEXT_READY_LIVE_KIWOOM_READY

LOCAL_MARKET_CONTEXT_READY_LIVE_KIWOOM_UNAVAILABLE

MARKET_CONTEXT_REGRESSION.
```

Treasury local readiness should remain PASS unless a real regression is found.

---

# 44. No deployment in M12BY

Even if Track A and market context are clean:

```text
deployments = 0

main merge = 0.
```

If Track A full proof PASS and live Kiwoom is available:

next scope may be:

```text
FINAL_DEPLOY_CURRENT_US_KR_MARKET_AND_TICKER_MESSAGE_SMOKE_WITH_NIGHT_FUTURES_AND_TREASURY_CURVE.
```

If Track A PASS but live Kiwoom unavailable:

next scope:

```text
KIWOOM_READONLY_GATEWAY_ENABLEMENT_AND_FINAL_MESSAGE_SMOKE.
```

Do not falsely claim live night-futures readiness.

---

# 45. Production firewall

Throughout M12BY:

```text
production DB mutations = 0

assessment production writes = 0

warning production mutations = 0

notification queue writes = 0

production sends = 0

monitoring registrations = 0

monitoring stops = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

remote raw-model push = 0.
```

External model calls for the frozen full22 proof are authorized.

Read-only Kiwoom market quote is conditionally authorized only if the configured gateway exists.

---

# 46. Required Track-A forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12by-scope-freeze

04-m12bx-failure-freeze

05-fundamental-core-batch2-omission-forensic

06-fundamental-core-complete-identity-field-inventory

07-fundamental-core-cardinality-schema-capability

08-fundamental-core-identity-domain-matrix

09-fundamental-core-batch-completeness-decision.
```

---

# 47. Required Track-A implementation/tests

Produce:

```text
10-dynamic-core-cardinality-schema-implementation

11-batch-ticker-enum-schema-implementation

12-top-level-core-identity-closure-implementation

13-fundamental-core-completeness-prompt-clarification

14-cardinality-positive-fixtures

15-cardinality-negative-fixtures

16-ticker-set-duplicate-negative-fixtures

17-top-level-identity-negative-fixtures

18-old-batch2-output-offline-replay

19-exact-ref-regressions

20-stage2-typed-contract-regressions

21-frozen-core-postconfirmation-regressions

22-three-axis-core-timing-expectation-regressions

23-business-delta-regressions

24-full-local-test-result

25-ruff-diff-result

26-model-facing-hash-manifest.
```

---

# 48. Required full22 proof artifacts

Produce:

```text
27-frozen22-input-identity-manifest

28-new-full22-generation-manifest

29-full22-call-plan-with-batch-identity-hashes

30-fundamental-core-model-artifacts

31-stage2-model-artifacts

32-fundamental-core-batch-completeness-audit

33-fundamental-core-identity-audit

34-fundamental-core-exact-ref-audit

35-stage2-typed-contract-audit

36-stage2-exact-ref-audit

37-frozen-core-ownership-audit

38-postconfirmation-maturity-audit

39-price-timing-immutability-audit

40-expectation-valuation-audit

41-business-delta-audit

42-canonical-semantic-audit

43-final-composition-audit

44-per-ticker-result-matrix

45-ibm-dossier

46-skhy-dossier

47-googl-dossier

48-rxrx-corz-regression-dossier

49-three-axis-render-audit

50-track-a-decision.
```

---

# 49. Required Market-context artifacts

Produce:

```text
51-kiwoom-restoration-freeze

52-kiwoom-historical-replay-regression

53-kiwoom-reference-basis-safety-regression

54-kiwoom-live-gateway-config-status

55-kiwoom-readonly-capability-smoke-if-available

56-kiwoom-zero-order-call-proof

57-treasury-restoration-freeze

58-treasury-series-scope-regression

59-treasury-parser-regression

60-treasury-bp-change-regression

61-treasury-asof-freshness-regression

62-us-market-rate-block-local-preview

63-kr-night-market-block-local-preview

64-market-time-layer-regression

65-market-context-fundamental-ownership-negative-tests

66-market-context-readiness-decision.
```

---

# 50. Required final decisions

Produce:

```text
67-fundamental-core-batch-contract-decision

68-full22-reproof-decision

69-message-model-contract-readiness

70-market-context-readiness

71-deployment-readiness

72-next-scope-decision

73-master-workflow-update

74-program-completion.
```

---

# 51. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bx_failure_stage
m12bx_failure_batch
m12bx_expected_tickers
m12bx_returned_tickers
m12bx_missing_tickers
m12bx_extra_tickers

fundamental_core_batch_contract_version

fundamental_core_identity_field_count
fundamental_core_identity_free_string_gap_count_before
fundamental_core_identity_free_string_gap_count_after

dynamic_cardinality_schema_supported
ticker_enum_schema_supported

old_batch2_replay_status

fundamental_core_prompt_change_count
fundamental_core_schema_change_count
fundamental_core_semantic_policy_change_count

stage2_prompt_change_count
stage2_schema_change_count
stage2_typed_contract_change_count
exact_ref_contract_change_count
canonical_semantic_classifier_change_count
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

fundamental_core_batch_count
fundamental_core_cardinality_failure_count
fundamental_core_ticker_set_failure_count
fundamental_core_duplicate_ticker_count
fundamental_core_missing_ticker_count
fundamental_core_extra_ticker_count
fundamental_core_identity_mismatch_count

fundamental_core_schema_valid_count
fundamental_core_semantic_valid_count
fundamental_core_exact_ref_violation_count

stage2_schema_valid_count
stage2_semantic_valid_count
stage2_typed_contract_violation_count
stage2_noncanonical_date_count
stage2_symbolic_date_fabrication_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count

frozen_core_revalidation_false_positive_count
postconfirmation_maturity_conflict_count
final_composition_valid_count
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

ibm_core_present_count

skhy_noncanonical_date_count

googl_overall_direction
googl_new_buyer
googl_holder
googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class

rxrx_fabricated_ref_count
corz_fabricated_ref_count
corz_postconfirmation_maturity_conflict_count

track_a_result

kiwoom_historical_commit
kiwoom_adapter_status
kiwoom_historical_replay_status
kiwoom_change_pct_suppressed_without_basis_count
kiwoom_live_gateway_status
kiwoom_live_readonly_call_count
kiwoom_live_order_call_count

treasury_historical_commit
treasury_provider
treasury_nominal_series
treasury_real_series
treasury_breakeven_series
treasury_parser_status
treasury_bp_change_status
treasury_asof_status
treasury_render_status

market_context_time_layer_status
market_context_fundamental_violation_count
market_context_readiness

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

message_model_contract_readiness
deployment_readiness

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

LIVE_GATEWAY_UNAVAILABLE
```

where appropriate.

Never replace unknown with zero.

---

# 52. Expected clean Track-A result

If batch/identity closure works:

```text
track_a_result =
FUNDAMENTAL_CORE_BATCH_COMPLETENESS_FULL22_PASS

fundamental_core_cardinality_failure_count = 0

fundamental_core_ticker_set_failure_count = 0

fundamental_core_duplicate_ticker_count = 0

fundamental_core_missing_ticker_count = 0

fundamental_core_extra_ticker_count = 0

fundamental_core_identity_mismatch_count = 0

fundamental_core_schema_valid_count = 22

fundamental_core_semantic_valid_count = 22

fundamental_core_exact_ref_violation_count = 0

stage2_schema_valid_count = 22

stage2_semantic_valid_count = 22

stage2_typed_contract_violation_count = 0

stage2_noncanonical_date_count = 0

stage2_symbolic_date_fabrication_count = 0

stage2_exact_ref_violation_count = 0

stage2_fabricated_ref_count = 0

frozen_core_revalidation_false_positive_count = 0

postconfirmation_maturity_conflict_count = 0

final_composition_valid_count = 22

business_delta_hard_failure_count = 0

price_timing_core_mutation_count = 0

price_timing_holder_mutation_count = 0

expectation_valuation_duplicate_anchor_count = 0

core_mutation_count = 0

three_axis_visible_count = 22.
```

No forced investment directions.

---

# 53. Expected market-context result

Treasury expected:

```text
provider =
FRED

nominal series =
[DGS3, DGS5, DGS10, DGS30]

real yield =
DFII10

breakeven =
T10YIE

frequency =
daily

intraday claim =
false

parser =
PASS

bp-change =
PASS

render =
PASS.
```

Kiwoom offline expected:

```text
historical 9/1–9/3 =
PASS

adapter =
PASS

KOSPI200 message =
PASS

KOSDAQ150 =
UNAVAILABLE_NOT_YET_PROVEN.
```

Kiwoom live:

```text
PASS_READ_ONLY
```

only if the authenticated gateway actually exists.

Otherwise:

```text
LIVE_KIWOOM_NIGHT_GATEWAY_UNAVAILABLE.
```

Do not fake a live PASS.

---

# 54. Top-level result taxonomy

Choose exactly one:

```text
M12BY_MODEL_AND_MARKET_CONTEXT_READY_FOR_FINAL_SMOKE

M12BY_MODEL_READY_KIWOOM_LIVE_GATEWAY_PENDING

M12BY_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY

M12BY_MULTIPLE_BLOCKERS.
```

---

# 55. Next-scope rules

## Track A PASS + Kiwoom live read-only PASS + Treasury PASS

```text
next_scope =
FINAL_DEPLOY_CURRENT_US_KR_MARKET_AND_TICKER_MESSAGE_SMOKE_WITH_NIGHT_FUTURES_AND_TREASURY_CURVE.
```

## Track A PASS + Kiwoom live unavailable + Treasury PASS

```text
next_scope =
KIWOOM_READONLY_GATEWAY_ENABLEMENT_AND_FINAL_MESSAGE_SMOKE.
```

## Track A FAIL

No model hotfix inside M12BY.

Market-context restoration remains frozen successful.

Choose the smallest bounded batch/model-contract follow-up.

---

# 56. Production firewall

M12BY is non-deploying.

Required:

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

V2 production gates = OFF

main merges = 0

deployments = 0

raw model artifact remote pushes = 0.
```

Kiwoom read-only quote smoke is allowed ONLY if a configured authenticated gateway exists.

Order calls:

```text
0.
```

---

# 57. Final task principle

M12BX achieved the broad Stage-2 typed-string closure the user requested.

The new proof did not fail on another Stage-2 free string.

It failed earlier because FUNDAMENTAL_CORE itself still had a structural batch gap:

```text
3 tickers requested

2 cores emitted

schema accepted the shorter array

hard preflight correctly rejected missing IBM.
```

Do NOT patch IBM.

Close the whole FUNDAMENTAL_CORE batch/identity class:

```text
dynamic exact cardinality

→ closed ticker domain

→ deterministic top-level identity values

→ preserve exact-set/duplicate hard validation

→ run a new full 22-subject proof.
```

At the same time, preserve the market-context work that is now actually recovered:

```text
Kiwoom KOSPI200 night futures
  9/1–9/3 historical parser + local LeadingMarket adapter = PASS

US Treasury historical curve
  DGS3 / DGS5 / DGS10 / DGS30 = confirmed

10Y real yield
  DFII10 = confirmed

10Y breakeven
  T10YIE = confirmed

FRED daily semantics + per-series as-of + bp changes = PASS.
```

Do NOT:

```text
special-case IBM

accept partial batches

retry IBM alone

weaken preflight exact-set validation

reopen Stage-2 typed contracts

rebuild Kiwoom history

drop Treasury 3Y simply because the user primarily remembered 5Y/10Y/30Y

call FRED daily data intraday live

fabricate night-futures change_pct

place Kiwoom orders

merge/deploy

resume automation.
```
