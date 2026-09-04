# Track C — US Live Monitoring Coexistence + Pause/Resume Guard

Protected natural window starts around 2026-09-04 08:00 KST.

Preflight shared:
- signed-in Codex CLI/runtime
- CODEX_HOME/app-server/state DB
- model concurrency
- CPU/memory pressure
- locks/namespaces

If interference NONE:
continue concurrently.

If POSSIBLE/CONFIRMED/UNKNOWN:
pause model-consuming shadow work by 07:55 or next safe checkpoint.
Static editing/light deterministic tests may continue if harmless.

Resume only after authoritative US run:
model phase terminal
delivery terminal
shared runtime released.

Do not guess a resume clock time.
Do not modify/kill production scheduler.
