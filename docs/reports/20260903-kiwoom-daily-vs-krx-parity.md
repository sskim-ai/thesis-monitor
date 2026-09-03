# Kiwoom Daily vs KRX NIGHT Parity

## Kiwoom 2026-09-01

Kiwoom `1061.00/1061.40/1031.30/1040.50` does not match KRX NIGHT BAS_DD 09/01. Absolute
O/H/L/C differences are `6.00/11.05/22.50/24.00`, or
`0.5623%/1.0304%/2.1351%/2.2546%` relative to KRX.

It matches KRX NIGHT BAS_DD 09/02 exactly in all four fields: absolute and percentage differences
are all zero.

`KIWOOM_0901_DAILY = MATCHES_NEXT_BAS_DD`.

## Kiwoom 2026-09-02

Kiwoom `1023.00/1048.35/1020.25/1043.60` does not match KRX NIGHT BAS_DD 09/02. Absolute
differences are `38.00/13.05/11.05/3.10`, or
`3.5815%/1.2295%/1.0715%/0.2979%`.

KRX BAS_DD 09/03 is not published at the observation cutoff, so the required next-BAS_DD
comparison cannot be performed.

`KIWOOM_0902_DAILY = INSUFFICIENT_EVIDENCE`.

## Calendar

The repository XKRX calendar resolves the preceding sessions as 09/01 -> 08/31, 09/02 -> 09/01,
and 09/03 -> 09/02. Thus the proven 09/01 Kiwoom-to-09/02 KRX match is exactly one exchange
session, not a naive calendar-day rule. The second link remains unproven.

`SESSION_DATE_MAPPING = NOT_CONFIRMED`.

