# Next Patch Plan

This patch turns the current live-provider prototype into a safer development/operation split.

## Goals

1. Add explicit provider switches.
   - `ENABLE_LIVE_PROVIDERS`: enable external providers.
   - `INCLUDE_MOCK_PROVIDER`: include or exclude sample mock data.
   - `LIVE_PROVIDER_TIMEOUT_SECONDS`: common external provider timeout.
   - `NAVER_NEWS_DISPLAY`: max Naver News results per request.
   - `GOOGLE_NEWS_DISPLAY`: max Google RSS results to keep per request.

2. Prevent mock data from leaking into production-style runs.
   - Local/dev default keeps mock enabled.
   - Live runs can set `INCLUDE_MOCK_PROVIDER=false`.

3. Improve provider observability.
   - Add `/provider-status` endpoint.
   - Show enabled providers and whether required credentials are configured.
   - Do not expose actual secrets.

4. Improve event retrieval controls.
   - Add `requires_review_only` query parameter to `/thesis-events`.
   - Add `provider` query parameter to filter by provider.

5. Add tests.
   - Provider mode selection.
   - Provider status endpoint.
   - `requires_review_only` filtering.
   - Provider filtering.

## Non-goals

- Do not add trading/order execution.
- Do not store brokerage credentials.
- Do not expose API keys in responses or logs.
