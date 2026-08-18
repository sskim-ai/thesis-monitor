# Peer / Sector Valuation Intelligence

## Status And Scope

`peer-sector-valuation-v1` is an experimental Phase 8.3 contract. It extends the Phase 7
`verified-profile-peers-v1` foundation without changing the operating checkout. The current provider
is still limited to final assessments in the active monitored universe. It is not a complete market,
sector, or industry dataset.

The contract answers a narrower question than an absolute or historical valuation:

```text
current absolute multiple
    + own historical distribution
    + current comparable-issuer cross-section
    + industry driver differences
    = valuation context, not an automatic verdict
```

## Provider Boundary

The repository has no broad point-in-time peer valuation provider. Current sources contribute only
parts of the contract:

| Source | Role | Boundary |
|---|---|---|
| OpenDART-derived snapshots | KR trailing EPS, book value, PER/PBR inputs | monitored issuers only |
| SEC Company Facts-derived snapshots | US trailing EPS/book inputs | monitored issuers only |
| Finnhub | selected US provider multiples and forward consensus reference | denominator period and security basis are often partial |
| Alpha Vantage | selected analyst estimate input | not a broad comparable-universe service |
| Massive | US price/reference and market breadth | not treated as a fundamental valuation provider |
| KRX Open API | KR index/breadth development | not treated as a peer PER/PBR provider |

Web search never becomes a canonical current peer number. A future provider must implement this
same contract with explicit price date, denominator period, security basis, source, and issuer
identity.

## Comparable Universe

Candidate selection is deterministic and contains no ticker peer lists. The hierarchy is:

1. verified taxonomy;
2. verified sub-industry when an official description adds narrower information;
3. verified industry;
4. verified sector as audit-only broad fallback.

Candidates prefer the subject's market. Cross-market comparison is not enabled by the current
active-universe provider. A statistic requires at least three eligible independent issuers,
excluding the subject. Five or more eligible issuers is `HIGH`, three or four is `MEDIUM`, and fewer
than three is `LOW`. A sector fallback remains `LOW` regardless of row count and cannot create a
user-visible peer Fact.

`canonical_company_id` collapses multiple securities only when identity provenance is authoritative,
deterministic-reference, or explicit-local verified. One security is retained deterministically and
the rest are audited as `same_issuer_duplicate`. Inferred ticker identity does not claim reliable
cross-security issuer equivalence.

## Point-In-Time Contract

Assessment date and exchange price session are distinct. A 2026-08-18 KST US assessment can validly
use the completed 2026-08-17 XNYS session. The subject's `price_as_of` defines the comparison session;
every peer metric must use that same exchange-session date. Comparing directly to the KST assessment
date would incorrectly reject every natural US peer observation.

Denominator filings must not be from the future relative to the price session. Exact denominator
periods are preferred. Missing period metadata creates a caution; materially incompatible periods
are excluded. Historical observations stored after the fact do not become point-in-time evidence for
an earlier session.

## Metric Eligibility

Each metric basis is a separate distribution:

- `trailing_pe`: positive TTM EPS, positive multiple, value status, comparable share basis;
- `price_to_book`: positive BVPS/equity, positive multiple, value status, comparable share basis;
- `forward_pe_consensus`: positive forward EPS and explicit `consensus_forward` source;
- `forward_pe_modeled`: positive forward EPS and explicit `modeled_forward` source;
- forward P/B uses the equivalent split and book denominator.

Consensus and modeled forward values never share a sample. Depositary-security basis that is unknown
or not normalized is excluded. Negative EPS is `negative_eps`; negative book equity is
`negative_equity`; stale date, period mismatch, provider conflict, and unsafe security basis retain
separate audit reasons. Missing is never zero.

## Statistics

The backend, never the renderer or AI, calculates:

```text
median
mean
Q1 / Q3 / IQR
minimum / maximum
eligible issuer count
subject relative multiple = subject / peer median
premium or discount (%) = (subject / peer median - 1) * 100
subject cross-sectional percentile
```

Median is primary. Mean, quartiles, range, and candidate rows are audit context. A user-visible Fact
contains only a validated summary and labels the source as a limited active-monitoring sample.
Own-history percentile and peer cross-section percentile have distinct semantics and labels.

## Industry Interpretation

Relative position does not replace `industry-specific-reasoning-v1`:

- semiconductors require cycle normalization, mix/utilization, CAPEX and cash conversion;
- insurance PBR requires ROE, underwriting quality and capital adequacy;
- transport/logistics requires rate, volume, fuel, contract mix and mid-cycle cash conversion;
- steel/materials requires spread, inventory and normalized earnings;
- automotive requires volume, mix, incentives, margin and FCF;
- biotech suppresses generic PER/PBR peer conclusions in favor of runway, milestones and dilution;
- HPC/crypto infrastructure, SaaS and holding companies suppress generic PER/PBR when the required
  economic metric is absent.

Peer discount is context, not `cheap`; peer premium is context, not `overvalued`. A dedicated
industry guardrail rejects language that turns relative multiple alone into that verdict.

## Canonical And AI Boundary

When a metric is `MEDIUM` or `HIGH`, monitoring state may emit `valuation:peer` with subject value,
peer median, sample count, relative multiple, premium/discount and cross-sectional percentile.
Every visible number follows the normal numeric registry and binder path. Raw candidate rows remain
in the audit state and do not enter the AI packet.

If no metric qualifies, the current absolute, own-history and industry reasoning paths remain
unchanged. The renderer does not print an empty peer section and does not calculate a replacement.

## Current Capability Result

The immutable 2026-08-18 active universe contains 7 KR and 13 US assessments. It produced zero
user-visible peer states under the full Phase 8.3 contract. KR mandatory fixtures lack three verified
same-market comparable issuers. US technology groups fall to a broad sector sample, while finance
services candidates lose eligibility through economic mismatch, negative denominators, or small
clean samples. TSM and SKHY depositary bases remain unsafe for trailing peer comparison. This is a
data coverage result, not a validator failure.

The implementation is therefore `STRONG PARTIAL`: selection, safety, statistics, canonical semantics
and audit contracts pass, but broad point-in-time provider coverage remains open. It is development
only and is not integrated, active, merged to main, or deployed.

