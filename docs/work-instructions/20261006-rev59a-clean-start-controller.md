# Thesis Monitor — REV59A Clean-Start Strict-Blind Controller Repair

## 0. Purpose
REV59A is a bounded clean-start execution-controller / authorization repair plus offline strict-blind lifecycle proof.

It is NOT a source-authority, valuation, B2 economic-policy, blind-judgment, deployment, or onboarding task.

Success means only: the final strict-blind controller can start from a clean fresh generation without REV58E failure/resume artifacts while preserving canonical request identity, native host qualification, blind/AI isolation, retry semantics, raw-first capture, and all frozen architecture contracts.

No source/provider/model call is allowed.

## 1. Architecture SoT
Preserve the project principle: source authority and typed unavailable/denied states are explicit; Market/Business/Valuation/Timing/Risk stay separate; missing data does not destroy independent evidence or unrelated subjects; every decision is same-generation and sealed-provenance reproducible.

## 2. Predecessor
Immediate predecessor: `rev59-result.zip`
Expected SHA-256:
`30d5f9524c661509d7b73346adda9e92175cf4b90933428f29ac6910d52a2190`
Expected terminal:
`R2B_R9_REV59_IMPLEMENTATION_REPAIR_REQUIRED`

Expected facts: REV58E architecture PASS remains accepted; product architecture failure was not proven; new generation/source/provider/model/blind/upstream/B2 calls all 0; tracked changes and production side effects 0.

Expected blockers:
1. Same canonical request SHA: Python tuple authorization membership FAIL, persisted JSON list PASS, changed hash FAIL.
2. Fresh B2/upstream execution route depends on historical failed ledger, continuation/controller freeze, and continuation authorization.
3. Resume-specific host route requires a CODEX_SANDBOX transition even though native owner allows unchanged host or explicitly allowed predeclared transition.

## 3. Repository
Parent: `a2068cab2bfc2e6d61a6c1b3408594a0ca7a84aa`
origin/main: `9b134350cd05c127b6dc866d34a477d95c54785c`
protected operating HEAD: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
Suggested branch: `codex/r2b-r9-rev59a-clean-start-controller`.

Before edits prove exact identities, clean worktree, protected snapshot, B2 v2 default-OFF. No rebase/force-push/protected mutation.

## 4. REV59 integrity
Verify sidecar SHA, CRC, manifest/member hashes, exact REVISED REV59 instruction, terminal, zero calls, exact three blockers, protected state. Artifact `rev59-integrity.json`. Mismatch: `R2B_R9_REV59A_REV59_INTEGRITY_GAP`.

## 5. SoT reconciliation
Create `controller-reconciliation.json`.

PRESERVE: REV58D/E source authority, typed price state, owner coverage, metric/evaluability semantics, fresh upstream causal staging, B2 v2 prompt/schema/policy/validator, retry boundary, blind protocol, production isolation.

NEW FACT: final strict-blind clean start is blocked by orchestration glue, not source/B2 semantics.

ROOT CAUSE: runtime-container-shape authorization + fresh execution coupled to historical failure/resume artifacts + resume-specific host assumptions.

CHANGE ALLOWED only: canonical serialized request authorization, clean-start state machine, native host qualification integration, offline strict-blind orchestration, tests/receipts.

CHANGE FORBIDDEN: provider topology/authority, valuation economics, B2 contracts, blind rubric/comparison/acceptance semantics, retry semantics, ticker behavior, production behavior.

## 6. Canonical request identity
Authorization must use canonical persisted identity, not Python object equality. Bind at least request SHA, canonical serialization version, logical request ID, stage, subject/batch, generation, and relevant schema/prompt/policy digests.

Required:
- same canonical bytes represented tuple/list/in-memory/persisted JSON => same authorization;
- changed SHA => reject;
- same logical ID but changed bytes => reject;
- same bytes but wrong generation/stage => reject.
No ticker/index-only authorization.
Artifact `canonical-request-identity-proof.json`.

## 7. Explicit execution modes
Define:
`CLEAN_START`
`RESUME_AFTER_RETRYABLE_EXECUTION_FAILURE`.

New final strict blind uses CLEAN_START and must NOT require historical failed ledger, continuation authorization, controller freeze, failed-attempt artifact, or REV58E continuation receipt.

Resume mode keeps its genuine resume safety requirements. Do not weaken resume safety.
Artifact `execution-mode-contract.json`.

## 8. Clean-start state machine
At minimum:
PREFLIGHT → PRE_SOURCE_AUTHORITIES_SEALED → SOURCE_COLLECTION → SOURCE_COLLECTION_SEALED → BLIND_PACKAGE_SEALED → BLIND_JUDGMENT_EXECUTION → BLIND_JUDGMENTS_SEALED → UPSTREAM_EXECUTION → UPSTREAM_AUTHORITY_SEALED → B2_REQUESTS_SEALED → B2_EXECUTION → B2_OUTPUTS_SEALED → REVEAL_COMPARISON → COMPLETE.

No historical failed ledger dependency in CLEAN_START. Illegal backward transitions fail closed. No source call after source seal; no blind rerun after blind seal; no B2 rerun after B2 seal.
Artifact `clean-start-state-machine.json`.

## 9. Native host qualification
Clean start must use native host-owner semantics:
- unchanged host => QUALIFIED;
- explicitly predeclared allowed transition => QUALIFIED_ALLOWED_TRANSITION;
- unapproved transition => DENIED_HOST_TRANSITION;
- missing provenance => fail closed.
Do not require a host difference merely because old resume controller did.
Artifact `host-qualification-proof.json`.

## 10. Detached authorization
Every future dispatch authorization binds execution mode, stage, generation, sealed request-set SHA, canonical request SHA, model/effort/timeout/cap, host receipt, prerequisite seals. It must not mutate request bytes. CLEAN_START authorization cites no prior failed ledger.
Artifact `detached-authorization-contract.json`.

## 11. Blind / Monitoring AI isolation
Offline-prove separate blind and Monitoring AI workspace/context roots.

Blind may receive only sealed source-only package, blind rubric/schema, and pre-judgment comparison/acceptance instructions. Monitoring AI may receive same-generation source/owner/upstream authority and frozen B2 inputs plus blind-seal existence/SHA if needed, but not blind judgment content before AI seal. Blind cannot read AI/v1 output.

Artifact `workspace-isolation-proof.json`; static path/context scan must show no forbidden pre-reveal cross-read.

## 12. Pre-provider authority seal
Before first future source call controller must be able to seal: blind rubric, blind response schema, comparison authority, acceptance policy, blind controller policy, source execution plan, source-request DAG. Preserve REVISED REV59 semantics; do not redesign them.
Artifact `pre-provider-authority-seal-proof.json`.

## 13. Retry / raw-first invariants
Retry only transport/response-form failure. Provider-schema-valid + deterministic local semantic reject = NO RETRY for blind/upstream/B2. Preserve existing taxonomy.

Every model attempt: durable raw receipt → SHA → parse → provider schema → local semantic validation. Artifact `raw-first-controller-proof.json`.

## 14. Strict-run repair boundary
`strict_run_started` = first external source/provider call of future REV59 rerun.

Before it, preflight may fail and a separate repair revision is allowed. After it: no new adapter, continuation policy, host exception, authorization reinterpretation, code repair, mapping/threshold change. Unplanned harness defect after start => stop and new revision.
Artifact `strict-run-boundary-contract.json`.

## 15. Offline full lifecycle dry run
Synthetic/local fixtures only, zero external calls. Demonstrate:
1 pre-provider seals;
2 source-plan admission;
3 simulated collection;
4 generation identity;
5 source seal;
6 simulated owner/metric/evaluability gate;
7 blind package seal;
8 blind request authorization;
9 simulated raw-first blind outputs;
10 blind output seal;
11 upstream stage-local seal/authorization/output seal;
12 upstream authority seal;
13 B2 request seal;
14 B2 detached authorization;
15 simulated raw-first B2 outputs;
16 B2 output seal;
17 reveal gate opens only after both seals;
18 comparison complete;
19 no historical failed ledger/continuation artifact used.
Artifact `clean-start-e2e-dry-run.json`.

## 16. Negative controls
At minimum:
1 same SHA tuple/list => same authorization;
2 changed SHA reject;
3 wrong generation reject;
4 wrong stage reject;
5 CLEAN_START without failed ledger allowed;
6 CLEAN_START requiring failed ledger fails test;
7 RESUME without required failed ledger rejects;
8 unchanged host qualifies;
9 predeclared allowed host transition qualifies;
10 unapproved host transition rejects;
11 blind reads AI output => reject;
12 AI reads blind judgment before AI seal => reject;
13 source call after source seal => reject;
14 blind rerun after blind seal => reject;
15 B2 rerun after B2 seal => reject;
16 reveal before both seals => reject;
17 semantic reject marked retryable => reject;
18 adapter registration after strict start => reject;
19 result-dependent continuation authorization => reject;
20 ticker-specific exception => reject.
Artifact `negative-controls.json`.

## 17. Frozen architecture regression
Require zero semantic drift in US completed-close authority, usa06012 technical role, typed price contracts, owner coverage, metric/evaluability, Core/A/Overall/Holder, B2 v1, B2 v2 prompt/schema/policy/validator, timing separation, active-risk precedence, legacy visibility, and blind rubric/comparison/acceptance semantics.
Artifact `frozen-architecture-regression.json`.
Any drift: `R2B_R9_REV59A_FROZEN_ARCHITECTURE_DRIFT`.

## 18. No external execution
Hard zero: source/provider/recollection/Alpha Vantage calls, blind/upstream/B2 model calls, production DB/WAL, official records, Telegram, scheduler, deploy/restart, operating mutation.

## 19. Validation
Code changes expected. Require focused pytest PASS, Ruff PASS, git diff --check PASS, full pytest PASS, secret scan PASS. Preserve failed attempts; do not weaken tests.

## 20. Feature commit / CI
Only after local gates: commit REV59A feature branch, feature push only, remote SHA readback, Hosted feature CI PASS. No main merge/push/deploy.

## 21. Protected state
End state protected operating HEAD must remain `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`; production side effects 0.

## 22. Success criteria
Require:
- REV59 integrity PASS and exact parent;
- representation-independent canonical authorization; changed bytes/generation/stage fail closed;
- CLEAN_START exists and requires no historical failure/resume artifacts; RESUME safety preserved;
- native host qualification handles unchanged/predeclared transition and rejects unapproved transition;
- detached authorization binds canonical identity;
- blind/AI isolation PASS;
- pre-provider blind/comparison/acceptance authorities sealable;
- retry semantics unchanged; raw-first preserved; strict-run boundary enforced;
- full offline clean-start strict-blind lifecycle PASS with no historical failed-ledger dependency;
- all 20 negative controls PASS;
- frozen architecture drift = 0;
- external source/provider/model calls = 0;
- production side effects = 0;
- focused/full/Ruff/diff/secret PASS;
- feature push/readback and Hosted CI PASS;
- protected state unchanged.

Success terminal:
`R2B_R9_REV59A_CLEAN_START_STRICT_BLIND_CONTROLLER_PASS_READY_TO_RERUN_REV59`

This authorizes only a new REV59-equivalent final fresh strict-blind run. It does not authorize architecture acceptance or production promotion.

## 23. Stop terminals
Use narrowest truthful:
`R2B_R9_REV59A_REV59_INTEGRITY_GAP`
`R2B_R9_REV59A_REPOSITORY_IDENTITY_GAP`
`R2B_R9_REV59A_SOT_RECONCILIATION_GAP`
`R2B_R9_REV59A_CANONICAL_REQUEST_IDENTITY_GAP`
`R2B_R9_REV59A_EXECUTION_MODE_GAP`
`R2B_R9_REV59A_HOST_QUALIFICATION_GAP`
`R2B_R9_REV59A_DETACHED_AUTHORIZATION_GAP`
`R2B_R9_REV59A_WORKSPACE_ISOLATION_GAP`
`R2B_R9_REV59A_PRE_PROVIDER_SEAL_GAP`
`R2B_R9_REV59A_RETRY_SEMANTICS_GAP`
`R2B_R9_REV59A_RAW_FIRST_GAP`
`R2B_R9_REV59A_STRICT_RUN_BOUNDARY_GAP`
`R2B_R9_REV59A_CLEAN_START_DRY_RUN_GAP`
`R2B_R9_REV59A_FROZEN_ARCHITECTURE_DRIFT`
`R2B_R9_REV59A_FULL_VALIDATION_GAP`
`R2B_R9_REV59A_FEATURE_CI_GAP`
`R2B_R9_REV59A_PROTECTED_STATE_GAP`

## 24. Result bundle
Create `rev59a-result.zip` + `.sha256`, including REPORT/summary, REV59 integrity, reconciliation, repository/protected receipts, canonical identity proof, execution-mode/state-machine/host/detached-authorization/workspace/pre-provider/raw-first/strict-boundary proofs, E2E dry-run, negative controls, frozen architecture regression, focused/full/Ruff/diff/secret results, network events, feature push/CI, final identities, bundle manifest. No credentials.

## 25. Next step
Do not execute automatically. Only after success terminal above, create/run a new final fresh strict-blind revision from the repaired feature HEAD. That run must start a genuinely clean generation and may not rely on REV58E/REV59 failure/resume artifacts.

Only a later strict-blind PASS may proceed to Architecture Acceptance Review.
