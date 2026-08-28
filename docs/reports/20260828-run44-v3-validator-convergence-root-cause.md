# Run-44 V3 Validator Convergence Root Cause

The 16:05 and 16:20 KR close attempts rendered the V3-selected near support and its daily
Bollinger confluence for `000660`. A weekly dynamic resistance candidate remained available, but
the V3 materiality selector intentionally omitted it. The legacy fallback validator reconstructed
an obligation from candidate availability and raised `fallback_dynamic_resistance_not_rendered`.

The latest operating runtime already fixes this ownership mismatch. When a validated V3 section
exists, fallback validation trusts the selected V3 output and does not recreate omitted dynamic
obligations. Real V3 binding failures still fail closed, and the legacy policy remains active when
V3 is off. This task changed no runtime module.

`ROOT_CAUSE_RENDERER_VALIDATOR_OWNERSHIP_MISMATCH = PASS`
`LATEST_RUNTIME_ALREADY_FIXED = YES`
`RUNTIME_HOTFIX_REQUIRED = NO`
