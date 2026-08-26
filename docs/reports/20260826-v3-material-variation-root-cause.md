# Price Structure v3 Material Variation Root Cause

MATERIAL_VARIATION_ROOT_CAUSE = PASS

| Ticker | Runs | Selection frequency | Primary cause | Divergent | Shared | Full | Family | Safe | Omitted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000660 | 5 | AMBIGUOUS:v3-monthly-wave:851988f906e688b59a32,v3-monthly-wave:949d2543129ae313fb32 | EARLY_ANCHOR_ONLY_AMBIGUITY | W0 | W1,W2,W3,W4 | MATERIAL_VARIATION | PASS | 6 | 1 |
| 003690 | 5 | AMBIGUOUS:v3-monthly-wave:82ea749dd000fab0f777,v3-monthly-wave:404a3c16d90a06c338d6 | EARLY_ANCHOR_ONLY_AMBIGUITY | W0 | W1,W2,W3,W4,W5 | MATERIAL_VARIATION | PASS | 3 | 4 |
| 005490 | 5 | AMBIGUOUS:v3-monthly-wave:c0da8e1405731029d0ac,v3-monthly-wave:89501ed4e39f6f48cd42 | GRAND_CYCLE_ONLY_AMBIGUITY | W0 | W1,W2,W3,W4,W5 | MATERIAL_VARIATION | PASS | 3 | 4 |
| 005930 | 5 | AMBIGUOUS:v3-monthly-wave:eda6736373d240150600,v3-monthly-wave:bb348f112c05010eb607 | EARLY_ANCHOR_ONLY_AMBIGUITY | W0 | W1,W2,W3,W4 | MATERIAL_VARIATION | PASS | 5 | 2 |
| 010120 | 5 | AMBIGUOUS:v3-monthly-wave:76fabe2784f06269ac12,v3-monthly-wave:3977ec22920fcb2454a3,v3-monthly-wave:0438e1f2624d208762e1, AMBIGUOUS:v3-monthly-wave:c4069adb6e3c4fcc908d,v3-monthly-wave:76fabe2784f06269ac12 | EARLY_LEG_AMBIGUITY_ACTIVE_PHASE_SHARED | W0,W1,W2 | W3,W4,W5 | MATERIAL_VARIATION | PASS | 2 | 5 |
| TSLA | 5 | AMBIGUOUS:v3-monthly-wave:bc9fa73c5ea43a202ba4,v3-monthly-wave:55c80820ac35aade928e | TRUE_ACTIVE_STRUCTURE_CONFLICT | W0,W1,W2,W3,W4 | W5 | MATERIAL_VARIATION | FAIL | 0 | 7 |
| TSM | 5 | AMBIGUOUS:v3-monthly-wave:f97c043a5c3e54abc0a3,v3-monthly-wave:f52bc2fa7d1ce1430c7d | MID_WAVE_DEPENDENCY_CONFLICT | W3 | W0,W1,W2,W4,W5 | MATERIAL_VARIATION | PASS | 2 | 5 |
