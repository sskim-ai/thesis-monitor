# thesis-monitor — Price Structure v3 Major Structural S/R Reality Gate Repair
## Prevent Bollinger-only / untraded derived levels from being labeled as "주요 구조 지지/저항"
## Shared semantic repair across US + KR; no ticker-specific exceptions
## Replay US current monitored universe + KR 7 controls before operating promotion

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `PRICE_STRUCTURE_MAJOR_SR_REALITY_GATE_REPAIR`
- Task class: `SHARED_SEMANTIC_SELECTOR_REPAIR + CROSS_MARKET_REPLAY + TEST_SINK + DEPLOY`
- Scope:
  - user-facing `MAJOR_SUPPORT`
  - user-facing `MAJOR_RESISTANCE`
  - labels rendered as `주요 구조 지지/저항`
- Explicit non-scope:
  - ordinary near support/resistance policy unless regression is found
  - wave/Fib family-consensus redesign
  - stored monitoring price rules
  - target/stop logic
  - US market digest
  - KR market digest
- Production Assist: preserve `OFF`
- Manual production scheduler: `0`
- Production-recipient test send: `0`
- DB / official assessment mutation: `0`

### Latest source-supported operating lineage

From the supplied current-time E2E bundle:

```text
BASE entering prior work =
a3050b19e3b983fe71ae3f68f400fc2e9a8d66aa

prior implementation =
f6bc769f823429426474a38f007dc8196b4e5f43

prior report / final main / operating =
c5d26d475d62b2f9d804a16ea5d68c88e09e633b
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve latest safe `origin/main`
4. resolve actual operating SHA
5. use `c5d26d...` or a safe linear descendant
6. record exact lineage

---

# 1. Defect summary

The current Price Structure selector can promote a derived volatility-band level to:

```text
MAJOR_SUPPORT
MAJOR_RESISTANCE
ACTIVE_STRUCTURAL
```

even when the source has no historical price reaction/anchor.

That makes a mathematically derived level look like a price level the market actually traded against.

The user-visible label:

```text
주요 구조 저항
```

must mean structural price history, not merely a remote indicator band.

---

# 2. Source-supported GOOGL negative control

Current E2E evidence for GOOGL:

```text
current price / Price Structure basis = $341.16
target session = 2026-08-27
security basis = US_LISTED:GOOGL
price basis = provider_adjusted_price_v1 / adjusted-close context
```

Selected major support:

```text
$267.08~$268.43

semantic_type = MAJOR_SUPPORT
source_families = [BOLLINGER_MONTHLY]
source_timeframe = monthly
reaction_count = 0
structural_score = 31
active_relevance = ACTIVE_STRUCTURAL
last_meaningful_interaction = 2026-08-03
```

Selected major resistance:

```text
$424.82~$426.96

semantic_type = MAJOR_RESISTANCE
source_families = [BOLLINGER_MONTHLY]
source_timeframe = monthly
reaction_count = 0
structural_score = 31
active_relevance = ACTIVE_STRUCTURAL
last_meaningful_interaction = 2026-08-03
```

The resistance center is approximately:

```text
$425.89
```

and is a derived monthly Bollinger level, not an observed structural high.

At the same time, the existing structure engine contains actual price-anchored major evidence:

```text
dominant_major_high
date = 2026-05-18
price = $408.61
confidence = high
source = major_swing_engine

recent_major_high
date = 2026-05-18
price = $408.61

first_higher_low / breakout_start
date = 2026-03-30
price = $272.11
```

Therefore the engine already has price-anchored evidence; the user-facing major selector is choosing an invalid semantic family.

---

# 3. Important root-cause hypothesis to verify

The following pattern is suspicious and MUST be traced:

```text
BOLLINGER_MONTHLY
reaction_count = 0
last_meaningful_interaction = current monthly observation date
confirmation_quality = 1.0
structural_score = high enough for ACTIVE_STRUCTURAL
```

A dynamic indicator observation date must not be treated as a historical price interaction date.

Verify whether:

```text
indicator observation recency
```

is leaking into:

```text
last_meaningful_interaction
interaction recency
reaction/structural scoring
major structural eligibility
```

Set:

```text
MAJOR_SR_ROOT_CAUSE = PASS / FAIL
INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0 / NONZERO
```

after repair.

---

# 4. Semantic contract — what "주요 구조 지지/저항" means

A user-facing major structural zone must have a real price anchor.

Required concept:

```text
MAJOR STRUCTURAL S/R
=
price-anchored historical structure
+
current role compatibility
+
same security/currency/adjustment basis
+
completed-bar temporal safety
```

A derived indicator by itself is not a historical structural anchor.

---

# 5. Price-anchor requirement

For a zone to be user-visible as:

```text
MAJOR_SUPPORT
MAJOR_RESISTANCE
```

require at least one qualifying price-anchored source.

Known examples of price-anchored evidence include repository-native equivalents of:

```text
validated PIVOT_*
validated major_swing / major_anchor
BALANCE_BOX with actual price boundaries
repeated reaction / rejection cluster
other source explicitly derived from observed OHLCV highs/lows/closes
```

Do not hard-code only these strings if the repository already has a semantic family classifier.

Create/reuse a semantic predicate such as:

```text
has_price_anchor_evidence(zone) == true
```

Hard:

```text
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
```

---

# 6. Dynamic-indicator-only families

The following families by themselves are NOT sufficient to label a zone major structural:

```text
BOLLINGER_*
FIBONACCI_*
wave projection
moving-average-only derived bands
other forward/derived volatility envelopes
```

They may remain:

```text
confluence
confirmation
volatility reference
projection
```

but not the sole structural anchor.

Hard:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
FIB_ONLY_MAJOR_SR_VISIBLE = 0
PROJECTION_ONLY_MAJOR_SR_VISIBLE = 0
```

---

# 7. Bollinger as confluence, not sole anchor

Allowed:

```text
PIVOT_MONTHLY + BOLLINGER_MONTHLY
→ major structural candidate
```

if the pivot itself passes all gates.

Allowed:

```text
BALANCE_BOX + BOLLINGER_WEEKLY
→ major candidate only if the balance-box evidence qualifies as actual price structure
```

Not allowed:

```text
BOLLINGER_MONTHLY only
→ MAJOR_SUPPORT / MAJOR_RESISTANCE
```

Bollinger may increase confidence only AFTER price-anchor eligibility is established.

---

# 8. Separate observation date from interaction date

Introduce/reuse semantically distinct fields:

```text
indicator_observation_date
last_price_interaction_date
historical_interaction_count
price_anchor_refs
```

Do not populate:

```text
last_price_interaction_date
historical_interaction_count
```

from the mere date on which Bollinger/Fib/MA was calculated.

If the existing public/internal contract must remain backward compatible:

fix semantics internally and add explicit audit metadata without breaking consumers.

Hard:

```text
INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0
DYNAMIC_FAMILY_FAKE_REACTION_COUNT = 0
```

---

# 9. `reaction_count = 0` rule

For dynamic-indicator-only zones:

```text
reaction_count = 0
```

must block major structural visibility.

For actual pivot/anchor evidence, a repository-native validated pivot may itself constitute a price anchor even if a generic merged-zone `reaction_count` field is zero.

Therefore do NOT implement:

```text
if reaction_count == 0: reject every major zone
```

Instead gate on actual price-anchor provenance.

This avoids incorrectly rejecting a valid confirmed major swing merely because a merged-zone counter was not populated.

---

# 10. Historical traded-range reality gate

Use canonical normalized OHLCV from the SAME:

```text
security
currency
corporate-action/adjustment basis
timeframe history
```

For a user-visible major resistance:

```text
its price anchor must come from an actually observed historical price point/boundary
```

For a user-visible major support:

same.

A derived resistance center above the highest observed relevant traded/anchored price cannot become major structural.

A derived support center below the lowest observed relevant traded/anchored price cannot become major structural.

Zone padding may extend slightly beyond the anchor price; the anchor itself must be real.

Hard:

```text
UNTRADED_DERIVED_MAJOR_RESISTANCE = 0
UNTRADED_DERIVED_MAJOR_SUPPORT = 0
```

---

# 11. Adjustment / corporate-action safety

Historical envelope and anchor validation must use the same canonical price basis.

Do not compare:

```text
adjusted zone
vs
unadjusted raw historical high
```

Hard:

```text
MAJOR_SR_ADJUSTMENT_BASIS_CONFLICT = 0
MAJOR_SR_SECURITY_BASIS_CONFLICT = 0
MAJOR_SR_CURRENCY_CONFLICT = 0
```

ADR/ordinary-share basis remains fail-closed.

---

# 12. Selector order

For user-visible major structural zones, use:

```text
1. eligibility / session / basis
2. current support-vs-resistance role
3. price-anchor reality gate
4. structural importance/rank
5. cross-timeframe confirmation
6. dynamic-indicator confluence
7. distance / presentation relevance
```

Do NOT rank Bollinger-only candidates first and then label the winner structural.

The reality gate must happen before final major ranking.

---

# 13. Existing major anchors should be reused

Do not invent a new swing algorithm.

The existing structure context already exposes data such as:

```text
major_anchors
major_swings
local_pivots
zones
balance boxes
```

Reuse validated repository-native price anchors.

This task is a selector/semantic ownership repair.

---

# 14. No forced replacement

If the old invalid major zone is rejected:

do NOT fill the empty slot with an arbitrary remote pivot.

Allowed outcomes:

```text
valid price-anchored major zone selected
or
major structural line omitted
```

Hard:

```text
FORCED_MAJOR_SR_FILL = 0
REMOTE_MAJOR_FILL_WITHOUT_MATERIALITY = 0
```

---

# 15. Missing major structural zone is normal

If no qualifying major support exists:

omit:

```text
• 주요 구조 지지: ...
```

If no qualifying major resistance exists:

omit that line.

Do not show:

```text
없음
N/A
계산 불가
```

inside the normal user message unless an actual safety warning matters.

---

# 16. GOOGL required post-repair behavior

The old GOOGL major resistance:

```text
$424.82~$426.96
source = BOLLINGER_MONTHLY only
reaction_count = 0
```

must NOT remain user-visible as `주요 구조 저항`.

Hard:

```text
GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE = 0
```

The old GOOGL major support:

```text
$267.08~$268.43
source = BOLLINGER_MONTHLY only
reaction_count = 0
```

must also not remain solely on that basis.

Hard:

```text
GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE = 0
```

A new price-anchored major zone may be selected if the existing engine proves it valid.

Do NOT hard-code `$408.61` or `$272.11` as the final displayed ranges.

They are regression evidence, not target outputs.

---

# 17. Preserve GOOGL near structure

Pre-fix near structure:

```text
near support ~ $329.40~$331.07
near resistance ~ $349.88~$351.66
```

This task does not automatically invalidate near/dynamic support-resistance.

Do not change near-zone semantics unless the shared repair necessarily exposes a separate correctness defect.

Hard:

```text
UNRELATED_NEAR_SR_POLICY_REWRITE = 0
```

---

# 18. US pre-fix Bollinger-only major inventory

From the supplied current-time E2E artifact, these user-visible major zones were Bollinger-only before this repair and MUST be re-audited:

```text
CORZ  MAJOR_SUPPORT      BOLLINGER_MONTHLY
GOOGL MAJOR_SUPPORT      BOLLINGER_MONTHLY
GOOGL MAJOR_RESISTANCE   BOLLINGER_MONTHLY
HUT   MAJOR_RESISTANCE   BOLLINGER_WEEKLY
IBM   MAJOR_RESISTANCE   BOLLINGER_MONTHLY
MU    MAJOR_RESISTANCE   BOLLINGER_MONTHLY
SKHY  MAJOR_RESISTANCE   BOLLINGER_DAILY
SNDK  MAJOR_RESISTANCE   BOLLINGER_WEEKLY
TSLA  MAJOR_SUPPORT      BOLLINGER_MONTHLY
TSM   MAJOR_SUPPORT      BOLLINGER_MONTHLY
TSM   MAJOR_RESISTANCE   BOLLINGER_MONTHLY
WULF  MAJOR_SUPPORT      BOLLINGER_MONTHLY
```

Do not write ticker-specific exceptions.

Under the new contract, each must either:

```text
be replaced by a qualifying price-anchored major zone
or
be omitted
```

---

# 19. Mixed-family controls that should not be rejected merely for Bollinger presence

Examples from the same artifact:

```text
CRCL MAJOR_SUPPORT
→ BOLLINGER_WEEKLY + PIVOT_WEEKLY

IBM MAJOR_SUPPORT
→ BOLLINGER_MONTHLY + PIVOT_MONTHLY

TSLA MAJOR_RESISTANCE
→ BOLLINGER_MONTHLY + PIVOT_MONTHLY
```

These are positive controls for:

```text
Bollinger as confluence after price-anchor eligibility
```

They still must pass all other gates.

---

# 20. Pivot-only positive controls

Examples from the same artifact include:

```text
CORZ MAJOR_RESISTANCE → PIVOT_MONTHLY
CRCL MAJOR_RESISTANCE → PIVOT_WEEKLY
HUT MAJOR_SUPPORT → PIVOT_MONTHLY
RXRX MAJOR_SUPPORT / RESISTANCE → PIVOT_MONTHLY
```

Use them to prove the repair does not erase legitimate price-anchored major zones.

---

# 21. Track A — root-cause + semantic repair

Trace:

```text
candidate generation
→ source-family attribution
→ interaction metadata
→ structural scoring
→ major-support/resistance ranking
→ numeric registry
→ renderer
```

Answer:

1. Why did GOOGL Bollinger-only zones receive `ACTIVE_STRUCTURAL`?
2. Why did `reaction_count=0` not block major visibility?
3. What exactly populated `last_meaningful_interaction=2026-08-03`?
4. Did indicator observation recency affect structural score?
5. Why were actual `major_anchors` not preferred?
6. Is the bug shared across KR/US?

Implement the smallest generic repair.

---

# 22. Track B — US full-universe replay

Replay ALL current monitored US/foreign stocks at the latest safe completed session.

Previous current universe had 13:

```text
CORZ CRCL GOOGL HUT IBM MU RXRX SKHY SNDK TSLA TSM WRD WULF
```

Use actual current universe at execution time.

Per ticker record:

```text
current price
eligibility
near support/resistance
major support/resistance BEFORE
major support/resistance AFTER
source families
price-anchor refs
historical interaction metadata
reason for retained/replaced/omitted
Fib visibility
stored-rule ownership
rendered Price Structure block
```

---

# 23. Track B — KR 7-control replay

Also replay these KR controls with current/safe available data:

```text
000660
003690
005490
005930
010120
012450
086280
```

Purpose:

```text
shared selector semantic regression
```

Do not require today’s numbers to match old frozen-session numbers.

Require:

```text
no Bollinger-only major structural label
near proximity semantics preserved
current-vs-stored ownership preserved
Fib family safety preserved
```

---

# 24. Cross-market zero-tolerance gate

Before test-sink send:

```text
US all current monitored names PASS
KR 7/7 controls PASS
```

Hard:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
UNTRADED_DERIVED_MAJOR_RESISTANCE = 0
UNTRADED_DERIVED_MAJOR_SUPPORT = 0
```

---

# 25. AI / fallback parity

For every replayed stock generate:

```text
AI candidate
deterministic fallback
```

Required parity:

```text
same major-zone eligibility
same authoritative major-zone numerics
same omission/replacement decision
same source-anchor ownership
same current-vs-stored ownership
```

Hard:

```text
AI_FALLBACK_MAJOR_SR_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_MAJOR_SR_NUMERIC_PARITY = PASS
AI_FALLBACK_MAJOR_SR_OMISSION_PARITY = PASS
```

---

# 26. Numeric registry / provenance

Every displayed major structural numeric must carry:

```text
fact_ref / zone_id
semantic_type
currency
source families
source refs
price-anchor refs
source timeframe(s)
as_of
security basis
adjustment basis
```

Hard:

```text
MAJOR_SR_NUMBERS_WITHOUT_PROVENANCE = 0
AI_CALCULATED_MAJOR_SR = 0
```

---

# 27. Renderer terminology

Only qualifying price-anchored structural zones may use:

```text
주요 구조 지지
주요 구조 저항
```

Do not silently relabel Bollinger-only ranges as structural.

If future product design wants to expose them, use a distinct concept such as:

```text
변동성 상단/하단
확장 참고 구간
```

but that is OUT OF SCOPE for this repair.

For now:

```text
Bollinger-only major candidate → omit from major structural line
```

---

# 28. Track C — dedicated test-sink proof

Use the existing dedicated non-production test sink.

Send test messages for:

```text
ALL current monitored US/foreign stocks
+
KR 7 controls
```

If a KR control is not in normal monitored-message routing, render/send it only through the existing test-only safe path.

No production recipients.

---

# 29. Test message review

For every received message verify:

```text
company header intact
current price basis intact
near support/resistance intact
major structural line only if price anchored
GOOGL $424.82~$426.96 absent as major resistance
no arbitrary replacement
Fib only if safe
stored rules separately labeled
no target/stop
no truncation
```

Hard:

```text
TEST_MAJOR_SR_MESSAGE_QUALITY = PASS
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
```

---

# 30. GOOGL exact test-sink control

The received GOOGL message must satisfy:

```text
GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE = 0
GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE = 0
```

If replacement zones appear:

report:

```text
display
source family
anchor date
anchor price
anchor ref
reason selected
```

If no valid replacement:

major line omission is PASS.

---

# 31. Cross-market before/after report

Create a compact table:

```text
market
ticker
semantic role
before zone
before families
before reaction count
after zone
after families
price anchor
after state = RETAINED / REPLACED / OMITTED
reason
```

This is the primary operator review artifact.

---

# 32. Operating promotion

Deploy only if:

```text
root cause confirmed
shared semantic repair PASS
US full-universe replay PASS
KR 7/7 replay PASS
test sink exact payload PASS
P0 = 0
material P1 = 0
```

Promote through normal path.

No feature-state changes are required.

Preserve:

```text
KR Price Structure ON
US Price Structure ON
Production Assist OFF
```

---

# 33. Post-deploy smoke

Read-only:

```text
GOOGL
all current US/foreign monitored stocks
KR 7 controls
US market digest
KR market digest
```

Hard:

```text
POST_DEPLOY_MAJOR_SR_REALITY_GATE = PASS
POST_DEPLOY_US_PRICE_STRUCTURE = PASS
POST_DEPLOY_KR_PRICE_STRUCTURE = PASS
US_MARKET_DIGEST_DIFF = 0
KR_MARKET_DIGEST_DIFF = 0
```

---

# 34. Next natural proof

Do not manually trigger production.

Observe the next natural stock-monitoring messages.

Verify:

```text
major structural lines are price anchored
no Bollinger-only major structural labels
GOOGL old 424 zone absent
near SR still useful
stored price rules separate
Fib safe
exactly once
```

Set:

```text
NATURAL_MAJOR_SR_REALITY_GATE = PASS / FAIL
```

---

# 35. Do not overcorrect

This repair must NOT mean:

```text
only monthly pivots are major
all reaction_count=0 zones are invalid
all Bollinger data is removed
near Bollinger zones are banned
all distant major zones are banned
```

A distant major zone can be valid if it is genuinely price anchored and structurally material.

The issue is:

```text
derived-only level presented as historical structural S/R
```

---

# 36. No target / stop conversion

Hard:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

Do not convert an actual prior high into a target.

---

# 37. Stored price-rule isolation

Hard:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
```

---

# 38. Fib / wave isolation

Do not change:

```text
family consensus
ambiguity handling
Fib eligibility
wave state machine
```

except if a major-zone confluence consumer needs the new price-anchor eligibility flag.

Hard:

```text
FIB_FAMILY_POLICY_DIFF = 0
WAVE_POLICY_DIFF = 0
```

---

# 39. Price Structure eligibility

Do not change:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

A stock can remain `ELIGIBLE_SR_ONLY` even when one/both major structural lines are omitted.

Do not downgrade the whole Price Structure section merely because no valid major structural zone exists.

---

# 40. Required focused tests

### Historical GOOGL negative controls

```text
BOLLINGER_MONTHLY-only $424.82~$426.96 → rejected as major
BOLLINGER_MONTHLY-only $267.08~$268.43 → rejected as major
```

### Price-anchor positive controls

```text
validated PIVOT_* major zone → retained if otherwise eligible
validated major_swing anchor → eligible for consideration
BALANCE_BOX actual-price anchor → eligible for consideration
```

### Mixed family

```text
PIVOT + BOLLINGER → price-anchor gate PASS
BOLLINGER only → FAIL major gate
```

### Metadata

```text
indicator observation date ≠ price interaction date
reaction metadata not fabricated
```

### Missing output

```text
no valid major resistance → omit line
no valid major support → omit line
```

---

# 41. Full regression

Required:

```text
Price Structure major selector tests
deterministic SR tests
proximity tests
family consensus tests
renderer integration tests
legacy technical suppression
US current monitored full replay
KR 7-control replay
AI/fallback parity
test-sink exact payload

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
OHLCV health
```

No Public Action change expected.

---

# 42. Required architecture docs

Create/update:

```text
docs/architecture/PRICE_STRUCTURE_MAJOR_SR_REALITY_GATE.md
docs/architecture/PRICE_STRUCTURE_V3_RENDERER_INTEGRATION.md
docs/architecture/US_PRICE_STRUCTURE_SELECTIVE_ROLLOUT.md
```

Document the distinction:

```text
historical price anchor
vs
dynamic indicator observation
vs
confluence
```

---

# 43. Required reports

Create:

1. `docs/reports/20260828-major-sr-reality-gate-root-cause.md`
2. `docs/reports/20260828-googl-major-sr-negative-control.md`
3. `docs/reports/20260828-major-sr-price-anchor-contract.md`
4. `docs/reports/20260828-major-sr-indicator-interaction-semantics.md`
5. `docs/reports/20260828-us-major-sr-before-after.md`
6. `docs/reports/20260828-kr7-major-sr-before-after.md`
7. `docs/reports/20260828-major-sr-ai-fallback-parity.md`
8. `docs/reports/20260828-major-sr-test-delivery.md`
9. `docs/reports/20260828-major-sr-exact-test-messages.md`
10. `docs/reports/20260828-major-sr-operating-promotion.md`
11. `docs/reports/20260828-major-sr-post-deploy-smoke.md`
12. `docs/reports/20260828-major-sr-natural-proof-status.md`
13. `docs/reports/20260828-major-sr-readiness.md`
14. `docs/reports/20260828-major-sr-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-major-sr-before-after.json
docs/reports/20260828-kr7-major-sr-before-after.json
docs/reports/20260828-major-sr-readiness.json
```

---

# 44. Required gates

Set exactly:

```text
MAJOR_SR_ROOT_CAUSE =
PASS / FAIL

INDICATOR_OBSERVATION_AS_PRICE_INTERACTION =
0 / NONZERO

DYNAMIC_FAMILY_FAKE_REACTION_COUNT =
0 / NONZERO

MAJOR_SR_WITHOUT_PRICE_ANCHOR =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

FIB_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

PROJECTION_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

UNTRADED_DERIVED_MAJOR_RESISTANCE =
0 / NONZERO

UNTRADED_DERIVED_MAJOR_SUPPORT =
0 / NONZERO

MAJOR_SR_ADJUSTMENT_BASIS_CONFLICT =
0 / NONZERO

MAJOR_SR_SECURITY_BASIS_CONFLICT =
0 / NONZERO

MAJOR_SR_CURRENCY_CONFLICT =
0 / NONZERO

FORCED_MAJOR_SR_FILL =
0 / NONZERO

REMOTE_MAJOR_FILL_WITHOUT_MATERIALITY =
0 / NONZERO

GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE =
0 / NONZERO

GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE =
0 / NONZERO

UNRELATED_NEAR_SR_POLICY_REWRITE =
0 / NONZERO

US_CURRENT_MONITORED_REPLAY =
PASS / FAIL

KR7_CONTROL_REPLAY =
PASS / FAIL

AI_FALLBACK_MAJOR_SR_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_MAJOR_SR_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_MAJOR_SR_OMISSION_PARITY =
PASS / FAIL

MAJOR_SR_NUMBERS_WITHOUT_PROVENANCE =
0 / NONZERO

AI_CALCULATED_MAJOR_SR =
0 / NONZERO

TEST_MESSAGE_COUNT =
...

TEST_MAJOR_SR_MESSAGE_QUALITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

POST_DEPLOY_MAJOR_SR_REALITY_GATE =
PASS / NOT_RUN / FAIL

POST_DEPLOY_US_PRICE_STRUCTURE =
PASS / NOT_RUN / FAIL

POST_DEPLOY_KR_PRICE_STRUCTURE =
PASS / NOT_RUN / FAIL

US_MARKET_DIGEST_DIFF =
0 / NONZERO

KR_MARKET_DIGEST_DIFF =
0 / NONZERO

FIB_FAMILY_POLICY_DIFF =
0 / NONZERO

WAVE_POLICY_DIFF =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

MAJOR_SR_REALITY_GATE =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_MAJOR_SR_REALITY_GATE =
PENDING / PASS / FAIL
```

---

# 45. Pre-deploy PASS rule

Require:

```text
GOOGL old Bollinger-only major zones rejected
all Bollinger-only major labels removed/replaced by real anchors
no false reaction metadata
US full universe PASS
KR 7 controls PASS
AI/fallback parity PASS
test sink PASS
no target/stop
no market-message regression
P0 = 0
material P1 = 0
```

Then:

```text
MAJOR_SR_REALITY_GATE =
DEPLOYED_AWAITING_NATURAL_PROOF
```

after operating promotion.

---

# 46. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_RESULT = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

MAJOR_SR_ROOT_CAUSE = ...
INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0
DYNAMIC_FAMILY_FAKE_REACTION_COUNT = 0

GOOGL_BEFORE_MAJOR_SUPPORT = ...
GOOGL_BEFORE_MAJOR_RESISTANCE = ...
GOOGL_AFTER_MAJOR_SUPPORT = ...
GOOGL_AFTER_MAJOR_RESISTANCE = ...
GOOGL_AFTER_SUPPORT_ANCHOR = ...
GOOGL_AFTER_RESISTANCE_ANCHOR = ...

GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE = 0
GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE = 0

US_CURRENT_MONITORED_COUNT = ...
US_CURRENT_MONITORED_REPLAY = ...
US_MAJOR_RETAINED_COUNT = ...
US_MAJOR_REPLACED_COUNT = ...
US_MAJOR_OMITTED_COUNT = ...

KR7_CONTROL_REPLAY = ...
KR_MAJOR_RETAINED_COUNT = ...
KR_MAJOR_REPLACED_COUNT = ...
KR_MAJOR_OMITTED_COUNT = ...

BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
UNTRADED_DERIVED_MAJOR_RESISTANCE = 0
UNTRADED_DERIVED_MAJOR_SUPPORT = 0
FORCED_MAJOR_SR_FILL = 0

AI_FALLBACK_MAJOR_SR_ELIGIBILITY_PARITY = ...
AI_FALLBACK_MAJOR_SR_NUMERIC_PARITY = ...
AI_FALLBACK_MAJOR_SR_OMISSION_PARITY = ...

TEST_MESSAGE_COUNT = ...
TEST_MAJOR_SR_MESSAGE_QUALITY = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0

OPERATING_PROMOTION = ...
POST_DEPLOY_MAJOR_SR_REALITY_GATE = ...
POST_DEPLOY_US_PRICE_STRUCTURE = ...
POST_DEPLOY_KR_PRICE_STRUCTURE = ...

US_MARKET_DIGEST_DIFF = 0
KR_MARKET_DIGEST_DIFF = 0
FIB_FAMILY_POLICY_DIFF = 0
WAVE_POLICY_DIFF = 0

UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...
OHLCV_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

MAJOR_SR_REALITY_GATE =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_MAJOR_SR_REALITY_GATE =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 47. Mandatory completion ZIP

Create:

`20260828-price-structure-major-sr-reality-gate-repair-bundle.zip`

Include:

```text
exact instruction
root-cause report
GOOGL negative-control evidence
price-anchor semantic contract
indicator-vs-price-interaction report
US full-universe before/after
KR 7-control before/after
AI/fallback parity
test delivery
exact test messages
operating promotion
post-deploy smoke
natural-proof status
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw Telegram sink IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 48. Final principle

`주요 구조 지지/저항` must answer:

```text
"Where has actual price structure created a meaningful historical level?"
```

It must NOT answer:

```text
"Where is a derived volatility band currently projected?"
```

Bollinger/Fib/projections may strengthen a real price-anchored structural zone.

They may not manufacture one.
