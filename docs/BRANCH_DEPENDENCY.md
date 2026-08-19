# Branch Dependency Manifest

As of 2026-08-19. Resolve final SHAs from Git; documentation commits are intentionally not
self-referential.

| Branch | Base / merge-base | Unique scope | Code dependency | Operating eligible | Promotion path |
|---|---|---|---|---|---|
| `main` / operating | Phase 8.5.4.2 operating code through `7e7ab5acee2176bc8a452115da19ac6e14d312ab` plus later operating documentation | Phase 8.5.x operating shadow | none | current baseline | already operating |
| `codex/phase-8-2a-krx-market-breadth` | main experimental ancestry | KRX breadth, universe and publication telemetry | KRX experimental | no | separate KRX decision |
| `codex/phase-8-3-peer-sector-valuation` | KRX experimental final | original Phase 8.3 peer contract | Git ancestry includes KRX; peer code does not require KRX runtime symbols | no | promote after KRX or reconstruct cleanly |
| `codex/integration-phase-8-3-peer-only` | latest main | two peer-only commits through `e17d992c4c5d40030294eff5a74504e88ab35911` | no KRX code/schema dependency | prepared, not approved | peer-only review branch |
| `codex/phase-8-3-2a-free-peer-poc` | peer-only clean branch | free-source service, audit tooling, tests and archive reports | no KRX implementation ancestry | no | development evidence only |
| `codex/phase-8-3-finalization` | Phase 8.3.2A `ad1b98a4...` | conservative peer wording, Phase 8.3 closure and Master Workflow v7 | no KRX implementation ancestry | no | final experimental evidence only |
| `codex/phase-8-3-1-1-peer-provider-decision` | research chain | commercial/provider decision history | documentation ancestry | no | retained as reference |
| `codex/phase-8-5-4-natural-live-targeted-repair` | operating main `e925ee0...` | run-26 night-session, semantic binding, typed valuation, fallback parity and RR overlap repair | no Phase 8.3 or KRX experimental dependency | promoted | fast-forwarded to main through `3a6547e...` |
| `codex/phase-8-5-4-1-operating-shadow-promotion` | Phase 8.5.4 `3a6547e...` | live-readiness, promotion, operating smoke and persistent-state evidence | documentation only after validated code promotion | evidence branch | fast-forward documentation after exact-SHA CI |
| `codex/phase-8-5-4-2-night-futures-calendar-repair` | operating main `c7581a9...` | holiday-aware preceding-DAY lookup | existing operating night-futures path only | promoted | fast-forwarded through `7e7ab5a...` |
| `codex/phase-8-5-5-natural-reasoning-ownership-repair` | operating main `c6481d145ccc1583feaf6f6de7d005e774d56933` | run-27 security/framework ownership and repetition repair | existing operating AI packet/validator path only | eligible after full gate | clean linear fast-forward |

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
