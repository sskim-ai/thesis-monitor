# Sealed Market Consumer Projection

R2B-R5 adds audit-only scripts. Production imports, policy, validators, source
acquisition, persistence, delivery and scheduler configuration remain unchanged.

`project_sealed_market_context` verifies the whole-source run seed, authority
graph, acquisition attempt, Class-C versions and optional denial set before
building the native Market adapter, fact catalog and numeric registry. It uses
the sealed cutoff, not the execution wall clock. Original source objects remain
unchanged. Published observation dates are retained, not relabelled as the query
date. US observations without returns cannot support directional market claims.

Only existing native semantic owners construct facts. Native KR aliases bind
back to canonical registry fields. The optional breakeven previous-level scalar
has no existing numeric registration: it is retained in an explicit denial
receipt, but withheld from the model projection. Any other unregistered scalar
fails closed. No new numeric semantic type or investment threshold is created.

The current R4 Market consumer and renderer own the accepted field set. Sparse
eligible facts may yield DATA_INSUFFICIENT; optional gaps are never zero. Raw
provider rows are not supplied to the model. The complete sealed source remains
the provenance owner, including inputs to native deterministic derivations.

Execution is separate from offline projection. Whole-cohort readiness, neutral
V2 fairness, source identity, clean code and validation are required before a
binding is issued. Market/Core request bytes are frozen at that point. A/B
requests necessarily depend on newly validated upstream outputs: their builder,
schema, validator, source inputs and code are frozen first, and their exact
request bytes are frozen before each stage. Offline availability probes are
never used as generated candidates.

The accepted UNKNOWN_LIMIT contract is composed in a separate `limits` object
within each affected batch. Ordinary subject schemas are unchanged. This keeps
all 22 subjects represented without inventing a fundamental claim for the
limited subject. The limit uses the existing typed validator and renderer.

The official signed-in Sol/xhigh transport is reused with read-only child
isolation, immutable prompt/schema inputs, tool-event checks and host-context
parity. Maximum calls: Market 2, Core 8, A 8, B 8. Timeout 1200 seconds; retries,
repair, fallback and judge calls are zero. A failure stops all subsequent work.
This contract does not claim a stronger runtime isolation guarantee than the
existing official transport provides.

Only fully validated outputs may enter local production-renderer capture. No
recipient or outbound delivery is created. Independent assessment contents
remain unread until result sealing; a partial result is not comparison-ready.
