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

Hard deterministic warnings remain visible in the comparison record even when the AI view differs. Shadow output never mutates official state or Telegram.

## Full Knowledge Requirement

The compact policy is not the complete investment framework. Use `knowledge-index.md` to read the relevant sections of the full runtime mirror for every packet. Apply the selected industry framework to the decision, not merely to an audit list. Record stable semantic framework names in `frameworks_used`.

## Evidence And Numbers

Use canonical `fact_catalog` objects only. Link every interpretation to `fact_ids`. Contract profitability, customer mix, FCF, inventory, ROIC, ADR conversion, and other absent facts stay Unknown.

Every investment-related number in prose requires a `numeric_claims` record tied to the exact `fact_id` and `field_path`. Preserve the backend value and unit; display-only KRW compaction and approved percentage rounding are allowed. A number found elsewhere in the packet is not interchangeable with the claimed semantic field.

## Claim Fence

Each worker owns a UUID claim and a claim-specific temporary output. The validator may accept an expired claim only while it remains the active claim. Once another worker reclaims the packet, the older claim can never finalize.

## Runtime Operational Context

The US evaluation remains a 07:50 KST backend operation, and its packet becomes ready only after the backend resolves the KRX morning gate. Night futures are price context, not a direct business-thesis signal. The Korean close run uses the successful 16:05 KST monitoring result. Korean close FX and supply values in the packet are the backend source of truth; do not refresh, recompute, or substitute them. Supply fields such as `price.supply.score`, quality, signal, and as-of date retain their packet semantics. Provider retries, market-session freshness, monitor schedules, and Action routing remain backend policy and must not be inferred from the investment Knowledge reference.
