# Track C — Temporary Night-Futures Suppression + Market Regression

Night-futures session-date convention remains unresolved.

Do not modify KRX/Kiwoom date architecture in this task.

Temporarily suppress the user-facing US night-futures section with an internal reason:
SESSION_DATE_CONVENTION_PENDING.

Preserve collector/history/DWM code.

Preserve US nominal Treasury primary block:
3Y / 5Y / 10Y / 30Y
latest safe yield + previous valid observation delta in bp.

Do not reintroduce 10Y real yield as the primary user-facing rate block.
