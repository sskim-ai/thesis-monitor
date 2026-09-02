# KRX Night Field Mapping

| Meaning | Source | Validation |
| --- | --- | --- |
| Date | `BAS_DD` | exact query-date match |
| Product | `PROD_NM` + `ISU_NM` | supported target root |
| Contract | `ISU_CD` + maturity in `ISU_NM` | nonempty and parseable |
| NIGHT | `MKT_NM` | exact session resolver |
| O/H/L/C | `TDD_OPNPRC/HGPRC/LWPRC/CLSPRC` | finite, positive, low <= open/close <= high |
| Volume | `ACC_TRDVOL` | optional integer |
| Change | `CMPPREVDD_PRC` | optional official point change |

Generic investing cash flow or non-NIGHT rows are unrelated and never mapped.
