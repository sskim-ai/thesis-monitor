# KR Investor-Flow Reconciliation

## Contracts

- Participant taxonomy: `kr-investor-flow-participants-v1`
- Window reconciliation: `kr-investor-flow-reconciliation-v1`
- Windows: `1d`, `5d`, `20d`, each defined by trading rows ending at `as_of_date`
- Display scope: foreign, institution total, and individual are the visible `major_three_participants`

The provider's mutually exclusive top-level reconciliation set is foreign, institution total,
individual, other corporation, and domestic foreign. Financial investment, insurance, investment
trust, other finance, bank, pension/public funds, private funds, and government are institution
subclasses. They are retained as diagnostics and are never added to institution total.

Foreign ownership quantity and ratio are position facts. They are not participants and never fill a
flow residual.

## Pipeline

```text
OHLCV Analyst daily investor_flow
        -> canonical participant taxonomy
        -> exact trading-row window sums
        -> displayed/omitted/full reconciliation
        -> attribution-safe signal and basis window
        -> shared AI packet and deterministic fallback
        -> semantic validation
```

The three existing visible values are identity-mapped. Additional participants come only from named
provider fields. No residual is assigned a participant identity.

## Reconciliation

Each window records participant flows, visible and omitted sets, visible/omitted/full net, optional
provider total, coverage, material omitted-flow state, attribution safety, signal, and participant
basis. A provider total is not currently exposed; the contract records
`complete_without_provider_total`. If a future canonical aggregate exists, exact integer equality is
required and a difference becomes `provider_total_conflict`.

Five- and 20-trading-day totals for other corporation, domestic foreign, and institution diagnostics
are sums of the exact daily rows. Existing provider totals for foreign, institution, and individual
remain primary when present. Duplicate dates are collapsed by date before window selection.

## Materiality

There is no new score or percentage threshold. Omitted flow is attribution-material when its net
changes the displayed side balance or is at least as large as a displayed nonzero actor. This is an
actor-attribution test, not a general quality score. An absorber, main-buyer, or offsetting claim is
allowed only when the selected window is complete, conflict-free, and attribution-safe.

When 5-day and 20-day directions reverse for at least two displayed actors, the primary basis is
`mixed`; prose must describe horizon tension and cannot use a timeless absorber phrase. Otherwise,
20-day is preferred, then 5-day, then 1-day. Safe non-attribution provider signals such as foreign
re-entry retain an explicit 20-day basis.

## Rendering And Validation

When omitted flow is material, fallback labels the visible table `수급(주요 3주체)`. It suppresses
actor-leading quality labels and uses the same canonical primary signal and basis delivered to AI.
The semantic validator rejects absorber/leader/offset claims when `attribution_safe=false`, and it
rejects safe 5-day/20-day attribution without the matching period label.

This repair changes only KR positioning wording. It does not change supply score, thesis status,
warning lifecycle, valuation, price/RR, cash flow, working capital, Public Action, or schema 4.
