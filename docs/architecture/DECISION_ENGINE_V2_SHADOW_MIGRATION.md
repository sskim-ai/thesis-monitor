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

The retrospective shadow and accepted-ownership phases are complete. The bounded production
cutover adds an accepted-only runtime behind explicit feature state while preserving scheduled
tasks, delivery routing, Price Structure, valuation, and persistence boundaries. Deployment may be
armed only after full-inventory preflight and dedicated test-sink proof. Natural KR and US cycles
remain the required live proof; deployment alone must not be called `LIVE_PASS`.
