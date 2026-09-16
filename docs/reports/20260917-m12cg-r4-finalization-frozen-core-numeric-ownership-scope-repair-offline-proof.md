# M12CG-R4 Finalization Frozen-Core Numeric Ownership Scope Repair

## Result

`M12CG_R4_FINALIZATION_SCOPE_REPAIR_OFFLINE_CLOSURE_PASS`

The accepted-plan validator now preserves exact numeric claims only when the integrated
runtime has independently validated the frozen Fundamental Core batch, matched the candidate
to that Core through the existing ownership gate, and retained the direct `CANDIDATE` field,
role, text, refs and composition without adjudication.

Standalone calls remain strict. Stage-2-authored, mutated, non-Core and
adjudication-authored numeric claims remain strict. The runtime permission is derived after
the existing gates and is not serialized into model input, output or persisted contracts.

## Implementation

- Work-instruction commit: `435cffa1630303f04e72ac2cabc13373d62155c8`
- Repair implementation: `0b13013feb1cf81b57b172c90167ce73cc3bd78b`
- Audit implementation: `9f8fb014b836918bf79029758e3abe5b48035aed`
- Required base: `5ea16d57ad50a1f7b44a31c11ae97471c30126bc`

Application files changed:

- `app/services/accepted_decision_v2_service.py`
- `app/services/accepted_decision_v2_runtime_service.py`
- `app/jobs/accepted_decision_v2_runtime.py`

The job change is minimal caller wiring: it loads the separately frozen Core batch and passes
it to the existing integrated owner. It does not establish a third acceptance authority.

## Offline Proof

- Available complete M12CE Stage-2 batches: 3/3 finalized
- Available Stage-2 subjects: 9/9 finalized
- GOOGL and HUT: newly finalized with byte-identical preacceptance plans
- Previously successful artifacts: 7/7 byte-identical
- Semantic changes to valid inputs: 0
- Raw/Core hash changes: 0
- Model-facing prompt/schema/catalog byte changes: 0/9
- F01-F20 boundary variants: 20/20 PASS
- Historical replay: 62 rows, 20 candidates, 7 batches preserved
- Immutable 010120 negative: preserved invalid
- Native D01-D14 regression: PASS
- Crash-window guarantee: at-least-once; a chunk may repeat after send and before cursor

This is an offline 9-subject proof, not a US14/KR8 or Full22 proof.

## Validation

- Focused: 232 passed, 1 skipped
- Full: 4142 passed, 63 skipped, 2 warnings
- Treasury: 79 passed
- Kiwoom: 70 passed
- Ruff: PASS
- `git diff --check`: PASS

## Safety

- External model calls / Full22 generations: 0 / 0
- Production sends / intents / DB writes: 0 / 0 / 0
- Main merge / deploy / remote push: 0 / 0 / 0
- Scheduler changes / Kiwoom live actions: 0 / 0

`new_full22_authorized=false`

`deployment_readiness=NO`
