# Business Delta Validation Convergence

Status: M12AO local integration contract

## Decision

`BusinessDeltaEvidenceView` is the sole semantic authority for
`business_thesis_change`. The selected architecture is
`CANONICAL_BUSINESS_DELTA_VIEW_CONSUMED_BY_POST_MODEL_VALIDATION`.

The pre-model builder owns:

- capability and allowed output states;
- baseline-context, eligible observed-change, ambiguous, and excluded roles;
- known-safe direction hints;
- direction-unspecified observed changes; and
- exclusion reasons.

The post-model validator consumes that frozen view. It validates ticker and
evidence identity, alias/canonical resolution, capability enums, changed-state
grounding, unresolved-state support, known-direction contradictions, and
`UNCHANGED_ONLY` consistency. It does not derive eligibility or direction from
raw statement wording.

## Direction Rules

Known-safe comparable-period direction remains limited to the existing typed
financial registry. Higher comparable `operating_cash_flow` and
`ocf_less_ppe_capex` may support `STRENGTHENED`; lower values may support
`WEAKENED`. Inventory, receivables, and other context-dependent working-capital
movements remain eligible observed changes with direction unspecified.

`UNRESOLVED` is valid only when at least one selected eligible observed change
has unresolved direction or selected known-safe evidence conflicts. It is never
valid for `UNCHANGED_ONLY` inputs. Baseline context may explain a thesis but
cannot establish a change.

## Identity

The frozen `BusinessDeltaEvidenceView` serialization is hashed before model
generation and again by post-model validation. The hashes must be identical.
Audit rows expose one canonical semantic source and must report zero legacy
raw-text eligibility or direction re-derivations.

## Preserved Contracts

- Model prompts and schemas are unchanged.
- The Stage 2 Korean lexical boundary repair is unchanged.
- The PPE-only cash-conversion label remains
  `cash_conversion_ocf_less_ppe` with empty `metric_refs`.
- Canonical `ocf_less_ppe_capex` is not free cash flow.
- Explicit not-FCF disclaimers remain allowed; affirmative proxy-as-FCF claims
  remain hard failures.
- No model output is rewritten, scored, voted, or thresholded.
- Production delivery, persistence, monitoring, scheduler, main, deploy, and
  remote-push behavior remain unchanged.

## Proof Sequence

All deterministic gates must pass before a new generation begins. A new
8-subject, three-repetition fictional proof is then run as 6 Stage 1 and 6 Stage
2 calls. Only a clean hard gate authorizes a new 22-subject same-packet monitored
shadow with 18 calls. Any hard failure stops the run without selective retry or
mid-run repair.
