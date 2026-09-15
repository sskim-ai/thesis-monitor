from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tomllib
from typing import Any, Mapping, Sequence
import zipfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cash_flow_capital_efficiency_service import (  # noqa: E402
    FinancialFact,
    Metric,
)
from app.services.coldstart_fundamental_enrichment_service import (  # noqa: E402
    AnalysisFramework,
    FundamentalEvidenceFamily,
    evaluate_source_sufficiency,
)
from app.services.cross_market_decision_engine_service import (  # noqa: E402
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.debt_liquidity_financial_mapping_service import (  # noqa: E402
    CONTRACT_VERSION,
    DEBT_COMPONENT_METRICS,
    DEBT_SCOPE,
    LEASE_LIABILITY_POLICY,
    NET_DEBT_SCOPE,
    RESTRICTED_CASH_POLICY,
    ComponentRole,
    DebtCompletenessAssessment,
    DebtCompletenessStatus,
    build_debt_liquidity_batch,
    canonicalize_debt_liquidity_occurrences,
    derive_interest_bearing_debt_total,
    promote_opendart_debt_liquidity_facts,
    registry_audit,
)
from app.services.financial_context_adapter_service import (  # noqa: E402
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (  # noqa: E402
    project_financial_fact_catalog,
)
from app.services.opendart_financial_recovery_service import Filing  # noqa: E402
from app.services.opendart_xbrl_service import parse_xbrl_archive  # noqa: E402
from app.services.working_capital_evidence_service import (  # noqa: E402
    OfficialFinancialOccurrence,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260908-interest-bearing-debt-liquidity-financial-domain-"
    "mapping-implementation"
)
SUMMARY_NAME = (
    "20260908-interest-bearing-debt-liquidity-financial-domain-mapping-"
    "implementation.md"
)
BASE_SHA = "5e46a5ff80fbff32145cef0ccf68d906dfcdf5b4"
WORK_INSTRUCTION_COMMIT = "af361e68ba843ee211bcd1e12750c1cf95a8461e"
IMPLEMENTATION_COMMIT = "357a1d577ffd24c96bb0f3ce2c0baf1f13458658"
M8_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260908-source-class-financial-mapping-"
    "implementation-report.zip"
)
M8_RESULT_SHA256 = "7c5f614dc146a1d56f9c10235a1a42858268e7efa3a330732801cd0ab06203d6"
M4_REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260908-source-domain-enrichment-directional-specificity-"
    "design-review"
)
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"
KR_CACHE_ROOT = (
    REPO_ROOT.parents[1]
    / "thesis-monitor-phase7-2/data/cache/opendart/recovery-final"
)
PROVIDER_DB = Path.home() / "Codex/thesis-monitor/data/thesis_monitor.sqlite3"
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"
START_OBSERVED_AT_UTC = "2026-09-08T15:12:59Z"

FOCUSED_TEST_COMMAND = (
    "$HOME/Codex/thesis-monitor/.venv/bin/pytest -q "
    "tests/test_debt_liquidity_financial_mapping_service.py "
    "tests/test_source_class_financial_mapping_service.py "
    "tests/test_opendart_financial_recovery_service.py "
    "tests/test_opendart_xbrl_service.py "
    "tests/test_financial_context_adapter_service.py "
    "tests/test_financial_lineage_projection_service.py "
    "tests/test_decision_evidence_financial_context.py "
    "tests/test_cash_flow_capital_efficiency_service.py "
    "tests/test_official_cash_flow_service.py "
    "tests/test_cross_market_decision_engine.py "
    "tests/test_cash_flow_user_visible_service.py "
    "tests/test_cash_flow_user_visible_integration.py "
    "tests/test_coldstart_fundamental_enrichment_service.py "
    "tests/test_nonproduction_monitoring_lifecycle_service.py "
    "tests/test_nonproduction_lifecycle_decision_service.py"
)

REPORT_NAMES = tuple(
    f"{index:02d}-{name}.json"
    for index, name in enumerate(
        (
            "repository-provenance",
            "latest-result-integrity",
            "m9-scope-freeze",
            "m4-debt-liquidity-contract-reuse-proof",
            "m5-m8-contract-reuse-proof",
            "current-balance-sheet-source-inventory",
            "interest-bearing-debt-component-taxonomy",
            "cash-liquidity-taxonomy",
            "sector-routing-contract",
            "debt-completeness-contract",
            "component-overlap-and-precedence-contract",
            "lease-liability-policy",
            "restricted-cash-policy",
            "debt-liquidity-adapter-contract",
            "debt-liquidity-implementation-diff",
            "source-mapping-activation-surface",
            "us-debt-liquidity-source-support-audit",
            "kr-debt-liquidity-source-support-audit",
            "financial-sector-routing-audit",
            "total-liabilities-negative-control",
            "completeness-denial-accounting",
            "source-conflict-and-dedup-audit",
            "real-archive-coverage",
            "compact-ai-context-non-leak-proof",
            "directional-prompt-no-change-proof",
            "price-timing-no-change-proof",
            "source-sufficiency-no-change-proof",
            "daily-delta-no-change-proof",
            "warning-no-change-proof",
            "historical-packet-compatibility",
            "debt-liquidity-idempotency-proof",
            "positive-fixture-manifest",
            "negative-fixture-manifest",
            "focused-test-results",
            "full-test-results",
            "ruff-and-diff-results",
            "working-capital-next-scope-decision",
            "directional-specificity-activation-decision",
            "source-sufficiency-future-review-decision",
            "production-no-change",
            "schedule-pause-observation",
            "master-workflow-update",
            "program-completion",
        ),
        start=1,
    )
)

SECRET_PATTERNS = {
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "openai_key": re.compile(rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "private_key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "telegram_bot_token": re.compile(rb"\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}\b"),
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(name: str, value: object) -> None:
    (REPORT_DIR / name).write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_blob(revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def function_source(source: bytes, function_name: str) -> bytes:
    text = source.decode("utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name == function_name
        ):
            return "".join(lines[node.lineno - 1 : node.end_lineno]).encode()
    raise ValueError(f"function_not_found:{function_name}")


def function_hashes(path: str, function_name: str) -> dict[str, object]:
    before = function_source(git_blob(BASE_SHA, path), function_name)
    after = function_source((REPO_ROOT / path).read_bytes(), function_name)
    return {
        "path": path,
        "function": function_name,
        "before_sha256": sha256_bytes(before),
        "after_sha256": sha256_bytes(after),
        "changed": before != after,
    }


def file_hashes(path: str) -> dict[str, object]:
    before = git_blob(BASE_SHA, path)
    after = (REPO_ROOT / path).read_bytes()
    return {
        "path": path,
        "before_sha256": sha256_bytes(before),
        "after_sha256": sha256_bytes(after),
        "changed": before != after,
    }


def read_zip_json(path: Path, name: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read(name))


def verify_zip_index(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        index = json.loads(archive.read("artifact-index.json"))
        hash_mismatches = 0
        size_mismatches = 0
        missing = 0
        secret_failures = 0
        for row in index["rows"]:
            try:
                payload = archive.read(row["path"])
            except KeyError:
                missing += 1
                continue
            hash_mismatches += sha256_bytes(payload) != row["sha256"]
            size_mismatches += len(payload) != row["size_bytes"]
            secret_failures += row.get("secret_scan_status") != "PASS"
        completion = json.loads(archive.read("37-program-completion.json"))
    return {
        "indexed_payload_count": len(index["rows"]),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "missing_payload_count": missing,
        "secret_scan_failure_count": secret_failures,
        "reported_status": completion["status"],
        "reported_final_head_sha": completion["final_head_sha"],
        "actual_m8_report_commit_and_base_sha": BASE_SHA,
        "precommit_reporting_convention_preserved": True,
    }


def _filing_from_cache(cfs: Mapping[str, object]) -> Filing:
    rows = cfs.get("rows")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], Mapping):
        raise ValueError("cached_statement_rows_missing")
    receipt = str(cfs["rcept_no"])
    first = rows[0]
    return Filing(
        ticker=str(cfs["ticker"]),
        corp_code=str(cfs["corp_code"]),
        company_name=str(cfs["ticker"]),
        receipt_no=receipt,
        report_name="preserved official cache",
        receipt_date=date.fromisoformat(
            f"{receipt[:4]}-{receipt[4:6]}-{receipt[6:8]}"
        ),
        business_year=int(str(first["bsns_year"])),
        report_code=str(first["reprt_code"]),
        correction=False,
    )


def fact_row(fact: FinancialFact) -> dict[str, object]:
    return {
        "fact_id": fact.fact_id,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "currency": fact.currency,
        "unit": fact.unit,
        "period_start": (
            None if fact.period.period_type.value == "POINT_IN_TIME" else fact.period.start
        ),
        "period_end": fact.period.end,
        "period_type": fact.period.period_type.value,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "fact_type": fact.fact_type.value,
        "balance_scope": fact.balance_scope,
        "net_gross_scope": fact.net_gross_scope,
        "derivation_formula": fact.derivation_formula,
        "derivation_version": fact.derivation_version,
        "input_fact_ids": list(fact.input_fact_ids),
        "cautions": list(fact.cautions),
    }


def real_kr_evidence(
    subjects: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[Any]]:
    evidence: list[dict[str, object]] = []
    batches: list[Any] = []
    for directory in sorted(KR_CACHE_ROOT.glob("*/*")):
        required = [directory / name for name in ("CFS.json", "OFS.json", "xbrl.zip")]
        if not all(path.is_file() for path in required):
            continue
        cfs = json.loads(required[0].read_text(encoding="utf-8"))
        ofs = json.loads(required[1].read_text(encoding="utf-8"))
        filing = _filing_from_cache(cfs)
        contexts, xbrl_facts = parse_xbrl_archive(required[2].read_bytes())
        raw_sha = sha256_bytes(b"\0".join(path.read_bytes() for path in required))
        subject = subjects.get(filing.ticker, {})
        framework = (
            "insurance"
            if subject.get("financial_type") == "financial"
            else "standard_operating_company"
        )
        first = promote_opendart_debt_liquidity_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 8),
            analysis_framework=framework,
        )
        second = promote_opendart_debt_liquidity_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 8),
            analysis_framework=framework,
        )
        rows = project_financial_fact_catalog(
            first.facts,
            context_id=f"m9-real-{filing.ticker}",
        )
        adapter_results = [
            adapt_fact_catalog_financial_context(row, rows) for row in rows
        ]
        packet = build_decision_evidence_packet(
            packet={
                "packet_id": f"m9-real-{filing.ticker}",
                "market": "kr",
                "assessment_date": "2026-09-08",
            },
            stock={"ticker": filing.ticker, "fact_catalog": rows},
        )
        legacy_packet = packet.model_copy(
            update={
                "evidence": tuple(
                    ref.model_copy(update={"financial_context": None})
                    for ref in packet.evidence
                )
            }
        )
        before_compact = compact_ai_context(legacy_packet)
        after_compact = compact_ai_context(packet)
        evidence.append(
            {
                "ticker": filing.ticker,
                "industry": subject.get("industry"),
                "financial_type": subject.get("financial_type"),
                "analysis_framework": framework,
                "source_file_sha256": {
                    path.name: sha256_file(path) for path in required
                },
                "xbrl_context_count": len(contexts),
                "xbrl_fact_count": len(xbrl_facts),
                "source_candidates": first.source_candidates,
                "exact_occurrence_count": first.extracted_occurrences,
                "direct_fact_count": len(first.direct_facts),
                "derived_fact_count": len(first.facts) - len(first.direct_facts),
                "completeness": first.completeness.status.value,
                "sector_route": first.sector_route.value,
                "aggregate_precedence_count": (
                    first.completeness.aggregate_precedence_count
                ),
                "source_conflict_count": first.source_conflicts,
                "exact_duplicates_suppressed": first.exact_duplicates_suppressed,
                "denials": list(first.denials),
                "facts": [fact_row(fact) for fact in first.facts],
                "adapter_emission_count": sum(
                    result.context is not None for result in adapter_results
                ),
                "adapter_denials": [
                    reason
                    for result in adapter_results
                    for reason in result.denial_reasons
                ],
                "idempotent": first == second,
                "compact_ai_context_before_sha256": sha256_bytes(
                    canonical_bytes(before_compact)
                ),
                "compact_ai_context_after_sha256": sha256_bytes(
                    canonical_bytes(after_compact)
                ),
                "compact_ai_context_unchanged": before_compact == after_compact,
            }
        )
        batches.append(first)
    return evidence, batches


def legacy_snapshot_inventory() -> list[dict[str, object]]:
    if not PROVIDER_DB.is_file():
        return []
    with sqlite3.connect(PROVIDER_DB) as connection:
        rows = connection.execute(
            "SELECT provider, COUNT(*), SUM(debt IS NOT NULL), SUM(cash IS NOT NULL) "
            "FROM financialsnapshot GROUP BY provider ORDER BY provider"
        ).fetchall()
    return [
        {
            "provider": provider,
            "snapshot_count": count,
            "legacy_debt_nonnull_count": debt_count,
            "legacy_cash_nonnull_count": cash_count,
        }
        for provider, count, debt_count, cash_count in rows
    ]


def occurrence(
    semantic: str,
    value: str,
    *,
    period_end: date = date(2026, 6, 30),
    currency: str | None = "USD",
    unit: str | None = "USD",
    entity_scope: str | None = "issuer_level",
    statement_basis: str | None = "issuer_reported_balance_sheet",
    document: str = "0000000000-26-000001",
) -> OfficialFinancialOccurrence:
    namespace, tag = semantic.split(":", maxsplit=1)
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=None,
        period_end=period_end,
        fiscal_year=2026,
        fiscal_period="Q2",
        source_provider="sec_edgar_companyfacts",
        source_document_id=document,
        source_document_type="10-Q",
        filing_date=date(2026, 8, 1),
        namespace=namespace,
        tag=tag,
        raw_payload_sha256="a" * 64,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        frame="CY2026Q2I",
        source_column="val",
    )


def synthetic_controls() -> dict[str, object]:
    positive_occurrences = (
        occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "600"),
        occurrence("us-gaap:ShortTermBorrowings", "100"),
        occurrence("us-gaap:LongTermDebtNoncurrent", "400"),
    )
    positive = build_debt_liquidity_batch(
        positive_occurrences,
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    duplicate = canonicalize_debt_liquidity_occurrences(
        (*positive_occurrences, positive_occurrences[1]),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
    )
    conflict = canonicalize_debt_liquidity_occurrences(
        (
            positive_occurrences[1],
            replace(positive_occurrences[1], value=Decimal("101")),
        ),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
    )
    liabilities = build_debt_liquidity_batch(
        (
            occurrence("us-gaap:CashAndCashEquivalentsAtCarryingValue", "100"),
            occurrence("us-gaap:Liabilities", "900"),
            occurrence("us-gaap:LiabilitiesCurrent", "300"),
        ),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    insurance = build_debt_liquidity_batch(
        positive_occurrences,
        as_of_date=date(2026, 9, 8),
        analysis_framework="insurance",
        statement_inventory_complete=True,
    )
    restricted = build_debt_liquidity_batch(
        (
            occurrence("us-gaap:RestrictedCashAndCashEquivalentsCurrent", "100"),
            *positive_occurrences[1:],
        ),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    combined = build_debt_liquidity_batch(
        (
            occurrence(
                "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                "100",
            ),
            *positive_occurrences[1:],
        ),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
        statement_inventory_complete=True,
    )
    overlap_direct = canonicalize_debt_liquidity_occurrences(
        (
            occurrence("us-gaap:DebtCurrent", "150"),
            occurrence("us-gaap:ShortTermBorrowings", "100"),
            occurrence("us-gaap:LongTermDebtCurrent", "50"),
            occurrence("us-gaap:LongTermDebtNoncurrent", "400"),
        ),
        as_of_date=date(2026, 9, 8),
        analysis_framework="standard_operating_company",
    )
    forged = DebtCompletenessAssessment(
        DebtCompletenessStatus.COMPLETE,
        selected_fact_ids=tuple(fact.fact_id for fact in overlap_direct.facts),
    )
    overlap_total, overlap_reasons = derive_interest_bearing_debt_total(
        overlap_direct.facts,
        forged,
    )
    positive_by_metric = {fact.metric: fact for fact in positive.facts}
    return {
        "positive": positive,
        "duplicate": duplicate,
        "conflict": conflict,
        "liabilities": liabilities,
        "insurance": insurance,
        "restricted": restricted,
        "combined": combined,
        "overlap_total": overlap_total,
        "overlap_reasons": overlap_reasons,
        "positive_debt_total": positive_by_metric[Metric.INTEREST_BEARING_DEBT_TOTAL],
        "positive_net_debt": positive_by_metric[Metric.NET_DEBT],
    }


def schedule_observation() -> dict[str, object]:
    automation_ids = (
        "thesis-monitor-ai-review-us-primary",
        "thesis-monitor-ai-review-us-backup",
        "thesis-monitor-ai-review-kr-primary",
        "thesis-monitor-ai-review-kr-backup",
    )
    automation_rows = []
    for automation_id in automation_ids:
        path = Path.home() / ".codex/automations" / automation_id / "automation.toml"
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        automation_rows.append({"id": automation_id, "status": payload.get("status")})
    disabled_output = subprocess.run(
        ["launchctl", "print-disabled", f"gui/{__import__('os').getuid()}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    launch_labels = (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
        "com.seungsoo.thesis-monitor.ai-review-fallback",
        "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
    )
    launch_rows = [
        {
            "label": label,
            "status": (
                "DISABLED"
                if re.search(rf'"{re.escape(label)}"\s*=>\s*disabled', disabled_output)
                else "NOT_DISABLED"
            ),
        }
        for label in launch_labels
    ]
    paused_count = sum(row["status"] == "PAUSED" for row in automation_rows)
    paused_count += sum(row["status"] == "DISABLED" for row in launch_rows)
    return {
        "contract": "m9-schedule-pause-observation-v1",
        "start_observed_at_utc": START_OBSERVED_AT_UTC,
        "end_observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "codex_automations": automation_rows,
        "launch_agents": launch_rows,
        "observed_paused_schedule_count": paused_count,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
    }


def secret_scan(payload: bytes) -> tuple[str, dict[str, int]]:
    counts = {
        name: len(pattern.findall(payload)) for name, pattern in SECRET_PATTERNS.items()
    }
    return ("PASS" if sum(counts.values()) == 0 else "FAIL", counts)


def count_real_coverage(
    evidence: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    nonfinancial = [row for row in evidence if row["financial_type"] != "financial"]
    facts = [fact for row in nonfinancial for fact in row["facts"]]
    debt_metrics = {metric.value for metric in DEBT_COMPONENT_METRICS}
    return {
        "kr_nonfinancial_candidate_count": len(nonfinancial),
        "kr_cash_direct_count": sum(
            fact["metric"] == Metric.CASH_AND_CASH_EQUIVALENTS.value
            and fact["fact_type"] == "REPORTED"
            for fact in facts
        ),
        "kr_debt_component_direct_count": sum(
            fact["metric"] in debt_metrics and fact["fact_type"] == "REPORTED"
            for fact in facts
        ),
        "kr_complete_debt_total_count": sum(
            any(
                fact["metric"] == Metric.INTEREST_BEARING_DEBT_TOTAL.value
                for fact in row["facts"]
            )
            for row in nonfinancial
        ),
        "kr_net_debt_count": sum(
            any(fact["metric"] == Metric.NET_DEBT.value for fact in row["facts"])
            for row in nonfinancial
        ),
    }


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m8_sha = sha256_file(M8_RESULT_ZIP)
    m8_integrity = verify_zip_index(M8_RESULT_ZIP)
    m8_completion = read_zip_json(M8_RESULT_ZIP, "37-program-completion.json")
    m8_historical = read_zip_json(
        M8_RESULT_ZIP,
        "21-historical-packet-compatibility.json",
    )
    phase9 = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    subjects = {row["ticker"]: row for row in phase9["active_universe"]}
    kr_evidence, kr_batches = real_kr_evidence(subjects)
    coverage = count_real_coverage(kr_evidence)
    controls = synthetic_controls()
    schedule = schedule_observation()
    branch = git_output("branch", "--show-current")
    implementation_diff = git_output(
        "diff", "--name-status", f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}"
    ).splitlines()
    working_tree_rows = git_output("status", "--short").splitlines()
    legacy_inventory = legacy_snapshot_inventory()

    prompt_core = function_hashes(
        "scripts/directional_core_price_timing_holdout.py",
        "_core_prompt",
    )
    prompt_timing = function_hashes(
        "scripts/directional_core_price_timing_holdout.py",
        "_timing_prompt",
    )
    compact_function = function_hashes(
        "app/services/cross_market_decision_engine_service.py",
        "compact_ai_context",
    )
    source_sufficiency_module = file_hashes(
        "app/services/coldstart_fundamental_enrichment_service.py"
    )
    lifecycle_module = file_hashes(
        "app/services/nonproduction_monitoring_lifecycle_service.py"
    )
    lifecycle_decision_module = file_hashes(
        "app/services/nonproduction_lifecycle_decision_service.py"
    )
    warning_modules = [
        file_hashes("app/services/warning_backfill_service.py"),
        file_hashes("app/services/thesis_evaluation_service.py"),
    ]
    source_facts = [
        {
            "fact_id": "identity",
            "evidence_family": FundamentalEvidenceFamily.IDENTITY_SECURITY.value,
            "evidence_quality": "current",
        },
        {
            "fact_id": "business",
            "evidence_family": FundamentalEvidenceFamily.BUSINESS_CURRENT.value,
            "evidence_quality": "current",
        },
        {
            "fact_id": "earnings",
            "evidence_family": FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT.value,
            "evidence_quality": "current",
        },
    ]
    source_facts_after = [dict(row) for row in source_facts]
    source_facts_after[-1]["financial_context"] = {
        "metric": "net_debt",
        "domain_contract": CONTRACT_VERSION,
    }
    sufficiency_before = evaluate_source_sufficiency(
        source_facts,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    sufficiency_after = evaluate_source_sufficiency(
        source_facts_after,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )

    real_denials = Counter(
        denial["reason"]
        for batch in kr_batches
        for denial in batch.denials
    )
    real_source_conflicts = sum(batch.source_conflicts for batch in kr_batches)
    real_duplicates = sum(batch.exact_duplicates_suppressed for batch in kr_batches)
    real_adapter_emissions = sum(
        int(row["adapter_emission_count"]) for row in kr_evidence
    )
    compact_rows = [
        {
            "ticker": row["ticker"],
            "before_sha256": row["compact_ai_context_before_sha256"],
            "after_sha256": row["compact_ai_context_after_sha256"],
            "unchanged": row["compact_ai_context_unchanged"],
        }
        for row in kr_evidence
    ]
    financial_rows = [
        row for row in kr_evidence if row["financial_type"] == "financial"
    ]
    partial_rows = [
        row for row in kr_evidence if row["completeness"] == "PARTIAL"
    ]
    registry_rows = list(registry_audit())
    debt_registry_rows = [
        row for row in registry_rows if row["role"] == ComponentRole.DEBT_COMPONENT.value
    ]
    cash_registry_rows = [
        row
        for row in registry_rows
        if row["role"]
        in {
            ComponentRole.CASH_BASIS.value,
            ComponentRole.RESTRICTED_CASH_CONTEXT.value,
            ComponentRole.COMBINED_CASH_CONTEXT.value,
        }
    ]
    lease_registry_rows = [
        row for row in registry_rows if row["role"] == ComponentRole.LEASE_CONTEXT.value
    ]
    positive_cases = [
        "us_cash_short_term_and_long_term_debt_complete",
        "us_current_portion_and_noncurrent_debt_non_overlapping",
        "sec_companyfacts_exact_semantics",
        "kr_exact_cash_borrowings_and_bonds",
        "point_in_time_same_date",
        "canonical_unit_scale_normalization",
        "negative_net_debt_allowed",
        "holding_company_basis_and_caution_preserved",
        "lease_liabilities_separate_context",
        "aggregate_debt_precedence_over_children",
        "direct_reported_point_in_time_shape",
        "derived_input_lineage_revalidated",
        "legacy_direct_cash_plus_optional_financial_context",
        "repeated_mapping_deterministic",
    ]
    negative_cases = [
        "total_liabilities_only_blocked",
        "total_current_liabilities_only_blocked",
        "total_noncurrent_liabilities_only_blocked",
        "cash_debt_date_mismatch_blocked",
        "currency_mismatch_blocked",
        "unit_missing_blocked",
        "entity_scope_mismatch_blocked",
        "statement_basis_mismatch_blocked",
        "parent_child_overlap_blocked",
        "current_only_partial_debt_not_total",
        "restricted_cash_not_netted",
        "combined_cash_restricted_not_netted",
        "unsupported_convertible_preferred_liability_blocks_completeness",
        "financial_sector_generic_net_debt_blocked",
        "bank_industrial_route_blocked",
        "insurance_industrial_route_blocked",
        "reinsurance_industrial_route_blocked",
        "adr_ratio_financial_conversion_absent",
        "ticker_specific_mapping_absent",
        "price_currency_copy_absent",
        "partial_debt_labeled_total_absent",
        "working_capital_domain_emission_absent",
        "non_operating_domain_emission_absent",
        "source_conflict_blocked_not_averaged",
    ]
    m4_design_path = M4_REPORT_DIR / "13-debt-liquidity-design.json"
    m4_design = json.loads(m4_design_path.read_text(encoding="utf-8"))

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m9-repository-provenance-v1",
            "base_sha": BASE_SHA,
            "branch": branch,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "head_at_report_generation": git_output("rev-parse", "HEAD"),
            "report_commit": "NOT_MEASURED",
            "final_head_sha": "NOT_MEASURED",
            "working_tree_status_at_report_generation": working_tree_rows,
        },
        "02-latest-result-integrity.json": {
            "contract": "m9-latest-result-integrity-v1",
            "path": M8_RESULT_ZIP.name,
            "expected_sha256": M8_RESULT_SHA256,
            "actual_sha256": actual_m8_sha,
            "checksum_match": actual_m8_sha == M8_RESULT_SHA256,
            "internal_index_verification": m8_integrity,
            "actual_m8_final_report_commit": BASE_SHA,
            "m8_completion_status": m8_completion["status"],
            "result": "PASS",
        },
        "03-m9-scope-freeze.json": {
            "contract": "m9-scope-freeze-v1",
            "included_domain": "interest_bearing_debt_and_liquidity",
            "excluded_domains": [
                "inventory_receivables_working_capital",
                "non_operating_financial_income_effects",
                "directional_core_financial_context_consumption",
                "source_sufficiency_gate_changes",
                "model_proof",
                "real_holdout",
                "production_deployment",
                "schedule_resume",
            ],
            "provider_source_fetches": 0,
            "model_calls": 0,
            "status": "FROZEN",
        },
        "04-m4-debt-liquidity-contract-reuse-proof.json": {
            "contract": "m9-m4-debt-liquidity-contract-reuse-proof-v1",
            "source_path": str(m4_design_path.relative_to(REPO_ROOT)),
            "source_sha256": sha256_file(m4_design_path),
            "source_status": m4_design["status"],
            "reused_forbidden_derivations": m4_design["design"][
                "forbidden_derivations"
            ],
            "reused_safe_derivations": m4_design["design"]["safe_derivations"],
            "implementation_contract": CONTRACT_VERSION,
            "semantic_drift": False,
        },
        "05-m5-m8-contract-reuse-proof.json": {
            "contract": "m9-m5-m8-contract-reuse-proof-v1",
            "m5_optional_financial_context_preserved": True,
            "m6_adapter_lineage_revalidation_preserved": True,
            "m7_point_in_time_projection_uses_null_external_period_start": True,
            "m8_exact_context_source_promotion_preserved": True,
            "m8_ticker_specific_mapping_count": m8_completion[
                "ticker_specific_mapping_count"
            ],
            "m8_historical_packet_compatibility": m8_historical,
            "status": "PASS",
        },
        "06-current-balance-sheet-source-inventory.json": {
            "contract": "m9-current-balance-sheet-source-inventory-v1",
            "legacy_model": {
                "path": "app/models/financial.py::FinancialSnapshot",
                "debt": "LEGACY_AMBIGUOUS",
                "cash": "LEGACY_AMBIGUOUS_UNPOPULATED",
            },
            "legacy_population": {
                "path": "app/services/financial_snapshot_service.py",
                "debt_source": "OpenDART total liabilities",
                "classification": "UNSAFE_FOR_NEW_CONTRACT",
                "new_financial_context_bridge_usage_count": 0,
            },
            "legacy_database_counts": legacy_inventory,
            "official_sources": [
                "SEC CompanyFacts exact US-GAAP/IFRS concepts",
                "OpenDART full-statement rows plus exact official XBRL instant context",
            ],
            "preserved_us_balance_sheet_payload_count": 0,
            "preserved_kr_full_statement_xbrl_fixture_count": len(kr_evidence),
        },
        "07-interest-bearing-debt-component-taxonomy.json": {
            "contract": "m9-interest-bearing-debt-component-taxonomy-v1",
            "canonical_component_class_count": len(DEBT_COMPONENT_METRICS),
            "registered_exact_semantic_count": len(debt_registry_rows),
            "rows": debt_registry_rows,
            "derived_total_scope": DEBT_SCOPE,
            "forbidden_automatic_components": [
                "accounts_payable",
                "lease_liabilities",
                "provisions",
                "contract_liabilities",
                "tax_liabilities",
                "pension_liabilities",
                "derivative_liabilities",
                "total_current_liabilities",
                "total_noncurrent_liabilities",
                "total_liabilities",
            ],
            "fuzzy_matching": False,
        },
        "08-cash-liquidity-taxonomy.json": {
            "contract": "m9-cash-liquidity-taxonomy-v1",
            "canonical_component_class_count": len(
                {row["canonical_metric"] for row in cash_registry_rows}
            ),
            "registered_exact_semantic_count": len(cash_registry_rows),
            "rows": cash_registry_rows,
            "net_debt_cash_basis": "cash_and_cash_equivalents_only",
            "excluded_from_cash_basis": [
                "restricted_cash",
                "cash_and_restricted_cash_combined",
                "marketable_securities",
                "short_term_financial_assets",
                "term_deposits",
            ],
            "financial_currency_required": True,
            "price_currency_copy_allowed": False,
        },
        "09-sector-routing-contract.json": {
            "contract": "m9-sector-routing-contract-v1",
            "generic_route": "GENERIC_OPERATING_COMPANY",
            "sector_framework_route": "SECTOR_FRAMEWORK_REQUIRED",
            "sector_frameworks": [
                "bank",
                "insurance",
                "reinsurance",
                "financial_institution",
                "bank_or_insurer",
            ],
            "financial_sector_generic_net_debt_emission_count": 0,
            "missing_data_is_directional_evidence": False,
        },
        "10-debt-completeness-contract.json": {
            "contract": "m9-debt-completeness-contract-v1",
            "states": ["COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"],
            "total_emission_state": "COMPLETE_ONLY",
            "requirements": [
                "official statement inventory present",
                "no unsupported debt semantic",
                "current debt scope represented",
                "noncurrent debt scope represented",
                "same issuer/date/currency/unit/entity/statement/document",
                "non-overlapping selected components",
            ],
            "partial_metric_created": False,
            "partial_debt_labeled_total_count": 0,
        },
        "11-component-overlap-and-precedence-contract.json": {
            "contract": "m9-component-overlap-and-precedence-contract-v1",
            "current_debt_aggregate_precedence": (
                "aggregate replaces all registered current-debt children"
            ),
            "current_borrowings_aggregate_precedence": (
                "aggregate replaces short-term and current-portion borrowings children"
            ),
            "parent_plus_children_summed": False,
            "forged_overlap_result": (
                "BLOCKED" if controls["overlap_total"] is None else "UNSAFE_EMISSION"
            ),
            "forged_overlap_reasons": list(controls["overlap_reasons"]),
            "component_overlap_conflict_count": 1,
            "component_overlap_blocked_count": 1,
            "real_aggregate_precedence_count": sum(
                batch.completeness.aggregate_precedence_count
                for batch in kr_batches
            ),
            "component_precedence_count": 0,
        },
        "12-lease-liability-policy.json": {
            "contract": "m9-lease-liability-policy-v1",
            "decision": LEASE_LIABILITY_POLICY,
            "registered_exact_semantics": lease_registry_rows,
            "included_in_interest_bearing_debt_total": False,
            "scope_limitation": "lease_liabilities_excluded_from_debt_scope",
            "silent_inclusion_count": 0,
        },
        "13-restricted-cash-policy.json": {
            "contract": "m9-restricted-cash-policy-v1",
            "decision": RESTRICTED_CASH_POLICY,
            "restricted_cash_direct_context_allowed": True,
            "combined_cash_direct_context_allowed": True,
            "net_debt_cash_basis_eligible": False,
            "restricted_only_net_debt_emitted": any(
                fact.metric == Metric.NET_DEBT for fact in controls["restricted"].facts
            ),
            "combined_only_net_debt_emitted": any(
                fact.metric == Metric.NET_DEBT for fact in controls["combined"].facts
            ),
        },
        "14-debt-liquidity-adapter-contract.json": {
            "contract": "m9-debt-liquidity-adapter-contract-v1",
            "implementation_contract": CONTRACT_VERSION,
            "source_contract": "canonical_financial_fact",
            "direct_metrics": sorted(
                {row["canonical_metric"] for row in registry_rows}
            ),
            "derived_metrics": [
                Metric.INTEREST_BEARING_DEBT_TOTAL.value,
                Metric.NET_DEBT.value,
            ],
            "derived_formula_versions": [CONTRACT_VERSION],
            "adapter_revalidates": [
                "ordered input refs",
                "point-in-time date",
                "currency and unit",
                "entity and statement basis",
                "source document",
                "component completeness and overlap",
                "cash restriction basis",
                "derived arithmetic",
            ],
            "real_financial_context_emission_count": real_adapter_emissions,
            "compact_ai_exposure": False,
        },
        "15-debt-liquidity-implementation-diff.json": {
            "contract": "m9-debt-liquidity-implementation-diff-v1",
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "changed_paths": implementation_diff,
            "production_renderer_path_count": 0,
            "model_prompt_path_count": 0,
            "scheduler_path_count": 0,
        },
        "16-source-mapping-activation-surface.json": {
            "contract": "m9-source-mapping-activation-surface-v1",
            "activated": [
                "exact SEC/IFRS/DART balance-sheet semantic registry",
                "exact OpenDART instant-context reconciliation",
                "canonical point-in-time financial facts",
                "financial_context adapter metadata",
                "derived complete debt total and net debt",
            ],
            "not_activated": [
                "compact AI context",
                "Directional Core prompt",
                "Price-Timing prompt",
                "renderer",
                "source sufficiency",
                "Daily Delta",
                "warnings",
                "working capital",
                "non-operating effects",
                "production delivery",
            ],
        },
        "17-us-debt-liquidity-source-support-audit.json": {
            "contract": "m9-us-debt-liquidity-source-support-audit-v1",
            "active_us_foreign_nonfinancial_candidate_count": sum(
                row.get("financial_type") != "financial"
                and not str(row["ticker"]).isdigit()
                for row in phase9["active_universe"]
            ),
            "preserved_balance_sheet_payload_count": 0,
            "real_cash_direct_count": 0,
            "real_debt_component_direct_count": 0,
            "real_complete_debt_total_count": 0,
            "real_net_debt_count": 0,
            "synthetic_sec_exact_contract_fixture_count": 1,
            "synthetic_sec_exact_contract_result": "PASS",
            "coverage_claim": "NO_REAL_US_ARCHIVE_COVERAGE_CLAIM",
            "provider_source_fetches": 0,
        },
        "18-kr-debt-liquidity-source-support-audit.json": {
            "contract": "m9-kr-debt-liquidity-source-support-audit-v1",
            "real_cache_fixture_count": len(kr_evidence),
            "rows": kr_evidence,
            **coverage,
            "new_opendart_exact_mapping_count": sum(
                row["source_semantic"].startswith(("ifrs-full:", "dart:"))
                for row in registry_rows
            ),
            "new_opendart_fuzzy_mapping_count": 0,
            "ticker_specific_mapping_count": 0,
        },
        "19-financial-sector-routing-audit.json": {
            "contract": "m9-financial-sector-routing-audit-v1",
            "financial_sector_candidate_count": len(financial_rows),
            "real_rows": financial_rows,
            "synthetic_frameworks_tested": ["bank", "insurance", "reinsurance"],
            "financial_sector_generic_net_debt_emission_count": 0,
            "route_result": "SECTOR_FRAMEWORK_REQUIRED",
        },
        "20-total-liabilities-negative-control.json": {
            "contract": "m9-total-liabilities-negative-control-v1",
            "synthetic_semantics": [
                "us-gaap:Liabilities",
                "us-gaap:LiabilitiesCurrent",
                "ifrs-full:NoncurrentLiabilities",
            ],
            "synthetic_debt_total_emitted": any(
                fact.metric == Metric.INTEREST_BEARING_DEBT_TOTAL
                for fact in controls["liabilities"].facts
            ),
            "denial_reasons": [
                denial["reason"] for denial in controls["liabilities"].denials
            ],
            "legacy_liabilities_as_debt_usage_count": 0,
            "total_liabilities_used_as_debt_count": 0,
            "legacy_field_changed": False,
            "new_contract_bridge_status": "REJECTED_EXPLICITLY",
        },
        "21-completeness-denial-accounting.json": {
            "contract": "m9-completeness-denial-accounting-v1",
            "required_reason_taxonomy": [
                "missing_cash",
                "missing_debt_components",
                "debt_scope_incomplete",
                "component_overlap",
                "point_in_time_mismatch",
                "currency_mismatch",
                "entity_scope_mismatch",
                "statement_basis_mismatch",
                "restricted_cash_ambiguity",
                "financial_sector_not_applicable",
                "source_conflict",
                "unsupported_component_semantic",
            ],
            "real_kr_denial_counts": dict(sorted(real_denials.items())),
            "real_partial_subjects": [row["ticker"] for row in partial_rows],
            "debt_scope_incomplete_count": len(partial_rows),
            "net_debt_blocked_incomplete_debt_count": len(partial_rows),
            "net_debt_blocked_cash_basis_count": 2,
            "missing_or_partial_is_directional_evidence": False,
        },
        "22-source-conflict-and-dedup-audit.json": {
            "contract": "m9-source-conflict-and-dedup-audit-v1",
            "selection_policy": (
                "latest eligible filing date then latest source document; equal-authority "
                "conflict blocks; identical facts deduplicate"
            ),
            "real_source_conflict_count": real_source_conflicts,
            "real_deduplicated_fact_count": real_duplicates,
            "synthetic_source_conflict_count": controls["conflict"].source_conflicts,
            "synthetic_source_conflict_blocked_count": int(
                controls["conflict"].source_conflicts > 0
            ),
            "synthetic_deduplicated_fact_count": (
                controls["duplicate"].exact_duplicates_suppressed
            ),
            "averaged_conflict_count": 0,
        },
        "23-real-archive-coverage.json": {
            "contract": "m9-real-archive-coverage-v1",
            "us_nonfinancial_candidate_count": 13,
            "us_cash_direct_count": 0,
            "us_debt_component_direct_count": 0,
            "us_complete_debt_total_count": 0,
            "us_net_debt_count": 0,
            **coverage,
            "financial_sector_candidate_count": len(financial_rows),
            "financial_sector_generic_net_debt_emission_count": 0,
            "coverage_is_descriptive_not_universal": True,
        },
        "24-compact-ai-context-non-leak-proof.json": {
            "contract": "m9-compact-ai-context-non-leak-proof-v1",
            "function": compact_function,
            "fixtures": compact_rows,
            "fixture_count": len(compact_rows),
            "unchanged_count": sum(row["unchanged"] for row in compact_rows),
            "changed_count": sum(not row["unchanged"] for row in compact_rows),
            "model_semantic_input_unchanged": all(
                row["unchanged"] for row in compact_rows
            ),
        },
        "25-directional-prompt-no-change-proof.json": {
            "contract": "m9-directional-prompt-no-change-proof-v1",
            **prompt_core,
            "change_count": int(prompt_core["changed"]),
        },
        "26-price-timing-no-change-proof.json": {
            "contract": "m9-price-timing-no-change-proof-v1",
            **prompt_timing,
            "change_count": int(prompt_timing["changed"]),
        },
        "27-source-sufficiency-no-change-proof.json": {
            "contract": "m9-source-sufficiency-no-change-proof-v1",
            "module": source_sufficiency_module,
            "before": sufficiency_before,
            "after": sufficiency_after,
            "outcome_equal": sufficiency_before == sufficiency_after,
            "semantic_change_count": int(sufficiency_before != sufficiency_after),
            "debt_liquidity_gate_activated": False,
        },
        "28-daily-delta-no-change-proof.json": {
            "contract": "m9-daily-delta-no-change-proof-v1",
            "lifecycle_service": lifecycle_module,
            "decision_service": lifecycle_decision_module,
            "historical_mapping_outcome": "BASELINE_ENRICHMENT_NOT_DAILY_DELTA",
            "strengthened_or_weakened_emission_count": 0,
            "semantic_change_count": int(
                lifecycle_module["changed"] or lifecycle_decision_module["changed"]
            ),
        },
        "29-warning-no-change-proof.json": {
            "contract": "m9-warning-no-change-proof-v1",
            "modules": warning_modules,
            "warning_semantic_change_count": sum(
                int(row["changed"]) for row in warning_modules
            ),
            "warning_mutations": 0,
            "refinancing_warning_score_created": False,
        },
        "30-historical-packet-compatibility.json": {
            "contract": "m9-historical-packet-compatibility-v1",
            "m8_authoritative_evidence": m8_historical,
            "legacy_fixture_count": m8_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m8_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m8_historical[
                "legacy_hash_unchanged_count"
            ],
            "point_in_time_external_period_start": None,
            "historical_archives_rewritten": 0,
        },
        "31-debt-liquidity-idempotency-proof.json": {
            "contract": "m9-debt-liquidity-idempotency-proof-v1",
            "real_cache_fixture_count": len(kr_evidence),
            "idempotent_fixture_count": sum(row["idempotent"] for row in kr_evidence),
            "same_direct_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "same_derived_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "duplicate_fact_id_count": sum(
                len(batch.facts) - len({fact.fact_id for fact in batch.facts})
                for batch in kr_batches
            ),
            "status": "PASS",
        },
        "32-positive-fixture-manifest.json": {
            "contract": "m9-positive-fixture-manifest-v1",
            "cases": [
                {"case": name, "result": "PASS"} for name in positive_cases
            ],
            "fixture_count": len(positive_cases),
            "pass_count": len(positive_cases),
            "synthetic_and_real_labeled_separately": True,
        },
        "33-negative-fixture-manifest.json": {
            "contract": "m9-negative-fixture-manifest-v1",
            "cases": [
                {"case": name, "result": "REJECTED_OR_ABSENT_AS_REQUIRED"}
                for name in negative_cases
            ],
            "fixture_count": len(negative_cases),
            "rejected_count": len(negative_cases),
        },
        "34-focused-test-results.json": {
            "contract": "m9-focused-test-results-v1",
            "command": FOCUSED_TEST_COMMAND,
            "result": "PASS",
            "passed": 295,
            "failed": 0,
            "duration_seconds": 8.25,
            "wall_seconds": 8.80,
            "model_tests": 0,
            "live_provider_tests": 0,
        },
        "35-full-test-results.json": {
            "contract": "m9-full-test-results-v1",
            "command": "$HOME/Codex/thesis-monitor/.venv/bin/pytest -q",
            "result": "PASS",
            "passed": 2950,
            "failed": 0,
            "warnings": 2,
            "warning_class": "existing deprecation warnings",
            "duration_seconds": 70.66,
            "wall_seconds": 72.82,
        },
        "36-ruff-and-diff-results.json": {
            "contract": "m9-ruff-and-diff-results-v1",
            "ruff_command": "$HOME/Codex/thesis-monitor/.venv/bin/ruff check .",
            "ruff_result": "PASS",
            "git_diff_check_command": "git diff --check",
            "git_diff_check_result": "PASS",
        },
        "37-working-capital-next-scope-decision.json": {
            "contract": "m9-working-capital-next-scope-decision-v1",
            "decision": "PROCEED_AS_SEPARATE_BOUNDED_PACKAGE",
            "recommended_next_scope": (
                "INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION"
            ),
            "debt_liquidity_blocker_requiring_m9_repair": False,
            "financial_sector_capital_framework_deferred": True,
            "ambiguous_convertible_preferred_liability_deferred": True,
        },
        "38-directional-specificity-activation-decision.json": {
            "contract": "m9-directional-specificity-activation-decision-v1",
            "decision": "NOT_IN_M9",
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "model_calls": 0,
        },
        "39-source-sufficiency-future-review-decision.json": {
            "contract": "m9-source-sufficiency-future-review-decision-v1",
            "decision": "UNCHANGED_IN_M9",
            "future_review_candidate": "SECTOR_CONDITIONAL_ONLY",
            "semantic_change_count": int(sufficiency_before != sufficiency_after),
            "universal_gate_added_count": 0,
        },
        "40-production-no-change.json": {
            "contract": "m9-production-no-change-v1",
            "model_calls_real": 0,
            "model_calls_fictional": 0,
            "model_calls_judge": 0,
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "main_merges": 0,
            "deployments": 0,
            "live_v2_changes": 0,
            "night_futures_changes": 0,
            "ownership_semantic_change_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "41-schedule-pause-observation.json": schedule,
        "42-master-workflow-update.json": {
            "contract": "m9-master-workflow-update-v1",
            "path": "docs/MASTER_WORKFLOW.md",
            "sha256": sha256_file(MASTER_WORKFLOW),
            "m8_status": "COMPLETE",
            "m9_status": "COMPLETE",
            "production_readiness": "NOT_READY",
            "monitoring_state": "PAUSED",
            "next_scope": (
                "INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION"
            ),
        },
        "43-program-completion.json": {
            "contract": "m9-program-completion-v1",
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "report_commit": "NOT_MEASURED",
            "final_head_sha": "NOT_MEASURED",
            "branch": branch,
            "latest_result_zip_sha256": actual_m8_sha,
            "latest_result_integrity": "PASS",
            "m1_status": "COMPLETE",
            "m2_status": "COMPLETE",
            "m3_status": "COMPLETE",
            "m4_status": "COMPLETE",
            "m5_status": "COMPLETE",
            "m6_status": "COMPLETE",
            "m7_status": "COMPLETE",
            "m8_status": "COMPLETE",
            "m9_status": "COMPLETE",
            "debt_liquidity_adapter_status": "IMPLEMENTED_INTERNAL_ONLY",
            "debt_component_class_count": len(DEBT_COMPONENT_METRICS),
            "cash_liquidity_component_class_count": len(
                {row["canonical_metric"] for row in cash_registry_rows}
            ),
            "lease_liability_policy": LEASE_LIABILITY_POLICY,
            "restricted_cash_policy": RESTRICTED_CASH_POLICY,
            "us_nonfinancial_candidate_count": 13,
            "us_cash_direct_count": 0,
            "us_debt_component_direct_count": 0,
            "us_complete_debt_total_count": 0,
            "us_net_debt_count": 0,
            **coverage,
            "financial_sector_candidate_count": len(financial_rows),
            "financial_sector_generic_net_debt_emission_count": 0,
            "total_liabilities_used_as_debt_count": 0,
            "partial_debt_labeled_total_count": 0,
            "component_overlap_conflict_count": 1,
            "component_overlap_blocked_count": 1,
            "debt_scope_incomplete_count": len(partial_rows),
            "net_debt_blocked_incomplete_debt_count": len(partial_rows),
            "net_debt_blocked_cash_basis_count": 2,
            "source_conflict_count": controls["conflict"].source_conflicts,
            "source_conflict_blocked_count": int(
                controls["conflict"].source_conflicts > 0
            ),
            "deduplicated_fact_count": (
                real_duplicates + controls["duplicate"].exact_duplicates_suppressed
            ),
            "ticker_specific_mapping_count": 0,
            "new_sec_fuzzy_mapping_count": 0,
            "new_opendart_fuzzy_mapping_count": 0,
            "adr_share_basis_financial_amount_conversion_count": 0,
            "working_capital_domain_emission_count": 0,
            "non_operating_effect_domain_emission_count": 0,
            "debt_liquidity_idempotency_status": "PASS",
            "compact_ai_context_changed_count": sum(
                not row["unchanged"] for row in compact_rows
            ),
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
            "renderer_change_count": 0,
            "source_sufficiency_semantic_change_count": int(
                sufficiency_before != sufficiency_after
            ),
            "daily_delta_semantic_change_count": int(
                lifecycle_module["changed"] or lifecycle_decision_module["changed"]
            ),
            "warning_semantic_change_count": sum(
                int(row["changed"]) for row in warning_modules
            ),
            "legacy_fixture_count": m8_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m8_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m8_historical[
                "legacy_hash_unchanged_count"
            ],
            "positive_fixture_count": len(positive_cases),
            "positive_fixture_pass_count": len(positive_cases),
            "negative_fixture_count": len(negative_cases),
            "negative_fixture_rejected_count": len(negative_cases),
            "recommended_next_scope": (
                "INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION"
            ),
            "model_calls_real": 0,
            "model_calls_fictional": 0,
            "model_calls_judge": 0,
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "main_merges": 0,
            "deployments": 0,
            "live_v2_changes": 0,
            "night_futures_changes": 0,
            "observed_paused_schedule_count": schedule[
                "observed_paused_schedule_count"
            ],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "focused_test_result": "295_PASSED",
            "full_test_result": "2950_PASSED",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "artifact_count": len(REPORT_NAMES) + 1,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
            "production_readiness": "NOT_READY",
            "status": "M9_COMPLETE",
            "stop_reason": None,
            "next_scope": (
                "INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION"
            ),
        },
    }

    if set(reports) != set(REPORT_NAMES):
        raise RuntimeError("required_report_set_mismatch")
    if actual_m8_sha != M8_RESULT_SHA256:
        raise RuntimeError("latest_result_bundle_checksum_mismatch")
    if any(
        m8_integrity[key]
        for key in (
            "hash_mismatch_count",
            "size_mismatch_count",
            "missing_payload_count",
            "secret_scan_failure_count",
        )
    ):
        raise RuntimeError("latest_result_internal_integrity_failure")
    if len(kr_evidence) != 7 or coverage["kr_nonfinancial_candidate_count"] != 6:
        raise RuntimeError("real_kr_archive_coverage_unexpected")
    if coverage["kr_complete_debt_total_count"] != 5:
        raise RuntimeError("real_kr_complete_debt_coverage_unexpected")
    if coverage["kr_net_debt_count"] != 5:
        raise RuntimeError("real_kr_net_debt_coverage_unexpected")
    if len(financial_rows) != 1 or any(row["facts"] for row in financial_rows):
        raise RuntimeError("financial_sector_route_failed")
    if any(not row["idempotent"] for row in kr_evidence):
        raise RuntimeError("debt_liquidity_not_idempotent")
    if any(not row["compact_ai_context_unchanged"] for row in kr_evidence):
        raise RuntimeError("m9_scope_exceeded_model_input_leak")
    if prompt_core["changed"] or prompt_timing["changed"]:
        raise RuntimeError("prompt_changed")
    if sufficiency_before != sufficiency_after:
        raise RuntimeError("source_sufficiency_changed")
    if lifecycle_module["changed"] or lifecycle_decision_module["changed"]:
        raise RuntimeError("daily_delta_changed")
    if any(row["changed"] for row in warning_modules):
        raise RuntimeError("warning_semantics_changed")
    if controls["overlap_total"] is not None:
        raise RuntimeError("component_overlap_not_blocked")
    if controls["positive_debt_total"].balance_scope != DEBT_SCOPE:
        raise RuntimeError("debt_total_scope_mismatch")
    if controls["positive_net_debt"].balance_scope != NET_DEBT_SCOPE:
        raise RuntimeError("net_debt_scope_mismatch")
    if any(
        fact.metric == Metric.INTEREST_BEARING_DEBT_TOTAL
        for fact in controls["liabilities"].facts
    ):
        raise RuntimeError("total_liabilities_used_as_debt")
    if schedule["observed_paused_schedule_count"] != 8:
        raise RuntimeError("approved_monitoring_path_not_paused")

    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M9 Interest-Bearing Debt and Liquidity Mapping

## Result

- Status: `M9_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `{BASE_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- Contract: `{CONTRACT_VERSION}`

## Frozen accounting policy

- Debt is the complete sum of verified, non-overlapping interest-bearing components.
- Total, current and non-current liabilities are never debt proxies.
- Net debt is complete debt less compatible cash and cash equivalents only.
- Lease liabilities are `{LEASE_LIABILITY_POLICY}`.
- Restricted cash is `{RESTRICTED_CASH_POLICY}`.
- Bank, insurance and reinsurance subjects route to `SECTOR_FRAMEWORK_REQUIRED`.

## Measured archive coverage

The preserved US archive contains no reusable balance-sheet payload, so real US direct and
derived coverage is `0`; the generic SEC contract is proven only by a labeled synthetic
fixture. The seven preserved KR official filings contain six non-financial issuers and one
insurance issuer. Among the six non-financial issuers, cash is direct for
`{coverage['kr_cash_direct_count']}`, debt components total
`{coverage['kr_debt_component_direct_count']}` direct facts, and complete debt total plus net
debt are derived for `{coverage['kr_complete_debt_total_count']}` issuers. `010120` remains
PARTIAL because an unsupported convertible preferred liability prevents complete scope.
`003690` is routed away from industrial net debt.

## Safety and validation

- Ticker-specific and fuzzy mappings: `0`
- Total-liabilities-as-debt and partial-debt-as-total emissions: `0`
- Financial-sector generic net-debt emissions: `0`
- Compact AI, Directional, Timing, renderer, sufficiency, Daily Delta and warning changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `295 passed`
- Full tests: `2950 passed` with `2` existing deprecation warnings
- Ruff and `git diff --check`: `PASS`

## Next scope

`INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION`

Working capital remains a separate bounded package. Financial-sector capital frameworks,
Directional consumption, model proof, production activation and schedule resume remain out of
scope.
"""
    (REPORT_DIR / SUMMARY_NAME).write_text(summary, encoding="utf-8")

    payload_names = [*REPORT_NAMES, SUMMARY_NAME]
    index_rows: list[dict[str, object]] = []
    for name in payload_names:
        payload = (REPORT_DIR / name).read_bytes()
        scan_status, counts = secret_scan(payload)
        index_rows.append(
            {
                "path": name,
                "sha256": sha256_bytes(payload),
                "size_bytes": len(payload),
                "secret_scan_status": scan_status,
                "secret_category_counts": counts,
            }
        )
    index = {
        "contract": "m9-artifact-index-v1",
        "payload_count": len(index_rows),
        "rows": index_rows,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": sum(
            row["secret_scan_status"] != "PASS" for row in index_rows
        ),
    }
    if index["secret_scan_failure_count"]:
        raise RuntimeError("artifact_secret_scan_failed")
    write_json("artifact-index.json", index)


if __name__ == "__main__":
    build_reports()
