# Thesis Monitor — Stage-2 Maturity `as_of` Deterministic Ownership Migration + Offline Compatibility Proof

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-stage2-maturity-as-of-deterministic-ownership-migration-offline-proof.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-stage2-maturity-as-of-deterministic-ownership-migration-offline-proof-report.zip
```

Suggested phase name:

```text
M12CD — Stage-2 Maturity as_of Deterministic Ownership Migration + Offline Compatibility Proof
```

This is a **bounded ownership-migration design audit + conditional implementation + offline compatibility proof** task.

It is NOT:

- a new Full22 model proof,
- a prompt-tuning experiment,
- a decision-policy redesign,
- a maturity semantic redesign,
- a validator relaxation,
- a Treasury change,
- a Kiwoom connector task,
- a deployment task,
- a scheduler/notification task,
- a production send task.

**No model call is authorized in M12CD.**

The task first decides whether a safe scalar deterministic migration exists. If and only if the pre-implementation audits authorize Case A, it then implements and proves that migration offline. A correct fail-closed stop before implementation is an allowed M12CD result. A wholly new Full22 generation is a separate next phase only after an offline migration PASS.

---

## 1. Authoritative source-of-truth order

Use this precedence, highest first:

```text
1. M12CC result ZIP from this handoff
2. current repository state and Git history
3. M12CB result ZIP
4. M12CA result ZIP
5. older handoff/session documents
```

Do not revive older blockers from stale handoff files.

### M12CC authoritative result

The supplied M12CC report ZIP SHA-256 is:

```text
7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd
```

Expected M12CC conclusions:

```text
maturity_as_of_semantic_ownership_classification = DETERMINISTIC_PROVENANCE_FIELD
top_level_result = MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
full22_generation_status = NOT_STARTED_BY_DESIGN
model_calls_started = 0
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_MIGRATION_DESIGN
```

Before implementation, independently verify the supplied ZIP/hash/manifest and re-read at minimum:

```text
audits/06-maturity-as-of-semantic-ownership-audit.json
audits/07-maturity-date-owner-provenance.json
audits/08-maturity-as-of-ownership-decision.json
audits/12-current-date-ownership-code-audit.json
audits/14-reuse-classification.json
audits/38-m12cb-failed-output-offline-replay.json
audits/49-ownership-branch-stop-decision.json
audits/52-010120-regression-dossier.json
audits/58-message-model-contract-readiness.json
audits/61-next-scope-decision.json
audits/62-program-completion.json
```

If the authoritative M12CC bundle does not support the above, STOP. Do not infer or recreate the result.

---

## 2. Repository provenance

Record, do not reinterpret, the following known provenance from M12CC:

```text
origin_main_observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
m12cc_base_commit = 978eced97e80d3f1f5f896f53dd317088f4f4a41
m12cc_work_instruction_commit = 7766b29
m12cc_final_local_sha = b26022916f0bd2dea58dde71a9fddb41a844a9d4
m12cc_implementation_sha = NOT_APPLICABLE_OWNERSHIP_BRANCH_STOP
```

These values describe the M12CC result. They do not authorize assuming that current `origin/main` still equals the previously observed SHA.

At task start record:

```text
current HEAD
current branch
current origin/main
working-tree cleanliness
all relevant worktrees
unmerged/unpushed commits
```

If current repository state differs from the M12CC documented state, classify the difference before doing work. Do not silently reset, overwrite, rebase, or discard local work.

---

## 3. Frozen diagnosis

The following diagnosis is closed and must not be reopened in M12CD.

### 3.1 M12CB repair remains solved

The frozen-core numeric claim-language validation false positive affecting:

```text
SNDK
TSLA
TSM
```

was solved in M12CB. Do not change that repair.

### 3.2 M12CB terminal blocker was genuine

For ticker `010120`, the rejected M12CB row cited:

```text
decision-evidence:e3e0e73c7b80428e5459
```

Canonical owned date:

```text
2026-08-12
```

Model-emitted `driver_maturity.as_of`:

```text
2026-09-15
```

Detailed classification:

```text
CONCRETE_BUT_UNOWNED_DATE
```

This was a genuine model-output ownership violation, not a validator false positive.

The immutable historical M12CB output must remain invalid and unmodified.

### 3.3 M12CC ownership audit is authoritative

M12CC established:

- `driver_maturity.as_of` is historically model-authored;
- no production renderer treats the selected value as an investment judgment;
- no accepted decision plan uses the selected value as an investment judgment;
- no persisted accepted state uses the selected value as an investment judgment;
- no downstream decision policy was found that gives semantic meaning to choosing one owned date over another;
- canonical date ownership already exists through `concrete_evidence_date`, evidence-local resolved dates, `maturity_ref_dates`, and the same-row deterministic validator.

Therefore M12CD treats removal of **model authorship** as the architectural direction, but it must first prove whether the existing single scalar field has a safe deterministic meaning. It must not assume that `MAX` is that meaning.

---

## 4. M12CD design posture — deterministic ownership confirmed, scalar policy NOT pre-decided

M12CC established only the following ownership conclusion:

```text
driver_maturity.as_of ownership class = DETERMINISTIC_PROVENANCE_FIELD
```

M12CC did **not** prove that `MAX(concrete_owned_dates)` is the canonical scalar policy for every valid maturity row.

The M12CC result explicitly left the multi-date case unresolved:

```text
multiple_owned_dates_conclusion = representation ambiguity
multiple_owned_dates_semantic_policy_found = false
```

Therefore, in M12CD:

- removal of **model ownership** of `driver_maturity.as_of` remains the intended architecture direction;
- the scalar meaning and aggregation policy are **not** pre-authorized;
- `MAX(concrete_owned_dates)` is only a **candidate deterministic policy** until the historical/semantic/identity audits below pass;
- no production/model-facing contract change is allowed before the scalar go/no-go decision.

### 4.1 Candidate policy to test, not assume

The preferred candidate for compatibility and operational simplicity is:

```text
semantic meaning = LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE
aggregation = MAX(concrete same-row owned dates)
```

This candidate may become the migration rule only if all required historical, semantic, symbolic/unresolved, downstream, and identity checks prove it safe.

Do **not** describe this candidate as canonical before those checks pass.

### 4.2 No “make 010120 pass” objective

The target is not to derive `2026-08-12` merely because it fixes the known historical failure.

The immutable M12CB/M12CC negative fixture remains:

```text
ticker = 010120
cited ref = decision-evidence:e3e0e73c7b80428e5459
owned date = 2026-08-12
historical model-authored as_of = 2026-09-15
classification = CONCRETE_BUT_UNOWNED_DATE
```

That historical raw output remains invalid regardless of what scalar policy is eventually chosen.

---

## 5. Mandatory pre-implementation Git / canonical-owner audit

Before production/model-contract edits, inspect Git history and current canonical owners.

At minimum trace:

```text
DriverEvidenceMaturity
accepted_v2_stage2_output_schema
accepted_v2_stage2_ref_catalog_manifest
_compact_stage2_owned_evidence
concrete_evidence_date
resolved_as_of_date
maturity_ref_dates
validate_preconfirmation_candidate
validate_accepted_v2_stage2_candidate
AcceptedV2ProductionBatchOutput
model-response parse / structured-output entrypoint
historical artifact load/replay path
candidate serialization / hash / identity helpers
accepted-plan hash / receipt / dedupe helpers
continuity/churn detection
renderer input/output path
```

Record:

- existing owner/helper that can be reused;
- exact model-response normalization entrypoint;
- whether an existing raw-output normalization layer already exists;
- whether a second date parser/map would be introduced by a proposed design;
- historical contract/version assumptions;
- all hashes/fingerprints/receipts that include `driver_maturity.as_of` directly or indirectly;
- downstream consumers that read `driver_maturity.as_of`.

### Hard rule

If an existing canonical helper already owns evidence-date resolution, reuse or narrowly extend it.

Do not create:

- a second ISO-date parser;
- a second evidence-date source-of-truth;
- a ticker-specific date map;
- a shadow validator;
- a duplicate ref catalog;
- a new “primary evidence ref” concept merely to solve this task.

If migration cannot be implemented without creating a parallel canonical date owner, STOP with:

```text
MATURITY_AS_OF_MIGRATION_PARALLEL_OWNER_RISK
```

---

## 6. Historical Scalar Projection Audit — MUST precede implementation

Before changing the production/model-facing contract, reconstruct and audit the **entire historical valid `driver_maturity` row set identified by M12CC**.

The current M12CC report indicates:

```text
expected historical valid row count = 62
```

Treat `62` as the expected count from the authoritative report, not as a hardcoded production constant. Re-read the M12CC artifact and record the actual authoritative count used for the audit. If the count differs, explain the discrepancy and prove that the complete authoritative valid row set was used. Do not silently audit a subset.

### 6.1 Per-row required fields

For every historical valid row, record at minimum:

```text
ticker
row identity / stable row identifier
driver text or stable driver fingerprint
historical model-authored as_of
supporting_evidence_refs
contradicting_evidence_refs
same-row cited refs
resolved_as_of_date for each cited ref
distinct concrete owned dates
unresolved/symbolic cited refs
MIN(concrete_owned_dates)
MAX(concrete_owned_dates)
old_as_of == MIN
old_as_of == MAX
old_as_of in owned-date set
concrete distinct date count
concrete cited-ref count
unresolved/symbolic ref count
old_as_of > assessment_date
old_as_of resolvable / unresolvable
```

Do not infer ref dates from the historical model output itself. Resolve dates through the current canonical evidence/date owner and record any historical/current mapping discrepancy explicitly.

### 6.2 Required aggregate statistics

Compute and artifact:

```text
total historical valid rows
single-concrete-date rows
multi-distinct-concrete-date rows
symbolic-only rows
symbolic+concrete rows
old as_of == MAX count / ratio
old as_of != MAX count / ratio
old as_of == MIN count / ratio
old as_of != MIN count / ratio
old as_of not in owned-date set count
future-date rows
unresolvable rows
```

Also distinguish:

```text
one concrete ref / one date
multiple concrete refs / one shared date
multiple concrete refs / multiple distinct dates
```

### 6.3 Historical validity is not automatic policy evidence

A high `old_as_of == MAX` ratio is evidence about compatibility, not proof of semantics.

Likewise, many historical `old_as_of != MAX` rows do not prove that the old model-authored choice carried investment meaning.

Historical behavior and semantic ownership are separate questions and must be reported separately.

---

## 7. Multi-date row semantic necessity audit

Audit **every multi-distinct-concrete-date row** separately.

For each such row determine:

- why one maturity row cites evidence from multiple dates;
- whether the row is a maturity statement updated by newer evidence;
- which cited ref/date the historical model-authored `as_of` selected;
- whether the historical selection follows an observable deterministic pattern;
- whether it appears stochastic/order-sensitive;
- whether supporting vs contradicting position matters;
- whether any existing canonical concept marks one cited ref as decisive/primary;
- whether downstream consumers treat the historical selected date as identifying a particular source event rather than generic provenance/freshness metadata.

### 7.1 Hidden primary-evidence semantics stop

Do **not** invent a primary-ref concept.

If Git history/current code/artifacts prove that historical `as_of` functioned as the date of a specific existing canonical “primary” or “decisive” evidence ref, STOP before migration with:

```text
PRIMARY_EVIDENCE_DATE_SEMANTICS_FOUND
```

Then propose a separate bounded ownership/representation design task.

Do not convert that hidden semantic into `MAX` merely for determinism.

### 7.2 Random/stochastic historical selection

If historical model-authored choices vary among owned dates with no downstream semantic consumer and no canonical primary-ref concept, classify that as historical model-authored variability, not as evidence that model ownership should be preserved.

Still quantify the compatibility/churn impact before choosing a new deterministic policy.

---

## 8. Scalar projection candidate comparison matrix

Before implementation, compare at least these candidates:

```text
1. MIN(concrete owned dates)
2. MAX(concrete owned dates)
3. first cited concrete ref date
4. first supporting concrete ref date
5. decisive/primary ref date — ONLY if an existing canonical concept is proven
6. no scalar / representation migration
```

For each candidate record:

```text
determinism
semantic meaning
historical compatibility
order sensitivity
prompt/model dependency
provenance fidelity
downstream compatibility
implementation complexity
hash/churn risk
symbolic+concrete behavior
all-symbolic behavior
future-date behavior
same-row ownership guarantee
ticker-generic applicability
```

### 8.1 Candidate rules

- Do not prefer “first cited” merely because it is easy; citation order may be model stochasticity.
- Do not prefer MIN or MAX merely because one matches more historical rows.
- Do not create a “primary ref” field or heuristic unless it already exists canonically.
- `no scalar / representation migration` must remain a genuine option if every scalar projection loses required meaning.

Produce a human-readable comparison table plus machine-readable JSON.

---

## 9. Exact semantic definition audit

The field name `as_of` does not itself define the semantics. M12CD must explicitly choose one of the following, or stop.

### Option A — `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`

Definition:

```text
Use only concrete resolved dates owned by evidence refs actually cited in the same maturity row.
Unresolved/symbolic refs do not contribute a scalar date.
If at least one concrete owned date exists, candidate aggregation may use MAX(concrete dates).
```

Important wording:

This value means:

> the latest **known concrete provenance date** among same-row cited evidence.

It does **not** mean:

> the absolute latest time represented by every item of evidence in the row.

Therefore a row containing:

```text
ref A -> 2026-08-12
ref B -> unresolved/symbolic latest
```

may derive `2026-08-12` only if the field is explicitly defined as latest **known concrete** provenance.

### Option B — `COMPLETE_ROW_EVIDENCE_CUTOFF`

Definition:

```text
Every cited evidence ref must have a concrete resolved date.
If even one cited ref is unresolved/symbolic, no complete deterministic cutoff exists.
```

Under this meaning:

```text
symbolic + concrete -> FAIL_CLOSED
symbolic-only -> FAIL_CLOSED
```

An aggregation such as MAX is considered only after every cited ref is concretely dated.

### Option C — `NO_SINGLE_SCALAR_SEMANTICS`

Definition:

```text
A maturity row can legitimately contain multiple evidence dates whose provenance cannot be truthfully collapsed into one scalar without material information loss or semantic ambiguity.
```

If this is the correct interpretation, STOP M12CD implementation and propose a separate bounded representation migration task.

### 9.1 Candidate policy approval conditions

The preferred candidate:

```text
LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE + MAX(concrete owned dates)
```

may be approved only if **all** are true:

- `as_of` consumers use it only as provenance/freshness metadata, not an exact source-event selector;
- choosing MAX does not change downstream semantic decisions;
- symbolic+concrete behavior is documented without overstating “latest” semantics;
- historical compatibility audit shows no dangerous unexplained churn;
- multi-date audit finds no primary-evidence-date semantics;
- derivation is ticker-generic;
- only same-row cited ownership is used;
- no assessment/global/latest/current-date fallback exists;
- future dates cannot be manufactured or hidden;
- identity/hash impact is safe under Section 11.

---

## 10. Scalar policy historical-compatibility classification

After Sections 6–9, classify the candidate scalar policy as exactly one of:

```text
MAX_MATCHES_HISTORICAL_CANONICAL_BEHAVIOR
MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE
MAX_CHANGES_MATERIAL_HISTORICAL_BEHAVIOR
NO_SAFE_SCALAR_AGGREGATION_POLICY
```

### 10.1 Interpretation

`MAX_MATCHES_HISTORICAL_CANONICAL_BEHAVIOR`
- historical valid behavior, semantics, and downstream use support MAX as the already-observed canonical projection.

`MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE`
- MAX is not proven as the historical canonical rule;
- it is a **new versioned deterministic contract**;
- historical differences are measured and shown semantically safe/compatible.

`MAX_CHANGES_MATERIAL_HISTORICAL_BEHAVIOR`
- the new projection would materially change accepted semantics/renderer/continuity/identity behavior or create unacceptable churn.

`NO_SAFE_SCALAR_AGGREGATION_POLICY`
- no single scalar policy can be justified safely from current history/consumer semantics.

### 10.2 No majority-rule canonicalization

Do not classify as `MAX_MATCHES_HISTORICAL_CANONICAL_BEHAVIOR` merely because “most rows used MAX.”

The classification must combine:

- row-level historical evidence;
- multi-date semantics;
- downstream consumer semantics;
- symbolic/unresolved semantics;
- identity/hash impact.

---

## 11. Candidate hash / continuity impact audit — MUST precede implementation

Moving `as_of` from model output to deterministic derivation can alter normalized candidate serialization and hashes even when investment meaning is unchanged.

Audit at minimum:

```text
fundamental_core_sha256
Stage-2 candidate hash / candidate serialization hash
accepted plan hash
persistence receipt / persisted identity
artifact identity
ref-catalog identity/hash
dedupe / idempotency keys
continuity / churn detector
historical replay artifact equality
renderer output
message payload identity if applicable
```

For each, record:

- whether `driver_maturity.as_of` participates directly or indirectly;
- whether old vs candidate-new deterministic value changes bytes/hash;
- whether the comparison crosses contract versions;
- whether downstream code would misclassify contract-version churn as evidence/decision drift.

Classify overall impact as exactly one of:

```text
HASH_NEUTRAL
HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL
HASH_CHANGE_BREAKS_IDENTITY_CONTRACT
```

### 11.1 Hard stop

If:

```text
hash_impact_classification = HASH_CHANGE_BREAKS_IDENTITY_CONTRACT
```

STOP before implementation with:

```text
MATURITY_AS_OF_DETERMINISTIC_MIGRATION_IDENTITY_CONFLICT
```

Do not add hidden post-processing or hash exceptions merely to reproduce old hashes.

### 11.2 Fundamental Core freeze

`fundamental_core_sha256` should not change merely because Stage-2 `driver_maturity.as_of` ownership changes. If it does, treat that as a scope violation or explain the exact canonical dependency before proceeding.

### 11.3 Contract/version classification

Before implementation record at minimum:

```text
internal candidate contract changed? yes/no
persisted artifact contract changed? yes/no
model-facing Stage-2 schema hash expected to change? yes/no
model-facing prompt hash expected to change? yes/no
ref-catalog identity/hash changed? yes/no
normalization/materialization contract requires a new version? yes/no
legacy-vs-new contract identity comparison behavior
```

If the approved policy is `MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE`, it **must** be represented as a new explicit model-facing/normalization contract version following repository conventions. Do not pretend the new deterministic projection is byte-identical historical contract behavior.

For pre-implementation hash estimates, use ephemeral audit computation built from the existing canonical date owner. Do not introduce a production date owner merely to perform the audit.

---

## 12. Pre-implementation go / no-go branch

Only after Sections 5–11 are complete may M12CD decide whether implementation is authorized.

### Case A — bounded deterministic scalar migration authorized

Required combination:

```text
scalar_policy_classification in {
  MAX_MATCHES_HISTORICAL_CANONICAL_BEHAVIOR,
  MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE
}

chosen_scalar_semantics = LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE
chosen_scalar_aggregation = MAX_CONCRETE_OWNED_DATES
primary_evidence_date_semantics_found = false
hash_impact_classification in {
  HASH_NEUTRAL,
  HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL
}
```

Then, and only then, continue to the implementation sections below.

### Case B — primary evidence semantics found

If:

```text
PRIMARY_EVIDENCE_DATE_SEMANTICS_FOUND
```

STOP before production/model-contract edits.

Next scope:

```text
BOUNDED_MATURITY_PRIMARY_EVIDENCE_OWNERSHIP_REPRESENTATION_DESIGN
```

### Case C — no safe scalar semantics

If either:

```text
NO_SAFE_SCALAR_AGGREGATION_POLICY
NO_SINGLE_SCALAR_SEMANTICS
```

STOP before production/model-contract edits.

Next scope:

```text
BOUNDED_MATURITY_AS_OF_SCALAR_REMOVAL_OR_REPRESENTATION_MIGRATION_DESIGN
```

### Case D — identity/hash break

If:

```text
HASH_CHANGE_BREAKS_IDENTITY_CONTRACT
```

STOP before implementation with:

```text
MATURITY_AS_OF_DETERMINISTIC_MIGRATION_IDENTITY_CONFLICT
```

### Case E — candidate MAX materially changes historical behavior

If:

```text
MAX_CHANGES_MATERIAL_HISTORICAL_BEHAVIOR
```

STOP. Do not force a migration proof to PASS.

Produce a bounded follow-up design recommendation based on the exact cause.

### Case F — complete-row cutoff semantics selected

If the audit concludes:

```text
chosen_scalar_semantics = COMPLETE_ROW_EVIDENCE_CUTOFF
```

that is a meaningful policy result, but it is **not** authorized for implementation by Case A. STOP before contract edits with:

```text
MATURITY_AS_OF_COMPLETE_ROW_CUTOFF_REQUIRES_SEPARATE_DESIGN
```

and propose a bounded follow-up task that explicitly designs the all-refs-concrete requirement and its historical compatibility. Do not silently reinterpret it as Option A.

---

## 13. Conditional model-facing ownership migration — Case A only

This entire section is conditional on Case A.

### 13.1 Model no longer owns `driver_maturity.as_of`

For **new M12CD-and-later model outputs after Case A approval**:

```text
driver_maturity.as_of is NOT model-authored.
```

The model selects/produces the maturity row semantic fields and exact evidence refs. The runtime derives the scalar provenance metadata only after exact same-row refs are known.

The model must not be asked to choose, guess, copy, or emit `driver_maturity.as_of`.

### 13.2 Internal typed field

If the chosen safe migration preserves the existing internal field, keep:

```text
DriverEvidenceMaturity.as_of: YYYY-MM-DD
```

Do not remove the internal field merely because the model no longer emits it.

If the audits show that the internal field cannot remain without semantic/identity break, Case A was not satisfied; STOP instead of improvising.

### 13.3 Deterministic derivation — only after policy approval

For the approved Case A policy:

```text
same_row_refs = supporting_evidence_refs ∪ contradicting_evidence_refs
concrete_owned_dates = concrete canonical dates owned by those same-row refs only
derived_as_of = MAX(concrete_owned_dates)
```

Under the approved semantic definition, this means:

> latest known concrete same-row provenance date

It does **not** mean:

- assessment date;
- current date;
- absolute latest point in time represented by unresolved/symbolic evidence;
- batch-global latest date;
- ticker-global latest date regardless of citation;
- investment judgment;
- confidence/maturity/price-confirmation signal.

### 13.4 Symbolic behavior under Case A

If Case A chose `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`:

```text
symbolic/unresolved + >=1 concrete same-row owned date
→ symbolic refs excluded from scalar derivation
→ derive MAX of concrete same-row owned dates
→ classify row as SYMBOLIC_PLUS_CONCRETE_ROW for audit
```

If no concrete same-row owned date exists:

```text
FAIL_CLOSED
```

Never substitute assessment/global/latest/current dates.

---

## 14. Conditional model-facing schema and prompt migration — Case A only

### 14.1 Model-facing schema boundary

For the new Stage-2 model-facing schema:

- remove `as_of` from model-facing `DriverEvidenceMaturity.properties`;
- remove it from that model-facing definition's `required` list if present;
- preserve `additionalProperties: false` / structured-output strictness so the model cannot emit undeclared `as_of`;
- after valid raw model JSON returns, deterministically materialize `as_of` before constructing the existing internal typed candidate.

Do not:

- make `as_of` optional and model-authored;
- replace it with a free-form date string;
- leave it in the schema and silently overwrite model output.

### 14.2 Structured-output/runtime support

Audit the actual runtime/schema builder.

If safe nested property removal is unsupported, STOP with:

```text
MATURITY_AS_OF_MODEL_SCHEMA_MIGRATION_BLOCKED
```

Do not weaken strict structured output.

### 14.3 Model-facing prompt

Remove instructions telling the model to choose/emit `driver_maturity.as_of`.

Use concise ownership wording equivalent to:

```text
The runtime owns row-level provenance-date materialization from exact same-row cited evidence refs. Do not emit or infer driver_maturity.as_of. Select only valid exact evidence refs; provenance scalar derivation is not a model task.
```

Do not add a large new ref/date catalog just to compensate for removing the field.

---

## 15. Schema complexity / size guard — conditional implementation gate

Before accepting the Case A schema change, measure per batch fixture:

```text
schema bytes before / after
prompt bytes before / after
combined model-facing bytes before / after
oneOf count before / after
anyOf count before / after
total branch count before / after
ref/date pair count
structured-output runtime support
```

M12CC measured baseline maxima:

```text
schema_bytes_before_max = 60,934
prompt_bytes_before_max = 174,291
combined_model_facing_bytes_before_max = 235,225
ref_date_pair_count_max = 166
oneOf_count_before_max = 0
anyOf_count_before_max = 5
total_schema_branch_count_before_max = 10
```

Acceptance:

- no ref×date combinatorial expansion;
- no large new oneOf/anyOf cross-product;
- no ticker-specific schema branches;
- no duplicated ref/date catalog solely for `as_of`;
- strict runtime schema remains valid;
- removing model authorship should shrink or minimally change model-facing complexity.

If implementation unexpectedly grows the schema materially, explain and fail closed unless the growth is independently justified by the narrow contract.

---

## 16. Conditional deterministic materialization boundary — Case A only

Implement one narrowly scoped canonical materialization path for **new model outputs only**.

Conceptually:

```text
raw Stage-2 structured output
  -> strict schema-valid raw JSON without driver_maturity.as_of
  -> candidate/ticker identity checks sufficient to select the correct packet
  -> ticker-local same-row exact-ref lookup
  -> canonical resolved concrete dates for those refs
  -> chosen scalar semantic/aggregation rule
  -> inject deterministic as_of into an in-memory new-contract representation
  -> construct existing internal typed candidate
  -> existing ownership + semantic + typed validators
```

### 16.1 Ticker-locality is mandatory

Derive only from the candidate's ticker-local canonical evidence packet.

A ref/date from another ticker must never become a valid owner merely because it exists in the same batch.

### 16.2 Unknown/cross-ticker refs

If a cited ref is absent from that ticker's canonical visible evidence set, fail closed before successful materialization.

### 16.3 Future dates

Do not hide a future-dated canonical evidence defect.

If the chosen deterministic value is later than `assessment_date`, fail closed under existing future-date policy. Do not choose an older date to force passage.

### 16.4 Defense in depth

Keep the existing hard same-row validator.

After materialization it must still reject:

- tampered `as_of`;
- unowned date;
- future date;
- unknown maturity ref;
- no concrete same-row owner where the chosen semantic requires one.

The migration removes redundant model authorship; it does not weaken deterministic validation.

---

## 17. Historical compatibility and immutability

### 17.1 Historical raw outputs are immutable

Do not rewrite M12CB/M12CC or older model outputs.

The historical `010120` output with model-emitted `2026-09-15` remains:

```text
CONCRETE_BUT_UNOWNED_DATE
```

and must continue to fail unchanged replay/validation.

### 17.2 Historical persisted artifacts remain readable

Existing persisted artifacts containing valid historical `DriverEvidenceMaturity.as_of` must remain readable without mutation whenever the current repository already supports them.

Do not bulk rewrite stored artifacts or regenerate historical hashes.

### 17.3 Ephemeral migration proof only

For offline proof, create an **ephemeral copy** of historical semantic rows using the approved new-contract shape. Do not alter source bytes.

For the known `010120` negative fixture:

- original raw output remains unchanged and invalid;
- only the ephemeral new-contract copy omits model-authored `as_of`;
- its exact same-row refs remain unchanged;
- deterministic derivation is evaluated under the approved Case A policy;
- if Case A uses the preferred candidate, the target row derives `2026-08-12`.

Required counters:

```text
historical_source_bytes_modified = 0
historical_bad_output_reinterpreted_count = 0
historical_artifact_rewrite_count = 0
```

---

## 18. Old-vs-derived row-level offline comparison

If and only if Case A authorizes migration, replay the **entire historical valid row set** through an ephemeral new-contract representation and compare row-by-row:

```text
ticker
row identity
old model-authored as_of
new deterministic as_of
equal / different
same-row ownership validity before
same-row ownership validity after
semantic output difference
renderer difference
accepted-plan difference
candidate serialization/hash difference
accepted-plan hash difference if applicable
continuity/churn classification
```

### 18.1 Required aggregate results

Report at least:

```text
historical_valid_row_count
derived_asof_equal_count
derived_asof_different_count
accepted_plan_semantic_change_count
renderer_change_count
candidate_hash_change_count
accepted_plan_hash_change_count
continuity_churn_event_count
```

### 18.2 Goal of offline proof

The goal is **not** merely:

```text
validator PASS
```

The goal is:

> prove that moving provenance-date authorship from the model to deterministic runtime does not introduce unintended investment-semantic, renderer, accepted-plan, identity, or continuity changes.

Any semantic decision difference caused only by the scalar migration must be investigated and may invalidate Case A.

---

## 19. Diagnostic taxonomy

Preserve existing detailed date-failure taxonomy:

```text
NONCANONICAL_DATE
SYMBOLIC_TO_CONCRETE_FABRICATION
CONCRETE_BUT_UNOWNED_DATE
FUTURE_DATE
UNRESOLVABLE_DATE
SAME_ROW_NO_OWNING_REF
```

Add non-breaking audit sub-classification for M12CD:

```text
NO_CONCRETE_OWNED_DATE
SYMBOLIC_ONLY_ROW
SYMBOLIC_PLUS_CONCRETE_ROW
MULTI_CONCRETE_DATE_ROW
FUTURE_DERIVED_DATE
UNOWNED_DERIVED_DATE
AMBIGUOUS_SCALAR_SEMANTICS
```

These are audit/diagnostic subtypes. Do not remove legacy counters/names if other tooling expects them.

The historical `010120` case remains specifically:

```text
CONCRETE_BUT_UNOWNED_DATE
```

Do not relabel it as symbolic fabrication.

---

## 20. Required positive fixtures — conditional on Case A implementation

### MDO-MIG-P01 — one ref / one date

```text
same-row concrete owned dates = {2026-08-12}
derived as_of = 2026-08-12
PASS
```

### MDO-MIG-P02 — multiple refs / same date

```text
same-row concrete owned dates = {2026-09-15, 2026-09-15}
derived as_of = 2026-09-15
PASS
```

### MDO-MIG-P03 — multiple refs / different dates

This fixture is valid only after the chosen scalar semantics/aggregation is approved.

For Case A preferred policy:

```text
same-row concrete owned dates = {2026-06-30, 2026-09-15}
derived as_of = 2026-09-15
PASS
```

### MDO-MIG-P04 — symbolic + concrete

This fixture must follow the chosen semantic definition.

If:

```text
chosen_scalar_semantics = LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE
```

then:

```text
one cited ref unresolved/symbolic
one cited ref owns 2026-08-12
derived as_of = 2026-08-12
classification includes SYMBOLIC_PLUS_CONCRETE_ROW
PASS
```

If `COMPLETE_ROW_EVIDENCE_CUTOFF` were selected, this same fixture must fail closed instead; do not force it to pass.

### MDO-MIG-P05 — historical 010120 ephemeral new-contract copy

Original historical raw output remains invalid.

Under approved Case A preferred policy, the ephemeral copy with model-authored `as_of` omitted derives:

```text
2026-08-12
```

### MDO-MIG-P06 — stable deterministic bytes/hash

Run materialization twice with identical semantic raw output, same-row refs, evidence dates, contract version, and canonical context.

Normalized bytes/hash must be identical.

### MDO-MIG-P07 — historical row equality sample

Include at least one historical valid row where:

```text
old_as_of == new_deterministic_as_of
```

and prove no renderer/accepted-plan semantic change.

### MDO-MIG-P08 — historical row changed projection sample

If the historical audit contains any valid row where:

```text
old_as_of != new_deterministic_as_of
```

include a representative fixture proving the precise downstream/hash consequences and why the difference is semantically safe under the new versioned contract.

If no such row exists, record `NOT_APPLICABLE` with evidence.

---

## 21. Required negative fixtures

### MDO-MIG-N01 — model attempts to emit `as_of`

Under implemented Case A strict schema, reject undeclared model-authored `as_of`.

No silent overwrite.

### MDO-MIG-N02 — no concrete same-row owner

All cited refs unresolved/symbolic.

Must fail closed for the preferred Case A semantic. No assessment/global/latest fallback.

### MDO-MIG-N03 — valid batch-global date but no same-row owner

Must fail.

### MDO-MIG-N04 — other ticker ref/date

A ref/date valid elsewhere in the batch but not owned by this ticker/row must fail.

### MDO-MIG-N05 — future canonical/derived date

Must fail. Do not select an older date to mask it.

### MDO-MIG-N06 — unknown ref

Must fail exact-ref/ownership validation.

### MDO-MIG-N07 — post-materialization tamper

After correct deterministic materialization, mutate internal `as_of` to another globally valid but same-row-unowned date.

Existing hard validator must fail with `CONCRETE_BUT_UNOWNED_DATE` semantics.

### MDO-MIG-N08 — assessment-date fallback trap

Provide valid `assessment_date` but no permitted same-row concrete scalar.

Must fail, not derive assessment date.

### MDO-MIG-N09 — latest/max-global fallback trap

Provide other rows/refs with later globally valid dates.

A row lacking a valid same-row scalar source must still fail.

### MDO-MIG-N10 — historical original remains invalid

Replay unchanged M12CB `010120` raw output and prove historical `2026-09-15` remains rejected.

### MDO-MIG-N11 — unresolved semantics cannot be overstated

For:

```text
concrete ref = 2026-08-12
symbolic/unresolved ref = latest
```

prove the implementation/report never labels `2026-08-12` as an absolute complete-row latest cutoff when the chosen semantic is only latest **known concrete** provenance.

### MDO-MIG-N12 — no invented primary ref

A multi-date row with no existing canonical decisive/primary-ref concept must not trigger a newly invented “primary evidence” heuristic.

---

## 22. Regression freeze — do not reopen solved contracts

The following remain frozen unless a direct regression is caused by the narrow migration:

```text
frozen-core numeric claim-language scope repair
standalone numeric validator strictness
preconfirmation BUY contract
BUY / WAIT / HOLDABLE three-axis independence
maturity polarity atomic-claim contract
Fundamental Core batch identity
exact-ref fidelity
Stage-2 typed string/date primitive contract
frozen-core ownership
post-confirmation HOLD maturity
expectation/valuation ownership
BusinessDelta ownership
Persistence V2
Treasury restoration
Kiwoom local restoration
```

Required targeted regressions include at least:

```text
GOOGL preconfirmation regression
SNDK regression
TSLA regression
TSM regression
maturity atomic identity/polarity tests
exact-ref tests
frozen-core ownership tests
Persistence V2 relevant regressions
```

Do not redesign these systems to make M12CD easier.

---

## 23. Market-context freeze

### 23.1 Treasury

Freeze:

```text
provider = FRED
nominal = DGS3 / DGS5 / DGS10 / DGS30
real = DFII10
breakeven = T10YIE
historical final renderer commit = 4407cd11a78579e11681b503b2d4e72ee3c3d60f
```

Preserve:

```text
daily semantics
per-series as-of semantics
bp-change semantics
```

M12CD Treasury code changes must be `0`.

### 23.2 Kiwoom

Freeze:

```text
historical commit = 28f4f70700046f98d5d899ee491d3e5f45922e9a
KOSPI200 2026-09-01/02/03 replay = PASS
local LeadingMarket adapter = PASS
KOSDAQ150 historical actual fixture = NOT_VERIFIED
```

Required live config names remain:

```text
KIWOOM_GATEWAY_URL
KIWOOM_GATEWAY_API_KEY
KIWOOM_GATEWAY_TIMEOUT_SECONDS
```

Authorized capability:

```text
READ_ONLY
```

Forbidden:

```text
order
modify
cancel
new connector construction in M12CD
```

If live gateway is unavailable, report that state only.

Expected live counts during M12CD:

```text
read/order/modify/cancel = 0/0/0/0
```

---

## 24. Formal proof policy — M12CD remains model-call zero

M12CD covers only:

```text
ownership migration design
historical compatibility audit
scalar semantic/policy audit
deterministic derivation implementation if authorized
offline replay
hash / continuity proof
local regressions
```

External model calls are forbidden.

Required counts:

```text
planned model calls = 0
started model calls = 0
completed model calls = 0
usable model outputs = 0
retry = 0
fallback = 0
judge = 0
repair = 0
selective rerun = 0
per-ticker retry = 0
wrapper retry = 0
```

Do not start Full22 in M12CD, even if offline migration passes.

If M12CD reaches a stop branch before implementation, zero model calls remain the correct result.

---

## 25. Implementation boundaries

Potential narrow code areas remain:

```text
app/services/accepted_decision_v2_runtime_service.py
app/services/preconfirmation_decision_v2_service.py only if canonical helper reuse requires it
app/services/evidence_maturity_pricing_service.py only if canonical helper placement requires it
tests/test_accepted_decision_v2_runtime.py
tests/test_preconfirmation_decision_v2_service.py
```

This is not permission to edit all of them.

Edit only what the pre-implementation audits prove necessary.

Avoid broad renames and unrelated cleanup.

### Hard prohibitions

Do not:

- add `010120` special logic;
- hardcode `2026-08-12` in production code;
- predeclare MAX as canonical before the audits;
- derive from `assessment_date`;
- derive from current system date;
- derive from batch-global max date;
- derive from ticker-global max date if not cited in the same row;
- weaken same-row validator;
- remove future-date validation;
- accept unknown refs;
- silently overwrite a model-emitted `as_of`;
- invent a primary evidence ref concept;
- mutate historical artifacts;
- rebuild Treasury/Kiwoom;
- call external models;
- send production messages;
- merge main;
- deploy;
- resume schedulers;
- push remotely unless a later explicit instruction authorizes it.

---

## 26. Required execution order

Follow this exact order.

### Track 0 — provenance / authoritative-result verification

1. verify M12CC ZIP/hash/manifest;
2. record repository state;
3. inspect Git history/canonical owners;
4. identify the exact historical valid maturity-row source;
5. identify all `as_of` downstream consumers and hash/identity participants;
6. confirm no new evidence contradicts the M12CC ownership class `DETERMINISTIC_PROVENANCE_FIELD`.

If M12CC ownership classification is materially contradicted, STOP:

```text
MATURITY_AS_OF_MIGRATION_SEMANTIC_CONFLICT
```

### Track 1 — Historical Scalar Projection Audit

Audit the complete authoritative historical valid row set, currently expected to be 62 rows.

Emit row-level matrix + aggregates from Section 6.

No production/model-contract edits yet.

### Track 2 — multi-date / scalar semantics / policy comparison

1. audit every multi-distinct-date row;
2. test for hidden primary-evidence-date semantics;
3. compare MIN/MAX/first/first-supporting/existing-primary/no-scalar candidates;
4. decide Option A / B / C scalar meaning;
5. classify MAX historical compatibility.

No production/model-contract edits yet.

### Track 3 — hash / identity / continuity preflight

Audit Section 11 before implementation.

If `HASH_CHANGE_BREAKS_IDENTITY_CONTRACT`, STOP.

### Track 4 — scalar migration go/no-go

Emit one explicit branch decision from Section 12.

If not Case A, STOP M12CD implementation and produce the required bounded next-scope recommendation.

### Track 5 — conditional narrow implementation

Case A only:

1. remove model-facing `driver_maturity.as_of`;
2. update prompt ownership wording;
3. implement/reuse canonical deterministic materializer under the approved semantic policy;
4. normalize before internal typed candidate construction;
5. retain hard validator;
6. version/classify model-facing and normalization contract changes;
7. pass schema complexity guard.

### Track 6 — historical old-vs-derived offline proof

Case A only:

1. replay all historical valid rows using ephemeral new-contract copies;
2. compare old vs derived row-by-row;
3. compare renderer/accepted-plan semantics;
4. compare candidate/hash/continuity effects;
5. retain unchanged 010120 raw failure as negative fixture.

### Track 7 — fixtures / regressions / full local validation

Case A only:

Run:

```text
all required positive/negative migration fixtures
focused pytest
full pytest
Ruff
git diff --check
frozen contract regressions
Treasury regression
Kiwoom local/config regression
```

No model calls.

### Track 8 — final readiness decision

Possible success result:

```text
M12CD_RESULT = MATURITY_AS_OF_DETERMINISTIC_OWNERSHIP_MIGRATION_OFFLINE_PASS
MESSAGE_MODEL_CONTRACT_READINESS = NOT_REPROVEN_MODEL_CALL_REQUIRED
DEPLOYMENT_READINESS = NO_BY_PHASE_BOUNDARY
NEXT_SCOPE = M12CE_NEW_FULL22_REPROOF_UNDER_FROZEN_DETERMINISTIC_AS_OF_CONTRACT
```

Possible correct stop results include, but are not limited to:

```text
PRIMARY_EVIDENCE_DATE_SEMANTICS_FOUND
NO_SAFE_SCALAR_AGGREGATION_POLICY
NO_SINGLE_SCALAR_SEMANTICS
MATURITY_AS_OF_DETERMINISTIC_MIGRATION_IDENTITY_CONFLICT
MATURITY_AS_OF_MODEL_SCHEMA_MIGRATION_BLOCKED
MATURITY_AS_OF_MIGRATION_PARALLEL_OWNER_RISK
MATURITY_AS_OF_COMPLETE_ROW_CUTOFF_REQUIRES_SEPARATE_DESIGN
```

Do not force an offline PASS.

---

## 27. Acceptance criteria

M12CD may report **offline migration PASS** only if all are true.

### Audit / policy

- complete authoritative historical valid row set audited;
- multi-distinct-date rows audited individually;
- scalar-policy comparison matrix complete;
- no hidden primary-evidence semantics found;
- chosen scalar semantics explicitly defined;
- chosen scalar aggregation explicitly defined;
- scalar policy classified as `MAX_MATCHES_HISTORICAL_CANONICAL_BEHAVIOR` or `MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE`;
- symbolic/unresolved behavior explicitly defined;
- hash impact is `HASH_NEUTRAL` or `HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL`.

### Ownership / implementation

- model-facing schema does not expose `driver_maturity.as_of`;
- model prompt does not ask model to choose/emit it;
- deterministic materialization uses only ticker-local same-row cited canonical evidence;
- no assessment/global/latest/current fallback exists;
- existing hard same-row validator remains active.

### Historical compatibility

- historical artifacts are not rewritten;
- unchanged M12CB `010120` remains invalid;
- all historical valid rows receive row-level old-vs-derived comparison;
- accepted-plan semantic changes = 0 unless a separately proven contract-neutral representation-only difference is explicitly classified and accepted by the work instruction; default expectation is 0;
- renderer changes = 0 unless proven formatting-only and contract-neutral; default expectation is 0;
- identity/hash changes are classified and safe across contract versions;
- no old model-owned hash is silently reinterpreted as same-contract identity.

### Regression

- M12CB frozen-core scope remains PASS;
- GOOGL preconfirmation remains PASS;
- SNDK/TSLA/TSM remain PASS;
- exact-ref / maturity atomic / frozen-core contracts remain PASS;
- Treasury/Kiwoom frozen regressions remain PASS.

### Safety

- model calls = 0;
- retry/fallback/judge/repair/selective rerun/per-ticker retry = 0;
- production mutation/send = 0;
- scheduler changes = 0;
- main merge/deploy/remote push = 0.

A correct stop under Case B/C/D/E/F is **not** an offline migration PASS, but it is a valid fail-closed M12CD result.

---

## 28. Required result artifacts

Produce a result ZIP containing at minimum:

```text
artifact-manifest.json
```

and audits equivalent to:

```text
01-repository-provenance.json
02-m12cc-result-integrity.json
03-m12cd-scope-freeze.json
04-maturity-as-of-canonical-owner-reconfirmation.json
05-model-output-parse-boundary-audit.json
06-historical-scalar-projection-audit.json
07-historical-scalar-projection-row-matrix.json
08-multi-date-row-semantic-audit.json
09-scalar-policy-comparison-matrix.json
10-symbolic-concrete-semantics-decision.json
11-deterministic-asof-semantic-definition.json
12-scalar-policy-historical-classification.json
13-candidate-hash-continuity-impact-audit.json
14-scalar-migration-go-no-go-decision.json
15-model-facing-schema-before-after.json
16-model-facing-prompt-before-after.json
17-schema-complexity-size-guard.json
18-deterministic-materializer-implementation.json
19-ticker-local-ref-date-ownership-audit.json
20-contract-version-hash-compatibility.json
21-historical-artifact-compatibility.json
22-historical-old-vs-derived-asof-matrix.json
23-historical-old-vs-derived-summary.json
24-historical-010120-original-replay.json
25-historical-010120-new-contract-copy-replay.json
26-mdo-mig-p01-single-ref-single-date.json
27-mdo-mig-p02-multi-ref-same-date.json
28-mdo-mig-p03-multi-ref-different-date.json
29-mdo-mig-p04-symbolic-plus-concrete.json
30-mdo-mig-p05-010120-derived-date.json
31-mdo-mig-p06-deterministic-hash-stability.json
32-mdo-mig-p07-historical-equal-projection-sample.json
33-mdo-mig-p08-historical-changed-projection-sample.json
34-mdo-mig-n01-model-emitted-as-of.json
35-mdo-mig-n02-no-concrete-owner.json
36-mdo-mig-n03-global-valid-same-row-unowned.json
37-mdo-mig-n04-cross-ticker-ref-date.json
38-mdo-mig-n05-future-date.json
39-mdo-mig-n06-unknown-ref.json
40-mdo-mig-n07-post-materialization-tamper.json
41-mdo-mig-n08-assessment-fallback-trap.json
42-mdo-mig-n09-global-max-fallback-trap.json
43-mdo-mig-n10-historical-original-still-invalid.json
44-mdo-mig-n11-unresolved-semantics-labeling.json
45-mdo-mig-n12-no-invented-primary-ref.json
46-googl-regression.json
47-sndk-tsla-tsm-regression.json
48-maturity-polarity-atomic-regressions.json
49-exact-ref-typed-contract-regressions.json
50-persistence-v2-regression.json
51-full-local-test-result.json
52-ruff-diff-result.json
53-model-contract-hash-manifest.json
54-treasury-regression.json
55-kiwoom-local-regression-config-status.json
56-message-model-contract-readiness.json
57-deployment-readiness.json
58-next-scope-decision.json
59-program-completion.json
```

### 28.1 Conditional artifact handling on stop branches

If M12CD stops before implementation under Case B/C/D/E/F:

- still emit artifacts 01–14 and final readiness/next-scope/program-completion artifacts;
- implementation/fixture artifacts that are not legally reachable must be emitted as explicit `NOT_RUN_BY_BRANCH` records or omitted only if the manifest and program completion make the branch clear;
- do not fabricate PASS artifacts for work that was not run.

Include exact repository diffs/source snapshots/test outputs needed to verify any implemented Case A path.

---

## 29. Program-completion minimum fields

`program-completion.json` must include at least:

```text
contract
source_of_truth_priority
origin_main_observed
m12cc_final_local_sha
work_instruction_commit
implementation_sha
final_local_sha
m12cc_result_integrity
m12cc_result_zip_sha256
maturity_as_of_semantic_ownership_classification
historical_valid_row_count
single_concrete_date_row_count
multi_concrete_date_row_count
symbolic_only_row_count
symbolic_plus_concrete_row_count
old_asof_equals_max_count
old_asof_not_equals_max_count
old_asof_equals_max_ratio
old_asof_equals_min_count
old_asof_not_in_owned_date_set_count
future_date_row_count
unresolvable_row_count
primary_evidence_date_semantics_found
chosen_scalar_semantics
chosen_scalar_aggregation
scalar_policy_classification
hash_impact_classification
internal_candidate_contract_changed
persisted_artifact_contract_changed
model_schema_hash_expected_changed
model_prompt_hash_expected_changed
ref_catalog_hash_changed
normalization_contract_version
deterministic_migration_go_no_go
maturity_as_of_model_authorship_after
maturity_as_of_internal_field_preserved
maturity_as_of_materializer_owner
maturity_as_of_ticker_locality_enforced
maturity_as_of_no_owner_fallback_count
assessment_date_default_count
latest_date_default_count
global_date_default_count
ticker_date_exception_count
historical_source_bytes_modified
historical_bad_output_reinterpreted_count
historical_artifact_rewrite_count
historical_010120_original_status
historical_010120_new_contract_copy_derived_as_of
derived_asof_equal_count
derived_asof_different_count
accepted_plan_semantic_change_count
renderer_change_count
candidate_hash_change_count
accepted_plan_hash_change_count
continuity_churn_event_count
model_schema_as_of_property_present_after
schema_bytes_before_max
schema_bytes_after_max
schema_growth_percent_max
prompt_bytes_before_max
prompt_bytes_after_max
combined_model_facing_bytes_before_max
combined_model_facing_bytes_after_max
oneof_count_before/after
anyof_count_before/after
total_schema_branch_count_before/after
model_contract_hash_before/after
normalization_contract_version
fundamental_core_sha256_changed
focused_test_result
full_test_result
ruff_result
git_diff_check
preconfirmation_flag_failure_count
preconfirmation_three_axis_violation_count
frozen_core_revalidation_false_positive_count
stage2_owned_exact_numeric_violation_count
maturity_atomic_identity_failure_count
treasury_local_regression_status
kiwoom_adapter_status
kiwoom_gateway_configured
kiwoom_authorized_capability
live_read_order_modify_cancel_counts
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output
retry/fallback/judge/repair/selective_rerun/per_ticker_retry counts
production_db_mutations
production_sends
scheduler_mutation_count
scheduler_resume_count
main_merges
deployments
remote_push_count
message_model_contract_readiness
deployment_readiness
top_level_result
next_scope
```

On a pre-implementation stop branch, fields that depend on implementation must be explicitly `NOT_APPLICABLE_BY_BRANCH` / `NOT_RUN_BY_BRANCH` rather than guessed.

---

## 30. M12CE and deployment boundary

M12CD never performs Full22.

Only if M12CD ends in:

```text
MATURITY_AS_OF_DETERMINISTIC_OWNERSHIP_MIGRATION_OFFLINE_PASS
```

may a separate M12CE be authorized.

M12CE must use:

```text
wholly new Full22 generation
start from call 1
no prior output reuse
no stitch
retry = 0
fallback = 0
judge = 0
repair = 0
selective rerun = 0
per-ticker retry = 0
```

Even M12CE 22/22 PASS does **not** itself authorize deploy.

Required post-M12CE sequence remains:

```text
Kiwoom read-only gateway configuration / verification
→ current US/KR market + monitored-stock message smoke
→ independent human judgment using collected facts only
→ compare human judgment with AI result
→ separate deploy / automation decision
```

M12CD must leave:

```text
main merge = 0
deploy = 0
scheduler resume = 0
real send = 0
```

---

## 31. Final instruction to the execution session

Do not optimize for making `010120` pass, and do not optimize for proving MAX.

The correct sequence is:

```text
confirm as_of is deterministic provenance
→ audit all historical valid row scalar-selection patterns
→ determine whether one scalar is semantically justified
→ compare MAX / MIN / first / existing-primary / no-scalar
→ define symbolic+concrete semantics precisely
→ audit hash / continuity / identity effects
→ authorize or reject deterministic scalar migration
→ only if safe, implement removal of model ownership
→ prove old-vs-derived behavior offline across all historical valid rows
→ stop before model calls
→ separate M12CE Full22
```

The architectural invariant remains:

```text
MODEL chooses maturity semantics and exact cited evidence refs.
DETERMINISTIC RUNTIME owns provenance metadata only if a safe scalar representation is proven.
HARD VALIDATOR independently verifies same-row evidence ownership.
HISTORICAL RAW OUTPUTS remain immutable.
```

If no safe scalar representation is proven, that is a valid M12CD fail-closed result. Do not force a deterministic scalar merely because the field has historically existed.
