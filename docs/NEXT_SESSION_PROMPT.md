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
7. `docs/reports/20260817-runtime-current-price-rr-repair-validation.md`
8. `docs/reports/20260817-runtime-current-price-rr-run23-replay.md`
9. `docs/reports/20260817-phase8-5-2-shadow-release-validation.md`
10. `docs/reports/20260817-operating-shadow-state.md`
11. `docs/reports/20260818-phase8-5-3-natural-live-message-root-cause.md`
12. `docs/reports/20260818-phase8-5-3-natural-live-message-validation.md`
13. `docs/reports/20260818-phase8-5-3-ai-natural-live-hardening-preview.md`
14. `docs/reports/20260818-phase8-5-3-fallback-price-parity-preview.md`
15. `docs/reports/20260818-phase8-5-3-1-language-dedup-validation.md`
16. `docs/reports/20260818-phase8-5-3-1-language-dedup-preview.md`
17. `docs/reports/20260818-phase8-5-3-1-language-dedup-audit.json`
18. `docs/reports/20260818-phase8-5-3-1-shadow-promotion.md`
19. `docs/reports/20260818-phase8-5-3-2-rxrx-valuation-label-validation.md`
20. `docs/reports/20260818-phase8-5-3-2-rxrx-valuation-label-preview.md`
21. `docs/reports/20260818-phase8-5-3-2-valuation-label-audit.json`
22. `docs/reports/20260818-phase8-5-3-2-shadow-promotion.md`

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
- current price context `current-price-context-v1`
- runtime specificity `runtime-message-specificity-v1`
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
Scheduled Tasks ACTIVE at 08:15/08:30/16:15/16:55 KST on the operating checkout. Phase 8.5.3.1
implementation commit `e166aaf6a4c13f9009a3885737d3b48e34c895d5` is included in main and the
operating checkout; always re-resolve the final documentation SHA. Reconcile any later natural
result instead of forcing these counts.

Phase 8.5.1 traced the failure to weekday-only KRX session classification. XKRX was closed on
2026-08-17, so the 2026-08-14 chart was the latest completed session and should have remained fresh.
The exchange-calendar repair restores exact canonical RR Facts and numeric paths for all four
affected stocks in read-only replay. Three unavailable controls remain unavailable by contract. The
original eight RR missing-path errors become zero. The natural 2026-08-18 KR packet then carried
complete paths for all four affected stocks with zero numeric/semantic hard errors, so Current-Price
RR Runtime Path is `LIVE PATH PASS`.

Phase 8.5.2 promoted the complete Phase 8.5.1 ancestry to `origin/main` and the clean operating
checkout. Implementation SHA: `2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf`; final operating main:
`a8ebb02753e28795f36dbf72c9deb3520f75ed44`. Exact-main GitHub
Actions run `32023730416` passed Test and Lint. The API was restarted and healthy; operating smoke
tests passed 89/89. All four Scheduled Tasks still target the configured operating checkout, and
no task was manually run. This is shadow deployment readiness, not Natural Live proof or Production
Assist approval.

Natural 2026-08-18 US packet `2026-08-18-us-run-24-487c07bde4e1` and KR packet
`2026-08-18-kr-run-25-23b5e31dc20e` had zero numeric/semantic hard errors but failed the runtime
message quality gate. Deterministic fallback delivered 14/14 US and 8/8 KR. Phase 8.5.3 immutable
replay passes both full validators and the unchanged quality gate: literal/skeleton duplicates fall
from US 3/7 and KR 5/7 to zero. Its fallback selector uses current dynamic support/resistance, RR,
invalidation, chart state, and registered lifecycle; crossed confirmations rendered as future
triggers fall from nine to zero. This code is now included in the Phase 8.5.3.1 operating promotion.

Phase 8.5.3.1 fixes the remaining Preview language and within-stock repetition defects. US object-
particle errors fall from six to zero, KR malformed supply phrases from two to zero, US watch/next
meaningless overlap from 13 stocks to zero, and the same RR Fact appearing three or more times from
six KR stocks to zero. Both immutable full validators, runtime quality, and final language pass.
The full Phase 8.5.3/8.5.3.1 chain was fast-forwarded to operating shadow after exact-SHA Actions
Test/Lint PASS; API health and 154 focused operating tests pass. Production Assist remains OFF.

Phase 8.5.3.2 fixes the remaining RXRX valuation display collision. The current PBR, historical PBR
median, and historical percentile now retain distinct comparison roles and labels; one additional
WULF legacy collision is closed by the same generic rule. Implementation
`b3ad1ea82bdbd3fe003831d449b0dcaa7c6a2da2` passed exact-SHA Actions run `32126079970` and is
promoted to operating shadow. Natural AI-assisted delivery remains PARTIAL.

Default operating task: inspect the **next natural US/KR packets** for AI specificity, Korean language,
intra-message dedup, dynamic-price parity, full-validator status, receipt, delivery/fallback,
archive, exactly-once state, and human message quality. Do not run a Scheduled Task manually. KRX
Open API is **APPROVED / NOT INTEGRATED**. Phase 8.2A may be developed and archive-validated on an
experimental branch while live proof is pending, but must not be merged or deployed. Phase 8.3
Peer/Sector Valuation follows. Do not combine operating and experimental scopes.

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
