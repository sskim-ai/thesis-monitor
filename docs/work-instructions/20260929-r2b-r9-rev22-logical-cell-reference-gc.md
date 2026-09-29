# Thesis Monitor — R2B-R9-REV22
## SEC Logical Same-Cell Same-Target Reference Group Ownership
### Archive-Backed Storage GC → New Full-Fresh All-Source Requalification → Replay Twice → Fresh Market/Core/A/B → Exact Detailed 24-Message Proof

**REV22 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV22.**

REV21 correctly stopped without implementation.

Its read-only evidence proves the previous REV21 assumption was too narrow:

- the affected SEC 20-F exhibit descriptions are **not** multiple text fragments inside one `<a>`;
- they are multiple **distinct `<a>` elements**;
- those anchors:
  - are in the same exact table row;
  - are in the same exact table cell;
  - point to the same exact exhibit document;
  - appear in a deterministic DOM/byte order;
  - collectively form the human-readable exhibit description.

REV21 was correct not to merge them because its instruction explicitly prohibited cross-anchor merging.

REV22 introduces a narrower structural contract:

> Multiple SEC exhibit anchors may form one logical reference group only when exact source structure proves they are one same-cell, same-target, contiguous exhibit-label presentation.

This is **not** a general cross-anchor concatenation rule.

Do not:
- merge across rows;
- merge across cells;
- merge different href/document identities;
- merge ambiguous or conflicting references;
- classify from filename alone;
- increase financial-document cap;
- weaken purpose fail-closed behavior;
- hardcode TSM;
- reuse prior mutable/current source values.

After offline closure:
1. use the sealed REV21 boundary fixture;
2. extract only any additional minimum fixture if needed;
3. verify immutable prior archives;
4. execute archive-backed storage GC;
5. start a completely new full-fresh generation;
6. require stock-source 22/22;
7. compose whole-source and replay twice;
8. run fresh Market/Core/A/B;
9. capture exact 24 sender-boundary messages.

---

# 0. Newest SoT

Adopt REV21 evidence report as the newest diagnostic SoT.

REV21 result ZIP SHA-256:

`922e56836ade9ceb7f884d2baf0d48453f81089b227eb151418daa7a80d87492`

Uploaded sidecar:
exact match.

Independent verification:

- ZIP CRC:
  PASS
- ZIP members:
  `26`
- internal manifest entries:
  `25`
- missing:
  `0`
- SHA mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV21_LOGICAL_EXHIBIT_DESCRIPTION_GAP`

Repository:

- branch:
  `codex/r2b-r9-rev21-logical-exhibit-routing-gc`
- base:
  `82423964faaf480440bb5a5068e7e41becb5a64f`
- instruction/final:
  `57bed90597997173639d5702a9daab67c8eb5cc7`
- implementation:
  none
- production code changes:
  `0`
- local-only:
  true
- main merge/push/deploy:
  `0`

REV21 operational state:

- provider calls:
  `0`
- model calls:
  `0`
- messages:
  `0/24`
- GC:
  `0`
- free bytes:
  `15,321,522,176`
- P0:
  `0`
- P1:
  `1`

REV21 explicitly preserved the prior TSM denial:

`FPI_FINANCIAL_DOCUMENT_CANDIDATE_BOUND_EXHAUSTED`

and did not alter classification.

---

# 1. Preserve all prior closed contracts

Do not reopen:

- canonical whole-source code-owner registry;
- completed-session current-price owner;
- Pass-A source-family visibility intersection;
- SNDK 52/53-week fiscal contract;
- TSM current 2026-06-30 financial authority;
- FPI finite candidate/document bounds;
- exact iXBRL field/context/unit ownership;
- same-accession cover→financial-attachment semantics;
- WRD asset/document slot accounting;
- selected financial owner;
- latest-published FX;
- current-effective technical semantics;
- OpenDART;
- event ownership;
- ECOS CYCLE ownership;
- KR completed-session technical owner;
- KOSPI200 typed unavailable;
- Market display contract;
- UNKNOWN_LIMIT;
- R7 absolute-current direction guard;
- quality/valuation semantics;
- detailed stock renderer;
- Core/A/B policy.

REV22 changes only SEC logical exhibit-description structural ownership and the resulting exact non-financial routing.

---

# 2. Exact REV21 source evidence

REV21 proved:

- affected annual documents:
  `12`
- anchor counts:
  - `2 anchors`: 10 documents
  - `3 anchors`: 2 documents
- every affected anchor individually contains one text fragment;
- every affected document's anchors are:
  - distinct anchors;
  - same row;
  - same cell;
  - same target document identity.

Examples:

## Articles of Incorporation

Same cell, same target `exhibit11.htm`:

1.
`Articles of Incorporation of Taiwan Semiconductor Manufacturing Company Limited, as `

2.
`amended and restated on June 3, 2025.`

## Land Lease

Same cell, same target `exhibit429.htm`:

1.
`Land Lease with Hsinchu Science Park Administration relating to AP3 located in Longtan `

2.
`Science Park (effective August 1, 2025 to December 31, 2034) (English summary). `

## Three-anchor lease

Same cell, same target `exhibit435.htm`:

1.
`Land Lease with Southern Taiwan Science Park Administration relating to the facility `

2.
`warehouse in Southern Taiwan Science Park (effective December 16, 2025 to November 30, `

3.
`2038) (English summary). `

The source HTML shows these as line-layout anchor splits inside one `<td>`.

REV21 also proves a critical positive financial control:

current 6-K financial statement target:

`a2026q2consolidatedreport-.htm`

is represented by **8 distinct anchors** in one cell, all pointing to the same target, whose ordered text forms:

`Consolidated Financial Statements for the Six Months Ended June 30, 2026 and 2025 and Independent Auditors’ Review Report ...`

Therefore same-cell grouping must preserve this as a **financial** description.

Do not create a rule that only groups legal exhibits.

---

# 3. Typed LogicalCellReferenceGroup

Create a structural owner, repository naming permitting:

`LogicalCellReferenceGroup`

This owner sits below financial/non-financial purpose routing.

It determines only whether several exact anchors represent one logical SEC reference label.

Required identity:

- accession;
- filing form;
- source primary document;
- source row ID / structural identity;
- source cell ID / structural identity;
- canonical target href;
- canonical target document identity;
- ordered anchor identities;
- exact anchor byte spans;
- exact anchor HTML hashes;
- exact raw anchor texts;
- normalized joined label;
- group SHA;
- ambiguity state.

It does **not** decide financial purpose itself.

---

# 4. Exact grouping eligibility

Multiple distinct anchors may be grouped only if **all** are proven:

1. same accession;
2. same source primary document;
3. same exact `<tr>` structural owner;
4. same exact `<td>` structural owner;
5. every grouped anchor is an SEC exhibit/reference anchor under the current exact parser contract;
6. every grouped anchor resolves to the same canonical target href/document identity;
7. anchors have one deterministic DOM/byte order;
8. the anchors form one contiguous same-target reference block within that cell;
9. no different-target exhibit anchor interrupts the block;
10. no meaningful non-whitespace unlinked text interrupts the block;
11. no source parser ambiguity about row/cell/anchor ordering;
12. every raw anchor/span remains preserved in provenance.

If any condition fails:
do not group.

---

# 5. “Same target” alone is insufficient

Do not group anchors merely because:

- href is equal;
- filename is equal;
- anchor text appears related;
- human reading suggests continuation.

Grouping requires the exact structural cell/row/contiguity contract in Section 4.

Negative examples:

- same href in different rows → no group;
- same href in different cells → no group;
- same href separated by another target anchor → no group;
- same href separated by meaningful plain text → no group unless a separately approved source-owner contract owns that text;
- different href but similar filename/text → no group;
- cross-accession → forbidden.

---

# 6. Cell-level anchor inventory

Before grouping, enumerate the exact ordered exhibit-anchor inventory for each candidate cell.

Record:

- all exhibit anchors in cell;
- all href targets;
- byte order;
- DOM order;
- intervening text nodes;
- intervening non-exhibit anchors;
- raw text;
- source spans.

Create:

`logical-cell-reference-inventory.json`

The grouping decision must be reproducible from this inventory.

No hidden DOM heuristic.

---

# 7. Contiguous same-target block

Define a contiguous block over the ordered exhibit/reference sequence.

A block may contain 1..N anchors.

For N > 1, all anchors in the block must:

- have same target;
- be adjacent in the relevant exhibit-anchor sequence;
- remain in one cell;
- have no conflicting text/reference between them.

The source may wrap each anchor in separate `<div>/<span>` layout containers.

Presentation wrappers and whitespace do not break the block.

Meaningful content with another target or unowned text does.

---

# 8. Logical label normalization

After structural grouping PASS:

- concatenate group anchor texts in source order;
- normalize Unicode under existing text policy;
- preserve punctuation;
- collapse only layout/whitespace boundaries;
- do not invent words;
- do not drop words;
- do not reorder tokens.

Store:

- raw piece list;
- normalized group label;
- normalization version;
- normalized SHA.

The original anchors remain independently auditable.

---

# 9. Multiple groups/references for one document

The same target document may still have multiple logical groups elsewhere.

Do not merge them automatically.

Each `LogicalCellReferenceGroup` is classified independently.

If multiple groups for the same target disagree in purpose:

`DOCUMENT_REFERENCE_PURPOSE_CONFLICT`

and fail closed.

If all exact groups are compatible:
the document may receive that compatible route under existing precedence policy.

---

# 10. Purpose routing happens after grouping

Purpose router input becomes:

`LogicalCellReferenceGroup.normalized_label`

or a single-anchor logical group.

Do not route on individual continuation anchors when a valid structural group exists.

Do not route before structural ambiguity is resolved.

---

# 11. Corporate governance route

Preserve a generic exact route such as:

`CORPORATE_GOVERNANCE_INSTRUMENT_NON_FINANCIAL`

Allowed when the full logical label unambiguously identifies:

- Articles of Incorporation;
- amended/restated Articles of Incorporation;
- charter/bylaws/governance instrument under the existing exact routing registry;

and does not describe:

- financial statements;
- financial results;
- earnings;
- accounting schedules.

For the REV21 fixture, the grouped `exhibit11.htm` description should be classified from the full logical label, not either fragment alone.

No TSM-specific condition.

---

# 12. Property/land lease legal route

Preserve/add generic route:

`PROPERTY_LEASE_AGREEMENT_NON_FINANCIAL`

Only when the full logical label unambiguously identifies a legal land/property lease agreement.

Positive structural/semantic shape may include:

- `Land Lease with <counterparty> ...`
- facility/location identity;
- effective date range;
- `English summary`.

The full label must not identify:

- lease liabilities;
- right-of-use assets;
- lease accounting policy;
- financial statement note;
- financial results;
- accounting schedules.

Substring `lease` alone is insufficient.

---

# 13. Financial statement route remains financial

The same grouping contract must reconstruct the current 6-K 8-anchor label.

The grouped label contains:

`Consolidated Financial Statements ... Six Months Ended June 30, 2026 and 2025 ... Independent Auditors’ Review Report ...`

This must remain:

- financial candidate;
- qualified financial statement when the existing content-purpose owner permits it;
- consuming the appropriate financial document slot.

This is a mandatory anti-overrouting control.

---

# 14. Exact REV21 regression matrix

Using only the sealed REV21 fixture:

Produce:

`rev21-logical-cell-reference-regression-matrix.json`

Required rows:

- 12 annual previously blocked documents;
- current 6-K financial statement group.

For every row record:

- anchor count;
- same row;
- same cell;
- same target;
- contiguity;
- intervening meaningful text;
- grouping decision;
- normalized logical label;
- purpose route;
- financial-slot consumption;
- source/provenance hashes.

Expected structural grouping:

- all 12 annual evidence rows:
  group only if Section 4 passes;
- current 6-K financial row:
  group if Section 4 passes.

Do not predetermine purpose if a row fails exact grouping.

---

# 15. Bound behavior after routing

Financial attachment/document cap remains unchanged.

Do not raise it.

After exact logical grouping + routing:

- proven governance instruments:
  do not consume financial slots;
- proven property/land legal agreements:
  do not consume financial slots;
- qualified financial statement:
  consumes financial slot;
- ambiguous/unresolved references:
  remain candidates;
- conflicting references:
  remain unresolved.

If genuine + unresolved financial candidates still exceed bound:
`FPI_FINANCIAL_DOCUMENT_CANDIDATE_BOUND_EXHAUSTED`

must still fire.

---

# 16. Offline TSM source closure

Using the sealed REV21/REV20 TSM regression evidence only:

run:

logical cell groups
→ purpose routing
→ financial slot accounting
→ FPI acquisition completeness
→ exact financial projection
→ selected financial owner
→ quality
→ source-use
→ stock assembly.

Require:

- current period remains:
  `2026-06-30`
  if current exact statement remains qualified;
- current qualified statement is not removed by routing;
- annual legal/governance exhibits are excluded only where exact routing proves it;
- no qualification override;
- no older-value substitution.

Expected goal:
TSM reaches a valid final source state under the unchanged finite bound.

If ambiguous references remain above bound:
stop honestly.

---

# 17. Negative structural tests

At minimum:

1. same row + same cell + same target + contiguous → group;
2. same row + different cell → no group;
3. different row + same cell identity impossible/malformed → fail;
4. same cell + different hrefs → separate groups;
5. same target anchors interrupted by different target → no cross-interruption group;
6. meaningful unlinked text between anchors → no group;
7. whitespace/layout wrappers only → allowed;
8. unknown DOM order → unresolved;
9. duplicate anchor span → fail;
10. overlapping byte spans → fail;
11. cross-accession → forbidden;
12. multiple groups same target with conflicting purpose → fail.

---

# 18. Negative semantic routing tests

At minimum:

- grouped `Articles of Incorporation ... amended ...` → governance non-financial;
- ambiguous `Articles` → unresolved;
- grouped `Land Lease with ... effective ...` → legal non-financial;
- `Lease Liabilities` → not legal-agreement route;
- `Right-of-Use Assets` → not legal-agreement route;
- `Lease Accounting Policy` → not legal-agreement route;
- `Financial Statements relating to Leases` → financial/unresolved;
- grouped `Consolidated Financial Statements ...` → financial;
- unknown label → unresolved.

No filename-only authority.

---

# 19. All22 offline readiness

After TSM repair:

run current source-owner regression fixtures for all22.

Require:

- all22 final source states valid;
- SNDK 52/53 unchanged;
- TSM current 2026-06-30 authority retained;
- WRD financial owner unchanged;
- SKHY bridge unchanged;
- completed-session prices unchanged;
- technical current-effective semantics unchanged;
- event/macro/FX/night contracts unchanged.

This is regression evidence only, not current live source.

---

# 20. Canonical code-owner registry

REV22 changes code.

Recompute canonical whole-source owner hashes under the new frozen implementation.

Prefer implementing logical reference grouping inside an already registered FPI/financial source owner module when architecturally natural.

If a new mandatory whole-source owner module is truly needed:
- update canonical registry centrally;
- update producer/seed/consumer/replay/test parity through the registry owner;
- preserve exact-set validation.

Require exact parity before network.

---

# 21. Whole offline implementation gate

Before destructive GC or network require:

- LogicalCellReferenceGroup schema PASS;
- exact cell anchor inventory PASS;
- structural grouping positives/negatives PASS;
- purpose routing positives/negatives PASS;
- financial 6-K positive control PASS;
- unchanged financial cap PASS;
- TSM old bound failure reproduced;
- repaired offline TSM source state valid or exact honest blocker;
- all22 offline readiness valid;
- canonical code-owner registry parity PASS;
- completed-session price regression PASS;
- Pass-A visibility regression PASS;
- all prior closed owner regressions PASS;
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

Only then storage GC may run.

---

# 22. Storage GC — mandatory before new full-fresh

REV21 itself is now sealed.

REV21 archive:

`thesis-monitor-20260929-r2b-r9-rev21-logical-exhibit-boundary-evidence-report.zip`

SHA:

`922e56836ade9ceb7f884d2baf0d48453f81089b227eb151418daa7a80d87492`

It already contains the minimum TSM boundary fixture needed for REV22.

Therefore do not retain the full REV20/REV21 expanded source generations merely for this repair once:

- REV20/REV21 immutable archives verify;
- REV22 local test fixtures are materialized/sealed;
- no other registered dependency requires full expanded trees.

---

# 23. Archive verification

Before each deletion require:

- ZIP exists;
- SHA sidecar exists;
- SHA matches;
- ZIP CRC PASS;
- internal manifest complete;
- no missing/hash/size/extra;
- no unique unarchived evidence;
- not active current worktree/generation.

Record exact archive identity.

---

# 24. Eligible storage cleanup

After Section 21 PASS and fixture sealing, clean safe archive-backed:

- REV20 expanded fresh generation/report;
- REV21 expanded evidence/report;
- older superseded expanded R9 generations/reports;
- old request/receipt/normalized/replay trees;
- duplicate diagnostics/validation exports.

Keep immutable ZIP/SHA.

Inspect completed old worktrees under the standing clean/no-untracked/ref-preserved rules.

Use `git worktree remove`.

Do not aggressive-prune shared `.git`.

---

# 25. Protected storage

Never auto-delete:

- current REV22 worktree;
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

# 26. GC receipts

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`

Record:

- before/after `df -h`;
- exact candidate path/size;
- archive SHA/integrity;
- deleted/skipped reasons;
- actual reclaimed bytes;
- worktree removals;
- final free bytes.

No silent deletion.

---

# 27. Disk thresholds

Current REV21 evidence report free bytes:

`15,321,522,176`

Remeasure.

Hard pre-collection minimum:

`12 GiB`

Preferred:

`14 GiB+`

Hard pre-model minimum:

`10 GiB`

If safe GC cannot reach 12 GiB:

`R2B_R9_REV22_STORAGE_GC_HEADROOM_GAP`

Do not delete protected/unverified evidence to meet a threshold.

---

# 28. New REV22 full-fresh generation

Only after:

- implementation gate PASS;
- archive-backed GC executed;
- free >= 12 GiB;

create a completely new generation.

Do not resume REV20/REV21.
Do not reuse prior mutable current source values.

Recompute:

- actual query time;
- exchange calendars;
- latest completed sessions;
- provider descriptors;
- financial candidate/document plans;
- event plans;
- Market/macro/FX/night;
- valuation;
- exact request budgets.

Alpha Vantage:
`0`

Massive/undeclared fallback:
`0`.

---

# 29. Fresh TSM acquisition

Run fresh official SEC owner.

Require:

- fresh candidate discovery;
- exact cell/reference inventory;
- structural logical-group decisions;
- purpose routing;
- unchanged finite financial bound;
- current/prior exact financial facts;
- source completeness.

If genuine/ambiguous financial candidates still exceed the unchanged bound:
fail closed.

Do not force TSM PASS.

---

# 30. Fresh all22 source acquisition

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
- issuer bridge if required.

No prior mutable current data.

---

# 31. Full source closure

Require:

- stocks:
  `22/22`
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
  qualified or accepted typed unavailable under current contract.

Create:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

All code metadata uses canonical registry.

---

# 32. Replay twice

Freeze new source corpus.

Disable network/provider access.

Replay entire graph twice.

Require exact semantic equality for:

- stocks 22;
- logical exhibit groups and routing;
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
- canonical code-owner registry identity.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and with full live coverage:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

---

# 33. Pass-A visibility replay

Before models require fresh cohort proof:

- technical-excluded family absent from A view;
- approved financial-quality/thesis/macro refs visible;
- A preflight PASS;
- no authority widening.

---

# 34. Pre-model disk guard

Immediately before model calls:

`free >= 10 GiB`

If below:

`R2B_R9_REV22_DISK_GUARD`

Preserve frozen source corpus.
Do not call models.

---

# 35. Fresh AI

Only after complete source qualification + replay + A visibility + disk guard:

- Market `2/2`
- Core `22/22`
- A `22/22`
- B `22/22`

No old outputs.
No target fitting.
No source recollection after model stage starts.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

---

# 36. Final Market messages

Preserve approved contract.

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
- USD/KRW same-date or latest-published official value with exact source date.

---

# 37. Final detailed stock messages

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

# 38. Exact sender-boundary capture

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

# 39. Human-review bundle

On full PASS create:

`r2b-r9-rev22-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- logical-cell-reference-group audit;
- TSM structural grouping/routing audit;
- TSM source-completeness trace;
- canonical code-owner registry parity;
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

# 40. Post-seal storage state

After REV22 ZIP + SHA are sealed and verified:

- do not delete active REV22 expanded data inside REV22;
- mark:
  `NEXT_FULL_FRESH_GC_ELIGIBLE_AFTER_REVIEW`;
- record its path/size.

Any later task that starts another full-fresh generation repeats archive-backed GC.

---

# 41. Production side effects

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

# 42. Success terminal

Use only:

`R2B_R9_REV22_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. LogicalCellReferenceGroup contract PASS;
2. same-row/same-cell/same-target/contiguous grouping PASS;
3. structural negative controls PASS;
4. governance exhibit routing PASS;
5. land/property lease legal routing PASS;
6. current 6-K financial 8-anchor positive control remains financial;
7. unchanged financial-document cap;
8. offline TSM source assembly valid;
9. offline all22 readiness valid;
10. canonical code-owner registry parity PASS;
11. storage archive verification PASS;
12. storage GC executed;
13. pre-collection free >= 12 GiB;
14. new generation uses no prior mutable current source;
15. fresh stocks `22/22`;
16. Market `2/2`;
17. events `22/22`;
18. quality/valuation `22/22`;
19. whole-source graph PASS;
20. replay twice PASS;
21. A visibility replay PASS;
22. complete adapter qualification;
23. pre-model free >= 10 GiB;
24. fresh Market/Core/A/B complete;
25. exact final payloads `24/24`;
26. message contract PASS;
27. Alpha/fallback `0`;
28. production side effects `0`;
29. human-review ZIP generated.

---

# 43. Honest stop terminals

- `R2B_R9_REV22_LOGICAL_CELL_REFERENCE_GROUP_GAP`
- `R2B_R9_REV22_FPI_NONFINANCIAL_ROUTING_GAP`
- `R2B_R9_REV22_FPI_FINANCIAL_DOCUMENT_CANDIDATE_BOUND_EXHAUSTED`
- `R2B_R9_REV22_FRESH_FINANCIAL_SOURCE_PARTIAL`
- `R2B_R9_REV22_STORAGE_GC_ARCHIVE_GAP`
- `R2B_R9_REV22_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV22_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV22_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV22_DISK_GUARD`
- exact Market/macro/FX/night blocker;
- exact model/render stage failure.

Do not:
- merge across rows/cells/targets;
- classify from filename alone;
- raise financial cap;
- suppress genuine unresolved references;
- weaken code-owner parity;
- reuse prior mutable current values;
- delete unverified unique evidence.

---

# 44. Required validation

## Structural grouping
- same row/cell/target/contiguous positive;
- different row negative;
- different cell negative;
- different target negative;
- interrupted target negative;
- meaningful inter-anchor plain text negative;
- whitespace/layout wrappers positive;
- unknown order negative;
- duplicate/overlap negative;
- conflicting same-target groups negative.

## Routing
- grouped Articles of Incorporation positive;
- grouped Land Lease positive;
- lease-accounting labels negative;
- consolidated financial statements positive financial;
- ambiguous labels unresolved.

## TSM
- REV20/21 old blocker reproduced;
- repaired offline TSM valid or honest bounded blocker;
- 2026-06-30 current financial authority preserved;
- no qualification override.

## Code registry
- exact registry parity;
- producer/seed/consumer/replay;
- missing/extra/tamper negatives.

## Storage
- REV20/21 archive SHA/CRC/manifest;
- fixture extraction;
- expanded deletion;
- protected paths;
- actual reclaimed bytes;
- free-space accounting.

## Full pipeline
- all22;
- Market2;
- financial/events;
- current-price/technical;
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

# 45. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV21 identity/SHA;
- repository identities;
- changed-file inventory;

## SEC logical reference repair
- LogicalCellReferenceGroup schema;
- exact cell inventories;
- grouping decisions;
- normalized logical descriptions;
- negative-control receipts;
- TSM annual routing before/after;
- 6-K 8-anchor financial positive control;
- financial-slot accounting;
- TSM source-completeness trace;
- REV21 fixture manifest.

## Code registry
- canonical registry;
- per-file hashes;
- aggregate registry SHA;
- producer/seed/consumer/replay parity.

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

# 46. Final principle

REV21 proved the source boundary precisely:

the SEC filing visually presents a single exhibit description using multiple distinct anchors that
share one row, one cell and one target document.

REV22 does not authorize general cross-anchor concatenation.

It owns only the exact structural case where the source DOM itself proves one contiguous same-cell,
same-target logical reference group.

That same rule must reconstruct both:
- non-financial legal/governance exhibit labels; and
- the multi-anchor current financial-statement label.

Purpose routing remains a separate fail-closed layer.

Once that structural ownership is proven, the unchanged finite financial-document bound decides TSM
source completeness.

Then archive-backed GC runs and a completely new full-fresh generation proceeds to the real
24-message human-review boundary.
