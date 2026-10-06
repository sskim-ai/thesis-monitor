# Thesis Monitor — REV59F Blind Capability-Contract Alignment + Final Strict Blind Reproof

## 0. Task identity

REV59F is a two-phase task.

Phase A: offline source-only review and bounded repair of three general blind capability-contract boundaries exposed by REV59E-R1.

Phase B: ONLY if Phase A proves a general, non-target-fitted contract and passes full validation/Hosted CI, execute a genuinely new full-fresh final strict blind.

This is NOT permission to rewrite failed outputs, create ticker exceptions, relax validators to accept observed answers, or optimize agreement rate.

Success terminal:
`R2B_R9_REV59F_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`

This authorizes only a separate Architecture Acceptance Review.

## 1. Predecessor integrity

Verify both immutable predecessors before edits.

REV59E:
SHA `4c1c317bb5fa65ad9056da05beb69008bc27519918bd9c3585b3f3fd07d1a642`
terminal `R2B_R9_REV59E_BLIND_INTEGRITY_GAP`
head `12261040946b5fad3283bba957fddc4d7f52f5bf`.

REV59E-R1:
SHA `b22f3de7673e58e69bf57e5bb1ac0346c1abbbf366b19640ec91fb82b0dbc51e`
final classified terminal `R2B_R9_REV59E_CONTRACT_SEMANTIC_GAP`
head `fa78e2d1989a2756bad5e6d6c061d48d47deda0c`.

Verify sidecars, CRC, manifests, raw-attempt seals, strict-run journals, diagnostic namespace separation, source/model counts, protected state, and that the original failed strict run was never resumed or rewritten.

Expected R1 facts:
- bounded null-price representation repair PASS;
- focused 350 PASS;
- full 8581 PASS / 63 skipped;
- actual Hosted CI PASS;
- new generation `REV59E-R1-20261006T052557Z`;
- source coverage 22/22, unresolved required cells 0;
- usa20590 14/14;
- Alpha Vantage 0;
- source recollection after seal 0;
- strict blind halted after 13 attempts on WRD semantic failure;
- semantic retry 0;
- Market/Core/A/B/B2 calls 0;
- separate user-authorized diagnostic executed only the remaining 9 frozen blind requests;
- combined diagnostic: 22 attempted, 18 semantic PASS, 4 semantic FAIL;
- formal strict cohort NOT sealed;
- comparison/reveal NOT executed;
- architecture acceptance NOT ready.

## 2. Architecture SoT / anti-target-fitting

Preserve all source authority, typed degradation, valuation isolation, clean-start controller, MARKET_SCOPED/SUBJECT_SCOPED typing, live blind adapter, B2 v2 economics, and strict-blind protocol.

The four failed outputs are diagnostic evidence of contract boundaries. They are NOT target labels.

Do not:
- edit/rewrite WRD/010120/047810/086280 outputs;
- add ticker-specific branches;
- loosen a validator merely because an observed output failed;
- add a relation/capability only to admit one failed output;
- use agreement rate as PASS threshold;
- reuse R1 source generation as a new strict PASS;
- rerun failed requests during Phase A.

Every contract change must be justified from source ontology and general semantics independent of the observed model answer.

# PHASE A — GENERAL CONTRACT REVIEW / REPAIR

## 3. Failure taxonomy

Treat the observed failures as three distinct contract families.

A. TIMING_RELATION_REF_COMPLETENESS
- 010120 and 086280 selected WAIT_FOR_ZONE.
- Frozen owner contains matching WAIT_FOR_ZONE relations.
- Output failed to cite a complete owner relation ref set.

B. TIMING_RELATION_CAPABILITY_MISMATCH
- 047810 selected FAVORABLE_NOW.
- Frozen owned range relations contain WAIT_FOR_ZONE only.
- Risk/reward/chart context does not automatically own FAVORABLE_NOW.

C. RISK_HOLDER_ONTOLOGY
- WRD: model treated absolute operating-loss level as active material risk, while frozen capability owner classified cited comparable-period loss narrowing/revenue growth as DIRECTIONAL_POSITIVE.
- 086280: Holder REVIEW with active_material_risk=false conflicts with current Holder-risk contract.

Do not collapse these into one validator issue.

## 4. Timing relation ownership review

Independently inspect the existing timing source ontology and producer/dataflow.

Define the authoritative relation object for each timing option:
- state;
- exact range/support/resistance relation;
- evidence refs required to own that state;
- relation provenance;
- generation/security binding.

Determine whether current blind package/prompt exposes these relation objects clearly enough for a model to cite the complete relation set.

For WAIT_FOR_ZONE, the model must cite the exact owned support/range relation, not merely nearby risk/reward or resistance context.

For FAVORABLE_NOW, define what source-owned relation is required. Do NOT infer FAVORABLE_NOW from generic attractive risk/reward unless the preexisting timing architecture actually grants that capability.

Artifact:
`timing-relation-authority-review.json`.

## 5. Timing contract repair boundary

Permissible repair if independently justified:
- materialize owned timing options as explicit structured capabilities in the blind source package;
- require each selected timing state to carry an exact `timing_relation_id` or complete relation-ref set;
- update prompt/schema/validator together so the model chooses only from owned relation capabilities;
- preserve UNRESOLVED when no owned relation supports a directional timing state.

Forbidden:
- adding FAVORABLE_NOW for 047810 because the model chose it;
- treating arbitrary R/R context as relation ownership;
- accepting missing support refs after the fact;
- ticker exceptions.

The same contract must work generically across all 22 and synthetic negative controls.

## 6. Absolute-level risk vs directional-change ontology review

Independently inspect source facts and capability ownership.

Separate at least:
- ABSOLUTE_LEVEL_ADVERSE_STATE
- DIRECTIONAL_DETERIORATION
- DIRECTIONAL_IMPROVEMENT
- PERSISTENT_MATERIAL_RISK
- NO_ADVERSE_CAPABILITY

A source fact may be directionally improving while its absolute level remains adverse. These are not logical opposites.

Determine whether existing source facts contain sufficient source-owned information to support an absolute-level adverse capability without inventing thresholds.

Requirements:
- no universal loss-margin/earnings cutoff;
- no ticker-specific threshold;
- no model-created adverse fact;
- exact source value/period/security provenance;
- capability owner must state what proposition is source-supported, not whether the stock should be AVOID.

Artifact:
`absolute-level-risk-capability-review.json`.

If source facts cannot support a general absolute-level capability without new subjective thresholds, do NOT add it. Preserve the current directional capability and document that the model may not elevate the absolute level to active material risk from those refs.

## 7. Active material risk contract

Review the distinction between:
- an adverse source observation;
- a material/persistent business risk capability;
- model economic judgment.

A model may judge severity only within capabilities actually exposed by the source contract.

If a versioned risk capability is added, it must be general and source-owned, with exact evidence/provenance and no ticker rules.

Do not make `operating_income < 0` automatically equal active material risk unless that rule was independently predeclared and economically justified outside these outputs.

## 8. Holder-risk axis review

Independently define Holder states and their required capabilities.

Determine whether `REVIEW` semantically requires `active_material_risk=true`, or whether Holder REVIEW may also be supported by a distinct holder-specific deterioration/watch capability that is not an active material risk.

Do not decide this from 086280 alone.

If current architecture intentionally defines REVIEW/REDUCE as active-risk-only, keep it and make blind capability/prompt explicit.

If the broader existing Holder architecture already supports a separate watch/review capability, represent that capability explicitly and version the blind contract accordingly.

Artifact:
`holder-risk-axis-review.json`.

No ticker exception.

## 9. Versioned blind contract

If Phase-A review proves changes are needed, create a versioned blind capability contract.

It must bind:
- source-only capability types;
- timing relation ownership;
- risk capability ownership;
- Holder capability ownership;
- prompt/schema/validator digests;
- comparison semantics if affected.

Do not change B2 v2 prompt/schema/policy/economics.

Do not alter historical sealed R1 outputs.

Artifact:
`blind-capability-contract-v2.json`.

## 10. Frozen R1 replay — diagnostic only

Replay all 22 sealed R1 blind outputs against:
1. original frozen validator;
2. candidate versioned contract, if any.

This is diagnostic only.

Report which failures would change and WHY at the general contract level.

Candidate acceptance MUST NOT require all four observed failures to become PASS.

A candidate that simply admits all four outputs without independent ontology proof fails anti-target-fitting.

Artifact:
`r1-frozen-output-contract-replay.json`.

No model calls.

## 11. Counterfactual / negative controls

At minimum prove:
- WAIT_FOR_ZONE with exact owned support relation PASS;
- WAIT_FOR_ZONE with only resistance/RR refs FAIL;
- FAVORABLE_NOW without owned FAVORABLE_NOW relation FAIL;
- FAVORABLE_NOW with independently owned relation PASS;
- directional improvement alone cannot become adverse capability;
- independently source-owned absolute adverse capability can coexist with directional improvement;
- active risk cannot be asserted without an admitted adverse/material capability;
- Holder REVIEW obeys the final generic Holder capability rule;
- timing remains independent from fundamental NewBuyer;
- no source capability automatically determines valuation attractiveness;
- no ticker-specific rules;
- wrong generation/security refs reject;
- historical AI/v1 labels remain inaccessible.

## 12. Offline full lifecycle

Run the full live blind adapter lifecycle with source-only fixtures spanning all revised capability classes.

Then run full clean-start offline lifecycle:
source seal simulation -> owner/metric state -> blind 22 -> blind seal -> fresh upstream simulation -> B2 seal -> reveal/comparison.

No external/model calls.

No fixture-only marker response.

## 13. Frozen architecture regression

Require drift=0 for:
- usa20590/usa06012 authority;
- typed price state;
- metric resolution/evaluability;
- Core/A/Overall/Holder production semantics except any explicitly versioned blind-only Holder capability representation;
- B2 v1/v2 economics;
- timing/fundamental separation;
- legacy confidence visibility;
- clean-start/authorization/raw-first/retry rules;
- production isolation.

Any B2 economic drift is a hard failure.

## 14. Phase-A validation / CI

Require focused tests, Ruff, diff, full pytest, secret scan.

Then commit Phase-A repair on feature branch, feature push only, remote SHA readback, actual Hosted CI PASS.

Seal exact repaired HEAD and all prompt/schema/validator/capability digests.

If any Phase-A gate fails: STOP; Phase-B provider/model calls=0.

# PHASE B — NEW FINAL STRICT BLIND

## 15. Conditional authorization

User pre-authorizes Phase B only after Phase A fully PASS.

Allowed shadow-only:
- genuinely new full-fresh source generation for existing 22;
- only presealed source DAG calls;
- independent blind reviewer using the qualified versioned contract;
- required fresh upstream reasoning;
- 22 B2 v2 calls using gpt-5.6-sol/xhigh and existing bounded retry;
- task-local evidence/result sealing.

Not authorized:
production DB/WAL/official records, Telegram, scheduler, deploy/restart, operating checkout mutation, main merge/push, production promotion, onboarding/new tickers, providers outside DAG, or repair after strict start.

## 16. Strict-run admission / pre-provider freeze

Verify exact Phase-A repaired HEAD, Hosted CI PASS, clean worktree, protected state, blind capability contract, workspace isolation, full clean-start preflight.

Before first provider call seal:
- execution plan;
- source DAG;
- blind rubric/prompt/schema/capability contract;
- comparison authority;
- acceptance policy.

`strict_run_started` = first external source call.

After it no code/prompt/schema/validator/capability/adapter repair.

## 17. New generation / source seal

Existing 22 only.
New KR/US generation.

Require usa20590 US14=14/14, usa06012 completed-close=0, Alpha Vantage=0, all fallback slots predeclared.

Execute planned source slots only.

Then generation identity -> immutable raw receipts -> SOURCE COLLECTION SEAL -> only then coverage/models.

After seal adaptive recollection=0.

## 18. Fresh owner / metric state

Owner coverage 22/22; unresolved required cells=0; complete provenance.

Use exact frozen metric/evaluability contracts. Contradictory ownership=0. No cross-metric denial propagation.

Build source-only blind capabilities only from this same generation.

## 19. Blind execution

Build/seal 22 SUBJECT_SCOPED requests.

Blind workspace has no current/historical AI/v1 labels.

Detached CLEAN_START authorization.
Raw-first.
Transport/form retry only.
Semantic reject after provider schema PASS=NO RETRY.

Strict semantics:
- on first semantic failure, preserve and halt the formal strict run;
- no failed request retry;
- no diagnostic continuation inside the formal strict run;
- any later diagnostic must be a separately labeled post-failure artifact and cannot be combined into formal PASS.

Seal blind 22/22 only if all 22 formally PASS.

## 20. Same-generation Monitoring AI / B2

Only after formal blind 22/22 seal.

Regenerate fresh Market/Core/A/Overall/Holder/risk/business/timing from same generation; no blind content input; no stale authority.

Stage-local seals, detached authorization, raw-first, semantic non-retry.

Then build/seal 22 B2 requests with frozen B2 v2 contract; run gpt-5.6-sol/xhigh; seal 22/22 AI outputs.

No AI rerun after seal.

## 21. Reveal / seven-axis comparison

Only after both formal seals.

Use presealed comparison authority.

Separate SOURCE_BINDING / CONTRACT_SEMANTICS / ECONOMIC_JUDGMENT.

Agreement rate is not PASS threshold.

No post-reveal mapping/threshold change.

## 22. Success criteria

Require:
- predecessor integrity;
- general capability review completed without target fitting;
- any versioned contract independently justified;
- frozen R1 replay diagnostic only;
- counterfactual controls PASS;
- B2/source architecture drift=0;
- Phase-A full validation + actual Hosted CI PASS;
- new generation;
- source drift/adaptive recollection=0;
- owner coverage 22/22;
- blind contamination=0;
- formal blind 22/22 PASS and sealed;
- no semantic retry/diagnostic continuation counted in formal cohort;
- fresh upstream 22/22/stale 0;
- B2 22/22 sealed;
- source-binding hard errors=0;
- contract-semantic hard errors=0;
- timing/fundamental conflations=0;
- post-seal mutations=0;
- production side effects=0;
- presealed acceptance policy PASS.

Success:
`R2B_R9_REV59F_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`.

## 23. Stop terminals

Use narrowest truthful, including:
`R2B_R9_REV59F_PREDECESSOR_INTEGRITY_GAP`
`R2B_R9_REV59F_TIMING_RELATION_CONTRACT_GAP`
`R2B_R9_REV59F_RISK_CAPABILITY_ONTOLOGY_GAP`
`R2B_R9_REV59F_HOLDER_RISK_CONTRACT_GAP`
`R2B_R9_REV59F_ANTI_TARGET_FITTING_GAP`
`R2B_R9_REV59F_BLIND_CONTRACT_VERSION_GAP`
`R2B_R9_REV59F_FROZEN_ARCHITECTURE_DRIFT`
`R2B_R9_REV59F_PHASE_A_VALIDATION_GAP`
`R2B_R9_REV59F_FEATURE_CI_GAP`
`R2B_R9_REV59F_SOURCE_PLAN_GAP`
`R2B_R9_REV59F_SOURCE_COLLECTION_GAP`
`R2B_R9_REV59F_OWNER_COVERAGE_GAP`
`R2B_R9_REV59F_BLIND_INTEGRITY_GAP`
`R2B_R9_REV59F_BLIND_EXECUTION_GAP`
`R2B_R9_REV59F_UPSTREAM_EXECUTION_GAP`
`R2B_R9_REV59F_MODEL_EXECUTION_GAP`
`R2B_R9_REV59F_SOURCE_BINDING_GAP`
`R2B_R9_REV59F_CONTRACT_SEMANTIC_GAP`
`R2B_R9_REV59F_ACCEPTANCE_QUALITY_GAP`
`R2B_R9_REV59F_POST_SEAL_MUTATION_GAP`
`R2B_R9_REV59F_PROTECTED_STATE_GAP`

Do not repair/tune inside Phase B.

## 24. Result / next

Create `rev59f-result.zip` + `.sha256` including predecessor integrity, three ontology reviews, versioned contract if any, R1 frozen replay, counterfactual controls, offline lifecycle, validation/CI/repaired HEAD, Phase-B source/generation/coverage, blind requests/attempts/formal seal, upstream/B2 seals, comparison, semantic review, protected/network/final identities, manifest.

Only after success terminal may Architecture Acceptance Review be created. Do not automatically integrate main or promote production.

