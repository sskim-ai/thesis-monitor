# Dynamic vs Structural S/R Contract

| Layer | User label | Required provenance | Historical reaction required | Owner |
|---|---|---|---|---|
| Near | 가까운 지지/저항 | canonical selected zone | according to source family | backend |
| Major | 주요 구조 지지/저항 | confirmed price-anchor refs | yes | backend |
| Dynamic | 볼린저 지지/저항 | completed Bollinger observation | no | backend |
| Dynamic confluence | `<existing S/R> · <TF> 볼린저 중첩` | both canonical facts | structural line remains primary | backend |
| Fib | Fib/SR 보조 근거 | family consensus | n/a | backend |

`BOLLINGER_DYNAMIC_AS_MAJOR_STRUCTURAL = 0`. Indicator observation dates are never copied into
price-interaction fields. Untraded Bollinger projections may be dynamic references when material,
but may not become historical structure.
