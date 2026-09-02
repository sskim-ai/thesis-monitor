# Run-51 Night Date Replay

Packet: `2026-09-02-us-run-51-39a4d4eec53e`

Observation: `2026-09-02T08:20:00+09:00`

Expected XKRX reference: `2026-09-01`

Provider raw `BAS_DD`: `2026-09-01`

Both required contracts match the v3 date contract:

- KOSPI200 nearest: `A0169000`, match `true`
- KOSDAQ150 nearest: `A0669000`, match `true`

Finality, instrument identity, same-contract DAY comparison, source occurrence identity, and
change provenance all pass. The canonical result is ready `2/2` and rendered `2/2`.

The replay does not rewrite the immutable run-51 production archive and creates no delivery intent.
