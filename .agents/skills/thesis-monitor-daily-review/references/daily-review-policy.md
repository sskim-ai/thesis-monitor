# Daily Review Policy

## Role Split

The backend decides facts, calculations, identity, materiality, freshness, event consumption, and deterministic status. The model interprets only the verified packet.

Never recalculate missing values, infer an ADR ratio, annualize a quarter, reverse an EPS from a multiple, or promote stale data. Unknown remains unknown.

## Analytical Order

For each stock, review:

1. Newly verified facts.
2. Their connection to the current thesis version.
3. Business-value materiality.
4. Earnings-estimate implications.
5. Meaning relative to market expectations.
6. Valuation implications.
7. Structural-risk changes.
8. Holder meaning.
9. New-observer meaning.
10. The next measurable check.

## Core Distinctions

- Fact is not interpretation; interpretation is not certainty.
- Initial baseline is not daily delta.
- Business thesis, valuation, and price or positioning are separate layers.
- Supply alone cannot change the thesis.
- A good company is not automatically a good stock or a good entry price.
- A modeled estimate is not market consensus.
- Historical valuation is usable only when price, share, and accounting bases are verified.
- Raw parser and provider metadata never belongs in user-facing language.

## Synthesis Standard

Do more than paraphrase the deterministic status. Combine compatible facts, identify noise, test the facts against thesis drivers and invalidation conditions, and state what remains unknown. Keep each stock focused on one to three decisive ideas.

For each stock, select at least one company-specific investment question. Connect a canonical fact to
another fact or verified basis, explain the relationship, identify the expectation embedded in the
current price or valuation, and name the next supplied fact that would change the judgment. Do not
create surface variety by replacing words in a shared template.

When two relevant valuation facts exist, interpret their direction together. A modeled forward
multiple above trailing can indicate a weaker modeled earnings denominator; a modeled forward
multiple below trailing can indicate earnings expansion assumptions that may coexist with cycle-peak
risk. These are qualitative relationships between backend values, not permission to calculate an
unstated spread or call an internal model market consensus. Apply the routed industry framework:
memory requires cycle, mix, utilization, inventory, capex, and FCF discipline; biotech requires
clinical/regulatory milestones, runway, dilution, and partnerships; foundry requires process mix,
utilization, capex, customer demand, and issuer-currency discipline; auto/platform requires growth,
margin, cash flow, and segment execution; power-intensive compute requires power economics,
utilization, expansion capital, and cash conversion.

New-observer and holder views answer different questions. The new observer needs a verified entry
condition, price asymmetry, retest, or missing business fact before committing new capital. The holder
needs the current chart review boundary and the separate fundamental deterioration that would force
thesis reassessment. Never repeat the same normalized sentence for both views, and never turn either
view into a buy or sell instruction.

Numeric placeholders are full phrases, not value-only slots. The deterministic binder owns the
canonical semantic label, source identity, instrument identity, and formatted value. Draft
`{{numeric:pe}}보다 {{numeric:fpe}}가 높습니다`, never `현재 PER {{numeric:pe}}보다 선행 PER
{{numeric:fpe}}가 높습니다`. Draft `{{numeric:kospi_return}}와
{{numeric:kosdaq_return}}가 반대 방향입니다`, never preface either placeholder with a manually
written futures product or return label. Context such as `TWD 기준인 {{numeric:revenue}}` is allowed
when it does not duplicate the registry label. A redundant authored label, unknown forward source,
unknown market instrument, or source/instrument label mismatch is a hard failure; remove or correct
the reference rather than rewriting the bound prose after validation.

Hard deterministic warnings remain visible in the comparison record even when the AI view differs. Shadow output never mutates official state or Telegram.

## Full Knowledge Requirement

The compact policy is not the complete investment framework. Use `knowledge-index.md` to read the relevant sections of the full runtime mirror for every packet. Apply the selected industry framework to the decision, not merely to an audit list. Record stable semantic framework names in `frameworks_used`.

## Evidence And Numbers

Use canonical `fact_catalog` objects only. Link every interpretation to `fact_ids`. Contract profitability, customer mix, FCF, inventory, ROIC, ADR conversion, and other absent facts stay Unknown.

Every investment-related number starts as a draft `{{numeric:ref_id}}` placeholder plus `numeric_fact_refs` containing only `ref_id`, `fact_id`, `field_path`, exact prose `text_ref`, and optional lower/upper role. The backend binds the canonical value, unit, semantic, source-aware label, approved formatter, user text, and final `numeric_claims`; the model does not transcribe the same number twice. A generated claim covers only its exact prose occurrence, and a number found elsewhere in the packet or another prose field is not interchangeable with the referenced semantic field.

Numeric grounding is fail-closed during the pilot. When a market or stock has at least four registered, prose-allowed numeric anchors, an output with zero numeric claims is rejected. This is not a quota for sparse packets: unavailable or unsafe numbers remain Unknown. When numbers are used, connect value to comparison, meaning, and the investment question instead of listing metrics without interpretation.

## Dual Knowledge and Chart Boundary

Investment Knowledge v3 remains the safety, company, earnings, valuation, expectation, and monitoring authority. Chart Knowledge v1 is a separate OHLCV interpretation reference. Backend-validated facts rank first, then Investment Knowledge safety, OHLCV Analyst outputs, Chart Knowledge interpretation, and finally examples.

Do not compute technical indicators in the review task. Missing support, resistance, ATR, Elliott, Fibonacci, risk/reward, or state-machine output remains unavailable. Adjusted technical prices and unadjusted historical-valuation prices are separate bases.

Output schema 4 integrates deterministic facts and AI reasoning by section. The draft-only numeric-reference envelope is removed before schema validation, so the validated external shape remains schema 4. Do not append the full deterministic report after the AI narrative. Keep deterministic official status and hard warnings, use numeric evidence when eligible, and place holder and new-observer views inside price positioning.

## Market Intelligence

Market analysis follows `verified fact -> market structure -> economic transmission -> monitored portfolio relevance -> next confirmation`. Prefer the backend-selected `key_change_fact_ids`, use two to four decisive changes at most, and distinguish index direction from breadth, sector concentration, market flow, discount-rate, FX, and commodity channels. An unavailable breadth or market-flow field stays Unknown and prevents a broad-market conclusion.

Use only packet `transmission_candidates` for `portfolio_transmission`, with the exact verified `portfolio_group` and supporting market fact. Market context can be a tailwind, headwind, or neutral condition; it never changes the company thesis without company-level evidence. Keep collection timing, immutable-session notes, policy identity, and other operating metadata in audit artifacts rather than Telegram prose.

Numeric prose is allowlisted. Use only registry entries with `registered=true` and `prose_allowed=true`, match an approved label for that exact semantic, and use an approved display variant. Unknown semantics, audit-only denominators, and fields with unverified currency or unit stay out of narrative prose.

Use structured company identity for the primary industry framework. Thesis themes, macro exposure, customer CAPEX, and secondary segments may add only routed secondary frameworks; they never replace a high-confidence primary framework. When structured identity remains ambiguous, use the general framework instead of forcing a specialized industry classification.

Company-profile provenance is backend identity evidence, not an invitation to infer classifications. A verified profile may drive a specialized framework. A partial profile reduces confidence, and an ambiguous or unavailable profile stays general unless the packet contains stronger structured identity.

## Claim Fence

Each worker owns a UUID claim and a claim-specific temporary output. The validator may accept an expired claim only while it remains the active claim. Once another worker reclaims the packet, the older claim can never finalize.

## Runtime Operational Context

The US evaluation starts at 08:05 KST together with the first KRX night-futures fetch. The backend retries only night futures at 08:10, 08:15, and 08:20, then finalizes with both fresh contracts, one fresh contract plus a caution, or no fresh contract plus a compact caution. The US primary starts at 08:15 and may poll backend packet readiness for up to five minutes; it never fetches KRX data itself. Night futures are Korean opening-price context, not a direct business-thesis signal. The Korean close run uses the successful 16:05 KST monitoring result. Korean close FX and supply values in the packet are the backend source of truth; do not refresh, recompute, or substitute them. Supply fields such as `price.supply.score`, quality, signal, and as-of date retain their packet semantics. Provider retries, market-session freshness, monitor schedules, and Action routing remain backend policy and must not be inferred from the investment Knowledge reference.
