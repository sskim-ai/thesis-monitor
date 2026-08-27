# KR Pre-Enable Exact Test Message

전용 TEST sink가 구성되지 않아 외부 전송과 수신 확인을 수행하지 않았습니다. 아래 문안은 전송 전 production-equivalent 후보입니다.

```text
🤖 AI 보조 한국시장 마감 · KR Pilot 4/5

🎯 판단
KOSPI와 KOSDAQ의 지수 방향과 시장 폭이 엇갈려 국내 장을 하나의 방향으로 묶기 어렵습니다.

🔎 핵심 근거
외국인은 양 시장에서 순매수했습니다. 기관은 양 시장에서 순매수했습니다. 개인은 양 시장에서 순매도했습니다.

📊 시장 내부
규모별: KOSPI 대형 +1.66% · 중형 +0.22% · 소형 -0.13%; KOSDAQ100 +1.94% · MID300 +0.76% · SMALL +0.44%.
업종 상대 강세: KOSPI 전기·전자 +2.62% · KOSDAQ 금융 +3.21%. 업종 상대 약세: KOSPI 유통 -2.36% · KOSDAQ 오락·문화 -1.29%.

📌 다음 확인
• 양 시장의 상승·하락 종목 분포와 외국인·기관의 시장별 수급 방향이 함께 유지되는지 확인합니다.
```

`TEST_EXACT_PAYLOAD_MATCH = NOT_SENT`
