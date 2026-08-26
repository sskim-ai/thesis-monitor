# Price Structure v3 Long-History SR after 1200D

The repaired replay uses 1200 completed daily bars for every long-listed eligible subject while
retaining dedicated weekly/monthly histories. Ranking remains capped at 12 zones per timeframe;
the observed maximum is `12`. Existing grouping and confluence tolerances are unchanged.

```text
LONG_HISTORY_ZONE_EXPLOSION = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0
FAKE_HIGHER_TIMEFRAME_COVERAGE = 0
WEEKLY_600 = PARTIAL
MONTHLY_300 = PARTIAL
WEEKLY_600_PASS_SUBJECTS = 12
MONTHLY_300_PASS_SUBJECTS = 8
```
