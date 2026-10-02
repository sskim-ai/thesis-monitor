# Thesis Monitor — R2B-R9-REV30
## Authority-Manifest Canonical Hash Parity Repair
### Reuse Exact Sealed REV29 Source Corpus — Provider Recollection 0
### Full 22-Subject Visibility Reproof → Source-Only Blind Seal → Market/Core/A/B → Exact 24 Messages

**REV30 supersedes every prior unexecuted post-REV29 instruction. Execute only REV30.**

REV29 completed the expensive parts successfully:

- archive-backed storage GC;
- one new full-fresh generation;
- 576 provider attempts;
- stocks 22/22;
- Markets 2/2;
- provider-native valuation acquisition integrated;
- valuation typed states 22/22;
- qualified PER 8;
- qualified PBR 10;
- fPER 0;
- whole-source replay twice exact PASS;
- complete source adapter qualification PASS;
- B valuation-context replay PASS;
- direction-isolation offline audit PASS.

REV29 then stopped **before any model call** at the pre-model A-visibility preparation gate.

The blocker is one exact serializer-contract mismatch:

- producer authority hash:
  `scripts.m12da_source_use_contract.canonical_sha256`
  with `ensure_ascii=True`;
- authority consumer:
  `app.services.unified_snapshot_contract.digest`
  with `ensure_ascii=False`;
- first failing subject:
  `MU`;
- first differing field:
  `/fresh_controller_event_source/selected/0/title`;
- character:
  `U+2019` RIGHT SINGLE QUOTATION MARK.

The sealed authority object is not corrupted.

For MU:

stored/producer SHA-256:

`44d5a630c20efa6148744b34dda204e82e9a59a83074b737497507820e10f240`

incorrect consumer SHA-256:

`17d0840e4029f3bea0ae47d7b6fcfc74806077c8ba866e2b41638dbc21b3c916`

Read-only forensic evaluation over all 22 sealed authority objects proved:

- producer hash matches stored hash:
  `22/22`;
- only MU differs under the alternate consumer JSON encoder;
- no source content was modified;
- no provider was recalled;
- no model was called;
- no hash was replaced;
- no selective reproof occurred.

REV30 must repair **only this authority-consumer canonicalization contract**, then continue from the exact sealed REV29 source corpus.

Do not recollect the 576-provider source graph.

---

# 0. Newest SoT

Adopt REV29 as newest source/result SoT.

REV29 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev29-native-valuation-full-fresh-report.zip`

SHA-256:

`67cf2155c35f42690d6fa88387ad06268d29e7903333947fa7bc42e454e69961`

Independent verification:

- uploaded sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `8297`;
- internal manifest:
  `8296/8296`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

Terminal:

`R2B_R9_REV29_LIVE_ADAPTER_REQUALIFICATION_GAP`

Repository:

- branch:
  `codex/r2b-r9-rev29-native-valuation-full-fresh`
- base:
  `2c6b7beb1a0c8e6dc7d5ebd20568f6f48b3f4868`
- instruction:
  `faeb565751689c18ad27590d795715b89e62b538`
- fully tested/frozen implementation:
  `2262834c7bc41898a308934abacdb5b88c04347a`
- final local documentation commit:
  `a3a99eff7c5fa38491ca3193cdc91c4772df216b`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true
- main merge:
  `0`
- remote push:
  `0`.

Generation:

`rev29-live-20260930T042411Z`

---

# 1. Exact sealed source corpus to continue

REV30 is a **sealed-source continuation**, not a new full-fresh generation.

Required source identity:

generation:

`rev29-live-20260930T042411Z`

whole-source semantic/replay hash:

`0dcc42dd3d237794f8cf4a50aa5a491afa8082b19d273bfca5e38f7f129baa3d`

`live/whole-source.json` archive SHA-256:

`e80d93417c228f961da0a194fbb793669ce7f9609dbb2d0ea575cac258e55c45`

`live/source-qualification.json` archive SHA-256:

`8d0e6cbb583fd90a48c001114cec7c273c3429230fc646292c91881c6edb183b`

Fresh valuation state matrix SHA-256:

`01999df2e5ede4565a4c114fa7f71bf69daddf4ebf906068b8d43a8142ffd7bb`

B valuation-context audit SHA-256:

`907384914847193bba98d7a8f7abeec0754a9bb826cf9c8988bb9641cdbc7205`

B valuation-context replay hash:

`7e1cd3f0acc8d0dc267fb487d8897ef4dcb16c587533a420b273336db9d6f510`

Numeric-registry audit SHA-256:

`cd9a7dd75ff3564031cc3b395ef44e396c230464fba023b26bb40c948349258e`

Direction-isolation audit SHA-256:

`9823a3ffefa2c00937af852446671cc1fb2cd855d0945c17fd7b8617ab6549bb`

These identities must remain byte/semantic identical through REV30 continuation.

Any source change means this continuation authority is void.

---

# 2. Why source recollection is prohibited

REV29 source collection itself passed.

Observed:

- provider attempts:
  `576`
- provider recollection after freeze:
  `0`
- stocks:
  `22/22`
- Markets:
  `2/2`
- whole-source replay:
  exact PASS twice
- complete source adapter:
  qualified
- valuation states:
  `22/22`.

The failure occurs in a **consumer integrity-check serializer**, after source freeze/replay.

Therefore REV30 provider calls must be:

`0`

Do not:
- rebuild source values;
- refresh events;
- refresh valuation;
- refresh price/technical;
- rerun Market providers;
- diagnose by calling a provider.

If the local sealed source corpus is missing or differs from Section 1:

stop:

`R2B_R9_REV30_SEALED_SOURCE_IDENTITY_GAP`

Do not silently fall back to a fresh generation.

---

# 3. Exact root cause

REV29 forensic receipt:

`authority-hash-forensics.json`

SHA-256:

`05a9202bf24caf2b70409f686423972031b1b17bd9c012473c276312590e198e`

Root cause:

`Authority manifest producer/consumer JSON encoding mismatch on non-ASCII fields`

Producer:

`canonical_sha256(... ensure_ascii=True ...)`

Consumer:

`digest(... ensure_ascii=False ...)`

MU is the only current object with a non-ASCII path affecting this hash.

The evidence string containing U+2019 is valid source content.

Do not normalize:
- apostrophes;
- Unicode punctuation;
- Korean;
- source titles;
- source bytes.

Repair the hash consumer.

---

# 4. Narrow implementation boundary

Do **not** globally change generic snapshot hashing.

Do **not** alter all uses of:

`app.services.unified_snapshot_contract.digest`

merely to make MU pass.

Instead, patch the **specific authority-manifest consumer path** used by:

`r2b_r2_contract.bound_chain`

or the exact repository-equivalent authority validation path.

That consumer must use the same canonical serialization contract as the producer.

Preferred architecture:

- one explicitly named authority-manifest canonical hash helper;
- both producer and authority consumer use the same semantic implementation;

or, if moving producer code would widen the change unnecessarily:

- the authority consumer calls a shared/repository-approved canonical helper with byte-for-byte equivalent behavior.

Required canonical properties must exactly match the producer:
- UTF-8 encoded serialized bytes;
- `ensure_ascii=True`;
- same key ordering;
- same separators;
- same handling of lists/dicts/null/bool/numeric/string;
- no Unicode normalization.

Do not modify unrelated hash contracts.

---

# 5. Backward compatibility requirement

For every ASCII-only current authority object:

new authority consumer hash must equal:
- old consumer hash;
- producer hash;
- stored hash.

For non-ASCII authority objects:

new authority consumer hash must equal:
- producer hash;
- stored hash.

No existing stored authority hash may be rewritten.

No source authority object may be rewritten.

---

# 6. Required hash tests

Add exact tests for:

## ASCII baseline
- nested object;
- lists;
- booleans/null;
- sorted-key variation;
- old/new authority consumer exact equality.

## Unicode
At minimum:
- U+2019 RIGHT SINGLE QUOTATION MARK;
- Korean Hangul;
- one non-BMP Unicode character/emoji;
- mixed ASCII+Unicode nested payload.

All must match producer canonical SHA exactly.

## Tampering
- content modified with stored original hash → fail;
- stored hash modified → fail;
- Unicode punctuation normalized/replaced → fail;
- reordered semantically equivalent dictionary → canonical hash remains stable only according to the exact producer contract.

## Scope isolation
Prove:
- authority-manifest consumer uses canonical authority hash;
- unrelated generic snapshot digest behavior is unchanged.

No test fixture may special-case MU.

---

# 7. Current sealed 22-object authority reproof

After implementation freeze, with network disabled:

load all 22 existing REV29 sealed authority objects.

Require:

- stored hash == producer-canonical hash:
  `22/22`;
- stored hash == repaired authority-consumer hash:
  `22/22`;
- no object content modified;
- no stored hash modified;
- no subject-specific branch;
- non-ASCII field inventory retained.

Create:

`authority-canonical-parity-22.json`

Record for each subject:
- stored hash;
- producer canonical hash;
- repaired consumer hash;
- equality booleans;
- non-ASCII field paths;
- source-object SHA.

---

# 8. Whole-source code identity

This repair is a validation/consumer change.

Do not alter any source-owner implementation listed in the REV29 whole-source code-owner registry.

REV29 registry:

- mandatory owners:
  `27`
- aggregate registry SHA-256:
  `c995c02c82bf1ed97c599402a70d91c0782ed40c7de8fba85e4f55db178f1cc5`.

If no registered source owner changed:

require the aggregate source-owner registry identity to remain exactly:

`c995c02c82bf1ed97c599402a70d91c0782ed40c7de8fba85e4f55db178f1cc5`

If a supposedly required repair changes that source-owner registry:

stop and explain why.
Do not silently continue as the same sealed-source proof.

---

# 9. Full validation before continuation

Before visibility/model continuation run:

- focused authority-hash tests;
- valuation integration tests;
- whole-source registry tests;
- required replay/B-binding tests;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

REV29 baseline:

- focused:
  `122 passed`
- full:
  `7005 passed / 63 skipped / 0 failed`
  (`7068` tests under report summary)
- Ruff:
  PASS
- diff:
  PASS
- knowledge:
  PASS.

REV30 full suite must be green.

Freeze the repair implementation.

No code/prompt/schema/source policy change after this freeze.

---

# 10. Reverify sealed source under repaired consumer

After repair freeze and with providers disabled:

require all existing REV29 source identities unchanged:

- whole-source semantic hash:
  `0dcc42dd3d237794f8cf4a50aa5a491afa8082b19d273bfca5e38f7f129baa3d`
- valuation state matrix SHA:
  `01999df2e5ede4565a4c114fa7f71bf69daddf4ebf906068b8d43a8142ffd7bb`
- B valuation-context audit SHA:
  `907384914847193bba98d7a8f7abeec0754a9bb826cf9c8988bb9641cdbc7205`
- B valuation-context replay hash:
  `7e1cd3f0acc8d0dc267fb487d8897ef4dcb16c587533a420b273336db9d6f510`.

Replay the sealed whole-source graph twice offline if the current continuation harness requires it.

Network:

`0`

Provider attempts:

`0`.

No old/new semantic source difference is permitted.

---

# 11. Full 22-subject visibility reproof — not selective

REV29 completed visibility only for:

- all KR8;
- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM.

It stopped at MU.

REV30 must **not** resume only from MU.

Re-run visibility preparation from the beginning for all:

`22/22`

under the repaired authority consumer.

Require:
- authority hash PASS;
- Pass-A visibility contract PASS;
- excluded technical family remains absent;
- approved financial/thesis/event refs unchanged;
- valuation absent from directional/A surfaces;
- B valuation context separately owned.

No selective ticker success claim.

---

# 12. Direction/valuation isolation reproof

Before source-only seal or models:

require:

## Core
provider-native valuation refs absent.

## Pass A
provider-native valuation refs absent from:
- supporting refs;
- contradicting refs;
- directional evidence buckets.

## Pass B
qualified valuation available only in the typed valuation context for:
- NewBuyer;
- Holder.

REV29 fresh coverage to preserve from the exact sealed source:

- qualified PER:
  `8`
- qualified PBR:
  `10`
- qualified fPER:
  `0`.

Do not change valuation coverage in REV30.

No provider refresh is allowed.

---

# 13. REV29 valuation coverage to preserve

Qualified PER + PBR:

- 000660
- 003690
- 005490
- 005930
- 012450
- 086280
- GOOGL
- IBM.

PBR only:

- CORZ
- WULF.

Identity unavailable:

- 010120
- 047810
- CPNG
- CRCL
- HUT
- MU
- RXRX
- SNDK
- TSLA.

ADR conversion unavailable:

- SKHY
- TSM
- WRD.

fPER:

- unavailable `22/22`.

REV30 must not target-fit or expand these counts.

Any changed coverage means the sealed-source continuation is invalid.

---

# 14. Source-only blind-review seal BEFORE model calls

REV29 did not reach this stage.

After complete 22/22 visibility PASS, but before the first model call, create:

`r2b-r9-rev30-source-only-review.zip`

and:

`.sha256`

It must contain the current sealed REV29 source evidence sufficient for an independent analyst to judge:

- US/KR Market;
- business/financial direction;
- events;
- quality;
- current price;
- technical;
- flow/positioning;
- valuation.

It must exclude:

- any Market model output;
- Core output;
- A output;
- B output;
- final messages;
- Monitoring AI decision labels;
- prior REV24 blind human judgment text.

Record:
- source generation:
  `rev29-live-20260930T042411Z`
- continuation implementation SHA;
- exact whole-source hash;
- archive creation timestamp;
- first model-call timestamp, initially null.

After sealing, it is immutable.

Before first model call verify its SHA and record:

`source_only_sealed_before_models = true`.

---

# 15. Do not perform the blind judgment in the execution session

The execution session must not inspect the source-only archive and write a human investment conclusion.

It must only seal the source-only artifact.

Independent judgment will be performed outside this execution session before Monitoring AI outputs are opened.

This preserves the user's requested blind comparison.

---

# 16. Disk guard

REV29 final free bytes:

`13,420,060,672`

approximately 12.5 GiB.

No collection is required in REV30.

Before first model transmission require:

`free >= 10 GiB`

If below:

`R2B_R9_REV30_DISK_GUARD`

Do not delete the sealed source corpus or blind-review archive to satisfy the guard.

Safe temporary validation cleanup is allowed only if:
- not source evidence;
- not required result evidence;
- recorded.

No destructive generation GC is required in REV30.

---

# 17. Explicit external transmission approval

The user previously required work instructions to explicitly authorize external transmission.

REV30 explicitly approves:

## Model transmission
After:
- repair validation PASS;
- sealed source verification PASS;
- visibility 22/22 PASS;
- source-only review sealed;
- disk guard PASS;

transmit the existing sealed source/model inputs to the existing official:

`GPT-5.6 Sol / xhigh`

Thesis Monitor runner.

Approved logical stages:
- Market:
  `2`
- Core:
  existing frozen 22-subject batching
- A:
  existing frozen 22-subject batching
- B:
  existing frozen 22-subject batching.

Use the same frozen prompt/schema/batching policy as REV29 intended.

No fallback model.
No judge model.
No result-driven source refresh.
No semantic/schema retry.
No selective ticker rerun.

Transport retry behavior must remain exactly the repository's already-frozen authorized transport policy.
REV30 does not create an additional discretionary retry policy.

Do not stop solely to request another approval for this exact official model destination/scope.

## Result upload
Secret-scanned:
- REV30 result ZIP/SHA;
- source-only review ZIP/SHA;
- 24-message human-review ZIP/SHA

may be uploaded to the existing iCloud Drive / Thesis Monitor folder.

---

# 18. Provider/API external transmission

REV30 provider/API data calls:

`0`

The source corpus is already sealed.

Do not call:
- Kiwoom;
- Finnhub;
- FRED;
- EIA;
- ECOS;
- SEC;
- OpenDART;
- event providers;
- any other source provider.

Alpha Vantage:

`0`.

---

# 19. Production side effects

Recipient delivery remains disabled.

Required:

`delivery_disabled = true`

Hard zero:
- Telegram recipient sends;
- production decision/warning DB writes;
- scheduler mutation;
- broker/trading actions;
- deploy;
- main merge;
- remote push;
- service restart.

Operational DB may be read-only only under the existing proof contract.

---

# 20. Fresh model continuation

After all pre-model gates:

run:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`.

This is a model continuation over the exact sealed REV29 source corpus.

No source generation ID change.

Create a separate REV30 continuation ID.

Record:
- source generation ID;
- source implementation SHA;
- continuation repair implementation SHA;
- prompt/schema identities;
- source manifest identity;
- model call ledger.

No prior model outputs exist for REV29, so model-output reuse must be:

`0`.

---

# 21. Accepted-output valuation-use audit

Require:

Qualified valuation may support only:
- NewBuyer valuation context;
- Holder valuation context;
- final Valuation section;
- confidence/caution only where already authorized.

It may not establish:
- Overall business direction;
- Core directional reason;
- Pass-A directional reason;
- supporting/contradicting directional refs.

If any accepted output violates authority:

reject it under the existing validator.

Do not silently strip the violating reason and accept.

---

# 22. Final Market messages

Preserve the accepted Market display-view contract.

US:
- configured indices/proxies;
- display-eligible macro with exact observation dates;
- Market judgment/confidence;
- sectors where qualified;
- KOSPI200 night D/W/M or honest unavailable.

KR:
- completed-session KOSPI/KOSDAQ;
- Market judgment;
- sectors where qualified;
- USD/KRW under current display contract.

No valuation source may affect Market direction.

---

# 23. Final stock messages

Preserve existing accepted detailed renderer plus REV29 provider-native valuation lines.

For qualified valuation:

- provider snapshot qualifier mandatory;
- no invented metric date.

Examples only:

`PER: xx.xx배 · Kiwoom snapshot`

`PBR: x.xx배 · Finnhub quarterly snapshot`

Unavailable:

`판단 자료 부족`

fPER remains unavailable for the sealed REV29 source corpus.

Do not show:
- internal hashes;
- refs;
- debug state;
- retrieval time as metric date.

Do not perform broad renderer redesign in REV30.

Existing detailed-renderer backlog remains P2.

---

# 24. Exact sender-boundary capture

Use production sender payload builder with delivery disabled.

Capture exactly:

- MARKET_US
- MARKET_KR
- US14
- KR8

Total:

`24/24`

Plus:
- `ALL_MESSAGES.md`
- exact payload hashes.

No post-hoc reconstruction.

Telegram:

`0`.

---

# 25. Human-review archive

Create:

`r2b-r9-rev30-24-message-human-review.zip`

+ SHA.

Include:
- exact 24 payloads;
- message hashes;
- model ledger;
- valuation state matrix identity;
- B valuation visibility/use audit;
- direction isolation;
- source generation identity;
- continuation implementation identity;
- sender-boundary proof;
- production isolation.

Do not include a human blind judgment.

---

# 26. Source-only artifact delivery is mandatory

Return/upload the standalone:

`r2b-r9-rev30-source-only-review.zip`

+ SHA

in addition to the result archive.

This artifact is required for the user's next blind human-vs-AI comparison.

Do not make the independent analyst extract source evidence manually from the giant result ZIP if this standalone artifact can be produced.

---

# 27. Structural comparison only

Execution may compare REV24/REV29 expected structural contracts for:

- required message count;
- valuation section presence;
- provider snapshot labels;
- missing required renderer fields;
- authority violations.

Do not compare investment labels to a human target.

Do not tune:
- BUY/SELL;
- NewBuyer;
- Holder;
- confidence

to match prior human judgments.

---

# 28. Success terminal

Use only:

`R2B_R9_REV30_SEALED_SOURCE_CONTINUATION_24_MESSAGE_PASS_READY_FOR_BLIND_HUMAN_REVIEW`

Require:

1. REV29 result integrity verified;
2. exact sealed source identity verified;
3. provider calls 0;
4. source-owner registry unchanged;
5. authority canonical hash repair narrowly scoped;
6. generic unrelated snapshot hashing unchanged;
7. Unicode/ASCII parity tests PASS;
8. tamper negatives PASS;
9. current 22 authority objects consumer/stored parity 22/22;
10. full validation green;
11. sealed whole-source hash unchanged;
12. valuation coverage unchanged;
13. full visibility 22/22 rerun from beginning;
14. Core/A valuation exclusion PASS;
15. B valuation visibility PASS;
16. source-only review ZIP sealed before first model call;
17. pre-model disk >=10 GiB;
18. Market 2/2;
19. Core 22/22;
20. A 22/22;
21. B 22/22;
22. accepted-output valuation authority audit PASS;
23. exact messages 24/24;
24. human-review ZIP generated;
25. Telegram 0;
26. production writes/scheduler/broker/deploy 0;
27. Alpha Vantage 0;
28. secret scan PASS;
29. result/source-only/human-review artifacts sealed;
30. approved iCloud upload receipts complete.

---

# 29. Honest stop terminals

- `R2B_R9_REV30_SEALED_SOURCE_IDENTITY_GAP`
- `R2B_R9_REV30_AUTHORITY_CANONICAL_HASH_CONTRACT_GAP`
- `R2B_R9_REV30_AUTHORITY_HASH_SCOPE_REGRESSION`
- `R2B_R9_REV30_CODE_OWNER_IDENTITY_GAP`
- `R2B_R9_REV30_VISIBILITY_REPROOF_GAP`
- `R2B_R9_REV30_VALUATION_VISIBILITY_GAP`
- `R2B_R9_REV30_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV30_SOURCE_ONLY_SEAL_GAP`
- `R2B_R9_REV30_DISK_GUARD`
- exact model/render/sender failure.

Do not solve any stop by:
- modifying source punctuation;
- rewriting stored authority hashes;
- special-casing MU;
- weakening hash validation;
- recollecting sources;
- skipping subjects;
- changing valuation coverage.

---

# 30. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum include:

## Integrity
- REPORT.md
- summary.json
- REV29 result identity/SHA
- repository identities
- changed-file inventory
- bundle manifest.

## Hash repair
- old producer/consumer contract description;
- changed authority-consumer code;
- Unicode/ASCII parity tests;
- tamper-negative tests;
- generic-digest scope-isolation proof;
- `authority-canonical-parity-22.json`.

## Sealed source continuation
- exact source generation ID;
- whole-source hash proof;
- source-owner registry proof;
- valuation state matrix identity;
- B valuation-context identity;
- provider calls 0 receipt;
- whole-source offline replay proof.

## Visibility
- full 22-subject visibility result;
- A valuation exclusion;
- B valuation visibility;
- direction isolation.

## Blind artifact
- source-only ZIP/SHA identity;
- proof it was sealed before first model call.

## Models
- Market/Core/A/B ledger;
- prompt/schema/source identities;
- transport attempts;
- accepted-output valuation-use audit.

## Messages
- exact24;
- message hashes;
- human-review ZIP/SHA.

## Safety
- Alpha 0;
- Telegram 0;
- production side effects 0;
- secret scan;
- upload receipts.

---

# 31. Final principle

REV29's source and valuation work succeeded.

The failure was not MU evidence, valuation, provider freshness, or model behavior.

It was one deterministic integrity-consumer bug:

the authority producer hashed canonical JSON using ASCII escaping while one consumer validated the same object using
non-ASCII JSON encoding.

Fix the **consumer contract**, not the evidence.

Because no source owner/value changes, the correct proof is to continue from the exact immutable REV29 source corpus,
reprove all 22 visibility subjects under the repaired consumer, seal the blind source-only artifact, and only then run
the models and exact 24-message capture.

Do not spend another 576-provider full-fresh run on a source corpus already proven complete and replay-stable.
