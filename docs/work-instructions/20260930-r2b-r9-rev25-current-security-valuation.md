# Thesis Monitor — R2B-R9-REV25
## Current-Security Valuation Owner Closure
### PER/PBR Qualified Where Exact Security/Class/Split/Denominator Authority Exists
### fPER Remains Fail-Closed Without Exact Estimate-Horizon Owner
### Archive-Backed Storage GC → New Full-Fresh → Replay Twice → Fresh Market/Core/A/B → Exact 24-Message Proof

**REV25 supersedes every prior unexecuted post-REV24 instruction. Execute only REV25.**

REV24 is the first accepted end-to-end human-review proof:

- Market 2/2 accepted;
- Core 22/22 accepted;
- Pass A 22/22 accepted;
- Pass B 22/22 accepted;
- exact sender-boundary messages 24/24;
- Telegram sends 0;
- provider recollection 0 during authorized timeout continuation;
- one user-authorized retry only for the no-output A transport timeout;
- no fallback, judge, semantic/schema retry or target fitting.

The independent source-only judgment was sealed before Monitoring AI reveal and compared afterward.

Do **not** retune Core/A/B directions merely to match the independent human labels.

The comparison identified one objective product/source-coverage gap:

> **Valuation is unavailable in all 22 stock messages.**

Every final stock message shows:

- PER: `판단 자료 부족`
- PBR: `판단 자료 부족`
- fPER: `판단 자료 부족`

The fresh source corpus already contains candidate EPS/equity/security metrics for many securities, but
`current-fresh-valuation-view-v1` currently denies use because exact security-owned denominators and
security/split basis are not closed.

Observed generic reasons include:

- `CURRENT_PROJECTION_OMITS_SECURITY_OWNED_DENOMINATORS`
- `ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY` for SKHY
- `NO_CONFIGURED_AUTHORIZED_EXACT_ESTIMATE_HORIZON_OWNER` for forward PE
- unresolved `security_basis`
- unresolved `split_basis`.

REV25 must qualify **current PER/PBR only where exact current-security ownership is provable**.

It must not fabricate valuation coverage.

fPER remains unavailable unless an existing exact estimate-horizon source can be independently qualified.

---

# 0. Newest accepted SoT

Use REV24 authorized retry continuation and 24-message human-review archives as the newest execution SoT.

Continuation ZIP SHA-256:

`4983ac784271eff518e19e3ead944194b48090b2e63f5352c7adfc0f125a51c8`

Human-review ZIP SHA-256:

`2c0e5843e1e1eb03b4a51b8ea9a39cf602242930c922de77efef66859c0711d1`

Source/decision generation:

`rev24-live-20260929T174642Z`

Continuation:

`rev24-retry1-20260929T224107Z`

Implementation:

`78f8e14a8dd891658c95e3125beb4dbdd833fdaa`

Source manifest:

`7c666dbdbe1fad3fe0e2d57bb31d39aca43e66b8c66d90a39751259e93e6d4ed`

Input manifest:

`8ec32c1ec4b767e35dfa013d295dd61a3c33ffeab45ddc444d8893a3cc485936`

Accepted:

- Market 2/2
- Core 22/22
- A 22/22
- B 22/22
- exact messages 24/24

Logical model calls:

`26`

Physical model calls:

`27`

Retry calls:

`1`

Production side effects:

`0`

Telegram:

`0`

Do not reinterpret the authorized REV24 retry as automatic retry authorization for a new REV25 model run.
REV25 uses the currently frozen/approved transport policy; any additional retry beyond that policy requires
separate authorization.

---

# 1. Blind-comparison preservation

Preserve as immutable audit inputs:

- source-only judgment freeze SHA:
  `55e46586c529685cb6c5d71296e3e3bd6db3b0829a69e75c5b7e59613337fed7`
- post-reveal comparison report.

No REV25 model/policy change may be justified only by disagreement with the human judgment.

Specifically preserve:

- field-isolation semantics demonstrated by 000660/SKHY;
- current risk-materiality semantics for HUT/RXRX/WULF/086280/WRD;
- strict breadth requirements in Market unless separately changed by explicit product policy.

REV25 is valuation ownership work, not decision calibration.

---

# 2. Exact current valuation gap

For direct-security subjects, current valuation source projection commonly reports:

PER:
`CURRENT_PROJECTION_OMITS_SECURITY_OWNED_DENOMINATORS`

PBR:
`CURRENT_PROJECTION_OMITS_SECURITY_OWNED_DENOMINATORS`

Forward:
`NO_CONFIGURED_AUTHORIZED_EXACT_ESTIMATE_HORIZON_OWNER`

Raw structured source projections may already contain candidate occurrences such as:

- diluted EPS;
- basic EPS;
- owners-parent/common equity;
- shares/share-count related facts where available.

But many are currently marked:

- `security_basis = UNRESOLVED`
- `split_basis = UNRESOLVED`.

This is correct fail-closed behavior until REV25 proves exact ownership.

---

# 3. Separate valuation metric owners

Do not use one generic "valuation available" flag.

Each metric is independently owned.

Required states per metric:

- `QUALIFIED`
- `NOT_MEANINGFUL`
- `UNAVAILABLE_SECURITY_BASIS`
- `UNAVAILABLE_DENOMINATOR`
- `UNAVAILABLE_ESTIMATE_HORIZON`
- `UNAVAILABLE_SOURCE_QUALITY`
- `UNAVAILABLE_OTHER_TYPED_REASON`.

One unavailable metric must not suppress another qualified metric.

---

# 4. Current PER contract

A current PER may be displayed only through one of two explicitly qualified paths.

## 4.1 Provider-native current multiple

Allowed only if the already-configured native metric route proves:

- exact monitored security identity;
- exact class/ADR identity;
- current valuation observation/as-of ownership;
- currency/basis;
- documented current-multiple semantic;
- split/corporate-action basis compatible with the quoted current security price;
- finite current-generation receipt;
- no cross-security transfer.

The provider-native metric is display/valuation context.

It must not become Overall business-direction evidence.

Do not use a native metric whose definition/security basis cannot be proven.

## 4.2 Source-derived current PER

Allowed only when:

- completed-session current security price is qualified;
- denominator is an exact security-owned EPS basis;
- denominator period policy is explicit:
  - TTM; or
  - latest FY, only if the product explicitly labels it as FY-based;
- share/security class matches monitored security;
- split basis matches current price;
- currency/unit compatible;
- source quality permits valuation use.

Do not annualize a single quarter merely to manufacture PER.

Do not sum incompatible quarterly/YTD facts.

Do not use issuer-wide EPS for a security class when class ownership is unresolved.

---

# 5. PER NOT_MEANINGFUL

If exact qualified denominator is <= 0 under the chosen PER basis:

render:

`PER: N/M`

or current accepted localized equivalent.

Do not show a negative PER as normal valuation.

Receipt must retain the exact denominator and basis.

---

# 6. Current PBR contract

PBR may be displayed only through:

## 6.1 Qualified provider-native PBR

Same exact security/class/currentness requirements as Section 4.1.

or

## 6.2 Source-derived book-value-per-share path

Require:

- exact common/owners-parent equity;
- exact eligible share-count denominator at compatible period;
- monitored security/class ownership;
- ADR ratio where relevant;
- split/corporate-action basis;
- currency compatibility;
- no preferred/non-common equity contamination unless explicitly accounted for;
- exact current price owner.

Do not use issuer total equity / ambiguous share count.

Do not derive PBR from diluted weighted-average shares when point-in-time common shares are required unless
an existing documented method explicitly authorizes it.

---

# 7. ADR / cross-security hard boundary

Preserve:

`SECURITY_VALUATION_BRIDGE_ELIGIBLE = false`

for issuer-business bridges unless a separate exact security conversion contract is proven.

For SKHY and TSM ADRs:

do not transfer home-market/security-class PER/PBR automatically.

Require exact:

- ADR identity;
- ADR-to-underlying ratio;
- currency;
- monitored ADR price basis;
- denominator conversion semantics.

If unresolved:

PER/PBR remain unavailable for that ADR.

This is not a task failure.

---

# 8. Split and corporate-action basis owner

Create/formalize a typed receipt, repository naming permitting:

`SecurityValuationBasisReceipt`

Required:

- monitored security;
- provider security ID;
- security class;
- listing/exchange;
- currency;
- price adjustment basis;
- corporate-action/split basis;
- denominator adjustment basis;
- as-of;
- provenance refs;
- basis SHA.

A valuation metric is eligible only when price and denominator basis are compatible.

Do not infer compatibility from numerically plausible values.

---

# 9. EPS occurrence selection

For structured SEC/OpenDART inputs:

enumerate all candidate EPS occurrences before selection.

Receipt must record:

- semantic/concept;
- source filing/accession;
- period start/end;
- period type;
- statement basis;
- currency/unit;
- security/class dimensions;
- split basis;
- current/prior/restated state;
- selection/exclusion reason.

Reject:

- duplicate historical restatements when a newer exact row supersedes them;
- incompatible YTD vs quarter mixing;
- unresolved class dimensions;
- stale denominator when a newer authoritative denominator exists but is unresolved.

No value-based selection.

---

# 10. Equity/share occurrence selection

Analogous typed candidate inventory for:

- owners-parent/common equity;
- common stockholders equity;
- shares outstanding;
- class-specific shares;
- ADR conversion facts where available.

Every selected denominator needs exact source-row ownership.

No implied denominator from market cap.

No reverse-engineering from an existing multiple.

---

# 11. Forward PER remains fail-closed

REV24 shows:

`NO_CONFIGURED_AUTHORIZED_EXACT_ESTIMATE_HORIZON_OWNER`

REV25 does not authorize scraping or inventing analyst estimates.

fPER may qualify only if an already-configured source can prove:

- exact security;
- estimate provider;
- EPS estimate horizon;
- consensus timestamp/as-of;
- fiscal-period mapping;
- currency/share basis;
- split basis;
- current price compatibility.

If no such owner exists:

`fPER: 판단 자료 부족`

is the correct output.

Current PER/PBR progress must not be blocked by fPER unavailability.

---

# 12. Valuation is not Overall direction

Preserve the existing principle:

Valuation may affect:

- New Buyer entry attractiveness;
- Holder trim/add context;
- valuation section;
- confidence/caution.

It cannot independently create Overall BUY/SELL business direction.

No REV24 Core/A/B direction is changed merely because valuation becomes available.

---

# 13. Offline REV24 valuation fixture

Before deleting REV24 expanded source data, seal a minimal regression fixture.

At minimum include representative cases:

- US direct common security with EPS candidates, e.g. GOOGL/MU;
- US loss/security with N/M candidate, e.g. CORZ/RXRX/HUT if source basis qualifies;
- KR direct common security with OpenDART EPS/equity candidates, e.g. 005930/003690;
- ADR/cross-security negative control, TSM or SKHY;
- no-estimate fPER control.

Include:

- current price receipt;
- raw denominator candidate inventory;
- security identity/basis receipts;
- current valuation-view denial receipt;
- fixture manifest + SHA.

Do not retain the whole REV24 expanded generation solely for these tests.

---

# 14. Offline success is metric-specific, not 22/22-value-forcing

REV25 must not target a fixed count of available PER/PBR.

Success means:

- every metric has an exact typed state;
- every displayed number has exact security/basis ownership;
- any source-capable direct security that can be proven is no longer falsely unavailable;
- unresolved ADR/security/split cases remain honestly unavailable;
- negative earnings become N/M only when exact denominator is qualified.

Report:

- PER qualified count;
- PER N/M count;
- PER unavailable count by reason;
- PBR qualified count;
- PBR unavailable count by reason;
- fPER qualified/unavailable count.

No target-fitted minimum coverage.

---

# 15. Evidence-maturity read-only audit

REV24 final messages showed:

`증거 성숙도: 판단 자료 부족`

for 22/22.

In REV25 perform a **read-only audit only**:

determine whether this is:

- the truthful result of single-period/non-recurring evidence;
- or a renderer/mapping collapse.

Do not change evidence-maturity semantics unless a concrete mapping defect is proven.

If all22 remain legitimately low-maturity, preserve it.

This audit is nonblocking for the valuation task.

---

# 16. Market judgment blind-difference audit only

Blind human Market judgments were more permissive than Monitoring AI because the human used major-index/segment moves
without true breadth.

REV25 must not loosen Market breadth/directional policy merely to match the human.

Record the difference as calibration evidence only.

No Market policy change is authorized here.

---

# 17. Canonical code-owner registry

REV25 changes valuation-source code.

Recompute exact whole-source code-owner registry identity.

If a new mandatory valuation owner module is introduced:
update the canonical registry centrally.

Require exact:

producer = seed = consumer = replay1 = replay2.

No manually duplicated inventory.

---

# 18. Whole offline implementation gate

Before destructive GC or network require:

- current-security valuation basis owner PASS;
- PER source/provider-native paths PASS;
- PBR source/provider-native paths PASS;
- N/M negative-earnings path PASS;
- ADR/cross-security negative controls PASS;
- split/corporate-action mismatch negatives PASS;
- fPER exact-horizon fail-closed PASS;
- valuation does not alter Overall direction contract;
- metric-independent availability PASS;
- REV24 24-message decision regression unchanged except valuation/new-buyer fields explicitly authorized by qualified valuation;
- evidence-maturity read-only audit complete;
- canonical code-owner registry parity PASS;
- all prior source-owner regressions PASS;
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

# 19. Archive-backed storage GC

Current free at REV24 continuation closeout:

`12,733,763,584 bytes`

This is below the standing `12 GiB` binary precollection threshold.

Therefore REV25 must GC before any new full-fresh acquisition.

Verify immutable archives first:

- original REV24 source/result ZIP + SHA;
- authorized retry continuation ZIP + SHA;
- 24-message human-review ZIP + SHA;
- blind source-only freeze + comparison fixtures.

Require SHA/CRC/manifest verification.

Then, after Section 13 minimal valuation fixture is sealed, delete safe archive-backed expanded:

- REV24 live provider/source/replay data;
- retry continuation expanded attempt directories;
- obsolete unpacked report data;
- older superseded expanded generations still present;
- clean old worktrees under the standing rules.

Preserve immutable archives and registered fixtures.

---

# 20. Storage protections and receipts

Never auto-delete:

- current REV25 worktree;
- operating/main;
- shared `.git`;
- production DB/WAL;
- credentials/.env;
- scheduler state;
- immutable ZIP/SHA archives;
- source-only judgment freeze;
- blind comparison report;
- registered minimal fixtures;
- active new generation.

Use `git worktree remove` for eligible worktrees.

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`.

Hard precollection:
`>= 12 GiB`

Preferred:
`>= 14 GiB`

Hard premodel:
`>= 10 GiB`.

---

# 21. Explicit external transmission approval

Per the user's standing request, REV25 explicitly authorizes:

- read-only requests to the existing declared provider/API inventory required by the sealed fresh plan;
- source/model payload transmission to the existing official GPT-5.6 Sol / xhigh Thesis Monitor runner after all qualification gates;
- secret-scanned result ZIP/SHA and human-review ZIP/SHA upload to the existing iCloud Drive / Thesis Monitor folder.

Still prohibited:

- Telegram/recipient message delivery during proof;
- production DB/warning writes;
- scheduler mutation;
- broker;
- deploy;
- main merge;
- remote push;
- restart.

Telegram remains `0`.

The one-off REV24 timeout retry authorization is historical and is not automatically expanded beyond the current REV25 frozen transport policy.

---

# 22. New REV25 full-fresh generation

Only after:

- offline gate PASS;
- GC PASS;
- free >= 12 GiB;

start a completely new generation.

Do not resume REV24.
Do not reuse REV24 mutable current source values.

Recompute:

- query time;
- US/KR completed sessions;
- provider descriptors;
- valuation-source candidate plans;
- financial/event/Market/macro/night plans;
- exact budgets.

Alpha Vantage:
`0`

No undeclared fallback.

---

# 23. Fresh valuation acquisition and ownership

For every stock:

- current price owner;
- security identity;
- valuation basis;
- provider-native metric candidate if configured;
- source-derived denominator candidates;
- metric-specific selection;
- typed unavailable/N-M state.

No cross-security metric reuse.

No stale valuation value.

No hidden fallback.

---

# 24. Fresh source closure

Require normal source completion:

- stocks 22/22 source states;
- Market 2/2;
- financial/events;
- current-price/technical;
- quality;
- valuation metric states for 22/22;
- macro/FX/night typed states.

"Valuation 22/22" means every security has typed metric states, not that every metric must be numeric.

Create whole-source packets and authority graph.

---

# 25. Replay twice

Freeze source corpus.

Disable network.

Replay twice with exact semantic equality for:

- all stock source packets;
- valuation basis receipts;
- denominator selections;
- metric states;
- Market/macro/FX/night;
- authority graph;
- code-owner registry.

Then issue normal source-adapter qualification flags only if all gates PASS.

---

# 26. Fresh model proof

After replay, A visibility and premodel disk guard:

run fresh Market/Core/A/B under the existing approved model destination.

Do not retune prompts based on the blind comparison.

Valuation facts are exposed only to stages already authorized for valuation/entry context.

No valuation-only Overall direction.

---

# 27. Final message contract

Preserve accepted detailed stock layout.

Valuation section:

- qualified PER: exact number + basis/as-of where current renderer supports it;
- qualified PBR: exact number + basis/as-of;
- non-meaningful PER: `N/M`;
- unavailable metric: `판단 자료 부족`;
- fPER unavailable independently if no estimate owner.

Do not copy a valuation number across securities/classes.

The user-facing section should no longer be uniformly unavailable when exact metric ownership exists.

---

# 28. Exact 24-message proof

Capture:

- MARKET_US
- MARKET_KR
- US14
- KR8

Total 24/24, delivery disabled.

Compare with REV24 only for:

- valuation fields;
- entry/holder context legitimately affected by newly qualified valuation;
- accidental direction drift.

Any unrelated Core/A/B direction drift requires explanation and may block acceptance.

---

# 29. Success terminal

Use only:

`R2B_R9_REV25_FULL_FRESH_VALUATION_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. metric-specific valuation ownership PASS;
2. no forced coverage target;
3. exact PER/PBR basis where numeric;
4. N/M semantics PASS;
5. ADR/cross-security fail-closed PASS;
6. fPER exact-horizon fail-closed PASS;
7. valuation cannot independently drive Overall direction;
8. evidence-maturity audit complete;
9. canonical code registry parity;
10. archive-backed GC executed;
11. precollection >=12 GiB;
12. fresh source no prior mutable reuse;
13. source 22/22 + Market2;
14. replay twice;
15. premodel >=10 GiB;
16. fresh Market/Core/A/B complete;
17. exact24 complete;
18. Telegram 0;
19. production side effects 0;
20. human-review archive generated/uploaded to approved iCloud destination.

---

# 30. Honest stop terminals

- `R2B_R9_REV25_SECURITY_VALUATION_BASIS_GAP`
- `R2B_R9_REV25_PER_DENOMINATOR_GAP`
- `R2B_R9_REV25_PBR_DENOMINATOR_GAP`
- `R2B_R9_REV25_VALUATION_SOURCE_PARTIAL`
- `R2B_R9_REV25_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV25_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV25_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV25_DISK_GUARD`
- exact model/render failure.

Do not:
- derive current PER from a single quarter;
- infer split/class compatibility from plausible values;
- transfer home-share valuation to ADR without exact conversion;
- use market cap to reverse-engineer a denominator;
- invent forward estimates;
- retune directional outputs to agree with the human blind judgment.

---

# 31. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum include:

## Blind-comparison preservation
- independent source-only judgment identity;
- human-vs-AI comparison identity;
- no-retuning receipt.

## Valuation
- security valuation basis schema/receipts;
- provider-native metric qualification matrix;
- EPS candidate/selection matrix;
- equity/share candidate/selection matrix;
- PER/PBR/fPER state matrix for all22;
- ADR negative-control receipts;
- N/M receipts;
- valuation-to-stage visibility audit.

## Evidence maturity
- read-only all22 mapping audit.

## Storage
- GC plan/result/protected/fixtures;
- before/after disk.

## Fresh source
- all22 matrix;
- Market2;
- valuation state matrix;
- replay twice;
- adapter qualification.

## Models/messages
- fresh Market/Core/A/B ledger;
- exact24;
- comparison against REV24 for unrelated direction drift;
- human-review ZIP/SHA.

## Safety
- provider/model counters;
- Alpha 0;
- fallback 0;
- Telegram 0;
- production side effects 0;
- secret scan;
- bundle manifest.

---

# 32. Final principle

REV24 proves the end-to-end source/model/message architecture is now operational.

Do not use the human-vs-AI comparison to tune the model toward one analyst's labels.

The next concrete usability gap is valuation ownership:

the system already sees candidate EPS/equity data but cannot yet prove that those denominators belong to the
exact monitored security, class, split basis and current-price basis.

REV25 should close that ownership where the source permits it and remain honestly unavailable elsewhere.

