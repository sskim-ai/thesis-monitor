# Track C — KR Dedicated Test Sink E2E Preflight

## Preconditions

Track A + Track B on same latest safe main.

## Test artifacts

Send to dedicated non-production sink only:

```text
1 KR market digest
3-5 representative KR stock messages
```

Representative stock set should cover available states:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT/BLOCKED if present
Fib-visible if present
stored-rule separation if present
```

## Hard safety

```text
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
```

## Market message must show

```text
size/style
KOSPI strong TOP3 / weak TOP3
KOSDAQ strong TOP3 / weak TOP3
```

## Stock messages

Validate Price Structure according to runtime eligibility.

Exact payload/format/provenance required.

If any material failure: STOP. Do not enable.
