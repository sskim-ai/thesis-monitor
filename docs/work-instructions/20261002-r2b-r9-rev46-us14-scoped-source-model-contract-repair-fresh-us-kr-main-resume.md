# Thesis Monitor — R2B-R9-REV46
## US14 Scoped Source / Issuer-Bridge / Model-Capture Contract Repair
## → Fresh US14 2026-10-01 Messages
## → Conditional Fresh KR8 2026-10-02 Messages
## → Main Integration Only After Both PASS

---

# 0. Why REV46 exists

REV45 correctly completed the policy repair but stopped before any live source/model work.

Accepted REV45 terminal:

`R2B_R9_REV45_US_SOURCE_GAP`

This was a pre-dispatch contract gap, not a provider-data failure.

REV45 proved:

- Finnhub `forwardPE` product policy:
  `FY1_USER_AUTHORIZED_PRODUCT_POLICY`;
- direct-US provider identity v2;
- historical replay deterministic;
- existing KR valuation regression unchanged;
- focused/full validation PASS;
- provider calls 0;
- model calls 0;
- messages 0;
- production mutations 0.

The Stage-B blocker was architectural:

1. current source acquisition accepts ALL22/KR8-only contracts, not US14-only;
2. SKHY issuer-business replay depends on a same-generation 000660 issuer owner;
3. existing model/capture contract expects ALL22 / 24-message topology rather than US-only / 15-message topology.

REV46 closes only those scoped contracts and resumes the exact user-authorized fresh proof.

Do not restart the valuation-provider hunt.

---

# 1. Verify REV45 immutable result

Result ZIP:

`thesis-monitor-20261002-r2b-r9-rev45-fy1-forwardpe-us-kr-fresh-messages-main-integration-report.zip`

Expected SHA-256:

`3384e6771a4268de872b80714ddc8abcea0f5baa39e7233d0807b6c3d50d3786`

Expected:

```text
ZIP members = 125
manifest payload entries = 124
CRC = PASS
manifest self excluded = true
missing = 0
hash mismatch = 0
size mismatch = 0
extra = 0
```

Expected REV45 final implementation:

`28f90b66247fed679770fd6e8a6824578f654d9f`

Expected branch:

`codex/r2b-r9-rev45-fy1-forwardpe-fresh-us-kr-main`

Expected validation:

```text
focused = 230 passed
full = 7940 passed / 63 skipped / 0 failed
Ruff = PASS
diff = PASS
Investment Knowledge = PASS
Chart Knowledge = PASS
secret scan = PASS
production isolation = PASS
```

Do not rewrite REV45 evidence.

---

# 2. Preserve REV45 remotely before repair

REV45 result says the feature branch was not remotely preserved because Stage B never dispatched.

Before REV46 implementation:

1. secret-scan outgoing REV45 history;
2. push exact REV45 final SHA to a non-force archival ref;
3. fetch it back;
4. prove exact SHA:

`28f90b66247fed679770fd6e8a6824578f654d9f`

Suggested ref:

`archive/worktree-cleanup/20261002/codex-r2b-r9-rev45-policy-repair`

Then create REV46 from that exact remote-preserved SHA.

Suggested branch:

`codex/r2b-r9-rev46-us14-scoped-fresh-resume`

No main merge yet.
No force push.
No rebase of accepted history.

---

# 3. Preserve REV45 policy semantics exactly

Do not reopen these decisions.

## Finnhub forwardPE

```text
provider = FINNHUB
route = /stock/metric
provider_field = forwardPE
canonical_horizon = FY1
horizon_authority = USER_AUTHORIZED_PRODUCT_POLICY
owner_kind = PROVIDER_NATIVE_ATOMIC_RATIO
display_label = fPER(FY1)
```

Do not create implied EPS.

## Direct-US identity v2

For Finnhub atomic valuation fields only:

```text
peTTM
pbQuarterly
forwardPE
```

SEC/issuer evidence is optional supporting evidence when:

- requested ticker exact;
- profile ticker exact;
- metric symbol exact;
- US listing compatible;
- currency compatible;
- same generation;
- no contradiction.

Do not relax global security identity.

## Structural denials

Keep fail-closed:

- real foreign-listing mismatch;
- TSM home-security remap;
- SKHY home-security remap for valuation;
- WRD depositary/basis mismatch.

---

# 4. Repair A — add an explicit US14 primary source contract

Add a dedicated source topology:

`one-shot-us14-source-acquisition-v1`

Primary monitored subjects are exactly:

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

The contract must own its exact expected read set instead of inheriting the ALL22 `exact_88_stock_plan_required` guard.

REV45 historical preflight observed:

```text
ALL22 stock reads = 88
US14 candidate stock reads = 56
```

Do not hardcode `56` unless the current source planner deterministically proves four reads per US14 subject under the actual current contract.

Preferred:

- build expected reads from current US14 roster + declared source roles;
- hash the expected plan;
- validate exact set equality;
- reject missing/extra/duplicate reads.

Existing ALL22 and KR8-only contracts must remain byte/behavior compatible.

---

# 5. Repair B — separate issuer-level auxiliary dependencies from monitored securities

SKHY is a US monitored ADS/security, but some business/financial evidence belongs to the issuer also represented by Korean security `000660`.

The old replay path incorrectly makes the US14 whole-source seed depend on a KR security-level owner/baseline.

Create an explicit dependency class:

`AUXILIARY_ISSUER_ONLY`

For the SKHY bridge, declare:

```text
primary_subject = SKHY
auxiliary_issuer_security = 000660
purpose = SHARED_ISSUER_BUSINESS_FINANCIAL_EVIDENCE
```

The auxiliary subject is **not** a monitored KR stock in the US run.

---

# 6. Exact auxiliary issuer boundary

The `000660` auxiliary dependency may provide only evidence required to establish shared-issuer business/financial facts for SKHY.

Allowed:

- canonical issuer identity;
- issuer relation / security relation;
- filing/financial fact ownership;
- business evidence;
- existing structural provenance needed to bind those facts;
- same-generation source receipts.

Forbidden in the US14 primary packet:

- 000660 current KR stock price;
- 000660 PER/PBR/fPER;
- 000660 technical timing;
- 000660 NewBuyer/Holder valuation;
- 000660 stock message;
- 000660 KR Market role;
- 000660 Core/A/B subject execution;
- transfer of Korean security-level valuation to SKHY ADS.

If the current bridge mechanically requires a KR security-level “technical/local baseline” merely to admit issuer-level business facts, repair that contract.

Do **not** solve this by collecting irrelevant KR price/valuation data before the KR close.

---

# 7. Same-generation issuer dependency

The auxiliary issuer evidence must be from the same fresh source generation as the US14 source seal when the current source policy requires same-generation evidence.

Represent it explicitly in the source generation manifest:

```text
primary_monitored_subjects = 14
auxiliary_issuer_subjects = [000660]
auxiliary_subject_user_message_eligible = false
auxiliary_subject_model_subject_eligible = false
auxiliary_subject_valuation_eligible = false
```

The source hash / whole-seed identity must include the declared auxiliary dependency.

Do not hide it as an undeclared fifteenth monitored stock.

---

# 8. Whole-source completeness contract

Create a scoped whole-source owner such as:

`US14_WITH_DECLARED_AUXILIARY_ISSUER_V1`

Completeness must require:

- all 14 US primary subjects;
- exactly the declared auxiliary issuer dependencies;
- required US Market/context evidence;
- no missing primary role;
- no undeclared KR stock packet;
- no cross-generation bridge;
- no prior-generation substitution.

The contract must distinguish:

```text
PRIMARY_MONITORED
AUXILIARY_ISSUER_ONLY
MARKET_CONTEXT
```

Existing ALL22 whole-source hash logic must remain intact.

---

# 9. Negative source tests

At minimum:

- 13/14 primary subjects -> fail;
- undeclared fifteenth primary stock -> fail;
- missing SKHY auxiliary issuer dependency -> fail;
- stale/prior-generation 000660 auxiliary evidence -> fail;
- auxiliary 000660 valuation injected -> fail;
- auxiliary 000660 stock message eligibility -> fail;
- auxiliary 000660 Core/A/B subject eligibility -> fail;
- KR Market evidence injected without a declared US need -> fail;
- old ALL22 guard still applied to US14 -> fail;
- ALL22 contract changed by the repair -> fail.

---

# 10. Repair C — US-only qualified model topology

Add a production-equivalent US-only model contract.

Suggested name:

`US14_MARKET_CORE_A_B_V1`

It consumes only the immutable fresh US whole-source seed created in Sections 4–8.

Expected primary model subjects:

```text
US Market = 1
US stocks = 14
```

The auxiliary 000660 issuer dependency may appear only as source evidence inside SKHY's permitted business context.

It is not a model subject.

---

# 11. US model-input isolation

Prove:

- US Market receives US Market/context only;
- each US Core receives its own US stock packet;
- SKHY may receive declared shared-issuer business evidence;
- no KR security valuation enters SKHY;
- no 000660 price/technical/valuation facts enter SKHY unless separately authorized in a future contract;
- Pass A receives no forward valuation;
- Pass B NewBuyer/Holder receives qualified valuation including Finnhub fPER(FY1);
- Overall remains independent of forward valuation.

Existing leakage guards remain active.

---

# 12. Repair D — US-only renderer/capture topology

Add an explicit capture contract:

`US14_15_MESSAGE_CAPTURE_V1`

Expected when a standalone US Market message remains canonical:

```text
1 US Market
14 US stock
= 15 messages
```

If the current canonical production renderer no longer emits a standalone Market message, derive the exact expected count from the current canonical renderer and record it.

Do not use the ALL22 `24-message` completeness guard for US-only proof.

Do not modify the 24-message combined contract.

---

# 13. Message-format preservation

Do not redesign the user-facing format.

Keep the current accepted stock-message layout.

Do not reintroduce:

- 기존 등록 가격 규칙
- 데이터 주의
- 다음 확인
- 미확인

For qualified direct-US Finnhub valuation:

```text
PER        = peTTM
PBR        = pbQuarterly
fPER(FY1)  = forwardPE
```

All remain provider-native snapshots for US.

Typed unavailable stays unavailable.

---

# 14. Offline acceptance before any live provider call

Before fresh data:

Require:

1. US14 source-plan exact-set tests PASS;
2. auxiliary issuer-only tests PASS;
3. whole-source seed tests PASS;
4. US-only Market/Core/A/B tests PASS;
5. US-only message capture tests PASS;
6. ALL22 regression PASS;
7. KR8 regression PASS;
8. REV45 forward-policy tests PASS;
9. full pytest PASS;
10. Ruff/diff/knowledge/secret scans PASS.

Network guard must prove:

`actual provider connections = 0`

during tests.

If offline closure fails:

`R2B_R9_REV46_US14_SCOPED_CONTRACT_VALIDATION_GAP`

Stop before fresh collection.

---

# 15. Fresh US target

Only after offline PASS.

Target:

```text
market = XNYS
completed_regular_session = 2026-10-01
KST run date = 2026-10-02
```

Runtime exchange calendar is authoritative.

Verify the latest completed US regular session is still exactly `2026-10-01`.

If not:
stop and report the actual target rather than silently changing dates.

---

# 16. Fresh US source generation

Execute exactly one new clean US14 source generation under the repaired scoped contract.

Primary:

```text
14 US stocks
```

Auxiliary:

```text
000660 issuer-only dependency only if SKHY business bridge actually requires it
```

Plus the exact US Market/context inputs required by the current production architecture.

No partial patching from REV29/REV44/REV45.

No old current values.

Historical fixtures remain test-only.

---

# 17. Provider restrictions

Use existing accepted providers only.

For Finnhub:

- use the normal `profile2` / `stock/metric` acquisition already required by valuation;
- `forwardPE` comes from the same `stock/metric` response;
- do not call `/stock/eps-estimate`.

Hard zero:

```text
Business Quant = 0
FMP = 0
Yahoo fresh collection = 0
Nasdaq Zacks = 0
Alpha Vantage = 0 unless an already-mandatory non-valuation role explicitly requires it
```

Do not add a new provider.

---

# 18. Fresh source seal before models

Before any US model call:

- source acquisition complete;
- exact session/date validated;
- primary vs auxiliary roles validated;
- security identity validated;
- provider-native valuation matrix generated;
- whole-source seed generated;
- all source validators PASS;
- source-only artifact sealed with SHA/manifest.

No provider refresh after this point.

---

# 19. Fresh US model execution

Run the repaired production-equivalent US-only topology.

Model timeout:

`600 seconds per attempt`

Retry:

`maximum 2 retries only for a failed logical call`

Do not rerun successful calls.

A model failure never triggers source recollection.

Continue independent calls where safe and preserve exact failure receipts.

---

# 20. Fresh US messages

Generate the exact US message previews.

No Telegram.

No production delivery.

Seal:

- model lineage;
- validator results;
- exact rendered previews;
- message-count receipt;
- US result ZIP + SHA.

US success terminal:

`R2B_R9_REV46_US14_FRESH_FY1_FORWARDPE_MESSAGE_PROOF_PASS`

---

# 21. US failure boundary

If US mandatory source/model/render validation fails:

- preserve the full bounded result;
- do not start KR;
- do not merge main.

Use the narrowest truthful terminal.

No stale fallback.

---

# 22. Conditional KR continuation

Only after US PASS.

Target KR:

```text
XKRX session = 2026-10-02
```

The current execution may reach this point before the accepted KR completed-session collection boundary.

If the gate is not open:

do not poll continuously and do not sleep for hours.

Seal US result and stop:

`R2B_R9_REV46_US_PASS_PENDING_KR_20261002_COMPLETED_SESSION`

On later resume:

- verify US ZIP/SHA unchanged;
- reuse US success exactly;
- do not recollect US;
- resume from KR stage only.

---

# 23. KR operational timing

Preserve the accepted user policy:

```text
16:10 KST first collection
if incomplete -> 16:15
if still incomplete -> 16:20 full resnapshot
```

For a manual resume after the accepted boundary, perform the appropriate current full-fresh KR proof without synthesizing past scheduler attempts.

Runtime XKRX calendar remains authoritative.

No KR messages on a KR market holiday.

---

# 24. Fresh KR8 proof

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

Use the accepted KR source/model/message architecture.

Preserve KR forward valuation:

```text
latest completed-session KIS unadjusted close
/
qualified KIS house-research FY1 EPS
=
current-price fPER(FY1)
```

Keep optional/unavailable values typed unavailable.

No valuation leakage into Core/A/Overall.

---

# 25. KR source seal → models → messages

Same order:

```text
fresh KR acquisition
→ validators
→ immutable source seal
→ KR Market/Core/A/B
→ renderer
→ exact previews
```

Timeout:

`600 seconds`

Retry:

`max 2 per failed logical model call`

No Telegram.

KR success terminal:

`R2B_R9_REV46_KR8_FRESH_CURRENT_FY1_MESSAGE_PROOF_PASS`

---

# 26. Combined acceptance

Only after US PASS + KR PASS.

Create a combined receipt containing:

- US target date/session/generation/hash;
- KR target date/session/generation/hash;
- provider-call counts;
- model-call/retry lineage;
- US message count;
- KR message count;
- all valuation states;
- auxiliary issuer dependency receipts;
- no stale-generation substitution;
- no Telegram;
- no production DB/scheduler mutation;
- full validation results.

Do not require an obsolete hardcoded message count if the canonical renderer count has changed.

---

# 27. Main merge authorization

Main integration is authorized only after:

```text
offline repaired-contract PASS
fresh US PASS
fresh KR PASS
combined proof PASS
```

Before merge:

1. seal combined result ZIP + SHA;
2. commit accepted REV46 implementation;
3. secret-scan outgoing feature history;
4. preserve feature tip remotely;
5. fresh-fetch origin;
6. record local-main/origin-main/feature relationships.

No force push.
No accepted-history rebase.

---

# 28. Safe main reconciliation

Handle fresh state:

## local main == origin/main
normal merge feature.

## origin/main ancestor of local main
merge feature, then normal push.

## local main ancestor of origin/main
fast-forward local main, then merge feature.

## true divergence
merge origin/main into local main preserving both histories.

If semantic conflicts touch source-policy/schema/model contracts:

`R2B_R9_REV46_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED`

Stop.

Do not guess.

---

# 29. Merged-main validation

On the actual merged main SHA run:

- scoped US14 source tests;
- auxiliary issuer bridge tests;
- US model/capture tests;
- Finnhub FY1 forwardPE tests;
- KR KIS FY1 tests;
- ALL22 regressions;
- full pytest;
- Ruff;
- git diff check as applicable;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- protected production-state comparison.

Only merged-main PASS may be pushed.

---

# 30. origin/main push

Immediately before push:

- fetch origin;
- verify origin/main did not move since reconciliation.

If moved:

`R2B_R9_REV46_REMOTE_MAIN_MOVED_REVIEW_REQUIRED`

If unchanged:

ordinary non-force push only.

Verify final remote SHA.

---

# 31. Still no deployment

Even after main push:

```text
deploy = 0
restart = 0
scheduler mutation = 0
Telegram = 0
production DB write = 0
broker action = 0
```

Stop at repository integration.

---

# 32. Required result states

Possible major terminals:

```text
R2B_R9_REV46_US14_SCOPED_CONTRACT_VALIDATION_GAP
R2B_R9_REV46_US_SOURCE_GAP
R2B_R9_REV46_US_MODEL_MESSAGE_GAP
R2B_R9_REV46_US14_FRESH_FY1_FORWARDPE_MESSAGE_PROOF_PASS
R2B_R9_REV46_US_PASS_PENDING_KR_20261002_COMPLETED_SESSION
R2B_R9_REV46_KR_SESSION_GATE_GAP
R2B_R9_REV46_KR_SOURCE_GAP
R2B_R9_REV46_KR_MODEL_MESSAGE_GAP
R2B_R9_REV46_COMBINED_VALIDATION_GAP
R2B_R9_REV46_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED
R2B_R9_REV46_MERGED_MAIN_VALIDATION_GAP
R2B_R9_REV46_REMOTE_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV46_US_KR_FRESH_MESSAGES_MAIN_INTEGRATION_PASS
```

---

# 33. Deliverables

At minimum include:

## Contract repair
- REV45 integrity
- REV45 remote preservation
- US14 source-plan contract
- auxiliary issuer-only contract
- whole-source completeness contract
- US-only model/capture contract
- offline regression receipts

## Fresh US
- exact source request/receipt ledger
- source-only ZIP + SHA
- primary/auxiliary subject ledger
- valuation matrix
- model lineage
- exact messages
- US proof ZIP + SHA

## Fresh KR, when gate permits
- source-only ZIP + SHA
- KIS FY1 valuation matrix
- model lineage
- exact messages
- KR proof ZIP + SHA

## Combined/main
- combined acceptance
- feature remote preservation
- main relationship/reconciliation
- merged-main validation
- remote push receipt if performed
- production isolation
- secret scan
- final manifest

Suggested final report:

`thesis-monitor-20261002-r2b-r9-rev46-us14-scoped-fresh-us-kr-main-resume-report.zip`

+ `.sha256`.

---

# 34. Core implementation principle

Do not solve the US-only gap by collecting the full KR market early.

Do not solve SKHY issuer evidence by transferring 000660 security valuation.

The correct separation is:

```text
US14 monitored securities
+
declared same-generation issuer-only dependency where required
+
US Market context
=
US-only immutable source seed
```

then:

```text
US source seal
→ US Market/Core/A/B
→ US messages
```

and only after the KR completed-session gate:

```text
fresh KR8
→ KR messages
→ combined proof
→ safe main integration
```
