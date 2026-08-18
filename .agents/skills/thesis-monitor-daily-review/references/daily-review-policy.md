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

Before prose generation, use the packet's `runtime_specificity_plan` to assign a primary decision
point, supporting evidence, material Unknown, and next confirmation for each stock. This is a
portfolio planning pass, not a category quota. Shared safety methods belong in validation and audit;
repeat them in user prose only when a specific current fact would otherwise be misunderstood. A
synonym-only rewrite of the same price-rule, supply-separation, or cash-conversion checklist remains
a semantic duplicate.

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
Every zone endpoint must use its exact `lower` or `upper` reference role so the bound phrase says
하단 or 상단. A missing, duplicated, or reversed endpoint role is a hard failure; a single pivot is
not a zone endpoint and must not receive a role.

Hard deterministic warnings remain visible in the comparison record even when the AI view differs. Shadow output never mutates official state or Telegram.

Confirmation lifecycle language uses `monitoring_state.delta.confirmation_transition` and the
matching `monitoring:confirmation_transition` fact as its sole transition source. Preserve the
recorded previous state, current state, and direction in every section; do not turn a prior
`failed_breakout` into the current state when the canonical transition ends at `not_reached`.
Directional language for RR or another monitoring metric requires that metric's canonical
previous/current pair or registered delta. A current value alone supports no claim of improvement,
deterioration, rise, fall, expansion, contraction, recovery, or slowdown.

Security identity and valuation basis are separate. Use `security_identity:current` to state whether
the security itself is a verified common share or depositary security. Use `security_basis:current`
for current-security denominator, share, and currency basis. A verified ADS identity may coexist
with withheld multiples; describe the specific basis gap without calling the identity unverified.
When identity is `unknown` or `conflict`, use neutral security wording and do not assert ADR, ADS,
common stock, or ordinary-share status. A depositary ratio is verified only with value, direction,
and authoritative source provenance.

Supply routing is market-specific. KR 1-day/5-day/20-day foreign and institutional horizons are
usable only when those canonical KR facts exist. US reviews may use verified volume,
relative-volume, or explicit positioning facts, but must not import KR investor horizons or repeat a
generic missing-investor-flow sentence across the stock set.

## Full Knowledge Requirement

The compact policy is not the complete investment framework. Use `knowledge-index.md` to read the relevant sections of the full runtime mirror for every packet. Apply the selected industry framework to the decision, not merely to an audit list. Record stable semantic framework names in `frameworks_used`.

## Evidence And Numbers

Use canonical `fact_catalog` objects only. Link every interpretation to `fact_ids`. Contract profitability, customer mix, FCF, inventory, ROIC, ADR conversion, and other absent facts stay Unknown.

Every investment-related number starts as a draft `{{numeric:ref_id}}` placeholder plus `numeric_fact_refs` containing `ref_id`, `fact_id`, `field_path`, exact prose `text_ref`, the mandatory exact lower/upper role for zone endpoints, and an optional typed Korean `postposition` family (`은/는`, `이/가`, `을/를`, or `와/과`). The backend binds the canonical value, unit, semantic, period/source-aware label, endpoint role, approved formatter, typed postposition, user text, and final `numeric_claims`; the model does not transcribe the same number twice. A generated claim covers only its exact prose occurrence, and a number found elsewhere in the packet or another prose field is not interchangeable with the referenced semantic field. A raw Korean particle immediately after a placeholder is invalid.

KR investor-flow language is actor-and-horizon exact. A directional statement for foreign or institutional flow at 1, 5, or 20 days requires that exact canonical claim in the same prose occurrence; another actor or horizon cannot substitute. US stock prose uses volume, relative volume, or an explicit US positioning fact and does not use generic `수급` language without such a contract. Every displayed KR financial amount and directly attached growth or margin claim carries a field-specific amount-period and statement-basis label derived from one uniquely matched source row. `CFS` is consolidated and `OFS` is separate; `IS`/`CIS`, filing type, a plain statement title, and report end date never substitute for single-quarter/cumulative status, consolidated/separate basis, or comparison-period identity. Historical, peer, expectation, and trailing/forward valuation judgments require an occurrence-bound typed draft interpretation reference, `exact_text_span`, and matching visible comparison claims. A trailing/forward relation is usable only when the backend relation fact verifies the same price, security, share, currency, denominator, and forward-period status. PBR/BVPS interpretation must pass `valuation-coherence-v1` on period, currency, share, and security basis.

Final message UX is also fail-closed. `priority_watch` contains ongoing thesis drivers or risks; `next_checks` contains the next filing, earnings release, or other time-bound confirmation that could change the judgment. An identical bullet, an event-oriented watch item, or a watch/next pair without distinct decision information is invalid. One exact numeric fact has one primary owner section and normally appears no more than twice in one stock message; three bindings of the same `fact_id` and `field_path` are excessive repetition. KR supply prose names the actor as subject and completes the horizon, direction, quantity, and predicate. Broken parallel fragments and mismatched Korean particles are invalid, while an empty watch or next-check section is allowed when it avoids semantic duplication.

Risk/reward references are basis exact. Current-price and support-entry ratios use distinct semantics and canonical labels. A support-entry ratio is a conditional scenario at verified dynamic support and cannot describe present-price asymmetry; a basis-free risk/reward binding is invalid.

After rendering, `runtime-message-quality-v1` must pass against the final Telegram text before the AI payload can be persisted for delivery. It rejects duplicate canonical labels, unsafe price-particle forms, and internal implementation vocabulary in addition to the existing semantic checks. Its version-2 receipt binds the packet, validated output, complete rendered payload set, policy, schema, message count, check results, errors, status, and an offset-aware check time. Delivery metadata stores the SHA-256 of the complete receipt file and the rendered payload-set hash. A missing, invalid, or changed receipt is a quality-integrity rejection, not a network retry, and no receipt is regenerated. Before any AI message is sent, the complete persisted deterministic fallback remains eligible for exactly one deadline delivery. After a partial AI delivery, stop all further AI and automatic fallback delivery, record an explicit partial-integrity/manual-intervention state, and never claim that a full deterministic fallback set was delivered. Existing completed archives remain governed by their historical manifest and are never rewritten merely because they predate the receipt contract.

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
