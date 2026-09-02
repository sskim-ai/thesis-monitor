# Daily Review Semantic Binding Contract

Contract chain:

```text
canonical fact/relation
  -> typed numeric registry
  -> candidate ownership normalization
  -> numeric binding
  -> sentence-local semantic validation
  -> strict daily-review validation
```

## Working-Capital Relations

The canonical signed gap is `inventory growth - comparator growth`, measured in percentage points.
The comparator is typed as `cogs_growth` or `revenue_growth`. Negative, positive, and zero values
map to `LOWER`, `GREATER`, and `EQUAL`; the visible directional formatter displays magnitude while
the sentence owns direction.

Direction and comparator validation use only the sentence containing the bound value. Words in a
later sentence cannot invert the relation. Korean `웃돌다` and `앞서다` are supported higher
relations; `밑돌다` is a lower relation. Percent and percentage-point units remain distinct.

## Typed Valuation Scope

Explicit company, listed-security, segment, and component scopes remain strict. A
`quality_unknown` reference whose canonical quality fact has no valuation scope is normalized to
`unknown`; it is not promoted to `listed_security`. Explicit scope mismatches remain validator
errors.

## Holder Variables

The holder contract supports business variables relevant to the routed industry. For
insurance/reinsurance, combined ratio, loss ratio, catastrophe loss, underwriting, and fundamental
damage are supported holder variables. This extends the generic business-variable vocabulary and
does not create ticker exceptions.

## Structured Market Labels

For canonical market breadth numerics, the binder owns `상승 종목 비율` and its exact number.
When AI prose writes the same approved label immediately before a placeholder, the ownership
normalizer removes only that label and leaves market/instrument context intact. Numeric facts are
not removed or hidden.

