# KR Close FX Message Verification

- Run date: 2026-08-12
- Provider: Alpha Vantage `CURRENCY_EXCHANGE_RATE`
- Live parse: USD/KRW, JPY/KRW converted to 100 JPY, and EUR/KRW all available
- Comparison values below are deterministic prior-KR-close fixtures used to verify rendering;
  production compares only with the prior KST-date snapshot from the same provider and series.

## Rendered Message

```text
🇰🇷 한국 시장환경 점검 · 2026-08-12
💱 환율
• 원/달러 1,416.4원 · +7.1원 (+0.51%)
• 원/100엔 886.2원 · -2.8원 (-0.32%)
• 원/유로 1,632.4원 · +5.5원 (+0.34%)
```

On the first collection day, each current rate remains visible and the unavailable comparison
is omitted rather than rendered as zero. Partial provider success renders only available pairs.
