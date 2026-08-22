# 2026-08-22 US AI Hard-error Root Cause

Packet: `2026-08-22-us-run-32-dde10ec6c9eb`

The immutable final candidate reproduced exactly 21 hard errors. Eighteen were
cash-flow period identity errors: CORZ, CRCL, GOOGL, IBM, MU, RXRX, TSLA, and
WULF each omitted fiscal and YTD identity; SNDK omitted fiscal and FY identity.
Three were unknown RR Fact-ID declarations in `price_positioning` for CORZ, HUT,
and WULF.

The cash-flow packet carried period fields, but did not provide a mandatory
canonical label and allowed/forbidden claim contract. The prompt therefore let
the model emit a valid FCF number without enough fiscal-duration prose. The
validator correctly rejected it.

For CORZ, HUT, and WULF, current RR was unavailable because support and
resistance overlapped. Their Fact catalogs correctly omitted
`chart:structure:risk_reward:current_price`, but the prompt had no explicit
catalog-subset ownership rule and the candidate declared that templated ID.

The canonical numbers, FCF formula, price levels, RR calculation, validator,
and deterministic fallback were not the cause and were not weakened.

