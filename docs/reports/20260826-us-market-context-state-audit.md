# 2026-08-26 US Market Context State Audit

The implemented state vocabulary is:

- `CURRENT_DIRECTIONAL`: current occurrence with a canonical signed change.
- `CURRENT_LEVEL_ONLY`: current occurrence with a level but no directional delta.
- `PUBLICATION_PENDING`: provider/session publication boundary, used for unavailable official breadth.
- `SOURCE_UNAVAILABLE`: stale, lagging, missing, bad-quality, or failed current-context source.

State and temporal role remain separate. A new official release can be directionally usable while displaying its actual observation date; a same-session RSP level can be current but not directional.

For the target replay:

- RSP: `CURRENT_OBSERVATION` + `CURRENT_LEVEL_ONLY`, both signal eligibility flags false.
- XLE/XLF: `CURRENT_OBSERVATION` + `CURRENT_DIRECTIONAL`, signal eligible true.
- WTI 8/18: `REFERENCE_LAGGING` + `SOURCE_UNAVAILABLE`, current-change eligibility false.
- Nasdaq official breadth: `PUBLICATION_PENDING`; no synthetic count.

Numeric registry coverage includes the new sector/style level semantics, preserving exact-level provenance without recasting a level as a return.
