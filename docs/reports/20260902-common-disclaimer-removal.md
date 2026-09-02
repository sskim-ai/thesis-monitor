# 2026-09-02 Common Disclaimer Removal

## Scope

The exact common line below was removed from the KR/US V2 production renderer and the legacy
decision-canary renderer:

`※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.`

The shadow-only research disclaimer remains because it is a different label on a non-production
artifact. Historical immutable reports were not rewritten.

## Proof

- Fresh run-51 production render: 14 messages, exact disclaimer occurrences `0`
- Immutable source artifact: 14 historical occurrences, retained as source evidence
- KR/US x BUY/HOLD/SELL renderer matrix: covered by focused parameterized tests
- Accepted-plan validation, order-language rejection, and decision ownership: unchanged
- Fresh production message quality: `PASS`
- Repeated substantive spans: `0`

`COMMON_DISCLAIMER_OCCURRENCE_AFTER_REPAIR = 0`

## Duplication Review

The accepted V2 block remains the first-class decision block. No investment fact or legacy body
was removed merely to shorten messages. The frozen 14-message replay found no repeated
substantive span, so no broader renderer redesign was justified in this track.
