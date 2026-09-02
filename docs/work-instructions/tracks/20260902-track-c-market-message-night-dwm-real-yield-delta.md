# Track C — Market Message: Night D/W/M + Real-Yield Delta

Render KOSPI200 and KOSDAQ150 near-month:
- Daily
- Weekly (진행중 when appropriate)
- Monthly (진행중 when appropriate)

Contract month is identity metadata only.

Use packet-owned D/W/M facts with numeric provenance.

Add US 10Y real yield:
- latest safe level/date
- previous valid observation level/date
- delta in %p
- delta in bp

Formula:
delta_pp = current - previous
delta_bp = delta_pp * 100

Do not label lagged observation change as "today".

Frozen run-51 market replay:
non-night numbers/selections unchanged;
only night D/W/M and real-yield delta are intentional additions.
Final validator must PASS before send.
