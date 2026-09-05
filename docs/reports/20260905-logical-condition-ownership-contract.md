# Logical Condition Ownership Contract

Contract: `source-owned-logical-condition-v1`.

The source evidence owns subject, generation, severity, condition identity, operator, and branches. Supported operators are `LEAF`, `ANY_OF`, and `ALL_OF`. IDs are deterministic from source occurrence identity and branch order. The AI claim may phrase a condition naturally, but validation uses only structured metadata and never infers an operator from candidate prose.

Claims carry the source condition reference, severity, coverage mode, and a tree of source branch references. Subject or generation mismatch, cross-condition branches, duplicate branch identity, severity mutation, and unknown source references fail closed. There are no ticker exceptions and no investment-decision rule changes.
