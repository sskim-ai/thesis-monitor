# Track B — US Price Structure Full-Universe Test Sink

Precondition: Track A PASS.

Send one test message for EVERY current monitored US/foreign stock to the dedicated non-production sink.

Use the production-selected route per ticker.

Verify:
- exact payload
- company header
- eligibility behavior
- SR/Fib visibility
- current-vs-stored ownership
- no target/stop
- no truncation
- exactly once

Any material ticker failure blocks enablement.
