# thesis-monitor — KRX Night Futures Date-Convention Read-Only Proof
## Verify which KRX BAS_DD corresponds to the Kiwoom `2026/09/01` night daily candle
## No code repair, no production mutation, no renderer change in this task

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Investigation date: `2026-09-02 KST`
- Task class: `READ_ONLY_PROVIDER_SESSION_DATE_PROOF`
- Production Assist: preserve `OFF`
- Production send: `0`
- Scheduler/job trigger: `0`
- Production DB mutation: `0`
- Provider raw-row rewrite: `0`
- Code repair: `0`
- Main merge: `0`

The only question to answer is:

```text
Which KRX BAS_DD corresponds to the Kiwoom night-chart candle
labeled 2026/09/01 for KOSPI200 202609?
```

Do not change the night-futures production contract until this is proven.

---

# 1. User-provided Kiwoom visual control

The user-provided Kiwoom screenshot shows:

```text
screen:
야간차트

instrument:
KOSPI200

contract:
202609

selected chart date:
2026/09/01

OHLC:
Open  = 1,061.00
High  = 1,061.40
Low   = 1,031.30
Close = 1,040.50

displayed percentages:
Open   -0.33%
High   -0.29%
Low    -3.12%
Close  -2.25%
```

Treat this screenshot as a visual control, not as the machine source of truth.

Do NOT assume yet whether the displayed date is:
- session start date
- KRX trading date
- session end date
- UI chart bucket date

That mapping is what this task must prove.

---

# 2. Existing KRX control already observed

Previously stored/observed KRX NIGHT row:

```text
BAS_DD = 2026-09-01

KOSPI200 near-month / 202609
MKT_NM = 야간

OHLC approximately:
Open  = 1,067.00
High  = 1,072.45
Low   = 1,053.80
Close = 1,064.50
```

This does NOT match the Kiwoom 2026/09/01 candle.

Do not reinterpret or rewrite this row.

---

# 3. Primary hypothesis to test

Hypothesis A:

```text
Kiwoom chart date 2026/09/01
= night session that STARTED 2026/09/01 evening
  and ENDED 2026/09/02 morning

therefore:
KRX BAS_DD = 2026-09-02
```

If true, the KRX row for:

```text
BAS_DD = 2026-09-02
MKT_NM = 야간
KOSPI200 202609
```

should match or materially align with:

```text
O 1061.00
H 1061.40
L 1031.30
C 1040.50
```

Hypothesis B:

```text
Kiwoom and KRX use different bar/session definitions
```

If BAS_DD=20260902 does not match, identify the exact difference instead of forcing Hypothesis A.

---

# 4. Read-only source access

Use the existing repository KRX source adapter or provider interface.

Do NOT:
- alter provider cache
- patch historical rows
- rewrite raw response files
- change production packet state
- trigger any market/stock production job

A direct read-only historical provider query is allowed for:

```text
2026-09-01
2026-09-02
```

because the purpose is provider-date semantics verification.

Record:
- exact endpoint/service
- request date
- response timestamp
- HTTP/status if applicable
- raw response SHA-256
- normalized row fingerprint

No secrets.

---

# 5. Mandatory KRX query — 2026-09-01

Query the exact KRX service for:

```text
BAS_DD = 20260901
```

Filter to:

```text
KOSPI200 futures
contract 202609
MKT_NM = 야간
```

Capture exact:

```text
BAS_DD
ISU_CD / ISU_NM
MKT_NM
contract/maturity
Open
High
Low
Close
volume if present
change / change-rate if present
```

Also capture the corresponding DAY/regular row for the same contract/date if the API provides it.

Required:

```text
KRX_0901_NIGHT_ROW_FOUND = PASS / FAIL
```

---

# 6. Mandatory KRX query — 2026-09-02

Query the exact same KRX service for:

```text
BAS_DD = 20260902
```

Filter identically:

```text
KOSPI200 futures
contract 202609
MKT_NM = 야간
```

Capture the same fields.

Required:

```text
KRX_0902_NIGHT_ROW_FOUND = PASS / FAIL
```

---

# 7. Exact OHLC parity test

Compare the Kiwoom screenshot candle:

```text
O 1061.00
H 1061.40
L 1031.30
C 1040.50
```

against both:

```text
KRX BAS_DD 20260901 NIGHT
KRX BAS_DD 20260902 NIGHT
```

Calculate absolute and percentage differences per field.

Set:

```text
KIWOOM_0901_MATCHES_KRX_0901 =
PASS / FAIL / PARTIAL

KIWOOM_0901_MATCHES_KRX_0902 =
PASS / FAIL / PARTIAL
```

Define `PASS` as exact equality after the repository/provider's legitimate numeric normalization.

Do not use loose tolerance to hide a session mismatch.

---

# 8. Percentage-baseline reverse check

The Kiwoom chart displays:

```text
Open   -0.33%
High   -0.29%
Low    -3.12%
Close  -2.25%
```

Reverse-calculate the implied comparison baseline for each field.

Check whether the implied baseline is approximately:

```text
1,064.50
```

Then compare `1,064.50` to the KRX 2026-09-01 NIGHT close.

Required report:

```text
KIWOOM_PERCENT_BASELINE_IMPLIED =
...

KRX_0901_NIGHT_CLOSE =
...

BASELINE_PARITY =
PASS / FAIL
```

This is a diagnostic to determine whether the Kiwoom 09/01 candle is chained from the preceding KRX NIGHT close.

Do not use the reverse calculation as a substitute for the actual 09/02 raw row.

---

# 9. Session timeline proof

Build one explicit timeline:

```text
2026-08-31 evening
→ 2026-09-01 morning

2026-09-01 regular day session

2026-09-01 evening
→ 2026-09-02 morning

2026-09-02 regular day session
```

Map, where evidence supports it:

```text
Kiwoom chart label
KRX BAS_DD
KRX MKT_NM
contract
OHLC
```

Do not infer unsupported timestamps.

The goal is to establish whether KRX labels the night session by its end/trading date while Kiwoom labels by its start date.

---

# 10. KRX semantic evidence

Inspect the repository's KRX provider docs/schema/comments for:

```text
BAS_DD semantic
MKT_NM semantic
night session trading-date convention
```

If repository docs cite an official KRX definition, preserve that exact meaning.

If the repository does not contain sufficient official documentation:

state:

```text
PROVIDER_SEMANTICS_DOC_SUPPORT = INSUFFICIENT
```

and rely on the exact row/timeline evidence without inventing a rule.

Required:

```text
PROVIDER_SEMANTICS_DOC_SUPPORT =
PROVEN /
PARTIAL /
INSUFFICIENT
```

---

# 11. KOSDAQ150 cross-control

Repeat the same date comparison for:

```text
KOSDAQ150 near-month / 202609
```

for both:

```text
BAS_DD 20260901
BAS_DD 20260902
```

This is a cross-control to ensure the date mapping is product-wide rather than a KOSPI200-only anomaly.

Capture exact OHLC and row fingerprints.

Set:

```text
KOSDAQ150_DATE_MAPPING_CONSISTENT =
PASS / FAIL / NOT_ENOUGH_EVIDENCE
```

---

# 12. Contract identity control

Verify for every compared row:

```text
same instrument root
same contract month
same NIGHT market/session
same adjustment convention if applicable
```

Hard:

```text
CROSS_CONTRACT_COMPARISON = 0
DAY_ROW_COMPARED_AS_NIGHT = 0
```

---

# 13. No code change in this task

Even if the result is obvious:

do NOT modify:
- expected night reference date
- renderer date label
- D/W/M history keying
- packet fact schema
- production source monitor

This task ends with a verdict and next-repair recommendation only.

Required:

```text
CODE_CHANGE_DURING_DATE_PROOF = 0
```

---

# 14. Final verdict taxonomy

Return exactly one:

```text
A. START_DATE_UI_VS_END_DATE_KRX_CONFIRMED

B. SAME_DATE_CONVENTION_BUT_DIFFERENT_SESSION_BAR

C. KIWOOOM_CHART_NOT_KRX_NIGHT_EQUIVALENT

D. CONTRACT_OR_ADJUSTMENT_MISMATCH

E. INSUFFICIENT_EVIDENCE
```

For verdict A, require strong evidence:

```text
Kiwoom 2026/09/01 candle
matches KRX BAS_DD 2026/09/02 NIGHT
AND
does not match KRX BAS_DD 2026/09/01 NIGHT
```

---

# 15. Repair implication

Do not implement, but classify what the next repair must do.

If verdict A:

```text
production source identity:
KRX BAS_DD / trading date

optional user-facing label:
night session start date

both must be stored separately
```

Recommended fields:

```text
provider_trading_date
session_start_date
session_end_date
user_display_session_date
```

Do not overload one `reference_date`.

If verdict B/C/D/E:
write the appropriate investigation/repair scope.

---

# 16. Required reports

Create:

1. `docs/reports/20260902-krx-night-0901-raw-row.md`
2. `docs/reports/20260902-krx-night-0902-raw-row.md`
3. `docs/reports/20260902-kiwoom-0901-vs-krx-ohlc-parity.md`
4. `docs/reports/20260902-kiwoom-percent-baseline-reverse-check.md`
5. `docs/reports/20260902-krx-night-session-timeline.md`
6. `docs/reports/20260902-krx-basdd-semantic-evidence.md`
7. `docs/reports/20260902-kosdaq150-date-cross-control.md`
8. `docs/reports/20260902-night-date-convention-verdict.md`
9. `docs/reports/20260902-night-date-convention-next-repair-scope.md`
10. `docs/reports/20260902-night-date-convention-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-krx-night-date-rows.json
docs/reports/20260902-kiwoom-krx-parity.json
docs/reports/20260902-night-date-convention-verdict.json
```

---

# 17. Required gates

Set exactly:

```text
KRX_SOURCE_SERVICE =
...

KRX_0901_NIGHT_ROW_FOUND =
PASS / FAIL

KRX_0902_NIGHT_ROW_FOUND =
PASS / FAIL

KRX_0901_NIGHT_OHLC =
O ... / H ... / L ... / C ...

KRX_0902_NIGHT_OHLC =
O ... / H ... / L ... / C ...

KIWOOM_0901_OHLC =
O 1061.00 / H 1061.40 / L 1031.30 / C 1040.50

KIWOOM_0901_MATCHES_KRX_0901 =
PASS / FAIL / PARTIAL

KIWOOM_0901_MATCHES_KRX_0902 =
PASS / FAIL / PARTIAL

KIWOOM_PERCENT_BASELINE_IMPLIED =
...

KRX_0901_NIGHT_CLOSE =
...

BASELINE_PARITY =
PASS / FAIL

PROVIDER_SEMANTICS_DOC_SUPPORT =
PROVEN / PARTIAL / INSUFFICIENT

KOSDAQ150_DATE_MAPPING_CONSISTENT =
PASS / FAIL / NOT_ENOUGH_EVIDENCE

CROSS_CONTRACT_COMPARISON =
0 / NONZERO

DAY_ROW_COMPARED_AS_NIGHT =
0 / NONZERO

CODE_CHANGE_DURING_DATE_PROOF =
0 / NONZERO

NIGHT_DATE_CONVENTION_VERDICT =
START_DATE_UI_VS_END_DATE_KRX_CONFIRMED /
SAME_DATE_CONVENTION_BUT_DIFFERENT_SESSION_BAR /
KIWOOOM_CHART_NOT_KRX_NIGHT_EQUIVALENT /
CONTRACT_OR_ADJUSTMENT_MISMATCH /
INSUFFICIENT_EVIDENCE

NEXT_REPAIR_CLASS =
SESSION_DATE_SCHEMA_SPLIT /
SESSION_BAR_DEFINITION_REPAIR /
CONTRACT_MAPPING_REPAIR /
MORE_EVIDENCE_REQUIRED /
NO_ACTION
```

---

# 18. Completion response

Return:

```text
KRX_SOURCE_SERVICE = ...

KRX 2026-09-01 NIGHT =
KOSPI200 ...
KOSDAQ150 ...

KRX 2026-09-02 NIGHT =
KOSPI200 ...
KOSDAQ150 ...

KIWOOM 2026/09/01 =
KOSPI200 202609
O 1061.00
H 1061.40
L 1031.30
C 1040.50

PARITY =
Kiwoom vs KRX 09/01 ...
Kiwoom vs KRX 09/02 ...

PERCENT_BASELINE =
implied ...
KRX 09/01 NIGHT close ...
parity ...

TIMELINE =
...

VERDICT =
...

INTERPRETATION =
...

NEXT_REPAIR_CLASS =
...

CODE_CHANGE_DURING_DATE_PROOF = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 19. Mandatory completion ZIP

Create:

`20260902-krx-night-date-convention-readonly-proof-bundle.zip`

Include:
- exact work instruction
- raw-row reports
- raw SHA/fingerprints
- parity table
- reverse-baseline calculation
- session timeline
- KOSDAQ150 cross-control
- semantic evidence
- final verdict
- next-repair scope
- machine-readable JSON
- artifact index

Exclude:
- secrets
- auth headers
- account identifiers
- recipient IDs
- hidden chain-of-thought

Compute SHA-256.

---

# 20. Final principle

Do not fix the date contract based on assumption.

Prove:

```text
Kiwoom label 2026/09/01
↔ which exact KRX BAS_DD NIGHT row?
```

The decisive test is the actual KRX `20260902` NIGHT OHLC.

Only after that result is known should the production session-date contract be modified.
