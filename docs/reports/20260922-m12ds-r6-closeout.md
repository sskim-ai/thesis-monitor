# M12DS-R6 Initial Source-Gate Checkpoint

Superseded as a stop decision by the user's subsequent continuation request: the user
confirmed that September 22 night data is not expected at this cutoff and authorized moving
on. The FAIL receipt remains unchanged. Non-night collection and inference are proceeding
with unavailable night evidence excluded; final capture status must be read from the later
continuation report, not the initial counts below.

Executed through 2026-09-23 KST. Terminal:
`M12DS_R6_NIGHT_HISTORY_OR_DWM_FAILED`.
This is a validated local implementation, not a successful fresh message proof.

## Repository

- Baseline and unchanged operating/main: `2097645892e30d84aba435416f98e7f9545a87fa`.
- Local branch: `codex/m12ds-r6-market-message-coverage`.
- Instruction commit: `cfb6f939858a2b87be70c4f46a4b51eaf068aee5`.
- Frozen implementation: `427a65deae14be6bdb6f8a288bb211c08181bba1`.
- Merge, push, deploy, notification intents/sends, production DB/warning/scheduler changes: zero.
- R6 remote CI: not run; remote publication is forbidden in this task.

## Implemented and Offline Verified

1. Existing SPY/QQQ/IWM ETF proxies select actual completed US session rows, not the
   live last row or the KST collection date. Levels and returns have typed numeric ownership.
2. WTI and Treasury 3Y/5Y/10Y/30Y use source-published observation/release metadata.
   Publication cadence is separate from observation frequency and from a new daily signal.
3. Deterministic sector TOP3/BOTTOM3 uses same-session returns and stable fact-ID ties.
   KOSPI and KOSDAQ remain separate. SOXX is not part of the broad US sector ranking universe.
4. Source-owned stock price-as-of and active support/resistance render independently of
   fundamental entry and tactical watch ranges, including partial quote contexts.
5. Opt-in official KRX same-contract month backfill and weekly/monthly OHLC/progress display
   preserve unresolved return baselines. Daily presentation and accepted judgment policy stay unchanged.

Focused: **1,576 PASS**. Full pytest: **5,227 PASS / 63 SKIP**, with the exact skipped-test set
unchanged from the integrated main proof. Ruff and diff check: PASS.
Historical 22-stock regression: accepted decisions and entry ranges unchanged; price-as-of and
technical-side labels verified. Historical market numeric catalogs: 2 PASS.
These are offline regressions, not new model outputs or current coverage proof.

## Current Source Blocker

Generation: `20260923-m12ds-r6-current-20260923T002457+0900`.
Cutoff: `2026-09-23T00:24:57.958217+09:00`.
Completed US/KR regular sessions: `2026-09-21` / `2026-09-22`.

The unchanged night-reference owner required `2026-09-22`. Official queries for September
22 and 23 returned HTTP 200 with empty data. The available selected pair owned September 21,
with September 18 regular-session baselines. Both products failed current-reference/finality
requirements. An empty response does not prove why publication is unavailable; no publication
outage, exact next availability time, or source-calendar repair is asserted.

Current night source gate: FAIL. Market2/Core8/A8/B8: NOT RUN. New exact message captures:
**0/24**. New message quality and full current D/W/M E2E: NOT EVALUATED.
No cached candidate, historical message, or stale night row was substituted.

## Historical Month Recovery

The selected December contracts were backfilled using official KRX responses only:

| Product | Contract | Historical Through | Included / Elapsed | Missing |
|---|---|---|---|---|
| KOSPI200 | A016C000 | 2026-09-21 | 15/15 | 0 |
| KOSDAQ150 | A066C000 | 2026-09-21 | 15/15 | 0 |

Thirty normalized daily rows bind to verified raw-response hashes. Same-contract D/W/M OHLC
arithmetic and historical renderer components pass. The monthly return baseline is unresolved
and remains labeled as such. This does not satisfy September 22 current coverage.

Official KRX HTTP requests: **19 = 6 probe + 13 month backfill**; month-cache hits: 2;
retry: 0; month-backfill HTTP errors: 0. Earlier bounded implementation diagnostics used
one SPY OHLCV request and one public FRED WTI metadata request, plus official documentation
browsing. SEC/OpenDART cohort calls and new model calls: 0.

## Remaining Work

Source availability is the immediate blocker, not a model/validator failure. R6 is not ready
for message approval or main integration. On a later explicitly resumed proof, first verify a
fresh official completed pair against the unchanged reference owner. A later clock alone is
not sufficient. If still missing, stop with receipts. If PASS, collect all current sources and
complete the frozen Market/Core/A/B pipeline and exact 24 captures before human review.

Do not bypass freshness, infer publication availability, refit judgment policy, schedule an
automatic retry, merge, deploy, or begin M12DT onboarding from this closeout.

Artifacts are local under
`/Users/sskim/Documents/Codex/Reports/20260922-m12ds-r6-market-message-coverage`.
The report ZIP contains validation and clearly labeled historical diagnostics; the required
review ZIP is an explicit NOT_GENERATED receipt, not a fresh 24-message bundle.
