# M9 Interest-Bearing Debt and Liquidity Mapping

## Result

- Status: `M9_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `5e46a5ff80fbff32145cef0ccf68d906dfcdf5b4`
- Work-instruction commit: `af361e68ba843ee211bcd1e12750c1cf95a8461e`
- Implementation commit: `357a1d577ffd24c96bb0f3ce2c0baf1f13458658`
- Contract: `interest-bearing-debt-liquidity-v1`

## Frozen accounting policy

- Debt is the complete sum of verified, non-overlapping interest-bearing components.
- Total, current and non-current liabilities are never debt proxies.
- Net debt is complete debt less compatible cash and cash equivalents only.
- Lease liabilities are `SEPARATE_CONTEXT_ONLY`.
- Restricted cash is `EXCLUDE_FROM_NET_DEBT_CASH_BASIS`.
- Bank, insurance and reinsurance subjects route to `SECTOR_FRAMEWORK_REQUIRED`.

## Measured archive coverage

The preserved US archive contains no reusable balance-sheet payload, so real US direct and
derived coverage is `0`; the generic SEC contract is proven only by a labeled synthetic
fixture. The seven preserved KR official filings contain six non-financial issuers and one
insurance issuer. Among the six non-financial issuers, cash is direct for
`6`, debt components total
`17` direct facts, and complete debt total plus net
debt are derived for `5` issuers. `010120` remains
PARTIAL because an unsupported convertible preferred liability prevents complete scope.
`003690` is routed away from industrial net debt.

## Safety and validation

- Ticker-specific and fuzzy mappings: `0`
- Total-liabilities-as-debt and partial-debt-as-total emissions: `0`
- Financial-sector generic net-debt emissions: `0`
- Compact AI, Directional, Timing, renderer, sufficiency, Daily Delta and warning changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `295 passed`
- Full tests: `2950 passed` with `2` existing deprecation warnings
- Ruff and `git diff --check`: `PASS`

## Next scope

`INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION`

Working capital remains a separate bounded package. Financial-sector capital frameworks,
Directional consumption, model proof, production activation and schedule resume remain out of
scope.
