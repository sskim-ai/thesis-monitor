# Phase 8.1.2 KR Human Quality Review

## Executive Conclusion

| Decision | Result |
|---|---|
| Data Recovery | PASS |
| Safety | PASS |
| Investment Message Quality | HOLD |
| Ready for main merge | HOLD |
| Production Assist evidence eligible | false |

Phase 8.1.1 proved that official OpenDART rows can recover useful field-level Facts. It did not prove
that those Facts improve a complete investment message. The archived AFTER artifacts are one-section
financial payloads produced by the recovery script, not complete `ai-assisted-pilot-renderer-v3`
stock messages. They omit price, supply, valuation, observer/holder, Unknown, and next-check sections.
No unsafe number or unsupported financial interpretation appears, but a list of verified figures is
not yet relational investment analysis.

This review changes no source artifact. The Phase 8.1.1 audit and Preview SHA-256 values remain
`cc5c5eb49f7f723c3ae07fd2f6481cb9c47ac554735db895a0bfbeddaf4667cf` and
`7241564cdf115b972ace42404e5fa8f8ace8ccd99909f8785fe9ebeda8c4b0d1`.

## Evidence Boundary

- Source packet: `2026-08-16-kr-run-21-049f367f0274`.
- Packet SHA-256: `20e94eff4f16d9b95e3e5e196c3c8f0b349a24b581b38c8d807cae802066b6b4`.
- Persisted message SHA-256: `202b83b805ceb39e8eb4fbed114a2754400be7da8db2e8d1a0920fe428d4edcc`.
- BEFORE: exact persisted natural-live message.
- AFTER: exact Phase 8.1.1 archive-only financial payload from the same source packet and recovered
  lineage.
- Price, supply, valuation, and market Facts were not changed, but they were not rendered into AFTER.
- No AI reanalysis, provider call, binder rerun, renderer rerun, or payload editing occurred in this
  review.

Because AFTER is not a complete schema-4 stock review, full validator and runtime final-message gate
PASS are not established for an integrated message. Phase 8.1.1 did establish automatic numeric
binding with manual, rejected, formatter, and unresolved counts all zero for the five payloads.

## Portfolio Summary

| Ticker | Recovered eligible Facts | Used Facts | Utilization | Score | Verdict | Primary remaining gap |
|---|---:|---:|---:|---:|---|---|
| 005930 | 7 | 5 | 71.4% | 8/20 | HOLD | segment-aware investment meaning |
| 005490 | 7 | 5 | 71.4% | 8/20 | HOLD | cyclical interpretation and cash conversion |
| 086280 | 7 | 5 | 71.4% | 8/20 | HOLD | divergence meaning and next condition |
| 003690 | 4 | 2 | 50.0% | 7/20 | HOLD | insurance-specific reasoning |
| 000660 | 0 | 0 | n/a | 6/20 | HOLD | safe negative control, no complete message |
| **Portfolio** | **25** | **17** | **68.0%** | **7.4/20 average** | **HOLD** | full relational renderer evidence |

Eligible Facts count verified revenue, operating income, net income, current operating margin, and
their verified same-quarter YoY relations when available. Used Facts are automatic numeric bindings
in the actual AFTER payload. Omitting a Fact is not itself an error; here the unused net-income Facts
matter because the resulting text offers no reason for their omission and no alternative relational
analysis.

## Score Matrix

| Dimension | Samsung | POSCO | Glovis | Korean Re | SK hynix |
|---|---:|---:|---:|---:|---:|
| Today relevance | 1 | 1 | 1 | 1 | 1 |
| Quantitative grounding | 2 | 2 | 2 | 2 | 0 |
| Comparison quality | 2 | 2 | 2 | 1 | 0 |
| Investment meaning | 0 | 0 | 0 | 0 | 1 |
| Industry fit | 0 | 0 | 0 | 0 | 0 |
| Delta-first | 1 | 1 | 1 | 1 | 1 |
| Observer/holder distinction | 0 | 0 | 0 | 0 | 0 |
| Unknown quality | 0 | 0 | 0 | 0 | 1 |
| Next-check quality | 0 | 0 | 0 | 0 | 0 |
| Readability | 2 | 2 | 2 | 2 | 2 |
| **Total** | **8** | **8** | **8** | **7** | **6** |

No user-visible critical financial error was found. HOLD follows from the portfolio rule that a
number list without investment meaning, industry reasoning, Unknown, next check, and full-context
rendering is not a quality-approved investment message.

## 삼성전자 (005930)

### A. Financial Fact Recovery

| Metric | Before | After | Quality | Source / basis note |
|---|---|---|---|---|
| Revenue | unavailable | 171조4,995억원 | verified_usable | Q2 single-quarter CFS |
| Operating income | amount lacked visible period/basis | 89조4,924억원 | verified_usable | Q2 single-quarter CFS |
| Operating margin | unavailable | 52.2% | verified_usable | same-period CFS dependencies |
| Revenue YoY | unavailable | 130% | verified_usable | equivalent prior Q2 CFS |
| Operating-income YoY | visible without exact lineage label | 1,813.8% | verified_usable | equivalent prior Q2 CFS |
| Net income / YoY | unavailable | eligible, not rendered | verified_usable | Q2 single-quarter CFS |

### B. Before Message

The exact persisted text is preserved under Samsung in the
[Before/After Preview](20260817-phase8-1-2-kr-before-after-preview.md#삼성전자-005930).

### C. After Message

The exact archive-only payload is preserved in the same Preview without edits.

### D. What Improved

- Amount period and consolidated basis are explicit.
- Revenue, operating income, margin, and two comparable YoY measures are numerically grounded.
- Unsupported segment attribution and unsafe derived metrics do not appear.

### E. What Still Feels Weak

- The figures are not connected to semiconductor versus non-semiconductor segment drivers.
- No relation to valuation, price structure, cash conversion, or current thesis is rendered.
- Net income is eligible but unused; no concrete Unknown or next confirmation explains the choice.

### F. Human Quality Score

`1 + 2 + 2 + 0 + 0 + 1 + 0 + 0 + 0 + 2 = 8/20`

### G. Verdict

HOLD.

## POSCO홀딩스 (005490)

### A. Financial Fact Recovery

| Metric | Before | After | Quality | Source / basis note |
|---|---|---|---|---|
| Revenue | unavailable | 19조2,587억원 | verified_usable | Q2 single-quarter CFS |
| Operating income | amount lacked visible period/basis | 8,190억원 | verified_usable | Q2 single-quarter CFS |
| Operating margin | unavailable | 4.3% | verified_usable | same-period CFS dependencies |
| Revenue YoY | unavailable | 9.7% | verified_usable | equivalent prior Q2 CFS |
| Operating-income YoY | visible without exact lineage label | 34.9% | verified_usable | equivalent prior Q2 CFS |
| Net income / YoY | unavailable | eligible, not rendered | verified_usable | Q2 single-quarter CFS |

### B. Before Message

The exact persisted text is preserved under POSCO Holdings in the
[Before/After Preview](20260817-phase8-1-2-kr-before-after-preview.md#posco홀딩스-005490).

### C. After Message

The exact archive-only payload is preserved in the same Preview without edits.

### D. What Improved

- The payload restores a coherent revenue, operating-income, margin, and YoY set.
- The numbers are period- and basis-specific rather than generic latest earnings.
- No cyclical improvement is promoted to structural growth.

### E. What Still Feels Weak

- The payload does not place the margin or growth in the steel/materials cycle.
- It does not connect earnings to PBR, FCF, ROIC, or dilution risk.
- No next condition distinguishes cyclical normalization from durable improvement.

### F. Human Quality Score

`1 + 2 + 2 + 0 + 0 + 1 + 0 + 0 + 0 + 2 = 8/20`

### G. Verdict

HOLD.

## 현대글로비스 (086280)

### A. Financial Fact Recovery

| Metric | Before | After | Quality | Source / basis note |
|---|---|---|---|---|
| Revenue | unavailable | 8조7,054억원 | verified_usable | Q2 single-quarter CFS |
| Operating income | amount lacked visible period/basis | 4,951억원 | verified_usable | Q2 single-quarter CFS |
| Operating margin | unavailable | 5.7% | verified_usable | same-period CFS dependencies |
| Revenue YoY | qualitative only | 15.8% | verified_usable | equivalent prior Q2 CFS |
| Operating-income YoY | visible without exact lineage label | -8.1% | verified_usable | equivalent prior Q2 CFS |
| Net income / YoY | unavailable | eligible, not rendered | verified_usable | Q2 single-quarter CFS |

### B. Before Message

The exact persisted text is preserved under Hyundai Glovis in the
[Before/After Preview](20260817-phase8-1-2-kr-before-after-preview.md#현대글로비스-086280).

### C. After Message

The exact archive-only payload is preserved in the same Preview without edits.

### D. What Improved

- The useful divergence between revenue growth and operating-income decline is now exact.
- Margin and CFS period labels make the current performance basis inspectable.
- Unsafe cash-flow conclusions are not inferred.

### E. What Still Feels Weak

- The divergence is not interpreted through freight, fuel, contract mix, or cash conversion.
- No price/supply balance or observer/holder distinction remains in AFTER.
- There is no condition describing what would improve or weaken the earnings-quality judgment.

### F. Human Quality Score

`1 + 2 + 2 + 0 + 0 + 1 + 0 + 0 + 0 + 2 = 8/20`

### G. Verdict

HOLD.

## 코리안리 (003690)

### A. Financial Fact Recovery

| Metric | Before | After | Quality | Source / basis note |
|---|---|---|---|---|
| Revenue | unavailable | unavailable | unknown | no exact promoted revenue occurrence |
| Operating income | amount lacked visible period/basis | 1,750억원 | verified_usable | Q2 single-quarter CFS |
| Operating-income YoY | visible without exact lineage label | 26.9% | verified_usable | equivalent prior Q2 CFS |
| Net income / YoY | unavailable | eligible, not rendered | verified_usable | Q2 single-quarter CFS |
| Operating margin | unavailable | unavailable | unknown | revenue dependency unavailable |

### B. Before Message

The exact persisted text is preserved under Korean Re in the
[Before/After Preview](20260817-phase8-1-2-kr-before-after-preview.md#코리안리-003690).

### C. After Message

The exact archive-only payload is preserved in the same Preview without edits.

### D. What Improved

- Operating income and its YoY comparison now have exact Q2 CFS lineage.
- Missing revenue is not filled with zero or inferred from an insurance metric.
- Manufacturing margin language does not leak into the payload.

### E. What Still Feels Weak

- Eligible net income and net-income YoY are omitted.
- The two displayed figures are not linked to underwriting quality, loss ratio, capital adequacy,
  investment return, or sustainable ROE.
- The payload has no insurance-specific Unknown or next check.

### F. Human Quality Score

`1 + 2 + 1 + 0 + 0 + 1 + 0 + 0 + 0 + 2 = 7/20`

### G. Verdict

HOLD.

## SK하이닉스 (000660)

### A. Financial Fact Recovery

| Metric | Before | After | Quality | Source / basis note |
|---|---|---|---|---|
| Revenue | denied | denied | denied | prior critical quality conflict retained |
| Operating income | denied | denied | denied | prior critical quality conflict retained |
| Margin | denied/unknown | unknown | denied dependency | unsafe earnings remain blocked |
| EPS / PER / historical PE | denied | not rendered | denied | no automatic valuation recovery |
| Inventory | unavailable in AFTER | eligible audit Fact, not rendered | verified_usable | Q2 CFS balance-sheet Fact |

### B. Before Message

The exact persisted text is preserved under SK hynix in the
[Before/After Preview](20260817-phase8-1-2-kr-before-after-preview.md#sk하이닉스-000660).

### C. After Message

The exact archive-only payload is preserved in the same Preview without edits.

### D. What Improved

- The new source rows do not override the existing critical quality conflict.
- Unsafe revenue, operating income, margin, EPS, PER, and historical PE remain absent.
- The payload states the safety disposition instead of inventing a replacement estimate.

### E. What Still Feels Weak

- The denial reason is accurate but not specific enough for a user to understand the conflicting
  profitability relationship.
- Safe inventory and existing independent PBR/chart Facts are absent because AFTER is not complete.
- No HBM-specific Unknown, observer/holder distinction, or next confirmation is rendered.

### F. Human Quality Score

`1 + 0 + 0 + 1 + 0 + 1 + 0 + 1 + 0 + 2 = 6/20`

### G. Verdict

HOLD for message quality; PASS as the negative-control safety fixture.

## Cross-Portfolio Findings

### What Improved

- The four numerically eligible companies present exact quarter and consolidated-basis labels.
- Automatic binding uses 17 recovered Facts; unsupported numeric and qualitative financial claims
  are both zero.
- Mixed CFS/OFS, single-quarter/YTD, unsafe growth, and SK hynix taint leakage remain zero.
- Korean amount formatting and postpositions in the AFTER payloads are clean.

### Repeated Weakness

`최근 정식 공시에서 확인한 항목입니다` is the substantive opening template for four companies.
Company names and numbers change, but no company-specific relation follows. The six phrases listed
in the work order do not otherwise dominate AFTER; the larger issue is omission rather than verbose
repetition.

### Delta-First

Recovered figures appear early in four payloads, but none states what changed relative to the prior
review or why that delta matters today. Mechanical early placement is 4/5; substantive delta-first
reasoning is 0/5.

### Industry Reasoning

| Ticker | Primary framework | Actual AFTER reasoning | Fit |
|---|---|---|---|
| 005930 | semiconductor / electronics mix | none beyond figures | missing |
| 005490 | cyclical steel and materials | none beyond figures | missing |
| 086280 | transport and logistics | none beyond figures | missing |
| 003690 | reinsurance | none beyond figures | missing |
| 000660 | memory semiconductor | safety denial only | safe but incomplete |

No wrong industry framework appears; industry reasoning is absent.

### Message Length And Balance

BEFORE averages 1,262 characters, 37.8 lines, and seven to nine user sections. AFTER averages 193
characters, 9.4 lines, and one section. AFTER is not too long; it is too incomplete for a full-message
quality comparison. Financial analysis does not crowd out price/supply. Instead, those sections are
missing entirely.

### Unknown And Next Checks

Good Unknown count is zero. Four payloads provide no Unknown; SK hynix names a critical quality
conflict but not the conflicting relationship or the Fact needed to resolve it. Concrete next-check
count is zero. Observer/holder distinction is absent in all five AFTER payloads.

### Peer Valuation And Cash Flow

No AFTER payload links recovered earnings to a comparable historical or peer valuation Fact. Peer
valuation remains an open capability gap. Cash-conversion evidence is material for Samsung, POSCO,
Hyundai Glovis, and SK hynix, so four of five reviews remain constrained by OCF/CAPEX/FCF coverage.

## Validator And Safety Disposition

| Check | Result |
|---|---|
| Numeric provenance | PASS for all 17 rendered references |
| Manual / rejected / formatter / unresolved | 0 / 0 / 0 / 0 |
| Financial quality and lineage | PASS |
| Statement basis and amount period | PASS |
| Unsafe growth leakage | 0 |
| Unsupported financial numeric claims | 0 |
| Unsupported qualitative financial interpretations | 0 |
| SK hynix safety regression | 0 |
| Integrated schema-4 full validator | NOT PROVEN; AFTER is not a full stock review |
| Runtime renderer quality gate | NOT PROVEN; AFTER is a financial-only recovery payload |

The NOT PROVEN results are evidence gaps, not validator failures. They block merge readiness and
human quality approval until a complete archive-only output is produced through the actual runtime
renderer and validators without AI reanalysis or source mutation.

## Persistent Gap Status

| Gap | Status | Classification |
|---|---|---|
| KR CFS/OFS | PARTIAL | latest shadow recovered; production not promoted |
| KR Field-Level Lineage | PARTIAL | engineering path works; operating persistence remains legacy |
| Safe Standalone Recovery | CLOSED | actual verified amounts recovered |
| Unsafe Growth Blocking | CLOSED | unsafe comparisons remain withheld |
| Investment Meaning | OPEN | figures are not related to thesis, valuation, or decision |
| Delta-First | OPEN | substantive current-versus-prior delta absent |
| Industry Reasoning | OPEN | no company-specific framework in AFTER |
| Message Length | PARTIAL | concise, but only because complete sections are omitted |
| Korean UX | PARTIAL | wording is clean; repeated generic opening remains |
| Unknown Quality | OPEN | concrete user-facing Unknown absent |
| Next Check Quality | OPEN | no judgment-changing next condition |
| Peer Valuation | OPEN | no verified peer relation used |
| Cash Flow | OPEN | OCF/CAPEX/FCF cannot support cash-conversion analysis |
| Natural Live Validation | OPEN | no deployed integrated message has been observed |

Engineering gaps already closed remain closed. Message-quality gaps are tracked separately.

## Recommendation

Do not merge or deploy based on these artifacts. Prioritize Phase 8.4 Delta-First Adaptive Renderer
to produce a complete same-context archive-only message that preserves price/supply/valuation while
integrating selected recovered Facts, concrete Unknowns, next checks, and observer/holder views.
Follow with Phase 8.5 Industry-Specific Reasoning. If KRX approval arrives, Phase 8.2A may be inserted
before those steps. Phase 8.3 peer/sector valuation remains useful, but adding more data before the
renderer can convert existing verified Facts into relational analysis would not solve this HOLD.

## Mutation Audit

| Mutation | Count |
|---|---:|
| Telegram sends | 0 |
| Operating DB writes | 0 |
| Assessment changes | 0 |
| Packet/output/archive rewrites | 0 |
| Pilot changes | 0 |
| Scheduled Task changes/runs | 0 |
| Production Assist changes | 0 |
| Provider calls | 0 |
| Main merge / operating deployment | 0 |

The operating DB SHA-256 remains
`c9a76f463f4e86862e65fae1fe51ab2b62dc8318c0b7bb95655c4ba9415a6726`; Pilot state remains
`ec77edaedcee670d86e3fbcf266813f96761dac1130c4466f2508d0f4a698e91`. Runtime remains KR 3/5
and US 3/5, AI mode `shadow`, and Production Assist OFF.

## Validation

- `pytest -q`: 951 passed; one pre-existing Starlette/httpx deprecation warning.
- `ruff check .`: PASS.
- `git diff --check`: PASS.
- Investment Knowledge canonical/upload/runtime SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Chart Knowledge canonical/runtime SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.
- Public Action: 0.4.5 with 20/20 unique operation IDs.
- Output schema: 4; DB migration: none.
