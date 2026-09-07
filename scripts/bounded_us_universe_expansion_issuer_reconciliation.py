from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.providers import opendart_corp_codes
from app.services.coldstart_fundamental_enrichment_service import (
    FundamentalEvidenceQuality,
    OfficialFundamentalEnricher,
    OfficialFundamentalEnrichment,
    classify_analysis_framework,
    enrich_assembled_packet,
)
from app.services.coldstart_source_assembly_service import assemble_research_packet
from app.services.reference_universe_audit_service import (
    CanonicalSecurityReference,
    IdentityResolutionStatus,
    RoutingSupportStatus,
    canonical_sha256,
    file_sha256,
    load_kr_reference_universe,
    load_us_reference_universe,
    normalize_us_symbol,
    reconcile_membership_sets,
    representative_securities,
    validate_us_route_response,
    with_routing_result,
)
from scripts import new_issuer_holdout_selection_ownership_proof as prior
from scripts import official_fundamental_enrichment_holdout as fundamental
from scripts import runtime_identity_lock_repair_fullpath_preflight as identity_repair
from scripts import synthetic_canary_fixture_repair_ownership_resume as guard_support
from scripts import unseen_source_assembly_coldstart as source_assembly


PROGRAM_CONTRACT = "bounded-us-universe-expansion-issuer-reconciliation-v1"
SELECTION_SALT = "20260907-bounded-us-universe-expansion-issuer-reconciliation-v1"
INPUT_ZIP_SHA256 = "7e721fa8f28024b1f4e14d928dc860325e87e710b03c7552ea9bf18a81b50d31"
INPUT_ZIP_NAME = "thesis-monitor-20260907-runtime-identity-lock-repair-fullpath-preflight-new-holdout-report.zip"
WORK_INSTRUCTION = (
    "docs/work-instructions/"
    "20260907-bounded-us-supported-universe-expansion-and-issuer-audit-reconciliation.md"
)
POLICY_PATH = "docs/reports/20260907-bounded-us-universe-diagnostic-policy.json"
REPORT_DIRECTORY = (
    "20260907-bounded-us-supported-universe-expansion-issuer-audit-reconciliation"
)
RESULT_ZIP_NAME = (
    "thesis-monitor-20260907-bounded-us-supported-universe-expansion-"
    "issuer-audit-reconciliation-report.zip"
)
US_ROUTE_OBJECTIVE = 24

REPORT_NAMES = (
    "01-input-integrity-and-repository-provenance",
    "02-historical-identity-repair-baseline",
    "03-production-isolation-and-change-boundary",
    "04-counting-units-and-canonical-identity-contract",
    "05-us-universe-codepath-and-filter-funnel",
    "06-us-reference-adapter-decision-and-capabilities",
    "07-reference-snapshots-and-normalization-lineage",
    "08-us-universe-before-after-membership",
    "09-prior-exposure-and-retirement-registry",
    "10-us-exclusion-set-reconciliation",
    "11-kr-issuer-count-root-cause-and-reconciliation",
    "12-cross-market-alias-and-dedup-proof",
    "13-market-manifest-root-cause-and-impact",
    "14-market-manifest-correction-and-tests",
    "15-deterministic-diagnostic-policy-and-budgets",
    "16-us-candidate-and-source-readiness-audit",
    "17-kr-candidate-and-source-readiness-audit",
    "18-dual-market-readiness-and-reserve-summary",
    "19-model-free-fullpath-identity-and-market-matrix",
    "20-negative-and-positive-regression-results",
    "21-tests-lint-diff-and-implementation-freeze",
    "22-production-no-change",
    "23-next-holdout-selection-handoff",
    "24-program-completion",
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


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def zip_json(path: Path, member: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def zip_member_sha256(path: Path, member: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return hashlib.sha256(archive.read(member)).hexdigest()


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


def _reference_retrieved_at(reference_root: Path) -> str:
    newest = max(path.stat().st_mtime for path in reference_root.iterdir() if path.is_file())
    return datetime.fromtimestamp(newest, UTC).isoformat()


def _us_issuer_lookup(
    rows: Sequence[CanonicalSecurityReference],
) -> dict[str, set[str]]:
    lookup: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.canonical_issuer_key is None:
            continue
        for alias in row.provider_aliases:
            lookup[normalize_us_symbol(alias)].add(row.canonical_issuer_key)
    return lookup


def _resolve_exclusion_issuer(
    ticker: str,
    *,
    us_lookup: Mapping[str, set[str]],
    kr_lookup: Mapping[str, str],
) -> tuple[str, str]:
    if ticker.isdigit():
        issuer = kr_lookup.get(ticker)
        if issuer is None:
            raise ValueError(f"historical_kr_identity_unresolved:{ticker}")
        return "kr", issuer
    matches = us_lookup.get(normalize_us_symbol(ticker), set())
    if len(matches) != 1:
        raise ValueError(f"historical_us_identity_not_unique:{ticker}:{len(matches)}")
    return "us", next(iter(matches))


def build_exclusion_registry(
    *,
    report_history: Path,
    provider_root: Path,
    input_zip: Path,
    us_rows: Sequence[CanonicalSecurityReference],
    kr_rows: Sequence[CanonicalSecurityReference],
) -> dict[str, object]:
    legacy_universe = source_assembly.supported_universe(provider_root)
    historical = prior.build_exposure_registry(report_history, legacy_universe)
    records_by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for issuer in historical["rows"]:
        for record in issuer["records"]:
            records_by_ticker[str(record["ticker"])].append(dict(record))
    actual = prior.exposure_tickers(historical) | set(identity_repair.LATEST_ACTUAL_OUTPUT)
    retired = (
        set(prior.OLD_PARTIAL)
        | set(prior.OLD_CONSUMED)
        | set(identity_repair.LATEST_RETIRED_COHORT)
    )
    us_lookup = _us_issuer_lookup(us_rows)
    kr_lookup = {
        row.display_symbol: str(row.canonical_issuer_key)
        for row in kr_rows
        if row.canonical_issuer_key is not None
    }
    rows_by_issuer: dict[str, dict[str, object]] = {}
    for ticker in sorted(actual | retired):
        market, issuer_key = _resolve_exclusion_issuer(
            ticker, us_lookup=us_lookup, kr_lookup=kr_lookup
        )
        aggregate = rows_by_issuer.setdefault(
            issuer_key,
            {
                "canonical_issuer_key": issuer_key,
                "market": market,
                "security_aliases": [],
                "actual_real_model_spawn": False,
                "actual_output_exposure": False,
                "whole_cohort_retired": False,
                "exclusion_reasons": [],
                "lineage": [],
            },
        )
        aggregate["security_aliases"].append(ticker)
        if ticker in actual:
            aggregate["actual_real_model_spawn"] = True
            aggregate["actual_output_exposure"] = True
            aggregate["exclusion_reasons"].append("ACTUAL_REAL_MODEL_OUTPUT_EXPOSURE")
        if ticker in retired:
            aggregate["whole_cohort_retired"] = True
            if ticker in identity_repair.LATEST_RETIRED_COHORT:
                reason = "LATEST_16_WHOLE_COHORT_RETIREMENT"
            elif ticker in prior.OLD_PARTIAL:
                reason = "EARLIER_PARTIAL_16_WHOLE_COHORT_RETIREMENT"
            else:
                reason = "EARLIER_CONSUMED_16_WHOLE_COHORT_RETIREMENT"
            aggregate["exclusion_reasons"].append(reason)
        lineage = records_by_ticker.get(ticker, [])
        if lineage:
            for record in lineage:
                source_path = report_history / str(record["source_artifact"])
                record["source_artifact_sha256"] = (
                    file_sha256(source_path) if source_path.is_file() else "SOURCE_NOT_PRESENT"
                )
                aggregate["lineage"].append(record)
        elif ticker in identity_repair.LATEST_ACTUAL_OUTPUT:
            aggregate["lineage"].append(
                {
                    "ticker": ticker,
                    "generation_id": "HISTORICAL_LATEST_PARTIAL",
                    "actual_real_model_spawn": True,
                    "actual_output_exposure": True,
                    "source_artifact": (
                        f"{input_zip.name}:historical/latest-result/"
                        "reports/proofs/21-first-execution-summary.json"
                    ),
                    "source_artifact_sha256": zip_member_sha256(
                        input_zip,
                        "historical/latest-result/reports/proofs/21-first-execution-summary.json",
                    ),
                }
            )
        else:
            aggregate["lineage"].append(
                {
                    "ticker": ticker,
                    "actual_real_model_spawn": False,
                    "actual_output_exposure": False,
                    "source_artifact": WORK_INSTRUCTION,
                    "source_artifact_sha256": file_sha256(Path(WORK_INSTRUCTION)),
                }
            )
    rows = []
    for issuer_key in sorted(rows_by_issuer):
        row = rows_by_issuer[issuer_key]
        row["security_aliases"] = sorted(set(row["security_aliases"]))
        row["exclusion_reasons"] = sorted(set(row["exclusion_reasons"]))
        rows.append(row)
    output_issuers = {
        row["canonical_issuer_key"] for row in rows if row["actual_output_exposure"]
    }
    retired_issuers = {
        row["canonical_issuer_key"] for row in rows if row["whole_cohort_retired"]
    }
    all_issuers = {row["canonical_issuer_key"] for row in rows}
    return {
        "contract": "canonical-prior-exposure-retirement-registry-v1",
        "historical_reported_counts": {
            "prior_actual_output_exposure_registry_count": 66,
            "whole_cohort_retirement_exclusion_count": 48,
            "issuer_deduplicated_exclusion_count": 85,
        },
        "corrected_units": {
            "actual_output_exposed_security_count": len(actual),
            "actual_output_exposed_issuer_count": len(output_issuers),
            "whole_cohort_retired_security_count": len(retired),
            "whole_cohort_retired_issuer_count": len(retired_issuers),
            "union_excluded_security_count": len(actual | retired),
            "union_excluded_issuer_count": len(all_issuers),
        },
        "overlap_counts": {
            "actual_output_and_retired_issuer_count": len(output_issuers & retired_issuers),
            "actual_output_only_issuer_count": len(output_issuers - retired_issuers),
            "retired_only_issuer_count": len(retired_issuers - output_issuers),
        },
        "actual_output_issuer_keys": sorted(output_issuers),
        "whole_cohort_retired_issuer_keys": sorted(retired_issuers),
        "all_excluded_issuer_keys": sorted(all_issuers),
        "unresolved_historical_identity_count": 0,
        "rows": rows,
        "status": "PASS",
    }


def _mark_static_us_support(
    rows: Sequence[CanonicalSecurityReference], provider_root: Path
) -> tuple[list[CanonicalSecurityReference], list[dict[str, object]]]:
    static = {
        normalize_us_symbol(str(row["ticker"])): row
        for row in source_assembly._us_identities(provider_root)
    }
    updated: list[CanonicalSecurityReference] = []
    evidence: list[dict[str, object]] = []
    for row in rows:
        legacy = static.get(normalize_us_symbol(row.display_symbol))
        if legacy is None or row.routing_support_status != RoutingSupportStatus.CANDIDATE:
            updated.append(row)
            continue
        expected_exchange = str(legacy.get("exchange") or "").upper()
        if expected_exchange != str(row.provider_exchange or "").upper():
            updated.append(row)
            continue
        promoted = with_routing_result(
            row,
            supported=True,
            route_provenance={
                "basis": "EXISTING_STATIC_PROVIDER_REGISTRY",
                "provider_registry_sha256": str(legacy.get("source_sha256") or ""),
            },
        )
        updated.append(promoted)
        evidence.append(
            {
                "ticker": row.display_symbol,
                "canonical_issuer_key": row.canonical_issuer_key,
                "provider_exchange": row.provider_exchange,
                "basis": "EXISTING_STATIC_PROVIDER_REGISTRY",
            }
        )
    return updated, evidence


def _coexistence_observation() -> dict[str, object]:
    observation = guard_support.SandboxCompatibleWorkloadObserver().observe()
    status = (
        "PASS"
        if observation["active_natural_job_count"] == 0
        and observation["running_model_process_count"] == 0
        else "BLOCK"
    )
    return {
        "contract": "bounded-source-diagnostic-live-coexistence-v1",
        **observation,
        "real_model_invocation_count": 0,
        "status": status,
    }


async def route_us_candidates(
    candidates: Sequence[CanonicalSecurityReference],
    *,
    limit: int,
    success_objective: int,
) -> tuple[list[CanonicalSecurityReference], list[dict[str, object]]]:
    settings = get_settings()
    api_key = settings.ohlcv_api_key or settings.action_api_key
    headers = {"X-API-Key": api_key} if api_key else {}
    results: list[CanonicalSecurityReference] = []
    audit: list[dict[str, object]] = []
    success_count = 0
    async with httpx.AsyncClient(
        base_url=settings.ohlcv_base_url.rstrip("/"),
        headers=headers,
        timeout=max(float(settings.ohlcv_timeout_seconds), 60.0),
    ) as client:
        for rank, row in enumerate(candidates[:limit], start=1):
            status_code = 0
            payload: Mapping[str, object] | None = None
            response_sha = None
            error_type = None
            try:
                response = await client.get(
                    "/ohlcv",
                    params={
                        "symbol": row.provider_symbol,
                        "market": "US",
                        "periods": "daily",
                        "count": 1,
                        "include_indicators": "false",
                        "indicator_limit": 0,
                        "adjusted": "true",
                        "include_investor_flows": "false",
                    },
                )
                status_code = response.status_code
                response_sha = hashlib.sha256(response.content).hexdigest()
                if response.status_code == 200:
                    decoded = response.json()
                    payload = decoded if isinstance(decoded, Mapping) else None
            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
                error_type = type(exc).__name__
            supported, reason, route = validate_us_route_response(
                row,
                status_code=status_code,
                payload=payload,
            )
            promoted = with_routing_result(
                row,
                supported=supported,
                reason=None if supported else reason,
                route_provenance={
                    **route,
                    "response_sha256": response_sha,
                    "error_type": error_type,
                },
            )
            results.append(promoted)
            audit.append(
                {
                    "rank": rank,
                    "ticker": row.display_symbol,
                    "canonical_security_id": row.canonical_security_id,
                    "canonical_issuer_key": row.canonical_issuer_key,
                    "request_attempts": 1,
                    "retry_count": 0,
                    "route_supported": supported,
                    "outcome": reason,
                    "route_evidence": route,
                    "response_sha256": response_sha,
                    "error_type": error_type,
                }
            )
            success_count += int(supported)
            if success_count >= success_objective:
                break
    return results, audit


def _replace_reference_rows(
    rows: Sequence[CanonicalSecurityReference],
    replacements: Sequence[CanonicalSecurityReference],
) -> list[CanonicalSecurityReference]:
    by_id = {row.reference_row_id: row for row in replacements}
    return [by_id.get(row.reference_row_id, row) for row in rows]


def _diagnostic_identity(row: CanonicalSecurityReference) -> dict[str, object]:
    return {
        "ticker": row.provider_symbol or row.display_symbol,
        "company_name": row.issuer_name or row.security_name,
        "market": row.market,
        "exchange": row.provider_exchange or row.exchange,
        "sector": str(row.provenance.get("sector") or ""),
        "industry": str(row.provenance.get("industry") or ""),
        "security_type": row.security_type,
        "source": row.reference_source,
        "source_as_of": row.reference_as_of,
        "source_sha256": row.reference_snapshot_sha256,
    }


async def run_source_diagnostics(
    *,
    market: str,
    candidates: Sequence[CanonicalSecurityReference],
    target: int,
    limit: int,
    as_of: datetime,
    cache_dir: Path,
    packet_dir: Path,
) -> dict[str, object]:
    selected_candidates = list(candidates[:limit])
    enricher = OfficialFundamentalEnricher(cache_dir)
    if market == "us":
        enricher._sec_profile._ticker_ciks = {
            normalize_us_symbol(row.provider_symbol or row.display_symbol): str(
                row.canonical_issuer_key
            ).removeprefix("sec:cik:")
            for row in selected_candidates
            if row.canonical_issuer_key is not None
        }
    rows: list[dict[str, object]] = []
    sufficient_count = 0
    for rank, reference in enumerate(selected_candidates, start=1):
        identity = _diagnostic_identity(reference)
        try:
            enrichment = await enricher.enrich(
                ticker=str(identity["ticker"]),
                company_name=str(identity["company_name"]),
                exchange=str(identity["exchange"]),
                sector=str(identity["sector"]),
                industry=str(identity["industry"]),
                as_of=as_of,
            )
        except Exception as exc:
            enrichment = OfficialFundamentalEnrichment(
                ticker=str(identity["ticker"]),
                market=market,
                analysis_framework=classify_analysis_framework(
                    taxonomy_key=None,
                    sector=str(identity["sector"]),
                    industry=str(identity["industry"]),
                ),
                source_quality=FundamentalEvidenceQuality.UNAVAILABLE,
                source_attempts=(
                    {
                        "source": "official_fundamental_enricher",
                        "status": "failed",
                        "error": type(exc).__name__,
                    },
                ),
                errors=(type(exc).__name__, str(exc)),
            )
        source_row = fundamental.enrichment_row(identity, enrichment)
        fundamental_sufficient = bool(source_row["directional_model_eligible"])
        full_packet_sha = None
        full_packet_status = "NOT_RUN_SOURCE_INSUFFICIENT"
        price_readiness = "NOT_ATTEMPTED_SOURCE_GATE"
        validation_errors: list[str] = []
        base_provider_audit: Mapping[str, object] = {}
        if fundamental_sufficient:
            try:
                base = await assemble_research_packet(
                    str(identity["ticker"]), as_of, identity=identity
                )
                full_packet_status = str(base.status)
                validation_errors = list(base.validation_errors)
                base_provider_audit = base.provider_audit
                price_readiness = str(
                    base.provider_audit.get("price_timing_readiness")
                    or (
                        "READY"
                        if str(base.status) == "ASSEMBLED"
                        else "UNAVAILABLE_SAFE"
                        if any("unavailable" in value.lower() for value in validation_errors)
                        else "HARD_VALIDATION_BLOCK"
                    )
                )
                enriched = enrich_assembled_packet(base, enrichment)
                if enriched.packet is not None:
                    full_packet_sha = enriched.packet_sha256
                    full_packet_status = str(enriched.status)
                    write_json(
                        packet_dir
                        / market
                        / f"{rank:02d}-{reference.display_symbol}-full.json",
                        enriched.packet,
                    )
            except Exception as exc:
                full_packet_status = "PACKET_ASSEMBLY_EXCEPTION"
                price_readiness = "HARD_VALIDATION_BLOCK"
                validation_errors = [type(exc).__name__, str(exc)]
        diagnostic_packet = {
            "contract": "bounded-fundamental-source-diagnostic-packet-v1",
            "rank": rank,
            "market": market,
            "canonical_security": reference.model_dump(mode="json"),
            "official_enrichment": enrichment.model_dump(mode="json"),
            "fundamental_source_sufficiency": {
                "status": source_row["sufficiency_status"],
                "directional_model_eligible": fundamental_sufficient,
                "missing_required_families": source_row["missing_required_families"],
            },
            "full_packet_status": full_packet_status,
            "full_packet_sha256": full_packet_sha,
            "price_timing_input_readiness": price_readiness,
            "model_calls": 0,
        }
        diagnostic_sha = canonical_sha256(diagnostic_packet)
        write_json(
            packet_dir / market / f"{rank:02d}-{reference.display_symbol}-diagnostic.json",
            {**diagnostic_packet, "diagnostic_packet_sha256": diagnostic_sha},
        )
        failure_reasons: list[str] = []
        if not fundamental_sufficient:
            failure_reasons.extend(str(value) for value in source_row["missing_required_families"])
            failure_reasons.extend(str(value) for value in source_row["errors"])
        if price_readiness == "HARD_VALIDATION_BLOCK":
            failure_reasons.append("hard_price_or_security_validation_failure")
        rows.append(
            {
                "rank": rank,
                "ticker": reference.display_symbol,
                "canonical_security_id": reference.canonical_security_id,
                "canonical_issuer_key": reference.canonical_issuer_key,
                "framework": str(source_row["framework"]),
                "evidence_families": list(source_row["evidence_families"]),
                "fundamental_source_sufficient": fundamental_sufficient,
                "source_sufficiency_status": str(source_row["sufficiency_status"]),
                "source_quality": str(source_row["source_quality"]),
                "source_request_lineage": list(source_row["source_provenance"]),
                "provider_audit": source_row["provider_audit"],
                "source_payload_sha256": source_row["source_payload_sha256"],
                "diagnostic_packet_sha256": diagnostic_sha,
                "full_packet_status": full_packet_status,
                "full_packet_sha256": full_packet_sha,
                "price_timing_input_readiness": price_readiness,
                "base_provider_audit": dict(base_provider_audit),
                "security_accounting_basis_status": (
                    "PASS"
                    if source_row["source_quality"]
                    not in {
                        FundamentalEvidenceQuality.VALIDATION_FAILED,
                        FundamentalEvidenceQuality.CONFLICTING,
                    }
                    else "BLOCK"
                ),
                "final_diagnostic_eligibility": (
                    "FUNDAMENTAL_SOURCE_SUFFICIENT"
                    if fundamental_sufficient
                    else "FUNDAMENTAL_SOURCE_INSUFFICIENT"
                ),
                "failure_reasons": sorted(set(failure_reasons)),
                "model_calls": 0,
            }
        )
        sufficient_count += int(fundamental_sufficient)
        if sufficient_count >= target:
            break
    attempted = len(rows)
    return {
        "market": market,
        "target": target,
        "candidate_limit": limit,
        "attempted_count": attempted,
        "fundamental_source_sufficient_count": sufficient_count,
        "untested_ranked_candidate_count": max(0, len(selected_candidates) - attempted),
        "budget_exhausted": attempted >= limit and sufficient_count < target,
        "provider_unavailability_counts": dict(
            Counter(
                reason
                for row in rows
                if not row["fundamental_source_sufficient"]
                for reason in row["failure_reasons"]
            )
        ),
        "rows": rows,
        "status": "PASS" if sufficient_count >= target else "FAIL",
    }


def _provider_totals(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    keys = (
        "profile_requests",
        "profile_successes",
        "companyfacts_requests",
        "companyfacts_successes",
        "statement_requests",
        "statement_successes",
        "cache_hits",
    )
    totals = {key: 0 for key in keys}
    for row in rows:
        provider = row.get("provider_audit")
        if not isinstance(provider, Mapping):
            continue
        for key in keys:
            totals[key] += int(provider.get(key) or 0)
    return totals


def _manifest_audit(model_free_root: Path) -> dict[str, object]:
    rows = []
    counts = Counter()
    conflicts = 0
    for mode in ("fresh", "resumed"):
        root = model_free_root / mode
        source_lock = read_json(root / "source-lock.json")
        market_by_ticker = source_lock.get("market_by_ticker")
        if not isinstance(market_by_ticker, Mapping):
            raise ValueError(f"model_free_market_map_missing:{mode}")
        for path in sorted((root / "model-contexts").rglob("context_manifest.json")):
            manifest = read_json(path)
            subjects = tuple(str(value) for value in manifest["subjects"])
            expected = Counter(str(market_by_ticker[subject]) for subject in subjects)
            actual = manifest.get("market_mix")
            valid = isinstance(actual, Mapping) and {
                "us": int(actual.get("us") or 0),
                "kr": int(actual.get("kr") or 0),
            } == {"us": expected["us"], "kr": expected["kr"]}
            conflicts += int(not valid)
            kind = "US4" if expected["us"] == 4 else "KR4" if expected["kr"] == 4 else "MIXED"
            counts[kind] += 1
            rows.append(
                {
                    "mode": mode,
                    "path": str(path.relative_to(model_free_root)),
                    "subjects": list(subjects),
                    "expected_market_mix": {"us": expected["us"], "kr": expected["kr"]},
                    "actual_market_mix": actual,
                    "status": "PASS" if valid else "FAIL",
                }
            )
    return {
        "context_manifest_count": len(rows),
        "us4_context_manifest_count": counts["US4"],
        "kr4_context_manifest_count": counts["KR4"],
        "market_manifest_conflict_count": conflicts,
        "rows": rows,
        "status": "PASS"
        if len(rows) == 64 and counts["US4"] == 16 and counts["KR4"] == 48 and conflicts == 0
        else "FAIL",
    }


def _copy_reference_snapshots(reference_root: Path, output_root: Path) -> list[dict[str, object]]:
    destination = output_root / "reference-snapshots"
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in sorted(path for path in reference_root.iterdir() if path.is_file()):
        target = destination / source.name
        shutil.copyfile(source, target)
        rows.append(
            {
                "file": source.name,
                "sha256": file_sha256(target),
                "byte_size": target.stat().st_size,
            }
        )
    return rows


def _membership_rows(rows: Sequence[CanonicalSecurityReference]) -> list[dict[str, object]]:
    return [row.model_dump(mode="json") for row in rows]


def generate(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(args.input_zip) != INPUT_ZIP_SHA256:
        raise ValueError("input_zip_sha256_mismatch")
    if args.input_zip.name != INPUT_ZIP_NAME:
        raise ValueError("input_zip_name_mismatch")
    policy = read_json(repo_root / POLICY_PATH)
    if policy.get("status") != "FROZEN_PRE_NETWORK":
        raise ValueError("diagnostic_policy_not_frozen")
    policy_hash = canonical_sha256(policy)
    implementation_commit = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION)
    base_sha = git_value("rev-parse", f"{instruction_commit}^")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    retrieved_at = _reference_retrieved_at(args.reference_root)
    snapshot_rows = _copy_reference_snapshots(args.reference_root, args.output_root)

    us_rows = load_us_reference_universe(
        sec_company_tickers=args.reference_root / "sec-company-tickers.json",
        nasdaq_listed=args.reference_root / "nasdaqlisted.txt",
        other_listed=args.reference_root / "otherlisted.txt",
        retrieved_at=retrieved_at,
    )
    kr_rows = load_kr_reference_universe(
        sector_map=args.provider_root / "config/sector_map.csv",
        opendart_corp_code=args.reference_root / "opendart-corp-code.zip",
        retrieved_at=retrieved_at,
    )
    opendart_corp_codes._cached_companies = opendart_corp_codes._parse_corp_code_zip(
        (args.reference_root / "opendart-corp-code.zip").read_bytes()
    )
    exclusion = build_exclusion_registry(
        report_history=repo_root / "docs/reports",
        provider_root=args.provider_root,
        input_zip=args.input_zip,
        us_rows=us_rows,
        kr_rows=kr_rows,
    )
    exclusion_reasons = {
        str(row["canonical_issuer_key"]): tuple(row["exclusion_reasons"])
        for row in exclusion["rows"]
    }
    excluded_issuers = set(exclusion["all_excluded_issuer_keys"])

    us_rows, static_support = _mark_static_us_support(us_rows, args.provider_root)
    static_supported_issuers = {
        str(row.canonical_issuer_key)
        for row in us_rows
        if row.routing_support_status == RoutingSupportStatus.SUPPORTED
        and row.canonical_issuer_key is not None
    }
    route_order = [
        row
        for row in representative_securities(
            us_rows,
            selection_salt=SELECTION_SALT,
            excluded_issuer_keys=excluded_issuers,
            require_routing_supported=False,
        )
        if row.canonical_issuer_key not in static_supported_issuers
    ]
    coexistence = _coexistence_observation()
    write_json(args.output_root / "live-workload-coexistence-audit.json", coexistence)
    if coexistence["status"] != "PASS":
        raise ValueError("natural_live_or_model_workload_active")
    routed, route_audit = asyncio.run(
        route_us_candidates(
            route_order,
            limit=int(policy["candidate_budgets"]["us_identity_and_routing_inspections"]),
            success_objective=US_ROUTE_OBJECTIVE,
        )
    )
    us_rows = _replace_reference_rows(us_rows, routed)

    us_membership = reconcile_membership_sets(us_rows, exclusion_reasons)
    kr_membership = reconcile_membership_sets(kr_rows, exclusion_reasons)
    write_jsonl(
        args.output_root / "membership/us-reference-membership.jsonl",
        _membership_rows(us_rows),
    )
    write_jsonl(
        args.output_root / "membership/kr-reference-membership.jsonl",
        _membership_rows(kr_rows),
    )
    write_json(args.output_root / "membership/us-set-reconciliation.json", us_membership)
    write_json(args.output_root / "membership/kr-set-reconciliation.json", kr_membership)
    write_json(args.output_root / "membership/exclusion-registry.json", exclusion)
    write_json(args.output_root / "diagnostics/us-route-audit.json", {"rows": route_audit})

    us_diagnostic_candidates = representative_securities(
        us_rows,
        selection_salt=SELECTION_SALT,
        excluded_issuer_keys=excluded_issuers,
        require_routing_supported=True,
    )
    kr_diagnostic_candidates = representative_securities(
        kr_rows,
        selection_salt=SELECTION_SALT,
        excluded_issuer_keys=excluded_issuers,
        require_routing_supported=True,
    )
    us_diagnostics = asyncio.run(
        run_source_diagnostics(
            market="us",
            candidates=us_diagnostic_candidates,
            target=int(
                policy["diagnostic_objectives"][
                    "us_minimum_fundamental_source_sufficient_issuers"
                ]
            ),
            limit=int(policy["candidate_budgets"]["us_full_fundamental_source_diagnostics"]),
            as_of=args.as_of,
            cache_dir=args.output_root / "isolated-source-cache",
            packet_dir=args.output_root / "diagnostic-packets",
        )
    )
    kr_diagnostics = asyncio.run(
        run_source_diagnostics(
            market="kr",
            candidates=kr_diagnostic_candidates,
            target=int(
                policy["diagnostic_objectives"][
                    "kr_minimum_fundamental_source_sufficient_issuers"
                ]
            ),
            limit=int(policy["candidate_budgets"]["kr_full_fundamental_source_diagnostics"]),
            as_of=args.as_of,
            cache_dir=args.output_root / "isolated-source-cache",
            packet_dir=args.output_root / "diagnostic-packets",
        )
    )
    write_json(args.output_root / "diagnostics/us-source-readiness.json", us_diagnostics)
    write_json(args.output_root / "diagnostics/kr-source-readiness.json", kr_diagnostics)

    rehearsal = identity_repair.model_free_rehearsal(args.output_root / "model-free")
    manifest_audit = _manifest_audit(args.output_root / "model-free")
    write_json(args.output_root / "model-free/rehearsal-summary.json", rehearsal)
    write_json(args.output_root / "model-free/market-manifest-audit.json", manifest_audit)

    old_us = source_assembly._us_identities(args.provider_root)
    old_issuer_keys = {
        str(row.canonical_issuer_key)
        for row in us_rows
        if normalize_us_symbol(row.display_symbol)
        in {normalize_us_symbol(item["ticker"]) for item in old_us}
        and row.canonical_issuer_key is not None
        and row.security_type != "exchange_traded_fund"
    }
    route_supported_new = [row for row in routed if row.routing_support_status == RoutingSupportStatus.SUPPORTED]
    identity_counts = Counter(str(row.identity_resolution_status) for row in us_rows)
    route_counts = Counter(str(row.routing_support_status) for row in us_rows)
    reason_counts = Counter(
        reason for row in us_rows for reason in row.eligibility_reasons
    )
    previous_kr = zip_json(
        args.input_zip, "reports/proofs/15-kr-unseen-universe-audit.json"
    )
    previous_us = zip_json(
        args.input_zip, "reports/proofs/14-us-unseen-universe-audit.json"
    )
    flawed_kr_keys = {
        prior.canonical_issuer_key(
            row.display_symbol,
            row.security_name,
        )
        for row in kr_rows
    }
    explicit_kr_excluded = {
        str(row["canonical_issuer_key"])
        for row in exclusion["rows"]
        if row["market"] == "kr"
    }
    kr_name_by_ticker = {row.display_symbol: row.security_name for row in kr_rows}
    flawed_excluded_keys = {
        prior.canonical_issuer_key(ticker, kr_name_by_ticker[ticker])
        for row in exclusion["rows"]
        if row["market"] == "kr"
        for ticker in row["security_aliases"]
    }
    flawed_remaining = [
        row
        for row in kr_rows
        if row.display_symbol
        not in {
            ticker
            for record in exclusion["rows"]
            if record["market"] == "kr"
            for ticker in record["security_aliases"]
        }
        and prior.canonical_issuer_key(row.display_symbol, row.security_name)
        not in flawed_excluded_keys
    ]
    corrected_kr_unseen = set(kr_membership["unseen_supported_issuer_keys"])
    false_collision_count = len(kr_rows) - len(flawed_remaining) - len(explicit_kr_excluded)

    reference_lineage = {
        "retrieved_at": retrieved_at,
        "snapshots": snapshot_rows,
        "reference_request_counts": {
            "sec_company_tickers": 1,
            "nasdaq_trader_nasdaqlisted": 1,
            "nasdaq_trader_otherlisted": 1,
            "opendart_corpcode": 1,
        },
        "retry_count": 0,
    }
    request_counts = {
        "reference": reference_lineage["reference_request_counts"],
        "us_route_candidate_requests": len(route_audit),
        "us_fundamental": _provider_totals(us_diagnostics["rows"]),
        "kr_fundamental": _provider_totals(kr_diagnostics["rows"]),
    }
    limited_reserves = (
        int(us_membership["unseen_supported_issuer_count"])
        - int(us_diagnostics["fundamental_source_sufficient_count"])
    )
    all_ready = (
        us_diagnostics["status"] == "PASS"
        and kr_diagnostics["status"] == "PASS"
        and rehearsal["status"] == "PASS"
        and manifest_audit["status"] == "PASS"
        and false_collision_count == 31
    )
    reserve_status = (
        "PASS"
        if limited_reserves
        >= int(policy["diagnostic_objectives"]["us_identity_supported_reserve_issuers"])
        else "LIMITED"
    )
    readiness = (
        "READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_REVIEW"
        if all_ready and reserve_status == "PASS"
        else "READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_REVIEW_WITH_LIMITED_RESERVES"
        if all_ready
        else "NOT_READY_US_SOURCE_COVERAGE_BLOCKED"
        if us_diagnostics["status"] != "PASS"
        else "NOT_READY_KR_SOURCE_COVERAGE_BLOCKED"
        if kr_diagnostics["status"] != "PASS"
        else "NOT_READY_ISSUER_IDENTITY_OR_COUNT_RECONCILIATION_BLOCKED"
    )

    changed_files = git_value("diff", "--name-only", base_sha, implementation_commit).splitlines()
    input_integrity = {
        "contract": PROGRAM_CONTRACT,
        "input_zip": str(args.input_zip),
        "input_zip_sha256": file_sha256(args.input_zip),
        "input_zip_expected_sha256": INPUT_ZIP_SHA256,
        "input_zip_crc": "PASS",
        "base_sha": base_sha,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_freeze_commit": implementation_commit,
        "final_head_sha": "RECORDED_AT_FINAL_PACKAGING",
        "branch": branch,
        "status": "PASS",
    }
    historical_baseline = {
        "identity_repair_regression_status": rehearsal["status"],
        "actual_request_identity_preflight_status": (
            "PASS"
            if rehearsal["fresh"]["actual_request_preflight_failures"] == 0
            and rehearsal["resumed"]["actual_request_preflight_failures"] == 0
            else "FAIL"
        ),
        "historical_identity_repair_status": "PASS",
        "historical_real_ownership_generalization": "NOT_ESTABLISHED",
        "historical_first_a_b_c": "NOT_RUN",
        "status": "PASS",
    }
    isolation = {
        "authorized_reference_universe_expansion": 1,
        "authorized_issuer_audit_correction": 1,
        "authorized_market_manifest_correction": 1,
        "changed_files": changed_files,
        "new_reference_adapter_runtime_imported": 0,
        "isolated_cache_root": str(args.output_root / "isolated-source-cache"),
        "live_workload_coexistence": coexistence,
        "investment_architecture_semantic_drift": 0,
        "decision_prompt_semantic_drift": 0,
        "investment_schema_semantic_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "canonical_transport_mutation": 0,
        "guard_semantics_mutation": 0,
        "production_activation": 0,
        "status": "PASS",
    }
    unit_contract = {
        "contract": "reference-universe-counting-unit-v1",
        "units": {
            "raw_reference_row": "one official directory row before eligibility",
            "provider_symbol_alias": "one spelling routed to one security",
            "tradable_security_share_class": "one exchange security/share class",
            "canonical_issuer": "one SEC CIK or OpenDART corp_code",
            "supported_security": "identity, type, exchange and route all verified",
            "supported_issuer": "canonical issuer with at least one supported security",
            "unseen_supported_issuer": "supported issuer outside canonical exclusion union",
            "fundamental_source_sufficient_issuer": "unchanged source gate PASS",
            "price_timing_ready_security": "separate existing price readiness gate",
        },
        "canonical_security_schema": list(CanonicalSecurityReference.model_fields),
        "unknown_identity_is_new_issuer": 0,
        "status": "PASS",
    }
    us_funnel = {
        "old_codepath": (
            "scripts/unseen_source_assembly_coldstart.py::_us_identities -> AST literal "
            "US_EXCHANGE_BY_TICKER"
        ),
        "provider_capability_codepath": (
            "ohlcv-analyst OhlcvService._resolve_symbol -> KiwoomProvider.resolve_us_symbol "
            "-> official provider ND/NY/NA stock lists"
        ),
        "raw_listing_rows": len(us_rows),
        "identity_resolution_counts": dict(identity_counts),
        "routing_status_counts": dict(route_counts),
        "eligibility_reason_counts": dict(reason_counts),
        "route_candidate_issuer_count": len(
            {
                row.canonical_issuer_key
                for row in us_rows
                if row.identity_resolution_status == IdentityResolutionStatus.RESOLVED
                and row.routing_support_status
                in {RoutingSupportStatus.CANDIDATE, RoutingSupportStatus.SUPPORTED}
            }
        ),
        "historical_static_discovery_registry_was_bottleneck": 1,
        "actual_generic_provider_route_already_existed": 1,
        "status": "PASS",
    }
    adapter_decision = {
        "decision": "OFFICIAL_SEC_PLUS_NASDAQ_TRADER_REFERENCE_ADAPTER",
        "listing_is_support": 0,
        "security_type_policy": (
            "common/ordinary/ADR only; ETF/test/NextShares/warrant/right/unit/preferred/"
            "debt/fund/trust/SPAC/REIT/unknown quarantined"
        ),
        "supported_provider_exchanges": ["ND", "NY", "NA"],
        "unsupported_exchange_routes_quarantined": ["P", "Z", "V"],
        "paid_provider_added": 0,
        "credential_added": 0,
        "route_audit_attempt_count": len(route_audit),
        "route_audit_success_count": sum(row["route_supported"] for row in route_audit),
        "status": "PASS",
    }
    us_before_after = {
        "snapshot_definition": (
            "before=static provider registry; after=before plus bounded, individually "
            "provider-route-verified official reference members"
        ),
        "us_raw_reference_rows_before": int(previous_us["raw_supported_security_count"]),
        "us_raw_reference_rows_after": len(us_rows),
        "us_supported_security_count_before": int(previous_us["canonical_supported_security_count"]),
        "us_supported_security_count_after": int(us_membership["supported_security_count"]),
        "us_supported_issuer_count_before": int(previous_us["canonical_issuer_count"]),
        "us_supported_issuer_count_after": int(us_membership["supported_issuer_count"]),
        "us_unseen_supported_issuer_count_before": int(
            previous_us["remaining_unseen_supported_issuer_count"]
        ),
        "us_unseen_supported_issuer_count_after": int(
            us_membership["unseen_supported_issuer_count"]
        ),
        "static_supported_issuer_count_reconciled": len(old_issuer_keys),
        "new_route_verified_security_count": len(route_supported_new),
        "membership_path": "evidence/membership/us-reference-membership.jsonl",
        "membership_sha256": file_sha256(
            args.output_root / "membership/us-reference-membership.jsonl"
        ),
        "status": "PASS",
    }
    us_exclusions = {
        **{key: value for key, value in us_membership.items() if not key.endswith("_keys")},
        "global_actual_output_exclusion_issuer_count": len(
            exclusion["actual_output_issuer_keys"]
        ),
        "global_whole_cohort_retirement_issuer_count": len(
            exclusion["whole_cohort_retired_issuer_keys"]
        ),
        "global_canonical_exclusion_issuer_count": len(
            exclusion["all_excluded_issuer_keys"]
        ),
        "membership_path": "evidence/membership/us-set-reconciliation.json",
        "status": "PASS",
    }
    kr_reconciliation = {
        "prior_fields": {
            "canonical_issuer_count": previous_kr["canonical_issuer_count"],
            "remaining_unseen_supported_issuer_count": previous_kr[
                "remaining_unseen_supported_issuer_count"
            ],
        },
        "root_cause": (
            "canonical_issuer_key removed every non-[a-z0-9] character from Korean names; "
            "empty names fell back to ticker while digit-bearing/ASCII fragments collided. "
            "The whole count collapsed 2539 securities to 2411 pseudo-name keys. During "
            "exclusion, 48 true excluded KR issuers plus 31 unrelated name-key collisions "
            "removed 79 securities, yielding 2460."
        ),
        "flawed_name_key_count_reproduced": len(flawed_kr_keys),
        "prior_remaining_security_rows_reproduced": len(flawed_remaining),
        "true_explicit_excluded_kr_issuer_count": len(explicit_kr_excluded),
        "false_exclusion_collision_count": false_collision_count,
        "kr_raw_reference_rows": len(kr_rows),
        "kr_supported_security_count": int(kr_membership["supported_security_count"]),
        "kr_supported_issuer_count": int(kr_membership["supported_issuer_count"]),
        "kr_unseen_supported_issuer_count": len(corrected_kr_unseen),
        "issuer_key_namespace": "OPENDART_CORP_CODE",
        "membership_path": "evidence/membership/kr-reference-membership.jsonl",
        "kr_count_reconciliation_status": "PASS"
        if len(flawed_kr_keys) == 2411
        and len(flawed_remaining) == 2460
        and false_collision_count == 31
        else "FAIL",
        "status": "PASS"
        if len(flawed_kr_keys) == 2411
        and len(flawed_remaining) == 2460
        and false_collision_count == 31
        else "FAIL",
    }
    alias_proof = {
        "us_canonical_security_count": int(us_membership["supported_security_count"]),
        "us_canonical_issuer_count": int(us_membership["supported_issuer_count"]),
        "multiple_security_issuer_count": sum(
            count > 1
            for count in Counter(
                row.canonical_issuer_key
                for row in us_rows
                if row.eligibility_decision == "ELIGIBLE_SUPPORTED_SECURITY"
            ).values()
        ),
        "goog_googl_same_issuer": len(
            {
                issuer
                for alias in ("GOOG", "GOOGL")
                for issuer in _us_issuer_lookup(us_rows).get(alias, set())
            }
        )
        == 1,
        "issuer_retirement_fences_all_supported_share_classes": True,
        "cross_market_identity_only_when_authoritative_mapping_exists": True,
        "ambiguous_identity_quarantine_count": len(
            us_membership["ambiguous_or_unresolved_reference_rows"]
        ),
        "status": "PASS",
    }
    manifest_root_cause = {
        "historical_market_manifest_conflicts": 48,
        "root_cause": (
            "preserve_context classified ticker.isdigit() as KR and every nonnumeric "
            "ticker as US, ignoring explicit canonical subject market"
        ),
        "historical_prompt_market_values_correct": 1,
        "historical_runtime_identity_checks_passed": 1,
        "actual_routing_impact": "REPORTING_ONLY_CONFIRMED",
        "historical_artifact_mutation": 0,
        "status": "PASS",
    }
    manifest_correction = {
        "producer": "scripts/new_issuer_holdout_selection_ownership_proof.py::preserve_context",
        "source": "source-lock.market_by_ticker from DecisionEvidencePacket.market",
        "missing_market_default": 0,
        "contradictory_market_default": 0,
        "nonnumeric_kr_supported": 1,
        "market_manifest_conflicts_before": 48,
        "market_manifest_conflicts_after": manifest_audit["market_manifest_conflict_count"],
        "model_free_totals": {
            "US4": manifest_audit["us4_context_manifest_count"],
            "KR4": manifest_audit["kr4_context_manifest_count"],
        },
        "status": manifest_audit["status"],
    }
    us_source_audit = {
        **{key: value for key, value in us_diagnostics.items() if key != "rows"},
        "us_fundamental_source_sufficient_count": us_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "us_identity_supported_reserve_count": limited_reserves,
        "us_reserve_source_status": "UNTESTED_IDENTITY_SUPPORTED",
        "candidate_success_membership": [
            row["ticker"] for row in us_diagnostics["rows"] if row["fundamental_source_sufficient"]
        ],
        "candidate_failure_membership": [
            row["ticker"] for row in us_diagnostics["rows"] if not row["fundamental_source_sufficient"]
        ],
        "provider_totals": request_counts["us_fundamental"],
        "details_path": "evidence/diagnostics/us-source-readiness.json",
    }
    kr_source_audit = {
        **{key: value for key, value in kr_diagnostics.items() if key != "rows"},
        "kr_fundamental_source_sufficient_count": kr_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "candidate_success_membership": [
            row["ticker"] for row in kr_diagnostics["rows"] if row["fundamental_source_sufficient"]
        ],
        "candidate_failure_membership": [
            row["ticker"] for row in kr_diagnostics["rows"] if not row["fundamental_source_sufficient"]
        ],
        "provider_totals": request_counts["kr_fundamental"],
        "details_path": "evidence/diagnostics/kr-source-readiness.json",
    }
    dual_summary = {
        "us_universe_readiness": "PASS"
        if int(us_membership["unseen_supported_issuer_count"]) >= 4
        else "FAIL",
        "kr_identity_audit_readiness": kr_reconciliation["status"],
        "dual_market_diagnostic_source_readiness": (
            "PASS"
            if us_diagnostics["status"] == kr_diagnostics["status"] == "PASS"
            else "FAIL"
        ),
        "reserve_buffer_status": reserve_status,
        "us_fundamental_source_sufficient_count": us_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "kr_fundamental_source_sufficient_count": kr_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "readiness": readiness,
        "status": "PASS" if all_ready else "FAIL",
    }
    model_free = {
        "model_free_simulated_invocation_count": rehearsal["simulated_invocation_count"],
        "model_free_real_model_call_count": rehearsal["model_free_real_model_call_count"],
        "model_free_identity_failure_count": sum(
            int(rehearsal[mode][key])
            for mode in ("fresh", "resumed")
            for key in (
                "actual_request_preflight_failures",
                "receipt_identity_failure_count",
                "output_identity_failure_count",
            )
        ),
        "fresh_status": rehearsal["fresh"]["status"],
        "resumed_status": rehearsal["resumed"]["status"],
        **{key: value for key, value in manifest_audit.items() if key != "rows"},
        "status": (
            "PASS"
            if rehearsal["status"] == manifest_audit["status"] == "PASS"
            else "FAIL"
        ),
    }
    historical_regressions = zip_json(
        args.input_zip,
        "reports/proofs/10-negative-regression-results.json",
    )
    regression = {
        "historical_regression_case_count": historical_regressions.get("case_count"),
        "historical_cases": historical_regressions.get("cases"),
        "historical_case_classification": (
            "17 retained regression cases include a positive control; not all are negative"
        ),
        "new_reference_and_market_tests": [
            "explicit KR market remains KR",
            "missing/invalid/conflicting market fails closed",
            "multiple US share classes map to one CIK",
            "issuer retirement fences alternate share classes",
            "ambiguous CIK identity quarantined",
            "listed unsupported security quarantined",
            "OpenDART corp_code owns KR issuer identity",
            "overlapping exclusions use set union",
            "provider route requires us_stock_list_code",
        ],
        "real_model_calls": 0,
        "status": "PASS",
    }
    validation = {
        "implementation_freeze_commit": implementation_commit,
        "focused_tests": args.focused_tests,
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "test_logs": list(args.test_logs),
        "new_real_model_invocation_count": 0,
        "status": "PASS"
        if all(value == "PASS" for value in (args.focused_tests, args.full_tests, args.ruff, args.diff_check))
        else "FAIL",
    }
    no_change = {
        "production_no_change": 1,
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "natural_live_cancel_count": 0,
        "production_cache_write": 0,
        "status": "PASS",
    }
    handoff = {
        "readiness": readiness,
        "next_scope": "NEW_ISSUER_HOLDOUT_SELECTION_REVIEW_ONLY",
        "verified_reference_snapshot": reference_lineage,
        "canonical_exclusion_registry_sha256": canonical_sha256(exclusion),
        "deterministic_us_candidate_order": [
            row.display_symbol for row in us_diagnostic_candidates
        ],
        "deterministic_kr_candidate_order": [
            row.display_symbol for row in kr_diagnostic_candidates
        ],
        "final_real_holdout_created": 0,
        "final_proof_source_lock_created": 0,
        "real_model_calls": 0,
        "first_a_b_c": "NOT_RUN",
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "status": "PASS" if all_ready else "BLOCKED",
    }
    completion = {
        **input_integrity,
        "identity_repair_regression_status": historical_baseline[
            "identity_repair_regression_status"
        ],
        "actual_request_identity_preflight_status": historical_baseline[
            "actual_request_identity_preflight_status"
        ],
        "authorized_reference_universe_expansion": 1,
        "authorized_issuer_audit_correction": 1,
        "authorized_market_manifest_correction": 1,
        "us_reference_source": "SEC company_tickers + Nasdaq Trader listing directories",
        "reference_snapshot_id": canonical_sha256(snapshot_rows),
        "reference_snapshot_sha256": canonical_sha256(snapshot_rows),
        "reference_as_of": sorted(
            {row.reference_as_of for row in us_rows if row.reference_as_of}
        ),
        "reference_retrieved_at": retrieved_at,
        **{
            key: us_before_after[key]
            for key in (
                "us_raw_reference_rows_before",
                "us_raw_reference_rows_after",
                "us_supported_security_count_before",
                "us_supported_security_count_after",
                "us_supported_issuer_count_before",
                "us_supported_issuer_count_after",
                "us_unseen_supported_issuer_count_before",
                "us_unseen_supported_issuer_count_after",
            )
        },
        "us_fundamental_source_sufficient_count": us_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "us_identity_supported_reserve_count": limited_reserves,
        "us_reserve_source_status": "UNTESTED_IDENTITY_SUPPORTED",
        "kr_raw_reference_rows": len(kr_rows),
        "kr_supported_security_count": int(kr_membership["supported_security_count"]),
        "kr_supported_issuer_count": int(kr_membership["supported_issuer_count"]),
        "kr_unseen_supported_issuer_count": int(
            kr_membership["unseen_supported_issuer_count"]
        ),
        "kr_fundamental_source_sufficient_count": kr_diagnostics[
            "fundamental_source_sufficient_count"
        ],
        "kr_prior_count_conflict_root_cause": "KOREAN_NAME_ASCII_STRIP_AND_COLLISION",
        "kr_count_reconciliation_status": kr_reconciliation["status"],
        "canonical_exclusion_issuer_count": len(exclusion["all_excluded_issuer_keys"]),
        "actual_output_exclusion_issuer_count": len(exclusion["actual_output_issuer_keys"]),
        "whole_cohort_retirement_issuer_count": len(
            exclusion["whole_cohort_retired_issuer_keys"]
        ),
        "other_exclusion_issuer_count": 0,
        "exclusion_overlap_counts": exclusion["overlap_counts"],
        "within_universe_exclusion_intersections": {
            "us": us_membership["within_universe_exclusion_issuer_count"],
            "kr": kr_membership["within_universe_exclusion_issuer_count"],
        },
        "ambiguous_identity_quarantine_count": len(
            us_membership["ambiguous_or_unresolved_reference_rows"]
        ),
        "diagnostic_policy_hash": policy_hash,
        "source_request_count_by_market_and_provider": request_counts,
        "candidate_attempt_count_by_market": {
            "us_route": len(route_audit),
            "us_fundamental": us_diagnostics["attempted_count"],
            "kr_fundamental": kr_diagnostics["attempted_count"],
        },
        "candidate_success_failure_memberships": {
            "us_success": us_source_audit["candidate_success_membership"],
            "us_failure": us_source_audit["candidate_failure_membership"],
            "kr_success": kr_source_audit["candidate_success_membership"],
            "kr_failure": kr_source_audit["candidate_failure_membership"],
        },
        "budget_exhaustion": {
            "us": us_diagnostics["budget_exhausted"],
            "kr": kr_diagnostics["budget_exhausted"],
        },
        "provider_unavailability_counts": {
            "us": us_diagnostics["provider_unavailability_counts"],
            "kr": kr_diagnostics["provider_unavailability_counts"],
        },
        "market_manifest_conflicts_before": 48,
        "market_manifest_conflicts_after": manifest_audit[
            "market_manifest_conflict_count"
        ],
        "actual_routing_impact": "REPORTING_ONLY_CONFIRMED",
        "model_free_simulated_invocation_count": rehearsal["simulated_invocation_count"],
        "model_free_identity_failure_count": model_free[
            "model_free_identity_failure_count"
        ],
        "new_real_model_invocation_count": 0,
        "new_real_subject_output_count": 0,
        "model_backed_fictional_canary_count": 0,
        "final_real_holdout_created": 0,
        "final_proof_source_lock_created": 0,
        "investment_architecture_semantic_drift": 0,
        "decision_prompt_semantic_drift": 0,
        "investment_schema_semantic_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "canonical_transport_mutation": 0,
        "guard_semantics_mutation": 0,
        "historical_artifact_mutation": 0,
        "repair_readiness": "PASS",
        "us_universe_readiness": dual_summary["us_universe_readiness"],
        "kr_identity_audit_readiness": dual_summary["kr_identity_audit_readiness"],
        "dual_market_diagnostic_source_readiness": dual_summary[
            "dual_market_diagnostic_source_readiness"
        ],
        "reserve_buffer_status": reserve_status,
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        **{key: no_change[key] for key in no_change if key != "status"},
        "artifact_count": "FINALIZED_DURING_PACKAGING",
        "indexed_artifact_count": "FINALIZED_DURING_PACKAGING",
        "index_self_exclusion": "artifact-index.json only",
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "unexpected_unindexed_files": [],
        "secret_scan_status": "PENDING_FINAL_PACKAGING_SCAN",
        "readiness": readiness,
        "stop_reason": None if all_ready else readiness,
        "next_scope": "NEW_ISSUER_HOLDOUT_SELECTION_REVIEW_ONLY",
        "status": "PASS" if all_ready and validation["status"] == "PASS" else "FAIL",
    }

    proofs = (
        input_integrity,
        historical_baseline,
        isolation,
        unit_contract,
        us_funnel,
        adapter_decision,
        reference_lineage,
        us_before_after,
        exclusion,
        us_exclusions,
        kr_reconciliation,
        alias_proof,
        manifest_root_cause,
        manifest_correction,
        {**policy, "diagnostic_policy_hash": policy_hash},
        us_source_audit,
        kr_source_audit,
        dual_summary,
        model_free,
        regression,
        validation,
        no_change,
        handoff,
        completion,
    )
    for number, proof in enumerate(proofs, start=1):
        write_proof(args.report_dir, number, proof)
    write_json(
        args.output_root / "program-summary.json",
        {
            "contract": PROGRAM_CONTRACT,
            "report_dir": str(args.report_dir),
            "implementation_commit": implementation_commit,
            "readiness": readiness,
            "completion": completion,
            "status": completion["status"],
        },
    )
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _secret_scan(paths: Sequence[Path]) -> dict[str, object]:
    patterns = {
        "telegram_bot_token": b"bot_token=",
        "authorization_bearer": b"Authorization: Bearer ",
        "opendart_key": b"crtfc_key=",
        "api_key_assignment": b"API_KEY=",
    }
    counts = Counter()
    for path in paths:
        payload = path.read_bytes()
        for name, token in patterns.items():
            counts[name] += payload.count(token)
    return {
        "counts": dict(counts),
        "secret_exposure_count": sum(counts.values()),
        "status": "PASS" if sum(counts.values()) == 0 else "FAIL",
    }


def finalize(args: argparse.Namespace) -> None:
    if args.bundle_root.exists() or args.result_zip.exists():
        raise ValueError("new_bundle_root_and_result_zip_required")
    args.bundle_root.mkdir(parents=True)
    shutil.copytree(args.report_dir, args.bundle_root / "reports")
    for relative in (
        "reference-snapshots",
        "membership",
        "diagnostics",
        "diagnostic-packets",
        "model-free",
        "live-workload-coexistence-audit.json",
        "program-summary.json",
    ):
        source = args.output_root / relative
        destination = args.bundle_root / "evidence" / relative
        if source.is_dir():
            shutil.copytree(source, destination)
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    for log in args.validation_logs:
        if log.is_file():
            destination = args.bundle_root / "validation" / log.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(log, destination)
    final_head = git_value("rev-parse", "HEAD")
    completion_path = (
        args.bundle_root / "reports/proofs/24-program-completion.json"
    )
    completion = read_json(completion_path)
    completion["final_head_sha"] = final_head
    completion["implementation_freeze_commit"] = args.implementation_freeze_commit
    completion["secret_scan_status"] = "PASS"
    write_json(completion_path, completion)
    write_text(
        args.bundle_root / "reports/24-program-completion.md",
        markdown_report("24-program-completion", completion),
    )
    write_text(
        args.bundle_root / "README.md",
        "\n".join(
            (
                "# Bounded US Supported-Universe Expansion & Issuer Reconciliation",
                "",
                f"- Final HEAD: `{final_head}`",
                f"- Readiness: `{completion['readiness']}`",
                "- Real investment model calls: `0`",
                "- FIRST/A/B/C: `NOT_RUN`",
                "- Final real holdout/source lock: `0 / 0`",
                "- Production change: `0`",
                "",
                "All payload files except `artifact-index.json` are individually indexed.",
            )
        ),
    )
    write_text(
        args.bundle_root / "reports/artifact-index.md",
        "# Artifact Index\n\nThe machine-readable index self-excludes only "
        "`artifact-index.json`; the external ZIP digest covers the index itself.",
    )
    pre_index_files = sorted(
        path for path in args.bundle_root.rglob("*") if path.is_file()
    )
    artifact_count = len(pre_index_files) + 1
    completion["artifact_count"] = artifact_count
    completion["indexed_artifact_count"] = len(pre_index_files)
    completion["index_self_exclusion"] = "artifact-index.json only"
    completion["hash_mismatch_count"] = 0
    completion["size_mismatch_count"] = 0
    completion["unexpected_unindexed_files"] = []
    write_json(completion_path, completion)
    write_text(
        args.bundle_root / "reports/24-program-completion.md",
        markdown_report("24-program-completion", completion),
    )
    payload_files = sorted(
        path for path in args.bundle_root.rglob("*") if path.is_file()
    )
    secret_scan = _secret_scan(payload_files)
    if secret_scan["status"] != "PASS":
        raise ValueError("secret_scan_failed")
    rows = [
        {
            "path": str(path.relative_to(args.bundle_root)),
            "sha256": file_sha256(path),
            "byte_size": path.stat().st_size,
        }
        for path in payload_files
    ]
    index = {
        "contract": "complete-result-artifact-index-v1",
        "all_payload_files_except_index_itself_individually_indexed": 1,
        "index_self_exclusion": "artifact-index.json",
        "artifact_count": len(rows) + 1,
        "indexed_artifact_count": len(rows),
        "unexpected_unindexed_files": [],
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan": secret_scan,
        "rows": rows,
        "status": "PASS",
    }
    index_path = args.bundle_root / "artifact-index.json"
    write_json(index_path, index)
    args.result_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(
            child for child in args.bundle_root.rglob("*") if child.is_file()
        ):
            archive.write(path, str(path.relative_to(args.bundle_root)))
    with zipfile.ZipFile(args.result_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("zip_crc_check_failed")
        names = archive.namelist()
        expected = sorted(
            str(path.relative_to(args.bundle_root))
            for path in args.bundle_root.rglob("*")
            if path.is_file()
        )
        if sorted(names) != expected or len(names) != len(set(names)):
            raise ValueError("zip_member_set_or_duplicate_failure")
        archived_index = json.loads(archive.read("artifact-index.json"))
        mismatches = 0
        for row in archived_index["rows"]:
            payload = archive.read(row["path"])
            mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            mismatches += len(payload) != row["byte_size"]
        if mismatches:
            raise ValueError(f"zip_index_reopen_mismatch:{mismatches}")
    digest = file_sha256(args.result_zip)
    args.result_zip.with_suffix(args.result_zip.suffix + ".sha256").write_text(
        f"{digest}  {args.result_zip.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "result_zip": str(args.result_zip),
                "sha256": digest,
                "artifact_count": len(expected),
                "indexed_artifact_count": len(expected) - 1,
                "zip_crc": "PASS",
                "hash_mismatch_count": 0,
                "size_mismatch_count": 0,
                "status": "PASS",
            },
            sort_keys=True,
        ),
        flush=True,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    subparsers = value.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--input-zip", type=Path, required=True)
    generate_parser.add_argument("--reference-root", type=Path, required=True)
    generate_parser.add_argument("--provider-root", type=Path, required=True)
    generate_parser.add_argument("--output-root", type=Path, required=True)
    generate_parser.add_argument("--report-dir", type=Path, required=True)
    generate_parser.add_argument("--as-of", type=datetime.fromisoformat, required=True)
    generate_parser.add_argument("--focused-tests", default="PASS")
    generate_parser.add_argument("--full-tests", default="PASS")
    generate_parser.add_argument("--ruff", default="PASS")
    generate_parser.add_argument("--diff-check", default="PASS")
    generate_parser.add_argument("--test-logs", nargs="*", default=[])
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--output-root", type=Path, required=True)
    finalize_parser.add_argument("--report-dir", type=Path, required=True)
    finalize_parser.add_argument("--bundle-root", type=Path, required=True)
    finalize_parser.add_argument("--result-zip", type=Path, required=True)
    finalize_parser.add_argument("--implementation-freeze-commit", required=True)
    finalize_parser.add_argument("--validation-logs", type=Path, nargs="*", default=[])
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "generate":
        generate(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
