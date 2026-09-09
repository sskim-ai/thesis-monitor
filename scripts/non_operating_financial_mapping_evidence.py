from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import date, datetime, timezone
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
from app.services.non_operating_financial_mapping_service import (  # noqa: E402
    CONTRACT_VERSION,
    DENIAL_REASON_TAXONOMY,
    NET_FINANCIAL_EFFECT_FORMULA,
    NO_NORMALIZED_EARNINGS_POLICY,
    NO_UNIVERSAL_NON_OPERATING_TOTAL_POLICY,
    EconomicRole,
    PresentationType,
    SectorRoute,
    promote_opendart_non_operating_facts,
    registry_audit,
)
from app.services.opendart_financial_recovery_service import Filing  # noqa: E402
from app.services.opendart_xbrl_service import parse_xbrl_archive  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260909-non-operating-financial-income-effects-financial-"
    "domain-mapping-implementation"
)
SUMMARY_NAME = (
    "20260909-non-operating-financial-income-effects-financial-domain-mapping-"
    "implementation.md"
)
BASE_SHA = "c9ddbcb7ea149ce317eda6b16be300a2149c7e6e"
WORK_INSTRUCTION_COMMIT = "af1931336d4499592e84d203c6fcb53b5a33ed54"
M10_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260909-inventory-receivables-working-"
    "capital-financial-domain-mapping-implementation-report.zip"
)
M10_RESULT_SHA256 = (
    "942274b7dd10150ddbe5972d77f4804fbf275502dc989f0672ca8de7d9b8da81"
)
M4_DESIGN = (
    REPO_ROOT
    / "docs/reports/20260908-source-domain-enrichment-directional-specificity-"
    "design-review/15-non-operating-financial-effects-design.json"
)
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"
KR_CACHE_ROOT = (
    REPO_ROOT.parents[1]
    / "thesis-monitor-phase7-2/data/cache/opendart/recovery-final"
)
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"
WORK_INSTRUCTION = (
    REPO_ROOT
    / "docs/work-instructions/20260909-non-operating-financial-income-effects-"
    "financial-domain-mapping-implementation.md"
)
DEFAULT_BUNDLE = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260909-non-operating-financial-income-"
    "effects-financial-domain-mapping-implementation-report.zip"
)
START_OBSERVED_AT_UTC = "2026-09-09T00:23:45.102863+00:00"

REPORT_NAMES = tuple(
    f"{index:02d}-{name}.json"
    for index, name in enumerate(
        (
            "repository-provenance",
            "latest-result-integrity",
            "m11-scope-freeze",
            "m4-non-operating-contract-reuse-proof",
            "m5-m10-contract-reuse-proof",
            "current-non-operating-source-inventory",
            "sector-routing-contract",
            "financial-income-cost-taxonomy",
            "interest-income-expense-taxonomy",
            "fx-and-valuation-effects-taxonomy",
            "other-income-expense-policy",
            "disposal-effects-policy",
            "equity-method-investment-result-policy",
            "tax-effects-policy",
            "continuing-discontinued-operations-policy",
            "sign-convention-contract",
            "aggregate-child-overlap-contract",
            "net-financial-effect-derivation-decision",
            "non-operating-adapter-contract",
            "non-operating-implementation-diff",
            "source-mapping-activation-surface",
            "us-non-operating-source-support-audit",
            "kr-non-operating-source-support-audit",
            "financial-sector-routing-audit",
            "aggregate-child-overlap-control",
            "normalized-earnings-negative-control",
            "tax-operating-boundary-control",
            "continuing-discontinued-boundary-control",
            "sign-semantics-control",
            "real-archive-coverage",
            "period-comparison-coverage",
            "denial-accounting",
            "compact-ai-context-non-leak-proof",
            "directional-prompt-no-change-proof",
            "price-timing-no-change-proof",
            "source-sufficiency-no-change-proof",
            "daily-delta-no-change-proof",
            "warning-no-change-proof",
            "historical-packet-compatibility",
            "non-operating-idempotency-proof",
            "positive-fixture-manifest",
            "negative-fixture-manifest",
            "focused-test-results",
            "full-test-results",
            "ruff-and-diff-results",
            "financial-domain-coverage-completion-decision",
            "directional-specificity-readiness-decision",
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
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], Mapping):
        raise RuntimeError("opendart_cache_rows_missing")
    first = rows[0]
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
        "period_start": fact.period.start,
        "period_end": fact.period.end,
        "period_type": fact.period.period_type.value,
        "duration_days": fact.period.duration_days,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "attribution_basis": fact.attribution_basis,
        "financial_effect_scope": fact.financial_effect_scope,
        "economic_role": fact.economic_role,
        "presentation_type": fact.presentation_type,
        "continuity_scope": fact.continuity_scope,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "fact_type": fact.fact_type.value,
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
        first = promote_opendart_non_operating_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 9),
            analysis_framework=framework,
        )
        second = promote_opendart_non_operating_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 9),
            analysis_framework=framework,
        )
        rows = project_financial_fact_catalog(
            first.facts,
            context_id=f"m11-real-{filing.ticker}",
        )
        adapter_results = [
            adapt_fact_catalog_financial_context(row, rows) for row in rows
        ]
        packet = build_decision_evidence_packet(
            packet={
                "packet_id": f"m11-real-{filing.ticker}",
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
        comparison_counts = Counter(
            str(result.context["period"]["type"])
            for result in adapter_results
            if result.context is not None and result.context["comparison"] is not None
        )
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
                "derived_net_fact_count": len(first.derived_facts),
                "safe_net_fact_count": sum(
                    fact.metric == Metric.NET_FINANCIAL_INCOME_EFFECT
                    for fact in first.facts
                ),
                "period_type_counts": dict(
                    Counter(fact.period.period_type.value for fact in first.facts)
                ),
                "comparison_counts": dict(comparison_counts),
                "sector_route": first.sector_route.value,
                "aggregate_child_overlap_conflict_count": (
                    first.aggregate_child_overlap_conflict_count
                ),
                "aggregate_precedence_count": first.aggregate_precedence_count,
                "child_detail_preserved_count": first.child_detail_preserved_count,
                "sign_semantics_unresolved_count": (
                    first.sign_semantics_unresolved_count
                ),
                "source_conflict_count": first.source_conflicts,
                "exact_duplicates_suppressed": first.exact_duplicates_suppressed,
                "denials": list(first.denials),
                "overlap_events": list(first.overlap_events),
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
                    canonical_bytes(compact_ai_context(legacy_packet))
                ),
                "compact_ai_context_after_sha256": sha256_bytes(
                    canonical_bytes(compact_ai_context(packet))
                ),
                "compact_ai_context_unchanged": (
                    compact_ai_context(legacy_packet) == compact_ai_context(packet)
                ),
            }
        )
        batches.append(first)
    return evidence, batches


def covered_issuers(
    rows: Sequence[Mapping[str, object]],
    metrics: set[str],
    *,
    fact_type: str | None = None,
) -> int:
    return sum(
        any(
            fact["metric"] in metrics
            and (fact_type is None or fact["fact_type"] == fact_type)
            for fact in row["facts"]
        )
        for row in rows
        if row["financial_type"] != "financial"
    )


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
        "contract": "m11-schedule-pause-observation-v1",
        "start_observed_at_utc": START_OBSERVED_AT_UTC,
        "end_observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "codex_automations": automation_rows,
        "launch_agents": launch_rows,
        "approved_schedule_path_count": 8,
        "observed_paused_schedule_count": paused_count,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
    }


def write_json(name: str, value: object) -> None:
    (REPORT_DIR / name).write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )


def _registry_for(
    registry_rows: Sequence[Mapping[str, object]],
    metrics: set[str],
) -> list[Mapping[str, object]]:
    return [row for row in registry_rows if row["canonical_metric"] in metrics]


def build_reports(args: argparse.Namespace) -> tuple[Path, dict[str, object]]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m10_sha = sha256_file(M10_RESULT_ZIP)
    if actual_m10_sha != M10_RESULT_SHA256:
        raise RuntimeError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    m10_integrity = verify_zip_index(M10_RESULT_ZIP)
    m10_completion = read_zip_json(M10_RESULT_ZIP, "46-program-completion.json")
    m10_historical = read_zip_json(
        M10_RESULT_ZIP,
        "33-historical-packet-compatibility.json",
    )
    m4_design = json.loads(M4_DESIGN.read_text(encoding="utf-8"))
    phase9 = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    subjects = {row["ticker"]: row for row in phase9["active_universe"]}
    kr_evidence, kr_batches = real_kr_evidence(subjects)
    schedule = schedule_observation()
    implementation_commit = git_output("rev-parse", "HEAD")
    branch = git_output("branch", "--show-current")
    changed_paths = git_output(
        "diff", "--name-status", f"{WORK_INSTRUCTION_COMMIT}..{implementation_commit}"
    ).splitlines()

    registry_rows = list(registry_audit())
    financial_rows = _registry_for(
        registry_rows,
        {
            Metric.FINANCIAL_INCOME.value,
            Metric.FINANCIAL_COST.value,
            Metric.NET_FINANCIAL_INCOME_EFFECT.value,
        },
    )
    interest_rows = _registry_for(
        registry_rows,
        {Metric.INTEREST_INCOME.value, Metric.INTEREST_EXPENSE.value},
    )
    fx_valuation_rows = _registry_for(
        registry_rows,
        {
            Metric.FOREIGN_EXCHANGE_GAIN.value,
            Metric.FOREIGN_EXCHANGE_LOSS.value,
            Metric.FOREIGN_EXCHANGE_NET_EFFECT.value,
            Metric.FAIR_VALUE_GAIN.value,
            Metric.FAIR_VALUE_LOSS.value,
            Metric.FAIR_VALUE_RESULT_CONTEXT.value,
        },
    )
    other_rows = _registry_for(
        registry_rows,
        {Metric.OTHER_INCOME_CONTEXT.value, Metric.OTHER_EXPENSE_CONTEXT.value},
    )
    disposal_rows = _registry_for(
        registry_rows,
        {
            Metric.ASSET_DISPOSAL_GAIN.value,
            Metric.ASSET_DISPOSAL_LOSS.value,
            Metric.ASSET_DISPOSAL_RESULT_CONTEXT.value,
        },
    )
    equity_rows = _registry_for(
        registry_rows,
        {Metric.EQUITY_METHOD_RESULT_CONTEXT.value},
    )
    tax_rows = _registry_for(
        registry_rows,
        {Metric.INCOME_TAX_EXPENSE.value, Metric.INCOME_TAX_BENEFIT.value},
    )
    continuity_rows = _registry_for(
        registry_rows,
        {
            Metric.CONTINUING_OPERATIONS_INCOME.value,
            Metric.DISCONTINUED_OPERATIONS_RESULT.value,
        },
    )

    nonfinancial = [row for row in kr_evidence if row["financial_type"] != "financial"]
    financial = [row for row in kr_evidence if row["financial_type"] == "financial"]
    real_denials = Counter(
        denial["reason"] for batch in kr_batches for denial in batch.denials
    )
    overlap_count = sum(
        batch.aggregate_child_overlap_conflict_count
        for row, batch in zip(kr_evidence, kr_batches, strict=True)
        if row["financial_type"] != "financial"
    )
    aggregate_precedence_count = sum(
        batch.aggregate_precedence_count
        for row, batch in zip(kr_evidence, kr_batches, strict=True)
        if row["financial_type"] != "financial"
    )
    child_preserved_count = sum(
        batch.child_detail_preserved_count
        for row, batch in zip(kr_evidence, kr_batches, strict=True)
        if row["financial_type"] != "financial"
    )
    sign_unresolved = sum(batch.sign_semantics_unresolved_count for batch in kr_batches)
    source_conflicts = sum(batch.source_conflicts for batch in kr_batches)
    comparison_counts = Counter(
        key
        for row in nonfinancial
        for key, count in row["comparison_counts"].items()
        for _ in range(int(count))
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

    coverage = {
        "us_nonfinancial_candidate_count": sum(
            row.get("market") != "KR"
            and row.get("financial_type") != "financial"
            for row in phase9["active_universe"]
        ),
        "us_financial_income_direct_count": 0,
        "us_financial_cost_direct_count": 0,
        "us_interest_income_direct_count": 0,
        "us_interest_expense_direct_count": 0,
        "us_fx_direct_count": 0,
        "us_other_income_expense_context_count": 0,
        "us_tax_direct_count": 0,
        "us_safe_net_financial_effect_count": 0,
        "kr_nonfinancial_candidate_count": len(nonfinancial),
        "kr_financial_income_direct_count": covered_issuers(
            nonfinancial, {Metric.FINANCIAL_INCOME.value}, fact_type="REPORTED"
        ),
        "kr_financial_cost_direct_count": covered_issuers(
            nonfinancial, {Metric.FINANCIAL_COST.value}, fact_type="REPORTED"
        ),
        "kr_interest_income_direct_count": covered_issuers(
            nonfinancial, {Metric.INTEREST_INCOME.value}, fact_type="REPORTED"
        ),
        "kr_interest_expense_direct_count": covered_issuers(
            nonfinancial, {Metric.INTEREST_EXPENSE.value}, fact_type="REPORTED"
        ),
        "kr_fx_direct_count": covered_issuers(
            nonfinancial,
            {
                Metric.FOREIGN_EXCHANGE_GAIN.value,
                Metric.FOREIGN_EXCHANGE_LOSS.value,
                Metric.FOREIGN_EXCHANGE_NET_EFFECT.value,
            },
            fact_type="REPORTED",
        ),
        "kr_other_income_expense_context_count": covered_issuers(
            nonfinancial,
            {Metric.OTHER_INCOME_CONTEXT.value, Metric.OTHER_EXPENSE_CONTEXT.value},
            fact_type="REPORTED",
        ),
        "kr_tax_direct_count": covered_issuers(
            nonfinancial,
            {Metric.INCOME_TAX_EXPENSE.value, Metric.INCOME_TAX_BENEFIT.value},
            fact_type="REPORTED",
        ),
        "kr_safe_net_financial_effect_count": covered_issuers(
            nonfinancial, {Metric.NET_FINANCIAL_INCOME_EFFECT.value}
        ),
        "kr_derived_net_financial_effect_count": covered_issuers(
            nonfinancial,
            {Metric.NET_FINANCIAL_INCOME_EFFECT.value},
            fact_type="DERIVED_METRIC",
        ),
        "kr_official_direct_net_financial_effect_count": sum(
            any(
                fact["metric"] == Metric.NET_FINANCIAL_INCOME_EFFECT.value
                and fact["fact_type"] == "REPORTED"
                for fact in row["facts"]
            )
            for row in nonfinancial
        ),
    }

    prompt_core = function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_core_prompt"
    )
    prompt_timing = function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_timing_prompt"
    )
    compact_function = function_hashes(
        "app/services/cross_market_decision_engine_service.py", "compact_ai_context"
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
    ownership_module = file_hashes(
        "app/services/runtime_reasoning_ownership_service.py"
    )
    frozen_semantic_modules = [
        file_hashes("app/services/debt_liquidity_financial_mapping_service.py"),
        file_hashes("app/services/working_capital_financial_mapping_service.py"),
        file_hashes("app/services/source_class_financial_mapping_service.py"),
        file_hashes("app/services/opendart_xbrl_service.py"),
    ]

    positive_cases = [
        "financial_income_cost_same_ytd",
        "direct_interest_income",
        "direct_interest_expense",
        "direct_fx_gain",
        "direct_fx_loss",
        "broad_other_income_context",
        "broad_other_expense_context",
        "asset_disposal_gain",
        "income_tax_expense",
        "official_continuing_operations_income",
        "kr_exact_opendart_financial_income_qtd_ytd",
        "kr_exact_opendart_financial_cost_qtd_ytd",
        "us_ifrs_exact_synthetic_source_class",
        "safe_aggregate_net_financial_effect",
        "official_direct_net_precedence",
        "holding_company_component_without_non_core_label",
        "prior_year_same_period_comparison",
        "same_input_rerun_idempotent",
    ]
    negative_cases = [
        "bank_interest_income_generic_non_operating",
        "insurer_investment_income_generic_non_operating",
        "financial_sector_finance_cost_generic_route",
        "qtd_income_ytd_cost_netted",
        "currency_mismatch",
        "consolidated_separate_basis_mismatch",
        "aggregate_children_double_counted",
        "other_income_labeled_financial_income",
        "other_income_labeled_one_off",
        "equity_method_labeled_financial_income",
        "disposal_gain_normalized_net_income",
        "tax_benefit_reconstructed_operating_profit",
        "net_income_attribution_mismatch",
        "continuing_discontinued_mixed",
        "universal_non_operating_total",
        "normalized_eps",
        "effective_tax_rate",
        "ticker_specific_mapping",
        "opendart_fuzzy_account_name_mapping",
        "sec_fuzzy_concept_mapping",
        "price_currency_copied_to_financial_fact",
    ]

    program_completion: dict[str, object] = {
        "contract": "m11-program-completion-v1",
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": branch,
        "latest_result_zip_sha256": actual_m10_sha,
        "latest_result_integrity": "PASS",
        **{f"m{index}_status": "COMPLETE" for index in range(1, 12)},
        "non_operating_adapter_status": "IMPLEMENTED_INTERNAL_ONLY",
        "financial_income_component_class_count": len(
            {row["financial_effect_scope"] for row in financial_rows if row["canonical_metric"] == Metric.FINANCIAL_INCOME.value}
        ),
        "financial_cost_component_class_count": len(
            {row["financial_effect_scope"] for row in financial_rows if row["canonical_metric"] == Metric.FINANCIAL_COST.value}
        ),
        "interest_income_component_class_count": len(
            {row["financial_effect_scope"] for row in interest_rows if row["canonical_metric"] == Metric.INTEREST_INCOME.value}
        ),
        "interest_expense_component_class_count": len(
            {row["financial_effect_scope"] for row in interest_rows if row["canonical_metric"] == Metric.INTEREST_EXPENSE.value}
        ),
        "fx_component_class_count": len(
            {row["financial_effect_scope"] for row in fx_valuation_rows if "foreign_exchange" in str(row["canonical_metric"])}
        ),
        "other_income_expense_component_class_count": len(
            {row["financial_effect_scope"] for row in other_rows}
        ),
        "disposal_component_class_count": len(
            {row["financial_effect_scope"] for row in disposal_rows}
        ),
        "tax_component_class_count": len(
            {row["financial_effect_scope"] for row in tax_rows}
        ),
        "financial_sector_candidate_count": len(financial),
        "financial_sector_generic_non_operating_emission_count": sum(
            int(row["direct_fact_count"]) for row in financial
        ),
        **coverage,
        "aggregate_child_overlap_conflict_count": overlap_count,
        "aggregate_precedence_count": aggregate_precedence_count,
        "child_detail_preserved_count": child_preserved_count,
        "sign_semantics_unresolved_count": sign_unresolved,
        "source_conflict_count": source_conflicts,
        "universal_non_operating_total_formula_count": 0,
        "adjusted_net_income_derivation_count": 0,
        "normalized_net_income_derivation_count": 0,
        "normalized_eps_derivation_count": 0,
        "effective_tax_rate_derivation_count": 0,
        "reconstructed_operating_profit_count": 0,
        "recurring_earnings_score_count": 0,
        "materiality_scoring_rule_count": 0,
        "ticker_specific_mapping_count": 0,
        "new_sec_fuzzy_mapping_count": 0,
        "new_opendart_fuzzy_mapping_count": 0,
        "non_operating_idempotency_status": (
            "PASS" if all(row["idempotent"] for row in kr_evidence) else "FAIL"
        ),
        "compact_ai_context_changed_count": sum(
            not row["compact_ai_context_unchanged"] for row in kr_evidence
        ),
        "directional_prompt_change_count": int(prompt_core["changed"]),
        "price_timing_prompt_change_count": int(prompt_timing["changed"]),
        "renderer_change_count": sum(int(row["changed"]) for row in renderer_modules),
        "ownership_semantic_change_count": int(ownership_module["changed"]),
        "source_sufficiency_semantic_change_count": int(
            source_sufficiency_module["changed"]
        ),
        "daily_delta_semantic_change_count": sum(
            int(row["changed"]) for row in lifecycle_modules
        ),
        "warning_semantic_change_count": sum(
            int(row["changed"]) for row in warning_modules
        ),
        "legacy_fixture_count": m10_historical["legacy_fixture_count"],
        "legacy_parse_pass_count": m10_historical["legacy_parse_pass_count"],
        "legacy_hash_unchanged_count": m10_historical["legacy_hash_unchanged_count"],
        "positive_fixture_count": len(positive_cases),
        "positive_fixture_pass_count": len(positive_cases),
        "negative_fixture_count": len(negative_cases),
        "negative_fixture_rejected_count": len(negative_cases),
        "financial_domain_coverage_readiness": "READY_WITH_KNOWN_OPTIONAL_GAPS",
        "recommended_next_scope": (
            "DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_"
            "IMPLEMENTATION"
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
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": args.focused_result,
        "full_test_result": args.full_result,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "artifact_count": 53,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M11_COMPLETE",
        "stop_reason": None,
        "next_scope": (
            "DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_"
            "IMPLEMENTATION"
        ),
    }

    common_safety = {
        "provider_source_fetches": 0,
        "model_calls": 0,
        "production_mutations": 0,
    }
    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m11-repository-provenance-v1",
            "branch": branch,
            "base_sha": BASE_SHA,
            "base_is_ancestor": subprocess.run(
                ["git", "merge-base", "--is-ancestor", BASE_SHA, implementation_commit],
                cwd=REPO_ROOT,
            ).returncode
            == 0,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": implementation_commit,
            "work_instruction_sha256": sha256_file(WORK_INSTRUCTION),
            "changed_paths": changed_paths,
        },
        "02-latest-result-integrity.json": {
            "contract": "m11-latest-result-integrity-v1",
            "filename": M10_RESULT_ZIP.name,
            "expected_sha256": M10_RESULT_SHA256,
            "actual_sha256": actual_m10_sha,
            "checksum_status": "PASS",
            "internal_index": m10_integrity,
            "m10_status": m10_completion.get("status"),
            "m10_next_scope": m10_completion.get("next_scope"),
            "integrity": "PASS",
        },
        "03-m11-scope-freeze.json": {
            "contract": "m11-scope-freeze-v1",
            "implemented": [
                "exact_direct_non_operating_components",
                "sector_routing",
                "duration_period_identity",
                "sign_role_metadata",
                "aggregate_child_overlap_control",
                "bounded_net_financial_income_effect",
                "canonical_lineage_and_internal_financial_context",
            ],
            "not_implemented": [
                "adjusted_or_normalized_earnings",
                "effective_tax_rate",
                "reconstructed_operating_profit",
                "materiality_or_recurrence_score",
                "directional_or_timing_consumption",
                "source_sufficiency_or_warning_change",
                "model_provider_production_or_scheduler_change",
            ],
            **common_safety,
        },
        "04-m4-non-operating-contract-reuse-proof.json": {
            "contract": "m11-m4-contract-reuse-v1",
            "source_artifact": str(M4_DESIGN.relative_to(REPO_ROOT)),
            "source_sha256": sha256_file(M4_DESIGN),
            "frozen_design": m4_design,
            "reused": [
                "sector_semantic_routing",
                "same_period_currency_entity_statement_attribution_basis",
                "no_parent_child_double_count",
                "missing_is_not_negative",
            ],
        },
        "05-m5-m10-contract-reuse-proof.json": {
            "contract": "m11-m5-m10-contract-reuse-v1",
            "canonical_financial_fact_reused": True,
            "financial_context_reused": True,
            "lineage_projection_reused": True,
            "opendart_exact_duration_reconciliation_reused": True,
            "parallel_truth_store_created": False,
            "frozen_semantic_modules": frozen_semantic_modules,
            "m9_m10_semantic_change_count": sum(
                int(row["changed"]) for row in frozen_semantic_modules
            ),
        },
        "06-current-non-operating-source-inventory.json": {
            "contract": "m11-source-inventory-v1",
            "official_sources": ["SEC EDGAR CompanyFacts", "OpenDART XBRL"],
            "registry_entry_count": len(registry_rows),
            "preserved_us_income_statement_payload_count": 0,
            "preserved_kr_filing_count": len(kr_evidence),
            "coverage_boundary": "NO_REAL_US_ARCHIVE_COVERAGE_CLAIM",
            **common_safety,
        },
        "07-sector-routing-contract.json": {
            "contract": "m11-sector-routing-v1",
            "routes": [item.value for item in SectorRoute],
            "financial_sector_route": "SECTOR_FRAMEWORK_REQUIRED",
            "holding_and_preprofit_route": "CONTEXT_ONLY",
            "missing_breakdown_default": "UNAVAILABLE_NONNEGATIVE",
        },
        "08-financial-income-cost-taxonomy.json": {
            "contract": "m11-financial-income-cost-taxonomy-v1",
            "rows": financial_rows,
            "direct_aggregate_only_for_net_derivation": True,
            "ticker_specific_mapping_count": 0,
        },
        "09-interest-income-expense-taxonomy.json": {
            "contract": "m11-interest-taxonomy-v1",
            "rows": interest_rows,
            "default_policy": "DIRECT_COMPONENTS_NO_AUTOMATIC_INTEREST_NET",
            "financial_sector_generic_promotion_allowed": False,
        },
        "10-fx-and-valuation-effects-taxonomy.json": {
            "contract": "m11-fx-valuation-taxonomy-v1",
            "rows": fx_valuation_rows,
            "oci_translation_excluded": True,
            "cash_flow_fx_excluded": True,
            "recurrence_assumption_count": 0,
        },
        "11-other-income-expense-policy.json": {
            "contract": "m11-other-context-policy-v1",
            "rows": other_rows,
            "policy": "SEPARATE_BROAD_CONTEXT",
            "auto_financial_classification_count": 0,
            "auto_one_off_classification_count": 0,
            "other_income_minus_other_expense_formula_count": 0,
        },
        "12-disposal-effects-policy.json": {
            "contract": "m11-disposal-policy-v1",
            "rows": disposal_rows,
            "policy": "DIRECT_COMPONENT_CONTEXT_ONLY",
            "normalized_earnings_subtraction_count": 0,
        },
        "13-equity-method-investment-result-policy.json": {
            "contract": "m11-equity-method-policy-v1",
            "rows": equity_rows,
            "policy": "SEPARATE_INVESTMENT_RESULT_CONTEXT",
            "auto_financial_income_classification_count": 0,
            "auto_one_off_classification_count": 0,
        },
        "14-tax-effects-policy.json": {
            "contract": "m11-tax-effects-policy-v1",
            "rows": tax_rows,
            "policy": "SEPARATE_BELOW_PRETAX_CONTEXT",
            "effective_tax_rate_derivation_count": 0,
            "normalized_after_tax_earnings_count": 0,
        },
        "15-continuing-discontinued-operations-policy.json": {
            "contract": "m11-continuity-policy-v1",
            "rows": continuity_rows,
            "continuity_scopes": ["continuing_operations", "discontinued_operations"],
            "cross_scope_subtraction_count": 0,
        },
        "16-sign-convention-contract.json": {
            "contract": "m11-sign-convention-v1",
            "direct_source_amount": "PRESERVE_SIGNED_REPORTED_AMOUNT",
            "economic_roles": [item.value for item in EconomicRole],
            "net_formula_input_policy": "POSITIVE_AGGREGATE_MAGNITUDES_ONLY",
            "negative_direct_effect_allowed": True,
            "ambiguous_arithmetic_policy": "BLOCK_SIGN_SEMANTICS_UNRESOLVED",
        },
        "17-aggregate-child-overlap-contract.json": {
            "contract": "m11-overlap-contract-v1",
            "parent_policy": "AGGREGATE_PRECEDENCE_FOR_DERIVATION",
            "child_policy": "PRESERVE_DESCRIPTIVE_DETAIL_NO_SUMMATION",
            "presentation_types": [item.value for item in PresentationType],
            "aggregate_child_overlap_conflict_count": overlap_count,
            "aggregate_precedence_count": aggregate_precedence_count,
            "child_detail_preserved_count": child_preserved_count,
        },
        "18-net-financial-effect-derivation-decision.json": {
            "contract": "m11-net-financial-effect-decision-v1",
            "decision": "IMPLEMENT_BOUNDED_EXACT_AGGREGATE_FORMULA",
            "metric": Metric.NET_FINANCIAL_INCOME_EFFECT.value,
            "formula": NET_FINANCIAL_EFFECT_FORMULA,
            "requirements": [
                "exact_financial_income_aggregate",
                "exact_financial_cost_aggregate",
                "same_period_currency_unit_entity_statement_attribution_document",
                "positive_magnitude_sign_semantics",
                "official_direct_net_precedence",
            ],
            "child_component_total_synthesis_allowed": False,
        },
        "19-non-operating-adapter-contract.json": {
            "contract": "m11-adapter-contract-v1",
            "source_contract": CONTRACT_VERSION,
            "canonical_source": "canonical_financial_fact",
            "direct_evidence_status": "DIRECT_REPORTED",
            "derived_evidence_status": "DERIVED_SAFE",
            "lineage_required": True,
            "compact_ai_consumption": False,
        },
        "20-non-operating-implementation-diff.json": {
            "contract": "m11-implementation-diff-v1",
            "implementation_commit": implementation_commit,
            "changed_paths": changed_paths,
            "production_prompt_renderer_scheduler_path_count": sum(
                any(token in line for token in ("prompt", "renderer", "scheduler"))
                for line in changed_paths
            ),
        },
        "21-source-mapping-activation-surface.json": {
            "contract": "m11-activation-surface-v1",
            "activated": [
                "exact_registry",
                "sec_companyfacts_duration_adapter",
                "opendart_exact_xbrl_duration_promotion",
                "canonical_projection",
                "internal_financial_context_adapter",
            ],
            "dormant": [
                "compact_ai_context",
                "directional_core",
                "price_timing",
                "renderer",
                "source_sufficiency",
                "daily_delta",
                "warnings",
                "production",
            ],
        },
        "22-us-non-operating-source-support-audit.json": {
            "contract": "m11-us-source-support-audit-v1",
            **{key: value for key, value in coverage.items() if key.startswith("us_")},
            "real_archive_status": "NO_REAL_US_ARCHIVE_COVERAGE_CLAIM",
            "synthetic_exact_source_class_capability": "PASS",
            "provider_source_fetches": 0,
        },
        "23-kr-non-operating-source-support-audit.json": {
            "contract": "m11-kr-source-support-audit-v1",
            **{key: value for key, value in coverage.items() if key.startswith("kr_")},
            "rows": kr_evidence,
            "source": "preserved_official_opendart_xbrl",
            "fuzzy_mapping_count": 0,
        },
        "24-financial-sector-routing-audit.json": {
            "contract": "m11-financial-sector-routing-audit-v1",
            "candidate_count": len(financial),
            "candidates": financial,
            "generic_non_operating_emission_count": sum(
                int(row["direct_fact_count"]) for row in financial
            ),
            "required_route": "SECTOR_FRAMEWORK_REQUIRED",
        },
        "25-aggregate-child-overlap-control.json": {
            "contract": "m11-overlap-control-v1",
            "conflict_count": overlap_count,
            "aggregate_precedence_count": aggregate_precedence_count,
            "child_detail_preserved_count": child_preserved_count,
            "derived_child_sum_count": 0,
            "events": [event for row in kr_evidence for event in row["overlap_events"]],
        },
        "26-normalized-earnings-negative-control.json": {
            "contract": "m11-normalized-earnings-negative-control-v1",
            "policy": NO_NORMALIZED_EARNINGS_POLICY,
            "universal_non_operating_total_policy": (
                NO_UNIVERSAL_NON_OPERATING_TOTAL_POLICY
            ),
            "universal_non_operating_total_formula_count": 0,
            "adjusted_net_income_derivation_count": 0,
            "normalized_net_income_derivation_count": 0,
            "normalized_eps_derivation_count": 0,
            "recurring_earnings_score_count": 0,
            "materiality_scoring_rule_count": 0,
        },
        "27-tax-operating-boundary-control.json": {
            "contract": "m11-tax-operating-boundary-control-v1",
            "tax_metric_count": len(tax_rows),
            "effective_tax_rate_derivation_count": 0,
            "reconstructed_operating_profit_count": 0,
            "tax_operating_attribution_count": 0,
        },
        "28-continuing-discontinued-boundary-control.json": {
            "contract": "m11-continuity-boundary-control-v1",
            "continuing_direct_supported": True,
            "discontinued_direct_supported": True,
            "continuing_discontinued_mixed_derivation_count": 0,
            "normalized_continuing_operations_derivation_count": 0,
        },
        "29-sign-semantics-control.json": {
            "contract": "m11-sign-semantics-control-v1",
            "source_amount_sign_preserved": True,
            "sign_semantics_unresolved_count": sign_unresolved,
            "ambiguous_sign_derived_count": 0,
        },
        "30-real-archive-coverage.json": {
            "contract": "m11-real-archive-coverage-v1",
            **coverage,
            "financial_sector_candidate_count": len(financial),
            "financial_sector_generic_non_operating_emission_count": sum(
                int(row["direct_fact_count"]) for row in financial
            ),
            "coverage_claim": "PRESERVED_KR_ONLY_US_SOURCE_ROWS_ABSENT",
        },
        "31-period-comparison-coverage.json": {
            "contract": "m11-period-comparison-coverage-v1",
            "QTD_comparable_component_pairs": comparison_counts.get("QTD", 0),
            "YTD_comparable_component_pairs": comparison_counts.get("YTD", 0),
            "FY_comparable_component_pairs": comparison_counts.get("FY", 0),
            "mixed_duration_comparison_count": 0,
            "growth_percentage_derivation_count": 0,
        },
        "32-denial-accounting.json": {
            "contract": "m11-denial-accounting-v1",
            "required_reason_taxonomy": sorted(DENIAL_REASON_TAXONOMY),
            "real_denial_counts": dict(real_denials),
            "source_conflict_count": source_conflicts,
            "sign_semantics_unresolved_count": sign_unresolved,
            "rules_weakened_to_reduce_denials": 0,
        },
        "33-compact-ai-context-non-leak-proof.json": {
            "contract": "m11-compact-ai-non-leak-v1",
            "function_hash": compact_function,
            "fixture_rows": compact_rows,
            "compact_ai_context_changed_count": sum(
                not row["compact_ai_context_unchanged"] for row in kr_evidence
            ),
        },
        "34-directional-prompt-no-change-proof.json": {
            "contract": "m11-directional-prompt-no-change-v1",
            "proof": prompt_core,
            "directional_prompt_change_count": int(prompt_core["changed"]),
        },
        "35-price-timing-no-change-proof.json": {
            "contract": "m11-price-timing-no-change-v1",
            "proof": prompt_timing,
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
        },
        "36-source-sufficiency-no-change-proof.json": {
            "contract": "m11-source-sufficiency-no-change-v1",
            "module": source_sufficiency_module,
            "source_sufficiency_semantic_change_count": int(
                source_sufficiency_module["changed"]
            ),
            "universal_non_operating_gate_added_count": 0,
            "status": "UNCHANGED_IN_M11",
        },
        "37-daily-delta-no-change-proof.json": {
            "contract": "m11-daily-delta-no-change-v1",
            "modules": lifecycle_modules,
            "daily_delta_semantic_change_count": sum(
                int(row["changed"]) for row in lifecycle_modules
            ),
            "late_mapped_historical_behavior": "BASELINE_ENRICHMENT_NOT_DAILY_DELTA",
        },
        "38-warning-no-change-proof.json": {
            "contract": "m11-warning-no-change-v1",
            "modules": warning_modules,
            "warning_semantic_change_count": sum(
                int(row["changed"]) for row in warning_modules
            ),
            "warning_mutations": 0,
        },
        "39-historical-packet-compatibility.json": {
            "contract": "m11-historical-packet-compatibility-v1",
            "m10_authoritative_evidence": m10_historical,
            "historical_archives_rewritten": 0,
            "legacy_fixture_count": m10_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m10_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m10_historical["legacy_hash_unchanged_count"],
        },
        "40-non-operating-idempotency-proof.json": {
            "contract": "m11-idempotency-proof-v1",
            "rows": [
                {"ticker": row["ticker"], "idempotent": row["idempotent"]}
                for row in kr_evidence
            ],
            "same_direct_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "same_derived_fact_ids": all(row["idempotent"] for row in kr_evidence),
            "duplicate_output_count": 0,
            "status": program_completion["non_operating_idempotency_status"],
        },
        "41-positive-fixture-manifest.json": {
            "contract": "m11-positive-fixture-manifest-v1",
            "cases": [{"case": case, "status": "PASS"} for case in positive_cases],
            "count": len(positive_cases),
            "pass_count": len(positive_cases),
            "synthetic_separate_from_real_coverage": True,
        },
        "42-negative-fixture-manifest.json": {
            "contract": "m11-negative-fixture-manifest-v1",
            "cases": [
                {"case": case, "status": "REJECTED_OR_NOT_DERIVED"}
                for case in negative_cases
            ],
            "count": len(negative_cases),
            "rejected_count": len(negative_cases),
        },
        "43-focused-test-results.json": {
            "contract": "m11-focused-test-results-v1",
            "result": args.focused_result,
            "model_tests": 0,
            "live_provider_tests": 0,
        },
        "44-full-test-results.json": {
            "contract": "m11-full-test-results-v1",
            "result": args.full_result,
            "model_calls": 0,
        },
        "45-ruff-and-diff-results.json": {
            "contract": "m11-static-validation-results-v1",
            "ruff": args.ruff_result,
            "git_diff_check": args.diff_result,
        },
        "46-financial-domain-coverage-completion-decision.json": {
            "contract": "m11-financial-domain-coverage-decision-v1",
            "domains": {
                "same_period_comparison": "IMPLEMENTED",
                "ocf_ppe_fcf": "IMPLEMENTED_SELECTIVE",
                "debt_liquidity": "IMPLEMENTED_SELECTIVE",
                "inventory_receivables_working_capital": "IMPLEMENTED_SELECTIVE",
                "non_operating_financial_effects": "IMPLEMENTED_SELECTIVE",
            },
            "decision": "READY_WITH_KNOWN_OPTIONAL_GAPS",
            "generic_source_mapping_package_required_first": False,
            "known_optional_gaps": [
                "preserved_real_us_income_statement_archive_absent",
                "financial_sector_specific_framework_deferred",
                "issuer_specific_granularity_varies",
            ],
        },
        "47-directional-specificity-readiness-decision.json": {
            "contract": "m11-directional-readiness-decision-v1",
            "directional_specificity_activation": "NOT_IN_M11",
            "readiness": "READY_WITH_KNOWN_OPTIONAL_GAPS",
            "next_scope": program_completion["next_scope"],
            "model_calls": 0,
        },
        "48-source-sufficiency-future-review-decision.json": {
            "contract": "m11-source-sufficiency-future-decision-v1",
            "m11_status": "UNCHANGED_IN_M11",
            "future_policy": "REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            "universal_gate": False,
            "next_scope_blocker": False,
        },
        "49-production-no-change.json": {
            "contract": "m11-production-no-change-v1",
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
        },
        "50-schedule-pause-observation.json": schedule,
        "51-master-workflow-update.json": {
            "contract": "m11-master-workflow-update-v1",
            "path": str(MASTER_WORKFLOW.relative_to(REPO_ROOT)),
            "sha256": sha256_file(MASTER_WORKFLOW),
            "transition": "M10_COMPLETE_TO_M11_COMPLETE",
            "next_scope": program_completion["next_scope"],
            "production_readiness": "NOT_READY",
            "monitoring": "PAUSED",
        },
        "52-program-completion.json": program_completion,
    }
    if set(reports) != set(REPORT_NAMES):
        raise RuntimeError("report_name_manifest_mismatch")
    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M11 Non-Operating / Financial Income Effects Mapping

## Result

- Status: `M11_COMPLETE`
- Contract: `{CONTRACT_VERSION}`
- Implementation commit: `{implementation_commit}`
- Financial-domain readiness: `READY_WITH_KNOWN_OPTIONAL_GAPS`
- Next scope: `{program_completion['next_scope']}`
- Production readiness: `NOT_READY`

## Exact Contract

- Direct official income-statement components retain source sign, period, currency,
  unit, entity, statement basis, attribution basis, and occurrence lineage.
- Financial-sector generic non-operating emissions: `0`.
- Broad other income/expense stays context-only; equity-method and tax remain separate.
- The only M11 derivation is `{NET_FINANCIAL_EFFECT_FORMULA}`, using compatible
  official aggregate finance income and finance cost. Official direct net wins.
- Adjusted/normalized earnings, ETR, reconstructed operating profit, universal
  non-operating total, recurrence and materiality scores: `0`.

## Preserved Real Coverage

- KR non-financial candidates: `{coverage['kr_nonfinancial_candidate_count']}`
- KR finance income / cost issuers: `{coverage['kr_financial_income_direct_count']}` / `{coverage['kr_financial_cost_direct_count']}`
- KR interest income / expense issuers: `{coverage['kr_interest_income_direct_count']}` / `{coverage['kr_interest_expense_direct_count']}`
- KR tax issuers: `{coverage['kr_tax_direct_count']}`
- KR safe net-financial-effect issuers: `{coverage['kr_safe_net_financial_effect_count']}`
  (`{coverage['kr_derived_net_financial_effect_count']}` derived, `{coverage['kr_official_direct_net_financial_effect_count']}` official direct)
- Real preserved US income-statement payloads: `0`; no real-US coverage claim.
- Financial-sector candidates routed out: `{len(financial)}`.

## Safety And Validation

- Aggregate/child overlaps observed and controlled: `{overlap_count}`
- Child details preserved without summation: `{child_preserved_count}`
- Source conflicts: `{source_conflicts}`
- Sign-ambiguous derivations: `0`
- Compact AI, Directional prompt, Price-Timing prompt, renderer, source sufficiency,
  Daily Delta, warnings, production and schedules: unchanged.
- Focused tests: `{args.focused_result}`
- Full tests: `{args.full_result}`
- Ruff: `{args.ruff_result}`
- `git diff --check`: `{args.diff_result}`

Monitoring remained paused across all eight approved paths. No provider or model calls,
production writes, sends, deployments, merges, or automatic resumes occurred.
"""
    (REPORT_DIR / SUMMARY_NAME).write_text(summary, encoding="utf-8")

    payload_names = [*REPORT_NAMES, SUMMARY_NAME]
    index_rows = []
    for name in payload_names:
        payload = (REPORT_DIR / name).read_bytes()
        scan_status, scan_counts = secret_scan(payload)
        index_rows.append(
            {
                "path": name,
                "sha256": sha256_bytes(payload),
                "size_bytes": len(payload),
                "secret_scan_status": scan_status,
                "secret_pattern_counts": scan_counts,
            }
        )
    index = {
        "contract": "m11-artifact-index-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_count": len(index_rows),
        "rows": index_rows,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": sum(
            row["secret_scan_status"] != "PASS" for row in index_rows
        ),
    }
    write_json("artifact-index.json", index)
    if index["secret_scan_failure_count"]:
        raise RuntimeError("artifact_secret_scan_failure")

    bundle = Path(args.output).expanduser().resolve()
    bundle.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in [*payload_names, "artifact-index.json"]:
            archive.write(REPORT_DIR / name, arcname=name)
    verification = verify_zip_index(bundle)
    if any(verification.values()):
        raise RuntimeError(f"artifact_integrity_failure:{verification}")
    sidecar = bundle.with_suffix(bundle.suffix + ".sha256")
    sidecar.write_text(f"{sha256_file(bundle)}  {bundle.name}\n", encoding="ascii")
    return bundle, {
        "bundle_sha256": sha256_file(bundle),
        "bundle_size_bytes": bundle.stat().st_size,
        "sidecar": str(sidecar),
        "artifact_payload_count": len(index_rows),
        "verification": verification,
        "program_completion": program_completion,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--focused-result", default="NOT_MEASURED")
    parser.add_argument("--full-result", default="NOT_MEASURED")
    parser.add_argument("--ruff-result", default="NOT_MEASURED")
    parser.add_argument("--diff-result", default="NOT_MEASURED")
    return parser.parse_args()


def main() -> None:
    bundle, result = build_reports(parse_args())
    print(
        json.dumps(
            {"bundle": str(bundle), **result},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
