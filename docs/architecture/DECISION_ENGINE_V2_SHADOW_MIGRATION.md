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
  -> accepted_decision_plan
  -> accepted renderer + validator
  -> dedicated accepted test sink
  -> migration recommendation
```

The raw candidate renderer and its prior test-sink receipt prove candidate-path behavior only.
After adjudication, `accepted_decision_plan` is the sole authority for summaries, counts,
rendering, validation, test delivery, and readiness. A required adjudication that is missing or
non-final stops at `NOT_READY`.

V2 is archive/test shadow only. The v1 production canary, subject scope, decisions, natural-proof
counters, scheduled tasks, delivery paths, and persistence remain unchanged. Migration requires a
separate bounded instruction; this phase does not expose v2 in production.
