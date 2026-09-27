# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV3
## Residual Four-Subject Financial Semantic Closure
### Generic SEC FPI document-purpose/period owner + same-document fragment identity + generic IFRS insurance-revenue mapping

**Purpose:** close only the four residual subjects left after the successful bounded SEC/OpenDART owner rollout. Do not rerun the full 19-subject acquisition and do not redesign the now-working financial owner. First replay the already captured R5-REV2 source artifacts offline. Fix only generic semantic/identity gaps. If additional SEC source documents are genuinely required, perform one bounded follow-up for the three blocked foreign issuers under a frozen request budget. OpenDART network calls should remain zero unless the frozen 003690 artifacts are proven insufficient.

No price/OHLCV calls. No Market/Core/A/B. No message generation. No scheduler mutation.

---

# 0. Newest accepted SoT

Adopt the R5-REV2 result as the newest SoT.

Result ZIP SHA-256:

`5a6b59e7406eddd2c19f3890859073afeefd474b515f6a73617c579748b896e6`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV2_FINANCIAL_BUSINESS_PREQUALIFICATION_PARTIAL`

Repository identities:

- base:
  `35fe0ce35160bb5199f2c8db00c927ff78ea9c0a`
- instruction:
  `2e1f77acb4daa96957231f211d4dbce4b1d4c28c`
- bounded-owner implementation:
  `62adffe5891f71c2e606d57dcc827ba8bf96314b`
- captured-source frozen SHA:
  `32ee6839cd57ede524db3a1cca53b8aaab626cb4`
- tested final:
  `45e90cb8d66bd1ade51439ba34bbd212ea8b2236`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted result facts:

- subjects: `22`
- complete stock source/business packets: `18/22`
- blocked: `4/22`
- current-price eligible: `22/22`
- sealed stock price roles: `88/88`
- system stop: `null`
- model/delivery calls: `0`
- production side effects: `0`

Newly complete under bounded financial owner:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- TSLA
- WULF
- 000660
- 005490
- 010120
- 012450
- 086280

Previously complete controls retained:

- SNDK
- 005930
- 047810

Therefore all **18 complete subjects are invariance controls** in REV3.

R5-REV2 validation:

- focused: `681 PASS`
- full: `5709 PASS / 63 pre-existing skips / 0 failures`
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled entrypoint smoke: PASS

Provider acquisition ledger accepted:

## SEC
- subjects: 13
- actual logical/HTTP attempts: `65`
- retries: `0`
- theoretical max logical: `94`
- theoretical max attempts with retry envelope: `282`

## OpenDART
- subjects: 6
- actual logical/HTTP attempts: `30`
- retries: `0`
- theoretical max logical: `36`
- theoretical max attempts with retry envelope: `108`

The bounded owner itself is therefore **not** the current blocker.

Do not overwrite or reinterpret R5-REV2.

---

# 1. Exact residual blocker matrix

Freeze this residual matrix before code changes and refine it only from the sealed R5-REV2 artifacts.

## SKHY — SEC / foreign private issuer

Current state:

- acquisition: `ACQUIRED`
- selected current filing:
  - form `6-K`
  - filing/report date `2026-09-18`
- selected document is a response to a Korea Exchange disclosure inquiry concerning media reports about a potential Japan semiconductor facility;
- it is **not** financial-result evidence;
- projection denial:
  `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION`
- no qualified current/prior financial comparison;
- packet remains blocked.

Exact semantic blocker:

`FOREIGN_FINANCIAL_PURPOSE_AND_COMPARABLE_PERIOD_SELECTION_MISSING`

Do not substitute an older annual value merely because it exists.

## TSM — SEC / foreign private issuer

Current state:

- acquisition completed within bounded owner;
- selected latest current 6-K dated `2026-09-01` is a **cash-dividend-per-share adjustment**, not a financial-results filing;
- a captured prior 6-K dated `2025-11-14`, report date `2025-09-30`, explicitly references consolidated financial statements;
- captured discovery metadata also contains multiple 2026 6-K candidates including financial-statement / period-bearing filings;
- current packet has context only, no qualified direction;
- acquisition denial was initially labeled `SEC_DOCUMENT_SOURCE_SCOPE_DENIED`;
- follow-up proved rejected URLs were `#fragment` anchors into already-fetched primary 20-F documents, not different external documents;
- refined issue:
  `SAME_DOCUMENT_FRAGMENT_ALIAS_FALSE_POSITIVE`
  plus
  `FOREIGN_FINANCIAL_PURPOSE_AND_COMPARABLE_PERIOD_SELECTION_MISSING`.

Do not select “latest 6-K” as financial evidence solely because it is latest.

## WRD — SEC / foreign private issuer

Current state:

- acquisition completed within bounded owner;
- latest 6-K dated `2026-09-24` is an announcement of restricted share units under a 2026 share plan;
- prior selected 6-K dated `2025-10-28` concerns a voluntary lock-up / Hong Kong IPO;
- neither proves a current/prior financial comparison;
- frozen submissions metadata contains other 6-K candidates, including a `2026-09-14` filing with report date `2026-06-30`;
- 20-F fragment links were incorrectly treated as out-of-scope external documents;
- refined issues:
  `SAME_DOCUMENT_FRAGMENT_ALIAS_FALSE_POSITIVE`
  plus
  `FOREIGN_FINANCIAL_PURPOSE_AND_COMPARABLE_PERIOD_SELECTION_MISSING`.

Do not infer that the 2026-09-14 candidate is financial evidence merely from its date. Purpose/period must be proven by the generic owner.

## 003690 — OpenDART / insurance financial semantic

Current state:

- acquisition: `ACQUIRED`
- existing generic canonical `revenue` source row is missing;
- operating-income and net-income rows remain denied because current quality/corroboration owner cannot evaluate them against a qualified revenue field;
- captured OpenDART CIS source already contains standard financial concepts including:
  - `ifrs-full_InsuranceRevenue` / `보험수익`
  - `ifrs-full_ProfitLossFromOperatingActivities`
  - `ifrs-full_ProfitLoss`
- current and comparable source columns/period labels are present in the captured statement;
- no company-specific insurance mapping was added.

Exact semantic blocker:

`GENERIC_CANONICAL_REVENUE_SEMANTIC_MISSING_FOR_IFRS_INSURANCE_REVENUE`

This must be fixed generically by exact standard financial concept semantics, not by ticker.

---

# 2. Scope rule — only three generic fixes

REV3 may change only the smallest generic code needed for:

1. **SEC same-document URL identity**
   - normalize intra-document `#fragment` aliases safely;

2. **SEC foreign-private-issuer financial-purpose + period selection**
   - distinguish financial-results 6-K/20-F evidence from non-financial 6-Ks;
   - select compatible current/prior financial periods generically;

3. **OpenDART canonical revenue semantics**
   - recognize exact standard IFRS insurance-revenue concepts as canonical revenue where statement/period/basis rules prove compatibility.

Do not add a fourth feature unless the frozen four-subject replay proves another mandatory generic gap.

---

# 3. Fix A — SEC same-document fragment identity

R5-REV2 proved TSM/WRD rejected links such as:

`primary-document.htm#fragment`

even when the already-fetched primary document bytes are the same source document.

Implement a generic SEC document identity function.

## 3.1 Canonical identity key

For SEC archive document identity, bind at minimum:

- scheme/host must be approved SEC host;
- issuer/CIK archive scope;
- accession directory;
- normalized document path/file;
- filing/accession ownership.

For **document identity only**, URL fragment must not create a new document identity.

Example:

`https://www.sec.gov/.../wrd-20251231x20f.htm#FINANCIALSTATEMENTS`
and
`https://www.sec.gov/.../wrd-20251231x20f.htm`

may resolve to the same document identity if:
- host/path/accession are identical;
- underlying captured source document SHA is identical or the fragment points into the already-fetched exact source.

Preserve the original full URL including fragment in diagnostic receipts.

## 3.2 Do not over-normalize

Must remain different:

- different accession;
- different path/file;
- different exhibit document;
- different approved-host scope;
- query/source identity that changes returned bytes;
- path traversal / alias outside the filing.

Do not strip path, accession or filename distinctions.

## 3.3 No fragment fetch

A same-document fragment must not consume a second network request merely to prove identity.

Use already-fetched document bytes.

---

# 4. Fix B — generic foreign financial-purpose owner

Create or extend a generic owner for foreign private issuer SEC filings.

Do not use ticker-specific selection.

Do not select:
- newest 6-K;
- largest document;
- first candidate;
- filename pattern alone;
- accession hardcode.

The owner must classify **filing/document purpose** and **economic financial period**.

---

# 5. Foreign filing purpose states

Every FPI candidate must receive one explicit state:

- `FINANCIAL_STATEMENTS`
- `FINANCIAL_RESULTS_OR_EARNINGS`
- `REVENUE_DISCLOSURE_ONLY`
- `DIVIDEND_OR_CAPITAL_RETURN`
- `GOVERNANCE_OR_COMPENSATION`
- `CORPORATE_EVENT_NONFINANCIAL`
- `RUMOR_OR_DISCLOSURE_RESPONSE`
- `UNKNOWN_PURPOSE`

Only purpose states already permitted by the existing financial/business field owner may contribute financial fields.

`UNKNOWN_PURPOSE` fails closed.

Do not treat all 6-Ks as financial evidence.

---

# 6. Purpose evidence must be source-owned

Purpose classification must be derived from source-owned filing/document evidence, for example:

- SEC filing form + accession;
- filing report date;
- filing index document/exhibit description;
- exact primary/exhibit source bytes;
- actual financial-statement table structure;
- exact canonical/XBRL financial concepts;
- explicit period-bearing financial statement headings.

A filename may be a supporting hint only.

Keyword-only title matching is insufficient to grant financial authority unless paired with actual financial statement/result content recognized by the existing parser/owner.

---

# 7. Foreign economic period contract

A qualifying financial candidate must expose an economic period independent of mere filing date.

At minimum preserve:

- filing date;
- SEC report date;
- financial period start/end where available;
- period role:
  - quarter/interim;
  - YTD;
  - annual;
  - instant;
- source of period identity;
- current/prior role.

Do not use:

`filingDate == financialPeriodEnd`

unless the source contract actually proves it.

For a non-financial 6-K whose report date is merely event date:
- it cannot own an earnings period.

---

# 8. Current/prior selection for FPI

Select a current/prior pair only when:

- same issuer/security;
- financial-purpose candidate;
- same canonical field semantic;
- compatible period role;
- comparable duration;
- compatible statement/accounting basis;
- compatible currency/unit;
- exact source occurrences;
- existing field-quality/source-use checks pass.

Do not substitute:
- annual 20-F for missing current interim;
- stale older quarter for latest required current period;
- different-purpose 6-K;
- non-comparable period.

If no pair exists:
- financial direction unavailable;
- subject may remain blocked.

This is honest behavior.

---

# 9. Foreign candidate search — offline first

Use already captured R5-REV2 SEC submissions/discovery bytes first.

For SKHY / TSM / WRD:

1. parse the existing captured submissions artifact;
2. produce a deterministic candidate inventory;
3. classify candidates whose required document bytes are already captured;
4. identify exact missing candidate documents needed for purpose/period classification.

No network in this phase.

The inventory must show:

- accession;
- form;
- filing date;
- report date;
- primary document;
- candidate purpose state;
- document captured? yes/no;
- reason for selection/rejection;
- current/prior suitability.

---

# 10. Generic bounded FPI follow-up — only if offline evidence is insufficient

If one or more of SKHY / TSM / WRD still require source documents after offline replay, generate a **generic FPI follow-up plan**.

No ticker-specific URL/accession hardcodes in production owner code.

The plan may contain concrete accession IDs as runtime results from the generic selector, but the code cannot special-case those IDs.

Before network access freeze:

- subjects requiring follow-up;
- candidate filings per subject;
- exact filing-index requests;
- exact document/exhibit requests;
- theoretical max logical requests;
- theoretical max transport attempts;
- request hashes;
- generic candidate cap;
- cap-exhaustion state.

No request executes with unknown/unbounded budget.

---

# 11. FPI candidate cap

Audit the already accepted foreign-owner bounded constants and introduce at most one generic candidate-purpose search cap if required.

Possible form:

`SEC_FPI_MAX_PURPOSE_CANDIDATES`

Requirements:

- same generic cap for all FPI subjects of the same issuer class;
- no ticker overrides;
- finite;
- tested with 0 / below-cap / at-cap / over-cap candidate fixtures;
- deterministic ordering by existing SEC filing metadata, not semantic desirability;
- cap exhaustion returns:
  `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`.

Do not silently increase the cap until a result is found.

---

# 12. FPI follow-up transport policy

For each frozen follow-up request:

- timeout `600 seconds`;
- first attempt `1`;
- transient retries max `2`;
- max attempts `3`;
- byte-identical retries only.

No retry for:
- identity failure;
- source-scope failure;
- purpose failure;
- period mismatch;
- schema failure;
- semantic failure;
- field-quality failure;
- policy failure.

Non-fail-fast across SKHY / TSM / WRD unless systemic SEC identity/security/config drift occurs.

---

# 13. Fix C — generic IFRS insurance revenue semantic

Use the frozen 003690 OpenDART source first.

Do **not** perform a new OpenDART call unless the frozen source is proven insufficient.

The captured source contains exact standard concept:

`ifrs-full_InsuranceRevenue`

with account name:

`보험수익`

in the income statement.

Implement a **generic canonical financial concept mapping** such that exact standard IFRS insurance-revenue semantics may qualify as canonical:

`revenue`

when all field-level conditions pass.

This mapping must not reference:
- ticker `003690`;
- company name;
- corp code;
- filing accession;
- hardcoded amount.

---

# 14. Insurance revenue mapping eligibility

`ifrs-full_InsuranceRevenue` may map to canonical `revenue` only when:

- exact concept ID matches the approved standard concept;
- source statement is an income-statement role accepted by the existing financial owner;
- exact issuer/security ownership passes;
- statement basis is explicit;
- current/prior source columns are explicit;
- period role is explicit;
- currency/unit is explicit;
- current/prior periods are compatible;
- lineage is exact;
- field quality/source-use passes.

Do not map arbitrary account names containing `수익` or `Revenue`.

Do not use fuzzy string matching as financial authority.

---

# 15. Explicit non-mapping controls for insurance statements

The following must **not** be mapped to canonical `revenue` merely because their names contain revenue/income text:

- investment income;
- interest revenue;
- dividend revenue;
- reinsurance income;
- other operating income;
- non-operating income;
- finance income;
- generic subtotal rows not defined by the existing canonical owner.

Similarly:

`dart_OperatingIncomeInsurance` / `보험영업수익`

must not automatically become canonical `operating_income` merely because the English identifier contains “OperatingIncome”.

Use exact semantic owner rules.

Existing qualified `ifrs-full_ProfitLossFromOperatingActivities` and `ifrs-full_ProfitLoss` rows retain their own semantics.

---

# 16. Re-evaluate 003690 financial quality after canonical revenue mapping

Using only the frozen captured OpenDART source:

1. project canonical revenue from the exact standard insurance-revenue row if eligible;
2. preserve exact current and prior comparable occurrences;
3. rerun the existing financial-quality owner unchanged;
4. rerun current/prior comparability;
5. compute directional eligibility only if all rules pass.

Do not relax:
- extreme-value rules;
- corroboration rules;
- taint rules;
- period compatibility;
- source-use rules.

Expected possibility:
- proper revenue denominator may change whether operating-income/net-income anomaly checks are meaningful.

Do not predeclare that it will PASS.

---

# 17. Field-level independence remains mandatory

For all four blocked subjects:

- one denied field does not kill a clean unrelated field;
- one clean field does not rescue a denied sibling;
- absolute context does not create direction;
- direction requires compatible observations;
- whole-envelope invariants remain strict only where the existing schema genuinely requires them.

Do not weaken existing quality contracts.

---

# 18. 18 complete subjects are invariance controls

All currently complete subjects must remain complete for the same accepted reasons:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SNDK
- TSLA
- WULF
- 000660
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

No new provider calls are needed for these controls.

Replay them offline against the updated generic owner.

Regression if:

- any packet changes from PASS to BLOCKED for unrelated reasons;
- existing source refs are rewritten without cause;
- 000660 denied operating/net fields become silently eligible;
- SNDK event authority is replaced;
- CPNG anomaly handling changes;
- 005930/047810 accepted evidence changes.

---

# 19. Offline proof sequence

Before any follow-up SEC network request:

## Phase A — fragment identity metamorphic tests

At minimum:

- same path + different fragment -> same document identity;
- same path + no fragment -> same identity;
- different file -> different;
- different accession -> different;
- different issuer/archive scope -> different;
- traversal/alias path -> rejected.

## Phase B — FPI purpose/period fixtures

At minimum cover:

- nonfinancial 6-K rumor response;
- dividend-adjustment 6-K;
- compensation/share-plan 6-K;
- financial-statements 6-K;
- quarterly/interim financial-results 6-K;
- annual 20-F;
- unknown-purpose 6-K;
- financial exhibit attached to 6-K;
- incompatible current/prior periods;
- annual vs interim mismatch.

## Phase C — insurance semantic fixtures

At minimum:

- `ifrs-full_InsuranceRevenue` positive;
- same concept wrong statement -> negative;
- investment income -> not canonical revenue;
- interest/dividend/reinsurance/other income -> not canonical revenue;
- `dart_OperatingIncomeInsurance` -> not operating income by name alone;
- field quality with correct revenue denominator;
- incompatible period negative.

## Phase D — frozen four-subject replay

No network.

Only if needed proceed to bounded SEC follow-up.

---

# 20. Follow-up budget receipt

If SEC follow-up is required, create before first call:

`residual-fpi-followup-plan.json`

with:

- exact subjects;
- generic selector version/hash;
- exact candidate filings;
- exact filing-index requests;
- exact document requests;
- planned logical calls;
- theoretical max logical calls;
- planned retries;
- theoretical max transport attempts;
- pagination count;
- document count;
- timeout;
- request hashes.

Alpha Vantage:

`0`

OpenDART new calls:

`0` by default.

If any budget cell is unknown/unbounded:
- no network;
- terminal boundedness gap.

---

# 21. Re-run complete stock owner for all 22

After offline fixes and any bounded follow-up:

re-run the exact complete stock owner.

For the four residual subjects report:

## SKHY
- selected financial-purpose source;
- financial period;
- current/prior availability;
- field lineage;
- context/direction eligibility;
- event evidence if already existing;
- final packet status.

## TSM
- fragment identity result;
- financial-purpose candidate result;
- current/prior period result;
- exact field comparison;
- final packet status.

## WRD
same requirements.

## 003690
- canonical insurance revenue lineage;
- current/prior occurrence;
- existing operating/net lineage;
- quality owner result;
- direction eligibility;
- final packet status.

For the 18 controls:
- invariance receipt and packet hash comparison.

---

# 22. Completion outcomes

## Outcome A — 22/22 complete

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV3_RESIDUAL_FINANCIAL_SEMANTICS_PASS`

Require:

- all three generic fixes PASS;
- 22/22 complete stock source/business packets;
- all 18 controls invariant;
- no threshold/validator relaxation;
- any SEC follow-up remained within frozen budget;
- full validation PASS;
- production side effects 0.

Then rebuild network-free source prequalification.

If full consumed graph passes:
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- generate the bounded R2B 24-message work instruction;
- do not execute R2B here.

## Outcome B — honest partial

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV3_RESIDUAL_FINANCIAL_SEMANTICS_PARTIAL`

Return exact remaining subject blocker such as:

- `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_BOUND`
- `NO_COMPARABLE_PERIOD`
- `FIELD_ABSENT`
- `FIELD_QUALITY_DENIED`
- `SOURCE_USE_DENIED`
- `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`
- other explicitly named source-semantic reason.

Do not broaden search automatically.

## Outcome C — generic owner boundedness fails

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV3_BOUNDEDNESS_GAP_REMAINS`

No follow-up calls.

---

# 23. No Market/Core/A/B in REV3

Required zero:

- stock OHLCV calls;
- Alpha Vantage;
- Massive;
- model calls;
- Market;
- Core;
- A;
- B;
- renderer;
- Telegram;
- recipient intent;
- production DB decision/warning writes;
- scheduler mutation;
- broker action;
- deploy;
- main merge;
- push;
- restart.

Only explicitly frozen bounded SEC FPI follow-up is allowed if offline replay proves it necessary.

---

# 24. Transport rules

For any authorized SEC follow-up:

- timeout: `600s`;
- max attempts: `3`;
- transient retries max `2`;
- byte-identical request only.

Retry:
- timeout;
- transient network/connection;
- provider transient server state under existing retry classification.

No retry:
- identity;
- purpose;
- period;
- source scope;
- semantic;
- quality;
- policy;
- schema;
- security.

Continue independent subjects after per-subject failure.

Systemic SEC security/config/identity drift stops the network phase immediately.

---

# 25. Validation

Required:

- same-document fragment tests;
- FPI purpose selection tests;
- FPI period/comparability tests;
- generic candidate-bound tests;
- exact SEC receipt tests if follow-up;
- insurance canonical-semantic tests;
- 003690 frozen-source regression;
- four residual subject replay;
- 18-control invariance suite;
- existing bounded-owner tests;
- previous R2B0/R1/R2/R3/R4/REV2 regressions;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- no new unexplained skip/xfail.

Do not loosen historical acceptance pins.

---

# 26. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R5-REV2 identity/SHA receipt
- repository identities
- changed-file inventory
- four-subject residual blocker matrix

## Fragment identity
- canonical SEC document identity contract
- fragment metamorphic tests
- TSM/WRD frozen diagnostics before/after

## Foreign purpose/period
- captured FPI candidate inventories for SKHY/TSM/WRD
- generic purpose classification matrix
- economic period matrix
- current/prior selection matrix
- rejected candidates with exact reason
- follow-up plan + SHA if executed
- planned/theoretical/actual/retry budget
- per-request receipts

## 003690
- standard IFRS insurance-revenue semantic registry receipt
- exact source rows
- current/prior lineage
- non-mapping negative matrix
- financial-quality before/after
- direction eligibility

## Cohort
- four residual packet matrix
- 18-control invariance matrix
- full 22 packet status/hashes
- exact remaining blockers
- network-free prequalification if reached
- R2B next instruction + SHA only if permitted

## Safety
- execution counters
- config/env/scheduler before/after
- validation logs
- secret scan
- bundle manifest.

---

# 27. Regression boundaries

Do not redesign:

- current price/OHLCV owners;
- CPNG anomaly isolation;
- technical evidence;
- bounded SEC/OpenDART acquisition architecture already proven in REV2;
- 18 completed stock packets except where generic replay proves a direct semantic bug;
- investment judgment policy;
- Overall / New Buyer / Holder policy;
- renderer/message policy;
- query-time snapshot contract;
- US/KR retry schedule design;
- primary/backup retirement design.

REV3 is a residual semantic closure, not another source-architecture rewrite.

---

# 28. Final principle

The remaining four subjects must be resolved by exact source meaning:

- Is this SEC document actually a financial-results document?
- What economic period does it own?
- Is current/prior comparison valid?
- Is this OpenDART concept really canonical revenue under standard IFRS semantics?

Do not resolve them by “latest”, “largest”, ticker exceptions, broader search, or threshold relaxation.
