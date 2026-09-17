# Thesis Monitor — M12CJ Current US/KR Market + Monitored-Stock Production-Equivalent Smoke
## KRX Night-Futures Human Acceptance Fixture + Blind Human/AI Comparison Handoff

## 0. Decision and task identity

This task follows the successful M12CH new-generation Full22 reproof.

It is a **current-data, production-equivalent smoke test** of the already-frozen implementation. It is not another contract redesign, Full22 proof, Kiwoom-gateway project, night-futures source migration, model-policy retune, deployment, scheduler activation, or production send.

Suggested result bundle:

`thesis-monitor-20260917-m12cj-current-market-monitored-stock-production-equivalent-smoke-report.zip`

The task has four bounded objectives:

1. acquire the latest **safe current US/KR market data** through the repository's existing canonical providers and build production-equivalent market messages in isolation;
2. verify the KRX KOSPI200 NIGHT D/W/M path against the user-supplied Kiwoom human acceptance fixture for **contract 202612 / reference date 2026-09-16**;
3. run the currently configured monitored-stock analysis/message path against current evidence using the already-proven contracts, without retries/repair or production delivery;
4. package a **facts-only human-review set separately from sealed AI verdicts**, so Chat can obtain an independent human judgment before opening/comparing the AI decisions.

All architecture/scope decisions return to Chat.

---

# 1. Authoritative source order and frozen entry state

Use this priority:

1. this M12CJ instruction;
2. current local repository state whose application/runtime/config tree matches the M12CH frozen runtime;
3. verified M12CH result bundle;
4. M12CI result only as historical evidence that its Windows-gateway preflight made no runtime changes;
5. older reports only as historical context.

M12CH authoritative result:

- result: `M12CH_FROZEN_CONTRACT_FULL22_REPROOF_PASS`
- result ZIP SHA-256: `84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e`
- formal generation: `20260917-uskr22-m12ch-20260917T000529Z-65611727332a`
- required runtime base: `1e0d81695ce0982827a35a58b5123dfb86e066cc`
- runtime tree SHA-256: `f66f345e3d49ab21d169acd056330342f1609a6c7738020fca1fbc7710b86263`
- Full22: Core 22/22, Stage-2 22/22, finalization 22/22, readback 22/22
- application/runtime/config semantic changes during M12CH: 0
- production sends/mutations/deploy: 0

M12CI historical result:

- result: `M12CI_KIWOOM_READ_ONLY_CONFIG_MISSING`
- result ZIP SHA-256: `c8e55db99196b08934373bafb4b97574d696bac8cda94373badaa5f5ad1bea26`
- runtime application changes from M12CH base: 0

**Scope correction:** M12CI was based on an incorrect assumption that the Windows/OpenAPI+ `KIWOOM_GATEWAY_*` bridge was a prerequisite for the night-futures verification. It is not a blocker for M12CJ. The subsequent unexecuted M12CI-R1 instruction is superseded and must not be run as a prerequisite.

Do not configure or create a Windows Kiwoom gateway merely to satisfy this task.

---

# 2. Night-futures source ownership — freeze this before execution

The production/machine authority for the user-facing Korean night-futures section is the repository's existing **official KRX NIGHT source** and KRX history/aggregation path.

Canonical semantic chain to preserve:

```text
official KRX NIGHT daily OHLC
→ immutable/raw KRX receipt
→ normalized KRX NIGHT daily-bar history
→ current reference-date near-month selection
→ same-contract Daily / Weekly / Monthly aggregation
→ packet-owned validated night-futures facts
→ deterministic market-message renderer
```

The supplied Kiwoom screenshots are **human acceptance/cross-check fixtures only**. They are not a production provider, trusted network source, or authority that can overwrite KRX values.

Hard rules:

- no `KIWOOM_GATEWAY_URL` / `KIWOOM_GATEWAY_API_KEY` provisioning for this work;
- no screenshot/manual value injection into production packet construction;
- no hardcoding `202612` into production selection logic;
- no forcing KRX data to equal a screenshot by rewriting, clipping, choosing another contract, or changing session semantics;
- no cross-contract splicing for D/W/M;
- no KOSDAQ150 failure merely because the user did not provide a human screenshot fixture.

Existing KR market breadth/flow providers are separate concerns. If the normal current KR producer already uses an existing configured Kiwoom REST or other source, it may run unchanged as part of its canonical path. Do not add/configure a new provider solely for M12CJ.

---

# 3. User-supplied KOSPI200 human acceptance fixture

The package contains the original ten screenshots under:

`inputs/kiwoom-kospi200-acceptance/`

Treat the values below as **human-observed acceptance evidence**, extracted from those screenshots. Preserve image hashes and bind every asserted value back to the relevant image file.

## 3.1 Instrument and contract

```text
instrument_root = KOSPI200
Kiwoom selected contract = 202612
fixture reference date = 2026-09-16
session = NIGHT
```

This is an acceptance fixture. Production near-month selection must derive the contract independently from the KRX source/roll policy.

## 3.2 Daily controls

| Session date | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 2026-09-11 | 1094.55 | 1107.50 | 1085.45 | 1098.85 | 30217 |
| 2026-09-14 | 1043.00 | 1046.55 | 1016.00 | 1028.80 | 41418 |
| 2026-09-15 | 1037.90 | 1050.30 | 1030.30 | 1038.00 | 17874 |
| 2026-09-16 | 1058.70 | 1069.30 | 1036.00 | 1050.55 | 34382 |

Human-visible close-to-prior-valid-night-close percentages:

- 2026-09-14: `-6.37%` from 1028.80 vs 1098.85;
- 2026-09-15: `+0.89%` from 1038.00 vs 1028.80;
- 2026-09-16: `+1.21%` from 1050.55 vs 1038.00.

These percentage controls do not replace an explicit provider reference-basis contract where the provider exposes a different official change basis.

## 3.3 Weekly controls

Human-observed weekly bars for contract 202612:

| Week label | Open | High | Low | Close | Human visible return |
|---|---:|---:|---:|---:|---:|
| 2026-08-24 | 1058.40 | 1089.00 | 1022.20 | 1067.30 | -0.92% |
| 2026-08-31 | 1065.30 | 1095.85 | 1022.60 | 1095.85 | +2.67% |
| 2026-09-07 | 1109.55 | 1128.55 | 1069.00 | 1098.85 | +0.27% |
| 2026-09-14 | 1043.00 | 1069.30 | 1016.00 | 1050.55 | -4.40% |

For the 2026-09-14 current week, the daily inputs supplied above independently imply:

```text
weekly open  = first constituent open = 1043.00
weekly high  = max(1046.55, 1050.30, 1069.30) = 1069.30
weekly low   = min(1016.00, 1030.30, 1036.00) = 1016.00
weekly close = latest constituent close = 1050.55
```

Current-week return control:

```text
1050.55 / 1098.85 - 1 = -4.3955...% → -4.40%
```

The prior completed same-contract weekly close is `1098.85` from the week labeled 2026-09-07.

## 3.4 Monthly controls

Human-observed monthly bars for contract 202612:

| Month label | Open | High | Low | Close | Human visible return |
|---|---:|---:|---:|---:|---:|
| 2026-08 | 983.40 | 1106.00 | 977.00 | 1061.55 | +1.59% on Kiwoom chart |
| 2026-09 current | 1062.00 | 1128.55 | 1016.00 | 1050.55 | -1.04% |

Current-month return control:

```text
1050.55 / 1061.55 - 1 = -1.0362...% → -1.04%
```

The prior completed same-contract monthly close is `1061.55`.

## 3.5 Fixture verdict semantics

Produce an explicit fixture comparison with one of:

- `EXACT_PARITY` — contract/session/date and comparable O/H/L/C match the Kiwoom fixture, and KRX-derived D/W/M aggregate reproduces the human values under the same semantics;
- `EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE` — a difference is real but is fully explained by a documented provider/chart/session/reference convention without changing machine authority;
- `UNEXPLAINED_MISMATCH` — comparable same-contract/session facts differ without a proven semantic reason;
- `SOURCE_UNAVAILABLE` — the authoritative KRX source/history needed for this control cannot be obtained safely.

`UNEXPLAINED_MISMATCH` or `SOURCE_UNAVAILABLE` blocks the night-futures portion of smoke readiness. Do not repair data in-place.

KOSDAQ150 has no user-supplied human fixture in M12CJ. Record `HUMAN_FIXTURE_NOT_PROVIDED`; continue to enforce its existing KRX/schema/source validators if it is part of the normal message path.

---

# 4. Exact runtime/base preflight

Use an isolated clean worktree or current clean local checkout. Do not reset an operating checkout.

Before any external provider or model call:

1. verify the M12CH result ZIP and its manifest;
2. verify current repository ancestry and the exact application/runtime/config tree against the M12CH frozen tree;
3. allow later docs/test/report commits only if application/runtime/config semantics are unchanged;
4. run the already-relevant focused regressions for accepted-v2 independent Core binding, symbolic/null provenance, numeric ownership, KRX night history/DWM, Treasury, message quality and native delivery readback;
5. inspect the actual current runtime caller graph used for US and KR market producer/message creation and monitored-stock delivery; do not resurrect an old script merely because it exists in a report;
6. resolve all provider/model configuration presence without printing secret values.

If a runtime/application source change is required to make the smoke possible, stop before the corresponding external call with a minimal reproducer. **M12CJ authorizes no application/runtime repair.**

Expected application/runtime/config source change count: `0`.

---

# 5. Isolation and safety boundary

All current-data collection and inference must run in a production-equivalent but isolated environment.

Required:

- temporary/output root distinct from production;
- temporary DB/state/ledger or a read-only snapshot plus isolated writable copy where existing code requires persistence;
- no production DB mutation;
- no production warning/assessment/notification mutation;
- no production Telegram/email/recipient send;
- no scheduler start/resume/change;
- no main merge, deployment or remote push;
- no broker order/modify/cancel path;
- no Windows Kiwoom gateway provisioning;
- capture sink or existing test-only transport for final delivery rendering;
- preserve canonical acceptance, identity, state and renderer logic; mock only external delivery I/O/settings.

Public/approved market-provider network reads and the existing approved model inference path are permitted only as required by sections 6–8.

Count separately:

```text
market_provider_reads
model_inference_calls
test_sink_invocations
production_sends = 0
production_order_calls = 0
production_modify_calls = 0
production_cancel_calls = 0
```

Do not expose credentials in report artifacts.

---

# 6. Current-session resolution — never fake a close

Record the actual execution timestamp with timezone and use the repository's existing exchange/session calendars.

## US

Resolve the latest safely completed US regular market session under the existing production rules. Build the US morning/current-market context against that session.

For an observation on 2026-09-17 KST, the KRX NIGHT reference control should resolve to the latest valid XKRX business date strictly before the observation date, i.e. `2026-09-16`. The supplied Kiwoom fixture is specifically for this reference date.

If execution occurs later, preserve the 2026-09-16 fixture as a dedicated historical acceptance control while the actual current message uses its naturally resolved latest safe night reference date.

## KR

If the KR regular session is still open at execution time, do not masquerade intraday data as a completed KR-close run. Use the latest completed regular session for a close-equivalent smoke unless the existing consumer has a separately typed intraday mode. Do not bypass session guards to obtain a green result.

Record:

- observed timestamp;
- target regular session date per market;
- source observation/as-of dates;
- stale/current/partial status under existing contracts;
- why every fact is eligible for the rendered role.

---

# 7. Current US/KR market-message smoke

Run the existing canonical current market collection and deterministic message paths with current safe data.

At minimum verify:

## US market message

- latest completed US index/market facts required by the current renderer;
- breadth/style/sector facts according to the existing source contracts;
- Treasury nominal curve and any existing real-yield facts at their actual observation dates;
- KRX night-futures section through the official KRX source/history path;
- correct reference date and current near-month contract identity;
- D/W/M typed sidecar and renderer consistency;
- no stale fact rendered as current;
- message quality validator PASS;
- capture sink/output only, no production send.

The dedicated 2026-09-16 KOSPI200 Kiwoom fixture comparison must be executed even if the current US smoke later uses a newer night reference date.

## KR market message

Use the current canonical KR producer/providers and safe session semantics. Do not make the Windows Kiwoom gateway a prerequisite. Existing already-configured source paths may run unchanged.

Verify source dates, market-session role, breadth/flow/sector/index contracts used by the actual message, message-quality validation and capture-sink output.

A source that is genuinely unavailable must use the existing omission/partial/fail-closed semantics. Do not fabricate a value or silently substitute a new provider.

---

# 8. Current monitored-stock smoke

Resolve the **actual currently configured monitored-stock population** from the canonical current state at task start. Do not hardcode the M12CH US14/KR8 list as the runtime population and do not add/remove a subject merely to match 22.

Export the resolved population and its source/identity before inference.

For every subject in scope:

1. collect/build current evidence using existing approved sources and current canonical preparation;
2. build Fundamental Core through the current owner;
3. freeze accepted Core independently;
4. run Stage-2 using only that current-generation Core;
5. materialize deterministic runtime fields;
6. run all current semantic/ownership/numeric/ref/entry-holder contracts;
7. finalize through the current accepted-v2 owner with the independently frozen Core;
8. render and native-read back the production-equivalent message;
9. route to the isolated capture sink only.

This is a **smoke**, not another M12CH proof and not a target-label experiment. Do not force prior BUY/HOLD/SELL, new-buyer, holder, maturity, wording or hash outcomes.

Existing production model/configuration must be used as configured. Do not silently substitute model/effort/schema/transport.

Forbidden inference behavior:

```text
retry = 0
wrapper_retry = 0
fallback_model = 0
judge = 0
repair_model = 0
schema_repair_model = 0
candidate_repair = 0
selective_rerun = 0
per_ticker_retry = 0
hotfix_after_first_call = 0
prior_model_output_reuse = 0
cross_generation_stitch = 0
```

A deterministic source/provider retry already owned by the provider contract is not a model retry; report it separately.

On a hard model/contract failure, stop that dependent market/model stream and preserve the exact output. Complete safe independent market-data/fixture diagnostics for the other stream where shared safety is intact. No patch-and-resume.

---

# 9. Blind human-review separation — mandatory

The purpose after M12CJ is to compare human judgment against AI without exposing the AI verdict first.

Therefore generate two strictly separated result surfaces.

## 9.1 Human-review facts-only set

Before opening or summarizing AI verdicts, create:

`human-review/`

containing at minimum:

- `US_MARKET_FACTS_ONLY.md/json`
- `KR_MARKET_FACTS_ONLY.md/json`
- `MONITORED_STOCK_FACTS_ONLY_INDEX.json`
- one facts-only file per monitored subject
- source/as-of/quality/ownership refs sufficient for independent judgment
- relevant price structure, current business/fundamental evidence, market context and known limitations already available to the model

Hard exclusion from these files:

- AI `BUY/HOLD/SELL` verdict;
- AI new-buyer result;
- AI holder result;
- AI directional balance;
- AI maturity verdict where it would reveal the decision rationale;
- model summary/recommendation text;
- any hint such as filenames or counts that reveals a per-subject AI choice.

These files must be generated from source/evidence data, not by asking an AI model to summarize its own verdict.

## 9.2 Sealed AI-output set

Put AI decisions, accepted plans and full AI-rendered monitored-stock messages under a separate directory and package them as:

`sealed-ai-verdicts.zip`

Record its SHA-256 and manifest in the top-level report, but **do not reproduce per-subject verdicts or decision distributions in the top-level REPORT.md or human-review files**.

The top-level result may state only structural counts such as:

```text
AI subjects attempted/completed/accepted/readback = N/N/N/N
```

without revealing decision labels.

This allows Chat to verify technical smoke completion while deliberately not reading the sealed verdicts until after the user provides an independent facts-only judgment.

If existing report tooling automatically prints verdict labels, suppress them only in this audit/report surface; do not change runtime model outputs or production renderer semantics.

---

# 10. KOSPI200 fixture proof artifacts

Export a dedicated machine-readable comparison:

`krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json`

It must record:

- image filenames and hashes;
- manually extracted fixture values from section 3;
- KRX raw request/receipt identities and payload hashes;
- selected KRX contract for 2026-09-16;
- exact KRX normalized daily bar;
- constituent dates used in current weekly and monthly aggregates;
- expected calendar dates, missing dates and finality/status;
- D/W/M O/H/L/C;
- weekly/monthly return baseline dates/closes;
- observed return calculations;
- exact comparison result per field;
- overall fixture verdict from section 3.5;
- any documented semantic difference without rewriting either source.

Also verify generic anti-hardcode controls: another reference date must still use canonical near-month selection rather than the fixture's literal `202612`.

---

# 11. No scope regression

Do not reopen or redesign without direct reproducible contrary evidence:

- M12CH 22/22 frozen contract reproof;
- BUY/WAIT/HOLDABLE independence and entry/holder semantics;
- preconfirmation/postconfirmation contracts;
- frozen-Core numeric ownership;
- independent Core binding;
- maturity atomic identity/polarity/eligibility;
- symbolic-null provenance state;
- concrete same-row MAX semantics;
- missing-vs-explicit-null presence guard;
- exact-ref fidelity and typed primitives;
- expectation/valuation and BusinessDelta ownership;
- Persistence V2/native accepted-v2 authority;
- Treasury FRED semantics;
- KRX night-futures machine authority and same-contract D/W/M design;
- documented at-least-once send-after-transport/before-cursor crash-window limitation.

If a current source observation differs from a historical value, that is not a contract regression by itself.

---

# 12. Required tests and controls

Before final packaging run the current relevant focused/full regressions, including at minimum:

- accepted-v2 model/raw/materialization/finalization/readback;
- independent Core binding and finalization numeric-scope negatives;
- KRX night history/session/near-month/same-contract DWM/renderer tests;
- US full market message and Treasury tests;
- KR current market/message tests used by the actual path;
- native delivery/capture sink regressions;
- human-review redaction/sealed-verdict separation tests added only to audit tooling if necessary.

Run full pytest, Ruff and `git diff --check`.

No existing test deletion or skip inflation. Report test counts and explain legitimate additions.

Application/runtime/config source diff must remain zero. Audit/work-instruction/report scripts may be added.

---

# 13. Required result artifacts

At minimum include:

1. `REPORT.md` — structural outcome only; no per-subject AI verdict labels.
2. `source-base-runtime-integrity.json`.
3. `scope-correction-m12ci.json` — explicitly records Windows gateway as non-prerequisite for night-futures fixture and M12CI-R1 as superseded/unexecuted.
4. `execution-session-resolution.json`.
5. `provider-call-ledger-redacted.json`.
6. `current-us-market-smoke.json` plus rendered capture output.
7. `current-kr-market-smoke.json` plus rendered capture output.
8. `krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json`.
9. raw/normalized KRX fixture source receipts needed to reproduce the comparison.
10. `monitored-population-snapshot.json`.
11. `monitored-stock-smoke-structural-matrix.json` with identities and PASS/failure boundaries but **no verdict labels**.
12. `human-review/` facts-only package.
13. `sealed-ai-verdicts.zip` plus SHA-256 and nested manifest.
14. `blind-review-separation-audit.json` proving top-level/human files contain no AI verdict leakage.
15. capture-sink traces and state/intent counts.
16. test/JUnit/Ruff/diff-check records.
17. `safety-counters.json`.
18. `completion-layer-ledger.json`.
19. `complete-blocker-ledger.json`.
20. `artifact-manifest.json` with relative path, size and SHA-256; manifest self-exclusion explicit.

Do not include credentials or raw secret-bearing environment dumps.

---

# 14. Completion layers and terminal outcomes

Keep these distinct:

1. `frozen_contract_full22` — carried forward from M12CH, not rerun as a proof in M12CJ;
2. `current_market_source_and_message_smoke`;
3. `current_monitored_stock_smoke`;
4. `human_blind_review_ready`;
5. `ai_comparison` — **NOT_PERFORMED_IN_M12CJ**;
6. `deployment_authorization` — **NOT_AUTHORIZED**.

Preferred terminal outcomes:

### `M12CJ_CURRENT_SMOKE_PASS_READY_FOR_BLIND_HUMAN_REVIEW`
Requires:

- current US/KR market smoke completed at valid session semantics;
- KRX KOSPI200 2026-09-16 fixture is `EXACT_PARITY` or a fully evidenced `EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE` acceptable under existing contracts;
- monitored-stock current smoke reaches accepted/readback/capture for the entire resolved current population, or any explicit existing safe omission semantics are individually proven and do not masquerade as success;
- facts-only review package complete;
- AI verdict package sealed with no top-level leakage;
- no runtime/app/config modifications;
- no production send/mutation/deploy.

### `M12CJ_KRX_NIGHT_FIXTURE_MISMATCH`
Use for an unexplained comparable KRX/Kiwoom same-contract/session D/W/M mismatch. Preserve source data and return to Chat; no data rewrite.

### `M12CJ_CURRENT_SOURCE_DEPENDENCY`
Use when an existing required current source/configuration is unavailable. Name the exact canonical dependency. Do not introduce a replacement provider.

### `M12CJ_MONITORED_STOCK_SMOKE_NOT_CLOSED`
Use when current monitored-stock inference/acceptance/readback fails under frozen contracts. Preserve the first exact failure per independent stream; no retry/repair.

### `M12CJ_UNEXPECTED_RUNTIME_DRIFT`
Use if the application/runtime/config tree materially differs from the M12CH frozen implementation before smoke execution.

Even a full M12CJ PASS does **not** authorize deployment or scheduler resume. It authorizes only the next Chat step: review the **facts-only** packet and obtain the user's independent judgment before opening `sealed-ai-verdicts.zip`.

---

# 15. Safety counters — hard zeros

Unless explicitly stated as test-only/capture behavior, require:

```text
main_merge = 0
remote_push = 0
deployment = 0
scheduler_start_resume_change = 0
production_send = 0
production_recipient_intent = 0
production_db_mutation = 0
broker_order = 0
broker_modify = 0
broker_cancel = 0
windows_kiwoom_gateway_provision = 0
model_retry = 0
fallback_model = 0
judge_model = 0
repair_model = 0
schema_repair_model = 0
selective_model_rerun = 0
per_ticker_model_retry = 0
cross_generation_stitch = 0
prior_model_output_reuse = 0
```

Current approved market reads and the bounded current smoke model inference calls are nonzero only if their exact canonical preconditions pass. Record denominators and call identities.

---

# 16. Return boundary

Return the complete result ZIP and SHA to Chat.

Do **not** automatically open or summarize the sealed AI verdicts in the result report.

Next sequence after an M12CJ PASS:

```text
Chat verifies technical smoke result without reading sealed verdicts
→ Chat presents facts-only current evidence to the user
→ user records independent market/stock judgments
→ only then open sealed-ai-verdicts.zip
→ compare human judgment vs AI outputs and diagnose disagreements
→ separate deployment / scheduler / real-send decision
```

The KOSPI200 Kiwoom fixture remains human acceptance evidence. KRX remains the machine authority.
