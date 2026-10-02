# REV15 Fiscal and FPI Financial Owners

This is an opt-in extension of the existing reported financial occurrence,
quality and comparison owners. It is not a parallel financial truth store.
`--exact-financial-owner` is required at the manual fresh-run freeze boundary.
Production imports retain their old default behavior. Delivery is disabled.

## Annual Fiscal Calendar

`issuer-declared-fiscal-week-calendar-v1` binds an official annual filing's
literal weekday/nearest-month-day policy and explicitly reported fiscal year,
end date and week count. Adjacent annual periods must have identical issuer,
metric, semantic, currency, unit and statement basis. Date differences alone
never authorize a 53/52 comparison. Periods must be contiguous, exactly 364/371
days, and end on the policy's exact weekday-nearest date.

The unchanged comparison constructor carries `FISCAL_WEEK_COUNT_DIFFERENCE`
and the policy receipt into the existing financial quality/fact lineage. The
comparison is reported annual, not a single quarter. Values are never week
adjusted. An unproven policy, nonadjacent year, quarter, or incompatible basis
is denied. Equal-duration annual comparisons do not acquire a duration tolerance.

## FPI Candidate Plan

The existing SEC submissions identity, cutoff, 550-day window and 128-candidate
metadata cap remain. The opt-in plan selects at most two current quarter-boundary
6-K candidates after the latest annual economic-period metadata, plus one current
20-F. Discovery ordering is economic report date, financial-document filename
hint, repeated same-issuer filename pattern, then filing identity. These are
fetch priorities only; none grants purpose, fact or financial authority.

The candidate plan is frozen after submissions and before document fetches.
Each candidate has one index, one primary and at most two already-authorized
exhibits. Fourteen total logical slots are compiled before network dispatch.
Response data fill these slots without adding descriptors. Outside-bound
candidates are retained in the audit; full issuer-history exhaustion is never
claimed. Unknown newer plausible financial documents remain fail-closed.

## Inline Occurrences

`sec-primary-inline-financial-v1` resolves exact standard IFRS Revenue,
RevenueFromContractsWithCustomers, ProfitLossFromOperatingActivities and
ProfitLoss through namespace-qualified concepts. Each occurrence binds SEC CIK,
accession, source bytes, exact duration context, consolidated basis, ISO currency,
scale, sign and inline element. Segment/scenario contexts, unsupported transforms,
missing units, ambiguous contexts and conflicting duplicates are denied.

The existing foreign field quality owner consumes these occurrences. Same-calendar
reported intervals explicitly handle leap-day annual comparisons; no arbitrary
day tolerance is introduced. Same-currency comparative evidence can select the
reporting-currency series when a convenience translation lacks a comparable.
Multiple otherwise eligible currencies remain ambiguous. Exact visual-table
conflicts are not averaged; unresolved note-column numbers cannot supersede an
exact inline occurrence. Annual extraction does not make old annual data current.

## Complete Absence

`FORMAL_FINANCIAL_SOURCE_COMPLETE_NO_QUALIFIED_FIELD` requires every frozen
candidate to be captured and purpose-classified, both parsers executed, no
unresolved lineage/parser/source error and no remaining bounded financial
candidate. A financial statement without resolved field context remains an owner
gap, not an absence proof. Accepted absence yields no financial numeric facts,
no direction, no clean-quality claim and no valuation authority. Other packet
evidence and the unchanged UNKNOWN_LIMIT contract remain responsible for Core.

## Freeze and Isolation

REV14 raw bytes are offline fixtures only. After exact-commit tests and integrity
checks, REV15 recollects all 22 stocks and both markets in one new generation.
No code/config changes after freeze, no old current-value reuse, no target fitting.
Only complete source replay twice can admit Market/Core/A/B. Telegram, production
DB, warning/notification, scheduler, broker, main, remote, deploy and restart are
all prohibited. Stop terminals preserve partial evidence without relabeling it.
