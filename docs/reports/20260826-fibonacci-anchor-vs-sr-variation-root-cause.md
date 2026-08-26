# Fibonacci Anchor vs SR Variation Root Cause

| Timeframe | True anchor material | SR-only material | Mixed material | Stable/minor |
|---|---|---|---|---|
| monthly | 2 | 1 | 0 | 17 |
| weekly | 3 | 7 | 1 | 9 |
| daily | 2 | 3 | 5 | 10 |

## Exact Tickers

```json
{
  "daily": {
    "MIXED_MATERIAL": [
      "010120",
      "IBM",
      "RXRX",
      "TSM",
      "WULF"
    ],
    "SR_ONLY_MATERIAL": [
      "003690",
      "005490",
      "GOOGL"
    ],
    "STABLE_OR_MINOR": [
      "000660",
      "005930",
      "012450",
      "CORZ",
      "CRCL",
      "HUT",
      "MU",
      "SKHY",
      "TSLA",
      "WRD"
    ],
    "TRUE_ANCHOR_MATERIAL": [
      "086280",
      "SNDK"
    ]
  },
  "monthly": {
    "SR_ONLY_MATERIAL": [
      "IBM"
    ],
    "STABLE_OR_MINOR": [
      "000660",
      "003690",
      "005490",
      "005930",
      "010120",
      "012450",
      "086280",
      "CORZ",
      "CRCL",
      "GOOGL",
      "HUT",
      "SKHY",
      "SNDK",
      "TSLA",
      "TSM",
      "WRD",
      "WULF"
    ],
    "TRUE_ANCHOR_MATERIAL": [
      "MU",
      "RXRX"
    ]
  },
  "weekly": {
    "MIXED_MATERIAL": [
      "RXRX"
    ],
    "SR_ONLY_MATERIAL": [
      "000660",
      "003690",
      "005490",
      "005930",
      "GOOGL",
      "IBM",
      "TSLA"
    ],
    "STABLE_OR_MINOR": [
      "010120",
      "012450",
      "086280",
      "CORZ",
      "CRCL",
      "HUT",
      "MU",
      "SKHY",
      "TSM"
    ],
    "TRUE_ANCHOR_MATERIAL": [
      "SNDK",
      "WRD",
      "WULF"
    ]
  }
}
```

The old classifier included AI-selected SR IDs in the same signature as swing anchors. The new
classifier measures only canonical swing-structure status and IDs; deterministic SR is audited
separately and has no variable-AI owner.
