# Thesis Monitor — M12CT-R1 Directional Balance Single-Scalar Ownership & Failure-Surface Repair

## 0. Task identity

Work-instruction filename:

`20260918-m12ct-r1-directional-balance-single-scalar-ownership-and-failure-surface-repair.md`

Suggested result bundle:

`thesis-monitor-20260918-m12ct-r1-directional-balance-single-scalar-ownership-and-failure-surface-repair-report.zip`

This is a **no-model, shadow-only Pass-B ownership repair + full offline re-proof** after M12CT.

It is NOT:

- a fresh live shadow;
- a resume of M12CT;
- a selective rerun of Pass B;
- an investment-policy redesign;
- an archetype/regime redesign;
- a valuation-method redesign;
- a data-quality/security-basis redesign;
- a production Stage-2 change;
- a target-label fit.

External model calls: **0**.
Provider request attempts: **0**.
Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify before work.

### M12CT result

- ZIP SHA-256:
  `cfd673b5e65d3aa6e7991f15792b093568ad94539c6b6072c3475d356ce20a4d`
- Artifact manifest:
  271 declared payloads, 271/271 hash and size PASS.
- Generation:
  `20260918-m12cs-fresh-two-pass-20260918T003939Z-53c603c6a257`
- Execution head:
  `53c603c6a257b0a093446d5dc1b0977c7f5533fa`
- Work-instruction commit:
  `53b59679d057c61836f3082f3bed4afa20eedf55`
- Terminal:
  `M12CT_PASS_B_FAILED`

### M12CS-R1 provider-wire closure

Preserve the accepted provider dialect projection and compatibility checker from:

`M12CS_R1_PROVIDER_DIALECT_COMPATIBILITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`

Do not reopen provider dialect design except where the changed Pass-B field surface requires regenerated hashes/schemas.

## 2. M12CT execution facts to preserve

M12CT proved:

- provider-wire live compatibility in 9/9 attempted calls;
- Pass A 8/8;
- Pass A subjects 22/22;
- deterministic post-Pass-A materialization 22/22;
- actual provider schema hashes 9/9 matched the frozen provider-wire contract;
- no target leak;
- no sealed-reference access;
- no production changes.

Do not reinterpret M12CT as a broad failed run.

## 3. Exact current failure

Archived Pass-B US batch 01 raw output:

- CORZ: buy=0.62, sell=0.38
- CPNG: buy=0.45, sell=0.55
- CRCL: buy=0.38, sell=0.62

All sum to 1.0.

Current local semantic requirement:

`directional_balance.buy + directional_balance.sell == 10.0`

Stable rule:

`PB_BALANCE_SUM`

The current prompt does not make the 0-to-10 scale or sum invariant visible.

The current provider schema can bound each field but cannot express the cross-field sum.

No automatic rescaling of the archived output is authorized.

## 4. Audit downstream semantics before modifying the model surface

Inspect:

- Pass-B schema builder;
- Pass-B raw normalizer;
- semantic validator;
- final decision/materialization object;
- renderer/reporting consumers;
- post-freeze comparison;
- any tests or downstream code that consume `directional_balance`.

Prove whether the frozen semantic contract is exactly one-dimensional:

`buy in [0,10]`
`sell = 10 - buy`

If any current consumer assigns independent meaning to both buy and sell beyond the sum-10 relation, stop:

`M12CT_R1_DIRECTIONAL_BALANCE_SEMANTIC_GAP_REQUIRES_CHAT`

Do not silently collapse distinct semantics.

Expected hypothesis: two model-authored values are redundant.

## 5. Preferred ownership repair

If section 4 confirms one-dimensional semantics, change the **shadow Pass-B model surface only**.

### Model-owned raw field

Replace the model-authored two-number object with one scalar, using a clear field name such as:

`directional_buy_score`

Requirements:

- JSON number
- minimum 0
- maximum 10

The model must not author `sell`.

### Model-visible semantics

The Pass-B prompt and, where supported, field description must explicitly state:

- score range is 0 through 10;
- 0 = fully sell-leaning directional balance;
- 5 = balanced;
- 10 = fully buy-leaning directional balance;
- runtime derives the complementary sell score;
- do not normalize to 0..1.

This is contract visibility, not outcome retuning.

### Runtime projection

Use deterministic decimal-safe arithmetic:

`buy = directional_buy_score`
`sell = 10 - directional_buy_score`

Avoid binary-floating artifacts in the final canonical representation. Use a stable Decimal/string-to-Decimal or equivalent deterministic method.

Final downstream object remains:

```json
{
  "directional_balance": {
    "buy": <0..10>,
    "sell": <0..10>
  }
}
```

No production schema change.

## 6. Preserve `PB_BALANCE_SUM` as a final invariant

Do not delete the economic invariant.

Move its enforcement boundary:

- raw model schema validates only `directional_buy_score in [0,10]`;
- deterministic runtime derives sell;
- materialized/final semantic validator asserts:
  - buy in [0,10]
  - sell in [0,10]
  - buy + sell == 10 exactly under canonical decimal semantics.

Keep or version `PB_BALANCE_SUM` as the final assertion.

The model can no longer create a sum mismatch.

## 7. Archived M12CT response handling

The archived M12CT Pass-B output must remain immutable and failed.

Do not reinterpret:

`0.62/0.38 -> 6.2/3.8`

Do not migrate/rescale it.

Required replay:

- archived old raw shape under the old contract reproduces `PB_BALANCE_SUM`;
- archived old raw shape is not accepted as a valid new Pass-B model payload;
- no historical output is stitched into a future generation.

This proves the repair changes the future model contract rather than retroactively altering evidence.

## 8. Directional-balance fixtures

Add no-model fixtures covering at minimum:

Positive model scores:
- 0
- 0.62
- 3.5
- 5
- 6.2
- 10

Expected deterministic complements:
- 10
- 9.38
- 6.5
- 5
- 3.8
- 0

Negative:
- <0
- >10
- null
- string
- NaN/Infinity if parser boundary permits such values
- raw model object attempting to author a separate sell field
- old `directional_balance` raw object instead of the new scalar

Final `PB_BALANCE_SUM` must PASS for every valid materialized score.

## 9. Do not impose new granularity policy

Do not introduce:
- integer-only balance;
- 0.5-only increments;
- arbitrary rounding buckets;
- label-dependent score thresholds.

The repair is about scale/ownership, not calibration.

If existing canonical serialization already specifies precision, preserve it.

## 10. Pass-B provider-wire regeneration

Regenerate all 8 Pass-B:

- internal semantic schemas;
- provider-wire schemas;
- prompt/input contract hashes.

Pass A must remain semantically and byte/hash-identical unless a package-path-only artifact requires rebinding. Any actual Pass-A prompt/schema/policy change is forbidden.

Re-run provider-wire dialect checks:

- `uniqueItems` on wire = 0
- unsupported provider keyword = 0
- array items complete
- documented provider limits remain within bounds

All 16 total future provider schemas must PASS.

## 11. Semantic/provider freeze versioning

Because the Pass-B model surface changes, create new freeze manifests.

### Semantic contract freeze

Document:
- Pass A unchanged;
- all investment policy semantics unchanged;
- Pass B directional-balance ownership changed from redundant two-field model authoring to single scalar + deterministic complement;
- final downstream directional-balance semantics unchanged.

### Provider-wire freeze

New hashes for all changed Pass-B wire schemas.

A future live run must bind to both new freeze manifests.

## 12. Failure-surface ordering repair

Fix shadow runner/reporting only.

Current bad order:

raw semantic normalization fails
-> zero normalized rows
-> materialized-envelope validation runs
-> Pydantic empty-tuple error masks primary cause

Required order:

1. persist raw provider output;
2. provider-schema/raw JSON validation;
3. run raw semantic validation;
4. persist exact raw semantic result/errors;
5. if raw semantic failed:
   - stop immediately;
   - record the semantic rule IDs as primary blocker;
   - do not call materialized-envelope validation;
6. only on raw semantic PASS:
   - normalize/materialize;
   - validate final envelope.

Required replay:
- archived M12CT batch 01 must report primary cause `PB_BALANCE_SUM`, not empty decisions.
- synthetic materialized-envelope failure must still surface correctly when raw semantics pass.

No production transport/error taxonomy change.

## 13. Failure taxonomy

Add or preserve stable stage categories such as:

- `PASS_B_PROVIDER_SCHEMA_REJECTED_PRE_INFERENCE`
- `PASS_B_RAW_CONTRACT_FAILED`
- `PASS_B_RAW_SEMANTIC_VALIDATION_FAILED`
- `PASS_B_MATERIALIZATION_FAILED`
- `PASS_B_FINAL_SEMANTIC_VALIDATION_FAILED`

For the archived M12CT response, causal replay must be:

`PASS_B_RAW_SEMANTIC_VALIDATION_FAILED`
with rule:
`PB_BALANCE_SUM`.

The wrapper-safe exception may be reported separately but must not mask the cause.

## 14. Re-run full offline contract proof

No external calls.

Re-run:

- provider-wire dialect scan all 16;
- schema/validator/materializer parity;
- semantic uniqueness;
- typed business-quality regression;
- security valuation basis regression;
- historical failure replay;
- M12CT balance failure replay;
- Pass-A branch coverage;
- Pass-B branch coverage;
- no-model 22-subject dry materialization;
- target/price leak proof.

Update semantic rule inventory where ownership changed.

Required:
- missing upstream enforcement = 0
- uncovered semantic rule = 0
- business/security quality conflation = 0
- unsafe valuation-basis projection = 0
- model-authored deterministic sell score count = 0
- arbitrary current-price discount = 0

## 15. No-model dry execution with new Pass-B surface

Using frozen 22 contexts and synthetic valid model judgments:

Pass A synthetic valid result
-> deterministic fundamental materialization
-> Pass B synthetic output with `directional_buy_score`
-> deterministic buy/sell projection
-> tactical/entry materialization
-> final semantic validation.

Required:
- 22/22 mechanical PASS
- final balance sum invariant 22/22 PASS
- no model-authored sell
- no old two-field raw balance object accepted

Do not synthesize desired investment decisions per ticker. This is mechanics only.

## 16. Blindness

Prior production AI and independent-assistant judgments remain irrelevant to this repair.

Do not open sealed post-freeze reference material.

Archived M12CT model output may be inspected only for failure-shape replay and contract mechanics, not as a target judgment.

Target-label leak count = 0.

## 17. Production boundary

Allowed:
- shadow scripts
- shadow schema/prompt builders
- shadow validators/materializers
- shadow tests
- documentation

Expected application/runtime/config changes: 0.

If any production application/runtime file is required, stop:

`M12CT_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

## 18. Validation

Baseline submitted by M12CT before execution:

- focused: 273 passed
- frozen-contract: 182 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

M12CS-R1 previous full baseline:

- full: 4,394 passed / 63 skipped
- Treasury/KRX: 121 passed

Run after repair:

- new balance ownership tests;
- focused shadow-contract tests;
- frozen-contract suite;
- full suite;
- Treasury/KRX;
- Ruff;
- Ruff format;
- git diff --check.

No test deletion or skip inflation.

## 19. Fresh-run authorization gate

No model/provider calls in M12CT-R1.

A later fresh two-pass run may be recommended only if:

- one-dimensional balance semantics proven;
- model surface owns one 0..10 buy score only;
- deterministic sell complement proven;
- final PB_BALANCE_SUM preserved;
- archived M12CT failure caught correctly offline;
- failure masking/order repaired;
- Pass A unchanged;
- all 16 provider schemas PASS dialect checks;
- missing upstream enforcement = 0;
- branch coverage complete;
- 22/22 dry materialization PASS;
- target leak = 0;
- production changes = 0.

Future run must begin from Pass A call 1 in a new generation.

## 20. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12ct-chat-review-reconciliation.json`
- `directional-balance-consumer-semantics-audit.json`
- `directional-balance-ownership-contract.json`
- `directional-balance-raw-to-runtime-projection.json`
- `directional-balance-positive-negative-fixtures.json`
- `m12ct-balance-failure-replay.json`
- `pass-b-failure-surface-order-contract.json`
- `m12ct-failure-cause-reclassification.json`
- updated Pass-B prompt/schema drafts
- all 8 regenerated Pass-B provider-wire schemas
- all 8 unchanged/rebound Pass-A provider-wire schemas
- `all-16-provider-wire-schema-dialect-scan.json`
- updated semantic validator rule inventory
- updated schema/validator/materializer parity matrix
- semantic contract freeze manifest
- provider-wire contract freeze manifest
- historical failure replay matrix
- Pass-A branch coverage
- Pass-B branch coverage
- 22-subject dry materialization
- target-leak proof
- tests/JUnit/logs
- Ruff / format / diff-check
- safety counters
- complete blocker ledger
- program completion
- REPORT.md
- artifact manifest
- result ZIP SHA sidecar.

## 21. Terminal states

Use one:

- `M12CT_R1_DIRECTIONAL_BALANCE_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- `M12CT_R1_DIRECTIONAL_BALANCE_SEMANTIC_GAP_REQUIRES_CHAT`
- `M12CT_R1_FAILURE_SURFACE_ORDER_NOT_CLOSED`
- `M12CT_R1_CONTRACT_PARITY_NOT_CLOSED`
- `M12CT_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CT_R1_OFFLINE_REPAIR_FAILED`

No state authorizes production integration.

## 22. Hard safety

- external model calls = 0
- provider request attempts = 0
- market refresh = 0
- production runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0

Return to Chat. Do not automatically execute the next fresh shadow.
