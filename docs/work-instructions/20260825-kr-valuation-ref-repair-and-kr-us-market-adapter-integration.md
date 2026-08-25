# thesis-monitor — KR Valuation Numeric-Ref Repair + KR/US Market Adapter Integration
## with Optional 2026-08-26 US Selective Live Canary

## Metadata

- Workstream: `POST_COMMON_CORE_MARKET_ADAPTERS`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: `2026-08-25 17:41 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_PRODUCTION_REPAIR + KR_US_ADAPTER_IMPLEMENTATION + CONDITIONAL_LIVE_CANARY`
- No paid APIs: `FREE_ONLY`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Expected current production main / operating

`b6ed8aaaf115bdae9c62b2c18eef7b8e61fa036f`

Resolve and use the actual latest safe `origin/main` and operating SHA.

### Current production state

```text
COMMON_AI_CORE_V1 = INTEGRATED_CANARY_PENDING_NATURAL

FREE_ANALYST_ADAPTIVE_CANARY =
ENABLED_PENDING_NATURAL

FREE_ANALYST_ADAPTIVE_FULL =
OFF

canary limits:
market <= 1
stocks <= 2
total <= 3

Production Assist governance = OFF
Pilot = enabled, unchanged

Open Research production integration = 0

Inventory = SELECTIVE_INVENTORY
Trade AR user-visible = OFF
Phase 9.0E = SELECTIVE_CURRENT_FORMAL_FULL_FCF
```

### Latest KR natural review

Known state:

```text
KR_PRODUCTION_NATURAL = LIVE_PASS
delivery = fallback 8/8
duplicates/orphans = 0/0
exactly-once = PASS

KR_FREE_ANALYST_CANARY_NATURAL = NOT_OBSERVED

reason:
SK hynix valuation numeric refs rejected before
the Free Analyst canary entry point

Inventory = LIVE_PASS
Investor Flow = LIVE_PASS
Macro = LIVE_PASS
Trade AR shadow proof = LIVE_PASS
Trade AR user-visible = 0

KRX 16:05 role target = LIVE_PASS
provider publication = pending

KR market digest domestic structured data =
INSUFFICIENT
```

Known rejected valuation refs:

```text
s000660_val_pbr:valuation:current
s000660_val_hist_pb:valuation:current
```

Verify exact immutable failure artifacts before coding.

### Architecture status

The common reasoning layers are already implemented:

```text
Verified packet
→ Free Analyst
→ Synthesis Validator
→ Adaptive Renderer
→ Hard Validators
→ deterministic fallback
```

The next major layer is market-specific evidence acquisition / normalization.

This task therefore does **not** wait for another KR natural run before implementing the KR/US adapters.

---

# 0. High-level decision

Proceed now in this order:

```text
Stage A
KR valuation numeric-ref bounded repair
→ promote only this repair after immutable replay PASS

Stage B
KR/US structured market adapter implementation
→ common interface
→ market-specific data acquisition/normalization
→ shadow/replay validation

Stage C
KR/US research seed/source adapters
→ shared Open Research semantics
→ market-specific search/source hints only
→ shadow validation

Stage D
Combined KR/US immutable replay

Stage E
Conditional 2026-08-26 US live canary
→ only if runtime production research connector actually exists
   and every gate passes
→ otherwise structured adapter may be live,
   Open Research remains shadow
```

Do not delay adapter implementation merely because the first KR Free Analyst canary was not observed.

The valuation-ref defect is bounded and should be fixed independently.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-kr-valuation-ref-repair-and-kr-us-market-adapter-integration.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse origin/main
git rev-parse origin/codex/open-research-event-attribution-shadow
git rev-parse origin/codex/adaptive-renderer-selector-shadow
```

Then:

1. verify actual latest production main/operating
2. verify current canary state
3. commit/push this exact instruction as a docs-only instruction commit
4. record instruction path / commit SHA / version
5. use separate branches/worktrees for:
   - Stage A production repair
   - Stage B/C adapter implementation
6. no force push / history rewrite
7. do not merge shadow-only research code into production unless Stage E explicitly permits it

Recommended branches:

```text
codex/kr-valuation-numeric-ref-repair
codex/kr-us-market-adapters
```

---

# 2. Hard prohibitions

Do NOT:

- weaken numeric/semantic validators
- remove safe valuation facts just to avoid the error
- enable full Free Analyst cohort
- change canary total above 3
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change Macro temporal rules
- change price/RR ownership
- change valuation basis rules
- fabricate KR/US breadth
- fabricate market-wide flow
- use stock-level quantity against market-wide monetary flow
- add a paid research/news API
- invent a fake production search provider
- hard-code Samsung / SK hynix / specific US tickers
- manually run natural KR/US production
- manually send Telegram
- mutate production DB during replay
- activate Open Research live merely because shadow research works

---

# Stage A — KR SK hynix Valuation Numeric-Ref Bounded Repair

# 3. Root-cause trace

Trace the exact natural failure path:

```text
safe current PBR Fact
safe historical PBR / historical valuation Fact
        ↓
valuation evidence registry / claim catalog
        ↓
AI candidate evidence view
        ↓
numeric_fact_ref declaration
        ↓
validator
```

Verify why:

```text
s000660_val_pbr:valuation:current
s000660_val_hist_pb:valuation:current
```

were referenced but not declared/resolvable.

Classify root cause:

```text
A. safe valuation Fact omitted from claim catalog
B. ref namespace mismatch
C. historical/current ownership mapping mismatch
D. candidate template emitted unsupported ref
E. other — document exactly
```

---

# 4. Repair principle

If the valuation facts are actually safe and already used by deterministic fallback:

repair:

```text
safe Fact
→ deterministic declaration/catalog
→ candidate ref
→ validator resolution
```

Do NOT:

```text
disable PBR
remove historical valuation
allow undeclared refs
permit wildcard valuation refs
```

---

# 5. Valuation ownership contract

Every declared valuation ref must preserve:

```text
metric
current / historical
price date
denominator basis
period/horizon
security basis
currency where applicable
source/provenance
```

Examples:

```text
current PBR
historical PBR distribution / historical position
```

must remain distinct.

Do not bind historical context as `current`.

---

# 6. Stage A negative controls

Required:

```text
safe declared current PBR
→ allowed

safe declared historical PBR context
→ allowed

undeclared valuation ref
→ reject

current metric using historical ownership
→ reject

PBR without safe BVPS/security basis
→ reject

provider-only multiple reversed into BVPS
→ reject
```

---

# 7. Immutable KR replay

Use the exact 2026-08-25 natural KR packet that produced the failure.

No provider recollection.

Target:

```text
pre-repair valuation ref errors = 2
post-repair valuation ref errors = 0

AI candidate hard errors = 0
Free Analyst entry reachable
Adaptive Renderer reachable
canary selector reachable
```

Do not send.

---

# 8. Stage A promotion

If Stage A passes:

- full tests
- Ruff
- `git diff --check`
- Knowledge/Chart parity
- Public Action/schema unchanged
- implementation SHA Actions PASS
- clean fast-forward to main
- sync operating
- restart only thesis-monitor API if imported runtime code changed
- `/health` PASS
- final main Actions PASS

Keep:

```text
FREE_ANALYST_ADAPTIVE_CANARY = ENABLED_PENDING_NATURAL
FULL MODE = OFF
limits = 1 / 2 / 3
```

Set:

`KR_VALUATION_NUMERIC_REF_REPAIR = DEPLOYED_PENDING_NATURAL`

Do not wait for another KR natural run before starting Stage B/C.

---

# Stage B — Common Market Adapter Interface

# 9. Purpose

The Common AI Core should not know how each market obtains:

- index
- breadth
- sector context
- market-wide flow
- session metadata
- official-market event context

Create a common typed interface.

Suggested conceptual contract:

```text
MarketContextAdapter
  market
  session
  cutoff

  get_index_context()
  get_breadth_context()
  get_sector_context()
  get_market_flow_context()
  get_session_context()
  get_official_event_sources()
  normalize()
```

Exact names may follow repository style.

---

# 10. Common normalized market context

Target common object:

```text
market
session
as_of
cutoff

indices[]
  symbol/name
  close
  return
  basis
  source_ref

breadth
  advancers
  decliners
  unchanged
  breadth_ratio if deterministically computed
  size_context
  availability

sectors[]
  name
  return
  source_ref

market_flows[]
  participant
  net_flow
  unit
  scope
  as_of
  source_ref

concentration[]
  metric
  deterministic inputs
  result
  unit
  limitations

session_context
  premarket / regular / after-hours / close
  market calendar ref

data_gaps[]
```

Never fill unavailable fields.

---

# 11. Deterministic calculations only

The adapter may deterministically compute relations such as:

```text
advancers / (advancers + decliners)
equal-weight vs cap-weight spread
sector-relative spread
top-N concentration
```

only when exact compatible inputs exist.

Persist:

```text
formula
input refs
unit
date/scope
result
```

AI must not perform these calculations.

---

# Stage B-KR — Korean Market Structured Adapter

# 12. KR structured source priority

Use existing/free structured sources in this order where supported:

```text
KRX / exchange
existing KR price provider
existing investor-flow provider
OpenDART for issuer official facts
existing official/statistical sources
```

Do not scrape news for structured market numbers if a structured source is available.

---

# 13. KR adapter target fields

Implement/acquire as available:

## Index

```text
KOSPI
KOSDAQ
close
return
as_of
```

## Breadth

```text
advancers
decliners
unchanged
KOSPI breadth
KOSDAQ breadth
```

## Size / sector

Where free structured data is available:

```text
large vs mid/small relative performance
sector returns
```

## Market-wide flow

Where compatible structured data is available:

```text
foreign
institution
retail
other official participant categories

unit:
value or quantity

market scope
as_of
```

## Stock flow

Reuse existing canonical 1D/5D/20D participant semantics.

---

# 14. KR flow compatibility

Do not calculate:

```text
stock quantity / market-wide KRW value
```

or any mixed-unit concentration.

If market-wide and stock-level values are available in compatible monetary units:
deterministic concentration may be computed.

Otherwise:

`Unknown`.

---

# 15. KR same-day publication timing

Preserve the existing KRX publication/readiness lifecycle.

The market adapter must distinguish:

```text
market session completed
provider publication pending
provider complete
```

Do not mark missing 16:05 provider rows as zero market flow.

Do not bypass the 08:05 next-morning evidence path.

---

# 16. KR domestic digest context

The adapter should make it possible for the KR digest to distinguish:

```text
headline index move
vs
market breadth
vs
large-cap concentration
vs
market-wide participant flow
```

Do not implement a new KR digest style yet unless it is required for adapter preview/replay.

The goal is to supply the missing structured context.

---

# Stage B-US — US Market Structured Adapter

# 17. US structured source priority

Use existing/free structured/official sources.

Possible categories:

```text
existing price/index provider
official exchange/index source where available
Fed / Treasury / BLS / BEA / official macro
SEC / issuer official filings
free public sector/breadth source if already supported
```

No paid API.

Do not invent a new source if no supported free provider exists.

---

# 18. US adapter target fields

## Index / style

As available:

```text
S&P 500
Nasdaq / Nasdaq 100
Russell 2000
SOX / semiconductor index
equal-weight index if safely available
```

## Breadth

As available:

```text
advancers
decliners
unchanged
broad-market breadth
```

## Sector

As available:

```text
sector index / sector ETF returns
```

## Session

Must distinguish:

```text
premarket
regular session
after-hours
```

## Macro structural fields

Reuse existing validated macro temporal facts rather than duplicate them.

---

# 19. US market flow policy

Do NOT imitate KR participant flows.

Unless a supported structured source exists, do not create:

```text
foreign
institution
retail
```

for US daily cash-equity market flow.

Potential future data types such as:

- ETF flows
- options positioning
- short interest
- 13F

must remain semantically separate and frequency-aware.

For v1:
Unknown is acceptable.

---

# 20. US session causality

The US adapter must preserve event/session timing.

Example:

```text
16:00 ET regular close
16:05 ET earnings release
```

The release cannot explain the regular-session move.

It may explain after-hours.

Persist:

```text
session role
event-time eligibility
```

---

# Stage C — KR/US Research Seed + Source Adapters

# 21. Principle

Do not create two different Open Research reasoning engines.

Keep common:

```text
Source validation
Entity validation
Time validation
Competing hypotheses
Negative evidence
Event Attribution
Free Analyst
Adaptive Renderer
```

Only market-specific:

```text
source hints
query seed vocabulary
official-source preference
session vocabulary
breadth vocabulary
```

---

# 22. KR research seed adapter

Provide hints such as categories, not conclusions.

Potential seed vocabulary:

```text
급락 / 급등
공시
주주환원
자사주
소각
유상증자
외국인 / 기관
수급
코스피 / 코스닥
업종
거버넌스
정책 / 규제
```

Official source hints:

```text
OpenDART
KRX
company IR
government/regulator
```

The Open Research Agent still generates actual queries dynamically.

---

# 23. US research seed adapter

Potential seed vocabulary:

```text
shares fall / rise
earnings
guidance
SEC filing
premarket
after hours
sector
peer
Treasury yields
macro release
analyst day
regulatory
```

Official source hints:

```text
SEC
company IR
Fed
Treasury
BLS
BEA
regulator/exchange
```

Again:
these are search hints, not hard-coded queries or conclusions.

---

# 24. Search result → structured fact verification

Market adapter rule:

```text
search discovers event / hypothesis
        ↓
if a structured or primary source can verify
        ↓
use structured/primary fact

if not
        ↓
retain as reported interpretation / secondary evidence
```

Do not use search as the primary source for a number when a structured source is available.

---

# 25. Runtime research connector audit — mandatory

Before any live Open Research activation, determine whether the production runtime has a supported free research/search connector.

Set:

```text
PRODUCTION_RESEARCH_CONNECTOR =
AVAILABLE / NOT_AVAILABLE / AMBIGUOUS
```

### AVAILABLE

Must prove:
- free
- source refs preserved
- bounded query budget
- no interactive human dependency
- production-safe timeout
- no secret leakage

### NOT_AVAILABLE

Do not invent one.
Open Research remains shadow.

### AMBIGUOUS

No live research canary.
Resolve separately.

This audit is critical.

---

# Stage D — Immutable Cross-Market Replay

# 26. KR replay

Use:
- the 2026-08-25 immutable KR natural packet
- repaired valuation refs
- KR market adapter data from stored/natural sources where available

No provider recollection for the mandatory baseline replay.

Report:
- common AI candidate
- market context
- canary eligibility
- digest preview
- stock preview

---

# 27. US replay

Use:
`2026-08-25-us-run-37-7e04812311c2`

Replay with:
- US market adapter
- Free Analyst
- Adaptive Renderer
- existing hard validators

Open Research sidecar may be included only for shadow comparison.

---

# 28. Cross-market adapter gates

Set:

```text
MARKET_ADAPTER_COMMON_CONTRACT = PASS / FAIL

KR_MARKET_ADAPTER =
PASS / PARTIAL / FAIL

US_MARKET_ADAPTER =
PASS / PARTIAL / FAIL

KR_US_REASONING_SCHEMA_COMMON =
PASS / FAIL

MARKET_CONTEXT_FACT_BOUNDARY =
PASS / FAIL

MARKET_CONTEXT_HIDDEN_ARITHMETIC =
0

MARKET_CONTEXT_UNIT_CONFLICT =
0

MARKET_CONTEXT_TEMPORAL_ERRORS =
0
```

`PARTIAL` is acceptable when free structured sources do not expose every breadth/flow field, provided missing values remain Unknown.

---

# 29. KR adapter value-add

Compare previous KR digest context with adapter-enhanced shadow preview.

Look for:

```text
KOSPI vs KOSDAQ distinction
breadth
sector/size concentration
market-wide flow
same-day publication caveat
```

Set:

```text
KR_MARKET_ADAPTER_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL
```

Do not force value where data remains unavailable.

---

# 30. US adapter value-add

Compare existing US market digest with adapter-enhanced shadow preview.

Look for:

```text
cap-weight vs broader market distinction
SOX / sector context
breadth
session-aware event context
macro + equity relationship
```

Set:

`US_MARKET_ADAPTER_VALUE_ADD = PASS / NO_MATERIAL_VALUE / FAIL`

---

# Stage E — Conditional 2026-08-26 US Live Canary

# 31. Goal

If every prerequisite passes tonight, use the next naturally scheduled US production run on `2026-08-26 KST` as the first live market-adapter canary.

Do not manually run production.

---

# 32. Structured adapter live eligibility

The structured US market adapter may be production-integrated if:

```text
US_MARKET_ADAPTER = PASS or safe PARTIAL
Fact boundary = PASS
unit conflicts = 0
temporal errors = 0
full tests/CI = PASS
fallback works
```

It must not block the packet if one structured field is unavailable.

Unavailable fields remain Unknown.

---

# 33. Open Research live eligibility

Open Research may become a live canary **only if**:

```text
PRODUCTION_RESEARCH_CONNECTOR = AVAILABLE

Open Research common shadow = PASS
US holdout = PASS
source provenance = PASS
entity/time = PASS
causality = PASS
negative evidence = PASS
Free Analyst integration = PASS
Adaptive Renderer = PASS
production dependency audit = PASS
```

If connector is `NOT_AVAILABLE` or `AMBIGUOUS`:

```text
OPEN_RESEARCH_LIVE_CANARY = BLOCKED_CONNECTOR
```

Do not fake it.

Tomorrow morning may still live-test:
- Free Analyst common canary
- structured US market adapter

while Open Research remains shadow.

---

# 34. Research canary must not increase AI exposure

If Open Research live canary is eligible:

it must fit **inside** the existing Common AI canary limit.

Existing total:

```text
market <= 1
stock <= 2
total <= 3
```

Research-enhanced messages do not create extra slots.

Additional research-specific limit:

```text
research-enhanced total <= 1 per run
```

So:

```text
AI-assisted total <= 3
of which research-enhanced <= 1
```

---

# 35. Research canary selection

Eligible only if:

```text
existing Free Analyst canary eligible
material research trigger exists
research sidecar validation PASS
source/entity/time PASS
causality PASS
negative evidence PASS
runtime-quality PASS
```

Suggested trigger classes:

```text
material price move
new official event
earnings/guidance
sector shock
unusual market breadth
thesis-sensitive event
```

No ticker hard-coding.

---

# 36. Research canary fallback

If research fails:

```text
research-enhanced candidate rejected
→ ordinary Free Analyst candidate if valid
→ otherwise deterministic fallback
```

Research failure must not block delivery.

---

# 37. Independent research kill switch

If Open Research canary is armed, require an independent control:

```text
OPEN_RESEARCH_CANARY = DISABLED
```

that leaves:
- Free Analyst canary
- deterministic fallback
- normal production delivery

untouched.

---

# 38. Tomorrow morning exact proof target

For the `2026-08-26` US natural run capture:

```text
packet
expected messages
actual messages

Free Analyst canary selected <= 3
research-enhanced selected <= 1

structured US market context used
research context used only if connector eligible

duplicates = 0
orphans = 0
exactly-once = PASS
receipt integrity = PASS

Fact mismatch = 0
unsupported numeric = 0
unsupported causality = 0
temporal violations = 0
hidden arithmetic = 0
external unsourced facts = 0
material information loss = 0
```

---

# 39. Tomorrow live message bundle

Create exact comparison:

```text
ACTUAL_LIVE_MESSAGE
DETERMINISTIC_FALLBACK
FREE_ANALYST_NO_MARKET_ADAPTER
FREE_ANALYST_WITH_MARKET_ADAPTER
RESEARCH_ENHANCED if eligible
```

Mark non-delivered versions clearly.

---

# 40. Do not wait for another KR natural proof before adapter work

This is an explicit project decision.

The common AI architecture is already replay-proven cross-market.

The KR canary was blocked by a bounded valuation ref defect.

Therefore:

```text
fix defect now
+
implement adapters now
```

is preferred to:

```text
wait another day
→ then start adapters
```

The next KR natural run remains useful as the user-visible canary proof, but it is not a prerequisite for writing the market adapters.

---

# 41. Promotion separation

Use separate promotion decisions.

## Stage A repair

May promote after bounded replay/full validation.

## Structured KR/US market adapters

May promote after:
- common contract PASS
- market adapter PASS/safe PARTIAL
- production dependency audit
- no change to public schema
- fallback-safe behavior

## Open Research

Do not promote unless runtime connector is genuinely available and live canary gates pass.

No "bundle all everything into main" shortcut.

---

# 42. Required architecture docs

Create/update:

1. `docs/architecture/MARKET_CONTEXT_ADAPTER.md`
2. `docs/architecture/KR_MARKET_CONTEXT_ADAPTER.md`
3. `docs/architecture/US_MARKET_CONTEXT_ADAPTER.md`
4. `docs/architecture/MARKET_RESEARCH_SEED_ADAPTERS.md`
5. `docs/architecture/PRODUCTION_RESEARCH_CONNECTOR_BOUNDARY.md`

Update:
6. `docs/architecture/COMMON_AI_CORE_V1.md`
   - market context as input, not reasoning fork

---

# 43. Required Stage A reports

Create:

1. `docs/reports/20260825-kr-valuation-numeric-ref-root-cause.md`
2. `docs/reports/20260825-kr-valuation-numeric-ref-repair.md`
3. `docs/reports/20260825-kr-valuation-numeric-ref-negative-controls.md`
4. `docs/reports/20260825-kr-run-valuation-post-repair-replay.md`

---

# 44. Required adapter reports

Create:

5. `docs/reports/20260825-market-adapter-common-contract.md`
6. `docs/reports/20260825-kr-market-adapter-source-audit.md`
7. `docs/reports/20260825-kr-market-adapter-replay.md`
8. `docs/reports/20260825-us-market-adapter-source-audit.md`
9. `docs/reports/20260825-us-market-adapter-replay.md`
10. `docs/reports/20260825-kr-us-market-adapter-comparison.md`
11. `docs/reports/20260825-market-adapter-unit-temporal-audit.md`
12. `docs/reports/20260825-market-adapter-value-add.md`

---

# 45. Required research-adapter reports

13. `docs/reports/20260825-kr-research-seed-adapter.md`
14. `docs/reports/20260825-us-research-seed-adapter.md`
15. `docs/reports/20260825-production-research-connector-audit.md`
16. `docs/reports/20260825-open-research-live-canary-readiness.md`

---

# 46. Required production/canary reports

If structured adapters are promoted / canary prepared:

17. `docs/reports/20260825-market-adapter-production-integration.md`
18. `docs/reports/20260825-us-20260826-live-canary-readiness.md`

After tomorrow natural run:
19. `docs/reports/20260826-us-market-adapter-natural-canary.md`
20. `docs/reports/20260826-us-market-adapter-sent-message-bundle.md`
21. `docs/reports/20260826-us-market-adapter-natural-gates.md`

If Open Research connector unavailable:
record `BLOCKED_CONNECTOR`, not failure.

---

# 47. Machine-readable summary

Create:

`docs/reports/20260825-kr-us-market-adapter-readiness.json`

Include:

```text
repository
kr_valuation_repair
common_adapter
kr_adapter
us_adapter
research_seed_adapters
production_research_connector
structured_production_readiness
research_live_readiness
canary
safety
next_action
```

---

# 48. Focused tests — valuation repair

Required:

- current PBR declared ref
- historical PBR declared ref
- undeclared ref rejected
- current/historical ownership mismatch rejected
- unsafe PBR basis rejected
- SK hynix immutable packet replay

---

# 49. Focused tests — common adapter

Required:

- missing data remains Unknown
- no default zero
- deterministic relation provenance
- unit compatibility
- date/scope compatibility
- market enum normalization
- session normalization
- KR/US common output schema

---

# 50. Focused tests — KR adapter

Required:

- KOSPI/KOSDAQ normalization
- breadth normalization
- publication-pending handling
- market-wide flow basis
- stock-level flow semantic preservation
- incompatible concentration blocked
- no residual participant invention

---

# 51. Focused tests — US adapter

Required:

- index normalization
- SOX/sector normalization where supplied
- breadth missing-data handling
- premarket/regular/after-hours
- post-close event cannot cause regular move
- no fake participant-flow semantics
- macro temporal facts reused, not duplicated incorrectly

---

# 52. Focused tests — research seed adapters

Required:

- seeds do not hard-code conclusions
- KR/US seed vocab differs but common research semantics remain same
- primary-source preference
- source normalization
- no ticker-specific logic
- runtime connector unavailable → live research blocked

---

# 53. Full validation

For every promoted production commit:

```text
focused tests PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action 0.4.5 unchanged
operationId 20/20 unique
schema 4 unchanged
implementation SHA Actions PASS
final main SHA Actions PASS
API /health PASS
worktrees clean
```

---

# 54. Readiness gates

Set:

```text
KR_VALUATION_NUMERIC_REF_REPAIR =
PASS / FAIL

KR_VALUATION_REPLAY =
PASS / FAIL

MARKET_ADAPTER_COMMON_CONTRACT =
PASS / FAIL

KR_MARKET_ADAPTER =
PASS / PARTIAL / FAIL

US_MARKET_ADAPTER =
PASS / PARTIAL / FAIL

KR_US_REASONING_SCHEMA_COMMON =
PASS / FAIL

MARKET_CONTEXT_FACT_BOUNDARY =
PASS / FAIL

KR_MARKET_ADAPTER_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

US_MARKET_ADAPTER_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

PRODUCTION_RESEARCH_CONNECTOR =
AVAILABLE / NOT_AVAILABLE / AMBIGUOUS

OPEN_RESEARCH_LIVE_CANARY =
READY_PENDING_US_NATURAL /
BLOCKED_CONNECTOR /
BLOCKED_VALIDATION /
OFF

STRUCTURED_MARKET_ADAPTER_PRODUCTION =
READY / DEPLOYED_PENDING_NATURAL / BLOCKED

OPEN_RESEARCH_PRODUCTION_INTEGRATION =
0 unless explicitly allowed by Stage E
```

---

# 55. Common-stack status after this task

Use one:

```text
COMMON_AI_CORE_V1 =
INTEGRATED_CANARY_PENDING_NATURAL /
CANARY_KR_LIVE_PASS_PENDING_US /
CANARY_CROSS_MARKET_LIVE_PASS

COMMON_MARKET_ADAPTER_V1 =
SHADOW_PASS /
PRODUCTION_PENDING_NATURAL /
LIVE_PASS

COMMON_OPEN_RESEARCH_V1 =
SHADOW_PASS /
LIVE_CANARY_PENDING /
BLOCKED_CONNECTOR
```

Do not claim Open Research live completion without a real production connector and natural evidence.

---

# 56. Severity

## P0

- wrong market/valuation fact
- wrong current/historical valuation ownership
- mixed-unit concentration displayed
- post-close event used as regular-session cause
- hidden arithmetic
- fabricated breadth/flow
- Trade AR leak
- duplicate Telegram
- exactly-once regression
- fake research provider
- Open Research enabled without provenance/time/entity validation

## P1

- valuation ref defect persists
- adapter produces wrong market/session semantics
- KR/US common schema diverges materially
- structured adapter blocks packet on partial data
- research live path lacks stable connector
- canary exceeds existing AI exposure limits
- fallback cannot recover from adapter/research failure

## P2

- free source does not provide a breadth field
- market-wide US participant flow unavailable
- KRX same-day publication pending
- research connector unavailable but structured adapter works
- minor digest wording
- low-value adapter context correctly omitted

---

# 57. Completion response — implementation stage

Return:

```text
INSTRUCTION_COMMIT = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...
TRACK_A_FINAL_MAIN = ...

ADAPTER_BRANCH = ...
ADAPTER_BASE = ...
ADAPTER_IMPLEMENTATION = ...
ADAPTER_REPORT_COMMIT = ...

KR_VALUATION_NUMERIC_REF_REPAIR = ...
KR_VALUATION_REPLAY = ...

MARKET_ADAPTER_COMMON_CONTRACT = ...
KR_MARKET_ADAPTER = ...
US_MARKET_ADAPTER = ...
KR_US_REASONING_SCHEMA_COMMON = ...

MARKET_CONTEXT_FACT_BOUNDARY = ...
MARKET_CONTEXT_HIDDEN_ARITHMETIC = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_TEMPORAL_ERRORS = 0

KR_MARKET_ADAPTER_VALUE_ADD = ...
US_MARKET_ADAPTER_VALUE_ADD = ...

PRODUCTION_RESEARCH_CONNECTOR = ...
OPEN_RESEARCH_LIVE_CANARY = ...

STRUCTURED_MARKET_ADAPTER_PRODUCTION = ...

FREE_ANALYST_ADAPTIVE_CANARY = ...
FREE_ANALYST_ADAPTIVE_FULL = OFF
CANARY_LIMIT = 1/2/3

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 58. Completion response — 2026-08-26 US live stage

After the natural US run, report:

```text
US_NATURAL_RUN = ...
US_EXPECTED_MESSAGES = ...
US_ACTUAL_MESSAGES = ...

FREE_ANALYST_AI_ASSISTED = ...
RESEARCH_ENHANCED_DELIVERED = ...

US_MARKET_ADAPTER_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

OPEN_RESEARCH_US_LIVE_CANARY =
LIVE_PASS / FAIL / NOT_OBSERVED / BLOCKED_CONNECTOR

DUPLICATES = 0
ORPHANS = 0
EXACTLY_ONCE = PASS
RECEIPT_INTEGRITY = PASS

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0

COMMON_MARKET_ADAPTER_V1 = ...
COMMON_OPEN_RESEARCH_V1 = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

---

# 59. NEXT_ACTION policy

If Stage A repair fails:

`NEXT_ACTION = KR_VALUATION_NUMERIC_REF_BOUNDED_REPAIR`

If repair passes but adapters fail:

`NEXT_ACTION = MARKET_ADAPTER_BOUNDED_REPAIR`

If adapters pass and research connector is unavailable:

```text
NEXT_ACTION =
WAIT_FOR_US_STRUCTURED_ADAPTER_NATURAL_CANARY
```

Open Research remains shadow.

If adapters pass and research connector is available + all research gates pass:

```text
NEXT_ACTION =
WAIT_FOR_US_MARKET_AND_RESEARCH_NATURAL_CANARY
```

After successful US live proof:

```text
NEXT_ACTION =
KR_MARKET_ADAPTER_NATURAL_PROOF
or
OPEN_RESEARCH_SELECTIVE_EXPANSION_DECISION
```

depending which layers actually reached production.

---

# 60. Final principle

Do not wait passively for another KR canary merely to start the next engineering phase.

The correct sequencing is:

```text
bounded defect
→ fix immediately

common reasoning core
→ already integrated

market-specific evidence acquisition
→ implement now

live exposure
→ only after replay and connector validation
```

The desired architecture is:

```text
KR/US structured adapters
        ↓
Common normalized market context
        ↓
Verified production packet
        ↓
Free Analyst
        ↓
Adaptive Renderer
        ↓
hard validators
        ↓
bounded live canary

Optional Open Research:
market-specific seeds/source adapters
        ↓
common Event Attribution
        ↓
Free Analyst
        ↓
same Adaptive/validator path
```

KR and US should differ in **how evidence is acquired**, not in how the investment analysis is reasoned.

Use tonight to finish the adapters and bounded repair.

Use the next US natural morning to observe live behavior if and only if every production gate is actually satisfied.
