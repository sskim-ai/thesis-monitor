# thesis-monitor — Four-Track Stabilization Program
## A. Natural Codex DNS/Network Transport
## B. Daily-Review Semantic/Provenance Convergence
## C. US Market Message: Night D/W/M + 3Y/5Y/10Y/30Y Treasury Curve
## D. Common Renderer Cleanup + Full Integration + Natural-Live Guard

---

# 0. Task metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-02 KST`
- Task class: `FOUR_TRACK_SEQUENTIAL_BOUNDED_REPAIR`
- Production Assist: preserve `OFF`
- Automated trading/order sizing: `0`
- Production recipient test send: `0`
- Dedicated non-production TEST recipient send: allowed only in explicit integration gate
- Historical production resend: `0`
- Production packet/claim/accepted/assessment mutation during replay/test: `0`
- Decision policy retuning: `0`
- Price Structure algorithm change: `0`
- Valuation algorithm change: `0`
- Scheduler timing/ownership change: `0` unless an exact bounded runtime-environment repair is proven necessary
- Track commits: `required`
- Track-specific CI gates: `required`
- Final integration gate: `required`

This instruction intentionally puts all remaining work under one master plan while keeping implementation isolation.

Do NOT implement this as one undifferentiated large patch.

Required sequence:

```text
Track A
→ focused tests
→ track commit

Track B
→ focused tests
→ track commit

Track C
→ focused tests
→ track commit

Track D
→ focused tests
→ track commit

then:
full US/KR production-equivalent regression
→ dedicated test sink / controlled actual-send if configured
→ full pytest / Ruff / CI
→ final merge
→ wait for natural live
```

Hard:

```text
ALL_TRACKS_COLLAPSED_INTO_ONE_UNREVIEWABLE_COMMIT = 0
```

---

# 1. Evidence basis / currently known failures

## 1.1 US run-51 natural failure

Observed:

```text
source monitor            14/14
technical                 14/14 PARTIAL_SAFE
V2 context                14/14
schema path duplication   0
Codex app-server state    repaired
natural model call        failed in later network/DNS stage
candidate                 0/14
accepted                  0/14
fallback                  14/14
delivery                  15/15 exactly once
```

Prior local read-only state DB defect and schema-path defect were repaired and must not regress.

## 1.2 KR 2026-09-02 natural failure

Observed:

```text
source monitor            8/8
technical                 8/8 FULL
V2 context                8/8
Codex runtime preflight   PASS
Codex app-server init     PASS
actual model request      attempted
chatgpt.com DNS/network   failed
candidate                 0/8
accepted                  0/8
fallback                  8/8
delivery                  9/9 exactly once
```

Primary current functional P1:

```text
natural scheduler Codex DNS/network transport stability
```

## 1.3 Daily-review secondary-path failures

KR review identified failures including:

```text
market breadth authored-label conflicts
working-capital signed-gap semantics:
  000660
  005490
  005930

003690 holder-decision-variable binding

valuation economic-scope mismatches:
  000660
  010120
  012450
```

Existing genuine guards must not be weakened.

## 1.4 User-facing market-message changes already decided

US night futures:

```text
near-month contract remains identity metadata

Daily:
open / close / gap% / return%

Weekly:
open / close / weekly%

Monthly:
open / close / monthly%

Weekly/monthly must say 진행중 when not complete.
```

US Treasury rates:

```text
remove the standalone 10Y real-yield block as the primary user-facing rate section

show nominal U.S. Treasury:
3Y / 5Y / 10Y / 30Y

for each:
current/latest safe yield
+
delta vs immediately previous valid observation in bp
```

Common stock renderer:

remove:

```text
※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.
```

from KR and US V2 stock messages.

---

# 2. Base / lineage rule

At task start:

```text
git fetch origin
resolve latest origin/main
resolve operating HEAD
resolve runtime/deployed SHA
verify clean worktrees
```

Do not branch from a stale SHA copied into an older report.

Before Track A begins, prove the chosen base contains the already-approved repairs:

```text
Codex writable runtime-state / claim-scoped state repair
V2 CLI absolute-path repair
canonical identifier numeric-provenance repair
daily-review earlier schema/quality repair
CPNG/HUT technical recovery
US-morning previous-XKRX-business-day night-date repair
KRX NIGHT OHLC/history work already merged, if present on current main
```

Required:

```text
BASE_CONTAINS_PREVIOUS_SAFE_REPAIRS = PASS
```

---

# 3. Track isolation contract

Each track must produce:

```text
implementation commit
focused test report
architecture/report docs
diff summary
regression statement
```

Track B must not opportunistically rewrite network runtime.
Track C must not retune decision policy.
Track D must not hide A/B/C defects with renderer changes.

Required:

```text
CROSS_TRACK_SCOPE_CREEP =
0 / NONZERO
```

---

# 4. Track A — Natural Codex DNS / Network Transport Stability

## 4.1 Goal

Make natural scheduler execution reliably reach the signed-in model transport.

Do not classify a local DNS/resolver failure as a business/data problem.

Do not "fix" it by bypassing Codex, using pre-baked model output, or switching to deterministic fallback as success.

## 4.2 Reproduce exact natural failure

Capture for KR and, where available, US natural attempts:

```text
scheduler process identity
effective UID/GID/groups
HOME
CODEX_HOME
TMPDIR
cwd
PATH
DNS resolver configuration
network namespace
proxy-related env presence
IPv4/IPv6 resolution behavior
chatgpt.com resolution result
TLS reachability
Codex CLI binary/version
app-server transport mode
WebSocket attempt
HTTPS fallback attempt
retry timing
terminal error
```

Do not expose tokens, cookies, auth headers, or recipient IDs.

Required:

```text
NATURAL_NETWORK_FAILURE_REPRODUCED = PASS
NATURAL_NETWORK_FIRST_FAILURE_BOUNDARY = ...
```

## 4.3 Distinguish failure classes

Use repository-native enums or add equivalent:

```text
LOCAL_DNS_RESOLUTION_FAILURE
LOCAL_NETWORK_CONNECTIVITY_FAILURE
TLS_HANDSHAKE_FAILURE
CODEX_APP_SERVER_TRANSPORT_FAILURE
MODEL_PROVIDER_RESPONSE_FAILURE
MODEL_TIMEOUT
MODEL_RATE_LIMIT
```

Hard:

```text
DNS_FAILURE_MISCLASSIFIED_AS_GENERIC_MODEL_FAILURE = 0
```

## 4.4 Compare natural vs passing test environments

Diff:

```text
interactive/preflight
test sink
scheduler-context probe
KR natural
US natural
```

Focus:

```text
resolver
network interface/namespace
launch-service environment
proxy env
PATH
HOME/CODEX_HOME
runtime user
TLS trust store
Codex binary
```

Set:

```text
TEST_LIVE_NETWORK_FIRST_DIVERGENCE = ...
```

## 4.5 Forbidden network hacks

Do NOT:

```text
hardcode public DNS such as 8.8.8.8
edit /etc/hosts for chatgpt.com
disable TLS verification
globally disable firewall/sandbox
run scheduler as root
copy credentials to a new insecure location
```

Hard:

```text
HARDCODED_PUBLIC_DNS = 0
HOSTS_FILE_CHATGPT_OVERRIDE = 0
TLS_VERIFICATION_DISABLED = 0
GLOBAL_SECURITY_DISABLE = 0
RUN_SCHEDULER_AS_ROOT = 0
```

## 4.6 Repair at the owning boundary

Preferred classes:

```text
scheduler runtime environment parity
launch/service network entitlement/config parity
resolver/environment inheritance fix
supported proxy/network path correction
Codex transport configuration correction
```

Use the smallest supported change.

If a LaunchAgent/service definition changes:

```text
timing unchanged
ownership unchanged
only bounded runtime/network env diff allowed
```

## 4.7 Natural-network preflight

Before expensive V2 generation, add a bounded scheduler-context readiness check.

It should verify:

```text
resolver can resolve required host
basic TLS/connectivity path is usable
Codex app-server can initialize
```

The preflight must:
- not consume stock packet decision state
- not send Telegram
- not write accepted decisions
- not expose credentials

Required:

```text
SCHEDULER_CONTEXT_NETWORK_PREFLIGHT = PASS
```

## 4.8 Bounded retry / backoff

For transient DNS/network errors:

implement a bounded retry schedule appropriate for the available production window.

Requirements:

```text
small bounded attempt count
backoff
jitter only if repository policy supports it
do not retry deterministic local misconfiguration indefinitely
do not hold packet claim until after the delivery window
```

Record:

```text
attempt count
elapsed time
terminal reason
```

Hard:

```text
UNBOUNDED_NETWORK_RETRY = 0
RETRY_STORM = 0
```

## 4.9 Primary / backup behavior

Primary failure should not corrupt the packet.
Backup should use the same repaired network contract.

Required:

```text
PRIMARY_BACKUP_NETWORK_CONTRACT_IDENTICAL = PASS
MULTIPLE_PRODUCERS_OWN_PACKET = 0
```

## 4.10 Track A acceptance

Must pass:

```text
scheduler-context DNS resolution
TLS/connectivity
Codex app-server init
actual signed-in safe model smoke call
primary path
backup path
no production send
```

Set:

```text
TRACK_A_NETWORK_RUNTIME = PASS / FAIL
```

Only after PASS may Track B be promoted onto the same integration branch.

---

# 5. Track B — Daily-Review Semantic / Provenance Convergence

## 5.1 Goal

Make the secondary daily-review candidate path converge under the existing strict validators.

Do NOT relax semantic/numeric/valuation guards merely to achieve PASS.

## 5.2 Exact error ledger

Build a run/ticker/span ledger for known KR failures:

```text
market breadth authored-label conflicts

000660
working-capital signed gap
valuation economic scope

005490
working-capital signed gap

005930
working-capital signed gap

003690
holder decision variable

010120
valuation economic scope

012450
valuation economic scope
```

For each:

```text
canonical fact
field path
AI-authored text
normalized text
validator rule
expected semantic
actual semantic
owner:
generator / normalizer / binder / validator / renderer
```

## 5.3 Working-capital signed-gap semantics

Define one canonical structured semantic.

Examples:

```text
inventory growth minus COGS growth
receivables growth minus revenue growth
working-capital gap
```

Do not let sentence word order invert the sign.

Preferred:

```text
canonical signed value
+
explicit numerator/denominator semantic
+
deterministic textual template for direction
```

Tests must include:

```text
positive gap
negative gap
zero
Korean wording inversion
percentage vs percentage-point
```

Hard:

```text
SIGNED_GAP_DIRECTION_INVERTED = 0
SIGNED_GAP_PERCENT_VS_PP_CONFUSION = 0
```

## 5.4 003690 holder decision variable

Identify exact holder variable expected by the valuation/holder-view contract.

Do not invent a variable or force a generic equity template onto reinsurance.

Make the candidate use:
- the canonical supported insurance/reinsurance variable
- or omit unsupported holder language

Required:

```text
003690_HOLDER_VARIABLE_BINDING = PASS
```

## 5.5 Valuation economic scope

For 000660 / 010120 / 012450:

distinguish:

```text
company-wide
segment
parent/common attributable
TTM
forward
provider-only
historical reconstructed
```

Do not bind a segment/partial economic fact to a company-wide valuation claim.

Required:

```text
000660_VALUATION_SCOPE = PASS
010120_VALUATION_SCOPE = PASS
012450_VALUATION_SCOPE = PASS
```

## 5.6 Preserve genuine guards

Required:

```text
000660_VALUATION_QUALITY_GUARD = PASS
005930_RISK_REWARD_GUARD = PASS
047810_IDENTIFIER_PROVENANCE = PASS
```

No hardcoded ticker exemption.

## 5.7 Market breadth authored labels

If structured breadth labels/numbers already exist:

deterministic renderer should own:

```text
상승
하락
보합
시장 폭
```

Do not allow AI prose to create duplicate numeric labels that collide with canonical registry.

Required:

```text
MARKET_BREADTH_AUTHORED_LABEL_CONFLICT = 0
```

## 5.8 Bounded correction convergence

Correction loop may receive:
- exact errors
- allowed fact IDs
- expected semantic
- forbidden new numerics

It must not:
- change accepted V2 decision
- invent facts
- create targets/stops
- weaken validators

Hard:

```text
DAILY_REVIEW_CORRECTION_CHANGES_V2_ACCEPTED = 0
DAILY_REVIEW_UNBOUND_NUMERIC_AFTER_CORRECTION = 0
DAILY_REVIEW_REPAIR_LOOP_UNBOUNDED = 0
```

## 5.9 Track B acceptance

Use frozen failing KR artifacts.

Target:

```text
all known signed-gap controls PASS
003690 holder binding PASS
valuation economic scope PASS
market breadth conflicts 0
numeric/semantic/valuation validators PASS
message-quality PASS
```

Set:

```text
TRACK_B_DAILY_REVIEW = PASS / FAIL
```

---

# 6. Track C — US Market Data / UI

## 6.1 Goal

Implement the user-approved US morning message format.

This track has two independent market-data features:

```text
C1. Korean night futures compact D/W/M
C2. U.S. nominal Treasury 3Y/5Y/10Y/30Y curve with bp deltas
```

Do not modify stock BUY/HOLD/SELL policy.

---

# 7. Track C1 — KRX NIGHT compact D/W/M

## 7.1 Source architecture

Use official/approved KRX NIGHT daily OHLC.

Preferred architecture already established:

```text
KRX NIGHT daily raw
→ immutable provenance
→ normalized same-contract daily history
→ same-contract D/W/M
→ packet-owned market facts
→ deterministic market renderer
```

If current main already contains this architecture:
modify only the user-facing projection and any missing required gap field.

Do not rewrite raw history.

## 7.2 Contract vs timeframe

```text
202609 etc.
= contract identity

Daily/Weekly/Monthly
= timeframe
```

Hard:

```text
CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME = 0
```

## 7.3 Daily display

User-approved:

```text
Daily:
시가
종가
갭%
등락%
```

Gap baseline:

```text
gap_pct =
night-session daily open
vs
validated preceding regular DAY close baseline
```

Daily return:

```text
daily_return_pct =
night-session daily close
vs
the same validated preceding regular DAY close baseline
```

Use exact existing regular/day comparison contract.

Hard:

```text
DAILY_GAP_BASELINE_INVENTED = 0
DAILY_GAP_AND_RETURN_USE_DIFFERENT_UNDISCLOSED_BASELINES = 0
```

## 7.4 Weekly display

User-approved:

```text
Weekly:
시가
종가
주간%
```

Same selected contract only.

Weekly return:

```text
current weekly close
vs
previous completed same-contract weekly close
```

If baseline unavailable:

```text
주간: 자료 부족
```

No cross-contract splicing.

## 7.5 Monthly display

User-approved:

```text
Monthly:
시가
종가
월간%
```

Same selected contract only.

Monthly return:

```text
current monthly close
vs
previous completed same-contract monthly close
```

If unavailable:

```text
월간: 자료 부족
```

## 7.6 In-progress labels

If current week/month not complete:

```text
주봉(진행중)
월봉(진행중)
```

Hard:

```text
IN_PROGRESS_WEEKLY_LABELED_FINAL = 0
IN_PROGRESS_MONTHLY_LABELED_FINAL = 0
```

## 7.7 Compact renderer target

Example structure:

```text
🌙 한국 야간선물 · 기준 09/01

• KOSPI200 최근월물 (202609)
  - 일봉: 시가 1,067.00 · 종가 1,064.50 · 갭 -x.xx% · 등락 -0.31%
  - 주봉(진행중): 시가 1,068.00 · 종가 1,064.50 · 주간 -1.60%
  - 월봉(진행중): 시가 1,067.00 · 종가 1,064.50 · 월간 +0.03%

• KOSDAQ150 최근월물 (...)
  - 일봉: ...
  - 주봉(진행중): ...
  - 월봉(진행중): ...
```

Do not show H/L in user-facing output.

Keep H/L internally if needed for source quality.

## 7.8 Track C1 gates

```text
NIGHT_DAILY_OPEN_CLOSE_GAP_RETURN = PASS
NIGHT_WEEKLY_OPEN_CLOSE_RETURN = PASS
NIGHT_MONTHLY_OPEN_CLOSE_RETURN = PASS
NIGHT_DWM_NUMERIC_PROVENANCE = PASS
MULTI_CONTRACT_DWM_SPLICING = 0
```

---

# 8. Track C2 — U.S. nominal Treasury curve

## 8.1 User-facing contract

Replace the standalone 10Y real-yield primary block with:

```text
3Y
5Y
10Y
30Y
```

nominal U.S. Treasury yields.

For each:

```text
latest safe yield
+
change vs immediately previous valid observation
in basis points
```

Example:

```text
🌐 미국 국채금리
• 3년: 3.72% · -2bp
• 5년: 3.84% · +1bp
• 10년: 4.21% · +4bp
• 30년: 4.86% · +6bp
```

## 8.2 Source verification

Use an existing approved authoritative source if present.

If the repository lacks one, use only an approved official/public source after documenting:
- provider
- exact series/maturity mapping
- observation convention
- publication lag
- source license/access

Do not silently scrape an arbitrary finance website.

Required:

```text
UST_3Y_SOURCE = PROVEN
UST_5Y_SOURCE = PROVEN
UST_10Y_SOURCE = PROVEN
UST_30Y_SOURCE = PROVEN
```

## 8.3 Observation pair

For each maturity:

```text
current = latest safe valid observation
previous = immediately previous valid observation of same series
delta_bp = (current_pct - previous_pct) * 100
```

Do not compare:
- to arbitrary prior calendar day
- to another maturity
- to real yield

Required:

```text
UST_OBSERVATION_PAIR_VALID = PASS
```

## 8.4 Temporal labeling

If observations lag the equity session:

show the observation date in the section header or per-line.

Do not write "오늘 +4bp" unless same-day semantics are valid.

Hard:

```text
LAGGED_UST_DATA_LABELED_SAME_DAY = 0
```

## 8.5 Precision

Use:
- yield `%`
- delta `bp`

No need to display both `%p` and `bp`.

Preserve source precision.

Hard:

```text
UST_DELTA_RENDERED_AS_PERCENT_RETURN = 0
```

## 8.6 Real-yield handling

The 10Y real yield may remain:
- internally available for macro reasoning if useful

but should no longer be the primary user-facing Treasury rate section.

Required:

```text
USER_FACING_PRIMARY_RATE_BLOCK = NOMINAL_3Y_5Y_10Y_30Y
```

## 8.7 Track C acceptance

Use frozen/archived test fixtures.

Required:

```text
all four maturities present or explicitly unavailable with exact cause
bp deltas correct
temporal labels correct
market numeric provenance PASS
```

Set:

```text
TRACK_C_US_MARKET = PASS / FAIL
```

---

# 9. Track D — Common Renderer Cleanup + Integration

## 9.1 Remove common disclaimer

Delete from KR and US V2 stock messages:

```text
※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.
```

Scope:

```text
BUY
HOLD
SELL
KR
US
```

Do not remove safety logic, decision classification, accepted ownership, or validation.

Required:

```text
COMMON_DISCLAIMER_OCCURRENCE_AFTER_REPAIR = 0
```

## 9.2 V2 block / legacy-body duplication review

Do not perform a large content redesign unless necessary.

At minimum:
- ensure no internal contradiction
- ensure V2 accepted block remains first-class
- quantify repeated text
- remove only obvious deterministic duplicate scaffolding if safely owned by renderer

Do not change core investment facts merely to shorten messages.

## 9.3 Decision consistency guard

Because US frozen replay previously showed different distributions across model executions:

```text
2 BUY / 9 HOLD / 3 SELL
vs
0 BUY / 11 HOLD / 3 SELL
```

add integration diagnostics:

per ticker:

```text
evidence fingerprint
prior accepted
fresh candidate
adjudication
fresh accepted
material evidence delta
```

Do not force deterministic model output.

Instead require:

```text
accepted decision changes
→ material evidence delta or valid adjudication
```

Set:

```text
UNEXPLAINED_ACCEPTED_DECISION_DRIFT = 0 / NONZERO
```

If nonzero:
do not final-merge as ready.

## 9.4 Preserve accepted-decision authority

Hard:

```text
RAW_CANDIDATE_USED_AS_FINAL = 0
DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED = 0
```

---

# 10. Sequential integration strategy

## 10.1 Track commits

Required:

```text
TRACK_A_COMMIT = ...
TRACK_B_COMMIT = ...
TRACK_C_COMMIT = ...
TRACK_D_COMMIT = ...
```

Each commit must be independently reviewable.

## 10.2 No premature main promotion

Preferred implementation:

```text
feature/integration branch
+
track commits in order
```

Promote to main only after all four tracks pass final gate.

If repository workflow requires intermediate main commits:
document why and retain rollback points.

---

# 11. Frozen regression controls

Use frozen artifacts where available from:

```text
US run-51
KR 2026-09-02 natural run
```

For data-dependent tests:
do not replace frozen evidence with fresh current data.

Network scheduler-context probe is allowed to use current connectivity because it tests the runtime transport itself.

Distinguish:

```text
frozen decision/data replay
vs
live network health probe
```

---

# 12. US production-equivalent test

Target reference cohort if unchanged:

```text
14
```

Exercise:

```text
scheduler-equivalent network/runtime
Codex app-server
actual model
candidate
validation
adjudication
accepted
renderer
final validator
```

Require:

```text
US_V2_CONTEXT_READY = 14
US_MODEL_REACHED = PASS
US_CANDIDATE_COUNT = 14
US_ACCEPTED_COUNT = 14
US_EXPLICIT_V2_COUNT = 14
US_FALLBACK_COUNT = 0
```

No forced BUY/HOLD/SELL distribution.

---

# 13. KR production-equivalent test

Reference cohort if unchanged:

```text
8
```

Require:

```text
KR_V2_CONTEXT_READY = 8
KR_MODEL_REACHED = PASS
KR_CANDIDATE_COUNT = 8
KR_ACCEPTED_COUNT = 8
KR_EXPLICIT_V2_COUNT = 8
KR_FALLBACK_COUNT = 0
```

Mandatory controls:

```text
047810 identifier
000660 valuation quality
005930 risk/reward
010120/012450 numerics
```

---

# 14. Controlled TEST-recipient send

After all functional/renderer gates pass:

send a production-equivalent message set to the existing dedicated non-production TEST recipient only.

Prefer:
- one US frozen set
- one KR frozen set

If executing both in one task would create excessive sends, use the repository-standard dedicated test sink and document exact coverage.

Hard:

```text
PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

Use real Telegram transport.

Require:
- exact payload
- duplicates 0
- acknowledged continuation on rate limit only

---

# 15. Production-state isolation

All replays/tests:

```text
production packet mutation = 0
production accepted mutation = 0
production assessment mutation = 0
production notification mutation = 0
production delivery-ledger mutation = 0
```

Test delivery must not suppress the next natural send.

---

# 16. Scheduler

Do not change:
- KR primary/backup/fallback times
- US primary/backup/fallback times
- packet ownership

If Track A requires a bounded runtime/network environment change:

record separately:

```text
SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0
SCHEDULER_RUNTIME_ENV_DIFF = DOCUMENTED_BOUNDED_DIFF
```

---

# 17. Full test gate

Require:

```text
Track A focused tests PASS
Track B focused tests PASS
Track C focused tests PASS
Track D focused tests PASS

US production-equivalent PASS
KR production-equivalent PASS

full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS

service health PASS
scheduler ownership/timing PASS
```

---

# 18. P0/P1 merge gate

Final merge only when:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Specifically:

```text
natural DNS/network runtime PASS
daily-review convergence PASS
night compact D/W/M PASS
UST 3Y/5Y/10Y/30Y PASS
common disclaimer removed
accepted ownership unchanged
unexplained decision drift = 0
US/KR production-equivalent PASS
test-recipient delivery PASS
```

---

# 19. Natural-live guard after merge

Do NOT manually replay historical packets to production.

Wait for ordinary natural runs.

Next KR natural proof:

```text
source ready
network preflight
app-server
model
candidate
accepted
explicit V2
fallback 0
9/9 exactly once if cohort 8
```

Next US natural proof:

```text
source ready
network preflight
model
candidate
accepted
explicit V2
fallback 0
market message includes:
  compact night D/W/M
  3Y/5Y/10Y/30Y nominal Treasury curve
15/15 exactly once if cohort 14
```

Test success is not natural LIVE_PASS.

---

# 20. Required architecture docs

Create/update:

```text
docs/architecture/CODEX_NATURAL_NETWORK_TRANSPORT_CONTRACT.md
docs/architecture/CODEX_TEST_LIVE_NETWORK_PARITY.md
docs/architecture/DAILY_REVIEW_SEMANTIC_BINDING_CONTRACT.md
docs/architecture/KRX_NIGHT_DWM_USER_DISPLAY_CONTRACT.md
docs/architecture/US_TREASURY_CURVE_MARKET_MESSAGE_CONTRACT.md
docs/architecture/V2_STOCK_MESSAGE_RENDERER_CONTRACT.md
docs/architecture/DECISION_ACCEPTED_OWNERSHIP.md
```

---

# 21. Required reports

At minimum:

## Track A
1. `docs/reports/20260902-natural-network-root-cause.md`
2. `docs/reports/20260902-test-live-network-environment-diff.md`
3. `docs/reports/20260902-scheduler-context-network-preflight.md`
4. `docs/reports/20260902-primary-backup-network-retry-proof.md`

## Track B
5. `docs/reports/20260902-daily-review-error-ledger.md`
6. `docs/reports/20260902-working-capital-signed-gap-controls.md`
7. `docs/reports/20260902-003690-holder-variable-control.md`
8. `docs/reports/20260902-valuation-economic-scope-controls.md`
9. `docs/reports/20260902-market-breadth-label-control.md`
10. `docs/reports/20260902-daily-review-convergence-replay.md`

## Track C
11. `docs/reports/20260902-night-compact-dwm-contract.md`
12. `docs/reports/20260902-night-daily-gap-baseline.md`
13. `docs/reports/20260902-night-weekly-monthly-return-controls.md`
14. `docs/reports/20260902-us-treasury-source-mapping.md`
15. `docs/reports/20260902-us-treasury-observation-pair.md`
16. `docs/reports/20260902-us-market-message-enriched-replay.md`

## Track D / integration
17. `docs/reports/20260902-common-disclaimer-removal.md`
18. `docs/reports/20260902-decision-consistency-integration.md`
19. `docs/reports/20260902-us-production-equivalent-final.md`
20. `docs/reports/20260902-kr-production-equivalent-final.md`
21. `docs/reports/20260902-test-recipient-integration-delivery.md`
22. `docs/reports/20260902-four-track-main-merge.md`
23. `docs/reports/20260902-four-track-natural-live-guard.md`
24. `docs/reports/20260902-four-track-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-network-proof.json
docs/reports/20260902-daily-review-proof.json
docs/reports/20260902-us-market-proof.json
docs/reports/20260902-decision-consistency-proof.json
docs/reports/20260902-four-track-readiness.json
```

---

# 22. Required gates

Set exactly:

```text
BASE_SHA =
...

BASE_CONTAINS_PREVIOUS_SAFE_REPAIRS =
PASS / FAIL

ALL_TRACKS_COLLAPSED_INTO_ONE_UNREVIEWABLE_COMMIT =
0 / NONZERO

CROSS_TRACK_SCOPE_CREEP =
0 / NONZERO

TRACK_A_COMMIT =
...

NATURAL_NETWORK_FAILURE_REPRODUCED =
PASS / FAIL

NATURAL_NETWORK_FIRST_FAILURE_BOUNDARY =
...

TEST_LIVE_NETWORK_FIRST_DIVERGENCE =
...

HARDCODED_PUBLIC_DNS =
0 / NONZERO

HOSTS_FILE_CHATGPT_OVERRIDE =
0 / NONZERO

TLS_VERIFICATION_DISABLED =
0 / NONZERO

GLOBAL_SECURITY_DISABLE =
0 / NONZERO

RUN_SCHEDULER_AS_ROOT =
0 / NONZERO

SCHEDULER_CONTEXT_NETWORK_PREFLIGHT =
PASS / FAIL

UNBOUNDED_NETWORK_RETRY =
0 / NONZERO

RETRY_STORM =
0 / NONZERO

PRIMARY_BACKUP_NETWORK_CONTRACT_IDENTICAL =
PASS / FAIL

TRACK_A_NETWORK_RUNTIME =
PASS / FAIL

TRACK_B_COMMIT =
...

SIGNED_GAP_DIRECTION_INVERTED =
0 / NONZERO

SIGNED_GAP_PERCENT_VS_PP_CONFUSION =
0 / NONZERO

003690_HOLDER_VARIABLE_BINDING =
PASS / FAIL

000660_VALUATION_SCOPE =
PASS / FAIL

010120_VALUATION_SCOPE =
PASS / FAIL

012450_VALUATION_SCOPE =
PASS / FAIL

000660_VALUATION_QUALITY_GUARD =
PASS / FAIL

005930_RISK_REWARD_GUARD =
PASS / FAIL

047810_IDENTIFIER_PROVENANCE =
PASS / FAIL

MARKET_BREADTH_AUTHORED_LABEL_CONFLICT =
0 / NONZERO

DAILY_REVIEW_CORRECTION_CHANGES_V2_ACCEPTED =
0 / NONZERO

DAILY_REVIEW_UNBOUND_NUMERIC_AFTER_CORRECTION =
0 / NONZERO

DAILY_REVIEW_REPAIR_LOOP_UNBOUNDED =
0 / NONZERO

TRACK_B_DAILY_REVIEW =
PASS / FAIL

TRACK_C_COMMIT =
...

CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME =
0 / NONZERO

DAILY_GAP_BASELINE_INVENTED =
0 / NONZERO

DAILY_GAP_AND_RETURN_USE_DIFFERENT_UNDISCLOSED_BASELINES =
0 / NONZERO

IN_PROGRESS_WEEKLY_LABELED_FINAL =
0 / NONZERO

IN_PROGRESS_MONTHLY_LABELED_FINAL =
0 / NONZERO

NIGHT_DAILY_OPEN_CLOSE_GAP_RETURN =
PASS / FAIL

NIGHT_WEEKLY_OPEN_CLOSE_RETURN =
PASS / FAIL

NIGHT_MONTHLY_OPEN_CLOSE_RETURN =
PASS / FAIL

NIGHT_DWM_NUMERIC_PROVENANCE =
PASS / FAIL

MULTI_CONTRACT_DWM_SPLICING =
0 / NONZERO

UST_3Y_SOURCE =
PROVEN / FAIL

UST_5Y_SOURCE =
PROVEN / FAIL

UST_10Y_SOURCE =
PROVEN / FAIL

UST_30Y_SOURCE =
PROVEN / FAIL

UST_OBSERVATION_PAIR_VALID =
PASS / FAIL

LAGGED_UST_DATA_LABELED_SAME_DAY =
0 / NONZERO

UST_DELTA_RENDERED_AS_PERCENT_RETURN =
0 / NONZERO

USER_FACING_PRIMARY_RATE_BLOCK =
NOMINAL_3Y_5Y_10Y_30Y / OTHER

TRACK_C_US_MARKET =
PASS / FAIL

TRACK_D_COMMIT =
...

COMMON_DISCLAIMER_OCCURRENCE_AFTER_REPAIR =
0 / NONZERO

RAW_CANDIDATE_USED_AS_FINAL =
0 / NONZERO

DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED =
0 / NONZERO

UNEXPLAINED_ACCEPTED_DECISION_DRIFT =
0 / NONZERO

US_V2_CONTEXT_READY =
14 / OTHER

US_MODEL_REACHED =
PASS / FAIL

US_CANDIDATE_COUNT =
14 / OTHER

US_ACCEPTED_COUNT =
14 / OTHER

US_EXPLICIT_V2_COUNT =
14 / OTHER

US_FALLBACK_COUNT =
0 / NONZERO

KR_V2_CONTEXT_READY =
8 / OTHER

KR_MODEL_REACHED =
PASS / FAIL

KR_CANDIDATE_COUNT =
8 / OTHER

KR_ACCEPTED_COUNT =
8 / OTHER

KR_EXPLICIT_V2_COUNT =
8 / OTHER

KR_FALLBACK_COUNT =
0 / NONZERO

US_PRODUCTION_EQUIVALENT =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT =
PASS / FAIL

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

TEST_RECIPIENT_DELIVERY =
PASS / FAIL

SCHEDULER_TIMING_DIFF =
0 / NONZERO

SCHEDULER_OWNERSHIP_DIFF =
0 / NONZERO

SCHEDULER_RUNTIME_ENV_DIFF =
0 /
DOCUMENTED_BOUNDED_DIFF /
UNSAFE_DIFF

FULL_TESTS =
PASS / FAIL

RUFF =
PASS / FAIL

GIT_DIFF_CHECK =
PASS / FAIL

ACTIONS =
PASS / FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

FOUR_TRACK_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 23. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_COMMIT = ...
TRACK_A_NETWORK_RUNTIME = ...
NETWORK_ROOT_CAUSE = ...
NETWORK_REPAIR = ...
SCHEDULER_CONTEXT_NETWORK_PREFLIGHT = ...

TRACK_B_COMMIT = ...
TRACK_B_DAILY_REVIEW = ...
SIGNED_GAP = ...
003690_HOLDER = ...
VALUATION_SCOPE = ...
BREADTH_LABEL = ...

TRACK_C_COMMIT = ...
TRACK_C_US_MARKET = ...

NIGHT_DISPLAY =
Daily open/close/gap/return ...
Weekly open/close/weekly ...
Monthly open/close/monthly ...

TREASURY_CURVE =
3Y ...
5Y ...
10Y ...
30Y ...
source ...
observation dates ...

TRACK_D_COMMIT = ...
DISCLAIMER_REMOVED = ...
UNEXPLAINED_ACCEPTED_DECISION_DRIFT = ...

US =
context ...
model ...
candidate ...
accepted ...
explicit ...
fallback ...

KR =
context ...
model ...
candidate ...
accepted ...
explicit ...
fallback ...

TEST_RECIPIENT_DELIVERY = ...
PRODUCTION_RECIPIENT_SEND = 0

FULL_TESTS = ...
RUFF = ...
GIT_DIFF_CHECK = ...
ACTIONS = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0
SCHEDULER_RUNTIME_ENV_DIFF = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

FOUR_TRACK_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_LIVE /
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 24. Mandatory completion ZIP

Create:

`20260902-four-track-stabilization-network-dailyreview-market-renderer-bundle.zip`

Include:
- exact master instruction
- all four track instructions
- all track commits/diffs
- network root-cause evidence
- scheduler-context network preflight
- primary/backup retry proof
- daily-review exact error ledger
- semantic/provenance controls
- night compact D/W/M proof
- Treasury source/observation proof
- common disclaimer removal proof
- decision-consistency report
- US/KR production-equivalent results
- test-recipient delivery receipts
- CI/main/deployment reports
- machine-readable JSON
- artifact index

Exclude:
- Telegram recipient IDs
- auth/session tokens
- Codex credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 25. Final principle

One master plan is acceptable.

One giant undifferentiated code change is not.

The implementation must preserve fault isolation:

```text
A. transport/runtime
B. semantic/provenance
C. market data/UI
D. renderer/integration
```

Each track must pass independently before final integration.

Do not hide transport failure with fallback.
Do not hide semantic failure by weakening validators.
Do not hide market-data uncertainty by inventing numbers.
Do not change accepted-decision policy merely to stabilize model output.

Only after all four tracks pass:
merge,
deploy,
and wait for ordinary KR/US natural live proof.
