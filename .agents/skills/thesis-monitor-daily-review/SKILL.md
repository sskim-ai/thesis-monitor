---
name: thesis-monitor-daily-review
description: Analyze Thesis Monitor daily review packets using only backend-verified facts, then write and validate structured shadow-review JSON. Use for scheduled US or KR daily investment review, backup catch-up runs, packet-based review validation, and backend-controlled pilot delivery.
---

# Thesis Monitor Daily Review

Invoke this workflow as `$thesis-monitor-daily-review` from each scheduled task.

Use this skill only for immutable packets under `data/ai_review/inbox`. Do not browse the web, call an external API, modify application code, or alter the database, official assessment, or Telegram delivery. In the delivery pilot, only the local validator/dispatcher may release the validated result; the Codex analyst still writes only its claim-specific JSON.

## Workflow

1. Claim one packet for the requested market:

   ```bash
   .venv/bin/python -m app.jobs.ai_review claim --market us --owner <task-name>
   ```

   Use `--market kr` for a Korean close review. The US primary task uses `--wait-seconds 300 --poll-seconds 15 --lease-minutes 10` so it can wait briefly for the 08:05-08:20 backend readiness gate while still allowing the 08:30 backup to reclaim an interrupted claim. Other workers use the default lease unless their scheduled prompt says otherwise. If the result is `no_pending_packet`, stop without modifying anything.

2. Read the returned `packet_path`, this skill, [daily-review-policy.md](references/daily-review-policy.md), [knowledge-index.md](references/knowledge-index.md), [chart-knowledge-index.md](references/chart-knowledge-index.md), and [output-schema.json](references/output-schema.json). Follow each stock's `knowledge_routing` against [Investment Knowledge v3](references/investment-thesis-analysis-monitoring-knowledge.md). When `chart_knowledge_routing.available=true`, also follow that route against [Chart Knowledge v1](references/stock-chart-value-analysis-knowledge-v1.md). Do not replace either routed source with general model knowledge.

3. Review the market once and every stock in `stocks`. For the market, begin with `key_change_fact_ids`, connect index, sector, rates, FX, commodities, or risk facts into a supported market structure, and use only `transmission_candidates` to connect those facts to `portfolio_exposure_groups`. Breadth and market-wide flows remain Unknown when coverage says unavailable. Use only `fact_id` values from each `fact_catalog` in `facts_used`. Every `required_market_fact_ids` entry must appear in `facts_used`, in `interpretation`, and in an `important_changes` item. For a US packet, these are the fresh KOSPI200/KOSDAQ150 night-futures facts selected by the backend. Interpret their relationship as Korean opening-price context, never as company-thesis confirmation. Record the semantic framework names actually applied in `frameworks_used`. Treat absent information as unknown. Investment Knowledge v3 and backend facts take precedence over Chart Knowledge examples or valuation shortcuts.

4. Fill the schema-4 reasoning sections. Each section must contain concise `text` and supporting `fact_ids`. Market `portfolio_transmission` also requires an exact backend `portfolio_group`, and each item must cite a fact allowed for that group. `next_checks` must cite the next available backend market fact that could change the interpretation; a generic or fact-free check is invalid. Keep no more than four important changes, four relevant portfolio groups, three next checks, and three material cautions. Keep operational method notes and session provenance in the audit packet, not in user-facing market prose. For every investment-related number, put a draft-only placeholder such as `{{numeric:price_now}}` in the exact prose field and add one `numeric_fact_refs` item to that market or stock review with `ref_id`, `fact_id`, `field_path`, and `text_ref`. Optional `role` is `lower` or `upper` for zone endpoints; otherwise omit it. Keep `numeric_claims` empty for these references. The backend resolves the canonical value, unit, semantic, source-aware label, formatter, user text, and final schema-4 `numeric_claims`, then removes `numeric_fact_refs` before schema validation. Use only registry rows with `registered=true`, `prose_allowed=true`, and compatible scope. Do not type the raw number in prose or calculate a new value.

5. When safe anchors are available, use 2-4 decisive numbers in `core_judgment`, at least two earnings anchors in `business_earnings`, current price plus the active dynamic level and provided risk/reward in `price_positioning`, at least two available horizons in `supply_analysis`, and at least two relevant multiples or relative metrics in `valuation_analysis`. Use `monitoring_state.current`, `previous`, and `delta` to explain what changed since the previous final assessment. A registered price rule is primary only while its lifecycle and relevance say it is current; after a confirmation is crossed, move to hold/retest and the next verified dynamic support/resistance. This is a validation boundary, not optional style: when a market or stock has at least four registered, prose-allowed numeric anchors, submitting zero numeric claims is a hard failure. Fresh required night-futures facts each require an exact market numeric claim. Missing data never authorizes invention. Explain why missing OCF, capex, FCF, inventory, or ROIC would change the judgment instead of merely saying that cash generation needs checking.
   `Anchor` is internal analysis terminology. Do not expose `앵커` in user-facing Korean prose. Write `최근 확인된 핵심 실적`, `현재 평가 기준`, or `핵심 숫자` according to context.

6. Write one complete draft JSON document to the returned claim-specific `temp_output_path`. Set `claim_id` from the claim response and copy both Knowledge versions and checksums. Every `numeric_fact_refs[].ref_id` must be unique within its review, its placeholder must occur exactly once in its declared `text_ref`, and its `fact_id` must also be in `facts_used`. The binder converts the draft to the final schema-4 document. Do not write outside `data/ai_review`.

7. Validate and finalize it:

   ```bash
   .venv/bin/python -m app.jobs.ai_review validate --packet-id <packet-id> --claim-id <claim-id> --policy-version <analysis-policy-version>
   ```

   A nonzero result means the review was rejected. Do not weaken the validator or invent replacement facts. Correct the JSON from the same packet once, then validate again. When the five-day delivery pilot is enabled, a successful validator command invokes the backend-controlled single-delivery renderer; never send Telegram separately from the task.

## Output Rules

- Keep `schema_version`, `packet_id`, `analysis_policy_version`, `knowledge_version`, `knowledge_sha256`, `chart_knowledge_version`, `chart_knowledge_sha256`, `market`, and `assessment_date` identical to the packet, and use the active claim's `claim_id`.
- Produce exactly one stock review for every packet stock and no others.
- Separate concise facts used, interpretation, and unknowns. Do not output hidden reasoning or chain-of-thought.
- Explain why facts matter, what is noise, what expectations may already reflect, and what number or event should be checked next.
- Select no more than four decisive market changes. Distinguish index direction from breadth and sector concentration, and do not call a move broad risk-on when breadth is unavailable. Market context may be a tailwind or headwind, but it never changes a company thesis by itself.
- In market prose, state the verified market fact, its economic transmission, the relevant monitored portfolio group, and the next confirming metric. Do not repeat the deterministic market report or describe the review method.
- Keep FX levels separate from FX changes, yield levels separate from basis-point changes, and oil levels separate from oil returns. Rates, FX, and oil are generic market context unless a verified company exposure provides a transmission path. Never turn a rate increase into automatic growth-stock weakness, currency movement into automatic exporter benefit, or an oil move into a company earnings fact.
- Do not issue buy or sell orders.
- Keep the deterministic assessment as a guardrail. You may propose a different AI view in shadow, but never erase a deterministic warning.
- Never expose internal parser/provider fields. Never call a modeled estimate market or analyst consensus.
- If historical comparability is withheld, do not use a historical percentile or range.
- Apply the routed industry framework. A low peak-cycle PER alone is not a memory valuation conclusion; insurance does not use SaaS metrics; preliminary earnings do not prove FCF, inventory, ROIC, or balance-sheet changes.
- Use `chart_context` only when its quality permits. Interpret OHLCV Analyst values; never calculate RSI, MACD, Bollinger, support, resistance, ATR, Fibonacci, Elliott counts, target, stop, or risk/reward yourself.
- Treat `ohlcv-structure-v2` as the sole source for dynamic zones, boxes, Major Swings, tentative Elliott, Fibonacci, chart invalidation, risk/reward, and chart state. Local Pivot zones are not Major Swing anchors. Low-confidence Elliott and low-confidence Fibonacci are audit-only, while medium-confidence Fibonacci is context and never a sole core reason.
- Respect structure confidence and basis exactly: monthly support has no defined invalidation contract, so its invalidation and dependent risk/reward remain Unknown. Never skip a nearer monthly support to manufacture a farther daily/weekly invalidation.
- Keep stored thesis price rules separate from dynamic chart levels. A price threshold crossing is price confirmation, not an automatic business-thesis change. Once confirmation is crossed, discuss hold/retest, volume, positioning, and subsequent fundamental evidence.
- Treat `monitoring_state.current.price_structure` as the current price view and `registered_rule_state` as preserved thesis history. Never promote a crossed confirmation price to support without a verified overlapping dynamic support or retest. Prefer the nearest Strong/Medium dynamic support and resistance, and state their exact prices and current-price risk/reward when registered numeric facts permit it. If support, resistance, structural invalidation, or risk/reward is unavailable, say why and do not substitute a legacy registered support.
- Satisfy every `state_grounding_requirements.price` entry in `price_positioning`: cite its exact `fact_id` and submit numeric claims for each listed field path. For a zone, write independently grounded lower and upper prices. When `state_grounding_requirements.valuation` names `valuation:peer`, cite it and use at least two supported peer-relative numbers in `valuation_analysis`.
- Treat `monitoring_state.delta` as monitoring change, not thesis change. Price structure, supply, valuation percentile, and peer-relative valuation may move while `business_thesis_change` remains `no_material_change`.
- Treat 1-day supply as current momentum, 5-day supply as short-term positioning, and 20-day supply as medium-term positioning. Explain horizon divergence without changing the fundamental status from flows alone.
- In valuation, separate current absolute multiples, the company's own historical percentile, and verified peer medians. A historical percentile means the current multiple is above that share of comparable past observations; never describe it as that percentage overvalued. Use peer figures only when `peer_valuation.available=true` and its metric sample is sufficient. Do not call a limited active-monitoring sample an industry-wide market average.
- Chart state enums and risk/reward references are analytical context, not buy or sell commands. Chart Knowledge fair-value formulas never override backend valuation or Investment Knowledge v3 safety.
- Chart `INVALID` means the price scenario needs review; it never changes deterministic thesis invalidation. `HOLD` is holder context, not a new-entry signal, and `TRIM` means position-management pressure rather than a sell order. Risk/reward must use the engine's nearest eligible resistance and may not be improved by selecting a farther target.
- Treat `knowledge_routing.industry_routing.primary_framework` as company identity. When routing confidence is high, include it in `frameworks_used`; use only listed secondary frameworks for thematic or segment context. Thesis wording must not replace the primary industry framework.
- Use `company_profile` provenance and quality as an identity guardrail. `partial` or `ambiguous` profile data may reduce routing confidence; never infer a missing classification from the ticker, company name, or thesis theme.
- Resolve every draft `numeric_fact_refs[].text_ref` to its exact placeholder-bearing prose field. The backend-generated `numeric_claims[].text_ref` and `usage` remain fenced to that exact occurrence. One binding cannot cover the same number in another prose field, and a fact with the same numeric value cannot support a different semantic meaning.
- Numeric semantics fail closed. An unregistered semantic or an entry with `prose_allowed=false` must remain absent from prose, even when its raw value exists in the packet.
- A lease expiry only permits reclaim. Before finalization the validator fences the result against the currently active claim; never reuse another claim's temporary path.

## Runtime Boundary

Allowed writes:

- `data/ai_review/outbox/*.json.tmp`
- Files produced by the validator under `data/ai_review/outbox`, `history`, or `rejected`

Forbidden writes:

- `app/`, `tests/`, `ops/`, `.github/`, `.agents/`, `pyproject.toml`
- Database or Telegram state

The primary and backup tasks use the same workflow. Claim leases and completed-output checks provide idempotency.
