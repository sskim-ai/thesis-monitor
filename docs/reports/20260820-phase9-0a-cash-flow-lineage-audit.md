# Phase 9.0A Cash-Flow Lineage Audit

The SEC audit retains exact namespace/tag, accession, form, filed date, start/end, unit, value, fiscal year/period, and payload SHA. FCF pairs require the same accession, start, end, and unit. The KR audit preserves OpenDART receipt, CFS/OFS, statement section, taxonomy tag, source row identity, amount, and denial reason.

KR evidence found exact OCF and PPE/intangible rows, but the existing XBRL matcher could not prove a unique CF period context. Therefore KR OCF is `PARTIAL`, CAPEX is `PARTIAL`, and FCF is `BLOCKED`; no value is promoted. SEC eligible pairs are issuer-level and do not authorize security-level per-share or yield arithmetic.

## Representative Proofs

- **KR non-financial industrial**: `000660`; OCF `PARTIAL`, CAPEX `PARTIAL`, FCF `BLOCKED`
- **US domestic issuer**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **non-calendar fiscal issuer**: `MU`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **foreign issuer / ADR**: `TSM`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **capex-heavy data-center**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **pre-profit biotech**: `RXRX`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **financial / insurance exclusion**: `003690`; OCF `PARTIAL`, CAPEX `NOT_APPLICABLE`, FCF `NOT_APPLICABLE`
