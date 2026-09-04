# Confirmation Validator Regression Matrix

| Fixture class | Text | Technical detected | Result |
| --- | --- | --- | --- |
| BUSINESS_LANGUAGE_MUST_PASS | USDC 점유율과 비이자성 수익 확대가 정상화 이익을 지지함. | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | HBM 출하와 고객 채택이 확대되고 가격과 제품구성 강세 및 현금창출이 유지되는 것 | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | 가격 결정력이 마진 방어를 지원함. | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | customer demand supports utilization. | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | pricing power supports margins. | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | supplier support improves execution. | False | PASS |
| BUSINESS_LANGUAGE_MUST_PASS | customer support helps close execution gaps. | False | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | 종가 돌파가 필요하다. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | 저항선 위로 안착해야 한다. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | 지지선 회복이 필요하다. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | 확인선 회복이 필요하다. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | 주가 돌파가 필요하다. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | close above resistance. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | breakout through confirmation. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | support-level retest. | True | PASS |
| PRICE_STRUCTURE_MUST_BLOCK | registered confirmation price recovery. | True | PASS |

Business fixture pass: `7`. Technical fixture block: `9`. Fresh-run false positives outside the original fixture set: `1` (`047810`).
