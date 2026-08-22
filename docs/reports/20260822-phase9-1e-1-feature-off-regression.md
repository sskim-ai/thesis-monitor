# Phase 9.1E.1 Feature-OFF Regression

The branch and previous operating main were replayed against the same operating database with a
fixed generation time and working-capital mode `OFF`.

- AI packet SHA-256 on both implementations:
  `023768a902041fe81209395738e8f109cf24a562b5fb0b4c25101759cd31a938`
- Deterministic fallback SHA-256 on both implementations:
  `f0ab9ca5167c5d829190322150371307a9116279b93fe4e0b5b8e433d5a68ed6`
- Working-capital user-visible contexts: `0`
- Production AI diff: `0`
- Fallback diff: `0`

Public Action remains `0.4.5`, output schema remains `4`, and operation IDs remain `20/20` unique.
Phase 9.0E mode and cash-flow output are unchanged. No Telegram, Scheduled Task, Pilot, DB, warning
or archive mutation was used for this proof.

