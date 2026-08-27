# KR Daily 1200 Merge Contract

## Path Decision

The merge path is not entered because the supported official endpoint exposes no older-window
request. Speculative use of ignored query parameters would produce overlapping latest rows rather
than an older page.

The existing `merge_history_pages` contract remains the required future implementation boundary:
same identity and basis, normalized trading dates, economic overlap equality, dedupe, ascending
sort, exchange-session gap detection, completed-bar filtering, and exact 1200 trim.

## Current Gates

| Gate | Result |
| --- | ---: |
| WINDOW_CHAIN_SECURITY_BASIS_CONFLICT | 0 |
| WINDOW_CHAIN_ADJUSTMENT_BASIS_CONFLICT | 0 |
| WINDOW_CHAIN_DUPLICATE_BAR | 0 |
| WINDOW_CHAIN_OUT_OF_ORDER | 0 |
| WINDOW_CHAIN_PARTIAL_BAR_INCLUDED | 0 |
| DUPLICATE_COMPLETED_BAR_AFTER_MERGE | 0 |
| CORPORATE_ACTION_BASIS_CONFLICT | 0 |
| ADJUSTED_RAW_PRICE_MIX | 0 |

All counters are zero because an unsupported second window is fail-closed, not merged.
