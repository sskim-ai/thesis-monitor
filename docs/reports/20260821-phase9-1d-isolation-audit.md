# Phase 9.1D Isolation Audit

The launcher is reachable only from the existing terminal-delivery hook. It validates terminal sent
counts and the archived delivery receipt SHA, then starts `app.jobs.working_capital_shadow_canary`
with `start_new_session=True` and all standard streams detached. It never imports the Telegram
notifier.

| Boundary | Result |
| --- | --- |
| production success / canary success | PASS |
| production success / canary validation failure | production unchanged |
| deterministic production fallback / canary success | PASS |
| duplicate invocation | `DUPLICATE_SKIPPED` |
| no eligible context | terminal suppressed receipt |
| cash-flow canary coexistence | independent launcher and archive |
| production influence | 0 |
| Telegram / assessment / warning mutation | 0 / 0 / 0 |

The two canaries neither wait for nor consume one another. Any launcher exception is caught per
canary, so one failure does not prevent the other launch and cannot alter the AI-review job result.
