# ka20001 Breadth Validation

`KR_INDEX_BREADTH = PASS`

| Market | Close | Return | Advancers | Decliners | Unchanged | Eligible | Listed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KOSPI | 6742.74 | +0.68% | 647 | 226 | 34 | 907 | 944 |
| KOSDAQ | 827.15 | +1.70% | 1186 | 466 | 74 | 1726 | 1824 |

Both composites matched their exact target-date `ka20009` row and `ka20003` composite identity.
Eligible count is rising + falling + unchanged and is not forced to listed count. Current-only data
outside the completed target session is rejected.
