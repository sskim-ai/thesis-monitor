# Track A — Fact Consumer Scope + Shadow Readiness Contract

Implement generic fact consumer ownership.

Separate:
- user visibility
- AI consumability
- market-renderer ownership
- archive/raw ownership

STOCK_V2 readiness validates only STOCK_V2-owned facts.
DAILY_REVIEW readiness validates only DAILY_REVIEW-owned facts.

Do not:
- derive AI scope from visibility
- whitelist night reference_price paths
- default unknown facts to exempt
- weaken numeric semantics

Mandatory negative control:
hidden + STOCK_V2-owned unsupported numeric must still FAIL.

Prove readiness projection exactly matches the actual AI prompt/context surface.
