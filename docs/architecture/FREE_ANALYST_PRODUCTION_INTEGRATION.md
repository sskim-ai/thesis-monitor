# Free Analyst Production Integration

## Contract

The production contract is `evidence-locked-free-analyst-v1`, consumed through `common-ai-core-v1`.

The structured object preserves:

- top findings
- thesis implications
- alternative interpretations
- expectation and valuation interaction
- positioning synthesis
- Unknowns
- next checks
- message plan

Every claim-bearing item has one typed support category:

```text
DIRECT_FACT
DIRECT_RELATION
THESIS_LINKAGE
BOUNDED_INFERENCE
ALTERNATIVE_INTERPRETATION
UNCERTAINTY_BOUNDARY
EXPECTATION_VALUATION_LINK
POSITIONING_SYNTHESIS
```

Every item also carries evidence references. A generic `AI_SUPPORTED` state is not valid.

## Packet Adapter

`free-analyst-natural-packet-adapter-v1` normalizes only known production headings. It fingerprints non-heading content before and after normalization, creates deterministic production-to-common evidence reference mappings, and rejects content mutation or reference collisions.

KR and US share the same adapter and analysis schema. Market-specific differences remain limited to source packet facts, supply semantics, and the required production supply heading.

## Numeric Boundary

Free Analyst cannot create arithmetic. Exact source relations that already passed production numeric binding may be reused without being mislabeled as hidden arithmetic. A numeric synthesis not present in its cited source remains rejected. Rendered numeric tokens must be a multiset subset of the validated source message.

The current signed directional relation contract remains authoritative. Absolute gaps cannot support `higher` or `lower` language.

## Production Candidate

Each candidate records:

- analysis mode
- adapter state
- Free Analyst generation and validation state
- selected renderer and reasons
- hard validation state
- fallback reason
- canary candidacy and selection
- final delivery mode

The candidate builder has no persistence, provider, delivery, or network side effects.

## Required Source Sections

Adaptive compression may not remove the production-required supply heading. If the selected renderer omits it, the exact validated source supply section is preserved under the market-correct heading. No new prose or number is generated during this preservation step.

Trade AR, unsupported per-share cash flow, hidden external facts, unsupported causality, and temporal promotion remain fail-closed.
