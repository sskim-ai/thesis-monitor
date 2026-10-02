# Thesis Monitor — R2B-R9-REV11
## Sealed Provider Dispatcher Closure + Full Fresh Live Requalification + Fresh 24-Message Proof

**REV11 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV11.**

REV10 completed the entire offline analytical/product contract. Do not reopen UNKNOWN_LIMIT, event/quality/valuation semantics, issuer bridge, Market display, detailed stock renderer, Core/A/B policy, source-use policy, or KOSPI200-only night scope.

REV10 Phase-A root gate is PASS and already has `dispatch_allowed=true`.

The only remaining pre-live gap is operational: convert the finite provider inventory into exact sealed per-request descriptors, execute only those descriptors, write fresh current-generation receipts, and feed those receipts directly into the fresh all-source controller.

After that dispatcher closes, REV11 must continue in the same task to full fresh provider acquisition → source closure/replay twice → live adapter qualification → fresh Market/Core/A/B → exact 24 sender-boundary messages → human-review ZIP.

No additional semantic redesign cycle is authorized unless this exact provider-dispatch contract cannot be closed.

---

# 0. Newest SoT

REV10 result ZIP SHA-256:
`30f1b5f78c3421d2c7e687ca2aa171635467ebeff341ef627f52d544797f891e`

Terminal:
`R2B_R9_REV10_PROVIDER_BUDGET_GAP`

Repository:
- branch `codex/r2b-r9-rev10-final-closure`
- base `4a976b7d4f0d10c403c0225c6173f00c2c3bd9fb`
- instruction `3828fe57cfc2fccbcceadd14376cbf2d5e2b84e6`
- exact tested implementation `e419371e05e0aabb18d651be6da5b98a9ea2375c`
- operating main `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV10 validation:
- focused 567 PASS
- full 6434 PASS / 63 unchanged skips / 0 failures
- Ruff / diff / Investment Knowledge / Chart Knowledge PASS
- provider calls 0
- model calls 0
- production side effects 0

---

# 1. REV10 Phase-A root gate is authoritative

`r9-rev10-phase-a-root-gate.json` is PASS with `dispatch_allowed=true`.

Accepted gates:
- event_archetype_gate PASS
- denied_quality_gate PASS
- valuation_matrix_gate PASS
- aggregate_whole_source_gate PASS
- replay_twice_gate PASS
- Market2_gate PASS
- Core22_gate PASS
- A22_gate PASS
- B22_gate PASS
- exact24_gate PASS

Offline common generation:
- Market 2/2
- Core/A/B 22/22
- final synthetic payloads 24/24
- NORMAL 20 / UNKNOWN_LIMIT 2
- replay identical

Do not redefine these gates in REV11.

---

# 2. Current provider-plan gap

REV10 candidate plan SHA:
`161cd5bb54ea0d39f98533828b4fabbfa433dc7b5b9fd814af87e1a5c40c6fa3`

Candidate theoretical HTTP-attempt envelope:
`2622`

It is diagnostic only. `exact_final_provider_plan_issued=false`.

Remaining operational gaps:
1. KR configured page-cap parity;
2. sealed US Market request descriptors;
3. sealed FRED descriptors;
4. sealed EIA descriptors;
5. sealed ECOS/USDKRW descriptors;
6. sealed KOSPI200 night descriptors;
7. event query/dispatch bindings where current role inventory requires them;
8. native-valuation read bindings where an already-authorized source qualifies;
9. one fresh receipt dispatcher/collector mapping every request output into the new all-source graph.

REV11 closes only this execution layer.

---

# 3. Sealed request descriptor

Implement one immutable `FreshRequestDescriptor` (or repository-equivalent) for every external logical request before execution.

Required fields:
- generation_id
- logical_request_id
- provider / source_family / role_id
- market and ticker/security/issuer where applicable
- endpoint/operation ID
- exact request args/params/body identity
- target session/period
- mandatory/optional
- page/document policy
- max_pages / max_documents
- timeout
- transient retry max
- max transport attempts
- request semantic hash
- destination raw artifact path
- expected normalizer/owner
- expected consumer role
- secret/config identity hash without secret value
- descriptor SHA-256

No external request may execute without an accepted descriptor. No descriptor may be created after seeing provider data.

---

# 4. Descriptor → receipt chain

Every descriptor must produce:
1. plan receipt
2. start receipt
3. per-attempt transport receipt
4. raw response/source artifact
5. normalization receipt
6. role-binding receipt
7. final logical-request receipt

Final receipt binds descriptor SHA, request hash, attempts/retries, raw hash, source observation period, retrieval time, normalization hash, generation ID and final status.

Only these receipts may feed R9-REV11 current source composition.

---

# 5. Fresh request dispatcher

Implement one current-generation dispatcher that:
- reads only the sealed final provider plan;
- executes only declared descriptors;
- enforces timeout/page/document/retry limits;
- allows only byte/semantic-identical transient retry under existing policy;
- denies semantic/schema/policy retry;
- preserves failed attempts;
- continues independent requests after per-request failure unless current systemic-stop policy applies;
- never discovers a new request dynamically outside the plan;
- writes all receipts to the current generation.

No hidden provider recursion may exceed a descriptor envelope.

---

# 6. KR page-cap parity

REV10 found:
- configured KR page cap 50
- bounded inspection contract max 20
- production setting unchanged.

Do not globally change 50→20 just to pass proof.

Separate global provider capability from request-local bounded execution.

For every KR paginated descriptor compute `required_max_pages` from the declared consumer window and endpoint page-size/consumer-complete semantics.

Use request-local cap only if `required_max_pages` fits the accepted bounded contract. The current bounded contract maximum must be read from code/proof, not blindly hardcoded.

If a required request genuinely exceeds the accepted bound, do not truncate. Return:
`R2B_R9_REV11_KR_PAGE_BUDGET_INSUFFICIENT`
with zero calls for that affected role.

The dispatcher must enforce the request-local cap even if global config permits more pages.

---

# 7. Provider descriptor inventories

Freeze exact descriptors for current code/role inventory.

## Stock price/OHLCV
All22 current chart/price roles, including the exact current adjusted/unadjusted D/W/M/valuation roles actually consumed. No old cache may fill a role.

## US Market
Current configured major-index/proxy/style and sector universe; exact target completed session; no stale fallback.

## KR Market
KOSPI/KOSDAQ, sectors, breadth, flows where current owner uses them; request-local page caps.

## FRED
Exact current configured series. Current known roles include DGS3/DGS5/DGS10/DGS30/DFII10/T10YIE/BAMLH0A0HYM2/VIXCLS/DCOILWTICO/DTWEXBGS plus only other current configured roles. Preserve source observation dates.

## EIA
Exact configured series/route, period selection and role mapping.

## ECOS / USDKRW
Exact already-authorized route with source-owned observation period/currentness. No undeclared FX provider.

## KOSPI200 night
KOSPI200 only. Pre-freeze every daily/weekly/monthly/history request needed by the current finite owner. Per-horizon `자료 부족` is allowed when qualified history is unavailable. No KOSDAQ150.

## SEC
Existing bounded owner for all applicable US14. Freeze CIK/issuer type, forms, discovery/index/document/exhibit caps, current/prior roles and max attempts.

## OpenDART
Existing bounded owner for all KR8, including 005930 and 047810. No complete-control exemption.

## Event/news
Before network classify each subject as EVENT_NOT_REQUIRED / EVENT_OPTIONAL_PLANNED / EVENT_REQUIRED_FOR_CURRENT_PRODUCT_ROLE. If planned, freeze provider/query/cutoffs/result limits/retries. No broadening after miss. Persisted events use current-eligibility receipts without fake fresh acquisition.

## Native valuation
Use only existing configured authorized valuation owners. Freeze exact read descriptors only when current-security identity/currentness/basis can be checked. If not, metric stays unavailable. No new provider. Alpha Vantage 0.

---

# 8. Final provider plan

Create immutable `r9-rev11-final-provider-plan.json` containing:
- generation ID
- code SHA / policy/schema hashes
- execution mode / query time / target sessions
- all descriptors and descriptor hashes
- descriptor count
- mandatory/optional role coverage
- per-provider logical count
- per-provider theoretical max transport attempts
- total theoretical max
- zero undeclared descriptors
- plan SHA

Create `r9-rev11-provider-role-coverage.json` proving every mandatory mutable role maps to a descriptor or typed no-network persisted/static owner.

No mandatory mutable role may remain NO_DESCRIPTOR / LEGACY_CARRY_IN / UNBOUNDED.

---

# 9. Final offline acceptance before first provider call

Require:
- exact REV10 root-gate receipt PASS
- descriptor schema PASS
- all mandatory roles covered
- KR request-local page budget PASS
- all provider maxima finite
- secret/config presence valid without exporting secrets
- no undeclared provider
- Alpha plan 0
- Massive/fallback 0
- fresh receipt-owner binding complete

Then issue:
`R2B_R9_REV11_FINAL_PROVIDER_PLAN_PASS`
and `live_dispatch_allowed=true`.

If not:
`R2B_R9_REV11_PROVIDER_PLAN_GAP`
with provider/model calls 0.

This is the final authorized offline stop. Do not reopen analytical contracts.

---

# 10. Fresh receipt → fresh controller binding

Every current-generation source consumer resolves through generation + role + logical request + receipt SHA (or exact repository equivalent).

Reject:
- unplanned receipt
- old generation
- mismatched descriptor SHA
- old macro
- old business comparison
- old quality
- old current valuation
- old stock/Market packet

Do not invoke legacy freeze paths that import old mutable Class-C/current data.

---

# 11. Full fresh live/ad-hoc execution

After `live_dispatch_allowed=true`, execute only the sealed plan.

Use actual current time and exchange calendars to choose latest eligible completed US/KR sessions.

If outside scheduled window use `AD_HOC_LIVE_REQUALIFICATION`; do not pretend it was scheduled.

No scheduler mutation.

Transport per descriptor:
- first attempt 1
- only accepted transient transport retry
- byte/semantic-identical request
- no semantic/schema/source-use/policy retry
- no dynamic widening

---

# 12. Fresh all22 stock acquisition

Fresh current-generation acquisition for:
US14 CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF
KR8 000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No prior-complete exemption.

Fresh roles include price/OHLCV, technical, financial/business, planned event state, quality, valuation, flow/positioning and current issuer bridge if needed.

---

# 13. Fresh US Market acquisition and required display coverage

Freshly acquire current major proxies, sector universe, breadth where owned, macro and KOSPI200 night context.

Before Market AI, require qualified fresh/current or LATEST_PUBLISHED_VERIFIED rows for at least:
- SPY
- QQQ
- IWM
- configured Treasury display block
- WTI
- dollar role
- VIX

Sector TOP3/BOTTOM3 shows when qualified; `자료 부족` is allowed only when the fresh sector source genuinely cannot qualify enough rows.

KOSPI200 D/W/M may show per-horizon `자료 부족` if the finite current owner cannot qualify that horizon.

No stale values may satisfy display coverage.

---

# 14. Fresh KR Market acquisition

Freshly acquire/qualify:
- KOSPI
- KOSDAQ
- breadth
- KOSPI sectors
- KOSDAQ sectors
- investor flows where owned
- USD/KRW

Before Market AI require current completed-session KOSPI/KOSDAQ context and USD/KRW source-time/currentness PASS.

Sector TOP3/BOTTOM3 renders when qualified; fresh source insufficiency may render `자료 부족` per venue.

No stale FX.

---

# 15. Fresh financial/business, quality, valuation

Preserve REV10 semantics.

Current-only valid financial source with explicit no-compatible-prior may proceed to UNKNOWN_LIMIT. Source/lineage failure may not hide as UNKNOWN_LIMIT. Absolute current amount alone is non-directional.

005930 and 047810 must use fresh OpenDART owner. SKHY bridge, if needed, is rebuilt from current-generation source. SNDK event context remains non-directional unless actual fresh/current source contract authorizes otherwise.

Quality is generated only from current financial/business input.

Create CurrentValuationView for all22. Each metric is independently QUALIFIED / N/M / 판단 자료 부족. Optional metric unavailability does not fail the run. No cross-security transfer and no valuation-only Overall direction.

---

# 16. Fresh source closure

Require:
- stock packets 22/22
- Market source 2/2
- mandatory US display macro roles currentness PASS
- USD/KRW PASS
- KOSPI200-only scope PASS
- quality views all22
- valuation views all22
- event/bridge states complete under current policy

Generate a new R9-REV11 FullSourceRunSeed, US packet, KR packet, combined packet and authority graph. No previous current hash reused as current identity.

---

# 17. Live replay twice and adapter qualification

Freeze live raw/source corpus, disable provider access, replay entire graph twice.

Require exact semantic equality for stocks, Markets, macro, night, event/bridge, quality, valuation, full packets and authority graph.

Then set NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true and, only if live mandatory coverage also passed, COMPLETE_SOURCE_ADAPTER_QUALIFIED=true. Do not inherit either flag.

---

# 18. Fresh model execution

Only after source qualification, run completely fresh:
- Market 2/2
- Core 22/22
- A 22/22
- B 22/22

No old AI outputs, no independent-review targets, no result-driven source refresh, no semantic/schema repair, no fallback/judge/selective ticker rerun. Use only current approved transient model transport retry policy.

---

# 19. Final messages

## US Market
`미국 시장 · YYYY-MM-DD`
1. SPY/QQQ/IWM/etc selected major rows with change + %
2. compact fresh/current or latest-published-verified rates/oil/dollar/VIX macro
3. market judgment + confidence
4. sector TOP3/BOTTOM3 or honest 자료 부족
5. KOSPI200 day/week/month, 자료 부족 per unavailable horizon
No KOSDAQ150.

## KR Market
`한국 시장 · YYYY-MM-DD`
1. KOSPI/KOSDAQ judgment + breadth/flow when owned
2. KOSPI TOP3/BOTTOM3 and KOSDAQ TOP3/BOTTOM3
3. USD/KRW with change/date where owned
No stale values.

## Stocks
Stable detailed format:
1. optional actual pilot label
2. company/ticker
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / evidence maturity / New Buyer / Holder
4. reevaluation
5. thesis/risk/market expectation
6. core judgment
7. business/earnings
8. existing warnings
9. key monitoring
10. current price structure
11. flow/positioning
12. Valuation

Do not render standalone registered price rules, data caution, next checks, unresolved/unknown.
Valuation section mandatory; each metric shows qualified / N/M / 판단 자료 부족.

---

# 20. Exact sender-boundary capture

Capture exact production-sender payload bytes with external delivery disabled:
- MARKET_US
- MARKET_KR
- US14 stock payloads
- KR8 stock payloads
- ALL_MESSAGES.md
Total 24/24.

No post-hoc reconstruction.

---

# 21. Human-review bundle

On full PASS create `r2b-r9-rev11-fresh-24-message-human-review.zip` + SHA containing exact 24 payloads, message hashes, final provider plan, descriptor inventory, planned/theoretical/actual provider counters, fresh receipt audit, Market display coverage, macro currentness, KOSPI200 D/W/M, all22 source summary, financial/event/quality/valuation matrices, 005930/047810/SKHY/SNDK traces, Market/Core/A/B ledger, validation and production-isolation proof.

---

# 22. Production side effects

Hard zero throughout REV11:
Telegram, recipient intent, production DB decisions/warnings, scheduler mutation, notifications mutation, broker, deploy, main merge, push, restart.

---

# 23. Success terminal

Use only:
`R2B_R9_REV11_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:
1. REV10 root gate exact PASS
2. request descriptor contract PASS
3. KR page-cap parity PASS
4. every mandatory role mapped
5. final provider plan issued
6. live_dispatch_allowed=true
7. no request outside plan
8. all mandatory mutable roles freshly acquired
9. live stock 22/22
10. live Market 2/2
11. required US display macro/index roles qualified
12. USD/KRW currentness PASS
13. KOSPI200-only PASS
14. fresh quality all22
15. fresh valuation all22
16. fresh event/bridge states complete
17. R7 direction guard PASS
18. new full-source graph PASS
19. live replay twice PASS
20. COMPLETE_SOURCE_ADAPTER_QUALIFIED=true
21. fresh Market/Core/A/B complete
22. exact final payloads 24/24
23. message contracts PASS
24. Alpha 0
25. Massive/undeclared fallback 0
26. production side effects 0
27. human-review ZIP created

---

# 24. Honest stop terminals

Provider/descriptor gap: `R2B_R9_REV11_PROVIDER_PLAN_GAP` — no provider/model calls. This is the only remaining authorized offline terminal; do not reopen analytical contracts.

KR cap insufficient: `R2B_R9_REV11_KR_PAGE_BUDGET_INSUFFICIENT`.

USDKRW descriptor/source-time gap: `R2B_R9_REV11_USDKRW_DESCRIPTOR_GAP`.

Fresh source partial: `R2B_R9_REV11_FULL_FRESH_SOURCE_PARTIAL` — no AI.

Required US display macro coverage partial: `R2B_R9_REV11_US_MARKET_DISPLAY_SOURCE_PARTIAL` — no stale substitution.

Actual financial source/lineage failure: `R2B_R9_REV11_FRESH_FINANCIAL_SOURCE_PARTIAL`; valid explicit no-comparison may proceed to UNKNOWN_LIMIT.

Adapter gap: `R2B_R9_REV11_LIVE_ADAPTER_REQUALIFICATION_GAP` — no scheduler authorization.

Model/render failure: exact stage terminal; preserve fresh source corpus; do not recollect because downstream failed.

---

# 25. Required validation

Dispatcher: descriptor hash, no undeclared request, bounded pages/documents, retry enforcement, generation isolation, old-receipt rejection, descriptor→receipt→consumer binding.

KR pagination: request-local cap, global config unchanged, sufficient-pages positive, insufficient-cap negative, cap exhaustion explicit.

Provider plans: stock, US Market, KR Market, FRED, EIA, ECOS, KOSPI200, SEC, OpenDART, events, valuation when configured.

Freshness: no old macro/business/quality/valuation/Market/stock packet.

Market display: positive SPY/QQQ/IWM, fresh/latest-published rates/oil/dollar/VIX, sector rank or honest unavailable, KR USD/KRW, KOSPI200 only.

Stocks: all22, current-only UNKNOWN_LIMIT, 005930, 047810, SKHY, SNDK, quality, valuation.

AI/render: fresh Market/Core/A/B, detailed NORMAL/UNKNOWN_LIMIT, exact sender-boundary 24.

Repository: focused/full pytest, Ruff, diff, Investment Knowledge, Chart Knowledge, secret scan, skip/xfail parity.

---

# 26. Required result bundle

Return immutable ZIP + `.sha256` containing REPORT.md, summary.json, REV10 identity/SHA, repository identities, changed-file inventory; descriptor schema/inventory, KR cap proof, provider-role coverage, final provider plan/SHA and budgets; all fresh request/attempt/raw/normalization/role receipts; all22 source, Market/macro/night, financial/business/events, quality, valuation, bridge; fresh run seed/full packets/authority/replay/adapter qualification; fresh Market/Core/A/B and exact payloads; human-review ZIP; safety counters, validation, secret scan and manifest.

---

# 27. After full PASS — generate only

Generate but do not execute `Post-R9-REV11 Unified Scheduler Cutover`. Require explicit human approval of exact fresh 24 messages. No scheduler activation inside REV11.

---

# 28. Final principle

The analytical/product contract is closed. REV11 must not invent another semantic redesign.

Its job is to turn the qualified finite provider inventory into one sealed executable plan, execute exactly that plan, bind every fresh receipt into the new source graph, and prove the current system end to end on real fresh data.

If REV11 stops offline, it may stop only because the executable provider plan itself cannot be made finite and exact—not because an already-passed analytical gate was reopened.
