# Thesis Monitor

Thesis Monitor is a FastAPI service for investment research monitoring. Given a ticker, it collects and normalizes company events such as news, filings, earnings, IR updates, guidance, customer announcements, orders, financing, and competitor events into thesis-relevant JSON.

This project is a data collection and structuring system. It does not make buy, sell, or hold recommendations, and it does not include order execution.

## System Structure

- `app/api`: FastAPI route modules.
- `app/models`: SQLModel persistence models.
- `app/schemas`: explicit API response schemas.
- `app/providers`: provider interface, mock provider, and future provider skeletons.
- `app/services`: event classification, scoring, watchlist, and collection logic.
- `app/jobs`: scheduled collection entry points.
- `docs`: architecture notes, data source roadmap, and Custom GPT Action schema.
- `tests`: pytest coverage for endpoints, classifier, scoring, and fact separation.

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
ENABLE_LIVE_PROVIDERS=false
```

Future providers can use API keys from `.env`, but real keys must never be committed.

Example provider configuration:

```text
ENABLE_LIVE_PROVIDERS=true
OPENDART_API_KEY=
NEWSAPI_API_KEY=
FINNHUB_API_KEY=
ALPHA_VANTAGE_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
OPENAI_API_KEY=
SEC_USER_AGENT=
ACTION_API_KEY=
```

Set `ENABLE_LIVE_PROVIDERS=false` to use only `MockProvider`. Set it to `true` to run `MockProvider` plus live providers in priority order. Provider failures are logged as warnings and do not fail the whole `/thesis-events` request.

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
ruff check .
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
      "provider": "mock",
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
        "dilution_risk": false,
        "capex_impact_known": false,
        "inventory_risk": false,
        "receivables_risk": false
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

Response shape:

```json
{
  "ticker": "NVDA",
  "checkpoints": [
    "Revenue growth vs guidance",
    "Gross margin and operating margin",
    "FCF after capex",
    "Inventory and receivables trend",
    "Customer concentration and demand signals"
  ]
}
```

### Get Company Profile

```http
GET /company-profile?ticker=NVDA
```

## Curl Examples

```bash
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/company-profile?ticker=NVDA"
curl "http://127.0.0.1:8000/thesis-events?ticker=AMD&lookback_days=30"
curl "http://127.0.0.1:8000/earnings-checkpoints?ticker=000660.KS"
curl http://127.0.0.1:8000/watchlist
curl -X POST http://127.0.0.1:8000/watchlist \
  -H "Content-Type: application/json" \
  -d '{"ticker":"NVDA","company_name":"NVIDIA","exchange":"NASDAQ","notes":"AI infrastructure thesis"}'
```

## Custom GPT Action

Use `docs/custom_gpt_action_schema.yaml` as the schema to paste into a Custom GPT Action. For local testing, expose your local FastAPI server with a secure tunnel and update the schema `servers` URL.

The live FastAPI app also exposes `/openapi.json`, which Custom GPT Actions can consume when the service is deployed.

Local Custom GPT Action testing requires an HTTPS URL. Use a tunnel such as ngrok or Cloudflare Tunnel in front of `uvicorn`, then update the schema server URL.

For production deployment, add a simple request authentication layer such as `ACTION_API_KEY` before exposing the API publicly.

## Provider Extension

Provider interfaces live in `app/providers/base.py`.

Initial implementation includes `MockProvider`, which returns sample profile, thesis event, and earnings checkpoint data for:

- `NVDA`
- `AMD`
- `000660.KS`

Future provider modules should implement:

- Google News RSS
- NewsAPI
- OpenDART
- SEC EDGAR filings
- Alpha Vantage
- Yahoo Finance or yfinance
- Company IR pages
- Finnhub
- Naver News
- Korea Exchange and KIND
- Competitor event feeds

Provider output should return raw facts only. Classification and thesis relevance scoring happen in `app/services/event_classifier.py` and `app/services/thesis_scoring.py`.

Current provider status:

| Provider | Status | Notes |
| --- | --- | --- |
| `MockProvider` | mock | Default provider used by API routes for stable local behavior. |
| `GoogleNewsRSSProvider` | live | API-key-free RSS provider. It cleans RSS text, deduplicates provider results, and returns empty results on network failure. |
| `NaverNewsProvider` | live | Uses Naver Search News API with `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET`. |
| `NewsAPIProvider` | skeleton | Requires `NEWSAPI_API_KEY`; mapping is TODO. |
| `OpenDARTProvider` | partial live | Calls OpenDART `list.json` when `OPENDART_API_KEY` and a seed `corp_code` mapping are available. Full ticker mapping is TODO. |
| `SecEdgarProvider` | partial live | Calls SEC submissions JSON for seed ticker-to-CIK mappings. Full ticker mapping is TODO. |
| `AlphaVantageProvider` | skeleton | Requires `ALPHA_VANTAGE_API_KEY`; financial/price mapping is TODO. |
| `CompanyIRProvider` | skeleton | Per-company IR crawler discovery is TODO. |

Provider priority when `ENABLE_LIVE_PROVIDERS=true`:

1. MockProvider
2. GoogleNewsRSSProvider
3. NaverNewsProvider
4. NewsAPIProvider
5. OpenDARTProvider
6. SecEdgarProvider
7. AlphaVantageProvider
8. CompanyIRProvider

Naver API keys can be issued from Naver Developers after creating an application with Search API access. OpenDART keys can be issued from the OpenDART API site. SEC EDGAR does not require an API key, but `SEC_USER_AGENT` must identify the app/user, for example `your-name your@email.com`.

Live provider normalization is intentionally conservative. Headlines and filing titles become `confirmed_facts`; unverified customer names, order size, revenue impact, margin impact, and FCF impact remain in `unknowns` or `inferred_implications`.

## Security Notes

- Keep API keys in `.env` only.
- Commit `.env.example`, never `.env`.
- Do not store brokerage account data, trading API keys, account numbers, or personally sensitive financial data.
- Do not store securities account credentials or order execution keys.
- Do not add order execution features to this service.
- This project is for research monitoring and does not execute trades.
