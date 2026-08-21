# Phase 9.0E User-Visible Before/After

The sanitized [full fallback and AI preview artifact](20260821-phase9-0e-full-preview.json) contains
all 13 complete before/after fallback messages and all 14 rendered archive-only AI preview messages.

## Feature OFF

OFF selects `0/13` subjects and renders no cash-flow block. Twelve immutable run-30 fallback
messages are byte-identical. TSLA differs only by the already-promoted Phase 9.0D.1 removal of its
unsupported legacy FCF clause (`-31` characters), not by Phase 9.0E cash-flow exposure.

## SELECTIVE Fallback Additions

These are the complete new cash-flow blocks appended to the deterministic fallback on first safe
exposure:

| Ticker | Added block |
|---|---|
| CORZ | 2026 회계연도 상반기 누계 build-out 단계의 PPE 투자 후 잉여현금흐름은 $-723.29M입니다. 전년 비교기간보다 음수 폭이 커졌고 build-out 재투자는 가동·청구 전환과 자금조달을 함께 봅니다. |
| CRCL | 2026 회계연도 상반기 누계 준비금·플랫폼 사업의 PPE 투자 후 잉여현금흐름은 $528.12M입니다. 전년 비교기간보다 늘었고 준비금 수익과 비이자 플랫폼 수익의 현금전환을 함께 봅니다. |
| GOOGL | 2026 회계연도 상반기 누계 AI·Cloud 확장의 PPE 투자 후 잉여현금흐름은 $4.26B입니다. 전년 비교기간보다 줄었고 AI·Cloud 투자 회수는 Cloud 성장·마진과 함께 봅니다. |
| IBM | 2026 회계연도 상반기 누계 Software·Consulting 사업의 PPE 투자 후 잉여현금흐름은 $7.3B입니다. 전년 비교기간보다 늘었고 Software·Consulting 전환과 인수자금 부담을 함께 봅니다. |
| MU | 2026 회계연도 3분기 누계 메모리 증설의 PPE 투자 후 잉여현금흐름은 $26.1B입니다. 전년 비교기간보다 늘었고 ASP·제품 믹스·재고 사이클과 설비투자 시점을 함께 봅니다. |
| RXRX | 2026 회계연도 상반기 누계 연구개발 단계의 PPE 투자 후 잉여현금흐름은 $-187.35M입니다. 전년 비교기간보다 음수 폭이 줄었고 현금소진 근거로만 쓰며 보유현금 근거 없이 runway를 계산하지 않습니다. |
| SNDK | 2026 회계연도 연간 메모리 증설의 PPE 투자 후 잉여현금흐름은 $11.49B입니다. ASP·제품 믹스·재고 사이클과 설비투자 시점을 함께 봅니다. |
| TSLA | 2026 회계연도 상반기 누계 자동차 성장투자의 PPE 투자 후 잉여현금흐름은 $352M입니다. 전년 비교기간보다 줄었고 자동차 마진과 성장투자 회수를 함께 봅니다. |
| WULF | 2026 회계연도 상반기 누계 build-out 단계의 PPE 투자 후 잉여현금흐름은 $-1.53B입니다. 전년 비교기간보다 음수 폭이 커졌고 build-out 재투자는 가동·청구 전환과 자금조달을 함께 봅니다. |

Each block owns one exact number; OCF and CAPEX remain lineage rather than a numeric dump. HUT,
SKHY, TSM, and WRD add no block.

## Archive-Only AI Preview

The same nine blocks were appended to `business_earnings` in an archive-only copy of the run-30 AI
candidate and bound to the same nine FCF Fact IDs. Numeric binding was automatic `9`, manual `0`,
rejected `0`, unresolved `0`; semantic errors were `0`; runtime quality passed with repeated
sentences `0` and repeated template skeletons `0`.

To isolate Phase 9.0E from the reason run-30 originally fell back, the preview copy removes the
candidate's pre-existing generic numeric-summary and typed-valuation violations. The immutable
candidate/archive is not rewritten. This preview therefore proves cash-flow enrichment validity,
not that the original run-30 candidate itself would have passed unchanged.

SNDK resolves one cash-flow Unknown. TSLA suppresses four occurrences of its unsupported legacy
cash-flow claim before adding the canonical H1 YTD PPE-only FCF. No assessment status or valuation
context changes.
