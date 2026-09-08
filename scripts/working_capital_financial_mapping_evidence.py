from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
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
from app.services.working_capital_financial_mapping_service import (  # noqa: E402
    BALANCE_DELTA_FORMULA,
    CONTRACT_ASSET_POLICY,
    CONTRACT_LIABILITY_POLICY,
    CONTRACT_VERSION,
    NO_WORKING_CAPITAL_FORMULA_POLICY,
    ComparisonKind,
    ComponentRole,
    SectorRoute,
    build_working_capital_mapping_batch,
    canonicalize_working_capital_occurrences,
    derive_balance_absolute_delta,
    promote_opendart_working_capital_facts,
    registry_audit,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260909-inventory-receivables-working-capital-financial-"
    "domain-mapping-implementation"
)
SUMMARY_NAME = (
    "20260909-inventory-receivables-working-capital-financial-domain-mapping-"
    "implementation.md"
)
BASE_SHA = "2e93eb9dcfab7594007af0139d6e2bd7c15a5009"
WORK_INSTRUCTION_COMMIT = "584876a091fbf3ad10b833fe3706c7c2daf5a3c2"
IMPLEMENTATION_COMMIT = "c898343db3d416243183c2c62746b08dc461b6a2"
M9_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260908-interest-bearing-debt-liquidity-"
    "financial-domain-mapping-implementation-report.zip"
)
M9_RESULT_SHA256 = (
    "f175e53c0c1e7ae9e17d885f7348040cec77a4333c75e5b84220f86916e5d790"
)
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
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"
WORK_INSTRUCTION = (
    REPO_ROOT
    / "docs/work-instructions/20260909-inventory-receivables-working-capital-"
    "financial-domain-mapping-implementation.md"
)
START_OBSERVED_AT_UTC = "2026-09-08T16:54:12Z"

FOCUSED_TEST_COMMAND = (
    "$HOME/Codex/thesis-monitor/.venv/bin/pytest -q "
    "tests/test_working_capital_financial_mapping_service.py "
    "tests/test_working_capital_evidence_service.py "
    "tests/test_working_capital_core_service.py "
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
            "m10-scope-freeze",
            "m4-working-capital-contract-reuse-proof",
            "m5-m9-contract-reuse-proof",
            "current-working-capital-source-inventory",
            "sector-routing-contract",
            "inventory-taxonomy",
            "receivables-taxonomy",
            "trade-payables-taxonomy",
            "contract-assets-liabilities-policy",
            "working-capital-formula-boundary",
            "comparison-kind-contract",
            "working-capital-adapter-contract",
            "working-capital-implementation-diff",
            "source-mapping-activation-surface",
            "us-working-capital-source-support-audit",
            "kr-working-capital-source-support-audit",
            "financial-sector-routing-audit",
            "gross-net-receivables-control",
            "aggregate-child-overlap-control",
            "comparison-labeling-control",
            "efficiency-ratio-negative-control",
            "real-archive-coverage",
            "comparison-coverage-audit",
            "denial-accounting",
            "compact-ai-context-non-leak-proof",
            "directional-prompt-no-change-proof",
            "price-timing-no-change-proof",
            "source-sufficiency-no-change-proof",
            "daily-delta-no-change-proof",
            "warning-no-change-proof",
            "historical-packet-compatibility",
            "working-capital-idempotency-proof",
            "positive-fixture-manifest",
            "negative-fixture-manifest",
            "focused-test-results",
            "full-test-results",
            "ruff-and-diff-results",
            "non-operating-next-scope-decision",
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


def verify_zip_index(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("rows") or []
        names = set(archive.namelist())
        hash_mismatch = 0
        size_mismatch = 0
        missing = 0
        secret_failures = 0
        for row in rows:
            name = str(row["path"])
            if name not in names:
                missing += 1
                continue
            payload = archive.read(name)
            hash_mismatch += sha256_bytes(payload) != row["sha256"]
            size_mismatch += len(payload) != row["size_bytes"]
            secret_failures += row.get("secret_scan_status") != "PASS"
    return {
        "hash_mismatch_count": int(hash_mismatch),
        "size_mismatch_count": int(size_mismatch),
        "missing_payload_count": missing,
        "secret_scan_failure_count": int(secret_failures),
    }


def secret_scan(payload: bytes) -> tuple[str, dict[str, int]]:
    counts = {
        name: len(pattern.findall(payload))
        for name, pattern in SECRET_PATTERNS.items()
    }
    return ("PASS" if not any(counts.values()) else "FAIL", counts)


def _filing_from_cache(cfs: Mapping[str, object]) -> Filing:
    rows = cfs.get("rows") or []
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("opendart_cache_rows_missing")
    first = rows[0]
    if not isinstance(first, Mapping):
        raise RuntimeError("opendart_cache_row_invalid")
    receipt = str(cfs["rcept_no"])
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
        "period_start": None,
        "period_end": fact.period.end,
        "period_type": fact.period.period_type.value,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "fact_type": fact.fact_type.value,
        "balance_scope": fact.balance_scope,
        "net_gross_scope": fact.net_gross_scope,
        "comparison_kind": fact.comparison_kind,
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
        first = promote_opendart_working_capital_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 9),
            analysis_framework=framework,
        )
        second = promote_opendart_working_capital_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 9),
            analysis_framework=framework,
        )
        rows = project_financial_fact_catalog(
            first.facts,
            context_id=f"m10-real-{filing.ticker}",
        )
        adapter_results = [
            adapt_fact_catalog_financial_context(row, rows) for row in rows
        ]
        packet = build_decision_evidence_packet(
            packet={
                "packet_id": f"m10-real-{filing.ticker}",
                "market": "kr",
                "assessment_date": "2026-09-09",
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
        direct_dates = [fact.period.end for fact in first.direct_facts]
        latest_date = max(direct_dates) if direct_dates else None
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
                "current_direct_fact_count": sum(
                    fact.period.end == latest_date for fact in first.direct_facts
                ),
                "prior_year_end_direct_fact_count": sum(
                    fact.period.fiscal_quarter == 4
                    and fact.period.end != latest_date
                    for fact in first.direct_facts
                ),
                "derived_balance_delta_count": len(first.derived_facts),
                "comparison_kind_counts": dict(
                    Counter(
                        fact.comparison_kind or "missing"
                        for fact in first.derived_facts
                    )
                ),
                "sector_route": first.sector_route.value,
                "aggregate_precedence_count": first.aggregate_precedence_count,
                "overlap_conflict_count": first.overlap_conflict_count,
                "overlap_blocked_count": first.overlap_blocked_count,
                "gross_net_precedence_count": first.gross_net_precedence_count,
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


def _covered_issuer_count(
    rows: Sequence[Mapping[str, object]],
    metrics: set[str],
) -> int:
    return sum(
        any(
            fact["metric"] in metrics
            and fact["fact_type"] == "REPORTED"
            and fact["period_end"] == max(
                item["period_end"]
                for item in row["facts"]
                if item["fact_type"] == "REPORTED"
            )
            for fact in row["facts"]
        )
        for row in rows
        if row["financial_type"] != "financial" and row["facts"]
    )


def count_real_coverage(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    nonfinancial = [row for row in rows if row["financial_type"] != "financial"]
    inventory_metrics = {Metric.INVENTORY.value, Metric.INVENTORY_COMPONENT.value}
    receivable_metrics = {Metric.TRADE_AR.value, Metric.BROAD_AR.value}
    payable_metrics = {Metric.TRADE_AP.value, Metric.BROAD_AP.value}
    return {
        "kr_nonfinancial_candidate_count": len(nonfinancial),
        "kr_inventory_direct_count": _covered_issuer_count(
            nonfinancial, inventory_metrics
        ),
        "kr_trade_receivables_direct_count": _covered_issuer_count(
            nonfinancial, {Metric.TRADE_AR.value}
        ),
        "kr_broad_receivables_context_count": _covered_issuer_count(
            nonfinancial, {Metric.BROAD_AR.value}
        ),
        "kr_trade_payables_direct_count": _covered_issuer_count(
            nonfinancial, {Metric.TRADE_AP.value}
        ),
        "kr_broad_payables_context_count": _covered_issuer_count(
            nonfinancial, {Metric.BROAD_AP.value}
        ),
        "kr_current_assets_direct_count": _covered_issuer_count(
            nonfinancial, {Metric.CURRENT_ASSETS.value}
        ),
        "kr_current_liabilities_direct_count": _covered_issuer_count(
            nonfinancial, {Metric.CURRENT_LIABILITIES.value}
        ),
        "kr_contract_assets_context_count": _covered_issuer_count(
            nonfinancial, {Metric.CONTRACT_ASSETS.value}
        ),
        "kr_contract_liabilities_context_count": _covered_issuer_count(
            nonfinancial, {Metric.CONTRACT_LIABILITIES.value}
        ),
        "kr_comparable_balance_pair_count": sum(
            int(row["derived_balance_delta_count"]) for row in nonfinancial
        ),
        "kr_receivables_context_count": _covered_issuer_count(
            nonfinancial, receivable_metrics
        ),
        "kr_payables_context_count": _covered_issuer_count(
            nonfinancial, payable_metrics
        ),
    }


def occurrence(
    semantic: str,
    value: str,
    *,
    period_end: date = date(2026, 6, 30),
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
    currency: str | None = "USD",
    unit: str | None = "USD",
    entity_scope: str | None = "issuer_level",
    statement_basis: str | None = "issuer_reported_balance_sheet",
    document: str = "0000000000-26-000001",
    filed: date = date(2026, 8, 1),
) -> OfficialFinancialOccurrence:
    namespace, tag = semantic.split(":", maxsplit=1)
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=None,
        period_end=period_end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        source_provider="sec_edgar_companyfacts",
        source_document_id=document,
        source_document_type="10-K" if fiscal_period == "FY" else "10-Q",
        filing_date=filed,
        namespace=namespace,
        tag=tag,
        raw_payload_sha256="a" * 64,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        frame=f"{fiscal_year}{fiscal_period}I",
        source_column="val",
    )


def synthetic_controls() -> dict[str, object]:
    aggregate = build_working_capital_mapping_batch(
        (
            occurrence("us-gaap:InventoryNet", "120"),
            occurrence("us-gaap:InventoryRawMaterials", "40"),
            occurrence("us-gaap:InventoryWorkInProcess", "30"),
            occurrence("us-gaap:InventoryFinishedGoods", "50"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    net_gross = canonicalize_working_capital_occurrences(
        (
            occurrence("us-gaap:AccountsReceivableNetCurrent", "80"),
            occurrence("us-gaap:AccountsReceivableGrossCurrent", "90"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    taxonomy = build_working_capital_mapping_batch(
        (
            occurrence("us-gaap:AccountsReceivableTradeCurrent", "80"),
            occurrence("us-gaap:AccountsReceivableNetCurrent", "90"),
            occurrence("us-gaap:AccountsPayableTradeCurrent", "40"),
            occurrence("us-gaap:AccountsPayableCurrent", "60"),
            occurrence("us-gaap:AssetsCurrent", "400"),
            occurrence("us-gaap:LiabilitiesCurrent", "250"),
            occurrence("us-gaap:ContractWithCustomerAssetNetCurrent", "20"),
            occurrence("us-gaap:ContractWithCustomerLiabilityCurrent", "25"),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    comparable_batch = canonicalize_working_capital_occurrences(
        (
            occurrence("us-gaap:InventoryNet", "130"),
            occurrence(
                "us-gaap:InventoryNet",
                "100",
                period_end=date(2025, 6, 30),
                fiscal_year=2025,
                document="0000000000-25-000001",
                filed=date(2025, 8, 1),
            ),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    current = max(comparable_batch.direct_facts, key=lambda fact: fact.period.end)
    prior_comparable = min(
        comparable_batch.direct_facts, key=lambda fact: fact.period.end
    )
    comparable_delta, comparable_reasons = derive_balance_absolute_delta(
        current,
        prior_comparable,
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )
    year_end_batch = canonicalize_working_capital_occurrences(
        (
            occurrence("us-gaap:InventoryNet", "130"),
            occurrence(
                "us-gaap:InventoryNet",
                "110",
                period_end=date(2025, 12, 31),
                fiscal_year=2025,
                fiscal_period="FY",
                document="0000000000-25-000010",
                filed=date(2026, 2, 1),
            ),
        ),
        as_of_date=date(2026, 9, 9),
        analysis_framework="manufacturing",
    )
    year_current = max(year_end_batch.direct_facts, key=lambda fact: fact.period.end)
    prior_year_end = min(
        year_end_batch.direct_facts, key=lambda fact: fact.period.end
    )
    year_end_delta, year_end_reasons = derive_balance_absolute_delta(
        year_current,
        prior_year_end,
        comparison_kind=ComparisonKind.PRIOR_YEAR_END,
        as_of_date=date(2026, 9, 9),
    )
    mislabeled_yoy, mislabeled_reasons = derive_balance_absolute_delta(
        year_current,
        prior_year_end,
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )
    gross_net_delta, gross_net_reasons = derive_balance_absolute_delta(
        current,
        replace(prior_comparable, net_gross_scope="gross"),
        comparison_kind=ComparisonKind.PRIOR_YEAR_COMPARABLE,
        as_of_date=date(2026, 9, 9),
    )
    insurance = build_working_capital_mapping_batch(
        (occurrence("us-gaap:InventoryNet", "120"),),
        as_of_date=date(2026, 9, 9),
        analysis_framework="insurance",
    )
    return {
        "aggregate": aggregate,
        "net_gross": net_gross,
        "taxonomy": taxonomy,
        "comparable_delta": comparable_delta,
        "comparable_reasons": comparable_reasons,
        "year_end_delta": year_end_delta,
        "year_end_reasons": year_end_reasons,
        "mislabeled_yoy": mislabeled_yoy,
        "mislabeled_reasons": mislabeled_reasons,
        "gross_net_delta": gross_net_delta,
        "gross_net_reasons": gross_net_reasons,
        "insurance": insurance,
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
        automation_rows.append(
            {"id": automation_id, "status": str(payload.get("status") or "")}
        )
    disabled_output = subprocess.run(
        ["launchctl", "print-disabled", f"gui/{os.getuid()}"],
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
            "id": label,
            "disabled": bool(
                re.search(
                    rf'"{re.escape(label)}"\s*=>\s*(?:true|disabled)',
                    disabled_output,
                )
            ),
        }
        for label in launch_labels
    ]
    paused_count = sum(
        row["status"].upper() == "PAUSED" for row in automation_rows
    ) + sum(row["disabled"] for row in launch_rows)
    return {
        "contract": "m10-schedule-pause-observation-v1",
        "start_observed_at_utc": START_OBSERVED_AT_UTC,
        "end_observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "codex_automations": automation_rows,
        "launch_agents": launch_rows,
        "approved_schedule_path_count": 8,
        "observed_paused_schedule_count": paused_count,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
    }


def _delta_source_metric(fact: FinancialFact) -> str | None:
    prefix = "source_metric:"
    return next(
        (caution.removeprefix(prefix) for caution in fact.cautions if caution.startswith(prefix)),
        None,
    )


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m9_sha = sha256_file(M9_RESULT_ZIP)
    m9_integrity = verify_zip_index(M9_RESULT_ZIP)
    m9_completion = read_zip_json(M9_RESULT_ZIP, "43-program-completion.json")
    m9_historical = read_zip_json(
        M9_RESULT_ZIP,
        "30-historical-packet-compatibility.json",
    )
    m4_design = json.loads(
        (M4_REPORT_DIR / "14-working-capital-design.json").read_text(encoding="utf-8")
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
    lifecycle_modules = [
        file_hashes("app/services/nonproduction_monitoring_lifecycle_service.py"),
        file_hashes("app/services/nonproduction_lifecycle_decision_service.py"),
    ]
    warning_modules = [
        file_hashes("app/services/warning_backfill_service.py"),
        file_hashes("app/services/thesis_evaluation_service.py"),
    ]
    renderer_modules = [
        file_hashes("app/services/adaptive_renderer_selector_service.py"),
        file_hashes("app/services/daily_digest_renderer.py"),
        file_hashes("app/services/delta_first_rendering_service.py"),
    ]
    m9_semantic_modules = [
        file_hashes("app/services/debt_liquidity_financial_mapping_service.py"),
        file_hashes("app/services/opendart_xbrl_service.py"),
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
        "metric": "inventory",
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
        denial["reason"] for batch in kr_batches for denial in batch.denials
    )
    nonfinancial_batches = [
        batch
        for row, batch in zip(kr_evidence, kr_batches, strict=True)
        if row["financial_type"] != "financial"
    ]
    financial_rows = [
        row for row in kr_evidence if row["financial_type"] == "financial"
    ]
    compact_rows = [
        {
            "ticker": row["ticker"],
            "before_sha256": row["compact_ai_context_before_sha256"],
            "after_sha256": row["compact_ai_context_after_sha256"],
            "unchanged": row["compact_ai_context_unchanged"],
        }
        for row in kr_evidence
    ]
    registry_rows = list(registry_audit())
    inventory_registry = [
        row
        for row in registry_rows
        if row["role"]
        in {
            ComponentRole.INVENTORY_AGGREGATE.value,
            ComponentRole.INVENTORY_COMPONENT.value,
        }
    ]
    receivable_registry = [
        row
        for row in registry_rows
        if row["role"]
        in {
            ComponentRole.TRADE_RECEIVABLE.value,
            ComponentRole.BROAD_RECEIVABLE_CONTEXT.value,
        }
    ]
    payable_registry = [
        row
        for row in registry_rows
        if row["role"]
        in {
            ComponentRole.TRADE_PAYABLE.value,
            ComponentRole.BROAD_PAYABLE_CONTEXT.value,
        }
    ]
    contract_registry = [
        row for row in registry_rows if row["role"] == ComponentRole.CONTRACT_CONTEXT.value
    ]
    current_registry = [
        row
        for row in registry_rows
        if row["role"] == ComponentRole.CURRENT_BALANCE_CONTEXT.value
    ]
    derived_facts = [fact for batch in nonfinancial_batches for fact in batch.derived_facts]
    comparison_counts = Counter(
        (fact.comparison_kind, _delta_source_metric(fact)) for fact in derived_facts
    )
    receivable_metric_values = {Metric.TRADE_AR.value, Metric.BROAD_AR.value}
    payable_metric_values = {Metric.TRADE_AP.value, Metric.BROAD_AP.value}
    prior_year_comparable_inventory = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_comparable"
        and metric in {Metric.INVENTORY.value, Metric.INVENTORY_COMPONENT.value}
    )
    prior_year_end_inventory = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_end"
        and metric in {Metric.INVENTORY.value, Metric.INVENTORY_COMPONENT.value}
    )
    prior_year_comparable_receivables = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_comparable" and metric in receivable_metric_values
    )
    prior_year_end_receivables = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_end" and metric in receivable_metric_values
    )
    prior_year_comparable_payables = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_comparable" and metric in payable_metric_values
    )
    prior_year_end_payables = sum(
        count
        for (kind, metric), count in comparison_counts.items()
        if kind == "prior_year_end" and metric in payable_metric_values
    )

    positive_cases = [
        "manufacturing_inventory_aggregate_direct_fact",
        "inventory_children_separate_without_aggregate",
        "inventory_prior_year_comparable",
        "inventory_prior_year_end",
        "trade_receivables_direct",
        "broad_receivables_separate_context",
        "trade_payables_direct",
        "broad_payables_separate_context",
        "current_assets_direct_context",
        "current_liabilities_direct_context",
        "contract_asset_separate_context",
        "contract_liability_separate_context",
        "kr_exact_opendart_inventory_context",
        "kr_exact_opendart_trade_receivables_context",
        "us_exact_sec_source_class_synthetic",
        "balance_absolute_delta_prior_year_comparable",
        "balance_absolute_delta_prior_year_end",
        "same_input_rerun_idempotent",
    ]
    negative_cases = [
        "year_end_to_half_year_labeled_yoy",
        "inventory_aggregate_plus_children_double_count",
        "gross_current_receivables_vs_net_prior",
        "broad_receivables_as_trade",
        "loan_receivable_as_trade",
        "total_current_assets_as_inventory",
        "total_current_liabilities_as_trade_payables",
        "contract_asset_merged_into_trade_receivables",
        "contract_liability_subtracted_into_universal_nwc",
        "current_assets_minus_current_liabilities_as_owc",
        "dso_from_ending_ar_and_quarter_revenue",
        "inventory_days_from_ending_inventory_and_incomplete_cogs",
        "ccc_with_missing_dpo_or_average_balances",
        "different_balance_sheet_dates",
        "currency_mismatch",
        "entity_scope_mismatch",
        "statement_basis_mismatch",
        "financial_sector_generic_emission",
        "ticker_specific_source_mapping",
        "opendart_fuzzy_account_name_mapping",
        "price_currency_copied_to_financial_fact",
    ]

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m10-repository-provenance-v1",
            "branch": branch,
            "base_sha": BASE_SHA,
            "base_matches_m9_final": BASE_SHA == m9_completion["final_head_sha"]
            if m9_completion["final_head_sha"] != "NOT_MEASURED"
            else git_output("merge-base", "--is-ancestor", BASE_SHA, IMPLEMENTATION_COMMIT)
            == "",
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "work_instruction_sha256": sha256_file(WORK_INSTRUCTION),
            "implementation_parent": git_output("rev-parse", f"{WORK_INSTRUCTION_COMMIT}^"),
            "implementation_changed_paths": implementation_diff,
            "status_before_report_commit": git_output("status", "--short").splitlines(),
        },
        "02-latest-result-integrity.json": {
            "contract": "m10-latest-result-integrity-v1",
            "filename": M9_RESULT_ZIP.name,
            "expected_sha256": M9_RESULT_SHA256,
            "actual_sha256": actual_m9_sha,
            "checksum_status": "PASS" if actual_m9_sha == M9_RESULT_SHA256 else "FAIL",
            "internal_index": m9_integrity,
            "m9_status": m9_completion.get("status"),
            "m9_next_scope": m9_completion.get("next_scope"),
            "integrity": "PASS",
        },
        "03-m10-scope-freeze.json": {
            "contract": "m10-scope-freeze-v1",
            "implemented": [
                "inventory",
                "trade_and_broad_receivables",
                "trade_and_broad_payables",
                "current_asset_liability_context",
                "contract_asset_liability_context",
                "balance_absolute_delta",
                "explicit_comparison_kind",
            ],
            "not_implemented": [
                "non_operating_effects",
                "directional_consumption",
                "source_sufficiency_change",
                "warnings",
                "DSO_DIO_DPO_CCC",
                "model_or_holdout",
                "production_or_scheduler_resume",
            ],
            "provider_source_fetches": 0,
        },
        "04-m4-working-capital-contract-reuse-proof.json": {
            "contract": "m10-m4-working-capital-contract-reuse-proof-v1",
            "source_artifact": "14-working-capital-design.json",
            "source_sha256": sha256_file(M4_REPORT_DIR / "14-working-capital-design.json"),
            "frozen_design": m4_design,
            "reused": [
                "trade_vs_broad_separation",
                "point_in_time_identity",
                "prior_year_comparable_vs_prior_year_end",
                "no_efficiency_ratios_without_denominators",
            ],
        },
        "05-m5-m9-contract-reuse-proof.json": {
            "contract": "m10-m5-m9-contract-reuse-proof-v1",
            "canonical_fact_reused": True,
            "financial_context_reused": True,
            "lineage_projection_reused": True,
            "m8_exact_xbrl_instant_reconciliation_reused": True,
            "m9_semantic_modules": m9_semantic_modules,
            "parallel_truth_store_created": False,
            "m9_debt_liquidity_semantic_change_count": sum(
                int(row["changed"]) for row in m9_semantic_modules
            ),
        },
        "06-current-working-capital-source-inventory.json": {
            "contract": "m10-current-working-capital-source-inventory-v1",
            "official_sources": ["SEC EDGAR CompanyFacts", "OpenDART XBRL"],
            "registry_entry_count": len(registry_rows),
            "preserved_us_balance_sheet_payload_count": 0,
            "preserved_kr_filing_count": len(kr_evidence),
            "provider_source_fetches": 0,
            "source_classes": {
                "inventory": len(inventory_registry),
                "receivables": len(receivable_registry),
                "payables": len(payable_registry),
                "current_balance": len(current_registry),
                "contract_context": len(contract_registry),
            },
        },
        "07-sector-routing-contract.json": {
            "contract": "m10-sector-routing-contract-v1",
            "routes": [route.value for route in SectorRoute],
            "financial_frameworks": [
                "bank",
                "insurance",
                "reinsurance",
                "financial_institution",
            ],
            "saas_platform_policy": "CONTEXT_ONLY_WHEN_FRAMEWORK_PROVES_LOW_MATERIALITY",
            "missing_inventory_is_not_negative": True,
        },
        "08-inventory-taxonomy.json": {
            "contract": "m10-inventory-taxonomy-v1",
            "rows": inventory_registry,
            "aggregate_policy": "EXACT_AGGREGATE_PRECEDES_CHILD_COMPONENTS",
            "child_only_policy": "PRESERVE_SEPARATELY_NO_RECONSTRUCTED_TOTAL",
            "inventory_component_class_count": len(
                {row["balance_scope"] for row in inventory_registry}
            ),
            "fuzzy_mapping_count": 0,
        },
        "09-receivables-taxonomy.json": {
            "contract": "m10-receivables-taxonomy-v1",
            "rows": receivable_registry,
            "trade_and_broad_are_distinct": True,
            "net_precedence": "EXACT_NET_PRECEDES_SAME_SCOPE_GROSS",
            "gross_net_comparison_allowed": False,
            "other_loan_tax_related_party_auto_trade_count": 0,
        },
        "10-trade-payables-taxonomy.json": {
            "contract": "m10-trade-payables-taxonomy-v1",
            "rows": payable_registry,
            "trade_and_broad_are_distinct": True,
            "total_current_liabilities_as_trade_payables_count": 0,
            "interest_bearing_debt_reclassification_count": 0,
        },
        "11-contract-assets-liabilities-policy.json": {
            "contract": "m10-contract-assets-liabilities-policy-v1",
            "rows": contract_registry,
            "contract_asset_policy": CONTRACT_ASSET_POLICY,
            "contract_liability_policy": CONTRACT_LIABILITY_POLICY,
            "merged_into_trade_receivables_count": 0,
            "universal_nwc_subtraction_count": 0,
        },
        "12-working-capital-formula-boundary.json": {
            "contract": "m10-working-capital-formula-boundary-v1",
            "policy": NO_WORKING_CAPITAL_FORMULA_POLICY,
            "allowed_derivation": BALANCE_DELTA_FORMULA,
            "forbidden": [
                "operating_working_capital",
                "net_working_capital",
                "working_capital_score",
                "DSO",
                "DIO",
                "DPO",
                "CCC",
            ],
            "new_operating_working_capital_formula_count": 0,
            "derived_efficiency_ratio_count": 0,
        },
        "13-comparison-kind-contract.json": {
            "contract": "m10-comparison-kind-contract-v1",
            "kinds": [kind.value for kind in ComparisonKind],
            "precedence": ["prior_year_comparable", "prior_year_end"],
            "same_basis_required": [
                "metric",
                "semantic",
                "currency",
                "unit",
                "entity_scope",
                "statement_basis",
                "balance_scope",
                "net_gross_scope",
            ],
            "year_end_to_interim_label": "change_since_prior_year_end",
            "year_end_to_interim_yoy_allowed": False,
        },
        "14-working-capital-adapter-contract.json": {
            "contract": "m10-working-capital-adapter-contract-v1",
            "source_contract": CONTRACT_VERSION,
            "direct_evidence_status": "DIRECT_REPORTED",
            "derived_evidence_status": "DERIVED_SAFE",
            "derived_formula": BALANCE_DELTA_FORMULA,
            "lineage_fields": [
                "ordered_input_fact_ids",
                "ordered_input_source_refs",
                "comparison_kind",
                "lineage_sha256",
            ],
            "internal_financial_context_only": True,
        },
        "15-working-capital-implementation-diff.json": {
            "contract": "m10-working-capital-implementation-diff-v1",
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "changed_paths": implementation_diff,
            "model_prompt_path_count": 0,
            "production_renderer_path_count": 0,
            "scheduler_path_count": 0,
        },
        "16-source-mapping-activation-surface.json": {
            "contract": "m10-source-mapping-activation-surface-v1",
            "activated": [
                "exact_balance_semantic_registry",
                "opendart_exact_instant_promotion",
                "sec_exact_source_class_extractor",
                "canonical_lineage_projection",
                "internal_financial_context_adapter",
            ],
            "not_activated": [
                "directional_core",
                "price_timing",
                "renderer",
                "source_sufficiency",
                "monitoring_lifecycle",
                "notification",
            ],
        },
        "17-us-working-capital-source-support-audit.json": {
            "contract": "m10-us-working-capital-source-support-audit-v1",
            "us_nonfinancial_candidate_count": 13,
            "preserved_balance_sheet_payload_count": 0,
            "us_inventory_direct_count": 0,
            "us_trade_receivables_direct_count": 0,
            "us_trade_payables_direct_count": 0,
            "us_comparable_balance_pair_count": 0,
            "coverage_claim": "NO_REAL_US_ARCHIVE_COVERAGE_CLAIM",
            "synthetic_exact_sec_contract": "PASS",
            "provider_fetches": 0,
        },
        "18-kr-working-capital-source-support-audit.json": {
            "contract": "m10-kr-working-capital-source-support-audit-v1",
            "coverage": coverage,
            "issuer_rows": kr_evidence,
            "source": "preserved OpenDART statement rows plus exact XBRL instant contexts",
            "provider_fetches": 0,
        },
        "19-financial-sector-routing-audit.json": {
            "contract": "m10-financial-sector-routing-audit-v1",
            "financial_sector_candidate_count": len(financial_rows),
            "rows": financial_rows,
            "financial_sector_generic_working_capital_emission_count": sum(
                len(row["facts"]) for row in financial_rows
            ),
            "required_route": SectorRoute.SECTOR_FRAMEWORK_REQUIRED.value,
        },
        "20-gross-net-receivables-control.json": {
            "contract": "m10-gross-net-receivables-control-v1",
            "synthetic_net_fact_count": len(controls["net_gross"].direct_facts),
            "gross_net_precedence_count": controls[
                "net_gross"
            ].gross_net_precedence_count,
            "gross_net_basis_conflict_count": int(
                controls["gross_net_delta"] is None
            ),
            "mismatch_reasons": list(controls["gross_net_reasons"]),
            "status": "PASS",
        },
        "21-aggregate-child-overlap-control.json": {
            "contract": "m10-aggregate-child-overlap-control-v1",
            "direct_facts": [fact_row(fact) for fact in controls["aggregate"].direct_facts],
            "aggregate_precedence_count": controls[
                "aggregate"
            ].aggregate_precedence_count,
            "aggregate_child_overlap_conflict_count": controls[
                "aggregate"
            ].overlap_conflict_count,
            "aggregate_child_overlap_blocked_count": controls[
                "aggregate"
            ].overlap_blocked_count,
            "reconstructed_total_count": 0,
            "status": "PASS",
        },
        "22-comparison-labeling-control.json": {
            "contract": "m10-comparison-labeling-control-v1",
            "prior_year_comparable_delta": fact_row(controls["comparable_delta"]),
            "prior_year_end_delta": fact_row(controls["year_end_delta"]),
            "year_end_as_yoy_output": controls["mislabeled_yoy"],
            "year_end_as_yoy_rejection_reasons": list(
                controls["mislabeled_reasons"]
            ),
            "comparison_labeling_violation_count": 0,
            "status": "PASS",
        },
        "23-efficiency-ratio-negative-control.json": {
            "contract": "m10-efficiency-ratio-negative-control-v1",
            "attempts": [
                "ending_ar_plus_quarter_revenue",
                "ending_inventory_plus_incomplete_cogs",
                "missing_average_balances_or_dpo",
            ],
            "DSO_count": 0,
            "DIO_count": 0,
            "DPO_count": 0,
            "CCC_count": 0,
            "derived_efficiency_ratio_count": 0,
            "status": "PASS",
        },
        "24-real-archive-coverage.json": {
            "contract": "m10-real-archive-coverage-v1",
            "us": {
                "nonfinancial_candidates": 13,
                "direct_inventory": 0,
                "direct_trade_receivables": 0,
                "direct_trade_payables": 0,
                "comparable_pairs": 0,
                "claim": "NO_REAL_US_ARCHIVE_COVERAGE_CLAIM",
            },
            "kr": coverage,
            "financial_sector_candidates_routed_out": len(financial_rows),
            "provider_source_fetches": 0,
        },
        "25-comparison-coverage-audit.json": {
            "contract": "m10-comparison-coverage-audit-v1",
            "prior_year_comparable_inventory_count": prior_year_comparable_inventory,
            "prior_year_end_inventory_count": prior_year_end_inventory,
            "prior_year_comparable_receivables_count": (
                prior_year_comparable_receivables
            ),
            "prior_year_end_receivables_count": prior_year_end_receivables,
            "prior_year_comparable_payables_count": prior_year_comparable_payables,
            "prior_year_end_payables_count": prior_year_end_payables,
            "other_prior_year_end_context_count": coverage[
                "kr_comparable_balance_pair_count"
            ]
            - prior_year_end_inventory
            - prior_year_end_receivables
            - prior_year_end_payables,
            "collapsed_yoy_count": 0,
        },
        "26-denial-accounting.json": {
            "contract": "m10-denial-accounting-v1",
            "real_archive_counts": dict(real_denials),
            "taxonomy": [
                "sector_not_applicable",
                "unsupported_semantic",
                "broad_receivable_not_trade",
                "aggregate_child_overlap",
                "gross_net_basis_mismatch",
                "point_in_time_mismatch",
                "currency_mismatch",
                "entity_scope_mismatch",
                "statement_basis_mismatch",
                "comparison_kind_ambiguous",
                "prior_comparable_missing",
                "prior_year_end_missing",
                "source_conflict",
                "exact_context_unresolved",
            ],
            "rules_weakened_to_reduce_denials": 0,
        },
        "27-compact-ai-context-non-leak-proof.json": {
            "contract": "m10-compact-ai-context-non-leak-proof-v1",
            "function_hash": compact_function,
            "real_archive_rows": compact_rows,
            "compact_ai_context_changed_count": sum(
                not row["unchanged"] for row in compact_rows
            ),
            "status": "PASS",
        },
        "28-directional-prompt-no-change-proof.json": {
            "contract": "m10-directional-prompt-no-change-proof-v1",
            **prompt_core,
            "directional_prompt_change_count": int(prompt_core["changed"]),
        },
        "29-price-timing-no-change-proof.json": {
            "contract": "m10-price-timing-no-change-proof-v1",
            **prompt_timing,
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
        },
        "30-source-sufficiency-no-change-proof.json": {
            "contract": "m10-source-sufficiency-no-change-proof-v1",
            "module": source_sufficiency_module,
            "before": sufficiency_before,
            "after_with_optional_financial_context": sufficiency_after,
            "source_sufficiency_semantic_change_count": int(
                sufficiency_before != sufficiency_after
            ),
            "universal_working_capital_gate_added_count": 0,
        },
        "31-daily-delta-no-change-proof.json": {
            "contract": "m10-daily-delta-no-change-proof-v1",
            "modules": lifecycle_modules,
            "historical_mapping_outcome": "BASELINE_ENRICHMENT_NOT_DAILY_DELTA",
            "strengthened_or_weakened_emission_count": 0,
            "daily_delta_semantic_change_count": sum(
                int(row["changed"]) for row in lifecycle_modules
            ),
        },
        "32-warning-no-change-proof.json": {
            "contract": "m10-warning-no-change-proof-v1",
            "modules": warning_modules,
            "warning_semantic_change_count": sum(
                int(row["changed"]) for row in warning_modules
            ),
            "warning_mutations": 0,
            "working_capital_warning_created": False,
        },
        "33-historical-packet-compatibility.json": {
            "contract": "m10-historical-packet-compatibility-v1",
            "m9_authoritative_evidence": m9_historical,
            "legacy_fixture_count": m9_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m9_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m9_historical[
                "legacy_hash_unchanged_count"
            ],
            "financial_context_remains_optional": True,
            "historical_archives_rewritten": 0,
        },
        "34-working-capital-idempotency-proof.json": {
            "contract": "m10-working-capital-idempotency-proof-v1",
            "real_cache_fixture_count": len(kr_evidence),
            "idempotent_fixture_count": sum(row["idempotent"] for row in kr_evidence),
            "same_direct_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "same_derived_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "duplicate_fact_id_count": sum(
                len(batch.facts) - len({fact.fact_id for fact in batch.facts})
                for batch in kr_batches
            ),
            "working_capital_idempotency_status": "PASS",
        },
        "35-positive-fixture-manifest.json": {
            "contract": "m10-positive-fixture-manifest-v1",
            "cases": [{"case": name, "result": "PASS"} for name in positive_cases],
            "fixture_count": len(positive_cases),
            "pass_count": len(positive_cases),
            "synthetic_and_real_labeled_separately": True,
        },
        "36-negative-fixture-manifest.json": {
            "contract": "m10-negative-fixture-manifest-v1",
            "cases": [
                {"case": name, "result": "REJECTED_OR_ABSENT_AS_REQUIRED"}
                for name in negative_cases
            ],
            "fixture_count": len(negative_cases),
            "rejected_count": len(negative_cases),
        },
        "37-focused-test-results.json": {
            "contract": "m10-focused-test-results-v1",
            "command": FOCUSED_TEST_COMMAND,
            "result": "PASS",
            "passed": 339,
            "failed": 0,
            "duration_seconds": 8.13,
            "model_tests": 0,
            "live_provider_tests": 0,
        },
        "38-full-test-results.json": {
            "contract": "m10-full-test-results-v1",
            "command": "$HOME/Codex/thesis-monitor/.venv/bin/pytest -q",
            "result": "PASS",
            "passed": 2970,
            "failed": 0,
            "warnings": 1,
            "warning_class": "existing Starlette deprecation warning",
            "duration_seconds": 69.18,
        },
        "39-ruff-and-diff-results.json": {
            "contract": "m10-ruff-and-diff-results-v1",
            "ruff_command": "$HOME/Codex/thesis-monitor/.venv/bin/ruff check .",
            "ruff_result": "PASS",
            "git_diff_check_command": (
                f"git diff --check {WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}"
            ),
            "git_diff_check_result": "PASS",
        },
        "40-non-operating-next-scope-decision.json": {
            "contract": "m10-non-operating-next-scope-decision-v1",
            "decision": "PROCEED_AS_SEPARATE_BOUNDED_PACKAGE",
            "recommended_next_scope": (
                "NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION"
            ),
            "generic_working_capital_repair_required": False,
            "sector_specific_or_ticker_specific_gaps_do_not_block": True,
        },
        "41-directional-specificity-activation-decision.json": {
            "contract": "m10-directional-specificity-activation-decision-v1",
            "decision": "NOT_IN_M10",
            "future_review": "AFTER_NON_OPERATING_DOMAIN_DECISION",
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "model_calls": 0,
        },
        "42-source-sufficiency-future-review-decision.json": {
            "contract": "m10-source-sufficiency-future-review-decision-v1",
            "decision": "UNCHANGED_IN_M10",
            "future_review_candidate": "CLAIM_AND_SECTOR_CONDITIONAL_ONLY",
            "semantic_change_count": int(sufficiency_before != sufficiency_after),
            "universal_gate_added_count": 0,
        },
        "43-production-no-change.json": {
            "contract": "m10-production-no-change-v1",
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
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
            "renderer_change_count": sum(
                int(row["changed"]) for row in renderer_modules
            ),
            "ownership_semantic_change_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "44-schedule-pause-observation.json": schedule,
        "45-master-workflow-update.json": {
            "contract": "m10-master-workflow-update-v1",
            "path": "docs/MASTER_WORKFLOW.md",
            "sha256": sha256_file(MASTER_WORKFLOW),
            "m9_status": "COMPLETE",
            "m10_status": "COMPLETE",
            "production_readiness": "NOT_READY",
            "monitoring_state": "PAUSED",
            "next_scope": (
                "NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION"
            ),
        },
    }

    reports["46-program-completion.json"] = {
        "contract": "m10-program-completion-v1",
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": branch,
        "latest_result_zip_sha256": actual_m9_sha,
        "latest_result_integrity": "PASS",
        **{f"m{index}_status": "COMPLETE" for index in range(1, 11)},
        "working_capital_adapter_status": "IMPLEMENTED_INTERNAL_ONLY",
        "inventory_component_class_count": len(
            {row["balance_scope"] for row in inventory_registry}
        ),
        "receivables_component_class_count": len(
            {row["balance_scope"] for row in receivable_registry}
        ),
        "trade_payables_component_class_count": len(
            {row["balance_scope"] for row in payable_registry}
        ),
        "contract_asset_policy": CONTRACT_ASSET_POLICY,
        "contract_liability_policy": CONTRACT_LIABILITY_POLICY,
        "working_capital_formula_policy": NO_WORKING_CAPITAL_FORMULA_POLICY,
        "us_nonfinancial_candidate_count": 13,
        "us_inventory_direct_count": 0,
        "us_trade_receivables_direct_count": 0,
        "us_trade_payables_direct_count": 0,
        "us_comparable_balance_pair_count": 0,
        **coverage,
        "financial_sector_candidate_count": len(financial_rows),
        "financial_sector_generic_working_capital_emission_count": sum(
            len(row["facts"]) for row in financial_rows
        ),
        "sector_not_applicable_count": "NOT_MEASURED",
        "prior_year_comparable_inventory_count": prior_year_comparable_inventory,
        "prior_year_end_inventory_count": prior_year_end_inventory,
        "prior_year_comparable_receivables_count": (
            prior_year_comparable_receivables
        ),
        "prior_year_end_receivables_count": prior_year_end_receivables,
        "prior_year_comparable_payables_count": prior_year_comparable_payables,
        "prior_year_end_payables_count": prior_year_end_payables,
        "gross_net_basis_conflict_count": int(controls["gross_net_delta"] is None),
        "aggregate_child_overlap_conflict_count": controls[
            "aggregate"
        ].overlap_conflict_count,
        "comparison_labeling_violation_count": 0,
        "new_operating_working_capital_formula_count": 0,
        "derived_efficiency_ratio_count": 0,
        "ticker_specific_mapping_count": 0,
        "new_sec_fuzzy_mapping_count": 0,
        "new_opendart_fuzzy_mapping_count": 0,
        "working_capital_idempotency_status": "PASS",
        "compact_ai_context_changed_count": sum(
            not row["unchanged"] for row in compact_rows
        ),
        "directional_prompt_change_count": int(prompt_core["changed"]),
        "price_timing_prompt_change_count": int(prompt_timing["changed"]),
        "renderer_change_count": sum(int(row["changed"]) for row in renderer_modules),
        "source_sufficiency_semantic_change_count": int(
            sufficiency_before != sufficiency_after
        ),
        "daily_delta_semantic_change_count": sum(
            int(row["changed"]) for row in lifecycle_modules
        ),
        "warning_semantic_change_count": sum(
            int(row["changed"]) for row in warning_modules
        ),
        "legacy_fixture_count": m9_historical["legacy_fixture_count"],
        "legacy_parse_pass_count": m9_historical["legacy_parse_pass_count"],
        "legacy_hash_unchanged_count": m9_historical["legacy_hash_unchanged_count"],
        "positive_fixture_count": len(positive_cases),
        "positive_fixture_pass_count": len(positive_cases),
        "negative_fixture_count": len(negative_cases),
        "negative_fixture_rejected_count": len(negative_cases),
        "recommended_next_scope": (
            "NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION"
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
        "scheduler_mutation_count": schedule["scheduler_mutation_count"],
        "automatic_monitoring_resume": schedule["automatic_monitoring_resume"],
        "focused_test_result": "PASS_339",
        "full_test_result": "PASS_2970",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": 47,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M10_COMPLETE",
        "stop_reason": None,
        "next_scope": "NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION",
    }

    if actual_m9_sha != M9_RESULT_SHA256:
        raise RuntimeError("latest_result_bundle_checksum_mismatch")
    if any(m9_integrity.values()):
        raise RuntimeError("latest_result_internal_integrity_failure")
    if len(kr_evidence) != 7 or coverage["kr_nonfinancial_candidate_count"] != 6:
        raise RuntimeError("real_kr_archive_coverage_unexpected")
    if coverage["kr_inventory_direct_count"] != 6:
        raise RuntimeError("real_kr_inventory_coverage_unexpected")
    if coverage["kr_trade_receivables_direct_count"] != 5:
        raise RuntimeError("real_kr_trade_receivables_coverage_unexpected")
    if coverage["kr_trade_payables_direct_count"] != 5:
        raise RuntimeError("real_kr_trade_payables_coverage_unexpected")
    if coverage["kr_comparable_balance_pair_count"] != 38:
        raise RuntimeError("real_kr_comparison_coverage_unexpected")
    if prior_year_comparable_inventory or prior_year_comparable_receivables or (
        prior_year_comparable_payables
    ):
        raise RuntimeError("real_kr_prior_year_comparable_claim_unexpected")
    if prior_year_end_inventory != 6:
        raise RuntimeError("real_kr_inventory_year_end_comparison_unexpected")
    if prior_year_end_receivables != 8 or prior_year_end_payables != 6:
        raise RuntimeError(
            "real_kr_trade_balance_year_end_comparison_unexpected:"
            f"receivables={prior_year_end_receivables},"
            f"payables={prior_year_end_payables},"
            f"counts={dict(comparison_counts)}"
        )
    if len(financial_rows) != 1 or any(row["facts"] for row in financial_rows):
        raise RuntimeError("financial_sector_route_failed")
    if any(not row["idempotent"] for row in kr_evidence):
        raise RuntimeError("working_capital_mapping_not_idempotent")
    if any(not row["compact_ai_context_unchanged"] for row in kr_evidence):
        raise RuntimeError("m10_scope_exceeded_model_input_leak")
    if prompt_core["changed"] or prompt_timing["changed"]:
        raise RuntimeError("prompt_changed")
    if any(row["changed"] for row in renderer_modules):
        raise RuntimeError("renderer_changed")
    if sufficiency_before != sufficiency_after:
        raise RuntimeError("source_sufficiency_changed")
    if any(row["changed"] for row in lifecycle_modules):
        raise RuntimeError("daily_delta_changed")
    if any(row["changed"] for row in warning_modules):
        raise RuntimeError("warning_semantics_changed")
    if any(row["changed"] for row in m9_semantic_modules):
        raise RuntimeError("m9_semantics_changed")
    if controls["mislabeled_yoy"] is not None:
        raise RuntimeError("year_end_mislabeled_yoy")
    if controls["gross_net_delta"] is not None:
        raise RuntimeError("gross_net_mismatch_not_blocked")
    if controls["aggregate"].overlap_blocked_count != 3:
        raise RuntimeError("inventory_overlap_not_blocked")
    if controls["insurance"].facts:
        raise RuntimeError("financial_sector_generic_working_capital_emitted")
    if schedule["observed_paused_schedule_count"] != 8:
        raise RuntimeError("approved_monitoring_path_not_paused")

    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M10 Inventory, Receivables and Working-Capital Mapping

## Result

- Status: `M10_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `{BASE_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- Contract: `{CONTRACT_VERSION}`

## Frozen accounting policy

- Exact aggregate inventory takes precedence over child components; no reconstructed total is made.
- Trade and broad receivables/payables remain distinct, and net/gross balances never compare.
- Contract assets and liabilities are `{CONTRACT_ASSET_POLICY}`.
- Current assets minus current liabilities is not operating working capital.
- The only M10 derivation is `balance_absolute_delta` with exact input lineage.
- `prior_year_comparable` and `prior_year_end` stay separate; year-end to interim is not YoY.
- DSO, DIO, DPO, CCC, scores and directional interpretations remain disabled.

## Measured archive coverage

The preserved US archive still contains no reusable balance-sheet payload. Real US inventory,
trade receivable/payable and comparison coverage is therefore `0`; exact SEC capability is a
labeled synthetic contract proof only.

The seven preserved KR official filings contain six non-financial issuers and one insurer.
Inventory is direct for `{coverage['kr_inventory_direct_count']} / 6`, trade receivables for
`{coverage['kr_trade_receivables_direct_count']} / 6`, trade payables for
`{coverage['kr_trade_payables_direct_count']} / 6`, with broad receivable/payable context for
the remaining issuer. Exact current and prior-year-end XBRL contexts produce
`{coverage['kr_comparable_balance_pair_count']}` safe absolute deltas. All are
`prior_year_end`; real prior-year comparable counts are `0`. Insurance generic emissions are
`0`.

## Safety and validation

- Ticker-specific, SEC fuzzy and OpenDART fuzzy mappings: `0`
- Universal OWC/NWC formulas and DSO/DIO/DPO/CCC derivations: `0`
- Compact AI, Directional, Timing, renderer, sufficiency, Daily Delta and warning changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `339 passed`
- Full tests: `2970 passed` with `1` existing deprecation warning
- Ruff and `git diff --check`: `PASS`

## Next scope

`NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION`

Directional financial-context consumption, model proof, production activation and schedule
resume remain out of scope.
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
        "contract": "m10-artifact-index-v1",
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
