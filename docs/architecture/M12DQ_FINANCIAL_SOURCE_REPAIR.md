# M12DQ Financial Source Repair

Contract: `m12dq-financial-source-projection-lineage-repair-v1`.
Local candidate only. No authority-policy, production, delivery or scheduler change.

## SEC Projection

The existing revenue allowlist is unchanged. Previously, the first concept with
any inventory suppressed the second concept even when only the second contained
the requested period. Business-field aliases are now collected and selected per
exact fiscal label, filing date and actual end date. Conflicting equal-duration
amounts fail closed, as do invalid monetary units and nonfinite/boolean amounts.

`us-gaap:OperatingIncomeLoss` projects to the existing `operating_income` field.
Its official definition is operating revenues less operating expenses. The
reviewed GOOGL/HUT/WULF inventories contain exact USD duration occurrences.
No IFRS operating-income alias, including-tax revenue alias, keyword inference,
or issuer-specific exception was added. Negative operating income remains signed.
Margin requires matching start/end/unit/accession for its two components.

Every selected occurrence retains concept, taxonomy, source filing, form, filing
date, CIK, actual duration, amount, source ordinal, occurrence hash and payload
hash in existing `raw_financial_fields`. The snapshot upsert identity includes
actual period end so comparative columns cannot overwrite current-period rows.
No fallback policy or period relabeling was introduced.

## OpenDART Backfill

The existing backfill caller now supplies the exact list-row receipt and consumes
the actual `(facts, unknowns, financial_lineage)` provider return. Missing receipt
or invalid filing date is skipped without fabricating metadata. A legacy two-item
return raises rather than silently losing lineage.

Formal event metadata and full field-level lineage reach the existing snapshot
materializer. Provider unknowns are retained in the event, result warnings and a
non-canonical source-audit record in `raw_financial_fields`. Normal financial
validation is run with the unchanged configured margin threshold before upsert.
Existing receipt-keyed history and formal/preliminary source selection are reused.

## Gates

M12DK source authority and M12DO dual raw/emitted B binding are unchanged.
The whole-cohort gate is reused, including its all-exposed-fields quality rule.
No contextual definition, condition, market fact or valuation is promoted to
business direction. No field is hidden to clear a quality failure.

SKHY issuer-level reuse is conditional on independently usable underlying-issuer
facts. The fresh underlying source remains tainted, so no cross-listing adapter,
EPS, price, multiple, ratio, range or business-fact transfer was exercised.

## Proof Boundary

The whole-cohort collection was frozen at `d9907928dd659325fcec074f727e2005871acd79`.
Additional malformed-unit/conflict negative controls were hardened offline after
collection; the frozen source files were not rewritten. Source audit and coverage
receipts distinguish collection SHA from final local SHA. No Core/A/B request was
constructed or sent after the failed source gate.

See [M12DQ closeout](../reports/20260921-m12dq-source-repair-closeout.md).
