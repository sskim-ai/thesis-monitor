# Thesis Monitor Project Handoff

This document is a canonical continuation point for the AI-assisted monitoring project. Read it
with [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md), [project-state.json](project-state.json), and
[NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md) before changing runtime policy, Knowledge,
validation, delivery, or Scheduled Tasks.

## Project Purpose

Thesis Monitor maintains an investment thesis from verified backend facts. The deterministic engine
owns official state. Codex adds a bounded interpretation of the same facts, and Telegram delivers one
integrated market-and-stock set only after validation. The system is research monitoring, not order
execution or an autonomous investment adviser.

## Current Versions

| Component | Contract |
|---|---|
| Branch | `codex/phase-8-5-1-runtime-current-price-rr-repair` (experimental; `main` unchanged) |
| Official assessment | Deterministic `ThesisAssessment` |
| AI mode | `shadow` |
| Analysis policy | `daily-review-v3.10` |
| Output schema | `4` |
| OHLCV structure | `ohlcv-structure-v2` |
| Investment Knowledge | `3.0` |
| Chart Knowledge | `1.0` |
| Pilot | `ai-assisted-pilot-v3`, persisted runtime KR 3/5 and US 3/5; US Day 3 is operationally counted but not human-reviewed here |
| Renderer | `ai-assisted-pilot-renderer-v3` |
| Public Action | `0.4.5`, operationId 20/20 |
| Production Assist | Disabled |
| Financial currency safety | Missing/empty is `unknown`; unsupported units are prose-denied |
| Security identity | `security-identity-v2` |
| Financial quality | `financial-quality-taint-v2` |
| KR financial lineage | Production remains legacy; Phase 8.1.1 archive-only recovery proves `financial-lineage-v2` with recent formal rows |
| Delta-first rendering | `delta-first-rendering-v1` |
| Semantic decision hierarchy | `semantic-scope-and-decision-hierarchy-v1`, `decision-material-delta-v1` |
| Valuation context wording | `valuation-context-wording-v1` |
| Industry reasoning | `industry-specific-reasoning-v1` |
| Runtime packet completeness | current-price RR preflight v1; natural proof pending |
| Runtime quality | `runtime-message-quality-v1`, receipt `runtime-message-quality-receipt-v2` |

Resolve the deployed commit with `git rev-parse HEAD`; a file inside a commit cannot contain that
commit's own final hash. The machine-readable state records `HEAD` plus the last verified base.

## Architecture

```text
Data providers
  -> deterministic normalization, validation, and calculation
  -> official ThesisAssessment
  -> immutable AI Review packet
  -> per-packet claim UUID, lease, flock, and fencing
  -> Investment Knowledge v3 + Chart Knowledge v1
  -> Codex structured review
  -> deterministic numeric-fact binding and canonical formatting
  -> schema, fact, semantic, routing, and grounding validator
  -> integrated market + stock renderer
  -> one AI-assisted Telegram set
     OR one deterministic fallback set
  -> exact immutable archive
```

See [AI_ASSISTED_MONITORING.md](architecture/AI_ASSISTED_MONITORING.md) for ownership boundaries.

## Roles

### Custom GPT

Custom GPT provides interactive initial research and monitoring using Investment Knowledge v3 and
the public Action contract. The repository upload artifact must remain byte-identical to the
canonical Investment Knowledge. Custom GPT Instructions take precedence if a conflict is found.

### Deterministic Backend

The backend collects facts, verifies identity and provenance, calculates financial, valuation,
market, supply, and chart values, and persists the official assessment. It remains the source of
truth for status, warnings, invalidation, canonical numbers, and Telegram fallback content.

### Codex

Codex reads an immutable packet and routed Knowledge only. It connects verified facts into business,
valuation, price, supply, market-structure, and portfolio-transmission interpretations. It does not
browse, collect facts, calculate indicators, create targets, or mutate official state.

### Validator

The backend first resolves draft numeric fact references into canonical prose and schema-4 claims.
The validator then resolves every fact and prose path, enforces industry routing, rejects unsupported
numeric semantics, verifies exact display variants, and checks current claim and policy identity
before atomic promotion. Unknown semantic types and stale or absent facts fail closed.

### Telegram

Telegram is a delivery surface, not a source of truth. During Pilot, validated AI narrative is merged
with deterministic status and numbers. A session sends either the AI-assisted set or the stored
deterministic fallback, never both.
The renderer preserves validated prose and only assembles headings, ordering, escaping, and Telegram
length handling; user-facing terminology must be resolved before validation.

## Monitoring Lifecycle

Initial research establishes a thesis-version baseline. Daily monitoring evaluates only changes after
that baseline. A new thesis version creates a fresh baseline and cannot inherit prior price-state
transitions as today's delta. Fingerprints and warning lifecycles remain deterministic.

```text
Initial research -> baseline -> daily delta -> deterministic assessment -> optional AI interpretation
```

Every final assessment also stores `monitoring-state-v1` under `price_context`: current price
structure, registered-rule lifecycle, supply, valuation, peer availability, the previous final state,
and deterministic delta. This state evolves even when the official business thesis is unchanged.
See [MONITORING_STATE_LIFECYCLE.md](architecture/MONITORING_STATE_LIFECYCLE.md).

## Dual Knowledge

- [Investment Knowledge v3](knowledge/investment-thesis-analysis-monitoring-knowledge-v3.md) governs
  business, industry, earnings, valuation, expectations, macro, risk, and monitoring safety.
- [Chart Knowledge v1](knowledge/stock-chart-value-analysis-knowledge-v1.md) governs interpretation of
  backend-provided OHLCV structure, positioning, and new-observer versus holder context.
- The two documents stay separate. Chart examples never override Investment Knowledge safety or
  backend calculations.

Canonical precedence is:

```text
Backend verified fact/calculation
  > Investment Knowledge v3 safety
  > OHLCV Analyst validated output
  > Chart Knowledge interpretation
  > examples
```

## Industry Routing

Primary industry identity comes from verified company profile fields, not thesis keywords or daily
themes. Structured subtype may refine a broad industry. Themes, customer exposure, and macro links
are secondary. Ambiguous or uncovered profiles stay general/low confidence rather than being forced
into a specialized framework. Production code contains no ticker-specific classification override.

## Numeric Provenance

Every user-facing investment number must bind:

```text
backend fact -> fact_id -> field_path -> value/unit -> semantic_type
  -> exact text_ref -> exact displayed usage
```

The single semantic registry defines unit, labels, formatter, rounding, prose permission, and scope.
Unknown semantics fail closed. Same-number/different-meaning and cross-prose coverage are invalid.
Derived numbers are usable only when the backend has registered them as canonical facts.
Under `daily-review-v3.10`, Codex places `{{numeric:ref_id}}` and selects only the canonical fact,
field, and prose location. The backend owns the value, unit, semantic, source-aware label, display
format, and generated final claim. Legacy manual claims still validate, but the draft binding path is
the production contract. See [NUMERIC_PROVENANCE.md](architecture/NUMERIC_PROVENANCE.md).
Issuer earnings amounts never inherit security price currency. A missing or blank
`financial_currency` becomes `unknown`; the amount remains auditable but has no canonical display and
cannot bind into prose. A non-empty unsupported currency keeps its identity and is also prose-denied.
Currency-independent earnings percentages remain usable.
During Pilot, a market or stock with at least four prose-eligible anchors cannot pass with zero
numeric claims. Sparse packets remain exempt, and every used number still requires exact prose
grounding rather than a quota-driven list.

## OHLCV Structure

`ohlcv-structure-v2` calculates Wilder ATR14, Local-Pivot zones and boxes, an independent Major Swing
stream, tentative Elliott/Fibonacci context, structural invalidation, nearest-resistance risk/reward,
and internal chart state. Correctness constraints are documented in
[OHLCV_STRUCTURE_ENGINE.md](architecture/OHLCV_STRUCTURE_ENGINE.md).

The central boundaries are:

- Local Pivot is not Major Swing.
- Adjusted chart price is not unadjusted historical-valuation price.
- Chart invalidation is not thesis invalidation.
- Chart state is not a buy or sell command.

## Market Intelligence

`daily-review-v3.10` retains deterministic numeric binding and adds relational stock reasoning,
canonical label ownership, lineage-exact financial eligibility, and authoritative security identity.
Verified market facts become selected changes, market structure, verified
portfolio transmission, and next confirmation. Market context may be a tailwind or headwind but never
becomes company fundamental confirmation. Rates, FX, oil, sectors, and flows use distinct semantic
contracts. Details are in [MARKET_INTELLIGENCE.md](architecture/MARKET_INTELLIGENCE.md).

## Stateful Price And Peer Context

Registered thesis price rules remain immutable history. The user-facing price section first uses a
new transition, then current Strong/Medium dynamic zones, current-price RR/invalidation, and only then
a still-relevant registered rule. A crossed confirmation is never promoted to support automatically.

Peer valuation is deterministic and fail-closed. The current repository can only use same-date active
monitored assessments, explicitly labeled as a limited sample. At least three comparable peers are
required, and the median is primary. The 2026-08-14 active universe had no qualifying peer metric, so
no peer number was invented. See [PEER_VALUATION.md](architecture/PEER_VALUATION.md).

## Pilot Architecture

Pilot v3 activated at KR 0/5 and US 0/5; the persisted runtime count is KR 3/5 and US 3/5. The
2026-08-16 US session remains an exactly-once operational success but failed human-quality review.
The natural KR
packet `2026-08-16-kr-run-21-049f367f0274` is operationally counted exactly once as Day 3/5, while
its human-quality status is `failed`. Neither packet is currently eligible
as Production Assist evidence. The required task
contract is policy v3.10/schema 4/structure v2. A successful day requires Codex completion, validation
pass, complete AI-assisted delivery, required artifact verification, and a verified atomic
`archive-complete.json` marker. Only then is success recorded. Archive-only recovery reuses the
persisted payload without resending Telegram, and packet/date idempotency prevents duplicate counts.
Fallback days do not increment the counter. Earlier
Pilot cohorts remain history and are never rewritten.

The natural US packet `2026-08-17-us-run-22-217ce9f324b9` passed the operating validator, delivered
14/14, archived 13 required artifacts with `archive-complete.json`, and appears exactly once in Pilot
state. It advanced the operational US count to Day 3/5. Phase 8 did not review its investment-message
quality and does not mark it as Production Assist evidence.

The next natural KR packet `2026-08-17-kr-run-23-378ee562573e` was rejected before AI delivery
because POSCO Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis lacked the required
current-price RR Fact and numeric path. Rejected AI sends were zero and deterministic fallback
eligibility was preserved; the deterministic fallback later sent 8/8 at 17:10 KST. No completed AI
delivery or AI archive marker was recorded, so runtime remains KR 3/5 and US 3/5. This is a separate
packet/numeric-path and natural-live gap, not a Phase 8 retrospective mutation.

## Phase 8 Market Cross-Section

The experimental branch adds `market-cross-section-v1` without registering a new production provider.
Massive free-plan live probing confirms full US grouped daily and paginated reference access. The
2026-08-14 sample produced 5,461 eligible security-level rows after deterministic filtering and
same-ticker previous adjusted-close validation. Massive remains shadow until 08:05 KST completeness is
observed over normal weekday sessions.

Kiwoom OpenAPI+ documentation exposes multi-symbol and industry-index/change primitives, but there is
no configured Windows market gateway or KOA-verified production TR evidence. The provider therefore
remains `bridge_shadow` and rejects canonical collection unless efficient market-wide capability and
universe semantics are explicitly SUPPORTED. KRX remains the intended primary after API approval.
See [MARKET_CROSS_SECTION.md](architecture/MARKET_CROSS_SECTION.md) and the
[capability report](reports/20260817-phase8-massive-kiwoom-capability.md).

## Phase 8.1 KR Financial Lineage

The experimental Phase 8.1 branch changes new formal OpenDART collection to the full-financial-
statement API and persists exact field occurrences under `financial-lineage-v2`. Filing period,
amount period, comparison period, CFS/OFS basis, account, source type, currency, and correction
identity remain distinct. Direct amounts can remain usable when only a growth comparison is unsafe.

The immutable operating DB copy predates this contract: its active KR cross-section has no v2 rows
and retains `fs_div=unknown` for most latest formal filings. Phase 8.1 does not infer or backfill those
rows. It records 60 persisted source-value cells across the requested 119-cell matrix and zero safe
historical v2 promotions. SK hynix denied earnings and dependent valuation remain denied.

Massive remains shadow-only. The adjusted grouped volume is explicitly audit-only because split
adjustment can produce decimal volume, and `close * adjusted volume` is not official turnover.
Reference metadata may be reused for one trading day. Exact 08:05 KST readiness remains
`NOT_YET_OBSERVED`; the normal-day 3-5 session telemetry requirement is still open. See
[the Phase 8.1 financial report](reports/20260817-phase8-1-kr-financial-lineage-validation.md) and
[Massive readiness report](reports/20260817-massive-0805-shadow-readiness.md).

## Phase 8.1.1 Authoritative Financial Recovery

Phase 8.1.1 supplies the missing official source rows without touching production history. It reads a
consistent operating-DB copy, discovers the latest formal filing and correction chain, re-requests
both `fnlttSinglAcntAll` CFS and OFS scopes, and stores sanitized raw responses in an ignored cache.
The field selector uses exact taxonomy/account identity first, rejects multiple occurrences, and
uses OFS only when that field has no CFS occurrence. Current and prior-year quarter occurrences are
separate canonical lineages; growth is available only when basis, account, duration, source type,
and currency match.

The seven active KR tickers returned 1,818 CFS and 1,291 OFS rows from seven latest formal filings.
The archive-only cross-section recovered 37 safe direct Facts: 17 income-statement amounts, five
operating margins, six inventory Facts, plus balance-sheet fields. Seventeen same-quarter YoY Facts
passed exact comparison lineage and three remained withheld. SK hynix's revenue, operating income,
and net income remain denied because the existing critical profitability conflict was not resolved
merely by finding a formal source row.

Interim OCF entered XBRL fallback for all seven filings because its structured column does not prove
single-quarter versus cumulative duration. No XBRL occurrence had a unique exact period, unit, and
statement-basis match, so OCF promotion is zero. Twenty-eight exact PPE/intangible CAPEX component
candidates remain audit-only and none are aggregated; FCF remains unavailable. The cold-cache run
used 29 provider calls. Final reproducibility reused seven XBRL archives and made 22 calls. The five
representative archive-only messages all pass automatic numeric binding with no manual, rejected,
or formatting result. Human quality remains pending Work review.

See the [readiness report](reports/20260817-phase8-1-1-authoritative-financial-recovery.md),
[full audit](reports/20260817-phase8-1-1-authoritative-financial-recovery-audit.json), and
[persisted Before / recovered After Preview](reports/20260817-phase8-1-1-kr-financial-preview.md).
No main merge, operating DB write, Telegram send, assessment rewrite, archive rewrite, or Pilot
mutation occurred.

## Phase 8.1.2 Human Quality Review

Phase 8.1.2 preserves the engineering result but places investment-message quality on HOLD. Across
Samsung, POSCO Holdings, Hyundai Glovis, Korean Re, and SK hynix, 17 of 25 message-eligible recovered
Facts are used with numeric provenance and no unsafe leakage. The portfolio score is 7.4/20.

The limiting evidence is structural: each archived AFTER is a financial-only recovery payload, not
a complete runtime-rendered stock message. It does not preserve the price, supply, valuation,
observer/holder, Unknown, or next-check sections needed to judge relational investment analysis.
Data Recovery and Safety are PASS; Investment Message Quality and main readiness are HOLD.
Production Assist evidence eligibility remains false. See the
[human review](reports/20260817-phase8-1-2-kr-financial-human-review.md) and
[verbatim Preview](reports/20260817-phase8-1-2-kr-before-after-preview.md). At that point the
recommended order was Phase 8.4 then Phase 8.5, both of which are now represented by later sections.

## Phase 8.4 Delta-First Full Messages

Phase 8.4 closes the financial-only evidence gap on
`codex/phase-8-4-delta-first-integrated-renderer`. Using the same immutable KR Day 3 context and the
Phase 8.1.1 recovery artifact, it produces five complete schema-4 stock reviews and renders them
through the existing production stock renderer. A deterministic materiality plan puts grounded
supply or price evidence first when the packet records that transition; on unchanged days it states
that no material event occurred and moves to current decision relevance. Redundant business and
priority-watch display sections are suppressed when their evidence is already integrated into the
core, next check, and unknown.

The archive-only set has 82 automatic bindings, zero manual/rejected/formatter/unresolved results,
nine valid occurrence-bound valuation interpretations, and no SK hynix denied earnings or PE
leakage. The full validator and runtime receipt pass with zero errors; final-language, zone, supply,
observer/holder, and repeat checks also pass. The five messages are 11.5% shorter by character and
23.3% shorter by section than their immutable full-message baseline. The review score is a
provisional 16.6/20, but the authoritative status remains `pending_work_human_review` and Production
Assist evidence eligibility is false. See [the exact Preview](reports/20260817-phase8-4-delta-first-full-preview.md),
[human-quality evidence](reports/20260817-phase8-4-human-quality-review.md), and
[the rendering contract](architecture/DELTA_FIRST_RENDERING.md). No main merge, deployment,
Telegram send, provider call, operating mutation, or Pilot mutation occurred.

## Phase 8.4.1 Semantic And Decision Hardening

Phase 8.4.1 on `codex/phase-8-4-1-semantic-decision-hardening` keeps the Phase 8.4 integrated
architecture and closes its four direct semantic blockers. Ordinary PER/PBR and own-history Facts
now carry listed-security scope, so company multiples cannot be rendered as memory, transport, or
materials segment multiples. Denied financial families are fenced across qualitative claims, while
an exact Fact-bound denial explanation remains allowed.

The deterministic decision hierarchy no longer promotes mild supply divergence solely because it
changed most recently. Samsung and Hyundai Glovis move earnings/valuation and entry relevance ahead
of supply; SK hynix correctly retains supply as the best available delta because earnings are
denied. Safe decision-band history is retained for Samsung PBR, Hyundai Glovis PER, and SK hynix PBR.
Samsung's extreme Q2 values classify `VALID_AND_COHERENT` from exact CFS account, period, currency,
comparison, and formula checks; the audit makes no external plausibility guess.

The five corrected reviews use 86 automatic bindings and 12 typed valuation occurrences. Full
schema validation and the runtime receipt pass with no final-language or template errors. Average
characters rise 4.2% from Phase 8.4 while lines fall 1.3%. Work directly scored Samsung 17, POSCO
16, Hyundai Glovis 18, Korean Re 16, and SK hynix 17, averaging 16.8/20. It accepted the integrated
architecture and identified one follow-up contradiction in valuation context wording. Production
Assist evidence eligibility remains false. See the
[validation report](reports/20260817-phase8-4-1-semantic-decision-validation.md),
[semantic audit](reports/20260817-phase8-4-1-semantic-audit.md), and
[exact Preview](reports/20260817-phase8-4-1-semantic-decision-preview.md). Main remains unmerged and
no deployment, Telegram, provider, operating-state, or Pilot mutation occurred.

## Phase 8.4.1.1 Valuation Context Finalization

Phase 8.4.1.1 closes that follow-up on
`codex/phase-8-4-1-1-valuation-context-finalization`. The old fixed peer-gap fallback ignored whether
own-history context was already visible and could say “current multiple only” beside a historical
percentile. `valuation-context-wording-v1` now records current, history, peer, and forward
availability separately from actual use and selects an auditable wording class.

Samsung, Hyundai Glovis, and SK hynix resolve to `CURRENT_PLUS_HISTORY`; POSCO resolves to
`CURRENT_ONLY` because safe history was not selected for the current decision; Korean Re resolves to
`CURRENT_ONLY` because no safe history is available. All five draft references agree with actual
numeric bindings. The binder accepts 86 automatic references, 12 typed valuation occurrences, and
five valuation-context references with zero rejection. Full validator and runtime receipt pass;
valuation-scope violations, denied echo, unsafe history, and after-message contradictions are zero.
Average characters rise 1.1% from Phase 8.4.1, with no line or section increase.

This completes the Phase 8.4 message-intelligence foundation. The exact final Preview still requires
the user's merge decision; main and the operating checkout are unchanged, Production Assist remains
OFF, and this retrospective sent no Telegram or mutated no runtime state. See the
[final Preview](reports/20260817-phase8-4-1-1-final-preview.md) and
[Master Workflow v2](MASTER_WORKFLOW.md).

## Phase 8.5 Industry-Specific Investment Reasoning

Phase 8.5 on `codex/phase-8-5-industry-specific-reasoning` adds
`industry-specific-reasoning-v1` without changing Investment Knowledge, Chart Knowledge, schema 4,
or the Phase 8.4 renderer architecture. The contract routes from verified company taxonomy,
separates primary framework from secondary themes, records confidence and missing drivers, and
requires supporting Facts for causal claims. It rejects memory low-PER cheap claims, insurance
low-PBR cheap claims without ROE/capital, biotech PER forcing, EPC order-to-margin leaps, and
hyperscaler-theme promotion to company revenue.

Archive-only full messages pass both the full validator and runtime receipt for five KR and six US
representatives. KR binding has 86 automatic numeric references and 12 accepted industry references
with zero error; SK hynix denied earnings/PER leakage remains zero. The active immutable routing
audit covers 20 stocks: nine high-confidence specialized routes and eleven low-confidence general
fallbacks. MU and TSM remain broad `semiconductor`, while WULF remains `general`, because current
structured evidence does not prove the finer memory/foundry/HPC primary labels. Phase 8.5 is
therefore strong PARTIAL pending better taxonomy coverage and natural-live evidence. See the
[architecture](architecture/INDUSTRY_SPECIFIC_REASONING.md),
[audit](reports/20260817-phase8-5-industry-reasoning-audit.md),
[KR Preview](reports/20260817-phase8-5-kr-industry-reasoning-preview.md), and
[US Preview](reports/20260817-phase8-5-us-industry-reasoning-preview.md).

The separate natural KR packet `2026-08-17-kr-run-23-378ee562573e` rejected four stocks pre-send for
missing required current-price RR Facts/paths. Rejected AI sends were zero; deterministic fallback
eligibility was preserved and later sent 8/8 at 17:10 KST; Pilot stayed KR 3/5 and US 3/5. This is a
packet/numeric-path and natural-live gap, not a renderer or Phase 8.5 reasoning failure.

## Phase 8.5.1 Runtime Current-Price RR Repair

Phase 8.5.1 on `codex/phase-8-5-1-runtime-current-price-rr-repair` identifies the run-23 failure as
`CALCULATED_BUT_NOT_CANONICALIZED`. The runtime session helper treated 2026-08-17 as a regular KRX
weekday even though XKRX was closed for a substitute holiday. That made the valid 2026-08-14 chart
look stale. Monitoring state retained the calculated RR and required grounding, while stale-chart
Fact filtering correctly withheld its canonical Fact.

The repair uses XKRX/XNYS calendars to determine sessions and preceding completed sessions. It does
not change RR calculation, nearest-resistance selection, stale-data denial, grounding requirements,
the binder, validator, or renderer. Read-only run-23 reconstruction restores exact RR paths for
POSCO Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis; Samsung Electronics, Korean Re,
and SK hynix remain unavailable by contract. The original eight RR missing-path errors become zero.
Current-price RR packet completeness advances to PARTIAL; Natural Live Validation remains OPEN until
the next naturally scheduled KR session passes without this blocker. See the
[root-cause report](reports/20260817-runtime-current-price-rr-root-cause.md),
[validation report](reports/20260817-runtime-current-price-rr-repair-validation.md), and
[run-23 replay](reports/20260817-runtime-current-price-rr-run23-replay.md).

On 2026-08-15 the owning desktop environment verified all four local-project tasks, retained their
08:15/08:30/16:15/16:55 schedules, and migrated their exact prompts to v3.10 with
`security-identity-v2` and `financial-quality-taint-v2`. All four are ACTIVE,
target the live local operating checkout, use GPT-5.6 Sol with high reasoning, and preserve the US
Primary 300-second readiness wait. No duplicate standalone task was created.

| Market | Primary | Backup | Fallback deadline |
|---|---:|---:|---:|
| US | 08:15 | 08:30 | 08:40 |
| KR | 16:15 | 16:55 | 17:10 |

The US deterministic run and first KRX fetch start at 08:05. KRX-only retries run at 08:10, 08:15,
and 08:20; the packet then proceeds with both contracts, a verified partial pair plus caution, or a
compact unavailable caution. The 08:15 primary may poll backend packet readiness for five minutes.
Detailed recovery and single-delivery rules are in
[AI_ASSISTED_PILOT.md](operations/AI_ASSISTED_PILOT.md).

The 2026-08-14 US v3.6 output had zero numeric claims and its initial Telegram delivery failed. A
manual retry sent the messages before the v3.7 policy was adopted, so delivery cannot be undone; the
session is retained as a failed-quality live sample and does not count toward Pilot totals.

The 2026-08-15 US session completed under v3.8 before the v3.9 deployment: validator PASS, 14/14
AI-assisted messages sent, and archive completion. Runtime state therefore counts it as US Day 1/5.

The natural 2026-08-16 KR v3.10 packet `2026-08-16-kr-run-21-049f367f0274` passed validation,
delivered the market plus all seven active stocks 8/8, verified 13 required archive artifacts, and
wrote `archive-complete.json` before the exactly-once Pilot record. Runtime state therefore counts it
as KR Day 3/5. Work's direct review failed the persisted payload because it contains six Korean
numeric-postposition defects, supply-direction claims without matching visible actor/horizon numbers,
a repeated stock core-judgment template, financial amounts without a user-visible period basis, and
valuation conclusions without sufficient historical or peer evidence. The operational count is not
rewritten, but Production Assist evidence eligibility remains false. See
[the operational reconciliation](reports/20260816-third-natural-kr-v310-operational-reconciliation.md)
and [the Work human review](reports/20260816-third-natural-kr-v310-work-human-review.md), alongside
[the exact persisted preview](reports/20260816-third-natural-kr-v310-telegram-preview.md).
The later v3.9 same-packet retrospective was archive-only and did not change that count or resend it.
The `e2c9290` plain-language preview was also unsent experimental evidence. Broad renderer-side word
replacement was removed because it crossed the post-validation semantic boundary; the Daily Review
Skill remains responsible for avoiding internal analysis jargon in authored user prose.

The natural 2026-08-15 KR v3.9 Scheduled Task completed packet
`2026-08-15-kr-run-19-919a670464b4`: validator PASS, the market plus seven active stocks delivered
8/8, all required archive hashes verified, and `archive-complete.json` was written before the packet
was recorded exactly once. Runtime state therefore counts it as KR Day 2/5. Experimental v3.10
retrospectives did not send this payload or mutate the count. At that time a Preview label such as
KR Pilot 3/5 was only the next-success candidate; the later natural KR session documented above is
the event that actually advanced runtime state.

Phase 7.2 production integration then deployed code commit `5f3aa5c37848092bcccf74bbc917604bebae33d4`.
Authoritative SEC identity remediation changed exactly CORZ, GOOGL, HUT, IBM, SKHY, and WULF; a
second pass was a six-of-six no-op. An isolated post-remediation US packet passed binder and full
validation with 161 automatic bindings and no manual claims. GOOGL's clean valuation lineage was
restored, while SKHY remained an ADS with ratio 0.1 and its unverified current-security multiples
stayed withheld. Deployment and retrospective validation did not add a Pilot count.

The first natural v3.10 session was US packet `2026-08-16-us-run-20-6c15d0003955`. The automated
pipeline passed after one correction cycle, delivered 14/14 AI-assisted messages, verified 13/13
required archive hashes, wrote the completion marker before state, and recorded the packet exactly
once. Runtime therefore advanced US to 2/5. The required human message review failed because CRCL's
confirmation transition contradicted its packet delta, SKHY's prose incorrectly described its
verified ADS identity as unverified, and all 13 US stocks repeated a KR-style investor-flow horizon
frame. TSM and WRD also resolved to `unknown` identity despite the deployment cross-section recording
`verified_depositary`; their unsafe multiples remained withheld. No manual count correction was
made. See [the Live validation report](reports/20260816-first-natural-v310-live-validation.md).

Phase 7.2.7 keeps that operational count unchanged and adds deterministic validation for confirmation
transition direction, security identity versus valuation basis, and market-aware supply routing.
Its US correction passed automated gates, but human review found additional blocking label, zone,
identity-prose, RR comparison, and sentence-quality issues. Its KR regression also reused a v3.9
artifact from a closed 2026-08-15 KR session, so it is not current financial-quality acceptance
evidence. The report and Previews remain preserved as failed-review evidence.

Phase 7.2.8 supersedes that acceptance conclusion without changing production. Its isolated US
packet `2026-08-16-us-run-20-a48638e987ce` passes 171 automatic bindings and 14/14 logical messages.
Its fresh current-code KR packet `2026-08-14-kr-run-17-006189184b28` uses the latest eligible
completed after-hours session, passes 141 automatic bindings and 8/8 logical messages, and keeps all
SK Hynix denied earnings and dependent PE lineage out of prose. Both full validators report zero
errors; label, instrument, zone-role, postposition, identity, comparative, and repetition hard checks
report zero findings. TSM and WRD remain safely `unknown` because no authoritative identity cache
exists. The branch is not merged or deployed and both Previews still require direct human approval.
See [the Phase 7.2.8 readiness report](reports/20260816-phase7-2-8-human-review-safety-readiness.md).

Phase 7.2.9 now supersedes the Phase 7.2.8 automated acceptance conclusion on the experimental
branch only. The immutable KR Day 3 payload fails the new runtime gate with six particle errors,
actor/horizon supply claims without occurrence-level numbers, missing financial periods,
unsupported valuation judgments, and repeated reasoning skeletons. Corrected isolated packets
`2026-08-16-kr-run-21-27d84c4e9795` and `2026-08-16-us-run-20-53fa21541277` pass automatic binding,
the full validator, and `runtime-message-quality-v1`; their logical payload counts are 8 and 14.
The gate is now in the delivery path and its receipt binds packet, validated-output, and rendered-set
hashes before delivery eligibility. CORZ PBR and dependent historical PB are denied by
`valuation-coherence-v1`, RXRX uses relative volume rather than generic supply language, and KR
financial amounts carry verified amount-period labels. These corrected Previews remain
`pending_work_human_review`, are not Production Assist evidence, and are neither merged nor deployed.
See [the Phase 7.2.9 readiness report](reports/20260816-phase7-2-9-runtime-quality-readiness.md).

Work subsequently failed the Phase 7.2.9 corrected KR Preview for amount-period, RR-basis, and
valuation-interpretation defects; its US Preview remained unapproved. Phase 7.2.9.1 addresses those
blockers on `codex/phase-7-2-9-1-quality-blockers`. It separates filing period from field-level amount
period, gives current-price and support-entry RR distinct semantics, requires typed homogeneous
valuation evidence, and verifies the full runtime receipt file SHA before retry or delivery reuse.
Corrected isolated packets `2026-08-16-kr-run-21-5844682f15da` and
`2026-08-16-us-run-20-f9b252d77940` pass their deterministic validators and runtime gates. Both remain
preserved artifacts, but Work subsequently failed both Previews. The failures were missing
consolidated/separate statement basis, a denied PER qualitative bypass, final-text particle and
duplicate-label defects, internal implementation language, a MU relation/caution contradiction, and
receipt audit coverage that overstated its partial-delivery evidence. They are not Production Assist
evidence. See [the Work review](reports/20260817-phase7-2-9-1-work-human-review.md) and
[the Phase 7.2.9.1 readiness report](reports/20260817-phase7-2-9-1-readiness.md).

Phase 7.2.9.2 repairs those blockers on `codex/phase-7-2-9-2-human-quality-hardening`. It adds
`financial-statement-basis-v1`, exact occurrence-bound `typed-valuation-interpretation-v2`, a final
rendered-language gate, forward-period relation/caution consistency, and explicit pre-send versus
post-partial receipt-integrity states. Corrected isolated packets
`2026-08-16-kr-run-21-23491b3e8f73` and `2026-08-16-us-run-20-fb918a643ae6` pass automatic binding,
the full validator, and the runtime final-message gate with 8 and 14 logical payloads. Their human
quality remains `pending_work_human_review`; production main and the operating checkout are
unchanged. See [the Phase 7.2.9.2 readiness report](reports/20260817-phase7-2-9-2-readiness.md).

## Source Map

- Packet, claim, validation, grounding: `app/services/ai_review_service.py`
- Numeric draft binding: `app/services/numeric_provenance_service.py`
- Market facts and transmission: `app/services/market_intelligence_service.py`
- Numeric semantics: `app/services/numeric_semantic_registry.py`
- Chart structure: `app/services/ohlcv_structure_service.py`
- Monitoring state and peer context: `app/services/monitoring_state_service.py`
- Exchange-session eligibility: `app/services/market_session.py`
- Runtime packet preflight: `app/services/runtime_packet_completeness_service.py`
- Renderer and delivery: `app/services/ai_assisted_delivery_service.py`
- Industry routing and causal guardrails: `app/services/industry_reasoning_service.py`
- Skill: `.agents/skills/thesis-monitor-daily-review/SKILL.md`
- Runtime policy: `.agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md`
- Output schema: `.agents/skills/thesis-monitor-daily-review/references/output-schema.json`
- Pilot archive: `data/ai_review/pilot/history`

## Known Gaps

- Massive US breadth is implemented in shadow, but exact 08:05 KST readiness over 3-5 normal
  sessions is not yet established.
- KR market breadth is partial pending KRX approval; the Kiwoom Windows gateway is not configured.
- KR market-wide investor flow is unavailable, and constituent-level sector participation remains
  incomplete.
- Industry-specific causal reasoning contracts are implemented, but specialized structured routing
  covers 9/20 immutable active stocks; taxonomy and business-unit coverage remain partial.
- There is no broad point-in-time peer valuation provider. Limited active-universe comparisons fail
  closed unless at least three comparable peers pass all basis checks.
- OCF extraction is partial; CAPEX aggregation and FCF remain open.
- The persisted US count includes the 2026-08-16 operationally complete session whose human message
  quality review failed. Operational count and human approval remain separate; this packet is not
  Production Assist evidence.
- TSM and WRD lack authoritative production identity evidence. Their live `unknown` state and
  multiple withholding are correct until a separately approved identity ingestion.
- Natural KR run-23 failed pre-send on missing required current-price RR Facts for four stocks. The
  retrospective packet repair is verified and the packet/numeric-path gap is PARTIAL; a new natural
  KR session is still required to close it. Natural Live Validation remains OPEN.
- Production Assist remains disabled pending a separate decision after successful Pilot evidence.

Never fill data gaps with model knowledge. Add a deterministic fact, semantic contract, and tests
first.

## Milestones

1. Initial baseline and daily-delta isolation.
2. Fact sanitization, warning provenance, and treasury materiality.
3. Historical valuation basis and modeled-versus-consensus safety.
4. Notification ordering, deferred FIFO, and KRX morning gate.
5. Codex Shadow packet, claim UUID, lease, flock, and finalize fencing.
6. Knowledge v3 parity and verified company-profile routing.
7. Prose-level numeric provenance and fail-closed semantic registry.
8. Single-delivery AI-assisted Pilot with deterministic fallback.
9. Dual Knowledge and OHLCV structure v1/v2 correctness hardening.
10. Phase 6 market intelligence and portfolio transmission.
11. Phase 6.1 quantitative hard gate, required night-futures grounding, fast morning pipeline, and
    persisted Telegram delivery retry.
12. Phase 7 durable monitoring state, registered-rule lifecycle, dynamic-price grounding, and
    fail-closed peer valuation.
13. Phase 7.1 deterministic numeric provenance binding, canonical formatter and currency-basis
    hardening, machine correction context, and persisted fallback retry safety.

## Next Steps

1. Review the Phase 8.5 and Phase 8.5.1 evidence; decide main merge and shadow deployment separately
   from Production Assist.
2. Wait for the next natural KR session and verify current-price RR packet completeness, the full
   validator, runtime receipt, archive, and exactly-once behavior. If KRX approval is confirmed,
   report whether Phase 8.2A should be inserted before later roadmap work.
3. Preserve operational counts KR 3/5 and US 3/5 and retain natural run-23 as a rejected pre-send
   session without replay, counter edits, or archive rewriting.
4. Keep TSM/WRD identity `unknown`, fine-grained industry routes general where unproved, peer data
   unavailable where absent, and OCF/CAPEX/FCF gaps explicit.
5. Run 3-5 Massive weekday shadow captures at 08:05 KST and, after KRX activation, collect five
   KRX/Kiwoom reconciliation sessions before metric-level fallback.
6. Keep Production Assist disabled until natural full-message evidence passes direct human review
   and the user explicitly approves it.
