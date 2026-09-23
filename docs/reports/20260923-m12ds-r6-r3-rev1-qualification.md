# M12DS-R6-R3-REV1 Source Qualification

## Decision

`M12DS_R6_R3_REV1_ALPHA_VANTAGE_ACCOUNT_INSUFFICIENT`

No selected US settled-close route. No model calls, Market/Core/A/B, new messages,
Telegram, production DB/warning writes, scheduler changes, merge, push, or deployment.
This is a local qualification closeout, not a 24-message success.

Base: `d70b18f4619ffb0988236c3620a2841c59cb424d`.
Instructions first frozen at `b1c28e9bf914d8a2b172c59125a76e9b66da3e0a`.
The original ZIP is byte-exact at that commit; only three Markdown trailing spaces
were subsequently removed for diff validation.

## Kiwoom First

The [official pinned schema](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)
explicitly identifies `usa06012` as a daily chart and labels row-local `cur_prc`
as current price/close. The parser already maps it to candle close. This corrects
the overly broad interpretation that a key named `cur_prc` cannot represent close.

Neither this schema nor the inspected parser proves exclusion of extended-hours
trades or immutability after the regular close. `DATED_DAILY_BAR_CLOSE` is therefore
distinct from `SETTLED_REGULAR_SESSION_CLOSE`. Generic quote fields remain quotes.
No latest-row, wall-clock, or next-session shortcut grants finality.

The manual direct SPY probe used `stex_tp=NA` and received provider code 7
(no instrument information). It did not yield a daily row and is not proof that
SPY or the full ETF universe is unsupported. R2's successful normalized SPY response
is retained as older parser evidence, not relabelled as a new R3 result.
Reason: `AFTER_HOURS_CONTAMINATION_POSSIBLE` means unproven exclusion, not observed contamination.

## Alpha Vantage Fallback

After recording Kiwoom's unresolved finality, one existing-key
`TIME_SERIES_DAILY`, compact, SPY request returned HTTP 200 with an Information
notice stating the 25-requests/day limit and no rows. There were no retries,
new keys, account changes, or subscription purchases.

The [official documentation](https://www.alphavantage.co/documentation/)
describes raw daily OHLCV; this is not used to infer an unverified cutoff guarantee.
The [official support page](https://www.alphavantage.co/support/)
states the standard daily limit. The current account tier was not inferred.
The canonical source universe remains 22 symbols, including the full sector ETF set.
One full refresh needs 22 calls; four uncached configured refresh attempts need 88.
Shared-account usage and a sustainable budget are not qualified. Actual first-request
denial, rather than an estimated quota alone, blocks this task.

## KR Post-Close

On September 23 at approximately 16:14 KST, the designated `ka20001`, `ka20003`,
and `ka20009` calls passed for each venue. XKRX regular close was 15:30.
The historical row owns the same date; composite index level and signed return
match exactly in all three responses. No tolerance was added.

`kr-post-close-sector-session-v1` receipts bind request identity, dates, response
hashes, exact parity, and separate KOSPI/KOSDAQ rankings. Ranking uses existing
size/listed-count and sector-taxonomy exclusions, with canonical fact-ID tie-breaks.
This is manual post-close source qualification, not a natural scheduled-run proof.

## Local Scope

Added offline source inspectors and negative controls only. No production-imported
module was edited. The macro informational helper requires a provenance-bound
dated finite FRED value and renders `최신 확인값 (기준 YYYY-MM-DD)` separately;
it can never supply direction references. No new macro live proof or final-message
integration is claimed. KR8 adjusted intraday, night D/W/M, technical support/resistance,
and tactical versus fundamental ownership remain unchanged.

The semantic audit was created before implementation. New tests cover quote-vs-row
context, dates, OHLC enclosure, basis mismatch, after-hours non-promotion, exact
previous session, full universe, Alpha notices/schema, KR parity/venue/ranking,
macro authenticity and informational-only use. Full validation and exact local SHA
are in the external report ZIP and its `validation/final.json`.

## Remaining Gate

US regular-only semantics and actual 08:05/08:10/08:15/08:20 availability remain open.
Afternoon responses cannot supply that morning evidence. Because semantics themselves
are not fully qualified, this is not `US_SEMANTICS_PASS_CUTOFF_OBSERVATION_PENDING`.
No 24-message review ZIP is produced. Fresh KR8 messages, night D/W/M E2E, and
Market/Core/A/B remain conditional on the complete information gate.

Private raw responses, public schema snapshot, receipts, logs and report ZIP/SHA
remain outside Git. Production schedules stay disabled/paused. Main readiness: NO.
