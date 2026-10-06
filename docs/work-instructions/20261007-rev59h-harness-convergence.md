# Thesis Monitor - REV59H Harness Convergence

User instruction received 2026-10-07 KST. Commit this instruction before
implementation. No main merge, remote push, deployment, or production changes
are authorized by this task.

## 0. Goal

Two bounded repairs, then one new full-fresh final strict blind.

Repair A: cross-platform anonymous stdin pipe identity.
Repair B: optional KOSPI200 night-futures typed-unavailable ownership.

Do not add a new controller layer. After blind seal, invoke the already-proven
production-equivalent Market -> Core -> A -> B/Overall/Holder -> B2 path.

Success:
`R2B_R9_REV59H_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`

## 1. Predecessor

Use REV59G final HEAD: `344425023927e8ac7e047a28ecbce868c2bfbcb5`.
Expected terminal: `R2B_R9_REV59G_OWNER_COVERAGE_GAP`.
Preserve all REV59G raw/source evidence and stopped run. Do not resume its generation.

## 2. Validation policy

Hosted full CI is NOT required before this new strict run.
Mandatory: focused tests; exact live-composition tests; real Linux targeted IPC
test; local full pytest; Ruff; diff check; secret scan; frozen architecture drift checks.

If Repair B requires changing source authority/economic meaning rather than
restoring typed-unavailable semantics, STOP:
`R2B_R9_REV59H_SOURCE_ARCHITECTURE_CHANGE_REQUIRED`.

Final strict-blind PASS is followed by a separate Architecture Acceptance task
where exact-SHA Hosted full CI is mandatory.

## 3. Linux IPC repair

Darwin keeps the already-qualified kernel pipe identity.
Linux must use actual positive kernel/procfs identity. A descriptor whose
`/proc/self/fd/<fd>` resolves coherently to `pipe:[inode]` may be admitted as
anonymous IPC. Do NOT require `st_nlink == 0` on Linux.
Unknown, stale or mismatched FD remains DENY.

Explicitly reject as anonymous IPC: named FIFO, deleted named FIFO, regular
file, directory, socket, protected-root FD, reused FD mismatch, unresolved FD.
Existing filesystem-target policy for regular files/directories is unchanged.

Run actual Linux tests for `subprocess.run(input=prompt_bytes)`, anonymous pipe
write-open, reuse mismatch, named/deleted FIFO, regular/protected file,
truncate/chmod/chown, stale FD, and procfs/fstat mismatch.
Use a real Linux environment such as Docker/Linux. No full Hosted CI required.

## 4. Night-futures ownership repair

Preserve all raw rows. Separate `producer_observation_count` from
`current_consumer_eligible_count`.
Current optional context must resolve to the existing equivalent of:
`AVAILABLE_FINAL`, `UNAVAILABLE_BEFORE_FINALITY`,
`UNAVAILABLE_NO_CURRENT_FINAL_ROW`, `INVALID_CONTRADICTORY_OWNERSHIP`.

- 1 current eligible: available.
- 0 current eligible plus complete request/temporal/finality provenance:
  resolved typed unavailable.
- More than 1 conflicting current eligible: invalid/contradictory, fail closed.

Do not merely remove the cardinality assertion.

## 5. Clock contract

Use the sealed generation observation clock. Test 23:59:59 KST, 00:00:01,
00:28, 05:59:59, 06:00:00, 08:10, and weekend/holiday boundaries.
Before 06:00 date rollover may have occurred without finality. After 06:00
publication is still not guaranteed. Provider success with no current final
row is semantic unavailable, not PLAN_GAP or automatically provider outage.

## 6. Downstream behavior

Unavailable night futures must insert no stale number. Market continues with
remaining evidence; unavailable/caution may be explicit; Core/A/B/B2 continue.
Unrelated owner/metric states remain unaffected.

Optional source coverage is resolved by qualified current value OR complete
typed denial provenance. A required source slot never planned/requested remains
PLAN_GAP.

## 7. Harness simplification

The strict-blind wrapper owns only source/generation seal; source-only blind
view; blind seal; invocation of existing Monitoring pipeline; Monitoring/B2
seal; comparison. Do not reimplement Market/Core/A/B/B2 logic in the wrapper.

## 8. Exact offline composition proof

With actual guard and zero external calls execute source fixture -> typed
owner projection -> blind request/seal -> actual native Market builders ->
existing Core/A/B/B2 builders/validators -> cleanup -> AI seal -> comparison.

Fixtures: final night available; before-finality unavailable; after-finality no
current row; stale-only row; contradictory multi-owner. First four continue;
contradictory case fails.

## 9. Drift gates

Zero drift: source authority; usa20590/usa06012 roles; blind prompt/schema/
validator; B2 economics; Core/A/B/Holder economics; valuation/evaluability;
timing/fundamental separation; protected-root policy.

## 10. New strict run

Only after all local/targeted gates PASS. Genuinely new source generation,
existing 22 only. Require usa20590 14/14; usa06012 completed-close 0; Alpha
Vantage 0; source DAG drift 0; adaptive recollection 0.
Optional night futures may be unavailable if correctly typed.

## 11. Blind

Same-generation source-only package, 22 SUBJECT_SCOPED requests. No AI/v1/
historical decision labels. Raw-first. Transport/form retry only; semantic
reject has no retry. First formal semantic failure stops. Blind seal at 22/22 only.

## 12. Monitoring

Only after blind seal invoke the existing production-equivalent path:
Market -> Core -> Pass A -> production Pass B/Overall -> Holder/risk/timing -> B2.
No duplicate strict-blind implementation of this pipeline. Fresh same-generation
authority only. Blind output never enters Monitoring input. Seal B2 22/22 before reveal.

## 13. Reveal

Compare only after BLIND SEAL plus AI SEAL using presealed seven-axis authority.
Separate SOURCE_BINDING, CONTRACT_SEMANTICS, ECONOMIC_JUDGMENT.
No match-rate threshold or post-reveal mapping/policy changes.

## 14. Success

Require Mac/Linux IPC PASS; no guard weakening; typed optional night unavailable
PASS; stale never promoted; 0 eligible typed denial continues; contradiction
fails; exact production-path composition PASS; local full suite PASS; architecture
drift 0; new generation; owner coverage 22/22 with permitted typed denial; blind
22/22 sealed; Monitoring complete; B2 22/22 sealed; no source-binding hard errors;
no contract-semantic hard errors; no post-seal mutation; no production side effects.

Success terminal:
`R2B_R9_REV59H_FINAL_FRESH_STRICT_BLIND_PASS_READY_FOR_ARCHITECTURE_ACCEPTANCE`.

## 15. After success

Do NOT merge main or promote production. Next task: Architecture Acceptance
Review, requiring exact candidate SHA Hosted FULL CI. Main integration remains
separate; production promotion remains separately authorized.

## Execution and delivery continuity

Retain the predecessor's bounded signed-in official Codex sol/xhigh request
policy (600 seconds, transport/form retries at most 2, semantic retries 0,
stage/global request budgets) unless an explicit new user instruction changes it.
No provider/model call occurs before pre-source gates and execution seals.
Do not repair code/guard/adapter after the strict run starts.
Keep result ZIPs/SHA files only in iCloud Drive's existing Thesis Monitor folder,
verify hashes, and distinguish local copying from confirmed cloud upload.
