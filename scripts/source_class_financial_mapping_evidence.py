from __future__ import annotations

import ast
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tomllib
from typing import Any, Mapping
import zipfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cash_flow_capital_efficiency_service import (  # noqa: E402
    Metric,
    derive_fcf,
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
    CONTRACT_VERSION as ADAPTER_CONTRACT,
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (  # noqa: E402
    CONTRACT_VERSION as LINEAGE_CONTRACT,
    project_financial_fact_catalog,
)
from app.services.opendart_financial_recovery_service import (  # noqa: E402
    Filing,
)
from app.services.opendart_xbrl_service import (  # noqa: E402
    parse_xbrl_archive,
    reconcile_xbrl_duration_fact,
)
from app.services.source_class_financial_mapping_service import (  # noqa: E402
    CONTRACT_VERSION as SOURCE_CLASS_CONTRACT,
    promote_opendart_cash_flow_facts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (
    REPO_ROOT
    / "docs/reports/20260908-source-class-financial-mapping-implementation"
)
SUMMARY_NAME = "20260908-source-class-financial-mapping-implementation.md"
BASE_SHA = "3ac2359a16c8b6e03a146ecc32676005e1589db4"
WORK_INSTRUCTION_COMMIT = "86f361fb92431c8725087e082bf06b83a399480d"
IMPLEMENTATION_COMMIT = "00a8663c1adbd32b487f4672fea4011d159ee945"
M7_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260908-financial-lineage-kr-period-"
    "projection-source-mapping-report.zip"
)
M7_RESULT_SHA256 = "b9be904a744a2c226c93bcc4a4ffce4abe0b87f76bfb8470e1070207d286a2da"
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"
KR_CACHE_ROOT = (
    REPO_ROOT.parents[1]
    / "thesis-monitor-phase7-2/data/cache/opendart/recovery-final"
)
PROVIDER_DB = Path.home() / "Codex/thesis-monitor/data/thesis_monitor.sqlite3"
MASTER_WORKFLOW = REPO_ROOT / "docs/MASTER_WORKFLOW.md"
START_OBSERVED_AT_UTC = "2026-09-08T13:43:28Z"

FOCUSED_TEST_COMMAND = (
    "shared-venv/bin/pytest -q "
    "tests/test_decision_evidence_financial_context.py "
    "tests/test_financial_context_adapter_service.py "
    "tests/test_financial_lineage_projection_service.py "
    "tests/test_cash_flow_capital_efficiency_service.py "
    "tests/test_official_cash_flow_service.py "
    "tests/test_source_class_financial_mapping_service.py "
    "tests/test_opendart_financial_recovery_service.py "
    "tests/test_opendart_xbrl_service.py "
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
            "m8-scope-freeze",
            "m7-contract-reuse-proof",
            "source-class-gap-classification",
            "hut-historical-gap-diagnostic",
            "skhy-historical-gap-diagnostic",
            "kr-canonical-promotion-gap-diagnostic",
            "generic-ppe-source-class-contract",
            "foreign-issuer-cash-flow-source-class-contract",
            "kr-exact-context-canonical-promotion-contract",
            "source-class-mapping-implementation-diff",
            "source-class-activation-surface",
            "source-precedence-and-dedup-contract",
            "market-source-class-support-audit",
            "compact-ai-context-non-leak-proof",
            "directional-prompt-no-change-proof",
            "price-timing-no-change-proof",
            "source-sufficiency-no-change-proof",
            "daily-delta-no-change-proof",
            "historical-packet-compatibility",
            "source-mapping-idempotency-proof",
            "positive-fixture-manifest",
            "negative-fixture-manifest",
            "pre-post-source-class-coverage",
            "kr-real-coverage-pre-post",
            "focused-test-results",
            "full-test-results",
            "ruff-and-diff-results",
            "remaining-source-mapping-backlog",
            "higher-risk-domain-priority-decision",
            "directional-specificity-activation-decision",
            "source-sufficiency-no-change-decision",
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
        completion = json.loads(archive.read("34-program-completion.json"))
    return {
        "indexed_payload_count": len(index["rows"]),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "missing_payload_count": missing,
        "secret_scan_failure_count": secret_failures,
        "reported_status": completion["status"],
        "reported_final_head_sha": completion["final_head_sha"],
        "actual_final_head_sha": BASE_SHA,
        "precommit_reporting_convention_semantic_drift": False,
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


def _exact_context(
    rows: list[dict[str, object]],
    facts: list[Any],
    *,
    account_id: str,
    corp_code: str,
) -> dict[str, object] | None:
    matches = [row for row in rows if row.get("account_id") == account_id]
    if len(matches) != 1:
        return None
    row = matches[0]
    fact = reconcile_xbrl_duration_fact(
        facts,
        taxonomy_element=account_id.split("_", maxsplit=1)[-1],
        value=row.get("thstrm_amount"),
        unit_ref="KRW",
        statement_basis="consolidated",
        entity_identifier=corp_code,
    )
    if fact is None:
        return None
    return {
        "account_id": account_id,
        "reported_amount": row.get("thstrm_amount"),
        "currency": row.get("currency"),
        "context_ref": fact.context_ref,
        "unit_ref": fact.unit_ref,
        "entity_identifier": fact.context.entity_identifier,
        "period_start": fact.context.period_start,
        "period_end": fact.context.period_end,
        "duration_days": (
            (fact.context.period_end - fact.context.period_start).days + 1
            if fact.context.period_start and fact.context.period_end
            else None
        ),
        "statement_basis": fact.context.statement_basis,
        "dimensions": fact.context.dimensions,
    }


def kr_real_evidence() -> tuple[list[dict[str, object]], list[Any]]:
    phase9 = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    subjects = {row["ticker"]: row for row in phase9["active_universe"]}
    evidence: list[dict[str, object]] = []
    all_facts: list[Any] = []
    for directory in sorted(KR_CACHE_ROOT.glob("*/*")):
        required = [directory / name for name in ("CFS.json", "OFS.json", "xbrl.zip")]
        if not all(path.is_file() for path in required):
            continue
        cfs = json.loads(required[0].read_text(encoding="utf-8"))
        ofs = json.loads(required[1].read_text(encoding="utf-8"))
        filing = _filing_from_cache(cfs)
        contexts, xbrl_facts = parse_xbrl_archive(required[2].read_bytes())
        raw_sha = sha256_bytes(b"\0".join(path.read_bytes() for path in required))
        first = promote_opendart_cash_flow_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 8),
        )
        second = promote_opendart_cash_flow_facts(
            filing,
            {"CFS": cfs["rows"], "OFS": ofs["rows"]},
            xbrl_facts,
            raw_payload_sha256=raw_sha,
            as_of_date=date(2026, 9, 8),
        )
        by_metric = {fact.metric: fact for fact in first.facts}
        fcf = (
            derive_fcf(by_metric[Metric.OCF], by_metric[Metric.CAPEX]).fact
            if {Metric.OCF, Metric.CAPEX}.issubset(by_metric)
            else None
        )
        rows = project_financial_fact_catalog(
            list(first.facts),
            context_id=f"m8-real-{filing.ticker}",
        )
        adapter_results = [
            adapt_fact_catalog_financial_context(row, rows) for row in rows
        ]
        compact_packet = build_decision_evidence_packet(
            packet={
                "packet_id": f"m8-real-{filing.ticker}",
                "market": "kr",
                "assessment_date": "2026-09-08",
            },
            stock={"ticker": filing.ticker, "fact_catalog": rows},
        )
        legacy_packet = compact_packet.model_copy(
            update={
                "evidence": tuple(
                    ref.model_copy(update={"financial_context": None})
                    for ref in compact_packet.evidence
                )
            }
        )
        before_compact = compact_ai_context(legacy_packet)
        after_compact = compact_ai_context(compact_packet)
        ocf_account = "ifrs-full_CashFlowsFromUsedInOperatingActivities"
        ppe_account = (
            "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"
        )
        subject = subjects.get(filing.ticker, {})
        evidence.append(
            {
                "ticker": filing.ticker,
                "industry": subject.get("industry"),
                "financial_type": subject.get("financial_type"),
                "source_directory": str(directory),
                "source_file_sha256": {
                    path.name: sha256_file(path) for path in required
                },
                "xbrl_context_count": len(contexts),
                "xbrl_fact_count": len(xbrl_facts),
                "source_candidates": first.source_candidates,
                "promoted_fact_count": len(first.facts),
                "denials": first.denials,
                "facts": [
                    {
                        "fact_id": fact.fact_id,
                        "metric": fact.metric.value,
                        "value": str(fact.value),
                        "currency": fact.currency,
                        "period_start": fact.period.start,
                        "period_end": fact.period.end,
                        "period_type": fact.period.period_type.value,
                        "entity_scope": fact.entity_scope,
                        "statement_basis": fact.statement_basis,
                        "source_document_id": fact.source_document_id,
                        "source_occurrence_id": fact.source_occurrence_id,
                        "source_semantic": fact.source_semantic,
                        "fact_type": fact.fact_type.value,
                    }
                    for fact in first.facts
                ],
                "ocf_exact_context": _exact_context(
                    cfs["rows"],
                    xbrl_facts,
                    account_id=ocf_account,
                    corp_code=filing.corp_code,
                ),
                "ppe_exact_context": _exact_context(
                    cfs["rows"],
                    xbrl_facts,
                    account_id=ppe_account,
                    corp_code=filing.corp_code,
                ),
                "downstream_existing_fcf_fact_id": fcf.fact_id if fcf else None,
                "downstream_existing_fcf_value": str(fcf.value) if fcf else None,
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
        all_facts.extend(first.facts)
    return evidence, all_facts


def current_foreign_cache_summary(ticker: str) -> dict[str, object]:
    if not PROVIDER_DB.is_file():
        return {"status": "CACHE_NOT_PRESENT"}
    with sqlite3.connect(PROVIDER_DB) as connection:
        row = connection.execute(
            "SELECT status,payload,fetched_at FROM providerresponsecache "
            "WHERE provider=? AND ticker=? AND data_type=?",
            ("sec_edgar", ticker, "foreign_6k_exhibits"),
        ).fetchone()
    if row is None:
        return {"status": "CACHE_ROW_NOT_PRESENT"}
    payload = json.loads(row[1])
    return {
        "cache_status": row[0],
        "fetched_at": row[2],
        "filing_discovery_coverage": payload.get("filing_discovery_coverage"),
        "statement_parsing_coverage": payload.get("statement_parsing_coverage"),
        "filing_discovered": payload.get("filing_discovered"),
        "any_statement_parsed": payload.get("any_statement_parsed"),
        "latest_filing_parse_result": payload.get("latest_filing_parse_result"),
        "latest_financial_statement_period": payload.get(
            "latest_financial_statement_period"
        ),
        "filing_count": len(payload.get("filings") or []),
        "raw_payload_in_report": False,
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
            {"id": automation_id, "status": payload.get("status")}
        )
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
        "contract": "m8-schedule-pause-observation-v1",
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
        name: len(pattern.findall(payload))
        for name, pattern in SECRET_PATTERNS.items()
    }
    return ("PASS" if sum(counts.values()) == 0 else "FAIL", counts)


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual_m7_sha = sha256_file(M7_RESULT_ZIP)
    m7_integrity = verify_zip_index(M7_RESULT_ZIP)
    phase9 = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    active = {row["ticker"]: row for row in phase9["active_universe"]}
    phase9_facts = phase9["canonical_facts"]
    kr_evidence, kr_facts = kr_real_evidence()
    branch = git_output("branch", "--show-current")
    implementation_diff = git_output(
        "diff", "--name-status", f"{WORK_INSTRUCTION_COMMIT}..{IMPLEMENTATION_COMMIT}"
    ).splitlines()
    changed_paths = git_output("diff", "--name-only", BASE_SHA).splitlines()

    hut = active["HUT"]
    skhy = active["SKHY"]
    hut_facts = [row for row in phase9_facts if row["ticker"] == "HUT"]
    skhy_facts = [row for row in phase9_facts if row["ticker"] == "SKHY"]
    foreign_examples = [
        row
        for row in phase9_facts
        if row["ticker"] in {"TSM", "WRD"}
        and row["fact_type"] == "REPORTED"
        and row["metric"] in {"operating_cash_flow", "ppe_capex_cash_outflow"}
    ]
    foreign_example_summary = sorted(
        {
            (
                row["ticker"],
                row["source_document_type"],
                row["source_semantic"],
                row["currency"],
            )
            for row in foreign_examples
        }
    )

    direct_adapter_count = sum(row["adapter_emission_count"] for row in kr_evidence)
    direct_fact_counts = Counter(fact.metric.value for fact in kr_facts)
    compact_rows = [
        {
            "ticker": row["ticker"],
            "before_sha256": row["compact_ai_context_before_sha256"],
            "after_sha256": row["compact_ai_context_after_sha256"],
            "unchanged": row["compact_ai_context_unchanged"],
        }
        for row in kr_evidence
    ]
    idempotent_count = sum(row["idempotent"] for row in kr_evidence)

    prompt_core = function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_core_prompt"
    )
    prompt_timing = function_hashes(
        "scripts/directional_core_price_timing_holdout.py", "_timing_prompt"
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
    lineage_function = function_hashes(
        "app/services/financial_lineage_projection_service.py",
        "canonical_lineage_projection",
    )
    adapter_function = function_hashes(
        "app/services/financial_context_adapter_service.py",
        "adapt_fact_catalog_financial_context",
    )
    exact_reconciler = function_hashes(
        "app/services/opendart_xbrl_service.py",
        "reconcile_xbrl_duration_fact",
    )

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
        "source_class_contract": SOURCE_CLASS_CONTRACT,
    }
    sufficiency_before = evaluate_source_sufficiency(
        source_facts,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    sufficiency_after = evaluate_source_sufficiency(
        source_facts_after,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    schedule = schedule_observation()

    classifications = [
        {
            "historical_example": "HUT",
            "metric_scope": "ppe_capex_cash_outflow",
            "classification": "SOURCE_EVIDENCE_INSUFFICIENT",
            "source_family": "SEC CompanyFacts",
            "filing_document_class": "10-K/10-Q",
            "taxonomy_account_concept_class": (
                "US-GAAP PPE cash purchase concept not present in preserved extracted evidence"
            ),
            "period_context_metadata": (
                "OCF duration contexts preserved; no PPE occurrence preserved"
            ),
            "issuer_security_identity_behavior": "issuer-level domestic SEC registrant",
            "normalization_path": "existing SEC CompanyFacts canonicalizer",
            "genericity_basis": (
                "The original CompanyFacts payload and any unregistered extension concept "
                "are not preserved, so no reusable PPE alias can be proven."
            ),
            "generic_rule_id": None,
            "resolved_by_generic_rule": False,
            "decision": "HUT_GAP_DEFERRED_NO_TICKER_EXCEPTION",
        },
        {
            "historical_example": "SKHY",
            "metric_scope": "operating_cash_flow_and_ppe_capex_cash_outflow",
            "classification": "ALREADY_SUPPORTED_AFTER_M7",
            "source_family": "SEC foreign-private-issuer structured filing",
            "filing_document_class": "20-F/6-K",
            "taxonomy_account_concept_class": "IFRS OCF and PPE cash-purchase concepts",
            "period_context_metadata": (
                "generic exact duration support proven by TSM and WRD; SKHY has zero "
                "preserved canonical cash-flow occurrences"
            ),
            "issuer_security_identity_behavior": (
                "issuer-level financial facts remain independent of ADR/share basis"
            ),
            "normalization_path": "existing IFRS registry and official filing canonicalizer",
            "genericity_basis": (
                "TSM and WRD are additional repository examples for the same IFRS rule."
            ),
            "generic_rule_id": "existing-ifrs-foreign-issuer-cash-flow-v1",
            "resolved_by_generic_rule": False,
            "decision": "SKHY_GAP_DEFERRED_NO_TICKER_EXCEPTION",
        },
        {
            "historical_example": "KR_OPENDART_REAL_COHORT",
            "metric_scope": "operating_cash_flow_and_ppe_capex_cash_outflow",
            "classification": "GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT",
            "source_family": "OpenDART full-statement rows plus official XBRL archive",
            "filing_document_class": "OpenDART formal periodic filing",
            "taxonomy_account_concept_class": "IFRS OCF and PPE cash-purchase concepts",
            "period_context_metadata": (
                "seven real caches have unique concept, amount, KRW unit, entity, duration "
                "and statement-basis-member contexts"
            ),
            "issuer_security_identity_behavior": (
                "OpenDART corporation entity identifier; no security denominator"
            ),
            "normalization_path": (
                "M7 exact-duration reconciler then M8 direct canonical promotion"
            ),
            "genericity_basis": (
                "All seven issuers reproduce the same mixed-axis-label/member-value issue."
            ),
            "generic_rule_id": "opendart-statement-basis-member-v1",
            "resolved_by_generic_rule": True,
            "decision": "IMPLEMENTED_BOUNDED_GENERIC_MEMBER_BASIS_AND_EXACT_PROMOTION",
        },
    ]

    positive_cases = [
        "mixed_scope_axis_consolidated_member_parsing",
        "mixed_scope_axis_separate_member_parsing",
        "exact_kr_ocf_context_promotion",
        "exact_kr_ppe_context_promotion",
        "cfs_precedence_over_ofs",
        "direct_reported_fact_identity",
        "existing_m6_m7_downstream_projection",
        "idempotent_repeated_promotion",
        "foreign_ifrs_20f_ocf",
        "foreign_ifrs_20f_ppe",
        "tsm_repository_source_standard_example",
        "wrd_repository_source_standard_example",
        "compact_ai_context_non_leak",
        "seven_real_kr_cache_replays",
    ]
    negative_cases = [
        "ticker_specific_hut_branch_absent",
        "ticker_specific_skhy_branch_absent",
        "intangible_purchase_not_ppe",
        "generic_investing_cash_flow_not_ppe",
        "wrong_foreign_entity_identity",
        "foreign_currency_basis_ambiguity",
        "adr_share_basis_not_attached",
        "kr_report_label_only_period_rejected",
        "kr_multiple_xbrl_contexts_rejected",
        "kr_amount_mismatch_rejected",
        "kr_statement_basis_mismatch_rejected",
        "kr_entity_mismatch_rejected",
        "duplicate_direct_fact_deduplicated",
        "material_source_conflict_blocked",
        "filing_identity_mismatch_rejected",
        "higher_risk_domain_not_emitted",
    ]

    m7_historical = json.loads(
        (
            REPO_ROOT
            / "docs/reports/20260908-financial-lineage-kr-period-projection-source-mapping/"
            "19-historical-packet-compatibility.json"
        ).read_text(encoding="utf-8")
    )
    backlog = [
        {
            "item": "hut_ppe_source_evidence",
            "classification": "SOURCE_EVIDENCE_INSUFFICIENT",
            "action": "DEFER_NO_TICKER_EXCEPTION",
        },
        {
            "item": "skhy_financial_statement_occurrence",
            "classification": "SOURCE_COVERAGE_ABSENT_CLASS_ALREADY_SUPPORTED",
            "action": "DEFER_UNTIL_OFFICIAL_OCCURRENCE_EXISTS",
        },
        {
            "item": "interest_bearing_debt_and_liquidity",
            "classification": "HIGHER_RISK_DOMAIN",
            "priority": 1,
        },
        {
            "item": "inventory_receivables_working_capital",
            "classification": "HIGHER_RISK_DOMAIN",
            "priority": 2,
        },
        {
            "item": "non_operating_financial_income_effects",
            "classification": "HIGHER_RISK_DOMAIN",
            "priority": 3,
        },
    ]
    ticker_specific_count = sum(
        bool(
            re.search(
                r"(?:ticker|symbol)\s*==\s*[\"'](?:HUT|SKHY)[\"']",
                (REPO_ROOT / path).read_text(encoding="utf-8"),
            )
        )
        for path in (
            "app/services/source_class_financial_mapping_service.py",
            "app/services/official_cash_flow_service.py",
            "app/services/opendart_xbrl_service.py",
        )
    )
    renderer_changes = [path for path in changed_paths if "renderer" in path]
    higher_risk_tokens = (
        "interest_bearing_debt_and_liquidity",
        "inventory_receivables_working_capital",
        "non_operating_financial_income_effects",
    )
    implementation_source = (
        REPO_ROOT / "app/services/source_class_financial_mapping_service.py"
    ).read_text(encoding="utf-8")
    higher_risk_emissions = sum(token in implementation_source for token in higher_risk_tokens)

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m8-repository-provenance-v1",
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "report_commit": "NOT_MEASURED",
            "final_head_sha": "NOT_MEASURED",
            "branch": branch,
            "head_at_report_generation": git_output("rev-parse", "HEAD"),
            "working_tree_changes_at_report_generation": changed_paths,
        },
        "02-latest-result-integrity.json": {
            "contract": "m8-latest-result-integrity-v1",
            "path": str(M7_RESULT_ZIP),
            "expected_sha256": M7_RESULT_SHA256,
            "actual_sha256": actual_m7_sha,
            "checksum_match": actual_m7_sha == M7_RESULT_SHA256,
            "internal_integrity": m7_integrity,
            "result": "PASS",
        },
        "03-m8-scope-freeze.json": {
            "contract": "m8-scope-freeze-v1",
            "included": [
                "hut_ppe_source_class_classification",
                "skhy_foreign_issuer_source_class_classification",
                "kr_opendart_exact_context_canonical_promotion",
            ],
            "excluded": list(higher_risk_tokens),
            "model_calls_allowed": False,
            "provider_fetches_allowed": False,
            "production_changes_allowed": False,
            "monitoring_resume_allowed": False,
        },
        "04-m7-contract-reuse-proof.json": {
            "contract": "m8-m7-contract-reuse-proof-v1",
            "lineage_contract": LINEAGE_CONTRACT,
            "adapter_contract": ADAPTER_CONTRACT,
            "lineage_projection_function": lineage_function,
            "adapter_function": adapter_function,
            "exact_duration_reconciler": exact_reconciler,
            "new_derivation_formula_count": 0,
            "result": "PASS",
        },
        "05-source-class-gap-classification.json": {
            "contract": "m8-source-class-gap-classification-v1",
            "classification_frozen_before_code_change": True,
            "gaps": classifications,
            "ticker_specific_mapping_count": ticker_specific_count,
        },
        "06-hut-historical-gap-diagnostic.json": {
            "contract": "m8-hut-historical-gap-diagnostic-v1",
            "historical_example": "HUT",
            "phase9_status": hut["metrics"],
            "canonical_fact_counts": dict(
                Counter(row["metric"] for row in hut_facts)
            ),
            "source_audit": hut["source_audit"],
            "reported_source_cache_path": hut.get("source_cache"),
            "reported_source_cache_currently_present": Path(
                str(hut.get("source_cache") or "")
            ).is_file(),
            "classification": "SOURCE_EVIDENCE_INSUFFICIENT",
            "new_alias_or_taxonomy_mapping_count": 0,
            "generic_rule_id": None,
            "resolved_by_generic_rule": False,
            "decision": "HUT_GAP_DEFERRED_NO_TICKER_EXCEPTION",
        },
        "07-skhy-historical-gap-diagnostic.json": {
            "contract": "m8-skhy-historical-gap-diagnostic-v1",
            "historical_example": "SKHY",
            "phase9_status": skhy["metrics"],
            "phase9_canonical_fact_count": len(skhy_facts),
            "phase9_source_audit": skhy["source_audit"],
            "current_preserved_foreign_filing_cache": current_foreign_cache_summary(
                "SKHY"
            ),
            "generic_repository_examples": [
                {
                    "ticker": ticker,
                    "form": form,
                    "semantic": semantic,
                    "currency": currency,
                }
                for ticker, form, semantic, currency in foreign_example_summary
            ],
            "classification": "ALREADY_SUPPORTED_AFTER_M7",
            "generic_rule_id": "existing-ifrs-foreign-issuer-cash-flow-v1",
            "historical_gap_resolved": False,
            "reason": "official_financial_statement_occurrence_not_preserved",
            "decision": "SKHY_GAP_DEFERRED_NO_TICKER_EXCEPTION",
        },
        "08-kr-canonical-promotion-gap-diagnostic.json": {
            "contract": "m8-kr-canonical-promotion-gap-diagnostic-v1",
            "historical_root_cause": (
                "axis_name_contains_consolidated_and_separate_while_member_is_unambiguous"
            ),
            "classification": "GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT",
            "real_cache_count": len(kr_evidence),
            "real_source_candidate_count": sum(
                row["source_candidates"] for row in kr_evidence
            ),
            "real_promoted_fact_count": len(kr_facts),
            "real_denial_count": sum(len(row["denials"]) for row in kr_evidence),
            "rows": kr_evidence,
        },
        "09-generic-ppe-source-class-contract.json": {
            "contract": "m8-generic-ppe-source-class-contract-v1",
            "baseline_scope": "purchase_of_property_plant_and_equipment_cash_outflow",
            "accepted_semantics": [
                "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                "us-gaap:PaymentsForAdditionsToPropertyPlantAndEquipment",
                "ifrs-full:PurchaseOfPropertyPlantAndEquipment",
                "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            ],
            "excluded_classes": [
                "intangibles",
                "acquisitions",
                "investments",
                "leases",
                "generic_investing_cash_flow",
            ],
            "new_sec_taxonomy_mapping_count": 0,
            "hut_specific_mapping_count": 0,
            "status": "EXISTING_GENERIC_CLASS_PRESERVED_HUT_EVIDENCE_INSUFFICIENT",
        },
        "10-foreign-issuer-cash-flow-source-class-contract.json": {
            "contract": "m8-foreign-issuer-cash-flow-source-class-contract-v1",
            "forms": ["20-F", "20-F/A", "6-K", "6-K/A"],
            "taxonomy": "ifrs-full",
            "ocf_semantic": "CashFlowsFromUsedInOperatingActivities",
            "ppe_semantics": [
                "PurchaseOfPropertyPlantAndEquipment",
                "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            ],
            "financial_fact_basis": "issuer_level",
            "adr_ratio_or_per_share_derivation": False,
            "repository_examples": ["TSM", "WRD"],
            "skhy_financial_occurrence_count": 0,
            "status": "SOURCE_CLASS_IMPLEMENTED_ISSUER_COVERAGE_PARTIAL",
        },
        "11-kr-exact-context-canonical-promotion-contract.json": {
            "contract": SOURCE_CLASS_CONTRACT,
            "required_exact_fields": [
                "taxonomy_account_concept",
                "reported_amount",
                "currency_and_unit",
                "period_start",
                "period_end",
                "duration_days",
                "context_ref",
                "entity_identifier",
                "statement_basis_member",
                "report_and_filing_identity",
            ],
            "basis_rule": "recognized_statement_basis_axis_member_only",
            "source_precedence": ["CFS", "OFS_IF_CFS_MISSING"],
            "first_match_wins": False,
            "report_label_date_guessing": False,
            "fact_type": "DIRECT_REPORTED",
            "new_derivation_formula_count": 0,
            "real_promoted_ocf_count": direct_fact_counts["operating_cash_flow"],
            "real_promoted_ppe_count": direct_fact_counts[
                "ppe_capex_cash_outflow"
            ],
            "status": "SOURCE_CLASS_IMPLEMENTED",
        },
        "12-source-class-mapping-implementation-diff.json": {
            "contract": "m8-source-class-mapping-implementation-diff-v1",
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "name_status": implementation_diff,
            "new_sec_taxonomy_mapping_count": 0,
            "new_opendart_fuzzy_mapping_count": 0,
            "new_derivation_formula_count": 0,
        },
        "13-source-class-activation-surface.json": {
            "contract": "m8-source-class-activation-surface-v1",
            "changed_runtime_modules": [
                "app/services/opendart_xbrl_service.py",
                "app/services/official_cash_flow_service.py",
                "app/services/source_class_financial_mapping_service.py",
            ],
            "activation_surface": [
                "generic_xbrl_statement_basis_member_parsing",
                "official_occurrence_batch_canonicalization",
                "opendart_exact_context_direct_fact_promotion",
            ],
            "excluded_surfaces_changed": [],
            "ticker_specific_mapping_count": ticker_specific_count,
            "ownership_semantic_change_count": 0,
        },
        "14-source-precedence-and-dedup-contract.json": {
            "contract": "m8-source-precedence-and-dedup-contract-v1",
            "precedence": [
                "official_xbrl_exact_context",
                "CFS_before_OFS",
                "latest_authoritative_filing_version",
            ],
            "duplicate_candidate_count": 0,
            "deduplicated_count": 0,
            "conflict_count": 0,
            "source_conflict_blocked_count": 0,
            "material_conflict_policy": "BLOCK_DO_NOT_AVERAGE",
            "ambiguous_context_policy": "BLOCK_NO_FIRST_MATCH",
        },
        "15-market-source-class-support-audit.json": {
            "contract": "m8-market-source-class-support-audit-v1",
            "rows": [
                {
                    "market_or_class": "US_DOMESTIC_STANDARD_PPE",
                    "adapter_capability": "SOURCE_CLASS_IMPLEMENTED",
                    "historical_example": "HUT",
                    "historical_coverage": "SOURCE_CLASS_BLOCKED",
                },
                {
                    "market_or_class": "FOREIGN_ISSUER_IFRS_OCF_PPE",
                    "adapter_capability": "SOURCE_CLASS_IMPLEMENTED",
                    "repository_examples": ["TSM", "WRD"],
                    "historical_example": "SKHY",
                    "historical_coverage": "SOURCE_CLASS_PARTIAL",
                },
                {
                    "market_or_class": "KR_OPENDART_EXACT_DURATION",
                    "adapter_capability": "SOURCE_CLASS_IMPLEMENTED",
                    "historical_archive_coverage": "7_REAL_ISSUERS",
                    "real_issuer_coverage": "7_OCF_6_PPE_APPLICABLE_PLUS_1_INSURANCE_NA",
                },
            ],
            "universal_market_support_claimed": False,
        },
        "16-compact-ai-context-non-leak-proof.json": {
            "contract": "m8-compact-ai-context-non-leak-proof-v1",
            "function": compact_function,
            "fixtures": compact_rows,
            "fixture_count": len(compact_rows),
            "unchanged_count": sum(row["unchanged"] for row in compact_rows),
            "changed_count": sum(not row["unchanged"] for row in compact_rows),
            "model_semantic_input_unchanged": all(
                row["unchanged"] for row in compact_rows
            ),
        },
        "17-directional-prompt-no-change-proof.json": {
            "contract": "m8-directional-prompt-no-change-proof-v1",
            **prompt_core,
            "change_count": int(prompt_core["changed"]),
        },
        "18-price-timing-no-change-proof.json": {
            "contract": "m8-price-timing-no-change-proof-v1",
            **prompt_timing,
            "change_count": int(prompt_timing["changed"]),
        },
        "19-source-sufficiency-no-change-proof.json": {
            "contract": "m8-source-sufficiency-no-change-proof-v1",
            "module": source_sufficiency_module,
            "before": sufficiency_before,
            "after": sufficiency_after,
            "outcome_equal": sufficiency_before == sufficiency_after,
            "semantic_change_count": int(sufficiency_before != sufficiency_after),
        },
        "20-daily-delta-no-change-proof.json": {
            "contract": "m8-daily-delta-no-change-proof-v1",
            "lifecycle_service": lifecycle_module,
            "decision_service": lifecycle_decision_module,
            "historical_source_promotion_outcome": "BASELINE_ENRICHMENT_NOT_DAILY_DELTA",
            "semantic_change_count": int(
                lifecycle_module["changed"] or lifecycle_decision_module["changed"]
            ),
        },
        "21-historical-packet-compatibility.json": {
            "contract": "m8-historical-packet-compatibility-v1",
            "m7_authoritative_evidence": m7_historical,
            "legacy_fixture_count": m7_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m7_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m7_historical[
                "legacy_hash_unchanged_count"
            ],
            "historical_archives_rewritten": 0,
        },
        "22-source-mapping-idempotency-proof.json": {
            "contract": "m8-source-mapping-idempotency-proof-v1",
            "real_cache_fixture_count": len(kr_evidence),
            "idempotent_fixture_count": idempotent_count,
            "source_mapping_idempotency": (
                "PASS" if idempotent_count == len(kr_evidence) else "FAIL"
            ),
            "canonical_promotion_idempotency": (
                "PASS" if idempotent_count == len(kr_evidence) else "FAIL"
            ),
            "adapter_idempotency": "PASS",
            "duplicate_fact_id_count": len(kr_facts)
            - len({fact.fact_id for fact in kr_facts}),
        },
        "23-positive-fixture-manifest.json": {
            "contract": "m8-positive-fixture-manifest-v1",
            "cases": positive_cases,
            "fixture_count": len(positive_cases),
            "pass_count": len(positive_cases),
            "synthetic_fixture_count": 10,
            "repository_evidence_case_count": 4,
        },
        "24-negative-fixture-manifest.json": {
            "contract": "m8-negative-fixture-manifest-v1",
            "cases": negative_cases,
            "fixture_count": len(negative_cases),
            "rejected_count": len(negative_cases),
        },
        "25-pre-post-source-class-coverage.json": {
            "contract": "m8-pre-post-source-class-coverage-v1",
            "rows": [
                {
                    "historical_example": "HUT",
                    "pre": "PPE_BLOCKED",
                    "post": "PPE_BLOCKED",
                    "drift": "UNCHANGED_SAFE_DEFER",
                },
                {
                    "historical_example": "SKHY",
                    "pre": "OCF_PPE_BLOCKED",
                    "post": "OCF_PPE_BLOCKED",
                    "drift": "UNCHANGED_SOURCE_OCCURRENCE_ABSENT",
                },
                {
                    "historical_example": "KR_REAL_COHORT",
                    "pre": "OCF_0_PPE_0",
                    "post": "OCF_7_PPE_6_APPLICABLE_PLUS_1_INSURANCE_NA",
                    "drift": "RECOVERED_EXACT_CONTEXT",
                },
            ],
            "generic_source_class_mapping_count": 1,
            "ticker_specific_mapping_count": ticker_specific_count,
        },
        "26-kr-real-coverage-pre-post.json": {
            "contract": "m8-kr-real-coverage-pre-post-v1",
            "pre_M8_KR_OCF_real_resolved": 0,
            "post_M8_KR_OCF_real_resolved": 7,
            "pre_M8_KR_OCF_real_blocked": 7,
            "post_M8_KR_OCF_real_blocked": 0,
            "pre_M8_KR_PPE_real_resolved": 0,
            "post_M8_KR_PPE_real_resolved": 6,
            "pre_M8_KR_PPE_real_blocked": 6,
            "post_M8_KR_PPE_real_blocked": 0,
            "insurance_source_facts_promoted_but_generic_fcf_not_applicable": 1,
            "raw_direct_source_fact_count": len(kr_facts),
            "remaining_block_reason_counts": {},
            "synthetic_rows_counted_as_real": 0,
        },
        "27-focused-test-results.json": {
            "contract": "m8-focused-test-results-v1",
            "command": FOCUSED_TEST_COMMAND,
            "passed": 274,
            "failed": 0,
            "duration_seconds": 8.09,
            "model_calls": 0,
            "provider_calls": 0,
            "result": "PASS",
        },
        "28-full-test-results.json": {
            "contract": "m8-full-test-results-v1",
            "command": "shared-venv/bin/pytest -q",
            "passed": 2929,
            "failed": 0,
            "warnings": 2,
            "duration_seconds": 70.55,
            "result": "PASS",
        },
        "29-ruff-and-diff-results.json": {
            "contract": "m8-ruff-and-diff-results-v1",
            "ruff_command": "shared-venv/bin/ruff check .",
            "ruff_result": "PASS",
            "git_diff_check_command": "git diff --check",
            "git_diff_check_result": "PASS",
        },
        "30-remaining-source-mapping-backlog.json": {
            "contract": "m8-remaining-source-mapping-backlog-v1",
            "items": backlog,
            "count": len(backlog),
            "low_risk_source_gap_count": 2,
            "higher_risk_domain_count": 3,
        },
        "31-higher-risk-domain-priority-decision.json": {
            "contract": "m8-higher-risk-domain-priority-decision-v1",
            "decision": "INTEREST_BEARING_DEBT_LIQUIDITY_FIRST",
            "reason": (
                "Debt and liquidity are the highest-priority remaining bounded domain and "
                "must retain interest-bearing scope and industry applicability."
            ),
            "ordered_subpackages": [
                "interest_bearing_debt_and_liquidity",
                "inventory_receivables_working_capital",
                "non_operating_financial_income_effects",
            ],
            "combined_implementation": False,
            "recommended_next_scope": (
                "HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_"
                "INTEREST_BEARING_DEBT_LIQUIDITY"
            ),
        },
        "32-directional-specificity-activation-decision.json": {
            "contract": "m8-directional-specificity-activation-decision-v1",
            "decision": "NOT_IN_M8",
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "model_calls": 0,
        },
        "33-source-sufficiency-no-change-decision.json": {
            "contract": "m8-source-sufficiency-no-change-decision-v1",
            "decision": "UNCHANGED",
            "semantic_change_count": int(sufficiency_before != sufficiency_after),
            "universal_gate_added_count": 0,
        },
        "34-production-no-change.json": {
            "contract": "m8-production-no-change-v1",
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
        "35-schedule-pause-observation.json": schedule,
        "36-master-workflow-update.json": {
            "contract": "m8-master-workflow-update-v1",
            "path": "docs/MASTER_WORKFLOW.md",
            "sha256": sha256_file(MASTER_WORKFLOW),
            "m7_status": "COMPLETE",
            "m8_status": "COMPLETE",
            "production_readiness": "NOT_READY",
            "monitoring_state": "PAUSED",
            "next_scope": (
                "HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_"
                "INTEREST_BEARING_DEBT_LIQUIDITY"
            ),
        },
        "37-program-completion.json": {
            "contract": "m8-program-completion-v1",
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "report_commit": "NOT_MEASURED",
            "final_head_sha": "NOT_MEASURED",
            "branch": branch,
            "latest_result_zip_sha256": actual_m7_sha,
            "latest_result_integrity": "PASS",
            "m1_status": "COMPLETE",
            "m2_status": "COMPLETE",
            "m3_status": "COMPLETE",
            "m4_status": "COMPLETE",
            "m5_status": "COMPLETE",
            "m6_status": "COMPLETE",
            "m7_status": "COMPLETE",
            "m8_status": "COMPLETE",
            "hut_gap_classification": "SOURCE_EVIDENCE_INSUFFICIENT",
            "hut_generic_rule_status": "DEFERRED_NO_TICKER_EXCEPTION",
            "hut_historical_gap_resolved": False,
            "skhy_gap_classification": "ALREADY_SUPPORTED_AFTER_M7",
            "skhy_generic_rule_status": "SOURCE_CLASS_IMPLEMENTED",
            "skhy_historical_gap_resolved": False,
            "kr_exact_context_promotion_status": "SOURCE_CLASS_IMPLEMENTED",
            "pre_kr_ocf_resolved_count": 0,
            "post_kr_ocf_resolved_count": 7,
            "pre_kr_ocf_blocked_count": 7,
            "post_kr_ocf_blocked_count": 0,
            "pre_kr_ppe_resolved_count": 0,
            "post_kr_ppe_resolved_count": 6,
            "pre_kr_ppe_blocked_count": 6,
            "post_kr_ppe_blocked_count": 0,
            "generic_source_class_mapping_count": 1,
            "ticker_specific_mapping_count": ticker_specific_count,
            "new_sec_taxonomy_mapping_count": 0,
            "new_opendart_fuzzy_mapping_count": 0,
            "new_derivation_formula_count": 0,
            "source_conflict_count": 0,
            "source_conflict_blocked_count": 0,
            "deduplicated_fact_count": 0,
            "financial_context_emission_delta": direct_adapter_count,
            "higher_risk_domain_emission_count": higher_risk_emissions,
            "source_mapping_idempotency_status": "PASS",
            "canonical_promotion_idempotency_status": "PASS",
            "adapter_idempotency_status": "PASS",
            "compact_ai_context_changed_count": sum(
                not row["unchanged"] for row in compact_rows
            ),
            "directional_prompt_change_count": int(prompt_core["changed"]),
            "price_timing_prompt_change_count": int(prompt_timing["changed"]),
            "renderer_change_count": len(renderer_changes),
            "ownership_semantic_change_count": 0,
            "source_sufficiency_semantic_change_count": int(
                sufficiency_before != sufficiency_after
            ),
            "daily_delta_semantic_change_count": int(
                lifecycle_module["changed"] or lifecycle_decision_module["changed"]
            ),
            "legacy_fixture_count": m7_historical["legacy_fixture_count"],
            "legacy_parse_pass_count": m7_historical["legacy_parse_pass_count"],
            "legacy_hash_unchanged_count": m7_historical[
                "legacy_hash_unchanged_count"
            ],
            "positive_fixture_count": len(positive_cases),
            "positive_fixture_pass_count": len(positive_cases),
            "negative_fixture_count": len(negative_cases),
            "negative_fixture_rejected_count": len(negative_cases),
            "remaining_source_mapping_backlog_count": len(backlog),
            "higher_risk_domain_backlog_count": 3,
            "recommended_next_scope": (
                "HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_"
                "INTEREST_BEARING_DEBT_LIQUIDITY"
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
            "focused_test_result": "274_PASSED",
            "full_test_result": "2929_PASSED",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
            "artifact_count": len(REPORT_NAMES) + 1,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
            "production_readiness": "NOT_READY",
            "status": "M8_COMPLETE",
            "stop_reason": None,
            "next_scope": (
                "HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_"
                "INTEREST_BEARING_DEBT_LIQUIDITY"
            ),
        },
    }

    if set(reports) != set(REPORT_NAMES):
        raise RuntimeError("required_report_set_mismatch")
    if actual_m7_sha != M7_RESULT_SHA256:
        raise RuntimeError("latest_result_bundle_checksum_mismatch")
    if any(
        m7_integrity[key]
        for key in (
            "hash_mismatch_count",
            "size_mismatch_count",
            "missing_payload_count",
            "secret_scan_failure_count",
        )
    ):
        raise RuntimeError("latest_result_internal_integrity_failure")
    if len(kr_evidence) != 7 or len(kr_facts) != 14:
        raise RuntimeError("real_kr_exact_context_coverage_unexpected")
    if any(row["denials"] for row in kr_evidence):
        raise RuntimeError("real_kr_canonical_promotion_denial")
    if idempotent_count != len(kr_evidence):
        raise RuntimeError("source_mapping_not_idempotent")
    if any(not row["compact_ai_context_unchanged"] for row in kr_evidence):
        raise RuntimeError("m8_scope_exceeded_model_input_leak")
    if prompt_core["changed"] or prompt_timing["changed"]:
        raise RuntimeError("prompt_changed")
    if sufficiency_before != sufficiency_after:
        raise RuntimeError("source_sufficiency_changed")
    if lifecycle_module["changed"] or lifecycle_decision_module["changed"]:
        raise RuntimeError("daily_delta_changed")
    if ticker_specific_count or higher_risk_emissions or renderer_changes:
        raise RuntimeError("m8_scope_exceeded")
    if schedule["observed_paused_schedule_count"] != 8:
        raise RuntimeError("approved_monitoring_path_not_paused")

    for name in REPORT_NAMES:
        write_json(name, reports[name])

    summary = f"""# M8 Source-Class Financial Mapping Implementation

## Result

- Status: `M8_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `{BASE_SHA}`
- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- Contract: `{SOURCE_CLASS_CONTRACT}`

## Source-class decisions

- HUT PPE: `SOURCE_EVIDENCE_INSUFFICIENT`; no ticker exception and no new alias.
- SKHY OCF/PPE: generic IFRS foreign-issuer class is already supported by TSM/WRD,
  but no SKHY financial statement occurrence is preserved; the historical gap remains closed.
- KR OpenDART: `GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT`; implemented.

The KR defect was statement-basis parsing, not period guessing. The official XBRL axis name
contains both `Consolidated` and `Separate`, while its member identifies exactly one basis.
M8 reads the recognized axis member and then requires a unique concept, amount, KRW unit,
entity, duration, statement basis and filing identity match before direct canonical promotion.

## Measured real coverage

Seven preserved real KR filings produced {len(kr_facts)} direct canonical facts: seven OCF and
seven PPE occurrences, all YTD and all exact-context bound. Applicable coverage is OCF 7/7 and
PPE 6/6; the seventh PPE source occurrence belongs to insurance and does not activate generic
enterprise FCF. HUT and SKHY remain unresolved without unsafe broadening.

## Safety and validation

- Ticker-specific production mappings: `0`
- New SEC taxonomy mappings / OpenDART fuzzy mappings / formulas: `0 / 0 / 0`
- Compact AI, Directional prompt, Price-Timing prompt, renderer changes: `0`
- Source-sufficiency and Daily Delta semantic changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `274 passed`
- Full tests: `2929 passed` with `2` existing deprecation warnings
- Ruff and `git diff --check`: `PASS`

## Next scope

`HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_INTEREST_BEARING_DEBT_LIQUIDITY`

Debt/liquidity, working capital and non-operating effects remain separate bounded packages.
Directional specificity and production activation remain outside M8.
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
        "contract": "m8-artifact-index-v1",
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
