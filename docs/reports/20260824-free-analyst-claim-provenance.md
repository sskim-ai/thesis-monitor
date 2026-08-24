# Evidence-Locked Free Analyst Claim Provenance

Every rendered sentence maps to a structured item, support type, and smallest-sufficient evidence refs. This is a claim provenance map, not chain-of-thought.

## kr-193419-01-__DAILY_DIGEST_KR__

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 오늘은 방향성 예측보다 새 관측이 없다는 시점 경계를 지키는 것이 판단의 핵심입니다. | kr-193419-01-daily-digest-kr-temporal-boundary | BOUNDED_INFERENCE | evidence:core:01, evidence:risk:01 |
| 다음 공식 관측 전까지 오늘의 거시 방향은 확정하지 않습니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01 |

## kr-193419-02-000660

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 현재 자료에서는 재고가 원가 규모보다 더 빠르게 쌓인다는 신호가 뚜렷하지 않습니다. | kr-193419-02-000660-inventory-balance | BOUNDED_INFERENCE | evidence:business:01 |
| 이 재고 관계는 현재 투자 논리를 약화시키지는 않지만, HBM 실행과 수익성의 지속 확인을 대체하지 못합니다. | kr-193419-02-000660-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 다만 ASP와 제품 믹스의 영향이 남아 있어 이 관계만으로 최종 수요 개선을 단정하기 어렵습니다. | kr-193419-02-000660-inventory-boundary | ALTERNATIVE_INTERPRETATION | evidence:business:01 |
| 매우 높은 기대를 정당화하려면 재고 관계 하나보다 핵심 실행과 수익성의 지속 확인이 더 중요합니다. | kr-193419-02-000660-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| HBM 출하와 수율의 지속성이 다음 핵심 확인 사항입니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-03-003690

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 현재 판단을 가르는 것은 일반기업 FCF가 아니라 보험영업의 지속성과 자본 여력입니다. | kr-193419-03-003690-insurance-applicability | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 보험영업과 자본 여력이 확인되기 전에는 새로운 방향 전환도 성립하지 않습니다. | kr-193419-03-003690-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 거래 주체 흐름은 보험영업과 준비금 판단을 대신하지 않습니다. | kr-193419-03-003690-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 보험영업의 지속성과 자본 여력 확인이 남아 있습니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-04-005490

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 재고가 매출보다 빠르게 늘어난 관계는 재고 부담 점검의 우선순위가 높아졌음을 시사합니다. | kr-193419-04-005490-inventory-pressure | BOUNDED_INFERENCE | evidence:business:01 |
| 따라서 재고 관계는 철강 스프레드와 소재 현금 회수의 확인 필요성을 높이지만, 사이클 악화를 확정하지는 않습니다. | kr-193419-04-005490-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 철강 물량과 원재료 가격 변화가 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다. | kr-193419-04-005490-inventory-scale-alternative | ALTERNATIVE_INTERPRETATION | evidence:business:01 |
| 반대로 재고가 매출보다 빠르게 늘어난 점은 운전자본 부담 가능성을 열어 둡니다. | kr-193419-04-005490-inventory-risk-alternative | ALTERNATIVE_INTERPRETATION | evidence:business:01 |
| 철강 스프레드와 리튬 사업의 현금 회수 속도가 남은 질문입니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-05-005930

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 재고가 원가보다 빠르게 늘어난 관계는 재고 부담 점검의 우선순위가 높아졌음을 시사합니다. | kr-193419-05-005930-inventory-pressure | BOUNDED_INFERENCE | evidence:business:01 |
| 따라서 DS 재고 부담 가능성은 열려 있으며, HBM 채택과 마진의 다음 확인 전에는 구조적 개선을 확정하기 어렵습니다. | kr-193419-05-005930-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| ASP나 제품 믹스 변화가 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다. | kr-193419-05-005930-inventory-scale-alternative | ALTERNATIVE_INTERPRETATION | evidence:business:01 |
| 반대로 재고가 원가보다 빠르게 늘어난 점은 운전자본 부담 가능성을 열어 둡니다. | kr-193419-05-005930-inventory-risk-alternative | ALTERNATIVE_INTERPRETATION | evidence:business:01 |
| 높은 기대 아래에서는 재고 부담 가능성을 해소할 실적 근거가 추가로 확인돼야 합니다. | kr-193419-05-005930-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| HBM 고객 채택과 DS 마진의 지속 여부가 아직 핵심 변수입니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-06-010120

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 수주가 매출로 전환된 근거만으로 현금 회수까지 확인된 것은 아니어서, 다음 판단에는 정식 회수 근거가 필요합니다. | kr-193419-06-010120-order-cash-gap | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 수주 전환은 논리 유지 근거지만, 현금 회수 확인 전에는 기대 상향의 근거가 충분하지 않습니다. | kr-193419-06-010120-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 높은 기대를 추가로 정당화하려면 수주 규모보다 현금 회수까지 이어지는 근거가 필요합니다. | kr-193419-06-010120-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 외국인·기관의 엇갈린 흐름은 수주 전환을 확인하는 근거가 아닙니다. | kr-193419-06-010120-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 수주잔고의 매출 전환과 현금 회수 근거가 다음 점검 대상입니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-07-012450

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 사업 규모만으로 수주가 현금으로 전환됐다고 볼 수 없어, 인도 일정과 운전자본 회수 조건의 확인이 필요합니다. | kr-193419-07-012450-contract-cash-gap | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 수주잔고의 사업 규모와 실제 인도·회수는 분리해 확인해야 합니다. | kr-193419-07-012450-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 높은 기대를 추가로 정당화하려면 수주잔고보다 인도와 운전자본 회수의 확인이 필요합니다. | kr-193419-07-012450-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 기관 유입은 장기 수주 실행을 확인하는 대리 지표가 될 수 없습니다. | kr-193419-07-012450-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 대형 수주의 인도 일정과 운전자본 회수 조건이 남아 있습니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## kr-193419-08-086280

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 현재 사업 흐름과 선대 투자의 현금 전환은 별도 문제이므로, 운임·물량과 자산 효율이 함께 확인돼야 합니다. | kr-193419-08-086280-fleet-cash-gap | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 물류 사업 흐름과 선대 투자 회수는 별도 증거로 확인해야 합니다. | kr-193419-08-086280-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 높은 기대를 추가로 정당화하려면 물류 흐름과 자산 투자 회수가 함께 확인돼야 합니다. | kr-193419-08-086280-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 단기와 누적 주체가 다른 수급은 구조적 매수세로 단정하기 어렵습니다. | kr-193419-08-086280-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 운임과 물량, 자산 투자 효율의 동행 여부가 남아 있습니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## us-run26-wulf-rr-sensitive

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 현재 근거로는 HPC 실행과 현금 전환의 연결이 닫히지 않아, 가격 움직임만으로 전환 기대를 확인했다고 볼 수 없습니다. | us-run26-wulf-rr-sensitive-hpc-threshold | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 가격 경계와 HPC 사업 실행은 분리해 확인해야 하며, 현재 가격은 가동과 현금 전환을 증명하지 않습니다. | us-run26-wulf-rr-sensitive-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 투기적 기대를 정당화하려면 가격 반등보다 가동·매출·현금전환의 연결이 먼저 확인돼야 합니다. | us-run26-wulf-rr-sensitive-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 가격 경계와 사업 실행은 분리해 확인합니다. | us-run26-wulf-rr-sensitive-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 다음 공식 자료에서 가동·건설 전력, HPC lease 매출, EBITDA, OCF·CAPEX·FCF와 희석을 확인합니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## us-run28-crcl-expectation-valuation

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 단일 매출 근거만으로는 준비금 수익을 비이자 수익이 대체하는지와 FCF의 질을 확인할 수 없습니다. | us-run28-crcl-expectation-valuation-platform-quality-gap | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 현재 매출은 성장의 한 단면이지만, 수익원 전환과 FCF가 함께 확인되기 전에는 기대 검증이 끝나지 않습니다. | us-run28-crcl-expectation-valuation-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 투기적 기대를 정당화하려면 단일 매출보다 수익원 전환과 현금흐름의 질이 확인돼야 합니다. | us-run28-crcl-expectation-valuation-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 가격·거래 확인은 사업 기대가 실적으로 전환됐다는 증거가 아닙니다. | us-run28-crcl-expectation-valuation-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 다음 공식 자료에서 USDC 유통량·점유율, 비이자 수익, 수익배분, adjusted EBITDA와 FCF를 확인합니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## us-run32-googl

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 전년보다 줄어든 PPE 투자 후 FCF는 AI 투자 회수 확인의 중요성을 높이지만, 그 자체로 투자 실패를 뜻하지는 않습니다. | us-run32-googl-cloud-fcf | BOUNDED_INFERENCE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 AI 투자 부담은 Cloud 성장·마진과 현금 전환이 함께 확인될 때 투자 논리의 검증 근거가 됩니다. | us-run32-googl-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 높은 기대를 정당화하려면 AI 투자 확대가 Cloud 성장·마진과 현금 회수로 이어지는 확인이 필요합니다. | us-run32-googl-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 현재 가격·거래 흐름은 사업 변화의 확인보다 전술적 배경으로만 해석해야 합니다. | us-run32-googl-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 다음 공식 실적에서 Cloud 성장·마진, Search monetization, 투자, 현금 전환과 투자수익성을 확인합니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |

## us-run32-mu

| Final sentence | Analysis item | Support type | Evidence refs |
|---|---|---|---|
| 늘어난 PPE 투자 후 FCF는 현금 전환과 양립하지만, 메모리 사이클 전반의 지속성을 확정하지는 않습니다. | us-run32-mu-memory-fcf | BOUNDED_INFERENCE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 따라서 현재 FCF는 업사이클과 양립하지만, ASP·HBM 믹스와 투자 규율의 확인 없이 구조적 개선을 확정하기 어렵습니다. | us-run32-mu-thesis-implication | THESIS_LINKAGE | evidence:metadata:05, evidence:core:01, evidence:business:01, evidence:next_check:01 |
| 매우 높은 기대를 정당화하려면 확대된 현금흐름이 메모리 사이클 전반에서 지속되는지 확인해야 합니다. | us-run32-mu-expectation | EXPECTATION_VALUATION_LINK | evidence:metadata:05, evidence:core:01, evidence:next_check:01 |
| 확인 가격 위를 유지하지만 거래량은 최근 평균보다 약해 HBM 수요와 메모리 마진의 확인으로 볼 수 없습니다. | us-run32-mu-positioning | POSITIONING_SYNTHESIS | evidence:supply:01 |
| 다음 공식 실적에서 ASP·출하, HBM 믹스, gross margin, 투자와 현금 전환을 확인합니다. | next-check | UNCERTAINTY_BOUNDARY | evidence:core:01, evidence:next_check:01 |
