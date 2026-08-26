# TRACK B — KR Afternoon Natural Market Message Review
## 2026-08-26 completed Korean session
## Read-only production evidence only

## Scope

Do not repair code in this track.

Do not manually trigger the KR afternoon task.

Target:

```text
KR completed session = 2026-08-26
```

Verify:

```text
natural scheduler/run identity
packet/delivery/receipt exactly once
exact natural message
Kiwoom index/breadth
size/style
market participant flows
ka10066 pagination
ka10051↔ka10066 reconciliation
concentration gating
KRX cross-provider state
message quality
```

## B1. Natural run

Discover:

```text
scheduled task ID/name
configured schedule
natural start/end KST
producer SHA
run ID
target session
packet ID
delivery ID
receipt ID
```

If natural run did not occur:

```text
KR_AFTERNOON_NATURAL = NOT_YET_OCCURRED
```

and STOP.

No manual execution.

## B2. Exactly once

Collect:

```text
packet count
intent count
delivery count
receipt count
duplicate
orphan
unowned retry
attempt_count
last error
```

Hard:

```text
duplicate = 0
orphan = 0
unowned retry = 0
```

## B3. Exact message

Return byte-for-byte persisted natural message.

Compare:

```text
intended/persisted payload
delivery payload
receipt-linked payload
```

Hard:

```text
KR_EXACT_MESSAGE_PAYLOAD_MATCH = PASS
```

## B4. ka20001 canonical market/breadth

For both KOSPI and KOSDAQ:

```text
close
change
return_pct
advance
decline
unchanged
```

Backend may derive deterministically:

```text
advance share
decline share
A/D ratio
net advancers
```

No AI arithmetic.

External/web breadth is cross-check only.

Kiwoom ka20001 is canonical.

## B5. ka20003 size/style/sector

Collect same-session structured:

```text
KOSPI large
KOSPI mid
KOSPI small
other safe KOSDAQ/sector-size fields
sector leaders/laggards where structured
```

Do not call sector-index return sector breadth.

## B6. ka10051 aggregate flows

For KOSPI/KOSDAQ:

```text
foreign
institution
retail
```

Canonical scale:

```text
100M KRW
```

Store raw and normalized bn KRW.

## B7. ka10066 full pagination

For KOSPI and KOSDAQ:

```text
page count
row count
duplicate count
pagination complete
```

Canonical scale:

```text
1M KRW
```

Hard:

```text
pagination complete = true
duplicate = 0
```

## B8. Reconciliation

Per market and participant:

```text
ka10051 aggregate
vs
sum ka10066 full pagination
```

Use existing canonical tolerance.

Do not widen.

Report absolute/relative differences and status.

## B9. Concentration gate

Only if reconciliation passes:

```text
top 5 same-direction contributors
share of reconciled aggregate
```

If reconciliation fails:

```text
BLOCKED_RECONCILIATION
```

No concentration prose.

Re-test both markets today.

Do not inherit yesterday's result.

## B10. KRX cross-provider

If exact 2026-08-26 KRX data published:

compare safe comparable fields.

Else:

```text
PUBLICATION_PENDING
```

Do not inject stale KRX into the natural message.

## B11. Message interpretation

Audit whether message distinguishes:

```text
KOSPI
vs
KOSDAQ

breadth
vs
index

foreign/institution/retail flow
vs
fundamental thesis
```

Preferred hierarchy:

```text
1. KOSPI/KOSDAQ direction
2. breadth
3. foreign/institution/retail
4. size/style
5. secondary sector/macro
```

Hard:

```text
KR_MARKET_DIGEST_LOCAL_FIRST = PASS
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0
MATERIAL_INFORMATION_LOSS = 0
V3_PRICE_STRUCTURE_LEAK = 0
```

## B12. Required reports

Create:

```text
20260826-kr-afternoon-natural-run-identity.md
20260826-kr-afternoon-exactly-once.md
20260826-kr-afternoon-kiwoom-market-data.md
20260826-kr-afternoon-breadth.md
20260826-kr-afternoon-size-sector.md
20260826-kr-afternoon-market-flows.md
20260826-kr-afternoon-ka10066-pagination.md
20260826-kr-afternoon-flow-reconciliation.md
20260826-kr-afternoon-concentration-eligibility.md
20260826-kr-afternoon-krx-cross-provider.md
20260826-kr-afternoon-message-evidence-utilization.md
20260826-kr-afternoon-exact-message.md
20260826-kr-afternoon-message-quality.md
20260826-kr-afternoon-safety-parity.md
20260826-kr-afternoon-review-readiness.md
```

## B13. Stop / repair policy

If a material problem is found:

```text
report it
classify P0/P1/P2
STOP
```

Do not repair inside Track B.

Spawn a separate bounded KR repair instruction.

## B14. Completion state

Target:

```text
KR_AFTERNOON_NATURAL = LIVE_PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
NEXT_ACTION = NO_ACTION
```
