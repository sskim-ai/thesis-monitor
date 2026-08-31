# 2026-08-31 KR V2 Natural Live Proof

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

## Executive result

The natural production pipeline collected all eight KR subjects, included new ticker 047810, and delivered exactly 1 market + 8 stock messages through the normal 17:10 deterministic fallback dispatcher. The V2 natural-live proof failed because two same-day active subjects lacked complete profiles, closing the global packet gate before candidate generation.

```text
KR_V2_NATURAL_LIVE = FAIL
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 1
OPEN_P2 = 0
NEXT_ACTION = BOUNDED_REPAIR
```

## P1 root cause

`same_day_new_subject_profile_gate_blocked_entire_v2_packet`: 047810 and CPNG were activated before the KR packet snapshots but had no complete company profile. The readiness contract counted 20 complete of 22 active, emitted `shadow_profile_gate_not_ready`, and caused both natural AI claims to return no eligible packet. No parser, market-data, delivery, identity-contamination, or duplicate-send P0 was observed.

## Gate summary

| Gate | Result |
| --- | --- |
| MANUAL_PRODUCTION_JOB_TRIGGER | 0 |
| MANUAL_PRODUCTION_SEND | 0 |
| PRODUCTION_STATE_MUTATION | 0 |
| KR_CANONICAL_SESSION_DATE | 2026-08-31 |
| KR_MONITORED_SUBJECT_COUNT | 8 |
| US_NEXT_LIVE_EXPECTED_STOCK_COUNT | 14 |
| KR_NEW_SUBJECT_047810 | FULLY_INCLUDED |
| US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY | NOT_READY_SAFE |
| KR_PRIMARY_ACTUAL_TIME | 2026-08-31T16:16:09.010+09:00 |
| KR_BACKUP_ACTUAL_TIME | 2026-08-31T16:57:11.283+09:00 |
| KR_PACKET_CLAIM_TIME | NOT_CLAIMED |
| KR_DISPATCHER_ACTUAL_TIME | 2026-08-31T17:10:07.170731+09:00 |
| KR_FIRST_DELIVERY_TIME | 2026-08-31T17:10:09.430568+09:00 |
| KR_LAST_DELIVERY_TIME | 2026-08-31T17:10:19.733510+09:00 |
| KR_DELIVERY_TIMING | NORMAL_1710_DISPATCH |
| KR_MARKET_DATA_COLLECTION | PASS |
| KR_INVESTOR_FLOW_COLLECTION | PASS |
| KR_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN | 0 |
| KR_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE | 0 |
| KR_RAW_CANDIDATE_VISIBLE | 0 |
| KR_ACCEPTED_READY_COUNT | 0 |
| KR_NOT_READY_COUNT | 8 |
| KR_ACCEPTED_BUY_COUNT | 0 |
| KR_ACCEPTED_HOLD_COUNT | 0 |
| KR_ACCEPTED_SELL_COUNT | 0 |
| KR_DECISION_BLOCK_VISIBLE_COUNT | 0 |
| KR_003690_CHANGE_CONDITION_WORDING | PASS |
| KR_PRICE_STRUCTURE_CONTRACT | PASS |
| KR_VALUATION_CONTRACT | PASS |
| KR_EXPECTED_STOCK_MESSAGE_COUNT | 8 |
| KR_EXPECTED_PRODUCTION_MESSAGE_COUNT | 9 |
| KR_SENT_PRODUCTION_MESSAGE_COUNT | 9 |
| KR_RECEIVED_PRODUCTION_MESSAGE_COUNT | 9 |
| KR_LIVE_EXACT_PAYLOAD | PASS |
| KR_EXACTLY_ONCE_DELIVERY | PASS |
| KR_DUPLICATE | 0 |
| KR_ORPHAN | 0 |
| KR_UNOWNED_RETRY | 0 |
| KR_EMPTY_VISIBLE_SECTION_COUNT | 0 |
| KR_V2_MESSAGE_QUALITY | FAIL |
| OPEN_P0 | 0 |
| OPEN_MATERIAL_P1 | 1 |
| OPEN_P2 | 0 |
| KR_V2_NATURAL_LIVE | FAIL |
| NEXT_ACTION | BOUNDED_REPAIR |

## Bounded repair

Complete normal onboarding/profile readiness for 047810 and CPNG, then prove packet eligibility without ticker exceptions. Re-run no production task manually. The next proof should be the next natural US cycle with 14 subjects, followed by a natural KR proof if needed.
