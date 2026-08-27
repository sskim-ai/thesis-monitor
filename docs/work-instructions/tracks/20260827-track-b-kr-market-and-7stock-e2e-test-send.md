# Track B — KR Market + Full Monitored-Stock E2E Test Send

## Preconditions

Track A PASS.
Latest validated main includes the daily-coverage/proximity repair.

## Test scope

Send to dedicated test sink exactly once each:

```text
1 KR market digest
+
every current monitored KR stock message
```

Market digest must include:

```text
direction
breadth
aggregate flow
size/style
KOSPI strong/weak TOP3
KOSDAQ strong/weak TOP3
```

Each stock message must obey current Price Structure eligibility.

Preserve:

```text
canonical target daily 1200
actual provider-limited 1000 = PARTIAL_SAFE
LONG_HORIZON != 가까운
Fib only if safe
current structure != stored rules
no target/stop
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_MESSAGE_QUALITY = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
```

If any monitored KR ticker fails: STOP. Do not enable.
