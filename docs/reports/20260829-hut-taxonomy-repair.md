# HUT Taxonomy Repair

- Date: `2026-08-29 KST`
- Contract: `decision-calibration-p1-repair-v1`
- Implementation SHA: `930952132077e8403bcec1a7e2c52d5732d8521a`
- Production canary: `OFF`
- Production recipient sends/intents: `0 / 0`

- Final: `HOLD / OPTIONALITY_OFFSETS_DOWNSIDE / LOW / UNFAVORABLE`
- Decisive reason: 계약형 AI/HPC 인프라 전환은 상당한 장기 선택권을 제공하지만, 높은 기대와 프리미엄 가치평가에 비해 실제 매출과 마진으로의 전환은 입증되지 않았다. 이는 BUY 비대칭성을 막지만 선택권보다 하방이 우세하다고 확정하기에도 부족해 HOLD가 적절하다. (`decision-evidence:4cfce0c1d1d7f61e130c`, `decision-evidence:4c28d1cc7a794cc4171c`, `canonical:valuation:current`, `decision-evidence:af3bdb852dc69e1ac700`, `decision-evidence:cb5b65968e8b5e6f42de`)
- Why not BUY: 높은 기대와 프리미엄 가치평가에 비해 실제 매출과 마진 전환이 확인되지 않아 현재의 장기 상방이 충분한 비대칭성을 제공한다고 보기 어렵다. (`decision-evidence:4c28d1cc7a794cc4171c`, `canonical:valuation:current`, `decision-evidence:af3bdb852dc69e1ac700`, `decision-evidence:cb5b65968e8b5e6f42de`)
- Why not SELL: 계약형 인프라 파이프라인과 AI 데이터센터 수요가 여전히 큰 장기 선택권과 명확한 가치 실현 경로를 제공하므로 실행 위험만으로 하방 우위를 확정할 수 없다. (`decision-evidence:4cfce0c1d1d7f61e130c`, `decision-evidence:fe783c093a24882e06a6`, `decision-evidence:8b040f8545884d2f40f7`)
- `HUT_DECISION_TAXONOMY = PASS`
