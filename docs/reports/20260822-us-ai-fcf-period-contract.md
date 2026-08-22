# US AI FCF Period Contract

Contract: `cash-flow-period-identity-v1`

The packet now supplies `required_period_label`, `duration_basis`, `is_ytd`,
`is_fy`, `allowed_period_claims`, `forbidden_period_claims`, and
`fcf_scope=OCF - PPE CAPEX`. The primary period also includes the canonical
label and retains period start/end when the source has them.

Supported identities are FY, YTD, QTD, and TTM. YTD forbids standalone-quarter
claims; FY and QTD forbid cumulative wording; all forms forbid annualization and
unverified calendar-period inference. The daily-review skill requires the exact
label and uses the existing industry-specific fallback sentence as its factual
period/scope seed.

Tests cover calendar and non-calendar fiscal identities, fiscal Q3 YTD, FY,
QTD, exact labels, and annualization rejection. No missing period start is
invented.

