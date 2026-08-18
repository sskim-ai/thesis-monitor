# Thesis Monitor Master Workflow

Master Workflow: `v2`
As of: `2026-08-18`
Repository: `sskim-ai/thesis-monitor`
Operating branch: `main`
Latest evidence branch: `codex/phase-8-5-3-2-rxrx-valuation-label-repair`
Commit resolution: run `git rev-parse HEAD`; this document is part of that commit and must not
hardcode a self-referential final SHA. Resolve `origin/main` and the clean operating checkout at
session start. Phase 8.5.3.2 passed immutable US/KR replay and was promoted to operating shadow;
natural AI-assisted delivery remains pending.

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

KRX Open API is approved and Phase 8.2A now has an experimental archive-only provider on
`codex/phase-8-2a-krx-market-breadth`. It reuses `market-cross-section-v1` and
`market-breadth-v1`, validates exact session/identity/unit semantics, and computes explicit
KOSPI/KOSDAQ common-share breadth. The 2026-08-14 dry run produced 2,532 eligible rows from 2,763
daily rows with 76/76 numeric registry entries supported. It is not merged, registered, scheduled,
or deployed. Phase 8.2A.1 confirms the universe implementation already required `LIST_DD` strictly
before the session plus a positive comparable previous close; the reversed capability wording was a
documentation error, and the denominator stays at v1. `krx-publication-readiness-v1` now separates
market-not-completed, provider-pending, partial, complete, error, and stale states. The completed
2026-08-18 session still returned empty HTTP 200 across all four core endpoints at 20:27 KST, so no
current snapshot was promoted and first-complete publication remains unobserved. KRX Open API does
not provide market-wide investor flow or security-level sector breadth; selected KOSPI 200/KOSDAQ
150 industry indices remain price proxies only. Kiwoom remains an unconfigured Windows-gateway
`bridge_shadow`; automatic fallback requires five comparable sessions. See
[KRX_MARKET_BREADTH.md](architecture/KRX_MARKET_BREADTH.md).

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
`runtime-message-specificity-v1` plan selects each stock's decision point, company evidence,
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
| 8.2A development | KRX primary-candidate provider, explicit universe, index/breadth Facts, archive Preview and numeric provenance PASS; experimental only, not deployed |
| 8.2A.1 | Listing-date contract CLOSED with unchanged denominator; publication-readiness state machine PASS; current complete observation still pending; experimental only |

## 21. Current Persistent Gaps

| Gap | Status |
|---|---|
| Industry-specific investment reasoning | STRONG PARTIAL |
| Structured specialized taxonomy coverage | PARTIAL |
| Peer/sector valuation | OPEN/PARTIAL |
| KR market breadth | PARTIAL |
| KR market-wide flow | OPEN |
| Massive 08:05 readiness | OPEN |
| OCF | PARTIAL |
| CAPEX aggregation | OPEN |
| FCF | OPEN |
| Natural live validation of Phase 8 code | PARTIAL |
| Current-price RR packet/numeric path | LIVE PATH PASS |
| AI natural-live message quality | PARTIAL: retrospective PASS, natural AI delivery pending |
| Fallback dynamic-price lifecycle | CLOSED: retrospective PASS and operating code promoted |
| KRX Open API primary breadth | HISTORICAL PASS; UNIVERSE CLOSED; CURRENT READINESS PARTIAL; NOT INTEGRATED/DEPLOYED |
| KRX market-wide investor flow | UNSUPPORTED by approved Open API; remains Unknown |
| KRX security-level sector breadth | OPEN; sector-index price proxies only |
| Human-approved Production Assist evidence | INSUFFICIENT |

Closed engineering gaps include numeric provenance, canonical formatting, financial quality taint,
security identity fail-closed, field-level financial lineage, unsafe growth blocking, integrated
full messages, valuation scope, denied echo, decision-material delta, historical retention,
valuation-context wording, observer/holder foundation, Unknown/next-check foundation, receipt
integrity, fallback/retry, exactly-once accounting, and valuation comparison-label collisions.

## 22. Current Roadmap

Default operating task: observe the next natural US/KR sessions for actual AI-assisted delivery,
final-language quality, receipt, archive, fallback, and exactly-once proof. Phase 8.2A KRX Market
Breadth Primary is implemented and archive-validated on an experimental branch only. Phase 8.2A.1
closes the universe contract and finalizes the Preview, but current-session readiness remains PARTIAL
because no complete normal-session publication has been observed. Promotion waits for live baseline
review, user Preview review, and a current-session complete provider proof. Phase 8.3 Peer/Sector
Valuation follows unless a new operating blocker takes priority.

Do not keep subdividing mature safety infrastructure or Phase 8.4 message assembly without a real
regression. The current priority sequence is natural AI delivery proof, KRX breadth, peer context,
and broader natural-live evidence.

## 23. Codex Work Order Standard

Every work order starts with exact repo/runtime preflight, states base/branch/scope/non-scope,
classifies root cause, defines deterministic contracts, adds positive and negative fixtures,
generates exact artifacts, runs focused and full validation, audits side effects, creates intentional
commits, pushes without force, and verifies Actions for the exact final SHA. Never merge, deploy,
run Scheduled Tasks, send Telegram, or mutate Pilot unless explicitly authorized.

## 24. Human Review Standard

Engineering PASS is not human-quality PASS. Review full final-renderer output for today relevance,
quantitative grounding, comparison, investment meaning, industry fit, delta-first quality,
observer/holder distinction, Unknown, next check, and readability. A wrong number, unsupported
claim, scope error, denied echo, industry mismatch, fabricated threshold, or contradiction is HOLD
regardless of score.

## 25. Pilot / Delivery / Receipt

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
Natural AI-assisted delivery is still pending.

## 26. Production Assist Approval Rules

Production Assist remains OFF. Five operational Pilot successes are not enough. Approval requires
exact-commit CI, full regression, direct human review of natural full messages, zero critical safety
issues, current persistent docs, correct receipts and exactly-once behavior, and explicit user
approval. Main merge and shadow deployment still do not authorize AI-assisted production delivery.

## 27. Current Next Task

Inspect the next naturally generated US and KR results without manual task execution. Verify AI
specificity, Korean language, watch/next separation, numeric dedup, current price-context parity,
full validation, receipt, single delivery/fallback, archive, and exactly-once state before human
message review. Review the committed Phase 8.2A.1 universe audit, readiness report, validation,
audit, and final market Preview. Its provider remains experimental and archive-only; promotion waits
for the natural baseline proof, user Preview review, and at least one current-session complete
observation. Phase 8.3 peer/sector work follows.
Missing metrics remain Unknown and industry conditions never become company achievements.

## 28. New Session Bootstrap Prompt

> First fetch and compare `origin/main`, the current experimental branch, and the operating
> checkout. Read `docs/project-state.json`, `docs/PROJECT_HANDOFF.md`,
> `docs/NEXT_SESSION_PROMPT.md`, `docs/MASTER_WORKFLOW.md`, and the latest validation reports.
> Recover the actual repository, runtime Pilot, Scheduled Task, contract, and Production Assist
> state. If the repository is newer than a commit or statement in this workflow, the repository and
> immutable runtime win and the documentation must be reconciled. Confirm whether a later natural
> US/KR AI-assisted delivery exists after the Phase 8.5.3.2 shadow promotion. If not, the next task
> is read-only natural proof review. Also inspect the experimental Phase 8.2A KRX reports and branch;
> do not call it integrated or deployed. Once live proof and KRX Human Review pass, decide whether to
> promote Phase 8.2A. Report the recovered state
> before editing.
