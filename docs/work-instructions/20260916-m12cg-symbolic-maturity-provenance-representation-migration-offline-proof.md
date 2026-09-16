# Thesis Monitor — M12CG Symbolic Maturity Provenance Representation Migration + Offline Proof

## 0. Task identity and authorization boundary

Work-instruction filename:
`20260916-m12cg-symbolic-maturity-provenance-representation-migration-offline-proof.md`

Result bundle:
`thesis-monitor-20260916-m12cg-symbolic-maturity-provenance-representation-migration-offline-proof-report.zip`

This is a bounded **Branch A / R2 representation migration and offline compatibility proof** following the M12CF Chat review. It is not another ownership-policy discovery task, a model retry, or a Full22 run.

Chat-level decision for this task:

- Preserve semantically eligible symbolic-only maturity rows and their exact claims/refs.
- Keep the model from authoring `driver_maturity[].as_of` or `provenance_status`.
- Extend only the versioned normalized maturity representation to support a truthful null date plus runtime-derived provenance status.
- Preserve the M12CD concrete-date projection and its meaning.
- Prove candidate/accepted-plan/receipt/persistence/continuity compatibility offline before any new model generation.

External model calls: **0**. Full22 generations: **0**. Production mutations and sends: **0**.

R2 was selected by an architecture review; it has **not yet passed implementation, identity, or persistence compatibility proof**. M12CG must establish those facts, not assume them.

---

## 1. Authoritative inputs and repository provenance

For scope and authorization, this work instruction is the current Chat decision. For observed facts, use:

1. M12CF result ZIP and its concrete audit/code-history artifacts;
2. current repository state and Git history, explicitly compared to the frozen base;
3. M12CE immutable proof artifacts;
4. M12CD migration/offline artifacts and M12CB historical negative fixtures;
5. older handoffs only as historical context.

Do not let stale handoffs revive closed GOOGL or frozen-core numeric blockers. Do not treat current repository divergence as permission to change this scope.

### 1.1 Required M12CF source integrity

File:
`thesis-monitor-20260916-m12cf-symbolic-only-maturity-provenance-ownership-review-report.zip`

SHA-256:
`4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846`

Expected manifest: **46 declared payload artifacts**, plus the manifest itself. Verify ZIP CRC, every declared size/hash, missing entries, duplicates and unexpected payloads. The manifest's self-exclusion is intentional, not a missing artifact. Integrity failure => STOP.

### 1.2 Exact provenance from the M12CF snapshot

| Field | Value |
|---|---|
| repository | `sskim-ai/thesis-monitor` |
| origin_main_observed | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |
| m12cd_runtime_implementation_sha | `9a9bda729afcb0777d7228ee7151d31f0b2f84f8` |
| m12cd_final_local_sha | `6f87e8723cae359054335ee8fa92f5efca40047b` |
| m12ce_work_instruction_sha | `96a562d5cafc138a38a9592914e789e1159159e1` |
| m12ce_final_local_sha | `3938f2e17af74d79c210e9c1cfee2a128675414e` |
| m12cf_work_instruction_sha | `03c5d22db436b8b9d841efc991ede3b1aba62237` |
| m12cf_final_local_sha / required implementation base | `912b1ce6c46f0caf801b2c620b42d904b489c4e7` |
| observed M12CF branch | `codex/20260916-m12cf-symbolic-only-maturity-review` |

M12CF changed documentation only. Do not label its final local/docs SHA as the runtime implementation SHA. Record M12CG work-instruction commit, implementation freeze, final documentation commit, observed origin main and active production checkout separately. Do not invent a commit ID or rewrite historical reports to fix labels.

Create an isolated local M12CG branch/worktree from the required base, after recording clean state and checking Git history. Suggested branch: `codex/20260916-m12cg-symbolic-maturity-provenance-offline-migration`.

If HEAD has unexplained runtime changes or the required base cannot be verified, STOP with `M12CG_BASE_OR_SCOPE_DIVERGENCE`. Do not reset somebody else's worktree, merge main, push, or silently use a different implementation.

### 1.3 Historical proof inputs

M12CE report SHA-256:
`512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9`

M12CD report SHA-256:
`89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff`

M12CE terminal generation:
`20260916-uskr22-m12ce-20260916T080425Z-96a562d5cafc`

M12CE call-8 raw Stage-2 **batch** output SHA-256:
`6c8e80898904b44a710c00fdb3d918bf00a6edf757f1e2cc987d8d2fcb79455f`

This digest names the full MU/RXRX/SKHY raw batch, not a separately serialized SKHY candidate. Record hash scope accurately. Hash extracted candidates/rows separately when needed.

Resolve files from the verified bundle/actual repository paths. Historical `/tmp/...` strings in reports are provenance, not guaranteed live paths. Missing replay sources => report coverage gap and STOP; do not regenerate model outputs to fill gaps.

---

## 2. Closed M12CF decision and remaining proof obligation

M12CF result:
`M12CF_SYMBOLIC_PROVENANCE_ARCHITECTURE_REVIEW_PASS_BRANCH_A`

Ownership classification:
`SYMBOLIC_PROVENANCE_IS_VALID_NONDATE_STATE`

Chosen representation:
`R2_NULLABLE_AS_OF_WITH_DETERMINISTIC_PROVENANCE_STATUS`

M12CF found two symbolic refs in the US14/KR8 input snapshot, both on SKHY:

- `canonical:financial_quality:latest`: a real financial-quality limitation, eligible for the relevant maturity atomic claim;
- `canonical:earnings:latest`: a period placeholder used in unproven context, **not independently eligible for a maturity atomic claim in this snapshot**.

Both have intentionally unknown source periods. An observation/assessment timestamp elsewhere is not their financial-source-period owner. Producer concrete source dates available: 0; demonstrated producer date-ownership gaps: 0. Do not repair upstream dates or introduce a connector.

The failing SKHY row is decisive and `CONFIRMED` because the **limitation is confirmed**, not because financial results or financial health are confirmed. Preserve that distinction and the BEARISH atomic claim/polarity.

M12CF row-exclusion audit retained HOLD / WAIT / REVIEW, MIXED maturity and UNKNOWN pricing labels but lost a decisive maturity limitation. Stable top-level labels alone are not semantic preservation. Do not delete, suppress, downgrade, or reword this row to obtain validation success.

R2 hash classification is currently:
`HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION`.

This is an impact forecast from M12CF, not completed identity proof. M12CG must measure it through canonical runtime consumers.

---

## 3. Allowed changes and explicit exclusions

Allowed, only as required for R2:

1. Versioned normalized maturity row representation: nullable `as_of` plus deterministic `provenance_status`.
2. Existing deterministic materializer and its runtime-only canonical provenance projection.
3. Version-aware, hard same-row provenance/date validation and narrow parsing/serialization compatibility adapters.
4. Existing accepted-payload contract registration/version dispatch, with offline hash/receipt/persistence/continuity proof.
5. Tests, offline replay/audit harness, documentation and evidence artifacts.

Do not redesign investment decisions, claim eligibility, claim identity, polarity, Fundamental Core, source facts, source collection, timing, market context, numeric validation or Persistence V2 architecture.

No ticker-specific production logic, ref-literal allowlist added solely for SKHY, hardcoded dates, assessment/system/current/global/sibling/file-timestamp fallback, new primary evidence concept, model repair, schema repair call, row deletion, evidence substitution, or hash-preserving output rewrite.

This task may change the **versioned normalized symbolic boundary**. It must not globally make legacy dates nullable or skip ownership validation whenever a date is absent.

---

## 4. Reuse canonical owners before writing code

Inspect current files and Git history against the M12CF owner excerpts before implementing:

| Responsibility | Existing owner / search target |
|---|---|
| Financial fact producer | `app/services/ai_review_service.py`, `_fact_catalog` |
| Evidence projection | `app/services/cross_market_decision_engine_service.py`, `DecisionEvidenceRef` construction |
| Maturity row type | `app/services/evidence_maturity_pricing_service.py`, `DriverEvidenceMaturity` |
| Catalog/model schema/materializer | `app/services/accepted_decision_v2_runtime_service.py`, `accepted_v2_stage2_ref_catalog_manifest`, `accepted_v2_stage2_output_schema`, `materialize_accepted_v2_stage2_output` |
| Model-facing projections | `_stage2_model_facing_candidate_payload`, `_stage2_model_facing_rejected_output` |
| Hard date/ownership validator | `app/services/preconfirmation_decision_v2_service.py` |
| Candidate/accepted identities | `app/services/accepted_decision_v2_service.py`, `resolve_accepted_v2_decision` |
| Receipt identities | `app/services/canonical_acceptance_receipt_service.py` |
| Persistence/continuity/renderer | Trace actual canonical callers/readers; do not invent parallel implementations |

Record exact changed symbols, caller paths and version boundaries. Retain the existing concrete resolver / `resolved_as_of_date` / `maturity_ref_dates` chain as the source of concrete ownership.

A runtime-only symbolic classification is a deterministic projection of canonical producer metadata, not a new evidence owner. Use the existing canonical producer semantics/structured fields. Never infer valid symbolic provenance solely from `concrete_evidence_date(...) is None`, a `:latest` suffix, arbitrary free text, or a swallowed parse exception.

If an existing canonical implementation already supports R2, reuse it and prove its scope. If the required symbolic state cannot be distinguished safely from corrupt/missing provenance without inventing a new source policy, STOP with `AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY` and return to Chat.

---

## 5. Versioned normalized R2 contract

The model continues to own maturity meaning, decisive flags, claims and exact refs. Runtime owns both provenance fields.

### 5.1 Approved normalized fields and states

For the new normalized contract, both fields must be explicitly present:

- `as_of`: strict real-calendar `YYYY-MM-DD` string **or JSON null**, as determined below;
- `provenance_status`: exactly one of the following enum values.

| Canonical same-row evidence | `provenance_status` | `as_of` |
|---|---|---|
| At least one concrete date; no valid symbolic refs; all refs valid | `CONCRETE_ONLY` | MAX of concrete same-row owned dates |
| At least one concrete date and at least one valid symbolic ref; all refs valid | `CONCRETE_WITH_SYMBOLIC_REFS` | Same concrete MAX |
| At least one valid symbolic ref; no concrete dates; no invalid/unresolvable refs | `SYMBOLIC_ONLY_NO_CONCRETE_DATE` | JSON null |

A multi-concrete-date row with no symbolic participation is still `CONCRETE_ONLY`. Keep multiplicity as an audit subclassification, not a fourth runtime state.

The scalar meaning remains:
`LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`.

It is not a complete evidence cutoff, a recency guarantee, an observation date, or a financial event date selected by the model. In mixed rows the status explicitly signals incomplete concrete coverage. In symbolic-only rows null means no concrete date is owned by the cited provenance; it does not mean no evidence, ignored evidence, zero age or invalid investment meaning.

### 5.2 Exact row scope

Derive from the union of the row's `supporting_evidence_refs` and `contradicting_evidence_refs`, using the existing ticker-local ownership and visibility restrictions.

Do not silently widen scope to:

- `what_remains_unproven.evidence_refs`;
- other maturity rows or other candidate claims;
- the entire Fundamental Core;
- prior accepted/batch-global/catalog dates;
- another ticker's identical-looking ref ID;
- raw source metadata that the cited canonical evidence does not own.

Atomic-claim linkages still enforce the existing association between claims, refs and polarity. Adding truthful nullable provenance must not make an otherwise ineligible claim eligible.

### 5.3 Invalid is not symbolic

All cited refs must resolve within the candidate's ticker and approved canonical visibility. If any participating ref is unknown, cross-ticker, noncanonical, malformed, provenance-unresolvable, or has a producer-ownership ambiguity, fail closed—even when another ref supplies a valid concrete date.

A missing producer field, an invalid calendar date, padded `latest`, `current`, an arbitrary symbolic token, an absent evidence row or a placeholder without established canonical semantics must not be reclassified as valid symbolic provenance by this migration.

Use canonical producer state to recognize intentional nondate semantics. A legitimate symbolic ref's occurrence in `what_remains_unproven` does not automatically establish standalone maturity-claim eligibility. Preserve the earnings-placeholder boundary from Section 2.

### 5.4 Concrete cases stay strict

For concrete-only and mixed rows:

- reuse the M12CD MAX rule without alternative MIN/first/primary policy;
- require exact same-row ticker-local ownership;
- retain real-calendar/typed checks and assessment-cutoff future checks;
- no null, date coercion, default date or sentinel string;
- ensure the normalized v2 field equals the deterministic projection, not merely any owned date;
- keep legacy validation semantics version-scoped; do not retroactively reinterpret historical model-owned choices.

For symbolic-only rows, no arithmetic/comparison may treat null as today, an epoch, a minimum date or a future-safe sentinel.

---

## 6. Hard model-output boundary and schema guard

The existing raw Stage-2 contract is:
`v2-accepted-stage2-model-output-v2`.

Keep the model-facing schema/prompt/catalog and claim choices unchanged wherever possible. This migration is not authorization to make the model select a provenance representation.

Mandatory checks at the raw ingress boundary:

- any model-authored `as_of`, including JSON null, => hard FAIL;
- any model-authored `provenance_status`, even a correct status, => hard FAIL;
- presence must be rejected before normalization can overwrite/delete either value;
- current exact-ref, typed-string, batch identity, frozen-core and atomic-polarity gates remain active;
- unknown extra fields remain rejected.

If the model schema is generated from a normalized/shared type, remove both runtime-only properties from raw properties and `required` lists; keep additional-property rejection. Do not inadvertently expose the nullable date/state enum or their internal normalized contract metadata to the model via `$defs`, examples, previous candidates or rejected-output projections.

Inspect both existing model-facing projection helpers. Stripping runtime-owned fields when preparing a **new input projection** is allowed; stripping prohibited fields from **received model output** to accept it is not.

Measure before/after schema bytes, prompt bytes, relevant `$defs`, branch counts and catalog hashes using identical frozen inputs and batch identities. Prefer byte equality for the complete actual model-visible payload. No ref×date×supporting/contradicting schema expansion.

If a model-facing delta is genuinely unavoidable, document exact bytes and why before proceeding. A new prompt/schema semantic policy is outside M12CG: STOP for Chat review rather than opportunistically expanding the task. No model calls are permitted to test runtime support.

---

## 7. Normalization and legacy contract versions

The old normalization contract is:
`stage2-maturity-as-of-deterministic-v1`.

Use a distinct version for R2; suggested token, subject to repository collision checks:
`stage2-maturity-as-of-deterministic-v2`.

Record the actual canonical normalized-output/accepted-payload contract identifiers and dispatch points before patching. Do not relabel old payloads as the new version or change the raw model contract merely to conceal a normalized schema change.

Requirements:

1. Explicit version dispatch must occur before selecting the nullable normalized type.
2. Legacy payloads remain readable and validated under their original contract, without inserted status/null/default values changing their canonical bytes or hashes.
3. New normalized payloads require explicit provenance fields and context validation; absence is an error, not automatic legacy fallback.
4. A claimed version/status is not proof of trust. Preserve trusted finalization/issuer/receipt gates and independently recompute provenance from canonical evidence.
5. Old raw `010120` and terminal M12CE verdicts stay immutable.
6. Compatibility adaptation is restricted to clearly labeled ephemeral/offline new-version representations; never overwrite historical storage or replay evidence.
7. Existing date/primitive/numeric validators remain strict for legacy and unrelated fields.

Do not rely on a global `Optional[str]` plus default state as the complete migration. The discriminating version boundary and hard relational validation are mandatory.

If truthful version registration requires a broad Persistence V2 schema/identity redesign rather than its existing extension points, STOP with `MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT` and provide the narrow unmet dependency.

---

## 8. Deterministic materialization and independent validation

Within the canonical runtime path:

1. Verify raw contract, packet/claim/market/assessment identity, exact subject coverage and frozen-core ownership.
2. Reject model-authored runtime fields.
3. Resolve same-row refs in the ticker-local canonical evidence/ownership context.
4. Classify every ref using the canonical concrete resolver or demonstrated intentional symbolic producer semantics. Preserve ambiguous/invalid states as failures.
5. Derive concrete-date set, symbolic-ref set and R2 state.
6. Materialize exactly the state/date pair from Section 5 into a fresh normalized copy with the new contract.
7. Parse the versioned normalized type; independently validate exact refs, atomic polarity, state/date consistency, ownership, MAX projection and future cutoff against canonical context.
8. Continue through existing acceptance/render/persistence proof paths without altering semantic decision fields.

The validator must recompute expected provenance; it must not accept a candidate merely because it contains a permitted status string or because a materializer reported PASS. Reusing canonical resolver functions is correct; trusting supplied status/date as the authority is not.

Determinism includes: same input yields identical normalized bytes/hash/status; same row-local ref set yields the same scalar/state despite iteration order. Do not reorder stored model-authored ref/claim arrays to manufacture hash equality. Full candidate hash invariance under deliberately permuted input arrays is not required unless the existing serialization contract already promises it.

The current hard validator is extended only for the versioned symbolic representation. Do not implement a blanket `if row.as_of is None: continue` that skips ownership, eligibility, primitive or polarity checks.

---

## 9. SKHY semantic-preservation proof

Use the immutable M12CE US Stage-2 batch 3 and its matched frozen context/Core. Preserve the whole batch and row order. Preserve SKHY's five maturity rows; row 2 must remain decisive with the exact driver, `CONFIRMED` maturity, supporting/contradicting evidence and atomic claim refs, and `what_remains_unproven` content.

Expected R2 representation for this existing row:

```json
{
  "as_of": null,
  "provenance_status": "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
}
```

These are added runtime fields, not a replacement for the original row. Production logic must not match ticker `SKHY`, row index 2, Korean driver text, a particular hash, or literal ref ID to assign them.

Compare all semantic fields, not only labels:

- decision and directional balance;
- BUY/SELL drivers, decisive reason and claim text/ref identity;
- each driver maturity/decisive flag, atomic polarity and overall maturity;
- new-buyer/holder axes and rationale;
- pre-/post-confirmation flags and timing;
- factual safety, pricing UNKNOWN, expectation/valuation and why-not-buy reasons;
- BusinessDelta and persistence-eligible semantic content;
- accepted-plan semantic fields and renderer output.

Expected retained labels from M12CE: HOLD / WAIT / REVIEW, MIXED overall maturity, UNKNOWN pricing, LIMITED factual safety. These are fixture observations, never forced decisions for a future generation.

Keep R1 row deletion as a negative semantic-preservation control: even if a candidate validates and labels match, removal of the decisive limitation must be reported as semantic loss and cannot pass M12CG.

M12CE had no accepted normalized baseline for the failing row under v1. Label such comparisons `NOT_AVAILABLE_OLD_NORMALIZER_REJECTED`; compare unchanged raw semantic content and a documented offline control instead of inventing a prior accepted artifact.

---

## 10. Historical and fresh offline coverage

### 10.1 Correct inventory labels

Use the full M12CD historical row inventory, expected **62 rows**, and every available fresh M12CE raw Stage-2 row, expected **42 rows across three completed Stage-2 batches / nine subjects**.

Do not call all 62 historical raw rows valid. The M12CD row matrix includes the immutable `010120` row with old `2026-09-15` outside its cited ref's owned set `{2026-08-12}`. Separate:

- historical source-row validity under its original contract;
- M12CD ephemeral deterministic representation validity;
- new M12CG representation validity;
- positive/negative/control fixture membership.

This corrects reporting only; it does not reopen or rewrite M12CD.

Keep per-snapshot source SHA, candidate key, stable row ID and row index. Do not assume rows from different generations are unique or interchangeable. Reconcile membership, deduplicate only for explicitly labeled analytical views, and do not omit failing/control rows to meet a target count.

### 10.2 Required comparisons

For each historical row compare:

1. immutable original model-authored date and original verdict;
2. M12CD deterministic date under its already-approved concrete semantics;
3. M12CG date and provenance status.

M12CG date parity must be measured against **M12CD**, not conflated with older model-to-MAX differences already approved in M12CD. Concrete-only and mixed dates must remain unchanged versus that baseline. Mixed status becomes explicit.

Historical M12CD inventory contains two symbolic+concrete SKHY rows and no symbolic-only row. Fresh M12CE inventory contains 39 single-concrete, two multi-concrete and one symbolic-only row. Recompute rather than hardcode population counts.

For each row/candidate record:

- source file path/hash, generation, market, ticker and stable identity;
- exact supporting/contradicting refs and atomic claim refs;
- raw/ref provenance, concrete dates, recognized symbolic refs, invalid/unresolved refs;
- baseline normalized version/date, new version/date/status;
- validation result under each appropriate contract;
- field-level semantic/renderer/accepted-plan diffs;
- per-row serialization changes and per-candidate/plan/receipt hash changes at their actual scopes;
- continuity/dedupe outcomes and reasons.

Report candidate-level changes once per candidate, not once per row. A candidate hash repeated on five row records is not five independently changed candidates.

### 10.3 Full-universe review without new calls

Inventory the frozen US14/KR8 evidence inputs and existing claim eligibility catalogs. This is coverage review, not fresh model proof. Do not claim fresh KR or stopped US batches were run. Missing outputs remain NOT_RUN.

Offline replay may consume immutable old outputs as test inputs, clearly labeled `OFFLINE_MIGRATION_REPLAY_ONLY`. No replay output can be counted as a new model call, accepted Full22 subject, or reusable production proof checkpoint.

---

## 11. Hash, identity, receipt, persistence and continuity proof

Before enabling the new representation, inventory each canonical hash input and contract-version owner. A detailed impact plan must exist before patching; then verify it by executing canonical paths in isolated offline fixtures.

| Surface | Required treatment |
|---|---|
| Source packets and Fundamental Core SHA | Byte/hash neutral; no new field injected into Core |
| Raw Stage-2 output SHA | Immutable; no edit or normalization written back |
| Normalized candidate payload/hash | Versioned changes expected and traceable |
| Candidate decision ID | Recompute from actual new payload; never preserve old ID artificially |
| Accepted evidence fingerprint/decision ID/plan hash | Measure transitive changes and prove semantic-field equality |
| Canonical acceptance receipt / final composed candidate hash | Existing trusted issuer and serialization contracts remain authoritative |
| Persisted candidate / receipt binding | New bytes must match new hashes; old receipts cannot authenticate new bytes |
| Dedupe/idempotency/continuity | Measure actual behavior with versioned fixtures; no false semantic change or duplicate operational event |
| Renderer output | Neutrality must be proven, not inferred from label equality |
| Historical readers/replay bytes | Read originals without mutating bytes/identities or default-injecting status |

At minimum execute:

- legacy write/read/hash validation parity using immutable fixtures;
- new normalized candidate -> accepted plan -> trusted finalization/receipt -> offline persistence -> load/verify roundtrip;
- identical new input replay twice: deterministic IDs and idempotent behavior;
- old payload/receipt retained beside new payload/receipt: no overwrite, aliasing or cross-version authentication;
- swapping old/new payloads or editing null/status/ref/version/receipt hash: reject;
- unsupported/missing version and forged provenance status: reject;
- continuity across an intentional version change with unchanged investment semantics, including unchanged BusinessDelta;
- no duplicate send intent/state transition from metadata-only migration in the isolated test sink;
- realistic malformed status/date data fails before persistence acceptance.

Explicitly define which diffs are allowed: new provenance fields, documented representation-version metadata and the canonical transitive identity/hash fields. Do not whitelist broad subtrees or silently drop decision/rationale fields from semantic comparison.

Hash classification must be measured as one of:

- `HASH_NEUTRAL` for truly unaffected surfaces;
- `HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL` for measured neutral changes;
- `HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION` only when the required version/receipt/persistence/continuity tests pass;
- `HASH_CHANGE_BREAKS_IDENTITY_CONTRACT` => STOP.

If existing identity/dedupe behavior cannot accommodate R2 without an unapproved redesign, STOP with `MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT`. Do not suppress churn counters, invent a secondary identity system, reuse receipts, or strip status before hashing to force a PASS.

Production DB mutations remain 0. Temporary test databases/receipts must be visibly isolated and non-production.

---

## 12. Required positive and negative fixtures

Use generic fixture factories and parameterize across ticker/market identities, including US and KR. Named historical fixtures are evidence, not production conditions. All expected negative rejections count as successful negative tests, not as permission to repair their inputs.

### Positive

| ID | Fixture | Expected |
|---|---|---|
| P01 | One concrete same-row owner | Concrete MAX, `CONCRETE_ONLY`, PASS |
| P02 | Multiple refs owning the same date | Same date/state, PASS |
| P03 | Multiple distinct concrete dates | M12CD MAX parity, PASS |
| P04 | One concrete + recognized symbolic ref | Same concrete date, explicit mixed state, PASS |
| P05 | Multiple concrete + recognized symbolic refs | MAX concrete, explicit mixed state, PASS |
| P06 | Eligible recognized symbolic-only limitation | JSON null + symbolic-only state, PASS |
| P07 | Supporting and contradicting valid refs | Both participate in provenance; polarity unchanged |
| P08 | Duplicate/reordered traversal of an identical ref set | Date/state invariant; stored semantic arrays not silently reordered |
| P09 | Same producer semantics under different ticker/market fixtures | Generic behavior; no SKHY branch |
| P10 | Frozen historical mixed SKHY rows | M12CD dates unchanged; mixed status added |
| P11 | Frozen M12CE SKHY row and whole batch | No semantic row loss; nullable provenance only |
| P12 | Legacy positive fixture under old version | Old serialization/hash/validator behavior preserved |
| P13 | New-version persistence roundtrip and identical second replay | Valid binding and deterministic/idempotent behavior |

### Negative / boundary

| ID | Fixture | Expected |
|---|---|---|
| N01 | Raw model emits `as_of`, including null | Model ownership FAIL before materialization |
| N02 | Raw model emits `provenance_status` | Model ownership FAIL even when value is correct |
| N03 | New normalized payload omits date/status/version | Contract/primitive FAIL; no implicit downgrade |
| N04 | Concrete refs + null date | State/date mismatch FAIL |
| N05 | Symbolic-only refs + invented concrete date | Unowned derivation FAIL |
| N06 | Mixed refs mislabeled concrete-only, or concrete-only mislabeled symbolic | Provenance mismatch FAIL |
| N07 | Unknown/cross-ticker ref, including a ref-ID collision across tickers | Exact/ownership FAIL; no global lookup rescue |
| N08 | Valid concrete ref + invalid/unresolvable ref | FAIL; concrete sibling cannot hide invalid provenance |
| N09 | Unresolvable-only/empty evidence row | FAIL, not symbolic success |
| N10 | Malformed/padded symbolic, `current`, bad calendar date, arbitrary missing producer date | Existing typed/provenance FAIL; no recognized-symbolic coercion |
| N11 | Future concrete date, including mixed with valid symbolic | Existing future-date FAIL; no clamping or symbolic downgrade |
| N12 | Date belongs only to another row, `what_remains_unproven`, another ticker or global catalog | Same-row ownership FAIL |
| N13 | Owned but non-MAX new-version date | Projection mismatch FAIL; legacy contract remains separately tested |
| N14 | Ref/date/status/producer metadata pair tamper | Detected by canonical context/hash/ownership gates |
| N15 | `canonical:earnings:latest` placeholder promoted into an ineligible standalone maturity claim | Existing atomic eligibility FAIL; nondate validity does not grant eligibility |
| N16 | Skhy decisive limitation row removed to retain aggregate labels | Semantic-preservation FAIL even if normal validator passes |
| N17 | New candidate with old receipt or altered version/hash | Identity/persistence FAIL |
| N18 | Legacy payload with null inserted or default status injected | Old strictness or byte/hash parity FAIL |
| N19 | Literal string `"null"`, empty string, number or boolean as normalized date | Typed FAIL; only explicit JSON null allowed in symbolic state |
| N20 | Immutable historical `010120` wrong-date raw output | Remains invalid `CONCRETE_BUT_UNOWNED_DATE` under original contract |
| N21 | Frozen-core mutation / numeric exact claim authored by Stage-2 | Existing frozen gates FAIL unchanged |
| N22 | Invalid polarity/claim mapping or maturity status altered during migration | Existing atomic/semantic gates FAIL |

Replay the original M12CE raw output under old normalization to confirm its original no-concrete-date rejection. Replaying the same immutable raw bytes through the new version is allowed **only as a separately labeled offline migration proof**, not a revision of the old verdict.

For `010120`, keep original raw failure immutable. Only the separately labeled M12CD ephemeral model-free representation may be used as the new baseline; do not remove its bad date in-place or report original raw PASS.

---

## 13. Taxonomy and measurement integrity

Preserve old error codes for historical contracts. Add precise new audit/validation subclassification without renaming history:

- `SYMBOLIC_ONLY_ROW`;
- `SYMBOLIC_PLUS_CONCRETE_ROW`;
- `MULTI_CONCRETE_DATE_ROW`;
- `NO_CONCRETE_OWNED_DATE`;
- `UNRESOLVABLE_PROVENANCE`;
- `PRODUCER_DATE_OWNERSHIP_GAP`;
- `AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY`;
- `FUTURE_DERIVED_DATE`;
- `UNOWNED_DERIVED_DATE`;
- `PROVENANCE_STATUS_MISMATCH`;
- `MODEL_AUTHORED_PROVENANCE_FIELD`;
- `UNSUPPORTED_NORMALIZED_CONTRACT`;
- `MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT`.

In v1, the M12CE symbolic-only row remains a representation failure. In the approved v2 symbolic-only state, absence of a concrete date is descriptive, not by itself a failure. Unknown/unresolvable provenance is still a failure. Do not collapse these outcomes into a single missing-date counter.

Distinguish ref-counts, distinct-date counts, row-counts, candidate-counts, batches and completed external calls. Mixed symbolic classification counts may overlap only when explicitly declared as orthogonal dimensions.

---

## 14. Frozen successful contracts

Do not reopen:

- M12CB frozen-core numeric claim-language ownership-scope repair;
- standalone numeric validator strictness;
- GOOGL preconfirmation BUY contract and price-confirmation isolation;
- BUY/WAIT/HOLDABLE three-axis independence;
- maturity polarity/atomic-claim identity and eligibility;
- Fundamental Core exact batch identity, sufficiency and immutability;
- exact-ref fidelity and ticker ownership;
- typed primitives outside the explicit versioned R2 date/state change;
- frozen-core ownership;
- post-confirmation HOLD maturity;
- expectation/valuation separation;
- BusinessDelta semantic ownership;
- Persistence V2 trusted acceptance/receipt architecture;
- M12CD concrete MAX policy and known-concrete scalar meaning;
- Treasury restoration and Kiwoom local restoration.

A controlled accepted-payload version adapter within existing Persistence V2 extension points is in scope; redesigning Persistence V2, dedupe policy or the receipt authority is not. Any boundary conflict => STOP for Chat.

---

## 15. Market-context freeze and safety

### Treasury

- provider: `FRED`;
- nominal: `DGS3 / DGS5 / DGS10 / DGS30`;
- real: `DFII10`;
- breakeven: `T10YIE`;
- historical final renderer: `4407cd11a78579e11681b503b2d4e72ee3c3d60f`;
- daily / per-series as-of / bp-change semantics frozen.

### Kiwoom

- historical commit: `28f4f70700046f98d5d899ee491d3e5f45922e9a`;
- KOSPI200 2026-09-01/02/03 replay: PASS;
- local LeadingMarket adapter: PASS;
- KOSDAQ150 actual historical fixture: UNVERIFIED, not upgraded by this task;
- gateway presently unconfigured/unavailable; capability READ_ONLY only;
- config names: `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS`;
- never print secrets, configure a gateway, create a connector or request order permissions in M12CG;
- live read/order/modify/cancel: `0/0/0/0`.

No production sends, delivery intents, DB mutations, scheduler changes/resumes, main merges, deployments or remote pushes. Do not alter the operating checkout. Offline test-sink activity must be separately counted, never conflated with production delivery.

---

## 16. Execution order and freeze

1. Verify source bundles and exact base/clean state; record safety counters.
2. Inspect canonical owners, call paths and version extension points.
3. Inventory baseline schemas, source/fixture hashes and historical validity labels.
4. Write the narrow version/hash/identity impact plan and R2 invariants before runtime patching.
5. Implement only the approved representation/normalization/validation adapters plus tests.
6. Prove raw model-facing non-leakage and required positive/negative fixtures.
7. Replay all historical and completed fresh artifacts offline; produce semantic diff matrices.
8. Execute canonical identity/receipt/persistence/continuity roundtrips in isolated test storage.
9. Run frozen regressions, full suite, Ruff and `git diff --check`.
10. Freeze implementation SHA; produce final docs/report/manifest, recording the docs SHA separately.
11. STOP. No model invocation or Full22 in this task.

Normal red/green unit-test iteration is allowed within this approved implementation scope before final freeze. Expected negative-test rejection is not an unexpected blocker. A new unresolved source policy, semantic decision change, identity conflict or broader architectural dependency must return to Chat; do not silently expand implementation to remove it.

---

## 17. Required test evidence

M12CF documented baseline, corroborated by its bundled JUnit:

- focused: 198 passed / 1 skipped;
- full: 4064 passed / 63 skipped; two reported existing warnings;
- Treasury: 69 passed;
- Kiwoom local: 32 passed;
- Ruff and diff check: PASS.

Run the relevant suites in M12CG. Record command, exit code, test count, failures/errors/skips, log/JUnit path, implementation SHA and test isolation. New tests may increase counts; do not delete old tests or silently increase skips. Explain any legitimate count or warning changes.

Static inspection alone is insufficient for the new hash/receipt/persistence/continuity result. If an execution path cannot be exercised offline, classify it NOT_PROVEN and stop rather than equating expected neutrality with PASS.

---

## 18. Required result artifacts

Include at least the following JSON/MD/matrix artifacts, with supporting raw excerpts and logs sufficient to verify claims:

1. `source-bundle-integrity.json`
2. `repository-provenance.json`
3. `canonical-owner-and-call-path-audit.json`
4. `r2-versioned-contract-decision.json`
5. `symbolic-producer-classification-and-eligibility-audit.json`
6. `model-facing-schema-prompt-nonleakage-audit.json`
7. `raw-model-provenance-ownership-negative-tests.json`
8. `deterministic-provenance-materialization-matrix.json`
9. `hard-validator-state-date-ref-matrix.json`
10. `historical-fixture-inventory-and-validity.json`
11. `historical-m12cd-vs-m12cg-row-matrix.json`
12. `fresh-m12ce-offline-r2-replay-matrix.json`
13. `skhy-symbolic-row-semantic-preservation.json`
14. `mixed-concrete-symbolic-parity-audit.json`
15. `immutable-negative-fixture-audit.json`
16. `candidate-accepted-plan-hash-impact-matrix.json`
17. `legacy-reader-serialization-compatibility.json`
18. `receipt-persistence-version-roundtrip-proof.json`
19. `dedupe-idempotency-continuity-proof.json`
20. `semantic-diff-allowlist-and-results.json`
21. `renderer-neutrality-proof.json`
22. `positive-negative-fixture-results.json`
23. `frozen-contract-regression.json`
24. `treasury-regression.json`
25. `kiwoom-local-regression-config-status.json`
26. `focused-and-full-local-test-result.json` plus JUnit/logs
27. `ruff-diff-check.json`
28. `model-and-production-zero-call-audit.json`
29. `m12cg-go-no-go-decision.json`
30. `deployment-readiness.json`
31. `next-scope-decision.json`
32. `program-completion.json`
33. `artifact-manifest.json`

Every manifest entry needs relative path, byte size and SHA-256; manifest self-exclusion must be explicit. Hash whole ZIP separately and return its `.sha256`. Do not include credentials or executable network/repair scripts disguised as replay evidence.

---

## 19. Program-completion required fields

Report actual values; use NOT_RUN / NOT_PROVEN and a reason for unavailable evidence, never invented zeros.

### Provenance and contracts

`top_level_result`, `origin_main_observed`, `required_base_sha`, `m12cd_runtime_implementation_sha`, `m12cf_final_local_sha`, `m12cf_result_zip_sha256`, `m12cf_manifest_verified_count`, `m12cg_work_instruction_sha`, `m12cg_implementation_sha`, `m12cg_final_local_sha`, `raw_model_output_contract_before`, `raw_model_output_contract_after`, `normalized_contract_before`, `normalized_contract_after`, `accepted_payload_contract_before`, `accepted_payload_contract_after`, `chosen_representation`, `canonical_materializer_owner`, `canonical_validation_owner`, `symbolic_classification_owner`.

### Coverage and semantics

`historical_fixture_inventory_count`, `historical_source_validity_breakdown`, `historical_negative_fixture_count`, `fresh_raw_maturity_row_count`, `fresh_stage2_batch_count`, `fresh_stage2_subject_count`, `concrete_only_row_count`, `mixed_row_count`, `symbolic_only_row_count`, `unresolvable_row_count`, `m12cd_concrete_date_parity_failure_count`, `raw_semantic_field_change_count`, `driver_row_loss_count`, `atomic_claim_or_polarity_change_count`, `skhy_limitation_preserved`, `accepted_plan_semantic_change_count`, `renderer_change_count`, `historical_bytes_changed_count`, `immutable_010120_negative_result`, `m12ce_old_contract_rejection_result`, `m12ce_new_contract_offline_replay_result`.

### Model boundary, identity and compatibility

`model_facing_prompt_byte_delta`, `model_facing_schema_byte_delta`, `model_facing_catalog_hash_changed`, `model_authored_asof_negative_test_result`, `model_authored_provenance_status_negative_test_result`, `fundamental_core_sha_changed_count`, `raw_output_sha_changed_count`, `normalized_candidate_hash_change_count`, `candidate_decision_id_change_count`, `accepted_plan_hash_change_count`, `receipt_identity_change_count`, `hash_impact_classification`, `legacy_reader_hash_parity`, `new_version_roundtrip_result`, `same_version_idempotency_result`, `cross_version_receipt_isolation_result`, `representation_only_continuity_event_count`, `duplicate_operational_intent_count`, `identity_conflict_count`, `unsupported_version_rejection_result`.

### Safety and completion

`runtime_source_changed_files`, `external_model_call_count = 0`, `full22_generation_count = 0`, `retry_call_count = 0`, `fallback_call_count = 0`, `judge_call_count = 0`, `repair_call_count = 0`, `schema_repair_call_count = 0`, `selective_rerun_count = 0`, `per_ticker_retry_count = 0`, `production_sends = 0`, `production_delivery_intents = 0`, `production_db_mutations = 0`, `scheduler_resume_count = 0`, `main_merges = 0`, `deployments = 0`, `remote_pushes = 0`, `kiwoom_authorized_capability = READ_ONLY`, `live_read_order_modify_cancel_counts = [0,0,0,0]`, `focused_tests`, `full_tests`, `treasury_tests`, `kiwoom_tests`, `ruff`, `git_diff_check`, `m12cg_go_no_go`, `message_model_contract_readiness`, `deployment_readiness`, `next_scope`.

If gates fail before measurements, do not claim the success-expected zero semantic-change counters were measured. Keep explicit not-measured status.

---

## 20. Formal terminal outcomes

### PASS — offline representation migration proven

`M12CG_SYMBOLIC_MATURITY_PROVENANCE_REPRESENTATION_MIGRATION_OFFLINE_PASS`

Requires all of:

- exact base/source integrity and canonical owner reuse;
- R2 version dispatch and deterministic state/date relationship proven;
- raw model cannot author either runtime field;
- concrete/mixed M12CD date parity;
- SKHY symbolic-only evidence/decisive meaning preserved;
- placeholder eligibility not broadened;
- expected typed/ref/future/tamper negative failures retained;
- full fixture inventory and original validity labels reconciled;
- legacy hashes/readers preserved and new identity/receipt/persistence behavior demonstrated;
- no semantic, renderer, unintended continuity or duplicate operational-intent change;
- frozen contracts and local market regressions healthy;
- model/production counters zero.

Even then:

`message_model_contract_readiness = NOT_READY_PENDING_NEW_FULL22`

`deployment_readiness = NO`

### STOP — identity conflict

`MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT`

No broad identity redesign inside this task. Return exact failing path/fixture/diff and a bounded design proposal.

### STOP — semantics or ownership ambiguity

`AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY` or `M12CG_SEMANTIC_PRESERVATION_FAILED`.

No arbitrary symbolic recognition, row deletion, fallback or semantic override.

### STOP — other dependency/integrity/coverage failure

Report the exact failed gate with NOT_PROVEN downstream measurements. Do not report R2 compatibility PASS on the strength of the M12CF review alone.

---

## 21. Historical immutability and future proof policy

M12CE stays terminal at call 8. Do not run call 9, retry call 8, select SKHY, patch that generation or stitch it into another proof. Old raw files, generation verdicts and their hashes remain unchanged.

After M12CG offline PASS, return to Chat. Only a separately approved next task (provisionally M12CH) may start a wholly new US14/KR8 Full22 generation from call 1 under frozen new contracts. No prior-output reuse/stitch, retry, fallback, judge, repair, schema/candidate repair, selective rerun or per-ticker retry. A future hard failure terminates that generation; no in-generation patch.

This fresh proof is required even if raw prompt/schema bytes remain identical, because the normalized runtime representation and acceptance boundary have changed. Offline replay is not a substitute for that proof.

---

## 22. Post-task operating sequence

`M12CG bounded implementation + offline proof`

→ Chat review

→ separately authorized wholly new Full22 proof

→ Chat review

→ Kiwoom read-only gateway configuration/verification

→ Chat review

→ current US/KR market + monitored-stock message smoke

→ independent human judgment using collected facts only, before consulting the AI verdict

→ compare that judgment with the AI result

→ separate deployment/automation decision.

No M12CG or subsequent Full22 PASS automatically authorizes a main merge, deploy, scheduler resume, real send or broker write. Architecture and scope decisions stay in Chat; Work/Codex executes only this bounded scope and returns evidence for review.
