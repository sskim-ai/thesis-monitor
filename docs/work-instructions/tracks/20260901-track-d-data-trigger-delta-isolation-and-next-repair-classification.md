# Track D — Data-Trigger Delta Isolation + Next Repair Classification

Compare:
previous passing KR test/replay
vs
2026-09-01 natural live

Across:
- code/runtime SHA
- environment/process namespace
- provider/source data
- technical fingerprints
- evidence facts
- candidate inputs
- model runtime
- validator inputs

Classify primary cause:
LIVE_DATA_TRIGGER /
CODE_REGRESSION /
CONFIG_REGRESSION /
SERVICE_RUNTIME_FAILURE /
PROVIDER_RUNTIME_FAILURE /
SCHEDULER_OWNERSHIP_FAILURE /
MULTI_FACTOR /
OTHER

Optional isolated replay copy may confirm causality only after read-only proof.
Never mutate production.

Return one bounded NEXT_ACTION but do not perform repair.
