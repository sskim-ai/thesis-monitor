# KR Daily OHLCV Zero Root Cause

`DAILY_ZERO_ROOT_CAUSE = PASS`

The canonical Price Structure target requested daily `1200`, while the local official/free OHLCV
API validates `count <= 1000`. The pre-enable runtime client sent `count=1200`; the API returned
HTTP 422 before provider collection, and the client therefore passed an empty daily array to the
engine. Weekly 600 and monthly 300 remained below the interface limit and succeeded.

Classification: `PROVIDER_PARAMETER_BUG`. The repair preserves the canonical requested count 1200,
caps only the provider-bound request at the verified interface maximum 1000, and propagates that
limit into coverage. No fallback, resampling, interpolation, or synthetic bar is used.
