# Thesis Monitor — R2B-R9-REV45
## Finnhub FY1 Forward P/E Policy Repair → Fresh US14 Messages → Conditional Fresh KR8 Messages → Main Integration
### One staged execution; no re-collection across successful stages
### US target session: 2026-10-01 XNYS
### KR target session: 2026-10-02 XKRX, only after completed-session gate
### Main merge authorized only after both market proofs and merged-main validation PASS

---

# 0. User authorization and objective

The user explicitly authorizes the following staged sequence:

1. adopt Finnhub `forwardPE` as Thesis Monitor `fPER(FY1)` for the provider-native US valuation family;
2. replace the over-strict SEC-receipt requirement for direct-US Finnhub provider-native valuation with a narrower provider/listing identity contract;
3. collect the newest completed US data for today's Korean-date run and generate current US messages;
4. if the US proof succeeds, collect the newest completed Korean-market data and generate current KR messages;
5. if both market proofs and all validations succeed, merge the accepted branch into `main`;
6. push `main` only when it can be done by an ordinary non-force update after fresh remote reconciliation.

This task does **not** authorize:
- deployment;
- service restart;
- scheduler activation/change;
- Telegram delivery;
- broker actions;
- production DB mutation.

Message generation is authorized; message sending is not.

---

# 1. REV44 result is the base SoT

Verify:

`thesis-monitor-20261002-r2b-r9-rev44-finnhub-provider-native-forwardpe-owner-report.zip`

Expected SHA-256:

`774fd38137feaa364fadee8b64baff2468c17129b883cb493e4dfe192f255ced`

Expected terminal:

`R2B_R9_REV44_FINNHUB_PROVIDER_NATIVE_FORWARDPE_OWNER_PASS_READY_FOR_FRESH_US_INTEGRATION`

Expected repository identity:

```text
branch = codex/r2b-r9-rev44-finnhub-forwardpe-owner
base = 0a0d68b9f9b1b62c61839ba3b7f91fba808a38b8
tested_implementation = deccb0f99957028d949b5c528b87f4a1c4440ab5
final = 931d639bfa46e73804406ce2922273a50eb39265
```

Expected REV44 safety:

```text
provider calls = 0
model calls = 0
messages = 0
production writes = 0
validation = PASS
```

Verify:
- sidecar;
- CRC;
- full manifest;
- no missing/hash/size/extra mismatch.

Do not modify or overwrite REV44 artifacts.

---

# 2. Preserve REV44 remotely first

REV44 was local-only at report time.

Before implementation:

1. secret-scan the REV44 outgoing commit range;
2. create/push a non-force archival remote ref for exact final SHA;
3. fetch the ref;
4. prove remote SHA is exactly:

`931d639bfa46e73804406ce2922273a50eb39265`

Suggested ref:

`archive/worktree-cleanup/20261002/codex-r2b-r9-rev44-finnhub-forwardpe-owner`

No force push.
No remote deletion.
No main merge yet.

Create REV45 from the exact remote-preserved REV44 final SHA.

Suggested branch:

`codex/r2b-r9-rev45-fy1-forwardpe-fresh-us-kr-main`

---

# 3. Storage preflight

Record current APFS free bytes.

Hard floor:

`12 GiB`

Preferred:

`16 GiB`

REV44 observed roughly 49 GiB available, but remeasure.

If below the hard floor:

`R2B_R9_REV45_STORAGE_HEADROOM_GAP`

Stop before provider/model work.

No broad worktree cleanup inside REV45.

---

# 4. Stage A — product-policy repair, offline first

Before any fresh provider collection, implement and fully test two bounded policy changes.

---

# 5. Policy A — Finnhub `forwardPE` is canonical FY1

The user explicitly authorizes the product semantic:

```text
provider = FINNHUB
route = /stock/metric
provider_field = forwardPE
canonical_metric = FORWARD_PE
canonical_horizon = FY1
estimate_basis = ANALYST_ESTIMATES_FORWARD
owner_kind = PROVIDER_NATIVE_ATOMIC_RATIO
```

Runtime/display state:

```text
QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE
```

Preferred user label:

`fPER(FY1)`

with source:

`Finnhub`.

Do not retain `PROVIDER_FORWARD_HORIZON_UNSPECIFIED` for a newly qualified direct-US `forwardPE` after this policy is active.

---

# 6. Preserve truthful provenance for Policy A

REV44's own captured public-doc corpus did not reproduce the exact next-fiscal-year sentence.

Do not rewrite that history.

Record:

```text
REV44_document_capture_FY1_definition = NOT_REPRODUCED
REV45_canonical_horizon = FY1
REV45_horizon_authority = USER_AUTHORIZED_PRODUCT_POLICY
provider_raw_field = forwardPE
```

Do not claim a field-definition SHA that REV44 did not actually capture.

The runtime semantic is nevertheless FY1 because the user explicitly chose this product interpretation.

---

# 7. Never reconstruct FY1 EPS from `forwardPE`

Do not create a consumable:

```text
implied_FY1_EPS = price / forwardPE
```

No implied EPS may enter:

- financial facts;
- source owner;
- numeric registry;
- model input;
- renderer;
- price target logic.

The US value is the provider-native ratio itself.

KR remains a separate method:

```text
KIS completed-session close / KIS FY1 EPS
```

Both may render as `fPER(FY1)` while preserving different provenance/method metadata.

---

# 8. Policy B — Finnhub direct-US provider identity v2

The old `sec-finnhub-direct-security-identity-v1` was too strict for this atomic valuation family because several direct US common stocks were denied solely because an archived SEC/official identity receipt was absent.

Create a bounded replacement:

`finnhub-direct-us-provider-identity-v2`

This applies **only** to Finnhub provider-native atomic valuation fields:

```text
peTTM
pbQuarterly
forwardPE
```

Do not weaken security identity globally for business evidence, prices, filings, events, or other providers.

---

# 9. Direct-US identity v2 PASS rule

For a local canonical security classified as a direct/common US-listed equity, PASS when all are true:

1. canonical monitored ticker exists;
2. local security class is direct/common equity;
3. requested Finnhub symbol equals canonical ticker;
4. `profile2.ticker` equals requested ticker;
5. `/stock/metric.symbol` equals requested ticker;
6. Finnhub profile exchange normalizes to a compatible US primary listing venue;
7. profile currency is compatible with the monitored US listing;
8. profile + metric belong to the same sealed generation;
9. no contradictory remap/listing/currency evidence exists.

A separate SEC/issuer identity receipt becomes:

`OPTIONAL_SUPPORTING_EVIDENCE`

for these atomic valuation fields.

---

# 10. Exchange normalization

Reuse an existing canonical exchange normalizer when available.

At minimum recognize compatible US variants such as:

```text
NASDAQ
NASDAQ GLOBAL SELECT MARKET
NASDAQ GLOBAL MARKET
NASDAQ CAPITAL MARKET
NYSE
NEW YORK STOCK EXCHANGE
```

Do not normalize foreign exchanges into US venues.

Do not pass a row merely because the ticker text matches.

---

# 11. Known structural denials remain

Do not relax these merely to increase coverage.

## HUT
Historical evidence shows requested `HUT` bound by Finnhub profile to:

`TORONTO STOCK EXCHANGE`

for the sealed generation.

That is a real listing conflict for the monitored US HUT security.

Keep fail-closed unless the **new fresh** response itself cleanly proves the intended US listing under the new contract.

Do not reuse a Toronto metric for Nasdaq HUT.

## SKHY
Historical Finnhub request remapped to:

`000660.KS / KRX / KRW`

Keep US ADS valuation unavailable unless the fresh provider response proves the monitored US ADS directly.

## TSM
Historical Finnhub request remapped to:

`2330.TW / TWSE / TWD`

Keep US ADR valuation unavailable unless fresh response proves the US ADR directly.

## WRD
Depositary security with basis/currency ambiguity.

Keep depositary guard.

No depositary-ratio arithmetic to rescue a provider-native P/E.

---

# 12. Stage A offline replay requirement

Before fresh collection:

Replay the sealed REV29/REV44 corpus under the new two policies.

Expected mechanics:

- GOOGL / IBM remain positive if numeric;
- direct US common names previously denied only for missing official identity may now PASS identity;
- actual HUT foreign-listing conflict remains denied on the historical fixture;
- SKHY / TSM / WRD remain depositary/remap denied;
- null/blank `forwardPE` remains typed unavailable.

Do not hardcode expected numeric coverage.

Run focused tests and full regression before Stage B.

If Stage A fails:

`R2B_R9_REV45_POLICY_REPAIR_VALIDATION_GAP`

No fresh provider calls.

---

# 13. Stage B — fresh US proof

Only after Stage A PASS.

This is a manual fresh proof, independent of the normal scheduler clock.

Target market/session:

```text
market = XNYS / US
target_completed_regular_session = 2026-10-01
run_KST_date = 2026-10-02
```

The runtime exchange calendar is authoritative.

If 2026-10-01 is not the latest completed eligible US regular session for the execution timestamp, stop and report the actual calendar state rather than silently shifting target.

---

# 14. US full-fresh source collection

Run the current complete US collection contract for the US14 roster plus exactly the US Market/context inputs required by the accepted pipeline.

US14:

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

Use the currently accepted source-owner graph.

For Finnhub provider-native valuation:

- one `profile2` and one `stock/metric` per eligible security only as required by the existing normal source plan;
- consume `peTTM`, `pbQuarterly`, and `forwardPE` from the same sealed `stock/metric` response;
- no extra request per metric;
- do not call `/stock/eps-estimate`.

Alpha Vantage:

`0` unless an already mandatory non-valuation production role explicitly requires it under existing policy; if no such mandatory role exists, keep `0`.

Do not add FMP/BQ/Yahoo/Zacks as forward-valuation providers.

---

# 15. US attempt/fallback collection policy

Preserve the user's current operating rule:

```text
08:10 KST first collection
if incomplete -> 08:15
if still incomplete -> 08:20 full resnapshot
```

Because REV45 is a manually invoked proof after those times, do not synthesize or replay the scheduler attempts.

Run exactly one controlled full-fresh source generation for the target completed US session.

If that source generation itself has provider-level incomplete mandatory data, use the existing bounded retry/timeout behavior, but:

- do not patch from an older generation;
- do not combine partial attempt values across generations;
- no favorable-value retry.

The sealed successful generation is the only model input.

---

# 16. US source seal before models

Before any model call:

- complete all US source acquisition;
- validate exact target date/session;
- validate source identity;
- validate forward valuation states;
- validate authority graph;
- create immutable source-only packet;
- record raw/projection hashes;
- seal source packet.

No provider refresh after model execution begins.

A downstream model/render failure must not trigger source recollection.

---

# 17. US valuation behavior

For a fresh direct-US qualified row:

```text
PER       = Finnhub peTTM provider snapshot
PBR       = Finnhub pbQuarterly provider snapshot
fPER(FY1) = Finnhub forwardPE provider-native FY1 snapshot
```

Each metric qualifies independently.

Examples:

- valid PER + missing forwardPE:
  current PER may display, fPER unavailable;
- valid forwardPE + invalid/missing PBR:
  fPER may display, PBR unavailable;
- identity fail:
  all Finnhub provider-native valuation metrics for that exact security remain unavailable.

No all-or-nothing stock rejection solely due optional valuation.

---

# 18. Forward valuation model authority

`fPER(FY1)` may enter only:

- Valuation display;
- Pass B NewBuyer valuation context;
- Pass B Holder valuation context.

It must not independently enter or alter:

- Market;
- Core;
- Pass A;
- Overall direction;
- business thesis polarity.

Required visibility:

```text
Core = false
Pass A = false
Pass B NewBuyer = true
Pass B Holder = true
Overall direction use = false
```

No fixed cheap/expensive BUY rule.

---

# 19. US model execution

After immutable source seal, run the accepted production-equivalent US AI chain.

Use the current architecture, not a simplified substitute.

Expected logical scope includes:

- US Market model/context if required;
- US Core;
- US Pass A;
- US Pass B / NewBuyer / Holder roles;
- final validator;
- renderer.

Model timeout:

`10 minutes per attempt`

Retries:

`maximum 2 retries per failed logical model call`

Do not retry successful calls.

If an individual call fails:
- continue independent remaining calls where architecture allows;
- preserve failure receipts;
- do not recollect provider data;
- complete the bounded run before deciding final status.

---

# 20. US message set

Generate production-equivalent previews only.

No Telegram.

Expected US delivery-equivalent set:

```text
1 US Market message
14 US stock messages
= 15 messages
```

If the current production contract has explicitly removed a standalone Market message, follow the current canonical renderer rather than forcing an obsolete count; record the exact expected and actual count.

Do not redesign the message format in REV45.

Preserve current accepted user-facing stock format.

Do not reintroduce sections previously removed from stock messages:

- 기존 등록 가격 규칙
- 데이터 주의
- 다음 확인
- 미확인

---

# 21. US success gate

US stage PASS requires:

- exact target session;
- complete immutable source generation;
- mandatory source validators PASS;
- every US14 subject has a typed packet;
- forwardPE FY1 policy applied only where identity/value qualify;
- depositary/remap failures stay unavailable;
- source-only seal before models;
- required model chain completed within bounded retry policy;
- exact renderer/validator PASS;
- no post-model source mutation;
- no Telegram;
- full tests/Ruff/diff/knowledge/secret checks PASS.

US terminal:

`R2B_R9_REV45_US14_FRESH_FY1_FORWARDPE_MESSAGE_PROOF_PASS`

If US does not PASS:
stop before KR and before main merge.

---

# 22. Seal US stage independently

After US PASS create an immutable US stage result:

`thesis-monitor-20261002-r2b-r9-rev45-us14-fresh-fy1-forwardpe-message-proof.zip`

+ SHA sidecar.

Do not recollect US later merely because KR occurs hours afterward.

The US result becomes frozen input/evidence for the final combined acceptance.

---

# 23. Stage C — conditional KR fresh proof

Proceed only after US PASS.

Target KR session:

```text
market = XKRX
target_regular_session = 2026-10-02
```

The KR proof is allowed only after the runtime calendar/session gate establishes that the 2026-10-02 regular session is completed and the normal post-close data boundary is satisfied.

Use the current operating target window:

```text
16:10 KST first
if incomplete -> 16:15
if still incomplete -> 16:20 full resnapshot
```

For this manual proof, if Stage C is reached before the accepted completed-session boundary:

do **not** sleep for hours or poll continuously.

Seal all US results and stop with:

`R2B_R9_REV45_US_PASS_PENDING_KR_20261002_COMPLETED_SESSION`

On resume after the gate:
- reuse the exact sealed US result;
- do not recollect US;
- execute only missing KR Stage C onward.

No automatic background wait.

---

# 24. KR holiday/session rule

Runtime XKRX calendar is authoritative.

If 2026-10-02 is not an eligible KR trading session:
- do not generate KR stock/market messages for that date;
- record the exact calendar state;
- do not silently use stale data as today's KR data.

Because main merge requires a current KR proof under this user-authorized plan, a non-trading-day result must stop before merge unless the user separately authorizes latest-prior-session proof.

---

# 25. KR full-fresh source collection

KR8:

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

Collect exactly the fresh KR Market/context and stock inputs required by the accepted production architecture.

Preserve the accepted KR FY1 method:

```text
latest completed-session KIS unadjusted close
/
qualified KIS house-research FY1 EPS
=
current-price fPER(FY1)
```

Preserve:
- exact-security corporate-action guard;
- exact FY1 period/source;
- KIS provider semantics;
- Kiwoom current provider-native PER/PBR where accepted;
- no forward valuation use for Overall/Core/A.

003690 or any other missing estimate remains typed unavailable rather than blocking the whole stock.

---

# 26. KR source seal and models

Same discipline as US:

1. finish source acquisition;
2. validate target 2026-10-02 completed session;
3. immutable source seal;
4. no provider refresh afterward;
5. execute accepted KR Market/Core/A/B chain;
6. render current production-equivalent messages.

Model timeout:

`10 minutes`

Retries:

`maximum 2 retries per failed logical model call`.

Continue independent calls after isolated failures where safe.

---

# 27. KR message set

Generate previews only.

No Telegram.

Expected KR set:

```text
1 KR Market message
8 KR stock messages
= 9 messages
```

If current canonical production renderer has a different explicit count, use it and document expected vs actual.

No user-facing format redesign.

---

# 28. KR success gate

KR stage PASS requires:

- target XKRX session exact;
- immutable fresh source;
- KR8 typed packets;
- KIS FY1 fPER contract preserved;
- all mandatory validators PASS;
- model chain/renderer PASS;
- no provider recollection after source seal;
- no Telegram;
- validation/secret scan PASS.

KR terminal:

`R2B_R9_REV45_KR8_FRESH_CURRENT_FY1_MESSAGE_PROOF_PASS`

If KR fails:
do not merge main.

Keep the successful US artifact unchanged.

---

# 29. Combined proof

Only after US PASS + KR PASS:

Create a combined acceptance receipt covering:

```text
US target session = 2026-10-01
KR target session = 2026-10-02
US source generation/hash
KR source generation/hash
US message count
KR message count
all model call lineage
all validation receipts
fPER owner methods by market
typed unavailable counts
no Telegram proof
no production DB/scheduler mutation
```

Expected production-equivalent total when both standalone Market messages are canonical:

`24 messages`

Do not force 24 if the current canonical renderer contract has intentionally changed; record exact canonical count.

---

# 30. Merge authorization

The user explicitly authorizes merge to `main` **only after**:

```text
Stage A PASS
Stage B US PASS
Stage C KR PASS
combined validation PASS
```

No merge based on a partial market proof.

Before touching main:

1. seal combined result ZIP + SHA;
2. commit all accepted implementation/docs/tests;
3. secret-scan;
4. push/preserve the REV45 feature branch remotely;
5. fresh-fetch origin;
6. record:
   - REV45 final SHA;
   - local main SHA;
   - origin/main SHA;
   - merge-base relationships.

---

# 31. Existing main divergence must be handled safely

Known pre-REV45 operating local main historically was:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

and origin/main historically differed.

Do not assume either historical SHA is still current.

Fresh-fetch immediately before merge.

Create non-destructive backup refs for:

```text
pre-rev45-local-main
pre-rev45-origin-main
accepted-rev45-tip
```

with timestamps/SHA receipts.

No force operations.

---

# 32. Main reconciliation algorithm

If local main and origin/main are already identical:
- merge REV45 into local main with an explicit merge commit.

If origin/main is an ancestor of local main:
- merge REV45 into local main;
- later push normally.

If local main is an ancestor of origin/main:
- first fast-forward local main to origin/main;
- then merge REV45.

If local main and origin/main have diverged:
- merge origin/main into local main normally, preserving both histories;
- if conflict-free and validation PASS, then merge REV45;
- if there are semantic conflicts in Thesis Monitor source/policy/schema files:
  stop with:

`R2B_R9_REV45_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED`

Do not guess conflict resolutions.
Do not rebase accepted history.
Do not force push.

---

# 33. Validation on merged main is mandatory

After local main contains all intended histories:

Run on **merged main SHA**:

- focused forward valuation tests;
- US source/identity/valuation tests;
- KR FY1 valuation tests;
- model/renderer contract tests;
- full pytest;
- Ruff;
- git diff --check where applicable;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- production-protected-file comparison.

The branch result being PASS is not sufficient.

Merged main itself must PASS.

---

# 34. Remote main push

Only after merged-main validation PASS.

A normal non-force push to:

`origin/main`

is authorized if fresh remote state has not changed since the reconciliation fetch.

Immediately before push:
- fetch origin again;
- prove expected remote main SHA unchanged.

If it changed:
stop:

`R2B_R9_REV45_REMOTE_MAIN_MOVED_REVIEW_REQUIRED`

Do not force push.

If unchanged:
perform ordinary push.

Verify remote main exact final SHA after push.

---

# 35. No deploy after merge

Even after successful main push:

```text
DEPLOY = 0
SERVICE_RESTART = 0
SCHEDULER_MUTATION = 0
TELEGRAM_SEND = 0
PRODUCTION_DB_WRITE = 0
```

Main integration is the end of REV45.

Production promotion/activation remains a separate explicit task.

---

# 36. Failure-continuation policy

Within a market stage:

- one stock/provider/model failure must not automatically abort unrelated subjects;
- continue to gather deterministic failure receipts;
- do not hide partial failures;
- do not patch with older values;
- do not recollect source because a downstream model failed.

At the stage boundary:

- US mandatory failure => no KR, no merge;
- KR mandatory failure => no merge;
- merge validation failure => no remote main push.

---

# 37. Final success terminal

Only if:

- policy repair PASS;
- fresh US proof PASS;
- fresh KR proof PASS;
- combined proof sealed;
- local main merge/reconciliation PASS;
- merged-main validation PASS;
- normal remote main push PASS and remote SHA verified;

use:

`R2B_R9_REV45_FY1_FORWARDPE_US_KR_FRESH_MESSAGES_MAIN_INTEGRATION_PASS`

Report exact:

```text
REV45 feature SHA
final local main SHA
final origin/main SHA
US session
KR session
US provider/model/message counts
KR provider/model/message counts
US fPER(FY1) qualified/unavailable states
KR fPER(FY1) qualified/unavailable states
all message preview files
full-test counts
secret-scan status
production isolation status
```

---

# 38. Valid partial terminals

Use the narrowest truthful state:

```text
R2B_R9_REV45_POLICY_REPAIR_VALIDATION_GAP
R2B_R9_REV45_US_SOURCE_GAP
R2B_R9_REV45_US_MODEL_MESSAGE_GAP
R2B_R9_REV45_US_PASS_PENDING_KR_20261002_COMPLETED_SESSION
R2B_R9_REV45_KR_SESSION_GATE_GAP
R2B_R9_REV45_KR_SOURCE_GAP
R2B_R9_REV45_KR_MODEL_MESSAGE_GAP
R2B_R9_REV45_COMBINED_VALIDATION_GAP
R2B_R9_REV45_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED
R2B_R9_REV45_MERGED_MAIN_VALIDATION_GAP
R2B_R9_REV45_REMOTE_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV45_STORAGE_HEADROOM_GAP
```

A partial result must preserve every already-successful immutable stage.

---

# 39. Required artifacts

At minimum:

## Stage A / policy
- `policy-repair-receipt.json`
- `finnhub-direct-us-provider-identity-v2.json`
- `finnhub-fy1-forwardpe-policy.json`
- offline replay matrix
- validation receipts

## US
- immutable US source-only ZIP + SHA
- US source authority/identity/valuation matrices
- model lineage
- exact US message previews
- US proof ZIP + SHA

## KR
- immutable KR source-only ZIP + SHA
- KR KIS FY1 valuation matrix
- model lineage
- exact KR message previews
- KR proof ZIP + SHA

## Combined / Git
- combined proof ZIP + SHA
- REV45 branch preservation receipt
- pre-main refs receipt
- main relationship/reconciliation receipt
- merged-main validation receipt
- origin/main push receipt if performed
- final repository identities
- secret scan
- production isolation
- bundle manifest

Suggested final result:

`thesis-monitor-20261002-r2b-r9-rev45-fy1-forwardpe-us-kr-fresh-messages-main-integration-report.zip`

+ `.sha256`.

---

# 40. Final principle

REV45 is allowed to finish the development loop, but only in this order:

```text
offline policy repair
→ full validation
→ fresh US source seal
→ US models/messages
→ freeze US success
→ wait/return until KR completed-session gate if necessary
→ fresh KR source seal
→ KR models/messages
→ combined proof
→ preserve feature branch
→ reconcile main non-destructively
→ validate merged main
→ normal non-force origin/main push
→ stop
```

Never trade reproducibility for speed, and never use stale/partial data to force the merge gate.
