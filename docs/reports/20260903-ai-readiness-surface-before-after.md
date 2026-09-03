# AI Readiness Surface Before and After

| Run-53 measure | Before | Repaired `STOCK_V2` |
| --- | ---: | ---: |
| Canonical facts | 626 | 626 |
| Total numeric entries | 2,057 | 2,057 |
| Consumer-included numeric entries | 2,057 | 1,987 |
| Nonconsumer numeric entries | 0 | 70 |
| Unsupported included entries | 2 | 0 |
| Ready | false | true |

The 70 excluded entries belong to the standalone market surface. Relevant market transmissions
remain in each stock catalog with explicit `STOCK_V2` ownership. The two failing night-reference
occurrences are preserved and classified outside the stock consumer surface.

