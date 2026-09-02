# Working-Capital Signed-Gap Controls

The run-52 packet already carried correct signed values and typed comparator lineage:

- `000660`: negative inventory-vs-COGS gap, `LOWER`;
- `005490`: positive inventory-vs-revenue gap, `GREATER`;
- `005930`: positive inventory-vs-COGS gap, `GREATER`.

The prior validator scanned the whole `business_earnings` section. For `000660`, a later phrase
about `높은 메모리 수익성` created a false second direction. For positive cases, `웃돌았습니다`
was absent from the canonical higher vocabulary. Invalid relations then lost numeric coverage and
appeared again as provenance errors.

The validator now isolates the one sentence containing the bound value and supports `웃돌다`.
Tests cover positive, negative, wrong direction, wrong comparator, percentage-point typing, and an
unrelated later direction word.

`SIGNED_GAP_DIRECTION_INVERTED = 0`

`SIGNED_GAP_PERCENT_VS_PP_CONFUSION = 0`

