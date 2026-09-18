# Thesis Monitor — M12CW-R1 Pass-B Preflight Directory Ownership Repair & Fresh-Pass-A Resume

## 0. Task identity

Work-instruction filename:

`20260918-m12cw-r1-pass-b-preflight-directory-ownership-repair-and-fresh-pass-a-resume.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cw-r1-pass-b-preflight-directory-ownership-repair-and-fresh-pass-a-resume-report.zip`

This is a **bounded external execution-harness repair + Pass-B-only resume from the already fresh accepted M12CW Pass A**.

It is NOT:

- another Pass-A run;
- a new investment-policy design;
- a capability-policy redesign;
- a prompt/schema retune;
- a continuation after a Pass-B model failure;
- a production integration/deployment task;
- a market/fundamental refresh.

Pass-A external model calls: **0**.

Pass-B external model calls: **8 maximum**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

### M12CW result

Verify:

- ZIP SHA-256:
  `0452cd7b8d31ed095b502d5524d1a502616a11eee8d53fd27ea3d31d7a216e90`
- Artifact manifest:
  338 declared payloads, 338/338 hash and size PASS.
- Source base:
  `0691560bb20b430c15e3c0862de679ce3c023b60`
- Implementation:
  `b63726d9c1a97886a842a304a433a5fb55166288`
- Generation:
  `20260918-m12cs-fresh-two-pass-20260918T040023Z-b63726d9c1a9`
- Submitted terminal:
  `M12CW_PASS_B_FAILED`

### Repository

Repository head must remain exactly:

`b63726d9c1a97886a842a304a433a5fb55166288`

Working tree must be clean before the harness proof begins.

No repository source/code/config changes are authorized.

If repository head/tree differs:

`M12CW_R1_FROZEN_IMPLEMENTATION_DRIFT`

## 2. Fresh Pass-A fixture binding

M12CW completed a fresh Pass A.

M12CW-R1 is explicitly authorized to reuse it.

Required:

- calls: 8/8 PASS
- subjects: 22/22 PASS
- price leak: 0
- technical leak: 0
- target-label leak: 0

Exact SHA-256 bindings:

### Pass-A classification

`fresh-pass-a-22-classification.json`

SHA-256:

`c3b6537ecd75e2fc4fee685f2390275316bc14aea2f03ed045273199a1be58be`

### Pass-A freeze manifest

`pass-a-output-freeze-manifest.json`

file SHA-256:

`44d82ba1ba774ef5725e461ff41ffeb2c8bb7ba6941bcf1d5b61ea82de97c7ea`

The freeze manifest's aggregate SHA must also be:

`c3b6537ecd75e2fc4fee685f2390275316bc14aea2f03ed045273199a1be58be`

### Fresh deterministic upstream

Fundamental materialization:

`1dc87de7336e90a50b8748d10693484c46a9357b910ba2738ad4db9d319e1737`

Business-quality runtime:

`c111b63410fc734935760a25b8432cc03920c051930b95bba8c74a9fd72cac60`

Security-valuation-basis runtime:

`db583a58be65f1396b556dbb23a3a555c931c0c3296fd591402979e3e2156716`

Fresh Pass-B capability catalog:

`d9c011ce46da40217461e4bda55d6e8f698271217b75aa040468c71abc76f568`

Fresh Pass-B context binding:

`82cffc4dbfe88878caa73992058af9e74c127cc39358bfcb6f1150fc3252ca10`

All-16 outbound provider-request binding:

`fea19e1cdea9307d5476029488f13ea6017e7bf4d1f47311b9fdd984b8514a57`

If any fixture hash mismatches:

- external model calls = 0;
- stop:
  `M12CW_R1_FRESH_PASS_A_FIXTURE_BINDING_FAILED`

Do not regenerate A to repair a fixture mismatch.

## 3. No historical target reuse

Allowed model-output reuse:

- only the accepted M12CW fresh Pass-A fixture.

Forbidden pre-freeze semantic use:

- M12CV Pass-B judgments;
- M12CU Pass-B judgments;
- M12CM production AI verdicts;
- independent assistant judgments;
- prior three-way comparison;
- sealed post-freeze comparison archive.

M12CW contains no valid Pass-B model output and therefore contributes no B target.

Target-label leak count must remain 0.

## 4. Exact harness failure reproduction

Before changing the external orchestration path, reproduce the M12CW failure offline.

The archived traceback is:

```text
m12cw_execute.py::invoke_pass_b_capability
  -> m12cv._build_preflight(result_root, inputs)
  -> shutil.copytree(base, dry)
  -> FileExistsError
```

Exact destination:

`outbound-request-dry-serialization/pass-b/us/batch-01`

Required reproduction:

1. use a scratch result tree;
2. create/freeze the normal top-level Pass-B dry serialization;
3. invoke the old Pass-B preflight path;
4. observe the same `FileExistsError`.

Required artifact:

`m12cw-pass-b-preflight-directory-collision-reproducer.json`

Do not modify the original M12CW artifact tree.

## 5. Ownership rule for frozen result directories

Adopt this shadow-execution invariant:

**Once a preflight artifact subtree is frozen into the result root, later execution stages may read/verify it but may not recreate, overwrite, merge, or delete it.**

Classify result-tree subpaths by owner:

- top-level preflight owner;
- Pass-A live owner;
- Pass-A freeze owner;
- deterministic materialization owner;
- Pass-B capability/preflight owner;
- Pass-B live owner;
- final freeze owner.

Create:

`result-tree-directory-ownership-contract.json`

Every path must have one writer.

No two stages may independently own the same frozen path.

## 6. Bounded harness repair

The repair must be **external execution harness only**.

Expected repository application/runtime/config source changes: 0.

Preferred repair:

### Option A — consume verified preflight receipt

Pass-B live execution receives the already-built/frozen:
- capability catalogs;
- prompts/contexts;
- provider-wire schemas;
- outbound request-binding receipts.

It verifies them and proceeds without calling the preflight builder again.

### Option B — isolated reproof

If the live wrapper contract requires a newly built preflight object:

1. create a unique scratch/temp root not under the frozen result evidence subtree;
2. run the preflight builder there;
3. compare every resulting hash against the frozen M12CW preflight;
4. require exact equality;
5. delete/discard the scratch copy;
6. live B execution consumes the original frozen request inputs.

Do not use:

`dirs_exist_ok=True`

to merge into the frozen evidence directory.

Do not delete the original preflight directory.

Do not overwrite frozen evidence.

## 7. Harness repair must be semantics-neutral

The repair may change only filesystem/orchestration mechanics.

It must not change:

- Pass-A result;
- deterministic materialization;
- capability catalogs;
- Pass-B prompt text;
- Pass-B internal schema;
- Pass-B provider-wire schema;
- ref catalogs;
- subject context;
- model;
- reasoning effort;
- validation rules;
- directional-balance semantics;
- entry-range policy.

Recompute no-model Pass-B live-request inputs and require exact hashes against the frozen M12CW preflight artifacts.

Required:

`PASS_B_ANALYTICAL_INPUT_DRIFT_COUNT = 0`

If any analytical/request hash differs:

`M12CW_R1_PASS_B_ANALYTICAL_INPUT_DRIFT`

and external model calls remain 0.

## 8. External orchestrator provenance

The failed M12CW external orchestrator receipt reports:

- path:
  `/Users/sskim/Documents/Codex/2026-07-04/the/m12cw_execute.py`
- SHA-256:
  `d1ef006f48fa9d361c3092b43e8c81ca00f077b212535333a5d70f1b76e5e299`
- repository source edit count: 0

Preserve this as the failed harness baseline.

Create a new bounded orchestrator, preferably a new filename such as:

`m12cw_r1_execute.py`

rather than overwriting historical evidence.

Record:
- old harness SHA;
- new harness SHA;
- exact diff classification;
- repository edit count;
- semantic/request hash drift count.

Required:

`repository_source_edit_count = 0`

## 9. Pre-live regression controls

Before any Pass-B provider request:

1. old collision reproducer: PASS;
2. repaired harness with already-existing frozen preflight subtree: PASS;
3. repeated no-network invocation does not alter frozen evidence hashes;
4. preflight builder is not called against the frozen result path by the live B path;
5. Pass-B analytical input drift: 0;
6. capability catalogs: 22/22;
7. capability/validator parity: PASS;
8. Pass-B provider schema dialect scan: 8/8 PASS;
9. outbound request binding: 8/8 exact;
10. single-scalar balance fixtures: PASS;
11. target leak: 0;
12. sealed reference open count: 0;
13. repo head exact/clean.

If any fails, model calls = 0.

## 10. Resumed analytical generation identity

Create a new execution generation ID with explicit provenance:

- mode:
  `PASS_B_RESUME_FROM_FRESH_M12CW_PASS_A_AFTER_HARNESS_REPAIR`
- upstream analytical generation:
  `20260918-m12cs-fresh-two-pass-20260918T040023Z-b63726d9c1a9`
- upstream Pass-A aggregate SHA:
  `c3b6537ecd75e2fc4fee685f2390275316bc14aea2f03ed045273199a1be58be`
- implementation commit:
  `b63726d9c1a97886a842a304a433a5fb55166288`
- new external harness SHA.

This is not same-generation hotfixing.

The old M12CW artifact remains immutable.

## 11. Pass-B live topology

Pass-A calls: 0.

Pass-B maximum calls: 8.

Run from B batch 1:

### US
1. CORZ / CPNG / CRCL
2. GOOGL / HUT / IBM
3. MU / RXRX / SKHY
4. SNDK / TSLA / TSM
5. WRD / WULF

### KR
6. 000660 / 003690 / 005490
7. 005930 / 010120 / 012450
8. 047810 / 086280

Hard:
- one attempt;
- retry 0;
- repair 0;
- fallback 0;
- judge 0;
- selective rerun 0;
- per-ticker rerun 0;
- post-call prompt/schema/capability hotfix 0.

First hard B failure stops remaining calls.

Do not rerun A.

## 12. Raw/final validation order

For every B call preserve:

1. persist raw response;
2. raw provider-contract validation;
3. raw semantic/capability validation;
4. persist exact rule IDs;
5. stop immediately on failure;
6. normalize;
7. deterministic directional balance:
   `sell = 10 - directional_buy_score`;
8. deterministic tactical/entry materialization;
9. final semantic/policy/cross-ref validation.

No downstream envelope error may mask the primary cause.

## 13. B PASS requirements

Require:

- 8/8 provider-completed Pass-B responses;
- 8/8 raw contract PASS;
- 8/8 raw semantic PASS;
- 22/22 subject rows normalized;
- 22/22 final semantic PASS;
- model-authored sell = 0;
- PB_BALANCE_SUM = 22/22;
- New Buyer consistency = 22/22;
- Overall/Holder policy validation = 22/22;
- runtime entry materialization = 22/22;
- deterministic impossible branch exposure = 0;
- target leak = 0.

## 14. Combined resumed fresh result

If Pass B closes, combine only:

1. frozen fresh M12CW Pass A;
2. exact fresh M12CW deterministic materialization/capability state;
3. new M12CW-R1 Pass B.

Create:

`combined-resumed-fresh-22-subject-results.json`

The artifact must explicitly record that:

- Pass A came from the fresh M12CW generation;
- Pass B came from the harness-repaired resume generation;
- analytical repository implementation commit was identical;
- only external harness filesystem mechanics changed between stages;
- analytical input drift count = 0.

Do not label this as an uninterrupted same-process generation.

Use terminal:

`M12CW_R1_RESUMED_FRESH_E2E_PASS_READY_FOR_CHAT_INTEGRATION_REVIEW`

only if all analytical gates pass.

## 15. Final freeze

Freeze:

- upstream Pass-A fixture hashes;
- new B raw outputs;
- new B normalized/final rows;
- combined 22-subject result;
- runtime entry ranges;
- capability receipt;
- harness provenance.

No sealed historical comparison access before this freeze.

## 16. Pre-reveal analysis

Before historical reveal, summarize only the combined fresh analytical result:

- archetype distribution;
- valuation-regime distribution;
- Overall distribution;
- New Buyer distribution;
- Holder distribution;
- directional scores;
- BUY / WAIT / HOLDABLE count;
- Holder REVIEW/REDUCE counts/reasons;
- fundamental resolved/unresolved;
- WAIT resolved-price count;
- WAIT unresolved count;
- resolved entry ranges;
- security-basis-unresolved outcomes;
- execution-dependent-growth outcomes.

For every WAIT with a resolved range include:
- current price/as-of;
- method/tier;
- fundamental low/high;
- preferred low/high if resolved;
- distance;
- tactical context;
- canonical refs.

## 17. One post-freeze comparison

Only after combined final freeze:

open the sealed post-freeze reference archive exactly once.

Compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. combined M12CW/M12CW-R1 resumed fresh result.

Report:
- exact three-axis agreement;
- Overall agreement;
- New Buyer agreement;
- Holder agreement;
- label distributions;
- BUY/WAIT/HOLDABLE frequency;
- Holder REVIEW frequency;
- resolved WAIT price coverage;
- remaining unresolved coverage;
- major interpretive differences for durable/core, cyclicals, execution-growth and security-basis-unresolved cases.

Do not treat prior judgments as ground truth.

After reveal:
- model calls 0;
- policy edits 0;
- prompt/schema edits 0;
- threshold tuning 0.

## 18. Postrun validation

Run:

- focused shadow-contract suite;
- frozen-contract suite;
- full pytest suite;
- Treasury/KRX;
- scoped Ruff check;
- scoped Ruff format check;
- git diff --check.

Formatting gate:

- repository Python files changed by M12CV implementation;
- frozen shadow/test Python execution surface;
- any external harness Python file separately with its own Ruff check/format if practical.

Repo-wide pre-existing format debt remains informational only.

No mass-formatting.

No test deletion or skip inflation.

## 19. Final readiness boundary

Even if:

`M12CW_R1_RESUMED_FRESH_E2E_PASS_READY_FOR_CHAT_INTEGRATION_REVIEW`

production remains unchanged.

No:
- production Stage-2 integration;
- scheduler enablement;
- production send;
- DB mutation;
- broker action;
- merge;
- push;
- deployment.

Return to Chat.

Chat will decide whether:
- the resumed fresh analytical proof is sufficient for production-integration design;
- one uninterrupted final A+B proof is still warranted;
- additional calibration is required.

## 20. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cw-chat-review-reconciliation.json`
- `fresh-pass-a-fixture-binding.json`
- `m12cw-pass-b-preflight-directory-collision-reproducer.json`
- `result-tree-directory-ownership-contract.json`
- `external-harness-repair-diff.json`
- old/new external orchestrator receipts/hashes
- `pass-b-analytical-input-drift-proof.json`
- `pass-b-preflight-idempotency-proof.json`
- capability catalog 22 binding
- provider dialect scan 8
- outbound request binding 8
- resumed-generation provenance manifest
- all 8 B inputs/prompts/schemas/contexts/ref catalogs
- all 8 raw outputs/transport logs where executed
- B raw semantic validation artifacts
- Pass-B call ledger
- directional-balance runtime 22
- entry-range materialization 22
- New Buyer consistency 22
- Overall/Holder policy validation
- combined resumed fresh 22 results
- combined final freeze manifest
- pre-reveal analysis
- post-freeze three-way comparison JSON/MD
- validation logs/JUnit
- scoped formatting evidence
- safety counters
- blocker ledger
- program completion
- REPORT.md
- artifact manifest
- external ZIP SHA sidecar.

## 21. Terminal states

Use one:

- `M12CW_R1_RESUMED_FRESH_E2E_PASS_READY_FOR_CHAT_INTEGRATION_REVIEW`
- `M12CW_R1_FROZEN_IMPLEMENTATION_DRIFT`
- `M12CW_R1_FRESH_PASS_A_FIXTURE_BINDING_FAILED`
- `M12CW_R1_HARNESS_DIRECTORY_OWNERSHIP_REPAIR_FAILED`
- `M12CW_R1_PASS_B_ANALYTICAL_INPUT_DRIFT`
- `M12CW_R1_PASS_B_PREFLIGHT_FAILED`
- `M12CW_R1_PASS_B_FAILED`
- `M12CW_R1_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CW_R1_POSTRUN_VALIDATION_FAILED`
- `M12CW_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration.

## 22. Hard safety

- Pass-A external model calls = 0
- Pass-B external model calls <= 8
- Fundamental Core model calls = 0
- market refresh = 0
- production runtime/config changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0.
