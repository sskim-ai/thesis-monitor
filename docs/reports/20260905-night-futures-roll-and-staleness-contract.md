# Night Futures Roll And Staleness Contract

Contract month는 필수다. 동일 instrument라도 contract month가 다르면 raw return 계산은 `cross_contract_raw_return_forbidden`으로 실패한다. Last trading date가 검증된 경우에만 days-to-expiry를 산출한다.

OPEN 표시는 현재 XKRX business-date night window와 quote session이 모두 일치할 때만 가능하다. 주말, 휴일, 종료 세션은 `최근`과 `종가`로 렌더링한다.
