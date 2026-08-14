# Next Session Prompt

Use the text below to continue thesis-monitor work in a new ChatGPT or Codex session.

---

Repository: `sskim-ai/thesis-monitor`, branch `main`.

Start by running `git fetch origin`, then compare `origin/main`, the development checkout, and the
operating checkout. Resolve the exact current commit with `git rev-parse HEAD`; do not trust a commit
hash copied from an older conversation. Read these files before changing code:

1. `docs/PROJECT_HANDOFF.md`
2. `docs/project-state.json`
3. `docs/architecture/AI_ASSISTED_MONITORING.md`
4. `docs/architecture/OHLCV_STRUCTURE_ENGINE.md`
5. `docs/architecture/MARKET_INTELLIGENCE.md`
6. `docs/operations/AI_ASSISTED_PILOT.md`
7. `docs/knowledge/README.md`
8. `.agents/skills/thesis-monitor-daily-review/SKILL.md`

Project purpose: keep deterministic `ThesisAssessment` as official source of truth while Codex uses
backend-verified facts, Investment Knowledge v3, and Chart Knowledge v1 to produce a validated,
quantitative market-and-stock interpretation. Telegram must receive one AI-assisted set on success or
one deterministic fallback set on AI failure.

Current contracts:

- Investment Knowledge 3.0 SHA
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge 1.0 SHA
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- AI policy `daily-review-v3.7`
- output schema 4
- OHLCV structure `ohlcv-structure-v2`
- Pilot `ai-assisted-pilot-v3`, KR 0/5 and US 0/5 at activation
- renderer `ai-assisted-pilot-renderer-v3`
- AI mode shadow; Production Assist disabled
- Public Action 0.4.5, operationId 20/20

Absolute safety rules:

- Do not browse or add external facts to an AI review packet.
- Do not let AI mutate assessment, thesis, warnings, notifications, or Telegram directly.
- Unknown numeric semantics fail closed; every prose number needs exact fact, field, semantic, text
  location, and approved display.
- Local Pivot is not Major Swing. Chart invalidation is not thesis invalidation. Chart state is not a
  buy/sell command.
- Market context is not company fundamental confirmation.
- Modeled estimates are not consensus. Suppressed historical valuation stays absent.
- One session sends AI-assisted or deterministic fallback, never both.
- Four or more safe prose-eligible anchors with zero numeric claims is a Pilot hard failure; sparse
  packets remain Unknown rather than receiving invented numbers.
- Fresh backend-selected KOSPI200/KOSDAQ150 night futures must be grounded and interpreted as Korean
  opening context, never as company-thesis confirmation.

US morning schedule: deterministic run and first KRX fetch 08:05, KRX deadline 08:20, Codex Primary
08:15, Backup 08:30, deterministic fallback 08:40. Telegram network retry reuses persisted final
text and never reruns analysis.

Known data gaps: KR local indices, market breadth, market-wide investor flows, broad sector coverage,
and some conservative general-profile taxonomy. Do not fill them with model knowledge.

Next work order:

1. Verify exact deployment and four Scheduled Task contracts.
2. Start/continue Pilot v3 only after all gates are green.
3. Review each successful market session by DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING,
   AI_REASONING, VALIDATION, RENDERER, and DELIVERY.
4. Preserve exact archives and old cohorts.
5. Keep Production Assist disabled until a separate explicit user decision.

Before completion, run full pytest, Ruff, `git diff --check`, Knowledge checksum validation, Skill and
schema validation, documentation path validation, push the exact commit, verify GitHub Actions Test
and Lint, then align the operating checkout and Scheduled Tasks.

---
