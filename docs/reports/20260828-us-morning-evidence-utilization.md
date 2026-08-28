# 2026-08-28 US Morning Evidence Utilization

`market-evidence-utilization-validator-v1` returned `PASS` with no errors. Every required ref was consumed by the AI market review and survived in the concise final message at the semantic level.

| Counter | Value |
|---|---:|
| CORE_MARKET_SLOT_UNCONSUMED | 0 |
| SELECTED_RSP_SLOT_UNCONSUMED | 0 |
| SELECTED_SECTOR_DISPERSION_UNCONSUMED | 0 |
| SELECTED_BREADTH_SLOT_UNCONSUMED | 0 |
| MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE | 0 |
| UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION | 0 |
| VALIDATOR_FORCED_NUMERIC_DUMP | 0 |
| US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS | 0 |

The previous natural defect is closed: the final message no longer drops all current ETF, RSP, and sector-dispersion evidence. Full per-fact extraction is in `20260828-us-morning-data-completeness-matrix.json`.

```text
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
```
