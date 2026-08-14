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

4. Fill the schema-4 reasoning sections. Each section must contain concise `text` and supporting `fact_ids`. Market `portfolio_transmission` also requires an exact backend `portfolio_group`, and each item must cite a fact allowed for that group. `next_checks` must cite the next available backend market fact that could change the interpretation; a generic or fact-free check is invalid. Keep no more than four important changes, four relevant portfolio groups, three next checks, and three material cautions. Keep operational method notes and session provenance in the audit packet, not in user-facing market prose. Every investment-related number in prose must also have a `numeric_claims` entry that exactly identifies its `fact_id`, `field_path`, backend `value`, `unit`, `semantic_type`, exact prose `text_ref`, and rendered `usage`. Use a number only when its registry entry has `registered=true`, `prose_allowed=true`, and a compatible market/stock scope. Use one of its approved semantic labels and display variants. Copy the registry's raw value even when the prose uses an approved compact or rounded display. Do not calculate a new value.

5. When safe anchors are available, use 2-4 decisive numbers in `core_judgment`, at least two earnings anchors in `business_earnings`, current price plus a relevant stored rule or provided chart indicator in `price_positioning`, at least two available horizons in `supply_analysis`, and at least two relevant multiples or relative metrics in `valuation_analysis`. This is a validation boundary, not optional style: when a market or stock has at least four registered, prose-allowed numeric anchors, submitting zero numeric claims is a hard failure. Fresh required night-futures facts each require an exact market numeric claim. Missing data never authorizes invention. Explain why missing OCF, capex, FCF, inventory, or ROIC would change the judgment instead of merely saying that cash generation needs checking.

6. Write one complete JSON document to the returned claim-specific `temp_output_path`. Set `claim_id` from the claim response and copy both Knowledge versions and checksums. Do not write outside `data/ai_review`.

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
- Treat 1-day supply as current momentum, 5-day supply as short-term positioning, and 20-day supply as medium-term positioning. Explain horizon divergence without changing the fundamental status from flows alone.
- Chart state enums and risk/reward references are analytical context, not buy or sell commands. Chart Knowledge fair-value formulas never override backend valuation or Investment Knowledge v3 safety.
- Chart `INVALID` means the price scenario needs review; it never changes deterministic thesis invalidation. `HOLD` is holder context, not a new-entry signal, and `TRIM` means position-management pressure rather than a sell order. Risk/reward must use the engine's nearest eligible resistance and may not be improved by selecting a farther target.
- Treat `knowledge_routing.industry_routing.primary_framework` as company identity. When routing confidence is high, include it in `frameworks_used`; use only listed secondary frameworks for thematic or segment context. Thesis wording must not replace the primary industry framework.
- Use `company_profile` provenance and quality as an identity guardrail. `partial` or `ambiguous` profile data may reduce routing confidence; never infer a missing classification from the ticker, company name, or thesis theme.
- Resolve every `numeric_claims[].text_ref` to the exact prose field containing `usage`. One claim cannot cover the same number in another prose field, and a fact with the same numeric value cannot support a different semantic meaning.
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
