# Bounded Official Financial Owner

Contract: `bounded-official-financial-acquisition-v1`.
Scope: opt-in, private source prequalification only. No production registration,
model call, renderer, delivery, production persistence or deployment.

## Stage Ownership

- Identity: frozen canonical local security/company/CIK/corp and issuer class.
- SEC discovery: one recent submissions response, finite 550-day window reused
  from existing official enrichment. Domestic 10-Q/10-K; FPI/ADR 6-K/20-F.
  Unread historical submission files overlapping that window deny completeness.
- SEC selection: report period, filing date and accession, never financial value.
  Domestic current plus comparable prior; foreign at most one current and one
  prior per allowed form. No amendment/version inference or ticker exceptions.
- SEC documents: Company Facts once; domestic primary document once per filing;
  foreign index, primary and at most two explicitly linked financial exhibits.
  More exhibits is `SEC_DOCUMENT_BOUND_EXHAUSTED`, not silent truncation.
- DART discovery: existing `authoritative_filings` after at most two list pages;
  response `total_page` cannot expand the plan. At most 200 candidates.
- DART documents: one selected current and prior-year comparable report,
  at most CFS and OFS full statements for each. No implicit XBRL or news fetch.
- Extraction: existing Company Facts, foreign statement-table and OpenDART
  field/column parsers. Source bytes, successful receipt, issuer, filing,
  occurrence, period, unit and basis remain bound.
- Quality: existing field-owned SEC, reported OpenDART observation and foreign
  comparative owners. Clean siblings can survive only under those owners.
  No threshold change, taint erasure or new financial-sector exception.
- Consumption: existing canonical `earnings_comparison` constructor, typed
  evidence builder and strict numeric registry. An explicit shadow-only adapter
  binds exactly current, prior, difference and comparable growth for the three
  permitted metrics after the comparative owner reconstructs each Fact. These
  numeric entries are audit-only, not prose-enabled. The production resolver
  is byte-unchanged; any other numeric field remains a packet blocker.

## Bounds

`maximum_logical = discovery + companyfacts + (current + prior) *
(documents_per_filing + indexes_per_filing)`.

| Class | Discovery | Candidates | Current/Prior | Docs/Filing | Index/Filing | Total |
|---|---:|---:|---:|---:|---:|---:|
| SEC domestic | 1 | 32 | 1/1 | 1 | 0 | 4 |
| SEC foreign/ADR | 1 | 128 | 2/2 | 3 | 1 | 18 |
| OpenDART | 2 | 200 | 1/1 | 2 | 0 | 6 |

These are conservative resource policies, not completeness guarantees. Current
and prior selection plus exact source context determines what can be admitted.
The plan emits named SEC/DART cap constants and all provider budget totals.
Every response-dependent selected filing/document request is frozen on disk
before dispatch. Request bodies/parameters cannot change across retries.

Timeout is 600 seconds wall time per HTTP attempt, at most two transient retries.
Only network/timeouts and explicitly retryable transient provider statuses are
retryable. Semantic/schema/identity/lineage/quality denials are not. Redirects
are disabled; the runner checks frozen code/config before each attempt.

## Period and Use

Raw amounts do not authorize business direction. A comparison requires exact
compatible current/prior period, semantic, issuer, currency, scale and basis,
and the existing comparative owner's PASS. A supplemental candidate-pair
audit never grants source-use authority. No Q/YTD/FY conversion or FX occurs.
Latest period selection never substitutes a past successful comparison for a
newer selected period. Ambiguous same-period observations are denied.

The R4 price/session corpus remains immutable. A new financial cutoff is a
separate time domain, not a new price observation or a production snapshot.
Serialized legacy numeric registries are compared as exact row multisets before
normalizing traversal order on a detached validation copy. The original packet
hash, every numeric row, source graph binding and multiplicity must match first;
the unchanged legacy validator then checks all other ownership dimensions.
005930, 047810 and SNDK keep their complete R4 result byte-equivalent. All other
subjects are attempted independently unless a trust/budget/config systemic
stop occurs. A source-owner PASS does not imply packet or next-phase PASS.
