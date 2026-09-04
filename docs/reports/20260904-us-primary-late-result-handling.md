# US Primary Late Result Handling

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Classification

`PRIMARY_LATE_RESULT_STATE = SUPERSEDED`

The primary persisted a complete candidate before backup claim, but had not validated it. Backup replaced the claim UUID at `08:30:39.046046`. When primary validated at `08:35:19.670`, the finalizer compared the current shared claim ID with `1e008869-f2e3-4a52-ba32-fe7b31bf472e`, found `15e1258f-7654-47d5-a58d-23d22310dedd`, moved the primary temp file to the rejected archive, and returned `stale_claim_output`.

The archived candidate exists at `/Users/sskim/Codex/thesis-monitor/data/ai_review/rejected/2026-09-04-us-run-55-54cd536c6e4d--daily-review-v3.10--dc747fff8565.json.1e008869-f2e3-4a52-ba32-fe7b31bf472e.stale_claim_output` with SHA `3dfaea9ce0643e56a676b6740cae7aedab2a7f01fdff090265923c4562d4b276`. It was not accepted, had no delivery eligibility as an AI output, and was never sent. This was deterministic fencing, not an orphan or duplicate delivery.
