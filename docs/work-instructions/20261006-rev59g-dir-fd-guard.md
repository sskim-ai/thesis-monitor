# Thesis Monitor — REV59G dir_fd-Aware Mutation Guard Repair + Final Strict Blind Reproof

## 0. Two-phase task
Phase A repairs/proves filesystem mutation-target ownership for dir_fd-aware operations without weakening protected-root or unknown-path fail-closed behavior.
Phase B runs a genuinely new full-fresh final strict blind ONLY after Phase A full validation + actual Hosted CI PASS.

This is not a blind/source/valuation/B2 economic redesign.

Success:
`R2B_R9_REV59G_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`

This authorizes only Architecture Acceptance Review.

## 1. Predecessor
Verify `rev59f-result.zip` SHA:
`1eef03fb354046ddfed4551332e33f9a39561eaf7b3039b84015c680b95b63c2`

Expected classified terminal:
`R2B_R9_REV59F_UPSTREAM_EXECUTION_GAP`

Expected HEAD:
`51d13ac745499885cf3a4196dc7580014eb5633f`

Expected Phase A:
blind-capability-contract-v2 implemented; frozen R1 replay remains 18 PASS/4 FAIL; candidate semantic replay 13 PASS/9 FAIL; candidate admission old artifacts 0/22; no old output rewrite; source/B2 production contract drift 0; focused 366 PASS; full 8597 PASS/63 skip; actual Hosted CI PASS.

Expected Phase B:
new generation `REV59F-20261006T092157Z`; provider calls 652; source sealed; recollection after seal 0; formal blind 22 attempts, 22 PASS, retry 0, sealed=true; Market/Core/A/B/B2 calls 0; reveal=false; production side effects 0.

Expected failure:
after blind seal, fresh Market request construction uses native builder inside `TemporaryDirectory`. Cleanup calls `os.unlink(entry.name, dir_fd=topfd)`. Existing `ManualMutationGuard` ignores dir_fd ownership and interprets the relative child as cwd-relative/protected, causing `R2B_R9_REV31_C1_MANUAL_STATE_MUTATION_BLOCKED`.

No confirmed protected write occurred. Strict run was not repaired/resumed.

## 2. Repair boundary
Preserve all source authority, typed degradation, blind-capability-contract-v2, seven-axis blind contract, clean-start controller, MARKET_SCOPED/SUBJECT_SCOPED, raw-first/non-retry, B2 economics, protected-root safety, and unknown-target fail-closed behavior.

Allowed only:
dir_fd-aware target resolution; canonical filesystem mutation target identity; guard audit receipts; actual native-builder+guard composition tests; equivalent src_dir_fd/dst_dir_fd handling for already-guarded operations.

Forbidden:
disable guard; blanket /tmp allowlist; unknown dir_fd allow; swallowing guard exceptions; weakening protected roots; REV59F path exceptions; source/blind/B2 semantic changes; resuming stopped REV59F generation.

# PHASE A — GUARD REPAIR

## 3. Canonical mutation-target identity
For every guarded mutation bind operation, raw path, absolute/relative, dir_fd/src_dir_fd/dst_dir_fd, resolved fd directory identity, canonical absolute target, symlink/traversal handling, protected-root relation, ownership decision, resolution confidence.

Relative path without dir_fd uses existing cwd semantics.
Relative path with valid dir_fd resolves relative to the actual directory referenced by that descriptor, not cwd.
Absolute path keeps absolute semantics.
Unresolvable/ambiguous dir_fd => DENY.

## 4. dir_fd resolution controls
Prove ordinary temp directory fd, nested temp fd, protected repo fd, protected operating fd, closed/stale fd, non-directory fd, reused fd, `..` traversal, dot/repeated separators, and absolute child with dir_fd.

Never trust caller textual hints.

## 5. Guarded-operation matrix
Audit all mutation primitives already intercepted by `qualified_official_launch_context.py`, including unlink/remove/rmdir/rename/replace/link/symlink/mkdir and any guarded chmod/chown/open-write/truncate operations.

For each existing primitive, dir_fd/src_dir_fd/dst_dir_fd semantics must be correctly resolved or explicitly rejected fail-closed. Do not expand permissions.

## 6. Actual TemporaryDirectory/native-builder composition
Install the actual parent guard and execute the actual strict-blind Monitoring native request builder offline inside a real TemporaryDirectory.

Require:
- request bytes/SHA equal unguarded qualified builder;
- cleanup completes;
- every cleanup target resolves inside created temp root;
- no protected-root target allowed;
- no allowlist exception or guard bypass.

This exact composition was missing in REV59F.

## 7. Protected-root negative controls
Reject at minimum:
absolute protected unlink; relative unlink with protected dir_fd; nested protected relative unlink; temp→protected rename; protected→temp rename; protected src_dir_fd; protected dst_dir_fd; symlink escape; `..` traversal; closed/unresolved fd; non-directory fd; fd reuse mismatch; unknown resolution; protected operating target.

## 8. Task-local positive controls
Allow under existing ownership policy:
absolute temp unlink; relative temp unlink via dir_fd; nested TemporaryDirectory cleanup; temp rename within owned root; temp mkdir/rmdir; native builder cleanup; task-local blind workspace cleanup where applicable.

No production-path expansion.

## 9. No guard-policy weakening
Protected roots unchanged. Allowlisted roots unchanged except representation normalization with no semantic expansion. Unknown target remains DENY. Manual-state policy unchanged. Guarded operation set not reduced. Audit logging preserved.

## 10. Full guarded clean-start offline lifecycle
With repaired actual guard installed and zero network/model calls:
pre-data seals → simulated source/generation/seal → real blind adapter fixture lifecycle → blind seal → actual native US/KR Market builders → Core/A/B builders → B2 builder → all temp cleanup → output seals → reveal/comparison.

No monkeypatch removing guard.

## 11. Frozen architecture regression
Drift=0 for blind-capability-contract-v2, seven-axis prompt/schema/validator, source authority, typed price state, metric/evaluability, Core/A/Overall/Holder, B2 v1/v2 economics, timing/fundamental separation, clean-start authorization, workspace isolation, retry/raw-first, production isolation.

## 12. Phase-A validation/CI
Require focused guard tests, focused composition tests, Ruff, git diff --check, full pytest, secret scan PASS.

Then commit feature branch, feature push only, remote SHA readback, actual Hosted CI PASS. Seal exact repaired HEAD.

Any Phase-A failure => STOP with Phase-B provider/model calls=0.

# PHASE B — NEW FINAL STRICT BLIND

## 13. Conditional authorization
User pre-authorizes Phase B only after Phase A fully PASS.

Allowed shadow-only: new full-fresh generation existing 22; only presealed source DAG; independent blind reviewer under frozen blind-capability-contract-v2; fresh upstream reasoning; 22 B2 calls using gpt-5.6-sol/xhigh existing bounded retry; task-local evidence/results.

Not authorized: production DB/WAL/official records, Telegram, scheduler, deploy/restart, operating checkout mutation, main merge/push, production promotion, onboarding/new tickers, providers outside DAG, guard/code/adapter repair after strict start.

## 14. Strict admission / pre-provider freeze
Verify exact repaired HEAD, Hosted CI PASS, clean worktree, protected state, guard composition proof, full guarded lifecycle preflight, blind contract digests, workspace isolation.

Seal admission. `strict_run_started` = first external source/provider call. After it no code/guard/adapter/authorization repair.

Before first provider call seal execution plan, source DAG, blind rubric/prompt/schema/capability contract, comparison authority, acceptance policy. No later changes.

## 15. New generation/source seal
Existing 22 only. New KR/US generation.
Require usa20590 US14=14/14; usa06012 completed-close=0; Alpha Vantage=0; fallbacks predeclared.

Execute planned source slots only.
Then generation identity → immutable raw receipts → SOURCE COLLECTION SEAL → owner coverage/models.
After seal adaptive recollection=0.

## 16. Fresh ownership/blind capabilities
Owner coverage 22/22; unresolved required cells=0; complete provenance. Use frozen metric/evaluability contracts; contradictory ownership=0; no cross-metric propagation. Materialize blind capabilities only from this generation.

## 17. Formal blind
Build/seal 22 SUBJECT_SCOPED requests. Blind context has no current/historical AI/v1 labels.
Detached CLEAN_START authorization; raw-first; transport/form retry only; semantic reject after schema PASS=NO RETRY.

First formal semantic failure => preserve and halt; no continuation counted toward formal cohort.
Formal blind seals only at 22/22 PASS.
After seal relabel/rerun/request mutation=0.

## 18. Same-generation Monitoring AI/B2
Only after formal blind seal.

Regenerate fresh Market→Core→Pass A→Overall/production Pass B→Holder→risk/business/timing using repaired guard during native builders. Blind content never input; no stale authority.

Stage-local seals; detached authorization; raw-first; semantic non-retry.
Fresh upstream 22/22, stale=0.

Then build/seal/run B2 22/22 with frozen B2 v2 contract. No AI rerun after seal.

## 19. Reveal/comparison
Only after both formal seals. Use presealed seven-axis comparison authority.
Separate SOURCE_BINDING / CONTRACT_SEMANTICS / ECONOMIC_JUDGMENT.
No agreement-rate threshold and no post-reveal mapping/threshold changes.

## 20. Success criteria
Require predecessor integrity; general dir_fd target identity fail-closed; protected-root negative controls PASS; task-local cleanup positives PASS; actual native builder+actual guard composition PASS; no guard-policy weakening; guarded full lifecycle PASS; frozen architecture drift=0; Phase-A full validation+actual Hosted CI PASS; new generation; source drift/recollection=0; owner coverage 22/22; blind contamination=0; formal blind 22/22 PASS/sealed; fresh upstream 22/22/stale 0; B2 22/22 sealed; source-binding/contract hard errors=0; timing/fundamental conflations=0; post-seal mutations=0; production side effects=0; presealed acceptance policy PASS.

Success:
`R2B_R9_REV59G_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`

## 21. Stop terminals
Use narrowest truthful:
`R2B_R9_REV59G_REV59F_INTEGRITY_GAP`
`R2B_R9_REV59G_MUTATION_TARGET_IDENTITY_GAP`
`R2B_R9_REV59G_DIR_FD_RESOLUTION_GAP`
`R2B_R9_REV59G_PROTECTED_ROOT_REGRESSION_GAP`
`R2B_R9_REV59G_NATIVE_BUILDER_GUARD_COMPOSITION_GAP`
`R2B_R9_REV59G_GUARD_POLICY_WEAKENING_GAP`
`R2B_R9_REV59G_GUARDED_LIFECYCLE_GAP`
`R2B_R9_REV59G_FROZEN_ARCHITECTURE_DRIFT`
`R2B_R9_REV59G_PHASE_A_VALIDATION_GAP`
`R2B_R9_REV59G_FEATURE_CI_GAP`
`R2B_R9_REV59G_SOURCE_PLAN_GAP`
`R2B_R9_REV59G_SOURCE_COLLECTION_GAP`
`R2B_R9_REV59G_OWNER_COVERAGE_GAP`
`R2B_R9_REV59G_BLIND_EXECUTION_GAP`
`R2B_R9_REV59G_UPSTREAM_EXECUTION_GAP`
`R2B_R9_REV59G_MODEL_EXECUTION_GAP`
`R2B_R9_REV59G_SOURCE_BINDING_GAP`
`R2B_R9_REV59G_CONTRACT_SEMANTIC_GAP`
`R2B_R9_REV59G_ACCEPTANCE_QUALITY_GAP`
`R2B_R9_REV59G_POST_SEAL_MUTATION_GAP`
`R2B_R9_REV59G_PROTECTED_STATE_GAP`

Do not repair/tune inside Phase B.

## 22. Result / next
Create `rev59g-result.zip` + `.sha256` containing predecessor integrity, mutation-target contract, operation matrix, positive/negative controls, native-builder guard composition, guard-policy regression, guarded lifecycle, validation/CI/repaired HEAD, Phase-B source/generation/coverage, blind requests/attempts/seal, upstream/B2 seals, comparison, semantic review, network/protected/final identities, manifest.

Only after success terminal may Architecture Acceptance Review be created. Do not automatically integrate main or promote production.
