# Branch Dependency Manifest

As of 2026-08-21. Resolve final SHAs from Git; documentation commits are intentionally not
self-referential.

| Branch | Base / merge-base | Unique scope | Code dependency | Operating eligible | Promotion path |
|---|---|---|---|---|---|
| `main` / operating | Phase 9.0D.1 final code and persistent state; exact SHA resolves from Git | Phase 9.0D live canary plus baseline cash-flow consistency repair | none | current baseline | already operating; Phase 9.0E is next |
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
