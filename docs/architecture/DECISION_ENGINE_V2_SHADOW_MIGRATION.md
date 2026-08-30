# Decision Engine V2 Shadow Migration

Flow:

```text
decision-evidence-packet-v1
  -> label-blind signed-in Codex CLI / xhigh
  -> evidence maturity + scenarios + asymmetry/cost
  -> preconfirmation-asymmetry-validator-v2
  -> compact shadow renderer
  -> v1/v2 comparison
  -> material-disagreement adjudication
  -> dedicated test sink
  -> migration recommendation
```

V2 is archive/test shadow only. The v1 production canary, subject scope, decisions, natural-proof
counters, scheduled tasks, delivery paths, and persistence remain unchanged. Migration requires a
separate bounded instruction; this phase does not expose v2 in production.
