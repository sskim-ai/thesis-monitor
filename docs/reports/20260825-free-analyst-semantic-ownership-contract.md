# Free Analyst Semantic Ownership Contract

- Contract: `free-analyst-semantic-ownership-v1`
- Common path: KR and US
- Ticker hard-codes / ticker deny lists: `0 / 0`
- Flat forbidden-word solution: `0`

Every claim-bearing item records entity, ticker, market, packet, industry context, thesis-driver refs, fact refs, relation refs, expectation refs, valuation refs, Unknown refs, concept families, and expectation level.

Validation requires:

```text
support ref exists
AND support ref owner == current message owner
AND role ref belongs to the claim support graph
AND concept family is present in current-entity cited evidence
AND expectation wording matches the current expectation occurrence
```

Current bounded concept families cover memory HBM/ASP/product mix, general operating product mix, defense backlog/delivery/project margin, insurance underwriting, logistics freight, Cloud AI CAPEX, and HPC execution. The registry binds provenance; it does not prohibit words globally.

Market digests are explicitly `market_global`. Entity-specific facts and thesis refs cannot be promoted to global scope. Any ownership failure makes that message ineligible and selects its deterministic fallback; other messages remain independent.
