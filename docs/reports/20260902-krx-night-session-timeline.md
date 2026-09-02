# KRX Night Session Timeline

| Interval | Evidence-backed mapping |
|---|---|
| 2026-08-31 evening to 2026-09-01 morning | Official KRX `BAS_DD=20260901`, NIGHT, KOSPI200 202609: O 1067.00 / H 1072.45 / L 1053.80 / C 1064.50. No Kiwoom label was supplied for this interval. |
| 2026-09-01 regular session | Official KRX `BAS_DD=20260901`, regular DAY control, same contract: O 1068.65 / H 1080.25 / L 1056.95 / C 1078.15. It was not compared as NIGHT. |
| 2026-09-01 evening to 2026-09-02 morning | Kiwoom visual label `2026/09/01`: O 1061.00 / H 1061.40 / L 1031.30 / C 1040.50. The candidate official KRX `BAS_DD=20260902` response has zero rows. |
| 2026-09-02 regular session | The queried official daily response has zero rows, so no row-level mapping is asserted. |

Repository contracts describe KRX NIGHT `BAS_DD` as an end/trading date and the UI date as the preceding start date. The supplied values are compatible with that hypothesis because their percentage baseline is the prior NIGHT close, but the missing 09/02 row leaves the exact mapping unproved.

No unsupported intraday timestamp or relabeled date was created.
