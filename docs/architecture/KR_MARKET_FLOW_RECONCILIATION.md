# KR Market Flow Reconciliation

## Contract

`kr-market-flow-reconciliation-v1` compares the market aggregate from `ka10051` with the complete
stock-level sum from `ka10066` for the same session, integrated exchange basis, market, participant,
and monetary unit.

The official field documentation identifies amount mode but does not publish output scale. The
2026-08-25 live proof establishes the working scale empirically:

- `ka10051 amt_qty_tp=0`: one source unit equals KRW 100 million.
- `ka10066 amt_qty_tp=1`: one source unit equals KRW 1 million.

These scales remain explicit metadata; unitless arithmetic is prohibited.

## Classification

- `EXACT`: normalized amounts match.
- `WITHIN_AGGREGATE_RESOLUTION`: difference is smaller than one `ka10051` source unit.
- `PAGINATION_INCOMPLETE`: the full continuation chain was not obtained.
- `DUPLICATE_IDENTITY`: normalized stock identities repeat.
- `UNRESOLVED_BASIS_OR_TAXONOMY`: a material difference remains after normalization.

Market-wide aggregate flow remains usable when its own contract passes even if stock-level
reconciliation blocks concentration.

## Concentration

`kr-market-flow-concentration-v1` computes:

```text
top five same-direction absolute stock flow
/
all same-direction absolute stock flow
```

It requires complete pages, zero duplicate identities, and reconciliation no worse than aggregate
resolution. It is descriptive, never causal. On 2026-08-25 KOSDAQ qualifies; KOSPI is blocked by
material unresolved differences. There is no cross-market fallback.
