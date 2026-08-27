# 2026-08-27 US Morning Message Quality

## Existing Runtime Gates

The delivered 14-message set passed the existing validator and runtime message-quality receipt:

- final validator: `passed`
- message-quality receipt: `passed`
- auto-bound numeric claims: `120`
- manual / rejected numeric claims: `0 / 0`
- substantive repeated sentences: `0`
- typed template repeats: `0`
- generic numeric-summary repeats: `0`
- generic methodology repeats: `0`
- rendered identity mismatches: `0`
- final-language hard errors: `0`
- message completeness: `14/14`

The common market renderer selected `CONCISE_HYBRID`; its hard and semantic-ownership validation passed. The concise text is natural, date-qualifies the 8/25 real-yield observation, and avoids unsupported breadth or broad risk-on claims.

## Review-Level Defect

The existing quality receipt does not test whether a completed-session market cross-section survived market evidence selection. Consequently, a syntactically and numerically valid digest passed while omitting SPY/QQQ/IWM/SOXX/RSP and all directional sector rows. This is analysis-quality P1, not a threshold failure and not a reason to relax any validator.

```text
BROAD_RISK_ON_WITHOUT_SUPPORT = 0
UNSUPPORTED_BREADTH_CLAIM = 0
TEMPORAL_LANGUAGE_WITHOUT_CURRENT_EVIDENCE = 0
RUNTIME_QUALITY = PASS
HUMAN_EVIDENCE_UTILIZATION = MATERIAL_P1
```
