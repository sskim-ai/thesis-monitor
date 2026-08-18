# Peer Data Provider Strategy

## Problem

Phase 8.3 validates peer selection, metric eligibility, point-in-time alignment, statistics, industry
guardrails, and numeric provenance, but the immutable active universe emits zero safe user-visible
peer Facts. The repository has no broad source that simultaneously proves issuer/security identity,
taxonomy, valuation denominator, date, forward basis, and display rights.

## Decision

Do not integrate a provider in Phase 8.3.1. Use official-source capability research and a small
audit-only entitlement probe to select a provider before writing an adapter. The preferred technical
shape is either:

1. one institutional global provider with explicit point-in-time and redistribution rights; or
2. a controlled KR/US split, with one authoritative provider per market and identity auxiliaries
   that never repair an unsafe valuation basis by themselves.

The initial shortlist is:

- global institutional: S&P Global Market Intelligence, FactSet, and LSEG;
- KR conditional: FnGuide FnSpace and DeepSearch, both subject to written field and licensing answers;
- US conditional cost/benefit: Intrinio, subject to commercial display, AI-processing, estimate, and
  ADR-basis rights;
- identity auxiliaries only: SEC EDGAR and OpenFIGI;
- existing supplemental sources only: Massive, Finnhub, and Alpha Vantage.

No candidate currently clears the Phase 8.3.2 entry gate. Phase 8.3.1.1 revalidates the shortlist
but leaves the overall result `BLOCKED_ON_PROVIDER_DECISION`.

## Why

An apparent PER or PBR field is not enough. A production peer row must answer which issuer and
security it represents, whether an ADR or share class is normalized, which denominator and fiscal
period were used, what was known at the comparison date, and whether the derived result may be stored
and displayed to a user. Provider breadth without those fields would weaken the contract that Phase
8.3 already proved.

## Rejected Alternative

- web-scraped valuation tables or blog data;
- ticker-specific peer lists;
- a current-only ratio endpoint presented as true point-in-time history;
- mixing restated fundamentals with historical prices without a publication timeline;
- combining provider-defined forward PE with FY1 or NTM consensus;
- using FIGI, CIK, or a ticker match as proof of ADR ratio or per-security denominator basis;
- selecting the cheapest feed before checking storage, AI-processing, and user-display rights; and
- promoting a provider because its theoretical universe is large.

## Safety Constraint

Provider data remains audit-only until all of the following are confirmed for the selected product
and entitlement:

- issuer and listed-security IDs, share class, exchange, active/delisted state;
- ADR/ADS relation and ratio where relevant;
- taxonomy with a documented crosswalk boundary;
- current PER/PBR inputs and positive denominator semantics;
- explicit price, filing, estimate, and effective dates;
- trailing, consensus-forward, and modeled-forward basis separation;
- restatement and revision-history behavior;
- license rights for storage, derived statistics, external AI processing, and Telegram display; and
- a 20-stock audit showing exact exclusions and no regression of the existing Phase 8.3 validators.

## Licensing And AI Boundary

The license gate precedes coverage. Evaluate each product and Order Form separately for internal
analytics, persistent storage, derived statistics, user-visible display, redistribution, hosted LLM
input, and AI-derived user output. Permission for an internal desktop or vendor-hosted AI feature
does not imply permission to send fields to an external LLM or publish a Telegram message.

FnSpace standard terms prohibit database construction and application/customer/third-party
exposure. Intrinio treats hosted third-party LLM transmission and external AI output as
redistribution/display and requires the applicable Startup/Enterprise Order Form. S&P, FactSet, and
LSEG provide technical AI/PIT products, but project-specific storage, downstream display, and hosted
LLM rights remain entitlement questions. `UNKNOWN_REQUIRES_VENDOR_CONFIRMATION` never becomes a
production pass.

## Time Classes

Provider claims use four distinct classes:

| Class | Meaning | Allowed use |
|---|---|---|
| `CURRENT_ONLY` | latest value without historical publication state | current audit only |
| `HISTORICAL_SERIES` | values by observation date, restatement behavior unknown | research with caution |
| `POINT_IN_TIME_RECONSTRUCTABLE` | filing/estimate timestamps permit deterministic reconstruction | candidate after validation |
| `TRUE_POINT_IN_TIME` | vendor supplies an as-known snapshot or revision feed | preferred for historical peers |

Forward estimates additionally require forecast period, estimate effective date, analyst count where
available, currency, and basic/diluted or share-basis metadata. FY1, NTM, calendar-year, modeled, and
consensus distributions remain separate.

## Provider Roles

Identity, fundamentals, and consensus may come from separate sources only when reconciliation is
explicit:

```text
issuer/security master
    -> taxonomy crosswalk
    -> point-in-time fundamentals
    -> separately identified consensus series
    -> Phase 8.3 eligibility and distribution contract
```

OpenFIGI and SEC can strengthen identifiers but do not supply valuation or ADR ratios. KRX can be an
authoritative KR market-statistics auxiliary but does not replace consensus. Massive can remain a US
price/reference source, but its latest-ratio endpoint is not a historical peer feed. A supplemental
source never upgrades a missing or denied subject metric.

## Phase 8.3.2 Entry Gate

Start integration only after the user selects a provider and the repository records:

1. credential or approved trial availability;
2. written confirmation of the mandatory fields;
3. acceptable storage, derived-display, and AI-processing rights;
4. a dated POC for Samsung or another KR representative, MU, and TSM;
5. explicit ADR/share-class results for TSM and SKHY; and
6. an observed coverage simulation rather than a marketing-universe estimate.

Until then, active user-visible peer coverage remains `0/20`, the contract stays `PASS`, capability
stays `STRONG PARTIAL`, and operating integration remains `NO`.

If a trailing provider passes before consensus history, integration may be split into Phase 8.3.2A
for current/trailing peers and Phase 8.3.2B for consensus forward. The second phase must not inherit
the first phase's license or point-in-time decision implicitly.

## Clean Integration Path

The original Phase 8.3 branch includes six KRX commits in Git ancestry but has no KRX code or schema
dependency. `codex/integration-phase-8-3-peer-only` reconstructs the peer implementation from latest
operating main, excludes all KRX provider/publication code, and reproduces the 20-stock fail-closed
audit. It is preparation only: no merge, deployment, or activation follows from its existence.
