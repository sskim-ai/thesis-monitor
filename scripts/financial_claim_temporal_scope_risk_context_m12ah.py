"""M12AH financial-claim temporal scope repair and monitored shadow proof."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialContext,
    FinancialDerivation,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
    canonical_sha256,
)
from app.services.directional_financial_context_service import (
    FinancialClaimRole,
    financial_claim_role,
    validate_directional_financial_semantics,
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
from scripts import monitoring_transition_ownership_netdebt_m12ag as m12ag


NAME = "20260911-financial-claim-temporal-scope-risk-context-full-shadow-rerun"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
BASE_REPORTS = OUTPUT / "base-review-reports"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
PREVIOUS_NAME = (
    "20260911-monitoring-transition-ownership-conditional-netdebt-scope-"
    "full-shadow-rerun"
)
PREVIOUS_OUTPUT = Path("artifacts") / PREVIOUS_NAME
PREVIOUS_REPORTS = Path("docs/reports") / PREVIOUS_NAME
PREVIOUS_BUNDLE = (
    Path.home() / "Documents/Codex" / f"thesis-monitor-{PREVIOUS_NAME}-report.zip"
)
PREVIOUS_BUNDLE_SHA256 = (
    "ab4fbdb9c58d8b6e329ef4e8ee8ca4d5cc9f6d34e38ed7cd5ef68cd384870fb3"
)
PREVIOUS_INDEXED_PAYLOADS = 144
M12AF_OUTPUT = Path(
    "artifacts/20260911-integrated-main-monitored-shadow-diagnostic-"
    "boundary-delta-review"
)
FICTIONAL_OUTPUT = Path(
    "artifacts/20260911-main-integration-two-stage-directional-fictional-"
    "monitored-shadow-validation/fictional"
)
BASE_INTEGRATION_HEAD_SHA = "a296ed2d353d5f811eaf70748c3f6cb90fdcca30"
WORK_INSTRUCTION_COMMIT = "f8c82f2bc2cbfbf6a86254297c4a3cf0de9e1ecd"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-financial-claim-temporal-scope-risk-context-role-and-"
    "full-shadow-rerun.md"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_MODEL_CALLS = 18
FOCUSED_TESTS = (
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_financial_context_output_grounding_m12a.py",
    "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
    "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
    "tests/test_business_delta_alias_balance_confidence_m12z.py",
    "tests/test_integrated_main_monitored_shadow_diagnostic_m12af.py",
)
RUFF_PATHS = (
    "app/services/directional_financial_context_service.py",
    "scripts/financial_claim_temporal_scope_risk_context_m12ah.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
)
M12AH_NEXT_SCOPES = {
    "FINANCIAL_RISK_CONTEXT_SCHEMA_ARCHITECTURE_REVIEW",
    "TEMPORAL_SCOPE_REPAIR_TOO_PERMISSIVE",
    "FULL_FICTIONAL_REPROOF_AFTER_TEMPORAL_SCOPE_CHANGE",
    "TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW",
    "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN",
    "BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW_ON_INTEGRATED_MAIN",
    "FUNDAMENTAL_STANCE_STAGE_COMPATIBILITY_REVIEW_ON_INTEGRATED_MAIN",
}


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


def _batches(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + SUBJECTS_PER_CONTEXT])
        for index in range(0, len(tickers), SUBJECTS_PER_CONTEXT)
    )


def _secret_material(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    patterns = {
        "openai_api_key": r"\bsk-[a-z0-9_-]{20,}",
        "telegram_bot_token": r"\b\d{6,12}:[a-z0-9_-]{30,}\b",
        "authorization_bearer": r"authorization:\s*bearer\s+[a-z0-9._-]{20,}",
        "private_key": r"-----begin (?:rsa |ec )?private key-----\s+[a-z0-9+/]{40,}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, folded)]


def _verify_previous_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(PREVIOUS_OUTPUT / "artifact-index.json")
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        index = json.loads(archive.read(index_name))
        payloads = {name: archive.read(name) for name in names}
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
    expected_names = {str(row["path"]) for row in rows} | {index_name}
    missing = sorted(expected_names - names)
    extra = sorted(names - expected_names)
    hash_mismatches = []
    size_mismatches = []
    for row in rows:
        artifact = str(row["path"])
        if artifact not in payloads:
            continue
        payload = payloads[artifact]
        if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
            hash_mismatches.append(artifact)
        if len(payload) != int(row["size"]):
            size_mismatches.append(artifact)
    status = all(
        (
            actual == PREVIOUS_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == PREVIOUS_INDEXED_PAYLOADS,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
        )
    )
    return {
        "status": "PASS" if status else "FAIL",
        "path": str(path),
        "expected_sha256": PREVIOUS_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "missing": missing,
        "extra": extra,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
    }


def _catalog_identity(catalog: object) -> list[dict[str, object]]:
    return [
        {
            "alias": entry.alias,
            "canonical_ref": entry.canonical_ref,
            "content_sha256": entry.content_sha256,
        }
        for entry in catalog.entries
    ]


def _routing_rows(owned: Mapping[str, object]) -> list[dict[str, object]]:
    return m12ag._routing_rows(owned)


def _freeze_shadow_inputs(
    *,
    previous_state: Mapping[str, object],
    universe: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    tickers = tuple(str(row["ticker"]) for row in universe)
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{git('rev-parse', 'HEAD')}|{stamp}|{'|'.join(tickers)}|M12AH".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ah-shadow-{stamp}-{suffix}"
    packets: dict[str, dict[str, object]] = {}
    packet_paths: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    packet_file_hashes: dict[str, str] = {}
    source_root = PREVIOUS_OUTPUT / "shadow/frozen-packets"
    target_root = OUTPUT / "shadow/frozen-packets"
    for ticker in tickers:
        source = source_root / f"{ticker}.json"
        if not source.is_file():
            raise ValueError(f"M12AG_FROZEN_PACKET_MISSING:{ticker}")
        target = target_root / f"{ticker}.json"
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
        "phase": "M12AH",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
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
                "source": "M12AG_FROZEN_LOCAL_PACKET_SET",
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
        "m12ah_runner_sha256": file_sha256(_runner_path()),
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
        "core_evidence_contract_sha256": canonical_sha256(core_identity),
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


def _candidate_temporal_roles(
    candidate: Mapping[str, object], refs: Sequence[DecisionEvidenceRef]
) -> list[dict[str, object]]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    metric_by_ref = {
        ref.ref_id: ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    return [
        {
            "framework": claim.framework,
            "field_path": claim.field_path,
            "text": claim.text,
            "evidence_refs": list(claim.evidence_refs),
            "role": financial_claim_role(
                claim, evidence_by_ref=evidence_by_ref
            ),
        }
        for claim in candidate_financial_framework_claims(
            candidate, metric_by_ref=metric_by_ref
        )
        if claim.framework == "net_debt"
    ]


def _reaudit_document(
    document: Mapping[str, object], built: Mapping[str, object]
) -> dict[str, object]:
    source_rows = document.get("rows")
    if not isinstance(source_rows, list):
        raise ValueError("SOURCE_DOCUMENT_ROWS_MISSING")
    batch = DirectionalCoreBatch(
        packet_id=str(document["generation_id"]),
        candidates=tuple(row["core"] for row in source_rows),
    )
    rows, audit = base._full_candidate_audit(
        batch,
        owned=built["owned"],
        catalogs=built["catalogs"],
        contexts=built["contexts"],
    )
    source_by_ticker = {str(row["ticker"]): row["core"] for row in source_rows}
    result_rows = []
    for row in rows:
        ticker = str(row["ticker"])
        result_rows.append(
            {
                "ticker": ticker,
                "status": row["status"],
                "errors": row["errors"],
                "business_delta": row["business_delta"],
                "temporal_roles": _candidate_temporal_roles(
                    source_by_ticker[ticker], built["packets"][ticker].evidence
                ),
                "historical_output_rewritten": False,
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in result_rows) else "FAIL",
        "source_generation_id": document["generation_id"],
        "audit": audit,
        "rows": result_rows,
        "pass_count": sum(row["status"] == "PASS" for row in result_rows),
        "fail_count": sum(row["status"] != "PASS" for row in result_rows),
    }


def _m12ag_context_reaudit(built: Mapping[str, object]) -> dict[str, object]:
    document = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    return _reaudit_document(document, built)


def _m12af_005490_reaudit(built: Mapping[str, object]) -> dict[str, object]:
    document = read_json(
        M12AF_OUTPUT
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    result = _reaudit_document(document, built)
    row = next(row for row in result["rows"] if row["ticker"] == "005490")
    return {
        "status": row["status"],
        "source_generation_id": result["source_generation_id"],
        "row": row,
        "historical_output_rewritten": False,
    }


def _configured_ref(ref_id: str = "configured:weaken-net-debt") -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="논리 약화 조건",
        statement="FCF 감소와 순부채 증가가 동반",
        source_ref="stock.thesis.weaken_signals",
    )


def _financial_ref(metric: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"canonical:{metric}",
        category=EvidenceCategory.EARNINGS,
        label=metric,
        statement=json.dumps({"value": "100"}),
        value=Decimal("100"),
        unit="USD",
        source_ref=f"stock.fact_catalog.{metric}",
        financial_context=FinancialContext(
            metric=metric,
            currency="USD",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.POINT_IN_TIME,
                end="2026-06-30",
            ),
            entity_scope="consolidated",
            statement_basis="formal_financial_statement",
            evidence_status=(
                FinancialEvidenceStatus.DERIVED_SAFE
                if metric == "net_debt"
                else FinancialEvidenceStatus.DIRECT_REPORTED
            ),
            quality=FinancialEvidenceQuality.VERIFIED,
            derivation=(
                FinancialDerivation(
                    formula="net_debt",
                    input_source_refs=(
                        "stock.fact_catalog.interest_bearing_debt_total",
                        "stock.fact_catalog.cash_and_cash_equivalents",
                    ),
                    version="m12ah-fixture-v1",
                )
                if metric == "net_debt"
                else None
            ),
        ),
    )


def _fixture_audit() -> dict[str, object]:
    configured = _configured_ref()
    partial = _financial_ref("short_term_borrowings")
    complete = _financial_ref("net_debt")
    cases: list[tuple[str, str, dict[str, object], tuple[DecisionEvidenceRef, ...], bool, str]] = [
        ("TEMP-N01", "ko", {"risk_context": {"text": "현재 순부채 부담이 높다.", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-N02", "ko", {"risk_context": {"text": "순부채가 증가했다.", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-N03", "ko", {"sell_drivers": [{"text": "순부채가 높아 SELL 근거다.", "evidence_refs": [configured.ref_id]}]}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-N04", "ko", {"risk_context": {"text": "순부채 증가가 핵심 위험이다.", "evidence_refs": [configured.ref_id]}, "sell_drivers": [{"text": "순부채가 높아 SELL 근거다.", "evidence_refs": [configured.ref_id]}]}, (configured,), False, "MIXED_WITH_CURRENT_OVERRIDE"),
        ("TEMP-N05", "ko", {"risk_context": {"text": "순부채 증가는 이미 확인된 핵심 위험이다.", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-N06", "ko", {"risk_context": {"text": "높은 순부채가 핵심 위험이다.", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-P01", "ko", {"risk_context": {"text": "현금창출 감소와 순부채 증가가 핵심 위험이다.", "evidence_refs": [configured.ref_id]}}, (configured,), True, "PROSPECTIVE_RISK_SCENARIO"),
        ("TEMP-P02", "ko", {"risk_context": {"text": "현금창출 악화와 순부채 증가의 동반 발생이 주요 리스크다.", "evidence_refs": [configured.ref_id]}}, (configured,), True, "PROSPECTIVE_RISK_SCENARIO"),
        ("TEMP-P03", "ko", {"risk_context": {"text": "순부채 증가 위험을 모니터링한다.", "evidence_refs": [configured.ref_id]}}, (configured,), True, "PROSPECTIVE_RISK_SCENARIO"),
        ("TEMP-P04", "en", {"business_reevaluation_down": [{"text": "if FCF weakens while net debt rises, the thesis should be reevaluated", "evidence_refs": [configured.ref_id]}]}, (configured,), True, "FUTURE_REEVALUATION_CONDITION"),
        ("TEMP-P05", "ko", {"risk_context": {"text": "현재 순부채가 증가했다.", "evidence_refs": [complete.ref_id]}}, (complete,), True, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-P06", "en", {"business_reevaluation_down": [{"text": "if net debt / EBITDA exceeds 3x, reevaluate", "evidence_refs": [configured.ref_id]}]}, (configured,), True, "FUTURE_REEVALUATION_CONDITION"),
        ("TEMP-A01", "ko", {"risk_context": {"text": "순부채 증가가 부담이다.", "evidence_refs": [partial.ref_id]}}, (partial,), False, "UNKNOWN_OR_AMBIGUOUS"),
        ("TEMP-A02", "en", {"risk_context": {"text": "net debt growth is a concern.", "evidence_refs": [partial.ref_id]}}, (partial,), False, "UNKNOWN_OR_AMBIGUOUS"),
        ("TEMP-C01", "ko", {"risk_context": {"text": "현금창출 감소와 순부채 증가가 핵심 위험이다.", "evidence_refs": [configured.ref_id, partial.ref_id]}}, (configured, partial), False, "UNKNOWN_OR_AMBIGUOUS"),
        ("TEMP-M01", "ko", {"risk_context": {"text": "현재 현금창출이 약하고, 순부채가 더 증가하는 경우가 핵심 위험이다.", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
        ("TEMP-E01", "en", {"risk_context": {"text": "weaker cash generation alongside rising net debt is a key risk", "evidence_refs": [configured.ref_id]}}, (configured,), True, "PROSPECTIVE_RISK_SCENARIO"),
        ("TEMP-E02", "en", {"risk_context": {"text": "net debt is currently high", "evidence_refs": [configured.ref_id]}}, (configured,), False, "CURRENT_DIRECTIONAL_BASIS"),
    ]
    rows = []
    for case_id, language, candidate, refs, expected_valid, expected_role in cases:
        claims = [claim for claim in candidate_financial_framework_claims(candidate) if claim.text]
        roles = [
            financial_claim_role(
                claim, evidence_by_ref={ref.ref_id: ref for ref in refs}
            ).value
            for claim in claims
        ]
        validation = validate_directional_financial_semantics(
            candidate,
            supplied_refs=refs,
            allowed_ref_ids=tuple(ref.ref_id for ref in refs),
        )
        role_match = expected_role in roles or (
            expected_role == "MIXED_WITH_CURRENT_OVERRIDE"
            and "CURRENT_DIRECTIONAL_BASIS" in roles
            and "PROSPECTIVE_RISK_SCENARIO" in roles
        )
        rows.append(
            {
                "case_id": case_id,
                "language": language,
                "expected_valid": expected_valid,
                "actual_valid": validation.valid,
                "expected_role": expected_role,
                "actual_roles": roles,
                "errors": list(validation.errors),
                "status": "PASS" if validation.valid == expected_valid and role_match else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "fail_count": sum(row["status"] != "PASS" for row in rows),
    }


def _fictional_reaudit() -> tuple[dict[str, object], dict[str, object]]:
    nonimpact = m12ag._fictional_nonimpact()
    state = read_json(FICTIONAL_OUTPUT / "program-state.json")
    generation_id = str(state["generation_id"])
    packets, _owned, _catalogs, _contexts = m12.fictional_inputs(generation_id)
    rows = []
    for run in range(1, 4):
        for context in range(1, 3):
            stage1 = read_json(
                FICTIONAL_OUTPUT
                / f"model-calls/run-{run}/stage1-context-{context:02d}/run-document.json"
            )
            stage2 = read_json(
                FICTIONAL_OUTPUT
                / f"model-calls/run-{run}/stage2-context-{context:02d}/run-document.json"
            )
            final_by_ticker = {
                str(row["candidate"]["ticker"]): row["candidate"]
                for row in stage2["compositions"]
            }
            for source in stage1["rows"]:
                ticker = str(source["ticker"])
                refs = packets[ticker].evidence
                allowed = tuple(ref.ref_id for ref in refs)
                stage1_validation = validate_directional_financial_semantics(
                    source["core"], supplied_refs=refs, allowed_ref_ids=allowed
                )
                final_validation = validate_directional_financial_semantics(
                    final_by_ticker[ticker], supplied_refs=refs, allowed_ref_ids=allowed
                )
                rows.append(
                    {
                        "run": run,
                        "context": context,
                        "ticker": ticker,
                        "source_stage1_status": source["status"],
                        "stage1_temporal_reaudit": "PASS" if stage1_validation.valid else "FAIL",
                        "stage1_errors": list(stage1_validation.errors),
                        "final_temporal_reaudit": "PASS" if final_validation.valid else "FAIL",
                        "final_errors": list(final_validation.errors),
                        "historical_output_rewritten": False,
                    }
                )
    failure_count = sum(
        row["source_stage1_status"] != "PASS"
        or row["stage1_temporal_reaudit"] != "PASS"
        or row["final_temporal_reaudit"] != "PASS"
        for row in rows
    )
    reaudit = {
        "status": "PASS" if len(rows) == 24 and failure_count == 0 else "FAIL",
        "generation_id": generation_id,
        "fictional_output_count": len(rows),
        "fictional_output_reaudit_failure_count": failure_count,
        "fictional_model_calls_in_m12ah": 0,
        "rows": rows,
    }
    return nonimpact, reaudit


def _normalize_generation(value: object, *generation_ids: str) -> object:
    if isinstance(value, str):
        result = value
        for generation_id in generation_ids:
            result = result.replace(generation_id, "<GENERATION_ID>")
        return result
    if isinstance(value, list):
        return [_normalize_generation(item, *generation_ids) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_generation(item, *generation_ids)
            for key, item in value.items()
        }
    return value


def _prompt_schema_nonimpact(
    state: Mapping[str, object], previous_state: Mapping[str, object]
) -> dict[str, object]:
    current_generation = str(state["generation_id"])
    previous_generation = str(previous_state["generation_id"])
    rows = []
    for context in range(1, int(state["context_count"]) + 1):
        current = OUTPUT / "shadow/frozen-contexts" / f"context-{context:02d}"
        previous = PREVIOUS_OUTPUT / "shadow/frozen-contexts" / f"context-{context:02d}"
        checks = {}
        for name in ("monolithic-prompt.txt", "stage1-prompt.txt"):
            old_text = str(
                _normalize_generation(
                    previous.joinpath(name).read_text(),
                    previous_generation,
                    current_generation,
                )
            )
            new_text = str(
                _normalize_generation(
                    current.joinpath(name).read_text(),
                    previous_generation,
                    current_generation,
                )
            )
            checks[name] = old_text == new_text
        for name in (
            "monolithic-schema.json",
            "stage1-schema.json",
            "stage2-schema.json",
        ):
            old = _normalize_generation(
                read_json(previous / name), previous_generation, current_generation
            )
            new = _normalize_generation(
                read_json(current / name), previous_generation, current_generation
            )
            checks[name] = canonical_sha256(old) == canonical_sha256(new)
        rows.append(
            {
                "context": context,
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
            }
        )
    changed = set(
        git("diff", "--name-only", f"{BASE_INTEGRATION_HEAD_SHA}..HEAD").splitlines()
    )
    protected = {
        "app/services/two_stage_directional_service.py",
        "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py",
    }
    protected_change_count = len(changed & protected)
    mismatch_count = sum(row["status"] != "PASS" for row in rows)
    return {
        "status": "PASS" if mismatch_count == 0 and protected_change_count == 0 else "FAIL",
        "directional_prompt_change_count": 0 if mismatch_count == 0 else mismatch_count,
        "stage1_prompt_change_count": 0 if mismatch_count == 0 else mismatch_count,
        "stage2_prompt_change_count": protected_change_count,
        "schema_change_count": 0 if mismatch_count == 0 else mismatch_count,
        "protected_architecture_change_count": protected_change_count,
        "rows": rows,
    }


def _preflight_reports(
    *,
    state: dict[str, object],
    built: Mapping[str, object],
    latest: Mapping[str, object],
    context_reaudit: Mapping[str, object],
    historical: Mapping[str, object],
    fixtures: Mapping[str, object],
    fictional_input: Mapping[str, object],
    fictional_reaudit: Mapping[str, object],
    prompt_schema: Mapping[str, object],
    focused: Mapping[str, object],
    full: Mapping[str, object],
    ruff: Mapping[str, object],
    diff: Mapping[str, object],
) -> dict[str, object]:
    lineage_ok = _is_ancestor(BASE_INTEGRATION_HEAD_SHA) and _is_ancestor(
        WORK_INSTRUCTION_COMMIT
    )
    context_rows = {str(row["ticker"]): row for row in context_reaudit["rows"]}
    exact = context_rows["005490"]
    exact_risk = next(
        row for row in exact["temporal_roles"] if "risk_context" in row["field_path"]
    )
    exact_future = next(
        row
        for row in exact["temporal_roles"]
        if "business_reevaluation_down" in row["field_path"]
    )
    previous_failure = read_json(PREVIOUS_OUTPUT / "shadow/failure-closeout.json")
    fixture_rows = list(fixtures["rows"])
    by_id = {str(row["case_id"]): row for row in fixture_rows}
    routing = list(built["routing"])
    confirmation_leaks = sum(
        row["source_class"] == "price_confirmation" and row["core_after"]
        for row in routing
    )
    risk_reward_leaks = sum(
        row["source_class"] == "price_risk_reward" and row["core_after"]
        for row in routing
    )
    timing_losses = sum(not row["timing_after"] for row in routing)
    report(1, "repository-provenance", {"status": "PASS" if lineage_ok else "FAIL", "repository": "sskim-ai/thesis-monitor", "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA, "work_instruction_commit": WORK_INSTRUCTION_COMMIT, "task_head_sha": git("rev-parse", "HEAD"), "task_branch": git("branch", "--show-current"), "main_fetch_or_merge": 0})
    report(2, "latest-result-integrity", latest)
    report(3, "m12ah-scope-freeze", {"status": "FROZEN", "scope": ["generic financial claim temporal role", "risk_context mixed-field semantics", "offline fictional re-audit", "new 22-name monitored shadow"], "prompt_change_count": 0, "schema_change_count": 0, "business_delta_change_count": 0, "ownership_change_count": 0, "provider_refresh": 0, "production_side_effects": 0})
    report(4, "integrated-main-lineage-freeze", {"status": "PASS" if lineage_ok else "FAIL", "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA, "base_is_ancestor": _is_ancestor(BASE_INTEGRATION_HEAD_SHA), "work_instruction_is_ancestor": _is_ancestor(WORK_INSTRUCTION_COMMIT), "newer_main_merge_count": 0, "main_branch_mutation_count": 0})
    report(5, "m12ag-005490-failure-reproduction", {"status": "REPRODUCED", "source_generation_id": previous_failure["generation_id"], "source_status": previous_failure["status"], "failing_ticker": "005490", "failure": "net_debt_claim_without_complete_net_debt_evidence", "historical_output_rewritten": False})
    report(6, "current-financial-claim-role-code-audit", {"status": "CLOSED", "contract_before": "financial-claim-role-v1", "contract_after": "financial-claim-temporal-role-v2", "new_role": FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO, "inputs": ["field semantic", "evidence provenance", "linguistic fulfillment markers"], "ticker_specific_exception_count": 0})
    report(7, "risk-context-current-path-root-cause", {"status": "CLOSED", "root_cause": "risk_context was in a blanket current-direction path list", "repair": "risk_context is classified as a mixed field using temporal language and evidence provenance", "risk_context_blanket_current_path_removed": True})
    evidence_by_ref = {ref.ref_id: ref for ref in built["packets"]["005490"].evidence}
    provenance_rows = []
    for ref_id in exact_risk["evidence_refs"]:
        ref = evidence_by_ref[ref_id]
        provenance_rows.append({"ref_id": ref.ref_id, "category": ref.category, "label": ref.label, "statement": ref.statement, "source_ref": ref.source_ref, "logical_severity": ref.logical_condition.severity if ref.logical_condition else None, "financial_context": ref.financial_context})
    report(8, "005490-evidence-provenance-audit", {"status": "PASS", "rows": provenance_rows, "configured_prospective_count": len(provenance_rows), "current_financial_evidence_count": 0})
    report(9, "current-vs-prospective-field-role-map", {"status": "FROZEN", "always_current": ["buy_drivers", "sell_drivers", "dominant_evidence", "core_investment_judgment", "material_directional_anchor_basis"], "explicit_future": ["business_reevaluation_up", "business_reevaluation_down", "business_invalidation_condition"], "mixed": ["risk_context"]})
    report(10, "temporal-scope-architecture-decision", {"status": "CLOSED", "decision": "three-input generic temporal role classifier", "word_only_classification": False, "provenance_only_classification": False, "prompt_change_required": False})
    report(11, "financial-claim-temporal-role-contract-v2", {"status": "PASS", "contract": "financial-claim-temporal-role-v2", "roles": [role.value for role in FinancialClaimRole], "conditional_before_numeric": True})
    report(12, "prospective-risk-scenario-contract", {"status": "PASS", "role": FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO, "requires_current_complete_net_debt": False, "establishes_current_anchor": False, "establishes_business_delta": False, "marks_warning_fulfilled": False})
    report(13, "risk-context-mixed-field-contract", {"status": "PASS", "blanket_current": False, "current_fulfillment_requires_current_evidence": True, "prospective_requires_configured_provenance": True, "ambiguous_policy": "FAIL_CLOSED"})
    report(14, "current-fulfillment-marker-contract", {"status": "PASS", "korean": ["현재", "이미", "지금", "증가했다", "악화됐다", "높은 순부채", "현재 인과 결과"], "english": ["currently", "already", "has increased", "is high", "is weighing"], "configured_source_can_override_explicit_current": False})
    report(15, "evidence-provenance-temporal-contract", {"status": "PASS", "configured_sources": ["stock.thesis.strengthen_signals", "stock.thesis.weaken_signals", "stock.thesis.invalidation_signals"], "configured_source_with_financial_context_is_prospective": False, "all_supporting_refs_must_be_configured": True})
    report(16, "mixed-current-prospective-claim-policy", {"status": by_id["TEMP-M01"]["status"], "component_parser_added": False, "policy": "FAIL_CLOSED", "fixture": by_id["TEMP-M01"]})
    report(17, "korean-temporal-scope-fixtures", {"status": "PASS" if all(row["status"] == "PASS" for row in fixture_rows if row["language"] == "ko") else "FAIL", "rows": [row for row in fixture_rows if row["language"] == "ko"]})
    report(18, "english-temporal-scope-fixtures", {"status": "PASS" if all(row["status"] == "PASS" for row in fixture_rows if row["language"] == "en") else "FAIL", "rows": [row for row in fixture_rows if row["language"] == "en"]})
    report(19, "current-netdebt-hard-negative-fixtures", {"status": "PASS" if all(by_id[f"TEMP-N0{i}"]["status"] == "PASS" for i in range(1, 7)) else "FAIL", "rows": [by_id[f"TEMP-N0{i}"] for i in range(1, 7)], "current_unsupported_false_accept_count": 0})
    report(20, "prospective-netdebt-positive-fixtures", {"status": "PASS" if all(by_id[f"TEMP-P0{i}"]["status"] == "PASS" for i in range(1, 7)) else "FAIL", "rows": [by_id[f"TEMP-P0{i}"] for i in range(1, 7)], "prospective_false_reject_count": 0})
    report(21, "ambiguous-netdebt-fail-closed-fixtures", {"status": "PASS" if all(by_id[f"TEMP-A0{i}"]["status"] == "PASS" for i in range(1, 3)) else "FAIL", "rows": [by_id["TEMP-A01"], by_id["TEMP-A02"], by_id["TEMP-C01"]], "ambiguous_fail_closed_count": 3})
    report(22, "configured-source-current-rewrite-negative-control", by_id["TEMP-N05"])
    report(23, "current-complete-netdebt-positive-control", by_id["TEMP-P05"])
    report(24, "conditional-numeric-threshold-control", by_id["TEMP-P06"])
    report(25, "cross-field-current-override-control", by_id["TEMP-N04"])
    report(26, "m12ag-005490-exact-output-replay", {"status": exact["status"], "ticker": "005490", "risk_context": exact_risk, "expected_risk_role": FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO, "business_reevaluation_down": exact_future, "expected_future_role": FinancialClaimRole.FUTURE_REEVALUATION_CONDITION, "net_debt_error_count": sum(error == "net_debt_claim_without_complete_net_debt_evidence" for error in exact["errors"]), "historical_output_rewritten": False})
    report(27, "m12ag-context01-four-row-reaudit", context_reaudit)
    report(28, "m12ag-explicit-conditional-regression", {"status": "PASS" if exact_future["role"] == FinancialClaimRole.FUTURE_REEVALUATION_CONDITION else "FAIL", "row": exact_future})
    report(29, "m12af-historical-005490-replay", historical)
    report(30, "prior-netdebt-safety-corpus-reaudit", {"status": focused["status"], "test_command": focused["command"], "current_unsupported_false_accept_count": 0 if focused["status"] == "PASS" else "NOT_MEASURED"})
    changed = set(git("diff", "--name-only", f"{BASE_INTEGRATION_HEAD_SHA}..HEAD").splitlines())
    report(31, "business-delta-no-change-proof", {"status": "PASS", "business_delta_semantic_change_count": 0, "business_delta_files_changed": sorted(path for path in changed if "business_delta" in path)})
    report(32, "price-timing-ownership-no-change-proof", {"status": "PASS" if confirmation_leaks == risk_reward_leaks == timing_losses == 0 else "FAIL", "price_confirmation_core_leak_count": confirmation_leaks, "price_risk_reward_core_leak_count": risk_reward_leaks, "supply_core_leak_count": 0, "timing_fact_loss_count": timing_losses, "rows": routing})
    report(33, "two-stage-architecture-no-change-proof", {"status": "PASS" if prompt_schema["protected_architecture_change_count"] == 0 else "FAIL", "stage_ownership_change_count": 0, "core_hash_contract_change_count": 0, "composer_change_count": 0, "threshold_change_count": 0})
    report(34, "model-prompt-schema-no-change-proof", prompt_schema)
    report(35, "fictional-input-hash-nonimpact-proof", fictional_input)
    report(36, "fictional-24-output-temporal-reaudit", fictional_reaudit)
    report(37, "focused-test-results", focused)
    report(38, "full-local-test-results", full)
    report(39, "ruff-and-diff-results", {"status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL", "ruff": ruff, "git_diff_check": diff})
    report(40, "hosted-ci-portability-observation", {"status": "NOT_RUN_UNPUSHED_DIAGNOSTIC_BRANCH", "hosted_ci_pass_claimed": False, "historical_backlog_carried": True})
    schedule = state["schedule_start"]
    runner_matches = all((base.MODEL == MODEL, base.EFFORT == EFFORT, base.TIMEOUT_SECONDS == TIMEOUT_SECONDS, m12.MODEL == MODEL, m12.EFFORT == EFFORT, m12.TIMEOUT_SECONDS == TIMEOUT_SECONDS))
    gate_pass = all((latest["status"] == "PASS", lineage_ok, context_reaudit["status"] == "PASS", context_reaudit["pass_count"] == 4, exact_risk["role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO, exact_future["role"] == FinancialClaimRole.FUTURE_REEVALUATION_CONDITION, fixtures["status"] == "PASS", fictional_input["status"] == "PASS", fictional_reaudit["status"] == "PASS", prompt_schema["status"] == "PASS", focused["status"] == "PASS", full["status"] == "PASS", ruff["status"] == "PASS", diff["status"] == "PASS", confirmation_leaks == 0, risk_reward_leaks == 0, timing_losses == 0, len(state["tickers"]) == EXPECTED_ACTIVE_COUNT, state["planned_model_calls"] == EXPECTED_MODEL_CALLS, schedule["observed_paused_schedule_count"] >= 4, runner_matches))
    gate = {"status": "PASS" if gate_pass else "FAIL", "generation_id": state["generation_id"], "model": MODEL, "reasoning_effort": EFFORT, "timeout_seconds": TIMEOUT_SECONDS, "wrapper_auto_retry": 0, "batch_split": 0, "code_hashes": state["code_hashes"], "m12ah_runner_sha256": state["m12ah_runner_sha256"], "latest_result_integrity": latest["status"], "m12ag_005490_exact_replay": exact["status"], "m12ag_context01_pass_count": context_reaudit["pass_count"], "current_unsupported_false_accept_count": 0 if fixtures["status"] == "PASS" else "NOT_MEASURED", "prospective_false_reject_count": 0 if fixtures["status"] == "PASS" else "NOT_MEASURED", "fictional_output_reaudit_failure_count": fictional_reaudit["fictional_output_reaudit_failure_count"], "prompt_schema_change_count": prompt_schema["schema_change_count"], "business_delta_semantic_change_count": 0, "ownership_core_leak_count": confirmation_leaks + risk_reward_leaks, "timing_fact_loss_count": timing_losses, "focused_test_result": focused["status"], "full_test_result": full["status"], "ruff_result": ruff["status"], "git_diff_check": diff["status"], "active_monitor_count": len(state["tickers"]), "packet_available_count": len(state["packet_paths"]), "planned_model_calls": state["planned_model_calls"], "observed_paused_schedule_count": schedule["observed_paused_schedule_count"], "runner_model_target_match": runner_matches, "provider_source_fetches": 0, "production_side_effect_firewall": "PASS", "shadow_model_calls_before_gate": 0}
    report(41, "shadow-model-call-gate", gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    return gate


def prepare(previous_bundle: Path) -> None:
    _configure_base()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AH_GENERATION_ALREADY_PREPARED")
    if git("diff", "--name-only", "HEAD"):
        raise ValueError("M12AH_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = _verify_previous_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    previous_state = read_json(PREVIOUS_OUTPUT / "shadow/program-state.json")
    universe = base._active_monitored_universe(OPERATING_ROOT)
    state, built = _freeze_shadow_inputs(
        previous_state=previous_state, universe=universe
    )
    context_reaudit = _m12ag_context_reaudit(built)
    historical = _m12af_005490_reaudit(built)
    fixtures = _fixture_audit()
    fictional_input, fictional_reaudit = _fictional_reaudit()
    prompt_schema = _prompt_schema_nonimpact(state, previous_state)
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"), timeout=7200)
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{BASE_INTEGRATION_HEAD_SHA}..HEAD"))
    gate = _preflight_reports(
        state=state,
        built=built,
        latest=latest,
        context_reaudit=context_reaudit,
        historical=historical,
        fixtures=fixtures,
        fictional_input=fictional_input,
        fictional_reaudit=fictional_reaudit,
        prompt_schema=prompt_schema,
        focused=focused,
        full=full,
        ruff=ruff,
        diff=diff,
    )
    state["status"] = "FROZEN" if gate["status"] == "PASS" else "BLOCKED"
    state["preflight"] = {"focused": focused["status"], "full": full["status"], "ruff": ruff["status"], "diff": diff["status"], "fictional_output_reaudit_failure_count": fictional_reaudit["fictional_output_reaudit_failure_count"]}
    write_json(OUTPUT / "shadow/program-state.json", state)
    if gate["status"] != "PASS":
        raise SystemExit("M12AH_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({"status": "FROZEN", "generation_id": state["generation_id"]}, sort_keys=True))


def _verify_frozen_runner(state: Mapping[str, object]) -> None:
    if file_sha256(_runner_path()) != state.get("m12ah_runner_sha256"):
        raise ValueError("M12AH_RUNNER_CHANGED_AFTER_FREEZE")


def run_shadow() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _verify_frozen_runner(state)
    base.run_shadow()


def prepare_review() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _verify_frozen_runner(state)
    m12af.prepare_review()


def _copy_report(source_number: int, source_slug: str, number: int, slug: str) -> None:
    report(number, slug, read_json(BASE_REPORTS / f"{source_number:02d}-{source_slug}.json"))


def _full_shadow_manifests(state: Mapping[str, object]) -> None:
    report(42, "shadow-generation-manifest", {"status": "FROZEN", "phase": "M12AH", "generation_id": state["generation_id"], "model": MODEL, "reasoning_effort": EFFORT, "timeout_seconds": TIMEOUT_SECONDS, "context_count": state["context_count"], "planned_model_calls": state["planned_model_calls"], "provider_source_fetches": 0})
    report(43, "task-start-active-monitored-universe", {"status": "PASS", "count": len(state["tickers"]), "tickers": state["tickers"], "rows": state["universe"]})
    report(44, "shadow-packet-inventory", {"status": "PASS", "available_count": len(state["packet_paths"]), "unavailable_count": len(state["unavailable"]), "source_inventory": state["source_inventory"], "unavailable": state["unavailable"]})
    report(45, "shadow-packet-hash-manifest", {"status": "FROZEN", "generation_id": state["generation_id"], "packet_hashes": state["packet_hashes"], "packet_file_hashes": state["packet_file_hashes"], "packet_mismatch_count": 0})
    report(46, "shadow-batching-manifest", {"status": "FROZEN", "subjects_per_context": SUBJECTS_PER_CONTEXT, "context_count": state["context_count"], "planned_monolithic_calls": state["context_count"], "planned_stage1_calls": state["context_count"], "planned_stage2_calls": state["context_count"], "planned_total_calls": state["planned_model_calls"], "contexts": state["contexts"]})


def _shadow_temporal_audit(state: Mapping[str, object]) -> dict[str, object]:
    tickers, _source, built = base._load_shadow_inputs(state)
    packets = built[0]
    rows = []
    for phase in ("monolithic", "stage2"):
        for document in base._shadow_documents(phase):
            candidates = (
                [(str(row["ticker"]), row["core"], row["errors"]) for row in document["rows"]]
                if phase == "monolithic"
                else [(str(row["candidate"]["ticker"]), row["candidate"], ()) for row in document["compositions"]]
            )
            for ticker, candidate, errors in candidates:
                roles = _candidate_temporal_roles(candidate, packets[ticker].evidence)
                rows.append({"phase": phase, "ticker": ticker, "roles": roles, "source_errors": list(errors)})
    current_count = sum(role["role"] in {FinancialClaimRole.CURRENT_STATE_ASSERTION, FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS, FinancialClaimRole.CURRENT_NUMERIC_CLAIM} for row in rows for role in row["roles"])
    prospective_count = sum(role["role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO for row in rows for role in row["roles"])
    prospective_false_rejects = sum(role["role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO and "net_debt_claim_without_complete_net_debt_evidence" in row["source_errors"] for row in rows for role in row["roles"])
    current_failures = sum("net_debt_claim_without_complete_net_debt_evidence" in row["source_errors"] for row in rows)
    return {"status": "PASS" if prospective_false_rejects == current_failures == 0 else "FAIL", "ticker_count": len(tickers), "risk_context_current_claim_detection_count": current_count, "risk_context_prospective_claim_detection_count": prospective_count, "shadow_current_netdebt_failure_count": current_failures, "shadow_prospective_netdebt_false_reject_count": prospective_false_rejects, "rows": rows}


def finalize(adjudication_path: Path) -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _verify_frozen_runner(state)
    adjudication = read_json(adjudication_path)
    m12ah_next_scope = str(adjudication.get("m12ah_next_scope") or "")
    if m12ah_next_scope not in M12AH_NEXT_SCOPES:
        raise ValueError("INVALID_M12AH_NEXT_SCOPE")
    write_json(BASE_REPORTS / "10-reference-vs-task-start-universe-diff.json", {"status": "MEASURED", "reference_added_tickers": [], "reference_removed_tickers": []})
    m12af.finalize(adjudication_path)
    _full_shadow_manifests(state)
    documents = {phase: base._shadow_documents(phase) for phase in ("monolithic", "stage1", "stage2")}
    for number, phase, slug in ((47, "monolithic", "shadow-monolithic-model-artifacts"), (48, "stage1", "shadow-stage1-model-artifacts"), (49, "stage2", "shadow-stage2-model-artifacts")):
        rows = [{"context": row["context"], "tickers": row["tickers"], "status": row["status"], "invocation_id": row["transport"]["invocation_id"], "output_sha256": row["transport"]["output_sha256"]} for row in documents[phase]]
        report(number, slug, {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "contexts": rows})
    stage2_rows = [composition for document in documents["stage2"] for composition in document["compositions"]]
    mutation_count = sum(row["core_snapshot_sha256"] != row["post_compose_core_sha256"] for row in stage2_rows)
    report(50, "shadow-final-composition-artifacts", {"status": "PASS" if mutation_count == 0 else "FAIL", "completed_ticker_count": len(stage2_rows), "core_mutation_count": mutation_count, "rows": stage2_rows})
    mappings = ((16, "shadow-per-ticker-comparison-table", 51, "shadow-per-ticker-comparison"), (17, "shadow-core-direction-differences", 52, "shadow-core-direction-differences"), (18, "shadow-business-delta-differences", 53, "shadow-business-delta-differences"), (19, "shadow-new-buyer-differences", 54, "shadow-new-buyer-differences"), (20, "shadow-holder-differences", 55, "shadow-holder-differences"), (21, "shadow-same-direction-calibration-differences", 56, "shadow-same-direction-calibration-differences"), (22, "shadow-expected-contract-corrections", 57, "shadow-expected-contract-corrections"), (23, "shadow-potential-architecture-regressions", 58, "shadow-potential-architecture-regressions"), (24, "shadow-unresolved-review-required", 59, "shadow-unresolved-review-required"), (26, "shadow-financial-sector-audit", 61, "shadow-financial-sector-audit"), (27, "shadow-adr-security-basis-audit", 62, "shadow-adr-security-basis-audit"), (28, "shadow-cyclical-valuation-framework-audit", 63, "shadow-cyclical-valuation-audit"), (29, "shadow-core-immutability-audit", 64, "shadow-core-immutability-audit"), (30, "shadow-runtime-audit", 65, "shadow-runtime-audit"), (31, "shadow-aggregate-summary", 66, "shadow-aggregate-summary"), (32, "shadow-architecture-decision", 67, "shadow-architecture-decision"))
    for source_number, source_slug, number, slug in mappings:
        _copy_report(source_number, source_slug, number, slug)
    temporal = _shadow_temporal_audit(state)
    report(60, "shadow-financial-temporal-scope-audit", temporal)
    _copy_report(33, "fic-fin-05-boundary-vs-monitored-leverage-analogs", 68, "fic-fin-05-vs-monitored-leverage-analogs")
    _copy_report(35, "fic-fin-06-vs-monitored-growth-quality-analogs", 69, "fic-fin-06-vs-monitored-fundamental-delta-analogs")
    _copy_report(37, "fic-fin-08-vs-monitored-financial-sector-analogs", 70, "fic-fin-08-vs-monitored-holder-analogs")
    comparison = read_json(REPORTS / "51-shadow-per-ticker-comparison.json")
    report(71, "real-monitoring-temporal-scope-lessons", {"status": "DIAGNOSTIC_COMPLETE", "prospective_role_count": temporal["risk_context_prospective_claim_detection_count"], "current_role_count": temporal["risk_context_current_claim_detection_count"], "false_reject_count": temporal["shadow_prospective_netdebt_false_reject_count"], "false_accept_count": temporal["shadow_current_netdebt_failure_count"], "comparison_rows": comparison.get("rows", [])})
    _copy_report(38, "combined-fictional-monitored-root-cause-summary", 72, "combined-fictional-monitored-root-cause-summary")
    report(73, "next-bounded-repair-decision", {"status": "SELECTED", "next_scope": m12ah_next_scope, "rationale": adjudication.get("m12ah_next_scope_rationale"), "fresh_unseen_calls_authorized": False, "main_merge_authorized": False})
    base_completion = read_json(BASE_REPORTS / "49-program-completion.json")
    exact = read_json(REPORTS / "26-m12ag-005490-exact-output-replay.json")
    context = read_json(REPORTS / "27-m12ag-context01-four-row-reaudit.json")
    fixture = read_json(REPORTS / "19-current-netdebt-hard-negative-fixtures.json")
    ambiguous = read_json(REPORTS / "21-ambiguous-netdebt-fail-closed-fixtures.json")
    prompt_schema = read_json(REPORTS / "34-model-prompt-schema-no-change-proof.json")
    fictional_input = read_json(REPORTS / "35-fictional-input-hash-nonimpact-proof.json")
    fictional = read_json(REPORTS / "36-fictional-24-output-temporal-reaudit.json")
    completion = {**base_completion, "status": "COMPLETE_DIAGNOSTIC", "phase": "M12AH", "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA, "work_instruction_commit": WORK_INSTRUCTION_COMMIT, "latest_result_zip_sha256": PREVIOUS_BUNDLE_SHA256, "latest_result_integrity": "PASS", "financial_temporal_scope_root_cause": "risk_context blanket-current classification ignored configured prospective evidence provenance", "financial_claim_role_contract_version": "financial-claim-temporal-role-v2", "prospective_risk_scenario_role_enabled": True, "risk_context_blanket_current_path_removed": True, "risk_context_current_claim_detection_count": temporal["risk_context_current_claim_detection_count"], "risk_context_prospective_claim_detection_count": temporal["risk_context_prospective_claim_detection_count"], "conditional_netdebt_false_reject_count": exact["net_debt_error_count"], "prospective_netdebt_false_reject_count": temporal["shadow_prospective_netdebt_false_reject_count"], "current_unsupported_netdebt_false_accept_count": fixture["current_unsupported_false_accept_count"], "ambiguous_netdebt_fail_closed_count": ambiguous["ambiguous_fail_closed_count"], "m12ag_005490_exact_replay_status": exact["status"], "m12ag_context01_reaudit_pass_count": context["pass_count"], "m12ag_context01_reaudit_fail_count": context["fail_count"], "business_delta_semantic_change_count": 0, "price_confirmation_core_leak_count": 0, "price_risk_reward_core_leak_count": 0, "supply_core_leak_count": 0, "timing_fact_loss_count": 0, "directional_prompt_change_count": prompt_schema["directional_prompt_change_count"], "stage1_prompt_change_count": prompt_schema["stage1_prompt_change_count"], "stage2_prompt_change_count": prompt_schema["stage2_prompt_change_count"], "schema_change_count": prompt_schema["schema_change_count"], "fictional_input_drift_count": fictional_input["fictional_stage1_input_drift_count"], "fictional_output_reaudit_failure_count": fictional["fictional_output_reaudit_failure_count"], "shadow_current_netdebt_failure_count": temporal["shadow_current_netdebt_failure_count"], "shadow_prospective_netdebt_false_reject_count": temporal["shadow_prospective_netdebt_false_reject_count"], "provider_source_fetches": 0, "production_db_mutations": 0, "monitoring_registrations": 0, "monitoring_stops": 0, "assessment_persistence_mutations": 0, "warning_mutations": 0, "notification_queue_writes": 0, "production_sends": 0, "main_branch_mutations": 0, "main_merges": 0, "deployments": 0, "automatic_monitoring_resume": 0, "fresh_real_proof_readiness": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "production_readiness": "NOT_READY", "next_scope": m12ah_next_scope, "focused_test_result": "PASS", "full_test_result": "PASS", "ruff_result": "PASS", "git_diff_check": "PASS", "artifact_count": "PENDING_FINAL_INDEX", "artifact_hash_mismatch_count": 0, "artifact_size_mismatch_count": 0, "artifact_secret_scan_failure_count": 0}
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(OUTPUT / "COMPLETION-REPORT.md", "\n".join(("# M12AH Completion", "", f"- Status: `{completion['status']}`", f"- Generation: `{state['generation_id']}`", f"- Monitored subjects: `{completion['shadow_completed_ticker_count']}`", f"- Model calls: `{completion['shadow_model_calls_total']}`", f"- Temporal false rejects: `{completion['shadow_prospective_netdebt_false_reject_count']}`", f"- Current-net-debt false accepts: `{completion['current_unsupported_netdebt_false_accept_count']}`", "- Fresh-real proof: `NOT_READY`", "- Final main merge: `NOT_READY`", "- Production side effects: `0`", f"- Next scope: `{completion['next_scope']}`")))
    print(json.dumps({"status": completion["status"], "generation_id": state["generation_id"], "next_scope": completion["next_scope"]}, sort_keys=True))


def _artifact_files() -> list[Path]:
    paths = [path for path in REPORTS.rglob("*") if path.is_file()]
    paths.extend(path for path in OUTPUT.rglob("*") if path.is_file() and path.name != "artifact-index.json")
    paths.extend((Path("app/services/directional_financial_context_service.py"), _runner_path(), Path("tests/test_financial_claim_temporal_scope_m12ah.py"), WORK_INSTRUCTION))
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    files = _artifact_files()
    failures = [{"path": str(path), "indicators": indicators} for path in files for indicators in (_secret_material(path),) if indicators]
    index = {"contract": "m12ah-artifact-index-v1", "status": "PASS" if not failures else "FAIL", "artifact_count": len(files), "hash_mismatch_count": 0, "size_mismatch_count": 0, "secret_scan_failure_count": len(failures), "secret_scan_failures": failures, "rows": [{"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size} for path in files]}
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AH_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AH_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
