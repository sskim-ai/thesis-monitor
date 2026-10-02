# Independent Market Views

REV24 separates display authorization from the existing directional consumer.
It does not change source acquisition, Core/A/B policy, source registry semantics,
production scheduling, delivery, or the Market model prompt/schema.

`MarketDirectionalModelView` receipts hash the existing exact context and schema.
`MarketUserDisplayView` binds to the authenticated sealed packet, authority graph,
generation, source hash and original publication occurrences. Both have separate
hashes. The display view is a sibling of the context, never included in it.

## Published Levels

The current generation must have queried the provider. Query instants are compared
as aware datetimes, so UTC `Z` and `+00:00` have identical semantics. Latest verified
publication, exact response hash, provider identity, source date and numeric registry
binding are required. Only the published level field is granted display permission;
prior/change/return fields are not granted by the publication display owner.
Every published display line retains the original observation date.

REFERENCE_LAGGING and today_signal_eligible=false remain directional denials.
They are not blanket display denials. Source-unavailable, renderer-only and hard
quality denials continue to prohibit display.

## KR Index Identity

Existing `numeric_alias_audit` is the source of identity evidence. Both close and
return must bind the current eligible native alias to the same canonical index,
session, exact value, unit and semantic type. Duplicate bindings, missing fields,
other-index substitution and source drift fail closed.

The canonical registry's generic index-return prose label requires series_code,
whereas native KR canonical indices use symbol. A validated typed alias supplies
the deterministic index label, only for the bound fields. The registry itself,
its generic prose permission and model directional permissions remain unchanged.
This exception cannot override registered quality denials or numeric mismatch.

## Consumers

- The sealed adapter creates both views after existing authority and numeric checks.
- Mandatory coverage reads the display view. US display roles use US_MACRO,
  including the already-required broad dollar index. KR requires both bound indices
  and the separately qualified ECOS FX level (or existing typed unavailable policy).
- The final display plan embeds its typed view and rebuilds it against the exact
  source at render time. Accepted-result hashes bind the resulting plan.
- Existing official-night numeric ownership is unchanged; missing D/W/M and sectors
  stay explicitly unavailable and do not block otherwise complete mandatory roles.
- Market projection and both view hashes are reproduced twice before model admission.

The central whole-source code registry now also owns display eligibility,
materialization, projection, qualification and final capture. Its legacy profile
is unchanged. No alternate path inventory is introduced.

## Proof

`scripts/r9_rev24_display_proof.py` accepts a sealed historical regression fixture.
It compares exact directional context/schema/packet to the old projection, runs
the real request materializer without invoking a model, and passes synthetic
accepted output through the deterministic renderer and disabled sender boundary.
Historical input is not reusable as current live data. Live qualification must
start a new full-fresh generation after offline and archive-backed GC gates.
