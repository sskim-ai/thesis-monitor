# US Exchange Breadth Source Capability

`NASDAQ_OFFICIAL_BREADTH_CONTRACT = PASS`

The official NasdaqTrader year-to-date daily file exposes Date, Advances, Declines, and Unchanged
for Nasdaq issues. The implementation preserves the exact venue scope and does not call it NYSE,
all-US, or S&P 500 breadth.

- Daily files: https://www.nasdaqtrader.com/Trader.aspx?id=DailyMarketFiles
- Field definitions: https://www.nasdaqtrader.com/Trader.aspx?id=DailyMarketSummaryDefs
- Exact YTD file: https://www.nasdaqtrader.com/dynamic/dailyfiles/daily2026.csv
- Retrieved payload SHA-256: `144e90c0f869f4f09858fbd3b7af831ffe660f2ae3614e5dceb85ae772837e23`
- Latest published session in the retrieved file: `2026-08-20`
- Invalid unrelated breadth rows retained for audit: `2026-03-09`

Provider calls in this task: Nasdaq HTTP requests `1/1` successful, cache hits `0`; OpenDART `0`;
paid source or subscription `0`.
