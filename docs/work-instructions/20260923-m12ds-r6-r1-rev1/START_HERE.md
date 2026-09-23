# START HERE — M12DS-R6-R1-REV1

Two independent fresh R6 runs reproduced the same partial result:

- Market/Core/A/B all complete
- only 16/24 messages
- night D/W/M PASS
- US stock support/resistance PASS
- Treasury 3/5/10/30 + WTI render restored

Remaining systematic failures:

1. US SPY/QQQ/IWM and sector/style rows stay at 2026-09-04 while session is
   2026-09-22; fresh collector reports ValueError.
   Root cause is NOT yet proven because rejected raw response/exception detail was not
   retained.

2. KR sector HTTP calls succeed 5/5, then ValueError; exact parser/schema cause is not
   retained.

3. All 8 KR stock final messages fail because producer uses `adjusted_intraday` while
   renderer accepts only adjusted_close/close/intraday. Dates actually match.

4. WTI is visible but lagged (2026-09-15); add explicit provider-publication freshness
   classification.

First diagnose with bounded no-model raw/shape/stack receipts. Then repair only existing
approved-provider/request/parser/cache paths when root cause is proven.

Do NOT make stale rows current.
Do NOT add a new provider without Chat.
Do NOT change investment policy.

Use the user-approved standing transport policy:
600s per attempt + up to two byte-identical transient retries (3 attempts total max).
Retry only typed transient transport/process failures; never retry schema/semantic/source-use/policy/security/identity failures.

After offline PASS:
NEW full source generation -> full information coverage gate -> Market/Core/A/B -> exact
24/24 messages -> human review.

Preserve night D/W/M and support/resistance behavior.
No main merge in this task.
