# 2026-08-28 KR Major S/R Before/After

- Subjects: `7`
- Result: `PASS`
- Classification: `{"ABSENT": 4, "OMITTED": 5, "REPLACED": 3, "RETAINED": 2}`
- Near-S/R unchanged: `7/7`

The comparison uses one captured adjusted OHLCV bundle for both revisions. Offline replay
provider calls were zero, so every non-major input is byte-identical.

| Ticker | Side | Result | Before | After | After anchor |
|---|---|---|---|---|---|
| 000660 | MAJOR_SUPPORT | ABSENT | omitted `BALANCE_BOX,BOLLINGER_DAILY` | omitted `BALANCE_BOX,BOLLINGER_DAILY` | - |
| 000660 | MAJOR_RESISTANCE | OMITTED | 약 181.9만~182.9만원 `BOLLINGER_WEEKLY` | omitted `-` | - |
| 003690 | MAJOR_SUPPORT | REPLACED | 약 1.1만~1.2만원 `BOLLINGER_MONTHLY` | 약 1.3만~1.4만원 `BALANCE_BOX` | `v3-balance-box:67010cf1778e629705af` |
| 003690 | MAJOR_RESISTANCE | ABSENT | omitted `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | omitted `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | - |
| 005490 | MAJOR_SUPPORT | RETAINED | 약 30.8만~31.7만원 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | 약 30.8만~31.7만원 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | `v3-pivot:61d4ed64742fdf2c3b84`, `v3-pivot:722dd70f940b5bd489ca`, `v3-pivot:a112aa6f1b1f8eac69b0` |
| 005490 | MAJOR_RESISTANCE | RETAINED | 약 42.5만~43.8만원 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | 약 42.5만~43.8만원 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | `v3-pivot:206cbf280d26e33eb5cd`, `v3-pivot:27d72c0da9ca8a90ae40`, `v3-pivot:92131790e22c1b0f8e22`, `v3-pivot:c51773e328a47a8845ce` |
| 005930 | MAJOR_SUPPORT | OMITTED | 약 19.7만~19.9만원 `BOLLINGER_WEEKLY` | omitted `BALANCE_BOX,BOLLINGER_DAILY` | - |
| 005930 | MAJOR_RESISTANCE | OMITTED | 약 32.4만~32.7만원 `BOLLINGER_MONTHLY` | omitted `-` | - |
| 010120 | MAJOR_SUPPORT | ABSENT | omitted `BALANCE_BOX` | omitted `BALANCE_BOX` | - |
| 010120 | MAJOR_RESISTANCE | OMITTED | 약 26.5만~26.8만원 `BOLLINGER_MONTHLY` | omitted `-` | - |
| 012450 | MAJOR_SUPPORT | OMITTED | 약 95.7만~96.3만원 `BOLLINGER_MONTHLY` | omitted `BALANCE_BOX` | - |
| 012450 | MAJOR_RESISTANCE | REPLACED | 약 145.2만~146만원 `BOLLINGER_MONTHLY` | 약 125.4만~126.8만원 `BOLLINGER_DAILY,PIVOT_DAILY` | `v3-pivot:7e69333277cb5d76404f`, `v3-pivot:8e5c4926ca578df6bb8b` |
| 086280 | MAJOR_SUPPORT | REPLACED | 약 17.8만~18만원 `BOLLINGER_MONTHLY` | 약 17.2만~17.7만원 `BOLLINGER_WEEKLY,PIVOT_WEEKLY` | `v3-pivot:3b0bc390b3b5eced161a` |
| 086280 | MAJOR_RESISTANCE | ABSENT | omitted `BALANCE_BOX` | omitted `BALANCE_BOX` | - |

## Exact Renderer Blocks

### 000660

Before:

```text
📐 현재 가격 구조
• 기준 종가: 1,730,000원
• 가까운 지지: 약 158.1만~159.8만원
• 주요 구조 저항: 약 181.9만~182.9만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 1,730,000원
• 가까운 지지: 약 158.1만~159.8만원
```

### 003690

Before:

```text
📐 현재 가격 구조
• 기준 종가: 14,500원
• 가까운 지지: 약 1.4만~1.41만원
• 가까운 저항: 약 1.48만~1.52만원
• 주요 구조 지지: 약 1.1만~1.2만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 14,500원
• 가까운 지지: 약 1.4만~1.41만원
• 가까운 저항: 약 1.48만~1.52만원
• 주요 구조 지지: 약 1.3만~1.4만원
```

### 005490

Before:

```text
📐 현재 가격 구조
• 기준 종가: 339,500원
• 가까운 지지: 약 32.6만~33.4만원
• 가까운 저항: 약 34.1만~35.1만원
• 주요 구조 지지: 약 30.8만~31.7만원
• 주요 구조 저항: 약 42.5만~43.8만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 339,500원
• 가까운 지지: 약 32.6만~33.4만원
• 가까운 저항: 약 34.1만~35.1만원
• 주요 구조 지지: 약 30.8만~31.7만원
• 주요 구조 저항: 약 42.5만~43.8만원
```

### 005930

Before:

```text
📐 현재 가격 구조
• 기준 종가: 266,000원
• 가까운 지지: 약 25.1만~25.5만원
• 가까운 저항: 약 27.7만~27.9만원
• 주요 구조 지지: 약 19.7만~19.9만원
• 주요 구조 저항: 약 32.4만~32.7만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 266,000원
• 가까운 지지: 약 25.1만~25.5만원
• 가까운 저항: 약 27.7만~27.9만원
```

### 010120

Before:

```text
📐 현재 가격 구조
• 기준 종가: 219,500원
• 가까운 지지: 약 21.1만~21.3만원
• 가까운 저항: 약 22.5만~22.7만원
• 주요 구조 저항: 약 26.5만~26.8만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 219,500원
• 가까운 지지: 약 21.1만~21.3만원
• 가까운 저항: 약 22.5만~22.7만원
```

### 012450

Before:

```text
📐 현재 가격 구조
• 기준 종가: 1,150,000원
• 가까운 지지: 약 110.2만~110.8만원
• 가까운 저항: 약 120.3만~123.4만원
• 주요 구조 지지: 약 95.7만~96.3만원
• 주요 구조 저항: 약 145.2만~146만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 1,150,000원
• 가까운 지지: 약 110.2만~110.8만원
• 가까운 저항: 약 120.3만~123.4만원
• 주요 구조 저항: 약 125.4만~126.8만원
```

### 086280

Before:

```text
📐 현재 가격 구조
• 기준 종가: 203,500원
• 가까운 지지: 약 20.2만~20.32만원
• 가까운 저항: 약 20.9만~21.4만원
• 주요 구조 지지: 약 17.8만~18만원
```

After:

```text
📐 현재 가격 구조
• 기준 종가: 203,500원
• 가까운 지지: 약 20.2만~20.32만원
• 가까운 저항: 약 20.9만~21.4만원
• 주요 구조 지지: 약 17.2만~17.7만원
```
