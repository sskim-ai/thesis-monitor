# 2026-09-04 V2 Timeout Ownership Contract

## Decision

`SINGLE_AUTHORITATIVE_TIMEOUT_OWNER = PASS`

The `--timeout` value belongs to each signed-in Codex model invocation. It
covers that invocation and its bounded transport retries. It is not a hidden
outer wall-clock deadline for a multi-batch stock generation.

The outer caller waits for one of these conditions:

1. A claim-bound terminal receipt.
2. An authorized cancellation or process shutdown.
3. The command-owned model timeout.
4. A configured production deadline.
5. Lost claim or fencing ownership.

An active stage with no persisted candidate is not a failure. There is no
shorter `168` second timeout in the repository contract.

## Corrected implementation detail

An initial implementation incorrectly applied `1800` seconds to the complete
US multi-batch generation. It produced a correct `TIMED_OUT` terminal receipt
after `1799.37` seconds, but changed established timeout scope. Commit
`35028fe9a6fd48b1111e84addca161401cbc5fe4` corrected the scope to one timeout
per signed-in model invocation. The subsequent US generation ran for `2371.70`
seconds overall and completed all five model batches.

`OUTER_SHORTER_HIDDEN_TIMEOUT = 0`

`PREMATURE_CHILD_CTRL_C = 0`
