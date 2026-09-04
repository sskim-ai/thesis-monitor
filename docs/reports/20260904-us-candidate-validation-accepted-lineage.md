# US Candidate, Validation, and Accepted Lineage

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

| Owner | Candidate | Persisted KST | Validation | Accepted |
| --- | --- | --- | --- | --- |
| Primary | market 1 + stocks 14; SHA `3dfaea9ce0643e56a676b6740cae7aedab2a7f01fdff090265923c4562d4b276` | `08:29:47.946` | `stale_claim_output` at `08:35:20.732` | 0 |
| Backup first | market 1 + stocks 14; SHA `fa1499059847e3a1bd3283fef2e266385960e4e1e18550f9f41e9cd0d9f24d11` | `08:33:17` | rejected 26 raw postpositions at `08:37:15.059` | 0 |
| Backup corrected | market 1 + stocks 14; SHA `29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b` | `08:41:37` | rejected 22 errors at `08:41:48.029` | 0 |

Primary and backup each had 125 bound references in the persisted draft shape. Backup used one correction. There is no final outbox review, accepted message artifact, or accepted SHA for this packet.

Final backup failures: 2 holder decision-variable, 2 working-capital ownership, 2 market semantic/provenance, and 16 typed valuation coverage/metric errors.
