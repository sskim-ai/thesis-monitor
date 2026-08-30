# V2 Production Runtime Contract

Contract: `v2-accepted-production-runtime-v1`

```text
complete packet inventory
  -> canonical evidence and local OHLCV
  -> signed-in Codex CLI / gpt-5.6-sol / xhigh
  -> candidate per subject
  -> bounded validator repair when required
  -> adjudication for every material change
  -> accepted_decision_plan
  -> accepted-only decision block
  -> normal delivery
  -> state advance only after complete delivery
```

Activation requires all four feature conditions: selector `v2_accepted`, V2 production enabled,
full monitored-stock target enabled, and V1 rollback available. Missing or non-final adjudication
suppresses only that subject's decision block. It cannot expose a raw candidate or silently render
V1 while the V2 selector is active.

The migration baseline is continuity evidence, not a frozen distribution. Same-evidence
unexplained decision churn fails closed. Price Structure, valuation, market messages, public
schema, market cap, target/stop, position sizing, and order execution are outside this contract.
