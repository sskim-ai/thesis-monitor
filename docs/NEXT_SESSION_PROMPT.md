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
6. `docs/architecture/NUMERIC_PROVENANCE.md`
7. `docs/architecture/MONITORING_STATE_LIFECYCLE.md`
8. `docs/architecture/PEER_VALUATION.md`
9. `docs/operations/AI_ASSISTED_PILOT.md`
10. `docs/operations/SCHEDULED_TASK_CONTRACTS.md`
11. `docs/knowledge/README.md`
12. `.agents/skills/thesis-monitor-daily-review/SKILL.md`

Project purpose: keep deterministic `ThesisAssessment` as official source of truth while Codex uses
backend-verified facts, Investment Knowledge v3, and Chart Knowledge v1 to produce a validated,
quantitative market-and-stock interpretation. Telegram must receive one AI-assisted set on success or
one deterministic fallback set on AI failure.

Current contracts:

- Investment Knowledge 3.0 SHA
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge 1.0 SHA
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- AI policy `daily-review-v3.10`
- output schema 4
- OHLCV structure `ohlcv-structure-v2`
- security identity `security-identity-v2`
- financial quality `financial-quality-taint-v2`
- Pilot `ai-assisted-pilot-v3`, persisted runtime count KR 3/5 and US 2/5; the latest US quality
  review failed, the natural KR Day 3 message review is pending Work review, and neither session is
  currently Production Assist evidence
- renderer `ai-assisted-pilot-renderer-v3`
- AI mode shadow; Production Assist disabled
- Public Action 0.4.5, operationId 20/20

Absolute safety rules:

- Do not browse or add external facts to an AI review packet.
- Do not let AI mutate assessment, thesis, warnings, notifications, or Telegram directly.
- Codex must use draft numeric fact references and placeholders for new numbers. The backend owns raw
  value, unit, semantic, source-aware label, rounding, approved display, and generated schema-4
  claims. Unknown semantics and uncovered raw prose numbers fail closed.
- Local Pivot is not Major Swing. Chart invalidation is not thesis invalidation. Chart state is not a
  buy/sell command.
- Market context is not company fundamental confirmation.
- Modeled estimates are not consensus. Suppressed historical valuation stays absent.
- One session sends AI-assisted or deterministic fallback, never both.
- The renderer preserves validated prose and may not apply broad semantic word replacement.
- AI validation rejection preserves held deterministic fallback eligibility. Delivery retry reuses
  the same persisted payload and never recollects, regenerates, reanalyzes, or reformats.
- A Pilot success is recorded only after full delivery, required archive verification, and a verified
  atomic `archive-complete.json` marker. Archive recovery must not resend Telegram and must count a
  packet/date at most once.
- Four or more safe prose-eligible anchors with zero numeric claims is a Pilot hard failure; sparse
  packets remain Unknown rather than receiving invented numbers.
- Fresh backend-selected KOSPI200/KOSDAQ150 night futures must be grounded and interpreted as Korean
  opening context, never as company-thesis confirmation.
- Registered price rules remain audit history. Current Strong/Medium dynamic structure and state
  delta are primary, and a crossed confirmation is never auto-promoted to support.
- Earnings amounts use verified financial currency; price and per-security valuation use verified
  security/price currency. An ADR price currency never relabels issuer financial statements. Missing
  or blank financial currency is `unknown`, and unsupported monetary units remain auditable but
  prose-denied. Never substitute price currency.
- Peer valuation requires verified profile, same geography, comparable basis, same-date data, and at
  least three peers excluding the company. Missing broad peer data remains unavailable.
- Inferred/default security identity cannot establish verified non-depositary status. Identity and
  current-security denominator/share/currency basis are separate gates. Critical financial inputs
  taint only their exact direct and derived lineage, and denied lineage cannot be interpreted
  qualitatively through an aggregate valuation fact.

The natural 2026-08-15 KR v3.9 Scheduled Task packet
`2026-08-15-kr-run-19-919a670464b4` passed validation, delivered 8/8, completed its verified archive,
and was counted exactly once as KR Day 2/5. Experimental v3.10 retrospective or Preview output does
not change this persisted count. Treat any next-day Pilot label as a candidate until delivery,
archive completion, and runtime state all agree.

The natural 2026-08-16 KR v3.10 packet `2026-08-16-kr-run-21-049f367f0274` passed validation,
delivered the market plus all seven active stocks 8/8, verified 13 required archive artifacts, and
was counted exactly once after `archive-complete.json`. Runtime state is therefore KR 3/5 and US 2/5.
Human message quality is `pending_work_human_review`, and the packet is not eligible Production
Assist evidence unless Work explicitly approves the persisted eight-message payload. Read
`docs/reports/20260816-third-natural-kr-v310-operational-reconciliation.md` and its linked Preview and
audits. Do not rerun AI, binding, validation, rendering, or Telegram delivery for this session.

The first natural v3.10 US packet `2026-08-16-us-run-20-6c15d0003955` passed the automated pipeline,
delivered 14/14, completed its archive, and was recorded exactly once, so runtime state now says US
2/5. Human message-quality review failed: CRCL's confirmation transition is internally inconsistent,
SKHY's prose incorrectly says its verified ADS identity is unverified, and all 13 US stock messages
repeat a KR-style investor-flow horizon frame. TSM and WRD also resolve to `unknown` in the packet
despite the deployment cross-section's `verified_depositary` result. Unsafe multiples stayed absent.
Do not edit the counter ad hoc; reconcile the quality/count contract explicitly before accepting a
further US Pilot advance. Read `docs/reports/20260816-first-natural-v310-live-validation.md` first.

Phase 7.2.7 is preserved as failed human-review evidence. Its KR regression reused a v3.9 artifact
from the closed 2026-08-15 KR session and is not current financial-quality acceptance evidence.

Phase 7.2.8 on `codex/phase-7-2-7-live-quality-reconciliation` preserved the then-current runtime
KR 2/5 and US 2/5 while repairing the remaining deterministic boundaries. The later natural KR Day
3 session, not that retrospective, advanced current runtime to KR 3/5. Corrected US experiment packet
`2026-08-16-us-run-20-a48638e987ce` passes 171 automatic bindings and 14/14 logical messages. Fresh
current-code KR packet `2026-08-14-kr-run-17-006189184b28` is built from the latest eligible complete
after-hours session, passes 141 automatic bindings and 8/8 messages, and keeps SK Hynix denied
earnings and dependent PE lineage out of prose. Both validators have zero errors and the label,
instrument, zone-role, postposition, identity, comparison, supply, and repetition hard checks pass.
TSM and WRD remain safely `unknown` because production has no authoritative identity cache. Review
`docs/reports/20260816-phase7-2-8-human-review-safety-readiness.md` and its linked full Previews.
The branch is not merged or deployed, and the correction is not human-approved evidence yet.

US morning schedule: deterministic run and first KRX fetch 08:05, KRX deadline 08:20, Codex Primary
08:15, Backup 08:30, deterministic fallback 08:40. Telegram network retry reuses persisted final
text and never reruns analysis.

Known data gaps: KR local indices, market breadth, market-wide investor flows, broad sector and peer
valuation coverage, and some conservative general-profile taxonomy. Do not fill them with model
knowledge.

Next work order:

1. Review the exact persisted KR Day 3 market-plus-seven-stock Preview and record Work's human-quality
   disposition separately from the operational KR 3/5 count.
2. Do not begin Phase 7.2.9 implementation without explicit resume approval.
3. Keep the Phase 7.2.8 corrected US/KR Previews experimental and unmerged; retain TSM/WRD identity
   as `unknown` unless authoritative evidence is separately ingested.
4. Preserve the US 2/5 human-quality failure, KR 3/5 pending status, exact archives, and old cohorts;
   do not edit counters or replay Telegram.
5. Keep Production Assist disabled until blocking quality findings are closed and the user explicitly
   approves it.

Before completion, run full pytest, Ruff, `git diff --check`, Knowledge checksum validation, Skill and
schema validation, documentation path validation, push the exact commit, and verify GitHub Actions
Test and Lint. Do not align the operating checkout or Scheduled Tasks until a separate deployment
approval.

---
