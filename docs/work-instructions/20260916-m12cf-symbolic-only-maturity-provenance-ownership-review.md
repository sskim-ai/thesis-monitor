# Thesis Monitor — M12CF Symbolic-Only Maturity Provenance Ownership Review

## 0. Task identity

Suggested work-instruction filename:

`20260916-m12cf-symbolic-only-maturity-provenance-ownership-review.md`

Suggested result bundle:

`thesis-monitor-20260916-m12cf-symbolic-only-maturity-provenance-ownership-review-report.zip`

This is a **bounded architecture/ownership review task** triggered by the first fresh-model proof under the frozen M12CD deterministic `driver_maturity.as_of` contract.

It is **NOT**:

- a prompt hotfix,
- a schema hotfix,
- a deterministic materializer patch,
- an `assessment_date` fallback task,
- a `latest`/current/system-date substitution task,
- a ticker-specific SKHY exception,
- an M12CE continuation,
- a selective rerun,
- a new Full22 model proof,
- a deployment task.

External model calls in M12CF: **0**.

The purpose of this task is to decide the canonical ownership and representation semantics of **symbolic-only same-row maturity provenance** before any further production/model contract migration is authorized.

---

# 1. Authoritative source-of-truth and repository provenance

Use this priority:

1. latest M12CE result bundle,
2. current repository state and Git history,
3. M12CD result bundle,
4. older handoff/state documents only for historical context.

Do not allow an older blocker to override the latest result.

Authoritative provenance entering M12CF:

- `origin_main_observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479`
- `m12cc_final_local_sha = b26022916f0bd2dea58dde71a9fddb41a844a9d4`
- `m12cd_work_instruction_sha = dbe40f4c9b5564660dab509d6534c8f9acbeb1b2`
- `m12cd_runtime_implementation_sha = 9a9bda729afcb0777d7228ee7151d31f0b2f84f8`
- `m12cd_final_local_sha = 6f87e8723cae359054335ee8fa92f5efca40047b`
- `m12ce_work_instruction_sha = 96a562d5cafc138a38a9592914e789e1159159e1`
- `m12ce_proof_runtime_base_sha = 6f87e8723cae359054335ee8fa92f5efca40047b`
- `m12ce_final_local_sha = 3938f2e17af74d79c210e9c1cfee2a128675414e`

M12CE result bundle SHA-256:

`512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9`

The M12CE result bundle must first be independently verified before any review work starts.

Expected M12CE manifest state:

- artifact count: `112`
- missing artifacts: `0`
- hash mismatches: `0`
- size mismatches: `0`

If this integrity check fails, STOP.

---

# 2. Current state and exact blocker

M12CD completed the deterministic ownership migration offline proof successfully.

Frozen deterministic contract entering M12CE:

- model output contract: `v2-accepted-stage2-model-output-v2`
- model does **not** author `driver_maturity.as_of`
- normalization contract: `stage2-maturity-as-of-deterministic-v1`
- candidate semantics: `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`
- candidate aggregation: `MAX_CONCRETE_OWNED_DATES`
- canonical materializer owner: existing M12CD deterministic materialization path
- assessment/global/current/latest/system-date fallback: forbidden
- cross-ticker ownership: forbidden
- unknown ref: fail closed
- future derived date: fail closed
- no concrete same-row owner: fail closed
- existing hard same-row validator remains authoritative

M12CE correctly started a wholly new generation from call 1 with no reuse/stitch/retry/repair.

Generation:

`20260916-uskr22-m12ce-20260916T080425Z-96a562d5cafc`

Observed proof state:

- planned model calls: `16`
- started: `8`
- completed: `8`
- usable outputs: `8`
- Fundamental Core accepted: `14`
- Stage-2 raw contract accepted subjects: `9`
- Stage-2 raw model-authored `as_of`: `0`
- Stage-2 exact-ref violations: `0`
- Stage-2 fabricated/unknown ref violations: `0`
- retry/fallback/judge/repair/schema-repair/candidate-repair/selective-rerun/per-ticker-retry/hotfix: all `0`

The first hard failure was:

`stage2_materialization_no_concrete_owned_date:SKHY:2`

Exact location:

- market: `us`
- Stage-2 batch: `3`
- model-call ordinal: `8`
- batch subjects: `MU / RXRX / SKHY`
- ticker: `SKHY`
- `driver_maturity` row index: `2`
- driver: `최신 재무자료의 품질 제약을 평가한다.`
- supporting claim ref:
  `maturity-claim:6c6ed446844ab5894c23baf4de0cb28428f2552c650f008790448e841220da57`
- supporting evidence ref:
  `canonical:financial_quality:latest`
- contradicting evidence refs: none
- concrete same-row owned dates: none
- materialized `as_of`: none

The canonical evidence packet for this ref contains:

- `ref_id = canonical:financial_quality:latest`
- `source_ref = stock.fact_catalog.financial_quality:latest`
- `as_of = latest`
- `source_period = null`
- `source_type = unknown`
- `state = unknown`
- reason codes include data-quality/provider/basis limitations

The ref is **allowed by the exact-ref contract** and is a real Fundamental Core / maturity-claim input. The model did not fabricate it.

The corresponding maturity atomic claim is also a real catalog member and is based solely on this symbolic ref.

Therefore classify the current issue as:

`SYMBOLIC_ONLY_MATURITY_PROVENANCE_REPRESENTATION_GAP`

Do **not** classify it as:

- model date hallucination,
- same-row wrong-date ownership,
- M12CD materializer bug,
- exact-ref failure,
- ticker-specific SKHY failure.

M12CE correctly failed closed and calls 9–16 were not run.

---

# 3. Required first principle

The question is **not** "what date can we substitute so this row passes?"

The question is:

> What does symbolic-only maturity evidence canonically own as provenance, and can/should the normalized `driver_maturity` representation express that state without inventing a concrete source date?

No repair is authorized until that is answered from Git history, producer semantics, consumer semantics, and existing canonical ownership contracts.

---

# 4. Mandatory Git/history and canonical-owner audit before any design decision

Before proposing any representation change, inspect Git history and current canonical owners for at least:

- `canonical:financial_quality:*` construction,
- `stock.fact_catalog.financial_quality:*`,
- evidence-packet `as_of` generation,
- `source_period` ownership,
- `resolved_as_of_date`,
- `maturity_ref_dates`,
- maturity atomic claim generation,
- Stage-2 exact-ref catalog generation,
- deterministic maturity materialization,
- hard maturity date validator,
- accepted-candidate schema,
- accepted decision plan construction,
- renderer,
- Persistence V2,
- candidate/plan hashing,
- dedupe/idempotency/continuity consumers.

For each relevant mechanism record:

- canonical owner/file/function,
- introduction commit if recoverable,
- current semantics,
- whether symbolic `latest` is intentional or accidental,
- whether a concrete observation timestamp/date exists elsewhere but is intentionally not used,
- whether the producer has enough information to resolve a true source-event/source-period date,
- whether downstream consumers distinguish source-period date from observation/run date.

**If an existing canonical mechanism already solves symbolic provenance, reuse it. Do not create a competing owner.**

---

# 5. Symbolic evidence population audit

Do not audit only SKHY.

Build a deterministic, model-free inventory across all currently available US/KR input/evidence packets and historical accepted artifacts for refs whose `as_of` or source period is symbolic/unresolved.

At minimum identify:

- ticker,
- market,
- ref id,
- source ref,
- evidence category/label,
- raw `as_of`,
- source period,
- source type,
- whether a concrete observation date exists elsewhere,
- whether `resolved_as_of_date` exists,
- whether it is eligible for Fundamental Core,
- whether it is eligible for maturity atomic claims,
- whether a maturity atomic claim can be symbolic-only,
- historical maturity-row usage count,
- fresh M12CE maturity-row usage count,
- whether it appeared alone or with concrete same-row refs,
- whether it was decisive.

At minimum classify each row/ref into:

- `CONCRETE_SOURCE_PROVENANCE`
- `SYMBOLIC_LATEST_NO_CONCRETE_SOURCE_PERIOD`
- `SYMBOLIC_WITH_CONCRETE_OBSERVATION_DATE`
- `UNRESOLVABLE_PROVENANCE`
- `PRODUCER_DATE_OWNERSHIP_GAP`

The historical M12CD audit observed zero symbolic-only valid rows and two symbolic+concrete rows. M12CE is the first fresh proof to surface a symbolic-only row. Preserve this distinction explicitly.

---

# 6. Producer semantics audit: source date vs observation date

For symbolic refs such as `canonical:financial_quality:latest`, determine whether the canonical producer logically owns any of these concepts:

1. **SOURCE_PERIOD_DATE**
   - the period/event date represented by the underlying financial evidence.

2. **OBSERVATION_DATE**
   - the date on which the system observed/derived the quality state.

3. **ASSESSMENT_DATE**
   - the batch/decision assessment date.

4. **SYMBOLIC_LATEST_STATE**
   - a deliberately non-concrete statement that no eligible concrete source period is available.

These are not interchangeable.

Forbidden substitutions:

- `latest -> assessment_date`
- `latest -> current date`
- `latest -> system date`
- `latest -> max ticker date`
- `latest -> nearest sibling evidence date`
- `source_period=null -> file timestamp`

unless Git/history proves that exact field is already canonically defined as that concept.

If the producer actually has a deterministic concrete **observation date** that is a distinct canonical concept, record it but do not silently treat it as a source-period date.

---

# 7. Consumer necessity audit for `driver_maturity.as_of`

Reconfirm, using code and historical artifacts, what downstream consumers need from this field.

Audit at minimum:

- final candidate serialization,
- accepted-plan construction,
- renderer text,
- persistence schema,
- candidate hash,
- accepted-plan hash,
- continuity/churn detector,
- dedupe/idempotency keys,
- message comparison logic,
- any monitoring scheduler/state transition logic.

Answer explicitly:

- Is a concrete ISO date mandatory because a real consumer uses it semantically?
- Is it mandatory only because of an old type/schema shape?
- Can the row be represented with no concrete date without changing investment semantics?
- Would nullable/optional/tagged provenance break identity contracts?
- Does removing a symbolic-only maturity row alter accepted-plan meaning or decision quality?

Do not infer necessity from the existing field type alone.

---

# 8. Required architecture classifications

After Sections 4–7, classify the symbolic-only case into exactly one primary category.

## Case A — SYMBOLIC_PROVENANCE_IS_VALID_NONDATE_STATE

Evidence state is valid and meaningful, but there is genuinely no concrete source date to own.

Implication:

- forcing a concrete date would fabricate provenance,
- representation must support a symbolic/no-concrete-date state if the row remains maturity-eligible.

## Case B — UPSTREAM_CANONICAL_PRODUCER_OWNS_CONCRETE_DATE

The current symbolic value is incomplete because an existing canonical producer already owns a valid concrete provenance date under the correct semantics.

Implication:

- fix belongs at that canonical producer/owner,
- not in Stage-2 prompt and not as a materializer fallback.

## Case C — SYMBOLIC_ONLY_MATURITY_ROW_IS_NOT_ELIGIBLE

The symbolic evidence is valid elsewhere in the decision system, but by historical/canonical contract a `driver_maturity` row requires at least one concrete-owned maturity evidence ref.

Implication:

- maturity claim/catalog eligibility may need a bounded change,
- but only if removing such rows does not erase a material fundamental risk or change decision semantics.

## Case D — AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY

Existing history/consumers do not establish one safe owner/representation.

Implication:

- STOP,
- propose a separate policy/representation design task,
- do not implement a speculative choice.

---

# 9. Candidate representation comparison

Do not preselect a winner. Compare at least the following candidates.

### R1. Keep mandatory concrete `as_of`; exclude symbolic-only maturity rows

### R2. Keep maturity row; allow `as_of = null` with explicit deterministic provenance status

Example conceptual status only, not pre-authorized schema:

- `CONCRETE`
- `NO_CONCRETE_SOURCE_DATE`

### R3. Replace scalar `as_of` with a tagged provenance object

Conceptually distinguish:

- concrete source date,
- symbolic latest/unresolved state,
- optional observation date if canonically owned.

### R4. Preserve scalar `as_of` but derive an existing canonical observation date

Only eligible if Git/history proves that observation date is already the correct semantic owner for this field.

### R5. Upstream canonical producer repair

Only eligible if the producer should already emit a concrete date under the existing source-date semantics.

### R6. No safe representation in current contract

Requires separate representation migration.

For each candidate score/document:

- provenance truthfulness,
- determinism,
- semantic fidelity,
- compatibility with concrete-date rows,
- support for symbolic+concrete rows,
- support for symbolic-only rows,
- historical compatibility,
- model dependency,
- order sensitivity,
- exact-ref compatibility,
- maturity atomic-claim compatibility,
- renderer impact,
- Persistence V2 impact,
- hash/identity impact,
- continuity/dedupe impact,
- implementation complexity,
- future extensibility,
- risk of hidden fallback semantics.

Do not invent a new `primary ref` concept.

---

# 10. Symbolic+concrete mixed-row semantics

The chosen architecture must also define mixed rows explicitly.

For a row containing:

- concrete ref A with date `D`, and
- symbolic ref B with no concrete date,

answer whether the normalized provenance means:

- latest known **concrete** same-row date only,
- complete evidence cutoff,
- multi-valued/tagged provenance,
- or no single scalar semantics.

Do not call `MAX(concrete_dates)` the absolute latest row evidence date when symbolic evidence is also present.

M12CD's current concrete projection may remain valid for concrete-bearing rows, but this review must state its exact meaning and limits.

---

# 11. SKHY semantic-preservation audit

Treat the M12CE SKHY row as an immutable case study, not as a special-case target.

The row expresses a real negative/limiting fact:

`최신 재무자료의 품질 상태가 미확인이라 실적의 지속성과 재무 내구성을 검증하기 어렵다.`

Audit whether removing this maturity row would materially change:

- overall maturity,
- decisive maturity composition,
- HOLD decision rationale,
- new-buyer WAIT rationale,
- holder REVIEW rationale,
- factual safety state,
- pricing requirement UNKNOWN state,
- `why_not_buy`,
- accepted plan semantics,
- rendered message.

If excluding symbolic-only rows suppresses a real decisive risk, classify R1 as semantically unsafe.

Do not modify the historical M12CE raw output.

---

# 12. Hash / identity / continuity impact audit

For each viable representation candidate determine the expected effect on:

- Fundamental Core SHA,
- Stage-2 raw output hash,
- normalized candidate hash,
- accepted-plan hash,
- persistence receipt/identity,
- dedupe/idempotency key,
- continuity/churn detector,
- renderer output,
- historical replay equality.

Use these classifications:

- `HASH_NEUTRAL`
- `HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL`
- `HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION`
- `HASH_CHANGE_BREAKS_IDENTITY_CONTRACT`

Any candidate classified `HASH_CHANGE_BREAKS_IDENTITY_CONTRACT` is not eligible for implementation in the next step without a separate identity migration design.

Never post-process hashes to preserve old equality.

---

# 13. Failure taxonomy

Preserve existing taxonomy and add audit sub-classification for this boundary.

At minimum distinguish:

- `NO_CONCRETE_OWNED_DATE`
- `SYMBOLIC_ONLY_ROW`
- `SYMBOLIC_PLUS_CONCRETE_ROW`
- `MULTI_CONCRETE_DATE_ROW`
- `UNRESOLVABLE_PROVENANCE`
- `PRODUCER_DATE_OWNERSHIP_GAP`
- `AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY`
- `FUTURE_DERIVED_DATE`
- `UNOWNED_DERIVED_DATE`

The M12CE SKHY failure must be recorded as at least:

- `NO_CONCRETE_OWNED_DATE`
- `SYMBOLIC_ONLY_ROW`
- architecture-level: `SYMBOLIC_ONLY_MATURITY_PROVENANCE_REPRESENTATION_GAP`

It is **not** `CONCRETE_BUT_UNOWNED_DATE`.

---

# 14. Formal stop/go branches

M12CF is review-only. No production runtime migration is authorized in this task.

End in exactly one design branch.

## Branch A — SYMBOLIC_PROVENANCE_IS_VALID_NONDATE_STATE

STOP before model call and before production runtime change.

Propose a bounded M12CG representation migration task using the best reviewed representation candidate.

## Branch B — UPSTREAM_CANONICAL_PRODUCER_OWNS_CONCRETE_DATE

STOP before model call.

Propose a bounded M12CG canonical-producer ownership repair + offline proof task.

Do not patch Stage-2.

## Branch C — SYMBOLIC_ONLY_MATURITY_ROW_IS_NOT_ELIGIBLE

STOP before model call.

Propose a bounded M12CG maturity eligibility/catalog repair + semantic-preservation offline proof.

Do not merely prompt the model not to choose the ref.

## Branch D — AMBIGUOUS_SYMBOLIC_PROVENANCE_POLICY

STOP.

Propose a bounded representation-policy design task before any code migration.

## Identity conflict override

If every viable candidate breaks identity contracts:

`MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT`

STOP and propose a dedicated identity migration design.

---

# 15. M12CE proof immutability

The M12CE generation is closed at the first hard failure.

Do not:

- continue call 9,
- rerun call 8,
- selectively rerun SKHY,
- patch the output,
- reuse calls 1–8 in a later proof,
- stitch a later generation onto this one.

The raw SKHY output SHA remains immutable:

`6c8e80898904b44a710c00fdb3d918bf00a6edf757f1e2cc987d8d2fcb79455f`

A future Full22 proof must be a wholly new generation from call 1.

---

# 16. Existing successful contracts remain frozen

Do not reopen or redesign:

- M12CB frozen-core numeric claim-language ownership scope repair,
- standalone numeric validator strictness,
- preconfirmation BUY contract,
- BUY/WAIT/HOLDABLE three-axis independence,
- maturity polarity atomic-claim identity,
- Fundamental Core batch identity,
- exact-ref fidelity,
- Stage-2 typed primitive contract,
- frozen-core ownership,
- post-confirmation HOLD maturity,
- expectation/valuation separation,
- BusinessDelta ownership,
- Persistence V2,
- Treasury restoration,
- Kiwoom local restoration,
- M12CD concrete-date deterministic materialization for rows where its preconditions are satisfied.

M12CF is specifically about the **symbolic-only boundary**.

---

# 17. Market-context freeze

## Treasury

Freeze:

- provider: `FRED`
- nominal: `DGS3 / DGS5 / DGS10 / DGS30`
- real: `DFII10`
- breakeven: `T10YIE`
- historical final renderer commit:
  `4407cd11a78579e11681b503b2d4e72ee3c3d60f`
- daily semantics: frozen
- per-series as-of semantics: frozen
- bp-change semantics: frozen

No Treasury redesign in M12CF.

## Kiwoom

Freeze:

- historical commit:
  `28f4f70700046f98d5d899ee491d3e5f45922e9a`
- KOSPI200 2026-09-01 / 09-02 / 09-03 replay: PASS
- local LeadingMarket adapter: PASS
- KOSDAQ150 actual historical fixture: still unverified
- live gateway capability: READ_ONLY only
- live gateway currently unconfigured/unavailable
- order/modify/cancel prohibited
- live read/order/modify/cancel counts remain `0/0/0/0`

If live gateway is unavailable, report that state only. Do not create a new connector.

---

# 18. Required tests and non-regression checks

Because M12CF is review-only, runtime source change count should normally be `0`.

Run enough local tests to prove the frozen base remains healthy, including at minimum:

- focused deterministic-as_of/maturity ownership tests,
- full local test suite,
- Ruff,
- `git diff --check`,
- Treasury regression,
- Kiwoom local regression.

Expected frozen baseline from M12CE:

- focused: `198 PASS / 1 skipped`
- full: `4064 PASS / 63 skipped / 2 warnings`
- Treasury: `69 PASS`
- Kiwoom: `32 PASS local`

If current repository state legitimately changes test counts for documentation-only reasons, explain precisely. Do not silently lower the bar.

---

# 19. Required artifacts

The result ZIP must include at minimum:

1. `m12ce-source-zip-integrity.json`
2. `repository-provenance.json`
3. `m12ce-hard-failure-reconstruction.json`
4. `symbolic-evidence-population-audit.json`
5. `symbolic-ref-producer-ownership-audit.json`
6. `source-date-vs-observation-date-semantics-audit.json`
7. `symbolic-maturity-claim-eligibility-audit.json`
8. `driver-maturity-asof-consumer-necessity-audit.json`
9. `symbolic-plus-concrete-semantics-audit.json`
10. `skhy-symbolic-row-semantic-preservation-audit.json`
11. `symbolic-provenance-representation-comparison-matrix.json`
12. `candidate-hash-identity-continuity-impact-audit.json`
13. `symbolic-provenance-failure-taxonomy.json`
14. `symbolic-provenance-canonical-owner-decision.json`
15. `m12cf-go-no-go-decision.json`
16. `full-local-test-result.json`
17. `ruff-diff-check.json`
18. `treasury-regression.json`
19. `kiwoom-local-regression-config-status.json`
20. `deployment-readiness.json`
21. `next-scope-decision.json`
22. `program-completion.json`
23. `artifact-manifest.json`

Include enough raw/code-history excerpts to independently verify the decision without modifying historical model outputs.

---

# 20. Program-completion required fields

At minimum record:

- `top_level_result`
- `origin_main_observed`
- `m12cd_runtime_implementation_sha`
- `m12cd_final_local_sha`
- `m12ce_work_instruction_sha`
- `m12ce_final_local_sha`
- `m12ce_result_zip_sha256`
- `m12ce_result_integrity`
- `m12ce_generation_id`
- `m12ce_model_calls_started`
- `m12ce_model_calls_completed`
- `m12ce_first_hard_failure`
- `m12ce_failure_ticker`
- `m12ce_failure_row_index`
- `m12ce_failure_ref`
- `symbolic_ref_count`
- `symbolic_only_maturity_claim_count`
- `historical_symbolic_only_maturity_row_count`
- `fresh_symbolic_only_maturity_row_count`
- `symbolic_plus_concrete_maturity_row_count`
- `producer_concrete_date_available_count`
- `producer_date_ownership_gap_count`
- `chosen_symbolic_provenance_classification`
- `chosen_representation_candidate`
- `hash_impact_classification`
- `skhy_row_semantic_loss_if_excluded`
- `runtime_source_change_count`
- `model_call_count = 0`
- `retry_call_count = 0`
- `fallback_model_call_count = 0`
- `judge_call_count = 0`
- `repair_call_count = 0`
- `selective_rerun_count = 0`
- `per_ticker_retry_count = 0`
- `production_sends = 0`
- `production_db_mutations = 0`
- `scheduler_resume_count = 0`
- `main_merges = 0`
- `deployments = 0`
- `kiwoom_authorized_capability = READ_ONLY`
- `kiwoom_gateway_configured`
- `live_read_order_modify_cancel_counts`
- `m12cf_design_branch`
- `next_scope`

---

# 21. Acceptance criteria

M12CF is PASS only if all are true:

1. M12CE source bundle integrity is independently verified.
2. The SKHY failure is reconstructed from immutable raw artifacts.
3. The review confirms it is a symbolic-only representation/ownership boundary, not a fabricated ref/date failure.
4. Git history and canonical producer ownership are audited before proposing a fix.
5. Source-period date, observation date, assessment date, and symbolic latest state are explicitly distinguished.
6. Symbolic ref population is audited beyond SKHY.
7. Maturity claim eligibility for symbolic-only refs is audited.
8. Downstream need for a concrete scalar `as_of` is proven rather than assumed.
9. At least R1–R6 representation candidates are compared.
10. SKHY semantic loss from excluding the row is explicitly measured/argued from artifacts.
11. Hash/identity/continuity impact is classified.
12. One of Branch A/B/C/D (or identity conflict override) is selected with evidence.
13. No model calls occur.
14. No M12CE proof continuation/rerun/reuse occurs.
15. Runtime/model contract is not opportunistically patched inside M12CF.
16. Frozen contracts remain unchanged.
17. Treasury and Kiwoom local regressions remain healthy.
18. No deployment/main merge/scheduler resume/production send occurs.

If the evidence cannot establish a safe owner/representation, **STOP is the correct result**.

---

# 22. Post-M12CF sequence

M12CF does **not** authorize a Full22 proof.

Expected sequence:

`M12CF architecture review`

→ Chat review of the result

→ bounded M12CG implementation/offline proof matching the selected branch

→ Chat review

→ wholly new Full22 generation from call 1 under the migrated frozen contract

→ Chat review

→ Kiwoom read-only gateway configuration/verification

→ Chat review

→ current US/KR market + monitored-stock message smoke

→ independent human judgment using collected facts only

→ compare human judgment with AI result

→ separate deploy/automation decision

Even a later Full22 PASS does not itself authorize deployment.

---

# 23. Final execution principle

Do not optimize for getting Full22 to pass.

Optimize for preserving truthful provenance ownership.

The M12CE failure is useful evidence that the deterministic concrete-date contract has reached a previously untested symbolic-only boundary. The correct response is to establish the canonical representation of that boundary before changing code or asking the model to behave differently.
