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

The earlier literal-wire-only inventory is development evidence, not the final
REV11 gate. All other REV11 restrictions remain unchanged.
