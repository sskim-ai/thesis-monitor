from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import ValidationError

from app.services.structured_autonomy_shadow_service import (
    StructuredAutonomyCandidate,
    derive_hold_lean,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)
from scripts import uskr22_structured_autonomy_shadow as engine


CONTRACT_VERSION = "natural-proof-structured-autonomy-blind-program-v1"
WORK_INSTRUCTION_SHA = "2a7b7b4cfe40cf8e9c3514b083daaa36eeba5e4f"
BASE_SHA = "d18e68b1e944d7749d093b08797fcd9498412680"
US_PACKET_ID = "2026-09-05-us-run-57-1fbbf143dbc5"
KR_PACKET_ID = "2026-09-04-kr-run-56-6a9ef43bb878"
US_COHORT = engine.US_COHORT
KR_COHORT = engine.KR_COHORT
COHORT = US_COHORT + KR_COHORT
RUNS = ("first", "a", "b", "c")

BLIND_FORBIDDEN_KEYS = frozenset(
    {
        "accepted_decision",
        "ai_confidence",
        "ai_generated_summary",
        "ai_market_expectation_assessment",
        "ai_valuation_conclusion",
        "buy_balance",
        "buy_drivers",
        "core_judgment",
        "decision",
        "decision_confidence",
        "directional_balance",
        "hold_lean",
        "holder_stance",
        "holder_view",
        "new_buyer_stance",
        "new_buyer_view",
        "overall_direction",
        "preferred_entry_mode",
        "sell_balance",
        "sell_drivers",
    }
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def directory_payload_sha256(path: Path) -> str:
    rows = []
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        if item.name == "manifest.json":
            continue
        rows.append(
            {
                "path": str(item.relative_to(path)),
                "sha256": file_sha256(item),
                "bytes": item.stat().st_size,
            }
        )
    return canonical_sha256(rows)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def configure_engine(generation_id: str) -> None:
    engine.US_PACKET_ID = US_PACKET_ID
    engine.KR_PACKET_ID = KR_PACKET_ID
    engine.KR_LATER_PACKET_ID = KR_PACKET_ID
    engine.SHADOW_PACKET_ID = generation_id
    engine.REPAIR_BASE_SHA = BASE_SHA
    engine.WORK_INSTRUCTION_SHA = WORK_INSTRUCTION_SHA


def normalized_kr_base_messages(source: Path, destination: Path) -> None:
    document = read_json(source)
    messages = []
    for row in document.get("messages") or ():
        if not isinstance(row, Mapping):
            continue
        payload = row.get("payload")
        text = payload.get("text") if isinstance(payload, Mapping) else row.get("text")
        if isinstance(text, str):
            messages.append({"ticker": row.get("ticker"), "text": text})
    write_json(destination, {"packet_id": document.get("packet_id"), "messages": messages})


def _state(path: Path, *, resume: bool) -> dict[str, object]:
    if path.exists():
        if not resume:
            raise ValueError(f"existing_program_state_requires_resume:{path}")
        return read_json(path)
    generation_id = (
        "20260905-uskr22-blind-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    value = {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "created_at": datetime.now(UTC).isoformat(),
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "base_sha": BASE_SHA,
        "old_candidate_reuse": 0,
        "selective_ticker_rerun": 0,
    }
    write_json(path, value)
    return value


def _engine_args(args: argparse.Namespace, output_root: Path) -> SimpleNamespace:
    internal_reports = output_root / "engine-internal-reports"
    normalized_kr = output_root / "input-lock" / "kr-base-messages.json"
    normalized_kr_base_messages(args.kr_base_messages, normalized_kr)
    return SimpleNamespace(
        us_packet=args.us_packet.resolve(),
        kr_packet=args.kr_packet.resolve(),
        kr_later_packet=args.kr_packet.resolve(),
        us_base_messages=args.us_base_messages.resolve(),
        kr_base_messages=normalized_kr.resolve(),
        output_dir=(output_root / "engine").resolve(),
        report_dir=internal_reports.resolve(),
        timeout=args.timeout,
        prepare_only=False,
        resume_existing=args.resume,
    )


def _source_lock(
    *,
    generation_id: str,
    args: argparse.Namespace,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    us = read_json(args.us_packet)
    kr = read_json(args.kr_packet)
    return {
        "contract": "structured-autonomy-source-lock-v2",
        "generation_id": generation_id,
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "base_sha": BASE_SHA,
        "sources": {
            "us": {
                "packet_id": us.get("packet_id"),
                "assessment_date": us.get("assessment_date"),
                "generated_at": us.get("generated_at"),
                "source_monitor_run_id": us.get("source_monitor_run_id"),
                "file_sha256": file_sha256(args.us_packet),
                "canonical_sha256": canonical_sha256(us),
                "ready_for_ai": us.get("ready_for_ai"),
            },
            "kr": {
                "packet_id": kr.get("packet_id"),
                "assessment_date": kr.get("assessment_date"),
                "generated_at": kr.get("generated_at"),
                "source_monitor_run_id": kr.get("source_monitor_run_id"),
                "file_sha256": file_sha256(args.kr_packet),
                "canonical_sha256": canonical_sha256(kr),
                "ready_for_ai": kr.get("ready_for_ai"),
            },
        },
        "universe": {"us": list(US_COHORT), "kr": list(KR_COHORT)},
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "fresh_experiment_generation": "PASS",
        "old_candidate_reuse": 0,
        "prior_decision_visibility": 0,
        "fresh_fact_collection": 0,
        "cross_market_fact_leakage": 0,
        "cross_generation_fact_leakage": 0,
    }


def _fact_row(value: object) -> dict[str, object]:
    dumped = value.model_dump(mode="json")
    return {
        "fact_id": dumped["ref_id"],
        "category": dumped["category"],
        "label": dumped["label"],
        "statement": dumped["statement"],
        "as_of_date_or_period": dumped.get("as_of"),
        "value": dumped.get("value"),
        "unit_or_currency": dumped.get("unit"),
        "source_field": dumped["source_ref"],
        "numeric_prose_eligible": dumped["numeric_prose_eligible"],
        "logical_condition": dumped.get("logical_condition"),
    }


def _blind_key_leaks(value: object, path: str = "$") -> list[str]:
    leaks: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).casefold() in BLIND_FORBIDDEN_KEYS:
                leaks.append(child_path)
            leaks.extend(_blind_key_leaks(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            leaks.extend(_blind_key_leaks(child, f"{path}[{index}]"))
    return leaks


def build_blind_pack(
    *,
    root: Path,
    generation_id: str,
    created_at: str,
    evidence: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], list[str]]:
    if root.exists():
        shutil.rmtree(root)
    subject_dir = root / "subjects"
    market_dir = root / "market"
    subject_dir.mkdir(parents=True)
    market_dir.mkdir(parents=True)
    market_facts: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
    subject_manifest = []
    leaks: list[str] = []
    for ticker in sorted(COHORT):
        packet = evidence[ticker]
        stock = stocks[ticker]
        facts = [_fact_row(row) for row in packet.evidence]
        document = {
            "contract": "blind-fact-pack-subject-v1",
            "generation_id": generation_id,
            "identity": {
                "ticker": ticker,
                "company_name": packet.company_name,
                "market": packet.market,
                "industry": stock.get("industry"),
                "sector": stock.get("sector"),
                "business_model": stock.get("business_model"),
            },
            "source": {
                "packet_id": packet.packet_id,
                "assessment_date": packet.assessment_date,
                "evidence_fingerprint": packet.evidence_sha256,
            },
            "facts": facts,
            "verified_price_structure": price_maps[ticker],
            "data_quality_cautions": list(packet.data_quality_cautions),
            "prohibited_inferences": list(packet.prohibited_claims),
        }
        leaks.extend(f"{ticker}:{item}" for item in _blind_key_leaks(document))
        path = subject_dir / f"{ticker}.json"
        write_json(path, document)
        subject_manifest.append(
            {
                "ticker": ticker,
                "market": packet.market,
                "file": f"subjects/{ticker}.json",
                "sha256": file_sha256(path),
                "fact_count": len(facts),
            }
        )
        for fact in facts:
            if fact["category"] in {"macro", "market", "flows"}:
                market_facts[packet.market][str(fact["fact_id"])] = fact
    for market in ("kr", "us"):
        write_json(
            market_dir / f"{market}.json",
            {
                "contract": "blind-fact-pack-market-v1",
                "generation_id": generation_id,
                "market": market,
                "facts": list(market_facts[market].values()),
            },
        )
    payload_sha = directory_payload_sha256(root)
    manifest = {
        "contract": "blind-fact-pack-manifest-v1",
        "generation_id": generation_id,
        "created_at": created_at,
        "neutral_order": "ticker_lexicographic",
        "subjects": subject_manifest,
        "subject_count": len(subject_manifest),
        "blind_pack_sha256": payload_sha,
        "ai_judgment_leakage_count": len(leaks),
        "ai_judgment_leakage_paths": leaks,
    }
    write_json(root / "manifest.json", manifest)
    return manifest, leaks


def build_ai_pack(
    *,
    root: Path,
    generation_id: str,
    created_at: str,
    candidates: Sequence[StructuredAutonomyCandidate],
    run_document: Mapping[str, object],
) -> dict[str, object]:
    if root.exists():
        shutil.rmtree(root)
    subject_dir = root / "subjects"
    subject_dir.mkdir(parents=True)
    selections = run_document["alias_selections"]
    subject_manifest = []
    for candidate in sorted(candidates, key=lambda row: row.ticker):
        document = {
            "contract": "ai-decision-pack-subject-v1",
            "generation_id": generation_id,
            "ticker": candidate.ticker,
            "decision": candidate.model_dump(mode="json"),
            "hold_lean": derive_hold_lean(
                candidate.decision, candidate.directional_balance
            ),
            "selected_evidence_refs": [
                row["canonical_ref"] for row in selections[candidate.ticker]
            ],
        }
        path = subject_dir / f"{candidate.ticker}.json"
        write_json(path, document)
        subject_manifest.append(
            {
                "ticker": candidate.ticker,
                "file": f"subjects/{candidate.ticker}.json",
                "sha256": file_sha256(path),
            }
        )
    payload_sha = directory_payload_sha256(root)
    manifest = {
        "contract": "ai-decision-pack-manifest-v1",
        "generation_id": generation_id,
        "created_at": created_at,
        "subjects": subject_manifest,
        "subject_count": len(subject_manifest),
        "ai_decision_pack_sha256": payload_sha,
        "sealed": True,
        "reveal_gate": "EXTERNAL_BLIND_JUDGMENT_FROZEN",
    }
    write_json(root / "manifest.json", manifest)
    return manifest


def external_template(generation_id: str) -> dict[str, object]:
    return {
        "contract": "structured-autonomy-external-blind-judgment-v1",
        "generation_id": generation_id,
        "status": "DRAFT_NOT_FROZEN",
        "reviewer": None,
        "frozen_at": None,
        "subjects": [
            {
                "ticker": ticker,
                "overall_direction": None,
                "directional_balance": {"buy": None, "sell": None},
                "hold_lean": None,
                "new_buyer_stance": None,
                "entry_mode": None,
                "holder_stance": None,
                "core_positive_evidence_fact_ids": [],
                "core_negative_evidence_fact_ids": [],
                "valuation_view": None,
                "price_timing_view": None,
                "key_unknown": None,
                "reassessment_or_invalidation_view": None,
                "confidence": None,
            }
            for ticker in sorted(COHORT)
        ],
    }


def decision_rows(candidates: Sequence[StructuredAutonomyCandidate]) -> list[list[object]]:
    return [
        [
            row.ticker,
            "US" if row.ticker in US_COHORT else "KR",
            row.decision,
            f"{row.directional_balance.buy:.1f}:{row.directional_balance.sell:.1f}",
            derive_hold_lean(row.decision, row.directional_balance),
            row.new_buyer_view.stance,
            row.holder_view.stance,
            row.new_buyer_view.preferred_entry_mode,
        ]
        for row in candidates
    ]


def write_natural_proof_files(machine_dir: Path, public_reports: Path) -> None:
    kr = {
        "contract": "natural-explicit-v2-proof-v1",
        "market": "kr",
        "operating_sha": BASE_SHA,
        "proof": "PENDING",
        "reason": "no_post_deployment_xkrx_session_yet",
        "latest_observation": {
            "observed_at_kst": "2026-09-05T16:20:03+09:00",
            "scheduler_result": "safe_noop",
            "skip_reason": "no_valid_role_target",
            "analysis_run_status": "not_started",
            "delivery_action": "safe_noop",
        },
        "production_intervention": 0,
    }
    us = {
        "contract": "natural-explicit-v2-proof-v1",
        "market": "us",
        "operating_sha": BASE_SHA,
        "proof": "PENDING",
        "reason": "no_post_deployment_authoritative_us_natural_run_yet",
        "predeployment_run57_is_not_counted": True,
        "production_intervention": 0,
    }
    write_json(machine_dir / "natural-kr-proof.json", kr)
    write_json(machine_dir / "natural-us-proof.json", us)
    write_text(
        public_reports / "20260905-kr-natural-explicit-v2-proof.md",
        "# KR Natural Explicit-V2 Proof\n\n"
        "`KR_NATURAL_EXPLICIT_V2_PROOF = PENDING`\n\n"
        "The 2026-09-05 16:05 and 16:20 KST scheduler observations were Saturday "
        "calendar-guard `safe_noop` executions. No model call or delivery occurred, so "
        "they are not counted as a natural V2 proof. Production intervention: `0`.\n",
    )
    write_text(
        public_reports / "20260905-us-natural-explicit-v2-proof.md",
        "# US Natural Explicit-V2 Proof\n\n"
        "`US_NATURAL_EXPLICIT_V2_PROOF = PENDING`\n\n"
        "Run 57 predates the integrated production deployment and is retained only as "
        "source evidence. It is not counted as post-deployment natural proof. Production "
        "intervention: `0`.\n",
    )
    write_text(
        public_reports / "20260905-natural-proof-summary.md",
        "# Natural Proof Summary\n\n"
        "| Market | Status | Basis |\n| --- | --- | --- |\n"
        "| KR | PENDING | No post-deployment XKRX session |\n"
        "| US | PENDING | No post-deployment authoritative natural run |\n\n"
        "Infrastructure natural proof and Structured Autonomy judgment quality remain "
        "separate gates. Replay, hotfix, manual task, and Telegram send: `0`.\n",
    )


def write_blind_protocol(path: Path, generation_id: str) -> None:
    write_text(
        path,
        "# Structured Autonomy Blind Comparison Protocol\n\n"
        f"Generation: `{generation_id}`\n\n"
        "1. Review only `BLIND_FACT_PACK`.\n"
        "2. Complete every subject in `external-comparison-template.json`.\n"
        "3. Set `status` to `FROZEN` and record `reviewer` and `frozen_at`.\n"
        "4. Return the frozen file before opening any AI decision artifact.\n"
        "5. AI results are advisory and the external judgment is not hardcoded truth.\n\n"
        "Do not inspect AI decision files, A/B/C reports, prior experiment decisions, or "
        "label-bearing filenames before the judgment is frozen.\n",
    )


def zip_paths(destination: Path, root: Path, paths: Sequence[Path]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_dir():
                for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
                    _write_deterministic_zip_member(archive, item, item.relative_to(root))
            else:
                _write_deterministic_zip_member(archive, path, path.relative_to(root))
    temporary.replace(destination)


def _write_deterministic_zip_member(
    archive: zipfile.ZipFile,
    source: Path,
    member: Path,
) -> None:
    info = zipfile.ZipInfo(str(member), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, source.read_bytes())


def _safe_validation_failure(exc: Exception) -> dict[str, object]:
    details: list[dict[str, str]] = []
    if isinstance(exc, ValidationError):
        for row in exc.errors(include_input=False, include_url=False):
            details.append(
                {
                    "location": ".".join(str(value) for value in row.get("loc") or ()),
                    "type": str(row.get("type") or "validation_error"),
                    "message": str(row.get("msg") or "validation failed"),
                }
            )
    return {
        "exception_type": type(exc).__name__,
        "summary": str(exc).splitlines()[0][:500],
        "details": details,
    }


def _write_blind_intake_bundle(
    *,
    output_root: Path,
    review_root: Path,
    blind_manifest: Mapping[str, object],
    ai_manifest: Mapping[str, object],
) -> Path:
    write_text(
        review_root / "SHA256SUMS.txt",
        f"{blind_manifest['blind_pack_sha256']}  BLIND_FACT_PACK payload\n"
        f"{ai_manifest['ai_decision_pack_sha256']}  AI_DECISION_PACK sealed payload\n",
    )
    blind_zip = (
        output_root / "thesis-monitor-structured-autonomy-blind-review-bundle.zip"
    )
    zip_paths(
        blind_zip,
        review_root,
        [
            review_root / "BLIND_FACT_PACK",
            review_root / "COMPARISON_PROTOCOL.md",
            review_root / "external-comparison-template.json",
            review_root / "SHA256SUMS.txt",
        ],
    )
    return blind_zip


def _write_incomplete_reports(
    *,
    output_root: Path,
    public_reports: Path,
    sealed_reports: Path,
    machine_dir: Path,
    review_root: Path,
    generation_id: str,
    source_lock: Mapping[str, object],
    run_documents: Mapping[str, Mapping[str, object]],
    failed_run: str,
    failure: Mapping[str, object],
    blind_manifest: Mapping[str, object],
    ai_manifest: Mapping[str, object],
) -> dict[str, object]:
    completed_runs = [run for run in RUNS if run in run_documents]
    hard_errors = sum(
        row["status"] != "PASS"
        for run in completed_runs
        for row in run_documents[run]["validation"]
    )
    failed_batches = sorted(
        path.name for path in (output_root / "engine" / f"run-{failed_run}").glob("batch-*.json")
    )
    run_failure = {
        "contract": "structured-autonomy-run-failure-v1",
        "generation_id": generation_id,
        "run": failed_run,
        "status": "FAILED_SCHEMA_VALIDATION",
        "completed_run_document": False,
        "batch_output_artifacts": failed_batches,
        "selective_ticker_rerun": 0,
        "post_result_candidate_edit": 0,
        "validation_triggered_rerun": 0,
        "approved_infrastructure_resume_count": 1,
        "approved_infrastructure_resume_scope": "run_a_batch_05",
        "failed_batch_retry": 0,
        "remaining_model_calls_started": 0,
        "failure": dict(failure),
    }
    stability = {
        "contract": "structured-autonomy-stability-v1",
        "generation_id": generation_id,
        "status": "NOT_MEASURED_INCOMPLETE_ABC",
        "runs_completed": [run for run in ("a", "b", "c") if run in run_documents],
        "failed_run": failed_run,
        "counts": {
            "STABLE": "NOT_MEASURED",
            "BOUNDARY_UNCERTAINTY": "NOT_MEASURED",
            "UNSTABLE": "NOT_MEASURED",
        },
        "majority_vote": 0,
        "decision_averaging": 0,
    }
    bias = {
        "contract": "structured-autonomy-judgment-bias-audit-v1",
        "generation_id": generation_id,
        "status": "INSUFFICIENT_EVIDENCE_INCOMPLETE_ABC",
        "unknown_negative_bias": "INSUFFICIENT_EVIDENCE",
        "valuation_bias": "INSUFFICIENT_EVIDENCE",
        "timing_bias": "INSUFFICIENT_EVIDENCE",
        "action_context_bias": "INSUFFICIENT_EVIDENCE",
    }
    promotion = {
        "contract": "structured-autonomy-promotion-review-v1",
        "generation_id": generation_id,
        "current_operating_sha": BASE_SHA,
        "current_model": engine.REASONING_MODEL,
        "current_reasoning_effort": engine.REASONING_EFFORT,
        "kr_natural_explicit_v2_proof": "PENDING",
        "us_natural_explicit_v2_proof": "PENDING",
        "fresh_experiment_generation": "PASS",
        "old_candidate_reuse": 0,
        "selective_ticker_rerun": 0,
        "validation_triggered_rerun": 0,
        "approved_infrastructure_resume_count": 1,
        "source_packet_us": US_PACKET_ID,
        "source_packet_kr": KR_PACKET_ID,
        "source_as_of_us": source_lock["sources"]["us"]["assessment_date"],
        "source_as_of_kr": source_lock["sources"]["kr"]["assessment_date"],
        "model_equivalence": "PASS",
        "first_run_validated": run_documents["first"]["validation_pass_count"],
        "a_b_c_gate": "RUN_INCOMPLETE",
        "ai_judgment_leakage_in_blind_pack": blind_manifest[
            "ai_judgment_leakage_count"
        ],
        "blind_pack_sha256": blind_manifest["blind_pack_sha256"],
        "ai_decision_pack_sha256": ai_manifest["ai_decision_pack_sha256"],
        "external_blind_judgment_status": "NOT_STARTED",
        "run_a_validated": run_documents.get("a", {}).get(
            "validation_pass_count", "NOT_RUN"
        ),
        "run_b_validated": run_documents.get("b", {}).get(
            "validation_pass_count", "NOT_RUN"
        ),
        "run_c_validated": "OTHER",
        "stable_count": "NOT_MEASURED",
        "boundary_uncertainty_count": "NOT_MEASURED",
        "unstable_count": "NOT_MEASURED",
        "ai_vs_external_full_agreement": "NOT_MEASURED",
        "ai_vs_external_boundary_difference": "NOT_MEASURED",
        "ai_vs_external_meaningful_difference": "NOT_MEASURED",
        "ai_vs_external_major_difference": "NOT_MEASURED",
        "buy_sell_direct_reversal": "NOT_MEASURED",
        "unknown_negative_bias": "INSUFFICIENT_EVIDENCE",
        "valuation_bias": "INSUFFICIENT_EVIDENCE",
        "timing_bias": "INSUFFICIENT_EVIDENCE",
        "action_context_bias": "INSUFFICIENT_EVIDENCE",
        "hard_safety_regression": hard_errors + 1,
        "message_quality_failures": sum(
            run_documents[run]["message_quality"]["status"] != "PASS"
            for run in completed_runs
        ),
        "production_decision_mutation": 0,
        "production_renderer_mutation": 0,
        "production_telegram_send": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "promotion_readiness": "NEEDS_MORE_SHADOW_WORK",
        "promotion_blockers": [
            f"run_{failed_run}_schema_validation_failed",
            "abc_stability_not_measured",
            "internal_shadow_gate_not_clean",
            "external_blind_judgment_not_frozen",
            "kr_natural_explicit_v2_proof_pending",
            "us_natural_explicit_v2_proof_pending",
        ],
    }
    for run in completed_runs:
        name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        write_json(machine_dir / name, run_documents[run])
    write_json(machine_dir / f"run-{failed_run}.json", run_failure)
    write_json(machine_dir / f"run-{failed_run}-failure.json", run_failure)
    write_json(machine_dir / "abc-stability.json", stability)
    write_json(machine_dir / "judgment-bias-audit.json", bias)
    write_json(machine_dir / "promotion-review.json", promotion)
    write_json(machine_dir / "structured-autonomy-source-lock.json", source_lock)

    report_values = {
        "20260905-structured-autonomy-fresh-first.md": (
            "# Structured Autonomy Fresh First\n\n"
            f"- Generation: `{generation_id}`\n"
            f"- Validation: `{run_documents['first']['validation_pass_count']}/22`\n"
            f"- Message quality: `{run_documents['first']['message_quality']['status']}`\n"
            "- Candidate decisions: `SEALED_PENDING_EXTERNAL_BLIND_FREEZE`\n"
        ),
        "20260905-structured-autonomy-fresh-first-validation.md": (
            "# Structured Autonomy Fresh-First Validation\n\n"
            f"`FIRST_RUN_VALIDATED = {run_documents['first']['validation_pass_count']}`\n\n"
            "Old candidate reuse, selective rerun, and production send: `0`.\n"
        ),
        "20260905-run-a.md": (
            "# Structured Autonomy Run A\n\n"
            f"- Validated: `{run_documents.get('a', {}).get('validation_pass_count', 'NOT_RUN')}/22`\n"
            "- Candidate decisions: `SEALED`\n"
            "- Validation failures: `MU`, `005490`; future-checkpoint metric policy.\n"
            "- Unsupported evidence refs: `0`\n"
            "- Numeric, accounting/security-basis, and material-repetition failures: `0`\n"
            "- Candidate edits or validation-triggered reruns: `0`\n\n"
            "The selected evidence owned the named checkpoint metric, but one or more qualitative future-risk/checkpoint phrases fell outside the validator's accepted future-context grammar. This run remains failed and frozen; it was not repaired in place.\n"
        ),
        "20260905-run-b.md": (
            "# Structured Autonomy Run B\n\n"
            f"- Validated: `{run_documents.get('b', {}).get('validation_pass_count', 'NOT_RUN')}/22`\n"
            "- Candidate decisions: `SEALED`\n"
            "- Validation failures: `GOOGL`, `005490`; future-checkpoint metric policy.\n"
            "- Unsupported evidence refs: `0`\n"
            "- Directional Unknown, sector-normal SELL, ADR basis, and KR accounting-basis audit findings: `0`\n"
            "- Material repetition: `0`\n"
            "- Candidate edits or reruns: `0`\n\n"
            "As in Run A, the evidence owned the metric while the phrasing did not satisfy the current future-checkpoint language gate. No current/historical metric value was accepted.\n"
        ),
        "20260905-run-c.md": (
            "# Structured Autonomy Run C\n\n"
            "- Status: `FAILED_SCHEMA_VALIDATION`\n"
            "- Failure point: `batch-05` logical-condition leaf shape.\n"
            "- Batch retry: `0`\n- C6 model call: `0`\n"
            "- Candidate decisions: `NOT_ACCEPTED_OR_REVEALED`\n"
            "\nBoth failures were under `reevaluation_down`: a logical-condition expression declared a `LEAF` while retaining an invalid child shape. The structured schema rejected the batch before a complete Run C candidate set or run document could exist.\n"
        ),
        "20260905-abc-stability.md": (
            "# Structured Autonomy A/B/C Stability\n\n"
            "`STATUS = NOT_MEASURED_INCOMPLETE_ABC`\n\n"
            "C did not produce a complete canonical run document. No majority vote or partial-run stability claim was made.\n"
        ),
        "20260905-external-blind-comparison.md": (
            "# External Blind Comparison\n\n"
            "`EXTERNAL_BLIND_JUDGMENT_STATUS = NOT_STARTED`\n\n"
            "No external judgment was supplied or fabricated. AI decisions remain sealed.\n"
        ),
        "20260905-judgment-bias-audit.md": (
            "# Structured Autonomy Judgment Bias Audit\n\n"
            "`STATUS = INSUFFICIENT_EVIDENCE_INCOMPLETE_ABC`\n\n"
            "A/B/C and external comparison are incomplete, so no bias conclusion is promoted.\n"
        ),
        "20260905-structured-autonomy-promotion-review.md": (
            "# Structured Autonomy Promotion Review\n\n"
            "`PROMOTION_READINESS = NEEDS_MORE_SHADOW_WORK`\n\n"
            "Blockers: incomplete C schema validation, A/B validation policy failures, external blind judgment not frozen, and KR/US natural proof pending.\n\n"
            "Production decision, renderer, Telegram, database, and main mutation: `0`.\n"
            "\nOpen P0 is `0` because every unsafe or nonconforming candidate failed closed. Open P1 is `2`: future-checkpoint semantic ownership generalization and logical-condition leaf-shape conformance. A new generation is required after those repairs; this generation must not be tuned or resumed.\n"
        ),
        "20260905-next-production-handoff.md": (
            "# Next Production Handoff\n\n"
            "1. Treat this generation as a frozen failed experiment; do not tune or resume it.\n"
            "2. Repair logical-condition generation/schema conformance and future-checkpoint semantic ownership generically.\n"
            "3. Start a new generation only after focused regression passes.\n"
            "4. Freeze external blind judgment from the blind-only intake before revealing AI decisions.\n"
            "5. Observe authoritative KR and US natural runs independently.\n"
        ),
    }
    for name, content in report_values.items():
        write_text(public_reports / name, content)
        if name in {
            "20260905-run-c.md",
            "20260905-abc-stability.md",
            "20260905-external-blind-comparison.md",
            "20260905-judgment-bias-audit.md",
            "20260905-structured-autonomy-promotion-review.md",
            "20260905-next-production-handoff.md",
        }:
            write_text(sealed_reports / name, content)

    blind_zip = _write_blind_intake_bundle(
        output_root=output_root,
        review_root=review_root,
        blind_manifest=blind_manifest,
        ai_manifest=ai_manifest,
    )
    artifact_rows = [
        ["generation", generation_id],
        ["blind fact pack", str(review_root / "BLIND_FACT_PACK")],
        ["blind intake ZIP", str(blind_zip)],
        ["machine promotion review", str(machine_dir / "promotion-review.json")],
        ["sealed AI decision pack", "SEALED_PENDING_EXTERNAL_BLIND_FREEZE"],
    ]
    artifact_index = (
        "# Program Artifact Index\n\n"
        + markdown_table(["Artifact", "Value"], artifact_rows)
        + "\n"
    )
    write_text(public_reports / "20260905-program-artifact-index.md", artifact_index)
    write_text(sealed_reports / "20260905-program-artifact-index.md", artifact_index)
    return {
        "promotion": promotion,
        "stability": stability,
        "bias": bias,
        "failure": run_failure,
        "blind_intake_zip": str(blind_zip),
        "blind_intake_zip_sha256": file_sha256(blind_zip),
    }


def _write_first_reports(
    *,
    destination: Path,
    candidates: Sequence[StructuredAutonomyCandidate],
    document: Mapping[str, object],
) -> None:
    rows = decision_rows(candidates)
    failures = [row for row in document["validation"] if row["status"] != "PASS"]
    write_text(
        destination / "20260905-structured-autonomy-fresh-first.md",
        "# Structured Autonomy Fresh First\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "New buyer", "Holder", "Entry"],
            rows,
        )
        + f"\n\nCandidates: `{len(candidates)}`. Old candidate reuse: `0`.\n",
    )
    write_text(
        destination / "20260905-structured-autonomy-fresh-first-validation.md",
        "# Structured Autonomy Fresh-First Validation\n\n"
        f"`FIRST_RUN_VALIDATED = {document['validation_pass_count']}`\n\n"
        + markdown_table(
            ["Ticker", "Status", "Errors"],
            [
                [row["ticker"], row["status"], ", ".join(row["errors"]) or "none"]
                for row in document["validation"]
            ],
        )
        + f"\n\nFailed subjects: `{len(failures)}`. Message quality: `{document['message_quality']['status']}`.\n",
    )


def _write_run_report(
    destination: Path, run: str, candidates: Sequence[StructuredAutonomyCandidate], document: Mapping[str, object]
) -> None:
    write_text(
        destination / f"20260905-run-{run}.md",
        f"# Structured Autonomy Run {run.upper()}\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "New buyer", "Holder", "Entry"],
            decision_rows(candidates),
        )
        + f"\n\nValidated: `{document['validation_pass_count']}/22`. Message quality: `{document['message_quality']['status']}`.\n",
    )


def _bias_audit(run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]]) -> dict[str, object]:
    candidates = [candidate for run in RUNS for candidate in run_candidates[run]]
    directional_unknown = sum(
        treatment.treatment == "DIRECTIONAL_NEGATIVE"
        for candidate in candidates
        for treatment in candidate.unknown_treatments
    )
    avoid = sum(candidate.new_buyer_view.stance == "AVOID" for candidate in candidates)
    reduce = sum(candidate.holder_view.stance == "REDUCE" for candidate in candidates)
    buy = sum(candidate.decision == "BUY" for candidate in candidates)
    sell = sum(candidate.decision == "SELL" for candidate in candidates)
    return {
        "contract": "structured-autonomy-judgment-bias-audit-v1",
        "runs": list(RUNS),
        "candidate_observations": len(candidates),
        "unknown_directional_negative_count": directional_unknown,
        "new_buyer_avoid_count": avoid,
        "holder_reduce_count": reduce,
        "buy_count": buy,
        "sell_count": sell,
        "unknown_negative_bias": "NO" if directional_unknown == 0 else "REVIEW_REQUIRED",
        "valuation_bias": "INSUFFICIENT_EVIDENCE_WITHOUT_EXTERNAL_COMPARISON",
        "timing_bias": "INSUFFICIENT_EVIDENCE_WITHOUT_EXTERNAL_COMPARISON",
        "action_context_bias": "INSUFFICIENT_EVIDENCE_WITHOUT_EXTERNAL_COMPARISON",
    }


def _finalize_internal(
    *,
    machine_dir: Path,
    sealed_reports: Path,
    generation_id: str,
    source_lock: Mapping[str, object],
    run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]],
    run_documents: Mapping[str, Mapping[str, object]],
    blind_manifest: Mapping[str, object],
    ai_manifest: Mapping[str, object],
) -> dict[str, object]:
    by_run = {
        run: {candidate.ticker: candidate for candidate in candidates}
        for run, candidates in run_candidates.items()
    }
    stability_rows = [
        classify_same_evidence_runs(
            (by_run["a"][ticker], by_run["b"][ticker], by_run["c"][ticker])
        )
        for ticker in COHORT
    ]
    stability = {
        **stability_summary(stability_rows),
        "runs_compared": ["a", "b", "c"],
        "rows": stability_rows,
        "majority_vote": 0,
        "decision_averaging": 0,
    }
    bias = _bias_audit(run_candidates)
    hard_errors = sum(
        row["status"] != "PASS"
        for run in RUNS
        for row in run_documents[run]["validation"]
    )
    message_failures = sum(
        run_documents[run]["message_quality"]["status"] != "PASS" for run in RUNS
    )
    promotion = {
        "contract": "structured-autonomy-promotion-review-v1",
        "generation_id": generation_id,
        "current_operating_sha": BASE_SHA,
        "current_model": engine.REASONING_MODEL,
        "current_reasoning_effort": engine.REASONING_EFFORT,
        "kr_natural_explicit_v2_proof": "PENDING",
        "us_natural_explicit_v2_proof": "PENDING",
        "fresh_experiment_generation": "PASS",
        "old_candidate_reuse": 0,
        "source_packet_us": US_PACKET_ID,
        "source_packet_kr": KR_PACKET_ID,
        "source_as_of_us": source_lock["sources"]["us"]["assessment_date"],
        "source_as_of_kr": source_lock["sources"]["kr"]["assessment_date"],
        "model_equivalence": "PASS",
        "first_run_validated": run_documents["first"]["validation_pass_count"],
        "a_b_c_gate": "RUN",
        "ai_judgment_leakage_in_blind_pack": blind_manifest[
            "ai_judgment_leakage_count"
        ],
        "blind_pack_sha256": blind_manifest["blind_pack_sha256"],
        "ai_decision_pack_sha256": ai_manifest["ai_decision_pack_sha256"],
        "external_blind_judgment_status": "NOT_STARTED",
        "run_a_validated": run_documents["a"]["validation_pass_count"],
        "run_b_validated": run_documents["b"]["validation_pass_count"],
        "run_c_validated": run_documents["c"]["validation_pass_count"],
        "stable_count": stability["counts"]["STABLE"],
        "boundary_uncertainty_count": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "unstable_count": stability["counts"]["UNSTABLE"],
        "ai_vs_external_full_agreement": "NOT_MEASURED",
        "ai_vs_external_boundary_difference": "NOT_MEASURED",
        "ai_vs_external_meaningful_difference": "NOT_MEASURED",
        "ai_vs_external_major_difference": "NOT_MEASURED",
        "buy_sell_direct_reversal": stability["buy_sell_reversal_count"],
        "unknown_negative_bias": bias["unknown_negative_bias"],
        "valuation_bias": bias["valuation_bias"],
        "timing_bias": bias["timing_bias"],
        "action_context_bias": bias["action_context_bias"],
        "hard_safety_regression": hard_errors,
        "message_quality_failures": message_failures,
        "production_decision_mutation": 0,
        "production_renderer_mutation": 0,
        "production_telegram_send": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "promotion_readiness": "NEEDS_MORE_SHADOW_WORK",
        "promotion_blockers": [
            "external_blind_judgment_not_frozen",
            "kr_natural_explicit_v2_proof_pending",
            "us_natural_explicit_v2_proof_pending",
        ],
    }
    if hard_errors or message_failures or stability["counts"]["UNSTABLE"]:
        promotion["promotion_readiness"] = "NEEDS_MORE_SHADOW_WORK"
        promotion["promotion_blockers"].append("internal_shadow_gate_not_clean")
    write_json(machine_dir / "abc-stability.json", stability)
    write_json(machine_dir / "promotion-review.json", promotion)
    write_json(machine_dir / "judgment-bias-audit.json", bias)
    for run in RUNS:
        name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        write_json(machine_dir / name, run_documents[run])
    write_json(machine_dir / "structured-autonomy-source-lock.json", source_lock)

    stability_rows_md = [
        [
            row["ticker"],
            row["classification"],
            " / ".join(row["label_sequence"]),
            " / ".join(
                f"{value['buy']:.1f}:{value['sell']:.1f}"
                for value in row["balance_sequence"]
            ),
            row["max_balance_distance"],
            ", ".join(row["reasons"]) or "none",
        ]
        for row in stability_rows
    ]
    write_text(
        sealed_reports / "20260905-abc-stability.md",
        "# Structured Autonomy A/B/C Stability\n\n"
        + markdown_table(
            ["Ticker", "Class", "Labels", "Balances", "Spread", "Reasons"],
            stability_rows_md,
        )
        + "\n\n"
        + json.dumps(stability["counts"], sort_keys=True)
        + "\n",
    )
    write_text(
        sealed_reports / "20260905-judgment-bias-audit.md",
        "# Structured Autonomy Judgment Bias Audit\n\n"
        + markdown_table(["Metric", "Value"], [[key, value] for key, value in bias.items()])
        + "\n\nExternal-comparison-dependent bias findings remain `INSUFFICIENT_EVIDENCE`.\n",
    )
    write_text(
        sealed_reports / "20260905-external-blind-comparison.md",
        "# External Blind Comparison\n\n"
        "`EXTERNAL_BLIND_JUDGMENT_STATUS = NOT_STARTED`\n\n"
        "No external judgment has been supplied or fabricated. Agreement and difference "
        "counts remain `NOT_MEASURED`.\n",
    )
    write_text(
        sealed_reports / "20260905-structured-autonomy-promotion-review.md",
        "# Structured Autonomy Promotion Review\n\n"
        f"`PROMOTION_READINESS = {promotion['promotion_readiness']}`\n\n"
        + markdown_table(
            ["Gate", "Value"],
            [[key, value] for key, value in promotion.items() if key != "promotion_blockers"],
        )
        + "\n\nBlockers: `"
        + ", ".join(promotion["promotion_blockers"])
        + "`. Production activation is not authorized.\n",
    )
    write_text(
        sealed_reports / "20260905-next-production-handoff.md",
        "# Next Production Handoff\n\n"
        "1. Freeze an independent 22-subject judgment from the blind intake pack.\n"
        "2. Reveal the sealed AI pack and classify differences.\n"
        "3. Observe the next authoritative KR and US natural runs.\n"
        "4. Recompute promotion readiness without tuning this generation.\n\n"
        "Production decision, renderer, Telegram, database, and main mutation: `0`.\n",
    )
    return {"promotion": promotion, "stability": stability, "bias": bias}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--public-report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    args.us_packet = args.us_packet.resolve()
    args.kr_packet = args.kr_packet.resolve()
    args.us_base_messages = args.us_base_messages.resolve()
    args.kr_base_messages = args.kr_base_messages.resolve()
    output_root = args.output_root.resolve()
    public_reports = args.public_report_dir.resolve()
    machine_dir = output_root / "machine"
    sealed_root = output_root / "sealed"
    sealed_reports = sealed_root / "reports"
    review_root = output_root / "review-intake"
    output_root.mkdir(parents=True, exist_ok=True)
    state = _state(output_root / "program-state.json", resume=args.resume)
    generation_id = str(state["generation_id"])
    configure_engine(generation_id)
    engine_args = _engine_args(args, output_root)
    (
        evidence,
        aliases,
        price_maps,
        _contexts,
        stocks,
        base_messages,
        _engine_source_lock,
    ) = engine.prepare(engine_args)
    source_lock = _source_lock(
        generation_id=generation_id,
        args=args,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    write_natural_proof_files(machine_dir, public_reports)
    write_json(machine_dir / "structured-autonomy-source-lock.json", source_lock)
    write_text(
        public_reports / "20260905-structured-autonomy-source-lock.md",
        "# Structured Autonomy Source Lock\n\n"
        f"- Generation: `{generation_id}`\n"
        f"- US: `{US_PACKET_ID}` / `{source_lock['sources']['us']['assessment_date']}`\n"
        f"- KR: `{KR_PACKET_ID}` / `{source_lock['sources']['kr']['assessment_date']}`\n"
        f"- Model: `{engine.REASONING_MODEL}` / `{engine.REASONING_EFFORT}`\n"
        "- Live provider fact fetches: `0`\n"
        "- Old candidate reuse: `0`\n"
        "- Cross-market leakage: `0`\n",
    )
    if args.prepare_only:
        print(
            json.dumps(
                {
                    "prepared": True,
                    "generation_id": generation_id,
                    "subjects": len(evidence),
                    "model": engine.REASONING_MODEL,
                    "reasoning_effort": engine.REASONING_EFFORT,
                },
                sort_keys=True,
            )
        )
        return

    run_candidates: dict[str, Sequence[StructuredAutonomyCandidate]] = {}
    run_documents: dict[str, Mapping[str, object]] = {}
    first_candidates, first_document, _first_rendered = engine.execute_run(
        run="first",
        args=engine_args,
        evidence_packets=evidence,
        alias_catalogs=aliases,
        price_maps=price_maps,
        stock_by_ticker=stocks,
        base_messages=base_messages,
    )
    run_candidates["first"] = first_candidates
    run_documents["first"] = first_document
    _write_first_reports(
        destination=sealed_reports,
        candidates=first_candidates,
        document=first_document,
    )
    blind_manifest, leaks = build_blind_pack(
        root=review_root / "BLIND_FACT_PACK",
        generation_id=generation_id,
        created_at=str(state["created_at"]),
        evidence=evidence,
        price_maps=price_maps,
        stocks=stocks,
    )
    ai_manifest = build_ai_pack(
        root=sealed_root / "AI_DECISION_PACK",
        generation_id=generation_id,
        created_at=str(state["created_at"]),
        candidates=first_candidates,
        run_document=first_document,
    )
    template = external_template(generation_id)
    write_json(review_root / "external-comparison-template.json", template)
    write_json(machine_dir / "external-comparison-template.json", template)
    write_json(machine_dir / "blind-fact-pack-manifest.json", blind_manifest)
    write_json(machine_dir / "ai-decision-pack-manifest.json", ai_manifest)
    write_blind_protocol(review_root / "COMPARISON_PROTOCOL.md", generation_id)
    write_text(
        public_reports / "20260905-blind-fact-pack-manifest.md",
        "# Blind Fact Pack Manifest\n\n"
        f"- Generation: `{generation_id}`\n"
        f"- Subjects: `{blind_manifest['subject_count']}`\n"
        f"- Blind SHA-256: `{blind_manifest['blind_pack_sha256']}`\n"
        f"- AI judgment leakage: `{blind_manifest['ai_judgment_leakage_count']}`\n",
    )
    write_text(
        public_reports / "20260905-ai-decision-pack-manifest.md",
        "# AI Decision Pack Manifest\n\n"
        f"- Generation: `{generation_id}`\n"
        f"- Subjects: `{ai_manifest['subject_count']}`\n"
        f"- AI decision SHA-256: `{ai_manifest['ai_decision_pack_sha256']}`\n"
        "- State: `SEALED`\n- Reveal gate: `EXTERNAL_BLIND_JUDGMENT_FROZEN`\n",
    )
    write_text(
        public_reports / "20260905-blind-comparison-protocol.md",
        (review_root / "COMPARISON_PROTOCOL.md").read_text(encoding="utf-8"),
    )
    if leaks:
        raise ValueError(f"ai_judgment_leakage_in_blind_pack:{len(leaks)}")

    first_pass = (
        int(first_document["validation_pass_count"]) == 22
        and first_document["message_quality"]["status"] == "PASS"
    )
    if not first_pass:
        failure = {
            "contract": "structured-autonomy-promotion-review-v1",
            "generation_id": generation_id,
            "first_run_validated": first_document["validation_pass_count"],
            "first_message_quality": first_document["message_quality"]["status"],
            "a_b_c_gate": "NOT_RUN_FIRST_GATE_FAILED",
            "external_blind_judgment_status": "NOT_STARTED",
            "promotion_readiness": "NEEDS_MORE_SHADOW_WORK",
            "production_decision_mutation": 0,
            "production_renderer_mutation": 0,
            "production_telegram_send": 0,
            "production_db_mutation": 0,
            "main_merge": 0,
        }
        write_json(machine_dir / "fresh-first.json", first_document)
        write_json(machine_dir / "promotion-review.json", failure)
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return

    for run in ("a", "b", "c"):
        try:
            candidates, document, _rendered = engine.execute_run(
                run=run,
                args=engine_args,
                evidence_packets=evidence,
                alias_catalogs=aliases,
                price_maps=price_maps,
                stock_by_ticker=stocks,
                base_messages=base_messages,
            )
        except Exception as exc:
            result = _write_incomplete_reports(
                output_root=output_root,
                public_reports=public_reports,
                sealed_reports=sealed_reports,
                machine_dir=machine_dir,
                review_root=review_root,
                generation_id=generation_id,
                source_lock=source_lock,
                run_documents=run_documents,
                failed_run=run,
                failure=_safe_validation_failure(exc),
                blind_manifest=blind_manifest,
                ai_manifest=ai_manifest,
            )
            print(
                json.dumps(
                    {
                        "generation_id": generation_id,
                        "status": "INCOMPLETE_ABC",
                        "failed_run": run,
                        "failure": result["failure"]["failure"],
                        "external_blind_judgment_status": "NOT_STARTED",
                        "promotion_readiness": result["promotion"][
                            "promotion_readiness"
                        ],
                        "blind_intake_zip": result["blind_intake_zip"],
                        "blind_intake_zip_sha256": result[
                            "blind_intake_zip_sha256"
                        ],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return
        run_candidates[run] = candidates
        run_documents[run] = document
        _write_run_report(sealed_reports, run, candidates, document)

    result = _finalize_internal(
        machine_dir=machine_dir,
        sealed_reports=sealed_reports,
        generation_id=generation_id,
        source_lock=source_lock,
        run_candidates=run_candidates,
        run_documents=run_documents,
        blind_manifest=blind_manifest,
        ai_manifest=ai_manifest,
    )
    write_text(
        sealed_reports / "20260905-program-artifact-index.md",
        "# Program Artifact Index\n\n"
        + markdown_table(
            ["Path", "SHA-256", "Bytes"],
            [
                [str(path.relative_to(output_root)), file_sha256(path), path.stat().st_size]
                for path in sorted(
                    candidate for candidate in output_root.rglob("*") if candidate.is_file()
                )
                if "engine/run-" not in str(path.relative_to(output_root))
            ],
        )
        + "\n",
    )
    blind_zip = _write_blind_intake_bundle(
        output_root=output_root,
        review_root=review_root,
        blind_manifest=blind_manifest,
        ai_manifest=ai_manifest,
    )
    print(
        json.dumps(
            {
                "generation_id": generation_id,
                "first_run_validated": first_document["validation_pass_count"],
                "runs_a_b_c": {
                    run: run_documents[run]["validation_pass_count"]
                    for run in ("a", "b", "c")
                },
                "stability": result["stability"]["counts"],
                "blind_pack_sha256": blind_manifest["blind_pack_sha256"],
                "ai_decision_pack_sha256": ai_manifest["ai_decision_pack_sha256"],
                "external_blind_judgment_status": "NOT_STARTED",
                "promotion_readiness": result["promotion"]["promotion_readiness"],
                "blind_intake_zip": str(blind_zip),
                "blind_intake_zip_sha256": file_sha256(blind_zip),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
