# Next Session Prompt

Use the text below to continue thesis-monitor in a new ChatGPT or Codex session.

---

Repository: `sskim-ai/thesis-monitor`.

First run `git fetch origin`, `git status`, `git rev-parse HEAD`, and
`git rev-parse origin/main`. Compare the current experimental checkout with the clean operating
checkout. Read, in this order:

1. `docs/project-state.json`
2. `docs/MASTER_WORKFLOW.md`
3. `docs/PROJECT_HANDOFF.md`
4. `docs/NEXT_SESSION_PROMPT.md`
5. `docs/reports/20260817-phase8-5-industry-reasoning-validation.md`
6. `docs/reports/20260817-phase8-5-industry-reasoning-audit.md`
7. the KR and US Phase 8.5 full Previews

Repository and immutable runtime state override stale conversation or document claims. Resolve the
current commit from Git rather than copying a historical SHA.

Current architecture is deterministic Facts plus Investment Knowledge v3 and Chart Knowledge v1,
bounded Codex reasoning, numeric/semantic validation, adaptive schema-4 rendering, and a hash-bound
runtime receipt. Phase 8.4.x is the completed message-intelligence foundation, and Phase 8.5 adds
`industry-specific-reasoning-v1`:

- integrated full schema-4 messages;
- delta-first and adaptive section selection;
- company/listed-security valuation scope;
- denied-Fact qualitative echo blocking;
- decision-material delta hierarchy;
- safe historical valuation retention;
- `valuation-context-wording-v1` availability/use classes;
- observer/holder, concrete Unknown, and current-value next-check foundations.
- structured primary/secondary industry routing with confidence;
- Fact-dependent causal and valuation-boundary references;
- framework mismatch and unsupported causal-leap guardrails.

Phase 8.4.1 Work scores were Samsung 17, POSCO 16, Hyundai Glovis 18, Korean Re 16, and SK hynix 17,
average 16.8/20. Phase 8.4.1.1 fixes the one remaining contradiction: visible own-history context can
no longer coexist with current-only wording. The exact final Preview is archive-only and sent no
Telegram.

The Phase 8.5 immutable active audit covers 20 stocks: nine have high-confidence specialized routes
and eleven remain low-confidence general fallback. This is strong PARTIAL because current structured
profiles do not prove finer routes for every company. Human-quality status remains pending Work
review; Codex's archive-only KR assessment averages 17.0/20 and is not Production Assist evidence.

Current core contracts:

- policy `daily-review-v3.10`
- output schema `4`
- OHLCV `ohlcv-structure-v2`
- security identity `security-identity-v2`
- financial quality `financial-quality-taint-v2`
- financial statement/amount basis v1
- financial lineage `financial-lineage-v2`
- typed valuation `typed-valuation-interpretation-v2`
- market cross-section `market-cross-section-v1`
- delta-first `delta-first-rendering-v1`
- decision hierarchy `decision-material-delta-v1`
- valuation context `valuation-context-wording-v1`
- industry reasoning `industry-specific-reasoning-v1`
- runtime gate `runtime-message-quality-v1`
- receipt `runtime-message-quality-receipt-v2`
- Pilot `ai-assisted-pilot-v3`, renderer v3
- Public Action `0.4.5`, operationId 20/20 unique

Knowledge checksums:

- Investment v3:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart v1:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

Runtime source of truth at handoff: KR 3/5 and US 3/5, AI mode shadow, Production Assist OFF, four
Scheduled Tasks ACTIVE at 08:15/08:30/16:15/16:55 KST on the operating checkout. The natural KR
packet `2026-08-17-kr-run-23-378ee562573e` was rejected pre-send because four stocks lacked required
current-price RR Facts. AI send was zero, fallback eligibility was preserved, deterministic fallback
later sent 8/8 at 17:10 KST, and Pilot did not advance. Reconcile any later natural result instead of
forcing these counts.

Default next task: **Runtime RR Packet Repair**. Repair the missing required current-price RR
Fact/numeric path without weakening validation, then collect natural Phase 8.5 evidence. Before
starting, determine whether KRX API approval is now available. If approved, report whether **Phase
8.2A KRX Market Breadth Primary** should be inserted first. Do not combine both scopes without user
approval.

Preserve the Phase 8.5 boundary: do not infer missing metrics, promote themes into company
achievements, force fine-grained taxonomy, create thresholds, or relax numeric, lineage, scope,
renderer, receipt, fallback, or exactly-once validation.

Do not merge main, deploy, run Scheduled Tasks manually, send Telegram, mutate the operating DB,
assessment, archive, notification, delivery, or Pilot, or enable Production Assist without an
explicit work order.

Before completion run focused tests, full `pytest -q`, `ruff check .`, `git diff --check`, Knowledge
checksum parity, Public Action 0.4.5, operationId 20/20 uniqueness, runtime isolation checks, push
without force, and GitHub Actions Test/Lint for the exact final commit.

---
