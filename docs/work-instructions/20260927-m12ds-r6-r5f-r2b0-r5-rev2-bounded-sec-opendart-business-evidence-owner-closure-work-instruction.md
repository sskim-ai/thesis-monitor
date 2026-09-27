# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV2
## Bounded SEC / OpenDART Financial-Business Evidence Owner Closure
### Generic bounded owner → frozen cohort replay → bounded current acquisition → 22-subject stock source/business prequalification

**This instruction supersedes the unexecuted R2B0-R5 “no-new-business-event normal-state” instruction. Do not execute that prior R5 instruction.**

**Primary objective:** close the financial/business-evidence source-owner gap generically for US SEC and KR OpenDART without ticker exceptions, validator weakening, event-query broadening, or synthetic lineage. The task ends at stock source/business-evidence prequalification. It must not run Market/Core/A/B or generate the 24-message corpus.

---

# 0. Latest SoT recheck — R4 is authoritative

Newest accepted result for this scope:

- R2B0-R4 result ZIP SHA-256:
  `58c35eeb01e5caca3bd8d2b120e4becc3f7bf245a9b6b3b35310e993c274f5aa`
- terminal:
  `M12DS_R6_R5F_R2B0_R4_EVENT_BUSINESS_UNION_PARTIAL`
- result integrity:
  - ZIP/sidecar exact;
  - internal manifest `318/318`;
  - missing/hash/size/extra mismatch `0`.

Repository at R4:
- base:
  `a0de7b591c33ac5cc0f5c449def29c1460a2d539`
- instruction:
  `b6650eefbcd0688db9320e6b823c790518818b4d`
- implementation/final:
  `35fe0ce35160bb5199f2c8db00c927ff78ea9c0a`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

R4 accepted facts:

- stock source roles verified: `88/88`;
- current price eligible: `22/22`;
- CPNG historical OHLC anomaly remains source-preserved and consumer-scoped;
- CPNG mandatory technical blocker: `0`;
- event plan executed: `20/20 logical`, `20 HTTP`, retry `0`;
- newly complete through event evidence: `SNDK`;
- existing complete controls: `005930`, `047810`;
- complete stock packets: `3/22`;
- blocked stock packets: `19/22`;
- selected new events consumed: `1`;
- stock OHLCV calls during R4: `0`;
- SEC financial refresh: `0`;
- OpenDART recovery: `0`;
- Alpha/Massive/model/render/send/scheduler mutation: `0`.

R4 explicitly leaves open:

- `SEC_FINANCIAL_TRANSPORT_PLAN_UNBOUNDED`
- `OPENDART_FINANCIAL_DISCOVERY_PLAN_UNBOUNDED`

The 20-request event experiment is evidence that broadening event/news search is not the primary next solution. Do not broaden event queries or relax event classifiers in this task.

If any later uploaded result artifact conflicts with this instruction, the later verified artifact wins.

---

# 1. Current blocker matrix — freeze before implementation

The task must first regenerate and freeze a machine-readable blocker matrix from the R4/R3 sealed artifacts and current repository owners.

The preliminary R4 diagnosis below is the starting point; the audit must refine it rather than assume it.

## 1.1 Already complete invariance controls

| Subject | Market | Current state | Control requirement |
|---|---|---|---|
| SNDK | US | PASS via existing event-owner admission | must remain PASS for the same accepted reason unless a new independent qualified financial owner additionally succeeds |
| 005930 | KR | PASS via existing financial/business owner | must remain PASS; no unrelated regression |
| 047810 | KR | PASS via existing financial/business owner | must remain PASS; no unrelated regression |

Do not reacquire these subjects merely to make counts symmetric unless a network-free frozen replay specifically proves generic owner invariance.

## 1.2 Blocked US subjects — SEC family

Blocked US13:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- TSLA
- TSM
- WRD
- WULF

Current R4/Class-C state is broadly:

- `project_reported_financial`
- `UNAVAILABLE`
- selected metric lineage for revenue / operating income / net income is not qualified.

This does **not** prove that the provider has no financial data.

For each US subject classify into one exact blocker category:

1. `NO_PROVIDER_SOURCE`
2. `ACQUISITION_ROUTE_UNBOUNDED`
3. `DOCUMENT_UNAVAILABLE`
4. `FIELD_ABSENT`
5. `LINEAGE_UNRESOLVED`
6. `PERIOD_NOT_COMPARABLE`
7. `STATEMENT_BASIS_MISMATCH`
8. `UNIT_OR_CURRENCY_MISMATCH`
9. `FIELD_QUALITY_DENIED`
10. `SOURCE_USE_OWNER_MISSING`
11. `SECURITY_IDENTITY_UNRESOLVED`
12. `OTHER_EXACTLY_NAMED`

Multiple field-level blockers may exist for one subject. Do not collapse them into one whole-company status if fields differ.

## 1.3 Blocked KR subjects — OpenDART family

Blocked KR6:

- 000660
- 003690
- 005490
- 010120
- 012450
- 086280

Known R4 frozen findings to preserve:

### 000660
Existing OpenDART selected revenue / operating-income rows:
- exact filing ID present;
- single-quarter role present;
- consolidated basis present;
- KRW present;
- lineage status `verified_tainted`;
- current financial owner rejects them for critical quality reasons.

Classify this primarily as:
`FIELD_QUALITY_DENIED`
unless a bounded new acquisition produces a different eligible current source.

### 003690
Existing owner:
- selected financial tuple mismatch;
- no mixed-filing synthesis permitted.

Classify at least:
`LINEAGE_OR_COMPATIBLE_TUPLE_MISMATCH`.

### 005490 / 010120 / 012450 / 086280
Existing OpenDART preliminary/saved rows have lineage but the selected revenue / operating-income fields fail the current statement/source-use contract, including unverified statement/currency semantics in the existing envelope.

Classify field-by-field after owner audit; do not assume the same repair applies to all four.

---

# 2. Target of this task

Build a **generic bounded financial/business evidence acquisition owner** for:

- US SEC
- KR OpenDART

and prove:

1. every network stage has a finite precomputable upper bound;
2. every consumed field has exact document/period/occurrence lineage;
3. current/prior comparative compatibility is explicit;
4. field-level quality/source-use is independent;
5. no absolute-current-only value is promoted to directional business evidence;
6. the same generic owner applies to the full cohort;
7. current one-shot acquisition runs non-fail-fast across independent subjects;
8. final stock source/business prequalification is honest even if not 22/22.

Do not target “22 PASS at any cost”.

---

# 3. US SEC owner audit — decompose the entire path

Audit the real current SEC financial call graph from the existing owner.

At minimum inspect:

- `SecFinancialSnapshotService.refresh`
- `SecFinancialSnapshotService._scan_foreign_filings`
- security/CIK/issuer-type owner
- submissions/discovery functions
- filing-index/document traversal
- linked exhibit traversal
- 10-Q / 10-K handling
- 20-F / 6-K handling
- company facts / XBRL / table extraction owners
- field selection
- current/prior occurrence selection
- canonical projection
- financial quality/source-use owner.

R3 already proved the current route is unbounded:

- foreign-filing discovery is entered from `refresh`;
- the five-6-K limit does not cap filing-index requests, linked exhibits, or all 20-F requests;
- offline examples with 0 / 3 / 9 exhibits produced 3 / 6 / 12 requests.

Preserve that finding until the new owner contract proves otherwise.

---

# 4. US SEC bounded design — stages must be separately bounded

The owner must explicitly separate these stages.

## SEC-A — issuer/security identity

Input from already-qualified local security master:

- canonical security ID;
- issuer/company ID;
- ticker;
- CIK;
- issuer type;
- exchange/security class;
- ADR/foreign issuer metadata where applicable.

No network discovery may start before exact issuer ownership passes.

Identity failure:
- no retry;
- subject blocked.

## SEC-B — filing discovery

Create a finite `SECDiscoveryPlan`.

It must specify before execution:

- allowed form families by issuer type;
- maximum discovery/index requests;
- maximum pages/files inspected;
- maximum candidate filings admitted;
- time/period search boundary;
- current/prior target roles.

Do not “scan until something useful appears”.

Cap exhaustion must produce:
`SEC_DISCOVERY_BOUND_EXHAUSTED`

and preserve the subject as blocked.

## SEC-C — document selection

Select a finite candidate set from the bounded discovery result.

Selection must be deterministic from:

- issuer type;
- form/document type;
- filing date;
- financial period;
- report role;
- exact existing policy.

Forbidden:

- latest-looking document;
- largest value;
- ticker-specific accession;
- manual accession list;
- one-company fallback.

## SEC-D — document fetch

Generate a finite `SECDocumentFetchPlan`.

Before requests, freeze:

- selected filing IDs/accessions;
- primary document count;
- filing-index count;
- linked exhibit count;
- XBRL/instance/table artifacts needed;
- exact maximum document calls per selected filing.

Every linked exhibit request must consume a declared slot.

Do not fetch “all exhibits”.

Bound exhaustion:
`SEC_DOCUMENT_BOUND_EXHAUSTED`

## SEC-E — XBRL/table extraction

Once source documents are fetched, extraction is local/offline.

Preserve:

- source document SHA;
- source row/occurrence identity;
- concept/account identity;
- raw value/text;
- unit/currency;
- period start/end;
- instant/duration role;
- statement/table context.

No additional network call may occur from extraction.

## SEC-F — current/prior occurrence pairing

For each canonical field, select explicit current/prior occurrences.

Do not require all financial fields to share one occurrence if the actual statement semantics are field-specific.

But each directional pair must pass the compatibility contract in Section 8.

## SEC-G — canonical field projection

Map source concepts/rows to the existing canonical semantic owner.

No new “best effort” semantic aliasing.

Ambiguous mapping:
- field unavailable;
- unrelated clean fields remain independently eligible.

## SEC-H — observed-direction eligibility

Direction is local/offline and field-specific.

No directional claim from a lone absolute current value.

---

# 5. KR OpenDART owner audit — decompose the entire path

Audit the real OpenDART path including:

- `OpenDartRecoveryClient.discover`
- filing/report search owner
- `total_page` handling
- filing selection
- statement/account fetch
- preliminary/formal report distinction
- CFS/OFS basis
- period-role mapping
- metric selection
- current/prior occurrence owner
- field quality
- canonical field projection
- directional eligibility.

R3 already proved:

`discover(limit=1)` is **not** a network bound because it can fetch every `total_page` page before selecting one filing.

Preserve that finding until fixed.

---

# 6. KR OpenDART bounded design

## DART-A — security/corp identity

Use the accepted local:

- canonical security ID;
- corp code;
- ticker;
- legal issuer identity.

Identity mismatch:
- no retry;
- block subject.

## DART-B — search/discovery bound

Create a finite `OpenDartDiscoveryPlan`.

It must specify before execution:

- exact report/form family;
- date/period search window;
- `MAX_DISCOVERY_PAGES`;
- `MAX_CANDIDATE_FILINGS`;
- current/prior target roles.

The transport layer itself must stop at the page cap.

Do not fetch `total_page` pages merely because the API reports that many.

Cap exhaustion:
`OPENDART_DISCOVERY_BOUND_EXHAUSTED`

## DART-C — document/report selection

Selection must be deterministic from:

- corp code;
- report type;
- period;
- formal/preliminary role;
- CFS/OFS requirements;
- existing owner policy.

Do not mix revenue from one filing with operating income from another unless the existing field-level contract explicitly permits them as independent evidence; never manufacture a synthetic earnings envelope.

## DART-D — financial statement/metric fetch bound

Freeze a finite request list for the selected current/prior reports before fetching.

The plan must state:

- report IDs;
- statement endpoints/owners;
- maximum statement requests per filing;
- maximum supplementary requests;
- exact total logical calls.

No hidden pagination.

## DART-E — statement/metric extraction

Offline after fetch.

Preserve exact:

- filing/report ID;
- row/account identity;
- statement section;
- CFS/OFS;
- source column;
- current/prior column;
- period;
- currency/unit;
- raw value;
- source artifact hash.

## DART-F — period/comparative lineage

Explicitly distinguish:

- single-quarter;
- cumulative/YTD;
- annual/FY;
- preliminary vs formal;
- current vs prior comparable.

Do not compare a single quarter to cumulative/YTD.

Do not compare consolidated to separate.

## DART-G — field-level quality

Evaluate each field independently.

A tainted revenue field must not automatically destroy an unrelated clean net-income field.

A clean field must not rescue a separate tainted/conflicted field.

Existing financial quality thresholds remain unchanged.

## DART-H — directional eligibility

Only compatible current/prior or another already-approved observed directional fact may produce direction.

---

# 7. Generic bounded constants — freeze before live acquisition

Do not hardcode ticker-specific limits.

During the offline audit, define generic finite constants for each provider/issuer class.

At minimum freeze:

## SEC
- `SEC_MAX_DISCOVERY_REQUESTS`
- `SEC_MAX_DISCOVERY_PAGES_OR_INDEX_FILES`
- `SEC_MAX_CANDIDATE_FILINGS`
- `SEC_MAX_SELECTED_CURRENT_FILINGS`
- `SEC_MAX_SELECTED_PRIOR_FILINGS`
- `SEC_MAX_DOCUMENTS_PER_FILING`
- `SEC_MAX_LINKED_EXHIBITS_PER_FILING`
- `SEC_MAX_TOTAL_LOGICAL_REQUESTS_PER_SUBJECT`

If domestic-US and foreign-private-issuer paths legitimately need different generic caps, use **issuer-class caps**, not ticker caps.

## OpenDART
- `DART_MAX_DISCOVERY_PAGES`
- `DART_MAX_CANDIDATE_FILINGS`
- `DART_MAX_SELECTED_CURRENT_FILINGS`
- `DART_MAX_SELECTED_PRIOR_FILINGS`
- `DART_MAX_STATEMENT_REQUESTS_PER_FILING`
- `DART_MAX_TOTAL_LOGICAL_REQUESTS_PER_SUBJECT`

Every constant must have:

- code owner;
- rationale;
- fixture/metamorphic proof;
- fail-closed exhaustion behavior.

If finite generic caps cannot be defined without changing provider/source semantics, stop before live acquisition.

---

# 8. Field / period / occurrence lineage contract

Every financial field admitted into stock business evidence must carry a field-level lineage object with at least:

- canonical company ID;
- canonical security ID;
- ticker;
- provider;
- provider issuer ID (`CIK` or `corp_code`);
- filing/report/document ID;
- form/report type;
- filing/publication date;
- source artifact SHA;
- source row/occurrence ID;
- statement/table identity;
- canonical financial field semantic;
- raw source concept/account;
- period start;
- period end;
- fiscal year/quarter where applicable;
- period role:
  - `SINGLE_QUARTER`
  - `CUMULATIVE_YTD`
  - `ANNUAL`
  - `INSTANT`
  - other existing explicitly typed role;
- current/prior role;
- statement basis:
  - consolidated/separate;
- currency;
- unit/scaling;
- source type:
  - formal/preliminary/etc.;
- field quality state;
- source-use eligibility;
- exact extraction/normalization owner version;
- normalized field hash.

No lineage object:
- no field admission.

---

# 9. Comparative compatibility contract

A current/prior pair may produce observed direction only if all required dimensions are compatible.

At minimum require:

- same canonical issuer/security ownership;
- same canonical financial field semantic;
- current period strictly after prior period;
- compatible period role;
- comparable duration/span;
- same statement basis;
- same currency/unit/scaling unless an existing explicit deterministic conversion owner is already approved;
- both field lineages source-use eligible;
- both pass field-quality requirements;
- no source ambiguity;
- no mixed incompatible filings presented as one tuple.

Examples of compatible structures may include, where existing policy permits:

- Q vs comparable Q;
- YTD vs same-span prior YTD;
- FY vs prior FY.

Examples that must not be silently compared:

- Q vs YTD;
- CFS vs OFS;
- preliminary source with unknown statement contract vs formal source when the existing policy requires formal comparability;
- different currencies without an approved conversion owner.

---

# 10. Absolute amount is context, not direction

A single current financial amount may be:

`ABSOLUTE_CONTEXT_ELIGIBLE`

if exact source lineage and source-use rules permit it.

It must **not** become:

- growth;
- improvement/deterioration;
- expansion/contraction;
- positive/negative business direction

without a compatible comparative observation or another existing approved directional fact.

The packet must separately expose:

- `context_eligible`
- `direction_eligible`

per field.

Do not conflate them.

---

# 11. Field-level source quality / partial survival

Replace any inappropriate envelope-wide failure behavior only where the current owner wrongly couples unrelated fields.

Required rule:

> Eligibility is field-specific first; aggregate/business evidence is built only from fields that individually qualify.

If revenue is conflicted:
- revenue direction unavailable.

If operating income is independently clean:
- operating-income evidence may survive.

The reverse also applies.

Do not let one clean field mark all sibling fields clean.

Do not weaken a true whole-envelope invariant where the existing accounting contract genuinely requires a tuple; document such cases explicitly.

---

# 12. Current R4 cohort blocker reclassification output

Before code implementation completes, produce:

`current-blocker-matrix-v2.json`

for all 22 subjects.

For each subject/field include:

- market;
- source family;
- current packet status;
- current event status;
- existing provider data present? `YES/NO/UNKNOWN`;
- acquisition route bounded? `YES/NO`;
- selected source document available? `YES/NO/UNKNOWN`;
- field occurrence available? `YES/NO/UNKNOWN`;
- field lineage qualified? `YES/NO`;
- period compatibility state;
- statement basis state;
- currency/unit state;
- field quality state;
- source-use state;
- direction eligibility state;
- exact blocker enum.

This matrix must distinguish:

- provider source truly absent;
- source exists but old acquisition was unbounded;
- acquisition bounded but document missing;
- field missing;
- lineage missing;
- field quality denied;
- period incompatibility;
- source-use owner missing.

Do not report all failures as `observed_business_union=0`.

---

# 13. Offline/metamorphic proof before any network

No provider calls until all bounded-owner tests pass.

## 13.1 SEC metamorphic boundedness

Use synthetic/offline transport fixtures covering at minimum:

- 0 linked exhibits;
- 3 linked exhibits;
- 9 linked exhibits;
- 99 linked exhibits;
- multiple 6-Ks;
- multiple 20-Fs;
- domestic 10-Q/10-K;
- foreign-private-issuer path.

Prove:

- request count never exceeds generic cap;
- cap exhaustion stops cleanly;
- no hidden traversal after exhaustion;
- selected filing/document logic is deterministic;
- no ticker exceptions.

Reproduce the old 0/3/9 exhibit counterexample and prove the repaired request count saturates at the declared bound.

## 13.2 OpenDART metamorphic boundedness

Use `total_page` fixture values at minimum:

- 1
- 3
- 9
- 99

Prove:

- `limit=1` no longer implies fetching all pages;
- network pages never exceed `DART_MAX_DISCOVERY_PAGES`;
- cap exhaustion yields explicit blocked state;
- deterministic filing selection from only the admitted bounded page set;
- no ticker exceptions.

## 13.3 Field lineage tests

Cover:

- exact issuer positive/negative;
- field occurrence identity;
- period role;
- current/prior compatibility;
- statement basis;
- currency/unit;
- formal/preliminary distinctions;
- field-level taint;
- clean sibling survival;
- conflicted sibling remains denied;
- absolute current amount cannot produce direction.

---

# 14. Frozen cohort replay — all 22 subjects

After generic tests pass, replay the frozen existing cohort offline through the new owner logic.

Use no network.

Purpose:

- prove generic owner applies to all 22;
- classify existing artifacts honestly;
- detect regressions before current acquisition.

Mandatory controls:

## 005930
Must remain complete for the same accepted source semantics.

## 047810
Must remain complete for the same accepted source semantics.

## SNDK
Must remain complete via its existing event evidence even if SEC financial evidence remains unavailable.

Do not require a financial PASS to preserve SNDK.

## CPNG
Price/anomaly/technical status must remain unchanged.

No financial repair may reopen OHLCV work.

Frozen replay output must include per-field lineage and exact blocker states even when a subject remains blocked.

---

# 15. Request budget — mandatory pre-network artifact

Before current acquisition, generate a deterministic:

`financial-acquisition-plan.json`

and SHA.

It must list every logical request for the live one-shot phase.

## Current acquisition subjects

Run financial acquisition only for the currently blocked R4 cohort:

### US13
- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- TSLA
- TSM
- WRD
- WULF

### KR6
- 000660
- 003690
- 005490
- 010120
- 012450
- 086280

Do not reacquire 005930 / 047810 / SNDK merely for symmetry.

The generic owners are already proven against them in frozen replay.

## Provider budget ledger

For each provider, freeze before the first call:

| Metric | SEC | OpenDART |
|---|---:|---:|
| subjects | 13 | 6 |
| planned logical requests | exact integer required | exact integer required |
| theoretical max logical requests | exact integer required | exact integer required |
| planned pagination requests | exact integer required | exact integer required |
| theoretical max pagination requests | exact integer required | exact integer required |
| planned document requests | exact integer required | exact integer required |
| theoretical max document requests | exact integer required | exact integer required |
| planned retries | 0 initially | 0 initially |
| theoretical max transport attempts | exact integer | exact integer |

Theoretical max transport attempts must account for the retry rule in Section 16.

No request may execute if any required budget cell is `unknown`, `null`, `unbounded`, or derived only after the request starts.

---

# 16. Transport / retry contract

For every declared SEC/OpenDART request:

- timeout: `600 seconds`
- first attempt: `1`
- transient retries: maximum `2`
- maximum attempts: `3`

Retries are allowed **only** for byte-identical requests after:

- transport timeout;
- transient network error;
- transient process/connection failure;
- provider transient server failure if the current transport policy already classifies it as retryable.

Every retry:
- consumes budget;
- preserves the same request body/URL/parameters;
- receives a new transport-attempt receipt.

No retry for:

- schema failure;
- semantic failure;
- source-use failure;
- financial-quality failure;
- policy failure;
- security identity failure;
- issuer mismatch;
- document identity mismatch;
- period mismatch;
- statement basis mismatch;
- currency/unit mismatch;
- line/field lineage failure.

Theoretical max transport attempts:

`sum(theoretical_max_logical_requests_per_provider) * 3`

unless an endpoint has an explicitly smaller retry cap.

---

# 17. Current one-shot acquisition — non-fail-fast across subjects

After all offline proofs and budget freeze PASS, execute the current one-shot financial acquisition.

Requirements:

- use only existing SEC/OpenDART provider owners;
- no Alpha;
- no Massive;
- no event/news search expansion;
- no alternative financial provider;
- no manual web fallback.

If one subject fails:
- preserve exact failure;
- continue every independent remaining subject/provider acquisition.

Do not stop at the first blocked subject.

Immediate stop is allowed only for a systemic condition affecting trust/safety, including:

- provider authentication/security compromise;
- provider issuer/security identity drift that invalidates the plan globally;
- request-plan hash mismatch;
- owner code/config drift from the frozen plan;
- secret/config integrity failure;
- unexpected provider/source family;
- budget enforcement failure capable of exceeding declared maximum.

A per-subject `BOUND_EXHAUSTED`, missing document, missing field, quality denial, or period incompatibility is **not** a systemic stop.

---

# 18. Current acquisition receipts

For every logical request and transport attempt preserve:

- provider;
- subject;
- issuer/security IDs;
- stage:
  - discovery
  - document
  - statement
  - other explicitly named owner stage;
- request-plan ID;
- exact request hash;
- attempt ordinal;
- timestamp;
- timeout policy;
- retry reason if any;
- HTTP/provider status;
- raw response/source artifact hash;
- pagination page identity;
- filing/report/document ID;
- success/failure;
- failure class.

Provider summary must report:

- planned logical calls;
- theoretical max logical calls;
- actual logical calls;
- actual transport attempts;
- actual retries;
- planned pagination;
- actual pagination;
- planned document fetches;
- actual document fetches;
- cap-exhausted subjects.

Alpha Vantage:

`planned = 0`
`actual = 0`

The user's account-wide Alpha budget remains `25/day`; this task must not consume it.

---

# 19. Current financial field projection

After each subject's bounded acquisition finishes, project fields locally.

Do not perform further network calls during projection.

For every candidate field:

1. exact issuer/security owner;
2. exact document/report;
3. exact period;
4. period role;
5. statement basis;
6. currency/unit;
7. raw occurrence;
8. canonical field semantic;
9. quality;
10. source-use eligibility;
11. current/prior compatibility;
12. context eligibility;
13. direction eligibility.

No latest/largest/closest-value heuristic.

No mixed provider.

No historical/current provider comparison without exact lineage compatibility.

---

# 20. Business evidence construction

The task is financial/business evidence owner closure, not just data collection.

Build source-owned business evidence only from qualified fields.

## Absolute context

A single qualified current amount may enter factual financial context when the existing schema permits.

It must not create direction.

## Directional observed evidence

Require either:

- compatible current/prior field pair; or
- another existing policy-approved observed directional financial fact.

Direction examples:
- revenue up/down;
- operating income up/down;
- margin expansion/contraction;
- other existing canonical directional field.

Each directional proposition must point to the exact two (or explicitly approved set of) source occurrences that support it.

No comparative lineage:
- no direction.

---

# 21. 22-subject stock source + business-evidence prequalification

After the one-shot acquisition:

combine:

- sealed accepted stock OHLCV/current-price owners;
- accepted CPNG anomaly isolation;
- accepted technical evidence;
- accepted identity/thesis baseline;
- newly acquired bounded SEC/OpenDART financial fields;
- preserved existing event evidence where already qualified;
- existing complete controls.

Re-run the complete stock owner for all 22.

Goal:

`22/22 STOCK SOURCE + BUSINESS EVIDENCE PREQUALIFICATION`

But honest partial completion is valid.

For every subject produce:

- price/technical status;
- financial provider/source family;
- exact field availability;
- exact current/prior pair availability;
- field-quality status;
- source-use status;
- business direction evidence;
- event evidence status;
- observed-business union cardinality;
- final packet status;
- exact blocker(s);
- packet hash if complete.

---

# 22. Existing complete controls — strict invariance

## 005930
Must not regress for reasons unrelated to the bounded financial owner repair.

## 047810
Must not regress for reasons unrelated to the bounded financial owner repair.

## SNDK
Must retain its existing event-based complete path even if its SEC financial acquisition remains blocked.

A new financial owner may add independently qualified evidence, but it must not replace or rewrite existing accepted evidence without an explicit reason.

Any unrelated break in these three controls is a regression and blocks PASS.

---

# 23. Field-level independence tests

Mandatory tests must prove:

1. revenue denied / operating-income clean:
   - revenue remains unavailable;
   - operating-income may survive if independently qualified.

2. operating-income denied / revenue clean:
   - inverse behavior.

3. current clean / prior incompatible:
   - absolute context may survive;
   - direction unavailable.

4. one field tainted:
   - unrelated clean field not globally killed.

5. one clean field:
   - conflicted sibling not rescued.

6. envelope-level invariant genuinely required by existing schema:
   - remains strict.

7. 003690:
   - no mixed-filing synthetic tuple.

8. 000660:
   - current quality thresholds unchanged.

---

# 24. Stop / success terminals

## Offline boundedness cannot close

`M12DS_R6_R5F_R2B0_R5_REV2_FINANCIAL_OWNER_BOUNDEDNESS_GAP_REMAINS`

Use when a provider owner still cannot emit a finite exact theoretical max before network.

Provider calls for that provider must remain `0`.

## Systemic execution stop

`M12DS_R6_R5F_R2B0_R5_REV2_SYSTEMIC_PROVIDER_STOP`

Only for the systemic conditions in Section 17.

Preserve all completed independent work.

## Current acquisition completed but prequalification partial

`M12DS_R6_R5F_R2B0_R5_REV2_FINANCIAL_BUSINESS_PREQUALIFICATION_PARTIAL`

Use when some subjects honestly remain blocked because:
- provider source absent;
- bounded discovery exhausted;
- document unavailable;
- field absent;
- lineage unresolved;
- comparable prior missing;
- period incompatibility;
- statement-basis mismatch;
- unit/currency mismatch;
- field-quality denial;
- source-use denial.

Do not hide these.

## Full success

`M12DS_R6_R5F_R2B0_R5_REV2_BOUNDED_SEC_OPENDART_BUSINESS_PREQUALIFICATION_PASS`

Require:

- bounded SEC owner PASS;
- bounded OpenDART owner PASS;
- exact finite request budget frozen before calls;
- current one-shot completed;
- all required field lineage/source-use receipts;
- 22/22 stock source + business-evidence prequalification;
- 005930/047810/SNDK invariance;
- full validation PASS;
- production side effects 0.

---

# 25. R2B / Market-Core-A-B remain blocked in this task

Do not run:

- Market model;
- Core model;
- A;
- B;
- 24-message generation;
- renderer;
- Telegram;
- production delivery.

Even if 22/22 prequalification succeeds, this task ends by generating the next bounded R2B instruction only.

Do not execute R2B here.

---

# 26. R2B next instruction — generate only after full or accepted partial source closure

If full success, generate an immutable R2B instruction for:

- current source cohort;
- exact query-time snapshot;
- existing Market/Core/A/B;
- US15 + KR9 = 24 rendered messages;
- send/delivery = 0;
- scheduler mutation = 0.

If partial, do **not** generate a misleading 24-message instruction unless the remaining blocked subjects are explicitly accepted by a later product decision.

---

# 27. Production side effects — hard zero

Throughout this task:

- Telegram/send = `0`
- recipient intent = `0`
- production DB decision/warning writes = `0`
- scheduler mutation = `0`
- notification mutation = `0`
- broker action = `0`
- deploy = `0`
- service restart = `0`
- main merge = `0`
- remote push = `0`
- model calls = `0`
- Market/Core/A/B = `0`
- rendered messages = `0`
- Alpha Vantage calls = `0`

Use private/isolated staging persistence for current acquisition artifacts.

---

# 28. Regression boundaries — do not redesign accepted work

Do not change unless a directly proven integration bug requires the smallest repair:

- stock current-price owner;
- OHLCV owner;
- R2B0 sealed 88-role price corpus;
- CPNG historical-anomaly isolation;
- CPNG technical evidence;
- technical indicator policy;
- 005930 / 047810 / SNDK accepted completion reasons;
- investment judgment policy;
- Overall policy;
- New Buyer policy;
- Holder policy;
- renderer/message policy;
- query-time snapshot semantics;
- US 08:10→08:15→08:20 conditional recollection policy;
- KR 16:00→16:05→16:10 conditional recollection policy;
- no-primary/backup scheduler design.

No event-query broadening.

No classifier/threshold relaxation.

---

# 29. Validation sequence

Run in this exact order.

## Phase 1 — generic fixture / metamorphic

- SEC boundedness;
- OpenDART boundedness;
- field lineage;
- period compatibility;
- field-level quality independence;
- retry classification;
- budget accounting.

No network.

## Phase 2 — frozen full-cohort replay

- all US14 + KR8;
- existing complete controls;
- existing R4 financial states;
- no network.

## Phase 3 — bounded acquisition proof

- exact plan;
- exact theoretical max;
- request hashes;
- provider budgets;
- secret/config fingerprints.

No network until all plan validations PASS.

## Phase 4 — current one-shot acquisition

- blocked US13 + KR6;
- non-fail-fast;
- systemic stop only;
- full receipts/budgets.

## Phase 5 — network-free 22-subject prequalification

Replay only captured source artifacts + accepted sealed price/technical evidence.

No further network.

## Phase 6 — repository validation

- focused tests;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- disabled unified entrypoint smoke;
- secret scan;
- no new unexplained skip/xfail.

---

# 30. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R4 SoT identity/SHA receipt
- R3 boundedness evidence receipt
- repository base/instruction/implementation/final SHAs
- changed-file inventory

## Blocker classification
- `current-blocker-matrix-v2.json`
- US13 classification
- KR6 classification
- 005930/047810/SNDK control matrix

## SEC design/proof
- SEC call graph
- SEC bounded constants
- SEC theoretical-max formula
- SEC fixture/metamorphic proof
- domestic/FPI route matrix
- SEC request-plan schema

## OpenDART design/proof
- OpenDART call graph
- OpenDART bounded constants
- OpenDART theoretical-max formula
- total_page metamorphic proof
- report/statement route matrix
- OpenDART request-plan schema

## Financial semantics
- field-lineage schema
- period/comparability matrix
- statement-basis matrix
- currency/unit matrix
- field-quality/source-use matrix
- context-vs-direction eligibility matrix

## Request budget
- `financial-acquisition-plan.json`
- plan SHA
- per-provider:
  - planned calls
  - theoretical max calls
  - actual calls
  - retries
  - pagination
  - cap-exhaustion counts
- Alpha calls = 0 receipt

## Current acquisition
- per-request/attempt receipts
- raw/source artifact hashes
- issuer/security receipts
- filing/report/document receipts
- field occurrence receipts
- extraction/normalization receipts
- subject blocker receipts

## Cohort prequalification
- 22-subject source/business matrix
- directional-evidence matrix
- packet statuses/hashes
- exact blocked reasons
- invariance controls

## Validation/safety
- execution counters
- config/env before/after
- scheduler before/after
- DB isolation receipt
- focused/full validation
- secret scan
- bundle manifest
- next R2B instruction + SHA only on permitted success.

---

# 31. Final operating principle

The objective is not to maximize the number of PASS subjects.

The objective is:

> A generic bounded SEC/OpenDART owner that knows exactly what it may request, exactly what document/row/period each field comes from, exactly when two observations are comparable, and exactly when a field may influence business direction.

If a provider or document cannot support that contract, return the subject/field as honestly BLOCKED.
