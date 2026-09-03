# 2026-09-03 US Scheduler and Ownership

| Stage | Natural time KST | Result | Ownership |
| --- | --- | --- | --- |
| source monitor | 08:05:34-08:06:50 | run 53 success | one immutable packet |
| primary | 08:15:28-08:21:14 | no pending review packet | no claim |
| backup | 08:31:54-08:32:34 | no pending review packet | no claim |
| fallback dispatcher | 08:40:06-08:40:24 | sent 15/15 | deterministic delivery |

Packet cutoff was `2026-09-03T08:05:34.715535+09:00`. The packet failed AI
readiness before claim creation, so there is no claim ID, claim owner, or claim
time to report. Neither primary nor backup acquired the packet. The fallback
dispatcher delivered the immutable deterministic payload once.

- `MULTIPLE_US_PRODUCERS_OWNED_PACKET = 0`
- `US_UNOWNED_RETRY = 0`
- `US_PACKET_COHORT_MUTATED_AFTER_CUTOFF = 0`
- `MANUAL_SOURCE_OR_AI_TRIGGER = 0`

