# Thesis Monitor — REV56A NewBuyer Typed-Veto Ownership + B2 v2 Closure

**Revision note:** reviewed/amended after independent inspection of the REV56 result. The core task is unchanged; amendments tighten fail-closed blocker coverage, local-only parent identity, and valuation-axis evidence separation.

## 0. Task identity

Suggested work-instruction filename:

`20261004-r2b-r9-rev56a-newbuyer-typed-veto-ownership-b2-v2-closure.md`

Suggested result bundle:

`thesis-monitor-20261004-r2b-r9-rev56a-newbuyer-typed-veto-ownership-b2-v2-closure-report.zip`

This is a bounded **NewBuyer axis ownership repair + conditional B2 v2 implementation** task.

It is NOT:

- a fresh source recollection task;
- a model-behavior reproof;
- a Core / Pass A / Overall redesign;
- a Holder redesign;
- a valuation-threshold calibration task;
- a blind-label fitting task;
- a new-ticker onboarding task;
- a production deployment task;
- a scheduler / Telegram / production DB task.

The purpose is to close the exact design gap found by REV56 without interpreting legacy free-form confidence prose.

---

# 1. Authoritative prior result

The immediate predecessor is:

`thesis-monitor-20261004-r2b-r9-rev56-b2-abstention-confidence-repair-report.zip`

Expected SHA-256:

`b87f6136a40f5252fcaecdf4ca94c535f24728453449292857cc86c0dfd6763b`

Expected terminal:

`R2B_R9_REV56_CONFIDENCE_MATERIALITY_OWNERSHIP_GAP`

Expected REV56 facts:

```text
phase_a = PASS
phase_b = DESIGN_GAP / TYPED_OWNER_INSUFFICIENT
accepted_v1_outputs = 22
validated_v1_branches = 168
qualified_subjects_free_unresolved = 14
positive_subjects_free_unresolved = 9

confidence refs = 79
quality refs = 16
total legacy confidence/quality refs = 95
existing materiality = CONTEXT_ONLY for all 95
claim-local semantic_scope present = 0
claim-local uncertainty_reason present = 0

materiality assignments made by REV56 = 0
blocking_count = null
superseded_claims = 0

active-risk v1 safety = 7/7 AVOID-only
production code changes = 0
model calls = 0
provider calls = 0
source recollection = 0
message generation = 0
Telegram = 0
production DB writes = 0
scheduler mutation = 0
deploy = 0
restart = 0
main merge = 0
remote push = 0
```

REV56 also proved at least one typed-owner collision:
two distinct WULF confidence statements share the same currently available structural signature and parent source ownership.

Therefore:

**Do not solve REV56 by reading the prose and assigning BLOCKING / WEAKENING with regex, keywords, language heuristics, or ticker exceptions.**

---

# 2. Repository identities — keep the three states separate

Verified GitHub main:

`origin/main = 9b134350cd05c127b6dc866d34a477d95c54785c`

Production-code baseline inherited from REV54/REV55:

`45f4c53f6113575f91a067c423d471023cd4f560`

REV56 docs/audit branch:

`codex/r2b-r9-rev56-b2-abstention-confidence-repair`

REV56 final local HEAD:

`edeabb9d3c4d8c600519f7b4e0f3e119c5ed31d5`

REV56 instruction commit:

`b50e757e45d30b61708b0e1b21dabf6a2226eb90`

Protected operating checkout:

`/Users/sskim/Codex/thesis-monitor`

Protected operating HEAD:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Important interpretation:

- `edeabb9d...` is the latest REV56 local review HEAD.
- REV56 production-code changes were 0.
- The relevant production-code baseline therefore remains `45f4c53f...`.
- `origin/main`, development branch, and operating checkout are not interchangeable.

Preferred parent is the exact REV56 final **local-only** review HEAD:

`edeabb9d3c4d8c600519f7b4e0f3e119c5ed31d5`

Important: REV56 performed `remote_push = 0`. Do not assume `fetch origin` can recover this commit.

Before branching, prove locally:

```text
git cat-file -e edeabb9d3c4d8c600519f7b4e0f3e119c5ed31d5^{commit}
```

If the exact local commit is present, create the new branch from it:

`codex/r2b-r9-rev56a-newbuyer-typed-veto-ownership`

If the local REV56 commit is absent, **stop with repository identity gap**. Do not reconstruct it from prose, do not fabricate ancestry, and do not push a replacement commit merely to satisfy the expected SHA.

Before any code edit:

1. fetch origin;
2. prove `origin/main` exact SHA;
3. prove the local REV56 parent commit exists and is exact;
4. prove clean worktree;
5. prove relevant production files at REV56 HEAD are byte-identical to the `45f4c53f...` production-code baseline;
6. prove operating checkout HEAD separately and do not modify it.

Unexpected identity:

`R2B_R9_REV56A_REPOSITORY_IDENTITY_GAP`

No rebase.
No force push.

---

# 3. Verify REV56 immutable result first

Before design or code:

- verify sidecar SHA;
- ZIP CRC;
- manifest membership;
- per-member size;
- per-member SHA;
- no missing;
- no extras;
- confirm terminal and repository identities.

Required artifact:

`REV56-integrity.json`

Do not reinterpret REV56 as PASS.
Do not fabricate v2 readiness from placeholder `NON_EXECUTABLE_NOT_CREATED_NOTICE` files.

If integrity differs:

`R2B_R9_REV56A_REV56_INTEGRITY_GAP`

---

# 4. Preserve blind-review integrity

The prior blind files may be hash-verified only.

Expected preserved hashes:

```text
rev47-independent-blind-assessment.json
67799b0491541ea0b13cd7fc2b7d22dac4cfe936f4dff75cd25fbe75d483f877

rev47-blind-vs-monitoring-ai-comparison.md
66bd080b9bf96e282a4f7e23ef0350c1dba9423db8f50d72c26c204190c1b932
```

For this task:

- do not use blind BUY/WAIT/AVOID labels as design inputs;
- do not fit rules to the positive9;
- do not fit to 003690;
- do not inspect desired agreement counts to decide code behavior;
- do not rerun any model.

The frozen 22 cohort is a contract regression set, not a target-label training set.

Target fitting terminal:

`R2B_R9_REV56A_TARGET_FITTING_GAP`

---

# 5. Core design principle for REV56A

REV56 proved that the legacy Core confidence/quality claim text does not contain enough **typed claim-local ownership** to safely classify each statement as BLOCKING / WEAKENING / INFORMATIONAL / SUPERSEDED.

Do not force that classification.

Instead separate two concepts:

## A. Historical/context claim

Existing Core confidence/quality claim:

```text
effect = CONFIDENCE_ONLY or DATA_QUALITY_ONLY
materiality = CONTEXT_ONLY
```

This claim remains preserved exactly.

It may remain useful for:

- explanation;
- uncertainty wording;
- human review;
- historical audit;
- Holder/Core context where already allowed.

But the claim does not automatically own a NewBuyer veto.

## B. Current NewBuyer veto entitlement

A NewBuyer WAIT veto must be owned by a separate, backend-generated, typed current blocker.

Introduce an axis-specific contract, suggested:

`newbuyer-current-veto-ownership-v1`

The key rule is:

```text
legacy confidence/quality prose
alone
!= current NewBuyer blocker
```

A legacy claim may be associated with a current blocker for audit, but the **blocker ref** owns the veto.

Do not claim the old prose is semantically resolved unless same-scope proof exists.

This is an admissibility rule, not a rewrite of Core history.

---

# 6. Do not mislabel legacy claims

REV56A must NOT manufacture:

```text
legacy claim -> WEAKENING
legacy claim -> INFORMATIONAL
legacy claim -> SUPERSEDED
```

when claim-local typed semantics do not prove those labels.

Instead, for NewBuyer veto purposes, give every legacy confidence/quality ref an explicit axis-specific status such as:

```text
CONTEXT_ONLY_NO_VETO_ENTITLEMENT
```

or:

```text
CURRENT_BACKEND_BLOCKER_BOUND
```

These statuses mean only:

- whether that legacy ref itself can veto NewBuyer;
- whether an exact current backend blocker exists and is linked for audit.

They do **not** assert that the prose itself is weak, informative, or resolved.

Required artifact:

`legacy-confidence-veto-entitlement-audit.json`

For each of the 95 refs record:

```text
ticker
claim_ref
effect
existing_materiality
parent_source_refs
historical_claim_preserved
newbuyer_veto_entitlement
linked_backend_blocker_refs
linkage_basis
blocker_coverage_complete
claim_semantics_reclassified = false
blind_label_used = false
```

Fail-closed sequencing is mandatory.

**Before backend blocker coverage is proven complete**, the default must be:

```text
newbuyer_veto_entitlement = UNRESOLVED_PENDING_BACKEND_COVERAGE
```

Absence of a typed blocker at this stage is **not** proof that the claim has no NewBuyer veto entitlement.

Only after Sections 7–9 prove backend blocker coverage complete may each legacy ref become one of:

```text
CONTEXT_ONLY_NO_VETO_ENTITLEMENT
CURRENT_BACKEND_BLOCKER_BOUND
```

`CONTEXT_ONLY_NO_VETO_ENTITLEMENT` means only that veto authority is not owned by that legacy prose ref under the completed backend contract. It does not mean the prose is false, weak, informational, or superseded.

---

# 7. Backend blocker ownership must be source/contract-derived

Create a separate typed blocker catalog.

Suggested contract:

`newbuyer-current-decision-blocker-v1`

The blocker generator must use only structured fields / typed source contracts / exact security ownership.

No natural-language claim interpretation.

Candidate classes may include only mechanically provable current states such as:

```text
NO_USABLE_VALUATION_FACTS
SECURITY_IDENTITY_DENIED
CROSS_SECURITY_OR_ADR_BASIS_DENIED
VALUATION_SECURITY_BASIS_DENIED
VALUATION_CURRENCY_BASIS_DENIED
HORIZON_OR_PERIOD_IDENTITY_DENIED
SOURCE_QUALITY_DENIED
CURRENT_TYPED_DATA_CONTRADICTION
CURRENT_BUSINESS_EVIDENCE_DENIED
```

Use a narrower set if the repository can prove fewer classes.

Do not create a class merely because it sounds useful.

Every emitted blocker must contain:

```text
blocker_ref
blocker_class
ticker
security_id
current_generation
source_owner_contract
source_owner_ref
affected_axis = NEWBUYER
affected_metric_refs
scope
status
reason_code
input_sha256
```

A blocker without exact typed provenance is invalid.

Also require a task-level coverage receipt:

`blocker-coverage-completeness.json`

It must state whether the structured backend owners are sufficient to cover **every current NewBuyer veto category the architecture intends to enforce** for this frozen cohort.

Critical rule:

```text
no emitted blocker
!=
proof of no blocker
```

until:

```text
blocker_coverage_complete = true
```

Do not enable v2 or strip legacy veto entitlement while blocker coverage remains incomplete.

Each blocker should additionally declare:

```text
scope_level = SECURITY_GLOBAL | VALUATION_GLOBAL | METRIC_SCOPED | BUSINESS_GLOBAL
applies_to_metric_refs
coverage_owner_contract
```

so a metric-scoped denial cannot silently become a global veto.

---

# 8. Metric-scoped denial is not automatically a global valuation blocker

Important.

If one valuation metric is denied but another relevant valuation metric remains qualified and usable, do not expose generic `UNRESOLVED` merely because one field failed.

Compute:

```text
qualified_relevant_valuation_refs
denied_relevant_valuation_refs
global_valuation_blocker_refs
```

For a positive-capability subject:

```text
qualified_relevant_valuation_refs nonempty
AND business gate PASS
AND active risk empty
```

the economic valuation judgment remains possible.

Therefore the model must choose:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

unless an exact global blocker proves that all otherwise relevant valuation interpretation is invalid.

A missing universal fair-value threshold is never a blocker.

A lack of absolute fair-value range is never a blocker.

Model discomfort is never a blocker.

---

# 9. Formal audit of existing CONTEXT_ONLY semantics

Before implementation, prove how the existing contracts use:

```text
CONFIDENCE_ONLY
DATA_QUALITY_ONLY
CONTEXT_ONLY
ACTIVE_MATERIAL_RISK
PERSISTENT_OR_IMPAIRED
```

Required artifact:

`context-only-veto-semantics-audit.json`

The audit must answer:

1. Does current Core policy already prohibit non-directional `CONTEXT_ONLY` claims from owning adverse material risk?
2. Are active material business risks separately typed and already mapped to the 7 AVOID controls?
3. Are valuation eligibility/denial states available independently of model-authored confidence prose?
4. Are source-quality denials available from typed quality contracts independently of legacy claim text?
5. Can a current NewBuyer blocker be generated from those typed owners without interpreting claim prose?
6. Would removing free confidence-prose veto change Core/A/Overall/Holder? It must not.
7. Does any **currently reachable v1 NewBuyer veto path** depend on a legacy free-form confidence/quality ref for which no structured current owner can be proven?
8. Can every intended v2 veto category be represented by an existing or newly derived backend-owned typed contract without interpreting claim prose?

These questions must be answered from execution/schema/dataflow ownership, not by deciding whether the prose “sounds material.”

Hard gate:

If question 7 is YES, question 8 is NO, or blocker coverage completeness cannot be proven, do not implement v2.
Stop with:

`R2B_R9_REV56A_BACKEND_BLOCKER_COVERAGE_GAP`

and record the exact missing owner contract/category.

This prevents both:
- “ignore uncertainty to get more ATTRACTIVE”; and
- “absence of typed ownership means no risk.”

---

# 10. Supersession policy after REV56

Do not claim broad old-claim supersession merely because an atomic PER/PBR/fPER is now qualified.

REV56 already proved claim-local scope is absent.

For REV56A:

- preserve old Core claims;
- do not delete or rewrite them;
- do not mark whole claims `SUPERSEDED` unless exact same-scope proof exists;
- do not require supersession merely to remove veto power.

The NewBuyer rule should instead be:

```text
historical/context claim remains visible
+
current veto entitlement comes only from current typed blocker
```

If exact same-scope supersession is provable for a subset, record it as an audit fact, but it is not required to fabricate whole-claim resolution.

Required artifact:

`newbuyer-supersession-and-admissibility.json`

Allowed states may include:

```text
HISTORICAL_CONTEXT_PRESERVED
SAME_SCOPE_SUPERSEDED
CURRENT_BLOCKER_BOUND
NO_VETO_ENTITLEMENT
```

Never infer same-scope from shared ticker or shared parent domain alone.

---

# 11. B2 v2 implementation gate

Only if Sections 7–10 close without prose interpretation may production code changes begin.

If they close, implement a new default-OFF v2 contract.

Suggested version:

`newbuyer-qualified-valuation-context-v2`

Preserve v1 bytes and behavior for historical reproducibility.

Do not silently mutate:

`newbuyer-qualified-valuation-context-v1`

Suggested implementation isolation:

```text
scripts/newbuyer_b2_v2_blockers.py
scripts/newbuyer_b2_v2_contract.py
scripts/newbuyer_b2_v2_shadow.py
```

Names may differ, but v1 must remain separately reproducible.

---

# 12. v2 valuation-state rule

For positive-capability / no-active-risk subjects:

## Case A — at least one qualified relevant valuation fact

Expose only:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

Do not expose generic `UNRESOLVED`.

The model is judging contextual valuation, not proving fair value.

## Case B — no usable qualified relevant valuation fact

Expose:

```text
UNRESOLVED
```

only if exact backend blocker refs are nonempty.

Required:

```text
valuation_resolution_blocker_refs >= 1
```

The refs must be backend-owned typed blocker refs.

Do not use legacy maturity confidence refs as valuation-resolution blockers.

---

# 13. v2 confidence-veto rule

The v1 rule:

```text
any confidence/quality ref
-> CONFIDENCE_UNCERTAINTY WAIT may be exposed
```

must not survive in v2.

In v2:

`CONFIDENCE_UNCERTAINTY` may be exposed only when an exact current backend blocker with the correct axis/scope exists.

Required:

```text
current_newbuyer_blocker_refs nonempty
```

The WAIT `reason_evidence_refs` must point to the typed blocker refs or exact typed owner refs, not merely to free-form Core confidence prose.

Legacy confidence refs may remain separately attached as context.

The v2 request/schema must keep two distinct collections:

```text
legacy_context_refs
current_newbuyer_blocker_refs
```

They are not interchangeable.

For `CONFIDENCE_UNCERTAINTY`:
- `reason_evidence_refs` may cite only typed blocker refs / their exact structured owner refs;
- legacy context refs alone may not satisfy the reason predicate.

If there is no typed blocker **after blocker coverage is proven complete**:

```text
CONFIDENCE_UNCERTAINTY
```

must not be an allowed WAIT reason.

---

# 14. Existing active-risk precedence is frozen

Exact cohort:

```text
CORZ
CPNG
HUT
RXRX
TSLA
WULF
047810
```

Required deterministic result:

`7/7 AVOID-only`

No v2 logic may:

- expose ATTRACTIVE;
- convert active risk into mere confidence;
- let low valuation compensate active material risk;
- suppress active-risk refs;
- change Core/A/Overall/Holder to achieve NewBuyer differentiation.

Failure:

`R2B_R9_REV56A_ACTIVE_RISK_SAFETY_GAP`

---

# 15. Business gate remains unchanged

Preserve B2 business gate semantics:

```text
Overall == BUY
AND current Core positive refs nonempty
AND current Core negative refs empty
AND active material business-risk refs empty
```

Do not inject valuation into this gate.

Do not alter Overall to increase positive capability.

Do not alter Core confidence claims to increase positive capability.

---

# 16. Timing remains a separate backend-owned axis

Keep existing timing states unchanged:

```text
FAVORABLE_NOW
WAIT_FOR_ZONE
UNRESOLVED
```

Do not redesign timing in REV56A.

Timing-specific WAIT reasons remain tied to exact timing predicates.

Do not use confidence uncertainty as a surrogate timing reason.

Do not turn tactical watch zones into fair value.

---

# 17. Required v2 WAIT truth binding

At minimum:

## `VALUATION_UNRESOLVED`

Allowed only if:

```text
valuation_state = UNRESOLVED
AND valuation_resolution_blocker_refs nonempty
AND qualified_relevant_valuation_refs empty
```

unless an explicit global blocker invalidates every otherwise-qualified relevant metric, which must be separately proven.

## `CONFIDENCE_UNCERTAINTY`

Allowed only if:

```text
current_newbuyer_blocker_refs nonempty
```

and those refs are typed backend blockers.

## `VALUATION_NEUTRAL`

Allowed only if:

```text
valuation_state = NEUTRAL
```

## `VALUATION_BURDENSOME`

Allowed only if:

```text
valuation_state = BURDENSOME
```

Existing timing WAIT reasons remain exact-state-bound.

No free WAIT reason.

---

# 18. 003690 / 012450 / GOOGL are diagnostics only

Use these only to prove predicates.

Do not use them as desired labels.

## 003690

Frozen REV55 observed:

```text
valuation = SUPPORTIVE
timing = FAVORABLE_NOW
stance = WAIT
reason = CONFIDENCE_UNCERTAINTY
```

REV56A question:

> Does any exact current backend blocker independently justify the confidence veto?

Do not answer from the old prose.

If no typed blocker exists, v2 must not expose `CONFIDENCE_UNCERTAINTY` for this input.

This does not authorize a ticker-specific ATTRACTIVE rule.

## 012450

Audit independently:

```text
free UNRESOLVED
confidence veto
```

If qualified relevant valuation facts exist, generic UNRESOLVED must disappear unless an exact global blocker exists.

## GOOGL

Do not force SUPPORTIVE.

A model-judged NEUTRAL valuation may legitimately remain WAIT.

The task is to remove unowned vetoes, not to maximize positive labels.

---

# 19. Synthetic tests — mandatory

If v2 implementation gate passes, add deterministic tests including:

### Legacy confidence prose cannot veto by itself

Input:

```text
legacy confidence refs nonempty
typed backend blocker refs empty
```

Expected:

```text
CONFIDENCE_UNCERTAINTY branch absent
```

### Legacy DATA_QUALITY_ONLY prose cannot veto by itself

Same expected result.

### Exact backend blocker can veto

Input:

```text
typed current blocker ref present
```

Expected:

`CONFIDENCE_UNCERTAINTY` or narrower typed WAIT branch allowed exactly as contract defines.

### Qualified valuation + no global blocker

Expected valuation states:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

`UNRESOLVED` absent.

### No usable valuation + exact blocker

Expected:

`UNRESOLVED` allowed.

### No usable valuation + no blocker

Reject as invalid/incomplete backend state.
Do not allow free model abstention.

### One metric denied, another metric qualified

Do not expose global unresolved solely because one metric is denied.

### SUPPORTIVE + no blocker

ATTRACTIVE capability must be structurally reachable under the existing B2 business gate.

### SUPPORTIVE + active risk

ATTRACTIVE absent; AVOID preserved.

### NEUTRAL

WAIT only for valuation stance, independent of legacy confidence prose.

### BURDENSOME

WAIT only for valuation stance, independent of legacy confidence prose.

### Blocker coverage incomplete

Input / audit state:

```text
blocker_coverage_complete = false
```

Expected:

```text
v2 implementation/enablement gate = DENY
legacy no-veto entitlement must not be inferred
```

### Confidence laundering into valuation state

Input contains legacy confidence/context refs but no extra valuation facts.

Expected:
- legacy refs cannot appear in `valuation_evidence_refs`;
- legacy refs cannot by themselves justify SUPPORTIVE / NEUTRAL / BURDENSOME;
- valuation-state evidence remains valuation-domain owned.

### No ticker-specific logic

Static scan / test must reject ticker literals in decision rules.

---

# 20. Frozen REV55 all-22 offline replay

Run exact frozen REV55 inputs through:

```text
B2 v1 capability
B2 v2 capability
```

No model calls.

For every ticker record:

```text
ticker
v1 request SHA
v1 allowed stances / reasons
v2 allowed stances / reasons
business gate
active risk refs
qualified valuation refs
denied valuation refs
global valuation blocker refs
current NewBuyer blocker refs
legacy confidence refs
legacy quality refs
legacy veto entitlement status
timing state
Core/A/Overall/Holder digests
source/input digest
```

Do not project a model stance unless contract-deterministic.

Do not include “expected ATTRACTIVE ticker list” as a success criterion.

Required artifact:

`rev55-22-v1-v2-offline-replay.json`

---

# 21. Authority freeze — 22/22

Require byte/digest preservation for:

```text
source inputs
source-use ownership
Core raw output
Core atomic claims
Core effects
Core capability
Pass A
Overall
directional score
Holder
valuation fact bytes
timing catalog
current price
```

Allowed differences only:

```text
NewBuyer v2 blocker sidecar
NewBuyer v2 schema
NewBuyer v2 validator
NewBuyer v2 prompt/contract
v2 shadow request bytes
```

Required:

`22/22 PASS`

Failure:

`R2B_R9_REV56A_AUTHORITY_LEAKAGE_GAP`

---

# 22. Provider-wire safety

Because REV53 failed on provider-wire schema typing, repeat the provider-wire scanner for every v2 request schema.

Require:

```text
const leaves typed
closed object shapes
required fields consistent
anyOf branches provider-valid
no unsupported JSON Schema keyword drift
```

Run local valid branch probes.

If v2 request freeze is created, every frozen request must pass the same scanner before sealing.

Failure:

`R2B_R9_REV56A_PROVIDER_WIRE_REGRESSION_GAP`

---

# 23. Prompt contract

If v2 is implemented, prompt must say only what the backend contract supports.

At minimum:

- valuation facts provided are qualified relevant context;
- when at least one usable qualified valuation fact exists and no global blocker exists, choose SUPPORTIVE / NEUTRAL / BURDENSOME;
- do not choose UNRESOLVED merely because no universal threshold or fair-value range exists;
- legacy confidence/context claims do not independently own a NewBuyer veto;
- current typed blocker refs, if present, cannot be ignored;
- SUPPORTIVE / NEUTRAL / BURDENSOME are valuation-axis judgments and must be grounded in qualified valuation refs / allowed valuation relations;
- legacy confidence/context refs cannot be used as `valuation_evidence_refs` or as the sole evidence for a valuation-state choice;
- business refs may establish the frozen business gate/context but must not be laundered into valuation evidence;
- active material risk remains AVOID;
- timing is separately backend-owned;
- do not infer fair value;
- do not infer target price;
- do not derive implied EPS from price/forwardPE;
- do not cross ADR/home-security valuation basis;
- do not invent numeric thresholds.

Do not mention desired blind labels.

---

# 24. Feature isolation

B2 v2 must be default OFF.

Production path remains v1 / existing behavior unless explicitly enabled in shadow invocation.

No DB migration.

No production persistence mutation.

No scheduler dependency.

If a migration becomes necessary:

`R2B_R9_REV56A_PERSISTENCE_REVIEW_REQUIRED`

and stop.

---

# 25. No external/model execution

Hard zero for REV56A:

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

Network access should be blocked during offline proof except the separately authorized Git fetch / feature push / hosted CI phases if implementation reaches those phases.

Record network events explicitly.

Alpha Vantage calls:

`0`

Do not use AV as fallback.

---

# 26. Validation sequence

If design gate fails before implementation:

- stop;
- do not fake v2 artifacts;
- mark not-created artifacts as non-executable notices;
- full pytest is not required if production code changes = 0;
- Hosted CI is not required.

If implementation occurs:

1. REV56 integrity;
2. context-only veto semantics audit;
3. backend blocker coverage audit;
4. legacy veto entitlement audit;
5. supersession/admissibility audit;
6. synthetic v2 tests;
7. all-22 offline v1/v2 replay;
8. active-risk 7/7;
9. authority freeze 22/22;
10. provider-wire scanner/probes;
11. feature-OFF compatibility;
12. focused pytest;
13. Ruff;
14. `git diff --check`;
15. full pytest;
16. secret scan;
17. commit;
18. feature branch push only;
19. remote SHA readback;
20. Hosted feature CI PASS.

Do not use historical Hosted CI as the REV56A CI result.

---

# 27. New v2 request freeze

Only after all local implementation validation passes:

create exact frozen B2 v2 requests for the same 22 frozen subjects.

Required artifact:

`rev56a-b2-v2-shadow-requests.json`

Per ticker record:

```text
ticker
v1 request SHA
v2 request SHA
source/input SHA unchanged
Core SHA unchanged
Pass A SHA unchanged
Overall SHA unchanged
Holder SHA unchanged
valuation facts SHA unchanged
timing SHA unchanged
blocker sidecar SHA
legacy veto-entitlement SHA
schema SHA
prompt SHA
```

Do not execute the requests.

---

# 28. Freeze the next model controller, do not run it

Only after REV56A success, freeze the not-executed next controller.

Suggested next task identity:

`REV57 — exact frozen B2 v2 model reproof`

Controller parameters:

```text
model = gpt-5.6-sol
effort = xhigh
CORZ smoke first
then remaining 21
timeout = 600 seconds
max retries = 2
physical attempt cap = 30
raw-first capture
seal outputs before any blind comparison
no selective rerun after reveal
```

Required artifact:

`rev57-controller-freeze.json`

Status must be:

`NOT_EXECUTED`

No model call in REV56A.

---

# 29. Success criteria

Use success only if all are proven:

```text
REV56 integrity PASS

legacy Core confidence/quality prose is preserved
legacy prose is not semantically reclassified without owner
legacy prose alone has no NewBuyer veto entitlement

every actual NewBuyer veto exposed by v2 has a backend-owned typed current blocker

blocker_coverage_complete = true
and absence of an emitted blocker is interpreted as no current blocker only after this proof

qualified relevant valuation facts cannot coexist with free generic UNRESOLVED
unless an exact global blocker invalidates all usable interpretation

CONFIDENCE_UNCERTAINTY cannot be exposed from legacy confidence refs alone

active-risk safety = 7/7 AVOID-only

Core/A/Overall/Holder unchanged 22/22

B2 v1 preserved
B2 v2 default OFF

provider-wire scanner PASS
focused tests PASS
full pytest PASS
Ruff PASS
git diff --check PASS
secret scan PASS
Hosted feature CI PASS

model/provider/source calls = 0

v2 requests sealed but not executed
REV57 controller sealed but not executed

origin/main unchanged
operating checkout unchanged
```

Success terminal:

`R2B_R9_REV56A_TYPED_VETO_OWNERSHIP_B2_V2_PASS_READY_FOR_MODEL_REPROOF`

---

# 30. Stop terminals

Use the narrowest truthful terminal:

```text
R2B_R9_REV56A_REPOSITORY_IDENTITY_GAP
R2B_R9_REV56A_REV56_INTEGRITY_GAP
R2B_R9_REV56A_CONTEXT_ONLY_SEMANTIC_GAP
R2B_R9_REV56A_BACKEND_BLOCKER_COVERAGE_GAP
R2B_R9_REV56A_SUPERSESSION_SCOPE_GAP
R2B_R9_REV56A_TARGET_FITTING_GAP
R2B_R9_REV56A_ACTIVE_RISK_SAFETY_GAP
R2B_R9_REV56A_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV56A_PROVIDER_WIRE_REGRESSION_GAP
R2B_R9_REV56A_PERSISTENCE_REVIEW_REQUIRED
R2B_R9_REV56A_FULL_VALIDATION_GAP
R2B_R9_REV56A_FEATURE_CI_GAP
R2B_R9_REV56A_FREEZE_GAP
```

Do not convert an ownership gap into a PASS by inventing missing semantics.

---

# 31. Required result bundle

Create:

`thesis-monitor-20261004-r2b-r9-rev56a-newbuyer-typed-veto-ownership-b2-v2-closure-report.zip`

plus:

`.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV56-integrity.json
repository-identities.json
context-only-veto-semantics-audit.json
legacy-confidence-veto-entitlement-audit.json
newbuyer-current-decision-blocker-contract.json
newbuyer-blocker-coverage-matrix.json
blocker-coverage-completeness.json
axis-evidence-separation.json
newbuyer-supersession-and-admissibility.json
b2-v1-preservation.json
b2-v2-contract.json
b2-v2-schema.json
b2-v2-validator.json
wait-reason-v2-contract.json
synthetic-v2-tests.json
rev55-22-v1-v2-offline-replay.json
negative-control-safety.json
authority-freeze-digests.json
provider-wire-regression.json
feature-off-compatibility.json
focused-validation.json
full-validation.json
secret-scan.json
rev56a-b2-v2-shadow-requests.json
rev56a-request-freeze-receipt.json
rev57-controller-freeze.json
feature-push-receipt.json
hosted-feature-ci.json
protected-before.json
protected-state.json
bundle-manifest.json
```

If implementation gate stops early, not-created implementation artifacts may be present only as explicit non-executable notices.

No credentials.

Manifest self may be excluded, but state that explicitly.

---

# 32. Final report must explicitly distinguish four repository identities

The final report must state:

```text
origin/main
production-code baseline inherited from 45f4c53f...
REV56A feature HEAD
protected operating checkout HEAD
```

Do not call a feature push a deployment.

Do not call main green state the operating state.

---

# 33. What comes after REV56A

Do not execute automatically.

If REV56A succeeds:

**next = REV57 frozen B2 v2 model reproof**

Only after frozen B2 v2 behavior is genuinely acceptable:

1. fresh shadow/current-data validation;
2. one final fresh strict blind end-to-end test;
3. only then redesign new-ticker registration/onboarding;
4. then add new monitored names.

Do not reorder this sequence.

---

# 34. Final principle

REV56 showed that this is unsafe:

```text
free-form confidence sentence
→ infer severity from prose
→ allow or deny NewBuyer stance
```

REV56A should replace it with:

```text
historical Core confidence/quality prose = preserved context

NewBuyer veto entitlement
= backend-owned typed current blocker only

qualified valuation exists
→ model must make an economic valuation judgment
unless exact typed global blocker proves it cannot

active material risk
→ still AVOID

no threshold fitting
no ticker exception
no blind-label fitting
no historical claim rewrite
```

The repair target is **ownership**, not a desired ATTRACTIVE count.
