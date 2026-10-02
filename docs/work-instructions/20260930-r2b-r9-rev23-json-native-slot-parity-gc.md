# Thesis Monitor — R2B-R9-REV23
## JSON-Native FPI Slot-Plan Persistence/Replay Parity
### Archive-Backed Storage GC → New Full-Fresh All-Source Requalification → Replay Twice → Fresh Market/Core/A/B → Exact Detailed 24-Message Proof

**REV23 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV23.**

REV22 successfully implemented and offline/live-proved the SEC logical same-cell/same-target
reference grouping contract.

REV22 then started a new full-fresh generation and captured the complete provider plan.

It stopped during fresh source replay on exactly one serialization-boundary P1:

`fpi_document_slot_plan_replay_mismatch`

Affected subjects:

- TSM
- WRD

The failure is not a semantic plan difference.

REV22 post-stop diagnostic proves:

### TSM
- persisted SHA:
  `6008a0336772a4bd0b8f42db4d87ec901cfcaa6ba215653cbda5b70d1f059586`
- replay SHA:
  same
- `canonical_json_equal = true`
- structural Python equality:
  false
- difference count:
  `156`

### WRD
- persisted SHA:
  `3d78fff70d030555bd48ac45da39af4f05fd891d0e887bb17fe1f82138c1fbf6`
- replay SHA:
  same
- `canonical_json_equal = true`
- structural Python equality:
  false
- difference count:
  `329`

Across both subjects, every one of the **485** detected differences is:

- path suffix:
  `target`
- persisted type:
  `list`
- replay/in-memory type:
  `tuple`
- JSON value equality:
  `true`.

The replay recomputation carries a Python tuple returned by the SEC reference resolver, while the
persisted JSON representation necessarily reloads the same two values as a list.

REV23 must close this representation contract **at the plan construction boundary**.

Do not:
- weaken strict persisted-plan equality;
- replace equality with hash-only acceptance;
- special-case TSM or WRD;
- ignore tuple/list differences globally;
- JSON-roundtrip arbitrary objects at comparison time to hide type drift;
- alter source classification;
- alter the logical-reference grouping/purpose rules;
- alter financial-document limits;
- reuse REV22 mutable source under changed code.

The persisted/replayed plan contract itself must become JSON-native and exactly round-trip stable.

After offline closure:
1. extract minimal REV22 parity fixtures;
2. verify immutable REV22 archive;
3. execute storage GC;
4. create a new full-fresh generation;
5. require source 22/22;
6. whole-source replay twice;
7. Pass-A visibility replay;
8. fresh Market/Core/A/B;
9. exact 24 sender-boundary messages.

---

# 0. Newest SoT

Adopt REV22 as newest implementation/result SoT.

REV22 result ZIP SHA-256:

`a48fc5cca70dc80e85f6fdb9557313e98116884f2d9d14db2924cdf1f0ffdf18`

Uploaded sidecar:
exact match.

Independent archive verification:

- ZIP CRC:
  PASS
- members:
  `7873`
- internal manifest entries:
  `7872`
- missing:
  `0`
- SHA mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV22_LIVE_ADAPTER_REQUALIFICATION_GAP`

Detail:

`fpi_document_slot_plan_replay_mismatch`

Repository:

- branch:
  `codex/r2b-r9-rev22-logical-cell-reference-gc`
- base:
  `57bed90597997173639d5702a9daab67c8eb5cc7`
- instruction:
  `3e0f515187d3806e9776517e3b1fc83cca95c367`
- implementation/final:
  `89ca33e8ee831ea64550fd905f1f055b5a4b5bc0`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true
- local-only:
  true
- main merge:
  `0`
- remote push:
  `0`

REV22 validation:

- focused:
  `1022 PASS`
- full:
  `6866 PASS / 63 unchanged skips`
- Ruff:
  PASS
- diff:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- production side effects:
  `0`

Fresh generation:

`rev22-live-20260929T144328Z`

Provider attempts:

`538`

Model calls:

`0`

Exact messages:

`0/24`

Post-stop diagnostic:

- subject statuses:
  `20 PASS / 2 EXCEPTION`
- exceptions:
  `TSM`, `WRD`
- qualification override:
  `false`
- source mutation:
  `0`
- additional network calls:
  `0`.

---

# 1. Preserve REV22 structural-owner success

Do not reopen REV22's SEC logical-reference design.

Accepted:

- same accession;
- same source primary;
- same row;
- same cell;
- same canonical target;
- contiguous ordered anchors;
- no meaningful interrupting text/reference;
- exact raw anchor/span provenance;
- grouping before purpose routing.

REV22 offline matrix:

`13/13 PASS`

Purpose routing:

- 12 annual legal/governance rows:
  non-financial;
- current 8-anchor TSM 6-K:
  financial.

Financial attachment cap remains:

`2`

Current selected TSM financial period remains:

`2026-06-30`

in the accepted offline/source-owner contract.

Do not loosen these rules in REV23.

---

# 2. Exact REV22 serialization failure

Current runtime representation path:

SEC resolver
→ logical cell inventory
→ FPI document slot plan
→ in-memory plan
→ JSON persistence
→ JSON reload
→ replay/recomputed plan
→ strict equality

The SEC resolver currently exposes a `target` pair as a Python tuple:

`(canonical_href, document_identity)`

The logical inventory retains this runtime `target`.

On JSON persistence:

tuple
→ JSON array
→ Python list after reload.

Recomputed plan retains tuple.

Result:

- semantic JSON equal;
- canonical JSON SHA equal;
- Python object equality false.

This is a type contract defect.

---

# 3. Do not solve at the equality checker

Forbidden fixes:

- `if tuple/list then compare equal`;
- recursive tuple→list conversion only inside the equality checker;
- compare canonical JSON hashes instead of exact plan object;
- disable persisted equality;
- ignore `target` fields;
- loosen replay.

The source-plan public contract itself must emit one JSON-native representation.

The strict persisted plan equality remains unchanged and must PASS naturally.

---

# 4. JSON-native persisted contract

Every object stored in a persisted/replayed FPI slot plan must be representable exclusively with:

- `null`
- boolean
- integer/finite number
- string
- list
- object/dict with string keys.

No tuple, set, Path, bytes, datetime object, enum object or other Python-runtime-only structure may
remain in the plan returned by the public slot-plan constructor.

This does **not** require converting internal local helper variables.

It applies at the persisted/public plan boundary.

---

# 5. Typed ReferenceTarget contract

Replace the ambiguous runtime tuple surface with a typed JSON-native representation.

Repository naming permitting:

`ReferenceTarget`

Fields:

- `canonical_href: str`
- `document_identity: str`

or equivalent exact names.

Preferred persisted representation:

```json
{
  "canonical_href": "...",
  "document_identity": "..."
}
```

A two-element anonymous list is less desirable because positional meaning is weaker.

If a typed ContractModel is used:

- internal access may use attributes;
- persistence must use `model_dump(mode="json")`;
- any parent persisted structure must receive the JSON-native dump, not the raw model object.

Do not use tuple in the public inventory/slot-plan JSON surface.

---

# 6. Resolver boundary

The SEC href resolver may internally compute two values however convenient.

But the boundary consumed by:

`sec_logical_cell_reference.logical_reference_inventory`

must normalize the resolved target into the typed JSON-native target before the inventory row is
returned.

After this point:

- no caller should receive a raw `(href, document_identity)` tuple as part of persisted inventory;
- ExactReferenceAnchor continues owning explicit string fields:
  - canonical_href
  - document_identity;
- inventory audit rows use the same named target shape.

---

# 7. One canonical target representation everywhere

Use the same target representation in:

- cell anchor inventory;
- logical reference group provenance;
- FPI filing document graph;
- document-slot plan;
- persisted candidate plan;
- replay recomputation;
- audit/report output;
- tests.

Do not let one layer use tuple and another use dict/list.

No dual representation.

---

# 8. Round-trip invariant

For every public persisted FPI slot plan:

```python
plan == json.loads(json.dumps(plan, ...))
```

must be true under the repository's exact canonical JSON encoder/decoder behavior.

Also require:

```python
persist(plan)
reload(plan) == recompute_same_plan(...)
```

without normalization at equality time.

Create a receipt:

`fpi-slot-plan-json-roundtrip.json`

with:

- ticker;
- original Python type audit;
- persisted SHA;
- reloaded SHA;
- replay SHA;
- exact equality;
- non-JSON-native path count;
- contract version.

---

# 9. Recursive JSON-native validator

Add one deterministic validator for persisted slot-plan output.

It must recursively fail if it finds:

- tuple;
- set;
- bytes;
- Path;
- datetime/date object;
- custom object/model not already dumped;
- non-string dictionary key;
- NaN/Infinity where current canonical JSON forbids them.

This is a pre-persistence assertion.

Do not silently coerce arbitrary unknown types.

For specifically approved typed models:
the plan builder must explicitly dump them first.

---

# 10. Exact REV22 diagnostic regression

Use the sealed REV22 diagnostic fixture.

Required:

## TSM
Old behavior:
- differences:
  `156`
- all:
  persisted list vs replay tuple at `.target`
- JSON semantic equality:
  true.

New behavior:
- differences:
  `0`
- exact Python equality:
  true
- canonical JSON equality:
  true
- persisted SHA == replay SHA.

## WRD
Old behavior:
- differences:
  `329`
- same target type issue.

New behavior:
- differences:
  `0`
- exact Python equality:
  true
- canonical JSON equality:
  true.

No source-purpose changes in this regression.

---

# 11. Target representation negative controls

Require:

- typed target object → PASS;
- raw tuple injected at public plan boundary → fail;
- list injected where target object is required → fail schema/type contract;
- missing canonical_href → fail;
- missing document_identity → fail;
- extra unknown target key → fail under current strict model policy;
- target strings changed → equality/hash fail;
- cross-document target swap → fail;
- same JSON values with wrong runtime type before public dump → public boundary must reject or explicitly typed-dump, not leak.

---

# 12. Pydantic/runtime collection discipline

Pydantic models may use tuples internally if the model contract requires immutable membership.

However:

- raw Pydantic model objects must never be embedded into persisted dicts;
- use `model_dump(mode="json")` at the owned public serialization boundary;
- persisted structures are JSON-native.

For `LogicalCellReferenceGroup.anchors`, existing tuple membership may remain inside the typed model,
provided every persisted group is emitted through JSON mode.

Do not change tuple semantics inside a model merely to chase this failure if the public dump is already
JSON-native.

The observed defect is the raw inventory `target`, not the typed group `anchors`.

---

# 13. Acquisition → disk → replay contract test

The existing offline test passed in-memory collector output and therefore missed the defect.

Add a mandatory integration test that follows the real persistence boundary:

1. build/recompute slot plan from fixture source;
2. JSON-write it with the real durable writer;
3. close/read file from disk;
4. JSON-load;
5. recompute plan again independently from the immutable fixture;
6. exact Python equality;
7. exact canonical hash equality.

Use both:
- TSM
- WRD

because both exposed the bug.

Do not mock the persistence step away.

---

# 14. Production replay path test

Use the exact function chain employed by the fresh controller/replay:

acquired source receipts
→ financial owner candidate/slot planning
→ persisted plan
→ replay load/recompute
→ equality guard.

Run without network.

Require:
- TSM PASS;
- WRD PASS;
- no special ticker branch.

This test must not use a hand-built plan with already-JSON-native target values.

---

# 15. All22 offline source readiness

After serialization repair:

run current registered offline source fixtures.

Require:

- all22 valid source states;
- TSM logical routing unchanged;
- WRD financial owner unchanged;
- SNDK 52/53 unchanged;
- SKHY selected-owner bridge unchanged;
- completed-session prices unchanged;
- current-effective technical unchanged;
- events/macros unchanged.

No current live qualification inheritance.

---

# 16. Canonical code-owner registry

REV22 added legitimate source-owner modules and centrally extended the canonical whole-source owner
inventory from 16 to 18 mandatory owners.

Preserve the REV22 canonical registry architecture.

REV23 changes code, therefore recompute per-file hashes / aggregate registry identity.

If the JSON-native serialization logic is implemented inside an existing registered owner:
path inventory should remain the same 18.

If a new mandatory whole-source owner module is introduced:
update the canonical registry centrally and all producer/seed/consumer/replay/test paths together.

Do not hand-maintain an independent list.

Require exact set/hash parity.

---

# 17. Offline implementation gate

Before destructive GC or provider calls require:

- typed ReferenceTarget / exact equivalent PASS;
- public plan JSON-native validator PASS;
- TSM old tuple/list regression reproduced;
- TSM fixed 0 differences;
- WRD old tuple/list regression reproduced;
- WRD fixed 0 differences;
- disk persistence round-trip integration PASS;
- production replay path PASS;
- logical grouping/purpose routing regression PASS;
- unchanged financial cap PASS;
- all22 offline readiness PASS;
- canonical code-owner registry exact parity PASS;
- completed-session current-price regression PASS;
- Pass-A visibility regression PASS;
- all previously closed owner regressions PASS;
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

Only after this gate may storage GC run.

---

# 18. Minimal REV22 serialization fixture

Before deleting REV22 expanded data, seal:

`rev22-slot-plan-json-parity-regression-fixture/`

At minimum:

- TSM persisted slot plan;
- TSM replay slot plan;
- TSM old 156-difference diagnostic;
- WRD persisted slot plan;
- WRD replay slot plan;
- WRD old 329-difference diagnostic;
- exact relevant source-plan inputs;
- generation/code identity;
- fixture manifest + SHA.

Do not retain the full 538-request REV22 generation solely for serialization regression.

Immutable REV22 ZIP remains the complete evidence archive.

---

# 19. Standing Storage GC — mandatory before next full-fresh

REV22 is now sealed by immutable ZIP/SHA:

ZIP SHA:

`a48fc5cca70dc80e85f6fdb9557313e98116884f2d9d14db2924cdf1f0ffdf18`

Archive checks:

- CRC PASS
- internal manifest `7872/7872`
- missing/hash/size/extra:
  `0`

After Section 18 fixture sealing and dependency checks, REV22 expanded source/report data is GC-eligible.

REV21 evidence expanded data is also eligible if no unique dependency remains beyond the sealed fixture.

---

# 20. GC rules

Before deletion:

- verify archive ZIP/SHA;
- CRC;
- manifest;
- fixture dependencies;
- current worktree protection;
- unique evidence.

Eligible:
- REV22 expanded live generation;
- REV22 unpacked report/replay data;
- REV21 expanded evidence report;
- remaining safe older R9 expanded data;
- old diagnostics/receipts/replay trees;
- clean completed worktrees when archive/ref-safe.

Preserve immutable ZIP/SHA.

Use:
`git worktree remove`

for worktrees.

No raw removal of active Git worktrees.
No aggressive shared `.git` prune.

---

# 21. Protected storage

Never auto-delete:

- current REV23 worktree;
- operating/main worktree;
- shared `.git`;
- production DB/WAL;
- `.env`;
- credentials/auth;
- scheduler/production state;
- immutable result ZIP/SHA;
- registered minimal fixtures;
- unique unverified evidence;
- active new full-fresh generation.

---

# 22. Storage receipts

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`

Record:

- before/after `df -h`;
- exact candidate paths/sizes;
- archive identities;
- deletion/skips;
- actual reclaimed bytes;
- worktree removals;
- final free bytes.

No silent deletion.

---

# 23. Disk admission

REV22 report:

- logical removed bytes:
  `1,072,277,179`
- actual free-space delta:
  `1,150,828,544`
- expanded directories removed:
  `18`
- worktrees removed:
  `2`
- closeout free bytes:
  `15,527,514,112`
  (~14.46 GiB).

Remeasure current disk.

Hard pre-collection minimum:

`12 GiB`

Preferred:

`14 GiB+`

Hard pre-model minimum:

`10 GiB`

If safe GC cannot maintain 12 GiB:

`R2B_R9_REV23_STORAGE_GC_HEADROOM_GAP`

Do not delete protected/unverified evidence merely for headroom.

---

# 24. New REV23 full-fresh generation

Only after:

- implementation gate PASS;
- storage GC executed;
- free >= 12 GiB;

create a completely new generation.

Do not resume REV22.
Do not reuse REV22 mutable current source values.

Recompute:

- query time;
- exchange calendars;
- completed sessions;
- all provider descriptors;
- financial plans;
- events;
- Market/macro/FX/night;
- valuation;
- budgets.

Alpha Vantage:
`0`

Massive/undeclared fallback:
`0`.

---

# 25. Fresh FPI slot-plan acceptance

For TSM and WRD:

- current source acquired fresh;
- logical reference grouping/purpose routing;
- slot plan built JSON-native;
- durable persisted;
- loaded from disk;
- replay recomputed;
- exact equality PASS;
- canonical SHA equality PASS.

No representation coercion at comparison time.

No source-qualification override.

---

# 26. Fresh all22 acquisition

Run current owners for US14 + KR8.

Fresh:

- price/OHLCV;
- completed-session current price;
- technical;
- financial/business;
- selected financial owner;
- events;
- quality;
- valuation;
- flow/positioning;
- issuer bridge where needed.

No prior mutable current data.

---

# 27. Full source closure

Require:

- stocks:
  `22/22`
- financial source plans round-trip stable;
- current-price states owned;
- technical states owned/typed unavailable;
- selected financial owners complete;
- events:
  `22/22`
- quality:
  `22/22`
- valuation:
  `22/22`
- Market:
  `2/2`
- macro/FX/night:
  qualified or accepted typed unavailable.

Create:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

All code identity uses canonical registry.

---

# 28. Replay twice

Freeze the fresh source corpus.

Disable network/provider access.

Replay entire graph twice.

Require exact semantic equality for:

- stocks 22;
- FPI slot plans;
- logical reference groups;
- financial source states;
- completed-session prices;
- technical states;
- events;
- quality;
- valuation;
- US/KR Market;
- macro/FX/night;
- whole-source packets;
- authority graph;
- code-owner registry.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and with full live coverage:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

---

# 29. Pass-A visibility replay

Before models require:

- technical excluded family absent from A model view;
- approved financial-quality/thesis/macro refs present;
- A preflight PASS;
- no authority widening.

---

# 30. Pre-model disk guard

Immediately before model calls:

`free >= 10 GiB`

If below:

`R2B_R9_REV23_DISK_GUARD`

Preserve frozen source corpus.
No model calls.

---

# 31. Fresh AI

Only after source qualification + replay + A visibility + disk guard:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`

No old output reuse.
No target fitting.
No source recollection after model stage starts.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

---

# 32. Final Market messages

Preserve approved user-facing contract.

## US

`미국 시장 · YYYY-MM-DD`

- major indices/proxies change + %;
- macro;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or `자료 부족`;
- KOSPI200 D/W/M or `자료 부족`.

## KR

`한국 시장 · YYYY-MM-DD`

- KOSPI/KOSDAQ completed-session judgment;
- breadth/flow where qualified;
- KOSPI/KOSDAQ sectors or `자료 부족`;
- USD/KRW same-date or latest-published official value with source date.

---

# 33. Final detailed stock messages

Stable order:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / evidence maturity / New Buyer / Holder;
4. reevaluation;
5. thesis / structural risk / market expectations;
6. core judgment;
7. business/earnings;
8. existing warnings;
9. key monitoring;
10. current price structure;
11. flow/positioning;
12. Valuation.

Do not render standalone:

- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

No internal refs/hashes/debug text.

---

# 34. Exact sender-boundary capture

Delivery disabled.

Capture exact:

- MARKET_US;
- MARKET_KR;
- US14;
- KR8;
- ALL_MESSAGES.md.

Total:

`24/24`

No post-hoc reconstruction.

---

# 35. Human-review bundle

On full PASS create:

`r2b-r9-rev23-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- JSON-native slot-plan contract;
- TSM/WRD round-trip parity receipts;
- logical reference routing audit;
- code-owner registry parity;
- storage GC receipts;
- all22 source matrix;
- current-price/technical;
- financial/events;
- quality/valuation;
- Market/macro/FX/night;
- whole-source graph;
- replay twice;
- A visibility replay;
- fresh Market/Core/A/B;
- validation;
- production isolation.

---

# 36. Post-seal storage state

After REV23 ZIP + SHA are sealed and verified:

- do not delete active REV23 expanded generation inside REV23;
- mark:
  `NEXT_FULL_FRESH_GC_ELIGIBLE_AFTER_REVIEW`;
- record path/size.

Any future full-fresh task repeats archive-backed GC.

---

# 37. Production side effects

Hard zero:

- Telegram send;
- recipient intent;
- production DB writes;
- warning/notification mutation;
- scheduler mutation;
- broker;
- deploy;
- main merge;
- remote push;
- restart.

---

# 38. Success terminal

Use only:

`R2B_R9_REV23_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. persisted slot-plan public surface JSON-native;
2. TSM old 156 target tuple/list diffs → 0;
3. WRD old 329 target tuple/list diffs → 0;
4. acquisition→disk→reload→recompute exact equality PASS;
5. no equality-guard relaxation;
6. logical reference grouping/routing unchanged;
7. unchanged financial-document cap;
8. offline all22 readiness PASS;
9. canonical code-owner registry parity PASS;
10. storage archive verification PASS;
11. storage GC executed;
12. pre-collection free >= 12 GiB;
13. no prior mutable current source reuse;
14. fresh stocks `22/22`;
15. Market `2/2`;
16. events `22/22`;
17. quality/valuation `22/22`;
18. whole-source graph PASS;
19. replay twice PASS;
20. A visibility replay PASS;
21. complete adapter qualification;
22. pre-model free >= 10 GiB;
23. fresh Market/Core/A/B complete;
24. exact final payloads `24/24`;
25. message contract PASS;
26. Alpha/fallback `0`;
27. production side effects `0`;
28. human-review ZIP generated.

---

# 39. Honest stop terminals

- `R2B_R9_REV23_FPI_SLOT_PLAN_JSON_NATIVE_GAP`
- `R2B_R9_REV23_FPI_SLOT_PLAN_REPLAY_PARITY_GAP`
- `R2B_R9_REV23_STORAGE_GC_ARCHIVE_GAP`
- `R2B_R9_REV23_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV23_FRESH_FINANCIAL_SOURCE_PARTIAL`
- `R2B_R9_REV23_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV23_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV23_DISK_GUARD`
- exact Market/macro/FX/night blocker;
- exact model/render failure.

Do not:
- accept tuple/list as equal in the guard;
- normalize only at comparison time;
- skip persisted round-trip testing;
- reuse REV22 current source under changed code;
- delete unverified unique evidence;
- bypass full source qualification.

---

# 40. Required validation

## JSON-native plan
- typed target object positive;
- tuple leak negative;
- raw model-object leak negative;
- non-string dict key negative;
- set/bytes/Path/datetime negative;
- deterministic JSON roundtrip.

## Persistence parity
- TSM persisted/replay exact equality;
- WRD persisted/replay exact equality;
- real durable writer/read;
- production replay function chain;
- canonical SHA equality.

## Structural source
- REV22 logical-cell grouping positives/negatives;
- governance/lease routing;
- financial 6-K positive;
- cap unchanged.

## Code registry
- exact path/hash parity;
- producer/seed/consumer/replay;
- missing/extra/tamper negatives.

## Storage
- REV22 archive verification;
- minimal fixture extraction;
- expanded deletion;
- protected paths;
- actual reclaimed bytes.

## Full pipeline
- all22;
- Market2;
- financial/events;
- price/technical;
- quality/valuation;
- macro/FX/night;
- replay twice;
- A visibility;
- Market/Core/A/B;
- exact24.

## Repository
- focused;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- unchanged skip/xfail identity.

---

# 41. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV22 identity/SHA;
- repository identities;
- changed-file inventory;

## Serialization repair
- ReferenceTarget schema/equivalent;
- JSON-native validator;
- TSM old/new difference matrix;
- WRD old/new difference matrix;
- durable round-trip receipts;
- production replay parity receipt;
- REV22 minimal fixture manifest.

## Source contracts
- logical cell reference regression;
- FPI slot plans;
- all22 offline readiness;
- canonical code-owner registry parity.

## Storage
- storage-gc-plan.json;
- storage-gc-result.json;
- storage-gc-protected.json;
- storage-gc-fixtures.json;
- before/after disk;
- deleted/skipped paths;
- archive identities.

## Fresh live
- provider plan/counters;
- all22 source matrix;
- current-price/technical;
- financial/events;
- quality/valuation;
- Market/macro/FX/night;
- whole-source graph;
- replay twice;
- A visibility replay;
- adapter qualification.

## AI/render
- fresh Market/Core/A/B;
- exact24;
- human-review ZIP/SHA.

## Safety
- Alpha/fallback 0;
- production side effects 0;
- validation;
- secret scan;
- bundle manifest.

---

# 42. Final principle

REV22 proves the financial-source semantics are now correct enough to reach persisted-plan replay.

The remaining failure is a pure serialization contract defect:

a Python tuple is not JSON-native, so JSON persistence changes its runtime type even though the
semantic JSON and hash are identical.

The correct solution is not to weaken equality.

The persisted/public plan must be JSON-native before it is written, and the same typed representation
must be produced again by replay.

Once that exact round-trip contract is closed, archive-backed GC runs and a new full-fresh generation
proceeds to the real 24-message human-review boundary.
