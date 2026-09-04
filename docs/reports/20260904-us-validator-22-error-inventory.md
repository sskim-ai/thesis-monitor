# 2026-09-04 US Validator 22-Error Inventory

Frozen candidate SHA-256: `29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b`

| ID | Scope | Rule / span | Canonical evidence | Classification |
|---:|---|---|---|---|
| 1 | CRCL | `holder_decision_variable_missing` | core cites earnings; prose uses non-interest revenue/reserve-income variables | `VALIDATOR_FALSE_POSITIVE` |
| 2 | HUT | `holder_decision_variable_missing` | core uses commissioning/operation/project-return variables | `VALIDATOR_FALSE_POSITIVE` |
| 3 | MU | `working_capital_owner_mismatch` | `working-capital-relation:dbdfd04e725e83528d8fdd31`; qualitative core support | `SCHEMA_OWNERSHIP_MISMATCH` |
| 4 | TSLA | `working_capital_owner_mismatch` | `working-capital-relation:36181e61768dfd580d9ede01`; qualitative core support | `SCHEMA_OWNERSHIP_MISMATCH` |
| 5 | market | semantic mismatch on `market:relative:IWM:SPY`, `fields.relative_return_pct` | IWM relative to SPY, signed pct | `PROVENANCE_BINDING_DEFECT` |
| 6 | market | unbound `-0.6%` in `important_changes[1].text` | exact IWM/SPY relative-return occurrence | `PROVENANCE_BINDING_DEFECT` |
| 7 | CRCL | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 8 | CRCL | uncovered `시장 예상 fPER 99.09배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 9 | GOOGL | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 10 | GOOGL | uncovered `시장 예상 fPER 16.62배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 11 | HUT | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 12 | HUT | uncovered `시장 예상 fPER 149.31배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 13 | IBM | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 14 | IBM | uncovered `시장 예상 fPER 19.04배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 15 | MU | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 16 | MU | `피크 이익` phrase misread as valuation occurrence | no multiple claim in the cited core sentence | `VALIDATOR_FALSE_POSITIVE` |
| 17 | MU | uncovered `시장 예상 fPER 5.87배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 18 | SKHY | uncovered generic valuation basis phrase | `security_basis:current`, listed-security scope | `CORRECTION_CONTEXT_DEFECT` |
| 19 | SNDK | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 20 | SNDK | uncovered `시장 예상 fPER 6.5배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |
| 21 | TSLA | `valuation_fpe:pe` metric mismatch | typed `forward_pe` fact | `SCHEMA_OWNERSHIP_MISMATCH` |
| 22 | TSLA | uncovered `시장 예상 fPER 145.9배` | `valuation:consensus_forward_earnings` | `SCHEMA_OWNERSHIP_MISMATCH` |

## Totals

- `VALIDATOR_FALSE_POSITIVE`: 3
- `SCHEMA_OWNERSHIP_MISMATCH`: 16
- `PROVENANCE_BINDING_DEFECT`: 2
- `CORRECTION_CONTEXT_DEFECT`: 1
- `TRUE_CANDIDATE_VIOLATION`: 0
- Unclassified: 0

The offline replay used the frozen packet, candidate, and registry with `MODEL_RERUN=0`, `TELEGRAM_SEND=0`, and `DATA_REFETCH=0`. After repair it passed with binding, typed, validation, and ownership errors all zero.
