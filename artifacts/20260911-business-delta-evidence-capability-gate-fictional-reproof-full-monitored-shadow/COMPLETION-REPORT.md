# M12AI Failure Closeout

## Result

- Status: `BLOCKED`
- Implementation freeze: `13b86bf41eaf56da86a8213efb2b99449c4dd1bf`
- Fictional generation: `20260911-m12ai-fictional-20260911T052302Z-d8c24c42e4b4`
- Stop: `run-1 / stage1 / context-01`
- Planned calls: `12`
- Actual model calls: `1` (`gpt-5.6-sol`, `xhigh`)
- Wrapper retries: `0`
- Final fictional outputs: `0`
- Monitored-shadow calls: `0`

## Failing Contract

The transport completed successfully and all four Stage 1 rows passed the
structured-output schema. Three rows passed semantic validation. `FIC-FIN-02`
failed `business-delta-evidence-capability-v1` with:

`BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE`

The candidate selected `WEAKENED` and cited both a lower comparable-period cash
conversion fact and improved operating evidence. The capability classifier
correctly marked the typed cash-conversion comparison as eligible, but the
model-facing view did not preserve its `WEAKENED` direction hint. Only the
operating evidence's `STRENGTHENED` hint remained, so the post-model validator
rejected the otherwise grounded mixed-evidence judgment.

Root cause:

`ELIGIBLE_TYPED_CASH_CONVERSION_COMPARISON_DIRECTION_HINT_NOT_PROPAGATED_TO_CAPABILITY_VIEW`

This is the smallest failing contract. No candidate, prompt, builder,
validator, schema, or fixture was changed after the generation started.

## Gates

- Prior M12AH bundle integrity: `PASS`
- Preflight focused tests: `89 passed`
- Preflight full tests: `3456 passed, 2 warnings`
- Ruff: `PASS`
- Diff check: `PASS`
- Fictional schema rows: `4/4 PASS`
- Fictional semantic rows: `3/4 PASS`
- Capability violations: `1`
- Fictional hard gate: `BLOCKED`
- Monitored shadow: `NOT RUN`
- Fresh-real proof: `NOT_READY`
- Final main merge: `NOT_READY`
- Production readiness: `NOT_READY`

## Safety

- Provider source fetches: `0`
- Production DB mutations: `0`
- Monitoring registrations/stops: `0/0`
- Assessment or warning mutations: `0/0`
- Notification queue writes: `0`
- Production sends: `0`
- Scheduler mutations: `0`
- Main mutations/merges/deployments: `0/0/0`
- Automatic monitoring resume: `0`

The first sandboxed attempt stopped before spawning a model because DNS was
unavailable. Its receipt is retained under `pre-model-failures`; the successful
network attempt was the sole actual model call.

## Next Scope

`BUSINESS_DELTA_ELIGIBLE_DIRECTION_HINT_PROPAGATION_REVIEW`

Review only how verified typed comparison direction semantics are carried into
the capability view and how mixed eligible evidence is validated. A new frozen
generation is required after any repair; this stopped generation must not be
selectively resumed.
