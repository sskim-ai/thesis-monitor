# Thesis Monitor — R2B-R9-REV20
## Canonical Whole-Source Code-Owner Registry + Archive-Backed Storage GC
### Then new full-fresh all-source requalification → replay twice → fresh Market/Core/A/B → exact detailed 24-message proof

**REV20 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV20.**

REV19 successfully closed the Pass-A visibility leak, executed the standing storage-GC policy,
started a new full-fresh generation, and captured 538 real provider attempts.

It stopped before complete source qualification and before any model call on exactly one P1:

`WHOLE_SOURCE_CODE_OWNER_INVENTORY_PRODUCER_CONSUMER_PARITY_GAP`

This is not:
- provider failure;
- source freshness failure;
- code drift after freeze;
- financial/technical/Market policy failure;
- model failure.

The production whole-input builder currently emits 16 exact legitimate code-owner fingerprints,
while `compose_full_source` still requires an older exact 13-owner set.

The three additional legitimate producer owners are:

- `app/services/selected_financial_owner.py`
- `app/services/latest_published_fx.py`
- `app/services/current_effective_technical.py`

REV20 must centralize the exact owner inventory so producer metadata, seed hashing, consumer validation,
offline synthetic/common-cohort proofs, and replay all use the same canonical typed registry.

Do **not**:
- remove the three legitimate owners;
- accept arbitrary supersets;
- weaken file-hash verification;
- bypass exact-set validation;
- mutate prior source evidence;
- reuse REV19 mutable/current source values under the new code;
- change any investment/source semantics.

After the offline contract passes:
1. extract only minimal REV19 regression fixtures;
2. verify the immutable REV19 archives;
3. execute storage GC on superseded expanded generations including REV19 where safe;
4. start a completely new full-fresh generation;
5. replay twice;
6. run fresh Market/Core/A/B;
7. capture exact 24 final sender-boundary messages.

---

# 0. Newest SoT

Adopt the **REV19 fresh execution report** as the newest execution SoT.

Fresh execution ZIP SHA-256:

`7e104d0dfbae4a0f656487c9e7b7e839eff4d02bb48d67845f885f3108b81b54`

Sidecar:
exact match.

Independent ZIP verification:

- CRC:
  PASS
- manifest entries:
  `8132`
- missing:
  `0`
- SHA mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV19_LIVE_ADAPTER_REQUALIFICATION_GAP`

Fresh generation:

`rev19-live-20260929T112301Z`

Frozen completed sessions:

- KR:
  `2026-09-29`
- US:
  `2026-09-28`

Provider attempts:

`538`

Model calls:

`0`

Exact live messages:

`0/24`

P0:

`0`

P1:

`1`

Repository:

- branch:
  `codex/r2b-r9-rev19-pass-a-visibility-gc`
- base:
  `ab456d6ef7cbc41d64940dd286fdfcfa5219948e`
- instruction:
  `a2a3a324c76348079124ca5c6c864cfff5e2734f`
- implementation/final:
  `c7b8076bd05cc25a0ed08b84f86af659f1fecf96`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true
- local-only:
  true
- main merge:
  0
- remote push:
  0

REV19 validation:

- focused:
  `941 PASS`
- full:
  `6785 PASS / 63 unchanged skips`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- production side effects:
  `0`

---

# 1. REV19 initial GC/offline report

Also preserve the earlier REV19 offline/GC report as supporting evidence.

ZIP SHA-256:

`506eeaff9049b40f8b91fe39771b3288ac644581e94a6bd3be87cb19d9dcde92`

Independent verification:

- CRC:
  PASS
- manifest entries:
  `496`
- missing/mismatch/extra:
  `0`

This earlier report proved:

- Pass-A visibility owner:
  PASS
- completed-session current-price owner:
  PASS
- storage GC:
  EXECUTED
- provider/model calls:
  0

It was superseded operationally by the later fresh-execution report after explicit execution approval.

Do not treat it as a separate current source generation.

---

# 2. Preserve all REV19 closed contracts

Do not reopen:

- completed-session current-price owner;
- US14 price regression `14/14`;
- Pass-A visibility intersection;
- technical family explicit exclusion from Pass A;
- approved financial-quality / thesis / macro Pass-A visibility;
- final A preflight;
- selected financial owner;
- latest-published FX;
- current-effective technical semantics;
- SNDK 52/53-week fiscal contract;
- TSM/WRD FPI financial owners;
- OpenDART;
- ECOS;
- events;
- KR completed-session technical owner;
- KOSPI200 typed unavailable;
- Market display;
- UNKNOWN_LIMIT;
- R7 absolute-current direction guard;
- valuation policy;
- detailed stock renderer;
- Core/A/B policy.

REV20 is metadata/code-identity parity work plus a new proof.

---

# 3. Exact REV19 failure

REV19 reached:

`FIRST_WHOLE_COMPOSITION_PRECONDITION`

and failed:

`whole_source_code_contract_identity_mismatch`

Producer:

`scripts/r9_rev11_replay.py:248`

Consumer:

`app/services/unified_full_source_cohort.py:97`

Producer owner count:

`16`

Consumer required owner count:

`13`

Frozen code hashes matched.
No actual post-freeze code drift occurred.

---

# 4. Exact producer owner inventory observed in REV19

The producer provided these 16 exact owner files:

1. `app/services/bounded_financial_projection.py`
2. `app/services/bounded_financial_stock_owner.py`
3. `app/services/canonical_business_quality_owner.py`
4. `app/services/current_effective_technical.py`
5. `app/services/current_fresh_valuation.py`
6. `app/services/fresh_event_carrier.py`
7. `app/services/fresh_financial_stock_owner.py`
8. `app/services/fresh_publication_replay.py`
9. `app/services/fresh_valuation_capability.py`
10. `app/services/latest_published_fx.py`
11. `app/services/persisted_business_event_owner.py`
12. `app/services/selected_financial_owner.py`
13. `app/services/unified_full_source_cohort.py`
14. `app/services/unified_sealed_context.py`
15. `app/services/unified_stock_event_input.py`
16. `scripts/m12dr_financial_source_authority.py`

REV19 consumer required the same list minus:

- `current_effective_technical.py`
- `latest_published_fx.py`
- `selected_financial_owner.py`

These three were introduced as legitimate source owners before REV19 and must remain fingerprinted.

---

# 5. Canonical typed WholeSourceCodeOwnerRegistry

Create exactly one canonical registry, repository naming permitting:

`WholeSourceCodeOwnerRegistry`

or:

`WHOLE_SOURCE_CODE_OWNER_FILES`

in one dedicated owner module.

The registry must be imported/consumed by all of:

- production whole-input metadata builder;
- FullSourceRunSeed/code identity builder;
- `compose_full_source` exact-set validation;
- whole-source replay;
- common-cohort synthetic fixture;
- code-contract tests;
- report/audit generation.

No caller may reconstruct the list independently.

---

# 6. Registry semantics

Each entry must own at minimum:

- relative repository path;
- owner role/classification;
- whether mandatory;
- file SHA-256 at freeze;
- registry version;
- semantic registry ID.

Recommended role classifications include:

- financial projection;
- stock financial owner;
- financial quality;
- selected financial owner;
- current-effective technical;
- fresh valuation;
- valuation capability;
- fresh event;
- persisted event;
- publication/macro;
- latest-published FX;
- stock event input;
- sealed/unified context;
- full-source composition;
- financial source authority.

Role names are audit metadata only.
They do not change source-use authority.

---

# 7. Exact-set verification remains strict

The consumer must still require:

`provided_paths == canonical_registry_paths`

exactly.

Do not accept:

- arbitrary superset;
- arbitrary subset;
- caller-provided extra owners;
- “at least required files”.

For every canonical path require:

- file exists;
- exact current freeze hash;
- no duplicate path;
- no path escape;
- no symlink substitution under the existing repository contract.

Unknown extra owner:

fail.

Missing owner:

fail.

Hash mismatch:

fail.

---

# 8. Production metadata builder parity

The production whole-input builder must obtain the registry from the same canonical owner.

Required proof:

`production_builder_paths == registry_paths`

and:

`production_builder_hashes == registry_current_hashes`

Do not construct one list in:

`scripts/r9_rev11_replay.py`

and another in:

`app/services/unified_full_source_cohort.py`.

Any current helper may wrap the registry, but it cannot define a separate inventory.

---

# 9. Seed / consumer / replay parity

The exact same registry identity must bind:

- source run seed;
- whole-source packet metadata;
- producer whole_inputs;
- consumer `compose_full_source`;
- first replay;
- second replay.

Create a receipt with:

- registry version;
- registry path list;
- per-file SHA;
- aggregate registry SHA;
- seed registry SHA;
- producer registry SHA;
- consumer registry SHA;
- replay1 registry SHA;
- replay2 registry SHA.

Require all equal.

---

# 10. Synthetic/common-cohort test gap closure

REV19 discovered:

`tests/test_r9_rev10_common_cohort.py`

independently constructs the same old 13-file list as the consumer.

Therefore it could not detect production 16-vs-13 drift.

Fix tests so the common-cohort fixture consumes the canonical registry owner used by production.

Add an explicit **production-builder parity test**:

production whole_inputs
→ canonical registry
→ compose_full_source

with the actual production builder function, not a separately hand-built metadata fixture.

---

# 11. Required negative tests

At minimum:

- canonical 16-owner exact set → PASS;
- remove one owner → fail;
- add unknown 17th owner → fail;
- tamper one file hash → fail;
- duplicate path → fail;
- reorder only:
  - normalized registry semantic identity remains deterministic if ordering is not semantic;
  - or exact deterministic canonical ordering is enforced;
- producer old 13 / consumer 16 → fail;
- producer 16 / consumer old 13 → fail;
- selected_financial_owner omitted → fail;
- latest_published_fx omitted → fail;
- current_effective_technical omitted → fail;
- caller arbitrary superset → fail.

Do not weaken validation to pass these tests.

---

# 12. Code-owner change procedure

Because REV20 changes the consumer/registry code itself:

- recompute all canonical owner hashes under the new exact implementation;
- freeze a new registry identity after tests;
- do not try to make REV19's old whole-source metadata pass under changed code;
- REV19 raw/source corpus is regression evidence only after the repair.

No mutable current source reuse across this code change.

---

# 13. Minimal REV19 regression fixture

Before GC of REV19 expanded data, extract/seal only what is necessary to reproduce the 16-vs-13 failure offline.

Create:

`rev19-code-owner-parity-regression-fixture/`

At minimum:

- exact old producer path list;
- exact old producer hashes;
- exact old consumer path list;
- old failure receipt;
- generation/code identity;
- minimal metadata needed to call the new parity validator;
- fixture manifest + SHA.

Do **not** preserve the full REV19 538-request expanded generation solely for this regression.

The immutable REV19 fresh-execution ZIP remains the authoritative evidence archive.

---

# 14. Whole offline repair gate

Before destructive GC or new network calls require:

- canonical registry schema PASS;
- exact 16 current owners present;
- production builder parity PASS;
- compose_full_source exact-set validation PASS;
- seed/producer/consumer/replay registry identity PASS;
- common-cohort fixture uses canonical registry;
- 16-vs-13 historical regression reproduced then fixed;
- missing/extra/tamper negatives PASS;
- all REV19 Pass-A visibility regressions PASS;
- completed-session current-price owner regressions PASS;
- all previously closed source-owner regressions PASS;
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

Only after this gate may storage GC execute.

---

# 15. Storage GC — execute before the new full-fresh generation

The user explicitly requires new full-fresh runs not to accumulate superseded expanded generations.

REV20 must repeat the standing archive-backed GC policy.

REV19 fresh execution is now sealed by:

- immutable ZIP;
- `.sha256`;
- CRC PASS;
- manifest `8132/8132`;
- no missing/mismatch/extra.

Therefore the REV19 expanded fresh generation/report becomes GC-eligible after Section 13 fixtures are sealed,
subject to protected-path checks.

---

# 16. Archive verification

Before deleting each candidate require:

- ZIP exists;
- SHA sidecar exists;
- SHA matches;
- CRC PASS;
- manifest complete;
- no unique unarchived evidence;
- no registered fixture dependency;
- not active current worktree/generation.

Record exact archive identity.

Do not infer safety from directory age/name alone.

---

# 17. GC eligible data

Delete archive-backed superseded expanded copies when safe:

- REV19 fresh expanded provider generation;
- REV19 unpacked source/replay/report internals;
- REV18 and older expanded generation remnants not already removed;
- old diagnostic directories;
- old request/attempt/normalized/replay trees;
- duplicate validation exports.

Preserve immutable ZIP/SHA archives.

If the earlier REV19 offline-GC report directory is already the current active worktree/report dependency,
preserve only what is still required until the new REV20 worktree is active and its minimal fixtures are sealed.

---

# 18. Old worktree cleanup

Inspect completed old worktrees.

Eligible only when:

- not current REV20;
- not operating/main;
- clean;
- no untracked files;
- branch/ref preserves needed commit;
- result archive sealed;
- no unique fixture dependency.

Use:

`git worktree remove`

No raw `rm -rf`.

Do not run aggressive shared Git object pruning.

---

# 19. Protected storage

Never auto-delete:

- current REV20 worktree;
- operating/main worktree;
- shared `.git`;
- production DB/WAL;
- `.env`;
- auth/credentials;
- scheduler/production state;
- immutable result ZIP/SHA;
- registered minimal regression fixtures;
- unverified unique evidence.

---

# 20. GC receipts

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`

Record:

- before/after `df -h`;
- free bytes;
- candidate path/size;
- archive SHA;
- integrity result;
- deleted/skipped reason;
- actual bytes reclaimed;
- actual free-space delta.

No silent deletion.

---

# 21. Disk headroom

REV19 GC already reclaimed:

- logical:
  `4,863,768,450 bytes`
- actual free-space delta:
  `5,218,668,544 bytes`
- 108 directories;
- 6 completed worktrees.

REV19 post-GC free:
~`15.97 GiB`.

REV19 fresh generation closeout free remained roughly:
`15.5 GiB` class.

REV20 must remeasure current disk.

Hard pre-collection minimum:

`12 GiB`

Preferred:

`14 GiB` or greater when safely achievable.

Hard pre-model minimum:

`10 GiB`.

If safe GC cannot reach 12 GiB:

`R2B_R9_REV20_STORAGE_GC_HEADROOM_GAP`

Do not delete protected/unverified evidence merely to satisfy headroom.

---

# 22. New REV20 full-fresh generation

Only after:

- offline code-owner gate PASS;
- storage GC executed;
- free >= 12 GiB;

create a completely new source generation.

Do not resume REV19.

Do not reuse REV19 provider receipts as current values.

Recompute:

- query time;
- US/KR completed sessions;
- provider descriptors;
- request budgets;
- financial candidate plans;
- event plans;
- Market/macro/FX/night;
- valuation.

Alpha Vantage:

`0`

Massive/undeclared fallback:

`0`.

---

# 23. Fresh source acquisition

Run all current source owners for:

US14:
- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

KR8:
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

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
- issuer bridge where required.

No prior mutable current values.

---

# 24. Fresh Market/macro/FX/night

Preserve accepted current owners.

US:
- selected major indices/proxies;
- sector universe;
- FRED/EIA;
- completed-session Market.

KR:
- KOSPI/KOSDAQ completed session;
- sectors/breadth/flow where qualified;
- ECOS USD/KRW current/latest-published contract.

Night:
- KOSPI200 only;
- current qualified values or typed `자료 부족`;
- no stale promotion.

---

# 25. Full source closure

Require:

- stock packets:
  `22/22`
- current-price projections complete where required;
- technical states owned;
- selected financial owners complete;
- event states:
  `22/22`;
- quality:
  `22/22`;
- valuation:
  `22/22`;
- Market:
  `2/2`;
- macro/FX/night:
  qualified or accepted typed unavailable under current contract.

Create new:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

Every packet's code-contract metadata must use the new canonical WholeSourceCodeOwnerRegistry.

---

# 26. Replay twice

Freeze the new source corpus.

Disable all provider access.

Replay entire graph twice.

Require exact semantic equality for:

- 22 stock packets;
- current-price projections;
- technical states;
- financial owner envelopes;
- events;
- quality;
- valuation;
- US/KR Market;
- macro/FX/night;
- whole-source packets;
- authority graph;
- canonical code-owner registry identity.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and with full live coverage:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

Do not inherit either flag.

---

# 27. Pass-A visibility replay

After whole-source replay, explicitly prove:

- excluded technical family remains absent from A model view;
- approved financial-quality / configured Pass-A refs remain visible;
- final A source-authority preflight PASS;
- no authority widening;
- no source family relabeling.

Run across the fresh cohort.

No model call yet.

---

# 28. Pre-model disk guard

Immediately before model calls:

`free >= 10 GiB`.

If below:

`R2B_R9_REV20_DISK_GUARD`

Preserve frozen source corpus.
No model calls.

---

# 29. Fresh AI

Only after:

- full source qualification;
- replay twice;
- A visibility replay;
- disk guard;

run fresh:

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
No source recollection after model execution begins.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

---

# 30. Final Market messages

Preserve approved format.

## US

`미국 시장 · YYYY-MM-DD`

- major indices/proxies change + %;
- macro;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or honest `자료 부족`;
- KOSPI200 D/W/M or `자료 부족`.

## KR

`한국 시장 · YYYY-MM-DD`

- KOSPI/KOSDAQ completed-session judgment;
- breadth/flow where qualified;
- KOSPI/KOSDAQ sectors or `자료 부족`;
- USD/KRW same-date or latest-published official value with source date.

---

# 31. Final detailed stock messages

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

Technical evidence may remain user-visible under the renderer contract even when excluded from Pass A.

---

# 32. Exact sender-boundary capture

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

# 33. Human-review bundle

On full PASS create:

`r2b-r9-rev20-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- canonical code-owner registry;
- producer/consumer/seed/replay parity receipt;
- missing/extra/tamper negative-test receipt;
- REV19 parity regression fixture manifest;
- storage GC plan/result/protected/fixtures;
- before/after disk;
- all22 source matrix;
- completed-session current-price matrix;
- A visibility audit;
- Market/macro/FX/night;
- financial/events;
- technical;
- quality;
- valuation;
- whole-source graph;
- replay twice;
- fresh Market/Core/A/B;
- validation;
- production isolation.

---

# 34. Post-seal storage disposition

After REV20 ZIP + SHA are sealed and verified:

- do not delete the active REV20 expanded generation inside REV20;
- mark:
  `NEXT_FULL_FRESH_GC_ELIGIBLE_AFTER_REVIEW`;
- record path/size.

Any later task that begins another full-fresh generation repeats this GC policy.

---

# 35. Production side effects

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

# 36. Success terminal

Use only:

`R2B_R9_REV20_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. canonical code-owner registry PASS;
2. exact current owner set includes all legitimate 16 owners;
3. production builder = consumer = seed = replay registry identity;
4. missing/extra/tamper negatives PASS;
5. synthetic common-cohort production parity test PASS;
6. no arbitrary superset acceptance;
7. no legitimate owner removed;
8. REV19 regression fixture sealed;
9. storage archive verification PASS;
10. storage GC executed;
11. pre-collection free >= 12 GiB;
12. new generation uses no prior mutable current source;
13. fresh stocks `22/22`;
14. Market `2/2`;
15. events `22/22`;
16. quality/valuation `22/22`;
17. new whole-source graph PASS;
18. replay twice PASS;
19. A visibility replay PASS;
20. complete adapter qualification;
21. pre-model free >= 10 GiB;
22. fresh Market/Core/A/B complete;
23. exact final payloads `24/24`;
24. message contract PASS;
25. Alpha/fallback `0`;
26. production side effects `0`;
27. human-review ZIP generated.

---

# 37. Honest stop terminals

- `R2B_R9_REV20_CODE_OWNER_REGISTRY_GAP`
- `R2B_R9_REV20_CODE_OWNER_HASH_PARITY_GAP`
- `R2B_R9_REV20_STORAGE_GC_ARCHIVE_GAP`
- `R2B_R9_REV20_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV20_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV20_FRESH_FINANCIAL_SOURCE_PARTIAL`
- `R2B_R9_REV20_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV20_DISK_GUARD`
- exact Market/macro/FX/night blocker
- exact model/render stage failure.

Do not:
- trim legitimate producer owners;
- allow arbitrary consumer supersets;
- ignore file hash mismatch;
- reuse REV19 current source under changed code;
- delete unverified unique evidence;
- bypass source qualification to run models.

---

# 38. Required validation

## Code-owner registry
- canonical 16 positive;
- missing owner negative;
- extra owner negative;
- tampered hash negative;
- duplicate negative;
- deterministic registry identity;
- producer parity;
- consumer parity;
- seed parity;
- replay parity;
- common-cohort production builder parity.

## Regression
- historical 16-vs-13 failure reproduced;
- repaired path PASS;
- all prior Pass-A visibility tests;
- completed-session current-price tests;
- source-owner regression suites.

## Storage
- archive SHA/CRC/manifest;
- REV19 minimal fixture extraction;
- REV19 expanded deletion when safe;
- protected paths;
- old clean worktrees;
- actual reclaimed bytes;
- free-space accounting.

## Full pipeline
- all22;
- Market2;
- events;
- financial;
- technical;
- quality/valuation;
- macro/FX/night;
- whole-source replay twice;
- A visibility replay;
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

# 39. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV19 fresh execution identity/SHA;
- repository identities;
- changed-file inventory;

## Code-owner closure
- canonical registry schema;
- registry file list/roles;
- per-file hashes;
- aggregate registry hash;
- seed/producer/consumer/replay parity;
- production-builder parity test;
- negative-test receipt;
- REV19 regression fixture.

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
- current-price matrix;
- A visibility audit;
- Market/macro/FX/night;
- financial/events;
- technical;
- quality/valuation;
- whole-source graph;
- replay twice;
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

# 40. Final principle

REV19 proves the external data paths, completed-session pricing, Pass-A visibility, and storage-GC
mechanism are all functioning.

The remaining defect is pure code-contract inventory drift:

the producer correctly knows about three legitimate source owners that the consumer's older
hand-maintained exact list does not.

The correct repair is not to delete those fingerprints or loosen the consumer.

It is to establish one canonical exact owner registry used by every producer, consumer, seed, replay,
and test path.

After that offline contract closes, archive-backed GC runs again and a completely new full-fresh
generation proceeds to the real 24-message human-review boundary.
