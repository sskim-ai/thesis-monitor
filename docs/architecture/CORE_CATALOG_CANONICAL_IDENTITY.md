# Core Catalog Canonical Identity

The source-use catalog is owned by
`scripts.m12da_source_use_contract.canonical_sha256`. Its deterministic JSON
serialization uses sorted keys, compact separators and `ensure_ascii=True`.
The Core-to-A derivative authority must use this owner for `catalog_sha256`.

`unified_snapshot_contract.digest` remains the distinct full-source snapshot
identity contract, with `ensure_ascii=False`. Do not replace it globally or
rehash previously sealed packets, seeds or source authority graphs.

Catalog claim text is unchanged. There is no transliteration, character
stripping, normalization, new collection sorting or policy change. Equivalent
escaped/unescaped JSON converges after parsing and canonical serialization.
Meaningful array order and text/value/ref tampering remain distinguishable.
Existing source-metadata collection normalization remains owned by its existing
canonical source-use helper.

## Bounded R6 Continuation

`scripts.r2b_r6_continuation` inherits the existing R5 capture, official transport,
A/B owners and renderer. It cannot dispatch Market, Core, canary or repair calls.

1. Verify the exact R5 ZIP and every manifest member before extraction.
2. Replay the accepted Market/Core schemas and deterministic validation; require
   byte-identical raw/accepted/request artifacts and all 22 subjects.
3. Rebuild all ordinary authority chains with the one-line catalog hash repair.
   Compare each pre-gate catalog identity to R5's sealed diagnostic identities.
   Preserve SNDK's existing typed limitation and all source rights.
4. Freeze all eight A requests, source identities, quality/fairness receipts,
   inherited outputs and exact implementation/validation before dispatch.
5. Execute A8, validate/freeze all 22 subjects, then construct/freeze B8 from the
   newly accepted A outputs. Stop on first failure, with no retry or repair.
6. Render 24 messages locally only after B22 succeeds; seal before comparison.

R5 owns ten inherited calls (Market2/Core8). R6 permits at most sixteen new calls
(A8/B8). Both consume the same sealed source run. The ledgers keep these stage
generations explicit; old A/B candidates are never inputs.

The offline proof is not inference. There was no complete R5 A request to compare
against; content continuity is proven at the exact pre-gate catalog, source
inputs and inherited claims, with every existing builder/policy unchanged except
the catalog assignment. Partial results do not open the comparison gate.

Independent-assessment content is never read in this task. Source acquisition,
Telegram, DB/notification/scheduler writes, main merge, push and deploy remain
outside this continuation's authorization.
