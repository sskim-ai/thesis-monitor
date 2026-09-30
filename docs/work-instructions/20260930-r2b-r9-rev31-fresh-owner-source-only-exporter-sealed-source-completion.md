# Thesis Monitor — R2B-R9-REV31
## Fresh-Owner Source-Only Exporter Repair
### Exact Sealed REV29 Source Reuse — Provider Calls 0
### Blind Source Archive Seal → Market/Core/A/B → Exact 24-Message Human Review
### KIS FY1 EPS/fPER Work Explicitly Deferred to the Next Independent Revision

**REV31 supersedes every prior unexecuted post-REV30 instruction. Execute only REV31.**

REV30 successfully closed the authority-hash canonicalization defect.

It proved:

- authority canonical parity:
  `22/22`;
- full 22-subject visibility reproof:
  PASS;
- provider-native valuation coverage unchanged:
  - PER qualified:
    `8`
  - PBR qualified:
    `10`
  - fPER qualified:
    `0`;
- Core/A valuation exclusion:
  PASS;
- B valuation-context binding:
  PASS;
- provider calls:
  `0`;
- model calls:
  `0`.

REV30 then stopped at the **source-only blind archive export boundary** before the first model call.

Root cause:

`scripts.r2b_sealed_blind_preflight.source_only_stock`

still expects the legacy field:

`financial_bindings`

while every current sealed fresh-stock object now uses the fresh-owner contract, including:

- `financial_source_graph`;
- `selected_financial_owner`;
- `financial_state`;
- `evidence_packet`;
- `source_graph`;
- `quality_view`;
- `valuation_view`;
- other current source-owned fields.

All 22 sealed fresh-stock objects lack `financial_bindings`.

This is an exporter contract mismatch.
It is not missing financial evidence.

REV31 must repair only the source-only facts exporter, seal the blind archive, and continue the already-qualified
sealed source through the models and exact 24-message boundary.

Do **not** recollect any source.

---

# 0. Newest SoT

Adopt REV30 as the newest continuation implementation/result SoT.

REV30 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev30-authority-canonical-parity-report.zip`

SHA-256:

`48c862bc8103a0bc900359156df05cae84fdc38648a299c633ca74886f29df2b`

Independent verification:

- sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `156`;
- internal manifest:
  `155/155`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

REV30 terminal:

`R2B_R9_REV30_SOURCE_ONLY_SEAL_GAP`

Repository:

- base:
  `a3a99eff7c5fa38491ca3193cdc91c4772df216b`
- instruction:
  `72f74e90b943d3b0f69db148c909242095abbf01`
- validated implementation:
  `c5984bcdc2102bb31c274fb32c8a336cc3d6b214`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.

REV30 validation:

- focused:
  `196 passed / 0 failed`
- full:
  `7021 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- changed-file secret scan:
  PASS.

---

# 1. Exact sealed source corpus

REV31 is a continuation of the exact sealed REV29 generation.

Source generation:

`rev29-live-20260930T042411Z`

Whole-source semantic SHA-256:

`0dcc42dd3d237794f8cf4a50aa5a491afa8082b19d273bfca5e38f7f129baa3d`

Source-owner registry SHA-256:

`c995c02c82bf1ed97c599402a70d91c0782ed40c7de8fba85e4f55db178f1cc5`

Fresh valuation state matrix SHA-256:

`01999df2e5ede4565a4c114fa7f71bf69daddf4ebf906068b8d43a8142ffd7bb`

B valuation-context replay SHA-256:

`7e1cd3f0acc8d0dc267fb487d8897ef4dcb16c587533a420b273336db9d6f510`

Direction-isolation audit SHA-256:

`9823a3ffefa2c00937af852446671cc1fb2cd855d0945c17fd7b8617ab6549bb`

These identities must not change.

Provider/API calls in REV31:

`0`

If any exact source identity differs:

`R2B_R9_REV31_SEALED_SOURCE_IDENTITY_GAP`

Do not recollect.

---

# 2. Preserve REV30 authority-hash repair

Do not reopen the canonical hash repair.

Require:

- current sealed authority objects:
  `22/22`
- stored == producer canonical == consumer canonical.

No:
- Unicode normalization;
- source-string modification;
- stored-hash rewrite;
- MU special case.

Generic unrelated digest behavior stays unchanged.

---

# 3. Exact exporter root cause

REV30 read-only inventory proved:

`missing_legacy_field = 22`

All 22 current fresh-stock source objects expose the current fresh-owner schema.

The exporter failure is:

`KeyError: financial_bindings`

First ordered subject:

`000660`

No partial source-only payload files were written.

No model was called.

Therefore the correct repair is:

> update the source-only exporter to consume the **current fresh-owner source contract**, not rebuild a legacy
> `financial_bindings` compatibility object.

Do not reintroduce the legacy field into the production fresh-stock object just to satisfy the exporter.

---

# 4. Source-only exporter purpose

The source-only archive exists for an independent analyst to make a blind investment judgment **before seeing
Monitoring AI outputs**.

It must contain enough current evidence to assess:

- US/KR Market;
- business and financial direction;
- events;
- evidence quality;
- current completed-session price;
- technical state;
- flow/positioning;
- valuation.

It must exclude all downstream AI decisions.

The exporter is a facts/evidence projection, not a model-input clone.

---

# 5. Required stock facts-only projection

For every US14 + KR8 subject, export source-owned information from the current fresh object.

At minimum preserve semantically:

## Identity
- ticker/security ID;
- market;
- fresh generation ID.

## Financial/business
- current selected financial owner;
- selected current/prior comparisons;
- exact facts needed to understand revenue/operating-income direction;
- comparison eligibility/denial;
- source periods/dates;
- financial quality relevant to those facts;
- source refs/provenance sufficient for later audit.

Use:
- `selected_financial_owner`;
- `financial_source_graph`;
- `financial_state`;
- related current fresh-owner fields.

Do not depend on:
`financial_bindings`.

## Events/business context
- qualified current event facts;
- typed unavailable/denial state;
- source dates.

## Current price
- completed-session current price;
- session date;
- exact owner/provenance.

## Technical
- current-effective technical features required for independent review;
- period/session identity.

## Quality
- field-level/source-level quality state;
- exact denials/anomalies relevant to interpretation.

## Valuation
- PER state/value/provider snapshot metadata when qualified;
- PBR state/value/provider snapshot metadata when qualified;
- fPER state;
- ADR/security-identity denial where relevant.

## Flow/positioning
- current qualified source-owned fields;
- honest unavailable state.

Do not add an analysis label.

---

# 6. Market facts-only projection

Export US and KR current Market source facts sufficient for blind assessment.

Include:
- completed-session major index/proxy moves;
- display-eligible macro/FX values with exact observation dates;
- current qualified sector/breadth/flow facts;
- typed unavailable sector/night states;
- exact source/currentness metadata.

Do not include:
- Market AI judgment;
- Market AI confidence;
- any prior model direction.

---

# 7. Explicit downstream-output exclusion

The source-only archive must prove absence of:

- Market model output;
- Core output;
- Pass A output;
- Pass B output;
- BUY/SELL AI decision label;
- AI balance score;
- AI confidence;
- AI NewBuyer label;
- AI Holder label;
- AI reevaluation text;
- final rendered messages;
- prior REV24 independent human judgment;
- prior human-vs-AI comparison labels.

Also exclude model raw responses and accepted-result payloads.

It is acceptable to include source-stage eligibility labels such as:
- `verified_usable`;
- `display_eligible`;
- `direction_eligible`;
- typed source denial;

because these are deterministic source contracts, not Monitoring AI investment decisions.

---

# 8. No prompt leakage

Do not make the blind artifact depend on opening model outputs.

Prefer not to include model prompts/schemas in the source-only archive.

If a source-only projection reuses a deterministic pre-model materializer, explicitly remove:
- instructions telling the model how to decide;
- target labels;
- model-stage-specific summaries that may bias the independent analyst.

The archive is an evidence package.

---

# 9. Fresh-owner projection tests

Add exact tests for all 22 current object shapes.

Required:

- exporter succeeds when `financial_bindings` is absent;
- exporter consumes `selected_financial_owner` and `financial_source_graph`;
- no legacy field reconstruction required;
- no missing financial selected facts;
- no duplicate financial owner rows;
- field-level quality remains isolated;
- valuation state/value retained;
- current price/technical retained;
- events retained;
- unavailable states retained.

Negative:
- selected financial owner missing when contract says required → fail;
- owner ref points outside source graph → fail;
- valuation qualified value without source receipt → fail;
- model/output key injected into source object → exporter exclusion proof catches/removes it or fails according to
  the chosen explicit contract.

No ticker-specific logic.

---

# 10. Whole-cohort source-only archive validation

Before sealing, build all:

`22/22`

stock facts projections plus:

`2/2`

Market facts projections.

Require:

- exactly current roster;
- no missing subject;
- no duplicate subject;
- current source generation only;
- source identities match Section 1;
- no old-generation mutable values;
- no downstream-output keys.

Create:

`source-only-projection-audit.json`

with:
- included subjects;
- included source categories;
- excluded downstream categories;
- per-subject projection SHA;
- source object SHA;
- generation identity.

---

# 11. Blind archive

Create standalone:

`r2b-r9-rev31-source-only-review.zip`

and `.sha256`.

Contents should be compact enough for external independent review but complete enough to judge the current source.

At minimum:
- README / contract;
- US Market facts;
- KR Market facts;
- US14 stock facts;
- KR8 stock facts;
- valuation state matrix identity;
- source graph/owner references needed for audit;
- source-only projection audit;
- manifest.

Do not include full giant raw provider corpora unless required to support a selected fact.
Use exact selected source evidence plus provenance references.

This artifact must be immutable after sealing.

---

# 12. Seal-before-model proof

Create:

`source-only-before-model-proof.json`

Require:

- source-only ZIP SHA;
- sealed timestamp;
- first model-call timestamp initially null;
- `source_only_sealed_before_models = true`;
- source generation ID;
- whole-source SHA;
- continuation implementation SHA.

Immediately before first model call:
- verify source-only ZIP SHA again;
- record exact proof without rewriting the ZIP.

If the blind archive cannot be created:

stop:

`R2B_R9_REV31_SOURCE_ONLY_SEAL_GAP`

No model calls.

---

# 13. Do not perform independent human judgment in execution

Execution session must not:
- read the sealed blind archive and create an investment opinion;
- compare it to prior Monitoring AI;
- tune prompts/output to human labels.

The independent judgment is performed outside this execution after artifacts return.

---

# 14. Full validation before model continuation

Before model calls run:

- focused source-only exporter tests;
- source-only downstream-exclusion tests;
- all22 source-only cohort tests;
- authority canonical parity tests;
- valuation integration tests;
- whole-source registry tests;
- visibility tests;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Full suite must be green.

Freeze implementation.

No prompt/source/schema changes after freeze.

---

# 15. Reprove full visibility 22/22

Even though REV30 already passed visibility:

after exporter repair implementation freeze, run the full 22 visibility preparation again with network disabled.

Require:

`22/22 PASS`

This proves the exporter-only code change did not affect:
- Core/A source eligibility;
- authority hashes;
- valuation isolation;
- B valuation context.

No selective continuation from a prior ticker.

---

# 16. Valuation coverage remains frozen

Preserve exact REV29/REV30 sealed coverage:

PER + PBR:
- 000660
- 003690
- 005490
- 005930
- 012450
- 086280
- GOOGL
- IBM

PBR only:
- CORZ
- WULF

Identity unavailable:
- 010120
- 047810
- CPNG
- CRCL
- HUT
- MU
- RXRX
- SNDK
- TSLA

ADR conversion unavailable:
- SKHY
- TSM
- WRD

fPER:
- unavailable `22/22`.

Any changed coverage invalidates sealed-source continuation.

---

# 17. Disk guard

REV30:

- before free bytes:
  `12,413,927,424`
- after free bytes:
  `11,692,756,992`.

No provider collection occurs in REV31.

Before first model call require:

`free >= 10 GiB`

If below:
perform only safe temporary/report cleanup that does not remove:
- sealed source;
- source-only archive;
- immutable result archives;
- required fixtures.

Record any cleanup.

If still below:

`R2B_R9_REV31_DISK_GUARD`

No model calls.

---

# 18. External transmission approval

The user explicitly approves the following REV31 external transmissions.

## Model runner
After all pre-model gates PASS, transmit the exact sealed source/model inputs to the existing official:

`GPT-5.6 Sol / xhigh`

Thesis Monitor runner.

Approved stages:
- Market:
  `2`
- Core:
  existing frozen batching
- A:
  existing frozen batching
- B:
  existing frozen batching.

Use current prompt/schema/batching contracts.

No fallback model.
No judge model.
No result-driven source refresh.
No semantic/schema retry.
No selective ticker rerun.

Transport retry:
only the already-frozen repository policy.
No new discretionary retry permission.

## iCloud
Secret-scanned:
- REV31 result ZIP/SHA;
- REV31 source-only ZIP/SHA;
- REV31 24-message human-review ZIP/SHA

may be uploaded to the existing iCloud Drive / Thesis Monitor folder.

Do not request redundant approval for this exact scope.

---

# 19. Provider/API calls remain zero

REV31 provider calls:

`0`

This includes:
- Kiwoom;
- Finnhub;
- SEC;
- OpenDART;
- FRED;
- EIA;
- ECOS;
- news/event providers;
- KIS;
- Alpha Vantage.

KIS is explicitly deferred to REV32 so it cannot contaminate this blind sealed-source proof.

---

# 20. Model continuation

After:
- source-only sealed;
- visibility 22/22;
- valuation visibility/isolation PASS;
- disk >=10 GiB;

run:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`.

No prior REV29/REV30 model outputs exist.

Model-output reuse:

`0`.

Record:
- source generation ID;
- continuation ID;
- implementation SHA;
- prompt/schema identities;
- input manifest;
- model call ledger.

---

# 21. Accepted-output valuation authority

Preserve:

qualified provider-native valuation may affect:
- NewBuyer context;
- Holder context;
- valuation-specific caution/confidence where currently authorized.

It cannot independently establish:
- Overall direction;
- Core directional reason;
- A directional reason;
- supporting/contradicting directional refs.

Reject authority violations.

Do not silently strip and accept.

---

# 22. Exact 24-message capture

Use production sender payload builder with:

`delivery_disabled = true`.

Capture:
- MARKET_US;
- MARKET_KR;
- US14;
- KR8.

Total:

`24/24`.

Also create:
- `ALL_MESSAGES.md`;
- exact message hashes.

No post-hoc reconstruction.

Telegram sends:

`0`.

---

# 23. Human-review archive

Create:

`r2b-r9-rev31-24-message-human-review.zip`

+ `.sha256`.

Include:
- exact 24 payloads;
- hashes;
- source generation identity;
- model ledger;
- valuation state identity;
- valuation-use audit;
- production isolation;
- required validation.

Do not include the independent blind human judgment.

---

# 24. Production side effects

Hard zero:
- Telegram recipient sends;
- production decision/warning DB writes;
- scheduler mutation;
- broker/trading;
- deploy;
- main merge;
- remote push;
- service restart.

Provider calls also zero in this continuation.

---

# 25. KIS FY1 EPS/fPER — mandatory next-work queue, not REV31 execution

The user explicitly selected the free-KIS route for Korean forward valuation.

REV31 must record a next-work handoff:

`next-work-kis-forward-eps.json`

with the following intended REV32 scope.

Official KIS endpoint verified externally:

- category:
  `국내주식 종목정보`
- name:
  `국내주식 종목추정실적`
- path:
  `/uapi/domestic-stock/v1/quotations/estimate-perform`
- input:
  exact Korean stock code (`sht_cd`);
- official KIS repository shows four output groups.

REV32 goal:
- bounded KR8 live capability probe;
- determine actual output schema/period labels;
- identify exact future fiscal-year rows;
- qualify `FY1 EPS`;
- qualify provider-native forecast PER if semantics are exact;
- optionally derive `FY1 fPER = current completed-session price / FY1 EPS` only if security/price/EPS basis compatibility is
  explicitly owned;
- never call FY1 metric `12M Forward` unless source semantics prove 12M/NTM;
- no FnGuide paid source;
- no broad full-fresh until the KIS contract is proven.

REV31 must **not call KIS**.

Reason:
adding KIS current data now would change the sealed source corpus before the blind REV29/REV31 comparison is completed.

---

# 26. Success terminal

Use only:

`R2B_R9_REV31_FRESH_OWNER_SOURCE_ONLY_SEAL_24_MESSAGE_PASS_READY_FOR_BLIND_HUMAN_REVIEW`

Require:

1. REV30 archive integrity PASS;
2. sealed REV29 source identities unchanged;
3. authority parity 22/22;
4. exporter consumes current fresh-owner contract;
5. no `financial_bindings` dependency;
6. all22 stock facts projection PASS;
7. Market2 facts projection PASS;
8. downstream AI output exclusion PASS;
9. source-only ZIP sealed;
10. source-only sealed before first model call;
11. full test suite green;
12. visibility 22/22 PASS after repair;
13. valuation coverage unchanged;
14. provider calls 0;
15. pre-model free >=10 GiB;
16. Market 2/2;
17. Core 22/22;
18. A 22/22;
19. B 22/22;
20. valuation-use authority PASS;
21. exact messages 24/24;
22. human-review ZIP generated;
23. Telegram 0;
24. production side effects 0;
25. source-only/result/human-review secret scan PASS;
26. approved iCloud upload receipt complete;
27. KIS FY1 next-work handoff recorded but not executed.

---

# 27. Honest stop terminals

- `R2B_R9_REV31_SEALED_SOURCE_IDENTITY_GAP`
- `R2B_R9_REV31_FRESH_OWNER_EXPORTER_CONTRACT_GAP`
- `R2B_R9_REV31_SOURCE_ONLY_DOWNSTREAM_LEAK`
- `R2B_R9_REV31_SOURCE_ONLY_SEAL_GAP`
- `R2B_R9_REV31_VISIBILITY_REPROOF_GAP`
- `R2B_R9_REV31_VALUATION_VISIBILITY_GAP`
- `R2B_R9_REV31_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV31_DISK_GUARD`
- exact model/render/sender failure.

Do not solve a stop by:
- source refresh;
- provider call;
- legacy-field injection into fresh source;
- subject-specific special case;
- source hash rewrite;
- skipping blind seal.

---

# 28. Required result artifacts

Return immutable result ZIP + `.sha256`.

Also return independently:

- `r2b-r9-rev31-source-only-review.zip`
- its `.sha256`
- `r2b-r9-rev31-24-message-human-review.zip`
- its `.sha256`.

Result ZIP at minimum contains:

## Integrity
- REPORT.md
- summary.json
- REV30 identity/SHA
- repository identities
- changed files
- bundle manifest.

## Exporter repair
- fresh-owner exporter contract
- legacy-field absence test
- projection tests
- downstream exclusion tests
- source-only projection audit.

## Source continuation
- source generation identity
- whole-source hash
- source-owner registry
- authority parity 22
- visibility 22
- valuation state identity
- provider calls 0.

## Blind seal
- standalone source-only ZIP identity/SHA
- seal timestamp
- first model-call timestamp
- seal-before-model proof.

## Models
- Market/Core/A/B ledger
- prompt/schema/input identities
- accepted-output valuation-use audit.

## Messages
- exact24
- message hashes
- human-review ZIP/SHA.

## Next work
- `next-work-kis-forward-eps.json`.

## Safety
- KIS calls 0
- Alpha 0
- Telegram 0
- production side effects 0
- secret scan.

---

# 29. Final principle

REV30 already proved the sealed source, authority hashes, visibility and valuation pipeline are correct.

The only blocker is an obsolete blind-export projection that still expects a removed legacy field.

Repair the exporter to read the **current fresh-owner facts**, not to mutate source objects backward into the legacy
schema.

Seal the blind source artifact before any model call.
Then finish the exact 24-message proof.

Only after this blind comparison corpus is safely sealed and completed should the project add the free KIS
`estimate-perform` route for Korean FY1 EPS/fPER in the next independent revision.
