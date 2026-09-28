# Thesis Monitor — R2B-R8
## Read-Only Blind-Comparison Verification + R7 Closeout + Final Live-Requalification Handoff

**Purpose:** finish the only open R7 bookkeeping item by verifying the exact post-seal blind-comparison artifact and appending a read-only comparison audit to the accepted R7 source-policy repair.

This task must **not** retune investment policy, rerun models, recollect sources, or modify the already accepted R7 absolute-current directional guard.

If the comparison artifact verifies and reveals no new objective source-contract violation beyond the already-fixed absolute-current issue, close R7 and generate—but do not execute—the next **final fresh live adapter requalification** work instruction required before scheduler activation.

---

# 0. Newest accepted SoT

Adopt R2B-R7 as the newest SoT.

R7 result ZIP SHA-256:

`aba5a144fb5b8bf8106684d2541352a8e72d12ed121bccbfabda036bebb62680`

Terminal:

`R2B_R7_ABSOLUTE_CURRENT_DIRECTION_GUARD_PASS`

Repository:

- branch:
  `codex/r2b-r7-absolute-financial-direction`
- base R6:
  `ad24ba92e8a7d8494a62c5e90a8321fba9c5230d`
- instruction:
  `7140f09f05f12e5b214f4511663a858a8b29d2ed`
- initial implementation:
  `651cadc11f6189f0d9f5d13c0426e4e9a56fe32d`
- final tested implementation:
  `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- final report-only commit:
  `d824014b7f9fad44a1619850d81a657925c6cf80`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted R7 objective repair:

- invalid directional claims found:
  `3`
- affected subjects:
  - `005930`
  - `047810`
- corrected states:
  - `005930 -> OBSERVE / OBSERVE / OBSERVE`
  - `047810 -> OBSERVE / OBSERVE / OBSERVE`
- corrected decision modes:
  `19 ordinary + 3 UNKNOWN_LIMIT`
- unaffected subjects:
  `20/20`
- unchanged original messages:
  `22/22`
- corrected message corpus:
  `24/24`
- source hashes:
  unchanged
- model calls:
  `0`
- provider calls:
  `0`
- production side effects:
  `0`

Validation:

- focused:
  `717 PASS`
- full:
  `6222 PASS / 63 unchanged skips`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS

Do not reopen this repair unless the verified comparison artifact proves another **objective source-contract violation**.

---

# 1. Missing artifact to verify

Required comparison ZIP:

`thesis-monitor-20260928-INDEPENDENT_V2_vs_MONITORING_AI_R6_COMPARISON.zip`

Expected SHA-256:

`8002957138129ec4d31bb9880c5d038de0114a60206a5248c293efa45334504f`

This artifact was created after:

- independent V2 was frozen;
- Monitoring-AI R6 result was sealed.

It is therefore post-seal review evidence.

R7 did not have access to the ZIP and correctly reported:

`post_seal_comparison_archive_verified = false`

R8 must verify it now.

---

# 2. Comparison artifact integrity

Before reading content:

1. verify outer ZIP SHA exactly;
2. verify ZIP CRC;
3. enumerate members;
4. verify internal file consistency where self-hashes/manifest exist;
5. record filenames and SHA values.

Expected contents include:

- comparison JSON
- comparison Markdown
- comparison CSV

Do not alter or regenerate the comparison artifact in R8.

If outer SHA mismatches:
- stop;
- no closeout.

Terminal:
`R2B_R8_COMPARISON_ARCHIVE_IDENTITY_MISMATCH`

---

# 3. Read-only comparison scope

The comparison may be used only for descriptive review.

Do not use it to:

- fit ticker outputs;
- change score thresholds;
- change archetype policy;
- change New Buyer or Holder policy;
- relax valuation/security-basis requirements;
- create per-ticker exceptions;
- alter source-quality rules merely to match the independent reviewer.

Only a **generic objective contract violation** may justify a new repair task.

R7 already fixed the known objective violation:
absolute-current financial amounts used directionally.

---

# 4. Reconcile comparison findings with R7 audits

Create:

`r7-comparison-reconciliation.json`

At minimum map the verified comparison findings to R7's existing audits:

## Objective source-policy findings

Expected:
- 005930 absolute-current directional leakage
- 047810 absolute-current directional leakage

Require:
- both are covered by `absolute-financial-direction-eligibility-v1`
- corrected messages are `UNKNOWN_LIMIT / OBSERVE`
- no remaining absolute-only directional claim exists in the 22-subject corrected corpus.

## Calibration-only findings

Expected comparison topics include:
- CPNG
- HUT
- WULF
- 000660
- GOOGL / MU / TSM / SKHY
- New Buyer conservatism
- Holder action compression
- directional-score compression

Reconcile them against:

- `execution-growth-downside-calibration-audit.json`
- `new-buyer-actionability-audit.json`
- `holder-actionability-audit.json`
- `directional-score-compression-audit.json`
- `large-cap-descriptive-policy-matrix.json`

Classification for each finding:

- `OBJECTIVE_CONTRACT_FIXED`
- `DESCRIPTIVE_POLICY_DIFFERENCE`
- `SOURCE_QUALITY_LIMITATION`
- `VALUATION_COVERAGE_LIMITATION`
- `REQUIRES_SEPARATE_PRODUCT_POLICY_DECISION`
- `NEW_OBJECTIVE_CONTRACT_VIOLATION`

Do not convert descriptive differences into bugs.

---

# 5. Specific calibration reconciliation

## CPNG / HUT / WULF

R7 already observed that downside is stronger in New Buyer/Holder than Overall.

Verify the comparison agrees descriptively.

Do not retune.

Record whether the issue is:
- permitted current policy behavior;
- ambiguous `INSUFFICIENT_DIRECTIONAL_EVIDENCE` semantics;
- separate future product-policy question.

## 000660

Distinguish:
- financial-quality/source limitation
from
- investment-policy conservatism.

Do not fix source-quality denial with policy changes.

## GOOGL / MU / TSM / SKHY

Verify the comparison difference is primarily:
- positive Overall
- New Buyer WAIT due unresolved valuation/security basis

Classify as coverage/policy behavior, not objective error unless a separate contract violation exists.

## Holder

Verify no ADD/REDUCE is currently available under the existing evidence vocabulary/contract.

Do not add actions in R8.

---

# 6. Corrected 24-message corpus verification

Verify R7's corrected corpus:

- 24/24 messages
- 20 stock messages unchanged from R6
- 2 market messages unchanged from R6
- 005930 corrected deterministically
- 047810 corrected deterministically
- SNDK UNKNOWN_LIMIT unchanged

Produce:

`corrected-corpus-verification.json`

Require:

- no model calls
- no source refresh
- source packet hashes unchanged
- corrected messages trace to the R7 guard
- no unrelated text/value changes.

---

# 7. R7 closeout condition

R7 is fully closed if:

1. comparison ZIP identity verified;
2. all comparison findings reconciled;
3. no new objective source-contract violation remains;
4. 005930/047810 correction verified;
5. corrected 24-message corpus verified;
6. no policy retuning occurred;
7. all original R7 validation remains PASS.

Closeout terminal:

`R2B_R8_R7_COMPARISON_RECONCILIATION_PASS`

If a new objective contract violation is found:

`R2B_R8_NEW_OBJECTIVE_CONTRACT_GAP`

Return exact generic contract issue.

Do not repair it inside R8.

---

# 8. Production readiness is still not authorized

Even after R7 closeout:

- do not activate scheduler;
- do not send Telegram;
- do not merge main;
- do not deploy.

Reason:

R7 changed source-use / directional eligibility code **after** the live cohort that originally qualified the adapter.

A fresh live adapter requalification is still required under the standing qualification semantics.

---

# 9. Generate next work instruction on R7 closeout PASS

Generate—but do not execute—a new instruction:

## Final Fresh Live Adapter Requalification After Direction Guard

The next instruction must require:

### A. Fresh real source cohort

Use the accepted current product collection contract:

#### US
- 08:10 initial
- incomplete -> 08:15 full Class-A recollect
- incomplete -> 08:20 full Class-A recollect

#### KR
- 16:00 initial
- incomplete -> 16:05 full Class-A recollect
- incomplete -> 16:10 full Class-A recollect

or explicitly approved ad-hoc live proof mode if outside scheduled window.

No cross-attempt patching.

### B. Current source graph

Prove with current code including R7:

- 22 stock packets
- US market packet
- KR market packet
- KRX night/publication context
- Class-B once per run
- Class-C version set
- full run seed
- whole-source packet
- authority graph
- absolute-current direction guard

### C. Guard regression in fresh cohort

Require:
- current-only absolute financial amount never owns direction
- compatible comparative financial observations remain direction-eligible
- UNKNOWN_LIMIT works when directional entitlement = 0
- no source authority widening.

### D. Adapter qualification

Set:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`

only from the fresh live cohort replay.

### E. No AI judgment retuning

This live requalification is primarily a source/adapter contract proof.

If model execution is included:
- use existing accepted policy unchanged;
- no comparison-label fitting;
- no provider refresh outside the frozen plan.

### F. Production side effects remain zero

- Telegram 0
- recipient intent 0
- production DB decision/warning writes 0
- scheduler mutation 0
- broker 0
- deploy 0
- merge/push 0

### G. After live requalification PASS

Generate the separate final scheduler-cutover instruction:

- retire paused legacy primary/backup paths;
- activate one US 08:10 entry;
- activate one KR 16:00 entry;
- verify duplicate-path count = 0;
- preserve KR holiday / US closed-session deterministic skip;
- no automatic replay after ambiguous delivery.

Do not execute scheduler cutover in the live-requalification task.

---

# 10. Alpha / provider budget

The generated live-requalification instruction must preserve:

- Alpha Vantage planned = 0
- Alpha Vantage actual = 0
- account-wide Alpha budget remains 25/day
- Massive/mock/undeclared fallback = 0

All provider plans must be frozen before calls.

---

# 11. R8 network/model policy

R8 itself is entirely read-only/offline.

Required:

- provider calls = 0
- model calls = 0
- Telegram = 0
- production DB writes = 0
- scheduler mutations = 0
- deploy = 0
- merge/push = 0

Only local artifact reads are allowed.

---

# 12. Required artifacts

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R7 identity/SHA receipt
- comparison ZIP identity/SHA receipt
- repository identities
- no-code-change receipt

## Comparison reconciliation
- member inventory
- comparison integrity receipt
- `r7-comparison-reconciliation.json`
- objective-vs-calibration classification matrix
- CPNG/HUT/WULF reconciliation
- 000660 source-quality reconciliation
- large-cap/New Buyer reconciliation
- Holder actionability reconciliation
- score compression reconciliation

## Corrected corpus
- corrected corpus verification
- 005930 before/after
- 047810 before/after
- 22 unaffected-message invariance
- source-hash invariance

## Closeout
- R7 final closeout terminal
- remaining open product-policy questions
- production-readiness state

## Next instruction
On PASS:
- final live-requalification work-instruction MD
- ZIP
- SHA sidecar
- explicit:
  `live requalification executed = false`
  `scheduler cutover executed = false`

## Safety
- provider/model counters = 0
- production side effects = 0
- secret scan
- bundle manifest

---

# 13. Final principle

The independent comparison is now review evidence, not a training target.

Use it to confirm the objective source-policy bug was fixed and to document remaining policy/coverage differences without retuning.

Then move to a fresh live adapter requalification, because production activation must be based on the current post-R7 code, not on an earlier live cohort.
