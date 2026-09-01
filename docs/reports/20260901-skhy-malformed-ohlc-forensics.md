# SKHY Malformed OHLC Forensics

Classification: `TRANSIENT_PROVIDER_DEFECT`

First bad stage: `PROVIDER_RESPONSE_INFERRED`

Root cause: Run-49 was invalid, while adjusted, unadjusted, and direct raw probes now agree on valid OHLC.

Repair category: `PROVIDER_REFETCH_RECOVERED`. Final technical state: `FULL`. No ticker exception, field swap, clipping, or synthetic candle was used.

- daily: `{"close": "164.6500", "date": "20260831", "high": "165.0700", "low": "160.5000", "open": "160.7450", "value": "1991101692", "volume": "12183251"}`; SHA `e87b9b3e008d4a9acc059107bc534d740fe24f297113dd5e02304d5589dcd38d`

Legacy exact specimen: `NOT_RETAINED_BY_LEGACY_PACKET`.
