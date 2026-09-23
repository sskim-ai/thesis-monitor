# M12DS-R6-R3-REV1 Result Review

## Decision

`PARTIAL SUCCESS — KIWOOM DAILY CLOSE ROLE PROVEN; FINALITY/CUTOFF REMAIN`

Uploaded report SHA-256:
`e62452cc3d736b0e5af30daa8c58ac495d88d22320e25c41816058591456c88f`

Terminal:
`M12DS_R6_R3_REV1_ALPHA_VANTAGE_ACCOUNT_INSUFFICIENT`

This was a correct stop before inference.

## Kiwoom US daily chart

Official schema now proves a key fact that was previously missing.

Endpoint:
`미국주식 일 차트 (usa06012)`

Row fields include:
- `dt` = date
- `open_pric` = open
- `high_pric` = high
- `low_pric` = low
- `cur_prc` = `현재가(종가)`
- volume/value fields

Therefore the context-specific semantic:

`usa06012 dated daily row -> row-local cur_prc = DAILY CLOSE`

is supported by official schema.

This must NOT be generalized to generic Kiwoom quote responses whose `cur_prc` remains
CURRENT_QUOTE.

What is still not proven:
- that the daily row excludes after-hours trades;
- that it stops mutating after the regular-session close;
- that the completed-session row is already available at the actual
  08:05/08:10/08:15/08:20 KST production cutoff.

The direct SPY/NA probe returned code 7 because the exchange-routing probe was wrong or
unresolved. It must not be treated as evidence that SPY/ETFs are unsupported.
Previous gateway evidence had already returned SPY rows successfully.

## Alpha Vantage

One existing-account TIME_SERIES_DAILY call returned HTTP 200 but no data, only the
provider's standard 25-request/day limit notice.

No retry, key change or paid upgrade was used.

Current production-refresh requirement was calculated as 22 calls per full universe; four
full configured attempts would be 88 calls/day.

Therefore the current Alpha account is not a sustainable production fallback under the
existing collection design.

Do not spend more work on Alpha Vantage unless the user separately changes provider/account
authorization.

## KR post-close sector authority

This is PASS.

At approximately 16:14 KST, after the 15:30 close:

For both KOSPI and KOSDAQ:
- exchange state CLOSED;
- ka20001 current composite;
- ka20003 full sector snapshot;
- ka20009 exact-date history;
- same-day level parity exact;
- same-day return parity exact;
- no tolerance;
- complete sector snapshot for the ranking owner.

KOSPI TOP3:
1. 의료/정밀기기 +3.36%
2. 전기/전자 +1.95%
3. 화학 +1.28%

KOSPI BOTTOM3:
1. 건설 -5.66%
2. 기계/장비 -3.22%
3. IT 서비스 -2.40%

KOSDAQ TOP3:
1. 비금속 +3.23%
2. 화학 +3.21%
3. 기계/장비 +2.35%

KOSDAQ BOTTOM3:
1. 금속 -0.82%
2. 운송장비/부품 -0.37%
3. 기타제조 -0.33%

The existing `kr-post-close-sector-session-v1` can now be carried into the full message
proof.

## Validation

Focused:
150 PASS

First full run:
5345 PASS / 1 FAIL / 63 existing skips

The single failure was environment contamination:
an empty process-level Telegram variable overrode the test fixture value.

Same code SHA in clean environment:
5346 PASS / 63 existing skips / 0 FAIL

Ruff / diff / Knowledge:
PASS

This is not a product-code regression.

## Production safety

Operating main unchanged:
`2097645892e30d84aba435416f98e7f9545a87fa`

DB/WAL/schedule hashes unchanged.
Sends/writes/scheduler/broker/deploy = 0.

## Next

R6-R4 should:

1. remove Alpha Vantage from the active qualification path;
2. resolve the correct Kiwoom exchange routing for the canonical ETF universe using the
   existing successful gateway/security identity owner;
3. preserve the official `usa06012 daily-row cur_prc = close` semantic;
4. prove regular-session finality / after-hours non-mutation;
5. first search existing 08:05-era raw receipts/logs for an exact historical cutoff proof;
6. if no such receipt exists, create a bounded read-only cutoff observer for the next
   08:05/08:10/08:15/08:20 window without enabling production jobs;
7. once cutoff proof passes, integrate the Kiwoom daily-close typed owner into the frozen
   R6 market source contract;
8. carry forward the already-PASS KR post-close sector owner;
9. fresh source generation -> Market/Core/A/B -> exact 24/24 capture -> human review.

No new external provider is needed at this point.
