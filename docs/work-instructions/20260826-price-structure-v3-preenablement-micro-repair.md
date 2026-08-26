# thesis-monitor — Price Structure v3 Pre-Enablement Micro Repair
## Consensus Membership Semantics + Real Previous-Stable Regression + Knowledge 1200/600/300 Sync + User-Visible Price Rounding
## No architecture redesign; no live enablement in this task

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_PREENABLEMENT_MICRO_REPAIR`
- Date: `2026-08-26 KST`
- Task type: `BOUNDED_PREENABLEMENT_REPAIR`
- Repository: `sskim-ai/thesis-monitor`
- Source policy: `FREE_ONLY`
- Current v3 state: `INTEGRATED_READY_NOT_ARMED`
- User-visible production mutation: `0`
- Telegram / scheduled-task / DB / assessment mutation: `0`
- Production Assist: preserve `OFF`
- Trade AR: preserve `OFF`
- Open Research production integration: preserve `0`

### Required base

Latest reported safe main / operating:

`f53434e38e374a41436f61fc06864357b783a516`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous implementation

```text
Instruction:
b0f81c8e16f588e314f93eb6097370e85f285241

Implementation:
631e82f202b6f081866ef83c8b67b2138a8b51d8

Final/main/operating:
f53434e38e374a41436f61fc06864357b783a516

PRICE_STRUCTURE_V3_FAMILY_CONSENSUS =
INTEGRATED_READY_NOT_ARMED

CODE_CORRECTNESS = PASS
PRODUCTION_ENABLEMENT_READY = YES
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Do not reinterpret this task as a new Fibonacci or Elliott redesign.

---

# 0. Why this micro repair exists

The family-consensus architecture is directionally correct.

However, the readiness evidence contains:

```text
previous_stable_regression = 0
previous_stable_regression_tickers = []
```

Therefore the declared `PREVIOUS_STABLE_REGRESSION=0` gate was not actually exercised against
the known previous stable cohort.

The current consensus universe also appears to include `alternative_hypothesis_id` from a
`SELECTED` run as if it were an equal active competing hypothesis.

That can over-expand the consensus universe and suppress otherwise stable Fib families.

Example control:

```text
012450
previous trial = stable
family-consensus replay = full MATERIAL_VARIATION
family-level FAIL
eligible Fib = 0
SR-only fallback
```

despite repeated primary selection remaining stable.

This task fixes that semantics and proves the real regression gate before enablement.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-price-structure-v3-preenablement-micro-repair.md`

Then:

1. fetch latest main
2. verify clean worktree
3. commit this exact instruction docs-only
4. create branch:

`codex/price-structure-v3-preenablement-micro-repair`

5. use latest safe main as base
6. no force push / history rewrite
7. no live enablement in this task

---

# 2. Hard prohibitions

Do NOT:

- change Fibonacci formulas
- change Elliott hard rules
- change wave-degree model
- widen confluence tolerance
- lower temporal safety
- force one hypothesis
- hard-code stable tickers
- hard-code SK hynix endpoints
- suppress TSLA true conflict
- let AI calculate technical numerics
- change business investment logic from technicals
- enable v3 in Telegram
- change scheduled task timing
- manually execute production tasks
- mutate DB / official assessment
- reduce OHLCV 1200/600/300 defaults

---

# 3. Consensus membership semantics — canonical repair

Build the family consensus universe from **materially observed competitors**, not every diagnostic
alternative.

The consensus universe MUST include:

```text
A. every hypothesis ID actually returned as SELECTED
   in any repeated independent run

B. every competing_hypothesis_id explicitly returned by
   an AMBIGUOUS run
```

A `SELECTED` run's `alternative_hypothesis_id` is diagnostic by default.

It enters the consensus universe ONLY when at least one is true:

```text
1. it is actually SELECTED in another independent run

2. it appears in another run's AMBIGUOUS competing_hypothesis_ids
```

Otherwise:

```text
alternative_hypothesis_id
= DIAGNOSTIC_ALTERNATIVE_ONLY
```

and MUST NOT contaminate family consensus.

---

# 4. Why SELECTED alternative is different from AMBIGUOUS competitor

Interpretation:

```text
SELECTED:
AI says one hypothesis is the best current interpretation.

alternative:
AI records a plausible runner-up.

AMBIGUOUS:
AI explicitly says two or more supplied hypotheses cannot be safely distinguished.
```

Do not treat those three meanings as equivalent.

The backend must preserve their different semantic roles.

---

# 5. Consensus membership audit object

Create:

`FAMILY_CONSENSUS_MEMBERSHIP_AUDIT`

Per subject:

```text
run_id
status

selected_hypothesis_id
alternative_hypothesis_id
ambiguous_competing_hypothesis_ids

consensus_member_ids
diagnostic_only_ids

membership_reason per ID:
  ACTUALLY_SELECTED
  EXPLICIT_AMBIGUOUS_COMPETITOR
  PROMOTED_ALTERNATIVE_BY_OTHER_RUN
  DIAGNOSTIC_ALTERNATIVE_ONLY
```

Hard target:

`UNJUSTIFIED_ALTERNATIVE_IN_CONSENSUS = 0`

---

# 6. Existing ambiguity safety remains

The repair must NOT shrink a real ambiguity set.

If an ID is:

```text
SELECTED in one run
AMBIGUOUS competitor in another
```

it remains in consensus.

If two IDs are both actually selected across runs:

both remain.

This preserves:

```text
SK hynix real W0 ambiguity
TSLA true structure conflict
TSM W3 dependency conflict
```

where observed.

---

# 7. Previous stable cohort — mandatory real regression

The previous variable-AI feedback trial's stable cohort must be explicitly re-tested:

```text
012450
086280
GOOGL
HUT
IBM
MU
WULF
```

Do not leave the list empty.

Set:

`PREVIOUS_STABLE_REGRESSION_TICKERS`

to these exact baseline controls unless the old immutable report proves a different set.

If different:
- use the immutable old report as source of truth
- document discrepancy

---

# 8. Stable regression baseline source

Use the immutable evidence from the immediate pre-family-consensus implementation/base.

For every stable control capture:

```text
old selected hypothesis frequency
old status frequency
old selected degree
old Fib-eligible state
old deterministic Fib families
old visible structural zones
```

Do not reconstruct the baseline from memory.

---

# 9. Stable regression pass rule

A previous stable control passes when the new membership semantics:

```text
does not remove safe Fib solely because of diagnostic alternatives
```

and there is no unintended material deterioration in:

```text
selected current structure
family eligibility
visible structural price zones
SR availability
confluence
```

Allowed changes:

```text
better provenance
display-only rounding
family-level classification detail
```

Not allowed:

```text
previously stable selected structure
→ SR-only
```

unless a newly discovered real ambiguity exists and is proven by actual repeated selections /
explicit AMBIGUOUS competing IDs.

---

# 10. Mandatory 012450 control

For `012450`, explicitly prove:

```text
if all repeated runs actually SELECT the same hypothesis
and no other hypothesis is ever SELECTED or explicitly listed as an AMBIGUOUS competitor,
a diagnostic alternative alone cannot make the subject family-level FAIL.
```

Set:

`012450_DIAGNOSTIC_ALTERNATIVE_CONTAMINATION = 0`

---

# 11. Other stable controls

Repeat the same audit for:

```text
086280
GOOGL
HUT
IBM
MU
WULF
```

Report whether the previous family-consensus MATERIAL_VARIATION status was caused by:

```text
real competitor
or
diagnostic alternative contamination
```

---

# 12. Difficult-cohort safety regression

Re-run the original difficult material cohort:

```text
000660
003690
005490
005930
010120
TSLA
TSM
```

The membership repair must not make true conflicts disappear.

Hard controls:

```text
TSLA_FALSE_STABILIZATION = 0
TSM_W3_DEPENDENCY_CONFLICT = PASS
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
```

---

# 13. SK hynix preservation

For SK hynix, re-run the exact 5-run frozen trial.

Current safe family result should not regress without evidence.

Audit:

```text
WAVE1_RETRACEMENT
WAVE3_RETRACEMENT
PRIMARY_CYCLE_RETRACEMENT
CURRENT_REBOUND

W5:
WAVE1_MULTIPLE
WAVE3_MULTIPLE
SPAN03_MULTIPLE
```

Do not require exact previous status if the corrected consensus membership legitimately changes it.

But explain every difference.

---

# 14. SK hynix resistance-zone continuity

Using the same frozen evidence, compare prior safe family-filtered structural resistance:

```text
approximately 1.869M–1.916M KRW
```

with the repaired result.

Do NOT hard-code this band.

The pass condition is:

```text
same underlying safe sources
→ equivalent structural band
```

or a fully explained source-backed difference.

Set:

`SK_HYNIX_STRUCTURAL_RESISTANCE_REGRESSION = PASS / MATERIAL_CHANGE / FAIL`

---

# 15. Family-consensus membership tests

Required:

### Case A
```text
Run1 SELECT A alt B
Run2 SELECT A alt B
Run3 SELECT A alt B
```

Consensus:

```text
A only
B diagnostic-only
```

### Case B
```text
Run1 SELECT A alt B
Run2 AMBIGUOUS [A,B]
```

Consensus:

```text
A,B
```

### Case C
```text
Run1 SELECT A
Run2 SELECT B
```

Consensus:

```text
A,B
```

### Case D
```text
Run1 SELECT A alt B
Run2 SELECT A alt C
```

with no explicit ambiguity:

```text
A only
```

### Case E
Invalid/wrong-ticker alternative:
reject from diagnostic set and record validator error.

---

# 16. Family consensus recalculation

After membership repair:

```text
consensus member IDs
→ endpoint dependency analysis
→ family stability
→ eligible Fib
→ filter unstable sources
→ rebuild confluence
→ shadow render
```

Do not reuse old confluence.

---

# 17. Previous stable regression gate — no vacuous pass

The readiness validator must fail if:

```text
baseline stable control count > 0
AND evaluated stable control count = 0
```

Create:

```text
PREVIOUS_STABLE_BASELINE_COUNT
PREVIOUS_STABLE_EVALUATED_COUNT
PREVIOUS_STABLE_REGRESSION_COUNT
```

Required:

```text
PREVIOUS_STABLE_BASELINE_COUNT = 7
PREVIOUS_STABLE_EVALUATED_COUNT = 7
PREVIOUS_STABLE_REGRESSION_COUNT = 0
```

unless immutable baseline evidence proves a different baseline count.

No empty-list PASS.

---

# 18. Custom GPT / Knowledge OHLCV default synchronization

The canonical internal price-structure calculation history is now:

```text
daily   = 1200
weekly  = 600
monthly = 300
```

Audit all source-of-truth knowledge/docs/runtime policy for stale defaults such as:

```text
daily 500 / weekly 300 / monthly 100
daily 300 / weekly 60 / monthly 60
```

The Custom GPT Investment Knowledge currently needs synchronization.

---

# 19. Knowledge wording requirement

Update the internal Price/OHLCV framework so it distinguishes:

```text
backend/internal SR & price-structure calculation:
  1200 / 600 / 300 where available

public getTickerAnalysisSnapshot:
  compact price context only
  NOT raw OHLCV access
```

Do not imply the Custom GPT can fetch raw 1200/600/300 bars through the public Action.

Keep:

```text
actual Action response only
no invented RSI/MACD/raw bars
```

---

# 20. Knowledge artifact output

If the repository owns the Custom GPT knowledge source:

- update it
- bump knowledge version/checksum according to project policy

If the live Custom GPT knowledge is external to the repo:

- create an upload-ready updated knowledge artifact
- do NOT mutate the live GPT automatically
- report exact file path and SHA-256

Set:

```text
CUSTOM_GPT_PRICE_HISTORY_DEFAULT =
1200_600_300_SYNCED / EXTERNAL_ARTIFACT_READY / FAIL
```

---

# 21. Knowledge regression

Ensure the knowledge update does NOT change:

```text
investment thesis vs price timing separation
price/supply not fundamental thesis
no unsupported target/stop
public snapshot does not expose raw OHLCV
```

Hard target:

`KNOWLEDGE_PRICE_POLICY_REGRESSION = 0`

---

# 22. User-visible technical-zone formatting contract

Raw technical numerics remain full precision in:

```text
numeric registry
audit JSON
provenance
backend calculations
```

User-visible prose must not show unnecessary 6-decimal technical prices.

---

# 23. Display-only formatting

Create or reuse one security-aware:

`format_technical_price_zone()`

It must be display-only.

It must NOT alter:

```text
zone_low raw
zone_high raw
Fib raw
confluence raw
numeric registry value
eligibility comparison
```

---

# 24. Formatter ownership order

Use:

```text
1. existing security/exchange-aware price formatter if canonical

2. verified market tick-size formatter if already owned

3. bounded currency/magnitude display formatter
```

Do not invent a trading tick rule without verified metadata.

---

# 25. KRW Korean-prose formatting

For Korean user-facing prose, allow a compact magnitude form.

Example for a high-price KRW zone:

```text
raw:
1,869,163.404750–1,915,788.795250 KRW

display:
약 186.9만~191.6만원
```

This is display formatting only.

If existing house style prefers whole KRW:

```text
약 1,869,000~1,916,000원
```

is also acceptable if deterministic and consistent.

Do not display:

```text
1,869,163.404750원
```

to users.

---

# 26. USD and other currencies

Reuse existing user-facing currency formatting.

Do not apply KRW "만원" rules to foreign securities.

Preserve security/currency basis.

---

# 27. Rounding containment test

Required:

```text
RAW_NUMERIC_CHANGED_BY_DISPLAY_FORMATTER = 0
```

And:

```text
DISPLAY_ZONE_CONTAINS_SAME_RAW_ZONE_MEANING = PASS
```

No rounding may change support↔resistance role or cross a current-price classification boundary.

---

# 28. Shadow renderer comparison

Create exact before/after shadow rendering for:

```text
000660
012450
TSLA
```

Demonstrate:

```text
numeric registry unchanged
logic unchanged except consensus-membership repair
display precision improved
```

---

# 29. Full 20-subject replay

Run full monitored universe.

Per subject report:

```text
old full-hypothesis stability
new full-hypothesis stability

old family-level status
new family-level status

actual SELECTED IDs across runs
explicit AMBIGUOUS competitor IDs
diagnostic-only alternative IDs

eligible family count
omitted unstable family count

SR-only fallback
confluence count
```

---

# 30. AI trial protocol

For previous stable 7:

```text
3 independent runs minimum
```

For difficult 7:

```text
5 independent runs
```

For valid-abstention controls:

```text
3 independent runs
```

Do not seed prior selections.

---

# 31. Quality objective

The task does NOT maximize Fib coverage.

It removes one artificial source of over-conservatism:

```text
diagnostic alternative
≠
active ambiguity
```

True ambiguity remains protected.

---

# 32. Required reports

Create:

1. `docs/reports/20260826-v3-consensus-membership-root-cause.md`
2. `docs/reports/20260826-v3-consensus-membership-repair.md`
3. `docs/reports/20260826-v3-previous-stable-real-regression.md`
4. `docs/reports/20260826-v3-012450-diagnostic-alternative-control.md`
5. `docs/reports/20260826-v3-difficult-cohort-safety-regression.md`
6. `docs/reports/20260826-sk-hynix-preenablement-regression.md`
7. `docs/reports/20260826-v3-knowledge-price-history-sync.md`
8. `docs/reports/20260826-v3-technical-zone-display-formatting.md`
9. `docs/reports/20260826-v3-preenablement-full-replay.md`
10. `docs/reports/20260826-v3-preenablement-safety-parity.md`
11. `docs/reports/20260826-v3-preenablement-readiness.md`
12. `docs/reports/20260826-v3-preenablement-artifact-index.md`

Recommended:

`docs/reports/20260826-v3-preenablement-readiness.json`

---

# 33. Required gates

Set exactly:

```text
CONSENSUS_MEMBERSHIP_SEMANTICS =
PASS / FAIL

UNJUSTIFIED_ALTERNATIVE_IN_CONSENSUS =
0 / NONZERO

PREVIOUS_STABLE_BASELINE_COUNT =
integer

PREVIOUS_STABLE_EVALUATED_COUNT =
integer

PREVIOUS_STABLE_REGRESSION_COUNT =
integer

PREVIOUS_STABLE_REGRESSION =
PASS / FAIL

012450_DIAGNOSTIC_ALTERNATIVE_CONTAMINATION =
0 / NONZERO

TSLA_TRUE_CONFLICT_PRESERVED =
PASS / FAIL

TSLA_FALSE_STABILIZATION =
0 / NONZERO

TSM_W3_DEPENDENCY_CONFLICT =
PASS / FAIL

SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE =
PASS / PARTIAL / FAIL

SK_HYNIX_STRUCTURAL_RESISTANCE_REGRESSION =
PASS / MATERIAL_CHANGE / FAIL

CUSTOM_GPT_PRICE_HISTORY_DEFAULT =
1200_600_300_SYNCED /
EXTERNAL_ARTIFACT_READY /
FAIL

STALE_INTERNAL_OHLCV_DEFAULT_REFERENCE =
0 / NONZERO

KNOWLEDGE_PRICE_POLICY_REGRESSION =
0 / NONZERO

TECHNICAL_ZONE_DISPLAY_FORMATTING =
PASS / FAIL

RAW_NUMERIC_CHANGED_BY_DISPLAY_FORMATTER =
0 / NONZERO

DISPLAY_ZONE_CONTAINS_SAME_RAW_ZONE_MEANING =
PASS / FAIL

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_PREENABLEMENT =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 34. Hard safety targets

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

UNJUSTIFIED_ALTERNATIVE_IN_CONSENSUS = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

TSLA_FALSE_STABILIZATION = 0
PREVIOUS_STABLE_REGRESSION_COUNT = 0
VALID_ABSTENTION_FORCED_TO_SELECTION = 0

TOLERANCE_WIDENING = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

RAW_NUMERIC_CHANGED_BY_DISPLAY_FORMATTER = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 35. Validation

Required:

```text
focused consensus-membership tests PASS
previous-stable 7/7 real regression PASS
012450 control PASS
difficult cohort safety PASS
SK hynix regression PASS
TSLA negative control PASS
TSM W3 control PASS
Knowledge sync PASS
display formatter tests PASS
full 20-subject replay safe

full pytest PASS
Ruff PASS
git diff --check PASS
Knowledge checksum/version PASS
Chart Knowledge consistency PASS
Public Action unchanged
operation IDs unchanged
implementation SHA Actions PASS
final main Actions PASS
API /health PASS
worktrees clean
```

---

# 36. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

CONSENSUS_MEMBERSHIP_SEMANTICS = ...
UNJUSTIFIED_ALTERNATIVE_IN_CONSENSUS = 0

PREVIOUS_STABLE_BASELINE_TICKERS = ...
PREVIOUS_STABLE_BASELINE_COUNT = ...
PREVIOUS_STABLE_EVALUATED_COUNT = ...
PREVIOUS_STABLE_REGRESSION_COUNT = 0
PREVIOUS_STABLE_REGRESSION = ...

012450_DIAGNOSTIC_ALTERNATIVE_CONTAMINATION = 0
012450_FAMILY_LEVEL_BEFORE = ...
012450_FAMILY_LEVEL_AFTER = ...

TSLA_TRUE_CONFLICT_PRESERVED = ...
TSLA_FALSE_STABILIZATION = 0
TSM_W3_DEPENDENCY_CONFLICT = ...

SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE = ...
SK_HYNIX_STRUCTURAL_RESISTANCE_BEFORE = ...
SK_HYNIX_STRUCTURAL_RESISTANCE_AFTER = ...
SK_HYNIX_STRUCTURAL_RESISTANCE_REGRESSION = ...

CUSTOM_GPT_PRICE_HISTORY_DEFAULT = ...
KNOWLEDGE_OLD_PRICE_HISTORY_DEFAULT = ...
KNOWLEDGE_NEW_PRICE_HISTORY_DEFAULT = 1200/600/300
KNOWLEDGE_OLD_SHA256 = ...
KNOWLEDGE_NEW_SHA256 = ...
UPDATED_KNOWLEDGE_ARTIFACT = ...

STALE_INTERNAL_OHLCV_DEFAULT_REFERENCE = 0
KNOWLEDGE_PRICE_POLICY_REGRESSION = 0

TECHNICAL_ZONE_DISPLAY_FORMATTING = ...
SK_HYNIX_RAW_RESISTANCE = ...
SK_HYNIX_DISPLAY_RESISTANCE = ...
RAW_NUMERIC_CHANGED_BY_DISPLAY_FORMATTER = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

PRICE_STRUCTURE_V3_PREENABLEMENT = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_FAMILY_SELECTIVE_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 37. Final principle

The last pre-enablement rule is:

```text
SELECTED alternative
is not automatically a competing active truth.
```

Use only:

```text
actually selected hypotheses
+
explicit AMBIGUOUS competitors
```

to define real family consensus.

Then prove the old stable controls actually remain stable.

After that:

```text
raw backend values stay exact
user-facing technical zones become readable
knowledge defaults agree with runtime
```

Only then proceed to selective production enablement.
