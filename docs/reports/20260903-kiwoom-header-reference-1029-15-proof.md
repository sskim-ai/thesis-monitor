# Kiwoom Header Reference 1029.15 Proof

## Arithmetic

- `1043.60 - 1029.15 = 14.45`
- `(1043.60 / 1029.15 - 1) * 100 = 1.404071321%`
- Two-decimal display: `+1.40%`

`HEADER_RETURN_PARITY = PASS`.

## KRX Source Fields

The exact KRX regular-session row is BAS_DD `20260902`, contract `A0169000`, `MKT_NM=정규`.
Within that same raw row:

- `TDD_CLSPRC = 1029.15`
- `SETL_PRC = 1029.15`
- `TDD_LWPRC = 1029.15`

Therefore the raw schema proves that `1029.15` is both that regular row's close and settlement
price. Value-only reconciliation cannot determine whether the Kiwoom UI's label `기준가` is sourced
specifically from `TDD_CLSPRC` or `SETL_PRC`, because they collide numerically. The low is an
incidental equal value, not a plausible reference semantic.

`HEADER_REFERENCE_1029_15_SOURCE = KRX_DAY_20260902_A0169000.TDD_CLSPRC_AND_SETL_PRC`.

`HEADER_REFERENCE_UI_FIELD_IDENTITY = NOT_DISAMBIGUATED_BY_VALUE_ONLY`.

No report labels the value exclusively as a day close or exclusively as settlement.

