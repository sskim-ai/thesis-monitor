# Thesis Monitor — Frozen-Context Input Layout Compatibility + New Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260913-frozen-context-input-layout-compatibility-new-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260913-frozen-context-input-layout-compatibility-new-full-shadow-report.zip
```

Master-workflow phase:

```text
M12BF — Frozen-State Verification Contract Compatibility
         A. Freeze successful M12BE active-universe count-contract repair
         B. Freeze successful M12BD complete formal fictional proof
         C. Reproduce exact nested-vs-flat frozen-context verification failure
         D. Make frozen-input verification explicitly layout-aware
         E. Preserve strict hash/path verification and fail on ambiguous dual layout
         F. Reuse M12BD fictional proof only if model-facing semantics remain identical
         G. Create a NEW full shadow generation after the verifier repair
         H. Run the complete monitored compatibility shadow
         I. If objectively clean, hand off to boundary / delta / holder policy review
```

M12BE successfully repaired the previous:

```text
active_count
vs
subject_count
```

shadow preflight contract drift.

M12BE reports:

```text
count_contract_status = PASS

cross_manifest_ticker_set_mismatch_count = 0

cross_manifest_duplicate_ticker_count = 0

task_start_active_monitor_count = 22

formal_fictional_reuse_status =
REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF

new_fictional_model_calls = 0

shadow_preflight_status = PASS
```

A NEW shadow generation was correctly created:

```text
generation =
20260911-m12ai-shadow-20260913T132402Z-c956834e1892

context_count = 6

planned_model_calls = 18
```

The shadow then stopped BEFORE any model process was spawned:

```text
phase =
SHADOW_PRESPAWN_FROZEN_STATE_VERIFICATION

model_calls_started = 0

model_calls_completed = 0

error =
KeyError: stage1_prompt
```

The producer and consumer disagree only on the serialized layout of
frozen input path/hash metadata.

Producer layout:

```text
frozen_contexts[].inputs.<input_name>.{path, sha256}
```

Consumer layout:

```text
frozen_contexts[].<input_name>
frozen_contexts[].<input_name>_sha256
```

This is a deterministic frozen-state verifier compatibility bug.

Do not change model prompts, schemas, evidence views, or investment semantics.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260913-shadow-active-universe-count-contract-compatibility-new-full-shadow-report.zip
```

Verified SHA-256:

```text
f9caae35d4c2a520103d34a8601ade64228322474d80ca3aec6ddf7e3ca35a49
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent archive verification:

```text
artifact_count = 793

ZIP entries =
793 indexed payloads
+ artifact-index.json
= 794

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12BE program status

Reported:

```text
phase = M12BE

status = BLOCKED

next_scope =
BOUNDED_FROZEN_CONTEXT_INPUT_LAYOUT_COMPATIBILITY_REPAIR_AND_NEW_GENERATION
```

The blocker is entirely pre-spawn.

Required frozen facts:

```text
shadow_model_calls_started = 0

shadow_model_calls_completed = 0

shadow_planned_model_calls = 18

provider_source_fetches = 0

production side effects = 0

selective reruns = 0

post-freeze hotfixes = 0
```

No candidate output exists for this shadow generation.

---

# 3. M12BD fictional proof — freeze successful

M12BE already revalidated and authorized reuse of the complete M12BD proof.

Preserve:

```text
fictional generation =
20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6

model =
gpt-5.6-sol / xhigh

model calls =
12 / 12

Stage 1 rows =
24 / 24

Stage 2 rows =
24 / 24

final compositions =
24

aggregate finalization =
PASS

hard semantic failures =
0

core mutation =
0
```

M12BF should not run new fictional model calls
unless a model-facing semantic identity gate fails.

Expected:

```text
formal_fictional_reuse_status =
REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF

new_fictional_model_calls =
0
```

---

# 4. M12BE active-universe count repair — freeze successful

Preserve:

```text
market-expectation-evidence-view-v1
authoritative count field =
subject_count
```

M12BE changed the stale consumer,
not the producer contract.

Preserve strict subject identity:

```text
count equality

row-count equality

exact ticker-set equality

duplicate count = 0

missing count = 0

extra count = 0
```

Do not reintroduce:

```text
direct ["active_count"] mapping access.
```

M12BE reports the post-repair direct Python hardcode scan:

```text
active_count direct mapping access count = 0.
```

Freeze this.

---

# 5. Exact new shadow setup before failure

M12BE new shadow state contains:

```text
active tickers = 22

packet count = 22

context count = 6

planned monolithic calls = 6

planned Stage-1 calls = 6

planned Stage-2 calls = 6

planned total calls = 18.
```

Cross-manifest preflight:

```text
status = PASS

ticker_set_mismatch_count = 0

duplicate_ticker_count = 0.
```

Do not reopen count/ticker-set semantics.

---

# 6. Exact producer layout

M12BE shadow `program-state.json`
stores each frozen context like:

```json
{
  "context": 1,
  "tickers": ["000660", "003690", "005490", "005930"],
  "inputs": {
    "monolithic_prompt": {
      "path": ".../context-01/monolithic-prompt.txt",
      "sha256": "..."
    },
    "monolithic_schema": {
      "path": ".../context-01/monolithic-schema.json",
      "sha256": "..."
    },
    "stage1_prompt": {
      "path": ".../context-01/stage1-prompt.txt",
      "sha256": "..."
    },
    "stage1_schema": {
      "path": ".../context-01/stage1-schema.json",
      "sha256": "..."
    },
    "stage2_schema": {
      "path": ".../context-01/stage2-schema.json",
      "sha256": "..."
    }
  }
}
```

This is internally complete.

All required inputs have:

```text
path

sha256.
```

The producer is not missing `stage1_prompt`.

It is nested under `inputs`.

---

# 7. Legacy fictional layout contrast

The frozen M12BD fictional state uses the legacy flat representation:

```json
{
  "context": 1,
  "stage1_prompt": ".../stage1-prompt.txt",
  "stage1_prompt_sha256": "...",
  "stage1_schema": ".../stage1-schema.json",
  "stage1_schema_sha256": "...",
  "stage2_schema": ".../stage2-schema.json",
  "stage2_schema_sha256": "..."
}
```

This legacy layout is still valid for the already completed fictional generation.

Therefore the shared verifier must understand BOTH versioned layouts safely.

Do not force a destructive migration of archived fictional state.

---

# 8. Exact stale consumer

The shared verifier in:

```text
scripts/business_delta_evidence_capability_m12ai.py
```

currently performs logic equivalent to:

```python
for key in (
    "stage1_prompt",
    "stage1_schema",
    "stage2_schema",
):
    path = Path(str(row[key]))
    if file_sha256(path) != row[f"{key}_sha256"]:
        fail()
```

Optional:

```text
monolithic_prompt
monolithic_schema
```

are read the same flat way.

This verifier assumes the legacy flat layout.

It is called by:

```text
run_shadow()
```

before any model spawn.

Hence:

```text
row["stage1_prompt"]
```

raises:

```text
KeyError
```

for the canonical nested shadow state.

---

# 9. Root-cause classification

Freeze:

```text
SHARED_FROZEN_STATE_VERIFIER_ONLY_SUPPORTS_LEGACY_FLAT_INPUT_LAYOUT
WHILE_SHADOW_PRODUCER_EMITS_NESTED_INPUT_IDENTITY_LAYOUT
```

This is NOT:

```text
a missing file

a hash mismatch

a prompt generation failure

a schema generation failure

a packet mismatch

a model-runtime failure

an active-universe failure.
```

---

# 10. Preferred architecture

Introduce one strict resolver such as:

```text
resolve_frozen_context_input(row, input_name)
```

or equivalent.

The resolver must return exactly:

```text
path

sha256

layout
```

for a requested input identity.

Supported layouts:

```text
LEGACY_FLAT

NESTED_INPUTS_V1
```

Do not let every caller reimplement layout detection.

---

# 11. Nested layout contract

For:

```text
NESTED_INPUTS_V1
```

require:

```text
row["inputs"] is a mapping

row["inputs"][input_name] is a mapping

entry["path"] exists and is non-empty

entry["sha256"] exists and is a valid SHA-256 identity string.
```

Then:

```text
actual file SHA-256 == entry["sha256"].
```

No fallback to unrelated fields.

---

# 12. Legacy flat layout contract

For:

```text
LEGACY_FLAT
```

require BOTH:

```text
row[input_name]

row[input_name + "_sha256"].
```

Then:

```text
actual file SHA-256 == declared flat SHA-256.
```

This preserves completed fictional-state compatibility.

---

# 13. Ambiguous dual layout must hard fail

If the same row provides BOTH:

```text
nested inputs.<name>

and

flat <name> / <name>_sha256
```

do NOT silently choose one.

Preferred:

```text
FAIL
AMBIGUOUS_FROZEN_INPUT_LAYOUT
```

even if values happen to match.

Reason:

```text
dual representations can drift later
and hide producer/consumer contract errors.
```

Do not normalize silently.

---

# 14. Partial dual layout must hard fail

Examples:

```text
nested stage1_prompt exists
but flat stage1_prompt_sha256 also exists

or

flat path exists
while nested hash exists.
```

Expected:

```text
FAIL
PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT.
```

One input identity must come from one coherent layout.

---

# 15. Required input names

For all two-stage frozen contexts require:

```text
stage1_prompt

stage1_schema

stage2_schema.
```

For shadow contexts additionally require:

```text
monolithic_prompt

monolithic_schema.
```

Do not require:

```text
stage2_prompt
```

because Stage-2 prompt may be generated from frozen Stage-1 core
according to the current two-stage architecture.

Preserve actual repository behavior.

---

# 16. Optional-vs-required must be explicit

Do not keep generic logic:

```text
if key present then verify
```

for shadow monolithic inputs.

The verifier caller should declare the expected input set.

Suggested:

```text
fictional required:
stage1_prompt
stage1_schema
stage2_schema

shadow required:
monolithic_prompt
monolithic_schema
stage1_prompt
stage1_schema
stage2_schema.
```

Missing required input:

```text
hard fail before model spawn.
```

---

# 17. Path existence / file identity

For every resolved input:

```text
path must exist

path must be a file

SHA-256 must match.
```

If path does not exist:

```text
FAIL
FROZEN_INPUT_MISSING.
```

If hash differs:

```text
FAIL
FROZEN_INPUT_CHANGED:<input_name>.
```

Do not weaken frozen-state integrity.

---

# 18. Context-directory identity

Where practical,
also require the resolved frozen input path
to belong to the expected context directory:

```text
.../frozen-contexts/context-XX/
```

and the input filename to match the requested semantic input.

Examples:

```text
stage1_prompt
→ stage1-prompt.txt

stage1_schema
→ stage1-schema.json.
```

If repository conventions intentionally allow alternative filenames,
use a contract mapping rather than substring guessing.

---

# 19. Do not rewrite producer state into flat layout

Forbidden primary repair:

```text
duplicate all nested paths/hashes into flat fields
just to satisfy the old verifier.
```

That recreates two sources of truth.

Preferred:

```text
fix the shared consumer/verifier.
```

The nested shadow layout is more explicit and should remain canonical
for newly produced shadow states.

---

# 20. Do not remove legacy fictional compatibility

Also forbidden:

```text
nested-only verifier
```

that breaks the frozen completed M12BD fictional state.

The verifier must be:

```text
strictly dual-layout aware
```

until a separate versioned migration removes the legacy format.

No migration in M12BF.

---

# 21. Layout identity report

For every frozen context,
produce an audit row:

```text
context

input_name

detected_layout

declared_path

declared_sha256

actual_sha256

path_exists

hash_match

status.
```

For M12BF new shadow expected:

```text
all rows =
NESTED_INPUTS_V1

all PASS.
```

For frozen M12BD fictional replay expected:

```text
all relevant rows =
LEGACY_FLAT

all PASS.
```

---

# 22. Exact M12BE stopped shadow offline replay

Do NOT run the old shadow.

Offline only:

Use the repaired input resolver
against the stopped M12BE nested frozen-context rows.

Expected:

```text
context count = 6

required shadow inputs per context = 5

resolved input identities = 30

nested layout count = 30

missing = 0

ambiguous = 0

hash mismatch = 0

status = PASS.
```

This proves the layout repair.

Do not authorize resuming the old generation.

---

# 23. Frozen M12BD fictional compatibility replay

Offline verify the completed M12BD fictional state
with the same resolver.

Expected:

```text
context rows use LEGACY_FLAT

required fictional input identities all resolve

hash mismatch = 0

status = PASS.
```

This proves the shared verifier did not break archived formal proof identity.

---

# 24. Positive layout fixtures

## INPUT-LAYOUT-P01 — legacy flat

```text
stage1_prompt + stage1_prompt_sha256
stage1_schema + stage1_schema_sha256
stage2_schema + stage2_schema_sha256

→ PASS.
```

## INPUT-LAYOUT-P02 — nested

```text
inputs.stage1_prompt.{path,sha256}
inputs.stage1_schema.{path,sha256}
inputs.stage2_schema.{path,sha256}

→ PASS.
```

## INPUT-LAYOUT-P03 — shadow nested

All five:

```text
monolithic_prompt
monolithic_schema
stage1_prompt
stage1_schema
stage2_schema

→ PASS.
```

---

# 25. Negative layout fixtures

## INPUT-LAYOUT-N01 — both layouts

Same input exists in nested and flat forms.

Expected:

```text
FAIL
AMBIGUOUS_FROZEN_INPUT_LAYOUT.
```

## INPUT-LAYOUT-N02 — nested missing sha

```text
inputs.stage1_prompt.path exists
sha256 missing

→ FAIL.
```

## INPUT-LAYOUT-N03 — flat missing hash

```text
stage1_prompt exists
stage1_prompt_sha256 missing

→ FAIL.
```

## INPUT-LAYOUT-N04 — hash mismatch

Declared hash does not match file.

```text
→ FAIL.
```

## INPUT-LAYOUT-N05 — required input missing

Shadow context missing:

```text
monolithic_schema

→ FAIL before spawn.
```

## INPUT-LAYOUT-N06 — unknown malformed inputs object

```text
inputs = []
```

or non-mapping.

Expected:

```text
FAIL.
```

---

# 26. Layout resolver must not become heuristic

Do NOT:

```text
search arbitrary nested fields for something ending in "_prompt"

take first matching path

infer hash from adjacent field names

accept unknown layout on best effort.
```

Recognized layouts only.

Unknown layout:

```text
FAIL_CLOSED.
```

---

# 27. Shared verifier caller contract

Refactor:

```text
_verify_frozen_state(...)
```

to call the strict resolver.

Preferred caller API may include:

```text
subject

required_inputs

allow_legacy_flat

allow_nested_inputs.
```

For current use:

```text
FICTIONAL:
allow legacy flat = true
allow nested = true

SHADOW:
allow legacy flat = true
allow nested = true
required monolithic inputs = true.
```

The dual allowance is for compatibility;
each ROW/INPUT still must resolve unambiguously to one layout.

---

# 28. Code-hash behavior

The verifier implementation itself will change.

Therefore an OLD stopped shadow state may fail:

```text
state["code_hashes"] == current _code_hashes()
```

after the patch.

That is expected.

Do NOT weaken the code-hash invariant
to resume the old generation.

Instead:

```text
offline replay only for layout identity

then create a NEW shadow generation
under the repaired code hash.
```

This is mandatory.

---

# 29. Fictional proof reuse despite verifier code change

Changing the frozen-state verifier
is NOT a model-facing semantic change.

M12BF may still reuse M12BD fictional proof
if the semantic surfaces remain unchanged.

Required semantic freeze:

```text
model prompt = unchanged

model schema = unchanged

Stage-1 WC binding view = unchanged

Stage-2 WC binding view = unchanged

configured-signal view = unchanged

configured financial support concepts = unchanged

BusinessDeltaEvidenceView = unchanged

MarketExpectationEvidenceView = unchanged

financial evidence projection = unchanged

two-stage core semantics = unchanged

final user schema = unchanged.
```

The verifier code hash may differ;
model-facing semantic hashes must not.

---

# 30. Formal fictional reuse decision

Expected:

```text
formal_fictional_reuse_status =
REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF

new_fictional_model_calls = 0.
```

If any model-facing semantic surface changed:

```text
NEW_FORMAL_PROOF_REQUIRED.
```

Run a full new 12-call proof before shadow.

No partial reuse.

---

# 31. M12BE count-contract repair — preserve

Re-run:

```text
subject_count contract fixtures

non-22 dynamic universe fixture

same-count different ticker-set negative fixture

duplicate ticker negative fixture

unknown report contract fail-closed fixture.
```

Expected:

```text
PASS.
```

No `active_count` regression.

---

# 32. New shadow generation mandatory

After the layout/verifier patch,
create a NEW shadow generation.

Do not resume:

```text
20260911-m12ai-shadow-20260913T132402Z-c956834e1892.
```

Reason:

```text
frozen-state verifier code hash changed

old generation stopped before spawn

clean provenance requires a new freeze under repaired verifier.
```

---

# 33. Re-enumerate active monitored names read-only

At M12BF shadow start:

```text
read the active monitored universe again.
```

No hard-coded 22.

No registrations.

No stops.

If active count changed:

```text
recompute context count and model-call plan.
```

---

# 34. Same-packet shadow contract

For each active ticker:

```text
one reproducible local frozen packet

same packet hash feeds:
monolithic
Stage 1
Stage 2.
```

No provider refresh.

Required:

```text
provider_source_fetches = 0.
```

---

# 35. New frozen-context manifest

For every new shadow context
emit the canonical nested input identity layout:

```text
inputs.<input_name>.path

inputs.<input_name>.sha256.
```

Also emit:

```text
context

tickers

packet hashes

BusinessDeltaEvidenceView hash

MarketExpectationEvidenceView hash

WC binding-view identity where applicable.
```

No duplicate flat input fields.

---

# 36. Pre-spawn frozen-state gate

Before the first model process,
require:

```text
all context inputs resolve

all required paths exist

all hashes match

no ambiguous dual layout

state code hashes match current implementation

packet hashes match

view identities match

active universe identity matches

planned calls match context count.
```

Then and only then spawn.

---

# 37. Shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage-1 calls = context_count

Stage-2 calls = context_count

total = 3 × context_count.
```

If N remains 22:

```text
contexts = 6

total calls = 18.
```

No repetitions.

---

# 38. Shadow model

Use:

```text
gpt-5.6-sol / xhigh.
```

No Astra.

No fallback.

No judge calls.

No selective rerun.

---

# 39. Shadow hard-stop policy

Hard stop only for objective failures:

```text
runtime/schema failure

frozen input path/hash mismatch

frozen layout ambiguity

packet mismatch

active-universe identity mismatch

invalid evidence identity

Stage-1 WC grounding failure

Stage-2 WC grounding failure

WC metric-specific ref mismatch

WC narrative-only substitution

irrelevant typed financial grounding

unsafe WC auto-direction

configured-signal field-use violation

configured-signal false fulfillment

FCF hard semantic violation

financial-sector hard semantic violation

business-delta hard semantic violation

market-expectation hard semantic violation

Stage-2 contamination

ADR/security-basis failure

core mutation

aggregate finalization failure

production-side-effect attempt.
```

Decision differences remain diagnostic only.

---

# 40. Optional audit coverage remains nonblocking

Preserve M12BD:

```text
zero observed optional lexical claim
!= semantic failure.
```

For every optional audit report:

```text
observed_claim_count

semantic_violation_count

coverage_status

semantic_status

readiness_blocking.
```

Do not reopen.

---

# 41. Stage-2 WC binding remains hard

Preserve:

```text
claim-local Stage-2 typed WC grounding.
```

For:

```text
fundamental_new_buyer.confirmation_business_condition

fundamental_holder.business_invalidation_condition
```

typed WC refs must be directly bound
when the condition mentions selected WC metrics
or generic WC and selected typed WC evidence exists.

No candidate-global grounding.

---

# 42. Context-preserving finalization remains hard

Preserve M12BC:

```text
model-call batch max = 4

no cross-context 8-candidate DirectionalCoreBatch

context identity preserved

final report aggregates audit rows only.
```

No change.

---

# 43. Decision variance remains diagnostic

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

OTHER_REVIEW_REQUIRED.
```

No exact enum stability requirement.

---

# 44. Full shadow acceptance

Require:

```text
all planned calls complete

all active tickers represented exactly once

frozen input verification PASS

active-universe identity PASS

packet mismatch = 0

all monolithic hard semantics PASS

all Stage-1 hard semantics PASS

all Stage-2 hard semantics PASS

all final compositions PASS

aggregate finalization PASS

core mutation = 0

Stage-1 WC grounding failure = 0

Stage-2 WC grounding failure = 0

WC metric mismatch = 0

WC narrative substitution = 0

irrelevant financial grounding = 0

unsafe WC auto-direction = 0

configured-signal violations = 0

FCF hard failures = 0

financial-sector hard failures = 0

business-delta hard failures = 0

expectation hard failures = 0

Stage-2 contamination = 0

ADR/security-basis failure = 0

timeout = 0

orphan = 0

wrapper retry = 0

production side effects = 0.
```

Decision-material comparison counts may be nonzero.

---

# 45. Per-ticker compatibility output

For every active ticker report:

```text
ticker

monolithic primary direction

two-stage primary direction

monolithic business delta

two-stage business delta

monolithic new-buyer stance

two-stage new-buyer stance

monolithic holder stance

two-stage holder stance

same-direction balance/calibration difference

comparison taxonomy

objective semantic violations if any

review note.
```

All active tickers exactly once.

---

# 46. Combined policy-review handoff

If full shadow is objectively clean,
combine:

```text
M12BD complete fictional proof

+

M12BF complete monitored shadow.
```

Preserve fictional diagnostics including:

```text
FIC-FIN-05 primary boundary

FIC-FIN-08 holder boundary

fictional same-direction calibration variance

business-delta diagnostics.
```

Add real monitored compatibility differences.

Do not resolve them in M12BF.

---

# 47. Next scope if shadow is clean

Required:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

Also:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY.
```

No fresh unseen proof yet.

---

# 48. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bf-scope-freeze

04-m12bd-fictional-proof-identity-freeze

05-m12be-count-contract-repair-freeze

06-m12be-shadow-layout-failure-reproduction

07-frozen-context-producer-layout-audit

08-frozen-state-verifier-consumer-layout-audit

09-fictional-vs-shadow-layout-comparison

10-frozen-input-layout-options

11-frozen-input-layout-decision

12-frozen-input-resolver-contract

13-required-input-set-contract

14-dual-layout-ambiguity-contract

15-frozen-input-path-hash-contract.
```

---

# 49. Required layout fixtures / offline replays

Produce:

```text
16-legacy-flat-positive-fixture

17-nested-inputs-positive-fixture

18-shadow-five-input-nested-positive-fixture

19-dual-layout-ambiguous-negative-fixture

20-partial-dual-layout-negative-fixture

21-nested-missing-hash-negative-fixture

22-flat-missing-hash-negative-fixture

23-hash-mismatch-negative-fixture

24-required-input-missing-negative-fixture

25-malformed-inputs-negative-fixture

26-m12be-stopped-shadow-layout-offline-replay

27-m12bd-fictional-legacy-layout-offline-replay.
```

---

# 50. Required semantic freeze artifacts

Produce:

```text
28-model-prompt-semantic-hash-freeze

29-model-schema-semantic-hash-freeze

30-stage1-wc-binding-view-hash-freeze

31-stage2-wc-binding-view-hash-freeze

32-configured-signal-view-hash-freeze

33-configured-financial-support-concept-hash-freeze

34-business-delta-view-hash-freeze

35-expectation-view-hash-freeze

36-financial-evidence-projection-hash-freeze

37-two-stage-core-semantics-freeze

38-final-user-schema-freeze

39-fictional-proof-reuse-decision.
```

Artifact 39 exactly one:

```text
REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF
```

or:

```text
NEW_FORMAL_PROOF_REQUIRED.
```

---

# 51. Required regression freeze artifacts

Produce:

```text
40-m12be-active-universe-count-contract-freeze

41-m12bd-stage2-wc-binding-freeze

42-m12bd-optional-audit-coverage-freeze

43-m12bc-context-finalizer-freeze

44-m12bc-diagnostic-variance-readiness-freeze

45-m12bb-stage1-wc-binding-freeze

46-m12ba-financial-sector-replacement-verb-freeze

47-m12az-fcf-local-temporal-scope-freeze

48-m12ay-configured-fcf-support-freeze

49-m12at-configured-signal-field-ownership-freeze

50-m12ap-expectation-independence-freeze

51-m12ao-business-delta-convergence-freeze

52-adr-security-basis-freeze

53-two-stage-core-immutability-freeze.
```

---

# 52. Required deterministic test gate

Produce:

```text
54-frozen-input-layout-unit-tests

55-frozen-state-verifier-regression-tests

56-count-contract-regression-tests

57-stopped-shadow-layout-offline-replay

58-fictional-legacy-layout-offline-replay

59-focused-test-results

60-full-local-test-results

61-ruff-and-diff-results

62-hosted-ci-portability-observation

63-new-shadow-model-call-gate.
```

No model call before artifact 63 PASS.

---

# 53. New shadow setup artifacts

Produce:

```text
64-task-start-active-monitored-universe

65-new-shadow-generation-manifest

66-shadow-packet-inventory

67-shadow-packet-hash-manifest

68-shadow-stage1-wc-binding-view-manifest

69-shadow-stage2-wc-binding-view-manifest

70-shadow-configured-signal-view-manifest

71-shadow-configured-financial-support-concept-manifest

72-shadow-delta-view-manifest

73-shadow-expectation-view-manifest

74-shadow-frozen-context-manifest

75-shadow-frozen-input-layout-audit

76-shadow-cross-manifest-preflight-matrix

77-shadow-batching-manifest

78-shadow-model-call-gate.
```

---

# 54. Required full shadow artifacts

Produce:

```text
79-shadow-monolithic-model-artifacts

80-shadow-stage1-model-artifacts

81-shadow-stage2-model-artifacts

82-shadow-context-hard-semantic-audit

83-shadow-stage1-wc-binding-audit

84-shadow-stage2-wc-binding-audit

85-shadow-financial-grounding-audit

86-shadow-optional-audit-coverage-matrix

87-shadow-configured-signal-field-use-audit

88-shadow-fcf-audit

89-shadow-business-delta-audit

90-shadow-market-expectation-audit

91-shadow-financial-sector-audit

92-shadow-stage2-language-audit

93-shadow-final-composition-audit

94-shadow-aggregate-finalization-audit

95-shadow-per-ticker-comparison

96-shadow-core-direction-differences

97-shadow-business-delta-differences

98-shadow-new-buyer-differences

99-shadow-holder-differences

100-shadow-same-direction-calibration-differences

101-shadow-expected-contract-corrections

102-shadow-potential-architecture-regressions

103-shadow-unresolved-review-required

104-shadow-adr-security-basis-audit

105-shadow-cyclical-valuation-audit

106-shadow-core-immutability-audit

107-shadow-runtime-audit

108-shadow-aggregate-summary

109-shadow-architecture-decision.
```

---

# 55. Required combined handoff artifacts

If shadow completes:

```text
110-fictional-primary-boundary-summary

111-fictional-delta-materiality-summary

112-fictional-new-buyer-boundary-summary

113-fictional-holder-boundary-summary

114-monitored-primary-difference-summary

115-monitored-delta-difference-summary

116-monitored-new-buyer-difference-summary

117-monitored-holder-difference-summary

118-same-direction-calibration-summary

119-combined-fictional-monitored-policy-input

120-next-bounded-policy-decision.
```

---

# 56. Required completion artifacts

Produce:

```text
121-frozen-context-layout-repair-success-decision

122-m12bd-fictional-proof-reuse-success-decision

123-new-full-shadow-completion-decision

124-two-stage-shadow-compatibility-decision

125-existing-monitored-impact-summary

126-fresh-real-proof-readiness-decision

127-final-main-merge-readiness-note

128-production-no-change

129-schedule-pause-observation

130-remote-push-prohibition-audit

131-master-workflow-update

132-program-completion.
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

m12be_shadow_generation_id
m12be_shadow_model_calls_started
m12be_shadow_model_calls_completed
m12be_shadow_stop_reason

frozen_layout_root_cause

frozen_input_resolver_contract_version

legacy_flat_layout_supported
nested_inputs_layout_supported
dual_layout_ambiguity_fails_closed

required_fictional_input_names
required_shadow_input_names

m12be_stopped_shadow_layout_replay_status
m12bd_fictional_legacy_layout_replay_status

m12be_stopped_shadow_nested_input_count
m12be_stopped_shadow_layout_ambiguity_count
m12be_stopped_shadow_hash_mismatch_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
stage1_wc_binding_semantic_change_count
stage2_wc_binding_semantic_change_count
configured_signal_view_change_count
configured_financial_support_concept_change_count
business_delta_view_change_count
expectation_view_change_count
financial_evidence_projection_change_count
two_stage_core_semantic_change_count
final_user_schema_change_count

formal_fictional_reuse_status
new_fictional_model_calls

task_start_active_monitor_count
task_start_active_monitor_tickers

new_shadow_generation_id
shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status
shadow_hard_semantic_failure_count

shadow_frozen_input_verification_failure_count
shadow_frozen_input_hash_mismatch_count
shadow_frozen_input_layout_ambiguity_count

shadow_stage1_wc_grounding_failure_count
shadow_stage2_wc_grounding_failure_count
shadow_stage2_wc_metric_specific_mismatch_count
shadow_stage2_wc_narrative_only_substitution_count

shadow_optional_audit_zero_observation_nonblocking_count

shadow_configured_signal_violation_count
shadow_fcf_hard_failure_count
shadow_business_delta_hard_failure_count
shadow_expectation_hard_failure_count
shadow_financial_sector_hard_failure_count
shadow_stage2_language_false_positive_count

shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_same_direction_calibration_change_count
shadow_multi_field_change_count

shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count

shadow_core_mutation_after_stance_count
shadow_timeout_count
shadow_orphan_count
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
artifact_secret_scan_failure_count.
```

Anything unmeasured:

```text
NOT_MEASURED.
```

---

# 58. Expected completion if full shadow is clean

Expected:

```text
formal_fictional_reuse_status =
REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF

new_fictional_model_calls =
0

shadow_completed_ticker_count =
task_start_active_monitor_count

shadow_aggregate_finalization_status =
PASS

shadow_hard_semantic_failure_count =
0

two_stage_shadow_compatibility_classification =
COMPLETE_WITH_POLICY_DIAGNOSTICS

fresh_real_proof_readiness =
NOT_READY

final_main_merge_readiness =
NOT_READY

production_readiness =
NOT_READY

next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

---

# 59. Failure handling

## A. Nested shadow layout still fails verifier

```text
STOP
FROZEN_INPUT_LAYOUT_REPAIR_FAILED.
```

No model calls.

## B. Legacy fictional layout breaks

```text
STOP
FROZEN_INPUT_LEGACY_COMPATIBILITY_REGRESSION.
```

No shadow.

## C. Dual layout is silently accepted

```text
STOP
FROZEN_INPUT_AMBIGUITY_SAFETY_REGRESSION.
```

## D. Old shadow state code-hash mismatch occurs

Expected for the old generation after patch.

Do NOT weaken code-hash checks.

Create a NEW shadow generation.

## E. Model-facing semantic hashes change

```text
formal_fictional_reuse_status =
NEW_FORMAL_PROOF_REQUIRED.
```

Run a full new 12-call fictional proof first.

## F. New full shadow reveals a genuine objective semantic failure

Do not proceed to policy review.

Use the smallest bounded semantic/architecture repair.

## G. New full shadow completes objectively clean

Expected:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

---

# 60. Local-only / production firewall

M12BF is LOCAL-ONLY.

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

automatic_monitoring_resume = 0.
```

Monitoring schedules remain paused.

Do not ask for GitHub push authorization.

---

# 61. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Report final ZIP SHA-256.

Do not push raw/report artifacts to GitHub.

---

# 62. Final task principle

M12BE fixed the active-universe report-count contract correctly.

The new shadow setup is internally complete:

```text
22 active names

22 packets

6 frozen contexts

all cross-manifest ticker identities PASS

18 planned calls.
```

The shadow never reached the model.

The only failure is that the shared frozen-state verifier still speaks
the old fictional serialization:

```text
stage1_prompt
stage1_prompt_sha256
```

while the shadow producer speaks the explicit nested serialization:

```text
inputs.stage1_prompt.path
inputs.stage1_prompt.sha256.
```

The correct M12BF flow is:

```text
keep both versioned frozen-state layouts valid

→ introduce one strict layout-aware frozen-input resolver

→ require one unambiguous layout per input identity

→ preserve file existence + SHA-256 verification

→ fail closed on dual/partial/unknown layout

→ keep old stopped generation non-resumable

→ prove the old M12BE nested layout offline

→ prove the completed M12BD legacy fictional layout offline

→ create a NEW shadow generation under the repaired verifier code hash

→ reuse the complete clean M12BD fictional proof
   if all model-facing hashes remain unchanged

→ run the complete monitored shadow

→ if objectively clean,
   stop semantic engineering
   and hand the complete cohort to:

DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

Do NOT:

```text
flatten the shadow producer

duplicate nested and flat path/hash fields

weaken frozen input hashes

weaken state code hashes to resume an old generation

rerun fictional proof unnecessarily

reopen active-universe count semantics

reopen Stage-2 WC grounding

reopen optional audit coverage policy

reopen context-preserving finalization

reopen decision-variance readiness policy

reopen FCF semantics

reopen financial-sector semantics

reopen configured-signal field ownership

reopen BusinessDeltaEvidenceView

reopen MarketExpectationEvidenceView

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring.
```

A frozen-state verifier must understand the versioned representation
that produced the frozen inputs,
without weakening the identity of those inputs.
