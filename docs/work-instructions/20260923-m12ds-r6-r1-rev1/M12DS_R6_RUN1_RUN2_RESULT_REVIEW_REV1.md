# M12DS-R6 Run1/Run2 Review

## Decision

`R6_PARTIAL_SUCCESS_NOT_READY_FOR_MAIN`

Two independent fresh runs reproduced the same information-coverage gaps. This is
strong evidence that the remaining failures are systematic source/contract issues, not
one-off model or transport failures.

### Run 1
- Report ZIP SHA-256:
  `54fa9395432278b9e1acf6c14f5950f80398a8d44c8727ea50bea04ecf57829d`
- Review ZIP SHA-256:
  `7231af5e120791cbdec8f9ddfbb05d3a26bf4f3cf73e41d442c9d3d4e673a2cc`
- Market 2/2, Core 22/22, A 22/22, B 22/22
- 16/24 accepted messages
- one transient inference retry
- night final-message E2E PASS

### Run 2
- Report ZIP SHA-256:
  `d1806ef34ff3de9a3fd5549a1f50aee654d4cff4a41a535223b6716d66f748c7`
- Review ZIP SHA-256:
  `486cbc232f9428a057cd4f2753a6ae3d9549df6ade91883d1fbdd5f29fc9fe2a`
- Market 2/2, Core 22/22, A 22/22, B 22/22
- 16/24 accepted messages
- no actual inference retry
- night final-message E2E PASS

Both runs:
- financial source readiness 22/22
- production sends/writes 0
- main merge/push/deploy 0

## What R6 successfully restored

### US macro display

The final US/KR market messages now visibly contain:
- Treasury 3Y
- Treasury 5Y
- Treasury 10Y
- Treasury 30Y
- WTI
- 10Y real yield
- 10Y breakeven
- high-yield spread
- VIX

The market model correctly refuses to use lagged WTI as evidence of current direction.

However the WTI row is dated 2026-09-15 while the message date is 2026-09-23.
The next repair must explicitly classify provider-publication freshness and render a
lagged-latest row as delayed/latest-published rather than presenting it in the same visual
class as current observations.

### Night futures

This part is a clear PASS.

For both KOSPI200 and KOSDAQ150:
- daily PASS
- weekly in-progress aggregate PASS
- weekly coverage 2/2 elapsed sessions
- monthly official KRX backfill PASS
- monthly coverage 16/16 elapsed sessions
- typed numeric binding PASS
- final-message E2E PASS

Monthly return remains unresolved because there is no prior same-contract monthly
baseline. That is honest and acceptable; monthly OHLC should remain visible.

### Stock technical levels

US stock messages now show explicit:
- technical support
- technical resistance
- tactical watch zone separately

The three concepts remain distinct from the fundamental entry range.

This behavior should be preserved and extended to KR stock messages after the KR capture
contract is fixed.

## Reproduced blocker 1 — US index/sector current bars

Both fresh runs still produce:
- SPY as-of 2026-09-04
- QQQ as-of 2026-09-04
- IWM as-of 2026-09-04
- US sector/style rows as-of 2026-09-04

while the completed US session is 2026-09-22.

Therefore the rows are correctly suppressed as:
- `not_latest_completed_session`
- `row_temporal_or_source_denial`

The fresh collector reports repeated:
`ohlcv_analyst:<symbol>:ValueError`
for indices, sectors/style and large-cap breadth symbols.

The collector did not retain the rejected raw response or detailed exception. Therefore
the exact cause is NOT yet proven.

Do not fix this by weakening session eligibility or admitting 2026-09-04 rows.

The next task must preserve enough provider evidence to determine whether:
1. the provider actually returned only old data;
2. current raw data arrived but parser/normalization failed;
3. a fresh call failed and an old cache/fallback row was retained;
4. request/session parameters are wrong.

Only after that distinction may a bounded repair be made.

US breadth is a separate condition:
the NASDAQ-Trader exact-session file for 2026-09-22 was not yet published and latest
available was 2026-09-18. That `PUBLICATION_PENDING` state is legitimate and must not be
"fixed" by stale substitution.

## Reproduced blocker 2 — KR sectors

KR sector collection reports:
- HTTP/provider requests: 5
- successes: 5
- network failures: 0
- resulting status: `UNAVAILABLE`
- error type: `ValueError`

Again, the frozen collector did not retain the rejected response or detailed error.

This pattern points to response-schema/parser/normalization failure after successful
transport, but the exact root cause is not proven.

The next task must retain a sanitized raw-response SHA/sample/shape and exception stack
locally before changing the parser.

Do not invent a sector ranking from model prose or another taxonomy.

## Reproduced blocker 3 — eight KR stock final messages

All eight KR subjects fail at the final message boundary with:

`accepted_calibration_render_invalid:accepted_quote_asof_invalid`

This is NOT a date mismatch.

For all eight:
- quote `as_of_date` = 2026-09-23
- assessment date = 2026-09-23
- availability = ready
- contract = current-price-context-v1
- producer price_basis = `adjusted_intraday`

The renderer currently accepts only:
- `adjusted_close`
- `close`
- `intraday`

Therefore this is a typed vocabulary mismatch.

Do not silently relabel `adjusted_intraday` as `intraday` or `adjusted_close`.

Repair one shared typed price-basis contract. Prefer decomposing the semantics into:
- phase: INTRADAY / CLOSE
- adjustment: RAW / ADJUSTED

with deterministic legacy mappings.

Then producer, validator, renderer and capture must consume the same canonical contract.

## Transport note

Run 2 used:
- 600s timeout
- up to 2 retries after first attempt (3 attempts maximum)

No retries were actually needed.

The user has now explicitly adopted this as the standing Thesis Monitor policy:

- 600 seconds (10 minutes) per attempt;
- first attempt + up to two byte-identical transient retries;
- maximum 3 attempts total per logical request;
- retry only typed transient transport/process failures;
- never retry schema/semantic/source-use/policy/security/identity failures.

## Next

Run M12DS-R6-R1-REV1:

1. instrument US OHLCV and KR sector failed-source diagnostics before repair;
2. make only a bounded existing-provider parser/request/cache repair once root cause is
   proven;
3. repair the KR current-price basis typed contract;
4. add provider-publication freshness display state for lagged macro rows such as WTI;
5. preserve already-working night D/W/M and stock support/resistance;
6. full regression;
7. new fresh generation;
8. require current US indices/sectors + KR sectors or an explicitly proven upstream
   publication-unavailable state;
9. Market/Core/A/B;
10. exact 24/24 captures;
11. human review before main integration.

Do not start onboarding yet.
