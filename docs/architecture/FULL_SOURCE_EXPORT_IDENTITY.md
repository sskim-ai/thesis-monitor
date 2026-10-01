# Full-Source Export Identity

The current `full-source-run-seed-v1` serializes its generation as
`seed.parent_run_id`. Source-only exporters use
`resolve_full_source_generation_identity` and the shared
`source_only_generation_preflight` before constructing review artifacts.

The parent value must be a nonempty string. A simultaneous `seed.run_id` is
only corroboration and must be a nonempty exact match. Run-id-only legacy
seeds are not supported by this current-source continuation. Identity values
are never normalized, replaced, or inferred. Full-source, source-view,
provider-plan and KIS generation IDs must match exactly.

The regression fixture `tests/fixtures/kr8_full_source_seed.json` is the exact
serialized seed from the verified REV40-R1 source archive. Its enclosing
whole-source file SHA-256 is
`2935bd02c7116e292ea7664d657db89e9d1b7590b757265288c0b08e60f6c1fc`.
Tests round-trip it through `FreshKRSourceRunSeed`, reproduce the old failed
lookup, and execute the repaired preflight. The existing full production
composer regression also serializes its real output into this same preflight.

`Kr8Continuation` inherits the accepted model, prompt, schema, renderer and
budget behavior unchanged. Its source-only projection consumes the existing
owner outputs and does not fetch data, recalculate source ownership, rewrite
generation IDs or read independent judgments. Native valuation is projected
once; forward evidence keeps separate dated KIS receipts and unavailable states.

Provider/model source identity and execution-code identity remain separate:
the original source code registry is preserved, while the repaired exporter
and new continuation controller receive a new execution freeze. No previous
diagnostic archive is overwritten or relabeled as valid blind evidence.
