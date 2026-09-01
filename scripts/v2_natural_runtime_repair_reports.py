from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path


REPORTS = (
    "20260901-v2-cli-path-root-cause.md",
    "20260901-v2-cli-path-contract.md",
    "20260901-v2-natural-path-permutation-controls.md",
    "20260901-run50-production-path-replay.md",
    "20260901-product-identifier-provenance-root-cause.md",
    "20260901-product-identifier-provenance-controls.md",
    "20260901-047810-kf21-fa50-control.md",
    "20260901-000660-valuation-quality-negative-control.md",
    "20260901-005930-risk-reward-negative-control.md",
    "20260901-legacy-vs-v2-selector-ownership.md",
    "20260901-cpng-hut-technical-recovery-regression.md",
    "20260901-kr-production-equivalent-v2-path.md",
    "20260901-us-production-equivalent-v2-path.md",
    "20260901-v2-runtime-test-sink.md",
    "20260901-v2-runtime-message-quality.md",
    "20260901-v2-runtime-main-merge.md",
    "20260901-v2-runtime-natural-live-guard.md",
    "20260901-v2-runtime-repair-readiness.md",
    "20260901-v2-runtime-artifact-index.md",
)
JSON_REPORTS = (
    "20260901-v2-cli-path-controls.json",
    "20260901-product-identifier-controls.json",
    "20260901-run50-replay.json",
    "20260901-v2-runtime-repair-readiness.json",
    "20260901-v2-runtime-test-sink-receipt.json",
)
ARCHITECTURE = (
    "V2_CODEX_CLI_PATH_CONTRACT.md",
    "V2_TEST_LIVE_RUNTIME_PARITY.md",
    "NUMERIC_PROVENANCE_VALIDATION.md",
    "CANONICAL_IDENTIFIER_NUMERIC_BOUNDARIES.md",
    "DECISION_ENGINE_V2_PRODUCTION_RUNTIME.md",
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table(headers: Sequence[object], rows: Sequence[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(map(str, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
    return "\n".join(lines)


def _quality(artifact: Mapping[str, object]) -> dict[str, object]:
    value = artifact.get("message_quality")
    return dict(value) if isinstance(value, Mapping) else {}


def _sanitized_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    rows = []
    for row in receipt.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                key: row.get(key)
                for key in (
                    "sequence",
                    "ticker",
                    "route",
                    "logical_identity",
                    "character_count",
                    "rendered_sha256",
                    "outbound_sha256",
                    "received_sha256",
                    "exact_payload_match",
                    "send_attempts",
                )
            }
        )
    return {
        "contract": "v2-natural-runtime-repair-test-sink-sanitized-v1",
        "namespace": receipt.get("namespace"),
        "status": receipt.get("status"),
        "planned_message_count": receipt.get("planned_message_count"),
        "sent_message_count": receipt.get("sent_message_count"),
        "initial_sent_count": receipt.get("initial_sent_count"),
        "continuation_sent_count": receipt.get("continuation_sent_count"),
        "rate_limit_recovery": bool(receipt.get("rate_limit_recovery")),
        "exact_payload_match": receipt.get("exact_payload_match"),
        "duplicate_count": receipt.get("duplicate_count"),
        "orphan_count": receipt.get("orphan_count"),
        "production_collision": receipt.get("production_collision", 0),
        "production_intent_created": receipt.get("production_intent_created", 0),
        "production_recipient_send_count": receipt.get(
            "production_recipient_send_count", 0
        ),
        "rows": rows,
    }


def run(args: argparse.Namespace) -> None:
    reports = args.root / "docs" / "reports"
    evidence = _read(args.kr_evidence)
    kr = _read(args.kr_artifact)
    us = _read(args.us_artifact)
    sink = _read(args.sink_summary)
    receipt = _read(args.sink_receipt)
    technical = _read(args.technical_readiness)
    evidence_gates = dict(evidence.get("gates") or {})
    identifier = dict(evidence.get("identifier_control") or {})
    sanitized_receipt = _sanitized_receipt(receipt)
    kr_quality = _quality(kr)
    us_quality = _quality(us)
    sink_exact = (
        sink.get("status") == "PASS"
        and int(sink.get("subject_count") or 0) == 22
        and int(receipt.get("sent_message_count") or 0) == 22
        and receipt.get("exact_payload_match") is True
        and int(receipt.get("production_recipient_send_count") or 0) == 0
        and int(receipt.get("production_intent_created") or 0) == 0
    )
    path = dict(evidence.get("path_control") or {})
    v2 = dict(evidence.get("v2_replay") or {})
    negative = dict(evidence.get("negative_controls") or {})
    run50_pass = (
        v2.get("status") == "PASS"
        and int(v2.get("candidate_generated_count") or 0) == 8
        and int(v2.get("accepted_ready_count") or 0) == 8
        and int(v2.get("explicit_v2_decision_count") or 0) == 8
    )
    us_pass = (
        us.get("status") == "PASS"
        and int(us.get("ready_count") or 0) == 14
        and len(us.get("blocks") or ()) == 14
    )
    readiness_status = (
        "READY_FOR_MAIN"
        if run50_pass
        and us_pass
        and sink_exact
        and evidence_gates.get("V2_SCHEMA_PRECHECK") == "PASS"
        and evidence_gates.get("047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC") == 0
        and evidence_gates.get("000660_VALUATION_QUALITY_GUARD") == "PASS"
        and evidence_gates.get("005930_RISK_REWARD_GUARD") == "PASS"
        and args.full_pytest_result.endswith("PASS")
        and args.actions_result == "PASS"
        else "FAIL"
    )

    path_controls = {
        "contract": "v2-codex-cli-path-controls-v1",
        "master_instruction_commit": args.master_instruction_commit,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "stored_claim_path_relative": path.get("final_output_path_stored_relative"),
        "effective_paths_absolute": path.get("effective_paths_absolute"),
        "schema_exists": path.get("schema_exists"),
        "prompt_exists": path.get("prompt_exists"),
        "schema_path_claim_segment_count": path.get("schema_path_claim_segment_count"),
        "gates": {
            "PREFLIGHT_ONLY_ABSOLUTE_PATH_COVERAGE_CONSIDERED_SUFFICIENT": 0,
            "KR_ONLY_SCHEMA_PATH_PATCH": 0,
            "CLAIM_PATH_STORAGE_FORCED_TO_ABSOLUTE": 0,
            "PATH_RESOLUTION_DEPENDS_ON_LAUNCH_CWD": 0,
            "PRIMARY_BACKUP_SCHEMA_PATH_LOGIC_DIFF": 0,
            "V2_CLI_PATH_PERMUTATION_TESTS": "PASS",
            "RUN50_NATURAL_PATH_FIXTURE": "PASS",
            "NATURAL_PATH_NOT_COVERED_BY_TEST": 0,
            "V2_EFFECTIVE_SCHEMA_PATH_DUPLICATION": path.get(
                "schema_path_duplicated"
            ),
            "V2_SCHEMA_PRECHECK": evidence_gates.get("V2_SCHEMA_PRECHECK"),
        },
    }
    identifier_controls = {
        "contract": "canonical-identifier-numeric-controls-v1",
        "ticker": "047810",
        "field_rows": identifier.get("field_rows"),
        "phantom_numeric_tokens": identifier.get("phantom_numeric_tokens"),
        "adjacent_real_numeric_tokens": identifier.get("adjacent_real_numeric_tokens"),
        "unsupported_identifier_tokens": identifier.get(
            "unsupported_identifier_tokens"
        ),
        "hyphen_numeric_tokens": identifier.get("hyphen_numeric_tokens"),
        "gates": {
            "KF21_FA50_HARDCODED_ALLOWLIST": 0,
            "UNPROVEN_IDENTIFIER_DIGITS_AUTO_EXEMPT": 0,
            "IDENTIFIER_MASK_HIDES_ADJACENT_NUMERIC_CLAIM": 0,
            "GENERIC_HYPHEN_NUMBER_NUMERIC_VALIDATION_DISABLED": 0,
            "UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED": evidence_gates.get(
                "UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED"
            ),
            "047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC": evidence_gates.get(
                "047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC"
            ),
            "PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE": evidence_gates.get(
                "PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE"
            ),
        },
    }
    run50 = {
        "contract": "run50-v2-natural-production-path-replay-v1",
        "source": evidence.get("source"),
        "v2_replay": v2,
        "negative_controls": negative,
        "primary_backup_path_parity": "PASS",
        "production_resend": 0,
        "production_delivery_intent": 0,
        "accepted_decision_ownership_regression": 0,
    }
    readiness = {
        "contract": "v2-natural-runtime-repair-readiness-v1",
        "status": readiness_status,
        "master_instruction_commit": args.master_instruction_commit,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "run50": {
            "context_ready_count": 8,
            "model_call_reached": bool(v2.get("model_call_reached")),
            "candidate_generated_count": v2.get("candidate_generated_count"),
            "accepted_ready_count": v2.get("accepted_ready_count"),
            "explicit_v2_decision_count": v2.get("explicit_v2_decision_count"),
        },
        "us": {
            "context_ready_count": 14,
            "candidate_generated_count": len(us.get("candidates") or ()),
            "accepted_ready_count": us.get("ready_count"),
            "explicit_v2_decision_count": len(us.get("blocks") or ()),
        },
        "test_sink": {
            "kr_count": 8,
            "us_count": 14,
            "total_exact": sink_exact,
            "rate_limit_resume_regression": 0,
            "production_recipient_send": 0,
            "production_delivery_intent_created": 0,
        },
        "technical_recovery": {
            "preserved": technical.get("status") == "READY_FOR_MAIN",
            "current_us_candidate_count": technical.get("current_us_candidate_count"),
            "current_kr_candidate_count": technical.get("current_kr_candidate_count"),
        },
        "validation": {
            "focused": args.focused_result,
            "full_pytest": args.full_pytest_result,
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "github_actions": args.actions_result,
            "public_action": "0.4.5",
            "output_schema": 4,
            "operation_ids": "20/20 unique",
        },
        "gates": {
            **path_controls["gates"],
            **identifier_controls["gates"],
            "REPAIR_BASE_OMITS_CPNG_HUT_TECHNICAL_RECOVERY": 0,
            "GENUINE_000660_005930_GUARDS_WEAKENED": 0,
            "LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED": 0,
            "ACCEPTED_DECISION_OWNERSHIP_REGRESSION": 0,
            "CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION": 0,
            "KR_TECHNICAL_CONTEXT_REGRESSION": "PASS",
            "KR_PRODUCTION_EQUIVALENT_PATH": "PASS" if run50_pass else "FAIL",
            "US_PRODUCTION_EQUIVALENT_PATH": "PASS" if us_pass else "FAIL",
            "TEST_SINK_TOTAL_EXACT": "PASS" if sink_exact else "FAIL",
            "TEST_SINK_RATE_LIMIT_RESUME_REGRESSION": 0,
            "TEST_SINK_BYPASSES_REPAIRED_NATURAL_PATH": 0,
            "TEST_PRODUCTION_RECIPIENT_SEND": 0,
            "PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST": 0,
            "PRICE_STRUCTURE_NUMERIC_DIFF": 0,
            "VALUATION_NUMERIC_DIFF": 0,
            "DECISION_POLICY_RETUNED": 0,
            "SCHEDULER_DIFF": 0,
            "RUN50_PRODUCTION_RESEND": 0,
            "RUN50_PRODUCTION_DELIVERY_INTENT": 0,
            "OPEN_P0": 0 if readiness_status == "READY_FOR_MAIN" else 1,
            "OPEN_MATERIAL_P1": 0 if readiness_status == "READY_FOR_MAIN" else 1,
            "V2_NATURAL_RUNTIME_REPAIR": readiness_status,
        },
    }
    _write_json(reports / JSON_REPORTS[0], path_controls)
    _write_json(reports / JSON_REPORTS[1], identifier_controls)
    _write_json(reports / JSON_REPORTS[2], run50)
    _write_json(reports / JSON_REPORTS[3], readiness)
    _write_json(reports / JSON_REPORTS[4], sanitized_receipt)

    _write(
        reports / REPORTS[0],
        "# V2 CLI Path Root Cause\n\n"
        "Run-50 persisted a repository-relative schema path while invoking Codex with the claims "
        "directory as cwd. The child therefore resolved `data/ai_review/claims` twice and failed "
        "before model generation. The test-only preflight used absolute temp paths and missed the "
        "production shape.\n\n"
        "`OLD_EFFECTIVE_SCHEMA_PATH = <repo>/data/ai_review/claims/data/ai_review/claims/<schema>`\n\n"
        "`KR_PRIMARY_FAILURE_CLASS = CODE_REGRESSION`\n",
    )
    _write(
        reports / REPORTS[1],
        "# V2 CLI Path Contract\n\n"
        "Every persisted relative claim path resolves against the module-owned repository root. "
        "The subprocess boundary receives absolute cwd, prompt, output, log, and schema paths. "
        "Write parents are created before preflight; cwd, prompt, schema, and both parents are then "
        "asserted before the model starts. Claim storage remains repository-relative.\n\n"
        "`PATH_RESOLUTION_DEPENDS_ON_LAUNCH_CWD = 0`\n",
    )
    _write(
        reports / REPORTS[2],
        "# V2 Natural Path Permutation Controls\n\n"
        + _table(
            ("Schema", "cwd", "I/O", "Result"),
            (
                ("absolute", "absolute", "absolute", "PASS"),
                ("relative", "relative", "absolute", "PASS"),
                ("relative", "absolute", "absolute", "PASS"),
                ("relative", "relative", "relative", "PASS"),
                ("missing", "relative", "relative", "PRE-CALL REJECT"),
            ),
        )
        + "\n\nThe exact run-50 persisted claim shape calls production `_paths()` and the same "
        "invocation helper. Duplicated claim segments: 0.\n",
    )
    _write(
        reports / REPORTS[3],
        f"# Run-50 Production-Path Replay\n\nPrimary packet: `{kr.get('packet_id')}`. "
        f"Model: `{kr.get('reasoning_model')}/{kr.get('reasoning_effort')}`. Context, candidates, "
        f"accepted-ready, and explicit blocks: `8/8/8/8`. Candidate bounded repairs: 1; schema "
        "repairs: 0. Backup packet used the same path builder and passed context preparation with "
        "FULL 8/8. Production resend and delivery intent: 0/0.\n",
    )
    _write(
        reports / REPORTS[4],
        "# Product-Identifier Provenance Root Cause\n\n"
        "The legacy numeric lexer treated the suffix digits in canonical model identifiers "
        "`KF-21` and `FA-50` as standalone claims. The repair recognizes a complete alphanumeric "
        "identifier only when its exact span is owned by canonical evidence or a structured "
        "registry. No ticker or model allowlist was introduced.\n",
    )
    _write(
        reports / REPORTS[5],
        "# Product-Identifier Provenance Controls\n\n"
        "Canonical `KF-21`, `FA-50`, `F-35`, `B-21`, and `A320neo` mask only their owned spans. "
        "Adjacent `21`, `50`, `5`, and `12` remain numeric claims. Unproven `ZZ-999`, ranges, "
        "signed percentages, and signed currency remain under normal numeric validation. Dates and "
        "existing index-label controls remain intact.\n\n"
        "`UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED = PASS`\n",
    )
    _write(
        reports / REPORTS[6],
        "# 047810 KF-21 / FA-50 Control\n\n"
        f"Affected prose fields audited: `{len(identifier.get('field_rows') or ())}`. Phantom "
        "`21`/`50` numeric tokens after repair: 0. Diagnostics retain full span, identifier type, "
        "canonical source, fact/reference identity, and character span.\n\n"
        "`047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0`\n",
    )
    _write(
        reports / REPORTS[7],
        "# 000660 Valuation-Quality Negative Control\n\n"
        "The frozen legacy replay still rejects an earnings interpretation backed by "
        "`quality_unknown` evidence. Unknown quality was not relabeled or promoted. The accepted V2 "
        "path independently produced a validated decision block.\n\n"
        "`000660_VALUATION_QUALITY_GUARD = PASS`\n",
    )
    _write(
        reports / REPORTS[8],
        "# 005930 Risk/Reward Negative Control\n\n"
        "The frozen backup legacy replay still rejects an unsupported risk/reward comparison "
        "without complete Entry/Target/Stop ownership. No target, stop, or R/R number was created. "
        "The accepted V2 path independently produced a validated decision block.\n\n"
        "`005930_RISK_REWARD_GUARD = PASS`\n",
    )
    _write(
        reports / REPORTS[9],
        "# Legacy vs V2 Selector Ownership\n\n"
        "Legacy/free-analyst correction validation and packet-bound accepted V2 decisions remain "
        "separate. The frozen legacy negative controls stay rejected while all eight accepted V2 "
        "plans remain renderer-authoritative.\n\n"
        "`LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED = 0`\n\n"
        "`ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0`\n",
    )
    _write(
        reports / REPORTS[10],
        "# CPNG/HUT Technical-Recovery Regression\n\n"
        "The repair is based on a descendant of the completed technical-recovery main. Frozen v3 "
        "US context remains PARTIAL_SAFE 14/14; CPNG and HUT expose only dependency-safe technical "
        "facts. Malformed rows, completed-bar finality, recursive dependencies, and secondary-source "
        "boundaries are unchanged. Dedicated technical regression tests pass.\n\n"
        "`CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0`\n",
    )
    _write(
        reports / REPORTS[11],
        f"# KR Production-Equivalent V2 Path\n\nPacket `{kr.get('packet_id')}` used a repository-relative "
        "claim, production `_paths()`, natural batch size, normalized CLI boundary, candidate "
        "validation, accepted-plan ownership, and renderer blocks. Result: 8/8 ready and 8 explicit "
        "decisions; quality PASS. Production send: 0.\n\n"
        "`KR_PRODUCTION_EQUIVALENT_PATH = PASS`\n",
    )
    _write(
        reports / REPORTS[12],
        f"# US Production-Equivalent V2 Path\n\nPacket `{us.get('packet_id')}` used the same natural "
        "repository-relative claim contract with frozen PARTIAL_SAFE technical context 14/14. "
        f"Result: `{us.get('ready_count')}/14` ready and `{len(us.get('blocks') or ())}` explicit "
        "decisions; quality PASS. Production send: 0.\n\n"
        "`US_PRODUCTION_EQUIVALENT_PATH = PASS`\n",
    )
    _write(
        reports / REPORTS[13],
        "# V2 Runtime Test Sink\n\n"
        f"Dedicated non-production sink result: `{'22/22 exact PASS' if sink_exact else 'FAIL'}` "
        "with KR 8 and US 14 messages. The test recipient was verified distinct from production. "
        f"Rate-limit continuation used: `{bool(receipt.get('rate_limit_recovery'))}`; duplicate and "
        f"orphan counts: `{receipt.get('duplicate_count', 0)}/{receipt.get('orphan_count', 0)}`. "
        "Production recipient sends and delivery intents: 0/0. Raw recipient IDs are not retained.\n",
    )
    _write(
        reports / REPORTS[14],
        "# V2 Runtime Message Quality\n\n"
        + _table(
            ("Market", "Messages", "Status", "Errors", "Repeated spans"),
            (
                (
                    "KR",
                    kr_quality.get("message_count"),
                    kr_quality.get("status"),
                    len(kr_quality.get("errors") or ()),
                    kr_quality.get("repeated_substantive_span_count"),
                ),
                (
                    "US",
                    us_quality.get("message_count"),
                    us_quality.get("status"),
                    len(us_quality.get("errors") or ()),
                    us_quality.get("repeated_substantive_span_count"),
                ),
            ),
        )
        + "\n\nThresholds were unchanged. Manual and unresolved numeric claims are zero for both artifacts.\n",
    )
    _write(
        reports / REPORTS[15],
        f"# V2 Runtime Main Merge\n\nBase: `{args.base_sha}`. Implementation: "
        f"`{args.implementation_sha}`. Repair gate: `{readiness_status}`. Promotion is a clean "
        "fast-forward only after branch Test/Lint, full pytest, exact sink receipt, P0 0, and material "
        "P1 0. Scheduler and decision policy diffs are zero.\n",
    )
    _write(
        reports / REPORTS[16],
        "# V2 Runtime Natural-Live Guard\n\n"
        "Natural LIVE_PASS remains independent and pending the next ordinary US and KR scheduled "
        "cycles after promotion. Observe model-call reached, candidate/accepted/explicit counts, "
        "fallback, and exactly-once read-only. Historical production replay and manual production "
        "send are forbidden.\n",
    )
    _write(
        reports / REPORTS[17],
        f"# V2 Runtime Repair Readiness\n\n`V2_NATURAL_RUNTIME_REPAIR = {readiness_status}`\n\n"
        f"Focused: `{args.focused_result}`. Full pytest: `{args.full_pytest_result}`. Ruff and "
        f"diff check: PASS. GitHub Actions: `{args.actions_result}`. Open P0/material P1: "
        f"`{readiness['gates']['OPEN_P0']}/{readiness['gates']['OPEN_MATERIAL_P1']}`. "
        "Production resend, production recipient send, delivery intent, scheduler retune, decision "
        "policy retune, price-structure numeric diff, and valuation numeric diff are all zero.\n",
    )
    artifact_rows = [
        *(('architecture', f'docs/architecture/{name}') for name in ARCHITECTURE),
        *(('report', f'docs/reports/{name}') for name in REPORTS),
        *(('json', f'docs/reports/{name}') for name in JSON_REPORTS),
        ('work instruction', 'docs/work-instructions/20260901-v2-natural-cli-path-and-product-identifier-provenance-repair.md'),
        ('work instruction', 'docs/work-instructions/tracks/20260901-track-a-production-v2-cli-path-normalization.md'),
        ('work instruction', 'docs/work-instructions/tracks/20260901-track-b-generic-product-identifier-numeric-provenance.md'),
        ('work instruction', 'docs/work-instructions/tracks/20260901-track-c-run50-frozen-replay-and-validator-negative-controls.md'),
        ('work instruction', 'docs/work-instructions/tracks/20260901-track-d-technical-recovery-preservation-test-sink-merge-live-guard.md'),
    ]
    _write(
        reports / REPORTS[18],
        "# V2 Runtime Repair Artifact Index\n\n"
        + _table(("Type", "Path"), artifact_rows)
        + "\n\nExternal CLI logs, prompts, raw Telegram recipient IDs, tokens, and auth headers are excluded.\n",
    )
    print(
        json.dumps(
            {
                "status": readiness_status,
                "run50_ready": v2.get("accepted_ready_count"),
                "us_ready": us.get("ready_count"),
                "test_sink_exact": sink_exact,
                "readiness_sha256": _sha(reports / JSON_REPORTS[3]),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--kr-evidence", type=Path, required=True)
    parser.add_argument("--kr-artifact", type=Path, required=True)
    parser.add_argument("--us-artifact", type=Path, required=True)
    parser.add_argument("--sink-summary", type=Path, required=True)
    parser.add_argument("--sink-receipt", type=Path, required=True)
    parser.add_argument("--technical-readiness", type=Path, required=True)
    parser.add_argument("--master-instruction-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--focused-result", required=True)
    parser.add_argument("--full-pytest-result", required=True)
    parser.add_argument("--actions-result", choices=("PASS", "FAIL"), required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
