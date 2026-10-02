# R2B0 One-Shot Stock Source Acquisition

This opt-in source-only proof is not registered as an operating source adapter.
R2A-R5 remains the accepted KRX historical proof; it was not recollected or
relabelled as current. Operating main, schedulers, prompts and validators remain
unchanged. No model, renderer, Telegram, delivery or production database owner ran.

## Frozen Ownership

Instruction: `80debb5f5ae8b24491b46b52cea863efd483ef99`.
Implementation: `5d089f8bae0b1ab4eed93cd076e04cb3cc359d9b`.
Base: `fdc1a1e69f3941676927b38c4d81ba4b4d6d369c`.
Plan file SHA: `e7d63a5278937b5ff6949ff55e93acf984875d57c5eb09de765eaec1327167b4`.
Run: `m12ds-r6-r5f-r2b0-20260926T075400Z`.

The canonical read-only universe exactly matched US14/KR8. The plan froze four
roles per subject: adjusted daily/weekly/monthly and unadjusted weekly valuation.
The existing session owner resolved completed sessions US 2026-09-25 and KR
2026-09-23. Returned dates are unchanged; this weekend acquisition does not claim
to be a scheduled production cycle or establish regular-close finality.

The configured local OHLCV service selects `KiwoomProvider`. Its exact clean code
and effective configuration were fingerprinted. An isolated process reused its
actual `get_bars`, pagination, normalization, authentication and rate-limit owners.
Only its process-local transport was restricted to the current planned chart
route, subject, exchange, timeframe, basis and continuation chain. No service
configuration or code was modified. US symbol lookup and investor-flow reads were
not part of the plan and were denied. Authentication was limited to one exchange.
Automatic retries were disabled in this isolated execution only.

Every source page has a pre-dispatch request intent, exact response bytes, source
hash, sanitized continuation metadata and timestamps. Every role has a unique
plan identity, normalization artifact/hash and result. No auth body, token or
general response headers were retained. Native pagination was declared before
dispatch and counted separately. Offline replay consumed the exact captured
requests and raw pages through the same source normalizer without a live client.

## Observed Result

- Logical roles attempted and captured: 88/88.
- Original provider data responses: 290; authentication: 1; total transports: 291.
- Offline raw-owner normalization reproduction: 88/88.
- Existing OHLC integrity and role binding gate: 85/88.
- Four usable roles: US 13/14, KR 8/8, total 21/22 subjects.
- Retries, fallback and prohibited-provider calls: 0.

CPNG has three unusable roles. The original 2023-06-05 row reports open 16.35
above high 15.80 in adjusted daily, and open 16.35 above high 16.20 in both
adjusted weekly and unadjusted weekly valuation. The existing
`ohlcv-provider-integrity-v1` owner rejects these as `HIGH_LT_OPEN`. Original
provider bytes reproduce the defect; it is not a transport error or a newly
introduced normalization difference. Monthly passed. No row was clipped,
dropped, repaired, swapped, replaced or retried.

## Gate and Handoff

Terminal: `M12DS_R6_R5F_R2B0_ONE_SHOT_SOURCE_ACQUISITION_PARTIAL`.

The instruction permits materializer implementation only after 88 usable roles.
That gate did not pass. Pure stock materializers, observed-business/financial
projection integration, full source graph assembly and packet hashes are
**NOT_REACHED**, not passed. Optional estimate/CF-WC absence is not a new blocker.
Network-free source prequalification, live source qualification and AI adapter
qualification stay false. R2B is not generated or executed; R3 remains blocked.

The next decision is bounded CPNG source-integrity handling under a separate
instruction, preserving this frozen raw evidence. Do not repeat all 88, search
historical archives for replacement envelopes, weaken the integrity validator,
or silently discard the malformed rows.

Implementation validation: focused 471 PASS, full 5571 PASS / 63 unchanged skips;
Ruff, diff check, Investment Knowledge, Chart Knowledge and disabled-entrypoint
smoke PASS. No new skip or xfail. Final exact-SHA validation and complete raw
receipts are in the local immutable result ZIP, not tracked or pushed to GitHub.
