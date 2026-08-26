# thesis-monitor — 2026-08-26 Master Operating Work Instruction
## US Morning Market Pipeline + KR Afternoon Natural Review + Price Structure v3 Selective Enablement
## Split-track execution package for multi-agent / multi-worktree use

## 0. Purpose

This package consolidates the work discussed on 2026-08-26 into one coordinated plan while keeping
the three operational surfaces isolated.

```text
TRACK A
US morning market-message pipeline
→ bounded code repair + 2026-08-25 replay

TRACK B
KR afternoon natural market message
→ 2026-08-26 read-only production review

TRACK C
Price Structure v3
→ bounded selective production enablement
→ only after Track A/B gates pass
```

Do not merge these into one undifferentiated implementation task.

If one agent cannot safely handle the whole package, assign each track to a separate agent/worktree.

---

# 1. Current known state

## Price Structure v3

Latest known safe Price Structure v3 / renderer state before this master task:

```text
final/main/operating =
33f82227245f3757815a231cdaad86b75f8c2b76

OHLCV internal history =
1200 daily / 600 weekly / 300 monthly

bar completion temporal safety =
PASS

current-cycle vs grand-cycle separation =
PASS

family consensus =
PASS

deterministic SR base =
PASS

nearest vs major SR =
PASS

cross-timeframe proximity/relevance =
PASS

no-wave SR fallback =
PASS

renderer ownership =
PASS

legacy technical detector false-positive repair =
PASS

current-data E2E validation =
PASS

Open P0 =
0

Open material P1 =
0

PRICE_STRUCTURE_V3 =
INTEGRATED_READY_NOT_ARMED

PRODUCTION_ENABLEMENT_READY =
YES
```

Price Structure calculation/renderer repair is considered CLOSED unless Track C finds a genuine
production-wiring defect.

Do not reopen completed calculation work.

---

# 2. Current market-session targets

At 2026-08-26 23:53 KST:

```text
KR latest completed regular session =
2026-08-26

US latest completed regular session =
2026-08-25

US 2026-08-26 regular session =
in progress
```

Therefore:

```text
KR Track B target = 2026-08-26
US Track A replay target = 2026-08-25
```

Never use an incomplete US 2026-08-26 daily bar as completed-session evidence.

If execution time advances past the next US close, keep the frozen 2026-08-25 replay for Track A
and separately record any newer natural proof.

---

# 3. Today's market facts to use as validation controls, not hard-coded production answers

## US 2026-08-25

Current observed pattern:

```text
cap-weight US indices positive
QQQ / SOXX relatively strong
RSP equal-weight weak/negative

→ technology / semiconductor-led narrow rally
→ not broad risk-on
```

Exact Nasdaq exchange breadth may be:

```text
PUBLICATION_PENDING
```

Current temporal-risk controls observed in backend context include potentially older observations:

```text
VIX observation may be 2026-08-24
nominal/real yield observation may be 2026-08-24
WTI observation may be 2026-08-18
```

These are test controls.

Use actual provider packet evidence as source of truth.

## KR 2026-08-26

Current external directional cross-check:

```text
KOSPI positive
KOSDAQ roughly flat/slightly negative
```

But web breadth counts conflict across sources.

Therefore:

```text
Kiwoom ka20001 = canonical breadth source
external/web = cross-check only
```

Use actual Kiwoom structured values.

---

# 4. Parallelization policy

Tracks A and B MAY run in parallel.

Track C MUST NOT start implementation/arming until Track A and Track B have produced their gate
results.

Recommended worktrees:

```text
worktree-A:
codex/us-morning-market-pipeline-repair

worktree-B:
codex/kr-afternoon-natural-review

worktree-C:
codex/price-structure-v3-selective-enablement
```

Track C must be created/rebased from the latest safe main after Track A's implementation/report merge.

Track B is read-only except documentation/report commits.

---

# 5. Merge / promotion order

Preferred order:

```text
1. Master instruction docs-only commit

2. Track A
   implementation + reports
   tests/CI
   fast-forward to main if PASS

3. Track B
   read-only reports
   rebase on latest main if necessary
   merge report commit

4. Gate review

5. Track C
   branch from latest main
   bounded selective enablement
   tests/CI
   arm only if all Track C gates pass

6. Natural post-enablement proof
   read-only
```

No force push.

All worktrees clean at handoff.

---

# 6. Track A gate required before Track C

Minimum Track A gate:

```text
CURRENT_PACKET_CLAIM_POLICY = PASS
STALE_PENDING_PACKET_CLAIM = 0
WAIT_CURRENT_PACKET_PATH = PASS
PRIMARY_BACKUP_OWNERSHIP = PASS
FALLBACK_DEADLINE_SAFETY = PASS
OLD_PACKET_CURRENT_CANARY_BUDGET_CONSUMPTION = 0

RSP_STATE_PROPAGATION = PASS
US_STYLE_SECTOR_PROPAGATION = PASS
XLE_XLF_STATE_PROPAGATION = PASS

RSP_AS_EXCHANGE_BREADTH = 0
NASDAQ_BREADTH_BOUNDARY = PASS

MACRO_TEMPORAL_RENDER_BOUNDARY = PASS
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_VIX_AS_TODAY = 0
PRIOR_YIELD_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0

US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
BROAD_RISK_ON_WITHOUT_BREADTH_SUPPORT = 0

DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0

PRICE_STRUCTURE_V3_DIFF = 0
BUSINESS_THESIS_MUTATION = 0

CODE_CORRECTNESS = PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Natural post-repair US proof MAY remain pending:

```text
US_MORNING_MARKET_MESSAGE_PIPELINE =
REPLAY_PASS_NATURAL_REPROOF_PENDING
```

This does not automatically block Track C if all deterministic/replay gates pass, because Track C
does not alter the US market-context acquisition logic.

However the final master state must continue to show natural US proof as pending until observed.

---

# 7. Track B gate required before Track C

Track B must verify the actual 2026-08-26 KR afternoon natural run.

Minimum gate:

```text
KR_AFTERNOON_NATURAL = LIVE_PASS

KR_TARGET_SESSION = 2026-08-26
KR_COMPLETED_SESSION = PASS

KR_PACKET_INTEGRITY = PASS
KR_EXACTLY_ONCE = PASS
KR_EXACT_MESSAGE_PAYLOAD_MATCH = PASS

KIWOOM_KA20001 = PASS/PARTIAL safe
KOSPI_BREADTH = PASS
KOSDAQ_BREADTH = PASS
KR_BREADTH_SEMANTICS = PASS

KIWOOM_KA20003 = PASS/PARTIAL safe
KR_SIZE_STYLE_CONTEXT = PASS/PARTIAL safe

KIWOOM_KA10051 = PASS
KIWOOM_KA10066 = PASS/PARTIAL safe

KOSPI_KA10066_PAGINATION = PASS
KOSDAQ_KA10066_PAGINATION = PASS

KOSPI_FLOW_RECONCILIATION = PASS/FAIL correctly gated
KOSDAQ_FLOW_RECONCILIATION = PASS/FAIL correctly gated

unreconciled concentration prose = 0

KR_MARKET_DIGEST_LOCAL_FIRST = PASS
MATERIAL_INFORMATION_LOSS = 0

MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0
V3_PRICE_STRUCTURE_LEAK = 0

PRODUCTION_MUTATION_FROM_REVIEW = 0

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

If the natural run did not occur or evidence cannot be retrieved:

```text
Track B = INCOMPLETE
Track C = DO_NOT_START
```

Do not manually trigger KR production to manufacture proof.

---

# 8. Track C precondition

Track C may begin only after:

```text
Track A deterministic/replay gate = PASS
Track B natural review gate = PASS
Price Structure v3 baseline = INTEGRATED_READY_NOT_ARMED
Price Structure open P0/P1 = 0/0
```

Track C must use the latest safe main after Track A/B merges.

---

# 9. Track C scope

Track C is NOT another feature-development project.

It should only:

```text
connect the already-validated v3 renderer to production
through bounded selective eligibility
```

Runtime policy:

```text
ELIGIBLE
→ current deterministic SR
→ nearest + major
→ safe family-stable Fib/SR confluence when material
→ stored monitoring price rules remain separately labeled

ELIGIBLE_SR_ONLY
→ deterministic SR only
→ no empty Fib line
→ no unstable Fib

OMIT_PRICE_STRUCTURE
→ omit v3 block safely

BLOCKED
→ omit v3 block
→ never fail the whole stock/market message
```

Do not hard-code the prior 6/1 and 4/9 counts as permanent rules.

Use runtime eligibility.

---

# 10. Initial production scope

Bound initial production to:

```text
current monitored universe
```

Do not automatically enable for every arbitrary new/unregistered ticker in the system.

Expansion beyond the monitored universe is a later task.

---

# 11. Price Structure production safety invariants

Must remain:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0

REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0

UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
```

---

# 12. Track C bounded arming policy

Use the existing project feature-flag/config framework.

Do not invent a second rollout system if one exists.

Required behavior:

```text
feature OFF
→ exact current production behavior

feature ON + ELIGIBLE
→ v3 current price structure visible

feature ON + ELIGIBLE_SR_ONLY
→ SR-only visible

feature ON + OMIT/BLOCKED
→ existing production behavior
```

Rollback must be one bounded config/flag change.

---

# 13. Production Assist / AI canary independence

Price Structure selective enablement must not alter:

```text
Production Assist = OFF
Free Analyst canary limits
US primary/backup ownership
KR scheduled task timing
Open Research production integration
```

Hard target:

`UNRELATED_RUNTIME_POLICY_DIFF = 0`

---

# 14. First natural post-enablement proof

After Track C is armed, do not manually trigger messages.

Collect the next natural:

```text
KR monitoring message
US monitoring message
```

when they occur.

If not observed during the task, end with:

```text
PRICE_STRUCTURE_PRODUCTION =
ARMED_AWAITING_NATURAL_PROOF
```

Do not claim LIVE_PASS.

---

# 15. Natural proof checklist

For the first natural KR and US messages after enablement:

```text
target session correct
exact packet
exact message
delivery/receipt exactly once

company header intact

current price structure visible only when eligible
SR-only when appropriate
Fib omitted when unstable
Fib range preserved when materially extending SR

current SR vs stored rules separated
no stale legacy technical prose
no unsupported target/stop

business text unchanged except existing natural daily delta
```

---

# 16. Natural proof control stocks

Where present in the natural message, prioritize checking:

```text
000660
012450
010120

MU
TSM
SNDK
TSLA
RXRX
```

Do not force them into a message if the natural scheduled product does not include them.

---

# 17. Master stop conditions

STOP the entire rollout before Track C if:

```text
Track A new P0/P1 > 0
Track B new P0/P1 > 0
KR natural exactly-once fails
wrong target session detected
US stale macro rendered as current
US stale prior packet claim remains possible
price-structure baseline regresses
```

Create a separate bounded repair for the failing track.

Do not mix the repair into another track.

---

# 18. Master success states

## Stage 1

```text
TRACK_A = REPLAY_PASS_NATURAL_REPROOF_PENDING
TRACK_B = LIVE_PASS
TRACK_C = NOT_STARTED
```

Safe to begin Track C.

## Stage 2

```text
TRACK_C =
ARMED_AWAITING_NATURAL_PROOF
```

Selective production is armed but natural proof is pending.

## Final

```text
TRACK_A natural US proof = PASS
TRACK_B natural KR proof = PASS
TRACK_C KR natural proof = PASS
TRACK_C US natural proof = PASS

MASTER =
LIVE_PASS
```

---

# 19. Master required reports

Create:

1. `docs/reports/20260826-master-track-status.md`
2. `docs/reports/20260826-master-gate-matrix.md`
3. `docs/reports/20260826-master-merge-lineage.md`
4. `docs/reports/20260826-master-natural-proof-status.md`
5. `docs/reports/20260826-master-final-readiness.md`
6. `docs/reports/20260826-master-artifact-index.md`

Recommended:

`docs/reports/20260826-master-final-readiness.json`

---

# 20. Master completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...

TRACK_A_BRANCH = ...
TRACK_A_BASE = ...
TRACK_A_IMPLEMENTATION = ...
TRACK_A_FINAL_MAIN = ...
TRACK_A_STATUS = ...

TRACK_B_BRANCH = ...
TRACK_B_BASE = ...
TRACK_B_REPORT_COMMIT = ...
TRACK_B_STATUS = ...

TRACK_C_BRANCH = ...
TRACK_C_BASE = ...
TRACK_C_IMPLEMENTATION = ...
TRACK_C_FINAL_MAIN = ...
TRACK_C_STATUS = ...

US_TARGET_SESSION = 2026-08-25
KR_TARGET_SESSION = 2026-08-26

US_REPLAY_GATE = ...
US_NATURAL_PROOF = ...

KR_NATURAL_GATE = ...

PRICE_STRUCTURE_BASELINE = ...
PRICE_STRUCTURE_SELECTIVE_ENABLEMENT = ...
PRICE_STRUCTURE_KR_NATURAL_PROOF = ...
PRICE_STRUCTURE_US_NATURAL_PROOF = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

MASTER_STATUS =
TRACKS_A_B_PASS_READY_FOR_C /
ARMED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
BOUNDED_REPAIR_REQUIRED

NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 21. Final principle

Keep the three questions separate:

```text
US:
Did the current completed US session produce the correct current packet and temporally valid market
message?

KR:
Did today's completed Korean session produce the correct local-first breadth/flow message exactly
once?

Price Structure:
Can the already validated v3 renderer now be exposed only where runtime eligibility says it is safe?
```

Parallelize collection and repair where safe.

Integrate only at the gates.
