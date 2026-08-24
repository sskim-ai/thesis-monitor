# KR 2026-08-24 Research Evidence

| Evidence | Type | Entity relation | Tier | Causal time | Statement |
|---|---|---|---|---|---|
| e-samsung-official-plan | CONFIRMED_EVENT_FACT | DIRECT_ISSUER | TIER_1_PRIMARY | True | 삼성전자는 8월 21일 2026년 주주환원 90조~110조원, 3분기 약 30조원 현금배당 계획, 임직원 보상용 약 15조원 자사주 매입을 공식 발표했고, 나머지 환원 방식과 규모는 2027년 1월 이사회에서 정하기로 했습니다. |
| e-samsung-reported-disappointment | REPORTED_INTERPRETATION | DIRECT_ISSUER | TIER_2_INDEPENDENT | True | 연합뉴스는 확정된 자사주 매입 세부안이 부족해 투자자들이 실망한 것으로 보인다는 애널리스트 해석을 전했습니다. |
| e-samsung-sk-policy-comparison | REPORTED_INTERPRETATION | SECTOR | TIER_2_INDEPENDENT | True | SBS는 삼성전자가 3분기 30조원 현금배당 외의 방식은 확정하지 않은 반면 SK하이닉스는 40조원 자사주를 전량 소각하기로 한 차이가 두 종목의 낙폭 차이를 설명한다는 해석을 전했습니다. |
| e-skhynix-official-plan | CONFIRMED_EVENT_FACT | DIRECT_ISSUER | TIER_1_PRIMARY | True | SK하이닉스는 8월 19일 40조원 규모 자사주 매입·전량 소각과 2025~2027년 누적 FCF의 50% 초과 주주환원 목표를 공식 발표했습니다. |
| e-market-close-breadth-flow | CONFIRMED_BREADTH_FACT | MARKET_STRUCTURE | TIER_2_INDEPENDENT | True | 코스피는 3.12% 내린 6,696.96으로 마감했지만 상승 종목 576개가 하락 종목 286개보다 많았고, 외국인과 기관은 합계 4.97조원을 순매도했으며 개인은 3.32조원을 순매수했습니다. |
| e-cross-market-divergence | CONFIRMED_BREADTH_FACT | MARKET_STRUCTURE | TIER_2_INDEPENDENT | True | 코스닥은 1.42% 상승했고 외국인은 3,255억원, 기관은 262억원을 순매수해 코스피 대형주 매도와 반대 흐름을 보였습니다. |
| e-security-returns | CONFIRMED_MARKET_FACT | SECTOR | TIER_2_INDEPENDENT | True | 8월 24일 삼성전자는 8.7% 하락한 257,000원, SK하이닉스는 3%대 하락으로 마감했습니다. |
| e-sk-sector-risk | REPORTED_INTERPRETATION | DIRECT_ISSUER | TIER_2_INDEPENDENT | True | 매일경제는 SK하이닉스 하락의 보조 배경으로 중국 메모리 증설 우려와 엔비디아 실적 발표 전 경계심을 제시했습니다. |
| e-us-prior-context | CONFIRMED_MARKET_FACT | MACRO | TIER_2_INDEPENDENT | True | 직전 미국 세션에서 S&P 500과 나스닥은 각각 0.4% 상승했지만 주간 기준으로는 기술주 약세와 장기금리 부담이 남았습니다. |
| e-nvidia-upcoming | CONFIRMED_EVENT_FACT | CUSTOMER | TIER_2_INDEPENDENT | False | 엔비디아의 8월 26일 실적 발표는 AI·반도체 수요 해석을 다시 확인할 다음 공식 일정입니다. |
| e-hbm-negative-scope | NEGATIVE_EVIDENCE | SECTOR | TIER_2_INDEPENDENT | True | 검색한 공식·주요 보도 범위에서는 장 마감 전 새 HBM 주문 축소, HBM 가격 하락 또는 고객 CAPEX 삭감 근거를 찾지 못했습니다. |
| e-flow-concentration-unknown | UNKNOWN | MARKET_STRUCTURE | TIER_2_INDEPENDENT | True | 시장 전체 순매도는 금액이고 패킷의 종목별 수급은 주식 수라서 삼성전자·SK하이닉스의 정확한 금액 집중도는 계산하지 않았습니다. |

## Boundary

The Samsung and SK hynix releases are confirmed issuer facts. Yonhap/SBS/Maeil interpretations remain reported interpretations. The exact two-stock share of market foreign selling is `Unknown`: packet stock flows are share counts while market flow evidence is KRW, so no 92% or substitute concentration was computed.
