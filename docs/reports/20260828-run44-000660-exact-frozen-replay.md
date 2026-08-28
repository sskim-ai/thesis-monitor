# Run-44 000660 Exact Frozen Replay

- packet: `2026-08-28-kr-run-44-4606feed1396`
- eligibility: `ELIGIBLE_SR_ONLY`
- result: `PASS`
- renderer errors: `[]`
- fallback errors: `[]`

## Selected Plan

| State | Semantic | Fact ref | Display |
| --- | --- | --- | --- |
| SELECTED_REQUIRED | STRUCTURE_BASIS_CLOSE | structure-close:000660:2026-08-28 | 1653000.0 |
| SELECTED_AS_CONFLUENCE | NEAR_SUPPORT | v3-zone:4c35a2f22ca7bd1f9ad1 | 약 159.2만~160.6만원 |

## Omitted Plan

| State | Semantic | Fact ref | Display |
| --- | --- | --- | --- |
| OMITTED_BY_MATERIALITY | dynamic_bollinger_resistance | v3-zone:4b6cff0ad3bea3ef381d | 약 186.7만~187.7만원 |

## Validator Required Refs

```json
[
  "structure-close:000660:2026-08-28",
  "v3-zone:4c35a2f22ca7bd1f9ad1"
]
```

## Renderer Text

```text
📐 현재 가격 구조
• 가격 구조 기준 종가(정규장): 1,653,000원
• 가까운 지지: 약 159.2만~160.6만원 · 일봉 볼린저 중첩
```

The weekly resistance `v3-zone:4b6cff0ad3bea3ef381d` at about
`186.7만~187.7만원` is `OMITTED_BY_MATERIALITY`, so it is not a validator obligation.
`RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0`.
