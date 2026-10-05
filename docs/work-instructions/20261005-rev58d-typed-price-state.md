# Thesis Monitor — REV58D Typed Price-State + US Completed-Close Wiring Repair

**Revision note:** independently reviewed against the sealed REV58C stop result. The core repair direction is retained, with additional fail-closed boundaries for: (1) planner omission vs attempted-source failure vs provider semantic denial; (2) technical/chart-row denial isolation from authoritative completed-close ownership; (3) independent temporal/security qualification of provider-native CURRENT_PRICE_CONTEXT_ONLY metrics; (4) offline B2 v2 request-builder compatibility under typed price unavailability; and (5) KR8/global valid-price regression because the common valuation container is cross-market.

## 0. Task identity

Work instruction:

`rev58d-work.md`

Result:

`rev58d-result.zip`
`rev58d-result.zip.sha256`

This is a bounded **typed unavailable-current-price contract + US14 locked completed-close planner/consumer restoration + subject-local propagation repair** task.

It is NOT:

- a fresh provider/source run;
- a model run;
- a B2 v2 economic-policy redesign;
- a prompt/schema tuning task;
- a final blind task;
- a production deploy / DB / Telegram / scheduler task.

No external source/model call is allowed.

---

# 1. Authoritative predecessor

Immediate predecessor:

`rev58c-result.zip`

Expected SHA-256:

`6dbc628640308de146f53ceb9dd241e28ac202d82dff5360cc8245769f701ccd`

Expected terminal:

`R2B_R9_REV58C_UPSTREAM_PRICE_DEPENDENCY_GAP`

Expected parent / final HEAD:

`898e241ca2a2f2ab3d6034aca3f8aa23879e4b37`

Expected origin/main:

`9b134350cd05c127b6dc866d34a477d95c54785c`

Expected protected operating HEAD:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Expected REV58C facts:

```text
REV47 locked close lineage = PASS
US14 authority regression = CONFIRMED
REV58B usa20590 planned requests = 0/14
REV58B usa06012 current-price projection inputs = 14/14
TSM HIGH_LT_CLOSE preserved
REV58B generation requalified = false

future usa20590 plan restoration = NOT_IMPLEMENTED
current-price consumer restoration = NOT_IMPLEMENTED
typed price denial = NOT_IMPLEMENTED
cohort isolation = NOT_IMPLEMENTED

exact fresh upstream path:
prepare_fresh_subject
→ assemble_fresh_stock
→ derive_current_valuation
→ valuation_current_price_missing

CurrentValuationView.price requires positive float
CurrentMultiple.numerator requires positive float,
including provider-native CURRENT_PRICE_CONTEXT_ONLY metrics

Core/A/Overall business semantics do not intrinsically require numeric price
Holder / production-v1 Pass B require a typed price/timing state

source/provider calls = 0
model calls = 0
product code changes = 0
```

REV58C correctly stopped before partial implementation.

---

# 2. SoT reconciliation — mandatory

Before edits create:

`authority-reconciliation.json`

It must explicitly record:

## PRESERVE

```text
REV47:
usa20590
= COMPLETED_REGULAR_SESSION_CLOSE

usa06012
= CHART / HISTORY / TECHNICAL
!= completed-session current-price authority
```

Locked owner contract:

`kiwoom-us-completed-session-price-v2`

Locked exclusion:

`LATEST_USA06012_CUR_PRC_NOT_COMPLETED_SESSION_CLOSE_AUTHORITY`

## NEW FACT

```text
REV58B planner omitted usa20590 for all US14
REV58B current-price consumer used usa06012 adjusted_daily
REV58C proved common fresh-input contract cannot represent price unavailable
```

## ROOT CAUSE FOR REV58D

```text
source authority wiring regression
+
missing typed unavailable-price state at common fresh valuation/input boundary
+
cohort traversal raises instead of carrying subject-local denial
```

## CHANGE ALLOWED

Only:

```text
typed current-price availability/denial representation
planned-source failure vs provider semantic denial distinction
price-dependent vs price-independent valuation propagation
technical/chart target-row typed denial isolation
timing typed unavailability propagation
subject-local isolation
US14 mandatory usa20590 planner wiring
US current-price consumer usa20590-only wiring
offline fresh request-builder compatibility glue
valid-price cross-market compatibility glue
```

## CHANGE FORBIDDEN

```text
price fabrication/correction
usa06012 close-authority promotion
ticker exception
B2 v2 economic-policy change
Core/A/Overall economic-policy change
blind-label fitting
sealed REV58B generation retroactive PASS
```

Any conflict with these invariants:

`R2B_R9_REV58D_SOT_RECONCILIATION_GAP`

---

# 3. Verify REV58C immutable result

Before code edit verify:

- SHA sidecar;
- ZIP CRC;
- manifest 88 payload / no mismatch;
- exact REVISED REV58C instruction SHA;
- expected terminal;
- exact REV47 authority proof;
- exact common fresh-input dependency reproduction;
- source/model calls 0;
- protected state unchanged.

Required:

`rev58c-integrity.json`

Mismatch:

`R2B_R9_REV58D_REV58C_INTEGRITY_GAP`

---

# 4. Repository identity

Start from exact:

`898e241ca2a2f2ab3d6034aca3f8aa23879e4b37`

Suggested branch:

`codex/r2b-r9-rev58d-typed-price-state`

Before edits:

- exact parent proof;
- origin/main proof;
- clean worktree;
- protected operating snapshot;
- B2 v2 default-OFF proof.

No rebase.
No force push.
No protected checkout mutation.

---

# 5. Preserve existing valid-price V1 contracts

Do NOT silently weaken these existing models:

```text
current-price-context-v1
current-fresh-valuation-view-v1
CurrentMultiple valid-price semantics
```

For valid qualified current-price inputs, existing serialization and behavior must remain reproducible.

The unavailable-price path may use:

- a versioned companion contract;
- a discriminated union;
- or a new V2 internal view.

But do not redefine an old V1 PASS object to mean something different.

Required artifact:

`price-state-contract-versioning.json`

---

# 6. Typed current-price state

Introduce a deterministic current-price availability state that distinguishes **planner integrity**, **source acquisition**, and **provider/row semantics**.

Required states/categories include at least:

```text
AVAILABLE

PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED
UNAVAILABLE_SOURCE_ACQUISITION_FAILED

DENIED_TARGET_ROW_MISSING
DENIED_TARGET_ROW_INTEGRITY
DENIED_SECURITY_OR_SESSION_BINDING
```

`PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED` is an architecture/planner failure. It is **not** a valid runtime subject-local owner that can make a future generation "complete." A future source plan containing this state must fail before collection/model execution.

`UNAVAILABLE_SOURCE_ACQUISITION_FAILED` means the mandatory owner request was planned and attempted under the sealed transport contract but no usable provider response was acquired after the allowed transport/form retry policy. It proves only source unavailability at the recorded attempts; it does not claim the market price itself was absent.

`DENIED_*` states require a successfully acquired/bound response from which the exact semantic denial is owned.

For AVAILABLE require the existing exact qualified `usa20590` owner.

For unavailable/denied states require, as applicable:

```text
ticker
security_id
source_generation
target_session
required_owner_contract
required_source_role

planner_slot_ref
request/attempt refs
provider transport/result classification
raw SHA only if a raw response exists

decision_version
field_eligibility
observation/attempt time
temporal provenance
scope = SUBJECT_PRICE_CURRENT_SESSION
does_not_affect_other_subjects = true
reason code
```

Do not fabricate a raw hash when no response exists.

Do not convert:
- planner omission into a provider denial;
- transport failure into `TARGET_ROW_MISSING`;
- an HTTP/provider failure into a semantic row denial.

Required artifact:

`price-state-source-failure-semantics.json`

---

# 7. US14 future source planner restoration

Repair the future full-fresh planner so every US subject has one mandatory exact-session completed-close slot:

```text
api_id = usa20590
path = /api/us/mrkcond
body.stk_cd = exact ticker
body.stex_tp = exact exchange
body.base_dt = target_completed_session YYYYMMDD
role = COMPLETED_REGULAR_SESSION_CLOSE
owner = kiwoom-us-completed-session-price-v2
```

Require:

```text
US subjects = 14
mandatory usa20590 completed-close slots = 14
unique subject/security bindings = 14/14
exact target-session base_dt binding = 14/14
ticker exceptions = 0
duplicate completed-close owner slots = 0
usa06012 completed-close owner slots = 0
```

Do not remove usa06012 chart/history/technical reads.

Compile the **full future source-request DAG offline** and prove the `usa20590` slots participate in the same bounded call-plan / max-physical-request accounting used by fresh collection. The repair must not add an unbudgeted side-channel collector.

Required:

`future-us14-source-plan-proof.json`

No provider call.

---

# 8. US current-price consumer authority

Repair current-price consumption:

```text
qualified usa20590 owner
→ numeric current_price

typed usa20590 denial
→ typed current_price unavailable

usa06012
→ never current-price authority
```

No fallback from denied/missing usa20590 to usa06012.

Required:

`current-price-consumer-proof.json`

Static scan and tests must reject usa06012 as a completed-close owner.

---

# 9. Preserve TSM technical denial

The sealed REV58B TSM row remains:

```text
usa06012 technical/chart row
HIGH_LT_CLOSE
```

Requirements:

```text
raw corrected = false
integrity relaxed = false
completed-close use = false
technical denial preserved = true
```

Once usa20590 is restored, this technical denial must not itself deny authoritative completed current price.

Represent chart/technical availability separately from current-price availability. A versioned technical state may be introduced if the existing chart owner cannot carry this distinction.

For the exact future-equivalent synthetic case:

```text
usa20590 completed close = AVAILABLE
usa06012 target technical row = DENIED_TARGET_ROW_INTEGRITY
```

require:

```text
current_price = AVAILABLE
Core/A/Overall price-independent business input remains eligible
technical/timing consumer may become typed UNRESOLVED if it requires that row
subject does not abort
cohort does not abort
```

The invalid technical row may affect only consumers that actually require that exact row.

---

# 10. Common fresh valuation contract — unavailable-price path

Repair the current blocker reproduced by REV58C.

The common fresh valuation layer must represent:

```text
current-price AVAILABLE
or
current-price typed UNAVAILABLE
```

without throwing solely because a numeric price is absent.

Do not force a numeric placeholder.

The unavailable-price path must remain source/provenance bound.

Required artifact:

`fresh-valuation-price-state-contract.json`

---

# 11. Price-dependent vs price-independent valuation metrics

For every metric, explicitly classify current-price dependency.

At minimum distinguish:

## CURRENT_PRICE_ARITHMETIC_REQUIRED

A metric whose current value is computed from the current price.

If price is denied:

```text
metric = UNUSABLE_TYPED_DENIAL
exact price-denial ref required
```

## CURRENT_PRICE_CONTEXT_ONLY

Provider-native atomic metric that is independently source-owned and is not calculated from the local current price.

If current price is unavailable/denied:

- do not erase an otherwise qualified native snapshot solely because the shared container lacks a numeric numerator;
- do not invent a numerator;
- preserve exact native snapshot ownership;
- mark price-context state separately.

However, survival is allowed only when that native metric independently passes its **own**:

```text
security identity
field eligibility
source ownership
horizon/period ownership
temporal/currentness policy
source-quality policy
```

Price unavailability is neither qualification nor denial of an independently owned native ratio.

This is the specific REV58C `CurrentMultiple.numerator` blocker.

## PRICE_INDEPENDENT / NOT_RELEVANT

Preserve according to the existing metric contract.

Required:

`metric-price-dependency-contract.json`

No cross-metric denial propagation.

---

# 12. CurrentMultiple / valuation-view representation

If the existing `CurrentMultiple` and `CurrentValuationView` cannot represent the above without changing their old meaning, introduce a versioned internal contract.

Rules:

- old valid-price V1 path remains unchanged;
- a native provider snapshot may not be downgraded merely because a local context price is unavailable if its contract states `CURRENT_PRICE_CONTEXT_ONLY`;
- unavailable derived metric must carry typed denial, not fake numerator;
- qualified metric and blocked metric sets must remain disjoint;
- no same-metric qualified/denied contradiction without explicit precedence.

Do not alter the frozen B2 v2 provider request schema/prompt/policy.

Required invariant:

```text
current_price_state
technical_chart_state
valuation_metric_state
```

are separate typed domains. None may be inferred from another merely because they share a ticker/session.

---

# 13. Fresh stock / upstream input assembly

`assemble_fresh_stock` and `prepare_fresh_subject` must carry the typed price state forward instead of aborting the subject before Core/A/Overall input construction.

For:

```text
Core
Pass A
Overall
```

if their exact business evidence is price-independent, preserve execution eligibility without injecting price into business evidence.

For:

```text
Holder
production/v1 Pass B
```

supply the exact typed price/timing unavailable state required by their existing semantics.

Do not force WAIT/AVOID merely because price is absent.

Required:

`upstream-price-state-compatibility.json`

---

# 14. Offline B2 v2 request-builder compatibility under typed price state

Before declaring the common contract repaired, prove the existing B2 v2 fresh request builder can consume the new internal typed state **without changing the frozen provider request schema/prompt/policy**.

Required synthetic/offline cases:

### A. Price unavailable + independently qualified provider-native context-only metric

Expected:

```text
subject valuation evaluability = EVALUABLE
native metric remains usable
no fake price
no fake numerator
no price-required metric reconstructed
B2 v2 request builds successfully
provider-wire scanner PASS
pre-model/local request validator PASS
```

### B. Price unavailable + all relevant valuation metrics price-dependent

Expected only with complete typed proof:

```text
ALL_RELEVANT_METRICS_UNUSABLE
exact contributing denial refs
B2 v2 request builds successfully
```

### C. Planner gap

`PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED` must **not** be converted into a model-resolvable request. Stop before B2 request construction.

Required artifact:

`b2-v2-price-state-request-builder-proof.json`

No model call.

---

# 16. Timing propagation

If required price/technical evidence is unavailable, timing may become the exact existing:

```text
UNRESOLVED
```

or versioned equivalent.

Do not:

- substitute price;
- convert timing unavailable into fundamental WAIT;
- alter Core/Overall;
- create a fair-value inference.

Required:

`timing-price-state-proof.json`

---

# 16. Production/v1 comparator compatibility

REVISED REV58B requires fresh same-generation v1-v2 side-by-side impact audit.

Repair only input-state handling needed for a truthful v1 comparator.

If price is unavailable:

- use existing typed unresolved range/timing behavior where already supported;
- do not invent stance;
- do not change v1 economic thresholds/rules.

Require valid-price parity against V1.

Required:

`v1-price-state-compatibility.json`

---

# 17. Subject-local cohort isolation

Repair cohort traversal so one subject's authoritative price denial does not abort unrelated subjects.

Mandatory synthetic fixture:

```text
A = valid usa20590 price
B = typed authoritative-price denial
C = valid usa20590 price
```

Expected:

```text
A processed
B processed with typed denial
C processed
no market-wide exception solely because B denied
```

Also require a separate technical-denial isolation fixture:

```text
A = valid usa20590 + valid usa06012
B = valid usa20590 + invalid usa06012 target technical row
C = valid usa20590 + valid usa06012
```

Expected:

```text
A processed
B authoritative current price remains AVAILABLE
B technical/timing state carries the chart denial only where consumed
C processed
no subject/cohort abort from B's technical-row denial
```

Unknown/systemic implementation failures remain fail-stop.

Do not convert arbitrary exceptions into subject-local denials.

Required:

`cohort-isolation-proof.json`

---

# 18. Fresh coverage producer integration

Using REV58A's tracked fresh coverage composer, prove it can consume:

- qualified authoritative current-price owner;
- typed authoritative current-price denial;
- price-dependent metric denials;
- surviving independent native metrics.

Coverage completeness means every required cell has a typed disposition **after a valid required-source plan exists**.

It does NOT mean every value is available.

A planner architecture gap (`PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED`) is not a current data disposition and must not be used to claim coverage completeness.

A planned-but-unavailable source attempt may be represented only through its exact typed source-availability owner.

`PRODUCER_SEMANTICS` restrictions remain unchanged.

Required:

`fresh-coverage-price-state-integration.json`

---

# 19. Sealed REV58B generation remains diagnostic only

Run an offline diagnostic replay against the sealed REV58B generation.

Because it planned:

```text
usa20590 slots = 0/14
```

it must NOT become a valid fresh-generation PASS after this repair.

Require:

```text
rev58b_generation_requalified = false
US14 planned-authority gap preserved
13 passing usa06012 rows not promoted
TSM technical HIGH_LT_CLOSE preserved
```

You may demonstrate new typed diagnostic propagation, but never claim the generation had the missing mandatory source authority.

---

# 20. REV47 valid-authority regression

Replay preserved REV47 completed-close fixtures.

Require:

```text
14/14 usa20590 qualified valid-owner behavior unchanged
exact security/date/finality binding unchanged
regular-close price values unchanged
```

No regression from typed unavailable support.

Required:

`rev47-valid-close-regression.json`

---

# 21. B2 v2 frozen economic contract

Do not change:

- blocker-role policy;
- metric evaluability semantics;
- business gate;
- active risk;
- timing independence;
- fundamental stance capability;
- legacy visibility;
- prompt;
- provider request schema;
- provider response schema;
- validator;
- blind ontology.

Required digest drift:

`0`

If any frozen contract changes:

`R2B_R9_REV58D_B2_V2_FROZEN_CONTRACT_DRIFT`

---

# 22. B2 v1 / Core / A / Overall / Holder semantic preservation

For valid-price fixtures require exact output/semantic parity.

Allowed change is limited to faithful typed unavailable-price handling.

Because `CurrentValuationView` / `CurrentMultiple` are common cross-market containers, require explicit valid-price regression for **both** markets:

```text
US14 REV47 valid completed-close owner fixtures = unchanged
KR8 valid current-price / valuation fixtures = unchanged
KR current FY1 fPER price-arithmetic semantics = unchanged
003690 KIS no-estimate / native-PER separation = unchanged
```

Do not alter economic decision logic.

Required:

`authority-semantic-parity.json`

and:

`kr8-common-valuation-regression.json`

---

# 23. No external execution

Hard zero:

```text
source/provider calls = 0
source recollection = 0
Alpha Vantage calls = 0

upstream model calls = 0
B2 model calls = 0

production DB/WAL writes = 0
official monitored-record writes = 0
Telegram = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating mutation = 0
```

Use sealed historical evidence and synthetic fixtures only.

---

# 24. Mandatory tests

At minimum:

1. valid usa20590 owner → AVAILABLE unchanged;
2. required usa20590 planner slot absent → PLAN_GAP, not runtime/provider denial;
3. planned usa20590 transport/acquisition failure → typed SOURCE_ACQUISITION_FAILED, not TARGET_ROW_MISSING;
4. successful usa20590 response with target row missing → exact semantic denial;
5. usa20590 attempted malformed/invalid → exact typed denial;
6. usa06012 valid chart row cannot own current price;
7. TSM HIGH_LT_CLOSE remains technical denial;
8. valid usa20590 + invalid usa06012 → current price stays AVAILABLE; technical/timing denial remains scoped;
9. no usa06012 fallback;
10. derived price-required metric blocked when price unavailable;
11. provider-native context-only metric survives only if independently security/field/horizon/time/source qualified;
12. no fake numerator for context-only metric;
13. no cross-metric denial propagation;
14. price/context/chart domains remain separately typed;
15. Core/A/Overall business input can proceed when price unavailable if exact evidence is price-independent;
16. Holder/v1 receives typed price/timing state;
17. timing unresolved does not create fundamental WAIT;
18. authoritative-price A/B/C cohort isolation;
19. technical-row-denial A/B/C cohort isolation;
20. unknown exception still fail-stop;
21. future planner emits exactly 14 unique usa20590 slots under bounded source-plan accounting;
22. no ticker literals;
23. sealed REV58B generation not requalified;
24. REV47 valid-owner parity 14/14;
25. KR8 common valuation valid-price parity;
26. 003690 no-estimate/native-PER separation unchanged;
27. B2 v2 request builder: price unavailable + native context-only metric → EVALUABLE request PASS without fake price/numerator;
28. B2 v2 request builder: all price-dependent metrics denied → typed all-metrics-unusable request PASS only with complete proof;
29. planner gap cannot reach model request construction;
30. B2 v2 frozen digest drift 0.

---

# 25. Validation

Require:

```text
focused pytest PASS
Ruff PASS
git diff --check PASS
full pytest PASS
secret scan PASS
```

Do not weaken tests.

Preserve failed attempts and repair history.

---

# 26. Feature commit / Hosted CI

Only after all local gates pass:

- commit to REV58D feature branch;
- feature push only;
- remote SHA readback;
- Hosted feature CI PASS.

No main merge.
No main push.
No deploy.

---

# 27. Protected state

At end require:

```text
protected operating HEAD =
b610e6de0a8c33d199961e821ff1b130e1fa9ad4

production DB/WAL writes = 0
official monitored-record writes = 0
Telegram = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating mutation = 0
```

---

# 28. Success criteria

REV58D succeeds only if:

```text
REV58C integrity PASS
SoT reconciliation PASS

REV47 usa20590 authority preserved

future US14 plan:
usa20590 mandatory slots = 14/14
usa06012 completed-close slots = 0

US current-price consumer = usa20590 owner only

typed unavailable-price state implemented
planner gap / acquisition failure / semantic denial remain distinct
no numeric placeholder/fabrication

CurrentValuationView/common fresh input can carry unavailable price
without cohort-wide abort

technical/chart denial state remains separate from current-price state
valid authoritative price is not invalidated by usa06012 technical-row denial

price-required metrics get scoped typed denial
independent provider-native context-only metrics can remain qualified only under their own complete authority/currentness
no fake numerator
no cross-metric propagation

offline B2 v2 request-builder price-state integration PASS
planner gap never becomes model-resolvable input

Core/A/Overall valid business path not blocked solely by numeric-price absence
Holder/v1 typed price/timing state supported

subject-local cohort isolation PASS

sealed REV58B generation remains non-requalified
REV47 valid-price parity = 14/14
KR8 common valuation valid-price parity = 8/8
003690 no-estimate/native-PER separation unchanged

B2 v2 frozen economic contract drift = 0
valid-price authority semantic drift = 0

source/provider calls = 0
model calls = 0

focused/full tests PASS
Ruff PASS
diff PASS
secret scan PASS
feature push/readback PASS
Hosted CI PASS

protected production state unchanged
```

Success terminal:

`R2B_R9_REV58D_TYPED_PRICE_STATE_AND_US_CLOSE_AUTHORITY_PASS_READY_FOR_NEW_FRESH_SHADOW`

This authorizes only a **new full-fresh shadow generation**.

It does not authorize final strict blind.

---

# 29. Stop terminals

Use the narrowest truthful terminal:

```text
R2B_R9_REV58D_REV58C_INTEGRITY_GAP
R2B_R9_REV58D_REPOSITORY_IDENTITY_GAP
R2B_R9_REV58D_SOT_RECONCILIATION_GAP
R2B_R9_REV58D_PRICE_STATE_CONTRACT_GAP
R2B_R9_REV58D_SOURCE_FAILURE_SEMANTICS_GAP
R2B_R9_REV58D_US14_SOURCE_PLANNER_GAP
R2B_R9_REV58D_TECHNICAL_DENIAL_ISOLATION_GAP
R2B_R9_REV58D_CURRENT_PRICE_CONSUMER_GAP
R2B_R9_REV58D_METRIC_PRICE_DEPENDENCY_GAP
R2B_R9_REV58D_NATIVE_METRIC_PRESERVATION_GAP
R2B_R9_REV58D_UPSTREAM_PRICE_STATE_GAP
R2B_R9_REV58D_V1_PRICE_STATE_GAP
R2B_R9_REV58D_COHORT_ISOLATION_GAP
R2B_R9_REV58D_COVERAGE_INTEGRATION_GAP
R2B_R9_REV58D_B2_V2_REQUEST_BUILDER_GAP
R2B_R9_REV58D_KR_COMMON_VALUATION_REGRESSION_GAP
R2B_R9_REV58D_B2_V2_FROZEN_CONTRACT_DRIFT
R2B_R9_REV58D_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV58D_FULL_VALIDATION_GAP
R2B_R9_REV58D_FEATURE_CI_GAP
R2B_R9_REV58D_PROTECTED_STATE_GAP
```

Do not solve a contract gap by fabricating a price.

---

# 30. Required result bundle

Create:

`rev58d-result.zip`
`rev58d-result.zip.sha256`

Include at minimum:

```text
REPORT.md
summary.json

rev58c-integrity.json
authority-reconciliation.json
repository-identities.json
protected-before.json

price-state-contract-versioning.json
price-state-source-failure-semantics.json
future-us14-source-plan-proof.json
current-price-consumer-proof.json
usa06012-role-proof.json

fresh-valuation-price-state-contract.json
metric-price-dependency-contract.json
b2-v2-price-state-request-builder-proof.json
upstream-price-state-compatibility.json
timing-price-state-proof.json
v1-price-state-compatibility.json

cohort-isolation-proof.json
fresh-coverage-price-state-integration.json
rev58b-diagnostic-replay.json
rev47-valid-close-regression.json
kr8-common-valuation-regression.json

b2-v2-frozen-contract-proof.json
authority-semantic-parity.json
default-off-proof.json

focused-validation.json
full-validation.json
ruff-validation.json
diff-validation.json
secret-scan.json

network-events.json
feature-push-receipt.json
hosted-feature-ci.json

protected-state.json
final-repository-identities.json
bundle-manifest.json
```

No credentials.

---

# 31. What comes next

Do not execute automatically.

Only if terminal is:

`R2B_R9_REV58D_TYPED_PRICE_STATE_AND_US_CLOSE_AUTHORITY_PASS_READY_FOR_NEW_FRESH_SHADOW`

then create a new fresh/current-data shadow revision.

That next fresh run must:

- seal source/model execution plan before first provider call;
- seal exact/conditional source-request DAG before first provider call;
- include mandatory usa20590 slots for all US14;
- keep usa06012 technical/chart only;
- use a genuinely new generation;
- seal all source collection before owner coverage;
- prohibit adaptive recollection;
- distinguish planner omission, source acquisition failure, and provider semantic denial;
- use typed subject-local authoritative-price unavailability/denial if a planned usa20590 owner cannot produce a qualified close;
- keep technical/chart denial separately scoped even when authoritative price is available;
- regenerate fresh upstream authority stage-by-stage;
- perform same-generation fresh v1/v2 side-by-side impact audit;
- keep all production side effects zero.

Only after that fresh shadow PASS may final strict blind be created.

---

# 32. Final principle

The source-authority and contract boundaries are separate:

```text
usa20590
→ authoritative completed-session price

usa06012
→ chart/history/technical

required owner not planned
→ planner architecture failure, not a runtime data denial

planned owner acquisition fails
→ typed source-unavailability state

provider response acquired but semantic row invalid
→ typed semantic denial

authoritative price unavailable
→ typed subject-local state

technical/chart row invalid
→ technical/timing scope only unless another exact consumer requires it

typed state
→ scoped metric/timing effects

scoped denial
→ unrelated subjects continue
```

Never:

```text
usa06012 valid row
→ completed-close authority

missing price
→ fake numerator

one denied subject
→ cohort abort

provider-native atomic ratio
→ erased only because local price is absent

price unavailable
→ automatically qualify a provider-native metric without its own current authority

valid usa20590 close
+ invalid usa06012 technical row
→ deny the authoritative current price

repair PASS
→ reuse REV58B generation as fresh PASS
```

The target is truthful authority plus typed unavailable-state propagation with zero economic-policy change.
