# V2 Path and Identifier Regression

The existing canonical repository path resolver remains the only V2 artifact path owner. The
runtime-state change occurs after absolute prompt/schema/cwd preflight and applies uniformly to
primary, backup, schema repair, and candidate repair.

Product-identifier typed-span handling is unchanged. Amounts, ratios, prices, ranges, dates, and
unsupported numeric strings keep their prior validation behavior.

- V2 schema path duplication: `0`
- V2 natural path regression: `PASS`
- Product identifier provenance regression: `0`
