# KR Enriched Market Context Replay

- Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
- Packet SHA256: `ef456b24b036fcc1b6926489c5e8058eed8a70f570f5df1d49e9c93fe35f487d`
- Immutable packet rewrite: `0`
- Supplemental evidence: KRX 8/25 publication readiness only

The exact target session returned no published rows. The replay therefore injected zero KOSPI,
KOSDAQ, breadth, or market-flow numbers. The digest changed from a generic temporal message to a
specific boundary: KOSPI/KOSDAQ and market-specific advance/decline counts were publication-pending,
so domestic direction and market flow were not inferred. Its next check now asks for the next KRX
completed publication.

All seven stocks retain their exact packet evidence. SK hynix leads with HBM/memory thesis evidence;
Hanwha Aerospace leads with defense backlog/delivery/margin, while Inventory remains supporting.
Canonical KR participant tuples remain in one `수급` owner.

Result: `8/8` eligible, generic lines `10 -> 0`, duplicate messages `5 -> 0`, hard safety errors `0`.

`KR_STRUCTURED_CONTEXT_VALUE_ADD = NO_MATERIAL_VALUE` for directional market analysis, with a
material safety-boundary improvement.
