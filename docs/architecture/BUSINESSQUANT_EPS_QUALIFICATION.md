# Business Quant EPS Qualification

REV42 is an offline denominator qualification experiment, not a production feed.
The work instruction was committed before implementation. Its scope excludes
price acquisition, forward-PER calculation, model calls, rendering, Telegram,
operating database changes and deployment.

## Access and Identity

The documented route is `GET https://data.businessquant.com/estimates`, with an
exact ticker, `mode=eps`, and an API key supplied only by the private caller.
Public request receipts contain no key or authenticated URL. API documentation
and pricing advertise free estimates; actual account entitlement must still be
verified. HTTP 200 does not establish requested-security coverage.

Metadata ticker and normalized CIK must both match independently accepted
listing/issuer identity. A free preview for another issuer is never assigned to
the requested ticker. Provider notes are diagnostic only, not numeric authority.
Raw response hash verification precedes parsing. Unexpected error envelopes and
transport failures are not treated as missing analyst coverage.

## Period and Basis

Use only the annual dimension. Select the latest reported fiscal year, then the
first later estimate. Require consecutive fiscal-year labels, never the largest
forecast year or a quarterly sum. Fiscal labels need not describe calendar years;
an undocumented period-end field does not become authoritative by observation.

EPS remains provider consensus with unspecified accounting methodology.
Retrieval time never fills estimate publication time. Negative and zero EPS are
valid observations if all other gates pass; this module calculates no multiple.

Currency and share basis require independently reviewed EPS-series evidence,
bound to the exact provider response, ticker and CIK. The conservative calibration
check requires at least two distinct annual reported values with exact Decimal
equality, zero numeric tolerance, matching currency and listed-share scope.
Historical matches alone do not assign GAAP/non-GAAP status. ADS qualification
additionally requires a source-owned ratio and explicitly proven ADS EPS series;
the ratio never triggers conversion or establishes the EPS basis by itself.

## Quota and Replay

The updated user cap is 18 attempted data calls, target 14, at most one normal
request per ticker. Exclusive persistent reservations count a crash as attempted;
the offline reservation helper rejects duplicates. Transport retries are not
implemented or used, even though the user allows one when no valid body exists.
No retry for HTTP 400/401/403/404, empty estimates, parser errors or ADR ambiguity.
On quota exhaustion use `DAILY_QUOTA_CONTINUATION_REQUIRED`; do not confuse it
with plan entitlement. A continuation must reuse sealed successful responses.

Actual responses live in the private report directory, never in Git. Unit tests
use fictional fixtures; integration/full validation denies outgoing sockets/DNS.
Replays must verify the original hashes and produce byte-identical canonical
semantics. Only secret-scanned result archives may enter the user's private
iCloud folder; there is no permission for public raw-data redistribution.

Official references: [estimates](https://businessquant.com/docs/api/estimates),
[overview](https://businessquant.com/docs/api/overview),
[pricing](https://businessquant.com/pricing),
[terms](https://businessquant.com/terms-of-use).
