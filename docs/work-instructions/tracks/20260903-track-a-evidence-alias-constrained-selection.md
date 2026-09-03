# Track A — Evidence Alias Constrained Selection

Replace free-form evidence-ref generation with deterministic subject-scoped aliases.

Requirements:
- E01/E02/... deterministic per evidence fingerprint
- dynamic allowed-choice constraint
- one alias → one canonical ref
- same subject / market / generation ownership
- downstream resolution back to canonical refs

No 086280-specific branch.
No validator weakening.
The model still chooses which valid evidence matters.
