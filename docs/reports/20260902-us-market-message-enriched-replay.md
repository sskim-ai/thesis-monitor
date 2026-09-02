# US Market Message Enriched Replay

Packet: `2026-09-02-us-run-51-39a4d4eec53e`.

The replay keeps the frozen index, style, sector, and selection inputs unchanged. It adds only the approved compact KRX NIGHT projection and official nominal Treasury curve facts. Production send and packet mutation are both zero.

```text
🌙 한국 야간선물 · 기준 09/01
• KOSPI200 최근월물 (202609)
  - 일봉: 시가 1,067.00 · 종가 1,064.50 · 갭 -0.08% · 등락 -0.31%
  - 주봉(진행중): 시가 1,068.00 · 종가 1,064.50 · 주간 -1.60%
  - 월봉(진행중): 시가 1,067.00 · 종가 1,064.50 · 월간 +0.03%
• KOSDAQ150 최근월물 (202609)
  - 일봉: 시가 1,440.00 · 종가 1,432.80 · 갭 -0.01% · 등락 -0.51%
  - 주봉(진행중): 시가 1,456.00 · 종가 1,432.80 · 주간 -2.99%
  - 월봉(진행중): 시가 1,440.00 · 종가 1,432.80 · 월간 -0.97%

🌐 미국 국채금리 · 08/31 관측
• 3년: 4.40% · -1bp
• 5년: 4.49% · +1bp
• 10년: 4.75% · +2bp
• 30년: 5.25% · +3bp
```

Machine proof: `docs/reports/20260902-us-market-proof.json`, status `PASS`. Treasury numeric registry unsupported count is zero; high/low and primary real-yield occurrences are zero.

`USER_FACING_PRIMARY_RATE_BLOCK = NOMINAL_3Y_5Y_10Y_30Y`

`TRACK_C_US_MARKET = PASS`
