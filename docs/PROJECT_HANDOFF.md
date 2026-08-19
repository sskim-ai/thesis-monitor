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
| Branch | operating `main` contains Phase 8.5.4.2 code through `7e7ab5a...`; evidence is on `codex/phase-8-5-4-2-night-futures-calendar-repair`; peer/KRX experimental ancestry remains excluded |
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
| KR financial lineage | `financial-lineage-v2` is present in operating code; recovered historical Facts remain archive-only pending separate data promotion |
| Delta-first rendering | `delta-first-rendering-v1` |
| Semantic decision hierarchy | `semantic-scope-and-decision-hierarchy-v1`, `decision-material-delta-v1` |
| Valuation context wording | `valuation-context-wording-v1` |
| Industry reasoning | `industry-specific-reasoning-v1` |
| Runtime packet completeness | current-price RR preflight v1; 2026-08-18 natural live path PASS |
| Current price context | `current-price-context-v1` |
| Runtime specificity | `runtime-message-specificity-v1` |
| Runtime quality | `runtime-message-quality-v1`, receipt `runtime-message-quality-receipt-v2` |
| Night futures | `night-futures-session-basis-v1` CLOSED retrospective; holiday-aware preceding DAY lookup operating shadow, natural proof pending |

## Phase 8.3 Final State

The operating checkout now contains Phase 8.5.4 and remains unchanged with respect to Phase 8.3.
Phase 8.3 is
finalized as archive-only `SELECTIVE_OPTIONAL_CONTEXT` and excludes KRX implementation ancestry. Its
clean lineage starts from
`codex/integration-phase-8-3-peer-only`, which reconstructs the peer contract from operating main.
The original Phase 8.3 branch still contains KRX Git ancestry but no required KRX runtime import;
see [BRANCH_DEPENDENCY.md](BRANCH_DEPENDENCY.md).

Peer provider policy is `FREE_ONLY`. Paid/institutional providers and commercial inquiries are
`CLOSED_BY_POLICY`; earlier research remains reference history. Historical peer point-in-time data
is deferred, and forward consensus was not pursued after the trailing value gate.

The 2026-08-18 POC measured one `MEDIUM+` state among 20 active stocks: 5.0% raw and 6.67% among 15
economically meaningful subjects. KR is 0/7. US is 1/13 overall and 1/8 meaningful. TSLA alone has
nine exact automotive candidates and three positive/current PER issuers. Broad Technology, Media
and semiconductor groups remain `LOW`; MU does not receive a memory comparison from generic
semiconductor candidates. RXRX and HPC/SaaS/holding frameworks remain correctly suppressed or
not meaningful. TSM/SKHY ADR basis remains unsafe.

The original full Preview added one sentence inside TSLA's existing Valuation section, increased
that message 8.34%, created no section, and left the other ten representative messages
character-identical. The final wording calls the sample a same-automotive-classification `기초
비교군`, retains the same canonical numbers, and explicitly says business-model and growth-
expectation differences limit direct peer-premium interpretation. The final targeted replay is
1,319 to 1,448 characters, or +9.78%; the other ten messages remain unchanged.

The Phase 8.3 contract and selection/safety tooling pass, but 263 read-only requests produced one
visible `MEDIUM` subject. Broad runtime value is therefore `LOW_ROI`; daily broad collection,
provider expansion, forward consensus, historical PIT and coverage-driven taxonomy widening stop.
The engine, validators, audit artifacts and clean peer-only branch remain available for naturally
qualifying MEDIUM/HIGH contexts. This is not integrated, deployed or active operating behavior.

The next state is `WAIT_FOR_NATURAL_US_KR_PROOF`. Do not start a new feature before reviewing the
next natural messages. A critical failure takes priority as a targeted repair; otherwise the default
candidate is Cash Flow / Capital Efficiency Enrichment because OCF, CAPEX, FCF, ROIC, inventory,
working capital, cash conversion and segment economics remain more persistent decision gaps than
peer coverage.

Resolve the deployed commit with `git rev-parse HEAD`; a file inside a commit cannot contain that
commit's own final hash. The machine-readable state records `HEAD`, the promoted code SHA, and the
last verified base separately.

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

Registered thesis price rules remain immutable history. The shared deterministic
`current-price-context-v1` selector first uses current Strong/Medium dynamic zones, current-price
RR/invalidation and chart state, then only a still-relevant registered lifecycle. It calculates
nothing. A crossed confirmation is history, never a future trigger or automatically promoted support.

Peer valuation is deterministic and fail-closed. Operating code only uses same-date active monitored
assessments and still has no qualifying state. The free-source experimental path extends candidate
discovery without changing operating monitoring state. At least three comparable independent
issuers are required and the median is primary. Broad sector samples remain audit-only. See
[PEER_VALUATION.md](architecture/PEER_VALUATION.md). The free-source POC architecture and reports
remain on the preserved `codex/phase-8-3-finalization` experimental branch.

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
universe semantics are explicitly SUPPORTED. KRX Open API is approved but not yet integrated and
remains the intended primary.
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

This completes the Phase 8.4 message-intelligence foundation. At Phase 8.4.1.1 completion, the exact
final Preview still required the user's merge decision and the retrospective sent no Telegram or
mutated no runtime state. The implementation was subsequently promoted with Phase 8.5.2 while
Production Assist remained OFF. See the
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
See the
[root-cause report](reports/20260817-runtime-current-price-rr-root-cause.md),
[validation report](reports/20260817-runtime-current-price-rr-repair-validation.md), and
[run-23 replay](reports/20260817-runtime-current-price-rr-run23-replay.md).

## Phase 8.5.2 Operating Shadow Promotion

Phase 8.5.2 verified that the Phase 8.5.1 source is a linear 31-commit descendant of the prior main
and includes the required Phase 7.2.9.2, 8.0A, 8.1, 8.1.1, 8.1.2, 8.4, 8.4.1, 8.4.1.1, 8.5, and
8.5.1 implementation chain. `origin/main` and the clean operating checkout were fast-forwarded from
`aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` through code commit
`2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf` and final promotion commit
`a8ebb02753e28795f36dbf72c9deb3520f75ed44`. GitHub Actions run `32023730416` passed Test and Lint.

The API LaunchAgent was restarted from the configured operating checkout; `/health` returned
`ok`, US AI Review health remained valid, and KR health correctly preserved the rejected natural
run-23 state rather than rewriting it. Operating smoke tests passed 89/89. The four Codex Scheduled
Tasks remain ACTIVE at 08:15/08:30/16:15/16:55 KST, use GPT-5.6 Sol/high, policy v3.10/schema 4,
and target the same operating checkout. No Scheduled Task was manually run. The deterministic US/KR
and fallback LaunchAgents also target that checkout and report last exit code zero.

This promotion sent no Telegram, changed no Pilot state, performed no DB migration, and did not
enable Production Assist. AI mode remains shadow. Natural Live Validation and the RR path remain
OPEN/PARTIAL until a later naturally scheduled session exercises the promoted code. See the
[release validation](reports/20260817-phase8-5-2-shadow-release-validation.md) and
[operating state](reports/20260817-operating-shadow-state.md) reports.

## Phase 8.5.3 Natural Live Message Hardening

The promoted code ran naturally on 2026-08-18. US packet
`2026-08-18-us-run-24-487c07bde4e1` and KR packet
`2026-08-18-kr-run-25-23b5e31dc20e` had zero numeric/semantic hard errors, but AI output failed the
unchanged runtime quality gate. Deterministic fallback delivered 14/14 US and 8/8 KR; Pilot remained
KR 3/5 and US 3/5. The KR packet carried complete canonical current-price RR paths for POSCO
Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis, so the RR runtime path is `LIVE PATH
PASS`. Full natural AI-assisted delivery remains PARTIAL.

Phase 8.5.3 adds `runtime-message-specificity-v1` to plan company evidence, industry driver,
decision point, Unknown, and next check before prose. It suppresses repeated methodology instead of
randomly paraphrasing it. Immutable replay reduces literal/skeleton duplicates from 3/7 to 0/0 in
US and 5/7 to 0/0 in KR with no gate relaxation and both full validators PASS.

Deterministic fallback now consumes `current-price-context-v1`, the same canonical current structure
available to AI packets. Dynamic support/resistance, current-price RR, chart invalidation/state, and
registered lifecycle are selected without renderer calculation. Nine crossed confirmations that had
been rendered as future triggers fall to zero; fake RR and automatic support promotion remain zero.
See the [root-cause report](reports/20260818-phase8-5-3-natural-live-message-root-cause.md),
[validation report](reports/20260818-phase8-5-3-natural-live-message-validation.md),
[AI Preview](reports/20260818-phase8-5-3-ai-natural-live-hardening-preview.md), and
[fallback Preview](reports/20260818-phase8-5-3-fallback-price-parity-preview.md).

This evidence is archive-only. It sent no Telegram, ran no Scheduled Task, changed no Pilot/DB/
assessment/archive state. Phase 8.5.3.1 subsequently completed the final language/dedup hardening
and promoted the full chain. A natural AI-assisted US/KR delivery is still required. KRX Open API is
approved but not integrated; Phase 8.2A becomes the next analytical infrastructure task after this
live blocker is cleared.

## Phase 8.5.3.1 Language/Dedup And Shadow Promotion

The 2026-08-18 immutable packets were replayed with no new Facts or provider calls. US Korean
object-particle errors fell from six to zero; the KR malformed actor-flow phrases fell from two to
zero and incomplete predicates from one to zero. Exact watch/next overlap fell from 13 US stocks to
zero. The same current-price RR Fact had appeared three times in six KR messages; exact RR is now
owned by price positioning and the three-or-more count is zero. Both full validators, runtime
quality, final language, fallback parity, and denied-Fact controls PASS.

Implementation commit `e166aaf6a4c13f9009a3885737d3b48e34c895d5` passed exact-SHA GitHub
Actions run `32122804278` Test/Lint and was fast-forwarded to main and the clean operating shadow
checkout. The API was restarted and `/health` passed. US/KR AI health passed, operating focused
tests passed 154/154, and all four Codex automations remain ACTIVE at
08:15/08:30/16:15/16:55 KST on the operating checkout. No automation was manually run; Telegram,
Pilot, DB, assessment, and archive mutations were zero. Production Assist remains OFF and AI mode
remains shadow. See the [validation report](reports/20260818-phase8-5-3-1-language-dedup-validation.md),
[Preview](reports/20260818-phase8-5-3-1-language-dedup-preview.md), and
[promotion report](reports/20260818-phase8-5-3-1-shadow-promotion.md).

## Phase 8.5.3.2 Valuation Label Repair

RXRX's immutable valuation sentence contained valid values and typed provenance but displayed both
the current PBR `1.82x` and five-year historical median `3.28x` as `역사적 PBR`. The registry had
collapsed multiple comparison roles into one display label. `valuation-comparison-label-v1` now
retains the role from `field_path`, produces `현재 PBR`, `역사적 PBR 중앙값`, and
`PBR 역사적 백분위`, and rejects same-label/different-role collisions. RXRX and one additional
WULF legacy occurrence are repaired; portfolio collisions after replay are zero. Biotech
interpretation remains cash-runway/pipeline/milestone/dilution first.

Implementation `b3ad1ea82bdbd3fe003831d449b0dcaa7c6a2da2` passed GitHub Actions run
`32126079970`, full `1043` tests, API health, and 74 operating focused tests before targeted shadow
promotion. Telegram, Scheduled Task, Pilot, and Production Assist mutations were zero. See the
[validation](reports/20260818-phase8-5-3-2-rxrx-valuation-label-validation.md),
[Preview](reports/20260818-phase8-5-3-2-rxrx-valuation-label-preview.md), and
[audit](reports/20260818-phase8-5-3-2-valuation-label-audit.json).

## Phase 8.5.4 Natural Live Targeted Repair

Natural US packet `2026-08-19-us-run-26-cd80a8e4d373` produced no AI send. The deterministic
fallback delivered 14/14 messages with no duplicate and preserved the archive/receipt path. AI was
rejected for RXRX/WULF current-PBR semantic ownership and CORZ typed valuation occurrence errors.
This operational delivery is successful, but natural AI-assisted delivery and human/canonical
quality remain `PARTIAL`.

The market packet also exposed a canonical source-meaning error. KOSPI200 and KOSDAQ150 night
changes were calculated from NIGHT and DAY rows with the same KRX `BAS_DD`. KRX assigns the
overnight trading day by its T+1 06:00 end, so that same-date DAY close occurs later and is not the
reference session. The required 2026-08-19 NIGHT row was unavailable and the exact original raw
response was not archived. Retrospective output therefore suppresses both figures as
`UNAVAILABLE_BY_CONTRACT`; the user's approximate observation is not hard-coded.

`night-futures-session-basis-v1` now requires verified NIGHT identity, preceding DAY reference,
contract/date coherence, both prices, source record identifiers and payload SHA. Unknown session,
reference, contract, date or source evidence fails closed. Provider change fields are not trusted
without verified comparison semantics.

Visible current PBR now has one owner, `fields.price_to_book`; historical median and percentile
retain their historical semantics. The CORZ earnings-quality phrase receives exact typed coverage
without restoring unsafe earnings or book multiples. Fallback valuation caution is generated from
the metrics actually rendered, closing the GOOGL/HUT/RXRX/WULF/CORZ parity controls. Overlapping
selected support/resistance zones make RR unavailable; HUT 0.66x and WULF 0.42x are suppressed in
archive-only replay without moving the zones.

The repaired immutable replay has zero numeric-binding, typed-valuation and full-validator errors,
and `runtime-message-quality-v1` passes. Its validation sent no Telegram, ran no Scheduled Task, and
mutated no Pilot/DB/archive. It is now promoted to operating shadow; natural proof is still pending.
See the [root-cause report](reports/20260819-run26-natural-live-root-cause.md),
[night audit](reports/20260819-night-futures-session-basis-audit.md),
[validation repair](reports/20260819-run26-ai-validation-repair.md),
[fallback parity](reports/20260819-fallback-valuation-context-parity.md), and
[archive-only Preview](reports/20260819-run26-targeted-repair-preview.md). Full test and safety
results are in the [Phase 8.5.4 validation report](reports/20260819-phase8-5-4-validation.md).

## Phase 8.5.4.1 Operating Shadow Promotion

Validated source `3a6547e394452e6e1b986a8193f56c98fd07ef89` was fast-forwarded to `main` and
the clean operating checkout. The Thesis Monitor API restarted from that checkout, `/health`
passed, and 430 read-only operating smoke tests passed. All four Codex Scheduled Tasks remain ACTIVE
at 08:15/08:30/16:15/16:55 KST, keep the operating checkout, policy `daily-review-v3.10`, schema 4,
and received no configuration change or manual execution.

The live KRX preflight queried 2026-08-19 through 2026-08-13. The expected 2026-08-19 payload was
empty, while 2026-08-18 had rows but no verified reference under the current strict collector. Both
KOSPI200 and KOSDAQ150 are therefore live-unavailable and suppressed. Targeted raw checks confirm
matching 2026-09 contracts for the safe 2026-08-18 NIGHT -> 2026-08-14 DAY candidate, but the
collector cannot bridge that holiday gap. A stale 2026-08-14 NIGHT -> 2026-08-13 DAY pair passes the
ordinary path. This availability debt cannot reopen same-date promotion.

Visible current-PBR ownership currently redirects a history `current_value` to the canonical base
Fact only when the values are equal. An explicit `source_current_fact_id` lineage edge does not yet
exist and is recorded as `OPEN_LOW_PRIORITY`; this does not weaken the fail-closed binder gate.
See the [promotion](reports/20260819-phase8-5-4-1-shadow-promotion.md),
[preflight](reports/20260819-night-futures-live-readiness-preflight.md),
[operating state](reports/20260819-phase8-5-4-1-operating-shadow-state.md), and
[smoke](reports/20260819-phase8-5-4-1-operating-smoke.md) reports.

## Phase 8.5.4.2 Night Futures Calendar Repair

The remaining collector failure was a calendar traversal bug, not missing provider history. Both
the parser and canonicalizer required `NIGHT BAS_DD - 1 calendar day`, so 2026-08-18 NIGHT looked for
2026-08-17 DAY and stopped even though XKRX marks 2026-08-17 as a holiday and the correct 2026-08-14
DAY rows were already within the bounded provider lookback.

Implementation `7e7ab5acee2176bc8a452115da19ac6e14d312ab` now uses one shared XKRX predecessor
function. It selects only the latest eligible earlier DAY session, then requires the same product,
contract and maturity. It does not reconnect an older contract after rollover. Provider raw change
is audit-only and must agree with the deterministic two-price calculation when present.

Historical replay and the live read-only probe both resolve:

| Instrument | NIGHT | DAY reference | Contract | Derived | Provider audit |
|---|---|---|---|---:|---:|
| KOSPI200 | 2026-08-18 1094.95 | 2026-08-14 1098.90 | `A0169000` | -3.95 / -0.35945036% | -3.95 match |
| KOSDAQ150 | 2026-08-18 1477.30 | 2026-08-14 1487.50 | `A0669000` | -10.20 / -0.68571429% | -10.20 match |

The 2026-08-19 provider response still has zero rows. These pairs are therefore historical/stale,
not current, and user-visible promotion remains zero. Operating smoke passed 494 tests after API
restart; `/health` passed; all four tasks remain ACTIVE and unchanged. Telegram, task runs, Pilot,
DB, archive and receipt mutations were all zero. See the
[repair](reports/20260819-night-futures-preceding-session-calendar-repair.md),
[holiday audit](reports/20260819-night-futures-holiday-traversal-audit.md),
[validation](reports/20260819-phase8-5-4-2-validation.md),
[promotion](reports/20260819-phase8-5-4-2-shadow-promotion.md), and
[operating state](reports/20260819-phase8-5-4-2-operating-state.md) reports.

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
exists. At Phase 7.2.8 completion the branch was not merged or deployed and both Previews required
direct human approval; later ancestry promotion does not retroactively make them live evidence.
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
- Current price-context selector: `app/services/current_price_context_service.py`
- Runtime specificity plan: `app/services/runtime_specificity_service.py`
- Renderer and delivery: `app/services/ai_assisted_delivery_service.py`
- Deterministic fallback assembly: `app/services/notification_service.py`
- Industry routing and causal guardrails: `app/services/industry_reasoning_service.py`
- Skill: `.agents/skills/thesis-monitor-daily-review/SKILL.md`
- Runtime policy: `.agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md`
- Output schema: `.agents/skills/thesis-monitor-daily-review/references/output-schema.json`
- Pilot archive: `data/ai_review/pilot/history`

## Known Gaps

- Massive US breadth is implemented in shadow, but exact 08:05 KST readiness over 3-5 normal
  sessions is not yet established.
- KRX historical capability, universe and publication-state contracts pass experimentally, but
  16:05, 08:05 and T+1 roles remain `NOT_YET_PROVEN`; operating integration is false. The Kiwoom
  Windows gateway is not configured.
- KR market-wide investor flow is unavailable, and constituent-level sector participation remains
  incomplete.
- Industry-specific causal reasoning contracts are implemented, but specialized structured routing
  covers 9/20 immutable active stocks; taxonomy and business-unit coverage remain partial.
- Peer provider policy is FREE_ONLY. Phase 8.3 is finalized at 1/20 active and 1/15 meaningful
  coverage as SELECTIVE_OPTIONAL_CONTEXT. Broad runtime value is LOW_ROI; historical PIT and
  forward expansion are deferred, and operating integration is false.
- OCF extraction is partial; CAPEX aggregation and FCF remain open.
- The persisted US count includes the 2026-08-16 operationally complete session whose human message
  quality review failed. Operational count and human approval remain separate; this packet is not
  Production Assist evidence.
- TSM and WRD lack authoritative production identity evidence. Their live `unknown` state and
  multiple withholding are correct until a separately approved identity ingestion.
- The 2026-08-18 natural KR packet proves the repaired current-price RR paths for the four run-23
  affected stocks. RR runtime path is LIVE PATH PASS. Both natural US and KR AI drafts still failed
  the runtime quality gate and delivered deterministic fallback, so full Natural Live AI quality is
  PARTIAL. Phase 8.5.3.2 passes immutable replay and is shadow-promoted but still needs natural proof.
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

1. Wait for the next natural US/KR sessions and verify AI quality,
   night-futures session/reference evidence, fallback context parity, Korean language, price/RR,
   full validator, runtime receipt, archive, and exactly-once behavior.
2. Preserve operational counts KR 3/5 and US 3/5 and retain all natural/replay artifacts without
   counter edits, resends, or archive rewriting.
3. Keep TSM/WRD identity `unknown`, fine-grained industry routes general where unproved, peer data
   unavailable where absent, and OCF/CAPEX/FCF gaps explicit.
4. Continue exact-slot KRX 16:05, 08:05 and T+1 observations on its separate experimental branch.
   Do not merge or deploy until role evidence and Human Review pass.
5. Keep Phase 8.3 closed as selective optional context unless materially new free-source, taxonomy,
   exact-group or natural-message evidence appears.
6. If the post-repair natural review passes without a critical blocker, begin Cash Flow / Capital
   Efficiency Enrichment design. If it fails, repair the new blocker first.
7. Keep Production Assist disabled until natural full-message evidence passes direct human review
   and the user explicitly approves it.
