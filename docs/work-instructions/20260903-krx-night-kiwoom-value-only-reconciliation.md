# thesis-monitor — KRX Night vs Kiwoom Value-Only Reconciliation
## Read-only provider queries + calculations only
## No production code change, no renderer change, no packet mutation

### 0. Purpose

The only purpose is to determine, from actual values, whether:

```text
Kiwoom chart date = night-session start date
KRX BAS_DD       = night-session end/trading date
```

and whether Kiwoom weekly/monthly bars can be reproduced by aggregating the corresponding KRX NIGHT daily bars.

Do NOT repair anything in this task.

Hard:
- CODE_CHANGE = 0
- PRODUCTION_MUTATION = 0
- PRODUCTION_SEND = 0
- CACHE/RAW_ROW_REWRITE = 0

---

## 1. User-provided Kiwoom controls

### KOSPI200 202609 — daily 2026/09/01

```text
O 1061.00
H 1061.40
L 1031.30
C 1040.50

displayed:
O -0.33%
H -0.29%
L -3.12%
C -2.25%
```

### KOSPI200 202609 — daily 2026/09/02

```text
O 1023.00
H 1048.35
L 1020.25
C 1043.60

displayed:
O -1.68%
H +0.75%
L -1.95%
C +0.30%
```

Header/reference display at the same time:

```text
current 1043.60
change +14.45
+1.40%
reference/base 1029.15
```

### KOSPI200 202609 — weekly bar labeled 2026/08/31

```text
O 1067.00
H 1072.45
L 1020.25
C 1043.60
```

### KOSPI200 202609 — monthly bar labeled 2026/09/01

```text
O 1061.00
H 1061.40
L 1020.25
C 1043.60
```

Treat screenshots as visual controls only.

---

## 2. Query exact KRX NIGHT rows

Using the repository's actual KRX futures daily adapter/service, query:

```text
BAS_DD = 20260901
BAS_DD = 20260902
BAS_DD = 20260903
```

For each date, capture KOSPI200 202609 NIGHT:

```text
BAS_DD
instrument / contract
MKT_NM
open
high
low
close
volume
change
change_pct
reference_price / settlement / base field if present
raw SHA-256
normalized fingerprint
```

Also capture the corresponding DAY/regular row separately for each date.

Do not mix DAY and NIGHT rows.

Required:
- KRX_0901_NIGHT_ROW
- KRX_0902_NIGHT_ROW
- KRX_0903_NIGHT_ROW

If 09/03 is not yet published:
record NOT_AVAILABLE and finish with partial evidence.
Do not invent.

---

## 3. Daily date-mapping parity

Compare exactly:

```text
Kiwoom daily 09/01
vs
KRX NIGHT BAS_DD 09/01
vs
KRX NIGHT BAS_DD 09/02
```

Then:

```text
Kiwoom daily 09/02
vs
KRX NIGHT BAS_DD 09/02
vs
KRX NIGHT BAS_DD 09/03
```

Per field calculate:

```text
absolute difference
percentage difference
exact_match boolean
```

Verdict for each Kiwoom daily bar:

```text
MATCHES_SAME_BAS_DD
MATCHES_NEXT_BAS_DD
MATCHES_NEITHER
INSUFFICIENT_EVIDENCE
```

---

## 4. Reverse-check Kiwoom daily popup percentages

For Kiwoom 09/01:

reverse-calculate baseline from each displayed percentage:

```text
baseline_open
baseline_high
baseline_low
baseline_close
```

Check whether they converge to:

```text
~1064.50
```

and whether that equals KRX 09/01 NIGHT close.

For Kiwoom 09/02:

reverse-calculate from:

```text
O -1.68%
H +0.75%
L -1.95%
C +0.30%
```

Check whether they converge to:

```text
~1040.50
```

and whether that equals the previous Kiwoom night daily close / matching KRX prior NIGHT close.

Required:
- KIWOOOM_0901_POPUP_BASELINE
- KIWOOOM_0902_POPUP_BASELINE
- POPUP_BASELINE_CHAIN_PARITY

---

## 5. Separately verify the header +1.40% baseline

Kiwoom header:

```text
1043.60
+14.45
+1.40%
기준가 1029.15
```

Calculate:

```text
1043.60 - 1029.15
1043.60 / 1029.15 - 1
```

Verify exact parity with +14.45 / +1.40%.

Then identify which KRX DAY/regular/reference field equals or best corresponds to:

```text
1029.15
```

Possible roles to test, without assuming:

```text
same-day regular-session close
settlement/reference price
official base/reference price
other provider-native reference field
```

Return exact field identity.

Do NOT label it "day close" unless the raw schema proves it.

Required:
- HEADER_REFERENCE_1029_15_SOURCE = ...
- HEADER_RETURN_PARITY = PASS/FAIL

---

## 6. Session-start vs KRX end/trading-date calculation

If:

```text
Kiwoom 09/01 daily == KRX BAS_DD 09/02 NIGHT
Kiwoom 09/02 daily == KRX BAS_DD 09/03 NIGHT
```

then calculate the implied mapping:

```text
Kiwoom display/session-start date = KRX BAS_DD - one session
```

Do not express this as simple calendar-day subtraction.

Use the actual XKRX business/session calendar.

Return:

```text
SESSION_DATE_MAPPING =
START_DATE_UI_TO_END_DATE_KRX
or
NOT_CONFIRMED
```

---

## 7. Weekly aggregation cross-check

Hypothesis:

Kiwoom weekly bar labeled `2026/08/31` aggregates night sessions whose START dates are:

```text
08/31
09/01
09/02
```

which should correspond to KRX BAS_DD:

```text
09/01
09/02
09/03
```

if the date-mapping hypothesis is correct.

Using the actual KRX NIGHT rows for the same contract 202609, calculate:

```text
weekly open  = first row open
weekly high  = max(high)
weekly low   = min(low)
weekly close = last row close
```

Compare with Kiwoom weekly:

```text
O 1067.00
H 1072.45
L 1020.25
C 1043.60
```

Required:
- WEEKLY_AGGREGATION_PARITY = PASS/FAIL/INSUFFICIENT

Do not splice another contract.

---

## 8. Monthly aggregation cross-check

Hypothesis:

Kiwoom monthly bar labeled `2026/09/01` aggregates night sessions whose START dates are:

```text
09/01
09/02
```

which should correspond to KRX BAS_DD:

```text
09/02
09/03
```

if the mapping is correct.

Calculate same-contract monthly-to-date OHLC:

```text
open  = first constituent open
high  = max(high)
low   = min(low)
close = last constituent close
```

Compare with Kiwoom monthly:

```text
O 1061.00
H 1061.40
L 1020.25
C 1043.60
```

Required:
- MONTHLY_AGGREGATION_PARITY = PASS/FAIL/INSUFFICIENT

---

## 9. KOSDAQ150 optional cross-control

If time/cost is small, repeat the same BAS_DD 09/01~09/03 row collection for KOSDAQ150 202609.

Use only as a product-wide date-mapping control.

No need for Kiwoom parity if no screenshot exists.

---

## 10. Final verdict

Return exactly one:

```text
A. START_DATE_UI_TO_END_DATE_KRX_CONFIRMED
B. DATE_MAPPING_LIKELY_BUT_0903_ROW_MISSING
C. DIFFERENT_BAR_DEFINITION
D. CONTRACT_OR_REFERENCE_FIELD_MISMATCH
E. INSUFFICIENT_EVIDENCE
```

For A, require:

```text
Kiwoom 09/01 daily == KRX 09/02 NIGHT
Kiwoom 09/02 daily == KRX 09/03 NIGHT
weekly aggregation matches
monthly aggregation matches
```

Do not change code.

---

## 11. Required reports

Create:
1. `20260903-krx-night-0901-0902-0903-raw-values.md`
2. `20260903-kiwoom-daily-vs-krx-parity.md`
3. `20260903-kiwoom-popup-baseline-reverse-check.md`
4. `20260903-kiwoom-header-reference-1029-15-proof.md`
5. `20260903-krx-night-weekly-aggregation-crosscheck.md`
6. `20260903-krx-night-monthly-aggregation-crosscheck.md`
7. `20260903-night-session-date-mapping-verdict.md`
8. `20260903-night-value-reconciliation-artifact-index.md`

Machine-readable:
- `20260903-krx-night-raw-values.json`
- `20260903-kiwoom-krx-daily-parity.json`
- `20260903-night-aggregation-parity.json`
- `20260903-night-date-mapping-verdict.json`

---

## 12. Completion response

Return:

```text
KRX_SOURCE_SERVICE = ...

KRX_0901_NIGHT =
O/H/L/C ...
reference fields ...

KRX_0902_NIGHT =
O/H/L/C ...
reference fields ...

KRX_0903_NIGHT =
O/H/L/C ...
reference fields ...

KIWOOM_0901_DAILY =
O1061.00 H1061.40 L1031.30 C1040.50

KIWOOM_0902_DAILY =
O1023.00 H1048.35 L1020.25 C1043.60

DAILY_PARITY =
09/01 -> ...
09/02 -> ...

POPUP_BASELINES =
09/01 ...
09/02 ...

HEADER_REFERENCE =
1029.15 source field ...
+14.45/+1.40 parity ...

WEEKLY_AGGREGATION =
calculated O/H/L/C ...
Kiwoom O/H/L/C ...
parity ...

MONTHLY_AGGREGATION =
calculated O/H/L/C ...
Kiwoom O/H/L/C ...
parity ...

SESSION_DATE_MAPPING = ...

VERDICT = ...

CODE_CHANGE = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

## Final principle

This task is only:

```text
query values
calculate
compare
conclude
```

No repair.
No production mutation.
No assumption-based date remapping.
