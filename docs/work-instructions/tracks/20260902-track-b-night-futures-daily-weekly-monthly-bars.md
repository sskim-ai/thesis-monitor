# Track B — Night Futures Daily / Weekly / Monthly Bars

Separate:
- near-month contract identity
from
- Daily / Weekly / Monthly analytical timeframes.

Run-51:
reference date = 2026-09-01.

User screenshot control:
KOSPI200 202609, 2026/09/01 daily:
O 1061.00 / H 1061.40 / L 1031.30 / C 1040.50.

Verify against frozen provider lineage; do not force match.

Build:
- completed daily bar
- weekly bar aggregated through reference date, labeled IN_PROGRESS if week incomplete
- monthly bar aggregated through reference date, labeled IN_PROGRESS if month incomplete

Do not copy daily into W/M.
Do not use regular-session bars as night bars.
Do not invent W/M return baselines.

Render D/W/M for both KOSPI200 and KOSDAQ150 in the US market message.
