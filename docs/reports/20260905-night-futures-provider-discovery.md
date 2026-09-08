# Night Futures Provider Discovery

`CURRENT_NIGHT_FUTURES_PROVIDER = KRX official fut_bydd_trd archive/history path`

`CURRENT_PROVIDER_SUPPORT = PARTIAL`

`NEW_EXTERNAL_DEPENDENCY_REQUIRED = NO`

Repository에는 KRX 공식 `fut_bydd_trd` 조회, raw receipt, 야간 OHLCV 정규화와 동일계약 D/W/M history가 이미 있다. Kiwoom OpenAPI+ probe는 KOSPI200 선물 discovery/realtime capability 일부만 문서화됐고 night-session final-close 의미는 아직 production-enabled가 아니다. 이번 작업은 network call이나 새 scraper를 추가하지 않았다.
