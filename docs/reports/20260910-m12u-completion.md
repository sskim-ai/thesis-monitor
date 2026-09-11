# M12U Completion: Offline Repair Passed, Canary Stopped

## Result

**PARTIAL_STOPPED / MODEL_TIMEOUT.** No new model calls after the failure.
Fresh real proof: **NOT_READY**. Production: **NOT_READY**.
Next scope: **ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW**.

The bounded semantic implementation passed deterministic validation. The new first shared context did not return a candidate within the frozen 1,800-second limit, so the generation stopped. This is not a semantic canary PASS or a repeated-stability measurement.

## Repository And Freeze

- Branch: `codex/20260910-financial-exclusion-expectation-m12u`
- Base: `e8e82e353ff71f251c66a1c6940af4d70ff0c778`
- Work instruction: `459af1097022b11fab15d9cda0a5836bd144bd9c`
- Offline contract review: `f73ce3a`, before implementation.
- Frozen implementation: `551f98f92e1f075990de1db1fd23eff4753c4da4`
- Final documentation SHA and its CI receipt are bound in the final ZIP export.
- Origin main remains `d18e68b1e944d7749d093b08797fcd9498412680`; no merge, deployment, restart or operating checkout mutation.
- After generation: 666 code files and 6 configuration files match their frozen hashes.
- Work-instruction file SHA-256: `0e9e1ecd6d5614568b5dbc5ffd9b895a1db5cbe0eb313018b4ce50e2699ca351`.

The authoritative M12T ZIP was rechecked: SHA-256 `d3202a35bcf5b13cd0afc86b59b1eda76c5088ecab377f3e63f316f6ca7a004b`; 142 indexed payloads, missing/extra/hash/size/secret failures all zero. Original raw output and FAIL receipts remain unchanged.

## Financial-Sector Exclusion Repair

The preserved phrase "일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다" was reproduced as a false reject before changes. The classifier now recognizes directly governed nominal non-applicability predicates and supported English equivalents, without a sentence/ticker whitelist.

Actual metric assertions, unrelated exclusions, mixed contradictory uses, double negation, conditional claims and industrial material anchors remain fail-closed. A leading exclusion does not immunize other fields.

New fixtures: 14 genuine exclusions and 15 negative/mixed controls, all PASS. Existing 12 positive and 20 negative fixtures also remain covered. Preserved M12T FIC-FIN-08 now passes offline for the correct exclusion reason; the old generation is not relabeled PASS.

## Economic Independence And Leverage

Frozen generic outcome: `LEV_EXPECTATION_CONTEXT_DEPENDENT_WITH_EXPLICIT_RULE`.
E07 classification: `CONDITIONAL_ON_SAME_UNRESOLVED_RISK`.

E07 is supplied evidence, not a hallucination. However, it describes expectation exposure to the same prolonged refinancing burden whose severity and persistence remain unresolved. Complete debt and thin cash establish limited resilience, not confirmed refinancing stress. No separate current pricing proposition is supplied.

For this qualitative pattern, the frozen target is **HOLD 4.5:5.5 SELL_LEAN**. Distinct evidence of confirmed financing stress plus independently established benign expectations can support minimum negative direction. Expectations already allowing for stress do not mechanically add negative corroboration. Strong resilience plus elevated expectations does not mechanically create BUY.

One generic calibration paragraph was appended. All prior prompt text is preserved. Source categories and evidence counts do not determine economic independence. No multiple or "expensive" conclusion is inferred. Absolute condition does not force a WEAKENED business delta; new-buyer and holder contracts are untouched.

Six LEV-MKT ordinal fixtures pass. They are authored qualitative contract examples checked with the existing ordinal tie-break, not an automated financial scoring engine.

Threshold 6.0, 0.5 increments, HOLD lean and tie-break toward 5.0 remain unchanged. First-class evidence projection, selector, other financial validators, source sufficiency, Daily Delta, Price-Timing and renderer semantics remain unchanged.

## New Generation

`20260910-m12u-fictional-20260909T231913Z-1e045065810d`

Source lock SHA-256:
`578672415e57bf74b15621face986961992a54ba17cac1d21d2b1a14753b6f9a`

Both planned context schemas equal M12T after generation-ID normalization. Both prompts differ only by the one frozen paragraph. All eight source contexts are unchanged.

| Context | Result |
|---|---|
| run-1/context-01, FIC-FIN-01..04 | MODEL_TIMEOUT; no candidate output |
| run-1/context-02, FIC-FIN-05..08 | NOT_RUN |
| run-2/context-01 and context-02 | NOT_RUN |
| run-3/context-01 and context-02 | NOT_RUN |

- Intended: 6 calls, 24 subject outputs. Actual: **1 call, 0 outputs**, 5 contexts not started.
- Started: 2026-09-10 **08:19:51 KST**. Finished: **08:49:51 KST**.
- Elapsed: **1,800.068784 seconds**; return code **-15** from the unchanged watchdog.
- Prompt/schema/output: **29,190 / 44,296 / 0 bytes**.
- CLI: **0.153.4**, header `gpt-6-astra / xhigh`; no fallback. A backend response model cannot be verified because no response was returned.
- Session: `01a08878-78e1-72c1-a4aa-1f02d3f0d680`.
- Runtime namespace: `17489fc8d5c4eb6a7185fe80`; unique invocation and working directory.
- CLI internal retry: **0**. Wrapper retry: **0**. Timeout: **1**. Orphan: **0**.
- Both the runner and child CLI were absent in the post-exit process check.
- No output file was created; no partial candidate was promoted.

This timeout did not have a logged websocket reconnect/error preceding it. It does not prove a particular backend, capacity or network root cause. M12T's prior recovered latency remains historical evidence, not proof that M12U transport was healthy.

Actual M12U exclusion, leverage, grounding, QTD/YTD, full/core/stance/delta stability and specificity are **NOT_MEASURED**. Empty rows/errors must not be interpreted as semantic success. No new FIC-FIN-05 or FIC-FIN-08 observation exists.

## Validation And Safety

- Focused: **186 PASS**. Full local: **3,225 PASS**, two existing deprecation warnings.
- Ruff and git diff check: **PASS**.
- Implementation GitHub Actions [34416304641](https://github.com/sskim-ai/thesis-monitor/actions/runs/34416304641): **3,220 PASS / 5 FAIL**, lint skipped after tests.
- The five failures are the same historical Git-object/local-ZIP portability dependencies. M12U new tests: **46 PASS; new hosted failures 0**.
- No CI threshold relaxation or portability repair in this task.
- Schedules: **8/8 PAUSED** at start and end. No automatic resume.
- Real-issuer/judge calls, provider fetches, Telegram sends, DB/assessment/warning/queue mutations, main merges and deployments: **0**.

P0 open: **0**. P1 open: **2**: Astra timeout recurrence and existing hosted-CI portability. The new semantic implementation needs model proof; it is not certified from deterministic fixtures alone.

## Handoff

Do not resume this generation, selectively retry its first context, enlarge the watchdog, split the batch, switch model/effort or run real issuers under this work instruction.

The next task is a bounded **ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW** using the preserved prompt, schema, transport log, receipt and run document. Keep the M12U semantic/config freeze intact until a separately authorized next experiment. Hosted-CI portability remains a separate P1.

Reports 01-79 contain the requested audit surfaces; 80-82 record live process observation, post-generation integrity and explicit no-output interpretation. Raw experiment artifacts are preserved separately in the ZIP.
