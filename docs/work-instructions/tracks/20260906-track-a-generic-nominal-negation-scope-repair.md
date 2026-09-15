# Track A — Generic Nominal Negation Scope Repair

Repair only the generic clause-level defect:

ACTION TERM + NOMINAL PREDICATE + EXPLICIT NEGATION

Examples:
- 매수 신호가 아니다
- 매도 명령이 아니다
- 진입 조건이 아니다
- 매수의 근거가 아니다

Do not whitelist WULF or the exact source sentence.

Negation must be bounded to its clause.
A later actionable directive must still trigger the hard gate.
Double-negation/ambiguous scope fails closed.
