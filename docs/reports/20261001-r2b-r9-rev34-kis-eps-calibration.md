# REV34 KIS EPS Calibration Closure

Terminal: `R2B_R9_REV34_KIS_EPS_SCALE_CONFLICT`.
Live integration and remaining-KR6 acquisition: **NOT ADMITTED**.

- Base: `07bc7f722828d798d6c463749532a4a885abc1d4`.
- Instruction commit: `a44d9c75624e54adb4a0ccea8de3c13ed8fab42e`.
- Frozen acquisition: `ff31b2830a59e4e1bf6d6127245729853487d5e3`.
- Tested offline implementation: `7e8dd357ad5f60bb677ddf775e6444347f4ff32f`.

The two sealed Stage-A estimate bodies were reused with their exact required
hashes. Only two new annual financial-ratio requests were made, using one
memory-only authentication and sequential pacing. Observed inter-request idle
time: 1.108563 seconds. No retries, continuation, Stage-A estimate refresh,
Stage-B data, current-price request, or OpenDART request occurred.

Samsung's historical raw ratios are `1/10` in 2023.12 and 2024.12, but
`3282/33025` in 2025.12 (`6564.00 / 66050.0`). All three periods are retained;
no uniform conversion is approved. The reason for the source difference is
not proven. The reference endpoint's human-display unit also remains
unresolved. No raw value is promoted to display EPS.

SK hynix's three candidate rows are inventoried without assigning EPS or PER
semantics: the prerequisite conversion never qualified. KR8 typed states are
complete, with the other six explicitly not queried, not labelled uncovered.
FY1 EPS/provider PER/derived fPER qualification: 0/0/0. Optional derived fPER
remains blocked by the existing denial-only share/split basis contract.

Validation: focused 237 passed; full pytest 7283 passed, 63 skipped; Ruff,
diff check, Investment Knowledge and Chart Knowledge passed. The 44 new
tests use synthetic positive conversions and cover exact all-period conflict,
source/period/security ownership, partial-row uniqueness and valuation-only
authority. Production modules and source plans are unchanged.

Protected .env, DB/WAL/SHM and scheduler fingerprints remain equal. Models,
messages, Telegram, orders, production writes, main merge, push, deploy,
restart and GC: all zero.

Local evidence: `/Users/sskim/Documents/Codex/Reports/20261001-r2b-r9-rev34-kis-eps-calibration`.
The immutable report ZIP and SHA include both ratio raw responses, receipts,
the full comparison matrix, KR8 states, preserved source identities, tests,
logs and changed code. They are secret-scanned and manifest/CRC verified.
Only the iCloud Drive `Thesis Monitor` folder is an approved delivery target;
the separate delivery receipt records actual per-file server upload status.

Next work is a separately bounded definition/unit review, not REV35 live
integration. No period dropping, tolerance change, price/PER inference,
per-period factor or result-seeking estimate refresh is authorized here.
