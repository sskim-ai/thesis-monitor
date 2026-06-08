# Data Sources

The current implementation uses mock providers. These are placeholders that allow API and Custom GPT Action integration to be tested before external services are connected.

## Current Providers

- `MockNewsProvider`: returns a sample production order event and a low-relevance analyst price target event.
- `MockFilingProvider`: scaffold only.
- `MockEarningsProvider`: scaffold only.
- `MockIRProvider`: scaffold only.

## Future Provider Candidates

- SEC EDGAR for US filings.
- DART and OpenDART for Korean filings.
- Company investor relations pages for earnings releases, presentations, and guidance.
- Yahoo Finance or yfinance for market data and basic financials.
- Alpha Vantage for financial statements and price data.
- Finnhub for company news and earnings calendar data.
- NewsAPI for broad news search.
- Google News RSS for lightweight ticker/company monitoring.
- Naver News for Korean-language news.
- Korea Exchange and KIND for Korean market disclosures.
- Competitor-specific providers for price cuts, product launches, and market share signals.

## Integration Guidelines

Provider implementations should normalize source records into `RawEvent` objects and avoid making investment conclusions. Use `confirmed_facts`, `inferred_implications`, and `unknowns` carefully.

API keys should be defined in `.env.example` and read from `.env` at runtime. Real keys must not be committed.

