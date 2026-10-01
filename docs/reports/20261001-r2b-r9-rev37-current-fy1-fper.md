# REV37 Current FY1 fPER Owner

Terminal: `R2B_R9_REV37_CORPORATE_ACTION_ROUTE_GAP`.
Production integration readiness: **NO**. Full code validation is green; official
corporate-action effective-window authority is not closed.

## Repository
- Base REV36: `e974621759e6ab76296485a8e2b47d707be4c5a7`.
- Instruction first: `730cafe4789d4e5ab6e8244ca259705357935f72`.
- Final tested implementation: `08dbc3f9a857d3784f2c6bca50710ecf6f4d3301`.
- Branch: `codex/r2b-r9-rev37-current-fy1-fper`.
- Main/operating unchanged: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
- Raw evidence and immutable report ZIP/SHA remain outside Git. No push.

## Bounded Proof
REV36 ZIP SHA, sidecar, CRC and manifest verified. Its EPS/PER receipts are unchanged.
The new offline owner, opt-in probe and tests are not production imports.

At the frozen 2026-10-01 acquisition cutoff, the existing XKRX calendar selected
2026-09-30. KIS unadjusted daily closes qualified for 7/7 EPS-covered securities;
all seven incomplete October 1 rows were excluded. Request flag 0, exact security,
currency, target OHLC, source hashes and calendar receipts are bound independently.

KR8: qualified EPS 7, provider FY1 PER 6, unadjusted close 7, current FY1 fPER 0,
typed outcomes 8. 003690 remains unavailable EPS, not N/M. No estimate refresh.

Auth 1; action queries 5; price queries 7; data total 12/20; retries 0. All data-to-data
intervals exceeded 1.1 seconds. Auth-to-first-data was 0.991985 seconds, below 1.1;
resetting the timer after auth is a disclosed transport follow-up, not an all-call PASS.

## Open Boundaries
1. Face-value replacement returned 100 rows with `tr_cont=F`; the pinned official
   route example continues only `M`. Unproven continuation is not terminal completeness.
2. All-security pages include alphanumeric six-character identifiers. This bounded
   parser rejects them globally; exact non-target representation handling needs repair.
3. Official record-date/unspecified-date query windows do not establish complete
   effective-date coverage. Listing/record/ex-rights dates are not interchangeable.

No corporate-action absence or actual fPER arithmetic was asserted. Pure effective-date
and Decimal arithmetic positives are synthetic only. No EPS adjustment is implemented.
Trailing PER, secondary KIS provider FY1 PER and current-price FY1 fPER stay separate.
Only valuation/NewBuyer/Holder roles are allowed; Overall/Core/Pass-A/business refs are not.

## Validation And Safety
- New tests: 78 passed; focused: 396 passed, 1 deselected.
- Full: 7442 passed, 63 skipped, 0 failed/errors, 3 existing warnings; 22m27s.
- Ruff, diff, Investment Knowledge, Chart Knowledge, secret scan: PASS.
- Actual-source replay: 8/8 outcomes, 7 prices and 5 family receipts identical.
- Additional actual-source negative controls: 56/56 rejected.
- JSON-native role-array fix preceded all live calls; its earlier interrupted
  validation is preserved separately and never counted as a completed full PASS.
- Production DB/WAL, env and scheduler protected fingerprints: 121/121 unchanged.
- Models/messages/Telegram/orders/main merge/push/deploy/restart/GC: 0.

Result: `thesis-monitor-20261001-r2b-r9-rev37-current-fy1-fper-report.zip` plus SHA,
with full source, request/receipt, authority gaps and validation evidence. Delivery
is only to iCloud Drive / Thesis Monitor after secret/integrity verification.
Do not execute REV38 until the action-specific owner gaps are resolved.
