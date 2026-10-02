# Thesis Monitor — R2B-R9-REV31-C1
## Qualified Official Model Launch Context
### Exact REV29 Sealed Source + Exact REV31 Source-Only Archive Reuse
### Provider Calls 0 → Actual Host Qualification → Market/Core/A/B → Exact 24 Messages
### KIS FY1 EPS/fPER Remains Deferred to REV32

**REV31-C1 is a bounded continuation of REV31. Execute only REV31-C1.**

REV31 successfully completed:

- fresh-owner source-only exporter repair;
- source-only cohort projection:
  - stocks 22/22
  - Markets 2/2;
- exact source-only blind archive seal;
- source-only archive sealed before any model call;
- authority parity 22/22;
- full 22-subject visibility PASS;
- provider-native valuation coverage preserved;
- Core/A valuation exclusion PASS;
- B valuation context binding PASS;
- full tests green.

REV31 then stopped **before transmitting any model request** because the model launch-context guard compared:

1. the restricted preparation sandbox context,
against
2. the actually authorized official host launch context.

The only reported safe-environment difference was:

`CODEX_SANDBOX`

The authorized host had official Codex state access; the preparation sandbox did not.

No model request was sent.

The correct repair is not to spoof the marker or weaken the guard.

The correct repair is to **qualify the actual permitted official launch context as its own frozen execution authority**
and require every model launch to occur under that exact qualified context.

---

# 0. REV31 integrity and newest SoT

REV31 report ZIP:

`thesis-monitor-20260930-r2b-r9-rev31-fresh-owner-exporter-report.zip`

SHA-256:

`0c99b1f9bdd6e73752d188b5d96b1bffc32114eac715bb2e334f03eec4dd64bc`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- internal manifest:
  `176/176`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`.

REV31 source-only ZIP:

`r2b-r9-rev31-source-only-review.zip`

SHA-256:

`af3b16102ec4e66d60f2d283efb2aad542ee77da84703a8b5b070cd330b66c19`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- internal manifest:
  `29/29`
- missing/hash/size/extra:
  `0`.

REV31 terminal:

`MARKET_MODEL_FAILURE`

Exact failure:

`HOST_LAUNCH_CONTEXT_DRIFT`

Repository:

- source generation:
  `rev29-live-20260930T042411Z`
- REV31 base:
  `afde504c124f2890c51a3fc8000de29f14a9ee2c`
- REV31 instruction:
  `0711339aec26662c3744852bf5f457bdc211a992`
- REV31 validated implementation:
  `dd2b348ffd734d8de97b128655aba4dc36ba59a5`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.

REV31 validation:

- focused:
  `293 passed`
- full:
  `7106 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- diff:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- changed-file secret scan:
  PASS.

---

# 1. Exact source identity — immutable

Continue from the exact sealed source generation:

`rev29-live-20260930T042411Z`

Whole-source SHA-256:

`0dcc42dd3d237794f8cf4a50aa5a491afa8082b19d273bfca5e38f7f129baa3d`

Source-owner registry SHA-256:

`c995c02c82bf1ed97c599402a70d91c0782ed40c7de8fba85e4f55db178f1cc5`

B valuation-context SHA-256:

`7e1cd3f0acc8d0dc267fb487d8897ef4dcb16c587533a420b273336db9d6f510`

Provider calls in REV31-C1:

`0`

No:
- source refresh;
- valuation refresh;
- event refresh;
- Market refresh;
- price/technical refresh;
- source-generation ID change.

If any source identity differs:

`R2B_R9_REV31_C1_SEALED_SOURCE_IDENTITY_GAP`

Do not fall back to full-fresh.

---

# 2. Exact source-only blind archive — immutable

Reuse byte-identically:

`r2b-r9-rev31-source-only-review.zip`

SHA-256:

`af3b16102ec4e66d60f2d283efb2aad542ee77da84703a8b5b070cd330b66c19`

REV31 proof:

- sealed at:
  `2026-09-30T07:55:45.715939+00:00`
- model calls before seal:
  `0`
- first model call:
  null
- source-only sealed before models:
  true.

Do not recreate or rewrite this ZIP.

Reverify its SHA immediately before the first model call.

---

# 3. Independent blind judgment already frozen externally

An independent source-only judgment has already been performed **outside the execution session** after the REV31
source-only archive was sealed and before any Monitoring AI output existed.

Audit identity:

`rev31-source-only-independent-judgment-freeze.md`

SHA-256:

`e935e4387f4d275466c932f9a03274dee739cfdd0dfc7411f40b755f7142b6c9`

This content must **not** be provided to:
- the model runner;
- Market/Core/A/B prompts;
- result-driven calibration;
- execution-stage decision logic.

REV31-C1 need only record the SHA as an external audit identity.

Do not read or import the judgment content in the execution session.

---

# 4. Exact REV31 runtime-boundary finding

REV31 `runtime-boundary-review.json` established:

- status:
  `BLOCKED_BEFORE_MODEL_TRANSMISSION`
- actual official state access ready:
  `true`
- frozen preparation state access ready:
  `false`
- uid/gid equal:
  `true`
- differing safe-environment names:
  exactly:
  `CODEX_SANDBOX`
- markers spoofed:
  `false`
- frozen receipt rewritten:
  `false`
- model requests sent:
  `0`.

Cause:

> Preparation froze the restricted sandbox context; the authorized host launch has a different CODEX_SANDBOX marker.

This is the authoritative diagnosis.

---

# 5. Security principle — two contexts are allowed, spoofing is not

Formalize two distinct context roles:

## PREPARATION_CONTEXT
The restricted local/sandbox process that:
- verifies source;
- prepares/freeze requests;
- performs deterministic validation.

## OFFICIAL_MODEL_EXECUTION_CONTEXT
The permitted host process that:
- can read the existing official Codex state;
- invokes the official signed-in model runner.

These contexts are not required to have the same `CODEX_SANDBOX` value.

They are required to have an explicitly qualified transition and immutable request/source/code identities.

Do not:
- overwrite `CODEX_SANDBOX`;
- export a fake marker;
- remove the marker;
- modify official state permissions;
- copy official state into the preparation sandbox;
- rewrite the old REV31 host receipt;
- disable host-context checking globally.

---

# 6. QualifiedOfficialModelLaunchContext receipt

Create a typed receipt, repository naming permitting:

`QualifiedOfficialModelLaunchContext`

It must be captured **inside the exact authorized host process that will execute the model call**, before the first
request is sent.

Record only non-secret metadata/hashes:

- contract/version;
- timestamp;
- uid;
- gid;
- cwd path hash;
- HOME path hash;
- CODEX_HOME presence/hash where applicable;
- official state path hash;
- official state read-access readiness;
- no state-write proof;
- safe-environment variable presence/value hashes under the existing safe allowlist;
- `CODEX_SANDBOX` presence/hash;
- network/launch-policy markers required by the official runner;
- executable/launcher identity hash where safely measurable;
- continuation implementation SHA;
- source generation ID;
- whole-source SHA;
- source-only ZIP SHA;
- request-freeze identity;
- prompt/schema identity summary;
- model:
  `gpt-5.6-sol`;
- effort:
  `xhigh`.

No secret values.

No KIS/OpenAI/model credential values.

---

# 7. Actual-context qualification gate

The official execution context qualifies only if:

1. it is reached through the existing approved official model-launch path;
2. it can read the official Codex state required by that launcher;
3. no state permission was modified to obtain access;
4. state DB write calls remain zero;
5. uid/gid are the expected current user identity;
6. frozen source/request/code identities match;
7. no source/provider call occurred;
8. no prompt/schema/model policy mutation occurred after request freeze;
9. no unapproved proxy/certificate override is introduced;
10. the context receipt itself is secret-scanned.

If the actual host cannot satisfy these:

`R2B_R9_REV31_C1_OFFICIAL_HOST_QUALIFICATION_GAP`

No model calls.

---

# 8. Explicit permitted preparation→execution transition

Create:

`launch-context-transition.json`

It must compare:

- REV31 preparation receipt;
- REV31-C1 actual qualified host receipt.

The transition may accept the already-observed:

`CODEX_SANDBOX`

difference **only because the target context itself has independently passed Section 7 qualification**.

All other security-relevant fields under the existing safe-environment comparison must either:
- match; or
- have an explicit, documented, pre-authorized target-context reason.

For the current known case, expected extra difference count:

`0`

beyond `CODEX_SANDBOX`.

If a new unexplained difference appears:

fail closed.

Do not expand an allowlist dynamically from whatever happens to differ.

---

# 9. Freeze the actual execution context

After Section 7/8 PASS, create:

`official-model-execution-context-freeze.json`

This becomes the authority for all model calls in this continuation.

Every actual model invocation must verify its immediate launch context against **this actual-host freeze**, not against
the preparation sandbox receipt.

The preparation receipt remains provenance evidence only.

If context changes after freeze:
- fail before request send;
- do not refresh the freeze automatically.

No per-call adaptive acceptance.

---

# 10. Narrow code boundary

The repair must be limited to:
- launch-context qualification;
- preparation→execution transition validation;
- model-invocation comparison against the qualified actual host freeze.

Do not change:
- source owners;
- source qualification;
- valuation owners;
- authority hash logic;
- fresh-owner exporter;
- Market/Core/A/B prompt text;
- model schemas;
- batching;
- model name/effort;
- sender renderer;
- delivery behavior.

If prompt/schema/request bytes change:
stop.

---

# 11. Request/input identity preservation

REV31 had already prepared/frozen model requests before the host boundary stopped transmission.

REV31-C1 must verify all current request artifacts against REV31 identities.

Require:
- same source generation;
- same subject batches;
- same prompts;
- same provider-wire schemas;
- same internal semantic schemas;
- same subject contexts;
- same model:
  `gpt-5.6-sol`
- same effort:
  `xhigh`
- same 1200-second timeout;
- same maximum logical call plan.

No regenerated request may differ semantically from the REV31 frozen request merely because launch-context code changed.

If request identity differs:
`R2B_R9_REV31_C1_REQUEST_FREEZE_IDENTITY_GAP`

No model calls.

---

# 12. Required launch-context tests

Before live model transmission:

## preparation vs actual
- restricted preparation receipt + independently qualified actual host → transition PASS;
- exact observed `CODEX_SANDBOX` difference → PASS only under qualified target context;
- unqualified host with same marker → fail;
- qualified host with unexpected proxy/cert override → fail;
- uid/gid mismatch → fail;
- source/request hash mismatch → fail.

## spoofing
- manually overriding CODEX_SANDBOX → fail;
- deleting marker to force equality → fail;
- rewriting old frozen receipt → fail.

## state
- actual host state readable through approved path → PASS;
- write attempt/counter nonzero → fail;
- permission mutation → fail.

## stability
- post-freeze context equal → PASS;
- post-freeze marker/env drift → fail before send.

No test may special-case a literal machine marker value.

---

# 13. Validation before model continuation

Require:

- focused launch-context tests PASS;
- REV31 fresh-owner exporter tests PASS;
- source-only exclusion tests PASS;
- authority parity 22/22 PASS;
- visibility 22/22 PASS;
- valuation visibility/isolation PASS;
- source-only archive SHA PASS;
- whole-source/source-owner identities PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze the C1 implementation.

No source/prompt/schema changes afterward.

---

# 14. Provider/API calls remain zero

REV31-C1 provider/API calls:

`0`

This includes:

- KIS;
- Kiwoom;
- Finnhub;
- SEC;
- OpenDART;
- FRED;
- EIA;
- ECOS;
- news/event sources;
- Alpha Vantage.

Do not use a provider call to diagnose the model host boundary.

---

# 15. KIS credential safety

REV31 reports that a Settings exception emitted sensitive user input text in a tool response.
The sensitive text was not archived.

REV31-C1 must:

- never print KIS credential values;
- never include them in receipts/logs;
- keep KIS disabled;
- make KIS calls:
  `0`;
- secret-scan result artifacts.

Before the future REV32 KIS probe, the user should supply/activate **rotated** KIS credentials through the secure local
environment.

Do not activate KIS during REV31-C1.

---

# 16. Disk guard

REV31 pre-transmission gate free bytes:

`11,037,462,528`

Hard pre-model floor:

`10 GiB`

Immediately before first model call:
- remeasure;
- require >=10 GiB.

If below:
perform only safe temporary/report cleanup that does not delete:
- sealed REV29 source;
- REV31 source-only archive;
- immutable result archives;
- registered fixtures.

If still below:

`R2B_R9_REV31_C1_DISK_GUARD`

No model calls.

---

# 17. Explicit external transmission approval

The user has explicitly requested external model transmission approval in the work instruction.

REV31-C1 explicitly authorizes transmission of the already-frozen current source/model inputs to the existing official:

`GPT-5.6 Sol / xhigh`

Thesis Monitor model runner.

Only after:
- actual host qualification PASS;
- actual execution-context freeze PASS;
- request identity PASS;
- source-only archive SHA PASS;
- disk guard PASS.

Approved stages:

- Market:
  `2/2`
- Core:
  current frozen batching for 22 subjects
- A:
  current frozen batching for 22 subjects
- B:
  current frozen batching for 22 subjects.

Expected maximum logical calls under current batching:

`26`

No fallback.
No judge.
No result-driven source refresh.
No semantic/schema retry.
No selective ticker rerun.

Transport retry is limited to the repository's already-frozen authorized transport policy.
REV31-C1 does not grant a new discretionary retry.

Do not request redundant user approval for this exact scope.

---

# 18. Model execution

After all gates:

run fresh model outputs over the exact sealed source:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`.

Model-output reuse:

`0`

REV31 sent zero requests, so no previous response exists.

Record:
- actual-host receipt identity;
- transition receipt;
- actual-host freeze identity;
- each call's immediate context verification;
- source/request/prompt/schema hashes;
- model call ledger.

---

# 19. Valuation authority boundaries

Preserve current sealed valuation state.

Qualified provider-native valuation may influence only the existing authorized:
- NewBuyer valuation context;
- Holder valuation context;
- valuation-specific caution/confidence.

It may not establish:
- Overall business direction;
- Core directional reason;
- A directional reason;
- supporting/contradicting directional refs.

Reject violations.

---

# 20. Exact messages

After Market/Core/A/B acceptance:

use production sender payload builder with:

`delivery_disabled = true`

Capture:
- MARKET_US;
- MARKET_KR;
- US14;
- KR8.

Require:

`24/24`

plus:
- `ALL_MESSAGES.md`;
- exact payload hashes.

No post-hoc reconstruction.

Telegram:

`0`.

---

# 21. Human-review archive

Create standalone:

`r2b-r9-rev31-c1-24-message-human-review.zip`

and `.sha256`.

Include:
- exact 24 sender payloads;
- model ledger;
- request/source identities;
- valuation authority audit;
- launch-context qualification/freeze receipts;
- sender-boundary proof;
- production isolation.

Do not include the external independent blind judgment text.

---

# 22. Preserve blind comparison validity

The external independent judgment SHA:

`e935e4387f4d275466c932f9a03274dee739cfdd0dfc7411f40b755f7142b6c9`

was created before any Monitoring AI output existed.

REV31-C1 must not expose it to the model.

After REV31-C1 completes, the user can compare:
- that already-frozen independent judgment;
against
- the new Monitoring AI output.

No second blind judgment is needed unless the source changes.

---

# 23. Production side effects

Hard zero:

- Telegram recipient sends;
- production decision/warning writes;
- scheduler mutation;
- broker/trading operations;
- deploy;
- main merge;
- remote push;
- service restart.

Official model reads/state access required for the approved launch are permitted only under the qualified host contract.

Official state writes:

`0`

---

# 24. Result upload approval

After secret scan, REV31-C1 explicitly authorizes upload to the existing iCloud Drive / Thesis Monitor folder of:

- REV31-C1 result ZIP + SHA;
- REV31-C1 human-review ZIP + SHA.

The REV31 source-only ZIP is already sealed and may be referenced/reused byte-identically; do not rewrite it.

No separate upload approval is required for this exact destination.

---

# 25. KIS FY1 EPS/fPER stays next

Do not execute KIS work in REV31-C1.

Preserve the next-work scope:

Official candidate endpoint:

`/uapi/domestic-stock/v1/quotations/estimate-perform`

Future REV32:

- use rotated KIS credentials;
- bounded KR8 capability probe;
- no broad full-fresh initially;
- exact `sht_cd` security identity;
- inspect actual period/year labels;
- qualify future fiscal-year EPS;
- define `FY1 EPS`, not 12M/NTM unless exact source semantics say so;
- qualify provider-native estimate PER if exact;
- derive `FY1 fPER = completed-session price / FY1 EPS` only if price/EPS security/share basis is exact;
- no FnGuide paid source;
- no Alpha Vantage.

REV32 must remain independent from the sealed REV29/REV31 blind proof.

---

# 26. Success terminal

Use only:

`R2B_R9_REV31_C1_QUALIFIED_HOST_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Require:

1. REV31 result integrity PASS;
2. REV31 source-only archive integrity PASS;
3. exact sealed source identity unchanged;
4. provider calls 0;
5. KIS calls 0;
6. actual official host independently qualified;
7. state read access available under approved host;
8. state permission mutations 0;
9. state writes 0;
10. preparation→execution transition explicitly qualified;
11. only expected safe-env difference accepted;
12. no marker spoofing;
13. actual execution context frozen before first request;
14. every model call matches actual-host freeze;
15. request/prompt/schema/source identities unchanged;
16. source-only ZIP SHA verified before model call;
17. full validation green;
18. pre-model free >=10 GiB;
19. Market 2/2;
20. Core 22/22;
21. A 22/22;
22. B 22/22;
23. valuation authority audit PASS;
24. exact messages 24/24;
25. human-review ZIP generated;
26. Telegram 0;
27. production writes/scheduler/broker/deploy 0;
28. secret scan PASS;
29. iCloud upload receipts complete;
30. external blind judgment SHA preserved but never exposed to models.

---

# 27. Honest stop terminals

- `R2B_R9_REV31_C1_SEALED_SOURCE_IDENTITY_GAP`
- `R2B_R9_REV31_C1_REQUEST_FREEZE_IDENTITY_GAP`
- `R2B_R9_REV31_C1_OFFICIAL_HOST_QUALIFICATION_GAP`
- `R2B_R9_REV31_C1_LAUNCH_CONTEXT_TRANSITION_GAP`
- `R2B_R9_REV31_C1_POST_FREEZE_CONTEXT_DRIFT`
- `R2B_R9_REV31_C1_STATE_ACCESS_GAP`
- `R2B_R9_REV31_C1_VISIBILITY_REGRESSION`
- `R2B_R9_REV31_C1_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV31_C1_DISK_GUARD`
- exact model/render/sender failure.

Do not solve by:
- spoofing CODEX_SANDBOX;
- modifying state permissions;
- rewriting frozen receipts;
- disabling context checks;
- refreshing source;
- regenerating a different blind archive;
- exposing the human judgment to the model.

---

# 28. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV31 report/source-only identities
- repository identities
- changed-file inventory
- bundle manifest.

## Launch boundary
- preparation host receipt identity;
- qualified actual-host receipt;
- transition receipt;
- official execution-context freeze;
- per-call context verification ledger;
- spoofing/state-write negative proofs.

## Sealed source
- source generation/whole-source/source-owner hashes;
- source-only ZIP SHA proof;
- request freeze identities;
- provider calls 0.

## Validation
- focused/full/Ruff/diff/knowledge;
- secret scan.

## Models
- Market/Core/A/B ledger;
- exact prompt/schema/input identities;
- model transport counters;
- accepted-output valuation authority audit.

## Messages
- exact24;
- message hashes;
- human-review ZIP/SHA.

## Safety
- KIS 0;
- Alpha Vantage 0;
- Telegram 0;
- state writes 0;
- production side effects 0;
- iCloud upload receipts.

## Next
- retained REV32 KIS FY1 EPS/fPER handoff.

---

# 29. Final principle

The source, source-only blind archive, valuation owner and model requests are already ready.

REV31 did not fail because the model rejected anything.
It did not send a model request at all.

The preparation sandbox and official execution host are two legitimate security contexts with different capabilities.

Do not force them to look identical by spoofing an environment marker.

Instead:

1. independently qualify the actual permitted official model host;
2. freeze that real host as the execution authority;
3. verify every call against that exact host freeze;
4. keep source/request/model identities immutable;
5. run the already-approved model proof and exact 24-message capture.

Only after that blind comparison completes should the project move to the separate free-KIS FY1 EPS/fPER REV32.
