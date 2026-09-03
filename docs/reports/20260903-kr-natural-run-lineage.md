# 2026-09-03 KR Natural Run Lineage

## Conclusion

`AUTHORITATIVE_RUN_IDENTIFIED = PASS`

The authoritative source analysis is KR monitor run `54`. Three scheduled close invocations reused that same source run, while the only actual delivery came from the 16:50 packet through the 17:10 deterministic fallback.

- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Scheduler: `com.seungsoo.thesis-monitor.kr-close`
- Invocation: `python -m app.jobs.monitor_daily --market kr`
- Timezone: `Asia/Seoul`
- Primary packet: `2026-09-03-kr-run-54-f19bb379daa7`
- Delivered packet: `2026-09-03-kr-run-54-78ed269de3df`

## Timeline

| Role | Scheduled | Observed / completed | Analysis | Packet | Delivery |
|---|---|---|---|---|---|
| Primary | 16:05 | 16:05:05 / 16:06:33 | `fresh`, `success`, KR8 8/8 | `f19bb379daa7` | held, 0 sent |
| Backup | 16:20 | 16:20:01 / artifact 16:20:13 | `reuse`, `already_completed` | `b081eb8a0619` | held, no receipt |
| Late backup | 16:50 | 16:50:03 / artifact 16:50:14 | `reuse`, `already_completed` | `78ed269de3df` | held pending fallback |
| Fallback | 17:10 | dispatched 17:10:06 / receipt 17:10:18 | no new thesis analysis | `78ed269de3df` | sent 9/9 |

The operating repository reflog shows revision `5d5f336...` checked out from 11:57 KST onward, with no later checkout before the close run.

## Exactly Once

- Actual market messages: 1
- Actual stock messages: 8
- AI-assisted primary messages sent: 0
- Deterministic fallback messages sent: 9
- Duplicate deliveries found: 0
- V2 plus fallback double-send found: 0

`AUTHORITATIVE_RUN_ID = 54`

