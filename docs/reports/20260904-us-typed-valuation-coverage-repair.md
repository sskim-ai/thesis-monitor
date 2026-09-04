# 2026-09-04 Typed Valuation Coverage Repair

The 16 valuation-family errors decomposed into 14 schema/metric ownership mismatches, one MU phrase false positive, and one SKHY correction-context defect.

For an absolute interpretation with exactly one bound valuation semantic, the validator now canonicalizes the authored metric only within the same family: trailing/forward PE remain earnings-family, while PBR/forward PBR remain book-family. It records the original `authored_metric`. Cross-family normalization is rejected.

Standalone `피크 이익` no longer triggers a valuation-multiple occurrence. Actual multiple language such as `피크 이익 배수` remains covered. Listed-security scope now includes canonical security identity/basis facts, and a generic missing-basis sentence is normalized to a grounded security-basis Unknown rather than accepted as free prose.

| Gate | Result |
|---|---|
| Typed valuation incident errors repaired | `16/16` |
| PE/PBR family crossover allowed | `0` |
| Provider denominator reverse-engineering | `0` |
| ADR/security-basis safety | `PASS` |
