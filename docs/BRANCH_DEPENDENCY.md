# Branch Dependency Manifest

As of 2026-08-21. Resolve final SHAs from Git; documentation commits are intentionally not
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
| `codex/night-futures-publication-telemetry-repair` | preserved instruction `b7cf6a2...`, explicit latest-main merge `e7b2add...` after Phase 9.1D | natural production-attempt archive plus detached bounded 08:45/09:15 publication observer | reuses the existing provider/parser/session-basis path; no market-summary, AI, fallback, Telegram, Public Action or DB dependency | telemetry-only promotion eligible | merge latest main preserved both independent instruction histories; natural deadline proof remains pending |
| `codex/kr-investor-flow-reconciliation-attribution-repair` | exact instruction `e9d7c73...` on operating main `af89324...` | complete KR top-level participant reconciliation, explicit signal basis, shared AI/fallback attribution safety | existing OHLCV supply path only; no score formula, Public Action schema, task, Pilot, DB, KRX breadth or peer dependency | promoted after exact-SHA CI | clean linear fast-forward; natural confirmation remains parallel |
| `codex/phase-9-1e-working-capital-user-visible-preintegration` | exact instruction `99f7e86...`; explicit merge `ee78eb7...` of Track A main `7c0e440...` | family-level natural-proof gate, OFF-by-default modes, Inventory/exact-Trade-AR preview, cash-flow redundancy, parity and kill switch | consumes only committed 9.0E/9.1D evidence; no production AI/fallback/Telegram/Public Action/snapshot/DB/task import | promotion eligible with feature OFF and exact-SHA CI | preserve instruction and Track A histories; future enablement requires a small family-specific instruction after `LIVE_PASS` |
| `codex/phase-9-1e-1-inventory-only-user-visible-enablement` | exact instruction `880e7a9...` on main `fb44510...`; explicit merge `018af42` of run-32 natural evidence | selective total-Inventory context in production AI/fallback with exact parity, typed `%p` binding, OFF kill switch and delivery metadata | reuses 9.1E contract; Trade AR/broad AR/AP/advanced ratios remain blocked; no ticker allowlist or state mutation | promoted and activated Inventory-only; natural user-visible proof pending | Inventory `LIVE_PASS_RUN32`; exact Trade AR `NOT_OBSERVED`; preserve both histories |

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
archive generator; the inert config field defaults to OFF. Inventory and exact Trade AR gates remain
`NOT_OBSERVED`, so mode preflight forces OFF. Promotion does not authorize user-visible working-
capital output and does not couple the future family proof to investor-flow natural confirmation.
