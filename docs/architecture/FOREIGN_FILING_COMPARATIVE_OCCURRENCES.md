# Foreign Filing Comparative Occurrences

Contract: `m12ds-r4-r3-foreign-filing-comparative-occurrence-lineage-v1`.

The existing `sec_foreign_filing` discovery route (five recent 6-Ks and the
existing 20-F search) remains the only source. No provider, ticker exception,
FX bridge or financial derivation was added. SEC payload SHA, document identity,
table/row/cell, explicit spanned headers, statement basis and raw unit accompany
each reported business occurrence in existing snapshot raw evidence.

The source audit found two distinct documents, not interchangeable versions:
the selected July earnings release has short quarter labels and rounded amounts;
the August consolidated statement, already discovered by the existing route,
has explicit three-month and six-month columns but was not parsed by the legacy
prose parser. The latter supplies a new selected current observation when the
ordinary latest-source selector runs. The former is not silently decorated with
lineage from the latter.

The HTML owner expands explicit colspan/rowspan headers. An explicit date range,
or an explicit number of calendar months ending on a stated month-end, resolves
the date interval. Bare quarter labels and filing dates never supply start dates.
Three-month and six-month cells remain distinct; no subtraction is performed.
Statement captions own consolidated/separate basis, not issuer convention.
Only exact statement revenue and operating-income row labels are recognized;
component revenue, EPS, margin percentages and cash-flow tables are excluded.

Current projection selects the latest explicit discrete period and leaves a
conflicting field absent. Comparative quality separately revalidates immutable
occurrence identities, source cells, dates, issuer, units, basis, values, cutoff
and selected snapshot binding. Same-document comparisons take precedence;
otherwise compatible same-provider prior-year occurrences use the latest
available filing. Conflicting authoritative prior cells cannot be bypassed by
an older filing. No choice depends on favorable amounts or direction.

The downstream authority recomputes this receipt from frozen inputs. A clean
independent field can grant issuer-business comparison authority only. The
existing restrictions on security valuation, per-share claims and recurring
profit remain unchanged. Alternate CompanyFacts conflicts are not cleared.

Production packet schemas and inference policy are not changed. This local
branch must not be merged, pushed or deployed by the R4-R3 task. New current
whole-cohort source coverage must pass before any Market/Core/A/B call.
