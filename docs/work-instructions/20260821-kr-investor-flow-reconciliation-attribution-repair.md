# thesis-monitor — KR Investor-Flow Reconciliation & Attribution Repair

## Metadata

- Workstream: `Bounded P1 analysis-integrity repair`
- Title: `KR Investor-Flow Reconciliation & Full-Participant Attribution`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `af89324ad865a7f1cf6fdc5599db335629649cca`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- User-visible scope: KR supply/positioning wording only, after deterministic repair passes
- DB assessment mutation: `0`
- Warning lifecycle mutation: `0`
- Investment-logic status mutation from supply alone: `0`

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260821-kr-investor-flow-reconciliation-attribution-repair.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify latest safe main/operating SHA.
3. Commit/push this instruction as a docs-only instruction commit.
4. Record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. Create the implementation branch from the latest safe main descendant containing the instruction commit.
6. No force push / history rewrite.
7. Do not silently edit the instruction after implementation begins.
8. If the parallel Phase 9.1E branch lands first, reconcile onto latest main explicitly before promotion.

Recommended branch:

`codex/kr-investor-flow-reconciliation-attribution-repair`

---

# 1. Problem statement

A KR production message can display numerically correct flows for:

- foreign
- institution
- retail

while the three displayed participants do **not** reconcile to the total investor-flow universe.

Example class observed on SK hynix:

```text
1-day:
foreign +6,365
institution +66,258
retail -720,118

displayed 3-participant net
= -647,495 shares
```

The missing offset is material.

The current signal can still render a phrase such as:

`외국인 이탈·기관/개인 흡수`

which may over-attribute the absorption to institution/retail even when omitted participant categories account for a material share.

This is an analysis-integrity issue.

---

# 2. Core repair principle

Do not repair attribution by inferring participant identity from residual arithmetic.

Never do:

```text
total residual
→ assume "기타법인"
```

unless the provider explicitly supplies the category and it is canonicalized from raw evidence.

The correct flow is:

```text
provider raw participant categories
        ↓
canonical participant taxonomy
        ↓
per-period reconciliation
        ↓
display-scope completeness
        ↓
attribution-safe signal
        ↓
user wording
```

---

# 3. Scope

Audit and repair KR investor-flow handling for the active KR monitored universe.

Known current KR monitored universe is approximately 7 tickers, but do not hard-code count/tickers.

Periods:

- 1 trading day
- 5 trading days
- 20 trading days

Evidence dimensions:

- foreign
- institution
- retail
- all additional provider-supplied participant categories
- aggregate/market-total field if provider supplies one
- foreign ownership position if available

---

# 4. Hard exclusions

Do NOT:

- invent missing participant categories
- infer "other corporations" from residual alone
- change historical raw provider evidence
- change thesis status based on supply flow
- open/close warnings from flow alone
- change valuation context from flow alone
- change price/RR logic
- change Public Action schema
- add paid provider
- manually send Telegram
- manually run production tasks
- mutate Pilot
- mutate assessment DB
- modify 9.0E cash-flow logic
- modify 9.1 working-capital logic
- modify night-futures telemetry

---

# 5. Provider/raw inventory first

Before coding user-facing changes, inspect actual KR supply raw payload/schema.

For each natural/source record identify every participant field supplied by provider.

Potential categories may include, depending on actual source:

- foreign
- institution
- retail
- other corporations
- other foreign
- financial-investment subclasses
- pension/public funds
- insurance
- investment trusts
- private equity
- banks
- other financials

Do not assume these exist.

Report only actual fields present.

---

# 6. Canonical participant taxonomy

Define a versioned contract, suggested:

`kr-investor-flow-participants-v1`

Each canonical participant must retain:

```text
participant_id
canonical_label
provider_field
provider_label
aggregation_role
display_role
source_ref
```

Distinguish:

- top-level participant
- institutional subclass
- supplemental participant
- ownership/position metric

Do not double-count an institutional total plus its subclasses.

---

# 7. Double-count prevention

If provider supplies both:

```text
institution_total
and
institution_subclasses
```

choose one reconciliation layer.

Do not sum both.

The canonical reconciliation contract must explicitly define:

`reconciliation_participants`

and separately:

`diagnostic_subcomponents`

if subclasses are retained.

---

# 8. Reconciliation contract

Implement a versioned reconciliation contract, suggested:

`kr-investor-flow-reconciliation-v1`

For each ticker/date/window:

```text
ticker
window
as_of_date

participant_flows:
  participant
  shares
  source_ref

displayed_participants
omitted_participants

displayed_net
omitted_net
all_participant_net

provider_total_if_available

reconciliation_status
reconciliation_difference

display_coverage_ratio
material_omitted_flow
attribution_safe

signal_basis_window
signal_participants
```

Actual naming follows repository conventions.

---

# 9. Reconciliation truth

If the provider gives a true aggregate total:

```text
sum(canonical reconciliation participants)
≈ provider aggregate
```

must pass deterministic tolerance appropriate to integer shares.

Prefer exact integer equality when source semantics imply exact shares.

If no aggregate total exists:

- do not fabricate one
- still reconcile the full set of provider-supplied mutually exclusive top-level participants
- classify aggregate completeness accordingly

---

# 10. Displayed-three-participant audit

For each 1D/5D/20D window calculate:

```text
displayed_3_net
full_canonical_net
omitted_participant_net
```

This is diagnostic.

Do not label the omitted balance by participant identity unless provider fields support it.

---

# 11. Material omitted-flow rule

Do not invent a universal arbitrary threshold without evidence.

Use an explicit deterministic materiality rule based on actual attribution risk.

Codex must inspect current score/signal architecture and propose the smallest safe rule.

Acceptable logic may consider:

- omitted flow relative to total absolute participant flow
- omitted flow relative to the attributed absorption amount
- whether omitted participants reverse the claimed absorber/donor identity
- whether displayed participants account for only a minority of offsetting flow

Do not create a 0–100 investor-flow quality score unless one already exists.

Document the selected rule and test boundary cases.

---

# 12. Attribution-safe signal

A signal may name absorbing participants only if the full canonical evidence supports that attribution.

Example:

```text
foreign net sell
institution + retail net buy
other participants immaterial
```

may allow:

`외국인 매도·기관/개인 흡수`

But if omitted participants are material:

use broader wording.

For example:

`20일 기준 외국인 순매도가 이어졌고, 기관·개인은 순매수였지만 기타 투자주체 흐름도 커 흡수 주체를 기관·개인으로만 단정하기 어렵습니다.`

Do not hard-code this sentence; implement structured attribution and render naturally.

---

# 13. Signal window must be explicit

Current `primary_signal` must identify the period that produced it.

Store:

```text
signal_basis_window = 1d / 5d / 20d / mixed
```

If a signal is based mainly on 20D, user-facing wording must say `20일 기준`.

Do not let a 20D interpretation appear immediately below contradictory 5D numbers without period context.

---

# 14. Mixed-window signal

If score/signal combines multiple windows:

- expose `mixed` internally
- user-facing wording must summarize the tension instead of pretending one period dominates

Example concept:

```text
5일 기관/개인 매도
vs
20일 기관/개인 순매수
```

should not render a timeless `기관/개인 흡수`.

---

# 15. Full-participant signal generation

Primary signal generation should use the complete canonical participant set where available.

Do not use only the three displayed participants if omitted categories materially alter attribution.

Possible safe signal dimensions:

- foreign direction
- institutional direction
- retail direction
- omitted/other-participant materiality
- multi-window consistency

No thesis-state mutation.

---

# 16. Display policy

Choose one of two safe user-facing policies:

A. display full participant categories when concise and stable

or

B. retain foreign/institution/retail as `주요 3주체` and add an attribution qualification when omitted participants are material

Prefer the lower-noise option supported by current renderer.

Do not create long investor-category dumps.

---

# 17. User-facing label if only three shown

If other provider-supplied categories are omitted from the visible table and materially exist, the header should make clear that the visible lines are not the full universe.

Examples:

- `주요 3주체`
- equivalent concise wording

Do not imply the three visible rows exhaust all investors.

---

# 18. Foreign ownership is position, not flow

Keep:

- foreign net flow
- foreign ownership shares/percentage

semantically separate.

Do not use ownership-position changes as missing flow reconciliation unless the provider explicitly supports such derivation and corporate actions are handled.

No reverse-engineering.

---

# 19. Corporate actions / denominator safety

If share counts changed due to:

- issuance
- split
- treasury actions
- other corporate action

do not infer participant flow from ownership-position delta.

Supply flow remains provider flow.

---

# 20. 1D / 5D / 20D rolling windows

Verify window construction:

- trading-day count
- as-of-date
- holiday handling
- no calendar-day assumption
- no duplicate date rows
- same participant taxonomy across windows

Report actual constituent count where useful.

---

# 21. Historical replay

Use immutable recent KR packet, including the 2026-08-21 natural KR run, as a primary replay.

Audit all active KR tickers.

For every ticker/window report:

```text
foreign
institution
retail
other canonical participants
displayed net
omitted net
reconciliation
signal before
signal after
```

Do not rewrite original archive.

---

# 22. SK hynix mandatory regression

Use SK hynix `000660` as a regression fixture based on the natural 2026-08-21 message.

Must verify:

- original foreign/institution/retail numbers remain unchanged if source facts were correct
- omitted participant flow is identified only from actual provider categories
- 1D/5D/20D reconciliation is complete
- `외국인 이탈·기관/개인 흡수` cannot survive unqualified if full-participant evidence does not support it
- signal period is explicit
- no investment-logic/valuation delta from this repair

No ticker-specific production code.

---

# 23. KR universe audit

Run active KR universe audit.

For each ticker:

- participant field coverage
- reconciliation status
- material omitted-flow status
- before/after primary signal
- before/after visible wording
- whether full participant display is necessary

Target:

unsupported absorber attribution = `0`.

---

# 24. Semantic validator

Add/extend validation so user-visible supply prose cannot claim:

- participant X absorbed participant Y
- participant X was the main buyer
- participant X offset selling

unless canonical full-participant attribution supports it.

The validator should understand period/window identity.

---

# 25. Numeric validator

All displayed participant flows must bind to canonical flow facts.

Targets:

```text
automatic binding > 0
manual = 0
rejected = 0
unresolved = 0
```

No residual-derived numeric category.

---

# 26. Runtime quality

Avoid turning repair into verbose disclaimers on every ticker.

Only qualify when omitted participants are materially relevant or signal-period ambiguity exists.

No repetitive portfolio boilerplate.

---

# 27. Score behavior

Audit whether `supply score = 50` or similar score depends on incomplete participant input.

If score already uses full provider flow:
document and preserve.

If score uses only 3 participants:
determine whether repair is required.

Do not change score merely to improve wording.

Any score-model change must be evidence-driven and regression-tested.

---

# 28. Primary signal behavior

The primary signal must expose internally:

```text
basis_window
participant_basis
attribution_confidence
omitted_participant_materiality
```

Use existing terminology where possible.

Do not expose internal enum names to user.

---

# 29. Fallback / AI parity

If supply interpretation appears in both AI and deterministic fallback paths:

they must consume the same canonical reconciliation result.

No separate AI residual inference.

Parity dimensions:

- participant directions
- period
- attribution-safe flag
- omitted-materiality flag
- signal wording meaning

---

# 30. Production safety

Repair must preserve:

- message count
- exactly-once
- receipts
- price/RR
- valuation
- 9.0E cash flow
- 9.1 working capital
- night futures
- KRX telemetry

---

# 31. Tests — participant mapping

Required:

- mutually exclusive top-level participants
- institution total + subclasses no double count
- missing optional participant
- other foreign distinct from foreign if provider semantics require
- unknown provider field stays unknown
- no residual-derived category

---

# 32. Tests — reconciliation

Required:

- exact reconciliation
- omitted participants zero
- omitted participants material
- omitted participants reverse absorber attribution
- no provider aggregate available
- provider aggregate conflict
- integer exactness

---

# 33. Tests — signal period

Required:

- 1D signal
- 5D signal
- 20D signal
- mixed-window signal
- 5D and 20D opposing directions
- no timeless absorber phrase when basis differs

---

# 34. Tests — wording

Required:

- attribution safe → concise absorber wording allowed
- attribution unsafe → qualified wording
- major-three-participant header when appropriate
- no unnecessary disclaimer when omitted flow immaterial
- Korean language naturalness
- no internal field leakage

---

# 35. Tests — SK hynix regression

Required fixture reproduces natural 2026-08-21 class.

Expected:

- numeric 3-participant facts unchanged
- full participant reconciliation explains residual from provider data if available
- unsupported `기관/개인 흡수` attribution removed/qualified
- period identified
- no status/valuation change

---

# 36. Full validation

Required:

- focused participant/reconciliation tests PASS
- KR universe replay PASS
- numeric binding PASS
- semantic validation PASS
- AI/fallback parity PASS
- runtime quality PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- final main SHA Actions PASS after promotion

---

# 37. Promotion gate

Promotion allowed when:

- P0 = 0
- material P1 = 0
- unsupported attribution = 0
- user-visible numbers remain canonical
- no residual-derived participant
- signal basis period explicit
- full regression PASS
- main ancestry clean

This is a user-visible wording/interpretation repair, so promotion should include exact before/after message previews.

---

# 38. Required reports

Create:

1. `docs/architecture/KR_INVESTOR_FLOW_RECONCILIATION.md`
2. `docs/reports/20260821-kr-investor-participant-inventory.md`
3. `docs/reports/20260821-kr-investor-flow-reconciliation-audit.md`
4. `docs/reports/20260821-kr-investor-flow-signal-period-audit.md`
5. `docs/reports/20260821-kr-investor-flow-before-after.md`
6. `docs/reports/20260821-kr-investor-flow-sk-hynix-regression.md`
7. `docs/reports/20260821-kr-investor-flow-validation.md`
8. `docs/reports/20260821-kr-investor-flow-readiness.md`

Recommended JSON:

`docs/reports/20260821-kr-investor-flow-reconciliation.json`

---

# 39. Complete bundle

Create:

`20260821-kr-investor-flow-reconciliation-repair-bundle.zip`

Include sanitized reports/JSON.

Report ZIP SHA-256.

---

# 40. Completion report

Include:

## Repository
- instruction commit
- implementation commit
- final
- previous/final main
- operating
- promotion method

## Provider taxonomy
- raw participant fields
- canonical participant set
- double-count rules

## KR universe
- ticker count
- 1D/5D/20D reconciliation
- omitted-material count
- unsupported attribution before/after

## SK hynix
- exact before/after
- residual source identity
- signal period
- wording result

## Validation
- numeric binding
- semantic
- AI/fallback parity
- full pytest/CI

## Safety
- manual Telegram/task/DB/Pilot = 0
- thesis/valuation mutations = 0

Final state:

```text
KR_INVESTOR_FLOW_RECONCILIATION_REPAIR = PASS/FAIL
OPEN_P0 = ...
OPEN_P1 = ...
```

---

# 41. Final philosophy

Correct numbers can still produce a misleading interpretation if the participant set is incomplete.

The system must distinguish:

```text
"These three participants moved this way"
```

from:

```text
"These three participants explain the whole market-side absorption"
```

The second claim requires full-participant attribution evidence.

Do not fabricate missing participant identity from arithmetic residuals.

Do not let a 20-day signal masquerade as a timeless current statement when 5-day behavior differs.

The repair succeeds when the user can trust both:

1. the displayed flows, and
2. the sentence explaining who actually absorbed whose flow.
