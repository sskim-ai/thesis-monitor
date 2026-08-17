# Massive US Market Provider

## Role

`MassiveUsMarketProvider` is a shadow provider for `market-cross-section-v1`. It calls the official
grouped daily stocks endpoint for the current and previous sessions and the paginated reference
ticker endpoint for active-security metadata.

## Configuration

```dotenv
MASSIVE_API_KEY=
MASSIVE_BASE_URL=https://api.massive.com
MASSIVE_CACHE_DIR=./data/cache/massive
MASSIVE_REQUESTS_PER_MINUTE=5
```

The key is sent only in the `Authorization: Bearer` header. It must not appear in URLs, logs, cache
envelopes, reports, or commits.

## Probe

```bash
python scripts/probe_massive_us_breadth.py \
  --date 2026-08-14 \
  --previous-date 2026-08-13 \
  --live
```

The CLI emits sanitized capability, coverage, exclusion, and calculated breadth data. Direct
execution assumes the project is installed or the repository root is on `PYTHONPATH`.

## Cache

Grouped responses are atomically stored under:

```text
data/cache/massive/us_market_daily/YYYY-MM-DD.json
```

Reference snapshots are atomically stored under `data/cache/massive/reference`. Each envelope records
request date, provider timestamp, latency, and raw response hash. The cache is runtime data and is not
committed.

## Failure Rules

- HTTP denial, rate limit, empty result, duplicate ticker, non-adjusted response, or session mismatch
  fails closed.
- The previous trading session is an explicit caller input; calendar-day guessing is not a production
  contract.
- Missing reference identity or previous adjusted close excludes that security and records a reason.
- No breadth Fact is published from an incomplete/unverified response.

Official references: [Grouped Daily](https://massive.com/docs/rest/stocks/aggregates/grouped-daily),
[Ticker Reference](https://massive.com/docs/rest/stocks/tickers/all-tickers), and
[Stocks plans](https://massive.com/pricing).
