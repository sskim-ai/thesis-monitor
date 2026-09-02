# Thesis Monitor Master Workflow

Master Workflow: `v31`
As of: `2026-09-01`
Repository: `sskim-ai/thesis-monitor`
Operating branch: `main`
Latest evidence branch: `codex/20260901-v2-natural-cli-path-product-identifier-repair`
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

## 0. V2 Natural CLI Path and Product-Identifier Provenance Repair

Exact instructions were committed first as
`b2c0a4af72c5eb060dcdacd8b281e30307c717f1` on base
`1aa10f04016cabede492c82686b6d671b4c27f55`. Implementation
`b5be74439b2e8e769b1605e539599835abbc8a84` closes two independent natural-runtime defects without
changing decision policy. All Codex CLI subprocess paths now resolve from the canonical repository
root, the schema is preflighted before the model call, writable parents are created deterministically,
and persisted claims retain portable relative paths. The same path contract serves primary, backup,
KR, US, test, and natural entry points.

The numeric lexer recognizes only canonical evidence-owned product identifiers as identifier spans.
It excludes those exact spans from numeric validation while continuing to validate adjacent real
numbers and reject unproven hyphen-number text. No `KF-21`/`FA-50` allowlist, KR-only exception, or
validator relaxation exists. Frozen run 50 passes `8/8`, the production-equivalent US path passes
`14/14`, and the dedicated non-production sink received `22/22 exact` after identity-aware 429
continuation. Production recipient sends, production delivery intents, duplicate and orphan messages,
scheduler changes, Price Structure numeric changes, and valuation numeric changes are all zero.

Focused tests are `270 PASS`; full pytest is `2045 PASS`; Ruff, diff, message quality, and the
implementation GitHub Actions Test/Lint run pass. Open P0/material P1 are `0/0`. Clean linear
promotion completed through `26004d926247c4ef053e49b74dc8fb9654353199`; branch Actions
`33507836260`, main Actions `33508187986`, API health, and operating parity pass. State is
`DEPLOYED_AWAITING_NATURAL_US_KR_LIVE`, not natural LIVE_PASS. Inspect the next ordinary KR and US
cycles read-only. Do not replay an already delivered production packet, manually run a Scheduled
Task, or use the production Telegram recipient for proof.

## 0. Malformed OHLC Provider Integrity

Exact instructions were committed first as `235cf78d5c386da0f5c02284b373b911ef1b7647` on base
`813beb6345fc2c6643018b33f568702b50fab37d`. Implementation
`a6707b82cb9d46c2895560ff07fd14d1bf8c2dc9` adds
`ohlcv-provider-integrity-v1`: every normalized provider response is checked before feature
construction, one malformed-content refetch is allowed, and repeated malformed content remains
unchanged and INVALID. Invalid rows now remain in the packet raw fingerprint and exact integrity
events retain sanitized row values and hashes. No clipping, swapping, ticker exception, threshold
change, or synthetic OHLC repair exists.

Direct provider probes classify CPNG as `STABLE_BAD_SOURCE` and HUT as
`INTERMITTENT_BAD_SOURCE`; both remain INVALID. MU and SKHY are
`TRANSIENT_PROVIDER_DEFECT` controls whose current raw responses are valid, so run-49 replay is
FULL 12 / INVALID 2. All 14 US decisions and all 8 KR decisions are accepted-ready with message
quality PASS. The dedicated sink passed 22/22 exact after a rate-limit continuation, with zero
production sends or intents. Full pytest is 2019 PASS; open P0/material P1 is 0/0. Report commit
`9c6919a2e35905defe380f7adcd7f0d454887abd` passed GitHub Actions run `33473079100`, was
fast-forwarded to main and operating, and passed API/OHLCV health. The deployed state is
`DEPLOYED_AWAITING_NATURAL_US_LIVE`; the natural pass remains pending and must be observed
read-only.

## 0. OHLCV Technical Context Resilience

Exact work instructions were committed first as
`1dd691a340b4961e105371af53142c76db7385d7` on base
`f7c4331e7aa34eeb87e0627fb7e79ee27a1cbfa7`. The root cause was
`PROCESS_NAMESPACE_MISMATCH`: the host OHLCV LaunchAgent was healthy while a restricted decision
process could not open the loopback socket. The repaired V2 path consumes validated
`packet-owned-technical-context-v1`, uses bounded recovery, and isolates malformed or unavailable
technical data by subject. It does not perform a duplicate decision-stage OHLCV HTTP fetch.

Run-49 isolated replay passed `14/14`, the dedicated US sink passed `14/14 exact`, KR run-48
remained FULL `8/8`, and the Korean-particle/Russell 2000 provenance false positive is closed
without an allowlist. Complete report commit `3efe688bb7eaa41bc084061c9eb9de910d86423a`
passed Actions run `33464969356` and was promoted by clean fast-forward. API and OHLCV health are
PASS; open P0/material P1 is `0/0`. Natural US `LIVE_PASS` is not inferred from replay or the test
sink. The next action is read-only observation of the next ordinary US cycle.

## 0. V2 Accepted Decision Ownership

Exact work instructions were committed first as `4662c08` on base
`29bdd4cf378438fedad7f602b4b8ede80c46dd44`. Tracks A/B/C implement deterministic accepted
ownership through `f55605189ee0179ab4af7030b94d79d706ed32a8`. Raw candidate and adjudication artifacts are
immutable history; after a material disagreement the only summary, renderer, validator, test-sink,
and readiness authority is `accepted_plan` under `v2-accepted-decision-ownership-v1`.

The raw candidate distribution remains BUY `2`, HOLD `14`, SELL `4`. The frozen adjudicated result
is BUY `1`, HOLD `16`, SELL `3`: keep v1 for `003690/SNDK`, and keep v2 for `GOOGL/HUT/RXRX`.
Rejected `003690` pre-confirmation BUY semantics cannot leak into accepted output; `GOOGL` remains
the sole accepted pre-confirmation BUY. Missing required adjudication fails closed as `NOT_READY`
and never silently falls back to either candidate.

The accepted renderer and validator passed all 20 subjects. The dedicated sink passed `20/20 exact`
with zero production recipient sends/intents and no recipient identifiers retained. V1 production
canary state and user-visible output are unchanged. Open P0/material P1 is `0/0`, and
`V2_MIGRATION_RECOMMENDATION=READY_WITH_OBSERVATION`. The next action is review of accepted V2
messages; this repair does not authorize production migration.

## 0. Pre-Confirmation Asymmetry Decision Engine V2

Exact work instructions were committed first as `46bdf4c` on base
`1359a5769c36d64dd5e0acc9bbf03f90578fb062`. Track A/B/C/D implementation is fixed through
`c0c9139babb06ead11112aea072a67ef364a9b22`. The archive-only engine adds driver-level evidence
maturity, pricing requirement, Bear/Base/Bull scenarios, asymmetry, confirmation cost,
pre-confirmation error cost, and explicit pre-confirmation BUY/post-confirmation HOLD semantics.
There is no fixed score or maturity-to-decision map.

The same 20 canonical evidence packets were reviewed label-blind with signed-in Codex CLI
`gpt-5.6-sol / xhigh`. V2 produced BUY `2`, HOLD `14`, SELL `4`; `003690` and `GOOGL` were
pre-confirmation BUY candidates. All 20 candidates and messages passed. Five v1/v2 disagreements
were adjudicated: keep v1 for `003690/SNDK`, keep v2 for `GOOGL/HUT/RXRX`; open P0/material P1 is
`0/0`.

The dedicated test sink passed `20/20 exact` with zero production recipient sends, intents,
duplicates, orphans, or raw recipient identifiers retained. Historical confirmation-delay outcome
diagnostics remain `NOT_AVAILABLE` because canonical PIT outcome/estimate series are not archived;
look-ahead leakage and alpha claims are zero. `V2_MIGRATION_RECOMMENDATION=READY_WITH_OBSERVATION`.
V2 production exposure is still zero and the exact v1 canary remains unchanged. Review the v2
shadow decisions before creating any separate bounded migration instruction.

## 0. Bounded Cross-Market Decision Canary

Exact work instructions were committed first as `c62ddff`; implementation is
`a639d326a578bb7f3a2c53b1df31723bfb2b9829`. The production decision surface is limited to KR
`003690,000660` and US `GOOGL,RXRX`. Current natural classifications are `HOLD/HOLD/HOLD/SELL`;
current BUY is zero and no BUY was forced. Signed-in Codex CLI uses `gpt-5.6-sol / xhigh`.

The dedicated test sink received four current production-equivalent messages plus two explicitly
historical BUY fixtures `6/6 exact`. Production recipient sends/intents, duplicates, orphans,
unowned retries, order language, Price Structure numeric changes, and non-canary decision blocks
are all zero. Identical-evidence model churn found in the first fresh pass is closed by the
`cross-market-decision-canary-continuity-state-v1` gate; rejected attempts remain archived.

The bounded state is `ENABLED_AWAITING_NATURAL_PROOF`, with open P0/material P1 `0/0`. Natural
evidence is still KR `0/2` and US `0/2`, so expansion is `HOLD`. Do not manually run tasks or send
production messages to manufacture proof. Wait for two ordinary cycles per market; genuine BUY
live proof may remain pending until a natural BUY occurs.

## 0. Cross-Market Decision Quality Review Before Canary

Exact instruction commit `86829a52c4711e1fad632cc9f558a44c08cc2ddc` precedes review
implementation `cd829ff8009759af7f5c73e487e43c06dc4b1a9c`. The review reused the exact
canonical evidence SHA `7649e675...b938720b`, hid all baseline labels during the independent pass,
and ran signed-in Codex CLI `gpt-5.6-sol` with `model_reasoning_effort="xhigh"`. Web enrichment,
future outcomes, fixed scores, order language, production sends, and runtime mutation were zero.

The baseline `BUY 2 / HOLD 18 / SELL 0` became independent `BUY 2 / HOLD 13 / SELL 5`. All five
HOLD-to-SELL disagreements were adjudicated on the same packets. CRCL and HUT returned to HOLD;
RXRX, TSLA, and WULF remained SELL. Final review distribution is `BUY 2 / HOLD 15 / SELL 3`.
Cross-market semantics pass, MACD alone owns no decision, and no class balance was forced.

The quality gate is `NOT_READY`: HOLD-default and SELL-suppression bias are `MATERIAL`, while
confidence, timing, and decision-change-condition calibration need bounded repair. Open P0/material
P1 are `0/4`. Production canary stays OFF and engine state stays `TEST_SINK_READY`. The next action
is `BOUNDED_REPAIR`, followed by a fresh review; this report does not authorize a canary.

## 0.1 Cross-Market AI Decision Engine v1

The exact instruction commit is `ec6ea8fa4449fd34961ecbbcf995064c46ff94a2`; implementation is
`f28d4bb3b8eacebe7fb48a3ca7800094711793eb`. The new archive/shadow-only engine builds a canonical
D/W/M OHLCV feature catalog, per-stock evidence packets, and AI-owned analytical BUY/HOLD/SELL
classifications. Signed-in Codex CLI ran `gpt-5.6-sol` with `model_reasoning_effort="xhigh"`.

Current shadow decisions pass `20/20` with `54/54` automatic numeric bindings, zero unresolved
numeric claims, and zero substantive cross-ticker repetition. The immutable temporal replay passes
`200/200` with look-ahead leak and unexplained churn both zero; it remains honestly `PARTIAL_SAFE`
because full historical D/W/M bars and forward 20/60/120 outcome diagnostics are not archived.
The dedicated non-production sink received `20/20` exact payloads after a bounded 18+2 rate-limit
continuation, with duplicate/orphan and production recipient send/intent all zero.

`DECISION_ENGINE_STATE=TEST_SINK_READY` and its original technical canary gate passed with open
P0/material P1 `0/0`. The later independent decision-quality review above supersedes actual canary
readiness as `NOT_READY`. Production packet consumption, scheduled prompts, fallback, DB,
assessments, and automated trading remain unchanged.

## 0. Latest One-Shot KR Close Live Proof

The operator-authorized proof starts from exact instruction commit
`a0d8f190a0dd2105925810bcf21eeb1d483e0277` on operating main
`23b17c487a4c0ae7dc56935e9028cf62f2b00f2c`; the evidence implementation is
`239db58958b1193a8fd591500618ee4e7940c994`. Preflight passed with a clean operating checkout,
healthy API/OHLCV services, a completed 2026-08-28 XKRX target, seven active KR subjects, no active
KR producer, no residual one-shot, and open P0/material P1 `0/0`.

Exactly one temporary LaunchAgent reused the regular KR close ProgramArguments and working
directory. It was loaded at `18:39:55 KST`, ran once at the `+300s` boundary, exited `0`, and was
removed before another interval. The normal `16:05/16:20/16:50` plist and SHA remained unchanged.
The producer created packet `2026-08-28-kr-run-44-e4cf532e619b`, refreshed current Kiwoom market
context with `42/42` successful requests, and held eight packet-owned intents. Because the regular
17:10 deadline had already passed, the existing KR fallback command completed that same packet
through the normal notification service without a second producer run or direct Telegram call.

The production notifier sent one KR market message and seven stock messages `8/8`. Persisted
rendered text and content SHA match the exact archived messages for all eight; duplicates, orphans,
unowned retries, and pending deliveries are zero. The live KR market surface, all seven V3 stock
messages, price labels, price-anchored major S/R, completed/provisional Bollinger roles, and
validator ownership pass. For `000660`, the selected near support rendered and the unselected
weekly dynamic resistance remained a materiality omission without reviving
`fallback_dynamic_resistance_not_rendered`. `FINAL_V3_VALIDATOR_CONVERGENCE=LIVE_PASS` and the
next default action is the still-pending natural US market/Price Structure review.

## 0.1 Run-44 V3 Validator Convergence Baseline

The task starts from exact instruction commit `1e8a008368ab79c44213545da192edbc5a545c98`
on operating main `026df711fa151cc7816b2a57d9ed7d224c1b33cf`. Permanent controls were
implemented at `aa5e7d4a799a1e2093bca6f87ff09f19c19e94a9`. The prior readiness
metadata that ended at `d3a58c9` was stale only: `d3a58c9` is the direct parent of `026df71`, and
the operating checkout and `origin/main` agreed at task start.

Exact frozen replay of packet `2026-08-28-kr-run-44-4606feed1396` now passes on the latest runtime.
For `000660`, V3 selects the structure close and near support with daily Bollinger confluence, while
the weekly dynamic resistance is intentionally `OMITTED_BY_MATERIALITY`. The current fallback
validator does not recreate that omitted obligation. Removing an actually selected standalone or
confluence fact still fails, and V3-off legacy behavior is unchanged.

KR `7/7`, US/foreign `13/13`, and the 22-message cross-market dedicated test-sink batch pass.
Rendered, outbound, and received hashes match for all messages; production sends/intents,
duplicates, and orphans are zero. The first 20-message batch hit Telegram rate limiting, and a
bounded continuation sent only the two unsent messages. Runtime-visible diff is zero, so no runtime
hotfix or restart is required. Open P0/material P1 is `0/0`. This retrospective state was
`READY_NO_RUNTIME_CHANGE`; the operator-authorized live proof above has since closed the KR side as
`LIVE_PASS`, while natural US proof remains pending.

## 0A. Latest Major Structural S/R Reality Gate

The repair starts from exact instruction commit `4a5702823da3f950b9f125bcbcfecd7c6cfa84df`
and implementation `c5f1fbcb9c952c2d14ad0b178a9b33351d15b512`. The shared
`major-sr-price-anchor-reality-gate-v1` contract requires confirmed Pivot, Balance Box, or verified
equivalent observed-price provenance before any zone may render as `주요 구조 지지/저항`.
Bollinger/Fibonacci/projection evidence remains available only as confluence after that anchor.

One fixed adjusted-OHLCV capture was replayed against the old base and repaired code. The repaired
result passed US `13/13` and KR `7/7`; visible dynamic-only major zones fell from 18 to zero, all 21
remaining visible majors have anchor and basis provenance, and near-S/R was unchanged `20/20`.
GOOGL's old monthly Bollinger-only support `$267.08~$268.43` is omitted and resistance
`$424.82~$426.96` is replaced by an actual balance-box anchor.

The dedicated non-production sink received 20 exact stock messages with zero production-recipient
sends, duplicates, orphans, or delivery intents. Operating promotion, API/OHLCV health, and the
post-deploy `13+7` replay pass. Open P0/material P1 are `0/0`. The gate is
`DEPLOYED_AWAITING_NATURAL_PROOF`; do not manually run a task or production Telegram. Review the
next natural stock messages read-only.

## 0B. Latest US Macro Exact-Payload Quality Repair

The bounded repair starts from instruction commit `e59c0e6a0574824bd512c1d4c06775b0afe1e468`
and implementation commit `535855631890928a9dd9e798e12adbeabde74df2`. Run-43 exposed two
independent defects: `market_sector_relative` escaped a negative macro exclusion and generated
`변화 없음했습니다`, while the old quality report asserted absence without validating the
received Telegram payload.

The plan now positively selects verified macro Fact families, omits generic zero/no-material
change, and lets the final renderer rebuild only specific, temporally bound macro prose from the
canonical Fact. `us-morning-exact-payload-quality-v1` validates the Telegram response text and
requires received/quality/report SHA parity. The immutable bad SHA fails as expected; one isolated
market-only test message passed with stock sends, production sends/intents, duplicates, and orphans
all zero. KR TOP3, KR Price Structure, and US Price Structure remain ON; AI mode is shadow and
Production Assist is OFF.

The repair is `DEPLOYED_AWAITING_NATURAL_PROOF`, with P0/material P1 `0/0`. Review the next natural
US morning message read-only; do not manually run a task or send production Telegram.

## 0C. Previous US Market And Price Structure Rollout

The rollout starts from instruction commit `2ee201690787136780c7d5c8a046506d44227633`
and implementation commit `1ba463571060a1fc9a5868afcdeab3de15f2bbe6`. The
`us-morning-full-message-v1` renderer owns the deterministic SPY/QQQ/IWM/SOXX/RSP block,
RSP participation, strongest/weakest sector evidence, and optional temporally safe night-futures
or macro context. Adaptive refinement may replace only the bounded next check; stored legacy plans
cannot promote market-relative facts to macro.

The `us-price-structure-selective-rollout-v1` gate applies the existing Price Structure v3 engine
to the active US/foreign universe without ticker allowlists. The 2026-08-27 completed-session replay
passed all 13 subjects as `ELIGIBLE_SR_ONLY`: exact numeric binding, AI/fallback parity, current-vs-
stored-rule separation, completed-bar safety, and USD listed-security identity all passed. One full
market message and all 13 stock previews reached the dedicated non-production sink exactly once;
production-recipient sends and production delivery intents were zero.

US Price Structure is enabled independently of the existing KR flags. Post-enable replay remains
13/13 PASS, API health is PASS, Production Assist remains OFF, and open P0/material P1 are `0/0`.
The state is `ENABLED_AWAITING_NATURAL_PROOF`, not `LIVE_PASS`. Wait for the next naturally
scheduled US morning market and stock cycle; do not run a task or production Telegram manually.

## 0D. Latest KR Market Formatting State

The bounded `📊 시장 내부` formatting repair starts from instruction commit
`dd1b5eb712081c222bcfe1b4465d4fe0aac5f89a` and implementation
`03a418ab1f616d0063becf3928a1327056dd2d66`. Canonical size, strong-sector, and weak-sector
tuples now render as standalone KOSPI/KOSDAQ bullet rows in both adaptive and deterministic paths.
Run-42 retains all values, TOP3 order, evidence selection, and numeric provenance.

One production-equivalent market message reached the dedicated non-production sink exactly once;
renderer, outbound, and received payload hashes matched. Stock test sends, production-recipient
sends, delivery intents, duplicates, and orphans were zero. KR TOP3 and KR Price Structure remain
ON; US Price Structure and Production Assist remain OFF. The state is
`DEPLOYED_AWAITING_NATURAL_PROOF`, with open P0/material P1 `0/0`. Wait for the next natural KR
market message; do not trigger a manual task or production Telegram.

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

Investment Knowledge v3.1 governs business, earnings, valuation, expectations, industry, macro,
risk, and monitoring safety.

SHA-256: `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312`

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

## 33. Common KR/US Market Adapter v1

Work instruction `c058839c5e63a08c096bd6a9a1b2139290d17eb0` first closed the run-38 KR
valuation numeric-ref blocker on a separate track. The adapter implementation commit
`7a210efe101547c1981b934fbf3dc867bc3e6426` then added `market-context-adapter-v1`,
market-specific KR/US normalization, research seed hints, and an explicit production research
connector boundary.

The common contract, Fact boundary, schema parity, unit gates, temporal gates, and deterministic
relation provenance pass. KR and US are both safe `PARTIAL`: KR run-38 has no local structured
index/breadth/market-flow evidence, while US run-37 has SPY/QQQ/IWM, SOXX, and two verified
relative relations but no breadth or participant flow. Missing remains Unknown. Neither replay
receives provider recollection or a fabricated value.

The structured adapter sidecar is production-pending-natural and does not change Public Action,
output schema, fallback, Telegram shape, canary limits, or packet identity. A production Open
Research connector is `NOT_AVAILABLE`, so `OPEN_RESEARCH_LIVE_CANARY=BLOCKED_CONNECTOR` and runtime
research integration remains zero. The next action is the naturally scheduled 2026-08-26 US
structured-adapter canary review; do not run a task or send Telegram manually.

## 34. Structured Data Acquisition First And Message Quality v2

Instruction commit `e04403c76abfd8d2f74ca91d438fccc54b479bad` supersedes the earlier
message-only bounded repair. Implementation commit `1a6d2f411e7fa9ef414197a3fa5711b336a0d3e7`
adds `structured-market-context-v1`, exact publication/session/freshness provenance, fail-closed KR
cross-section capture, and a broader free US style/sector context. It also adds `message-quality-v2`
without changing the existing `1/2/3` canary limits or enabling full mode.

KR acquisition is safe `PARTIAL`: the exact 2026-08-25 KRX slot returned HTTP success but no rows,
so the packet records publication pending and exposes no invented index, breadth, or market-flow
number. The prior-session capability probe confirms KOSPI/KOSDAQ stock and index coverage, but its
numbers are not substituted for the current session. US acquisition is safe `PARTIAL`: RSP and all
11 sector SPDRs provide current structured style/sector evidence, while exchange breadth and
participant flow remain unavailable.

Immutable run-37/run-38 replays pass `14/14` and `8/8`. Generic synthesis lines fall from `36` to
`0`, duplicate substantive messages from `18` to `0`, and all `245` numeric claims bind
automatically with zero hard-safety errors. KR structured-context value-add is
`NO_MATERIAL_VALUE` for the pending publication; US value-add is `PASS`. Both message-quality v2
gates pass. Promotion keeps missing data Unknown, Production Assist OFF, Open Research integration
at zero, and full Free Analyst mode OFF. The next proof is the naturally scheduled US structured
quality-v2 canary, followed by KR when a complete publication exists; never manufacture either run.

## 35. Kiwoom KR Market Context v1

Instruction commit `f45c6c9d47253c0ad8cad9affcf0eb54be188117` adds an official Kiwoom REST
integration on the existing `market-cross-section-v1`, `structured-market-context-v1`, and
`market-context-adapter-v1` chain. Implementation commit
`32178dc5b2cd4a5fd38af51514b4ac5d12d1cbd0` validates KOSPI/KOSDAQ index and breadth,
KOSPI size, sector context, and six market-wide foreign/institution/retail flow Facts for the
completed 2026-08-25 session.

`ka10051` aggregate amounts normalize at KRW 100 million per source unit and fully paginated
`ka10066` stock amounts at KRW 1 million per source unit. KOSDAQ reconciliation is within the
aggregate representational unit and supports provenance-bound descriptive concentration. KOSPI
reconciliation remains `UNRESOLVED_BASIS_OR_TAXONOMY`, so KOSPI concentration is blocked while its
validated aggregate direction remains available.

Immutable run-38 replay passes 8/8 with 123 existing automatic bindings, zero new exact numeric
prose claims, zero semantic hard errors, and a material market-digest improvement. The production
adapter is safe `PARTIAL`: collection failure cannot block packet creation, KRX telemetry remains
independent, full mode remains OFF, canary remains 1/2/3, Open Research production remains zero,
and Production Assist remains OFF. The next action is the first naturally scheduled eligible KR
proof; no manual task or Telegram send may manufacture it.

## 36. KR Post-Deployment Rehearsal And US Exchange Breadth v1

Instruction commit `d7a01015617b3fbfb16f4194d1d02c41004a4197` fixes the exact work bundle before
execution. The KR rehearsal independently recollected the completed 2026-08-25 session through the
deployed Kiwoom path. A bounded session guard repair now compares the target with the
calendar-derived latest completed regular session, allowing valid post-midnight recollection while
still rejecting older/current incomplete sessions. All 42 calls succeeded, the source SHA exactly
matched prior stable evidence, and immutable run-38 passed 8/8 with a 1/2/3 canary simulation and
all hard safety counts at zero.

US breadth extends the existing common market adapter with official NasdaqTrader year-to-date
advances, declines, and unchanged counts under exact scope `NASDAQ_LISTED_ISSUES`. Derived net,
shares, and A/D relations preserve source scope and provenance. Provider failure is supplemental
and fail-open. The run-37 target session is 2026-08-24, but the retrieved official file is published
only through 2026-08-20; run-37 therefore remains 14/14 with breadth suppressed and no historical
substitution. The published 2026-08-20 row proves parser, arithmetic, adapter, and classification
value separately. NYSE remains unavailable rather than derived from a partial universe.

State is safe `PARTIAL` and production-ready with P0/material P1 at 0/0. Full Free Analyst remains
OFF, canary limits remain 1/2/3, Open Research integration remains zero, Trade AR and Production
Assist remain OFF. The next action is read-only natural KR proof plus the first US packet whose
exact completed-session Nasdaq row is published; do not manufacture either observation.

## 37. KR Digest Priority And US Entity-Specific Synthesis

Instruction commit `8cf5226ca0c5ae5553fb06b24399462ea3cf6088` and implementation commit
`f2326c39485e600bca2cee15747deeb8465c5c8a` close the final bounded message-quality repair before
Open Research connector work.

`kr-market-digest-quality-v1` keeps a rich completed-session KR context local-first through
judgment, interpretation, and next check. Richness requires KOSPI/KOSDAQ indices, reconciled scoped
breadth for both, and at least one of market flow, size/style, or sector evidence. Global context is
retained only for material contradiction. KOSPI concentration remains blocked; safe KOSDAQ
concentration is optional rather than mandatory.

`entity-specific-synthesis-v1` and `cross-message-synthesis-specificity-v1` require supported
drivers without ticker sentence hard-coding. Shared structure is allowed inside a real industry
cohort; generic cross-industry reuse with available specific support is canary-ineligible per
message. Immutable KR/US replays pass 8/8 and 14/14, cross-industry generic repetition is `4 -> 0`,
and all hard safety counts are zero.

Keep Free Analyst full mode OFF, canary `1/2/3`, Open Research production integration `0`, Trade AR
OFF, and Production Assist OFF. Natural proof continues read-only and independently. With no new
P0/P1, stop message-polishing iterations and continue to the Open Research production connector
and selective event-attribution integration.

## 38. Fibonacci Variable AI Anchor Bounded Closure

Instruction commit `d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890` fixes the exact P1 closure
scope. `price-only-ai-anchor-packet-v1` carries bounded completed OHLCV, deterministic candle
features, canonical pivot/SR IDs, candidate neighborhoods, and swing segments with no prior anchor
or precomputed Fibonacci. `variable-ai-swing-anchor-selection-v1` returns IDs only; backend
validation, Decimal Fibonacci, confluence, and per-timeframe deterministic-SR fallback remain
authoritative.

The actual signed-in variable runtime executed five independent runs for the two-KR/two-US
benchmark and three for every other active monitored packet. Egress, runtime availability,
deterministic arithmetic, provenance, look-ahead, and KR/US schema pass with no user-visible change.
However, material variation remains for monthly `3/20`, weekly `11/20`, and daily `10/20`; four
timeframes also required semantic fail-closed rejection. Material full-debug candidate omission is
zero, so rich packet coverage is bounded `PARTIAL`, not an information-loss failure.

State remains `AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE=SHADOW` and
`PRODUCTION_ENABLEMENT_READY=NO`. Open P0 is zero. The open material P1 is limited to variable
higher-timeframe anchor/SR stability and ambiguous/insufficient output semantics. Do not widen
canonical tolerances or arm production. A future bounded repair may separate variable Fibonacci
anchor judgment from deterministic SR ownership and rerun the same frozen 5/3 protocol. This
feature-local P1 does not block the independent Open Research roadmap or natural monitoring tracks.

## 39. Fibonacci Anchor/SR Ownership And Consensus Closure

Instruction commit `39cab7ed8b1cb3bebea1bd1240498caa454bd09a` fixes the final bounded P1 scope;
implementation commit `0dfef76bba606f018893d6e68e7beaf410aa7438` adds the archive-only consensus
core. `fibonacci-sr-ownership-v1` makes support/resistance deterministic backend property and
removes SR from variable-AI output. The AI selects only backend-enumerated
`canonical-swing-structure-candidate-v1` IDs or returns a typed valid abstention.

The same frozen public-price universe ran with the prior 5/3 protocol through 17 actual signed-in
runtime calls. Runtime and semantic failures are zero. Valid abstentions are 56 with zero wrongful
rejections. Monthly/weekly/daily SR variation is `0/0/0`; stable Fib consensus remains selective at
`10/7/11`, while 13 materially unstable and 19 insufficient timeframes are safely omitted. All 28
eligible Fibonacci timeframes preserve deterministic arithmetic and provenance, and unstable
user-visible eligibility is zero.

`AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE=INTEGRATED_READY_NOT_ARMED` and
`PRODUCTION_ENABLEMENT_READY=YES`. This is permission for a separately instructed bounded
multi-timeframe Fibonacci enablement, not activation. Production imports, Telegram, scheduled
tasks, Public Action, assessment state, price rules, tolerances, and Production Assist remain
unchanged. The independent Open Research and natural monitoring tracks continue under Phase
Advancement Rule v1.

## 40. Price Structure Wave Fibonacci Engine v3

Exact instruction commit `5bcf2a1a73a10c73db12c37e93a51652983599d5` precedes implementation
commit `63b3ce219f996ea23b0a2a254d842bbb579adef2`. The v3 archive-only core supersedes the
generic per-timeframe Fib concept with completed adjusted OHLCV, monthly primary-wave candidates,
weekly endpoint confirmation, independent monthly/weekly/daily SR maps, wave-owned Fibonacci
families, and final cross-timeframe synthesis. AI makes ID-only selections and cannot calculate
technical prices.

The 20-stock frozen replay made 20 successful local provider calls. Weekly 600 passes for 12 and
monthly 300 passes for eight; shorter listings remain explicit partial/fail. Daily 1200 is partial
for all 20 because the current `/ohlcv` interface caps requests at 1000. The deterministic engine
produces three confirmed primary hypotheses, 11 ambiguous results, and six valid no-impulse
results. Seventeen signed-in archive-only model calls yield 14 stable selections and six stable
abstentions with zero runtime failures, semantic rejections, or unstable Fib eligibility.

The quoted SK hynix reference and v3 primary method materially disagree at W0-W2, while the user
reference source archive itself was not supplied. Therefore `SK_HYNIX_REFERENCE` is
`MATERIAL_METHOD_CONFLICT`, `PRICE_STRUCTURE_WAVE_FIB_V3=SHADOW`, and
`PRODUCTION_ENABLEMENT_READY=NO`. Open P0 is zero; the two material P1s are the daily provider cap
and the SK method conflict. Keep production SR, packets, Telegram, tasks, schema, assessment state,
and Production Assist unchanged. The next action is a bounded feature-local repair, not live
enablement.

### 40.1 Temporal, History, Degree, And Feedback Bounded Repair

Exact bounded-repair instruction commit `82cb04e2880d1ed7b0405e1ddd20c5f333305394` precedes
implementation commit `bea877d3a6a9977c19832cbde28ed235676929d2`. The repair adds
exchange-calendar `COMPLETE/PARTIAL` bar state, provider-native daily pagination with a canonical
cache identity, separate grand/current/intermediate candidate sets, and strict variable-AI
selection feedback into deterministic Fib, SR, confluence, and shadow rendering.

SK hynix's August monthly bar is partial at the frozen observation time, so the June high and July
low are provisional. The current-cycle set independently surfaces the 2023-01 W0 candidate; older
2015/2016 candidates remain grand-cycle context. Fourteen signed-in archive-only calls have zero
runtime/semantic rejection and zero selected-but-not-fed results. Seven subjects are stable, six
safely abstain, and seven material-variation subjects remain shadow-only and user-visible
ineligible.

Provider-native continuation gives 1200 completed daily bars for 14 long-listed subjects; six
short-listing histories are safe partial. Dedicated weekly/monthly coverage remains selective and
is never fabricated. `PRICE_STRUCTURE_WAVE_FIB_V3=INTEGRATED_READY_NOT_ARMED` and selective
`PRODUCTION_ENABLEMENT_READY=YES`, with open P0/material P1 at `0/0`. This permits only a separately
instructed bounded enablement of stable eligible subjects. Current production SR, packet,
Telegram, tasks, Public Action, assessment state, and Production Assist remain unchanged.

### 40.2 Hypothesis Equivalence And Fibonacci Family Consensus

Exact instruction commit `b0f81c8e16f588e314f93eb6097370e85f285241` precedes implementation
commit `631e82f202b6f081866ef83c8b67b2138a8b51d8`. The repair adds deterministic
`wave-hypothesis-equivalence-class-v1`, `fib-family-endpoint-dependency-v1`,
`price-structure-v3-ambiguity-set-v1`, `fib-family-consensus-v1`, and
`family-filtered-confluence-v1` contracts. Fibonacci stability is now evaluated only across the
endpoints each family actually depends on. Unstable family sources are removed before confluence;
the existing price tolerance and deterministic SR ownership remain unchanged.

The original material cohort is `000660`, `003690`, `005490`, `005930`, `010120`, `TSLA`, and
`TSM`. Eleven signed-in archive-only calls cover five material-cohort, three stable-control, and
three abstention-control runs, totaling 74 ticker decisions with zero runtime or semantic failure.
The 20-subject replay passes KR `7/7` and US/foreign `13/13`; prior stable regression, forced
abstention selection, dependency mismatch, correlated-Fib inflation, and unstable confluence are
all zero.

SK hynix remains full-hypothesis `MATERIAL_VARIATION`, but six endpoint-dependent families are
safe: current rebound and W3 retracement are exact invariant; primary-cycle retracement and two W5
projection families are price equivalent; one additional W5 family is exact invariant. W1
retracement remains material and is omitted. The supplied reference engine is retained byte-audited
under `docs/reference/user-wave-engine/` as `REFERENCE_ONLY / NOT_PRODUCTION_RUNTIME`, and the
endpoint/confirmation comparison is `REFERENCE_MATCH`. TSLA's true conflict and TSM's W3-dependent
conflict remain material.

`PRICE_STRUCTURE_V3_FAMILY_CONSENSUS=INTEGRATED_READY_NOT_ARMED`, code correctness is PASS, and
selective production-enablement readiness is YES with open P0/material P1 `0/0`. This authorizes
only a separately instructed bounded family-selective enablement. Production imports, SR, packet,
Telegram, task schedules, Public Action, assessments, and Production Assist remain unchanged.

### 40.3 Pre-Enablement Membership And Display Micro-Repair

Exact instruction commit `38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8` precedes implementation
commit `84f8f549bc8fa0338309a84b23b2738f2e357646`. The
`family-consensus-membership-audit-v1` contract limits the active family universe to hypotheses
actually selected across runs or explicitly returned as `AMBIGUOUS` competitors. An alternative
attached to `SELECTED` remains diagnostic unless another run promotes it through one of those
active paths. Wrong-ticker, same-ID, unknown, and wrong-degree alternatives fail validation.

The same immutable protocol runs 11 signed-in archive-only calls: three repeats for the exact
seven-stock prior-stable cohort, five for the seven difficult controls, and three for valid
abstentions. Runtime and semantic failures are zero. Stable baseline/evaluation is `7/7`, artificial
regression is zero, and `012450` moves from family `FAIL` to `PASS` with diagnostic contamination
zero. TSLA's true conflict, TSM's W3 conflict, and SK hynix's raw structural resistance remain
unchanged.

Investment Knowledge v3.1 synchronizes internal history defaults to daily 1200, weekly 600, and
monthly 300 while preserving the compact Public Action/no-raw-OHLCV boundary. Technical-zone
formatting is display-only: raw `Decimal` values and all calculations stay unchanged, while SK
hynix's high-price KRW resistance renders as `약 186.9만~191.6만원`. State remains
`INTEGRATED_READY_NOT_ARMED`; selective enablement readiness is YES with open P0/material P1
`0/0`. No production import, Telegram, task, Public Action, assessment, or Production Assist state
changes in this repair.

### 40.4 Deterministic SR Completeness And Active Relevance

Exact instruction commit `7267ca1d3e518d39986941bfda1d6447560db344` precedes final code
implementation `176f3e73eb097fac99f4038a8987b610954804cc`. The shadow v3 core now uses
`deterministic-sr-base-layer-v1` and `sr-proximity-relevance-gate-v1`: monthly, weekly, and daily
base SR is selected before optional wave/Fib; nearest applies a quality floor then proximity;
major applies active relevance then structural importance; current-zone and timeframe-fallback
ownership are explicit.

The immutable 20-subject replay passes KR `7/7` and US/foreign `13/13`. Remote historical
cross-zones no longer displace local nearest SR for `010120`, `MU`, `TSM`, or no-wave `SNDK`.
`003690` and `HUT` recover valid daily resistance that had been excluded when optional Fib occupied
combined-map structural slots. SKHY remains a legitimate short-history monthly insufficiency. SK
hynix's family-stable Fib/SR resistance remains `about KRW 1.869M-1.916M`, `012450` remains stable,
and TSLA receives no unstable Fib.

`PRICE_STRUCTURE_V3_SR_COMPLETENESS=INTEGRATED_READY_NOT_ARMED`, code correctness is PASS, and
selective production-enablement readiness is YES with open P0/material P1 `0/0`. This authorizes
only `BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`. Production imports, current
messages, Telegram, tasks, Public Action, assessment state, price rules, tolerances, and Production
Assist remain unchanged.

### 40.5 Current-Data End-to-End Shadow Message Validation

Exact instruction commit `688c17280a10e91214d4bd9888522fdc6f9bc0c5` precedes the archive-only
validator implementation `ef586c3816ff76417d2620636975d054935533d4`. The active 20-subject
universe was recollected read-only from the official free Kiwoom path. The completed-session gate
uses KR `2026-08-26` and US `2026-08-25`; all 13 incomplete US `2026-08-26` daily stubs are
excluded before analysis, and current weekly/monthly partial context is rebuilt only from completed
daily observations.

The exact candidate archive contains 20 baseline/candidate messages and numeric bindings for every
new technical range. KR eligibility is `6 ELIGIBLE / 1 ELIGIBLE_SR_ONLY`; US/foreign is
`4 ELIGIBLE / 9 ELIGIBLE_SR_ONLY`; omit and blocked counts are zero. Human review classifies 16
material improvements, four minor improvements, no added-value regressions zero, and worse zero.
All 10 mandatory controls pass. Wrong-session data, mixed-session structure, look-ahead, partial-bar
pivot confirmation, remote-nearest promotion, fabricated fill, unstable Fib exposure, unregistered
technical numbers, business-text change, and runtime-visible change are all zero.

`PREENABLEMENT_CURRENT_DATA_VALIDATION=PASS` and the recommendation is `ENABLE_SELECTIVELY`, but
this validation does not arm production. The only authorized next feature-local action remains
`BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`; Telegram, tasks, Public Action,
assessments, price rules, Production Assist, and current runtime imports remain unchanged.

### 40.6 Renderer Ownership Integration Micro-Repair

Exact instruction commit `2ac7eaaede9cb8d9047173bbec5f2bd99c665573` precedes implementation
commit `4246efb4f8afa3516402d1df7864967c177ac6e7`. The pure
`price-structure-v3-renderer-ownership-v1` contract preserves material Fib/SR range extensions,
separates current completed-session structure from `chart:stored_price_rules`, and suppresses stale
parallel technical prose without changing the surrounding business sentence.

The same 20-subject current-data dataset replays with unchanged eligibility: KR
`6 ELIGIBLE / 1 ELIGIBLE_SR_ONLY`, US/foreign `4 ELIGIBLE / 9 ELIGIBLE_SR_ONLY`, and zero blocked.
SK hynix retains major resistance `about KRW 1.869M-1.879M` while displaying the full safe Fib/SR
range `about KRW 1.869M-1.916M`. SNDK and TSM keep current SR and stored management rules under
separate headings. MU retains its business thesis and removes only the stale 2026-08-12
OHLCV/MACD sentence. TSLA remains SR-only and `012450` retains its stable family range.

All renderer ownership, provenance, calculation-parity, business-parity, temporal, and isolation
counters are zero. Human review remains 16 material improvements, four minor improvements, and
zero worse. `PRICE_STRUCTURE_V3_RENDERER_INTEGRATION=INTEGRATED_READY_NOT_ARMED` and
`PRODUCTION_ENABLEMENT_READY=YES`; only the separately instructed
`BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT` may arm production.

### 40.7 Legacy Technical Detector False-Positive Micro-Repair

Exact instruction commit `97b65fc1d258339563b54961a83acd997867e11e` precedes implementation
commit `3685aa991589ca0e7cc560104d4ebf8289e3f91d`. The
`legacy-technical-token-detection-v1` contract replaces whole-message substring scanning with
semantic-field classification, complete indicator-token boundaries, existing freshness checks,
and sentence-level suppression. Company identity, status lines, and section headings are protected
before lexical matching.

The immutable 20-subject replay restores `🏢 Recursion Pharmaceuticals(RXRX)` and changes no other
prior-renderer message text. Ordinary words produce zero technical matches, while RSI/MACD/OHLCV
with Korean postpositions remain valid. MU still removes exactly one stale 2026-08-12 technical
sentence and retains its business thesis.

All entity, structure, nontechnical-suppression, SR/Fib, eligibility, provenance, temporal, and
runtime-isolation counters are zero. State remains `INTEGRATED_READY_NOT_ARMED` with
`PRODUCTION_ENABLEMENT_READY=YES`; a separate bounded selective-enablement task is still required.

### 40.8 Master Market Validation Gate

Exact master instruction commit `e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d` split the work into
US pipeline repair, KR natural review, and conditionally gated Price Structure v3 enablement.
Track A implementation `505a3a2c63390c683323192b7ca516513dfe7a24` closes stale pending-packet
claim ownership, preserves level-only RSP without directional leakage, propagates current sector
state, and binds release observations to their source dates. Its 2026-08-25 replay passes with
natural reproof still pending. Combined validation repair `65196d2d2a54483143d23d1c61500f70d0e2325a`
preserves legacy KR adapter payload compatibility.

Track B observed natural KR run 40 and confirmed packet integrity, official Kiwoom breadth/flow,
safe reconciliation suppression, and 8/8 exactly-once delivery. It also found two material P1s:
the sent digest omitted same-session KR local market evidence, and 378 sector breadth numeric paths
were absent from the AI registry. Open P0 is zero, but Track B is `MATERIAL_P1_FOUND_STOP`.

The master gate therefore keeps Price Structure v3 `INTEGRATED_READY_NOT_ARMED`; Track C was not
created and production was not armed. The next bounded task is
`BOUNDED_KR_LOCAL_FIRST_AND_NUMERIC_REGISTRY_REPAIR`, followed by immutable run-40 replay and a new
natural KR proof. Natural US reproof continues in parallel. Manual Telegram, scheduled-task,
pilot, database, archive, and Production Assist mutations remain zero.

### 40.9 Bounded KR Local-First and Numeric Registry Repair

Exact instruction commit `f6ba660048d3fa520e3aeb43d04036c119764292` precedes Track A
`3828c2093ede67ab2f61c6fceb13a670b22931db`, Track B
`d6c766543205ee74f2c4023cd17a0bfd682b4a7f`, and integrated implementation
`848eb80f6ce6504a9a855973b591ee0749167514`. The deterministic KR digest now consumes one shared
local-first plan: KOSPI/KOSDAQ direction and breadth are the minimum sufficient primary block,
aggregate investor flow is participant-owned, and size/sector leaders are bounded supplements.
Prior/global context is explicitly secondary.

The exact registry preserves listed, advance, decline, and unchanged sector counts as prose-safe
semantics and keeps limit counts audit-only. No wildcard or inferred semantic is admitted. The
integration also fixes cross-market same-name sector fact collisions by including taxonomy,
market scope, and sector code in deterministic fact identity.

Immutable run 40 replay changes numeric registration from `1583/1961` with 378 unsupported paths
to `1961/1961` with zero unsupported paths. Final policy classifies 1,472 paths prose-allowed and
489 denied; reconciliation remains `UNRESOLVED_BASIS_OR_TAXONOMY`, concentration claims remain
suppressed, and the AI readiness gate passes with P0/material P1 `0/0`. State is
`REPLAY_PASS_NATURAL_REPROOF_PENDING`: wait for the next natural KR close without a manual run.
Track C remains `DO_NOT_START`, Price Structure v3 remains `INTEGRATED_READY_NOT_ARMED`, and
Production Assist stays OFF.

### 40.10 US Morning Natural Market Data Review

Exact instruction commit `5377d5e4f15a82e01ac40b6d50d47eee9ef0a30c` governs the read-only
review of natural US run 41 and packet `2026-08-27-us-run-41-ae4f42c23abc`. The run used the
completed `2026-08-26` US regular session and delivered one market digest plus 13 stock messages
exactly once. Packet claim, primary/backup lease transfer, temporal normalization, numeric
registration, final validation, runtime receipt, Nasdaq exact-session publication boundary, and
payload identity all pass.

The packet contained current SPY, QQQ, IWM, SOXX, RSP, and 11 directional sector facts plus one
XLC level-only fact. The AI market review selected only real yield, WTI, and nominal yield; the
concise delivered digest selected only the date-labeled 8/25 real-yield observation. The
deterministic fallback shares this omission. Seven required material rows are lost and the issue is
`us_current_session_market_evidence_omitted_from_natural_digest`, a material P1. Track A is
`BOUNDED_REPAIR_REQUIRED`; perform no repair inside the review. The next separately instructed task
is `BOUNDED_US_MARKET_REPAIR`. Natural KR proof continues independently, Track C remains
`DO_NOT_START`, v3 remains unarmed, and production safety settings remain unchanged.

### 40.11 Bounded US Current-Session Market Evidence Repair

Exact instruction commit `c17f67a5d385b51d1249aa7b3d5452207938f084` precedes independent
Track A implementation `c4b02a10c2b7da0184c7dba26c7c1db39344f258`, Track B implementation
`2f7d6853605541a81e430754d7b6fea98ccbbbea`, and integrated implementation
`069f002437163bff1df7aa6e258918c1777d5dfa`.

`us-market-digest-plan-v1` establishes one current-session-first evidence plan for structured AI
and deterministic fallback. The semantic order is current market, RSP participation/style, sector
dispersion, official breadth, then macro context. Near-flat SPY/QQQ/IWM/SOXX observations remain
primary; RSP is never called exchange breadth; current directional sector leader/laggard ranking is
calculated once in the backend plan; level-only sectors and unavailable breadth stay fail-closed.

`market-evidence-utilization-validator-v1` checks plan slots, canonical refs, and structured
interpretation refs without keyword scanning or numeric-dump requirements. On immutable run 41,
the historical macro-only digest fails with core, RSP, sector, and macro-substitution errors. The
repaired concise AI and fallback candidates share plan SHA
`8761a2f65a3ae6b429f1d7feb0a4ab67bd5120ca0d27526ed9fc6f9b570ce8ef` and pass with all material
loss counters zero.

State is `REPLAY_PASS_NATURAL_REPROOF_PENDING`, with open P0/material P1 `0/0`. Do not claim
`LIVE_PASS` from replay. Wait for the next naturally scheduled US morning run and inspect its
packet, shared plan, route, exact delivery, evidence utilization, receipt, and exactly-once state
read-only. Natural KR reproof remains independent. `PRICE_STRUCTURE_TRACK_C=DO_NOT_START`, Price
Structure v3 remains `INTEGRATED_READY_NOT_ARMED`, and Production Assist remains OFF.

### 40.11.1 US Current-Session Repair Natural Reproof

Exact instruction commit `18d36852f74a6a1609365cbcb5dc093feb293e71` governs the read-only
review of natural US run 43. Operating SHA `910e2f7e78b3d5445e5caa46c605fa85a76c43b2`
produced packet `2026-08-28-us-run-43-c086d78415ac` for the completed `2026-08-27` session.
The `codex-us-primary` automation owned the sole claim, completed one permitted same-claim
correction, and the backend dispatcher delivered one digest plus 13 stock messages `14/14`
exactly once.

The final digest consumes SPY, QQQ, IWM, SOXX, RSP, and the XLK/XLP sector extrema from the shared
plan. Official Nasdaq exact-session breadth remains `PUBLICATION_PENDING`, with latest published
source session `2026-08-25`; RSP is not substituted. Macro temporal roles pass, lagging WTI/FX/
dollar facts are not phrased as current, and macro does not replace market structure. Archive,
persisted delivery, and receipt-linked payload hashes match. Material information loss is zero,
US Price Structure remains OFF with zero leakage, and open P0/material P1 are `0/0`.

Therefore `US_MORNING_NATURAL=LIVE_PASS` and `US_TRACK_A=LIVE_PASS`. One non-rendered optional
MACRO_CONTEXT label/mapping issue remains P2. Next action is `REVIEW_MASTER_GATES`; no bounded US
market repair is open and Production Assist remains OFF.

### 40.12 KR Afternoon Natural Market Reproof

Exact instruction commit `107f40b0b6b7e794f420534e71b69af0c969e643` governs the read-only
review of natural KR run 42. Operating SHA `a1fb1a7006109f8699e03997662bde27db5ad464`
produced the final immutable packet `2026-08-27-kr-run-42-5d8d23e6fbd6` for the completed
2026-08-27 XKRX session. The 16:55 backup claimed it, final validation and runtime quality passed,
and the 17:10 dispatcher delivered one digest plus seven stock messages `8/8` exactly once.

Kiwoom acquisition is complete at `42/42`: ka20001 preserves index-versus-breadth semantics,
ka20003 preserves size/sector returns and component counts, ka10051 owns aggregate participant
flow, and ka10066 completed 14 KOSPI pages plus 19 KOSDAQ pages without duplicate identities.
Today's six aggregate-versus-paginated comparisons remain
`UNRESOLVED_BASIS_OR_TAXONOMY`; concentration relations and prose remain zero. The packet numeric
registry is `1989/1989` registered with zero unsupported paths. The required sector-count inventory
is `252/252` registered supported paths plus 126 intentional internal-only paths.

The exact AI digest is KR local-first: it consumes KOSPI/KOSDAQ direction, both breadth states, and
all foreign/institution/retail directions. Size and sector detail are safely omitted from the
concise message and retained by deterministic fallback. Archive, persisted delivery, and
receipt-linked rendered payloads match; KRX official secondary publication remains pending with no
stale injection. Open P0/material P1 are `0/0`, so `NATURAL_KR_REPROOF=PASS` and the bounded KR
repair is independently `LIVE_PASS_RUN42`.

This does not start Track C. The separate bounded US repair still requires one new natural US
morning reproof, so `PRICE_STRUCTURE_TRACK_C=DO_NOT_START` and Price Structure v3 remains
`INTEGRATED_READY_NOT_ARMED`. Production Assist stays OFF; review-triggered Telegram, Scheduled
Task, DB, assessment, and production behavior changes are zero.

### 40.13 KR Size / Sector Message Selection Bounded Repair

Exact instruction commit `794c6f5d956d0928eac0113d658fede58b1266dc` precedes implementation
commit `6a54db130e95e25969a5ca0a100648d4a12c3aa2`. The run-42 review proved the
source, registry, and local-first path, but its prior brevity policy allowed safe same-session
size/style and sector extrema to disappear. That historical `OMITTED_SAFE` conclusion is retained
as an immutable observation but is no longer valid under the new user-facing selection policy.

`KrMarketDigestPlan` now marks complete size/style and relative sector-extrema slots
`SELECTED_REQUIRED`. It renders KOSPI large/mid/small, KOSDAQ100/MID300/SMALL, and at most one
relative-strong and one relative-weak non-empty sector per available market. The backend owns
selection, ranking, signs, formatting, and evidence refs. AI and deterministic fallback consume
the same claims after index, breadth, and participant flow; global context yields first.

Immutable run-42 replay makes the old message fail as expected and makes repaired AI/fallback pass
with six size refs and four sector refs. Numeric registry policy, provider acquisition, flow
reconciliation, concentration, US digest policy, Price Structure v3, business thesis, archives,
Telegram, tasks, DB, assessments, and Production Assist are unchanged. Open P0/material P1 are
`0/0`; state is `REPLAY_PASS_NATURAL_REPROOF_PENDING`, not `LIVE_PASS`. Wait for the next natural
KR close and verify required detail, local-first ordering, provenance, receipt, duplicates, and
orphans read-only. The separate US natural reproof remains pending and Track C remains
`DO_NOT_START`.

### 40.14 KR Market Pre-Enable Test-Send Gate

Exact instruction commit `f161bc1c724cfd431efaaa458af61e02a378daeb` precedes audit-only
implementation `7d2823c236c458cf76c77faae043c6288e46e65e`. The immutable production packet
`2026-08-27-kr-run-42-5d8d23e6fbd6` remains the completed-session owner. Its stored 42/42 Kiwoom
acquisition, 1,989/1,989 numeric registry, local-first plan, and repaired AI/fallback size-sector
selection all replay PASS without an additional provider call.

The operating environment and all thesis-monitor LaunchAgents expose only the production Telegram
recipient; no dedicated test/staging/developer chat is configured. The safety gate therefore sets
`TEST_SINK_AVAILABLE=NO`, `TEST_DELIVERY_COUNT=0`, and `ENABLEMENT_ACTION=DO_NOT_ENABLE`. Production
Telegram, delivery intent, tasks, DB, assessments, archives, US policy, Price Structure v3, and
Production Assist remain unchanged. The pre-existing size/sector policy is already active by code
default and was neither re-armed nor reverted, so its state remains
`ACTIVE_AWAITING_NATURAL_PROOF`.

Open P0 is zero. The one material operational P1 is `dedicated_test_sink_not_configured`. The next
bounded action is to configure one explicit test recipient that differs from production, then rerun
this preflight exactly once. A production recipient must never substitute for that proof.

### 40.15 KR TOP3 Sector and Price Structure Selective Pre-Enablement

Exact instruction commit `0c95ddc9be319dbacc5ce1d824802e0c3c72fed1` precedes guarded
implementation `a7de99c2d1d1211615e0fcbf4bd3eadc06d957fb`. Track A expands the backend-owned
same-session sector ranking to strong/weak TOP3 per KOSPI and KOSDAQ with stable ties, no stale
carry-forward, no duplicate fill, and explicit exclusion of KOSDAQ size, company-classification,
KOSDAQ 150, and Global indexes. Track B wires the existing Price Structure v3 engine and renderer
behind a default-OFF monitored-KR guard. Current SR remains separate from stored monitoring rules;
Fib renders only after family-consensus safety.

Run-42 replay selects KOSPI strong `전기/전자, 금속, 제조`, KOSPI weak
`유통, 전기/가스, 음식료/담배`, KOSDAQ strong `금융, 전기/전자, 기계/장비`, and KOSDAQ weak
`오락/문화, 출판/매체복제, 통신`. Current completed-session price evidence classifies all seven
monitored KR subjects `ELIGIBLE_SR_ONLY`; no unstable Fib, target, stop, look-ahead, or partial-bar
pivot leaks.

Track C did not send because no dedicated non-production Telegram sink exists. Track D therefore
did not start. Both new guards remain OFF, US Price Structure remains OFF, delivery and production
intent counts are zero, and operating user-visible behavior is unchanged. Open P0 is zero; the one
material P1 is `dedicated_test_sink_not_configured`. Configure exactly one isolated test sink and
rerun Track C before any KR-only enablement.

### 40.16 KR Daily History and Nearest-Semantics Bounded Repair

Exact instruction commit `0a8dae7eeca7126844094f0aebcc7a7df0bea606` precedes independent
Track A `da82d89c2e1c3bc125442128da1573d532263d74`, Track B
`83f3d643bc2cb40d9039c1d965647d01a43769e2`, and integrated code
`04fb7ad7646a55e03000134f50b3f402a6c49c87`. Track A proves the seven monitored-KR daily zero
count came from requesting 1,200 bars from an `/ohlcv` endpoint capped at 1,000. The client now
requests at most 1,000 while preserving the canonical 1,200-bar target and reports all seven daily
series `PARTIAL/provider_limit`; it does not synthesize daily bars or substitute weekly/monthly
data.

Track B separates mathematical nearest-zone ownership from user-visible proximity. Only
`NEAR/ACTIVE_NEAR` may render as `가까운`; `RELEVANT/ACTIVE_STRUCTURAL` renders as `주요 구조`,
and `LONG_HORIZON/LONG_HORIZON_HISTORICAL` renders as `장기 구조`. One zone per side owns each
primary user-visible semantic, while distinct near and structural zones remain allowed. The old
000660 section fails the new provenance validator as expected; all seven repaired sections pass.
The policy is an explicit KR rollout option, so existing US/shadow renderer callers retain their
prior behavior.

Read-only current-data replay returns daily/weekly/monthly evidence for all seven subjects, zero
validator errors, zero look-ahead or partial-bar pivots, and no changes to TOP3 sector code, US
Price Structure, market digest, business thesis, valuation, Telegram, tasks, DB, archives, or
production flags. State is `REPLAY_PASS_READY_FOR_PREENABLE`, with open P0/material P1 `0/0`.
Price Structure remains `INTEGRATED_READY_NOT_ARMED`; do not enable or send from this repair.
Configure a dedicated non-production test sink and rerun the bounded pre-enable proof separately.

### 40.17 KR Daily 1200 Extension or Verified Degradation

Exact instruction commit `3e42f3fad2e32ff1b3cca47861cfb9704095ce28` precedes provider audit
`c9e8fc1e25394857bd88d4652e3a8b1e88638011`, degradation implementation
`d60b7b2a9edecbad0ed54c2151ecfba163478522`, and seven-ticker replay implementation
`f957bea48e1bf8df23c6b8fe769812ade5663456`.

Track A proves the supported thesis-monitor `/ohlcv` contract caps `count` at 1,000 and exposes no
cursor, offset, date window, or continuation state. Unsupported `end_date` input is ignored and
returns the latest overlapping window, while `count=1200` is rejected. The upstream Kiwoom adapter
has private continuation mechanics, but they are not part of the supported consumer contract; the
static 1,200-bar audit artifact is not a live cache. Capability is therefore
`PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW`.

Track B preserves the canonical daily target at 1,200 and records long-listed provider-limited
series as `PARTIAL_SAFE/provider_limit` at 1,000. `PARTIAL_SAFE` is explicitly not `PASS`; short
listings remain `PARTIAL`, insufficient evidence remains `FAIL`, and the existing coverage-aware
proximity/Fib/current-cycle gates remain authoritative. No second window, synthetic bar, alternate
provider, weekly/monthly substitution, or adjusted/raw merge is admitted.

The frozen 2026-08-27 replay returns 1,000 completed bars for all seven KR controls, zero actual
session gaps, zero duplicates, ascending order, and seven `ELIGIBLE_SR_ONLY` results with zero
renderer-validator errors. `2026-06-03` and `2026-07-17` are official KRX closures that the local
calendar package overexpected; they are retained as diagnostics rather than counted as data gaps.
The old 000660 section still fails as expected. Open P0/material P1 are `0/0`, and state is
`REPLAY_PASS_READY_FOR_PREENABLE`.

Price Structure remains `INTEGRATED_READY_NOT_ARMED`. This work changes no user-visible runtime,
Telegram, task, DB, assessment, archive, TOP3 sector path, US path, production flag, or operating
checkout. Next action is exactly `RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT` under a
separate authorization.

### 40.18 KR TOP3 / Price Structure Final Pre-Enable Stop

Exact instruction commit `9f37cfad97487876d6dfa63c03750f4dab664dbf` precedes Track A audit
commit `05b57901f7cf25086b580510aac6a6e72329cdfc`. The repository-native test routing contract
accepts dedicated test, staging, or developer recipient secrets, but none is configured in the
canonical or operating environment. The production recipient is present only as a one-way
redacted alias and was not copied, queried, or used as a substitute.

The strict sequence stopped at Track A with
`KR_FINAL_PREENABLE=BLOCKED` and `BLOCKED_NO_TEST_SINK`. Track B data collection, current-universe
resolution, market/stock generation, test delivery, and quality proof are `NOT_RUN` or `NOT_SENT`.
Track C was not created or started: operating remains
`43731f015901b96e2dee3af009b9e1d074382349`, both KR guards remain OFF, US Price Structure remains
OFF, and no restart or smoke was performed. Telegram messages, production intents, manual tasks,
DB/Pilot/archive mutations, and Production Assist changes are zero.

Open P0 is zero. The sole material P1 is `dedicated_test_sink_not_configured`. Configure exactly
one approved non-production destination through the existing secret/config mechanism, prove its
isolation, and rerun Track A. Do not reinterpret prior replay evidence as this final test-send
proof, and do not begin Track B or Track C until Track A passes.

### 40.19 KR Test Sink Configuration Resume Stop

Exact instruction commit `68ede1eae42315d94a89023fbc6c1f9be07fc99d` precedes blocked-resume
evidence commit `69e4bd6bc15da2a654ab6dcb678263f0ea049d37`. The existing resolver was applied to
the canonical and operating environment files, current process environment, and every
thesis-monitor LaunchAgent environment key set. No approved test, staging, or developer Telegram
recipient key exists. Only the production recipient has a redacted alias; it was never copied,
queried, logged, or used.

The explicit operator-secret boundary stopped the workflow before session resolution. Provider
calls, market/stock candidate generation, Telegram payloads, receipts, operating promotion,
service restart, smoke, and flag writes are zero. Operating remains
`43731f015901b96e2dee3af009b9e1d074382349`; KR TOP3, KR Price Structure, and US Price Structure
remain OFF; Production Assist stays OFF.

State remains `KR_FINAL_PREENABLE=BLOCKED_NO_TEST_SINK` and `KR_ROLLOUT=NOT_ENABLED`, with open
P0/material P1 `0/1`. The only next action is `OPERATOR_PROVIDE_DEDICATED_TEST_CHAT`. Once exactly
one approved secret is externally configured, rerun the resolver and isolation proof before any
data collection or send.

### 40.20 KR Test Sink Resume PASS and Sequential Enablement

The operator configured one dedicated private Telegram group through the canonical ignored secret
key `TELEGRAM_TEST_CHAT_ID`. Exact instruction commit
`68ede1eae42315d94a89023fbc6c1f9be07fc99d` precedes implementation
`315081005198e7b5676e9383f10d4a52b3d3ca34`. The Settings model now accepts the test-only key, while
the production notifier continues to own only `TELEGRAM_CHAT_ID`. Direct runtime equality proves
the recipients differ; reports and receipts contain aliases only.

Completed-session run 42 produced one TOP3 market message and seven monitored-KR stock messages.
The isolated `TEST_ONLY_NON_PRODUCTION` sender delivered 8/8 once, and Telegram response text hashes
match rendered and outbound hashes 8/8. Duplicate, orphan, retry, production-recipient send, and
production delivery-intent counts are zero. All seven price sections are `ELIGIBLE_SR_ONLY` with
zero unstable Fib, target, stop, look-ahead, partial-bar pivot, proximity, or ownership errors.

Main and operating advanced linearly to the implementation SHA. Feature-off parity passed first;
KR market TOP3 then passed with Price Structure OFF; KR Price Structure then passed 7/7 with the US
negative control still blocked. Final state is `KR_ROLLOUT=ENABLED_AWAITING_NATURAL_PROOF`, not
`LIVE_PASS`. Open P0/material P1 are `0/0`; Production Assist remains OFF. Wait for the next natural
KR market and stock cycle and inspect it read-only.

### 40.21 US Night-Futures Canonicalization and Current-Time E2E

Exact instruction commit `f6ab0168d3ef0d8ce1e2b5980ea7aae147db0c75` precedes canonical
implementation `df2e922bbb3ba554c9495408b64233661ff77c89`, generic US source-session
guard `3325d8a8db84fec6c8ca5d4c70dc5b2210c4179f`, historical positive-fixture proof
`fc6a53a944a9089eecc94d81f46b4602180b6b02`, and deployed implementation
`f6bc769f823429426474a38f007dc8196b4e5f43`.

`night_futures_gate` now exclusively owns compact-summary projection and full-message visibility.
The current `2026-08-28` expected night session had no ready canonical products, so the current
market message safely omitted it; one separately labeled `2026-08-27` historical fixture proved
fixed Fact identity and value/session/state parity. Current-time market `1/1`, stock `13/13`, and
fixture `1/1` test-sink deliveries matched exact received payloads with zero production sends.

Twelve US/foreign subjects rendered current-session SR-only structure. WRD failed closed because
its daily source ended one session before its declared `as_of`; no ticker exception was added.
Local full pytest is `1841 PASS`, GitHub Actions Test/Lint PASS, API/OHLCV health PASS, and open
P0/material P1 are `0/0`. State is `DEPLOYED_AWAITING_NATURAL_PROOF`. Do not manually trigger the
US Scheduled Task; inspect the next natural market and stock messages read-only.

### 40.22 Provisional Bollinger Expansion and Price Label Clarity v2

Exact instruction commit `73286dd44135bbc30ef3a145e02f5db81aedbdea` precedes implementation
`8c3bb493dc45a12c837053e08361f949ff771f00`. The existing price-anchored near/major layer and
completed-bar dynamic Bollinger layer remain unchanged. Valid in-progress D/W/M bars now feed a
separate `PROVISIONAL_BOLLINGER_SUPPORT/RESISTANCE` layer with observation timestamp, bar start,
expected close, PARTIAL state, security/currency/adjustment basis, and explicit non-authority.

The provisional layer cannot feed near/major S/R, stored rules, Fib, or wave anchors. The renderer
allows at most one distinct provisional line per subject or one overlap annotation. It labels the
line `잠정`, `진행중`, and `봉 마감 전 변동 가능`. Current quote and completed regular-session
structure close have separate ownership; equal values collapse to `현재가(정규장 종가)`, while
different values render both explicit labels.

Current-time replay is US `13/13` plus KR `7/7` PASS. It produced 17 standalone provisional lines,
two overlap annotations, one safe suppression, zero authority/major-SR leaks, and zero SNDK/WULF
bypass. The dedicated test sink received the corrected immutable full-message set `20/20` with
exact hashes, duplicates/orphans/production sends all zero. The first abbreviated-artifact attempt
was test-only and is retained as a diagnostic failure. Full pytest is `1865 PASS`; implementation
and evidence Actions Test/Lint PASS; open P0/material P1 are `0/0`. Main and operating advanced
linearly to `d3a58c953c2dd6d100031421770be3a54d0328b5`; API/OHLCV health and post-deploy US `13/13`
plus KR `7/7` frozen replay pass. State is `DEPLOYED_AWAITING_NATURAL_PROOF`. Natural
provisional/price-label proof remains independently `PENDING` and must not be triggered manually.

### 40.23 2026-08-29 US Morning Market Data and Natural Message Review

Exact instruction commit `428836d4a997a10eb7dd1d1935acdea8ea469b54` precedes read-only
evidence implementation `7fc982ecce30a0af261dcda198ef50280e707531`. The XNYS calendar and
run-45 packet both resolve the latest completed regular session to `2026-08-28`. SPY, QQQ, IWM,
SOXX, and RSP are current, all 11 supported sector proxies are current, and the deployed
deterministic renderer reproduces the exact naturally delivered market message byte-for-byte.

Official Nasdaq breadth is `PUBLICATION_PENDING`: the exact target row is absent and the latest
official row is `2026-08-26`, so no stale breadth is promoted. The canonical night-futures target
is the `2026-08-29` 06:00 end-date session; all four production-gate attempts found only the stale
`2026-08-28` session, and the entire section is safely omitted. Macro evidence is temporally
classified, but no item passes the existing additional-materiality selector.

Natural monitor run 45 delivered one market and 13 stock messages `14/14` once through the
deterministic production renderer. Market-message evidence parity is `PASS`; rejected AI output
was never sent. The primary and backup AI full-stock candidates remain rejected, so the overall
review is `PARTIAL_SAFE` with open P0/material P1 `0/1`. The P1 is bounded to AI validation and
does not reopen current market-data, temporal-safety, renderer, or delivery proof. No Telegram,
task, DB, assessment, scheduler, feature, or Production Assist mutation was performed by this
review.

### 40.24 US Friday/Saturday Night Futures and Run-45 AI Validator Repair

Exact work-instruction commit `f8ca4fcb4557037468e35578a98a66aa9cb750b5` precedes
implementation `f621b0ab253a3e9fc6752f7d7aff9ccdad06ca19`. Official KRX read-only evidence proves that
`BAS_DD` is the night-session end business date: the `20260828` rows exactly reconcile the prior
regular-session closes and provider changes. The Friday-night-to-Saturday target therefore requires
`BAS_DD=20260829`; that official endpoint returned no rows. This is `UPSTREAM_NOT_PUBLISHED`, not a
date-resolver defect. Existing current-session omission remains fail-closed with stale visible facts
and raw-summary bypass both zero.

The immutable run-45 primary and backup AI candidates move from `37 -> 0` and `4 -> 0` validation
errors. The repair uses existing structured ownership contracts for selected US market slots,
field-specific valuation interpretation, inventory relations, and canonical monitoring facts.
Strict semantic, numeric, runtime-quality, and Price Structure gates are unchanged. Primary and
backup replay pass; the isolated test sink received the production-equivalent market plus 13 stock
messages `14/14` once with exact payload parity and zero duplicate, orphan, production-recipient
send, or production delivery intent.

Open P0/material P1 are `0/0`; Production Assist stays OFF. Main and operating were promoted
linearly, API health and the post-deploy ownership smoke pass, and state is
`DEPLOYED_AWAITING_NATURAL_PROOF`. Wait for the next natural US run and inspect AI routing, exact
delivery, and the canonical night-futures section or safe omission read-only. Do not manually
trigger a Scheduled Task or send a production Telegram message.

### 40.25 Decision Calibration P1 Repair Before Canary

Exact instruction commit `5ccc8aadc29644295164b612de163bbf06fbcf76` precedes taxonomy,
timing/confidence, decision-change-condition, and adjudication implementation through
`930952132077e8403bcec1a7e2c52d5732d8521a`. The same 20 canonical evidence packets were rerun
blind with signed-in Codex CLI `gpt-5.6-sol / xhigh`; no web facts, future evidence, score, class
target, or ticker outcome exception entered the pass.

Nine material comparisons were adjudicated. Final distribution is BUY `0`, HOLD `17`, SELL `3`.
RXRX, TSLA, and WULF remain SELL. HUT resolves to `HOLD / OPTIONALITY_OFFSETS_DOWNSIDE / LOW /
UNFAVORABLE`; CRCL remains `HOLD / LOW / INSUFFICIENT`. All six timing and three confidence cases
are closed, all 20 decisions own asymmetric evidence-linked upgrade/downgrade conditions, numeric
binding is `60/60`, and repeated substantive spans are zero.

An independent xhigh portfolio audit sets HOLD-default and SELL-suppression bias to `NONE` and all
calibration/semantic gates to PASS. The dedicated non-production sink received the final set
`20/20 exact` through an owned `17 + 3` rate-limit continuation, with zero duplicate, orphan,
production-recipient send, or production delivery intent. Open P0/material P1 is `0/0` and
`DECISION_CANARY_READINESS=PASS`, but production canary remains OFF. A separate bounded canary
instruction is required before any runtime exposure.

### 40.26 Decision Evidence Polarity Renderer P1 Repair

Exact instruction commit `0bba7c9` precedes implementation
`86b9fc44006c45431ccc1822131df3b4a74eb1ca`. Decision-relative support/opposition remains intact,
while `decision-evidence-polarity-v1` independently owns BULLISH, BEARISH, and NEUTRAL claims.
The production canary renderer and artifact validator consume the same structured plan; no
free-form sentiment classifier or ticker exception exists.

Fresh run-44/run-45 evidence reproduced the four accepted SHA values exactly and classifications
remain 003690 HOLD, 000660 HOLD, GOOGL HOLD, RXRX SELL. GOOGL bullish evidence and RXRX neutral
quality evidence no longer appear under SELL. Two historical BUY fixtures also pass the common
polarity validator. The dedicated sink received all six payloads exactly once with zero production
recipient send, intent, duplicate, or orphan.

Local full pytest is `1903 PASS`; implementation Actions Test/Lint PASS. Main and operating were
promoted linearly, the repaired continuity state was installed, and only the exact KR 2 + US 2
canary was rearmed. Natural counts remain `0/2` per market. Open P0/material P1 are `0/0`; the next
action is read-only natural canary review with no manual task or production Telegram proof.

### 40.27 V2 Accepted Production Cutover

Exact instruction commit `0eb8bad` precedes decision-aware wording `1a6488e`, accepted runtime
`7f32c34`, and exact preflight convergence `6c429fc2f8afc4316b319494ca098c77594d0d2d`.
The runtime consumes the complete packet inventory, uses signed-in Codex CLI
`gpt-5.6-sol / xhigh`, requires final adjudication for material decision changes, and renders only
`accepted_decision_plan`. Missing or non-final ownership suppresses that subject's decision block;
raw candidates and silent V1 visible fallback are prohibited.

Fresh KR run-44 plus US run-46 preflight produced `20/20 READY`, BUY/HOLD/SELL `1/16/3`, strict
message quality PASS, and zero repeated substantive spans. Five subject-local validator repairs
changed no top-level decision. The dedicated non-production sink received `20/20 exact` with zero
retry, duplicate, orphan, production-recipient send, or production intent. Current code reproduces
all 13 saved prompts and both accepted artifacts exactly.

Main and operating advanced linearly to `2a30bb3dcaecb40f83ca53f59982de1e18dab0ee`. The visible
selector is `V2_ACCEPTED`, full monitored coverage is targeted, V1 rollback remains available, and
Production Assist remains OFF. Schedules and LaunchAgent checksums are unchanged; API and OHLCV
health pass. State is `MERGED_ARMED_AWAITING_NATURAL_LIVE`, not LIVE_PASS. Review the normal KR
2026-08-31 and US 2026-08-31 New York / 2026-09-01 KST cycles read-only. Do not manually trigger a
task or send a production Telegram message for proof.

### 40.28 Atomic Monitoring Onboarding and Scoped Readiness

Exact instruction commit `8da71e7` precedes implementation `2c4b973`. Registration now records
monitoring intent as `PENDING_ONBOARDING`; only the canonical readiness coordinator may promote a
subject through `READY` to `ACTIVE`. The persisted invariant is
`ACTIVE => onboarding_ready && production_eligible`, with identity, security master, official
structured company profile, investment logic, initial evidence, baseline assessment, and decision
readiness all evaluated subject by subject. Retry is idempotent and preserves thesis and assessment
history.

Production collection and AI packets use an immutable `production-packet-universe-v1` snapshot
scoped by market, session, and cutoff. An incomplete subject excludes only itself; it cannot block
ready peers or the other market. The 2026-08-31 incident replay passes, downstream numeric
registries consume the frozen cohort, and activation after cutoff cannot mutate an in-flight packet.

The full cloned operating-universe audit ends with `21` active, `21` ready-active, and `0` active
incomplete subjects. Official read-only evidence makes 047810 `ACTIVE_READY` from the next eligible
session. CPNG remains `PENDING_SAFE` because initial evidence, baseline assessment, and decision
readiness are absent; none was fabricated. The isolated sink received all `22/22` exact messages
through an identity-checked rate-limit continuation with zero duplicate, orphan, production send,
or production intent. No scheduler, Price Structure, valuation, accepted-decision ownership, or
2026-08-31 production replay changed.

The first real operating reconciliation revealed a legacy-only selector issue: seven US subjects
had an earliest provisional assessment followed by a final one. Bounded repair `6521d50` selects an
explicit initial baseline first and otherwise the earliest final legacy assessment. Full regression
is `1962 passed`; Actions run `33386496321` passes Test/Lint. Final operating reconciliation is
`21/21/0`, API health passes, 047810 is active from `2026-09-01`, and CPNG remains pending with its
three evidence blockers. This operational convergence changed no readiness threshold.

### 40.29 Pending Onboarding Auto-Reconciler and Preflight Resume

Exact instruction commit `c95e176` precedes final implementation
`5e3820456ace797450b9403386edaa2fc6af6cf1`. Pending onboarding now has three bounded entry points:
immediate registration continuation, a 30-minute generic background reconciler, and cached-only
market preflight before packet-universe freeze. All three call the existing readiness coordinator;
none can force-set active or allow a raw decision candidate to grant readiness.

Generic KR and US registration, retry classification, idempotency, cross-market and same-market
isolation, cutoff eligibility, and ready-peer continuation pass. The dedicated sink completed
`22/22 exact` through a `20 + 2` identity-aware continuation with zero production send, intent,
duplicate, or orphan. Existing market delivery schedules, accepted ownership, Price Structure, and
valuation are unchanged.

The deployed generic reconciler encountered CPNG without a ticker argument. It rebuilt canonical
initial evidence, preserved the final baseline, produced accepted-v2 `HOLD`, and activated CPNG as
`ACTIVE_READY` with first eligible session `2026-09-01`. Current counts are active-ready `22`,
pending/retryable/review-required `0/0/0`. Manual CPNG resume and ticker bypass are zero. Open
P0/material P1 are `0/0`; wait for the next natural US packet and do not replay the 2026-08-31
production message.

### 40.30 2026-09-01 US V2 Natural Live Read-Only Verification

Exact instruction commit `e6c11cff168fa430d7ddc7095d8c407d80948553` precedes the immutable
run-49 proof. The 2026-08-31 New York session froze all 14 eligible US/foreign subjects, including
CPNG, and delivered market `1` plus stock `14` exactly once at 08:40 KST. Market-message quality,
macro temporal safety, safe night-futures omission, Price Structure, valuation, exact payload, and
delivery gates pass. No manual task, send, retry, recipient access, or production-state mutation
occurred.

V2 natural live itself is `FAIL`. Both natural primary and backup automations stopped in
`accepted_decision_v2_runtime.prepare_context` when the local OHLCV request raised
`httpcore.ConnectError`. No packet-bound candidate, adjudication, or accepted plan was created for
any of the 14 subjects. The backup AI prose path then retained a false-positive
`numbers_without_provenance:market_context.text:2000` rejection, so deterministic fallback was the
terminal route. Explicit BUY/HOLD/SELL visibility is `0/14`; CPNG is
`MISSING_UNEXPECTED`, CORZ is `FALLBACK_RENDERER_ROUTE`, and the prior GOOGL BUY plus three SELL
controls are not visible as V2 decisions.

Open P0/material P1/P2 are `0/2/0`. Do not replay or resend the completed cycle. The next action is
`BOUNDED_DECISION_PIPELINE_REPAIR`, scoped to packet-bound V2 context availability/continuation and
the independent `2000` validator false positive. Preserve all immutable proof artifacts.

### 40.31 OHLCV Technical Context Resilience and Provenance Repair

Exact instruction commit `1dd691a340b4961e105371af53142c76db7385d7` precedes canonical
implementation `91180f3b00942d09d2c509e60a2a3d63c48d3951`, bounded retry cap
`43638307a5c4b568047112fda28e4eb784ef180a`, and final generation-convergence code
`1e0fb9cd6e4542474c623800a805026c236f2a53`. The run-49 ConnectError root cause is
`PROCESS_NAMESPACE_MISMATCH`: the host LaunchAgent service was healthy, but the restricted decision
process could not open loopback. Duplicate decision-stage HTTP acquisition and cohort-wide
exception propagation amplified the incident.

The repaired path validates and freezes `packet-owned-technical-context-v1` during canonical
acquisition. V2 consumes that packet artifact without fresh local HTTP; retry/recovery is bounded,
and malformed or missing contexts remain subject-local. Run-49 replay prepares and accepts all
14 subjects with technical states FULL/PARTIAL_SAFE/UNAVAILABLE/INVALID `10/0/0/4`. The four
INVALID subjects fail OHLC integrity rather than transport and do not block peers. KR run-48 is
FULL `8/8`, including 047810 without a special case. Price Structure, valuation, decision policy,
accepted ownership, Public Action, schedules, and fallback policy are unchanged.

The numeric lexer now treats Korean particles after structural index names correctly while
retaining exact unsupported-number rejection. Phantom `2000` is zero and real unsupported controls
pass. The isolated signed-in xhigh replay is accepted-ready `14/14`; the dedicated sink received
14/14 exact stock messages with zero production send or intent. Open P0/material P1 is `0/0`.
This is `READY_FOR_MAIN`, not natural LIVE_PASS. After linear promotion, wait for the next natural
US cycle and inspect OHLCV acquisition, technical-state counts, candidate/accepted counts,
fallback, explicit decisions, and exactly-once delivery read-only.

### 40.32 V2 Natural CLI Path and Product-Identifier Provenance Repair

Exact instruction commit `b2c0a4af72c5eb060dcdacd8b281e30307c717f1` precedes implementation
`b5be74439b2e8e769b1605e539599835abbc8a84`. The natural runtime no longer interprets configured
relative schema, prompt, output, or log paths against the LaunchAgent working directory. It resolves
them once against the canonical repository root, verifies the schema before calling Codex CLI, and
keeps portable relative claim storage. Primary and backup use one resolver.

Canonical evidence-owned product identifiers are now typed non-numeric spans. The exact identifier
span is masked, while adjacent amounts, ratios, prices, ranges, signed values, dates, and unproven
hyphen-number strings retain normal numeric validation. Run-50 KR natural-path replay is `8/8`, the
production-equivalent US replay is `14/14`, and the dedicated test sink is `22/22 exact` with zero
production send or intent. CPNG/HUT technical recovery, 000660 valuation, 005930 risk/reward, Price
Structure, accepted ownership, schedules, and delivery boundaries remain unchanged.

Open P0/material P1 is `0/0`; the repair passed `READY_FOR_MAIN` and was deployed by clean linear
fast-forward through `26004d926247c4ef053e49b74dc8fb9654353199`. Branch/main Actions and API
health pass. Natural proof is still pending and must come from the next ordinary KR and US cycles
without a manual task or production resend.

### 40.33 Run-51 Runtime State, Daily Review, and Night-Futures Repair

Exact instruction commit `ff255fc710a3b86b0496cdedca505a7a4a5323e7` precedes runtime
implementation `16fa1222136b300d900682904f8391ef5c4b482a`. The natural V2 failure is now
classified correctly as a local pre-model app-server state failure. `codex-runtime-state-v1`
provides owner-only, claim-scoped `CODEX_HOME`/`CODEX_SQLITE_HOME`, a read-only signed-in auth
reference, and a real SQLite WAL preflight. The scheduler-context probe and immutable run-51 xhigh
replay reach the model; accepted-ready and explicit decisions are `14/14`.

The exact rejected daily-review candidate converges from 47 errors to zero with strict schema,
numeric, valuation, semantic, final-language, and runtime quality gates unchanged. The repair adds
in-memory legacy scope assignment, numeric-span synchronization, typed canonical repetition
handling, and depositary-ratio identity precision. Result is 15/15 messages, numeric auto-binding
`124`, and zero substantive/template repetition.

Official KRX evidence proves that night `BAS_DD` is the completed session end date. XKRX calendar
mapping expected `2026-09-02`, while the provider returned `2026-09-01`; run-51 therefore remains
correctly `SOURCE_LIMITATION_SAFE` with ready/rendered `0/0`. No value was forced ready.

Cross-market production-equivalent proof is KR `8/8` plus US `14/14`; the dedicated non-production
sink received `22/22 exact` through a rate-limit-safe `20 + 2` continuation with zero duplicate,
orphan, production send, or production intent. Full regression is `2062 passed`; implementation
Actions Test/Lint pass. Open P0/material P1/P2 are `0/0/0`, and the bounded repair is
`READY_FOR_MAIN`. This is not natural LIVE_PASS. Wait for the next ordinary US and KR cycles and
inspect the repaired paths read-only.

### 40.34 US Morning Previous-XKRX Night Reference Contract

Exact instruction commit `46c6707325fe214a7d686095b940cabb55911006` precedes implementation
`7efc07bb0a9c635b78bb63ec642b50656b01b0b4`. The US-morning product target now uses
`us-morning-night-reference-date-v3`: for KST date `D`, the expected night reference is the latest
valid XKRX business date strictly before `D`. US regular-session dates no longer own the product
mapping; provider raw `BAS_DD` and the independent 06:00 finality gate remain explicit.

Run-51 now expects `2026-09-01`, exactly matching both official provider rows. Date, instrument,
same-contract DAY comparison, finality, and provenance gates pass at ready/rendered `2/2`. The
renderer adds those two packet-owned facts with non-night numeric/selection diff `0/0`. Frozen V2
accepted-ready remains `14/14`, daily-review quality passes, and KR/US production-equivalent proof
remains `8/8 + 14/14`. Full regression is `2077 passed`; implementation Actions Test/Lint pass.

Open P0/material P1/P2 are `0/0/0`. The next dependency is the next ordinary US morning cycle,
reviewed read-only. Do not manually run a task, resend production, expose recipient values, or treat
retrospective replay as natural proof. Production Assist remains OFF.

### 40.35 Run-51 Official KRX Night OHLC History and Controlled Live Path

Exact instruction commit `999d185a30afd64359bea793a270c9fd29d5e996` precedes implementation
`4341d352b8402a16dcd66d34504fc39a17acc61b` on operating base
`d0039e6c84ccb8fd74c743b0ceec033760499229`. Official KRX `fut_bydd_trd` now owns NIGHT daily
OHLC raw preservation, normalized contract/date/session identity, data-driven near-month selection,
and same-contract daily/weekly/monthly aggregation. Current week and month remain `IN_PROGRESS`;
contract roll is partial rather than spliced.

Run-51 binds to `2026-09-01`. KOSPI200 official daily O/H/L/C is
`1067.00/1072.45/1053.80/1064.50`; KOSDAQ150 is
`1440.00/1447.00/1415.50/1432.80`. The visual KOSPI200 screenshot is `NOT_COMPARABLE` because its
provider/session/chart convention is unverified; official KRX remains machine authority. A bounded
TEST/HISTORICAL backfill made `21/21` official requests, stored `78` valid bars, recorded `216`
rejections without repair, used no post-cutoff date, and did not mutate the frozen packet.

The US 10Y real-yield pair is `2.44%` on `2026-08-31` versus `2.42%` on `2026-08-28`, rendered as
`+0.02%p (+2bp)`. Non-night market numeric and selection diff are `0/0`. Signed-in Codex CLI
`gpt-5.6-sol / xhigh` produced `14/14 READY` with HOLD/SELL `11/3`, fallback `0`, and strict quality
PASS. The atomic TEST-only delivery sent and acknowledged `15/15` exact payloads with zero retry,
duplicate, orphan, production-recipient send, or production-state mutation.

Open P0/material P1/P2 are `0/0/2`; the P2 items are screenshot convention reconciliation and
optional rejection-report presentation polish. `RUN51_KRX_NIGHT_LIVE_PATH_ACTUAL_SEND = PASS`, but
this controlled TEST proof is not natural LIVE_PASS. The next dependency remains the next ordinary
US morning cycle, reviewed read-only. Production Assist remains OFF.
