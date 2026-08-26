# 2026-08-26 US Fallback Ownership Timeline

| Time KST | Event | Owner / state |
|---|---|---|
| 08:06:07 | Monitor run 39 starts | natural monitor |
| 08:07:06 | Monitor completes 13/13 | run 39 complete |
| 08:20:05 | Current packet persisted | run-39 packet ready |
| 08:20:43 | Primary starts | incorrectly owns stale run-37 before repair |
| 08:40:05 | Fallback deadline | fallback atomically owns 14 intents |
| 08:42:13 | Backup current candidate validates | too late to replace fallback |
| 08:42:31 | Backup terminal activity | current AI output archived, no duplicate delivery |

The repair separates packet readiness delay from inference latency. It prevents old-packet budget consumption but does not lengthen the fallback window.

```text
WAIT_CURRENT_PACKET_PATH = PASS
PRIMARY_BACKUP_OWNERSHIP = PASS
FALLBACK_DEADLINE_SAFETY = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```
