# 2026-09-03 KR Natural Run Anomalies

## P0

Open P0: 0.

The actual deterministic delivery was complete, exactly once, and based on current KR source/technical/supply facts. No wrong-market text was found in the delivered messages.

## P1 Observations

1. The corrected 16:05 AI candidate passed validation, but its delivery receipt remained `pending` with 0/9 sent. Delivery-retry runs reported `no_pending_ai_delivery`; no natural artifact explains the queue-state mismatch. The bounded first failing area is the accepted-candidate to delivery-queue handoff.
2. Packet `78ed269de3df` acquired a validation result at 17:10:56, after the 17:10:06 fallback dispatch. It contains KR-irrelevant `IWM/SPY` numeric semantic errors. Chronology proves this file did not trigger or contaminate the already-sent fallback, but its packet ownership/provenance is anomalous and should be audited separately.

## P2 / Data Quality

- The quality receipt intentionally covered only the adaptive canary set: market + two stocks, not all KR8.
- The 16:20 and 16:50 analysis-reuse invocations each performed 42 successful Kiwoom calls. This is operational overhead, not a correctness failure.
- All KR8 supply rows had material omitted-participant flow, so three-participant attribution was qualified rather than complete.
- SK하이닉스 earnings fields were tainted by critical profitability outliers; the system correctly withheld those figures and earnings-based multiples.
- LS일렉트릭, 한화에어로스페이스, and 한국항공우주산업 had no safe current valuation multiple; the delivered text did not recompute one.
- The 16:05 independent KRX publication check returned four empty HTTP-200 responses while current Kiwoom context remained available.
- Source-owned full-window `period_return_pct` values can be very large and must not be relabeled as one-day/one-week/one-month returns. They were not user-visible.

No repair, replay, rerun, or production mutation was performed.

