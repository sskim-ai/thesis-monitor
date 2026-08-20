# KR Valuation Basis Caution Audit

## LS ELECTRIC / Hanwha Aerospace

- `010120` LS일렉트릭: issuer `krx`; security `common_stock`; identity `unknown` / `unverified`; EPS basis `unknown`; trailing PE `insufficient_metadata`; PBR `insufficient_metadata`.
- `012450` 한화에어로스페이스: issuer `krx`; security `common_stock`; identity `unknown` / `unverified`; EPS basis `unknown`; trailing PE `insufficient_metadata`; PBR `insufficient_metadata`.

Both records select a KRX common-stock shape, but the source is the inferred local tier and the
canonical identity remains `unknown`/unverified. EPS currency/share basis and book share basis are
not verified; dependent trailing PE/PBR remain unavailable by contract. This is an upstream
identity/denominator limitation, not merely false prose. The repair keeps fail-closed valuation and
does not calculate or mark any denominator verified. The common warning is suppressed only where
company-specific Unknown prose already conveys the decision-relevant limitation.
