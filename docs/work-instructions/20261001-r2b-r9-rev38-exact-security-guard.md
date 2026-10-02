# Thesis Monitor — R2B-R9-REV38
## Exact-Security Corporate-Action Guard + Current FY1 fPER Closure
### Reuse REV36 FY1 EPS + REV37 Unadjusted Completed-Session Close
### Replace All-Security KSD Queries with Exact SHT_CD Queries
### Wide Guard Envelope + Explicit Bounded Share-Unit Policy
### Compute Current FY1 fPER for Qualified Securities
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV38 supersedes every prior unexecuted post-REV37 current-FY1-fPER instruction. Execute only REV38.**

REV37 proved the important arithmetic inputs successfully:

- qualified KIS FY1 EPS:
  `7/8`;
- exact KIS unadjusted completed-session close:
  `7/7 eligible subjects`;
- latest completed session:
  `2026-09-30`;
- exact security/price/date/currency binding:
  PASS;
- Decimal arithmetic owner:
  implemented and tested;
- current FY1 fPER actually qualified:
  `0/8`.

The only live blocker was the corporate-action absence proof.

REV37 queried all securities at once with:

`SHT_CD=""`

for five KIS/KSD corporate-action routes.

That created three avoidable problems:

1. unrelated six-character alphanumeric identifiers caused the conservative global parser to reject the page;
2. `rev_split` returned 100 rows with `tr_cont=F`, creating continuation uncertainty;
3. all-security date-window completeness became much harder to reason about.

Official KIS generated examples explicitly support:

`SHT_CD=<specific stock code>`

for every required action family:

- merger/split;
- face-value replacement / split;
- bonus issue;
- paid-in capital increase;
- capital reduction.

REV38 therefore replaces the all-security guard with **exact monitored-security queries**.

This is a bounded current-fPER owner repair.
It is not a new full-fresh generation.

---

# 0. Newest SoT

Adopt REV37 as newest current-FY1-fPER SoT.

REV37 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev37-current-fy1-fper-report.zip`

SHA-256:

`0e6db44339d6d658d2650ee43d5a96a9ffbc5d916d171a47a0b9a8a6028eb473`

Independent verification:

- uploaded sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `406`;
- internal bundle manifest:
  `405/405`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

Terminal:

`R2B_R9_REV37_CORPORATE_ACTION_ROUTE_GAP`

Repository:

- base:
  `e974621759e6ab76296485a8e2b47d707be4c5a7`
- branch:
  `codex/r2b-r9-rev37-current-fy1-fper`
- instruction:
  `730cafe4789d4e5ab6e8244ca259705357935f72`
- implementation used for actual calls/final tests:
  `08dbc3f9a857d3784f2c6bca50710ecf6f4d3301`
- final:
  `f1b4e6bc37cd4614eeb77975e2541c0afa44d3ea`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

REV37 validation:

- focused:
  `396 passed`
- full:
  `7442 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- diff:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- secret scan:
  PASS.

REV37 calls:

- auth:
  `1`
- KIS action:
  `5`
- KIS daily price:
  `7`
- data calls:
  `12`
- retries:
  `0`
- estimate refresh:
  `0`
- models:
  `0`
- messages:
  `0/24`.

REV37 final free bytes:

`9,451,577,344`

REV38 is bounded.

---

# 1. Preserve current valuation inputs byte-identically

Do not refresh KIS FY1 estimates.

Do not refresh completed-session price unless a receipt is missing or hash-invalid.

Reuse accepted REV36/REV37 receipts.

## FY1 EPS qualified

000660:
- EPS:
  `378298.2`
- estimate date:
  `2026-07-29`.

005930:
- EPS:
  `46209`
- estimate date:
  `2026-07-30`.

005490:
- EPS:
  `29217.6`

010120:
- EPS:
  `3680.2`

012450:
- EPS:
  `49839.8`

047810:
- EPS:
  `2325.2`

086280:
- EPS:
  `22537.7`.

003690:
- EPS unavailable.

Use the exact estimate dates/periods from the REV36 per-security receipts for all seven subjects.
Do not infer missing dates from this work instruction.

## REV37 exact completed-session unadjusted closes

000660:
`1776000`

005930:
`268500`

005490:
`306000`

010120:
`205000`

012450:
`1007000`

047810:
`126200`

086280:
`196800`

Session:
`2026-09-30`

Price basis:
`KIS_UNADJUSTED_COMPLETED_SESSION_CLOSE`

These are sealed proof inputs, not hardcoded production constants.

---

# 2. Current FY1 fPER formula remains unchanged

Primary current metric:

`CurrentFY1Fper = completed_session_unadjusted_close / qualified_KIS_FY1_EPS`

Do not change:
- arithmetic;
- Decimal precision;
- N/M policy;
- display rounding;
- valuation-only role permissions.

Do not use KIS provider FY1 PER to derive or repair this metric.

Provider FY1 PER remains a separate dated research-snapshot metric.

---

# 3. Exact-security KIS/KSD action queries

The official KIS generated source documents that all required routes accept:

`SHT_CD=<specific stock code>`

rather than only blank/all-security mode.

REV38 must query each FY1-EPS-qualified security explicitly.

Subjects:

- 000660
- 005930
- 005490
- 010120
- 012450
- 047810
- 086280.

003690:
- no FY1 EPS;
- no corporate-action query required for current fPER.

---

# 4. Required action families

Per exact security, query:

1. merger/split
   - `/uapi/domestic-stock/v1/ksdinfo/merger-split`
   - TR:
     `HHKDB669104C0`

2. face-value replacement / split
   - `/uapi/domestic-stock/v1/ksdinfo/rev-split`
   - TR:
     `HHKDB669105C0`

3. bonus issue
   - `/uapi/domestic-stock/v1/ksdinfo/bonus-issue`
   - TR:
     `HHKDB669101C0`

4. paid-in capital increase by subscription-date basis
   - `/uapi/domestic-stock/v1/ksdinfo/paidin-capin`
   - TR:
     `HHKDB669100C0`
   - `GB1=1`

5. paid-in capital increase by record-date basis
   - same route/TR
   - `GB1=2`

6. capital reduction
   - `/uapi/domestic-stock/v1/ksdinfo/cap-dcrs`
   - TR:
     `HHKDB669106C0`.

Paid-in is deliberately queried under both official date modes.

Do not treat one mode as covering the other.

---

# 5. Why exact-security mode replaces REV37 all-security mode

Official KIS examples explicitly document:

- blank `SHT_CD`:
  all securities;
- exact code:
  specific-security query.

REV38 adopts exact-security mode as the corporate-action guard contract.

Benefits that must be proven from actual responses:

- no unrelated alphanumeric security IDs can invalidate a monitored subject;
- returned records are scoped to the exact requested security;
- row count is materially bounded;
- continuation pressure is reduced;
- absence applies to the requested security rather than to a locally filtered global page.

Do not globally relax the identifier parser.

An alphanumeric record for another security must never become a monitored-security match.

---

# 6. Exact-security response identity

For every action query:

require:

- request SHT_CD:
  exact six-digit monitored security;
- every nonempty returned monitored-identity field:
  compatible with that exact security;
- no cross-security row accepted;
- response hash;
- request hash;
- exact route/TR ID;
- query date envelope;
- continuation header;
- retrieval time.

If a response returns a conflicting security:
that family fails for the subject.

Do not use name matching to rescue it.

---

# 7. Wide corporate-action guard envelope

The KIS examples label most `F_DT/T_DT` parameters only as generic date ranges and do not fully establish which event
date drives filtering for every route.

REV38 therefore adopts an explicit **bounded product policy** rather than pretending the route proves an abstract
all-time effective-date theorem.

For each security:

- start:
  `FY1 estimate date - 365 calendar days`
- end:
  `completed-session price date + 365 calendar days`.

This is the:

`SHARE_UNIT_GUARD_ENVELOPE_V1`

It is intentionally wider than the critical arithmetic window.

The critical arithmetic window remains:

`estimate_date < share-unit-changing effect <= completed_session_price_date`.

The query envelope is wider only to catch:
- record dates before an effect;
- listing dates after a record date;
- subscription dates around rights issues;
- scheduling offsets.

Do not shrink the envelope merely to reduce rows.

---

# 8. Product-policy status of the guard

REV38 is explicitly authorized to qualify current FY1 fPER under:

`BOUNDED_EXACT_SECURITY_SHARE_UNIT_GUARD_V1`

when all conditions in this instruction pass.

This is a deliberate product policy.

It does **not** claim:
- KIS/KSD proves the absence of every possible corporate action for all time;
- every route's F_DT/T_DT is an effective-date filter.

It claims:

> exact-security official KIS/KSD schedule queries over a deliberately wide ±365-day envelope, across all relevant
> share-unit-changing schedule families, returned no action record that could affect the EPS/share basis between
> the KIS estimate snapshot and the completed-session close.

This is sufficient for the current FY1 fPER product metric.

Do not describe it as legal/corporate-action completeness outside this use case.

---

# 9. Event-date fields to inspect

For returned exact-security rows, preserve all source-owned date fields.

At minimum, by family where present:

- `record_date`
- `right_dt`
- `list_dt` / `list_date`
- `sub_term`
- `sub_term_ft`
- `td_stop_dt`
- other officially documented event dates.

Do not collapse them to one date.

No invented `effective_date`.

---

# 10. Conservative event blocking rule

A returned exact-security corporate-action row blocks current FY1 fPER when:

## Direct critical-window date
Any source-owned share-unit-relevant date falls:

`estimate_date < date <= price_date`

or:

## Straddling evidence
The row contains source-owned dates on both sides of the critical window such that the action process clearly spans
the estimate→price interval.

or:

## Ambiguous nearby action
A share-unit-changing row is returned by the wide guard query and its source-owned dates are insufficient to prove it
is wholly outside the critical interval.

For ambiguous exact-security action rows:
block.

Do not invent an adjustment.

---

# 11. Nonblocking rows

A row may be safely nonblocking only when every relevant source-owned event date proves the action is wholly:

- on/before estimate date; or
- after price date

and no interval field overlaps the critical window.

Keep the row in the audit.

Do not silently discard historical/future exact-security actions.

---

# 12. Empty exact-security response

An empty response may support the bounded absence guard only when:

- HTTP/provider status PASS;
- exact requested security recorded;
- query envelope correct;
- no transport error;
- continuation is terminal under the response contract;
- raw response retained;
- route contract accepts exact SHT_CD;
- no parser error.

Empty + successful exact-security bounded query is allowed evidence.

This differs from REV37's filtered all-security page absence.

---

# 13. Continuation policy

Per-security calls are expected to be small, but continuation remains fail-closed.

## Terminal
If the route returns a known terminal/no-more-data header:
accept.

## Continuation
If response indicates additional data:

do not truncate.

The official KIS generated corpus uses both:
- `M`
- and, in other generated routes, `F`

as next-page indicators.

However individual KSD examples are inconsistent.

Therefore REV38 must:

1. inspect the actual exact-security response;
2. inspect response/body CTS/cursor fields;
3. follow continuation only when the exact next-request cursor/header can be constructed from source-owned response
   fields and official shared transport conventions;
4. never resend an unchanged cursor/page and call that completion;
5. detect duplicate-page loops and fail that family.

If exact-security mode still returns unresolved continuation:

that family/subject remains:

`CORPORATE_ACTION_SOURCE_INCOMPLETE`.

Do not block all other subjects automatically.

---

# 14. No global parser rejection

Modify the action parser so:

- exact requested numeric monitored security is accepted;
- unrelated rows are ignored only when exact response identity proves they are not the requested security;
- alphanumeric official KSD identifiers elsewhere do not invalidate the whole parser;
- an alphanumeric row that conflicts with an exact-security response remains a route integrity error.

No `str.isdigit()` requirement over the entire page.

No promotion of an alphanumeric code to a monitored six-digit stock.

---

# 15. Per-security CorporateActionCompatibilityReceipt V2

Create:

`CorporateActionCompatibilityReceiptV2`

Fields:

- security;
- estimate date;
- price session date;
- guard envelope start/end;
- six route variants:
  - merger_split
  - rev_split
  - bonus_issue
  - paidin_capin_gb1
  - paidin_capin_gb2
  - cap_dcrs;
- query status;
- continuation status;
- raw response SHA(s);
- returned exact-security rows;
- all source dates;
- blocking decision;
- compatibility state.

States:

- `NO_RELEVANT_SHARE_UNIT_ACTION_FOUND_V1`
- `POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT`
- `CORPORATE_ACTION_SOURCE_INCOMPLETE`
- `CORPORATE_ACTION_IDENTITY_CONFLICT`
- other typed reason.

Only the first state permits current FY1 fPER arithmetic.

---

# 16. Reuse REV37 price receipts

Do not make seven daily-price calls again.

Verify byte/hash identity of the REV37 price receipts.

Require:
- exact security;
- session:
  `2026-09-30`;
- unadjusted basis:
  `FID_ORG_ADJ_PRC=0`;
- selected completed session;
- raw source hash.

If a price receipt is missing or hash-invalid:
that security is unavailable in REV38.

Do not refresh it automatically.

REV39/full integration will acquire fresh prices.

---

# 17. Compute actual current FY1 fPER

For each security with:

- qualified REV36 FY1 EPS;
- verified REV37 unadjusted close;
- V2 corporate-action compatibility:
  `NO_RELEVANT_SHARE_UNIT_ACTION_FOUND_V1`;

compute:

`CurrentFY1Fper = close / FY1 EPS`

using the already-tested Decimal arithmetic.

No provider PER involved in the calculation.

Persist:

- numerator;
- denominator;
- exact quotient/fraction;
- 2-decimal display;
- EPS estimate date;
- price session date;
- corporate-action receipt hash.

This time actual arithmetic **must** be performed for qualifying real subjects.

No synthetic-only proof.

---

# 18. Provider FY1 PER remains secondary

Preserve REV36 provider FY1 PER where available.

For each security with both:

- current FY1 fPER;
- KIS provider FY1 PER;

create a diagnostic comparison:

- current derived;
- provider research snapshot;
- difference;
- ratio;
- price-date vs research-date distinction.

Do not:
- demand equality;
- alter either value;
- use provider PER to validate current arithmetic.

---

# 19. KR8 typed matrix

Produce all eight subjects.

For:

003690:
- current fPER:
  `UNAVAILABLE_EPS`.

For other subjects:
one of:

- `QUALIFIED_CURRENT_PRICE_FY1_FPER`
- `UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_ACTION`
- `UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE`
- `UNAVAILABLE_PRICE_RECEIPT`
- other exact typed reason.

No numeric coverage target.

Actual share-unit event may legitimately deny one security.

---

# 20. Expected arithmetic is not a qualification target

Do not hardcode current fPER values.

The work instruction may not be used to target a desired multiple.

Production code must derive only from:
- sealed REV36 EPS;
- sealed REV37 close;
- V2 action guard.

Tests for live fixtures may assert exact reproduced output after the owner computes it.

No manual number injection.

---

# 21. Transport pacing fix

REV37 disclosed:

auth completion → first data request:
`0.991985 seconds`

below the intended 1.1 seconds.

REV38 must reset the monotonic pacing timestamp **after authentication completes**.

Require:

- auth completion → first data request:
  `>= 1.1 sec`
- every data completion → next data request:
  `>= 1.1 sec`.

No extra API call merely to test pacing.

Record actual timing.

---

# 22. Call plan

Seven FY1-EPS-qualified securities × six action variants:

maximum initial action requests:

`42`

No price requests.

No estimate requests.

No OpenDART.

Continuation calls are allowed only under Section 13.

Hard KIS action-data call maximum including continuation:

`60`

excluding one normal authentication operation.

This cap is an instruction safety budget, not a provider quota.

Sequential only.
No parallel calls.

---

# 23. Bounded batching

To reduce risk:

execute in deterministic subject order:

1. 000660
2. 005930
3. 005490
4. 010120
5. 012450
6. 047810
7. 086280.

Within each subject:
use a deterministic route order.

Do not stop after a subject qualifies merely to save calls unless:
- a hard transport/rate/secret failure occurs.

Complete the seven-subject typed matrix where possible.

---

# 24. Rate-limit behavior

If KIS returns:

`EGW00201`

or another explicit rate-limit state:

- do not immediately retry;
- stop further external calls for the run;
- preserve completed subjects;
- terminal:
  `R2B_R9_REV38_KIS_RATE_LIMIT_GAP`.

Do not classify unqueried subjects as clean.

---

# 25. Credential policy

The user explicitly accepts continued use of the existing KIS credential pair.

Use secure local configuration only.

Never log/archive:
- App Key;
- Secret;
- access token;
- Authorization header.

If exposed:
stop:

`R2B_R9_REV38_KIS_SECRET_EXPOSURE_GAP`.

Do not archive the exposed output.

---

# 26. External transmission approval

REV38 explicitly authorizes:

- one normal KIS auth;
- exact-security read-only KIS/KSD action queries in Sections 3–4;
- bounded continuation under Section 13;
- official KIS repository/API documentation reads;
- secret-scanned result ZIP/SHA upload to the existing iCloud Drive / Thesis Monitor folder.

No:
- estimate-perform;
- daily-price refresh;
- FnGuide;
- Alpha Vantage;
- models;
- Telegram;
- orders;
- production DB writes;
- scheduler mutation;
- deploy;
- main merge;
- push;
- restart.

No additional approval required for this exact scope.

---

# 27. No broad full-fresh / no models

REV38 must not run:

- all22 source collection;
- KR broad fresh collection;
- US collection;
- Market;
- Market/Core/A/B;
- exact24.

Models:
`0`

Messages:
`0/24`

Telegram:
`0`.

REV39 is the production integration/full-fresh task if REV38 passes.

---

# 28. Disk guard

REV37 final free:

`9,451,577,344 bytes`

REV38 is bounded.

Before external calls require:

`>= 8 GiB`

If below:
perform safe temporary test/report scratch cleanup only.

Do not delete:
- REV31 blind artifacts;
- accepted REV31-C1 result;
- REV36/REV37 immutable archives;
- sealed price/EPS receipts.

No full-generation GC in REV38.

---

# 29. Offline tests before calls

Require:

## Exact-security routes
- exact SHT_CD positive;
- blank/all-security not used;
- wrong returned security negative;
- alphanumeric unrelated row does not globally poison exact request;
- conflicting alphanumeric exact-request row fails.

## Guard envelope
- estimate-365 / price+365;
- correct critical window;
- exact boundaries.

## Event decisions
- date in critical window blocks;
- straddling interval blocks;
- ambiguous exact-security action blocks;
- wholly pre-estimate nonblocking;
- wholly post-price nonblocking.

## Empty
- successful terminal empty qualifies;
- transport failed empty does not;
- continuation unresolved empty does not.

## Continuation
- source-owned cursor positive;
- duplicate page loop negative;
- unchanged cursor negative;
- unknown status negative.

## Arithmetic
- qualified V2 guard allows real receipt;
- incomplete guard blocks;
- event blocks;
- EPS unavailable;
- Decimal rounding.

No ticker-specific route behavior.

---

# 30. Validation after acquisition

Require:

- focused REV38 tests;
- REV32–37 KIS regressions;
- actual seven-subject action receipt replay;
- actual price receipt replay;
- actual FY1 EPS receipt replay;
- current PER/PBR regression;
- valuation authority isolation;
- whole-source registry tests if owner code is registered;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No PASS if full suite is red.

No hotfix after first external action query.
If code/contract needs repair after live acquisition begins:
stop and issue a new bounded revision.

---

# 31. Success terminal

If:

- all six action variants are complete for each qualifying subject or produce an honest event denial;
- exact-security V2 guard closes;
- actual current FY1 fPER arithmetic is performed for every security whose guard qualifies;
- KR8 typed matrix is complete;
- full validation is green;

use:

`R2B_R9_REV38_EXACT_SECURITY_CURRENT_FY1_FPER_PASS_READY_FOR_FULL_FRESH_INTEGRATION`

This does not require:
- 003690 numeric fPER;
- all seven positive subjects to qualify if a real action correctly blocks one.

It does require:
- no unresolved action-source state for a subject declared qualified.

---

# 32. Honest stop terminals

- `R2B_R9_REV38_EXACT_SECURITY_ACTION_ROUTE_GAP`
- `R2B_R9_REV38_ACTION_CONTINUATION_GAP`
- `R2B_R9_REV38_ACTION_IDENTITY_CONFLICT`
- `R2B_R9_REV38_POST_ESTIMATE_SHARE_UNIT_ACTION`
- `R2B_R9_REV38_CURRENT_FY1_FPER_GAP`
- `R2B_R9_REV38_KIS_RATE_LIMIT_GAP`
- `R2B_R9_REV38_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV38_DISK_GUARD`
- `R2B_R9_REV38_VALIDATION_GAP`.

Do not solve by:
- all-security fallback;
- arbitrary action-date invention;
- omitting a required action family;
- treating incomplete continuation as empty;
- using provider FY1 PER instead of current arithmetic.

---

# 33. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV37 identity/SHA
- repository identities
- changed files
- bundle manifest.

## Preserved inputs
- REV36 FY1 EPS receipt identities
- REV37 price receipt identities
- no estimate refresh receipt
- no price refresh receipt.

## Action plan
- official exact-security route review
- query envelope per subject
- six route variants per subject
- pacing plan.

## Raw action evidence
- request/response/receipt per subject/family
- continuation headers/cursors
- raw hashes
- exact returned rows.

## V2 guard
- per-subject date-field audit
- event classification
- compatibility receipt.

## Current fPER
- KR8 typed matrix
- actual arithmetic receipts
- exact quotient/display values
- provider FY1 PER comparison diagnostic.

## Validation
- focused/full/Ruff/diff/knowledge
- actual-source replay
- secret scan.

## Safety
- auth count
- action calls
- continuation calls
- estimate calls 0
- price calls 0
- FnGuide 0
- Alpha 0
- models 0
- messages 0
- Telegram 0
- production mutations 0.

---

# 34. Next handoff

If PASS, prepare REV39 recommendation only.

REV39 should:

1. integrate fresh KIS estimate-perform into normal KR source acquisition;
2. qualify FY1 EPS through the accepted output3 owner;
3. acquire fresh KIS unadjusted completed-session close;
4. run exact-security V2 corporate-action guard;
5. compute current FY1 fPER;
6. preserve KIS provider FY1 PER as secondary;
7. preserve existing current PER/PBR;
8. expose forward valuation only to Valuation + B/NewBuyer/Holder;
9. archive-backed GC before full-fresh if disk <12 GiB;
10. run one full-fresh/replay/model/exact24 proof.

Do not execute REV39 inside REV38.

---

# 35. Final principle

REV37 showed the arithmetic path is already sound.

The remaining blocker came from choosing the wrong acquisition topology for the corporate-action guard:

all-security pages created unrelated identifiers, pagination pressure and ambiguous global absence.

Official KIS supports exact-security corporate-action queries.

Use them.

For a practical current forward multiple, the relevant contract is:

- exact KIS FY1 EPS;
- exact unadjusted completed-session close;
- exact security;
- broad exact-security corporate-action guard around the estimate→price interval;
- no relevant share-unit-changing action.

Under that bounded product policy, calculate the current FY1 fPER directly from the acquired values.

Do not let unrelated global KSD rows prevent a valid per-security arithmetic metric.
