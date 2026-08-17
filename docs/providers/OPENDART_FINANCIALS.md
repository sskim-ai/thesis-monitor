# OpenDART Financial Provider

## Structured Primary

Formal Korean financial collection uses `fnlttSinglAcntAll.json` as the structured primary. The
provider requests both CFS and OFS scopes, then selects CFS per field and uses an exact OFS
occurrence only when that field has no unambiguous CFS occurrence. It preserves the source row
instead of reducing statement basis to an inferred filing-level label.

Required row fields include receipt/report identity, `fs_div`, `sj_div`, account ID/name/detail,
current and comparison column labels and values, currency, and ordering metadata. Account ID is
primary. Exact aliases are a bounded fallback; fuzzy name similarity is not used.

The major-account endpoint remains audit context only when the full-statement endpoint is
unavailable. A row without field-level CFS/OFS evidence cannot become verified v2 lineage.

## Amount Columns

For income statements in quarterly and semiannual reports:

- `thstrm_amount` is the current three-month amount;
- `thstrm_add_amount` is current cumulative YTD;
- `frmtrm_q_amount` is the prior-year three-month comparison;
- `frmtrm_add_amount` is prior-year cumulative comparison.

Balance-sheet amounts are point-in-time. Annual flow amounts are full-year. Report end date alone is
never used to relabel a source column.

## XBRL

`fnlttXbrl.xml` is the authoritative fallback format for unresolved context. The parser accepts the
ZIP archive, parses XML/XBRL contexts, and requires a unique exact taxonomy, period, unit, basis,
and filing match. Unsupported or ambiguous contexts remain unknown.

The Phase 8.1 runtime path does not backfill old snapshots because their original full-statement
rows and XBRL archives are not persisted. Future ingestion can retain exact v2 lineage without a DB
migration.

Phase 8.1.1 adds a separate archive-only recovery client. It discovers the latest formal filing and
its correction history, stores sanitized CFS/OFS raw envelopes atomically, and promotes only exact
field occurrences into shadow canonical Facts. XBRL is downloaded only when a structured candidate
exists but its period, basis, unit, or occurrence is ambiguous. A cached filing archive is reused;
missing or multiple exact-like facts stay unresolved.

The 2026-08-17 validation recovered seven H1 filings with 1,818 CFS and 1,291 OFS rows. It restored
17 safe income-statement amounts while keeping three SK hynix fields denied. Interim OCF had seven
conditional XBRL attempts and zero unique resolutions. Exact PPE and intangible-acquisition rows are
retained as `capex_components[]` audit candidates, but their periods are not safe enough to aggregate
and no FCF is calculated.

## Safety

- CFS and OFS are never inferred from IS/CIS/BS/CF.
- Current and comparison basis are independent.
- Formal and preliminary source types remain distinct.
- Correction filings supersede selection but do not delete original provenance.
- CFS/OFS, period, account, or currency mismatch blocks only dependent calculations when a direct
  occurrence remains independently verified.
- Provider errors and ambiguous rows produce Unknown, never zero or a first-row fallback.

Official API references:

- [OpenDART full financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020)
- [OpenDART XBRL original financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019019)
