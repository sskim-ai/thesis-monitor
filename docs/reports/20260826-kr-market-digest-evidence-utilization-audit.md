# KR Market Digest Evidence Utilization Audit

Date: 2026-08-26 KST
Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
Contract: `kr-market-digest-quality-v1`

## Richness Predicate

| Predicate input | Result |
|---|---:|
| completed/provider-complete final session | YES |
| KOSPI and KOSDAQ indices | YES |
| KOSPI and KOSDAQ reconciled breadth | YES |
| market-wide participant flow | YES |
| size/style context | YES |
| sector context | YES |
| `KR_DOMESTIC_CONTEXT_RICH` | **YES** |

The source session is 2026-08-25. Both markets had more advancers than decliners; KOSDAQ
outperformed KOSPI. Foreign flow was negative in KOSPI and positive in KOSDAQ, while institutions
were net buyers in both markets.

## Priority Use

| Role | Priority | Local facts used | Result |
|---|---|---|---|
| judgment | P1 | KOSPI/KOSDAQ relative move and scoped breadth | local-first PASS |
| interpretation | P2 | KOSPI/KOSDAQ foreign and institution flow | local-first PASS |
| next check | P2 | persistence of KOSPI foreign selling versus broad participation | local-first PASS |

The post-repair plan used 4 P1 source refs in judgment, 6 P2 source refs in interpretation, and the
compatible P1/P2 set in next-check provenance.

## Compression And Boundaries

- One market-structure conclusion is rendered.
- One flow interpretation is rendered.
- One unresolved local next check is rendered.
- Global-context sentences retained: `0`.
- Global retention reason: `no_material_global_contradiction_required`.
- Concentration scopes used: `0`.
- KOSPI concentration remains fail-closed.
- KOSDAQ concentration is reconciled in the sidecar but omitted because it was not needed for the
  compressed conclusion.
- New exact numeric claims: `0`; baseline automatic numeric refs preserved: `123`.

## Verdict

`KR_DOMESTIC_CONTEXT_RICH = YES`
`KR_MARKET_DIGEST_LOCAL_FIRST = PASS`
`KR_MARKET_DIGEST_NEXT_CHECK = PASS`
