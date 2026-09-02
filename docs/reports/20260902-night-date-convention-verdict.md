# Night Date-Convention Verdict

`NIGHT_DATE_CONVENTION_VERDICT = INSUFFICIENT_EVIDENCE`

The exact 09/01 KRX NIGHT row does not match the Kiwoom candle. The Kiwoom displayed percentages independently reproduce from the KRX 09/01 NIGHT close of 1064.50, strongly suggesting the visual candle is the next NIGHT bar. However, the decisive official `BAS_DD=20260902` query returned HTTP 200 with zero rows. The reverse calculation cannot replace that raw row.

| Gate | Result |
|---|---|
| KRX source service | `fut_bydd_trd` |
| `KRX_0901_NIGHT_ROW_FOUND` | `PASS` |
| `KRX_0902_NIGHT_ROW_FOUND` | `FAIL` |
| `KIWOOM_0901_MATCHES_KRX_0901` | `FAIL` |
| `KIWOOM_0901_MATCHES_KRX_0902` | `FAIL` (row absent) |
| `BASELINE_PARITY` | `PASS` |
| `PROVIDER_SEMANTICS_DOC_SUPPORT` | `PARTIAL` |
| `KOSDAQ150_DATE_MAPPING_CONSISTENT` | `NOT_ENOUGH_EVIDENCE` |
| `CROSS_CONTRACT_COMPARISON` | `0` |
| `DAY_ROW_COMPARED_AS_NIGHT` | `0` |
| `CODE_CHANGE_DURING_DATE_PROOF` | `0` |

Verdict A is deliberately withheld because its mandatory exact 09/02 match is unavailable.
