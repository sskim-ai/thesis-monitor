# Production Bounded Rewrite Contract

Contract: `production-bounded-rewrite-invariance-v1`.

A quality rewrite may be attempted at most once. It must preserve decision fields, claim types, logical-condition references, evidence references, numeric and price references, buyer/holder stance, and severity. A successful rewrite requires a Class-A/B rerun. If rewriting fails or changes a protected field, the rewrite is rejected and the original safe candidate remains the authoritative artifact; no retry loop is opened.

The production integration uses deterministic numeric-reference language normalization, not model-owned semantic rewriting, for the observed Run-57 particle/label defects.
