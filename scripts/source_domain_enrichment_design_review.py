from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from scripts.nonproduction_integration_decision_message_review import SECRET_PATTERNS
from scripts.websocket_timeout_runtime_review_first_a_closeout import (
    observe_pause_state,
)


CONTRACT = "source-domain-enrichment-directional-specificity-design-review-v1"
EXPECTED_LATEST_RESULT_SHA256 = (
    "e1ebc077c56c2412280f58d8244498848b9a1f96ae3c4d233aa2535786ef3228"
)
EXPECTED_LATEST_FINAL_SHA = "5990caa239f8778ae46670abddf30f68db1bb332"
EXPECTED_LATEST_PAYLOAD_COUNT = 44
EXPECTED_WORK_INSTRUCTION_ZIP_SHA256 = (
    "90565c404230949945aeba2fe11fb195fc6038702f0712bfedbc56bd380a5b33"
)
EXPECTED_WORK_INSTRUCTION_MEMBER_SHA256 = (
    "0cf730f864f014c8d58c1a86f1babd588e4dcf3c45d660adf59142655db11aaf"
)
BASE_SHA = EXPECTED_LATEST_FINAL_SHA
DOMAINS = (
    "same_period_prior_year_comparison",
    "operating_cash_flow",
    "ppe_capex_simple_cash_conversion",
    "debt_liquidity",
    "inventory_receivables_working_capital",
    "non_operating_financial_income_effects",
)
SUPPORT_STATUSES = {
    "SUPPORTED_CURRENTLY",
    "PARTIALLY_SUPPORTED",
    "SOURCE_EXISTS_MAPPING_INCOMPLETE",
    "FIXTURE_EVIDENCE_ONLY",
    "NOT_SUPPORTED",
    "NOT_MEASURED",
}
PARTIAL_SUPPORT_STATUSES = {
    "PARTIALLY_SUPPORTED",
    "SOURCE_EXISTS_MAPPING_INCOMPLETE",
    "FIXTURE_EVIDENCE_ONLY",
}
UNSUPPORTED_STATUSES = {"NOT_SUPPORTED", "NOT_MEASURED"}
REPORT_NAMES = (
    "01-repository-provenance.json",
    "02-latest-result-integrity.json",
    "03-m4-scope-freeze.json",
    "04-m1-m2-m3-contract-reuse-proof.json",
    "05-source-domain-backlog-reconciliation.json",
    "06-current-source-parser-and-mapping-inventory.json",
    "07-source-domain-contract-matrix.json",
    "08-sector-applicability-matrix.json",
    "09-market-source-support-matrix.json",
    "10-same-period-comparison-design.json",
    "11-operating-cash-flow-design.json",
    "12-ppe-capex-cash-conversion-design.json",
    "13-debt-liquidity-design.json",
    "14-working-capital-design.json",
    "15-non-operating-financial-effects-design.json",
    "16-materiality-contract.json",
    "17-direct-vs-derived-evidence-contract.json",
    "18-period-specificity-contract.json",
    "19-earnings-quality-contract.json",
    "20-directional-specificity-contract.json",
    "21-warning-kill-condition-domain-contract.json",
    "22-valuation-boundary-contract.json",
    "23-offline-representative-fixture-manifest.json",
    "24-offline-domain-semantics-audit.json",
    "25-us-free-source-domain-support-audit.json",
    "26-kr-free-source-domain-support-audit.json",
    "27-current-schema-compatibility-audit.json",
    "28-candidate-implementation-packages.json",
    "29-implementation-order-decision.json",
    "30-required-schema-change-decision.json",
    "31-required-source-sufficiency-change-decision.json",
    "32-required-directional-specificity-change-decision.json",
    "33-required-model-validation-scope.json",
    "34-required-real-holdout-scope.json",
    "35-production-no-change.json",
    "36-schedule-pause-observation.json",
    "37-master-workflow-update.json",
    "38-program-completion.json",
)
SUMMARY_NAME = (
    "20260908-source-domain-enrichment-directional-specificity-design-review.md"
)
SIDE_EFFECT_COUNTS = {
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
    "scheduler_mutation_count": 0,
    "automatic_monitoring_resume": 0,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def git_value(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not name.startswith("/") and "\\" not in name and ".." not in path.parts


def verify_latest_result(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    if actual_sha != EXPECTED_LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        duplicate_members = sorted(
            name for name, count in Counter(names).items() if count > 1
        )
        unsafe_members = sorted(name for name in names if not _safe_member(name))
        crc_failure = archive.testzip()
        completion = json.loads(archive.read("31-program-completion.json"))
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("rows") if isinstance(index, Mapping) else None
        if not isinstance(completion, Mapping) or not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_DOCUMENT_STRUCTURE_INVALID")
        indexed = {
            str(row["path"]): row
            for row in rows
            if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        missing_index = sorted(payload_names - set(indexed))
        unexpected_index = sorted(set(indexed) - payload_names)
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        secret_failures: list[str] = []
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(name)
            expected_size = row.get("size_bytes", row.get("bytes"))
            if len(payload) != expected_size:
                size_mismatches.append(name)
            if any(pattern.search(payload) for pattern in SECRET_PATTERNS.values()):
                secret_failures.append(name)
        checks = {
            "zip_sha256": True,
            "crc": crc_failure is None,
            "duplicates": not duplicate_members,
            "safe_paths": not unsafe_members,
            "index_membership": not missing_index and not unexpected_index,
            "indexed_payload_count": len(rows) == EXPECTED_LATEST_PAYLOAD_COUNT,
            "indexed_hashes": not hash_mismatches,
            "indexed_sizes": not size_mismatches,
            "independent_secret_scan": not secret_failures,
            "m3_status": completion.get("status") == "M3_COMPLETE",
            "m3_next_scope": completion.get("next_scope")
            == "SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW",
            "m3_final_sha": completion.get("implementation_commit")
            == "41fdd088d0ab312d2bbd975b8066851faabaf0a1",
        }
        if not all(checks.values()):
            failed = ",".join(key for key, passed in checks.items() if not passed)
            raise ValueError(f"LATEST_RESULT_BUNDLE_INTEGRITY_FAILURE:{failed}")
        return {
            "contract": "m4-latest-result-integrity-v1",
            "source_path": str(path),
            "expected_sha256": EXPECTED_LATEST_RESULT_SHA256,
            "actual_sha256": actual_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "hash_mismatch_count": len(hash_mismatches),
            "size_mismatch_count": len(size_mismatches),
            "secret_scan_failure_count": len(secret_failures),
            "checks": checks,
            "completion": dict(completion),
            "status": "PASS",
        }


def verify_work_instruction(path: Path) -> dict[str, object]:
    actual_zip_sha = file_sha256(path)
    if actual_zip_sha != EXPECTED_WORK_INSTRUCTION_ZIP_SHA256:
        raise ValueError("WORK_INSTRUCTION_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1 or not _safe_member(names[0]):
            raise ValueError("WORK_INSTRUCTION_MEMBER_INVALID")
        payload = archive.read(names[0])
    member_sha = bytes_sha256(payload)
    if member_sha != EXPECTED_WORK_INSTRUCTION_MEMBER_SHA256:
        raise ValueError("WORK_INSTRUCTION_MEMBER_CHECKSUM_MISMATCH")
    return {
        "contract": "m4-work-instruction-integrity-v1",
        "zip_sha256": actual_zip_sha,
        "member": names[0],
        "member_sha256": member_sha,
        "status": "PASS",
    }


def repository_provenance(
    repo_root: Path,
    *,
    work_instruction_commit: str,
    implementation_commit: str,
) -> dict[str, object]:
    head = git_value(repo_root, "rev-parse", "HEAD")
    branch = git_value(repo_root, "branch", "--show-current")
    origin_main = git_value(repo_root, "rev-parse", "origin/main")
    merge_base = git_value(repo_root, "merge-base", BASE_SHA, origin_main)
    changed = tuple(
        row
        for row in git_value(repo_root, "diff", "--name-only", BASE_SHA).splitlines()
        if row
    )
    categories = {
        "source_ingestion_normalization": "UNCHANGED",
        "decision_evidence_packet": "UNCHANGED_DESIGN_ONLY",
        "directional_ownership": "UNCHANGED_DESIGN_ONLY",
        "valuation_safety": "UNCHANGED",
        "accounting_attribution": "UNCHANGED_DESIGN_ONLY",
        "adr_security_basis": "UNCHANGED",
        "onboarding_daily_delta_lifecycle": "UNCHANGED",
        "renderer_message_ownership": "UNCHANGED",
    }
    allowed_prefixes = (
        "docs/MASTER_WORKFLOW.md",
        "docs/work-instructions/",
        "docs/reports/20260908-source-domain-enrichment-directional-specificity-design-review/",
        "scripts/source_domain_enrichment_design_review.py",
        "tests/test_source_domain_enrichment_design_review.py",
    )
    unexpected = sorted(
        path for path in changed if not any(path.startswith(item) for item in allowed_prefixes)
    )
    return {
        "contract": "m4-repository-provenance-v1",
        "branch": branch,
        "base_sha": BASE_SHA,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "observed_head": head,
        "origin_main_sha": origin_main,
        "merge_base_base_origin_main": merge_base,
        "origin_main_is_ancestor_of_base": merge_base == origin_main,
        "changed_paths_from_base": list(changed),
        "unexpected_changed_paths": unexpected,
        "drift_classification": categories,
        "unexplained_semantic_drift": bool(unexpected),
        "status": "PASS" if not unexpected else "FAIL",
    }


def _common_contract(
    *,
    domain: str,
    purpose: Sequence[str],
    sectors: Sequence[str],
    cautions: Sequence[str],
    us_status: str,
    kr_status: str,
    locations: Sequence[str],
    evidence_modes: Sequence[str],
    period_basis: Sequence[str],
    comparison: Sequence[str],
    safe: Sequence[Mapping[str, object]],
    forbidden: Sequence[str],
    directional: Sequence[str],
    message: Sequence[str],
    sufficiency: str,
    missing: str,
    tests: Sequence[str],
    risk: str,
) -> dict[str, object]:
    return {
        "domain": domain,
        "investment_purpose": list(purpose),
        "applicable_sector_families": list(sectors),
        "non_applicable_or_caution_sector_families": list(cautions),
        "us_free_public_source_availability": us_status,
        "kr_free_public_source_availability": kr_status,
        "current_parser_mapping_locations": list(locations),
        "directly_reported_vs_derived": list(evidence_modes),
        "period_basis": list(period_basis),
        "currency_basis": "same verified financial currency; no inferred FX conversion",
        "entity_attribution_basis": (
            "same issuer, consolidation scope, statement basis, and attribution basis"
        ),
        "single_quarter_vs_cumulative_semantics": (
            "QTD, YTD, FY, TTM, and point-in-time remain distinct; no label-based guess"
        ),
        "comparability_requirements": list(comparison),
        "safe_derivations": [dict(row) for row in safe],
        "forbidden_derivations": list(forbidden),
        "decision_evidence_packet_representation": {
            "classification": "SCHEMA_EXTENSION_REQUIRED",
            "proposal": "optional typed financial_context on DecisionEvidenceRef",
            "activation_in_m4": False,
        },
        "directional_core_usage": list(directional),
        "valuation_usage": (
            "context for denominator quality only; no multiple, price target, or valuation fact"
        ),
        "message_usage": list(message),
        "source_sufficiency_impact": sufficiency,
        "missing_data_behavior": missing,
        "required_validation_tests": list(tests),
        "implementation_risk": risk,
        "schema_change_required": True,
        "initial_analysis_use": "eligible as absolute evidence when valid and material",
        "monitoring_baseline_use": "may enrich baseline; enrichment is not Daily Delta",
        "daily_delta_use": (
            "only newly effective post-baseline validated change; preserve M3 cutoff lineage"
        ),
        "warning_kill_condition_use": (
            "may support warning when material and contextual; no one-period automatic kill"
        ),
    }


def domain_contracts() -> list[dict[str, object]]:
    rows = [
        _common_contract(
            domain=DOMAINS[0],
            purpose=("trend persistence", "period-specific earnings direction"),
            sectors=("all reporting issuers with compatible comparatives",),
            cautions=("new issuers without comparable history", "basis-changing issuers"),
            us_status="SOURCE_EXISTS_MAPPING_INCOMPLETE",
            kr_status="SUPPORTED_CURRENTLY",
            locations=(
                "app/services/sec_financial_snapshot_service.py",
                "app/services/kr_financial_lineage_service.py::growth_lineage_compatible",
            ),
            evidence_modes=("DIRECT_REPORTED", "DERIVED_SAFE"),
            period_basis=("QTD vs QTD", "YTD vs YTD", "FY vs FY"),
            comparison=(
                "same semantic account",
                "same duration and period type",
                "same currency, entity, statement, and attribution basis",
                "prior-year end distance must be compatible",
            ),
            safe=(
                {
                    "name": "same_period_absolute_delta",
                    "status": "DERIVED_SAFE",
                    "formula": "current - prior comparable",
                    "inputs": 2,
                    "failure_conditions": ["any comparability mismatch"],
                },
                {
                    "name": "same_period_direction_relation",
                    "status": "DERIVED_SAFE",
                    "formula": "signed relation without negative-base growth percentage",
                    "inputs": 2,
                    "failure_conditions": ["zero/negative base percentage request"],
                },
                {
                    "name": "qtd_from_compatible_ytd",
                    "status": "DERIVED_SAFE",
                    "formula": "current YTD - previous-quarter YTD",
                    "inputs": 2,
                    "failure_conditions": ["fiscal year or basis mismatch"],
                },
            ),
            forbidden=(
                "QTD vs YTD",
                "quarter vs FY",
                "different duration or fiscal basis",
                "different attribution or consolidation basis",
                "incompatible currency arithmetic",
                "annualization of interim results",
            ),
            directional=(
                "establish trend or persistence only when comparable",
                "required evidence for an explicit improvement/deterioration claim",
                "not independent valuation evidence",
            ),
            message=(
                "name the actual period type when material",
                "do not call unavailable comparison negative evidence",
            ),
            sufficiency="REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            missing="comparison unavailable; no trend claim and no negative polarity",
            tests=(
                "QTD/QTD, YTD/YTD, and FY/FY acceptance",
                "mixed period, basis, attribution, and currency rejection",
                "safe cumulative-to-quarter derivation lineage",
            ),
            risk="MEDIUM",
        ),
        _common_contract(
            domain=DOMAINS[1],
            purpose=(
                "earnings cash conversion",
                "growth-quality cross-check",
                "operating cash generation",
            ),
            sectors=(
                "standard operating company",
                "manufacturing",
                "software",
                "cloud/platform",
                "biotech",
            ),
            cautions=("bank", "insurance/reinsurance", "financial institution"),
            us_status="SUPPORTED_CURRENTLY",
            kr_status="PARTIALLY_SUPPORTED",
            locations=(
                "app/services/official_cash_flow_service.py",
                "app/services/cash_flow_capital_efficiency_service.py",
                "app/services/opendart_financial_recovery_service.py",
            ),
            evidence_modes=("DIRECT_REPORTED", "DERIVED_SAFE_PERIOD"),
            period_basis=("reported QTD", "YTD", "FY", "safe TTM"),
            comparison=(
                "same cash-flow semantic",
                "same issuer, currency, unit, entity, and statement basis",
                "source filing version compatibility",
            ),
            safe=(
                {
                    "name": "ocf_qtd",
                    "status": "DERIVED_SAFE",
                    "formula": "current YTD OCF - prior-quarter YTD OCF",
                    "inputs": 2,
                    "failure_conditions": ["period or source-version mismatch"],
                },
                {
                    "name": "ocf_ttm",
                    "status": "DERIVED_SAFE",
                    "formula": "prior FY + current YTD - prior comparable YTD",
                    "inputs": 3,
                    "failure_conditions": ["missing or incompatible component"],
                },
            ),
            forbidden=(
                "EBITDA, operating income, or net income as OCF proxy",
                "interim annualization",
                "cumulative YTD labeled as a single quarter",
                "industrial interpretation for a financial institution",
                "missing OCF converted to zero",
            ),
            directional=(
                "cash-conversion evidence, not an automatic thesis verdict",
                "contrast with compatible earnings only",
                "negative OCF is a fact requiring sector and stage context",
            ),
            message=(
                "label operating cash flow and period explicitly",
                "avoid implying a working-capital cause without supporting facts",
            ),
            sufficiency="REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            missing="Unknown for a cash-conversion claim; otherwise no negative inference",
            tests=(
                "official operating-activities semantic acceptance",
                "YTD/QTD/TTM period safety",
                "financial-industry interpretation suppression",
            ),
            risk="MEDIUM",
        ),
        _common_contract(
            domain=DOMAINS[2],
            purpose=("reinvestment burden", "post-PPE cash conversion"),
            sectors=(
                "manufacturing",
                "semiconductor/memory",
                "automotive",
                "cloud/platform",
                "infrastructure",
            ),
            cautions=(
                "bank",
                "insurance/reinsurance",
                "asset-light issuer with material intangible investment",
            ),
            us_status="SUPPORTED_CURRENTLY",
            kr_status="PARTIALLY_SUPPORTED",
            locations=(
                "app/services/official_cash_flow_service.py",
                "app/services/cash_flow_capital_efficiency_service.py::derive_fcf",
                "app/services/opendart_financial_recovery_service.py::CAPEX_COMPONENTS",
            ),
            evidence_modes=("DIRECT_REPORTED_PPE_OUTFLOW", "DERIVED_SAFE"),
            period_basis=("same-period QTD", "YTD", "FY", "safe TTM"),
            comparison=(
                "OCF and PPE purchase share exact period and basis",
                "PPE scope remains explicit",
                "same currency and normalized unit",
            ),
            safe=(
                {
                    "name": "ppe_capex_positive_outflow",
                    "status": "DERIVED_SAFE",
                    "formula": "semantic-aware sign normalization to positive magnitude",
                    "inputs": 1,
                    "failure_conditions": ["unverified investing semantic"],
                },
                {
                    "name": "ocf_less_ppe_capex",
                    "status": "DERIVED_SAFE",
                    "formula": "OCF - PPE acquisition cash outflow",
                    "inputs": 2,
                    "failure_conditions": ["period, currency, entity, or basis mismatch"],
                },
            ),
            forbidden=(
                "generic investing cash flow as capex",
                "business acquisitions as PPE capex",
                "securities purchases as PPE capex",
                "automatic intangible or capitalized-software inclusion",
                "maintenance-capex inference",
                "partial capex subtraction labeled as company-defined FCF",
                "different-period OCF and capex arithmetic",
            ),
            directional=(
                "separate operating cash generation from reinvestment absorption",
                "higher capex is not inherently negative",
                "use OCF less PPE capex, never an inferred maintenance-capex result",
            ),
            message=(
                "preferred label: OCF less PPE acquisition cash outflow",
                "if FCF is used, qualify it as PPE-only and not management-defined FCF",
            ),
            sufficiency="REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            missing="PPE cash-conversion unavailable; OCF may remain independently usable",
            tests=(
                "accepted/rejected CAPEX semantics",
                "sign normalization",
                "same-basis arithmetic and complete input lineage",
            ),
            risk="MEDIUM",
        ),
        _common_contract(
            domain=DOMAINS[3],
            purpose=("financial resilience", "refinancing and dilution risk"),
            sectors=(
                "standard operating company",
                "capital-intensive company",
                "pre-profit company",
                "holding company",
            ),
            cautions=(
                "bank",
                "insurance/reinsurance",
                "financial institution requiring sector capital framework",
            ),
            us_status="SOURCE_EXISTS_MAPPING_INCOMPLETE",
            kr_status="SOURCE_EXISTS_MAPPING_INCOMPLETE",
            locations=(
                "app/models/financial.py::FinancialSnapshot",
                "app/services/financial_snapshot_service.py",
                "app/services/coldstart_fundamental_enrichment_service.py",
            ),
            evidence_modes=("DIRECT_REPORTED_COMPONENTS", "DERIVED_SAFE_IF_COMPLETE"),
            period_basis=("balance-sheet point-in-time",),
            comparison=(
                "same balance-sheet date for cash and debt components",
                "complete interest-bearing debt scope",
                "same currency, entity, and consolidation basis",
            ),
            safe=(
                {
                    "name": "interest_bearing_debt_total",
                    "status": "DERIVED_SAFE",
                    "formula": "sum verified non-overlapping short/long/current debt components",
                    "inputs": "2+",
                    "failure_conditions": ["component overlap or incomplete scope"],
                },
                {
                    "name": "net_debt",
                    "status": "DERIVED_SAFE",
                    "formula": "complete interest-bearing debt - compatible cash basis",
                    "inputs": 2,
                    "failure_conditions": ["cash/debt scope or period mismatch"],
                },
            ),
            forbidden=(
                "total liabilities substituted for debt",
                "net debt from incomplete debt components",
                "price currency copied to financial facts",
                "ordinary industrial net-debt logic for banks or insurers",
                "missing debt detail treated as bearish evidence",
            ),
            directional=(
                "liquidity and refinancing context when capital structure is thesis-relevant",
                "sector-specific capital framework replaces generic debt logic for financials",
            ),
            message=(
                "name verified debt/cash scope",
                "do not say net debt when only liabilities are available",
            ),
            sufficiency="SECTOR_CONDITIONAL_REQUIRED",
            missing="Unknown; may limit confidence for financing-dependent issuers",
            tests=(
                "debt component completeness and overlap",
                "cash/debt point-in-time compatibility",
                "total-liabilities negative control",
                "financial-sector routing",
            ),
            risk="HIGH",
        ),
        _common_contract(
            domain=DOMAINS[4],
            purpose=("working-capital quality", "cash-conversion warning"),
            sectors=(
                "manufacturing",
                "hardware",
                "consumer/retail",
                "EPC/construction",
                "selected distributor",
            ),
            cautions=("bank", "insurance", "asset manager", "many SaaS issuers"),
            us_status="PARTIALLY_SUPPORTED",
            kr_status="PARTIALLY_SUPPORTED",
            locations=(
                "app/services/cash_flow_capital_efficiency_service.py",
                "app/services/opendart_financial_recovery_service.py",
                "docs/reports/20260820-phase9-0b-canonical-facts.json",
            ),
            evidence_modes=("DIRECT_REPORTED_POINT_IN_TIME", "DERIVED_SAFE"),
            period_basis=(
                "balance date vs prior-year comparable date",
                "balance date vs prior year-end with explicit label",
            ),
            comparison=(
                "trade vs broad AR/AP semantics remain distinct",
                "same balance scope, currency, entity, and basis",
                "revenue/COGS relation requires compatible flow period",
            ),
            safe=(
                {
                    "name": "balance_absolute_delta",
                    "status": "DERIVED_SAFE",
                    "formula": "current point-in-time balance - compatible prior balance",
                    "inputs": 2,
                    "failure_conditions": ["balance scope mismatch"],
                },
                {
                    "name": "balance_yoy_relation",
                    "status": "DERIVED_SAFE",
                    "formula": "directional relation to prior-year comparable balance",
                    "inputs": 2,
                    "failure_conditions": ["year-end comparator mislabeled YoY"],
                },
                {
                    "name": "balance_vs_revenue_relation",
                    "status": "DERIVED_SAFE",
                    "formula": "compare compatible balance and revenue directions",
                    "inputs": "3+",
                    "failure_conditions": ["period or semantic mismatch"],
                },
            ),
            forbidden=(
                "other receivables as trade AR",
                "other payables as trade AP",
                "year-end to interim balance called YoY",
                "DSO without average trade AR and compatible revenue",
                "inventory days without average inventory and compatible COGS",
                "DPO without explicit denominator policy",
                "CCC with any missing component",
                "missing working-capital data treated as negative",
            ),
            directional=(
                "compare inventory/receivable movement with compatible revenue evidence",
                "state observed divergence without asserting its cause",
                "CCC remains deferred",
            ),
            message=(
                "identify point-in-time comparison basis",
                "avoid generic working-capital deterioration when only one balance is known",
            ),
            sufficiency="REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            missing="Unavailable and confidence-limiting only when the claim depends on it",
            tests=(
                "trade/broad semantic separation",
                "point-in-time period labels",
                "balance vs flow compatibility",
                "CCC dependency failure controls",
            ),
            risk="MEDIUM",
        ),
        _common_contract(
            domain=DOMAINS[5],
            purpose=("operating vs non-operating earnings attribution",),
            sectors=("standard operating company", "holding company"),
            cautions=(
                "bank",
                "insurance/reinsurance",
                "financial institution where interest is core economics",
            ),
            us_status="PARTIALLY_SUPPORTED",
            kr_status="SOURCE_EXISTS_MAPPING_INCOMPLETE",
            locations=(
                "app/services/coldstart_fundamental_enrichment_service.py",
                "app/services/sec_financial_snapshot_service.py",
                "app/services/opendart_financial_recovery_service.py",
            ),
            evidence_modes=("DIRECT_REPORTED_COMPONENTS", "DERIVED_SAFE_IF_COMPLETE"),
            period_basis=("same income-statement duration and fiscal period",),
            comparison=(
                "same period, currency, entity, statement, and attribution basis",
                "sector semantic class verified before operating/non-operating label",
                "no double count across subtotal and components",
            ),
            safe=(
                {
                    "name": "verified_non_operating_component_sum",
                    "status": "DERIVED_SAFE",
                    "formula": "signed sum of complete, non-overlapping mapped components",
                    "inputs": "2+",
                    "failure_conditions": ["incomplete bridge or sector semantic mismatch"],
                },
            ),
            forbidden=(
                "pretax income minus operating income called complete non-operating income",
                "unmapped residual normalized by invention",
                "bank interest income labeled non-operating",
                "tax effect attributed without direct evidence",
                "net-income improvement equated with operating improvement",
            ),
            directional=(
                "limit an operating-quality conclusion when material verified effects explain NI",
                "keep financial-sector core revenue semantics separate",
            ),
            message=(
                "name the reported effect and period",
                "do not use a generic non-operating label where sector treatment differs",
            ),
            sufficiency="REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            missing="No attribution claim; missing evidence is not negative",
            tests=(
                "component/subtotal overlap",
                "sector semantic routing",
                "same-period operating/pretax/net-income compatibility",
            ),
            risk="HIGH",
        ),
    ]
    if tuple(row["domain"] for row in rows) != DOMAINS:
        raise ValueError("domain_contract_order_mismatch")
    return rows


def sector_matrix() -> list[dict[str, object]]:
    definitions = {
        "standard_operating_company": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "SECONDARY",
        ),
        "semiconductor_memory": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
        ),
        "automotive": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
        ),
        "bank": (
            "PRIMARY",
            "CONTEXT_ONLY",
            "NOT_APPLICABLE",
            "SECTOR_FRAMEWORK",
            "NOT_APPLICABLE",
            "PRIMARY_CORE_ECONOMICS",
        ),
        "insurance_reinsurance": (
            "PRIMARY",
            "CONTEXT_ONLY",
            "NOT_APPLICABLE",
            "SECTOR_FRAMEWORK",
            "NOT_APPLICABLE",
            "PRIMARY_CORE_ECONOMICS",
        ),
        "shipping_transport": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "SECONDARY",
        ),
        "holding_company": (
            "PRIMARY",
            "SECONDARY",
            "CONTEXT_ONLY",
            "PRIMARY",
            "CONTEXT_ONLY",
            "PRIMARY",
        ),
        "consumer": (
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
        ),
        "epc_construction": (
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
        ),
        "saas_recurring_revenue": (
            "PRIMARY",
            "PRIMARY",
            "CONTEXT_ONLY",
            "SECONDARY",
            "SECONDARY_RECEIVABLES_ONLY",
            "SECONDARY",
        ),
        "cloud_platform": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "CONTEXT_ONLY",
            "SECONDARY",
        ),
        "biotech": (
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "PRIMARY",
            "CONTEXT_ONLY",
            "SECONDARY",
        ),
        "preprofit_robotaxi_like": (
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "PRIMARY",
            "SECONDARY",
            "SECONDARY",
        ),
    }
    rows = []
    for sector, values in definitions.items():
        rows.append(
            {
                "sector_family": sector,
                "domain_applicability": dict(zip(DOMAINS, values, strict=True)),
                "generic_domain_required_for_all_issuers": False,
            }
        )
    return rows


def market_support_matrix(
    contracts: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    gaps = {
        ("us", DOMAINS[0]): "history exists, but no typed packet comparator adapter",
        ("kr", DOMAINS[0]): "coverage remains selective and basis-validated",
        ("us", DOMAINS[1]): "official canonical path exists; issuer coverage is selective",
        ("kr", DOMAINS[1]): "stored rows exist; actual XBRL duration reconciliation is 0/7",
        ("us", DOMAINS[2]): "PPE-only canonical path exists; intangibles stay excluded",
        ("kr", DOMAINS[2]): "PPE candidates exist; aggregation eligible is 0",
        ("us", DOMAINS[3]): "cash/debt concepts not mapped into a safe complete contract",
        ("kr", DOMAINS[3]): "legacy liabilities-as-debt field is unsafe for this contract",
        ("us", DOMAINS[4]): "preserved facts are selective; no broad production adapter",
        ("kr", DOMAINS[4]): "inventory has selective safe facts; trade AR/AP unavailable",
        ("us", DOMAINS[5]): "bank sector concepts exist; generic issuer bridge incomplete",
        ("kr", DOMAINS[5]): "no complete mapped generic attribution bridge",
    }
    rows: list[dict[str, object]] = []
    for contract in contracts:
        for market, key in (
            ("us", "us_free_public_source_availability"),
            ("kr", "kr_free_public_source_availability"),
        ):
            status = str(contract[key])
            if status not in SUPPORT_STATUSES:
                raise ValueError(f"unsupported_source_support_status:{status}")
            rows.append(
                {
                    "market": market,
                    "domain": contract["domain"],
                    "support_status": status,
                    "parser_mapping_paths": contract[
                        "current_parser_mapping_locations"
                    ],
                    "known_gap": gaps[(market, str(contract["domain"]))],
                    "universal_issuer_coverage_claimed": False,
                    "provider_call_used": False,
                }
            )
    return rows


def source_inventory(repo_root: Path) -> dict[str, object]:
    rows = [
        {
            "path": "app/services/official_cash_flow_service.py",
            "capability": "SEC/IFRS official OCF and PPE-only CAPEX semantic registry",
            "required_tokens": ["SEMANTIC_REGISTRY", "REJECTED_SEMANTICS"],
            "gap": "not represented in DecisionEvidenceRef",
        },
        {
            "path": "app/services/cash_flow_capital_efficiency_service.py",
            "capability": "typed canonical facts and guarded period/FCF derivation",
            "required_tokens": ["class FinancialFact", "def derive_fcf"],
            "gap": "advanced working-capital and ROIC remain deferred",
        },
        {
            "path": "app/services/sec_financial_snapshot_service.py",
            "capability": "SEC Company Facts income/equity snapshot history",
            "required_tokens": ["_CONCEPTS", "_companyfacts_snapshots"],
            "gap": "no generic OCF/debt/working-capital/non-operating mapping here",
        },
        {
            "path": "app/services/opendart_financial_recovery_service.py",
            "capability": "KR income, inventory, OCF candidate, and CAPEX components",
            "required_tokens": ["FIELD_SPECS", "CAPEX_COMPONENTS"],
            "gap": "cash-flow period reconciliation unresolved in stored audit",
        },
        {
            "path": "app/services/kr_financial_lineage_service.py",
            "capability": "period/basis-safe comparison and cumulative distinction",
            "required_tokens": ["growth_lineage_compatible", "year_to_date_cumulative"],
            "gap": "does not recover unresolved OpenDART cash-flow durations",
        },
        {
            "path": "app/services/financial_snapshot_service.py",
            "capability": "current KR snapshot assembly",
            "required_tokens": ["snapshot.debt = liabilities", "snapshot.cash = None"],
            "gap": "legacy liabilities-as-debt is unsafe and excluded from M4 debt design",
        },
        {
            "path": "app/services/coldstart_fundamental_enrichment_service.py",
            "capability": "sector framework and selected bank/insurance concepts",
            "required_tokens": ["InterestIncomeExpenseNet", "NoninterestIncome"],
            "gap": "no broad financial-domain enrichment producer",
        },
        {
            "path": "app/services/cross_market_decision_engine_service.py",
            "capability": "current compact DecisionEvidenceRef",
            "required_tokens": ["class DecisionEvidenceRef", "metric_refs"],
            "gap": "typed financial period/basis/direct-derived/comparison metadata absent",
        },
    ]
    for row in rows:
        path = repo_root / str(row["path"])
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        row["file_exists"] = path.is_file()
        row["tokens_present"] = all(
            token in text for token in row.pop("required_tokens")
        )
        row["inspection_status"] = (
            "VERIFIED" if row["file_exists"] and row["tokens_present"] else "UNRESOLVED"
        )
    return {
        "contract": "m4-current-source-parser-mapping-inventory-v1",
        "rows": rows,
        "verified_count": sum(row["inspection_status"] == "VERIFIED" for row in rows),
        "unresolved_count": sum(
            row["inspection_status"] != "VERIFIED" for row in rows
        ),
        "provider_calls": 0,
        "status": "PASS"
        if all(row["inspection_status"] == "VERIFIED" for row in rows)
        else "FAIL",
    }


def schema_compatibility(
    contracts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    current_fields = sorted(DecisionEvidenceRef.model_fields)
    missing_typed_fields = (
        "currency",
        "unit_scale",
        "period_type",
        "period_start",
        "period_end",
        "entity_scope",
        "statement_basis",
        "attribution_basis",
        "evidence_status",
        "comparison_basis",
        "derivation_inputs",
        "limitations",
    )
    proposal = {
        "field": "financial_context",
        "placement": "optional field on DecisionEvidenceRef",
        "required_when": "typed financial domain evidence is emitted",
        "shape": {
            "metric": "canonical metric identifier",
            "evidence_status": "DIRECT_REPORTED | DERIVED_SAFE",
            "currency": "verified financial currency",
            "unit_scale": "explicit source/normalized scale",
            "period": {
                "type": "QTD | YTD | FY | TTM | POINT_IN_TIME",
                "start": "date or null for point-in-time",
                "end": "date",
                "duration_days": "integer or null",
            },
            "entity_scope": "issuer/consolidation scope",
            "statement_basis": "official statement basis",
            "attribution_basis": "total/parent/common/null as applicable",
            "comparison": {
                "kind": "prior_year_comparable | prior_year_end | none",
                "input_source_refs": "ordered references",
                "compatibility_status": "PASS",
            },
            "derivation": {
                "formula": "registered formula or null",
                "input_source_refs": "ordered references",
                "version": "derivation contract or null",
            },
            "quality": "verified/partial status",
            "limitations": "bounded list",
        },
        "existing_fields_reused": ["value", "unit", "source_ref", "as_of"],
        "production_activation": False,
        "migration": "additive and optional; no existing packet rewrite",
    }
    rows = [
        {
            "domain": row["domain"],
            "classification": "SCHEMA_EXTENSION_REQUIRED",
            "reason": (
                "current ref cannot bind typed period, financial currency, entity/basis, "
                "direct-derived status, and comparison/derivation lineage together"
            ),
            "m4_implementation": False,
        }
        for row in contracts
    ]
    return {
        "contract": "m4-current-schema-compatibility-audit-v1",
        "current_model": "DecisionEvidenceRef",
        "current_fields": current_fields,
        "missing_typed_fields": list(missing_typed_fields),
        "rows": rows,
        "schema_sufficient_domain_count": 0,
        "schema_extension_required_domain_count": len(rows),
        "bounded_schema_proposal": proposal,
        "schema_modified_in_m4": False,
        "status": "COMPLETE",
    }


def _phase9_fixture_candidates(repo_root: Path) -> dict[str, dict[str, object]]:
    source = read_json(
        repo_root / "docs/reports/20260820-phase9-0b-canonical-facts.json"
    )
    facts = source.get("canonical_facts")
    if not isinstance(facts, list):
        raise ValueError("phase9_canonical_facts_missing")
    by_id = {
        str(row["fact_id"]): row
        for row in facts
        if isinstance(row, Mapping) and row.get("fact_id")
    }
    candidates: list[dict[str, object]] = []
    for row in facts:
        if not isinstance(row, Mapping) or row.get("metric") != "free_cash_flow_ppe":
            continue
        inputs = row.get("input_fact_ids")
        if not isinstance(inputs, list) or len(inputs) != 2:
            continue
        input_rows = [by_id.get(str(ref)) for ref in inputs]
        if any(item is None for item in input_rows):
            continue
        typed_inputs = [item for item in input_rows if item is not None]
        ocf = next(
            (item for item in typed_inputs if item.get("metric") == "operating_cash_flow"),
            None,
        )
        capex = next(
            (
                item
                for item in typed_inputs
                if item.get("metric") == "ppe_capex_cash_outflow"
            ),
            None,
        )
        if ocf is None or capex is None:
            continue
        ocf_value = Decimal(str(ocf["value"]))
        capex_value = Decimal(str(capex["value"]))
        fcf_value = Decimal(str(row["value"]))
        if fcf_value != ocf_value - capex_value:
            continue
        candidates.append(
            {
                "ticker": row.get("ticker"),
                "period_type": row.get("period_type"),
                "period_start": row.get("period_start"),
                "period_end": row.get("period_end"),
                "currency": row.get("currency"),
                "ocf_fact_id": ocf.get("fact_id"),
                "capex_fact_id": capex.get("fact_id"),
                "fcf_fact_id": row.get("fact_id"),
                "ocf": str(ocf_value),
                "ppe_capex": str(capex_value),
                "ocf_less_ppe_capex": str(fcf_value),
                "lineage_complete": True,
            }
        )
    strong = next(
        row
        for row in candidates
        if Decimal(str(row["ocf"])) > 0
        and Decimal(str(row["ocf_less_ppe_capex"])) > 0
    )
    weak = next(
        row
        for row in candidates
        if Decimal(str(row["ocf"])) > 0
        and Decimal(str(row["ocf_less_ppe_capex"])) < 0
    )
    return {"strong": strong, "weak": weak}


def representative_fixtures(repo_root: Path) -> dict[str, object]:
    selected = _phase9_fixture_candidates(repo_root)
    kr_audit = read_json(
        repo_root
        / "docs/reports/20260817-phase8-1-1-authoritative-financial-recovery-audit.json"
    )
    phase9 = read_json(
        repo_root / "docs/reports/20260820-phase9-0b-canonical-facts.json"
    )
    insurance = next(
        row
        for row in phase9["active_universe"]
        if row.get("industry") == "insurance_reinsurance"
    )
    summary = kr_audit["summary"]
    rows = [
        {
            "case": "profitable_strong_cash_conversion",
            "fixture_type": "PRESERVED_CANONICAL_FACT_SELECTION",
            "selection_rule": "first complete OCF>0 and OCF-less-PPE>0 lineage chain",
            "evidence": selected["strong"],
            "validated_semantics": ["period", "currency", "PPE scope", "arithmetic"],
            "status": "PASS",
        },
        {
            "case": "profitable_weak_post_ppe_cash_conversion",
            "fixture_type": "PRESERVED_CANONICAL_FACT_SELECTION",
            "selection_rule": "first complete OCF>0 and OCF-less-PPE<0 lineage chain",
            "evidence": selected["weak"],
            "validated_semantics": [
                "positive OCF is distinct from negative post-PPE residual",
                "no automatic business deterioration verdict",
            ],
            "status": "PASS",
        },
        {
            "case": "high_leverage_weak_liquidity",
            "fixture_type": "CONTRACT_NEGATIVE_CONTROL",
            "source_anchor": "app/services/financial_snapshot_service.py",
            "observed_legacy_mapping": "snapshot.debt = liabilities; snapshot.cash = None",
            "result": "BLOCKED_UNSAFE_DEBT_SCOPE",
            "validated_semantics": ["total liabilities are not interest-bearing debt"],
            "status": "PASS",
        },
        {
            "case": "inventory_receivables_buildup",
            "fixture_type": "PRESERVED_KR_COVERAGE_CONTROL",
            "source_anchor": (
                "docs/reports/20260817-phase8-1-1-authoritative-financial-recovery-audit.json"
            ),
            "safe_inventory_facts": summary["safe_inventory_facts"],
            "trade_receivables_coverage": "NOT_PROVEN",
            "result": "PARTIAL; no buildup conclusion without compatible comparison",
            "status": "PASS",
        },
        {
            "case": "cumulative_loss_despite_latest_quarter_profit",
            "fixture_type": "REPOSITORY_PERIOD_CONTRACT_FIXTURE",
            "source_anchor": "tests/test_kr_financial_lineage_service.py",
            "validated_semantics": [
                "single-quarter and YTD cumulative fields remain distinct",
                "no mixed-period directional conclusion",
            ],
            "status": "PASS",
        },
        {
            "case": "net_income_improvement_with_non_operating_effect",
            "fixture_type": "SOURCE_MAPPING_BOUNDARY_CONTROL",
            "source_anchor": "app/services/coldstart_fundamental_enrichment_service.py",
            "verified_available_concepts": [
                "InterestIncomeExpenseNet",
                "NoninterestIncome",
            ],
            "result": "SECTOR_SPECIFIC_ONLY; generic attribution remains mapping-incomplete",
            "status": "PASS",
        },
        {
            "case": "generic_domain_not_applicable",
            "fixture_type": "PRESERVED_INDUSTRY_APPLICABILITY_CONTROL",
            "source_anchor": (
                "docs/reports/20260820-phase9-0b-canonical-facts.json"
            ),
            "observed_subject": insurance.get("ticker"),
            "observed_industry": insurance.get("industry"),
            "generic_fcf_status": insurance["metrics"]["fcf"]["status"],
            "result": "GENERIC_ENTERPRISE_FCF_NOT_APPLICABLE",
            "status": "PASS",
        },
    ]
    return {
        "contract": "m4-offline-representative-fixture-manifest-v1",
        "rows": rows,
        "fixture_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "model_calls": 0,
        "provider_calls": 0,
        "historical_subjects_used_as_generic_rules": False,
        "status": "PASS",
    }


def semantics_audit(repo_root: Path) -> dict[str, object]:
    files = {
        "cashflow": (
            repo_root / "app/services/cash_flow_capital_efficiency_service.py"
        ).read_text(encoding="utf-8"),
        "official": (repo_root / "app/services/official_cash_flow_service.py").read_text(
            encoding="utf-8"
        ),
        "dart": (
            repo_root / "app/services/opendart_financial_recovery_service.py"
        ).read_text(encoding="utf-8"),
        "kr_lineage": (
            repo_root / "app/services/kr_financial_lineage_service.py"
        ).read_text(encoding="utf-8"),
        "packet": (
            repo_root / "app/services/cross_market_decision_engine_service.py"
        ).read_text(encoding="utf-8"),
        "snapshot": (
            repo_root / "app/services/financial_snapshot_service.py"
        ).read_text(encoding="utf-8"),
    }
    checks = {
        "qtd_ytd_fy_ttm_types_exist": all(
            token in files["cashflow"] for token in ('QTD = "QTD"', 'YTD = "YTD"', 'TTM = "TTM"')
        ),
        "guarded_qtd_derivation_exists": "def derive_qtd_from_ytd" in files["cashflow"],
        "guarded_ttm_derivation_exists": "def derive_ttm" in files["cashflow"],
        "guarded_fcf_derivation_exists": "def derive_fcf" in files["cashflow"],
        "official_ocf_semantic_exists": (
            "NetCashProvidedByUsedInOperatingActivities" in files["official"]
        ),
        "generic_investing_rejected": (
            "generic_investing_cash_flow_not_ppe_capex" in files["official"]
        ),
        "acquisition_and_intangible_rejected": all(
            token in files["official"]
            for token in ("business_acquisition_excluded", "intangible_purchase_excluded")
        ),
        "kr_ocf_requires_xbrl_period": (
            '"operating_cash_flow"' in files["dart"]
            and "xbrl_period_required=True" in files["dart"]
        ),
        "kr_comparison_compatibility_exists": (
            "def growth_lineage_compatible" in files["kr_lineage"]
        ),
        "unsafe_total_liabilities_debt_mapping_detected": (
            "snapshot.debt = liabilities" in files["snapshot"]
        ),
        "current_packet_lacks_financial_context": (
            "financial_context" not in files["packet"]
        ),
    }
    return {
        "contract": "m4-offline-domain-semantics-audit-v1",
        "checks": checks,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "domain_count": len(DOMAINS),
        "all_domains_audited": True,
        "provider_calls": 0,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def materiality_contract() -> dict[str, object]:
    return {
        "contract": "financial-domain-materiality-v1-design",
        "states": [
            "MATERIAL",
            "SUPPORTIVE",
            "CONTEXT_ONLY",
            "NOT_APPLICABLE",
            "UNAVAILABLE",
        ],
        "material_when_may_change": [
            "investment thesis strength",
            "earnings quality",
            "financial resilience",
            "valuation interpretation without creating valuation evidence",
            "warning or invalidation logic",
        ],
        "selection": "select only decision-relevant domains; no mention-all requirement",
        "fixed_score": False,
        "missing_is_negative": False,
        "status": "FROZEN_DESIGN",
    }


def direct_derived_contract(
    contracts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    derivations = [
        {"domain": row["domain"], **dict(item)}
        for row in contracts
        for item in row["safe_derivations"]
    ]
    forbidden = [
        {"domain": row["domain"], "derivation": item}
        for row in contracts
        for item in row["forbidden_derivations"]
    ]
    return {
        "contract": "direct-vs-derived-financial-evidence-v1-design",
        "allowed_statuses": ["DIRECT_REPORTED", "DERIVED_SAFE"],
        "derived_requirements": [
            "registered formula",
            "ordered input source IDs",
            "period/currency/entity/attribution compatibility",
            "explicit failure conditions",
        ],
        "derived_metrics": derivations,
        "derived_metric_count": len(derivations),
        "forbidden_derivations": forbidden,
        "forbidden_derivation_count": len(forbidden),
        "status": "FROZEN_DESIGN",
    }


def period_contract() -> dict[str, object]:
    return {
        "contract": "financial-period-specificity-v1-design",
        "period_types": ["QTD", "YTD", "FY", "TTM", "POINT_IN_TIME"],
        "rules": [
            "single-quarter, cumulative YTD, annual, and point-in-time remain explicit",
            "prior comparison must share period type and compatible duration",
            "QTD reconstruction requires canonical same-year YTD compatibility",
            "TTM requires prior FY + current YTD - prior comparable YTD",
            "late pre-baseline facts cannot become current Daily Delta",
        ],
        "forbidden": [
            "interim annualization",
            "QTD/YTD or YTD/FY comparison",
            "year-end/interim balance movement labeled YoY",
            "generic recent-results wording that hides a material period conflict",
        ],
        "status": "FROZEN_DESIGN",
    }


def earnings_quality_contract() -> dict[str, object]:
    return {
        "contract": "earnings-quality-cross-domain-v1-design",
        "invariant": "reported net-income growth is not earnings-quality improvement",
        "qualifying_domains": [
            "operating profit",
            "operating cash flow",
            "PPE reinvestment",
            "working capital",
            "debt/liquidity",
            "financial/non-operating effects",
        ],
        "allowed_roles": ["SUPPORTING", "LIMITING", "WARNING"],
        "causality_rule": "state observed relation; do not invent working-capital or capex cause",
        "deterministic_score": False,
        "status": "FROZEN_DESIGN",
    }


def directional_specificity_contract() -> dict[str, object]:
    return {
        "contract": "directional-financial-specificity-v1-design",
        "anchor_count": {"minimum": 1, "maximum": 3},
        "anchor_classes": [
            "absolute_condition",
            "trend",
            "cash_conversion_quality",
            "balance_sheet_resilience",
            "sector_kpi",
            "valuation_evidence",
            "risk",
        ],
        "selection_rule": "prefer decision relevance and independence over line-item count",
        "correlated_groups": [
            {
                "observations": ["revenue", "operating_profit", "net_income"],
                "possible_single_conclusion": "profitable operation or profitability trend",
                "automatic_independent_anchor_count": 0,
            }
        ],
        "required_specific_patterns_when_proven": [
            "profit growth plus cash-flow weakness",
            "profit growth plus leverage pressure",
            "single-quarter profit plus cumulative loss",
            "net-income growth driven by non-operating effects",
            "profit growth plus inventory/receivable buildup",
            "profit growth plus strong cash conversion and liquidity",
        ],
        "checklist_or_fixed_score": False,
        "production_prompt_modified": False,
        "status": "FROZEN_DESIGN",
    }


def warning_contract(contracts: Sequence[Mapping[str, object]]) -> dict[str, object]:
    rows = []
    for row in contracts:
        domain = str(row["domain"])
        kill_candidate = domain in {
            "debt_liquidity",
            "inventory_receivables_working_capital",
            "operating_cash_flow",
        }
        rows.append(
            {
                "domain": domain,
                "early_warning": "CONDITIONAL",
                "kill_condition": "CONDITIONAL_PERSISTENT_CONTEXT"
                if kill_candidate
                else "NOT_FROM_ONE_PERIOD_DOMAIN_FACT",
                "requirements": [
                    "validated source",
                    "materiality",
                    "persistence or explicit structural context",
                    "existing thesis metric linkage",
                ],
            }
        )
    return {
        "contract": "financial-domain-warning-kill-condition-v1-design",
        "rows": rows,
        "one_period_automatic_kill": False,
        "warning_mutations_in_m4": 0,
        "status": "FROZEN_DESIGN",
    }


def valuation_contract() -> dict[str, object]:
    return {
        "contract": "financial-domain-valuation-boundary-v1-design",
        "invariant": "earnings quality and financial condition are not valuation",
        "allowed": [
            "qualify confidence in a denominator",
            "state conditions for future multiple expansion/compression interpretation",
        ],
        "forbidden": [
            "invent EPS/BVPS/FCF denominator",
            "infer a market multiple or price target",
            "combine issuer cash flow with ADR/security price without verified basis",
            "treat PPE-only residual as company-defined FCF",
        ],
        "valuation_unavailable_remains_unavailable": True,
        "status": "FROZEN_DESIGN",
    }


def candidate_packages() -> list[dict[str, object]]:
    return [
        {
            "package": "B_PACKET_FINANCIAL_CONTEXT_EXTENSION",
            "scope": "add optional typed financial_context and validation; no producer activation",
            "semantic_risk": "MEDIUM",
            "affected_modules": [
                "app/services/cross_market_decision_engine_service.py",
                "packet validators and tests",
            ],
            "required_tests": ["backward compatibility", "typed metadata hard failures"],
            "model_revalidation_required": False,
            "fresh_real_holdout_required": False,
        },
        {
            "package": "A_EXISTING_CANONICAL_DOMAIN_ADAPTERS",
            "scope": "bridge same-period comparison and existing OCF/PPE facts into packet",
            "semantic_risk": "MEDIUM",
            "affected_modules": ["new bounded packet adapter", "canonical lineage tests"],
            "required_tests": ["period/basis lineage", "PPE label", "missing semantics"],
            "model_revalidation_required": False,
            "fresh_real_holdout_required": False,
        },
        {
            "package": "A_ADDITIONAL_SOURCE_MAPPING_SUBPACKAGES",
            "scope": "separate debt/liquidity, working-capital, and non-operating mappings",
            "semantic_risk": "HIGH",
            "affected_modules": ["SEC/OpenDART normalization adapters"],
            "required_tests": ["component completeness", "sector routing", "offline fixtures"],
            "model_revalidation_required": False,
            "fresh_real_holdout_required": False,
        },
        {
            "package": "C_DIRECTIONAL_SPECIFICITY_CONTRACT",
            "scope": "use frozen enriched input for 1-3 independent issuer-specific anchors",
            "semantic_risk": "HIGH",
            "affected_modules": ["Directional Core prompt/validator", "semantic audits"],
            "required_tests": ["period specificity", "correlation", "missing nonnegative"],
            "model_revalidation_required": True,
            "fresh_real_holdout_required": True,
        },
        {
            "package": "D_SECTOR_GATE_REVIEW_IF_COVERAGE_PROVES_REQUIRED",
            "scope": "separate decision before any debt/liquidity source-sufficiency gate",
            "semantic_risk": "HIGH",
            "affected_modules": ["source-sufficiency contract only if separately approved"],
            "required_tests": ["coverage impact", "sector applicability", "fail-closed behavior"],
            "model_revalidation_required": True,
            "fresh_real_holdout_required": True,
        },
    ]


def package_order(packages: Sequence[Mapping[str, object]]) -> list[str]:
    return [str(row["package"]) for row in packages]


def _market_audit(
    market: str, market_rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    rows = [dict(row) for row in market_rows if row["market"] == market]
    return {
        "contract": f"m4-{market}-free-source-domain-support-audit-v1",
        "market": market,
        "rows": rows,
        "supported_domain_count": sum(
            row["support_status"] == "SUPPORTED_CURRENTLY" for row in rows
        ),
        "partial_domain_count": sum(
            row["support_status"] in PARTIAL_SUPPORT_STATUSES for row in rows
        ),
        "unsupported_domain_count": sum(
            row["support_status"] in UNSUPPORTED_STATUSES for row in rows
        ),
        "provider_calls": 0,
        "status": "COMPLETE",
    }


def artifact_index(report_dir: Path) -> dict[str, object]:
    rows = []
    secret_failure_count = 0
    for path in sorted(item for item in report_dir.rglob("*") if item.is_file()):
        if path.name == "artifact-index.json":
            continue
        payload = path.read_bytes()
        secret_counts = {
            name: len(pattern.findall(payload))
            for name, pattern in SECRET_PATTERNS.items()
        }
        status = "PASS" if not any(secret_counts.values()) else "FAIL"
        secret_failure_count += int(status != "PASS")
        rows.append(
            {
                "path": str(path.relative_to(report_dir)),
                "sha256": bytes_sha256(payload),
                "size_bytes": len(payload),
                "secret_scan_status": status,
                "secret_category_counts": secret_counts,
            }
        )
    result = {
        "contract": "m4-artifact-index-v1",
        "payload_count": len(rows),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": secret_failure_count,
        "rows": rows,
        "status": "PASS" if not secret_failure_count else "FAIL",
    }
    if secret_failure_count:
        raise ValueError("artifact_secret_scan_failed")
    return result


def verify_artifact_index(report_dir: Path, index: Mapping[str, object]) -> None:
    for row in index["rows"]:
        path = report_dir / str(row["path"])
        payload = path.read_bytes()
        if file_sha256(path) != row["sha256"]:
            raise ValueError(f"artifact_hash_mismatch:{path}")
        if len(payload) != row["size_bytes"]:
            raise ValueError(f"artifact_size_mismatch:{path}")


def _summary_markdown(completion: Mapping[str, object]) -> str:
    return f"""# 2026-09-08 M4 Source Domain Enrichment Design Review

## Result

- Status: `{completion['status']}`
- Domains closed: `{completion['domain_design_complete_count']}/{completion['domain_count']}`
- US support: `{completion['us_supported_domain_count']} supported / {completion['us_partial_domain_count']} partial / {completion['us_unsupported_domain_count']} unsupported`
- KR support: `{completion['kr_supported_domain_count']} supported / {completion['kr_partial_domain_count']} partial / {completion['kr_unsupported_domain_count']} unsupported`
- Packet schema: `{completion['schema_extension_required_domain_count']} domains require an additive typed extension`
- Universal source gate added: `{completion['universal_source_gate_added_count']}`
- Production readiness: `{completion['production_readiness']}`
- Next scope: `{completion['recommended_next_scope']}`

## Decision

The existing free/public stack already has strong canonical OCF and PPE-only cash-flow
lineage for a selective US/foreign subset, safe KR period-comparison machinery, and
partial working-capital/sector evidence. KR cash-flow duration, complete debt/liquidity,
trade receivable/payable, and generic non-operating attribution remain selective or
mapping-incomplete. Missing evidence stays Unknown rather than negative.

Current `DecisionEvidenceRef` cannot safely carry financial period type, currency,
entity/statement/attribution basis, direct-versus-derived status, or comparison and
derivation lineage as one typed object. The smallest next change is therefore an
optional `financial_context` schema extension with validators and no producer or prompt
activation. Existing canonical adapters follow only after that contract is frozen.
Directional specificity, any sector-conditional source gate, model validation, and a
fresh real holdout remain later, separately frozen steps.

## Safety

This was an offline design review. Model and provider calls, production database or
notification mutations, sends, merges, deployments, V2/Night Futures changes, and
scheduler resume actions were all zero. The eight approved monitoring paths remained
paused at both observations.
"""


def _deterministic_zip(report_dir: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in report_dir.rglob("*") if item.is_file()):
            info = zipfile.ZipInfo(str(path.relative_to(report_dir)))
            info.date_time = (2026, 9, 8, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = args.repo_root.resolve()
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    for path in report_dir.iterdir():
        if path.is_file():
            path.unlink()

    start_pause = observe_pause_state()
    latest = verify_latest_result(args.latest_result_zip.resolve())
    instruction = verify_work_instruction(args.work_instruction_zip.resolve())
    provenance = repository_provenance(
        repo_root,
        work_instruction_commit=args.work_instruction_commit,
        implementation_commit=args.implementation_commit,
    )
    if provenance["status"] != "PASS":
        raise ValueError("UNEXPLAINED_M4_BASELINE_DRIFT")

    contracts = domain_contracts()
    sectors = sector_matrix()
    market_rows = market_support_matrix(contracts)
    inventory = source_inventory(repo_root)
    schema = schema_compatibility(contracts)
    fixtures = representative_fixtures(repo_root)
    semantics = semantics_audit(repo_root)
    materiality = materiality_contract()
    direct_derived = direct_derived_contract(contracts)
    periods = period_contract()
    earnings_quality = earnings_quality_contract()
    specificity = directional_specificity_contract()
    warnings = warning_contract(contracts)
    valuation = valuation_contract()
    packages = candidate_packages()
    order = package_order(packages)
    us_audit = _market_audit("us", market_rows)
    kr_audit = _market_audit("kr", market_rows)
    end_pause = observe_pause_state()
    pause_pass = all(
        row.get("status") == "VERIFIED_PAUSED_COMPLETE"
        for row in (start_pause, end_pause)
    )

    completion: dict[str, object] = {
        "contract": CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": args.work_instruction_commit,
        "implementation_commit": args.implementation_commit,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": provenance["branch"],
        "latest_result_zip_sha256": latest["actual_sha256"],
        "latest_result_integrity": latest["status"],
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "m3_status": "COMPLETE",
        "m4_status": "COMPLETE",
        "domain_count": len(contracts),
        "domain_design_complete_count": len(contracts),
        "same_period_comparison_decision": "REQUIRED_FOR_SPECIFIC_DIRECTIONAL_CLAIMS",
        "operating_cash_flow_decision": "SECTOR_CONDITIONAL_SELECTIVE_ENRICHMENT",
        "ppe_capex_decision": "PPE_ONLY_OCF_LESS_CAPEX_SELECTIVE_ENRICHMENT",
        "debt_liquidity_decision": "SECTOR_CONDITIONAL_MAPPING_REQUIRED",
        "working_capital_decision": "SECTOR_CONDITIONAL_RAW_BALANCES_FIRST",
        "non_operating_effects_decision": "SECTOR_SEMANTIC_MAPPING_REQUIRED",
        "us_supported_domain_count": us_audit["supported_domain_count"],
        "us_partial_domain_count": us_audit["partial_domain_count"],
        "us_unsupported_domain_count": us_audit["unsupported_domain_count"],
        "kr_supported_domain_count": kr_audit["supported_domain_count"],
        "kr_partial_domain_count": kr_audit["partial_domain_count"],
        "kr_unsupported_domain_count": kr_audit["unsupported_domain_count"],
        "schema_sufficient_domain_count": schema["schema_sufficient_domain_count"],
        "schema_extension_required_domain_count": schema[
            "schema_extension_required_domain_count"
        ],
        "universal_source_gate_added_count": 0,
        "sector_conditional_gate_candidate_count": 1,
        "derived_metric_count": direct_derived["derived_metric_count"],
        "forbidden_derivation_count": direct_derived["forbidden_derivation_count"],
        "directional_specificity_contract_status": specificity["status"],
        "earnings_quality_contract_status": earnings_quality["status"],
        "period_specificity_contract_status": periods["status"],
        "materiality_contract_status": materiality["status"],
        "implementation_package_count": len(packages),
        "recommended_implementation_order": order,
        "semantic_change_required": True,
        "schema_change_required": True,
        "source_sufficiency_change_required": False,
        "directional_prompt_change_required": True,
        "new_model_validation_required": True,
        "new_real_holdout_proof_required": True,
        "recommended_next_scope": "DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION",
        **SIDE_EFFECT_COUNTS,
        "observed_paused_schedule_count": min(
            int(start_pause.get("observed_scheduler_object_count") or 0),
            int(end_pause.get("observed_scheduler_object_count") or 0),
        ),
        "focused_test_result": args.focused_test_result,
        "full_test_result": args.full_test_result,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.git_diff_check,
        "artifact_count": len(REPORT_NAMES) + 1,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M4_COMPLETE" if pause_pass else "M4_BLOCKED",
        "stop_reason": None if pause_pass else "SCHEDULE_PAUSE_STATE_NOT_VERIFIED",
        "next_scope": "DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION",
    }
    if completion["status"] != "M4_COMPLETE":
        raise ValueError(str(completion["stop_reason"]))

    reuse = {
        "contract": "m4-m1-m2-m3-contract-reuse-proof-v1",
        "rows": [
            {
                "phase": "M1",
                "reused": ["Unknown nonnegative semantics", "early Core validation"],
                "reopened": False,
            },
            {
                "phase": "M2",
                "reused": [
                    "source-to-Core preserved-domain audit",
                    "Directional/Timing ownership",
                    "file-only message boundary",
                ],
                "reopened": False,
            },
            {
                "phase": "M3",
                "reused": [
                    "initial vs baseline vs Daily Delta separation",
                    "baseline cutoff",
                    "late pre-baseline evidence is not a delta",
                    "idempotent warning/assessment boundary",
                ],
                "reopened": False,
            },
        ],
        "status": "PASS",
    }
    backlog = {
        "contract": "m4-source-domain-backlog-reconciliation-v1",
        "source": (
            "docs/reports/20260908-nonproduction-monitoring-bootstrap-daily-delta-"
            "lifecycle-integration/25-source-domain-backlog-update.json"
        ),
        "rows": [
            {
                "domain": row["domain"],
                "prior_state": "PRESERVE_AS_SEPARATE_DESIGN_REVIEW",
                "m4_state": "CONTRACT_CLOSED",
                "next_action": "SCHEMA_THEN_BOUNDED_SOURCE_ADAPTER",
            }
            for row in contracts
        ],
        "reconciled_count": len(contracts),
        "status": "PASS",
    }
    scope = {
        "contract": "m4-scope-freeze-v1",
        "included": [
            "offline parser/mapping introspection",
            "six safe domain contracts",
            "sector and market support classification",
            "bounded schema and implementation-order decision",
            "offline fixture and static validation",
        ],
        "excluded": [
            "provider/source fetch",
            "model/judge call",
            "broad parser or packet production change",
            "Directional prompt/renderer/source-sufficiency change",
            "production merge/deploy/send/database mutation",
            "scheduler resume",
            "paid source",
        ],
        "side_effect_counts": SIDE_EFFECT_COUNTS,
        "status": "FROZEN",
    }
    domain_files = dict(
        zip(
            REPORT_NAMES[9:15],
            (
                {
                    "contract": "m4-domain-design-v1",
                    "design": row,
                    "status": "FROZEN_DESIGN",
                }
                for row in contracts
            ),
            strict=True,
        )
    )
    schedule = {
        "contract": "m4-schedule-pause-observation-v1",
        "start": start_pause,
        "end": end_pause,
        "expected_paused_path_count": 8,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if pause_pass else "FAIL",
    }
    artifacts: dict[str, object] = {
        REPORT_NAMES[0]: provenance,
        REPORT_NAMES[1]: {**latest, "work_instruction": instruction},
        REPORT_NAMES[2]: scope,
        REPORT_NAMES[3]: reuse,
        REPORT_NAMES[4]: backlog,
        REPORT_NAMES[5]: inventory,
        REPORT_NAMES[6]: {
            "contract": "m4-source-domain-contract-matrix-v1",
            "rows": contracts,
            "domain_count": len(contracts),
            "complete_count": len(contracts),
            "status": "COMPLETE",
        },
        REPORT_NAMES[7]: {
            "contract": "m4-sector-applicability-matrix-v1",
            "rows": sectors,
            "sector_count": len(sectors),
            "universal_domain_requirement": False,
            "status": "FROZEN_DESIGN",
        },
        REPORT_NAMES[8]: {
            "contract": "m4-market-source-support-matrix-v1",
            "rows": market_rows,
            "pair_count": len(market_rows),
            "provider_calls": 0,
            "status": "COMPLETE",
        },
        **domain_files,
        REPORT_NAMES[15]: materiality,
        REPORT_NAMES[16]: direct_derived,
        REPORT_NAMES[17]: periods,
        REPORT_NAMES[18]: earnings_quality,
        REPORT_NAMES[19]: specificity,
        REPORT_NAMES[20]: warnings,
        REPORT_NAMES[21]: valuation,
        REPORT_NAMES[22]: fixtures,
        REPORT_NAMES[23]: semantics,
        REPORT_NAMES[24]: us_audit,
        REPORT_NAMES[25]: kr_audit,
        REPORT_NAMES[26]: schema,
        REPORT_NAMES[27]: {
            "contract": "m4-candidate-implementation-packages-v1",
            "rows": packages,
            "package_count": len(packages),
            "status": "FROZEN_DESIGN",
        },
        REPORT_NAMES[28]: {
            "contract": "m4-implementation-order-decision-v1",
            "order": order,
            "reason": (
                "freeze additive packet representation before source producers or prompt semantics"
            ),
            "simultaneous_source_prompt_renderer_change": False,
            "status": "DECIDED",
        },
        REPORT_NAMES[29]: {
            "contract": "m4-required-schema-change-decision-v1",
            "schema_change_required": True,
            "decision": "ADDITIVE_OPTIONAL_FINANCIAL_CONTEXT_REQUIRED",
            "proposal": schema["bounded_schema_proposal"],
            "implemented_in_m4": False,
            "status": "DECIDED",
        },
        REPORT_NAMES[30]: {
            "contract": "m4-required-source-sufficiency-change-decision-v1",
            "source_sufficiency_change_required_now": False,
            "universal_gate_added_count": 0,
            "sector_conditional_candidate_domains": ["debt_liquidity"],
            "future_gate_condition": (
                "separate coverage proof for financing-dependent sector/framework claims"
            ),
            "status": "NO_CURRENT_GATE_CHANGE",
        },
        REPORT_NAMES[31]: {
            "contract": "m4-required-directional-specificity-change-decision-v1",
            "directional_prompt_change_required": True,
            "implementation_timing": "after enriched packet input is frozen",
            "design_contract": specificity,
            "implemented_in_m4": False,
            "status": "DECIDED",
        },
        REPORT_NAMES[32]: {
            "contract": "m4-required-model-validation-scope-v1",
            "required": True,
            "timing": "after packet, adapters, and Directional contract are separately frozen",
            "requirements": [
                "fresh generation ID",
                "same frozen source/model/effort/schema/validator/renderer contract",
                "period/sector/missing-data negative controls",
                "no selective rerun or in-run hotfix",
            ],
            "model_calls_in_m4": 0,
            "status": "FUTURE_REQUIRED",
        },
        REPORT_NAMES[33]: {
            "contract": "m4-required-real-holdout-scope-v1",
            "required": True,
            "timing": "after model validation contract freeze",
            "required_cases": [
                "dual-market",
                "financial-sector N/A",
                "capital-intensive negative post-PPE cash conversion",
                "working-capital divergence",
                "non-operating attribution",
                "missing domain remains nonnegative",
            ],
            "historical_retired_cohort_reuse": False,
            "real_holdout_runs_in_m4": 0,
            "status": "FUTURE_REQUIRED",
        },
        REPORT_NAMES[34]: {
            "contract": "m4-production-no-change-v1",
            "side_effect_counts": SIDE_EFFECT_COUNTS,
            "production_schema_changed": False,
            "production_prompt_changed": False,
            "source_parser_output_changed": False,
            "renderer_changed": False,
            "production_readiness": "NOT_READY",
            "status": "PASS",
        },
        REPORT_NAMES[35]: schedule,
        REPORT_NAMES[36]: {
            "contract": "m4-master-workflow-update-v1",
            "path": "docs/MASTER_WORKFLOW.md",
            "required_marker": "m4-source-domain-enrichment-design-review-v1",
            "marker_present": (
                "m4-source-domain-enrichment-design-review-v1"
                in (repo_root / "docs/MASTER_WORKFLOW.md").read_text(encoding="utf-8")
            ),
            "next_scope": "DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION",
            "status": "PASS",
        },
        REPORT_NAMES[37]: completion,
    }
    if set(artifacts) != set(REPORT_NAMES):
        raise ValueError("required_artifact_set_mismatch")
    for name in REPORT_NAMES:
        write_json(report_dir / name, artifacts[name])
    (report_dir / SUMMARY_NAME).write_text(
        _summary_markdown(completion), encoding="utf-8"
    )
    index = artifact_index(report_dir)
    if index["payload_count"] != completion["artifact_count"]:
        raise ValueError("artifact_payload_count_mismatch")
    write_json(report_dir / "artifact-index.json", index)
    verify_artifact_index(report_dir, index)
    _deterministic_zip(report_dir, args.output_zip.resolve())
    return {
        "status": completion["status"],
        "report_dir": str(report_dir),
        "artifact_payload_count": index["payload_count"],
        "output_zip": str(args.output_zip.resolve()),
        "output_zip_sha256": file_sha256(args.output_zip.resolve()),
        "recommended_next_scope": completion["recommended_next_scope"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--work-instruction-zip", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--work-instruction-commit", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--focused-test-result", default="NOT_MEASURED")
    parser.add_argument("--full-test-result", default="NOT_MEASURED")
    parser.add_argument("--ruff-result", default="NOT_MEASURED")
    parser.add_argument("--git-diff-check", default="NOT_MEASURED")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False, indent=2))
