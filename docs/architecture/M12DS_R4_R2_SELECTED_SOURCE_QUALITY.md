# Selected-Source Quality Ownership

Contract: `m12ds-r4-r2-selected-source-quality-ownership-v1`.

The source closure resolves the frozen packet's earnings projection to exactly one
database row using ticker, provider, period, filing date, scope, fiscal role and
snapshot type. SEC amount/currency and any packet document claims must match.
Ambiguous projections are denied, never resolved by amount magnitude or provider
precedence. Issuer and official foreign-filing document bindings are checked.

The audit binds the exact selected document and immutable snapshot content,
including raw field records, units/basis, field errors and occurrence identities
where the upstream owner supplies them. Unknown metadata remains unknown. Every
alternate provider/period row retains its own errors in the audit. Financial
derivation bundles bind the same selected identity and revalidate it on consumption.

Same-provider comparisons reuse the existing SEC field-quality owner. Currency,
period role, statement basis, unit scale and issuer must be compatible. That owner
also checks duration, exact occurrence, same filing and payload. Cross-provider
comparisons have no new equivalence or FX permission. The foreign release parser's
legacy absolute-only rows do not carry an approved exact comparative-lineage owner;
they cannot be promoted to directional comparisons by this repair.

The old ticker-wide `narrowed_sec` denial is removed. Denials now remove only the
selected fact's directional ref. Independent comparative or issuer-projection refs
are preserved. A clean selected foreign-filing amount without an eligible comparison
has `SOURCE_COMPARISON_UNAVAILABLE`, not an inherited historical source conflict.
Other already-accepted R3 source families retain their existing policy; this task
does not redefine their economic interpretation or grant new annual/FY comparisons.

## Proof Boundaries

- Renamed synthetic controls cover provider, period, issuer, document, currency,
  duration, basis, field taint and frozen-input switches.
- Prior frozen all-subject replay is diagnostic only, not a new current input.
- Source-ownership PASS and whole-cohort directional readiness are separate gates.
- Code is frozen before a new all-subject live source collection.
- Any incomplete cohort stops Market/Core/A/B before the first model call.
- R3 prompt/schema/decision policy and the R4-R1 night/capture owners are unchanged.
- Main merge, push, deploy and all production mutations remain forbidden.
