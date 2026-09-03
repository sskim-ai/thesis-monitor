# Retry, Dedupe, and Fallback Repair

Retry now discovers the same states that enqueue/hold persist and records discovery before calling
the normal delivery function. A fresh process can recover pending work without rerunning analysis,
packet generation, the renderer, or the model.

At the fallback deadline, a completely unsent AI attempt no longer stays pending forever. Its
deterministic payload is restored, the AI terminal reason is recorded, and one fallback set is
sent. A partially sent AI set is not mixed with fallback; it is held for manual integrity review.

Proof:

- normal E2E AI sent `9`, fallback `0`, duplicate `0`
- retry after archive completion: `no_pending_ai_delivery`
- backup after AI send: `0`
- fallback after AI send: `no_held_session`, sent `0`
- controlled 9-row failure: AI sent `0`, fallback sent `9`, second fallback sent `0`
