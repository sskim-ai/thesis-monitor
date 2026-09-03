# Night Session Date-Mapping Verdict

## Confirmed

- Kiwoom daily 09/01 exactly equals KRX NIGHT BAS_DD 09/02 in all O/H/L/C fields.
- XKRX preceding-session lookup maps KRX 09/02 to UI/start date 09/01.
- The 09/01 popup percentages reproduce from baseline `1064.50`, equal to KRX NIGHT 09/01 close.
- The 09/02 popup percentages reproduce from baseline `1040.50`, equal to KRX NIGHT 09/02 close.
- Header `1043.60` versus `1029.15` reproduces `+14.45` and rounded `+1.40%`.
- KRX DAY 09/02 stores `1029.15` in both `TDD_CLSPRC` and `SETL_PRC`.
- Partial weekly and monthly aggregation open/high values match the Kiwoom controls.

## Missing

Official KRX BAS_DD 09/03 returned HTTP 200 with zero rows at 12:10 KST. Therefore Kiwoom daily
09/02 cannot yet be independently matched to KRX NIGHT 09/03, and neither weekly nor monthly
aggregation can be completed.

## Decision

`SESSION_DATE_MAPPING = NOT_CONFIRMED`.

`VERDICT = B. DATE_MAPPING_LIKELY_BUT_0903_ROW_MISSING`.

This is a bounded value-only result. It does not authorize a date remap, renderer change, cache
rewrite, or packet mutation. A later read-only comparison can promote the verdict to A only if the
official 09/03 NIGHT row independently closes daily, weekly, and monthly parity.

