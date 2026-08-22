# US AI Validator Negative Controls

The repair adds packet structure and strengthens period validation. It does not
relax numeric, semantic, ownership, or quality thresholds.

Negative controls continue to reject:

- YTD described as a standalone quarter
- FY or QTD described as cumulative YTD
- annualized or extrapolated cash flow
- omitted canonical fiscal-period label
- unknown or unavailable RR Fact IDs
- unsupported numeric arithmetic and ownership

Positive controls accept canonical FY, YTD, QTD, and non-calendar fiscal labels,
plus current RR only when its Fact exists in the catalog. Focused US suite:
`38 passed`. Full suite: `1372 passed`.

