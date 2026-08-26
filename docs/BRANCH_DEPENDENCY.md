# Branch Dependency Manifest

As of 2026-08-24. Resolve final SHAs from Git; documentation commits are intentionally not
self-referential.

| Branch | Base / merge-base | Unique scope | Code dependency | Operating eligible | Promotion path |
|---|---|---|---|---|---|
| `main` / operating | Phase 9.0E final code and persistent state at `33c2f8be...` | selective current-formal full-FCF rollout pending natural proof | none | current baseline | already operating; 9.1A promotion deferred for KR natural window |
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
