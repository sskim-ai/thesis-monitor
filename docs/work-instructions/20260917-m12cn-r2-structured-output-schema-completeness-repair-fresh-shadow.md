# Thesis Monitor — M12CN-R2 Structured Output Schema Completeness Repair + Fresh 8-Call Policy Shadow

## 0. Task identity

Work-instruction filename:

`20260917-m12cn-r2-structured-output-schema-completeness-repair-fresh-shadow.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cn-r2-structured-output-schema-completeness-repair-fresh-shadow-report.zip`

This is a **shadow-only response-format schema repair + wholly fresh 8-call policy calibration rerun**.

It is NOT:

- a production Stage-2 contract change;
- a production investment-policy integration;
- an archetype-policy redesign;
- a WAIT/tactical semantic redesign;
- a valuation-method expansion;
- a model retry of the failed R1 generation;
- a deployment/scheduler/notification/broker/persistence task.

Production application/runtime/config behavior change count must remain **0**.

## 1. Exact source state

Verify before work:

### M12CN-R1 result

- Result ZIP SHA-256:
  `37d928236611b14c4b0baddcb24bb3a5140520a56e095bb62197629b52681218`
- Result manifest: 78 declared payloads; 78/78 hash/size PASS.
- R1 terminal:
  `M12CN_R1_POLICY_CALIBRATION_SHADOW_FAILED`
- Required runtime base:
  `831890d1bf0dff303f67a6e0de1403ad3221b5d8`
- R1 harness commit:
  `bfecbc3f14de4d98b39279f8a09f459deb72b7d7`
- R1 generation:
  `20260917-m12cn-r1-policy-shadow-20260917T095249Z-bfecbc3f14de`

Use the packaged immutable M12CM shadow input and policy principles. Do not refresh market/fundamental data.

## 2. Exact R1 blocker

R1 attempted only US batch 01.

The high-level helper raised:

`CodexTransportError: OTHER_TRANSPORT_FAILURE:attempts=1`

However the raw provider response is authoritative:

```text
type = invalid_request_error
code = invalid_json_schema
message = Invalid schema for response_format 'codex_output_schema':
          In context=('properties', 'evidence_refs'), array schema missing items.
HTTP status = 400
```

Classify the R1 event as:

`SCHEMA_REJECTED_PRE_INFERENCE`

Do not classify it as transient network failure, timeout, model refusal, quota/rate-limit failure, or semantic model-output failure.

Counts entering R2:

- wrapper attempt: 1;
- actual accepted inference: 0;
- model output: 0;
- evaluated subjects: 0.

No same-generation retry is authorized or useful.

## 3. Independently confirmed invalid schema nodes

All eight R1 exported response schemas contain exactly the same six arrays without `items`:

```text
$defs.NonWaitEntryBand.properties.evidence_refs

$defs.NonWaitEntryRange.properties.assumptions
$defs.NonWaitEntryRange.properties.re_evaluate_conditions
$defs.NonWaitEntryRange.properties.technical_basis_refs
$defs.NonWaitEntryRange.properties.unresolved_inputs
$defs.NonWaitEntryRange.properties.valuation_basis_refs
```

They currently resemble:

```json
{
  "type": "array",
  "minItems": 0,
  "maxItems": 0
}
```

This is not accepted by the provider response-format schema contract.

The failure appeared first at `evidence_refs`; do not assume the other five are acceptable merely because provider validation stopped at the first offending path.

## 4. Repair boundary

Inspect the exact R1 shadow schema owner first.

Expected owner is the R1 shadow harness/schema construction path, likely within the M12CN shadow script/tests. Repair the canonical constructor, not eight exported JSON files individually.

Required behavior:

- every schema object with `type: "array"` has an explicit `items`;
- zero-length arrays remain zero-length through `minItems=0, maxItems=0`;
- for zero-length string/ref lists, preserve an appropriate item schema such as the existing string/ref item contract;
- do not relax `maxItems=0`;
- do not make non-WAIT entry fields model-populatable;
- do not add arbitrary `additionalProperties`;
- do not weaken enum/ref restrictions;
- do not change production Stage-2 v4.

Expected application source changes: **0**.

If closing this requires an application/runtime file rather than shadow harness/test code, stop with the exact dependency and return to Chat.

## 5. Preserve the R1 policy contract unchanged

Freeze these semantics.

### WAIT

`new_buyer = WAIT`:

- parent status: `ENTRY_RANGE_RESOLVED | ENTRY_RANGE_UNRESOLVED`;
- fundamental component: `RESOLVED | UNRESOLVED`;
- tactical component: `RESOLVED | UNRESOLVED`;
- `NOT_APPLICABLE` forbidden for all three.

If fundamental is UNRESOLVED:

- parent is `ENTRY_RANGE_UNRESOLVED`;
- preferred low/high = null;
- distance = null;
- method/combination remain unresolved;
- tactical RESOLVED may remain watch/support context only.

If tactical cannot be safely selected:

- tactical = UNRESOLVED;
- no invented candidate/price/ref;
- preserve the exact unresolved dependency.

### non-WAIT

`new_buyer in {ATTRACTIVE, AVOID}`:

- parent/fundamental/tactical = NOT_APPLICABLE;
- entry numeric fields = null;
- empty array fields remain empty;
- schema completeness does not make those fields semantically usable.

No change to archetypes, three-axis policy, data-quality policy, or valuation methods.

## 6. Mandatory response-format schema preflight

The old `shadow-schema-structural-proof` checked policy structure but did not prove provider-compatible JSON-schema completeness.

Keep that proof and add a separate recursive response-format preflight.

For each of all eight generated schemas, recursively inspect every node.

At minimum:

1. every `type: "array"` has `items`;
2. every `$defs` branch is traversed;
3. every `properties` subtree is traversed;
4. every `anyOf` / `oneOf` / `allOf` branch is traversed;
5. intended strict object constraints remain present where required;
6. required/property consistency is checked for the generated strict-output objects;
7. no schema node is silently dropped during dynamic per-batch enum/ref injection.

Required negative control:

- feed one exact R1 schema to the new checker;
- it must FAIL and report all six missing-item JSON paths, not only the first.

Required positive control:

- repaired schema must report zero array-without-items paths.

Do this for all 8 schemas before any inference.

If any schema fails local preflight:

- model calls = 0;
- return `M12CN_R2_SCHEMA_PREFLIGHT_FAILED`;
- do not call the provider hoping to discover the next schema error.

## 7. Provider-error classification in the shadow harness

Do not modify the production transport taxonomy in this task.

In the shadow runner/reporting layer only, preserve the raw provider response and distinguish:

- `SCHEMA_REJECTED_PRE_INFERENCE`
- `TRANSPORT_TIMEOUT`
- `NETWORK_FAILURE`
- `RATE_LIMIT_OR_QUOTA`
- `MODEL_OUTPUT_CONTRACT_FAILURE`
- other actual documented categories.

At minimum, R1's archived error must replay-classify as:

`SCHEMA_REJECTED_PRE_INFERENCE`

Do not report a provider 400 `invalid_json_schema` as `OTHER_TRANSPORT_FAILURE` in the final causal blocker ledger.

This reporting fix must not cause retries.

## 8. Static controls before inference

Before any model call:

1. package/source/base integrity PASS;
2. R1 archived schema fails new completeness checker at the six exact paths;
3. repaired schemas pass completeness checker 8/8;
4. WAIT/non-WAIT structural branch proof passes 8/8;
5. R1 semantic fixtures still pass:
   - WAIT + tactical NOT_APPLICABLE = FAIL;
   - WAIT + tactical UNRESOLVED = PASS when correctly specified;
   - WAIT + resolved tactical + unresolved fundamental = parent unresolved;
   - non-WAIT + NOT_APPLICABLE components = PASS;
6. arbitrary current-price discount remains forbidden;
7. generic renamed-identity controls remain equivalent;
8. target-label leak scan PASS;
9. production runtime/config tree unchanged.

Freeze shadow code, prompt template, schema builder, validator and generated 8 input sets before call 1.

## 9. Blindness

Before all 22 R2 shadow outputs are frozen, do not semantically open/use as model-visible material:

- independent assistant judgment;
- M12CM production AI verdicts;
- prior three-way comparison;
- any M12CN/R1 partial model labels.

R1 contains **no valid model output**, so there is nothing to reuse.

Allowed pre-freeze R1 evidence:

- raw invalid-schema response;
- exported invalid schemas;
- static policy contracts;
- safe frozen M12CM input;
- generic fixture results.

Target-label leak count must be 0.

## 10. Fresh 8-call execution

After preflight PASS, create a wholly new generation ID.

Run exactly:

- US 5 Stage-2-style shadow batches;
- KR 3 Stage-2-style shadow batches;

using the frozen M12CM facts and accepted Fundamental Core.

Fundamental Core model calls = 0.

For each call:

- one attempt;
- no retry;
- no repair model;
- no judge;
- no fallback model;
- no selective or per-ticker rerun;
- no previous shadow output reuse;
- no cross-generation stitching;
- no post-call hotfix.

First hard failure stops subsequent calls.

Preserve raw response, schema, prompt, ref catalog, context, transport log and exact gate.

A provider-side schema rejection after local preflight is a hard failure and requires exact new schema/error evidence; do not patch and resume.

## 11. PASS requirements

`M12CN_R2_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`

requires all of:

- archived R1 invalid schema detected locally with six exact paths;
- repaired schemas complete 8/8;
- semantic branch proof 8/8;
- provider schema rejection count 0;
- shadow calls started/completed/accepted = 8/8/8;
- subjects semantically accepted = 22/22;
- target-label leaks = 0;
- arbitrary-discount count = 0;
- WAIT tactical NOT_APPLICABLE count = 0;
- production runtime/config changes = 0;
- all outputs frozen before references are opened;
- exactly one post-freeze descriptive comparison;
- no inference after comparison.

Agreement with prior human/AI labels remains descriptive, never a PASS target.

## 12. Entry-range coverage reporting

For the complete 22-subject output, report:

- archetype distribution;
- overall/new-buyer/holder distributions;
- BUY/WAIT/HOLDABLE count;
- WAIT subject count;
- entry parent resolved/unresolved;
- fundamental resolved/unresolved;
- tactical resolved/unresolved;
- tactical candidate available vs selected;
- fundamental valuation method coverage;
- unresolved reason frequencies;
- holder REVIEW reasons;
- data-quality effect distribution.

Do not create new valuation sources in this task.

If fundamental coverage remains too sparse, record the measured gap for Chat. Do not manufacture price bands.

## 13. Post-freeze comparison

Only after the complete fresh R2 output hash freeze, perform exactly one descriptive comparison of:

1. M12CM production AI;
2. independent assistant blind judgment;
3. M12CN-R2 shadow.

Report per-axis agreement and key qualitative changes.

No second inference, prompt edit, threshold retune or schema edit after reveal.

## 14. Safety

Throughout:

- production policy changes = 0;
- production Stage-2 changes = 0;
- production sends/intents/DB writes = 0;
- scheduler changes = 0;
- broker read/order/modify/cancel = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0;
- market refresh = 0.

Return to Chat even after PASS.

## 15. Required artifacts

At minimum:

- `source-base-integrity.json`
- `r1-provider-schema-error-reclassification.json`
- `r1-invalid-schema-completeness-scan.json`
- `response-format-schema-completeness-contract.json`
- `schema-completeness-negative-positive-controls.json`
- `shadow-schema-version-and-diff.json`
- `shadow-schema-structural-proof.json`
- all eight repaired schemas
- exact shadow prompt/schema builder sources and hashes
- `generic-policy-control-matrix.json`
- `entry-range-catalog-coverage.json`
- `blindness-and-target-leak-proof.json`
- `shadow-call-ledger.json`
- all executed model inputs/raw outputs/transport logs
- `shadow-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `entry-range-coverage-and-methods.json`
- `holder-review-reason-analysis.json`
- `valuation-vs-overall-direction-analysis.json`
- post-freeze three-way JSON/MD comparison
- test commands/logs/JUnit
- Ruff / git diff --check
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- `artifact-manifest.json`
- external result ZIP SHA sidecar.

## 16. Validation baseline

R1 submitted baseline:

- focused: 68 passed;
- frozen-contract: 14 passed;
- full: 4,189 passed / 63 skipped;
- Treasury/KRX: 121 passed;
- Ruff: PASS;
- git diff --check: PASS.

No test deletion or skip inflation.

## 17. Terminal states

Use one of:

- `M12CN_R2_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`
- `M12CN_R2_SCHEMA_PREFLIGHT_FAILED`
- `M12CN_R2_PROVIDER_SCHEMA_REJECTED_AFTER_PREFLIGHT`
- `M12CN_R2_POLICY_CALIBRATION_SHADOW_FAILED`
- `M12CN_R2_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration or deployment.
