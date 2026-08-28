# SNDK Eligibility Root Cause

## Result

`SNDK_ELIGIBILITY_ROOT_CAUSE = PASS`; state is `BLOCKED_SAFE`.

The frozen daily row dated `2026-08-27` reports close `1449.4`
below low `1456.0`. Canonical OHLC normalization rejects that row,
so the latest valid completed daily row is `2026-08-26` at `1499.37`. The US
rollout correctly denies a `2026-08-27` structure with `daily_history_as_of_mismatch`.

The same pattern appears independently for WULF (`daily_history_as_of_mismatch`),
which confirms a shared provider/data-basis issue rather than a ticker exception. No bypass was added.

## Prior Artifact

```text
📐 현재 가격 구조
• 기준 종가: $1,456.93
• 가까운 지지: 약 $1,412.98~$1,447.71
• 가까운 저항: 약 $1,481.27~$1,518.11
• 주요 구조 저항: 약 $1,527.66~$1,535.33
```

The prior artifact accepted a mutable value as the dated close. It is retained as evidence, not as a
safe basis for current Price Structure.
