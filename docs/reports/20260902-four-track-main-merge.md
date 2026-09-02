# Four-Track Main Merge

## Lineage

- work instruction: `87887dbf9d42a841f27b6344694ce03bfe34c092`
- base: `89d3dc7ea350564c2b55b36b0c9ef9406330b3f9`
- Track A: `20c80b6d968b5770947a6621fa4867d51967dbe0`
- Track B: `70d60e4ba100ad140b9aef6e26cfda0acf4f1a8f`
- Track C: `4407cd11a78579e11681b503b2d4e72ee3c3d60f`
- Track D: `ee4e4688816d35f7a5ade7630eac07e6edd215eb`
- integration evidence: `c0a4d66616eb775415b602e58ddf2c8198cf4962`
- report/promotion target: the commit containing this report

## Gate

`BASE_CONTAINS_PREVIOUS_SAFE_REPAIRS = PASS`

`ALL_TRACKS_COLLAPSED_INTO_ONE_UNREVIEWABLE_COMMIT = 0`

`CROSS_TRACK_SCOPE_CREEP = 0`

`OPEN_P0 = 0`

`OPEN_MATERIAL_P1 = 0`

`OPEN_P2 = 2` carried non-blocking presentation items: unverified screenshot-convention
reconciliation and optional historical rejection-report polish.

`FOUR_TRACK_REPAIR = READY_FOR_MAIN`

Promotion is allowed only after the report/promotion target passes GitHub Actions Test/Lint and
`origin/main` remains the recorded base. The merge method must be a clean linear fast-forward.
Runtime restart is limited to the thesis-monitor service because imported runtime code changed;
scheduler times, ownership, recipient configuration, and Production Assist do not change.
