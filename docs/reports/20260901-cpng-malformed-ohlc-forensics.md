# CPNG Malformed OHLC Forensics

Classification: `STABLE_BAD_SOURCE`

First bad stage: `KIWOOM_RAW_RESPONSE`

Root cause: Provider-native daily and weekly rows repeat high < open on 2023-06-05.

Repair category: `RAW_PROVIDER_INVALID_RETAIN_INVALID`. Final technical state: `INVALID`. No ticker exception, field swap, clipping, or synthetic candle was used.

- daily: `{"close": "15.6600", "date": "20230605", "high": "15.8000", "low": "15.4300", "open": "16.3500", "value": "153797295", "volume": "8540469"}`; SHA `040e806e0bdc59b75272f5930c2a51d7d7ba19972f680cb8ffabf3f614f8b193`
- weekly: `{"close": "16.0100", "date": "20230605", "high": "16.2000", "low": "15.4300", "open": "16.3500", "value": "656595258", "volume": "38646007"}`; SHA `ab3fb261697365bf7531f8a40790b02bd7b9391edfcc8b0cf766e702714c9939`

Legacy exact specimen: `RETAINED`.
