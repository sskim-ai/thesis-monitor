# SEC Logical Cell Reference Ownership

`sec-logical-cell-reference-v1` is a structural contract, not a source-purpose
or investment authority. It inventories every anchor and intervening meaningful
text/content boundary in exact source order before target selection.

Multiple anchors join only inside one exact tr/td, with the same canonical href
and document identity, in a contiguous block. External/non-reference anchors,
other targets, plain text, non-layout content, row/cell boundaries and parser
ambiguity prevent joining. Malformed cells cannot authorize exclusion.

Each typed group retains accession, form, primary source/hash, row/cell IDs,
anchor IDs, DOM order, UTF-8 byte spans, exact HTML/hash and raw decoded text.
Ordered raw texts concatenate without invented spaces; existing NFKC policy
and whitespace collapse then normalize the label. This preserves source splits
inside words and numbers. Group and normalized-label hashes are reproducible.

The filing-purpose router consumes these labels only after structure validation.
Independent groups never merge across cells. Every group must independently
authorize the same compatible non-financial route; conflicts stay candidates.
Governance instruments and explicit Land Lease with a counterparty can route as
non-financial. Financial statements, lease liabilities, right-of-use assets and
accounting schedules/policies veto those routes. No filename-only exclusion.

The existing financial attachment limit is unchanged. An 8-anchor financial
statement label uses the same structural contract and remains a financial
candidate. No issuer-specific routing is introduced.

The slot plan includes the complete logical-cell inventory and per-document
groups, ambiguity/route denial, source spans and hashes. Report tooling exports
`logical-cell-reference-inventory.json` without creating a parallel truth store.
Production deployment, delivery and model decision contracts are unchanged.

## JSON-Native Persistence

`sec-reference-target-v1` names `canonical_href` and `document_identity` in a
strict `ReferenceTarget`. The inventory boundary explicitly dumps this target
with JSON mode. Anonymous tuple/list targets are rejected. Group membership may
remain immutable internally; its existing JSON-mode dump remains unchanged.

The inventory and public slot-plan constructors recursively reject runtime-only
types before hashing or persistence. They do not coerce values. Both durable
write/read equality and independent plan recomputation must match exactly.
The production projection equality guard is unchanged, including tamper checks.

Regression coverage includes collector -> disk -> reload -> projection, not
only the in-memory collector return. Real TSM/WRD archived-source parity is
recorded separately as historical offline evidence, never current qualification.
