# Phase 9.1D Natural Runtime Proof

## Canary identity

- Packet: `2026-08-22-us-run-32-dde10ec6c9eb`
- Canary: `wc-canary-e16eaeeece1f21f9d42e8d27`
- Attempt: `attempt-20260821T234020368501Z-f33fad65`
- Receipt: `wc-receipt-b27e0c026493f8c0f2bdc655`
- Receipt SHA-256: `172a4e626408d333bcee7bd7d9b80d8b68133763d4fe5efc19fb3f410d2bdff0`
- Production delivery SHA-256: `e88e6ef439acfee7dafb9c7e768e241ef7bba894ae4439cfe1855b5728ae6089`
- Terminal state: `COMPLETE_PASS`, reason `all_shadow_gates_passed`
- Time: 08:40:20.368501..08:40:20.451777 KST-equivalent source window (stored UTC 23:40:20); total 55.423 ms
- Eligible subjects: 3; selected: 2 (`MU`, `TSLA`)
- Numeric binding: automatic 2, manual 0, rejected 0, unresolved 0
- Semantic errors: 0; quality errors: 0; cash-flow cross-links: 2
- Production influence / Telegram / assessment mutation / warning mutation: all 0
- Production AI, fallback, Public Action, public snapshot diffs: all 0

## Inventory proof

### MU

- Semantic: exact total Inventory, `us-gaap:InventoryNet`, balance scope `total`.
- Current/prior comparable lineage: six Fact IDs preserved in relation `working-capital-relation:dbdfd04e725e83528d8fdd31`.
- Relation: `inventory_vs_cogs`, LOWER by `15.7339...%p`, rendered `15.7%p`.
- PIT/freshness: PASS / CURRENT_FORMAL; latest formal balance date `2026-05-28`.
- Applicability/materiality: PRIMARY / existing working-capital driver or Unknown.
- Interpretation: inventory normalization is compatible, but NAND ASP and SSD demand are not asserted; no causal overclaim.

### TSLA

- Semantic: exact total Inventory, `us-gaap:InventoryNet`, balance scope `total`.
- Current/prior comparable lineage: six Fact IDs preserved in relation `working-capital-relation:36181e61768dfd580d9ede01`.
- Relation: `inventory_vs_revenue`, LOWER by `26.6321...%p`, rendered `26.6%p`.
- PIT/freshness: PASS / CURRENT_FORMAL; latest formal balance date `2026-06-30`.
- Applicability/materiality: PRIMARY / existing working-capital driver or Unknown.
- Interpretation: delivery, incentives, and mix remain required context; no demand direction or cash-flow causation is asserted.

No inventory component was substituted for total Inventory. No DSO, inventory-days, DPO, CCC, thesis mutation, or production influence was generated.

`INVENTORY_NATURAL_PROOF = LIVE_PASS`

## Exact Trade AR proof

No exact Trade AR relation was naturally selected into the shadow output. TSM contained an eligible exact `trade_accounts_receivable` metric context, but the subject was `CONTEXT_ONLY`, `shadow_used=false`, and its selected relation was Inventory because the formal balance period lagged newer provisional earnings. It therefore does not satisfy the natural-selection proof contract.

`TRADE_AR_NATURAL_PROOF = NOT_OBSERVED`

`NOT_OBSERVED` is not a failure.
