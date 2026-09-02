# Night Date-Convention Artifact Index

Work-instruction commit: `25b6b902b12a033d594972b82d77175cf1cdacdd`

## Human-readable reports

- `20260902-krx-night-0901-raw-row.md`
- `20260902-krx-night-0902-raw-row.md`
- `20260902-kiwoom-0901-vs-krx-ohlc-parity.md`
- `20260902-kiwoom-percent-baseline-reverse-check.md`
- `20260902-krx-night-session-timeline.md`
- `20260902-krx-basdd-semantic-evidence.md`
- `20260902-kosdaq150-date-cross-control.md`
- `20260902-night-date-convention-verdict.md`
- `20260902-night-date-convention-next-repair-scope.md`
- `20260902-night-date-convention-artifact-index.md`

## Machine-readable reports

- `20260902-krx-night-date-rows.json`
- `20260902-kiwoom-krx-parity.json`
- `20260902-night-date-convention-verdict.json`

## Provider ledger

Three read-only calls were made: the two required dates plus one 09/01 extraction retry after the temporary selector omitted spaces in `PROD_NM`. All succeeded, cache hits were zero, and both 09/01 responses had the same raw SHA. No raw provider file, cache, production packet, DB, scheduler, or recipient state was changed.

## Boundary

`CODE_CHANGE_DURING_DATE_PROOF = 0`

`PRODUCTION_SEND = 0`

`MAIN_MERGE = 0`
