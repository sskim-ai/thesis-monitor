# CPNG Generic Reconciler Control

Before: `PENDING_ONBOARDING`, inactive, production-ineligible, blocked by `INITIAL_EVIDENCE` and `DECISION_READINESS` after its final baseline existed.

The deployed generic `--market all --origin deployment_smoke` reconciler encountered CPNG without a ticker argument. It rebuilt canonical evidence, preserved the compatible final baseline, generated and validated an accepted-v2 `HOLD`, and allowed the existing coordinator to activate it.

After: `ACTIVE_READY`, retry class `NONE`, remaining blockers `0`, raw candidate grants readiness `false`, and first eligible session `2026-09-01`. Manual one-off resume and ticker bypass are both `0`.

Three retrospective P1s were closed before success: CLI artifact paths are absolute; market expectation facts use the existing `EXPECTATIONS` category; and `initial-onboarding-evidence-v1` now requires canonical market expectations. Each repair passed full local tests and Actions Test/Lint.
