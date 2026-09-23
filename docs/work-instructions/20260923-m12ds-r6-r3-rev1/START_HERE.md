# START HERE — M12DS-R6-R3-REV1

Important revision:

DO NOT start with Alpha Vantage.

First prove whether the existing Kiwoom `usa06012` response is a true dated DAILY
OHLCV/candle route whose row-local `cur_prc` is the candle CLOSE.

The same field name `cur_prc` in a generic quote context remains CURRENT_QUOTE.
Only the dated daily-row context may be mapped to CLOSE, and only after official
documentation + live behavior prove the semantics/finality.

US priority:
1. Kiwoom `usa06012` daily-row close qualification.
2. If and only if Kiwoom cannot prove regular-session settled close, use the already
   configured Alpha Vantage account for bounded TIME_SERIES_DAILY qualification.
3. No new key, no paid upgrade, no other provider.

Still required:
- actual 08:05/08:10/08:15/08:20 KST cutoff availability proof
- SPY/QQQ/IWM + full sector ETF universe
- same-basis current/previous close
- deterministic US sector TOP3/BOTTOM3

KR:
- after KRX close, prove ka20001 + ka20003 same-session ownership against ka20009
- then KOSPI/KOSDAQ TOP3/BOTTOM3

Preserve:
- KR adjusted_intraday basis
- night D/W/M
- technical support/resistance
- tactical/fundamental separation
- latest-available WTI display separate from direction evidence

Only after US + KR information gates pass:
NEW fresh generation -> Market/Core/A/B -> exact 24/24 capture.

Transport:
- 600s per attempt
- up to 2 byte-identical transient retries
- max 3 attempts total

Do not enable disabled production schedulers.
No main merge in this task.
