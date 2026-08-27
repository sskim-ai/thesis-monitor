# OHLCV Provider Limit And Window Chaining

Contract: `ohlcv-provider-limit-window-chaining-v1`.

## Capability Gate

Window chaining may run only when the official consumer contract exposes a documented cursor,
continuation token, offset, or date boundary. Internal provider pagination is not sufficient when
the caller cannot receive and resume its state.

The current KR `/ohlcv` contract has a maximum `count` of 1000 and exposes no older-window control.
`count=1200` is rejected. An unknown `end_date` returns the current latest window and is not a
supported boundary. Therefore chaining is disabled and no speculative second request is made.

## Safe Chaining Contract

If the provider contract is extended later, a bounded two-window implementation must validate:

- identical security and listing identity;
- identical currency, adjustment, price, and session basis;
- strict canonical trading-date ordering;
- economically identical overlap before dedupe;
- zero duplicate completed bars after merge;
- zero unapproved exchange-session gaps;
- zero partial current bars in completed coverage;
- an exact trim to the canonical 1200 completed daily bars.

Any identity, basis, overlap, or chronology conflict blocks the merge. Weekly and monthly data may
never be converted into missing daily rows.

## Current Result

`DAILY_1200_PROVIDER_CAPABILITY = PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW`

`DAILY_1200_IMPLEMENTATION_PATH = VERIFIED_PARTIAL_SAFE_1000`
