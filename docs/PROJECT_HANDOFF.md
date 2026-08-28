# Thesis Monitor Project Handoff

This document is a canonical continuation point for the AI-assisted monitoring project. Read it
with [MASTER_WORKFLOW.md](MASTER_WORKFLOW.md), [project-state.json](project-state.json), and
[NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md) before changing runtime policy, Knowledge,
validation, delivery, or Scheduled Tasks.

## Latest Handoff - One-Shot KR Close Live Proof

Use instruction commit `a0d8f190a0dd2105925810bcf21eeb1d483e0277` and start with
`docs/reports/20260828-run-now-kr-live-proof.json`, the exact KR market/stock messages, V3 validator
proof, delivery proof, and scheduler-cleanup report. The evidence implementation commit is
`239db58958b1193a8fd591500618ee4e7940c994`.

Operating and `origin/main` were both `23b17c487a4c0ae7dc56935e9028cf62f2b00f2c` at preflight.
The regular KR command ran once from a temporary `+300s` LaunchAgent, generated packet
`2026-08-28-kr-run-44-e4cf532e619b`, and exited `0`. The temporary label was removed with run count
one; the normal `16:05/16:20/16:50` schedule and plist SHA are unchanged. Current Kiwoom context was
available with `42/42` successful requests.

The existing KR fallback command completed the held packet through the normal notifier because the
calendar fallback deadline had already passed. Production delivery was `8/8`: one market digest and
seven stock messages, exact persisted payload match `8/8`, duplicate/orphan/unowned retry `0/0/0`.
All live V3 semantics pass, including the `000660` selected-support/omitted-resistance incident.
Open P0/material P1 is `0/0`; `FINAL_V3_VALIDATOR_CONVERGENCE=LIVE_PASS`. Do not rerun KR. Continue
with the pending natural US market and Price Structure review.

## Previous Handoff - Run-44 V3 Validator Convergence

Use instruction commit `1e8a008368ab79c44213545da192edbc5a545c98` and implementation
`aa5e7d4a799a1e2093bca6f87ff09f19c19e94a9`. Start with
`docs/reports/20260828-final-operating-readiness.json`, the exact `000660` frozen replay, KR7/US
replays, cross-market exact test messages, and the artifact index.

The actual operating and `origin/main` baseline was
`026df711fa151cc7816b2a57d9ed7d224c1b33cf`; the earlier `d3a58c9` report value was stale
metadata only. Latest runtime already resolves run-44. Candidate availability is not a render
obligation; emitted V3 bindings are the validator source of truth. Intentional materiality or
display-budget omissions pass, while missing selected standalone, confluence, and provisional facts
fail. V3-off legacy validation remains unchanged.

Run-44, KR `7/7`, US/foreign `13/13`, and 22 dedicated test-sink messages pass with exact payload
parity and zero production sends/intents, duplicates, or orphans. No runtime module changed. Open
P0/material P1 is `0/0`, Production Assist is OFF, and the earlier cancelled 16:50 KR production
run was not recreated by that retrospective task. The later operator-authorized one-shot above
closed the KR live proof. Continue only with the remaining natural US review.

## Latest Handoff - Major Structural S/R Reality Gate

Use instruction commit `4a5702823da3f950b9f125bcbcfecd7c6cfa84df` and implementation
`c5f1fbcb9c952c2d14ad0b178a9b33351d15b512`. Start with
`docs/reports/20260828-major-sr-readiness.json`, the GOOGL negative control, price-anchor contract,
indicator/interaction semantics, US/KR before-after, exact test-message, promotion, and smoke
reports.

The root cause was shared: Bollinger observation dates occupied a legacy interaction field, merge
treated them as price interactions, and major ranking/rendering had no anchor gate. The new shared
contract separates observation from interaction and requires confirmed Pivot/Balance-Box/equivalent
price evidence. One same-raw replay passes US `13/13` plus KR `7/7`, near-S/R stays identical, and
all visible majors carry source, anchor, as-of, currency, security, and adjustment provenance.

Twenty stock messages reached the dedicated non-production sink exactly once. Production sends,
intents, duplicates, orphans, task runs, Pilot/DB mutations, and archive rewrites were zero.
Operating is healthy with KR/US Price Structure ON, AI mode shadow, and Production Assist OFF.
P0/material P1 is `0/0`; `MAJOR_SR_REALITY_GATE=DEPLOYED_AWAITING_NATURAL_PROOF` and
`NATURAL_MAJOR_SR_REALITY_GATE=PENDING`. Wait for natural stock messages and review them read-only.
Do not run a Scheduled Task or production Telegram manually.

## Latest Handoff - US Macro Exact-Payload Quality Repair

Use instruction commit `e59c0e6a0574824bd512c1d4c06775b0afe1e468` and implementation
commit `535855631890928a9dd9e798e12adbeabde74df2`. Start with
`docs/reports/20260828-us-macro-quality-readiness.json`, the exact-message, root-cause, neutral
policy, broken-payload regression, test-delivery, safety-parity, and artifact-index reports.

The historical run-43 payload SHA `23bfd679...f822` fails the new exact-payload gate as expected.
Generic neutral macro is omitted; a specific neutral macro requires canonical evidence, date,
temporal role, and grammar-safe semantic rendering. The final renderer ignores stored macro prose.
One production-equivalent US market message reached the dedicated non-production sink exactly once;
its rendered/outbound/received/validator/report SHA is `d4c4d2e2...bbb3d3`. Stock sends,
production-recipient sends/intents, duplicates, orphans, and retries were zero.

Operating has KR TOP3, KR Price Structure, and US Price Structure ON; AI mode is shadow and
Production Assist is OFF. P0/material P1 is `0/0`; state is
`DEPLOYED_AWAITING_NATURAL_PROOF`. Next action is read-only review of the next natural US morning
message. Do not manually run a Scheduled Task or send production Telegram.

## Latest Handoff - US Market And Price Structure Rollout

Use instruction commit `2ee201690787136780c7d5c8a046506d44227633` and implementation
commit `1ba463571060a1fc9a5868afcdeab3de15f2bbe6`. Start with the
`20260828-us-full-message-*` and `20260828-us-price-structure-*` report families and the single
completion bundle.

The immutable source is run-43 packet `2026-08-28-us-run-43-c086d78415ac` for completed session
2026-08-27. The deterministic full-market renderer consumes SPY/QQQ/IWM/SOXX/RSP and sector
dispersion without legacy macro promotion. All 13 active US/foreign subjects passed selective
Price Structure as `ELIGIBLE_SR_ONLY`; no Fib, look-ahead, partial-bar pivot, security/currency
conflict, target/stop, or current-vs-stored-rule leakage was observed.

The dedicated non-production sink received one market message and 13 stock messages, each exactly
once with payload parity. Production-recipient sends and production delivery intents were zero.
Operating has KR TOP3, KR Price Structure, and US Price Structure ON; Production Assist remains
OFF. `US_FULL_MESSAGE=DEPLOYED_AWAITING_NATURAL_PROOF` and
`US_PRICE_STRUCTURE=ENABLED_AWAITING_NATURAL_PROOF`, with P0/material P1 `0/0`.

Next action is read-only review of the next naturally scheduled US morning market and stock cycle.
Do not manually run a Scheduled Task or send a production Telegram. Natural proof alone may promote
these product-family states to `LIVE_PASS`.

## Latest Handoff — US Current-Session Natural Reproof PASS

Use instruction commit `18d36852f74a6a1609365cbcb5dc093feb293e71`. Start with
`docs/reports/20260828-us-morning-natural-reproof-readiness.json`, the exact-message,
current-packet, exactly-once, shared-plan, evidence-utilization, macro, breadth, and completeness
reports.

Natural US run 43 used operating SHA `910e2f7e78b3d5445e5caa46c605fa85a76c43b2` and packet
`2026-08-28-us-run-43-c086d78415ac` for completed session `2026-08-27`. `codex-us-primary`
owned the only claim. The backend delivered one market digest plus 13 stock messages `14/14`
exactly once, with archive, DB payload, rendered text, and receipt hashes aligned.

The final digest consumes SPY/QQQ/IWM/SOXX, RSP participation/style, and XLK/XLP dispersion from
the shared market plan. Nasdaq breadth remains safely `PUBLICATION_PENDING`; macro temporal roles
pass and macro does not replace the current-session market. Material information loss, US Price
Structure leakage, open P0, and open material P1 are all zero. `US_MORNING_NATURAL=LIVE_PASS` and
`US_TRACK_A=LIVE_PASS`. One non-rendered optional MACRO_CONTEXT label/mapping item remains P2.
Next action is `REVIEW_MASTER_GATES`; do not reopen the bounded repair.

## Latest Handoff — KR Market Internal Formatting PASS

Use instruction commit `dd1b5eb712081c222bcfe1b4465d4fe0aac5f89a` and implementation
`03a418ab1f616d0063becf3928a1327056dd2d66`. Start with
`docs/reports/20260828-kr-market-internal-readiness.md`, the exact test message, delivery evidence,
AI/fallback parity, safety parity, and the single completion bundle.

The run-42 production-equivalent market payload retained every value, TOP3 rank, selected evidence,
and source ref. `📊 시장 내부` now has standalone size/strong/weak headings and scoped bullet rows.
The dedicated non-production sink received exactly one market message with byte-identical response;
stock sends, production sends/intents, duplicates, and orphans were zero.

Operating is healthy at the implementation SHA. KR TOP3 and KR Price Structure remain ON, US Price
Structure and Production Assist remain OFF, and open P0/material P1 are `0/0`. Keep rollout state
`ENABLED_AWAITING_NATURAL_PROOF`; the next action is read-only review of the next naturally
scheduled KR close message. Do not run a task or production Telegram manually.

## Latest Handoff — KR Final Pre-Enable Resume PASS

Use exact instruction commit `68ede1eae42315d94a89023fbc6c1f9be07fc99d` and implementation
commit `315081005198e7b5676e9383f10d4a52b3d3ca34`. Implementation Actions run `33094185080`
passed Test and Lint. Start with `docs/reports/20260828-kr-final-rollout-readiness.json`, the test
sink isolation and delivery evidence, operating-promotion reports, and the single completion bundle.

The canonical test sink is configured outside git and differs from production. Test delivery was
one market plus seven stock messages, exact 8/8, one attempt each, with production-recipient sends,
production delivery intents, duplicates, orphans, and unowned retries all zero. The completed
session is 2026-08-27 packet `2026-08-27-kr-run-42-5d8d23e6fbd6`.

Operating has KR TOP3 ON and KR Price Structure ON. All seven KR subjects were
`ELIGIBLE_SR_ONLY`; US Price Structure and Production Assist remain OFF. State is
`ENABLED_AWAITING_NATURAL_PROOF`, not `LIVE_PASS`, with open P0/material P1 `0/0`. Do not run a
manual task or production Telegram. Inspect the next natural KR market digest and monitored-stock
cycle, then close or independently roll back the affected flag if a material failure appears.

## Current Authoritative Handoff — 2026-08-27 KR Natural Reproof

Start from exact instruction commit `107f40b0b6b7e794f420534e71b69af0c969e643` and read
`docs/reports/20260827-kr-afternoon-natural-reproof-readiness.md`, the exact-message report,
Kiwoom family audits, reconciliation/concentration reports, local-first parity, completeness JSON,
and artifact index first.

Natural KR run 42 used operating SHA `a1fb1a7006109f8699e03997662bde27db5ad464` and final packet
`2026-08-27-kr-run-42-5d8d23e6fbd6` for the completed 2026-08-27 session. The backup AI reviewer
passed after one bounded correction, and the deadline dispatcher delivered `8/8` exactly once.
All archive, persisted, and receipt-linked payloads match.

Kiwoom is complete at `42/42`; ka10066 pagination is KOSPI `14/1316` and KOSDAQ `19/1824` with no
duplicates. Aggregate reconciliation remains unresolved for all six actor/market pairs, so
concentration stays blocked. Numeric registration is `1989/1989` with unsupported zero. The exact
digest consumes both index directions, both breadth states, and all aggregate participant
directions before any secondary context. KRX secondary publication remains pending and safe.

`NATURAL_KR_REPROOF=PASS`, open P0/material P1 are `0/0`, and the bounded KR repair is
`LIVE_PASS_RUN42`. The separate US repair remains `REPLAY_PASS_NATURAL_REPROOF_PENDING`; wait for
the next naturally scheduled US morning proof. Track C stays `DO_NOT_START`, Price Structure v3
stays `INTEGRATED_READY_NOT_ARMED`, and Production Assist stays OFF. Do not manually execute a
task or Telegram delivery.

## Current Authoritative Handoff — 2026-08-26

### Price Structure v3 Renderer Integration Micro-Repair

Start from exact instruction commit `2ac7eaaede9cb8d9047173bbec5f2bd99c665573` and implementation
commit `4246efb4f8afa3516402d1df7864967c177ac6e7`. Read the renderer readiness JSON, Fib render audit,
current-vs-stored audit, legacy-prose audit, exact six controls, full-universe replay, exact message
diff, quality, safety, and artifact index first.

The renderer now preserves a partially overlapping Fib/SR range when it extends beyond a displayed
structure zone. Current OHLCV-derived SR renders under `📐 현재 가격 구조`; existing confirmation,
support, warning, and invalidation rules remain under `🧭 기존 등록 가격 규칙` and
`chart:stored_price_rules`. MU's stale 2026-08-12 OHLCV/MACD sentence is suppressed while its
business sentence is unchanged.

The frozen 20-subject replay preserves KR `6+1` and US/foreign `4+9` eligibility with 16 material,
four minor, and zero worse outcomes. All hard counters are zero. State is
`INTEGRATED_READY_NOT_ARMED`, production enablement readiness is YES, and open P0/material P1 is
`0/0`. Do not activate from this handoff. The next authorized task remains bounded selective
enablement; Telegram, schedules, Public Action 0.4.5, schema 4, stored rules, assessments, and
Production Assist remain unchanged.

### Price Structure v3 Pre-Enablement Micro-Repair

The exact instruction is commit `38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8`; implementation is
`84f8f549bc8fa0338309a84b23b2738f2e357646`. Read the pre-enablement readiness JSON, membership
repair, real stable regression, `012450`, difficult-cohort, SK hynix, Knowledge sync, display, full
replay, and safety reports first.

Active family membership now means actually selected IDs plus explicit `AMBIGUOUS` competitors.
A `SELECTED` alternative is diagnostic only unless another run promotes it. The exact stable cohort
`012450, 086280, GOOGL, HUT, IBM, MU, WULF` was evaluated 7/7 with zero artificial regression;
`012450` is `FAIL -> PASS` with contamination zero. TSLA and TSM conflicts remain protected, and
SK hynix's raw resistance is unchanged while the shadow display is compact.

Investment Knowledge v3.1 and its runtime/upload mirrors are byte-identical at
`dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312`, with internal history
`1200/600/300` and no raw OHLCV in Public Action. State is `INTEGRATED_READY_NOT_ARMED`, production
enablement readiness YES, P0/material P1 `0/0`. The next feature-local action is separately
instructed bounded family-selective enablement. Do not arm this repair, run a task, send Telegram,
mutate assessments, or enable Production Assist.

### Price Structure v3 Family Consensus Stability Closure

Start from immutable instruction commit `b0f81c8e16f588e314f93eb6097370e85f285241` and
implementation commit `631e82f202b6f081866ef83c8b67b2138a8b51d8`. Read the family-consensus
artifact index/readiness JSON, the five family-contract architecture documents, and the detailed SK
hynix validation first. The repair preserves deterministic SR and existing tolerances while making
Fibonacci eligibility depend on exact endpoint families, bounded hypothesis equivalence classes,
and validated ambiguity sets. Unstable family sources are excluded before confluence.

The signed-in archive-only protocol completed 11 calls and 74 ticker decisions with zero runtime
failure or semantic rejection. Full-universe replay passes KR `7/7` and US/foreign `13/13`.
SK hynix's full hypothesis remains material, but six of seven Fibonacci families are safely exact
or price equivalent and one material W1 family is omitted. TSLA retains zero safe families and its
true conflict; TSM retains its W3-dependent conflict. The supplied user engine is staged only as
`REFERENCE_ONLY / NOT_PRODUCTION_RUNTIME`; its endpoint and confirmation method matches the
selected SK hypothesis.

State is `INTEGRATED_READY_NOT_ARMED`; production-enablement readiness is YES and open P0/material
P1 is `0/0`. The next feature-local task is
`BOUNDED_PRICE_STRUCTURE_V3_FAMILY_SELECTIVE_ENABLEMENT`. Do not activate from this handoff.
Production SR, packets, Telegram, schedules, Public Action 0.4.5, schema 4, assessments, and
Production Assist remain unchanged.

### Price Structure Wave Fibonacci v3 Bounded Repair

Start with exact instruction commit `82cb04e2880d1ed7b0405e1ddd20c5f333305394`, implementation
commit `bea877d3a6a9977c19832cbde28ed235676929d2`, the four bounded-repair architecture documents,
and `docs/reports/20260826-v3-bounded-repair-artifact-index.md`. Calendar-aware completion keeps
SK hynix's June/July monthly endpoints provisional at the 2026-08-26 observation cutoff. Official
free provider continuation gives 1200 completed daily bars for 14 long-listed subjects; six shorter
listing histories remain safe partial.

The 2023-01 SK W0 is independently visible in `PRIMARY_CURRENT_CYCLE`; 2015/2016 candidates remain
`GRAND_CYCLE`. Fourteen signed-in archive-only calls have zero runtime/semantic rejection and zero
selected-but-not-fed outcomes. Seven subjects are stable, six safely abstain, and seven material
variations, including SK, remain shadow-only. The unavailable user reference engine is P2.

State is `INTEGRATED_READY_NOT_ARMED`, selective production readiness is `YES`, and open P0/material
P1 is `0/0`. Do not activate v3 from this handoff. The next feature-local task is a separately
instructed bounded enablement limited to stable eligible subjects with immediate fallback for all
others. Production SR, Telegram, schedules, Public Action 0.4.5, schema 4, assessments, and
Production Assist are unchanged.

### 2026-08-26 KR Rehearsal And US Exchange Breadth

The exact instruction commit is `d7a01015617b3fbfb16f4194d1d02c41004a4197`; implementation is
`0e2fc6548e4eadc53df6acbdae8f92b397bd6522`, with evidence commit
`3b1fef7050dbed7eea535ba57e614c104d82e4de`. KR completed-session recollection passed 42/42,
matched source SHA `44665b1b...` exactly, and replayed run-38 at 8/8 with no safety error. The
post-midnight session guard now accepts only the calendar-derived latest completed regular session.

Official Nasdaq breadth is integrated as a supplemental fail-open source with exact scope
`NASDAQ_LISTED_ISSUES`. Run-37 resolves to completed session 2026-08-24, but the official YTD file
retrieved on 2026-08-26 is published only through 2026-08-20. Therefore run-37 breadth is
`PUBLICATION_PENDING`, injection is zero, and all 14 existing messages remain safe. A separate
published 2026-08-20 holdout proves the contract and broad-vs-concentrated context value without
being back-projected. NYSE official/free breadth remains unavailable.

State is `US_EXCHANGE_BREADTH=PARTIAL`, production-ready, with open P0/material P1 0/0. Keep full
mode OFF, canary 1/2/3, Open Research integration 0, Trade AR OFF, and Production Assist OFF. Wait
for natural KR proof and a natural US exact-session publication; do not run a task or Telegram
manually.

### Structured Data Acquisition First And Message Quality v2

The exact instruction commit is `e04403c76abfd8d2f74ca91d438fccc54b479bad`; implementation is
`1a6d2f411e7fa9ef414197a3fa5711b336a0d3e7`. `structured-market-context-v1` keeps exact market,
session, retrieval, publication, source, hash, and data-gap identity. Missing/current-publication
data never defaults to zero or borrows a prior session.

KR and US acquisition are both safe `PARTIAL`. The 2026-08-25 exact KRX slot is
`MARKET_COMPLETED_PROVIDER_PENDING`, so KR receives no current breadth, index, or market-flow
number and its structured value-add is `NO_MATERIAL_VALUE`. US receives RSP plus the 11 sector
SPDRs; current style/sector context adds material evidence while exchange breadth and participant
flow stay Unknown. US structured value-add is `PASS`.

Quality-v2 archive replays pass KR `8/8` and US `14/14`; generic synthesis is `36 -> 0`, duplicate
substantive messages are `18 -> 0`, all `245` numeric claims bind automatically, and all hard safety
counts are zero. The `1/2/3` Free Analyst canary remains enabled pending natural proof, full mode is
OFF, Production Assist is OFF, and Open Research production integration remains zero. Review the
next naturally scheduled US run read-only, then KR when complete KRX publication evidence exists.
Do not manually execute a task or send Telegram.

### Free Analyst Adaptive Limited Canary Armed

Instruction commit `73802b8849f674698bfdb3bfd7f3d0df89c236b2` explicitly authorizes the
already-integrated limited canary. The immutable simulation passes with market `1`, stocks `2`,
total `3`, scoped runtime quality PASS, and all hard safety counts zero. Operating Settings are now
`FREE_ANALYST_ADAPTIVE_ENABLED=true` and mode `free_analyst_adaptive_canary`; full mode is OFF.

Production Assist governance remains OFF and the existing Pilot remains enabled unchanged. Open
Research/Event Attribution and exact Trade AR remain outside scope; Inventory and cash-flow modes
are unchanged. State is `INTEGRATED_CANARY_PENDING_NATURAL`. At 12:44 KST neither post-activation
KR nor US natural run existed. Wait for the first eligible KR run without manual execution, audit
every slot and receipt read-only, and disable only the canary on a delivered hard incident.

### Prior Common AI Core v1 Integration Baseline

Instruction commit `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7` precedes implementation commit
`4bcf117fa36d9a74c45e6f9c2626e38e07e52bd3`; exact implementation Actions run `32803786800`
passes Test and Lint. The minimum production-relevant Free Analyst, evidence-lock adapter, and
Adaptive Renderer chain is integrated. Open Research and Event Attribution are not integrated.

Before the explicit activation above, the control plane was type B. `ai_review_mode=shadow` and the
operating `ai_review_pilot_enabled=true` allowed the existing Pilot to select validated current AI output;
Production Assist remains a separate governance approval state. The new feature defaults to
OFF/current and independently required both its own switch and the existing Pilot gate. US run-37 replays
14/14, the fixed KR negative-control replay passes 8/8, and every hard safety count is zero. A
simulated one-market plus two-stock canary passes scoped runtime quality. The full cohort remains
disabled due to two generic synthesis-repetition P2s.

Open P0/material P1 were 0/0 and the integration state was
`COMMON_AI_CORE_V1=INTEGRATED_READY_NOT_ARMED`. That state is superseded by the explicitly armed
limited canary above; full mode is still not authorized.

### 2026-08-24 KR Shadow Gate Packet Persistence Repair

Instruction commit `7da8d8866a9b7aafc8c010424cdbc4192de46cbb` precedes implementation
`64086c4af7735dcbe2fd3f5093f4167952a280e0`. `ROOT_CAUSE_BRANCH = C`: the v3.2-era company-profile
and numeric-semantic gate correctly protected AI Shadow claims, but incorrectly denied the immutable
packet required by deterministic fallback. Natural run 36 completed 7/7 on a valid XKRX target; 210
new investor-flow reconciliation audit paths made Shadow ineligible, then packet, intents, and sends
were all zero.

The new `kr-production-packet-persistence-v1` contract blocks only incomplete/invalid production,
fallback unavailability, explicit P0/hard errors, and persistence failure.
`shadow-cohort-readiness-v1` keeps unsupported AI claims fail-closed and records its own suppression
or exception with production influence `none`. Production packet identity excludes transient shadow
state. The read-only `/tmp` replay persists one packet, binds and holds eight unique intents, keeps
AI unclaimable, and leaves deterministic fallback reachable with zero Telegram sends.

Open P0/material P1 are 0/0. State is `DEPLOYED_PENDING_NATURAL`; replay is not LIVE PASS. Wait for
the first natural eligible KR packet. Inventory remains `SELECTIVE_INVENTORY` and enabled pending
natural; exact Trade AR and Production Assist remain OFF. Do not manually run KR production,
recreate providers, mutate DB/Pilot, or rewrite the original run.

### 2026-08-24 Macro Digest Temporal Repair

Instruction commit `951558c0ec79f84b739eff1cbafd2870eb6f3fba` precedes implementation
`68a6c39a098380d8a22de5b4d784c730818e9b04`. The architecture trace confirmed Branch B:
observation dates, provider freshness, and market-session state existed, but no role distinguished a
new daily observation from prior-session/reference evidence.

`macro-digest-temporal-eligibility-v1` is now shared by thesis daily signals, shocks, ticker impacts,
the deterministic digest, market intelligence, AI context, rendering, and semantic validation. In
immutable run-35, SPY/QQQ/IWM/SOXX become explicit 8/21 prior-session context; unchanged FRED,
WTI, VIX and collection-date USD/KRW references cannot create a current signal. The mixed regime is
preserved. A normal 8/22 after-close replay and weekend/holiday/mixed/revision/early-close fixtures
preserve genuinely new observations.

Open P0/material P1 are 0/0 and state is `DEPLOYED_PENDING_NATURAL`, not live pass. Do not recreate
the 8/24 provider state, rerun production, send Telegram, or rewrite the archive. Review the next
natural US digest read-only. Inventory remains enabled pending its separate natural evidence; Trade
AR and Production Assist remain OFF; night-futures and KR producer natural proofs continue in
parallel.

Phase 9.1E.1 Inventory-only enablement is implemented on immutable instruction commit
`880e7a9834439971f53b8a7bc0712d0ece26854d`, explicit morning-evidence merge `018af42`, and initial
implementation commit `85ab01130f34650edca6a0bcba5c5ae52db4edf0`. Run-32 packet
`2026-08-22-us-run-32-dde10ec6c9eb` proves total Inventory `LIVE_PASS`; exact Trade AR remains
`NOT_OBSERVED`.

The implementation reuses `working-capital-user-visible-v1`, enforces Inventory-only preflight,
adds current-formal/PIT/materiality/cash-flow-redundancy selection to AI and fallback, and binds one
Inventory `%p` relation to `business_earnings`. The 20-subject replay selects `000660`, `005490`,
and `005930`; MU and TSLA are suppressed by compatible Phase 9.0E cash-flow context. AI/fallback,
numeric, semantic, causal, quality and kill-switch checks pass with open P0/material P1 zero.

Operating activation completed at 12:16 KST after exact-SHA CI, main/operating parity, health and
scheduler checks. `WORKING_CAPITAL_USER_VISIBLE_MODE=SELECTIVE_INVENTORY`, Inventory is
`ENABLED_PENDING_NATURAL`, and Trade AR is `OFF_PENDING_NATURAL_PROOF`. Never mark user-visible
Inventory live pass until an actual natural delivered message selects it.

Phase 9.1E working-capital user-visible pre-integration is complete on immutable instruction commit
`99f7e86f3ae40cc86a4865ef70dc89abf79d5a37` and implementation commit
`a4f8570130d1fd33f802d391c6a196d1c5579278`. The branch explicitly reconciles Track A main before
implementation. Contracts are `working-capital-user-visible-v1` and
`working-capital-user-visible-enable-gate-v1`.

The 20-subject preview retains seven Phase 9.1D candidates and selects five lower-noise future
sentences: Inventory 3 and exact Trade AR 2. MU and TSLA Inventory are suppressed by compatible
cash-flow priority with no incremental Unknown resolution. Binding is 5 automatic and zero
manual/rejected/unresolved; selector, parity, semantic, causal, Unknown, and degraded-quality errors
are zero. Production AI/fallback/Telegram/Public Action/snapshot/DB/warnings are unchanged.

`WORKING_CAPITAL_USER_VISIBLE_MODE=OFF`. Inventory and exact Trade AR natural proof both remain
`NOT_OBSERVED`; each enablement decision is `NO_PENDING_NATURAL`. Do not treat preview evidence as
natural proof. The next valid change is a small family-specific enablement-only instruction after a
natural Phase 9.1D `LIVE_PASS`.

The KR investor-flow reconciliation repair is complete on instruction commit
`e9d7c73cf6f25b2423b55a6899465e86441316d1` and implementation commit
`47fc87e2a9189556a7206065fdb759f3603ce497`; Actions run `32480802390` passes Test/Lint. Run-31
packet `2026-08-21-kr-run-31-27d43ced72a0` proved that the visible foreign/institution/individual
tuple omitted material other-corporation and domestic-foreign flows. The repair keeps that public
tuple stable, reconciles all provider top-level participants internally, prevents institution
subclass double counting, records the 1d/5d/20d basis, and rejects unsafe absorber/leader prose.
Unsupported attribution falls from two to zero across 21/21 complete windows. Public Action
`0.4.5`, schema 4, supply scoring, task settings, Pilot, DB, and Production Assist are unchanged.
Natural confirmation remains pending and does not block Phase 9.1E architecture.

The independent night-futures publication telemetry P1 repair is implemented after explicitly
reconciling the preserved instruction branch with Phase 9.1D main. Instruction SHA is
`b7cf6a2f413e309bb637e524aeb7c1436e4c5b1b`; implementation SHA is
`d54f1102c02c9ff1c6a8ddd18fc40d1aea059caf`. The contracts are
`night-futures-attempt-archive-v1` and `night-futures-publication-telemetry-v1`.

Natural production attempts at 08:05/10/15/20 now archive complete returned NIGHT-date inventory
and per-product rejection/readiness through an isolated best-effort writer. A detached observer runs
at 08:45 and 09:15, stops after readiness, and has no production/DB/Telegram dependency. The 08:20
deadline, session basis, stale suppression, US primary/backup/fallback, and all user-visible outputs
are unchanged. Full validation is 1,337 passed; live provider calls and manual operations were zero.

The repair is deployed for observation, not policy change:
`P1_TELEMETRY_GAP = REPAIR_DEPLOYED_PENDING_NATURAL`,
`DEADLINE_VERDICT = DEADLINE_UNPROVEN`, and `FAIL_CLOSED_SAFETY = PASS`. Do not run the observer or
production task manually. Review natural stored evidence with the read-only script after the normal
09:15 horizon. Phase 9.1D natural metric-family proof and Phase 9.1E architecture remain parallel.

### Prior Phase 9.1C/9.1D Context

Phase 9.1C is closed retrospectively on
`codex/phase-9-1c-working-capital-shadow-consumption` as a linear descendant of Phase 9.1B final SHA
`2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6` and immutable work-instruction commit
`613d91d74d3a91c43ed61f98a13a2ca57b7a90ae`. Phase 9.1B remains
`working-capital-evidence-v1:canonical-core-v1`; Phase 9.1C adds the archive-only
`working-capital-shadow-consumption-v1` contract.

Inventory is total-inventory only. Exact trade and separate broad AR/AP remain distinct through raw
Fact, delta/YoY Fact, and structured relation identity. Prior-year comparison requires the same
issuer fiscal quarter and exact semantic, scope, currency/unit, entity, basis, and source version.
The 20-subject canonical implementation matches all Phase 9.1A metric coverage with zero newly blocked items:
160 selected reported Facts feed 44 delta, 44 balance YoY, 31 flow YoY Facts, and 53 eligible
relations. Arithmetic, provenance, and idempotency errors are zero.

The 9.1C immutable replay consumes seven current-formal relations: five Inventory and two exact
Trade AR. Automatic relation binding is 7/7; semantic, PIT/freshness, causal, arithmetic, repetition,
Unknown contradiction, and degraded-quality counts are zero. TSM is
`FORMAL_LAGGING_PROVISIONAL`; Korean Re remains N/A. Broad AR/AP and AP relations are excluded from
the initial canary because they did not add enough daily analytical value.

DSO, Inventory Days, DPO, CCC, and standard ROIC remain deferred. Open P0/material P1 are zero;
`PHASE_9_1D_READY = YES` with
`SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`.

Implementation SHA `aba64e85c34db620416ea9ee5cae36c0fe6b31d0` passed GitHub Actions run
`32454469417` Test/Lint and 1,324 local tests. The evidence generator is archive-only and has no
runtime database dependency.

Main and operating remain at `33c2f8be376b2cbb2961ecf9dc3c873715e0a034` with Phase 9.0E mode
`SELECTIVE_CURRENT_FORMAL_FULL_FCF`; API health passes and the four AI tasks plus KRX telemetry are
unchanged. Phase 9.1A/9.1B/9.1C user-visible diff is zero. Promotion is
`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`; no Telegram, task, Pilot, DB, or archive mutation occurred.

## Project Purpose

Thesis Monitor maintains an investment thesis from verified backend facts. The deterministic engine
owns official state. Codex adds a bounded interpretation of the same facts, and Telegram delivers one
integrated market-and-stock set only after validation. The system is research monitoring, not order
execution or an autonomous investment adviser.

## Current Versions

| Component | Contract |
|---|---|
| Branch | `main` operating through Phase 9.0E selective enablement; peer/KRX breadth ancestry excluded |
| Official assessment | Deterministic `ThesisAssessment` |
| AI mode | `shadow` |
| Analysis policy | `daily-review-v3.10` |
| Output schema | `4` |
| OHLCV structure | `ohlcv-structure-v2` |
| Investment Knowledge | `3.0` |
| Chart Knowledge | `1.0` |
| Pilot | `ai-assisted-pilot-v3`, persisted runtime KR 3/5 and US 3/5; US Day 3 is operationally counted but not human-reviewed here |
| Renderer | `ai-assisted-pilot-renderer-v3` |
| Public Action | `0.4.5`, operationId 20/20 |
| Production Assist | Disabled |
| Financial currency safety | Missing/empty is `unknown`; unsupported units are prose-denied |
| Security identity | `security-identity-v2` |
| Financial quality | `financial-quality-taint-v2` |
| KR financial lineage | `financial-lineage-v2` is present in operating code; recovered historical Facts remain archive-only pending separate data promotion |
| Delta-first rendering | `delta-first-rendering-v1` |
| Semantic decision hierarchy | `semantic-scope-and-decision-hierarchy-v1`, `decision-material-delta-v1` |
| Valuation context wording | `valuation-context-wording-v1` |
| Industry reasoning | `industry-specific-reasoning-v1` |
| Runtime packet completeness | current-price RR preflight v1; 2026-08-18 natural live path PASS |
| Current price context | `current-price-context-v1` |
| Runtime specificity | `runtime-message-specificity-v2` |
| Runtime reasoning ownership | `runtime-reasoning-ownership-v1` |
| Business numeric ownership | `numeric-summary-ownership-v1` |
| Typed template skeleton | `typed-template-skeleton-v1` |
| Runtime quality | `runtime-message-quality-v1`, receipt `runtime-message-quality-receipt-v2` |
| Night futures | `night-futures-session-basis-v1` CLOSED retrospective; holiday-aware preceding DAY lookup operating shadow, natural proof pending |
| Cash-flow canonical core | `cash-flow-capital-efficiency-v1`, selective internal Facts only |
| Cash-flow consumption | `cash-flow-shadow-consumption-v1` plus `cash-flow-user-visible-v1`; selective pending natural proof |
| Cash-flow runtime canary | `cash-flow-runtime-shadow-canary-v1`, natural US LIVE PASS |
| Baseline cash-flow consistency | `baseline-cash-flow-claim-consistency-v1`, retrospective closed |
| Cash-flow kill switch | `CASH_FLOW_USER_VISIBLE_MODE`; invalid/default OFF |
| Working-capital evidence | `working-capital-evidence-v1`; 9.1B canonical core implemented shadow |
| Working-capital consumption | `working-capital-shadow-consumption-v1`; retrospective PASS, 9.1D selective canary ready |
| Working-capital user-visible | `working-capital-user-visible-v1`; Inventory implemented/ready, exact Trade AR OFF pending proof |

## Phase 8.3 Final State

The operating checkout now contains Phase 8.5.4 and remains unchanged with respect to Phase 8.3.
Phase 8.3 is
finalized as archive-only `SELECTIVE_OPTIONAL_CONTEXT` and excludes KRX implementation ancestry. Its
clean lineage starts from
`codex/integration-phase-8-3-peer-only`, which reconstructs the peer contract from operating main.
The original Phase 8.3 branch still contains KRX Git ancestry but no required KRX runtime import;
see [BRANCH_DEPENDENCY.md](BRANCH_DEPENDENCY.md).

Peer provider policy is `FREE_ONLY`. Paid/institutional providers and commercial inquiries are
`CLOSED_BY_POLICY`; earlier research remains reference history. Historical peer point-in-time data
is deferred, and forward consensus was not pursued after the trailing value gate.

The 2026-08-18 POC measured one `MEDIUM+` state among 20 active stocks: 5.0% raw and 6.67% among 15
economically meaningful subjects. KR is 0/7. US is 1/13 overall and 1/8 meaningful. TSLA alone has
nine exact automotive candidates and three positive/current PER issuers. Broad Technology, Media
and semiconductor groups remain `LOW`; MU does not receive a memory comparison from generic
semiconductor candidates. RXRX and HPC/SaaS/holding frameworks remain correctly suppressed or
not meaningful. TSM/SKHY ADR basis remains unsafe.

The original full Preview added one sentence inside TSLA's existing Valuation section, increased
that message 8.34%, created no section, and left the other ten representative messages
character-identical. The final wording calls the sample a same-automotive-classification `기초
비교군`, retains the same canonical numbers, and explicitly says business-model and growth-
expectation differences limit direct peer-premium interpretation. The final targeted replay is
1,319 to 1,448 characters, or +9.78%; the other ten messages remain unchanged.

The Phase 8.3 contract and selection/safety tooling pass, but 263 read-only requests produced one
visible `MEDIUM` subject. Broad runtime value is therefore `LOW_ROI`; daily broad collection,
provider expansion, forward consensus, historical PIT and coverage-driven taxonomy widening stop.
The engine, validators, audit artifacts and clean peer-only branch remain available for naturally
qualifying MEDIUM/HIGH contexts. This is not integrated, deployed or active operating behavior.

The next state is `WAIT_FOR_NEXT_NATURAL_US_KR_PROOF`. Do not start a new feature before reviewing the
next natural messages. A critical failure takes priority as a targeted repair; otherwise the default
candidate is Cash Flow / Capital Efficiency Enrichment because OCF, CAPEX, FCF, ROIC, inventory,
working capital, cash conversion and segment economics remain more persistent decision gaps than
peer coverage.

Resolve the deployed commit with `git rev-parse HEAD`; a file inside a commit cannot contain that
commit's own final hash. The machine-readable state records `HEAD`, the promoted code SHA, and the
last verified base separately.

## Architecture

```text
Data providers
  -> deterministic normalization, validation, and calculation
  -> official ThesisAssessment
  -> immutable AI Review packet
  -> per-packet claim UUID, lease, flock, and fencing
  -> Investment Knowledge v3 + Chart Knowledge v1
  -> Codex structured review
  -> deterministic numeric-fact binding and canonical formatting
  -> schema, fact, semantic, routing, and grounding validator
  -> integrated market + stock renderer
  -> one AI-assisted Telegram set
     OR one deterministic fallback set
  -> exact immutable archive
```

See [AI_ASSISTED_MONITORING.md](architecture/AI_ASSISTED_MONITORING.md) for ownership boundaries.

## Roles

### Custom GPT

Custom GPT provides interactive initial research and monitoring using Investment Knowledge v3 and
the public Action contract. The repository upload artifact must remain byte-identical to the
canonical Investment Knowledge. Custom GPT Instructions take precedence if a conflict is found.

### Deterministic Backend

The backend collects facts, verifies identity and provenance, calculates financial, valuation,
market, supply, and chart values, and persists the official assessment. It remains the source of
truth for status, warnings, invalidation, canonical numbers, and Telegram fallback content.

### Codex

Codex reads an immutable packet and routed Knowledge only. It connects verified facts into business,
valuation, price, supply, market-structure, and portfolio-transmission interpretations. It does not
browse, collect facts, calculate indicators, create targets, or mutate official state.

### Validator

The backend first resolves draft numeric fact references into canonical prose and schema-4 claims.
The validator then resolves every fact and prose path, enforces industry routing, rejects unsupported
numeric semantics, verifies exact display variants, and checks current claim and policy identity
before atomic promotion. Unknown semantic types and stale or absent facts fail closed.

### Telegram

Telegram is a delivery surface, not a source of truth. During Pilot, validated AI narrative is merged
with deterministic status and numbers. A session sends either the AI-assisted set or the stored
deterministic fallback, never both.
The renderer preserves validated prose and only assembles headings, ordering, escaping, and Telegram
length handling; user-facing terminology must be resolved before validation.

## Monitoring Lifecycle

Initial research establishes a thesis-version baseline. Daily monitoring evaluates only changes after
that baseline. A new thesis version creates a fresh baseline and cannot inherit prior price-state
transitions as today's delta. Fingerprints and warning lifecycles remain deterministic.

```text
Initial research -> baseline -> daily delta -> deterministic assessment -> optional AI interpretation
```

Every final assessment also stores `monitoring-state-v1` under `price_context`: current price
structure, registered-rule lifecycle, supply, valuation, peer availability, the previous final state,
and deterministic delta. This state evolves even when the official business thesis is unchanged.
See [MONITORING_STATE_LIFECYCLE.md](architecture/MONITORING_STATE_LIFECYCLE.md).

## Dual Knowledge

- [Investment Knowledge v3](knowledge/investment-thesis-analysis-monitoring-knowledge-v3.md) governs
  business, industry, earnings, valuation, expectations, macro, risk, and monitoring safety.
- [Chart Knowledge v1](knowledge/stock-chart-value-analysis-knowledge-v1.md) governs interpretation of
  backend-provided OHLCV structure, positioning, and new-observer versus holder context.
- The two documents stay separate. Chart examples never override Investment Knowledge safety or
  backend calculations.

Canonical precedence is:

```text
Backend verified fact/calculation
  > Investment Knowledge v3 safety
  > OHLCV Analyst validated output
  > Chart Knowledge interpretation
  > examples
```

## Industry Routing

Primary industry identity comes from verified company profile fields, not thesis keywords or daily
themes. Structured subtype may refine a broad industry. Themes, customer exposure, and macro links
are secondary. Ambiguous or uncovered profiles stay general/low confidence rather than being forced
into a specialized framework. Production code contains no ticker-specific classification override.

## Numeric Provenance

Every user-facing investment number must bind:

```text
backend fact -> fact_id -> field_path -> value/unit -> semantic_type
  -> exact text_ref -> exact displayed usage
```

The single semantic registry defines unit, labels, formatter, rounding, prose permission, and scope.
Unknown semantics fail closed. Same-number/different-meaning and cross-prose coverage are invalid.
Derived numbers are usable only when the backend has registered them as canonical facts.
Under `daily-review-v3.10`, Codex places `{{numeric:ref_id}}` and selects only the canonical fact,
field, and prose location. The backend owns the value, unit, semantic, source-aware label, display
format, and generated final claim. Legacy manual claims still validate, but the draft binding path is
the production contract. See [NUMERIC_PROVENANCE.md](architecture/NUMERIC_PROVENANCE.md).
Issuer earnings amounts never inherit security price currency. A missing or blank
`financial_currency` becomes `unknown`; the amount remains auditable but has no canonical display and
cannot bind into prose. A non-empty unsupported currency keeps its identity and is also prose-denied.
Currency-independent earnings percentages remain usable.
During Pilot, a market or stock with at least four prose-eligible anchors cannot pass with zero
numeric claims. Sparse packets remain exempt, and every used number still requires exact prose
grounding rather than a quota-driven list.

## OHLCV Structure

`ohlcv-structure-v2` calculates Wilder ATR14, Local-Pivot zones and boxes, an independent Major Swing
stream, tentative Elliott/Fibonacci context, structural invalidation, nearest-resistance risk/reward,
and internal chart state. Correctness constraints are documented in
[OHLCV_STRUCTURE_ENGINE.md](architecture/OHLCV_STRUCTURE_ENGINE.md).

The central boundaries are:

- Local Pivot is not Major Swing.
- Adjusted chart price is not unadjusted historical-valuation price.
- Chart invalidation is not thesis invalidation.
- Chart state is not a buy or sell command.

## Market Intelligence

`daily-review-v3.10` retains deterministic numeric binding and adds relational stock reasoning,
canonical label ownership, lineage-exact financial eligibility, and authoritative security identity.
Verified market facts become selected changes, market structure, verified
portfolio transmission, and next confirmation. Market context may be a tailwind or headwind but never
becomes company fundamental confirmation. Rates, FX, oil, sectors, and flows use distinct semantic
contracts. Details are in [MARKET_INTELLIGENCE.md](architecture/MARKET_INTELLIGENCE.md).

## Stateful Price And Peer Context

Registered thesis price rules remain immutable history. The shared deterministic
`current-price-context-v1` selector first uses current Strong/Medium dynamic zones, current-price
RR/invalidation and chart state, then only a still-relevant registered lifecycle. It calculates
nothing. A crossed confirmation is history, never a future trigger or automatically promoted support.

Peer valuation is deterministic and fail-closed. Operating code only uses same-date active monitored
assessments and still has no qualifying state. The free-source experimental path extends candidate
discovery without changing operating monitoring state. At least three comparable independent
issuers are required and the median is primary. Broad sector samples remain audit-only. See
[PEER_VALUATION.md](architecture/PEER_VALUATION.md). The free-source POC architecture and reports
remain on the preserved `codex/phase-8-3-finalization` experimental branch.

## Pilot Architecture

Pilot v3 activated at KR 0/5 and US 0/5; the persisted runtime count is KR 3/5 and US 3/5. The
2026-08-16 US session remains an exactly-once operational success but failed human-quality review.
The natural KR
packet `2026-08-16-kr-run-21-049f367f0274` is operationally counted exactly once as Day 3/5, while
its human-quality status is `failed`. Neither packet is currently eligible
as Production Assist evidence. The required task
contract is policy v3.10/schema 4/structure v2. A successful day requires Codex completion, validation
pass, complete AI-assisted delivery, required artifact verification, and a verified atomic
`archive-complete.json` marker. Only then is success recorded. Archive-only recovery reuses the
persisted payload without resending Telegram, and packet/date idempotency prevents duplicate counts.
Fallback days do not increment the counter. Earlier
Pilot cohorts remain history and are never rewritten.

The natural US packet `2026-08-17-us-run-22-217ce9f324b9` passed the operating validator, delivered
14/14, archived 13 required artifacts with `archive-complete.json`, and appears exactly once in Pilot
state. It advanced the operational US count to Day 3/5. Phase 8 did not review its investment-message
quality and does not mark it as Production Assist evidence.

The next natural KR packet `2026-08-17-kr-run-23-378ee562573e` was rejected before AI delivery
because POSCO Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis lacked the required
current-price RR Fact and numeric path. Rejected AI sends were zero and deterministic fallback
eligibility was preserved; the deterministic fallback later sent 8/8 at 17:10 KST. No completed AI
delivery or AI archive marker was recorded, so runtime remains KR 3/5 and US 3/5. This is a separate
packet/numeric-path and natural-live gap, not a Phase 8 retrospective mutation.

## Phase 8 Market Cross-Section

The experimental branch adds `market-cross-section-v1` without registering a new production provider.
Massive free-plan live probing confirms full US grouped daily and paginated reference access. The
2026-08-14 sample produced 5,461 eligible security-level rows after deterministic filtering and
same-ticker previous adjusted-close validation. Massive remains shadow until 08:05 KST completeness is
observed over normal weekday sessions.

Kiwoom OpenAPI+ documentation exposes multi-symbol and industry-index/change primitives, but there is
no configured Windows market gateway or KOA-verified production TR evidence. The provider therefore
remains `bridge_shadow` and rejects canonical collection unless efficient market-wide capability and
universe semantics are explicitly SUPPORTED. KRX Open API is approved but not yet integrated and
remains the intended primary.
See [MARKET_CROSS_SECTION.md](architecture/MARKET_CROSS_SECTION.md) and the
[capability report](reports/20260817-phase8-massive-kiwoom-capability.md).

## Phase 8.1 KR Financial Lineage

The experimental Phase 8.1 branch changes new formal OpenDART collection to the full-financial-
statement API and persists exact field occurrences under `financial-lineage-v2`. Filing period,
amount period, comparison period, CFS/OFS basis, account, source type, currency, and correction
identity remain distinct. Direct amounts can remain usable when only a growth comparison is unsafe.

The immutable operating DB copy predates this contract: its active KR cross-section has no v2 rows
and retains `fs_div=unknown` for most latest formal filings. Phase 8.1 does not infer or backfill those
rows. It records 60 persisted source-value cells across the requested 119-cell matrix and zero safe
historical v2 promotions. SK hynix denied earnings and dependent valuation remain denied.

Massive remains shadow-only. The adjusted grouped volume is explicitly audit-only because split
adjustment can produce decimal volume, and `close * adjusted volume` is not official turnover.
Reference metadata may be reused for one trading day. Exact 08:05 KST readiness remains
`NOT_YET_OBSERVED`; the normal-day 3-5 session telemetry requirement is still open. See
[the Phase 8.1 financial report](reports/20260817-phase8-1-kr-financial-lineage-validation.md) and
[Massive readiness report](reports/20260817-massive-0805-shadow-readiness.md).

## Phase 8.1.1 Authoritative Financial Recovery

Phase 8.1.1 supplies the missing official source rows without touching production history. It reads a
consistent operating-DB copy, discovers the latest formal filing and correction chain, re-requests
both `fnlttSinglAcntAll` CFS and OFS scopes, and stores sanitized raw responses in an ignored cache.
The field selector uses exact taxonomy/account identity first, rejects multiple occurrences, and
uses OFS only when that field has no CFS occurrence. Current and prior-year quarter occurrences are
separate canonical lineages; growth is available only when basis, account, duration, source type,
and currency match.

The seven active KR tickers returned 1,818 CFS and 1,291 OFS rows from seven latest formal filings.
The archive-only cross-section recovered 37 safe direct Facts: 17 income-statement amounts, five
operating margins, six inventory Facts, plus balance-sheet fields. Seventeen same-quarter YoY Facts
passed exact comparison lineage and three remained withheld. SK hynix's revenue, operating income,
and net income remain denied because the existing critical profitability conflict was not resolved
merely by finding a formal source row.

Interim OCF entered XBRL fallback for all seven filings because its structured column does not prove
single-quarter versus cumulative duration. No XBRL occurrence had a unique exact period, unit, and
statement-basis match, so OCF promotion is zero. Twenty-eight exact PPE/intangible CAPEX component
candidates remain audit-only and none are aggregated; FCF remains unavailable. The cold-cache run
used 29 provider calls. Final reproducibility reused seven XBRL archives and made 22 calls. The five
representative archive-only messages all pass automatic numeric binding with no manual, rejected,
or formatting result. Human quality remains pending Work review.

See the [readiness report](reports/20260817-phase8-1-1-authoritative-financial-recovery.md),
[full audit](reports/20260817-phase8-1-1-authoritative-financial-recovery-audit.json), and
[persisted Before / recovered After Preview](reports/20260817-phase8-1-1-kr-financial-preview.md).
No main merge, operating DB write, Telegram send, assessment rewrite, archive rewrite, or Pilot
mutation occurred.

## Phase 8.1.2 Human Quality Review

Phase 8.1.2 preserves the engineering result but places investment-message quality on HOLD. Across
Samsung, POSCO Holdings, Hyundai Glovis, Korean Re, and SK hynix, 17 of 25 message-eligible recovered
Facts are used with numeric provenance and no unsafe leakage. The portfolio score is 7.4/20.

The limiting evidence is structural: each archived AFTER is a financial-only recovery payload, not
a complete runtime-rendered stock message. It does not preserve the price, supply, valuation,
observer/holder, Unknown, or next-check sections needed to judge relational investment analysis.
Data Recovery and Safety are PASS; Investment Message Quality and main readiness are HOLD.
Production Assist evidence eligibility remains false. See the
[human review](reports/20260817-phase8-1-2-kr-financial-human-review.md) and
[verbatim Preview](reports/20260817-phase8-1-2-kr-before-after-preview.md). At that point the
recommended order was Phase 8.4 then Phase 8.5, both of which are now represented by later sections.

## Phase 8.4 Delta-First Full Messages

Phase 8.4 closes the financial-only evidence gap on
`codex/phase-8-4-delta-first-integrated-renderer`. Using the same immutable KR Day 3 context and the
Phase 8.1.1 recovery artifact, it produces five complete schema-4 stock reviews and renders them
through the existing production stock renderer. A deterministic materiality plan puts grounded
supply or price evidence first when the packet records that transition; on unchanged days it states
that no material event occurred and moves to current decision relevance. Redundant business and
priority-watch display sections are suppressed when their evidence is already integrated into the
core, next check, and unknown.

The archive-only set has 82 automatic bindings, zero manual/rejected/formatter/unresolved results,
nine valid occurrence-bound valuation interpretations, and no SK hynix denied earnings or PE
leakage. The full validator and runtime receipt pass with zero errors; final-language, zone, supply,
observer/holder, and repeat checks also pass. The five messages are 11.5% shorter by character and
23.3% shorter by section than their immutable full-message baseline. The review score is a
provisional 16.6/20, but the authoritative status remains `pending_work_human_review` and Production
Assist evidence eligibility is false. See [the exact Preview](reports/20260817-phase8-4-delta-first-full-preview.md),
[human-quality evidence](reports/20260817-phase8-4-human-quality-review.md), and
[the rendering contract](architecture/DELTA_FIRST_RENDERING.md). No main merge, deployment,
Telegram send, provider call, operating mutation, or Pilot mutation occurred.

## Phase 8.4.1 Semantic And Decision Hardening

Phase 8.4.1 on `codex/phase-8-4-1-semantic-decision-hardening` keeps the Phase 8.4 integrated
architecture and closes its four direct semantic blockers. Ordinary PER/PBR and own-history Facts
now carry listed-security scope, so company multiples cannot be rendered as memory, transport, or
materials segment multiples. Denied financial families are fenced across qualitative claims, while
an exact Fact-bound denial explanation remains allowed.

The deterministic decision hierarchy no longer promotes mild supply divergence solely because it
changed most recently. Samsung and Hyundai Glovis move earnings/valuation and entry relevance ahead
of supply; SK hynix correctly retains supply as the best available delta because earnings are
denied. Safe decision-band history is retained for Samsung PBR, Hyundai Glovis PER, and SK hynix PBR.
Samsung's extreme Q2 values classify `VALID_AND_COHERENT` from exact CFS account, period, currency,
comparison, and formula checks; the audit makes no external plausibility guess.

The five corrected reviews use 86 automatic bindings and 12 typed valuation occurrences. Full
schema validation and the runtime receipt pass with no final-language or template errors. Average
characters rise 4.2% from Phase 8.4 while lines fall 1.3%. Work directly scored Samsung 17, POSCO
16, Hyundai Glovis 18, Korean Re 16, and SK hynix 17, averaging 16.8/20. It accepted the integrated
architecture and identified one follow-up contradiction in valuation context wording. Production
Assist evidence eligibility remains false. See the
[validation report](reports/20260817-phase8-4-1-semantic-decision-validation.md),
[semantic audit](reports/20260817-phase8-4-1-semantic-audit.md), and
[exact Preview](reports/20260817-phase8-4-1-semantic-decision-preview.md). Main remains unmerged and
no deployment, Telegram, provider, operating-state, or Pilot mutation occurred.

## Phase 8.4.1.1 Valuation Context Finalization

Phase 8.4.1.1 closes that follow-up on
`codex/phase-8-4-1-1-valuation-context-finalization`. The old fixed peer-gap fallback ignored whether
own-history context was already visible and could say “current multiple only” beside a historical
percentile. `valuation-context-wording-v1` now records current, history, peer, and forward
availability separately from actual use and selects an auditable wording class.

Samsung, Hyundai Glovis, and SK hynix resolve to `CURRENT_PLUS_HISTORY`; POSCO resolves to
`CURRENT_ONLY` because safe history was not selected for the current decision; Korean Re resolves to
`CURRENT_ONLY` because no safe history is available. All five draft references agree with actual
numeric bindings. The binder accepts 86 automatic references, 12 typed valuation occurrences, and
five valuation-context references with zero rejection. Full validator and runtime receipt pass;
valuation-scope violations, denied echo, unsafe history, and after-message contradictions are zero.
Average characters rise 1.1% from Phase 8.4.1, with no line or section increase.

This completes the Phase 8.4 message-intelligence foundation. At Phase 8.4.1.1 completion, the exact
final Preview still required the user's merge decision and the retrospective sent no Telegram or
mutated no runtime state. The implementation was subsequently promoted with Phase 8.5.2 while
Production Assist remained OFF. See the
[final Preview](reports/20260817-phase8-4-1-1-final-preview.md) and
[Master Workflow v2](MASTER_WORKFLOW.md).

## Phase 8.5 Industry-Specific Investment Reasoning

Phase 8.5 on `codex/phase-8-5-industry-specific-reasoning` adds
`industry-specific-reasoning-v1` without changing Investment Knowledge, Chart Knowledge, schema 4,
or the Phase 8.4 renderer architecture. The contract routes from verified company taxonomy,
separates primary framework from secondary themes, records confidence and missing drivers, and
requires supporting Facts for causal claims. It rejects memory low-PER cheap claims, insurance
low-PBR cheap claims without ROE/capital, biotech PER forcing, EPC order-to-margin leaps, and
hyperscaler-theme promotion to company revenue.

Archive-only full messages pass both the full validator and runtime receipt for five KR and six US
representatives. KR binding has 86 automatic numeric references and 12 accepted industry references
with zero error; SK hynix denied earnings/PER leakage remains zero. The active immutable routing
audit covers 20 stocks: nine high-confidence specialized routes and eleven low-confidence general
fallbacks. MU and TSM remain broad `semiconductor`, while WULF remains `general`, because current
structured evidence does not prove the finer memory/foundry/HPC primary labels. Phase 8.5 is
therefore strong PARTIAL pending better taxonomy coverage and natural-live evidence. See the
[architecture](architecture/INDUSTRY_SPECIFIC_REASONING.md),
[audit](reports/20260817-phase8-5-industry-reasoning-audit.md),
[KR Preview](reports/20260817-phase8-5-kr-industry-reasoning-preview.md), and
[US Preview](reports/20260817-phase8-5-us-industry-reasoning-preview.md).

The separate natural KR packet `2026-08-17-kr-run-23-378ee562573e` rejected four stocks pre-send for
missing required current-price RR Facts/paths. Rejected AI sends were zero; deterministic fallback
eligibility was preserved and later sent 8/8 at 17:10 KST; Pilot stayed KR 3/5 and US 3/5. This is a
packet/numeric-path and natural-live gap, not a renderer or Phase 8.5 reasoning failure.

## Phase 8.5.1 Runtime Current-Price RR Repair

Phase 8.5.1 on `codex/phase-8-5-1-runtime-current-price-rr-repair` identifies the run-23 failure as
`CALCULATED_BUT_NOT_CANONICALIZED`. The runtime session helper treated 2026-08-17 as a regular KRX
weekday even though XKRX was closed for a substitute holiday. That made the valid 2026-08-14 chart
look stale. Monitoring state retained the calculated RR and required grounding, while stale-chart
Fact filtering correctly withheld its canonical Fact.

The repair uses XKRX/XNYS calendars to determine sessions and preceding completed sessions. It does
not change RR calculation, nearest-resistance selection, stale-data denial, grounding requirements,
the binder, validator, or renderer. Read-only run-23 reconstruction restores exact RR paths for
POSCO Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis; Samsung Electronics, Korean Re,
and SK hynix remain unavailable by contract. The original eight RR missing-path errors become zero.
See the
[root-cause report](reports/20260817-runtime-current-price-rr-root-cause.md),
[validation report](reports/20260817-runtime-current-price-rr-repair-validation.md), and
[run-23 replay](reports/20260817-runtime-current-price-rr-run23-replay.md).

## Phase 8.5.2 Operating Shadow Promotion

Phase 8.5.2 verified that the Phase 8.5.1 source is a linear 31-commit descendant of the prior main
and includes the required Phase 7.2.9.2, 8.0A, 8.1, 8.1.1, 8.1.2, 8.4, 8.4.1, 8.4.1.1, 8.5, and
8.5.1 implementation chain. `origin/main` and the clean operating checkout were fast-forwarded from
`aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` through code commit
`2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf` and final promotion commit
`a8ebb02753e28795f36dbf72c9deb3520f75ed44`. GitHub Actions run `32023730416` passed Test and Lint.

The API LaunchAgent was restarted from the configured operating checkout; `/health` returned
`ok`, US AI Review health remained valid, and KR health correctly preserved the rejected natural
run-23 state rather than rewriting it. Operating smoke tests passed 89/89. The four Codex Scheduled
Tasks remain ACTIVE at 08:15/08:30/16:15/16:55 KST, use GPT-5.6 Sol/high, policy v3.10/schema 4,
and target the same operating checkout. No Scheduled Task was manually run. The deterministic US/KR
and fallback LaunchAgents also target that checkout and report last exit code zero.

This promotion sent no Telegram, changed no Pilot state, performed no DB migration, and did not
enable Production Assist. AI mode remains shadow. Natural Live Validation and the RR path remain
OPEN/PARTIAL until a later naturally scheduled session exercises the promoted code. See the
[release validation](reports/20260817-phase8-5-2-shadow-release-validation.md) and
[operating state](reports/20260817-operating-shadow-state.md) reports.

## Phase 8.5.3 Natural Live Message Hardening

The promoted code ran naturally on 2026-08-18. US packet
`2026-08-18-us-run-24-487c07bde4e1` and KR packet
`2026-08-18-kr-run-25-23b5e31dc20e` had zero numeric/semantic hard errors, but AI output failed the
unchanged runtime quality gate. Deterministic fallback delivered 14/14 US and 8/8 KR; Pilot remained
KR 3/5 and US 3/5. The KR packet carried complete canonical current-price RR paths for POSCO
Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis, so the RR runtime path is `LIVE PATH
PASS`. Full natural AI-assisted delivery remains PARTIAL.

Phase 8.5.3 adds `runtime-message-specificity-v1` to plan company evidence, industry driver,
decision point, Unknown, and next check before prose. It suppresses repeated methodology instead of
randomly paraphrasing it. Immutable replay reduces literal/skeleton duplicates from 3/7 to 0/0 in
US and 5/7 to 0/0 in KR with no gate relaxation and both full validators PASS.

Deterministic fallback now consumes `current-price-context-v1`, the same canonical current structure
available to AI packets. Dynamic support/resistance, current-price RR, chart invalidation/state, and
registered lifecycle are selected without renderer calculation. Nine crossed confirmations that had
been rendered as future triggers fall to zero; fake RR and automatic support promotion remain zero.
See the [root-cause report](reports/20260818-phase8-5-3-natural-live-message-root-cause.md),
[validation report](reports/20260818-phase8-5-3-natural-live-message-validation.md),
[AI Preview](reports/20260818-phase8-5-3-ai-natural-live-hardening-preview.md), and
[fallback Preview](reports/20260818-phase8-5-3-fallback-price-parity-preview.md).

This evidence is archive-only. It sent no Telegram, ran no Scheduled Task, changed no Pilot/DB/
assessment/archive state. Phase 8.5.3.1 subsequently completed the final language/dedup hardening
and promoted the full chain. A natural AI-assisted US/KR delivery is still required. KRX Open API is
approved but not integrated; Phase 8.2A becomes the next analytical infrastructure task after this
live blocker is cleared.

## Phase 8.5.3.1 Language/Dedup And Shadow Promotion

The 2026-08-18 immutable packets were replayed with no new Facts or provider calls. US Korean
object-particle errors fell from six to zero; the KR malformed actor-flow phrases fell from two to
zero and incomplete predicates from one to zero. Exact watch/next overlap fell from 13 US stocks to
zero. The same current-price RR Fact had appeared three times in six KR messages; exact RR is now
owned by price positioning and the three-or-more count is zero. Both full validators, runtime
quality, final language, fallback parity, and denied-Fact controls PASS.

Implementation commit `e166aaf6a4c13f9009a3885737d3b48e34c895d5` passed exact-SHA GitHub
Actions run `32122804278` Test/Lint and was fast-forwarded to main and the clean operating shadow
checkout. The API was restarted and `/health` passed. US/KR AI health passed, operating focused
tests passed 154/154, and all four Codex automations remain ACTIVE at
08:15/08:30/16:15/16:55 KST on the operating checkout. No automation was manually run; Telegram,
Pilot, DB, assessment, and archive mutations were zero. Production Assist remains OFF and AI mode
remains shadow. See the [validation report](reports/20260818-phase8-5-3-1-language-dedup-validation.md),
[Preview](reports/20260818-phase8-5-3-1-language-dedup-preview.md), and
[promotion report](reports/20260818-phase8-5-3-1-shadow-promotion.md).

## Phase 8.5.3.2 Valuation Label Repair

RXRX's immutable valuation sentence contained valid values and typed provenance but displayed both
the current PBR `1.82x` and five-year historical median `3.28x` as `역사적 PBR`. The registry had
collapsed multiple comparison roles into one display label. `valuation-comparison-label-v1` now
retains the role from `field_path`, produces `현재 PBR`, `역사적 PBR 중앙값`, and
`PBR 역사적 백분위`, and rejects same-label/different-role collisions. RXRX and one additional
WULF legacy occurrence are repaired; portfolio collisions after replay are zero. Biotech
interpretation remains cash-runway/pipeline/milestone/dilution first.

Implementation `b3ad1ea82bdbd3fe003831d449b0dcaa7c6a2da2` passed GitHub Actions run
`32126079970`, full `1043` tests, API health, and 74 operating focused tests before targeted shadow
promotion. Telegram, Scheduled Task, Pilot, and Production Assist mutations were zero. See the
[validation](reports/20260818-phase8-5-3-2-rxrx-valuation-label-validation.md),
[Preview](reports/20260818-phase8-5-3-2-rxrx-valuation-label-preview.md), and
[audit](reports/20260818-phase8-5-3-2-valuation-label-audit.json).

## Phase 8.5.4 Natural Live Targeted Repair

Natural US packet `2026-08-19-us-run-26-cd80a8e4d373` produced no AI send. The deterministic
fallback delivered 14/14 messages with no duplicate and preserved the archive/receipt path. AI was
rejected for RXRX/WULF current-PBR semantic ownership and CORZ typed valuation occurrence errors.
This operational delivery is successful, but natural AI-assisted delivery and human/canonical
quality remain `PARTIAL`.

The market packet also exposed a canonical source-meaning error. KOSPI200 and KOSDAQ150 night
changes were calculated from NIGHT and DAY rows with the same KRX `BAS_DD`. KRX assigns the
overnight trading day by its T+1 06:00 end, so that same-date DAY close occurs later and is not the
reference session. The required 2026-08-19 NIGHT row was unavailable and the exact original raw
response was not archived. Retrospective output therefore suppresses both figures as
`UNAVAILABLE_BY_CONTRACT`; the user's approximate observation is not hard-coded.

`night-futures-session-basis-v1` now requires verified NIGHT identity, preceding DAY reference,
contract/date coherence, both prices, source record identifiers and payload SHA. Unknown session,
reference, contract, date or source evidence fails closed. Provider change fields are not trusted
without verified comparison semantics.

Visible current PBR now has one owner, `fields.price_to_book`; historical median and percentile
retain their historical semantics. The CORZ earnings-quality phrase receives exact typed coverage
without restoring unsafe earnings or book multiples. Fallback valuation caution is generated from
the metrics actually rendered, closing the GOOGL/HUT/RXRX/WULF/CORZ parity controls. Overlapping
selected support/resistance zones make RR unavailable; HUT 0.66x and WULF 0.42x are suppressed in
archive-only replay without moving the zones.

The repaired immutable replay has zero numeric-binding, typed-valuation and full-validator errors,
and `runtime-message-quality-v1` passes. Its validation sent no Telegram, ran no Scheduled Task, and
mutated no Pilot/DB/archive. It is now promoted to operating shadow; natural proof is still pending.
See the [root-cause report](reports/20260819-run26-natural-live-root-cause.md),
[night audit](reports/20260819-night-futures-session-basis-audit.md),
[validation repair](reports/20260819-run26-ai-validation-repair.md),
[fallback parity](reports/20260819-fallback-valuation-context-parity.md), and
[archive-only Preview](reports/20260819-run26-targeted-repair-preview.md). Full test and safety
results are in the [Phase 8.5.4 validation report](reports/20260819-phase8-5-4-validation.md).

## Phase 8.5.4.1 Operating Shadow Promotion

Validated source `3a6547e394452e6e1b986a8193f56c98fd07ef89` was fast-forwarded to `main` and
the clean operating checkout. The Thesis Monitor API restarted from that checkout, `/health`
passed, and 430 read-only operating smoke tests passed. All four Codex Scheduled Tasks remain ACTIVE
at 08:15/08:30/16:15/16:55 KST, keep the operating checkout, policy `daily-review-v3.10`, schema 4,
and received no configuration change or manual execution.

The live KRX preflight queried 2026-08-19 through 2026-08-13. The expected 2026-08-19 payload was
empty, while 2026-08-18 had rows but no verified reference under the current strict collector. Both
KOSPI200 and KOSDAQ150 are therefore live-unavailable and suppressed. Targeted raw checks confirm
matching 2026-09 contracts for the safe 2026-08-18 NIGHT -> 2026-08-14 DAY candidate, but the
collector cannot bridge that holiday gap. A stale 2026-08-14 NIGHT -> 2026-08-13 DAY pair passes the
ordinary path. This availability debt cannot reopen same-date promotion.

Visible current-PBR ownership currently redirects a history `current_value` to the canonical base
Fact only when the values are equal. An explicit `source_current_fact_id` lineage edge does not yet
exist and is recorded as `OPEN_LOW_PRIORITY`; this does not weaken the fail-closed binder gate.
See the [promotion](reports/20260819-phase8-5-4-1-shadow-promotion.md),
[preflight](reports/20260819-night-futures-live-readiness-preflight.md),
[operating state](reports/20260819-phase8-5-4-1-operating-shadow-state.md), and
[smoke](reports/20260819-phase8-5-4-1-operating-smoke.md) reports.

## Phase 8.5.4.2 Night Futures Calendar Repair

The remaining collector failure was a calendar traversal bug, not missing provider history. Both
the parser and canonicalizer required `NIGHT BAS_DD - 1 calendar day`, so 2026-08-18 NIGHT looked for
2026-08-17 DAY and stopped even though XKRX marks 2026-08-17 as a holiday and the correct 2026-08-14
DAY rows were already within the bounded provider lookback.

Implementation `7e7ab5acee2176bc8a452115da19ac6e14d312ab` now uses one shared XKRX predecessor
function. It selects only the latest eligible earlier DAY session, then requires the same product,
contract and maturity. It does not reconnect an older contract after rollover. Provider raw change
is audit-only and must agree with the deterministic two-price calculation when present.

Historical replay and the live read-only probe both resolve:

| Instrument | NIGHT | DAY reference | Contract | Derived | Provider audit |
|---|---|---|---|---:|---:|
| KOSPI200 | 2026-08-18 1094.95 | 2026-08-14 1098.90 | `A0169000` | -3.95 / -0.35945036% | -3.95 match |
| KOSDAQ150 | 2026-08-18 1477.30 | 2026-08-14 1487.50 | `A0669000` | -10.20 / -0.68571429% | -10.20 match |

The 2026-08-19 provider response still has zero rows. These pairs are therefore historical/stale,
not current, and user-visible promotion remains zero. Operating smoke passed 494 tests after API
restart; `/health` passed; all four tasks remain ACTIVE and unchanged. Telegram, task runs, Pilot,
DB, archive and receipt mutations were all zero. See the
[repair](reports/20260819-night-futures-preceding-session-calendar-repair.md),
[holiday audit](reports/20260819-night-futures-holiday-traversal-audit.md),
[validation](reports/20260819-phase8-5-4-2-validation.md),
[promotion](reports/20260819-phase8-5-4-2-shadow-promotion.md), and
[operating state](reports/20260819-phase8-5-4-2-operating-state.md) reports.

## Phase 8.5.5 Natural Reasoning Ownership Repair

Natural KR packet `2026-08-19-kr-run-27-63a064e837ff` produced a rejected AI candidate and then
delivered deterministic fallback 8/8 exactly once. AI sent 0. The initial errors were one Korean Re
depositary-ratio false positive and unauthorized `chart_risk_reward` use by POSCO Holdings and
Hyundai Glovis. The bounded correction then failed runtime quality because two substantive
candidates and four sentence skeletons repeated across the portfolio.

Korean Re is canonical `verified_non_depositary` common stock. Its sentence said `합산비율 ... 확인`,
not ADR ratio. The old validator made the depositary qualifier optional and falsely matched the
insurance metric. Phase 8.5.5 requires explicit ADR/ADS/depositary wording and suppresses
depositary candidates before prose for domestic/non-depositary securities. Verified depositary
fixtures remain eligible.

Framework ownership now separates business/industry reasoning from price context.
`chart_risk_reward` is price context only; it never becomes steel or transport reasoning. POSCO
retains `steel_materials_valuation`, Hyundai Glovis retains `shipping_transport_valuation`, and
Korean Re retains `insurance_reinsurance_valuation`. Candidate plans expose owner, evidence,
decision role, specificity key and suppression reason under `runtime-reasoning-ownership-v1`.

The immutable replay binds 117 numeric references automatically with manual/rejected/unresolved 0,
has zero full-validator errors, and passes final language and receipt verification. Existing quality
thresholds remain unchanged. Substantive repeats fall 2 -> 0 and template skeletons 4 -> 0; average
stock-message length falls 2.34%. The actual fallback, dynamic price, RR overlap guard,
night-futures contract, archive, receipt and Pilot state were not modified.

See the [root cause](reports/20260819-run27-natural-reasoning-root-cause.md),
[ownership architecture](architecture/RUNTIME_REASONING_OWNERSHIP.md),
[repetition audit](reports/20260819-run27-repetition-audit.md),
[archive-only preview](reports/20260819-run27-repaired-ai-preview.md), and
[validation](reports/20260819-phase8-5-5-validation.md).

Implementation `2ac9091d2865727194d6cf5ae63c73fe0c1cc5e0` passed Actions run `32234428454`
Test/Lint, was fast-forwarded to main and operating, passed API health, and passed 276 operating
smoke tests. All four automations remain ACTIVE and unchanged. This is
`CLOSED_RETROSPECTIVE_PENDING_NATURAL`, not a natural AI-assisted PASS. Wait for the next natural
US/KR sessions. Cash Flow / Capital Efficiency remains pending.

## Phase 8.5.5.1 US Numeric Summary Ownership Repair

Natural US packet `2026-08-20-us-run-28-9024def294e6` passed numeric, semantic and final-language
validation, but the unchanged runtime quality gate rejected the AI candidate. AI sent 0;
deterministic fallback delivered 14/14 with pending 0. The fallback and exactly-once path remained
safe. The natural market packet also suppressed night futures because no latest completed session
pair was available, which is valid live fail-closed behavior rather than numeric exposure proof.

The remaining blocker came from three connected paths. The Daily Review policy required two
earnings anchors, so valuation-source TTM EPS and BVPS filled sparse `business_earnings` sections.
Those sections shared the portfolio scaffold `현재 확인된 핵심 숫자는`. Separately, every numerical
RR change was treated as material, producing ten standalone previous/current RR tuples. The old
text-only normalizer then grouped those tuples with WULF's economically different current-PBR to
historical-percentile relation.

`numeric-summary-ownership-v1` removes the numeric quota and gives business detail only to direct
earnings metrics; valuation-only denominators no longer fill the section, and a company-specific
Unknown is valid when business evidence is absent. `typed-template-skeleton-v1` combines text shape
with section, owner, numeric semantic type and comparison relation. Existing chart-transition flags,
not a new threshold, decide whether an RR delta renders. Six material transitions were integrated
with their price context and four non-material pairs were suppressed.

The archive-only replay has 149 automatic bindings, manual/rejected/unresolved 0, validator errors
0, and a verified PASS receipt. Template skeleton blockers fall 5 -> 0, generic numeric-summary
families 1 -> 0 and business ownership violations 9 -> 0. Substantive and methodology repetition
remain 0; observer/holder, specific next checks and specific Unknowns remain 13/13. Run-27 remains
PASS and average stock-message length falls 4.00%.

Implementation `c915d44e3080ad18c5a646932a51d77a4c15dc1a` passed Actions run `32319601429`
Test/Lint, was fast-forwarded to main and operating, passed API health and 291 operating smoke tests.
All four automations remain ACTIVE at 08:15/08:30/16:15/16:55 KST with no configuration change or
manual run. See the [root cause](reports/20260820-run28-us-numeric-summary-root-cause.md),
[typed audit](reports/20260820-run28-typed-repetition-audit.md),
[ownership audit](reports/20260820-run28-business-earnings-ownership-audit.md),
[archive-only Preview](reports/20260820-run28-repaired-ai-preview.md),
[validation](reports/20260820-phase8-5-5-1-validation.md), and
[promotion](reports/20260820-phase8-5-5-1-shadow-promotion.md).

This is `CLOSED_RETROSPECTIVE_PENDING_NATURAL`, not a natural AI-assisted PASS. Natural
AI-Assisted Delivery remains `PARTIAL`; Cash Flow / Capital Efficiency remains pending.

## Phase 8.5.5.2 KR Structured Field Repair

Natural KR packet `2026-08-20-kr-run-29-6e8809e1e944` passed numeric, semantic, and final-language
checks but failed runtime quality. AI sent 0 and deterministic fallback delivered 8/8 with pending
0. The immutable receipt identified canonical foreign/institution 1/5/20-day tuple shapes, exact
current RR duplicated between core and price, one common financial-basis sentence, and one generic
inventory/CAPEX-to-FCF/ROIC watch family.

`canonical-supply-flow-tuple-v1` now distinguishes stable structured rows from optional analytical
prose without hiding any eligible supply number. `numeric-primary-owner-v1` owns exact current RR in
`price_positioning.text` once; candidate normalization removes only a standalone or safe numeric-
list-tail secondary occurrence when one unambiguous price primary exists. Other forms remain
fail-closed. Generic warning/watch candidates are suppressed while existing company-specific
business prose, Unknowns, and next checks remain.

The archive-only replay has 112 automatic numeric bindings, manual/rejected/unresolved/formatting
failures 0, validator errors 0, runtime quality PASS, final language PASS, and verified receipt.
Substantive repetition falls 2 -> 0 and blocker skeletons 4 -> 0 under the repaired typed audit;
the three canonical supply tuple families are recorded as structural exceptions. Exact RR owner
violations fall 4 -> 0. Run-28 and run-27 remain PASS, and average stock-message length falls 3.19%.

LS ELECTRIC and Hanwha Aerospace remain fail-closed for share-basis-dependent valuation. Both have
inferred local KRX/common-stock records, but canonical identity is still `unknown`/unverified,
EPS security basis is unknown, and trailing PE/PBR basis is insufficient. No denominator was
recalculated or marked verified.

Phase Advancement Rule v1 classifies open safety/correctness as P0, bounded analysis-integrity
repairs as P1, and non-material quality/UX as P2. P0 open is 0 and the run-29 targeted P1 is closed
retrospectively with CI PASS, so `PHASE_9_0A_READY = YES`. This authorizes only a separate Phase 9.0A
Cash Flow / Capital Efficiency evidence-architecture task. Natural AI proof and KRX exact-slot
publication evidence continue in parallel; no Phase 9.0A implementation occurred here.

See the [root cause](reports/20260820-run29-kr-structured-repetition-root-cause.md),
[supply audit](reports/20260820-run29-structured-supply-tuple-audit.md),
[RR audit](reports/20260820-run29-rr-cross-section-ownership-audit.md),
[cash-conversion audit](reports/20260820-run29-industry-cash-conversion-specificity.md),
[basis audit](reports/20260820-kr-valuation-basis-caution-audit.md),
[archive-only Preview](reports/20260820-run29-repaired-ai-preview.md), and
[validation](reports/20260820-phase8-5-5-2-validation.md). The clean linear descendant passed
exact-SHA Actions Test/Lint, was fast-forwarded to `main` and the operating checkout, restarted on
`127.0.0.1:8766`, returned `/health` PASS, and passed 497 read-only operating smoke tests. Four
AI-review tasks remain ACTIVE at 08:15/08:30/16:15/16:55 with no configuration change or manual
execution. The KRX exact-slot LaunchAgent remains calendar-loaded for 08:05/16:05 with last exit 0
and user-visible integration disabled. See the
[promotion report](reports/20260820-phase8-5-5-2-shadow-promotion.md).

## Phase 9.0A Cash Flow / Capital Efficiency Evidence Architecture

Phase 9.0A is architecture-closed under `cash-flow-capital-efficiency-v1`; user-visible runtime
behavior changed by zero. The contract extends `financial-lineage-v2` rather than creating a second
truth store. Every raw fact carries period, entity/statement basis, currency/unit, source
occurrence, filing date, semantic mapping, source sign, and raw SHA. Every derived fact requires
input fact IDs and a formula.

The baseline backend FCF definition is OCF minus positive-magnitude PPE-only cash outflow.
Intangibles and capitalized software stay separate; total investing cash flow, acquisitions, and
securities purchases are excluded. Q2/Q3 standalone cash flow requires adjacent compatible YTD
subtraction. TTM requires prior FY plus current YTD less prior comparable YTD under the issuer's
fiscal calendar. No annualization, CFS/OFS mixing, currency mixing, or restatement mixing is
allowed.

The operating universe contains 20 active subjects, 7 KR and 13 US/foreign. Official SEC Company
Facts produced 12 direct OCF and 11 same-accession/period/unit OCF/PPE pairs. Stored Phase 8.1.1
OpenDART evidence retains exact CF tags for all seven KR subjects, but its unique period context is
unresolved, so KR OCF/CAPEX remain partial and FCF remains blocked. Korean Re is not applicable for
generic corporate FCF/CCC/ROIC. TSM demonstrates that issuer-level FCF can be eligible without an
ADR ratio, while security-level FCF/share, yield, and EV arithmetic remain blocked without verified
security and FX basis.

Raw inventory/trade AR/trade AP and balance deltas are the next working-capital layer. DSO,
inventory days, DPO, and CCC are deferred because safe average typed balances and purchases are not
available across the audited set. Standard ROIC is deferred because no verified excess-cash policy
exists; all cash is never treated as excess cash by default.

Open P0 and P1 are zero. `PHASE_9_0B_READY = YES` with scope
`SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`. The next major task is Phase 9.0B canonical core
implementation for eligible evidence, fail-closed elsewhere. It is not approval for user-visible
cash-flow output. Natural US/KR proof and KRX 08:05/16:05 telemetry continue in parallel. The
single download/copy artifact is the
[Phase 9.0A complete report bundle](reports/20260820-phase9-0a-complete-report-bundle.md).

## Phase 9.0B Canonical OCF / PPE-CAPEX / FCF Core

Phase 9.0B implements `cash-flow-capital-efficiency-v1` as an internal canonical/shadow core. It
does not change the daily packet, AI prompt, fallback, Telegram, Public Action 0.4.5, schema 4, or
database. The implementation extends the existing Fact lineage instead of creating a cash-flow
truth store.

Only reviewed SEC semantics can produce `operating_cash_flow` or
`ppe_capex_cash_outflow`. Generic investing outflow, acquisitions, securities, intangibles, and
capitalized software do not enter baseline CAPEX. PPE cash payments normalize to positive outflow
magnitude, and `free_cash_flow_ppe` is exact Decimal `OCF - PPE CAPEX`. Every FCF carries exactly
two input Fact IDs and matching period, currency/unit, entity scope, statement basis, and
source-document chain.

Cash-flow `Q2`/`Q3` filing labels remain YTD. QTD uses strict adjacent YTD subtraction and TTM uses
prior FY plus current YTD less prior comparable YTD. SEC comparative rows can carry the later
filing's `fy`; the canonicalizer therefore preserves fiscal context from the earliest official
occurrence for the same semantic/start/end/unit while selecting the latest filing value/version.
No calendar-year guess or annualization is used.

The 20-subject implementation reproduces Phase 9.0A exactly: OCF `12 eligible / 7 partial /
1 blocked`, PPE CAPEX `11 eligible / 6 partial / 2 blocked / 1 N/A`, and FCF `11 eligible /
8 blocked / 1 N/A`. The stored SEC audit contains 191 derived FCF Facts, all with complete lineage
and exact arithmetic. HUT has OCF but no accepted PPE CAPEX; SKHY has no accepted SEC OCF/PPE
semantic. Six KR non-financial subjects remain blocked on `period_context_unresolved`, and Korean
Re generic FCF is not applicable. The KR gap is classified `MEDIUM_COMPLEXITY_FOLLOWUP`.

Open P0 and P1 are zero. CCC and standard ROIC remain deferred. `PHASE_9_0C_READY = YES` with scope
`CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY`. Phase 9.0C may feed these Facts only into an
internal shadow packet and archive preview before any later user-visible decision. Natural US/KR
proof and KRX exact-slot telemetry continue independently. See the
[Phase 9.0B complete report bundle](reports/20260820-phase9-0b-complete-report-bundle.md).

## Phase 9.0C Cash Flow Shadow Consumption

Phase 9.0C consumes canonical cash-flow Facts only through an archive sidecar. It requires the
official filing date to be on or before replay cutoff, compares the primary period with the latest
formal and preliminary financial periods, and allows only same-type, same-duration, same-basis
comparisons. It creates sign-aware relations rather than percentage growth or good/bad scores.

Of 20 active subjects, 12 are consumption-eligible and 10 are materially rendered: nine full FCF
and HUT as OCF-only. TSM and WRD remain formal-lagging-provisional context-only. Six KR
non-financial subjects remain blocked on OpenDART period context, while Korean Re is not applicable
for generic enterprise FCF. No old safe period substitutes for a newer blocked or preliminary
period.

The archive preview automatically binds all 10 exact cash-flow numbers to canonical Fact IDs.
Manual, rejected, unresolved, semantic-error, future-fact, stale-as-current, management-FCF
mislabel, unsupported valuation, and KR numeric-injection counts are zero. Eight of 17 generic
cash-flow Unknowns resolve, eight remain valid, and one insurance Unknown is suppressed. Run-28
before/after and run-29 negative control pass runtime quality, final language, and receipts; no
candidate changes assessment or valuation state.

Open P0 and P1 are zero. `PHASE_9_0D_READY = YES` with scope
`SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY`. Phase 9.0D may attach the same context to natural
runtime only as a delivery-isolated canary. Telegram, fallback, Public Action 0.4.5, schema 4,
Scheduled Task prompts, database assessments, CCC, and standard ROIC remain unchanged. See the
[architecture](architecture/CASH_FLOW_SHADOW_CONSUMPTION.md) and
[Phase 9.0C complete report bundle](reports/20260820-phase9-0c-complete-report-bundle.md).

## Phase 9.0D Runtime Shadow Canary

Phase 9.0D is implemented from immutable instruction commit
`a24e4f2210f944fa7c43d8dbf8be1d1a8e652164`. The AI-review job launches a detached cash-flow
canary only after a terminal production delivery result. The canary uses the exact natural packet,
Phase 9.0B canonical Facts and Phase 9.0C consumption gates, then writes a separate immutable audit
namespace. It has no Telegram sender, fallback selector, Public Action, assessment, warning, Pilot
or DB mutation path.

Production isolation, idempotency, generation/validator/archive failure, fallback and duplicate
tests pass. Natural run-30 completed the canary with nine full-FCF, one OCF-only, two
formal-lagging-provisional and one blocked contexts, 10 automatic bindings, and zero production
influence. Runtime canary state is `LIVE_PASS_SELECTIVE_SUBSET`. See the
[Phase 9.0D complete report bundle](reports/20260820-phase9-0d-complete-report-bundle.md).

## Phase 9.0D.1 Baseline Consistency And Phase 9.0E Rollout

Phase 9.0D.1 suppresses unsupported current cash-flow baseline prose before enrichment. Phase 9.0E
then constructs one selected context for both AI and fallback and exposes one fiscal-period-labeled
PPE-only FCF number under business/earnings ownership. A different context, period, currency,
Fact ID, or baseline suppression identity fails before delivery.

The initial rollout is US/foreign SEC current-formal full FCF only. On run-30, CORZ, CRCL, GOOGL,
IBM, MU, RXRX, SNDK, TSLA, and WULF are selected. SNDK resolves one Unknown and TSLA suppresses
four legacy claim occurrences before canonical exposure. First-exposure fallback length increases
by 114.33 characters on average; identical later evidence is delta-suppressed.

The feature is enabled but not naturally proven. Use
[the kill-switch procedure](operations/CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md) for a Phase 9.0E P0.
Do not manually run the US task or send Telegram. The complete report is
[Phase 9.0E complete report](reports/20260821-phase9-0e-complete-report.md).

## Phase 9.1A Working-Capital Evidence Architecture

Phase 9.1A adds the read-only `working-capital-evidence-v1` architecture and deterministic audit
generator. It consumes official SEC Company Facts stored evidence and a bounded OpenDART CFS cache,
then emits point-in-time Inventory, exact trade AR/AP, separate broad AR/AP, revenue, COGS,
prior-year comparable pairs, and typed cross-growth relations. It does not enter runtime imports or
create user-visible facts.

Coverage across 20 active subjects is selective: total Inventory 11 eligible, exact trade AR 6,
broad AR 9, exact trade AP 8, and broad AP 10; one insurance subject is not applicable. Safe
relations cover AR/revenue 14, inventory/revenue 11, inventory/COGS 11, and AP/COGS 14. MU proves
non-calendar fiscal handling, TSM proves issuer-level foreign evidence, six KR non-financials prove
same-period CFS balance comparability, and Korean Re remains excluded.

Phase 9.1B implements that core with 160 selected reported Facts, 44 balance deltas, 44 balance YoY,
31 flow YoY Facts, and 53 eligible typed relations. All derived Facts and relations retain exact
input IDs; arithmetic, provenance, idempotency, and 9.1A coverage-regression errors are zero.

Phase 9.1C consumes the core only in archive shadow. PIT and latest-formal gates leave seven current
material contexts: Inventory for `000660`, `005490`, `005930`, `MU`, and `TSLA`; exact Trade AR for
`010120` and `086280`. TSM is context-only because the formal balance lags newer provisional
earnings. Insurance is N/A. Broad AR/AP, AP relations, and low-value industry contexts are omitted
from the proposed 9.1D canary.

The proposed next scope is
`SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`. It must remain delivery-independent and
cannot expose working-capital prose to Telegram without a later explicit decision. DSO, Inventory
Days, DPO, CCC, user-visible rendering, status mutation, and causality remain prohibited. Promotion
of the full 9.1A -> 9.1B -> 9.1C chain remains deferred until the separate KR natural-window review.

On 2026-08-15 the owning desktop environment verified all four local-project tasks, retained their
08:15/08:30/16:15/16:55 schedules, and migrated their exact prompts to v3.10 with
`security-identity-v2` and `financial-quality-taint-v2`. All four are ACTIVE,
target the live local operating checkout, use GPT-5.6 Sol with high reasoning, and preserve the US
Primary 300-second readiness wait. No duplicate standalone task was created.

| Market | Primary | Backup | Fallback deadline |
|---|---:|---:|---:|
| US | 08:15 | 08:30 | 08:40 |
| KR | 16:15 | 16:55 | 17:10 |

The US deterministic run and first KRX fetch start at 08:05. KRX-only retries run at 08:10, 08:15,
and 08:20; the packet then proceeds with both contracts, a verified partial pair plus caution, or a
compact unavailable caution. The 08:15 primary may poll backend packet readiness for five minutes.
Detailed recovery and single-delivery rules are in
[AI_ASSISTED_PILOT.md](operations/AI_ASSISTED_PILOT.md).

The 2026-08-14 US v3.6 output had zero numeric claims and its initial Telegram delivery failed. A
manual retry sent the messages before the v3.7 policy was adopted, so delivery cannot be undone; the
session is retained as a failed-quality live sample and does not count toward Pilot totals.

The 2026-08-15 US session completed under v3.8 before the v3.9 deployment: validator PASS, 14/14
AI-assisted messages sent, and archive completion. Runtime state therefore counts it as US Day 1/5.

The natural 2026-08-16 KR v3.10 packet `2026-08-16-kr-run-21-049f367f0274` passed validation,
delivered the market plus all seven active stocks 8/8, verified 13 required archive artifacts, and
wrote `archive-complete.json` before the exactly-once Pilot record. Runtime state therefore counts it
as KR Day 3/5. Work's direct review failed the persisted payload because it contains six Korean
numeric-postposition defects, supply-direction claims without matching visible actor/horizon numbers,
a repeated stock core-judgment template, financial amounts without a user-visible period basis, and
valuation conclusions without sufficient historical or peer evidence. The operational count is not
rewritten, but Production Assist evidence eligibility remains false. See
[the operational reconciliation](reports/20260816-third-natural-kr-v310-operational-reconciliation.md)
and [the Work human review](reports/20260816-third-natural-kr-v310-work-human-review.md), alongside
[the exact persisted preview](reports/20260816-third-natural-kr-v310-telegram-preview.md).
The later v3.9 same-packet retrospective was archive-only and did not change that count or resend it.
The `e2c9290` plain-language preview was also unsent experimental evidence. Broad renderer-side word
replacement was removed because it crossed the post-validation semantic boundary; the Daily Review
Skill remains responsible for avoiding internal analysis jargon in authored user prose.

The natural 2026-08-15 KR v3.9 Scheduled Task completed packet
`2026-08-15-kr-run-19-919a670464b4`: validator PASS, the market plus seven active stocks delivered
8/8, all required archive hashes verified, and `archive-complete.json` was written before the packet
was recorded exactly once. Runtime state therefore counts it as KR Day 2/5. Experimental v3.10
retrospectives did not send this payload or mutate the count. At that time a Preview label such as
KR Pilot 3/5 was only the next-success candidate; the later natural KR session documented above is
the event that actually advanced runtime state.

Phase 7.2 production integration then deployed code commit `5f3aa5c37848092bcccf74bbc917604bebae33d4`.
Authoritative SEC identity remediation changed exactly CORZ, GOOGL, HUT, IBM, SKHY, and WULF; a
second pass was a six-of-six no-op. An isolated post-remediation US packet passed binder and full
validation with 161 automatic bindings and no manual claims. GOOGL's clean valuation lineage was
restored, while SKHY remained an ADS with ratio 0.1 and its unverified current-security multiples
stayed withheld. Deployment and retrospective validation did not add a Pilot count.

The first natural v3.10 session was US packet `2026-08-16-us-run-20-6c15d0003955`. The automated
pipeline passed after one correction cycle, delivered 14/14 AI-assisted messages, verified 13/13
required archive hashes, wrote the completion marker before state, and recorded the packet exactly
once. Runtime therefore advanced US to 2/5. The required human message review failed because CRCL's
confirmation transition contradicted its packet delta, SKHY's prose incorrectly described its
verified ADS identity as unverified, and all 13 US stocks repeated a KR-style investor-flow horizon
frame. TSM and WRD also resolved to `unknown` identity despite the deployment cross-section recording
`verified_depositary`; their unsafe multiples remained withheld. No manual count correction was
made. See [the Live validation report](reports/20260816-first-natural-v310-live-validation.md).

Phase 7.2.7 keeps that operational count unchanged and adds deterministic validation for confirmation
transition direction, security identity versus valuation basis, and market-aware supply routing.
Its US correction passed automated gates, but human review found additional blocking label, zone,
identity-prose, RR comparison, and sentence-quality issues. Its KR regression also reused a v3.9
artifact from a closed 2026-08-15 KR session, so it is not current financial-quality acceptance
evidence. The report and Previews remain preserved as failed-review evidence.

Phase 7.2.8 supersedes that acceptance conclusion without changing production. Its isolated US
packet `2026-08-16-us-run-20-a48638e987ce` passes 171 automatic bindings and 14/14 logical messages.
Its fresh current-code KR packet `2026-08-14-kr-run-17-006189184b28` uses the latest eligible
completed after-hours session, passes 141 automatic bindings and 8/8 logical messages, and keeps all
SK Hynix denied earnings and dependent PE lineage out of prose. Both full validators report zero
errors; label, instrument, zone-role, postposition, identity, comparative, and repetition hard checks
report zero findings. TSM and WRD remain safely `unknown` because no authoritative identity cache
exists. At Phase 7.2.8 completion the branch was not merged or deployed and both Previews required
direct human approval; later ancestry promotion does not retroactively make them live evidence.
See [the Phase 7.2.8 readiness report](reports/20260816-phase7-2-8-human-review-safety-readiness.md).

Phase 7.2.9 now supersedes the Phase 7.2.8 automated acceptance conclusion on the experimental
branch only. The immutable KR Day 3 payload fails the new runtime gate with six particle errors,
actor/horizon supply claims without occurrence-level numbers, missing financial periods,
unsupported valuation judgments, and repeated reasoning skeletons. Corrected isolated packets
`2026-08-16-kr-run-21-27d84c4e9795` and `2026-08-16-us-run-20-53fa21541277` pass automatic binding,
the full validator, and `runtime-message-quality-v1`; their logical payload counts are 8 and 14.
The gate is now in the delivery path and its receipt binds packet, validated-output, and rendered-set
hashes before delivery eligibility. CORZ PBR and dependent historical PB are denied by
`valuation-coherence-v1`, RXRX uses relative volume rather than generic supply language, and KR
financial amounts carry verified amount-period labels. These corrected Previews remain
`pending_work_human_review`, are not Production Assist evidence, and are neither merged nor deployed.
See [the Phase 7.2.9 readiness report](reports/20260816-phase7-2-9-runtime-quality-readiness.md).

Work subsequently failed the Phase 7.2.9 corrected KR Preview for amount-period, RR-basis, and
valuation-interpretation defects; its US Preview remained unapproved. Phase 7.2.9.1 addresses those
blockers on `codex/phase-7-2-9-1-quality-blockers`. It separates filing period from field-level amount
period, gives current-price and support-entry RR distinct semantics, requires typed homogeneous
valuation evidence, and verifies the full runtime receipt file SHA before retry or delivery reuse.
Corrected isolated packets `2026-08-16-kr-run-21-5844682f15da` and
`2026-08-16-us-run-20-f9b252d77940` pass their deterministic validators and runtime gates. Both remain
preserved artifacts, but Work subsequently failed both Previews. The failures were missing
consolidated/separate statement basis, a denied PER qualitative bypass, final-text particle and
duplicate-label defects, internal implementation language, a MU relation/caution contradiction, and
receipt audit coverage that overstated its partial-delivery evidence. They are not Production Assist
evidence. See [the Work review](reports/20260817-phase7-2-9-1-work-human-review.md) and
[the Phase 7.2.9.1 readiness report](reports/20260817-phase7-2-9-1-readiness.md).

Phase 7.2.9.2 repairs those blockers on `codex/phase-7-2-9-2-human-quality-hardening`. It adds
`financial-statement-basis-v1`, exact occurrence-bound `typed-valuation-interpretation-v2`, a final
rendered-language gate, forward-period relation/caution consistency, and explicit pre-send versus
post-partial receipt-integrity states. Corrected isolated packets
`2026-08-16-kr-run-21-23491b3e8f73` and `2026-08-16-us-run-20-fb918a643ae6` pass automatic binding,
the full validator, and the runtime final-message gate with 8 and 14 logical payloads. Their human
quality remains `pending_work_human_review`; production main and the operating checkout are
unchanged. See [the Phase 7.2.9.2 readiness report](reports/20260817-phase7-2-9-2-readiness.md).

## Phase 9.1D Handoff

- Contract: `working-capital-runtime-shadow-canary-v1`
- Instruction commit: `dc4e1cf14faa7cebf78eb8ba5a5e73b6369c991c`
- Implementation commit: `5316113062782b09595a495ec9a903a4973f9df5`
- Scope: total Inventory and exact Trade AR only, dynamically selected
- Retrospective parity: 5 Inventory + 2 exact Trade AR, relation drift 0
- Binding: 7 automatic, 0 manual/rejected/unresolved
- Production influence and user-visible diff: 0
- Runtime state: `DEPLOYED_PENDING_NATURAL`
- Inventory natural proof: `NOT_OBSERVED`
- exact Trade AR natural proof: `NOT_OBSERVED`
- Phase 9.1E architecture readiness: YES, natural proof continues in parallel

The canary is dispatched independently from the cash-flow canary after a terminal delivery receipt.
It combines packet financial-period context with the static canonical report so a newer formal
period suppresses an older relation. Empty opportunities produce a terminal suppressed receipt;
validation failures remain isolated and retryable under one logical canary ID.

## KR Producer Integrity Handoff

- Instruction commit: `2125562a863d858ee1ab62675c31c7c13be33506`
- Implementation commit: `c26c9359b134df0a4cd697fd97e7616cc508e885`
- Contracts: `xkrx-role-target-v1`, `packet-bound-delivery-intent-v1`,
  `kr-orphan-delivery-reconciliation-v1`
- Trigger: Saturday `daily_kr` run 33; expected packet
  `2026-08-22-kr-run-33-c2491c2e78ad` was never persisted
- Root cause: no producer session guard, notifications before packet, and packet-ID-only hold entry
- Guard: `kr_daily_production` before KR-close/provider/run state
- Delivery order: analysis without queue, persisted packet, provisional packet-bound intent, hold
- Pending semantics: raw DB pending is distinct from deliverable and held-session pending
- Reconciliation: stock 7 plus digest 1 changed to existing `failed` state; reason
  `non_trading_day_orphan_no_packet`; sent/deleted/`sent_at` counts zero
- Tests: 50 focused and 1,406 full PASS; Actions run `32565412721` PASS
- State: `DEPLOYED_PENDING_NATURAL`; next natural weekend/holiday proof is pending
- Inventory: `ENABLED_PENDING_NATURAL`; exact Trade AR remains OFF

## Source Map

- Packet, claim, validation, grounding: `app/services/ai_review_service.py`
- Numeric draft binding: `app/services/numeric_provenance_service.py`
- Market facts and transmission: `app/services/market_intelligence_service.py`
- Numeric semantics: `app/services/numeric_semantic_registry.py`
- Chart structure: `app/services/ohlcv_structure_service.py`
- Monitoring state and peer context: `app/services/monitoring_state_service.py`
- Exchange-session eligibility: `app/services/market_session.py`
- Runtime packet preflight: `app/services/runtime_packet_completeness_service.py`
- Working-capital runtime canary: `app/services/working_capital_runtime_shadow_canary_service.py`
- Current price-context selector: `app/services/current_price_context_service.py`
- Runtime specificity plan: `app/services/runtime_specificity_service.py`
- Candidate ownership normalization: `app/services/runtime_reasoning_ownership_service.py`
- Renderer and delivery: `app/services/ai_assisted_delivery_service.py`
- KR producer entry: `app/jobs/monitor_daily.py`
- Delivery-intent reconciliation: `app/services/notification_delivery_integrity_service.py`
- Deterministic fallback assembly: `app/services/notification_service.py`
- Industry routing and causal guardrails: `app/services/industry_reasoning_service.py`
- Skill: `.agents/skills/thesis-monitor-daily-review/SKILL.md`
- Runtime policy: `.agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md`
- Output schema: `.agents/skills/thesis-monitor-daily-review/references/output-schema.json`
- Pilot archive: `data/ai_review/pilot/history`

## Known Gaps

- Massive US breadth is implemented in shadow, but exact 08:05 KST readiness over 3-5 normal
  sessions is not yet established.
- KRX historical capability, universe and publication-state contracts pass experimentally, but
  16:05, 08:05 and T+1 roles remain `NOT_YET_PROVEN`; operating integration is false. A dedicated
  telemetry-only LaunchAgent now captures natural 08:05 and 16:05 observations without feeding the
  market digest. T+1 has no defined exact clock and is not double-counted from 08:05. The Kiwoom
  Windows gateway is not configured.
- KR market-wide foreign/institution/retail flow, KOSPI/KOSDAQ breadth, KOSPI size, and sector
  context are implemented through official Kiwoom REST evidence. KOSPI stock-sum concentration is
  still blocked by basis/taxonomy reconciliation; same-day complete KRX cross-check is pending.
- Industry-specific causal reasoning contracts are implemented, but specialized structured routing
  covers 9/20 immutable active stocks; taxonomy and business-unit coverage remain partial.
- Peer provider policy is FREE_ONLY. Phase 8.3 is finalized at 1/20 active and 1/15 meaningful
  coverage as SELECTIVE_OPTIONAL_CONTEXT. Broad runtime value is LOW_ROI; historical PIT and
  forward expansion are deferred, and operating integration is false.
- Cash-flow architecture, canonical core, archive consumption, natural canary, baseline consistency,
  and selective initial rollout are closed. User-visible natural proof is pending. KR remains
  partial on unresolved CF period context; CCC and standard ROIC are deferred.
- Working-capital architecture, canonical core, and archive consumption are promoted. The detached
  Inventory/exact-Trade-AR runtime canary is deployed. Selective Inventory is enabled pending its
  first natural user-visible proof; exact Trade AR, broad AR/AP, exact AP, DSO, Inventory Days,
  DPO, and CCC remain disabled or deferred.
- The KR non-trading-day producer repair is deployed pending natural weekend/holiday proof. Its
  deterministic guard, packet-bound delivery-intent ordering, and exact run-33 reconciliation are
  closed; a future non-trading session must show zero provider calls, runs, rows, packets, and
  notifications. This proof runs in parallel and does not supersede the Inventory next action.
- The persisted US count includes the 2026-08-16 operationally complete session whose human message
  quality review failed. Operational count and human approval remain separate; this packet is not
  Production Assist evidence.
- TSM and WRD lack authoritative production identity evidence. Their live `unknown` state and
  multiple withholding are correct until a separately approved identity ingestion.
- The 2026-08-18 natural KR packet proves the repaired current-price RR paths for the four run-23
  affected stocks. RR runtime path is LIVE PATH PASS. Both natural US and KR AI drafts still failed
  the runtime quality gate and delivered deterministic fallback, so full Natural Live AI quality is
  PARTIAL. Phase 8.5.3.2 passes immutable replay and is shadow-promoted but still needs natural proof.
- Production Assist remains disabled pending a separate decision after successful Pilot evidence.

Never fill data gaps with model knowledge. Add a deterministic fact, semantic contract, and tests
first.

## Common Market Adapter Handoff

- Instruction commit: `c058839c5e63a08c096bd6a9a1b2139290d17eb0`
- Stage A repair: `b39c2ea38a8d5d3466889a9da394df05ad95701a`, replay PASS
- Adapter implementation: `7a210efe101547c1981b934fbf3dc867bc3e6426`
- Contract: `market-context-adapter-v1`
- KR run-38: `PARTIAL`; local index/breadth/sector/size/market flow Unknown
- US run-37: `PARTIAL`; SPY/QQQ/IWM, SOXX, two verified relative relations; breadth/flow Unknown
- Common Fact/unit/temporal gates: PASS, conflicts/errors `0/0`
- Research seeds: shadow configuration only
- Production research connector: `NOT_AVAILABLE`
- Open Research live canary/integration: `BLOCKED_CONNECTOR / 0`
- Structured adapter: `DEPLOYED_PENDING_NATURAL` after exact-SHA promotion
- Public Action/schema/fallback/canary limits: unchanged at `0.4.5 / 4 / unchanged / 1-2-3`
- Open P0/material P1: `0/0`

Inspect the next naturally scheduled US packet and delivered artifacts read-only. Confirm sidecar
presence, partial-field fallback, canary counts, hard safety, duplicates/orphans, and exactly-once
receipt integrity. Do not create the three dated 2026-08-26 natural reports until that run exists.
KR natural canary, Inventory, macro, KRX telemetry, and weekend/holiday proofs continue in parallel.

## Milestones

1. Initial baseline and daily-delta isolation.
2. Fact sanitization, warning provenance, and treasury materiality.
3. Historical valuation basis and modeled-versus-consensus safety.
4. Notification ordering, deferred FIFO, and KRX morning gate.
5. Codex Shadow packet, claim UUID, lease, flock, and finalize fencing.
6. Knowledge v3 parity and verified company-profile routing.
7. Prose-level numeric provenance and fail-closed semantic registry.
8. Single-delivery AI-assisted Pilot with deterministic fallback.
9. Dual Knowledge and OHLCV structure v1/v2 correctness hardening.
10. Phase 6 market intelligence and portfolio transmission.
11. Phase 6.1 quantitative hard gate, required night-futures grounding, fast morning pipeline, and
    persisted Telegram delivery retry.
12. Phase 7 durable monitoring state, registered-rule lifecycle, dynamic-price grounding, and
    fail-closed peer valuation.
13. Phase 7.1 deterministic numeric provenance binding, canonical formatter and currency-basis
    hardening, machine correction context, and persisted fallback retry safety.

## Next Steps

1. After the next natural US cycle, review the selected Phase 9.0E cash-flow subjects, exact Facts,
   period/scope, AI/fallback path, message quality, Unknown resolution, canary parity, and delivery
   integrity. Do not run it manually.
2. In parallel, inspect the next natural US/KR sessions after Phase 8.5.5.2 and verify AI quality,
   structured supply, RR ownership, business numeric ownership, reasoning ownership, night-futures
   lineage, language, fallback, runtime receipt, archive, and exactly-once behavior.
3. Preserve operational counts KR 3/5 and US 3/5 and retain all natural/replay artifacts without
   counter edits, resends, or archive rewriting.
4. Keep TSM/WRD and unverified KRX identity/share bases `unknown`, fine-grained industry routes
   general where unproved, peer data unavailable where absent, and security-level cash-flow
   valuation metrics blocked where share/FX basis is incomplete.
5. Let `com.seungsoo.thesis-monitor.krx-publication-telemetry` capture natural 08:05 and 16:05 KRX
   observations. Do not run it manually, define T+1 by inference, or integrate breadth until role
   evidence and Human Review pass.
6. Keep Phase 8.3 closed as selective optional context unless materially new free-source, taxonomy,
   exact-group or natural-message evidence appears.
7. Apply Phase Advancement Rule v1 to new runtime findings: disable Phase 9.0E for P0, bound material
   P1 repairs, and retain P2 as backlog.
8. Phase 9.1A architecture, 9.1B canonical core, and 9.1C archive consumption are promoted. Phase
   9.1D canaries only current-formal total Inventory and exact Trade AR after terminal delivery.
   Observe enabled Inventory naturally and keep exact Trade AR, broad/AP use, DSO, Inventory Days,
   DPO, CCC, and standard ROIC disabled.
9. Keep Production Assist disabled until natural full-message evidence passes direct human review
   and the user explicitly approves it.
10. On the next natural KR weekend or holiday, inspect the producer artifacts read-only and confirm
    zero provider calls, monitor runs, notification rows, packets, and sends. Do not trigger a
    manual production run; continue waiting for the first eligible Inventory packet in parallel.

## 2026-08-24 Legacy Compatibility Closure

- Instruction commit: `2ddec88382f0aff32fcae68a87d1aff62f60f2ef`
- Implementation commit: `5c58f32e23db7a817f5f9947d2af509f6021f4ff`
- Contracts: `macro-temporal-legacy-rehydration-v1`, exact shadow numeric registry classes
- Immutable replay: packet 1; dry-run intents 8; AI 8; fallback 8; duplicate/orphan/send 0/0/0
- Macro: prior session 4; reference 8; current/defaulted-current/false-current 0/0/0
- Registry: 210 unsupported before, 210 exact internal-derived after, prose-eligible 0
- Inventory: 000660 2.1%p, 005490 7.1%p, 005930 35.8%p; mismatch 0
- Safety: production DB/Telegram/task/Pilot/archive mutation all 0
- State: `DEPLOYED_PENDING_NATURAL`; P0/P1 0/0
- Next: `WAIT_FOR_FIRST_SUCCESSFUL_KR_NATURAL_PACKET`

## 2026-08-25 Kiwoom KR Market Context Handoff

- Instruction commit: `f45c6c9d47253c0ad8cad9affcf0eb54be188117`
- Implementation commit: `32178dc5b2cd4a5fd38af51514b4ac5d12d1cbd0`
- Contracts: `kiwoom-kr-market-context-v1`, `kr-market-flow-reconciliation-v1`,
  `kr-market-flow-concentration-v1`
- Exact TRs: `ka20001`, `ka20003`, `ka20009`, `ka10051`, `ka10066`
- Session proof: completed 2026-08-25 KST, index/history/composite identity matched
- Breadth: KOSPI 647/226/34; KOSDAQ 1186/466/74
- Market flow: both markets and all three primary participants PASS in KRW integrated basis
- Pagination: KOSPI 14 pages/1316 rows; KOSDAQ 19 pages/1824 rows; complete; duplicates 0
- Concentration: KOSDAQ PASS; KOSPI blocked by unresolved basis/taxonomy
- Run-38 enriched replay: 8/8; hard safety 0; market digest material improvement
- Runtime: best effort before KR packet persistence; packet continues on provider failure
- KRX: independent telemetry; same-day reconciliation `NOT_OBSERVED`
- State: `PARTIAL`, `PRODUCTION_READY=YES`, pending natural proof
- Safety: no Telegram, manual task, Pilot, DB, archive rewrite, or Production Assist change

At the next natural eligible KR close, inspect the persisted structured sidecar, selected 1/2/3
canary messages, fallback, receipt, duplicates/orphans, and provider-failure fallback behavior.
Do not run production manually. Keep KOSPI concentration suppressed until reconciliation is closed.

## 2026-08-26 KR/US Bounded Quality Handoff

The exact instruction is commit `8cf5226ca0c5ae5553fb06b24399462ea3cf6088`; code implementation
is `f2326c39485e600bca2cee15747deeb8465c5c8a`. Read the bounded-quality readiness, exact
before/after, KR utilization, US specificity, safety-parity, and canary reports first.

KR run-38 replay is 8/8. Its market digest now uses P1 local structure for judgment and P2 local
flow for interpretation and next check. US run-37 replay is 14/14; generic shared synthesis is
`8 -> 0`, cross-industry generic repetition is `4 -> 0`, and missing supported discriminators are
`4 -> 0`. TSM is owned by the semiconductor-foundry framework, while CORZ/HUT/WULF retain supported
data-center distinctions and CRCL remains the positive control. All hard safety errors are zero.

Do not manually run KR/US production or Telegram. Keep full mode OFF, canary limits 1/2/3, Open
Research integration 0, Trade AR OFF, and Production Assist OFF. Observe natural delivery
read-only. Unless that observation reveals a new P0/P1, the next major engineering scope is the
Open Research production connector and selective event attribution.

## 2026-08-26 Fibonacci Variable AI Anchor Handoff

The exact instruction is commit `d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890`. Read the
Fibonacci P1 closure readiness JSON, exact benchmark, stability, egress, candle-context, KR/US
replay, reference comparison, and safety-parity reports first.

The signed-in local Codex route actually ran with `gpt-5.6-sol`, high reasoning, read-only sandbox,
ephemeral sessions, and a strict ID-only schema. Frozen public price packets cover 20/20 active
subjects. Benchmark packets ran five times and all others three times. Runtime failures are zero,
private/secret/thesis egress is zero, and material candidate omissions versus full debug are zero.

Do not enable this feature. Monthly/weekly material variation is `3/11`, semantic timeframe
rejections are `4`, and only `8/20` stocks satisfy the first-pool higher-timeframe gate. State is
`SHADOW`, code correctness is PASS, variable trial is PARTIAL, and
`PRODUCTION_ENABLEMENT_READY=NO`. The bounded next repair is anchor-versus-SR ownership separation
plus tighter `AMBIGUOUS/INSUFFICIENT_STRUCTURE` semantics; retain existing tolerances and frozen
trial protocol. This P1 is local to Fibonacci enablement and does not block Open Research work.

## 2026-08-26 Fibonacci Anchor/SR Consensus Handoff

The exact instruction is commit `39cab7ed8b1cb3bebea1bd1240498caa454bd09a`; the archive-only
implementation is `0dfef76bba606f018893d6e68e7beaf410aa7438`. Read the final P1 readiness,
root-cause, ownership, candidate, abstention, exact benchmark, stability, KR/US replay, and safety
parity reports before changing this feature.

SR is now backend-owned and cannot vary with AI selection. AI returns only a canonical swing
structure ID, optional alternative, or valid `AMBIGUOUS`/`INSUFFICIENT_STRUCTURE` abstention.
Consensus is per timeframe under the unchanged 5/3 protocol. Monthly/weekly/daily SR variation is
zero; valid abstentions are 56; 28 timeframe structures are eligible; 13 unstable and 19
insufficient timeframes are safely omitted; unstable Fib exposure is zero.

State is `INTEGRATED_READY_NOT_ARMED`, code correctness is PASS, and production enablement readiness
is YES with P0/material P1 at 0/0. Do not treat this as activation. The next feature-local action is
a separately instructed bounded multi-timeframe Fibonacci enablement. Keep existing merge
tolerances, deterministic SR, backend Fibonacci arithmetic, user-visible routing, task schedules,
and Production Assist unchanged until then.

## 2026-08-26 Price Structure v3 SR Completeness Handoff

The exact instruction is commit `7267ca1d3e518d39986941bfda1d6447560db344`; final code
implementation is `176f3e73eb097fac99f4038a8987b610954804cc`. Read the SR readiness JSON,
base-layer audit, proximity root cause, missing-side audit, negative controls, full replay, and SK
hynix regression before changing this feature.

Deterministic monthly/weekly/daily SR now precedes wave/Fib. Nearest and major have separate
rankings, current-zone ownership is explicit, and daily/weekly fallback preserves requested versus
source timeframe. Remote historical cross-zones are audit-only unless they pass the active
local-relative relevance gate. `010120`, `MU`, `TSM`, and no-wave `SNDK` pass; `003690` and `HUT`
recover local daily resistance; SKHY remains legitimate insufficient monthly history.

State is `INTEGRATED_READY_NOT_ARMED`; P0/material P1 are `0/0`; user-visible diff is zero. The next
feature-local task is `BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`. Preserve
current grouping/Fib tolerances, SK hynix stable confluence, TSLA Fib suppression, task schedules,
Public Action, assessments, and Production Assist until separately instructed.

## 2026-08-26 Price Structure v3 Current-Data Validation Handoff

The exact instruction is commit `688c17280a10e91214d4bd9888522fdc6f9bc0c5`; the archive-only
validator implementation is `ef586c3816ff76417d2620636975d054935533d4`. Read
`docs/reports/20260826-v3-current-data-enablement-readiness.json`, the exact candidate-message JSON,
session audit, review table, controls, and safety parity before changing this feature.

The validation uses the active 20-subject universe and target sessions KR `2026-08-26` / US
`2026-08-25`. Fresh collection exposed incomplete US `2026-08-26` stubs; all 13 are excluded and
none enters a pivot, wave, current price, or message. Eligibility is KR `6/1/0/0` and US
`4/9/0/0` for eligible/SR-only/omit/blocked. Human quality is material 16, minor four, worse zero;
all mandatory controls and all hard safety counters pass.

This is still `INTEGRATED_READY_NOT_ARMED`. Production recommendation is `ENABLE_SELECTIVELY`, and
the next separately instructed action is
`BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`. Do not reuse an incomplete US bar,
reintroduce exact overlapping ranges, widen Fib/SR tolerance, or mutate business text, runtime
routing, Telegram, tasks, assessments, Public Action, or Production Assist.

## 2026-08-26 Price Structure v3 Legacy Detector Handoff

The exact instruction is commit `97b65fc1d258339563b54961a83acd997867e11e`; implementation is
`3685aa991589ca0e7cc560104d4ebf8289e3f91d`. Read the legacy-detector readiness JSON, RXRX exact
regression, protected-field audit, token-boundary policy, nontechnical-suppression audit, and exact
candidate-message JSON first.

The prior detector matched `rsi` inside `Recursion` because it scanned every line with an
unbounded case-insensitive substring regex. Detection is now semantic-field first and
token-boundary aware. All 20 headers, names, tickers, and headings survive; RXRX restores only its
header; MU still suppresses its one stale OHLCV/MACD sentence. SR/Fib, stored rules, eligibility,
business facts, provenance, and runtime output are unchanged.

State is `INTEGRATED_READY_NOT_ARMED`; P0/material P1 are `0/0`; selective production-enablement
readiness is YES. Do not enable implicitly. The next feature-local action remains
`BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`, with Production Assist OFF and no
manual task or Telegram operation.

## 2026-08-27 KR Local-First and Numeric Registry Handoff

The exact instruction is `f6ba660048d3fa520e3aeb43d04036c119764292`; integrated code is
`848eb80f6ce6504a9a855973b591ee0749167514`. Read
`docs/reports/20260827-kr-bounded-repair-readiness.md`, the before/after digest, evidence ownership,
378-path inventory, registry-after, AI readiness, fallback parity, safety parity, and artifact index
before changing this path.

Run 40 immutable replay now uses KR local evidence as the digest primary block and binds all
1,961 numeric paths: 1,472 prose-allowed, 489 denied, zero unsupported. Supported sector count
semantics are exact; audit-only limits remain denied. Cross-market sector fact IDs are unique.
Reconciliation and concentration uncertainty are unchanged and remain suppressed from prose.

Replay gates close at P0/material P1 `0/0`, but natural KR proof is still pending. Do not run a
manual KR task or Telegram. Wait for the next natural close, inspect it read-only, and keep Track C
`DO_NOT_START`, Price Structure v3 `INTEGRATED_READY_NOT_ARMED`, and Production Assist OFF. Natural
US reproof may continue independently.

## 2026-08-27 US Morning Natural Market Data Review Handoff

The exact instruction is commit `5377d5e4f15a82e01ac40b6d50d47eee9ef0a30c`. Read the US morning
readiness JSON/Markdown, completeness matrix, evidence-utilization audit, exact message, ownership,
and AI/fallback parity reports before changing the US market path.

Natural run 41 and packet `2026-08-27-us-run-41-ae4f42c23abc` correctly own the completed
`2026-08-26` session. Backup claim `47434507-ac80-48ed-95f0-ea1fb91abe83` delivered `14/14`
messages exactly once. RSP is safely `CURRENT_DIRECTIONAL`, XLC remains `CURRENT_LEVEL_ONLY`,
official Nasdaq breadth is `PUBLICATION_PENDING`, all macro facts are date/role-bound, and the exact
market payload matches its receipt-linked archive.

The natural digest still fails human evidence utilization: SPY, QQQ, IWM, SOXX, RSP, XLI, and XLV
were material omissions, and no current-session ETF/sector fact reached the final digest. Existing
runtime quality passed because it does not enforce this cross-section survival. This is one open
material P1 and no P0. State is `MATERIAL_P1_FOUND_STOP`; Track A is
`BOUNDED_REPAIR_REQUIRED`; next action is `BOUNDED_US_MARKET_REPAIR`. Do not fold the repair into
this report-only branch. KR natural proof stays pending and Price Structure Track C stays blocked.

Latest bounded US market repair follows instruction commit
`c17f67a5d385b51d1249aa7b3d5452207938f084` and integrated implementation
`069f002437163bff1df7aa6e258918c1777d5dfa`. Read
`docs/architecture/US_MARKET_DIGEST_PLAN.md`,
`docs/architecture/MARKET_EVIDENCE_UTILIZATION_VALIDATOR.md`, and
`docs/reports/20260827-us-bounded-repair-readiness.json` first. Immutable run 41 proves the old
macro-only digest now fails and repaired AI/fallback candidates consume current ETF, RSP, and
sector-dispersion slots from one shared plan. Breadth remains unavailable without zero fill.

State is `REPLAY_PASS_NATURAL_REPROOF_PENDING`, not `LIVE_PASS`. Wait for the next natural US
morning. Do not trigger a task or send Telegram. Verify the naturally produced shared plan,
current-session slot consumption, optional macro subordination, exact delivery, receipt, duplicate
count, and orphan count read-only. Keep the KR natural reproof separate, Price Structure Track C at
`DO_NOT_START`, v3 unarmed, and Production Assist OFF.

## 2026-08-27 KR Size / Sector Selection Repair Handoff

The exact instruction is commit `794c6f5d956d0928eac0113d658fede58b1266dc`; implementation is
`6a54db130e95e25969a5ca0a100648d4a12c3aa2`. Read
`docs/reports/20260827-kr-size-sector-repair-readiness.json`, the run-42 before/after, plan,
AI/fallback parity, provenance, message-quality, safety, validation, and artifact-index reports
before changing the KR digest path.

The shared KR plan now requires complete safe size/style groups and bounded relative sector
extrema. Immutable packet `2026-08-27-kr-run-42-5d8d23e6fbd6` proves six size and four sector
source refs survive into repaired AI and fallback messages with zero material information loss.
The old exact message fails the new policy as expected. Provider acquisition, numeric-registry
policy, participant-flow reconciliation, concentration, US digest logic, Price Structure v3, and
business-thesis state are unchanged.

State is `REPLAY_PASS_NATURAL_REPROOF_PENDING`, not `LIVE_PASS`; P0/material P1 are `0/0`. Wait for
the next natural KR close and inspect current session, exact packet/message, required size/style,
relative sector extrema, index/breadth/flow preservation, provenance, exactly-once receipt,
duplicates, and orphans read-only. Do not manually run a task or send Telegram. The independent US
natural reproof remains pending, Track C remains `DO_NOT_START`, v3 remains unarmed, and Production
Assist remains OFF.

## 2026-08-27 KR Market Pre-Enable Test-Send Handoff

The exact instruction is commit `f161bc1c724cfd431efaaa458af61e02a378daeb`; the fail-closed audit
implementation is `7d2823c236c458cf76c77faae043c6288e46e65e`. Start with
`docs/reports/20260827-kr-preenable-gate-matrix.json` and the 16-report artifact bundle.

Run-42 production-equivalent data, numeric provenance, reconciliation suppression, shared plan,
repaired AI candidate, and deterministic fallback all pass. The AI candidate includes both markets'
size/style and relative strong/weak sector lines. It was not sent: operating configuration has no
dedicated TEST chat and production must not be reused. Test delivery, receipt, received-message
inspection, and further enablement are therefore `NOT_SENT` / `DO_NOT_ENABLE`.

The size/sector policy remains pre-existing `ACTIVE_BY_CODE_DEFAULT`; this task changed no runtime
gate. Open P0 is zero and the one material P1 is `dedicated_test_sink_not_configured`. Next action is
a bounded external configuration repair: add one explicit dedicated test sink, prove its ID differs
from production, and rerun this exact preflight once. Keep Price Structure v3 unarmed, US untouched,
Production Assist OFF, and all production/manual delivery paths unused.

## 2026-08-27 KR Price Structure Daily History / Nearest Semantics Handoff

The exact instruction is commit `0a8dae7eeca7126844094f0aebcc7a7df0bea606`; independent Track A
and B are `da82d89c2e1c3bc125442128da1573d532263d74` and
`83f3d643bc2cb40d9039c1d965647d01a43769e2`; integrated code is
`04fb7ad7646a55e03000134f50b3f402a6c49c87`. Start with
`docs/reports/20260827-kr-price-structure-repair-readiness.json`, the seven-ticker replay, render
diff, daily-history contract, proximity validator, safety parity, and artifact index.

Daily acquisition was failing because the client sent `count=1200` to an endpoint capped at
1,000. It now requests 1,000, retains the 1,200-bar canonical target, and marks the result
`PARTIAL/provider_limit`. No synthetic daily bars or weekly/monthly substitution is allowed.
User-visible proximity is also provenance-bound: only `NEAR/ACTIVE_NEAR` is `가까운`, while
relevant structural and long-horizon zones use their own labels. The old 000660 output fails as
expected and all seven current repaired outputs pass.

State is `REPLAY_PASS_READY_FOR_PREENABLE`, P0/material P1 `0/0`. This repair sent nothing and did
not arm either KR guard. Price Structure v3 remains `INTEGRATED_READY_NOT_ARMED`; US behavior,
TOP3 sector logic, Telegram, tasks, DB, assessments, archives, and Production Assist are unchanged.
The next action remains a separately authorized test-sink pre-enable rerun after one dedicated
non-production recipient is configured.

## 2026-08-27 KR Daily 1200 Extension / Degradation Handoff

The exact instruction commit is `3e42f3fad2e32ff1b3cca47861cfb9704095ce28`; Track A is
`c9e8fc1e25394857bd88d4652e3a8b1e88638011`, Track B is
`d60b7b2a9edecbad0ed54c2151ecfba163478522`, and Track C implementation is
`f957bea48e1bf8df23c6b8fe769812ade5663456`. Start with
`docs/reports/20260827-kr-daily-1200-readiness.json`, then read provider capability, window probe,
seven-ticker coverage, replay, render diff, safety, and validation reports.

The supported `/ohlcv` endpoint has a hard 1,000-row maximum and no exposed older-window control.
The canonical target remains 1,200; all seven frozen-session daily series are therefore
`PARTIAL_SAFE/provider_limit` at 1,000, never `PASS`. Actual session gaps and duplicates are zero.
The two calendar-library overexpectations are official KRX closures and are retained separately.
All seven price-structure sections remain `ELIGIBLE_SR_ONLY`, all proximity validators pass, and
the old 000660 negative fixture still fails as expected.

State is `REPLAY_PASS_READY_FOR_PREENABLE`, P0/material P1 `0/0`. Price Structure remains
`INTEGRATED_READY_NOT_ARMED`; operating stays on `43731f015901b96e2dee3af009b9e1d074382349`.
No test send or enablement occurred. Next action is
`RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT` under a separate instruction.

## 2026-08-27 KR Final Pre-Enable Stop Handoff

The exact master instruction commit is `9f37cfad97487876d6dfa63c03750f4dab664dbf`; Track A blocked-path
evidence is `05b57901f7cf25086b580510aac6a6e72329cdfc`. Start with
`docs/reports/20260827-kr-final-rollout-readiness.json`, then read the sink configuration/isolation,
delivery, enablement, safety, and artifact-index reports.

No approved dedicated non-production Telegram destination exists under the repository's accepted
secret keys. `KR_FINAL_PREENABLE=BLOCKED`, detail is `BLOCKED_NO_TEST_SINK`, and the sole material
P1 is `dedicated_test_sink_not_configured`; P0 is zero. The strict dependency stopped before
current-session resolution and all Track B work. No test payload, receipt, or message-quality proof
exists. Track C branches were not created, operating was not promoted, both KR feature flags and
US Price Structure remain OFF, and production mutation counters are zero.

Next action is only `CONFIGURE_APPROVED_DEDICATED_TEST_SINK_AND_RERUN_TRACK_A`. Use the existing
secret/config mechanism, never the production recipient. Do not run Track B, create Track C,
promote operating, change flags, restart services, or send any message until isolation proves
Track A PASS.

## 2026-08-28 KR Test Sink Resume Stop Handoff

The exact instruction commit is `68ede1eae42315d94a89023fbc6c1f9be07fc99d`; blocked-resume
evidence is `69e4bd6bc15da2a654ab6dcb678263f0ea049d37`. Start with
`docs/reports/20260828-kr-final-rollout-readiness.json`, then read test-sink config/isolation,
delivery, enablement, natural-proof, and artifact-index reports.

No real test chat was present in any approved secure configuration path. The current process,
canonical environment, operating environment, and seven thesis-monitor LaunchAgents expose zero
accepted test-recipient keys. `KR_FINAL_PREENABLE=BLOCKED_NO_TEST_SINK`; P0/material P1 is `0/1`,
with only `dedicated_test_sink_not_configured`. Track B and all later stages were not run.

The operator must provide exactly one approved non-production Telegram chat through an accepted
secret key. Until then, do not resolve a session, call providers, generate or send messages,
promote operating, restart services, or change flags. Production must never substitute for the
test destination.

## 2026-08-28 US Night-Futures / Current-Time E2E Handoff

Start with `docs/reports/20260828-us-current-time-readiness.json` and the artifact index. Instruction
commit is `f6ab0168d3ef0d8ce1e2b5980ea7aae147db0c75`; deployed implementation is
`f6bc769f823429426474a38f007dc8196b4e5f43`.

Raw night-futures summary strings can no longer bypass `night_futures_gate`. Current expected
session `2026-08-28` remained unavailable and was omitted; one actual `2026-08-27` historical pair
passed the separately labeled positive fixture. Current market `1`, all 13 stocks, and the fixture
were delivered only to the isolated test sink with exact payload parity and zero production intent.
WRD is the sole blocked stock because daily coverage ended `2026-08-26`; all other 12 are
`ELIGIBLE_SR_ONLY` for session `2026-08-27`.

Main/operating deployment and post-deploy smoke pass. Natural market, night-futures display, and US
Price Structure proofs are still `PENDING`; the correct next action is only
`WAIT_FOR_NEXT_NATURAL_US_MESSAGES`. Production Assist remains OFF.

## 2026-08-28 Provisional Bollinger / Price Label v2 Handoff

Start with `docs/reports/20260828-provisional-bollinger-readiness.json`. Exact instruction commit is
`73286dd44135bbc30ef3a145e02f5db81aedbdea`; implementation is
`8c3bb493dc45a12c837053e08361f949ff771f00`.

The new provisional layer consumes only validated in-progress D/W/M bars and remains separate from
price-anchored near/major structure, completed-bar dynamic Bollinger, stored monitoring rules, Fib,
and wave anchors. User-facing output is limited to one provisional range or overlap annotation per
subject. Current quote and completed regular-session structure close now have explicit ownership
and equal-price collapse.

Current-time US 13 + KR 7 replay and corrected full-message test-sink delivery pass `20/20`, with
zero authority leaks, SNDK/WULF bypass, ambiguous labels, duplicate ranges, duplicate delivery,
orphan, or production-recipient send. The initial abbreviated-artifact test attempt is diagnostic
only and never touched production. Open P0/material P1 are `0/0`. Main and operating are deployed
at `d3a58c953c2dd6d100031421770be3a54d0328b5`; API/OHLCV health and post-deploy frozen replay pass
`20/20`. Wait for natural US/KR messages; never trigger a production task for proof. Production
Assist remains OFF.

## 2026-08-29 US Morning Market Data Review Handoff

The exact instruction commit is `428836d4a997a10eb7dd1d1935acdea8ea469b54`; the read-only
evidence implementation is `7fc982ecce30a0af261dcda198ef50280e707531`. Start with
`docs/reports/20260829-us-morning-review-summary.json`, then read the exact-message, natural-run,
Nasdaq breadth, night-futures, macro, and artifact-index reports.

Run 45 targets completed US session `2026-08-28`. All five core ETFs and 11 sector proxies are
current. The exact deterministic candidate equals the naturally delivered market message, and
delivery completed `14/14` with no review-task send. Nasdaq breadth and the `2026-08-29` night
session were not published at collection time; prior rows were rejected and omitted. Macro facts
were classified but none was selected.

State is `PARTIAL_SAFE`, with P0/material P1 `0/1`. The remaining P1 is the rejected AI full-stock
path: the primary candidate has stock risk/reward, valuation, inventory-ownership, and numeric
coverage errors; the backup has three market-evidence-consumption errors and one framework
allowlist error. Rejected AI was not sent. Preserve the already-proven market-data and delivery
parity, and perform only a separately authorized bounded AI validation repair. US Price Structure
natural proof was not adjudicated by this market-message review. Production Assist remains OFF.
