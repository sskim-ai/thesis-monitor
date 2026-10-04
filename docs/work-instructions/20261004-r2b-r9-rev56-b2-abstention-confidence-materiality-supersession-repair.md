# Thesis Monitor — R2B-R9-REV56
## B2 Abstention + Confidence Materiality / Supersession Repair
### Close the behavioral WAIT blocker proven by REV55
### Offline audit first, then default-OFF v2 shadow implementation only if gates prove the repair
### No model calls / no source calls / no production enablement / no main merge

---

# 0. Why REV56 exists

REV55 finally reached the actual B2 model behavior.

REV55 terminal:

`R2B_R9_REV55_B2_MODEL_STILL_WAIT_BIASED`

The model proof was technically clean:

```text
CORZ smoke = PASS
22/22 logical requests dispatched
22/22 accepted
22 physical attempts
0 retries
7/7 active-risk controls = AVOID
0 unsupported refs
0 cross-security refs
0 fair-value / target / implied-EPS fabrication
```

But the positive-capability cohort was:

```text
ATTRACTIVE = 0/9
WAIT = 9/9
```

Therefore the structural reachability repair from REV52 was insufficient behaviorally.

REV55 observed among the 9 positive-capability subjects:

```text
valuation state:
  UNRESOLVED = 7
  NEUTRAL = 1
  SUPPORTIVE = 1

WAIT reason:
  VALUATION_UNRESOLVED = 6
  CONFIDENCE_UNCERTAINTY = 3
```

Most importantly:

```text
003690:
  valuation = SUPPORTIVE
  timing = FAVORABLE_NOW
  NewBuyer = WAIT
  reason = CONFIDENCE_UNCERTAINTY
```

So the remaining blocker is not merely timing.

REV56 must determine and repair, offline:

1. whether `UNRESOLVED` remains an overly permissive abstention branch even when relevant qualified valuation exists;
2. whether `CONFIDENCE_UNCERTAINTY` can be driven by stale, superseded, or merely weakening claims;
3. whether current downstream security/valuation qualification must supersede older valuation-basis uncertainty **for NewBuyer only**;
4. which confidence conditions are actually material enough to veto a positive NewBuyer stance.

No ticker target fitting is allowed.

---

# 1. Exact repository state

Expected green main:

`9b134350cd05c127b6dc866d34a477d95c54785c`

REV54 feature branch:

`codex/r2b-r9-rev54-provider-wire-const-typing`

Expected feature SHA:

`45f4c53f6113575f91a067c423d471023cd4f560`

REV55 made no code changes.

Create REV56 from exact REV54 feature SHA.

Suggested branch:

`codex/r2b-r9-rev56-b2-abstention-confidence-repair`

Do not base on operating checkout.

Protected operating checkout remains:

```text
/Users/sskim/Codex/thesis-monitor
HEAD = b610e6de0a8c33d199961e821ff1b130e1fa9ad4
```

At start:
- fetch origin;
- prove expected remote refs;
- prove clean worktree.

Unexpected identity:

`R2B_R9_REV56_REPOSITORY_IDENTITY_GAP`

No rebase.
No force push.

---

# 2. Verify REV55 immutable result

Result:

`thesis-monitor-20261004-r2b-r9-rev55-b2-frozen-model-reproof-report.zip`

Expected SHA-256:

`a0f88c4a9108da54bf23cda7736c1840778455000ba85e028c55c5783fc70e93`

Expected ZIP integrity:

```text
members = 246
manifest payload entries = 245
manifest self excluded = true
CRC = PASS
missing = 0
hash mismatch = 0
size mismatch = 0
extra = 0
```

Expected terminal:

`R2B_R9_REV55_B2_MODEL_STILL_WAIT_BIASED`

Expected execution:

```text
requested = 22
accepted = 22
physical attempts = 22
retries = 0
CORZ smoke = PASS
active-risk safety = 7/7
positive-capability ATTRACTIVE = 0/9
ready_for_fresh_shadow = false
```

Do not rerun REV55.

---

# 3. Blind comparison remains comparator-only

Preserve the pre-sealed blind evidence but do not use its desired labels to construct rules.

Expected independent blind assessment:

`67799b0491541ea0b13cd7fc2b7d22dac4cfe936f4dff75cd25fbe75d483f877`

Expected comparison:

`66bd080b9bf96e282a4f7e23ef0350c1dba9423db8f50d72c26c204190c1b932`

Forbidden:

```text
if ticker == ...
make the 7 blind BUY controls ATTRACTIVE
fit a multiple threshold to blind labels
weaken active-risk safety to improve agreement
```

The repair is contract-derived, not answer-key-derived.

---

# 4. Phase A must be completed before code edits

Before editing production code, create an offline audit over the exact REV55 22 requests and accepted outputs.

Required artifact:

`rev55-abstention-confidence-root-cause-audit.json`

For every subject record:

```text
ticker
B2 positive capability
qualified relevant valuation refs available
valuation state selected
valuation refs selected
NewBuyer stance
WAIT reason
confidence refs available
confidence refs selected
quality refs available
condition refs available
active risk refs
timing state
```

No implementation change until this matrix is sealed.

---

# 5. Audit A — UNRESOLVED reachability

Trace the exact B2 v1 schema/validator rule for:

```text
valuation_context.state = UNRESOLVED
authority = NOT_RESOLVED
reason = JUDGMENT_NOT_RESOLVED
```

Answer mechanically:

1. Can UNRESOLVED be chosen when qualified relevant valuation refs are nonempty?
2. Does UNRESOLVED require any blocker ref?
3. Can it return empty valuation/business refs?
4. Does validator distinguish:
   - facts unavailable;
   - facts available but model abstains;
   - facts present but unusable due to exact basis/identity blocker?

REV55 already indicates qualified valuation can coexist with UNRESOLVED.

Do not treat the observation as sufficient; prove the exact code path.

---

# 6. Proposed v2 valuation-resolution rule

If Phase A confirms free abstention, implement a versioned v2 shadow contract:

`newbuyer-qualified-valuation-context-v2`

Do not mutate archived v1 semantics.

For positive-capability subjects:

```text
qualified relevant valuation refs nonempty
AND business gate PASS
AND active risk empty
```

then the model must choose one economic state:

```text
SUPPORTIVE
NEUTRAL
BURDENSOME
```

**unless** there is an exact backend-owned:

`valuation_resolution_blocker`

that makes economic interpretation genuinely unresolved.

`UNRESOLVED` is not a generic conservative fallback.

---

# 7. Typed valuation-resolution blockers

Create a backend-owned typed blocker set.

Candidate blocker classes may include only exact current states such as:

```text
SECURITY_IDENTITY_UNRESOLVED
VALUATION_BASIS_UNRESOLVED
CURRENCY_BASIS_UNRESOLVED
METRIC_NOT_RELEVANT_TO_ARCHETYPE
ONLY_UNQUALIFIED_METRICS
HORIZON_OR_PERIOD_IDENTITY_UNRESOLVED
SOURCE_QUALITY_DENIAL
```

Do not include:

```text
VALUATION_SEEMS_HARD
MODEL_NOT_CONFIDENT
NO_ABSOLUTE_FAIR_VALUE_RANGE
NO_UNIVERSAL_PE_THRESHOLD
```

Those do not make a model-judged contextual valuation impossible.

If no typed blocker exists:
UNRESOLVED branch must not be exposed.

---

# 8. Current downstream authority may supersede old uncertainty — scope-limited

REV55 frozen Core capability contains older neutral claims such as:

```text
Security identity remains unresolved
security and valuation basis remains unresolved
주당 지표와 통화 등 가치평가 기준이 확인되지 않음
증권 정체성이 확인되지 않음
```

while the downstream REV47/REV45+ valuation facts may now contain exact:
- security identity qualification;
- valuation metric qualification;
- current security binding;
- explicit FY1 horizon ownership.

REV56 must audit this systematically.

Do not edit or delete old Core claims.

Instead introduce a NewBuyer-only supersession layer:

`newbuyer_current_authority_supersession_v1`

It may mark an older uncertainty claim:

`SUPERSEDED_FOR_NEWBUYER_CONTEXT`

only when a later/current exact owner proves the **same semantic subject** resolved.

Required proof tuple:

```text
old claim semantic scope
old source generation / claim ref
current owner semantic scope
same security
current owner status
current owner ref
supersession reason
```

No textual keyword-only suppression.

---

# 9. Supersession must not rewrite history

A superseded claim remains valid historical evidence about the earlier stage.

Required distinction:

```text
Core historical claim = preserved
Core/Overall decision = unchanged
Holder = unchanged

NewBuyer admissibility of that uncertainty claim
= filtered by current downstream authority
```

This repair must not retroactively change Core/A/Overall.

---

# 10. Audit B — confidence materiality

Current capability includes many `confidence` refs.

REV55 shows `CONFIDENCE_UNCERTAINTY` can veto positive output.

Create a typed NewBuyer-only materiality classification:

```text
BLOCKING
WEAKENING
INFORMATIONAL
SUPERSEDED
```

Every admissible confidence ref must map to exactly one state.

Do not let the model invent materiality.

---

# 11. BLOCKING definition

`BLOCKING` means the current evidence defect prevents a sound NewBuyer economic stance.

Examples that may qualify when exact/current:

```text
current security identity unresolved
current valuation basis unresolved
current valuation source denied
current business evidence quality denied
material accounting/source integrity issue
exact current critical data contradiction
```

Only BLOCKING refs may enable:

`CONFIDENCE_UNCERTAINTY -> WAIT`

on an otherwise positive B2 path.

---

# 12. WEAKENING definition

`WEAKENING` means confidence should be lower but the judgment is still possible.

Examples to test:

```text
single-quarter recurrence not established
durable trend not yet established
one-year vs one-year comparison caveat
ordinary persistence uncertainty
non-directional caution that does not invalidate the evidence
```

WEAKENING refs:
- remain visible;
- may affect confidence/wording later;
- must **not alone** enable `CONFIDENCE_UNCERTAINTY` WAIT.

Do not automatically classify from English/Korean text alone.
Use claim provenance / reason role / logical-condition severity / existing typed owner where possible.

If type ownership is insufficient:
stop with a design gap rather than NLP keyword rules.

---

# 13. INFORMATIONAL definition

Information that is relevant but neither blocks nor weakens the NewBuyer decision materially.

It cannot enable WAIT.

---

# 14. SUPERSEDED definition

An older uncertainty claim becomes `SUPERSEDED` for B2 only when an exact later owner resolves its semantic issue.

It:
- remains auditable;
- is not passed to model as a current confidence blocker;
- cannot be used in reason_evidence_refs for `CONFIDENCE_UNCERTAINTY`.

---

# 15. Exact REV55 confidence audit

For the positive-capability cohort:

```text
GOOGL
MU
SNDK
000660
003690
005490
005930
010120
012450
```

produce per-ref classification.

Specially inspect:
- persistence/recurrence caveats;
- security identity uncertainty;
- valuation basis uncertainty;
- source-quality cautions;
- current data-quality denials.

No desired stance is assumed.

---

# 16. 003690 is a diagnostic, not a target

REV55 observed:

```text
valuation = SUPPORTIVE
timing = FAVORABLE_NOW
stance = WAIT
reason = CONFIDENCE_UNCERTAINTY
```

The selected confidence refs included:
- one-period persistence caveats;
- older security/basis uncertainty claims.

REV56 must answer:

> Under current exact downstream authority, which of those refs are still current BLOCKING evidence?

Do not assert the answer in advance.

If zero remain BLOCKING:
the v2 validator/schema must not permit `CONFIDENCE_UNCERTAINTY` for that exact frozen input.

This is a contract consequence, not a forced ATTRACTIVE label.

---

# 17. 012450 diagnostic

REV55 observed:

```text
timing = FAVORABLE_NOW
valuation = UNRESOLVED
stance = WAIT
reason = CONFIDENCE_UNCERTAINTY
```

Audit both independently:

1. Was UNRESOLVED justified by a current valuation-resolution blocker?
2. Were any selected confidence refs current BLOCKING refs?

Do not let one uncertainty category stand in for the other.

---

# 18. GOOGL diagnostic

REV55 observed:

```text
valuation = NEUTRAL
stance = WAIT
reason = CONFIDENCE_UNCERTAINTY
```

Audit whether its selected confidence refs are:
- current blockers;
- persistence WEAKENING;
- stale/superseded identity/basis claims;
- technical data quality irrelevant to fundamental valuation.

Do not force SUPPORTIVE.

A v2 result may still be WAIT if a real blocker exists or valuation is NEUTRAL under the selected stance policy.

---

# 19. Active-risk path is frozen

Exact active-risk cohort:

```text
CORZ
CPNG
HUT
RXRX
TSLA
WULF
047810
```

No v2 abstention/confidence repair may:
- expose ATTRACTIVE for these;
- suppress AVOID;
- let low valuation compensate active business risk.

Required deterministic regression:

`7/7 AVOID-only`

---

# 20. v2 positive stance mapping

For positive-capability / no-risk subjects, v2 should distinguish economic valuation from blocker state.

Minimum candidate mapping:

```text
valuation SUPPORTIVE
AND no current BLOCKING confidence refs
→ ATTRACTIVE capability

valuation NEUTRAL
→ WAIT capability

valuation BURDENSOME
→ WAIT capability

valuation UNRESOLVED
→ WAIT only when exact valuation_resolution_blocker exists
```

Timing remains separately backend-owned.

Do not invent universal valuation thresholds.

---

# 21. Timing must not be conflated with confidence

Keep:

```text
FAVORABLE_NOW
WAIT_FOR_ZONE
UNRESOLVED
```

unchanged from REV52/55.

REV56 does not redesign timing.

A timing reason may only be used through the existing timing predicates.

`CONFIDENCE_UNCERTAINTY` may not be used as a surrogate for timing uncertainty.

---

# 22. WAIT reason v2 truth binding

Implement only if Phase A/B evidence supports the design.

## VALUATION_UNRESOLVED

Allowed only when:
- valuation state UNRESOLVED;
- exact valuation_resolution_blocker nonempty.

## CONFIDENCE_UNCERTAINTY

Allowed only when:
- current, unsuperseded `BLOCKING` confidence refs nonempty.

## VALUATION_NEUTRAL

Allowed only when valuation state NEUTRAL.

## VALUATION_BURDENSOME

Allowed only when valuation state BURDENSOME.

Existing timing-specific reasons remain tied to exact timing states.

No free WAIT reason.

---

# 23. Prompt contract v2

If v2 is implemented, prompt must say:

- UNRESOLVED requires backend-supplied exact blocker refs;
- do not abstain merely because no universal multiple threshold exists;
- SUPPORTIVE/NEUTRAL/BURDENSOME remain model judgments;
- WEAKENING confidence refs lower certainty but do not by themselves veto a stance;
- SUPERSEDED refs are not current blockers;
- BLOCKING refs are backend-owned and cannot be ignored;
- active risk remains AVOID;
- no target/fair-value/implied-EPS inference;
- no numeric threshold invention.

---

# 24. No model call in REV56

REV56 is offline only.

Hard zero:

```text
model calls = 0
source/provider calls = 0
source recollection = 0
message generation = 0
Telegram = 0
DB writes = 0
scheduler mutation = 0
deploy = 0
restart = 0
main merge = 0
main push = 0
```

Do not reuse revealed blind labels in any model prompt because there are no model calls.

---

# 25. Synthetic v2 validator tests

Required.

## UNRESOLVED with qualified refs but no blocker
Reject.

## UNRESOLVED with exact current blocker
Accept.

## CONFIDENCE_UNCERTAINTY with WEAKENING only
Reject.

## CONFIDENCE_UNCERTAINTY with SUPERSEDED only
Reject.

## CONFIDENCE_UNCERTAINTY with exact BLOCKING ref
Accept.

## SUPPORTIVE + no blocker
ATTRACTIVE branch available.

## SUPPORTIVE + active risk
ATTRACTIVE unavailable; AVOID preserved.

## NEUTRAL + no blocker
WAIT only.

## BURDENSOME + no blocker
WAIT only.

---

# 26. Frozen REV55 22-subject offline replay

Run exact frozen inputs through:

```text
B2 v1 capability
B2 v2 capability
```

No model.

For each ticker record:

```text
v1 allowed branches
v2 allowed branches
qualified valuation refs
valuation-resolution blockers
confidence refs:
  BLOCKING
  WEAKENING
  INFORMATIONAL
  SUPERSEDED
timing
active risk
```

Do not generate projected model stances unless deterministically fixed by the contract.

---

# 27. Mandatory anti-target-fitting controls

The v2 contract must be tested across all 22.

Specifically ensure:
- 005490 and 010120 are not automatically forced positive;
- CRCL/IBM do not become positive merely because valuation can resolve;
- active-risk 7 remain protected;
- US/KR logic is common except source-specific provenance;
- no branch rule mentions ticker.

If a general rule only works by special-casing blind controls:

`R2B_R9_REV56_TARGET_FITTING_GAP`

---

# 28. Authority-freeze proof

Require 22/22 unchanged:

```text
source inputs
Core claims
Core capability
Pass A
Overall
directional score
Holder
valuation fact bytes
timing catalog
current price
```

Only B2 v2 NewBuyer context/schema/validator may differ.

---

# 29. Feature isolation

B2 v1 remains preserved for historical reproducibility.

B2 v2 must be behind a new/default-OFF shadow version.

Do not silently change the already-proven v1 contract bytes.

Suggested version:

`newbuyer-qualified-valuation-context-v2`

Feature default remains OFF.

No DB migration.

If persistence migration appears necessary:

`R2B_R9_REV56_PERSISTENCE_REVIEW_REQUIRED`

---

# 30. Validation

Run:

1. REV55 root-cause offline audit;
2. supersession tests;
3. confidence-materiality tests;
4. valuation-resolution-blocker tests;
5. v2 schema/validator tests;
6. all-22 frozen replay;
7. active-risk negative controls;
8. authority-freeze digest test;
9. provider-wire projection/scanner tests;
10. feature-OFF compatibility;
11. no-network guard;
12. Ruff;
13. `git diff --check`;
14. full pytest;
15. secret scan.

Full pytest mandatory if production code changes.

---

# 31. New v2 request freeze

If implementation and all tests PASS:

create exact frozen v2 requests for the same 22 subjects.

Do not execute them.

Create:

`rev56-b2-v2-shadow-requests.json`

and record per ticker:

```text
v1 request SHA
v2 request SHA
source/input SHA unchanged
Core/A/Overall/Holder unchanged
valuation fact SHA unchanged
timing SHA unchanged
prompt/schema differences explained
```

Freeze a not-executed REV57 controller:

```text
model = gpt-5.6-sol
effort = xhigh
CORZ smoke first
then remaining21
600s
2 retries
physical cap30
raw-first
pre-reveal seal
```

---

# 32. Commit / feature CI

If implementation occurs and local validation PASS:

- commit bounded v2 repair;
- secret scan;
- push feature branch only;
- exact remote SHA readback;
- Hosted feature CI must complete successfully.

No main merge.

---

# 33. Success terminal

Use only if root cause, contract repair, offline replay and validation all PASS:

`R2B_R9_REV56_B2_ABSTENTION_CONFIDENCE_REPAIR_PASS_READY_FOR_V2_MODEL_REPROOF`

Required final facts:

```text
free UNRESOLVED abstention removed or bounded by exact blockers
confidence WAIT requires current BLOCKING evidence
stale same-scope uncertainty can be superseded only with exact proof
WEAKENING refs cannot independently veto positive stance
active-risk safety = 7/7
B2 v1 preserved
B2 v2 default OFF
authority freeze = 22/22
full pytest PASS
Hosted feature CI PASS
model calls = 0
new v2 request freeze sealed
main unchanged
```

---

# 34. Stop terminals

Use the narrowest truthful state:

```text
R2B_R9_REV56_REPOSITORY_IDENTITY_GAP
R2B_R9_REV56_REV55_INTEGRITY_GAP
R2B_R9_REV56_ABSTENTION_ROOT_CAUSE_GAP
R2B_R9_REV56_SUPERSESSION_AUTHORITY_GAP
R2B_R9_REV56_CONFIDENCE_MATERIALITY_OWNERSHIP_GAP
R2B_R9_REV56_VALUATION_BLOCKER_CONTRACT_GAP
R2B_R9_REV56_TARGET_FITTING_GAP
R2B_R9_REV56_ACTIVE_RISK_SAFETY_GAP
R2B_R9_REV56_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV56_PROVIDER_WIRE_REGRESSION_GAP
R2B_R9_REV56_PERSISTENCE_REVIEW_REQUIRED
R2B_R9_REV56_FULL_VALIDATION_GAP
R2B_R9_REV56_FEATURE_CI_GAP
R2B_R9_REV56_FREEZE_GAP
```

---

# 35. Result bundle

Create:

`thesis-monitor-20261004-r2b-r9-rev56-b2-abstention-confidence-repair-report.zip`

+ `.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV55-integrity.json
repository-identities.json
rev55-abstention-confidence-root-cause-audit.json
valuation-unresolved-reachability.json
confidence-ref-inventory.json
confidence-materiality-contract.json
authority-supersession-contract.json
superseded-claim-audit.json
valuation-resolution-blocker-contract.json
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
full-validation.json
secret-scan.json
rev56-b2-v2-shadow-requests.json
rev56-request-freeze-receipt.json
rev57-controller-freeze.json
feature-push-receipt.json
hosted-feature-ci.json
protected-state.json
bundle-manifest.json
```

No credentials.

---

# 36. Next task after PASS

Do not execute automatically.

Next task:

> REV57 — exact frozen B2 v2 model reproof.

It will:
- CORZ smoke;
- then remaining21;
- seal before blind comparison;
- require active-risk7 safety;
- evaluate whether positive-capability behavior is now differentiated;
- prohibit rerunning based on revealed labels.

No fresh source proof until v2 frozen model behavior passes.

---

# 37. Final principle

REV55 proved the remaining problem is behavioral, but the behavior is enabled by contract choices:

```text
qualified valuation exists
→ model may freely abstain UNRESOLVED

and

any allowed confidence ref
→ may justify CONFIDENCE_UNCERTAINTY WAIT
```

REV56 must replace that with:

```text
UNRESOLVED requires an exact current blocker

confidence veto requires exact current BLOCKING materiality

stale same-scope uncertainty may be superseded only by stronger current authority

ordinary persistence caution remains visible but cannot silently become a veto
```

without:
- inventing valuation thresholds;
- fitting blind labels;
- weakening active-risk protection;
- rewriting Core history.
