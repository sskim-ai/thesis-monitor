# Track C — US Market: Night D/W/M + Nominal Treasury Curve

Night futures user-facing format:

Daily:
- open
- close
- gap%
- return%

Weekly:
- open
- close
- weekly%

Monthly:
- open
- close
- monthly%

Keep:
- near-month identity
- same-contract aggregation
- in-progress labels
- no contract splicing
- exact numeric provenance

Gap:
night open vs validated preceding regular DAY close.
Daily return:
night close vs same baseline.

Treasury:
replace primary standalone 10Y real-yield block with nominal:
3Y / 5Y / 10Y / 30Y.

Each:
latest safe yield + delta vs previous valid observation in bp.

Use approved authoritative source and prove maturity mapping/observation dates.
Keep real yield internal if useful, but not as primary user-facing rates block.
