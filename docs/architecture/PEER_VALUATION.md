# Peer Valuation

> Historical Phase 7 foundation. Phase 8.3 extends this contract with issuer deduplication,
> exchange-session alignment, forward-basis separation, quality classes and industry guardrails in
> [PEER_SECTOR_VALUATION.md](PEER_SECTOR_VALUATION.md). The extension remains experimental and is
> not deployed.

## Problem

Company multiples and historical percentiles do not show how a company compares with current peers.
The repository also has no broad, point-in-time peer valuation provider, so an apparent sector
average could easily be incomplete, stale, or hindsight-contaminated.

## Decision

Use a deterministic, fail-closed peer contract. The initial provider is explicitly limited to
same-date final assessments in the active monitored universe. It is not presented as the full market
or industry. A peer fact is prose-eligible only when the verified profile, geography, metric basis,
date, denominator, and minimum sample all pass.

## Why

This produces auditable relative context when comparable observations exist and honest
unavailability when they do not. A future broad provider can implement the same contract without
changing the AI boundary.

## Rejected Alternative

- Asking Codex or web search to fill peer multiples.
- Hard-coding peers by ticker.
- Calling a monitored-universe sample an industry average.
- Including loss-making P/E, negative/invalid P/B, stale prices, future filings, or unsafe ADR bases.
- Using a mean alone when outliers dominate the distribution.

## Safety Constraint

- Peer selection starts from verified taxonomy, then industry, then sector.
- KR companies prefer KR peers and US companies prefer US peers.
- The minimum is three comparable peers excluding the subject company.
- Median is primary; mean and 25th/75th percentiles are audit context.
- Modeled and consensus bases are never mixed.
- Preliminary earnings, ADR/ADS, currency, and historical-comparability safeguards remain active.
- Biotech and other unsuitable frameworks are not forced into P/E comparison.

## Eligibility And Calculation

Trailing P/E requires positive TTM EPS, a positive value, a `value` status, comparable security/share
basis, same-date price, and no future denominator filing. P/B requires positive BVPS and the
equivalent price/share-basis checks. Biotechnology and similar profiles do not receive mandatory
peer P/E. The backend calculates:

```text
company versus peer median (%) = (company multiple / peer median - 1) * 100
```

The AI never performs this arithmetic. Each snapshot stores provider, group and version, as-of date,
sample quality, metric summaries, included peers, excluded peers, and exclusion reasons.

## Current Availability

At the 2026-08-14 retrospective, the repository had no broad KR or US peer valuation provider. The
20 active monitored assessments produced no peer metric meeting the full sample and comparability
contract. Results therefore remain unavailable instead of inventing a median. This is a known data
gap, not a validator failure.

## User Semantics

When available, the message says `limited verified peer sample` unless a future provider proves
broader coverage. Historical percentile and peer premium are separate:

- historical percentile describes rank within the company's comparable history;
- peer premium/discount describes the current multiple relative to the current peer median.

Neither is an automatic overvaluation verdict.
