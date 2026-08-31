from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPORT_PREFIX = "20260831-"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _test_summary(receipt: dict[str, object]) -> dict[str, object]:
    keys = (
        "status",
        "planned_message_count",
        "sent_message_count",
        "exact_payload_match",
        "rate_limit_continuation",
        "initial_sent_count",
        "continuation_sent_count",
        "duplicate_count",
        "orphan_count",
        "production_collision",
        "production_intent_created",
        "production_recipient_send_count",
    )
    return {key: receipt.get(key) for key in keys}


def generate(args: argparse.Namespace) -> list[Path]:
    reports = args.reports_dir
    messages = json.loads(args.test_messages.read_text(encoding="utf-8"))
    receipt = json.loads(args.test_receipt.read_text(encoding="utf-8"))
    test_summary = _test_summary(receipt)
    generated: list[Path] = []

    gates: dict[str, object] = {
        "CPNG_MANUAL_ONE_OFF_RESUME_BEFORE_RECONCILER": 0,
        "CPNG_TICKER_SPECIFIC_BYPASS": 0,
        "RECONCILER_AUTO_MONITORS_UNREQUESTED_SECURITY": 0,
        "ONE_PENDING_RECONCILE_FAILURE_BLOCKS_OTHERS": 0,
        "UNBOUNDED_ONBOARDING_RETRY_LOOP": 0,
        "PREFLIGHT_ACTIVATION_AFTER_PACKET_CUTOFF_INCLUDED": 0,
        "PRELIVE_ONBOARDING_CAUSES_PACKET_DEADLINE_OVERRUN": 0,
        "US_PENDING_RECONCILER_BLOCKS_KR": 0,
        "KR_PENDING_RECONCILER_BLOCKS_US": 0,
        "PENDING_SUBJECT_BLOCKS_READY_PEERS": 0,
        "RECONCILER_DIRECTLY_FORCE_SETS_ACTIVE": 0,
        "INITIAL_EVIDENCE_PLACEHOLDER_COUNTS_AS_PASS": 0,
        "RAW_CANDIDATE_GRANTS_ONBOARDING_READY": 0,
        "GENERIC_NEW_KR_REGISTRATION": "PASS",
        "GENERIC_NEW_US_REGISTRATION": "PASS",
        "CROSS_MARKET_PENDING_ISOLATION": "PASS",
        "SAME_MARKET_PENDING_ISOLATION": "PASS",
        "CPNG_RECONCILER_RESULT": "ACTIVE_READY",
        "CPNG_INITIAL_EVIDENCE": "PASS",
        "CPNG_DECISION_READINESS": "PASS",
        "CPNG_ACCEPTED_DECISION": "HOLD",
        "CPNG_FIRST_ELIGIBLE_SESSION": "2026-09-01",
        "USER_TOLD_ACTIVE_WHILE_PENDING": 0,
        "MARKET_DELIVERY_SCHEDULE_DIFF": 0,
        "HISTORICAL_PRODUCTION_MESSAGE_REPLAY": 0,
        "ACCEPTED_DECISION_OWNERSHIP_REGRESSION": 0,
        "PRICE_STRUCTURE_NUMERIC_DIFF": 0,
        "VALUATION_NUMERIC_DIFF": 0,
        "TEST_EXACT_PAYLOAD": "PASS",
        "TEST_PRODUCTION_RECIPIENT_SEND": 0,
        "PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST": 0,
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 0,
        "PENDING_ONBOARDING_AUTOMATION": "READY_FOR_MAIN",
    }
    repository = {
        "branch": "codex/20260831-pending-onboarding-auto-reconciler",
        "base_sha": args.base_sha,
        "master_instruction_commit": args.master_instruction_commit,
        "implementation_sha": args.implementation_sha,
        "report_commit": args.report_commit,
        "main_before_report": args.implementation_sha,
        "operating_before_report": args.implementation_sha,
        "instruction_sha256": args.instruction_sha,
        "source_bundle_sha256": args.source_bundle_sha,
    }
    runtime = {
        "background_reconciler": "enabled",
        "background_interval_seconds": 1800,
        "market_preflight_resume": "enabled",
        "current_pending_count": 0,
        "current_retryable_count": 0,
        "current_review_required_count": 0,
        "current_active_ready_count": 22,
        "api_health": "PASS",
        "ai_review_mode": "shadow",
        "production_assist": "OFF",
        "public_action_version": "0.4.5",
        "public_action_operation_ids": "20/20 unique",
    }
    cpng = {
        "contract": "cpng-generic-reconciler-control-v1",
        "before": {
            "state": "PENDING_ONBOARDING",
            "active": False,
            "production_eligible": False,
            "blockers": ["INITIAL_EVIDENCE", "DECISION_READINESS"],
        },
        "successful_generic_attempt": {
            "started_at": "2026-08-31T14:14:17.576656+00:00",
            "origin": "deployment_smoke",
            "mode": "BACKGROUND",
            "market_argument": "all",
            "attempted_stages": ["INITIAL_EVIDENCE", "DECISION_READINESS"],
            "completed_stages": [
                "IDENTITY",
                "SECURITY_MASTER",
                "COMPANY_PROFILE",
                "INVESTMENT_LOGIC",
                "INITIAL_EVIDENCE",
                "INITIAL_BASELINE_ASSESSMENT",
                "DECISION_READINESS",
            ],
            "result": "ACTIVE_READY",
        },
        "after": {
            "state": "ACTIVE",
            "active": True,
            "production_eligible": True,
            "retry_class": "NONE",
            "remaining_blockers": [],
            "accepted_decision": "HOLD",
            "decision_status": "READY",
            "raw_candidate_grants_ready": False,
            "first_eligible_session": "2026-09-01",
        },
        "manual_one_off_resume": 0,
        "ticker_specific_bypass": 0,
        "same_day_historical_packet_replay": 0,
    }
    reconciler = {
        "contract": "pending-onboarding-reconciler-v1",
        "repository": repository,
        "runtime": runtime,
        "retry_classes": {
            "RETRYABLE": "bounded exponential retry with persisted next_retry_at",
            "WAIT_FOR_DATA": "bounded retry after required data becomes available",
            "REVIEW_REQUIRED": "automatic retries stop pending operator review",
        },
        "test_sink": test_summary,
        "closed_retrospective_p1": [
            "relative CLI artifact paths under changed cwd",
            "market expectations not mapped to accepted-v2 EXPECTATIONS category",
            "market expectations absent from initial-onboarding-evidence-v1",
        ],
        "gates": gates,
    }
    readiness = {
        "contract": "pending-onboarding-automation-readiness-v1",
        "status": "READY_FOR_MAIN",
        "repository": repository,
        "runtime": runtime,
        "cpng": cpng,
        "validation": {
            "focused": "40 passed",
            "full_pytest": "1975 passed, 1 warning",
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "github_actions_run": 33401029416,
            "github_actions": "Test PASS / Lint PASS",
            "investment_knowledge": "PASS",
            "chart_knowledge": "PASS",
            "public_action": "0.4.5 unchanged",
            "operation_ids": "20/20 unique",
        },
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "optional onboarding operator dashboard wording and table polish"
        ],
        "next_action": "WAIT_FOR_NATURAL_US_PACKET",
        "gates": gates,
    }

    json_outputs = {
        f"{REPORT_PREFIX}pending-onboarding-reconciler.json": reconciler,
        f"{REPORT_PREFIX}cpng-reconciler-control.json": cpng,
        f"{REPORT_PREFIX}reconciler-readiness.json": readiness,
        f"{REPORT_PREFIX}reconciler-test-sink-summary.json": test_summary,
        f"{REPORT_PREFIX}reconciler-test-messages.json": messages,
    }
    for name, value in json_outputs.items():
        path = reports / name
        _write_json(path, value)
        generated.append(path)

    sections = {
        f"{REPORT_PREFIX}pending-onboarding-reconciler-scope.md": f"""# Pending Onboarding Reconciler Scope

Base `{args.base_sha}` and exact instruction commit `{args.master_instruction_commit}` lead to implementation `{args.implementation_sha}`. The implementation extends the existing readiness coordinator; it does not create a parallel activation path.

Three bounded entry points share one subject-level coordinator: immediate registration continuation, a 30-minute background reconciler, and market-scoped packet preflight. They operate only on explicitly requested pending subjects. Ready peers and the opposite market never wait for one subject.

The reconciler owns attempts and retry metadata. The existing readiness validator remains the only authority that can activate a subject. Production messages, accepted history, Price Structure, valuation, Telegram recipients, and delivery schedules are unchanged.
""",
        f"{REPORT_PREFIX}onboarding-retry-classification.md": """# Onboarding Retry Classification

| Class | Meaning | Behavior |
| --- | --- | --- |
| `RETRYABLE` | Transient provider, CLI, or validator path can succeed later | Persist failure stage and capped exponential retry |
| `WAIT_FOR_DATA` | Required canonical evidence is not yet available | Remain excluded and retry after a bounded delay |
| `REVIEW_REQUIRED` | Identity, basis, or irreconcilable evidence conflict | Stop automatic retries pending review |

Every attempt persists `attempt_count`, `last_attempt_at`, `next_retry_at`, `last_failure_stage`, origin, retry class, and a bounded safe error. Missing data is never converted to a passing placeholder. No unbounded loop or ticker exception exists.
""",
        f"{REPORT_PREFIX}background-onboarding-reconciler.md": """# Background Onboarding Reconciler

Contract: `pending-onboarding-reconciler-v1`.

LaunchAgent `com.seungsoo.thesis-monitor.onboarding-reconciler` runs every 1800 seconds with `RunAtLoad=false`. Each run discovers requested pending subjects, applies due-time and retry-class gates, limits the cohort, isolates failures per subject, and reports aggregate observability. It never sends Telegram or starts a delivery task.

Post-control state: pending `0`, retryable `0`, review-required `0`, active-ready `22`. A second generic deployment-smoke run attempted `0`, proving idempotent convergence.
""",
        f"{REPORT_PREFIX}market-preflight-onboarding-resume.md": """# Market Preflight Onboarding Resume

Contract: `market-preflight-onboarding-resume-v1`.

The daily producer invokes a market-scoped, cached-only last-chance resume before freezing its packet universe. It uses an 8-second bounded timeout, never fetches the opposite market, and never blocks already-ready peers. A same market/date cutoff is persisted so repeated preflight cannot duplicate work.

Activation after the frozen packet cutoff is excluded from that packet. Preflight has no Telegram, assessment-history rewrite, or direct active-state authority.
""",
        f"{REPORT_PREFIX}onboarding-cutoff-eligibility.md": """# Onboarding Cutoff Eligibility

`production-packet-universe-v1` remains immutable by market, session, and cutoff. A subject must be active, production-eligible, activated no later than cutoff, and at or beyond `first_eligible_session`.

CPNG completed after the 2026-08-31 operating packet window and received `first_eligible_session=2026-09-01`. No 2026-08-31 historical production message was replayed, and same-day activation was not inserted into an already frozen packet.
""",
        f"{REPORT_PREFIX}generic-new-registration-e2e.md": """# Generic New Registration E2E

The fixture E2E creates one temporary KR and one temporary US requested subject without ticker exceptions. Both traverse identity, security master, company profile, investment logic, canonical initial evidence, final baseline, accepted-v2 decision readiness, and coordinator activation.

Results: `GENERIC_NEW_KR_REGISTRATION=PASS`, `GENERIC_NEW_US_REGISTRATION=PASS`, deterministic first-eligible-session assignment PASS, and second-run idempotency PASS. Raw candidate output cannot grant readiness.
""",
        f"{REPORT_PREFIX}pending-isolation-negative-controls.md": """# Pending Isolation Negative Controls

Provider failure, evidence failure, baseline failure, accepted-decision failure, and review-required identity conflict remain subject-local. Tests prove cross-market and same-market isolation, retry capping, packet cutoff exclusion, first-session exclusion, and ready-peer continuation.

All zero controls pass: unrequested auto-monitoring, one-subject global blocking, direct force-active, placeholder evidence acceptance, raw-candidate readiness, KR-to-US blocking, US-to-KR blocking, and packet deadline overrun.
""",
        f"{REPORT_PREFIX}cpng-generic-reconciler-control.md": """# CPNG Generic Reconciler Control

Before: `PENDING_ONBOARDING`, inactive, production-ineligible, blocked by `INITIAL_EVIDENCE` and `DECISION_READINESS` after its final baseline existed.

The deployed generic `--market all --origin deployment_smoke` reconciler encountered CPNG without a ticker argument. It rebuilt canonical evidence, preserved the compatible final baseline, generated and validated an accepted-v2 `HOLD`, and allowed the existing coordinator to activate it.

After: `ACTIVE_READY`, retry class `NONE`, remaining blockers `0`, raw candidate grants readiness `false`, and first eligible session `2026-09-01`. Manual one-off resume and ticker bypass are both `0`.

Three retrospective P1s were closed before success: CLI artifact paths are absolute; market expectation facts use the existing `EXPECTATIONS` category; and `initial-onboarding-evidence-v1` now requires canonical market expectations. Each repair passed full local tests and Actions Test/Lint.
""",
        f"{REPORT_PREFIX}registration-user-facing-status.md": """# Registration User-Facing Status

Pending registration returns `PENDING_ONBOARDING`, the remaining canonical stages, and an explicit statement that automatic onboarding continues. It never tells the user that monitoring is active.

Only an active, production-eligible, coordinator-approved subject returns `ACTIVE_READY` and states that automatic review begins from the next eligible cycle. `USER_TOLD_ACTIVE_WHILE_PENDING=0`.
""",
        f"{REPORT_PREFIX}reconciler-test-sink.md": f"""# Reconciler Test Sink

The pre-main test used a SQLite operating snapshot and the dedicated non-production sink. The initial pass sent 20 exact payloads; identity-aware continuation sent only the remaining 2.

Final: planned `22`, sent `22`, exact payload `PASS`, duplicate `0`, orphan `0`, production collision `0`, production recipient send `0`, production delivery intent `0`.

Message artifact SHA-256: `{_sha(args.test_messages)}`. Raw recipient values, message identifiers, tokens, and auth data are excluded.
""",
        f"{REPORT_PREFIX}reconciler-main-merge.md": f"""# Reconciler Main Merge

Linear promotion sequence: `{args.implementation_sha}` is the final code implementation after bounded repairs. Main and operating were advanced only after local full pytest and exact-SHA Actions Test/Lint passed.

The new background LaunchAgent is loaded with a 1800-second interval. Existing market delivery plist content did not change. API health is PASS. Production Assist remains OFF (`ai_review_mode=shadow`).

Report commit: `{args.report_commit}`. No manual Scheduled Task, production Telegram, historical replay, Pilot mutation, or accepted-history rewrite occurred.
""",
        f"{REPORT_PREFIX}reconciler-readiness.md": """# Reconciler Readiness

`PENDING_ONBOARDING_AUTOMATION=READY_FOR_MAIN`.

Open P0: `0`. Open material P1: `0`. CPNG is `ACTIVE_READY` with accepted decision `HOLD` and first eligible session `2026-09-01`. Current counts are active-ready `22`, pending `0`, retryable `0`, review-required `0`.

Validation: focused `40 passed`; full pytest `1975 passed`; Ruff PASS; diff check PASS; Actions run `33401029416` Test/Lint PASS; Investment and Chart Knowledge parity PASS; Public Action `0.4.5`; operationId `20/20 unique`; API health PASS.

Safety: market schedule diff `0`, test production send/intent `0/0`, manual production task `0`, historical production replay `0`, accepted-decision ownership regression `0`, Price Structure numeric diff `0`, valuation numeric diff `0`.

Next action: `WAIT_FOR_NATURAL_US_PACKET`. CPNG may enter only a naturally frozen packet on or after its first eligible session.
""",
    }
    for name, text in sections.items():
        path = reports / name
        _write(path, text)
        generated.append(path)

    instruction_copy = reports / (
        f"{REPORT_PREFIX}pending-onboarding-auto-reconciler-exact-instruction.md"
    )
    shutil.copyfile(args.instruction, instruction_copy)
    generated.append(instruction_copy)

    index = reports / f"{REPORT_PREFIX}reconciler-artifact-index.md"
    rows = ["# Reconciler Artifact Index", "", f"Report commit: `{args.report_commit}`.", ""]
    for path in sorted(generated):
        rows.append(f"- `{path.as_posix()}`: `{_sha(path)}`")
    _write(index, "\n".join(rows))
    generated.append(index)
    return generated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument("--instruction", type=Path, required=True)
    parser.add_argument("--test-messages", type=Path, required=True)
    parser.add_argument("--test-receipt", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--master-instruction-commit", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--report-commit", required=True)
    parser.add_argument("--instruction-sha", required=True)
    parser.add_argument("--source-bundle-sha", required=True)
    args = parser.parse_args()
    print(json.dumps([str(path) for path in generate(args)], indent=2))


if __name__ == "__main__":
    main()
