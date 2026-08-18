# Phase 8.3.2A Free-Source Peer Coverage

Assessment archive: 2026-08-18. KR price session: 2026-08-18. US price session: 2026-08-17.
Provider policy: `FREE_ONLY`. Scope: archive-only POC.

## Result

| Measure | Result |
|---|---:|
| Active subjects | 20 |
| Peer-valuation-meaningful subjects | 15 |
| `MEDIUM+` user-visible subjects | 1 |
| Raw coverage | 1/20 = 5.0% |
| Meaningful coverage | 1/15 = 6.67% |
| KR coverage | 0/7 |
| US coverage | 1/13; 1/8 meaningful |
| State distribution | MEDIUM 1, LOW 9, SUPPRESSED 5, NOT_MEANINGFUL 5 |

Only TSLA qualifies. Its exact automotive candidate group has nine independent issuers. Three have
positive, current and basis-safe TTM EPS, giving a `MEDIUM` PER sample. Nine have positive eligible
book value, but the existing PER-centered automotive message selects PER and keeps PBR in audit.

## Subject Matrix

| Market | Ticker | Framework | Selected group | Candidates | Issuers | PER | PBR | State |
|---|---|---|---|---:|---:|---:|---:|---|
| KR | 000660 | memory | KSIC division 26 | 2 | 2 | 0 | 0 | LOW |
| KR | 003690 | insurance | none | 0 | 0 | 0 | 0 | SUPPRESSED |
| KR | 005490 | steel/materials | none | 0 | 0 | 0 | 0 | SUPPRESSED |
| KR | 005930 | general/SOTP | KSIC division 26 | 2 | 2 | 0 | 0 | LOW |
| KR | 010120 | general | KSIC division 28 | 1 | 1 | 0 | 0 | LOW |
| KR | 012450 | general | KSIC division 31 | 1 | 1 | 0 | 0 | LOW |
| KR | 086280 | transport/logistics | none | 0 | 0 | 0 | 0 | SUPPRESSED |
| US | CORZ | HPC infrastructure | broad technology | 10 | 10 | 0 | 0 | NOT_MEANINGFUL |
| US | CRCL | general | broad technology | 10 | 10 | 8 | 8 | LOW |
| US | GOOGL | general | broad media | 10 | 10 | 7 | 9 | LOW |
| US | HUT | HPC infrastructure | broad technology | 9 | 9 | 0 | 0 | NOT_MEANINGFUL |
| US | IBM | general | broad technology | 9 | 9 | 7 | 8 | LOW |
| US | MU | memory | broad semiconductors | 10 | 10 | 9 | 10 | LOW |
| US | RXRX | biotech | biotech | 10 | 10 | 0 | 0 | NOT_MEANINGFUL |
| US | SKHY | memory / ADS | none | 0 | 0 | 0 | 0 | SUPPRESSED |
| US | SNDK | general | broad technology | 11 | 11 | 9 | 9 | LOW |
| US | TSLA | automotive | exact automotive | 9 | 9 | 3 | 9 | MEDIUM |
| US | TSM | semiconductor / ADR | none | 0 | 0 | 0 | 0 | SUPPRESSED |
| US | WRD | SaaS-like / depositary | none | 0 | 0 | 0 | 0 | NOT_MEANINGFUL |
| US | WULF | HPC infrastructure | broad technology | 9 | 9 | 0 | 0 | NOT_MEANINGFUL |

## Exclusions

Metric-level repeated audit reasons are: negative EPS 15, unavailable free KR current peer
valuation 12, stale denominator 4, negative equity 1, missing TTM EPS 1 and missing BVPS 1. These
are occurrence counts across subject/metric audits, not unique securities.

Broad taxonomy is the dominant user-visible suppression reason even where free metrics exist.
MU's ten semiconductor candidates are not independently verified memory issuers. CRCL, GOOGL,
IBM and SNDK receive only `Technology` or `Media` groups. Their distributions remain audit-only.

## TSLA Statistics

| Metric | Subject | Peer median | Sample | Relative position | Display |
|---|---:|---:|---:|---:|---|
| PER | 176.7188x | 23.1763x | 3 | +662.4979% | yes, MEDIUM |
| PBR | 15.4263x | 1.3206x | 9 | +1068.1281% | audit only for this message |

The PER sample is GM 40.7742x, THO 15.6485x and WGO 23.1763x. Six other automotive candidates
have non-positive TTM EPS and are excluded. This says TSLA embeds substantially different earnings
expectations; it is not an automatic `overvalued` conclusion. Automotive volume, mix, margin,
CAPEX and FCF must explain the difference.

## Value Gate

The free-only strategy has low ROI as a broad feature: 6.67% meaningful coverage despite 263
read-only requests. It does demonstrate a safe selective path. Recommendation: keep the contract
and tooling as optional archive capability, do not integrate it into operating runtime, and do not
start free forward-consensus expansion until exact-industry coverage improves materially.

## Parallel Tracks

Natural AI-assisted delivery remains `PARTIAL`. No 2026-08-19 natural artifact was present at
review time; the latest immutable evidence remains the 2026-08-18 US/KR packets whose AI drafts
failed runtime message quality and whose deterministic fallbacks delivered. Phase 8.5.3.2 remains
the operating shadow baseline.

KRX historical capability is PASS and the universe contract is CLOSED, but same-day 16:05,
next-morning 08:05 and T+1 reconciliation roles remain `NOT_YET_PROVEN`. The latest committed
publication evidence remains HTTP 200 / zero rows at 20:27, 21:02 and 21:06 KST on 2026-08-18.
This Phase does not modify KRX code, role policy or operating integration.

Persistent gaps after this POC: free peer coverage PARTIAL/selective, taxonomy PARTIAL, ADR basis
PARTIAL, forward consensus DEFERRED, historical peer PIT DEFERRED, KRX timing OPEN, natural AI
delivery PARTIAL and cash flow PARTIAL/OPEN.

Paid calls, signup and trial: 0. DB mutation, Telegram, Scheduled Task, Pilot and deployment: 0.
