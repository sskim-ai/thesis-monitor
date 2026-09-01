# MU Malformed OHLC Forensics

Classification: `TRANSIENT_PROVIDER_DEFECT`

First bad stage: `PROVIDER_RESPONSE_INFERRED`

Root cause: Run-49 was invalid, while adjusted, unadjusted, and direct raw probes now agree on valid OHLC.

Repair category: `PROVIDER_REFETCH_RECOVERED`. Final technical state: `FULL`. No ticker exception, field swap, clipping, or synthetic candle was used.

- daily: `{"close": "956.9700", "date": "20260831", "high": "959.9699", "low": "930.7900", "open": "931.3900", "value": "21358656603", "volume": "22569478"}`; SHA `43df9b6de0ea05a365a0b7f3614f2edc98bc2c1fd628ebd0ee22ffcf61c4bbc6`

Legacy exact specimen: `NOT_RETAINED_BY_LEGACY_PACKET`.
