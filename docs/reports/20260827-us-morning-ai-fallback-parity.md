# 2026-08-27 US Morning AI / Fallback Parity

## AI Path

The full structured packet exposed SPY, QQQ, IWM, SOXX, RSP, 11 sector ETFs, XLC level-only state, unavailable breadth, and temporally bound macro facts. Therefore `AI_EVIDENCE_CURRENT_SESSION=PASS` at the input boundary.

The AI-authored `market-review.json`, however, selected only:

```text
market:real_yield:DFII10
market:oil:DCOILWTICO
market:nominal_yield:DGS10
```

No `2026-08-26` core ETF, RSP, or sector fact survived into AI reasoning. This added audit gate is `AI_CURRENT_SESSION_EVIDENCE_UTILIZATION=FAIL`.

## Deterministic Comparison

The receipt-linked deterministic baseline uses the same packet and macro temporal semantics. It also omits all current ETF/RSP/sector facts and leads with real yield, WTI, and nominal yield. Thus the paths agree semantically and temporally, but share the same material omission. Parity is not evidence-utilization success.

The final AI candidate bound `120` numeric claims automatically, with `0` manual, rejected, or unsupported claims. The AI did not calculate sector returns or rankings.

```text
AI_EVIDENCE_CURRENT_SESSION = PASS
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = FAIL
AI_UNREGISTERED_NUMERIC = 0
AI_CALCULATED_MARKET_NUMERIC = 0
AI_FALLBACK_MARKET_SEMANTIC_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS
UNEXPLAINED_AI_INELIGIBILITY = 0
```

Route classification remains `AI`; fallback was not the delivered route.
