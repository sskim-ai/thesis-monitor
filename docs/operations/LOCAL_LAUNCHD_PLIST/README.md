# Local LaunchAgent Drafts (Not Installed)

Status: offline implementation only. No LaunchAgent was copied, bootstrapped,
enabled, started or disabled by this task. No operating DB, account Lane,
financial provider or model was accessed. Existing monitor_daily and paused
09:00 jobs are untouched. Do not infer actual installation from these files.

The operator-managed configuration is local operational intent, not an external
signature, daily human approval, persistent grant or serialized Owner. Every
consumed market/session creates an original in-memory ApprovalDecision and
OperatorApproval, original registration capture/ProspectiveOwner, and existing
SelectedRunLedger. The only analysis path is run_registered -> original Source
Seal/Cold/Census/ModelPlan -> production factory -> Sol High -> B/B2 -> Renderer.

## Paths and Preparation for a Later Authorized Installation

Use this dedicated clean worktree, not the dirty operating main checkout:
`/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-pr52-local-launchd-20261119`.
The interpreter is the existing operating venv absolute path in each plist.
Keep the worktree/ref; removing it breaks this draft. No sys.path insertion or
expired maintenance caller/session/campaign is used.

After separate installation and recurring usage approval, prepare private
`data/local-launchd` and `logs` directories (0700). The example is DISABLED and
its zero hashes are deliberate placeholders, not deployable credentials or
approved configuration. Write operator-owned 0600 us.json; set code_commit to
the exact clean local commit. For KR, use market=kr and a separate kr.json,
kr-endpoints.json, omit auxiliary_issuer, and retain the same run_root/lease.
Do not change run_root to evade an existing session intent/STOP.

Prepare existing ProductionSourceConfiguration (not a new schema), the existing
qualified CurrentOfficialCodexBinding JSON, and static endpoint maps under the
declared hash-bound paths. Endpoint maps are provider -> original RuntimeCap
rules (host/prefix/methods/endpoint), not whole historical campaign grants.
Only declared public protocols/identity routing are copied. For US, the public
000660 SecurityMaster-shaped identity is ISSUER_CONTEXT only, not a new SKHY
investment basis. Native inspector, current Settings DB identity and original
plan/Source validators still have to pass. Do not invent identities, reuse old
Owner handles, omit Source checks, or reset account STOPs to fill placeholders.

The reviewed binding's HOME/PATH/CODEX_HOME is reused; authentication/provider
overrides are still rejected by its original validator. No keys in plist or
configuration. Settings reads the existing env file only after enabled/calendar
and dedup gates. Never put .env, auth files or private Thesis into result ZIPs.

## Fixed Limits and Dedup

US: Source <=1800s, physical HTTP <=710 (Kiwoom552, SEC86, Finnhub28,
Google14, FRED13, KRX7, DART6, EIA3, ECOS1), Sol gpt-6.1-sol/high <=30,
600s per call, one shared B2 timeout retry inside that cap. Optional Google429
uses SELECTED_US_OPTIONAL_NEWS_429_V1 only. No new fee/paid-plan authority.
KR: Source600s, HTTP332 (Kiwoom190, KIS85, DART48, Naver8, ECOS1), models18,
600s per call, retry0. Model input384KiB/output128KiB and Repair0 are unchanged.
Both: original Owner expiry and 4h30 campaign ceiling, shorter deadline wins.

The existing shared pair lease excludes other participating callers. Original
account Lane is required; no recovery/reset/epoch transition. Fixed
`runs/<market>-<XNYS-or-XKRX-completed-session>` uses cycle.lock, immutable intent,
campaign.jsonl and terminal.json. Any prior intent/journal/terminal/STOP consumes
the session even after a crash; there is no restart/refill/backup campaign.
Required final bars/provider completion are checked by original Source, not
inferred from clock alone. Missing inputs cannot reach the model or NO-SEND.

## Schedule Caveat

US draft is literally Monday-Friday **KST06:10**, KR Monday-Friday KST15:35.
Mac timezone must be Asia/Seoul at installation. US Monday KST is NY Sunday and
will NO_RUN; US Friday closes on KST Saturday, which this requested schedule
does not cover. Confirm Tue-Sat KST if all five US sessions are intended; this
task has NOT silently changed the requested weekdays. XNYS/XKRX holidays and
not-yet-closed sessions do not fall back to yesterday's session.

08:10/16:10 are best-effort readiness goals, not SEND or completion guarantees.
The Mac must be powered on, user logged in, timezone correct, and awake with
network/credentials available. launchd may defer a sleeping Mac's trigger;
calendar/Source/dedup gates still apply. No power or clock settings are changed.

## Later Installation / Cancellation (NOT Executed)

First activate US NO-SEND only after explicit installation and recurring
financial/model cap approval, deployment configuration review, and a check for
other active jobs. Validate syntax and matching hashes, then install the US
plist under the current user's ~/Library/LaunchAgents with its exact label.
`launchctl bootstrap gui/$(id -u) <installed-plist>` loads the next eligible
trigger; RunAtLoad=false and KeepAlive=false. Never kickstart in this step.
Do not install backup triggers. KR installation requires its own review.

Inspect later with `launchctl print gui/$(id -u)/local.thesis-monitor.canonical.us.no-send`.
Cancel only that label with `launchctl bootout gui/$(id -u)/local.thesis-monitor.canonical.us.no-send`
and `launchctl disable gui/$(id -u)/local.thesis-monitor.canonical.us.no-send`.
Use the .kr. label for KR. These commands are instructions only; this task did
not execute launchctl, modify existing jobs, install services, or send messages.
