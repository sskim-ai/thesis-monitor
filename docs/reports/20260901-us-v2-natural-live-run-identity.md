# 2026-09-01 US V2 Natural Live Run Identity

- `RUN_ID`: `49`
- `PACKET_ID`: `2026-09-01-us-run-49-2d1bb6df1608`
- canonical US session: `2026-08-31`
- source monitor: `success`, `2026-09-01T08:05:34.939847+09:00` to `2026-09-01T08:06:48.494921+09:00`, `14/14`
- primary scheduled: `08:15 KST`; actual: `2026-09-01T08:16:49.034000+09:00` to `2026-09-01T08:27:56.163000+09:00`
- backup scheduled: `08:30 KST`; actual: `2026-09-01T08:30:49.043000+09:00` to `2026-09-01T08:41:13.579000+09:00`
- terminal packet claim owner: `codex-us-backup`
- dispatch: `2026-09-01T08:40:05.140617+09:00`
- delivery mode: `deterministic_fallback`
- job exit: source monitor succeeded; both V2 generators exited fail-closed; backup fallback sent successfully.

No production job, scheduler, retry, or send was manually invoked during this proof.
