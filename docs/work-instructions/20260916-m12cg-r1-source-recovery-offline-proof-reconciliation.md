# Thesis Monitor — M12CG-R1 Source Recovery, Offline Proof Reconciliation & Canonical Boundary Audit

## 0. Task identity and decision

This is an **offline evidence-closure and proof-harness reconciliation task**, not M12CH Full22, not a new R2 architecture design, and not authorization for production runtime repair.

The submitted M12CG result remains `M12CG_REQUIRED_SOURCE_COVERAGE_FAILURE` / `NO_GO`. Preserve its immutable result and implementation. This revision supplies missing historical source bundles, addresses contradictions in reported proof measurements, and establishes the actual receipt/serialization/continuity boundaries before another model generation can be considered.

Work-instruction filename: `20260916-m12cg-r1-source-recovery-offline-proof-reconciliation.md`.

Result ZIP: `thesis-monitor-20260916-m12cg-r1-source-recovery-offline-proof-reconciliation-report.zip` plus SHA-256.

Required counters: external model calls 0; Full22 generations 0; runtime behavioral source changes 0; main merge/deploy/scheduler resume/real send/production DB mutation/remote push 0; live Kiwoom read/order/modify/cancel 0/0/0/0.

Allowed edits: isolated offline test/audit harness, granular test assertions after canonical-contract verification, audit/report schemas and documentation. Do not mutate historical payloads, production logic, evidence, validators, hash policy, identity dispatch or source facts to obtain a green report.

If a genuine runtime or architecture defect is established, preserve the failing evidence and propose a **separate bounded repair**, without implementing it here. Independent non-mutating diagnostics may still finish; downstream dependent PASS claims must remain blocked.

## 1. Source precedence and input package

For authorization, this instruction and the latest Chat decision supersede the earlier task's inferred next step. For observed facts, prioritize the verified original M12CG result and byte-level sources over derived summaries; compare actual repository state separately. Earlier handoffs cannot revive closed blockers or override negative evidence.

This package contains original, unmodified source ZIPs under `sources/`, their sidecars, an input manifest, a package verifier, and Chat source-binding checks. **Do not assume a previous session's `/tmp` or `/Users/...` path exists.** Resolve each source by packaged filename and SHA, then map internal relative paths.

| Phase | ZIP SHA-256 | Verified declared payloads in Chat | Purpose |
|---|---|---:|---|
| M12CB | `86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb` | 262 | Original historical contexts/raw output and 010120 negative |
| M12CC | `7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd` | 114 | Ownership audit and historical proof linkage |
| M12CD | `89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff` | 89 | Full 62-row inventory, deterministic baseline, scripts and source snapshot |
| M12CE | `512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9` | 112 | Three completed raw Stage-2 batches / 42 fresh rows / exact context |
| M12CF | `4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846` | 46 | Branch A/R2 ownership decision and producer/consumer history |
| M12CG | `ad8a75edb25d88220cb59d61919a9ba7c86278362b4bac2d30193092e14d06e8` | 42 | Partial implementation, patch, JUnit and incomplete proof artifacts |

Reverify ZIP SHA, CRC, path safety, duplicate members, manifest hashes/sizes, missing entries and unexpected payloads before any replay. Manifest self-exclusion is permitted only where declared by the original bundle. A missing required source is a preflight STOP, not permission to continue patching. The supplied verifier reads/checks bytes only; it does not run historical scripts or contact services.

Chat established that all 62 M12CD inventory entries bind to original M12CB output SHA/ticker/row/ref/old-date records. That closes file availability in this conversation, **not M12CG runtime replay coverage**. Revalidate `review/m12cg-recovered-historical-source-map.json` against original sources; it is an index, not a replacement evidence owner.

## 2. Repository provenance and frozen implementation

| Field | Value from M12CG record |
|---|---|
| repository | `sskim-ai/thesis-monitor` |
| required local base/final M12CG docs | `66ee9c86ee037e52e7a68b857e4ad47bcae7e20f` |
| M12CG runtime implementation | `b7e541b6a3c54567018f937f32d6f92be09a7e4e` |
| pre-M12CG final/M12CF base | `912b1ce6c46f0caf801b2c620b42d904b489c4e7` |
| M12CG work-instruction Git commit | `ef5a0ad12bac733ec5ab5220db258a86e912665b` |
| M12CG instruction content SHA-256 | `327175d2657e7b85c0f23b6e0ba9999ecdadcee3a185942cb2aca5c1a6a04486` |
| observed origin main | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |
| M12CD runtime implementation | `9a9bda729afcb0777d7228ee7151d31f0b2f84f8` |

Do not mistake the 64-character instruction digest for a Git commit. Record work-instruction commit, source content digest, frozen runtime implementation, final docs commit, observed origin main, and operating checkout separately. Historical origin values are not assertions about a newly fetched remote.

Create a clean isolated local branch/worktree from the required final M12CG base. Suggested branch: `codex/20260916-m12cg-r1-offline-proof-reconciliation`. Verify ancestry, source file hashes and clean state. Do not reset or modify another worktree. Unexplained base/runtime divergence => `M12CG_R1_BASE_OR_SCOPE_DIVERGENCE` STOP.

Keep all application source/config/production behavior byte-identical to the frozen base. The M12CG modified runtime surfaces are:

- `app/jobs/accepted_decision_v2_runtime.py`
- `app/services/accepted_decision_v2_runtime_service.py`
- `app/services/evidence_maturity_pricing_service.py`
- `app/services/preconfirmation_decision_v2_service.py`

Other runtime surfaces are frozen too. Reuse canonical owners and Git history before writing a test adapter. No new parallel validator, receipt issuer, evidence owner, persistence schema, dedupe key or symbolic policy.

## 3. Preserve the approved R2 design

Keep raw Stage-2 contract `v2-accepted-stage2-model-output-v2`: model authors neither `as_of` nor `provenance_status`, including `as_of=null`. Received prohibited fields must fail before normalization, not be stripped or overwritten.

Versioned normalized contract: `stage2-maturity-as-of-deterministic-v2`.
Accepted batch output: `v2-accepted-production-output-v2`.
Artifact contract: `v2-accepted-production-artifact-v2`.
Legacy versions remain separately dispatched and strict; never relabel original payloads.

| State | Deterministic date |
|---|---|
| `CONCRETE_ONLY` | M12CD MAX of same-row concrete owned dates |
| `CONCRETE_WITH_SYMBOLIC_REFS` | Same concrete MAX; explicit incomplete concrete coverage |
| `SYMBOLIC_ONLY_NO_CONCRETE_DATE` | JSON null, only for established eligible canonical nondate provenance |

Scalar meaning remains `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`, not absolute latest cutoff. Scope is ticker-local union of supporting/contradicting evidence refs. No assessment/current/global/latest/sibling/file-time fallback. Unknown/cross-ticker/malformed/unresolvable provenance remains a failure. Symbolic validity does not promote an ineligible atomic claim.

SKHY's decisive financial-quality limitation must remain, including its `CONFIRMED` limitation semantics, exact claims/refs/polarity and five-row structure. `canonical:earnings:latest` is not promoted from a placeholder to standalone maturity evidence. Do not special-case SKHY, 010120, row indices, Korean text or hashes in runtime logic.

## 4. Preflight and measurement ownership

Run source integrity and repository checks first. Record source presence and timestamps before executing any audit; do not defer required-source discovery to the report close.

Recover the original M12CG proof harness from the executor's local files/Git if available and hash it before editing. It is not included in the uploaded M12CG result. If unavailable, create a clearly labeled reconstruction of the proof harness that calls existing canonical runtime APIs; never call it the original harness. Include all scripts in the new result.

For every measurement define input artifact hash, runtime SHA, comparator owner/version, stage, denominator and expected result before execution. Use PASS, FAIL, NOT_RUN, NOT_PROVEN, NOT_APPLICABLE_PENDING_CHAT_DECISION and EXPECTED_REJECTION distinctly. A parent cannot be PASS if a required child is FAIL or unmeasured. A zero production counter does not prove an unexecuted delivery path.

## 5. Historical 62-row recovery and replay

Use these original M12CD files:

- `audits/07-historical-scalar-projection-row-matrix.json`
- `audits/22-historical-old-vs-derived-asof-matrix.json`
- `audits/24-historical-010120-original-replay.json`
- `audits/25-historical-010120-new-contract-copy-replay.json`

Bind their historical raw file paths to M12CB `raw/reproof-no-repair/<market>/...` by original hash, not matching filenames alone. Resolve the exact corresponding contexts, frozen Fundamental Cores, catalogs and prior accepted state. Record all rebindings from stale host paths to package-relative sources. No model regeneration.

The population is a 62-row historical inventory, **not 62 valid original rows**. Separate original contract verdict, M12CD ephemeral normalized baseline verdict, and new M12CG/R2 verdict. Keep the 010120 original date `2026-09-15` invalid against its same-row owned `2026-08-12`. Never modify raw bytes to call the original PASS. A separately identified ephemeral representation may follow the already-approved M12CD conversion; log every such transformation.

Replay all 62 through the frozen M12CG runtime, retaining batch membership/order and source identity. Row-only date projection proves only row projection; it does not prove a full candidate, accepted plan or receipt. Record the real boundary reached per row/candidate/batch. Do not count isolated-ticker diagnostic invocations as successful historical whole-batch or new Full22 proofs.

Compare dates against the M12CD deterministic baseline, not against old stochastic date choices. Reconcile expected concrete/mixed/symbolic populations from source data, including the two known mixed rows, without hardcoded count shortcuts. Preserve exact source packets and Fundamental Core hashes. Emit per-row validity/date/status/diff records and candidate-level identity counts at their actual scope.

## 6. Repair diagnostic expectation and fixture aggregation, not runtime errors

The original audit expected `stage2_model_authored_maturity_as_of_forbidden`; actual runtime emitted `stage2_model_authored_as_of_forbidden:CORZ:0`. The older M12CD artifact `34-mdo-mig-n01-model-emitted-as-of.json` uses the latter code too.

Inspect the exact error owner and history. If the harness expected a nonexistent token, fix only that expectation to the canonical contract; explicitly retain the original failed test result in history. Reexecute both non-null and JSON-null raw `as_of` injection plus correct/incorrect `provenance_status` injection through the real raw ingress boundary. Record exception type/code, stage, whether materialization/acceptance/persistence occurred, and unchanged raw SHA. A rejection for an unrelated exception is not a PASS.

Do not rename runtime codes, suppress errors or count any exception as acceptable. Regenerate each fixture result separately. Replace N01–N19 blanket summaries with individual fixture IDs and evidence pointers. Retain expected negative rejection as distinct from a broken assertion/report.

## 7. Reconcile all semantic flags with executable field-level comparison

The original deterministic materialization matrix has **42/42 row-level `raw_semantic_fields_preserved=false`**, while aggregate changes are zero and candidate-level preservation is true. SKHY's nested row is also false. Do not assume all rows changed, and do not assume the false flags are harmless.

Recover actual raw and normalized payloads and the comparator. Produce JSON-pointer-level differences for every false flag. A semantic projection may exclude only:

- newly runtime-owned `as_of` and `provenance_status`, with their own separate correctness proof;
- exact, enumerated representation-version metadata;
- explicitly traced transitive identity/hash fields when comparing identity-bearing objects.

Do not drop whole `driver_maturity`, decision, rationale, evidence, accepted-plan or BusinessDelta subtrees. Preserve array order and duplicates where the canonical serialization does. Preserve exact text/claim/ref/decisive/maturity/axis/polarity values. Distinguish semantic JSON equality from serialized byte equality and model-object equality.

Use a generic R2-row projection paired to the original raw row by immutable source identity. Any corrected report must be generated from that executable comparison; never edit audit booleans manually. A real semantic difference => `M12CG_R1_SEMANTIC_CHANGE_CONFIRMED` STOP before promotion, with a bounded follow-on proposal.

## 8. Diagnose legacy and new serialization roundtrip false results

The original result records `legacy_reader_roundtrip_equal=false`, `new_reader_roundtrip_equal=false`, `legacy_artifact_roundtrip_equal=false`, while claiming some fixture parity/roundtrip PASS and state equality. These are open proof obligations.

For matched legacy and R2 fixtures, capture original in-memory type, object equality, `model_dump(mode="json")`, emitted bytes, loaded type, re-emitted JSON/bytes, canonical hashes and exact field diffs. Freeze timestamps, packet/claim identity and serialization mode when that is the existing contract. Do not add normalization that hides missing/default-injected provenance or changes evidence meaning.

Classify the cause based on executed evidence, not speculation:

- `COMPARATOR_REPRESENTATION_MISMATCH_WITH_CANONICAL_HASH_PARITY`
- `SERIALIZATION_DEFAULT_INJECTION_OR_FIELD_LOSS`
- `UNSTABLE_TIMESTAMP_OR_NONDETERMINISTIC_SERIALIZATION`
- `CANONICAL_HASH_OR_IDENTITY_BREAK`
- `UNRESOLVED_ROUNDTRIP_FAILURE`

The first can close a harness error only if canonical serialization/hash and all authoritative readers genuinely match. List/tuple or object-vs-dict explanations must be demonstrated, not guessed. A production parser/serializer correction is outside R1; confirmed runtime failure => STOP with the exact minimal failing path and proposed scope.

Test supported legacy/new dispatch, missing/unknown versions, new data mislabeled old and vice versa, null/status absence/tamper, repeated same-version read/write and legacy original byte/hash retention. Do not relabel v1 data as v2, inject default status into legacy records, or reuse old IDs to force equality.

## 9. Trace receipt ownership before attempting integration proof

Inspect Git history and actual callers for:

- `parse_accepted_v2_production_artifact` and `load_accepted_v2_production_artifact`;
- `advance_accepted_v2_state` / `load_accepted_v2_state`;
- accepted-v2 runtime-local receipt contract and callers;
- `canonical_acceptance_receipt_service` issuer/verifier/trusted finalization;
- real persistence/continuity/dedupe/delivery-intent consumers.

Do not equate these by name. Produce a call graph with exact contract versions, data types, SHA owners, who authenticates whom, and trust boundaries. Classify:

A. `EXISTING_SUPPORTED_CANONICAL_RECEIPT_PATH`: exercise the already-supported path with isolated test storage and a test-only harness adapter preserving every canonical input and trust gate.

B. `MISSING_REQUIRED_PRODUCTION_BRIDGE`: the authorized end-to-end route genuinely has no required integration; STOP for separate bounded architecture/implementation decision. No new production bridge in R1.

C. `DIFFERENT_RECEIPT_OWNER_OR_REQUIREMENT_NOT_APPLICABLE`: show why the named canonical service belongs to a different architecture and identify the actual owner; return `NOT_APPLICABLE_PENDING_CHAT_DECISION`, not self-approved waiver/PASS.

D. `UNRESOLVED_RECEIPT_OWNERSHIP`: remain NOT_PROVEN and provide exact missing evidence.

A test adapter may prepare inputs for existing real APIs. It may not mint authoritative receipt fields, bypass trusted issuer validation, replace receipt verification with matching hashes, or fabricate a production call edge. Reusing an existing fixture is valid only when its types and owner chain apply to R2.

For A, execute original/new payload → accepted plan → trusted finalization → receipt → isolated persistence → load/verify, same-version repeat, cross-version coexistence, old/new receipt swap, payload/status/ref/version/hash tamper, actual dedupe/idempotency/continuity/intent checks. Separate test sink activity from production. Prove no duplicate intent under applicable canonical behavior; a sink never called is NOT_PROVEN, not zero-change proof.

BusinessDelta and investment semantics must remain unchanged. No new dedupe policy or receipt identity redesign. Any identity conflict => `MATURITY_SYMBOLIC_PROVENANCE_IDENTITY_CONFLICT` STOP.

## 10. Accepted-plan/finalization coverage and frozen numeric contract

Do not report 9/9 accepted-plan equivalence from 9/9 Stage-2 validation. The original M12CG records:

- nine R2-normalized subjects;
- eight v1-normalizable subjects;
- six paired old/new finalized-plan and renderer comparisons;
- seven new-only finalizations, including SKHY;
- GOOGL/HUT finalization errors under both normalized modes: `adjudication_introduced_unregistered_numeric`;
- no v1 normalized baseline for SKHY.

Correct the renderer label `PARTIAL_PASS_7_OF_9_COMPARABLE`: seven new finalizations and six paired comparisons are different denominators. Preserve SKHY's `NOT_AVAILABLE_OLD_NORMALIZER_REJECTED`; do not invent a prior accepted artifact.

Run identical frozen raw/context/core/prior-state inputs on the **exact pre-M12CG runtime** and the frozen M12CG runtime, offline. Merely selecting normalized v1 mode under new code is not a pre-change runtime control. Record finalization path, numeric claim/ref that causes rejection and baseline parity. M12CE's zero full final compositions are relevant: its Stage-2 PASS never guaranteed downstream plan acceptance.

If these failures are baseline-parity and unrelated to R2, record them without modifying the existing numeric/preconfirmation rules; still mark the affected plan/receipt coverage unavailable. If new or a trust-boundary wiring issue is found, STOP and request a separate bounded investigation. Never rewrite historical outputs, delete offending text, force an adjudication, call a model/judge, or selectively count only passing candidates as whole-population proof.

## 11. Explicit-null versus missing canonical metadata boundary

Chat's isolated exact-helper probe found that `symbolic_maturity_evidence_kind` still classifies financial-quality provenance after `source_period` is deleted from structured statement JSON, and earnings placeholder provenance after `period_label`/`period_type` are deleted. `dict.get(... ) is None` conflates absent keys and explicit null at helper level. The probe did not execute the full canonical path.

Reproduce through actual canonical input types and callers, retaining immutable original fixtures separately. Test explicit null, missing key, null-valued required discriminator, malformed statement, missing reason_codes, bad list types, wrong producer version/source_ref, arbitrary latest token, padded/current date, unknown ref and concrete+invalid mixtures. Do not manipulate producer metadata in real records.

Classify evidence:

- upstream schema demonstrably rejects omission before recognition;
- omission is explicitly valid canonical producer semantics, with actual versioned schema/history proof;
- missing/corrupt metadata is incorrectly accepted as intentional symbolic provenance;
- unresolved reachability/contract semantics.

The third conflicts with M12CG's approved missing-versus-null guard: STOP with `M12CG_R1_SYMBOLIC_MISSING_METADATA_BOUNDARY_GAP` and a narrow proposed guard/test repair, not an implementation. Do not globally forbid valid symbolic evidence, add ref/ticker allowlists, infer a date, or invent producer semantics. Placeholder eligibility remains independently enforced even when its provenance is valid nondate metadata.

## 12. Model-facing parity and proof coverage matrix

No model calls to establish schema support or regenerate evidence. Compare pre-M12CG and M12CG builders using identical frozen in-memory inputs and serialization settings, in addition to archived-vs-rehydrated artifact comparison. Record schema/prompt/catalog hashes and bytes independently. Never label nested key-order/LF reconstruction as exact byte equality or a proven runtime semantic change without the paired builder test.

For every original M12CG P01–P13 and N01–N22, provide a row linking the fixture to executable test/harness step, runtime SHA, input/output hashes, expected gate, actual result and scope. Existing tests may satisfy requirements only when exact behavior is demonstrated. Do not use a group label or green full-suite count as a substitute for a missing mandatory negative test.

All US14/KR8 source context inventory remains in scope without new calls. Historical rows and three completed M12CE batches are offline fixtures, not new accepted Full22 outputs. Fresh unexecuted US/KR model batches remain NOT_RUN.

## 13. Safety and existing-contract freeze

Do not reopen frozen-core numeric ownership-scope repair, standalone numeric strictness, GOOGL preconfirmation BUY, BUY/WAIT/HOLDABLE independence, maturity atomic polarity/eligibility, Fundamental Core identity/immutability, exact-ref fidelity, typed primitives, post-confirmation HOLD, expectation/valuation separation, BusinessDelta ownership, Persistence V2 authority, M12CD MAX semantics, Treasury or Kiwoom restoration.

Treasury: FRED; nominal DGS3/DGS5/DGS10/DGS30; real DFII10; breakeven T10YIE; historical renderer `4407cd11a78579e11681b503b2d4e72ee3c3d60f`; daily/per-series as-of/bp-change semantics frozen.

Kiwoom: historical `28f4f70700046f98d5d899ee491d3e5f45922e9a`; KOSPI200 2026-09-01/02/03 replay PASS; local LeadingMarket adapter PASS; KOSDAQ150 actual historical fixture UNVERIFIED. Gateway unconfigured/unavailable as last reported; READ_ONLY only. Names `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS`; never print secrets. Do not configure a gateway, create a connector, or make live calls in R1. No order/modify/cancel.

No production DB, send, intent, scheduler, operating checkout, main branch merge, deployment or remote push. Audit scripts must have no hidden network/model/repair paths. Historical scripts in supplied ZIPs are read-only references; do not execute bundled Full22/model/build scripts blindly.

## 14. Execution sequence and stop discipline

1. Validate package/source manifests and all 62 source bindings; assert required repository base and isolation.
2. Freeze runtime hashes; recover original harness provenance or label reconstruction.
3. Establish granular measurement definitions, original contradictions and scope-aware parent aggregation.
4. Trace receipt ownership and investigate explicit-null/missing-metadata reachability before claiming a proof path exists.
5. Repair only proven test/audit expectation/comparator issues; never change runtime behavior.
6. Execute full historical and completed M12CE offline fixtures; retain originals and new artifacts separately.
7. Execute paired pre-M12CG/new-runtime finalization and serialization comparisons; capture every false diff.
8. Where an existing supported receipt path is proven, exercise it canonically in isolated storage. Otherwise retain its explicit STOP/NOT_PROVEN classification.
9. Run focused/full/frozen regressions and lint/diff checks for any test/harness edits; record actual scope, counts and commands.
10. Generate all reports from one granular result matrix; validate child/parent status and denominators; preserve negative and unavailable cases.
11. Freeze local audit/docs commits, produce result ZIP/manifest/SHA and STOP for Chat review.

A newly confirmed runtime defect does not authorize a repair here. Continue independent read-only diagnostics only when they do not rely on the broken gate or mask its consequences. No model retry, no Full22, no old generation continuation. Old M12CE remains terminal at call 8.

## 15. Required artifacts and reproducibility

Include original/new comparisons and scripts, not only aggregate JSON. Required minimum:

- source-integrity-and-availability-preflight.json
- historical-62-row-source-binding.json
- repository-provenance-and-runtime-freeze.json
- original-harness-provenance-or-reconstruction.json
- original-report-inconsistency-inventory.json
- raw-provenance-negative-code-ownership.json
- granular-positive-negative-fixture-matrix.json
- historical-original-v1-r2-validity-and-date-matrix.json
- fresh-42-row-field-level-semantic-diffs.json
- candidate-accepted-plan-renderer-denominator-matrix.json
- pre-m12cg-vs-current-finalization-baseline.json
- serialization-roundtrip-type-json-byte-hash-diffs.json
- canonical-receipt-owner-call-graph.json
- receipt-path-classification-and-trust-boundary.json
- receipt-cross-version-isolation-proof.json (or explicit NOT_PROVEN with dependency)
- operational-dedupe-idempotency-continuity-proof.json (or explicit NOT_PROVEN)
- missing-vs-explicit-null-canonical-boundary-tests.json
- identical-input-model-facing-builder-comparison.json
- report-aggregation-consistency-check.json
- frozen-regression-and-tests.json plus actual commands/JUnit/logs
- safety-zero-call-audit.json
- go-no-go-and-unmet-dependencies.json
- next-bounded-scope-proposal.md
- program-completion.json
- artifact-manifest.json and ZIP sidecar.

Bundle executable offline proof scripts with CLI arguments for source/repo/output roots, no stale absolute host paths. Include exact before/after candidate, normalized output, finalized plan, artifact, receipt and state payloads for measured cases; names must say historical/ephemeral/negative/control and scope. Include exception traces and JSON-pointer diffs for every false/negative/unmeasured result. Do not include secrets. A synthetic-only case must be labeled synthetic, not historical whole-batch proof.

If emitting a reduced snapshot, explain it and retain a hash-addressable original source reference. Never replace exact source evidence with summaries. Use relative artifact paths; aggregate repeated candidate hashes once per candidate, not once per driver row.

## 16. Program-completion and aggregation contract

Report at least:

`top_level_result`, `required_base_sha`, `frozen_runtime_implementation_sha`, `work_instruction_commit`, `work_instruction_content_sha256`, `audit_implementation_sha`, `final_local_sha`, `runtime_source_change_count`, `sources_verified`, `historical_rows_bound`, `historical_rows_replayed`, `historical_original_negative_count`, `fresh_rows_replayed`, `raw_boundary_negative_result`, `diagnostic_expectation_classification`, `semantic_row_false_flag_cause`, `semantic_change_count`, `semantic_comparison_denominator`, `legacy_roundtrip_classification`, `new_roundtrip_classification`, `canonical_hash_parity`, `new_version_roundtrip_result`, `receipt_owner_classification`, `receipt_isolation_result`, `continuity_result`, `duplicate_intent_result`, `paired_finalization_comparable_count`, `new_only_finalized_count`, `baseline_finalization_errors`, `missing_metadata_boundary_classification`, `parent_child_status_mismatch_count`, `source_coverage_ready`, `offline_compatibility_ready`, `new_full22_authorized`, `message_model_contract_readiness`, `deployment_readiness`, all zero-call/production counters and next scope.

Measured zeros need a denominator; unavailable values are NOT_PROVEN/NOT_RUN, not 0. Add `observed_result`, `expected_contract_result` and `test_assertion_result` separately for negative tests. A harness repair must not overwrite the original outcome.

Do not automatically collapse all issues to the first missing source. Emit the complete blocker set, separating SOURCE, HARNESS/REPORT, RUNTIME, ARCHITECTURE and COVERAGE. A fully green JUnit suite cannot override a required failing proof artifact.

## 17. Terminal outcomes and subsequent authorization

### Offline evidence closure demonstrated

`M12CG_R1_OFFLINE_EVIDENCE_CLOSURE_PASS` requires all applicable original M12CG offline gates to be genuinely proven, all mandatory source rows replayed, contradictory flags resolved with raw diffs, exact raw-field negatives, legacy/new canonical serialization/hash fidelity, correct source metadata boundary, and executed valid receipt/continuity/identity proof. No previously required gate may be silently waived as not applicable.

Even then: `new_full22_authorized=false` in the executor result; `message_model_contract_readiness=NOT_READY_PENDING_CHAT_REVIEW_AND_NEW_FULL22`; `deployment_readiness=NO`. Return to Chat before any next model task.

### Confirmed runtime guard/serialization/semantic/identity issue

`M12CG_R1_RUNTIME_REPAIR_REQUIRED` with precise subtype and reproducer. No runtime fix here; propose the smallest canonical-owner repair and required offline reproof scope.

### Missing integration or unresolved proof authority

`M12CG_R1_ARCHITECTURE_DECISION_REQUIRED` with receipt owner/caller evidence. Do not add a new bridge or revise proof applicability without Chat.

### Remaining source/harness/coverage ambiguity

`M12CG_R1_OFFLINE_PROOF_NOT_CLOSED`, with measured results and explicit unavailable dependencies. Do not initiate M12CH to gather missing offline evidence.

Future order remains: offline closure/repair → Chat review → separately authorized wholly new Full22 from call 1 (no reuse/stitch/retry/fallback/judge/repair/selective/per-ticker rerun) → Chat review → Kiwoom read-only gateway verification → Chat review → current US/KR market and monitored-stock message smoke → independent human judgment from collected facts before consulting the AI verdict → AI comparison → separate deploy/automation decision.
