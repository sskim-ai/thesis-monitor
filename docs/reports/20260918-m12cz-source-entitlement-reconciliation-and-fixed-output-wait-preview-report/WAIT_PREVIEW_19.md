# M12CZ Fixed-Output WAIT Preview (19)

이 문서는 frozen M12CX 결과를 다시 계산하지 않은 document-only preview다. 원래 label, 점수, 이유, evidence ref, archetype/tier, range raw value는 변경하지 않았다. 역사적 range는 조건부 reference이며 적정가·목표가·자동 매수선이 아니다.

## 1. CORZ — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `5.6` : SELL `4.4` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 사업 전환의 진전은 인정하되 부채·희석·실행 위험이 완화되기 전까지 전체 판단은 보유, 신규 진입은 대기로 둔다.
- Holder 근거: 대규모 투자와 부채, 잠재 희석이 현금흐름과 주주가치에 미치는 영향을 재점검해야 한다.
- 실제 대기 조건: 사업 전환은 진전됐지만 높은 기대와 자본조달 부담이 실제 현금흐름 전환의 불확실성을 키운다.
- Frozen price: `17.17` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 청구 용량과 코로케이션 현금흐름의 지속 확대가 확인될 것 / 부채와 잠재 희석 부담이 안정될 것 / 내부통제 개선이 확인될 것
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 2. CPNG — MIXED_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.8` : SELL `5.2` / `LOW` / thesis `MIXED`
- 장기 정책 요약: 성장 기반은 남아 있으나 수익성과 현금흐름 정상화가 확인될 때까지 전체 판단은 보유, 신규 진입은 대기로 둔다.
- Holder 근거: 핵심 커머스 마진과 현금흐름 전환력이 약화돼 수익성 정상화 경로를 재점검해야 한다.
- 실제 대기 조건: 매출 성장 기반은 유지되지만 마진과 현금흐름 약화가 지속 가능한 이익 성장의 확신을 제한한다.
- Frozen price: `14.49` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 핵심 커머스 마진과 잉여현금흐름이 회복될 것 / 데이터 사고 관련 비용이 구조적 부담으로 고착되지 않을 것 / 신규 사업의 손실 축소가 지속될 것
- 미해결 입력: ARCHETYPE_UNRESOLVED / no supplied tactical candidate was safely selected
- 감사 주석(원래 label 외부): 근거 사용 범위 확인 중: 1.05억달러는 공식 management-defined FCF로 확인됐지만 frozen packet에는 filing/definition binding이 없었습니다.

## 3. CRCL — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.2` : SELL `5.8` / `LOW` / thesis `MIXED`
- 장기 정책 요약: 장기 성장 경로는 유효하지만 높은 기대와 금리 민감 수익구조의 실행 위험 때문에 전체 판단은 보유, 신규 진입은 대기로 둔다.
- Holder 근거: 장기 성장 경로가 남아 있고 보유 논리를 훼손할 실행 악화는 아직 확인되지 않았다.
- 실제 대기 조건: 고성장 기대가 큰 가운데 금리 민감 수익을 비이자 수익으로 대체하는 실행이 아직 핵심 미확인이다.
- Frozen price: `81.85` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: USDC 성장과 비이자 플랫폼·결제 수익 확대가 함께 확인될 것 / 금리 하락 환경에서도 정상화 이익과 현금흐름 방어가 확인될 것
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 4. GOOGL — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `BUY` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `6.5` : SELL `3.5` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: Search의 내구성과 Cloud·AI 성장성이 우세하지만 투자회수의 지속성은 추가 검증이 필요합니다.
- Holder 근거: Search와 Cloud·AI의 성장 기반이 유지되며 보유 논리를 훼손할 확인된 악화는 없습니다.
- 실제 대기 조건: 성장 논리는 유효하지만 높은 기대 속에서 Cloud·AI 투자회수의 지속성을 먼저 확인해야 합니다.
- Frozen price: `345.2` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 558.69192~600.38847 USD / HISTORICAL_TRAILING_PE_QUANTILE
- Tactical support: 표시하지 않음
- 재검토 조건: Cloud 성장과 마진의 지속성 확인 / AI 투자 대비 FCF와 ROIC 회복 확인 / Search 수익화 방어 확인
- 미해결 입력: no supplied tactical candidate was safely selected
- 문서 태그 보정: range가 현재가 위에 있다는 이유만으로 PRICE_WAIT를 만들지 않으며, frozen primary reason에 따라 BUSINESS_CONFIRMATION_WAIT를 사용합니다.

## 5. HUT — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.0` : SELL `6.0` / `LOW` / thesis `MIXED`
- 장기 정책 요약: AI·HPC 장기 계약의 잠재력과 높은 실행·자본 부담 위험이 맞서고 있습니다.
- Holder 근거: 대형 계약의 준공·가동·NOI 전환과 모회사 자본 부담을 계속 점검해야 합니다.
- 실제 대기 조건: 장기 가치 옵션은 크지만 계약이 안정적인 손익과 현금흐름으로 전환됐는지 확인이 필요합니다.
- Frozen price: `91.91` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 프로젝트 준공·가동과 계약 매출·NOI 인식 확인 / 프로젝트 파이낸싱을 통한 모회사 자본 부담 제한 확인 / 채굴 의존도 축소 확인
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 6. MU — PRICE_WAIT

- 원래 판단: Overall `BUY` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `7.5` : SELL `2.5` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: 사업 논리는 우호적이어서 전체 방향과 보유 판단은 긍정적으로 유지하되, 현재 가격이 확정된 펀더멘털 범위를 웃돌아 신규 매수만 대기한다.
- Holder 근거: 핵심 수요·계약 논리가 유지되고 조건부 사이클·투자 위험의 현실화는 확인되지 않았다.
- 실제 대기 조건: 현재 가격이 확정된 펀더멘털 범위 상단을 넘어 신규 진입의 안전마진이 부족하다.
- Frozen price: `933.31` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 247.893451~632.348662 USD / HISTORICAL_PB_QUANTILE
- Tactical support: 표시하지 않음
- 재검토 조건: 현재 가격이 확정된 펀더멘털 범위 안으로 들어올 때 / 이익과 장부가치 개선으로 펀더멘털 범위가 상향 확정될 때
- 미해결 입력: no supplied tactical candidate was safely selected

## 7. RXRX — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.0` : SELL `6.0` / `HIGH` / thesis `MIXED`
- 장기 정책 요약: 초기 플랫폼 검증은 긍정적이나 임상·경제성 미입증과 현금소진·희석 위험이 커 전체는 중립, 신규 매수는 대기, 기존 보유는 재검토한다.
- Holder 근거: 초기 검증 신호에도 임상 성공과 반복 가능한 경제성이 미입증이고 현금소진·희석 위험이 커 보유 논리를 재점검해야 한다.
- 실제 대기 조건: 플랫폼의 임상 성공과 반복 가능한 경제성이 아직 입증되지 않았고 현금소진·희석 위험도 크다.
- Frozen price: `3.22` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 주요 임상 후보의 진전과 긍정적 데이터가 확인될 때 / 현금소진과 희석 위험이 낮아지고 반복 가능한 파트너 경제성이 입증될 때
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 8. SKHY — VALUATION_INPUT_UNRESOLVED

- 원래 판단: Overall `BUY` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `7.0` : SELL `3.0` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: HBM 리더십과 수요 논리는 유효해 전체 방향과 보유 판단은 긍정적으로 유지하되, 주당 기준과 펀더멘털 옵션이 미해결이라 신규 매수만 대기한다.
- Holder 근거: HBM 기술·공급 리더십과 장기계약 논리가 유지되고 조건부 경쟁·투자 위험의 현실화는 확인되지 않았다.
- 실제 대기 조건: 주당 기준과 가치평가 계보가 충분히 검증되지 않아 정책상 펀더멘털 진입 판단을 확정할 수 없다.
- Frozen price: `177.46` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 현재 증권 기준의 주당 분모와 장부가치 계보가 검증될 때 / 정책상 펀더멘털 옵션이 해소되어 가격 비교가 가능해질 때
- 미해결 입력: STRUCTURAL_CYCLICAL_PRIMARY_PB_UNAVAILABLE / no supplied tactical candidate was safely selected

## 9. SNDK — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.0` : SELL `6.0` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 구조적 수요 기회와 사이클 지속성 위험이 공존해 전체 판단은 보유이며, 보유자는 논리를 재검토하고 신규 자금은 검증을 기다린다.
- Holder 근거: NAND 수요·재고와 계약 현금화의 지속성이 확인되지 않아 투자 논리의 불확실성을 재검토해야 한다.
- 실제 대기 조건: AI 데이터센터 수요 기대는 유효하지만 계약 현금화와 NAND 사이클의 지속성이 아직 검증되지 않았다.
- Frozen price: `1,529.99` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: RPO와 장기계약의 실제 매출·현금흐름 전환 확대를 확인한다. / NAND 수요·재고와 사이클 현금창출의 지속성을 확인한다.
- 미해결 입력: STRUCTURAL_CYCLICAL_PRIMARY_PB_UNAVAILABLE / no supplied tactical candidate was safely selected

## 10. TSM — VALUATION_INPUT_UNRESOLVED

- 원래 판단: Overall `HOLD` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `6.0` : SELL `4.0` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: 구조적 AI 수요와 첨단공정 경쟁력으로 논리는 유지되지만, 높은 기대와 해외 팹 비용 부담 때문에 전체 판단은 보유이고 신규 진입은 대기한다.
- Holder 근거: AI/HPC 수요와 첨단공정 경쟁력이 핵심 논리를 유지해 기존 보유는 가능하다.
- 실제 대기 조건: 높은 성장 기대가 반영된 가운데 해외 팹 비용의 마진 희석 위험이 남아 신규 자금은 실행 확인을 기다린다.
- Frozen price: `420.64` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: AI/HPC 성장과 첨단공정 마진이 높은 기대를 상회하는지 확인한다. / 해외 팹 비용에도 마진과 현금창출이 유지되는지 확인한다.
- 미해결 입력: STRUCTURAL_CYCLICAL_PRIMARY_PB_UNAVAILABLE / no supplied tactical candidate was safely selected

## 11. WRD — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.0` : SELL `6.0` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 유료 상용화 진전은 인정하지만 단위경제성과 손실 축소가 입증되지 않아 전체 판단은 보유, 신규는 대기, 기존 보유는 재점검이다.
- Holder 근거: 유료 이용과 매출은 성장하지만 큰 영업손실과 미입증 단위경제성이 병존해 보유 논리를 재점검한다.
- 실제 대기 조건: 상용화 진전만으로 이용률·마진·현금소진 경제성이 입증되지 않았고 영업손실도 커 실행 확인 전까지 대기한다.
- Frozen price: `5.66` (2026-09-16, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 차량당 이용률과 Robotaxi 매출의 동반 개선 / gross margin 개선과 operating loss 축소 및 현금소진 통제 확인
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 12. 000660 — MIXED_WAIT

- 원래 판단: Overall `HOLD` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `5.0` : SELL `5.0` / `LOW` / thesis `MIXED`
- 장기 정책 요약: HBM 수요와 재고 신호는 우호적이나 높은 기대 반영과 재무 품질 제약으로 확신은 낮다. 보유는 가능하지만 신규 진입은 가치 범위와의 괴리 축소를 기다린다.
- Holder 근거: HBM4 수요와 제한적인 재고 부담이 논리를 지지하며, 기대 수준이 높아도 실행 훼손은 아직 확인되지 않았다.
- 실제 대기 조건: 현재 가격은 확정된 기본가치 범위보다 높고 역사적 장부가치 배수도 높은 구간이어서 신규 진입의 안전마진이 부족하다.
- Frozen price: `1,744,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 626,251.883649~895,763.06431 KRW / HISTORICAL_PB_QUANTILE
- Tactical support: 1,397,000.0~1,420,000.0 KRW (별도 tactical support)
- 재검토 조건: 현재 가격과 장부가치 기반 적정 범위의 괴리가 축소될 때 / HBM4 실행이 현금창출과 자본효율 개선으로 확인될 때
- 미해결 입력: 없음
- 감사 주석(원래 label 외부): 근거 사용 범위 확인 중: 품질 flag는 방향 근거가 아니며 expectations-only Overall 수용은 Chat 정책 판단 대기입니다.

## 13. 003690 — VALUATION_INPUT_UNRESOLVED

- 원래 판단: Overall `HOLD` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `6.0` : SELL `4.0` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: 자본배분 개선과 절대가치 지지가 논리를 받치지만 재해손실과 ROE 지속성 확인이 필요하다. 보유는 가능하나 신규 진입은 기본가치 해소를 기다린다.
- Holder 근거: 현재 확인된 근거에는 보유 논리의 훼손이나 실행 악화가 나타나지 않았으며, 재해손실 위험은 아직 조건부다.
- 실제 대기 조건: 절대가치 지지는 있으나 안전하게 선택할 기본가치 범위가 확정되지 않아 신규 자금의 가격 비대칭을 판단하기 어렵다.
- Frozen price: `15,070.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 안전한 기본가치 산정 방법이 확보될 때 / 언더라이팅 수익성과 지속 가능한 ROE가 함께 확인될 때
- 미해결 입력: MATURE_VALUE_SAFE_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 14. 005490 — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `4.0` : SELL `6.0` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 회복 가능성은 남아 있으나 재고, 대규모 투자, 희석 위험이 실행 증명을 요구한다. 보유자는 재점검하고 신규 진입자는 FCF·ROIC와 주당가치 개선을 기다린다.
- Holder 근거: 재고 증가와 대규모 투자·희석 가능성이 현금창출 및 주당가치 개선을 제약할 수 있어 보유 논리의 실행 상태를 재점검해야 한다.
- 실제 대기 조건: 회복 경로는 존재하지만 재고 부담과 투자·희석 위험 때문에 현금수익성과 주당가치 개선이 확인되기 전에는 신규 진입 근거가 부족하다.
- Frozen price: `327,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 표시하지 않음
- 재검토 조건: 철강과 소재의 이익 개선이 FCF와 ROIC 상승으로 연결될 때 / 재고 부담이 완화되고 희석을 반영한 주당가치가 개선될 때
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE / no supplied tactical candidate was safely selected

## 15. 005930 — PRICE_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `5.0` : SELL `5.0` / `HIGH` / thesis `MIXED`
- 장기 정책 요약: HBM과 서버 메모리의 상방 경로는 유효하지만 높은 기대와 재고의 현금전환 위험이 맞서 전체 판단은 중립입니다.
- Holder 근거: 재고 증가가 원가 증가를 크게 앞서 현금전환 저하 여부를 점검해야 합니다.
- 실제 대기 조건: 현재 가격 위치에서는 펀더멘털 대비 안전여유가 부족해 신규 진입을 기다립니다.
- Frozen price: `253,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 121,910.325418~148,986.259705 KRW / HISTORICAL_PB_QUANTILE
- Tactical support: 228,000.0~233,000.0 KRW (별도 tactical support)
- 재검토 조건: 가격 부담이 완화될 때 / HBM 실행과 현금창출력의 동반 개선이 확인될 때
- 미해결 입력: 없음
- 감사 주석(원래 label 외부): 근거 사용 범위 확인 중: Holder REVIEW는 원래 label을 유지하되 sole working-capital ref의 status-use 권한은 REVIEW PENDING입니다.

## 16. 010120 — VALUATION_INPUT_UNRESOLVED

- 원래 판단: Overall `BUY` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `6.5` : SELL `3.5` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: 전력 인프라 수요와 수주 가시성이 방향성을 지지하며, 기존 보유는 가능하지만 신규 자금은 가격 기준 확정 전까지 대기합니다.
- Holder 근거: 수주 확대와 고부가 전력기기 믹스의 중기 성장 논리는 유지됩니다.
- 실제 대기 조건: 검증 가능한 펀더멘털 가격 범위가 확정되지 않아 신규 진입을 기다립니다.
- Frozen price: `202,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 184,494.532776~191,505.467224 KRW (별도 tactical support)
- 재검토 조건: 주당가치 입력이 검증되어 펀더멘털 범위가 산출될 때 / 수주 증가와 현금흐름 개선이 함께 확인될 때
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE

## 17. 012450 — VALUATION_INPUT_UNRESOLVED

- 원래 판단: Overall `BUY` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `7.0` : SELL `3.0` / `MEDIUM` / thesis `INTACT`
- 장기 정책 요약: 수주 가시성과 수출 수익성이 긍정적 방향을 지지하며, 기존 보유는 가능하지만 신규 자금은 가격 기준 확정 전까지 대기합니다.
- Holder 근거: 대규모 수주잔고와 고수익 수출 사업이 중기 투자 논리를 지지합니다.
- 실제 대기 조건: 검증 가능한 펀더멘털 가격 범위가 확정되지 않아 신규 진입을 기다립니다.
- Frozen price: `1,096,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 1,024,143.038736~1,073,856.961264 KRW (별도 tactical support)
- 재검토 조건: 주당가치 입력이 검증되어 펀더멘털 범위가 산출될 때 / 프로젝트 이행과 해외 자본배분의 건전성이 확인될 때
- 미해결 입력: PROFITABLE_GROWTH_PRIMARY_PE_UNAVAILABLE

## 18. 047810 — BUSINESS_CONFIRMATION_WAIT

- 원래 판단: Overall `HOLD` / Holder `REVIEW` / New Buyer `WAIT`
- 원래 균형·확신: BUY `5.2` : SELL `4.8` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 중장기 성장 경로와 수익성·현금화 위험이 공존하므로 전체 판단은 보유이며, 신규 진입은 실행 확인까지 대기하고 기존 보유자는 논리를 재점검한다.
- Holder 근거: 매출 성장에도 수익성이 저하됐고 높은 기대를 충족할 실행 검증이 남아 있어 보유 논리를 재점검해야 한다.
- 실제 대기 조건: 성장 경로는 유효하지만 마진 정상화와 성장의 현금화가 아직 검증되지 않아 신규 진입은 대기가 적절하다.
- Frozen price: `130,300.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 없음 (입력/방법 미확정)
- Tactical support: 120,500.0~126,500.0 KRW (별도 tactical support)
- 재검토 조건: 양산·인도 확대와 추가 수주가 확인될 때 / 영업이익률 정상화와 FCF 개선이 함께 확인될 때
- 미해결 입력: EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE

## 19. 086280 — PRICE_WAIT

- 원래 판단: Overall `HOLD` / Holder `HOLDABLE` / New Buyer `WAIT`
- 원래 균형·확신: BUY `5.1` : SELL `4.9` / `MEDIUM` / thesis `MIXED`
- 장기 정책 요약: 투자 회수와 고객 다변화 논리는 유지되지만 유가와 높은 실적 기대 부담이 공존한다. 전체 판단은 보유이며 신규 진입은 기본 범위 재진입까지 대기한다.
- Holder 근거: 현재 확인된 근거만으로 사업 논리의 훼손이나 구조적인 실행 악화가 확인되지는 않아 보유 가능하다.
- 실제 대기 조건: 현재 가격이 결정론적 기본 범위 상단을 웃돌아 신규 자금의 가격 비대칭이 충분하지 않다.
- Frozen price: `206,000.0` (2026-09-17, `canonical:price:current`)
- 조건부 역사 방법 reference: 149,319.110896~186,322.135071 KRW / HISTORICAL_PB_QUANTILE
- Tactical support: 176,000.0~180,000.0 KRW (별도 tactical support)
- 재검토 조건: 가격이 결정론적 기본 범위 안으로 복귀할 때 / 비계열 화주 확대와 FCF 기반 투자 회수가 확인될 때
- 미해결 입력: 없음
