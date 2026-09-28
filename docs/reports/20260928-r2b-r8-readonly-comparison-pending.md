# R2B-R8 Read-Only Verification: Comparison Archive Missing

## Status

`R2B_R8_COMPARISON_ARCHIVE_MISSING`

R7's objective repair and corrected corpus independently reverify. R8 cannot
close the remaining comparison item because the required comparison ZIP is not
available. This is a missing input, not an archive hash mismatch and not a new
observed contract violation. The absence of the comparison prevents asserting
that it contains no additional objective violation.

## Missing Input

Required file:
`thesis-monitor-20260928-INDEPENDENT_V2_vs_MONITORING_AI_R6_COMPARISON.zip`

Expected SHA-256:
`8002957138129ec4d31bb9880c5d038de0114a60206a5248c293efa45334504f`

The uploaded R8 ZIP contains only its Markdown instruction. Filename searches
covered iCloud Drive, Downloads, Documents, Desktop and this task's attachment
directory. The exact file is absent from both approved iCloud delivery locations.
No comparison archive was substituted, regenerated, or read before verification.
Its outer SHA, CRC, member inventory, and JSON/Markdown/CSV consistency are pending.

## Completed Verification

- Accepted R7 ZIP SHA verified before reading; ZIP CRC and all 172 manifest
  entries pass. R6 ZIP identity, CRC, and all 815 manifest entries also pass.
- All 22 subjects' directional entitlement recomputed offline using unchanged
  R7 code and the same sealed inputs.
- Exactly 3 invalid original directional claims are excluded, in 005930 and
  047810. Their deterministic all-axis OBSERVE states validate with null scores
  and confidence; no retained absolute-only directional claim remains.
- Corrected corpus: 24/24 messages. Twenty stock messages and two market
  messages are byte-identical to R6; SNDK UNKNOWN_LIMIT is unchanged.
- Two corrected messages reproduce from the existing deterministic limitation
  renderer and match their R7 capture receipts exactly.
- Prepared input, quality supplement, Market/Core/A/B original freezes and source
  hashes remain unchanged. R6/R7 archives were never rewritten.
- Original R7 validation remains PASS: focused 717, full 6,222, unchanged skips
  63. Executable code is byte-identical; no full-suite rerun was necessary for
  this document-only append.

## Comparison and Handoff

R7's existing CPNG/HUT/WULF, New Buyer, Holder, score-range, large-cap and source
quality audits are preserved as R7 evidence, not represented as newly verified
comparison findings. Their reconciliation classifications remain pending the
required archive. No policy retuning or target fitting occurred.

R7 objective guard status: PASS, unchanged.
R7 complete comparison closeout: NOT ISSUED.
New objective violation determination from comparison: NOT ASSESSED.
Live requalification instruction: NOT GENERATED; closeout prerequisite unmet.
Live requalification executed: false.
Scheduler cutover executed: false.
Production/scheduler readiness: NOT AUTHORIZED.

Bounded resume: supply the exact missing ZIP. Verify its outer SHA before reading,
then CRC/member consistency, append descriptive reconciliation, and generate the
next work instruction only if all R8 closeout conditions pass. No repeated
source/model calls or R7 guard modification is needed to resume this audit.

## Repository and Safety

- Branch: `codex/r2b-r8-readonly-comparison`.
- Base: `d824014b7f9fad44a1619850d81a657925c6cf80` (R7 final report commit).
- Instruction-first and final report-only commit identities are bundled.
- Runtime implementation changes: 0. Offline verification helper lives only in
  the local report artifacts, not in the product runtime.
- Operating HEAD remains `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`, clean.
- Operating configuration, DB file hashes and scheduler state unchanged during
  the R8 verification window; no broader historical-window claim is made.
- Provider, Alpha Vantage, model, Telegram, recipient intent, production writes,
  scheduler mutation, broker, deployment, main merge, push and restart: 0.
- Offline network guard recorded 0 attempts.

Delivery: a secret-scanned pending-report ZIP plus SHA sidecar, with destination
readback hashes and iCloud per-file upload flags recorded separately.
