# Thesis Monitor — KR Holiday-Day Source / Message Suppression Proof
## 2026-09-24 KST — KRX Holiday Read-Only Proof + Minimal Repair If Required

**Execution date:** 2026-09-24 KST  
**Scope:** Korea market / canonical KR stock universe only  
**Primary objective:** prove that a KRX holiday is not treated as an active trading session and that KR market/stock messages are not generated or sent on that holiday.

---

# 0. Source-of-truth precedence

At execution time use:

1. any newer verified result ZIP explicitly supplied in-session;
2. current accepted R5A-R1 Rev2 preparation result:
   - result ZIP SHA-256:
     `bcebd2c6e0114852aa87164dcd1d46c289ae44f9cb073ee4de4a43a3e4430f3f`
   - accepted implementation/final SHA:
     `67ff7af7f7529f7aa6adda97af22105fd0501917`
   - operating main:
     `2097645892e30d84aba435416f98e7f9545a87fa`;
3. earlier handoff/result artifacts.

This KR task is an independent side proof. It must not modify, replace, or invalidate the US R5A-R1 evidence or the 2026-09-25 actual-cutoff plan.

Use a **separate worktree/branch**. Do not run this task in the prepared US live-cutoff worktree.

---

# 1. Required KR holiday policy

For a day on which the KRX regular market is closed:

- the date must not be classified as an active KR trading session;
- no synthetic/fake daily bar may be created for that date;
- the latest completed KR session must remain the most recent actual KRX trading session;
- stale/previous-session quote data must not be relabeled as same-day intraday data;
- KR market and KR stock messages for that holiday must be **suppressed**;
- the suppression must occur before any unnecessary model generation or delivery attempt.

Desired operational contract:

`KR holiday -> no KR Market/Core/A/B fresh generation -> no KR rendered messages -> no delivery intent/send`

The holiday is not an error condition. It should resolve to a deterministic skip/suppressed state, not a failure that retries indefinitely.

---

# 2. Today's expected date relation

Execution date:

`2026-09-24 KST`

Treat 2026-09-24 as the concrete holiday test date supplied by the operator.

Dynamically prove through the repository's authoritative KR trading-calendar path that:

- `2026-09-24` is not an open KRX regular-session date;
- the latest completed KR regular trading session resolves to the correct preceding session;
- no hardcoded “today minus one day” assumption is used.

Expected previous session is believed to be `2026-09-23`, but the implementation must derive it through the authoritative calendar/session logic rather than accepting this line as proof.

Also determine the next valid KR regular session dynamically. Do not hardcode it merely from this instruction.

---

# 3. Phase A — calendar/session proof

Without model calls or message generation, capture:

1. local KST date/time used by the process;
2. KR exchange calendar source/provider;
3. holiday/open-session decision for 2026-09-24;
4. latest completed session date;
5. previous session date;
6. next open session date;
7. any session-open/session-close timestamps used downstream;
8. evidence that weekend/holiday logic is exchange-calendar based rather than a weekday shortcut.

Required assertions:

- 2026-09-24 active-session = false;
- latest completed session != 2026-09-24;
- no code path creates a 2026-09-24 KR daily bar merely because the process date is 9/24.

If the authoritative calendar itself is wrong or unavailable, stop promotion and report the exact blocker. Do not substitute a guessed weekday rule.

---

# 4. Phase B — canonical KR universe source proof

Use the repository's **canonical KR stock universe**. Do not hand-select or silently shrink the set.

For every canonical KR symbol, capture read-only source evidence sufficient to determine:

- quote/current-price value if the normal provider returns one on the holiday;
- quote timestamp / provider business date where available;
- latest daily OHLCV row date;
- latest daily close;
- raw/adjusted basis metadata;
- normalized downstream price basis;
- whether any field is labeled `INTRADAY`, `CURRENT_SESSION`, equivalent;
- whether a 2026-09-24 bar appears anywhere in the normalized or persisted candidate data.

Do not infer “intraday” simply because a quote endpoint returns a numeric current price.

Required holiday invariant:

`holiday quote != proof of active intraday session`

If the provider returns the previous close or a stale quote, preserve the raw value and timestamp but normalize it as a closed-session / previous-session / non-intraday basis according to the existing schema.

Do not change the existing KR adjusted/raw vocabulary contract except where a proven bug requires a minimal repair.

---

# 5. Phase C — market context / normalized source object

Construct the normal pre-model KR market/stock source context in isolation.

Model calls must remain zero.

For KR market and every canonical KR stock assert that downstream context does not claim:

- today's KR session is open;
- today's KR intraday move exists;
- today's KR close exists;
- “장중”, “오늘 상승”, “오늘 하락”, “현재 매수세”, or equivalent real-time semantics solely from stale/previous-session data.

Capture the exact normalized fields that would normally feed Market/Core/A/B.

Required context evidence must make the holiday state explicit through the repository's existing equivalent fields, for example:

- market/session open = false;
- active trading date = null / not-today;
- latest completed trading date = prior valid session;
- current quote basis = closed/stale/previous-session where applicable;
- message eligibility = false / holiday suppressed.

Do not invent new schema names merely to satisfy this instruction; use or minimally extend the repository's established contract.

---

# 6. Phase D — KR holiday message suppression proof

This is the primary business rule.

Prove that on `2026-09-24`:

- KR market message eligibility = false;
- every canonical KR stock message eligibility = false;
- no fresh KR Market model generation is invoked;
- no KR Core/A/B generation is invoked;
- no KR rendered message is produced for delivery;
- no Telegram/send API is called;
- no delivery intent/outbox row is created;
- no retry/scheduler loop attempts to compensate for the holiday.

Preferred architecture:

`authoritative KR calendar gate`
→ `HOLIDAY / CLOSED_SESSION`
→ `KR message pipeline skip`
→ zero downstream generation/delivery side effects.

The gate should occur as early as practical, before paid/model work.

A holiday-day no-op terminal is acceptable only if it is deterministic and observable in logs/results.

Suggested semantic terminal:

`KR_HOLIDAY_MESSAGE_SUPPRESSED`

Use an existing canonical terminal if the repository already has one. Do not invent a new production-visible terminal if an established equivalent exists.

---

# 7. If suppression already exists

If all contracts already hold:

- do not modify production code;
- add only missing proof/tests if needed;
- produce a read-only result showing the actual 2026-09-24 holiday behavior;
- preserve provider raw receipts/hashes where read-only calls were necessary;
- report PASS at the exact tested scope.

Do not improve unrelated KR logic.

---

# 8. If suppression is missing or incorrect

If the system would generate/send KR messages on a KRX holiday, perform the **smallest causal repair**.

Allowed repair scope:

- authoritative KR session/calendar gating;
- pre-model message eligibility;
- KR market/stock holiday suppression;
- focused tests/fixtures;
- observability/result semantics necessary to prove the gate.

Do not change:

- investment thesis logic;
- technical/fundamental scoring;
- price levels;
- buy/sell/watch semantics;
- US source logic;
- US R5A/R5B collector;
- canonical KR universe;
- model prompts except if an existing prompt invocation must simply be bypassed on holidays;
- scheduler cadence except to make the existing run skip KR work;
- production recipients;
- delivery routing;
- broker logic.

The desired repair is **skip KR generation on holiday**, not “generate a holiday message”.

---

# 9. Required focused tests

At minimum prove offline:

## Calendar

- known open KRX day -> active session true;
- `2026-09-24` -> active session false;
- holiday latest completed session resolves to previous valid exchange session;
- weekend + holiday adjacency still resolves correctly;
- next session is exchange-calendar derived.

## Source basis

- stale/previous-session quote on holiday is not promoted to `INTRADAY`;
- daily OHLCV has no fake holiday bar;
- latest daily row remains prior valid session;
- adjusted/raw metadata is preserved.

## Message gate

- holiday -> KR Market generation call count 0;
- holiday -> KR Core/A/B generation call count 0;
- holiday -> KR rendered message count 0;
- holiday -> send/delivery intent count 0;
- open trading day fixture -> normal eligibility path remains reachable;
- US message path is not accidentally suppressed by KR holiday state.

## Scheduler/no-op behavior

- a scheduled whole-system run on a KR holiday may still execute other eligible markets, but KR branch deterministically skips;
- KR holiday skip is not classified as provider failure;
- holiday skip does not trigger retries/backfill.

No real model call is needed for these tests.

---

# 10. Actual-day read-only provider observation

Because this is a real KRX holiday, collect read-only provider evidence only where it materially proves source-basis behavior.

For each canonical KR symbol, if the normal provider call is safe/read-only:

- record request timestamp;
- provider date/time fields;
- quote/current-price fields;
- latest daily row;
- raw response hash;
- normalization result.

Do not send orders.
Do not use broker/account mutation endpoints.
Do not broaden provider scope.
Do not add a new external provider.

If a provider call is unavailable or fails, preserve that as provider evidence; do not reinterpret it as the holiday gate itself. The calendar gate must be independently provable.

---

# 11. Production-safety invariants

Unless a minimal holiday-gate code repair is required, production code should remain unchanged.

In all cases:

- actual message sends = 0
- recipient intent = 0
- delivery/outbox writes = 0
- broker actions = 0
- production DB decision/warning writes = 0
- scheduler mutation = 0
- notification mutation = 0
- model calls = 0
- Market/Core/A/B generation = 0
- US collector mutation = 0
- merge = 0
- push = 0
- deploy = 0
- service restart = 0.

Use isolated/test persistence where any code path would otherwise write.

Operating main must remain unchanged and clean.

---

# 12. Required validation

Run:

- focused KR holiday/calendar tests;
- focused source-basis tests;
- focused message-suppression tests;
- full pytest;
- Ruff;
- implementation diff check;
- Investment/Chart Knowledge check;
- secret scan.

No new unexplained skip/xfail.

If code changes:

- identify base SHA;
- implementation SHA;
- final local SHA;
- exact changed files;
- causal justification per file.

Do not report remote CI PASS unless actually pushed and observed.

---

# 13. Required result artifacts

Result ZIP must include at minimum:

- `REPORT.md`
- `summary.json`
- repo/base/final SHA receipts
- canonical KR universe receipt
- authoritative KR calendar/session receipt
- latest-completed-session proof
- next-session proof
- per-symbol holiday quote/daily-row source table
- raw response hashes where provider calls were used
- normalized source-basis table
- fake-holiday-bar check
- KR market message eligibility result
- per-stock message eligibility results
- model/Market/Core/A/B call count proof = 0
- rendered KR messages = 0
- send/delivery intent = 0
- scheduler/notification mutation = 0
- production DB mutation = 0
- focused/full/Ruff/diff/Knowledge logs
- operating before/after
- secret scan
- bundle manifest.

If code repair occurs, additionally include:

- patch/diff;
- new tests;
- before/after failing/passing proof.

---

# 14. Acceptance criteria

PASS only if all are proven:

1. 2026-09-24 is recognized as a closed KR session by the authoritative calendar.
2. Latest completed KR session is the correct prior valid exchange session.
3. No fake 2026-09-24 daily bar exists.
4. Holiday-returned quote data is not mislabeled as same-day intraday/current-session data.
5. Canonical KR universe is complete.
6. KR market message is suppressed.
7. Every canonical KR stock message is suppressed.
8. Model/Market/Core/A/B generation count = 0 for KR.
9. Rendered KR message count = 0.
10. Delivery/send intent = 0.
11. No production mutation.
12. US R5A-R1 preparation/live-cutoff path is untouched.

Suggested terminal:

`M12DS_KR_HOLIDAY_MESSAGE_SUPPRESSION_PROOF_PASS`

Use a repository-established equivalent if one already exists.

---

# 15. Interpretation

This task proves **holiday-day behavior only**.

It does not prove:

- normal KR intraday price correctness;
- normal open-session current-price basis;
- 15:30 KR close finalization timing;
- next open day's real-time quote freshness;
- US close ownership.

Those require separate live open-session evidence.

A successful result should establish the narrower operating guarantee:

> On a KRX holiday, Thesis Monitor recognizes that there is no active KR session, does not reinterpret previous-session data as today's intraday data, and does not generate or send KR market/stock messages.

Do not expand the conclusion beyond that scope.
