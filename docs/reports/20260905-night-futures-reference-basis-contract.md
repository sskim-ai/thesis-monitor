# Night Futures Reference Basis Contract

화면 header 비교는 `1052.5` 기준 `41.40` / `3.93%`이지만 source가 기준의 경제적 의미를 직접 소유하지 않아 `UNKNOWN`이다. 전 야간 종가 비교는 `1049.05` 기준 `44.85` / `4.28%`이며 `PRIOR_NIGHT_CLOSE`로 명시된다.

서로 다른 reference type은 숫자가 달라도 conflict가 아니다. 산술 일치만으로 UNKNOWN을 official base나 regular close로 승격하지 않는다.
