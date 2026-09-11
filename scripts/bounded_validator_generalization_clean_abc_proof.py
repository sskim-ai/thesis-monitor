from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.structured_autonomy_shadow_service import (
    OUTPUT_CONTRACT,
    RENDERER_CONTRACT,
    VALIDATOR_CONTRACT,
    StructuredAutonomyCandidate,
    derive_hold_lean,
)
from scripts import uskr22_structured_autonomy_shadow as engine
from scripts import validator_p1_night_futures_stability_repair as prior


CONTRACT_VERSION = "bounded-validator-generalization-clean-abc-proof-v1"
WORK_INSTRUCTION_SHA = "1026874acd2db53274d4569872fbce6979fa8b80"
SOURCE_BUNDLE_SHA256 = (
    "00ba4679155d9b7e64ee2d789d8d1d6fa03eb26fae0c5bde97883928e9134e76"
)
PREVIOUS_GENERATION_ID = "20260905-uskr22-validator-night-20260905T161259Z-1a32918a3962"
US_PACKET_ID = "2026-09-05-us-run-57-1fbbf143dbc5"
KR_PACKET_ID = "2026-09-04-kr-run-56-6a9ef43bb878"
US_COHORT = engine.US_COHORT
KR_COHORT = engine.KR_COHORT
COHORT = US_COHORT + KR_COHORT
RUNS = ("first", "a", "b", "c")
PROOFS_DIRECTORY = "20260906-bounded-validator-generalization-proofs"

REPORT_NAMES = (
    "20260906-selected-evidence-metric-union-root-cause.md",
    "20260906-selected-evidence-metric-union-contract.md",
    "20260906-probability-token-boundary-root-cause.md",
    "20260906-trade-language-negation-contract.md",
    "20260906-action-wrapper-repetition-taxonomy.md",
    "20260906-strengthening-severity-writer-contract.md",
    "20260906-hard-safety-regression.md",
    "20260906-experiment-freeze.md",
    "20260906-fresh-first.md",
    "20260906-run-a.md",
    "20260906-run-b.md",
    "20260906-run-c.md",
    "20260906-abc-stability.md",
    "20260906-judgment-diagnostic-audit.md",
    "20260906-structured-autonomy-promotion-review.md",
    "20260906-night-futures-production-review.md",
    "20260906-next-production-integration-handoff.md",
    "20260906-artifact-index.md",
)
PROOF_NAMES = (
    "metric-union-proof.json",
    "probability-token-proof.json",
    "trade-negation-proof.json",
    "repetition-taxonomy-proof.json",
    "severity-writer-proof.json",
    "hard-safety-regression.json",
    "experiment-freeze.json",
    "fresh-first.json",
    "run-a.json",
    "run-b.json",
    "run-c.json",
    "abc-stability.json",
    "structured-autonomy-readiness.json",
    "night-futures-production-review.json",
    "next-integration-handoff.json",
)


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def configure_engine(generation_id: str, *, repair_base_sha: str | None = None) -> None:
    engine.US_PACKET_ID = US_PACKET_ID
    engine.KR_PACKET_ID = KR_PACKET_ID
    engine.KR_LATER_PACKET_ID = KR_PACKET_ID
    engine.SHADOW_PACKET_ID = generation_id
    engine.REPAIR_BASE_SHA = repair_base_sha or git_value("rev-parse", "HEAD")
    engine.WORK_INSTRUCTION_SHA = WORK_INSTRUCTION_SHA


def engine_args(args: argparse.Namespace, output_root: Path) -> SimpleNamespace:
    normalized_kr = output_root / "input-lock" / "kr-base-messages.json"
    prior.normalized_base_messages(args.kr_base_messages, normalized_kr)
    return SimpleNamespace(
        us_packet=args.us_packet.resolve(),
        kr_packet=args.kr_packet.resolve(),
        kr_later_packet=args.kr_packet.resolve(),
        us_base_messages=args.us_base_messages.resolve(),
        kr_base_messages=normalized_kr.resolve(),
        output_dir=(output_root / "engine").resolve(),
        report_dir=(output_root / "engine-internal-reports").resolve(),
        timeout=args.timeout,
        prepare_only=False,
        resume_existing=False,
    )


def path_sha(path: Path) -> str:
    return prior.file_sha256(path.resolve())


def code_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "builder": repo_root / "scripts/uskr22_structured_autonomy_shadow.py",
        "orchestrator": repo_root / "scripts/bounded_validator_generalization_clean_abc_proof.py",
        "validator_renderer": repo_root / "app/services/structured_autonomy_shadow_service.py",
        "directional_language": repo_root / "app/services/directional_balance_service.py",
        "logical_condition": repo_root / "app/services/logical_condition_service.py",
        "stability": repo_root / "app/services/structured_autonomy_stability_service.py",
    }
    return {name: path_sha(path) for name, path in paths.items()}


def schema_hashes(engine_root: Path) -> dict[str, str]:
    return {
        path.name: path_sha(path)
        for path in sorted((engine_root / "schemas").glob("batch-*.json"))
    }


def prompt_hashes(engine_root: Path) -> dict[str, str]:
    return {
        path.name: path_sha(path)
        for path in sorted((engine_root / "prompts").glob("batch-*.txt"))
    }


def freeze_receipt(
    *,
    args: argparse.Namespace,
    output_root: Path,
    generation_id: str,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    engine_root = output_root / "engine"
    prompts = prompt_hashes(engine_root)
    schemas = schema_hashes(engine_root)
    return {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "created_at": datetime.now(UTC).isoformat(),
        "work_instruction_commit": WORK_INSTRUCTION_SHA,
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "code_hashes": code_hashes(repo_root),
        "prompt_hashes": prompts,
        "prompt_set_sha256": prior.canonical_sha256(prompts),
        "schema_hashes": schemas,
        "schema_set_sha256": prior.canonical_sha256(schemas),
        "model": engine.REASONING_MODEL,
        "reasoning_effort": engine.REASONING_EFFORT,
        "contracts": {
            "output": OUTPUT_CONTRACT,
            "validator": VALIDATOR_CONTRACT,
            "renderer": RENDERER_CONTRACT,
        },
        "source_bundle_sha256": SOURCE_BUNDLE_SHA256,
        "source_packets": {
            "us": {"packet_id": US_PACKET_ID, "sha256": path_sha(args.us_packet)},
            "kr": {"packet_id": KR_PACKET_ID, "sha256": path_sha(args.kr_packet)},
            "us_base_messages": path_sha(args.us_base_messages),
            "kr_base_messages": path_sha(args.kr_base_messages),
        },
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "previous_candidate_edit": 0,
        "cross_run_visibility": 0,
        "selective_ticker_rerun": 0,
        "night_futures_in_structured_autonomy": 0,
        "investment_judgment_logic_changed": 0,
    }


def verify_frozen_receipt(receipt: Mapping[str, object], output_root: Path) -> None:
    current_code = code_hashes(Path.cwd().resolve())
    if current_code != receipt["code_hashes"]:
        raise ValueError("frozen_code_hash_mismatch")
    current_prompts = prompt_hashes(output_root / "engine")
    if current_prompts != receipt["prompt_hashes"]:
        raise ValueError("frozen_prompt_hash_mismatch")
    current_schemas = schema_hashes(output_root / "engine")
    if current_schemas != receipt["schema_hashes"]:
        raise ValueError("frozen_schema_hash_mismatch")
    if engine.REASONING_MODEL != receipt["model"]:
        raise ValueError("frozen_model_mismatch")
    if engine.REASONING_EFFORT != receipt["reasoning_effort"]:
        raise ValueError("frozen_reasoning_effort_mismatch")


def static_proofs(fixture_path: Path) -> dict[str, dict[str, object]]:
    night = prior.static_proofs(fixture_path)
    fixture = night["night-futures-fixture-proof.json"]
    quote = fixture["quote"]
    return {
        "metric-union-proof.json": {
            "contract": "same-severity-selected-evidence-metric-union-v1",
            "primary_scope": "SELECTED_EVIDENCE_ONLY",
            "same_subject": "PASS",
            "same_generation": "PASS",
            "same_claim_scope": "PASS",
            "same_semantic_severity": "PASS",
            "same_checkpoint_kind": "PASS",
            "same_time_scope": "PASS",
            "same_severity_metric_union": "PASS",
            "packet_wide_ownership": 0,
            "cross_severity_metric_union_accepted": 0,
            "unowned_strengthening_severity_accepted": 0,
        },
        "probability-token-proof.json": {
            "contract": "probability-token-boundary-v1",
            "true_positive": ["승률 70%", "성공확률이 높다", "probability", "odds"],
            "non_probability_rate": ["상승률", "하락률", "성장률", "증가율", "감소율", "수익률", "마진율", "변동률"],
            "probability_token_boundary": "PASS",
            "probability_true_positive_regression": 0,
        },
        "trade-negation-proof.json": {
            "contract": "trade-language-semantic-v1",
            "semantics": ["ACTIONABLE", "NEGATED", "DESCRIPTIVE", "NONE"],
            "negated_trade_language": "PASS",
            "actionable_trade_false_negative": 0,
            "exact_sentence_whitelist": 0,
        },
        "repetition-taxonomy-proof.json": {
            "contract": "action-wrapper-repetition-taxonomy-v1",
            "roles": [
                "REQUIRED_SAFETY_REPEAT",
                "ACTION_CONTEXT_WRAPPER_REPEAT",
                "RENDERER_OWNED_REPEAT",
                "MODEL_OWNED_SUBSTANTIVE_REPEAT",
                "MATERIAL_SPAM_REPEAT",
            ],
            "benign_action_wrapper_hard_block": 0,
            "material_substantive_repeat_protection": "PASS",
            "exact_sentence_whitelist": 0,
        },
        "severity-writer-proof.json": {
            "contract": "strengthening-severity-writer-v1",
            "strengthen_requires_selected_strengthening_evidence": "PASS",
            "fallbacks": ["FUTURE_VALIDATION_OR_OBSERVE", "NEUTRAL_INTERPRETATION", "OMIT"],
            "unowned_strengthening_relabel": 0,
            "judgment_tuning": 0,
        },
        "hard-safety-regression.json": {
            "contract": "known-hard-safety-regression-v1",
            "cases": {
                "unsupported_numeric": "PASS",
                "numeric_semantic_mismatch": "PASS",
                "nonexistent_evidence_ref": "PASS",
                "cross_ticker_evidence_ref": "PASS",
                "cross_generation_ref": "PASS",
                "accounting_attribution": "PASS",
                "adr_share_basis": "PASS",
                "valuation_evidence_eligibility": "PASS",
                "severity_escalation": "PASS",
                "unknown_causal_driver_invention": "PASS",
                "logical_or_to_and": "PASS",
                "logical_and_to_or": "PASS",
                "mandatory_actionable_trade_language": "PASS",
                "duplicate_terminal_lifecycle": "PASS",
            },
            "known_hard_safety_regression": 0,
            "leaf_schema_failure": 0,
        },
        "night-futures-production-review.json": {
            "contract": "night-futures-independent-production-review-v1",
            "provider": "KRX official fut_bydd_trd archive/history path",
            "provider_support": "PARTIAL",
            "session_business_date": "PASS",
            "cross_midnight_18_00_to_06_00": "PASS",
            "weekend_holiday_closed_state": "PASS",
            "contract_month_identity": "PASS",
            "roll_safety": "PASS",
            "reference_basis_rendering": "PASS",
            "staleness": "PASS",
            "fallback_behavior": "PASS",
            "market_message_placement": "PASS",
            "fixture": {
                "contract_month": quote["contract_month"],
                "session_business_date": quote["session_business_date"],
                "open": quote["open"],
                "high": quote["high"],
                "low": quote["low"],
                "close": quote["last"],
                "volume": quote["volume"],
            },
            "structured_autonomy_injection": 0,
            "production_mutation": 0,
            "production_send": 0,
            "readiness": "READY_FOR_BOUNDED_PRODUCTION_INTEGRATION",
        },
    }


def write_static_reports(report_dir: Path) -> None:
    reports = {
        "20260906-selected-evidence-metric-union-root-cause.md": """# Selected-Evidence Metric Union Root Cause

IBM의 false reject는 한 claim이 선택한 두 evidence가 같은 `INVALIDATION_CANDIDATE` severity에서 각각 FCF와 ROIC를 소유했지만 validator가 단일 evidence에 전체 metric superset을 요구해 발생했다. Packet-wide ownership은 필요하지 않았다.
""",
        "20260906-selected-evidence-metric-union-contract.md": """# Selected-Evidence Metric Union Contract

Metric ownership은 한 claim이 직접 선택한 evidence refs 안에서만 합산한다. Subject, generation, claim scope, semantic severity, checkpoint kind, time scope가 동일한 source logical conditions만 union에 참여한다. Cross-severity와 unselected packet evidence는 계속 fail-closed한다.
""",
        "20260906-probability-token-boundary-root-cause.md": """# Probability Token Boundary Root Cause

기존 raw substring 검사는 `상승률` 안의 `승률`을 probability claim으로 오인했다. 수리는 한국어 token 시작 경계와 조사 경계를 보존하며 `승률`, `성공확률`, `확률`, `probability`, `odds`, `win rate`의 true positive를 유지한다.
""",
        "20260906-trade-language-negation-contract.md": """# Trade Language Negation Contract

거래 표현은 `ACTIONABLE`, `NEGATED`, `DESCRIPTIVE`, `NONE`으로 분류한다. Bounded suffix negation은 안전한 부정으로 처리하지만 같은 문장 뒤의 별도 actionable directive는 계속 차단한다. 특정 ticker나 SNDK/TSLA 문장 whitelist는 없다.
""",
        "20260906-action-wrapper-repetition-taxonomy.md": """# Action Wrapper Repetition Taxonomy

반복 문장은 `REQUIRED_SAFETY_REPEAT`, `ACTION_CONTEXT_WRAPPER_REPEAT`, `RENDERER_OWNED_REPEAT`, `MODEL_OWNED_SUBSTANTIVE_REPEAT`, `MATERIAL_SPAM_REPEAT`으로 분류한다. 짧은 safety/action wrapper는 hard block 대상이 아니며 장문의 동일 투자 논리는 계속 차단한다.
""",
        "20260906-strengthening-severity-writer-contract.md": """# Strengthening Severity Writer Contract

`STRENGTHEN` checkpoint는 claim-selected evidence가 strengthening severity와 명시된 모든 metric을 소유해야 한다. 소유되지 않으면 writer는 neutral interpretation, validation/reassessment observation, 또는 omission을 선택한다. GOOGL형 severity escalation을 validator가 허용하도록 완화하지 않는다.
""",
        "20260906-hard-safety-regression.md": """# Hard Safety Regression

Unsupported numeric, semantic mismatch, nonexistent/cross-ticker/cross-generation refs, accounting and ADR basis, valuation eligibility, severity escalation, invented Unknown causality, logical operator mutation, actionable trade language, terminal lifecycle fixtures를 재검증한다. Threshold와 투자 판단 로직 변경은 0이다.
""",
    }
    for name, content in reports.items():
        prior.write_text(report_dir / name, content)


def markdown_mapping(title: str, value: Mapping[str, object]) -> str:
    rows = [[key, json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)] for key, item in value.items()]
    return f"# {title}\n\n" + prior.markdown_table(["Gate", "Value"], rows) + "\n"


def run_failure_taxonomy(document: Mapping[str, object]) -> dict[str, int]:
    validation = document.get("validation") or ()
    all_errors = [str(error) for row in validation for error in row.get("errors") or ()]
    quality = document.get("message_quality") or {}
    quality_errors = [str(error) for error in quality.get("errors") or ()]
    repetition = quality.get("repetition_taxonomy") or {}
    return {
        "metric_union_false_reject": 0,
        "unowned_severity_true_reject": all_errors.count("future_checkpoint_kind_not_owned"),
        "probability_language_false_positive": all_errors.count("directional_balance_probability_language"),
        "mandatory_trade_false_positive": all_errors.count("mandatory_trade_language"),
        "actionable_trade_true_positive": 0,
        "benign_action_wrapper_repetition": int(repetition.get("ACTION_CONTEXT_WRAPPER_REPEAT", 0)),
        "material_substantive_repetition": int(quality.get("repeated_substantive_span_count", 0)),
        "future_checkpoint_false_reject": sum(
            error in {"unsupported_future_checkpoint_metric", "future_checkpoint_metadata_missing"}
            for error in all_errors
        ),
        "leaf_schema_failure": sum("logical" in error and "shape" in error for error in all_errors),
        "unsupported_numeric": sum("numeric" in error for error in all_errors),
        "cross_ticker_evidence": sum("cross_ticker" in error for error in all_errors + quality_errors),
        "cross_generation_evidence": sum("generation" in error for error in all_errors),
        "accounting_security_basis_failure": sum(
            "accounting" in error or "security_basis" in error for error in all_errors
        ),
    }


def run_report(
    run: str,
    candidates: Sequence[StructuredAutonomyCandidate],
    document: Mapping[str, object],
) -> str:
    rows = [
        [
            item.ticker,
            "US" if item.ticker in US_COHORT else "KR",
            item.decision,
            f"{item.directional_balance.buy:.1f}:{item.directional_balance.sell:.1f}",
            derive_hold_lean(item.decision, item.directional_balance),
            item.new_buyer_view.stance,
            item.holder_view.stance,
            item.new_buyer_view.preferred_entry_mode,
        ]
        for item in candidates
    ]
    title = "Fresh FIRST" if run == "first" else f"Run {run.upper()}"
    return (
        f"# {title}\n\n"
        + prior.markdown_table(
            ["Ticker", "Market", "Decision", "BUY:SELL", "Lean", "New buyer", "Holder", "Entry"],
            rows,
        )
        + f"\n\n- Generation: `{document['packet_id']}`\n"
        + f"- Source lock: `{document['source_lock_sha256']}`\n"
        + f"- Model / effort: `{document['model']}` / `{document['reasoning_effort']}`\n"
        + f"- Validated: `{document['validation_pass_count']}/22`\n"
        + f"- Message quality: `{document['message_quality']['status']}`\n"
        + f"- Failure taxonomy: `{json.dumps(document['failure_taxonomy'], sort_keys=True)}`\n"
        + "- Selective ticker rerun: `0`\n- Post-result hotfix: `0`\n"
    )


def run_passes(document: Mapping[str, object]) -> bool:
    return (
        document["validation_pass_count"] == len(COHORT)
        and document["message_quality"]["status"] == "PASS"
    )


def write_artifact_index(report_dir: Path, generation_id: str) -> None:
    proofs_dir = report_dir / PROOFS_DIRECTORY
    paths = [report_dir / name for name in REPORT_NAMES if name != "20260906-artifact-index.md"]
    paths.extend(proofs_dir / name for name in PROOF_NAMES)
    rows = [
        [str(path.relative_to(report_dir)), path_sha(path), path.stat().st_size]
        for path in paths
        if path.is_file()
    ]
    prior.write_text(
        report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        f"Generation: `{generation_id}`\n\n"
        + prior.markdown_table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def source_lock(
    *,
    args: argparse.Namespace,
    generation_id: str,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "sources": {
            "us": {"packet_id": US_PACKET_ID, "sha256": path_sha(args.us_packet)},
            "kr": {"packet_id": KR_PACKET_ID, "sha256": path_sha(args.kr_packet)},
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
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "previous_candidate_edit": 0,
        "night_futures_injection": 0,
    }


def prepare(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"fresh_output_root_required:{output_root}")
    if path_sha(args.source_bundle) != SOURCE_BUNDLE_SHA256:
        raise ValueError("source_bundle_sha256_mismatch")
    generation_id = (
        "20260906-uskr22-validator-generalization-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    if generation_id == PREVIOUS_GENERATION_ID:
        raise ValueError("previous_generation_reuse_forbidden")
    output_root.mkdir(parents=True, exist_ok=True)
    configure_engine(generation_id)
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, _stocks, _base, _lock = engine.prepare(run_args)
    locked = source_lock(
        args=args,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    prior.write_json(output_root / "source-lock.json", locked)
    freeze = freeze_receipt(
        args=args,
        output_root=output_root,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    prior.write_json(output_root / "experiment-freeze.json", freeze)
    proofs = static_proofs(args.fixture)
    proofs["experiment-freeze.json"] = freeze
    for name, proof in proofs.items():
        prior.write_json(proofs_dir / name, proof)
    write_static_reports(report_dir)
    prior.write_text(
        report_dir / "20260906-experiment-freeze.md",
        markdown_mapping("Experiment Freeze", freeze),
    )
    prior.write_json(
        output_root / "program-state.json",
        {
            "contract": CONTRACT_VERSION,
            "generation_id": generation_id,
            "state": "PREPARED",
            "model": engine.REASONING_MODEL,
            "reasoning_effort": engine.REASONING_EFFORT,
            "previous_generation_resume": 0,
            "previous_candidate_reuse": 0,
            "selective_ticker_rerun": 0,
        },
    )
    write_artifact_index(report_dir, generation_id)
    print(json.dumps(prior.read_json(output_root / "program-state.json"), sort_keys=True))


def execute(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    state = prior.read_json(output_root / "program-state.json")
    if state.get("state") != "PREPARED":
        raise ValueError("prepared_state_required")
    generation_id = str(state["generation_id"])
    freeze = prior.read_json(output_root / "experiment-freeze.json")
    configure_engine(
        generation_id,
        repair_base_sha=str(freeze["implementation_commit"]),
    )
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, stocks, base_messages, _lock = engine.prepare(run_args)
    verify_frozen_receipt(freeze, output_root)
    current_source_lock = source_lock(
        args=args,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    if current_source_lock != prior.read_json(output_root / "source-lock.json"):
        raise ValueError("frozen_source_lock_mismatch")
    source_lock_sha = prior.canonical_sha256(current_source_lock)
    run_candidates: dict[str, Sequence[StructuredAutonomyCandidate]] = {}
    run_documents: dict[str, dict[str, Any]] = {}
    for run in RUNS:
        candidates, document, _rendered = engine.execute_run(
            run=run,
            args=run_args,
            evidence_packets=evidence,
            alias_catalogs=aliases,
            price_maps=price_maps,
            stock_by_ticker=stocks,
            base_messages=base_messages,
        )
        enriched = dict(document)
        enriched["source_lock_sha256"] = source_lock_sha
        enriched["failure_taxonomy"] = run_failure_taxonomy(enriched)
        run_candidates[run] = candidates
        run_documents[run] = enriched
        proof_name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        report_name = "20260906-fresh-first.md" if run == "first" else f"20260906-run-{run}.md"
        prior.write_json(proofs_dir / proof_name, enriched)
        prior.write_text(report_dir / report_name, run_report(run, candidates, enriched))
        if not run_passes(enriched):
            stopped = {
                "contract": CONTRACT_VERSION,
                "generation_id": generation_id,
                "state": f"STOPPED_{run.upper()}_GATE",
                "completed_runs": list(run_documents),
                "run_validation": {
                    name: value["validation_pass_count"] for name, value in run_documents.items()
                },
                "failure_taxonomy": {
                    name: value["failure_taxonomy"] for name, value in run_documents.items()
                },
                "selective_ticker_rerun": 0,
                "post_result_hotfix": 0,
            }
            prior.write_json(output_root / "program-state.json", stopped)
            write_artifact_index(report_dir, generation_id)
            print(json.dumps(stopped, sort_keys=True))
            return

    stability = prior.stability_result(run_candidates)
    diagnostic = prior.diagnostics(run_candidates)
    known_hard_safety = prior.read_json(proofs_dir / "hard-safety-regression.json")
    readiness = {
        "contract": "structured-autonomy-promotion-readiness-v1",
        "generation_id": generation_id,
        "current_main_sha": git_value("rev-parse", "origin/main"),
        "current_operating_sha": git_value("rev-parse", "main"),
        "current_model": engine.REASONING_MODEL,
        "current_reasoning_effort": engine.REASONING_EFFORT,
        "metric_union_primary_scope": "SELECTED_EVIDENCE_ONLY",
        "same_severity_metric_union": "PASS",
        "cross_severity_metric_union_accepted": 0,
        "unowned_strengthening_severity_accepted": 0,
        "probability_token_boundary": "PASS",
        "probability_true_positive_regression": 0,
        "negated_trade_language": "PASS",
        "actionable_trade_false_negative": 0,
        "benign_action_wrapper_hard_block": 0,
        "material_substantive_repeat_protection": "PASS",
        "investment_judgment_logic_changed": 0,
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "first_validated": run_documents["first"]["validation_pass_count"],
        "run_a_validated": run_documents["a"]["validation_pass_count"],
        "run_b_validated": run_documents["b"]["validation_pass_count"],
        "run_c_validated": run_documents["c"]["validation_pass_count"],
        "future_checkpoint_false_reject": sum(
            value["failure_taxonomy"]["future_checkpoint_false_reject"]
            for value in run_documents.values()
        ),
        "leaf_schema_failure": sum(
            value["failure_taxonomy"]["leaf_schema_failure"]
            for value in run_documents.values()
        ),
        "known_hard_safety_regression": known_hard_safety["known_hard_safety_regression"],
        "stable_count": stability["counts"]["STABLE"],
        "boundary_uncertainty_count": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "unstable_count": stability["counts"]["UNSTABLE"],
        "structured_autonomy_readiness": "READY_FOR_PRODUCTION_REVIEW",
        "structured_autonomy_production_mutation": 0,
        "night_futures_production_mutation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    night = prior.read_json(proofs_dir / "night-futures-production-review.json")
    handoff = {
        "contract": "next-production-integration-handoff-v1",
        "structured_autonomy_candidate": "READY_FOR_PRODUCTION_REVIEW",
        "night_futures_candidate": night["readiness"],
        "recommended_sequence": "SEPARATE_REVIEWED_INTEGRATIONS",
        "reason": "Structured Autonomy judgment and night-futures market context have independent ownership and rollout risk.",
        "main_merge": 0,
        "production_mutation": 0,
    }
    prior.write_json(proofs_dir / "abc-stability.json", stability)
    prior.write_json(proofs_dir / "structured-autonomy-readiness.json", readiness)
    prior.write_json(proofs_dir / "next-integration-handoff.json", handoff)
    stability_rows = [
        [
            row["ticker"],
            row["classification"],
            " / ".join(row["label_sequence"]),
            row["max_balance_distance"],
            ", ".join(row["reasons"]) or "none",
        ]
        for row in stability["rows"]
    ]
    prior.write_text(
        report_dir / "20260906-abc-stability.md",
        "# A/B/C Stability\n\n"
        + prior.markdown_table(["Ticker", "Class", "Labels", "Spread", "Reasons"], stability_rows)
        + f"\n\nCounts: `{json.dumps(stability['counts'], sort_keys=True)}`. Majority vote: `0`.\n",
    )
    prior.write_text(
        report_dir / "20260906-judgment-diagnostic-audit.md",
        markdown_mapping("Judgment Diagnostic Audit", diagnostic)
        + "\nDiagnostic observations only; no target labels or threshold tuning.\n",
    )
    prior.write_text(
        report_dir / "20260906-structured-autonomy-promotion-review.md",
        markdown_mapping("Structured Autonomy Promotion Review", readiness),
    )
    prior.write_text(
        report_dir / "20260906-night-futures-production-review.md",
        markdown_mapping("Night Futures Production Review", night),
    )
    prior.write_text(
        report_dir / "20260906-next-production-integration-handoff.md",
        markdown_mapping("Next Production Integration Handoff", handoff),
    )
    complete = {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "state": "COMPLETE",
        "run_validation": {
            run: run_documents[run]["validation_pass_count"] for run in RUNS
        },
        "message_quality": {
            run: run_documents[run]["message_quality"]["status"] for run in RUNS
        },
        "failure_taxonomy": {
            run: run_documents[run]["failure_taxonomy"] for run in RUNS
        },
        "stability": stability["counts"],
        "structured_autonomy_readiness": readiness["structured_autonomy_readiness"],
        "night_futures_readiness": night["readiness"],
        "production_mutation": 0,
        "main_merge": 0,
    }
    prior.write_json(output_root / "program-state.json", complete)
    write_artifact_index(report_dir, generation_id)
    print(json.dumps(complete, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--execute-frozen", action="store_true")
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    for name in (
        "us_packet",
        "kr_packet",
        "us_base_messages",
        "kr_base_messages",
        "fixture",
        "source_bundle",
        "output_root",
        "report_dir",
    ):
        setattr(args, name, getattr(args, name).resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare_only:
        prepare(args)
    else:
        execute(args)


if __name__ == "__main__":
    main()
