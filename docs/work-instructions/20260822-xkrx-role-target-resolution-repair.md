# thesis-monitor — XKRX Role-Target Resolution Repair

## Metadata

- Workstream: `Bounded P1 shared scheduling/target repair`
- Title: `Role-Target Resolution for Weekend/Holiday Natural Observers`
- Instruction version: `1.0`
- Date: `2026-08-22 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `f5a956930c1fbc4cbc6c6dc053a1cf2e428d4000`
- Triggering natural evidence:
  - night-futures 08:45/09:15 observer skipped on Saturday
  - KRX 08:05 telemetry skipped on Saturday
- Known passing behavior:
  - night-futures expected-session basis logic PASS
  - Phase 8.5.4.2 NIGHT → preceding eligible DAY logic PASS
  - fail-closed safety PASS
- Current night-futures deadline:
  `DEADLINE_UNPROVEN`
- Deadline change in this task:
  `0`
- Observer times change in this task:
  `0`
- KRX user-visible integration:
  `0`
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260822-xkrx-role-target-resolution-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify latest safe main/operating
2. commit/push instruction docs-only
3. record exact instruction commit SHA
4. create implementation branch from latest safe main descendant containing instruction commit
5. if the parallel AI repair lands first, reconcile onto latest main before promotion
6. no force push / history rewrite
7. no silent instruction edits

Recommended branch:

`codex/xkrx-role-target-resolution-repair`

---

# 1. Problem statement

Two natural telemetry roles skipped on a Saturday before evaluating the actual role-specific target:

1. night-futures post-deadline observer
2. KRX next-morning 08:05 publication telemetry

The suspected bad control flow is:

```text
wall-clock local date
→ "is today an XKRX trading day?"
→ false
→ skip
```

This is incorrect for roles whose target can legitimately refer to:

- an overnight NIGHT session associated with the current observation morning
- the latest completed eligible XKRX trading session from the prior business day

The exact root cause must be verified from code/logs before repair.

---

# 2. Correct design principle

Scheduling eligibility must be role-first:

```text
observation timestamp
        ↓
observation role
        ↓
role-specific target resolver
        ↓
target session/date
        ↓
target eligibility/completion
        ↓
provider observation
```

Do not use wall-clock trading-day status as a universal precondition.

---

# 3. Hard exclusions

Do NOT:

- change `night-futures-session-basis-v1`
- change NIGHT BAS_DD semantics
- change XKRX preceding-eligible-DAY pairing
- change same instrument/contract/maturity matching
- change provider-change cross-check
- change 08:20 production night-futures deadline
- change 08:45/09:15 observer times
- change KRX 08:05/16:05 times
- change US primary/backup schedules
- change KR schedules
- integrate KRX user-visible
- query historical provider data manually to fake natural proof
- alter Telegram
- mutate DB/Pilot
- change Public Action/schema

---

# 4. Shared role-target contract

Implement/reuse a versioned resolver, suggested:

`xkrx-role-target-v1`

Conceptual input:

```text
observed_at_kst
role
xkrx_calendar
```

Conceptual output:

```text
role
target_kind
target_session_date
target_xkrx_business_date
target_completed
observation_eligible
skip_reason
calendar_evidence
```

Roles should be explicit.

At minimum:

- `night_futures_production`
- `night_futures_post_deadline_observer`
- `krx_next_morning_publication`
- `krx_same_day_publication`

Use existing names if present.

---

# 5. Role: night-futures production

This role already passed session-basis review.

Do not change semantics.

Use existing verified logic.

The new shared resolver must not cause a regression.

---

# 6. Role: night-futures post-deadline observer

At 08:45 / 09:15 KST:

derive the target NIGHT session using the **same verified session-basis function used by production**.

Do not independently infer:

- "today"
- "yesterday"
- Friday/Saturday

from string arithmetic.

The resolver must answer whether the expected NIGHT session is valid for observation even when the wall-clock date is Saturday/Sunday/holiday.

If the target session is valid and expected:
observer should run.

If there is genuinely no expected target:
skip with structured reason.

---

# 7. Role: KRX next-morning 08:05

This role should target the latest completed eligible XKRX trading session whose publication is expected to be checked next morning.

On a non-trading wall-clock morning, that may still be the prior eligible session.

Do not skip merely because `observed_at.date()` is not itself an XKRX trading day.

Derive:

```text
latest completed eligible XKRX session
→ publication target date
```

Then decide whether the 08:05 role should observe it.

---

# 8. Role: KRX same-day 16:05

Preserve current semantics:

- target same-day completed session when appropriate
- if market/session not completed, classify accordingly
- no weekend/holiday provider call when no valid same-day target exists

The shared resolver must not cause useless 16:05 weekend observations.

---

# 9. Structured skip reasons

Replace generic weekend/holiday skip with role-aware reasons, e.g.:

- `NO_VALID_ROLE_TARGET`
- `TARGET_NOT_COMPLETED`
- `TARGET_ALREADY_TERMINAL`
- `TARGET_ALREADY_OBSERVED`
- `NON_TRADING_WALLCLOCK_BUT_VALID_PRIOR_TARGET`
- `CALENDAR_UNAVAILABLE`

Use repo conventions.

The important requirement is auditability.

---

# 10. Weekend matrix

Mandatory tests for Saturday observation.

### Night observer
Verify the target using session-basis contract.

Do not hard-code expected BAS_DD in the test without deriving it from the canonical resolver.

Expected:
- valid overnight target → observer eligible
- no valid target → structured skip

### KRX 08:05
Expected:
- latest completed Friday-equivalent eligible session target remains observable
- wall-clock Saturday alone does not skip

---

# 11. Sunday matrix

Determine expected behavior from actual market/session contract.

Night observer:
- if no relevant expected NIGHT target, skip
- if contract says a target exists, observe

KRX 08:05:
- avoid repeatedly re-observing the same Friday target if Saturday already produced terminal evidence, unless policy explicitly requires it

Idempotency matters.

---

# 12. Monday / holiday matrix

Test:

- Monday after normal Friday
- Monday following holiday
- holiday morning with prior completed session
- day after holiday
- consecutive holidays
- XKRX special closure

Use XKRX calendar, not calendar-day subtraction.

---

# 13. Target deduplication

Role-target identity must avoid duplicate observations of the same target when:

- Saturday 08:05 already observed Friday
- Sunday scheduler fires again
- retry/restart occurs

Use a deterministic observation identity.

Do not suppress a required later observer if earlier evidence was non-terminal and policy requires another slot.

---

# 14. Night observer natural publication telemetry

Preserve existing telemetry contracts:

- attempt archive
- per-product readiness
- returned BAS_DD inventory
- raw refs/SHA
- first-observed interval

This repair only makes the scheduled observer reach the proper role target.

Do not modify readiness semantics.

---

# 15. KRX publication telemetry

Preserve:

`krx-publication-readiness-v1`

The repair should enable 08:05 to inspect the valid prior completed target on non-trading wall-clock mornings.

Do not change readiness classifications simply to generate data.

---

# 16. Provider-call control

Avoid unnecessary calls.

Before provider call, resolver may check:

- valid target exists
- target is not already terminal
- observation role requires this slot

Do not turn weekend scheduling into repeated duplicate calls.

Report provider-call bounds.

---

# 17. Natural-proof separation

Implementation may be promoted after deterministic tests.

But the current material P1 states become:

```text
NIGHT_OBSERVER_ROLE_TARGET_REPAIR =
DEPLOYED_PENDING_NATURAL

KRX_0805_ROLE_TARGET_REPAIR =
DEPLOYED_PENDING_NATURAL
```

Do not mark live PASS from synthetic tests.

The next naturally matching weekend/holiday execution is the proof.

---

# 18. No deadline inference

This repair restores observation.

It does not answer whether 08:20 is too early.

Keep:

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`

until actual post-deadline natural availability evidence exists.

---

# 19. Test matrix — resolver

Required:

- normal trading weekday
- Saturday
- Sunday
- exchange holiday
- day after holiday
- consecutive holidays
- same-day 16:05
- next-morning 08:05
- night production
- night 08:45
- night 09:15

For each report:
- role
- observed timestamp
- target
- eligibility
- skip reason

---

# 20. Test matrix — no session regression

Night futures:

- same-BAS_DD DAY/NIGHT bad pairing still rejected
- preceding eligible DAY
- weekend skip in DAY selection
- holiday skip
- same contract
- maturity/rollover
- provider conflict

Phase 8.5.4.2 behavior must remain PASS.

---

# 21. Test matrix — KRX

Required:

- Friday session, Saturday 08:05 observation
- Friday session, Sunday duplicate suppression
- Monday 08:05 targeting latest completed session as policy defines
- Saturday 16:05 no same-day target
- market holiday 16:05 no invalid target
- provider pending
- provider complete
- provider error

---

# 22. Test matrix — idempotency

- repeated scheduler invocation
- process restart
- same role/target
- observer #1 terminal success then observer #2 no-op
- observer #1 unavailable then observer #2 allowed

No duplicate logical observations.

---

# 23. Production isolation

Hard target:

```text
US/KR Telegram diff = 0
AI/fallback diff = 0
production receipt diff = 0
message count diff = 0
night production deadline diff = 0
observer schedule diff = 0
KRX schedule diff = 0
```

This is target-resolution/telemetry repair only.

---

# 24. Regression

Preserve:

- night-futures Phase 8.5.4.2
- night publication telemetry contracts
- KRX publication telemetry
- Phase 9.0E
- Phase 9.1A/B/C/D/E-preintegration
- investor-flow repair
- exactly-once
- Public Action/schema

---

# 25. Full validation

Required:

- focused role-target tests PASS
- weekend/holiday matrix PASS
- night session regression PASS
- KRX regression PASS
- idempotency PASS
- production isolation PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- exact final main SHA Actions PASS after promotion

---

# 26. Promotion gate

Promotion allowed when:

- P0 = 0
- implementation material P1 = 0
- role-target root cause closed
- schedule times unchanged
- production behavior unchanged
- session-basis logic unchanged
- CI PASS
- main ancestry clean

Protect current natural execution windows.

No manual observer run after promotion.

---

# 27. Required architecture doc

Create:

`docs/architecture/XKRX_ROLE_TARGET_RESOLUTION.md`

Document:

- role-first model
- target derivation
- weekend/holiday rules
- deduplication
- skip reasons
- relationship to session-basis logic
- relationship to KRX readiness

---

# 28. Required reports

Create:

1. `docs/reports/20260822-xkrx-role-target-root-cause.md`
2. `docs/reports/20260822-xkrx-role-target-matrix.md`
3. `docs/reports/20260822-night-observer-role-target-validation.md`
4. `docs/reports/20260822-krx-0805-role-target-validation.md`
5. `docs/reports/20260822-xkrx-role-target-idempotency.md`
6. `docs/reports/20260822-xkrx-role-target-production-isolation.md`
7. `docs/reports/20260822-xkrx-role-target-readiness.md`
8. `docs/reports/20260822-xkrx-role-target-natural-proof-plan.md`

Recommended JSON:

`docs/reports/20260822-xkrx-role-target-readiness.json`

---

# 29. Complete bundle

Create:

`20260822-xkrx-role-target-resolution-repair-bundle.zip`

Report ZIP SHA-256.

---

# 30. Completion report

Include:

## Repository
- instruction commit
- implementation
- final
- previous/final main
- operating

## Root cause
- exact wall-clock precheck path
- roles affected
- why synthetic tests missed it

## Resolver
- roles
- target derivation
- weekend/holiday matrix
- skip reasons

## No-regression
- Phase 8.5.4.2
- KRX readiness
- schedules
- provider-call bounds

## Validation
- tests
- full pytest/CI

## Safety
- manual task/provider recreation/Telegram/DB/Pilot = 0
- deadline unchanged
- observer times unchanged
- Production Assist OFF

Final state:

```text
XKRX_ROLE_TARGET_RESOLUTION_REPAIR = PASS/FAIL

NIGHT_OBSERVER_ROLE_TARGET_REPAIR =
DEPLOYED_PENDING_NATURAL / FAIL

KRX_0805_ROLE_TARGET_REPAIR =
DEPLOYED_PENDING_NATURAL / FAIL

DEADLINE_VERDICT = DEADLINE_UNPROVEN
```

---

# 31. Final philosophy

A scheduler's wall-clock date and an observation role's target date are not the same concept.

The correct question is not:

> Is Saturday a trading day?

It is:

> At this Saturday-morning observation role, what market/session target are we supposed to inspect?

The role-target resolver must answer that first.

Success is:

> Weekend/holiday observers evaluate the correct prior/overnight target, while same-day roles still skip when no valid target exists, with no change to production timing or session semantics.
