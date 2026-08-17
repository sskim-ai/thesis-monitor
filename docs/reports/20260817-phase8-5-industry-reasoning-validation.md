# Phase 8.5 Industry-Specific Reasoning Validation

## Repository And Scope

- Branch: `codex/phase-8-5-industry-specific-reasoning`
- Base: `9c4c1cdae3c790d2fc66afa05fe35dfd09553e80`
- Main merge: no
- Operating deployment: no
- DB migration: none
- Production Assist: OFF
- AI mode: shadow
- Pilot: KR 3/5, US 3/5; mutation 0
- Telegram sends: 0
- Scheduled Task runs/config changes: 0

## Implementation

The new `industry-specific-reasoning-v1` service routes only from structured company evidence,
builds an auditable Fact-dependent reasoning plan, and validates causal, valuation-boundary,
attribution-boundary, and missing-driver references. It supports memory, semiconductor/foundry,
insurance, transport/logistics, steel/materials, automotive, biotech, HPC/crypto infrastructure,
EPC/construction, SaaS, holding company, and general frameworks.

The binder removes draft-only reasoning references and verifies exact spans and supporting Facts.
The full semantic validator adds framework-specific guardrails without relaxing numeric provenance,
financial quality/lineage, security identity, valuation scope, price/RR, supply, or renderer gates.

## Archive-Only Evidence

| Artifact | Result |
|---|---|
| KR representative full schema-4 set | 5/5 stock messages plus market message |
| US representative full schema-4 set | 6/6 stock messages plus market message |
| KR numeric binding | 86 automatic, 0 rejected |
| KR industry references | 12 accepted, 0 errors |
| KR full validator / receipt | PASS / PASS |
| US full validator / receipt | PASS / PASS |
| Industry guardrail errors | 0 |
| SK hynix denied leakage | 0 |
| Provider calls and runtime mutations | 0 |

The first attempt to reuse the natural US run-22 generated output did not satisfy the latest full
validator because its older generation semantics predated current contracts. No gate was relaxed.
The final US evidence uses immutable natural run-20 packet state plus the committed, validated Phase
7.2.9.2 renderer output, with all visible numbers rebound from the packet registry.

## Framework Coverage

The immutable active audit covers 20 stocks: high confidence 9, low/general 11. Fine-grained
specialization remains unavailable where current structured profiles do not prove it. This makes
Phase 8.5 **strong PARTIAL**, not CLOSED.

## Persistent Gap Status

| Gap | Status |
|---|---|
| Message Intelligence Foundation | CLOSED |
| Industry-Specific Reasoning | STRONG PARTIAL |
| Structured specialized taxonomy coverage | PARTIAL |
| Peer/Sector Valuation | OPEN/PARTIAL |
| KR Market Breadth | PARTIAL |
| KR Market-Wide Flow | OPEN |
| OCF | PARTIAL |
| CAPEX Aggregation | OPEN |
| FCF | OPEN |
| Current-Price RR Packet/Numeric Path | OPEN |
| Natural Live Validation | OPEN |
| Human-Approved Production Evidence | INSUFFICIENT |

## Recommendation

Repair the natural current-price RR packet/numeric path as a separate narrow work order before
using Phase 8.5 natural-live evidence. KRX Phase 8.2A may be inserted only after explicit approval is
confirmed. After that, Phase 8.3 peer/sector valuation and structured taxonomy enrichment provide
the highest-value inputs to the new reasoning contract.
