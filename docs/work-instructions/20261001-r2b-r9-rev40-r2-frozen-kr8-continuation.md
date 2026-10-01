# Thesis Monitor — R2B-R9-REV40-R2
## Source-Only Export Identity Contract Repair + Frozen KR8 Model Continuation
### Reuse Exact REV40-R1 Fresh KR8 Source Generation
### Provider Calls 0 / Source Recollection 0
### Repair `whole.seed.parent_run_id` Export Preflight
### Valid Source-Only Blind Seal → Valuation Visibility → KR8 Core/A/B → Exact 8 Stock Messages
### US Provider / US Models / US Messages = 0

**REV40-R2 supersedes every unexecuted post-REV40-R1 continuation instruction. Execute only REV40-R2.**

REV40-R1 did **not** fail on KIS acquisition, current FY1 fPER, storage, validation, or US isolation.

It stopped before the first model call because the frozen source-only export controller used the wrong serialized seed
field:

expected by controller:
`whole.seed.run_id`

actual current full-source contract:
`whole.seed.parent_run_id`.

The source/provider/KIS generation identities were already equal:

`rev40-r1-kr8-20261001T082129Z`

No source value was replaced.
No model was called.
No stock message was generated.

REV40-R2 must repair only the generic export/preflight identity contract and then continue from the exact already-frozen
REV40-R1 source corpus.

---

# 0. REV40-R1 result identity

Adopt REV40-R1 as newest live Korean integration SoT.

Result ZIP:

`thesis-monitor-20261001-r2b-r9-rev40-r1-kr8-live-fper-report.zip`

SHA-256:

`34c3ade5f8b1f640f3d4f88b6aa6a35b82c2da3151ca1236a193addb7e571d35`

Integrity independently verified:

- sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `2926`;
- internal manifest:
  `2925/2925`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

Terminal:

`R2B_R9_REV40_R1_SOURCE_ONLY_SEAL_GAP`

Repository identities from REV40-R1:

- base:
  `8fcb75412d4763df46e946285bf636778e043a73`
- instruction:
  `526833a4739180fdbb913ebb4f4752a9dd47ce10`
- exact tested implementation:
  `f4ac42985fd1824160926e5c2dde269935479cea`
- final local:
  `9ee68b0fda72595e26206ce28fad611214608aea`
- operating/main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- scope:
  `KR8_ONLY`.

REV40-R1 validation:

- focused:
  `496 passed / 1 skipped`
- full:
  `7696 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- diff:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- secret scan:
  PASS.

---

# 1. Diagnostic artifacts are absence packs, not valid blind/model proof

REV40-R1 source-only diagnostic ZIP:

`r2b-r9-rev40-r1-kr8-source-only-review.zip`

SHA-256:

`bd62e80b8dda3973a4ae8977510b8a9abd9b7a17a390f27ffb3f53fb357319dc`

Integrity:
- CRC PASS;
- 7 members;
- manifest 6/6 PASS.

But its status is:

`NO_QUALIFIED_BLIND_SOURCE_PROOF`

and:

`valid_blind_source_pack=false`.

Therefore it must **not** be treated as the user's valid source-only blind artifact.

REV40-R1 human-review diagnostic ZIP:

`r2b-r9-rev40-r1-kr8-human-review.zip`

SHA-256:

`a9fb7bcf392b32a5e7ceaee51bb770b73571ce01a8f8214c271b2d106ed1aa0e`

Integrity:
- CRC PASS;
- 11 members;
- manifest 10/10 PASS.

It correctly records:

- exact stock messages:
  `0`
- expected:
  `8`
- success:
  `false`.

Preserve both as diagnostic evidence.
Do not overwrite or relabel them as PASS artifacts.

---

# 2. Exact stopped source generation

Reuse only:

`rev40-r1-kr8-20261001T082129Z`

Expected current live path:

`/Users/sskim/Documents/Codex/Reports/20261001-r2b-r9-rev40-r1-kr8-live-fper/live`

Before any code/model action verify:

- path exists;
- generation identity equals expected;
- current provider plan identity equals expected;
- current KIS integration identity equals expected;
- no provider files changed after the recorded stop;
- no model output exists.

If the live corpus is missing or changed:

`R2B_R9_REV40_R2_FROZEN_SOURCE_IDENTITY_GAP`

Do not recollect automatically.

---

# 3. Exact full-source serialized identity

REV40-R1 full-source file archived in the result has SHA-256:

`2935bd02c7116e292ea7664d657db89e9d1b7590b757265288c0b08e60f6c1fc`

Expected identity path:

`whole.seed.parent_run_id`

Expected value:

`rev40-r1-kr8-20261001T082129Z`

The failed frozen controller attempted:

`whole.seed.run_id`

and raised:

`KeyError: run_id`.

The repaired contract must use the actual serialized full-source schema.

---

# 4. Repair the shared identity resolver, not the old frozen artifact

Do not hand-edit the already-frozen REV40-R1 report controller and continue as if unchanged.

Repair the generic repository-side source-only export/preflight implementation that produces the controller.

Preferred contract:

`resolve_full_source_generation_identity(whole_source)`

or existing repository-equivalent shared helper.

Rules:

1. canonical current serialized path:
   `seed.parent_run_id`;

2. if legacy `seed.run_id` is supported for old immutable regression fixtures:
   - support it only under an explicit legacy-schema branch;
   - if both fields exist, require exact equality;
   - never silently prefer a conflicting field;

3. value must be a nonempty string;

4. source view generation ID, provider generation ID, KIS generation ID and full-source identity must all be exactly equal;

5. no identity rewriting, relabeling or copy-forward.

Do not add ticker-specific or REV40-specific logic.

---

# 5. Mandatory real serialized-seed regression

REV40-R1 tests missed this because they did not execute the report-side exporter against an actually serialized
whole-source seed.

Add a regression using a real serialized fixture that preserves the relevant exact shape:

```json
{
  "seed": {
    "parent_run_id": "rev40-r1-kr8-20261001T082129Z"
  }
}
```

Required tests:

## Current schema positive
`parent_run_id` only:
PASS.

## Legacy schema positive
`run_id` only:
PASS only if explicit legacy support remains intended.

## Both equal
PASS.

## Both conflicting
FAIL.

## Both absent
FAIL.

## wrong type / empty
FAIL.

## Source-view mismatch
FAIL.

## Provider-plan mismatch
FAIL.

## KIS-generation mismatch
FAIL.

## Real serializer regression
Serialize through the same producer used by the current whole-source graph, then pass the bytes/object to the exact
source-only export preflight.

A hand-built dict test alone is insufficient.

---

# 6. Repair scope

Allowed code change:

- shared full-source identity resolver/preflight;
- source-only exporter/controller generator;
- exact regression tests;
- minimal documentation/report update.

Not allowed:

- provider acquisition semantics;
- KIS FY1 owner;
- current-fPER arithmetic;
- current PER/PBR;
- corporate-action guard;
- business/financial/event source logic;
- model prompts/schema;
- renderer semantics except continuation plumbing required by the existing frozen design;
- US pipeline.

If any of those must change:

stop with a new gap.

---

# 7. Freeze repaired continuation controller

After repair:

- run focused tests;
- full repository tests;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Then freeze a new REV40-R2 continuation controller.

Record:
- base;
- repair commit;
- frozen controller hashes;
- exact source generation identity;
- no provider recollection proof.

No model before this freeze.

---

# 8. Provider/source network budget

REV40-R2 provider calls:

`0`

Explicitly prohibited:

- KIS auth;
- KIS estimate-perform;
- KIS daily price;
- KIS corporate-action routes;
- Kiwoom;
- OpenDART;
- Naver;
- ECOS;
- any KR provider refresh;
- any US provider.

The exact REV40-R1 fresh source corpus is the current source for this continuation.

If any source value is missing:

stop.
Do not refresh.

---

# 9. Preserve REV40-R1 source results

REV40-R1 already proved:

- scope:
  `KR8_ONLY`
- KR composed source:
  `8/8`
- fresh KIS typed states:
  `8/8`
- current FY1 fPER source-owner qualified:
  `7/8`
- 003690:
  FY1 EPS unavailable
- US-only provider calls:
  `0`.

Fresh current-price FY1 fPER source states included:

- 000660:
  `4.78`
- 005490:
  `10.51`
- 005930:
  `5.89`
- 010120:
  `55.43`
- 012450:
  `20.61`
- 047810:
  `54.45`
- 086280:
  `8.78`
- 003690:
  `UNAVAILABLE_EPS`.

These are expected frozen-source replay outputs, not hardcoded model/render values.

Any mismatch against exact source receipts is a stop.

---

# 10. Preserve current valuation independence

Current PER/PBR, FY1 EPS, KIS research FY1 PER and current-price FY1 fPER remain independent.

Examples from frozen source include:

- 000660 current PER/PBR qualified while KIS provider FY1 PER is unavailable due no PER row;
- 010120/047810 current PER/PBR can be unavailable by current security-identity owner while FY1 EPS/current fPER are
  independently qualified.

Do not let one metric suppress an unrelated qualified metric.

No absent=>clean.

---

# 11. Offline replay before source-only seal

With network disabled:

replay the exact frozen KR source and KIS integration.

Require:

- generation identity unchanged;
- KIS replay first/second semantic hash exact match.

REV40-R1 accepted KIS replay hash:

`d62633ef6bd14007de267468990e7ca679d44e318af2ca9b38f432ff538bd70a`

Require source and valuation matrices to reproduce.

No mutable source update.

---

# 12. Produce a valid source-only blind artifact

After repaired preflight PASS and before any model call, create:

`r2b-r9-rev40-r2-kr8-source-only-review.zip`

+ `.sha256`.

This must be a **real blind-review pack**, not a status/diagnostic stub.

Include enough source-only information to independently assess KR8 without seeing Monitoring AI judgment:

## KR supporting market/context
Only current facts actually supplied to the KR stock pipeline.

## KR8 source facts
For every stock:
- business/financial facts;
- directional source refs and exact dates;
- events;
- quality;
- current price;
- technical/flow/positioning;
- current PER/PBR;
- FY1 EPS;
- KIS estimate date;
- current FY1 fPER;
- KIS research FY1 PER when qualified;
- typed unavailable states.

## Provenance
- generation ID;
- source hashes/receipt IDs;
- exact owner states.

Exclude:
- Core output;
- Pass A;
- Pass B;
- model labels/confidence;
- final stock messages;
- previous human blind judgment.

Required:

`source_only_sealed_before_models=true`

and archive SHA/manifest/CRC PASS.

---

# 13. Do not create the blind human judgment in the execution session

The execution session only seals the source-only archive.

It must not:
- read a prior human blind judgment;
- generate a human-vs-AI comparison;
- insert Monitoring AI labels into the source-only pack.

The independent analyst will inspect the valid source-only archive separately.

---

# 14. Valuation visibility gate before models

After source-only sealing and before first model call, run deterministic visibility checks.

For all KR8:

## Core input
Must not contain:
- current FY1 fPER;
- KIS research FY1 PER;
- FY1 EPS as valuation-direction authority.

## Pass A input
Must not contain forward valuation direction authority.

## Pass B
May contain typed valuation context only:
- current PER;
- current PBR;
- FY1 EPS;
- estimate date;
- current FY1 fPER;
- KIS research FY1 PER;
- typed caveats/unavailable states.

Require:

- `overall_direction_use=false`;
- no supporting/contradicting business-direction refs from valuation.

If visibility fails:

`R2B_R9_REV40_R2_VALUATION_VISIBILITY_GAP`

No models.

---

# 15. Model configuration

Use the existing official model path only:

- model:
  `GPT-5.6 Sol`
- effort:
  `xhigh`
- timeout:
  `1200 seconds`
- model semantic retry:
  `0`
- fallback:
  `0`
- judge:
  `0`.

Preserve existing frozen KR batching.

Do not increase model-call budget.

Maximum physical/logical budget remains the existing KR-only frozen controller limit:

`10`

unless the repository's accepted batching proves a stricter lower number.

---

# 16. KR models only

Run only:

- supporting KR Market model if the frozen KR stock architecture requires it;
- KR8 Core;
- KR8 Pass A;
- KR8 Pass B.

Required accepted stock coverage:

- Core:
  `8/8`
- A:
  `8/8`
- B:
  `8/8`.

Do not call:
- US Market;
- US Core/A/B;
- US stocks.

US counters:
`0`.

---

# 17. No result-driven source refresh

Once the source-only archive is sealed:

no provider/source calls.

A model disagreement with a source is not permission to recollect.

No:
- selective ticker refresh;
- result-driven estimate refresh;
- source mutation;
- prompt/schema retry.

If a true source defect is discovered:
stop and issue a new task.

---

# 18. Accepted-output valuation audit

For each accepted Core/A/B output verify:

## Allowed
Forward valuation in:
- NewBuyer valuation;
- Holder valuation;
- valuation-specific caution/context.

## Forbidden
Forward valuation used as:
- Overall business direction;
- Core direction authority;
- Pass-A direction authority;
- supporting/contradicting business evidence.

If an accepted output violates the boundary:

reject it.

Do not silently strip the offending field and call it accepted.

---

# 19. Exact 8 Korean stock messages

After accepted KR8 Core/A/B:

use the production sender payload builder with:

`delivery_disabled=true`

Capture exactly:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280.

Required:

`8/8`.

Do not produce US stock messages.

KR Market message, if generated by existing support flow, is not part of the `8/8` stock success count.

---

# 20. Valuation renderer

For each KR stock, render distinct metrics when qualified:

- current PER
- current PBR
- `현재가 기준 fPER(FY1)`
- `KIS 리서치 fPER(FY1)` with estimate date
- FY1 EPS with KIS Research estimate date.

Do not:
- call KIS Research consensus;
- label it NTM/12M;
- substitute zero for unavailable;
- hide a qualified current-fPER merely because current PER/PBR is unavailable.

Broader renderer backlog remains deferred.

---

# 21. Valid human-review artifact

After exact 8 stock messages, create:

`r2b-r9-rev40-r2-kr8-human-review.zip`

+ SHA.

Include:
- exact 8 sender-boundary stock payloads;
- hashes;
- model ledger;
- KR8 valuation matrix;
- valuation visibility/use audit;
- source/replay identity;
- production isolation.

Do not include independent blind-human judgment.

---

# 22. Storage

REV40-R1 report recorded final free:

`14,369,939,456 bytes`

approximately 13.38 GiB.

REV40-R2 does not need another broad GC.

Before model calls require:

`>= 10 GiB`.

If below:
safe temporary cleanup only.

Do not delete:
- active REV40-R1 fresh source corpus;
- valid REV40-R2 source-only archive;
- immutable result archives;
- current fixtures.

---

# 23. External transmission approval

The user has already approved this KR-only continuation.

## Provider transmission
None.

## Model transmission
Approved after all source seal/visibility gates for:
- KR supporting Market if required;
- KR8 Core/A/B.

## Result upload
After secret scan, upload new REV40-R2:
- result ZIP/SHA;
- valid source-only ZIP/SHA;
- valid human-review ZIP/SHA

to the existing iCloud Drive / Thesis Monitor destination.

No additional approval required for this exact scope.

---

# 24. Production side effects

Hard zero:

- Telegram recipient sends;
- production DB/warning/notification writes;
- scheduler mutation;
- broker/trading;
- deploy;
- main merge;
- remote push;
- restart.

`delivery_disabled=true`.

---

# 25. Validation

Require:

## Repair tests
- current serialized parent_run_id;
- optional legacy run_id;
- both equal;
- both conflicting;
- absent/empty/type mismatch;
- source/provider/KIS identity mismatch;
- real serializer → exact source-seal preflight.

## Existing regressions
- REV39/REV40-R1 KIS FY1/current-fPER tests;
- KR8 no-US scope tests;
- valuation visibility/isolation;
- sender immutability;
- current PER/PBR regression.

## Full validation
- focused;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No source/model continuation on red validation.

---

# 26. Success terminal

Use only:

`R2B_R9_REV40_R2_KR8_FROZEN_SOURCE_8_MESSAGE_PASS_READY_FOR_BLIND_REVIEW`

Require:

1. REV40-R1 result integrity PASS;
2. exact REV40-R1 source generation identity PASS;
3. provider calls 0;
4. source recollection 0;
5. current seed identity repair generic;
6. real serialized-seed regression PASS;
7. full validation green;
8. frozen source replay PASS;
9. current KIS replay exact hash PASS;
10. KR8 source states reproduce 8/8;
11. current FY1 fPER source states reproduce 8/8 typed;
12. valid new source-only ZIP sealed before models;
13. source-only pack contains actual source facts;
14. Core forward valuation exclusion PASS;
15. A forward valuation exclusion PASS;
16. B forward valuation visibility PASS;
17. premodel free >=10 GiB;
18. KR Core accepted 8/8;
19. KR A accepted 8/8;
20. KR B accepted 8/8;
21. valuation direction-leak audit PASS;
22. exact KR stock messages 8/8;
23. valid human-review ZIP;
24. US provider/model/message 0;
25. Telegram 0;
26. production mutations 0;
27. secret scan PASS;
28. result/source-only/human-review archives generated and uploaded.

---

# 27. Honest stop terminals

- `R2B_R9_REV40_R2_REV40_R1_INTEGRITY_GAP`
- `R2B_R9_REV40_R2_FROZEN_SOURCE_IDENTITY_GAP`
- `R2B_R9_REV40_R2_SOURCE_SEED_SCHEMA_GAP`
- `R2B_R9_REV40_R2_SOURCE_ONLY_SEAL_GAP`
- `R2B_R9_REV40_R2_VALUATION_VISIBILITY_GAP`
- `R2B_R9_REV40_R2_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV40_R2_DISK_GUARD`
- exact KR model failure
- exact KR render/sender failure
- `R2B_R9_REV40_R2_VALIDATION_GAP`.

Do not solve by:
- provider refresh;
- generating a new source generation;
- manually patching generation IDs;
- omitting the blind seal;
- expanding to US.

---

# 28. Required result bundle

Return immutable result ZIP + SHA.

Also standalone:
- `r2b-r9-rev40-r2-kr8-source-only-review.zip`
- `.sha256`
- `r2b-r9-rev40-r2-kr8-human-review.zip`
- `.sha256`.

Result bundle at minimum:

## Integrity
- REPORT.md
- summary.json
- REV40-R1 result identity/SHA
- repository identities
- changed files
- manifest.

## Repair proof
- seed schema contract
- real serialized-seed fixture
- test receipts
- old failure reproduction
- repaired source-seal PASS.

## Frozen source proof
- live source identities
- no-provider counters
- replay receipts
- KIS replay hash
- KR8 source/valuation matrices.

## Blind proof
- source-only ZIP/SHA
- `sealed_before_models=true`
- source-only content inventory.

## Visibility/model
- Core/A exclusion
- B valuation visibility
- model call ledger
- acceptance audit.

## Messages
- exact 8 KR sender payloads
- hashes
- human-review ZIP/SHA.

## Safety
- US provider/model/message 0
- provider calls 0
- Telegram 0
- production mutations 0
- secret scan.

---

# 29. Next handoff

If PASS:

1. independent analyst must inspect the **REV40-R2 valid source-only pack first**;
2. freeze a KR8 blind judgment;
3. only then inspect the REV40-R2 human-review/model outputs;
4. compare how current FY1 fPER affected NewBuyer/Holder entry calibration;
5. keep US forward-EPS source qualification as a separate task;
6. keep broad renderer restoration as a separate task.

No automatic Core/A/B retuning from the comparison.

---

# 30. Final principle

REV40-R1 successfully acquired the new Korean source capability.

Do not throw that fresh source away because the export controller looked for the wrong field name.

Repair the serialized identity contract generically.

Then prove:

- valid source-only blind seal;
- strict valuation visibility;
- KR8-only models;
- exact 8 stock messages.

No provider recollection and no US expansion are required.
