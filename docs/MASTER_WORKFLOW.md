# Thesis Monitor Master Workflow

Master Workflow: `v17`
As of: `2026-08-24`
Repository: `sskim-ai/thesis-monitor`
Operating branch: `main`
Latest evidence branch: `codex/kr-shadow-cohort-activation-gate-packet-persistence-repair`
Commit resolution: run `git rev-parse HEAD`; this document is part of that commit and must not
hardcode a self-referential final SHA. Resolve `origin/main` and the clean operating checkout at
session start. Phase 9.1A defines `working-capital-evidence-v1`; Phase 9.1B implements canonical
Facts and typed relations; Phase 9.1C closes archive-only consumption; Phase 9.1D observes detached
natural canaries; Phase 9.1E defines the user-visible family gate. Natural run-32 established total
Inventory `LIVE_PASS` with zero production influence while exact Trade AR remains `NOT_OBSERVED`.
Phase 9.1E.1 implements only the Inventory path, reuses the existing contract, preserves strict
AI/fallback parity and leaves Trade AR/broad AR/AP/advanced ratios blocked. Open P0/material P1 are
zero. Natural AI-assisted delivery remains `PARTIAL` independently.
KRX 8.2A.x and peer 8.3.x also remain experimental.

## 1. Project Mission

Thesis Monitor is a daily investment-monitoring system, not a news or price-alert feed. It combines
deterministic Facts, two bounded Knowledge references, AI reasoning, fail-closed validation, and an
adaptive message. It monitors whether a stored thesis is being confirmed, weakened, or left
unchanged without turning market movement into autonomous trading advice.

```text
Deterministic Facts + Knowledge + AI Reasoning + Validator + Adaptive Message
```

## 2. Responsibility Split

| Owner | Responsibility |
|---|---|
| Backend | Facts, identity, calculations, official assessment, canonical values |
| Knowledge | Investment and chart interpretation frameworks |
| Codex | Bounded analyst interpretation of one immutable packet |
| Validator | Numeric, lineage, scope, semantic, and message safety boundary |
| Renderer | Assembly of already-validated content |
| Receipt | Integrity binding for packet, output, and rendered payload set |
| Work | Architecture decisions and direct human-quality review |
| GitHub | Versioned source of truth for code, contracts, and review evidence |
| Telegram | Final communication surface, never a source of truth |

## 3. Source of Truth

Use this order when records disagree:

1. fetched Git refs and the clean checkout actually being used;
2. operating runtime state and immutable archives for delivery/Pilot facts;
3. `docs/project-state.json` for structured project state;
4. this workflow, `PROJECT_HANDOFF.md`, and `NEXT_SESSION_PROMPT.md`;
5. older reports and conversation history.

Never overwrite a natural runtime result to preserve a stale documented count. Reconcile the docs.

## 4. New Session Startup Routine

Run `git fetch origin`, `git status`, `git rev-parse HEAD`, and `git rev-parse origin/main`. Verify
the operating checkout separately. Read `project-state.json`, this workflow, the handoff, the next
session prompt, and the latest validation reports. Confirm Pilot, Production Assist, AI mode, all
four Scheduled Tasks, policy/schema/contracts, Knowledge checksums, Public Action, operationId
uniqueness, and migration state before editing.

If a natural packet completes during work, inspect its validator, delivery, archive, and Pilot state
read-only. Do not preserve an old count by editing documents or runtime data.

## 5. Immutable Investment/Safety Principles

- Missing data remains Unknown; it is never filled with model knowledge or zero.
- Backend calculations are not repeated by AI or renderer.
- Price, supply, and market context do not confirm a company thesis.
- Modeled estimates are not consensus.
- A good company is not automatically a good entry price.
- Adjusted chart prices and unadjusted valuation prices remain distinct.
- Telegram receives one AI-assisted set or one deterministic fallback set, never both.
- Existing packets, assessments, notifications, deliveries, and archives are immutable.
- Experimental Preview, operational Pilot success, human approval, main merge, deployment, and
  Production Assist approval are separate states.

## 6. Thesis vs Monitoring State

`ThesisAssessment` is the official deterministic thesis result. `monitoring-state-v1` stores
current, previous, and delta state for dynamic price structure, registered rules, supply, valuation,
and peer availability. A monitoring delta can change while the business thesis remains unchanged.
Registered levels are audit history; current dynamic structure is the decision context.

## 7. Investment Knowledge

Investment Knowledge v3.0 governs business, earnings, valuation, expectations, industry, macro,
risk, and monitoring safety.

SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`

Canonical, upload, and runtime mirror files must remain byte-identical. Knowledge changes require a
separate approved work order.

## 8. Chart Knowledge

Chart Knowledge v1.0 governs interpretation of backend-provided OHLCV structure and
observer/holder price context.

SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

It never authorizes Codex to calculate indicators or convert chart invalidation into thesis
invalidation.

## 9. Financial Safety

`financial-quality-taint-v2`, `financial-statement-basis-v1`, and
`financial-amount-period-v1` are fail-closed. Filing period, statement period, amount period,
comparison period, currency, and CFS/OFS basis are independent. Unsafe lineage taints only the
direct or derived Fact that depends on it; a safe current amount may survive an unsafe comparison.

## 10. Financial Lineage

`financial-lineage-v2` records provider, receipt, report code, statement basis/type, exact account,
amount scope, start/end dates, comparison lineage, currency, source type, and row identity.
`opendart-authoritative-recovery-v1` proved archive-only recovery for seven active KR tickers:
3,109 source rows, 37 safe direct Facts, 17 safe income-statement amounts, five margins, 17 safe
YoY Facts, and six inventory Facts. XBRL is ambiguity-only and unique-match-only. OCF remains
PARTIAL; CAPEX components are audit-only; FCF remains OPEN.

## 11. Security Identity / ADR

`security-identity-v2` separates issuer identity, listed-security identity, depositary status, ADR
ratio, share basis, and currency basis. Verified ADS identity does not prove a current-security
valuation denominator. Unknown or conflicting identity withholds dependent prose. TSM and WRD remain
Unknown until authoritative ingestion is separately approved.

## 12. Valuation Safety

`typed-valuation-interpretation-v2` binds each exact interpretation occurrence to metric, Fact,
numeric references, direction, basis, source, and economic scope.
`semantic-scope-and-decision-hierarchy-v1` keeps ordinary PER/PBR at company/listed-security scope,
blocks denied-Fact qualitative echo, and retains safe decision-relevant history.

`valuation-context-wording-v1` records current/history/peer/forward availability and actual use. Its
classes are `CURRENT_ONLY`, `CURRENT_PLUS_HISTORY`, `CURRENT_PLUS_PEER`,
`CURRENT_PLUS_HISTORY_PLUS_PEER`, and `LIMITED_VALUATION`. A visible historical percentile cannot
coexist with current-only wording. Peer missing is not peer zero, and a company multiple is not a
segment multiple.

## 13. OHLCV Structure

`ohlcv-structure-v2` owns pivots, major swings, zones, boxes, ATR, tentative wave/Fibonacci context,
dynamic invalidation, and risk/reward. Current-price RR and support-entry conditional RR have
different semantic IDs and labels. A crossed confirmation is never automatically called support.

## 14. Supply

KR supply uses exact foreign/institution actor and 1/5/20-day horizon Facts. One actor or horizon
cannot cover another. US stock positioning uses verified volume, relative volume, or an explicit US
positioning Fact; KR investor-flow boilerplate is forbidden. Supply is positioning context only.

## 15. Market Intelligence

Market reasoning follows verified change, market structure, economic transmission, monitored
portfolio relevance, and next confirmation. Index direction, breadth, concentration, sectors,
flows, rates, FX, oil, VIX, and night futures retain separate semantics. Night futures are Korean
opening context, not company-thesis evidence.

## 16. US Breadth

`market-cross-section-v1` and `market-breadth-v1` support a shadow Massive full-market daily
cross-section with `massive-us-active-common-equities-v1`. The 2026-08-14 capability sample had
12,424 raw rows and 5,461 eligible securities. Reference cache TTL is one trading session. Split-
adjusted decimal volume and close-times-volume remain audit-only. Exact 08:05 KST readiness over
3-5 normal sessions is still OPEN.

## 17. KR Breadth Status

KRX Open API is approved. Historical capability and breadth calculation pass, the common-share
universe contract is closed, and publication-readiness/telemetry contracts pass. The provider role
is time-slot specific: same-day 16:05, next-morning 08:05 and T+1 reconciliation are all
`NOT_YET_PROVEN`; only historical retrieval is `SUPPORTED`. Current-session readiness is `PARTIAL`,
sector coverage is `PARTIAL_PRICE_PROXY_ONLY`, market-wide investor flow is `UNSUPPORTED`, and
production integration is `NOT YET`.

`krx-exact-slot-capture-v1` is now operating as telemetry only. A dedicated LaunchAgent records the
four core endpoint statuses, row counts, provider dates and payload hashes at natural 08:05 and
16:05 KST slots. It has no market-packet, DB, AI or notification integration. Wrong-minute,
weekend and XKRX-holiday launches stop before provider access. The T+1 role has no defined exact
clock in the current contract, so it is not inferred from 08:05 and remains unconfigured.

The 2026-08-18 core four endpoints returned HTTP 200 with zero rows at 20:27, 21:02 and 21:06 KST.
That is `MARKET_COMPLETED_PROVIDER_PENDING`; first non-empty, first complete and observed-complete-by
were not observed. This evidence does not prove that KRX is a late or T+1 provider. Authority is
not same-day operational suitability. Close, morning, reconciliation and historical roles remain
separate; 16:05 and 08:05 require 3-5 clean sessions and T+1 requires at least three.

Kiwoom remains an unconfigured `bridge_shadow`; automatic fallback is disabled. Market-wide KR
investor flow remains unavailable. For copyable official references, use the
[KRX service list](https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd),
[Korean terms](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO002.jsp), and
[English terms](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO005.jsp).

## 17A. Peer Valuation Status

`peer-sector-valuation-v1` and `verified-profile-peers-v2` pass, including taxonomy selection,
issuer deduplication, security basis, denominator safety, staleness, minimum sample, industry
guardrails and numeric provenance. Phase 8.3 is finalized on the current roadmap as
`SELECTIVE_OPTIONAL_CONTEXT`; its broad runtime value is `LOW_ROI` and operating integration is
`NO`. The original Phase 8.3 branch includes KRX Git ancestry, while
`codex/integration-phase-8-3-peer-only` reconstructs the peer contract from operating main without
KRX code. Phase 8.3.2A and finalization start from that clean ancestry.

Peer provider policy is permanently `FREE_ONLY` on the current roadmap. Paid/institutional research
is retained as reference but the paid path is `CLOSED_BY_POLICY`. Historical peer PIT and forward
peer consensus are `DEFERRED`; broad provider, forward and PIT expansion are stopped.

The immutable free-source POC measures one `MEDIUM+` subject among 20 active stocks: 1/20 raw
coverage and 1/15 among economically meaningful subjects. KR is 0/7; US is 1/13. TSLA alone has an
exact automotive group and three clean PER issuers. Broad Technology, Media and semiconductor
groups remain `LOW`, including MU because semiconductor is not a verified memory peer universe.
The recommendation is selective optional context, not a broad runtime feature. Tooling, validators,
statistics, audit artifacts and the clean peer-only branch are preserved. `LOW` remains audit-only,
and `NOT_MEANINGFUL` is correct suppression rather than a coverage failure. Reopen only when exact
taxonomy or free valuation coverage improves naturally, a safe new free source appears, a specific
industry reliably has three clean issuers, or a natural operating-message review establishes a new
peer need.

The TSLA sample retains `MEDIUM` quality and the same four visible numeric claims, but user-facing
wording now identifies the sample as a same-automotive-classification `기초 비교군`. Taxonomy and
current-multiple eligibility do not prove full economic comparability, so the sentence explicitly
limits direct peer-premium interpretation without adding unverified TSLA narratives.

## 18. Numeric Provenance

Every visible investment number follows:

```text
Fact -> fact_id -> field_path -> semantic_type -> canonical formatter
     -> exact text_ref -> exact usage -> schema-4 numeric claim
```

Codex authors draft placeholders and references. The binder owns labels, values, rounding, units,
period/basis phrases, Korean postpositions, and final claims. Unknown semantics, raw prose numbers,
wrong zone roles, and partial occurrence coverage are rejected.

## 19. Renderer / Message Architecture

`delta-first-rendering-v1` plus `decision-material-delta-v1` selects verified decision relevance
before section order. Phase 8.4.x closes integrated full messages, delta-first selection, adaptive
suppression, scope, denied echo, history retention, valuation context wording, observer/holder,
Unknown, and next-check foundations.

The renderer assembles validated content; it does not calculate or repair meaning. The exact final
Telegram text must pass `runtime-message-quality-v1`. Phase 8.4.1 Work review scores were Samsung
17, POSCO 16, Hyundai Glovis 18, Korean Re 16, and SK hynix 17: average 16.8/20. Phase 8.4.1.1 fixes
the one remaining valuation-context contradiction without reopening the architecture.

`industry-specific-reasoning-v1` now sits between verified Fact selection and adaptive rendering.
It routes only from structured company classification, records confidence and missing drivers, and
requires exact supporting Fact IDs for causal claims. Thesis and themes cannot replace the primary
framework. The Phase 8.5 archive audit covers 20 active KR/US stocks: nine have high-confidence
specialized routes and eleven correctly remain low-confidence `general`. The reasoning contract is
implemented, while specialized taxonomy coverage remains a strong PARTIAL gap.

Phase 8.5.3 adds two bounded runtime contracts without redesigning schema 4. The
`runtime-message-specificity-v2` plan selects each stock's decision point, company evidence,
industry driver, Unknown, and next confirmation before prose; methodology-only safety boilerplate is
suppressed rather than paraphrased. The `current-price-context-v1` selector gives AI and deterministic
fallback the same current price, dynamic support/resistance, current-price RR, chart invalidation,
chart state, and registered-rule lifecycle. The selector performs no calculation. Crossed registered
confirmations are history, never future triggers or automatically promoted support.

Phase 8.5.3.1 adds final Korean object-particle and actor-flow checks plus structured intra-message
dedup. `priority_watch` owns ongoing drivers/risks, while `next_checks` owns time-bound confirmation
events. Numeric repetition is audited by `fact_id` and `field_path`; the same exact Fact cannot be
printed three or more times in one stock message. These checks extend `runtime-message-quality-v1`
without changing its existing portfolio repetition threshold.

Phase 8.5.3.2 adds `valuation-comparison-label-v1`. Historical-distribution `current_value`,
`historical_median`, `historical_mean`, percentile cut values, and current percentile retain
distinct comparison roles through the numeric registry and binder. A legacy schema-4 packet is
recovered from its exact field path. Different values with different roles cannot share one visible
label in a stock message. RXRX now renders current PBR, historical PBR median, and historical PBR
percentile distinctly without changing its biotech valuation boundary.

Phase 8.5.4 reconstructs natural US packet `2026-08-19-us-run-26-cd80a8e4d373`. The natural task
delivered deterministic fallback 14/14 exactly once, but AI output was rejected. The six-error
attempt had RXRX/WULF current-PBR ownership errors and CORZ typed valuation occurrence errors.
Retrospective replay now binds visible current PBR to the base `price_to_book` Fact, keeps history
statistics in historical roles, exactly covers the CORZ earnings-quality occurrence, and passes the
full validator and runtime language gate with zero errors. This is retrospective evidence only.

The same phase adds `night-futures-session-basis-v1`. The archived implementation compared DAY and
NIGHT rows carrying the same KRX `BAS_DD`, but KRX assigns the overnight trading day by the 06:00
end time. The same-date DAY close therefore occurs later and is not a valid night-session reference.
The repaired contract requires verified instrument/contract, NIGHT session, immediately preceding
DAY reference, dates, prices, source IDs and payload SHA before promotion. Run-26 cannot reproduce
the required 2026-08-19 NIGHT row, so both night-futures changes are
`UNAVAILABLE_BY_CONTRACT`, not corrected by an assumed value.

Fallback valuation wording now derives from the metrics actually rendered under
`valuation-context-wording-v1`. Safe PE can no longer coexist with a generic “earnings excluded”
tail. Selected support and resistance overlap also fails RR closed generically; run-26 HUT and WULF
archive-only replays suppress the old 0.66x and 0.42x ratios without moving any zone.

Phase 8.5.4.1 fast-forwarded the validated Phase 8.5.4 code through `3a6547e` to `main` and the clean
operating checkout. The API was restarted and passed health; 430 operating smoke tests passed. A
read-only live preflight found the expected 2026-08-19 KRX rows still pending, so KOSPI200 and
KOSDAQ150 are currently unavailable rather than promoted from stale data. A stale but structurally
valid 2026-08-14 NIGHT -> 2026-08-13 DAY same-contract pair proves the ordinary-session path. The
collector still cannot bridge a multi-day holiday reference such as 2026-08-18 -> 2026-08-14;
this is an availability debt, not a wrong-session safety opening. Natural proof is still required.

Phase 8.5.4.2 closes that availability debt retrospectively and is promoted to operating shadow at
implementation commit `7e7ab5a`. Parser and canonical validation now share an XKRX previous-session
lookup rather than calendar subtraction. The 2026-08-18 NIGHT rows resolve through the 2026-08-17
holiday to 2026-08-14 DAY for matching September contracts. Backend-derived KOSPI200 -3.95 and
KOSDAQ150 -10.20 changes agree with provider audit fields. The current 2026-08-19 response is still
empty, so those historical pairs remain stale and user-visible current exposure remains zero.
Same-date, future-session, rollover, raw-change-conflict and stale controls remain fail-closed.

Phase 8.5.5 reconstructs natural KR packet `2026-08-19-kr-run-27-63a064e837ff`. AI sent 0 and
deterministic fallback delivered 8/8 exactly once. Korean Re's alleged depositary prose was a
validator false positive: the optional depositary qualifier made `합산비율 ... 확인` match an ADR
ratio expression even though canonical identity was verified non-depositary common stock. The
repair requires an explicit ADR/ADS/depositary qualifier and suppresses depositary candidates before
prose for domestic/non-depositary securities.

The same phase separates `chart_risk_reward` from industry frameworks. It is owned only by
`price_context`; POSCO retains steel/materials reasoning and Hyundai Glovis retains
transport/logistics reasoning. `runtime-reasoning-ownership-v1` and
`runtime-message-specificity-v2` publish candidate owner, evidence, decision role, section,
specificity key and suppression reason. The immutable replay automatically binds all 117 numeric
references, has zero validator errors, reduces substantive/template repeats from 2/4 to 0/0, and
passes the unchanged runtime-quality threshold and receipt verification. Average stock-message
length falls 2.34%. This is retrospective proof only.

Phase 8.5.5.1 reconstructs natural US packet `2026-08-20-us-run-28-9024def294e6`. Numeric,
semantic and final-language validation passed, but the unchanged runtime quality gate rejected the
AI candidate; AI sent 0 and deterministic fallback delivered 14/14 exactly once. The packet kept
Phase 8.5.5 ownership, observer/holder, Unknown and next-check improvements, but a policy-level
two-anchor quota copied valuation-source TTM EPS and BVPS into sparse `business_earnings` sections.
The same portfolio scaffold began with `현재 확인된 핵심 숫자는`, while ten stocks repeated a
standalone previous-RR/current-RR tuple.

`numeric-summary-ownership-v1` removes the numeric quota, keeps real earnings revenue/income/margin
Facts, rejects valuation-owned business fillers, and permits a specific Unknown when direct business
evidence is absent. `typed-template-skeleton-v1` preserves section, owner, numeric semantics,
comparison relation and text shape. It therefore separates RR previous-to-current from PBR
current-to-historical-percentile without allowing genuine same-role template repetition. RR deltas
render only when an existing chart-state, confirmation, structure or availability transition makes
them decision-relevant; no RR threshold or formula changed.

The immutable run-28 replay binds 149 numbers automatically with manual/rejected/unresolved 0,
passes the full validator, final language, unchanged runtime gate and receipt, and reduces template
skeletons 5 -> 0, generic numeric-summary families 1 -> 0 and business ownership violations 9 -> 0.
Run-27 remains PASS. Average stock-message length falls 4.00%. Implementation `c915d44` passed
GitHub Actions run `32319601429`, was fast-forwarded to main and operating, passed API health and
291 operating smoke tests. This remains retrospective proof; Natural AI-Assisted Delivery is still
`PARTIAL`.

Phase 8.5.5.2 reconstructs natural KR packet `2026-08-20-kr-run-29-6e8809e1e944`. The final AI
candidate passed numeric, semantic, and language checks but failed runtime quality on three
independent prose families: canonical 1/5/20-day supply rows were treated as prose templates, exact
current RR appeared in both core and price, and common financial-basis/cash-conversion cautions
repeated across stocks. AI sent 0; deterministic fallback delivered 8/8 exactly once.

`canonical-supply-flow-tuple-v1` preserves stable foreign/institution actor-horizon rows while
continuing to check adjacent interpretation. `numeric-primary-owner-v1` assigns exact current RR to
`price_positioning.text` once and removes only safely identifiable secondary occurrences before
binding. Common financial caution and inventory/CAPEX-to-FCF/ROIC candidates are suppressed when
company-specific Unknowns and next checks already own the decision question. The immutable replay
binds 112 numbers automatically with manual/rejected/unresolved 0, passes validation, language,
runtime quality and receipt verification, and retains run-28/run-27 PASS. Average stock-message
length falls 3.19%. No threshold, RR formula, support/resistance, denominator, fallback, KRX user
integration, Telegram, task, Pilot, DB, archive, or receipt behavior changed.

## 20. Phase History

| Phase | Result |
|---|---|
| 7.x | Numeric provenance, security/financial quality, statement/amount basis, typed valuation, renderer quality, receipt/fallback integrity |
| 8.0A/8.2 capability | Massive US breadth implemented in shadow; Kiwoom/KRX bridge architecture prepared |
| 8.1 | `financial-lineage-v2` and exact XBRL fallback architecture |
| 8.1.1 | Recent authoritative OpenDART recovery with safe direct Fact promotion |
| 8.1.2 | Data/Safety PASS; financial-only message quality gap identified |
| 8.4 | Integrated schema-4 delta-first full messages |
| 8.4.1 | Economic scope, denied echo, decision hierarchy, history retention |
| 8.4.1.1 | Valuation-context wording matrix and contradiction validator; Phase 8.4 foundation finalized |
| 8.5 | Fact-dependent industry routing/causal guardrails; archive-only KR/US full-message evidence; specialized coverage strong PARTIAL |
| 8.5.1 | Exchange-calendar session repair and exact current-price RR packet/numeric-path replay; natural-live proof pending |
| 8.5.2 | Phase 8.5.1 linear ancestry promoted to main and the operating shadow checkout; API/task health verified; natural-live proof pending |
| 8.5.3 | Natural US/KR quality failure reconstructed; AI specificity and fallback dynamic-price parity PASS; promoted with 8.5.3.1, natural AI delivery pending |
| 8.5.3.1 | Korean language and intra-message dedup PASS; Phase 8.5.3 chain promoted to operating shadow; natural AI delivery pending |
| 8.5.3.2 | Valuation comparison-role labels and collision validator PASS; targeted repair promoted to operating shadow; natural AI delivery pending |
| 8.5.4 | Run-26 night-session, semantic binding, typed valuation, fallback parity and overlapping-zone RR repairs PASS retrospectively |
| 8.5.4.1 | Phase 8.5.4 promoted to main and operating shadow; API/health/smoke PASS; latest night pair unavailable fail-closed; natural proof pending |
| 8.5.4.2 | Holiday-aware XKRX preceding-DAY lookup PASS retrospectively and promoted to operating shadow; current provider row pending; natural proof pending |
| 8.5.5 | Run-27 security/framework ownership and repetition repair PASS retrospectively and promoted to operating shadow; natural proof pending |
| 8.5.5.1 | Run-28 business numeric ownership, typed skeleton and RR-delta repetition repair PASS retrospectively and promoted to operating shadow; natural proof pending |
| 8.5.5.2 | Run-29 canonical supply tuple, current-RR single owner and typed prose repetition repair PASS retrospectively; promoted to operating shadow; Phase Advancement Rule v1 applied |
| 8.2A.x | KRX historical engine, universe and publication-state contracts PASS; exact 08:05/16:05 telemetry-only capture operating; user-visible integration 0; roles not yet proven |
| 8.3 | Peer selection/safety/statistics contract PASS; capability strong PARTIAL; original measured coverage 0/20 |
| 8.3.1/8.3.1.1 | Paid provider research completed; clean peer-only branch prepared; production provider gate not passed |
| 8.3.2A | Policy changed to FREE_ONLY; current free-source POC measured 1/20 and recommends selective optional context; not merged or deployed |
| 8.3 Finalization | Contract/safety PASS; broad expansion stopped at LOW_ROI; tooling retained as SELECTIVE_OPTIONAL_CONTEXT; not merged or deployed |

### Current Status Summary

| Area | Status |
|---|---|
| Phase 8.4 Message Intelligence | COMPLETE |
| Phase 8.5 Industry-Specific Reasoning | STRONG PARTIAL |
| Phase 8.5.1 RR Runtime | LIVE PATH PASS |
| Phase 8.5.3 Runtime Specificity | PASS retrospective |
| Phase 8.5.3.1 Language/Dedup | PASS |
| RXRX valuation label repair | CLOSED |
| Fallback dynamic price | CLOSED |
| Natural AI-Assisted Delivery | PARTIAL |
| Phase 8.5.5 reasoning ownership | LIVE_PASS on run-29 exercised security/framework routes |
| Phase 8.5.5 natural repetition | repaired families LIVE_PASS; run-29 independent KR family CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Phase 8.5.5 operating state | OPERATING_SHADOW |
| Phase 8.5.5.1 US numeric-summary ownership | LIVE_PASS on run-29 exercised generic-summary/ownership audit |
| Phase 8.5.5.1 typed repetition | LIVE_PASS on run-29; new KR tuple family handled separately |
| Phase 8.5.5.1 operating state | OPERATING_SHADOW |
| Phase 8.5.5.2 KR structured repetition | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Phase 8.5.5.2 supply / RR ownership | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Phase 8.5.5.2 operating state | OPERATING_SHADOW |
| Phase 8.5.4.2 calendar repair / operating | PASS retrospective / OPERATING_SHADOW |
| Night-futures session basis | CLOSED_RETROSPECTIVE |
| Preceding DAY calendar lookup | CLOSED_RETROSPECTIVE_PENDING_NATURAL; current provider row pending |
| Fallback valuation context parity | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Phase 8.3 Contract / Safety | PASS / PASS |
| Phase 8.3 broad value / scope | LOW_ROI / SELECTIVE_OPTIONAL_CONTEXT |
| KRX historical / universe / breadth | PASS / CLOSED / PASS |
| KRX 16:05 / 08:05 / T+1 | NOT_YET_PROVEN / NOT_YET_PROVEN / NOT_YET_PROVEN |
| KRX exact-slot capture | OPERATING_TELEMETRY_ONLY_PENDING_NATURAL; 08:05/16:05 active, T+1 clock undefined |
| KRX user-visible integration | NO |
| Production Assist / AI mode | OFF / shadow |
| Phase 9.0A | ARCHITECTURE_CLOSED; runtime behavior change 0 |
| Phase 9.0B readiness / scope | YES / SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE |

## 21. Current Persistent Gaps

| Gap | Status |
|---|---|
| Industry-specific investment reasoning | STRONG PARTIAL |
| Structured specialized taxonomy coverage | PARTIAL |
| Peer/sector valuation | CLOSED SCOPE: contract/safety PASS, SELECTIVE_OPTIONAL_CONTEXT, operating NO |
| Peer provider policy | FREE_ONLY; paid path CLOSED_BY_POLICY |
| Historical peer PIT | DEFERRED |
| Forward peer consensus | DEFERRED |
| KR market breadth | historical PASS; current readiness PARTIAL; operating integration NO |
| KRX 16:05 / 08:05 / T+1 roles | NOT_YET_PROVEN |
| KRX exact-slot telemetry capture | CLOSED_CONFIGURATION_PENDING_NATURAL_0805_1605; T+1 slot undefined |
| KR market-wide flow | UNSUPPORTED |
| Massive 08:05 readiness | OPEN |
| OCF | ARCHITECTURE_CLOSED; 12/20 evidence-eligible, 7 partial, 1 blocked |
| PPE CAPEX | ARCHITECTURE_CLOSED; 11/20 evidence-eligible, 6 partial, 2 blocked, 1 N/A |
| FCF | ARCHITECTURE_CLOSED_SELECTIVE; 11/20 evidence-eligible, 8 blocked, 1 N/A |
| Working-capital days / CCC | DEFERRED; no full safe CCC coverage |
| Standard ROIC | DEFERRED; verified excess-cash policy absent |
| Natural live validation of Phase 8 code | PARTIAL |
| Current-price RR packet/numeric path | LIVE PATH PASS |
| AI natural-live message quality | PARTIAL: retrospective PASS, natural AI delivery pending |
| Reasoning ownership | LIVE_PASS_RUN29 |
| Natural cross-ticker repetition | PRIOR_FAMILIES_LIVE_PASS; KR_STRUCTURED_FAMILY_CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| US numeric-summary ownership | LIVE_PASS_RUN29 |
| Typed template repetition | LIVE_PASS_RUN29; KR_STRUCTURED_EXTENSION_PENDING_NATURAL |
| Canonical supply tuple ownership | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Canonical current-RR owner | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Fallback dynamic-price lifecycle | CLOSED: retrospective PASS and operating code promoted |
| Night-futures session-basis integrity | CLOSED_RETROSPECTIVE |
| Night-futures preceding DAY calendar lookup | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| Fallback valuation context parity | CLOSED_RETROSPECTIVE_PENDING_NATURAL |
| KRX Open API primary breadth | APPROVED, NOT INTEGRATED; experimental development authorized |
| Human-approved Production Assist evidence | INSUFFICIENT |

Closed engineering gaps include numeric provenance, canonical formatting, financial quality taint,
security identity fail-closed, field-level financial lineage, unsafe growth blocking, integrated
full messages, valuation scope, denied echo, decision-material delta, historical retention,
valuation-context wording, observer/holder foundation, Unknown/next-check foundation, receipt
integrity, fallback/retry, exactly-once accounting, and valuation comparison-label collisions.

## 21A. Phase Advancement Rule v1

Every newly observed blocker is classified before it can affect the roadmap:

- **P0 Safety/Correctness**: wrong or unproved visible data, identity/basis/session errors,
  fabricated calculations, invalid canonical RR, receipt/archive/exactly-once failure, or duplicate
  delivery. Any open P0 blocks Phase 9.0A.
- **P1 Analysis Integrity**: ownership/framework/meaning errors or structural repetition severe
  enough to make analysis generic or prevent valid output. A bounded targeted repair plus
  retrospective replay and CI PASS closes the roadmap gate; every P1 does not require a separate
  natural delivery before architecture work may continue.
- **P2 Quality/UX**: non-material wording, labeling, ordering, length, qualitative RR polish, or
  unavailable optional integrations. P2 remains backlog and cannot block a major phase.

Aggregate Natural AI-Assisted Delivery and individual repair proof are separate. A repair may be
marked `LIVE_PASS` only when its behavior was exercised in a natural packet and did not recur; an
unexercised repair remains `NOT_OBSERVED`. A different new P1 family does not reopen an already
exercised repair. Natural runtime observation and major evidence-architecture design may proceed in
parallel while Production Assist remains OFF. A new P0 interrupts Phase 9.0A work for targeted
repair; material P1 is bounded and prioritized, and P2 never interrupts it. KRX publication timing
is a parallel evidence track and does not block Phase 9.0A.

## 21B. Phase 9.0A Cash-Flow Evidence Architecture

`cash-flow-capital-efficiency-v1` extends the financial-lineage, financial-quality, and
security-identity contracts. Reported facts remain occurrence-bound and every derived metric
requires input fact IDs. Flow periods are explicit `QTD`, `YTD`, `FY`, or `TTM`; balances are
`POINT_IN_TIME`. Q2/Q3 QTD and TTM derivations require compatible issuer, fiscal calendar,
semantic, currency/unit, entity scope, statement basis, and restatement policy. Annualization is
forbidden.

Backend baseline FCF is OCF minus positive-magnitude PPE-only cash outflow. Intangibles,
capitalized software, acquisitions, securities purchases, and total investing cash flow are not
silently included. Management-defined FCF remains separate. The active-universe audit classifies
20 stocks from the operating database: 11 have a same-accession/period/unit official SEC OCF/PPE
pair. Seven KR subjects retain exact OpenDART rows but remain partial because the existing XBRL
audit could not prove a unique cash-flow period context. Korean Re is excluded from generic
corporate FCF.

Raw inventory/trade AR/trade AP and comparable-date deltas precede DSO/CCC. Broad receivable or
payable totals are partial, and full CCC coverage is zero. Standard ROIC is deferred because no
verified excess-cash policy exists; total cash is never silently treated as excess cash. Foreign
issuer-level cash-flow margins can remain eligible without an ADR ratio, while per-share, yield,
EV, FX, and depositary-basis arithmetic remains blocked until security-level basis is verified.

Open P0 and P1 are zero. `PHASE_9_0B_READY = YES`; scope is
`SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`. Phase 9.0B may implement canonical core facts only
for eligible evidence and must fail closed elsewhere. Working-capital days/CCC and ROIC are later
phases. The one-file human report is
[the Phase 9.0A complete bundle](reports/20260820-phase9-0a-complete-report-bundle.md).

## 21C. Phase 9.0B Canonical OCF / PPE-CAPEX / FCF Core

Phase 9.0B implements the `cash-flow-capital-efficiency-v1` canonical core without importing it
into any runtime packet or public schema. The exact official-filing registry maps only operating
activities cash flow and reviewed PPE-payment concepts. Reported Facts retain accession,
occurrence, filing version, source semantic, period, currency/unit, entity/basis, source sign, and
raw SHA. PPE payments normalize to positive outflow magnitude only after semantic validation.

Interim cash-flow occurrences remain YTD. Q1 QTD, adjacent-YTD QTD, and three-input TTM Facts are
typed `DERIVED_PERIOD`; FCF is typed `DERIVED_METRIC` and always contains the OCF and PPE-CAPEX Fact
IDs. SEC comparative rows use the earliest official occurrence's economic fiscal context and the
latest filing's authoritative value, preventing a later comparative column from changing the
underlying fiscal year. Annualization remains prohibited.

Stored official evidence reproduces the Phase 9.0A universe counts with no drift: OCF
`12 eligible / 7 partial / 1 blocked`, PPE CAPEX `11 eligible / 6 partial / 2 blocked / 1 N/A`, and
FCF `11 eligible / 8 blocked / 1 N/A`. All 191 generated FCF Facts pass input-lineage and exact
arithmetic reproduction. KR non-financial Facts remain fail-closed on unresolved OpenDART period
context, Korean Re remains outside generic enterprise FCF, and issuer-level foreign cash flow is
kept separate from security-level yield/per-share arithmetic.

Open P0 and P1 are zero. `PHASE_9_0C_READY = YES`; scope is
`CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY`. CCC and standard ROIC remain deferred. The
OpenDART period-context gap is `MEDIUM_COMPLEXITY_FOLLOWUP`, not a prerequisite for selective
shadow consumption. See the
[Phase 9.0B complete bundle](reports/20260820-phase9-0b-complete-report-bundle.md).

## 21D. Phase 9.0C Cash-Flow Shadow Consumption

Phase 9.0C adds `cash-flow-shadow-consumption-v1` as an archive-only consumer of the canonical
core. It never recalculates OCF, PPE CAPEX, or FCF. A Fact must first pass source-date point-in-time
eligibility, formal-period freshness, comparable-period compatibility, industry applicability, and
deterministic materiality. No arbitrary day threshold, annualization, mixed-period comparison, or
old-period substitution is permitted.

The 20-subject audit finds 10 current formal contexts, two formal-lagging-provisional contexts,
seven blocked, and one not applicable. Twelve are consumption-eligible, but materiality renders
only nine full-FCF contexts and one OCF-only context. All 10 exact numbers bind automatically to
Phase 9.0B Fact IDs; manual, rejected, unresolved, semantic-error, future-fact, stale-as-current,
and KR numeric-injection counts are zero. Eight of 17 prior cash-flow Unknowns resolve, eight remain
valid, and Korean Re's generic enterprise-FCF Unknown is suppressed as not applicable.

Run-28 before/after and the run-29 KR negative control pass final language, runtime quality, and
receipt verification without threshold changes. Human review classifies 8 material improvements,
4 minor improvements, 8 no meaningful changes, and 0 degraded. Open P0 and P1 are zero.
`PHASE_9_0D_READY = YES` with scope `SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY`. Cash-flow remains
absent from the production packet, prompt, fallback, Public Action, and Telegram. See the
[Phase 9.0C complete bundle](reports/20260820-phase9-0c-complete-report-bundle.md).

## 21E. Phase 9.0D Cash-Flow Runtime Shadow Canary

Phase 9.0D implements `cash-flow-runtime-shadow-canary-v1` from immutable instruction commit
`a24e4f2210f944fa7c43d8dbf8be1d1a8e652164`. A terminal production AI-assisted or deterministic
fallback result launches a detached child only after `delivery-result.json` is final. The parent
keeps its original result and exit path; canary generation, validation, quality or archive failure
cannot alter Telegram, fallback, backup, receipt, exactly-once, Pilot or assessment behavior.

The child uses the exact packet plus Phase 9.0B Facts and Phase 9.0C PIT/freshness/comparison,
industry and materiality contracts. Its manifest, sidecar, shadow output, numeric/semantic
validation, quality receipt and completion marker live in a separate create-once namespace.
Identity combines packet, consumption contract and canary policy, so primary/backup/retry
processing produces one logical proof. The production candidate is never enriched or overwritten.

Temporary run-28 replay passes with 10 automatic bindings and zero semantic, quality or production-
influence errors. The run-29 KR negative control passes with zero cash-flow injection. These are
retrospective deployment checks, not natural proof. Runtime state is
`RUNTIME_CANARY_DEPLOYED_PENDING_NATURAL`; user-visible cash flow remains disabled and
`PHASE_9_0E_READY = NO` until the first natural US canary is reviewed. See the
[Phase 9.0D complete bundle](reports/20260820-phase9-0d-complete-report-bundle.md).

## 21F. Phase 9.0D Natural Proof And Baseline Consistency

Natural run `2026-08-21-us-run-30-5a3b7c1c4390` delivered deterministic fallback `14/14`
exactly once, then launched canary `cf-canary-f5ce3f836df99c546cf6f696`. The canary completed with
nine full-FCF subjects, one OCF-only subject, two formal-lagging-provisional suppressions, one
blocked subject, 10 automatic numeric bindings, zero semantic/quality/PIT/lineage/arithmetic
errors, and zero production influence. Phase 9.0D runtime behavior is therefore
`LIVE_PASS_SELECTIVE_SUBSET`.

Human cross-artifact review found that TSLA's saved version-5 `custom_gpt` thesis still asserted
generic current `FCF 적자` and an implied turn-positive requirement. A prose-only warning backfill
treated the thesis reference as confirmation, but no financial Fact, period, or scope supported the
current claim. The same filing contains positive H1 YTD PPE-only FCF, negative Q2 QTD PPE-only FCF,
and positive TTM PPE-only FCF; the legacy phrase cannot be assigned to any one of them. Its
pre-repair severity is P0 because unsupported current financial state reached fallback.

Phase 9.0D.1 adds `baseline-cash-flow-claim-consistency-v1`. AI packet and fallback paths suppress
unsupported current-state prose without changing stored history or exposing canonical amounts.
The detached canary now compares production qualitative claims and canonical current-formal
context by rendered section. The 20-subject audit recognizes 21 occurrences: 13 consistent and 8
suppressed occurrences of one TSLA root family. Repaired run-30 cross-artifact errors are zero;
RXRX negative cash burn, WRD future watch ownership, HUT OCF-only, TSM/WRD lagging-formal, SKHY
blocked, and insurance N/A controls remain intact.

Open P0 and material P1 are zero. `PHASE_9_0E_READY = YES`; initial scope is
`SELECTIVE_CURRENT_FORMAL_FULL_FCF_USER_VISIBLE_INTEGRATION`. User-visible cash-flow remains off
until that separate phase. A second arbitrary natural run is not required for this bounded repair.

## 21G. Phase 9.0E Selective User-Visible Cash Flow

Phase 9.0E implements `cash-flow-user-visible-v1` from immutable instruction commit
`309f5f1756d39d5972c5d4b48faaeab4862d8077`. The selector exposes at most one PPE-only FCF number
under `business_earnings` when a US/foreign SEC subject is PIT-safe, current formal, full-FCF,
industry-applicable, material, lineage-complete, and baseline-consistent. There is no ticker
allowlist or numeric threshold. OCF-only, KR, insurance generic FCF, lagging-provisional, stale,
blocked, management-FCF, security-level valuation, CCC, and ROIC remain excluded.

Run-30 archive preview selects 9 of 13 subjects. All nine numbers bind automatically to canonical
FCF Fact IDs; AI/fallback parity, semantic validation, final language, and runtime quality pass with
zero repeated cash-flow sentence/skeleton blockers. HUT is OCF-only, SKHY is blocked, and TSM/WRD
lag formal provisional periods. Run-29 injects zero KR cash-flow numbers. OFF injects zero and any
invalid mode fails safe to OFF.

Implementation SHA `cf3194981124de2a6f85fbe81b145ef06e1db08d` passed Actions run
`32443322364`, was fast-forwarded to main/operating, and was enabled at 2026-08-21 12:31:47 KST
after OFF health verification. API health and 396 operating focused tests pass; four AI tasks and
KRX telemetry schedules are unchanged. No task or Telegram was run manually.

State is `DEPLOYED_SELECTIVE_PENDING_NATURAL`. The next natural US run is the first user-visible
proof; it can trigger the documented OFF kill switch if a P0 appears. Open P0/material P1 are zero,
so Working Capital Canonical Core architecture may proceed in parallel. Broader cash-flow exposure
still waits for natural proof.

## 21H. Phase 9.1A Working-Capital Evidence Architecture

Phase 9.1A implements the architecture-only `working-capital-evidence-v1` contract from immutable
instruction commit `eaaadb1ac4fb5c9a7d3486ecc8274708c285ff79`. It extends existing canonical
financial Facts with source availability, balance scope, and net/gross scope while remaining outside
all production packet, prompt, renderer, fallback, Public Action, database, task, and delivery paths.

Inventory means total inventory only. Exact trade AR/AP and broader AR/AP remain distinct metrics;
current/noncurrent and issuer-reported net/gross scope are preserved without summation or renaming.
The primary comparable is the same issuer fiscal quarter in the prior fiscal year with exact
semantic, currency/unit, entity, statement basis, and source-version compatibility. Revenue and COGS
relations use compatible filing periods, with YTD preferred for Q2/Q3. DSO, Inventory Days, DPO, and
CCC remain deferred.

The 20-subject audit records Inventory `11 eligible / 3 partial / 5 blocked / 1 N/A`; trade AR
`6 / 1 / 12 / 1`; broad AR `9 / 3 / 7 / 1`; trade AP `8 / 1 / 10 / 1`; and broad AP
`10 / 1 / 8 / 1`. Eligible cross-growth relations are AR/revenue 14, inventory/revenue 11,
inventory/COGS 11, and AP/COGS 14. KR non-financial CFS balance-sheet evidence is independently safe
despite the separate cash-flow period-context gap; Korean Re remains not applicable for generic
industrial working capital.

Implementation SHA `0d3b42715fc8964fe053d72e0ecc979fb78b14cc` passes Actions run
`32447178183`, 1,288 full tests, Ruff, deterministic generator hashes, and all safety checks. Open P0
and material P1 are zero. `PHASE_9_1B_READY = YES`; scope is
`SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE`. Main/operating promotion is deferred until the separate
KR natural-window review, not because of an architecture blocker.

## 21I. Phase 9.1B Canonical Working-Capital Core

Phase 9.1B starts from Phase 9.1A final SHA `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
and immutable instruction commit `0952bee040133aa49a4ba494ecae76163e9a9511`. It preserves the
`working-capital-evidence-v1` raw registry and adds derivation version
`working-capital-evidence-v1:canonical-core-v1`.

The core consumes only PIT-visible Phase 9.1A Facts. Each of Inventory, exact trade AR, separate
broad AR, exact trade AP, and separate broad AP independently selects an exact prior-year
same-fiscal-quarter comparable. Safe pairs emit canonical Decimal delta and YoY Facts; compatible
Revenue/COGS pairs emit flow YoY Facts. Six structured relation families preserve the exact balance
metric/semantic/scope, flow semantic, four raw input IDs, two YoY Fact IDs, direction, gap, formula,
version, eligibility, and cautions. The canonical layer emits no quality verdict or causality.

The 20-subject audit exactly reproduces Phase 9.1A metric coverage with zero newly blocked items. It
contains 160 selected reported Facts, 44 delta, 44 balance YoY, 31 flow YoY Facts, and 53 eligible
relations. Arithmetic, provenance, and idempotency errors are zero. Insurance remains N/A and KR
non-financial balance-sheet support remains independent of the OpenDART cash-flow duration gap.

The service is imported only by tests and the read-only evidence generator. User-visible runtime,
AI packet, Telegram, fallback, Public Action 0.4.5, schema 4, DB, task, Pilot, and warning behavior
change by zero. DSO, Inventory Days, DPO, CCC, ROIC, contract assets, inventory components, accrued
liabilities, and prior-quarter lifecycle remain deferred. Open P0/material P1 are zero, so
`PHASE_9_1C_READY = YES`; scope is
`WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY`. Promotion remains deferred for the separate
KR natural-window review.

Implementation SHA `a35c615a77b44b37739d4f6a73aa9f0f290ba831` passed Actions run
`32450301567` Test/Lint plus 1,301 full local tests. Final documentation resolves from Git so the
committed artifact does not attempt to contain its own SHA.

## 21J. Phase 9.1C Working-Capital Shadow Consumption

Phase 9.1C starts from Phase 9.1B final SHA `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
and immutable instruction commit `613d91d74d3a91c43ed61f98a13a2ca57b7a90ae`. The
`working-capital-shadow-consumption-v1` sidecar consumes canonical 9.1B relations without
recomputing balances, growth, or gaps.

Every selected relation requires all six canonical input Facts to be available at the immutable
packet cutoff and to match the latest validated formal balance date. Phase 9.0C freshness evidence
keeps TSM formal-lagging-provisional and suppresses it from current reasoning. Insurance is N/A;
biotech, special financial-like, cloud/software, HPC, broad AR/AP, and AP relations are not forced
into prose when their incremental value is weak.

The replay selects seven relations: five Inventory and two exact Trade AR. Each message owns at most
one percentage-point relation in `business_earnings`; automatic binding is 7/7, manual/rejected/
unresolved and relation arithmetic errors are zero. Exact Trade and Broad semantics remain distinct;
contract assets and accrued liabilities do not leak; unsupported causal claims, DSO, Inventory
Days, DPO, CCC, thesis/valuation/warning mutation, and Unknown contradictions are zero. Human review
classifies seven material improvements, thirteen no-change subjects, and zero degraded subjects.

`PHASE_9_1D_READY = YES` with scope
`SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`. Working-capital user-visible output
remains disabled, Phase 9.0E remains `SELECTIVE_CURRENT_FORMAL_FULL_FCF`, and promotion remains
deferred for the separate KR natural-window review.

Implementation SHA `aba64e85c34db620416ea9ee5cae36c0fe6b31d0` passed Actions run
`32454469417` Test/Lint plus 1,324 full local tests. The archive generator depends only on committed
evidence; an initial CI-only local-SQLite dependency was removed before this passing implementation
SHA was accepted.

## 22. Phase 9.1D Working-Capital Runtime Shadow Canary

Phase 9.1A architecture, 9.1B canonical core, and 9.1C archive consumption are promoted through
main `d0dc76a2446ee5ef9188d1b06dcb241df004c143`. Phase 9.1D adds
`working-capital-runtime-shadow-canary-v1` after terminal production delivery. Its detached archive
is independent from production and from the cash-flow canary.

The runtime scope is total Inventory and exact Trade AR only. The canary filters the canonical
snapshot before reusing the Phase 9.1C PIT, latest-formal/provisional freshness, industry,
materiality, one-insight, Unknown-resolution, renderer, and semantic/causal validator. Broad AR,
all AP, inventory components, DSO, Inventory Days, DPO, and CCC are excluded. A newer formal period
known by the production packet suppresses the older canonical relation instead of substituting it
as current.

The 20-subject parity replay selects the same five Inventory and two exact Trade AR relations with
zero relation drift. Numeric binding is 7 automatic and zero manual/rejected/unresolved; semantic,
causal, quality, and production-influence errors are zero. Implementation SHA
`5316113062782b09595a495ec9a903a4973f9df5` passes 1,330 local tests. Natural proof remains separate:
Inventory and exact Trade AR start at `NOT_OBSERVED`, while the canary state is
`DEPLOYED_PENDING_NATURAL` after clean promotion.

`PHASE_9_1E_ARCHITECTURE_READY = YES`. This is not user-visible enablement. Each metric family needs
its own natural proof before a future user-visible decision.

## 23. Current Roadmap

The development state is `PHASE_9_1D_DEPLOYED_PENDING_NATURAL`. Open P0 and material P1 are zero.
Phase 9.1E architecture may proceed in parallel with natural canary observation, but working-capital
user-visible output remains disabled. Broad AR/AP, AP relations, low-value industries, and all
advanced working-capital day ratios remain excluded or deferred. KR OpenDART cash-flow period
recovery remains a medium follow-up rather than a blocker.

In parallel, observe the next natural US/KR sessions for AI-assisted delivery, ownership,
repetition, night-session integrity, fallback, language, receipt, archive, and exactly-once proof.
Also let the telemetry-only LaunchAgent accumulate natural KRX 16:05 and 08:05 evidence. Do not run
it manually, infer a T+1 slot, or integrate KRX breadth before the separate role gates close.

## 23A. Night-Futures Publication Telemetry Repair

The independent repair starts from instruction commit
`b7cf6a2f413e309bb637e524aeb7c1436e4c5b1b`, then explicitly merges the Phase 9.1D main before
implementation. It adds `night-futures-attempt-archive-v1` and
`night-futures-publication-telemetry-v1` without changing `night-futures-session-basis-v1`.

Each existing 08:05/10/15/20 production attempt now archives the expected NIGHT and preceding XKRX
DAY, every returned `BAS_DD`, HTTP/row/SHA evidence, parser/canonicalization/cross-check state, and
independent KOSPI200/KOSDAQ150 rejection/readiness. Telemetry writes are atomic, idempotent, and
best-effort. The 08:30 backup remains query-free.

A detached LaunchAgent observes only at 08:45 and 09:15, after the production/fallback lifecycle.
It uses the same provider and pairing path, stops after readiness, and can write only telemetry.
Readiness is expressed as an observed interval, never an exact inferred publication time. No
production deadline, provider request, market summary, AI, fallback, Telegram, Public Action,
schema, or DB behavior changes.

Implementation is complete with 61 focused and 1,337 full tests. Natural publication evidence is
still pending, so `P1_TELEMETRY_GAP = REPAIR_DEPLOYED_PENDING_NATURAL`,
`DEADLINE_VERDICT = DEADLINE_UNPROVEN`, and `FAIL_CLOSED_SAFETY = PASS`.

## 23B. KR Investor-Flow Reconciliation Repair

Run-31 exposed a correctness gap between the visible foreign/institution/individual tuple and a
prose attribution that treated those three participants as exhaustive. The official/free provider
also reports other corporations and domestic foreigners as top-level participants; institution
subclasses are diagnostics that sum to the institution total and must never be added again.

`kr-investor-flow-participants-v1` and `kr-investor-flow-reconciliation-v1` preserve the public
three-participant tuple while carrying complete internal 1d/5d/20d reconciliation, explicit signal
basis, omitted-participant materiality, and fail-closed attribution safety. No residual category is
derived. AI and fallback share this state, and unsafe absorber/leader prose is rejected. The run-31
audit closes 21/21 windows and reduces unsupported attribution from two to zero. Public Action
`0.4.5`, schema 4, supply scoring, task settings, Pilot, and production-assist state are unchanged.

Instruction `e9d7c73cf6f25b2423b55a6899465e86441316d1` precedes implementation
`47fc87e2a9189556a7206065fdb759f3603ce497`; Actions run `32480802390` passes Test/Lint. The
bounded repair is `PASS` with open P0/P1 zero. Natural confirmation continues independently.

## 23C. Phase 9.1E Working-Capital User-Visible Pre-Integration

Phase 9.1E starts from immutable instruction commit
`99f7e86f3ae40cc86a4865ef70dc89abf79d5a37` and explicitly reconciles the independently promoted
KR investor-flow main before implementation. It adds `working-capital-user-visible-v1` and
`working-capital-user-visible-enable-gate-v1` as preview-only contracts.

The future modes are OFF, selective Inventory, selective exact Trade AR, and their combination.
Missing/invalid config resolves OFF, and a mode request cannot bypass family-specific natural proof.
Inventory and exact Trade AR remain `NOT_OBSERVED`, so effective operating mode is OFF. A clean
preview is explicitly `PREVIEW_ONLY_NOT_ENABLEMENT_EVIDENCE`.

The 20-subject audit preserves all seven Phase 9.1D candidates and selects five lower-noise future
previews: three Inventory and two exact Trade AR. MU and TSLA are suppressed only because compatible
Phase 9.0E cash-flow context already owns the point and the relation resolves no additional Unknown.
Broad AR and AP selection, parity errors, semantic/causal errors, numeric binding errors, and
production/user-visible diffs are zero. Exact numbers remain owned by `business_earnings`.

`PHASE_9_1E_PREINTEGRATION_READY = YES`. Inventory and exact Trade AR enablement each remain
`NO_PENDING_NATURAL`. After a family reaches natural `LIVE_PASS`, use a small enablement-only
instruction for that family; no new broad architecture phase is required.

## 23D. Phase 9.1E.1 Inventory-Only User-Visible Enablement

Immutable instruction commit `880e7a9834439971f53b8a7bc0712d0ece26854d` precedes the explicit
morning-evidence merge and implementation. Run-32 packet
`2026-08-22-us-run-32-dde10ec6c9eb` selected MU and TSLA total Inventory in the detached 9.1D
canary. Numeric binding was automatic 2/2, semantic and quality errors were zero, and production
influence was zero. This independently upgrades Inventory to `LIVE_PASS`; TSM exact Trade AR was
not selected and remains `NOT_OBSERVED`.

Phase 9.1E.1 reuses `working-capital-user-visible-v1` and permits only
`SELECTIVE_INVENTORY`. The selector is contract-driven, current-formal and PIT-safe, uses total
Inventory only, applies industry materiality and Phase 9.0E cash-flow redundancy, and places one
typed `%p` relation in `business_earnings`. It does not mutate thesis, warning, valuation, Pilot or
DB state. AI and fallback share exact packet/context/relation/Fact/date/scope/direction identity.

The 20-subject replay finds five Inventory candidates, selects KR `000660`, `005490`, and `005930`,
and suppresses MU/TSLA because current cash-flow context already owns the point. Trade AR, broad AR
and AP selected counts are zero. Feature-OFF packet/fallback output is byte-identical to prior main.
`INVENTORY_ONLY_ROLLOUT_READY=YES`. Main/operating promotion and activation completed safely at
12:16 KST with mode `SELECTIVE_INVENTORY`; Inventory is `ENABLED_PENDING_NATURAL`. Exact Trade AR
cannot be enabled in this phase.

## 23E. KR Non-Trading-Day Producer And Delivery Integrity

The 2026-08-22 Saturday Stage A review found that downstream KRX and Codex reviewers safely no-op'd,
but the independent KR producer still ran seven companies, called providers, and created delivery
state before failing on an absent packet. Direct evidence lock corrected the report count: there
were seven stock rows plus one KR digest marker, all unsent and packet-unbound.

Instruction commit `2125562a863d858ee1ab62675c31c7c13be33506` precedes implementation
`c26c9359b134df0a4cd697fd97e7616cc508e885`. The producer now resolves the shared
`xkrx-role-target-v1` role `kr_daily_production` before any stateful work. Active-pilot KR analysis
queues nothing until an immutable packet file exists; queued rows use
`packet-bound-delivery-intent-v1` and remain non-deliverable until held. Retry/fallback selection
requires matching packet ID, market and assessment date.

The controlled `kr-orphan-delivery-reconciliation-v1` command terminalized the exact eight incident
rows as existing status `failed` with reason `non_trading_day_orphan_no_packet`. Sent rows,
`sent_at`, deletion, payload mutation, Telegram, provider recreation and ad hoc SQL were all zero.
Implementation Actions run `32565412721` and the 1,406-test full suite pass.

`KR_PRODUCER_REPAIR_READY = YES`; open P0/material P1 are zero. Deployment state is
`DEPLOYED_PENDING_NATURAL`. A later natural weekend/holiday must prove analysis/provider/packet/
notification/Telegram counts all zero; no manual run is proof. Inventory remains
`ENABLED_PENDING_NATURAL`, exact Trade AR remains OFF, and the next action remains the first
eligible Inventory packet review.

## 23F. Macro Digest Temporal Eligibility

The 2026-08-24 US fallback exposed a Branch B wiring gap: exact observation dates, provider
freshness, and market-session state existed, but downstream digest logic treated source `fresh` as
equivalent to a new daily signal. `macro-digest-temporal-eligibility-v1` now separates current
observations, prior market sessions, reference-lagging observations, stale daily evidence, and
unavailable evidence without a new DB truth store or universal day threshold.

The immutable run-35 replay has zero current observations: 8/21 equity returns are explicit prior
session context, while unchanged FRED/WTI/VIX and the ECOS collection-date USD/KRW item cannot
create important changes, thesis daily signals, shocks, or ticker impacts. The long-term mixed
regime remains valid background. The 8/22 normal after-close replay preserves real current price,
rate, and volatility signals; holiday, mixed-timing, closed-session release, revision, and early-
close fixtures pass. AI and fallback share one contract and the semantic validator rejects false
current wording.

The repair changes no provider, DB schema, Public Action, output schema, task schedule, night-
futures logic, KRX integration, Inventory/Trade-AR mode, valuation, price/RR, Pilot, or Production
Assist. State is `DEPLOYED_PENDING_NATURAL`; replay is not live proof. Observe the next natural US
digest read-only and confirm temporal roles, wording, ticker transmission, receipt, and exactly-once
delivery without a manual task or Telegram send.

## 23G. KR Production Packet / Shadow Gate Separation

Natural KR run 36 on 2026-08-24 completed seven of seven assessments on a valid XKRX production
target, but the historical Shadow activation guard denied packet persistence because 210 internal
investor-flow reconciliation numeric paths were not AI prose-registered. This was Branch C: the
profile/numeric gate legitimately protected AI Shadow claims, but had become incorrectly coupled to
the immutable production packet required by deterministic fallback.

Instruction commit `7da8d8866a9b7aafc8c010424cdbc4192de46cbb` precedes implementation
`64086c4af7735dcbe2fd3f5093f4167952a280e0`. `kr-production-packet-persistence-v1` now admits only
a supported target, complete successful analysis, schema-valid packet, available fallback, and zero
explicit production hard errors. `shadow-cohort-readiness-v1` separately owns profile/numeric AI
claimability and records suppression or exceptions with production influence `none`.

The repaired no-send replay persists one packet, binds digest plus seven stock intents, holds all
eight for fallback, and remains idempotent with zero duplicate packet/intent. AI remains suppressed
while the numeric gate is false. Inventory remains `SELECTIVE_INVENTORY`, Trade AR remains OFF,
macro temporal and investor-flow behavior are unchanged, and Production Assist remains OFF.

State is `DEPLOYED_PENDING_NATURAL`, not live pass. Wait for the first natural eligible KR packet to
prove persistence, eight-message AI/fallback delivery, exactly-once behavior, and zero orphans.

## 24. Codex Work Order Standard

Every work order starts with exact repo/runtime preflight, states base/branch/scope/non-scope,
classifies root cause, defines deterministic contracts, adds positive and negative fixtures,
generates exact artifacts, runs focused and full validation, audits side effects, creates intentional
commits, pushes without force, and verifies Actions for the exact final SHA. Never merge, deploy,
run Scheduled Tasks, send Telegram, or mutate Pilot unless explicitly authorized.

## 25. Human Review Standard

Engineering PASS is not human-quality PASS. Review full final-renderer output for today relevance,
quantitative grounding, comparison, investment meaning, industry fit, delta-first quality,
observer/holder distinction, Unknown, next check, and readability. A wrong number, unsupported
claim, scope error, denied echo, industry mismatch, fabricated threshold, or contradiction is HOLD
regardless of score.

## 26. Pilot / Delivery / Receipt

Pilot is `ai-assisted-pilot-v3`, renderer v3, policy `daily-review-v3.10`, schema 4. Persisted state is
KR 3/5 and US 3/5. `runtime-message-quality-receipt-v2` binds packet, validated output, rendered set,
policy/schema/gate, counts, results, status, and timestamp; delivery metadata binds its whole-file
SHA. Pre-send integrity failure leaves exactly one deterministic fallback eligible. Post-partial
failure stops all further delivery and requires manual intervention.

The natural 2026-08-17 KR packet `2026-08-17-kr-run-23-378ee562573e` was rejected pre-send because
four stocks lacked the required current-price RR Fact and numeric path. Rejected AI sent: 0;
fallback eligibility: preserved; the deterministic fallback later sent 8/8 at 17:10 KST; Pilot
change: 0. This is a packet/numeric-path and Natural Live Validation gap, not a Phase 8.4 renderer
failure.

Phase 8.5.1 traces that failure to weekday-only KRX session handling. 2026-08-17 was an XKRX
substitute holiday, so the actual 2026-08-14 chart was the latest completed session rather than
stale. Exchange-calendar-aware reconstruction restores exact current-price RR Facts and registry
paths for all four affected stocks; three unavailable controls remain unavailable by contract. The
immutable source validation's eight RR missing-path errors fall to zero in replay.

Phase 8.5.2 fast-forwarded the complete 31-commit Phase 8 chain from the prior main
`aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` to code commit
`2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf`; the final promotion documentation commit is
`a8ebb02753e28795f36dbf72c9deb3520f75ed44`. The exact main Actions run passed Test and Lint, the
operating checkout was clean and exact, the API was restarted and healthy, and operating smoke tests
passed. All four Codex Scheduled Tasks remain ACTIVE at 08:15/08:30/16:15/16:55 KST, use policy
v3.10/schema 4, and target the operating checkout. No task was run manually. This is an operating
shadow promotion only: Production Assist remains OFF, AI mode remains shadow, Telegram sends and
Pilot mutations from the promotion are zero, and Natural Live Validation remains OPEN.

The promoted code then ran naturally on 2026-08-18. US packet
`2026-08-18-us-run-24-487c07bde4e1` and KR packet
`2026-08-18-kr-run-25-23b5e31dc20e` both kept numeric and semantic hard errors at zero, but their AI
drafts failed `runtime-message-quality-v1`; deterministic fallback delivered 14/14 US and 8/8 KR.
The KR packet contains complete canonical current-price RR paths for 005490, 010120, 012450, and
086280, so the RR runtime path is now `LIVE PATH PASS`. Full natural AI delivery remains PARTIAL.

Phase 8.5.3 reconstructs both quality failures from immutable archives. The bounded retrospective
correction reduces US literal/skeleton duplicate groups from 3/7 to 0/0 and KR from 5/7 to 0/0,
with no threshold relaxation and full validators PASS. The new deterministic fallback selector
reduces crossed confirmations rendered as future triggers from nine to zero and preserves dynamic
support, resistance, RR, and explicit unavailable reasons. This is archive-only evidence: no
Telegram, task, Pilot, DB, assessment, or archive mutation occurred.

Phase 8.5.3.1 then fixes the remaining Preview UX defects. Immutable replay reduces US Korean
object-particle errors from six to zero, KR malformed actor-flow phrases from two to zero, US
watch/next meaningless overlap from 13 stocks to zero, and KR exact RR Fact exposure at three or
more occurrences from six stocks to zero. Both full validators, runtime quality, and final language
PASS. The complete Phase 8.5.3/8.5.3.1 chain was fast-forwarded to main and the clean operating
shadow checkout at implementation commit `e166aaf6a4c13f9009a3885737d3b48e34c895d5` after exact-SHA
Actions Test/Lint PASS. API health and 154 operating smoke tests pass; all four Codex automations
remain ACTIVE and were not run manually. Production Assist remains OFF and AI mode remains shadow.

Phase 8.5.3.2 traces the RXRX display defect to a numeric registry mapping that collapsed the
historical distribution's current value and historical median into one `historical_pb_multiple`
label. Immutable replay now renders `현재 PBR 1.82배`, `역사적 PBR 중앙값 3.28배`, and
`PBR 역사적 백분위 9.5%`. The same generic repair also closes one WULF legacy collision; portfolio
same-label/different-role collisions are zero. Exact implementation commit
`b3ad1ea82bdbd3fe003831d449b0dcaa7c6a2da2` passed Actions run `32126079970`, was
fast-forwarded to main and operating shadow, and passed API health plus 74 operating focused tests.
Natural AI-assisted delivery is still pending. Run-28 proved live fail-closed night-futures
suppression when no completed current session pair was available; numeric NIGHT-to-preceding-DAY
exposure remains pending natural evidence.

## 27. Production Assist Approval Rules

Production Assist remains OFF. Five operational Pilot successes are not enough. Approval requires
exact-commit CI, full regression, direct human review of natural full messages, zero critical safety
issues, current persistent docs, correct receipts and exactly-once behavior, and explicit user
approval. Main merge and shadow deployment still do not authorize AI-assisted production delivery.

## 28. Current Next Task

Wait for the first natural eligible KR production packet and verify one persisted packet, eight
packet-bound intents, AI or fallback delivery, exactly-once receipt, and zero duplicates/orphans;
do not run a task or send Telegram manually. In parallel, continue the selected Inventory,
macro-temporal, night-futures, investor-flow, and weekend/holiday observations without manufacturing
evidence. Keep exact Trade AR OFF and do not
implement DSO, Inventory Days, DPO, CCC, ROIC, broad/AP output, or KR cash-flow period recovery
without separate authorization.

## 29. New Session Bootstrap Prompt

> First fetch and compare `origin/main`, the current experimental branch, and the operating
> checkout. Read `docs/project-state.json`, `docs/PROJECT_HANDOFF.md`,
> `docs/NEXT_SESSION_PROMPT.md`, `docs/MASTER_WORKFLOW.md`, and the latest validation reports.
> Recover the actual repository, runtime Pilot, Scheduled Task, contract, and Production Assist
> state. If the repository is newer than a commit or statement in this workflow, the repository and
> immutable runtime win and the documentation must be reconciled. Confirm whether a later natural
> US/KR AI-assisted delivery exists after the Phase 8.5.3.2 shadow promotion. Run-26 delivered
> fallback 14/14 while AI was rejected; Phase 8.5.4 closes its blockers retrospectively and Phase
> 8.5.4.2 closes holiday-aware preceding-DAY lookup retrospectively in operating shadow. Natural KR
> run-27 then delivered fallback 8/8 while AI was rejected; Phase 8.5.5 closes its reasoning-owner
> blockers retrospectively. Natural US run-28 delivered fallback 14/14 after the unchanged runtime
> gate rejected generic numeric-summary and RR-delta repetition; Phase 8.5.5.1 closes those blockers
> retrospectively and is operating shadow. Phase 8.3 is finalized as selective optional context
> and must not be reopened without new evidence. Phase 9.0A is architecture-closed and Phase 9.0B
> implements the selective canonical OCF/PPE-CAPEX/FCF core with zero user-visible behavior diff.
> Phase 9.0C closes archive-only PIT/freshness/materiality consumption with zero semantic errors and
> zero user-visible behavior diff. `PHASE_9_0D_READY = YES`. Read
> `docs/architecture/CASH_FLOW_SHADOW_CONSUMPTION.md` and the one-file Phase 9.0C report bundle
> before adding the delivery-isolated runtime canary. Natural AI and KRX exact-slot evidence
> continue independently; do not make either a false prerequisite for 9.0D, and stop for any newly
> observed P0.

## 30. Legacy Macro And Shadow Registry Closure

The 2026-08-24 19:34 KR rehearsal exposed two independent compatibility gaps. Legacy macro
briefings without temporal metadata were fail-opened as current, while 210 exact investor-flow
reconciliation numerics were unknown to the shadow registry. `macro-temporal-legacy-rehydration-v1`
now derives a non-mutating, fail-closed view for legacy evidence and all relevant consumers share
it. The numeric registry now classifies the exact 30 reconciliation paths per KR stock as internal
derived, non-prose evidence; unknown paths still fail closed and production packet persistence
remains independent.

Immutable replay produces one packet, eight held intents, a validated eight-message AI bundle, and
a complete eight-message fallback with zero duplicates, orphans, sends, false-current claims, or
Inventory parity mismatches. This closes retrospective code readiness only. The next action remains
the first natural eligible KR packet; no task or Telegram send may be manufactured for proof.

## 31. Common AI Core v1 Production Integration

The Free Analyst structured analysis, natural packet adapter, evidence-lock validator, and Adaptive
Renderer are now integrated behind `free-analyst-adaptive-production-v1`. Work started from the
immutable instruction commit `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`; implementation commit
`4bcf117fa36d9a74c45e6f9c2626e38e07e52bd3` passed Actions run `32803786800` Test/Lint.

The authoritative Production Assist control plane is type B: Production Assist is a governance
approval state, while the existing Pilot gate is already enabled for validated current AI output.
Free Analyst Adaptive is independently default OFF/current and cannot bypass the Pilot delivery
gate. The bounded canary is at most one market message
and two stock messages. Immutable US run-37 passes 14/14 and KR replay passes 8/8 with all hard
safety counts at zero; the three-message canary simulation passes scoped runtime quality. Full
cohort rollout remains disabled because two generic synthesis sentences form a broad-cohort P2.
Open Research and Event Attribution production integration are zero.

State is `COMMON_AI_CORE_V1=INTEGRATED_READY_NOT_ARMED`, open P0/material P1 are 0/0, Production
Assist remains OFF, and the next action is a separate explicit canary enablement decision. Natural
runtime evidence, KR packet proof, Inventory observation, and telemetry continue independently.

## 32. Common AI Core v1 Limited Canary Enablement

The explicit canary instruction is fixed at
`73802b8849f674698bfdb3bfd7f3d0df89c236b2`. Preflight reran the immutable selector and selected
one market plus two stock messages with scoped runtime quality PASS and zero hard safety errors.
The operating Settings now use `FREE_ANALYST_ADAPTIVE_ENABLED=true` and
`FREE_ANALYST_ADAPTIVE_MODE=free_analyst_adaptive_canary`, with hard maxima `1/2/3`.

Production Assist governance remains OFF, the existing Pilot remains enabled and unchanged, and
full Free Analyst mode remains OFF. Open Research/Event Attribution, exact Trade AR, Inventory,
cash-flow, schedules, Public Action, schema, DB, and fallback were unchanged. State is
`COMMON_AI_CORE_V1=INTEGRATED_CANARY_PENDING_NATURAL`. Do not run production manually; inspect the
first eligible KR natural packet, then the next eligible US packet. Any delivered P0 disables only
the new canary through its independent kill switch.
