# Thesis Monitor — M12CG-R4-R1 Independent Frozen-Core Binding & Offline Closure

## 0. Decision: complete the existing R4 condition, not a new feature

This is a correction to the proof of **R4's existing independently validated frozen-Core condition**. It is not an entry/holder redesign, a new numeric policy, another symbolic migration, a delivery redesign, or a Full22 task.

The R4 executor reports `M12CG_R4_FINALIZATION_SCOPE_REPAIR_OFFLINE_CLOSURE_PASS`. Preserve that original result and its bytes. Chat verified the positive payload outcomes, but full closure remains pending at the independent-trust/negative-proof boundary. Do not rewrite R4 as either a failure or an accepted global PASS.

Work instruction: `20260917-m12cg-r4-r1-independent-core-binding-offline-closure.md`.
Result ZIP: `thesis-monitor-20260917-m12cg-r4-r1-independent-core-binding-offline-closure-report.zip` plus `.sha256`.

Authorize, in this order within the same bounded task:

1. Correct the offline harness so the reference Core comes independently from the immutable validated Core-stage source, not from the Stage-2 output being tested.
2. Prove the existing job and artifact-reader numeric allowance are anchored to that original Core or an already-existing applicable final-artifact authority. Keep the anchor fixed during adversarial output/artifact tests.
3. If those exact tests demonstrate a missing binding at an existing owner, implement only the minimal binding/wiring correction and its regressions. If the actual upstream owner already enforces the invariant, prove it and make no unnecessary runtime change.
4. Repair the specific F11/F17 and compound-fixture evidence mapping. Reuse the already repaired R3 aggregation contract; do not create another proof framework.

External model calls **0**; Full22 generations **0**; production mutations/sends **0**. Ordinary isolated offline tests and existing test-sink invocations are permitted. Return to Chat before any fresh model proof.

## 1. Source integrity and local base

Run `python verify_package.py` in this extracted package. It verifies bytes/manifests only. Ten original result bundles M12CB through R4 are provided under `sources/`; source-index hashes are authoritative for locating them. Previous host-specific paths are provenance, not executable locations. Do not regenerate model outputs or modify original verdicts.

Latest R4 ZIP SHA-256: `3a94aec96179cdac4d1eea3985dae4a0625be4bd3a524c512377a540c0468e8b`.
Latest R4 manifest: **203 declared payloads**, explicit manifest self-exclusion.

| Role | Value |
|---|---|
| Repository | `sskim-ai/thesis-monitor` |
| Required local base / R4 final docs | `e15aefdf2bc8ce880482304adcee43c95d4579f0` |
| R4 runtime implementation | `0b13013feb1cf81b57b172c90167ce73cc3bd78b` |
| R4 audit implementation | `9f8fb014b836918bf79029758e3abe5b48035aed` |
| R4 work-instruction Git commit | `435cffa1630303f04e72ac2cabc13373d62155c8` |
| R4 instruction content SHA-256 | `37d9fa5a43355ae42772923c8f9babcc835bd36cfd4fea3261b98e16de949302` |
| Pre-R4 / R3 final local | `5ea16d57ad50a1f7b44a31c11ae97471c30126bc` |
| Existing presence-guard implementation | `50dcec1a56a81db1ebc7e23a322e69f9b028323a` |
| Historical origin-main observation, not a fresh remote check | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |

Use an isolated clean local worktree. Verify ancestry and exact application hashes before changes. Export local sources/test bodies; the R4 local commit is unavailable remotely through Chat (404), which is not permission to push, fetch another implementation as a substitute, or claim a new origin state. A shared source/base/isolation failure stops affected execution.

## 2. Carry-forward ledger: do not restart closed work

The following are verified at the stated scopes, not fresh Full22 results:

- Three immutable M12CE raw Stage-2 batches; nine candidate subjects and 42 maturity rows.
- R4 artifacts show 9/9 READY subjects and 3/3 complete available batches. GOOGL/HUT plans are byte-identical to the old rejected preacceptance plan objects; seven previously successful artifacts remain byte-identical to R3.
- All nine candidate semantic payloads match raw M12CE candidates after removal of only runtime row `as_of`/`provenance_status`.
- Nine before/after model-facing prompt/schema/catalog files match byte-for-byte.
- Historical inventory remains 62 rows / 20 candidates / 7 batches with one original negative candidate. The original 010120 wrong-date output is still invalid; only the separately identified M12CD ephemeral representation is the migration baseline.
- R3/R4 native D01-D14 regression: 14 case IDs / 29 reported cases. Existing at-least-once send-before-cursor crash duplication is an acknowledged limit, not a new repair in this task.
- R4 supplied JUnit: full 4142 passed/63 skipped; focused 232 passed/1 skipped; Treasury79; Kiwoom70. These are historical run records, not substitutes for new affected regressions.

The one outstanding causal item is whether the new **numeric exemption remains bound to an independently validated original Core through every supported entrance**, with proper negative proof. Do not reset dates, axes, symbolic states, presence guard, native delivery policy or numeric language policy to FAIL because that proof is pending.

## 3. Concrete observations to resolve

### 3.1 Positive harness self-derived its reference

R4 `finalization_reproof` materializes Stage-2 `output`, then calls `trusted_batch(batch_context, output.fundamental_cores)`. That creates a reference from the tested output itself. It does not establish independence, despite the owner-contract prose saying independently loaded.

Chat independently compared the supplied reference data to the original Core-stage output files: the positive values really match. Thus this is not evidence that the nine positive outputs are fabricated. It is a missing test of independent binding under coordinated mutations.

Use these independent M12CE Core-stage files (whole original-file hashes, not pretty-reformatted hashes):

| Batch | Original relative path under M12CE `raw/reproof-no-repair/us/` | SHA-256 |
|---|---|---|
| 01 | `core-batch-01.output.json` | `dba70bde34bb2791ed45408fcacfa7f8207fd816d9c9a518cea9aedaddc859ec` |
| 02 | `core-batch-02.output.json` | `134f87dbda8c5b857a70ac237d3b80a2593be09f5d9a625303e656bd2630d309` |
| 03 | `core-batch-03.output.json` | `2d33dce25eb87cddefe1f95bcc74757043ceb51aee4727a6fe907c52b6ca896f` |

Bind Core-stage output, evidence context, generation identity, subject ordering, existing validation verdict and frozen digest. Record the actual freeze/validation owner and the exact existing procedure. Do not treat manifest integrity alone as semantic validation; replay existing Core validators where required. Keep that validated reference outside mutated fixture objects. Never regenerate it from a mutated output after a test begins.

### 3.2 The production job and the harness are different paths

R4 `app/jobs/accepted_decision_v2_runtime.py::validate_output` reads `paths["core_temp"]` separately and passes it to the finalizer. Exercise that **actual existing path**, with isolated paths/claim/settings, rather than concluding it is unsafe merely because the harness differed.

Capture where `core_temp` is written, validated and frozen, and how the expected original identity/digest survives into this call. Boundedly follow that existing owner only. Typed parsing and batch packet/claim/cardinality checks are not by themselves proof that arbitrary replacement text is the previously frozen Core.

### 3.3 The changed artifact reader creates a scope from serialized fields

R4 `load_accepted_v2_production_artifact` validates candidate/Core equality using fields in the artifact, then builds `AcceptedDecisionFrozenCoreNumericScope` from those serialized Core fields. Its exported code does not show an independent original-Core input or verified final-artifact authority when granting the allowance.

An existing upstream/native owner may provide that assurance. Test the supported native caller chain and show exactly where self-consistently modified artifact fields are rejected. Do not equate a diagnostic sidecar with trusted authority, and do not demand that a helper alone defend against arbitrary privileged code execution. The obligation is untrusted model/output/file data at the **supported actual boundaries**, with trusted original data held fixed.

### 3.4 Equality and provenance are different

The R4 scope dataclass contains `fundamental_core_sha256`, but `frozen_core_fields_bound` never reads it. Chat's exact-expression-only probe accepts empty/all-zero digests with matching fields and accepts jointly changed plan/scope field values. This is not a full runtime exploit demonstration. It establishes that this predicate cannot itself establish provenance; existing caller enforcement must do so.

Do not fix this by checking a digest's length or comparing two newly recomputed digests from the same untrusted object. Either prove the existing internal issuer/binding is sufficient, or use the actual independent frozen anchor at the minimal existing owner. A new serialized `trusted=true`, a model-authored hash, a caller-supplied unvalidated set, or a self-consistent artifact is not authority.

### 3.5 F17 was not the originally required negative

R4's F17 maps to a no-trusted-core rejection and a successful numeric artifact roundtrip. The original F17 required a tampered accepted plan after bypassing materialization. Execute that missing negative at its intended boundary.

Likewise, do not claim every digit/unit/ref/logical-condition, joint-trust, role or metadata variant from one test name. Export the actual assertion bodies and parameter IDs. The result's 20 F IDs are not automatically 20 exhaustive variants. This is a reporting/test-coverage correction, not a request to repeat broad harness discovery.

## 4. Scope accounting and allowed existing owners

R4 changed three application files although the instruction expected two and required separate approval for a third. Record this deviation; do not silently rewrite its authorization. This corrective instruction explicitly permits retaining/testing the existing job caller forwarding below, because feeding an independently frozen Core to the existing validator is within this invariant. Do not roll it back only to meet a file count.

Allowed application owners **only if a demonstrated counterexample needs a binding fix**:

1. `app/services/accepted_decision_v2_service.py`: numeric-scope validation/render forwarding; strict standalone defaults and exact role/field checks.
2. `app/services/accepted_decision_v2_runtime_service.py`: existing Core/candidate/final-plan binding and artifact reader; no source/claim/decision policy change.
3. `app/jobs/accepted_decision_v2_runtime.py::validate_output` and its existing Core freeze-path forwarding: pass verified existing references; no scheduler/transport changes.
4. Only if necessary for the existing reader signature, `app/services/ai_assisted_delivery_service.py::_load_delivery_accepted_v2`: minimal forwarding of an **already-established existing trusted reference/authority**, after demonstrating the call dependency. No new delivery policy, ledger, issuer, artifact discovery convention or source collection.

The fourth allowance is conditional, not a request to modify that file. Record why each changed call site is required. Any new trust architecture, persistence schema/version, receipt bridge, signature system or independent policy owner is outside scope: preserve the reproducer, finish independent safe checks, and return the exact dependency. No automatic broad refactor.

## 5. Required test sequence and focused cases

First run against frozen R4 code; classify the observed rejection/acceptance before implementing. Then repair only a reproducible missing binding. Hold original reference bytes/digests and canonical context fixed across negative mutations. Use exact exception class/code or an already-defined safe-suppression state, not any-exception PASS.

| ID | Case | Required proof |
|---|---|---|
| B01 | Original three complete M12CE batches with independently read/validated Core-stage references | 9/9 finalization, GOOGL/HUT no rewritten claims, complete original batch boundaries |
| B02 | Modify candidate/Core numeric claim while original trusted Core is unchanged | Intended ownership rejection, even when candidate's self-computed digest is refreshed |
| B03 | Coordinated output Core/candidate/plan/scope-like data changed consistently | No privilege from self-consistency; original externally retained anchor still controls |
| B04 | Missing/stale/wrong packet, ticker, claim, generation or Core reference | Fail closed for the exempted path; legacy strict nonnumeric behavior not broken |
| B05 | Call the actual job path with output mutations, leaving original core artifact/freeze record untouched | Same intended rejection before accepted artifact/receipt emission; no automatic relabeling of output as trusted |
| B06 | Modify serialized artifact Core/candidate/plan/block and refresh internal hashes/text consistently, with authoritative external data unchanged | Reader or actual upstream/native gate rejects/suppresses before invalid block or state; document the exact authoritative gate |
| B07 | Bypass materialization and inject tampered accepted plan/role/refs/digest into supported integrated validator/reader | Original F17 and role-specific guards demonstrated, not merely a no-scope test or positive roundtrip |
| B08 | Raw payload tries to supply trust context/permission, including a correct-looking scope | Raw contract rejects; no serialized authorization channel |
| B09 | Standalone, Stage-2 sibling numeric, genuine adjudication, wrong-role, order-language and exact-ref controls | Existing strictness preserved at each actual boundary; no blanket CANDIDATE bypass |
| B10 | Actual applicable isolated consumer for a newly finalized GOOGL/HUT-containing fixture | Correct reference binding, normal valid content reaches existing sink; no invalid acceptance masked by base-AI fallback |
| B11 | Required negative node/variant omitted or skipped from the result manifest | Repaired R3 aggregation reports pending/failure, not global PASS; observed runtime and assertion results remain distinct |

Split compound rows into explicit variants before execution, using only this contract's required boundaries. Do not invent arbitrary full trust-store compromise or concurrent privileged memory tampering as new requirements. A synthetic whole-artifact mutation control is labeled synthetic; it is not a new model output. A valid base-AI fallback cannot count as acceptance of the tested v2 artifact.

If B03/B06 are rejected by an existing actual canonical owner, capture that evidence and close without redundant runtime protections. If a missing input causes FileNotFoundError or setup TypeError before the intended gate, fix the test setup; it does not demonstrate protection.

## 6. Preserve behavior and finish all independent evidence in this task

Use unchanged original raw/context/Core data. Numeric regex, numeric registry, `numeric_prose_eligible`, schemas/prompts/catalogs, field/claim text/refs, axes, maturity, symbolic/null/MAX policy, persistence IDs and adjudication selection semantics stay frozen. No numeric rewrite or registry widening.

After any permitted binding patch:

- Replay all three available fresh batches through canonical materialization/finalization and the tested reader, with true independent references. Retain the original seven successful artifacts and newly successful GOOGL/HUT plans as R4 parity baselines. No text/semantic/hash churn for valid equivalent inputs.
- Retain the 62 historical rows and immutable 010120 negative at their established boundaries. Do not require all historical raw negatives to become positive or relabel offline output as Full22.
- Compare actual model-facing bytes where builders are exercised; no new model calls. Evidence/provenance labels outside payloads may differ and must not be called model-visible changes.
- Rerun existing F01-F20 at real variant scopes. Specifically repair F11/F17 evidence and narrower F10/F12/F13/F16/F18 mappings; export tests. Keep directly relevant W2/W3 tests as regressions, not a new delivery/harness workstream.
- Run focused/full suites, Treasury/Kiwoom regressions, Ruff and `git diff --check`; include commands, source SHA, JUnit and new test bodies. Explain count/skip changes; do not drop failing tests.

The closing ledger has one causal item with any dependent blocked checks. Do not stop independent safe proof/export work because one binding test fails. Shared source/base/isolation failures stop affected execution. Do not expand into another unrelated audit.

## 7. Output artifacts: evidence, not asserted trust

Include at minimum:

1. `source-base-and-scope-accounting.json`: source hashes, exact base, third-file deviation and new explicitly bounded caller changes.
2. `independent-core-source-binding.json`: separate Core-stage source paths/hashes, existing validation verdict/owner, context/claim/generation association and retained expected digest.
3. `actual-job-reader-authority-path.json`: exact relevant source/caller excerpts and hashes, what authenticates what, and where the numeric scope can be constructed. No naming-based inference.
4. `binding-before-after-case-matrix.json`: B01-B11 variants, canonical runtime gates, exact expected/observed outcomes, raw/canonical identities and stage reached.
5. `negative-inputs-and-traces/`: original and ephemeral mutated inputs; mutation JSON pointers; fixed external trust reference hashes; full exceptions; whether acceptance/persistence/sink was reached.
6. `original-f01-f20-variant-proof.json`: source test files, exact parameterized node IDs, collected vs executed inventory, assertions, evidence paths and explicit unavailable variants. F17 must remain the actual tamper obligation.
7. `fresh-9-subject-3-batch-parity.json` with raw/normalized/plan/artifact/renderer files and separate source-of-trust inputs; `historical-boundary-regression.json`.
8. `model-facing-byte-parity.json` and compared files; `native-regression.json` with current scope and retained crash limitation.
9. `application-diff.patch`, full local changed sources and tests, before/after hashes, `test-results.json`, JUnit/logs and `aggregation-results.json`.
10. `completion-layer-ledger.json`, `complete-blocker-ledger.json`, `program-completion.json`, result MD, `artifact-manifest.json`, ZIP sidecar.

Use portable source/repo/output-root arguments. Report integrity and semantic validity independently. Export the test source when the local commit is not remotely available; do not ask for a push. Do not hardcode the binding-contract artifact to PASS or set causal blockers to zero independently of measured child results.

## 8. Decision outcomes

`M12CG_R4_R1_INDEPENDENT_BINDING_OFFLINE_CLOSURE_PASS` requires independent validated trust input in the actual tested path, exact negative rejection or documented already-effective upstream enforcement, actual reader/job coverage, original 9/9 positive preservation, standalone/adjudication/Stage-2 strictness, source and semantic immutability, granular F/B proof and required regressions. Runtime change count may be zero if the existing owner already enforced the invariant.

`M12CG_R4_R1_POSITIVE_REPLAY_PASS_BINDING_NOT_PROVEN` retains measured successes but forbids whole offline closure. Identify the exact unexecuted gate, missing source or unresolved owner; do not reset every closed finding.

`M12CG_R4_R1_EXISTING_OWNER_BINDING_REPAIR_FAILED` requires an executed requirement failure. `M12CG_R4_R1_NEW_AUTHORITY_DESIGN_REQUIRED` is reserved for a demonstrated missing trust mechanism outside the narrowly permitted existing-owner correction; no new bridge is implemented here.

Always retain five separate completion layers: closed designs/repairs; offline acceptance; offline operations; fresh Full22 (NOT_RUN here); deployment (NOT_AUTHORIZED). A completed positive replay is not complete negative binding proof. A passing assertion that reproduces a defect is not a passing production property.

Program completion records at least: exact source/base/implementation/audit/docs SHAs; `independent_core_source_count`; `core_reference_derived_from_tested_output=false`; `original_core_validation_owner`; `actual_job_path_executed`; `actual_reader_path_executed`; `authority_at_reader`; `joint_mutation_outcomes`; `f17_actual_tamper_result`; F/B IDs and variant denominators; `scope_deviation_disposition`; changed owners; 9-subject/3-batch results; 7-artifact parity; original negative preservation; semantic/hash/model-facing deltas; native/harness/frozen regressions; dependency-aware blockers; every safety counter.

Even after PASS: `new_full22_authorized=false`, `deployment_readiness=NO`. Return to Chat. Do not attach an automatic next-model run to the proof script.

## 9. Frozen safety and subsequent sequence

No external model/retry/fallback/judge/repair/schema-repair/selective/per-ticker rerun; no Full22; no production send/intent/DB mutation; no main merge, remote push, deployment, scheduler changes or operating-checkout mutation. Offline temporary state/sink tests are separately counted and network-blocked. Mock external I/O only, never the authoritative acceptance logic.

Treasury remains FRED: DGS3/DGS5/DGS10/DGS30, DFII10, T10YIE; renderer `4407cd11a78579e11681b503b2d4e72ee3c3d60f`; daily/per-series as-of/bp-change semantics unchanged.

Kiwoom remains historical `28f4f70700046f98d5d899ee491d3e5f45922e9a`; KOSPI200 2026-09-01/02/03 replay and local LeadingMarket adapter preserved; KOSDAQ150 actual historical fixture UNVERIFIED. Gateway last reported unavailable/unconfigured; READ_ONLY only. Names `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS` are not credentials. No live read/order/modify/cancel or gateway/connector setup here.

No redesign of entry/holder independence, preconfirmation, M12CB numeric scope, standalone numeric strictness, Core ownership, exact refs, atomic polarity, typed primitives, postconfirmation HOLD, expectation/valuation, BusinessDelta, Persistence V2 or the presence guard. Existing crash-after-send/before-cursor behavior is at-least-once and may repeat a chunk; retain it for later deployment review, not as a reason for a new delivery project now.

Sequence: this bounded closure → Chat review → separately authorized new US14/KR8 Full22 from call 1 with no prior-output reuse/stitch/retry/fallback/judge/repair/selective/per-ticker rerun → Chat → Kiwoom read-only verification → current US/KR market/stock smoke → facts-only independent human judgment before seeing AI verdict → comparison → separate deployment/automation decision. Offline replay sources are never new-model proof outputs.
