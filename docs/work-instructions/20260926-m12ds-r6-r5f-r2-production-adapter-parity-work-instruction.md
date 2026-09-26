# Thesis Monitor — M12DS-R6-R5F-R2
## Production Adapter Parity Closure
### Existing Source Owners + Existing Market/Core/A/B/Renderer/Delivery Behind the Unified Single-Run Contract

**Purpose:** close the two open adapter-parity gaps from R5F-R1 without activating the new scheduler. Reuse the existing production owners and validators behind the new unified snapshot pipeline, prove deterministic parity with frozen real inputs, register the concrete adapter, and produce a production-equivalent dry-run capture. Scheduler cutover remains a separate later task.

---

# 0. Newest accepted SoT

Adopt the R5F-R1 result as the newest SoT for this scope.

Result ZIP SHA-256:

`08308c83e4e6756d5c1e0194202f6b60db4cb66357026396c20a4858fba8505e`

Verdict:

`IMPLEMENTATION_PARTIAL_ADAPTER_PARITY_OPEN`

Promotion state:

- `READY_FOR_PROMOTION = NO`
- `PIPELINE_PASS = NO`

Repository identities:

- base / operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- instruction:
  `f2e747c253210e2b30992a62e6be533531abae7a`
- implementation:
  `2b111be6507d477957f9ef2eeb9b9eecd95f249d`
- tested final:
  `d0f9a48cd7b215e6a3422e5ca399baa9c02cf028`

R5F-R1 validation:

- focused: `75 passed`
- full: `5302 passed / 63 skipped / 0 failed`
- Ruff: PASS
- diff: PASS
- Investment Knowledge: PASS
- Chart Knowledge: PASS
- real provider calls: 0
- Alpha calls: 0
- model calls: 0
- Telegram sends: 0
- scheduler mutations: 0
- production DB mutations: 0

R5F-R1 bundle integrity independently rechecked:

- ZIP/sidecar SHA exact;
- manifest entries: `33/33`;
- missing: `0`;
- hash/size mismatch: `0`;
- extra manifest-scope files: `0`.

---

# 1. Accepted R5F-R1 implementation

Do not rewrite the orchestration foundation unless a proven adapter integration defect requires a minimal change.

Accepted foundation includes:

- unified US collection windows:
  `08:10 -> 08:15 -> 08:20` conditional full recollection;
- unified KR collection windows:
  `16:00 -> 16:05 -> 16:10` conditional full recollection;
- first complete attempt only;
- no cross-attempt symbol patching;
- query-time snapshot semantics;
- `finality_claim = NOT_CLAIMED`;
- immutable snapshot/policy identity;
- same snapshot across downstream stages;
- process lock / durable cycle identity;
- pre-delivery intent;
- no automatic replay after ambiguous interruption;
- no recollection after AI/render/delivery failure;
- deterministic market-closed / KRX-holiday skip;
- sanitized failure notification;
- immutable debug ZIP;
- iCloud-backed local copy + local hash verification;
- two new scheduler templates:
  - US 08:10
  - KR 16:00
- templates remain inactive;
- old primary/backup schedules remain unactivated/paused/disabled;
- no scheduler mutation has occurred.

---

# 2. Open gaps to close

## Gap A — SOURCE_ADAPTER_PARITY

R5F-R1 finding:

The existing research/source collector does not yet expose a qualified attempt-local production adapter proving all of:

- canonical per-market universe;
- complete production source-role coverage;
- fresh whole-attempt isolation;
- source row/session binding;
- raw receipt binding;
- normalized packet binding;
- zero fallback/external-reference calls;
- no inherited prior-attempt state;
- no pre-acquired night-input leakage unless that input is explicitly part of the current production contract.

The new pipeline currently uses `UnqualifiedAdapter` and correctly fails closed.

## Gap B — MARKET_CORE_A_B_RENDER_DELIVERY_ADAPTER_PARITY

R5F-R1 finding:

The existing analysis controller is research-oriented and depends on fixed manifests / blind packs / both-market topology. The new pipeline has only synthetic `PipelinePorts` fixtures, not the real existing Market/Core/A/B/validator/renderer/delivery owners.

The task must adapt the existing owners. It must **not** replace them with simplified investment logic.

---

# 3. Scope rule

This is an adapter task, not a rewrite.

The implementation must:

1. preserve existing source owner logic where valid;
2. preserve existing Market/Core/A/B prompts, schemas and validators;
3. preserve existing investment policy;
4. preserve existing render semantics;
5. preserve existing delivery contract;
6. expose them through the new unified single-market run interfaces.

Do not build a second parallel investment engine.

Do not weaken validation merely to make parity pass.

---

# 4. Production source adapter

Create a concrete adapter behind the R5F-R1 source collection interface.

## 4.1 Market isolation

The adapter must collect exactly the configured market for the run.

### US
Canonical current production universe:
- 14 US stock subjects;
- required US market context roles.

### KR
Canonical current production universe:
- 8 KR stock subjects;
- required KR market context roles.

Do not collect both markets merely because the old research collector does.

Do not silently reduce the canonical universe.

Freeze the actual current canonical symbols from operating configuration/repository and include a receipt.

---

## 4.2 Attempt-local isolation

Every collection attempt receives a fresh attempt directory/state.

Prove:

- attempt B cannot read attempt A normalized packet;
- attempt C cannot read A/B;
- no prior run's packet is imported;
- no operating-state copy can silently qualify stale data;
- success packet contains only values collected/owned by that attempt.

A failed attempt remains diagnostic only.

---

## 4.3 Source-role inventory

Before implementation, enumerate every source role consumed by the real Market/Core/A/B path for each market.

For every role record:

- owner function/module;
- provider;
- endpoint/source family;
- market;
- symbol/universe;
- expected row/session date;
- raw/adjusted basis;
- freshness/as-of semantics;
- mandatory/optional status;
- validator;
- fallback behavior.

Then bind all **mandatory** production roles into the unified snapshot contract.

Do not invent role coverage from downstream prompt fields.

---

## 4.4 Raw receipts

For every external/source read that contributes to the frozen packet, preserve:

- request identity;
- provider/source;
- request timestamp;
- response/result identity;
- raw response hash or source artifact hash;
- normalization hash;
- role binding;
- target/as-of date;
- basis;
- validator receipt.

A caller assertion such as `valid=true` is not sufficient.

The adapter must produce evidence consumable by `unified_snapshot_contract.py`.

---

## 4.5 Fallback prohibition for parity proof

During parity proof:

- Alpha Vantage calls = 0;
- Massive calls = 0;
- undocumented fallback provider calls = 0.

If the existing source owner would normally fall back:
- disable the fallback for this proof;
- fail closed instead;
- document the behavior.

The product decision is query-time snapshot from the configured production source, not external finality reconciliation.

---

# 5. Existing AI owner adapter

Create a concrete downstream `PipelinePorts` implementation that invokes the **existing** production-equivalent owners for:

- Market
- Core
- A
- B
- validator
- renderer
- delivery abstraction

Do not copy prompt text into a new independent implementation.

Reuse canonical production functions/modules or extract stable adapters around them.

---

# 6. Per-market execution shape

The new scheduler runs one market at a time.

The adapter must prove the old both-market/research assumptions have been removed from the runtime boundary.

## US run

Expected configured output set:

- US market message: 1
- US stock messages: 14
- total: `15`

## KR run

Expected configured output set:

- KR market message: 1
- KR stock messages: 8
- total: `9`

Combined offline parity corpus:

`15 + 9 = 24`

Do not require both markets to be collected in the same live run.

Do not let KR holiday state suppress an eligible US run.

---

# 7. Prompt / schema / policy parity

For each stage prove that the unified adapter uses the same canonical:

- system/instruction templates;
- typed schema;
- policy configuration;
- Knowledge versions;
- numeric/source validators;
- stock roster;
- message IDs;
- renderer rules;
- delivery target contract

as the existing accepted path.

Where an old controller freezes research manifests, replace only the controller-specific packaging with the unified run/snapshot identities.

Do not remove source validation, typed schema checks, numeric checks or policy checks.

---

# 8. Frozen-input parity proof before any real model call

First prove adapter parity offline using previously sealed real source/input artifacts.

Required:

1. source adapter can ingest/replay the frozen real provider/source artifacts without network;
2. resulting unified packet is deterministic;
3. same canonical role values are presented to the existing analysis owner;
4. stage input hashes are deterministic;
5. expected message IDs/population exactly match production configuration;
6. no old research-only state is required;
7. no cross-market dependency exists unless explicitly required by the current product contract;
8. no night/pre-acquired input is silently consumed outside the declared role inventory.

If parity fails, stop before live provider/model calls.

---

# 9. Production-equivalent AI dry-run

Only after Sections 4–8 PASS.

Run a controlled production-equivalent AI capture using the concrete adapter.

This capture may use **frozen accepted real source packets**; it does not need to pretend to be a live scheduled run.

Required corpus:

## US
- Market: `1/1`
- Core: `14/14`
- A: `14/14`
- B: `14/14`
- rendered: `15/15`

## KR
- Market: `1/1`
- Core: `8/8`
- A: `8/8`
- B: `8/8`
- rendered: `9/9`

Combined:
- market messages: `2/2`
- stock messages: `22/22`
- rendered: `24/24`

Use actual configured model path if current project rules allow isolated dry-run calls.
If live model invocation requires separate authorization in the repository, stop after exact prompt/packet capture and report the authorization blocker rather than substituting fake outputs.

Telegram/delivery send must remain disabled.

---

# 10. Snapshot identity propagation

For every real dry-run output prove:

`run_id`
+
`market`
+
`snapshot_id`
+
`policy_hash`
+
`source packet hash`

remain identical through:

`collection -> Market -> Core -> A -> B -> validator -> render`

No stage may load a later historical packet or a different attempt.

Every final message must be traceable to the same successful snapshot.

---

# 11. Message semantic validation

Review all 24 production-equivalent rendered messages.

Required:

- correct market;
- correct stock;
- correct as-of/session context;
- query-time snapshot semantics;
- no `official final close` / `확정 종가` claim unless independently supported;
- no later-lookahead;
- no stale prior-run packet;
- no source basis contradiction;
- correct raw/adjusted vocabulary;
- current existing investment-policy wording/structure preserved;
- no accidental source/proof/debug text leaked into user-facing message.

KR holiday behavior remains a skip, but the 9-message KR parity corpus should use a frozen valid open-session input so the actual analysis/render adapter can be exercised.

---

# 12. Delivery adapter parity

Prove the delivery adapter using dry-run/test transport only.

Required:

- exact normal message IDs/order;
- no duplicate sends;
- one delivery opportunity per unified run;
- no old fallback/delivery-retry path;
- pre-delivery intent identity;
- ambiguous interruption remains fail-closed;
- delivery failure does not recollect or restart AI;
- failure finalization receives the same run/snapshot context.

Actual Telegram sends:
`0`

Recipient/delivery intent to production:
`0`

---

# 13. Failure path using concrete adapters

With the real adapters registered in test/dry-run mode, exercise at least:

1. source mandatory-role missing -> no model;
2. source validator failure -> retry state machine handles collection stage only;
3. model failure after snapshot -> no recollection;
4. schema/validator failure -> no normal delivery;
5. renderer failure -> failure finalization;
6. delivery test-transport failure -> failure finalization;
7. failure notification fixture generated;
8. debug bundle generated;
9. configured iCloud-backed local destination copy/hash verified.

No external failure notification should actually be sent during this proof.

---

# 14. Adapter registration

After parity passes, register the concrete production adapter behind the unified entrypoint.

Requirements:

- `UnqualifiedAdapter` remains the safe default when adapter qualification is absent;
- production adapter registration is explicit;
- feature flag / activation remains disabled by default;
- merely importing the module does not perform provider/model/delivery work;
- disabled-entrypoint smoke remains side-effect free.

Do not activate scheduler jobs in R5F-R2.

---

# 15. Scheduler state

R5F-R2 must make **zero scheduler mutations**.

Preserve current state:

- four old Codex primary/backup automations paused;
- legacy daily/KR-close/fallback/delivery-retry launch agents unloaded and durably disabled;
- unified US/KR templates inactive;
- unrelated telemetry/publication/onboarding/API service unchanged.

The R5F-R1 scheduler migration plan remains `NOT_APPLIED`.

Scheduler promotion is a separate R5F-R3 task after R5F-R2 is accepted.

---

# 16. iCloud evidence

Use the existing configured iCloud-backed report/debug destination.

For generated R5F-R2 result/debug fixtures:

- create locally;
- hash;
- copy to configured iCloud-backed local path;
- locally verify size/hash;
- emit detached receipt.

Do not claim Apple-server/remote-device sync.

---

# 17. Network / safety budgets

Before Section 9 parity completion:

- live provider calls = 0
- model calls = 0

During optional Section 9 controlled AI capture:

- provider calls remain `0` if frozen source packets are used;
- model calls must equal the exact expected bounded stage calls and be recorded;
- no automatic model retry unless already approved by the existing production owner.

Always:

- Alpha Vantage = 0
- Massive = 0
- Telegram sends = 0
- production delivery intents = 0
- broker actions = 0
- production DB mutations = 0
- scheduler mutations = 0
- notification mutations = 0
- deploy = 0
- service restart = 0.

Do not push unless separately authorized.

---

# 18. Validation

Required:

- source-adapter focused tests;
- raw-receipt/role-binding tests;
- attempt-isolation tests;
- zero-fallback tests;
- Market/Core/A/B adapter tests;
- prompt/schema/policy parity tests;
- per-market population tests;
- snapshot identity propagation tests;
- 24-message semantic validation tests;
- delivery dry-run parity tests;
- concrete-adapter failure-path tests;
- disabled-entrypoint smoke;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge check;
- Chart Knowledge check;
- secret scan.

No new unexplained skip/xfail.

Do not modify old provenance validators or thresholds to obtain PASS.

---

# 19. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R5F-R1 identity receipt
- repository base/instruction/implementation/final SHAs
- changed-file inventory
- production source-role inventory
- canonical US14 / KR8 universe receipt
- source-owner mapping
- raw receipt coverage matrix
- zero-fallback proof
- attempt isolation proof
- AI owner mapping
- prompt/schema/policy parity matrix
- per-market message-ID/population receipt
- frozen-input adapter parity proof
- controlled AI capture receipts if run
- rendered US15 corpus if run
- rendered KR9 corpus if run
- combined 24-message validation report
- snapshot identity propagation matrix
- concrete failure-path proof
- delivery dry-run proof
- debug/iCloud fixture receipt
- scheduler before/after proof showing zero mutations
- network/model/delivery counters
- validation logs
- secret scan
- bundle manifest.

Do not overwrite the R5F-R1 result.

---

# 20. Completion criteria

## PASS / promotion ready

Use:

`M12DS_R6_R5F_R2_PRODUCTION_ADAPTER_PARITY_PASS`

only if:

1. concrete source adapter qualified;
2. mandatory role/raw receipt coverage complete;
3. no fallback provider calls;
4. concrete Market/Core/A/B/validator/renderer/delivery adapter qualified;
5. US14 and KR8 exact populations proven;
6. query-time snapshot identity preserved end-to-end;
7. old research-only/both-market assumptions removed from runtime dependency;
8. full validation PASS;
9. controlled production-equivalent 24-message proof completed, or the only remaining blocker is an explicit separate model-call authorization with all exact prompts/inputs already frozen;
10. scheduler remains inactive.

## Partial

If either adapter cannot achieve parity:

`M12DS_R6_R5F_R2_ADAPTER_PARITY_GAP_REMAINS`

Return the smallest exact owner/module/role blocker and create the next bounded repair instruction.

---

# 21. What comes after R5F-R2 PASS

Do **not** activate schedules automatically.

The next separate task will be R5F-R3:

- promote tested adapter code;
- retire old primary/backup reservations;
- activate exactly one US 08:10 entry;
- activate exactly one KR 16:00 entry;
- verify no duplicate scheduler path;
- perform controlled shadow/live operational validation;
- then authorize normal sends only after that cutover proof passes.
