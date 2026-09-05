# Fresh USKR22 GPT-5.6 Shadow

Date: 2026-09-05 KST

Status: shadow-only; no production mutation or delivery.

Fresh writer and reviewer outputs were generated only after model and contract preflights, using identical frozen US14/KR8 packets and no previous candidate text. Model: `gpt-5.6-sol` / `xhigh`; subjects: `22`. Writer SHA: `15294f7424853d722de0ddda3f8b848ae8dbe5ae805046a3fd30f01d55b800f0`; reviewer SHA: `86b70b8522303c42a41cf67aabd29612173b8817b4290e42ba45cd60c373b19a`.

| Ticker | Market | A | B | C | Reviewer | Findings | Eligible |
|---|---|---|---|---|---|---|---|
| CORZ | us | 0 | 0 | 0 | WARN | 1 | True |
| CPNG | us | 0 | 0 | 0 | PASS | 0 | True |
| CRCL | us | 0 | 0 | 0 | PASS | 0 | True |
| GOOGL | us | 0 | 0 | 0 | PASS | 0 | True |
| HUT | us | 0 | 0 | 0 | WARN | 1 | True |
| IBM | us | 0 | 0 | 0 | PASS | 0 | True |
| MU | us | 0 | 0 | 0 | PASS | 0 | True |
| RXRX | us | 0 | 0 | 0 | PASS | 0 | True |
| SKHY | us | 0 | 0 | 0 | PASS | 0 | True |
| SNDK | us | 0 | 0 | 0 | PASS | 0 | True |
| TSLA | us | 0 | 0 | 0 | PASS | 0 | True |
| TSM | us | 0 | 0 | 0 | PASS | 0 | True |
| WRD | us | 0 | 0 | 0 | PASS | 0 | True |
| WULF | us | 0 | 0 | 0 | PASS | 0 | True |
| 000660 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 003690 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 005490 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 005930 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 010120 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 012450 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 047810 | kr | 0 | 0 | 0 | PASS | 0 | True |
| 086280 | kr | 0 | 0 | 0 | PASS | 0 | True |

Residual advisory findings discovered only by the reviewer are not hidden or rewritten in this run. They remain bounded P1 inputs for the next production-policy repair:

| Ticker | Code | Confidence | Claims | Explanation |
|---|---|---|---|---|
| CORZ | MATERIAL_CONTRADICTION | HIGH | corz.invalidation | The evidence treats contract cancellation or major reduction and repeated completion failure as alternative invalidation conditions. The claim joins contract reduction with repeated completion failure, materially narrowing the source-owned condition. |
| HUT | MATERIAL_CONTRADICTION | HIGH | hut.invalidation | The evidence treats contract cancellation or major reduction and repeated project-completion failure as alternative invalidation conditions. The claim joins contract reduction with repeated completion failure, materially narrowing the source-owned condition. |
