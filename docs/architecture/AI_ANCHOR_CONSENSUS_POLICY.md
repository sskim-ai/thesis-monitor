# AI Anchor Consensus Policy

## Contract

`ai-anchor-consensus-policy-v1` evaluates repeated variable-AI selection over canonical swing
structures. The benchmark cohort runs five times per packet and the wider active universe runs
three times. The policy consumes validated structure IDs; it does not inspect or modify SR.

## Classes

- `STABLE`: the repeated primary structure selection agrees.
- `MINOR_VARIATION`: differing selections are canonically equivalent under existing structure
  identity and tolerance policy.
- `MATERIAL_VARIATION`: selections are not canonically equivalent.
- `VALID_ABSTENTION`: the run set safely abstains because structure is ambiguous or insufficient.

Stable and minor results may be eligible for deterministic backend Fibonacci. Material variation is
`OMIT_UNSTABLE`; valid abstention is `OMIT_AMBIGUOUS` or `OMIT_INSUFFICIENT`. No class widens an
existing tolerance or promotes an unstable structure.

## Safety

Consensus is per ticker and timeframe. A monthly omission cannot invalidate weekly/daily output,
and no Fibonacci outcome can invalidate deterministic SR. Backend Decimal arithmetic, source Fact
references, look-ahead checks, and numeric provenance remain authoritative. Current production and
user-visible routes remain unarmed until a separate bounded enablement.

