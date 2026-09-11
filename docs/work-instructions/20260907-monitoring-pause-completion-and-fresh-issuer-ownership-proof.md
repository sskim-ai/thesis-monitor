# Thesis Monitor — Monitoring Pause Completion & Fresh Issuer Ownership Proof

## 0. Task and intent

This is a new, bounded task after the completed capacity-failure partial-proof closeout.

Perform:

    finish the user's temporary pause of existing US/KR scheduled monitoring
    → verify no remaining automatic monitoring delivery path
    → preserve the held backlog and all investment history
    → if the pause is operationally complete, prepare one fresh unseen issuer proof
    → freeze source/runtime identity
    → FIRST → gates → A → gates → B → gates → C → gates

Do not turn this into another broad review project.

The investment architecture is not authorized for repair or production activation here.
The historical capacity error is classified, not proven resolved.
The retired cohort cannot be resumed.
The user's existing free-data-route policy remains an operating constraint, not a new gating project.

Suggested result bundle:

    thesis-monitor-20260907-monitoring-pause-completion-fresh-issuer-ownership-proof-report.zip

The operational pause and the research proof have separate success statuses.
If safe pause completion is blocked, preserve the operational evidence and stop before new model calls.
If the pause is complete but the source/model/proof fails, keep scheduling paused. Never auto-resume.

## 1. Source of truth and verified baseline

Latest historical result:

    thesis-monitor-20260907-scheduled-monitoring-pause-capacity-failure-partial-proof-closeout-report.zip

SHA-256 independently computed from the attachment:

    6c63a46a135a0abd6f5491366d33d56bbfe2d19f40e4b1f171633a3078b4adbe

Verify at task start. A mismatch blocks use of this bundle as the historical baseline.
Current HEAD/worktree is authoritative for current code; the ZIP is authoritative for historical reported outcomes.
Record discrepancies; do not silently rewrite either history or current code.

Historical repository:

    branch = codex/20260907-scheduled-monitoring-pause-capacity-failure-partial-proof-closeout
    base_sha = 5e98621bf5531f6da960ac7a47413f53f0fbe344
    work_instruction_commit = 309cd95959d184461a02078aa0c5b2c388d65f0a
    implementation_commit = 63f5f57df51566ed2198f1e007d470bbb61e1a02
    final_head_sha = 63f5f57df51566ed2198f1e007d470bbb61e1a02

Reported completion timestamp:

    2026-09-07T16:48:50+09:00

Recorded final scheduler observation:

    2026-09-07T16:30:35+09:00

These are historical observations, not proof of scheduler or model-capacity state now.

Archive verification:
- 127 ZIP members;
- 126 payload files indexed;
- only artifact-index.json excluded;
- indexed hash/size mismatch counts = 0.

The historical completion JSON says 126 members / 125 indexed payloads. Those are stale counters, not evidence of corrupt payloads. Preserve the old report and cite the actual index/inventory in a correction overlay. No new integrity framework is needed.

## 2. What is already complete — do not repeat it without cause

The historical FIRST:
- 7 real model invocations: 6 successful output contexts, 1 failed context;
- Core: 4 successful contexts, 16 output subjects;
- Timing: 2 successful contexts out of 3 attempted, 8 output subjects;
- 24 stage rows, 16 distinct issuers;
- FIRST attempted once, completed zero times, status FAILED;
- no A/B/C.

The failure:
- invocation ends in `first:PRICE_TIMING:03`;
- category CLI_REPORTED_MODEL_CAPACITY_FAILURE;
- lifecycle POST_SPAWN_NON_TIMEOUT_FAILURE;
- exit 1, elapsed 382.087626 seconds, configured timeout 1800 seconds;
- no watchdog termination;
- OUTPUT_FILE_MISSING is a downstream observation;
- explicit-run retry count 0; internal retries UNKNOWN;
- current model capacity NOT_CHECKED.

The closeout:
- Core16 and Timing8 offline checks PASS_PARTIAL_SCOPE;
- 8 composer/renderer derivatives are OFFLINE_RECONSTRUCTED, with input/code hashes;
- the derivatives are not historical raw model output and were not delivered;
- full-run ownership/renderer/hard-safety gates remain NOT_MEASURED;
- repeated stability remains NOT_MEASURED;
- ownership generalization remains NOT_ESTABLISHED;
- new real and fictional model calls in closeout = 0.

The source report records 10 focused tests, 2675 full tests, Ruff and CI PASS.
Treat these as historical test evidence, not a claim that tests ran in the current task.

Reuse the preserved partial proof. Do not regenerate it or rerun a canary campaign merely to restate PASS.
No model call to fill the missing historical Timing rows.

## 3. The unresolved operational dependency

The latest pause result is:

    us_pause_status = PAUSED_BY_TASK
    kr_pause_status = BLOCKED_OUT_OF_SCOPE_DEPENDENCY
    pause_result = PARTIAL_OPERATIONAL_COMPLETION
    changed_scheduler_objects = 6
    forced_termination_count = 0
    auto_resume_configured = false

Six primary/backup objects were paused:

    com.seungsoo.thesis-monitor.daily
    com.seungsoo.thesis-monitor.kr-close

    thesis-monitor-ai-review-us-primary
    thesis-monitor-ai-review-us-backup
    thesis-monitor-ai-review-kr-primary
    thesis-monitor-ai-review-kr-backup

Producer agents were recorded disabled and unloaded.
Four Codex automation definitions were recorded PAUSED.

Two dependencies were inspected but left active:

    com.seungsoo.thesis-monitor.ai-review-fallback
      python -m app.jobs.ai_review fallback --market all
      historical triggers: 08:40 / 17:10 KST

    com.seungsoo.thesis-monitor.ai-review-delivery-retry
      python -m app.jobs.ai_review retry-delivery --market all
      historical triggers: 08:22 / 08:25 / 08:30 / 16:22 / 16:25 / 16:30 KST

At the historical pause:
- KR packet `2026-09-07-kr-run-60-4ec80c93055c`;
- 9 held delivery items, sent count 0;
- US pending count 0, sent count 15;
- no existing per-market pause control was reported in the shared fallback/retry path.

KR9 means nine held delivery items, not nine monitored companies.
The recorded successful KR monitor run had ticker_count=8.

The shared fallback could still deliver the held KR packet.
Do not claim that it actually sent at 17:10 without later ledger/runtime evidence.
Do not assume the packet is still held now.

The final report recommends a separately authorized fresh proof, but that does not supersede the incomplete user-requested pause. Resolve this operational prerequisite first.

## 4. Authorization boundary for completing the pause

The user authorized a temporary stop of the existing US-morning and KR-afternoon scheduled monitoring, preserving registrations/history and with no automatic resumption.

This instruction explicitly extends the pause investigation to the two named fallback/retry dependencies above. It does NOT authorize disabling an unrelated shared scheduler, message service, macro workflow or Night Futures job.

An additional fallback/retry job may be temporarily disabled only after current code/configuration proves that ALL of its work belongs to these two authorized monitoring flows.

The label, word "shared", or `--market all` alone is not proof of exclusive scope.

Decision:
1. If a named dependency exclusively serves the paused US/KR monitoring flows, include that exact job in the reversible pause.
2. If it genuinely serves unrelated flows, do not globally disable it.
3. If an existing scoped suppression mechanism can safely pause only US/KR monitoring, use it without changing unrelated behavior.
4. If neither an exclusive job nor a supported scoped control exists, report PAUSE_DEPENDENCY_BLOCKED. Do not invent/deploy a new gate or silently broaden this task.

No new per-market control plane, generic queue-management service, billing gate or scheduler redesign is required or authorized.
This is an operational closure using existing controls wherever possible.

## 5. Provenance and work-instruction commit

Before changing any code/configuration or scheduler object, record:

    git branch --show-current
    git rev-parse HEAD
    git status --short

Commit this instruction before implementation or operational mutation.
Record the actual commit; do not invent a branch or restore to a historical SHA.

Classify later changes:
- documentation/evidence changes;
- authorized scheduler-state changes;
- experiment/report-only changes;
- unexplained semantic/runtime changes.

Do not reset, merge, cherry-pick or discard unrelated work.
Unexplained semantic drift affecting the proof blocks model execution.
Safe read-only scheduler/archive inspection may continue independently if its inputs remain trustworthy.

## 6. Phase A — Current-state and dependency inspection

Use read-only state before mutation:
- effective enabled/loaded state of the six paused objects;
- persisted automation status and controller interpretation;
- current definitions, command, market routing and purpose of the two dependencies;
- current-running processes/jobs separately from future trigger state;
- current KR packet/held delivery state;
- any automatic recreation/re-enable mechanism relevant to these exact objects.

Capture IDs, backend, safe definition hash, trigger/timezone, observed_at and reference backup.
Do not expose credentials or token-bearing arguments.

Trace fallback/retry scope through actual handlers and current scheduler configuration.
Determine whether macro, Night Futures, other recipient flows or other applications can use the same job.
Do not infer scope solely from function or job names.

Do not run `fallback`, `retry-delivery`, the producer or AI review as a production smoke test.
Such execution may write state or send messages.
Use read-only inspection and existing model-free test doubles.

If US is already paused, do not toggle it.
A blocked US observation is not a reason to omit safe KR observation, or vice versa.

## 7. Phase B — Safely complete the authorized pause

For every authorized exclusive dependency:
- back up definition/status with a hash;
- use the existing supported reversible pause/disable mechanism;
- preserve definitions;
- verify the persisted and effective state, including unloaded state where required;
- verify an ordinary controller will not immediately re-enable it.

The previous task saw an already-loaded KR calendar job execute at 16:20 after a disable override.
Therefore `disabled=true` alone is not sufficient evidence when a loaded calendar trigger can still run.

Do not forcibly terminate active processes.
Distinguish disabling future starts from stopping a running job.
If a safe inactive transition cannot be established, record BLOCKED_ACTIVE_RUN and defer the unsafe operation.
Do not treat an unload command that may kill active work as a harmless pause.

Record the mutation order, observations and any intervening invocation.
Use an existing supported lock/guard if available; do not invent a new lifecycle implementation solely for this task.

After mutation, inspect current state again. A zero process count alone does not prove schedules are disabled.
No schedule deletion, stock unregistration or automatic resume.

Expected statuses use existing canonical values or explicitly mapped equivalents:

    ALREADY_PAUSED
    PAUSED_BY_TASK
    PAUSED_COMPLETE
    BLOCKED_ACCESS
    BLOCKED_ACTIVE_RUN
    BLOCKED_OUT_OF_SCOPE_DEPENDENCY
    UNKNOWN

Keep per-market status separate from overall success.

## 8. Preserve backlog and handle the pause-transition evidence

Read and preserve the delivery ledger for the historical KR packet, if it still exists.
Record exact message IDs or safe identifiers and counts by held/pending/sent/failed state with observation time.

Do not:
- send held messages to clear the queue;
- delete them;
- mark them sent without delivery;
- requeue them;
- modify investment evaluation/baseline/warning data;
- create artificial no_material_change assessments during the pause.

If the 17:10 fallback already ran, record actual delivery/DB evidence and distinguish it from actions initiated by this task.
Do not infer that the old sent=0 still applies, or that disabling later can undo earlier delivery.

The prior report states one 16:20 transition invocation; the broader producer counter moved from 9 to 11 while the cited 16:20 segment moved 10 to 11.
Reconcile only if existing logs/ledger cheaply support it. Otherwise keep the wider interval/count and write scope UNKNOWN.
This is a bounded observation, not a full monitoring-history repair project.

Investment-state preservation:
- retain registered stocks, investment-logic versions, baseline, assessments, warnings and price rules;
- retained delivery backlog remains history, not proof of fresh data;
- no task-initiated manual investment-state DB mutation.

No task-initiated Telegram send, including test messages.
No in-flight process termination.
No automatic resumption after task success, failure, a capacity recovery or a timer.

## 9. Operational completion condition

Mark scheduled pause complete only when:
- both US/KR primary and backup entry points remain paused;
- all relevant automatic fallback/retry paths are either safely paused as proven exclusive jobs or blocked by an existing scoped mechanism;
- the held backlog has no remaining authorized automatic send path through these schedules;
- current in-flight state is explicitly recorded;
- effective future trigger state is verified, not guessed;
- unrelated jobs remain unchanged;
- restoration requires a new explicit user request.

Distinguish "no future automatic scheduled work" from a claim that no external/manual activity can ever occur.
Do not claim complete service silence from a job-state snapshot.

If a needed dependency cannot be safely paused within this boundary:
- preserve safe changes already made;
- record the blocker accurately;
- do not start a new real model proof;
- do not build a new suppression service here.

Use a separate operational readiness field. Do not report all-task PASS merely because the historical partial audit passed.

## 10. Phase C — Fresh proof preparation only after pause completion

No additional review-only handoff is required if operational completion and all existing proof gates pass.
Proceed using the established experiment runner.

Use existing data sources and existing free-route policy:
- no new paid provider, upgrade, account, credentials or paid fallback;
- no new free-entitlement/billing/quota gate project;
- no market-wide detailed-data scan;
- obey existing bounded request/cache/retry behavior;
- preserve source-sufficiency and financial/identity safeguards.

Do not claim that all current routes have been independently cost-audited.
AI inference configuration remains separate from the user's external-data policy.

Do not redesign source coverage, supported universe or valuation to improve candidate availability.
If current supported sources cannot supply the required cohort, report a bounded source blocker without calling the model.
Diagnose both US and KR safely even if the first market fails.

## 11. Exposure registry and immutable historical cohort

The latest exposure overlay reports:
- prior registry count 85;
- 16 newly exposed issuer rows;
- reconciled count 101.

Use the actual canonical registry and overlay, not just those totals.
Preserve earlier exclusions and aliases; verify deduplication with existing issuer identity.
Never shrink exclusions merely to fill the target.

The fully exposed historical cohort is:

    NVMI  SKYH  WKSP  EROC
    373160  452200  389470  380550
    008970  047080  068270  475830
    033160  079940  103140  278280

Preserve:
- issuer exposure = 16/16;
- Core stage coverage = 16/16;
- Timing stage coverage = 8/16;
- complete historical FIRST coverage = 0;
- retirement reason INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE;
- future unseen reuse = 0;
- same-cohort architecture-tuning rerun = 0.

Keep the legacy retirement label with its explicit stage-based explanation rather than rewriting original artifacts.
No retry of historical Timing03, no remaining-Timing continuation, no historical A/B/C, no replacement of missing rows using another run.
Capacity failure is nonsemantic; it does not undo exposure under the precommitted experiment rules.

## 12. Deterministic new candidate selection

Use the existing supported universe, canonical issuer keys and current exclusion registry.
Before evaluating candidate outcomes, freeze:
- candidate universe/reference snapshot identity;
- exclusion hash;
- deterministic selection rule/seed;
- market targets US4/KR12;
- bounded primary/reserve ordering and evaluation budgets;
- objective eligibility/replacement criteria.

Use the existing selector. Do not create a new reference-discovery project.
If a new seed/version is necessary, record it once before source evaluation; do not reroll based on output.

Accept only the first eligible issuers under the precommitted order.
Objective pre-model failures may use the next reserve: identity, unsupported source path, duplicate issuer or source validation/sufficiency.
Do not select on anticipated BUY/HOLD/SELL, desired stability, price trend or attractive narratives.

Do not treat identity-supported reserves as source-ready.
Do not treat examined-but-source-failed candidates as unexamined reserves.
Keep counts by market and by security/issuer/readiness stage consistent.

If US fails its bounded target, still complete safe bounded KR diagnostics.
If KR fails, retain US results without launching a partial proof.
No real model call until US4 and KR12 both pass.

## 13. Fresh final source lock

Build a new source generation for the final new 16 issuers using current supported routes.
Historical source locks are not reused for a different cohort.

Revalidate:
- issuer/security identity and provenance;
- required fundamental families;
- accounting attribution and ADR/share/currency basis;
- supported period/currentness checks;
- safe price-readiness category.

Fundamental sufficiency and Price-Timing readiness remain distinct:
- valid absent price follows the existing UNAVAILABLE_SAFE path;
- no invented current price/technicals;
- malformed/future/unsafe data remain blocked;
- missing optional forward estimates do not become fabricated values.

Persist final ordered cohort, market mix, context grouping, per-issuer packet hashes, source_generation_id and source_lock.
No source refresh or issuer replacement after the first real call.

All replacements must be resolved before final freeze under the already-precommitted reserve order.
If the target cannot be met, no final execution lock and no real model calls.

## 14. Final runtime precommit and identity checks

Model/runtime remain the previously frozen experiment settings:

    model = gpt-5.6-sol
    reasoning_effort = xhigh
    batch_semantics = MODEL_CONTEXT_COUPLED
    shared_context_subject_count = 4
    model_timeout_seconds = 1800
    model_timeout_owner_count = 1

Use the exact prior canonical run/stage ordering.
Do not change interleaving of Core/Timing, context size, state-namespace lifecycle or model parameters to reduce capacity risk.

Create a new runtime generation with explicit source-generation linkage.
One binding must supply actual prompt, on-disk schema, validator, receipt and manifest IDs.
Do not weaken schema const rules, accept both source/runtime IDs, or make synthetic identity exceptions for real requests.

Precommit:
- implementation commit/hash and clean semantic worktree evidence;
- source lock and full cohort;
- stage/context/run topology;
- model/effort/timeout;
- expected invocation budget derived from the actual frozen runner;
- no automatic retries/model switch;
- preservation/early-stop rules;
- failure and retirement semantics.

For the previously measured four Core plus four Timing contexts per run, the expected model budget is 8 per run and 32 for complete FIRST/A/B/C, with deterministic rendering separate.
Confirm this against current frozen code. If it differs, do not silently change topology or add a renderer model stage; record and stop pending reconciliation.

Reuse prior 64-context model-free rehearsal evidence where affected code is unchanged.
Do not repeat the whole rehearsal merely to increase test counts.
Validate the actual imminent prompt/schema files and binding before each call.
Timing-dependent inputs may be materialized after the corresponding Core output, but must pass exact-request identity checks before transport.

The source inputs will differ from the retired cohort intentionally.
Prove within-generation FIRST/A/B/C input immutability; do not falsely require the new cohort's hashes to match the retired cohort.

## 15. Capacity and live-workload boundaries

Local schedule pause is not evidence that remote model capacity is available.
Preserve current capacity as NOT_CHECKED unless a real authorized invocation provides a result.

Do not add:
- a capacity probe or polling loop;
- a synthetic canary campaign;
- fallback models/effort/accounts;
- larger timeout;
- new retry/backoff policy;
- automatic fresh-cohort retries.

Keep the existing live-workload guard. Paused schedules do not prove that no manual or in-flight workload exists.
Observe safely using the already repaired supported path.
Do not assume zero contention on observation failure.
Do not remove protected-window rules; if they defer an invocation, use existing safe policy or stop with a factual defer record.
No force cancellation of other work.

Only the one explicitly precommitted new proof sequence is authorized.

## 16. FIRST and per-context evidence

Execute FIRST once as a cohort-level attempt, not once per ticker.

Before every real context:
- actual-request source/runtime/market identity PASS;
- current coexistence decision safe;
- no prior failure that requires stop.

After every successful context, before the next:
- persist exact raw output, stdout, stderr/log or safe redacted derivative;
- persist actual prompt/schema, receipt, binding, manifest and subject mapping;
- compute byte size/SHA-256 and reopen verification;
- retain original bytes distinct from normalized/derived output;
- run applicable frozen offline semantic checks.

A preservation failure is a real stop; model output still counts as exposure even if persistence failed.
Pre-spawn failures do not require nonexistent subprocess output/receipt; preserve the primary error and pre-spawn evidence instead.
A post-spawn missing receipt remains independently reportable.

No new Telegram send.
For deterministic composed/rendered rows, save structured state and rendered message at generation time.
Do not wait for full-run success to save them.
Label later reconstructions clearly and keep original vs derivative provenance distinct.

## 17. Per-context and per-run gates

For every completed Core context, enforce existing hard invariants:

    DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
    DIRECTIONAL_CORE_SUPPLY_REFS = 0
    SUPPLY_DIRECTIONAL_CORE_USAGE = 0
    BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
    SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
    DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
    PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0
    FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

For available Timing/composed/renderer rows, enforce applicable existing invariants:

    TIMING_STAGE_DIRECTION_MUTATION = 0
    TIMING_STAGE_BALANCE_MUTATION = 0
    TIMING_STAGE_HOLD_LEAN_MUTATION = 0
    PRICE_TIMING_NEW_BUYER_UPGRADE = 0
    PRICE_ONLY_HOLDER_REDUCE = 0
    PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0
    PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
    AI_IMPERATIVE_PRIMARY_ACTION = 0
    KNOWN_HARD_SAFETY_REGRESSION = 0

No premature Timing/renderer PASS before the needed stage exists.
Retain measured scope, applicable/checked rows, violations, validator version and source artifact.

Core owns fundamental direction, balance, HOLD lean and business invalidation.
Timing can make new-buyer stance more conservative, not upgrade it.
Timing may create price-review pressure but not price-only holder REDUCE.
Technical/supply movement is not business-thesis change.
Preserve numeric/accounting/ADR/provisional-earnings safeguards and Unknown handling.

After complete FIRST, full ownership, renderer and hard-safety gates must PASS before A.
Then:

    A → its own complete gates → B → its own complete gates → C → its own complete gates

Stop at the first required execution/preservation/identity/semantic gate failure.
Do not collect further stochastic samples after a failure.

## 18. Failure, exposure and retirement accounting

Separate:
- attempted/terminal/successful/failed contexts;
- stage output rows and distinct issuers;
- FIRST attempts and completed runs;
- full-run vs partial checks;
- explicit orchestration retries vs unknown internal CLI/backend retries.

On a capacity diagnostic:
- preserve exact receipt/log and primary error;
- classify CLI_REPORTED_MODEL_CAPACITY_FAILURE where supported;
- do not replace primary error with OUTPUT_FILE_MISSING;
- do not call it watchdog timeout unless watchdog evidence supports that;
- stop the new proof with retry=0 and no model switch.

If no usable real output exists:
- UNEXPOSED output state;
- semantic checks NOT_MEASURED;
- later reuse requires explicit review, not an automatic retry.

If any real issuer output exists:
- mark actual unique-issuer exposure immediately;
- remaining timing stages do not make already exposed issuers unseen;
- preserve the entire locked cohort's retirement/exclusion contract;
- no selective remaining-context/stage continuation.

If all 16 Core outputs exist but Timing is incomplete:
- issuer exposure FULLY_EXPOSED;
- stage coverage shown separately;
- retire with explicit incomplete-FIRST-after-full-exposure reason.

If a hard semantic defect is confirmed:
- REVEALED_FOR_ARCHITECTURE_TUNING;
- retire for generic repair;
- no same-task architecture fix or same-cohort rerun.

After clean FIRST, A/B/C are allowed only as already-precommitted repeats, not as fresh unseen evidence.
Any A/B/C failure stops later contexts/runs and leaves the cohort exposed/retired.
No automatic new cohort loop.

## 19. Stability and generalization decision

Use only legitimately completed runs that passed their own hard gates.
Retain failing/partial outputs as failure evidence; do not mix them into valid stability denominators or hide them.

Use the existing frozen categories/thresholds for:
- Directional Core stability;
- Price-Timing stability;
- boundary uncertainty;
- ownership generalization.

Do not invent thresholds or automatically claim PASS merely because a stability report exists.
Only an actual PASS under the canonical frozen protocol permits readiness advancement.
If the required protocol is missing or ambiguous, stop before real calls rather than inventing a permissive criterion.

Insufficient complete repeats => NOT_MEASURED/NOT_ESTABLISHED, not zero instability.
Do not combine the prior Core16/Timing8 partial proof with the new cohort to fill missing samples.

Full proof PASS may hand off to Monitoring Bootstrap Integration Review.
Do not implement bootstrap, merge/deploy V2, activate production messaging or resume schedules here.

## 20. Narrow implementation and test scope

Prefer no semantic implementation changes in this task.
Allowed:
- explicitly authorized reversible scheduler/config pause;
- existing experiment orchestration/report finalization glue;
- model-free tests for actually changed paths.

Forbidden:
- new scheduler platform/per-market gate;
- general transport redesign;
- source-sufficiency relaxation;
- universe-expansion or free-API entitlement project;
- investment architecture/prompt/schema semantic changes;
- arbitrary ticker exceptions;
- production model/renderer deployment.

If a blocker needs one of these changes, stop and name a separate scope.
Do not hotfix after new real outputs.

Run focused and repository-required tests/lint for changed code.
If no relevant code changed, reuse prior validated evidence with matching hashes instead of rebuilding tests/fixtures unnecessarily.
Tests must not invoke actual schedules, model APIs or Telegram.

## 21. Production accounting and restoration

Do not report production_scheduler_change=0 if additional jobs were paused.

Separate:
- prior task changed scheduler objects = 6;
- current task's actual idempotent/new mutations;
- logical schedules = 2;
- additional exclusive fallback/retry dependencies paused;
- unauthorized/unrelated schedule changes = 0.

Expected zero for task-initiated:
- manual investment-state DB mutation;
- stock registration/unregistration;
- Telegram send;
- live V2/Structured Autonomy change;
- main merge/deployment;
- Night Futures change;
- provider/credential/paid dependency changes;
- forced termination;
- auto-resume.

If an in-flight natural job writes DB or sends during the transition, record observed action and attribution honestly.
A task-initiated count of zero is not proof that all production activity was zero.

Preserve restoration references for every changed object, including additional dependencies.
Do not execute restoration.
A later explicit resume must examine the monitoring gap and held backlog before delivery; missing dates are not no_material_change and retained old packets are not fresh alerts.

## 22. Compact deliverables

Use existing artifact conventions, not a new framework.

Always produce:
1. input integrity, current repository and work-instruction provenance;
2. current scheduler/dependency scope inventory;
3. pause actions, before/after evidence and per-market completion;
4. backlog/in-flight/transition observation and restoration reference;
5. actual production-change accounting.

If pause completion permits proof, also produce:
6. prior exposure registry + new deterministic candidate/reserve policy;
7. US/KR source-readiness and final selection/freeze manifest;
8. actual request identity/transport/coexistence evidence;
9. per-context raw artifacts, composed/rendered output and partial audits;
10. per-run FIRST/A/B/C execution and ownership/renderer/hard-safety gates;
11. exposure/stage-coverage/retirement state;
12. stability/generalization and next-scope decision;
13. final completion + artifact index.

If a phase did not run, use explicit NOT_RUN/NOT_MEASURED with the blocker.
Do not produce dozens of empty PASS artifacts.
Archive successful and failed contexts, not only final summaries.

Final completion minimum:
- input SHA and commit/branch identities;
- historical vs current scheduler-change counts;
- fallback/retry scope proof and actual pause state;
- US/KR pause statuses and remaining blockers;
- held/sent/in-flight counts with times and unknowns;
- forced termination, auto-resume, test/model/Telegram side effects;
- exposure-registry and selection-policy identity;
- source lock/runtime generation/model/effort/context/timeout;
- attempted/successful/failed/terminal contexts by run and stage;
- stage rows and unique exposed issuer count;
- per-context/per-run gate statuses with denominators;
- capacity/timeout/identity/semantic failure classification;
- explicit retries and internal-retry observability;
- full-run and repeated-proof outcome;
- investment/runtime drift and production change accounting;
- operational readiness and research readiness separately;
- stop_reason and next_scope.

## 23. Artifact finalization

Freeze all payloads, including completion reports, before generating the final index.
Index every payload except the index itself with path/hash/byte size and provenance class.
Keep the final ZIP checksum in an external sidecar.

Verify:
- CRC and safe unique paths;
- every payload's membership/hash/size;
- actual member_count = indexed_payload_count + 1 when only the index is excluded;
- completion counts match the final inventory.

Avoid the prior one-file count lag.
This is a packaging fix, not a reason to invalidate already hash-verified historical evidence.
No PENDING_FINALIZE fields in a delivered completion report.
Never expose secrets or credential-bearing configuration.

## 24. End-state decisions

A. Pause dependency unresolved:
   keep completed pauses in place; no proof calls;
   report PARTIAL_OPERATIONAL_COMPLETION with the exact unsupported/shared dependency.
   Do not silently disable unrelated work.

B. Pause complete, source target incomplete:
   no real calls; preserve both market diagnostics;
   report the bounded source blocker, no new policy project.

C. Pause complete, proof execution fails:
   preserve all outputs/failure evidence; no retry or automatic new cohort;
   keep scheduling paused and classify capacity separately from model/architecture defects.

D. Confirmed semantic defect:
   no same-task repair; next scope generic semantic repair with new unseen proof later.

E. Full canonical FIRST/A/B/C proof PASS:
   next scope Monitoring Bootstrap Integration Review;
   production still not promoted and scheduling still paused.

The intent is to finish the user's actual pause, then perform the real proof—not add another layer of administrative gates, and not repeat the already-completed offline closeout.
