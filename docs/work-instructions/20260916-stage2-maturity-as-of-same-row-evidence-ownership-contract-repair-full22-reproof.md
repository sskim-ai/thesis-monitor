# Thesis Monitor — Stage-2 Maturity `as_of` Same-Row Evidence Ownership Contract Repair + New Full22 Reproof

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-stage2-maturity-as-of-same-row-evidence-ownership-contract-repair-full22-reproof.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-stage2-maturity-as-of-same-row-evidence-ownership-contract-repair-full22-reproof-report.zip
```

Suggested phase name:

```text
M12CC — Stage-2 Maturity as_of Same-Row Evidence Ownership Contract Repair
```

This is a **bounded Stage-2 `driver_maturity.as_of` semantic-ownership audit + conditional typed-date ownership contract hardening + conditional wholly new frozen US14/KR8 full22 reproof**.

The ownership audit is mandatory. Model-facing repair and full22 reproof are conditional on proving `MODEL_OWNS_MEANINGFUL_DATE_SELECTION`.

It is NOT:

- a new investment-decision architecture,
- a change to BUY/HOLD/SELL semantics,
- a change to new-buyer ATTRACTIVE/WAIT/AVOID semantics,
- a change to holder HOLDABLE/REVIEW/REDUCE semantics,
- a change to timing semantics,
- a change to `pre_confirmation_buy`,
- a change to maturity polarity semantics,
- a change to maturity atomic-claim identity,
- a change to Fundamental Core ownership,
- a reopening of M12CB frozen-core numeric claim-language scope,
- a validator relaxation,
- a date allowlist bypass,
- an `010120` ticker exception,
- a `2026-08-12` production hardcode,
- an assessment-date fallback,
- a “latest date” fallback,
- a rejected-output patch/canonicalization task,
- a repair-model route,
- a retry/fallback/judge/selective-rerun task,
- a generation-resume or generation-stitch task,
- a Treasury redesign,
- a Kiwoom gateway configuration task,
- a production deploy/merge/push task.

The exact objective is:

```text
first determine the canonical semantic owner of driver_maturity.as_of
(model meaningful selection vs deterministic provenance vs hybrid)

+

preserve the existing deterministic same-row evidence/date validation rule

+

reuse the existing canonical evidence-date ownership chain
(resolved evidence date -> maturity_ref_dates -> same-row deterministic validator)

+

ONLY IF the audit proves MODEL_OWNS_MEANINGFUL_DATE_SELECTION:
make the row-local ownership relationship substantially more model-consumable
without inventing a second owner or weakening validation

+

ONLY THEN prove the repaired model-facing contract with a wholly new US14 + KR8 generation from call 1.

If the audit instead proves deterministic provenance or unresolved hybrid ownership,
stop before model calls and return the appropriate bounded design/migration next scope.
```

---

# 0.1 Operating model and source-of-truth priority

This project continues under the frozen operating model:

```text
Chat: architecture/scope decision
→ Work/Codex: execute only the narrow authorized task
→ Chat: review the result from the whole-system architecture perspective
```

Before writing new code, inspect Git history and existing canonical owners. If an implementation or helper already exists, reuse or complete it rather than creating parallel ownership logic.

For M12CC, source-of-truth priority is:

```text
1. latest M12CB result ZIP
2. current repository state
3. latest M12CA result ZIP
4. older M12BZ/new-session handoff
```

Do not revive older blockers from stale handoff state.

---

# 1. Authoritative M12CB result and integrity gate

Use this as the latest authoritative completed phase:

```text
thesis-monitor-20260916-stage2-frozen-core-claim-language-validation-scope-repair-full22-reproof-report.zip
```

Expected SHA-256:

```text
86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb
```

Independently verify the ZIP before implementation.

Expected artifact integrity:

```text
artifact_count = 262
manifest artifacts = 262
ZIP entries = 263 including artifact-manifest.json
missing artifact = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Do not proceed on an integrity mismatch.

Also record the exact SHA-256 of the supplied M12CC work instruction used for execution.

---

# 2. Repository provenance

M12CB authoritative provenance:

```text
origin_main_observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
base_documentation_sha = 29878d2ecc5ff96add09b25fb7fe0fb2b216b43e
m12cb_implementation_branch = codex/20260916-m12cb-stage2-frozen-core-claim-language-scope
m12cb_work_instruction_commit = 3830959
m12cb_implementation_sha = dcaac603f11edbde150a5d34ee20201fece5e7dc
m12cb_final_local_sha = 978eced97e80d3f1f5f896f53dd317088f4f4a41
```

`base_documentation_sha` must not be reinterpreted as the actual origin main SHA.

Before changing anything, record:

```text
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git log -n 30 --oneline --decorate
```

Do not silently reset to `origin/main` or discard M12CB local lineage. If actual repository state differs materially from the M12CB report, classify the divergence before implementation.

Suggested M12CC branch:

```text
codex/20260916-m12cc-stage2-maturity-as-of-ownership
```

Use the actual repository state and existing branch/commit discipline if the project already has a canonical continuation mechanism.

---

# 3. Freeze M12CB as successful target-scope convergence

M12CB succeeded at its authorized objective.

Freeze these facts:

```text
M12CB target defect = FROZEN_CORE_EXACT_NUMERIC_SCOPE_FALSE_POSITIVE
historical affected tickers = SNDK / TSLA / TSM
M12CB target-scope convergence = PASS
```

The immutable M12CA failed batch replay proved:

```text
SNDK trusted Stage-2 = PASS
TSLA trusted Stage-2 = PASS
TSM trusted Stage-2 = PASS
frozen-core exact numeric claims replayed = 4
Stage-2-owned exact numeric claims = 0
```

The wholly new M12CB generation also proved SNDK/TSLA/TSM PASS under the repaired ownership scope.

Freeze the M12CB validator contract:

```text
standalone validator scope = FULL_CANDIDATE
trusted integrated Stage-2 claim-language scope = STAGE2_OWNED_FIELDS_ONLY
ownership gate = before scoped semantics
exact-number regex changed = false
standalone strictness = preserved
frozen-core mutation still hard-fails
Stage-2-owned exact numeric prose still hard-fails
unsupported Stage-2 metrics still hard-fail
unknown Stage-2 refs still hard-fail
```

M12CC must not reopen this logic.

---

# 4. Freeze GOOGL and all previously closed contracts

GOOGL remains a required regression fixture:

```text
ticker = GOOGL
overall_direction = BUY
overall_maturity = PARTIAL
pre_confirmation_buy = true
new_buyer = WAIT
holder = HOLDABLE
timing = UNFAVORABLE
```

Freeze:

```text
preconfirmation semantic validation = PASS
mechanical new-buyer mapping = 0
price-confirmation contamination = 0
```

Do not change:

- frozen-core numeric claim-language scope repair,
- standalone numeric validator strictness,
- preconfirmation BUY contract,
- three-axis independence,
- preconfirmation lifecycle semantics,
- post-confirmation HOLD maturity semantics,
- maturity polarity and atomic-claim contract,
- Fundamental Core batch identity,
- exact-ref fidelity,
- Stage-2 typed string/date primitive contract,
- frozen-core ownership,
- expectation/valuation separation and ownership,
- BusinessDelta ownership,
- Persistence V2,
- Price/Timing immutability,
- Treasury restoration,
- Kiwoom local restoration.

These contracts are frozen regressions, not redesign targets.

---

# 5. M12CB deterministic gate results to preserve

Freeze these M12CB deterministic results as the pre-M12CC baseline:

```text
focused tests = 115 PASS
wider regression reference = 208 PASS / 4 SKIPPED
full suite = 4055 PASS / 63 SKIPPED / 2 WARNINGS
Ruff = PASS
git diff --check = PASS
worktree clean = true
```

M12CC may add tests. Existing tests must not be deleted or weakened merely to obtain green status.

---

# 6. Authoritative M12CB full22 result

M12CB generation:

```text
20260916-uskr22-m12cb-20260916T041207Z-dcaac603f11e
```

Frozen packets:

```text
US packet SHA = 2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228
KR packet SHA = 819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597
frozen ticker count = 22
```

Call accounting:

```text
planned = 16
started = 15
completed = 15
usable = 14
retry = 0
fallback = 0
judge = 0
repair = 0
selective rerun = 0
hotfix = 0
resume/stitch = 0
```

Coverage before hard stop:

```text
Fundamental Core valid = 22/22
Stage-2 schema-valid outputs = 20
Stage-2 formally accepted semantics = 17
Stage-2 diagnostic semantic passes = 19/20
US final composition = 14/14
global full22 final composition = NOT_REACHED
```

Do not continue, resume, repair, or stitch this generation.

---

# 7. Current blocker: genuine Stage-2 maturity-date ownership violation

The only current blocker is:

```text
MODEL_OUTPUT_MATURITY_DATE_OWNERSHIP_VIOLATION
```

Affected ticker:

```text
010120
```

Affected row:

```text
$.candidates[1].driver_maturity[2].as_of
```

Driver:

```text
수주와 수익성 지속에 대한 높아진 기대는 확인된 부담이다.
```

Same-row supporting evidence:

```text
decision-evidence:e3e0e73c7b80428e5459
```

Canonical owned concrete date for that ref:

```text
2026-08-12
```

Model-emitted date:

```text
2026-09-15
```

Deterministic validator error:

```text
maturity_evidence_date_not_owned:수주와 수익성 지속에 대한 높아진 기대는 확인된 부담이다.
```

M12CB audit classification:

```text
validator_false_positive = false
global_schema_enum_contains_emitted_date = true
same_row_date_owned = false
detailed_date_failure_classification = CONCRETE_BUT_UNOWNED_DATE
```

Do not classify this incident as symbolic-date fabrication merely because an older aggregate counter may have grouped it there.

Therefore this is **not** a validator false positive and must not be “fixed” by accepting the bad date.

KR Stage-2 batch 2 is rejected as a unit. Do not salvage or stitch the individually diagnostic-PASS rows from that rejected batch.

KR Stage-2 batch 3 was not run and must not be appended to the old generation.

---

# 8. Existing canonical ownership chain — inspect before coding

M12CB repository snapshot already shows a canonical ownership chain. M12CC must start by proving its current repository equivalent and Git provenance.

Known components from M12CB:

### 8.1 Evidence compaction

`_compact_stage2_owned_evidence(...)` adds:

```text
resolved_as_of_date
```

by applying the existing `concrete_evidence_date(...)` parser to canonical evidence `as_of`.

### 8.2 Stage-2 ref catalog manifest

`accepted_v2_stage2_ref_catalog_manifest(...)` already builds:

```text
maturity_ref_dates
allowed_maturity_dates
maturity_date_catalog_hash
```

`maturity_ref_dates` is the canonical evidence-ref -> concrete-date ownership relation used by the current Stage-2 contract.

### 8.3 Stage-2 output schema

`accepted_v2_stage2_output_schema(...)` currently constrains `DriverEvidenceMaturity.as_of` to the **batch-wide** `allowed_maturity_dates` enum.

This is only a coarse validity boundary. It does not by itself prove that a date is owned by an evidence ref cited in the same row.

### 8.4 Prompt

The production Stage-2 prompt already says:

```text
Every driver_maturity.as_of must be an exact YYYY-MM-DD date owned by at least one evidence ref cited in that same driver_maturity row.
Use each evidence item's resolved_as_of_date when non-null.
```

The rule therefore already exists semantically.

### 8.5 Deterministic validator

`validate_preconfirmation_candidate(...)` computes the set of concrete dates owned by the row's supporting and contradicting evidence refs and requires:

```text
row.as_of in cited_dates
```

It also rejects unresolved and future dates.

This deterministic validator remains authoritative and must remain fail-closed.

---

# 9. Mandatory pre-model semantic ownership audit for `driver_maturity.as_of`

**This audit precedes any prompt/schema/model-facing repair. Do not assume that the model should continue to choose `driver_maturity.as_of`.**

Before changing the model-facing contract, classify the semantic ownership of `driver_maturity.as_of` as exactly one of:

```text
MODEL_OWNS_MEANINGFUL_DATE_SELECTION
DETERMINISTIC_PROVENANCE_FIELD
HYBRID_REQUIRES_SEPARATE_POLICY_DECISION
```

Required artifact:

```text
audits/06-maturity-as-of-semantic-ownership-audit.json
```

The audit must answer with code/history/downstream evidence, not architectural preference:

1. Does `driver_maturity.as_of` encode an actual investment/semantic judgment by the model?
2. Or is it provenance metadata that should simply identify the concrete date owned by evidence cited in the same row?
3. When one row cites multiple refs that own different concrete dates, is choosing one of those dates a meaningful model decision, or merely a provenance representation problem?
4. How do downstream renderers, validators, reports, message composition, persistence, and any later decision logic consume `driver_maturity.as_of`?
5. Historically, was the field model-owned, deterministic-owned, or changed between the two?
6. Do existing `resolved_as_of_date` and `maturity_ref_dates` already determine the correct value completely for the relevant row shape?
7. Is there any historical evidence that the model is expected to choose among multiple same-row-owned dates for semantic reasons?
8. Would deterministic derivation change the meaning/output contract, or merely remove model-authored provenance duplication?

Required evidence sources include at minimum:

```text
Git history / blame
DriverEvidenceMaturity schema/model definition
prompt history
accepted_v2_stage2_ref_catalog_manifest
_compact_stage2_owned_evidence
resolved_as_of_date
maturity_ref_dates
validate_preconfirmation_candidate
downstream renderer/composer use sites
persistence / report artifact consumers
historical proof artifacts where available
```

Important constraints:

- Do not change the output contract merely because deterministic ownership looks simpler.
- Do not add a deterministic rewrite merely to make historical `010120` pass.
- Do not infer ownership from the single failing ticker.
- Do not proceed to model calls until this classification is frozen.

---

# 10. Mandatory Git-history / canonical-owner audit

In parallel with the semantic audit, inspect Git history for at least:

```text
accepted_v2_stage2_ref_catalog_manifest
accepted_v2_stage2_output_schema
_compact_stage2_owned_evidence
validate_preconfirmation_candidate
DriverEvidenceMaturity
maturity_ref_dates
resolved_as_of_date
maturity_evidence_date_not_owned
```

Required output artifact:

```text
audits/07-maturity-date-owner-provenance.json
```

It must answer:

1. Which function is the canonical owner of concrete evidence date parsing?
2. Which function owns evidence-ref -> date mapping?
3. Which function owns deterministic same-row validation?
4. Which function/schema owns model-visible allowed dates?
5. Is there an older row-local schema/helper that should be reused?
6. Would any proposed implementation create a parallel date owner?
7. Has `driver_maturity.as_of` historically been model-selected, deterministically derived, or both at different times?
8. Is any existing helper already capable of deriving a row-local owned-date projection without a second parser/source of truth?

If an existing canonical row-local helper already exists, reuse it.

Do not create a second parser for dates and do not maintain a second independently computed map.

Expected likely reuse classification, subject to actual Git history:

```text
EXISTING_MATURITY_REF_DATE_OWNER_PRESENT_MODEL_CONSUMPTION_CONTRACT_INCOMPLETE
```

Use actual evidence from Git history rather than forcing this wording.

---

# 11. Pre-model ownership decision gate

Combine Sections 9 and 10 into one explicit classification artifact:

```text
audits/08-maturity-as-of-ownership-decision.json
```

The decision must be exactly one of the following branches.

## 11.A `MODEL_OWNS_MEANINGFUL_DATE_SELECTION`

Proceed with M12CC only if historical/current contract evidence shows that selecting one same-row-owned date is itself a meaningful model-owned semantic choice.

Then:

```text
continue to schema complexity guard
→ model-facing representation audit
→ bounded prompt/schema contract hardening
→ deterministic freeze gate
→ wholly new full22 proof from call 1
```

Do not change the semantic rule merely to reduce implementation complexity.

## 11.B `DETERMINISTIC_PROVENANCE_FIELD`

If the audit shows that `as_of` is provenance metadata and the canonical row evidence already determines it, **stop before any model call and before changing the output contract in this task**.

Required result:

```text
MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
```

Required action:

```text
model_calls_started = 0
full22_generation = NOT_STARTED_BY_DESIGN
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_MIGRATION_DESIGN
```

Propose a separate bounded migration task that explicitly decides how to move the field from model-authored output to deterministic provenance without breaking downstream contracts.

Do not implement the migration inside M12CC.

## 11.C `HYBRID_REQUIRES_SEPARATE_POLICY_DECISION`

If some rows/use-cases require semantic model selection while others are deterministic provenance, or historical/downstream behavior does not establish a single owner, **stop before any model call**.

Required result:

```text
MATURITY_AS_OF_HYBRID_OWNERSHIP_POLICY_GAP
```

Required action:

```text
model_calls_started = 0
full22_generation = NOT_STARTED_BY_DESIGN
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_POLICY_DESIGN
```

Do not hide a hybrid semantic decision inside prompt wording, schema generation, or post-processing.

---

# 12. Existing date-validation rule and semantic boundary

Regardless of who semantically owns the field, the current deterministic validation rule remains frozen during M12CC:

```text
A driver_maturity.as_of value is valid when:
- it is a concrete YYYY-MM-DD date,
- at least one evidence ref cited in that same driver_maturity row owns that date,
- it is not later than assessment_date.
```

This is a **validation rule**, not proof that the model is the canonical semantic owner of the date.

If and only if Section 11 selects `MODEL_OWNS_MEANINGFUL_DATE_SELECTION`, preserve these consequences:

- Do not require the newest cited date unless the historical/current contract already does so.
- Do not require the oldest cited date.
- Do not automatically use `assessment_date`.
- Do not automatically use the batch maximum date.
- Do not automatically use `latest`.
- A symbolic source `latest/current/today` does not itself own a concrete date.
- If multiple same-row refs own different concrete dates, preserve the proven historical rule for model selection; do not invent newest/oldest preference.
- Do not change row supporting/contradicting evidence refs merely to make a chosen date valid.
- Do not change maturity classification merely to make a date valid.
- Do not mutate the frozen Fundamental Core.

If Section 11 selects B or C, do not reinterpret this validator rule as authorization to implement a model repair.

---

# 13. Mandatory schema complexity / size / runtime-support guard

**This guard must run before choosing schema-first enforcement.**

The current Stage-2 schema already carries substantial ref/date catalogs. Do not encode the cross-field relation through large `oneOf`/`anyOf` expansions without measuring cost and actual runtime support.

Required artifact:

```text
audits/09-schema-complexity-size-runtime-guard.json
```

Measure at minimum, per representative batch and for the worst/biggest frozen full22 batch:

```text
schema_bytes_before
schema_bytes_after_candidate_design
schema_growth_bytes
schema_growth_percent
oneOf_count_before
oneOf_count_after
anyOf_count_before
anyOf_count_after
total_branch_count_before
total_branch_count_after
ref_count
unique_owned_date_count
ref_date_pair_count
supporting_position_branch_count_if_applicable
contradicting_position_branch_count_if_applicable
model_prompt_bytes_before
model_prompt_bytes_after_candidate_design
model_schema_bytes_before
model_schema_bytes_after_candidate_design
combined_model_facing_bytes_before
combined_model_facing_bytes_after_candidate_design
historical_batch_max_schema_bytes
candidate_vs_historical_max_percent
structured_output_runtime_feature_support
structured_output_runtime_probe_result
maintenance_complexity_classification
```

Acceptance rule:

```text
schema-first is allowed only when:
- representation is compact,
- branch growth is bounded and maintainable,
- no combinatorial ref × date × supporting/contradicting expansion is required,
- the actual structured-output runtime supports every schema primitive used,
- the representation is generic across all 22,
- model-facing size remains within the established safe envelope.
```

Reject schema-first when any of the following is true:

```text
combinatorial explosion
unsupported/partially supported cross-field JSON Schema behavior
large duplicated ref/date branches
schema size materially exceeds historical safe maxima without strong justification
maintenance requires ticker-specific generated branches
supporting/contradicting positions must be exhaustively enumerated
```

Do not force complex relational policy into JSON Schema merely because schema rejection would occur earlier.

The deterministic same-row validator remains hard and unchanged either way.

---

# 14. Mandatory model-facing date representation audit

Only if Section 11.A applies, compare the available ways to make same-row ownership consumable by the model.

Required artifact:

```text
audits/10-model-facing-date-representation-audit.json
```

Compare at least:

### A. Global date enum + stronger prompt only

Current coarse shape:

```text
allowed_maturity_dates = batch-global concrete date set
```

Audit whether wording alone sufficiently communicates the ref/date relation. Do not assume it does: M12CB already proved the model can know the allowed date set yet miss same-row ownership.

### B. Evidence-local `resolved_as_of_date` made more explicit

Audit whether each evidence item can expose its canonical owned concrete date more directly/consistently without creating another owner.

### C. Compact `ref -> owned dates` model-facing catalog

Conceptually:

```text
maturity_date_ownership:
  decision-evidence:... -> [YYYY-MM-DD, ...]
```

It must be a deterministic projection of the existing canonical `maturity_ref_dates`, not a separately computed map.

### D. Ref-first deterministic candidate projection

Audit whether choosing refs first can yield a compact row-local set of allowed dates from the canonical map, without post-generation repair or a second semantic owner.

### E. Existing canonical mechanism discovered in Git history

Prefer reuse over any new representation if an existing canonical helper/mechanism already solves the model-consumption problem.

Selection criteria, recorded explicitly:

```text
deterministic ownership preserved
hallucination surface minimized
schema size minimized
prompt/context size minimized
generic across all 22
no ticker-specific logic
no hardcoded dates
no conflict with exact-ref contract
no second parser/source of truth
compatible with actual structured-output runtime
maintainable under future ref/date growth
```

Do not pick a mechanism solely because it makes the known `010120` case pass.

---

# 15. Conditional repair order — only for `MODEL_OWNS_MEANINGFUL_DATE_SELECTION`

M12CC is a contract-hardening task, not an instruction to blindly implement a predetermined mechanism.

After Sections 9–14 pass and only under branch 11.A, use this decision order.

## 15.1 Schema-level row-local ownership constraint — only if compact and runtime-supported

Determine whether the actual structured-output schema path can compactly express:

```text
for each driver_maturity row:
  emitted as_of date D
  must have at least one same-row supporting/contradicting evidence ref R
  where D is in canonical maturity_ref_dates[R]
```

Any schema constraint must be generated **only** from the existing canonical `maturity_ref_dates` mapping.

Do not hardcode ticker/date pairs.

Do not generate a large exhaustive expansion of:

```text
all refs × all dates × supporting/contradicting positions
```

If the schema complexity guard rejects this design, schema-first is forbidden for M12CC.

Required proof if schema-first is selected:

```text
M12CB invalid 010120 row/date pair => schema rejection
same row with 2026-08-12 => schema acceptance, only if that date is valid under the frozen semantics
global date owned only elsewhere => schema rejection for this row
schema guard = PASS
runtime support probe = PASS
```

The deterministic same-row validator remains defense in depth.

## 15.2 Preferred fallback — compact deterministic model-facing ownership projection + explicit prompt rule + hard validator

If schema-level cross-field enforcement is unsupported, non-compact, or materially increases complexity, do **not** force JSON Schema to encode it.

Expose the canonical relation more directly to the model using the winning representation from Section 14, typically a compact projection derived from `maturity_ref_dates` and/or existing evidence-local `resolved_as_of_date`.

Requirements:

- derived from the existing canonical owner,
- no second date parser,
- no second independent source of truth,
- no ticker-specific logic,
- no hardcoded `010120`/`2026-08-12` production rule,
- no assessment-date default,
- no latest/max-date default,
- no post-generation auto-correction,
- deterministic validator unchanged.

If useful, expose per-atomic-claim owned dates only as a **derived view** of the evidence-ref/date map. Atomic claims must not become a second source of date truth.

Strengthen prompt wording only enough to clarify the existing proven model-owned rule. Explicitly forbid batch-global normalization and unowned-date selection.

## 15.3 Forbidden repair paths

Do not:

- make `2026-09-15` valid for the failed row,
- add `010120` exceptions,
- add a `2026-08-12` production hardcode,
- add a per-date allowlist exception,
- remove or weaken `maturity_evidence_date_not_owned`,
- change `concrete_evidence_date(...)` semantics without a separately authorized task,
- silently replace invalid model `as_of` after generation,
- choose a date based on unrelated same-batch evidence,
- widen same-row ownership to same-ticker or same-batch ownership,
- default to `assessment_date`,
- default to newest/latest/max concrete date,
- invoke a repair model,
- retry a failed batch,
- use the existing production repair prompt as the proof mechanism,
- continue the M12CB generation after the failed batch,
- selectively rerun only `010120`,
- migrate `as_of` to deterministic ownership inside M12CC if Section 11.B is the result.

---

# 16. Date-failure diagnostic taxonomy

Preserve compatibility counters where needed, but add a precise detailed classification for every maturity date failure.

Required minimum taxonomy:

```text
NONCANONICAL_DATE
SYMBOLIC_TO_CONCRETE_FABRICATION
CONCRETE_BUT_UNOWNED_DATE
FUTURE_DATE
UNRESOLVABLE_DATE
SAME_ROW_NO_OWNING_REF
```

Definitions:

- `NONCANONICAL_DATE`: malformed/non-contract concrete representation or date not accepted by the canonical typed/date primitive contract.
- `SYMBOLIC_TO_CONCRETE_FABRICATION`: a symbolic/unresolved source is converted into a concrete date without a canonical owning ref.
- `CONCRETE_BUT_UNOWNED_DATE`: emitted date is concrete and may even exist in the batch/global catalog, but no evidence ref cited in that row owns it.
- `FUTURE_DATE`: emitted/owned date violates the frozen future-date rule relative to assessment date.
- `UNRESOLVABLE_DATE`: canonical evidence date cannot be resolved under the existing parser/contract.
- `SAME_ROW_NO_OWNING_REF`: row has refs but none supply an eligible concrete owner for the emitted/required date.

The M12CB `010120` incident is exactly:

```text
CONCRETE_BUT_UNOWNED_DATE
```

It is **not** `SYMBOLIC_TO_CONCRETE_FABRICATION`.

If an older aggregate counter such as a symbolic/fabrication bucket already includes this case, do not break compatibility by deleting it mid-task. Instead add the new detailed classification and report both the legacy aggregate behavior and the corrected detailed cause.

Required artifact:

```text
audits/11-maturity-date-diagnostic-taxonomy.json
```

---

# 17. Required deterministic fixtures

Before any new model call, add/confirm contrastive fixtures that prove the ownership and taxonomy contract.

Use generic fixtures. The historical `010120` case may be retained as a frozen regression artifact, but production logic must not depend on the ticker.

## Positive fixtures

### MDO-P01 — one same-row ref owns one date

```text
same-row ref R1 owns 2026-08-12
row.as_of = 2026-08-12
=> PASS
```

### MDO-P02 — multiple same-row refs own the same date

```text
R1 owns 2026-08-12
R2 owns 2026-08-12
row.as_of = 2026-08-12
=> PASS
```

### MDO-P03 — multiple same-row refs own different dates, only if historical contract proves model selection is allowed

```text
R1 owns D1
R2 owns D2
row.as_of = D1 or D2 according to the proven historical model-owned semantics
=> PASS
```

Do not include MDO-P03 as proof of model ownership by itself; it is only valid after Section 11.A is established independently.

## Negative fixtures

### MDO-N01 — assessment date is globally valid but same-row unowned

```text
assessment_date is in the global valid date set
same-row refs do not own assessment_date
row.as_of = assessment_date
=> FAIL
classification = CONCRETE_BUT_UNOWNED_DATE
```

### MDO-N02 — another ticker/ref owns a valid concrete date

```text
same-row R1 owns D1
another ticker/ref owns D2
row.as_of = D2
=> FAIL
classification = CONCRETE_BUT_UNOWNED_DATE
```

### MDO-N03 — global catalog contains date but same-row owner does not

```text
D2 in allowed_maturity_dates
same-row owned-date union excludes D2
row.as_of = D2
=> FAIL
classification = CONCRETE_BUT_UNOWNED_DATE
```

### MDO-N04 — symbolic/latest/current/padded date

```text
latest/current/today or padded symbolic representation
=> existing typed/date failure remains
classification = NONCANONICAL_DATE or SYMBOLIC_TO_CONCRETE_FABRICATION according to actual canonical path
```

Do not weaken the existing typed primitive contract merely to fit the new taxonomy.

### MDO-N05 — future date

```text
row.as_of > assessment_date
=> FAIL
classification = FUTURE_DATE
```

### MDO-N06 — unresolved evidence date

```text
no canonical concrete date can be resolved
=> FAIL
classification = UNRESOLVABLE_DATE or SAME_ROW_NO_OWNING_REF according to exact existing failure point
```

### MDO-N07 — unknown evidence ref

Unknown maturity refs remain hard failures under the existing exact-ref contract.

### MDO-N08 — ref/date pair arbitrarily swapped

```text
R1 owns D1
R2 owns D2
row cites only R1
row.as_of = D2
=> FAIL
classification = CONCRETE_BUT_UNOWNED_DATE
```

### MDO-N09 — no rejected-output canonicalization

The immutable M12CB bad row must remain invalid. Model-facing hardening may prevent recurrence; it must not reinterpret the historical invalid output as valid.

---

# 18. M12CB failed-output offline forensic replay

Use the immutable M12CB KR Stage-2 batch-2 output bytes as a regression source.

Do not edit the candidate.

Required pre-new-generation audit:

```text
ticker = 010120
failed driver = exact historical driver text
cited ref = decision-evidence:e3e0e73c7b80428e5459
owned date = 2026-08-12
emitted date = 2026-09-15
semantic validator = FAIL maturity_evidence_date_not_owned
detailed classification = CONCRETE_BUT_UNOWNED_DATE
source bytes modified = false
```

Then:

- Under branch 11.A, prove the selected model-facing contract exposes/constrains the canonical ownership relation without weakening the validator.
- Under branch 11.B or 11.C, preserve this replay as evidence and stop before model calls; do not implement an ad hoc model repair.

If schema-level enforcement is selected under 11.A, prove the historical invalid output is schema-invalid under the new schema.

If schema-first is rejected and the compact projection path is selected, prove the exact canonical mapping is present in generated model-facing context and that the deterministic validator still rejects the immutable historical output.

Do not label the historical output PASS.

---

# 19. Preserve maturity atomic-claim identity and polarity

The M12CB failure is not an atomic-claim identity failure.

Freeze:

```text
maturity_atomic_identity_failure_count = 0
maturity_same_atomic_claim_overlap_count = 0
maturity_unproven_source_overlap_count = 0
maturity polarity regression = PASS
```

Do not change supporting/contradicting claim-set semantics or polarity adapter logic as part of M12CC.

Date ownership hardening must not become a hidden maturity/polarity rewrite.

---

# 20. Preserve M12CB frozen-core claim-language repair

Required regression proof before model calls:

```text
M12CA immutable SNDK/TSLA/TSM replay = 3/3 PASS under trusted Stage-2 path
standalone full-candidate validator = still strict
Stage-2-owned exact numeric negative fixture = FAIL as expected
mutated frozen core = FAIL as expected
unsupported metric negative fixture = FAIL as expected
unknown ref negative fixture = FAIL as expected
```

No changes to exact-number regex or Stage-2-owned claim inventory are authorized.

---

# 21. Preserve GOOGL / preconfirmation / three-axis contract

Run the existing GOOGL regression before model calls.

Expected:

```text
BUY
PARTIAL
pre_confirmation_buy = true
new_buyer = WAIT
holder = HOLDABLE
timing = UNFAVORABLE
trusted Stage-2 validation = PASS
```

Also run the existing suites for:

```text
preconfirmation lifecycle
three-axis independence
postconfirmation maturity
maturity polarity
exact refs
Stage-2 typed contract
Fundamental Core batch identity
price/timing immutability
expectation/valuation ownership
business delta
```

Do not “fix” unrelated failures under this scope. Stop and classify if a new unrelated deterministic regression appears.

---

# 22. Market-context freeze

M12CC must not redesign Treasury or Kiwoom.

## Treasury frozen contract

```text
provider = FRED
nominal = DGS3 / DGS5 / DGS10 / DGS30
real yield = DFII10
breakeven = T10YIE
historical final renderer commit = 4407cd11a78579e11681b503b2d4e72ee3c3d60f
daily semantics = PASS
per-series as-of = PASS
bp-change regression = PASS
```

Run only the necessary regression proving M12CC did not alter it.

## Kiwoom frozen contract

```text
historical commit = 28f4f70700046f98d5d899ee491d3e5f45922e9a
KOSPI200 2026-09-01/02/03 replay = PASS
local LeadingMarket adapter = PASS
KOSDAQ150 historical actual fixture = NOT_VERIFIED
required live config names:
  KIWOOM_GATEWAY_URL
  KIWOOM_GATEWAY_API_KEY
  KIWOOM_GATEWAY_TIMEOUT_SECONDS
live gateway = unavailable/unconfigured
live read/order/modify/cancel = 0/0/0/0
authorized capability = READ_ONLY
```

Do not configure the gateway in M12CC.

No order permission is required or allowed.

---

# 23. Deterministic freeze gate before any model call

No model call may begin until all of the following are recorded and frozen:

```text
1. repository provenance audit
2. M12CB result integrity audit
3. M12CB target-scope freeze
4. current blocker forensic audit + detailed taxonomy
5. driver_maturity.as_of semantic ownership audit
6. Git-history/canonical-owner audit
7. explicit ownership decision = MODEL_OWNS_MEANINGFUL_DATE_SELECTION
8. schema complexity/size/runtime-support guard
9. model-facing date representation audit
10. implementation/reuse classification
11. same-row date ownership positive/negative fixtures
12. immutable M12CB failed-output replay
13. GOOGL regression
14. SNDK/TSLA/TSM M12CB-scope regression
15. maturity polarity/atomic-identity regressions
16. exact-ref/typed-contract regressions
17. full local pytest
18. Ruff
19. git diff --check
20. model-facing prompt/schema hash freeze
21. frozen US/KR input packet identity
22. exact new call plan
```

If the ownership decision is `DETERMINISTIC_PROVENANCE_FIELD` or `HYBRID_REQUIRES_SEPARATE_POLICY_DECISION`, stopping before model execution is the required behavior, not a failed gate.

If any other deterministic gate fails, stop before model execution.

---

# 24. Model-facing change classification

M12CC is allowed to change the **model-consumability of the existing date-ownership contract only under ownership branch 11.A (`MODEL_OWNS_MEANINGFUL_DATE_SELECTION`)**.

Under branch 11.B or 11.C, model-facing change count must remain zero and the task stops before model calls.

Classify every model-facing diff.

Allowed only when necessary:

```text
schema structural hardening to encode existing same-row date ownership
or
prompt/context representation that exposes existing canonical maturity_ref_dates more explicitly
```

Forbidden semantic changes:

```text
investment decision policy
three-axis policy
preconfirmation policy
maturity policy
Fundamental Core content/ownership
holder semantics
timing semantics
exact-ref policy
numeric-claim policy
expectation/valuation policy
business-delta policy
```

Report separately:

```text
model_prompt_contract_clarity_change_count
model_schema_contract_hardening_change_count
investment_semantic_policy_change_count
```

Expected:

```text
investment_semantic_policy_change_count = 0
```

Do not hide a semantic change under “schema hardening.”

---

# 25. New full22 reproof — no continuation

Only after deterministic freeze passes **and ownership branch 11.A has been proven**, create a wholly new generation ID.

Any model-facing prompt/schema/context change requires this wholly new generation from call 1.

Under branch 11.B or 11.C, do not create a generation ID and do not call the model.

Do not reuse:

```text
20260916-uskr22-m12cb-20260916T041207Z-dcaac603f11e
```

Start from call 1 with the same frozen US14/KR8 packet identities unless a deterministic identity check proves they are no longer the authorized frozen inputs. Any packet change must be classified before model execution; do not silently refresh facts under this bounded task.

Expected frozen packet SHAs from M12CB:

```text
US = 2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228
KR = 819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597
```

Use the established model/runtime configuration from the frozen proof unless the repository's canonical runner says otherwise.

M12CB used:

```text
model = gpt-5.6-sol
reasoning = xhigh
```

Do not introduce a second model, judge, fallback, repair model, or retry path.

---

# 26. Full22 proof discipline

When branch 11.A reaches model proof, the new proof must remain fail-closed. A new hard failure ends that generation; do not patch it in-place.

Required:

```text
retry = 0
fallback = 0
judge = 0
repair = 0
selective rerun = 0
per-ticker retry = 0
candidate patch = 0
cross-generation stitching = 0
```

Stop on the first new hard failure.

A batch rejected as a unit must remain rejected as a unit for proof accounting.

Do not salvage passing rows from a rejected batch.

Do not resume later batches after a hard stop merely to obtain coverage numbers.

---

# 27. Full22 acceptance requirements

For M12CC to call the message/model contract clean, all 22 tickers must pass the normal full pipeline in the new generation.

Required minimum:

```text
Fundamental Core = 22/22
Stage-2 schema/typed contract = 22/22
Stage-2 deterministic semantic validation = 22/22
maturity same-row date ownership violations = 0
maturity unresolved-date violations = 0
maturity future-date violations = 0
maturity atomic-identity violations = 0
exact-ref violations = 0
fabricated refs = 0
frozen-core ownership mutations = 0
Stage-2-owned numeric violations = 0
preconfirmation contract failures = 0
three-axis contract failures = 0
final composition = 22/22
```

The M12CB target tickers must also remain PASS:

```text
SNDK
TSLA
TSM
GOOGL
CORZ
RXRX
SKHY
IBM
```

Do not treat “010120 now passes” as sufficient. The proof target is full22 clean from call 1.

---

# 28. Specific `010120` regression dossier

Create a dedicated dossier containing at minimum:

```text
historical M12CB failed output hash
historical failed driver text
historical same-row refs
historical emitted as_of
historical owned dates
historical deterministic error
new-generation 010120 driver_maturity rows
new-generation same-row refs and owned dates
new-generation emitted as_of values
schema status
semantic status
whether any assessment-date normalization occurred
whether any batch-global date leakage occurred
```

Do not force the new generation to reproduce the same prose or maturity rows. The dossier is for contract verification, not output targeting.

---

# 29. Required global date-ownership audit

Across all new Stage-2 rows, emit a machine-readable audit with one record per `driver_maturity` row:

```text
ticker
driver
emitted_as_of
supporting_evidence_refs
contradicting_evidence_refs
owned_concrete_dates_by_ref
same_row_owned_date_union
emitted_date_owned
assessment_date
future_date
```

Required per-row detailed classification field:

```text
date_failure_classification =
  NONE |
  NONCANONICAL_DATE |
  SYMBOLIC_TO_CONCRETE_FABRICATION |
  CONCRETE_BUT_UNOWNED_DATE |
  FUTURE_DATE |
  UNRESOLVABLE_DATE |
  SAME_ROW_NO_OWNING_REF
```

Required aggregate fields:

```text
row_count
same_row_date_not_owned_count                # legacy-compatible aggregate if already present
noncanonical_date_count
symbolic_to_concrete_fabrication_count
concrete_but_unowned_date_count
future_date_count
unresolvable_date_count
same_row_no_owning_ref_count
assessment_date_without_owner_count
batch_global_only_date_count
```

For a clean full22 proof all hard-failure counts must be zero.

The historical M12CB `010120` failure must contribute to `CONCRETE_BUT_UNOWNED_DATE` in forensic reporting, not be mislabeled as symbolic fabrication.

---

# 30. Final message/model readiness decision

Readiness depends on the ownership branch.

If branch 11.A executes and the entire new full22 proof is clean:

```text
MESSAGE_MODEL_CONTRACT_READINESS = YES
```

If branch 11.A executes and a new hard blocker occurs:

```text
MESSAGE_MODEL_CONTRACT_READINESS = NO
```

If branch 11.B or 11.C stops before model calls:

```text
MESSAGE_MODEL_CONTRACT_READINESS = NOT_EVALUATED_BY_DESIGN
```

This is not a proof failure; it means canonical ownership must be resolved/migrated in a separate bounded task before another model proof is meaningful.

Do not expand M12CC scope mid-run.

---

# 31. Deployment remains forbidden even on 22/22 PASS

Even if M12CC achieves a clean 22/22 proof:

```text
main merge = 0
deployment = 0
production send = 0
real send = 0
production DB mutation = 0
warning mutation = 0
notification queue write = 0
scheduler mutation = 0
scheduler resume = 0
automatic monitoring resume = 0
remote push = 0 unless explicitly required only for the bounded work branch by an existing authorized workflow
```

Do not interpret 22/22 as authorization to deploy.

The user-authorized next sequence after a clean message/model contract remains:

```text
1. Kiwoom read-only gateway configuration / verification
2. current US/KR market + ticker message smoke
3. independent human judgment using only collected evidence
4. compare human judgment against AI result
5. decide deployment / automation separately
```

If M12CC passes, `next_scope` should point to step 1, not deployment.

---

# 32. Kiwoom next-stage boundary

M12CC must merely report Kiwoom status.

Expected current state:

```text
KIWOOM_GATEWAY_URL = unconfigured
KIWOOM_GATEWAY_API_KEY = unconfigured
KIWOOM_GATEWAY_TIMEOUT_SECONDS = available/configurable per existing contract
live gateway = unavailable
live calls = 0/0/0/0
```

Do not request order permission. Do not call order/modify/cancel.

If the live gateway is unavailable/unconfigured, report that state only. **Do not build a new connector, gateway implementation, or alternate live-data path inside M12CC.**

After clean M12CC full22, the next authorized architecture discussion in Chat is the bounded **read-only gateway configuration and verification** scope.

---

# 33. Required report artifacts

Produce a result bundle containing at least:

```text
artifact-manifest.json

audits/01-repository-provenance.json
audits/02-m12cb-result-integrity.json
audits/03-m12cc-scope-freeze.json
audits/04-m12cb-target-convergence-freeze.json
audits/05-m12cb-terminal-failure-forensic.json
audits/06-maturity-as-of-semantic-ownership-audit.json
audits/07-maturity-date-owner-provenance.json
audits/08-maturity-as-of-ownership-decision.json
audits/09-schema-complexity-size-runtime-guard.json
audits/10-model-facing-date-representation-audit.json
audits/11-maturity-date-diagnostic-taxonomy.json
audits/12-current-date-ownership-code-audit.json
audits/13-schema-capability-audit.json
audits/14-reuse-classification.json
audits/15-repair-decision.json
audits/16-model-facing-change-classification.json
audits/17-maturity-date-ownership-implementation.json
audits/18-same-row-owned-date-positive-fixture.json
audits/fixtures/mdo-p01-single-ref-single-date-pass.json
audits/fixtures/mdo-p02-multi-ref-same-date-pass.json
audits/fixtures/mdo-p03-multi-ref-different-owned-date-pass-if-model-owned.json
audits/fixtures/mdo-n01-assessment-date-global-valid-same-row-unowned.json
audits/fixtures/mdo-n02-other-ticker-ref-owned-date.json
audits/fixtures/mdo-n03-global-catalog-same-row-unowned.json
audits/fixtures/mdo-n04-symbolic-padded-typed-date.json
audits/fixtures/mdo-n05-future-date.json
audits/fixtures/mdo-n06-unresolvable-no-owner.json
audits/fixtures/mdo-n07-unknown-ref.json
audits/fixtures/mdo-n08-ref-date-pair-swap.json
audits/fixtures/mdo-n09-historical-bad-output-remains-invalid.json
audits/19-batch-valid-row-unowned-date-negative-fixture.json
audits/20-assessment-date-default-negative-fixture.json
audits/21-latest-date-default-negative-fixture.json
audits/22-symbolic-date-negative-fixture.json
audits/23-future-date-negative-fixture.json
audits/24-unknown-ref-negative-fixture.json
audits/25-multiple-date-semantics-regression.json
audits/26-m12cb-failed-output-offline-replay.json
audits/27-googl-regression.json
audits/28-sndk-tsla-tsm-regression.json
audits/29-maturity-polarity-atomic-identity-regressions.json
audits/30-exact-ref-typed-contract-regressions.json
audits/31-full-local-test-result.json
audits/32-ruff-diff-result.json
audits/33-model-contract-hash-manifest.json
audits/34-frozen22-input-identity-manifest.json
audits/35-new-full22-generation-manifest.json
audits/36-full22-call-plan.json
audits/<ownership-branch-stop-decision-if-applicable>.json
audits/<schema-complexity-measurements-by-batch>.json
audits/<detailed maturity-date taxonomy counts>.json
...
audits/<new full22 model artifact inventory>.json
audits/<global maturity date ownership audit>.json
audits/<per-ticker result matrix>.json
audits/<010120 regression dossier>.json
audits/<GOOGL dossier>.json
audits/<SNDK-TSLA-TSM dossier>.json
audits/<full22 reproof decision>.json
audits/<Treasury regression>.json
audits/<Kiwoom local regression/config status>.json
audits/<message-model-contract-readiness>.json
audits/<deployment-readiness>.json
audits/<next-scope-decision>.json
audits/<program-completion>.json
```

Numbering may continue according to the actual report generator, but preserve clear one-purpose-per-artifact auditability.

If ownership branch 11.B or 11.C stops the task before later audits/proof, still emit the corresponding required artifact stubs with an explicit status such as `NOT_RUN_BY_OWNERSHIP_BRANCH`; do not fabricate measurements or imply zero.

Include raw immutable inputs/outputs, prompt/schema/ref-catalog artifacts, hashes, and deterministic validation evidence sufficient to independently reproduce every reported count.

---

# 34. Program-completion required fields

Final `program-completion` must include at least:

```text
contract
origin_main_observed
base_documentation_sha
implementation_branch
work_instruction_commit
implementation_sha
final_local_sha
source_of_truth_priority
m12cb_result_zip_sha256
m12cb_result_integrity
m12cb_generation_id
m12cb_terminal_failure_classification
m12cb_terminal_failure_ticker
m12cb_terminal_failure_emitted_as_of
m12cb_terminal_failure_owned_as_of
m12cb_target_scope_convergence
m12cc_reuse_classification
maturity_as_of_semantic_ownership_classification
maturity_as_of_ownership_decision_evidence
maturity_as_of_model_ownership_design_gap
maturity_as_of_hybrid_policy_gap
maturity_date_owner_contract
schema_bytes_before_max
schema_bytes_after_candidate_max
schema_growth_percent_max
oneof_count_before
oneof_count_after
anyof_count_before
anyof_count_after
total_schema_branch_count_before
total_schema_branch_count_after
ref_date_pair_count_max
structured_output_runtime_feature_support
structured_output_runtime_probe_result
model_prompt_bytes_before_max
model_prompt_bytes_after_max
combined_model_facing_bytes_before_max
combined_model_facing_bytes_after_max
schema_complexity_guard_result
model_facing_date_representation_selected
model_prompt_contract_clarity_change_count
model_schema_contract_hardening_change_count
investment_semantic_policy_change_count
deterministic_validator_policy_changed
historical_bad_output_reinterpreted_count
assessment_date_default_count
latest_date_default_count
ticker_date_exception_count
focused_test_result
full_test_result
ruff_result
git_diff_check
frozen_us_packet_sha
frozen_kr_packet_sha
new_reproof_generation_id
full22_generation_status
ownership_branch_stop_reason
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output
wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count
per_ticker_retry_count
fundamental_core_valid_count
stage2_schema_valid_count
stage2_semantic_valid_count
maturity_row_count
maturity_date_not_owned_count
noncanonical_date_count
symbolic_to_concrete_fabrication_count
concrete_but_unowned_date_count
maturity_date_unresolvable_count
same_row_no_owning_ref_count
future_maturity_date_count
batch_global_only_date_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count
maturity_atomic_identity_failure_count
preconfirmation_flag_failure_count
preconfirmation_three_axis_violation_count
frozen_core_revalidation_false_positive_count
stage2_owned_exact_numeric_violation_count
googl_regression_status
sndk_regression_status
tsla_regression_status
tsm_regression_status
010120_regression_status
final_composition_valid_count
message_model_contract_readiness
market_context_readiness
kiwoom_adapter_status
kiwoom_gateway_configured
kiwoom_authorized_capability
live_read_order_modify_cancel_counts
treasury_local_regression_status
deployment_readiness
production_db_mutations
production_sends
real_send_count
scheduler_mutation_count
scheduler_resume_count
main_merges
deployments
remote_push_count
artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
top_level_result
next_scope
```

For any field not measured because a fail-closed stop occurred, report `NOT_MEASURED_*` explicitly rather than implying zero.

---

# 35. Success criteria

M12CC first succeeds or stops based on **Track 0 canonical ownership audit**. Full22 proof is conditional, not unconditional.

## Track 0 — canonical ownership determination

Required in all cases:

```text
semantic ownership audit completed
Git/canonical-owner audit completed
exactly one ownership classification selected
no ticker/date exception
no validator weakening
historical 010120 remains CONCRETE_BUT_UNOWNED_DATE
all already-passed M12CB/market-context contracts remain frozen
```

### Track 0A result — `MODEL_OWNS_MEANINGFUL_DATE_SELECTION`

Continue to Tracks A and B.

### Track 0B result — `DETERMINISTIC_PROVENANCE_FIELD`

The correct M12CC completion is a fail-closed design-gap stop:

```text
MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
model calls = 0
output contract migration = 0 in this task
next scope = bounded ownership migration design
```

Do not mark this as a model-proof failure.

### Track 0C result — `HYBRID_REQUIRES_SEPARATE_POLICY_DECISION`

The correct M12CC completion is a fail-closed policy-gap stop:

```text
MATURITY_AS_OF_HYBRID_OWNERSHIP_POLICY_GAP
model calls = 0
prompt/schema repair = 0 in this task
next scope = bounded ownership policy design
```

## Track A — contract repair, only under Track 0A

```text
existing canonical date owner reused
parallel date owner count = 0
same-row deterministic validator preserved
historical invalid output remains invalid
no ticker/date exception
no assessment-date/latest default
schema complexity guard completed before schema-first decision
schema-first used only if compact + maintainable + runtime-supported
model-facing representation selected by explicit A/B/C/D/E audit
all deterministic fixtures PASS
investment semantic policy change count = 0
```

## Track B — fresh full22 proof, only under Track 0A

```text
new generation from call 1
US14 + KR8 complete normally
22/22 Fundamental Core PASS
22/22 Stage-2 schema/typed contract PASS
22/22 deterministic semantic PASS
all maturity date ownership failures = 0
all exact-ref/fabrication failures = 0
all frozen-core ownership failures = 0
final composition = 22/22
retry/fallback/judge/repair/selective-rerun/per-ticker-retry/stitch = 0
```

Only then:

```text
MESSAGE_MODEL_CONTRACT_READINESS = YES
```

Still:

```text
DEPLOYMENT_READINESS = NO_BY_PHASE_BOUNDARY
```

because deployment requires the separately authorized Kiwoom/smoke/human-comparison sequence.

---

# 36. Failure handling

If the semantic ownership audit returns `DETERMINISTIC_PROVENANCE_FIELD`:

```text
stop before model-facing repair
stop before model calls
report MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
propose separate bounded ownership migration task
```

If it returns `HYBRID_REQUIRES_SEPARATE_POLICY_DECISION`:

```text
stop before model-facing repair
stop before model calls
report MATURITY_AS_OF_HYBRID_OWNERSHIP_POLICY_GAP
propose separate bounded ownership-policy task
```

If branch 11.A applies but a deterministic test/complexity/runtime gate fails before model calls:

```text
stop
classify root cause
no full22 generation
```

If a new full22 generation hits any hard failure:

```text
stop at first hard failure
no retry
no per-ticker retry
no repair
no selective rerun
no continuation
no stitching
no hotfix inside the same generation
```

Produce the complete forensic bundle for the failure and return to Chat for architectural review.

Do not silently broaden M12CC.

---

# 37. Expected next-scope decision

Use the ownership/proof branch, not a single unconditional next scope.

If Section 11.A is proven and M12CC full22 is clean:

```text
next_scope = BOUNDED_KIWOOM_READ_ONLY_GATEWAY_CONFIGURATION_AND_VERIFICATION
```

That next task must remain read-only and must not authorize order/modify/cancel capabilities.

If Section 11.A is proven but full22 is not clean:

```text
next_scope = exact bounded repair for the newly observed first hard failure
```

If Section 11.B is the ownership result:

```text
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_MIGRATION_DESIGN
```

If Section 11.C is the ownership result:

```text
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_POLICY_DESIGN
```

Do not move to Kiwoom until message/model contract readiness is clean under branch 11.A.

---

# 38. Final execution reminder

The key architectural boundary is:

```text
M12CB proved that validators must respect field ownership.
M12CC must first determine who canonically owns driver_maturity.as_of meaning.
Only if the model truly owns meaningful date selection should M12CC harden the model-facing typed-date contract and run full22.
```

Do not solve an ownership-design question by assuming the model must keep choosing the field.

Do not solve a model-consumability problem by weakening a correct validator.

Do not solve a cross-field relation with combinatorial JSON Schema expansion when a compact canonical projection is safer.

Do not solve a row-local ownership problem with a batch-global default.

Do not solve a generic contract problem with a ticker/date exception.

Do not deploy after full22 merely because it is green.

