# KR Packet And Delivery Integrity

Contract: `packet-bound-delivery-intent-v1`.

For an active KR AI-assisted pilot, the implemented order is:

```text
analysis persisted with queue_notifications=false
-> packet status created/already_exists
-> returned packet path is_file
-> digest/stock intents queued with packet-bound provisional metadata
-> hold promotes provisional rows to held
```

The provisional state `packet_bound_pending_hold` is not selected by retry or fallback. A crash
after queuing is therefore non-deliverable and recoverable by the next producer attempt. A missing
packet, non-ready cohort, or packet write failure creates zero new delivery intents and returns
`packet_not_ready`.

Retry/fallback selection now validates packet file existence plus packet ID, market, and assessment
date. Packet-less metadata and raw pending rows fail closed. Normal AI/fallback retry limits,
receipts, message content, and exactly-once behavior are unchanged.

Tests cover packet failure, packet-before-intent ordering, provisional binding, valid held binding,
raw pending without packet, missing packet metadata, fallback zero-send, and normal trading-day
reuse.
