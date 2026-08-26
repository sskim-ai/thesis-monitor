# Fibonacci v2 Selector Path Audit

## Finding

The archived v2 selector path called `reference_select_price_structure()` three times. It was a
deterministic reference harness, not a variable AI runtime. No prior selection, human anchor, or
Fibonacci result is supplied to the new primary trial.

```text
WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED_BEFORE_REPAIR = NO
CURRENT_VARIABLE_AI_RUNTIME = signed-in local Codex CLI, archive-only, ephemeral, read-only
```

## Separation

Stage 1 receives only public price evidence and returns canonical IDs. The existing backend still
owns validation, Decimal Fibonacci arithmetic, confluence, and rendering. Production routes do not
import the archive trial script.
