# thesis-monitor — Kiwoom KR Market Breadth + Market-Wide Investor Flow Integration v1
## ka20001 / ka20003 / ka10051 / ka10066, with deterministic reconciliation and KR digest replay

## Metadata

- Workstream: `KR_STRUCTURED_MARKET_CONTEXT_V1`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: approximately `22:47 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `FREE_STRUCTURED_SOURCE_PROBE → CANONICAL_INTEGRATION → SAME_DAY_REPLAY`
- Source policy: `FREE_ONLY`
- Primary new structured source: `Kiwoom REST API`
- Open Research production integration: `0`
- Free Analyst full mode: `OFF`
- Existing bounded AI canary: preserve `market 1 / stocks 2 / total 3`
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

### Expected current production main / operating

Use the actual latest safe `origin/main` and operating SHA.

The previously reported structured-data/quality-v2 main may already be newer than earlier SHAs.  
Do not force a hard-coded SHA without resolving the repository first.

### Goal

Fill the largest remaining KR market-context gaps with structured Kiwoom data:

```text
KOSPI / KOSDAQ
+ advancers / decliners / unchanged
+ large / mid / small context
+ sector context
+ market-wide investor flow
+ per-stock monetary investor flow
+ deterministic flow concentration where basis-compatible
```

Then replay the existing 2026-08-25 KR natural packet with the richer structured context and inspect the resulting KR market digest / Free Analyst messages.

Do not touch US acquisition in this task except regression.

---

# 0. Why this task now

Current Common AI Core / Market Adapter logic is sufficiently mature.

The KR market digest remains limited primarily because the packet lacks domestic structured market context.

Kiwoom official REST documentation exposes relevant TRs:

```text
ka20001  업종현재가요청
ka20003  전업종지수요청
ka10051  업종별투자자순매수요청
ka10066  장마감후투자자별매매요청
ka10063  장중투자자별매매요청 (optional / not required for v1)
```

This task must use them as structured sources, not as prose/news substitutes.

---

# 1. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-kiwoom-kr-market-breadth-market-wide-flow-integration.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating
2. verify existing Kiwoom auth/token provider code
3. verify there is no duplicate Kiwoom market adapter already doing the same work
4. commit/push this exact instruction as a docs-only instruction commit
5. implementation must be based on that instruction commit SHA
6. create a dedicated branch
7. no force push / history rewrite

Recommended branch:

`codex/kiwoom-kr-market-context-v1`

---

# 2. Hard prohibitions

Do NOT:

- expose Kiwoom access tokens
- log authorization headers
- add a paid API
- use article/news text for structured market totals
- assume numeric units not proven by docs/live reconciliation
- default missing API output to zero
- sum partial pagination as if complete
- mix KRX-only and integrated KRX+NXT basis silently
- mix stock quantity with market-wide monetary flow
- invent foreign/institution/retail market totals
- infer other-participant identity from residuals
- let AI calculate concentration
- enable Open Research in production
- increase Free Analyst canary limits
- enable full mode
- enable Trade AR
- manually send Telegram
- manually run normal KR production
- mutate production monitoring/assessment state during replay

---

# 3. Official TR contract audit — mandatory before implementation

Create a source-contract report from the current Kiwoom official REST documentation and live schema behavior.

Audit at minimum:

## ka20001 — 업종현재가요청

Expected relevant request semantics:

```text
mrkt_tp:
0 KOSPI
1 KOSDAQ
2 KOSPI200

inds_cd examples:
001 KOSPI composite
002 large-cap
003 mid-cap
004 small-cap
101 KOSDAQ composite
```

Expected relevant response semantics include:

```text
cur_prc
pred_pre
flu_rt
trde_qty
trde_prica
trde_frmatn_stk_num
trde_frmatn_rt
upl
rising
stdns
fall
lst
```

Use this TR as a primary candidate for:
- current local index context
- current market breadth

Do not assume signed formatting semantics until normalized through existing Kiwoom parser conventions.

---

# 4. ka20003 — 전업종지수요청

Probe both:

```text
inds_cd = 001
inds_cd = 101
```

Expected list contains market/style/sector index rows with fields including:

```text
stk_cd
stk_nm
cur_prc
pred_pre
flu_rt
trde_qty
trde_prica
rising
stdns
fall
flo_stk_num
```

Use this as a primary candidate for:

```text
KOSPI composite
large-cap
mid-cap
small-cap
KOSDAQ composite
available sector/style indices
sector/style breadth
```

Do not assume every returned row is a sector suitable for user-visible comparison.  
Classify row type deterministically.

---

# 5. ka10051 — 업종별투자자순매수요청

Treat this as the **primary candidate for direct market-/industry-level investor flow**.

Probe:

```text
KOSPI:
mrkt_tp = 0

KOSDAQ:
mrkt_tp = 1

amt_qty_tp = 0  # amount per official documentation
base_dt = 20260825 for historical/same-day controlled probe
stex_tp = 3     # integrated, if production market basis uses integrated KRX+NXT
```

Also probe `stex_tp=1` KRX-only where useful for reconciliation with KRX-only sources.

Expected participant fields include repository-equivalent:

```text
securities / financial-investment
insurance
investment-trust
bank
pension/fund components
other corporation
individual
foreign
native-treated-foreign
state
private fund
institution total
```

The first `종합(KOSPI)` / `종합(KOSDAQ)`-equivalent row is a candidate for the market aggregate.

Do not rely on row ordering alone.

Identify aggregate row by verified industry code/name semantics.

---

# 6. ka10051 unit validation — mandatory

The request distinguishes amount vs quantity, but user-visible units must be explicitly validated.

For each live probe persist:

```text
amt_qty_tp
raw numeric values
documented/requested mode
normalization unit
scale
market
date
stex_tp
```

Do not expose:

```text
외국인 -X억원
```

until the scale/unit conversion is proven.

Acceptable proof sources:

1. official Kiwoom unit metadata if available in current repo/docs
2. existing Kiwoom provider normalization already proven elsewhere
3. deterministic reconciliation to another trusted same-basis structured source

If scale remains ambiguous:

```text
market_flow.available = false
reason = unit_unverified
```

Fail closed.

---

# 7. ka10066 — 장마감후투자자별매매요청

Use as the **per-stock monetary-flow and market-total reconciliation source**.

Required controlled probes:

```text
KOSPI:
mrkt_tp = 001

KOSDAQ:
mrkt_tp = 101

amt_qty_tp = 1  # amount
trde_tp = 0     # net buy
stex_tp = 3     # integrated basis
```

Also probe KRX-only `stex_tp=1` if needed.

Response contains per-stock fields including:

```text
ind_invsr
frgnr_invsr
orgn
fnnc_invt
insrnc
invtrt
etc_fnnc
bank
penfnd_etc
samo_fund
natn
etc_corp
```

This TR is not assumed to provide a market-total row.

Use full pagination.

---

# 8. ka10066 pagination contract

Follow:

```text
response cont-yn
response next-key
```

until terminal.

Persist:

```text
page number
cont-yn
next-key hash/ref (not secret if ordinary cursor, but do not expose raw if sensitive)
row count
cumulative row count
duplicate stock codes
terminal state
```

Hard rules:

```text
pagination incomplete
→ no market total
→ no concentration
```

No partial-sum promotion.

---

# 9. Duplicate / market-basis normalization

Kiwoom may expose KRX / NXT / integrated security representations.

Before aggregation:

- verify selected `stex_tp`
- normalize security identity
- detect duplicate representations
- do not double-count KRX/NXT/SOR forms
- preserve exact market basis

For v1, prefer one explicitly configured basis per final market context.

Recommended default if current production uses integrated market prices:

`stex_tp = 3`

but audit actual production basis before deciding.

---

# 10. ka10051 ↔ ka10066 reconciliation

For each market/participant where both are valid:

```text
ka10051 aggregate participant flow
vs
sum(all fully paginated ka10066 stock participant flow)
```

Compare:

```text
foreign
institution total
individual
other corporation
other supported categories
```

Do not demand exact equality until scale/rounding semantics are understood.

First classify discrepancy:

```text
EXACT
ROUNDING_COMPATIBLE
BASIS_DIFFERENCE
CATEGORY_TAXONOMY_DIFFERENCE
PAGINATION_GAP
UNIT_CONFLICT
UNRESOLVED
```

Only create an allowed tolerance after evidence demonstrates the provider rounding rule.

Do not invent a tolerance upfront.

---

# 11. Primary market-wide flow ownership

Preferred ownership after reconciliation:

```text
market-wide aggregate
→ ka10051 verified aggregate row

per-stock decomposition
→ ka10066 fully paginated rows
```

If ka10051 aggregate cannot be validated but ka10066 full sum can be validated independently:

a ka10066-derived market total may be used with explicit:

```text
derived_from_full_stock_universe = true
```

and full provenance.

Do not silently substitute.

---

# 12. Concentration calculations

Once same unit/date/session/market basis is validated, allow deterministic calculations such as:

```text
Top-N foreign net-selling share of KOSPI foreign net selling

Top-N institution net-selling share

monitored semiconductor names'
share of total market foreign selling
```

Required inputs:

```text
same participant
same monetary unit
same market
same date
same exchange basis
full market denominator
```

Formula must be deterministic and stored with input refs.

Do not calculate a percentage when the market denominator is:
- zero
- opposite sign in a way that makes the ratio misleading
- incomplete
- unit-incompatible

---

# 13. Concentration semantic guard

A concentration ratio is not automatically causal.

Example:

```text
Samsung + SK hynix = high share of foreign net selling
```

Fact:
concentrated flow.

Interpretation:
large-cap positioning pressure may have been important.

Do not automatically render:
`the decline was caused by foreign deleveraging`.

That remains Event Attribution / Free Analyst interpretation with appropriate boundary.

---

# 14. ka10063 — optional intraday support

Do not make ka10063 required for v1.

It may be probed for future:

```text
intraday investor flow
```

but:
- no production dependency
- no new blocking source
- no change to daily close monitoring semantics

Primary v1 objective is completed-session context.

---

# 15. KR canonical market-context model

Extend/reuse the existing KR Market Adapter to populate:

```text
kr_market_context:
  session_date
  exchange_basis
  as_of

  kospi:
    close
    return
    advancers
    decliners
    unchanged
    upper_limit
    lower_limit

  kosdaq:
    same

  size_style:
    large
    mid
    small

  sectors:
    validated rows only

  market_flow:
    kospi:
      foreign
      institution
      individual
      other_corporation
      supported_detail_categories
      unit
      source
    kosdaq:
      same

  flow_concentration:
    optional derived facts

  publication_state
  data_gaps
```

Do not create empty fake objects with zero-valued data.

---

# 16. Source priority within KR adapter

Preferred source ownership:

```text
Index / breadth:
Kiwoom ka20001 / ka20003
with KRX source retained as independent cross-check where available

Market-wide participant flow:
Kiwoom ka10051

Per-stock monetary flow:
Kiwoom ka10066

Existing stock-level 1D/5D/20D positioning:
existing canonical provider remains unchanged unless a separate migration is approved
```

Do not replace a proven existing stock-flow provider merely because Kiwoom is now available.

---

# 17. KRX publication timing coexistence

Do not remove the existing KRX 16:05 / next-morning telemetry.

New behavior:

```text
KRX same-day pending
+
Kiwoom same-day valid
→ market context may use Kiwoom
→ retain KRX pending telemetry separately
```

The two providers have different roles.

Do not mark KRX as failed simply because Kiwoom supplies data earlier.

---

# 18. Same-day live probe — 2026-08-25

Because this instruction is being executed on the evening of 2026-08-25 KST, perform a read-only live probe for the completed 2026-08-25 session if the API still returns that session.

Mandatory probe set:

```text
ka20001:
KOSPI 001
KOSDAQ 101

ka20003:
001
101

ka10051:
KOSPI amount integrated, base_dt=20260825
KOSDAQ amount integrated, base_dt=20260825

ka10066:
KOSPI amount/net/integrated full pagination
KOSDAQ amount/net/integrated full pagination
```

If current-time ka20001/ka20003 no longer unambiguously represent 8/25:
do not use them as historical 8/25 proof.

Use a historical endpoint or leave the historical breadth portion Unknown.

---

# 19. Historical retention / archive policy

Because some Kiwoom TRs may be current-session oriented, archive successful completed-session raw evidence every production day.

Persist sanitized raw/reference artifacts sufficient to reproduce:

```text
index
breadth
market flow
per-stock market-flow decomposition
```

Do not rely on being able to reconstruct every field later.

Use immutable archive refs / hashes.

---

# 20. Freshness and schedule policy

Audit actual Kiwoom availability after close.

Do not assume `16:05` is ideal.

Probe at bounded times, e.g. current existing production window plus optional read-only observers.

Determine:

```text
first reliable completed-session availability
```

from natural evidence over multiple days.

Do not change production schedule based on one day unless deterministic availability is already proven.

For immediate integration:
the adapter must fail closed if Kiwoom is not ready at the scheduled run.

---

# 21. Same-day replay input classes

Keep evidence classes separate:

## Natural packet evidence

Today’s immutable KR production packet.

## Supplemental Kiwoom structured evidence

Newly collected post-close Kiwoom market context.

Never rewrite the natural packet.

Construct only a replay object:

```text
immutable KR packet
+
supplemental Kiwoom context
```

---

# 22. KR enriched replay

Run the enriched object through:

```text
Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ hard validators
→ canary selector simulation
```

No Telegram.

Generate:

```text
SPARSE_PREVIOUS_MESSAGE
vs
KIWOOM_ENRICHED_MESSAGE
vs
DETERMINISTIC_FALLBACK
```

---

# 23. KR market-digest acceptance

The enriched digest should be able to use, when validated:

```text
KOSPI / KOSDAQ relative behavior
advancers / decliners
large / mid / small divergence
market-wide foreign / institution / individual flow
sector context
concentration when safely computed
```

The AI should be able to distinguish:

```text
broad risk-off / risk-on
large-cap concentration
rotation
mixed breadth
participant-flow concentration
```

but only to the strength supported by structured facts.

---

# 24. User-visible flow wording

Preferred examples of semantic shape:

```text
외국인·기관이 KOSPI 전체에서 순매도했고
매도가 일부 대형주에 집중됐다
```

only if:
- market-wide flow is validated
- per-stock monetary decomposition is validated
- concentration relation is safe

Do not show every participant number by default.

Prioritize:
- dominant market-wide direction
- unusual concentration
- whether breadth confirms or contradicts the headline index

---

# 25. Stock-level message interaction

Existing stock 1D/5D/20D positioning remains stock-specific.

Market context may add:

```text
today's stock flow
vs market-wide flow
```

only where same unit/basis or qualitative relation is supported.

Do not blend:
- stock-share flow
- market monetary flow

into one numeric comparison.

---

# 26. Message Quality v2 regression

Do not start another broad prompt rewrite.

Use the current quality-v2 logic.

Check whether richer Kiwoom evidence naturally improves:

```text
KR market digest
SK hynix
Hanwha Aerospace
Samsung Electronics if monitored/current
```

If the enriched context exposes one narrow quality issue:
log it.

Do not widen scope unless P0/P1.

---

# 27. Open Research relationship

Open Research remains production OFF.

However, this structured Kiwoom context becomes future deterministic evidence for Event Attribution.

Future shape:

```text
Kiwoom breadth / market flow / concentration
+
Open Research company/news evidence
→ competing hypotheses
```

Do not integrate Open Research in this task.

---

# 28. Production integration gate

Set:

```text
KIWOOM_KR_MARKET_CONTEXT =
PASS / PARTIAL / FAIL
```

Production integration is allowed if:

- auth/provider integration is stable
- missing fields fail closed
- index/breadth semantics valid
- market-flow unit valid
- pagination complete for any derived total
- no unit conflicts
- no duplicate security counting
- adapter failure does not block packet
- full tests / CI PASS

Safe PARTIAL may be integrated if useful fields are valid and unavailable fields remain Unknown.

---

# 29. Market-wide flow support status

Set separately:

```text
KR_MARKET_WIDE_INVESTOR_FLOW =
PASS / PARTIAL / BLOCKED_UNIT / BLOCKED_RECONCILIATION / FAIL
```

PASS requires at least:

```text
KOSPI aggregate:
foreign
institution
individual

KOSDAQ aggregate:
foreign
institution
individual

validated unit / scale
validated date/session
validated market basis
```

Other participant categories may be secondary.

---

# 30. Concentration support status

Set:

```text
KR_MARKET_FLOW_CONCENTRATION =
PASS / NOT_READY / FAIL
```

PASS requires:
- ka10066 full universe complete
- market aggregate denominator valid
- same unit/basis
- deterministic relation provenance

Do not block market-wide-flow PASS if concentration remains NOT_READY.

---

# 31. Sector / size support status

Set:

```text
KR_SECTOR_SIZE_CONTEXT =
PASS / PARTIAL / FAIL
```

At minimum evaluate:

```text
KOSPI large
KOSPI mid
KOSPI small
KOSDAQ composite
```

plus available sector rows from ka20003.

---

# 32. Cross-provider reconciliation

Where KRX provides same-day or next-morning index/breadth:

compare to Kiwoom.

Classify:

```text
MATCH
ROUNDING_ONLY
SESSION_BASIS_DIFFERENCE
PUBLICATION_TIMING_DIFFERENCE
CONFLICT
```

Do not let a benign timing difference become a data conflict.

---

# 33. Negative controls

Mandatory tests:

### Missing Kiwoom response
→ Unknown, packet continues

### Pagination interrupted
→ no ka10066 market sum/concentration

### Duplicate integrated stock representation
→ no double count

### KOSPI data mapped to KOSDAQ
→ reject

### amount mode interpreted as shares
→ reject

### unknown scale rendered as KRW
→ reject

### stock quantity / market amount concentration
→ reject

### market foreign flow used to change business thesis
→ reject

### foreign selling concentration rendered as confirmed cause
→ reject without additional attribution support

### Open Research auto-enabled
→ reject

---

# 34. Positive controls

Mandatory:

### ka20001 KOSPI
valid same-session index + breadth
→ canonical market breadth accepted

### ka20001 KOSDAQ
→ separate canonical market breadth accepted

### ka10051 aggregate KOSPI
validated amount/unit
→ market-wide foreign/institution/individual accepted

### ka10066 full pagination
same basis
→ per-stock monetary decomposition accepted

### validated concentration
→ safe derived relation accepted

### KRX pending + Kiwoom valid
→ Kiwoom context usable, KRX remains pending telemetry

---

# 35. Focused tests

Add tests for:

- Kiwoom auth wrapper does not log token
- ka20001 request/response normalization
- ka20003 classification
- ka10051 KOSPI aggregate identification
- ka10051 KOSDAQ aggregate identification
- ka10051 amount/quantity mode semantics
- market-flow unit validation
- ka10066 pagination
- ka10066 duplicate security normalization
- ka10066 participant taxonomy
- ka10051 ↔ ka10066 reconciliation
- concentration math
- sign handling
- zero/opposite-sign denominator guard
- KRX vs Kiwoom reconciliation
- publication-pending coexistence
- adapter fail-closed
- packet continues on provider failure
- Free Analyst market context input
- no business-thesis mutation from flow
- canary limits unchanged

---

# 36. Full regression

Preserve:

- Common AI Core
- Free Analyst semantic ownership
- Message Quality v2
- KR valuation repair
- Inventory
- Trade AR OFF
- FCF
- existing stock 1D/5D/20D flow
- Macro temporal
- price/RR
- valuation
- exactly-once
- KRX role-target telemetry
- US adapter behavior
- Open Research production OFF

---

# 37. Full validation

Before production promotion:

```text
focused Kiwoom tests PASS
same-day live probe PASS/safe PARTIAL
KR enriched replay PASS
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

# 38. Architecture docs

Create/update:

1. `docs/architecture/KR_MARKET_CONTEXT_ADAPTER.md`
2. `docs/architecture/KIWOOM_KR_MARKET_CONTEXT.md`
3. `docs/architecture/KR_MARKET_FLOW_RECONCILIATION.md`
4. `docs/architecture/KR_MARKET_BREADTH.md`

Document:
- TR ownership
- basis/unit
- pagination
- fail-closed behavior
- KRX coexistence
- future Open Research use

---

# 39. Required reports

Create:

1. `docs/reports/20260825-kiwoom-tr-contract-audit.md`
2. `docs/reports/20260825-kiwoom-live-probe.md`
3. `docs/reports/20260825-kiwoom-ka20001-breadth-validation.md`
4. `docs/reports/20260825-kiwoom-ka20003-sector-size-validation.md`
5. `docs/reports/20260825-kiwoom-ka10051-market-flow-validation.md`
6. `docs/reports/20260825-kiwoom-ka10066-pagination-validation.md`
7. `docs/reports/20260825-kiwoom-market-flow-reconciliation.md`
8. `docs/reports/20260825-kiwoom-market-flow-concentration.md`
9. `docs/reports/20260825-kr-kiwoom-enriched-replay.md`
10. `docs/reports/20260825-kr-kiwoom-message-before-after.md`
11. `docs/reports/20260825-kr-kiwoom-production-readiness.md`
12. `docs/reports/20260825-kr-kiwoom-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-kr-kiwoom-production-readiness.json`

---

# 40. Exact message benchmark

Create:

`docs/reports/20260825-kr-kiwoom-exact-message-benchmark.md`

Include:

```text
KR MARKET DIGEST:
SPARSE_PREVIOUS
KIWOOM_ENRICHED
DETERMINISTIC_REFERENCE

SK HYNIX:
SPARSE_PREVIOUS
KIWOOM_ENRICHED
DETERMINISTIC_REFERENCE

HANWHA:
SPARSE_PREVIOUS
KIWOOM_ENRICHED
DETERMINISTIC_REFERENCE
```

If Samsung is in the actual monitored packet, include it too.

For each:
- exact input context fields
- new structured facts used
- interpretation added
- unsupported conclusions prevented

---

# 41. Market data table

Create:

`docs/reports/20260825-kr-kiwoom-market-data-table.md`

Include, if validated:

```text
KOSPI:
close
return
advancers
decliners
unchanged
large/mid/small returns

KOSDAQ:
close
return
advancers
decliners
unchanged

Market-wide flow:
foreign
institution
individual
other corporation
unit / basis

Top per-stock flow:
foreign top sellers/buyers
institution top sellers/buyers

Concentration:
only validated ratios

Sector:
top / bottom validated sector rows
```

No unitless user-facing amount values.

---

# 42. Production promotion

If all integration gates pass:

- promote Kiwoom KR market-context code cleanly to main
- sync operating
- restart only thesis-monitor API if required
- `/health` PASS
- final main Actions PASS
- worktrees clean

Keep:
- Free Analyst full mode OFF
- canary 1/2/3 unchanged
- Open Research production 0
- Trade AR OFF
- existing Pilot/governance unchanged

Set:

```text
KIWOOM_KR_MARKET_CONTEXT =
DEPLOYED_PENDING_NATURAL
```

---

# 43. Natural proof

Do not manually run KR production after promotion.

The next eligible KR natural production run should prove:

```text
Kiwoom market context naturally collected
→ packet context
→ Free Analyst / Adaptive
→ bounded canary
→ Telegram / receipt
```

If Kiwoom is unavailable:
normal packet must still complete with Unknown/fallback-safe context.

---

# 44. Gates

Set exactly:

```text
KIWOOM_TR_CONTRACT =
PASS / FAIL

KIWOOM_LIVE_PROBE =
PASS / PARTIAL / FAIL

KR_INDEX_BREADTH =
PASS / PARTIAL / FAIL

KR_SECTOR_SIZE_CONTEXT =
PASS / PARTIAL / FAIL

KR_MARKET_WIDE_INVESTOR_FLOW =
PASS / PARTIAL / BLOCKED_UNIT / BLOCKED_RECONCILIATION / FAIL

KR_MARKET_FLOW_CONCENTRATION =
PASS / NOT_READY / FAIL

KIWOOM_KRX_RECONCILIATION =
PASS / PARTIAL / NOT_OBSERVED / FAIL

KR_KIWOOM_ENRICHED_REPLAY =
PASS / FAIL

KR_KIWOOM_MESSAGE_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

KIWOOM_KR_MARKET_CONTEXT =
PASS / PARTIAL / FAIL

PRODUCTION_READY =
YES / NO
```

---

# 45. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
FINAL_MAIN = ...
OPERATING = ...
REPORT_COMMIT = ...

KIWOOM_TR_CONTRACT = ...
KIWOOM_LIVE_PROBE = ...

KA20001_KOSPI = ...
KA20001_KOSDAQ = ...
KA20003 = ...

KA10051_KOSPI = ...
KA10051_KOSDAQ = ...
KA10051_UNIT = ...

KA10066_KOSPI_PAGES = ...
KA10066_KOSPI_ROWS = ...
KA10066_KOSDAQ_PAGES = ...
KA10066_KOSDAQ_ROWS = ...
KA10066_PAGINATION_COMPLETE = ...

KR_INDEX_BREADTH = ...
KR_SECTOR_SIZE_CONTEXT = ...

KR_MARKET_WIDE_INVESTOR_FLOW = ...
KR_MARKET_FLOW_CONCENTRATION = ...

KA10051_KA10066_RECONCILIATION = ...
KIWOOM_KRX_RECONCILIATION = ...

KR_KIWOOM_ENRICHED_REPLAY = ...
KR_KIWOOM_MESSAGE_VALUE_ADD = ...

FACT_MISMATCH = 0
UNIT_CONFLICT = 0
SESSION_DATE_CONFLICT = 0
DEFAULT_ZERO = 0
PAGINATION_PARTIAL_PROMOTED = 0
DUPLICATE_SECURITY_DOUBLE_COUNT = 0
HIDDEN_ARITHMETIC = 0
UNSUPPORTED_CAUSALITY = 0

FREE_ANALYST_CANARY = ...
FULL_MODE = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

KIWOOM_KR_MARKET_CONTEXT = ...
PRODUCTION_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_KR_KIWOOM_NATURAL_PROOF /
KIWOOM_BOUNDED_REPAIR /
UNIT_RECONCILIATION_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 46. Mandatory ZIP

Create:

`20260825-kiwoom-kr-market-breadth-market-flow-integration-bundle.zip`

Include all sanitized reports.

Never include:
- token
- auth header
- secrets

Compute/report SHA-256.

---

# 47. Severity

## P0

- wrong market/session
- wrong unit displayed
- fabricated market flow/breadth
- mixed-unit concentration
- incomplete pagination promoted as full market
- duplicate security double counted
- wrong participant identity
- production DB/Telegram mutation from replay
- secret/token exposure

## P1

- ka10051 aggregate incorrectly mapped
- ka10066 reconciliation materially unresolved but concentration still enabled
- Kiwoom failure blocks production packet
- KRX/Kiwoom basis confusion
- market flow is treated as business-thesis change
- concentration is rendered as proven cause

## P2

- ka10066 concentration not ready
- some sector rows unavailable
- KRX publication remains later than Kiwoom
- same-day source timing needs more natural observations
- optional detailed participant categories omitted
- normal safe PARTIAL acquisition

---

# 48. Final principle

The KR market digest should not be limited by missing deterministic market structure when a supported structured source already exists.

Use Kiwoom for:

```text
market index / breadth
market-wide investor flow
per-stock monetary investor flow
sector / size context
```

but validate:

```text
unit
session
exchange basis
pagination
participant taxonomy
```

before exposing any number.

The intended result is not “more numbers.”

It is the ability to distinguish safely:

```text
broad sell-off
vs
large-cap concentration
vs
rotation
vs
market-wide foreign/institution pressure
```

and give the Free Analyst enough verified KR evidence to explain the market without substituting US context or inventing a narrative.
