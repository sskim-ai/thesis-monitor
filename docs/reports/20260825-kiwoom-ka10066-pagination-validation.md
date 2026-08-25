# ka10066 Pagination Validation

| Market | Pages | Rows | Complete | Duplicate normalized identities | Page-chain SHA-256 |
| --- | --- | --- | --- | --- | --- |
| KOSPI | 14 | 1316 | True | 0 | bc30ece8e04d2162d4343f53fae3e0e98e9818d2fe6becb5ab5f50653ab04fe2 |
| KOSDAQ | 19 | 1824 | True | 0 | 5b8028006c495a53804fa457c6e752ba5b5b03912be320b75f9922f98a48ec46 |

Continuation follows response `cont-yn` and `next-key` until terminal. Amount mode is
`amt_qty_tp=1`; the empirically verified scale is KRW 1 million per source unit. An incomplete
chain or duplicate KRX/NXT-normalized identity blocks all concentration derived from that market.
