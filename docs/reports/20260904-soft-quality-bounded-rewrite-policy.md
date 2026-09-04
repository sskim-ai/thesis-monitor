# Soft Quality Bounded Rewrite Policy

Date: 2026-09-04 KST

Status: shadow-only; no production mutation.

A Class C warning permits no rewrite or one bounded rewrite. Fact refs, numeric refs, decision fields, semantic claim types, evidence refs, and metrics must remain byte-equivalent as structured sets. Class A/B rerun after a successful rewrite. Failed or invariance-rejected rewrite keeps the original eligible when the original passes Class A/B.
