# Thesis Monitor

Thesis Monitor is a FastAPI service for investment research monitoring. Given a ticker, it collects and normalizes company events such as news, filings, earnings, IR updates, guidance, customer announcements, orders, financing, and competitor events into thesis-relevant JSON.

This project is a data collection and structuring system. It does not make buy, sell, or hold recommendations, and it does not include order execution.

## Install

```bash
cd thesis-monitor
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Environment

Copy `.env.example` to `.env` for local configuration.

```bash
cp .env.example .env
```

The default database is SQLite:

```text
DATABASE_URL=sqlite:///./thesis_monitor.sqlite3
```

Future providers can use API keys from `.env`, but real keys must never be committed.

## Run Locally

```bash
uvicorn app.main:app --reload
```

OpenAPI is exposed at:

```text
http://127.0.0.1:8000/openapi.json
```

## Test

```bash
pytest
```

## API Endpoints

### Health

```http
GET /health
```

Response:

```json
{"status": "ok"}
```

### Add Watchlist Item

```http
POST /watchlist
```

Request:

```json
{
  "ticker": "NVDA",
  "company_name": "NVIDIA",
  "exchange": "NASDAQ",
  "notes": "AI infrastructure thesis"
}
```

### List Watchlist

```http
GET /watchlist
```

### Get Thesis Events

```http
GET /thesis-events?ticker=NVDA&lookback_days=30
```

Response shape:

```json
{
  "ticker": "NVDA",
  "company_name": "NVIDIA",
  "lookback_days": 30,
  "events": [
    {
      "date": "2026-06-08",
      "source": "Company IR",
      "title": "Example production order with named hyperscale customer",
      "url": "https://example.com/production-order",
      "event_type": "production_order",
      "confirmed_facts": ["Customer name was disclosed"],
      "inferred_implications": [
        "Potential revenue contribution, but margin impact is not yet confirmed"
      ],
      "unknowns": ["Order size and margin profile were not disclosed"],
      "financial_impact": {
        "revenue_guidance_changed": false,
        "margin_guidance_changed": false,
        "fcf_impact_known": false,
        "dilution_risk": false
      },
      "thesis_relevance": {
        "requires_review": true,
        "relevance_score": 45,
        "reason": "named customer was disclosed; production order may validate demand thesis"
      }
    }
  ]
}
```

### Get Earnings Checkpoints

```http
GET /earnings-checkpoints?ticker=NVDA
```

### Get Company Profile

```http
GET /company-profile?ticker=NVDA
```

## Custom GPT Action

Use `docs/custom_gpt_action_schema.yaml` as the schema to paste into a Custom GPT Action. For local testing, expose your local FastAPI server with a secure tunnel and update the schema `servers` URL.

The live FastAPI app also exposes `/openapi.json`, which Custom GPT Actions can consume when the service is deployed.

## Provider Extension

Provider interfaces live in `app/providers/base.py`.

Initial implementation includes mock providers so the API works without external keys. Future provider modules should implement:

- SEC EDGAR filings
- DART and OpenDART filings
- Company IR pages
- Yahoo Finance or yfinance
- Alpha Vantage
- Finnhub
- NewsAPI
- Google News RSS
- Naver News
- Korea Exchange and KIND
- Competitor event feeds

Provider output should return raw facts only. Classification and thesis relevance scoring happen in `app/services/event_classifier.py` and `app/services/thesis_scoring.py`.

## Security Notes

- Keep API keys in `.env` only.
- Commit `.env.example`, never `.env`.
- Do not store brokerage account data, trading API keys, account numbers, or personally sensitive financial data.
- This project is for research monitoring and does not execute trades.

