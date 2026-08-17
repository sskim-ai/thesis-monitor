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
- experimental KR field lineage `financial-lineage-v2` with Phase 8.1.1 authoritative archive-only
  recovery on `codex/phase-8-1-1-authoritative-financial-recovery`; not deployed
- Pilot `ai-assisted-pilot-v3`, persisted runtime count KR 3/5 and US 3/5; the natural US Day 2 and
  KR Day 3 human message-quality reviews failed, while US Day 3 has no Phase 8 human-quality approval
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
was counted exactly once after `archive-complete.json`. Runtime state at that point was KR 3/5 and
US 2/5.
Human message quality is `failed`, while the operational KR 3/5 count remains unchanged. The packet
is not eligible Production Assist evidence. Work found six numeric-postposition defects,
actor/horizon supply claims without matching visible numbers, a repeated core-judgment template,
financial amounts without period labels, and valuation conclusions without adequate comparison
evidence. Read `docs/reports/20260816-third-natural-kr-v310-work-human-review.md` and the linked
operational report, Preview, and audits. Do not rerun AI, binding, validation, rendering, or Telegram
delivery for this session.

The later natural US packet `2026-08-17-us-run-22-217ce9f324b9` passed the operating validator,
delivered 14/14, archived 13 required artifacts, and was counted exactly once after its completion
marker. Current operational state is KR 3/5 and US 3/5. Phase 8 did not perform a human-quality review
of this packet, so do not treat it as Production Assist evidence.

Phase 8.1 on `codex/phase-8-1-kr-financial-lineage` is a branch-only provider/canonical experiment.
It uses OpenDART full financial statements to preserve field-level CFS/OFS, amount-period, account,
currency, comparison, source-type, and correction lineage. Growth and margin are exact dependency
Facts, so an unsafe comparison no longer requires suppressing a separately verified current amount.
The operating DB predates v2 and has no source rows that can be safely reconstructed, so no
historical amount was backfilled. XBRL context parsing is exact and fail-closed. Read
`docs/architecture/KR_FINANCIAL_LINEAGE.md`, `docs/providers/OPENDART_FINANCIALS.md`, and
`docs/reports/20260817-phase8-1-kr-financial-lineage-validation.md` before continuing.

Phase 8.1.1 resolves the Phase 8.1 evidence gap without mutating production. Seven latest formal
filings yielded 1,818 CFS and 1,291 OFS rows. Exact field promotion recovered 17 safe
income-statement amounts, five margins, six inventory Facts, and 17 comparable YoY Facts across the
active KR universe. Three SK hynix income fields remain denied under the existing quality conflict.
All seven interim OCF candidates remain Unknown after exact XBRL reconciliation produced zero
unique basis/period matches; 28 CAPEX components are audit-only and FCF stays unavailable. Review
`docs/reports/20260817-phase8-1-1-authoritative-financial-recovery.md`, its JSON audit, and the five
persisted Before / recovered After messages. These Previews are `pending_work_human_review` and are
not Production Assist evidence. Do not promote the shadow cache or merge/deploy this branch without
separate approval.

Massive Phase 8.1 remains shadow-only. Reference cache TTL is one trading day; adjusted decimal
volume and deterministic close-times-adjusted-volume are audit-only. Exact 08:05 KST readiness is
`NOT_YET_OBSERVED`, despite complete after-deadline capability data. Do not change Scheduled Task
times until 3-5 normal sessions are observed. See
`docs/reports/20260817-massive-0805-shadow-readiness.md`.

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

Phase 7.2.9 on the same experimental branch adds typed Korean numeric postpositions, exact KR
actor/horizon supply grounding, amount-period labels, comparison-backed valuation language,
`valuation-coherence-v1`, US relative-volume semantics, normalized reasoning-template checks, and
the mandatory `runtime-message-quality-v1` delivery receipt. Read
`docs/reports/20260816-phase7-2-9-runtime-quality-readiness.md` and both linked full Previews. The
immutable KR Day 3 output fails the new gate as expected; corrected isolated KR and US outputs pass
the binder, full validator, and runtime gate but remain `pending_work_human_review`. Production main
and the operating checkout do not contain this application code.

Work later failed the Phase 7.2.9 corrected KR Preview because Samsung's Q2 amount was labeled H1,
Hanwha's current-price and support-entry RR were conflated, and valuation interpretation remained
too permissive; the US Preview stayed unapproved. Phase 7.2.9.1 is on
`codex/phase-7-2-9-1-quality-blockers`. Its corrected isolated KR and US payloads pass the new
field-level amount-period, RR-basis, typed-valuation, receipt-integrity, validator, and runtime-gate
checks, but Work failed both Previews for statement-basis, occurrence-scope, final-language,
relation/caution, and receipt-edge-case defects. Read
`docs/reports/20260817-phase7-2-9-1-work-human-review.md`; do not promote the earlier deterministic
PASS to human approval.

Phase 7.2.9.2 is on `codex/phase-7-2-9-2-human-quality-hardening`. It adds verified
consolidated/separate amount basis, exact occurrence-bound typed valuation evidence, final rendered
language checks, relation/caution consistency, and distinct pre-send versus post-partial receipt
integrity handling. Corrected isolated packets `2026-08-16-kr-run-21-23491b3e8f73` and
`2026-08-16-us-run-20-fb918a643ae6` pass mechanical gates with 8 and 14 logical payloads. Start with
`docs/reports/20260817-phase7-2-9-2-readiness.md` and its linked Previews. Both remain
`pending_work_human_review`; do not merge or deploy without separate approval.

US morning schedule: deterministic run and first KRX fetch 08:05, KRX deadline 08:20, Codex Primary
08:15, Backup 08:30, deterministic fallback 08:40. Telegram network retry reuses persisted final
text and never reruns analysis.

Phase 8 on `codex/phase-8-0a-8-2-market-breadth` implements a shadow Massive US cross-section and a
fail-closed Kiwoom Windows-gateway bridge contract. Massive capability is supported, but exact 08:05
KST readiness remains pending weekday shadow. Kiwoom remains PARTIAL/NOT_CONFIGURED; KRX remains the
future primary. Read `docs/reports/20260817-phase8-massive-kiwoom-capability.md` and
`docs/architecture/MARKET_CROSS_SECTION.md`. Do not call ETF proxy returns breadth or infer absent KR
flow.

Known data gaps: KR local breadth, market-wide investor flows, constituent sector participation,
broad peer valuation coverage, and some conservative general-profile taxonomy. Do not fill them with
model knowledge.

Next work order:

1. Preserve the KR Day 3 and US Day 2 human-quality failures separately from their operational counts.
2. Review the Phase 7.2.9.2 corrected KR/US Previews and runtime receipt evidence; do not call their
   deterministic PASS a human-quality approval.
3. Keep the Phase 7.2.9.2 implementation experimental and unmerged; retain TSM/WRD identity as
   `unknown` unless authoritative evidence is separately ingested.
4. Preserve exact packets, outputs, archives, and old cohorts; do not replay Telegram.
5. Keep KR 3/5 and US 3/5 unchanged, and keep Production Assist disabled until blocking quality
   findings are closed and the user explicitly approves it.
6. Keep Massive and Kiwoom shadow-only. Gather Massive 08:05 timing evidence and wait for KRX
   activation plus a configured Kiwoom gateway before any production source transition.

Before completion, run full pytest, Ruff, `git diff --check`, Knowledge checksum validation, Skill and
schema validation, documentation path validation, push the exact commit, and verify GitHub Actions
Test and Lint. Do not align the operating checkout or Scheduled Tasks until a separate deployment
approval.

---
