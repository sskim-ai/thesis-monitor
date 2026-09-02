# Night Daily Gap Baseline

Run-51 frozen reference date is `2026-09-01`; both products use the validated `2026-08-31` regular DAY close for daily gap and daily return.

| Product | DAY close | Night open | Night close | Gap | Return |
| --- | ---: | ---: | ---: | ---: | ---: |
| KOSPI200 | 1,067.85 | 1,067.00 | 1,064.50 | -0.08% | -0.31% |
| KOSDAQ150 | 1,440.10 | 1,440.00 | 1,432.80 | -0.01% | -0.51% |

The canonical model carries separate gap and return lineage fields whose baseline date and close are identical. Source provider point changes remain evidence, while the user values are deterministically recomputed from canonical open/close and the validated baseline.

`DAILY_GAP_BASELINE_INVENTED = 0`

`DAILY_GAP_AND_RETURN_USE_DIFFERENT_UNDISCLOSED_BASELINES = 0`
