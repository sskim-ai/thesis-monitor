# R2B-R4 Verified V2 Pre-Model Closeout

Terminal: `R2B_R4_PREMODEL_CONTRACT_DRIFT`.

The newly supplied neutral V2 receipt matches the exact instruction SHA and
attests that independent V2 was frozen after the quality supplement and before
any Monitoring-AI calls/output. Only that receipt was read. Independent V1/V2
assessment archives/content were not opened. Blind fairness is `PASS_V2`.

The unchanged R3 owners were replayed on exact sealed inputs:

- Core/A/B offline readiness: 22/22 each.
- Applicability: PRESENT 7, RECONSTRUCTIBLE 14, NOT_APPLICABLE 1.
- Quality owner gaps: 0; supplement hash unchanged.
- Stored-price-rule version ownership: 20/20.
- Unclassified model-visible source-time refs: 0.
- UNKNOWN_LIMIT remains non-directional; confidence-only quality is preserved.

## Actual Market Consumer Failure

Both original US/KR market source packets were passed unchanged to
`scripts.m12ds_r4_r4_market.market_context`. Its R3 delegate accesses
`packet['market_context']`, producing `KeyError('market_context')` for each.
`app.services.unified_full_source_cohort.compose_full_source` instead publishes
`market_sources.component`, source-owned stock packets, publication projections,
authority bindings and (US) night context. Stock subpackets also lack Market
context; their 22/22 probes never qualified the separate Market consumer.

This is an unclosed producer/consumer layout contract, not missing provider
values, changed source hashes, a failed V2 receipt, or a model rejection. An
empty context would silently discard available sealed market evidence. Running
the existing production market builder would require an explicitly bound
offline reconstruction rather than an arbitrary rename or a live DB read.

R4 Section 5 forbids source-policy repair. Therefore no substitute projection,
old context, new acquisition, changed Market policy, or stock-only dispatch was
used. A separately authorized bounded Market adapter closure is required.

## Safety And Delivery

Model input binding NOT_ISSUED; Market/Core/A/B calls 0/0/0/0; messages 0/24.
No comparison-ready receipt is emitted. Reveal remains CLOSED.
Provider refresh, Telegram, production DB/warnings, scheduler, main merge,
remote push, deploy and restart are zero. Code changes are archive-only audit
and tests; no source, quality, investment or renderer policy changes.

The immutable local closeout ZIP contains exact neutral receipt, source/read
audit, reproducible 22-subject probes, both Market failure receipts, repository
identity, changed files, validation and safety evidence. It is a failure report,
not a Monitoring-AI result. Earlier missing-receipt report remains immutable.
