# Thesis Monitor — R2B-R9-REV29
## Provider-Native Valuation Live Acquisition + NewBuyer/Holder Context Wiring
### Archive-Backed Storage GC → New Full-Fresh All22 → Replay Twice
### Fresh Market/Core/A/B → Exact Sender-Boundary 24-Message Human-Review Proof

**REV29 supersedes every prior unexecuted post-REV28 instruction. Execute only REV29.**

REV28 is the first accepted positive provider-native valuation-owner proof.

It established that source-derived PER/PBR and provider-native PER/PBR are distinct authority contracts.

Qualified bounded examples:

- 005930:
  - Kiwoom PER `41.17`
  - Kiwoom PBR `4.22`
- IBM:
  - Finnhub `peTTM` `19.5016`
  - Finnhub `pbQuarterly` `7.6717`

Those values were fresh REV28 diagnostic responses only.
REV29 must not reuse them as current values.

REV28 also closed:

- exact Kiwoom security-code identity through ka10099 + ka10001;
- exact IBM direct-security identity through authoritative SEC identity + Finnhub profile/metric;
- provider-native atomic snapshot semantics;
- null metric-as-of under explicit provider-latest-snapshot policy;
- common-cohort native-qualified-source integration;
- whole-source code-owner registry parity;
- all validation green.

REV28 deliberately did **not**:

- modify production provider routes;
- start a new full-fresh generation;
- prove all22 valuation coverage;
- inject valuation into models;
- run Market/Core/A/B;
- generate 24 messages.

REV29 must now carry the proven owner through the real fresh pipeline.

---

# 0. Newest SoT

Adopt REV28 as newest implementation/result SoT.

REV28 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev28-native-valuation-snapshot-report.zip`

SHA-256:

`f9b5a28cbb8144f3e9bdf0f9740a42b4be05be08c4f116f49731f7ccc3920170`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- ZIP members:
  `96`
- internal manifest:
  `95/95`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`.

REV28 terminal:

`R2B_R9_REV28_PROVIDER_NATIVE_VALUATION_SNAPSHOT_PASS_READY_FOR_FULL_FRESH`

Repository:

- base:
  `9dfbbd04e95b962629ed4f6b0036dca66346735b`
- branch:
  `codex/r2b-r9-rev28-native-valuation-snapshot`
- instruction:
  `5d35616098faed06af504956d916872bd0f0f610`
- acquisition implementation:
  `e86c7c13419c8b11865732bf11a790eac56c5c12`
- replay/tested implementation:
  `33615d82b3a820e0a55ca680caa2b393dbab10b6`
- final:
  `2c6b7beb1a0c8e6dc7d5ebd20568f6f48b3f4868`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true
- main merge:
  `0`
- remote push:
  `0`.

REV28 bounded execution:

- data requests:
  `4`
- Kiwoom auth:
  `1`
- retries:
  `0`
- models:
  `0`
- messages:
  `0/24`
- full fresh:
  `0`
- destructive GC:
  `0`
- Alpha Vantage:
  `0`.

Validation:

- focused:
  `98 passed`
- full:
  `6991 passed / 63 skipped / 0 failed`
  (`7054 collected`)
- previous `matrix_native_qualified_source_required`:
  CLOSED
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- secret scan:
  PASS.

---

# 1. REV28 qualified contracts to preserve exactly

Preserve:

## 1.1 ProviderNativeValuationSnapshot

Qualified state:

`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`

Allowed:

- deterministic display;
- NewBuyer valuation context;
- Holder valuation context.

Forbidden:

`overall_direction_use = false`

The metric is provider atomic.
It is not Thesis Monitor price/EPS or price/BPS arithmetic.

## 1.2 Snapshot time semantics

Keep separate:

- retrieval timestamp;
- metric_asof;
- denominator period.

For provider latest snapshot:
- retrieval timestamp is owned;
- metric_asof may be null;
- underlying denominator period may be null.

Do not invent dates.

Do not call the metric a same-session recomputation.

## 1.3 Kiwoom

- ka10099 owns exact provider security-code/list-market identity;
- ka10001 owns provider-native PER/PBR fields for that exact code;
- PER retains provider weekly/earnings-season update caveat;
- PBR retains unknown-metric-as-of caveat.

## 1.4 Finnhub direct security

Requires:
- authoritative direct-security identity;
- profile2 ticker/exchange/currency compatibility;
- stock/metric symbol compatibility.

Qualified fields:
- `peTTM` → provider TTM PER snapshot;
- `pbQuarterly` → provider quarterly PBR snapshot.

## 1.5 ADR/fPER

Preserve:

- TSM/SKHY and any other depositary security:
  no home-share valuation transfer without exact ADR owner;
- fPER:
  unavailable while exact estimate-horizon owner/entitlement is absent.

No `forwardPE` substitution.

---

# 2. REV28 values are fixtures, not REV29 current values

Do not reuse:

- 005930 `41.17 / 4.22`;
- IBM `19.5016 / 7.6717`;

as current REV29 valuation.

They are regression fixtures only.

REV29 must request new provider-native values in the new fresh generation.

Any exact equality/difference to REV28 is incidental.

No target fitting.

---

# 3. Production acquisition integration is required

REV28 reported:

`production_provider_routes_unchanged = true`

Therefore positive owner logic exists, but the normal full-fresh provider plan does not yet acquire the required valuation routes.

REV29 must integrate provider-native valuation into the normal sealed full-fresh plan.

This is mandatory before the live run.

No diagnostic side-channel acquisition after source freeze.

No post-model valuation refresh.

---

# 4. KR production valuation acquisition

Current monitored KR roster:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280.

Build the valuation plan from the actual roster/security registry at runtime.

Do not hardcode coverage results.

## 4.1 Security-list identity

For every distinct required Kiwoom market type in the current KR roster:

acquire one fresh ka10099 list response unless the official continuation contract requires bounded continuation.

Expected current roster is KOSPI-only, but runtime source identity is authoritative.

Use the exact current market-type plan.

## 4.2 Basic-information snapshot

For each KR monitored security:

one fresh:

`ka10001`

request for the exact six-digit code.

Maximum expected current KR valuation data calls:

- ka10099:
  1 for KOSPI-only current roster;
- ka10001:
  8.

If a runtime roster contains another market:
one additional exact list call is permitted.

No repeated calls for favorable values.

## 4.3 Metric qualification

For every KR security independently:

- exact code/list identity PASS;
- exact ka10001 code PASS;
- PER field valid → qualified provider snapshot;
- PBR field valid → qualified provider snapshot;
- missing/zero/sentinel/malformed → typed unavailable.

One unavailable metric does not make the stock source fail.

fPER remains separately unavailable.

---

# 5. US production valuation acquisition

Current US roster is 14 subjects.

For each subject, use current authoritative security identity.

Provider-native Finnhub valuation may qualify only when:
- exact monitored ticker;
- exact direct listed security;
- profile2 binding;
- stock/metric binding;
- exchange/currency/security contract PASS;
- not a disallowed depositary/home-share mismatch.

For every US subject for which the sealed plan cannot prove it is ineligible before provider acquisition:

acquire:

1. Finnhub profile2;
2. Finnhub stock/metric.

A known, source-owned depositary security may be skipped before metric acquisition only if the existing exact
security owner proves that skip deterministically.

Do not skip based on a ticker/name heuristic.

Maximum valuation add-on:
- `2 × 14 = 28` Finnhub data requests
  if no subjects are safely pre-excluded.

No Alpha Vantage.

No alternate valuation vendor.

---

# 6. US identity expansion

REV28 proved IBM only.

REV29 must evaluate every current US subject independently.

Possible states include:

- `QUALIFIED_DIRECT_SECURITY`
- `UNAVAILABLE_SECURITY_IDENTITY`
- `UNAVAILABLE_ADR_CONVERSION`
- `UNAVAILABLE_EXCHANGE_MISMATCH`
- `UNAVAILABLE_CURRENCY_MISMATCH`
- other exact typed reason.

Do not require all direct securities to qualify.

Do not infer that MU or another ticker qualifies because IBM did.

Use current authoritative SEC/security-master evidence and current Finnhub response.

For GOOGL/CPNG/RXRX or other classed securities:
exact ticker/class/listing binding is mandatory.

For TSM/SKHY/WRD or any depositary security:
fail closed unless the exact provider response itself is proven to own the traded depositary security valuation.

No home-share transfer.

---

# 7. Valuation is optional source coverage, but typed state is mandatory

Fresh stock source qualification remains:

`22/22`

when every stock has an exact valuation state even if some metrics are unavailable.

For every security require exactly:

- PER state;
- PBR state;
- fPER state.

Possible PER/PBR states:
- qualified provider latest snapshot;
- typed unavailable.

fPER:
- typed unavailable unless an independently qualified exact horizon owner unexpectedly exists under the already-approved
source inventory.

No numeric-coverage target.

No source failure merely because valuation is unavailable.

---

# 8. Provider-native valuation fact materialization

For every qualified PER/PBR:

materialize a valuation fact + numeric-registry row owned by the current valuation view.

Required:
- exact security ID;
- provider;
- route;
- provider field;
- numeric value;
- retrieval timestamp;
- nullable metric_asof;
- provider caveat;
- snapshot/raw/receipt hashes;
- `overall_direction_use=false`.

Do not assign `as_of_date` from retrieval time if metric_asof is null.

If the generic fact schema cannot represent null metric date safely:
use the provider-snapshot metadata field and the exact existing null-as-of policy.
Do not fabricate a date merely to satisfy a generic numeric renderer.

---

# 9. NewBuyer/Holder model-context contract

REV28 authorized snapshot permissions:

- display;
- new_buyer valuation context;
- holder valuation context.

REV28 used:

`model_injection = 0`

because no models ran.

REV29 must explicitly wire qualified provider-native valuation to the **non-directional NewBuyer/Holder calibration context**
before running models.

Do not inject valuation into:
- Core directional evidence;
- Pass A directional/business evidence;
- any direction bucket;
- any supporting/contradicting ref used to establish Overall business direction.

---

# 10. B valuation context only

If the existing architecture places NewBuyer/Holder calibration in Pass B:

add a dedicated typed block such as:

`valuation_context`

containing only:
- PER qualified/unavailable state;
- PBR qualified/unavailable state;
- fPER qualified/unavailable state;
- qualified numeric value;
- provider snapshot label;
- caveats;
- exact non-directional ownership receipt.

The prompt/contract must state:

valuation may affect:
- NewBuyer attractiveness;
- Holder add/hold/reduce context;
- valuation-specific reasons;
- confidence/caution where the current accepted policy permits.

valuation may **not** independently alter:
- Overall direction;
- business direction score;
- directional supporting refs;
- directional contradicting refs.

If the repository has a different dedicated calibration stage:
use that existing stage rather than creating an unnecessary new stage.

---

# 11. Direction-isolation validator

Add deterministic validation.

For every provider-native valuation fact:

- no Core directional claim may cite it;
- no A directional claim may cite it;
- no B Overall-direction reason may use it as the sole directional evidence;
- no direction bucket may contain its ref;
- `overall_direction_use=false`.

The final accepted decision may mention valuation in:
- NewBuyer reason;
- Holder reason;
- valuation section.

Do not force Overall direction to equal a prior run.
Fresh business evidence may legitimately change it.

The validator should check evidence authority, not target outputs.

---

# 12. Offline B visibility proof before live run

Using fictional/synthetic fixtures through production owners:

prove:

## Qualified valuation
- PER/PBR appear in the B valuation-context block;
- do not appear in Core;
- do not appear in A;
- direction refs cannot cite them;
- NewBuyer/Holder context can cite them.

## Unavailable valuation
- typed unavailable state appears;
- no fake number;
- no hidden previous value.

## ADR
- unavailable;
- no home-share value.

## fPER
- unavailable;
- no generic forwardPE fallback.

No model calls.

---

# 13. Detailed message valuation renderer

Preserve REV28's qualified lines.

Examples of shape only:

- `PER: xx.xx배 · Kiwoom snapshot`
- `PBR: x.xx배 · Kiwoom snapshot`
- `PER: xx.xx배 · Finnhub TTM snapshot`
- `PBR: x.xx배 · Finnhub quarterly snapshot`
- `fPER: 판단 자료 부족`.

Use actual current values only.

Do not show metric_asof when null.

Do not show retrieval timestamp as metric date.

Provider snapshot qualifier is mandatory for provider-native numbers.

---

# 14. Known detailed-renderer backlog is NOT silently fixed in REV29

The existing detailed-message backlog includes:
- optional detailed sections not always materialized;
- English business-performance prose in some accepted outputs;
- static/low-information evidence-maturity rendering.

Do not perform broad renderer redesign in REV29.

REV29's renderer change is limited to:
- qualified valuation lines;
- exact provider snapshot qualifier;
- required valuation binding.

Reason:
source/model/valuation proof must remain independently auditable.

Record the renderer backlog in the result bundle for the next renderer-only task.

---

# 15. Pre-GC offline implementation gate

Before destructive GC require:

- production valuation-plan builder PASS;
- KR ka10099/ka10001 slot planning PASS;
- US profile2/metric slot planning PASS;
- exact per-security eligibility/denial contract PASS;
- provider-native fact materialization PASS;
- B-only valuation context PASS;
- direction isolation PASS;
- detailed valuation renderer PASS;
- ADR/fPER negative controls PASS;
- canonical code-owner registry parity PASS;
- whole-source replay fixture PASS;
- Pass-A visibility regression PASS;
- Market directional/display regression PASS;
- current-price/technical regressions PASS;
- all source-owner regressions PASS;
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

Only then execute storage GC.

---

# 16. Archive-backed storage GC is mandatory

REV28 final free bytes:

`11,027,091,456`

This is below the standing full-fresh precollection floor:

`12 GiB`

Therefore no full-fresh provider call may begin before GC.

Verify immutable archives first, including at minimum:

- accepted REV24 source/result;
- REV24 retry continuation;
- REV24 24-message human-review;
- REV25 report/review;
- REV26;
- REV27;
- REV28;
- REV24 blind-review audit artifacts.

For every archive:
- SHA PASS;
- CRC PASS;
- manifest PASS where present.

---

# 17. Minimal REV28 regression fixture before GC

Before deleting any expanded REV28 working evidence, seal a minimal fixture containing:

## KR
- ka10099 exact-security identity input/output needed for 005930 regression;
- ka10001 response/receipt;
- qualified PER/PBR snapshot receipts.

## US
- IBM authoritative SEC identity;
- profile2 response/receipt;
- metric response/receipt;
- qualified PER/PBR snapshot receipts.

## Negatives
- ADR denial fixture;
- fPER entitlement denial fixture;
- wrong-code/exchange/current-generation negative data required by tests.

Include:
- manifest;
- hashes;
- explicit fixture-only marker.

The fixture must not be used as current data in REV29 live generation.

---

# 18. GC eligible scope

After archive + fixture verification, safely remove archive-backed superseded expanded data including:

- REV28 expanded probe/report internals not needed by registered fixture;
- REV27 expanded probe data;
- REV26 expanded probe data;
- REV25 expanded diagnostic data;
- superseded older R9 live expanded generations still present;
- obsolete temporary validation exports;
- eligible clean old worktrees.

Use:

`git worktree remove`

for worktrees.

Do not raw-delete worktrees.

No aggressive shared-Git pruning.

---

# 19. Protected storage scope

Never auto-delete:

- REV29 current worktree;
- operating/main;
- shared `.git`;
- production DB/WAL;
- credentials/.env;
- scheduler state/config;
- immutable ZIP/SHA archives;
- blind-review audit artifacts;
- registered minimal fixtures;
- active new generation.

Record exact protected paths.

---

# 20. GC receipts and disk thresholds

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`.

Record:
- before free bytes;
- candidate paths/sizes;
- archive proof;
- deleted/skipped paths/reasons;
- after free bytes;
- actual reclaimed bytes;
- worktree removals.

Hard precollection:
`>= 12 GiB`

Preferred:
`>= 14 GiB`

Hard premodel:
`>= 10 GiB`.

If safe GC cannot reach 12 GiB:

`R2B_R9_REV29_STORAGE_GC_HEADROOM_GAP`

Do not delete protected evidence to force a run.

---

# 21. New REV29 full-fresh generation

Only after:
- offline implementation gate PASS;
- GC PASS;
- free >= 12 GiB;

start a completely new generation.

Do not resume REV24/REV28.

Do not reuse mutable current values.

Recompute:
- query time;
- US/KR calendars;
- completed sessions;
- source plans;
- Market/macro/FX/night;
- financial;
- events;
- technical;
- current price;
- quality;
- valuation;
- exact provider budgets.

Alpha Vantage:

`0`

unless a separately approved change exists.
REV29 itself does not authorize Alpha Vantage.

---

# 22. External transmission approval

The user has requested that external transmission be explicitly approved in the work instruction.

REV29 explicitly approves:

## Provider/API reads
Read-only requests to the existing declared provider inventory plus the REV28-proven valuation routes:

- Kiwoom ka10099;
- Kiwoom ka10001;
- Finnhub profile2;
- Finnhub stock/metric;

as part of the sealed REV29 full-fresh plan.

No new provider.

## Model transmission
After all source/replay/preflight gates PASS:

source/model payload transmission to the existing official:

`GPT-5.6 Sol / xhigh`

Thesis Monitor model runner is explicitly approved.

Use only the existing frozen Market/Core/A/B batching/transport contract.

No fallback model.
No judge model.
No semantic/schema result-driven retry.
No selective ticker rerun.

## Result upload
Secret-scanned:
- result ZIP/SHA;
- source-only review ZIP/SHA;
- 24-message human-review ZIP/SHA

may be uploaded to the existing iCloud Drive / Thesis Monitor folder.

Do not request redundant approval for these exact transmissions.

---

# 23. Production recipient delivery remains disabled

REV29 proof must use:

`delivery_disabled = true`

for sender-boundary capture.

Still prohibited:
- Telegram recipient sends;
- production decision/warning DB writes;
- scheduler mutation;
- broker/trading action;
- deploy;
- main merge;
- remote push;
- service restart.

Provider/API and approved model transmissions are proof actions, not prohibited recipient delivery.

Telegram:

`0`

---

# 24. Fresh source acquisition — all22

Run all current source owners for US14 + KR8.

Include:
- completed-session price;
- OHLCV/current-effective technical;
- financial/business;
- selected financial owner;
- events;
- quality;
- flow/positioning;
- Market context;
- provider-native valuation slots.

No prior mutable current value.

---

# 25. Fresh valuation state matrix

Create:

`fresh-valuation-state-matrix.json`

For every 22 subjects and each metric:

- PER state;
- PBR state;
- fPER state;
- value if qualified;
- provider;
- route/field;
- exact security-identity state;
- snapshot retrieval time;
- metric_asof;
- caveats;
- denial reason;
- source hashes;
- whole-source fact IDs.

Report counts:
- qualified PER;
- qualified PBR;
- unavailable by reason;
- ADR unavailable;
- fPER unavailable.

No minimum numeric coverage target.

---

# 26. Fresh full-source closure

Require:

- stock source state:
  `22/22`
- Market:
  `2/2`
- financial/events:
  all typed complete;
- price/technical:
  all typed complete;
- quality:
  all typed complete;
- valuation:
  `22/22` exact metric-state triplets;
- macro/FX/night:
  typed complete.

Valuation unavailability does not fail a stock when the typed state is correct.

Create:
- FullSourceRunSeed;
- US source packet;
- KR source packet;
- combined packet;
- authority graph;
- code-owner registry receipt.

---

# 27. Source-only blind-review artifact BEFORE models

Before any model transmission, seal a dedicated artifact:

`r2b-r9-rev29-source-only-review.zip`

It must contain enough current fresh evidence to permit an independent analyst to judge:

- Market US/KR;
- business/financial direction;
- events;
- quality;
- current price;
- technical;
- flow;
- valuation.

It must exclude:

- Market model output;
- Core output;
- Pass A output;
- Pass B output;
- final 24 messages;
- any Monitoring AI decision label.

Include:
- source-only manifest;
- SHA;
- generation ID;
- source graph hashes.

Once sealed, it is immutable.

This exists so the later human-vs-AI comparison can again be genuinely blind.

---

# 28. Replay twice

Freeze the source corpus.

Disable network.

Replay entire source graph twice.

Require exact semantic equality for:

- stock source 22;
- Market source/views;
- financial;
- events;
- current price;
- technical;
- quality;
- provider-native valuation receipts;
- valuation facts/numeric registry;
- valuation B-context blocks;
- macro/FX/night;
- authority graph;
- code-owner registry.

No provider call during replay.

Then issue normal current source-adapter qualification only if all gates PASS.

---

# 29. Pass-A visibility

Require the existing A visibility contract unchanged.

Provider-native valuation must be absent from A directional inputs.

No valuation ref may enter:
- directional supporting refs;
- directional contradicting refs;
- directional evidence buckets.

Regression must explicitly test this.

---

# 30. Pass-B valuation visibility

Before real B model calls, materialize and audit the exact B input.

For each subject:
- qualified PER/PBR appear only in the valuation-context surface;
- unavailable states appear without old numeric value;
- snapshot provider/caveat is visible as context;
- `overall_direction_use=false`;
- source refs/hashes exact.

Create:

`pass-b-valuation-visibility.json`

No model call if this gate fails.

---

# 31. Pre-model disk guard

Immediately before model transmission:

`free >= 10 GiB`

If below:

`R2B_R9_REV29_DISK_GUARD`

Preserve frozen source.
Do not call models.

---

# 32. Fresh AI proof

After all gates PASS:

run fresh:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`.

Use current frozen batching.

No prior model-output reuse.

No fallback/judge.

No source refresh caused by model result.

No semantic/schema retry.

Any transport retry must comply with the repository's already-authorized frozen transport policy.
REV29 does not create a new retry permission beyond that policy.

---

# 33. Valuation reasoning boundaries in accepted model results

Audit all accepted outputs.

Qualified valuation may appear in:
- NewBuyer reasoning;
- Holder reasoning;
- explicit valuation context.

It must not be the authority for:
- Overall direction;
- business thesis direction;
- directional supporting refs;
- directional contradicting refs.

If the model violates this:
reject the affected output under the existing validation contract.
Do not silently strip the reason and accept.

---

# 34. Final Market messages

Preserve accepted REV24 Market display-view contract.

US:
- current configured indices/proxies;
- latest-published display-eligible macro values with true observation dates;
- model judgment/confidence;
- sectors where qualified;
- KOSPI200 night D/W/M or `자료 부족`.

KR:
- KOSPI/KOSDAQ completed-session values;
- model judgment;
- sectors where qualified;
- USD/KRW with correct display/currentness contract.

No valuation change is authorized for Market direction.

---

# 35. Final stock messages

Preserve current accepted detailed renderer except the REV28-qualified valuation line behavior.

Valuation section must show per metric:

## qualified
Example form:
`PER: 19.50배 · Finnhub TTM snapshot`

## unavailable
`PER: 판단 자료 부족`

## fPER
keep unavailable when no exact estimate owner.

No provider metric appears without exact current source binding.

No prior generation value.

No cross-security transfer.

Do not render internal hashes/refs/debug labels.

---

# 36. Exact sender-boundary capture

Use the actual production sender payload builder with recipient delivery disabled.

Capture:

- MARKET_US
- MARKET_KR
- US14 stock messages
- KR8 stock messages
- ALL_MESSAGES.md.

Total:

`24/24`

No post-hoc reconstruction.

Telegram send count:

`0`

---

# 37. Human-review archive

Create:

`r2b-r9-rev29-24-message-human-review.zip`

Include:
- exact 24 sender payloads;
- hashes;
- valuation state matrix;
- valuation visibility/use audit;
- source 22 matrix;
- Market source/views;
- replay receipts;
- model ledger;
- validation;
- production isolation.

Upload only after secret scan.

---

# 38. REV24 vs REV29 comparison

Create a deterministic structural comparison against accepted REV24.

Compare:
- valuation section coverage;
- provider snapshot labels;
- fPER unavailability;
- missing/extra message sections;
- direction labels;
- NewBuyer/Holder labels.

Do **not** treat direction differences as failures merely because they differ from REV24.

Flag only:
- unsupported source use;
- authority leak;
- valuation-driven Overall direction;
- renderer contract regression;
- missing required sections.

---

# 39. No blind human judgment inside execution session

The execution session must not generate a human-style investment judgment to match the AI.

It should only seal:

`r2b-r9-rev29-source-only-review.zip`

before models.

Independent source-only judgment and post-reveal comparison will be performed outside the execution session after the
result is returned.

Do not include model labels in the source-only archive.

---

# 40. Success terminal

Use only:

`R2B_R9_REV29_FULL_FRESH_NATIVE_VALUATION_24_MESSAGE_PASS_READY_FOR_BLIND_HUMAN_REVIEW`

Require:

1. REV28 provider-native snapshot contract preserved;
2. production valuation acquisition integrated;
3. offline valuation planning PASS;
4. B-only valuation context PASS;
5. direction isolation PASS;
6. archive-backed GC PASS;
7. precollection free >=12 GiB;
8. new full-fresh generation;
9. no prior mutable source reuse;
10. stock source 22/22;
11. Market 2/2;
12. valuation exact typed states 22/22;
13. source-only review ZIP sealed before models;
14. replay twice PASS;
15. A visibility PASS;
16. B valuation visibility PASS;
17. premodel free >=10 GiB;
18. Market/Core/A/B complete;
19. accepted outputs pass valuation-use audit;
20. exact messages 24/24;
21. qualified provider-native valuation rendered where owned;
22. unavailable metrics remain honest;
23. ADR/home-share transfer 0;
24. fPER fabrication 0;
25. Alpha Vantage 0;
26. Telegram 0;
27. production DB/scheduler/broker/deploy mutations 0;
28. secret scan PASS;
29. source-only + human-review archives generated;
30. approved iCloud upload complete.

---

# 41. Honest stop terminals

- `R2B_R9_REV29_VALUATION_PLAN_INTEGRATION_GAP`
- `R2B_R9_REV29_VALUATION_MODEL_VISIBILITY_GAP`
- `R2B_R9_REV29_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV29_STORAGE_GC_ARCHIVE_GAP`
- `R2B_R9_REV29_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV29_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV29_VALUATION_SOURCE_PARTIAL`
- `R2B_R9_REV29_REPLAY_GAP`
- `R2B_R9_REV29_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV29_DISK_GUARD`
- exact model/render failure.

Do not lower source/identity requirements to avoid a stop.

---

# 42. Required validation

## Acquisition
- KR roster → exact ka10099 market plan;
- each KR code → ka10001 slot;
- US profile/metric slot planning;
- known source-owned ineligible security skip;
- wrong identity negative;
- old-generation/cache negative.

## Valuation
- native PER/PBR positive;
- unavailable field/sentinel;
- exact security mismatch;
- ADR negative;
- fPER unavailable;
- no source-derived denominator bypass.

## AI visibility
- absent Core;
- absent A;
- present B valuation context when qualified;
- unavailable state without old value;
- direction ref prohibition.

## Replay
- native raw/receipt/snapshot equality;
- current valuation view equality;
- B valuation context equality.

## Renderer
- qualified snapshot labels;
- unavailable metrics;
- no false metric date;
- no internal leak.

## Full system
- all22;
- Market2;
- financial/events;
- current price/technical;
- quality;
- valuation;
- macro/FX/night;
- replay twice;
- Market/Core/A/B;
- exact24.

## Repository
- canonical code registry;
- focused tests;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

---

# 43. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV28 archive identity/SHA
- repository identities
- changed-file inventory
- validation
- bundle manifest.

## Storage
- GC plan/result/protected/fixtures
- before/after free bytes
- removed/skipped paths.

## Fresh acquisition
- sealed provider plan
- provider counters
- valuation slot inventory
- source 22 matrix
- Market2.

## Valuation
- fresh valuation state matrix
- qualified snapshot receipts
- exact security identity receipts
- ADR/fPER denials
- numeric registry audit
- B valuation-context audit
- direction-isolation audit.

## Blind review
- source-only review ZIP/SHA identity proving it was sealed before first model call.

## AI
- Market/Core/A/B ledger
- model transport counters
- accepted-output valuation-use audit.

## Messages
- exact24
- message hashes
- human-review ZIP/SHA
- REV24 structural comparison.

## Safety
- Alpha 0
- Telegram 0
- production writes 0
- scheduler/broker/deploy 0
- secret scan.

---

# 44. Final principle

REV28 proved that useful PER/PBR can be restored without weakening provenance by treating official provider ratios as
atomic provider-latest snapshots for the exact traded security.

REV29 must now prove that contract in the **real current generation**, not only in bounded diagnostic fixtures.

The valuation value may improve NewBuyer/Holder context, but it is not business-direction evidence.

Numeric coverage is not a target:
- qualify exact securities;
- deny unsupported securities;
- preserve ADR/fPER boundaries;
- show the user the provider snapshot honestly.

Once the source-only corpus is sealed, models may run and exact 24 messages may be captured.
The independent human source-only judgment must be performed only afterward, outside the execution session, so the
blind comparison remains genuine.
