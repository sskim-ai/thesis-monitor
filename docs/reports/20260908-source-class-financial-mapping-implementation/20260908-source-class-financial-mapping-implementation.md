# M8 Source-Class Financial Mapping Implementation

## Result

- Status: `M8_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `3ac2359a16c8b6e03a146ecc32676005e1589db4`
- Work-instruction commit: `86f361fb92431c8725087e082bf06b83a399480d`
- Implementation commit: `00a8663c1adbd32b487f4672fea4011d159ee945`
- Contract: `source-class-financial-mapping-v1`

## Source-class decisions

- HUT PPE: `SOURCE_EVIDENCE_INSUFFICIENT`; no ticker exception and no new alias.
- SKHY OCF/PPE: generic IFRS foreign-issuer class is already supported by TSM/WRD,
  but no SKHY financial statement occurrence is preserved; the historical gap remains closed.
- KR OpenDART: `GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT`; implemented.

The KR defect was statement-basis parsing, not period guessing. The official XBRL axis name
contains both `Consolidated` and `Separate`, while its member identifies exactly one basis.
M8 reads the recognized axis member and then requires a unique concept, amount, KRW unit,
entity, duration, statement basis and filing identity match before direct canonical promotion.

## Measured real coverage

Seven preserved real KR filings produced 14 direct canonical facts: seven OCF and
seven PPE occurrences, all YTD and all exact-context bound. Applicable coverage is OCF 7/7 and
PPE 6/6; the seventh PPE source occurrence belongs to insurance and does not activate generic
enterprise FCF. HUT and SKHY remain unresolved without unsafe broadening.

## Safety and validation

- Ticker-specific production mappings: `0`
- New SEC taxonomy mappings / OpenDART fuzzy mappings / formulas: `0 / 0 / 0`
- Compact AI, Directional prompt, Price-Timing prompt, renderer changes: `0`
- Source-sufficiency and Daily Delta semantic changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `274 passed`
- Full tests: `2929 passed` with `2` existing deprecation warnings
- Ruff and `git diff --check`: `PASS`

## Next scope

`HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_INTEREST_BEARING_DEBT_LIQUIDITY`

Debt/liquidity, working capital and non-operating effects remain separate bounded packages.
Directional specificity and production activation remain outside M8.
