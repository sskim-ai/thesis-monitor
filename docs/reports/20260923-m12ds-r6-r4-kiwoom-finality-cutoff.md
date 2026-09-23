# M12DS-R6-R4: Kiwoom Finality and Cutoff

## Authority and Boundary

- Base: `e25e41baf231318b873adf62cab8433eeded5b0e`.
- Work-instruction commit: `0273b66c540f313d3e88657158b8d8d2f09eadf8`.
- Operating main remains `2097645892e30d84aba435416f98e7f9545a87fa`.
- Original five instruction files are byte-exact in the instruction commit.
  This implementation removes only three Markdown trailing-space occurrences.
- Local audit branch only. No merge, push, deploy, production send, recipient
  intent, DB decision/warning write, scheduler, notification, or broker mutation.
- Existing four AI tasks remain PAUSED; production launchd remains disabled.
- No Alpha Vantage calls or new provider.

## Source Findings

Routing is recovered for all 22 canonical market symbols from successful
gateway `resolved_symbol` receipts, not default exchange guesses. ETF identities
originate from the provider stock list; known equities use the existing registry.
XLC uses its successful R2 response and matching request/hash companion because
its R1 request was HTTP 502. SPY is NY, not NA.

At 17:19:11-17:19:24 KST on September 23, a bounded direct usa06012 sweep
returned all 22 responses. Each contains September 22 and September 21 daily
rows. September 23 provisional rows are retained but excluded from the completed
pair. No future row is required to calculate the historical pair.

Initial offline checks rejected eight ETF responses because a May 1 row had
`upd_stkpc_tp=1f`. That older row is not consumed. The repair limits conflicting
basis checks to the two selected dates, while preserving the complete raw body.
The same 22 saved responses pass dated-pair validation without any refetch.
The original failed inspection receipt is preserved, not overwritten.

**Finality is unresolved.** Comparing earlier adjusted gateway rows with the new
direct adjusted rows finds the same September 22 O/H/L in 22/22, but a different
close in 19/22. Examples: SPY 774.12 to 773.38, QQQ 747.35 to 747.46,
SOXX 569.64 to 572.78. These are different observations, not a daily return.
The gateway source maps usa06012 cur_prc directly to close. However, its earlier
upstream wire body and loaded-process code SHA are not independently preserved.
Provider extended-hours exposure, day-rollover correction, or acquisition/version
differences remain hypotheses, not established root causes.

The official daily-row close semantic stays accepted. These discrepancies block
promotion to regular-session-close authority. Later short-term stability alone
must not erase contrary historical evidence.

## Actual Cutoff

The existing morning source ledger owns the macro collection group at
08:08:12-08:08:52 KST. Its 22 US entries report `ValueError`; it does not own
each upstream response, route, and acquisition timestamp. Qualifying cutoff
coverage is therefore 0/22. No file mtime or afternoon response substitutes for
actual morning availability.

A manual observer is prepared for the next September 24 configured windows:
08:05, 08:10, 08:15, 08:20 KST. It is **not launched or scheduled**. It requires
the frozen route-file SHA, preserves raw UTF-8 bodies/hashes and actual UTC/KST/ET
timestamps, and stops at the first complete availability attempt. Its conservative
qualification requires the entire attempt inside the selected minute. Late/missed
attempts fail closed and are never backdated. This is an observation constraint,
not a new production freshness threshold.

The observer has at most 88 data requests, one token acquisition, zero retries,
no pagination, no quote/model/send surface, and a fresh output-directory guard.
Availability PASS does not promote finality or authorize inference.

## Local Implementation

- `scripts/m12ds_r6_r4_kiwoom_finality.py`: raw/body identity, routing, dated
  pair selection, narrowly scoped extended-hours evidence, cutoff/full-universe
  gates, stable sector ranking with XLC required, and dated macro information.
- `scripts/m12ds_r6_r4_cutoff_observer.py`: manual read-only observer, plan-only
  by default. It does not register a scheduler or alter production runtime.
- The macro information formatter emits `최신 확인값 (기준 YYYY-MM-DD)` with
  zero direction refs. It consumes the R3 authenticated-envelope validator and
  is audit-only. Actual final-message integration/capture remains unexecuted.
- KR R3 raw receipts independently revalidate KOSPI/KOSDAQ post-close parity and
  both venues' TOP3/BOTTOM3. They are qualification history, not new generation
  values. Fresh KR8/night D/W/M and fresh message proof are not claimed.

## Validation and Artifacts

Focused tests include quote/daily distinction, wrong exchange, response hash,
future/stale date, basis/currency conflict, provisional exclusion, quote-movement
requirements, no SPY-to-universe extrapolation, XLC completeness, exact cutoff,
no-lookahead, manual-observer no-network preflight, and dated macro separation.
Existing KR, night D/W/M, price structure, and policy tests remain unchanged.

Exact-commit validation, raw responses, hashes, source receipts, and the final
report are stored outside Git under the task's local Reports directory. The
final JSON receipt owns actual test counts/status. Remote CI is not run because
push is forbidden.

## Decision

Current source gate: **NO**. Expected stop state unless new independent evidence
closes finality: `M12DS_R6_R4_KIWOOM_FINALITY_UNRESOLVED`.
Market/Core/A/B and the 24-message success bundle must not run or be fabricated.
The independent current-quote route was not present in approved adapter code;
bounded separate approval was requested rather than silently expanding it.
The private final report records whether that approval/evidence arrived.
