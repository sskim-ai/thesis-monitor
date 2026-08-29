# Cross-Market AI Decision Engine v1

The engine produces an AI-owned analytical `BUY`, `HOLD`, or `SELL` classification. It never owns an order, position size, brokerage action, thesis mutation, or warning mutation.

## Ownership

```text
canonical company/market facts
  + completed-bar D/W/M feature facts
  -> decision-evidence-packet-v1
  -> signed-in Codex CLI gpt-5.6-sol / xhigh
  -> structured decision plan
  -> evidence/numeric/semantic validator
  -> shadow renderer
```

The model owns the conclusion. The backend owns calculations, evidence identities, numeric rendering, horizon validation, and delivery safety. There is no fixed weighted score.

## State

Current implementation is shadow/test only. Production packet, Public Action, scheduled prompts, fallback messages, assessment DB, and automated trading behavior are unchanged.
