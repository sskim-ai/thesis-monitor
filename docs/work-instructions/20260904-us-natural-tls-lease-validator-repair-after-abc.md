# thesis-monitor — 2026-09-04 US Natural AI Repair
## TLS trust + claim lease renewal / backup fencing + validator-22 repair
## Execute ONLY after the currently-running Structured Autonomy A/B/C experiment is fully terminal
## Production-like TEST proof first; natural production proof remains separate

---

# 0. Mission

Repair the actual failure chain observed in the 2026-09-04 US natural monitoring run.

Authoritative natural facts:

```text
packet =
2026-09-04-us-run-55-54cd536c6e4d

operating revision =
5d5f3363d3a762b62698943b1feb4fa121d0d0f9

primary candidate =
market 1 + stocks 14
SHA =
3dfaea9ce0643e56a676b6740cae7aedab2a7f01fdff090265923c4562d4b276

backup first candidate SHA =
fa1499059847e3a1bd3283fef2e266385960e4e1e18550f9f41e9cd0d9f24d11

backup corrected candidate SHA =
29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b
```

Natural failure chain:

```text
08:15:45  primary starts

~08:16:06
primary claim acquired
lease = 10 minutes

~08:26:06
static lease expires
primary process is still active

08:29:47
primary authored full 15-part review candidate

08:30:09
primary claim-scoped xhigh V2 canary starts

08:30:13
raw TLS error = UnknownIssuer

08:30:15
scheduled backup starts

08:30:39
backup reclaims expired primary claim
same packet / shared delivery ownership domain

08:33:37
backup V2 canary starts

08:33:41
same UnknownIssuer

08:35:20
primary attempts validation/finalization
→ stale_claim_output

08:37:15
backup first candidate rejected

08:41:48
backup corrected candidate rejected
→ 22 remaining validator errors

08:40 fallback path
→ deterministic messages 15/15 exactly once
→ duplicate 0
```

There was:

```text
NO 08:20 primary-missing checker
NO 08:20 false liveness flag
NO shadow interference with natural US
```

Do not repair a nonexistent 08:20 checker.

---

# 1. Current ABC hard wait gate

A Structured Autonomy A/B/C experiment is currently running.

This repair MUST NOT start while that experiment still owns or may own:

```text
signed-in Codex CLI
Codex app-server
shared CODEX_HOME
model concurrency
runtime locks
temporary claim/model directories
heavy CPU/memory resources
```

Before doing ANY repair implementation or model/network test, establish:

```text
CURRENT_ABC_TERMINAL = PASS
CURRENT_ABC_MODEL_PROCESSES = 0
CURRENT_ABC_APP_SERVER_RELEASED = PASS
CURRENT_ABC_ARTIFACTS_PERSISTED = PASS
CURRENT_ABC_WORKTREE_STATE_CAPTURED = PASS
```

If not all PASS:

```text
WAIT
```

Do not:
- kill ABC
- shorten ABC
- reuse ABC app-server
- share its model process
- change its prompt/schema
- inspect partial ABC outcomes and retune this repair

The user will run this task after ABC is done.

---

# 2. Branch / worktree isolation

Create a separate repair branch/worktree.

Suggested:

```text
codex/20260904-us-natural-tls-lease-validator-repair
```

Do not continue directly inside the Structured Autonomy shadow branch.

Production-base selection rule:

1. Identify the exact code ancestry of natural operating revision:
   `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`.
2. Identify any later production-path repair commits already meant for main.
3. Do NOT automatically import shadow-only Structured Autonomy experiments.
4. Choose the narrowest production descendant that contains required existing live-path fixes.
5. Record exact base SHA before implementation.

Required:

```text
BASE_CONTAINS_NATURAL_OPERATING_REVISION = PASS
SHADOW_ONLY_DECISION_CONTRACT_IMPORTED = 0
```

Make the work-instruction commit first.

---

# 3. Repair Track B — TLS trust root cause

The natural claim-scoped signed-in CLI:

```text
Codex 0.148.0-alpha.15
gpt-5.6-sol
xhigh
read-only sandbox
```

reproduced raw:

```text
UnknownIssuer
```

on BOTH primary and backup V2 canaries.

The outer review-authoring automation completed, but the nested claim-scoped signed-in CLI transport did not.

The TLS issue is therefore real and production-relevant.

---

# 4. TLS repair principles

Forbidden:

```text
NODE_TLS_REJECT_UNAUTHORIZED=0
--insecure
curl -k
disable certificate verification
accept-all certificate callback
global trust-store bypass
hardcoded private certificate
secret/token copying
```

Do not make the error disappear by weakening TLS.

The repair must establish why the approved signed-in CLI cannot validate the actual peer chain.

Compare, without exposing secrets:

```text
CLI binary/path/version
launch wrapper
sandbox mode
CODEX_HOME
HOME
PATH
SSL_CERT_FILE
SSL_CERT_DIR
REQUESTS_CA_BUNDLE
CURL_CA_BUNDLE
HTTPS_PROXY / HTTP_PROXY / ALL_PROXY presence
NO_PROXY semantics
system trust/keychain access
working-directory sandbox boundary
app-server environment
Desktop automation environment
claim-scoped CLI environment
```

Record only:
- variable present/absent
- path identity if non-secret
- trust-store source
- SHA/metadata where useful

Do not expose tokens or proxy credentials.

---

# 5. TLS chain evidence

Using an approved non-mutating diagnostic path, determine:

```text
peer certificate chain observable?
issuer chain complete?
root/intermediate trusted?
system trust differs from CLI trust?
proxy/interception certificate present?
sandbox loses system keychain access?
CLI bundles its own CA?
```

Do not use public web as a substitute for the runtime's actual trust path.

If a corporate/local interception certificate exists:
- do not export/share its private key
- do not embed certificate material in repo
- use approved OS/runtime trust integration only

---

# 6. TLS transport preflight contract

After repair, before ANY 15-name model run:

execute ONE minimal signed-in CLI preflight using the SAME production-equivalent runtime:

```text
same CLI binary/version family
same CODEX_HOME policy
same sandbox/read-only policy
same app-server launch path
same model endpoint path
same authentication mode
```

No production packet.
No Telegram.
No scheduler mutation.
No DB mutation.

Required:

```text
TLS_PREFLIGHT_MODEL_RESULT_COUNT = 1
TLS_UNKNOWN_ISSUER = 0
TLS_CERTIFICATE_VERIFY_ERROR = 0
CLI_EXIT_CODE = 0
```

If preflight fails:

```text
STOP
```

Do not attempt full US E2E.

---

# 7. Transport error classifier repair

Current wrapper misclassifies:

```text
UnknownIssuer
```

because it recognizes an equivalent marker such as:

```text
unknown issuer
```

but not the raw token form.

Add a normalized transport-error taxonomy.

Required equivalent classes:

```text
TLS_CERTIFICATE_UNKNOWN_ISSUER
TLS_CERTIFICATE_EXPIRED
TLS_CERTIFICATE_HOSTNAME_MISMATCH
TLS_CERTIFICATE_OTHER
DNS_FAILURE
CONNECT_TIMEOUT
CONNECTION_REFUSED
LOCAL_NETWORK_CONNECTIVITY_FAILURE
OTHER_TRANSPORT_FAILURE
```

`UnknownIssuer` must classify specifically as:

```text
TLS_CERTIFICATE_UNKNOWN_ISSUER
```

not:

```text
LOCAL_NETWORK_CONNECTIVITY_FAILURE
```

Preserve raw diagnostic token in audit metadata.

No user-visible secret/error dump.

---

# 8. Fail-fast transport semantics

A deterministic TLS certificate failure should not burn multiple minutes of the primary claim lease through useless reconnect loops.

Use repository-native retry policy, but classify permanent certificate-validation errors as non-retriable or tightly bounded.

Required:

```text
UNKNOWN_ISSUER_RETRY_STORM = 0
```

Do not broadly disable all network retries.
Only distinguish permanent certificate failures from transient transport failures.

---

# 9. Repair Track C — claim lease / backup fencing root cause

Natural primary had:

```text
10-minute static lease
no liveness grace / heartbeat predicate on this path
```

Primary remained active after lease expiry.

Backup reclaimed the same packet at 08:30:39 because:

```text
lease expired
AND
no final output existed
```

This caused primary finalization to be fenced as:

```text
stale_claim_output
```

The repair must prevent an actively progressing primary from losing ownership solely because a static lease clock elapsed.

---

# 10. Do NOT solve lease by duration-only inflation

Forbidden as sole repair:

```text
10 minutes → 30 minutes
10 minutes → 60 minutes
```

A longer static timeout only moves the race.

A duration increase may be an additional safety margin,
but the primary repair must be active ownership renewal / liveness-aware fencing.

---

# 11. Required claim contract

Claim ownership must have repository-native equivalents of:

```text
claim_owner
fencing_token / claim_generation
lease_expires_at
last_heartbeat_at / last_renewed_at
terminal_state
```

The active worker must renew its own lease while performing legitimate work.

Renewal must require:

```text
current owner == worker owner
AND
current fencing token == worker fencing token
```

If ownership changed:
- renewal fails
- stale worker cannot write accepted/delivery state
- stale worker should stop at the next safe boundary

---

# 12. Heartbeat independence from blocking model calls

The 2026-09-04 primary spent several minutes inside a nested CLI call.

Lease renewal must continue even while:
- model subprocess is running
- validator is running
- correction subprocess is running

Do not design heartbeat logic that can only execute after the blocking subprocess returns.

Preferred repository-native patterns:
- background lease-renewal task/thread
- async subprocess with renewal loop
- parent watchdog that renews while child is alive

The renewal interval must be safely below lease expiry.

Do not hardcode a magic interval if configuration already exists.

---

# 13. Backup reclaim predicate

Scheduled backup must NOT reclaim an actively healthy primary merely because:

```text
lease_expires_at < now
```

Preferred semantics:

```text
lease expired
AND
owner heartbeat stale/missing
AND
owner process/session no longer valid under available runtime evidence
AND
no accepted/pending terminal ownership already exists
```

Use only signals available in the actual production environment.

Do not require PID inspection if jobs may run across isolated processes/hosts and PID is not authoritative.

Persisted heartbeat/fencing state should be authoritative where possible.

---

# 14. Backup behavior while primary healthy

At 08:30, if primary owns the claim and heartbeat is fresh:

```text
BACKUP_ACTION =
SAFE_NOOP_PRIMARY_ACTIVE
```

or a repository-native defer/retry state.

Do not:
- start a second model call
- replace claim owner
- clone delivery ownership
- mutate primary candidate

Backup may remain available to reclaim later if primary actually dies/stalls.

---

# 15. Correct reclaim behavior

Add a controlled failure test:

```text
primary claims packet
primary heartbeat stops
lease expires
backup schedule/retry executes
```

Expected:

```text
backup reclaim = PASS
new fencing token = PASS
old primary write rejected = PASS
backup can finish = PASS
duplicate delivery = 0
```

Lease repair must not make backup impossible.

---

# 16. Fallback remains independent safety boundary

Do not remove the 08:40 deterministic fallback safety.

If AI is not accepted/delivered by the hard deadline:

```text
fallback may send 15/15
```

After fallback terminal:
- late AI may be archived
- late AI may NOT send duplicates

Required:

```text
LATE_AI_AFTER_FALLBACK_SENT = 0
DUPLICATE_SENT = 0
```

---

# 17. Repair Track D — validator 22-error decomposition

The corrected backup candidate:

```text
SHA =
29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b
```

still had `22` authoritative validation errors.

Forensic category counts:

```text
holder decision-variable errors = 2
working-capital ownership errors = 2
market semantic/provenance errors = 2
typed valuation coverage/metric errors = 16
```

Do NOT weaken the validator globally.

---

# 18. Extract exact 22 errors first

Before code changes, locate the authoritative corrected-candidate validation archive and produce a table:

```text
error_id
ticker/market scope
text_ref
fact_id
field_path
validator rule
rendered span
candidate claim
available canonical evidence
class
```

Classify every error as exactly one:

```text
TRUE_CANDIDATE_VIOLATION
VALIDATOR_FALSE_POSITIVE
SCHEMA_OWNERSHIP_MISMATCH
RENDERER_OWNERSHIP_MISMATCH
CORRECTION_CONTEXT_DEFECT
PROVENANCE_BINDING_DEFECT
OTHER
```

Required:

```text
ERRORS_CLASSIFIED = 22/22
UNCLASSIFIED = 0
```

---

# 19. Validator repair principles

For `VALIDATOR_FALSE_POSITIVE`:
- repair validator semantics generically
- add exact regression fixture
- add neighboring true-positive fixture

For `TRUE_CANDIDATE_VIOLATION`:
- keep validator strict
- constrain authoring schema/prompt/correction context
- do not whitelist the bad sentence

For `SCHEMA_OWNERSHIP_MISMATCH`:
- move responsibility to structured field / typed reference where appropriate

For `PROVENANCE_BINDING_DEFECT`:
- fix exact reference/semantic ownership
- do not allow free numeric prose

Ticker-specific exception count must remain:

```text
0
```

---

# 20. Holder decision-variable errors

For the 2 holder decision-variable errors, determine whether:
- prose invented an action state
- holder field was missing/incorrect
- deterministic state already existed but prose used a conflicting variable
- validator expected a typed holder reference

Do not make holder decisions from price alone.

Preserve distinction:
- business investment logic
- price review
- holder management state

No mandatory sell-order language.

---

# 21. Working-capital ownership errors

For the 2 working-capital errors:

Do not infer:
- DSO
- DPO
- CCC
- receivable quality
- inventory quality

unless the packet explicitly supports them.

If the candidate only says the metric is Unknown / should be checked:
make sure the schema identifies it as a future validation item rather than a current observed fact.

Reuse the evidence-grounding philosophy:

```text
CURRENT_METRIC_CLAIM
vs
FUTURE_CHECKPOINT
vs
UNKNOWN
```

Do not silently calculate missing working-capital metrics.

---

# 22. Market semantic/provenance errors

For the 2 market errors:

Require exact mapping between:
- instrument
- semantic type
- unit
- comparison role
- fact_id / field_path
- rendered span

Do not treat:
- sector relative return
- index return
- futures return
- yield change
as interchangeable.

No number may survive solely because the formatted value matches.

---

# 23. Typed valuation coverage/metric errors

For the 16 valuation errors, classify by:
- metric identity
- trailing vs forward
- historical vs current
- PER vs PBR
- provider vs derived
- ordinary vs ADR/security basis
- numeric ref
- interpretation span
- Unknown/quality claim
- coverage requirement

Do not solve by:
- suppressing all valuation
- relaxing typed coverage
- accepting same number with wrong semantic
- back-calculating missing EPS/BVPS
- using provider multiple to derive denominator

Where one value can represent more than one semantic:
the selected reference must match the actual sentence semantics.

---

# 24. Correction pass

Keep a bounded correction contract.

Do not increase correction retries merely to force acceptance.

Preferred:

```text
candidate
→ authoritative validation
→ structured correction context
→ at most existing permitted correction count
→ final validation
```

After repair, the frozen corrected-candidate regression should validate if and only if its remaining errors were contract defects, not genuine unsupported claims.

Document any genuine candidate violations that remain rejected.

---

# 25. Frozen deterministic validator replay

Validator debugging may replay the frozen candidate through the validator OFFLINE.

This is allowed:

```text
MODEL_RERUN = 0
TELEGRAM_SEND = 0
DATA_REFETCH = 0
```

Use:
- frozen packet
- frozen candidate
- frozen reference registry

Do not regenerate model text to make tests pass.

---

# 26. Cross-track ordering

Execute in this order:

```text
A. wait for current ABC terminal
B. create isolated production repair worktree
C. TLS root-cause + classifier fix
D. minimal TLS signed-in CLI preflight
E. lease renewal / backup fencing
F. validator 22-error decomposition
G. validator/schema/correction repairs
H. focused unit/contract tests
I. real production-entrypoint TEST E2E
J. full suite + reports
```

If TLS preflight fails:
- continue deterministic code/unit work if useful
- do NOT claim end-to-end readiness
- do NOT run model-consuming E2E

---

# 27. Unit / contract test layers

Layer 1 — TLS classifier:

```text
UnknownIssuer
unknown issuer
certificate verify failed
expired certificate
hostname mismatch
DNS failure
timeout
```

Correct class for each.

Layer 2 — claim state machine:
- renew same fencing token
- reject foreign fencing token
- fresh heartbeat blocks backup
- stale heartbeat allows backup
- stale primary cannot finalize
- fallback terminal blocks late AI send

Layer 3 — validator:
- exact 22 incident fixtures
- true-positive neighbors
- previous accepted-good fixtures
- numeric/provenance safety
- ADR/security basis
- Unknown semantics

---

# 28. Real production-entrypoint E2E

Synthetic simplified candidate tests do NOT count as release proof.

Run one true live-path E2E using:
- real US production entrypoint
- real packet builder / selector / accepted-plan finalizer
- real claim/lease state machine
- real signed-in CLI path
- real retry/fallback orchestration
- real Telegram adapter
- dedicated NON-PRODUCTION TEST recipient

No production recipient.

No production scheduler mutation.

---

# 29. E2E success scenario

Required:

```text
source ready = 15/15 relevant scopes
primary claim acquired
lease renewals observed
backup at backup-window sees fresh primary
backup action = SAFE_NOOP_PRIMARY_ACTIVE

signed-in xhigh result > 0
UnknownIssuer = 0

candidate = 15
final validation = PASS
accepted = 15

AI market sent to TEST = 1
AI stocks sent to TEST = 14

fallback = 0
duplicate = 0
```

Exact decision distribution is NOT a readiness target.

---

# 30. E2E long-running primary scenario

Force or simulate a production-equivalent model duration longer than the original 10-minute lease boundary without changing judgment output.

Expected:

```text
heartbeat renewals continue
lease remains owned by primary
backup does not reclaim
primary finalizes with same fencing token
```

Do not require an actual 10+ minute paid wait if the state machine can use a controlled clock in a production-equivalent integration harness.

But at least one real signed-in CLI success must still be proven separately.

---

# 31. E2E primary-death scenario

Controlled:

```text
primary claims
heartbeat stops
lease expires
backup executes
```

Expected:

```text
backup reclaim = 1
old primary finalization = fenced
backup accepted = 15
TEST send = 15
fallback = 0
duplicate = 0
```

---

# 32. E2E TLS failure scenario

Inject/mock classifier-level `UnknownIssuer` without weakening TLS.

Expected:

```text
class = TLS_CERTIFICATE_UNKNOWN_ISSUER
retry storm = 0
accepted AI = 0
fallback eligibility preserved
duplicate = 0
```

Do NOT alter OS trust just to create this test.

---

# 33. E2E fallback / late AI scenario

Controlled late primary:

```text
fallback reaches hard deadline first
fallback sends 15
primary later completes
```

Expected:

```text
fallback sent = 15
late AI sent = 0
duplicate = 0
late AI state = archived/superseded/deduped equivalent
```

---

# 34. Do not mix Structured Autonomy shadow contract

This repair addresses the production US natural daily-review/AI-assisted delivery path.

Do NOT make production natural acceptance depend on unfinished Structured Autonomy shadow promotion.

Required:

```text
STRUCTURED_AUTONOMY_PRODUCTION_PROMOTION = 0
```

The current ABC experiment remains a separate decision-structure program.

---

# 35. Tests

Run:

```text
focused TLS trust/classifier tests
focused claim/lease/fencing tests
focused backup/fallback tests
focused exact 22 validator incident tests
focused valuation/provenance tests
focused US AI-assisted delivery tests
real production-entrypoint TEST E2E

full pytest
Ruff
git diff --check
secret scan
```

If exact-SHA CI exists:
- implementation SHA CI
- final/report SHA CI

No deleting tests to get green.

---

# 36. Production mutation rules

During this repair:

```text
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
PRODUCTION_DB_MUTATION = 0
MAIN_MERGE = 0
```

Code changes may be committed/pushed to the repair branch only.

Any TEST delivery must use dedicated non-production recipient.

---

# 37. Natural proof remains separate

Even after E2E PASS:

```text
READY_FOR_NATURAL_PROOF
```

is the strongest allowed pre-merge operational verdict.

Next natural US production proof should require:

```text
primary signed-in transport succeeds
AI market = 1
AI stocks = 14
fallback = 0
duplicate = 0

backup does not reclaim fresh primary

accepted count = 15
pending reaches terminal
```

If natural primary genuinely dies:
backup recovery may be valid, but must remain exactly-once.

---

# 38. Required reports

Create:

1. `docs/reports/20260904-us-repair-base-selection.md`
2. `docs/reports/20260904-current-abc-terminal-preflight.md`
3. `docs/reports/20260904-us-tls-runtime-differential.md`
4. `docs/reports/20260904-us-tls-chain-root-cause.md`
5. `docs/reports/20260904-us-transport-error-taxonomy.md`
6. `docs/reports/20260904-us-signed-in-cli-tls-preflight.md`
7. `docs/reports/20260904-us-claim-lease-renewal-contract.md`
8. `docs/reports/20260904-us-backup-reclaim-fencing-contract.md`
9. `docs/reports/20260904-us-fallback-late-ai-contract.md`
10. `docs/reports/20260904-us-validator-22-error-inventory.md`
11. `docs/reports/20260904-us-holder-decision-variable-repair.md`
12. `docs/reports/20260904-us-working-capital-ownership-repair.md`
13. `docs/reports/20260904-us-market-semantic-provenance-repair.md`
14. `docs/reports/20260904-us-typed-valuation-coverage-repair.md`
15. `docs/reports/20260904-us-correction-contract.md`
16. `docs/reports/20260904-us-live-path-e2e-success.md`
17. `docs/reports/20260904-us-live-path-e2e-failure-matrix.md`
18. `docs/reports/20260904-us-repair-readiness.md`
19. `docs/reports/20260904-us-repair-artifact-index.md`

Machine-readable:

```text
20260904-us-transport-proof.json
20260904-us-claim-lease-proof.json
20260904-us-validator-22-proof.json
20260904-us-live-path-e2e-proof.json
20260904-us-repair-proof.json
```

---

# 39. Required gates

```text
CURRENT_ABC_TERMINAL =
PASS / FAIL

CURRENT_ABC_MODEL_PROCESSES =
0 / NONZERO

CURRENT_ABC_APP_SERVER_RELEASED =
PASS / FAIL

BASE_SHA =
...

BASE_CONTAINS_NATURAL_OPERATING_REVISION =
PASS / FAIL

SHADOW_ONLY_DECISION_CONTRACT_IMPORTED =
0 / NONZERO

TLS_ROOT_CAUSE_IDENTIFIED =
PASS / FAIL

TLS_VERIFICATION_BYPASS =
0 / NONZERO

TLS_PREFLIGHT_MODEL_RESULT_COUNT =
1 / OTHER / NOT_RUN

TLS_UNKNOWN_ISSUER =
0 / NONZERO

UNKNOWN_ISSUER_CLASSIFICATION =
TLS_CERTIFICATE_UNKNOWN_ISSUER / OTHER

UNKNOWN_ISSUER_RETRY_STORM =
0 / NONZERO

CLAIM_RENEWAL_IMPLEMENTED =
PASS / FAIL

CLAIM_FENCING_TOKEN =
PASS / FAIL

HEARTBEAT_SURVIVES_BLOCKING_MODEL_CALL =
PASS / FAIL

FRESH_PRIMARY_BLOCKS_BACKUP_RECLAIM =
PASS / FAIL

STALE_PRIMARY_ALLOWS_BACKUP_RECLAIM =
PASS / FAIL

STALE_PRIMARY_FINALIZATION_REJECTED =
PASS / FAIL

FALLBACK_LATE_AI_DUPLICATE =
0 / NONZERO

VALIDATOR_INCIDENT_ERRORS_FOUND =
22 / OTHER

VALIDATOR_INCIDENT_ERRORS_CLASSIFIED =
22 / OTHER

TICKER_SPECIFIC_VALIDATOR_EXCEPTION =
0 / NONZERO

VALIDATOR_GLOBAL_WEAKENING =
0 / NONZERO

UNSUPPORTED_NUMERIC_ACCEPTED =
0 / NONZERO

ADR_SECURITY_BASIS_SAFETY =
PASS / FAIL

US_TEST_E2E_PRIMARY_ACCEPTED =
15 / OTHER / NOT_RUN

US_TEST_E2E_AI_MARKET_SENT =
1 / OTHER / NOT_RUN

US_TEST_E2E_AI_STOCK_SENT =
14 / OTHER / NOT_RUN

US_TEST_E2E_FALLBACK_SENT =
0 / NONZERO / NOT_RUN

US_TEST_E2E_DUPLICATE_SENT =
0 / NONZERO / NOT_RUN

US_TEST_E2E_BACKUP_WHILE_PRIMARY_HEALTHY =
SAFE_NOOP_PRIMARY_ACTIVE / OTHER / NOT_RUN

US_TEST_E2E_BACKUP_AFTER_PRIMARY_DEATH =
PASS / FAIL / NOT_RUN

STRUCTURED_AUTONOMY_PRODUCTION_PROMOTION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

READINESS =
READY_FOR_NATURAL_PROOF /
NEEDS_MORE_REPAIR /
BLOCKED_TLS /
NOT_READY
```

---

# 40. Completion response

Return:

```text
CURRENT ABC =
terminal ...
runtime released ...

BASE =
...

TLS =
root cause ...
repair ...
preflight ...

TRANSPORT CLASSIFIER =
...

LEASE / FENCING =
...

BACKUP =
healthy-primary behavior ...
dead-primary behavior ...

VALIDATOR 22 =
true violations ...
false positives ...
schema ownership ...
provenance defects ...

TEST E2E =
primary success ...
long-running primary ...
primary death ...
TLS failure ...
fallback-late-AI ...

FULL TESTS =
...

READINESS =
...

PRODUCTION SEND = 0
SCHEDULER CHANGE = 0
DB MUTATION = 0
MAIN MERGE = 0

ZIP =
...
ZIP_SHA256 =
...
```

---

# 41. Stop conditions

Stop immediately if:

```text
current ABC is still active
```

Stop before live-path model E2E if:

```text
signed-in CLI TLS preflight != PASS
```

Stop promotion readiness if:

```text
backup can still reclaim a fresh primary
```

Stop promotion readiness if:

```text
validator reaches green only by global weakening
```

Stop promotion readiness if:

```text
TEST duplicate > 0
```

Do not bypass security review.

---

# 42. Final principle

There are three independent correctness requirements:

```text
1. transport must be trustworthy and actually work
2. long-running active primary must retain fenced ownership
3. candidate must satisfy strict semantic/provenance validation
```

Fixing only one or two is insufficient.

The deterministic fallback already protected user delivery.
Keep that safety behavior intact while restoring the AI path.
