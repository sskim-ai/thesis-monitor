# ROIC and FCF Metric-Grounding Regression

| Run | Ticker | Prior errors | New target errors | Result |
| --- | --- | --- | --- | --- |
| a | GOOGL | mandatory_sell_language, mandatory_trade_language | none | PASS |
| a | 010120 | unsupported_metric_or_inference | none | PASS |
| a | 047810 | mandatory_sell_language, mandatory_trade_language | none | PASS |
| a | 086280 | mandatory_sell_language, mandatory_trade_language, unsupported_metric_or_inference | none | PASS |
| c | 005490 | unsupported_metric_or_inference | none | PASS |

Prior false-positive repair: `PASS`. Current ROIC/CCC/DSO/DPO values were not created.
