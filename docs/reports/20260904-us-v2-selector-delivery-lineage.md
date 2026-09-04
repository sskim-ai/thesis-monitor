# US V2 Selector and Delivery Lineage

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

The V2 decision canary was armed for both claims and reached signed-in CLI execution. Each canary produced zero model results because `UnknownIssuer` prevented the response transport from completing. The outer review candidates still existed, but neither passed the authoritative AI review finalizer.

There was therefore no accepted-to-pending-to-sent AI chain. The observed path was:

```text
packet ready
  -> primary candidate
  -> backup claim supersedes primary
  -> primary stale rejection
  -> backup validation rejection
  -> hard fallback eligibility
  -> deterministic fallback 15/15 sent
```

The final backup validation happened after fallback and returned no held session with pending count zero. Operating revision for producer, primary, backup, and fallback was the same `5d5f336...` checkout.
