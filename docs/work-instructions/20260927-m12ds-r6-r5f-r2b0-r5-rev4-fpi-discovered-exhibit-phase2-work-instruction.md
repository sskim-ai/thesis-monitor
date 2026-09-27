# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV4
## FPI Discovered-Exhibit Phase-2 Closure
### Fetch only exact selector-eligible HTML exhibits already discovered and sealed by REV3; no new discovery/search expansion

**Purpose:** close the remaining TSM/WRD source-coverage gap created by REV3's intentionally frozen first-phase manifest. REV3 already performed bounded candidate/index/primary-document collection and discovered exact selector-eligible financial exhibit URLs after the manifest was frozen. This task introduces a generic two-phase FPI acquisition contract and performs one bounded phase-2 fetch using only those already-discovered URLs. SKHY receives no new discovery or network expansion.

No OpenDART calls. No OHLCV calls. No Alpha/Massive. No Market/Core/A/B. No messages. No scheduler mutation.

---

# 0. Newest accepted SoT

Adopt R5-REV3 as newest SoT.

REV3 result ZIP SHA-256:

`3cd387be5c553e52d94470c2ab158e49dadf961b719ad0cde522ec6fbdab0e78`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV3_RESIDUAL_FINANCIAL_SEMANTICS_PARTIAL`

Bundle integrity independently verified:

- ZIP/sidecar SHA exact;
- manifest entries: `542/542`;
- missing: `0`;
- hash/size mismatch: `0`;
- ZIP contains those 542 entries plus `bundle-manifest.json`.

Repository identities:

- base:
  `45e90cb8d66bd1ade51439ba34bbd212ea8b2236`
- REV3 instruction:
  `09a15038bc57d8b48d96bacbdbdd57ec4de06f50`
- acquisition-frozen implementation:
  `932856b9805e69be2c5fc3c494cbf3e3087f613c`
- final implementation:
  `aacfe8a5f2cfe6f94e4bd99b01acc4ce4654512b`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted REV3 facts:

- complete stock packets: `19/22`
- newly complete: `003690`
- blocked:
  - `SKHY`
  - `TSM`
  - `WRD`
- 18 prior controls remain invariant;
- 003690 insurance revenue semantic closure PASS;
- SEC same-document fragment identity fix PASS;
- FPI financial-purpose/period owner added;
- first bounded follow-up:
  - SKHY `14/14` logical/HTTP, retries `0`
  - TSM `14/14`, retries `0`
  - WRD `14/14`, retries `0`
  - total `42/42`, retries `0`
- no additional discovery;
- OpenDART new calls: `0`;
- model/Market/Core/A/B/render/send/scheduler/DB/deploy: `0`.

Validation:

- focused `809 PASS`;
- full `5797 PASS / 63 unchanged skips / 0 failures`;
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke: PASS.

Do not overwrite REV3.

---

# 1. Exact residual states

## SKHY

Current terminal source state:

- `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_BOUND`
- `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`
- `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION`

REV3 inspected the frozen eight-candidate FPI window and fetched each planned primary/index document.

`unrequested-exhibit-diagnostics.json` shows **no newly discovered selector-eligible exhibit URL** for SKHY in that bounded window.

Therefore:

- REV4 must make `0` SKHY network calls;
- no candidate-window expansion;
- no extra discovery;
- no older annual substitution;
- no event-query broadening.

SKHY remains an honest blocked control unless a pure offline bug is discovered in the already-captured bytes.

## TSM

REV3 phase-1 discovered an exact selector-eligible exhibit after reading the already-frozen filing index/primary:

Filing:
- accession `0001046179-26-000541`
- form `6-K`
- filing date `2026-08-14`
- SEC report date `2026-06-30`

Already-discovered exact HTML exhibit:

`https://www.sec.gov/Archives/edgar/data/1046179/000104617926000541/a2026q2consolidatedreport-.htm`

REV3 did not fetch it because the URL was unknown before the phase-1 manifest was frozen.

This is **not new discovery in REV4**. It is a sealed output of REV3.

## WRD

REV3 phase-1 discovered selector-eligible HTML financial exhibit candidates after the phase-1 manifest was frozen.

Frozen exact HTML candidates include:

1. accession `0001104659-26-107261`
   - filing date `2026-09-14`
   - SEC report date `2026-06-30`
   - exhibit:
     `https://www.sec.gov/Archives/edgar/data/1867729/000110465926107261/wrd-20260914xex99d1.htm`

2. accession `0001104659-26-094852`
   - filing date `2026-08-12`
   - exhibit:
     `https://www.sec.gov/Archives/edgar/data/1867729/000110465926094852/tm2622690d1_ex99-1.htm`

3. accession `0001104659-26-082931`
   - filing date `2026-07-13`
   - exhibit:
     `https://www.sec.gov/Archives/edgar/data/1867729/000110465926082931/tm2620306d1_ex99-1.htm`

Image/JPG assets discovered in the same indexes are **not authorized** by default.

REV4 must not introduce OCR/image-based financial extraction.

---

# 2. Why a second phase is legitimate

REV3 correctly required:

> every request URL must be known before the phase-1 network operation starts.

That contract prevented a newly discovered exhibit link from being fetched inside the same immutable request manifest.

The generic solution is a **two-phase bounded FPI acquisition protocol**:

## Phase 1 — candidate/index/primary

- bounded candidate filings;
- frozen phase-1 request manifest;
- fetch index/primary documents only;
- derive selector-eligible exhibit URLs from captured source bytes;
- seal discovery output.

## Phase 2 — exact discovered exhibits

- no new filing discovery;
- create a new immutable phase-2 manifest from the sealed phase-1 discovery output;
- enforce a finite generic exhibit cap;
- fetch only exact selector-eligible documents in that manifest;
- no recursive exhibit traversal.

This preserves pre-network boundedness for every phase.

Do not weaken the rule by allowing dynamic follow-links in the middle of a frozen phase.

---

# 3. Generic Phase-2 owner contract

Implement a generic contract equivalent to:

`FPI_DISCOVERED_EXHIBIT_PHASE2`

Inputs:

- sealed phase-1 result ID/hash;
- issuer/security identity;
- filing/accession identity;
- already-discovered selector-eligible URLs;
- document type/MIME eligibility;
- generic exhibit cap;
- exact phase-2 manifest hash.

Output:

- per-exhibit source receipt;
- source SHA;
- filing/accession owner binding;
- purpose/period parsing;
- occurrence lineage;
- phase-2 result hash.

No ticker-specific branch.

---

# 4. Generic exhibit eligibility

A phase-2 URL may enter the manifest only if it was already present in the sealed REV3 phase-1 diagnostics and passes generic eligibility.

Required:

- approved SEC archive host;
- same issuer/CIK;
- same accession directory;
- exact discovered URL;
- existing selector marked it eligible for financial-purpose inspection;
- document type supported by the existing financial parser.

For REV4, supported phase-2 document types are text/HTML/XML documents already supported by the existing parser.

Do not fetch:

- JPG/PNG/image attachments;
- arbitrary PDF/image requiring OCR;
- unrelated corporate exhibits;
- links not present in the sealed discovery output.

If a future owner wants image/OCR financial extraction, that is a separate task.

---

# 5. Generic Phase-2 cap

Before implementation/network, define and test a finite generic cap:

`SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT`

Requirements:

- same cap for all FPI subjects;
- no ticker override;
- finite integer;
- large enough to represent the exact frozen REV4 manifest;
- no recursive phase-3 discovery;
- excess discovered eligible URLs produce:
  `FPI_PHASE2_EXHIBIT_BOUND_EXHAUSTED`.

Tests at minimum:

- 0 URLs;
- 1 URL;
- at cap;
- over cap;
- duplicate URL;
- image/non-supported type;
- wrong accession/issuer.

Do not repeatedly increase the cap until a subject passes.

---

# 6. Phase-2 manifest — freeze before network

Generate:

`fpi-phase2-exhibit-plan.json`

from the sealed REV3 discovery artifacts.

The plan must include:

- source REV3 ZIP/hash;
- subject;
- issuer/CIK;
- accession;
- exact source filing metadata;
- exact exhibit URL;
- document identity;
- purpose of fetch:
  `FINANCIAL_PURPOSE_INSPECTION`;
- logical request ID;
- request hash;
- timeout;
- retry policy;
- sequence/order;
- stop condition;
- generic cap.

The plan SHA must be frozen before the first request.

No URL absent from this file may be requested.

---

# 7. Network budget

Expected maximum from the currently sealed REV3 diagnostics:

- SKHY: `0`
- TSM: up to `1`
- WRD: up to `3`

Maximum logical exhibit requests:

`4`

The exact plan must be generated from sealed artifacts; if the resulting eligible HTML count differs from 4, use the artifact-derived exact integer and explain the discrepancy before network access.

For each request:

- timeout `600s`;
- initial attempt `1`;
- transient retries max `2`;
- max attempts `3`;
- byte-identical retry only.

Theoretical maximum transport attempts for 4 logical requests:

`12`

If logical request count is N:

`theoretical max attempts = N * 3`.

Alpha Vantage = `0`.
OpenDART = `0`.
Stock OHLCV = `0`.

---

# 8. Sequential processing and early stop

The frozen plan may list multiple WRD exhibits.

Execution may stop requesting later WRD plan entries **only if** the existing generic owner has already proven a complete qualified current/prior financial evidence set and no further planned document is required by the typed contract.

Requirements:

- skipped planned entries are recorded as:
  `NOT_REQUIRED_AFTER_QUALIFIED_SELECTION`;
- not counted as failures;
- the plan itself remains immutable;
- no unplanned request may replace them.

For TSM, the single frozen exhibit is attempted unless pre-network offline evidence proves it is not needed.

SKHY makes no request.

---

# 9. No discovery expansion

REV4 may not:

- request newer/older SEC submission pages;
- enlarge the eight-candidate window;
- fetch a ninth candidate;
- run generic SEC discovery again;
- add new accessions;
- browse SEC manually;
- broaden event/news search;
- substitute annual 20-F for missing current interim evidence merely to get PASS.

REV4 is only phase-2 completion of sources **already discovered by REV3**.

---

# 10. Parse exhibits through the existing generic financial owner

For each captured exhibit:

- preserve exact source bytes/hash;
- bind issuer/accession;
- classify financial purpose;
- derive economic financial period from source-owned financial content;
- extract canonical financial field occurrences using existing owner/parser;
- preserve current/prior rows;
- preserve currency/unit;
- preserve statement/accounting basis;
- preserve exact occurrence IDs;
- run existing quality/source-use owner unchanged.

Do not add ticker-specific concept mappings.

Do not select numbers by magnitude/latest/plausibility.

---

# 11. TSM acceptance

TSM may become complete only if the newly captured exact exhibit proves sufficient current financial evidence under the generic owner.

At minimum:

- exact issuer/security;
- exact accession;
- financial purpose;
- current financial period;
- canonical field occurrence(s);
- comparable prior occurrence(s) or another existing approved directional fact;
- period compatibility;
- unit/currency;
- quality/source-use.

Preserve existing TSM denials not actually resolved.

Do not mark PASS simply because the exhibit filename says `consolidatedreport`.

---

# 12. WRD acceptance

WRD may become complete only from generic source semantics.

Process frozen eligible HTML exhibits in the planned order.

Do not use JPG assets.

Require:

- exact source document;
- financial-purpose proof;
- economic period;
- canonical field occurrences;
- comparable prior evidence if direction is used;
- quality/source-use.

If none of the already-discovered phase-2 documents qualifies:

WRD remains:

`NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE2_BOUND`

or a more exact field/period blocker.

Do not open a new discovery phase automatically.

---

# 13. SKHY closure behavior

No new network.

Re-run SKHY from the sealed REV3 corpus under the unchanged generic owner.

If still blocked, record the stronger final bounded state:

`NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE1_AND_NO_PHASE2_ELIGIBLE_EXHIBIT`

plus the existing:

`FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`

where applicable.

Do not search further in REV4.

If a pure offline parser bug is discovered in captured bytes:
- fix generically;
- prove via fixture;
- no new source call.

---

# 14. 003690 and 19 complete subjects are frozen controls

Current complete subjects include 003690, bringing the control set to `19`.

All 19 must remain invariant unless a directly affected generic helper requires a semantically equivalent serialization change.

At minimum preserve:

- CPNG anomaly isolation;
- SNDK event authority;
- 005930/047810 prior authority;
- 000660 denied operating/net comparison state;
- 003690 exact insurance-revenue semantics and packet hash/evidence.

Any unrelated control regression blocks PASS.

---

# 15. Re-run 22-subject complete stock owner

After phase-2 processing, re-run all 22 through the same complete owner.

Report:

- packet status;
- packet hash;
- financial source status;
- event status;
- observed-business union;
- direction eligibility;
- exact denials.

Expected possibilities:

## 22/22
Full stock source/business prequalification may proceed.

## 21/22
Likely SKHY remains honestly blocked while TSM/WRD close.

Do not hide the remaining blocker.

## 19/22 or 20/22
Preserve exact TSM/WRD failures.

No automatic expansion.

---

# 16. Network-free source prequalification

Only if all 22 complete stock packets PASS:

combine with accepted:

- market source owners;
- KRX night/history replay;
- B/C/D source mechanics;
- run seed.

Then require:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

and generate bounded R2B instruction.

If <22/22:
- do not generate a misleading full 24-message R2B instruction;
- return exact remaining product/source decision needed.

---

# 17. Completion terminals

## Full 22/22

`M12DS_R6_R5F_R2B0_R5_REV4_FPI_PHASE2_SOURCE_PREQUALIFICATION_PASS`

Requires:
- generic phase-2 owner PASS;
- all planned/needed requests within frozen budget;
- 22/22 complete packets;
- 19 controls invariant;
- full validation;
- no production side effects;
- R2B instruction generated.

## Honest partial

`M12DS_R6_R5F_R2B0_R5_REV4_FPI_PHASE2_PARTIAL`

Return exact remaining subjects/reasons.

No search expansion.

## Boundedness/identity failure before network

`M12DS_R6_R5F_R2B0_R5_REV4_PHASE2_BOUNDEDNESS_GAP`

Provider calls remain zero.

## Systemic SEC stop

`M12DS_R6_R5F_R2B0_R5_REV4_SYSTEMIC_SEC_STOP`

Only for:
- SEC identity/security drift;
- config/secret integrity failure;
- request-plan mismatch;
- budget enforcement failure.

Per-document 404/semantic/field/period denial is not systemic; continue independent planned entries.

---

# 18. Transport rules

Allowed:
- only exact manifest-listed SEC HTML/text exhibit requests.

Required zero:
- SEC discovery calls;
- SEC submission calls;
- OpenDART calls;
- OHLCV calls;
- Alpha Vantage;
- Massive;
- model;
- Market/Core/A/B;
- render;
- Telegram;
- recipient intent;
- production DB writes;
- scheduler mutation;
- broker;
- deploy;
- merge/push/restart.

For authorized exhibit requests:
- timeout `600s`;
- max attempts `3`;
- transient retries max `2`;
- byte-identical retries only.

No retry for:
- 4xx semantic/source denial;
- identity;
- period;
- purpose;
- schema;
- quality;
- source-use.

---

# 19. Validation

Required:

- phase-2 manifest generation tests;
- generic cap tests;
- eligible-type tests;
- wrong issuer/accession/url negatives;
- no recursive discovery proof;
- TSM frozen exhibit replay;
- WRD frozen exhibit replay;
- SKHY zero-request proof;
- FPI purpose/period regressions;
- financial field lineage tests;
- 19-control invariance;
- full 22 packet replay;
- prior REV2/REV3 bounded owner regression;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- no new unexplained skip/xfail.

Do not relax selection/quality thresholds.

---

# 20. Required result bundle

Return immutable ZIP + `.sha256` including at minimum:

- `REPORT.md`
- `summary.json`
- REV3 result identity/SHA receipt
- repository identities
- changed-file inventory

## Phase-2 contract
- generic two-phase acquisition contract
- generic exhibit cap + rationale
- manifest generator proof
- `fpi-phase2-exhibit-plan.json`
- plan SHA
- planned/theoretical/actual request budget
- retries
- skipped-as-not-required entries

## Source receipts
- exact TSM exhibit receipt(s)
- exact WRD exhibit receipt(s)
- raw source hashes
- issuer/accession bindings
- purpose/period extraction
- field occurrence lineage
- quality/source-use

## SKHY
- zero-network receipt
- final bounded blocker proof

## Cohort
- TSM packet result
- WRD packet result
- SKHY packet result
- 19-control invariance
- full 22 matrix/hashes
- exact remaining blockers
- network-free prequalification if reached
- R2B next instruction + SHA only if 22/22 permits it

## Safety/validation
- execution counters
- config/env/scheduler before-after
- full validation
- secret scan
- bundle manifest.

---

# 21. Final principle

REV3 already found the next source links.

REV4 must **consume only those already-discovered, selector-eligible source documents under a new immutable phase-2 budget**.

It must not turn “an exhibit was discovered after manifest freeze” into permission for open-ended SEC crawling.
