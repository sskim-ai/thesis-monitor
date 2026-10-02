# REV11 Response Binding Clarification

User clarification received on 2026-09-28:

> 동결된 슬롯 안의 응답값 연결 허용

Before acquisition, freeze the selection rules, request slots, dependency graph,
source identities and maximum request budgets. After acquisition, response-owned
values may be bound only into those existing slots. Do not add or mutate a
descriptor after observing provider data.

The resolved wire request and its parent receipt identities must be recorded
before sending. SEC document selection and Kiwoom continuation keys are permitted
only through the existing bounded source owners. No broader discovery, budget
increase, fabricated completion or change to the REV10 analytical contracts is
authorized by this clarification.

Second user clarification, received on 2026-09-28:

> 기존 상한 내 수집 후 완전성 검증 허용

KR collection may use the existing request-local owner cap, within the accepted
maximum of 20, without asserting a guaranteed minimum page size. Preserve the
global configured capability of 50. After collection, prove consumer completeness;
insufficient consumed data or an unresolved continuation at the bounded limit is
SOURCE_PARTIAL and may not advance to AI. This is not permission to silently
truncate, raise caps, broaden queries or relabel partial data as complete.

The earlier literal-wire-only inventory is development evidence, not the final
REV11 gate. All other REV11 restrictions remain unchanged.
