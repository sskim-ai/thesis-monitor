# Phase 8.3.1.1 Security And ADR Matrix

Date/accessed: `2026-08-18`

| Provider | Issuer ID | Security/listing ID | Share class | Common identifiers | ADR/ordinary relation | ADR ratio | TSM/SKHY result |
|---|---|---|---|---|---|---|---|
| S&P Global MI | supported | supported | supported product claim | broad cross-reference | likely supported; exact entitlement POC | not proven publicly for selected fields | `SECURITY_BASIS_PARTIAL` pending POC |
| FactSet | `fsymEntityId` | security/regional/listing permanent IDs | hierarchy supported | CUSIP/ISIN/FIGI/CIK and more | related-security/entity API supports hierarchy | exact depositary ratio field not proven publicly | `SECURITY_BASIS_PARTIAL` pending POC |
| LSEG | broad issuer/security coverage | supported | supported product claim | LSEG and standard IDs | product-level support plausible | per-ADR denominator/ratio requires POC | `SECURITY_BASIS_PARTIAL` |
| FnSpace | company and 6-digit ticker | security fields available by API package | common/preferred behavior needs POC | KR local identifiers | not relevant for KR ordinary peer sample | not applicable | KR share basis still conditional |
| DeepSearch | company symbols plus legal/business IDs | `KRX:005930` style symbol | preferred/common distinction unproven | NICE/legal/business IDs | unproven | unproven | KR share basis unknown |
| Intrinio | company ID, CIK, LEI | security ID, FIGI, MIC, primary flags | explicit `share_class` | FIGI/ISIN/CUSIP/CIK | ADR coverage advertised and security maps to company | no explicit ratio in reviewed API fields | `SECURITY_BASIS_PARTIAL` |
| OpenFIGI | no issuer ID | FIGI/composite/share-class FIGI | supported | FIGI hierarchy | does not prove issuer/depositary relation | absent | identity auxiliary only |
| SEC | CIK issuer/filing identity | filing/security descriptions | reported classes | CIK and filing facts | filing evidence can support audit | no normalized provider ratio contract | identity/filing auxiliary only |

## Fixture Decisions

- `TSM`: no shortlisted public API evidence closes US ADR ratio, ratio direction, currency, and
  per-ADR denominator in one response. Current canonical promotion remains denied.
- `SKHY`: same result. Provider availability cannot repair the existing denied trailing-PE lineage.
- `GOOG/GOOGL`: FactSet and Intrinio expose issuer/security hierarchy capable of deterministic issuer
  dedup, subject to entitled POC. OpenFIGI share-class identity alone is insufficient.
- Provider identity is supplemental evidence and never replaces `security-identity-v2`.

## Evidence

- [FactSet Symbology API](https://developer.factset.com/api-catalog/symbology-api)
- [FactSet related securities workflow](https://developer.factset.com/recipe-catalog/streamline-research-process-easily-obtaining-related-securities-any-list-company)
- [Intrinio security lookup](https://docs.intrinio.com/documentation/web_api/get_security_by_id_v2)
- [Intrinio company lookup](https://docs.intrinio.com/documentation/web_api/get_company_v2)
- [Intrinio ADR coverage](https://intrinio.com/products/us-fundamentals)
- [DeepSearch entity identity](https://help.deepsearch.com/dp/api/func/company/company-search/findentity)
- [OpenFIGI API](https://www.openfigi.com/api/documentation)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
