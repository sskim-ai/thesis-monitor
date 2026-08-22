# XKRX Role-target Readiness

Instruction SHA: `932df17e137e029ea53fc2f01adc30a440141894`

Implementation SHA: `6da46cc779ff5385a2cf99fb689840f00e695e36`

The wall-clock precheck root cause is closed by `xkrx-role-target-v1`. Weekend,
holiday, consecutive-holiday, special-closure, same-day, night-production, night
observer, KRX 08:05, dedup, pending retry, and terminal suppression tests pass.

- focused role-target suite: `25 passed`
- full pytest: `1378 passed`, one external Starlette deprecation warning
- Ruff full repository: PASS
- `git diff --check`: PASS
- Investment and Chart Knowledge: unchanged/PASS
- Public Action `0.4.5`, operationId `20/20 unique`, schema `4`: PASS
- implementation GitHub Actions run `32544635210`: Test PASS, Lint PASS
- schedule/deadline/provider/session-basis changes: 0
- user-visible production diff: 0
- manual task/provider recreation/Telegram/DB/Pilot: 0

Open P0: 0. Open material P1: 0.

`XKRX_ROLE_TARGET_RESOLUTION_REPAIR = PASS`

`NIGHT_OBSERVER_ROLE_TARGET_REPAIR = DEPLOYED_PENDING_NATURAL`

`KRX_0805_ROLE_TARGET_REPAIR = DEPLOYED_PENDING_NATURAL`

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`
