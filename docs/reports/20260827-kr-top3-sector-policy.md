# KR TOP3 Sector Policy

Contract: `kr-sector-relative-ranking-v1`  
Selection owner: backend deterministic ranking  
Tie-break: return, then canonical sector name, then source ref  
User terms: `업종 상대 강세` / `업종 상대 약세`

| Market | Side | Rank | Sector | Return % | Source ref |
| --- | --- | --- | --- | --- | --- |
| KOSPI | strong | 1 | 전기/전자 | 2.62 | kiwoom:ka20003:KOSPI:013:2026-08-27 |
| KOSPI | strong | 2 | 금속 | 2.3 | kiwoom:ka20003:KOSPI:011:2026-08-27 |
| KOSPI | strong | 3 | 제조 | 2.04 | kiwoom:ka20003:KOSPI:027:2026-08-27 |
| KOSPI | weak | 1 | 유통 | -2.36 | kiwoom:ka20003:KOSPI:016:2026-08-27 |
| KOSPI | weak | 2 | 전기/가스 | -2.05 | kiwoom:ka20003:KOSPI:017:2026-08-27 |
| KOSPI | weak | 3 | 음식료/담배 | -1.56 | kiwoom:ka20003:KOSPI:005:2026-08-27 |
| KOSDAQ | strong | 1 | 금융 | 3.21 | kiwoom:ka20003:KOSDAQ:111:2026-08-27 |
| KOSDAQ | strong | 2 | 전기/전자 | 3.08 | kiwoom:ka20003:KOSDAQ:124:2026-08-27 |
| KOSDAQ | strong | 3 | 기계/장비 | 2.48 | kiwoom:ka20003:KOSDAQ:123:2026-08-27 |
| KOSDAQ | weak | 1 | 오락/문화 | -1.29 | kiwoom:ka20003:KOSDAQ:141:2026-08-27 |
| KOSDAQ | weak | 2 | 출판/매체복제 | -1.11 | kiwoom:ka20003:KOSDAQ:118:2026-08-27 |
| KOSDAQ | weak | 3 | 통신 | -0.82 | kiwoom:ka20003:KOSDAQ:128:2026-08-27 |

No AI sorting, stale carry-forward, or duplicate fill is permitted.
