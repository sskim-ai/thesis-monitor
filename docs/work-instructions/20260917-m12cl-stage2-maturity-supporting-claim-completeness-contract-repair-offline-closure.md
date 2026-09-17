# Thesis Monitor — M12CL Stage-2 Maturity Supporting-Claim Completeness Contract Repair + Offline Closure

## 0. Task identity and bounded authorization

This task follows M12CK. M12CK successfully closed the deterministic source-evidence-ref ownership problem but correctly stopped on a second, independent defect: the raw model output may still emit a `driver_maturity` row with an empty `supporting_claim_refs` list even though the existing hard semantic contract requires at least one supporting atomic claim identity.

This M12CL task is a **bounded model-facing Stage-2 contract-completeness repair + offline reproof**.

It is NOT:

- a new current-market smoke;
- a retry or continuation of M12CJ;
- a new Full22 model generation;
- a repair-model/judge/fallback task;
- an inference of missing WRD/WULF claim identities;
- a Fundamental Core redesign;
- an atomic-claim catalog expansion task;
- a BUY/HOLD/SELL or new-buyer/holder redesign;
- a KRX/Kiwoom/market-provider task;
- a provenance-date/source-ref ownership redesign;
- a finalization/numeric/delivery redesign;
- a deployment task.

External model calls: **0**. Market/provider reads: **0**. Production sends/intents/DB mutations: **0**. Broker order/modify/cancel: **0/0/0**. Scheduler/main/deploy/remote-push changes: **0**.

Return to Chat after offline proof. Do not start a fresh smoke in this task even if every test passes.

---

## 1. Authoritative sources and exact entry state

Authority order:

1. this M12CL instruction;
2. exact current local repository state matching the M12CK report head and changed-source hashes;
3. M12CK result bundle;
4. M12CJ result bundle;
5. M12CH successful fresh Full22 result;
6. older artifacts only as historical context.

Packaged source bundles:

| Source | ZIP SHA-256 | Role |
|---|---|---|
| M12CK result | `be2e94364d27513122d4a6cfd9fe016bf543a8a2d143bf5a20560a04c6e3c712` | exact v3 source-ref ownership repair and remaining blocker |
| M12CJ result | `b700f8db4ac8e382b560513575ee5fb9dae68cb302a5e1b129a4df7bd2786754` | immutable current-smoke failure and sealed batch-5 evidence |
| M12CH result | `84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e` | successful no-repair 22/22 baseline |

M12CK repository observations:

- required runtime base entering M12CK: `1e0d81695ce0982827a35a58b5123dfb86e066cc`;
- M12CK local base: `49bf44b3dd4c801a6f5aea494eeb76db53048db8`;
- M12CK work-instruction commit: `8b6e5dbddaa3ea6f54773f10e60de5f9f888b6fa`;
- M12CK report-generation HEAD: `edb2debb43e3dcc4e59baa26fc57db4cc381d585`;
- changed application owners and hashes are authoritative from M12CK `changed-source-hashes.json`.

Use an isolated clean worktree from the exact local M12CK state. Verify ancestry and the three application-source hashes before changes. Do not fetch/merge/push merely to reconcile labels. If current local source does not match the result evidence, return `M12CL_SOURCE_OR_BASE_MISMATCH` before application changes.

Run and record source ZIP SHA/CRC/path/manifest verification first. Historical results remain immutable.

---

## 2. Carry forward what is already closed

### 2.1 M12CK source-ref projection repair

Freeze as closed at its demonstrated scope:

- ownership classification: `DETERMINISTIC_SOURCE_REF_PROJECTION`;
- 128/128 successful M12CH maturity sides matched selected claim → canonical parent-source projection;
- raw Stage-2 v3 no longer exposes `supporting_evidence_refs` or `contradicting_evidence_refs` to the model;
- source refs are runtime-owned and projected in selected-claim order / canonical parent order with first-occurrence de-duplication;
- `as_of` and `provenance_status` remain runtime-owned;
- independent hard source-ref/atomic-identity validator remains authoritative;
- M12CH 22/22 normalized candidate / accepted artifact / renderer parity passed;
- R01–R16 passed.

Do not restore model-authored source refs and do not reinterpret v3 historical outputs as v4.

### 2.2 Market / KRX / blind separation

Carry M12CJ current-market and KRX NIGHT/Kiwoom findings unchanged. M12CL performs no market reads.

Keep M12CJ `sealed-ai-verdicts.zip` unchanged with SHA-256:

`562743b20737242624f0968d2128c026124c3db1b8989344785c1319f6bbd951`

Do not publish or summarize per-subject BUY/HOLD/SELL, new-buyer, holder, balance, accepted-plan, or recommendation fields. Human/AI comparison remains `NOT_PERFORMED`.

---

## 3. Exact remaining blocker

M12CK terminal result:

`M12CK_OFFLINE_REPAIR_FAILED`

because M12CJ batch 5 `driver_maturity` row 1 for both `WRD` and `WULF` contains:

```text
supporting_claim_refs = []
```

The v3 runtime therefore fails before source-ref projection with:

```text
stage2_materialization_supporting_claim_identity_missing:WRD:1
stage2_materialization_supporting_claim_identity_missing:WULF:1
```

The old M12CJ outputs remain frozen negative fixtures and must never be post-hoc repaired or relabeled PASS.

M12CK correctly states that runtime source-ref projection cannot invent a missing model-owned atomic claim identity.

---

## 4. Mandatory pre-change completeness audit

Before changing schema or prompt, verify the existing contract from code, successful outputs, schema, prompt, and hard validators.

Classify the remaining issue as exactly one of:

- `MODEL_SCHEMA_UNDERCONSTRAINED_RELATIVE_TO_EXISTING_ATOMIC_IDENTITY_CONTRACT`;
- `SUPPORTLESS_MATURITY_ROW_IS_VALID_AND_HARD_VALIDATOR_IS_WRONG`;
- `ATOMIC_CATALOG_INSUFFICIENT_FOR_REQUIRED_DRIVER_SEMANTICS`;
- `HARNESS_OR_CONTEXT_MISMATCH`;
- `UNRESOLVED_SUPPORTING_CLAIM_COMPLETENESS`.

Do not preselect the first classification without measuring the following.

### 4.1 Successful M12CH denominator

Recount every `driver_maturity` row in the immutable M12CH Full22 output and record:

- total maturity rows;
- count/distribution of `supporting_claim_refs` cardinality;
- count/distribution of `contradicting_claim_refs` cardinality;
- any valid row with zero supporting claim refs;
- whether the hard validator ever accepts zero supporting claim refs.

Chat's independent structural recount found:

- 64 maturity rows;
- empty supporting claim list: 0/64;
- supporting cardinality: 41×1, 22×2, 1×3;
- empty contradicting claim list: 15/64.

Reproduce from packaged bytes rather than blindly copying these values.

### 4.2 Frozen M12CJ schema mismatch

Inspect the exact M12CJ batch-5 model-facing schema.

Expected observation to verify:

- `supporting_claim_refs` is required but has no `minItems`;
- `contradicting_claim_refs` is required but may be empty;
- the old `supporting_evidence_refs` field had `minItems=1`;
- the hard semantic validator/materializer rejects empty supporting atomic identity.

If this differs materially, stop and classify the actual owner.

### 4.3 Structural batch-5 relation only

Use the minimum redacted fields required to classify completeness. Do not export verdicts.

Verify:

- WRD's old supporting source ref is the parent of an existing WRD atomic claim, but the raw output omitted that claim ref;
- WULF's old supporting source refs are not parent refs of any WULF atomic claim in the frozen maturity atomic catalog;
- therefore source-ref reverse mapping cannot generally recover a missing claim identity.

This is evidence **against** auto-inference, not an instruction to reveal or rewrite the sealed candidate.

Required artifact:

`supporting-claim-completeness-audit.json`.

If the audit proves that a valid `driver_maturity` row may legitimately have no supporting atomic claim, STOP before repair and return the exact semantic design dependency. Do not weaken the hard validator just to admit M12CJ.

---

## 5. Conditional repair — v4 raw model contract

Only if section 4 proves `MODEL_SCHEMA_UNDERCONSTRAINED_RELATIVE_TO_EXISTING_ATOMIC_IDENTITY_CONTRACT`, implement the following.

### 5.1 Versioning

M12CK introduced raw model contract:

`v2-accepted-stage2-model-output-v3`

Do not silently change that historical version's schema semantics. Introduce the next explicit model-facing raw contract version, suggested:

`v2-accepted-stage2-model-output-v4`

Legacy v2/v3 inputs remain distinguishable historical/offline inputs. The current model-facing builder uses v4 after this repair.

No normalized accepted-candidate schema/version change is required solely for this raw completeness constraint.

### 5.2 Supporting atomic claim is mandatory

For every v4 `driver_maturity` row:

```text
supporting_claim_refs: array of exact supplied maturity claim refs
minItems = 1
maxItems = existing bound
```

Keep:

```text
contradicting_claim_refs
```

allowed to be empty. Do **not** add `minItems=1` to contradicting claims; valid M12CH rows demonstrate that contradiction is optional.

Preserve batch/ticker claim enums and every existing cross-ticker/unknown/disjointness/polarity/eligibility hard check.

### 5.3 Prompt semantics

State explicitly:

- every emitted maturity driver must be grounded in at least one exact same-ticker atomic claim from `MATURITY_ATOMIC_CLAIM_CATALOG`;
- if no supplied atomic claim supports the proposed driver, **do not emit that driver**; choose a driver that is actually represented by the supplied atomic claims;
- do not create, infer, approximate, shorten, or repair a claim ref;
- source evidence refs are runtime-owned and cannot substitute for missing atomic claim identity;
- contradicting claim refs may be empty when there is no canonical contradicting atomic claim;
- supporting/contradicting remains relative to the driver and is not identical to absolute BULLISH/BEARISH polarity.

Do not add WRD/WULF names, exact claim refs, exact text, historical target decisions, or any ticker-specific branch to production prompt/schema.

### 5.4 No post-hoc fill

Forbidden:

- reverse-map old source refs to claim refs;
- choose the nearest claim by text similarity;
- promote arbitrary `stock.thesis.strengthen_signals` rows into the atomic catalog;
- populate an empty list from buy/sell drivers after model output;
- catch the hard error and pick the first allowed claim;
- repair model calls, retries, selective per-ticker reruns, or historical output edits.

The frozen WRD/WULF M12CJ outputs must continue to fail as historical v2 negatives.

### 5.5 Defense in depth

Keep the existing materializer/hard-validator empty-support rejection even though v4 structured output should prevent it upstream. Schema-level prevention and runtime fail-closed validation are both required.

Expected application/model-contract footprint should stay within existing Stage-2 schema/prompt/version/materializer owners. If a new application owner beyond the current M12CK owner set is necessary, identify the exact call dependency and STOP for Chat before broadening.

---

## 6. Required tests and exact cases

Define actual node IDs/variants before implementation. Minimum obligations:

| ID | Case | Required result |
|---|---|---|
| C01 | Immutable M12CJ WRD historical v2 output | remains frozen negative; no auto-fill |
| C02 | Immutable M12CJ WULF historical v2 output | remains frozen negative; no auto-fill |
| C03 | v4 model schema `supporting_claim_refs=[]` | rejected by model-facing/raw contract; not deferred as a normal valid shape |
| C04 | v4 row with exactly one valid same-ticker supporting claim | accepted, source refs deterministically projected |
| C05 | v4 row with 2–3 valid supporting claims | accepted; projection order/de-dup unchanged |
| C06 | valid v4 row with empty contradicting claims | accepted where all other semantics valid |
| C07 | model-authored supporting/contradicting evidence refs | existing v3+ raw-ingress rejection preserved |
| C08 | unknown or cross-ticker supporting claim | hard rejection |
| C09 | same claim on supporting and contradicting sides | existing disjointness rejection |
| C10 | old WULF source-only support signals | no source→claim inference / no atomic-catalog promotion |
| C11 | old WRD source ref that happens to have an atomic parent | historical output still not post-hoc completed |
| C12 | M12CH 64 maturity rows under v4 schema projection | 64/64 have >=1 supporting claim; semantic parity |
| C13 | M12CJ 12 historically valid subjects under v4-compatible offline projection | 12/12 semantic parity; WRD/WULF remain historical negatives |
| C14 | M12CK deterministic source-ref projection | unchanged |
| C15 | symbolic/mixed/concrete provenance | unchanged |
| C16 | finalization numeric ownership, entry/holder, frozen-Core binding | no regression |
| C17 | raw model authors `as_of`/`provenance_status` | existing rejection preserved |
| C18 | prompt/schema contain no ticker-specific target examples and no repair-model dependency | PASS |

An unrelated exception is not a successful negative assertion. Record expected class/code/boundary and actual observed result separately.

---

## 7. Offline reproof and honest interpretation

### 7.1 M12CH successful baseline

Using immutable M12CH raw/Core/context data with **zero model calls**:

- verify all 22 subjects remain representable under the v4 model-facing contract after removing only runtime-owned fields;
- 64/64 maturity rows satisfy supporting-claim nonempty constraint;
- normalized candidates remain semantically identical;
- final accepted artifacts/renderers remain identical where replayed with equivalent inputs/clocks;
- source-ref projection, provenance status/date, numeric finalization and independent-Core binding remain unchanged.

Do not relabel this replay as a new Full22.

### 7.2 M12CJ frozen current generation

Keep historical M12CJ frozen:

- 12/14 historically valid subjects remain valid in compatible offline projection;
- WRD/WULF remain historical negative fixtures because their raw model-owned supporting claim selection is missing;
- do **not** invent claim refs to make 14/14 offline.

The purpose of M12CL is to prove that **future v4 structured outputs cannot legally omit supporting claim identity**, not to rewrite the bad v2 generation.

### 7.3 Fresh proof boundary

If M12CL passes, the next required evidence is a separately authorized **new current monitored-stock smoke from call 1** using v4. Do not perform it here.

A PASS therefore means:

`OFFLINE_CONTRACT_CLOSED_FRESH_CURRENT_SMOKE_REQUIRED`

not production readiness.

---

## 8. Blind separation

Keep the M12CJ sealed archive byte-identical. M12CL may inspect/export only structural maturity relation evidence necessary for this contract repair.

Prohibited top-level/output fields include per-subject:

- overall BUY/HOLD/SELL;
- new-buyer decision;
- holder decision;
- directional balance;
- accepted decision/plan/source/recommendation;
- verdict distribution.

Produce a blind-separation regression showing zero prohibited-field leaks. Human/AI comparison remains `NOT_PERFORMED`.

---

## 9. Validation and regression suites

After repair run:

1. focused Stage-2/model-contract/atomic-identity tests;
2. full repository tests;
3. Treasury frozen regressions;
4. KRX/Kiwoom frozen regressions;
5. Ruff;
6. `git diff --check`.

Latest M12CK bundled baselines:

- focused: 252 passed / 0 skipped;
- full: 4171 passed / 63 skipped;
- Treasury: 228 passed;
- Kiwoom/KRX: 115 passed.

Explain legitimate new-test count increases. No deleted tests or skip inflation to obtain green status.

No market network read or model call is needed for these regressions.

---

## 10. Required result artifacts

At minimum include:

- `source-base-integrity.json`;
- `m12ck-result-integrity.json`;
- `supporting-claim-completeness-audit.json`;
- `raw-v3-v4-contract-diff.json` and actual compared schema/prompt bytes;
- `model-facing-v4-schema-proof.json`;
- `c01-c18-case-matrix.json` with exact node IDs/variants;
- `m12ch-64-row-v4-parity.json`;
- `m12ch-22-subject-v4-offline-replay.json`;
- `m12cj-12-valid-plus-2-frozen-negative-replay.json`;
- `source-ref-projection-regression.json`;
- `provenance-regression.json`;
- `blind-separation-regression.json`;
- `application-diff.patch`, changed-source hashes and source excerpts;
- JUnit/logs for focused/full/Treasury/KRX-Kiwoom;
- Ruff and diff-check logs;
- `safety-counters.json`;
- `completion-layer-ledger.json`;
- `complete-blocker-ledger.json`;
- `program-completion.json`;
- `REPORT.md`;
- `artifact-manifest.json` with explicit self-exclusion and external ZIP sidecar.

Do not export the full sealed AI candidate merely to prove a schema condition.

---

## 11. Terminal outcomes

Use one of:

### `M12CL_SUPPORTING_CLAIM_COMPLETENESS_OFFLINE_CLOSURE_PASS`

Only if:

- audit confirms the existing hard contract requires >=1 supporting atomic claim for every maturity row;
- v4 model-facing schema enforces `minItems=1` for supporting claims and does not require contradicting claims;
- prompt semantics align with the atomic catalog;
- no auto-inference/post-hoc repair exists;
- M12CH 64-row / 22-subject parity passes;
- M12CJ 12 valid subjects remain unchanged and 2 bad historical outputs remain negative;
- all hard source-ref/provenance/finalization/entry-holder/Core-binding regressions pass;
- blind seal remains intact;
- no model/provider/production activity occurred.

This authorizes only a later Chat decision about a **fresh current smoke**. It does not authorize that smoke automatically.

### `M12CL_ATOMIC_CATALOG_DESIGN_DEPENDENCY`

Use if a valid maturity row is proven to require supporting semantics not representable by at least one canonical atomic claim and cannot safely choose another claim-grounded driver under the current design. Do not broaden the catalog or hard validator in this task.

### `M12CL_SUPPORTING_CLAIM_REPAIR_FAILED`

Use for an executed contract/test failure.

### `M12CL_SOURCE_OR_BASE_MISMATCH`

Use when exact source/runtime identity cannot be established.

No result authorizes merge, deploy, scheduler resume, production delivery, or human/AI unsealing.

---

## 12. Subsequent order after Chat review

If and only if Chat accepts M12CL offline closure:

1. create a **new current US14/KR8 monitored-stock smoke** from call 1 using the frozen v4 contract;
2. no prior-output reuse, stitching, repair-model, fallback-model, judge, selective rerun or per-ticker retry;
3. preserve current-market / KRX results only according to the smoke instruction's freshness rules; do not silently reuse stale market facts;
4. return to Chat;
5. if smoke closes, show facts-only material for independent human judgment before opening sealed AI verdicts;
6. compare human vs AI;
7. make a separate deployment/automation decision.

The previously demonstrated at-least-once crash-window limitation remains visible for deployment review and is not part of M12CL.
