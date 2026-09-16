# Thesis Monitor — M12CG-R2 Symbolic Metadata Presence Guard Repair & Owner-Scoped Offline Reproof

## 0. Task identity and bounded authorization

This is a **narrow runtime guard repair plus offline regression/proof completion** after M12CG-R1. It is not a new symbolic policy, receipt-architecture migration, model-facing repair, new Full22 generation, or deployment task.

Work instruction: `20260916-m12cg-r2-symbolic-metadata-presence-guard-and-offline-reproof.md`.
Result ZIP: `thesis-monitor-20260916-m12cg-r2-symbolic-metadata-presence-guard-and-offline-reproof-report.zip` plus `.sha256`.

Chat decisions:

1. Accept R1's terminal `M12CG_R1_RUNTIME_REPAIR_REQUIRED`. Do not relabel R1 or original M12CG as offline PASS.
2. Preserve Branch A/R2. A known absent source period is valid nondate provenance; an absent required metadata key is not evidence of that state.
3. Authorize only presence-aware validation at the **existing canonical symbolic classifier**, with its tests and offline proof harness. Do not change source facts or create missing keys.
4. Do not force the accepted-v2 artifact/state route into `canonical_acceptance_receipt_service` merely because both use the word receipt. Demonstrate assurance through the actual applicable owner/caller chain. This is a scope correction, **not waiver of payload binding, version isolation, persistence, continuity or duplicate-intent proof**.
5. If the actual operating route needs a bridge or new trust/dedupe policy, preserve the gap and STOP for another bounded Chat decision. No bridge implementation here.
6. External model calls = 0; Full22 generations = 0; production actions = 0. Return to Chat even after all authorized offline work passes.

## 1. Authoritative sources and mandatory preflight

For authorization use this instruction. For observed facts use original verified bytes and current exact repository evidence, not historical summaries. Required source bundles are packaged under `sources/` with their original sidecars. Verify package manifest, source SHA/CRC, safe relative paths, duplicate entries, every manifest hash/size and missing/extra payloads before changing runtime code.

| Source | ZIP SHA-256 | Declared payloads |
|---|---|---:|
| M12CB | `86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb` | 262 |
| M12CC | `7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd` | 114 |
| M12CD | `89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff` | 89 |
| M12CE | `512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9` | 112 |
| M12CF | `4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846` | 46 |
| M12CG | `ad8a75edb25d88220cb59d61919a9ba7c86278362b4bac2d30193092e14d06e8` | 42 |
| M12CG-R1 | `55b2c890fedad3b5b09e5995862637d040f69db882745bfdddfa30d1d38c191f` | 86 |

Manifest self-exclusion is permitted only as declared. Treat historical `/tmp` or host-specific paths as provenance, not usable locations. Rebind by hash and packaged relative path. Never regenerate outputs to fill coverage. Missing or invalid required sources => `M12CG_R2_SOURCE_OR_BASE_FAILURE` before patching.

Review documents/source maps in this package are indexes and Chat analysis, not replacement evidence owners. Historical scripts are read-only reference until inspected; never execute a bundled Full22/network script as a proof shortcut.

## 2. Exact repository provenance

| Role | SHA |
|---|---|
| Required local base / R1 final docs | `b5b605fd92c19af68ce39b299d0e1b540160c849` |
| R1 audit implementation (not runtime) | `9f85763b98f2a921a4dd59f49a53a3a68449b85a` |
| R1 instruction Git commit | `28d640856f0bd3c6d1655d260f6f043562325eaf` |
| R1 instruction content SHA-256 | `fe8145dc0a0fef99c1b77adf4fcceb007a7ecfa1f56c48e31a202dbdde073a50` |
| Frozen M12CG runtime / before-repair control | `b7e541b6a3c54567018f937f32d6f92be09a7e4e` |
| Original M12CG final docs | `66ee9c86ee037e52e7a68b857e4ad47bcae7e20f` |
| Exact pre-M12CG control | `912b1ce6c46f0caf801b2c620b42d904b489c4e7` |
| Historical origin main observation (not freshly verified) | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |

Repository: `sskim-ai/thesis-monitor`. Suggested isolated branch: `codex/20260916-m12cg-r2-symbolic-metadata-guard-offline`.

Verify ancestry and byte hashes from R1 `repository-provenance-and-runtime-freeze.json`. Inspect Git history and existing implementation before writing code. Do not reset another worktree, modify operating checkout, merge main, or push remotely. Record instruction commit, runtime implementation freeze, audit implementation, final docs and origin observation separately. A 64-character content digest is not a Git commit.

R1 changed audit/test/docs only. Its full tests are not a new runtime implementation. Unexplained source/config divergence => STOP.

## 3. Facts accepted from R1, with exact scope

R1 recovers six prior source bundles and binds all 62 historical rows. Its included harness calls the whole-batch materializer and candidate validator on seven historical batches / 20 candidates: 19 originally valid candidates, one original negative candidate, 20 valid ephemeral R2 candidates, 62/62 date parity. Historical status population is 60 concrete-only and two mixed rows. This is **not historical accepted-plan/receipt/delivery proof**.

Fresh replay covers three completed M12CE batches / nine subjects / 42 rows: 41 concrete-only, one symbolic-only; Stage-2 validation 9/9. Exact supplied fresh candidate comparisons preserve all semantic fields after removing only runtime date/status fields. Seven R2 finalizations and six paired old/new finalization/renderer comparisons are different denominators.

Raw as_of negative mismatch was a harness error: the canonical error is `stage2_model_authored_as_of_forbidden`, not `stage2_model_authored_maturity_as_of_forbidden`. Runtime had correctly rejected the field. Preserve this error contract.

Legacy and new CORZ artifact serialization fixtures have equal JSON, re-emitted bytes and canonical hashes despite object-equality false. R1 reports differing explicitly-set field sets. This closes the comparator contradiction **for those fixtures**, not every version/receipt/continuity boundary. Do not alter production equality or serialization to make objects compare equal.

R1's exact pre-M12CG/current-code controls reproduce GOOGL/HUT `adjudication_introduced_unregistered_numeric` in both. Their downstream accepted-plan proof remains unavailable; baseline parity is not PASS for those candidates. R1's paired builder outputs are identical for the three observed US batches, not a fresh Full22.

## 4. Confirmed defect and smallest repair

Existing owner: `app/services/evidence_maturity_pricing_service.py::symbolic_maturity_evidence_kind`.

Current problematic predicates use `statement.get(key) is None`. They accept both a present JSON-null key and an absent key. R1 demonstrates:

- Financial-quality `source_period` deletion passes typed `AcceptedV2ProductionContext` parsing and the actual `materialize_accepted_v2_stage2_output` route, producing null plus `SYMBOLIC_ONLY_NO_CONCRETE_DATE`.
- Earnings `period_label`/`period_type` deletion passes typed `DecisionEvidenceRef` and the classifier. Do not falsely report a full maturity-eligibility/materializer proof for this placeholder from a helper test.
- Explicit null in the original source is valid; missing reason codes/bad reason-code container are already rejected in the reported full materializer cases.

Required change: check key **presence and explicit null value** independently for required nullable producer fields, within their existing discriminated producer branches:

| Existing branch | Required nullable fields |
|---|---|
| Financial-quality limitation | `source_period` present and JSON null |
| Earnings period placeholder | `period_label` present and JSON null; `period_type` present and JSON null |

Reuse current producer version/type/state/source_ref/reason-code predicates. Missing metadata must yield non-recognition/invalid provenance via the existing failure path, never a fake date or a repaired statement. Preserve existing concrete resolution and valid symbolic behavior.

Expected runtime footprint: this classifier in one application file. Tests/audit/docs may change. If another runtime owner must change, first prove why the confirmed defect is impossible to close at this owner; STOP for Chat rather than broadening automatically.

Do not use `setdefault`, insert missing JSON nulls, catch-and-default parsing, infer state from `:latest`, create a ticker/ref allowlist, change producer semantics, or globally reject valid symbolic states. Do not make an earnings placeholder eligible for maturity merely because its provenance is well formed.

## 5. Frozen raw and normalized contracts

Keep:

- Raw Stage-2: `v2-accepted-stage2-model-output-v2`.
- Normalization: `stage2-maturity-as-of-deterministic-v2`.
- Accepted output: `v2-accepted-production-output-v2`.
- Artifact: `v2-accepted-production-artifact-v2`; legacy v1 dispatched separately.

This repairs enforcement of the already approved missing-versus-explicit-null invariant, not valid-input semantics. Do not bump versions just to conceal a different policy. An actual contract semantic change needs Chat authorization.

| Row state | as_of |
|---|---|
| `CONCRETE_ONLY` | MAX concrete ticker-local same-row owned dates |
| `CONCRETE_WITH_SYMBOLIC_REFS` | Same MAX; explicit incomplete concrete coverage |
| `SYMBOLIC_ONLY_NO_CONCRETE_DATE` | JSON null only for established valid symbolic provenance |

Meaning: `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`, not absolute latest cutoff. Derive only from supporting/contradicting row refs. No assessment/current/global/latest/sibling/source-file-time fallback. Every participating invalid/unresolvable ref fails, including mixed rows with a valid concrete peer.

Model still cannot emit either runtime field, including correct status or `as_of=null`; reject before normalization. Preserve exact refs, atomic eligibility/polarity, future-date checks, typed primitives, Core identity and standalone numeric strictness.

## 6. Pre-patch regression and typed/full-path fixtures

First preserve the R1 failure through exact before-repair runtime, then demonstrate fail-closed after repair with identical ephemeral mutated input. Raw sources remain immutable. Record source/context/raw hashes, mutation JSON pointers, typed parse outcome, classifier result, materializer result, independent validator result and boundary reached.

Required cases:

| ID | Case | Expected after repair |
|---|---|---|
| G01 | Original explicit-null financial-quality limitation | Same symbolic kind, null/status, SKHY five rows and decisive limitation preserved |
| G02 | Delete only financial-quality `source_period` | Classifier non-recognition; actual materializer provenance rejection |
| G03 | Original explicit-null earnings placeholder | Same provenance kind; original standalone atomic ineligibility unchanged |
| G04 | Delete only `period_label` | Non-recognition / invalid projection |
| G05 | Delete only `period_type` | Non-recognition / invalid projection |
| G06 | Delete both earnings nullable keys | Non-recognition / invalid projection |
| G07 | Required null field replaced by string `"null"`, empty string, number, bool, object or array | Non-recognition under this symbolic branch; no coercion or invented date |
| G08 | Concrete peer plus invalid missing-metadata ref | Hard rejection; no ignoring invalid peer |
| G09 | Concrete peer plus valid explicit-null symbolic ref | Existing mixed MAX/state unchanged |
| G10 | Invalid/missing producer discriminator, source_ref, source type/state, malformed statement or reason-code container | Existing rejection preserved; classify actual rejecting layer |
| G11 | Arbitrary/padded symbolic token, `current`, bad calendar/future/cross-ticker ref | Existing hard failures preserved |
| G12 | Raw model authors as_of or status, including null/correct values | Exact raw-ingress rejection before materialization |
| G13 | Forged normalized null/status against missing-metadata canonical context | Independent hard validator rejects, even when materializer is bypassed by a test input |
| G14 | Equivalent existing producer schema with generic US/KR fixture identities | Generic guard; no ticker/ref/text/row-index dependency |

For G04-G06 do not invent a standalone maturity claim to bypass eligibility. Prove typed classifier/projector rejection; use existing legitimate mixed/negative fixture paths where applicable and report the actual boundary. Do not count an unrelated eligibility exception as proof of metadata guard rejection.

No production data tampering; all mutations are labeled negative ephemeral fixtures. Preserve canonical error names. Expected rejection succeeds only when exception type/code and the rejecting boundary are the intended ones; any arbitrary exception is not proof.

## 7. Offline valid-input neutrality and complete replay

Replay the full historical 62-row inventory and all fresh 42 rows with original batch membership/order using exact packaged contexts/Core/ownership. Keep generation and source identity, not just ticker. Do not count repeated subjects as distinct Full22 coverage.

Historical original `010120` remains invalid: original date `2026-09-15`, cited owner `2026-08-12`. Use only separately labeled M12CD-approved ephemeral conversion as migration baseline. Do not remove its date in-place, rewrite raw bytes or label the original PASS.

For every valid before-repair input require unchanged:

- projected as_of and provenance_status;
- raw/model-facing schema/prompt/catalog and frozen Core bytes/hashes;
- full normalized candidate JSON/bytes/hash;
- semantic claims, row order, exact refs, decisive/polarity/maturity and all decision axes;
- successful accepted-plan/renderer/identity/state outputs, within the measured scope.

Compare before-R2 versus after-R2 using the same clock, inputs, serialization and version. Expected change is only **rejection of invalid missing-required-metadata inputs**. No valid-output churn should result from the guard. Any valid semantic/hash/model-facing delta => `M12CG_R2_UNEXPECTED_VALID_INPUT_CHANGE` STOP.

Do not write summary records into a file called normalized candidates. R1's `payloads/historical/ephemeral-r2-normalized-candidates.json` contains diagnostics, not full candidate payloads. Export actual full normalized historical payloads in R2 with hashes and exact source bindings. Export finalized plans, renderer text, receipts and state only where actually produced; mark unavailable ones explicitly.

## 8. Per-fixture evidence and aggregation correction

Keep every original M12CG P01-P13/N01-N22 obligation visible. R1 fixed aggregate contradictions but its `fixture_matrix` still defaults individual statuses from `focused_tests["status"]`. A suite-level PASS does not establish each fixture's intended assertion.

Mandatory corrections:

1. Bind every fixture to executed test node IDs (including parameter IDs), assertion/code owner, input/output hashes and result, or to a concrete replay record with equivalent behavior. A descriptive pointer alone is insufficient.
2. N16: execute an ephemeral decisive-row deletion and show the semantic comparator flags loss; unchanged-row preservation alone does not prove this negative control.
3. N17: split parser/version/status tamper proof from actual payload/receipt swap proof. R1's serialization audit cannot make receipt isolation PASS. Use NOT_PROVEN when the applicable owner path is absent or unexecuted.
4. N22: demonstrate actual atomic polarity/claim linkage or maturity semantic mutation; a MAX/status-only test is not a substitute. Similarly, an unknown-ref test cannot alone prove all empty/unresolvable-row cases under N09.
5. Reconcile partial variants individually; do not mark a compound fixture PASS when only one disjunct was tested.
6. Replace R1 hardcoded terminal/fixture labels with executable conditions. Add harness tests where a required assertion fails, is skipped, is absent, or has no denominator: parent must not be PASS. Do not merely change R1's hardcoded failure string to PASS.

Report separately `observed_result`, `expected_contract_result`, `assertion_result`, `evidence_scope`, denominator and dependency. Skipped/unavailable is not a measured zero. No manual boolean editing; all matrices derive from granular results.

## 9. Receipt applicability — explicit Chat scope decision

R1 identifies two different routes:

| Route | Payload / authority |
|---|---|
| accepted-v2 production artifact/state | `AcceptedDecisionPlan`, artifact parser/loader, runtime orchestration receipt `v2-accepted-production-receipt-v1`, `advance_accepted_v2_state` |
| canonical acceptance persistence | `DirectionalCoreCandidate`, trusted `canonical_two_stage_finalizer_v1`, `CanonicalAcceptanceReceiptV1`, `LocalEphemeralAcceptedAssessmentPersistence.apply` |

Decision for this task: **use the native accepted-v2 owners to prove the accepted-v2 fixture route; do not add a synthetic conversion/bridge to the other receipt service**. A plain orchestration receipt is not promoted to the other service's trusted attestation. No receipt name alone confers authority.

This does NOT establish that the other service is unnecessary for every intended production path. It does NOT waive any assurance. Produce a requirement-to-owner matrix distinguishing:

- parser/normalized candidate/accepted-plan acceptance;
- artifact and receipt/payload/version binding;
- persisted state loading and repeated-input idempotency;
- actual selected operational route, continuity/dedupe and intent transition;
- unrelated service-specific requirements versus genuinely missing required trust edges.

Trace actual CLI/job → artifact → consumer → validation → sidecar/receipt → state → delivery code with file/symbol/line and source hash, including how invalid/swapped data is rejected. R1's call graph includes static assertions and two grep outputs; retain verified findings but supply full relevant code excerpts/call-site evidence before treating absent direct calls as a complete trust-boundary proof.

If a canonical-receipt-service-specific test is not applicable to the demonstrated accepted-v2 route, label it `NOT_APPLICABLE_SERVICE_SPECIFIC_OWNER_MISMATCH` and explicitly link the **equivalent native-owner obligation**. Overall receipt/identity readiness stays NOT_PROVEN until that native obligation is executed. This is never a blanket exemption.

Allowed: offline tests of existing native APIs, ephemeral filesystem/state and an existing test-only delivery sink. Mock external I/O boundaries only; do not replace acceptance, hash validation, identity, dedupe or state-transition logic with stubs that always pass. Instrument the actual existing route without production sends, network calls or persistent user-data changes.

Required when supported by the actual route: legacy/new coexistence, native payload/receipt swap and field tamper rejection, version mismatch, unchanged same-version replay, metadata-only migration continuity, no duplicate operational intent. If the sidecar is only diagnostic, document the real authority and test that owner instead of treating a sidecar match as authentication.

If an applicable native path cannot enforce or demonstrate the needed property, report `M12CG_R2_NATIVE_ACCEPTANCE_TRUST_BOUNDARY_NOT_PROVEN` or `M12CG_R2_REQUIRED_INTEGRATION_DESIGN_DECISION`. Do not invent a bridge, alter receipt trust, add dedupe policy or declare the property irrelevant. The guard repair may still be proven independently; all downstream/global readiness remains blocked.

## 10. Baseline GOOGL/HUT numeric failures remain a separate open coverage item

Preserve R1 paired pre-M12CG/current control for `adjudication_introduced_unregistered_numeric`. No numeric regex/threshold/ownership widening or GOOGL preconfirmation repair is authorized in R2.

Keep measured totals distinct: nine Stage-2-valid subjects, eight legacy-normalizable, seven R2 finalizations, six paired comparisons, two known finalization failures, no legacy accepted artifact for symbolic SKHY. Recompute rather than hardcode.

Read-only diagnostics may identify the exact rejected numeric token/claim and caller/ref ownership with full input snapshots. R1 only supplied the error code and parity; do not assert a semantic cause not yet evidenced. If reaching all-subject final acceptance needs another runtime correction, return a separate bounded proposal. Baseline parity does not upgrade failed acceptance or constitute Full22 readiness.

## 11. Serialization, identities and model-facing tests

Preserve the demonstrated legacy/new CORZ canonical JSON/hash equality. Also test the changed boundary through original valid symbolic SKHY and available mixed historical fixtures where the actual route reaches acceptance; record any unavailable pre-symbolic baseline honestly.

Distinguish object equality, field-set metadata, JSON equality, emitted bytes, canonical hashes and authority validation. Do not alter runtime equality or insert legacy defaults to make a comparator pass. Same bytes saved twice at a frozen timestamp prove state determinism, not delivery dedupe.

Paired before/after builders must use identical inputs, actual source code and serialization settings. Compare schema/prompt/catalog bytes for every available offline batch used in proof. Any invalid input now rejected before a builder is a correctly classified negative, not a valid-input byte delta. No calls to external models to verify support.

## 12. Existing contract and market freeze

Do not reopen M12CB frozen-core numeric scope, standalone numeric strictness, GOOGL preconfirmation, BUY/WAIT/HOLDABLE independence, atomic maturity polarity/eligibility, Fundamental Core batch identity/immutability, exact refs, typed primitives outside this presence guard, post-confirmation HOLD, expectation/valuation separation, BusinessDelta or Persistence V2 authority. R2 normalization/null/MAX policy stays unchanged for valid inputs.

Treasury: FRED; nominal DGS3/DGS5/DGS10/DGS30; real DFII10; breakeven T10YIE; historical renderer `4407cd11a78579e11681b503b2d4e72ee3c3d60f`; daily/per-series as-of/bp-change semantics frozen.

Kiwoom: historical `28f4f70700046f98d5d899ee491d3e5f45922e9a`; KOSPI200 2026-09-01/02/03 replay and local LeadingMarket adapter preserved. KOSDAQ150 actual historical fixture remains UNVERIFIED. Last gateway status unconfigured/unavailable; READ_ONLY only. Config names `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS`; no secret output. No gateway configuration, connector creation, live read, order, modify or cancel in R2.

Zero external model/Full22/retry/fallback/judge/repair-model/selective-model-rerun/per-ticker-retry calls. Ordinary local red/green test iteration in this bounded repair is permitted. No main merge, remote push, deployment, scheduler resume, production send/intent/DB mutation or operating-checkout change.

## 13. Execution sequence

1. Verify all seven source bundles, exact repository base and clean isolated worktree; freeze before-repair hashes.
2. Read existing classifier, producer schemas and caller history; preserve the exact R1 typed/materializer reproducer.
3. Specify required presence/null invariants and add failing regressions; record expected errors.
4. Patch only the canonical classifier guard; prove missing-key rejection and valid explicit-null preservation through typed/projector/materializer/independent-validator paths at their actual eligibility boundaries.
5. Correct harness coverage mapping, dynamic aggregation and payload export; keep original reports immutable.
6. Replay complete historical/fresh sources with valid-input bytes/hash/semantic neutrality and negative fixture coverage.
7. Prove owner-scoped artifact/state/receipt boundaries and, only through existing isolated routes, continuity/dedupe/intent. Never add a production bridge. Preserve separate unresolved architecture gaps.
8. Run focused/full/frozen suites, lint and diff checks, recording exact commands/exit codes/JUnit and source SHA.
9. Freeze runtime implementation; generate results, all original/new payloads and granular test-to-proof mapping; report partial successes and all blockers separately.
10. STOP for Chat. No M12CH or any Full22 in this task.

A known R1 guard failure is the authorized repair target, not a reason to abandon unrelated safe diagnostics. A new semantic/identity/producer-policy issue is not permission to expand the patch.

## 14. Test count reconciliation

R1 supplied JUnit: focused 178 passed / 1 skipped, full 4084 passed / 63 skipped, Treasury 79 passed, Kiwoom 70 passed. Earlier M12CG used different focused/market selections (214/1, Treasury69, Kiwoom32). Do not misinterpret different suite selection as deleted tests or feature restoration. Preserve all preexisting full-suite tests and explain additions/skips/warnings by node IDs and commands.

A full green suite cannot override an unexecuted or failing migration gate. Tests that assert reproduction of the old defect may themselves be green; record the runtime observed behavior separately from assertion success.

## 15. Required artifacts

At minimum include:

- `source-integrity-and-runtime-base.json` and package/source hashes;
- `canonical-symbolic-classifier-history-and-presence-contract.json`;
- `before-after-missing-vs-explicit-null-boundary.json` with G01-G14 granular results;
- `independent-validator-canonical-context-tamper-proof.json`;
- `guard-runtime-diff.patch` and exact changed files/symbols/hashes;
- `historical-62-source-binding-and-original-ephemeral-verdicts.json`;
- `historical-before-after-r2-candidate-row-matrix.json` plus actual normalized payloads;
- `fresh-42-before-after-r2-semantic-hash-matrix.json` plus actual raw/normalized payloads;
- `raw-runtime-field-negative-tests.json`;
- `model-facing-before-after-builder-byte-proof.json`;
- `original-fixtures-test-node-assertion-coverage.json` (P01-P13/N01-N22; no group-only PASS);
- `semantic-loss-and-polarity-negative-controls.json`;
- `native-acceptance-requirement-owner-call-path-matrix.json` plus source excerpts;
- `native-artifact-receipt-version-binding-proof.json` or precise NOT_PROVEN;
- `state-roundtrip-idempotency-proof.json`;
- `native-delivery-continuity-dedupe-intent-proof.json` or precise NOT_PROVEN;
- `baseline-finalization-errors-and-coverage.json`;
- `serialization-type-json-bytes-hash-comparison.json`;
- `dynamic-aggregation-negative-control-tests.json`;
- `focused-full-frozen-regressions.json` plus commands/JUnit/logs;
- `safety-zero-call-and-production-audit.json`;
- `complete-blocker-and-scope-status-matrix.json`;
- `program-completion.json`, result MD, next bounded proposal;
- `artifact-manifest.json` (relative paths, sizes, SHA; explicit self-exclusion), ZIP sidecar.

Include portable proof scripts with source/repo/output-root arguments and every evidence payload needed to verify claims. Do not omit failed/control inputs; redact secrets without converting summaries into fake original bytes. No stale-path-only results. Trace every reduced view to the original hash and distinguish it from a full payload.

## 16. Program completion

Required fields include:

`top_level_result`, `source_bundle_count_verified`, `required_base_sha`, `before_runtime_sha`, `work_instruction_commit`, `work_instruction_content_sha256`, `guard_implementation_sha`, `audit_implementation_sha`, `final_local_sha`, `runtime_changed_files`, `runtime_changed_symbols`, `explicit_null_preservation_result`, `financial_quality_missing_key_guard_result`, `earnings_missing_label_guard_result`, `earnings_missing_type_guard_result`, `independent_validator_rejection_result`, `guard_repair_status`, `historical_rows_replayed`, `historical_candidates_valid`, `historical_original_negative_count`, `historical_date_parity_failures`, `fresh_rows_replayed`, `fresh_stage2_subjects_valid`, `valid_input_semantic_change_count`, `valid_input_normalized_hash_change_count`, `model_facing_byte_delta_count`, `fixture_variants_required`, `fixture_variants_proven`, `fixture_variants_not_proven`, `unsupported_group_pass_count`, `native_owner_applicability`, `service_specific_requirement_disposition`, `native_receipt_binding_result`, `native_state_roundtrip_result`, `continuity_result`, `duplicate_intent_result`, `paired_finalization_count`, `new_finalization_count`, `baseline_finalization_error_count`, `accepted_plan_coverage_complete`, `offline_migration_compatibility_status`, `complete_blocker_set`, `new_full22_authorized=false`, `message_model_contract_readiness`, `deployment_readiness=NO` and every model/production/live count.

Use NOT_PROVEN/NOT_RUN plus reason where unmeasured; never write an expected zero as measured. Separate the targeted repair status, broader offline migration status, model proof readiness and deployment readiness.

## 17. Terminal outcomes

### Target guard fixed, broader proof still open

`M12CG_R2_GUARD_REPAIR_PASS_OFFLINE_CLOSURE_PENDING`.
Requires exact intended guard fix and all valid-input regression/replay checks; lists remaining native-authority, coverage, fixture or finalization obligations. This is **not overall M12CG offline PASS**.

### All applicable migration obligations genuinely closed

`M12CG_R2_OWNER_SCOPED_OFFLINE_MIGRATION_PASS`.
Requires guard proof, complete historical/fresh coverage at the required boundaries, no semantic/hash/model-facing valid-input changes, exact original fixture evidence, native-owner acceptance/binding/state/continuity proof, complete requirement mapping and no silently waived gate. Known failed finalizations must remain explicit; if an applicable all-subject acceptance requirement is unproven, this outcome is unavailable.

Even then, `new_full22_authorized=false`, `message_model_contract_readiness=NOT_READY_PENDING_CHAT_REVIEW_AND_NEW_FULL22`, `deployment_readiness=NO`.

### Stop

Use precise `M12CG_R2_GUARD_REPAIR_FAILED`, `M12CG_R2_UNEXPECTED_VALID_INPUT_CHANGE`, `M12CG_R2_NATIVE_ACCEPTANCE_TRUST_BOUNDARY_NOT_PROVEN`, `M12CG_R2_REQUIRED_INTEGRATION_DESIGN_DECISION`, or source/base failure. Independent guard success may be recorded beneath an overall STOP; do not hide remaining blockers behind the first issue.

## 18. Subsequent order

Guard repair + owner-scoped offline closure → Chat review → only then a separately authorized wholly new Full22 from call 1 → Chat review → Kiwoom read-only gateway verification → Chat review → current US/KR market and monitored-stock message smoke → independent human judgment using collected facts before seeing the AI verdict → AI comparison → separate deployment/automation decision.

No output reuse/stitch, model retry/fallback/judge/repair/selective/per-ticker rerun in that future Full22. M12CE remains terminal at call8; never continue it. No PASS automatically authorizes a main merge, deploy, scheduler resume or real send.
