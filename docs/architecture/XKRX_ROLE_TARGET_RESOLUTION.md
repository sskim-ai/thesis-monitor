# XKRX Role-target Resolution

Contract: `xkrx-role-target-v1`

Observation eligibility is role-first: timestamp, role, canonical target,
completion, then provider access. Wall-clock XKRX session membership is evidence,
not a universal precondition.

## Roles

- `night_futures_production` and `night_futures_post_deadline_observer` reuse
  `night-futures-session-basis-v1` and the same expected NIGHT session resolver.
- `krx_next_morning_publication` targets the preceding completed XKRX session,
  including weekend and holiday mornings.
- `krx_same_day_publication` targets the wall-clock date only when it is an XKRX
  session and the 15:30 close has completed.

The exchange calendar traverses weekends, consecutive holidays, and special
closures. No date-string subtraction is used.

## Idempotency

Before a provider call, each job loads prior attempts for the canonical target.
The same role/target is observed once even across process restart. A terminal
target is not queried again. A nonterminal 08:45 NIGHT attempt may proceed to
the distinct 09:15 horizon role; pending KRX publication may proceed at a later
natural slot.

Structured reasons include `no_valid_role_target`, `target_not_completed`,
`target_already_observed`, and `target_already_terminal`. Existing readiness,
session pairing, provider, deadline, and schedules are unchanged.

