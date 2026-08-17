# Phase 8.5 Industry-Specific Reasoning Audit

## Executive Conclusion

`industry-specific-reasoning-v1` is implemented and passes archive-only full-message validation.
The result is **strong PARTIAL**: the evidence boundary and supported framework contracts are ready,
but only 9 of 20 active immutable KR/US stock packets have a verified specialized primary route.
The remaining 11 correctly use `general` rather than being inferred from thesis or theme prose.

No Investment Knowledge or Chart Knowledge source was changed. Telegram sends, provider calls,
production DB writes, archive rewrites, assessment mutations, delivery mutations, and Pilot
mutations were all zero.

## Active-Universe Coverage

| Confidence | Count |
|---|---:|
| High | 9 |
| Medium | 0 |
| Low/general fallback | 11 |

| Primary framework | Count |
|---|---:|
| General | 11 |
| Semiconductor | 4 |
| Automotive | 1 |
| Biotech | 1 |
| Insurance | 1 |
| Steel/materials | 1 |
| Transport/logistics | 1 |

The active immutable set contains seven KR and thirteen US stocks. Memory, foundry, and HPC
contracts exist and are tested, but current profile evidence does not justify those exact primary
labels for MU, TSM, or WULF. MU and TSM remain `semiconductor`; WULF remains `general` with a
hyperscaler-CAPEX secondary context.

## KR Representative Audit

| Ticker | Framework | Confidence | Used drivers and meaning | Missing drivers retained |
|---|---|---|---|---|
| 005930 Samsung | general | Low | verified company revenue, operating income/margin, valuation and price; no segment attribution | OCF, balance-sheet and segment contribution |
| 005490 POSCO | steel/materials | High | revenue/margin plus mixed PER/PBR relation; PBR alone is not a cheap conclusion | spread, raw material, utilization, inventory, normalized earnings, OCF |
| 086280 Hyundai Glovis | transport/logistics | High | external growth versus profit direction, margin, RR and own history | volume, freight, fuel, contract mix, working capital, OCF |
| 003690 Korean Re | insurance | High | earnings and company valuation with an explicit ROE/capital boundary | loss/combined ratio, investment yield, ROE, capital adequacy |
| 000660 SK hynix | semiconductor | High | safe PBR, own-history, price and supply only | segment mix, utilization, CAPEX, FCF; denied earnings remain blocked |

Samsung's `general` route is intentional. The verified profile says Communications Equipment and
the packet has no authoritative segment classification. The previous priority-watch HBM text is no
longer allowed to promote the primary framework.

## US Representative Audit

| Ticker | Framework | Confidence | Boundary |
|---|---|---|---|
| MU | semiconductor | High | company-level multiples; exact memory route not asserted without structured taxonomy |
| TSM | semiconductor | High | segment attribution and ADR valuation safety remain separate; hyperscaler context is secondary |
| TSLA | automotive | High | growth is linked to missing margin, incentives, CAPEX and FCF rather than option value alone |
| RXRX | biotech | High | cash runway, milestones and dilution frame; PER is not forced as the valuation answer |
| WULF | general | Low | thesis/HPC theme cannot override verified Financial Services profile evidence |
| IBM | general | Low | verified revenue, margin/cash/balance-sheet framework without invented SaaS metrics |

## Causal And Valuation Validation

- All 12 requested framework routes have unit fixtures.
- Verified causal references require supporting Fact IDs and every required middle family.
- Missing-driver Unknown references pass only when the driver is absent.
- Framework mismatch, biotech PER-cheap, insurance PBR-cheap, memory low-PER-cheap, EPC order-to-
  margin, and hyperscaler-to-company-revenue leaps are rejected.
- Short marker detection is token-bound; unrelated field paths do not become ARR, PE, or ROE.
- KR binder accepted 86 automatic numeric references and 12 industry references with zero errors.
- KR and US full validators passed; both runtime quality receipts passed.
- SK hynix denied earnings/PER numeric or qualitative leakage: 0.

## Message And Human-Quality Review

The assessment below is a Codex retrospective, not Work approval or Production Assist evidence.

| KR stock | Prior score | Phase 8.5 assessment | Industry dimensions /8 | Main result |
|---|---:|---:|---:|---|
| Samsung | 17 | 16 | 6 | safer complex-company attribution; specialization remains unavailable |
| POSCO | 16 | 17 | 7 | cyclical PER/PBR relation improved |
| Hyundai Glovis | 18 | 18 | 8 | transport causal chain retained |
| Korean Re | 16 | 17 | 7 | insurance ROE/capital boundary improved |
| SK hynix | 17 | 17 | 7 | negative-control safety retained |
| **Average** | **16.8** | **17.0** | **7.0** | no critical issue |

KR message length changed from 5,884 to 5,955 characters, an increase of about 1.2%; lines and
sections were unchanged. US representative length changed from 7,572 to 7,616 characters, about
0.6%; only MU gained the already-required data-caution section. No substantive repeated sentence,
generic Unknown, or generic next-check finding was reported by the runtime gate.

## Natural Runtime Gap

Natural packet `2026-08-17-kr-run-23-378ee562573e` remains a separate packet/numeric-path issue.
Pre-send validation rejected POSCO, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis because the
required current-price RR Fact/path was absent. Rejected AI sends were zero, fallback eligibility
was preserved, and the deterministic fallback later sent 8/8 at 17:10 KST. Pilot stayed KR 3/5 and
US 3/5. No validator was relaxed in Phase 8.5.

## Remaining Limits

- Specialized primary coverage is constrained by structured taxonomy and business-unit evidence.
- Peer/sector valuation remains unavailable or partial.
- OCF is partial; CAPEX aggregation and FCF remain open.
- KRX approval is not evidenced in repository state; status remains pending/unknown.
- Human-approved natural-live Production Assist evidence remains insufficient.
