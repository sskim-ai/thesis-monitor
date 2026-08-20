# Phase 9.0B Lineage Verification

- Canonical FCF facts audited: `191`
- Complete input lineage: `191`
- Complete lineage percentage: `100%`
- Lineage/arithmetic failures: `0`

Every eligible FCF retains exactly two input Fact IDs, matching issuer, period, currency/unit, entity scope, statement basis, and source-document chain. Derived raw SHA is deterministic over both input payload hashes.

## Representative Proofs

- **US domestic issuer**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **non-calendar fiscal issuer**: `MU`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **foreign issuer / ADR**: `TSM`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **CAPEX-heavy infrastructure**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **pre-profit biotech**: `RXRX`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **financial industry exclusion**: `003690`; OCF `PARTIAL`, CAPEX `NOT_APPLICABLE`, FCF `NOT_APPLICABLE`
- **KR period-context block**: `000660`; OCF `PARTIAL`, CAPEX `PARTIAL`, FCF `BLOCKED`
