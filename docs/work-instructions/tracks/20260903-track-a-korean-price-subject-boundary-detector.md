# Track A — Korean Price-Subject Boundary Detector

Replace raw substring matching for Korean 주가/종가 with:
- recognized technical subject expressions
- valid left lexical boundary
- Korean particle tolerance
- nearby technical action/context

Must not match:
수주가, 발주가, 신규수주가, 최종가격.

Must detect:
주가, 현재주가, 당일주가, 종가, 전일종가, 정규장종가
when paired with genuine technical semantics.

No 047810-specific exception.
