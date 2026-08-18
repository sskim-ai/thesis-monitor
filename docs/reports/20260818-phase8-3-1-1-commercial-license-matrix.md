# Phase 8.3.1.1 Commercial And Licensing Matrix

Date/accessed: `2026-08-18`

`SUPPORTED` below means public terms support the use class at product level. It does not replace an
entitlement or Order Form. Telegram is treated as user-visible external display, and sending source
data to a hosted LLM is treated separately from internal deterministic calculation.

| Provider | Internal analytics | Persistent storage | Derived statistics | User-visible display | External redistribution | External LLM input | AI-derived user output | Cost | Decision |
|---|---|---|---|---|---|---|---|---|---|
| S&P Global MI | supported by licensed products | entitlement-specific | entitlement-specific | vendor confirmation | vendor confirmation | AI-ready products exist; product/order rights required | vendor confirmation | `INSTITUTIONAL_CONTACT_REQUIRED` | conditional |
| FactSet | licensed use supported | contract-specific | contract-specific | API supports client-facing apps, but publication rights are contract-specific | authorization required | FactSet AI products do not prove rights for this external model | vendor confirmation | `INSTITUTIONAL_CONTACT_REQUIRED` | conditional |
| LSEG | licensed use supported | contract-specific | license required | redistribution license required | license required | AI/client output falls under redistribution policy | license required even for derived output | `INSTITUTIONAL_CONTACT_REQUIRED` | conditional |
| FnSpace standard | internal/research only | prohibited DB construction | only limited citation | prohibited in apps/customer/third-party exposure | prohibited | not granted | prohibited external output | published KRW package prices | blocked by standard license |
| FnSpace enterprise/custom | possible via corporate inquiry | unknown | unknown | unknown | unknown | unknown | unknown | `CONTACT_REQUIRED` | vendor confirmation |
| DeepSearch | API use supported | unknown | unknown | unknown | unknown | unknown | unknown | `CONTACT_REQUIRED` | vendor confirmation |
| Intrinio Individual | personal/internal only | default terms restrict database incorporation unless ordered | internal only | explicitly no redistribution/display | prohibited | terms classify third-party LLM transmission as redistribution | no external output | `$150/month` | not production eligible |
| Intrinio Startup | commercial use advertised | Order Form controls | possible under Order Form | display rights advertised | scope limited by Order Form | GenAI advertised, but external provider rights must be explicit | display license/order scope required | `$333/month` start; phased | conditional |
| Intrinio Enterprise | commercial/custom | Order Form controls | negotiable | negotiable | negotiable | negotiable | negotiable | `$1,250/month+` | conditional |

## Critical Findings

FnSpace's public license says data and processed data cannot be built into a subscriber database or
exposed through an application to customers or third parties. Its published corporate inquiry path
does not itself grant an exception. A separate written enterprise license is mandatory.

Intrinio's terms define display broadly, require an executed Order Form for commercial/third-party
rights, and classify transmission to OpenAI or another hosted model as redistribution even when the
result is internal. External AI-generated output also needs display/redistribution rights. The
pricing page's Startup `Commercial Use and Display Rights` and `GenAI integration` claims make it a
real candidate, but the exact Order Form must name the intended Telegram and hosted-LLM use.

S&P, FactSet, and LSEG provide technical data/AI delivery products, but public pages do not replace
the negotiated product and downstream-rights schedule. Their user display, derived output, storage,
and third-party model rights remain `UNKNOWN_REQUIRES_VENDOR_CONFIRMATION` for this project.

## Evidence

- [FnSpace service/license, lines covering prices and restrictions](https://www.fnspace.com/Customer/Info)
- [FnSpace terms](https://www.fnspace.com/Customer/Service)
- [Intrinio terms, effective 2026-06-03](https://docs.intrinio.com/terms)
- [Intrinio current pricing](https://intrinio.com/pricing)
- [S&P licensing terms](https://www.spglobal.com/en/licensing-terms-and-conditions)
- [S&P data licensing/AI collaborator model](https://www.spglobal.com/market-intelligence/en/solutions/alliance-collaborators)
- [FactSet legal page](https://www.factset.com/legal)
- [FactSet data attribution guidance](https://www.factset.com/data-attribution)
- [LSEG redistribution and derived-data policy](https://www.lseg.com/en/data-analytics/market-data/data-redistribution)

No legal conclusion is inferred beyond the published text. Contract-specific unknowns require the
vendor questionnaire; none is silently promoted to `SUPPORTED`.
