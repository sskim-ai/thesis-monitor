# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV5
## TSM/WRD Offline Financial-Semantic Closure + SKHY One Final Generic Coverage Window

**Purpose:** resolve the final three blocked subjects from REV4 without reopening the now-proven bounded SEC/OpenDART architecture. TSM and WRD must be resolved from already-captured source bytes only. SKHY alone may use one additional **generic second candidate window** derived from the already-captured SEC submissions metadata, with a frozen two-phase budget. No new SEC submissions/discovery request is allowed.

If this task reaches 22/22 complete stock source/business packets, rebuild network-free prequalification and generate the bounded R2B 24-message instruction. Do not execute R2B here.

---

# 0. Newest accepted SoT

Adopt REV4 as the newest SoT.

REV4 result ZIP SHA-256:

`034cde40aa18ad365782425ec89255e89c3e9df23987283a6bb5e6f871eeab02`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV4_FPI_PHASE2_PARTIAL`

Bundle integrity independently verified:

- ZIP/sidecar exact;
- internal manifest `130/130`;
- missing/hash/size/extra mismatch `0`.

Repository identities:

- base:
  `aacfe8a5f2cfe6f94e4bd99b01acc4ce4654512b`
- instruction:
  `d4ff5071c683d251c5c6c27d9988c6e157ba0d9e`
- implementation/final/acquisition:
  `9aa2ec1d47bd31dbe0111bf5b85edfa2e030efd0`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted state:

- complete stock source/business packets: `19/22`
- blocked:
  - `SKHY`
  - `TSM`
  - `WRD`
- all 19 REV3 controls invariant;
- phase-2 planned logical requests: `4`;
- actual logical/HTTP requests: `4/4`;
- retries: `0`;
- SKHY requests: `0`;
- no new discovery/submissions/OpenDART/OHLCV calls;
- model/Market/Core/A/B/render/send/scheduler/DB/deploy: `0`.

Validation:

- focused `854 PASS`;
- full `5842 PASS / 63 unchanged skips / 0 failures`;
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke: PASS.

Do not overwrite REV4.

---

# 1. Exact residual states

## TSM

Captured financial statement:

- accession `0001046179-26-000541`
- filing date `2026-08-14`
- report date `2026-06-30`
- exact exhibit:
  `a2026q2consolidatedreport-.htm`
- purpose:
  `FINANCIAL_STATEMENTS`
- document class:
  auditor-reviewed interim financial statement
- exact economic periods captured:
  - Q2 2026: `2026-04-01..2026-06-30`
  - Q2 2025: `2025-04-01..2025-06-30`
  - H1 2026: `2026-01-01..2026-06-30`
  - H1 2025: `2025-01-01..2025-06-30`
- revenue and operating-income occurrences are already parsed with exact TWD/unit/source-cell lineage.

Remaining denials:

- `NEWER_FPI_PURPOSE_OR_PERIOD_UNRESOLVED`
- `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`
- `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION`
- net-income `PERIOD_NOT_COMPARABLE`
- historical acquisition denials remain recorded.

Later already-captured primary documents include:

- 2026-09-24 6-K
- 2026-08-25 6-K

Both currently `UNKNOWN_PURPOSE`.

REV5 must make **zero new TSM network calls**.

## WRD

Captured phase-2 financial sources:

### 2026-09-14 / report date 2026-06-30
- exact exhibit:
  `wrd-20260914xex99d1.htm`
- contains reviewed condensed consolidated interim financial statements;
- source text explicitly states:
  - six months ended June 30, 2026;
  - IAS 34 interim financial reporting;
  - consolidated statements of profit or loss.

### 2026-08-12 exhibit
- exact exhibit:
  `tm2622690d1_ex99-1.htm`
- contains:
  `UNAUDITED CONDENSED CONSOLIDATED STATEMENT OF PROFIT OR LOSS`
- unit text:
  `Expressed in thousands of Renminbi ("RMB"), except for per share data`
- six months ended June 30 columns.

Current parser result:
- revenue labels recognized;
- statement boundary owner rejects caption/unit ownership;
- no canonical occurrence admitted.

REV5 must make **zero new WRD network calls**.

## SKHY

Current state:

- phase-1 frozen candidate window size: `8`
- no selector-eligible phase-2 exhibit within that window;
- phase-2 network calls: `0`
- current denials:
  - `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_BOUND`
  - `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`
  - `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION`
  - `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE1_AND_NO_PHASE2_ELIGIBLE_EXHIBIT`

The already-captured SEC submissions metadata contains more candidates beyond the first 8.

REV5 may inspect **exactly one more non-overlapping generic window of the same size**, derived from that sealed metadata.

No new SEC submissions/discovery request.

---

# 2. Fix A — field-specific financial supersession for TSM

The current global newer-document gate is too coarse.

A newer 6-K must not invalidate an already-qualified complete financial statement merely because its filing date is later.

Implement a generic **field-specific/economic-period supersession** rule.

A newer document supersedes a selected financial field only if it affirmatively proves:

1. same issuer/security;
2. financial authority for that canonical field or a broader statement set containing that field;
3. economic period later than the currently selected period under the same comparison family;
4. compatible statement/accounting basis;
5. compatible currency/unit;
6. exact source occurrence;
7. existing source-use/quality passes.

A later filing that is:

- nonfinancial;
- dividend/capital return;
- monthly revenue only;
- compensation/governance;
- corporate event;
- rumor response

must not globally invalidate unrelated quarterly financial statement fields.

---

# 3. TSM newer-document classification — offline only

Use already captured REV3/REV4 raw primary bytes for the 2026-08-25 and 2026-09-24 6-Ks.

No network.

Classify each generically into the existing purpose states.

Required output:

- exact accession;
- raw SHA;
- source content evidence;
- purpose;
- any economic period;
- any canonical financial fields actually owned;
- field-specific supersession impact.

If a newer document remains `UNKNOWN_PURPOSE` after the improved generic classifier:

- do not invent purpose;
- record `NEWER_DOCUMENT_PURPOSE_UNRESOLVED`.

For a field that could plausibly be superseded by an unresolved source, preserve fail-closed behavior for that field.

Do not weaken the gate merely to force TSM PASS.

---

# 4. TSM selected-current rule

For every canonical field independently:

- choose the latest **qualified economic observation**, not the latest filing date;
- current/prior comparison must be period-compatible;
- Q2 compares to Q2;
- H1 compares to H1;
- monthly revenue does not automatically supersede quarterly operating income/net income;
- annual does not substitute for missing interim current evidence.

Use already captured Q2/H1 occurrences when they remain the latest qualified comparable observations for that field.

No `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION` should remain solely because a later **nonfinancial** filing exists.

---

# 5. TSM net-income period audit

The current revenue/operating-income occurrences are well formed, but net income retains `PERIOD_NOT_COMPARABLE`.

Audit the captured TSM exhibit only.

Required:

- locate exact net-income/profit occurrence(s);
- period headers;
- current/prior role;
- Q2 vs H1 role;
- statement basis;
- unit/currency;
- source cell identity.

If a compatible pair exists:
- use existing generic pairing rules.

If no compatible pair exists:
- net income remains unavailable;
- unrelated revenue/operating-income evidence may still survive field-level eligibility.

Do not require all three fields to pass unless the existing stock business contract genuinely requires the tuple.

---

# 6. Fix B — generic WRD statement boundary semantics

Do not add WRD/ticker-specific branches.

Extend the generic foreign statement boundary owner to recognize exact structural variants common to IFRS/HK interim financial statements.

Supported generic caption family may include source-owned forms equivalent to:

- `CONDENSED CONSOLIDATED STATEMENT OF PROFIT OR LOSS`
- `UNAUDITED CONDENSED CONSOLIDATED STATEMENT OF PROFIT OR LOSS`
- `CONDENSED CONSOLIDATED STATEMENTS OF PROFIT OR LOSS`
- `CONDENSED CONSOLIDATED STATEMENTS OF PROFIT OR LOSS AND OTHER COMPREHENSIVE INCOME`

Recognition must be structural, not broad document keyword search.

Caption ownership must be bound to the relevant table/section by DOM/structural locality.

---

# 7. Generic WRD currency/unit semantics

Extend the generic unit owner to parse source-owned variants equivalent to:

- `Expressed in thousands of Renminbi ("RMB"), except for per share data`
- `In thousands of Renminbi`
- `RMB in thousands`
- existing equivalent structural forms.

Requirements:

- currency = `CNY/RMB` under the existing canonical currency owner;
- unit scale = `1000`;
- unit statement must structurally own the financial table/section;
- no ticker-specific phrase;
- no number guessing;
- no whole-document nearest-text heuristic without bounded structural relation.

Negative controls:

- per-share unit text must not set statement scale;
- HKD/USD text in an unrelated note must not own the table;
- a unit phrase in a different statement section must not leak.

---

# 8. WRD period semantics

The captured interim statement is explicitly **six months ended June 30**.

It must be represented as:

`HALF_YEAR / CUMULATIVE_INTERIM`

or the exact existing equivalent.

Do not infer a standalone quarter from a six-month-only statement.

Current/prior:

- H1 2026
- H1 2025

may compare when all other lineage/basis rules pass.

If a separate three-month statement is not present:
- quarterly evidence remains unavailable;
- half-year evidence may still be valid.

---

# 9. WRD field extraction

From the captured financial tables, bind only exact source rows recognized by the existing canonical owner.

At minimum audit:

- revenue;
- operating profit/income equivalent if exact existing canonical mapping exists;
- net income/profit/loss equivalent if exact existing canonical mapping exists.

Do not create new broad semantic aliases merely because a row sounds similar.

For each admitted field preserve:

- caption boundary;
- unit/currency boundary;
- source row;
- period;
- current/prior occurrence;
- basis;
- source SHA;
- owner version;
- quality/source-use result.

---

# 10. WRD source priority

The 2026-09-14 reviewed interim financial statement has report date `2026-06-30`.

The 2026-08-12 source may also contain the same six-month reporting period.

Do not pick based on filename or filing date alone.

Use generic source-quality/authority rules, such as:

- audited/reviewed statement evidence class;
- same economic period;
- exact statement boundary;
- source-use quality.

If two sources own the same economic period:
- deterministic existing source-precedence rule must select or reconcile them;
- no value-based choice.

The July listing-rule waiver remains nonfinancial.

---

# 11. SKHY — one final generic second candidate window

Implement a generic bounded coverage-window owner for FPI cases satisfying all of:

- current first candidate window exhausted;
- no financial-purpose source found;
- no phase-2 eligible exhibit;
- sealed submissions metadata already contains additional eligible-form candidates.

This is not a SKHY-specific code path.

At runtime REV5 applies only to SKHY because it is the only current subject satisfying the condition.

---

# 12. SKHY window contract

Existing generic candidate window size:

`8`

REV5 allows exactly:

`SEC_FPI_MAX_COVERAGE_WINDOWS = 2`

Thus:

- Window 1 = already completed first 8 candidates;
- Window 2 = next non-overlapping up to 8 candidates from the **same sealed submissions metadata**.

No third window.

No new submissions request.

No date-range widening beyond what is already present in the sealed candidate inventory.

After Window 2:
- source found -> proceed generically;
- source not found -> final honest coverage block.

---

# 13. Expected SKHY Window-2 candidate derivation

Do not hardcode these accessions in production code.

The plan generator must derive them from the sealed ordered submissions candidate inventory after excluding Window 1.

The already-sealed inventory indicates the next candidate region begins after the first eight entries, including filings around:

- 2026-08-18
- 2026-08-14
- 2026-08-10
- 2026-08-07
- 2026-08-06

The exact up-to-8 accessions/URLs must be generated from the sealed artifact and frozen into the new request plan before network access.

If the artifact-derived next-window list differs:
- use the artifact;
- explain the difference;
- do not manually force a candidate.

---

# 14. SKHY Window-2 phase-1 budget

For up to 8 candidates, freeze before network:

For each selected candidate:
- one filing index request;
- one primary document request.

Maximum logical phase-1 requests:

`8 * 2 = 16`

Timeout:
`600s`

Retries:
- transient max 2;
- max attempts 3;
- byte-identical only.

Maximum phase-1 transport attempts:

`16 * 3 = 48`

No request starts unless the exact plan count/hash and theoretical max are frozen.

---

# 15. SKHY Window-2 phase-2 exhibit contract

If the frozen Window-2 phase-1 results discover selector-eligible text/HTML/XML financial exhibits:

- seal phase-1 result;
- generate a separate immutable phase-2 exhibit plan;
- generic cap:
  reuse accepted `SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT = 3`;
- no recursive phase 3.

Maximum logical phase-2 requests:

`3`

Maximum attempts:

`9`

Overall theoretical REV5 SKHY maximum:

- logical requests: `19`
- transport attempts: `57`

Actual may be lower.

No image/OCR source expansion.

---

# 16. SKHY final coverage terminal

If Window 2 + bounded phase 2 still finds no qualified financial-purpose source:

record:

`NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_TWO_BOUNDED_WINDOWS`

and:

`FPI_FINANCIAL_PURPOSE_COVERAGE_EXHAUSTED_FINAL`

Do not automatically add Window 3.

This is an honest source-coverage outcome.

---

# 17. Non-fail-fast network behavior

SKHY network acquisition, if executed, must continue independent planned requests after ordinary per-document failure.

Immediate stop only for systemic:

- issuer/security identity drift;
- plan hash mismatch;
- code/config drift;
- secret integrity failure;
- unexpected provider;
- budget enforcement failure.

Do not stop after one nonfinancial candidate.

Do not retry semantic/quality/purpose/period failures.

---

# 18. 19 current complete subjects are invariance controls

All existing complete packets must remain semantically invariant:

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
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

At minimum prove:

- packet status unchanged;
- existing evidence authority not replaced unexpectedly;
- CPNG anomaly state unchanged;
- SNDK event authority unchanged;
- 003690 insurance-revenue semantic unchanged;
- 000660 denials unchanged;
- 005930/047810 authority unchanged.

A direct serialization change caused by shared helper repair may alter hash only if semantic equivalence is proven field-by-field. Otherwise any control regression blocks PASS.

---

# 19. Re-run all 22 complete stock packets

After offline TSM/WRD fixes and any SKHY bounded acquisition:

produce a full 22-subject matrix.

For TSM report:

- newer-document purpose classifications;
- per-field supersession state;
- selected current/prior financial periods;
- revenue/op-income/net-income status;
- direction eligibility;
- final packet.

For WRD report:

- statement caption owner;
- currency/unit owner;
- period owner;
- admitted canonical fields;
- current/prior comparison;
- direction eligibility;
- final packet.

For SKHY report:

- Window-2 exact candidate plan;
- actual requests/retries;
- any phase-2 plan;
- selected/rejected financial sources;
- final packet or final coverage blocker.

---

# 20. Completion outcomes

## Outcome A — 22/22 complete

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV5_RESIDUAL_THREE_SUBJECT_PASS`

Require:

- TSM semantic closure PASS;
- WRD semantic closure PASS;
- SKHY source closure PASS;
- 19 controls invariant;
- full validation PASS;
- production side effects 0.

Then rebuild network-free full source prequalification.

If it passes:
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- generate R2B current-source + 24-message work instruction;
- do not execute R2B here.

## Outcome B — TSM/WRD close, SKHY final honest block

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV5_SKHY_FINAL_COVERAGE_BLOCK`

Require:
- TSM PASS;
- WRD PASS;
- SKHY two-window bounded search exhausted;
- exact final SKHY source blocker;
- 21/22 complete.

Do not expand automatically.

Return the product/source decision needed before any 24-message proof.

## Outcome C — residual semantic partial

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV5_RESIDUAL_SEMANTIC_PARTIAL`

Return exact TSM/WRD/SKHY blocker(s).

No automatic broadening.

## Outcome D — boundedness/systemic stop

Use a narrowly named boundedness/systemic terminal.

Preserve all completed offline work.

---

# 21. R2B remains blocked unless 22/22

Do not run:

- current full cohort;
- Market/Core/A/B;
- renderer;
- 24 messages;
- Telegram;
- scheduler cutover

inside REV5.

Generate R2B only on 22/22 + network-free prequalification PASS.

If 21/22 because SKHY is final source-blocked:
- do not silently drop SKHY;
- do not generate a misleading 24-message instruction.

---

# 22. Safety / provider budgets

Required zero:

- TSM network calls;
- WRD network calls;
- OpenDART;
- OHLCV;
- Alpha Vantage;
- Massive;
- model;
- Market/Core/A/B;
- renderer;
- Telegram;
- recipient intent;
- production DB decision/warning writes;
- scheduler mutations;
- broker;
- deploy;
- main merge/push/restart.

Allowed network:
- only frozen SKHY Window-2 SEC plan and optional derived Phase-2 exhibit plan.

Record:

- planned logical;
- theoretical max logical;
- actual logical;
- retries;
- phase1 requests;
- phase2 requests;
- cap exhaustion.

---

# 23. Validation

Required:

## TSM
- newer-document purpose fixtures;
- field-specific supersession;
- nonfinancial later filing does not globally invalidate older qualified statements;
- revenue-only later evidence affects only owned field;
- period comparison;
- net-income compatibility;
- no network proof.

## WRD
- generic IFRS/HK statement caption variants;
- RMB/renminbi thousands unit variants;
- structural table ownership;
- six-month period;
- no fake quarter;
- unrelated unit/caption negatives;
- no ticker branches;
- no network proof.

## SKHY
- two-window generic selector tests;
- non-overlap;
- max 2 windows;
- exact next-window plan from sealed metadata;
- phase1/phase2 caps;
- final-exhaustion terminal;
- no third-window route.

## Cohort
- 19-control invariance;
- full 22 stock replay;
- previous REV2/REV3/REV4 regressions;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- disabled entrypoint smoke;
- secret scan;
- no new unexplained skip/xfail.

No threshold relaxation.

---

# 24. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- REV4 identity/SHA receipt
- repository identities
- changed-file inventory

## TSM
- later-document purpose matrix
- field-specific supersession matrix
- selected period/field lineage
- packet result

## WRD
- statement-boundary before/after
- caption/unit structural receipts
- period/field lineage
- packet result

## SKHY
- sealed submissions inventory identity
- Window-1 receipt
- Window-2 plan + SHA
- exact candidate list
- phase1 budget/actual
- any phase2 exhibit plan + SHA
- phase2 budget/actual
- source receipts
- final coverage decision
- packet result

## Cohort
- 19-control invariance
- 22 packet matrix/hashes
- exact residual blockers
- network-free prequalification if reached
- R2B next instruction + SHA only if 22/22 allows it

## Safety
- execution counters
- config/env/scheduler before-after
- validation logs
- secret scan
- bundle manifest.

---

# 25. Final principle

TSM and WRD already have the necessary source bytes; fix source meaning, not coverage.

SKHY alone may consume one final generic bounded coverage window from already-sealed submissions metadata.

After that window, absence of qualified financial evidence is a legitimate terminal source state, not permission for open-ended crawling.
