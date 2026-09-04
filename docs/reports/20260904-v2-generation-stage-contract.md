# 2026-09-04 V2 Generation Stage Contract

The persisted contract remains `accepted-v2-generation-stage-v1` and is now
generation-aware.

Every receipt binds:

- `packet_id`, market, business date, and run ID
- claim ID, owner, generation, and fencing token
- deterministic generation ID
- latest stage, stage history, terminal state, and completion time

Observed active stages include `started`, `context_ready`, `model_path_ready`,
`model_invoking`, `candidate_batch_created`, and `validating`. Terminal stages
include `accepted_artifact_created`, `interrupted`, `timed_out`, `failed`, and
safe suppression.

The writer refuses to append to an existing stage receipt whose generation
identity differs. Tests prove that another generation's stage history remains
untouched.

| Gate | Result |
|---|---|
| V2 generation stage persisted | PASS |
| Active child without candidate treated as failure | 0 |
| Cross-generation receipt acceptance | 0 |
| Cross-claim receipt acceptance | 0 |
