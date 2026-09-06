# thesis-monitor — Official Fundamental Enrichment + Pre-Model Source Sufficiency + New Holdout
## Fix cold-start fundamental breadth, not the decision engine
## Enrich unseen packets with approved read-only business/earnings/filing evidence
## Add a framework-aware pre-model source-sufficiency gate
## Never call directional judgment on price-only packets
## Use the prior unseen16 only as enrichment fixtures
## Select a completely NEW issuer-level holdout after source-enrichment freeze
## Run FIRST → A → B → C on one immutable source lock
## Keep live V2 / Telegram / scheduler / DB / night-futures untouched

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-unseen-source-assembly-coldstart-generalization-proof-report.zip
```

SHA-256:

```text
d4137d320975c328f3cbfeffcc37b1ade03df8b81c22d4b5b07d28415d1821fc
```

Source branch / commits reported by execution:

```text
branch:
codex/20260906-unseen-source-assembly-coldstart

work-instruction commit:
ce927d9

implementation freeze:
3e77c89

final report commit:
c067a4a
```

Source program generation:

```text
20260906-unseen-source-coldstart-20260906T045044Z-f6ba15029561
```

Source unseen lock:

```text
295747d087f29f688e18d2bcccb74a752ef71b5224c1374a198da1181549d3a2
```

Source outcome:

```text
archive-independent fixture = 11/11 ASSEMBLED

final unseen cohort = 16
US = 8
KR = 8

FIRST = 8/16
A = 16/16
B = 12/16
C = NOT_RUN

validator false positive = 0
hard-safety regression = 0
future-checkpoint failure = 0
LEAF schema failure = 0
metric ownership failure = 0
source drift = 0
same-generation repair = 0

verdict =
GENERALIZATION_NEEDS_ARCHITECTURE_WORK

readiness =
NEEDS_ARCHITECTURE_WORK
```

Source-quality audit:

```text
identity/security basis =
AVAILABLE_ALL

price context =
AVAILABLE_ALL

deterministic price structure =
AVAILABLE_ALL_OR_PARTIAL_SAFE

latest earnings context =
UNAVAILABLE_PRESERVED_AS_UNKNOWN

event/filing evidence =
UNAVAILABLE_PRESERVED_AS_UNKNOWN

cash-flow/capital efficiency =
UNAVAILABLE_PRESERVED_AS_UNKNOWN

valuation =
UNAVAILABLE_PRESERVED_AS_UNKNOWN

relative to retired22 =
MATERIALLY_LOWER_FUNDAMENTAL_BREADTH
```

Blocking observation in the source report:

```text
US cold-start packets lacked non-price business evidence;
FIRST failed 8 and B failed 4 on
confirmation_business_condition_without_business_evidence
```

The bounded repair requested by the source report is:

```text
Add approved read-only business/earnings/filing evidence
before a new source freeze and new holdout.
```

---

# 1. Root-cause framing

Do NOT repair:

```text
BUY/HOLD/SELL logic
Structured Actionability
action renderer semantics
claim validator thresholds
natural-language action detector
```

The decision architecture is already proven clean on:
- hard-safety
- source fencing
- metric ownership
- actionability
- renderer ownership
- retired USKR22 one-shot regression

The current defect is:

```text
cold-start source packet
has identity + price
but insufficient issuer-specific fundamentals
```

Therefore:

```text
ROOT_CAUSE_CLASS =
COLD_START_FUNDAMENTAL_EVIDENCE_GAP
```

until fresh approved-source enrichment proves otherwise.

---

# 2. Decision engine byte-level freeze

The following hashes must remain unchanged throughout this task:

```text
builder_prompt =
2a4e6b4775db5e3f4d1b56b3f804613994e2602e4aaefd7902a9c1640cacb672

directional_balance =
2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab

logical_condition =
255837edf51ff7fe06f26ed4d4782479131d2485e5e19349aa2a3f095ca1d234

stability =
e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188

validator_renderer =
ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f

prompt_set =
95a46a8d3ac708aa981203270236eec7b21bdf196be7577245cc1e52fea50c89

schema_set =
e86b747a0c6f459650275598a7c3c217bb0116ef6b6f8927debf3dfa938fd668
```

Required:

```text
DECISION_ENGINE_HASH_DRIFT = 0
INVESTMENT_DECISION_THRESHOLD_MUTATION = 0
ACTIONABILITY_CONTRACT_MUTATION = 0
RENDERER_DECISION_SEMANTIC_MUTATION = 0
VALIDATOR_POLICY_WEAKENING = 0
```

If any decision hash must change to complete this task:

```text
STOP
```

and report why source enrichment could not be isolated.

---

# 3. Allowed implementation surface

Allowed changes are restricted to:

```text
approved read-only issuer fundamentals acquisition
filing / earnings source orchestration
fundamental fact normalization
source provenance
framework-aware source-sufficiency classification
cold-start packet assembly
issuer identity / issuer-level exclusion
candidate pool / holdout harness
```

Forbidden:

```text
ticker-specific decision prompt
ticker-specific validator exception
label targeting
price threshold tuning
WAIT/AVOID tuning
holder stance tuning
new action-language whitelist
```

---

# 4. Discover existing approved fundamental paths first

Before writing new provider logic, inventory the repository paths already used to obtain fundamentals for the mature/retired cohort.

Search for canonical existing components providing, where supported:

```text
company/security identity
official filings
official earnings / provisional earnings
reported revenue / operating income / margins
balance-sheet facts
operating cash flow
capex
FCF
sector-appropriate operating metrics
business events
valuation denominators / provider multiples with safe basis
```

Produce a reuse map:

```text
existing component
approved source/provider
market coverage
input contract
output facts
freshness semantics
security-basis handling
reuse unchanged / generic adapter required
```

Prefer reuse.

---

# 5. Approved-source hierarchy

Follow existing approved source hierarchy.

Preferred:

```text
KR:
official exchange / OpenDART / company official disclosure paths
already approved in repository

US/foreign:
SEC / company official earnings / approved structured official paths
already approved in repository
```

Do NOT introduce:

```text
new paid provider
browser scraping
ad-hoc HTML scraping
manual ticker facts
manual financial CSV
community/reddit data
news as a substitute for official earnings
```

Required:

```text
NEW_PAID_PROVIDER = 0
NEW_WEBSITE_SCRAPER = 0
MANUAL_TICKER_FACT_INJECTION = 0
```

---

# 6. Fundamental evidence families

Create or expose source-owned evidence-family metadata.

Suggested generic families:

```text
IDENTITY_SECURITY
BUSINESS_CURRENT
EARNINGS_FINANCIAL_CURRENT
LIQUIDITY_CASHFLOW_CURRENT
SECTOR_OPERATING_CURRENT
REGULATORY_CAPITAL_CURRENT
CLINICAL_REGULATORY_CURRENT
CAPITAL_ALLOCATION_CURRENT
VALUATION_SAFE
PRICE_CONTEXT
MARKET_CONTEXT
```

Exact enum names should follow repository conventions.

The family is source/normalizer-owned.

Do not infer evidence family from arbitrary Korean prose.

---

# 7. BUSINESS_CURRENT

Examples of valid `BUSINESS_CURRENT` anchors may include:

```text
official segment / business description
current reported revenue mix
reported orders/backlog
reported customer/region mix
reported capacity / utilization
official company operating update
material official business event
```

A generic sector label alone is NOT sufficient.

A stock-price move is NOT sufficient.

A chart signal is NOT sufficient.

---

# 8. EARNINGS_FINANCIAL_CURRENT

Examples may include hard-valid, current:

```text
revenue
operating income / margin
net income attribution where safe
reported EPS where safe
cash / debt
OCF
capex
FCF
regulatory capital
sector-appropriate reported financial KPI
```

Do not require EPS for all companies.

Do not fabricate denominators.

Do not annualize one quarter.

Preserve current accounting/security-basis rules.

---

# 9. Sector/lifecycle alternatives

Source sufficiency must be framework-aware, not a single fixed checklist.

Examples:

## Standard operating company

Typical sufficient combination:

```text
BUSINESS_CURRENT
+
EARNINGS_FINANCIAL_CURRENT
```

## Bank / insurer

May use:

```text
EARNINGS_FINANCIAL_CURRENT
+
REGULATORY_CAPITAL_CURRENT
and/or
sector-relevant underwriting / credit metrics
```

## Pre-profit biotech

May use:

```text
CLINICAL_REGULATORY_CURRENT
+
LIQUIDITY_CASHFLOW_CURRENT
```

Revenue/PER is not mandatory.

## Asset-heavy / cyclical

May require current operating/cycle evidence plus financial evidence appropriate to the framework.

Do not encode ticker-specific requirements.

---

# 10. Pre-model source sufficiency gate

Add a deterministic gate BEFORE any Structured Autonomy judgment call.

Suggested statuses:

```text
SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT

SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY

INSUFFICIENT_FUNDAMENTAL_EVIDENCE

SECURITY_OR_ACCOUNTING_BASIS_BLOCK

SOURCE_FRESHNESS_BLOCK
```

Exact enum names may follow repository style.

The gate must be explainable by evidence-family presence/quality, not a hidden weighted score.

---

# 11. Directional judgment eligibility

A packet may call the Structured Autonomy directional model only if:

```text
identity/security basis is hard-valid
+
at least one valid issuer-specific fundamental/business anchor
+
at least one valid financial/operating/liquidity/regulatory anchor
appropriate to the analysis framework
+
required evidence is not materially stale/invalid
```

Valuation is NOT universally mandatory.

Price context is NOT sufficient by itself.

Required:

```text
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0
```

---

# 12. Insufficient packet behavior

If the source-sufficiency gate fails:

```text
do not call the directional judgment model
```

Return a source/preflight classification such as:

```text
INSUFFICIENT_FUNDAMENTAL_EVIDENCE
```

with:
- what evidence family is missing
- why it matters
- which approved source path was attempted
- whether the issue is unavailable, stale, validation-failed, or unsupported

Do NOT create:
- BUY
- HOLD
- SELL
- BUY:SELL
- new-buyer stance
- holder stance

from a price-only packet.

Required:

```text
DIRECTIONAL_MODEL_CALLS_ON_INSUFFICIENT_PACKET = 0
```

---

# 13. Source sufficiency must not use price direction

The gate must not become a hidden investment model.

Forbidden inputs to sufficiency eligibility:

```text
price rising/falling
RSI/MACD
support/resistance
BUY/HOLD/SELL expectation
valuation attractiveness
prior AI label
```

The gate asks only:

```text
Do we have enough trustworthy issuer fundamentals
to permit directional investment judgment?
```

---

# 14. Missing valuation handling

If fundamentals are sufficient but valuation is unavailable:

```text
valuation = UNKNOWN
```

Do not automatically block directional business judgment.

However:
- new-buyer attractiveness may be confidence-limited
- valuation-specific claims must remain unavailable
- no invented target/cheapness conclusion

Preserve existing valuation safety.

---

# 15. Freshness

Use existing data-quality semantics:

```text
fresh / current
partial
stale / refresh_due
validation_failed
unavailable
conflicting
```

Do not invent a universal day-count threshold if the repository already has expected reporting cadence.

A stale fundamental anchor may not satisfy a current directional gate if it is beyond the framework/provider's normal cadence.

Report the exact reason.

---

# 16. Fundamental enrichment packet contract

Cold-start packet should now support, where available:

```text
identity/security basis
company/business facts
official latest earnings/financial facts
material filing/event facts
cash-flow/capital-efficiency facts
sector-relevant operating facts
safe valuation context
price context
market context
source quality / provenance
```

Unavailable fields remain Unknown.

Do not force all families into every industry.

---

# 17. No stored thesis dependency

Preserve the already-proven lifecycle result:

```text
stored monitoring state required = 0
monitoring thesis required = 0
prior daily assessment required = 0
thesis version required = 0
stored price rules required = 0
unregistered ticker supported = 1
```

Do not auto-register fixture or unseen subjects.

Required:

```text
MONITORING_REGISTRATION_CALLS = 0
PRODUCTION_DB_MUTATION = 0
```

---

# 18. Prior unseen16 becomes enrichment fixture only

Use the previous unseen16 ONLY to test source enrichment and the source-sufficiency gate.

Fixture set:

```text
US:
LLY
AAPL
NFLX
GOOG
CRM
PFE
META
AMD

KR:
446070
011090
093370
092460
067280
309930
397810
027970
```

Do NOT run Structured Autonomy judgment on these fixtures in this task.

They have already been exposed to model outputs.

Required:

```text
PRIOR_UNSEEN16_JUDGMENT_MODEL_CALLS = 0
```

---

# 19. Fixture objective

For each prior unseen16 fixture, attempt approved fundamental enrichment.

Report:

```text
identity
issuer id
business evidence families
financial/earnings evidence families
valuation availability
freshness
source provenance
sufficiency status
missing families
```

This fixture stage answers:

```text
Can the generic cold-start source path actually add
issuer fundamentals to the same subjects that previously had none?
```

It is not a judgment test.

---

# 20. Fixture-stage repair policy

Before final source-enrichment freeze, generic source-side defects may be repaired.

Allowed examples:

```text
SEC filing path not wired into cold-start assembler
OpenDART financial facts not added to cold-start fact catalog
company official earnings normalizer not reused
issuer identity not propagated to packet
source-family metadata missing
freshness classification bug
```

Forbidden:

```text
AAPL-specific path
LLY-specific facts
011090-specific financial mapping
manual packet patch
manual issuer fact entry
```

---

# 21. Source-enrichment promotion gate

Before selecting a final holdout, require:

```text
all source-enrichment tests pass
hard accounting/security-basis regression = 0
fixture judgment calls = 0
source-sufficiency gate unit tests pass
```

Also require a meaningful fixture result.

Do not require 16/16 fixture sufficiency by weakening standards.

But if the generic enrichment path produces almost no fundamental anchors across the fixtures:

```text
STOP
```

and report real provider/source limitations.

Suggested diagnostic:

```text
fixture_sufficient_count
fixture_limited_count
fixture_real_source_failure_count
```

No arbitrary pass threshold should override source truth.

---

# 22. Source-sufficiency synthetic tests

Before final holdout selection, create ticker-free packet fixtures.

At minimum test:

```text
identity + price only
→ INSUFFICIENT

identity + business only
→ LIMITED / INSUFFICIENT

identity + financial only
→ LIMITED / INSUFFICIENT

standard company:
business + earnings
→ SUFFICIENT

bank/insurer:
earnings + regulatory capital
→ SUFFICIENT

pre-profit biotech:
clinical/regulatory + liquidity/runway
→ SUFFICIENT

stale-only fundamentals
→ SOURCE_FRESHNESS_BLOCK or LIMITED

validation-failed financial facts
→ not sufficient

valuation missing but fundamentals sufficient
→ directional eligibility may remain sufficient

price strong but fundamentals absent
→ still INSUFFICIENT

price weak but fundamentals absent
→ still INSUFFICIENT
```

Required:

```text
SOURCE_SUFFICIENCY_SYNTHETIC_SUITE = PASS
```

---

# 23. Freeze source enrichment and sufficiency gate

After fixture/synthetic work, freeze:

```text
source enrichment code
provider configuration
fundamental evidence-family registry
source sufficiency policy
freshness policy
issuer identity policy
candidate selection algorithm
packet schema/normalization
base-context builder
```

Then:

```text
SOURCE_ENRICHMENT_MUTATION_AFTER_FREEZE = 0
SOURCE_SUFFICIENCY_POLICY_MUTATION_AFTER_FREEZE = 0
```

---

# 24. Issuer-level holdout exclusion

The previous test demonstrated that ticker-only exclusion is insufficient:

```text
GOOG
and
GOOGL
```

are different securities of the same issuer.

The final holdout must exclude at issuer level.

Build canonical:

```text
issuer_id
security_id
share_class / security type where available
```

Exclusion means:

```text
if ANY security from issuer was previously in
retired22 / preflight11 / prior unseen16,
exclude ALL securities from that issuer
from the final judgment holdout.
```

Required:

```text
FINAL_HOLDOUT_ISSUER_OVERLAP = 0
```

---

# 25. Exclusion sets

Exclude at least the issuers represented by:

## Retired22

```text
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF, 000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280
```

## Earlier source-assembly fixtures11

```text
010140, 011200, 017800, 021240, 024110, 035420, 051160, 055550, 443060, MSFT, NVDA
```

## Prior unseen16 enrichment fixtures

```text
LLY, AAPL, NFLX, GOOG, CRM, PFE, META, AMD, 446070, 011090, 093370, 092460, 067280, 309930, 397810, 027970
```

Ticker overlap checks remain useful but are secondary.

Issuer overlap is authoritative.

---

# 26. Candidate universe

Use the canonical supported-security universe.

Do NOT require:
- watchlist membership
- monitoring registration
- prior AI-review packet
- prior base message

Do NOT select by:
- expected label
- popularity
- known company quality
- expected source richness after manual inspection

Selection policy must be fixed before final names are chosen.

---

# 27. Coverage audit before final selection

To avoid a holdout composed only of cherry-picked large caps, predeclare a ranked candidate pool before source outcomes.

Recommended when universe size permits:

```text
attempt first 64 ranked issuer-distinct candidates
```

Record:

```text
attempted
packet assembled
fundamental sufficient
limited
source unavailable
security/accounting blocked
KR/US counts
framework/sector distribution
```

This gives a real cold-start source-coverage rate.

Do not hide failures by replacing them silently.

---

# 28. Final holdout selection

Target:

```text
16 issuer-distinct unseen subjects
```

Preferred:

```text
KR 8
US 8
```

Allowed:

```text
12–20 total
```

Minimum executable:

```text
12
```

Fill from the predeclared deterministic ranking using only subjects that pass the frozen source-sufficiency gate.

Every skipped subject remains in the audit with an objective reason.

No manual replacement.

---

# 29. Holdout diversity

Use available canonical framework/sector metadata.

Seek reasonable diversity across:
- financial
- insurance
- consumer
- industrial
- software/cloud
- semiconductor/hardware
- healthcare/biotech
- asset-heavy/cyclical
- transport
- other supported frameworks

Do not force an unsupported category.

Do not use AI judgment to select diversity.

---

# 30. No model call before final source lock

Before final holdout source lock:

```text
STRUCTURED_AUTONOMY_DIRECTIONAL_CALLS = 0
AI_SEMANTIC_REVIEWER_JUDGMENT_CALLS = 0
```

Source enrichment and sufficiency classification are deterministic/read-only.

---

# 31. Immutable final source lock

For each eligible final subject freeze:

```text
issuer id
security id
ticker
market
business/financial evidence families
source fact IDs
source timestamps
freshness
security basis
valuation state
price context
packet SHA
base-context SHA
```

Create:

```text
NEW_UNSEEN_SOURCE_LOCK_SHA256
```

No source refresh between FIRST/A/B/C.

Required:

```text
FIRST_ABC_SOURCE_DRIFT = 0
```

---

# 32. Decision-engine re-verification

Immediately before FIRST, re-hash the frozen decision engine.

Required exact values:

```text
builder_prompt = 2a4e6b4775db5e3f4d1b56b3f804613994e2602e4aaefd7902a9c1640cacb672
directional_balance = 2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab
logical_condition = 255837edf51ff7fe06f26ed4d4782479131d2485e5e19349aa2a3f095ca1d234
stability = e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188
validator_renderer = ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f
prompt_set = 95a46a8d3ac708aa981203270236eec7b21bdf196be7577245cc1e52fea50c89
schema_set = e86b747a0c6f459650275598a7c3c217bb0116ef6b6f8927debf3dfa938fd668
```

Any mismatch:

```text
STOP
```

---

# 33. New unseen FIRST

Run FIRST once over the new source-sufficient holdout.

Use:

```text
gpt-5.6-sol / xhigh
```

or the same documented operating-equivalent model/effort only if the production-equivalent config changed before task start.

No:
- prior candidate reuse
- prior label visibility
- selective rerun
- candidate edit
- same-generation hotfix

---

# 34. FIRST failure taxonomy

Classify each non-validation result as:

```text
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ONTOLOGY_GAP
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
UNEXPECTED_SOURCE_SUFFICIENCY_ESCAPE
SCHEMA_FAILURE
```

Because all locked subjects already passed the pre-model sufficiency gate, a price-only/source-empty failure should now be treated as:

```text
UNEXPECTED_SOURCE_SUFFICIENCY_ESCAPE
```

and investigated in a later task, not repaired in this generation.

---

# 35. A/B/C gate

Proceed only if FIRST has:

```text
validator false positive = 0
schema failure = 0
hard-safety regression = 0
source-sufficiency escape = 0
```

Then run:

```text
A
B
C
```

on the exact same source lock.

No run reads another run.

No majority voting.

---

# 36. Stability

After completed FIRST/A/B/C, classify:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Evaluate:
- BUY/HOLD/SELL
- BUY:SELL balance
- new-buyer stance
- entry mode
- holder stance

Do not call a 5.5↔6.0 threshold crossing automatically unstable.

Do not tune thresholds.

---

# 37. Fundamental-vs-price dominance audit

This is a required diagnostic.

For every final unseen decision, record whether dominant decision evidence is:

```text
BUSINESS_FUNDAMENTAL
VALUATION
PRICE_TIMING
MIXED
```

Flag for review if:

```text
business/financial evidence exists
but directional BUY/SELL is dominated solely by price
without business/valuation support
```

This is advisory diagnostic unless it violates an existing hard rule.

Do NOT change the decision engine in this task.

---

# 38. Price-only direction guard

The pre-model gate already prevents price-only packets.

Additionally verify:

```text
no subject with INSUFFICIENT_FUNDAMENTAL_EVIDENCE
received BUY/HOLD/SELL
```

Required:

```text
DIRECTIONAL_DECISIONS_ON_INSUFFICIENT_PACKET = 0
```

This is a hard lifecycle invariant.

---

# 39. Renderer shadow proof

If FIRST is clean, render representative final unseen subjects using the frozen V2 action renderer.

Verify:
- primary action wording comes from renderer
- rationale comes from AI
- no imperative command
- price review separate from business invalidation
- unavailable valuation does not become invented cheap/expensive claim

Required:

```text
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0
```

---

# 40. Hard-safety regression

Re-run all existing hard-safety suites, including:

```text
numeric provenance
accounting attribution
official provisional earnings
security / ADR basis
evidence identity
cross-ticker fencing
cross-generation fencing
severity ownership
future-checkpoint ownership
logical condition ownership
explicit actionable commands
structured/prose contradiction
lifecycle / exactly-once relevant tests
```

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 41. No provider degradation to meet quota

Do not weaken source standards to obtain 12 or 16 eligible names.

If fewer than 12 issuer-distinct subjects pass the frozen sufficiency gate:

```text
GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE
```

and stop before AI judgment.

This time that verdict is legitimate because approved fundamental sources were actually attempted.

---

# 42. Generalization verdict

Possible verdicts:

```text
GENERALIZATION_STRONG

GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY

GENERALIZATION_NEEDS_ARCHITECTURE_WORK

GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE
```

Use:
- source coverage
- source sufficiency escapes
- validator false positives
- hard-safety behavior
- A/B/C stability
- fundamental-vs-price dominance diagnostics

Do not use label distribution as a target.

---

# 43. Current 22 and prior holdouts remain frozen

Do not re-open:
- retired22
- preflight11
- prior unseen16

for judgment tuning.

They may remain regression/source fixtures only.

Any new architecture repair after this task requires:
- separate authorization
- a NEW source freeze
- another NEW issuer-level holdout

---

# 44. Production remains untouched

Required:

```text
MAIN_MERGE = 0
PRODUCTION_DB_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
NIGHT_FUTURES_PRODUCTION_MUTATION = 0
```

Current live legacy messages may continue.

---

# 45. Night futures

Night futures is already:

```text
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

No changes in this task.

It remains:
- market/timing context
- not company business evidence
- not earnings evidence
- not valuation evidence

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
```

---

# 46. Maximum readiness

If:
- approved fundamental enrichment works
- >=12 issuer-distinct new subjects pass sufficiency
- no source-sufficiency escapes
- FIRST/A/B/C complete cleanly
- hard-safety regression = 0
- generalization stability acceptable

then:

```text
READINESS =
READY_FOR_PRODUCTION_INTEGRATION_REVIEW
```

Still no deployment.

---

# 47. Next production integration handoff

If ready, prepare the next bounded task for:

```text
main merge review
deployment review
authoritative scheduled KR job activation
authoritative scheduled US job activation
Structured Autonomy decision source
+
V2 action renderer
+
exactly-once delivery
+
natural KR proof
+
natural US proof
```

A shadow or CLI V2 output is not live activation proof.

---

# 48. Required reports

Create:

1. `docs/reports/20260906-fundamental-enrichment-root-cause.md`
2. `docs/reports/20260906-approved-fundamental-source-reuse-map.md`
3. `docs/reports/20260906-fundamental-evidence-family-contract.md`
4. `docs/reports/20260906-source-sufficiency-contract.md`
5. `docs/reports/20260906-source-sufficiency-synthetic-suite.md`
6. `docs/reports/20260906-prior-unseen16-enrichment-fixtures.md`
7. `docs/reports/20260906-fundamental-source-coverage-audit.md`
8. `docs/reports/20260906-source-enrichment-freeze.md`
9. `docs/reports/20260906-issuer-identity-exclusion-policy.md`
10. `docs/reports/20260906-new-holdout-selection-policy.md`
11. `docs/reports/20260906-new-holdout-candidate-coverage.md`
12. `docs/reports/20260906-new-holdout-selection.md`
13. `docs/reports/20260906-new-holdout-source-preflight.md`
14. `docs/reports/20260906-new-holdout-source-lock.md`
15. `docs/reports/20260906-decision-engine-freeze-verification.md`
16. `docs/reports/20260906-new-unseen-first.md`
17. `docs/reports/20260906-new-unseen-run-a.md`
18. `docs/reports/20260906-new-unseen-run-b.md`
19. `docs/reports/20260906-new-unseen-run-c.md`
20. `docs/reports/20260906-new-unseen-stability.md`
21. `docs/reports/20260906-fundamental-vs-price-dominance-audit.md`
22. `docs/reports/20260906-new-unseen-renderer-shadow-proof.md`
23. `docs/reports/20260906-hard-safety-regression.md`
24. `docs/reports/20260906-generalization-verdict.md`
25. `docs/reports/20260906-production-integration-next-handoff.md`
26. `docs/reports/20260906-night-futures-no-change.md`
27. `docs/reports/20260906-program-completion.md`
28. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 49. Machine-readable proofs

Create:

```text
approved-fundamental-source-reuse-map.json
fundamental-evidence-family-contract.json
source-sufficiency-contract.json
source-sufficiency-synthetic-suite.json
prior-unseen16-enrichment-fixtures.json
fundamental-source-coverage-audit.json
source-enrichment-freeze.json
issuer-identity-exclusion-policy.json
new-holdout-selection-policy.json
new-holdout-candidate-coverage.json
new-holdout-selection.json
new-holdout-source-preflight.json
new-holdout-source-lock.json
decision-engine-freeze-verification.json
new-unseen-first.json
new-unseen-run-a.json
new-unseen-run-b.json
new-unseen-run-c.json
new-unseen-stability.json
fundamental-vs-price-dominance-audit.json
new-unseen-renderer-shadow-proof.json
hard-safety-regression.json
generalization-verdict.json
production-integration-next-handoff.json
night-futures-no-change.json
program-completion.json
```

---

# 50. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
d4137d320975c328f3cbfeffcc37b1ade03df8b81c22d4b5b07d28415d1821fc

ROOT_CAUSE_CLASS =
COLD_START_FUNDAMENTAL_EVIDENCE_GAP / OTHER

DECISION_ENGINE_HASH_DRIFT =
0 / NONZERO

NEW_PAID_PROVIDER =
0 / NONZERO

NEW_WEBSITE_SCRAPER =
0 / NONZERO

MANUAL_TICKER_FACT_INJECTION =
0 / NONZERO

MONITORING_REGISTRATION_CALLS =
0 / NONZERO

FUNDAMENTAL_EVIDENCE_FAMILY_REGISTRY =
PASS / FAIL

SOURCE_SUFFICIENCY_SYNTHETIC_SUITE =
PASS / FAIL

PRICE_ONLY_DIRECTIONAL_MODEL_CALLS =
0 / NONZERO

DIRECTIONAL_MODEL_CALLS_ON_INSUFFICIENT_PACKET =
0 / NONZERO

PRIOR_UNSEEN16_JUDGMENT_MODEL_CALLS =
0 / NONZERO

PRIOR_UNSEEN16_FIXTURE_SUFFICIENT_COUNT =
...

PRIOR_UNSEEN16_FIXTURE_LIMITED_COUNT =
...

PRIOR_UNSEEN16_FIXTURE_REAL_SOURCE_FAILURE_COUNT =
...

SOURCE_ENRICHMENT_MUTATION_AFTER_FREEZE =
0 / NONZERO

SOURCE_SUFFICIENCY_POLICY_MUTATION_AFTER_FREEZE =
0 / NONZERO

FINAL_HOLDOUT_ISSUER_OVERLAP =
0 / NONZERO

FINAL_HOLDOUT_TICKER_OVERLAP =
0 / NONZERO

CANDIDATE_COVERAGE_ATTEMPT_COUNT =
...

CANDIDATE_FUNDAMENTAL_SUFFICIENT_COUNT =
...

CANDIDATE_LIMITED_COUNT =
...

CANDIDATE_REAL_SOURCE_FAILURE_COUNT =
...

FINAL_HOLDOUT_SELECTED_COUNT =
...

FINAL_HOLDOUT_ELIGIBLE_COUNT =
...

FINAL_HOLDOUT_KR_COUNT =
...

FINAL_HOLDOUT_US_COUNT =
...

NEW_UNSEEN_SOURCE_LOCK_SHA256 =
...

STRUCTURED_AUTONOMY_DIRECTIONAL_CALLS_BEFORE_SOURCE_LOCK =
0 / NONZERO

FIRST_ABC_SOURCE_DRIFT =
0 / NONZERO

NEW_UNSEEN_FIRST_VALIDATED =
...

NEW_UNSEEN_FIRST_VALIDATOR_FALSE_POSITIVE =
0 / NONZERO

NEW_UNSEEN_FIRST_HARD_SAFETY_TRUE_REJECT =
...

NEW_UNSEEN_FIRST_ONTOLOGY_GAP =
...

NEW_UNSEEN_FIRST_SOURCE_SUFFICIENCY_ESCAPE =
0 / NONZERO

NEW_UNSEEN_FIRST_SCHEMA_FAILURE =
0 / NONZERO

NEW_UNSEEN_RUN_A_VALIDATED =
... / NOT_RUN

NEW_UNSEEN_RUN_B_VALIDATED =
... / NOT_RUN

NEW_UNSEEN_RUN_C_VALIDATED =
... / NOT_RUN

NEW_UNSEEN_STABLE_COUNT =
... / NOT_MEASURED

NEW_UNSEEN_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

NEW_UNSEEN_UNSTABLE_COUNT =
... / NOT_MEASURED

DIRECTIONAL_DECISIONS_ON_INSUFFICIENT_PACKET =
0 / NONZERO

PRICE_ONLY_DOMINATED_DIRECTIONAL_REVIEW_FLAGS =
...

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / OTHER

AI_IMPERATIVE_PRIMARY_ACTION =
0 / NONZERO

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

GENERALIZATION_VERDICT =
GENERALIZATION_STRONG /
GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY /
GENERALIZATION_NEEDS_ARCHITECTURE_WORK /
GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE

LIVE_STRUCTURED_AUTONOMY_ACTIVATION =
0 / NONZERO

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

READINESS =
READY_FOR_PRODUCTION_INTEGRATION_REVIEW /
NEEDS_ARCHITECTURE_WORK /
BLOCKED_BY_REAL_SOURCE_COVERAGE /
NOT_READY
```

---

# 51. Stop conditions

STOP if:
- any decision-engine hash changes
- any ticker-specific fundamental mapping is added
- any manual financial fact is injected
- price-only packets can call directional judgment
- sufficiency uses price direction or expected label
- prior unseen16 receives AI judgment
- final holdout overlaps any prior issuer
- GOOG/GOOGL-style same-issuer leakage remains possible
- source policy changes after final freeze
- packet changes after source lock
- same-generation unseen repair is proposed
- source standards are weakened to meet the 12/16 quota
- live V2 / scheduler / Telegram / DB / night futures are modified

---

# 52. Completion response

Return:

```text
FUNDAMENTAL ENRICHMENT =
approved sources reused
new dependency = 0
business/earnings/filing coverage

SOURCE SUFFICIENCY =
contract
synthetic suite
price-only model calls = 0

PRIOR UNSEEN16 FIXTURES =
sufficient ...
limited ...
real source failures ...
AI judgment calls = 0

ISSUER EXCLUSION =
policy
prior issuer overlap = 0

CANDIDATE COVERAGE =
attempted ...
fundamental sufficient ...
limited ...
real source failures ...

NEW HOLDOUT =
selected ...
eligible ...
KR/US ...
issuer overlap = 0

SOURCE LOCK =
...

DECISION ENGINE =
hash drift = 0

FIRST =
...

A =
...

B =
...

C =
...

STABILITY =
...

FUNDAMENTAL VS PRICE =
...

HARD SAFETY =
...

GENERALIZATION =
...

LIVE V2 =
not activated

NIGHT FUTURES =
unchanged

PRODUCTION MUTATION =
0

READINESS =
...

NEXT PRODUCTION INTEGRATION HANDOFF =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 53. Final principle

A cold-start stock is not analysis-ready merely because its price history exists.

The correct sequence is:

```text
issuer identity
→ trustworthy current fundamentals
→ framework-appropriate source sufficiency
→ immutable source lock
→ AI investment judgment
→ deterministic validation
→ V2 rendering
```

Never let:

```text
price-only packet
```

become:

```text
BUY / HOLD / SELL
```

just because the model can produce an answer.
