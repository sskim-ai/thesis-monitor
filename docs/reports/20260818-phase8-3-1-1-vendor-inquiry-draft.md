# Phase 8.3.1.1 Vendor Inquiry Draft

Date: `2026-08-18`
Status: `COPY-READY / NOT SENT`

## Subject

API and licensing inquiry for point-in-time peer valuation analytics with AI-assisted user output

## Message

Hello,

We are evaluating your data for an internal investment-monitoring system covering a small KR/US
equity universe. The system deterministically calculates peer medians, percentiles, relative
multiples, and premium/discount statistics, then may send a short derived analytical message to an
authorized end user through Telegram. A hosted LLM may receive validated fields or derived facts to
write the explanation; it does not calculate the statistics.

Could you please confirm the following for the exact API/data package and commercial entitlement?

1. Does the product provide historical point-in-time fundamentals as known on each requested date?
2. Are historical values as reported at that time, or are later restatements applied backward?
3. Which filing, source, effective, update, and first-available timestamps are included?
4. Are historical consensus estimate snapshots available, rather than only today's consensus and
   historical actuals?
5. For consensus, are estimate effective/revision timestamp, fiscal period, currency, analyst count,
   and basic/diluted or share basis available?
6. Are issuer, security, listing, exchange, share class, and active/delisted identifiers available?
7. For ADR/ADS securities such as TSM and SKHY, are underlying ordinary security, depositary ratio,
   ratio direction, currency, and per-ADR denominator explicitly supplied?
8. May we persist raw fields and normalized audit records locally, and for how long?
9. May we display derived peer median, percentile, relative multiple, and premium/discount values to
   an authorized end user in a Telegram message?
10. Is that display treated as derived data, display, redistribution, or another licensed use?
11. May source fields or normalized facts be sent to OpenAI or another hosted LLM API?
12. May AI-generated analytics derived from the licensed data be shown to the authorized end user?
13. What attribution, audit, output suppression, or non-reconstruction controls are required?
14. Which commercial plan, data packages, display/redistribution rights, AI rights, API quota, storage
   rights, one-time history fees, and recurring fees are required?
15. Can a trial cover Samsung Electronics, SK hynix, POSCO Holdings, Hyundai Glovis, Korean Re, MU,
   TSM, TSLA, RXRX, GOOGL/GOOG, CORZ, HUT, and WULF?

For Korean data, please also confirm six-digit ticker, common/preferred distinction, CFS/OFS basis,
IFRS denominator basis, and consensus fiscal-period metadata.

We will not redistribute raw source data or use it to train a model. Please identify any separate
third-party publisher or exchange agreements that apply.

Thank you.

## Vendor-Specific Follow-Ups

- FnGuide: does a corporate/custom agreement override the public FnSpace restrictions on database
  construction, application output, third-party exposure, and processed data?
- DeepSearch: provide the applicable API commercial terms, storage/display/AI rights, EPS consensus
  history fields, and restatement model.
- Intrinio: identify the exact Startup/Enterprise Order Form language needed for hosted-LLM input and
  external AI-derived display, plus the Zacks estimate-history fee and ADR-ratio field.
- S&P, FactSet, LSEG: quote the smallest entitlement covering KR+US PIT fundamentals, PIT consensus,
  issuer/security hierarchy, derived display, hosted LLM input, and one authorized end user.

No inquiry was transmitted during this phase.
