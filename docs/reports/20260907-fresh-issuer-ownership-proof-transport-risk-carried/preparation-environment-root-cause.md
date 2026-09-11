# Preparation Root Cause

The source preparation process did not receive the existing SEC/OpenDART configuration. The worktree had no local `.env`, and `THESIS_MONITOR_ENV_FILE` was not bound. US official-profile requests therefore failed and KR official profiles were unavailable. No secret value is recorded. The frozen candidate budget is not retried in this task, and no model subprocess was spawned.
