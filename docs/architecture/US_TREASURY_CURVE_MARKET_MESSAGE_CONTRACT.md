# US Treasury Curve Market Message Contract

The primary user-facing rate block is the nominal U.S. Treasury constant-maturity curve: FRED `DGS3`, `DGS5`, `DGS10`, and `DGS30`.

Each line requires a latest safe observation and the immediately previous valid observation from the same series. The displayed delta is `(current percent - previous percent) * 100` basis points. It is never a percent return and is never compared across maturities.

Observation dates are retained. When all four share one date, the renderer owns one dated section heading; mixed dates remain line-qualified. Missing facts, incomplete pairs, and arithmetic mismatches are rendered with distinct fail-closed reasons.

The 10-year real yield may remain in canonical macro evidence, but it is not the primary user-facing rate block. This contract does not alter macro axes, stock decisions, or market-selection thresholds.
