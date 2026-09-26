# Complete Stock Owner Binding

## Pre-Implementation Contract Audit

Instruction base: R1 `2eb9ad9a`; instruction-first commit `c12b51dd`.
This audit precedes assembly. The existing source-only stock surface is
`scripts/m12ds_r4_r1_project_source.py:STOCK_FIELDS`, not a new simplified schema.
The source dictionary itself has no monolithic Pydantic input model. Its real
typed consumers are `DecisionEvidencePacket`, `OwnedEvidencePacket`,
`PacketOwnedTechnicalContext`, and the source-authority/earnings-lineage gate.
Do not confuse model-output required fields with source-input requirements.

| Stock Path | Requirement / Consumer | Owner / Absence / Binding |
|---|---|---|
| ticker | mandatory, all | same-subject local identity and four receipt entries |
| company_name | mandatory local seed, all | watchlist/company; no ticker-name substitution |
| thesis_version, thesis.core_thesis | mandatory, Core/A/B | exact active local thesis version; not observed business |
| thesis.time_horizon | optional, Core | existing builder default; preserve source null |
| thesis.thesis_drivers, validation_metrics, strengthen_signals, weaken_signals, invalidation_signals, market_expectations, valuation_framework, macro_exposures | optional configured context, Core/A/B | exact local definitions; never current observations |
| industry, sector, business_model, revenue_sources | optional, routing/Core | local company metadata; missing stays missing |
| company_profile | optional, routing | no undeclared provenance-file lookup; omit absent |
| knowledge_routing, chart_knowledge_routing | conditional, interpretation | existing pure routing owners; no hidden profile lookup |
| evidence | optional event union, Core/A/B | absent events allowed only when eligible observed financial union is nonempty |
| valuation | conditional, Core/A/B | reported metrics require selected Class-C current-formal/PIT/taint lineage; multiples/estimates unavailable without qualified owner |
| price_and_positioning.price.current_price | mandatory in this complete stock plan, timing/B/render context | sealed adjusted_daily last close; numeric registry and receipt required |
| price_and_positioning.supply | optional, timing | no volume-to-investor-flow inference |
| chart_context | optional components, timing/B/render context | real chart owner, per-consumer dependency scope; explicit availability |
| fact_catalog | mandatory, all | existing pure fact builder; exact source graph per retained fact |
| numeric_registry | mandatory for catalog numeric fields | existing build_numeric_registry; exact recomputation, no invented semantic |
| current_price_context | conditional, timing/B/render context | existing selector; unavailable zones/RR are typed unavailable, not zero |
| technical_context | optional as a whole, conditional if supplied | existing typed contract accepts PARTIAL_SAFE; usable facts must have exact feature/source lineage |
| technical_context.features.{D,W,M}.facts.* | individually optional | actual feature dependencies; blocked features remain blocked_features and data cautions |
| data_cautions | required when components unavailable | source-owned reason, never a negative investment verdict |
| cash_flow_user_visible, working_capital_user_visible | optional, Core | omit absent selected canonical consumption projection; no recomputation or substitution |

Core requires a nonempty observed-business union, not any specific technical
feature. `build_owned_evidence_packet` separates price/technical evidence from
Core; Pass A expressly excludes technical/current-price references. Pass B's
entry catalog supports unavailable tactical bands. Renderer-facing context
supports unavailable support/resistance/RR. No existing rule makes RSI, EMA,
MACD, ATR, ADX, DMI, OBV, full-history range or V3 long-cycle mandatory.

Financial values exposed in an earnings row must ALL pass
`m12dk_current_source_authority.earnings_lineage_receipt`. A configured thesis,
data caution, or price feature cannot satisfy the observed-business union.
The source-only allowlist excludes previous/deterministic assessments,
monitoring state, model claims and rendered prose. These are rejected inputs,
not silently copied or repaired.

## Boundary

Pure assembly receives explicit source rows/receipts, run identity, accepted
local/Class-C projections, and expected input hashes. It never locates operating
storage. Capture and proof are separate, read-only/offline orchestration.
No production wiring, provider/model calls, rendering or deployment is added.
The final packet hash is non-null only after existing downstream gates pass.
An assembled diagnostic candidate is not a qualified complete packet.

## Local R2 Result

The pure owner and exact packet/typed evidence/numeric graph checks are implemented.
All 88 sealed roles remain inputs. The first all-subject diagnostic produces two
complete packets (005930, 047810), not 22. The final immutable report records the
exact-SHA replay and regression results. No live/model readiness follows from a
successful synthetic fixture or an assembled diagnostic packet.

Remaining paths are source-owned financial/business inputs, not CPNG OHLC:

- US14: `project_reported_financial` selects no qualified direct metric from the
  supplied persisted SEC rows. No alternate observed event union was supplied.
  A configured thesis is not substituted. Exact filing/occurrence projection
  must be supplied by its accepted owner before the business union can qualify.
- 000660: existing earnings quality denies critical snapshot outliers.
- 003690: selected revenue and operating income come from different filing IDs;
  the owner does not fabricate one earnings envelope source tuple.
- 005490, 010120, 012450, 086280: existing earnings lineage rejects the selected
  financial statement-basis contract. Class-C value presence is not final gate PASS.
- 005930 and 047810 satisfy the same unchanged gates on supplied evidence.

CPNG's 170 safe typed features and existing bounded legacy structure remain;
optional full-history/recursive components stay unavailable. Its mandatory
current price is safe. Its whole-stock blocker is the empty observed business
union, not a mandatory historical technical feature. No CPNG policy waiver is
requested. V3 full-history output is not substituted for unavailable components.

The assembler consumes serialized technical context through the existing typed
loader: a string-valued feature does not gain numeric-prose permission from an
in-memory Decimal producer instance. Catalog numeric fields retain the existing
numeric registry, while technical refs retain their actual typed permission.

Outcome C: `M12DS_R6_R5F_R2B0_R2_COMPLETE_STOCK_OWNER_GAP_REMAINS`.
Network-free full adapter prequalification is NOT_REACHED; R2B is not generated.
The immutable report contains the final hashes and exact missing field matrix.
