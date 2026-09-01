# KR OHLC Integrity Regression

KR packet `2026-08-31-kr-run-48-a573c2a6f245` produced `{"FULL": 8, "INVALID": 0, "PARTIAL_SAFE": 0, "UNAVAILABLE": 0}` across 8 subjects. Both mandatory controls `000660` and `047810` are FULL. No KR-specific bypass or scheduler change was introduced. `KR_OHLC_INTEGRITY_REGRESSION = PASS`.
