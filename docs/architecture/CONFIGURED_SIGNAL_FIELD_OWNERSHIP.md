# Configured Signal Field Ownership

Contract: `configured-signal-field-ownership-v1`

Frozen decision: `CURRENT_DIRECTIONAL_DRIVER_ONLY_WITH_CONFIGURED_REF_FENCING`

Frozen at: `2026-09-12T11:17:24Z`

## Repository Evidence

- The Directional Core prompt requires buy and sell drivers to be based on current evidence.
- `buy_drivers`, `sell_drivers`, `dominant_evidence`,
  `core_investment_judgment`, and `material_directional_anchor_basis` are
  already classified as always-current paths by the financial claim validator.
- The final composer copies buy and sell drivers into the directional result
  without prospective-role metadata.
- Directional schemas have no role field that could safely distinguish a
  current driver from a future configured condition.
- Dedicated future fields already exist for business reevaluation,
  confirmation, and invalidation conditions. `risk_context` may describe a
  configured condition only as prospective risk context.

These contracts make `sell_drivers` a current directional-driver field, not a
mixed risk inventory.

## Ownership Rules

Configured source refs from `stock.thesis.strengthen_signals`,
`stock.thesis.weaken_signals`, and `stock.thesis.invalidation_signals` begin in
`CONFIGURED_ONLY` state. Their existence, repetition by a model, or use in a
risk field does not establish fulfillment.

Configured-only refs are not eligible for:

- `buy_drivers`
- `sell_drivers`
- `dominant_evidence`
- `material_directional_anchor_basis`
- `core_investment_judgment`

They remain eligible for the matching business reevaluation fields, Stage 2
confirmation or invalidation conditions, and prospective `risk_context` use.

A signal may become `FULFILLED_BY_CURRENT_EVIDENCE` only through independently
verified current evidence supplied to the configured-signal view. Model prose
cannot certify fulfillment. Partial net-debt evidence and OCF-minus-PPE proxy
evidence cannot certify the respective configured conditions.

## Enforcement

The model-facing schema must fence configured-only aliases out of current
directional fields for both monolithic and Stage 1 calls. A post-model
validator must independently reject the same misuse as
`configured_future_signal_used_as_current_directional_driver`.

Financial completeness remains a separate check. A current net-debt claim
without complete current evidence still fails its existing financial safety
contract.

The external Directional schema, renderer contract, persisted state, and
production behavior do not change. Because allowed model refs change, a new
full fictional proof is required before a new full monitored shadow.

## Historical 005490 Decision

The stopped M12AS candidate remains invalid. `E01` and `E17` are configured
weaken signals and are valid in `business_reevaluation_down`, but invalid in
`sell_drivers[0]` while unfulfilled. The primary error becomes field ownership,
not a net-debt completeness exemption.
