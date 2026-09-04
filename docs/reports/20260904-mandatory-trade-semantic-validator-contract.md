# Mandatory-Trade Semantic Validator Contract

A rejection requires an action plus imperative, mandatory, automatic-execution, or order semantics. Explicit comparisons and negations remain analysis language, not executable instructions. The rule is deterministic and uses no classifier.

| Expected | Text | Matches | Result |
| --- | --- | --- | --- |
| ALLOW | 자동 매도보다 사업 성과 재점검이 우선이다. | none | PASS |
| ALLOW | 상단에서는 자동 매도보다 회복의 질을 평가한다. | none | PASS |
| ALLOW | 무조건 매도할 가격대로 보지는 않는다. | none | PASS |
| ALLOW | 기계적 매도 대신 Valuation 정당화를 확인한다. | none | PASS |
| ALLOW | 자동 축소가 아니라 사업 성과를 확인한다. | none | PASS |
| BLOCK | 반드시 매도해야 한다. | 반드시 매도 | PASS |
| BLOCK | 즉시 매도한다. | 즉시 매도 | PASS |
| BLOCK | 자동으로 매도한다. | 자동으로 매도 | PASS |
| BLOCK | 자동 매도한다. | 자동 매도한다 | PASS |
| BLOCK | 무조건 비중을 줄인다. | 무조건 비중을 줄인다 | PASS |
| BLOCK | 이 가격에서는 손절해야 한다. | 손절해야 | PASS |
| BLOCK | must sell immediately. | must sell | PASS |
| BLOCK | automatically reduce the position. | automatically reduce | PASS |
