# Thesis Monitor — R2B-R9-REV52
## Implement Selected B2 NewBuyer Contract Behind Default-OFF Shadow Path
### Exact frozen REV47 replay first
### Production behavior OFF-path must remain byte/semantic compatible
### No provider calls / no model calls / no fresh messages / no main merge

---

# 0. Task objective

REV51 selected:

`R2B_R9_REV51_OPTION_B_SELECTED_FOR_IMPLEMENTATION_DESIGN`

with variant:

`B2_EVIDENCE_BOUND_MODEL_JUDGMENT`.

REV52 implements that selected contract in repository code **behind a default-OFF shadow path**, proves deterministic schema /
validator / data-flow behavior on frozen REV47 evidence, and preserves all current production behavior when the feature is OFF.

REV52 stops before any model call.

The next separately approved task will run bounded shadow B-model proof using the frozen source/core inputs.

---

# 1. Exact base

Repository:

`sskim-ai/thesis-monitor`

Expected green `origin/main`:

`9b134350cd05c127b6dc866d34a477d95c54785c`

Hosted CI for that SHA is green.

Use the clean development worktree created by REV49:

```text
/Users/sskim/Documents/Codex/thesis-monitor-dev-main
```

Expected current branch before REV52:

`codex/r2b-r9-newbuyer-reachability-audit`

Expected HEAD:

`9b134350cd05c127b6dc866d34a477d95c54785c`

Fetch origin first.

If `origin/main` moved:

`R2B_R9_REV52_REMOTE_MAIN_MOVED_REVIEW_REQUIRED`

Do not silently move the base.

Create a new branch from the exact verified base:

`codex/r2b-r9-rev52-newbuyer-b2-shadow-implementation`

Do not use or modify the protected operating checkout:

`/Users/sskim/Codex/thesis-monitor`

---

# 2. Verify REV51 immutable result

Result:

`thesis-monitor-20261003-r2b-r9-rev51-newbuyer-repair-design-shadow-proof-report.zip`

Expected SHA-256:

`9d5aa6fbe229711e6e99ecd5cdda56b7754000fcd55f7a472febc7d64c1fbb4d`

Expected ZIP integrity:

```text
members = 48
manifest payload entries = 47
manifest self excluded = true
CRC = PASS
missing = 0
hash mismatch = 0
size mismatch = 0
extra = 0
```

Expected terminal:

`R2B_R9_REV51_OPTION_B_SELECTED_FOR_IMPLEMENTATION_DESIGN`

Expected selected variant:

`B2_EVIDENCE_BOUND_MODEL_JUDGMENT`

Expected design facts:

```text
B2 mandatory gates G1-G10 = PASS
positive controls reachable = 7/7
active-risk negative controls protected = 7/7
current production ATTRACTIVE available = 0/22
B2 positive capability = 9/22
model decisions generated in REV51 = 0
```

Do not reinterpret Option C as selected.

---

# 3. Preserve REV50/REV51 semantics

The implementation must preserve these proven boundaries.

## 3.1 Business gate

Selected B2 business eligibility:

```text
production Overall == BUY
AND current Core positive refs nonempty
AND current Core negative refs empty
AND active material business risk refs empty
```

No valuation fact may create or alter Overall/Core/A.

## 3.2 Valuation is evidence-bound judgment

New typed valuation state:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
UNRESOLVED
```

Authority:

```text
MODEL_JUDGED
SOURCE_DETERMINISTIC
NOT_RESOLVED
```

For the new B2 provider-native valuation path, economic state is generally:

`MODEL_JUDGED`

unless an already existing source-owned deterministic relation explicitly owns the relation.

Metric presence alone never proves SUPPORTIVE.

## 3.3 No fair-value fabrication

Forbidden:

```text
fPER/PER/PBR -> implied target
multiple scalar -> absolute fair value
universal multiple threshold
implied EPS reconstruction
ticker-specific rule
```

## 3.4 Risk precedence

Any active material business risk blocks the new positive B2 path.

The new B2 path does not introduce a "cheap enough to compensate deterioration" rule.

Existing AVOID semantics remain protected.

## 3.5 Timing remains independent

Typed timing:

```text
FAVORABLE_NOW
WAIT_FOR_ZONE
UNRESOLVED
```

A tactical watch zone is not fair value.

Timing cannot override active business risk.

---

# 4. Feature/path isolation

Implement a versioned shadow path, default OFF.

Preferred flag name from REV51:

`NEWBUYER_QUALIFIED_VALUATION_SHADOW`

Default:

`false`

Requirements:

- production dispatch remains old path while OFF;
- old archived v1 outputs remain valid;
- old schemas remain deserializable;
- no historical result rewrite;
- no DB migration unless absolutely required;
- no main/runtime activation in REV52.

If repository configuration conventions require another exact mechanism, use the existing feature-flag pattern and document it.

---

# 5. Production files expected to change

REV51 blueprint identified likely files:

```text
scripts/m12ds_r2_schemas.py
scripts/m12ds_r3_schemas.py
scripts/m12ds_r2_judgment_policy.py
scripts/m12ds_r3_policy.py
scripts/r2b_r2_contract.py
scripts/r2b_r5_execution.py
app/services/provider_valuation_calibration_context.py
app/services/kr_forward_valuation_context.py
app/services/detailed_stock_message_service.py
```

Do not mechanically modify all files.

Change only files actually required after tracing the current code.

For every changed production file record:
- pre-change SHA;
- reason;
- exact semantic delta.

No unrelated cleanup/refactor.

---

# 6. New B2 typed contract

Introduce a versioned NewBuyer shadow structure equivalent to:

```text
contract = newbuyer-qualified-valuation-context-v1

valuation_context:
  state:
    SUPPORTIVE | NEUTRAL | BURDENSOME | UNRESOLVED
  authority:
    MODEL_JUDGED | SOURCE_DETERMINISTIC | NOT_RESOLVED
  reason_class: closed enum
  valuation_evidence_refs: exact qualified refs
  business_evidence_refs: exact current business refs
  relation_refs: exact deterministic relation refs, if any

timing_context:
  state:
    FAVORABLE_NOW | WAIT_FOR_ZONE | UNRESOLVED
  relation
  selected
  evidence_refs
  reason
  kind = TACTICAL_NOT_FAIR_VALUE

new_buyer:
  ATTRACTIVE | WAIT | AVOID

reason_class: closed enum
reason_evidence_refs
active_risk_refs
```

No free numerical fields in the model-authored structure.

Exact financial numbers remain source/backend/renderer-owned.

---

# 7. B2 branch generation

When shadow B2 is enabled for schema generation:

## AVOID capability

If current active material business risk exists:

```text
new_buyer = AVOID
reason = ACTIVE_ADVERSE_UNCOMPENSATED
```

Require exact current active-risk refs.

Do not expose ATTRACTIVE for that subject.

## ATTRACTIVE capability

Expose ATTRACTIVE only when:

```text
selected B2 business gate PASS
qualified relevant valuation refs nonempty
active risk empty
```

The model must additionally return:

```text
valuation_context.state = SUPPORTIVE
valuation_context.authority = MODEL_JUDGED
```

with exact qualified refs.

Reason must be a new typed positive valuation-context reason; do not reuse:

`VALID_FUNDAMENTAL_DISCOUNT`

because the B2 path does not own an absolute fundamental discount.

Use a semantically scoped enum such as:

`QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE`

or a repository-consistent equivalent.

## WAIT capability

WAIT remains available through truth-bound typed reasons, not free rationale.

---

# 8. Preserve existing absolute fundamental-range path

Do not delete or weaken the existing:

```text
fundamental_valid
AND compensating_discount
→ VALID_FUNDAMENTAL_DISCOUNT
```

path.

It remains a separately source-owned absolute-range path.

The new B2 path is additional and versioned.

When both paths are present:
- no duplicate contradictory positive semantics;
- provenance must identify which path owns the decision;
- active-risk precedence remains common.

---

# 9. Qualified valuation ref set

Build an exact NewBuyer-only qualified valuation context.

US may include, where already qualified:

```text
Finnhub peTTM
Finnhub pbQuarterly
Finnhub forwardPE / fPER(FY1)
```

KR may include, where already qualified:

```text
current PER
PBR
KIS-derived current-price fPER(FY1)
```

Each ref must preserve:
- ticker/security;
- provider;
- metric;
- currency/basis when owned;
- horizon when applicable;
- qualification state;
- retrieval/as-of metadata already owned.

Do not widen source qualification.

---

# 10. PBR restriction

PBR must not independently support a non-UNRESOLVED economic state unless asset relevance is already proven by the current contract.

Do not infer asset relevance from:
- low PBR;
- archetype name alone;
- ticker identity;
- model preference.

If only PBR is available without proven relevance:
the B2 model-judgment positive path must not become available solely from that fact.

---

# 11. Forward/trailing relation restriction

Do not infer:

```text
fPER < PER => cheap
fPER < PER => earnings growth proven
```

unless an existing exact basis contract owns that inference.

The coexistence of qualified PER and fPER may be exposed as separate evidence refs.

No automatic economic relation is generated in REV52.

---

# 12. Truth-bound WAIT reasons

Implement the REV51 typed rules.

## `VALUATION_UNRESOLVED`

Allowed only when:

```text
valuation_context.state == UNRESOLVED
```

If qualified valuation facts exist, wording/semantics mean:

`valuation judgment unresolved`

not:

`valuation facts unavailable`.

## `CONFIDENCE_UNCERTAINTY`

Allowed only with:

```text
eligible confidence caution ref
OR eligible data-quality ref
OR typed insufficient business evidence
```

## `NO_CLEAN_ENTRY`

Allowed only when:

```text
timing_context.state == WAIT_FOR_ZONE
```

with exact timing relation refs.

## `ENTRY_TIMING_UNRESOLVED`

Allowed only when:

```text
timing_context.state == UNRESOLVED
```

## `PRICE_NOT_FAVORABLE`

Do not expose on the B2 path unless an existing deterministic owned price relation proves it.

For the REV51 frozen design:
treat this reason as deprecated/unavailable for the new path.

## Additional typed reasons

Implement closed reasons for:
- valuation NEUTRAL;
- valuation BURDENSOME;
- business gate not met;
- other exact states required by the selected B2 contract.

Every reason must have a backend predicate.

---

# 13. Timing contract

Implement backend-owned timing derivation, not model-invented timing.

Requirements for a resolved selected candidate:
- exact ticker/security;
- ENTRY permission;
- matching currency;
- compatible date/as-of;
- compatible price basis;
- finite ordered low/high;
- exact selected candidate identity;
- exact current price.

Then:

```text
low <= current_price <= high
→ FAVORABLE_NOW

current_price outside selected range
→ WAIT_FOR_ZONE

no valid selected candidate / incompatible basis
→ UNRESOLVED
```

The model may not override this state.

`FAVORABLE_NOW` means only:
inside the selected tactical watch zone.

It is not an execution instruction or fair-value statement.

---

# 14. Renderer isolation

Implement only the minimum renderer support necessary to safely represent a future B2 shadow result.

Do not change current production rendering while feature OFF.

New-path rendering must never collapse to an unconditional bare:

`BUY`

from valuation-context attractiveness alone.

Proposed semantics:

```text
NewBuyer fundamental attractiveness:
  ATTRACTIVE / WAIT / AVOID

Entry timing:
  FAVORABLE_NOW / WAIT_FOR_ZONE / UNRESOLVED
```

Existing user-facing exact metric values remain rendered from backend-owned valuation fields, not model prose.

No message generation is authorized in REV52.

---

# 15. Prompt/schema authority boundary

Prepare the B-only prompt/schema for later model proof.

Prompt must state:

- SUPPORTIVE/NEUTRAL/BURDENSOME is an economic model judgment;
- exact refs mandatory;
- no universal threshold;
- no fair-value/target/implied-EPS inference;
- no new numeric facts;
- no cross-security facts;
- active-risk precedence cannot be overridden;
- qualified facts may exist while judgment remains UNRESOLVED;
- timing is backend-owned and independent;
- Overall/Core/A/Holder are frozen inputs, not editable outputs.

Do not call the model in REV52.

---

# 16. Frozen REV47 offline replay

Use exact preserved REV47 source/model evidence only.

No network.

Run all 22 subjects through:

```text
feature OFF production path
feature ON B2 schema/context path
```

For feature OFF require semantic/byte-compatible behavior with frozen production replay.

For feature ON record:

```text
business gate
active risks
qualified valuation refs
timing state
allowed NewBuyer branches
reason enums
```

Expected design-level capability from REV51:

```text
B2 positive capability = 9/22
positive blind controls reachable = 7/7
active-risk controls AVOID-only = 7/7
```

Do not force exact counts if implementation discovers a justified contract mismatch; stop and explain instead of changing rules to hit the count.

---

# 17. Exact positive controls

Require branch-capability preservation for:

```text
GOOGL
MU
SNDK
000660
003690
005930
012450
```

For each:
- no active risk;
- selected B2 business gate;
- qualified relevant valuation refs;
- ATTRACTIVE branch structurally available;
- WAIT branch also available where appropriate;
- no synthetic fair-value range.

No model output is generated.

---

# 18. Exact negative controls

Require:

```text
CORZ
CPNG
HUT
RXRX
TSLA
WULF
047810
```

For every active-risk control:

```text
ATTRACTIVE branch unavailable
AVOID available
risk refs exact
timing cannot override risk
low/qualified valuation cannot suppress AVOID
```

This gate is mandatory.

---

# 19. Neutral/difficult controls

Inspect:

```text
CRCL
IBM
SKHY
TSM
WRD
005490
010120
086280
```

Expected from REV51 selected B2:

- CRCL / IBM remain outside positive B2 gate;
- SKHY / TSM / WRD remain valuation-gap WAIT;
- 086280 remains outside positive B2 gate;
- 005490 / 010120 may have B2 positive capability but timing WAIT_FOR_ZONE.

Do not encode ticker-specific outcomes.

These are consistency checks only.

---

# 20. Synthetic validator tests

At minimum:

## Positive
Business gate PASS + no risk + qualified relevant valuation + SUPPORTIVE exact refs:
`ATTRACTIVE PASS`.

## Unsupported positive
SUPPORTIVE with:
- no refs;
- unqualified refs;
- cross-security refs;
- only irrelevant PBR;
- active risk;
- hidden numeric/free-value fields;
- fair-value target prose/fields.

All reject.

## WAIT contradiction tests
Every reason rejects when its typed predicate is false.

## AVOID
Exact current active-risk refs required.

## Timing
- inside selected zone;
- below;
- above;
- boundary low;
- boundary high;
- missing candidate;
- wrong date;
- currency mismatch;
- price-basis mismatch;
- duplicate selected candidate.

---

# 21. Overall/Core/A/Holder freeze proof

On the frozen REV47 inputs, prove the B2 implementation does not alter:

```text
Core atomic claims
Core capability
A outputs
Overall direction
directional buy score
Holder stance
Holder reason/refs
```

Compute exact digests before and after shadow context construction.

Required:

`22/22 identical`

Any difference:

`R2B_R9_REV52_AUTHORITY_LEAKAGE_GAP`

---

# 22. Feature-OFF compatibility

Run all current production B schema/validator tests with the flag OFF.

Require:
- old schema shape unchanged;
- old normalized output unchanged;
- old validator outcomes unchanged;
- archived outputs still deserialize;
- existing safe absolute-range path unchanged.

Feature OFF is the rollback path.

---

# 23. No DB migration

REV52 should not require database migration.

If implementation discovers that persistent schema changes are required:

stop with:

`R2B_R9_REV52_PERSISTENCE_SCHEMA_REVIEW_REQUIRED`

Do not create an implicit migration.

Shadow B2 output may remain run-artifact JSON / in-memory typed contract until later promotion design.

---

# 24. Validation sequence

Run in this order:

1. focused new B2 unit tests;
2. REV51-equivalent synthetic/control tests;
3. current R2/R3 judgment-policy tests;
4. valuation integration tests;
5. KR forward valuation tests;
6. exact frozen REV47 22-subject replay;
7. no-network proof;
8. Ruff;
9. `git diff --check`;
10. full pytest;
11. secret scan.

No live network from tests.

---

# 25. Full pytest mandatory

Unlike REV51, REV52 changes production code.

Full pytest is mandatory.

Require:
- zero failures;
- zero errors;
- no new unexplained skip/xfail.

Record baseline/current count delta.

---

# 26. Commit discipline

After all local validation PASS:

- commit the bounded B2 shadow implementation;
- secret-scan outgoing commit;
- push feature branch only.

Do not merge main.

Do not push main.

Suggested branch:

`codex/r2b-r9-rev52-newbuyer-b2-shadow-implementation`

Record exact remote feature SHA after readback.

Hosted feature CI may be run/observed if normal branch push triggers it.

If CI runs:
record terminal result.

Do not block REV52 completion solely because a non-required feature CI remains queued unless existing repository policy requires it.

---

# 27. No model proof yet

Hard zero:

```text
provider calls = 0
model calls = 0
source recollection = 0
fresh message generation = 0
Telegram = 0
production DB write = 0
scheduler mutation = 0
deploy = 0
restart = 0
main merge = 0
main push = 0
```

Do not use the blind labels as model targets.

---

# 28. Success terminal

Use only if implementation + deterministic replay + full validation pass:

`R2B_R9_REV52_NEWBUYER_B2_SHADOW_IMPLEMENTATION_PASS_READY_FOR_MODEL_PROOF`

Required final state:

```text
feature default = OFF
production OFF behavior preserved
B2 shadow path implemented
positive controls capability = safe
negative controls protected
WAIT reasons truth-bound
timing backend-owned
Overall/Core/A/Holder unchanged
full pytest PASS
feature branch remotely preserved
main unchanged
model calls = 0
provider calls = 0
```

---

# 29. Failure/stop terminals

Use the narrowest truthful state:

```text
R2B_R9_REV52_REMOTE_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV52_REV51_INTEGRITY_GAP
R2B_R9_REV52_B2_CONTRACT_IMPLEMENTATION_GAP
R2B_R9_REV52_WAIT_REASON_TRUTH_BINDING_GAP
R2B_R9_REV52_TIMING_CONTRACT_GAP
R2B_R9_REV52_NEGATIVE_CONTROL_SAFETY_GAP
R2B_R9_REV52_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV52_FEATURE_OFF_COMPATIBILITY_GAP
R2B_R9_REV52_PERSISTENCE_SCHEMA_REVIEW_REQUIRED
R2B_R9_REV52_FULL_VALIDATION_GAP
R2B_R9_REV52_FEATURE_PUSH_GAP
```

---

# 30. Result bundle

Create:

`thesis-monitor-20261003-r2b-r9-rev52-newbuyer-b2-shadow-implementation-report.zip`

+ `.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV51-integrity.json
repository-identities.json
implementation-diff.json
feature-flag-contract.json
b2-schema-contract.json
b2-validator-contract.json
wait-reason-contract.json
timing-contract.json
valuation-context-dataflow.json
feature-off-compatibility.json
rev47-22-shadow-replay.json
positive-control-results.json
negative-control-results.json
neutral-control-results.json
authority-freeze-digests.json
synthetic-validator-results.json
focused-validation.json
full-validation.json
secret-scan.json
feature-push-receipt.json
protected-state.json
bundle-manifest.json
```

No credentials.

---

# 31. Next task after PASS

Do not run automatically.

Next task:

> REV53 — bounded frozen-REV47 B2 shadow model proof.

That task will:
- keep provider calls at zero;
- use exact frozen Core/A/valuation context;
- call only the new B2 shadow B-model path;
- preserve original production outputs;
- compare model behavior against the pre-sealed blind review only after outputs are sealed;
- test whether the model overuses UNRESOLVED/NEUTRAL or produces unsupported SUPPORTIVE;
- require 7/7 negative-control safety;
- decide whether B2 is behaviorally ready for fresh live proof.

No production enablement or main merge until that model proof passes.

---

# 32. Final principle

REV52 changes reachability, not investment labels.

A positive branch may now exist when:

```text
business gate is already positive
+
no active risk
+
qualified valuation evidence exists
+
future B model explicitly judges that valuation context SUPPORTIVE
```

but the backend still owns:
- evidence eligibility;
- risk precedence;
- timing;
- reason truth-binding;
- prohibition on fair-value fabrication.

The model owns only the scoped economic judgment, not the source facts and not the rest of the investment architecture.
