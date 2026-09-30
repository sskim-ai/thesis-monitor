# Provider Valuation Calibration Context

REV29 adds an opt-in shadow acquisition and Pass B context adapter. Production
configuration, delivery, schedulers and persistence are unchanged.

`r9_rev11_live --provider-native-valuation` freezes exact-security optional
Kiwoom ka10099/ka10001 and Finnhub profile2/metric slots in the existing sealed
dispatcher. An archived listing can select a request market only; it cannot
qualify current identity or supply a current multiple. Current list/profile
responses and all numeric responses require this generation's bound receipts.

The existing REV28 native snapshot owner qualifies each atomic multiple. The
adapter does not recompute PER/PBR from a current price, invent a metric date,
convert ADR share units or enable fPER. Source-derived qualification remains
separate. Optional valuation failures produce explicit unavailable states, not
invented zeroes or a whole-stock failure; receipt tampering still fails closed.

`provider-valuation-calibration-context-v1` binds the three metric states to the
exact current valuation view, generation and security. Qualified snapshot refs
are available only through `holder_valuation_refs` and `new_buyer_valuation_refs`.
Existing directional, holder-risk, business-support and discount capabilities
are unchanged. A native multiple alone cannot grant an ATTRACTIVE decision or
determine an entry range. Numeric display belongs to the existing detailed
valuation renderer with the provider-latest-snapshot qualifier.

Core and A capture reject valuation blocks/refs. Pass B capture requires the
exact reconstructed valuation context; the post-model validator rejects native
refs in other fields or Overall multiple-based rationale. The whole source
graph and derived B contexts must reproduce exactly in two offline replays.

The live proof remains conditional on full offline tests, archive-backed GC,
12 GiB free before collection, 10 GiB before models, all mandatory source gates,
and a sealed source-only archive before any model call. No prior current values
or prior model judgments are reused. Completion requires all 24 disabled-delivery
sender-boundary captures; partial results must retain their actual stop gate.
