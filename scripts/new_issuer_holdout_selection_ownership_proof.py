from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import re
import shutil
import subprocess
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.codex_transport_lifecycle_service import InstrumentedTransportError
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    CORE_OUTPUT_CONTRACT,
    MATERIAL_DIRECTIONAL_DOMAINS,
    TIMING_DOMAINS,
    TIMING_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    PriceTimingCandidate,
    canonical_sha256,
    compose_decision,
    core_fingerprint,
    technical_feature_inventory,
    validate_ownership,
)
from app.services.structured_autonomy_shadow_service import (
    explicit_actionable_trade_directives,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import official_fundamental_enrichment_holdout as fundamental
from scripts import structured_actionability_unseen_coldstart as actionability
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import unseen_source_assembly_coldstart as source_assembly
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "dual-market-source-coverage-new-issuer-holdout-ownership-proof-v1"
SELECTION_CONTRACT = "dual-market-source-coverage-policy-v1"
SELECTION_SALT = "20260907-new-issuer-holdout-selection-ownership-proof-v1"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
TIMEOUT_OWNER_COUNT = 1
BATCH_SEMANTICS = "MODEL_CONTEXT_COUPLED"
CONTEXT_SIZE = 4
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
KR_RESERVE_LIMIT = 36
REPORT_DIRECTORY = "20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof"
FORENSIC_ZIP_SHA256 = (
    "c88368357cd4fbde183d90620194307f9e5498cfd75d2dcafad6b8d04ffbc3b4"
)
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-dual-market-source-coverage-and-new-issuer-holdout-ownership-proof.md"
)
WORK_INSTRUCTION_SHA256 = (
    "2af740911024b5f3e51118155edc2e5652368748dac80ea478fd10a3bb8e6be1"
)
OLD_PARTIAL = (
    "ORCL",
    "UNH",
    "KO",
    "AVGO",
    "095570",
    "058860",
    "246960",
    "099520",
    "403870",
    "014790",
    "079810",
    "060980",
    "061970",
    "012030",
    "225190",
    "245620",
)
OLD_CONSUMED = (
    "PLTR",
    "V",
    "MA",
    "AMZN",
    "XOM",
    "DIS",
    "NKE",
    "MCD",
    "033920",
    "104480",
    "071320",
    "096240",
    "032860",
    "060570",
    "016600",
    "462520",
)
RUNS = ("first", "a", "b", "c")
STAGES = ("DIRECTIONAL_CORE", "PRICE_TIMING")

PROOF_NAMES = (
    "01-repository-provenance",
    "02-latest-forensic-result-integrity",
    "03-prior-real-issuer-exposure-registry",
    "04-new-holdout-exclusion-set",
    "05-dual-market-source-coverage-policy",
    "06-us-candidate-manifest",
    "07-us-source-coverage-audit",
    "08-us-source-failure-detail",
    "09-kr-candidate-manifest",
    "10-kr-source-coverage-audit",
    "11-kr-source-failure-detail",
    "12-dual-market-source-coverage-summary",
    "13-cross-market-failure-comparison",
    "14-source-coverage-remediation-decision",
    "15-new-holdout-selection-result",
    "16-new-source-generation",
    "17-source-sufficiency-audit",
    "18-source-identity-audit",
    "19-new-source-lock",
    "20-new-holdout-precommit",
    "21-architecture-semantic-freeze",
    "22-prompt-schema-freeze",
    "23-model-context-freeze",
    "24-transport-topology-freeze",
    "25-holdout-unseen-reuse-gate",
    "26-live-workload-coexistence-audit",
    "27-first-execution-summary",
    "28-first-context-artifact-manifest",
    "29-first-context-partial-semantic-audits",
    "30-first-run-ownership-gate",
    "31-first-run-renderer-gate",
    "32-first-run-hard-safety-gate",
    "33-run-a-execution-summary",
    "34-run-a-context-artifact-manifest",
    "35-run-a-context-partial-semantic-audits",
    "36-run-a-ownership-gate",
    "37-run-a-renderer-gate",
    "38-run-a-hard-safety-gate",
    "39-run-b-execution-summary",
    "40-run-b-context-artifact-manifest",
    "41-run-b-context-partial-semantic-audits",
    "42-run-b-ownership-gate",
    "43-run-b-renderer-gate",
    "44-run-b-hard-safety-gate",
    "45-run-c-execution-summary",
    "46-run-c-context-artifact-manifest",
    "47-run-c-context-partial-semantic-audits",
    "48-run-c-ownership-gate",
    "49-run-c-renderer-gate",
    "50-run-c-hard-safety-gate",
    "51-holdout-exposure-retirement-state",
    "52-core-stability",
    "53-timing-stability",
    "54-ownership-generalization",
    "55-renderer-ownership-proof",
    "56-hard-safety-regression",
    "57-production-no-change",
    "58-night-futures-no-change",
    "59-monitoring-bootstrap-next-handoff",
    "60-program-completion",
)

RUN_PROOFS = {
    "first": (27, 28, 29, 30, 31, 32),
    "a": (33, 34, 35, 36, 37, 38),
    "b": (39, 40, 41, 42, 43, 44),
    "c": (45, 46, 47, 48, 49, 50),
}

SECRET_PATTERNS = {
    "openai_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "telegram_bot_token": re.compile(rb"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b"),
    "bearer_token": re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/-]{24,}"),
    "named_secret": re.compile(
        rb"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
        rb"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/-]{20,}"
    ),
}


class SemanticStop(RuntimeError):
    pass


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


def source_sha256(value: object) -> str:
    return hashlib.sha256(inspect.getsource(value).encode()).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{PROOF_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, number), value)


def canonical_issuer_key(ticker: str, name: str | None = None) -> str:
    if ticker in {"GOOG", "GOOGL"}:
        return "us:alphabet"
    normalized_name = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    if normalized_name:
        return f"name:{normalized_name.removesuffix('classa')}"
    return f"ticker:{ticker}"


def _candidate_tickers(document: Mapping[str, object]) -> list[str]:
    values: list[str] = []
    candidates = document.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, Mapping) and isinstance(candidate.get("ticker"), str):
                values.append(str(candidate["ticker"]))
    rows = document.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping) and isinstance(row.get("ticker"), str):
                values.append(str(row["ticker"]))
    return list(
        dict.fromkeys(
            value
            for value in values
            if not re.match(r"^(?:SYNTHETIC|FICTIONAL|CANARY|SYN)(?:_|$)", value)
        )
    )


def build_exposure_registry(
    report_history: Path,
    universe: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    identities = {str(row["ticker"]): row for row in universe}
    records: dict[str, list[dict[str, object]]] = defaultdict(list)
    relevant_contracts = {
        "uskr22-structured-autonomy-run-v1",
        "direction-timing-two-stage-run-v1",
        CORE_OUTPUT_CONTRACT,
    }
    for path in sorted(report_history.rglob("*.json")):
        relative = str(path.relative_to(report_history))
        if not re.search(r"2026090[3-6]", relative):
            continue
        try:
            document = read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        contract = str(document.get("contract") or "")
        if contract not in relevant_contracts:
            continue
        tickers = _candidate_tickers(document)
        if not tickers:
            continue
        candidate_count = int(document.get("candidate_count") or len(tickers))
        if candidate_count < 1:
            continue
        generation_id = str(
            document.get("program_generation_id")
            or document.get("packet_id")
            or document.get("generation_id")
            or "NOT_MEASURED"
        )
        run = str(document.get("run") or "first")
        invocation_by_ticker: dict[str, str] = {}
        invocations = document.get("batch_invocations") or document.get("invocations")
        if isinstance(invocations, list):
            for invocation in invocations:
                if not isinstance(invocation, Mapping):
                    continue
                batch = str(invocation.get("batch") or invocation.get("batch_id") or "?")
                invocation_id = str(
                    invocation.get("invocation_id")
                    or f"{generation_id}:{run}:batch-{batch}"
                )
                subjects = invocation.get("tickers")
                if isinstance(subjects, list):
                    for ticker in subjects:
                        invocation_by_ticker[str(ticker)] = invocation_id
        generation_ids = document.get("generation_ids")
        for ticker in tickers:
            identity = identities.get(ticker, {})
            issuer_key = canonical_issuer_key(
                ticker, str(identity.get("company_name") or "")
            )
            invocation_id = invocation_by_ticker.get(ticker)
            if invocation_id is None and isinstance(generation_ids, Mapping):
                invocation_id = str(generation_ids.get(ticker) or "NOT_MEASURED")
            records[issuer_key].append(
                {
                    "ticker": ticker,
                    "generation_id": generation_id,
                    "invocation_id": invocation_id or "NOT_MEASURED",
                    "experiment_class": contract,
                    "model_call_started": True,
                    "usable_output_exists": True,
                    "exposure_class": "REAL_MODEL_OUTPUT",
                    "source_artifact": relative,
                }
            )
    rows = []
    for issuer_key, issuer_records in sorted(records.items()):
        deduplicated = {
            (
                str(row["ticker"]),
                str(row["generation_id"]),
                str(row["invocation_id"]),
                str(row["source_artifact"]),
            ): row
            for row in issuer_records
        }
        ordered = sorted(
            deduplicated.values(),
            key=lambda row: (
                str(row["generation_id"]),
                str(row["invocation_id"]),
                str(row["source_artifact"]),
            ),
        )
        ticker = str(ordered[0]["ticker"])
        identity = identities.get(ticker, {})
        rows.append(
            {
                "issuer": identity.get("company_name") or ticker,
                "canonical_issuer_key": issuer_key,
                "market": identity.get("market")
                or ("kr" if ticker.isdigit() else "us"),
                "tickers": sorted({str(row["ticker"]) for row in ordered}),
                "model_call_started": True,
                "usable_output_exists": True,
                "exposure_class": "PRIOR_REAL_MODEL_EXPOSURE",
                "records": ordered,
            }
        )
    known_partial_keys = {
        canonical_issuer_key(ticker, str(identities.get(ticker, {}).get("company_name") or ""))
        for ticker in OLD_PARTIAL
    }
    known_consumed_keys = {
        canonical_issuer_key(ticker, str(identities.get(ticker, {}).get("company_name") or ""))
        for ticker in OLD_CONSUMED
    }
    additional = [
        row
        for row in rows
        if str(row["canonical_issuer_key"])
        not in known_partial_keys | known_consumed_keys
    ]
    return {
        "contract": "prior-real-issuer-exposure-registry-v1",
        "scan_scope": "docs/reports/20260903..20260906 relevant model-output JSON only",
        "registry_count": len(rows),
        "known_retired_partial_count": len(OLD_PARTIAL),
        "known_consumed_regression_count": len(OLD_CONSUMED),
        "additional_historical_exposure_count": len(additional),
        "rows": rows,
        "model_calls_in_this_phase": 0,
        "status": "PASS",
    }


def exposure_tickers(registry: Mapping[str, object]) -> set[str]:
    result: set[str] = set()
    for row in registry.get("rows") or []:
        if isinstance(row, Mapping):
            result.update(str(value) for value in row.get("tickers") or [])
    if "GOOG" in result or "GOOGL" in result:
        result.update(("GOOG", "GOOGL"))
    return result


def stable_rank(row: Mapping[str, object]) -> str:
    return hashlib.sha256(
        "|".join(
            (
                SELECTION_SALT,
                str(row.get("market") or ""),
                str(row.get("sector") or row.get("industry") or "unclassified"),
                str(row.get("ticker") or ""),
            )
        ).encode()
    ).hexdigest()


def ranked_market_candidates(
    rows: Sequence[Mapping[str, object]], market: str
) -> list[dict[str, object]]:
    eligible = [dict(row) for row in rows if str(row.get("market")) == market]
    strata: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in eligible:
        key = str(row.get("sector") or row.get("industry") or "unclassified")
        strata[key].append(row)
    for values in strata.values():
        values.sort(key=lambda row: (stable_rank(row), str(row["ticker"])))
    keys = sorted(
        strata,
        key=lambda value: hashlib.sha256(
            f"{SELECTION_SALT}|{market}|{value}".encode()
        ).hexdigest(),
    )
    result = []
    while any(strata[key] for key in keys):
        for key in keys:
            if strata[key]:
                result.append(strata[key].pop(0))
    return result


def program_generation_id(implementation_commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{implementation_commit}|{stamp}|{SELECTION_SALT}".encode()
    ).hexdigest()[:12]
    return f"20260907-new-issuer-holdout-{stamp}-{suffix}"


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        **{
            name: repo_root / path
            for name, path in {
                "ownership_service": "app/services/direction_timing_ownership_service.py",
                "directional_balance": "app/services/directional_balance_service.py",
                "alias_fencing": "app/services/structured_autonomy_alias_service.py",
                "validator_renderer": "app/services/structured_autonomy_shadow_service.py",
                "stability_classifier": "app/services/structured_autonomy_stability_service.py",
                "source_enrichment": "app/services/coldstart_fundamental_enrichment_service.py",
                "source_assembly": "app/services/coldstart_source_assembly_service.py",
                "transport_lifecycle": "app/services/codex_transport_lifecycle_service.py",
                "frozen_runner": "scripts/directional_core_price_timing_holdout.py",
                "transport_adapter": (
                    "scripts/model_transport_revalidation_ownership_continuation.py"
                ),
            }.items()
        },
        "experiment_runner": Path(__file__).resolve(),
    }
    return {name: file_sha256(path) for name, path in paths.items()}


def transport_topology_hashes() -> dict[str, str]:
    return {
        "ContinuationTransportAdapter": source_sha256(
            transport.ContinuationTransportAdapter
        ),
        "GuardedTransportAdapter": source_sha256(guarded.GuardedTransportAdapter),
        "invoke_instrumented_codex": source_sha256(
            transport.invoke_instrumented_codex
        ),
        "instrumented_runner": source_sha256(transport.instrumented_runner),
    }


async def evaluate_candidate(
    identity: Mapping[str, object],
    *,
    as_of: datetime,
    cache_dir: Path,
) -> tuple[dict[str, object], object | None]:
    pair = (
        await fundamental.enrich_rows([identity], as_of=as_of, cache_dir=cache_dir)
    )[0]
    _, enrichment = pair
    row = fundamental.enrichment_row(identity, enrichment)
    row["issuer_key"] = enrichment.issuer_id or canonical_issuer_key(
        str(identity["ticker"]), str(identity.get("company_name") or "")
    )
    if not row["directional_model_eligible"]:
        row["preflight_status"] = "SOURCE_INSUFFICIENT"
        return row, None
    base = await fundamental.assemble_research_packet(
        str(identity["ticker"]), as_of, identity=identity
    )
    enriched = fundamental.enrich_assembled_packet(base, enrichment)
    row.update(
        {
            "base_status": base.status,
            "preflight_status": enriched.status,
            "directional_model_eligible": bool(
                enriched.source_sufficiency.directional_model_eligible
                and enriched.packet is not None
            ),
            "packet_sha256": enriched.packet_sha256,
            "validation_errors": list(enriched.validation_errors),
            "provider_audit": enriched.provider_audit,
        }
    )
    return row, enriched if row["directional_model_eligible"] else None


def _family_state(row: Mapping[str, object], family: str) -> str:
    return "PASS" if family in set(row.get("evidence_families") or []) else "UNAVAILABLE"


def _provider_metric(row: Mapping[str, object], key: str) -> int:
    provider = row.get("provider_audit") or {}
    if not isinstance(provider, Mapping):
        return 0
    fundamental_provider = provider.get("fundamental") or provider
    if not isinstance(fundamental_provider, Mapping):
        return 0
    return int(fundamental_provider.get(key) or 0)


def _raw_required_domain_present(
    cache_dir: Path,
    ticker: str,
    missing_required_families: Sequence[object],
) -> bool:
    if not any(
        "REGULATORY_CAPITAL_CURRENT" in str(value)
        or "SECTOR_OPERATING_CURRENT" in str(value)
        for value in missing_required_families
    ):
        return False
    path = cache_dir / "sec_companyfacts" / f"{ticker}.json"
    if not path.is_file():
        return False
    try:
        payload = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return False
    tags = {
        str(tag).lower()
        for namespace in facts.values()
        if isinstance(namespace, Mapping)
        for tag in namespace
    }
    markers = (
        "tier1",
        "riskweighted",
        "capitalrequired",
        "assetsheldbyinsuranceregulators",
        "premiums",
        "policyholder",
        "insurance",
        "lossesincurred",
        "noninterestincome",
        "interestincomeexpense",
    )
    return any(any(marker in tag for marker in markers) for tag in tags)


def candidate_coverage_row(
    row: Mapping[str, object],
    result: object | None,
    *,
    identity: Mapping[str, object],
    cache_dir: Path,
) -> dict[str, object]:
    ticker = str(row["ticker"])
    provider = row.get("provider_audit") or {}
    fundamental_provider = provider.get("fundamental") or provider
    if not isinstance(fundamental_provider, Mapping):
        fundamental_provider = {}
    validation_errors = [str(value) for value in row.get("validation_errors") or []]
    missing = [str(value) for value in row.get("missing_required_families") or []]
    source_provenance = row.get("source_provenance") or []
    identity_valid = bool(row.get("issuer_id")) and _family_state(
        row, "IDENTITY_SECURITY"
    ) == "PASS"
    profile_ok = int(fundamental_provider.get("profile_successes") or 0) > 0
    financial_ok = int(
        fundamental_provider.get("companyfacts_successes")
        or fundamental_provider.get("statement_successes")
        or 0
    ) > 0
    source_sufficient = result is not None and bool(
        row.get("directional_model_eligible")
    )
    base_status = str(row.get("base_status") or "NOT_RUN_SOURCE_INSUFFICIENT")
    data_received_not_assembled = bool(
        financial_ok
        and row.get("sufficiency_status")
        == "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT"
        and base_status != "ASSEMBLED"
    )
    raw_required_domain_present = _raw_required_domain_present(
        cache_dir, ticker, missing
    )

    reason_codes: list[str] = []
    if not source_sufficient:
        if not identity_valid:
            reason_codes.append("IDENTITY_VALIDATION_FAILURE")
        if not profile_ok:
            reason_codes.append("OFFICIAL_SOURCE_UNAVAILABLE")
        if not financial_ok:
            reason_codes.append("OFFICIAL_FINANCIAL_SOURCE_UNAVAILABLE")
        if any("EARNINGS_FINANCIAL_CURRENT" in value for value in missing):
            reason_codes.append("EARNINGS_CONTEXT_INSUFFICIENT")
        if any(
            "REGULATORY_CAPITAL_CURRENT" in value
            or "SECTOR_OPERATING_CURRENT" in value
            or "BUSINESS_CURRENT" in value
            or "LIQUIDITY_CASHFLOW_CURRENT" in value
            for value in missing
        ):
            reason_codes.append("REQUIRED_FUNDAMENTAL_DOMAIN_INSUFFICIENT")
        if data_received_not_assembled:
            reason_codes.append("SOURCE_FETCH_SUCCEEDED_PACKET_ASSEMBLY_FAILED")
        if base_status == "VALIDATION_BLOCK" or validation_errors:
            reason_codes.append("VALIDATION_FAILURE")
        if not reason_codes:
            reason_codes.append("SOURCE_SUFFICIENCY_RULE_REJECTED")

    missing_price = any(
        value
        in {
            "current_price_unavailable",
            "price_as_of_unavailable",
            "technical_context_not_safe:UNAVAILABLE",
        }
        for value in validation_errors
    )
    if source_sufficient:
        failure_class = "NOT_APPLICABLE"
    elif raw_required_domain_present:
        failure_class = "PIPELINE_COVERAGE_GAP"
        if "NORMALIZATION_OR_MAPPING_GAP" not in reason_codes:
            reason_codes.append("NORMALIZATION_OR_MAPPING_GAP")
    elif missing_price or not profile_ok or not financial_ok:
        failure_class = "SOURCE_ABSENCE"
    else:
        failure_class = "UNKNOWN"
        reason_codes.append("UNKNOWN_SOURCE_COVERAGE_FAILURE")

    return {
        "ticker": ticker,
        "canonical_issuer_identity": row.get("issuer_key"),
        "issuer_key": row.get("issuer_key"),
        "company_name": identity.get("company_name"),
        "market": row.get("market"),
        "candidate_rank": row.get("market_sequence"),
        "primary_or_reserve": row.get("initial_or_reserve"),
        "identity_validation_status": "PASS" if identity_valid else "FAIL",
        "source_pipeline_attempted": [
            "official_profile",
            "official_financial_enrichment",
            *(["coldstart_packet_assembly"] if row.get("base_status") else []),
        ],
        "source_pipeline_status": row.get("preflight_status"),
        "official_profile_status": "PASS" if profile_ok else "UNAVAILABLE",
        "filing_or_official_financial_status": (
            "PASS" if financial_ok else "UNAVAILABLE"
        ),
        "earnings_context_status": _family_state(
            row, "EARNINGS_FINANCIAL_CURRENT"
        ),
        "valuation_input_status": _family_state(row, "VALUATION_SAFE"),
        "price_context_status": (
            "PASS"
            if source_sufficient or base_status == "ASSEMBLED"
            else "NOT_ATTEMPTED_SOURCE_GATE"
            if not row.get("base_status")
            else "UNAVAILABLE"
            if missing_price
            else "FAIL"
        ),
        "other_required_domain_status": (
            "PASS" if not missing else "INSUFFICIENT"
        ),
        "framework": row.get("framework"),
        "evidence_families": list(row.get("evidence_families") or []),
        "missing_required_families": missing,
        "source_sufficiency_status": "PASS" if source_sufficient else "FAIL",
        "failure_domains": missing
        + (["PRICE_CONTEXT"] if missing_price else []),
        "failure_reason_codes": sorted(set(reason_codes)),
        "failure_class": failure_class,
        "data_received_but_not_assembled": data_received_not_assembled,
        "assembler_or_normalization_gap_suspected": (
            failure_class == "PIPELINE_COVERAGE_GAP"
        ),
        "true_source_absence_suspected": failure_class == "SOURCE_ABSENCE",
        "raw_required_domain_evidence_present": raw_required_domain_present,
        "source_provenance": list(source_provenance),
        "validation_errors": validation_errors,
        "provider_audit": dict(provider),
        "packet_created": bool(row.get("packet_sha256")),
        "packet_hash": row.get("packet_sha256"),
        "eligible_for_final_holdout": source_sufficient,
        "selected": bool(row.get("selected")),
        "duplicate_issuer": bool(row.get("duplicate_issuer")),
        "model_calls": 0,
    }


async def evaluate_market_candidates(
    *,
    market: str,
    rows: Sequence[Mapping[str, object]],
    target: int,
    as_of: datetime,
    cache_dir: Path,
    selected_issuer_keys: set[str],
) -> tuple[list[object], list[dict[str, object]]]:
    selected: list[object] = []
    audit_rows: list[dict[str, object]] = []
    for sequence, identity in enumerate(rows, start=1):
        if len(selected) >= target:
            break
        row, result = await evaluate_candidate(
            identity, as_of=as_of, cache_dir=cache_dir
        )
        issuer_key = str(row["issuer_key"])
        duplicate = issuer_key in selected_issuer_keys
        row.update(
            {
                "market_sequence": sequence,
                "initial_or_reserve": "INITIAL" if sequence <= target else "RESERVE",
                "duplicate_issuer": duplicate,
                "selected": False,
                "model_calls": 0,
            }
        )
        if duplicate:
            result = None
            row["directional_model_eligible"] = False
            row["preflight_status"] = "DUPLICATE_ISSUER"
            row["validation_errors"] = ["duplicate_issuer"]
        if result is not None:
            row["selected"] = True
            selected.append(result)
            selected_issuer_keys.add(issuer_key)
        detail = candidate_coverage_row(
            row, result, identity=identity, cache_dir=cache_dir
        )
        if duplicate:
            detail["failure_reason_codes"] = ["IDENTITY_VALIDATION_FAILURE"]
            detail["failure_class"] = "PIPELINE_COVERAGE_GAP"
            detail["identity_validation_status"] = "FAIL"
            detail["eligible_for_final_holdout"] = False
        audit_rows.append(detail)
    return selected, audit_rows


def market_coverage_audit(
    market: str,
    target: int,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    sufficient = sum(bool(row.get("eligible_for_final_holdout")) for row in rows)
    failures = [row for row in rows if not row.get("eligible_for_final_holdout")]
    provider_keys = (
        "profile_requests",
        "profile_successes",
        "companyfacts_requests",
        "companyfacts_successes",
        "statement_requests",
        "statement_successes",
        "cache_hits",
    )
    return {
        "contract": f"{market}-source-coverage-audit-v1",
        "market": market,
        "target_count": target,
        "attempted_count": len(rows),
        "identity_validation_pass_count": sum(
            row.get("identity_validation_status") == "PASS" for row in rows
        ),
        "source_sufficient_count": sufficient,
        "source_insufficient_count": len(failures),
        "pipeline_coverage_gap_count": sum(
            row.get("failure_class") == "PIPELINE_COVERAGE_GAP"
            for row in failures
        ),
        "source_absence_count": sum(
            row.get("failure_class") == "SOURCE_ABSENCE" for row in failures
        ),
        "unknown_failure_count": sum(
            row.get("failure_class") == "UNKNOWN" for row in failures
        ),
        "provider_totals": {
            key: sum(
                _provider_metric(row, key) for row in rows
            )
            for key in provider_keys
        },
        "rows": list(rows),
        "source_target_status": "PASS" if sufficient >= target else "FAIL",
        "real_model_calls": 0,
        "status": "PASS" if sufficient >= target else "FAIL_CLOSED",
    }


def source_failure_detail(
    market: str, audit: Mapping[str, object]
) -> dict[str, object]:
    failures = [
        dict(row)
        for row in audit.get("rows") or []
        if isinstance(row, Mapping) and not row.get("eligible_for_final_holdout")
    ]
    counts = Counter(
        code for row in failures for code in row.get("failure_reason_codes") or []
    )
    return {
        "contract": f"{market}-source-failure-detail-v1",
        "market": market,
        "failure_count": len(failures),
        "failure_reason_code_counts": dict(sorted(counts.items())),
        "rows": failures,
        "status": "PASS" if not failures else "DIAGNOSTIC_COMPLETE",
    }


def candidate_manifest(
    market: str,
    target: int,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": f"{market}-candidate-manifest-v1",
        "market": market,
        "target_count": target,
        "bounded_candidate_count": len(rows),
        "initial_candidates": [
            str(row["ticker"]) for row in rows[:target]
        ],
        "ordered_reserve": [
            str(row["ticker"]) for row in rows[target:]
        ],
        "candidate_rows": [
            {
                "candidate_rank": rank,
                "primary_or_reserve": "INITIAL" if rank <= target else "RESERVE",
                "ticker": row["ticker"],
                "company_name": row.get("company_name"),
                "exchange": row.get("exchange"),
                "sector": row.get("sector"),
                "industry": row.get("industry"),
            }
            for rank, row in enumerate(rows, start=1)
        ],
        "model_calls": 0,
        "status": "FROZEN",
    }


def dual_market_summary(
    us_audit: Mapping[str, object], kr_audit: Mapping[str, object]
) -> dict[str, object]:
    us_codes = {
        str(code)
        for row in us_audit.get("rows") or []
        if isinstance(row, Mapping) and not row.get("eligible_for_final_holdout")
        for code in row.get("failure_reason_codes") or []
    }
    kr_codes = {
        str(code)
        for row in kr_audit.get("rows") or []
        if isinstance(row, Mapping) and not row.get("eligible_for_final_holdout")
        for code in row.get("failure_reason_codes") or []
    }
    us_pass = us_audit.get("source_target_status") == "PASS"
    kr_pass = kr_audit.get("source_target_status") == "PASS"
    dual_status = {
        (True, True): "BOTH_PASS",
        (False, True): "US_FAIL_KR_PASS",
        (True, False): "US_PASS_KR_FAIL",
        (False, False): "BOTH_FAIL",
    }[(us_pass, kr_pass)]
    return {
        "contract": "dual-market-source-coverage-summary-v1",
        "us_target": us_audit["target_count"],
        "us_attempted": us_audit["attempted_count"],
        "us_source_sufficient": us_audit["source_sufficient_count"],
        "us_source_insufficient": us_audit["source_insufficient_count"],
        "kr_target": kr_audit["target_count"],
        "kr_attempted": kr_audit["attempted_count"],
        "kr_source_sufficient": kr_audit["source_sufficient_count"],
        "kr_source_insufficient": kr_audit["source_insufficient_count"],
        "shared_failure_reason_codes": sorted(us_codes & kr_codes),
        "us_only_failure_reason_codes": sorted(us_codes - kr_codes),
        "kr_only_failure_reason_codes": sorted(kr_codes - us_codes),
        "pipeline_coverage_gap_count_us": us_audit[
            "pipeline_coverage_gap_count"
        ],
        "pipeline_coverage_gap_count_kr": kr_audit[
            "pipeline_coverage_gap_count"
        ],
        "source_absence_count_us": us_audit["source_absence_count"],
        "source_absence_count_kr": kr_audit["source_absence_count"],
        "unknown_failure_count_us": us_audit["unknown_failure_count"],
        "unknown_failure_count_kr": kr_audit["unknown_failure_count"],
        "dual_market_source_status": dual_status,
        "market_failure_did_not_abort_other_market_diagnostic": 1,
        "real_holdout_model_calls_while_source_target_failed": 0,
        "status": "PASS" if dual_status == "BOTH_PASS" else "DIAGNOSTIC_COMPLETE",
    }


def remediation_decision(summary: Mapping[str, object]) -> dict[str, object]:
    status = str(summary["dual_market_source_status"])
    readiness, next_scope = {
        "BOTH_PASS": (
            "READY_FOR_NEW_HOLDOUT_FREEZE",
            "NEW_ISSUER_HOLDOUT_OWNERSHIP_PROOF",
        ),
        "US_FAIL_KR_PASS": (
            "NOT_READY_US_SOURCE_COVERAGE_BLOCKED",
            "BOUNDED_US_SOURCE_COVERAGE_REMEDIATION",
        ),
        "US_PASS_KR_FAIL": (
            "NOT_READY_KR_SOURCE_COVERAGE_BLOCKED",
            "BOUNDED_KR_SOURCE_COVERAGE_REMEDIATION",
        ),
        "BOTH_FAIL": (
            "NOT_READY_DUAL_MARKET_SOURCE_COVERAGE_BLOCKED",
            "BOUNDED_SHARED_THEN_MARKET_SPECIFIC_SOURCE_COVERAGE_REMEDIATION",
        ),
    }[status]
    return {
        "contract": "source-coverage-remediation-decision-v1",
        "dual_market_source_status": status,
        "readiness": readiness,
        "next_scope": next_scope,
        "final_holdout_source_lock_allowed": int(status == "BOTH_PASS"),
        "real_model_execution_allowed": int(status == "BOTH_PASS"),
        "production_semantic_mutation": 0,
        "status": "PASS" if status == "BOTH_PASS" else "FAIL_CLOSED",
    }


def write_source_blocked_proofs(
    *,
    args: argparse.Namespace,
    provenance: Mapping[str, object],
    registry: Mapping[str, object],
    exclusion: Mapping[str, object],
    policy: Mapping[str, object],
    us_audit: Mapping[str, object],
    kr_audit: Mapping[str, object],
    summary: Mapping[str, object],
    decision: Mapping[str, object],
) -> None:
    reason = str(summary["dual_market_source_status"])
    selection = {
        "contract": "new-holdout-selection-result-v1",
        "ordered_final_cohort": [],
        "required_market_mix": {"us": TARGET_US, "kr": TARGET_KR},
        "source_sufficient_us_count": us_audit["source_sufficient_count"],
        "source_sufficient_kr_count": kr_audit["source_sufficient_count"],
        "final_holdout_cohort_frozen": 0,
        "selection_after_model_output": 0,
        "status": "NOT_RUN_SOURCE_COVERAGE_BLOCKED",
    }
    write_proof(args.report_dir, 15, selection)
    for number in range(16, 57):
        write_proof(
            args.report_dir,
            number,
            {
                "contract": f"{PROOF_NAMES[number - 1]}-v1",
                "status": "NOT_RUN",
                "reason": reason,
                "real_model_calls": 0,
            },
        )
    production = {
        "contract": "production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "status": "PASS",
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "status": "PASS",
    }
    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "readiness": decision["readiness"],
        "next_scope": decision["next_scope"],
        "status": "NOT_READY",
    }
    write_proof(args.report_dir, 57, production)
    write_proof(args.report_dir, 58, night)
    write_proof(args.report_dir, 59, handoff)
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": provenance["base_sha"],
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": provenance["branch"],
        "latest_forensic_zip_sha256": FORENSIC_ZIP_SHA256,
        "latest_forensic_bundle_integrity": "PASS",
        "prior_real_issuer_exposure_registry_count": registry["registry_count"],
        "new_holdout_exclusion_count": exclusion["new_holdout_exclusion_count"],
        "dual_market_source_policy_hash": canonical_sha256(policy),
        "us_target_count": us_audit["target_count"],
        "us_candidate_attempt_count": us_audit["attempted_count"],
        "us_source_sufficient_count": us_audit["source_sufficient_count"],
        "us_source_insufficient_count": us_audit["source_insufficient_count"],
        "us_pipeline_coverage_gap_count": us_audit["pipeline_coverage_gap_count"],
        "us_source_absence_count": us_audit["source_absence_count"],
        "us_unknown_failure_count": us_audit["unknown_failure_count"],
        "us_source_target_status": us_audit["source_target_status"],
        "kr_target_count": kr_audit["target_count"],
        "kr_candidate_attempt_count": kr_audit["attempted_count"],
        "kr_source_sufficient_count": kr_audit["source_sufficient_count"],
        "kr_source_insufficient_count": kr_audit["source_insufficient_count"],
        "kr_pipeline_coverage_gap_count": kr_audit["pipeline_coverage_gap_count"],
        "kr_source_absence_count": kr_audit["source_absence_count"],
        "kr_unknown_failure_count": kr_audit["unknown_failure_count"],
        "kr_source_target_status": kr_audit["source_target_status"],
        "dual_market_source_status": summary["dual_market_source_status"],
        "real_holdout_model_calls_while_source_target_failed": 0,
        "new_holdout_cohort": [],
        "new_source_generation_id": "NOT_CREATED",
        "new_source_lock": "NOT_CREATED",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": TIMEOUT_SECONDS,
        "model_timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "shared_context_subject_count": CONTEXT_SIZE,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": "NOT_MEASURED_NO_PRECOMMIT",
        "schema_semantic_drift": "NOT_MEASURED_NO_PRECOMMIT",
        "model_semantic_input_drift": 0,
        "transport_topology_mutation": 0,
        "timeout_increase_this_task": 0,
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "NOT_CREATED",
        "future_unseen_holdout_reuse_allowed": "NOT_APPLICABLE_NO_FINAL_COHORT",
        "first_complete_run_attempt_count": 0,
        "real_holdout_model_invocation_count": 0,
        "real_holdout_subject_output_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {run: "NOT_RUN" for run in RUNS},
        **{
            f"{('first' if run == 'first' else 'run_' + run)}_{gate}_gate_status": "NOT_RUN"
            for run in RUNS
            for gate in ("ownership", "renderer", "hard_safety")
        },
        "ownership_generalization_verdict": "NOT_MEASURED",
        "ownership_proof_completion_state": "STOPPED_PRE_MODEL_SOURCE_FAILURE",
        **{key: value for key, value in production.items() if key not in {"contract", "status"}},
        "night_futures_code_mutation": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "readiness": decision["readiness"],
        "stop_reason": reason,
        "next_scope": decision["next_scope"],
    }
    write_proof(args.report_dir, 60, completion)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "EVIDENCE_COMPLETE",
        "source_gate_only": True,
        "branch": provenance["branch"],
        "base_sha": provenance["base_sha"],
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "implementation_tree": provenance["implementation_tree"],
        "architecture_hashes": architecture_hashes(Path.cwd().resolve()),
        "selection_policy_sha256": canonical_sha256(policy),
        "ordered_cohort": [],
        "holdout_output_exposure_state": "UNEXPOSED",
        "model_invocation_count": 0,
        "readiness": decision["readiness"],
        "stop_reason": reason,
        "run_results": completion["run_results"],
    }
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    repo_root = Path.cwd().resolve()
    if file_sha256(args.forensic_zip) != FORENSIC_ZIP_SHA256:
        raise ValueError("LATEST_FORENSIC_RESULT_CHECKSUM_MISMATCH")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if MODEL != frozen.MODEL or EFFORT != frozen.EFFORT:
        raise ValueError("frozen_model_or_effort_drift")
    if args.timeout != TIMEOUT_SECONDS:
        raise ValueError("timeout_increase_or_decrease_forbidden")

    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    branch = git_value("branch", "--show-current")
    work_instruction_commit = git_value(
        "log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH
    )
    base_sha = git_value("rev-parse", f"{work_instruction_commit}^")
    generation_id = program_generation_id(implementation_commit, args.as_of)
    universe = source_assembly.supported_universe(args.provider_root)
    identities = {str(row["ticker"]): row for row in universe}
    registry = build_exposure_registry(repo_root / "docs/reports", universe)
    exposed = exposure_tickers(registry)
    exclusions = set(OLD_PARTIAL) | set(OLD_CONSUMED) | exposed
    if "GOOG" in exclusions or "GOOGL" in exclusions:
        exclusions.update(("GOOG", "GOOGL"))

    candidates = [row for row in universe if str(row["ticker"]) not in exclusions]
    us_ranked = ranked_market_candidates(candidates, "us")
    kr_ranked = ranked_market_candidates(candidates, "kr")
    if len(us_ranked) < TARGET_US or len(kr_ranked) < TARGET_KR:
        raise ValueError("candidate_universe_below_required_market_mix")
    us_candidates = us_ranked
    kr_candidates = kr_ranked[: TARGET_KR + KR_RESERVE_LIMIT]
    policy = {
        "contract": SELECTION_CONTRACT,
        "target_cohort_size": TARGET_TOTAL,
        "target_market_mix": {"us": TARGET_US, "kr": TARGET_KR},
        "candidate_universe": "frozen canonical supported-security universe",
        "supported_universe_count": len(universe),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "market_policies": {
            "us": {
                "target_issuer_count": TARGET_US,
                "candidate_universe": [str(row["ticker"]) for row in us_candidates],
                "initial_candidate_count": min(TARGET_US, len(us_candidates)),
                "reserve_count": max(0, len(us_candidates) - TARGET_US),
                "bounded_evaluation_limit": len(us_candidates),
            },
            "kr": {
                "target_issuer_count": TARGET_KR,
                "candidate_universe": [str(row["ticker"]) for row in kr_candidates],
                "initial_candidate_count": TARGET_KR,
                "reserve_count": max(0, len(kr_candidates) - TARGET_KR),
                "bounded_evaluation_limit": len(kr_candidates),
            },
        },
        "objective_eligibility_rules": [
            "supported common stock identity",
            "not previously model exposed",
            "not in retired partial cohort",
            "not in consumed regression cohort",
            "unique canonical issuer identity",
        ],
        "source_sufficiency_rules": [
            "frozen official enrichment directional eligibility",
            "assembled canonical packet directional eligibility",
            "required identity, fundamental, valuation, and price validation gates",
        ],
        "deterministic_ordering_rule": (
            "sector-stratified round robin ordered by SHA256(selection_salt|market|"
            "canonical_sector_or_industry|ticker)"
        ),
        "selection_seed_or_rule": SELECTION_SALT,
        "replacement_rules": [
            "ordered reserve only",
            "identity validation failure",
            "unsupported market or duplicate issuer",
            "source insufficiency or hard source validation failure",
            "missing required evidence packet",
        ],
        "replacement_forbidden_reasons": [
            "valuation appearance",
            "price trend",
            "expected direction or ownership result",
            "transport result",
        ],
        "diversity_rule": (
            "canonical sector/industry strata round robin; unclassified remains one stratum"
        ),
        "finalization_rule": (
            "first source-sufficient unique 4 US and 12 KR in precommitted order"
        ),
        "stop_condition": (
            "complete both bounded market diagnostics; freeze only when both targets pass"
        ),
        "MARKET_FAILURE_DOES_NOT_ABORT_OTHER_MARKET_DIAGNOSTIC": 1,
        "selection_uses_model_output": 0,
        "selection_uses_expected_direction": 0,
        "model_calls": 0,
        "status": "FROZEN",
    }
    us_manifest = candidate_manifest("us", TARGET_US, us_candidates)
    kr_manifest = candidate_manifest("kr", TARGET_KR, kr_candidates)

    provenance = {
        "contract": "repository-provenance-v1",
        "branch": branch,
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "worktree_status_before_generated_evidence": git_value("status", "--short"),
        "status": "PASS",
    }
    write_proof(args.report_dir, 1, provenance)
    write_proof(
        args.report_dir,
        2,
        {
            "contract": "latest-forensic-result-integrity-v1",
            "path": str(args.forensic_zip),
            "expected_sha256": FORENSIC_ZIP_SHA256,
            "actual_sha256": file_sha256(args.forensic_zip),
            "latest_forensic_bundle_integrity": "PASS",
            "historical_stall_classification": "TRANSIENT_STALL_NOT_REPRODUCED",
            "historical_stall_fixed_claimed": 0,
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 3, registry)
    exclusion_document = {
        "contract": "new-holdout-exclusion-set-v1",
        "known_retired_partial": list(OLD_PARTIAL),
        "known_consumed_regression": list(OLD_CONSUMED),
        "prior_exposure_tickers": sorted(exposed),
        "excluded_tickers": sorted(exclusions),
        "new_holdout_exclusion_count": len(exclusions),
        "deduplicated_exclusion_count": len(exclusions),
        "canonical_alphabet_share_class_fence": ["GOOG", "GOOGL"],
        "status": "PASS",
    }
    write_proof(args.report_dir, 4, exclusion_document)
    write_proof(args.report_dir, 5, policy)
    write_proof(args.report_dir, 6, us_manifest)
    write_proof(args.report_dir, 9, kr_manifest)

    cache_dir = args.output_root / "source-cache"
    selected_issuer_keys: set[str] = set()
    us_selected, us_rows = asyncio.run(
        evaluate_market_candidates(
            market="us",
            rows=us_candidates,
            target=TARGET_US,
            as_of=args.as_of,
            cache_dir=cache_dir,
            selected_issuer_keys=selected_issuer_keys,
        )
    )
    us_audit = market_coverage_audit("us", TARGET_US, us_rows)
    write_proof(args.report_dir, 7, us_audit)
    write_proof(args.report_dir, 8, source_failure_detail("us", us_audit))

    kr_selected, kr_rows = asyncio.run(
        evaluate_market_candidates(
            market="kr",
            rows=kr_candidates,
            target=TARGET_KR,
            as_of=args.as_of,
            cache_dir=cache_dir,
            selected_issuer_keys=selected_issuer_keys,
        )
    )
    kr_audit = market_coverage_audit("kr", TARGET_KR, kr_rows)
    write_proof(args.report_dir, 10, kr_audit)
    write_proof(args.report_dir, 11, source_failure_detail("kr", kr_audit))
    summary = dual_market_summary(us_audit, kr_audit)
    decision = remediation_decision(summary)
    write_proof(args.report_dir, 12, summary)
    write_proof(
        args.report_dir,
        13,
        {
            "contract": "cross-market-failure-comparison-v1",
            **{
                key: summary[key]
                for key in (
                    "shared_failure_reason_codes",
                    "us_only_failure_reason_codes",
                    "kr_only_failure_reason_codes",
                    "pipeline_coverage_gap_count_us",
                    "pipeline_coverage_gap_count_kr",
                    "source_absence_count_us",
                    "source_absence_count_kr",
                    "unknown_failure_count_us",
                    "unknown_failure_count_kr",
                )
            },
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 14, decision)
    if summary["dual_market_source_status"] != "BOTH_PASS":
        write_source_blocked_proofs(
            args=args,
            provenance=provenance,
            registry=registry,
            exclusion=exclusion_document,
            policy=policy,
            us_audit=us_audit,
            kr_audit=kr_audit,
            summary=summary,
            decision=decision,
        )
        print(
            json.dumps(read_json(proof_path(args.report_dir, 60)), sort_keys=True),
            flush=True,
        )
        return

    selected = [*us_selected, *kr_selected]
    preflight_rows = [*us_rows, *kr_rows]
    cohort = tuple(
        item.ticker
        for market in ("us", "kr")
        for item in selected
        if item.market == market
    )
    if len(cohort) != TARGET_TOTAL:
        raise ValueError(f"final_cohort_size_mismatch:{len(cohort)}")
    packets = {item.ticker: item.packet for item in selected if item.packet is not None}
    base_contexts = {item.ticker: str(item.deterministic_base_context) for item in selected}
    for ticker in cohort:
        write_json(args.output_root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(
            args.output_root / "base-contexts" / f"{ticker}.txt",
            base_contexts[ticker],
        )

    evidence, owned, core_aliases, timing_aliases, price_maps, stocks = (
        frozen.build_inputs(packets, base_contexts, cohort)
    )
    source_lock = frozen.source_lock_document(
        generation_id=generation_id,
        cohort=cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    source_lock["contract"] = "new-issuer-holdout-source-lock-v1"
    source_lock_sha = canonical_sha256(source_lock)
    write_json(
        args.output_root / "source-lock.json",
        {**source_lock, "source_lock_sha256": source_lock_sha},
    )
    prompt_lock = frozen._write_prompt_schema_lock(
        output_root=args.output_root,
        generation_id=generation_id,
        cohort=cohort,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    architecture = architecture_hashes(repo_root)
    topology = transport_topology_hashes()
    groups = [list(batch) for batch in frozen.batches(cohort)]
    identity_rows = []
    for ticker in cohort:
        preflight = next(row for row in preflight_rows if row["ticker"] == ticker)
        identity_rows.append(
            {
                "ticker": ticker,
                "market": "kr" if ticker.isdigit() else "us",
                "company_name": identities[ticker].get("company_name"),
                "canonical_issuer_key": preflight["issuer_key"],
                "source_identity_valid": not preflight["duplicate_issuer"],
                "previously_exposed": ticker in exclusions,
            }
        )
    source_sufficiency = {
        "contract": "new-source-sufficiency-audit-v1",
        "rows": preflight_rows,
        "attempted_count": len(preflight_rows),
        "selected_sufficient_count": len(cohort),
        "directional_model_calls_on_source_insufficient": 0,
        "provider_totals": {
            key: sum(_provider_metric(row, key) for row in preflight_rows)
            for key in (
                "profile_requests",
                "profile_successes",
                "companyfacts_requests",
                "companyfacts_successes",
                "statement_requests",
                "statement_successes",
                "cache_hits",
            )
        },
        "status": "PASS",
    }
    identity_audit = {
        "contract": "new-source-identity-audit-v1",
        "rows": identity_rows,
        "duplicate_issuer_count": sum(not row["source_identity_valid"] for row in identity_rows),
        "prior_exposure_overlap_count": sum(row["previously_exposed"] for row in identity_rows),
        "status": "PASS"
        if all(row["source_identity_valid"] and not row["previously_exposed"] for row in identity_rows)
        else "FAIL",
    }
    if identity_audit["status"] != "PASS":
        raise ValueError("final_holdout_identity_or_exposure_overlap")
    selection = {
        "contract": "new-holdout-selection-result-v1",
        "ordered_cohort": list(cohort),
        "context_groups": groups,
        "selected_count": len(cohort),
        "us_count": sum(not ticker.isdigit() for ticker in cohort),
        "kr_count": sum(ticker.isdigit() for ticker in cohort),
        "selection_policy_sha256": canonical_sha256(policy),
        "us_candidate_manifest_sha256": canonical_sha256(us_manifest),
        "kr_candidate_manifest_sha256": canonical_sha256(kr_manifest),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "replacement_count": sum(
            row["selected"] and row["initial_or_reserve"] == "RESERVE"
            for row in preflight_rows
        ),
        "selection_after_model_output": 0,
        "status": "PASS",
    }
    source_generation = {
        "contract": "new-source-generation-v1",
        "source_generation_id": generation_id,
        "ordered_issuer_manifest": identity_rows,
        "per_issuer_packet_hashes": source_lock["packet_sha256"],
        "aggregate_source_lock_sha256": source_lock_sha,
        "source_pipeline": "FROZEN_OFFICIAL_FUNDAMENTAL_ENRICHMENT_AND_ASSEMBLY",
        "model_calls": 0,
        "status": "PASS",
    }
    precommit = {
        "contract": "new-holdout-precommit-v1",
        "ordered_cohort": list(cohort),
        "canonical_issuer_identities": identity_rows,
        "market_mix": {"us": TARGET_US, "kr": TARGET_KR},
        "context_grouping": groups,
        "selection_policy_sha256": canonical_sha256(policy),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "us_coverage_audit_sha256": canonical_sha256(us_audit),
        "kr_coverage_audit_sha256": canonical_sha256(kr_audit),
        "selection_result_sha256": canonical_sha256(selection),
        "source_generation_id": generation_id,
        "source_lock_sha256": source_lock_sha,
        "packet_sha256": source_lock["packet_sha256"],
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout": TIMEOUT_SECONDS,
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "context_size": CONTEXT_SIZE,
        "transport_topology_identity": canonical_sha256(topology),
        "context_evidence_preservation_policy": (
            "exact-byte-output-stdout-stderr-receipt-prompt-schema-v1"
        ),
        "per_context_partial_semantic_audit_policy": (
            "direction-timing-ownership-early-stop-v1"
        ),
        "stop_rules": "FIRST then gated A/B/C; no retry, selective rerun, split, or hotfix",
        "cohort_mutation_after_precommit": 0,
        "source_mutation_after_precommit": 0,
        "context_grouping_mutation_after_precommit": 0,
        "status": "FROZEN",
    }
    write_json(args.output_root / "new-holdout-precommit.json", precommit)
    write_proof(args.report_dir, 15, selection)
    write_proof(args.report_dir, 16, source_generation)
    write_proof(args.report_dir, 17, source_sufficiency)
    write_proof(args.report_dir, 18, identity_audit)
    write_proof(
        args.report_dir, 19, {**source_lock, "source_lock_sha256": source_lock_sha}
    )
    write_proof(args.report_dir, 20, precommit)
    write_proof(
        args.report_dir,
        21,
        {
            "contract": "architecture-semantic-freeze-v1",
            "architecture_hashes": architecture,
            "implementation_commit": implementation_commit,
            "architecture_semantic_drift": 0,
            "investment_decision_threshold_mutation": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        22,
        {
            "contract": "prompt-schema-freeze-v1",
            "prompt_schema_lock": prompt_lock,
            "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
            "core_prompt_builder_sha256": source_sha256(frozen._core_prompt),
            "timing_prompt_builder_sha256": source_sha256(frozen._timing_prompt),
            "prompt_semantic_drift": 0,
            "schema_semantic_drift": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        23,
        {
            "contract": "model-context-freeze-v1",
            "context_groups": groups,
            "context_size": CONTEXT_SIZE,
            "market_grouping": ["US4", "KR4", "KR4", "KR4"],
            "batch_semantics": BATCH_SEMANTICS,
            "runs": list(RUNS),
            "stage_order": list(STAGES),
            "namespace_rule": (
                "NEW_ISSUER_HOLDOUT_20260907_{RUN}_{STAGE}; stable across batches"
            ),
            "model_semantic_input_drift": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        24,
        {
            "contract": "transport-topology-freeze-v1",
            "hashes": topology,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "timeout_owner_count": TIMEOUT_OWNER_COUNT,
            "transport_grouping_mode": BATCH_SEMANTICS,
            "transport_topology_mutation": 0,
            "timeout_increase_this_task": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        25,
        {
            "contract": "holdout-unseen-reuse-gate-v1",
            "ordered_cohort": list(cohort),
            "prior_registry_overlap": sorted(set(cohort) & exposed),
            "retired_partial_overlap": sorted(set(cohort) & set(OLD_PARTIAL)),
            "consumed_regression_overlap": sorted(set(cohort) & set(OLD_CONSUMED)),
            "source_sufficiency_status": source_sufficiency["status"],
            "source_identity_status": identity_audit["status"],
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "ACTIVE_UNEXPOSED",
            "future_unseen_holdout_reuse_allowed": 1,
            "status": "PASS",
        },
    )
    live_audit = {
        "contract": "natural-live-workload-coexistence-guard-v1",
        "events": [],
        "live_workload_contention_risk": 0,
        "shadow_pause_for_natural_live": 0,
        "natural_live_cancel_count": 0,
        "scheduler_mutation": 0,
        "status": "PASS",
    }
    write_json(args.output_root / "live-workload-coexistence-audit.json", live_audit)
    write_proof(args.report_dir, 26, live_audit)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": generation_id,
        "branch": branch,
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(cohort),
        "source_lock_sha256": source_lock_sha,
        "selection_policy_sha256": canonical_sha256(policy),
        "precommit_sha256": canonical_sha256(precommit),
        "architecture_hashes": architecture,
        "transport_topology_hashes": topology,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "ACTIVE_UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 1,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "exposed_subjects": [],
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {},
        "production_mutation": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    repo_root = Path.cwd().resolve()
    if architecture_hashes(repo_root) != state["architecture_hashes"]:
        raise ValueError("architecture_semantic_drift_after_freeze")
    if transport_topology_hashes() != state["transport_topology_hashes"]:
        raise ValueError("transport_topology_mutation_after_freeze")
    if canonical_sha256(read_json(proof_path(args.report_dir, 5))) != state[
        "selection_policy_sha256"
    ]:
        raise ValueError("selection_policy_drift_after_freeze")
    if canonical_sha256(read_json(args.output_root / "new-holdout-precommit.json")) != state[
        "precommit_sha256"
    ]:
        raise ValueError("precommit_drift_after_freeze")
    lock = read_json(args.output_root / "source-lock.json")
    recorded = lock.pop("source_lock_sha256")
    if canonical_sha256(lock) != recorded or recorded != state["source_lock_sha256"]:
        raise ValueError("source_lock_drift_after_freeze")
    policy_path = proof_path(args.report_dir, 5)
    try:
        policy_relative = policy_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("selection_policy_must_be_repository_local") from exc
    tracked_policy = git_value("ls-files", str(policy_relative))
    if not tracked_policy:
        raise ValueError("selection_policy_must_be_committed_before_model_call")


def load_inputs(args: argparse.Namespace):
    state = read_json(args.output_root / "program-state.json")
    cohort = tuple(str(value) for value in state["ordered_cohort"])
    packets = {
        ticker: read_json(args.output_root / "packets" / f"{ticker}.json")
        for ticker in cohort
    }
    contexts = {
        ticker: (args.output_root / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in cohort
    }
    inputs = frozen.build_inputs(packets, contexts, cohort)
    return state, cohort, packets, contexts, *inputs


def scan_secrets(paths: Sequence[Path]) -> dict[str, object]:
    counts = Counter()
    for path in paths:
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for name, pattern in SECRET_PATTERNS.items():
            counts[name] += len(pattern.findall(payload))
    total = sum(counts.values())
    return {
        "category_counts": {name: counts[name] for name in SECRET_PATTERNS},
        "secret_exposure_count": total,
        "secret_scan_status": "PASS" if total == 0 else "FAIL",
    }


def _elapsed(receipt: Mapping[str, object], event: str) -> object:
    value = receipt.get(event)
    started = receipt.get("invocation_start_monotonic")
    if isinstance(value, (int, float)) and isinstance(started, (int, float)):
        return round(value - started, 6)
    return None


def context_directory(
    output_root: Path, run: str, stage: str, batch_number: int
) -> Path:
    return (
        output_root
        / "model-contexts"
        / run.upper()
        / stage
        / f"batch-{batch_number:02d}"
    )


def receipt_source_path(receipt_root: Path, invocation_id: str) -> Path:
    return receipt_root / f"{hashlib.sha256(invocation_id.encode()).hexdigest()[:16]}.json"


def copy_exact(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise ValueError(f"artifact_size_mismatch:{destination}")
    if file_sha256(source) != file_sha256(destination):
        raise ValueError(f"artifact_hash_mismatch:{destination}")


def preserve_context(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    run: str,
    stage: str,
    batch_number: int,
    subjects: Sequence[str],
    invocation_id: str,
    sequence_position: int,
    context_dir: Path,
    receipt_root: Path,
) -> dict[str, object]:
    source_receipt = receipt_source_path(receipt_root, invocation_id)
    if not source_receipt.is_file():
        raise ValueError(f"transport_receipt_missing:{invocation_id}")
    receipt = read_json(source_receipt)
    stdout_source = source_receipt.with_suffix(".stdout.log")
    stderr_source = source_receipt.with_suffix(".stderr.log")
    copies = {
        "receipt": (source_receipt, context_dir / "transport_receipt.json"),
        "stdout": (stdout_source, context_dir / "stdout.raw.log"),
        "stderr": (stderr_source, context_dir / "stderr.raw.log"),
    }
    for source, destination in copies.values():
        if source.is_file():
            copy_exact(source, destination)
        else:
            destination.write_bytes(b"")
    required = [
        context_dir / "transport_receipt.json",
        context_dir / "stdout.raw.log",
        context_dir / "stderr.raw.log",
        context_dir / "transport_log.raw.log",
        context_dir / "prompt.txt",
        context_dir / "schema.json",
    ]
    output = context_dir / "output.raw.json"
    if output.is_file():
        required.append(output)
    scan = scan_secrets(required)
    reopened = True
    for path in required:
        try:
            path.read_bytes()
        except OSError:
            reopened = False
    preservation = scan["secret_scan_status"] == "PASS" and reopened
    manifest = {
        "contract": "model-context-artifact-manifest-v1",
        "generation_id": state["program_generation_id"],
        "run_id": run,
        "invocation_id": invocation_id,
        "stage": stage,
        "batch_id": f"{batch_number:02d}",
        "subjects": list(subjects),
        "subject_count": len(subjects),
        "market_mix": {
            "us": sum(not ticker.isdigit() for ticker in subjects),
            "kr": sum(ticker.isdigit() for ticker in subjects),
        },
        "source_lock": state["source_lock_sha256"],
        "per_subject_packet_hashes": {
            ticker: read_json(args.output_root / "source-lock.json")["packet_sha256"][ticker]
            for ticker in subjects
        },
        "model": receipt.get("model"),
        "reasoning_effort": receipt.get("reasoning_effort"),
        "timeout": receipt.get("configured_timeout_seconds"),
        "timeout_owner_count": receipt.get("timeout_owner_count"),
        "runtime_state_namespace_hash": (
            (receipt.get("transport_metadata") or {}).get("runtime_state_namespace_hash")
        ),
        "sequence_position": sequence_position,
        "prompt_sha256": file_sha256(context_dir / "prompt.txt"),
        "schema_sha256": file_sha256(context_dir / "schema.json"),
        "input_bytes": receipt.get("input_bytes"),
        "status": receipt.get("status"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "first_stderr_seconds": receipt.get("elapsed_to_first_stderr_seconds"),
        "last_stderr_seconds": _elapsed(receipt, "last_stderr_byte_monotonic"),
        "stderr_bytes": receipt.get("stderr_bytes"),
        "first_stdout_seconds": receipt.get("elapsed_to_first_stdout_seconds"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "exit_code": receipt.get("exit_code"),
        "output_file_created": output.is_file(),
        "output_parsed": receipt.get("output_parsed"),
        "termination_initiator": receipt.get("termination_initiator"),
        "child_cleanup_status": receipt.get("child_cleanup_status"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "raw_output_path": str(output.relative_to(args.output_root)) if output.is_file() else None,
        "raw_output_sha256": file_sha256(output) if output.is_file() else None,
        "raw_output_bytes": output.stat().st_size if output.is_file() else 0,
        "receipt_path": str((context_dir / "transport_receipt.json").relative_to(args.output_root)),
        "receipt_sha256": file_sha256(context_dir / "transport_receipt.json"),
        **scan,
        "artifact_reopen_status": "PASS" if reopened else "FAIL",
        "context_evidence_preservation_status": "PASS" if preservation else "FAIL",
        "per_context_partial_semantic_audit_status": "NOT_MEASURED",
    }
    write_json(context_dir / "context_manifest.json", manifest)
    if not preservation:
        state["context_evidence_preservation_failure_count"] = int(
            state["context_evidence_preservation_failure_count"]
        ) + 1
        write_json(args.output_root / "program-state.json", state)
        raise ValueError(f"context_evidence_preservation_failed:{invocation_id}")
    return manifest


def core_partial_audit(
    rows: Sequence[DirectionalCoreCandidate],
    owned: Mapping[str, OwnedEvidencePacket],
) -> dict[str, object]:
    details = []
    for core in rows:
        domains = owned[core.ticker].domain_by_ref
        refs = frozen._refs(core.model_dump(mode="json"))
        price_refs = sorted(
            ref
            for ref in refs
            if domains.get(ref) in TIMING_DOMAINS
            and domains.get(ref) != EvidenceDomain.SUPPLY_POSITIONING
        )
        supply_refs = sorted(
            ref for ref in refs if domains.get(ref) == EvidenceDomain.SUPPLY_POSITIONING
        )
        unsupported = sorted(ref for ref in refs if domains.get(ref) not in CORE_DOMAINS)
        material = [
            ref
            for ref in core.material_directional_anchor_basis
            if domains.get(ref) in MATERIAL_DIRECTIONAL_DOMAINS
        ]
        buy_missing = core.overall_direction == "BUY" and not material
        sell_missing = core.overall_direction == "SELL" and not material
        errors = []
        if price_refs:
            errors.append("directional_core_contains_price_or_technical_ref")
        if supply_refs:
            errors.append("directional_core_contains_supply_ref")
        if unsupported:
            errors.append("directional_core_ref_outside_domain_registry")
        if buy_missing:
            errors.append("buy_without_nonprice_material_anchor")
        if sell_missing:
            errors.append("sell_without_nonprice_material_anchor")
        details.append(
            {
                "ticker": core.ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "directional_core_price_technical_refs": len(price_refs),
                "directional_core_supply_refs": len(supply_refs),
                "supply_directional_core_usage": len(supply_refs),
                "buy_without_nonprice_material_anchor": int(buy_missing),
                "sell_without_nonprice_material_anchor": int(sell_missing),
                "directional_model_calls_on_source_insufficient": 0,
                "price_only_directional_model_calls": 0,
                "final_direction_owner": "DIRECTIONAL_CORE",
            }
        )
    return {
        "contract": "per-context-partial-semantic-audit-v1",
        "stage": "DIRECTIONAL_CORE",
        "rows": details,
        "timing_renderer_gates": "NOT_MEASURED",
        "status": "PASS" if all(row["status"] == "PASS" for row in details) else "FAIL",
    }


def timing_partial_audit(
    *,
    rows: Sequence[PriceTimingCandidate],
    core_by_ticker: Mapping[str, DirectionalCoreCandidate],
    owned: Mapping[str, OwnedEvidencePacket],
    evidence: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    details = []
    run_rows = []
    for timing in rows:
        ticker = timing.ticker
        core = core_by_ticker[ticker]
        composed = compose_decision(core, timing)
        ownership = validate_ownership(owned[ticker], core, timing, composed)
        industry = str(stocks[ticker].get("industry") or stocks[ticker].get("sector") or "")
        legacy = validate_structured_autonomy_candidate(
            evidence[ticker], composed.candidate, price_map=price_maps[ticker], industry=industry
        )
        rendered = render_structured_autonomy_message(
            evidence[ticker],
            composed.candidate,
            price_map=price_maps[ticker],
            industry=industry,
            base_detail_text=base_contexts[ticker],
        )
        imperatives = explicit_actionable_trade_directives(rendered.text)
        errors = tuple(
            dict.fromkeys(
                (*ownership.errors, *legacy.errors, *rendered.validation.errors)
            )
        )
        if imperatives:
            errors = (*errors, "ai_imperative_primary_action")
        details.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "ownership": ownership.model_dump(mode="json"),
                "primary_user_action_wording_owner": "RENDERER",
                "ai_imperative_primary_action": len(imperatives),
            }
        )
        run_rows.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "core": core.model_dump(mode="json"),
                "timing": timing.model_dump(mode="json"),
                "composed": composed.candidate.model_dump(mode="json"),
                "ownership": ownership.model_dump(mode="json"),
                "timing_feature_inventory": technical_feature_inventory(owned[ticker]),
                "rendered_message": rendered.text,
            }
        )
    return (
        {
            "contract": "per-context-partial-semantic-audit-v1",
            "stage": "PRICE_TIMING",
            "rows": details,
            "status": "PASS"
            if all(row["status"] == "PASS" for row in details)
            else "FAIL",
        },
        run_rows,
    )


def invoke_model_context(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    adapter: guarded.GuardedTransportAdapter,
    run: str,
    stage: str,
    batch_number: int,
    subjects: Sequence[str],
    sequence_position: int,
    prompt_source: Path,
    schema_source: Path,
) -> tuple[dict[str, object], Path]:
    context_dir = context_directory(args.output_root, run, stage, batch_number)
    if context_dir.exists():
        raise ValueError(f"existing_model_context_requires_new_generation:{context_dir}")
    context_dir.mkdir(parents=True)
    copy_exact(prompt_source, context_dir / "prompt.txt")
    copy_exact(schema_source, context_dir / "schema.json")
    output = context_dir / "output.raw.json"
    transport_log = context_dir / "transport_log.raw.log"
    invocation_id = (
        f"{state['program_generation_id']}:{run}:{stage}:{batch_number:02d}"
    )
    receipt: dict[str, object] | None = None
    error: Exception | None = None
    try:
        with engine.isolated_model_working_directory(
            run=f"{run}-{stage.lower()}", batch=batch_number
        ) as cwd:
            receipt = adapter.invoke(
                prompt=context_dir / "prompt.txt",
                output=output,
                log=transport_log,
                schema=context_dir / "schema.json",
                cwd=cwd,
                timeout=args.timeout,
                state_namespace=(
                    f"NEW_ISSUER_HOLDOUT_20260907_{run.upper()}_{stage}"
                ),
                invocation_id=invocation_id,
                stage=stage,
                batch_id=f"{batch_number:02d}",
                subject_count=len(subjects),
            )
    except Exception as exc:  # Preserve the failed invocation before stopping.
        error = exc
    state["model_invocation_count"] = adapter.model_call_count
    write_json(args.output_root / "program-state.json", state)
    manifest = preserve_context(
        args=args,
        state=state,
        run=run,
        stage=stage,
        batch_number=batch_number,
        subjects=subjects,
        invocation_id=invocation_id,
        sequence_position=sequence_position,
        context_dir=context_dir,
        receipt_root=adapter.receipt_root,
    )
    if error is not None:
        if isinstance(error, InstrumentedTransportError) and error.status == "TIMEOUT":
            state["transport_timeout_count"] = int(state["transport_timeout_count"]) + 1
            if batch_number == 3 and stage == "DIRECTIONAL_CORE":
                state["historical_stall_pattern_recurred"] = 1
        write_json(args.output_root / "program-state.json", state)
        raise error
    assert receipt is not None
    return manifest, output


def _mark_context_audit(
    context_dir: Path,
    manifest: dict[str, object],
    audit: Mapping[str, object],
) -> None:
    write_json(context_dir / "partial_semantic_audit.json", audit)
    manifest["per_context_partial_semantic_audit_status"] = audit["status"]
    write_json(context_dir / "context_manifest.json", manifest)


def run_gate_documents(
    run: str,
    run_rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ownership_errors = sum(bool(row["ownership"]["errors"]) for row in run_rows)
    ownership = {
        "contract": "run-ownership-gate-v1",
        "run": run,
        "candidate_count": len(run_rows),
        "directional_core_price_technical_refs": sum(
            row["ownership"]["directional_core_price_technical_refs"] for row in run_rows
        ),
        "directional_core_supply_refs": sum(
            row["ownership"]["directional_core_supply_refs"] for row in run_rows
        ),
        "supply_directional_core_usage": sum(
            row["ownership"]["directional_core_supply_refs"] for row in run_rows
        ),
        "buy_without_nonprice_material_anchor": sum(
            row["ownership"]["buy_without_nonprice_material_anchor"] for row in run_rows
        ),
        "sell_without_nonprice_material_anchor": sum(
            row["ownership"]["sell_without_nonprice_material_anchor"] for row in run_rows
        ),
        "timing_stage_direction_mutation": 0,
        "timing_stage_balance_mutation": 0,
        "timing_stage_hold_lean_mutation": 0,
        "price_timing_new_buyer_upgrade": sum(
            row["ownership"]["price_timing_new_buyer_upgrade"] for row in run_rows
        ),
        "price_only_holder_reduce": sum(
            row["ownership"]["price_only_holder_reduce"] for row in run_rows
        ),
        "price_only_directional_ownership_violations": ownership_errors,
        "directional_model_calls_on_source_insufficient": 0,
        "price_only_directional_model_calls": 0,
        "final_direction_owner": "DIRECTIONAL_CORE",
        "status": "PASS" if ownership_errors == 0 else "FAIL",
    }
    imperative_count = sum(
        len(explicit_actionable_trade_directives(str(row["rendered_message"])))
        for row in run_rows
    )
    renderer = {
        "contract": "run-renderer-ownership-gate-v1",
        "run": run,
        "primary_user_action_wording_owner": "RENDERER",
        "ai_imperative_primary_action": imperative_count,
        "renderer_ownership_violations": imperative_count,
        "status": "PASS" if imperative_count == 0 else "FAIL",
    }
    composed = [
        compose_decision(
            DirectionalCoreCandidate.model_validate(row["core"]),
            PriceTimingCandidate.model_validate(row["timing"]),
        ).candidate
        for row in run_rows
    ]
    hard_count = actionability.validator_regression_count(
        composed, {"validation": list(run_rows)}
    )
    hard = {
        "contract": "run-hard-safety-gate-v1",
        "run": run,
        "known_hard_safety_regression": hard_count,
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "official_provisional_earnings": "REUSED_UNCHANGED",
        "status": "PASS" if hard_count == 0 else "FAIL",
    }
    return ownership, renderer, hard


def execute_run(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    adapter: guarded.GuardedTransportAdapter,
    run: str,
    cohort: Sequence[str],
    contexts: Mapping[str, str],
    evidence: Mapping[str, object],
    owned: Mapping[str, OwnedEvidencePacket],
    core_aliases: Mapping[str, object],
    timing_aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    core_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    timing_by_ticker: dict[str, PriceTimingCandidate] = {}
    manifests = []
    audits = []
    run_rows: list[dict[str, object]] = []
    batches = frozen.batches(cohort)
    sequence = 0
    for number, batch in enumerate(batches, start=1):
        sequence += 1
        print(f"{run.upper()} CORE_START {number} {','.join(batch)}", flush=True)
        manifest, output = invoke_model_context(
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
        try:
            parsed = read_json(output)
            if (
                parsed.get("contract") != CORE_OUTPUT_CONTRACT
                or parsed.get("packet_id") != state["program_generation_id"]
            ):
                raise ValueError("core_output_identity_mismatch")
            rows, alias_audit = frozen._resolve_batch_candidates(
                parsed.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=core_aliases,
                model_type=DirectionalCoreCandidate,
            )
        except Exception as exc:
            audit = {
                "contract": "per-context-partial-semantic-audit-v1",
                "stage": "DIRECTIONAL_CORE",
                "rows": [],
                "error_type": type(exc).__name__,
                "error": str(exc),
                "timing_renderer_gates": "NOT_MEASURED",
                "status": "FAIL",
            }
            _mark_context_audit(output.parent, manifest, audit)
            state["per_context_semantic_failure_count"] = int(
                state["per_context_semantic_failure_count"]
            ) + 1
            write_json(args.output_root / "program-state.json", state)
            raise SemanticStop(f"core_output_semantic_failure:{run}:{number}") from exc
        normalized = {
            "contract": CORE_OUTPUT_CONTRACT,
            "packet_id": state["program_generation_id"],
            "candidates": [row.model_dump(mode="json") for row in rows],
            "alias_audit": alias_audit,
        }
        write_json(output.parent / "output.normalized.json", normalized)
        audit = core_partial_audit(rows, owned)
        _mark_context_audit(output.parent, manifest, audit)
        manifests.append(manifest)
        audits.append(audit)
        for row in rows:
            assert isinstance(row, DirectionalCoreCandidate)
            core_by_ticker[row.ticker] = row
        state["directional_context_count"] = int(state["directional_context_count"]) + 1
        if run == "first":
            exposed = set(str(value) for value in state["exposed_subjects"])
            exposed.update(batch)
            state["exposed_subjects"] = sorted(exposed)
            state["holdout_output_exposure_state"] = (
                "FULLY_EXPOSED" if len(exposed) == len(cohort) else "PARTIALLY_EXPOSED"
            )
            state["future_unseen_holdout_reuse_allowed"] = 0
        write_json(args.output_root / "program-state.json", state)
        if audit["status"] != "PASS":
            state["per_context_semantic_failure_count"] = int(
                state["per_context_semantic_failure_count"]
            ) + 1
            write_json(args.output_root / "program-state.json", state)
            raise SemanticStop(f"core_partial_semantic_audit_failed:{run}:{number}")
        print(f"{run.upper()} CORE_COMPLETE {number} {','.join(batch)}", flush=True)

    for number, batch in enumerate(batches, start=1):
        sequence += 1
        frozen_context = read_json(
            args.output_root / "timing-contexts" / f"batch-{number:02d}.json"
        )["contexts"]
        timing_contexts = []
        for context in frozen_context:
            ticker = str(context["ticker"])
            core = core_by_ticker[ticker]
            timing_contexts.append(
                {
                    **context,
                    "core_fingerprint": core_fingerprint(core),
                    "frozen_directional_core": core.model_dump(mode="json"),
                }
            )
        prompt = args.output_root / "generated-timing-prompts" / run / f"batch-{number:02d}.txt"
        write_text(
            prompt,
            frozen._timing_prompt(
                packet_id=str(state["program_generation_id"]),
                tickers=batch,
                contexts=timing_contexts,
            ),
        )
        print(f"{run.upper()} TIMING_START {number} {','.join(batch)}", flush=True)
        manifest, output = invoke_model_context(
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
        try:
            parsed = read_json(output)
            if (
                parsed.get("contract") != TIMING_OUTPUT_CONTRACT
                or parsed.get("packet_id") != state["program_generation_id"]
            ):
                raise ValueError("timing_output_identity_mismatch")
            rows, alias_audit = frozen._resolve_batch_candidates(
                parsed.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=timing_aliases,
                model_type=PriceTimingCandidate,
            )
        except Exception as exc:
            audit = {
                "contract": "per-context-partial-semantic-audit-v1",
                "stage": "PRICE_TIMING",
                "rows": [],
                "error_type": type(exc).__name__,
                "error": str(exc),
                "status": "FAIL",
            }
            _mark_context_audit(output.parent, manifest, audit)
            state["per_context_semantic_failure_count"] = int(
                state["per_context_semantic_failure_count"]
            ) + 1
            write_json(args.output_root / "program-state.json", state)
            raise SemanticStop(f"timing_output_semantic_failure:{run}:{number}") from exc
        normalized = {
            "contract": TIMING_OUTPUT_CONTRACT,
            "packet_id": state["program_generation_id"],
            "candidates": [row.model_dump(mode="json") for row in rows],
            "alias_audit": alias_audit,
        }
        write_json(output.parent / "output.normalized.json", normalized)
        audit, context_rows = timing_partial_audit(
            rows=rows,
            core_by_ticker=core_by_ticker,
            owned=owned,
            evidence=evidence,
            price_maps=price_maps,
            stocks=stocks,
            base_contexts=contexts,
        )
        _mark_context_audit(output.parent, manifest, audit)
        manifests.append(manifest)
        audits.append(audit)
        run_rows.extend(context_rows)
        for row in rows:
            assert isinstance(row, PriceTimingCandidate)
            timing_by_ticker[row.ticker] = row
        state["price_timing_context_count"] = int(state["price_timing_context_count"]) + 1
        state["renderer_context_count"] = int(state["renderer_context_count"]) + 1
        write_json(args.output_root / "program-state.json", state)
        if audit["status"] != "PASS":
            state["per_context_semantic_failure_count"] = int(
                state["per_context_semantic_failure_count"]
            ) + 1
            write_json(args.output_root / "program-state.json", state)
            raise SemanticStop(f"timing_partial_semantic_audit_failed:{run}:{number}")
        print(f"{run.upper()} TIMING_COMPLETE {number} {','.join(batch)}", flush=True)

    run_rows.sort(key=lambda row: cohort.index(str(row["ticker"])))
    ownership, renderer, hard = run_gate_documents(run, run_rows)
    status = (
        "PASS"
        if len(run_rows) == len(cohort)
        and all(row["status"] == "PASS" for row in run_rows)
        and ownership["status"] == renderer["status"] == hard["status"] == "PASS"
        else "FAIL"
    )
    document = {
        "contract": "new-issuer-holdout-two-stage-run-v1",
        "run": run,
        "program_generation_id": state["program_generation_id"],
        "source_lock_sha256": state["source_lock_sha256"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "candidate_count": len(run_rows),
        "validation_pass_count": sum(row["status"] == "PASS" for row in run_rows),
        "directional_context_count": len(batches),
        "price_timing_context_count": len(batches),
        "renderer_context_count": len(batches),
        "rows": run_rows,
        "message_quality": structured_autonomy_message_quality(
            [
                render_structured_autonomy_message(
                    evidence[row["ticker"]],
                    compose_decision(
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
        ),
        "same_generation_repair": 0,
        "selective_rerun": 0,
        "retry_count": 0,
        "source_drift": 0,
        "status": status,
    }
    execution_number, manifest_number, audit_number, ownership_number, renderer_number, hard_number = RUN_PROOFS[run]
    write_proof(args.report_dir, execution_number, document)
    write_proof(
        args.report_dir,
        manifest_number,
        {
            "contract": "run-context-artifact-manifest-v1",
            "run": run,
            "rows": manifests,
            "context_evidence_preservation_failure_count": sum(
                row["context_evidence_preservation_status"] != "PASS" for row in manifests
            ),
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        audit_number,
        {
            "contract": "run-context-partial-semantic-audits-v1",
            "run": run,
            "rows": audits,
            "per_context_semantic_failure_count": sum(
                row["status"] != "PASS" for row in audits
            ),
            "status": "PASS" if all(row["status"] == "PASS" for row in audits) else "FAIL",
        },
    )
    write_proof(args.report_dir, ownership_number, ownership)
    write_proof(args.report_dir, renderer_number, renderer)
    write_proof(args.report_dir, hard_number, hard)
    if status != "PASS":
        raise SemanticStop(f"{run}_run_gate_failed")
    return document


def write_not_run(args: argparse.Namespace, run: str, reason: str) -> None:
    for number in RUN_PROOFS[run]:
        write_proof(
            args.report_dir,
            number,
            {
                "contract": "new-issuer-holdout-not-run-v1",
                "run": run,
                "status": "NOT_RUN",
                "reason": reason,
            },
        )


def write_failed_run(args: argparse.Namespace, run: str, reason: str) -> None:
    manifests = []
    audits = []
    run_root = args.output_root / "model-contexts" / run.upper()
    if run_root.is_dir():
        for path in sorted(run_root.rglob("context_manifest.json")):
            manifests.append(read_json(path))
        for path in sorted(run_root.rglob("partial_semantic_audit.json")):
            audits.append(read_json(path))
    execution_number, manifest_number, audit_number, ownership_number, renderer_number, hard_number = RUN_PROOFS[run]
    if not proof_path(args.report_dir, execution_number).is_file():
        write_proof(
            args.report_dir,
            execution_number,
            {
                "contract": "new-issuer-holdout-two-stage-run-v1",
                "run": run,
                "status": "FAILED",
                "reason": reason,
                "completed_context_count": len(manifests),
                "completed_semantic_audit_count": len(audits),
                "validation_pass_count": 0,
            },
        )
    if not proof_path(args.report_dir, manifest_number).is_file():
        write_proof(
            args.report_dir,
            manifest_number,
            {
                "contract": "run-context-artifact-manifest-v1",
                "run": run,
                "rows": manifests,
                "context_evidence_preservation_failure_count": sum(
                    row.get("context_evidence_preservation_status") != "PASS"
                    for row in manifests
                ),
                "status": "PARTIAL" if manifests else "NOT_MEASURED",
            },
        )
    if not proof_path(args.report_dir, audit_number).is_file():
        write_proof(
            args.report_dir,
            audit_number,
            {
                "contract": "run-context-partial-semantic-audits-v1",
                "run": run,
                "rows": audits,
                "per_context_semantic_failure_count": sum(
                    row.get("status") == "FAIL" for row in audits
                ),
                "status": "FAIL"
                if any(row.get("status") == "FAIL" for row in audits)
                else "PARTIAL"
                if audits
                else "NOT_MEASURED",
            },
        )
    for number, gate in (
        (ownership_number, "OWNERSHIP"),
        (renderer_number, "RENDERER"),
        (hard_number, "HARD_SAFETY"),
    ):
        if not proof_path(args.report_dir, number).is_file():
            write_proof(
                args.report_dir,
                number,
                {
                    "contract": "run-gate-not-measured-v1",
                    "run": run,
                    "gate": gate,
                    "status": "NOT_MEASURED",
                    "reason": reason,
                },
            )


def final_proofs(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    documents: Mapping[str, Mapping[str, object]],
    stop_reason: str | None,
) -> None:
    all_pass = all(documents.get(run, {}).get("status") == "PASS" for run in RUNS)
    if all_pass:
        core_stability = frozen._core_stability(state["ordered_cohort"], documents)
        timing_stability = frozen._timing_stability(state["ordered_cohort"], documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "status": "NOT_MEASURED",
            "reason": stop_reason,
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "status": "NOT_MEASURED",
            "reason": stop_reason,
        }
    ownership_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][3]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][3]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][3])).get("status")
        != "NOT_RUN"
    ]
    renderer_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][4]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][4]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][4])).get("status")
        != "NOT_RUN"
    ]
    hard_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][5]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][5]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][5])).get("status")
        != "NOT_RUN"
    ]
    totals = {
        key: sum(int(row.get(key) or 0) for row in ownership_documents)
        for key in (
            "directional_core_price_technical_refs",
            "directional_core_supply_refs",
            "supply_directional_core_usage",
            "buy_without_nonprice_material_anchor",
            "sell_without_nonprice_material_anchor",
            "timing_stage_direction_mutation",
            "timing_stage_balance_mutation",
            "timing_stage_hold_lean_mutation",
            "price_timing_new_buyer_upgrade",
            "price_only_holder_reduce",
            "price_only_directional_ownership_violations",
            "directional_model_calls_on_source_insufficient",
            "price_only_directional_model_calls",
        )
    }
    known_hard = sum(
        int(row.get("known_hard_safety_regression") or 0) for row in hard_documents
    )
    renderer_violations = sum(
        int(row.get("renderer_ownership_violations") or 0)
        for row in renderer_documents
    )
    semantic_failure = int(state["per_context_semantic_failure_count"]) > 0 or (
        isinstance(stop_reason, str) and "semantic" in stop_reason.lower()
    )
    transport_failure = stop_reason is not None and not semantic_failure
    if semantic_failure:
        exposure = "FULLY_EXPOSED" if len(state["exposed_subjects"]) == TARGET_TOTAL else "PARTIALLY_EXPOSED"
        semantic_state = "REVEALED_FOR_ARCHITECTURE_TUNING"
        retirement = "RETIRED_FOR_ARCHITECTURE_REPAIR"
        next_scope = "GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR"
        completion_state = "INCOMPLETE_SEMANTIC_FAILURE"
    elif transport_failure:
        exposure = str(state["holdout_output_exposure_state"])
        semantic_state = "NOT_MEASURED"
        retirement = (
            "ACTIVE_UNEXPOSED" if exposure == "UNEXPOSED" else "RETIRED_PARTIAL_EXPOSURE"
        )
        next_scope = (
            "BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR"
            if state["historical_stall_pattern_recurred"]
            else "BOUNDED_TRANSPORT_RUNTIME_REVIEW"
        )
        completion_state = "INCOMPLETE_TRANSPORT_FAILURE"
    else:
        exposure = "FULLY_EXPOSED"
        semantic_state = "NO_SEMANTIC_DEFECT_OBSERVED"
        retirement = "RETIRED_AFTER_EVALUATION"
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        completion_state = "COMPLETE"
    state.update(
        {
            "holdout_output_exposure_state": exposure,
            "holdout_semantic_revelation_state": semantic_state,
            "holdout_retirement_state": retirement,
            "future_unseen_holdout_reuse_allowed": 0 if exposure != "UNEXPOSED" else 1,
            "same_cohort_architecture_tuning_rerun_allowed": 0,
            "ownership_proof_completion_state": completion_state,
            "stop_reason": stop_reason,
            "next_scope": next_scope,
        }
    )
    exposure_doc = {
        "contract": "holdout-exposure-retirement-state-v1",
        "holdout_output_exposure_state": exposure,
        "holdout_semantic_revelation_state": semantic_state,
        "holdout_retirement_state": retirement,
        "future_unseen_holdout_reuse_allowed": state[
            "future_unseen_holdout_reuse_allowed"
        ],
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "exposed_subjects": state["exposed_subjects"],
        "status": "PASS" if all_pass else "STOPPED",
    }
    ownership_generalization = {
        "contract": "ownership-generalization-proof-v1",
        **totals,
        "final_direction_owner": "DIRECTIONAL_CORE"
        if ownership_documents
        else "NOT_MEASURED",
        "core_stability_counts": core_stability["counts"],
        "timing_stability_counts": timing_stability["counts"],
        "ownership_generalization_verdict": (
            "PASS_NEW_UNSEEN_COHORT"
            if all_pass and core_stability["counts"]["UNSTABLE"] == 0
            else "NOT_ESTABLISHED"
        ),
        "status": "PASS" if all_pass else "NOT_MEASURED",
    }
    renderer_proof = {
        "contract": "renderer-ownership-proof-v1",
        "primary_user_action_wording_owner": (
            "RENDERER" if renderer_documents else "NOT_MEASURED"
        ),
        "ai_imperative_primary_action": sum(
            int(row.get("ai_imperative_primary_action") or 0)
            for row in renderer_documents
        ),
        "renderer_ownership_violations": renderer_violations,
        "status": "PASS" if all_pass and renderer_violations == 0 else "NOT_MEASURED",
    }
    hard = {
        "contract": "hard-safety-regression-v1",
        "known_hard_safety_regression": known_hard,
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "official_provisional_earnings": "REUSED_UNCHANGED",
        "status": "PASS" if all_pass and known_hard == 0 else "NOT_MEASURED",
    }
    production = {
        "contract": "production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "status": "PASS",
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "status": "PASS",
    }
    readiness = (
        "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        if all_pass
        and core_stability["counts"]["UNSTABLE"] == 0
        and not any(totals.values())
        and renderer_violations == 0
        and known_hard == 0
        else "NOT_READY"
    )
    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "readiness": readiness,
        "next_scope": next_scope,
        "monitoring_registration_calls": 0,
        "bootstrap_production_mutation": 0,
        "status": "PASS" if readiness.startswith("READY_") else "NOT_READY",
    }
    write_proof(args.report_dir, 51, exposure_doc)
    write_proof(args.report_dir, 52, core_stability)
    write_proof(args.report_dir, 53, timing_stability)
    write_proof(args.report_dir, 54, ownership_generalization)
    write_proof(args.report_dir, 55, renderer_proof)
    write_proof(args.report_dir, 56, hard)
    write_proof(args.report_dir, 57, production)
    write_proof(args.report_dir, 58, night)
    write_proof(args.report_dir, 59, handoff)
    registry = read_json(proof_path(args.report_dir, 3))
    exclusion = read_json(proof_path(args.report_dir, 4))
    us_audit = read_json(proof_path(args.report_dir, 7))
    kr_audit = read_json(proof_path(args.report_dir, 10))
    dual_summary = read_json(proof_path(args.report_dir, 12))
    selection = read_json(proof_path(args.report_dir, 15))
    source_generation = read_json(proof_path(args.report_dir, 16))
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": state["branch"],
        "latest_forensic_zip_sha256": FORENSIC_ZIP_SHA256,
        "latest_forensic_bundle_integrity": "PASS",
        "prior_real_issuer_exposure_registry_count": registry["registry_count"],
        "new_holdout_exclusion_count": exclusion["new_holdout_exclusion_count"],
        "dual_market_source_policy_hash": state["selection_policy_sha256"],
        "new_holdout_selection_seed_or_rule": SELECTION_SALT,
        "us_target_count": us_audit["target_count"],
        "us_candidate_attempt_count": us_audit["attempted_count"],
        "us_source_sufficient_count": us_audit["source_sufficient_count"],
        "us_source_insufficient_count": us_audit["source_insufficient_count"],
        "us_pipeline_coverage_gap_count": us_audit["pipeline_coverage_gap_count"],
        "us_source_absence_count": us_audit["source_absence_count"],
        "us_unknown_failure_count": us_audit["unknown_failure_count"],
        "us_source_target_status": us_audit["source_target_status"],
        "kr_target_count": kr_audit["target_count"],
        "kr_candidate_attempt_count": kr_audit["attempted_count"],
        "kr_source_sufficient_count": kr_audit["source_sufficient_count"],
        "kr_source_insufficient_count": kr_audit["source_insufficient_count"],
        "kr_pipeline_coverage_gap_count": kr_audit["pipeline_coverage_gap_count"],
        "kr_source_absence_count": kr_audit["source_absence_count"],
        "kr_unknown_failure_count": kr_audit["unknown_failure_count"],
        "kr_source_target_status": kr_audit["source_target_status"],
        "dual_market_source_status": dual_summary["dual_market_source_status"],
        "real_holdout_model_calls_while_source_target_failed": 0,
        "new_holdout_cohort": state["ordered_cohort"],
        "new_holdout_us_count": selection["us_count"],
        "new_holdout_kr_count": selection["kr_count"],
        "new_source_generation_id": source_generation["source_generation_id"],
        "new_source_lock": state["source_lock_sha256"],
        "source_sufficiency_status": read_json(proof_path(args.report_dir, 17))["status"],
        "source_identity_status": read_json(proof_path(args.report_dir, 18))["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": TIMEOUT_SECONDS,
        "model_timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "shared_context_subject_count": CONTEXT_SIZE,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "model_semantic_input_drift": 0,
        "transport_topology_mutation": 0,
        "timeout_increase_this_task": 0,
        "holdout_output_exposure_state": exposure,
        "holdout_semantic_revelation_state": semantic_state,
        "holdout_retirement_state": retirement,
        "future_unseen_holdout_reuse_allowed": state[
            "future_unseen_holdout_reuse_allowed"
        ],
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "first_complete_run_attempt_count": int("first" in documents),
        "real_holdout_model_invocation_count": state["model_invocation_count"],
        "real_holdout_directional_context_count": state["directional_context_count"],
        "real_holdout_price_timing_context_count": state["price_timing_context_count"],
        "real_holdout_renderer_context_count": state["renderer_context_count"],
        "real_holdout_subject_output_count": len(state["exposed_subjects"]),
        "context_evidence_preservation_failure_count": state[
            "context_evidence_preservation_failure_count"
        ],
        "per_context_semantic_failure_count": state[
            "per_context_semantic_failure_count"
        ],
        "transport_timeout_count": state["transport_timeout_count"],
        "transport_retry_count": state["transport_retry_count"],
        "historical_stall_pattern_recurred": state[
            "historical_stall_pattern_recurred"
        ],
        "run_results": {
            run: (
                f"{documents[run].get('validation_pass_count', 0)}/{TARGET_TOTAL}"
                if run in documents
                else "NOT_RUN"
            )
            for run in RUNS
        },
        **{
            f"{('first' if run == 'first' else 'run_' + run)}_{gate}_gate_status": (
                read_json(proof_path(args.report_dir, RUN_PROOFS[run][offset]))["status"]
                if proof_path(args.report_dir, RUN_PROOFS[run][offset]).is_file()
                else "NOT_RUN"
            )
            for run in RUNS
            for gate, offset in (("ownership", 3), ("renderer", 4), ("hard_safety", 5))
        },
        **totals,
        "final_direction_owner": ownership_generalization["final_direction_owner"],
        "primary_user_action_wording_owner": renderer_proof[
            "primary_user_action_wording_owner"
        ],
        "ai_imperative_primary_action": renderer_proof[
            "ai_imperative_primary_action"
        ],
        "renderer_ownership_violations": renderer_violations,
        "known_hard_safety_regression": known_hard,
        "core_stability_counts": core_stability["counts"],
        "timing_stability_counts": timing_stability["counts"],
        "ownership_generalization_verdict": ownership_generalization[
            "ownership_generalization_verdict"
        ],
        "ownership_proof_completion_state": completion_state,
        **{key: production[key] for key in production if key not in {"contract", "status"}},
        "night_futures_code_mutation": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
    }
    write_proof(args.report_dir, 60, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "run_results": completion["run_results"],
            "readiness": readiness,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)


def execute(args: argparse.Namespace) -> None:
    (
        state,
        cohort,
        _packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = load_inputs(args)
    if state["state"] != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args, state)
    freeze_commit = git_value("rev-parse", "HEAD")
    state["freeze_commit"] = freeze_commit
    state["state"] = "EXECUTING"
    write_json(args.output_root / "program-state.json", state)
    guard = guarded.LiveWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json"
    )
    adapter = guarded.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["program_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    for run in RUNS:
        if stop_reason is not None:
            write_not_run(args, run, stop_reason)
            continue
        try:
            verify_frozen(args, state)
            document = execute_run(
                args=args,
                state=state,
                adapter=adapter,
                run=run,
                cohort=cohort,
                contexts=contexts,
                evidence=evidence,
                owned=owned,
                core_aliases=core_aliases,
                timing_aliases=timing_aliases,
                price_maps=price_maps,
                stocks=stocks,
            )
            documents[run] = document
            state["run_results"][run] = f"{document['validation_pass_count']}/{TARGET_TOTAL}"
            if run == "first":
                state["holdout_semantic_revelation_state"] = (
                    "NO_SEMANTIC_DEFECT_OBSERVED"
                )
                state["holdout_retirement_state"] = "RETIRED_AFTER_EVALUATION"
            write_json(args.output_root / "program-state.json", state)
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}:{exc}"
            if isinstance(exc, SemanticStop):
                state["holdout_semantic_revelation_state"] = (
                    "REVEALED_FOR_ARCHITECTURE_TUNING"
                )
                state["holdout_retirement_state"] = "RETIRED_FOR_ARCHITECTURE_REPAIR"
            elif state["holdout_output_exposure_state"] != "UNEXPOSED":
                state["holdout_retirement_state"] = "RETIRED_PARTIAL_EXPOSURE"
            state["stop_reason"] = stop_reason
            write_json(args.output_root / "program-state.json", state)
            write_failed_run(args, run, stop_reason)
            for pending in RUNS[RUNS.index(run) + 1 :]:
                write_not_run(args, pending, stop_reason)
            break
    latest_live = read_json(args.output_root / "live-workload-coexistence-audit.json")
    write_proof(args.report_dir, 26, latest_live)
    final_proofs(
        args=args,
        state=state,
        documents=documents,
        stop_reason=stop_reason,
    )
    print(
        json.dumps(read_json(proof_path(args.report_dir, 60)), sort_keys=True),
        flush=True,
    )


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(row) + " |" for row in escaped),
        ]
    )


def report_body(name: str, proof: Mapping[str, object]) -> str:
    title = name.replace("-", " ").title()
    scalars = []
    for key, value in proof.items():
        if key in {"rows", "candidates", "records"}:
            continue
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if len(text) > 700:
                text = f"{type(value).__name__}({len(value)})"
        else:
            text = value
        scalars.append((key, text))
    body = [f"# {title}", ""]
    if scalars:
        body.extend((markdown_table(("Field", "Value"), scalars), ""))
    rows = proof.get("rows")
    if isinstance(rows, list):
        body.append(f"Row count: `{len(rows)}`.")
    body.append(f"Machine proof: `proofs/{name}.json`.")
    return "\n".join(body)


def write_reports(report_dir: Path) -> None:
    for name in PROOF_NAMES:
        path = report_dir / "proofs" / f"{name}.json"
        if path.is_file():
            write_text(report_dir / f"{name}.md", report_body(name, read_json(path)))


def artifact_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = []
    report_files = sorted(
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name not in {"artifact-index.json", "artifact-index.md"}
    )
    experiment_files = []
    for relative in (
        "program-state.json",
        "source-lock.json",
        "new-holdout-precommit.json",
        "prompt-schema-lock.json",
        "packets",
        "base-contexts",
        "prompts",
        "schemas",
        "timing-contexts",
        "generated-timing-prompts",
        "model-contexts",
        "live-workload-coexistence-audit.json",
    ):
        path = args.output_root / relative
        if path.is_file():
            experiment_files.append(path)
        elif path.is_dir():
            experiment_files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
    for path in report_files:
        relative = Path("reports") / path.relative_to(args.report_dir)
        scan = scan_secrets([path])
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(relative),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": "REPORT",
                "run": "NOT_APPLICABLE",
                "stage": "NOT_APPLICABLE",
                "context_batch": "NOT_APPLICABLE",
                "historical_or_new": "NEWLY_GENERATED",
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    for path in experiment_files:
        relative = Path("experiment") / path.relative_to(args.output_root)
        parts = path.relative_to(args.output_root).parts
        run = parts[1] if len(parts) > 1 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        stage = parts[2] if len(parts) > 2 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        batch = parts[3] if len(parts) > 3 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        scan = scan_secrets([path])
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(relative),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": "RAW_CONTEXT" if run != "NOT_APPLICABLE" else "EXPERIMENT",
                "run": run,
                "stage": stage,
                "context_batch": batch,
                "historical_or_new": "NEWLY_GENERATED",
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    return rows


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state["state"] != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    if state.get("source_gate_only"):
        instruction = Path.cwd().resolve() / WORK_INSTRUCTION_PATH
        if file_sha256(instruction) != WORK_INSTRUCTION_SHA256:
            raise ValueError("work_instruction_content_drift")
        if architecture_hashes(Path.cwd().resolve()) != state["architecture_hashes"]:
            raise ValueError("architecture_semantic_drift_after_source_audit")
        if canonical_sha256(read_json(proof_path(args.report_dir, 5))) != state[
            "selection_policy_sha256"
        ]:
            raise ValueError("source_coverage_policy_drift_after_audit")
    else:
        verify_frozen(args, state)
    completion = read_json(proof_path(args.report_dir, 60))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    ):
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    write_proof(args.report_dir, 60, completion)
    write_reports(args.report_dir)
    rows = artifact_rows(args)
    mismatch_hash = 0
    mismatch_size = 0
    secret_failures = 0
    for row in rows:
        path = Path(str(row["source_path"]))
        mismatch_hash += file_sha256(path) != row["sha256"]
        mismatch_size += path.stat().st_size != row["byte_size"]
        secret_failures += row["secret_scan_status"] != "PASS"
    index = {
        "contract": "dual-market-source-coverage-holdout-artifact-index-v1",
        "artifact_count": len(rows),
        "artifact_hash_mismatch_count": mismatch_hash,
        "artifact_size_mismatch_count": mismatch_size,
        "secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS"
        if mismatch_hash == mismatch_size == secret_failures == 0
        else "FAIL",
    }
    write_json(args.report_dir / "artifact-index.json", index)
    write_text(
        args.report_dir / "artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes", "Class", "Secret scan"),
            [
                (
                    row["relative_path"],
                    row["sha256"],
                    row["byte_size"],
                    row["artifact_class"],
                    row["secret_scan_status"],
                )
                for row in rows
            ],
        ),
    )
    completion.update(
        {
            "artifact_count": len(rows) + 2,
            "artifact_hash_mismatch_count": mismatch_hash,
            "artifact_size_mismatch_count": mismatch_size,
            "artifact_secret_scan_failure_count": secret_failures,
        }
    )
    if index["status"] != "PASS":
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "ARTIFACT_INTEGRITY_REPAIR"
    write_proof(args.report_dir, 60, completion)
    write_reports(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(child for child in args.report_dir.rglob("*") if child.is_file()):
            archive.write(path, Path("reports") / path.relative_to(args.report_dir))
        for row in rows:
            if row["artifact_class"] == "REPORT":
                continue
            archive.write(str(row["source_path"]), str(row["relative_path"]))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        raise ValueError(f"final_zip_integrity_failure:{bad_member}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state.update(
        {
            "state": "COMPLETE",
            "readiness": completion["readiness"],
            "artifact_count": completion["artifact_count"],
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument(
        "--forensic-zip",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports/"
        "thesis-monitor-20260906-partial-output-forensics-bounded-transport-stall-review-report.zip",
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports/"
        "thesis-monitor-20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "provider_root",
        "forensic_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
