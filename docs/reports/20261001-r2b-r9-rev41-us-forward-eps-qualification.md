# REV41 US14 Exact Forward EPS Qualification

Terminal: `R2B_R9_REV41_SOURCE_STABILITY_GAP`.

This is an automated-access authority gap, not a transient HTTP failure.
Do not retry requests or change headers to work around it. Do not start REV42
valuation integration automatically.

## Evidence

- Base: `3ed46521c7bd50565665747ff35d872d3e601f7d`, verified at the accepted
  remote preservation ref. Operating main was not used as the development base.
- Implementation: `5efffa765c7f18adae2c2fe3ba764449e4d463f2`.
- Nine candidate families; 19 candidate-data requests (8 smoke, 11 expansion),
  nine direct documentation captures. No retries, auth or redirect following.
- Yahoo public-table/embedded-JSON FY1 semantics: 11/14. Exact NTM: 0/14.
  All 14 subjects have typed states. Automated-adoptable source families: 0.
- TSM: direct ADS EPS basis unresolved. SKHY: completed-period anchor unresolved,
  additionally ADS basis unresolved. WRD: conflicting default/explicit methodology
  modules, with additional CNY/USD and ADS-basis gaps. No EPS conversion.
- WULF's initial declaration used the wrong Nasdaq segment; SEC cover evidence
  corrected the declaration to Nasdaq Capital Market. The validator was unchanged.
  Both initial and corrected offline results are retained locally.
- Estimate-as-of remains null; Current Estimate snapshot semantics are explicit.
  MU/SNDK FY2027 follow completed FY2026. Provider fiscal month-end labels are not
  exact 52/53-week filing dates. GAAP and normalized bases remain distinct.

[Yahoo terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html) require
prior permission for automated collection. That permission is not established;
semantic coverage is not source-use eligibility. The site-specific terms review
was completed after Stage C, a recorded procedural limitation. No further
candidate requests were made; the task-local collector is now closed.

StockAnalysis remains secondary: public EPS currency, accounting method,
estimate-as-of and ADS ownership were not formally qualified. Nasdaq public
returned a forecast skeleton; MarketScreener returned 403. FMP lacks an existing
configured key and verified US14 entitlement. Nasdaq Zacks samples do not
establish the required representative entitlement. Finnhub's prior premium gap
was not reprobed; Alpha Vantage remained policy-excluded. Finviz did not establish
an exact fiscal-year EPS owner. No global claim that no free source exists is made.

## Verification

Focused US/KR regression: 380 passed. Full pytest: 7,780 passed, 63 skipped,
three pre-existing deprecation warnings. Ruff, diff check, Investment Knowledge
and Chart Knowledge passed. Test network access was denied.

All 14 original and transport-redacted response replays have identical semantic
results, excluding the explicitly distinct raw-body hashes. Raw originals stay
local; report export removes anonymous transport identifiers. Raw data is not
committed to Git.

Model/Market/Core/A/B calls, Telegram, KR providers, KIS, Alpha Vantage,
production DB/scheduler mutation, main merge, push and deploy: 0.
The protected-state hash audit passed. No worktree cleanup was performed.

The detailed result, complete ledgers, redacted raw evidence, validation and
source hashes are delivered as
`thesis-monitor-20261001-r2b-r9-rev41-us14-forward-eps-source-qualification-report.zip`
and its SHA sidecar, only to the approved iCloud `Thesis Monitor` folder.

Next: close a permitted automated source contract or qualify a documented free
API before designing current-close/EPS integration. KR REV40-R2 semantics remain
unchanged.
