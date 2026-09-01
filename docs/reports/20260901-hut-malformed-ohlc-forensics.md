# HUT Malformed OHLC Forensics

Classification: `INTERMITTENT_BAD_SOURCE`

First bad stage: `KIWOOM_RAW_RESPONSE`

Root cause: The dated daily/weekly row carries a mutable cur_prc above the row high.

Repair category: `RAW_PROVIDER_INVALID_RETAIN_INVALID`. Final technical state: `INVALID`. No ticker exception, field swap, clipping, or synthetic candle was used.

- daily: `{"close": "81.9400", "date": "20260831", "high": "79.9900", "low": "75.7100", "open": "79.4300", "value": "326287049", "volume": "4201466"}`; SHA `18aa3dc5e29ca6c0fef996945925c47d6699931cffb6434c81a409d19e438caa`
- weekly: `{"close": "81.9400", "date": "20260831", "high": "79.9900", "low": "75.7100", "open": "79.4300", "value": "326287049", "volume": "4201466"}`; SHA `f41b46f51f8b9719c6088aff569661eb9f4a306a2bcee7a55d6ba8a77dc40b56`

Legacy exact specimen: `RETAINED_CURRENT_PROBES`.
