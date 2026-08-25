# US Exchange Breadth Implementation

Implementation SHA: `0e2fc653aa3333e584224043324e4c9fe0ec4cfa`.

- Official parser/provider: `app/providers/nasdaq_trader_breadth_provider.py`
- Fail-open persistence service: `app/services/us_exchange_breadth_service.py`
- Common adapter extension: `app/services/market_context_adapter_service.py`
- US packet collection hook: `app/jobs/monitor_daily.py`
- Exact completed-session loader: `app/services/ai_review_service.py`

The adapter takes its relation scope from the actual scoped breadth. Nasdaq stays
`NASDAQ_LISTED_ISSUES`; existing broad US providers stay `US_BROAD`. Provider failure returns an
internal unavailable receipt and the current US packet continues.
