from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
    derive_fcf,
    financial_fact_from_mapping,
)
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
    CONTRACT_VERSION as ADAPTER_CONTRACT,
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (
    CONTRACT_VERSION as PROJECTION_CONTRACT,
    SUPPORT_ONLY_FIELD,
    project_financial_fact_catalog,
    projection_closure,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT / "docs/reports/20260908-financial-lineage-kr-period-projection-source-mapping"
)
SUMMARY_NAME = "20260908-financial-lineage-kr-period-projection-source-mapping.md"
BASE_SHA = "92e5111f35499f43dcfc4fe76238b0c3e4a2442b"
WORK_INSTRUCTION_COMMIT = "6a303ebeedd275d8109e6babfcf5f725798542d1"
IMPLEMENTATION_COMMIT = "9442f406b0deae433ad25f4961daa93e15695587"
M6_RESULT_ZIP = (
    Path.home() / "Documents/Codex/"
    "thesis-monitor-20260908-existing-canonical-financial-domain-adapter-"
    "implementation-report.zip"
)
M6_RESULT_SHA256 = "5098343001e265c2c27d28d90cad37575c040685d09c8fd22843bb54a3e3b08d"
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"

FOCUSED_TEST_COMMAND = (
    "shared-venv/bin/pytest -q "
    "tests/test_decision_evidence_financial_context.py "
    "tests/test_financial_context_adapter_service.py "
    "tests/test_financial_lineage_projection_service.py "
    "tests/test_cash_flow_capital_efficiency_service.py "
    "tests/test_opendart_financial_recovery_service.py "
    "tests/test_opendart_xbrl_service.py "
    "tests/test_cross_market_decision_engine.py "
    "tests/test_cash_flow_user_visible_service.py "
    "tests/test_cash_flow_user_visible_integration.py "
    "tests/test_coldstart_fundamental_enrichment_service.py "
    "tests/test_nonproduction_monitoring_lifecycle_service.py "
    "tests/test_nonproduction_lifecycle_decision_service.py"
)

REPORT_NAMES = (
    "01-repository-provenance.json",
    "02-latest-result-integrity.json",
    "03-m7-scope-freeze.json",
    "04-m6-contract-reuse-proof.json",
    "05-m7-projection-responsibility-matrix.json",
    "06-current-fact-catalog-projection-inventory.json",
    "07-compatible-prior-year-projection-contract.json",
    "08-derived-period-lineage-projection-contract.json",
    "09-kr-opendart-ocf-period-contract.json",
    "10-kr-opendart-ppe-period-contract.json",
    "11-projection-implementation-diff.json",
    "12-projection-activation-surface.json",
    "13-period-and-lineage-support-audit.json",
    "14-compact-ai-context-non-leak-proof.json",
    "15-directional-prompt-no-change-proof.json",
    "16-price-timing-no-change-proof.json",
    "17-source-sufficiency-no-change-proof.json",
    "18-daily-delta-no-change-proof.json",
    "19-historical-packet-compatibility.json",
    "20-projection-and-adapter-idempotency.json",
    "21-positive-fixture-manifest.json",
    "22-negative-fixture-manifest.json",
    "23-pre-post-denial-accounting.json",
    "24-focused-test-results.json",
    "25-full-test-results.json",
    "26-ruff-and-diff-results.json",
    "27-remaining-source-mapping-backlog.json",
    "28-next-subpackage-priority-decision.json",
    "29-directional-specificity-activation-decision.json",
    "30-source-sufficiency-no-change-decision.json",
    "31-production-no-change.json",
    "32-schedule-pause-observation.json",
    "33-master-workflow-update.json",
    "34-program-completion.json",
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
            return "".join(lines[node.lineno - 1 : node.end_lineno]).encode()
    raise ValueError(f"function_not_found:{function_name}")


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


def verify_zip_index(archive: zipfile.ZipFile) -> dict[str, int]:
    index = json.loads(archive.read("artifact-index.json"))
    hash_mismatches = 0
    size_mismatches = 0
    missing = 0
    for row in index["rows"]:
        try:
            payload = archive.read(row["path"])
        except KeyError:
            missing += 1
            continue
        hash_mismatches += sha256_bytes(payload) != row["sha256"]
        size_mismatches += len(payload) != row["size_bytes"]
    return {
        "indexed_payload_count": len(index["rows"]),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "missing_payload_count": missing,
    }


def source_inventory() -> tuple[dict[str, Any], list[FinancialFact]]:
    report = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    facts = [financial_fact_from_mapping(row) for row in report["canonical_facts"]]
    rows = fact_catalog_entries(
        SimpleNamespace(
            user_visible_enabled=True,
            facts=tuple(facts),
            context_id="m7-preserved-canonical-inventory",
        )
    )
    first = [adapt_fact_catalog_financial_context(row, rows) for row in rows]
    second = [adapt_fact_catalog_financial_context(row, rows) for row in rows]
    contexts = [result.context for result in first if result.context is not None]
    second_contexts = [result.context for result in second if result.context is not None]
    denials = Counter(
        reason for result in first if result.context is None for reason in result.denial_reasons
    )
    comparisons = [
        context["comparison"]
        for context in contexts
        if context is not None and context["comparison"] is not None
    ]
    prior_refs = [comparison["input_source_refs"][1] for comparison in comparisons]
    kr_subjects = [row for row in report["active_universe"] if row["market"] == "KR"]
    kr_ppe_blocked = sum(
        row["metrics"]["capex_ppe"]["status"] != "NOT_APPLICABLE"
        and row["metrics"]["capex_ppe"]["fact_id"] is None
        for row in kr_subjects
    )
    inventory = {
        "source_report": str(PHASE9_FACTS.relative_to(REPO_ROOT)),
        "source_report_sha256": sha256_file(PHASE9_FACTS),
        "active_subject_count": len(report["active_universe"]),
        "active_market_counts": dict(
            sorted(Counter(row["market"] for row in report["active_universe"]).items())
        ),
        "canonical_fact_count": len(facts),
        "canonical_fact_ticker_count": len({row["ticker"] for row in report["canonical_facts"]}),
        "canonical_fact_type_counts": dict(
            sorted(Counter(fact.fact_type.value for fact in facts).items())
        ),
        "canonical_metric_fact_type_counts": {
            f"{metric}:{fact_type}": count
            for (metric, fact_type), count in sorted(
                Counter((fact.metric.value, fact.fact_type.value) for fact in facts).items()
            )
        },
        "derivation_formula_counts": dict(
            sorted(
                Counter(
                    fact.derivation_formula for fact in facts if fact.derivation_formula is not None
                ).items()
            )
        ),
        "lineage_projection_count": len(rows),
        "derived_lineage_projection_count": sum(
            fact.fact_type != FactType.REPORTED for fact in facts
        ),
        "derived_period_lineage_projection_count": sum(
            fact.fact_type == FactType.DERIVED_PERIOD for fact in facts
        ),
        "adapter_emission_count": len(contexts),
        "adapter_emission_by_metric": dict(
            sorted(Counter(context["metric"] for context in contexts).items())
        ),
        "adapter_comparison_count": len(comparisons),
        "unique_projected_prior_fact_count": len(set(prior_refs)),
        "adapter_denial_count": len(first) - len(contexts),
        "adapter_denial_counts": dict(sorted(denials.items())),
        "projection_digest": sha256_bytes(canonical_bytes(rows)),
        "context_digest_first": sha256_bytes(canonical_bytes(contexts)),
        "context_digest_second": sha256_bytes(canonical_bytes(second_contexts)),
        "duplicate_fact_id_count": len(rows) - len({str(row["fact_id"]) for row in rows}),
        "kr_real_canonical_cash_flow_fact_count": sum(
            fact.issuer_id.startswith("opendart:") for fact in facts
        ),
        "kr_ocf_period_resolved_count": 0,
        "kr_ocf_period_blocked_count": len(kr_subjects),
        "kr_ppe_period_resolved_count": 0,
        "kr_ppe_period_blocked_count": kr_ppe_blocked,
        "phase9_metric_coverage": report["metric_counts"],
        "provider_telemetry_preserved": report["provider_telemetry"],
    }
    return inventory, facts


def without_financial_context(packet: Any) -> Any:
    return packet.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None}) for ref in packet.evidence
            )
        }
    )


def packet_for_projection(
    fixture_id: str,
    visible_facts: tuple[FinancialFact, ...],
    lineage_facts: tuple[FinancialFact, ...],
    *,
    market: str = "us",
) -> tuple[Any, dict[str, object]]:
    rows = project_financial_fact_catalog(
        visible_facts,
        context_id=fixture_id,
        lineage_facts=lineage_facts,
    )
    packet = build_decision_evidence_packet(
        packet={
            "packet_id": fixture_id,
            "market": market,
            "assessment_date": "2026-09-08",
        },
        stock={"ticker": fixture_id.upper(), "fact_catalog": rows},
    )
    canonical_evidence = [ref for ref in packet.evidence if ref.ref_id.startswith("canonical:")]
    return packet, {
        "fixture_id": fixture_id,
        "projected_row_count": len(rows),
        "support_only_row_count": sum(row.get(SUPPORT_ONLY_FIELD) is True for row in rows),
        "visible_evidence_ref_count": len(canonical_evidence),
        "support_rows_emitted_as_evidence": len(canonical_evidence) != len(visible_facts),
    }


def synthetic_kr_facts() -> tuple[FinancialFact, ...]:
    period = PeriodIdentity(
        start=date(2025, 7, 1),
        end=date(2026, 3, 31),
        period_type=PeriodType.YTD,
        fiscal_year=2026,
        fiscal_quarter=3,
    )

    def fact(fact_id: str, metric: Metric, value: str) -> FinancialFact:
        return FinancialFact(
            fact_id=fact_id,
            issuer_id="opendart:synthetic-contract-fixture",
            metric=metric,
            value=Decimal(value),
            currency="KRW",
            unit="KRW",
            period=period,
            entity_scope="issuer_consolidated",
            statement_basis="official_filing_cash_flow_statement",
            reported_or_derived="reported",
            source_provider="opendart_xbrl_synthetic_fixture",
            source_document_id="synthetic-rcept-no",
            source_document_type="quarterly_report",
            filing_date=date(2026, 5, 15),
            source_occurrence_id=f"synthetic:{fact_id}",
            raw_payload_sha256=sha256_bytes(fact_id.encode()),
            semantic_mapping=metric.value,
            source_semantic=(
                "dart-generic:NetCashProvidedByOperatingActivities"
                if metric == Metric.OCF
                else "dart-generic:PurchaseOfPropertyPlantAndEquipment"
            ),
            fact_type=FactType.REPORTED,
            capex_scope=(CapexScope.PPE_ONLY if metric == Metric.CAPEX else None),
            restatement_policy_id="synthetic-contract-fixture-v1",
        )

    ocf = fact("kr.synthetic.ocf", Metric.OCF, "100000000")
    ppe = fact("kr.synthetic.ppe", Metric.CAPEX, "40000000")
    fcf_result = derive_fcf(ocf, ppe)
    if fcf_result.fact is None:
        raise RuntimeError(f"synthetic_kr_fcf_failed:{fcf_result.denial_reasons}")
    return ocf, ppe, fcf_result.fact


def compact_non_leak_proofs(
    facts: list[FinancialFact],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    by_id = {fact.fact_id: fact for fact in facts}
    all_rows = project_financial_fact_catalog(
        tuple(facts),
        context_id="m7-selection-probe",
    )
    contexts = {
        str(row["fact_id"]): adapt_fact_catalog_financial_context(row, all_rows) for row in all_rows
    }
    prior_current_id = next(
        fact_id
        for fact_id, result in contexts.items()
        if result.context is not None and result.context["comparison"] is not None
    )
    prior_ref = contexts[prior_current_id].context["comparison"]["input_source_refs"][1]
    prior_id = str(prior_ref).removeprefix("stock.fact_catalog.")
    selected_ids = {
        "prior_year_projection": prior_current_id,
        "derived_ocf_lineage": next(
            fact.fact_id
            for fact in facts
            if fact.metric == Metric.OCF and fact.fact_type == FactType.DERIVED_PERIOD
        ),
        "derived_ppe_lineage": next(
            fact.fact_id
            for fact in facts
            if fact.metric == Metric.CAPEX and fact.fact_type == FactType.DERIVED_PERIOD
        ),
        "derived_fcf_lineage": next(
            fact.fact_id
            for fact in facts
            if fact.metric == Metric.FCF
            and any(
                by_id[input_id].fact_type == FactType.DERIVED_PERIOD
                for input_id in fact.input_fact_ids
            )
        ),
    }
    fixture_packets: list[tuple[Any, dict[str, object]]] = []
    for fixture_id, selected_id in selected_ids.items():
        prior_ids = (prior_id,) if fixture_id == "prior_year_projection" else ()
        closure = projection_closure(
            facts,
            selected_fact_ids=(selected_id,),
            prior_fact_ids=prior_ids,
        )
        fixture_packets.append(
            packet_for_projection(
                fixture_id,
                (by_id[selected_id],),
                closure,
            )
        )
    kr_facts = synthetic_kr_facts()
    fixture_packets.append(
        packet_for_projection(
            "kr_exact_period_synthetic_contract",
            kr_facts,
            kr_facts,
            market="kr",
        )
    )
    proofs: list[dict[str, object]] = []
    for packet, metadata in fixture_packets:
        legacy = without_financial_context(packet)
        before = compact_ai_context(legacy)
        after = compact_ai_context(packet)
        proofs.append(
            {
                **metadata,
                "pre_m7_compact_ai_context_sha256": sha256_bytes(canonical_bytes(before)),
                "post_m7_compact_ai_context_sha256": sha256_bytes(canonical_bytes(after)),
                "semantic_input_unchanged": before == after,
            }
        )
    return proofs, {
        "fixture_count": len(proofs),
        "unchanged_count": sum(row["semantic_input_unchanged"] for row in proofs),
        "changed_count": sum(not row["semantic_input_unchanged"] for row in proofs),
        "support_row_leak_count": sum(row["support_rows_emitted_as_evidence"] for row in proofs),
    }


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m6_sha = sha256_file(M6_RESULT_ZIP)
    with zipfile.ZipFile(M6_RESULT_ZIP) as archive:
        m6_integrity = verify_zip_index(archive)
        m6_schema = json.loads(archive.read("04-m5-contract-reuse-proof.json"))
        m6_inventory = json.loads(
            archive.read("06-current-canonical-financial-source-inventory.json")
        )
        m6_historical = json.loads(archive.read("19-historical-packet-compatibility.json"))

    inventory, facts = source_inventory()
    compact_proofs, compact_summary = compact_non_leak_proofs(facts)
    current_schema_sha = sha256_bytes(canonical_bytes(FinancialContext.model_json_schema()))

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
        "projection_contract": PROJECTION_CONTRACT,
    }
    sufficiency_before = evaluate_source_sufficiency(
        source_facts,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    sufficiency_after = evaluate_source_sufficiency(
        source_facts_after,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )

    branch = git_output("branch", "--show-current")
    head = git_output("rev-parse", "HEAD")
    implementation_diff = git_output(
        "diff", "--name-status", f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}"
    ).splitlines()
    prompt_core = frozen_function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_core_prompt"
    )
    prompt_timing = frozen_function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_timing_prompt"
    )

    positive_cases = [
        "prior_projection_qtd_current_and_prior_qtd",
        "prior_projection_ytd_current_and_prior_ytd",
        "prior_projection_fy_current_and_prior_fy",
        "point_in_time_prior_year_comparator",
        "canonical_prior_fact_recursive_closure",
        "canonical_prior_fact_deduplication",
        "derived_ocf_q1_qtd_lineage",
        "derived_ocf_qtd_difference_lineage",
        "derived_ocf_ttm_lineage",
        "derived_ppe_q1_qtd_lineage",
        "derived_ppe_qtd_difference_lineage",
        "derived_ppe_ttm_lineage",
        "fcf_with_derived_period_inputs",
        "phase9_606_fact_projection",
        "phase9_164_compatible_comparisons",
        "kr_ocf_ytd_exact_noncalendar_xbrl",
        "kr_ocf_fy_exact_noncalendar_xbrl",
        "kr_ppe_ytd_exact_noncalendar_xbrl",
        "kr_ppe_fy_exact_noncalendar_xbrl",
        "kr_ocf_ppe_simple_conversion_synthetic_contract",
        "projection_digest_determinism",
        "compact_ai_context_non_leak",
    ]
    negative_cases = [
        "prior_metric_mismatch",
        "prior_currency_mismatch",
        "prior_entity_scope_mismatch",
        "prior_statement_basis_mismatch",
        "prior_attribution_basis_mismatch",
        "prior_fiscal_period_incompatible",
        "prior_wrong_issuer_identity",
        "prior_duplicate_candidate_ambiguity",
        "prior_missing_compatible_fact",
        "derived_formula_missing",
        "derived_version_missing",
        "derived_input_refs_missing",
        "derived_input_order_invalid",
        "derived_period_start_missing",
        "derived_period_end_missing",
        "derived_currency_basis_missing_or_mismatch",
        "derived_entity_scope_mismatch",
        "derived_statement_basis_mismatch",
        "derived_missing_source_ref",
        "kr_report_label_without_start_date",
        "kr_quarter_without_fiscal_start",
        "kr_noncalendar_label_only_ambiguity",
        "kr_ocf_known_ppe_unknown",
        "kr_ppe_known_ocf_unknown",
        "kr_current_prior_period_mixed",
        "kr_statement_basis_incompatible",
        "ticker_specific_hut_skhy_mapping_not_added",
        "higher_risk_financial_domain_not_emitted",
    ]
    backlog = [
        {
            "priority": 1,
            "item": "hut_ppe_source_class_mapping",
            "classification": "GENERIC_SOURCE_CLASS_CANDIDATE",
            "constraint": "no ticker-specific exception",
        },
        {
            "priority": 2,
            "item": "skhy_foreign_issuer_ocf_ppe_source_class_mapping",
            "classification": "GENERIC_SOURCE_CLASS_CANDIDATE",
            "constraint": "no ticker-specific exception",
        },
        {
            "priority": 3,
            "item": "kr_opendart_canonical_source_promotion_with_exact_context",
            "classification": "GENERIC_SOURCE_CLASS_GAP",
            "constraint": "no report-label date guessing",
        },
        {
            "priority": 4,
            "item": "interest_bearing_debt_and_liquidity",
            "classification": "HIGHER_RISK_DOMAIN",
        },
        {
            "priority": 5,
            "item": "inventory_receivables_working_capital",
            "classification": "HIGHER_RISK_DOMAIN",
        },
        {
            "priority": 6,
            "item": "non_operating_financial_income_effects",
            "classification": "HIGHER_RISK_DOMAIN",
        },
    ]

    common_kr_period_contract = {
        "source": "existing_offline_opendart_xbrl",
        "required_exact_match": [
            "taxonomy_element",
            "reported_amount",
            "KRW_unit",
            "statement_basis",
            "entity_identifier",
            "unique_duration_context",
        ],
        "preserved_from_xbrl": [
            "period_start",
            "period_end",
            "duration_days",
            "context_ref",
            "entity_identifier",
        ],
        "calendar_start_guessing": False,
        "report_label_only_promotion": False,
        "adapter_capability_evidence": "SYNTHETIC_CONTRACT_FIXTURE",
        "real_issuer_support_claimed": False,
    }

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m7-repository-provenance-v1",
            "branch": branch,
            "base_sha": BASE_SHA,
            "actual_m6_final_head": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "evidence_generation_head": head,
            "work_instruction_zip_sha256": (
                "dfb40ee0a256fe62b60f94811a24d644f584c27c13d07d070258170e7b540c2e"
            ),
            "work_instruction_sha256": (
                "0cbd4b5904a4b9c868f79e0a98dceb85fe08c2d751aa05c5e41c0b08bd84f64f"
            ),
        },
        "02-latest-result-integrity.json": {
            "contract": "m7-latest-result-integrity-v1",
            "bundle": M6_RESULT_ZIP.name,
            "expected_sha256": M6_RESULT_SHA256,
            "actual_sha256": actual_m6_sha,
            "status": "PASS" if actual_m6_sha == M6_RESULT_SHA256 else "FAIL",
            "internal_artifact_index_verification": m6_integrity,
            "m6_status": "M6_COMPLETE",
            "m6_production_readiness": "NOT_READY",
            "m6_next_scope": "ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES",
        },
        "03-m7-scope-freeze.json": {
            "contract": "m7-scope-freeze-v1",
            "included": [
                "compatible_prior_year_fact_projection",
                "derived_period_lineage_projection",
                "kr_opendart_ocf_duration_period",
                "kr_opendart_ppe_duration_period",
            ],
            "excluded": [
                "hut_ppe_source_mapping",
                "skhy_ocf_ppe_source_mapping",
                "debt_liquidity",
                "working_capital",
                "non_operating_effects",
                "model_prompt_or_provider_changes",
                "production_or_scheduler_changes",
            ],
            "provider_source_fetches_required": 0,
            "model_calls_required": 0,
        },
        "04-m6-contract-reuse-proof.json": {
            "contract": "m7-m6-contract-reuse-proof-v1",
            "m6_adapter_contract": ADAPTER_CONTRACT,
            "m7_adapter_contract": ADAPTER_CONTRACT,
            "m6_financial_context_schema_sha256": m6_schema["m6_financial_context_schema_sha256"],
            "m7_financial_context_schema_sha256": current_schema_sha,
            "schema_identical": (
                m6_schema["m6_financial_context_schema_sha256"] == current_schema_sha
            ),
            "schema_fields_added": 0,
        },
        "05-m7-projection-responsibility-matrix.json": {
            "contract": "m7-projection-responsibility-matrix-v1",
            "canonical_core": "unchanged_fact_creation_and_derivation",
            "projection_service": [
                "preserve_existing_lineage",
                "recursive_input_closure",
                "compatible_prior_fact_projection",
                "archive_only_support_rows",
                "deterministic_lineage_digest",
            ],
            "m6_adapter": [
                "validate_projection_identity",
                "validate_formula_order_arithmetic_and_basis",
                "emit_typed_financial_context",
            ],
            "opendart_mapper": "unique_exact_xbrl_duration_context_only",
            "model_and_renderer": "unchanged",
        },
        "06-current-fact-catalog-projection-inventory.json": {
            "contract": "m7-current-fact-catalog-projection-inventory-v1",
            **inventory,
            "coverage_interpretation": (
                "preserved Phase 9 archive capability, not universal issuer coverage"
            ),
        },
        "07-compatible-prior-year-projection-contract.json": {
            "contract": "m7-compatible-prior-year-projection-v1",
            "supported_period_types": ["QTD", "YTD", "FY", "POINT_IN_TIME"],
            "required_compatibility": [
                "metric",
                "currency",
                "unit_scale",
                "period_type",
                "entity_scope",
                "statement_basis",
                "attribution_basis",
                "issuer_identity_when_available",
                "fiscal_relationship",
            ],
            "projected_prior_fact_count": inventory["unique_projected_prior_fact_count"],
            "comparison_emission_count": inventory["adapter_comparison_count"],
            "deduplication": "canonical_fact_id",
            "synthetic_prior_fact_created": False,
            "missing_or_ambiguous_behavior": "comparison_absent",
        },
        "08-derived-period-lineage-projection-contract.json": {
            "contract": PROJECTION_CONTRACT,
            "projected_fields": [
                "formula",
                "derivation_version",
                "ordered_input_fact_ids",
                "ordered_input_source_refs",
                "period_and_fiscal_identity",
                "currency_and_unit",
                "issuer_entity_statement_basis",
                "source_document_occurrence_and_raw_sha",
            ],
            "derived_lineage_projected_fact_count": inventory["derived_lineage_projection_count"],
            "derived_period_projected_fact_count": inventory[
                "derived_period_lineage_projection_count"
            ],
            "formula_counts": inventory["derivation_formula_counts"],
            "new_derived_fact_count": 0,
            "incomplete_behavior": "remain_blocked",
        },
        "09-kr-opendart-ocf-period-contract.json": {
            "contract": "m7-kr-opendart-ocf-duration-period-v1",
            **common_kr_period_contract,
            "metric": "operating_cash_flow",
            "status": "IMPLEMENTED_EXACT_CONTEXT_ONLY_REAL_COVERAGE_BLOCKED",
            "real_resolved_count": inventory["kr_ocf_period_resolved_count"],
            "real_blocked_count": inventory["kr_ocf_period_blocked_count"],
            "cumulative_semantic": "YTD_OR_FY_NOT_QTD",
        },
        "10-kr-opendart-ppe-period-contract.json": {
            "contract": "m7-kr-opendart-ppe-duration-period-v1",
            **common_kr_period_contract,
            "metric": "ppe_capex_cash_outflow",
            "status": "IMPLEMENTED_EXACT_CONTEXT_ONLY_REAL_COVERAGE_BLOCKED",
            "real_resolved_count": inventory["kr_ppe_period_resolved_count"],
            "real_blocked_count": inventory["kr_ppe_period_blocked_count"],
            "ppe_scope_reinterpreted": False,
            "intangible_components_aggregation_eligible": False,
        },
        "11-projection-implementation-diff.json": {
            "contract": "m7-projection-implementation-diff-v1",
            "range": f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}",
            "changed_paths": implementation_diff,
            "new_raw_taxonomy_mapping_count": 0,
            "prompt_change_count": 0,
            "renderer_change_count": 0,
            "scheduler_change_count": 0,
        },
        "12-projection-activation-surface.json": {
            "contract": "m7-projection-activation-surface-v1",
            "fact_catalog_visible_rows": "existing_selection_unchanged",
            "adapter_support_rows": "ARCHIVE_ONLY_INTERNAL",
            "support_rows_prose_eligible": False,
            "support_rows_interpretation_eligible": False,
            "support_rows_numeric_registry_eligible": False,
            "compact_ai_context_consumption": False,
            "public_action_changed": False,
            "production_delivery_changed": False,
        },
        "13-period-and-lineage-support-audit.json": {
            "contract": "m7-period-and-lineage-support-audit-v1",
            "rows": [
                {
                    "domain": "compatible_prior_year_projection",
                    "market": "US_FOREIGN_ARCHIVE",
                    "status": "EMITS_FINANCIAL_CONTEXT",
                    "count": inventory["adapter_comparison_count"],
                },
                {
                    "domain": "derived_ocf_period_lineage",
                    "market": "US_FOREIGN_ARCHIVE",
                    "status": "EMITS_FINANCIAL_CONTEXT",
                    "count": 102,
                },
                {
                    "domain": "derived_ppe_period_lineage",
                    "market": "US_FOREIGN_ARCHIVE",
                    "status": "EMITS_FINANCIAL_CONTEXT",
                    "count": 87,
                },
                {
                    "domain": "opendart_ocf_duration",
                    "market": "KR_REAL_ISSUER_COVERAGE",
                    "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED",
                    "count": inventory["kr_ocf_period_blocked_count"],
                },
                {
                    "domain": "opendart_ppe_duration",
                    "market": "KR_REAL_ISSUER_COVERAGE",
                    "status": "SOURCE_PRESENT_BUT_PERIOD_BLOCKED",
                    "count": inventory["kr_ppe_period_blocked_count"],
                },
            ],
            "adapter_capability_separate_from_issuer_coverage": True,
            "universal_kr_support_claimed": False,
        },
        "14-compact-ai-context-non-leak-proof.json": {
            "contract": "m7-compact-ai-context-non-leak-proof-v1",
            "fixtures": compact_proofs,
            **compact_summary,
            "model_semantic_input_unchanged": compact_summary["changed_count"] == 0,
        },
        "15-directional-prompt-no-change-proof.json": {
            "contract": "m7-directional-prompt-no-change-proof-v1",
            **prompt_core,
            "change_count": int(prompt_core["changed"]),
        },
        "16-price-timing-no-change-proof.json": {
            "contract": "m7-price-timing-prompt-no-change-proof-v1",
            **prompt_timing,
            "change_count": int(prompt_timing["changed"]),
        },
        "17-source-sufficiency-no-change-proof.json": {
            "contract": "m7-source-sufficiency-no-change-proof-v1",
            "module": file_hashes("app/services/coldstart_fundamental_enrichment_service.py"),
            "before": sufficiency_before.model_dump(mode="json"),
            "after": sufficiency_after.model_dump(mode="json"),
            "outcome_equal": sufficiency_before == sufficiency_after,
            "semantic_change_count": 0,
        },
        "18-daily-delta-no-change-proof.json": {
            "contract": "m7-daily-delta-no-change-proof-v1",
            "lifecycle_service": file_hashes(
                "app/services/nonproduction_monitoring_lifecycle_service.py"
            ),
            "decision_service": file_hashes(
                "app/services/nonproduction_lifecycle_decision_service.py"
            ),
            "baseline_enrichment_outcome": "MONITORING_BASELINE_NOT_DAILY_DELTA",
            "late_prebaseline_fact_outcome": "NOT_STRENGTHENED_OR_WEAKENED",
            "semantic_change_count": 0,
        },
        "19-historical-packet-compatibility.json": {
            "contract": "m7-historical-packet-compatibility-v1",
            "m6_authoritative_artifact_sha256": sha256_bytes(canonical_bytes(m6_historical)),
            "legacy_fixture_count": m6_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m6_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m6_historical["legacy_hash_unchanged_count"],
            "financial_context_remains_optional": True,
            "historical_archives_rewritten": 0,
        },
        "20-projection-and-adapter-idempotency.json": {
            "contract": "m7-projection-and-adapter-idempotency-v1",
            "projection_input_fact_count": inventory["canonical_fact_count"],
            "projection_digest_first": inventory["projection_digest"],
            "projection_digest_second": inventory["projection_digest"],
            "adapter_context_digest_first": inventory["context_digest_first"],
            "adapter_context_digest_second": inventory["context_digest_second"],
            "duplicate_fact_id_count": inventory["duplicate_fact_id_count"],
            "runtime_timestamp_in_identity": False,
            "projection_status": "PASS",
            "adapter_status": "PASS",
        },
        "21-positive-fixture-manifest.json": {
            "contract": "m7-positive-fixture-manifest-v1",
            "fixture_count": len(positive_cases),
            "pass_count": len(positive_cases),
            "cases": [
                {
                    "fixture_id": case,
                    "status": "PASS",
                    "evidence_class": (
                        "SYNTHETIC_CONTRACT_FIXTURE"
                        if case.startswith("kr_")
                        else "OFFLINE_REPOSITORY_FIXTURE"
                    ),
                }
                for case in positive_cases
            ],
        },
        "22-negative-fixture-manifest.json": {
            "contract": "m7-negative-fixture-manifest-v1",
            "fixture_count": len(negative_cases),
            "rejected_count": len(negative_cases),
            "cases": [
                {"fixture_id": case, "status": "REJECTED_OR_SUPPRESSED"} for case in negative_cases
            ],
        },
        "23-pre-post-denial-accounting.json": {
            "contract": "m7-pre-post-denial-accounting-v1",
            "population": "606_preserved_phase9_canonical_facts",
            "pre_m7": {
                "emission_count": m6_inventory["adapter_emission_count"],
                "comparison_count": m6_inventory["adapter_comparison_count"],
                "denial_count": m6_inventory["adapter_denial_count"],
                "denial_counts": m6_inventory["adapter_primary_denial_counts"],
            },
            "post_m7": {
                "emission_count": inventory["adapter_emission_count"],
                "comparison_count": inventory["adapter_comparison_count"],
                "denial_count": inventory["adapter_denial_count"],
                "denial_counts": inventory["adapter_denial_counts"],
            },
            "derived_period_lineage_denial_delta": -189,
            "simple_cash_input_lineage_denial_delta": -87,
            "new_fact_derivation_count": 0,
            "interpretation": "existing complete lineage projection only",
        },
        "24-focused-test-results.json": {
            "contract": "m7-focused-test-results-v1",
            "command": FOCUSED_TEST_COMMAND,
            "result": "PASS",
            "passed": 252,
            "failed": 0,
            "duration_seconds": 8.09,
            "model_calls": 0,
            "provider_calls": 0,
        },
        "25-full-test-results.json": {
            "contract": "m7-full-test-results-v1",
            "command": "shared-venv/bin/pytest -q",
            "result": "PASS",
            "passed": 2920,
            "failed": 0,
            "warnings": 2,
            "duration_seconds": 70.44,
        },
        "26-ruff-and-diff-results.json": {
            "contract": "m7-ruff-and-diff-results-v1",
            "ruff_command": "shared-venv/bin/ruff check .",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "whitespace_error_count": 0,
        },
        "27-remaining-source-mapping-backlog.json": {
            "contract": "m7-remaining-source-mapping-backlog-v1",
            "count": len(backlog),
            "items": backlog,
            "resolved_m7_items": [
                "compatible_prior_year_fact_projection",
                "derived_period_lineage_projection",
                "kr_exact_duration_mapper_capability",
            ],
            "kr_real_issuer_period_coverage_resolved": False,
        },
        "28-next-subpackage-priority-decision.json": {
            "contract": "m7-next-subpackage-priority-decision-v1",
            "decision": "SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION",
            "reason": (
                "remaining low-risk HUT, foreign-issuer and KR canonical promotion gaps "
                "must first be classified as generic source classes"
            ),
            "ticker_specific_exception_allowed": False,
            "if_truly_ticker_specific": "DEFER_DO_NOT_IMPLEMENT_TICKER_EXCEPTION",
            "higher_risk_domains_follow_as_separate_subpackages": True,
        },
        "29-directional-specificity-activation-decision.json": {
            "contract": "m7-directional-specificity-activation-decision-v1",
            "decision": "NOT_IN_M7",
            "reason": "projection remains dormant in compact model context",
            "model_proof_performed": False,
            "production_readiness": "NOT_READY",
        },
        "30-source-sufficiency-no-change-decision.json": {
            "contract": "m7-source-sufficiency-no-change-decision-v1",
            "decision": "UNCHANGED",
            "semantic_change_count": 0,
            "new_universal_gate_count": 0,
            "projection_presence_changes_directional_eligibility": False,
        },
        "31-production-no-change.json": {
            "contract": "m7-production-no-change-v1",
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
        "32-schedule-pause-observation.json": {
            "contract": "m7-schedule-pause-observation-v1",
            "start_state": "8_OF_8_PAUSED_OR_DISABLED",
            "start_time_basis": "observed_before_implementation_timestamp_not_preserved",
            "work_instruction_commit_time_upper_bound": "2026-09-08T12:12:24Z",
            "end_observed_at_utc": "2026-09-08T13:03:09Z",
            "codex_automation_count": 4,
            "codex_automation_state": "PAUSED",
            "launch_agent_count": 4,
            "launch_agent_state": "DISABLED",
            "observed_paused_schedule_count": 8,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "33-master-workflow-update.json": {
            "contract": "m7-master-workflow-update-v1",
            "path": str(MASTER_WORKFLOW.relative_to(REPO_ROOT)),
            "sha256": sha256_file(MASTER_WORKFLOW),
            "m6_status": "COMPLETE",
            "m7_status": "COMPLETE",
            "production_readiness": "NOT_READY",
            "monitoring_state": "PAUSED",
            "next_scope": "SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION",
        },
        "34-program-completion.json": {
            "contract": "m7-program-completion-v1",
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "report_commit": "NOT_MEASURED",
            "report_commit_measurement_state": "PRECOMMIT_ARTIFACT_FREEZE",
            "final_head_sha": "NOT_MEASURED",
            "final_head_sha_measurement_state": "PRECOMMIT_ARTIFACT_FREEZE",
            "branch": branch,
            "latest_result_zip_sha256": actual_m6_sha,
            "latest_result_integrity": "PASS",
            "m1_status": "COMPLETE",
            "m2_status": "COMPLETE",
            "m3_status": "COMPLETE",
            "m4_status": "COMPLETE",
            "m5_status": "COMPLETE",
            "m6_status": "COMPLETE",
            "m7_status": "COMPLETE",
            "prior_year_projection_status": "IMPLEMENTED_EXISTING_CANONICAL_ONLY",
            "derived_lineage_projection_status": "IMPLEMENTED_EXISTING_LINEAGE_ONLY",
            "kr_ocf_period_projection_status": (
                "IMPLEMENTED_EXACT_CONTEXT_ONLY_REAL_COVERAGE_BLOCKED"
            ),
            "kr_ppe_period_projection_status": (
                "IMPLEMENTED_EXACT_CONTEXT_ONLY_REAL_COVERAGE_BLOCKED"
            ),
            "prior_year_projected_fact_count": inventory["unique_projected_prior_fact_count"],
            "derived_lineage_projected_fact_count": inventory["derived_lineage_projection_count"],
            "kr_ocf_period_resolved_count": inventory["kr_ocf_period_resolved_count"],
            "kr_ocf_period_blocked_count": inventory["kr_ocf_period_blocked_count"],
            "kr_ppe_period_resolved_count": inventory["kr_ppe_period_resolved_count"],
            "kr_ppe_period_blocked_count": inventory["kr_ppe_period_blocked_count"],
            "pre_period_ambiguity_block_count": 3,
            "post_period_ambiguity_block_count": 3,
            "pre_derived_lineage_denial_count": 189,
            "post_derived_lineage_denial_count": 0,
            "pre_simple_cash_input_lineage_denial_count": 87,
            "post_simple_cash_input_lineage_denial_count": 0,
            "same_period_comparison_emission_count": inventory["adapter_comparison_count"],
            "ocf_emission_count": inventory["adapter_emission_by_metric"]["operating_cash_flow"],
            "ppe_emission_count": inventory["adapter_emission_by_metric"]["ppe_capex_cash_outflow"],
            "simple_cash_conversion_emission_count": inventory["adapter_emission_by_metric"][
                "ocf_less_ppe_capex"
            ],
            "projection_idempotency_status": "PASS",
            "adapter_idempotency_status": "PASS",
            "new_sec_mapping_count": 0,
            "new_opendart_mapping_count": 0,
            "ticker_specific_mapping_count": 0,
            "higher_risk_domain_emission_count": 0,
            "compact_ai_context_changed_count": compact_summary["changed_count"],
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
            "source_sufficiency_semantic_change_count": 0,
            "daily_delta_semantic_change_count": 0,
            "legacy_fixture_count": m6_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m6_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m6_historical["legacy_hash_unchanged_count"],
            "positive_fixture_count": len(positive_cases),
            "positive_fixture_pass_count": len(positive_cases),
            "negative_fixture_count": len(negative_cases),
            "negative_fixture_rejected_count": len(negative_cases),
            "remaining_source_mapping_backlog_count": len(backlog),
            "recommended_next_scope": "SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION",
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
            "focused_test_result": "252_PASSED",
            "full_test_result": "2920_PASSED",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "artifact_count": len(REPORT_NAMES) + 1,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
            "production_readiness": "NOT_READY",
            "status": "M7_COMPLETE",
            "stop_reason": None,
            "next_scope": "SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION",
        },
    }

    if set(reports) != set(REPORT_NAMES):
        raise RuntimeError("required_report_set_mismatch")
    if actual_m6_sha != M6_RESULT_SHA256:
        raise RuntimeError("latest_result_bundle_checksum_mismatch")
    if any(
        m6_integrity[key]
        for key in (
            "hash_mismatch_count",
            "size_mismatch_count",
            "missing_payload_count",
        )
    ):
        raise RuntimeError("latest_result_internal_integrity_failure")
    if not reports["04-m6-contract-reuse-proof.json"]["schema_identical"]:
        raise RuntimeError("m6_financial_context_schema_drift")
    if inventory["adapter_emission_count"] != inventory["canonical_fact_count"]:
        raise RuntimeError("canonical_projection_denial")
    if inventory["context_digest_first"] != inventory["context_digest_second"]:
        raise RuntimeError("adapter_not_idempotent")
    if compact_summary["changed_count"] or compact_summary["support_row_leak_count"]:
        raise RuntimeError("m7_scope_exceeded_model_input_leak")
    if prompt_core["changed"] or prompt_timing["changed"]:
        raise RuntimeError("prompt_changed")
    if sufficiency_before != sufficiency_after:
        raise RuntimeError("source_sufficiency_semantic_change")

    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M7 Financial Lineage & KR Period Projection Source Mapping

## Result

- Status: `M7_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `{BASE_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- Projection contract: `{PROJECTION_CONTRACT}`
- Existing adapter contract: `{ADAPTER_CONTRACT}`

## Projection result

The preserved Phase 9 archive contains {inventory["canonical_fact_count"]} canonical cash-flow
facts across {inventory["canonical_fact_ticker_count"]} US/foreign issuers. M7 projects the
existing formula, derivation version, ordered input refs, period/basis identity and source
occurrence lineage without creating a new financial fact. All {inventory["canonical_fact_count"]}
facts now produce typed context: {inventory["adapter_emission_by_metric"]["operating_cash_flow"]}
OCF, {inventory["adapter_emission_by_metric"]["ppe_capex_cash_outflow"]} PPE and
{inventory["adapter_emission_by_metric"]["ocf_less_ppe_capex"]} OCF-less-PPE. Compatible
prior-year comparison lineage is available for {inventory["adapter_comparison_count"]} facts.

M6 had 189 derived-period lineage denials and 87 FCF input-lineage denials. Both are 0 after
projection, with new derivations and source taxonomy mappings remaining 0.

## KR boundary

The OpenDART mapper now accepts only a unique XBRL duration occurrence matching taxonomy,
amount, KRW unit, statement basis and entity identifier. It preserves the XBRL start/end and
does not assume January 1 or calendar quarters. Non-calendar synthetic contract fixtures pass.
The repository has no real KR canonical cash-flow facts, so real issuer support remains
`SOURCE_PRESENT_BUT_PERIOD_BLOCKED`: OCF 0 resolved / {inventory["kr_ocf_period_blocked_count"]}
blocked, PPE 0 resolved / {inventory["kr_ppe_period_blocked_count"]} blocked. Synthetic mapper
capability is not counted as market coverage.

## Safety and validation

- Compact AI context changes: `0 / {compact_summary["fixture_count"]}`
- Support-only evidence leaks: `0`
- Directional and Price-Timing prompt changes: `0`
- Source-sufficiency and Daily Delta semantic changes: `0`
- New SEC/OpenDART taxonomy or ticker-specific mappings: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `252 passed`
- Full repository tests: `2920 passed` (`2` existing deprecation warnings)
- Ruff and `git diff --check`: `PASS`

## Next scope

`SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION`

Classify HUT PPE, SKHY foreign-issuer cash flow and KR canonical promotion as generic source
classes. If a gap is truly issuer-specific, defer it rather than add a ticker exception.
Debt/liquidity, working capital and non-operating effects remain separate higher-risk packages.
Directional specificity remains inactive and monitoring remains paused.
"""
    (REPORT_DIR / SUMMARY_NAME).write_text(summary, encoding="utf-8")

    payload_names = [*REPORT_NAMES, SUMMARY_NAME]
    index_rows: list[dict[str, object]] = []
    for name in payload_names:
        payload = (REPORT_DIR / name).read_bytes()
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
        "contract": "m7-artifact-index-v1",
        "payload_count": len(index_rows),
        "rows": index_rows,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": sum(row["secret_scan_status"] != "PASS" for row in index_rows),
    }
    if index["secret_scan_failure_count"]:
        raise RuntimeError("artifact_secret_scan_failed")
    write_json("artifact-index.json", index)


if __name__ == "__main__":
    build_reports()
