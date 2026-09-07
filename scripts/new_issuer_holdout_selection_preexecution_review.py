from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any

from app.services.coldstart_source_assembly_service import deterministic_base_context
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    TIMING_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    PriceTimingCandidate,
    canonical_sha256,
    core_fingerprint,
)
from app.services.reference_universe_audit_service import canonical_market_mix
from app.services.structured_autonomy_shadow_service import (
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
)
from scripts import bounded_us_universe_expansion_issuer_reconciliation as universe_audit
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_identity_binding as runtime_identity
from scripts import runtime_identity_lock_repair_fullpath_preflight as identity_repair


PROGRAM_CONTRACT = "new-issuer-holdout-selection-preexecution-readiness-review-v1"
INPUT_ZIP_NAME = (
    "thesis-monitor-20260907-bounded-us-supported-universe-expansion-"
    "issuer-audit-reconciliation-report.zip"
)
INPUT_ZIP_SHA256 = "12ed21a8fcd378036fb86e08193fcffb5b3e0f9f0710f92602a2f3c595c18cf4"
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-new-issuer-holdout-selection-and-preexecution-readiness-review.md"
)
WORK_INSTRUCTION_SHA256 = "d77ef5b3d30089520f3123536a432cf796471c54c014156e3e0bf5c33e23f328"
POLICY_PATH = "docs/reports/20260907-new-issuer-selection-preexecution-review-policy.json"
POLICY_RAW_SHA256 = "2367c91d38a068c2208d3017bb483c173e881f664d6f963a4797d7a6c1bbc86f"
REPORT_DIRECTORY = "20260907-new-issuer-holdout-selection-preexecution-readiness-review"
RESULT_ZIP_NAME = (
    "thesis-monitor-20260907-new-issuer-holdout-selection-"
    "preexecution-readiness-review-report.zip"
)
TARGET_US = 4
TARGET_KR = 12
RUNS = ("first", "a", "b", "c")
STAGES = ("DIRECTIONAL_CORE", "PRICE_TIMING")
MODEL_FREE_ARTIFACT_MODE = "MODEL_FREE_REAL_INPUT_REHEARSAL"

REPORT_NAMES = (
    "01-input-integrity-and-repository-provenance",
    "02-accepted-latest-baseline-and-final-completion-authority",
    "03-production-isolation-and-change-boundary",
    "04-review-policy-and-request-budgets",
    "05-exclusion-registry-continuity-and-alias-fence",
    "06-supported-universe-snapshot-and-set-invariants",
    "07-us-primary-reserve-status-reconciliation",
    "08-kr-candidate-and-reserve-status-review",
    "09-us-source-period-provenance-and-readiness-review",
    "10-kr-source-period-provenance-and-readiness-review",
    "11-dual-market-selection-review-decision",
    "12-proposed-cohort-and-context-grouping",
    "13-nonexecutable-source-review-manifest",
    "14-packet-raw-and-canonical-hash-audit",
    "15-runtime-identity-and-explicit-market-preflight",
    "16-model-free-fullpath-and-fixture-mode-audit",
    "17-guard-lifecycle-and-preservation-readiness",
    "18-tests-lint-diff-and-freeze",
    "19-production-no-change-and-zero-model-counters",
    "20-next-proof-handoff-draft",
    "21-program-completion",
)

CRITICAL_INPUT_MEMBERS = (
    "reports/proofs/24-program-completion.json",
    "reports/proofs/23-next-holdout-selection-handoff.json",
    "evidence/membership/exclusion-registry.json",
    "evidence/membership/us-reference-membership.jsonl",
    "evidence/membership/kr-reference-membership.jsonl",
    "evidence/membership/us-set-reconciliation.json",
    "evidence/membership/kr-set-reconciliation.json",
    "evidence/diagnostics/us-source-readiness.json",
    "evidence/diagnostics/kr-source-readiness.json",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    rows = []
    for line in archive.read(member).decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"zip_jsonl_object_required:{member}")
        rows.append(value)
    return rows


def _summary_value(value: object) -> str:
    if isinstance(value, list):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict):
        if len(value) > 12:
            return f"{len(value)} keys; sha256={canonical_sha256(value)}"
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def markdown_report(name: str, proof: Mapping[str, object]) -> str:
    rows = [
        f"| {str(key).replace('|', '/')} | {_summary_value(value).replace('|', '/')} |"
        for key, value in proof.items()
    ]
    return f"# {name}\n\n| Field | Value |\n| --- | --- |\n" + "\n".join(rows) + "\n"


def write_proof(report_dir: Path, number: int, proof: Mapping[str, object]) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(report_dir / "proofs" / f"{name}.json", proof)
    write_text(report_dir / f"{name}.md", markdown_report(name, proof))


def verify_input_bundle(path: Path) -> dict[str, object]:
    if path.name != INPUT_ZIP_NAME:
        raise ValueError("input_zip_name_mismatch")
    actual_sha = file_sha256(path)
    if actual_sha != INPUT_ZIP_SHA256:
        raise ValueError("input_zip_sha256_mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        unsafe = sorted(
            name
            for name in names
            if name.startswith("/")
            or "\\" in name
            or ".." in PurePosixPath(name).parts
        )
        crc_failure = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("input_artifact_index_rows_missing")
        indexed = {
            str(row["path"]): row
            for row in rows
            if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        indexed_names = set(indexed)
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        for name in sorted(payload_names & indexed_names):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("byte_size"):
                size_mismatches.append(name)
        completion = zip_json(archive, "reports/proofs/24-program-completion.json")
    missing_from_index = sorted(payload_names - indexed_names)
    missing_from_payload = sorted(indexed_names - payload_names)
    status = (
        "PASS"
        if not duplicates
        and not unsafe
        and crc_failure is None
        and not missing_from_index
        and not missing_from_payload
        and not hash_mismatches
        and not size_mismatches
        and completion.get("final_head_sha")
        == "edd24c8bd0bf1d79d8bd49a875bf609eb90752eb"
        else "FAIL"
    )
    result = {
        "contract": "selection-review-input-bundle-integrity-v1",
        "input_zip": str(path),
        "input_zip_sha256": actual_sha,
        "member_count": len(names),
        "duplicate_member_count": len(duplicates),
        "unsafe_path_count": len(unsafe),
        "crc_status": "PASS" if crc_failure is None else f"FAIL:{crc_failure}",
        "indexed_payload_count": len(indexed),
        "actual_payload_count": len(payload_names),
        "missing_from_index": missing_from_index,
        "missing_from_payload": missing_from_payload,
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "final_completion_authority_member": (
            "reports/proofs/24-program-completion.json"
        ),
        "final_completion_head": completion.get("final_head_sha"),
        "status": status,
    }
    if status != "PASS":
        raise ValueError(f"input_bundle_integrity_failed:{result}")
    return result


def _membership_by_symbol(
    rows: Sequence[Mapping[str, object]], market: str
) -> dict[str, Mapping[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        if row.get("market") != market:
            continue
        grouped.setdefault(str(row.get("display_symbol")), []).append(row)
    resolved: dict[str, Mapping[str, object]] = {}
    for symbol, matches in grouped.items():
        eligible = [
            row
            for row in matches
            if row.get("eligibility_decision") == "ELIGIBLE_SUPPORTED_SECURITY"
        ]
        if len(eligible) == 1:
            resolved[symbol] = eligible[0]
        elif len(matches) == 1:
            resolved[symbol] = matches[0]
    return resolved


def diagnostic_member(market: str, row: Mapping[str, object]) -> str:
    return (
        f"evidence/diagnostic-packets/{market}/"
        f"{int(row['rank']):02d}-{row['ticker']}-diagnostic.json"
    )


def full_packet_member(market: str, row: Mapping[str, object]) -> str:
    return (
        f"evidence/diagnostic-packets/{market}/"
        f"{int(row['rank']):02d}-{row['ticker']}-full.json"
    )


def build_candidate_ledger(
    *,
    market: str,
    ordered_tickers: Sequence[str],
    membership_rows: Sequence[Mapping[str, object]],
    diagnostic_rows: Sequence[Mapping[str, object]],
    excluded_issuer_keys: set[str],
    target: int,
    diagnostic_snapshot: str,
) -> tuple[list[dict[str, object]], tuple[str, ...]]:
    membership = _membership_by_symbol(membership_rows, market)
    diagnostics = {str(row["ticker"]): row for row in diagnostic_rows}
    selected: list[str] = []
    ledger: list[dict[str, object]] = []
    seen_issuers: set[str] = set()
    for rank, ticker in enumerate(ordered_tickers, start=1):
        reference = membership.get(ticker)
        if reference is None:
            raise ValueError(f"candidate_reference_missing:{market}:{ticker}")
        issuer = str(reference.get("canonical_issuer_key") or "")
        if not issuer or issuer in seen_issuers:
            raise ValueError(f"candidate_issuer_missing_or_duplicate:{market}:{ticker}")
        seen_issuers.add(issuer)
        if issuer in excluded_issuer_keys:
            raise ValueError(f"excluded_issuer_in_candidate_order:{market}:{ticker}")
        if reference.get("eligibility_decision") != "ELIGIBLE_SUPPORTED_SECURITY":
            raise ValueError(f"unsupported_candidate_in_order:{market}:{ticker}")
        diagnostic = diagnostics.get(ticker)
        sufficient = bool(
            diagnostic and diagnostic.get("fundamental_source_sufficient") is True
        )
        if diagnostic is None:
            source_status = "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED"
        elif sufficient:
            source_status = "FUNDAMENTAL_SOURCE_SUFFICIENT"
        else:
            source_status = "FUNDAMENTAL_SOURCE_FAILED"
        is_primary = sufficient and len(selected) < target
        if is_primary:
            selected.append(ticker)
            reserve_role = "PROPOSED_PRIMARY"
        elif source_status == "FUNDAMENTAL_SOURCE_FAILED":
            reserve_role = "NONPRIMARY_KNOWN_SOURCE_FAILURE"
        elif source_status == "FUNDAMENTAL_SOURCE_SUFFICIENT":
            reserve_role = "FUNDAMENTAL_SOURCE_SUFFICIENT_NOT_PRIMARY"
        else:
            reserve_role = "IDENTITY_SUPPORTED_RESERVE_UNTESTED"
        artifact_references = [
            f"evidence/membership/{market}-reference-membership.jsonl",
            "reports/proofs/23-next-holdout-selection-handoff.json",
        ]
        if diagnostic is not None:
            artifact_references.append(diagnostic_member(market, diagnostic))
            if diagnostic.get("full_packet_sha256"):
                artifact_references.append(full_packet_member(market, diagnostic))
        ledger.append(
            {
                "market": market,
                "rank": rank,
                "ticker": ticker,
                "canonical_issuer_key": issuer,
                "canonical_security_id": reference.get("canonical_security_id"),
                "representative_rule": (
                    "supported common/ordinary; non-ADR preferred; then canonical ID"
                ),
                "source_status": source_status,
                "last_evaluation_snapshot": (
                    diagnostic_snapshot if diagnostic is not None else None
                ),
                "reserve_role": reserve_role,
                "failure_reasons": list(
                    diagnostic.get("failure_reasons") or []
                    if diagnostic is not None
                    else []
                ),
                "diagnostic_packet_sha256": (
                    diagnostic.get("diagnostic_packet_sha256")
                    if diagnostic is not None
                    else None
                ),
                "full_packet_sha256": (
                    diagnostic.get("full_packet_sha256")
                    if diagnostic is not None
                    else None
                ),
                "price_timing_readiness": (
                    diagnostic.get("price_timing_input_readiness")
                    if diagnostic is not None
                    else "NOT_MEASURED"
                ),
                "artifact_references": artifact_references,
            }
        )
    if len(selected) != target:
        raise ValueError(f"selection_target_not_met:{market}:{len(selected)}:{target}")
    return ledger, tuple(selected)


def summarize_us_ledger(
    rows: Sequence[Mapping[str, object]], *, budget_scope: int = 24
) -> dict[str, int]:
    global_untested = sum(
        row.get("source_status") == "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED"
        for row in rows
    )
    within_budget_untested = sum(
        row.get("source_status") == "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED"
        for row in rows[:budget_scope]
    )
    return {
        "unseen_supported_count": len(rows),
        "source_pass_count": sum(
            row.get("source_status") == "FUNDAMENTAL_SOURCE_SUFFICIENT"
            for row in rows
        ),
        "known_source_fail_count": sum(
            row.get("source_status") == "FUNDAMENTAL_SOURCE_FAILED" for row in rows
        ),
        "untested_global_count": global_untested,
        "untested_within_budget_count": within_budget_untested,
        "identity_supported_nonprimary_count": sum(
            row.get("reserve_role") != "PROPOSED_PRIMARY" for row in rows
        ),
        "source_sufficient_reserve_count": sum(
            row.get("reserve_role")
            == "FUNDAMENTAL_SOURCE_SUFFICIENT_NOT_PRIMARY"
            for row in rows
        ),
    }


def validate_set_reconciliation(document: Mapping[str, object]) -> dict[str, object]:
    security_ids = {str(value) for value in document.get("supported_security_ids") or []}
    issuer_keys = {str(value) for value in document.get("supported_issuer_keys") or []}
    exclusion_keys = {
        str(value) for value in document.get("global_exclusion_issuer_keys") or []
    }
    within_keys = {
        str(value)
        for value in document.get("within_universe_exclusion_issuer_keys") or []
    }
    unseen_keys = {
        str(value) for value in document.get("unseen_supported_issuer_keys") or []
    }
    recorded_invariants = document.get("invariants")
    recorded_invariants = (
        recorded_invariants if isinstance(recorded_invariants, Mapping) else {}
    )
    checks = {
        "supported_security_count": len(security_ids)
        == document.get("supported_security_count"),
        "supported_issuer_count": len(issuer_keys)
        == document.get("supported_issuer_count"),
        "within_universe_exclusion_count": len(within_keys)
        == document.get("within_universe_exclusion_issuer_count"),
        "unseen_supported_issuer_count": len(unseen_keys)
        == document.get("unseen_supported_issuer_count"),
        "within_is_supported_intersection_exclusions": within_keys
        == issuer_keys & exclusion_keys,
        "unseen_is_supported_minus_exclusions": unseen_keys
        == issuer_keys - exclusion_keys,
        "issuer_lte_security": len(issuer_keys) <= len(security_ids),
        "unseen_lte_supported_issuer": len(unseen_keys) <= len(issuer_keys),
        "unseen_intersection_exclusions_empty": not unseen_keys & exclusion_keys,
        "recorded_invariants_true": bool(recorded_invariants)
        and all(value is True for value in recorded_invariants.values()),
    }
    return {
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def _source_fact_rows(packet: Mapping[str, object]) -> list[dict[str, object]]:
    stocks = packet.get("stocks")
    if not isinstance(stocks, list) or len(stocks) != 1:
        raise ValueError("single_stock_packet_required")
    stock = stocks[0]
    if not isinstance(stock, Mapping):
        raise ValueError("stock_object_required")
    facts = stock.get("fact_catalog")
    if not isinstance(facts, list):
        raise ValueError("fact_catalog_required")
    result = []
    allowed_families = {
        "IDENTITY_SECURITY",
        "BUSINESS_CURRENT",
        "EARNINGS_FINANCIAL_CURRENT",
        "LIQUIDITY_CASHFLOW_CURRENT",
        "SECTOR_OPERATING_CURRENT",
        "REGULATORY_CAPITAL_CURRENT",
    }
    for fact in facts:
        if not isinstance(fact, Mapping) or fact.get("evidence_family") not in allowed_families:
            continue
        fields = fact.get("fields") if isinstance(fact.get("fields"), Mapping) else {}
        result.append(
            {
                "fact_id": fact.get("fact_id"),
                "evidence_family": fact.get("evidence_family"),
                "source": fact.get("source"),
                "source_document_id": fact.get("source_document_id"),
                "as_of_date": fact.get("as_of_date"),
                "filing_date": fields.get("filing_date"),
                "period": fields.get("period"),
                "period_type": fields.get("period_type"),
                "period_end": fields.get("period_end"),
                "entity_scope": fields.get("entity_scope"),
                "statement_basis": fields.get("statement_basis"),
                "security_basis": fields.get("security_basis"),
                "currency": fields.get("currency"),
                "source_payload_sha256": fact.get("source_payload_sha256"),
            }
        )
    return result


def packet_source_review(
    *,
    archive: zipfile.ZipFile,
    market: str,
    candidate: Mapping[str, object],
    diagnostic: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, Any]]:
    full_member = full_packet_member(market, diagnostic)
    diagnostic_path = diagnostic_member(market, diagnostic)
    full_bytes = archive.read(full_member)
    diagnostic_bytes = archive.read(diagnostic_path)
    packet = json.loads(full_bytes)
    diagnostic_packet = json.loads(diagnostic_bytes)
    if not isinstance(packet, dict) or not isinstance(diagnostic_packet, dict):
        raise ValueError(f"packet_object_required:{candidate['ticker']}")
    embedded_diagnostic_hash = diagnostic_packet.pop("diagnostic_packet_sha256", None)
    diagnostic_canonical = canonical_sha256(diagnostic_packet)
    full_canonical = canonical_sha256(packet)
    stock = packet.get("stocks", [{}])[0]
    if not isinstance(stock, Mapping):
        raise ValueError("stock_object_required")
    source_assembly = packet.get("source_assembly")
    source_assembly = source_assembly if isinstance(source_assembly, Mapping) else {}
    source_sufficiency = packet.get("source_sufficiency")
    source_sufficiency = (
        source_sufficiency if isinstance(source_sufficiency, Mapping) else {}
    )
    source_facts = _source_fact_rows(packet)
    valid_families = set(source_sufficiency.get("valid_families") or [])
    required_family_ready = {
        "IDENTITY_SECURITY",
        "BUSINESS_CURRENT",
        "EARNINGS_FINANCIAL_CURRENT",
    }.issubset(valid_families)
    hash_status = (
        "PASS"
        if full_canonical == diagnostic.get("full_packet_sha256")
        and diagnostic_canonical == embedded_diagnostic_hash
        and embedded_diagnostic_hash == diagnostic.get("diagnostic_packet_sha256")
        else "FAIL"
    )
    period_rows = [
        row
        for row in source_facts
        if row.get("period") or row.get("filing_date") or row.get("source_document_id")
    ]
    technical_status = str(source_assembly.get("technical_context_status") or "NOT_MEASURED")
    unknowns = [str(value) for value in stock.get("unknowns") or []]
    mandatory_unknowns = [
        *unknowns,
        "original_raw_official_provider_response_bytes_not_bundled",
    ]
    if technical_status == "PARTIAL_SAFE":
        mandatory_unknowns.append("technical_context_partial_safe_features_may_be_unavailable")
    review = {
        "ticker": candidate["ticker"],
        "market": market,
        "canonical_issuer_key": candidate["canonical_issuer_key"],
        "canonical_security_id": candidate["canonical_security_id"],
        "assessment_date": packet.get("assessment_date"),
        "packet_generated_at": packet.get("generated_at"),
        "packet_market": packet.get("market"),
        "packet_id": packet.get("packet_id"),
        "full_packet_member": full_member,
        "diagnostic_packet_member": diagnostic_path,
        "full_packet_raw_sha256": bytes_sha256(full_bytes),
        "full_packet_raw_bytes": len(full_bytes),
        "full_packet_canonical_sha256": full_canonical,
        "diagnostic_packet_raw_sha256": bytes_sha256(diagnostic_bytes),
        "diagnostic_packet_raw_bytes": len(diagnostic_bytes),
        "diagnostic_packet_canonical_sha256": diagnostic_canonical,
        "source_payload_sha256": diagnostic.get("source_payload_sha256"),
        "raw_provider_response_archive_state": "NOT_BUNDLED_NORMALIZED_FACTS_ONLY",
        "source_request_lineage": list(diagnostic.get("source_request_lineage") or []),
        "source_facts": source_facts,
        "source_period_rows": period_rows,
        "source_sufficiency_status": source_sufficiency.get("status"),
        "required_family_ready": required_family_ready,
        "price_context_readiness": source_assembly.get("price_context_readiness"),
        "price_timing_readiness": source_assembly.get("price_timing_readiness"),
        "technical_context_status": technical_status,
        "security_accounting_basis_status": diagnostic.get(
            "security_accounting_basis_status"
        ),
        "mandatory_unknowns": list(dict.fromkeys(mandatory_unknowns)),
        "hash_status": hash_status,
        "status": (
            "PASS"
            if hash_status == "PASS"
            and packet.get("market") == market
            and stock.get("ticker") == candidate["ticker"]
            and required_family_ready
            and diagnostic.get("fundamental_source_sufficient") is True
            else "FAIL"
        ),
    }
    hash_row = {
        "ticker": candidate["ticker"],
        "market": market,
        "full_packet_raw_sha256": review["full_packet_raw_sha256"],
        "full_packet_canonical_sha256": full_canonical,
        "expected_full_packet_canonical_sha256": diagnostic.get("full_packet_sha256"),
        "diagnostic_packet_raw_sha256": review["diagnostic_packet_raw_sha256"],
        "diagnostic_packet_canonical_sha256": diagnostic_canonical,
        "expected_diagnostic_packet_canonical_sha256": diagnostic.get(
            "diagnostic_packet_sha256"
        ),
        "raw_and_canonical_hashes_intentionally_distinct": (
            review["full_packet_raw_sha256"] != full_canonical
            and review["diagnostic_packet_raw_sha256"] != diagnostic_canonical
        ),
        "status": hash_status,
    }
    return review, hash_row, packet


def build_review_manifest(
    *,
    implementation_commit: str,
    policy_hash: str,
    input_zip_sha256: str,
    selected_rows: Sequence[Mapping[str, object]],
    source_reviews: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    cohort = [str(row["ticker"]) for row in selected_rows]
    groups = [cohort[index : index + 4] for index in range(0, len(cohort), 4)]
    market_by_ticker = {str(row["ticker"]): str(row["market"]) for row in selected_rows}
    if [canonical_market_mix(group, market_by_ticker) for group in groups] != [
        {"us": 4, "kr": 0},
        {"us": 0, "kr": 4},
        {"us": 0, "kr": 4},
        {"us": 0, "kr": 4},
    ]:
        raise ValueError("proposed_context_market_grouping_invalid")
    document: dict[str, object] = {
        "contract": "new-issuer-selection-review-manifest-v1",
        "artifact_role": "SELECTION_REVIEW_MANIFEST",
        "executable": False,
        "model_execution_authorized": False,
        "proof_source_lock": None,
        "selection_status": "PROPOSED_REVIEWED",
        "execution_authorized": False,
        "implementation_commit": implementation_commit,
        "selection_policy_sha256": policy_hash,
        "input_zip_sha256": input_zip_sha256,
        "proposed_cohort": cohort,
        "proposed_context_grouping": groups,
        "market_by_ticker": market_by_ticker,
        "subjects": [
            {
                **dict(row),
                "source_periods": source_reviews[str(row["ticker"])][
                    "source_period_rows"
                ],
                "full_packet_raw_sha256": source_reviews[str(row["ticker"])][
                    "full_packet_raw_sha256"
                ],
                "full_packet_canonical_sha256": source_reviews[str(row["ticker"])][
                    "full_packet_canonical_sha256"
                ],
                "mandatory_unknowns": source_reviews[str(row["ticker"])][
                    "mandatory_unknowns"
                ],
            }
            for row in selected_rows
        ],
        "proposed_cohort_output_exposure_state": "UNEXPOSED",
        "proposed_cohort_semantic_revelation_state": "NOT_MEASURED",
        "holdout_activation_state": "NOT_ACTIVATED_REVIEW_ONLY",
        "future_unseen_eligibility": "CONDITIONAL_ON_PRE_EXECUTION_RECHECK",
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "hash_basis": "canonical JSON excluding source_manifest_sha256",
    }
    document["source_manifest_sha256"] = canonical_sha256(document)
    return document


def validate_review_manifest(document: Mapping[str, object]) -> None:
    without_hash = dict(document)
    recorded = without_hash.pop("source_manifest_sha256", None)
    errors = []
    if document.get("artifact_role") != "SELECTION_REVIEW_MANIFEST":
        errors.append("artifact_role")
    if document.get("executable") is not False:
        errors.append("executable")
    if document.get("model_execution_authorized") is not False:
        errors.append("model_execution_authorized")
    if document.get("proof_source_lock") is not None:
        errors.append("proof_source_lock")
    if recorded != canonical_sha256(without_hash):
        errors.append("source_manifest_sha256")
    if errors:
        raise ValueError(f"review_manifest_invalid:{','.join(errors)}")


def _first_owned_ref(
    owned: OwnedEvidencePacket,
    domains: Sequence[EvidenceDomain],
) -> str | None:
    for domain in domains:
        match = next(
            (row.ref.ref_id for row in owned.evidence if row.domain == domain),
            None,
        )
        if match is not None:
            return match
    return None


def _replace_exact_strings(value: object, replacements: Mapping[str, str]) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _replace_exact_strings(child, replacements)
            for key, child in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_replace_exact_strings(child, replacements) for child in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


def real_input_fixture_core(owned: OwnedEvidencePacket) -> DirectionalCoreCandidate:
    ticker = owned.source_packet.ticker
    business = _first_owned_ref(
        owned,
        (EvidenceDomain.BUSINESS_CURRENT, EvidenceDomain.SECTOR_OPERATING_CURRENT),
    )
    earnings = _first_owned_ref(
        owned,
        (
            EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT,
        ),
    )
    risk = _first_owned_ref(
        owned,
        (
            EvidenceDomain.STRUCTURAL_RISK,
            EvidenceDomain.DATA_QUALITY_LIMIT,
            EvidenceDomain.MARKET_EXPECTATIONS,
        ),
    )
    unknown = _first_owned_ref(
        owned,
        (EvidenceDomain.DATA_QUALITY_LIMIT, EvidenceDomain.MARKET_EXPECTATIONS),
    )
    if any(ref is None for ref in (business, earnings, risk, unknown)):
        raise ValueError(f"model_free_core_fixture_domain_missing:{ticker}")
    template = identity_repair._localized_core(owned).model_dump(mode="json")
    replacements = {
        f"fictional:{ticker}:business": str(business),
        f"fictional:{ticker}:earnings": str(earnings),
        f"fictional:{ticker}:risk": str(risk),
        f"fictional:{ticker}:unknown": str(unknown),
    }
    return DirectionalCoreCandidate.model_validate(
        _replace_exact_strings(template, replacements)
    )


def real_input_fixture_timing(
    owned: OwnedEvidencePacket,
    core: DirectionalCoreCandidate,
) -> PriceTimingCandidate:
    ticker = owned.source_packet.ticker
    support = _first_owned_ref(
        owned,
        (EvidenceDomain.SUPPORT_RESISTANCE, EvidenceDomain.PRICE_CONTEXT),
    )
    technical = _first_owned_ref(
        owned,
        (
            EvidenceDomain.TECHNICAL_STATE,
            EvidenceDomain.OHLCV_TECHNICAL,
            EvidenceDomain.PRICE_CONTEXT,
        ),
    )
    supply = _first_owned_ref(owned, (EvidenceDomain.SUPPLY_POSITIONING,))
    if support is None or technical is None:
        raise ValueError(f"model_free_timing_fixture_domain_missing:{ticker}")
    template = identity_repair._localized_timing(owned, core).model_dump(mode="json")
    replacements = {
        f"fictional:{ticker}:support": support,
        f"fictional:{ticker}:rsi": technical,
    }
    if supply is None:
        template["supply_positioning_rationale"] = None
    else:
        replacements[f"fictional:{ticker}:supply"] = supply
    return PriceTimingCandidate.model_validate(
        _replace_exact_strings(template, replacements)
    )


class RealInputModelFreeAdapter(identity_repair.ModelFreeTerminalAdapter):
    def invoke(self, **kwargs: object) -> dict[str, object]:
        prompt = Path(str(kwargs["prompt"]))
        schema = Path(str(kwargs["schema"]))
        output = Path(str(kwargs["output"]))
        log = Path(str(kwargs["log"]))
        invocation_id = str(kwargs["invocation_id"])
        stage = str(kwargs["stage"])
        batch_id = str(kwargs["batch_id"])
        prompt_identity = runtime_identity.prompt_identity(
            prompt.read_text(encoding="utf-8")
        )
        tickers = tuple(str(value) for value in prompt_identity["tickers"])
        schema_value = read_json(schema)
        if runtime_identity.schema_packet_id(schema_value) != self.continuation_generation:
            raise ValueError("simulated_terminal_received_stale_schema")
        if runtime_identity.schema_subjects(schema_value) != tickers:
            raise ValueError("simulated_terminal_subject_constraint_mismatch")
        if stage == "DIRECTIONAL_CORE":
            candidates = [
                identity_repair._reference_to_alias(
                    real_input_fixture_core(self.owned[ticker]).model_dump(mode="json"),
                    self.core_aliases[ticker].by_ref,
                )
                for ticker in tickers
            ]
        elif stage == "PRICE_TIMING":
            candidates = []
            for ticker in tickers:
                core = real_input_fixture_core(self.owned[ticker])
                candidate = real_input_fixture_timing(
                    self.owned[ticker], core
                ).model_dump(mode="json")
                candidates.append(
                    identity_repair._reference_to_alias(
                        candidate,
                        self.timing_aliases[ticker].by_ref,
                    )
                )
        else:
            raise ValueError(f"unsupported_simulated_stage:{stage}")
        document = {
            "contract": prompt_identity["contract"],
            "packet_id": self.continuation_generation,
            "candidates": candidates,
        }
        write_json(output, document)
        write_text(log, f"{MODEL_FREE_ARTIFACT_MODE}\n")
        self.receipt_root.mkdir(parents=True, exist_ok=True)
        receipt_path = runner.receipt_source_path(self.receipt_root, invocation_id)
        receipt = {
            "contract": "codex-transport-lifecycle-v1",
            "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
            "synthetic_adapter_output": True,
            "real_investment_output": False,
            "real_model_invocations": 0,
            "generation_id": self.continuation_generation,
            "invocation_id": invocation_id,
            "stage": stage,
            "batch_id": batch_id,
            "subject_count": len(tickers),
            "model": runner.MODEL,
            "reasoning_effort": runner.EFFORT,
            "configured_timeout_seconds": runner.TIMEOUT_SECONDS,
            "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
            "input_bytes": prompt.stat().st_size,
            "prompt_sha256": file_sha256(prompt),
            "schema_sha256": file_sha256(schema),
            "status": "PASS",
            "output_parsed": True,
            "output_bytes": output.stat().st_size,
            "stdout_bytes": output.stat().st_size,
            "stderr_bytes": 0,
            "exit_code": 0,
            "termination_initiator": "NONE",
            "child_cleanup_status": "NOT_NEEDED",
            "orphan_model_process_count": 0,
            "transport_metadata": {
                "runtime_state_namespace_hash": MODEL_FREE_ARTIFACT_MODE
            },
        }
        write_json(receipt_path, receipt)
        receipt_path.with_suffix(".stdout.log").write_bytes(output.read_bytes())
        receipt_path.with_suffix(".stderr.log").write_bytes(b"")
        self.simulated_invocation_count += 1
        self.invocation_lifecycle[invocation_id] = {
            "failure_stage": None,
            "spawn_started": 1,
            "transport_receipt_expected": 1,
            "transport_receipt_created": 1,
            "root_exception_masked": 0,
        }
        return receipt


def _prepare_real_input_rehearsal(
    *,
    root: Path,
    packets: Mapping[str, Mapping[str, object]],
    cohort: Sequence[str],
    source_generation_id: str,
    runtime_generation_id: str,
    review_manifest_sha256: str,
) -> tuple[SimpleNamespace, dict[str, object], RealInputModelFreeAdapter, dict[str, object]]:
    base_contexts = {
        ticker: deterministic_base_context(packets[ticker]) for ticker in cohort
    }
    evidence, owned, core_aliases, timing_aliases, price_maps, stocks = (
        frozen.build_inputs(packets, base_contexts, cohort)
    )
    for ticker in cohort:
        write_json(root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(root / "base-contexts" / f"{ticker}.txt", base_contexts[ticker])
    source_lock = frozen.source_lock_document(
        generation_id=source_generation_id,
        cohort=cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    source_lock.update(
        {
            "contract": "model-free-real-input-rehearsal-source-binding-v1",
            "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
            "executable": False,
            "model_execution_authorized": False,
            "proof_source_lock": False,
            "review_manifest_sha256": review_manifest_sha256,
            "real_investment_model_invocation_count": 0,
        }
    )
    source_lock_sha = canonical_sha256(source_lock)
    write_json(root / "source-lock.json", {**source_lock, "source_lock_sha256": source_lock_sha})
    prompt_schema = frozen._write_prompt_schema_lock(
        output_root=root,
        generation_id=source_generation_id,
        cohort=cohort,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    state: dict[str, object] = {
        "contract": "model-free-real-input-rehearsal-state-v1",
        "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
        "program_generation_id": runtime_generation_id,
        "source_generation_id": source_generation_id,
        "source_lock_sha256": source_lock_sha,
        "packet_hashes": source_lock["packet_sha256"],
        "ordered_cohort": list(cohort),
        "model_invocation_count": 0,
        "real_investment_model_invocation_count": 0,
        "simulated_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "context_preservation_secondary_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "proposed_cohort_output_exposure_state": "UNEXPOSED",
        "exposure_registry_write_enabled": 0,
        "status": "PREPARED",
    }
    write_json(root / "program-state.json", state)
    write_json(
        root / "review-prompt-schema-manifest.json",
        {
            **prompt_schema,
            "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
            "executable": False,
            "model_execution_authorized": False,
        },
    )
    args = SimpleNamespace(
        output_root=root,
        report_dir=root / "run-proofs",
        timeout=runner.TIMEOUT_SECONDS,
    )
    adapter = RealInputModelFreeAdapter(
        continuation_generation=runtime_generation_id,
        receipt_root=root / "simulated-receipts",
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
    )
    inputs = {
        "cohort": tuple(cohort),
        "contexts": base_contexts,
        "evidence": evidence,
        "owned": owned,
        "core_aliases": core_aliases,
        "timing_aliases": timing_aliases,
        "price_maps": price_maps,
        "stocks": stocks,
    }
    return args, state, adapter, inputs


def _execute_model_free_review_run(
    *,
    args: SimpleNamespace,
    state: dict[str, object],
    adapter: RealInputModelFreeAdapter,
    run: str,
    cohort: Sequence[str],
    contexts: Mapping[str, str],
    evidence: Mapping[str, object],
    owned: Mapping[str, object],
    core_aliases: Mapping[str, object],
    timing_aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    core_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    run_rows: list[dict[str, object]] = []
    manifests: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    batches = frozen.batches(cohort)
    sequence = 0
    for number, batch in enumerate(batches, start=1):
        sequence += 1
        manifest, output = runner.invoke_model_context(
            args=args,
            state=state,
            adapter=adapter,
            run=run,
            stage="DIRECTIONAL_CORE",
            batch_number=number,
            subjects=batch,
            sequence_position=sequence,
            prompt_source=args.output_root / "prompts" / f"core-batch-{number:02d}.txt",
            schema_source=args.output_root / "schemas" / f"core-batch-{number:02d}.json",
        )
        parsed = read_json(output)
        output_identity = runtime_identity.validate_output_identity(
            parsed,
            runtime_identity.load_binding(output.parent / "identity-binding-lock.json"),
        )
        write_json(output.parent / "output-identity-validation.json", output_identity)
        if output_identity["status"] != "PASS":
            raise ValueError(f"model_free_core_output_identity_mismatch:{run}:{number}")
        rows, alias_audit = frozen._resolve_batch_candidates(
            parsed.get("candidates"),
            batch=batch,
            evidence=evidence,
            catalogs=core_aliases,
            model_type=DirectionalCoreCandidate,
        )
        write_json(
            output.parent / "output.normalized.json",
            {
                "contract": CORE_OUTPUT_CONTRACT,
                "packet_id": state["program_generation_id"],
                "candidates": [row.model_dump(mode="json") for row in rows],
                "alias_audit": alias_audit,
            },
        )
        audit = runner.core_partial_audit(rows, owned)
        runner._mark_context_audit(output.parent, manifest, audit)
        if audit["status"] != "PASS":
            raise ValueError(f"model_free_core_semantic_failure:{run}:{number}")
        manifests.append(manifest)
        audits.append(audit)
        for row in rows:
            core_by_ticker[row.ticker] = row
        state["directional_context_count"] = int(state["directional_context_count"]) + 1
        write_json(args.output_root / "program-state.json", state)

    for number, batch in enumerate(batches, start=1):
        sequence += 1
        frozen_contexts = read_json(
            args.output_root / "timing-contexts" / f"batch-{number:02d}.json"
        )["contexts"]
        timing_contexts = []
        for context in frozen_contexts:
            ticker = str(context["ticker"])
            core = core_by_ticker[ticker]
            timing_contexts.append(
                {
                    **context,
                    "core_fingerprint": core_fingerprint(core),
                    "frozen_directional_core": core.model_dump(mode="json"),
                }
            )
        prompt = (
            args.output_root / "generated-timing-prompts" / run / f"batch-{number:02d}.txt"
        )
        write_text(
            prompt,
            frozen._timing_prompt(
                packet_id=str(state["program_generation_id"]),
                tickers=batch,
                contexts=timing_contexts,
            ),
        )
        manifest, output = runner.invoke_model_context(
            args=args,
            state=state,
            adapter=adapter,
            run=run,
            stage="PRICE_TIMING",
            batch_number=number,
            subjects=batch,
            sequence_position=sequence,
            prompt_source=prompt,
            schema_source=args.output_root / "schemas" / f"timing-batch-{number:02d}.json",
        )
        parsed = read_json(output)
        output_identity = runtime_identity.validate_output_identity(
            parsed,
            runtime_identity.load_binding(output.parent / "identity-binding-lock.json"),
        )
        write_json(output.parent / "output-identity-validation.json", output_identity)
        if output_identity["status"] != "PASS":
            raise ValueError(f"model_free_timing_output_identity_mismatch:{run}:{number}")
        rows, alias_audit = frozen._resolve_batch_candidates(
            parsed.get("candidates"),
            batch=batch,
            evidence=evidence,
            catalogs=timing_aliases,
            model_type=PriceTimingCandidate,
        )
        write_json(
            output.parent / "output.normalized.json",
            {
                "contract": TIMING_OUTPUT_CONTRACT,
                "packet_id": state["program_generation_id"],
                "candidates": [row.model_dump(mode="json") for row in rows],
                "alias_audit": alias_audit,
            },
        )
        audit, context_rows = runner.timing_partial_audit(
            rows=rows,
            core_by_ticker=core_by_ticker,
            owned=owned,
            evidence=evidence,
            price_maps=price_maps,
            stocks=stocks,
            base_contexts=contexts,
        )
        runner._mark_context_audit(output.parent, manifest, audit)
        if audit["status"] != "PASS":
            raise ValueError(f"model_free_timing_semantic_failure:{run}:{number}")
        manifests.append(manifest)
        audits.append(audit)
        run_rows.extend(context_rows)
        state["price_timing_context_count"] = int(state["price_timing_context_count"]) + 1
        state["renderer_context_count"] = int(state["renderer_context_count"]) + 1
        write_json(args.output_root / "program-state.json", state)

    run_rows.sort(key=lambda row: cohort.index(str(row["ticker"])))
    ownership, renderer, hard = runner.run_gate_documents(run, run_rows)
    rendered = [
        render_structured_autonomy_message(
            evidence[row["ticker"]],
            runner.compose_decision(
                DirectionalCoreCandidate.model_validate(row["core"]),
                PriceTimingCandidate.model_validate(row["timing"]),
            ).candidate,
            price_map=price_maps[row["ticker"]],
            industry=str(
                stocks[row["ticker"]].get("industry")
                or stocks[row["ticker"]].get("sector")
                or ""
            ),
            base_detail_text=contexts[row["ticker"]],
        )
        for row in run_rows
    ]
    status = (
        "PASS"
        if len(run_rows) == len(cohort)
        and all(row["status"] == "PASS" for row in run_rows)
        and ownership["status"] == renderer["status"] == hard["status"] == "PASS"
        else "FAIL"
    )
    result = {
        "contract": "model-free-real-input-two-stage-run-v1",
        "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
        "synthetic_adapter_output": True,
        "real_investment_output": False,
        "run": run,
        "runtime_generation_id": state["program_generation_id"],
        "candidate_count": len(run_rows),
        "context_count": len(manifests),
        "semantic_audit_count": len(audits),
        "ownership_gate": ownership,
        "renderer_gate": renderer,
        "hard_safety_gate": hard,
        "message_quality": structured_autonomy_message_quality(rendered),
        "real_model_invocations": 0,
        "exposure_registry_write": 0,
        "status": status,
    }
    write_json(args.output_root / "run-summaries" / f"{run}.json", result)
    if status != "PASS":
        raise ValueError(f"model_free_real_input_run_failed:{run}")
    return result


def _real_input_mode_summary(root: Path, adapter: RealInputModelFreeAdapter) -> dict[str, object]:
    preflights = [
        read_json(path)
        for path in sorted(root.rglob("actual-request-identity-preflight.json"))
    ]
    locks = [
        read_json(path) for path in sorted(root.rglob("identity-binding-lock.json"))
    ]
    receipt_validations = [
        read_json(path)
        for path in sorted(root.rglob("receipt-identity-validation.json"))
    ]
    output_validations = [
        read_json(path)
        for path in sorted(root.rglob("output-identity-validation.json"))
    ]
    manifests = [
        read_json(path) for path in sorted(root.rglob("context_manifest.json"))
    ]
    receipts = [
        read_json(path) for path in sorted(root.rglob("transport_receipt.json"))
    ]
    market_counts = Counter()
    market_failures = 0
    source_lock = read_json(root / "source-lock.json")
    state = read_json(root / "program-state.json")
    market_by_ticker = source_lock["market_by_ticker"]
    for manifest in manifests:
        subjects = tuple(str(value) for value in manifest["subjects"])
        expected = canonical_market_mix(subjects, market_by_ticker)
        actual = manifest.get("market_mix")
        market_failures += int(actual != expected)
        market_counts["US4" if expected == {"us": 4, "kr": 0} else "KR4"] += 1
    status = (
        "PASS"
        if len(preflights) == len(locks) == len(receipt_validations) == len(output_validations) == 32
        and len(manifests) == len(receipts) == 32
        and all(row.get("status") == "PASS" for row in preflights)
        and all(row.get("status") == "PASS" for row in receipt_validations)
        and all(row.get("status") == "PASS" for row in output_validations)
        and all(row.get("context_evidence_preservation_status") == "PASS" for row in manifests)
        and all(row.get("artifact_mode") == MODEL_FREE_ARTIFACT_MODE for row in receipts)
        and market_failures == 0
        and adapter.model_call_count == 0
        else "FAIL"
    )
    return {
        "runtime_generation_id": state["program_generation_id"],
        "source_generation_id": source_lock["program_generation_id"],
        "actual_request_preflight_count": len(preflights),
        "actual_request_preflight_failure_count": sum(
            row.get("status") != "PASS" for row in preflights
        ),
        "binding_lock_count": len(locks),
        "receipt_identity_failure_count": sum(
            row.get("status") != "PASS" for row in receipt_validations
        ),
        "output_identity_failure_count": sum(
            row.get("status") != "PASS" for row in output_validations
        ),
        "context_preservation_failure_count": sum(
            row.get("context_evidence_preservation_status") != "PASS"
            for row in manifests
        ),
        "market_manifest_failure_count": market_failures,
        "us4_context_count": market_counts["US4"],
        "kr4_context_count": market_counts["KR4"],
        "simulated_invocation_count": adapter.simulated_invocation_count,
        "real_model_invocation_count": adapter.model_call_count,
        "receipt_artifact_mode_failure_count": sum(
            row.get("artifact_mode") != MODEL_FREE_ARTIFACT_MODE for row in receipts
        ),
        "status": status,
    }


def run_real_input_rehearsal(
    *,
    root: Path,
    packets: Mapping[str, Mapping[str, object]],
    cohort: Sequence[str],
    review_manifest_sha256: str,
) -> dict[str, object]:
    source_id = f"selection-review-source-{review_manifest_sha256[:16]}"
    modes: dict[str, dict[str, object]] = {}
    for mode in ("fresh", "resumed"):
        mode_root = root / mode
        runtime_id = f"selection-review-runtime-{mode}-{review_manifest_sha256[:12]}"
        args, state, adapter, inputs = _prepare_real_input_rehearsal(
            root=mode_root,
            packets=packets,
            cohort=cohort,
            source_generation_id=source_id,
            runtime_generation_id=runtime_id,
            review_manifest_sha256=review_manifest_sha256,
        )
        run_results = {}
        for run in RUNS:
            run_results[run] = _execute_model_free_review_run(
                args=args,
                state=state,
                adapter=adapter,
                run=run,
                **inputs,
            )
        state.update(
            {
                "status": "PASS",
                "simulated_invocation_count": adapter.simulated_invocation_count,
                "real_investment_model_invocation_count": adapter.model_call_count,
                "proposed_cohort_output_exposure_state": "UNEXPOSED",
                "exposure_registry_write_enabled": 0,
            }
        )
        write_json(mode_root / "program-state.json", state)
        summary = _real_input_mode_summary(mode_root, adapter)
        summary["run_results"] = {
            run: result["status"] for run, result in run_results.items()
        }
        write_json(mode_root / "mode-summary.json", summary)
        if summary["status"] != "PASS":
            raise ValueError(f"model_free_real_input_mode_failed:{mode}")
        modes[mode] = summary
    total = sum(int(row["simulated_invocation_count"]) for row in modes.values())
    result = {
        "contract": "model-free-real-input-fresh-resumed-rehearsal-v1",
        "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
        "source_generation_id": source_id,
        "fresh": modes["fresh"],
        "resumed": modes["resumed"],
        "model_free_real_input_request_count": total,
        "real_investment_model_invocation_count": 0,
        "model_free_fixture_exposure_registry_write_count": 0,
        "status": (
            "PASS" if modes["fresh"]["status"] == modes["resumed"]["status"] == "PASS" else "FAIL"
        ),
    }
    write_json(root / "rehearsal-summary.json", result)
    return result


def pre_spawn_lifecycle_fixture(root: Path, cohort: Sequence[str]) -> dict[str, object]:
    context_dir = root / "lifecycle-fixtures" / "pre-spawn"
    context_dir.mkdir(parents=True)
    runner.copy_exact(root / "prompts/core-batch-01.txt", context_dir / "prompt.txt")
    runner.copy_exact(root / "schemas/core-batch-01.json", context_dir / "schema.json")
    state = read_json(root / "program-state.json")
    error = RuntimeError("MODEL_FREE_PRESPAWN_SENTINEL")
    args = SimpleNamespace(output_root=root)
    manifest = runner.preserve_context(
        args=args,
        state=state,
        run="prespawn-fixture",
        stage="DIRECTIONAL_CORE",
        batch_number=1,
        subjects=tuple(cohort[:4]),
        invocation_id="model-free-prespawn-sentinel",
        sequence_position=0,
        context_dir=context_dir,
        receipt_root=root / "empty-prespawn-receipts",
        error=error,
        transport_lifecycle={
            "failure_stage": "PRE_SPAWN_REVIEW_FIXTURE",
            "spawn_started": 0,
            "transport_receipt_expected": 0,
            "transport_receipt_created": 0,
            "root_exception_masked": 0,
        },
    )
    status = (
        "PASS"
        if manifest.get("spawn_started") == 0
        and manifest.get("transport_receipt_expected") == 0
        and manifest.get("root_exception_masked") == 0
        and manifest.get("root_exception") == "MODEL_FREE_PRESPAWN_SENTINEL"
        and manifest.get("context_evidence_preservation_status") == "PASS"
        else "FAIL"
    )
    result = {
        "contract": "model-free-prespawn-lifecycle-fixture-v1",
        "artifact_mode": MODEL_FREE_ARTIFACT_MODE,
        "original_exception_preserved": manifest.get("root_exception"),
        "spawn_started": manifest.get("spawn_started"),
        "transport_receipt_expected": manifest.get("transport_receipt_expected"),
        "transport_receipt_created": manifest.get("transport_receipt_created"),
        "root_exception_masked": manifest.get("root_exception_masked"),
        "status": status,
    }
    write_json(context_dir / "fixture-summary.json", result)
    return result


def preserve_input_members(
    archive: zipfile.ZipFile, output_root: Path, members: Sequence[str]
) -> None:
    for member in sorted(set(members)):
        target = output_root / "input-preserved" / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(member))


def _selected_rows(
    ledger: Sequence[Mapping[str, object]], selected: Sequence[str]
) -> list[Mapping[str, object]]:
    by_ticker = {str(row["ticker"]): row for row in ledger}
    return [by_ticker[ticker] for ticker in selected]


def _candidate_member_list(
    market: str, diagnostic_rows: Sequence[Mapping[str, object]]
) -> list[str]:
    result = []
    for row in diagnostic_rows:
        result.append(diagnostic_member(market, row))
        if row.get("full_packet_sha256"):
            result.append(full_packet_member(market, row))
    return result


def _policy(repo_root: Path) -> tuple[dict[str, Any], str]:
    path = repo_root / POLICY_PATH
    if file_sha256(path) != POLICY_RAW_SHA256:
        raise ValueError("review_policy_raw_hash_mismatch")
    policy = read_json(path)
    if policy.get("status") != "FROZEN_PRE_REVIEW_DIAGNOSTICS":
        raise ValueError("review_policy_not_frozen")
    budgets = policy.get("request_budgets")
    if not isinstance(budgets, Mapping) or any(
        int(budgets.get(key) or 0) != 0
        for key in (
            "kr_full_fundamental_evaluations",
            "reference_refresh_by_feed",
            "retry_count",
            "us_additional_route_checks",
            "us_full_fundamental_evaluations",
        )
    ):
        raise ValueError("review_policy_zero_request_boundary_missing")
    return policy, canonical_sha256(policy)


def generate(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    integrity = verify_input_bundle(args.input_zip)
    policy, policy_hash = _policy(repo_root)
    if git_value("status", "--short"):
        raise ValueError("implementation_worktree_must_be_clean_before_review")
    implementation_commit = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    instruction_commit = git_value(
        "log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH
    )
    policy_commit = git_value("log", "-1", "--format=%H", "--", POLICY_PATH)
    base_sha = git_value("rev-parse", f"{instruction_commit}^")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)

    with zipfile.ZipFile(args.input_zip) as archive:
        completion = zip_json(archive, "reports/proofs/24-program-completion.json")
        handoff = zip_json(
            archive, "reports/proofs/23-next-holdout-selection-handoff.json"
        )
        exclusion = zip_json(archive, "evidence/membership/exclusion-registry.json")
        us_membership = zip_jsonl(
            archive, "evidence/membership/us-reference-membership.jsonl"
        )
        kr_membership = zip_jsonl(
            archive, "evidence/membership/kr-reference-membership.jsonl"
        )
        us_sets = zip_json(archive, "evidence/membership/us-set-reconciliation.json")
        kr_sets = zip_json(archive, "evidence/membership/kr-set-reconciliation.json")
        us_set_audit = validate_set_reconciliation(us_sets)
        kr_set_audit = validate_set_reconciliation(kr_sets)
        if us_set_audit["status"] != "PASS" or kr_set_audit["status"] != "PASS":
            raise ValueError("supported_universe_set_reconciliation_failed")
        us_diagnostics = zip_json(
            archive, "evidence/diagnostics/us-source-readiness.json"
        )
        kr_diagnostics = zip_json(
            archive, "evidence/diagnostics/kr-source-readiness.json"
        )
        exclusion_canonical = canonical_sha256(exclusion)
        exclusion_raw = bytes_sha256(
            archive.read("evidence/membership/exclusion-registry.json")
        )
        if exclusion_canonical != policy["exclusion_registry"]["canonical_json_sha256"]:
            raise ValueError("canonical_exclusion_registry_hash_mismatch")
        if exclusion_raw != policy["exclusion_registry"]["raw_file_sha256"]:
            raise ValueError("raw_exclusion_registry_hash_mismatch")
        excluded = set(str(value) for value in exclusion["all_excluded_issuer_keys"])
        diagnostic_snapshot = str(completion["reference_retrieved_at"])
        us_ledger, selected_us = build_candidate_ledger(
            market="us",
            ordered_tickers=[str(value) for value in handoff["deterministic_us_candidate_order"]],
            membership_rows=us_membership,
            diagnostic_rows=us_diagnostics["rows"],
            excluded_issuer_keys=excluded,
            target=TARGET_US,
            diagnostic_snapshot=diagnostic_snapshot,
        )
        kr_ledger, selected_kr = build_candidate_ledger(
            market="kr",
            ordered_tickers=[str(value) for value in handoff["deterministic_kr_candidate_order"]],
            membership_rows=kr_membership,
            diagnostic_rows=kr_diagnostics["rows"],
            excluded_issuer_keys=excluded,
            target=TARGET_KR,
            diagnostic_snapshot=diagnostic_snapshot,
        )
        selected_rows = [
            *_selected_rows(us_ledger, selected_us),
            *_selected_rows(kr_ledger, selected_kr),
        ]
        diagnostics_by_market = {
            "us": {str(row["ticker"]): row for row in us_diagnostics["rows"]},
            "kr": {str(row["ticker"]): row for row in kr_diagnostics["rows"]},
        }
        source_reviews: dict[str, dict[str, object]] = {}
        hash_rows: list[dict[str, object]] = []
        packets: dict[str, dict[str, Any]] = {}
        for candidate in selected_rows:
            market = str(candidate["market"])
            ticker = str(candidate["ticker"])
            review, hash_row, packet = packet_source_review(
                archive=archive,
                market=market,
                candidate=candidate,
                diagnostic=diagnostics_by_market[market][ticker],
            )
            source_reviews[ticker] = review
            hash_rows.append(hash_row)
            packets[ticker] = packet
        manifest = build_review_manifest(
            implementation_commit=implementation_commit,
            policy_hash=policy_hash,
            input_zip_sha256=INPUT_ZIP_SHA256,
            selected_rows=selected_rows,
            source_reviews=source_reviews,
        )
        validate_review_manifest(manifest)
        preserve_input_members(
            archive,
            args.output_root,
            [
                *CRITICAL_INPUT_MEMBERS,
                *_candidate_member_list("us", us_diagnostics["rows"]),
                *_candidate_member_list("kr", kr_diagnostics["rows"]),
            ],
        )

    write_jsonl(args.output_root / "candidate-ledgers/us-candidates.jsonl", us_ledger)
    write_jsonl(args.output_root / "candidate-ledgers/kr-candidates.jsonl", kr_ledger)
    write_json(args.output_root / "source-reviews/selected-subjects.json", source_reviews)
    write_json(args.output_root / "source-reviews/packet-hash-audit.json", {"rows": hash_rows})
    write_json(args.output_root / "selection-review-manifest.json", manifest)

    before_registry_hash = exclusion_canonical
    guard = universe_audit._coexistence_observation()
    guard.update(
        {
            "review_observed_at": args.as_of.astimezone(UTC).isoformat(),
            "guard_authorization_requires_future_recheck": True,
            "review_authorizes_future_spawn": False,
        }
    )
    write_json(args.output_root / "guard/current-workload-observation.json", guard)
    if guard["status"] != "PASS":
        raise ValueError("live_workload_observation_blocked")

    synthetic_baseline = identity_repair.model_free_rehearsal(
        args.output_root / "model-free/synthetic-baseline"
    )
    if synthetic_baseline["status"] != "PASS":
        raise ValueError("synthetic_model_free_baseline_failed")
    cohort = tuple([*selected_us, *selected_kr])
    real_input = run_real_input_rehearsal(
        root=args.output_root / "model-free/real-input",
        packets=packets,
        cohort=cohort,
        review_manifest_sha256=str(manifest["source_manifest_sha256"]),
    )
    lifecycle = pre_spawn_lifecycle_fixture(
        args.output_root / "model-free/real-input/fresh", cohort
    )
    if lifecycle["status"] != "PASS":
        raise ValueError("prespawn_lifecycle_fixture_failed")
    after_registry_hash = canonical_sha256(
        read_json(
            args.output_root
            / "input-preserved/evidence/membership/exclusion-registry.json"
        )
    )
    exposure_leak_count = int(before_registry_hash != after_registry_hash)

    us_summary = summarize_us_ledger(us_ledger)
    kr_summary = {
        "unseen_supported_count": len(kr_ledger),
        "review_attempted_count": len(kr_diagnostics["rows"]),
        "review_pass_count": sum(
            row["source_status"] == "FUNDAMENTAL_SOURCE_SUFFICIENT"
            for row in kr_ledger
        ),
        "review_fail_count": sum(
            row["source_status"] == "FUNDAMENTAL_SOURCE_FAILED" for row in kr_ledger
        ),
        "identity_supported_untested_count": sum(
            row["source_status"] == "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED"
            for row in kr_ledger
        ),
    }
    source_review_status = (
        "PASS" if all(row["status"] == "PASS" for row in source_reviews.values()) else "FAIL"
    )
    hash_status = "PASS" if all(row["status"] == "PASS" for row in hash_rows) else "FAIL"
    explicit_market_status = (
        "PASS"
        if all(
            canonical_market_mix(group, manifest["market_by_ticker"])
            in ({"us": 4, "kr": 0}, {"us": 0, "kr": 4})
            for group in manifest["proposed_context_grouping"]
        )
        else "FAIL"
    )
    real_input_preflight_status = str(real_input["status"])
    selection_review_status = (
        "PASS"
        if source_review_status == hash_status == explicit_market_status == "PASS"
        and real_input_preflight_status == "PASS"
        and synthetic_baseline["status"] == "PASS"
        and lifecycle["status"] == "PASS"
        and exposure_leak_count == 0
        and all(
            value == "PASS"
            for value in (
                args.focused_tests,
                args.full_tests,
                args.ruff,
                args.diff_check,
            )
        )
        else "FAIL"
    )
    readiness = (
        "READY_FOR_SEPARATELY_AUTHORIZED_NEW_HOLDOUT_PROOF"
        if selection_review_status == "PASS"
        else "MODEL_FREE_REQUEST_PATH_BLOCKED"
    )

    changed_files = git_value("diff", "--name-only", f"{base_sha}..HEAD").splitlines()
    allowed_prefixes = (
        WORK_INSTRUCTION_PATH,
        POLICY_PATH,
        "scripts/new_issuer_holdout_selection_preexecution_review.py",
        "tests/test_new_issuer_holdout_selection_preexecution_review.py",
    )
    unexpected_changed_files = [
        path for path in changed_files if path not in allowed_prefixes
    ]
    production_isolation_status = "PASS" if not unexpected_changed_files else "FAIL"

    provenance = {
        **integrity,
        "base_sha": base_sha,
        "work_instruction_commit": instruction_commit,
        "policy_commit": policy_commit,
        "implementation_commit": implementation_commit,
        "branch": branch,
        "worktree_status_before_generated_evidence": "CLEAN",
        "status": "PASS",
    }
    baseline = {
        "accepted_final_completion_authority": (
            "reports/proofs/24-program-completion.json"
        ),
        "accepted_final_head_sha": completion["final_head_sha"],
        "accepted_readiness": completion["readiness"],
        "accepted_reference_snapshot_id": completion["reference_snapshot_id"],
        "accepted_exclusion_issuer_count": completion[
            "canonical_exclusion_issuer_count"
        ],
        "intermediate_program_summary_authority": False,
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "status": "PASS",
    }
    production_isolation = {
        "changed_files_since_task_base": changed_files,
        "unexpected_changed_files": unexpected_changed_files,
        "new_review_tool_imported_by_live_runtime": False,
        "shared_production_store_write": 0,
        "source_request_count": 0,
        "production_isolation_status": production_isolation_status,
        "status": production_isolation_status,
    }
    policy_proof = {
        "policy_path": POLICY_PATH,
        "policy_raw_sha256": file_sha256(repo_root / POLICY_PATH),
        "selection_policy_hash": policy_hash,
        "request_budgets": policy["request_budgets"],
        "retry_count": 0,
        "network_request_count": 0,
        "status": "PASS",
    }
    exclusion_proof = {
        "exclusion_registry_hash_before": before_registry_hash,
        "exclusion_registry_hash_after": after_registry_hash,
        "exclusion_registry_raw_sha256": exclusion_raw,
        "canonical_exclusion_issuer_count": len(excluded),
        "exclusion_membership_removed_without_provenance": 0,
        "actual_output_exposed_issuer_count": len(exclusion["actual_output_issuer_keys"]),
        "whole_cohort_retired_issuer_count": len(
            exclusion["whole_cohort_retired_issuer_keys"]
        ),
        "alias_share_class_fence": "PRESERVED_BY_CANONICAL_ISSUER_KEY",
        "status": "PASS" if exposure_leak_count == 0 and len(excluded) == 85 else "FAIL",
    }
    universe_proof = {
        "accepted_reference_snapshot_ids": [completion["reference_snapshot_id"]],
        "us_supported_security_count": us_sets["supported_security_count"],
        "us_supported_issuer_count": us_sets["supported_issuer_count"],
        "us_unseen_supported_issuer_count": len(us_ledger),
        "kr_supported_security_count": kr_sets["supported_security_count"],
        "kr_supported_issuer_count": kr_sets["supported_issuer_count"],
        "kr_unseen_supported_issuer_count": len(kr_ledger),
        "us_set_invariants": us_set_audit,
        "kr_set_invariants": kr_set_audit,
        "status": (
            "PASS"
            if us_set_audit["status"] == kr_set_audit["status"] == "PASS"
            else "FAIL"
        ),
    }
    us_proof = {
        **us_summary,
        "proposed_us4": list(selected_us),
        "known_source_failure_membership": [
            row["ticker"]
            for row in us_ledger
            if row["source_status"] == "FUNDAMENTAL_SOURCE_FAILED"
        ],
        "candidate_ledger": "evidence/candidate-ledgers/us-candidates.jsonl",
        "status": "PASS"
        if us_summary
        == {
            "unseen_supported_count": 25,
            "source_pass_count": 4,
            "known_source_fail_count": 2,
            "untested_global_count": 19,
            "untested_within_budget_count": 18,
            "identity_supported_nonprimary_count": 21,
            "source_sufficient_reserve_count": 0,
        }
        else "FAIL",
    }
    kr_proof = {
        **kr_summary,
        "proposed_kr12": list(selected_kr),
        "candidate_ledger": "evidence/candidate-ledgers/kr-candidates.jsonl",
        "status": "PASS"
        if kr_summary["unseen_supported_count"] == 2491
        and kr_summary["review_attempted_count"] == 12
        and kr_summary["review_pass_count"] == 12
        and kr_summary["review_fail_count"] == 0
        else "FAIL",
    }
    source_by_market = {
        market: [
            row for row in source_reviews.values() if row.get("market") == market
        ]
        for market in ("us", "kr")
    }
    source_proofs = {}
    for market in ("us", "kr"):
        rows = source_by_market[market]
        source_proofs[market] = {
            "market": market,
            "reviewed_count": len(rows),
            "source_period_review_status": (
                "PASS" if all(row["source_period_rows"] for row in rows) else "FAIL"
            ),
            "source_provenance_review_status": (
                "PASS" if all(row["source_request_lineage"] for row in rows) else "FAIL"
            ),
            "raw_provider_response_archive_state": (
                "NOT_BUNDLED_NORMALIZED_FACTS_ONLY"
            ),
            "price_readiness_by_subject": {
                str(row["ticker"]): {
                    "price_context": row["price_context_readiness"],
                    "price_timing": row["price_timing_readiness"],
                    "technical_context": row["technical_context_status"],
                }
                for row in rows
            },
            "mandatory_unknowns": {
                str(row["ticker"]): row["mandatory_unknowns"] for row in rows
            },
            "rows": rows,
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        }
    dual = {
        "terminal_matrix": "BOTH_READY_FOR_SELECTION",
        "us_status": us_proof["status"],
        "kr_status": kr_proof["status"],
        "selection_review_status": selection_review_status,
        "proof_executed": False,
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "status": selection_review_status,
    }
    cohort_proof = {
        "proposed_us4": list(selected_us),
        "proposed_kr12": list(selected_kr),
        "proposed_context_grouping": manifest["proposed_context_grouping"],
        "context_market_mix": [
            canonical_market_mix(group, manifest["market_by_ticker"])
            for group in manifest["proposed_context_grouping"]
        ],
        "selection_status": "PROPOSED_REVIEWED",
        "execution_authorized": False,
        "status": "PASS",
    }
    hash_proof = {
        "rows": hash_rows,
        "raw_and_canonical_hash_status": hash_status,
        "raw_provider_response_bytes_present": 0,
        "raw_provider_response_limitation_explicit": 1,
        "status": hash_status,
    }
    preflight_proof = {
        "actual_request_identity_preflight_status": real_input_preflight_status,
        "explicit_market_preflight_status": explicit_market_status,
        "fresh_actual_request_count": real_input["fresh"][
            "actual_request_preflight_count"
        ],
        "resumed_actual_request_count": real_input["resumed"][
            "actual_request_preflight_count"
        ],
        "identity_preflight_failure_count": (
            real_input["fresh"]["actual_request_preflight_failure_count"]
            + real_input["resumed"]["actual_request_preflight_failure_count"]
        ),
        "market_manifest_failure_count": (
            real_input["fresh"]["market_manifest_failure_count"]
            + real_input["resumed"]["market_manifest_failure_count"]
        ),
        "status": (
            "PASS"
            if real_input_preflight_status == explicit_market_status == "PASS"
            else "FAIL"
        ),
    }
    model_free_proof = {
        "synthetic_baseline_artifact_mode": synthetic_baseline["artifact_mode"],
        "synthetic_baseline_simulated_context_count": synthetic_baseline[
            "simulated_invocation_count"
        ],
        "model_free_real_input_request_count": real_input[
            "model_free_real_input_request_count"
        ],
        "model_free_simulated_context_count": (
            synthetic_baseline["simulated_invocation_count"]
            + real_input["model_free_real_input_request_count"]
        ),
        "model_free_fixture_exposure_registry_leak_count": exposure_leak_count,
        "available_partial_safe_unavailable_safe_branches": {
            "available": "COVERED_SYNTHETIC_AND_REAL_INPUT",
            "partial_safe": "COVERED_REAL_INPUT",
            "unavailable_safe": "COVERED_SYNTHETIC_BASELINE",
        },
        "fresh": real_input["fresh"],
        "resumed": real_input["resumed"],
        "real_investment_model_invocation_count": 0,
        "status": (
            "PASS"
            if synthetic_baseline["status"] == real_input["status"] == "PASS"
            and exposure_leak_count == 0
            else "FAIL"
        ),
    }
    guard_proof = {
        "current_observation": guard,
        "pre_spawn_fixture": lifecycle,
        "post_spawn_fixture_receipt_count": real_input[
            "model_free_real_input_request_count"
        ],
        "guard_review_status": (
            "PASS" if guard["status"] == lifecycle["status"] == "PASS" else "FAIL"
        ),
        "guard_authorization_requires_future_recheck": True,
        "review_is_not_spawn_authorization": True,
        "status": (
            "PASS" if guard["status"] == lifecycle["status"] == "PASS" else "FAIL"
        ),
    }
    validation = {
        "tested_commit": implementation_commit,
        "focused_tests": args.focused_tests,
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "validation_logs": [path.name for path in args.test_logs],
        "model_backed_tests_run": 0,
        "status": (
            "PASS"
            if all(
                value == "PASS"
                for value in (
                    args.focused_tests,
                    args.full_tests,
                    args.ruff,
                    args.diff_check,
                )
            )
            else "FAIL"
        ),
    }
    production = {
        "production_no_change": 1,
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_cache_write": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "natural_live_cancel_count": 0,
        "new_real_investment_model_invocation_count": 0,
        "model_backed_fictional_canary_count": 0,
        "real_first_a_b_c_execution_count": 0,
        "final_real_holdout_activation": 0,
        "executable_proof_source_lock_created": 0,
        "status": "PASS",
    }
    handoff_proof = {
        "next_scope": "NEW_ISSUER_HOLDOUT_FINAL_FREEZE_AND_OWNERSHIP_PROOF",
        "next_task_requires_separate_authorization": True,
        "future_model": runner.MODEL,
        "future_reasoning_effort": runner.EFFORT,
        "future_batch_semantics": runner.BATCH_SEMANTICS,
        "future_subjects_per_context": runner.CONTEXT_SIZE,
        "future_timeout_seconds": runner.TIMEOUT_SECONDS,
        "future_timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "future_execution_requires_new_source_and_workload_recheck": True,
        "review_manifest_executable": False,
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "status": "PASS",
    }
    completion_proof: dict[str, object] = {
        "contract": PROGRAM_CONTRACT,
        "summary_role": "PREPACKAGING_REPOSITORY_SNAPSHOT_NOT_FINAL_BUNDLE_AUTHORITY",
        "base_sha": base_sha,
        "work_instruction_commit": instruction_commit,
        "policy_commit": policy_commit,
        "implementation_commit": implementation_commit,
        "final_head_sha": "FINALIZED_IN_RESULT_BUNDLE_AFTER_REPORT_COMMIT",
        "branch": branch,
        "input_zip_sha256": integrity["input_zip_sha256"],
        "input_integrity_status": integrity["status"],
        "accepted_reference_snapshot_ids": [completion["reference_snapshot_id"]],
        "exclusion_registry_hash_before": before_registry_hash,
        "exclusion_registry_hash_after": after_registry_hash,
        "exclusion_membership_removed_without_provenance": 0,
        "canonical_exclusion_issuer_count": len(excluded),
        "us_unseen_supported_count": us_summary["unseen_supported_count"],
        "us_source_pass_count": us_summary["source_pass_count"],
        "us_known_source_fail_count": us_summary["known_source_fail_count"],
        "us_untested_global_count": us_summary["untested_global_count"],
        "us_untested_within_budget_count": us_summary[
            "untested_within_budget_count"
        ],
        "us_identity_supported_nonprimary_count": us_summary[
            "identity_supported_nonprimary_count"
        ],
        "us_source_sufficient_reserve_count": us_summary[
            "source_sufficient_reserve_count"
        ],
        "kr_unseen_supported_count": kr_summary["unseen_supported_count"],
        "kr_review_attempted_count": kr_summary["review_attempted_count"],
        "kr_review_pass_count": kr_summary["review_pass_count"],
        "kr_review_fail_count": kr_summary["review_fail_count"],
        "proposed_us4": list(selected_us),
        "proposed_kr12": list(selected_kr),
        "proposed_context_grouping": manifest["proposed_context_grouping"],
        "selection_policy_hash": policy_hash,
        "review_manifest_sha256": manifest["source_manifest_sha256"],
        "review_manifest_executable": False,
        "executable_proof_source_lock_created": 0,
        "source_period_review_status": source_review_status,
        "source_provenance_review_status": source_review_status,
        "raw_and_canonical_hash_status": hash_status,
        "price_readiness_by_subject": {
            ticker: {
                "price_context": row["price_context_readiness"],
                "price_timing": row["price_timing_readiness"],
                "technical_context": row["technical_context_status"],
            }
            for ticker, row in source_reviews.items()
        },
        "mandatory_unknowns": {
            ticker: row["mandatory_unknowns"] for ticker, row in source_reviews.items()
        },
        "actual_request_identity_preflight_status": real_input_preflight_status,
        "explicit_market_preflight_status": explicit_market_status,
        "model_free_simulated_context_count": model_free_proof[
            "model_free_simulated_context_count"
        ],
        "model_free_real_input_request_count": real_input[
            "model_free_real_input_request_count"
        ],
        "model_free_fixture_exposure_registry_leak_count": exposure_leak_count,
        "guard_review_status": guard_proof["guard_review_status"],
        "guard_authorization_requires_future_recheck": True,
        "real_investment_model_invocation_count": 0,
        "real_subject_output_count": 0,
        "model_backed_fictional_canary_count": 0,
        "real_first_a_b_c_execution_count": 0,
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "investment_architecture_semantic_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "prompt_schema_semantic_drift": 0,
        "runtime_identity_contract_drift": 0,
        "guard_transport_semantic_drift": 0,
        "historical_artifact_mutation": 0,
        **{key: value for key, value in production.items() if key != "status"},
        "request_counts_by_market_and_provider": {
            "us": {},
            "kr": {},
            "reference": {},
        },
        "retry_count": 0,
        "budget_exhaustion": {"us": False, "kr": False},
        "artifact_count": "FINALIZED_DURING_PACKAGING",
        "indexed_artifact_count": "FINALIZED_DURING_PACKAGING",
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "unexpected_unindexed_files": [],
        "secret_scan_status": "PENDING_FINAL_PACKAGING_SCAN",
        "selection_review_status": selection_review_status,
        "readiness": readiness,
        "stop_reason": None if selection_review_status == "PASS" else readiness,
        "next_scope": (
            "NEW_ISSUER_HOLDOUT_FINAL_FREEZE_AND_OWNERSHIP_PROOF"
            if selection_review_status == "PASS"
            else "BOUNDED_PREEXECUTION_REVIEW_REPAIR"
        ),
        "status": selection_review_status,
    }

    proofs = (
        provenance,
        baseline,
        production_isolation,
        policy_proof,
        exclusion_proof,
        universe_proof,
        us_proof,
        kr_proof,
        source_proofs["us"],
        source_proofs["kr"],
        dual,
        cohort_proof,
        manifest,
        hash_proof,
        preflight_proof,
        model_free_proof,
        guard_proof,
        validation,
        production,
        handoff_proof,
        completion_proof,
    )
    for number, proof in enumerate(proofs, start=1):
        write_proof(args.report_dir, number, proof)
    write_json(
        args.output_root / "program-summary.json",
        {
            "artifact_role": "PREPACKAGING_INTERMEDIATE_SUMMARY",
            "final_authority": "result ZIP reports/proofs/21-program-completion.json",
            "completion": completion_proof,
        },
    )
    print(json.dumps(completion_proof, ensure_ascii=False, sort_keys=True), flush=True)


def _artifact_class(path: Path, root: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    if relative.startswith("evidence/input-preserved/"):
        provenance = "historical"
        artifact_class = "PRESERVED_INPUT"
    elif relative.startswith("evidence/model-free/"):
        provenance = "model-free"
        artifact_class = "MODEL_FREE_REHEARSAL"
    elif relative.startswith("reports/"):
        provenance = "source-only"
        artifact_class = "REPORT"
    else:
        provenance = "source-only"
        artifact_class = "REVIEW_EVIDENCE"
    market = "us" if "/us/" in relative else "kr" if "/kr/" in relative else None
    run = next(
        (value for value in ("FIRST", "A", "B", "C") if f"/{value}/" in relative),
        None,
    )
    stage = next((value for value in STAGES if f"/{value}/" in relative), None)
    return {
        "artifact_class": artifact_class,
        "provenance_class": provenance,
        "market": market,
        "run": run,
        "stage": stage,
    }


def _scan_secrets(paths: Sequence[Path]) -> dict[str, object]:
    counts = Counter()
    for path in paths:
        payload = path.read_bytes()
        for name, pattern in runner.SECRET_PATTERNS.items():
            counts[name] += len(pattern.findall(payload))
    total = sum(counts.values())
    return {
        "category_counts": dict(counts),
        "secret_exposure_count": total,
        "secret_scan_status": "PASS" if total == 0 else "FAIL",
    }


def finalize(args: argparse.Namespace) -> None:
    if args.bundle_root.exists() or args.result_zip.exists():
        raise ValueError("new_bundle_and_result_zip_required")
    completion = read_json(args.report_dir / "proofs" / f"{REPORT_NAMES[-1]}.json")
    final_head = git_value("rev-parse", "HEAD")
    if final_head == args.implementation_freeze_commit:
        raise ValueError("final_report_commit_required_before_packaging")
    args.bundle_root.mkdir(parents=True)
    shutil.copytree(args.report_dir, args.bundle_root / "reports")
    shutil.copytree(args.output_root, args.bundle_root / "evidence")
    repository_root = args.bundle_root / "repository"
    repository_root.mkdir()
    shutil.copyfile(WORK_INSTRUCTION_PATH, repository_root / Path(WORK_INSTRUCTION_PATH).name)
    shutil.copyfile(POLICY_PATH, repository_root / Path(POLICY_PATH).name)
    validation_root = args.bundle_root / "validation"
    validation_root.mkdir()
    for path in args.validation_logs:
        shutil.copyfile(path, validation_root / path.name)

    completion.update(
        {
            "summary_role": "FINAL_BUNDLE_CANONICAL_COMPLETION",
            "final_head_sha": final_head,
            "implementation_freeze_commit": args.implementation_freeze_commit,
            "artifact_count": "CALCULATED_BEFORE_INDEX",
            "indexed_artifact_count": "CALCULATED_BEFORE_INDEX",
            "secret_scan_status": "CALCULATED_BEFORE_INDEX",
        }
    )
    write_json(
        args.bundle_root / "reports/proofs" / f"{REPORT_NAMES[-1]}.json",
        completion,
    )
    write_text(
        args.bundle_root / "reports" / f"{REPORT_NAMES[-1]}.md",
        markdown_report(REPORT_NAMES[-1], completion),
    )
    write_json(
        args.bundle_root / "evidence/program-summary.json",
        {
            "artifact_role": "FINAL_BUNDLE_CANONICAL_SUMMARY",
            "final_authority": "reports/proofs/21-program-completion.json",
            "completion": completion,
        },
    )
    write_text(
        args.bundle_root / "README.md",
        "\n".join(
            (
                "# New Issuer Holdout Selection Pre-Execution Readiness Review",
                "",
                "This is a review-only result. It contains no real investment model output,",
                "no executable proof source lock, and no production activation.",
                "",
                "Final authority: `reports/proofs/21-program-completion.json`.",
            )
        ),
    )
    payload_paths = sorted(path for path in args.bundle_root.rglob("*") if path.is_file())
    artifact_count = len(payload_paths) + 1
    indexed_count = len(payload_paths)
    secret_scan = _scan_secrets(payload_paths)
    if secret_scan["secret_scan_status"] != "PASS":
        raise ValueError("secret_scan_failed")
    completion.update(
        {
            "artifact_count": artifact_count,
            "indexed_artifact_count": indexed_count,
            "index_self_exclusion": "artifact-index.json only",
            "hash_mismatch_count": 0,
            "size_mismatch_count": 0,
            "unexpected_unindexed_files": [],
            "secret_scan_status": "PASS",
        }
    )
    write_json(
        args.bundle_root / "reports/proofs" / f"{REPORT_NAMES[-1]}.json",
        completion,
    )
    write_text(
        args.bundle_root / "reports" / f"{REPORT_NAMES[-1]}.md",
        markdown_report(REPORT_NAMES[-1], completion),
    )
    write_json(
        args.bundle_root / "evidence/program-summary.json",
        {
            "artifact_role": "FINAL_BUNDLE_CANONICAL_SUMMARY",
            "final_authority": "reports/proofs/21-program-completion.json",
            "completion": completion,
        },
    )
    payload_paths = sorted(path for path in args.bundle_root.rglob("*") if path.is_file())
    secret_scan = _scan_secrets(payload_paths)
    if secret_scan["secret_scan_status"] != "PASS":
        raise ValueError("final_secret_scan_failed")
    index_rows = []
    for path in payload_paths:
        index_rows.append(
            {
                "path": path.relative_to(args.bundle_root).as_posix(),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                **_artifact_class(path, args.bundle_root),
            }
        )
    index = {
        "contract": "complete-result-artifact-index-v1",
        "artifact_count": len(index_rows) + 1,
        "indexed_artifact_count": len(index_rows),
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "rows": index_rows,
        "unexpected_unindexed_files": [],
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan": secret_scan,
        "status": "PASS",
    }
    write_json(args.bundle_root / "artifact-index.json", index)

    with zipfile.ZipFile(args.result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.bundle_root).as_posix())
    with zipfile.ZipFile(args.result_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("final_zip_crc_failed")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("final_zip_duplicate_members")
        archived_index = json.loads(archive.read("artifact-index.json"))
        indexed = {str(row["path"]): row for row in archived_index["rows"]}
        actual = set(names) - {"artifact-index.json"}
        if actual != set(indexed):
            raise ValueError("final_zip_member_index_mismatch")
        hash_mismatches = []
        size_mismatches = []
        for name in sorted(actual):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row["sha256"]:
                hash_mismatches.append(name)
            if len(payload) != row["byte_size"]:
                size_mismatches.append(name)
        if hash_mismatches or size_mismatches:
            raise ValueError("final_zip_payload_integrity_mismatch")
    result_sha = file_sha256(args.result_zip)
    sidecar = args.result_zip.with_suffix(args.result_zip.suffix + ".sha256")
    write_text(sidecar, f"{result_sha}  {args.result_zip.name}")
    print(
        json.dumps(
            {
                "status": "PASS",
                "result_zip": str(args.result_zip),
                "sha256": result_sha,
                "artifact_count": len(index_rows) + 1,
                "indexed_artifact_count": len(index_rows),
                "hash_mismatch_count": 0,
                "size_mismatch_count": 0,
                "zip_crc": "PASS",
            },
            sort_keys=True,
        ),
        flush=True,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    commands = value.add_subparsers(dest="command", required=True)
    generate_parser = commands.add_parser("generate")
    generate_parser.add_argument("--input-zip", type=Path, required=True)
    generate_parser.add_argument("--output-root", type=Path, required=True)
    generate_parser.add_argument("--report-dir", type=Path, required=True)
    generate_parser.add_argument("--as-of", type=datetime.fromisoformat, required=True)
    generate_parser.add_argument("--focused-tests", required=True)
    generate_parser.add_argument("--full-tests", required=True)
    generate_parser.add_argument("--ruff", required=True)
    generate_parser.add_argument("--diff-check", required=True)
    generate_parser.add_argument("--test-logs", type=Path, nargs="+", required=True)

    finalize_parser = commands.add_parser("finalize")
    finalize_parser.add_argument("--output-root", type=Path, required=True)
    finalize_parser.add_argument("--report-dir", type=Path, required=True)
    finalize_parser.add_argument("--bundle-root", type=Path, required=True)
    finalize_parser.add_argument("--result-zip", type=Path, required=True)
    finalize_parser.add_argument("--implementation-freeze-commit", required=True)
    finalize_parser.add_argument("--validation-logs", type=Path, nargs="+", required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "generate":
        generate(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
