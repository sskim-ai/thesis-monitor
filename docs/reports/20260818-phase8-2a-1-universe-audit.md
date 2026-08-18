# Phase 8.2A.1 KRX Universe Audit

Date: 2026-08-18
Session: 2026-08-14 archive snapshot
Result: PASS; denominator unchanged

## Root Cause

This was a documentation wording error, not an eligibility bug. The implementation excluded
`listing_date >= session_date`, while the Phase 8.2A capability code block made that exclusion look
like an inclusion rule. Phase 8.2A.1 rewrites the policy positively as:

```text
LIST_DD < session_date
AND comparable_previous_close exists
```

The code now preserves the same eligibility while assigning separate exclusion reasons:
`new_listing_no_prior_close`, `future_listing`, `listing_date_missing`,
`listing_date_invalid`, and `missing_comparable_previous_close`. Same-session KRX comparison values
are never substituted for a previous exchange close.

## Listing Audit

| Observation | Count |
|---|---:|
| Raw daily rows | 2,763 |
| Prior-session listings | 2,763 |
| Same-session listings | 0 |
| Future listings | 0 |
| Missing listing dates | 0 |
| Missing comparable previous close | 0 |

## Denominator Before / After

| Scope | Before eligible | After eligible | Before excluded | After excluded |
|---|---:|---:|---:|---:|
| Aggregate | 2,532 | 2,532 | 231 | 231 |
| KOSPI | 804 | 804 | - | - |
| KOSDAQ | 1,728 | 1,728 | - | - |

The denominator and every breadth count are unchanged, so
`krx-kospi-kosdaq-common-share-v1` remains correct. The raw snapshot contains no same-session,
future, missing-listing-date, or missing-comparable-close row; fixture tests enforce those boundaries.
