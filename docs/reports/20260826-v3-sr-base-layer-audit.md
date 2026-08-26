# Price Structure v3 Deterministic SR Base-Layer Audit

- Instruction commit: `7267ca1d3e518d39986941bfda1d6447560db344`
- Implementation: `176f3e73eb097fac99f4038a8987b610954804cc`
- Immutable replay: `20` subjects; live calls `0`.

SR maps are built independently for monthly, weekly, and daily before optional Fib. All missing sides carry an explicit reason; fabricated fill is `0`.

| Classification | Count |
| --- | --- |
| AVAILABLE_LOCAL | 116 |
| INSUFFICIENT_HISTORY | 2 |
| NO_CONFIRMED_HISTORICAL_LEVEL | 2 |
