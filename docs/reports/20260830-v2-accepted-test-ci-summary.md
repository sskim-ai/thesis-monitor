# V2 Accepted Ownership Test and CI Summary

Date KST: `2026-08-30`

## Local Validation

| Check | Result |
|---|---|
| Focused accepted ownership, script, report, persistent-state suite | `32 passed` |
| Full pytest | `1942 passed, 1 deprecation warning` |
| Ruff | `PASS` |
| git diff --check | `PASS` |
| Investment Knowledge canonical/runtime SHA | `dc747fff...c312 / identical` |
| Chart Knowledge canonical/runtime SHA | `beee6455...19b / identical` |
| Public Action | `0.4.5 unchanged` |
| operationId | `20/20 unique` |

## Exact-SHA Actions

Evidence commit: `fda9909660b837cabc6ce0ad2fb278b5e21c3a6b`

GitHub Actions run: `33295943901`

Workflow/job: `test / pytest`

Result: `PASS`; both `Test` and `Lint` completed successfully.

The final documentation-only commit must receive the same exact-SHA workflow result before main
promotion. No production migration, recipient send, task mutation, DB mutation, or V1 canary state
change is authorized by this summary.
