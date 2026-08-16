# Scheduled Task Contracts

## Required Runtime

All four tasks run in the live local checkout of `sskim-ai/thesis-monitor` with workspace-write
access. They invoke `$thesis-monitor-daily-review`, policy `daily-review-v3.10`, final output schema 4,
OHLCV structure v2, Pilot v3, renderer v3, security identity v2, and financial quality v2. Investment Knowledge v3 and Chart Knowledge v1 must
match the checksums in `docs/project-state.json`.

Each prompt must prohibit external research, source-code edits, direct database mutation, and direct
Telegram writes. Codex writes only the claim-specific temporary output under `data/ai_review`, uses
draft `numeric_fact_refs` placeholders for every newly authored investment number, and lets the
backend render values and generate final claims. `no_pending_packet` is a clean no-op.

## Exact Tasks

All times are Asia/Seoul and use an exact schedule.

| Title | Schedule | Claim command |
|---|---:|---|
| Thesis Monitor US Primary | 08:15 daily | `.venv/bin/python -m app.jobs.ai_review claim --market us --owner codex-us-primary --wait-seconds 300 --poll-seconds 15 --lease-minutes 10` |
| Thesis Monitor US Backup | 08:30 daily | `.venv/bin/python -m app.jobs.ai_review claim --market us --owner codex-us-backup` |
| Thesis Monitor KR Primary | 16:15 daily | `.venv/bin/python -m app.jobs.ai_review claim --market kr --owner codex-kr-primary` |
| Thesis Monitor KR Backup | 16:55 daily | `.venv/bin/python -m app.jobs.ai_review claim --market kr --owner codex-kr-backup` |

Use this prompt for each task, substituting its exact claim command:

> In the current local thesis-monitor project, invoke `$thesis-monitor-daily-review`. Require Pilot
> `ai-assisted-pilot-v3`, policy `daily-review-v3.10`, final schema 4, OHLCV
> `ohlcv-structure-v2`, renderer `ai-assisted-pilot-renderer-v3`, security identity
> `security-identity-v2`, and financial quality `financial-quality-taint-v2`. Run `<CLAIM_COMMAND>`. If it
> returns `no_pending_packet`, stop without modifying anything. Otherwise follow the skill against the
> claimed immutable packet and claim-specific temporary path. Author every new investment number with
> `{{numeric:ref_id}}` plus `numeric_fact_refs`; do not transcribe, calculate, round, relabel, or guess
> a value. Use only routed packet facts and the two repository Knowledge mirrors. Do not browse, edit
> source or tests, mutate official assessment/database state, or send Telegram directly. Run the
> claim-specific validator/finalizer after writing the draft. On validation rejection, use the
> archived machine context to correct the reference or wording, or remove the unsafe number, once;
> then rewrite the claim-specific temporary draft and validate one final time. If it still rejects,
> stop and leave the deterministic fallback eligible. On
> delivery retry, reuse persisted finalized content without recollection, packet regeneration,
> analysis rerun, or reformatting. Production Assist stays disabled.

## Verification Checklist

Before marking the deployment gate passed, confirm in the ChatGPT desktop Scheduled view:

1. exactly these four local-project tasks exist and no duplicate standalone web tasks were created;
2. all four are ACTIVE, use Asia/Seoul, and retain 08:15/08:30/16:15/16:55;
3. each targets the clean operating checkout at the exact pushed `origin/main` commit;
4. each prompt contains v3.10, schema 4, structure v2, Pilot v3, renderer v3, security identity v2,
   financial quality v2, and the appropriate claim
   command;
5. workspace-write is the only filesystem permission and external browsing is unavailable;
6. persisted runtime remains KR 3/5 and US 2/5; the US operational success has separate
   human-quality FAIL status, while natural KR Day 3 is `pending_work_human_review`;
7. task verification, retrospective, or Preview work does not reset or increment either counter;
8. human-quality disposition is tracked separately and Production Assist remains disabled.

Phase 7.2.8 is an isolated branch validation only. The existing four task definitions, schedules,
checkout, policy, and runtime state remain unchanged. Its current-code KR packet replaces the invalid
Phase 7.2.7 closed-session v3.9 regression as financial-quality review evidence, but neither the US
nor KR Preview is a Scheduled Task result or Pilot success. The later natural KR packet is the only
event that advanced runtime to KR 3/5. US remains 2/5 with human-quality FAIL, natural KR Day 3 awaits
Work review, and Production Assist evidence remains false.
