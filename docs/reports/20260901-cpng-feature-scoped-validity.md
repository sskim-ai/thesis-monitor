# CPNG Feature-Scoped Validity

| TF | State | Safe | Blocked | V2 usable |
| --- | --- | --- | --- | --- |
| D | INVALID | 59 | 19 | False |
| W | INVALID | 51 | 27 | False |
| M | PARTIAL_SAFE | 60 | 0 | True |

The D/W 2023-06-05 raw rows remain preserved. Recent finite windows are computed only when their exact dependency starts after the bad date; recursive facts spanning it are absent. Aggregate: `PARTIAL_SAFE`.
