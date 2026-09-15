# Thesis Monitor — Exact Evidence-Ref Fidelity Repair + Full 22 Reproof + Historical Kiwoom Night-Futures Recovery Audit

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-exact-evidence-ref-fidelity-full22-reproof-historical-kiwoom-nightfutures-recovery-audit.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-exact-evidence-ref-fidelity-full22-reproof-historical-kiwoom-nightfutures-recovery-audit-report.zip
```

Master-workflow phase:

```text
M12BU — Evidence-Ref Fidelity + Historical Night-Futures Recovery Audit
         Phase A
         A. Freeze all successful M12BS/M12BT message-contract changes
         B. Freeze the existing exact evidence-ownership validator
         C. Repair FUNDAMENTAL_CORE evidence-ref emission fidelity structurally
         D. Add exact-ref positive/negative fixtures
         E. Run full deterministic tests
         F. Run a NEW complete US14 + KR8 reproof from scratch
         G. No repair / judge / fallback / selective rerun inside the proof
         H. Require all 22 final compositions to pass

         Phase B — ONLY if Phase A is clean
         I. Search repository history/branches/reflogs for the historical
            2026-09-01 / 09-02 / 09-03 Kiwoom night-futures implementation
         J. Recover the exact code, fixtures, sample extracted data, parser, and tests
         K. Reproduce the historical extraction against the preserved sample data
         L. Determine why that implementation is absent from the current canonical path
         M. Freeze a reintegration plan into the current LeadingMarketSnapshot pipeline
         N. Do NOT write a new futures connector in M12BU
         O. Do NOT deploy in M12BU
```

This task has one model-contract repair and one READ-ONLY historical recovery audit.

It must NOT become another semantic-engine rewrite.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260915-postconfirmation-hold-maturity-contract-repair-full-22-reproof-report.zip
```

Verified SHA-256:

```text
047387e9ff884d67d6066ca7410d8de52009d05bcaf832a35489d6b1f1dc11d6
```

Recompute at task start.

Sidecar must match exactly.

Independent archive verification:

```text
artifact_count = 48

indexed artifact missing = 0

hash mismatch = 0

size mismatch = 0

extra indexed payload = 0.
```

Recompute independently.

---

# 2. M12BT authoritative outcome

M12BT status:

```text
BLOCKED
```

Top-level:

```text
FULL_REPROOF_NEW_HARD_FAILURE.
```

New reproof generation:

```text
20260915-uskr22-m12bt-20260915T111659Z-b7f967d806d8
```

Planned model calls:

```text
16
```

Started/completed with usable output:

```text
3 / 3
```

The reproof stopped in:

```text
US FUNDAMENTAL_CORE batch 3.
```

First hard failure:

```text
ticker =
RXRX

failure =
EXACT_EVIDENCE_REF_IDENTITY_VIOLATION

failure class =
FABRICATED_EVIDENCE_REF_ONE_DIGIT_SUBSTITUTION.
```

---

# 3. Exact RXRX failure — freeze

Supplied valid ref:

```text
decision-evidence:774e2e7f46d2025d7257
```

Model-emitted invalid ref:

```text
decision-evidence:774e2e7f46d2020d7257
```

Difference:

```text
one digit
5 → 0
```

The emitted ref was NOT present in the supplied candidate evidence catalog.

The current hard ownership validator correctly rejected it.

Do NOT:

```text
fuzzy-match the ref

edit the candidate

replace 0 with 5

accept near-match refs

weaken ownership validation.
```

The exact-ref validator is correct.

---

# 4. Root-cause classification

Freeze:

```text
MODEL_OUTPUT_EXACT_EVIDENCE_REF_COPY_FIDELITY_GAP
```

not:

```text
semantic ownership bug

RXRX-specific issue

provider issue

BusinessDelta issue

transport issue

CORZ maturity issue.
```

M12BT reports:

```text
schema valid output = true

semantic ownership = false.
```

This means the current JSON schema permits arbitrary evidence-ref strings
that are syntactically valid but not from the supplied catalog.

---

# 5. CORZ post-confirmation repair — freeze

M12BT local repair:

```text
postconfirmation-hold-maturity-v1
```

Invariant:

```text
post_confirmation_hold = true
⇒
overall_maturity = CONFIRMED.
```

Schema conditional support:

```text
unsupported by current structured-output subset.
```

Decision:

```text
explicit Stage-2 prompt rule
+
existing hard semantic validator.
```

Exact historical CORZ invalid output remains:

```text
INVALID.
```

Do not reopen this repair in M12BU.

---

# 6. Successful M12BS contracts — freeze

Preserve:

```text
three-axis user-facing decision UX

REVIEW safe copy

core vs price/timing separation

expectation/valuation overlap ownership

US as-of heading repair

CPNG phrase repair

047810 internal-label repair.
```

Do not change those contracts in Phase A.

---

# 7. Preferred exact-ref architecture

The model must only be able to emit evidence refs from the actual frozen evidence catalog.

Preferred bounded repair:

```text
dynamic schema enum restriction
for evidence-ref fields
using the exact valid refs supplied for the current batch.
```

The schema should reject a one-digit fabricated ref before semantic validation.

Hard semantic ownership validation remains authoritative for:

```text
cross-subject ref misuse

field-role misuse

noncore ref misuse

wrong evidence-domain ownership.
```

Schema fidelity and semantic ownership are complementary.

---

# 8. Batch-level exact-ref enum

If current structured-output schema generation can safely support it,
build:

```text
allowed_ref_enum =
union of all exact decision/evidence refs supplied to the current model batch.
```

Every model-output field that semantically stores an evidence ref
must use that enum or a derived exact enum.

A fabricated one-digit string must become:

```text
SCHEMA_INVALID
```

rather than a syntactically valid arbitrary string.

Cross-subject valid refs may still be caught by the existing ownership validator.

---

# 9. Per-subject exact-ref restriction — optional stronger form

If the current schema architecture can encode per-subject branches
without unsupported conditional constructs:

prefer:

```text
ticker-specific candidate schema branch
+
ticker-specific evidence-ref enum.
```

However:

Do NOT introduce unsupported:

```text
if / then / else
```

or other structured-output-incompatible keywords.

If per-subject branching is not safely supported:

```text
use batch-union enum
+
existing exact ownership validator.
```

That is acceptable.

---

# 10. Structured-output capability proof

Before modifying the schema,
deterministically prove current structured output supports:

```text
string enum

array items enum

any required oneOf/branch construct if used.
```

Do not assume capability.

If only simple enums are supported:

use simple enum.

Do not fake structural enforcement.

---

# 11. Evidence-ref field inventory

Audit the complete FUNDAMENTAL_CORE output schema.

List every field/path that can emit an evidence ref, including applicable:

```text
material anchor refs

buy-driver refs

sell-driver refs

risk refs

uncertainty refs

business-thesis context refs

earnings context refs

market-expectation refs

valuation refs

dominant-evidence refs

working-capital refs

other proof-critical refs.
```

Do not constrain only the field that happened to fail RXRX.

The repair must be generic.

---

# 12. No non-ref text restriction

Do NOT accidentally enum-constrain:

```text
free-text rationale

summary

claim text

labels

metric names
```

to evidence refs.

Only actual reference identity fields.

---

# 13. Prompt fidelity rule

Even with schema enums,
add one concise fundamental-core prompt rule:

```text
Evidence refs are identifiers.
Copy them exactly from the supplied evidence catalog.
Never synthesize, shorten, edit, guess, or repair an evidence ref.
If no valid ref supports a claim, do not cite one.
```

Do not overemphasize the rule so much that the model simply over-cites refs.

---

# 14. Missing support behavior

If the model cannot find a valid exact ref:

preferred behavior is:

```text
omit unsupported claim

or express the limitation/unknown
according to the existing candidate contract.
```

Forbidden:

```text
invent similar-looking ref

fuzzy nearest-match ref.
```

---

# 15. Hard validator remains unchanged

Do NOT change:

```text
noncore_ref_in_fundamental_core

evidence ownership

field ownership

subject ownership

semantic role validators.
```

Expected:

```text
canonical semantic service change count = 0.
```

Only model-facing ref fidelity changes.

---

# 16. Exact RXRX negative fixture

Use:

```text
valid:
decision-evidence:774e2e7f46d2025d7257

invalid:
decision-evidence:774e2e7f46d2020d7257.
```

Expected after repair:

```text
invalid string is rejected by model-output schema
or deterministic schema validation.
```

Do not auto-correct it.

---

# 17. Exact RXRX historical replay

The old M12BT RXRX candidate remains:

```text
INVALID.
```

Required:

```text
candidate rewrite = false

candidate repair = false

fuzzy match = false.
```

The old output is forensic evidence only.

---

# 18. Positive ref fixtures

Add at least:

## ERF-P01

Exact valid ref:

```text
decision-evidence:774e2e7f46d2025d7257
```

→ schema PASS where the field is allowed.

## ERF-P02

Multiple exact valid refs from the same batch

→ schema PASS.

## ERF-P03

Exact valid ref with subject ownership correct

→ semantic ownership PASS.

---

# 19. Negative ref fixtures

Add at least:

## ERF-N01

One-digit substitution

→ schema FAIL.

## ERF-N02

One-character deletion

→ schema FAIL.

## ERF-N03

One-character insertion

→ schema FAIL.

## ERF-N04

Completely fabricated but syntactically plausible ref

→ schema FAIL.

## ERF-N05

Exact valid ref belonging to another subject in the same batch

→ schema may PASS under batch-union enum
but MUST semantic ownership FAIL.

This proves schema fidelity does not replace semantic ownership.

---

# 20. Ref catalog integrity

The allowed enum must come from the SAME frozen input catalog supplied to the model.

Do NOT:

```text
re-read a different provider packet

derive refs from old artifacts

allow refs from other batches

include refs not visible to the model.
```

Freeze:

```text
ref_catalog_hash
```

per model call.

Prompt and schema must reference the same catalog identity.

---

# 21. Schema size safety

Measure:

```text
allowed ref count

schema byte size

prompt byte size.
```

If the enum causes an unacceptable schema/runtime limit:

STOP before model calls with:

```text
EVIDENCE_REF_ENUM_SCHEMA_SIZE_LIMIT.
```

Then propose a bounded alternative,
such as a stable short alias catalog.

Do not silently fall back to arbitrary strings.

---

# 22. Short alias fallback — only if necessary

Only if exact ref enum cannot safely fit supported schema limits,
consider:

```text
per-subject short model-facing aliases
E01, E02, ...
```

with deterministic post-schema identity resolution.

This is a broader model-facing contract change.

If required:

```text
STOP
EXACT_REF_ALIAS_CONTRACT_REQUIRED.
```

Do not implement the alias redesign inside M12BU.

Default expectation:

```text
exact enum is sufficient.
```

---

# 23. Model-facing hash impact

Expected changes:

```text
FUNDAMENTAL_CORE prompt semantic hash = changed

FUNDAMENTAL_CORE schema semantic hash = changed.
```

Preserve M12BT Stage-2 prompt repair.

Expected unchanged:

```text
Stage-2 schema

canonical semantic validators

three-axis renderer

core/timing contract

expectation/valuation classifier

BusinessDelta contract

Persistence V2

KR financial repair.
```

---

# 24. Full deterministic pre-model gate

Before any external model call:

run:

```text
exact-ref fidelity fixtures

schema-capability tests

existing core schema tests

M12BT post-confirmation tests

three-axis regressions

core/timing regressions

expectation/valuation regressions

BusinessDelta regressions

holder/new-buyer regressions

full local pytest

Ruff

git diff --check.
```

Require:

```text
PASS.
```

No reproof with red tests.

---

# 25. Frozen monitored cohort

Use exact M12BT frozen inputs.

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

Total:

```text
22.
```

Frozen packet SHA:

```text
US =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

No provider refetch.

No packet mutation.

---

# 26. New full proof generation mandatory

Because fundamental-core prompt/schema changes:

create a NEW proof generation.

Do NOT reuse:

```text
M12BT core outputs

M12BT partial outputs

M12BS Stage-2 outputs.
```

Run complete architecture from call 1.

No stitching across generations.

---

# 27. Full call plan

Derive the current complete call plan from the harness.

M12BT expected:

```text
16 calls total
```

across US/KR FUNDAMENTAL_CORE and PRICE_TIMING.

Freeze before call 1:

```text
call ordinal

market

stage

batch

tickers

prompt contract hash

schema hash

ref catalog hash.
```

Dynamic Stage-2 prompts may be frozen after valid new core output exists,
according to existing architecture.

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

No repair model.

No selective rerun.

No per-candidate retry.

---

# 29. Proof stop policy

Preserve existing no-repair proof policy.

If a hard model/runtime/schema/semantic failure occurs:

record it.

Do NOT patch and rerun.

Do NOT accept a near-match ref.

Do NOT retry just the failed ticker.

---

# 30. Full 22 acceptance

PASS requires:

```text
22 / 22 subjects represented

all required model calls complete

fundamental core schema valid = 22

fundamental core exact-ref fidelity violations = 0

fundamental core semantic valid = 22

Stage-2 valid = 22

postconfirmation maturity conflicts = 0

final composition valid = 22

BusinessDelta hard failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchor = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

fallback/judge/repair/selective rerun = 0.
```

No expected direction distribution.

---

# 31. CORZ regression

Require:

```text
post_confirmation_hold = true
⇒
overall_maturity = CONFIRMED.
```

The exact old invalid candidate stays invalid.

No CORZ target direction.

---

# 32. RXRX regression

Report new RXRX:

```text
overall direction

holder

all evidence refs emitted

ref catalog membership

subject ownership result.
```

Require:

```text
fabricated evidence ref count = 0

exact-ref fidelity violation count = 0.
```

No expected direction.

---

# 33. GOOGL regression

Report:

```text
overall direction

new buyer

holder

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

No expected BUY/HOLD/SELL.

---

# 34. Three-axis renderer

After clean reproof,
render all 22 locally.

Require:

```text
overall direction visible = 22

new-buyer visible = 22

holder visible = 22

REVIEW copy safe

mechanical stance mapping = 0.
```

Do not deploy yet.

---

# 35. Phase A top-level result

Choose:

```text
EXACT_EVIDENCE_REF_FIDELITY_REPAIR_AND_FULL_REPROOF_PASS

FULL_REPROOF_NEW_HARD_FAILURE

MODEL_TRANSPORT_INCOMPLETE

PREMODEL_TEST_GATE_FAILURE.
```

Phase B may run ONLY for the first result.

---

# 36. Phase B — historical Kiwoom night-futures recovery audit

This is mandatory after a clean Phase A.

The user states that in early September there was a dedicated implementation built from:

```text
actual Kiwoom night-futures data
for 2026-09-01
2026-09-02
2026-09-03
```

and code was written/refined against those extracted samples.

M12BS incorrectly treated night futures as if a new connector had to be built
without first recovering that implementation.

M12BU must recover that historical work before any new provider development.

---

# 37. Historical search window

Search local repository history and all local refs around:

```text
2026-08-31 through 2026-09-06
```

with emphasis on:

```text
2026-09-01
2026-09-02
2026-09-03.
```

Use read-only Git commands.

Search:

```text
git log --all

git branch --all

git tag

git show

git grep on historical commits

git reflog where available.
```

Do not mutate history.

---

# 38. Historical search terms

Search both code and commit metadata for:

```text
night_futures

night futures

야간선물

야간 선물

KOSPI200

KOSPI 200

KOSDAQ150

KOSDAQ 150

Kiwoom

키움

OpenAPI

futures

선물

evening

night session

overnight.
```

Also search actual parser field names discovered in historical artifacts.

Do not stop after the first match.

---

# 39. Search current and historical artifact references

Search:

```text
tracked source files

tracked tests

tracked fixtures

historical artifact/report manifests

proof reports

sample JSON/CSV/text extracts

README/design notes

local branches.
```

If normal history does not find the implementation:

inspect read-only:

```text
reflogs

dangling/unreachable commit metadata
```

using safe Git inspection only.

Do NOT run garbage collection.

Do NOT rewrite refs.

Do NOT resurrect commits yet.

---

# 40. Recover exact historical implementation identity

For every candidate historical implementation record:

```text
commit SHA

branch/ref if available

commit timestamp

files changed

parser/service modules

fixture/sample files

tests

data-source path

output fact schema

message integration path.
```

Determine which implementation was the final one tested against the 9/1-9/3 samples.

Do not choose the oldest prototype merely because it appears first.

---

# 41. Recover actual 9/1, 9/2, 9/3 samples

Locate the exact preserved sample data used for development.

Acceptable forms:

```text
raw Kiwoom API response

normalized JSON

CSV

captured structured text

test fixture produced directly from the extraction.
```

Record:

```text
date

instrument

session

source

field names

sample hash.
```

Do not fabricate samples from screenshots or memory if exact data exists.

---

# 42. Expected instrument scope

Audit whether the historical implementation covered:

```text
KOSPI200 night futures

KOSDAQ150 night futures
```

or only one of them.

Do not assume both.

The user recalls Kiwoom night-futures data for 9/1-9/3,
and earlier historical artifacts indicate both KOSPI200 and KOSDAQ150 may have existed.

Recover the actual implemented scope.

---

# 43. Historical parser reproduction

Against the exact preserved samples,
run the historical parser in an isolated/local compatibility harness.

Do not call live Kiwoom.

Compare outputs to historical expected values/tests.

Record:

```text
instrument identity

session identity

current/close value

reference/settlement value

change value

change percent

as-of timestamp

timezone

trading date.
```

Use only fields the historical parser actually owned.

---

# 44. Historical data fidelity

Require:

```text
9/1 reproduction

9/2 reproduction

9/3 reproduction
```

for every instrument that had a preserved fixture.

Report:

```text
exact match

normalization-only difference

failure.
```

Do not silently update expected historical values.

---

# 45. Determine current-code disappearance reason

Classify why the implementation is not used by current canonical market messages:

```text
MERGE_OMISSION

LATER_REFACTOR_REMOVAL

CODE_STILL_EXISTS_BUT_NOT_WIRED

LEGACY_PIPELINE_ISOLATION

SOURCE_AUTH_PATH_REMOVED

TEST_ONLY_IMPLEMENTATION

SUPERSEDED_BY_ANOTHER_IMPLEMENTATION

UNKNOWN.
```

Support classification with Git/code evidence.

---

# 46. Existing source/auth path audit

Determine what the historical Kiwoom implementation required:

```text
local Windows OpenAPI process

authenticated Kiwoom session

gateway/service

TR/request identifiers

market code

account/login dependency

non-account market-data login only if supported.
```

Do not expose credentials.

Do not assume trading permission was required.

Separate:

```text
read-only market-data auth

from

order/trading capability.
```

---

# 47. Read-only permission target

For future reintegration,
the desired scope is:

```text
market-data read only.
```

No order submission.

No modification/cancel.

No portfolio mutation.

No account trading action.

If the historical code depended on a broader process token,
identify how to restrict the runtime path to quote/read requests only.

---

# 48. Current LeadingMarketSnapshot mapping

Map historical output into the current M12BS concept:

```text
LeadingMarketSnapshot
```

or exact current equivalent.

For each historical field decide:

```text
directly reusable

needs deterministic adapter

obsolete

unsafe/ambiguous.
```

Do NOT copy old semantics blindly.

---

# 49. Completed-session separation

Historical night-futures values must map to:

```text
leading / overnight market context
```

not:

```text
completed cash-session return.
```

Reintegration plan must preserve:

```text
completed session

current night/evening futures
```

as separate observations.

---

# 50. Fundamental ownership separation

Historical Kiwoom futures data may be used for:

```text
market risk appetite

next-session timing

new-buyer timing context.
```

It may NOT create:

```text
BusinessDelta

holder REVIEW/REDUCE

fundamental invalidation

earnings change.
```

The reintegration plan must explicitly preserve this.

---

# 51. No new connector before recovery decision

M12BU MUST NOT:

```text
build a new US futures connector

build a new KR Kiwoom connector

scrape CME

replace Kiwoom with ETF moves

replace futures with an unrelated derivative.
```

First finish historical recovery.

After recovery choose one:

```text
HISTORICAL_IMPLEMENTATION_REUSABLE

HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

HISTORICAL_IMPLEMENTATION_SOURCE_AUTH_OBSOLETE

HISTORICAL_IMPLEMENTATION_NOT_FOUND.
```

---

# 52. Historical recovery success criteria

A successful recovery audit requires:

```text
exact historical implementation commit/path identified

9/1-9/3 sample fixtures identified

historical parser reproduced locally

historical output contract understood

current pipeline disconnect reason identified

current reintegration mapping defined

read-only auth/runtime requirement defined

no new connector written.
```

---

# 53. If historical implementation cannot be found

Do not conclude immediately that it never existed.

Report search coverage:

```text
branches searched

commit window searched

reflog searched

artifact references searched

unreachable commits inspected or not

sample fixtures found/not found.
```

Only then classify:

```text
HISTORICAL_IMPLEMENTATION_NOT_FOUND.
```

Next scope may investigate archived worktrees/backups
before new connector development.

---

# 54. If source/auth is obsolete

If code is found but live source/auth path no longer works:

preserve historical parser/tests.

Classify:

```text
HISTORICAL_IMPLEMENTATION_SOURCE_AUTH_OBSOLETE.
```

Then a later task may replace only the live transport layer
while reusing:

```text
instrument identity

normalization contract

session semantics

message integration tests.
```

Do not throw away the historical work.

---

# 55. Phase B does not deploy

Even if historical implementation is fully reusable:

Do NOT integrate/deploy in M12BU.

Produce the bounded next scope:

```text
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE
```

with exact recovered code/sample identities.

Reason:

keep the 22-subject model reproof and the futures source reintegration causally separate.

---

# 56. US futures

The historical Kiwoom recovery audit is primarily KR night futures.

Also record whether the historical implementation included:

```text
US index futures
```

through Kiwoom overseas futures or another prior path.

Do not assume it did.

If not:

leave US futures source as a separate unresolved source.

The future reintegration task may have:

```text
KR historical recovery path
+
US safe-source decision.
```

---

# 57. Production firewall

Throughout M12BU:

```text
production DB mutations = 0

assessment writes = 0

warning mutations = 0

notification queue writes = 0

production sends = 0

scheduler mutations = 0

monitoring registrations/stops = 0

main merge = 0

deployment = 0

remote raw artifact push = 0.
```

External model calls for the frozen 22 reproof are allowed.

Historical Git/source audit is local/read-only.

---

# 58. Required Phase-A forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bu-scope-freeze

04-m12bt-failure-freeze

05-rxrx-exact-ref-forensic

06-fundamental-core-evidence-ref-field-inventory

07-structured-output-ref-enum-capability

08-exact-ref-fidelity-options

09-exact-ref-fidelity-decision

10-ref-catalog-hash-contract.
```

---

# 59. Required Phase-A implementation/test artifacts

Produce:

```text
11-core-ref-enum-schema-implementation

12-core-ref-fidelity-prompt-implementation

13-exact-ref-positive-fixtures

14-exact-ref-negative-fixtures

15-cross-subject-valid-ref-ownership-negative

16-exact-old-rxrx-invalid-replay

17-schema-size-safety-audit

18-focused-ref-fidelity-tests

19-m12bt-regression-tests

20-full-local-test-result

21-ruff-diff-result

22-model-facing-hash-change-manifest.
```

---

# 60. Required Phase-A reproof artifacts

Produce:

```text
23-frozen-22-input-identity-manifest

24-new-full-reproof-generation-manifest

25-full-reproof-call-plan-with-ref-catalog-hashes

26-fundamental-core-model-artifacts

27-stage2-model-artifacts

28-schema-audit

29-exact-ref-fidelity-audit

30-canonical-semantic-audit

31-postconfirmation-maturity-audit

32-price-timing-immutability-audit

33-expectation-valuation-anchor-audit

34-business-delta-audit

35-core-immutability-audit

36-final-composition-audit

37-per-ticker-result-matrix

38-rxrx-postrepair-dossier

39-corz-postrepair-dossier

40-googl-postrepair-dossier

41-three-axis-render-audit

42-phase-a-reproof-decision.
```

---

# 61. Required Phase-B historical recovery artifacts

ONLY if Phase A PASS:

```text
43-historical-kiwoom-search-plan

44-git-history-search-results

45-branch-ref-search-results

46-reflog-unreachable-search-results

47-historical-night-futures-implementation-candidates

48-historical-final-implementation-identity

49-historical-20260901-sample-identity

50-historical-20260902-sample-identity

51-historical-20260903-sample-identity

52-historical-instrument-scope

53-historical-parser-contract

54-historical-parser-reproduction-20260901

55-historical-parser-reproduction-20260902

56-historical-parser-reproduction-20260903

57-historical-readonly-auth-runtime-contract

58-current-leading-market-mapping

59-current-pipeline-disconnect-root-cause

60-historical-reuse-decision

61-night-futures-reintegration-plan.
```

If Phase A fails:

mark Phase B:

```text
NOT_RUN_PHASE_A_BLOCKED
```

and keep the promised next scope in the workflow note.

---

# 62. Required final decisions

Produce:

```text
62-exact-ref-fidelity-repair-decision

63-full-22-reproof-decision

64-message-model-contract-readiness

65-historical-kiwoom-recovery-decision

66-leading-futures-next-scope-decision

67-deployment-readiness

68-master-workflow-update

69-program-completion.
```

---

# 63. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bt_failure_ticker
m12bt_supplied_valid_ref
m12bt_emitted_invalid_ref
m12bt_failure_class

exact_ref_fidelity_contract_version

fundamental_core_prompt_change_count
fundamental_core_schema_change_count
stage2_prompt_change_count_after_m12bt
stage2_schema_change_count
canonical_semantic_service_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
persistence_v2_contract_change_count

ref_enum_supported
per_subject_ref_enum_supported
ref_catalog_count_total
max_ref_catalog_count_per_batch
max_schema_size_bytes
ref_schema_size_limit_status

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
exact_ref_fidelity_violation_count
fabricated_ref_count
cross_subject_ref_ownership_failure_count

stage2_valid_count
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

rxrx_overall_direction
rxrx_holder
rxrx_emitted_ref_count
rxrx_fabricated_ref_count

corz_overall_direction
corz_overall_maturity
corz_post_confirmation_hold

googl_overall_direction
googl_new_buyer
googl_holder
googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class

phase_a_result

historical_kiwoom_audit_ran

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

us_futures_source_status
kr_night_futures_source_status

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
NOT_RUN_PHASE_A_BLOCKED

NOT_FOUND

NOT_APPLICABLE

NOT_MEASURED
```

where appropriate.

Do not substitute zero for unknown.

---

# 64. Expected clean Phase-A result

Expected if exact-ref fidelity repair works:

```text
phase_a_result =
EXACT_EVIDENCE_REF_FIDELITY_REPAIR_AND_FULL_REPROOF_PASS

fundamental_core_valid_count = 22

exact_ref_fidelity_violation_count = 0

fabricated_ref_count = 0

stage2_valid_count = 22

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

Do NOT force decision enums.

---

# 65. Expected historical recovery result

Preferred outcome:

```text
historical_kiwoom_audit_ran = true

historical_final_implementation_commit = identified

historical_20260901_sample_found = true

historical_20260902_sample_found = true

historical_20260903_sample_found = true

historical_parser_reproduction = PASS

historical_reuse_decision =
HISTORICAL_IMPLEMENTATION_REUSABLE
or
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER.
```

Do NOT force this outcome.

If the code is found but auth/source is obsolete:

report that honestly.

---

# 66. Next scope after clean Phase A + successful historical recovery

Required:

```text
next_scope =
HISTORICAL_KIWOOM_NIGHT_FUTURES_REINTEGRATION_AND_FINAL_MESSAGE_SMOKE
```

This next task should:

```text
reuse recovered 9/1-9/3 implementation/tests

integrate into current LeadingMarketSnapshot

perform current read-only Kiwoom quote smoke if auth is available

resolve US futures separately

deploy only after source safety + full message smoke pass.
```

---

# 67. Next scope if Phase A passes but historical code is not found

Required:

```text
next_scope =
ARCHIVED_KIWOOM_NIGHT_FUTURES_IMPLEMENTATION_RECOVERY_OR_SOURCE_REPLACEMENT_DECISION
```

Do NOT jump directly to a new connector.

Search archived worktrees/backups/artifact references first.

---

# 68. Failure handling

## A. Exact-ref enum unsupported

If simple string enum itself is unsupported:

```text
STOP
STRUCTURED_OUTPUT_EXACT_REF_ENUM_UNSUPPORTED.
```

No prompt-only proof retry unless separately authorized.

## B. Enum schema too large

```text
STOP
EVIDENCE_REF_ENUM_SCHEMA_SIZE_LIMIT.
```

Propose short alias contract next.

## C. RXRX or another subject fabricates a ref despite enum/schema

```text
STOP
EXACT_REF_SCHEMA_ENFORCEMENT_FAILURE.
```

No fuzzy acceptance.

## D. Cross-subject exact ref appears

Existing semantic ownership validator must fail.

Do not broaden ownership.

## E. New hard semantic failure

Stop proof under current policy.

No repair inside M12BU.

## F. Full 22 PASS

Proceed to the historical Kiwoom audit.

## G. Historical implementation is found

Do not reintegrate yet.

Freeze exact provenance and next-step plan.

---

# 69. Final task principle

M12BT proved two things:

```text
1. the CORZ post-confirmation maturity validator was correct
   and its model-facing prompt repair is locally valid;

2. the full reproof exposed a different, narrower issue:
   the model copied one evidence-ref digit incorrectly,
   while the schema allowed arbitrary ref strings.
```

The correct model-contract repair is:

```text
restrict model evidence refs to the exact supplied catalog

→ keep exact ownership validation

→ never fuzzy-correct refs

→ run a brand-new full 22-subject proof

→ if clean, stop model-contract work.
```

Then, because the user has explicitly recalled an earlier
2026-09-01 / 09-02 / 09-03 Kiwoom night-futures implementation,
the correct futures workflow is:

```text
DO NOT build a new connector first

→ recover the historical code/commit/fixtures

→ reproduce its parser against the exact 9/1-9/3 extracted data

→ identify why it disappeared from the current pipeline

→ map it into LeadingMarketSnapshot

→ preserve read-only quote usage

→ integrate/deploy only in the NEXT bounded task.
```

Do NOT:

```text
special-case RXRX

weaken ref ownership

fuzzy-match evidence refs

reuse the partial M12BT generation

patch CORZ again

start a new night-futures connector before recovering the old one

treat screenshots/memory as a substitute for exact historical fixtures

merge/deploy in M12BU

resume scheduler or notifications.
```
