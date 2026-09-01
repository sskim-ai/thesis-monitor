# Technical Feature Numeric Parity

The packet-owned builder calls the existing `build_multi_timeframe_feature_packet` after validating
the same bars. No indicator formula, Price Structure rule, or decision calibration changed.

Exact equality and packet SHA parity passed for representative US/KR classes:

`CORZ`, `GOOGL`, `MU`, `TSLA`, `CPNG`, `000660`, `047810`.

`TECHNICAL_FEATURE_NUMERIC_PARITY = PASS`

`PRICE_STRUCTURE_NUMERIC_DIFF = 0`

`VALUATION_NUMERIC_DIFF = 0`
