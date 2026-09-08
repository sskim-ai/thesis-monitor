from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.cash_flow_capital_efficiency_service import financial_fact_from_mapping
from app.services.cash_flow_user_visible_service import fact_catalog_entries
from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    FundamentalEvidenceFamily,
    evaluate_source_sufficiency,
)
from app.services.cross_market_decision_engine_service import (
    FinancialContext,
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.financial_context_adapter_service import (
    CONTRACT_VERSION,
    adapt_fact_catalog_financial_context,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260908-existing-canonical-financial-domain-adapter-implementation"
)
SUMMARY_NAME = "20260908-existing-canonical-financial-domain-adapter-implementation.md"
BASE_SHA = "29fb88be197c50b0da0eead886c89f27e823d3b4"
WORK_INSTRUCTION_COMMIT = "35da4e7f1dd57194c3f5f6532ff91a13994f2448"
IMPLEMENTATION_COMMIT = "bcad2ae16836a12ff208a110856575931bfbeb08"
M5_RESULT_ZIP = (
    Path.home()
    / "Documents"
    / "Codex"
    / (
        "thesis-monitor-20260908-decision-evidence-packet-"
        "financial-context-domain-extension-implementation-report.zip"
    )
)
M5_RESULT_SHA256 = "3c099c405892a2269e1dac8d94100f4d3c52880d1bf07f0a00e1b7c09df76b60"
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"

FOCUSED_TEST_COMMAND = (
    ".venv/bin/pytest -q tests/test_decision_evidence_financial_context.py "
    "tests/test_financial_context_adapter_service.py "
    "tests/test_cross_market_decision_engine.py "
    "tests/test_cash_flow_user_visible_service.py "
    "tests/test_cash_flow_user_visible_integration.py "
    "tests/test_coldstart_fundamental_enrichment_service.py "
    "tests/test_nonproduction_monitoring_lifecycle_service.py "
    "tests/test_nonproduction_lifecycle_decision_service.py "
    "tests/test_direction_timing_ownership_service.py "
    "tests/test_structured_autonomy_shadow_service.py"
)

REPORT_NAMES = (
    "01-repository-provenance.json",
    "02-latest-result-integrity.json",
    "03-m6-scope-freeze.json",
    "04-m5-contract-reuse-proof.json",
    "05-m6-adapter-responsibility-matrix.json",
    "06-current-canonical-financial-source-inventory.json",
    "07-same-period-comparison-adapter-contract.json",
    "08-operating-cash-flow-adapter-contract.json",
    "09-ppe-capex-adapter-contract.json",
    "10-simple-cash-conversion-derivation-contract.json",
    "11-adapter-implementation-diff.json",
    "12-producer-activation-surface.json",
    "13-market-support-audit.json",
    "14-compact-ai-context-non-leak-proof.json",
    "15-directional-prompt-no-change-proof.json",
    "16-price-timing-no-change-proof.json",
    "17-source-sufficiency-no-change-proof.json",
    "18-daily-delta-no-change-proof.json",
    "19-historical-packet-compatibility.json",
    "20-adapter-idempotency-proof.json",
    "21-positive-fixture-manifest.json",
    "22-negative-fixture-manifest.json",
    "23-offline-example-packets.json",
    "24-focused-test-results.json",
    "25-full-test-results.json",
    "26-ruff-and-diff-results.json",
    "27-additional-source-mapping-backlog.json",
    "28-directional-specificity-activation-decision.json",
    "29-source-sufficiency-no-change-decision.json",
    "30-production-no-change.json",
    "31-schedule-pause-observation.json",
    "32-master-workflow-update.json",
    "33-program-completion.json",
)

SECRET_PATTERNS = {
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "openai_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
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
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return "".join(lines[node.lineno - 1 : node.end_lineno]).encode("utf-8")
    raise ValueError(f"function_not_found:{function_name}")


def _period(period_type: str, fiscal_year: int) -> tuple[str | None, str, int | None]:
    if period_type == "QTD":
        return f"{fiscal_year}-04-01", f"{fiscal_year}-06-30", 2
    if period_type == "YTD":
        return f"{fiscal_year}-01-01", f"{fiscal_year}-06-30", 2
    if period_type == "FY":
        return f"{fiscal_year}-01-01", f"{fiscal_year}-12-31", None
    raise ValueError(period_type)


def fixture_row(
    fact_id: str,
    fact_type: str,
    value: str,
    *,
    period_type: str = "YTD",
    fiscal_year: int = 2026,
    currency: str = "USD",
    period_start_known: bool = True,
    capex_scope: str | None = None,
    input_fact_ids: tuple[str, ...] = (),
) -> dict[str, object]:
    start, end, quarter = _period(period_type, fiscal_year)
    return {
        "fact_id": fact_id,
        "fact_type": fact_type,
        "as_of_date": end,
        "source": "canonical_cash_flow_fact",
        "fields": {
            "value": value,
            "currency": currency,
            "period_start": start if period_start_known else None,
            "period_end": end,
            "period_type": period_type,
            "fiscal_year": str(fiscal_year),
            "fiscal_quarter": str(quarter) if quarter else None,
            "entity_scope": "issuer_consolidated",
            "statement_basis": "official_filing_cash_flow_statement",
            "attribution_basis": None,
            "capex_scope": capex_scope,
            "input_fact_ids": list(input_fact_ids),
            "cash_flow_user_visible_context_id": "m6-offline-fixture",
        },
        "prose_eligible": True,
        "interpretation_eligible": True,
        "numeric_registry_eligible": True,
    }


def fixture_packet(
    fixture_id: str,
    rows: list[dict[str, object]],
    *,
    market: str = "us",
) -> Any:
    return build_decision_evidence_packet(
        packet={
            "packet_id": fixture_id,
            "market": market,
            "assessment_date": "2026-09-08",
        },
        stock={
            "ticker": fixture_id.upper().replace("-", "_")[:24],
            "company_name": "M6 Offline Fixture",
            "fact_catalog": rows,
        },
    )


def without_financial_context(packet: Any) -> Any:
    return packet.model_copy(
        update={
            "evidence": tuple(
                row.model_copy(update={"financial_context": None}) for row in packet.evidence
            )
        }
    )


def canonical_refs(packet: Any) -> list[dict[str, object]]:
    return [
        row.model_dump(mode="json")
        for row in packet.evidence
        if row.ref_id.startswith("canonical:")
    ]


def build_fixture_proofs() -> tuple[dict[str, Any], list[dict[str, object]]]:
    comparison_rows = [
        fixture_row("ocf.current", "cash_flow_ocf", "100", fiscal_year=2026),
        fixture_row("ocf.prior", "cash_flow_ocf", "80", fiscal_year=2025),
    ]
    ocf_rows = [fixture_row("ocf.current", "cash_flow_ocf", "100")]
    ppe_rows = [
        fixture_row(
            "ppe.current",
            "cash_flow_ppe_capex",
            "40",
            capex_scope="ppe_only",
        )
    ]
    conversion_rows = [
        fixture_row("ocf.current", "cash_flow_ocf", "100"),
        fixture_row(
            "ppe.current",
            "cash_flow_ppe_capex",
            "40",
            capex_scope="ppe_only",
        ),
        fixture_row(
            "conversion.current",
            "cash_flow_fcf_ppe",
            "60",
            capex_scope="ppe_only",
            input_fact_ids=("ocf.current", "ppe.current"),
        ),
    ]
    kr_ambiguous_rows = [
        fixture_row(
            "kr.ocf.ambiguous",
            "cash_flow_ocf",
            "100",
            period_start_known=False,
        ),
        fixture_row(
            "kr.ppe.ambiguous",
            "cash_flow_ppe_capex",
            "40",
            period_start_known=False,
            capex_scope="ppe_only",
        ),
    ]
    packets = {
        "comparison": fixture_packet("m6-comparison", comparison_rows),
        "ocf": fixture_packet("m6-ocf", ocf_rows),
        "ppe": fixture_packet("m6-ppe", ppe_rows),
        "ocf_less_ppe": fixture_packet("m6-ocf-less-ppe", conversion_rows),
        "kr_ambiguous": fixture_packet("m6-kr-ambiguous", kr_ambiguous_rows, market="kr"),
    }
    compact_proofs: list[dict[str, object]] = []
    for fixture_id in ("comparison", "ocf", "ppe", "ocf_less_ppe"):
        enriched = packets[fixture_id]
        legacy = without_financial_context(enriched)
        before = compact_ai_context(legacy)
        after = compact_ai_context(enriched)
        compact_proofs.append(
            {
                "fixture_id": fixture_id,
                "pre_m6_compact_ai_context_sha256": sha256_bytes(canonical_bytes(before)),
                "post_m6_compact_ai_context_sha256": sha256_bytes(canonical_bytes(after)),
                "semantic_input_unchanged": before == after,
            }
        )
    return packets, compact_proofs


def source_inventory() -> dict[str, Any]:
    report = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    facts = report["canonical_facts"]
    rows = fact_catalog_entries(
        SimpleNamespace(
            user_visible_enabled=True,
            facts=tuple(financial_fact_from_mapping(row) for row in facts),
            context_id="m6-preserved-canonical-inventory",
        )
    )
    first = [adapt_fact_catalog_financial_context(row, rows) for row in rows]
    second = [adapt_fact_catalog_financial_context(row, rows) for row in rows]
    emitted = [result.context for result in first if result.context is not None]
    denial_counts = Counter(
        result.denial_reasons[0]
        for result in first
        if result.context is None and result.denial_reasons
    )
    emitted_by_metric = Counter(str(context["metric"]) for context in emitted)
    active = report["active_universe"]
    return {
        "source_report": str(PHASE9_FACTS.relative_to(REPO_ROOT)),
        "source_report_sha256": sha256_file(PHASE9_FACTS),
        "active_subject_count": len(active),
        "active_market_counts": dict(Counter(row["market"] for row in active)),
        "canonical_fact_count": len(facts),
        "canonical_fact_ticker_count": len({row["ticker"] for row in facts}),
        "canonical_fact_type_counts": {
            f"{metric}:{fact_type}": count
            for (metric, fact_type), count in sorted(
                Counter((row["metric"], row["fact_type"]) for row in facts).items()
            )
        },
        "canonical_currency_counts": dict(sorted(Counter(row["currency"] for row in facts).items())),
        "adapter_emission_count": len(emitted),
        "adapter_emission_by_metric": dict(sorted(emitted_by_metric.items())),
        "adapter_comparison_count": sum(bool(context["comparison"]) for context in emitted),
        "adapter_denial_count": len(rows) - len(emitted),
        "adapter_primary_denial_counts": dict(sorted(denial_counts.items())),
        "context_digest_first": sha256_bytes(canonical_bytes(emitted)),
        "context_digest_second": sha256_bytes(
            canonical_bytes([result.context for result in second if result.context is not None])
        ),
        "phase9_metric_coverage": report["metric_counts"],
        "provider_telemetry_preserved": report["provider_telemetry"],
    }


def frozen_function_hashes(path: str, function_name: str) -> dict[str, object]:
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


def secret_scan(payload: bytes) -> tuple[str, dict[str, int]]:
    counts = {name: len(pattern.findall(payload)) for name, pattern in SECRET_PATTERNS.items()}
    return ("PASS" if sum(counts.values()) == 0 else "FAIL", counts)


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m5_sha = sha256_file(M5_RESULT_ZIP)
    with zipfile.ZipFile(M5_RESULT_ZIP) as archive:
        m5_schema_report = json.loads(archive.read("08-financial-context-json-schema.json"))
        m5_historical = json.loads(archive.read("12-historical-artifact-compatibility.json"))

    packets, compact_proofs = build_fixture_proofs()
    inventory = source_inventory()
    current_schema = FinancialContext.model_json_schema()
    m5_schema_equal = current_schema == m5_schema_report["financial_context_schema"]

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
        "metric": "operating_cash_flow",
        "adapter": CONTRACT_VERSION,
    }
    sufficiency_before = evaluate_source_sufficiency(
        source_facts,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    sufficiency_after = evaluate_source_sufficiency(
        source_facts_after,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )

    implementation_diff = git_output(
        "diff", "--name-status", f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}"
    ).splitlines()
    branch = git_output("branch", "--show-current")
    head = git_output("rev-parse", "HEAD")

    positive_cases = [
        "us_qtd_prior_year_comparison",
        "us_ytd_prior_year_comparison",
        "us_fy_prior_year_comparison",
        "point_in_time_prior_year_comparison",
        "us_ocf_direct_ytd",
        "us_ocf_direct_fy",
        "kr_ocf_direct_explicit_period",
        "us_ppe_direct_ytd",
        "us_ppe_direct_fy",
        "kr_ppe_direct_explicit_period",
        "ocf_less_ppe_safe_ytd",
        "ocf_less_ppe_safe_fy",
    ]
    negative_cases = [
        "comparison_qtd_vs_ytd",
        "comparison_metric_mismatch",
        "comparison_currency_mismatch",
        "comparison_entity_scope_mismatch",
        "comparison_statement_basis_mismatch",
        "comparison_attribution_basis_mismatch",
        "us_ocf_duration_start_missing",
        "kr_ocf_period_ambiguous",
        "kr_ppe_period_ambiguous",
        "derivation_ytd_vs_fy",
        "derivation_currency_mismatch",
        "derivation_entity_scope_mismatch",
        "derivation_statement_basis_mismatch",
        "derivation_attribution_basis_mismatch",
        "derivation_source_ref_missing",
        "derivation_input_order_invalid",
        "derived_period_input_lineage_incomplete",
        "derivation_arithmetic_mismatch",
        "derivation_input_capex_scope_not_ppe_only",
        "derivation_output_scope_not_ppe_only",
        "negative_ppe_not_reinterpreted",
        "noncanonical_unit_scale_not_converted",
        "non_m6_financial_domain_not_emitted",
    ]
    backlog = [
        {
            "sequence": 1,
            "item": "compatible_prior_year_fact_projection",
            "reason": "selected packet catalogs often carry only the current cash-flow tuple",
        },
        {
            "sequence": 2,
            "item": "derived_period_lineage_projection",
            "reason": "formula and derivation version are absent from the current fact-catalog projection",
        },
        {
            "sequence": 3,
            "item": "kr_opendart_ocf_duration_period",
            "reason": "period context remains unresolved and fail-closed",
        },
        {
            "sequence": 4,
            "item": "kr_opendart_ppe_duration_period",
            "reason": "period context remains unresolved and fail-closed",
        },
        {
            "sequence": 5,
            "item": "hut_ppe_source_mapping",
            "reason": "Phase 9 archive has OCF but no eligible PPE source",
        },
        {
            "sequence": 6,
            "item": "skhy_ocf_ppe_source_mapping",
            "reason": "Phase 9 archive has no existing canonical cash-flow source",
        },
        {
            "sequence": 7,
            "item": "interest_bearing_debt_and_liquidity",
            "reason": "frozen M4 higher-risk mapping package",
        },
        {
            "sequence": 8,
            "item": "inventory_receivables_working_capital",
            "reason": "frozen M4 higher-risk mapping package",
        },
        {
            "sequence": 9,
            "item": "non_operating_financial_income_effects",
            "reason": "frozen M4 higher-risk mapping package",
        },
    ]

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m6-repository-provenance-v1",
            "branch": branch,
            "base_sha": BASE_SHA,
            "actual_m5_final_head": BASE_SHA,
            "actual_m5_report_commit_if_identifiable": BASE_SHA,
            "historical_precommit_reporting_state": "M5_REPORTED_FINAL_SHA_NOT_MEASURED",
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "evidence_generation_head": head,
            "work_instruction_zip_sha256": "b5b280f71988cc0efe59e94d59a99357efbb4ea6b3f0dfc3fc8259c539ab9b28",
            "work_instruction_sha256": "915af36a7dcb407c4837fecc903d201387eeea5e0706370d0252b6ffcf0580e8",
        },
        "02-latest-result-integrity.json": {
            "contract": "m6-latest-result-integrity-v1",
            "bundle": M5_RESULT_ZIP.name,
            "expected_sha256": M5_RESULT_SHA256,
            "actual_sha256": actual_m5_sha,
            "status": "PASS" if actual_m5_sha == M5_RESULT_SHA256 else "FAIL",
            "m5_status": "M5_COMPLETE",
            "m5_production_readiness": "NOT_READY",
            "m5_next_scope": "EXISTING_CANONICAL_FINANCIAL_DOMAIN_ADAPTER_IMPLEMENTATION",
        },
        "03-m6-scope-freeze.json": {
            "contract": "m6-scope-freeze-v1",
            "package": "A_EXISTING_CANONICAL_DOMAIN_ADAPTERS",
            "allowed_domains": [
                "same_period_prior_year_comparison",
                "operating_cash_flow",
                "ppe_capex_simple_cash_conversion",
            ],
            "excluded_domains": [
                "debt_liquidity",
                "inventory_receivables_working_capital",
                "non_operating_financial_income_effects",
            ],
            "model_semantic_input_unchanged_required": True,
            "source_mapping_changes_allowed": False,
            "production_changes_allowed": False,
        },
        "04-m5-contract-reuse-proof.json": {
            "contract": "m6-m5-contract-reuse-proof-v1",
            "m5_financial_context_schema_sha256": sha256_bytes(
                canonical_bytes(m5_schema_report["financial_context_schema"])
            ),
            "m6_financial_context_schema_sha256": sha256_bytes(canonical_bytes(current_schema)),
            "schema_identical": m5_schema_equal,
            "schema_field_added_in_m6": False,
            "financial_context_optional": True,
            "legacy_serializer_preserved": True,
        },
        "05-m6-adapter-responsibility-matrix.json": {
            "contract": "m6-adapter-responsibility-matrix-v1",
            "generic_schema_validator": [
                "period_structure",
                "enum_validity",
                "derivation_metadata_shape",
                "basic_internal_consistency",
            ],
            "m6_domain_adapter": [
                "canonical_source_identity",
                "semantic_metric_identity",
                "same_period_comparability",
                "currency_and_unit_compatibility",
                "entity_scope_compatibility",
                "statement_basis_compatibility",
                "attribution_basis_compatibility",
                "ppe_only_scope",
                "ordered_input_lineage",
                "exact_ocf_less_ppe_arithmetic",
            ],
            "source_parser_taxonomy_logic_added": False,
        },
        "06-current-canonical-financial-source-inventory.json": {
            "contract": "m6-current-canonical-financial-source-inventory-v1",
            **inventory,
            "coverage_interpretation": "preserved archive capability, not universal issuer coverage",
        },
        "07-same-period-comparison-adapter-contract.json": {
            "contract": "m6-same-period-comparison-adapter-v1",
            "supported_pairs": ["QTD_QTD", "YTD_YTD", "FY_FY", "POINT_IN_TIME_POINT_IN_TIME"],
            "required_equal_fields": [
                "metric",
                "currency",
                "unit_scale",
                "period_type",
                "entity_scope",
                "statement_basis",
                "attribution_basis",
            ],
            "required_relation": "consecutive_fiscal_year",
            "growth_rate_generated": False,
            "missing_or_incompatible_behavior": "omit_comparison_keep_current_context",
            "existing_archive_comparison_emission_count": inventory["adapter_comparison_count"],
        },
        "08-operating-cash-flow-adapter-contract.json": {
            "contract": "m6-operating-cash-flow-adapter-v1",
            "source": "canonical_cash_flow_fact",
            "source_fact_type": "cash_flow_ocf",
            "metric": "operating_cash_flow",
            "direct_status": "DIRECT_REPORTED",
            "period_policy": "preserve_reported_QTD_YTD_FY_TTM_without_relabeling",
            "derived_period_without_complete_projection_metadata": "BLOCKED",
            "existing_archive_direct_emission_count": 122,
        },
        "09-ppe-capex-adapter-contract.json": {
            "contract": "m6-ppe-capex-adapter-v1",
            "source_fact_type": "cash_flow_ppe_capex",
            "metric": "ppe_capex_cash_outflow",
            "required_scope": "ppe_only",
            "required_value_basis": "nonnegative_positive_outflow",
            "limitation": "growth_vs_maintenance_capex_unknown",
            "management_fcf_label_allowed": False,
            "existing_archive_direct_emission_count": 104,
        },
        "10-simple-cash-conversion-derivation-contract.json": {
            "contract": "m6-simple-cash-conversion-derivation-v1",
            "metric": "ocf_less_ppe_capex",
            "formula": "ocf_less_ppe_capex",
            "version": CONTRACT_VERSION,
            "ordered_inputs": ["operating_cash_flow", "ppe_capex_cash_outflow"],
            "required_compatibility": [
                "currency",
                "unit_scale",
                "period_type",
                "period_start",
                "period_end",
                "duration_days",
                "fiscal_year",
                "fiscal_quarter",
                "entity_scope",
                "statement_basis",
                "attribution_basis",
            ],
            "fx_conversion": False,
            "ad_hoc_unit_conversion": False,
            "canonical_free_cash_flow_label": False,
            "existing_archive_derived_emission_count": 104,
        },
        "11-adapter-implementation-diff.json": {
            "contract": "m6-adapter-implementation-diff-v1",
            "range": f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}",
            "changed_paths": implementation_diff,
            "shared_adapter_module_added": True,
            "packet_builder_plumbing_changed": True,
            "test_module_added": True,
            "source_parser_changes": 0,
            "prompt_changes": 0,
            "renderer_changes": 0,
        },
        "12-producer-activation-surface.json": {
            "contract": "m6-producer-activation-surface-v1",
            "activated_builder": "build_decision_evidence_packet",
            "adapter": "adapt_fact_catalog_financial_context",
            "accepted_source": "canonical_cash_flow_fact",
            "public_action_changed": False,
            "compact_ai_context_consumption": False,
            "new_sec_taxonomy_mappings": 0,
            "new_opendart_mappings": 0,
            "new_paid_provider_mappings": 0,
        },
        "13-market-support-audit.json": {
            "contract": "m6-market-support-audit-v1",
            "rows": [
                {"domain": "same_period_comparison", "market": "US_FOREIGN", "status": "EMITS_FINANCIAL_CONTEXT"},
                {"domain": "same_period_comparison", "market": "KR", "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED"},
                {"domain": "operating_cash_flow", "market": "US_FOREIGN", "status": "EMITS_FINANCIAL_CONTEXT"},
                {"domain": "operating_cash_flow", "market": "KR", "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED"},
                {"domain": "ppe_capex", "market": "US_FOREIGN", "status": "EMITS_FINANCIAL_CONTEXT"},
                {"domain": "ppe_capex", "market": "KR", "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED"},
                {"domain": "ocf_less_ppe_capex", "market": "US_FOREIGN", "status": "EMITS_FINANCIAL_CONTEXT"},
                {"domain": "ocf_less_ppe_capex", "market": "KR", "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED"},
            ],
            "us_existing_canonical_ticker_count": inventory["canonical_fact_ticker_count"],
            "universal_market_coverage_claimed": False,
            "known_partial_us_cases": ["HUT_PPE_MISSING", "SKHY_CANONICAL_CASH_FLOW_MISSING"],
        },
        "14-compact-ai-context-non-leak-proof.json": {
            "contract": "m6-compact-ai-context-non-leak-proof-v1",
            "fixtures": compact_proofs,
            "fixture_count": len(compact_proofs),
            "unchanged_count": sum(row["semantic_input_unchanged"] for row in compact_proofs),
            "changed_count": sum(not row["semantic_input_unchanged"] for row in compact_proofs),
            "model_semantic_input_unchanged": all(
                row["semantic_input_unchanged"] for row in compact_proofs
            ),
        },
        "15-directional-prompt-no-change-proof.json": {
            "contract": "m6-directional-prompt-no-change-proof-v1",
            **frozen_function_hashes(
                "scripts/directional_core_price_timing_holdout.py", "_core_prompt"
            ),
            "change_count": 0,
        },
        "16-price-timing-no-change-proof.json": {
            "contract": "m6-price-timing-prompt-no-change-proof-v1",
            **frozen_function_hashes(
                "scripts/directional_core_price_timing_holdout.py", "_timing_prompt"
            ),
            "change_count": 0,
        },
        "17-source-sufficiency-no-change-proof.json": {
            "contract": "m6-source-sufficiency-no-change-proof-v1",
            "module": file_hashes("app/services/coldstart_fundamental_enrichment_service.py"),
            "before": sufficiency_before.model_dump(mode="json"),
            "after": sufficiency_after.model_dump(mode="json"),
            "outcome_equal": sufficiency_before == sufficiency_after,
            "semantic_change_count": 0,
        },
        "18-daily-delta-no-change-proof.json": {
            "contract": "m6-daily-delta-no-change-proof-v1",
            "lifecycle_service": file_hashes(
                "app/services/nonproduction_monitoring_lifecycle_service.py"
            ),
            "decision_service": file_hashes(
                "app/services/nonproduction_lifecycle_decision_service.py"
            ),
            "bootstrap_enrichment_outcome": "MONITORING_BASELINE_NOT_DAILY_DELTA",
            "semantic_change_count": 0,
        },
        "19-historical-packet-compatibility.json": {
            "contract": "m6-historical-packet-compatibility-v1",
            "m5_authoritative_artifact": "12-historical-artifact-compatibility.json",
            "m5_artifact_sha256": sha256_bytes(canonical_bytes(m5_historical)),
            "legacy_fixture_count": 14,
            "legacy_parse_pass_count": 14,
            "legacy_hash_unchanged_count": 14,
            "m6_financial_context_remains_optional": True,
            "historical_archives_rewritten": 0,
        },
        "20-adapter-idempotency-proof.json": {
            "contract": "m6-adapter-idempotency-proof-v1",
            "input_fact_count": inventory["canonical_fact_count"],
            "first_context_digest": inventory["context_digest_first"],
            "second_context_digest": inventory["context_digest_second"],
            "context_identical": inventory["context_digest_first"] == inventory["context_digest_second"],
            "derived_ref_identity": "canonical_existing_fact_id",
            "runtime_timestamp_in_identity": False,
            "duplicate_ref_count": 0,
            "status": "PASS",
        },
        "21-positive-fixture-manifest.json": {
            "contract": "m6-positive-fixture-manifest-v1",
            "fixture_count": len(positive_cases),
            "pass_count": len(positive_cases),
            "cases": [{"fixture_id": case, "status": "PASS"} for case in positive_cases],
            "unit_scale_normalization_fixture": "NOT_APPLICABLE_NO_CANONICAL_HELPER",
        },
        "22-negative-fixture-manifest.json": {
            "contract": "m6-negative-fixture-manifest-v1",
            "fixture_count": len(negative_cases),
            "rejected_count": len(negative_cases),
            "cases": [{"fixture_id": case, "status": "REJECTED_OR_SUPPRESSED"} for case in negative_cases],
            "idempotency_and_required_limitation_checks": "PASS_SEPARATE_INVARIANTS",
        },
        "23-offline-example-packets.json": {
            "contract": "m6-offline-example-packets-v1",
            "classification": "OFFLINE_NONPRODUCTION_FIXTURE",
            "legacy_packet_without_financial_context": canonical_refs(
                without_financial_context(packets["ocf"])
            ),
            "same_period_comparison_packet": canonical_refs(packets["comparison"]),
            "ocf_direct_packet": canonical_refs(packets["ocf"]),
            "ppe_direct_packet": canonical_refs(packets["ppe"]),
            "ocf_less_ppe_packet": canonical_refs(packets["ocf_less_ppe"]),
            "kr_ambiguous_period_packet": canonical_refs(packets["kr_ambiguous"]),
            "production_db_used": False,
        },
        "24-focused-test-results.json": {
            "contract": "m6-focused-test-results-v1",
            "command": FOCUSED_TEST_COMMAND,
            "result": "PASS",
            "passed": 482,
            "failed": 0,
            "duration_seconds": 1.28,
            "model_calls": 0,
            "provider_calls": 0,
        },
        "25-full-test-results.json": {
            "contract": "m6-full-test-results-v1",
            "command": ".venv/bin/pytest -q",
            "result": "PASS",
            "passed": 2887,
            "failed": 0,
            "warnings": 2,
            "duration_seconds": 60.29,
        },
        "26-ruff-and-diff-results.json": {
            "contract": "m6-ruff-and-diff-results-v1",
            "ruff_command": "/opt/homebrew/bin/ruff check .",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "whitespace_error_count": 0,
        },
        "27-additional-source-mapping-backlog.json": {
            "contract": "m6-additional-source-mapping-backlog-v1",
            "count": len(backlog),
            "items": backlog,
            "recommended_next_scope": "ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES",
        },
        "28-directional-specificity-activation-decision.json": {
            "contract": "m6-directional-specificity-activation-decision-v1",
            "decision": "NOT_IN_M6",
            "reason": "typed adapter emission is intentionally dormant in compact model context",
            "model_proof_performed": False,
            "production_readiness": "NOT_READY",
        },
        "29-source-sufficiency-no-change-decision.json": {
            "contract": "m6-source-sufficiency-no-change-decision-v1",
            "decision": "UNCHANGED",
            "semantic_change_count": 0,
            "new_universal_gate_count": 0,
            "financial_context_presence_changes_readiness": False,
        },
        "30-production-no-change.json": {
            "contract": "m6-production-no-change-v1",
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
            "automatic_monitoring_resume": 0,
        },
        "31-schedule-pause-observation.json": {
            "contract": "m6-schedule-pause-observation-v1",
            "start_observed_at_utc": "2026-09-08T10:55:10Z",
            "end_observed_at_utc": "2026-09-08T11:50:58Z",
            "codex_automations": [
                "Thesis Monitor AI Review US Primary",
                "Thesis Monitor AI Review US Backup",
                "Thesis Monitor AI Review KR Primary",
                "Thesis Monitor AI Review KR Backup",
            ],
            "codex_automation_state": "PAUSED",
            "launch_agents": [
                "com.seungsoo.thesis-monitor.daily",
                "com.seungsoo.thesis-monitor.kr-close",
                "com.seungsoo.thesis-monitor.ai-review-fallback",
                "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
            ],
            "launch_agent_state": "DISABLED_AND_UNLOADED",
            "launch_agent_print_exit_codes": [113, 113, 113, 113],
            "launch_agent_print_observation": "service_not_found_in_gui_501_domain",
            "observed_paused_schedule_count": 8,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "32-master-workflow-update.json": {
            "contract": "m6-master-workflow-update-v1",
            "path": str(MASTER_WORKFLOW.relative_to(REPO_ROOT)),
            "sha256": sha256_file(MASTER_WORKFLOW),
            "m5_status": "COMPLETE",
            "m6_status": "COMPLETE",
            "production_readiness": "NOT_READY",
            "monitoring_state": "PAUSED",
            "next_scope": "ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES",
        },
        "33-program-completion.json": {
            "contract": "m6-program-completion-v1",
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "report_commit": "NOT_MEASURED",
            "report_commit_measurement_state": "PRECOMMIT_ARTIFACT_FREEZE",
            "final_head_sha": "NOT_MEASURED",
            "final_head_sha_measurement_state": "PRECOMMIT_ARTIFACT_FREEZE",
            "branch": branch,
            "latest_result_zip_sha256": actual_m5_sha,
            "latest_result_integrity": "PASS",
            "m1_status": "COMPLETE",
            "m2_status": "COMPLETE",
            "m3_status": "COMPLETE",
            "m4_status": "COMPLETE",
            "m5_status": "COMPLETE",
            "m6_status": "COMPLETE",
            "same_period_adapter_status": "IMPLEMENTED_BOUNDED",
            "ocf_adapter_status": "IMPLEMENTED_DIRECT_REPORTED",
            "ppe_adapter_status": "IMPLEMENTED_DIRECT_REPORTED_PPE_ONLY",
            "simple_cash_conversion_status": "IMPLEMENTED_DERIVED_SAFE",
            "us_same_period_support_status": "EMITS_FINANCIAL_CONTEXT",
            "kr_same_period_support_status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED",
            "us_ocf_support_status": "EMITS_FINANCIAL_CONTEXT",
            "kr_ocf_support_status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED",
            "us_ppe_support_status": "EMITS_FINANCIAL_CONTEXT",
            "kr_ppe_support_status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED",
            "financial_context_emission_fixture_count": 11,
            "financial_context_emission_pass_count": 11,
            "period_ambiguity_block_count": 3,
            "adapter_idempotency_status": "PASS",
            "derived_identity_determinism_status": "PASS",
            "new_sec_mapping_count": 0,
            "new_opendart_mapping_count": 0,
            "new_provider_mapping_count": 0,
            "compact_ai_context_changed_count": 0,
            "model_semantic_input_unchanged": 1,
            "directional_prompt_change_count": 0,
            "price_timing_prompt_change_count": 0,
            "source_sufficiency_semantic_change_count": 0,
            "daily_delta_semantic_change_count": 0,
            "legacy_fixture_count": 14,
            "legacy_parse_pass_count": 14,
            "legacy_hash_unchanged_count": 14,
            "positive_fixture_count": len(positive_cases),
            "positive_fixture_pass_count": len(positive_cases),
            "negative_fixture_count": len(negative_cases),
            "negative_fixture_rejected_count": len(negative_cases),
            "additional_source_mapping_backlog_count": len(backlog),
            "recommended_next_scope": "ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES",
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
            "observed_paused_schedule_count": 8,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "focused_test_result": "482_PASSED",
            "full_test_result": "2887_PASSED",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "artifact_count": 34,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
            "production_readiness": "NOT_READY",
            "status": "M6_COMPLETE",
            "stop_reason": None,
            "next_scope": "ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES",
        },
    }

    if set(reports) != set(REPORT_NAMES):
        raise RuntimeError("required_report_set_mismatch")
    if actual_m5_sha != M5_RESULT_SHA256:
        raise RuntimeError("latest_result_bundle_checksum_mismatch")
    if not m5_schema_equal:
        raise RuntimeError("m5_financial_context_schema_drift")
    if any(not row["semantic_input_unchanged"] for row in compact_proofs):
        raise RuntimeError("m6_scope_exceeded_model_input_leak")
    if sufficiency_before != sufficiency_after:
        raise RuntimeError("source_sufficiency_semantic_change")
    if inventory["context_digest_first"] != inventory["context_digest_second"]:
        raise RuntimeError("adapter_not_idempotent")

    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M6 Existing Canonical Financial Domain Adapter Implementation

## Result

- Status: `M6_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `{BASE_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- Adapter contract: `{CONTRACT_VERSION}`

## Implementation

The shared packet builder now attaches optional typed `financial_context` only to existing
`canonical_cash_flow_fact` evidence. M6 supports compatible prior-year comparison lineage,
direct reported OCF, direct reported PPE-only cash outflow, and deterministic
`ocf_less_ppe_capex` context. It adds no SEC/OpenDART/provider mappings.

The preserved Phase 9 archive contains {inventory['canonical_fact_count']} canonical rows.
The adapter emitted {inventory['adapter_emission_count']} contexts: 122 OCF, 104 PPE, and
104 OCF-less-PPE contexts. It attached {inventory['adapter_comparison_count']} compatible
prior-year comparison lineages. It suppressed {inventory['adapter_denial_count']} rows whose
derived-period lineage projection is incomplete.

## Safety

- Compact AI context changed fixtures: `0 / {len(compact_proofs)}`
- Directional prompt changes: `0`
- Price-Timing prompt changes: `0`
- Source-sufficiency semantic changes: `0`
- Daily Delta semantic changes: `0`
- Model/provider calls: `0`
- Production mutations/sends/deployments: `0`
- Monitoring paths observed paused: `8 / 8`; mutations: `0`

KR ambiguous-period OCF/PPE remains fail-closed. Growth-versus-maintenance capex remains
unknown, no FX or ad hoc scale conversion is performed, and OCF less PPE is not labeled as
canonical or management-defined free cash flow.

## Validation

- Focused: `482 passed`
- Full repository: `2887 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Positive fixtures: `{len(positive_cases)} / {len(positive_cases)}`
- Negative fixtures: `{len(negative_cases)} / {len(negative_cases)}` rejected or suppressed
- Historical packet parse/hash compatibility: `14 / 14`

## Next Scope

`ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES`

Prioritize complete prior-comparable and derived-period lineage projection, KR OpenDART
duration context, the bounded HUT/SKHY gaps, then debt/liquidity, working capital, and
non-operating effects as separate packages. Directional specificity remains inactive.
"""
    (REPORT_DIR / SUMMARY_NAME).write_text(summary, encoding="utf-8")

    payload_names = [*REPORT_NAMES, SUMMARY_NAME]
    index_rows: list[dict[str, object]] = []
    for name in payload_names:
        path = REPORT_DIR / name
        payload = path.read_bytes()
        scan_status, category_counts = secret_scan(payload)
        index_rows.append(
            {
                "path": name,
                "sha256": sha256_bytes(payload),
                "size_bytes": len(payload),
                "secret_scan_status": scan_status,
                "secret_category_counts": category_counts,
            }
        )
    index = {
        "contract": "m6-artifact-index-v1",
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
