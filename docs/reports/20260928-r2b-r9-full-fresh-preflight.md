# R2B-R9 Full Fresh Requalification: Pre-Network Closeout

## Decision

`R2B_R9_LIVE_ADAPTER_REQUALIFICATION_GAP`

This is a pre-network contract failure, not a provider timeout, unavailable-data
result, or model failure. The requested fresh live qualification was **not
executed**. No prior result was relabeled as R9. R8 is superseded; its missing
comparison ZIP was not a prerequisite and was not used as a blocker.

The R9 instruction explicitly requires product/configuration conflicts to be
reported before network and prohibits inheriting the old complete-source flag.
The accepted R7 executable contract was preserved, not changed during this proof.

## Identities

- Branch: `codex/r2b-r9-full-fresh-requalification`
- Base/report-only R7 final: `d824014b7f9fad44a1619850d81a657925c6cf80`
- Tested R7 runtime: `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- R9 instruction-first commit: `da925a96c5f8d905da16ee7daee5cf079db54b9e`
- Operating main, unchanged: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- Non-document tree entries compared: 1,157; changed runtime/config entries: 0.
- Final report-only commit is recorded in the ZIP repository receipt.

## Blocking Contract Gaps

### B1: Night-Futures Product Scope

R9 expects KOSPI200 only. `app/macro/providers/krx.py:59` marks the unified
receipt unavailable unless there are exactly **two** observations.
`app/jobs/probe_krx_night_futures.py:27` declares KOSPI200 and KOSDAQ150; the
provider constructor has no product-scope parameter. The active 24-role source
contract also requires both product artifacts.

Merely hiding KOSDAQ150 in the message would not repair acquisition, receipt,
replay, and source-authority parity. No two-product query was sent in R9.

### B2: Market Display Selection

The accepted path is `daily_digest_renderer` ->
`accepted_calibration_message_service.calibration_market_render` ->
`market_numeric_claim_service.render_typed_market_facts`.

It joins every eligible numeric claim in source order. It does not implement
the R9 both-market sector TOP3/BOTTOM3 selection, and it can retain individual
dated index/yield rows. This is not evidence that stale values passed R9: no
live facts were acquired or displayed. It is a product-format contract conflict.

A new, explicitly synthetic six-sector plus yield diagnostic exercised both
market renderers offline. Source order and the raw yield row were retained;
ranked TOP3/BOTTOM3 blocks were absent. These outputs are diagnostic fixtures,
not R9 market messages or investment evidence.

### B3: Fresh Acquisition Composition

`scripts/unified_live_cohort_proof.py` is an older REV8 controller, not a fresh
R9 controller. Its `supplemental_class_c` reads persisted macro observations,
then imports earnings-comparison facts, quality bundles, financial-source
graphs and issuer-bridge output from parent accepted stock packets for all22.

Those paths were inspected, not executed. Reusing them would violate R9 even
if the individual facts still passed historical eligibility checks.

Existing official source owners remain reusable building blocks. This report
does **not** claim that fresh SEC/OpenDART acquisition is impossible. It records
that no end-to-end, all22 R9 request/receipt/composition plan was qualified.
Native SEC discovered-exhibit traversal and OpenDART pagination must not be
invoked without finite request/page/document budgets. Unresolved budget fields
are null and dispatch is disabled, never interpreted as unlimited permission.

### B4: Macro Observation/Publication Time

`app/macro/providers/ecos.py:48` creates `observed_at` from the query `as_of`
date. Its normalized raw payload retains the statistic name but not the
original observation period. USDKRW is mapped by the current Market consumer;
other unconsumed series must not be silently promoted.

A fresh HTTP response alone would not establish the correct observation date
or `LATEST_PUBLISHED_VERIFIED`. Preserve raw source period and current retrieval
identity, or explicitly deny the optional row. No arbitrary day threshold or
cached-value substitution was introduced.

## Inventory And Session

- Current production-eligible static universe: US14 + KR8 = 22.
- Runtime-bound role groups: 24, with consumer-file hashes and schema inventory.
- Stock chart/valuation read roles: 88, none dispatched.
- US market symbol registry: 22 symbols, none dispatched.
- Macro registry inventory: FRED13, EIA3, ECOS4; current Market mapping recorded
  per series, without inventing observation dates or values.
- Actual preflight: 2026-09-28 13:58 KST; ad-hoc mode, not scheduled execution.
- Canonical completed sessions at that time: US 2026-09-25; KR 2026-09-23.
  KR was intraday/provisional; no final-close claim was made.
- Repository unified windows: US 08:10/08:15/08:20, KR 16:00/16:05/16:10 KST.
  Window configuration matched the instruction; activation was not performed.

## Execution Accounting

| Stage | Result |
|---|---|
| Fresh provider requests | 0; not started |
| Fresh stock packets | 0/22; not attempted, not 22 data failures |
| Fresh Market contexts | 0/2; not attempted |
| Current/prior financial and quality reproof | NOT_RUN for all22 |
| 005930 / 047810 / SNDK / 000660 / SKHY / CPNG live controls | NOT_RUN |
| Fresh source seal / FullSourceRunSeed / authority graph | Not generated |
| Offline source replay twice | NOT_RUN: no R9 source corpus |
| Market / Core / A / B model calls | 0 / 0 / 0 / 0 |
| Fresh messages | 0/24; not generated |
| Complete source adapter qualified | false |
| Human-review 24-message ZIP | Not generated |
| Scheduler-cutover instruction | Not generated or executed |

No source-only or unknown-limit output was manufactured to inflate these counts.
All missing live receipts, periods, packet hashes, and output hashes remain null
or empty with `NOT_RUN` reasons in the result bundle.

## Validation

Validation executed against clean instruction commit `da925a96`, whose executable
bytes equal accepted R7. The final commit changes only this report.

- Focused: 717 passed, 0 skipped.
- Full pytest: 6,222 passed, 63 skipped, 0 failures/errors.
- Skip/xfail identities exactly match the prior R7 validation baseline.
- Ruff, `git diff --check`, Investment Knowledge and Chart Knowledge: PASS.
- Test network guard: 0 socket/DNS attempts, 0 external connections.
- R9 read-only preflight: runtime parity, universe, window and safety checks PASS;
  four configuration/composition conflicts remain open.
- New R9 freshness receipts, latest-publication proof, live comparison controls,
  all22 live source closure and live AI binding remain NOT_RUN. Regression PASS
  is not fresh qualification PASS.

The report helper's first local attempt used a Pydantic method on the session
dataclass and stopped. It was corrected to `dataclasses.asdict` and rerun in a
new report directory. No runtime/policy code changed, and neither attempt made
a provider/model request. This was a reporting-helper correction, not a live
data or model retry.

## Safety

Preflight before/after hashes confirm unchanged operating configuration,
production database files, scheduler inventory and operating HEAD. Both
worktrees were clean at the check. No secrets or raw recipient IDs are exported.

Alpha planned/actual 0; Massive/mock/undeclared fallback 0; Telegram 0; recipient
intent 0; production DB/decision/warning writes 0; scheduler/notification
mutation 0; broker/deploy/main merge/remote push/restart 0.

No P0 incident was observed because live dispatch was withheld. Four P1
preflight contract gaps remain; this is not a claim that the unexecuted live
pipeline has passed P0/P1 validation.

## Bounded Resume Scope

Before a new fresh acquisition, close and freeze these exact contracts offline:

1. KOSPI200-only collection/receipt/replay/render scope, including missing W/M.
2. Explicit internal-versus-display Market selection, including both-market
   qualified sector TOP3/BOTTOM3 and canonical numeric bindings.
3. All22 fresh official financial/business and macro acquisition composition,
   finite per-provider call/page/document budgets, private storage and new
   retrieval identities, with no parent-packet business/quality carry-in.
4. Source observation/publication period preservation and current-query proof;
   optional unqualified fields stay unavailable.

Then issue a new source-generation identity, acquire all mutable roles, seal
and replay the source graph twice, prove the R7 guard on fresh facts, and only
after complete qualification run fresh Market/Core/A/B and render 24 messages.
No retry-until-PASS, implicit provider fallback, or scheduler activation.

The result is delivered as one secret-scanned report ZIP and one SHA-256 sidecar
to the approved iCloud Drive destinations. Upload status is verified separately
and is not inferred merely from a local copy.
