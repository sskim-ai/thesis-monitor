# Backup Market Evidence And Framework Repair

The backup now consumes each selected canonical US market-plan claim in `market_context` and cites all evidence refs. `hyperscaler_capex_transmission` is a stock framework and is removed from the market owner; it was not added to an allowlist.

```json
[
  {
    "slot": "CURRENT_MARKET",
    "evidence_refs": [
      "market:index:SPY",
      "market:index:QQQ",
      "market:index:IWM",
      "market:sector:SOXX"
    ],
    "owner": "market_context",
    "reason": "canonical_market_plan_owner_handoff"
  },
  {
    "slot": "PARTICIPATION_STYLE",
    "evidence_refs": [
      "market:style:RSP",
      "market:index:SPY"
    ],
    "owner": "market_context",
    "reason": "canonical_market_plan_owner_handoff"
  },
  {
    "slot": "SECTOR_DISPERSION",
    "evidence_refs": [
      "market:sector:XLC",
      "market:sector:XLK"
    ],
    "owner": "market_context",
    "reason": "canonical_market_plan_owner_handoff"
  },
  {
    "framework": "hyperscaler_capex_transmission",
    "reason": "stock_framework_removed_from_market_owner"
  }
]
```
