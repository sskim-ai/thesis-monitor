# KR Market Breadth

## Definition

KR breadth uses exact `ka20001` counts for rising, falling, and unchanged securities. Eligible
count is their sum. Listed count and limit counts are retained separately from `ka20003`/`ka20001`.
Missing or malformed counts make breadth unavailable; they never become zero.

## Scope

KOSPI and KOSDAQ are preserved independently and may also be combined by summing counts. A combined
ratio does not replace scoped ratios. KOSPI large/mid/small rows are size context, not sectors.

## Session Identity

Breadth is valid only after composite close/return identity matches the target-date historical row.
The completed-session proof prevents a current-only response from being attached to the wrong date.

## Interpretation

Breadth can confirm or contradict headline index direction. It cannot establish why the market
moved. Sector breadth, price return, participant flow, and concentration retain separate semantic
roles, and exact structured tuples need not all be rendered in prose.
