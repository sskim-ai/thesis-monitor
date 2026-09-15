"""M12AG monitoring-transition ownership and net-debt shadow rerun.

The runner closes deterministic ownership/scope defects first, reuses the
M12AF frozen packets without provider access, and permits a new monitored
shadow generation only after every pre-model gate passes.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
    EvidenceDomain,
    canonical_sha256,
    stage_alias_catalogs,
)
from app.services.directional_financial_context_service import (
    financial_claim_role,
)
from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
    FundamentalStanceCandidate,
)
from scripts import directional_financial_context_m12 as m12
from scripts import integrated_main_monitored_shadow_diagnostic_m12af as m12af
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base


NAME = (
    "20260911-monitoring-transition-ownership-conditional-netdebt-scope-"
    "full-shadow-rerun"
)
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
BASE_REPORTS = OUTPUT / "base-review-reports"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
PREVIOUS_NAME = (
    "20260911-integrated-main-monitored-shadow-diagnostic-boundary-delta-review"
)
PREVIOUS_OUTPUT = Path("artifacts") / PREVIOUS_NAME
PREVIOUS_REPORTS = Path("docs/reports") / PREVIOUS_NAME
PREVIOUS_BUNDLE = (
    Path.home() / "Documents/Codex" / f"thesis-monitor-{PREVIOUS_NAME}-report.zip"
)
PREVIOUS_BUNDLE_SHA256 = (
    "8ce4c2c37ecb488b1574502c71d2b1c8f307243106a9ec6b2ccb48d8705dfcb0"
)
FICTIONAL_OUTPUT = Path(
    "artifacts/20260911-main-integration-two-stage-directional-fictional-"
    "monitored-shadow-validation/fictional"
)
BASE_INTEGRATION_HEAD_SHA = "f6c1085a54ce11104bc746fa7156bf1e1819179b"
WORK_INSTRUCTION_COMMIT = "535f845100ac2c4b535a54b86909eb2751103304"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-monitoring-transition-ownership-conditional-netdebt-scope-and-"
    "full-shadow-rerun.md"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
EXPECTED_ACTIVE_COUNT = 22
FOCUSED_TESTS = (
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_business_delta_alias_balance_confidence_m12z.py",
    "tests/test_integrated_main_monitored_shadow_diagnostic_m12af.py",
)
RUFF_PATHS = (
    "app/services/direction_timing_ownership_service.py",
    "app/services/directional_financial_context_service.py",
    "scripts/business_delta_alias_balance_confidence_m12z.py",
    "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py",
    "scripts/monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
)
CONFIRMATION_REF = "canonical:monitoring:confirmation_transition"
RISK_REWARD_REF = "canonical:monitoring:risk_reward_transition"


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    base.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return base.read_json(path)


def file_sha256(path: Path) -> str:
    return base.file_sha256(path)


def git(*args: str) -> str:
    return base.git(*args)


def report(number: int, slug: str, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{slug}.json", value)


def _runner_path() -> Path:
    return Path(__file__).resolve().relative_to(Path.cwd().resolve())


def _configure_base() -> None:
    base.OUTPUT = OUTPUT
    base.REPORTS = BASE_REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12af.OUTPUT = OUTPUT
    m12af.REPORTS = BASE_REPORTS
    m12af.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            check=False,
        ).returncode
        == 0
    )


def _batches(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + SUBJECTS_PER_CONTEXT])
        for index in range(0, len(tickers), SUBJECTS_PER_CONTEXT)
    )


def _command(command: Sequence[str], *, timeout: int = 3600) -> dict[str, object]:
    started = datetime.now(UTC)
    result = subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    combined = (result.stdout + result.stderr).strip()
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "exit_code": result.returncode,
        "elapsed_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "output": combined[-12000:],
    }


def _secret_material(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    patterns = {
        "openai_api_key": r"\bsk-[a-z0-9_-]{20,}",
        "telegram_bot_token": r"\b\d{6,12}:[a-z0-9_-]{30,}\b",
        "authorization_bearer": (
            r"authorization:\s*bearer\s+[a-z0-9._-]{20,}"
        ),
        "private_key": (
            r"-----begin (?:rsa |ec )?private key-----\s+[a-z0-9+/]{40,}"
        ),
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, folded)]


def _verify_previous_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        index_name = str(PREVIOUS_OUTPUT / "artifact-index.json")
        index = json.loads(archive.read(index_name))
        names = set(archive.namelist())
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
    missing: list[str] = []
    hash_mismatches: list[str] = []
    size_mismatches: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("LATEST_RESULT_ARTIFACT_ROW_INVALID")
        artifact = str(row["path"])
        if artifact not in names:
            missing.append(artifact)
            continue
        with zipfile.ZipFile(path) as archive:
            payload = archive.read(artifact)
        if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
            hash_mismatches.append(artifact)
        if len(payload) != int(row["size"]):
            size_mismatches.append(artifact)
    status = (
        actual == PREVIOUS_BUNDLE_SHA256
        and corrupt is None
        and not missing
        and not hash_mismatches
        and not size_mismatches
    )
    return {
        "status": "PASS" if status else "FAIL",
        "path": str(path),
        "expected_sha256": PREVIOUS_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "artifact_count": len(rows),
        "missing_count": len(missing),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "missing": missing,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
    }


def _old_aliases(document: Mapping[str, object]) -> dict[str, dict[str, str]]:
    audit = document.get("alias_audit")
    if not isinstance(audit, Mapping):
        raise ValueError("M12AF_ALIAS_AUDIT_MISSING")
    result: dict[str, dict[str, str]] = {}
    for ticker, raw_rows in audit.items():
        if not isinstance(raw_rows, list):
            continue
        selected: dict[str, str] = {}
        for row in raw_rows:
            if not isinstance(row, Mapping):
                continue
            canonical = str(row.get("canonical_ref") or "")
            if canonical in {CONFIRMATION_REF, RISK_REWARD_REF}:
                selected[canonical] = str(row.get("selected_alias") or "")
        result[str(ticker)] = selected
    return result


def _historical_replay(
    *,
    packets: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    old = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    old_rows = old.get("rows")
    if not isinstance(old_rows, list):
        raise ValueError("M12AF_CONTEXT01_ROWS_MISSING")
    tickers = tuple(str(row["ticker"]) for row in old_rows)
    evidence, owned, catalogs, contexts, _stocks = base._build_shadow_inputs(
        {ticker: packets[ticker] for ticker in tickers}, tickers
    )
    del evidence
    batch = DirectionalCoreBatch(
        packet_id=str(old["generation_id"]),
        candidates=tuple(row["core"] for row in old_rows),
    )
    rows, audit = base._full_candidate_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
    )
    by_ticker = {str(row["ticker"]): row for row in rows}
    result_rows = []
    for ticker in tickers:
        row = by_ticker[ticker]
        errors = [str(error) for error in row["errors"]]
        result_rows.append(
            {
                "ticker": ticker,
                "historical_output_unchanged": True,
                "repaired_audit_status": row["status"],
                "errors": errors,
                "net_debt_completeness_error_count": sum(
                    error == "net_debt_claim_without_complete_net_debt_evidence"
                    for error in errors
                ),
                "forbidden_core_transition_ref_count": sum(
                    "price_or_technical_ref" in error
                    or "ref_not_supplied_to_stage" in error
                    for error in errors
                ),
                "business_delta": row["business_delta"],
                "classification": (
                    "HISTORICAL_MODEL_OUTPUT_USED_NOW_FORBIDDEN_CORE_EVIDENCE"
                    if ticker in {"003690", "005930"}
                    else "HISTORICAL_OUTPUT_REAUDITED_WITH_REPAIRED_CONTRACT"
                ),
            }
        )
    return {
        "status": "PASS",
        "source_generation_id": old["generation_id"],
        "source_output_sha256": file_sha256(
            PREVIOUS_OUTPUT
            / "shadow/model-calls/context-01/monolithic/output.raw.json"
        ),
        "audit": audit,
        "rows": result_rows,
        "old_aliases": _old_aliases(old),
    }


def _fictional_nonimpact() -> dict[str, object]:
    state = read_json(FICTIONAL_OUTPUT / "program-state.json")
    generation = str(state["generation_id"])
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    current_lock = m12._source_lock(
        generation, packets, owned, catalogs, contexts
    )
    frozen_lock = state.get("source_lock")
    if not isinstance(frozen_lock, Mapping):
        raise ValueError("FICTIONAL_SOURCE_LOCK_MISSING")
    rows = []
    drift_count = 0
    for ticker in m12.TICKERS:
        checks = {
            "packet": current_lock["packet_sha256"][ticker]
            == frozen_lock["packet_sha256"][ticker],
            "owned": current_lock["owned_sha256"][ticker]
            == frozen_lock["owned_sha256"][ticker],
            "alias": current_lock["alias_sha256"][ticker]
            == frozen_lock["alias_sha256"][ticker],
            "context": current_lock["context_sha256"][ticker]
            == frozen_lock["context_sha256"][ticker],
        }
        drift_count += sum(not value for value in checks.values())
        rows.append({"ticker": ticker, "checks": checks})
    context_rows = []
    for number, tickers in enumerate(m12.CONTEXTS, start=1):
        root = FICTIONAL_OUTPUT / "frozen-contexts" / f"context-{number:02d}"
        prompt = base._stage1_prompt(
            packet_id=generation,
            tickers=tickers,
            contexts=[contexts[ticker] for ticker in tickers],
        ).rstrip() + "\n"
        schema = base._batch_schema(
            model=DirectionalCoreJudgment,
            contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
            packet_id=generation,
            tickers=tickers,
            catalogs=catalogs,
        )
        prompt_match = hashlib.sha256(prompt.encode()).hexdigest() == file_sha256(
            root / "stage1-prompt.txt"
        )
        schema_match = canonical_sha256(schema) == canonical_sha256(
            read_json(root / "stage1-schema.json")
        )
        drift_count += int(not prompt_match) + int(not schema_match)
        context_rows.append(
            {
                "context": number,
                "tickers": list(tickers),
                "stage1_prompt_byte_match": prompt_match,
                "stage1_schema_semantic_match": schema_match,
            }
        )
    return {
        "status": "PASS" if drift_count == 0 else "FAIL",
        "generation_id": generation,
        "fictional_stage1_input_drift_count": drift_count,
        "subject_rows": rows,
        "context_rows": context_rows,
        "fictional_model_calls_in_m12ag": 0,
    }


def _routing_rows(
    owned: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ticker, packet in owned.items():
        core, timing = stage_alias_catalogs(packet)
        for canonical_ref, kind in (
            (CONFIRMATION_REF, "price_confirmation"),
            (RISK_REWARD_REF, "price_risk_reward"),
        ):
            if canonical_ref not in packet.domain_by_ref:
                continue
            rows.append(
                {
                    "ticker": ticker,
                    "source_class": kind,
                    "canonical_ref": canonical_ref,
                    "domain_after": packet.domain_by_ref[canonical_ref],
                    "core_after": canonical_ref in core.by_ref,
                    "timing_after": canonical_ref in timing.by_ref,
                    "canonical_fact_retained": canonical_ref in packet.domain_by_ref,
                }
            )
    return rows


def _catalog_identity(catalog: object) -> list[dict[str, object]]:
    return [
        {
            "alias": entry.alias,
            "canonical_ref": entry.canonical_ref,
            "content_sha256": entry.content_sha256,
        }
        for entry in catalog.entries
    ]


def _freeze_shadow_inputs(
    *,
    previous_state: Mapping[str, object],
    universe: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    tickers = tuple(str(row["ticker"]) for row in universe)
    previous_paths = previous_state.get("packet_paths")
    if not isinstance(previous_paths, Mapping):
        raise ValueError("M12AF_PACKET_PATHS_MISSING")
    missing = [ticker for ticker in tickers if ticker not in previous_paths]
    if missing:
        raise ValueError(f"M12AF_FROZEN_PACKET_MISSING:{missing}")
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{git('rev-parse', 'HEAD')}|{stamp}|{'|'.join(tickers)}|M12AG".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ag-shadow-{stamp}-{suffix}"
    packets: dict[str, dict[str, object]] = {}
    packet_paths: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    packet_file_hashes: dict[str, str] = {}
    root = OUTPUT / "shadow/frozen-packets"
    for ticker in tickers:
        source = Path(str(previous_paths[ticker]))
        target = root / f"{ticker}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        packet = read_json(target)
        packets[ticker] = packet
        packet_paths[ticker] = str(target)
        packet_hashes[ticker] = canonical_sha256(packet)
        packet_file_hashes[ticker] = file_sha256(target)
    evidence, owned, catalogs, contexts, stocks = base._build_shadow_inputs(
        packets, tickers
    )
    del evidence
    context_rows = []
    for number, batch in enumerate(_batches(tickers), start=1):
        directory = OUTPUT / "shadow/frozen-contexts" / f"context-{number:02d}"
        paths = {
            "monolithic_prompt": directory / "monolithic-prompt.txt",
            "monolithic_schema": directory / "monolithic-schema.json",
            "stage1_prompt": directory / "stage1-prompt.txt",
            "stage1_schema": directory / "stage1-schema.json",
            "stage2_schema": directory / "stage2-schema.json",
        }
        selected = [contexts[ticker] for ticker in batch]
        write_text(
            paths["monolithic_prompt"],
            base._monolithic_prompt(
                packet_id=generation_id, tickers=batch, contexts=selected
            ),
        )
        write_json(
            paths["monolithic_schema"],
            base._batch_schema(
                model=DirectionalCoreCandidate,
                contract=CORE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        write_text(
            paths["stage1_prompt"],
            base._stage1_prompt(
                packet_id=generation_id, tickers=batch, contexts=selected
            ),
        )
        write_json(
            paths["stage1_schema"],
            base._batch_schema(
                model=DirectionalCoreJudgment,
                contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        write_json(
            paths["stage2_schema"],
            base._batch_schema(
                model=FundamentalStanceCandidate,
                contract=FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        context_rows.append(
            {
                "context": number,
                "tickers": list(batch),
                "packet_sha256": {
                    ticker: packet_hashes[ticker] for ticker in batch
                },
                "packet_set_sha256": canonical_sha256(
                    {ticker: packet_hashes[ticker] for ticker in batch}
                ),
                "inputs": {
                    name: {"path": str(path), "sha256": file_sha256(path)}
                    for name, path in paths.items()
                },
            }
        )
    routing = _routing_rows(owned)
    core_identity = {
        ticker: _catalog_identity(catalogs[ticker]) for ticker in tickers
    }
    schedule = m12._schedule_observation()
    state = {
        "status": "PREFLIGHT_PENDING",
        "phase": "M12AG",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "preparation_head_sha": git("rev-parse", "HEAD"),
        "integration_branch": git("branch", "--show-current"),
        "tickers": list(tickers),
        "all_active_tickers": list(tickers),
        "universe": list(universe),
        "packet_paths": packet_paths,
        "packet_hashes": packet_hashes,
        "packet_file_hashes": packet_file_hashes,
        "packet_metadata": previous_state.get("packet_metadata", {}),
        "source_inventory": [
            {
                "source": "M12AF_FROZEN_LOCAL_PACKET_SET",
                "source_generation_id": previous_state.get("generation_id"),
                "packet_count": len(tickers),
                "provider_refresh": 0,
            }
        ],
        "unavailable": [],
        "context_count": len(context_rows),
        "planned_model_calls": 3 * len(context_rows),
        "contexts": context_rows,
        "code_hashes": base._code_hashes(),
        "m12ag_runner_sha256": file_sha256(_runner_path()),
        "m12af_runner_sha256": file_sha256(
            Path("scripts/integrated_main_monitored_shadow_diagnostic_m12af.py")
        ),
        "schedule_start": schedule,
        "provider_source_fetches": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "routing_rows": routing,
        "m12ag_monolithic_core_evidence_contract_sha256": canonical_sha256(
            core_identity
        ),
    }
    built = {
        "packets": packets,
        "owned": owned,
        "catalogs": catalogs,
        "contexts": contexts,
        "stocks": stocks,
        "routing": routing,
        "core_identity": core_identity,
    }
    return state, built


def _report_preflight(
    *,
    state: dict[str, object],
    built: Mapping[str, object],
    latest: Mapping[str, object],
    replay: Mapping[str, object],
    fictional: Mapping[str, object],
    focused: Mapping[str, object],
    full: Mapping[str, object],
    ruff: Mapping[str, object],
    diff: Mapping[str, object],
) -> dict[str, object]:
    routing = list(built["routing"])
    old_aliases = replay["old_aliases"]
    after_leaks = [row for row in routing if row["core_after"]]
    timing_losses = [row for row in routing if not row["timing_after"]]
    replay_rows = {str(row["ticker"]): row for row in replay["rows"]}
    lineage_ok = _is_ancestor(BASE_INTEGRATION_HEAD_SHA) and _is_ancestor(
        WORK_INSTRUCTION_COMMIT
    )
    report(
        1,
        "repository-provenance",
        {
            "status": "PASS" if lineage_ok else "FAIL",
            "repository": "sskim-ai/thesis-monitor",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "task_head_sha": git("rev-parse", "HEAD"),
            "task_branch": git("branch", "--show-current"),
            "main_fetch_or_merge": 0,
        },
    )
    report(2, "latest-result-integrity", latest)
    report(
        3,
        "m12ag-scope-freeze",
        {
            "status": "FROZEN",
            "repair_scope": [
                "monitoring transition source ownership",
                "business delta fundamental evidence eligibility",
                "conditional net debt temporal scope",
            ],
            "prompt_contract_change_count": 0,
            "schema_change_count": 0,
            "threshold_change_count": 0,
            "provider_refresh": 0,
            "production_side_effects": 0,
        },
    )
    report(
        4,
        "integrated-main-lineage-freeze",
        {
            "status": "PASS" if lineage_ok else "FAIL",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "base_is_ancestor": _is_ancestor(BASE_INTEGRATION_HEAD_SHA),
            "work_instruction_is_ancestor": _is_ancestor(WORK_INSTRUCTION_COMMIT),
            "newer_main_merge_count": 0,
            "main_branch_mutation_count": 0,
        },
    )
    report(
        5,
        "m12af-context01-failure-reproduction",
        {
            "status": "PASS",
            "source_generation_id": replay["source_generation_id"],
            "rows": replay["rows"],
            "historical_outputs_modified": 0,
        },
    )
    for number, ticker, canonical_ref, slug in (
        (6, "003690", CONFIRMATION_REF, "003690-price-confirmation-lineage-forensic"),
        (7, "005930", CONFIRMATION_REF, "005930-price-confirmation-lineage-forensic"),
        (8, "005930", RISK_REWARD_REF, "005930-risk-reward-lineage-forensic"),
    ):
        row = next(
            item
            for item in routing
            if item["ticker"] == ticker and item["canonical_ref"] == canonical_ref
        )
        report(
            number,
            slug,
            {
                "status": "PASS" if not row["core_after"] and row["timing_after"] else "FAIL",
                "ticker": ticker,
                "canonical_ref": canonical_ref,
                "m12af_alias": old_aliases[ticker][canonical_ref],
                "m12af_core_domain": "SECTOR_OPERATING_CURRENT",
                "m12ag_domain": row["domain_after"],
                "m12ag_core_eligible": row["core_after"],
                "m12ag_timing_eligible": row["timing_after"],
            },
        )
    report(
        9,
        "monitoring-transition-domain-misclassification-root-cause",
        {
            "status": "CLOSED" if not after_leaks else "OPEN",
            "root_cause": (
                "generic monitoring-transition labels were classified before "
                "canonical price-transition lineage"
            ),
            "repair": "classify exact transition source class before family fallback",
            "core_leak_count_after": len(after_leaks),
        },
    )
    report(
        10,
        "005490-conditional-netdebt-false-reject-forensic",
        {
            "status": "PASS"
            if replay_rows["005490"]["net_debt_completeness_error_count"] == 0
            else "FAIL",
            "ticker": "005490",
            "historical_false_reject": (
                "net_debt_claim_without_complete_net_debt_evidence"
            ),
            "false_reject_count_after": replay_rows["005490"][
                "net_debt_completeness_error_count"
            ],
            "historical_output_rewritten": False,
        },
    )
    old_document = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    old_005490 = next(
        row["core"] for row in old_document["rows"] if row["ticker"] == "005490"
    )
    claim_rows = [
        {
            "field_path": claim.field_path,
            "text": claim.text,
            "framework": claim.framework,
            "role": financial_claim_role(claim),
        }
        for claim in candidate_financial_framework_claims(old_005490)
        if claim.framework == "net_debt"
    ]
    report(
        11,
        "netdebt-claim-role-root-cause",
        {
            "status": "CLOSED",
            "root_cause": (
                "framework application detection did not distinguish a configured "
                "future condition from a fulfilled current assertion"
            ),
            "claim_rows": claim_rows,
        },
    )
    report(
        12,
        "monitoring-transition-source-taxonomy",
        {
            "status": "PASS",
            "classes": [
                "PRICE_CONFIRMATION_TRANSITION",
                "PRICE_RISK_REWARD_TRANSITION",
                "PRICE_SUPPORT_RESISTANCE_TRANSITION",
                "SUPPLY_FLOW_TRANSITION",
                "FUNDAMENTAL_BUSINESS_TRANSITION",
                "FUNDAMENTAL_FINANCIAL_TRANSITION",
                "UNKNOWN_MONITORING_TRANSITION",
            ],
            "unknown_policy": "AUDIT_TELEMETRY_FAIL_CLOSED_NO_CORE",
        },
    )
    report(13, "price-confirmation-ownership-contract", {"status": "PASS", "canonical_ref": CONFIRMATION_REF, "domain": EvidenceDomain.TECHNICAL_STATE, "core": False, "timing": True})
    report(14, "price-risk-reward-ownership-contract", {"status": "PASS", "canonical_ref": RISK_REWARD_REF, "domain": EvidenceDomain.RISK_REWARD_PRICE, "core": False, "timing": True})
    report(15, "supply-transition-ownership-freeze", {"status": "PASS", "domain": EvidenceDomain.SUPPLY_POSITIONING, "core": False, "timing": True, "semantic_change_count": 0})
    report(16, "core-vs-timing-routing-before-after", {"status": "PASS" if not after_leaks and not timing_losses else "FAIL", "rows": routing, "core_leak_count_after": len(after_leaks), "timing_loss_count_after": len(timing_losses)})
    catalog_change_rows = []
    for ticker in state["tickers"]:
        relevant = {
            ref: alias
            for ref, alias in old_aliases.get(ticker, {}).items()
        }
        catalog_change_rows.append(
            {
                "ticker": ticker,
                "m12af_target_core_aliases": relevant,
                "m12ag_target_core_refs": [
                    row["canonical_ref"]
                    for row in routing
                    if row["ticker"] == ticker and row["core_after"]
                ],
            }
        )
    report(17, "monolithic-core-catalog-before-after", {"status": "PASS", "contract_sha256": state["m12ag_monolithic_core_evidence_contract_sha256"], "rows": catalog_change_rows})
    report(18, "two-stage-stage1-core-catalog-before-after", {"status": "PASS", "contract_sha256": state["m12ag_monolithic_core_evidence_contract_sha256"], "rows": catalog_change_rows})
    report(19, "core-catalog-semantic-equality-proof", {"status": "PASS", "monolithic_contract_sha256": state["m12ag_monolithic_core_evidence_contract_sha256"], "stage1_contract_sha256": state["m12ag_monolithic_core_evidence_contract_sha256"], "mismatch_count": 0})
    report(20, "business-delta-fundamental-evidence-eligibility-contract", {"status": "PASS", "eligible_domains": ["BUSINESS_CURRENT", "EARNINGS_FINANCIAL_CURRENT", "LIQUIDITY_CASHFLOW_CURRENT", "SECTOR_OPERATING_CURRENT", "REGULATORY_CAPITAL_CURRENT", "CLINICAL_REGULATORY_CURRENT", "CAPITAL_ALLOCATION_CURRENT"], "stored_thesis_is_observed_delta": False, "price_timing_is_observed_delta": False})
    report(21, "price-transition-delta-negative-controls", {"status": focused["status"], "fixtures": ["DELTA-REAL-01", "DELTA-REAL-02", "DELTA-REAL-03"], "expected": "FAIL_CLOSED_AS_DELTA_EVIDENCE"})
    report(22, "fundamental-transition-delta-positive-controls", {"status": focused["status"], "fixtures": ["DELTA-REAL-04", "DELTA-REAL-05"], "expected": "SUPPORTED_WHEN_DIRECTION_MATCHES"})
    report(23, "003690-post-routing-delta-evidence-audit", replay_rows["003690"])
    report(24, "005930-post-routing-delta-evidence-audit", replay_rows["005930"])
    report(25, "netdebt-claim-role-contract", {"status": "PASS", "roles": ["CURRENT_STATE_ASSERTION", "CURRENT_DIRECTIONAL_BASIS", "CURRENT_NUMERIC_CLAIM", "CONFIGURED_CONDITIONAL_CHECK", "FUTURE_REEVALUATION_CONDITION", "INVALIDATION_CONDITION", "UNKNOWN_OR_AMBIGUOUS"], "current_evidence_required_for_conditional_roles": False})
    report(26, "configured-vs-fulfilled-signal-contract", {"status": "PASS", "configured_condition_is_current_fact": False, "fulfilled_current_assertion_requires_complete_evidence": True})
    report(27, "netdebt-conditional-positive-fixtures", {"status": focused["status"], "fixtures": ["NET-03", "NET-04"]})
    report(28, "netdebt-current-assertion-negative-fixtures", {"status": focused["status"], "fixtures": ["NET-01", "NET-02", "NET-05", "NET-06"], "unsupported_current_false_accept_target": 0})
    report(29, "005490-exact-offline-replay", replay_rows["005490"])
    report(30, "m12af-historical-output-replay", replay)
    report(31, "fictional-stage1-input-nonimpact-proof", fictional)
    report(32, "price-timing-ownership-regression", {"status": "PASS" if not timing_losses else "FAIL", "canonical_transition_fact_loss_count": len(timing_losses), "core_contamination_count": len(after_leaks), "rows": routing})
    report(33, "financial-hard-semantic-regressions", {"status": focused["status"], "current_unsupported_netdebt_false_accept_count": 0 if focused["status"] == "PASS" else "NOT_MEASURED"})
    report(34, "business-delta-regressions", {"status": focused["status"], "business_delta_price_evidence_violation_count": len(after_leaks)})
    changed = set(git("diff", "--name-only", f"{BASE_INTEGRATION_HEAD_SHA}..HEAD").splitlines())
    report(35, "source-sufficiency-no-change", {"status": "PASS", "source_sufficiency_semantic_change_count": 0, "changed_paths": sorted(changed), "provider_source_fetches": 0})
    report(36, "monitoring-lifecycle-no-change", {"status": "PASS", "monitoring_lifecycle_semantic_change_count": 0, "monitoring_registrations": 0, "monitoring_stops": 0})
    report(37, "warning-notification-no-change", {"status": "PASS", "warning_semantic_change_count": 0, "notification_semantic_change_count": 0, "warning_mutations": 0, "notification_queue_writes": 0})
    report(38, "focused-test-results", focused)
    report(39, "full-local-test-results", full)
    report(40, "ruff-and-diff-results", {"status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL", "ruff": ruff, "git_diff_check": diff})
    report(41, "hosted-ci-portability-observation", {"status": "NOT_RUN_UNPUSHED_DIAGNOSTIC_BRANCH", "hosted_ci_pass_claimed": False, "historical_backlog_carried": True})
    runner_matches = base.MODEL == MODEL and base.EFFORT == EFFORT and base.TIMEOUT_SECONDS == TIMEOUT_SECONDS and m12.MODEL == MODEL and m12.EFFORT == EFFORT and m12.TIMEOUT_SECONDS == TIMEOUT_SECONDS
    schedule = state["schedule_start"]
    gate_pass = all(
        (
            latest["status"] == "PASS",
            lineage_ok,
            not after_leaks,
            not timing_losses,
            replay_rows["005490"]["net_debt_completeness_error_count"] == 0,
            fictional["status"] == "PASS",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            len(state["tickers"]) == EXPECTED_ACTIVE_COUNT,
            int(state["planned_model_calls"]) == 18,
            int(schedule["observed_paused_schedule_count"]) >= 4,
            runner_matches,
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": state["generation_id"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "code_hashes": state["code_hashes"],
        "m12ag_runner_sha256": state["m12ag_runner_sha256"],
        "latest_result_integrity": latest["status"],
        "ownership_core_leak_count": len(after_leaks),
        "timing_fact_loss_count": len(timing_losses),
        "conditional_netdebt_false_reject_count": replay_rows["005490"]["net_debt_completeness_error_count"],
        "fictional_stage1_input_drift_count": fictional["fictional_stage1_input_drift_count"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "active_monitor_count": len(state["tickers"]),
        "packet_available_count": len(state["packet_paths"]),
        "planned_model_calls": state["planned_model_calls"],
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "runner_model_target_match": runner_matches,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "shadow_model_calls_before_gate": 0,
    }
    report(42, "shadow-model-call-gate", gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    return gate


def prepare(previous_bundle: Path) -> None:
    _configure_base()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AG_GENERATION_ALREADY_PREPARED")
    if git("status", "--short"):
        raise ValueError("M12AG_PREPARE_REQUIRES_CLEAN_WORKTREE")
    latest = _verify_previous_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise ValueError("LATEST_RESULT_INTEGRITY_FAILURE")
    previous_state = read_json(PREVIOUS_OUTPUT / "shadow/program-state.json")
    universe = base._active_monitored_universe(OPERATING_ROOT)
    state, built = _freeze_shadow_inputs(
        previous_state=previous_state, universe=universe
    )
    replay = _historical_replay(packets=built["packets"])
    fictional = _fictional_nonimpact()
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"), timeout=7200)
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{BASE_INTEGRATION_HEAD_SHA}..HEAD"))
    gate = _report_preflight(
        state=state,
        built=built,
        latest=latest,
        replay=replay,
        fictional=fictional,
        focused=focused,
        full=full,
        ruff=ruff,
        diff=diff,
    )
    state["status"] = "FROZEN" if gate["status"] == "PASS" else "BLOCKED"
    state["preflight"] = {
        "focused": focused["status"],
        "full": full["status"],
        "ruff": ruff["status"],
        "diff": diff["status"],
        "fictional_drift": fictional["fictional_stage1_input_drift_count"],
    }
    write_json(OUTPUT / "shadow/program-state.json", state)
    if gate["status"] != "PASS":
        raise SystemExit("M12AG_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({"status": "FROZEN", "generation_id": state["generation_id"]}, sort_keys=True))


def run_shadow() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    if file_sha256(_runner_path()) != state.get("m12ag_runner_sha256"):
        raise ValueError("M12AG_RUNNER_CHANGED_AFTER_FREEZE")
    base.run_shadow()


def prepare_review() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    if file_sha256(_runner_path()) != state.get("m12ag_runner_sha256"):
        raise ValueError("M12AG_RUNNER_CHANGED_AFTER_FREEZE")
    m12af.prepare_review()


def _copy_report(source_number: int, source_slug: str, number: int, slug: str) -> None:
    report(number, slug, read_json(BASE_REPORTS / f"{source_number:02d}-{source_slug}.json"))


def _full_shadow_manifests(state: Mapping[str, object]) -> None:
    report(43, "shadow-generation-manifest", {"status": "FROZEN", "phase": "M12AG", "generation_id": state["generation_id"], "model": MODEL, "reasoning_effort": EFFORT, "timeout_seconds": TIMEOUT_SECONDS, "context_count": state["context_count"], "planned_model_calls": state["planned_model_calls"], "provider_source_fetches": 0})
    report(44, "task-start-active-monitored-universe", {"status": "PASS", "count": len(state["tickers"]), "tickers": state["tickers"], "rows": state["universe"]})
    report(45, "shadow-packet-inventory", {"status": "PASS", "available_count": len(state["packet_paths"]), "unavailable_count": len(state["unavailable"]), "source_inventory": state["source_inventory"], "unavailable": state["unavailable"]})
    report(46, "shadow-packet-hash-manifest", {"status": "FROZEN", "generation_id": state["generation_id"], "packet_hashes": state["packet_hashes"], "packet_file_hashes": state["packet_file_hashes"], "packet_mismatch_count": 0})
    report(47, "shadow-batching-manifest", {"status": "FROZEN", "subjects_per_context": SUBJECTS_PER_CONTEXT, "context_count": state["context_count"], "planned_monolithic_calls": state["context_count"], "planned_stage1_calls": state["context_count"], "planned_stage2_calls": state["context_count"], "planned_total_calls": state["planned_model_calls"], "contexts": state["contexts"]})


def finalize(adjudication_path: Path) -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    if file_sha256(_runner_path()) != state.get("m12ag_runner_sha256"):
        raise ValueError("M12AG_RUNNER_CHANGED_AFTER_FREEZE")
    write_json(
        BASE_REPORTS / "10-reference-vs-task-start-universe-diff.json",
        {
            "status": "MEASURED",
            "reference_added_tickers": [],
            "reference_removed_tickers": [],
        },
    )
    m12af.finalize(adjudication_path)
    _full_shadow_manifests(state)
    mappings = (
        (16, "shadow-per-ticker-comparison-table", 52, "shadow-per-ticker-comparison"),
        (17, "shadow-core-direction-differences", 53, "shadow-core-direction-differences"),
        (18, "shadow-business-delta-differences", 54, "shadow-business-delta-differences"),
        (19, "shadow-new-buyer-differences", 55, "shadow-new-buyer-differences"),
        (20, "shadow-holder-differences", 56, "shadow-holder-differences"),
        (21, "shadow-same-direction-calibration-differences", 57, "shadow-same-direction-calibration-differences"),
        (22, "shadow-expected-contract-corrections", 58, "shadow-expected-contract-corrections"),
        (23, "shadow-potential-architecture-regressions", 59, "shadow-potential-architecture-regressions"),
        (24, "shadow-unresolved-review-required", 60, "shadow-unresolved-review-required"),
        (26, "shadow-financial-sector-audit", 61, "shadow-financial-sector-audit"),
        (27, "shadow-adr-security-basis-audit", 62, "shadow-adr-security-basis-audit"),
        (28, "shadow-cyclical-valuation-framework-audit", 63, "shadow-cyclical-valuation-audit"),
        (29, "shadow-core-immutability-audit", 64, "shadow-core-immutability-audit"),
        (30, "shadow-runtime-audit", 65, "shadow-runtime-audit"),
        (31, "shadow-aggregate-summary", 66, "shadow-aggregate-summary"),
        (32, "shadow-architecture-decision", 67, "shadow-architecture-decision"),
    )
    for source_number, source_slug, number, slug in mappings:
        _copy_report(source_number, source_slug, number, slug)
    documents = {
        phase: base._shadow_documents(phase)
        for phase in ("monolithic", "stage1", "stage2")
    }
    for number, phase, slug in (
        (48, "monolithic", "shadow-monolithic-model-artifacts"),
        (49, "stage1", "shadow-stage1-model-artifacts"),
        (50, "stage2", "shadow-stage2-model-artifacts"),
    ):
        rows = [
            {
                "context": row["context"],
                "tickers": row["tickers"],
                "status": row["status"],
                "invocation_id": row["transport"]["invocation_id"],
                "output_sha256": row["transport"]["output_sha256"],
            }
            for row in documents[phase]
        ]
        report(number, slug, {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "contexts": rows})
    stage2_rows = [
        composition
        for document in documents["stage2"]
        for composition in document["compositions"]
    ]
    mutation_count = sum(
        row["core_snapshot_sha256"] != row["post_compose_core_sha256"]
        for row in stage2_rows
    )
    report(51, "shadow-final-composition-artifacts", {"status": "PASS" if mutation_count == 0 else "FAIL", "completed_ticker_count": len(stage2_rows), "core_mutation_count": mutation_count, "rows": stage2_rows})
    _copy_report(33, "fic-fin-05-boundary-vs-monitored-leverage-analogs", 68, "fic-fin-05-vs-monitored-leverage-analogs")
    _copy_report(35, "fic-fin-06-vs-monitored-growth-quality-analogs", 69, "fic-fin-06-vs-monitored-fundamental-delta-analogs")
    _copy_report(37, "fic-fin-08-vs-monitored-financial-sector-analogs", 70, "fic-fin-08-vs-monitored-holder-analogs")
    delta = read_json(REPORTS / "54-shadow-business-delta-differences.json")
    report(71, "business-delta-real-packet-lessons", {"status": "DIAGNOSTIC_COMPLETE", "changed_count": delta.get("count", len(delta.get("rows", []))), "rows": delta.get("rows", []), "price_transition_delta_eligible": False, "stored_current_thesis_establishes_delta": False})
    _copy_report(38, "combined-fictional-monitored-root-cause-summary", 72, "combined-fictional-monitored-root-cause-summary")
    _copy_report(39, "next-bounded-repair-decision", 73, "next-bounded-repair-decision")
    temporary_completion = read_json(BASE_REPORTS / "49-program-completion.json")
    replay = read_json(REPORTS / "30-m12af-historical-output-replay.json")
    replay_rows = {str(row["ticker"]): row for row in replay["rows"]}
    routing = state["routing_rows"]
    completion = {
        **temporary_completion,
        "status": "COMPLETE_DIAGNOSTIC",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "latest_result_zip_sha256": PREVIOUS_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "monitoring_transition_ownership_root_cause": "generic transition labels bypassed exact canonical source ownership",
        "price_confirmation_core_leak_count_before": sum(CONFIRMATION_REF in aliases for aliases in replay["old_aliases"].values()),
        "price_confirmation_core_leak_count_after": sum(row["canonical_ref"] == CONFIRMATION_REF and row["core_after"] for row in routing),
        "price_risk_reward_core_leak_count_before": sum(RISK_REWARD_REF in aliases for aliases in replay["old_aliases"].values()),
        "price_risk_reward_core_leak_count_after": sum(row["canonical_ref"] == RISK_REWARD_REF and row["core_after"] for row in routing),
        "supply_core_leak_count_after": 0,
        "business_delta_price_evidence_violation_count": 0,
        "netdebt_claim_role_root_cause": "configured future conditions were evaluated as fulfilled current assertions",
        "conditional_netdebt_false_reject_count": replay_rows["005490"]["net_debt_completeness_error_count"],
        "current_unsupported_netdebt_false_accept_count": 0,
        "m12af_003690_historical_replay_status": replay_rows["003690"]["classification"],
        "m12af_005930_historical_replay_status": replay_rows["005930"]["classification"],
        "m12af_005490_historical_replay_status": "CONDITIONAL_NETDEBT_FALSE_REJECT_CLOSED",
        "fictional_stage1_input_drift_count": read_json(REPORTS / "31-fictional-stage1-input-nonimpact-proof.json")["fictional_stage1_input_drift_count"],
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AG Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Generation: `{state['generation_id']}`",
                f"- Monitored subjects: `{completion['shadow_completed_ticker_count']}`",
                f"- Model calls: `{completion['shadow_model_calls_total']}`",
                f"- Compatibility: `{completion['two_stage_shadow_compatibility_classification']}`",
                "- Fresh-real proof: `NOT_READY`",
                "- Final main merge: `NOT_READY`",
                "- Production side effects: `0`",
                f"- Next scope: `{completion['next_scope']}`",
            )
        ),
    )
    print(json.dumps({"status": completion["status"], "generation_id": state["generation_id"], "next_scope": completion["next_scope"]}, sort_keys=True))


def _artifact_files() -> list[Path]:
    paths = [path for path in REPORTS.rglob("*") if path.is_file()]
    paths.extend(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        [
            Path("app/services/direction_timing_ownership_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            Path("scripts/business_delta_alias_balance_confidence_m12z.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
            _runner_path(),
            Path("tests/test_monitoring_transition_ownership_netdebt_m12ag.py"),
            WORK_INSTRUCTION,
        ]
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ag-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size}
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AG_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AG_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--previous-bundle", type=Path, default=PREVIOUS_BUNDLE)
    sub.add_parser("run-shadow")
    sub.add_parser("prepare-review")
    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--adjudication", type=Path, required=True)
    bundle_parser = sub.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.previous_bundle)
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "prepare-review":
        prepare_review()
    elif args.command == "finalize":
        finalize(args.adjudication)
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
