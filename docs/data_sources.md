# Data Sources

The default API flow uses mock providers so local tests and Custom GPT Action integration remain deterministic. External providers are added as optional classes and should be enabled deliberately after credentials, rate limits, and source terms are reviewed.

## Current Providers

- `MockProvider`: mock profile, event, and earnings checkpoint data for `NVDA`, `AMD`, and `000660.KS`.
- `GoogleNewsRSSProvider`: live, keyless RSS search provider. It maps headlines to conservative `RawEvent` objects.
- `NewsAPIProvider`: skeleton, returns empty results unless `NEWSAPI_API_KEY` is configured; API mapping is TODO.
- `OpenDARTProvider`: skeleton, returns empty results unless `OPENDART_API_KEY` is configured; Korean ticker to DART `corp_code` mapping is TODO.
- `SecEdgarProvider`: skeleton, returns empty results unless `SEC_USER_AGENT` is configured; ticker to CIK mapping is TODO.
- `AlphaVantageProvider`: skeleton, returns empty results unless `ALPHA_VANTAGE_API_KEY` is configured.
- `CompanyIRProvider`: skeleton for future company IR crawling.

## Priority Order

1. Google News RSS or NewsAPI for broad event discovery.
2. OpenDART for Korean filings.
3. SEC EDGAR for US filings.
4. yfinance or Alpha Vantage for price and financial statement signals.
5. Company IR crawler for official earnings releases, presentations, and guidance.

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

Do not place unverified customer names, order sizes, revenue impact, or margin impact in `confirmed_facts`. If a source only hints at those items, put them in `unknowns` or `inferred_implications`.
