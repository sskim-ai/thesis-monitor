# US Current-Session Evidence Root Cause

- Run: `41`
- Packet: `2026-08-27-us-run-41-ae4f42c23abc`
- Target session: `2026-08-26`
- Implementation SHA: `069f002437163bff1df7aa6e258918c1777d5dfa`
- Replay mode: immutable archive read-only

## Finding

Run-41 contained current directional SPY, QQQ, IWM, SOXX, RSP, XLI, and XLV facts. The existing important-change selector legitimately chose three macro changes, but the market digest had no typed owner requiring the current-session cross-section. `required_market_fact_ids` covered night futures only, while fallback rendering consumed a separate macro interpretation. The final adaptive digest therefore retained only the dated real-yield narrative.

This is a bounded P1 evidence-consumption failure, not a source, numeric provenance, or macro temporal-classification failure.

## Historical Validator

Status: `FAIL`

- `CORE_MARKET_SLOT_UNCONSUMED`
- `SELECTED_RSP_SLOT_UNCONSUMED`
- `SELECTED_SECTOR_DISPERSION_UNCONSUMED`
- `MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE`
