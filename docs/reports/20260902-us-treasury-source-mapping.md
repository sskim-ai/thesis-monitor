# US Treasury Source Mapping

Provider: Federal Reserve Bank of St. Louis FRED. The source series are official/public daily U.S. Treasury constant-maturity yields, quoted in percent and linked to the Board of Governors H.15 release. The existing `FredProvider` remains the only collector; no paid source or arbitrary finance site was introduced.

| Maturity | Series | Canonical fact | Source |
| --- | --- | --- | --- |
| 3Y | `DGS3` | `market:nominal_yield:DGS3` | `https://fred.stlouisfed.org/series/DGS3` |
| 5Y | `DGS5` | `market:nominal_yield:DGS5` | `https://fred.stlouisfed.org/series/DGS5` |
| 10Y | `DGS10` | `market:nominal_yield:DGS10` | `https://fred.stlouisfed.org/series/DGS10` |
| 30Y | `DGS30` | `market:nominal_yield:DGS30` | `https://fred.stlouisfed.org/series/DGS30` |

The provider ingests the two newest non-missing rows oldest-first so first-time series activation retains an immediate prior observation. The DB identity remains provider + series + observation date; no migration is needed.

`UST_3Y_SOURCE = PROVEN`

`UST_5Y_SOURCE = PROVEN`

`UST_10Y_SOURCE = PROVEN`

`UST_30Y_SOURCE = PROVEN`
