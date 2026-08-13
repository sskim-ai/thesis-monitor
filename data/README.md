# Local Runtime Data

This directory is the local source of truth for thesis-monitor runtime data.

- `thesis_monitor.sqlite3`: primary SQLite database.
- `theses/`: latest human-readable thesis snapshot per ticker.
- `history/`: append-style assessment history exported from the database.
- `runs/`: daily monitor run summaries.
- `ai_review/inbox/`: immutable backend-verified packets for scheduled Codex review.
- `ai_review/claims/`: expiring local leases used by primary and backup tasks.
- `ai_review/outbox/`: schema- and guardrail-validated AI review JSON.
- `ai_review/history/YYYY/MM/`: completed output and deterministic/AI comparison records.
- `kakao_tokens.json`: locally rotated Kakao refresh token when Kakao delivery is enabled.

Runtime files are intentionally ignored by Git. Back them up through the Mac mini backup system.
