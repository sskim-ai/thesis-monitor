# Phase 8.3.1 KR Provider Matrix

Date/accessed: `2026-08-18`
Evidence policy: official product, API, pricing, and license pages only

## Matrix

| Provider/product | Universe/taxonomy | PER/PBR | Forward | Point-in-time | Identity/basis | Cost/license | Verdict |
|---|---|---|---|---|---|---|---|
| FnGuide FnSpace API | KR company financials and consensus; daily/fiscal/forward datasets | strong | consensus and estimated ratios | daily estimate history documented; exact restatement model needs confirmation | KR ticker/company fields; preferred/share and basis details need POC | published monthly tiers; standard terms prohibit DB/app/customer/third-party exposure | `CONDITIONAL_BEST_KR_TECHNICAL_FIT` |
| FnGuide DataGuide | broad KR financial, price, industry and consensus history; peer tools | strong | consensus history since 2000 | historical basis-date output | consolidated-basis and peer tooling; security hierarchy POC required | Excel product; KRW 7.2m first annual account; bulk DB/external sharing restricted | research workstation, not production API |
| DeepSearch Data API | listed/unlisted KR company, market, financial and industry APIs | current ratios documented | target-price consensus documented; EPS consensus history unclear | historical market/financial query; true PIT/restatement model unproven | KR symbol and NICE/legal/business IDs; security/share basis unclear | public pricing and redistribution terms not established | `CONDITIONAL_COST_BENEFIT_RESEARCH` |
| NICE ValueSearch | 1.5m+ companies, KSIC, listed-company current metrics | current EPS/BPS/PER | not proven | not proven | company identity broad; common/preferred and share basis unclear | sales contact; Excel workflow; API/display terms unknown | sales clarification only |
| KRX Data Marketplace/Open API | authoritative listed-security and market classifications | current/historical market PER/PBR available in marketplace | unsupported | historical market series; Open API publication timing unresolved | authoritative 6-digit security identity; no consensus denominator lineage | redistribution approval/terms apply | authoritative auxiliary, not full peer provider |
| Kiwoom REST API | broker universe and screen/filter data | current filters/quotes | not proven | not proven | broker security IDs; issuer/share hierarchy unproven | account/usage terms apply | current broker source only |
| Global institutional feeds | broad multi-market fundamentals/estimates | strong product-level claims | strong | S&P/FactSet/LSEG PIT products documented | global identifiers; KR entitlement and share basis require POC | contact sales and negotiated redistribution | institutional shortlist |

## Fixture Capability Questions

| Fixture | Required proof before eligibility |
|---|---|
| Samsung | company-wide taxonomy and peers; do not label total-company multiple as memory-segment valuation |
| SK hynix | safe PBR peers; external peer data cannot restore the denied subject trailing PE |
| POSCO Holdings | holding/operating-company distinction and cyclical PBR/normalized earnings basis |
| Hyundai Glovis | logistics taxonomy, mid-cycle earnings period, and cash-conversion fields |
| Korean Re | reinsurance taxonomy, PBR, ROE, capital, and underwriting-quality availability |

No provider was entitlement-tested across these five subjects. A claim that any candidate supplies
three clean peers is therefore `THEORETICAL`, not observed.

## Official Evidence

### FnGuide

- FnSpace service/pricing/license: <https://www2.fnspace.com/Customer/Info>
- FnSpace consensus history/estimated ratios: <https://www.fnspace.com/DataMart/RequestInfo?aid=A000005&cid_p=C001&pid=P0003>
- FnSpace API catalog: <https://www1.fnspace.com/DataMart/MartList>
- DataGuide data coverage: <https://help-dataguide.fnguide.com/ko/articles/%EC%A0%9C%EA%B3%B5-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%95%88%EB%82%B4-5c5347da>
- DataGuide pricing and use restrictions: <https://help-dataguide.fnguide.com/ko/articles/%EC%9D%B4%EC%9A%A9-%EB%B0%8F-%EC%9A%94%EA%B8%88-%EC%95%88%EB%82%B4-48b18a4b>
- DataGuide company/market output and peer features: <https://help-dataguide.fnguide.com/ko/articles/%EA%B8%B0%EC%97%85%EC%8B%9C%EC%9E%A5%EC%9D%98-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%B6%9C%EB%A0%A5%ED%95%98%EA%B8%B0-18e890dd>
- Consensus guide: <https://www.fnguide.com/download/CONSENSUS_USER_GUIDE.pdf>

### DeepSearch And NICE

- DeepSearch API master: <https://help.deepsearch.com/dp/api/master>
- DeepSearch query overview: <https://help.deepsearch.com/dp/api/inquiry/overview>
- DeepSearch company identity summary: <https://help.deepsearch.com/dp/api/func/company/company-search/getentitysummary>
- DeepSearch target-price consensus history: <https://help.deepsearch.com/dp/api/func/company/consensus/searchtargetprices>
- NICE ValueSearch: <https://www.niceinfo.co.kr/business/VALUESearch.nice>
- NICE ValueSearch Excel guide: <https://www.nicevse.com/vse/res/file/NICE%20%EA%B8%B0%EC%97%85%EC%A0%95%EB%B3%B4%20%EB%8D%B0%EC%9D%B4%ED%84%B0%20%EC%84%9C%EB%B9%84%EC%8A%A4%20%EC%86%8C%EA%B0%9C%EC%9E%90%EB%A3%8C%20ValueSearch%20Excel.pdf>

### Copy-Ready KRX Service And Terms List

```text
KRX Data Marketplace / service list
https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=ko

KRX information products / data-sale service list
https://data.krx.co.kr/contents/MDC/INFO/informationController/MDCINFO008.cmd

KRX Market Data Usage Policies (Korean PDF)
https://data.krx.co.kr/inc/datasale/Market%20Data%20Usage%20Polices_ko.pdf

Kiwoom REST API official home
https://openapi.kiwoom.com/main/home
```

KRX service pages support current/historical listed-security PER/PBR and classifications, but those
facts do not establish forward consensus. The usage policy requires a separate review of storage,
derived output, and redistribution before user-facing integration.

## KR Recommendation

1. `BEST TECHNICAL FIT, CONDITIONAL`: FnGuide FnSpace after a written commercial license and exact
   security/PIT field confirmation.
2. `BEST COST/BENEFIT RESEARCH, CONDITIONAL`: DeepSearch after pricing, consensus, PIT,
   common/preferred, and redistribution answers.
3. `BEST INSTITUTIONAL`: evaluate S&P Global MI or FactSet entitlement over the five KR fixtures.

No KR candidate is approved for integration in this phase.
