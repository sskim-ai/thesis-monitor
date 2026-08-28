# 2026-08-28 US Morning Shared Market Plan

The production packet, deterministic payload, persisted delivery, and final AI route share `us-market-digest-plan-v1`. Canonical plan SHA is `c9b5a53c451aa0e537f2401892c68d3dccafd299040fa12ec6d628695f397b39`.

| Slot | Plan state | Evidence | AI | Fallback | Final digest |
|---|---|---|---|---|---|
| CURRENT_MARKET | selected, required | SPY, QQQ, IWM, SOXX | consumed | consumed | consumed |
| PARTICIPATION_STYLE | selected, required | RSP, SPY | consumed | consumed | consumed |
| SECTOR_DISPERSION | selected, required | XLK, XLP | consumed | consumed | consumed |
| BREADTH_STATE | omitted unavailable | none | safely omitted | safely omitted | omitted |
| MACRO_CONTEXT | selected, optional | SOXX/SPY relative | consumed in review | represented in fallback context | omitted by concise renderer |

Current-session structure owns the final digest. Macro is optional context and did not replace the required slots. The optional MACRO_CONTEXT plan label is malformed and maps a relative-equity fact under a macro slot; because it was not rendered and did not alter selection or parity, it is recorded as P2 wording/mapping polish.

```text
US_SHARED_MARKET_DIGEST_PLAN = PASS
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
AI_MACRO_ONLY_SELECTION_WITH_CURRENT_MARKET = 0
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0
CORE_MARKET_SLOT_UNCONSUMED = 0
```
