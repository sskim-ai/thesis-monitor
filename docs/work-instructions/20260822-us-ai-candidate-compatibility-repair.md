# thesis-monitor — US AI Candidate Compatibility Repair

## Metadata

- Workstream: `Bounded P1 repair`
- Title: `US AI Candidate Compatibility — Cash-Flow Period Labels + Current-Price RR Fact Ownership`
- Instruction version: `1.0`
- Date: `2026-08-22 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `f5a956930c1fbc4cbc6c6dc053a1cf2e428d4000`
- Triggering natural evidence:
  `2026-08-22 US natural run`
- Current Phase 9.0E natural state:
  `LIVE_PASS_SELECTIVE_SUBSET`
- Current Phase 9.1D Inventory proof:
  `LIVE_PASS`
- Current Phase 9.1D exact Trade AR proof:
  `NOT_OBSERVED`
- Working-capital user-visible mode:
  `OFF`
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`
- Runtime policy:
  `daily-review-v3.10`
- Goal:
  make the AI-assisted US candidate satisfy the already-correct numeric/semantic contracts without weakening validators or changing deterministic fallback facts.

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260822-us-ai-candidate-compatibility-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify latest safe main/operating
2. commit/push this instruction as a docs-only commit
3. record exact instruction commit SHA
4. create implementation branch from the latest safe main descendant containing the instruction commit
5. no force push / history rewrite
6. no silent instruction edits after implementation begins
7. if the parallel XKRX repair lands first, reconcile onto latest main explicitly before promotion

Recommended branch:

`codex/us-ai-candidate-compatibility-repair`

---

# 1. Problem statement

The 2026-08-22 US natural production path remained safe because deterministic fallback delivered the complete bundle exactly once.

However, the final AI candidate was rejected by hard validation.

Current evidence classifies the remaining hard errors as:

```text
18 × cash-flow period-label / fiscal-YTD-FY compatibility errors
3 × current-price RR Fact-ID ownership errors
   affected class: CORZ / HUT / WULF
```

These counts must be verified against immutable run artifacts before implementation.

The repair must make AI output conform to existing canonical facts.

It must NOT make the validator accept weaker claims.

---

# 2. Core repair principle

Correct direction:

```text
canonical fact
→ structured AI packet metadata
→ prompt/serializer ownership
→ AI wording
→ existing validator PASS
```

Forbidden direction:

```text
AI wording fails
→ loosen validator
```

The deterministic fallback is the safety reference.

---

# 3. Hard exclusions

Do NOT:

- change canonical FCF arithmetic
- change PPE-only FCF definition
- change Phase 9.0E selector
- change current-price RR arithmetic
- change support/resistance calculation
- change fallback facts to match bad AI wording
- weaken numeric validator
- weaken semantic validator
- bypass Fact-ID ownership
- annualize YTD FCF
- relabel YTD as standalone quarter
- relabel fiscal period as calendar period without proof
- alter Public Action/schema
- enable working-capital user-visible output
- change night-futures or KRX logic
- manually run production tasks
- manually send Telegram
- mutate DB/Pilot
- change Production Assist

---

# 4. Evidence-first root-cause trace

Before code changes, trace each final hard error from:

```text
canonical Fact / relation
→ production AI packet
→ prompt instructions
→ generated AI claim
→ numeric/semantic validator
→ error
```

For every error report:

- ticker
- section
- exact error string
- claim text
- expected Fact/metadata
- supplied AI packet metadata
- ownership slot
- root cause

Do not repair by regex alone unless the root cause is genuinely legacy prose formatting.

---

# 5. Cash-flow period identity contract

The AI must receive enough structured metadata to distinguish:

- fiscal year
- fiscal quarter
- YTD
- standalone quarter/QTD where canonical
- full-year/FY
- non-calendar fiscal year
- balance-date vs flow-period concepts

For selected FCF context, include at minimum:

```text
period_start if canonical
period_end
fiscal_year
fiscal_quarter if applicable
period_type
duration_basis
is_ytd
is_fy
financial_currency
fcf_scope = OCF - PPE CAPEX
fact_id
```

Use existing fields if already present.

Do not invent missing start dates.

---

# 6. User-facing fiscal-period renderer

Create/reuse one canonical formatter for AI-visible period labels.

Examples conceptually:

- `FY2026 Q3 YTD`
- `2026 회계연도 3분기 누계`
- `2026년 상반기 누계`
- `FY2026`

The exact wording must follow issuer fiscal context.

Do not transform a non-calendar fiscal period into a misleading calendar label.

---

# 7. Period-label allowed-claim contract

For each selected FCF Fact, derive machine-readable allowed labels.

Example concept:

```text
allowed_period_claims:
  - fiscal_year = 2026
  - period_type = ytd
  - fiscal_quarter = 3
  - period_end = ...
forbidden:
  - standalone_q3
  - calendar_2026_q3
  - annualized
```

Prefer structured validation over free-form heuristic matching.

---

# 8. AI prompt/packet rule

The AI prompt must explicitly state:

- use the supplied period label
- do not paraphrase YTD as standalone quarter
- do not infer calendar-quarter identity
- do not annualize
- do not shorten a fiscal-year label if it changes meaning
- exact FCF number and period belong to `business_earnings` / earnings-quality owner

Avoid adding verbose accounting instructions to user-facing prose.

---

# 9. Current-price RR ownership contract

Trace the three current-price RR Fact-ID ownership errors.

The AI packet and validator must agree on which canonical facts own:

- current price
- support zone
- resistance zone
- RR
- invalidation price where applicable
- confirmation-price state where applicable

Do not let one synthetic RR sentence own unrelated price facts implicitly.

---

# 10. Existing current-price context is authoritative

Reuse:

`current-price-context-v1`

and existing Phase 8.5.5.x ownership rules.

Do not create a second RR calculation path.

The AI should consume canonical current-price context, not raw OHLCV.

---

# 11. RR Fact references

For every AI RR claim, packet metadata should expose the exact references required by the validator.

Conceptual:

```text
current_price_fact_id
support_context_id
resistance_context_id
rr_relation_id
invalidation_fact_id if used
confirmation_state_id if used
```

Actual repository naming prevails.

Do not attach a Fact ID merely because its numeric value happens to match.

---

# 12. CORZ / HUT / WULF mandatory replay

Use the exact immutable 2026-08-22 US natural packet.

For CORZ, HUT, WULF:

- reproduce each RR ownership failure
- identify missing/wrong owner
- correct packet/prompt/claim binding
- prove no RR arithmetic changed
- prove fallback output remains semantically unchanged

No ticker-specific production code.

---

# 13. Run-32 immutable replay target

Primary acceptance target:

```text
AI hard validation errors:
before = 21
after  = 0
```

If the verified original count differs from 21:
report the exact verified count and explain discrepancy.

Required:
- validated AI outbox candidate produced
- numeric PASS
- semantic PASS
- final-language PASS
- runtime-quality PASS, unless a separate unrelated P2 remains
- no archive rewrite

Write repaired comparison artifacts separately.

---

# 14. Validator preservation

Snapshot the relevant validator behavior before/after.

Required:

- known-bad fiscal/QTD/YTD fixtures still fail
- wrong fiscal-calendar conversion still fails
- wrong Fact ownership still fails
- missing RR Fact IDs still fail
- unsupported arithmetic still fails

The repair is not complete if errors disappear because the validator stopped checking them.

---

# 15. Deterministic fallback regression

Fallback must remain correct and independent.

Verify:

- same canonical FCF facts
- same current-price/RR relations
- same exact numbers
- same periods
- no new duplication
- exactly-once unaffected

No fallback wording rewrite unless strictly required by a shared safe formatter, and any diff must be audited.

---

# 16. AI/fallback factual parity

For all selected FCF and RR claims compare:

```text
ticker
fact/relation IDs
number
currency
period
scope
current price
support/resistance relation
RR
```

Factual mismatch target:

`0`

Prose may differ.

---

# 17. Phase 9.0E regression

Must preserve the already-observed natural success:

- selective FCF context
- current-formal eligibility
- PPE-only scope
- baseline consistency
- user-visible fact correctness
- kill switch
- deterministic fallback

Do not invalidate the Phase 9.0E natural LIVE PASS.

---

# 18. Phase 9.1D / 9.1E isolation

Do not change:

- working-capital canary selector
- Inventory natural proof
- Trade AR proof state
- working-capital user-visible OFF mode
- 9.1E natural-proof gates

The AI compatibility repair is not an Inventory enablement task.

---

# 19. Runtime quality

After numeric/semantic compatibility is repaired, run existing quality gates.

Do not solve factual compatibility by generating longer repetitive prose.

Report:
- substantive repetition
- numeric skeleton repetition
- typed-prose skeleton
- generic numeric summary
- average message length change

Any pure wording P2 should remain P2.

---

# 20. Natural production policy

Do not manually invoke a natural task to prove the repair.

Implementation can be promoted after immutable replay + full regression PASS.

The next natural US run becomes live proof of restored AI-assisted compatibility.

Do not require fallback to stop existing; fallback remains safety path.

---

# 21. Test matrix — FCF periods

Required:

- calendar H1 YTD
- fiscal non-calendar YTD
- fiscal Q3 YTD
- full FY
- standalone QTD if canonical
- YTD not QTD
- FY not YTD
- period-end only when start unknown
- no annualization
- exact period label rendering

---

# 22. Test matrix — RR ownership

Required:

- current price owner
- support owner
- resistance owner
- RR relation owner
- invalidation owner
- confirmation state
- missing owner → fail
- wrong owner → fail
- duplicate owner → quality/semantic handling

Include CORZ/HUT/WULF regression fixtures.

---

# 23. Regression suite

Preserve:

- run-32 fallback delivery
- run-31 KR
- run-30
- run-29/28/27
- Phase 8.5.5/.1/.2
- Phase 9.0B/C/D/D.1/E
- Phase 9.1A/B/C/D/E-preintegration
- investor-flow repair
- night-futures telemetry
- KRX telemetry
- exactly-once / receipts

---

# 24. Full validation

Required:

- focused FCF-period tests PASS
- focused RR ownership tests PASS
- run-32 immutable replay PASS
- AI hard errors 0
- numeric PASS
- semantic PASS
- final-language PASS
- runtime quality report
- AI/fallback factual parity PASS
- validator negative controls PASS
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

# 25. Promotion gate

Promotion allowed when:

- P0 = 0
- material P1 = 0
- run-32 hard errors = 0
- validator negative controls PASS
- fallback regression PASS
- production/user-visible facts unchanged
- CI PASS
- main ancestry clean

Protect scheduled US/KR execution windows.

No manual production run.

---

# 26. Required reports

Create:

1. `docs/architecture/AI_FINANCIAL_PERIOD_AND_PRICE_OWNERSHIP.md`
2. `docs/reports/20260822-us-ai-hard-error-root-cause.md`
3. `docs/reports/20260822-us-ai-fcf-period-contract.md`
4. `docs/reports/20260822-us-ai-rr-ownership-audit.md`
5. `docs/reports/20260822-us-run32-ai-replay.md`
6. `docs/reports/20260822-us-ai-fallback-parity.md`
7. `docs/reports/20260822-us-ai-validator-negative-controls.md`
8. `docs/reports/20260822-us-ai-compatibility-validation.md`
9. `docs/reports/20260822-us-ai-compatibility-readiness.md`

Recommended JSON:

`docs/reports/20260822-us-ai-compatibility-readiness.json`

---

# 27. Complete bundle

Create:

`20260822-us-ai-candidate-compatibility-repair-bundle.zip`

Report ZIP SHA-256.

---

# 28. Completion report

Include:

## Repository
- instruction commit
- implementation commit
- final
- previous/final main
- operating

## Root cause
- verified original hard-error count
- FCF-period errors
- RR-ownership errors
- affected tickers/sections

## Repair
- packet changes
- prompt/serializer changes
- formatter changes
- validator changes: ideally none or strictly stronger/neutral only

## Replay
- before errors
- after errors
- AI outbox result

## Validation
- negative controls
- fallback parity
- full pytest/CI

## Safety
- manual Telegram/task/DB/Pilot = 0
- Production Assist OFF
- working-capital user-visible mode unchanged

Final:

```text
US_AI_CANDIDATE_COMPATIBILITY_REPAIR = PASS/FAIL
OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
AI_NATURAL_PROOF = PENDING
```

---

# 29. Final philosophy

The fallback already proved the facts were deliverable safely.

The AI repair should not alter those facts.

It should make the AI say the same facts with the correct fiscal-period identity and correct Fact ownership.

Success is not:

> the validator stopped complaining.

Success is:

> the AI packet now contains enough exact structure that the AI naturally produces claims the unchanged safety validator can approve.
