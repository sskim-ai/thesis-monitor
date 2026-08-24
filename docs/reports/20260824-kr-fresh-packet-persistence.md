# KR Fresh Packet Persistence

- Contract: `kr-production-packet-persistence-v1`
- Analysis complete: PASS, 7/7
- Supported market and packet schema: PASS
- Deterministic fallback available: PASS
- Production hard-error gate: PASS
- Shadow influence on persistence: none
- Packet: `2026-08-24-kr-run-36-51d4359299cd`
- Packet SHA-256: `c1f0b08d88bc708635edd03e0e8f47a25439839b3174a41414ba57266f44d58d`
- Persisted packet count: 1 in the isolated rehearsal data root

Eight packet-bound rehearsal intents were created and held: one digest plus seven stock messages.
All eight point to the packet, all retain deterministic fallback eligibility, and sent count is 0.
Duplicate intents 0; orphan intents 0. No production `NotificationDelivery` row was written.

The natural packet `2026-08-24-kr-run-36-b82af21dfde3` was not reused. It remains the immutable
identity of the 16:xx failure, while the fresh packet has new content and a distinct digest.

`KR_PACKET_DELIVERY_DRY_RUN = PASS`

`NATURAL_EXACTLY_ONCE_PROOF = NOT_APPLICABLE_TO_REHEARSAL`
