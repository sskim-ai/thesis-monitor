# Phase 8.1.1 Authoritative Financial Recovery

## Decision

Phase 8.1.1 closes the Phase 8.1 evidence gap at the archive-only shadow boundary. Recent formal
OpenDART rows now feed `financial-lineage-v2`, and actual safe standalone financial amounts are
recovered without rewriting the operating database or historical assessments. The branch is not
merged or deployed. Telegram, Pilot, Scheduled Tasks, Production Assist, and the operating checkout
are unchanged.

## Repository And Isolation

| Item | Result |
|---|---|
| Branch | `codex/phase-8-1-1-authoritative-financial-recovery` |
| Base | `7307cbd15c1b437b8ec5dcb7257783e42c575391` |
| Production main / operating checkout | `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` |
| Source DB copy SHA-256 | `d1b4b121d11005952bd050ca5d0c0c1056b310d223afb4f6db57ae00086936fd` |
| Source KR packet | `2026-08-16-kr-run-21-049f367f0274` |
| Packet SHA-256 | `20e94eff4f16d9b95e3e5e196c3c8f0b349a24b581b38c8d807cae802066b6b4` |
| Persisted message SHA-256 | `202b83b805ceb39e8eb4fbed114a2754400be7da8db2e8d1a0920fe428d4edcc` |
| DB migration | none |
| Runtime Pilot | KR 3/5, US 3/5 |
| Production Assist | OFF |

The operating DB is read through a consistent local copy. Raw source envelopes and XBRL archives
are stored only in the ignored recovery cache. They contain no API key. The committed
[audit JSON](20260817-phase8-1-1-authoritative-financial-recovery-audit.json) contains sanitized
lineage, source identities, hashes, and result counts.

## Source Recovery

The client used the official periodic-filing list with original and correction reports included,
then selected the latest authoritative filing for each requested economic period. Each latest H1
filing was queried in both full-statement scopes.

| Ticker | Company | Latest receipt | CFS rows | OFS rows |
|---|---|---:|---:|---:|
| 000660 | SK hynix | `20260814003509` | 247 | 176 |
| 003690 | Korean Re | `20260814003862` | 355 | 301 |
| 005490 | POSCO Holdings | `20260814000957` | 256 | 156 |
| 005930 | Samsung Electronics | `20260814003699` | 223 | 145 |
| 010120 | LS ELECTRIC | `20260814003088` | 322 | 218 |
| 012450 | Hanwha Aerospace | `20260814003198` | 205 | 161 |
| 086280 | Hyundai Glovis | `20260814002854` | 210 | 134 |
| **Total** | | **7 filings** | **1,818** | **1,291** |

Six correction filings were retained in discovery history. None superseded the selected 2026 H1
filing. There were no list, CFS, OFS, or corp-code failures. Account ID is primary; bounded exact
aliases are fallback only. Multiple occurrences fail closed, and an ambiguous CFS field cannot be
replaced by OFS.

## Field-Level Promotion

| Ticker | Revenue | Operating income | Net income | Margin | Inventory | OCF |
|---|---|---|---|---|---|---|
| 000660 | denied | denied | denied | unknown | verified | unknown |
| 003690 | unknown | verified | verified | unknown | unknown | unknown |
| 005490 | verified | verified | verified | verified | verified | unknown |
| 005930 | verified | verified | verified | verified | verified | unknown |
| 010120 | verified | verified | verified | verified | verified | unknown |
| 012450 | verified | verified | verified | verified | verified | unknown |
| 086280 | verified | verified | verified | verified | verified | unknown |

Results across the seven tickers:

- 37 safe direct Facts;
- 17 safe revenue, operating-income, or net-income amounts;
- five safe current operating margins;
- six safe inventory Facts;
- 17 verified same-quarter YoY calculations;
- three YoY calculations withheld;
- three direct SK hynix income fields still denied.

The source packet had zero historical `financial-lineage-v2` rows. The After path therefore proves
real recovery rather than relabeling legacy values. Current and prior-year three-month occurrences
are separate Facts before growth calculation. Account, statement basis, amount scope, duration,
currency, and formal source type must all match. A safe current amount survives when its comparison
is absent or incompatible.

## Representative Before And After

The [Before / After Preview](20260817-phase8-1-1-kr-financial-preview.md) preserves each source
natural-live message and places a newly bound archive-only financial payload beside it.

| Company | Before v2 evidence | Recovered user-visible result |
|---|---|---|
| Samsung | no v2 occurrence | Q2 consolidated revenue, operating income, margin, and exact YoY |
| POSCO Holdings | no v2 occurrence | Q2 consolidated revenue, operating income, margin, and exact YoY |
| Hyundai Glovis | no v2 occurrence | Q2 consolidated revenue, operating income, margin, and exact YoY |
| Korean Re | no v2 occurrence | Q2 consolidated operating income and exact YoY; revenue remains Unknown |
| SK hynix | denied aggregate earnings | no income recovery; existing critical conflict remains authoritative |

All five shadow messages use automatic numeric binding. Manual binding, rejected binding,
formatting errors, and unresolved placeholders are zero. They remain
`pending_work_human_review`; automated success is not investment-message approval.

## XBRL And Cash Flow

Structured rows were sufficient for direct income-statement and balance-sheet promotion. XBRL was
entered only for seven interim OCF rows whose structured column could not prove duration. The cold
cache downloaded seven filing archives; exact reconciliation found zero unique period, unit, and
statement-basis matches. OCF therefore remains Unknown. A subsequent reproducibility run reused all
seven XBRL archives.

Exact taxonomy scanning found 28 CFS/OFS PPE and intangible-acquisition component candidates. Their
classification is auditable, but none has an aggregation-eligible period contract. CAPEX is
PARTIAL, FCF is OPEN, and no cash-flow value appears in the Preview. Inventory is safely available
for six of seven companies. ROE and ROIC remain outside this phase.

## Massive Shadow

No new exact 08:05 KST normal-session observation occurred during this work. Massive readiness
remains `NOT_YET_OBSERVED`. The one-trading-session reference-cache policy, conservative free-plan
rate handling, split-adjusted decimal volume audit semantic, and user-visible total-volume denial are
unchanged. Scheduled Task times were not modified.

## Safety And Mutation Audit

| Mutation | Count |
|---|---:|
| Telegram sends | 0 |
| Operating DB writes | 0 |
| Assessment changes | 0 |
| Existing packet/output/archive changes | 0 |
| Pilot changes | 0 |
| Scheduled Task changes/runs | 0 |
| Production Assist changes | 0 |
| Main merge / operating deployment | 0 |

The operating DB and Pilot SHA-256 values remained
`c9a76f463f4e86862e65fae1fe51ab2b62dc8318c0b7bb95655c4ba9415a6726` and
`ec77edaedcee670d86e3fbcf266813f96761dac1130c4466f2508d0f4a698e91` after collection.

## Validation

Focused financial recovery, CFS/OFS, amount-period, XBRL, taint, and basis suites pass. The final
full run completed with 951 passing tests and one pre-existing Starlette/httpx deprecation warning.
Ruff and `git diff --check` pass. Knowledge mirrors retain their required SHA-256 values, Public
Action remains 0.4.5 with 20/20 unique operation IDs, output schema remains 4, and no migration was
added. Exact GitHub Actions results are checked against the final pushed commit.

Official API contracts used by the recovery path:

- [OpenDART full financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020)
- [OpenDART original XBRL financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019019)
- [OpenDART filing list](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)

## Persistent Gap Status

| Gap | Status | Reason |
|---|---|---|
| KR CFS/OFS | PARTIAL | latest active-universe shadow closed; production promotion not approved |
| KR field-level lineage | PARTIAL | actual rows recovered in shadow; operating DB remains legacy |
| Safe standalone recovery | CLOSED for latest shadow | 17 income-statement amounts actually recovered |
| Unsafe growth blocking | CLOSED | mixed or missing comparison remains withheld |
| XBRL fallback | PARTIAL | conditional path works; seven real attempts resolved zero |
| KR OCF | PARTIAL | exact account exists, exact duration/basis does not |
| KR CAPEX | PARTIAL | 28 components found, zero aggregation-eligible |
| KR FCF | OPEN | depends on verified OCF and CAPEX |
| Inventory | PARTIAL | six of seven latest filings verified |
| Massive 08:05 readiness | OPEN | no exact normal-session observation |

## Remaining Gaps

Production promotion needs a separate review and approval. QoQ and TTM were not expanded because
the latest filing already recovered useful standalone and same-quarter YoY Facts; no PER or
historical PE eligibility is inferred from this shadow work. OCF requires stronger XBRL
statement-basis evidence, and CAPEX needs a company-neutral aggregation contract. The corrected
messages still require direct Work review before any merge or deployment decision.
