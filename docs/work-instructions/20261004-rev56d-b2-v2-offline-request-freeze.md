# Thesis Monitor — REV56D B2 v2 Offline Implementation + Request Freeze

**Revision note:** independently reviewed against the sealed REV56C result. The core v2 implementation plan is retained, with four fail-closed clarifications: (1) metric usability is composed from the complete REV56C category-cell ownership rather than ref counts alone; (2) BUSINESS_GLOBAL quality can affect the business gate only through exact linkage to the gate-supporting evidence; (3) legacy confidence/quality prose is backend-audit-only and is not model-visible in B2 v2; (4) entry timing remains an independent axis and must not erase a SUPPORTIVE fundamental/valuation NewBuyer stance.

## 0. Task identity

Work-instruction filename:

`rev56d-work.md`

Work-instruction ZIP:

`rev56d-work.zip`

Required result bundle:

`rev56d-result.zip`

Required result sidecar:

`rev56d-result.zip.sha256`

This is a bounded **NewBuyer B2 v2 implementation + offline 22-subject replay + exact model-request freeze** task.

It is NOT:

- a model execution task;
- a fresh source recollection task;
- a fresh/current-data shadow task;
- a Core / Pass A / Overall / Holder redesign;
- a legacy Core claim rewrite;
- a blind-label fitting task;
- a new-ticker onboarding task;
- a production deployment task;
- a scheduler / Telegram / production DB task.

The task consumes the completed REV56C typed owner coverage and blocker census.

Success in REV56D means:

> B2 v2 is implemented, validated offline, default-OFF, exact requests are frozen, and REV57 may be designed/executed separately.

No model call is allowed in REV56D.

---

# 1. Authoritative predecessor result

Immediate predecessor:

`rev56c-result.zip`

Expected SHA-256:

`c8f9cc7e9acbc6531995f645d5ecf268dfb5b40aacce0d8c60c224a7c4d9991e`

Expected terminal:

`R2B_R9_REV56C_KIS_NO_ESTIMATE_OWNER_COVERAGE_PASS`

Expected repository identities:

```text
origin/main
9b134350cd05c127b6dc866d34a477d95c54785c

production-code baseline before REV56C
45f4c53f6113575f91a067c423d471023cd4f560

REV56C parent
9bd94d753fd8ef5efff963c5ca65f15b6ce45965

REV56C final feature HEAD
1907898a7e478f240b51d1cee9d1a69cac094080

protected operating checkout
b610e6de0a8c33d199961e821ff1b130e1fa9ad4
```

Expected REV56C facts:

```text
coverage_complete = true
complete_subjects = 22
unresolved_required_cells = 0

total_cells = 506
PROVEN_APPLICABLE = 311
PROVEN_NOT_APPLICABLE = 195

owner_provenance_complete = true
temporal_provenance_complete = true
decision_provenance_complete = true

coverage receipt SHA-256
c2ce41bdbe5cf35ac2202a895a197b5110700f110ca6512fd52dd6b857531f0d

current_blocker_count = 37
blocker_census_complete = true

blocker census receipt SHA-256
96c6d93ec3b9aa7664bc5f6975f27466f93a05d06d2f05ea663756df00a610ff

blocker scopes:
35 METRIC_SCOPED
2 BUSINESS_GLOBAL
0 VALUATION_GLOBAL emitted

legacy refs unchanged = 95
legacy entitlement changes = 0

accepted B2 v1 outputs = 22
B2 v1 branches = 168

active-risk safety = 7/7 AVOID-only

003690 native PER preserved
003690 FY1 fPER remains unavailable/nonnumeric
003690 no-estimate blocker is METRIC_SCOPED only

B2 v2 implemented = false
model calls = 0
source/provider calls = 0
deploy = 0
operating mutation = 0
```

REV56D must not weaken any of these facts.

---

# 2. Repository identity gate

Start from the exact REV56C final feature HEAD:

`1907898a7e478f240b51d1cee9d1a69cac094080`

REV56C was feature-pushed and remote-readback/Hosted CI passed.

Before branching:

1. verify the commit object locally;
2. if absent, fetch the exact REV56C feature branch and prove the fetched SHA equals the expected SHA;
3. prove `origin/main` separately;
4. prove clean worktree;
5. prove protected operating checkout separately;
6. snapshot protected state.

Suggested new branch:

`codex/r2b-r9-rev56d-b2-v2`

Do not:

- branch from `origin/main` and pretend equivalence;
- rebase;
- force-push;
- merge to main;
- modify the operating checkout.

Unexpected identity:

`R2B_R9_REV56D_REPOSITORY_IDENTITY_GAP`

---

# 3. Verify REV56C immutable result first

Before implementation verify:

- sidecar SHA;
- ZIP CRC;
- manifest membership;
- per-member size;
- per-member SHA;
- no missing/extras;
- expected terminal;
- expected feature HEAD;
- coverage 22/22;
- provenance completeness 3/3;
- blocker census count 37;
- census receipt SHA;
- coverage receipt SHA;
- global valuation blocker count 0;
- native PER preservation;
- B2 v1 unchanged;
- active-risk 7/7.

Required artifact:

`rev56c-integrity.json`

Mismatch terminal:

`R2B_R9_REV56D_REV56C_INTEGRITY_GAP`

---

# 4. Frozen inputs only

Use exactly the frozen cohort and source generations inherited from REV56C.

```text
US = rev46-us14-resume1-20261002T064847Z
KR = rev47-kr8-20261002T114556Z
subjects = 22
```

No source recollection.

No price refresh.

No valuation refresh.

No business-evidence refresh.

No external provider calls.

Alpha Vantage calls:

`0`

REV56D is implementation/replay only.

---

# 5. Blind integrity

The prior independent blind assessment and post-reveal comparison may be hash-verified only.

Do not use:

- desired ATTRACTIVE count;
- desired BUY/WAIT/AVOID labels;
- 003690 desired result;
- 012450 desired result;
- GOOGL desired result;
- any agreement percentage

to design v2 behavior.

No ticker-specific decision logic.

No after-the-fact branch edits based on frozen model labels.

Target fitting terminal:

`R2B_R9_REV56D_TARGET_FITTING_GAP`

---

# 6. Preserve B2 v1 exactly

Do not mutate:

`newbuyer-qualified-valuation-context-v1`

B2 v1 must remain byte/behavior reproducible.

Required:

```text
accepted_v1_outputs = 22
validated_v1_branches = 168
```

unchanged.

Build v2 as a separate versioned contract.

Suggested identity:

`newbuyer-qualified-valuation-context-v2`

Suggested isolated modules, names may differ:

```text
scripts/newbuyer_b2_v2_contract.py
scripts/newbuyer_b2_v2_policy.py
scripts/newbuyer_b2_v2_shadow.py
scripts/newbuyer_b2_v2_validator.py
```

B2 v2 is default OFF.

No production caller may switch to v2 in this task.

---

# 7. REV56C blocker census is evidence, not automatic veto policy

REV56C sealed an exhaustive census of 37 typed current-owner eligibility denials.

Do NOT interpret:

```text
37 blocker census entries
```

as:

```text
37 enabled NewBuyer vetoes
```

All REV56C census entries were sealed with:

```text
activation = NOT_ENABLED
```

REV56D must define an explicit **axis-role policy** before activating any effect.

Required artifact:

`blocker-role-policy.json`

For every blocker category/scope combination define exactly one policy role.

Allowed roles:

```text
METRIC_ELIGIBILITY_ONLY
BUSINESS_GATE_QUALITY
NEWBUYER_CONFIDENCE_VETO
GLOBAL_VALUATION_VETO
CONTEXT_ONLY
```

Role assignment must come from typed semantics, not legacy prose or blind labels.

No role may be inferred from the word "blocker" alone.

---

# 8. Scope policy for the 37 current blocker receipts

At minimum enforce:

## METRIC_SCOPED

Default role:

`METRIC_ELIGIBILITY_ONLY`

Effect:

- affected metric is unusable;
- unaffected valuation metrics remain usable;
- does not directly create `CONFIDENCE_UNCERTAINTY`;
- does not directly create `AVOID`;
- does not become a global valuation veto.

This includes the 003690 normal-empty FY1 fPER denial.

## BUSINESS_GLOBAL

May use:

`BUSINESS_GATE_QUALITY`

only if the current typed owner is **exactly linked to the evidence that satisfies the B2 business gate**.

Required linkage proof:

```text
business_quality_blocker_ref
→ exact affected source/business evidence ref(s)
→ exact Core positive/negative capability ref(s) derived from those inputs
→ business-gate contribution
```

Shared ticker, shared quarter, shared parent source, or generic `BUSINESS_GLOBAL` scope is not enough.

After applying the exact quality denial, recompute the gate support deterministically:

```text
eligible_positive_core_refs_after_quality
eligible_negative_core_refs_after_quality
```

A BUSINESS_GLOBAL quality denial may set:

```text
business_evidence_admissible = false
```

only if the exact required business-gate support is invalidated under the versioned business-gate contract.

If at least one independent eligible positive Core ref still satisfies the gate and no other gate predicate fails, do not kill the gate merely because a different business-quality observation is denied.

It must not become a valuation state.

It must not rewrite Core/Overall.

If exact linkage to the business-gate evidence cannot be proven, use `CONTEXT_ONLY` and fail closed before claiming a business veto.

## NEWBUYER_CONFIDENCE_VETO

May be used only for a typed current owner whose explicit semantics are genuinely cross-cutting NewBuyer confidence/admissibility.

Do not classify `BUSINESS_SOURCE_QUALITY` or `VALUATION_SOURCE_QUALITY` as generic confidence merely to preserve the old branch.

If no REV56C current blocker qualifies for this role:

```text
NEWBUYER_CONFIDENCE_VETO count = 0
```

is valid.

## GLOBAL_VALUATION_VETO

Do not assign this role to a metric-scoped blocker.

REV56C emitted no native `VALUATION_GLOBAL` blocker.

Any all-metrics-unusable state must be proved compositionally under Section 10 rather than promoting one metric blocker.

---

# 9. Legacy 95 confidence/quality refs after complete coverage

REV56C proved complete backend owner coverage.

Therefore B2 v2 may now define axis-specific legacy entitlement.

Do NOT rewrite historical Core claims.

Do NOT mutate their original:

```text
effect
materiality
claim text
source refs
```

Create a separate v2 entitlement sidecar.

Required artifact:

`legacy-v2-entitlement.json`

For each of the 95 refs record:

```text
ticker
claim_ref
historical_claim_preserved = true
original_effect
original_materiality

v2_newbuyer_veto_entitlement
linked_current_blocker_refs
linkage_basis
coverage_receipt_sha256
blocker_census_receipt_sha256

model_visible_in_b2_v2 = false
renderer_or_audit_context_only = true

claim_semantics_reclassified = false
blind_label_used = false
```

Allowed v2 entitlement states:

```text
CONTEXT_ONLY_NO_VETO_ENTITLEMENT
CURRENT_TYPED_VETO_BOUND
```

Default after complete coverage:

`CONTEXT_ONLY_NO_VETO_ENTITLEMENT`

A legacy ref may be `CURRENT_TYPED_VETO_BOUND` only if there is an exact structured linkage independent of prose interpretation.

Shared ticker alone is not enough.

Shared parent source alone is not enough.

If exact linkage does not exist, keep the legacy ref context-only and let the current typed blocker stand independently.

**Model-visibility rule:** the legacy confidence/quality prose and its semantic text must not be included in the B2 v2 provider/model input. This prevents the old confidence escape hatch from being laundered into a valuation-state choice such as `NEUTRAL` or `BURDENSOME`.

If a current typed veto exists, pass the **current typed blocker contract/ref/reason**, not the historical prose claim.

Legacy refs remain available to backend audit and later renderer/explanation layers, but outside the v2 valuation-model decision input.

---

# 10. New valuation evaluability contract

Before subject-level evaluability, create a deterministic per-metric resolution receipt:

`NewBuyerValuationMetricResolutionV2`

Required artifact:

`metric-resolution-v2.json`

For every relevant valuation metric slot, derive exactly one:

```text
USABLE
UNUSABLE_TYPED_DENIAL
NOT_RELEVANT
INVALID_CONTRADICTORY_OWNERSHIP
```

A metric is `USABLE` only if:

```text
metric is relevant under the frozen B2 metric contract
AND a qualified valuation fact exists
AND every required REV56C category cell for that metric is PROVEN_APPLICABLE
AND no typed current denial blocks that exact metric ref
```

A metric is `UNUSABLE_TYPED_DENIAL` only when exact current-owner denial/blocker refs cover that metric.

`PROVEN_NOT_APPLICABLE` cells do not block the metric; they prove that domain is not consumed.

Hard invariants:

```text
usable_metric_refs ∩ blocked_metric_refs = empty
every blocked ref matches the exact metric slot it blocks
no cross-metric denial propagation
no simple "qualified ref exists" shortcut when a required category cell denies eligibility
```

If the same metric appears simultaneously qualified and denied without an explicit typed precedence/supersession contract, mark:

`INVALID_CONTRADICTORY_OWNERSHIP`

and reject the v2 request.

Then create the subject-level deterministic backend contract:

`NewBuyerValuationEvaluabilityV2`

For each subject compute:

```text
relevant_valuation_metric_refs
metric_resolution_refs
qualified_relevant_valuation_refs
metric_blocker_refs
blocked_metric_refs
usable_valuation_metric_refs

coverage_receipt_ref
blocker_census_receipt_ref

evaluability_state
all_metrics_unusable_proof
```

`usable_valuation_metric_refs` must equal the exact set of per-metric receipts in state `USABLE`; do not compute it by a loose ref-count heuristic.

Allowed `evaluability_state`:

```text
EVALUABLE
ALL_RELEVANT_METRICS_UNUSABLE
INVALID_INCOMPLETE_CONTRACT
```

## EVALUABLE

Required:

```text
usable_valuation_metric_refs nonempty
```

Model valuation choices must be exactly:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

`UNRESOLVED` is forbidden.

## ALL_RELEVANT_METRICS_UNUSABLE

Allowed only if:

- the relevant metric universe is explicit;
- complete REV56C owner coverage applies;
- every relevant metric is unusable through exact typed current-owner evidence;
- no independently qualified usable metric survives;
- all contributing blocker refs are recorded.

This may be a **composite evaluability proof**.

Do not mutate the underlying metric-scoped blockers into `VALUATION_GLOBAL`.

Required:

```text
all_metrics_unusable_proof = true
usable_valuation_metric_refs = []
```

The v2 valuation state may then be deterministically constrained to:

`UNRESOLVED`

with exact blocker refs.

## INVALID_INCOMPLETE_CONTRACT

This must never be model-resolvable.

Reject the request before model execution.

For the frozen 22 cohort expected count must be 0 because REV56C coverage is complete.

---

# 11. No free valuation UNRESOLVED

For any subject with:

```text
evaluability_state = EVALUABLE
```

the v2 schema and validator must make `UNRESOLVED` structurally impossible.

The model cannot abstain because:

- no universal fair-value threshold exists;
- there is no target price;
- there is no absolute fair-value range;
- valuation feels uncertain;
- legacy confidence prose exists;
- one different valuation metric is unavailable.

The model must make an economic contextual judgment:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

using only the qualified usable valuation facts.

---

# 12. No valuation-evidence laundering

Never use legacy confidence/context prose as evidence for:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
UNRESOLVED
```

Never use business evidence as valuation evidence.

Never use blocker prose as valuation facts.

The backend contract must physically separate:

```text
valuation_fact_refs
valuation_metric_blocker_refs
business_blocker_refs
active_risk_refs
timing_refs
legacy_context_refs_backend_only
```

The **provider/model-visible v2 request must omit `legacy_context_refs_backend_only` and the legacy prose content entirely**.

The model-visible valuation decision may consume:
- qualified usable valuation facts;
- permitted current business context needed to interpret those facts;
- typed current blocker states that the capability contract explicitly authorizes.

It may not consume historical confidence/quality prose as a hidden substitute for valuation evidence or veto authority.

Required audit:

`axis-evidence-separation-v2.json`

The audit must prove both:
- ref-role separation; and
- model-input visibility separation.

---

# 13. Business gate

Preserve the existing B2 business gate semantics as the base:

```text
Overall == BUY
AND current Core positive refs nonempty
AND current Core negative refs empty
AND active material business-risk refs empty
```

Do not alter Core or Overall to obtain more positive capability.

Add a separate v2 business-evidence admissibility layer only if justified by `BUSINESS_GATE_QUALITY` blocker-role policy.

Suggested derived fields:

```text
base_business_gate_pass
base_business_positive_refs
base_business_negative_refs

business_quality_blocker_refs
business_quality_linkage_refs
eligible_positive_core_refs_after_quality
eligible_negative_core_refs_after_quality

business_evidence_admissible
v2_business_gate_pass
```

If a BUSINESS_GLOBAL current owner is activated as `BUSINESS_GATE_QUALITY`, it may change the gate only through the exact linkage/recomputation rule in Section 8.

Do not automatically set the entire business gate false merely because a BUSINESS_GLOBAL census entry exists.

The exact WAIT reason must be typed, e.g.:

`BUSINESS_EVIDENCE_UNCERTAINTY`

Do not overload it into valuation `UNRESOLVED`.

Do not call it active material risk.

Do not convert it into AVOID.

---

# 14. Active material risk precedence is frozen

Exact active-risk cohort remains:

```text
CORZ
CPNG
HUT
RXRX
TSLA
WULF
047810
```

Required deterministic safety:

`7/7 AVOID-only`

Active material risk takes precedence over valuation/timing.

No v2 change may:

- expose ATTRACTIVE;
- downgrade active risk to WAIT;
- let cheap valuation compensate active risk;
- suppress active-risk evidence.

Failure terminal:

`R2B_R9_REV56D_ACTIVE_RISK_SAFETY_GAP`

---

# 15. Timing remains backend-owned and independent

Preserve existing timing states:

```text
FAVORABLE_NOW
WAIT_FOR_ZONE
UNRESOLVED
```

Do not redesign technical timing.

Do not infer fair value from timing zones.

Do not let legacy confidence prose alter timing.

**B2 v2 stance scope remains fundamental/valuation NewBuyer attractiveness, not a buy-now execution signal.**

Therefore timing must not downgrade an otherwise valid:

```text
SUPPORTIVE valuation
+ eligible business gate
+ no active material risk
```

from `ATTRACTIVE` to `WAIT`.

Timing remains a separate mandatory output/context field.

A later renderer may show, for example:

```text
NewBuyer attractiveness = ATTRACTIVE
Entry timing = WAIT_FOR_ZONE
```

without converting the fundamental stance to WAIT.

Timing reason codes belong to `timing_context`, not as an alternative escape hatch for the fundamental NewBuyer stance.

This is an axis-separation invariant, not a ticker-specific relaxation.

---

# 16. B2 v2 stance capability rules

Implement deterministic allowed-stance/reason capability before model output.

Order of precedence:

## A. Active material risk

Allowed:

`AVOID` only.

## B. Base/v2 business gate not eligible

Do not expose ATTRACTIVE.

Preserve the existing safe v1 envelope for non-positive business-gate subjects, except where a narrower typed v2 reason is required.

If failure is specifically caused by a current `BUSINESS_GATE_QUALITY` blocker, expose WAIT only with:

`BUSINESS_EVIDENCE_UNCERTAINTY`

and exact blocker refs.

Do not invent AVOID.

## C. Valuation ALL_RELEVANT_METRICS_UNUSABLE

Expose:

`WAIT`

with exact reason:

`VALUATION_UNRESOLVED`

Required evidence:

- composite all-metrics-unusable receipt;
- exact contributing typed blocker refs.

Legacy refs are not reason evidence.

## D. Valuation EVALUABLE + model valuation BURDENSOME

Expose:

`WAIT`

reason:

`VALUATION_BURDENSOME`

## E. Valuation EVALUABLE + model valuation NEUTRAL

Expose:

`WAIT`

reason:

`VALUATION_NEUTRAL`

## F. Valuation EVALUABLE + model valuation SUPPORTIVE

If the v2 business gate passes and active risk is absent:

`ATTRACTIVE`

is the fundamental/valuation NewBuyer stance.

This remains true for all backend-owned timing states:

```text
FAVORABLE_NOW
WAIT_FOR_ZONE
UNRESOLVED
```

Timing is carried independently:

- `FAVORABLE_NOW` → timing context says entry zone currently favorable;
- `WAIT_FOR_ZONE` → timing context says wait for the tactical zone;
- `UNRESOLVED` → timing context says entry timing unresolved.

Do not convert either of the latter two into a fundamental `WAIT`.

No legacy confidence veto may silently override this branch.

If a separately authorized typed `NEWBUYER_CONFIDENCE_VETO` exists, that is a distinct v2 veto path and must be explicit in the capability contract.

---

# 17. `CONFIDENCE_UNCERTAINTY` in v2

The v1 behavior:

```text
legacy confidence/quality ref exists
→ CONFIDENCE_UNCERTAINTY may be exposed
```

must not survive.

In v2, `CONFIDENCE_UNCERTAINTY` is allowed only if:

```text
NEWBUYER_CONFIDENCE_VETO typed current blocker refs nonempty
```

and the blocker-role policy explicitly authorizes that role.

Required:

```text
reason_evidence_refs = typed current blocker refs
```

Legacy refs may appear only in a separate context field.

If no typed blocker qualifies as `NEWBUYER_CONFIDENCE_VETO`, the branch must be absent from every frozen v2 request.

Do not keep the old branch merely for backward-looking symmetry.

---

# 18. 003690 safety requirement

REV56C proved:

```text
native PER independently qualified
CURRENT_FY1_FPER unavailable
no-estimate denial METRIC_SCOPED
blocks_other_valuation_metrics = false
blocks_newbuyer_global_resolution = false
```

REV56D must preserve this exactly.

Therefore:

- FY1 fPER must remain excluded from usable metrics;
- native PER must remain usable;
- `evaluability_state` must not become ALL_RELEVANT_METRICS_UNUSABLE solely because FY1 fPER is unavailable;
- no `VALUATION_GLOBAL` promotion;
- no ticker-specific ATTRACTIVE rule;
- no legacy confidence veto unless an independently qualifying typed current confidence blocker exists.

Do not predetermine the final model stance.

---

# 19. 010120 metric-scope diagnostic

Preserve the case where one metric may be denied while another qualified metric survives.

Required:

```text
one denied metric
+ one independently qualified relevant metric
→ EVALUABLE
```

No global unresolved.

No all-metrics-unusable composite.

---

# 20. Zero-qualified-metric diagnostics

Some frozen subjects have no surviving qualified relevant valuation metrics.

For each such subject, require a complete composition proof:

```text
relevant metric universe
all metric blockers/unavailability owners
usable metric refs = []
all_metrics_unusable_proof = true
```

Only then allow:

`VALUATION_UNRESOLVED`

Do not use:

- simple count=0;
- missing refs;
- legacy confidence;
- model abstention

as the proof.

Required artifact:

`all-metrics-unusable-proof.json`

---

# 21. Prompt contract

Create a v2 prompt that states only backend-proven semantics.

At minimum:

- use only provided qualified usable valuation facts;
- blocked/unavailable metrics must not be reconstructed;
- if valuation evaluability is EVALUABLE, choose exactly SUPPORTIVE / NEUTRAL / BURDENSOME;
- do not choose UNRESOLVED in EVALUABLE;
- absence of fair-value threshold is not unresolved;
- no target-price inference;
- no implied-EPS reverse calculation;
- no cross-security/ADR transfer;
- no invented currency/share conversion;
- legacy confidence/quality prose is not present in the model-visible B2 v2 input;
- current typed blocker refs cannot be ignored where the capability contract assigns them a role;
- active material risk remains AVOID;
- timing is backend-owned and independent from the fundamental/valuation NewBuyer stance;
- SUPPORTIVE valuation with eligible business/no active risk remains fundamental ATTRACTIVE even when timing is WAIT_FOR_ZONE or UNRESOLVED;
- do not invent numeric thresholds.

Do not mention desired blind labels.

---

# 22. v2 request schema

Create an exact provider-wire-valid v2 request contract.

At minimum include:

```text
contract_version
ticker
security_id
source_generation

business_gate
business_quality_blocker_refs

active_risk_refs

valuation_evaluability
valuation_metric_resolution_refs
qualified_usable_valuation_facts
valuation_metric_blocker_refs
all_metrics_unusable_proof_ref

timing_state
timing_refs

allowed_stances
allowed_wait_reasons

authority_digests
coverage_receipt_sha256
blocker_census_receipt_sha256
legacy_context_backend_audit_sha256
prompt_version
schema_version
```

`legacy_context_backend_audit_sha256` is an integrity pointer only. The referenced legacy prose/refs are not included in the provider/model-visible payload.

Keep unrelated historical/debug material out of the provider request.

---

# 23. v2 response schema and validator

The validator must enforce branch truth mechanically.

Required examples:

## ATTRACTIVE

Allowed only if:

```text
active_risk_refs empty
v2_business_gate_pass = true
valuation_evaluability = EVALUABLE
valuation_state = SUPPORTIVE
```

and no authorized current veto role blocks the branch.

`timing_state` is independently validated against the backend-owned timing receipt but is **not** an ATTRACTIVE gate.

The validator/presentation contract must preserve:

```text
new_buyer = ATTRACTIVE
timing_state = FAVORABLE_NOW | WAIT_FOR_ZONE | UNRESOLVED
```

as three valid combinations when all fundamental predicates are satisfied.

## AVOID

For this task, preserve active-material-risk AVOID semantics.

Do not invent valuation-only AVOID.

## WAIT / VALUATION_UNRESOLVED

Allowed only if:

```text
valuation_evaluability = ALL_RELEVANT_METRICS_UNUSABLE
all_metrics_unusable_proof = true
```

## WAIT / CONFIDENCE_UNCERTAINTY

Allowed only with typed `NEWBUYER_CONFIDENCE_VETO` refs.

## WAIT / BUSINESS_EVIDENCE_UNCERTAINTY

Allowed only with activated BUSINESS_GATE_QUALITY blocker refs.

## WAIT / valuation/timing reasons

Must exactly match the backend/model state they claim.

No free reason strings.

---

# 24. Provider-wire safety

Repeat the provider-wire scanner that protects against REV53-style schema failures.

Require:

```text
all const leaves typed
all object shapes closed where required
required fields consistent
enum branches typed
anyOf/oneOf branches provider-valid
no unsupported keyword drift
```

Every exact frozen v2 request must pass the scanner.

Required artifact:

`provider-wire-v2.json`

Failure:

`R2B_R9_REV56D_PROVIDER_WIRE_GAP`

---

# 25. Synthetic branch tests

Add deterministic tests at minimum for:

1. SUPPORTIVE + FAVORABLE_NOW + business pass + no risk → ATTRACTIVE.
2. SUPPORTIVE + WAIT_FOR_ZONE + business pass + no risk → ATTRACTIVE + independent WAIT_FOR_ZONE timing.
3. SUPPORTIVE + timing UNRESOLVED + business pass + no risk → ATTRACTIVE + independent timing UNRESOLVED.
4. NEUTRAL → WAIT valuation neutral.
5. BURDENSOME → WAIT valuation burdensome.
6. EVALUABLE + attempt valuation UNRESOLVED → reject.
7. all relevant metrics blocked with exact composite proof → WAIT valuation unresolved.
8. zero usable metrics without complete proof → reject request.
9. one metric blocked + one independently usable metric → EVALUABLE.
10. 003690 no-estimate fPER + usable native PER → EVALUABLE.
11. active risk + supportive valuation → AVOID-only.
12. legacy confidence refs nonempty + no current confidence veto → no CONFIDENCE_UNCERTAINTY branch.
13. legacy confidence/quality prose is absent from the provider/model-visible request.
14. typed current confidence-veto synthetic ref → CONFIDENCE_UNCERTAINTY allowed.
15. BUSINESS_GLOBAL quality denial with no exact linkage to gate-supporting Core refs → CONTEXT_ONLY / business gate unchanged.
16. BUSINESS_GLOBAL quality denial exactly invalidating required gate-supporting refs → exact business WAIT reason, not valuation unresolved.
17. metric blocker never becomes business blocker.
18. business blocker never becomes valuation fact.
19. legacy context never enters valuation evidence or model-visible valuation input.
20. qualified metric + same-metric typed denial without explicit precedence → INVALID_CONTRADICTORY_OWNERSHIP / reject.
21. cross-metric blocker propagation → reject.
22. ticker literal/static special-case scan.
23. malformed blocker role → reject.
24. coverage/census SHA mismatch → reject.

---

# 26. Frozen 22-subject offline v1/v2 replay

Run exact frozen inputs through:

```text
B2 v1
B2 v2 capability builder
```

No model.

Required artifact:

`replay-22.json`

For each ticker record:

```text
ticker

v1_request_sha256
v1_allowed_stances
v1_allowed_reasons

v2_business_gate
active_risk_refs

relevant_valuation_metric_refs
valuation_metric_resolution_refs
qualified_relevant_valuation_refs
blocked_metric_refs
usable_valuation_metric_refs
valuation_evaluability
all_metrics_unusable_proof_ref

business_blocker_refs
confidence_veto_refs

legacy_context_ref_count
legacy_v2_entitlement_summary
legacy_context_model_visible = false

timing_state
timing_reason

v2_allowed_fundamental_stances
v2_allowed_fundamental_wait_reasons

Core SHA
Pass A SHA
Overall SHA
Holder SHA
source/input SHA
```

Do not project a model-selected stance unless it is backend-deterministic.

Do not use an expected ATTRACTIVE ticker list.

---

# 27. Capability-delta audit

Create:

`v1-v2-capability-delta.json`

For each ticker list exact structural changes between v1 and v2.

Expected legitimate change classes include:

```text
FREE_VALUATION_UNRESOLVED_REMOVED
LEGACY_CONFIDENCE_VETO_REMOVED
LEGACY_CONTEXT_REMOVED_FROM_MODEL_INPUT
TYPED_BUSINESS_QUALITY_WAIT_ADDED
ALL_METRICS_UNUSABLE_PROOF_BOUND
METRIC_SCOPE_PRESERVED
TIMING_NO_LONGER_ERASES_FUNDAMENTAL_ATTRACTIVENESS
ATTRACTIVE_REACHABILITY_RESTORED
NO_CHANGE
```

Do not label a change "correct" based on blind-model agreement.

Every delta must cite a contract rule.

---

# 28. Legacy entitlement audit

After v2 mapping, require:

```text
95 / 95 historical claims byte-preserved
95 / 95 claim semantics not reclassified
```

Count:

```text
CONTEXT_ONLY_NO_VETO_ENTITLEMENT
CURRENT_TYPED_VETO_BOUND
```

Do not require any minimum count for either class.

No exact linkage → context only.

---

# 29. Authority freeze — 22/22

Require unchanged digests for:

```text
frozen source packets
source-use ownership
Core raw outputs
Core atomic claims
Core effects/materiality
Pass A
Overall
directional score
Holder
B2 v1 contract/output
valuation fact bytes
timing catalog
current price
active-risk refs
legacy Core claim bytes
REV56C owner coverage receipt
REV56C blocker census receipt
```

Allowed changes:

```text
B2 v2 code
B2 v2 policy
B2 v2 schema/validator/prompt
v2 entitlement sidecar
v2 metric-resolution/evaluability sidecars
v2 blocker-role/business-gate policy
v2 presentation-plan metadata
v2 offline replay
v2 frozen requests
```

Any authority leakage:

`R2B_R9_REV56D_AUTHORITY_LEAKAGE_GAP`

---

# 30. Feature isolation

B2 v2 must remain default OFF.

No production caller change.

No scheduler change.

No production DB schema migration.

No Telegram change.

No deploy.

If v2 requires persistence migration:

`R2B_R9_REV56D_PERSISTENCE_REVIEW_REQUIRED`

and stop.

---

# 31. Exact v2 request freeze

Only after all local implementation gates pass, freeze exact model requests for all 22 subjects.

Required artifact:

`v2-requests.json`

Per request record:

```text
ticker
request_sha256
input/source SHA
Core SHA
Pass A SHA
Overall SHA
Holder SHA

coverage receipt SHA
blocker census receipt SHA
legacy entitlement SHA
valuation evaluability SHA
blocker role policy SHA

schema SHA
prompt SHA
provider-wire validation PASS
```

Request bytes must be immutable after sealing.

No model execution.

---

# 32. Request-freeze receipt

Create:

`v2-freeze.json`

Include:

```text
subjects = 22
requests = 22
all_unique_request_sha256
schema_sha256
prompt_sha256
policy_sha256
coverage_receipt_sha256
blocker_census_receipt_sha256

model_calls = 0
sealed = true
```

Any later request change requires a new revision.

---

# 33. Freeze REV57 controller — do not execute

Create:

`rev57-controller.json`

Status:

`NOT_EXECUTED`

Suggested controller:

```text
task = exact frozen B2 v2 model reproof
model = gpt-5.6-sol
effort = xhigh

smoke = CORZ first
then remaining 21

timeout = 600 seconds
max retries = 2
physical attempt cap = 30

raw-first capture
seal outputs before blind comparison
no selective rerun after reveal
same exact frozen request bytes
```

Do not start it.

No model call in REV56D.

---

# 34. Validation sequence

Required order:

1. REV56C integrity;
2. repository identity;
3. protected-state snapshot;
4. coverage/census SHA proof;
5. blocker-role policy;
6. legacy v2 entitlement mapping;
7. valuation evaluability contract;
8. business-gate v2 layer;
9. stance capability policy;
10. prompt/schema/validator;
11. synthetic branch tests;
12. provider-wire scanner;
13. frozen 22 v1/v2 replay;
14. capability-delta audit;
15. active-risk 7/7 safety;
16. authority freeze 22/22;
17. default-OFF compatibility;
18. focused pytest;
19. Ruff;
20. `git diff --check`;
21. full pytest;
22. secret scan;
23. freeze 22 exact v2 requests;
24. freeze REV57 controller;
25. final local commit;
26. feature branch push only;
27. remote SHA readback;
28. Hosted feature CI PASS;
29. protected operating rehash;
30. final result sealing.

Do not call the model.

---

# 35. Network / execution policy

Hard zero:

```text
model calls = 0
source/provider calls = 0
source recollection = 0
message generation = 0
Telegram = 0
production DB/WAL writes = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating checkout mutation = 0
main merge = 0
main push = 0
```

Permitted network only:

- Git fetch for identity;
- feature branch push after local validation;
- Hosted feature CI.

Record every permitted network event.

---

# 36. Success criteria

REV56D succeeds only if all are proven:

```text
REV56C integrity PASS

exact coverage receipt verified
exact blocker census receipt verified

B2 v1 preserved
B2 v2 separately versioned
B2 v2 default OFF

blocker-role policy explicit
no census entry automatically activated by name alone

metric-scoped blockers affect only their metrics
business blockers remain business-axis
legacy context never becomes valuation evidence

legacy 95 claims byte-preserved
legacy claims no longer independently veto v2
unless exact current typed-veto linkage exists
legacy confidence/quality prose absent from model-visible B2 v2 input

per-metric usability resolved from complete category ownership
no qualified/denied contradiction or cross-metric blocker propagation

EVALUABLE:
UNRESOLVED structurally impossible

ALL_RELEVANT_METRICS_UNUSABLE:
requires complete composite typed proof

003690 native PER usable
003690 no-estimate FY1 fPER blocked only metric-scoped
no global valuation promotion

SUPPORTIVE + eligible business + no active risk:
fundamental NewBuyer ATTRACTIVE independent of timing state
timing remains separately backend-owned

active-risk safety = 7/7 AVOID-only

Core/A/Overall/Holder unchanged 22/22
source/valuation/timing authority unchanged

provider-wire PASS
synthetic tests PASS
frozen 22 replay PASS
authority freeze PASS
default-OFF compatibility PASS

focused pytest PASS
Ruff PASS
git diff --check PASS
full pytest PASS
secret scan PASS
Hosted feature CI PASS

22 exact v2 requests sealed
REV57 controller sealed NOT_EXECUTED

model/provider/source calls = 0

origin/main unchanged
protected operating checkout unchanged
```

Success terminal:

`R2B_R9_REV56D_B2_V2_OFFLINE_PASS_READY_FOR_REV57`

This terminal authorizes only a separate REV57 execution task.

It does not authorize automatic model execution or production activation.

---

# 37. Stop terminals

Use the narrowest truthful terminal:

```text
R2B_R9_REV56D_REPOSITORY_IDENTITY_GAP
R2B_R9_REV56D_REV56C_INTEGRITY_GAP
R2B_R9_REV56D_COVERAGE_RECEIPT_GAP
R2B_R9_REV56D_BLOCKER_ROLE_POLICY_GAP
R2B_R9_REV56D_LEGACY_ENTITLEMENT_GAP
R2B_R9_REV56D_VALUATION_EVALUABILITY_GAP
R2B_R9_REV56D_BUSINESS_GATE_POLICY_GAP
R2B_R9_REV56D_STANCE_CAPABILITY_GAP
R2B_R9_REV56D_PROVIDER_WIRE_GAP
R2B_R9_REV56D_ACTIVE_RISK_SAFETY_GAP
R2B_R9_REV56D_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV56D_B2_V1_COMPATIBILITY_GAP
R2B_R9_REV56D_TARGET_FITTING_GAP
R2B_R9_REV56D_PERSISTENCE_REVIEW_REQUIRED
R2B_R9_REV56D_FULL_VALIDATION_GAP
R2B_R9_REV56D_REQUEST_FREEZE_GAP
R2B_R9_REV56D_FEATURE_CI_GAP
R2B_R9_REV56D_PROTECTED_STATE_GAP
```

Do not convert an ambiguous policy mapping into PASS.

---

# 38. Required result bundle

Create:

`rev56d-result.zip`

and:

`rev56d-result.zip.sha256`

Include at minimum:

```text
REPORT.md
summary.json

rev56c-integrity.json
repository-identities.json
protected-before.json

coverage-receipt-proof.json
blocker-census-proof.json

blocker-role-policy.json
legacy-v2-entitlement.json
metric-resolution-v2.json
valuation-evaluability-v2.json
all-metrics-unusable-proof.json
business-gate-v2.json
axis-evidence-separation-v2.json
presentation-plan-v2.json

b2-v2-contract.json
b2-v2-schema.json
b2-v2-validator.json
b2-v2-prompt.txt
wait-reason-v2-contract.json

synthetic-v2-tests.json
provider-wire-v2.json
replay-22.json
v1-v2-capability-delta.json

active-risk-safety.json
authority-freeze-digests.json
b2-v1-compatibility.json
default-off-compatibility.json

focused-validation.json
full-validation.json
ruff-validation.json
diff-validation.json
secret-scan.json

v2-requests.json
v2-freeze.json
rev57-controller.json

feature-push-receipt.json
hosted-feature-ci.json
protected-state.json
final-repository-identities.json
bundle-manifest.json
```

No credentials.

If the task stops before request freeze, use explicit non-executable NOT_CREATED receipts.

---

# 39. Final report requirements

Final report must explicitly state:

```text
terminal

origin/main
REV56C parent HEAD
REV56D final feature HEAD
protected operating checkout

coverage receipt SHA
blocker census receipt SHA

blocker role counts:
METRIC_ELIGIBILITY_ONLY
BUSINESS_GATE_QUALITY
NEWBUYER_CONFIDENCE_VETO
GLOBAL_VALUATION_VETO
CONTEXT_ONLY

legacy v2 entitlement counts
legacy model-visible ref count (must be 0)

metric resolution counts:
USABLE
UNUSABLE_TYPED_DENIAL
NOT_RELEVANT
INVALID_CONTRADICTORY_OWNERSHIP

EVALUABLE subject count
ALL_RELEVANT_METRICS_UNUSABLE subject count
INVALID_INCOMPLETE_CONTRACT subject count

timing-independent ATTRACTIVE capability count
SUPPORTIVE capability rows by timing state

003690 valuation evaluability
003690 native PER preserved
003690 FY1 fPER blocked metric-scoped

active-risk 7/7

B2 v1 accepted outputs / branches
B2 v2 default OFF

frozen v2 requests count
model calls = 0

source/provider calls = 0
deploy = 0
operating mutation = 0
```

Do not report model behavior because no model was run.

---

# 40. What comes next

Do not execute automatically.

Only if REV56D succeeds:

**next = REV57 exact frozen B2 v2 model reproof**

REV57 will:

- use the exact 22 sealed request bytes;
- run CORZ smoke first;
- then the remaining 21;
- seal raw outputs before blind comparison;
- prohibit selective rerun after reveal.

After REV57:

1. evaluate the sealed v2 result independently;
2. fresh/current-data shadow validation as required;
3. one final fresh strict blind end-to-end test;
4. new-ticker registration/onboarding redesign;
5. add new monitored names.

Do not reorder this sequence.

---

# 41. Final principle

REV56C completed the ownership surface.

REV56D must convert that ownership into a decision contract without reintroducing the old ambiguity.

Correct direction:

```text
complete typed coverage
→ explicit blocker role

metric blocker
→ metric eligibility only

usable valuation exists
→ economic valuation judgment required

supportive valuation
+ eligible business
+ no active risk
→ fundamental ATTRACTIVE
  while timing remains a separate axis

all valuation metrics unusable
→ backend-composed typed unresolved proof

legacy confidence prose
→ context only unless exact typed current veto linkage exists

active material risk
→ AVOID

supportive valuation + favorable timing + eligible business gate
→ ATTRACTIVE structurally reachable
```

Never:

```text
legacy prose exists
→ WAIT

timing WAIT_FOR_ZONE / UNRESOLVED
→ erase a SUPPORTIVE fundamental stance

one metric unavailable
→ global unresolved

blocker census entry exists
→ automatic veto

zero valuation refs
→ free model abstention

blind result
→ policy tuning
```

The repair target is a fully typed, branch-valid B2 v2 contract — not a desired label distribution.
