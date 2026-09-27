# REV8 Live Full-Source Cohort: Partial Closeout

## Result

Terminal: `M12DS_R6_R5F_R2B0_R5_REV8_FULL_SOURCE_COMPOSITION_GAP`

This is not a full implementation or authority PASS. No R2B instruction was generated or executed.

- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = false`
- `COMPLETE_SOURCE_ADAPTER_QUALIFIED = false`
- FullSourceRunSeed / US whole packet / KR whole packet / combined packet / full authority graph: not produced.
- P0 open: 0. P1 open: 3 (listed below).
- No source recollection after acquisition. No model, renderer, Telegram, DB write, scheduler change, merge, push, deploy or restart.

## Repository and Freeze

| Identity | Value |
|---|---|
| Branch | codex/m12ds-r6-r5f-r2b0-r5-rev8-live-full-source |
| Base / accepted REV7 | b0dc78708f480d591889b40ea9f50707ef1283db |
| Work-instruction commit | 77a3a27cb898ad5ed34b639b4bc1cc3061e5a625 |
| Acquisition implementation | 6ecd3e1a6f71e768a89259099505519a5afd6c6b |
| Parent proof | rev8-live-20260927T083836Z |
| Scope | AD_HOC_LIVE_SOURCE_PROOF / LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION |
| Operating main | b610e6de0a8c33d199961e821ff1b130e1fa9ad4, unchanged and clean |

Final local documentation SHA is recorded in repository-identities.json and final-validation.json.
Actual source query times are retained separately from source sessions. US session: 2026-09-25.
KR session and expected KRX night session: 2026-09-23. No clock spoofing or session relabelling.

Two pre-network plans were superseded during development, with zero provider calls.
Only sealed-live was dispatched. All runtime code stayed identical to the acquisition freeze.
Earlier pre-network validation exits caused by changing code fingerprints are not accepted receipts.
The acquisition-final validation is clean and exact; final validation also identifies its exact local SHA.

## Live Acquisition

| Owner | Actual logical requests | HTTP attempts | Transient retries | Frozen logical cap |
|---|---:|---:|---:|---:|
| Kiwoom stock roles | 291 | 294 | 3 | 579 |
| Native OHLCV US market | 25 | 27 | 2 | 48 |
| Kiwoom KR market | 42 | 42 | 0 | 109 |
| KRX night | 6 | 6 | 0 | 7 |
| Total | 364 | 369 | 5 | 743 |

Auth exchanges are counted but bodies and tokens are not exported.
All transport retries retained the same request. Per-request timeout: 600 seconds; retries: at most 2.
No cap exhaustion or systemic stop. Alpha Vantage, Massive, synthetic live sources and fallback: 0.

- Stock Class A: all 88 roles newly captured; unchanged native normalizer replay **88/88 PASS twice**.
- Current-price consumer: **22/22 eligible**. CPNG remains PARTIAL_SAFE under the unchanged historical-anomaly policy.
- US market: exact current registry, **22/22 observations**, no warnings; transitive owner replay PASS twice.
- KR market: native owner returned 2 indices, 63 sectors and breadth; 41 data responses plus auth.
  This is capture success, **not** source-adapter qualification.
- KRX: two current eligible products; six raw response receipts; native probe/history/materializer output reproduced exactly twice.
  No historical REV7 night packet was substituted. Historical DWM completeness is not asserted beyond the new captured owner output.
- Optional events/calendar/exchange breadth: explicitly unavailable, no calls.
- Class C: read-only version set frozen at proof start, hashes invariant. No latest-looking row substitution.
- Class D: excluded, no calls.

## Exact Blocker 1: KR Page Completion

Both KOSPI and KOSDAQ ka20001 and ka20009:
- The frozen existing owner graph consumes one page (max_pages=1).
- The actual response page advertises continuation=true.
- The native parser found matching target-session data.
- KiwoomReceiptObserver.finish therefore records mandatory_complete=false.
- verify_aggregate independently rejects with aggregate_page_set_incomplete.

The exact four read keys, raw hashes, attempt and session are in KR-page-completeness-blocker.json.
Neither continuation flags nor missing pages were patched. Additional pages were not requested after the frozen plan completed.
This is an owner/observer consumption-completeness mismatch to investigate, not proof that omitted pages are irrelevant.

Optional ka10066 pagination completed (KOSPI 14 pages, KOSDAQ 19 pages).
Concentration was independently denied by existing UNRESOLVED_BASIS_OR_TAXONOMY reconciliation.
Optional flow denial must not be conflated with the mandatory four-read closure issue.

## Exact Blocker 2: Current Stock Business Owner Integration

The new base stock materializer produces **2 PASS / 20 BLOCKED**:
- PASS: 005930, 047810.
- 003690: financial_selected_tuple_mismatch in the base direct-financial owner.
- Remaining 19: observed_business_union:eligible_reported_financial_or_event.

This is **not a retraction of REV7's accepted 22/22** and not a new price-data failure.
The current composition path uses the base stock owner but does not yet connect the accepted
bounded comparative financial / issuer-bridge / event owners. The accepted Class-C business versions
are frozen separately and their native quality replay is recorded in accepted-business-version-replay.json;
they were not silently copied into current packets or counted as consumed evidence.

Required remaining work:
- Rebind the accepted source-only comparative owners to the new stock plan while preserving original financial periods.
- Preserve 003690 insurance, TSM/WRD foreign statement and 000660 denied-field semantics.
- Bind SKHY through its existing issuer-only bridge, with no security/per-share/valuation transfer.
- Handle SNDK event authority explicitly. No old Class-B event was relabelled as a new run acquisition.

All 22 current packet/component statuses and exact failures are included. Old stock price packets were never used as current values.

## Exact Blocker 3: Whole-Source Authority

The new FullSourceRunSeed/composition module is an unqualified prototype.
It has schema, hash and subset boundary tests, but the complete real run-seed/role/business-owner/source-authority closure
is not implemented and proven end to end. Existing build_source_authority is not replaced by a weaker allocator.

No accepted seed or whole-source hash is emitted. Nulls in composition-not-produced.json mean absent artifacts,
not permitted missing fields in an accepted full packet. Full-composition negative controls remain unclosed;
component test success does not qualify this prototype.

## Offline Reproof

- All 88 native stock normalizations: exact twice.
- 22 price/technical component and base stock result matrices: exact twice.
- US transitive market output: exact twice.
- KR mandatory-page denial: exact twice.
- KRX native output: exact twice.
- Frozen Class-C versions and accepted legacy financial quality: invariant.
- Full whole-source composition: NOT REACHED / NOT PASS.
- Network attempts in replay: 0.

The native night replay restores the original captured live-origin annotation only after checking the actual
request/response graph. Replay itself makes no live call and is not counted as a second Class-B acquisition.

## Validation and Safety

Acquisition exact SHA:
- Focused: 978 PASS.
- Full: 5966 PASS, 63 unchanged skips.
- Ruff / diff / Investment Knowledge / Chart Knowledge / disabled production entrypoint smoke: PASS.
- No new unexplained skip/xfail.
- Exact final local SHA receipt is included separately.
- GitHub Actions: not run; remote push is outside scope.

Operating code/config/env, production DB bytes and scheduler inventory invariance: PASS.
Source-worker overrides are process-local; operating services and secret files were not modified.
No raw artifacts, prompts or logs were pushed to GitHub.
All exported bodies are secret-scanned. Auth exchange bodies and recipient IDs are excluded.

## Bounded Next Scope

Use this immutable captured cohort for an **offline-only** owner/assembler repair:
1. Resolve KR consumed-page versus exhaust-pagination ownership with raw dependency proof.
2. Connect the existing accepted comparative financial, issuer and event owners to the new current stock generation.
3. Close explicit run-seed, role, Class-B/Class-C and build_source_authority bindings; rerun complete negative controls and replay twice.

Do not recollect because assembly failed. Do not start Market/Core/A/B or generate the R2B instruction
until the complete 22-stock and whole-source authority gates pass.

## Deliverables

One immutable report ZIP plus SHA-256 sidecar, containing the new raw receipts, frozen plan,
Class-C versions, both replays, blockers, code changes and validation receipts.
iCloud local-copy and server-sync status are recorded separately to avoid claiming a copy is a completed upload.
