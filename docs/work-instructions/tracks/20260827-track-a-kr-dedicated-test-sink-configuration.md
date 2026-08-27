# Track A — KR Dedicated Test Sink Configuration

## Objective

Configure exactly one non-production test sink through the existing secret/config mechanism.

Prove:

```text
test sink != production sink
test namespace != production namespace
no raw IDs/secrets in repo/reports
```

Hard:

```text
TEST_SINK_AVAILABLE = YES
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
SECRET_IN_REPO = 0
```

If this cannot be proven: STOP. Do not send.
