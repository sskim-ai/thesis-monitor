# Shadow Investor-Flow Numeric Field Inventory

The immutable packet exposed 210 unsupported reconciliation fields: 30 exact paths for each of
seven KR stocks. The path shape is identical for `1d`, `5d`, and `20d`.

| Family within each window | Fields | Per window |
|---|---|---:|
| Participant flows | foreign, institution, individual, other_corporation, domestic_foreign | 5 |
| Display reconciliation | displayed_net, omitted_net, all_participant_net | 3 |
| Audit diagnostics | constituent_count, display_coverage_ratio | 2 |
| Total | | 10 |

Thus `10 fields x 3 windows x 7 tickers = 210`. All values originate from the existing positioning
reconciliation structure. They are useful for internal parity and attribution safety, but none owns
user prose. Canonical foreign/institution facts outside this audit subtree retain their existing
structured-prose contract.
