# US Daily Digest Night Futures Validation

## Scope

- Repository baseline: `a8aab0dba86bf4821baee90096c4b9999431e853`
- Production path: morning macro collection -> US daily monitoring -> daily digest -> Telegram
- DB migration: none
- Public Action contract: unchanged (`0.4.5`, 20 operationIds)
- GitHub Actions: pending at report creation

## Root Cause

The morning `MacroBriefing.market_summary` contained both KRX night-futures series and
`_macro_report()` had a private renderer for them. `DailyDigest` and
`render_daily_digest()` did not carry or render those observations, so the US morning
Daily Digest omitted the section.

Freshness had a separate defect. KRX observations used the generic daily rule, which
allows up to four calendar days. The 2026-08-13 07:50 KST briefing therefore stored the
2026-08-11 KRX session as `fresh`, even though the latest completed XKRX session for the
morning of 2026-08-13 was 2026-08-12.

The exact 07:50 KRX response for 2026-08-12 was not persisted, so it cannot now be
distinguished whether that date was wholly empty or contained regular rows without a
verified night pair. A live re-probe at 08:35 KST confirmed that the official endpoint
then exposed the complete 2026-08-12 regular/night pairs. The defect was the decision to
let an older pair pass as fresh during that source delay.

## Freshness Design

The provider now combines two independent checks:

1. The XKRX trading calendar determines the latest completed exchange session before the
   morning run date.
2. The official KRX response still must contain explicit regular/night rows, the same
   contract code, and a verified maturity.

The probe records each queried date as `empty`, `rows_without_verified_pair`,
`verified_pair`, or `fetch_error`. Empty weekend and exchange-holiday dates do not make a
valid prior session stale. An older pair is stale when the XKRX calendar says a newer
session completed, even if the newer API payload is temporarily empty.

The provider persists `trade_date`, `expected_latest_session_date`, and
`session_freshness` in internal observation metadata. Existing observations can have
their explicit provider freshness refreshed without creating a duplicate row.

## 2026-08-13 Diagnostic

### Stored at 07:50 KST

| Series | API trade date | Retrieved at | Stored quality | Expected session | New decision |
|---|---|---|---|---|---|
| KOSPI200 night | 2026-08-11 | 2026-08-13 07:50:26 KST | fresh | 2026-08-12 | stale, excluded |
| KOSDAQ150 night | 2026-08-11 | 2026-08-13 07:50:26 KST | fresh | 2026-08-12 | stale, excluded |

The KRX response exposes `BAS_DD` as the trade/session date but no separate intraday
source timestamp. Retrieval time is therefore retained separately and is not used as a
substitute trade date.

Rendering the existing 07:50 briefing with the hardened code produces no price section
and one compact caution:

```text
⚠️ 데이터 주의
• 한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해 오늘 개장 전 신호에서 제외했습니다.
```

### Official live re-probe at 08:35 KST

- Queried dates: 2026-08-13, 2026-08-12
- 2026-08-13: empty
- 2026-08-12: 385 rows, explicit `정규` / `야간`
- Expected latest completed session: 2026-08-12
- Session freshness: fresh
- KOSPI200 2026-09: regular 1,035.30, night 1,002.50, -32.80pt (-3.1682%)
- KOSDAQ150 2026-09: regular 1,478.30, night 1,482.40, +4.10pt (+0.2773%)

## Daily Digest Rendering

The macro report and Daily Digest now use the same summarizer and formatter. The Daily
Digest inserts the section between `📈 중요한 변화` and `🧭 현재 시장 상황`.

```text
🌙 한국 야간선물 · 08/12 기준
• KOSPI200 최근월물 1,002.50 · -32.80pt (-3.17%)
• KOSDAQ150 최근월물 1,482.40 · +4.10pt (+0.28%)
```

Partial input displays only the fresh contract and adds one contract-specific caution.
If both contracts are stale, the price section is omitted and only the compact caution is
added to the existing data-quality section.

No night-futures move changes the six-axis regime, macro thesis, company thesis,
earnings estimate, market expectation, structural risk, or valuation state.

## Validation

- Full pytest: 430 passed, 1 pre-existing Starlette deprecation warning
- Focused KRX / digest / macro renderer tests: 54 passed
- Ruff: passed
- Diff check: passed

Coverage includes both fresh, both stale, each partial direction, explicit trade-date
precedence over provider timestamps, actual stale source lag, weekend, XKRX holiday,
provider quality persistence, and macro-renderer consistency.
