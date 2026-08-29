# Track C — Run-45 Integrated Replay + Test Sink + Readiness

Preconditions:
Track A contract resolved/source-limitation documented.
Track B deterministic validation tests PASS.

Replay the frozen run-45 packet read-only.

Require:
- primary/backup candidate validation safe
- all 13 stock candidates pass intended production contract
- Price Structure numerics unchanged
- market data unchanged except night-futures section only if Track A proves it should change

Then send 1 US market + all current US/foreign stock messages to the dedicated non-production test sink.

Verify exact payload, no duplicate/orphan, rejected AI never sent.

No production US morning rerun.
