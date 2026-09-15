# Thesis Monitor — Stage-2 Exact Evidence-Ref Fidelity + Full 22 Reproof + Mandatory Historical Kiwoom Night-Futures Recovery

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-stage2-exact-ref-fidelity-full22-reproof-mandatory-historical-kiwoom-recovery.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-stage2-exact-ref-fidelity-full22-reproof-mandatory-historical-kiwoom-recovery-report.zip
```

Master-workflow phase:

```text
M12BV — Two Independent Tracks

TRACK A — Stage-2 exact evidence-ref fidelity
  A1. Freeze the successful FUNDAMENTAL_CORE exact-ref repair from M12BU
  A2. Freeze the existing hard ownership validator
  A3. Apply exact-ref catalog restriction to every Stage-2 evidence-ref output path
  A4. Add prompt fidelity rule and deterministic fixtures
  A5. Run full deterministic regression
  A6. Create a NEW full US14 + KR8 proof generation
  A7. Run the complete 22-subject architecture from call 1
  A8. No fallback / judge / repair / selective rerun

TRACK B — Historical Kiwoom night-futures recovery
  B1. Run regardless of whether TRACK A model reproof passes or fails
      once deterministic local tests are green
  B2. Search Git history / branches / reflogs / local artifact references for
      the 2026-09-01 / 09-02 / 09-03 Kiwoom night-futures implementation
  B3. Recover the exact historical code, samples, parser, tests, and source contract
  B4. Reproduce the parser against the preserved actual extracted data
  B5. Determine why that implementation disappeared from the current market pipeline
  B6. Map the recovered implementation into the current LeadingMarketSnapshot contract
  B7. Do NOT write a new futures connector in M12BV
  B8. Do NOT deploy in M12BV
```

Important workflow correction:

```text
The historical Kiwoom recovery audit must NOT be blocked behind
the full 22-subject model proof result.
```

M12BU blocked that audit because Phase A failed.
Do not repeat that coupling.

The Kiwoom recovery audit is read-only/local and independent of the model proof.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260915-exact-evidence-ref-fidelity-full22-reproof-historical-kiwoom-nightfutures-recovery-audit-report.zip
```

Verified SHA-256:

```text
07d8fef5660238975e97283cc3ba50b333dd01d0d9c9bb210061ffd96f31bfeb
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
artifact_count = 69

missing = 0

hash mismatch = 0

size mismatch = 0

extra indexed payload = 0

artifact secret scan failure = 0.
```

Recompute before work.

---

# 2. M12BU repository/result baseline

M12BU:

```text
implementation branch =
codex/20260915-m12bu-exact-ref-fidelity-night-futures-audit

implementation head =
7108012c12d84fb9195c8013f2e8103830c1a405

base main =
9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479.
```

Deterministic gate:

```text
focused =
92 passed

full local =
3986 passed, 63 skipped, 1 warning

Ruff =
PASS

git diff --check =
PASS.
```

Use the exact intended integration line containing M12BS/M12BT/M12BU work.

Do not silently drop those changes.

---

# 3. M12BU success that must be frozen

The FUNDAMENTAL_CORE exact-ref repair worked.

Contract:

```text
fundamental-core-exact-ref-fidelity-v1.
```

Result:

```text
US FUNDAMENTAL_CORE valid =
14 / 14

FUNDAMENTAL_CORE fabricated ref count =
0

FUNDAMENTAL_CORE exact-ref fidelity violation count =
0

RXRX fabricated ref count =
0

RXRX subject ownership =
PASS.
```

RXRX emitted the original correct ref:

```text
decision-evidence:774e2e7f46d2025d7257
```

and did NOT emit the old one-digit mutation.

Do NOT reopen FUNDAMENTAL_CORE ref fidelity unless needed only to share generic helper code.

---

# 4. M12BU new blocker — exact Stage-2 failure

First downstream hard failure:

```text
ticker =
CORZ

stage =
US PRICE_TIMING / Stage-2 batch 1

failure class =
FABRICATED_EVIDENCE_REF_ONE_CHARACTER_INSERTION.
```

Nearest valid supplied ref:

```text
decision-evidence:36090e913951b40587f1
```

Model-emitted invalid ref:

```text
decision-evidence:36090e913951b40587f1d
```

Difference:

```text
one trailing character:
"d".
```

Invalid ref paths:

```text
$.candidates[0].asymmetry.downside_permanence.evidence_refs

$.candidates[0].preconfirmation_error_cost.capital_loss_channel.evidence_refs.
```

The hard semantic validator correctly rejected this.

Do NOT:

```text
strip the final character

fuzzy-match nearest ref

edit CORZ candidate

weaken exact ownership

accept near-match identifiers.
```

---

# 5. Root-cause classification

Freeze:

```text
STAGE2_MODEL_OUTPUT_EXACT_EVIDENCE_REF_COPY_FIDELITY_GAP.
```

This is NOT:

```text
a CORZ semantic problem

post-confirmation maturity regression

BusinessDelta failure

provider error

core/timing ownership regression

transport problem.
```

M12BU fixed the exact same failure class structurally in FUNDAMENTAL_CORE.

Stage-2 did not yet inherit that structural protection.

---

# 6. General architecture requirement

Evidence refs are opaque identifiers.

At every model-output stage that emits evidence refs:

```text
the output must be constrained to the exact evidence refs
visible to that model call.
```

The architecture should have:

```text
one reusable exact-ref catalog/schema helper
```

rather than independent implementations for:

```text
FUNDAMENTAL_CORE

PRICE_TIMING / Stage-2.
```

However:

Do NOT refactor broadly if a thin reusable extraction/helper is sufficient.

Preserve existing output shapes.

---

# 7. Stage-2 evidence-ref field inventory

Audit the full Stage-2 / PRICE_TIMING output schema.

Enumerate EVERY path that can emit an evidence ref.

At minimum inspect structures equivalent to:

```text
asymmetry

downside_permanence

preconfirmation_error_cost

capital_loss_channel

confirmation evidence

maturity evidence

new-buyer timing evidence

holder-related Stage-2 evidence if any

price/timing support refs

any nested evidence_refs arrays.
```

Do not patch only the two CORZ paths.

Produce a machine-readable field inventory.

---

# 8. Stage-2 exact ref catalog source

The Stage-2 allowed-ref catalog must be built from the SAME evidence set
actually visible in that Stage-2 model call.

Possible inputs may include:

```text
frozen accepted core evidence refs

frozen source/decision evidence visible to Stage-2

canonical refs explicitly included in Stage-2 context

price/timing refs explicitly included in the prompt.
```

Do NOT include:

```text
refs not visible in Stage-2 prompt

refs from another batch

refs from another ticker unless batch-union schema intentionally allows them

historical refs not present in the frozen context.
```

Freeze a:

```text
stage2_ref_catalog_hash
```

for every Stage-2 model call.

---

# 9. Preferred Stage-2 schema enforcement

Reuse the proven M12BU mechanism:

```text
string enum

array-items enum

batch-union exact-ref catalog
```

for all Stage-2 evidence-ref fields.

A one-character insertion must become:

```text
SCHEMA_INVALID
```

before semantic ownership validation.

Existing semantic ownership remains authoritative for:

```text
cross-subject ref misuse

wrong field role

wrong evidence domain

wrong lifecycle ownership.
```

---

# 10. Batch-union vs per-subject enum

M12BU selected:

```text
batch_union = true
```

for FUNDAMENTAL_CORE.

Default for M12BV:

```text
reuse batch-union exact ref enum in Stage-2
+
existing subject ownership validator.
```

Do not introduce per-subject branching unless:

```text
the current structured-output subset demonstrably supports it
and it materially reduces risk without large schema growth.
```

No unsupported conditionals.

---

# 11. Null / no-evidence behavior

Preserve the current Stage-2 contract for legitimate no-evidence cases.

If the existing schema allows:

```text
null

empty evidence_refs
```

under specific fields:

do not accidentally require a ref.

Rule:

```text
if a ref is emitted,
it must be exact and catalog-owned.
```

No fabricated ref is preferable to an unsupported claim.

---

# 12. Stage-2 prompt fidelity rule

Add one concise rule equivalent to:

```text
Evidence refs are exact identifiers.
Copy only refs present in the supplied Stage-2 evidence catalog.
Never edit, append, shorten, infer, or synthesize an evidence ref.
If no exact supplied ref supports the statement, do not cite one.
```

Avoid verbose ref instructions that crowd out decision reasoning.

---

# 13. One shared helper — bounded convergence

Where practical extract a generic helper such as:

```text
build_exact_ref_enum_schema(...)

collect_model_visible_ref_catalog(...)

hash_ref_catalog(...)
```

or repository-equivalent.

Both:

```text
FUNDAMENTAL_CORE

Stage-2
```

should consume it.

Do NOT change semantic ownership.

Goal:

```text
one fidelity mechanism,
two stage-specific visible catalogs.
```

---

# 14. CORZ exact negative fixture

Exact valid:

```text
decision-evidence:36090e913951b40587f1
```

Exact invalid:

```text
decision-evidence:36090e913951b40587f1d
```

Expected:

```text
invalid ref → Stage-2 schema FAIL.
```

No post-hoc correction.

---

# 15. Stage-2 fidelity fixtures

Add at minimum:

## S2-ERF-P01

Exact valid Stage-2 ref in allowed field:

```text
PASS.
```

## S2-ERF-P02

Multiple exact refs from current batch catalog:

```text
PASS.
```

## S2-ERF-N01

One trailing character:

```text
FAIL schema.
```

## S2-ERF-N02

One character deleted:

```text
FAIL schema.
```

## S2-ERF-N03

One character substituted:

```text
FAIL schema.
```

## S2-ERF-N04

Syntactically plausible fabricated ref:

```text
FAIL schema.
```

## S2-ERF-N05

Exact ref valid in batch but owned by another subject:

```text
schema may PASS under batch union

semantic subject ownership MUST FAIL.
```

---

# 16. Exact historical CORZ output replay

Replay the exact M12BU CORZ Stage-2 output offline.

Expected:

```text
still INVALID.
```

Required:

```text
candidate_modified = false

fuzzy_match_count = 0

candidate_auto_repair_count = 0.
```

Do not “prove” the repair by changing old output.

---

# 17. Preserve post-confirmation maturity contract

M12BT repair remains frozen:

```text
post_confirmation_hold = true
⇒
overall_maturity = CONFIRMED.
```

M12BU CORZ result:

```text
overall_direction =
HOLD

overall_maturity =
MIXED

post_confirmation_hold =
false

maturity conflict =
false.
```

This demonstrates the previous repair worked.

Do not reopen it.

---

# 18. Model-facing change scope

Expected:

```text
Stage-2 prompt semantic hash =
changed

Stage-2 schema semantic hash =
changed

FUNDAMENTAL_CORE prompt/schema =
unchanged from M12BU

canonical semantic validators =
unchanged

three-axis contract =
unchanged

core/timing ownership =
unchanged

expectation/valuation ownership =
unchanged

Persistence V2 =
unchanged

KR-financial cold-start =
unchanged.
```

Report all hashes.

---

# 19. Schema-size safety

For every Stage-2 batch record:

```text
allowed ref count

schema size bytes

prompt size bytes

ref catalog hash.
```

If Stage-2 exact enum exceeds a proven schema/runtime limit:

```text
STOP BEFORE MODEL
STAGE2_EXACT_REF_ENUM_SCHEMA_SIZE_LIMIT.
```

Do NOT silently revert Stage-2 refs to arbitrary strings.

If a short-alias contract becomes necessary:

make it a later bounded task.

---

# 20. Full deterministic pre-model gate

Before external model calls run:

```text
shared exact-ref helper tests

FUNDAMENTAL_CORE exact-ref regressions

Stage-2 exact-ref tests

CORZ invalid-output replay

M12BT maturity tests

three-axis tests

core/timing tests

expectation/valuation tests

BusinessDelta tests

holder/new-buyer tests

full local pytest

Ruff

git diff --check.
```

Required:

```text
PASS.
```

---

# 21. Frozen monitored cohort

Reuse exact frozen 22-subject packets:

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

# 22. New complete proof generation

Because Stage-2 model-facing prompt/schema changes:

create a NEW full proof generation.

Do NOT reuse:

```text
M12BU FUNDAMENTAL_CORE outputs

M12BU Stage-2 output

M12BT outputs

M12BS outputs.
```

Run the complete current architecture from call 1.

No stitching.

---

# 23. Full 22 proof call plan

Derive the complete plan from the current harness.

Expected recent topology:

```text
16 planned calls.
```

Freeze before first call:

```text
ordinal

market

stage

batch

tickers

prompt hash

schema hash

visible-ref catalog hash.
```

Stage-2 catalog is frozen after its corresponding new core output exists,
according to the existing architecture.

---

# 24. Model configuration

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No repair calls.

No selective rerun.

No per-ticker retry.

---

# 25. Reproof stop policy

Preserve current formal no-repair proof policy.

If a hard:

```text
runtime

schema

exact-ref fidelity

semantic

ownership

core mutation
```

failure occurs:

record it.

Do NOT patch/rerun in the same proof.

No fuzzy ref acceptance.

---

# 26. Full 22 PASS criteria

Require:

```text
subjects = 22

FUNDAMENTAL_CORE schema valid = 22

FUNDAMENTAL_CORE exact-ref violations = 0

FUNDAMENTAL_CORE semantic valid = 22

Stage-2 schema valid = 22

Stage-2 exact-ref violations = 0

Stage-2 fabricated refs = 0

Stage-2 semantic valid = 22

post-confirmation maturity conflicts = 0

final compositions valid = 22

BusinessDelta hard failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchor = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

fallback / judge / repair / selective rerun = 0.
```

No expected BUY/HOLD/SELL distribution.

---

# 27. RXRX regression

Require:

```text
FUNDAMENTAL_CORE fabricated refs = 0

all emitted refs exact catalog members

subject ownership = PASS.
```

No expected direction.

---

# 28. CORZ regression

Require:

```text
Stage-2 fabricated refs = 0

all emitted Stage-2 refs exact catalog members

subject ownership = PASS

post_confirmation_hold=true
only if maturity=CONFIRMED.
```

No expected direction.

---

# 29. GOOGL regression

Report:

```text
overall direction

new-buyer stance

holder stance

market expectation

valuation

price/timing core-anchor count

expectation/valuation overlap class.
```

Require:

```text
price/timing core-anchor count = 0

duplicate expectation/valuation anchor count = 0.
```

No expected direction.

---

# 30. Three-axis local render after proof

If full 22 proof is clean,
render all 22 locally.

Require:

```text
종합 방향 visible = 22

신규 관찰자 visible = 22

보유자 visible = 22

REVIEW copy safe

mechanical stance mapping = 0.
```

No deployment in M12BV.

---

# 31. TRACK A result taxonomy

Choose exactly one:

```text
STAGE2_EXACT_REF_FIDELITY_AND_FULL22_REPROOF_PASS

FULL22_REPROOF_NEW_HARD_FAILURE

MODEL_TRANSPORT_INCOMPLETE

PREMODEL_TEST_GATE_FAILURE

STAGE2_EXACT_REF_ENUM_SCHEMA_SIZE_LIMIT.
```

TRACK B still runs after deterministic local gate,
even if TRACK A model proof later fails.

---

# 32. TRACK B trigger

Run historical Kiwoom recovery when:

```text
local deterministic tests are green
```

regardless of:

```text
full 22 model proof PASS or FAIL.
```

Do not gate historical recovery on model output.

Only skip historical recovery for:

```text
repository integrity failure

secret/security incident

deterministic local test failure that makes repository inspection unsafe.
```

---

# 33. Historical Kiwoom task statement

The user recalls a dedicated implementation built from ACTUAL Kiwoom
night-futures extracted data on:

```text
2026-09-01

2026-09-02

2026-09-03.
```

The implementation must be searched/recovered before writing any new night-futures connector.

This is mandatory.

---

# 34. Historical search range

Search all local history/refs with emphasis on:

```text
2026-08-30 through 2026-09-07.
```

Use read-only:

```text
git log --all

git branch --all

git tag

git show

git grep <commit>

git reflog

git fsck --no-reflogs --unreachable
```

only where safe.

Do NOT:

```text
git gc

rewrite refs

reset branches

checkout over current work

delete unreachable objects.
```

---

# 35. Search terms

Search commit messages, file names, code, tests, and fixtures for:

```text
night_futures

night futures

야간선물

야간 선물

Kiwoom

키움

OpenAPI

KOSPI200

KOSPI 200

KOSDAQ150

KOSDAQ 150

evening

night session

overnight

futures

선물.
```

Also search any actual TR/request IDs found during provenance discovery.

Do not stop after one match.

---

# 36. Search non-current branches and worktree history

Inventory:

```text
all local branches

remote-tracking refs

tags

reflog entries

available worktrees

stashes if any, read-only

unreachable commit objects

artifact/report manifests referencing night futures.
```

Do not mutate any of them.

---

# 37. Historical implementation identity

For each candidate implementation record:

```text
commit SHA

parent SHA

branch/ref if known

commit timestamp

file paths

service/parser modules

test files

fixture/sample files

source/auth path

instrument scope

message/market integration path.
```

Rank candidates chronologically/functionally.

Identify the final implementation that used the 9/1-9/3 actual data.

---

# 38. Recover 9/1 / 9/2 / 9/3 actual samples

Locate exact preserved data for each date.

Preferred:

```text
raw Kiwoom response

normalized JSON

CSV

structured capture

exact parser fixture derived from actual extraction.
```

Screenshots may be supporting evidence only.

Do NOT reconstruct numeric fixtures from screenshots
when structured historical data exists.

For each sample record:

```text
date

instrument

session

raw/normalized format

sample SHA-256

source code path / commit.
```

---

# 39. Historical instrument scope

Determine exactly whether historical code covered:

```text
KOSPI200 night/evening futures

KOSDAQ150 night/evening futures

US index futures via Kiwoom overseas futures

other derivatives.
```

Do not assume.

Report actual scope.

---

# 40. Historical parser reproduction

Run the recovered historical parser against the recovered structured samples
in an isolated local harness.

Do NOT call live Kiwoom.

For each sample compare:

```text
instrument identity

trading/session date

as-of timestamp

price

reference/settlement basis

change

change percent

session status
```

only where the historical contract owned those fields.

Classify:

```text
EXACT_PASS

NORMALIZATION_ONLY_PASS

FAIL.
```

Do not update historical expected values to make it pass.

---

# 41. Historical auth/runtime contract

Determine how live collection historically worked.

Record whether it required:

```text
Windows Kiwoom OpenAPI process

authenticated market-data session

gateway/service

specific TR/request IDs

market code

account context

order-capable session.
```

Do not expose secrets.

Distinguish:

```text
read-only market-data use

from

trading/order capability.
```

The future target is read-only market data.

---

# 42. Why it disappeared from current pipeline

Classify with evidence:

```text
MERGE_OMISSION

LATER_REFACTOR_REMOVAL

CODE_STILL_EXISTS_NOT_WIRED

LEGACY_PIPELINE_ISOLATION

AUTH_GATE_REMOVED

TEST_ONLY_PATH

SUPERSEDED

CLEAN_HISTORY_RELEASE_OMISSION

UNKNOWN.
```

Note:

the recent clean-history/integration work may have dropped historical code/artifacts.
Check that possibility explicitly.

---

# 43. Map to current LeadingMarketSnapshot

Current M12BS introduced/currently owns a leading-market concept.

For each recovered historical field classify:

```text
DIRECT_MAPPING

DETERMINISTIC_ADAPTER_REQUIRED

OBSOLETE

AMBIGUOUS_UNSAFE.
```

Map at least:

```text
instrument id

session

current price

reference basis

change

change percent

as-of

timezone

freshness.
```

Do not turn overnight futures into completed cash-session returns.

---

# 44. Fundamental ownership firewall

Recovered night-futures data may influence only:

```text
시장환경 점검

current risk appetite

next-session timing

new-buyer timing / positioning context.
```

It must NEVER create:

```text
BusinessDelta

holder REVIEW/REDUCE

fundamental invalidation

earnings change.
```

The reintegration plan must include explicit negative tests.

---

# 45. Historical reuse decision

Choose exactly one:

```text
HISTORICAL_IMPLEMENTATION_REUSABLE

HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

HISTORICAL_IMPLEMENTATION_FOUND_SOURCE_AUTH_OBSOLETE

HISTORICAL_IMPLEMENTATION_FOUND_BUT_PARSER_INVALID

HISTORICAL_IMPLEMENTATION_NOT_FOUND.
```

Do not conclude `NOT_FOUND` until all search surfaces were audited.

---

# 46. No new connector in M12BV

Forbidden:

```text
new Kiwoom collector

new CME scraper

new US futures API connector

ETF-as-futures substitution

new production auth gateway.
```

M12BV only recovers, reproduces, and maps historical work.

The next task implements/reintegrates based on recovered evidence.

---

# 47. US futures historical audit

As part of recovery,
determine whether the 9/1-9/3 work also contained:

```text
US index futures

overseas futures

CME-linked contracts via Kiwoom.
```

If yes:
recover it.

If no:
report:

```text
US_FUTURES_NOT_IN_HISTORICAL_KIWOOM_SCOPE.
```

Do not fabricate US coverage.

---

# 48. Combined next-scope logic

## Case A
TRACK A PASS
+
historical reusable

```text
next_scope =
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

## Case B
TRACK A PASS
+
historical code found but auth obsolete

```text
next_scope =
KIWOOM_NIGHT_FUTURES_READONLY_TRANSPORT_REPLACEMENT_USING_RECOVERED_PARSER_CONTRACT.
```

## Case C
TRACK A PASS
+
historical implementation not found after exhaustive audit

```text
next_scope =
ARCHIVED_WORKTREE_BACKUP_RECOVERY_OR_NEW_SOURCE_DECISION.
```

## Case D
TRACK A FAIL
+
historical audit succeeds

Report BOTH independently.

Next primary engineering scope addresses the reproof failure,
while the recovered Kiwoom plan remains frozen and must not be lost.

---

# 49. Production firewall

Throughout M12BV:

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

External model calls for the frozen 22 proof are allowed.

Git history audit is read-only/local.

---

# 50. Required TRACK-A forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bv-scope-freeze

04-m12bu-success-failure-freeze

05-stage2-corz-ref-forensic

06-stage2-evidence-ref-field-inventory

07-stage2-visible-ref-catalog-contract

08-shared-exact-ref-helper-decision

09-stage2-exact-ref-schema-decision

10-stage2-schema-size-safety.
```

---

# 51. Required TRACK-A implementation/test artifacts

Produce:

```text
11-shared-exact-ref-helper-implementation

12-stage2-ref-enum-schema-implementation

13-stage2-ref-fidelity-prompt-implementation

14-stage2-ref-positive-fixtures

15-stage2-ref-negative-fixtures

16-cross-subject-stage2-ownership-negative

17-old-corz-invalid-output-replay

18-fundamental-core-ref-regression

19-postconfirmation-regression

20-three-axis-core-timing-expectation-regressions

21-full-local-test-result

22-ruff-diff-result

23-model-facing-hash-manifest.
```

---

# 52. Required TRACK-A proof artifacts

Produce:

```text
24-frozen-22-input-identity-manifest

25-new-full-reproof-generation-manifest

26-full-reproof-call-plan-with-core-and-stage2-ref-hashes

27-fundamental-core-model-artifacts

28-stage2-model-artifacts

29-core-exact-ref-fidelity-audit

30-stage2-exact-ref-fidelity-audit

31-canonical-semantic-audit

32-postconfirmation-maturity-audit

33-price-timing-immutability-audit

34-expectation-valuation-audit

35-business-delta-audit

36-core-immutability-audit

37-final-composition-audit

38-per-ticker-result-matrix

39-rxrx-dossier

40-corz-dossier

41-googl-dossier

42-three-axis-render-audit

43-track-a-decision.
```

---

# 53. Required TRACK-B historical artifacts

Produce regardless of TRACK-A model outcome, after deterministic local gate:

```text
44-historical-search-surface-inventory

45-historical-git-log-results

46-historical-branch-tag-results

47-historical-reflog-results

48-historical-unreachable-object-results

49-historical-artifact-reference-results

50-historical-implementation-candidates

51-historical-final-implementation-identity

52-historical-20260901-sample-identity

53-historical-20260902-sample-identity

54-historical-20260903-sample-identity

55-historical-instrument-scope

56-historical-parser-contract

57-historical-parser-reproduction-20260901

58-historical-parser-reproduction-20260902

59-historical-parser-reproduction-20260903

60-historical-auth-runtime-contract

61-current-pipeline-disconnect-root-cause

62-current-leading-market-mapping

63-historical-reuse-decision

64-night-futures-reintegration-plan.
```

---

# 54. Required final decisions

Produce:

```text
65-stage2-exact-ref-repair-decision

66-full22-reproof-decision

67-message-model-contract-readiness

68-historical-kiwoom-recovery-decision

69-leading-futures-next-scope-decision

70-deployment-readiness

71-master-workflow-update

72-program-completion.
```

---

# 55. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bu_core_exact_ref_contract_version
m12bu_core_valid_count
m12bu_core_exact_ref_violation_count

m12bu_stage2_failure_ticker
m12bu_stage2_valid_ref
m12bu_stage2_invalid_ref
m12bu_stage2_failure_class

shared_exact_ref_helper_contract_version

fundamental_core_prompt_change_count
fundamental_core_schema_change_count
stage2_prompt_change_count
stage2_schema_change_count
canonical_semantic_service_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
persistence_v2_contract_change_count

stage2_ref_enum_supported
stage2_ref_catalog_count_total
stage2_max_ref_catalog_count_per_batch
stage2_max_schema_size_bytes
stage2_schema_size_limit_status

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
fundamental_core_valid_count
fundamental_core_exact_ref_violation_count
fundamental_core_fabricated_ref_count

stage2_schema_valid_count
stage2_valid_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count
stage2_cross_subject_ownership_failure_count

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

rxrx_fabricated_ref_count

corz_overall_direction
corz_overall_maturity
corz_post_confirmation_hold
corz_stage2_fabricated_ref_count

googl_overall_direction
googl_new_buyer
googl_holder
googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class

track_a_result

historical_kiwoom_audit_ran
historical_search_surface_count
historical_search_commit_count
historical_candidate_implementation_count
historical_final_implementation_commit
historical_final_implementation_paths

historical_20260901_sample_found
historical_20260902_sample_found
historical_20260903_sample_found

historical_kospi200_scope_found
historical_kosdaq150_scope_found
historical_us_futures_scope_found

historical_parser_reproduction_20260901
historical_parser_reproduction_20260902
historical_parser_reproduction_20260903

historical_disconnect_root_cause
historical_reuse_decision
historical_readonly_auth_requirement

kr_night_futures_source_status
us_futures_source_status

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

Use explicit:

```text
NOT_FOUND

NOT_APPLICABLE

NOT_MEASURED
```

where appropriate.

Do not convert unknown to zero.

---

# 56. Expected clean TRACK-A result

If Stage-2 structural exact-ref restriction works:

```text
track_a_result =
STAGE2_EXACT_REF_FIDELITY_AND_FULL22_REPROOF_PASS

fundamental_core_valid_count = 22

fundamental_core_exact_ref_violation_count = 0

fundamental_core_fabricated_ref_count = 0

stage2_valid_count = 22

stage2_exact_ref_violation_count = 0

stage2_fabricated_ref_count = 0

postconfirmation_maturity_conflict_count = 0

final_composition_valid_count = 22

canonical_semantic_failure_count = 0

business_delta_hard_failure_count = 0

price_timing_core_mutation_count = 0

price_timing_holder_mutation_count = 0

expectation_valuation_duplicate_anchor_count = 0

core_mutation_count = 0

three_axis_visible_count = 22.
```

Do NOT force directions.

---

# 57. Expected historical recovery result

Preferred but not forced:

```text
historical_kiwoom_audit_ran = true

historical_final_implementation_commit = identified

historical_20260901_sample_found = true

historical_20260902_sample_found = true

historical_20260903_sample_found = true

historical parser reproductions = PASS

historical_reuse_decision =
HISTORICAL_IMPLEMENTATION_REUSABLE
or
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER.
```

If reality differs, report it.

---

# 58. Deployment readiness

M12BV never deploys.

If:

```text
TRACK A PASS
```

and:

```text
historical Kiwoom recovery is reusable
```

then:

```text
message_model_contract_readiness =
READY

deployment_readiness =
NOT_READY_PENDING_NIGHT_FUTURES_REINTEGRATION

next_scope =
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

If US futures are not part of recovered historical scope,
the next task must resolve them separately without discarding the KR recovered implementation.

---

# 59. Failure handling

## A. Stage-2 simple enum unsupported

```text
STOP MODEL TRACK
STAGE2_STRUCTURED_OUTPUT_EXACT_REF_ENUM_UNSUPPORTED.
```

Still run historical Kiwoom TRACK B.

## B. Stage-2 schema exceeds limit

```text
STOP MODEL TRACK
STAGE2_EXACT_REF_ENUM_SCHEMA_SIZE_LIMIT.
```

Still run TRACK B.

Next model scope may use short aliases.

## C. CORZ or another Stage-2 candidate fabricates a ref despite schema

```text
STAGE2_EXACT_REF_SCHEMA_ENFORCEMENT_FAILURE.
```

No fuzzy acceptance.

Still complete TRACK B.

## D. New unrelated hard semantic failure

Stop the model proof under current no-repair policy.

Run TRACK B independently.

## E. Historical implementation not found

Do not write a new connector in M12BV.

Produce exhaustive search evidence and the correct next scope.

## F. Both tracks succeed

Proceed next only to recovered-night-futures reintegration/final message smoke.

No deployment in M12BV.

---

# 60. Final task principle

M12BU proved the fundamental-core exact-ref fix works:

```text
RXRX one-digit evidence-ref mutation disappeared

US core passed 14/14.
```

The exact same fidelity class then appeared in Stage-2:

```text
CORZ added one trailing character to a supplied evidence ref.
```

The correct model-contract repair is therefore:

```text
share the exact-ref fidelity mechanism with Stage-2

→ constrain every Stage-2 evidence-ref path to the exact visible catalog

→ keep subject/field ownership hard validators

→ never fuzzy-correct

→ run a complete new 22-subject proof.
```

Separately, the user has confirmed a real early-September implementation already existed for
Kiwoom night-futures data using actual 9/1, 9/2, 9/3 extractions.

That recovery must no longer be held hostage by model reproof progress.

Therefore M12BV must ALSO:

```text
search all local Git history/branches/reflogs/artifact references

→ recover the exact code and samples

→ reproduce the old parser

→ determine why it disappeared from current code

→ map it into LeadingMarketSnapshot

→ freeze a reintegration plan

→ do not write a new connector yet.
```

Do NOT:

```text
special-case CORZ

weaken ref validation

rewrite candidate refs

reuse partial model generations

block the historical Kiwoom audit behind another model failure

invent a new night-futures provider before recovering the old implementation

merge/deploy

resume automation.
```
