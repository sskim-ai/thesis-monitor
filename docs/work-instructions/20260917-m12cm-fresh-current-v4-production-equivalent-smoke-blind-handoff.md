# Thesis Monitor — M12CM Fresh Current US14/KR8 Production-Equivalent Smoke Under Stage-2 v4
## Current Market Refresh + KRX Night-Futures Regression + Blind Human/AI Handoff

## 0. Task identity and bounded authorization

This task follows the accepted M12CL result:

`M12CL_SUPPORTING_CLAIM_COMPLETENESS_OFFLINE_CLOSURE_PASS`

M12CM is a **fresh current-data production-equivalent smoke** under the frozen Stage-2 v4 contract. It is not another contract redesign, schema repair, provider migration, Full22 historical reproof, deployment, scheduler activation, production send, or human/AI comparison task.

Suggested work-instruction filename:

`20260917-m12cm-fresh-current-v4-production-equivalent-smoke-blind-handoff.md`

Required result bundle:

`thesis-monitor-20260917-m12cm-fresh-current-v4-production-equivalent-smoke-blind-handoff-report.zip`

matching `.sha256`.

The objectives are exactly:

1. verify current safe US/KR market-source and deterministic market-message paths without changing providers;
2. carry the KRX/Kiwoom KOSPI200 202612 date-semantic control forward and, when available, close the previously unpublished mapped provider date;
3. freeze a new facts-only human-review packet **before any model inference**;
4. run a wholly new current monitored-stock Core + Stage-2 v4 stream from call 1 with no retry/repair/reuse/stitching;
5. require complete accepted-v2 finalization/readback/capture for the current canonical population;
6. seal all AI verdicts so Chat/user can judge the facts independently before any AI comparison.

All architecture, repair, deployment and comparison decisions return to Chat.

---

# 1. Authoritative sources and exact entry state

Use this priority:

1. this M12CM instruction;
2. exact local repository state matching the M12CL final/report head and application hashes;
3. verified M12CL result bundle;
4. verified M12CJ result bundle for prior current-smoke/fixture evidence;
5. verified M12CH result bundle for the successful no-repair 22/22 baseline;
6. older reports only for historical context.

### M12CL

- terminal result: `M12CL_SUPPORTING_CLAIM_COMPLETENESS_OFFLINE_CLOSURE_PASS`;
- result ZIP SHA-256: `744f638e56436d31b6bdc8eb4aece3f68cd7daf0e4a2f02d8feabf7dbddd8024`;
- required pre-M12CL base: `edb2debb43e3dcc4e59baa26fc57db4cc381d585`;
- M12CL instruction commit: `8b9c1c9029ee334ddb6c319700cd2c2dbd6495fb`;
- M12CL result `head_at_report_generation`: `831890d1bf0dff303f67a6e0de1403ad3221b5d8`;
- changed application owner:
  `app/services/accepted_decision_v2_runtime_service.py`;
- expected post-M12CL SHA-256 for that application file:
  `af8a4b717be88d98c29c4b8c839f4b5235ec2d6ec998dbd9947198b7c5212d98`;
- active raw Stage-2 contract:
  `v2-accepted-stage2-model-output-v4`.

### M12CJ

- terminal result: `M12CJ_MONITORED_STOCK_SMOKE_NOT_CLOSED`;
- result ZIP SHA-256:
  `b700f8db4ac8e382b560513575ee5fb9dae68cb302a5e1b129a4df7bd2786754`;
- market layer passed;
- canonical monitored population at that observation:
  US14 + KR8;
- US Core 14/14;
- US Stage-2 raw 14/14;
- deterministic validation 12/14;
- WRD/WULF failed because supporting atomic claim identity was absent;
- no KR model calls followed the first hard US failure;
- historical sealed AI archive remains sealed.

### M12CH

- result ZIP SHA-256:
  `84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e`;
- generation:
  `20260917-uskr22-m12ch-20260917T000529Z-65611727332a`;
- Core 22/22;
- Stage-2 22/22;
- finalization 22/22;
- native readback 22/22.

M12CL proved that all M12CH 64 maturity rows are compatible with v4 and that accepted artifacts/renderers remain semantically unchanged under offline replay.

Do not reopen M12CH/M12CL because fresh current facts or model decisions differ.

---

# 2. Frozen v4 model contract — verify before any model call

M12CM must use the exact current builder/schema path, not a historical copied schema.

Before call 1 prove from the actual local runtime:

```text
active raw contract =
v2-accepted-stage2-model-output-v4
```

For every `DriverEvidenceMaturity` row:

```text
supporting_claim_refs:
  required
  array
  exact enum values from same-ticker MATURITY_ATOMIC_CLAIM_CATALOG
  minItems = 1

contradicting_claim_refs:
  required
  array
  exact enum values from same-ticker catalog
  empty allowed
```

The model still must not author:

```text
supporting_evidence_refs
contradicting_evidence_refs
as_of
provenance_status
```

Those remain runtime-owned projections/materialization.

Prompt contract must still say:

- every driver has at least one exact same-ticker supporting atomic claim;
- if no supplied atomic claim supports a driver, do not emit that driver;
- contradictory claims may be empty;
- no invented/approximated/shortened/split/repaired claim identities;
- supporting/contradicting relation is driver-relative, not equivalent to absolute BULLISH/BEARISH polarity.

Run a local schema negative before model inference showing that an otherwise-valid row with
`supporting_claim_refs=[]` is rejected by the actual schema path.

Do not patch the schema after call 1.

---

# 3. Current population preflight

Resolve the canonical monitored population from the current production universe/state at actual execution time.

M12CJ observed this exact expected set:

### US expected 14

```text
CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

### KR expected 8

```text
000660
003690
005490
005930
010120
012450
047810
086280
```

This list is an **expected drift control**, not authority to overwrite current canonical state.

If the canonical population still equals 22 with the same identities, use the fixed 16-call topology in section 8.

If the population differs because of a separately documented intentional monitoring-state change, do not silently force it back to 22. Export the exact difference and return to Chat before inference unless the current runtime already owns a deterministic supported batching path and the difference is clearly not a task-scope change.

No subject may be dropped because its output is difficult.

NVDA or any other inactive/unrequested subject must not be inserted merely to restore a count.

---

# 4. Isolation and safety

Use an isolated temporary root and isolated state/DB/intent/delivery surfaces.

Permitted:

- current approved market/provider reads used by canonical runtime;
- current approved signed-in inference transport;
- isolated test/capture sink;
- provider-owned deterministic retry behavior already part of a source contract.

Forbidden:

```text
production_send = 0
production_recipient_intent = 0
production_db_mutation = 0
production_warning_mutation = 0
scheduler_start_resume_change = 0
main_merge = 0
remote_push = 0
deployment = 0
broker_order = 0
broker_modify = 0
broker_cancel = 0
windows_kiwoom_gateway_provision = 0
model_retry = 0
wrapper_retry = 0
fallback_model = 0
judge_model = 0
repair_model = 0
schema_repair_model = 0
candidate_repair = 0
selective_model_rerun = 0
per_ticker_model_retry = 0
prior_model_output_reuse = 0
cross_generation_stitch = 0
hotfix_after_first_formal_call = 0
```

Do not expose credentials.

A hard source/model/contract failure is preserved as evidence and cannot be repaired/resumed within the same generation.

---

# 5. Current session resolution

Record the execution timestamp with timezone and use existing exchange/session calendars.

## US

Resolve the latest safely completed US regular session under the canonical current-market rules.

Use actual source observation dates for Treasury, breadth, sector/style and other market facts. Do not relabel lagging publication data as current.

## KR

Respect the actual XKRX regular-session state.

If execution occurs before the current KR regular session completes, do not label intraday data as a completed KR-close run. Use the existing typed behavior: latest completed close-equivalent context or a separately typed supported intraday mode if the current canonical runtime actually owns one.

Do not bypass a session guard.

For both markets export:

- observation timestamp;
- chosen target session;
- source/as-of dates;
- current/stale/partial/omitted states;
- exact reason a rendered fact is eligible.

---

# 6. KRX night futures and Kiwoom acceptance control

KRX remains the machine authority.

Preserve the chain:

```text
official KRX NIGHT daily OHLC
→ immutable/raw receipt
→ normalized daily history
→ canonical near-month selection
→ same-contract D/W/M
→ packet-owned facts
→ deterministic renderer
```

No Kiwoom gateway is required.

The M12CJ result includes the original ten user screenshots and extracted fixture.

### Human fixture

Instrument:

```text
KOSPI200
contract shown by Kiwoom = 202612
```

Kiwoom session-date 2026-09-16:

```text
Daily
O 1058.70
H 1069.30
L 1036.00
C 1050.55
V 34382

Current weekly
O 1043.00
H 1069.30
L 1016.00
C 1050.55
return -4.40%

Current monthly
O 1062.00
H 1128.55
L 1016.00
C 1050.55
return -1.04%
```

M12CJ established a provider/chart date-semantic mapping: a Kiwoom night session labeled by its session-start/business date may correspond to the KRX `BAS_DD` representing the session completion/publication date.

It obtained three exact same-economic-session controls and one mapped source-not-present case.

In M12CM:

1. preserve the prior M12CJ comparison unchanged;
2. if KRX `BAS_DD=2026-09-17` is now safely available, compare it to the Kiwoom `2026-09-16` night-session fixture;
3. require exact comparable O/H/L/C/V parity for that mapped economic session, or an evidence-backed semantic explanation;
4. do not rewrite KRX or Kiwoom values;
5. no KOSDAQ150 human fixture is required; keep machine validators only;
6. current user-facing night facts may naturally use a later safe reference date than the historical 2026-09-16 fixture.

Allowed historical fixture outcomes:

- `EXACT_PARITY_WITH_DATE_MAPPING`;
- `EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE`;
- `SOURCE_NOT_YET_AVAILABLE`;
- `UNEXPLAINED_MISMATCH`.

An `UNEXPLAINED_MISMATCH` is a real blocker for that night-futures smoke layer.

The literal contract `202612` is only a human historical fixture. Current near-month selection must remain generic.

---

# 7. Freeze facts-only human review before inference

This is mandatory.

After current source collection/preparation is complete and **before the first formal model call**, create and freeze:

`human-review/`

At minimum:

- `US_MARKET_FACTS_ONLY.md/json`;
- `KR_MARKET_FACTS_ONLY.md/json`;
- `MONITORED_STOCK_FACTS_ONLY_INDEX.json`;
- one facts-only JSON/MD per monitored subject;
- source/as-of/quality/ref lineage;
- current price/technical structure already available to canonical evidence;
- current fundamental/business/evidence facts;
- material market context and source limitations.

Record hashes and freeze timestamp in:

`human-review-freeze-manifest.json`.

After call 1, these files must never change.

Hard exclusions from facts-only files:

- model BUY/HOLD/SELL;
- new-buyer verdict;
- holder verdict;
- directional balance;
- model maturity conclusion;
- accepted-plan recommendation;
- model-generated summary;
- any filenames/counts/ordering designed to hint at verdict labels.

Facts-only generation must be deterministic from evidence/source objects, not a model summary of model output.

---

# 8. Fresh 16-call formal topology

When the canonical population is the expected US14/KR8, execute exactly this fresh topology from call 1.

### US Fundamental Core — calls 01–05

```text
01 CORZ / CPNG / CRCL
02 GOOGL / HUT / IBM
03 MU / RXRX / SKHY
04 SNDK / TSLA / TSM
05 WRD / WULF
```

### US Stage-2 v4 — calls 06–10

Same five batches.

### KR Fundamental Core — calls 11–13

```text
11 000660 / 003690 / 005490
12 005930 / 010120 / 012450
13 047810 / 086280
```

### KR Stage-2 v4 — calls 14–16

Same three batches.

Required:

- new generation ID created at execution time;
- no M12CH/M12CJ model output reused as a current answer;
- every Core raw response frozen immediately;
- every accepted Core independently persisted before Stage-2;
- Stage-2 consumes only the same-generation accepted Core;
- every raw Stage-2 output frozen before materialization;
- v4 schema is the model-facing schema;
- no speculative later calls after a prerequisite hard failure.

Current configured model/effort are whatever the exact frozen runtime currently owns; M12CJ/M12CH observed `gpt-5.6-sol / xhigh`. Verify without silently substituting.

---

# 9. First-hard-failure semantics

For every batch:

1. raw parse/schema;
2. exact subject/batch identity;
3. exact refs;
4. materialization of runtime-owned source refs/provenance;
5. maturity atomic identity/polarity/eligibility;
6. all semantic/numeric/entry-holder/Core-binding gates;
7. accepted-plan finalization;
8. artifact construction;
9. native readback;
10. deterministic render/capture.

As soon as an unexpected hard failure occurs in a formal dependent stream:

- stop the dependent later inference calls;
- do not retry the call;
- do not repair the output;
- do not switch models;
- do not drop a subject;
- do not resume from the next call after a patch;
- preserve exact failing raw bytes/context/Core/schema/prompt and stack/gate;
- safe independent market/source diagnostics may finish if they do not alter the generation.

Expected-negative local preflight fixtures are not formal failures.

---

# 10. v4-specific required observations

For every successfully parsed Stage-2 v4 output export structural, verdict-free measurements:

- number of `driver_maturity` rows;
- `supporting_claim_refs` cardinality distribution;
- count with zero supporting claims — must be **0**;
- contradicting cardinality distribution;
- exact claim-ref enum membership;
- cross-ticker/unknown claim count — 0;
- overlap count between support/contradiction — 0;
- model-authored source-ref count — 0;
- model-authored `as_of` count — 0;
- model-authored `provenance_status` count — 0;
- runtime projected source-ref parity result;
- symbolic/mixed/concrete provenance counts observed naturally.

Do not require the new generation to have the same row counts or decisions as M12CH.

WRD/WULF are not target-label fixtures. The only relevant regression is that the new v4 schema does not permit the historical empty-support shape.

---

# 11. Current market-message smoke

Execute the canonical current market paths in the same isolated run.

## US

Verify:

- latest completed-session indices;
- breadth/style/sector facts under existing source contracts;
- Treasury nominal/real/breakeven facts at their true observation dates;
- KRX night section under current safe KRX availability;
- message-quality validation;
- capture sink only.

## KR

Verify the canonical current KR market/message path at valid session semantics.

Do not add a Windows Kiwoom gateway.

If an existing configured provider is unavailable, use only its already-defined partial/omission/fail-closed behavior. Do not invent a replacement source.

M12CJ's market PASS is historical evidence. M12CM must report its own current source observations; it does not need to redesign the passed market architecture.

---

# 12. Complete monitored-stock smoke PASS criteria

For every current monitored subject require:

```text
Core accepted
Stage-2 raw v4 accepted
supporting_claim_refs non-empty for every maturity row
runtime materialization PASS
semantic ownership/identity/ref/numeric contracts PASS
accepted plan READY
accepted artifact valid
native readback PASS
render/message quality PASS
capture sink reached when applicable
```

For expected 22-subject population, required denominator:

```text
Core 22/22
Stage-2 raw v4 22/22
materialized/semantic 22/22
finalized 22/22
native readback 22/22
message/capture 22/22
8/8 Stage-2 batches complete
```

Do not count base-AI fallback, invalid-v2 suppression, or a raw candidate as an accepted-v2 success.

A legitimate current investment decision may differ from historical M12CH or M12CJ.

---

# 13. Seal AI outputs — do not expose verdicts

After successful/partial model execution, place all model/decision material into:

`sealed-ai-verdicts.zip`

Include:

- raw Core and Stage-2 outputs;
- normalized candidates;
- accepted plans/artifacts;
- full AI monitored-stock rendered messages;
- model prompts/schemas/call metadata needed for later audit.

Record only the sealed archive SHA-256 and structural counts in top-level output.

Top-level `REPORT.md`, blocker ledger and `human-review/` must not reveal:

- per-ticker decision labels;
- new-buyer/holder labels;
- directional balance;
- verdict distribution;
- text snippets that disclose the verdict.

A structural failure report may identify the ticker and exact contract field/gate only as needed to diagnose a hard failure, without exposing unrelated verdict content.

Run a leakage scan across all unsealed report surfaces.

Do not unseal M12CJ's historical sealed archive and do not compare it to the new AI decisions in M12CM.

---

# 14. Required regressions

Before/after formal execution as appropriate, run:

- Stage-2 v4 schema/prompt tests;
- v3 historical compatibility tests;
- supporting-claim empty rejection;
- M12CK source-ref deterministic projection;
- symbolic/mixed/concrete provenance;
- frozen-Core numeric and independent-Core binding;
- entry/holder and pre/post-confirmation;
- accepted-v2 finalization/readback;
- KRX night history/session/near-month/same-contract DWM/renderer;
- US full market/Treasury;
- actual KR market/message tests used by current path;
- native capture-sink delivery regressions;
- blind-review redaction/sealing tests.

Run full pytest, Ruff and `git diff --check`.

No application/runtime/config source edits are authorized in M12CM.

Expected application/runtime/config diff count from the M12CL base: **0**.

Any actual runtime repair need returns to Chat.

---

# 15. Required result artifacts

At minimum:

1. `REPORT.md` — structural outcome only, no AI verdict labels.
2. `source-base-runtime-integrity.json`.
3. `m12cl-v4-preflight.json`.
4. `execution-session-resolution.json`.
5. `monitored-population-snapshot.json`.
6. `provider-call-ledger-redacted.json`.
7. `current-us-market-smoke.json` and rendered capture.
8. `current-kr-market-smoke.json` and rendered capture.
9. `krx-night-kospi200-historical-acceptance-regression.json` and necessary KRX receipts.
10. `human-review/` facts-only files.
11. `human-review-freeze-manifest.json`.
12. `model-call-ledger-structural.json`.
13. `stage2-v4-structural-matrix.json` with no verdict labels.
14. `monitored-stock-smoke-structural-matrix.json`.
15. complete failure evidence if first-hard-failure occurs.
16. accepted/readback/capture structural identity records.
17. `sealed-ai-verdicts.zip` and SHA/manifest.
18. `blind-review-separation-audit.json`.
19. capture-sink/state/intent structural traces.
20. test JUnit/logs, Ruff and diff-check outputs.
21. `safety-counters.json`.
22. `completion-layer-ledger.json`.
23. `complete-blocker-ledger.json`.
24. `artifact-manifest.json` with manifest self-exclusion.

No credentials.

---

# 16. Completion layers and terminal outcomes

Keep distinct:

1. `m12cl_v4_offline_contract` — carried PASS, not relabeled as fresh proof;
2. `current_market_source_and_message_smoke`;
3. `fresh_current_monitored_stock_v4_smoke`;
4. `blind_human_review_ready`;
5. `human_ai_comparison` — NOT_PERFORMED;
6. `deployment_authorization` — NOT_AUTHORIZED.

### PASS

Use:

`M12CM_FRESH_CURRENT_V4_SMOKE_PASS_READY_FOR_BLIND_HUMAN_REVIEW`

only when:

- current market smoke is valid under real session/source semantics;
- KRX night-futures historical acceptance control has no unexplained mismatch;
- fresh canonical monitored population completes the formal v4 stream;
- zero maturity rows have empty supporting claims;
- accepted/readback/capture completes for the entire required population;
- facts-only packet was frozen before model inference and unchanged afterward;
- AI output is sealed with no unsealed verdict leakage;
- runtime/app/config changes are zero;
- production actions are zero.

### Model/contract hard failure

Use:

`M12CM_FRESH_CURRENT_V4_SMOKE_NOT_CLOSED`

with the exact first hard boundary. Preserve current generation and do not repair/retry.

### Current-source dependency

Use:

`M12CM_CURRENT_SOURCE_DEPENDENCY`

only for an existing canonical source/config dependency that prevents required current smoke semantics. Do not add a provider.

### Unexpected runtime drift

Use:

`M12CM_UNEXPECTED_RUNTIME_DRIFT`

if the runtime/application/config base differs materially from M12CL before formal execution.

### KRX mismatch

Use:

`M12CM_KRX_NIGHT_ACCEPTANCE_MISMATCH`

for a truly unexplained comparable same-economic-session KRX/Kiwoom mismatch.

No terminal result authorizes deployment.

---

# 17. Return boundary and next step

Return the result ZIP and `.sha256` to Chat.

Even after PASS:

- do not open `sealed-ai-verdicts.zip` in the result report;
- do not merge main;
- do not deploy;
- do not resume scheduler;
- do not send production notifications.

Next sequence after a genuine M12CM PASS:

```text
Chat independently verifies structural PASS
→ Chat opens/presents only human-review facts
→ user records independent market and monitored-stock judgments
→ only then Chat opens sealed-ai-verdicts.zip
→ compare human vs AI reasoning/decisions
→ diagnose meaningful disagreements
→ separate deployment / scheduler / real-send decision
```

The user, not the model, makes the investment decisions.
