# Thesis Monitor — R2B-R9-REV54
## Provider-Wire JSON-Schema Const Typing / Parity Repair
### Repair the exact REV53 HTTP 400 schema defect
### Re-project and re-freeze all 22 B2 requests
### No model proof / no provider-source calls / no main merge

---

# 0. Task objective

REV53 did **not** test B2 model behavior.

The first and only live B2 model invocation (`CORZ`) failed before any model judgment with:

```text
HTTP 400
invalid_json_schema
schema must have a 'type' key
path:
properties.new_buyer_shadow.anyOf[0].properties.contract
```

The exact failing wire node was:

```json
{"const":"newbuyer-qualified-valuation-context-v1"}
```

without an explicit JSON-Schema `type`.

The same const-only wire pattern exists in all 22 frozen REV52/REV53 wire schemas.

REV54 must:

1. repair provider-wire schema projection generically and fail-closed;
2. strengthen provider-dialect scanning so the exact defect cannot pass offline qualification again;
3. preserve the richer local B2 semantic schema and validator unchanged;
4. regenerate all 22 provider-wire schemas from the same frozen REV47/B2 inputs;
5. prove only provider-wire representation changed, not investment semantics;
6. create a new immutable 22-request freeze for the next model-proof task;
7. run full validation and Hosted feature CI.

REV54 must **not** perform another model proof.

---

# 1. Exact repository identities

Green `origin/main` expected:

`9b134350cd05c127b6dc866d34a477d95c54785c`

REV52 B2 feature branch:

`codex/r2b-r9-rev52-newbuyer-b2-shadow-implementation`

Expected exact remote feature SHA:

`53673bac5f36c9cd833281e612b1cf70bf3e22c4`

Expected REV52 feature Hosted CI:

`success`

Use the clean development worktree and create a child repair branch from the exact REV52 feature SHA:

`codex/r2b-r9-rev54-provider-wire-const-typing`

Do not base this repair on `main`, because the B2 implementation is not on `main`.

At start:

```text
fetch origin
verify origin/main exact
verify remote REV52 feature exact
verify worktree clean
```

If either expected ref moved unexpectedly:

`R2B_R9_REV54_REPOSITORY_IDENTITY_GAP`

No rebase.
No force operations.

---

# 2. Verify REV53 immutable result

Result ZIP:

`thesis-monitor-20261003-r2b-r9-rev53-b2-frozen-shadow-model-proof-report.zip`

Expected SHA-256:

`8f4d12a3ad07d161a2e9e362f92ccc2f8e5152d09846f3604b96b5d8f4b85b1e`

Expected ZIP integrity:

```text
members = 100
manifest payload entries = 99
manifest self excluded = true
CRC = PASS
missing = 0
hash mismatch = 0
size mismatch = 0
extra = 0
```

Expected final terminal:

`R2B_R9_REV53_IMPLEMENTATION_REPAIR_REQUIRED`

Expected runtime facts:

```text
logical requests expected = 22
logical dispatched = 1
CLI attempts = 1
accepted outputs = 0
not dispatched = 21
HTTP status = 400
provider error code = invalid_json_schema
first request elapsed = 4.332 sec
model judgment outputs = 0
```

Expected model-result partial ZIP SHA:

`dae1c150cf7a836fae61f52491459d932f91d5b972c483e2cc80127f7711e08d`

Do not reinterpret REV53 as WAIT bias, overgeneralization, or negative-control PASS.

Behavior was not evaluated.

---

# 3. Exact root cause to reproduce first

Before editing, reproduce offline from exact REV52 feature code:

```text
scripts/newbuyer_b2_contract.py
scripts/m12cs_r1_provider_schema.py
```

Known implementation:

`newbuyer_b2_contract.output_schema()` emits many const-only semantic leaves, including:

```text
contract
input_sha256
decision_path
valuation_context.state
valuation_context.authority
valuation_context.reason_class
valuation_context.relation_refs
timing_context
new_buyer
reason_class
active_risk_refs
```

Known provider projector:

`project_provider_wire_schema()`

currently preserves generic `const` nodes unchanged except for the unrelated `uniqueItems` removal / shared-enum projection.

Known provider scanner:

`scan_provider_structured_output_schema()`

validates types **only if `type` is already present**, so const-only leaves can pass the scanner.

First produce:

`rev53-schema-defect-reproduction.json`

containing:
- exact failing CORZ internal node;
- exact failing CORZ wire node;
- all 22 affected request/schema SHAs;
- count/path inventory of all const-only wire nodes;
- proof old scanner returned PASS despite the defect.

Do not edit before this receipt exists.

---

# 4. Repair layer

The preferred repair layer is the provider-wire dialect projection/scanner, not the local B2 semantic contract.

Reason:

- the local closed schema intentionally uses exact `const` semantics;
- the local validator owns exact semantic equality;
- provider projection already exists to lower richer local constraints into the provider-supported wire dialect;
- provider-specific typing belongs at that boundary.

Do not rewrite all B2 const nodes manually unless the generic projector cannot safely represent them.

Do not weaken the local semantic validator.

---

# 5. Generic const type inference

Implement one canonical helper for provider projection.

For every schema node containing `const`, infer JSON type from the const value with exact Python/JSON semantics.

Required primitive mapping:

```text
str   -> string
bool  -> boolean
int   -> integer       # bool must be handled before int
float -> number
None  -> null
```

Reject:
- non-finite numeric const;
- unsupported Python-only value;
- ambiguous/unserializable value.

If an existing explicit `type` conflicts with the inferred const type:

fail closed:

`provider_const_type_mismatch`

Do not silently overwrite a conflicting explicit type.

---

# 6. Primitive const projection

For primitive constants the provider wire schema must explicitly contain both:

```json
{
  "type": "<inferred-type>",
  "const": <value>
}
```

Preserve other provider-supported constraints only when semantically compatible.

Example:

```json
{"const":"WAIT"}
```

must project to:

```json
{"type":"string","const":"WAIT"}
```

The internal semantic schema remains unchanged.

---

# 7. Object const lowering

Do not rely on a bare provider-wire:

```json
{"type":"object","const":{...}}
```

as the primary generic representation.

Lower a mapping constant to a strict typed object schema:

```text
type = object
properties = one property per exact object key
required = all exact keys
additionalProperties = false
```

Recursively project each child value as an exact typed const/lowered const structure.

The local validator still owns exact semantic equality.

Required invariants:

- no missing object key can pass provider wire;
- no extra object key can pass provider wire;
- nested scalar values retain exact const;
- nested arrays use the array lowering in Section 8.

Record the lowered path in the projection receipt.

---

# 8. Array const lowering

Provider-wire constant arrays must be lowered without weakening local exact semantics.

For current B2 schemas, first inventory every array-valued const and classify element shape:

```text
EMPTY
HOMOGENEOUS_STRING
HOMOGENEOUS_INTEGER
HOMOGENEOUS_NUMBER
HOMOGENEOUS_BOOLEAN
HOMOGENEOUS_OBJECT
OTHER
```

Expected B2 exact-ref arrays are string arrays.

For homogeneous primitive arrays, provider wire must include:

```text
type = array
items = explicit typed item schema
minItems = exact length
maxItems = exact length
```

When every element comes from a known finite exact set, item enum/const typing may narrow it further.

Because exact ordering/set equality may be richer than the provider dialect, the existing local semantic validator remains the final exact owner.

For empty arrays:
- use an explicit typed array representation accepted by the provider dialect;
- do not emit an untyped `items: {}` node;
- if no safe item type can be derived from the owning logical field, use owning-field metadata or a dedicated lowering rule;
- otherwise fail closed rather than inventing an arbitrary item type.

For heterogeneous/complex arrays not safely lowerable:

`R2B_R9_REV54_COMPLEX_CONST_ARRAY_REVIEW_REQUIRED`

Do not weaken them to unconstrained arrays.

---

# 9. Exact B2 empty-array handling

The B2 local schema contains semantically typed ref-array fields that may have `const=[]`.

For these fields, the logical item type is known to be `string`, including where applicable:

```text
valuation_evidence_refs
business_evidence_refs
relation_refs
reason_evidence_refs
active_risk_refs
timing_context.evidence_refs
```

Provider projection may use:

```json
{
  "type":"array",
  "items":{"type":"string"},
  "minItems":0,
  "maxItems":0
}
```

for the wire representation of an exact empty ref-array.

Local validator continues to enforce the original `const=[]`.

Do not generalize this string-array rule to unrelated fields.

---

# 10. Scanner must detect missing type on const

Strengthen:

`scan_provider_structured_output_schema()`

so every provider-wire schema node with `const` is checked for:

```text
explicit type present
explicit type allowed
const value compatible with type
```

Add explicit error classes such as:

```text
const_type_missing:<path>
const_type_mismatch:<path>
const_nonfinite_number:<path>
```

The old REV53 CORZ wire schema must now scan:

`FAIL`

with at least:

`const_type_missing` at the exact `contract` path.

The newly projected schema must scan:

`PASS`.

---

# 11. Scanner must validate const-lowered arrays/objects

Add coverage so the provider scanner cannot PASS:

```text
properties without object type
object without required exact properties
object with additionalProperties != false
array without items
array const/lowered shape with invalid item typing
nested anyOf branch with untyped const
$defs child with untyped const
```

Walk every schema-bearing location:

```text
properties
$defs
items
anyOf
```

Do not inspect arbitrary JSON payload objects as schemas.

---

# 12. Provider-wire semantic parity

For all 22 frozen B2 subjects prove:

```text
internal semantic schema SHA unchanged from REV52
prompt SHA unchanged from REV52
frozen subject/input SHA unchanged from REV52
business gate unchanged
active-risk set unchanged
qualified valuation refs unchanged
backend timing unchanged
allowed local B2 branches unchanged
```

Only these may change:

```text
provider-wire schema SHA
provider-dialect projection receipt
new frozen request SHA resulting from wire-schema bytes
```

No investment semantic may change.

---

# 13. Local exact-validator preservation

The local B2 validator must continue to validate against the original richer local schema.

Do not replace local validation with the lowered provider-wire schema.

Required negative controls remain exact:

- duplicate refs rejected;
- wrong refs rejected;
- wrong stance rejected;
- wrong reason rejected;
- active-risk violations rejected;
- timing override rejected;
- forbidden PBR-only anchor rejected;
- fair-value fabrication rejected where current validator owns the restriction.

---

# 14. Provider dialect fixture from exact HTTP 400

Add a regression fixture from REV53:

```text
old CORZ provider wire schema
```

No network.

Test:

1. old scanner behavior is reproduced/documented;
2. strengthened scanner rejects old schema;
3. new projection generates typed contract leaf;
4. new scanner passes new schema;
5. local semantic schema remains unchanged.

The provider error text itself may be stored sanitized as:

```text
invalid_json_schema:
schema must have a 'type' key
```

No secret/provider request ID needed.

---

# 15. Primitive const matrix tests

Add direct projector/scanner tests for:

```text
string
boolean
integer
number
null
```

Require:
- type inferred correctly;
- explicit matching type preserved;
- explicit conflicting type rejected;
- bool not misclassified as integer;
- nonfinite number rejected.

---

# 16. Object const tests

Test at minimum:

```json
{
  "const": {
    "state":"WAIT_FOR_ZONE",
    "selected":"candidate-x",
    "evidence_refs":["ref-a","ref-b"]
  }
}
```

Projected wire must be strict typed object shape.

Test:
- all keys required;
- no extra properties;
- nested string const typed;
- nested array typed;
- scanner PASS;
- local exact validator still rejects changed object value/order/refs according to local semantics.

---

# 17. Array const tests

Test:

```text
[]
["a"]
["a","b"]
```

for ref-array logical fields.

Require:
- explicit `type=array`;
- explicit typed `items`;
- exact length bounds;
- no untyped item schema;
- scanner PASS.

Test unsupported complex/heterogeneous arrays fail closed unless an exact supported lowering is intentionally implemented.

---

# 18. All-22 exact provider-wire audit

Regenerate provider wire for the frozen 22 B2 subjects.

For every subject record:

```text
ticker
internal schema SHA
old provider-wire schema SHA
new provider-wire schema SHA
old const-only node count
new const-only-without-type count
object const lowered count
array const lowered count
primitive const typed count
scanner status
scanner error count
```

Required:

```text
22/22 new scanner PASS
const-only-without-type = 0 for every subject
```

If any subject fails:

`R2B_R9_REV54_ALL22_PROVIDER_WIRE_PARITY_GAP`

No model call.

---

# 19. Global regression across existing structured-output schemas

Because `project_provider_wire_schema()` is shared infrastructure, run a bounded inventory over all current repository
callers/fixtures of that projector.

For every representative production schema family prove:
- projection still succeeds or fails with an explicit reason;
- semantic local schema SHA unchanged;
- no unexpected wire-shape weakening;
- previous `uniqueItems` local-owner behavior unchanged;
- shared enum `$defs` behavior unchanged.

At minimum run existing:

`tests/test_m12cs_r1_provider_schema.py`

plus all direct callers found by repository search.

Any unrelated schema regression:

`R2B_R9_REV54_SHARED_PROJECTOR_REGRESSION_GAP`

---

# 20. Request-schema rejection classification

REV53 runtime initially labeled the nonzero process result:

`PROCESS_NONZERO_UNCLASSIFIED`

even though raw provider output later proved:

```text
HTTP 400
invalid_json_schema
```

For the **next frozen proof controller**, add a deterministic task/shadow classifier:

```text
REQUEST_SCHEMA_PROVIDER_REJECTED
retry_eligible = false
```

when raw error evidence proves provider-side invalid schema.

This classifier may live in the reusable shadow transport layer only if that is already the appropriate owner.

Do not alter production investment semantics.

Do not classify:
- auth failure;
- timeout;
- 429/5xx;
- ordinary model output schema mismatch

as request-schema rejection.

Add exact tests.

---

# 21. No live provider/model call in REV54

Hard zero:

```text
B2 model calls = 0
other model calls = 0
provider source calls = 0
source recollection = 0
message generation = 0
Telegram = 0
production DB write = 0
scheduler mutation = 0
deploy = 0
restart = 0
main merge = 0
main push = 0
```

REV54 is an offline provider-wire repair and freeze task.

Do not use a live model call merely to test schema acceptance.

The next task performs controlled acceptance/model proof.

---

# 22. New immutable 22-request freeze

After all tests pass, regenerate the frozen B2 requests from the same REV52 subject/prompt inputs using the repaired
provider-wire projection.

Create a new artifact:

`rev54-b2-shadow-requests.json`

containing exactly 22 ticker-keyed requests.

For every ticker record:

```text
old REV52 request SHA
new REV54 request SHA
prompt SHA old/new
subject/input SHA old/new
internal semantic schema SHA old/new
provider-wire schema SHA old/new
```

Required:

```text
prompt = IDENTICAL
subject/input = IDENTICAL
internal semantic schema = IDENTICAL
provider wire = CHANGED_ONLY_AS_REQUIRED_BY_DIALECT_REPAIR
```

No previous frozen request is overwritten.

---

# 23. Next-proof execution artifact

Freeze, but do not execute, a new REV55 proof controller/input package with:

```text
exact 22 REV54 requests
model = gpt-5.6-sol
reasoning effort = xhigh
timeout = 600 sec
max retries = 2
physical attempt cap = 30
raw-first capture
REQUEST_SCHEMA_PROVIDER_REJECTED classifier
fail-closed first smoke policy
```

The first future live call should be one smoke subject before dispatching the remaining 21.

Suggested smoke subject:

`CORZ`

because it is the exact subject that reproduced the provider rejection.

The controller must stop after smoke if provider request schema is rejected again.

Do not execute it in REV54.

---

# 24. Feature-OFF / B2 semantics freeze

Prove REV54 does not alter:

```text
feature default = OFF
old production NewBuyer path
B2 business gate
B2 qualified valuation facts
B2 positive capability 9/22
positive controls 7/7
active-risk negative controls 7/7
Core/A/Overall/Holder freeze
timing distribution
```

Expected frozen timing remains:

```text
UNRESOLVED = 14
WAIT_FOR_ZONE = 6
FAVORABLE_NOW = 2
```

Any semantic drift:

`R2B_R9_REV54_B2_SEMANTIC_DRIFT`

---

# 25. Validation sequence

Run:

1. exact REV53 defect reproduction;
2. primitive const tests;
3. object const tests;
4. array const tests;
5. exact CORZ old/new regression;
6. all-22 B2 wire audit;
7. shared projector regression;
8. B2 feature-OFF compatibility;
9. B2 control/replay tests;
10. request-schema rejection classifier tests;
11. no-network guard;
12. Ruff;
13. `git diff --check`;
14. full pytest;
15. secret scan.

Full pytest is mandatory because shared provider-schema infrastructure changes.

---

# 26. Hosted feature CI

After local full PASS:

1. commit bounded repair;
2. secret-scan outgoing commit;
3. push feature branch only;
4. read back exact feature SHA;
5. observe Hosted feature CI to terminal state.

Do not merge `main`.

Hosted CI must be:

`completed / success`

for REV54 PASS.

No force push.

Suggested branch:

`codex/r2b-r9-rev54-provider-wire-const-typing`

---

# 27. Success terminal

Use only if all offline/provider-wire/CI gates pass:

`R2B_R9_REV54_PROVIDER_WIRE_CONST_TYPING_PARITY_PASS_READY_FOR_REPROOF`

Required final statements:

```text
REV53 root cause reproduced = true
old CORZ wire scanner now FAIL = true
new CORZ wire scanner PASS = true
new all22 wire scanner PASS = 22/22
const-without-type = 0/22
B2 semantic capability unchanged
feature default OFF
full pytest PASS
Hosted feature CI PASS
new 22-request freeze sealed
model calls = 0
provider source calls = 0
main unchanged
```

---

# 28. Failure/stop terminals

Use the narrowest truthful state:

```text
R2B_R9_REV54_REPOSITORY_IDENTITY_GAP
R2B_R9_REV54_REV53_INTEGRITY_GAP
R2B_R9_REV54_ROOT_CAUSE_REPRODUCTION_GAP
R2B_R9_REV54_CONST_TYPE_PROJECTION_GAP
R2B_R9_REV54_COMPLEX_CONST_ARRAY_REVIEW_REQUIRED
R2B_R9_REV54_ALL22_PROVIDER_WIRE_PARITY_GAP
R2B_R9_REV54_SHARED_PROJECTOR_REGRESSION_GAP
R2B_R9_REV54_REQUEST_SCHEMA_CLASSIFIER_GAP
R2B_R9_REV54_B2_SEMANTIC_DRIFT
R2B_R9_REV54_FULL_VALIDATION_GAP
R2B_R9_REV54_FEATURE_CI_GAP
R2B_R9_REV54_FREEZE_GAP
```

---

# 29. Result bundle

Create:

`thesis-monitor-20261003-r2b-r9-rev54-provider-wire-const-typing-parity-report.zip`

+ `.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV53-integrity.json
repository-identities.json
rev53-schema-defect-reproduction.json
const-node-inventory-old.json
const-projection-contract.json
primitive-const-tests.json
object-const-tests.json
array-const-tests.json
corz-old-new-wire-comparison.json
all22-provider-wire-audit.json
shared-projector-regression.json
request-schema-rejection-classifier.json
b2-semantic-freeze.json
feature-off-compatibility.json
focused-validation.json
full-validation.json
secret-scan.json
rev54-b2-shadow-requests.json
rev54-request-freeze-receipt.json
rev55-controller-freeze.json
feature-push-receipt.json
hosted-feature-ci.json
protected-state.json
bundle-manifest.json
```

No credentials.

---

# 30. Next task after PASS

Do not execute automatically.

Next task:

> REV55 — resume the frozen B2 model proof using the exact REV54 request freeze.

REV55 should:

1. perform one live CORZ schema/model smoke;
2. require accepted wire + local B2 output;
3. only then dispatch the remaining 21;
4. preserve raw-first capture;
5. seal all outputs before blind reveal;
6. run the same discrimination / negative-control / post-seal blind comparison planned in REV53.

Do not regenerate source, Core, A, valuation context, or prompts.

---

# 31. Final principle

REV53 failed before the model had any chance to make an investment judgment.

Therefore the correct repair is not:
- prompt tuning;
- changing B2 business/valuation logic;
- retrying the same invalid schema.

It is:

```text
preserve local semantic schema
→ correctly lower it into provider wire dialect
→ make the scanner detect the exact provider requirement offline
→ freeze new request bytes
→ only then re-run the behavioral proof
```

Provider-wire compatibility is a transport/schema concern, not an investment-policy concern.
