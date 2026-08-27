# SR Nearest vs User-Visible Proximity

Contract: `sr-nearest-user-visible-proximity-v1`.

`summary.nearest_support` and `summary.nearest_resistance` identify the mathematically nearest
valid structural candidates. They do not promise that a zone is close enough for the Korean label
`가까운`.

The renderer consumes the existing `sr-proximity-relevance-gate-v1` output:

| Tier | Relevance | User-visible semantic |
| --- | --- | --- |
| `NEAR` | `ACTIVE_NEAR` | near support/resistance |
| `RELEVANT` | `ACTIVE_STRUCTURAL` | major structural support/resistance |
| `LONG_HORIZON` | `LONG_HORIZON_HISTORICAL` | long-horizon structural support/resistance |
| mismatch or out of range | any | omit |

No new percentage threshold is introduced. The closest remote zone is not promoted to fill an
empty near field. Safe weekly/monthly zones may still own a near label when their canonical tier is
`NEAR`. One primary zone owns each visible side/class semantic; internal alternatives remain in the
sidecar.

The final renderer validator binds an exact line to its numeric binding and zone provenance. It
checks `fact_ref`, semantic type, displayed range, tier, active relevance, and duplicate ownership.
Final prose is not accepted from keyword presence alone.

