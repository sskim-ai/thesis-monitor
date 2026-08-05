# Local Runtime Data

This directory is the local source of truth for thesis-monitor runtime data.

- `thesis_monitor.sqlite3`: primary SQLite database.
- `theses/`: latest human-readable thesis snapshot per ticker.
- `history/`: append-style assessment history exported from the database.
- `runs/`: daily monitor run summaries.
- `kakao_tokens.json`: locally rotated Kakao refresh token when Kakao delivery is enabled.

Runtime files are intentionally ignored by Git. Back them up through the Mac mini backup system.
