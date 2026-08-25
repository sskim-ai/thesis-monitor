# 2026-08-25 Trade AR Natural Canary Proof

- Exact semantic: `trade_accounts_receivable`
- Ticker: `TSM`
- Current Fact: `working-capital-reported:f45352209836619ff1049bee`
- YoY Fact: `working-capital-derived:fa48565f8ff0695b952c5e98`
- Sidecar status: `CONTEXT_ONLY`
- Freshness: `FORMAL_LAGGING_PROVISIONAL`
- Shadow used: `False`
- Suppression: `newer_provisional_period_not_balance_aligned`
- User-visible Trade AR: `0`
- User-visible broad AR: `0`
- User-visible AP: `0`
- DSO: `0`

The exact Trade AR Fact existed, but the formal balance period lagged newer provisional operating evidence. It remained context-only and was correctly suppressed. The detached working-capital canary passed, but no Trade AR relation was naturally rendered.

`TRADE_AR_NATURAL_PROOF = NOT_OBSERVED`

`TRADE_AR_ENABLEMENT_CANDIDATE = NO_PENDING_NATURAL`
