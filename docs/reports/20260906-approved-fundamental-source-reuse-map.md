# Approved Fundamental Source Reuse Map

| Gate | Value |
| --- | --- |
| components | [{"component": "SecCompanyProfileSource", "market": "US", "output": "issuer identity, SIC, latest filing availability", "reuse": "UNCHANGED", "source": "SEC submissions and company_tickers"}, {"component": "SecFinancialSnapshotService._companyfacts_snapshots", "market": "US", "output": "reported revenue and earnings occurrences", "reuse": "GENERIC_READ_ONLY_ADAPTER", "source": "SEC companyfacts official XBRL"}, {"component": "OpenDartCompanyProfileSource", "market": "KR", "output": "issuer identity and KSIC", "reuse": "UNCHANGED", "source": "OpenDART company/corpCode"}, {"component": "OpenDartRecoveryClient + financial-lineage-v2", "market": "KR", "output": "CFS-first revenue and earnings occurrences", "reuse": "GENERIC_READ_ONLY_ADAPTER", "source": "OpenDART formal statements"}] |
| contract | "approved-fundamental-source-reuse-map-v1" |
| manual_ticker_fact_injection | 0 |
| new_paid_provider | 0 |
| new_website_scraper | 0 |
