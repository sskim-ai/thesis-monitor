# C21S boundary corrections

The native /ohlcv path is dated adjusted-bar research, not an independent
current-price Owner. PriceContext carries dated_technical_only through public
JSON serialization. The thesis and valuation consumers cannot fall back to a
technical period's latest_close for this scope. An already admitted independent
PriceDecisionContext remains distinct and is not overwritten by those consumers.
No new quote Owner issuance API is introduced.

Raw daily and independent unadjusted valuation history labels are never shifted.
Chart dates and technical histories use the native completed projection.
Missing current-price authority stays unavailable with an explicit warning.

Requests explicitly enable investor flows only for KR adjusted daily bars.
KR W/M and unadjusted valuation W, and all US requests, disable them. Existing
provider twenty-session flow fields and reconciliation are preserved; the test
fixture supplies those fields rather than inventing a new backend aggregate.

Per-bar indicator attachment is min(request_count, 5), or zero when disabled.
Only provider values are selected; missing/null/warmup fields are not recomputed.
D1000/W700/M300 ceilings and Pivot D300/W120/M60 remain unchanged.

New tests are isolated from prior passing suites. The earlier C21R request-limit
assertion is updated to five for future runs, but its suite was not rerun here.
Synthetic freshness rejection remains evidence, not a reason to relax the gate.

Live source authority remains unproven. The full fetch_price_context path makes
four service GETs per security (three technical plus valuation W), not three.
A technical-only KR+US plan is six service GETs; full fetch is eight. Neither is
approved for live execution here, and neither number specifies underlying
Kiwoom authentication, identity, pagination, or investor-flow HTTP attempts.

Real W/M completion labels, deployed process/code/settings identity, original
Source Parent, and account/Lane budget need separate evidence and live approval.
No service settings, rollout flags, Source/Stage/Rust/account gates are changed.
