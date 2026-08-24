# 2026-08-24 Macro Today-Signal Audit

## Runtime Wiring

| Consumer | Before | After |
|---|---|---|
| Regime/state | all latest source-usable observations | unchanged background state |
| Daily axes | inherited regime axes | current observations only |
| Thesis `today_signal` | all fresh/revised axes | current-only daily axes |
| Macro shock | latest fresh observation | current-series allow set |
| Ticker impact | latest fresh factor | current-series allow set; events still date-gated |
| Digest one-line | regime axes presented as today | current-only axes; explicit no-new-signal path |
| Important changes | all source-fresh changes | current, or explicitly labeled prior session |

## Run-35 Result

- Current observations: 0.
- Prior market session: SPY, QQQ, IWM, SOXX (all 2026-08-21).
- Reference lagging: DGS10, DFII10, T10YIE, BAMLH0A0HYM2, DTWEXBGS, USDKRW,
  DCOILWTICO, VIXCLS.
- Daily axes after gate: growth 0, inflation 0, liquidity 0, financial conditions 0,
  risk appetite 0, earnings momentum 0.
- False current ticker impacts after gate: 0.
- Structural macro thesis state mutations from no-new-signal: 0.

## Fixture Matrix

| Case | Equity | Release series | Result |
|---|---|---|---|
| Monday after weekend, no new facts | prior Friday | unchanged | no new signal |
| US holiday | prior completed session | unchanged | no new signal |
| Normal after-close weekday | new completed session | per series | current equity signal retained |
| New macro release while cash market closed | prior equity | new official occurrence | release is current |
| Mixed timing | prior equity | current VIX, reference WTI | VIX only affects daily axes |
| Source quality stale | any | any | stale for daily signal |
| Same-period official revision | unchanged occurrence date | revised value | current release occurrence |
| Early close | actual XNYS session close | per series | completed session recognized |
| Prior/reference only | prior/reference | prior/reference | no daily direction generated |

No blanket `market_session == closed` suppression and no elapsed-day threshold were introduced.
