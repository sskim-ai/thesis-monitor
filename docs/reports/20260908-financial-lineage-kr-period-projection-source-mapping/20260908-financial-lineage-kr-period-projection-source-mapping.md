# M7 Financial Lineage & KR Period Projection Source Mapping

## Result

- Status: `M7_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `92e5111f35499f43dcfc4fe76238b0c3e4a2442b`
- Work-instruction commit: `6a303ebeedd275d8109e6babfcf5f725798542d1`
- Implementation commit: `9442f406b0deae433ad25f4961daa93e15695587`
- Projection contract: `canonical-financial-lineage-projection-v1`
- Existing adapter contract: `existing-canonical-financial-domain-adapter-v1`

## Projection result

The preserved Phase 9 archive contains 606 canonical cash-flow
facts across 12 US/foreign issuers. M7 projects the
existing formula, derivation version, ordered input refs, period/basis identity and source
occurrence lineage without creating a new financial fact. All 606
facts now produce typed context: 224
OCF, 191 PPE and
191 OCF-less-PPE. Compatible
prior-year comparison lineage is available for 164 facts.

M6 had 189 derived-period lineage denials and 87 FCF input-lineage denials. Both are 0 after
projection, with new derivations and source taxonomy mappings remaining 0.

## KR boundary

The OpenDART mapper now accepts only a unique XBRL duration occurrence matching taxonomy,
amount, KRW unit, statement basis and entity identifier. It preserves the XBRL start/end and
does not assume January 1 or calendar quarters. Non-calendar synthetic contract fixtures pass.
The repository has no real KR canonical cash-flow facts, so real issuer support remains
`SOURCE_PRESENT_BUT_PERIOD_BLOCKED`: OCF 0 resolved / 7
blocked, PPE 0 resolved / 6 blocked. Synthetic mapper
capability is not counted as market coverage.

## Safety and validation

- Compact AI context changes: `0 / 5`
- Support-only evidence leaks: `0`
- Directional and Price-Timing prompt changes: `0`
- Source-sufficiency and Daily Delta semantic changes: `0`
- New SEC/OpenDART taxonomy or ticker-specific mappings: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `252 passed`
- Full repository tests: `2920 passed` (`2` existing deprecation warnings)
- Ruff and `git diff --check`: `PASS`

## Next scope

`SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION`

Classify HUT PPE, SKHY foreign-issuer cash flow and KR canonical promotion as generic source
classes. If a gap is truly issuer-specific, defer it rather than add a ticker exception.
Debt/liquidity, working capital and non-operating effects remain separate higher-risk packages.
Directional specificity remains inactive and monitoring remains paused.
