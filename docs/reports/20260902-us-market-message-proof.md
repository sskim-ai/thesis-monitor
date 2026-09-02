# US Market Message Proof

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY -0.69%
• QQQ -1.27%
• IWM -1.14%
• SOXX -2.10%
• RSP -0.82%

🔎 시장 내부
• 동일가중 S&P500은 하락해 시가총액가중 S&P500과 방향이 같았습니다.
• 반도체 SOXX가 SPY를 크게 밑돌아 반도체 상대약세가 두드러졌습니다.
• 업종 강세: 에너지 +1.27%
• 업종 약세: 경기소비재 -1.72%

📌 다음 확인
• 다음 완료 세션의 주요 지수·동일가중·업종 분산이 이어지는지 확인합니다.
```

| Fact | Field | Value | Semantic |
| --- | --- | --- | --- |
| market:index:SPY | fields.return_pct | -0.687 | index_return_pct |
| market:index:QQQ | fields.return_pct | -1.2724 | index_return_pct |
| market:index:IWM | fields.return_pct | -1.1431 | index_return_pct |
| market:sector:SOXX | fields.return_pct | -2.0996 | sector_return_pct |
| market:style:RSP | fields.return_pct | -0.8205 | style_return_pct |
| market:index:SPY | fields.return_pct | -0.687 | index_return_pct |
| market:sector:SOXX | fields.return_pct | -2.0996 | sector_return_pct |
| market:index:SPY | fields.return_pct | -0.687 | index_return_pct |
| market:sector:XLE | fields.return_pct | 1.2664 | sector_return_pct |
| market:sector:XLY | fields.return_pct | -1.7154 | sector_return_pct |

- market evidence utilization: `PASS`
- phantom numeric errors: `0`
- outbound/archive/ledger SHA: `5f66d74ce7f7ce8198fecb7018fbe2baab90efdd35c56680865343e12dc19f41`
- exact payload: `PASS`
- `US_MARKET_MESSAGE_STATUS = PASS`
