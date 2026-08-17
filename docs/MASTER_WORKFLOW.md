# Thesis Monitor Master Workflow

Master Workflow: `v2`
As of: `2026-08-17`
Repository: `sskim-ai/thesis-monitor`
Operating branch: `main`
Release evidence branch: `codex/phase-8-5-2-shadow-release-promotion`
Commit resolution: run `git rev-parse HEAD`; this document is part of that commit and must not
hardcode a self-referential final SHA. Phase 8.5.1 code commit
`2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf` is promoted to `origin/main` and the clean operating
checkout configured for thesis-monitor.

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

KRX remains `PENDING_PROVIDER_APPROVAL` and is the intended primary. Kiwoom remains an unconfigured
Windows-gateway `bridge_shadow`; it is not an authoritative KRX replacement. Automatic metric-level
fallback requires five same-date reconciliation sessions and explicit universe/unit comparability.
Market-wide KR investor flow remains unavailable.

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
| Natural live validation of Phase 8 code | OPEN |
| Current-price RR packet/numeric path | PARTIAL |
| Human-approved Production Assist evidence | INSUFFICIENT |

Closed engineering gaps include numeric provenance, canonical formatting, financial quality taint,
security identity fail-closed, field-level financial lineage, unsafe growth blocking, integrated
full messages, valuation scope, denied echo, decision-material delta, historical retention,
valuation-context wording, observer/holder foundation, Unknown/next-check foundation, receipt
integrity, fallback/retry, and exactly-once accounting.

## 22. Current Roadmap

Default next: observe the next natural KR session and verify that the repaired current-price RR path
passes packet completeness, the full validator, receipt, archive, and exactly-once checks. If KRX
approval is explicitly confirmed first, Phase 8.2A KRX Market Breadth Primary may be inserted.
After checking the next natural US/KR results, proceed to Phase 8.3 Peer/Sector Valuation and
structured taxonomy enrichment, natural-live quality validation, and a separate production decision.

Do not keep subdividing mature safety infrastructure or Phase 8.4 message assembly without a real
regression. The current priority sequence is better industry coverage, peer context, KR breadth,
and natural-live evidence.

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
immutable source validation's eight RR missing-path errors fall to zero in replay. The gap is
PARTIAL, not CLOSED, until a new natural KR session proves the path end to end.

Phase 8.5.2 fast-forwarded the complete 31-commit Phase 8 chain from the prior main
`aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` to code commit
`2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf`. The exact main Actions run passed Test and Lint, the
operating checkout was clean and exact, the API was restarted and healthy, and operating smoke tests
passed. All four Codex Scheduled Tasks remain ACTIVE at 08:15/08:30/16:15/16:55 KST, use policy
v3.10/schema 4, and target the operating checkout. No task was run manually. This is an operating
shadow promotion only: Production Assist remains OFF, AI mode remains shadow, Telegram sends and
Pilot mutations from the promotion are zero, and Natural Live Validation remains OPEN.

## 26. Production Assist Approval Rules

Production Assist remains OFF. Five operational Pilot successes are not enough. Approval requires
exact-commit CI, full regression, direct human review of natural full messages, zero critical safety
issues, current persistent docs, correct receipts and exactly-once behavior, and explicit user
approval. Main merge and shadow deployment still do not authorize AI-assisted production delivery.

## 27. Current Next Task

Inspect the next naturally generated US and KR results from the promoted operating shadow checkout.
For KR, verify the repaired current-price RR path without manual execution or replay. For both
markets, verify framework routing, full validation, receipt, single delivery/fallback, archive, and
exactly-once state before human message review. KRX status remains pending or unknown from repository
evidence; if explicit approval becomes available, report whether Phase 8.2A should be inserted before
Phase 8.3 peer/sector work. Missing metrics remain Unknown and industry conditions never become
company achievements.

## 28. New Session Bootstrap Prompt

> First fetch and compare `origin/main`, the current experimental branch, and the operating
> checkout. Read `docs/project-state.json`, `docs/PROJECT_HANDOFF.md`,
> `docs/NEXT_SESSION_PROMPT.md`, `docs/MASTER_WORKFLOW.md`, and the latest validation reports.
> Recover the actual repository, runtime Pilot, Scheduled Task, contract, and Production Assist
> state. If the repository is newer than a commit or statement in this workflow, the repository and
> immutable runtime win and the documentation must be reconciled. Confirm whether the next task is
> natural-live proof of the repaired RR path or whether newly approved KRX access makes Phase 8.2A
> KRX Market Breadth Primary the immediate priority. Report the recovered state before editing.
