# Validator Hard Semantic Soft Classification

Date: 2026-09-04 KST

Status: shadow-only; no production mutation.

- Class A HARD_DETERMINISTIC: `33`
- Class B SEMANTIC_HARD: `16`
- Class C SOFT_QUALITY: `15`

Class A remains fail-closed. Class B is hard only for explicit metadata contradictions. Class C cannot veto a Class A/B-safe message and may request one bounded rewrite.
