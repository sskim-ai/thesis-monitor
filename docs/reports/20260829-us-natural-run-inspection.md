# 2026-08-29 US Natural Run Inspection

- Natural run: `FOUND`
- Monitor run ID: `45`
- Packet ID: `2026-08-29-us-run-45-0e9c491532df`
- Route delivered: `DETERMINISTIC_PRODUCTION_RENDERER`
- Deliveries: `14/14 sent` (1 market + 13 stocks)
- Market evidence parity: `PASS`
- Primary AI validation: `rejected` with `37` errors
- Backup AI validation: `rejected` with `4` errors
- Rejected AI sent: `false`

The primary AI full-stock candidate failed stock-level risk/reward, valuation, inventory-ownership, and numeric-occurrence checks. After rejecting one intermediate stale-claim output, the backup's final candidate failed three market-evidence-consumption checks and one framework allowlist check. These failures did not alter the market evidence and did not cause a duplicate delivery; the regular deterministic route had already completed all 14 sends.

## Exact Delivered Market Message

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY -0.23%
• QQQ -0.65%
• IWM -1.35%
• SOXX -3.20%
• RSP -0.34%

🔎 시장 내부
• 동일가중 S&P500은 하락해 시가총액가중 S&P500과 방향이 같았습니다.
• 업종 강세: 커뮤니케이션 서비스 +1.42%
• 업종 약세: 정보기술 -1.55%

📌 다음 확인
• 다음 완료 세션의 주요 지수·동일가중·업종 분산이 이어지는지 확인합니다.
```
