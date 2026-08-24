# Evidence-Locked Free Analyst Structured Contract

- Contract: `evidence-locked-free-analyst-shadow-v1`
- Execution: `SHADOW_OFFLINE_ONLY`
- Production import/wiring: `0`

## Object Boundary

The analyst produces a typed conclusion record before rendering. `top_findings`,
`thesis_implications`, `alternative_interpretations`, `expectation_valuation_interaction`,
`positioning_synthesis`, `unknowns`, `next_checks`, and `message_plan` remain separate. Each
claim-bearing item carries a support type, a smallest-sufficient evidence-ref set, a typed rule,
materiality, confidence, direction, and an uncertainty boundary.

The object contains concise conclusions, not private chain-of-thought. It consumes the same
immutable validated evidence used by current AI and vNext. It does not retrieve, recalculate, or
mutate canonical Facts.

## Freedom Boundary

The analyst may create new bounded synthesis, prioritize evidence, connect it to the stored thesis,
surface a material alternative, and omit low-value facts. It may not invent facts, arithmetic,
causes, temporal roles, valuation denominators, price levels, Trade AR, or external knowledge.
