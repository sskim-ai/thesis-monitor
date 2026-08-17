# KR Financial Lineage Architecture

## Purpose

`financial-lineage-v2` separates the source identity of each Korean financial amount from the
filing that contained it. The objective is not to display more numbers. It is to retain a verified
standalone amount when only a comparison or derived metric is unsafe.

```text
OpenDART filing
  -> exact full-statement CFS/OFS request
  -> exact account/source-column occurrence
  -> field-level amount period and statement basis
  -> dependency-specific quality decision
  -> canonical Fact
  -> AI interpretation
```

## Filing, Statement, And Amount Periods

The filing period does not define every amount in the filing. A semiannual filing can contain both
Q2 single-quarter and H1 cumulative income-statement columns. Each occurrence therefore preserves:

- receipt, report code, business year, provider, and source type;
- `fs_div`, statement type, account ID/name/detail, and source column;
- amount role and variant;
- amount-period type, start, and end;
- currency, source-row identity, and verification state.

`IS`, `CIS`, `BS`, `CF`, and `SCE` identify statement type only. They never establish consolidated
or separate basis. CFS and OFS come from the explicit OpenDART full-statement scope or the source
row itself.

## Source Priority

For the same field and economic period:

1. formal filing over preliminary earnings;
2. verified CFS over verified OFS;
3. latest authoritative correction over the original filing;
4. no selection when the exact source occurrence is ambiguous.

The original filing remains in history. Only exact duplicates from the same filing, account,
period, basis, and source column may be deduplicated.

## Dependency Graph

Direct amounts require an exact account occurrence, amount period, currency, and statement basis.
Operating margin additionally requires homogeneous revenue and operating-income lineages. Growth
requires current and comparison amounts with the same account, basis, amount scope, duration,
currency, and source type. QoQ and YoY period distance must also match their respective contracts.

This permits:

```text
current operating income: verified CFS Q2 -> usable
comparison operating income: OFS or cumulative/ambiguous -> not comparable
result: current amount stays usable; growth is withheld
```

It does not permit annualization, prorating, first-row selection, natural-language account matching,
or mixing preliminary and formal amounts into a derived metric.

## Preliminary And Formal Filings

Preliminary earnings retain their own source type and may expose only directly reported revenue,
operating income, and explicitly reported net income. Margin may be calculated from homogeneous
verified preliminary amounts. Preliminary data does not create OCF, CAPEX, FCF, inventory, ROIC,
BVPS, or book equity. A later formal filing becomes primary while preliminary evidence remains
historical provenance.

## XBRL Fallback

The XBRL utility parses instance documents with an XML parser and preserves contexts, duration or
instant periods, units, dimensions, taxonomy identity, and explicit statement-basis dimensions. A
JSON row can be reconciled only to one exact XBRL occurrence. Multiple matches remain ambiguous;
there is no first-match fallback.

Runtime promotion still requires an exact account/taxonomy, period, unit, basis, and filing match.
Historical records that lack their original XBRL or full-statement source row are not reconstructed.

## Persistence

Field lineage is stored in the existing `raw_financial_fields` JSON using contract
`financial-lineage-v2`. No database migration is required. Historical assessments retain the
lineage available at their assessment cutoff; a future correction is not retroactively applied.

## Cash Flow Boundary

OpenDART CF statements make authoritative OCF extraction feasible when an exact taxonomy/account ID
is stable. CAPEX is not one universal account and can span tangible, intangible, construction, and
other investment cash outflows. CAPEX and FCF therefore remain unavailable until a validated
company-neutral account aggregation contract exists.
