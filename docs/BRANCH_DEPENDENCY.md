# Branch Dependency Manifest

As of 2026-09-01. Resolve final SHAs from Git; documentation commits are intentionally not
self-referential.

| Branch | Base / merge-base | Unique scope | Code dependency | Operating eligible | Promotion path |
|---|---|---|---|---|---|
| `codex/20260902-run51-live-path-krx-night-ohlc-history` | exact instruction `999d185...` on clean operating main `d0039e6...` | official KRX NIGHT raw/daily history, data-driven near-month, same-contract D/W/M, dated real-yield pair, Run-51 xhigh V2 and exact TEST delivery proof | extends existing KRX night provider and deterministic US market renderer; no scheduler, DB schema, decision policy, valuation, Price Structure, production recipient, or Production Assist dependency | promotion eligible after full exact-SHA CI; natural US LIVE still pending | implementation `4341d35...`; clean linear fast-forward, operating sync/restart if required, then read-only next ordinary US cycle |
| `codex/20260901-v2-natural-cli-path-product-identifier-repair` | exact instruction `b2c0a4a...` on main `1aa10f0...` | canonical repo-root Codex CLI path resolution, schema preflight, portable claim paths, and canonical product-identifier numeric boundaries | extends accepted V2 runtime and numeric provenance only; preserves OHLCV recovery, Price Structure, valuation, decision policy, schedules, DB, Public Action, Telegram production, and KRX | promoted/deployed; natural KR/US proof pending | implementation `b5be744...`, validated promotion `26004d9...`, branch/main Actions `33507836260`/`33508187986`; API health PASS, then wait for ordinary KR/US cycles |
| `codex/20260901-malformed-ohlc-provider-integrity-repair` | exact instruction `235cf78...` on main `813beb6...` | normalized-row integrity, one bounded content refetch, exact invalid-row lineage, four-ticker forensics and replay/sink proof | extends existing OHLCV client and packet telemetry only; no Price Structure formula, valuation, decision policy, task, DB, Public Action, Telegram production, KRX or peer dependency | promoted and deployed; natural US proof pending | implementation `a6707b8...`, report/promotion `9c6919a...`, Actions `33473079100`; API/OHLCV health PASS, then wait for next ordinary US cycle |
| `codex/20260901-ohlcv-technical-context-resilient-v2-repair` | exact instruction `1dd691a...` on main `f7c4331...` | packet-owned technical context, bounded OHLCV recovery, subject isolation, exact numeric-span provenance and V2 convergence | extends accepted V2 runtime only; no provider formula, Price Structure, valuation, task schedule, DB, Telegram production or KRX integration change | promoted and deployed; natural US proof pending | report/promotion `3efe688...`, Actions `33464969356`; wait for the next ordinary US cycle |
| `codex/20260830-v2-adjudicated-decision-ownership-repair` | exact instruction `4662c08` on main `29bdd4c...` | deterministic candidate + adjudication -> accepted plan authority, accepted renderer/validator, frozen 20 replay and exact sink proof | consumes immutable V2 candidate/agreement artifacts; no new AI reasoning, v1 canary, production packet, task, DB, Public Action, trading, KRX or provider dependency | shadow code/docs promotion eligible; V2 production exposure remains zero | Track A `5730f81...`, Track B `6370d3f...`, Track C `f556051...`; accepted message review then separate bounded migration instruction |
| `codex/20260830-preconfirmation-asymmetry-decision-engine-v2` | exact instruction `46bdf4c` on main `1359a57...` | driver maturity, pricing requirement, scenarios/asymmetry/cost, pre-confirmation BUY, 20-stock label-blind replay, adjudication and test-sink proof | consumes `decision-evidence-packet-v1` only; no production canary, packet, prompt, task, DB, Public Action, assessment, trading, KRX or provider dependency | shadow code/docs promotion eligible; v2 production exposure remains zero | Track A `5aed685...`, Track B `de2d7c9...`, Track C `209e1eb...`, Track D `c0c9139...`; separate bounded migration instruction required |
| `codex/20260829-cross-market-decision-engine-bounded-canary` | exact instruction `c62ddff` on main `f7e0829...` | exact KR 2 + US 2 decision blocks, evidence-bound continuity, safe decision-only suppression, historical BUY fixtures and pre-enable proof | extends the calibrated decision engine and existing AI delivery path; no Public Action, schema, DB, assessment, task schedule, global universe, trading, KRX, or peer dependency | bounded operating enablement eligible after exact-SHA CI; natural proof still pending | implementation `a639d32...`; enable exact subject config, then wait for 2 natural cycles per market; expansion HOLD |
| `codex/20260829-decision-calibration-p1-repair-before-canary` | exact instruction `5ccc8aa...` on main `3317ef7...` | BUY/HOLD/SELL taxonomy, timing/confidence calibration, directional change conditions, same-evidence blind rerun, bounded adjudication and exact test-sink proof | extends archive-only cross-market decision engine contracts; no production packet, task, assessment, Public Action, DB, trading, or canary activation dependency | promotion eligible after exact-SHA CI; canary remains OFF | implementation `9309521...`; next step requires a separate bounded canary instruction |
| `codex/20260829-cross-market-ai-decision-quality-review-before-canary` | exact instruction `86829a5...` on main `398f4fa...` | label-blind signed-in `xhigh` review, agreement screening, material adjudication, bias/calibration audits and canary recommendation | consumes immutable decision evidence only; no runtime import, task, Telegram, DB, assessment, Public Action or production-canary dependency | report/audit promotion eligible; production canary `NOT_READY` | review `cd829ff...`; close four bounded material P1 items, then repeat the same quality gate |
| `main` / operating | runtime baseline `23b17c4...`; final docs SHA resolves from Git | provisional Bollinger/price-label runtime plus run-44 validator convergence controls; KR live proof passed | no KRX/peer experimental dependency | current baseline after promotion | wait for remaining natural US proof |
| `codex/run-now-one-shot-kr-close-live-proof` | exact instruction `a0d8f19...` on operating main `23b17c4...` | operator-authorized one-shot regular KR close, exact production messages, V3 validator/delivery/scheduler proof | no runtime code, recurring schedule, Public Action, provider contract, DB schema, KRX breadth, or peer dependency | report/audit promotion eligible | evidence `239db58...`; `8/8` production delivery, one producer run, zero residual schedule; final docs resolve from Git |
| `codex/run44-v3-validator-convergence-cross-market-readiness` | exact instruction `1e8a008...` on operating main `026df71...` | frozen run-44 fixture/tests, cross-market read-only replay/test-sink tooling, validator ownership docs and final readiness | no runtime behavior change, provider addition, DB/task mutation, KRX breadth, or peer dependency | tests/docs promotion eligible | implementation `aa5e7d4...`; clean linear fast-forward after final exact-SHA CI |
| `codex/20260828-price-structure-major-sr-reality-gate` | exact instruction `4a57028...` on operating main `c5d26d4...` | separate indicator observation from price interaction; require confirmed price-anchor provenance before major ranking/rendering | reuses shared v3 engine and KR/US selective rollout; no ticker allowlist, threshold, market digest, Public Action, DB, task, or Production Assist dependency | promoted and deployed awaiting natural proof | implementation `c5f1fbc...`; next natural review is read-only |
| `codex/20260828-us-macro-zero-change-quality-gate` | exact instruction `e59c0e6...` on prior operating main `f4369c8...` | positive macro Fact ownership, grammar-safe semantic rendering, exact Telegram response validation and hash-bound reports | reuses existing US market plan/full renderer and safe test sink; no Price Structure calculation, KR renderer, Public Action, DB, task, or Production Assist dependency | promoted and deployed awaiting natural proof | implementation `5358556...`; next natural US morning review is read-only |
| `codex/20260828-us-market-price-structure-rollout` | exact instruction `2ee2016...` on latest operating/report main `178bc7e...` | deterministic full US morning market message plus selective active-universe Price Structure v3 rollout | reuses current-session market plan, existing v3 engine/renderer, and canonical test-sink safety; no Public Action, DB, task schedule, assessment, or Production Assist dependency | promoted and US-only enabled awaiting natural proof | implementation `1ba4635...`; wait for natural US market and stock proof |
| `codex/phase-8-2a-krx-market-breadth` | main experimental ancestry | KRX breadth, universe and publication telemetry | KRX experimental | no | separate KRX decision |
| `codex/phase-8-3-peer-sector-valuation` | KRX experimental final | original Phase 8.3 peer contract | Git ancestry includes KRX; peer code does not require KRX runtime symbols | no | promote after KRX or reconstruct cleanly |
| `codex/integration-phase-8-3-peer-only` | latest main | two peer-only commits through `e17d992c4c5d40030294eff5a74504e88ab35911` | no KRX code/schema dependency | prepared, not approved | peer-only review branch |
| `codex/phase-8-3-2a-free-peer-poc` | peer-only clean branch | free-source service, audit tooling, tests and archive reports | no KRX implementation ancestry | no | development evidence only |
| `codex/phase-8-3-finalization` | Phase 8.3.2A `ad1b98a4...` | conservative peer wording, Phase 8.3 closure and Master Workflow v7 | no KRX implementation ancestry | no | final experimental evidence only |
| `codex/phase-8-3-1-1-peer-provider-decision` | research chain | commercial/provider decision history | documentation ancestry | no | retained as reference |
| `codex/phase-8-5-4-natural-live-targeted-repair` | operating main `e925ee0...` | run-26 night-session, semantic binding, typed valuation, fallback parity and RR overlap repair | no Phase 8.3 or KRX experimental dependency | promoted | fast-forwarded to main through `3a6547e...` |
| `codex/phase-8-5-4-1-operating-shadow-promotion` | Phase 8.5.4 `3a6547e...` | live-readiness, promotion, operating smoke and persistent-state evidence | documentation only after validated code promotion | evidence branch | fast-forward documentation after exact-SHA CI |
| `codex/phase-8-5-4-2-night-futures-calendar-repair` | operating main `c7581a9...` | holiday-aware preceding-DAY lookup | existing operating night-futures path only | promoted | fast-forwarded through `7e7ab5a...` |
| `codex/phase-8-5-5-natural-reasoning-ownership-repair` | operating main `c6481d145ccc1583feaf6f6de7d005e774d56933` | run-27 security/framework ownership and repetition repair | existing operating AI packet/validator path only | promoted | clean linear fast-forward through `2ac9091...` |
| `codex/phase-8-5-5-1-us-numeric-summary-typed-repetition` | operating main `0402c1b19673d0ced6fcb1fef1cfcd1b1ef291fb` | run-28 business numeric ownership, typed skeleton and RR-delta repetition repair | existing operating AI policy/specificity/quality path only | promoted | clean linear fast-forward through `c915d44...` |
| `codex/phase-8-5-5-2-kr-structured-field-repetition` | operating main `f1ff6ae5f855f34c20274ea6e9ed8d801d51ae18` | run-29 canonical supply tuple, current-RR owner and typed prose repetition repair | existing operating AI binding/quality path only | promoted | clean linear fast-forward through `be2fb8f...`; final docs resolve from Git |
| `codex/krx-exact-slot-telemetry-capture` | operating main `006a997789d3e5ebac85ef867ae31296d175056c` | KRX readiness metadata, append-only evidence and 08:05/16:05 LaunchAgent | telemetry only; no breadth/packet/DB/AI/delivery import | promoted | clean linear fast-forward through `18bc7c3...` |
| `codex/phase-9-0a-cash-flow-capital-efficiency-architecture` | operating main `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9` | cash-flow period/lineage contracts, read-only official-source coverage, tests and architecture reports | extends existing financial lineage; no runtime import, packet, DB, KRX breadth or peer dependency | promoted architecture-only | clean linear fast-forward after exact-SHA CI |
| `codex/phase-9-0b-canonical-ocf-capex-fcf-core` | Phase 9.0A operating main `970ad2c3a1844e6dcbddbf47dff17d71170852d2` | official occurrence canonicalization, typed period derivation, deterministic PPE-only FCF, internal shadow audit | extends Phase 9.0A contract; no packet, prompt, public schema, renderer, DB, task, KRX breadth or peer dependency | eligible after exact-SHA CI | clean linear fast-forward only; user-visible behavior diff 0 |
| `codex/phase-9-0c-cash-flow-shadow-consumption` | Phase 9.0B operating main `86fafbf66dc690aa1ba5b9e0089c9098f1d7a6ef` | PIT/freshness/comparison/materiality sidecar, archive-only reasoning and validators | consumes Phase 9.0B Facts; no production packet, prompt, public schema, renderer, DB, task, KRX breadth or peer dependency | eligible after exact-SHA CI | clean linear fast-forward only; user-visible behavior diff 0 |
| `codex/phase-9-0d-selective-cash-flow-runtime-shadow-canary` | exact instruction commit `a24e4f2210f944fa7c43d8dbf8be1d1a8e652164` | detached post-delivery cash-flow sidecar, canary validation, receipts and idempotent audit archive | consumes Phase 9.0B/9.0C contracts; no Telegram, Public Action, assessment, fallback, Pilot, KRX breadth or peer dependency | promoted; natural LIVE PASS | clean linear fast-forward; run-30 proof complete |
| `codex/phase-9-0d-1-baseline-cash-flow-consistency-repair` | exact instruction commit `20367c056e6d1da7db3edee37818210c070e1e7d` on Phase 9.0D main | qualitative FCF sign/period/scope/provenance contract, packet/fallback repair and cross-artifact canary audit | consumes Phase 9.0B Facts and 9.0D contexts; no canonical number injection, DB migration, task, KRX breadth or peer dependency | promoted | clean linear fast-forward; one bounded user-visible prose correction; final SHA resolves from Git |
| `codex/phase-9-0e-selective-cash-flow-user-visible-integration` | exact instruction commit `309f5f1756d39d5972c5d4b48faaeab4862d8077` on Phase 9.0D.1 main | dynamic current-formal full-FCF selector, shared AI/fallback context, numeric/semantic validation, delta-first rendering and kill switch | consumes Phase 9.0B-9.0D.1 contracts; excludes KR, OCF-only, CCC/ROIC, KRX breadth, peer, DB and task changes | promoted and selectively enabled pending natural | clean linear fast-forward through `cf3194981124de2a6f85fbe81b145ef06e1db08d`; final docs resolve from Git |
| `codex/phase-9-1a-working-capital-evidence-architecture` | exact instruction commit `eaaadb1ac4fb5c9a7d3486ecc8274708c285ff79` on Phase 9.0E main `33c2f8be...` | point-in-time Inventory, separate trade/broad AR/AP, comparable-period and revenue/COGS relation architecture | extends canonical financial Fact metadata; audit/tests only, no packet, AI, fallback, Public Action, DB, task, KRX breadth or peer integration | promoted in Phase 9.1 chain | implementation `0d3b42715fc8964fe053d72e0ecc979fb78b14cc` |
| `codex/phase-9-1b-canonical-working-capital-core` | exact instruction commit `0952bee040133aa49a4ba494ecae76163e9a9511` on Phase 9.1A final `d4a4daf08ff5f68bc1072cc065e69ca5de5da145` | canonical Inventory/trade-broad AR/AP delta/YoY Facts, structured Revenue/COGS relations and audit-only snapshot | consumes Phase 9.1A Facts; no packet, AI, fallback, Public Action, DB, task, KRX breadth or peer integration | promoted in Phase 9.1 chain | full 9.1A -> instruction -> 9.1B lineage preserved |
| `codex/phase-9-1c-working-capital-shadow-consumption` | exact instruction commit `613d91d74d3a91c43ed61f98a13a2ca57b7a90ae` on Phase 9.1B final `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6` | PIT/freshness/materiality sidecar, exact trade/broad semantic guard, cautious industry reasoning, Unknown resolution and archive-only before/after audit | consumes only Phase 9.1B canonical Facts/relations; no production packet, AI, Telegram, fallback, Public Action, DB, task, KRX breadth or peer integration | promoted as main `d0dc76a...` | full Phase 9.1 dependency chain preserved; 9.1D canaries Inventory + exact Trade AR only |
| `codex/phase-9-1d-selective-working-capital-runtime-shadow-canary` | exact instruction commit `dc4e1cf14faa7cebf78eb8ba5a5e73b6369c991c` on promoted Phase 9.1C main `d0dc76a2446ee5ef9188d1b06dcb241df004c143` | detached post-delivery total-Inventory/exact-Trade-AR selector, validation and immutable receipt | reuses Phase 9.1B/9.1C contracts; no production AI/Telegram/fallback/Public Action/DB/task state mutation | deployment pending exact-SHA CI | clean linear fast-forward; natural metric-family proof remains separate |
| `codex/price-structure-v3-family-consensus-stability` | exact instruction commit `b0f81c8e16f588e314f93eb6097370e85f285241` on operating main `2984d7658b79d9c09d43e23929b71719f88a8c82` | endpoint dependency registry, hypothesis equivalence, typed ambiguity, family consensus, family-filtered confluence, reference audit | extends shadow v3 only; no production packet, SR, Telegram, task, Public Action, DB, assessment, or Production Assist dependency | integrated ready, not armed; selective enablement ready | clean linear fast-forward only; later enablement must preserve family omission and true-conflict controls |
| `codex/night-futures-publication-telemetry-repair` | preserved instruction `b7cf6a2...`, explicit latest-main merge `e7b2add...` after Phase 9.1D | natural production-attempt archive plus detached bounded 08:45/09:15 publication observer | reuses the existing provider/parser/session-basis path; no market-summary, AI, fallback, Telegram, Public Action or DB dependency | telemetry-only promotion eligible | merge latest main preserved both independent instruction histories; natural deadline proof remains pending |
| `codex/kr-investor-flow-reconciliation-attribution-repair` | exact instruction `e9d7c73...` on operating main `af89324...` | complete KR top-level participant reconciliation, explicit signal basis, shared AI/fallback attribution safety | existing OHLCV supply path only; no score formula, Public Action schema, task, Pilot, DB, KRX breadth or peer dependency | promoted after exact-SHA CI | clean linear fast-forward; natural confirmation remains parallel |
| `codex/phase-9-1e-working-capital-user-visible-preintegration` | exact instruction `99f7e86...`; explicit merge `ee78eb7...` of Track A main `7c0e440...` | family-level natural-proof gate, OFF-by-default modes, Inventory/exact-Trade-AR preview, cash-flow redundancy, parity and kill switch | consumes only committed 9.0E/9.1D evidence; no production AI/fallback/Telegram/Public Action/snapshot/DB/task import | promotion eligible with feature OFF and exact-SHA CI | preserve instruction and Track A histories; future enablement requires a small family-specific instruction after `LIVE_PASS` |
| `codex/phase-9-1e-1-inventory-only-user-visible-enablement` | exact instruction `880e7a9...` on main `fb44510...`; explicit merge `018af42` of run-32 natural evidence | selective total-Inventory context in production AI/fallback with exact parity, typed `%p` binding, OFF kill switch and delivery metadata | reuses 9.1E contract; Trade AR/broad AR/AP/advanced ratios remain blocked; no ticker allowlist or state mutation | promoted and activated Inventory-only; natural user-visible proof pending | Inventory `LIVE_PASS_RUN32`; exact Trade AR `NOT_OBSERVED`; preserve both histories |
| `codex/kr-non-trading-day-producer-guard-orphan-reconciliation` | exact instruction `2125562...` on operating main `2244b8f...` | shared XKRX producer-role guard, packet-bound delivery-intent ordering, and exact run-33 orphan reconciliation tooling | existing KR producer, packet hold, and notification-delivery paths only; no Inventory/Trade-AR, cash-flow, investor-flow, night-futures, KRX breadth, Public Action, schema, or task-schedule change | promotion eligible after exact-SHA CI; natural weekend/holiday proof remains pending | implementation `c26c935...`; clean linear fast-forward and operating restart required |
| `codex/kr-shadow-cohort-activation-gate-packet-persistence-repair` | exact instruction `7da8d88...` on operating main `7b78f99...` | production packet persistence and Shadow readiness separation for natural KR run 36 | existing AI packet/producer/fallback path only; Inventory mode, Trade AR, macro temporal, investor-flow, Public Action, schema, task schedule and DB unchanged | promotion eligible after exact-SHA CI; natural KR proof pending | implementation `64086c4...`; clean linear fast-forward and operating restart required |
| `codex/kr-us-structured-data-first-quality-v2` | exact instruction `e04403c...` on operating main `b7dc151...` | exact structured market context acquisition, KR KRX fail-closed cross-section, US RSP/sector context, and message-quality v2 | extends the common market adapter and limited Free Analyst canary; no paid provider, schema, schedule, DB, Pilot, full-mode, Open Research, or manual delivery dependency | promotion eligible after exact-SHA CI | implementation `1a6d2f4...`; preserve `1/2/3`, full OFF, and natural US then KR proof |
| `codex/20260826-kr-postdeploy-live-rehearsal-us-exchange-breadth-v1` | exact instruction `d7a0101...` on operating main `73de7d4...` | bounded KR latest-completed-session guard plus official Nasdaq-listed advances/declines/unchanged sidecar | extends Kiwoom session validation and the common structured market adapter; no NYSE derivation, participant-flow proxy, schema, task, DB, Pilot, full-mode, Open Research, Trade AR, or manual delivery dependency | safe partial promotion eligible after exact-SHA CI | implementation `0e2fc65...`; run-37 exact breadth remains publication-pending and next natural proof must not be manufactured |
| `codex/kr-digest-us-entity-synthesis-bounded-repair` | exact instruction `8cf5226...` on main `760dbe1...` | KR local-first digest planning plus US entity-specific and cross-message synthesis quality | consumes existing structured context and stored thesis evidence; no provider, Public Action, schema, task, DB, Pilot, full-mode, Open Research, Trade AR, or canary-limit dependency | promotion eligible after exact-SHA CI | implementation `f2326c3...`; natural proof is read-only and Open Research work may continue in parallel |
| `codex/price-structure-v3-renderer-integration-micro-repair` | exact instruction `2ac7eaa...` on current-data validation main `bb4e5b0...` | Fib range preservation, current-vs-stored ownership labels, stale legacy technical suppression | consumes frozen v3 current-data evidence and existing `chart:stored_price_rules`; no calculation, packet, Telegram, task, DB, assessment, or activation dependency | shadow promotion eligible after exact-SHA CI | implementation `4246efb...`; next task is separately instructed bounded selective enablement |
| `codex/20260827-kr-afternoon-natural-market-data-review-and-reproof` | exact instruction `107f40b...` on operating/report main `a1fb1a7...` | read-only run-42 identity, Kiwoom family, registry, local-first, parity and exactly-once natural proof | consumes stored production evidence only; no runtime, task, Telegram, DB, assessment, Price v3 or Production Assist mutation | report-only promotion eligible | KR Track B `LIVE_PASS_RUN42`; Track C still waits for independent natural US reproof |
| `codex/20260827-kr-size-sector-message-selection-bounded-repair` | exact instruction `794c6f5...` on latest report main `de25986...` | required complete KR size/style and bounded relative sector-extrema selection, shared AI/fallback retention, utilization validation | extends the existing KR local-first plan and shared renderer only; no provider, numeric-registry policy, reconciliation, concentration, US digest, Price v3, DB, task or Telegram dependency | promotion eligible after exact-SHA CI | implementation `6a54db1...`; replay PASS, natural KR reproof pending |
| `codex/20260827-kr-top3-sector-price-structure-preenablement` | exact instruction `0c95ddc...` on main `97d9081...` | default-OFF deterministic KR sector TOP3 plus monitored-KR Price Structure v3 runtime wiring and fail-closed preflight | reuses run-42 context, existing v3 engine/renderer, and existing sink audit; US, Public Action, DB, task schedule, Telegram production, and Production Assist remain unchanged | code promotion eligible; feature activation blocked | implementation `a7de99c...`; Track C blocked by missing dedicated test sink, Track D not started |
| `codex/20260828-us-morning-natural-market-data-reproof` | exact instruction `18d3685...` on operating main `910e2f7...` | read-only run-43 identity, current-session ETF/RSP/sector, breadth, macro, shared-plan, parity and exactly-once proof | consumes stored production evidence plus one official read-only Nasdaq publication check; no runtime, task, Telegram, DB, assessment, archive, Price Structure or Production Assist mutation | report-only promotion eligible | US Track A `LIVE_PASS`; next action `REVIEW_MASTER_GATES` |

The Phase 8.3 original branch has a hidden Git ancestry dependency but no required KRX code,
schema or runtime import. The clean branch resolves that promotion risk. Phase 8.3.2A starts from
the clean peer-only branch and reads a KRX archived issue-reference payload only as POC input; it
does not import or contain KRX provider/readiness code.

Phase 8.3 is now closed as `SELECTIVE_OPTIONAL_CONTEXT`. Preserve the clean peer-only branch as the
promotion-ready tooling path and preserve Phase 8.3.2A/finalization as experimental result history.
No new integration branch is needed, and no Phase 8.3 branch is approved for promotion here.

Promotion paths remain:

1. KRX first: `main -> KRX -> peer`.
2. Peer first: `main -> codex/integration-phase-8-3-peer-only`; KRX commits excluded.

Phase 8.5.4.1 performed no branch deletion, force push, history rewrite or tag rewrite. It promoted
only the clean Phase 8.5.4 operating-main descendant and did not include either experimental chain.

Phase 8.5.4 intentionally returns to operating main because it repairs the natural run-26 path.
Its KRX-named files modify the existing operating night-futures adapter only; they do not import the
Phase 8.2A market-breadth provider, readiness telemetry or peer experimental implementation.

Phase 8.5.5 likewise starts from operating main. It changes only runtime specificity metadata,
packet framework roles, security-language validation, Daily Review policy, tests and archive-only
evidence. It imports no Phase 8.3 or Phase 8.2A experimental code and changes no KRX provider path.

Phase 8.5.5.1 likewise starts from the latest operating main. It changes only the Daily Review
policy, runtime specificity/quality ownership, tests and run-28 archive-only evidence. It imports no
Phase 8.3 or Phase 8.2A experimental code and makes no KRX provider, schema or task change.

Phase 8.5.5.2 likewise starts from the combined latest operating main after Phase 8.5.5.1 and the
telemetry-only KRX capture. It changes only AI candidate ownership, typed quality, Daily Review
policy, tests, and run-29 archive-only evidence. It does not import KRX breadth, Phase 8.3 peer
implementation, or any provider/task/database schema change.

The exact-slot telemetry branch also starts from the latest operating main. It reconstructs only the
Phase 8.2A readiness and append-only observation contracts, not the breadth engine or market-packet
integration. Its dedicated LaunchAgent is operating evidence collection; it does not alter the four
Codex AI-review Scheduled Tasks or any user-visible message path.

Phase 9.0A likewise starts from the latest operating main and excludes the preserved Phase 8.3 and
KRX breadth experimental ancestries. Its service module is a non-runtime eligibility contract, and
its evidence generator is archive/read-only tooling. It changes no packet, prompt, renderer,
provider scheduler, database schema, or delivery path. Phase 9.0B must start from the final promoted
Phase 9.0A main and retain this separation.

Phase 9.0B starts from that final Phase 9.0A main. Its two new services are imported only by tests
and the archive-only evidence generator; production packet and API modules do not import them. It
uses stored SEC/OpenDART evidence, performs no provider network call, and retains KRX breadth and
peer experimental code outside its ancestry. Phase 9.0C must preserve this boundary until an
explicit shadow-consumption contract is reviewed.

Phase 9.0C starts from final Phase 9.0B operating main. Its consumer service is imported only by
tests and the archive evidence generator. It reads canonical Facts and immutable replay artifacts,
performs no provider network call, and does not enter production packet, prompt, API, fallback,
renderer, task, database, or delivery imports. Phase 9.0D may add only a delivery-isolated runtime
shadow canary unless a later explicit user-visible gate approves more.

Phase 9.0D starts from its promoted, immutable work-instruction commit. The existing AI-review CLI
imports only a best-effort detached launcher after a terminal production result; all cash-flow
context, output, validation and receipts remain under a separate canary archive namespace. It does
not import Telegram dispatch into the canary, alter the four task configurations, or change any
production packet/output schema. The natural run-30 canary closed the Phase 9.0D behavior proof.

Phase 9.0D.1 starts from its docs-only instruction commit, preserves the canary's detached boundary,
and sanitizes only unsupported qualitative baseline prose. It neither stores nor renders new
canonical amounts. Phase 9.0E is ready for a separately instructed selective rollout and remains
independent of KR coverage, CCC, ROIC, KRX breadth, and overall AI-assisted delivery completeness.

Phase 9.0E starts from its immutable instruction commit and reuses the canonical/core/consumption/
canary/baseline chain. It changes the production packet and fallback only when the operating mode is
SELECTIVE and every dynamic gate passes. The operating config is external to Git and can return to
OFF without reverting code. Natural proof remains pending; Working Capital Canonical Core
architecture may proceed independently while broad user-visible expansion waits.

Phase 9.1A starts from the immutable instruction commit on the clean Phase 9.0E operating baseline.
Its service is consumed only by tests and the read-only evidence generator; production packet,
selector, fallback, Public Action, database, task, and delivery imports are unchanged. The branch
uses stored SEC evidence plus a bounded official OpenDART CFS audit cache. Promotion is deferred for
the KR natural window and must not be combined with an unreviewed natural P0. Phase 9.1B must retain
the exact trade-versus-broad semantics and selective fail-closed scope.

Phase 9.1B starts from its immutable instruction commit on the final Phase 9.1A branch rather than
main, because 9.1B consumes the unpromoted 9.1A Fact metadata and source mappings. Its core service
is imported only by tests and the read-only evidence generator. Promotion must preserve the full
linear dependency chain and remains deferred until the separate KR natural review is consumed.

Phase 9.1D starts from the promoted Phase 9.1A -> 9.1B -> 9.1C main. The production AI-review job
imports only a best-effort detached launcher after terminal delivery; the canary consumes no output
from the independent cash-flow canary. The parallel night-futures telemetry branch preserves its own
instruction commit and must merge latest main explicitly if Phase 9.1D lands first.

The night-futures telemetry branch did merge latest Phase 9.1D main explicitly before implementation.
Its only production-path change is a best-effort copy of provider diagnostics after the already
scheduled natural call. The detached observer has an independent LaunchAgent and cannot write the
market summary, AI archive, delivery receipt, Telegram, or DB. The production deadline and session
basis remain unchanged; a future natural evidence review, not this merge, owns any policy decision.

Phase 9.1E preserves its own instruction commit and explicitly merges the independently promoted KR
investor-flow Track A before implementation. Its new service is imported only by tests and the
archive generator; the config field defaults to OFF. The later Phase 9.1E.1 enablement proved the
Inventory mechanism and activated only selective Inventory, while exact Trade AR remains
`NOT_OBSERVED` and OFF. Neither family proof is coupled to investor-flow natural confirmation.

The KR non-trading-day producer repair starts from its immutable docs-only instruction commit on the
latest operating main. It reuses the XKRX role-target resolver before any KR provider/run/delivery
state and requires a persisted identity-matching packet before queue/hold eligibility. Its bounded
maintenance command reconciles only the exact run/date/packet/count identity and is not a general
notification editor. The run-33 mutation is limited to seven stock rows plus one digest row; all
remain unsent with null `sent_at`. Natural weekend/holiday proof remains parallel to the Inventory
user-visible observation.

The macro digest temporal repair starts from docs-only instruction commit
`951558c0ec79f84b739eff1cbafd2870eb6f3fba` on the latest operating main. It adds a derived
eligibility sidecar to existing macro observations and changes only daily-signal consumers,
rendering, AI market context, validation, calendar-aware US early-close handling, tests, and
read-only replay evidence. It adds no provider, DB migration, KRX breadth ancestry, night-futures
policy, cash-flow/working-capital mode, task schedule, or production operation. Natural proof is a
parallel observation after deployment.

The KR Shadow gate packet repair starts from its exact docs-only instruction commit on the latest
operating main. It preserves the v3.2 numeric/profile gate as AI claimability, adds a separate
production persistence contract, and keeps packet-bound ordering. It changes no public output,
feature selector, provider, DB schema, task schedule, or Production Assist state. Its retrospective
run-36 replay is no-send evidence only; the next natural eligible KR run owns live proof.

The legacy macro/shadow registry closure starts from docs-only instruction commit
`2ddec88382f0aff32fcae68a87d1aff62f60f2ef`, a linear descendant of the KR Shadow packet repair.
It adds a non-destructive compatibility view for legacy macro briefings and exact non-prose
registrations for investor-flow reconciliation numerics. It changes no provider, schema, task,
feature mode, packet-persistence contract, or Production Assist setting. The 19:34 replay is
isolated no-send evidence; natural KR proof remains pending.

Common AI Core v1 production integration starts from immutable instruction commit
`3df40de53cf35ff5c47d662e0a14fbf9e30be3f7` on base
`f7d2552185ff2ff6d932337e7555ce02f87fa613`; implementation commit is
`4bcf117fa36d9a74c45e6f9c2626e38e07e52bd3`. It ports only the minimum Free Analyst, evidence-lock
adapter, and Adaptive Renderer units from their audited shadow branches. Open Research and Event
Attribution are explicitly excluded. The integration depends on the existing AI delivery receipt,
runtime quality, numeric/semantic/temporal validators, and Production Assist pilot gate. It adds no
dependency on Phase 9.0E, Inventory/Trade AR, KRX breadth, macro temporal, or provider work. The
limited canary remains `READY_NOT_ARMED`; full cohort rollout is not a descendant authorization.

The explicit limited-canary branch starts from main `cd0fb79a6925d75029debb24f00d1a4c7495aa75`
and its immutable instruction commit `73802b8849f674698bfdb3bfd7f3d0df89c236b2`. It changes no
production code. Runtime activation uses the existing independent Settings switch and preserves
Branch-B Pilot semantics, deterministic fallback, receipts, schemas, schedules, Inventory,
cash-flow, and all research exclusions. Natural KR proof must precede US completion, but neither is
manufactured or required for the enablement commit itself.

The Kiwoom KR market-context branch starts from immutable instruction commit
`f45c6c9d47253c0ad8cad9affcf0eb54be188117`, whose parent is the exact structured-data-quality-v2
main. It extends only the existing market cross-section, structured context, adapter, and KR packet
acquisition boundary. It does not import Open Research, alter canary limits, change Public Action or
schema 4, modify schedules, or add a trading/account surface. KRX telemetry remains an independent
parallel provider track. Production activation is environment-only and fail-closed; natural proof
must not be manufactured.

The Fibonacci variable-anchor repair branch starts from docs-only instruction commit
`d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890`, whose parent is operating main
`75328361b6831d44c647c64e0d811da6251ea673`. Its new service is imported only by tests and the
archive trial generator. The signed-in variable runtime receives only the frozen public
`price-only-ai-anchor-packet-v1`; it does not enter scheduled task, production packet, fallback,
Telegram, Public Action, or assessment imports. Promotion preserves SHADOW state because actual
monthly/weekly stability failed. The open P1 is feature-local and has no ancestry dependency on
Open Research, KRX telemetry, cash flow, working capital, or natural delivery proof.

The final Fibonacci consensus branch starts from immutable instruction commit
`39cab7ed8b1cb3bebea1bd1240498caa454bd09a`, whose parent is operating main
`987a684f72b96c9d549eaf4d4328590bb0b7cd81`. It supersedes only the feature-local variable-anchor
P1 state. The new service remains archive/test-only and depends on existing deterministic
multi-timeframe structure code; production packet, selector, fallback, Telegram, Public Action,
task, and assessment imports remain unchanged. A later enablement branch must descend from this
closure and preserve backend SR ownership, typed abstention, per-timeframe consensus omission, and
the existing tolerances. It has no ancestry dependency on Open Research, KRX telemetry, cash flow,
working capital, or natural delivery proof.

The Price Structure Wave Fibonacci v3 branch starts from immutable instruction commit
`5bcf2a1a73a10c73db12c37e93a51652983599d5`, whose parent is operating main
`aa79fefec9fe9da43c1b241a68f7ec43f9247b1d`. Implementation commit
`63b3ce219f996ea23b0a2a254d842bbb579adef2` adds only a new archive/test service, evidence
generator, and focused tests. No production module imports the v3 service. It preserves the prior
consensus safety principles while redefining price structure around monthly wave ownership,
weekly confirmation, independent timeframe SR, and source-provenance-preserving Fib families.

The branch is promotable as shadow evidence but is not a production-enablement ancestor: daily
1200 coverage and SK reference-method review remain feature-local material P1. It changes no
Open Research, KRX telemetry, cash flow, working capital, Free Analyst canary, task, schema,
Telegram, DB, assessment, or Production Assist state.

The v3 temporal/cycle/feedback bounded repair starts from exact instruction commit
`82cb04e2880d1ed7b0405e1ddd20c5f333305394`, whose parent is prior v3 final main
`d78940be0aab43227a1eb76bc0d9caa6f56c0d00`. Implementation commit
`bea877d3a6a9977c19832cbde28ed235676929d2` extends only the shadow v3 service, canonical history
cache contract, archive evidence generator, architecture, and tests. It does not add a production
import or change user-visible routing. A later bounded enablement must descend from this repair,
admit only stable eligible subjects, omit material variation/abstention, and preserve deterministic
SR fallback. The unavailable user reference remains a non-blocking P2 and is not an ancestry
dependency.

The v3 family-consensus stability repair starts from immutable instruction commit
`b0f81c8e16f588e314f93eb6097370e85f285241`, whose parent is operating main
`2984d7658b79d9c09d43e23929b71719f88a8c82`. Implementation commit
`631e82f202b6f081866ef83c8b67b2138a8b51d8` extends only the shadow v3 service, archive evidence
generator, contracts, tests, and documentation. The user-supplied wave engine remains isolated as
reference data and is never imported by runtime code. Any later enablement must consume only exact
or price-equivalent endpoint families, filter unstable families before confluence, retain TSLA/TSM
true conflicts, and preserve current tolerances and deterministic SR. It has no dependency on Open
Research, KRX telemetry, cash flow, working capital, task execution, or natural delivery proof.

The v3 pre-enablement micro-repair starts from exact instruction commit
`38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8`, whose parent is operating main
`f53434e38e374a41436f61fc06864357b783a516`. Implementation commit
`84f8f549bc8fa0338309a84b23b2738f2e357646` narrows family membership semantics, adds
display-only technical-zone formatting, synchronizes Investment Knowledge v3.1, and extends only
the archive/test evidence path. A later bounded enablement must descend from this repair, preserve
diagnostic-versus-active membership, retain explicit ambiguity and cross-run selected competitors,
and keep raw numerics unchanged. Production packets, Telegram, tasks, Public Action, assessments,
and Production Assist remain outside this branch.

The v3 SR-completeness/proximity repair starts from exact instruction commit
`7267ca1d3e518d39986941bfda1d6447560db344`, whose parent is operating main
`cb5e660a617cc5bdff7cc4fa8d0d44e1fab27317`. Final code implementation
`176f3e73eb097fac99f4038a8987b610954804cc` extends only the archive/test v3 service, tests, and
evidence generator. A later enablement must descend from this closure and preserve deterministic
SR-first ownership, nearest/major separation, active cross-zone relevance, typed fallback
provenance, and family-stable Fib-only confluence. It has no dependency on natural monitoring,
Open Research, KRX telemetry, cash flow, working capital, tasks, or Production Assist.

The v3 current-data shadow-message validation starts from exact instruction commit
`688c17280a10e91214d4bd9888522fdc6f9bc0c5`, whose parent is the SR-completeness final main
`68e927b5eaf2a10dadd5faafa26de9c18b67170f`. Validator implementation
`ef586c3816ff76417d2620636975d054935533d4` adds only an archive/read-only evidence generator and
focused tests. It does not enter a production import path. A later selective enablement must
descend from this validation, preserve KR `2026-08-26` / US `2026-08-25` completed-session gating,
admit only ELIGIBLE or ELIGIBLE_SR_ONLY subjects, and retain all numeric/provenance and business-text
parity gates. It has no dependency on natural monitoring, Open Research, KRX telemetry, cash flow,
working capital, tasks, or Production Assist.

The v3 renderer-integration micro-repair starts from exact instruction commit
`2ac7eaaede9cb8d9047173bbec5f2bd99c665573`, whose parent is the final current-data validation main
`bb4e5b0772f56b22ac49cb1c2bf72287391b8b19`. Implementation commit
`4246efb4f8afa3516402d1df7864967c177ac6e7` adds a pure renderer service, archive replay, policy
documents, and focused tests. Production modules do not import the renderer. A later enablement
must preserve complete material Fib ranges, explicit current/stored ownership, stale-technical
suppression, source registries, and the unchanged eligibility cohort.

The v3 legacy-detector false-positive repair starts from exact instruction commit
`97b65fc1d258339563b54961a83acd997867e11e`, whose parent is renderer-integration final main
`a4c6713649137180e0b37a4eb42ae6b35f07423c`. Implementation commit
`3685aa991589ca0e7cc560104d4ebf8289e3f91d` changes only the shadow renderer detector, archive
evidence generator, architecture, and focused tests. A later selective enablement must descend from
this closure and preserve protected structural fields, complete token boundaries, sentence-level
MU suppression, existing SR/Fib numerics, current/stored ownership, and the unchanged eligibility
cohort. Production imports and runtime behavior remain unchanged.

The 2026-08-26 master validation starts from immutable instruction commit
`e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d`, whose parent is operating main
`33f82227245f3757815a231cdaad86b75f8c2b76`. Track A implementation
`505a3a2c63390c683323192b7ca516513dfe7a24` and combined compatibility repair
`65196d2d2a54483143d23d1c61500f70d0e2325a` are the code ancestors for the next bounded KR repair.
Track B report `f089ebe1bd2f47612b36a3093ed57f35f39bf67f` is read-only evidence.

No Price Structure Track C branch exists because Track B has two material P1s. A future selective
enablement must descend from the eventual bounded KR local-first/numeric-registry closure and may
begin only after the Track B replay and natural gate return P0/P1 `0/0`. This stop does not erase
the prior v3 shadow readiness and does not block parallel natural US reproof.

The bounded KR closure starts from immutable instruction commit
`f6ba660048d3fa520e3aeb43d04036c119764292`, whose parent is operating main
`95553b931150f4dd61573888e9fa94198eb43041`. Track A
`3828c2093ede67ab2f61c6fceb13a670b22931db` and Track B
`d6c766543205ee74f2c4023cd17a0bfd682b4a7f` are integrated by code commit
`848eb80f6ce6504a9a855973b591ee0749167514`. Any later Track C must descend from this closure and
must preserve local-first digest ownership, exact sector-count semantics, unique market-scoped
sector fact identity, unresolved reconciliation suppression, and zero unsupported numeric paths.

Immutable replay is PASS at P0/material P1 `0/0`; the remaining dependency is observation of a
natural KR close. This observation requirement does not authorize manual production execution and
does not arm Price Structure v3. Parallel natural US proof remains independent.

The US morning natural review branch starts from immutable instruction commit
`5377d5e4f15a82e01ac40b6d50d47eee9ef0a30c`, whose parent is clean main
`ae4d22a4134341f7dfeffc4aef918c97e56091b2`. It is report/state-only and makes no production
behavior change. Natural run 41 proves current packet ownership and exactly-once delivery but finds
one material Track A P1: current-session ETF/RSP/sector evidence was present canonically and absent
from both AI and deterministic market digests. A future `BOUNDED_US_MARKET_REPAIR` must descend from
the promoted review state and preserve temporal roles, level-only semantics, exact-session breadth
fail-closed behavior, numeric binding, canary limits, and fallback parity. It must not depend on or
arm Price Structure Track C; KR natural reproof remains a separate pending dependency.

The bounded US current-session evidence repair starts from immutable instruction commit
`c17f67a5d385b51d1249aa7b3d5452207938f084`, whose parent is promoted review main
`d625eaca37a461f9754e080362778986cddb2b52`. Track A
`c4b02a10c2b7da0184c7dba26c7c1db39344f258` and Track B
`2f7d6853605541a81e430754d7b6fea98ccbbbea` are integrated by implementation
`069f002437163bff1df7aa6e258918c1777d5dfa`.

Any subsequent US natural-proof report must descend from this repair and preserve the shared
current-session-first digest plan, typed omission reasons, RSP/style ownership, backend sector
relation, evidence-ref utilization validator, existing numeric registry, and macro temporal
policy. Replay is PASS at P0/material P1 `0/0`; the remaining dependency is one naturally scheduled
US morning observation. This branch does not satisfy the separate KR natural gate, does not create
Price Structure Track C, and does not arm v3.

The KR market pre-enable audit branch starts from exact instruction commit
`f161bc1c724cfd431efaaa458af61e02a378daeb`, whose parent is clean main
`de352342f15a75069289f35f00b4bd24ddcdd19f`. Audit implementation
`7d2823c236c458cf76c77faae043c6288e46e65e` adds only an evidence generator and routing safety
tests. It introduces no production import, runtime gate, Telegram intent, task, DB mutation, or
feature activation.

A future pre-enable rerun may descend from this audit only after one dedicated TEST sink is
configured outside the production recipient. It must preserve the collision guard, use the frozen
run-42 production-equivalent packet unless a newer completed-session instruction supersedes it, send
exactly once, and leave the already-active code default unchanged unless a separately proven existing
gate is discovered. This dependency does not arm Price Structure v3 or alter the independent US
natural-proof track.

The KR daily-history and nearest-semantics repair starts from exact instruction commit
`0a8dae7eeca7126844094f0aebcc7a7df0bea606`, whose parent is clean main
`43731f015901b96e2dee3af009b9e1d074382349`. Independent Track A
`da82d89c2e1c3bc125442128da1573d532263d74` and Track B
`83f3d643bc2cb40d9039c1d965647d01a43769e2` are integrated by code commit
`04fb7ad7646a55e03000134f50b3f402a6c49c87`.

A future KR pre-enable rerun must descend from this repair and preserve the provider's 1,000-bar
transport ceiling as `PARTIAL/provider_limit`, the 1,200-bar canonical target, completed-bar and
look-ahead gates, provenance-bound proximity labels, one primary user-visible semantic per side,
and old-000660 negative control. It must also preserve explicit KR-only renderer opt-in, unchanged
US/TOP3 behavior, both default-OFF guards, and the dedicated-test-sink requirement. This repair
does not itself authorize a Telegram send, runtime enablement, operating promotion, or Production
Assist.

The KR daily-1200 extension/degradation policy starts from exact instruction commit
`3e42f3fad2e32ff1b3cca47861cfb9704095ce28`, whose parent is clean main
`48a699798462639b27056523ef8fdd94b261092b`. Track A
`c9e8fc1e25394857bd88d4652e3a8b1e88638011` proves the supported provider capability; Track B
`d60b7b2a9edecbad0ed54c2151ecfba163478522` implements the verified degradation contract; Track C
`f957bea48e1bf8df23c6b8fe769812ade5663456` closes the frozen seven-ticker replay.

Any later pre-enable rerun must descend from this closure and preserve the 1,200 canonical target,
1,000 provider cap, `PARTIAL_SAFE/provider_limit` semantics, official-closure-aware gap audit,
proximity/Fib/current-cycle validators, and old-000660 negative control. It must not infer an older
window from unsupported parameters, use the static backfill artifact as runtime truth, arm either
guard, alter US/TOP3 behavior, or promote operating without separate authorization.

The final KR pre-enable instruction branch starts from exact instruction commit
`9f37cfad97487876d6dfa63c03750f4dab664dbf`, whose parent is clean final main
`0ede6a0eb3335371322d1f7921b350d07f669f9a`. Track A evidence commit
`05b57901f7cf25086b580510aac6a6e72329cdfc` records the fail-closed result. No Track B or Track C
branch exists because the dedicated test-sink prerequisite failed.

A future rerun must descend from this evidence state after exactly one approved non-production
recipient is configured through the existing secret/config mechanism. It must first prove sink and
intent isolation, then rerun Track A; only a PASS may authorize Track B. It may not reuse the
production recipient, treat prior replay as current test-send proof, promote operating, or change a
feature flag while this P1 remains open. The operating checkout intentionally remains
`43731f015901b96e2dee3af009b9e1d074382349`.

The 2026-08-28 resume branch starts from exact instruction commit
`68ede1eae42315d94a89023fbc6c1f9be07fc99d`, whose parent is final main
`6a2068b00f10e28c5eba2133d2423293f4a1bb25`. Evidence commit
`69e4bd6bc15da2a654ab6dcb678263f0ea049d37` confirms the operator-supplied secret is still absent.
No data-collection, delivery, operating-promotion, or enablement descendant exists.

A future execution must descend from this stop state only after an operator configures exactly one
accepted test recipient outside git. It must repeat sink resolution and direct equality isolation
before resolving the KR session. The absence of a secret cannot be repaired by code, Telegram
discovery, production-recipient reuse, or another alias framework.

The resumed execution descends linearly from that stop through final main
`5b926a9a1edf396244ef83ab127d7608ceefe390` to implementation
`315081005198e7b5676e9383f10d4a52b3d3ca34`. The implementation adds only canonical Settings
acceptance for the ignored test key and an isolated audit sender with duplicate-send refusal; it
does not alter the production Telegram recipient or delivery-intent path.

The test-sink gate, run-42 preflight, exact 8/8 test delivery, feature-off promotion, TOP3-only
smoke, and KR Price Structure 7/7 smoke all pass. Subsequent work must treat KR TOP3 and KR Price
Structure as enabled awaiting natural proof, keep US Price Structure and Production Assist OFF,
and preserve independent rollback. No new branch should reinterpret the old blocked reports as
current state; the 20260828 resume readiness artifact is authoritative.

The KR market-internal formatting branch starts with exact instruction commit
`dd1b5eb712081c222bcfe1b4465d4fe0aac5f89a`, whose parent is enabled main
`d00b5b6c89e67748d6b1d376e709770ae747566c`. Implementation
`03a418ab1f616d0063becf3928a1327056dd2d66` changes only canonical KR size/sector presentation and
adaptive/deterministic renderer placement.

Subsequent natural-proof work must descend from this implementation and preserve the exact value,
TOP3, selection, and provenance parity proved against run-42. It must keep KR TOP3 and KR Price
Structure ON, US Price Structure and Production Assist OFF, and must not reinterpret the single
non-production test message as natural production proof. The next authorized action is read-only
review of the next natural KR close message.

The US night-futures/current-time E2E branch starts with instruction commit
`f6ab0168d3ef0d8ce1e2b5980ea7aae147db0c75`, whose parent is clean main
`a3050b19e3b983fe71ae3f68f400fc2e9a8d66aa`, and deploys implementation
`f6bc769f823429426474a38f007dc8196b4e5f43`.

Subsequent US natural-proof work must preserve gate-owned night-futures summary projection, fixed
series Fact IDs, no stale or unavailable directional output, exact response-payload validation,
and the generic daily source-session alignment guard. WRD's current block is evidence-derived, not
a ticker policy. No descendant may manually trigger natural proof, reuse the production recipient
for tests, expose unstable Fib/targets/stops, or reinterpret the historical fixture as a natural
runtime PASS.

The provisional-Bollinger/price-label branch starts from exact instruction commit
`73286dd44135bbc30ef3a145e02f5db81aedbdea`, whose parent is deployed main
`5500f539fc93a9162f762cef4f7069f24d0350db`. Implementation
`8c3bb493dc45a12c837053e08361f949ff771f00` preserves the completed-bar dynamic layer and the
major-SR reality gate while adding a strictly non-authoritative partial-bar layer and explicit
price ownership.

All descendants must preserve partial-bar OHLC validation, one-line provisional budget,
near/major/stored/Fib/wave exclusion, current/structure price-label metadata, and SNDK/WULF
no-bypass controls. The corrected full-message test delivery is authoritative; the earlier
abbreviated-artifact test attempt is diagnostic only. No descendant may reinterpret test-sink
evidence as natural proof, manually invoke production, or enable Production Assist.

Evidence commit `d3a58c953c2dd6d100031421770be3a54d0328b5` passed Actions Test/Lint and is the
linearly deployed main/operating runtime. Post-deploy API/OHLCV health and frozen US `13/13` plus KR
`7/7` replay pass. Natural proof remains pending, so descendants must begin from deployed main and
preserve the no-manual-proof boundary.

The 2026-08-29 US morning review starts from exact instruction commit
`428836d4a997a10eb7dd1d1935acdea8ea469b54`, whose parent is clean main
`104b0a04d326e66178c9f432798fdeb6cf82a85a`. Read-only evidence implementation
`7fc982ecce30a0af261dcda198ef50280e707531` consumes immutable run-45 artifacts, the official
Nasdaq archive, canonical night-futures telemetry, and a read-only delivery database.

Any bounded AI repair may descend from this evidence but must preserve completed session
`2026-08-28`, exact deterministic market-message parity, official breadth fail-closed behavior,
the `2026-08-29` night-session omission, macro temporal selection, and zero duplicate delivery.
It may not reinterpret this market review as US Price Structure natural proof or mutate Telegram,
tasks, DB, assessments, schedulers, feature flags, or Production Assist.

The bounded US night-futures/run-45 repair starts from exact instruction commit
`f8ca4fcb4557037468e35578a98a66aa9cb750b5`, whose parent is clean main
`3cc91234ef88c655df981b0366a17045c95983f3`. Implementation
`f621b0ab253a3e9fc6752f7d7aff9ccdad06ca19` consumes the immutable run-45 candidates and official
KRX daily source evidence.

All descendants must preserve KRX night-session end-date semantics, safe omission when the target
business-date row is unpublished, strict structured numeric/semantic validation, existing runtime
quality thresholds, and Price Structure numeric ownership. The isolated 14-message test-sink proof
does not count as natural production proof. No descendant may relabel the prior night session as
Friday/Saturday current data, expose recipient values, manually run production, create a production
delivery intent for proof, or enable Production Assist.

The cross-market decision-engine branch starts from exact instruction commit
`ec6ea8fa4449fd34961ecbbcf995064c46ff94a2`, whose parent is clean operating main
`7269120fb4d97abb61c5d5d5f91863f4c998e84b`. Implementation
`f28d4bb3b8eacebe7fb48a3ca7800094711793eb` adds two unreferenced shadow services, an archive-only
evidence/AI/test tool, tests, and reports. No production module imports either service.

Any future canary must descend from this implementation, preserve `xhigh` signed-in CLI reasoning,
canonical evidence/numeric ownership, completed-bar and no-look-ahead gates, AI-owned decisions,
and deterministic omission on failure. It must not enable production automatically, fabricate a
score-based fallback decision, create order sizing, expose recipient values, or reinterpret the
test-sink proof as natural production evidence. Operator review is the next dependency.

The decision-evidence-polarity repair starts from operating main
`483888edcd4afb64d108c667b47d7e9f6b5ba423`, with exact instruction commit `0bba7c9` and
implementation `86b9fc44006c45431ccc1822131df3b4a74eb1ca`. It extends only the bounded decision
candidate, renderer/validator, archive/test tooling, and tests. It does not alter decision
calibration, Price Structure, valuation, market messages, schedules, recipients, assessments, DB,
Pilot, or Production Assist. Descendants must preserve explicit BULLISH/BEARISH/NEUTRAL ownership,
the exact four-subject canary, and the no-manual-natural-proof boundary.

The V2 production cutover descends linearly from operating main
`6db9256b539e437a7067a1822237ef9c504c63fa`. Exact instruction commit `0eb8bad` precedes Track A
`1a6488e`, Track B `7f32c34`, and convergence implementation
`6c429fc2f8afc4316b319494ca098c77594d0d2d`. Premerge/exact-provenance evidence advances through
`2a30bb3dcaecb40f83ca53f59982de1e18dab0ee`.

All descendants must preserve accepted-plan-only rendering, required adjudication for material
changes, subject-local NOT_READY suppression, same-evidence churn rejection, signed-in
`gpt-5.6-sol / xhigh`, complete packet inventory, unchanged Price Structure/valuation/market
messages, and selector-based V1 rollback. Test-sink proof is not natural proof. No descendant may
manually run a Scheduled Task, send a production Telegram proof, expose raw recipient IDs, rewrite
accepted history, or declare LIVE_PASS before both required natural KR and US cycles.

The atomic onboarding/scoped-readiness branch starts from clean main
`ecd01297f81d0b68aaf95ecfe866721b6aa2c104`. Exact instruction commit `8da71e7` precedes
implementation `2c4b973`.

All descendants must preserve pending-first registration, the canonical activation coordinator,
`ACTIVE => onboarding_ready && production_eligible`, immutable market/session/cutoff packet
snapshots, and subject-local exclusion. They may not restore global-universe readiness gating,
mutate an in-flight packet after cutoff, manufacture onboarding evidence, copy facts across tickers,
or treat the isolated test sink as natural proof. CPNG remains pending until its own baseline is
complete; 047810 eligibility begins only in a later frozen session. Price Structure, valuation,
accepted-decision ownership, schedules, recipients, and Production Assist remain unchanged.

Bounded descendant `6521d50` is required: legacy baseline fallback selects the earliest `final`
assessment after honoring an explicit `initial_baseline`. This restores seven safe legacy US
subjects found during operating reconciliation and must not be weakened to accept provisional
evidence. Final operating audit is active/ready-active/incomplete `21/21/0`.

The pending-onboarding automation descendant begins at clean main
`9c0e2907a5914f43e257cd886d25078288f1bba4`. Exact instruction commit `c95e176` precedes final code
implementation `5e3820456ace797450b9403386edaa2fc6af6cf1`.

Descendants must preserve requested-subject filtering, bounded retry classes, subject and market
isolation, canonical initial evidence, accepted-v2-only readiness, immutable packet cutoffs, and
first-eligible-session enforcement. They may not add ticker-specific resume paths, force-set active,
count placeholders as evidence, let raw candidates activate, replay historical production
messages, expose recipient values, or alter existing delivery schedules. CPNG is ACTIVE_READY from
`2026-09-01`; its next proof must be a natural US packet.

The OHLCV V2 resilience branch starts from read-only report main
`f7c4331e7aa34eeb87e0627fb7e79ee27a1cbfa7`. Exact instruction commit
`1dd691a340b4961e105371af53142c76db7385d7` precedes packet-owned technical context, bounded
recovery, subject isolation, and numeric-provenance repair through
`1e0fb9cd6e4542474c623800a805026c236f2a53`. Descendants must not restore decision-stage local
HTTP as the only technical source, weaken OHLC integrity, add ticker exceptions, retune decisions,
or conflate the test sink with natural proof. Promotion is a clean linear fast-forward; the next
production evidence is the next natural US cycle.

The V2 natural CLI path/product-identifier repair starts from clean main
`1aa10f04016cabede492c82686b6d671b4c27f55`. Exact instruction commit
`b2c0a4af72c5eb060dcdacd8b281e30307c717f1` precedes implementation
`b5be74439b2e8e769b1605e539599835abbc8a84`. Descendants must preserve canonical repository-root
subprocess path resolution, schema preflight before model invocation, portable relative claim
storage, exact evidence-owned identifier spans, and validation of adjacent or unproven numerics.
They may not add a KR/ticker identifier allowlist, weaken generic numeric validation, restore
launch-CWD dependence, bypass the repaired natural path in tests, manually trigger production, or
treat the 22-message dedicated-sink proof as natural live evidence.

The run-51 three-P1 repair starts from clean main
`2a6bbc449d6802490560cb89d83e0d1fc3e88b24`. Exact instruction commit
`ff255fc710a3b86b0496cdedca505a7a4a5323e7` precedes runtime implementation
`16fa1222136b300d900682904f8391ef5c4b482a`.

Descendants must preserve private claim-scoped Codex state, owner-safe signed-in auth reference,
strict daily-review validators, exact-span synchronization, accepted-decision ownership, XKRX
night-session end-date mapping, and source-limited omission when the provider is stale. They may
not use world-writable state, root execution, plaintext auth copies, ticker exceptions, relaxed
quality thresholds, forced night rows, manual production tasks, production Telegram proof, or raw
recipient values. The dedicated `22/22` sink result is production-equivalent evidence only; the
next dependency is ordinary natural US/KR observation.

The previous-XKRX night-reference repair starts from clean main
`ec616105f69aea3ba561ea9a6eea0835801d9a07`. Exact instruction commit
`46c6707325fe214a7d686095b940cabb55911006` precedes implementation
`7efc07bb0a9c635b78bb63ec642b50656b01b0b4`.

Descendants must preserve XKRX ownership of the US-morning night-reference target, the latest valid
XKRX business date strictly before KST date `D`, raw provider `BAS_DD`, independent 06:00 finality,
same-contract DAY comparison, and fail-closed stale/future handling. They may not restore US-session
ownership, use naive calendar subtraction, force rows ready, weaken validators, alter schedules,
manually replay production, expose recipient values, or treat run-51 replay as natural live proof.

The four-track stabilization branch starts from clean main
`89d3dc7ea350564c2b55b36b0c9ef9406330b3f9`. Exact instruction commit
`87887dbf9d42a841f27b6344694ce03bfe34c092` precedes independently reviewable Track A/B/C/D
commits `20c80b6d968b5770947a6621fa4867d51967dbe0`,
`70d60e4ba100ad140b9aef6e26cfda0acf4f1a8f`,
`4407cd11a78579e11681b503b2d4e72ee3c3d60f`, and
`ee4e4688816d35f7a5ade7630eac07e6edd215eb`.

Descendants must preserve bounded DNS/TCP/TLS and Codex transport retry limits, unchanged task
timing/ownership, strict daily-review validators, same-contract NIGHT D/W/M, dated official nominal
Treasury observations, and accepted-plan-only rendering. They may not add DNS/TLS/root shortcuts,
retune decisions, restore common stock disclaimers, use raw candidates as final, expose recipient
values, manually trigger production, or treat the dedicated `22/22` sink as natural proof. The next
dependency is ordinary natural KR/US observation; Production Assist remains OFF.
