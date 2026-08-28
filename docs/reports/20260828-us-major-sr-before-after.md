# 2026-08-28 US Major S/R Before/After

- Subjects: `13`
- Result: `PASS`
- Classification: `{"ABSENT": 6, "OMITTED": 4, "REPLACED": 7, "RETAINED": 9}`
- Near-S/R unchanged: `13/13`

The comparison uses one captured adjusted OHLCV bundle for both revisions. Offline replay
provider calls were zero, so every non-major input is byte-identical.

| Ticker | Side | Result | Before | After | After anchor |
|---|---|---|---|---|---|
| CORZ | MAJOR_SUPPORT | REPLACED | 약 $16.25~$16.34 `BOLLINGER_MONTHLY` | 약 $13.32~$13.6 `PIVOT_MONTHLY` | `v3-pivot:1945039698d19a0041b1`, `v3-pivot:e84fe5838c9d280b9714` |
| CORZ | MAJOR_RESISTANCE | RETAINED | 약 $18.58~$18.68 `PIVOT_MONTHLY` | 약 $18.58~$18.68 `PIVOT_MONTHLY` | `v3-pivot:11acb35f80bf7aff9a8e` |
| CRCL | MAJOR_SUPPORT | RETAINED | 약 $84.05~$85.6 `BOLLINGER_WEEKLY,PIVOT_WEEKLY` | 약 $84.05~$85.6 `BOLLINGER_WEEKLY,PIVOT_WEEKLY` | `v3-pivot:3ba0d6a4282e01d42ddb` |
| CRCL | MAJOR_RESISTANCE | RETAINED | 약 $110.92~$111.48 `PIVOT_WEEKLY` | 약 $110.92~$111.48 `PIVOT_WEEKLY` | `v3-pivot:7e674dd0875b4e7ac0af` |
| GOOGL | MAJOR_SUPPORT | OMITTED | 약 $267.08~$268.43 `BOLLINGER_MONTHLY` | omitted `-` | - |
| GOOGL | MAJOR_RESISTANCE | REPLACED | 약 $424.82~$426.96 `BOLLINGER_MONTHLY` | 약 $359.84~$361.66 `BALANCE_BOX` | `v3-balance-box:f9459a3f3cd44b427f10` |
| HUT | MAJOR_SUPPORT | RETAINED | 약 $65.9~$66.24 `PIVOT_MONTHLY` | 약 $65.9~$66.24 `PIVOT_MONTHLY` | `v3-pivot:569300fa2e406317769f` |
| HUT | MAJOR_RESISTANCE | OMITTED | 약 $99.21~$99.72 `BOLLINGER_WEEKLY` | omitted `BALANCE_BOX,BOLLINGER_DAILY` | - |
| IBM | MAJOR_SUPPORT | RETAINED | 약 $209.46~$216.44 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | 약 $209.46~$216.44 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | `v3-pivot:0496a99e9271406d735f`, `v3-pivot:0a299e34fa49e074ce09`, `v3-pivot:2b177166eb439fc537f0`, `v3-pivot:daaecabe29891d2448c2` |
| IBM | MAJOR_RESISTANCE | REPLACED | 약 $264.61~$265.94 `BOLLINGER_MONTHLY` | 약 $247.87~$253.91 `BALANCE_BOX,BOLLINGER_WEEKLY` | `v3-balance-box:00979ee59c25c6db21f8` |
| MU | MAJOR_SUPPORT | ABSENT | omitted `BOLLINGER_WEEKLY` | omitted `-` | - |
| MU | MAJOR_RESISTANCE | OMITTED | 약 $1,020.52~$1,025.65 `BOLLINGER_MONTHLY` | omitted `BALANCE_BOX` | - |
| RXRX | MAJOR_SUPPORT | RETAINED | 약 $2.76~$2.78 `PIVOT_MONTHLY` | 약 $2.76~$2.78 `PIVOT_MONTHLY` | `v3-pivot:7837bce04b9dfeeda7de` |
| RXRX | MAJOR_RESISTANCE | RETAINED | 약 $3.78~$3.82 `PIVOT_MONTHLY` | 약 $3.78~$3.82 `PIVOT_MONTHLY` | `v3-pivot:4a36e6e212db329aff68`, `v3-pivot:81a2006e7780513174eb` |
| SKHY | MAJOR_SUPPORT | ABSENT | omitted `BALANCE_BOX,BOLLINGER_DAILY,PIVOT_DAILY` | omitted `BALANCE_BOX,BOLLINGER_DAILY,PIVOT_DAILY` | - |
| SKHY | MAJOR_RESISTANCE | REPLACED | 약 $173.32~$174.2 `BOLLINGER_DAILY` | 약 $167.04~$167.88 `PIVOT_DAILY` | `v3-pivot:49ca3e562c4a897872b9` |
| SNDK | MAJOR_SUPPORT | ABSENT | omitted `BOLLINGER_DAILY,PIVOT_DAILY` | omitted `-` | - |
| SNDK | MAJOR_RESISTANCE | ABSENT | omitted `BOLLINGER_WEEKLY` | omitted `-` | - |
| TSLA | MAJOR_SUPPORT | REPLACED | 약 $249.49~$250.76 `BOLLINGER_MONTHLY` | 약 $298.54~$300.88 `PIVOT_MONTHLY` | `v3-pivot:85830049edd0f527573f`, `v3-pivot:cb76749a86be60711b2b` |
| TSLA | MAJOR_RESISTANCE | RETAINED | 약 $366.78~$372.67 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | 약 $366.78~$372.67 `BOLLINGER_MONTHLY,PIVOT_MONTHLY` | `v3-pivot:b132d066eee1638e7a89` |
| TSM | MAJOR_SUPPORT | REPLACED | 약 $297~$298.5 `BOLLINGER_MONTHLY` | 약 $409.83~$411.9 `BALANCE_BOX` | `v3-balance-box:2daa61a6833b980c7f42` |
| TSM | MAJOR_RESISTANCE | OMITTED | 약 $482.55~$484.98 `BOLLINGER_MONTHLY` | omitted `-` | - |
| WRD | MAJOR_SUPPORT | REPLACED | 약 $5.64~$5.68 `PIVOT_WEEKLY` | 약 $5.16~$5.2 `PIVOT_WEEKLY` | `v3-pivot:6735055df971e623e884` |
| WRD | MAJOR_RESISTANCE | RETAINED | 약 $6.8~$6.84 `PIVOT_MONTHLY` | 약 $6.8~$6.84 `PIVOT_MONTHLY` | `v3-pivot:a18afb1b90363e93bb8f` |
| WULF | MAJOR_SUPPORT | ABSENT | omitted `BOLLINGER_MONTHLY` | omitted `PIVOT_WEEKLY` | - |
| WULF | MAJOR_RESISTANCE | ABSENT | omitted `PIVOT_MONTHLY` | omitted `PIVOT_MONTHLY` | - |

## Exact Renderer Blocks

### CORZ

Before:

```text
📐 현재 가격 구조
• 기준 종가: $17.54
• 가까운 지지: 약 $16.86~$17.3
• 가까운 저항: 약 $17.75~$18.08
• 주요 구조 지지: 약 $16.25~$16.34
• 주요 구조 저항: 약 $18.58~$18.68
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $17.54
• 가까운 지지: 약 $16.86~$17.3
• 가까운 저항: 약 $17.75~$18.08
• 주요 구조 지지: 약 $13.32~$13.6
• 주요 구조 저항: 약 $18.58~$18.68
```

### CRCL

Before:

```text
📐 현재 가격 구조
• 기준 종가: $94.22
• 가까운 지지: 약 $91.07~$91.53
• 가까운 저항: 약 $95.54~$97.94
• 주요 구조 지지: 약 $84.05~$85.6
• 주요 구조 저항: 약 $110.92~$111.48
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $94.22
• 가까운 지지: 약 $91.07~$91.53
• 가까운 저항: 약 $95.54~$97.94
• 주요 구조 지지: 약 $84.05~$85.6
• 주요 구조 저항: 약 $110.92~$111.48
```

### GOOGL

Before:

```text
📐 현재 가격 구조
• 기준 종가: $341.16
• 가까운 지지: 약 $329.4~$331.07
• 가까운 저항: 약 $349.88~$351.66
• 주요 구조 지지: 약 $267.08~$268.43
• 주요 구조 저항: 약 $424.82~$426.96
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $341.16
• 가까운 지지: 약 $329.4~$331.07
• 가까운 저항: 약 $349.88~$351.66
• 주요 구조 저항: 약 $359.84~$361.66
```

### HUT

Before:

```text
📐 현재 가격 구조
• 기준 종가: $86.99
• 가까운 지지: 약 $82.64~$83.06
• 가까운 저항: 약 $87.66~$89.42
• 주요 구조 지지: 약 $65.9~$66.24
• 주요 구조 저항: 약 $99.21~$99.72
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $86.99
• 가까운 지지: 약 $82.64~$83.06
• 가까운 저항: 약 $87.66~$89.42
• 주요 구조 지지: 약 $65.9~$66.24
```

### IBM

Before:

```text
📐 현재 가격 구조
• 기준 종가: $239.11
• 가까운 지지: 약 $229.92~$235.49
• 가까운 저항: 약 $240.19~$246.22
• 주요 구조 지지: 약 $209.46~$216.44
• 주요 구조 저항: 약 $264.61~$265.94
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $239.11
• 가까운 지지: 약 $229.92~$235.49
• 가까운 저항: 약 $240.19~$246.22
• 주요 구조 지지: 약 $209.46~$216.44
• 주요 구조 저항: 약 $247.87~$253.91
```

### MU

Before:

```text
📐 현재 가격 구조
• 기준 종가: $915.99
• 가까운 지지: 약 $851.82~$856.1
• 가까운 저항: 약 $946.42~$951.18
• 주요 구조 저항: 약 $1,020.52~$1,025.65
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $915.99
• 가까운 지지: 약 $851.82~$856.1
• 가까운 저항: 약 $946.42~$951.18
```

### RXRX

Before:

```text
📐 현재 가격 구조
• 기준 종가: $3.45
• 가까운 지지: 약 $3.3~$3.35
• 가까운 저항: 약 $3.57~$3.6
• 주요 구조 지지: 약 $2.76~$2.78
• 주요 구조 저항: 약 $3.78~$3.82
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $3.45
• 가까운 지지: 약 $3.3~$3.35
• 가까운 저항: 약 $3.57~$3.6
• 주요 구조 지지: 약 $2.76~$2.78
• 주요 구조 저항: 약 $3.78~$3.82
```

### SKHY

Before:

```text
📐 현재 가격 구조
• 기준 종가: $159.76
• 가까운 지지: 약 $151.11~$154.34
• 가까운 저항: 약 $162.24~$165.14
• 주요 구조 저항: 약 $173.32~$174.2
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $159.76
• 가까운 지지: 약 $151.11~$154.34
• 가까운 저항: 약 $162.24~$165.14
• 주요 구조 저항: 약 $167.04~$167.88
```

### SNDK

Before:

```text
[omitted]
```

After:

```text
[omitted]
```

### TSLA

Before:

```text
📐 현재 가격 구조
• 기준 종가: $354.65
• 가까운 지지: 약 $336.09~$339.08
• 가까운 저항: 약 $356.63~$365.37
• 주요 구조 지지: 약 $249.49~$250.76
• 주요 구조 저항: 약 $366.78~$372.67
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $354.65
• 가까운 지지: 약 $336.09~$339.08
• 가까운 저항: 약 $356.63~$365.37
• 주요 구조 지지: 약 $298.54~$300.88
• 주요 구조 저항: 약 $366.78~$372.67
```

### TSM

Before:

```text
📐 현재 가격 구조
• 기준 종가: $425.67
• 가까운 지지: 약 $413.45~$423.02
• 가까운 저항: 약 $451.23~$453.5
• 주요 구조 지지: 약 $297~$298.5
• 주요 구조 저항: 약 $482.55~$484.98
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $425.67
• 가까운 지지: 약 $413.45~$423.02
• 가까운 저항: 약 $451.23~$453.5
• 주요 구조 지지: 약 $409.83~$411.9
```

### WRD

Before:

```text
📐 현재 가격 구조
• 기준 종가: $6.04
• 가까운 저항: 약 $6.27~$6.31
• 주요 구조 지지: 약 $5.64~$5.68
• 주요 구조 저항: 약 $6.8~$6.84
```

After:

```text
📐 현재 가격 구조
• 기준 종가: $6.04
• 가까운 저항: 약 $6.27~$6.31
• 주요 구조 지지: 약 $5.16~$5.2
• 주요 구조 저항: 약 $6.8~$6.84
```

### WULF

Before:

```text
[omitted]
```

After:

```text
[omitted]
```
