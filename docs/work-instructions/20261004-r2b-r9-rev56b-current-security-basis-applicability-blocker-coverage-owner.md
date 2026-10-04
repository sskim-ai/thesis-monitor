# Thesis Monitor — REV56B Current Security/Basis Applicability + Blocker-Coverage Owner

## 0. Task identity

Suggested work-instruction filename:

`20261004-r2b-r9-rev56b-current-security-basis-applicability-blocker-coverage-owner.md`

Suggested result bundle:

`thesis-monitor-20261004-r2b-r9-rev56b-current-security-basis-applicability-blocker-coverage-owner-report.zip`

This is a bounded **current NewBuyer security/basis applicability-owner + blocker-coverage completeness proof** task.

It is NOT:

- a B2 v2 model run;
- a B2 v2 decision/prompt implementation unless explicitly authorized by a later task;
- a Core / Pass A / Overall / Holder redesign;
- a legacy confidence prose reclassification task;
- a source/provider recollection task;
- a fresh-current-data run;
- a blind-label fitting task;
- a new-ticker onboarding task;
- a production deployment task;
- a scheduler / Telegram / production DB task.

The purpose is to close the exact backend coverage gap found by REVISED REV56A.

---

# 1. Authoritative predecessor result

Immediate predecessor:

`thesis-monitor-20261004-r2b-r9-rev56a-newbuyer-typed-veto-ownership-b2-v2-closure-report.zip`

Expected SHA-256:

`2bb91614394290265e33d7a995b4f9a64be3ed7a1ea129a1551eacc73cc711ca`

Expected integrity:

```text
sidecar SHA = PASS
ZIP CRC = PASS
manifest payload count = 76
ZIP member count = 77 including bundle-manifest.json
manifest missing = 0
manifest extras = 0
size mismatch = 0
hash mismatch = 0
```

Expected terminal:

`R2B_R9_REV56A_BACKEND_BLOCKER_COVERAGE_GAP`

Expected key facts:

```text
phase_a = PASS
phase_b = BACKEND_BLOCKER_COVERAGE_INCOMPLETE
subjects = 22
accepted_v1_outputs = 22
validated_v1_branches = 168

confidence_refs = 79
quality_refs = 16
context_only_refs = 95
legacy_entitlements_pending = 95

broad_unknown_refs = 38
reachable_scope_gap_refs = 26
reachable_scope_gap_subjects = 15

blocker_coverage_complete = false
current_blocker_count = null
zero_current_blockers_claimed = false

materiality_assignments = 0
superseded_claims = 0

active_risk_avoid_only = 7/7
authority_unchanged = 22/22

v2_implemented = false
new_frozen_v2_requests = 0

production_code_changes = 0
model_calls = 0
provider_calls = 0
source_recollection = 0
message_generation = 0
Telegram = 0
production_db_writes = 0
scheduler_mutation = 0
deploy = 0
restart = 0
main_merge = 0
remote_push = 0
```

Expected 15 subjects with a reachable broad security/basis coverage gap:

```text
000660
003690
005490
005930
010120
012450
086280
CRCL
GOOGL
IBM
MU
SKHY
SNDK
TSM
WRD
```

REV56A established:

```text
no emitted blocker != proof of no blocker
```

and correctly left all 95 legacy confidence/quality refs at:

`UNRESOLVED_PENDING_BACKEND_COVERAGE`

Do not reinterpret REV56A as a failed test run. It is an intended fail-closed design stop.

---

# 2. Repository identities — keep four identities separate

Verified origin main:

`origin/main = 9b134350cd05c127b6dc866d34a477d95c54785c`

Production-code baseline inherited through REV56A:

`45f4c53f6113575f91a067c423d471023cd4f560`

REV56A final local HEAD:

`d472d4d3941b62bcc2435ac634e50467249e9983`

REV56A instruction commit:

`ee74d2bf489ffccccb32b8c8eeeff8c1a201ed0e`

Protected operating checkout:

`/Users/sskim/Codex/thesis-monitor`

Protected operating HEAD:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Important:

- REV56A final HEAD was local-only: `remote_push = 0`.
- Do not assume `fetch origin` can recover it.
- The relevant production-code baseline remains `45f4c53f...` because REV56A production code changes were 0.
- The docs-only REV56A commit and production-code baseline are different identities.
- `origin/main`, feature work, and operating checkout are not interchangeable.

Before branching, prove locally:

```text
git cat-file -e d472d4d3941b62bcc2435ac634e50467249e9983^{commit}
```

If the exact local REV56A commit is absent:

**STOP.**

Do not reconstruct it from the report.
Do not synthesize replacement ancestry.
Do not branch from `origin/main` and pretend equivalence.

Terminal:

`R2B_R9_REV56B_REPOSITORY_IDENTITY_GAP`

If present, create a new branch from the exact local parent, suggested:

`codex/r2b-r9-rev56b-current-security-basis-coverage-owner`

Before any production-code edit:

1. fetch origin;
2. prove `origin/main` exact SHA;
3. prove local REV56A parent exact SHA;
4. prove clean worktree;
5. prove relevant production files at REV56A HEAD are byte-identical to `45f4c53f...`;
6. prove operating checkout HEAD separately;
7. snapshot protected operating state.

No rebase.
No force push.

---

# 3. Verify REV56A immutable result first

Before design or code:

- verify sidecar SHA;
- ZIP CRC;
- manifest membership;
- per-member byte length;
- per-member SHA-256;
- no missing;
- no extras;
- verify `summary.json`;
- verify terminal;
- verify final repository identities;
- verify `blocker_coverage_complete=false`;
- verify all 95 legacy entitlements remain pending;
- verify current blocker count is null, not zero;
- verify B2 v2 was not implemented.

Required artifact:

`REV56A-integrity.json`

If any mismatch:

`R2B_R9_REV56B_REV56A_INTEGRITY_GAP`

---

# 4. Preserve blind integrity

The blind assessment/comparison may be hash-verified only.

Do not use:

- desired BUY / WAIT / AVOID labels;
- desired ATTRACTIVE count;
- 003690 desired outcome;
- 012450 desired outcome;
- GOOGL desired outcome;
- any post-reveal agreement score

as an input to the owner contract.

The 22 frozen subjects are a **contract regression cohort**, not training labels.

Any label-guided rule or ticker-specific branch:

`R2B_R9_REV56B_TARGET_FITTING_GAP`

---

# 5. Frozen source scope

This task uses only the already frozen structured source generation inherited from REV56A.

Expected frozen generations:

```text
US = rev46-us14-resume1-20261002T064847Z
KR = rev47-kr8-20261002T114556Z
```

"Current" means current within those frozen generations.

It does NOT mean newly collected October 4 data.

Hard zero:

```text
source/provider recollection = 0
```

Do not call Alpha Vantage.
Do not call KIS.
Do not call Kiwoom.
Do not call FMP/Finnhub/SEC/OpenDART.
Do not refresh prices.
Do not refresh valuation.
Do not refresh business evidence.

Alpha Vantage calls:

`0`

---

# 6. Exact REV56A gap to close

REV56A found that the following structured owners exist in part:

- metric-level valuation qualification/denial receipts;
- provider-native valuation receipts;
- security-valuation-basis receipts;
- exact-security code/identity receipts for some routes;
- canonical reported-business-quality owners;
- current effective technical-quality owners;
- event-review context.

But no exhaustive NewBuyer owner currently proves, for every relevant decision scope:

```text
exact current source/security/generation
assessed_scope
scope_level
applicable_metric_refs
explicit NOT_APPLICABLE disposition for unused denominator domains
complete checked categories
all-metrics-invalid proof for global valuation blockers
```

In particular:

- a qualified atomic ratio does not automatically prove every underlying denominator field;
- an unavailable denominator reconstruction does not automatically invalidate an independently qualified atomic ratio;
- existence of `canonical:security_identity:current` or `canonical:security_basis:current` does not prove a completed current decision because those broad legacy records may contain unknown state / blank as-of / null eligibility;
- unknown is neither DENIED nor CLEAR;
- parent-ref presence is not blocker coverage completeness.

REV56B must solve only this ownership/applicability problem.

---

# 7. Required new contract

Define an independent typed contract, suggested:

`newbuyer-security-basis-applicability-coverage-v1`

It must be generated only from:

- frozen structured source packets;
- frozen structured owner receipts;
- explicit producer/dataflow semantics;
- exact current metric/security/source lineage.

Do not derive any field by interpreting legacy confidence prose.

Do not mutate or "complete" the old broad legacy Core facts in place.

The new owner must be independent of the old prose claim text.

---

# 8. Contract output — task-level receipt

Create:

`newbuyer-security-basis-coverage-receipt.json`

Top-level required fields:

```text
contract
version
cohort_id
subjects
source_generations
input_bundle_sha256
checked_categories
category_requirement_contract_sha256
coverage_complete
coverage_incomplete_reasons
subject_receipt_refs
producer_code_sha256
policy_sha256
created_from_frozen_inputs = true
source_recollection = false
legacy_prose_used = false
blind_labels_used = false
```

The task-level receipt must also record:

```text
coverage_proof_kinds_used
owner_provenance_complete
temporal_provenance_complete
decision_provenance_complete
```

`coverage_complete=true` requires all three provenance-completeness flags to be true.

`coverage_complete=true` is allowed only if every required category for every subject has a proven disposition under Sections 9–15.

Absence of a blocker is not sufficient.

---

# 9. Contract output — per-subject receipt

For every one of the 22 frozen subjects create one deterministic typed subject receipt.

Required fields:

```text
receipt_ref
contract
ticker
canonical_security_id
source_generation
source_packet_sha256
decision_axis = NEWBUYER

relevant_valuation_metric_refs
qualified_relevant_valuation_refs
denied_relevant_valuation_refs

categories
coverage_complete
coverage_incomplete_reasons

current_newbuyer_blocker_refs
global_valuation_blocker_refs

legacy_context_refs
legacy_context_veto_status

owner_provenance_complete
temporal_provenance_complete
decision_provenance_complete

input_sha256
receipt_sha256
```

A subject cannot be complete merely because every category has some owner ref. The owner must also carry enough provenance to establish the exact frozen decision state.

`legacy_context_refs` are audit linkage only.

They must never determine a category disposition.

Until the subject's required categories are complete:

```text
legacy_context_veto_status =
UNRESOLVED_PENDING_BACKEND_COVERAGE
```

No subject may receive `NO_VETO_ENTITLEMENT` solely because its emitted blocker list is empty.

---

# 10. Required category model

The exact category set must be derived from B2 v2's intended decision surface and existing producer contracts.

At minimum audit whether these categories are required:

```text
SECURITY_IDENTITY
SECURITY_CLASS_OR_LISTING
PRICE_TO_SECURITY_BINDING
VALUATION_SECURITY_BASIS
VALUATION_CURRENCY_BASIS
SHARE_OR_DENOMINATOR_BASIS
DEPOSITARY_OR_ADR_CONVERSION
VALUATION_HORIZON_OR_PERIOD
PROVIDER_SECURITY_BINDING
VALUATION_SOURCE_QUALITY
BUSINESS_SOURCE_QUALITY
```

Do not blindly force every category onto every metric.

Before assigning any disposition, build a deterministic **category-requirement matrix**:

```text
metric_ref
category
required = true | false
requirement_owner_contract
requirement_proof_kind
requirement_reason
producer/dataflow proof refs
```

A category may be excluded from a metric only through positive producer/dataflow proof. Do not exclude it merely because no current error/ref mentions it.

This requirement matrix must be built independently of the 26 legacy reachable-gap refs. Those refs are regression witnesses only, not inputs to category necessity.

For each category record:

```text
category
required_for_metric_refs
category_requirement_basis
coverage_disposition
coverage_proof_kind
owner_state
scope_level
owner_contract
owner_ref
owner_decision_version
owner_field_eligibility
owner_as_of
owner_effective_at
owner_temporal_scope
source_generation
security_id
applies_to_metric_refs
not_applicable_to_metric_refs
not_applicable_reason_codes
denial_reason_codes
qualification_reason_codes
input_refs
input_sha256
```

Allowed `coverage_proof_kind`:

```text
RUNTIME_OWNER_RECEIPT
COMPOSED_TYPED_OWNER
PRODUCER_SEMANTICS
```

Rules:

- `RUNTIME_OWNER_RECEIPT` or `COMPOSED_TYPED_OWNER` may establish `QUALIFIED` / `DENIED` only when decision version, field eligibility, generation/security binding, and temporal provenance are complete for that contract.
- `PRODUCER_SEMANTICS` may establish `PROVEN_NOT_APPLICABLE` by proving that the metric/decision path does not consume that semantic domain.
- `PRODUCER_SEMANTICS` alone must **not** manufacture a current `QUALIFIED` or `DENIED` state.
- If a contract is genuinely timeless/static, `owner_temporal_scope` must explicitly say so and explain why `owner_as_of` is not applicable; blank/missing time is not sufficient.


Allowed `coverage_disposition`:

```text
PROVEN_APPLICABLE
PROVEN_NOT_APPLICABLE
UNRESOLVED
```

Allowed `owner_state` when applicable:

```text
QUALIFIED
DENIED
UNKNOWN
```

`PROVEN_NOT_APPLICABLE` is not a synonym for missing data.

It requires positive contract/dataflow proof that the category is outside the semantic inputs of the affected metric/decision.

If this cannot be proven:

`UNRESOLVED`

---

# 11. Scope levels

Every applicable category must declare one of:

```text
SECURITY_GLOBAL
VALUATION_GLOBAL
METRIC_SCOPED
BUSINESS_GLOBAL
```

Do not silently promote scope.

A metric-scoped denial can affect only its declared metric refs unless a separate typed proof establishes a broader invalidation.

Example:

```text
PER denied
CURRENT_FY1_FPER qualified
```

must not become a global valuation blocker merely because PER is denied.

Likewise:

```text
recomputed denominator unavailable
provider-native atomic ratio qualified
```

must preserve the atomic ratio unless the typed owner proves the ratio itself depends on the unavailable denominator scope.

---

# 12. Atomic-ratio independence proof

For every qualified provider-native or source-native ratio used by NewBuyer, explicitly prove whether it is semantically independent of separately reconstructed denominator fields.

Required per metric:

```text
metric_ref
metric
producer_contract
producer_ref
exact_security_binding
exact_generation_binding
source_native_or_derived
depends_on_external_denominator_reconstruction
depends_on_cross_security_transfer
depends_on_depositary_conversion
depends_on_external_currency_conversion
applicable_security_basis_categories
not_applicable_security_basis_categories
proof_refs
```

A category may become `PROVEN_NOT_APPLICABLE` only when producer/dataflow semantics prove the metric does not consume that domain.

Never infer independence from:

- the fact that a number exists;
- the fact that the ratio is dimensionless;
- absence of an error;
- absence of a blocker;
- the old confidence prose.

If exact producer semantics are insufficient:

`UNRESOLVED`

---

# 13. Cross-security / ADR / depositary rules

This is especially important for names where issuer evidence and monitored-security valuation are different surfaces.

Existing issuer-business bridges may authorize:

```text
issuer business evidence
```

while explicitly denying:

```text
security per-share transfer
security valuation transfer
```

Do not let an issuer bridge prove monitored-security valuation basis.

For ADR/depositary/cross-security subjects:

- preserve exact monitored security ID;
- preserve underlying/issuer ID separately;
- require explicit depositary/conversion owner before cross-security per-share transfer;
- if no exact conversion is required by an independently provider-native monitored-security ratio, prove non-applicability at the metric level;
- otherwise leave unresolved or denied according to the exact typed owner.

No whole-security clearance from issuer identity alone.

---

# 14. Exact-security identity receipts

Receipts such as exact ticker/code identity may prove only what their contract states.

For example, a receipt that proves:

```text
requested_security_id == returned_security_id
status = QUALIFIED_EXACT_SECURITY
```

does not automatically prove:

```text
currency
share class
EPS basis
depositary conversion
denominator basis
valuation horizon
```

Do not broaden owner scope.

Likewise, a receipt with `currency=null` cannot be used as positive currency proof.

Each use must record the exact field/semantic owned.

---

# 15. Completeness semantics

For each subject define the **required category × relevant metric matrix** first.

Then require every cell to be one of:

```text
QUALIFIED_APPLICABLE
DENIED_APPLICABLE
PROVEN_NOT_APPLICABLE
```

Any cell that remains:

```text
UNKNOWN
UNRESOLVED
MISSING_OWNER
AMBIGUOUS_SCOPE
```

means subject coverage is incomplete.

Task-level:

```text
coverage_complete=true
```

requires all 22 subjects complete.

Do not use partial cohort completeness as permission to enable v2.

If 21/22 close:

`coverage_complete=false`

---

# 16. Blocker generation rules

REV56B may derive **typed blocker candidates/receipts** only from applicable typed owner states.

A blocker must include:

```text
blocker_ref
blocker_class
ticker
canonical_security_id
source_generation
owner_contract
owner_ref
category
scope_level
affected_axis = NEWBUYER
affected_metric_refs
status
reason_codes
input_sha256
```

No blocker may cite legacy prose as its owner.

Legacy refs may be linked only as historical/context audit refs.

`UNKNOWN` does not produce either:

- a blocker; or
- clearance.

It produces incomplete coverage.

Until task-level `coverage_complete=true`:

```text
current_blocker_count = null
```

Typed blocker candidates may be enumerated, but do not publish `0` or any exhaustive current-blocker count while required cells remain unresolved. A partial candidate count is not a complete blocker census.

---

# 17. Global valuation blocker rule

A `VALUATION_GLOBAL` blocker is high bar.

It is allowed only if typed proof establishes that **all otherwise relevant valuation metrics** for that subject are invalid for the NewBuyer valuation decision.

Required fields:

```text
all_relevant_metric_refs
invalidated_metric_refs
still_qualified_metric_refs
all_metrics_invalid_proof
global_reason_code
```

Required:

```text
all_metrics_invalid_proof = true
still_qualified_metric_refs = []
```

If even one relevant metric remains independently qualified:

- do not emit a generic global valuation blocker;
- keep narrower metric denial scoped to its metric.

This rule applies regardless of legacy confidence text.

---

# 18. Business quality remains separate

Selected reported-business-quality owners may generate typed business-quality denial evidence when their contract proves it.

Do not convert business quality into valuation state.

Maintain distinct collections:

```text
business_blocker_refs
valuation_blocker_refs
security_basis_blocker_refs
legacy_context_refs
```

No laundering across axes.

A business-quality denial may affect the business gate / NewBuyer admissibility only according to an explicit policy contract.

It must not become:

```text
valuation = UNRESOLVED
```

unless a separate valuation owner proves that.

---

# 19. Legacy confidence/context handling

All 95 historical confidence/quality refs remain preserved byte-for-byte.

During REV56B:

- no `BLOCKING` classification;
- no `WEAKENING` classification;
- no `INFORMATIONAL` classification;
- no blanket `SUPERSEDED`;
- no prose-derived severity;
- no prose-derived category mapping;
- no prose-derived valuation evidence.

Before complete coverage:

```text
UNRESOLVED_PENDING_BACKEND_COVERAGE
```

Only if task-level `coverage_complete=true` may a later stage consider axis-specific:

```text
CONTEXT_ONLY_NO_VETO_ENTITLEMENT
CURRENT_BACKEND_BLOCKER_BOUND
```

REV56B itself does not need to rewrite all 95 entitlements. Its job is to produce the independent coverage owner proof.

---

# 20. Valuation evidence separation

Legacy Core confidence/context prose must never be used to justify:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
UNRESOLVED
```

Business evidence must never be used as a substitute for valuation evidence.

Required audit:

`axis-evidence-separation.json`

It must prove separately:

```text
valuation metric refs
security/basis applicability refs
business-quality refs
technical-quality refs
active-risk refs
legacy context refs
```

No ref class may silently migrate to another axis.

---

# 21. Producer/dataflow audit before implementation

Before writing a new runtime owner, inspect and record the actual producer semantics of all relevant existing contracts.

At minimum inspect equivalent current code/dataflow for:

```text
provider-native valuation snapshot
security valuation basis
exact-security identity/code receipt
forward valuation owner
current denominator scope
reported business quality owner
technical current-effective quality
B2 v1 contract/shadow
```

Required artifact:

`security-basis-owner-producer-audit.json`

For each producer record:

```text
path
symbol/function
contract
fields produced
fields not produced
security binding
generation binding
metric scope
known limitations
sha256
```

Do not infer missing semantics from names.

---

# 22. Implementation authorization boundary

Two outcomes are allowed.

## Outcome A — existing structured semantics are sufficient

If the required applicability matrix can be deterministically derived from frozen owners **with complete field eligibility, decision-version, security/generation, and temporal provenance for every applicable current-state disposition**, implement the new default-OFF coverage owner.

Suggested isolation:

```text
scripts/newbuyer_security_basis_coverage.py
scripts/newbuyer_security_basis_coverage_contract.py
```

Names may differ.

It must not change B2 v1 behavior.

It must not yet change production NewBuyer stance logic.

## Outcome B — structured semantics are insufficient

If even one required category cannot be proven from current structured owners:

STOP.

Do not recollect sources.
Do not interpret prose.
Do not guess.
Do not label unknown as NOT_APPLICABLE.
Do not implement a fake "complete" receipt.

Terminal:

`R2B_R9_REV56B_SOURCE_OWNER_CONTRACT_GAP`

Required report must identify the exact missing field/category/producer contract needed for the next repair.

---

# 23. No B2 v2 decision implementation in REV56B

Even if coverage reaches 22/22 complete:

Do not yet:

- change NewBuyer prompt;
- change stance schema;
- change WAIT reason schema;
- remove `CONFIDENCE_UNCERTAINTY` from runtime v1;
- expose ATTRACTIVE through new v2 rules;
- build or run frozen model requests;
- run REV57.

REV56B closes owner coverage only.

If successful, next task will consume its sealed receipt to implement B2 v2 under the already accepted REV56A rules.

This split is deliberate.

---

# 24. Frozen cohort proof

Run the new coverage owner over the exact same 22 frozen subjects.

Required artifact:

`rev56b-22-security-basis-coverage.json`

Per subject include:

```text
ticker
canonical_security_id
generation
source_input_sha256
v1_request_sha256

relevant_metric_refs
qualified_metric_refs
denied_metric_refs

required_category_metric_cells
resolved_cell_count
unresolved_cell_count

typed_blocker_refs
global_valuation_blocker_refs

coverage_complete
coverage_incomplete_reasons

legacy_refs_count
legacy_prose_used = false
blind_label_used = false
```

Task-level summary:

```text
subjects = 22
complete_subjects
incomplete_subjects
coverage_complete
```

No result may be hidden because a ticker is inconvenient.

---

# 25. Mandatory diagnostics

Explicitly audit at least:

```text
003690
012450
GOOGL
010120
047810
SKHY
```

They are diagnostics, not expected labels.

## 003690

Prove whether every security/basis category relevant to its qualified valuation metric(s) is either:

- qualified applicable; or
- proven not applicable.

Do not infer "no blocker" from absence.

## 012450

Same requirement. No automatic removal of generic unresolved yet.

## GOOGL

Preserve provider-native metric scope. Do not require SUPPORTIVE.

## 010120

It has a pattern where some metrics may be denied while another valuation metric remains qualified. Prove metric-scoped handling; do not promote narrower denial to global valuation blockage.

## 047810

Active material risk remains independently typed. Coverage work must not weaken AVOID safety.

## SKHY

Cross-security/depositary and issuer-business evidence boundaries must remain explicit. A business issuer bridge must not grant per-share security valuation authority.

---

# 26. Negative controls

Required deterministic tests:

### A. Missing owner

A required category cell has no structured owner.

Expected:

```text
coverage_disposition = UNRESOLVED
subject coverage_complete = false
```

Not DENIED.
Not NOT_APPLICABLE.
Not CLEAR.

### B. Empty blocker list

All emitted blocker arrays empty but one required category unresolved.

Expected:

```text
coverage_complete = false
no_current_blocker_proven = false
```

### C. Proven not applicable

A category is outside an atomic metric's actual producer/dataflow semantics with explicit proof.

Expected:

```text
coverage_disposition = PROVEN_NOT_APPLICABLE
```

### D. Metric-scoped denial + qualified alternate metric

Expected:

```text
no VALUATION_GLOBAL blocker
qualified alternate metric preserved
```

### E. All relevant metrics invalid

Only with exact typed proof over all relevant metrics may:

```text
VALUATION_GLOBAL
```

be emitted.

### F. Legacy prose mutation attempt

Any attempt to derive category state from claim text must fail.

### G. Missing temporal / decision provenance

A structured owner ref exists but has one or more of:

```text
decision_version = null
field_eligibility = null
as_of/effective_at blank where the contract requires time
```

Expected:

```text
coverage cell = UNRESOLVED
```

Existence of the ref is not qualification.

### H. Producer semantics cannot fabricate current state

Producer code proves a metric does not consume depositary conversion.

Expected:

```text
DEPOSITARY_OR_ADR_CONVERSION = PROVEN_NOT_APPLICABLE
```

But the same producer-semantics proof must not be reused to mark unrelated security identity/currency categories `QUALIFIED`.

### I. Ticker-specific rule

Static/test guard must reject decision logic keyed to the 22 ticker names.

---

# 27. Authority freeze

For all 22 require unchanged digests for:

```text
frozen source packets
source-use ownership
Core raw outputs
Core atomic claims
Core effects/materiality
Pass A
Overall
directional score
Holder
B2 v1 contract bytes
B2 v1 accepted outputs
valuation fact bytes
timing catalog
current price
active-risk refs
legacy confidence/quality claim bytes
```

Allowed new artifacts only:

```text
REV56B applicability/coverage owner
REV56B typed blocker sidecar/candidates
REV56B audits/tests
default-OFF helper code if Outcome A
```

Any change to Core/A/Overall/Holder/B2 v1:

`R2B_R9_REV56B_AUTHORITY_LEAKAGE_GAP`

---

# 28. Provider/schema safety

If new runtime code or JSON schema is added:

- closed object shapes where required;
- typed enum values;
- no untyped `const` leaves;
- required fields consistent;
- stable canonical serialization;
- deterministic receipt hashes;
- no unsupported provider-wire assumptions.

This task does not send model requests, but all new schemas must be locally validated.

Required artifact:

`rev56b-schema-validation.json`

---

# 29. Validation sequence

Always:

1. REV56A integrity;
2. repository identity/local-parent proof;
3. frozen input hash proof;
4. producer/dataflow audit;
5. required category universe derivation;
6. category × metric applicability matrix;
7. subject coverage receipts;
8. negative controls;
9. 22/22 authority freeze;
10. protected-state rehash;
11. secret scan.

If Outcome A implements code, also require:

12. focused tests;
13. Ruff;
14. `git diff --check`;
15. full pytest;
16. default-OFF compatibility;
17. commit;
18. feature branch push only;
19. remote SHA readback;
20. Hosted feature CI PASS.

If Outcome B stops before production code changes:

- full pytest is not required solely for a design stop;
- Hosted CI is not required;
- do not fake PASS placeholders;
- not-created artifacts must be explicit non-executable notices.

Preserve failed audit/test attempts and repairs if any.

---

# 30. Network and execution policy

During offline proof:

```text
model calls = 0
provider calls = 0
source recollection = 0
message generation = 0
Telegram = 0
production DB/WAL writes = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating checkout mutation = 0
main merge = 0
main push = 0
```

Permitted network only:

- initial Git fetch for identity;
- feature branch push if Outcome A produces code and all local gates pass;
- Hosted feature CI if a feature push occurs.

Record every permitted network phase separately.

No model execution.

---

# 31. Success criteria

REV56B succeeds only if all are proven:

```text
REV56A integrity PASS

exact local REV56A parent proven present

required NewBuyer security/basis category universe explicitly defined

every required category × metric cell for all 22 has:
  QUALIFIED_APPLICABLE
  or DENIED_APPLICABLE
  or PROVEN_NOT_APPLICABLE

every applicable current-state cell has complete:
  owner decision version
  field eligibility
  security/generation binding
  temporal provenance (or explicit typed timeless/static scope)

every PROVEN_NOT_APPLICABLE cell is backed by positive producer/dataflow non-consumption proof

no unresolved/missing/ambiguous/provenance-incomplete cell remains

coverage_complete = true
owner_provenance_complete = true
temporal_provenance_complete = true
decision_provenance_complete = true
complete_subjects = 22/22

no legacy prose used to derive coverage
no blind labels used
no ticker-specific rules

metric-scoped denial never promoted without typed global proof
all global valuation blockers satisfy all-metrics-invalid proof

Core/A/Overall/Holder unchanged 22/22
B2 v1 unchanged
active-risk safety unchanged 7/7

model/provider/source calls = 0
operating checkout unchanged
origin/main unchanged
```

If code was added:

```text
focused tests PASS
Ruff PASS
git diff --check PASS
full pytest PASS
secret scan PASS
feature push/readback PASS
Hosted feature CI PASS
```

Success terminal:

`R2B_R9_REV56B_SECURITY_BASIS_COVERAGE_OWNER_PASS_READY_FOR_B2_V2_IMPLEMENTATION`

This terminal authorizes only the **next work-instruction design** for B2 v2 implementation.

It does not authorize REV57 or a model call.

---

# 32. Stop terminals

Use the narrowest truthful terminal:

```text
R2B_R9_REV56B_REPOSITORY_IDENTITY_GAP
R2B_R9_REV56B_REV56A_INTEGRITY_GAP
R2B_R9_REV56B_FROZEN_INPUT_IDENTITY_GAP
R2B_R9_REV56B_CATEGORY_UNIVERSE_GAP
R2B_R9_REV56B_SOURCE_OWNER_CONTRACT_GAP
R2B_R9_REV56B_APPLICABILITY_SCOPE_GAP
R2B_R9_REV56B_GLOBAL_BLOCKER_SCOPE_GAP
R2B_R9_REV56B_TARGET_FITTING_GAP
R2B_R9_REV56B_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV56B_SCHEMA_VALIDATION_GAP
R2B_R9_REV56B_FULL_VALIDATION_GAP
R2B_R9_REV56B_FEATURE_CI_GAP
R2B_R9_REV56B_PROTECTED_STATE_GAP
```

Never convert an ownership gap into completeness by assigning NOT_APPLICABLE without proof.

---

# 33. Required result bundle

Create:

`thesis-monitor-20261004-r2b-r9-rev56b-current-security-basis-applicability-blocker-coverage-owner-report.zip`

plus `.sha256`.

Include at minimum:

```text
REPORT.md
summary.json
REV56A-integrity.json
repository-identities.json
local-parent-proof.json
frozen-input-identity.json
security-basis-owner-producer-audit.json
newbuyer-security-basis-coverage-contract.json
newbuyer-security-basis-coverage-receipt.json
category-universe.json
category-requirement-matrix.json
category-metric-applicability-rules.json
owner-provenance-completeness.json
rev56b-22-security-basis-coverage.json
typed-blocker-candidate-audit.json
global-blocker-scope-proof.json
axis-evidence-separation.json
legacy-context-preservation.json
negative-controls.json
authority-freeze-digests.json
default-off-compatibility.json
rev56b-schema-validation.json
focused-validation.json
full-validation.json
ruff-validation.json
diff-validation.json
secret-scan.json
feature-push-receipt.json
hosted-feature-ci.json
protected-before.json
protected-state.json
final-repository-identities.json
bundle-manifest.json
```

If the task stops before implementation, not-created implementation-specific artifacts may appear only as explicit non-executable notices.

No credentials.
No raw recipient IDs.
No auth files.

Manifest self-hash may be excluded if explicitly stated.

---

# 34. Final report requirements

The final report must explicitly state:

```text
origin/main
production-code baseline
REV56A local parent
REV56B final feature HEAD
protected operating checkout
```

It must also state:

```text
coverage_complete
owner_provenance_complete
temporal_provenance_complete
decision_provenance_complete
complete_subjects / 22
unresolved required cells
provenance-incomplete required cells
current typed blocker count
global valuation blocker count
legacy prose used = false
blind labels used = false
source recollection = 0
model calls = 0
provider calls = 0
```

If coverage is incomplete, list exact:

```text
ticker
metric_ref
category
missing owner contract/field
why existing receipts are insufficient
```

Do not hide the residual gap behind an aggregate count.

---

# 35. What comes after REV56B

Do not execute automatically.

If REV56B succeeds:

**next = bounded B2 v2 implementation using the sealed REV56B coverage owner**

That next task may then:

- assign legacy NewBuyer veto entitlement only after complete coverage;
- implement typed blocker-bound `CONFIDENCE_UNCERTAINTY`;
- remove free generic valuation `UNRESOLVED` where qualified valuation is usable and no global blocker exists;
- preserve metric scope;
- freeze exact B2 v2 requests.

Only after that implementation passes offline validation:

**REV57 = frozen B2 v2 model reproof**

Then:

1. fresh/current-data shadow validation as required;
2. one final fresh strict blind end-to-end test;
3. new-ticker registration/onboarding redesign;
4. add new monitored names.

Do not reorder this sequence.

---

# 36. Final principle

REV56A correctly proved:

```text
no emitted blocker
!=
proof of no blocker
```

REV56B must now prove the missing inverse boundary:

```text
for every category the NewBuyer decision actually depends on,
there is an explicit structured owner disposition
```

and only then can:

```text
absence of typed blocker
```

be interpreted as:

```text
no blocker within the completely covered decision surface
```

Unknown is not denial.
Unknown is not clearance.
Missing scope is not NOT_APPLICABLE.
Metric denial is not global denial.
Legacy prose is not a valuation fact.
Issuer business evidence is not monitored-security valuation authority.

The repair target is **complete typed applicability ownership**, not a desired stance count.
