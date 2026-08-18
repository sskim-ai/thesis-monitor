# Phase 8.3.1 Provider Recommendation

Date: `2026-08-18`
Decision: `NO PROVIDER SELECTED / PROCUREMENT OR CREDENTIAL DECISION REQUIRED`

## Recommended Architecture

The best technical architecture is a single global institutional source if its entitlement covers
both KR and US security bases, PIT fundamentals, estimates, storage, external AI processing, and
derived user display. This minimizes cross-provider denominator and revision reconciliation.

If institutional cost is not justified, use a market split rather than a loose multi-source blend:

```text
KR dedicated fundamentals/consensus
    + US dedicated fundamentals/consensus
    + OpenFIGI/SEC identity auxiliaries
    -> one Phase 8.3 normalization and eligibility contract
```

An identity auxiliary never supplies valuation basis. KRX and Massive remain market/reference
sources. Consensus and modeled forward samples stay separate.

## Shortlist

### KR

1. `BEST TECHNICAL FIT, CONDITIONAL`: FnGuide FnSpace. It documents API financial/consensus history
   and estimated ratios at practical published prices. Its standard license is a hard blocker because
   it prohibits DB construction and app/customer/third-party exposure. Proceed only with a written
   commercial license and a field-level POC.
2. `BEST COST/BENEFIT RESEARCH, CONDITIONAL`: DeepSearch. It offers a real KR company/market API and
   useful identity/taxonomy, but public documents do not close PIT, EPS-consensus history, share basis,
   pricing, or redistribution.
3. `BEST INSTITUTIONAL`: S&P Global MI or FactSet, after confirming KR entitlement and 6-digit/common-
   preferred/security-basis behavior.

### US

1. `BEST TECHNICAL API FIT`: FactSet. Its official estimate API, classifications, identity hierarchy,
   fixed/rolling periods, and PIT products best match the implemented contract.
2. `BEST INSTITUTIONAL PIT FIT`: S&P Global MI. Compustat PIT and detailed estimate-change history are
   the strongest backtest-integrity fit.
3. `BEST COST/BENEFIT, CONDITIONAL`: Intrinio commercial/startup. It has strong fundamentals and
   timestamps, with Zacks estimates available separately. Individual rights are insufficient, and
   ADR/display/AI rights require the order form.

LSEG is the strongest alternate institutional candidate. Bloomberg is not rejected technically, but
cost, entitlement, and implementation complexity make it a weaker first procurement path.

### Cross-Market

Shortlist S&P Global MI, FactSet, and LSEG. Do not assert actual 20-stock coverage until an entitled
POC runs the exact fixtures.

## Not Recommended As Primary

- Massive: current latest-day ratios and no consensus/PIT ratio history.
- Finnhub: live fields are broad, but exact as-of/forward basis and TSM ADR basis are unsafe.
- Alpha Vantage: useful current fields; no true PIT and live MU estimate coverage was empty.
- FMP: attractive cost, but PIT, revision, issuer, ADR, and license gaps are material.
- Tiingo/SimFin: useful trailing fundamentals components without consensus.
- OpenFIGI/SEC: identity and filing auxiliaries, not valuation providers.
- KRX/Kiwoom: authoritative/current market roles, not forward peer-consensus providers.

## Cost Tiers

| Tier | Recommended next evaluation | Trade-off |
|---|---|---|
| Low cost | Tiingo or FMP POC plus current repository sources | incomplete consensus/PIT/security basis; reconciliation burden high |
| Mid tier | FnSpace custom rights for KR + Intrinio commercial for US | two providers and two license negotiations; likely best cost-aware path |
| Institutional | S&P Global MI or FactSet global entitlement | strongest data integrity and simplest normalization; highest cost |

Public sticker price is not total project cost. Cross-provider reconciliation, security-master work,
license monitoring, and failed-closed coverage can outweigh a cheaper feed.

## Vendor Questionnaire

Before Phase 8.3.2, obtain written answers for:

1. exact KR/US exchange and inactive-security coverage;
2. issuer ID, security ID, share class, ordinary/depositary relation, and ADR ratio;
3. current PER/PBR input fields, denominator period, price date, currency, and restatement behavior;
4. FY1/NTM definitions, estimate effective date, analyst count, revision history, and basic/diluted
   basis;
5. GICS/SIC/KSIC or equivalent taxonomy history and stability;
6. API/bulk limits and update SLA;
7. storage and retention rights;
8. derived median/percentile and Telegram display rights;
9. sending raw fields or derived facts to an external AI service; and
10. trial entitlement for Samsung, SK hynix, POSCO, Hyundai Glovis, Korean Re, MU, TSM, TSLA, RXRX,
    GOOGL, CORZ, HUT, and WULF.

## Phase 8.3.2 Gate

The next integration phase requires a user-selected provider, available credential/trial, acceptable
license, and confirmed mandatory fields. None is complete. The recommended next action is a pricing
and rights decision between:

- S&P/FactSet institutional global evaluation; or
- FnSpace/DeepSearch KR plus Intrinio US cost-aware evaluation.

Natural-live operating blockers and KRX time-slot evidence remain higher-priority operating work.
No purchase, signup, integration, main merge, or deployment is authorized by this report.
