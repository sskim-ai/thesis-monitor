# Phase 8.2A KRX Market Preview

Date: 2026-08-18
Immutable provider session: 2026-08-14
Mode: archive-only
Telegram sends: 0

## BEFORE — Existing KR Market Context

한국 현물 지수와 market breadth가 backend packet에 없어 미국 지수, 반도체 가격, 원/달러, 유가, 야간선물을 전일 해외 맥락으로만 사용합니다. 한국 시장 전체 외국인·기관·개인 수급도 확인되지 않습니다.

## AFTER — KRX-Enhanced Archive Preview

### 한국 현물 시장

KOSPI는 6,977.94로 2.42% 상승했고, KOSDAQ은 864.65로 0.38% 상승했습니다.

KOSPI common-share breadth는 상승 575 / 하락 180 / 보합 49종목, 상승 비율 71.5%, 동일가중 수익률 1.30%입니다. 지수 상승과 함께 시장 참여도 넓었습니다.

KOSDAQ은 상승 866 / 하락 718 / 보합 144종목, 상승 비율 50.1%, 동일가중 수익률 0.53%로 지수 상승보다 참여 확산은 제한적이었습니다.

업종 가격 proxy에서는 코스피 200 경기소비재가 4.23%로 가장 강했고, 코스닥 150 헬스케어는 -0.89%였습니다. 이는 업종지수 가격 흐름이며 개별 기업 실적 확인이 아닙니다.

시장 전체 외국인·기관·개인 순매수는 승인된 KRX Open API에서 제공되지 않아 `Unknown`으로 유지합니다.

## Selection

Decision-material selected Facts:

- `market:cross-section:index:KOSPI`
- `market:breadth:kr:kospi:returns`

Numeric registry: 76/76 registered, unsupported 0, ready `true`.

Source attribution: 한국거래소 통계정보. This preview is not sent and does not change any stock thesis.
