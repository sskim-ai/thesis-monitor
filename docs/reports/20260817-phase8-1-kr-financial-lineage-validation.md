# Phase 8.1 KR Financial Lineage Validation

## Decision

Phase 8.1 implements `financial-lineage-v2` on the experimental branch. It preserves exact OpenDART
field occurrences, keeps filing/statement/amount/comparison periods separate, and makes growth and
margin eligibility depend on their own inputs. No main merge, production deployment, database
migration, provider backfill, Telegram send, or Pilot mutation occurred.

## Before Architecture

The former provider preferred the major-account endpoint and stored selected amounts as formatted
fact strings. Formal snapshots often retained `fs_div=unknown`, while later packet metadata matched
one snapshot by date and value and copied it across all direct fields. A comparison problem could
therefore taint an aggregate earnings context and suppress an otherwise safe direct amount.

The immutable operating copy confirms this is a persistence limitation, not merely a renderer issue:
all seven active KR tickers have no historical `financial-lineage-v2` row. The copy contains 119
requested coverage cells, 60 cells with some persisted source value, and zero cells eligible for v2
promotion without recovering the original authoritative source occurrence. No such recovery was
invented. See the [coverage matrix](20260817-phase8-1-kr-financial-coverage-matrix.json).

| Layer | Input | Output | Former fail condition / overblocking risk |
|---|---|---|---|
| OpenDART provider | filing list + major/full account APIs | `RawEvent` facts | major-account rows often lost CFS/OFS |
| Snapshot parser | formatted financial facts | `FinancialSnapshot` | snapshot-level period/basis copied across fields |
| Amount-period service | snapshot and basis strings | period label/eligibility | later value/date rematch could be ambiguous |
| Financial quality | source metadata + dependencies | field eligibility | comparison taint could reach aggregate earnings |
| Valuation | quarter snapshots | EPS/PER/PBR and direct context | one latest row supplied all direct fields |
| Packet/renderer | quality-filtered canonical Facts | bound prose | safely withheld data appeared only as broad Unknown |

## Implementation

- Formal ingestion calls `fnlttSinglAcntAll` for explicit CFS and OFS scopes, selecting CFS per
  field and using OFS only for a field without an unambiguous CFS occurrence.
- Every selected source column stores receipt/report identity, account, statement type, statement
  basis, amount role/scope, dates, currency, and source-row identity.
- Duplicate candidate rows fail closed unless their full source identity is unique.
- Formal CFS, formal OFS, preliminary, and correction priority are deterministic and generic.
- Valuation selects direct revenue and operating income at field level within the current period.
- Operating margin requires homogeneous revenue and operating-income lineage.
- QoQ/YoY are calculated only after exact current/comparison compatibility; mixed CFS/OFS,
  single-quarter/YTD, account, currency, duration, or source-type mismatch returns Unknown.
- Financial quality retains the direct occurrence even when the comparison-derived field is denied.
- XBRL is parsed by XML context, not regex; only a unique exact occurrence can reconcile.

## Safe Amount Survival

The generic regression fixture verifies this boundary:

| Fact | Current source | Comparison source | Result |
|---|---|---|---|
| Operating income | verified CFS Q2, KRW | n/a | usable |
| Operating-income YoY | verified CFS Q2 | OFS prior-year quarter | withheld |

The immutable operating copy itself recovered zero historical amounts because it predates v2 and
does not retain the authoritative full-statement response needed for a safe backfill. Recovery is
therefore implementation-ready for new collection, not falsely claimed for old packets.

## Active KR Cross-Section

| Ticker | Current persisted condition | Phase 8.1 decision |
|---|---|---|
| 000660 SK hynix | formal basis unknown; CFS preliminary has critical outliers | denied earnings/PER stays denied |
| 003690 Korean Re | formal basis unknown; CFS preliminary exists | no historical promotion; new exact rows required |
| 005490 POSCO Holdings | formal basis unknown; multiple preliminary occurrences | no first-row selection; ambiguity stays closed |
| 005930 Samsung Electronics | formal basis unknown despite known amount period | no CFS inference from IS; new exact CFS row required |
| 010120 LS ELECTRIC | formal basis unknown; CFS preliminary exists | standalone recovery only after exact source selection |
| 012450 Hanwha Aerospace | formal basis unknown; CFS preliminary exists | no mixed formal/preliminary growth |
| 086280 Hyundai Glovis | formal basis unknown; CFS preliminary exists | current amount and comparison remain separate |

## Preliminary And Formal

Formal filing wins within the same period when its field lineage is verified. Preliminary evidence
remains a distinct historical source and cannot create balance-sheet or cash-flow facts. Existing
SK hynix taint remains active, so the new lineage path cannot re-expose its unsafe earnings, EPS,
PER, or qualitative earnings interpretation.

## Cash Flow Feasibility

| Metric | Status | Decision |
|---|---|---|
| OCF | PARTIAL | exact CF taxonomy/account extraction is feasible but not yet promoted |
| CAPEX | PARTIAL | heterogeneous account aggregation requires a separate contract |
| FCF | OPEN | unavailable until validated OCF and CAPEX exist on the same basis |
| Inventory | PARTIAL | exact BS account lineage required before promotion |
| ROE/ROIC | OPEN | dependency graph is not complete in this phase |

No CAPEX amount from a financing disclosure is relabeled as statement CAPEX.

## Validation

Focused suites cover CFS, OFS, unknown/conflict, single-quarter and cumulative periods, mixed basis,
account/currency mismatch, correction priority, exact XBRL duration/instant/dimensions/unit,
preliminary/formal regression, safe amount survival, and SK hynix taint. Final full suite result:
`942 passed, 1 warning`. Ruff and `git diff --check` pass.

Human message quality was not evaluated because no retrospective AI output or Telegram Preview was
created. This phase changes provider/canonical contracts only.

## Persistent Gap Status

| Gap | Status | Evidence |
|---|---|---|
| KR CFS/OFS | PARTIAL | exact future ingestion implemented; historical rows remain unknown |
| KR field-level lineage | PARTIAL | v2 contract implemented; production has not collected v2 rows |
| Safe standalone amount recovery | PARTIAL | regression passes; immutable historical recovery is 0 |
| Unsafe growth blocking | CLOSED for v2 contract | mixed basis/scope/account/currency tests fail closed |
| KR OCF | PARTIAL | exact CF taxonomy extraction still pending |
| KR CAPEX | PARTIAL | heterogeneous account aggregation unresolved |
| KR FCF | OPEN | depends on validated OCF and CAPEX |
| Massive 08:05 readiness | OPEN | no exact 08:05 normal-session observation |
| Massive rate-limit semantics | PARTIAL | official 5/min; no live headers or intentional 429 |
| Massive volume semantics | CLOSED | adjusted decimal volume identified and user-visible use denied |
