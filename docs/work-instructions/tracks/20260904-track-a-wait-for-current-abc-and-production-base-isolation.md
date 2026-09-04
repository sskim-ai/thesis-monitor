# Track A — Wait for Current ABC + Production Base Isolation

Do not begin this repair while the morning Structured Autonomy A/B/C experiment is still active.

Hard gates:
CURRENT_ABC_TERMINAL=PASS
CURRENT_ABC_MODEL_PROCESSES=0
CURRENT_ABC_APP_SERVER_RELEASED=PASS

Then create a separate production-repair worktree based on the natural operating lineage rooted at 5d5f336..., not the shadow experiment branch by default.

Do not import unfinished Structured Autonomy production behavior.
