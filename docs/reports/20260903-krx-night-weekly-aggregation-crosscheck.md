# KRX NIGHT Weekly Aggregation Cross-Check

The hypothesis requires KRX NIGHT BAS_DD 09/01, 09/02, and 09/03 for the same `A0169000`
contract. Only the first two rows are officially available at the cutoff.

Available-row aggregation is:

- Open: first row `1067.00`
- High: max `1072.45`
- Low: min `1031.30`
- Close: last row `1040.50`

Kiwoom weekly bar labeled 08/31 is `1067.00/1072.45/1020.25/1043.60`. Open and high already match;
low and close require the absent final constituent. The values are consistent with the hypothesis,
but substituting Kiwoom 09/02 for the missing official KRX row would violate source independence.

`WEEKLY_AGGREGATION_PARITY = INSUFFICIENT`.

Contract splice: `0`. DAY/NIGHT mixing: `0`.

