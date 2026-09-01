# US Market Message Proof

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY -0.30%
• QQQ +0.05%
• IWM -0.62%
• SOXX +0.48%
• RSP -0.59%

🔎 시장 내부
• 동일가중 S&P500은 하락해 시가총액가중 S&P500과 방향이 같았습니다.
• 반도체 SOXX가 SPY를 크게 웃돌아 반도체 상대강세가 두드러졌습니다.
• 업종 강세: 에너지 +2.04%
• 업종 약세: 커뮤니케이션 서비스 -1.35%

🌐 보조 시장환경
• 미국 10년물 실질금리는 상승했습니다.

📌 다음 확인
• 다음 완료 세션의 주요 지수·동일가중·업종 분산이 이어지는지 확인합니다.
```

- core index observations: all dated `2026-08-31`.
- SOXX/SPY relative spread: selected after passing the existing materiality rule.
- IWM/SPY relative spread: safely omitted at `-0.32pp`, below the existing `0.50pp` threshold.
- RSP is described as participation style, not broad advance/decline breadth.
- sector leader/laggard: XLE/XLC, exact payload-bound.
- runtime quality receipt: `us-morning-exact-payload-quality-v1` / `PASS` / errors `0` / payload `7dd1595687cd4e6e5821661a66a6a353385797575be29372a61d1df1763324a6`.
- `US_MARKET_MESSAGE_QUALITY = PASS`
