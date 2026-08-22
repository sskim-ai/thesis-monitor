# Working-Capital User-Visible Pre-Integration

Contracts:

- `working-capital-user-visible-v1`
- `working-capital-user-visible-enable-gate-v1`

## Problem

Phase 9.1D can observe safe Inventory and exact Trade AR reasoning, but a passing canary alone does
not define production placement, numeric ownership, AI/fallback parity, independent family rollout,
or a kill switch. Building those pieces only after natural proof would leave avoidable integration
risk; enabling them before proof would expose an unproven metric family.

## Decision

Phase 9.1E prepares selective working-capital rendering without enabling it. Canonical facts remain
owned by Phase 9.1B, archive reasoning by Phase 9.1C, and natural observation by the independent
Phase 9.1D canary. The pre-integration layer consumes those outputs and never recalculates balances,
YoY changes, percentage-point gaps, or cash flow.

## Feature Modes

```text
OFF
SELECTIVE_INVENTORY
SELECTIVE_EXACT_TRADE_AR
SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
```

`WORKING_CAPITAL_USER_VISIBLE_MODE` defaults to `OFF`. Missing, blank, or invalid values resolve to
`OFF`. Phase 9.1E ends with `OFF`; all generated prose is marked
`PREVIEW_ONLY_NOT_ENABLEMENT_EVIDENCE`.

## Enablement Gate

Each metric family has a separate machine-readable gate. It preserves the natural packet and
receipt, canonical Fact IDs, relation IDs, PIT/freshness result, semantic/causal/numeric result,
production influence, open P0/P1, and evidence reference. A requested mode becomes effective only
when every family in that mode is eligible.

Natural proof must be `LIVE_PASS` from a Phase 9.1D receipt. `NOT_OBSERVED`, `LIVE_FAIL`, incomplete
evidence, an open P0/material P1, or a failed validator keeps the effective mode `OFF`. Inventory
can later enable independently from exact Trade AR and vice versa.

## User-Visible Context

The preview context preserves:

- ticker, packet, assessment date, and immutable cutoff;
- feature and preview modes;
- exact metric family and semantic scope;
- latest-formal balance date and PIT/currentness state;
- one canonical relation and its input Fact IDs;
- industry applicability and materiality reason;
- `business_earnings` numeric ownership;
- exact Unknown resolution and remaining Unknowns;
- allowed/prohibited claims and gate reference;
- AI/fallback/user-visible enablement booleans;
- optional compatible cash-flow context and its alignment state.

The selector may only reuse a Phase 9.1D canary-selected total Inventory or exact Trade AR relation.
It cannot broaden selection to broad AR, AP, contract assets, accrued liabilities, DSO, Inventory
Days, DPO, or CCC. There is no production ticker allowlist.

## Placement And Numeric Ownership

The future placement is one concise sentence in `business_earnings`. It contains one primary
relation and at most one exact percentage-point value. Core, valuation, price, positioning,
observer, holder, warnings, and next checks do not repeat that exact value. No standalone
working-capital section is mandatory.

## Cash-Flow Coexistence

Phase 9.0E cash flow remains independent. A cash-flow context is compatible only when its primary
period end matches the working-capital balance date. An incompatible or unverified period cannot be
combined. When compatible cash flow already communicates the decision-relevant point and working
capital resolves no additional Unknown, working capital is suppressed. The layer never recomputes
FCF or stacks two numeric dumps.

## AI/Fallback Parity

AI and deterministic fallback preview consume the same
`working_capital_user_visible_context_id`. Their ticker, metric family, Fact IDs, relation ID,
balance date, semantic scope, direction, displayed value, Unknown resolution, suppression reason,
and numeric owner must match. Prose may differ after enablement, but Phase 9.1E uses one conservative
renderer to make the parity proof exact.

## Semantic And Causal Safety

The validator rejects broad AR as exact Trade AR, inventory components as total Inventory,
unsupported causal claims, DSO/Inventory Days/DPO/CCC, duplicate/missing primary numbers, and
working-capital-only thesis or valuation changes. It allows only cautious relation language:
Inventory is interpreted with industry demand/price/mix context, while exact Trade AR triggers an
order-to-cash or collection follow-up without declaring customer stress or late payment.

## Kill Switch

`OFF` disables all future production enrichment while retaining Phase 9.1B canonical facts, Phase
9.1C archive reasoning, Phase 9.1D canary evidence, and Phase 9.0E cash flow. The preflight gate is
required even if an operator requests a selective mode. See
`docs/operations/WORKING_CAPITAL_USER_VISIBLE_KILL_SWITCH.md`.

## Future Enablement

1. Observe a natural Phase 9.1D receipt; do not run a task manually.
2. Classify Inventory and exact Trade AR independently.
3. Verify packet/Fact/relation/PIT/semantic/causal/numeric evidence and zero production influence.
4. Close P0/material P1 and run the preflight for only the proven family.
5. Use a small enablement-only instruction, preserve the kill switch, and verify the next natural
   delivery.

A clean preview is not natural proof. Phase 9.1E removes architecture risk while leaving the final
enablement decision evidence-gated.

## Why

The design lets natural evidence, architecture readiness, and actual enablement advance
independently. It preserves a small future rollout while keeping evidence semantics and production
safety fail-closed.

## Rejected Alternative

The phase rejects immediate enablement, a combined all-or-nothing Inventory/Trade-AR switch, ticker
allowlists, broad AR/AP expansion, duplicate cash-flow and working-capital paragraphs, and any
operator path that can bypass natural proof.

## Safety Constraint

The operating mode remains `OFF`. Production AI, fallback, Telegram, Public Action, snapshot,
assessment DB, warning lifecycle, Scheduled Tasks, and Production Assist are unchanged. Preview
artifacts cannot be used as enablement evidence.

## Phase 9.1E.1 Inventory-Only Enablement

The natural run-32 canary established `INVENTORY_NATURAL_PROOF=LIVE_PASS`: MU and TSLA selected
total Inventory with complete Fact/relation lineage, automatic numeric binding, zero semantic or
quality errors, and zero production influence. Exact Trade AR existed in context for TSM but was not
selected, so `TRADE_AR_NATURAL_PROOF=NOT_OBSERVED`.

Phase 9.1E.1 therefore permits only `SELECTIVE_INVENTORY`. Trade AR and combined modes are hard
rejected by the preflight and resolve to `OFF`. The production selector remains contract-driven:
current-formal, PIT-safe, total Inventory, materiality-selected, non-redundant with Phase 9.0E cash
flow, and owned by `business_earnings`. It renders one typed `%p` relation at most. AI and fallback
must share the exact packet/context/relation/Fact/date/scope/direction identity.

Operating activation follows implementation CI, OFF-mode regression, main/operating promotion,
health and schedule checks. The kill switch is the same configuration key set to `OFF`; disabling
user-visible Inventory does not disable canonical evidence, shadow consumption, the detached
canary, or cash flow.

After activation the state is `ENABLED_PENDING_NATURAL`, not live pass. The first natural delivered
message that actually selects Inventory must verify lineage, balance date, semantics, causal guard,
AI/fallback path, numeric ownership, cash-flow coexistence, exactly-once delivery and message
quality. A P0 sets the mode back to `OFF` while preserving immutable evidence.

The operating mode was safely activated as `SELECTIVE_INVENTORY` on 2026-08-22 at 12:16 KST after
exact-SHA CI, main/operating parity, health and scheduler checks. Inventory is
`ENABLED_PENDING_NATURAL`; exact Trade AR remains `OFF_PENDING_NATURAL_PROOF`.
