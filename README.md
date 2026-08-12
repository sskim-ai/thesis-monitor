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

The default database is SQLite under the local runtime data directory:

```text
DATA_DIR=./data
DATABASE_URL=sqlite:///./data/thesis_monitor.sqlite3
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
KRX_OPEN_API_KEY=
FRED_API_KEY=
EIA_API_KEY=
ECOS_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
OPENAI_API_KEY=
OPENAI_NARRATIVE_MODEL=gpt-5.6-sol
OPENAI_TIMEOUT_SECONDS=60
SEC_USER_AGENT=
ACTION_API_KEY=
OHLCV_BASE_URL=http://127.0.0.1:8765
OHLCV_API_KEY=
NOTIFICATION_DRY_RUN=true
NOTIFICATION_CHANNEL=telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
MACRO_MONITOR_ENABLED=true
```

Set `ENABLE_LIVE_PROVIDERS=false` to use only `MockProvider`. Set it to `true` to run `MockProvider` plus live providers in priority order. Provider failures are logged as warnings and do not fail the whole `/thesis-events` request.

## Telegram Notifications

Telegram is the only supported notification channel. Morning briefings and stock assessments are
sent as readable Korean analysis reports through Telegram. Keep `NOTIFICATION_DRY_RUN=true` until
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` have been tested. The report is generated from structured
macro, company, event, expectation, and valuation data by deterministic rules and templates; it does
not consume OpenAI or other LLM credits. Long reports are split at Telegram-safe boundaries without
dropping analysis sections. Successful chunks are checkpointed in the notification payload, so a
persisted retry resumes from the next chunk instead of repeating normally completed chunks.

The repository-root `.env` is dedicated to thesis-monitor settings. Unknown keys fail validation at
startup, including removed `KAKAO_*` settings and misspelled Telegram keys. Before deploying:

1. Back up `.env` outside the repository.
2. Remove `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, `KAKAO_REFRESH_TOKEN`,
   `KAKAO_TEMPLATE_ID`, and `KAKAO_WEB_URL`.
3. Review key names without printing values:
   `grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env | cut -d= -f1`.
4. Remove other keys that are not thesis-monitor settings, then run
   `.venv/bin/python -m app.jobs.validate_env --env-file .env`.
5. Run `.venv/bin/pytest` and reload the LaunchAgents after validation succeeds.

The validator reports key names and validation categories only; it never prints configured values.

## Macro Monitoring

The 07:50 U.S. monitoring job also builds a macro morning briefing before evaluating the
U.S. stock watchlist. It collects U.S. rates, real yields, breakeven inflation,
credit spreads, volatility, oil, dollar liquidity, U.S. equity and sector
proxies, Federal Reserve releases, big-tech earnings dates, and selected Korean
macro indicators. When the official KRX response explicitly identifies regular/night sessions,
the same contract, and maturity, the briefing also shows KOSPI200 and KOSDAQ150 night-futures
closes versus that contract's regular close. A provider failure produces a partial briefing and does not
stop the stock thesis monitor.

Additional API keys enable the full source set:

- `FRED_API_KEY`: U.S. rates, inflation expectations, credit, volatility, oil,
  dollar, and liquidity series.
- `EIA_API_KEY`: weekly U.S. crude inventories, production, and refinery
  utilization.
- `ECOS_API_KEY`: Bank of Korea rates, USD/KRW, CPI, and M2 key statistics.
- `ALPHA_VANTAGE_API_KEY`: secondary U.S. consensus, share-count, dividend,
  split, and current-multiple cross-checks. Responses are cached and never used
  as point-in-time historical truth. The same key supplies the dedicated 16:05
  KR-close USD/KRW, 100JPY/KRW, and EUR/KRW snapshot.
- `KRX_OPEN_API_KEY`: official KRX index-futures daily data. It is used only when
  explicit session and same-contract evidence passes validation; the key is sent
  in the `AUTH_KEY` header and is never stored in a source URL.
- `ENABLE_NEWSAPI_PROVIDER`: defaults to `false`. A configured NewsAPI key does
  not add NewsAPI to the daily collection path unless this switch is enabled.
- `OPENFIGI_API_KEY`: optional identity-mapping rate-limit upgrade. Keyless
  mapping remains available; official filing identity and ADR documents remain
  authoritative.
- `FMP_API_KEY`: optional secondary/fallback fundamentals adapter. Disabled
  when unset.
- `SHARADAR_API_KEY`: optional U.S. point-in-time validation adapter. Disabled
  when unset.

Macro outputs are stored in SQLite and daily briefing JSON files under
`data/macro/briefings/`. The persistent notification outbox guarantees at most one daily digest per
date and deduplicates same-day material alerts. Read-only Action endpoints include:

```text
GET /macro/briefings/latest
GET /macro/regime/latest
GET /macro/theses
GET /macro/events
GET /macro/provider-status
GET /macro/ticker/{ticker}/impacts
```

The TrendForce DRAM RSS code remains a feasibility probe only. DRAM spot prices,
contract news, and missing-data warnings are not wired into production briefings.

## Run Locally

```bash
uvicorn app.main:app --reload
```

OpenAPI is exposed at:

```text
http://127.0.0.1:8000/openapi.json
```

The filtered Custom GPT Action schema is exposed at:

```text
https://sskim-macmini.tailb44bb1.ts.net/thesis/action-openapi.json
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

### Register or Update a Monitored Thesis

```http
POST /monitoring-items
X-Action-API-Key: configured server key
```

```json
{
  "ticker": "000660",
  "company_name": "SK하이닉스",
  "exchange": "KRX",
  "core_thesis": "HBM demand and execution sustain earnings growth",
  "time_horizon": "2-3 years",
  "strengthen_signals": ["HBM customer expansion"],
  "weaken_signals": ["HBM market share decline"],
  "invalidation_signals": ["major HBM customer loss"]
}
```

Submitting changed thesis fields creates a new version. Submitting the same fields is idempotent.

```http
GET /monitoring-items
GET /monitoring-items/000660
GET /monitoring-items/000660/assessments
POST /monitoring-items/000660/deactivate
```

### Run Daily Monitoring

```bash
python -m app.jobs.monitor_daily --market us
python -m app.jobs.monitor_daily --market kr
python -m app.jobs.monitor_daily --market all
```

The Mac mini U.S. LaunchAgent template is `ops/com.seungsoo.thesis-monitor.daily.plist`. Its 07:50
KST primary slot collects macro data, adds verified KRX night-futures context when available,
evaluates U.S. stocks, and queues notifications. The 08:05 and
08:35 slots retry pending Telegram deliveries when the production analysis already succeeded. The
Korean close template is `ops/com.seungsoo.thesis-monitor.kr-close.plist`; its 16:05 primary slot
collects the dedicated KR-close FX snapshot, reuses same-date morning macro data, and evaluates
Korean stocks after the regular close. FX collection is isolated from the stock run. The 16:20 and 16:50
slots likewise retry pending Telegram deliveries after a successful analysis. A retry starts analysis
recovery only when that market has no successful post-cutoff run; it never refreshes analysis merely
because a delivery is pending. Same-date test runs before the 07:45 U.S. or 16:00 Korean cutoff do not
suppress the scheduled production analysis, while later retry slots do not resend completed messages.
Both `started_at` and `completed_at` must be at or after the market cutoff for a successful run to
replace the scheduled production analysis. Telegram delivery retries resume persisted chunk progress
without refreshing the completed assessment.

Price context is requested from the separate local OHLCV Analyst service using targets of 500 daily,
300 weekly, and 100 monthly bars. Shorter provider histories are accepted and their actual counts are
stored with each assessment. Korean investor flow uses only the latest valid daily bar from OHLCV
Analyst, including individual, institution, and foreign net buying plus the provider's supply summary.

Daily business and valuation decisions are delta-based. Configured expansion or compression
conditions do not change today's valuation unless new evidence matches them. Structural risk and
unresolved warnings persist separately from the daily business-thesis change. U.S. assessments made
during the regular session are marked provisional; the scheduled morning run prioritizes completed
close data.

The valuation snapshot reuses OHLCV Analyst for current prices and Finnhub metrics for supported U.S.
listings. Missing multiples are shown as unavailable, negative-earnings P/E as `N/M`, and unsupported
KRX multiples are never estimated. Provider-defined forward consensus has no guaranteed NTM/FY1
label or denominator timestamp, so those snapshots remain partial unless the provider supplies enough
freshness metadata. `price_rules` are the only source of observer and holder price checks; the service
does not invent support or invalidation levels.

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

Use `openapi.action.json` as the canonical schema for a Custom GPT Action. Configure API-key
authentication with header name `X-Action-API-Key`. Rebuild the schema after route or schema changes:

```bash
python scripts/generate_action_schema.py
```

Paste `docs/custom_gpt_instructions_ko.md` into the GPT Instructions field and upload
`docs/custom_gpt_knowledge_ko.md` as the stable Knowledge reference. Keep secrets only in the
Action authentication settings; do not upload `.env` or runtime files under `data/`.

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
| `GoogleNewsRSSProvider` | live | API-key-free RSS provider. It cleans RSS text and deduplicates provider results. Collection retries transient failures and then continues with other providers. |
| `NaverNewsProvider` | live | Uses Naver Search News API with `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET`. |
| `NewsAPIProvider` | opt-in skeleton | Disabled by default even when a key is configured. |
| `OpenDARTProvider` | partial live | Calls OpenDART `list.json` when `OPENDART_API_KEY` and a seed `corp_code` mapping are available. Full ticker mapping is TODO. |
| `SecEdgarProvider` | partial live | Calls SEC submissions JSON for seed ticker-to-CIK mappings. Full ticker mapping is TODO. |
| `AlphaVantageService` | secondary live | Cached consensus, share-count, dividend, split, and current-multiple cross-checks. |
| `OpenFIGIProvider` | optional identity | Keyless identity lookup with optional key for a higher request allowance. |
| `FMPProvider` | optional adapter | Disabled unless `FMP_API_KEY` is configured. |
| `SharadarProvider` | optional adapter | Disabled unless `SHARADAR_API_KEY` is configured. |
| `CompanyIRProvider` | skeleton | Per-company IR crawler discovery is TODO. |

Provider priority when `ENABLE_LIVE_PROVIDERS=true`:

1. MockProvider
2. GoogleNewsRSSProvider
3. NaverNewsProvider
4. NewsAPIProvider (only when `ENABLE_NEWSAPI_PROVIDER=true`)
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
