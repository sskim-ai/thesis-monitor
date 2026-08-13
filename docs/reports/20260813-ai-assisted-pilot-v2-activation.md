# AI-Assisted Pilot v2 Activation Validation

## Identity

- Base: `e97eaaca4d3dc454628b9303f216395e96ab3e37`
- Analysis policy: `daily-review-v3.3`
- AI output schema: `3`
- Delivery renderer: `ai-assisted-pilot-renderer-v2`
- Pilot state: `data/ai_review/pilot/state-v2.json`
- Investment Knowledge: v3.0, SHA
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge: v1.0, SHA
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

Investment Knowledge v3 is unchanged. The chart reference is a separate byte-identical canonical and
runtime mirror. Production Assist remains disabled; the pilot uses deterministic status, warnings,
facts, and calculations as the official source of truth.

## Activation Gates

| Gate | Result |
| --- | --- |
| Chart Knowledge canonical/runtime checksum | Pass |
| Investment Knowledge v3 checksum unchanged | Pass |
| OHLCV contract inventory and live read-only smoke | Pass |
| Structured chart packet and thesis-version transition | Pass |
| Chart numeric semantic coverage and fail-closed validation | Pass |
| Schema 3 quantitative grounding | Pass |
| Integrated renderer without full deterministic duplication | Pass |
| Old schema/policy output delivery exclusion | Pass |
| Single AI-assisted or deterministic-fallback delivery | Pass |
| Full tests, lint, and diff check | Pass |

## Live Contract Smoke

The operational database discovered 20 active companies dynamically: 7 KR and 13 US. All 20 returned
daily, weekly, and monthly OHLCV context. Nineteen returned the requested Bollinger outputs; `SKHY`
had insufficient long-band output. RSI and MACD were available for all 20. The 7 Korean companies
returned 1-day, 5-day, and 20-day investor flows. US supply and dynamic support/resistance, boxes, ATR,
Elliott, Fibonacci, risk/reward, and chart-state outputs are not in the current provider contract and
remain unavailable rather than inferred.

## Scheduled Tasks

The active local-project schedule remains:

| Task | KST | Role |
| --- | ---: | --- |
| US Primary | 08:50 | Process ready US packet |
| US Backup | 09:30 | Reclaim eligible pending US packet |
| KR Primary | 16:15 | Process ready KR packet |
| KR Backup | 16:55 | Reclaim eligible pending KR packet |

All four task prompts use `$thesis-monitor-daily-review`, `daily-review-v3.3`, schema 3, Investment
Knowledge v3, Chart Knowledge v1, exact numeric claims, and the existing claim/fencing workflow.
They run in the operational local project with `gpt-5.6-sol` and high reasoning. External web research,
source-code changes, direct database mutation, and direct Telegram writes are prohibited.

## Pilot v2

Pilot v1 history remains archived. Pilot v2 starts a separate market counter:

- KR: 0/5 at activation
- US: 0/5 at activation

Only validator-passed, fully archived AI-assisted deliveries increment a counter. A deterministic
fallback is an operational success but does not increment the AI pilot count. After five successful v2
deliveries, that market automatically returns to deterministic delivery; it does not enter Production
Assist.

The delivery rule remains exclusive per packet:

- valid AI output: one integrated AI-assisted set
- no valid AI output by the hard deadline: one stored deterministic fallback set
- old or late schema-2 / `daily-review-v3.2` output: archive only, never Pilot v2 delivery
- partial Telegram delivery: resume the AI-assisted message; never mix in a deterministic full report

## Validation

- Focused Phase 4 tests: 70 passed
- Full test suite: 525 passed, 1 third-party deprecation warning
- Ruff: pass
- `git diff --check`: pass
- DB migration: none
- Public Action schema: unchanged
- Official deterministic assessment and Telegram fallback semantics: unchanged
