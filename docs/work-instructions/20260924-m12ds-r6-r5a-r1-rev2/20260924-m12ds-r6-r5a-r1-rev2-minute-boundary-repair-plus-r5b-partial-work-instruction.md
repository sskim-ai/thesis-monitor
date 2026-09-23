# Thesis Monitor — M12DS-R6-R5A-R1 Minute-Boundary Repair + Next Actual Cutoff Re-observation

**Suggested result branch:** `codex/m12ds-r6-r5a-r1-boundary-repair`  
**Suggested preparation terminal:** `M12DS_R6_R5A_R1_BOUNDARY_REPAIR_READY_FOR_NEXT_CUTOFF`  
**Suggested successful observation terminal:** `M12DS_R6_R5A_R1_ACTUAL_CUTOFF_OBSERVATION_COMPLETE`

## 0. Source of truth

Treat the following uploaded result as the newest SoT:

- R6-R5A result ZIP SHA-256:
  `7e641cd64dceeb7af6d68a6bdc22786ad48d20f5e2352fa855dfdc9a0799a16a`
- R6-R5A result terminal:
  `M12DS_R6_R5A_CUTOFF_OBSERVATION_PARTIAL`
- R6-R5A final local SHA:
  `b016d1a6d9437594df986208c9434cea39e71a8f`
- operating main:
  `2097645892e30d84aba435416f98e7f9545a87fa`
- operating main must remain unchanged unless separately authorized.

Preserve the original R6-R5A report and raw artifacts byte-for-byte. Do not rewrite or
"complete" the missing 08:10/08:15/08:20 windows.

## 1. Accepted findings from R6-R5A

The 2026-09-24 KST run targeting the completed 2026-09-23 US regular session is accepted
as a valid **PARTIAL** observation.

Observed:

- 08:05 KST:
  - 28/28 raw responses
  - full22 adjusted `usa06012` availability 22/22
  - strict validity 22/22
  - all requests began and ended in the owned minute
- 08:10 / 08:15 / 08:20:
  - 0/28 requests
  - failure occurred before the first AAPL provider request
  - receipt timestamps were about 2–3 ms before each intended slot
  - `configured_minute_exhausted`
  - provider retries 0
  - backfill 0

The failure mechanism is accepted as:

`single duration sleep -> early wake by a few milliseconds -> exact-minute guard rejects`

Do not relabel this as a Kiwoom/provider outage.

### Quote finding that must be preserved

At actual 08:05 KST:

- SPY `base_close_pric = 773.3800`
- SOXX `base_close_pric = 572.7800`
- XLC `base_close_pric = 113.5300`

For all three, the value and the quote previous O/H/L tuple matched the **2026-09-22**
daily row, not the target 2026-09-23 daily row.

Therefore:

`usa20100.base_close_pric` is **not proven as the just-completed target-session close owner
at 08:05**.

Do not promote this 3-symbol result to an unsupported full22 claim, but do preserve it as
negative qualification evidence.

The remaining Kiwoom candidate is the dated `usa06012` daily-row close. Its regular-session
finality is still unproven.

## 2. R5B-PARTIAL is allowed from the valid 08:05 frozen cutoff evidence

Do not advance the source gate to full R6-R5B or treat R6-R5A as complete.

However, the existing 08:05 cutoff observation is valid owned evidence and must not be
discarded:

- full22 adjusted `usa06012` availability 22/22;
- strict validity 22/22;
- requests owned by the actual 08:05 KST window;
- frozen target session 2026-09-23 values preserved in the existing
  `later-comparison-handoff.json`.

Therefore, once the **existing frozen R5 later-window condition** is satisfied, a separate
read-only **R5B-PARTIAL delayed historical comparison** is explicitly allowed against those
frozen 2026-09-23 target values.

This partial comparison is qualification-only. It does not make R6-R5A complete and it
does not waive the missing 08:10 / 08:15 / 08:20 intra-window evidence.

The original R6-R5A proof still requires all four windows:

- 08:05
- 08:10
- 08:15
- 08:20 KST

because intra-window mutation is evidence.

The minute-boundary wait defect remains the smallest blocker for completing that proof.
The repaired R5A-R1 four-window observation must therefore still run on the next eligible
actual cutoff date.

R5B-PARTIAL and R5A-R1 are independent qualification tracks:

- R5B-PARTIAL may use only the already frozen valid 08:05 evidence plus later historical
  same-date reads under the frozen R5 later-window contract;
- R5A-R1 repairs collection timing and obtains the missing complete four-window cutoff
  observation;
- neither task substitutes for the other.

## 3. Scope of this repair

Patch only the observer timing/wait behavior needed to prevent an early timer return from
being misclassified as an exhausted configured minute.

Allowed implementation scope:

- `scripts/m12ds_r6_r5_cutoff_observer.py`
- focused tests for the timing helper / cutoff loop
- date-shifted plan preparation code or offline utility if required
- work-instruction/report-only support files

Do NOT change:

- symbol universe
- exchange routes
- API ids
- endpoints
- request bodies
- adjusted/raw mode semantics
- SPY/SOXX/XLC diagnostic subset
- existing 0.6 s inter-request pacing — unchanged
- request timeout
- no-retry policy
- same-minute ownership requirement
- source authority rules
- `review_cutoff` semantics
- `later_historical_comparison` semantics
- Market/Core/A/B prompts or validators
- production scheduling
- delivery or DB behavior.

## 4. Required timing repair

Introduce a bounded **not-before-slot** wait.

Required semantics:

1. Before a configured slot, wait until wall clock is `>= slot`.
2. A sleep that returns early must cause another short wait/check, not immediate
   `configured_minute_exhausted`.
3. No provider request may begin before `slot`.
4. Once the slot minute is entered, the existing same-minute ownership guard remains
   active.
5. If the process is suspended or delayed past the owned minute, record
   `MISSED_NOT_BACKFILLED`; never issue a late substitute request.
6. The wait loop is not a provider retry.
7. Provider attempts remain one per planned request and `retries=0`.
8. Do not use a detached task, daemon, launchd, cron, ChatGPT automation, or background
   sleeper.

Implementation may use repeated bounded sleeps and wall-clock checks. Do not weaken
ownership to a tolerance such as "within ±N ms".

### Required boundary tests

At minimum prove offline:

- sleep returns at `slot - 3 ms` -> no provider request yet -> wait again -> request starts
  at/after slot;
- sleep returns at `slot - 1 ms` multiple times -> still no early request and no false
  exhaustion;
- process arrives within the owned minute -> collection proceeds;
- process arrives after the owned minute -> `MISSED_NOT_BACKFILLED`;
- request crossing out of the owned minute remains rejected by existing strict validation;
- no retry/backfill path is introduced;
- provider call count is unchanged;
- four configured windows remain distinct.

No real provider call is allowed for these tests.

## 5. Frozen route and request contract

Original route SHA-256:

`c3020384e933286760e33d03a627b26cd662753a4cb3f5c893b111d36b9a8c7e`

Original R6-R5A plan SHA-256:

`018c17edb00fd78181ae3f3627785b678dd854dc11689c7c1fd5b14290930f8f`

Original request-array SHA-256:

`b7b3c835ed25de038838513fc09400aabf439e93f2a96994fa9c2404c863f9ec`

The original plan is date-specific (`cutoff_date=2026-09-24`, target `2026-09-23`), so a
legitimate next-day plan cannot have the same whole-file SHA.

Do **not** falsify or hand-edit this fact.

For the next eligible run:

1. preserve the original plan file and SHA as the parent evidence;
2. generate the next plan deterministically through the existing `plan(day, routes)`
   contract;
3. record:
   - `parent_plan_sha256 = 018c17...`
   - new derived plan SHA-256
   - route SHA-256 unchanged
   - request-array SHA-256 unchanged at
     `b7b3c835ed25de038838513fc09400aabf439e93f2a96994fa9c2404c863f9ec`;
4. assert exact request-array equality with the parent plan;
5. assert unchanged:
   - request count 28/sample
   - cutoff max 112 calls
   - later max 28 calls
   - quote subset SPY/SOXX/XLC
   - retries 0
   - auth max 1/invocation
   - scheduler registration false
   - authority promotion false.

A changed request-array hash is a hard stop.

## 6. Next actual observation date

Expected next run:

- KST cutoff date: **2026-09-25**
- expected completed US target session: **2026-09-24**

But verify with XNYS dynamically. Do not hardcode acceptance solely from these expected
dates.

Owned windows:

- 08:05
- 08:10
- 08:15
- 08:20 KST

Preferred manual foreground start:

- 08:04 KST

If the date is not an eligible XNYS context, do not fabricate a run. Derive the next
eligible cutoff date and regenerate only the date-bound plan fields while preserving the
request contract.

## 7. Preparation behavior when executed before the actual window

If this work instruction is executed outside the valid actual cutoff window:

- implement the boundary repair;
- run focused/full/Ruff/diff/knowledge validation;
- generate and hash the derived next-day plan;
- produce the exact foreground command for the next actual window;
- do **not** call Kiwoom data APIs merely to test readiness;
- do **not** wait overnight;
- do **not** create a scheduler.

Stop at:

`M12DS_R6_R5A_R1_BOUNDARY_REPAIR_READY_FOR_NEXT_CUTOFF`

Return a structural report and ZIP/SHA.

## 8. Actual re-observation behavior

Only when manually launched inside the valid actual cutoff window:

At each of the four windows collect exactly the same frozen request set:

### Full canonical universe
- full22 adjusted `usa06012`

### Diagnostic subset
For SPY / SOXX / XLC:
- raw `usa06012`
- `usa20100`

Preserve per request:

- actual start/end KST/UTC/ET
- symbol
- exchange route
- API id
- canonical request hash
- HTTP/provider status
- raw response SHA
- target row date
- target O/H/L/C
- previous dated row O/H/L/C where available
- raw/adjusted basis
- quote current price
- quote previous O/H/L
- `base_close_pric`

Do not stop after 08:05 even if 22/22 is present.

## 9. Re-observation acceptance

Preferred complete status requires:

- four windows actually reached;
- each window full22 adjusted availability 22/22;
- strict validity 22/22 at each window;
- diagnostic subset raw + quote complete at each window;
- Successful COMPLETE status requires 112/112 planned data responses.
- Any provider/request failure that reduces this count requires `PARTIAL` or
  `TECHNICAL_COLLECTION_FAILURE`, even when the failure is fully preserved and explained;
- no request begins before its owned slot;
- no request is backfilled from a different minute;
- close O/H/L transition matrices generated for 08:05→08:10→08:15→08:20;
- quote relation recorded at each window;
- final Kiwoom owner decision still `null`;
- no R5B/later request in the same cutoff execution; a separately launched
  R5B-PARTIAL read-only task is allowed only after the frozen R5 later-window condition is
  satisfied.

If incomplete, classify truthfully as PARTIAL or TECHNICAL failure. Do not relax the
contract to obtain COMPLETE.

## 10. R5B-PARTIAL delayed historical comparison from the frozen 08:05 evidence

A separate **R5B-PARTIAL** read-only task is allowed before R5A-R1 four-window completion
once the existing frozen R5 later-window condition is satisfied.

### 10.1 Frozen inputs

Use the existing `later-comparison-handoff.json` and its frozen 2026-09-23 target values
from the valid R6-R5A 08:05 observation.

Do not recollect, regenerate, replace, normalize, or silently update those cutoff values.

The comparison must be for the **same target session/date** and must preserve the frozen
cutoff identity per symbol.

### 10.2 Comparison requirements

For each of the full22 symbols compare:

- frozen 08:05 cutoff `usa06012` target close;
- later historical `usa06012` close for the same target date;
- exact close equality;
- O/H/L equality where the frozen handoff contains the corresponding fields.

Also preserve, but do not reinterpret away, the already observed diagnostic-subset
negative evidence:

- SPY / SOXX / XLC `usa20100.base_close_pric` at actual 08:05 matched the 2026-09-22
  previous-session tuple rather than the target 2026-09-23 tuple.

### 10.3 Asymmetric decision rule

The R5B-PARTIAL result is intentionally asymmetric.

**Negative/disqualifying path**

If **any one** of the 22 symbols has:

`frozen 08:05 usa06012 target close != later historical same-date close`

then that mismatch may be used as negative/disqualifying evidence against
`usa06012` latest-row settled-close ownership at the cutoff.

Report the exact affected symbols and frozen/later values. Do not hide a mismatch inside
an aggregate pass rate.

**Non-promoting equality path**

If all 22 symbols are exact close matches, this is qualification evidence only.

Even with 22/22 equality, do **not** declare:

`KIWOOM_REGULAR_CLOSE_OWNER_PASS`

because both of the following unresolved evidence classes remain:

1. R4 historical evidence: 19/22 close drift;
2. R6-R5A missing intra-window evidence: 08:10 / 08:15 / 08:20 were not collected.

Therefore, 22/22 equality in R5B-PARTIAL does not close the source gate and does not cancel
the repaired next-day R5A-R1 four-window observation.

### 10.4 Qualification-only isolation

R5B-PARTIAL must be a separately executed, read-only qualification task.

Must remain zero:

- model calls;
- Market/Core/A/B;
- rendered messages;
- Telegram sends;
- recipient/delivery intent;
- scheduler mutation;
- notification mutation;
- production DB decision/warning writes;
- broker actions;
- merge/push/deploy/service restart.

The later historical value must never become a production lookahead dependency.

R5B-PARTIAL must not alter:

- frozen cutoff artifacts;
- `later-comparison-handoff.json`;
- source authority;
- production prompts;
- production decision logic;
- the R5A-R1 repair plan;
- the requirement to run the repaired four-window observation.

### 10.5 Relationship to full R5B

R5B-PARTIAL is not the final R5B gate.

After R5A-R1 obtains a complete repaired 08:05 / 08:10 / 08:15 / 08:20 observation, the
normal delayed historical comparison for that newly observed target session remains
required under the existing frozen decision rules.

Do not declare:

- `KIWOOM_REGULAR_CLOSE_OWNER_PASS`
- `US_REGULAR_CLOSE_EXTERNAL_SOURCE_REQUIRED`

solely from R5B-PARTIAL.

A negative R5B-PARTIAL mismatch may disqualify the candidate earlier; a fully matching
R5B-PARTIAL result may not promote it.

## 11. Safety invariants

Must remain zero unless separately authorized:

- model calls
- Market/Core/A/B
- rendered messages
- Telegram sends
- recipient intent
- DB decision/warning writes
- scheduler mutation
- notification mutation
- broker actions
- source-provider expansion
- Alpha Vantage calls
- merge
- push
- deploy
- service restart.

Operating main must remain unchanged and clean.

## 12. Required validation

Before returning the preparation report:

- focused tests PASS
- full pytest PASS with no new unexplained skip/xfail
- Ruff PASS
- implementation diff check PASS
- Investment/Chart Knowledge check PASS
- secret scan PASS
- operating before/after equality for production DB/WAL/schedule/launchd state
- route SHA exact
- parent plan SHA exact
- derived plan SHA recorded
- request-array SHA exact and unchanged
- provider calls during preparation: 0
- model calls: 0.

Remote CI must not be represented as PASS unless actually pushed and observed.

## 13. Required artifacts

Preparation result ZIP must include at least:

- `REPORT.md`
- `summary.json`
- patched observer code
- new focused tests
- parent-plan receipt
- derived-plan JSON
- derived-plan SHA receipt
- exact request-array equality proof
- minute-boundary offline reproduction/tests
- validation logs
- operating before/after
- secret scan
- bundle manifest.

If R5B-PARTIAL is executed as a separate task, its result ZIP must include at least:

- `REPORT.md`
- `summary.json`
- the frozen `later-comparison-handoff.json` identity/receipt
- per-symbol frozen 08:05 versus later historical same-date comparison
- exact mismatch list
- O/H/L comparison where available
- explicit asymmetric-decision receipt
- proof that model/Market/Core/A/B/message/scheduler/production mutation counts are zero
- bundle manifest and secret scan.

Actual observation result, when later executed, must additionally include:

- all four per-window observation directories
- per-window receipts
- raw hashes
- cutoff receipt
- close/O/H/L mutation matrix
- quote relation matrix
- missing/failure list
- later-comparison handoff prepared but not executed.

## 14. Final interpretation

This task is a **collector timing repair**, not a source-authority promotion.

The current source truth remains:

- `usa20100.base_close_pric`: negative target-owner evidence at actual 08:05 on the
  SPY/SOXX/XLC diagnostic subset;
- `usa06012` dated daily-row close: present for target date at 08:05, but regular-session
  finality still unproven;
- R4 19/22 historical close drift remains active negative evidence;
- R5B-PARTIAL may use the valid frozen 08:05 evidence asymmetrically: any mismatch may
  disqualify, but even 22/22 equality cannot promote the owner candidate;
- no external provider is authorized;
- no fresh Market/Core/A/B run is authorized yet.
