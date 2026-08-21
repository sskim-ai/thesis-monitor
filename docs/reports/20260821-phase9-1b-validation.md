# Phase 9.1B Validation

- Focused Phase 9.1A/9.1B evidence and core tests: `37 passed`.
- Broader financial/runtime/delivery/KRX regression: `260 passed, 1 existing third-party deprecation warning`.
- Full pytest: `1301 passed, 1 existing third-party deprecation warning`.
- Deterministic generator: canonical-facts, complete-report JSON, and complete-report Markdown SHA-256 values are identical after rerun.
- Canonical arithmetic/provenance/idempotency: `0 / 0 / 0` errors.
- Ruff: PASS.
- `git diff --check`: PASS.
- Investment Knowledge v3 and Chart Knowledge v1 checksum parity: PASS.
- Public Action `0.4.5`; operationId `20/20 unique`; schema `4` unchanged.
- Runtime-import audit: core service is imported only by tests and the read-only evidence generator.
- User-visible behavior diff: `0`.
- Implementation exact SHA `a35c615a77b44b37739d4f6a73aa9f0f290ba831`; Actions run `32450301567`: Test PASS, Lint PASS.
- Final exact-SHA Actions: pending final documentation commit.
