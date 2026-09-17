# Thesis Monitor — M12CI Kiwoom Read-Only Gateway Configuration & Verification

## 0. Decision and bounded authorization

M12CH completed the frozen-contract fresh Full22 reproof successfully:

- top-level result: `M12CH_FROZEN_CONTRACT_FULL22_REPROOF_PASS`
- fresh model generation: US14 + KR8, 22/22
- planned / started / completed / usable model calls: 16 / 16 / 16 / 16
- Fundamental Core accepted: 22/22
- Stage-2 raw/materialized/semantic accepted: 22/22
- accepted-plan finalization / rendered blocks / native readback: 22/22
- model/output repair, retry, fallback, judge, selective/per-ticker rerun, prior-output reuse, cross-generation stitching: 0
- production send / DB mutation / scheduler mutation / merge / deploy / push: 0
- deployment remains unauthorized.

This task is the next operating phase: **verify the existing Kiwoom gateway in READ_ONLY mode**. It is not another investment-decision repair, Full22/model task, market-message smoke, broker-write test, new connector implementation, or deployment task.

Work instruction:
`20260917-m12ci-kiwoom-read-only-gateway-configuration-verification.md`

Suggested result:
`thesis-monitor-20260917-m12ci-kiwoom-read-only-gateway-configuration-verification-report.zip`

External model calls: **0**.
Full22 generations: **0**.
Broker order/modify/cancel calls: **0 / 0 / 0**.
Production sends/scheduler changes/DB mutations/main merges/deployments/remote pushes: **0**.

Live Kiwoom **read** calls are authorized only through the repository's existing read-only gateway client/adapter and only as needed for the bounded verification below.

---

## 1. Authoritative entering state

### 1.1 Latest proof

Verify first:

`thesis-monitor-20260917-m12ch-frozen-contract-new-full22-reproof-report.zip`

Expected SHA-256:

`84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e`

Expected report manifest:

- 163 declared payloads, manifest self-excluded
- missing/hash/size/extra mismatch: 0.

Authoritative M12CH repository state:

- required runtime base: `1e0d81695ce0982827a35a58b5123dfb86e066cc`
- harness freeze: `65611727332a4198c24eba0fb1a0f41f382bbf3d`
- M12CH final local/docs: `323ce79f072abfff96f42e28e081e260908f3355`
- runtime source drift during M12CH: 0
- message/model contract readiness: `FULL22_REPROVEN_LOCAL_ONLY`
- deployment readiness: `NO_BY_PHASE_BOUNDARY`.

The M12CH proof used the frozen 2026-09-15 evidence snapshot. It is not a current-market assessment.

### 1.2 Frozen Kiwoom facts

Carry forward without redesign:

- historical Kiwoom commit: `28f4f70700046f98d5d899ee491d3e5f45922e9a`
- KOSPI200 historical replay for 2026-09-01 / 09-02 / 09-03: PASS
- local `LeadingMarket` adapter: PASS
- KOSDAQ150 actual historical fixture: **UNVERIFIED**
- previously reported live gateway state: unavailable / unconfigured
- required live configuration names:
  - `KIWOOM_GATEWAY_URL`
  - `KIWOOM_GATEWAY_API_KEY`
  - `KIWOOM_GATEWAY_TIMEOUT_SECONDS`
- required capability: **READ_ONLY**
- order permission is not required and must not be exercised.

Treasury remains frozen and is not part of this task:
FRED DGS3/DGS5/DGS10/DGS30, DFII10, T10YIE; existing daily/per-series as-of/bp-change semantics remain unchanged.

---

## 2. Source-of-truth and owner-first rule

Before any network call, inspect current local Git history and existing canonical owners for:

1. Kiwoom gateway configuration parsing;
2. gateway HTTP/client transport;
3. read-only capability declaration or enforcement;
4. `LeadingMarket` normalization/adapter;
5. the exact read endpoints actually consumed by the application;
6. error/timeout/schema validation;
7. any existing health/capability probe;
8. the caller used later by current-market collection.

Reuse those owners. **Do not create a new connector, alternate HTTP client, parallel adapter, new endpoint contract, or broker abstraction.**

Record exact files, symbols, callers and source hashes.

If current local repository state materially diverges from M12CH runtime or the known Kiwoom owner cannot be identified, stop with:

`M12CI_KIWOOM_OWNER_OR_BASE_DIVERGENCE`

No application repair is authorized in this task.

---

## 3. Secret and configuration safety

### 3.1 Never expose credentials

Never print, commit, package, diff, log, hash into a report, or echo:

- `KIWOOM_GATEWAY_API_KEY`
- authorization headers
- tokens/cookies
- secret query values
- complete environment dumps.

Reports may contain:

- whether each required variable is present;
- sanitized URL origin/host only if it contains no credential material;
- timeout value if non-secret;
- redacted header names;
- config-source type, not secret contents.

### 3.2 Configuration discovery

Use only supported existing configuration sources in the user's current environment / already-established secret mechanism.

Do not:

- invent placeholder credentials;
- write secrets into repository files;
- create a `.env` containing a secret;
- register a new third-party connector;
- request order permissions;
- bypass TLS/auth/security checks.

If required configuration is absent, terminate live verification cleanly:

`M12CI_KIWOOM_READ_ONLY_CONFIG_MISSING`

Report exactly which **variable names** are missing, never values.

If configuration exists but authentication or gateway reachability fails, distinguish:

- `M12CI_KIWOOM_GATEWAY_UNREACHABLE`
- `M12CI_KIWOOM_GATEWAY_AUTH_FAILED`
- `M12CI_KIWOOM_GATEWAY_SCHEMA_OR_CAPABILITY_MISMATCH`

Do not convert these into an implementation task automatically.

---

## 4. Capability freeze and write prohibition

Before live reads, prove from existing code/config and, where supported, gateway capability metadata that the path used is read-only.

Allowed network actions:

- existing health/capability read, if canonical;
- the minimum existing live market/index reads required by the Kiwoom `LeadingMarket` path;
- read-only schema/error handling needed to verify those results.

Forbidden:

- order placement;
- order amendment/modification;
- cancellation;
- simulated/dry-run order endpoints;
- account-changing calls;
- authentication/permission escalation;
- write-capability probing by deliberately invoking a write endpoint.

If the connected credential happens to have broader external privileges, do not test them. Record only:

`configured_for_task_capability = READ_ONLY_USE_ONLY`

and keep broker writes at 0.

Instrument/count live operations by category:

`read / order / modify / cancel`

Order/modify/cancel must remain `0 / 0 / 0`.

---

## 5. Live read verification

### 5.1 Use the existing application route

Exercise the exact read route and adapter the application would use later for current KR market context. Do not call guessed undocumented endpoints merely to obtain green data.

Before execution, record:

- gateway client owner;
- method/endpoint family used by the existing client;
- expected response type/schema;
- normalization owner;
- timeout and existing retry policy;
- market/index identifiers from existing code.

Use the repository's existing retry policy without widening it. Do not write a new retry wrapper.

### 5.2 Required positive verification

Where supported by the existing route, perform enough live read calls to demonstrate:

1. gateway connectivity/authentication;
2. response parse/schema validity;
3. timestamps/as-of semantics;
4. current KOSPI200 read through the canonical adapter;
5. current KOSDAQ150 read through the canonical adapter if the existing client supports it;
6. deterministic normalized `LeadingMarket` representation from the response;
7. no broker write side effect.

Do not assert a live KOSDAQ150 PASS when the current canonical client does not support that read. In that case report the exact supported boundary.

Historical KOSDAQ150 fixture status remains `UNVERIFIED` even if a live schema read succeeds. Use a separate classification such as:

`LIVE_READ_SCHEMA_VERIFIED_HISTORICAL_FIXTURE_UNVERIFIED`

Do not upgrade historical replay coverage.

### 5.3 Freshness and timestamps

Record the actual gateway/server/provider timestamps and the task execution time, preserving timezone/offset semantics.

Do not rewrite a stale response as current. Classify:

- current/usable under existing application's freshness rule;
- stale under existing rule;
- timestamp missing/ambiguous.

Do not invent a new freshness threshold in this task.

---

## 6. Negative and fail-closed checks

Use existing test fixtures/local mocks for negative behavior where a live negative would require unsafe calls. Do not sabotage real credentials.

Verify at minimum:

- missing config -> no network call;
- malformed/sanitized synthetic gateway response -> parser rejects;
- wrong/missing required response fields -> adapter rejects or returns its documented unavailable state;
- timeout/network failure -> existing safe failure result;
- auth failure handling does not expose secret values;
- unsupported market/index does not silently map to KOSPI200;
- no fallback to fabricated zero/current values;
- no fallback to an order/write path;
- no production state or message send as a side effect.

A negative test passes only when the intended gate/error is observed, not merely because any exception occurred.

---

## 7. Historical/local regression

Rerun the existing Kiwoom regression suite and preserve:

- historical commit/reference provenance;
- KOSPI200 2026-09-01/02/03 replay behavior;
- local `LeadingMarket` adapter;
- existing schema and fallback behavior.

Do not fabricate a KOSDAQ150 historical fixture. Its prior unverified state remains explicit unless a genuine existing historical source fixture is found in the repository and can be traced to the canonical owner. Discovery of such a preexisting fixture is allowed; creating one from today's live response and calling it historical is forbidden.

Run the relevant full/focused frozen regression needed to confirm that this configuration verification caused no application contract drift. Application/runtime source changes should normally be **0**.

If live verification reveals a runtime/schema defect requiring application code change, stop with a minimal reproducer and propose a separately bounded repair. Do not repair opportunistically.

---

## 8. No current-market message smoke yet

This task may read the minimum current Kiwoom market data needed to verify the gateway, but it must **not**:

- run a fresh US/KR model analysis;
- build the full current market + monitored-stock message smoke;
- treat the live index sample as a complete current-market dataset;
- send Telegram/email/other production messages;
- resume a scheduler.

Those are the next phase after Chat reviews this result.

---

## 9. Required result artifacts

Include at minimum:

1. `source-and-repository-integrity.json`
2. `m12ch-result-integrity.json`
3. `kiwoom-canonical-owner-call-graph.json`
4. `kiwoom-config-presence-redacted.json`
5. `kiwoom-read-only-capability-audit.json`
6. `kiwoom-network-call-ledger.json`
7. `kiwoom-live-health-auth-result.json`
8. `kiwoom-live-read-raw-redacted.json` or equivalent sanitized raw evidence
9. `kiwoom-live-leading-market-normalization.json`
10. `kiwoom-kospi200-live-verification.json`
11. `kiwoom-kosdaq150-live-verification.json`
12. `kiwoom-timestamp-freshness-audit.json`
13. `kiwoom-negative-fail-closed-tests.json`
14. `kiwoom-historical-local-regression.json`
15. `runtime-diff-and-test-results.json`
16. `safety-zero-write-audit.json`
17. `completion-layer-ledger.json`
18. `complete-blocker-ledger.json`
19. `program-completion.json`
20. `REPORT.md`
21. `artifact-manifest.json`
22. external ZIP SHA-256 sidecar.

Sanitize all network evidence. Never include the API key or authorization value.

---

## 10. Program completion

Record actual measured values:

- `top_level_result`
- `m12ch_result_sha256`
- `m12ch_full22_status`
- `required_base_sha`
- `current_local_sha`
- `runtime_source_change_count`
- `kiwoom_historical_commit`
- `canonical_gateway_client_owner`
- `canonical_leading_market_owner`
- `gateway_url_config_present`
- `gateway_api_key_config_present`
- `gateway_timeout_config_present`
- `gateway_auth_result`
- `gateway_health_result`
- `configured_for_task_capability`
- `live_read_call_count`
- `live_order_call_count`
- `live_modify_call_count`
- `live_cancel_call_count`
- `kospi200_live_result`
- `kosdaq150_live_result`
- `kosdaq150_historical_fixture_status`
- `normalized_leading_market_result`
- `freshness_result`
- `secret_exposure_count`
- `historical_regression_result`
- `runtime_contract_drift_count`
- focused/full/Kiwoom test results
- production DB/message/scheduler/main/deploy/push counts
- `current_market_message_smoke_authorized=false`
- `deployment_readiness=NO`
- `next_scope`.

Every zero must have a measured denominator. Use `NOT_RUN`, `NOT_PROVEN`, or an exact blocker rather than invented zero where execution was impossible.

---

## 11. Terminal outcomes

### PASS

`M12CI_KIWOOM_READ_ONLY_GATEWAY_VERIFIED`

Requires:

- canonical existing owner used;
- required configuration present without secret exposure;
- gateway auth/connectivity PASS;
- applicable live read(s) PASS;
- canonical `LeadingMarket` normalization PASS;
- timestamps/freshness classified truthfully;
- write calls order/modify/cancel = 0/0/0;
- historical/local regression healthy;
- no runtime contract drift;
- no production mutation/send/scheduler/deployment activity.

Even after PASS:

- deployment remains unauthorized;
- current-market message smoke has not run;
- return to Chat.

### Configuration missing

`M12CI_KIWOOM_READ_ONLY_CONFIG_MISSING`

No new connector or secret persistence. Return missing variable **names only**.

### Gateway/auth/schema unavailable

Use the exact bounded outcome:

- `M12CI_KIWOOM_GATEWAY_UNREACHABLE`
- `M12CI_KIWOOM_GATEWAY_AUTH_FAILED`
- `M12CI_KIWOOM_GATEWAY_SCHEMA_OR_CAPABILITY_MISMATCH`
- `M12CI_KIWOOM_LIVE_DATA_FRESHNESS_FAILED`

Do not turn those into a broader runtime repair in this task.

### Runtime defect found

`M12CI_KIWOOM_RUNTIME_REPAIR_REQUIRED`

Provide exact owner, input, response shape, error, minimal reproducer and narrow repair proposal. Do not implement the repair without Chat authorization.

---

## 12. Subsequent order

On `M12CI_KIWOOM_READ_ONLY_GATEWAY_VERIFIED`:

**Chat review
→ current US/KR market + monitored-stock message smoke
→ independent human judgment using only collected facts before seeing AI verdicts
→ AI-result comparison
→ separate deployment/automation decision.**

No M12CI PASS authorizes main merge, scheduler resume, production message send, broker write or deployment.
