# Phase 9.1E Selector Parity

The preview replays all 20 Phase 9.1D subjects without broadening selection.

| Result | Count |
| --- | ---: |
| 9.1D canary candidates | 7 |
| Inventory candidates | 5 |
| exact Trade AR candidates | 2 |
| future preview selected | 5 |
| Inventory preview selected | 3 |
| exact Trade AR preview selected | 2 |
| broad AR selected | 0 |
| AP selected | 0 |
| selector parity errors | 0 |
| broadened selections | 0 |

Selected preview subjects are `000660`, `005490`, `005930`, `010120`, and `086280`. MU and TSLA
retain their exact 9.1D context but are user-visible-suppressed under the documented
`cash_flow_higher_priority_no_incremental_unknown_resolution` rule. Their Phase 9.0E cash-flow
period ends match the working-capital balance dates, so the suppression is period-compatible.

Cash-flow periods that do not match the balance date are marked `INCOMPATIBLE_PERIOD`; they cannot
be combined or used as the same-period redundancy reason. The WC relation may still stand alone if
all its own gates pass. This is suppression-only divergence from 9.1D, never broader selection.
