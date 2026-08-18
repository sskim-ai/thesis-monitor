# Phase 8.3.2A Validation

Date: 2026-08-19

Branch: `codex/phase-8-3-2a-free-peer-poc`

Base: clean peer-only branch `e17d992c4c5d40030294eff5a74504e88ab35911`, whose merge-base
with `origin/main` is `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`.

Scope: free-source current peer POC and archive-only Human Preview. Main merge and operating
deployment are outside scope.

## Contract Result

| Gate | Result |
|---|---|
| Provider policy | PASS: `FREE_ONLY`; paid calls/signup/trial 0 |
| Candidate selection | PASS: verified taxonomy hierarchy, subject exclusion, issuer dedup |
| Security basis | PASS: common-share evidence required; ADR/ADS unsafe subjects suppressed |
| Denominator | PASS: positive EPS/BVPS, currency, period, session and freshness checks |
| Broad fallback | PASS: Technology/Media/generic semiconductor remain LOW/audit-only |
| Minimum sample | PASS: fewer than 3 independent issuers never visible |
| Industry controls | PASS: biotech/HPC/SaaS/holding suppression; no cheap/overvalued verdict |
| Numeric provenance | PASS: TSLA visible 4/4 values have exact fact/path/semantic/usage bindings |
| Renderer arithmetic | PASS: 0 calculations; precomputed Phase 8.3 statistics only |
| Historical peer PIT | PASS boundary: deferred, never claimed implemented |
| Forward peer | deferred after trailing POC value gate; no free estimate calls |

## Measured Evidence

Coverage is `MEDIUM 1`, `LOW 9`, `SUPPRESSED 5`, `NOT_MEANINGFUL 5`. Raw coverage is
1/20 (5.0%); meaningful coverage is 1/15 (6.67%). KR is 0/7. US is 1/13 overall and 1/8
meaningful. The only visible subject is TSLA. Its selected PER sample has three independent issuers,
a 23.1763x median and a canonical subject value of 176.7188x.

The fresh final collection made 263 read-only calls: Finnhub 232, OpenDART company 27, OpenDART
corp-code 1, OpenFIGI mapping 2 and SEC ticker identity 1. No endpoint requiring a paid entitlement
was retried or bypassed. Committed artifact credential exposure is zero.

The full Preview replays eleven immutable Phase 8.5.3.1 messages. TSLA alone receives a peer sentence
inside its existing Valuation section and grows 8.34%. The other ten messages are character-identical
before/after. New section count is zero and Telegram sends are zero.

## Tests

Focused service, candidate, metric, negative-control, preview and documentation tests:
`28 passed`.

Full suite: `1068 passed`, one upstream Starlette/httpx deprecation warning, zero failures.

Ruff: PASS.

`git diff --check`: PASS.

Project-state JSON, candidate audit JSON and valuation audit JSON parse: PASS.

## Knowledge And Action

Investment Knowledge parity: PASS, all three files
`559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.

Chart Knowledge parity: PASS, both files
`beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.

Public Action: `0.4.5`.

operationId: 20 total / 20 unique.

No KRX provider, universe, readiness or publication implementation appears in the Phase 8.3.2A
branch diff. KRX archived issue-reference data is read only as POC evidence and is not committed.

## Operating Safety

| Mutation | Count / state |
|---|---|
| Main merge | 0 |
| Operating deployment | 0 |
| DB migration or mutation | 0 |
| Telegram | 0 |
| Scheduled Task manual run | 0 |
| Scheduled Task config change | 0 |
| Pilot mutation | 0 |
| Production Assist | OFF |
| AI mode | shadow |

GitHub Actions Test/Lint is verified against the exact pushed final branch SHA after this report is
committed; the completion response records that external result without embedding a self-referential
commit SHA in this file.

## Decision

Engineering PASS. Human value gate: low broad-feature ROI. Continue only as selective optional
context; do not integrate into operating runtime and do not start forward expansion under current
coverage.
