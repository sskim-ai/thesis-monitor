# Thesis Monitor — M12CG-R4 Finalization Frozen-Core Numeric Ownership Scope Repair + Offline Closure

## 0. Chat decision and bounded authorization

This is one concrete runtime repair following completed R3 W1 diagnosis. It is **not another broad audit, entry/holder redesign, symbolic migration, numeric-policy relaxation, delivery redesign or Full22 task**.

Work instruction: `20260916-m12cg-r4-finalization-frozen-core-numeric-ownership-scope-repair-offline-proof.md`.
Result ZIP: `thesis-monitor-20260916-m12cg-r4-finalization-frozen-core-numeric-ownership-scope-repair-offline-proof-report.zip` plus `.sha256`.

Authorize the smallest change that allows the integrated finalizer to preserve **exact, already-validated frozen Fundamental Core-owned claims** while retaining strict exact-number rejection for newly authored, mutated or unproven text. Reuse the existing canonical validators and owners; no new acceptance or evidence authority.

Expected application footprint: the exact-number scope in `app/services/accepted_decision_v2_service.py::validate_accepted_v2_decision` and its existing integrated caller in `app/services/accepted_decision_v2_runtime_service.py`, only as necessary. Prefer one owner plus minimal caller wiring; tests/harness/docs may change. A third application owner or a model/source/identity-policy change needs a demonstrated dependency and separate Chat authorization, not automatic expansion.

External model calls 0; Full22 generations 0; production actions 0. Existing isolated offline delivery sink is permitted for regression. Complete independent authorized regressions when a scoped blocker appears; no unauthorized runtime patch or dependent PASS.

## 1. Source integrity and exact base

The package includes all nine original result ZIPs M12CB through M12CG-R3, their sidecars, source index, prior R3-REV2 instruction, historical source map and Chat verification. Run `python verify_package.py` before changing code. It verifies only bytes and nested manifests, not runtime behavior. Preserve source ZIPs and old verdicts unchanged.

Latest R3 result SHA-256: `cfa1d9d86b08f6bc1ce5056ce73442602d72fa87bb6d5812c26296f75d8b83c3`.
Latest R3 manifest: 247 declared payloads, explicit self-exclusion. All nine expected hashes/counts are in `inputs/source-index.json`; resolve sources by that index, not an old host `/tmp` path or filename alone.

| Role | Value |
|---|---|
| Repository | `sskim-ai/thesis-monitor` |
| Required base / R3 final local docs | `5ea16d57ad50a1f7b44a31c11ae97471c30126bc` |
| R3 audit implementation | `ddc73fe70f67c1c10f4c49e18c2497af9f77d09f` |
| R3 instruction Git commit | `3bfb49b343d7502005e7a4dfbeddc683eaffa857` |
| R3 instruction content SHA-256 | `11f67ed26f50361d359b6838b71cf04fa673a4d8cb7a69a4932589b0c9417130` |
| Frozen guard runtime implementation | `50dcec1a56a81db1ebc7e23a322e69f9b028323a` |
| R3 required base / R2 final docs | `f15f299c668787171742aa1beda22415cc4e7537` |
| Exact pre-M12CG control | `912b1ce6c46f0caf801b2c620b42d904b489c4e7` |
| Historical origin observation, not current branch authority | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |

Use an isolated clean local worktree, suggested branch `codex/20260916-m12cg-r4-finalization-numeric-owner-scope`. Verify ancestry and runtime file hashes. The local R3 commit was not available through the Chat GitHub connection; do not push or substitute origin main to make it accessible. Export exact local rejecting function, regex, Core validation/binding chain, callers and their source hashes in the result. An unexplained base/source mismatch stops dependent work before patching.

Authority order: this instruction for authorization; verified R3 raw evidence for diagnosis; exact matching local repository for implementation; earlier source bundles for immutable regression. Older handoffs cannot reopen closed blockers.

## 2. Carry forward closed work; one open causal owner

R3 result: `M12CG_R3_NATIVE_DELIVERY_OFFLINE_PROOF_PASS_FINALIZATION_GAP_REMAINS`.

- W2: native offline delivery/binding/continuity proof PASS for D01-D14 / 29 recorded cases and generic subset fixtures, not a fresh full-packet Full22 run.
- W3: existing proof harness repaired; 35 historical IDs and 84 mapped evidence variants. Carry original scopes and rerun affected tests, not another architecture survey.
- R2 metadata-presence guard, symbolic R2 state/null contract, concrete MAX semantics, M12CB Stage-2 ownership scope and entry/holder investment semantics remain closed at their documented scopes.
- Historical inventory remains 62 rows / 20 snapshot candidates / 7 batches, including immutable original 010120 negative. Fresh observed M12CE inventory remains 42 rows / 9 subjects / 3 Stage-2 batches. M12CE stays terminal at call 8.
- R3 Stage-2 9/9; finalizations 7/9; legacy/R2 paired comparisons 6; GOOGL/HUT unfinalized. Diagnosis does not upgrade those historical results.

The only currently demonstrated application repair is the **downstream accepted-plan numeric ownership gate**. Do not count blocked renderer/acceptance tests as additional root defects.

## 3. Diagnosis and minimal red reproducer

Use R3 `audits/googl-hut-numeric-token-claim-ref-owner-trace.json` and complete `payloads/numeric-trace/` alongside immutable M12CE batch 02/context. The whole raw batch SHA is `8b55960daf4f6774713bf9a9462689d20a7a9bc6be108608fdbe0cf547f355f1`; context SHA is `6de8095b960786b9ee0ec572b9941730127459482c372e344667ea3a69cb0680`. Whole-batch, canonical subset and pretty-serialized payload hashes are different scopes; retain labels.

| Fixture | Rejected accepted-plan field | Matched inherited token(s) |
|---|---|---|
| GOOGL | `accepted_buy_drivers[1]` | `12.4172배` |
| GOOGL | `accepted_sell_drivers[1]` | `19.2893배`, `12.4172배` |
| HUT | `accepted_buy_drivers[0]` | `949MW` |
| HUT | `accepted_sell_drivers[1]` | `153.5593배`, `7.3898배` |

These are fixture observations, never production conditions. The exact text and refs match Core -> candidate -> accepted-plan same-role fields; accepting source is CANDIDATE. The final validator reports `adjudication_introduced_unregistered_numeric` by exact-number detection without a registry comparison. The error label does not prove adjudication authored the claim.

Before patching, read the actual local function/history and run the frozen reproducer through the real full finalizer; record the intended ValueError, predicate and source-chain checks. Verify both current numeric loops, including balance summary, and every caller. Do not infer which fields are Core-owned from `_EXACT_NUMBER` matches alone. If actual local behavior materially contradicts the evidence, stop that repair with the mismatch; do not force the diagnosis.

The historical origin implementation independently inspected in Chat supports the unconditional-gate diagnosis but is not a substitute for the current local file. Keep current function and call-site excerpts reproducible.

## 4. Owner-scoped fix: mandatory invariants

### 4.1 Default strictness is unchanged

`validate_accepted_v2_decision(packet, plan)` without independently established Core ownership remains strict. Existing callers, standalone validation, genuine adjudication-authored content and legacy paths do not gain a blanket numeric exemption. No `if accepted_source == CANDIDATE: skip_numeric` rule; no suppression of the error tuple after running validation; no always-true boolean or serialized trust marker.

Do not change `_EXACT_NUMBER`, units, thresholds, order-language checks, exact-ref fidelity, numeric registry or source facts. Do not turn `numeric_prose_eligible=false` into true, recursively harvest values from arbitrary evidence prose, or add a numeric allowlist. Core-source validation remains the authority it already was; this repair removes duplicate checking at the wrong ownership scope, not establishes a new numeric-validation policy.

### 4.2 Integrated permission must be derived from actual validated ownership

Reuse the real integrated chain before authorizing any narrow exclusion:

1. The trusted frozen Core was validated by its existing owner against the correct packet/market/ticker/assessment/evidence identity.
2. Its stored/recomputed canonical digest matches the previously frozen Core, not just a mutually edited candidate and model-supplied Core. Raw model self-declarations are not a trust source.
3. Candidate Core-owned fields and digest match that exact Core through the existing immutable ownership gate.
4. Accepted-plan source and composition are bound to that candidate and Core. Exact field/role, whole claim structure, text, refs, logical-condition metadata and ordering match the corresponding validated source.
5. All nonnumeric gates still run: identity, exact refs, source scope, order language, axes, maturity/polarity, pre/post-confirmation, change conditions, evidence sufficiency and accepted-plan consistency.

Use an existing context-aware API or a minimal internal validation-context adapter in the existing owners. Any derived allowance is runtime-local, constructed/recomputed after the real gates, never a model/payload field. A plain passed-in set of claims, user-supplied Core, plan status READY, source enum, digest string, or refs that merely exist is insufficient.

Do not launder ownership by copying a known Core claim into a Stage-2-only field, changing its buy/sell role, adding a ref, or replacing an accepted plan with another plan containing the same number. Bind the exception to the canonical composition path and exact field mapping.

### 4.3 Field and source restrictions

Initially authorize only the **direct CANDIDATE path demonstrated by R3** and the fields the existing Core contract truly owns (the observed buy/sell drivers; exact balance summary where ownership is independently established). Do not treat every accepted-plan claim as Core-owned.

Keep newly authored Stage-2 reasons, entry/holder explanations, conditions and other non-Core fields under their existing numeric restrictions, even if their text mentions a number found elsewhere in the packet. Preserve existing adjudication paths including KEEP_V1, KEEP_V2 and NEEDS_REPAIR. A claim merely copied by an adjudication does not gain the new direct-candidate permission in this task. No adjudication policy expansion is authorized; if an applicable regression establishes a distinct unresolved dependency, report it precisely without rewriting that path.

The whole field/claim must be unchanged. Text normalization, removing digits, rewriting units, replacing refs or reconstructing a shorter claim to pass is forbidden.

### 4.4 No representation/identity migration

Keep raw/model schema, prompt, catalog, output fields, normalized versions and serialized accepted-plan contracts unchanged. This is enforcement of the established ownership boundary, not a new payload contract. Do not serialize the runtime-local permission context or change IDs/hashes to disguise a difference. Existing finalization identities, renderer, state and receipt generation remain canonical.

A semantic schema/version redesign or new trusted receipt/ledger bridge is outside scope. Preserve the existing standalone contract and return precise errors for all other failures.

## 5. Targeted positive/negative coverage

Implement regressions before changing the gate; retain the red baseline. Parameterize generic cases across identities without ticker, date, token, Korean-text, row-index or ref-literal production branches.

| ID | Case | Required outcome |
|---|---|---|
| F01 | Original immutable GOOGL current-contract fixture | Full integrated finalization passes after fix; all text/refs/axes/Core unchanged |
| F02 | Original immutable HUT current-contract fixture | Same; no numeric rewrite/registry addition |
| F03 | Same complete M12CE batch GOOGL/HUT/IBM | 3/3 finalization via actual batch route; not stitched single-subject success |
| F04 | Other two available fresh batches | Existing six successes unchanged; fresh available total 9/9 and 3/3 batches |
| F05 | Valid same-role frozen Core numeric claims under other generic identities | Same owner-scoped result; no symbol-specific condition |
| F06 | Core-owned unchanged balance summary vs mutated/non-Core summary | Demonstrated owned case passes; unproven or changed case retains hard failure |
| F07 | Existing nonnumeric, standalone and legacy valid fixtures | Prior output/validation parity |
| F08 | Standalone numeric plan with no trusted Core context, even CANDIDATE/READY | Original strict rejection |
| F09 | Stage-2-owned exact numeric claim with a real ref | Hard failure; finding the number in packet prose grants no exception |
| F10 | Change one digit/unit/text/ref/logical condition in frozen claim | Existing identity/ownership or numeric gate rejects at intended boundary |
| F11 | Mutate Core and candidate together; stale/missing/forged Core digest | Actual frozen-source/binding rejection; self-consistency is not authority |
| F12 | Wrong packet/ticker/market/assessment/evidence fingerprint or copied Core from another batch | Hard identity/ownership rejection |
| F13 | Move copied claim into opposite role or non-Core field; keep numeric value | No field-agnostic exemption; intended existing gate remains hard |
| F14 | Add unproven allowed-looking claim/ref or exact-number Stage-2 sibling alongside an inherited claim | Only verified field permitted; sibling still fails |
| F15 | Genuinely new adjudication numeric text; all existing adjudication branches | Strictness/selection semantics unchanged; no blanket KEEP_V2 bypass |
| F16 | Raw model supplies an exemption/trust context, runtime field or forged metadata | Raw contract rejection; no privilege from untrusted payload |
| F17 | Bypass materializer in a test and pass tampered accepted plan to integrated validation | Independently recomputed binding/ownership rejects |
| F18 | Valid inherited number plus order command, unknown ref, bad polarity/primitive or decision condition | Nonnumeric gates still active, not suppressed by numeric permission |
| F19 | Existing M12CB scope, N21 mutation/Stage-2 exact-number and R2 missing/null guards | All prior negative boundaries preserved |
| F20 | Unchanged normalization/accepted-plan/renderer/identity fields | No difference except new acceptance of formerly blocked, unmodified plans |

For every negative record expected error class/code and layer, actual observed rejection and assertion outcome separately. An unrelated exception does not prove protection. Parameter counts and fixture IDs are different denominators; reuse repaired R3 aggregation with explicit expected variants and executed nodes. Do not introduce another proof-harness framework.

Tests may prepare ephemeral invalid copies, never edit source artifacts. Date and valuation tokens in historical text are not current market assertions.

## 6. Offline reproof and honest baselines

Run the original three complete fresh M12CE Stage-2 batches through the new integrated finalization path with matched Core/context/prior-state. Single-ticker traces remain diagnostics only. If both fixes pass, report new offline finalization 9/9 subjects and 3/3 batches, not US14/KR8 or Full22 PASS.

Replay the historical 62-row / 20-candidate / 7-batch inventory through already established boundaries; preserve concrete/mixed dates, original validity and the separate M12CD ephemeral conversions. The original 010120 date violation remains immutable and invalid. Record any deeper finalization coverage separately rather than demanding historical outputs all be positive or laundering them into a new generation.

For GOOGL/HUT, R3 has resolver-created `accepted-plan.json` that failed final validation; this is a preacceptance comparison object, **not a previously accepted or persisted artifact**. Compare new accepted semantic content and canonical plan identity to that unchanged object. New successful artifact creation is expected and must be labeled new offline evidence. Do not claim old accepted-artifact byte equality where no such artifact existed.

For the original seven fresh successful finalizations, require identical normalized candidate, plan, rendered output and canonical hashes under fixed equivalent inputs/clocks. Source packets, raw output and frozen Core bytes/hashes must never change. All candidate axes, maturity, polarity, reasons, expectation/valuation, BusinessDelta and evidence refs are immutable for the repair. No model-facing prompt/schema/catalog delta; export actual compared bytes, not only hash summaries. Manifest provenance-label differences are not model-visible differences.

## 7. Carry W2/W3 forward; regression is not redesign

Run the existing D01-D14 native tests and W3 harness controls after the finalization change, with the already-supported capture sink and temporary state. Reuse their code, owner mapping, existing event keys and policies. No new native path, receipt bridge, ledger or broad call-graph discovery.

Add only the necessary direct positive integration check that a newly finalized GOOGL/HUT-containing artifact follows the existing consumer/render path. When a native synthetic/subset fixture is needed, regenerate it through existing APIs, label the transformations and do not count it as original whole-batch delivery. Whole-batch acceptance from section 6 remains separate.

Carry the demonstrated operating guarantees precisely:

- Normal same-event re-entry after persisted success does not produce an unintended duplicate.
- A distinct authorized test event can send; an always-suppressed sink is not a positive proof.
- Invalid accepted-v2 material cannot authorize its own block/state. Existing safe base-AI delivery fallback, where exercised offline, is not a model fallback or acceptance of invalid v2 data.
- Diagnostic orchestration sidecar and native runtime message-quality receipt have different roles; do not interchange them.
- R3 crash-after-send/before-cursor case is at-least-once and can repeat a chunk. Preserve this documented limitation for later deployment review. No exactly-once claim or crash-policy redesign is authorized here.

All sink/message/state counts remain test-scoped. No real network, production credentials, persistent user state, notification recipient or broker access. Mock only external I/O/settings, not acceptance/identity/dedupe/state logic.

## 8. Execution and scope stop rules

1. Verify package/source bytes, local base and isolation. Carry the five-layer closure ledger forward.
2. Export exact local numeric predicate/callers and validated Core binding; reproduce both red cases on the frozen runtime. This is bounded pre-patch verification, not another open-ended owner audit.
3. Add ownership/field-boundary regressions and define the minimal API/caller scope.
4. Implement the existing-owner fix only, leaving strict defaults and all independent gates active.
5. Execute F01-F20 variants and fresh whole-batch finalization; compare all canonical payloads.
6. Replay historical normalization regressions; run existing native/harness suites with source-faithful labels.
7. Run focused/full/Treasury/Kiwoom suites, Ruff and `git diff --check`. R3 baseline: full 4133 pass/63 skip, focused223/1, Treasury79, Kiwoom70. Explain additions/selections; no silent skip growth/test deletion.
8. Freeze repair implementation, audit implementation and final docs SHAs separately. Generate actual payloads, granular results, parent statuses and one causal blocker ledger. Stop for Chat.

Normal local red/green test iteration is authorized before freeze. A distinct runtime/identity/semantic defect is not authority to widen the repair. Complete safe independent checks where possible; block dependent claims. Shared source/base/isolation failures stop affected execution. Do not multiply one cause into a new task per blocked downstream check.

If Core/source provenance cannot be established using existing owners, return `M12CG_R4_TRUSTED_CORE_BINDING_DEPENDENCY` with exact gate and reproducer; no self-declared trust shortcut. If a valid-input semantic/hash/model-facing delta occurs, return `M12CG_R4_UNEXPECTED_VALID_INPUT_CHANGE`. Genuine output violations stay negative; never rewrite them to force 9/9.

## 9. Required result artifacts

Keep artifacts compact but executable and complete:

- `source-base-integrity.json`, `repository-provenance.json`, `runtime-diff.patch` and exact old/new application source/caller excerpts with hashes;
- `finalization-core-owner-binding-contract.json` with actual call order, field mapping, default standalone behavior and why no new authority is introduced;
- `googl-hut-before-after-numeric-gate.json` with original context/raw/Core/plan, predicates, exact errors and new finalization outcomes;
- `finalization-positive-negative-variant-matrix.json`, collected/executed node IDs and assertion scopes;
- `fresh-whole-batch-finalization-matrix.json` and all complete batch inputs, normalized outputs, finalized artifacts and rendered messages;
- `historical-original-ephemeral-regression-matrix.json` with source bindings and immutable 010120 control;
- `candidate-core-plan-renderer-hash-parity.json`, actual before/after files and allowed differences only at newly successful acceptance;
- `model-facing-byte-parity.json` plus compared payload bytes;
- `native-regression-and-newly-finalized-integration.json` with existing sink traces/state and retained crash limitation;
- `harness-regression-results.json`, tests/commands/JUnit, Ruff and diff checks;
- `safety-counters.json`, `completion-layer-ledger.json`, `complete-blocker-ledger.json`, `program-completion.json`, result MD;
- `artifact-manifest.json` with relative paths/sizes/SHA and explicit self-exclusion, external ZIP SHA sidecar.

Include portable offline scripts and all failed/control outputs needed for independent comparison. Scripts must not hide model/network routes. Do not substitute diagnostics for full candidate files or count a suite PASS as a missing fixture. Historical output reuse is permitted only for these explicitly labeled offline tests.

## 10. Completion/reporting contract

Report already closed design/repair findings, fresh R4 work, actual remaining dependencies, model proof and deployment as separate layers. Measured zero needs a denominator; skipped/unavailable is NOT_PROVEN/NOT_RUN, not zero.

Required program fields include `top_level_result`, `required_base_sha`, `r3_result_sha256`, `instruction_git_sha`, `instruction_content_sha256`, `repair_implementation_sha`, `audit_implementation_sha`, `final_local_sha`, `changed_application_files`, `exact_local_predicate_verified`, `core_binding_owner`, `field_scope_mapping`, `standalone_numeric_strictness`, `adjudication_strictness`, `core_mutation_rejection`, `stage2_numeric_rejection`, `googl_before_after`, `hut_before_after`, `fresh_batch_count`, `fresh_stage2_subject_count`, `fresh_finalized_subject_count`, `fresh_failed_subject_count`, `historical_row_count`, `historical_original_negative_count`, `existing_successful_artifact_parity_count`, `newly_finalized_artifact_count`, `semantic_change_count`, `raw_or_core_hash_change_count`, `model_facing_byte_delta_count`, `native_regression_status`, `crash_window_guarantee`, `fixture_id_count`, `variant_required_count`, `variant_proven_count`, `completion_layers`, `causal_blocker_count`, `dependent_blocked_check_count`, safety counts and `new_full22_authorized=false` / `deployment_readiness=NO`.

`M12CG_R4_FINALIZATION_SCOPE_REPAIR_OFFLINE_CLOSURE_PASS` requires exact trusted ownership fix, positive full-batch acceptance of both original cases, complete available 9-subject finalization, preserved all negative/standalone/adjudication gates, immutable input/semantics, native/harness regressions and no silent waiver. This closes the demonstrated offline integration gap, not future fresh model coverage or production readiness.

`M12CG_R4_REPAIR_PASS_OTHER_OFFLINE_DEPENDENCY_REMAINS` is allowed only when the targeted repair is proven but a specifically evidenced required dependent check is not; keep its scope explicit. Otherwise use the exact failed gate or `M12CG_R4_FINALIZATION_SCOPE_REPAIR_FAILED`. Do not relabel earlier R3 or M12CE terminal results.

## 11. Frozen contracts, market context and subsequent order

No redesign of M12CB numeric scope, standalone numeric strictness, preconfirmation BUY, BUY/WAIT/HOLDABLE independence, atomic maturity polarity/eligibility, Core batch identity, exact-ref fidelity, typed primitives, postconfirmation HOLD, expectation/valuation ownership, BusinessDelta, Persistence V2 authority, symbolic R2/null/status, concrete MAX or presence guard.

Treasury remains FRED: nominal DGS3/DGS5/DGS10/DGS30, real DFII10, breakeven T10YIE; historical final renderer `4407cd11a78579e11681b503b2d4e72ee3c3d60f`; daily/per-series as-of/bp-change semantics frozen.

Kiwoom remains historical `28f4f70700046f98d5d899ee491d3e5f45922e9a`; KOSPI200 2026-09-01/02/03 replay and local LeadingMarket adapter PASS at historical scope. KOSDAQ150 actual historical fixture remains UNVERIFIED. Gateway last reported unavailable/unconfigured; read-only only. `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS` are names, not credentials. No gateway configuration, connector creation, live read/order/modify/cancel in R4.

Model calls, Full22, model retry/fallback/judge/repair/selective/per-ticker rerun all 0. Production sends/intents/DB mutations, remote pushes, main merge, deploy, scheduler start/resume/change and operating-checkout mutation all 0. Ordinary local tests and isolated sink re-entry are not model retries.

After R4: Chat reviews offline closure -> separately authorized wholly new US14/KR8 Full22 from call 1, no output reuse/stitch/model retries/fallback/judge/repair/selective/per-ticker rerun -> Chat -> Kiwoom read-only gateway verification -> Chat -> current US/KR market and monitored-stock message smoke -> independent human judgment from collected facts before reading the AI verdict -> AI comparison -> separate deployment/automation decision. Do not start the fresh proof in this task, even after offline PASS.
