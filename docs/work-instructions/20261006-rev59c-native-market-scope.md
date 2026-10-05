# Thesis Monitor — REV59C Native Market-Scope Repair + Final Fresh Strict Blind

## 0. Two-phase task
Phase A: offline native Market-scope controller repair + validation/Hosted CI.
Phase B: ONLY if Phase A fully PASS, run a new full-fresh final strict blind on the exact repaired HEAD.

This is not permission to repair/tune after Phase B starts.

Success terminal:
`R2B_R9_REV59C_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`

This authorizes only a separate Architecture Acceptance Review.

## 1. Predecessor gates
Verify before edits:
- REV59A ZIP SHA `62bb009d7aede553c47d9c5be043f733ad1843d810bcb4eeadd31ee3b6a7d574`
- REV59A terminal `R2B_R9_REV59A_CLEAN_START_STRICT_BLIND_CONTROLLER_PASS_READY_TO_RERUN_REV59`
- REV59A final HEAD `519ec4806065f7594579ab7740685cff92f23014`
- REV59B ZIP SHA `9f19e6d8eb64254d585683b8191f89060da8ae92e5c1709e229592725dcded9c`
- REV59B terminal `R2B_R9_REV59B_IMPLEMENTATION_REPAIR_REQUIRED`
- REV59B strict_run_started=false, generation=false, source/provider/model calls=0, production side effects=0.

REV59B root cause to repair:
native US/KR Market capture legitimately uses `stage=market`, `subjects=[]`; native capture accepts it, but the generic REV59A controller incorrectly applies a universal nonempty-subject invariant. Fake Market subjects are forbidden.

Start Phase A from exact REV59A final HEAD. Verify current origin/main separately and protected operating checkout; no protected mutation.

## 2. SoT reconciliation
PRESERVE all REV58D/E source authority, typed degradation, valuation isolation, B2 v2 semantics, REV59A CLEAN_START/host/raw-first/retry/isolation, and REVISED REV59 blind rubric/comparison/acceptance.

NEW FACT: native Market request is MARKET_SCOPED and legitimately has `subjects=[]`.

CHANGE ALLOWED only: typed request scope, US/KR market identity binding, controller admission/canonical authorization support, native-path parity tests.

FORBIDDEN: fake Market ticker, globally allowing empty subjects, weakening subject-scoped identity, changing native Market bytes, source/B2 economics, blind rules.

# PHASE A — OFFLINE REPAIR

## 3. Typed request scope
Implement/reuse:
`MARKET_SCOPED`
`SUBJECT_SCOPED`.

MARKET_SCOPED is allowed only for registered Market stages. It binds stage, scope, market=US|KR, generation, canonical request SHA, native market contract, and relevant schema/prompt/policy digests. `subjects=[]` is valid; fake subject is forbidden.

SUBJECT_SCOPED retains nonempty exact subjects/security binding.

## 4. US/KR Market identity
US and KR Market requests are not interchangeable. Wrong-market, wrong-generation, wrong-stage, changed-byte authorization must reject.

Extend canonical detached authorization without object equality or ticker/index-only authorization.

## 5. Mandatory native-path parity
Generic synthetic tests are insufficient. Using exact committed native US/KR Market capture/build paths and local fixtures, prove:
- exact native request construction;
- request bytes/SHA unchanged by controller integration;
- controller plan admission PASS;
- canonical detached CLEAN_START authorization PASS;
- raw-first simulated handling;
- native provider/schema/local semantic validation;
- output seal unlocks dependent stage;
- no fake subject.

Artifacts:
`native-us-market-controller-parity.json`
`native-kr-market-controller-parity.json`.

## 6. Subject-scope regression
Core, Pass A, production Pass B/Overall/Holder as applicable, blind per-subject requests, and B2 remain SUBJECT_SCOPED with nonempty subjects. Empty subjects reject.

## 7. Clean-start native E2E dry run
Repeat full REV59A offline lifecycle using actual native US/KR Market topology:
pre-data seals -> simulated source seal -> blind seal -> native Market -> remaining upstream -> upstream seal -> B2 seal -> both output seals -> reveal/comparison.
No historical failure/resume artifact.

## 8. Phase-A negative controls
At minimum:
US Market empty subjects valid; KR Market empty valid; fake Market subject reject; US-as-KR reject; KR-as-US reject; wrong generation/stage/bytes reject; Core/PassA/B2/blind empty subjects reject; representation-only tuple/list same SHA authorizes; CLEAN_START no failed ledger; RESUME safety unchanged; unchanged host valid; predeclared allowed host transition valid; unapproved transition reject; semantic reject non-retryable; reveal before both seals reject; repair registration after strict start reject.

## 9. Frozen architecture / validation
Semantic drift=0 for source authority, typed price state, coverage, metric/evaluability, Core/A/Overall/Holder, B2 v1/v2 prompt/schema/policy/validator, timing/risk/legacy visibility, blind rubric/schema/comparison/acceptance.

Before ANY external source/model call:
focused pytest, Ruff, git diff --check, full pytest, secret scan all PASS.

Then commit Phase-A repair, feature push only, remote SHA readback, Hosted feature CI PASS. Seal exact repaired HEAD. If any Phase-A gate fails: STOP; Phase B calls=0.

# PHASE B — FINAL FRESH STRICT BLIND

## 10. Conditional user authorization / admission
The user pre-authorizes Phase B only after all Phase-A gates PASS.

Allowed: new task-local full-fresh generation for existing 22; only presealed source DAG calls; independent blind reviewer; required fresh upstream reasoning; 22 B2 v2 calls with `gpt-5.6-sol`, `xhigh`, existing bounded timeout/retry; task-local evidence/result sealing.

Not allowed: production DB/WAL/official records, Telegram, scheduler, deploy/restart, operating checkout mutation, main merge/push, production promotion, onboarding/new tickers, provider additions outside sealed DAG, or code/harness repair after strict run starts.

If an inherently interactive credential/provider confirmation cannot be pre-authorized, stop before that action and request only it.

Bind Phase B to exact Phase-A repaired HEAD + Hosted CI PASS + clean worktree + CLEAN_START + protected state unchanged.

## 11. Strict-run boundary / pre-provider freeze
Run clean-start harness preflight. `strict_run_started` = first external source/provider call.

After it: code repair, adapter addition, continuation-policy addition, host exception, authorization reinterpretation = 0. New harness defect => stop/new revision.

Before first provider call seal:
execution plan, exact/conditional source DAG, blind rubric, blind response schema, blind controller policy, seven-axis comparison authority, acceptance policy.

Agreement rate is not a PASS threshold; no post-data/result rule change.

## 12. New full-fresh generation
Existing 22 only. New KR/US generation after Phase B starts.

Source DAG:
- mandatory usa20590 completed-close US14 = 14/14;
- usa06012 completed-close slots = 0;
- Alpha Vantage planned/actual = 0;
- all fallback slots predeclared.

Execute only planned slots. Preserve attempts.
After acquisition: generation identity -> raw/receipt seal -> SOURCE COLLECTION SEAL -> only then coverage/models.
After source seal adaptive recollection=0.

## 13. Fresh typed ownership
Owner coverage 22/22; unresolved required cells=0; complete provenance.
Then blocker census.

Metric states:
`USABLE | UNUSABLE_TYPED_DENIAL | NOT_RELEVANT | INVALID_CONTRADICTORY_OWNERSHIP`.
Contradictory=0; no cross-metric propagation.

Evaluability:
`EVALUABLE | ALL_RELEVANT_METRICS_UNUSABLE | INVALID_INCOMPLETE_CONTRACT`.
No invalid subject proceeds.

## 14. Source-only blind / isolation
Build blind package only from sealed current source/typed-owner evidence. Exclude current AI/v1, historical AI/blind labels/comparisons, v1-v2 delta, direct AI stance fields. Contamination=0.

Blind and Monitoring AI use separate workspace/context roots. Blind cannot read AI/v1. AI cannot read blind judgment content before AI seal; blind-seal existence/SHA only may be used for sequencing.

## 15. Blind judgment
Use presealed v2-native seven axes:
Overall; NewBuyer fundamental ATTRACTIVE/WAIT/AVOID; Entry timing FAVORABLE_NOW/WAIT_FOR_ZONE/UNRESOLVED; Holder; active risk; valuation evaluability; valuation state SUPPORTIVE/NEUTRAL/BURDENSOME/UNRESOLVED.

Timing cannot downgrade fundamental ATTRACTIVE. No universal cutoff, target/fair-value invention, implied-EPS reverse calculation, ticker rule, v1/historical target.

Seal blind requests before dispatch. Detached CLEAN_START authorization with typed request scope. Raw-first. Retry only transport/response-form; provider-schema-valid semantic reject=NO RETRY.

Seal 22/22 blind judgments before Monitoring AI execution/reveal. After seal relabel/rerun/request mutation=0.

## 16. Same-generation Monitoring AI
Only after blind seal, regenerate fresh production-equivalent Market/context -> Core -> Pass A -> Overall/production Pass B -> Holder -> active risk/business/timing using the repaired native MARKET_SCOPED US/KR path.

Blind content never input. No stale REV57/58E authority.

Each stage: prerequisite seal -> request build -> stage-local seal -> detached CLEAN_START authorization -> raw-first -> schema -> semantic validation -> output seal -> next.

Fresh upstream authority=22/22; stale=0.

Fresh v1 comparator is impact audit only, hidden from blind, not target/threshold.

## 17. B2 v2
Build 22 requests from same generation/fresh upstream using frozen B2 v2 contract. Legacy confidence prose model-visible=0; blind content absent.

Seal all requests before B2. Detached CLEAN_START authorization.

Model `gpt-5.6-sol`, `xhigh`, timeout 600s, existing max retries 2, physical cap 30, raw-first. Semantic reject after provider schema PASS=NO RETRY.

Seal 22/22 AI outputs before comparison. After AI seal rerun/mutation=0.

## 18. Reveal / comparison / semantic review
Only after both sides sealed. Use only presealed seven-axis comparison authority. No post-reveal mapping.

Review separately:
`SOURCE_BINDING | CONTRACT_SEMANTICS | ECONOMIC_JUDGMENT`.

Hard architecture errors: wrong generation/security/source, unavailable reconstruction, fake numeric fact, cross-metric propagation, axis leakage, active-risk violation, timing overwriting fundamental, legacy-confidence veto, stale authority.

SUPPORTIVE/NEUTRAL/BURDENSOME disagreement alone is economic judgment. Agreement rate alone is not PASS threshold.

## 19. Immutability / production isolation
After source seal source calls=0.
After blind seal blind rerun/relabel=0.
After AI seal AI rerun/mutation=0.
After reveal mapping/policy/threshold change=0.
After strict start code/harness repair=0.

Production DB/WAL/official records/Telegram/scheduler/deploy/restart/operating mutation/main merge/main push = 0.

## 20. Final success criteria
Require Phase A PASS + exact repaired HEAD/Hosted CI; Phase B CLEAN_START; pre-provider authorities sealed; new generation; source drift=0; adaptive recollection=0; usa20590 14/14; owner coverage 22/22; contradictory metrics=0; blind contamination=0; isolation PASS; blind 22/22 sealed before AI; fresh upstream 22/22/stale 0; B2 requests and outputs 22/22 sealed; source-binding hard errors=0; contract-semantic hard errors=0; active-risk violations=0; timing/fundamental conflations=0; legacy-confidence veto visibility=0; post-seal mutations=0; production side effects=0; presealed acceptance policy=PASS.

Success:
`R2B_R9_REV59C_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`.

## 21. Stop terminals
Use narrowest truthful terminal, including:
`R2B_R9_REV59C_REV59A_INTEGRITY_GAP`
`R2B_R9_REV59C_REV59B_INTEGRITY_GAP`
`R2B_R9_REV59C_REPOSITORY_IDENTITY_GAP`
`R2B_R9_REV59C_MARKET_SCOPE_REPAIR_GAP`
`R2B_R9_REV59C_NATIVE_MARKET_PARITY_GAP`
`R2B_R9_REV59C_SUBJECT_SCOPE_REGRESSION_GAP`
`R2B_R9_REV59C_FROZEN_ARCHITECTURE_DRIFT`
`R2B_R9_REV59C_PHASE_A_VALIDATION_GAP`
`R2B_R9_REV59C_FEATURE_CI_GAP`
`R2B_R9_REV59C_CLEAN_START_PREFLIGHT_GAP`
`R2B_R9_REV59C_PRE_DATA_AUTHORITY_SEAL_GAP`
`R2B_R9_REV59C_SOURCE_PLAN_GAP`
`R2B_R9_REV59C_SOURCE_COLLECTION_GAP`
`R2B_R9_REV59C_ADAPTIVE_SOURCE_RECOLLECTION_GAP`
`R2B_R9_REV59C_OWNER_COVERAGE_GAP`
`R2B_R9_REV59C_BLIND_INTEGRITY_GAP`
`R2B_R9_REV59C_BLIND_EXECUTION_GAP`
`R2B_R9_REV59C_UPSTREAM_EXECUTION_GAP`
`R2B_R9_REV59C_STALE_UPSTREAM_AUTHORITY_GAP`
`R2B_R9_REV59C_REQUEST_FREEZE_GAP`
`R2B_R9_REV59C_MODEL_EXECUTION_GAP`
`R2B_R9_REV59C_SOURCE_BINDING_GAP`
`R2B_R9_REV59C_CONTRACT_SEMANTIC_GAP`
`R2B_R9_REV59C_ACCEPTANCE_QUALITY_GAP`
`R2B_R9_REV59C_POST_SEAL_MUTATION_GAP`
`R2B_R9_REV59C_IMPLEMENTATION_REPAIR_REQUIRED`
`R2B_R9_REV59C_PROTECTED_STATE_GAP`

Do not repair/tune inside Phase B.

## 22. Result bundle / next step
Create `rev59c-result.zip` + `.sha256`, including predecessor integrity, Phase-A repair/parity/regression/tests/CI/repaired HEAD, Phase-B admission/pre-data seals/source/generation/coverage, blind package/isolation/requests/attempts/seal, upstream stage freezes/authorizations/outputs/authority, v1 comparator, B2 request/output seals, seven-axis comparison, semantic review, network/protected/final identities, bundle manifest.

No credentials/API keys/recipient IDs.

Only after success terminal may a separate Architecture Acceptance Review be created. Do not automatically integrate main or promote production.
