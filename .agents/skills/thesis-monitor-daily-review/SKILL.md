---
name: thesis-monitor-daily-review
description: Analyze Thesis Monitor daily review packets using only backend-verified facts, then write and validate structured shadow-review JSON. Use for scheduled US or KR daily investment review, backup catch-up runs, and packet-based review validation.
---

# Thesis Monitor Daily Review

Invoke this workflow as `$thesis-monitor-daily-review` from each scheduled task.

Use this skill only for immutable packets under `data/ai_review/inbox`. Do not browse the web, call an external API, modify application code, or alter the database, official assessment, or Telegram delivery.

## Workflow

1. Claim one packet for the requested market:

   ```bash
   .venv/bin/python -m app.jobs.ai_review claim --market us --owner <task-name>
   ```

   Use `--market kr` for a Korean close review. If the result is `no_pending_packet`, stop without modifying anything.

2. Read the returned `packet_path`, this skill, [daily-review-policy.md](references/daily-review-policy.md), and [output-schema.json](references/output-schema.json).

3. Review the market once and every stock in `stocks`. Use only `fact_id` values from each `fact_catalog` in `facts_used`. Treat absent information as unknown.

4. Write one complete JSON document to the returned `temp_output_path`. Do not write outside `data/ai_review`.

5. Validate and finalize it:

   ```bash
   .venv/bin/python -m app.jobs.ai_review validate --packet-id <packet-id> --policy-version <analysis-policy-version>
   ```

   A nonzero result means the review was rejected. Do not weaken the validator or invent replacement facts. Correct the JSON from the same packet once, then validate again.

## Output Rules

- Keep `schema_version`, `packet_id`, `analysis_policy_version`, `market`, and `assessment_date` identical to the packet.
- Produce exactly one stock review for every packet stock and no others.
- Separate concise facts used, interpretation, and unknowns. Do not output hidden reasoning or chain-of-thought.
- Explain why facts matter, what is noise, what expectations may already reflect, and what number or event should be checked next.
- Do not issue buy or sell orders.
- Keep the deterministic assessment as a guardrail. You may propose a different AI view in shadow, but never erase a deterministic warning.
- Never expose internal parser/provider fields. Never call a modeled estimate market or analyst consensus.
- If historical comparability is withheld, do not use a historical percentile or range.

## Runtime Boundary

Allowed writes:

- `data/ai_review/outbox/*.json.tmp`
- Files produced by the validator under `data/ai_review/outbox`, `history`, or `rejected`

Forbidden writes:

- `app/`, `tests/`, `ops/`, `.github/`, `.agents/`, `pyproject.toml`
- Database or Telegram state

The primary and backup tasks use the same workflow. Claim leases and completed-output checks provide idempotency.
