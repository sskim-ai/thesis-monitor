# Phase 8.3 Finalization

Date: 2026-08-19
Branch: `codex/phase-8-3-finalization`
Base: Phase 8.3.2A `ad1b98a4a28a1c18a02cb09f3a57e753dbd032b5`
Operating main: `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`

## Final Status

| Dimension | Result |
|---|---|
| Phase 8.3 contract | PASS |
| Peer selection and safety | PASS |
| Provider policy | `FREE_ONLY` |
| Paid provider path | `CLOSED_BY_POLICY` |
| Broad runtime value | `LOW_ROI` |
| Feature scope | `SELECTIVE_OPTIONAL_CONTEXT` |
| Operating integration | NO |
| Historical peer PIT | DEFERRED |
| Forward peer | DEFERRED |
| Phase status | FINALIZED on the current roadmap |

## Coverage Truth

| State | Subjects |
|---|---:|
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 9 |
| SUPPRESSED | 5 |
| NOT_MEANINGFUL | 5 |
| MEDIUM+ / active | 1 / 20 (5.0%) |
| MEDIUM+ / meaningful | 1 / 15 (6.67%) |
| KR | 0 / 7 |
| US | 1 / 13 |

The single MEDIUM subject is TSLA. `NOT_MEANINGFUL` is correct suppression for frameworks where a
generic PER/PBR peer statistic would not be economically useful; it is not treated as a failed
coverage target.

## ROI Decision

The Phase 8.3.2A audit used 263 read-only requests, including 232 Finnhub requests, to produce one
visible MEDIUM context. That result proves the fail-closed contract works, but it does not justify
daily broad collection or continued coverage expansion. Five clean contexts would be preferable to
ten unsafe ones; no denominator, identity, taxonomy or sample rule is relaxed.

## Retained

- `peer-sector-valuation-v1` and `verified-profile-peers-v2`;
- free-source assembly and current-multiple eligibility;
- issuer deduplication and security/share-basis checks;
- statistics, numeric semantics, provenance and validators;
- audit artifacts and the clean peer-only branch.

## Stopped

- broad provider and paid-provider expansion;
- daily broad peer runtime collection;
- free forward-consensus expansion;
- historical peer PIT work;
- coverage-driven taxonomy widening;
- KR broad-industry promotion to compensate for measured 0/7 coverage.

Reopen only if verified taxonomy or free valuation coverage improves materially, a new safe free
source appears, an exact industry group reliably reaches three clean issuers, or natural operating
message review establishes a new decision-relevant peer need.

## TSLA Wording

The visible numbers and `MEDIUM` state are unchanged. The generic formatter now says “same
classification, current-multiple-comparable listed companies, baseline group” and explicitly limits
economic comparability. It does not add Robotaxi, software, AI or autonomy claims.

## Parallel State

No natural US/KR artifact newer than the 2026-08-18 fallback sessions was present at finalization.
Natural AI-assisted delivery remains `PARTIAL`. KRX historical capability remains PASS, but 16:05,
08:05 and T+1 roles remain `NOT_YET_PROVEN`; no new exact-slot telemetry was present.

## Next Decision

State: `WAIT_FOR_NATURAL_US_KR_REVIEW`.

If the next natural message review identifies a critical blocker, perform a targeted runtime repair.
If it passes, the default candidate is Cash Flow / Capital Efficiency Enrichment: OCF, CAPEX, FCF,
ROIC, relevant ROE, inventory, working capital, cash conversion and segment margin. This phase does
not start that work.

## Safety

Main merge, operating deployment, DB migration, Telegram send, Scheduled Task execution/config,
Pilot mutation and Production Assist activation: 0. Production Assist remains OFF; AI mode remains
shadow. No branch was deleted, force-pushed or rewritten.

## Validation

| Gate | Result |
|---|---|
| Focused wording/documentation tests | 18 passed |
| Full pytest | 1,068 passed, one upstream Starlette/httpx deprecation warning |
| Ruff | PASS |
| Git diff check | PASS |
| Investment Knowledge parity | PASS, three files at `559ad45e...a5a9d18` |
| Chart Knowledge parity | PASS, two files at `beee6455...0ede19b` |
| Public Action | `0.4.5` |
| operationId | 20 / 20 unique |
| GitHub Actions | verify Test/Lint against the exact final SHA after push |
