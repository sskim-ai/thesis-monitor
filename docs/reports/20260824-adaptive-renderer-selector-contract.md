# Adaptive Renderer Selector Contract

- Contract: `adaptive-renderer-selector-shadow-v1`
- Input: validated `evidence-locked-free-analyst-shadow-v1` structured analysis only
- Decision: deterministic typed rules; no LLM selector call
- Modes: `DIRECT_ANALYST`, `CONCISE_HYBRID`, `MINIMAL_VNEXT`
- Ticker/industry hard-code: `0`
- Production wiring: `0`

`DIRECT_ANALYST` preserves material two-sided alternatives, multiple thesis implications, or any boundary that Hybrid would lose. `CONCISE_HYBRID` is selected for one clear thesis linkage, a preserved boundary, and a clear next check. `MINIMAL_VNEXT` is reserved for a reference-only temporal state with no material synthesis beyond the safe source boundary.

Every decision records eligible and disallowed renderers, selection reasons, direct-required reasons, minimal-forbidden reasons, and candidate-level retained/dropped/material-dropped elements. The selected renderer is rejected if `material_dropped_elements` is non-empty.
