# Kiwoom US Completed Close Ownership

REV47 opt-in source-only integration uses `kiwoom-us-completed-session-price-v2`.
It is not registered in production acquisition, scheduling or delivery.

## Authority

The owner replays immutable `usa20590` request, capture and raw-response bytes.
It requires an exact security/exchange, USD, explicit target `base_dt`, unique
target row, valid finite positive directional-wire price magnitudes and coherent
OHLC. Both the original source clock and the supplement request clock must agree
on the target completed XNYS session. There is no older-row substitution.

Official Kiwoom specification: `Kiwoom-Securities/Kiwoom-REST-API`, commit
`953e5dbff123f437ab4d11a78a95191a685eb51f`,
`kiwoom/_data/kiwoom_api_spec.json`. SHA-256:
`42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79`.
The provider's string sign is a direction marker, not a negative USD price.
Numeric negative values, zero, nonfinite values and inconsistent OHLC fail.

The display/valuation price is an unadjusted historical regular-session close,
not a real-time price. It needs no adjusted/weekly equality inference. Finnhub
atomic valuation, user-authorized FY1 policy and directional exclusions are
unchanged. No implied EPS is derived.

## Technical Boundary

The latest native chart quote does not gain completed-close authority merely
by falling inside its OHLC range. Its explicit denial is
`LATEST_USA06012_CUR_PRC_NOT_COMPLETED_SESSION_CLOSE_AUTHORITY`.

The current declared US corpus has no qualified exact-security US share-unit
compatibility guard. The existing KIS exact guard is domestic KR only. Therefore
REV47 does not invent a no-action assertion or splice raw `usa20590` OHLC into
adjusted history. Current technical consumers are typed unavailable with
`EXACT_US_SECURITY_ADJUSTMENT_COMPATIBILITY_UNPROVEN`; price display and valuation
remain independently eligible. Earlier chart rows are retained for audit, not
silently promoted into current features. Enabling target technical injection
requires a separately qualified guard and an owner-backed compatible series.

## Immutable Composition

`completed-close-lineage.json` declares all US14 supplements, each with exact
request/capture/response/documentation hashes. Artifact paths cannot escape the
source root. Per-stock input hashes, price projections, component hashes and the
whole-source seed bind the complete supplement set. Missing, changed, partial or
wrong-market sets fail. Original REV46 generation IDs, receipt times and raw
bytes remain unchanged. The composed packet declares the additional price time
domain rather than relabeling old evidence as a new acquisition.

The default historical source layout is unchanged. A REV47 proof must include
this explicit lineage; it cannot fall back to the legacy chart price owner if
the declared supplement is absent or invalid.

## Execution Boundaries

No provider request occurs in this owner or its offline tests. Source sealing
precedes any model request. US source/model/message PASS is required before KR;
both markets must pass before main integration. No deployment, Telegram,
scheduler, production DB or broker side effects are authorized by this module.
