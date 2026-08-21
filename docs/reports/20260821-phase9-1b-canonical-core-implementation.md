# Phase 9.1B Canonical Core Implementation

Contract: `working-capital-evidence-v1`. Derivation version: `working-capital-evidence-v1:canonical-core-v1`.

The Phase 9.1A exact SEC/OpenDART occurrence registry remains the sole raw source layer. Phase 9.1B adds a canonical core that consumes those `FinancialFact` objects, applies source-availability PIT filtering, selects the latest exact prior-year fiscal-quarter pair, emits deterministic delta and YoY Facts, and builds structured growth relations with six raw/derived input references.

Raw metric families are `inventory`, exact trade AR, separate broad AR, exact trade AP, and separate broad AP. Missing is never zero. Negative balances remain blocked upstream. Trade and broad semantics survive in Fact identity, scope metadata, and relation identity.

The audit snapshot is internal only. AI packets, Telegram, fallback, Public Action `0.4.5`, snapshot schema `4`, thesis state, warnings, and database storage are unchanged.
