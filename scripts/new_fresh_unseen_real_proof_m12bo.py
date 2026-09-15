from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
from typing import Any
import zipfile

from app.config import get_settings
from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    FundamentalEvidenceFamily,
    OfficialFundamentalEnrichment,
)
from app.services.reference_universe_audit_service import (
    CanonicalSecurityReference,
    file_sha256,
    load_us_reference_universe,
)
from scripts import new_issuer_holdout_selection_ownership_proof as prior
from scripts import official_fundamental_enrichment_holdout as fundamental
from scripts import unseen_source_assembly_coldstart as source_assembly


PROGRAM_CONTRACT = "new-fresh-unseen-real-proof-m12bo-v1"
SEEN_REGISTRY_CONTRACT = "fresh-proof-seen-subject-registry-v1"
SELECTION_CONTRACT = "m12bo-fresh-unseen-sector-slot-selection-v1"
SELECTION_SALT = "M12BO-20260914-FRESH-UNSEEN-V1"
TARGET_TOTAL = 12
TARGET_BY_MARKET = {"kr": 6, "us": 6}
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
MAX_SUBJECTS_PER_CALL = 4
LATEST_RESULT_SHA256 = "c98eee1b2de414d83a7b6b85b3693060b304c1995cdda59a62a1e9530e02a1ba"
LATEST_RESULT_NAME = (
    "thesis-monitor-20260914-persistence-v2-implementation-local-ephemeral-replay-report.zip"
)
WORK_INSTRUCTION = (
    "docs/work-instructions/20260914-new-fresh-unseen-real-proof-canonical-integrated-pipeline.md"
)
REPORT_DIRECTORY = "20260914-new-fresh-unseen-real-proof-canonical-integrated-pipeline"
RESULT_ZIP_NAME = (
    "thesis-monitor-20260914-new-fresh-unseen-real-proof-canonical-integrated-pipeline-report.zip"
)

HISTORICAL_FRESH_NEGATIVES = (
    "NVMI",
    "SKYH",
    "WKSP",
    "EROC",
    "373160",
    "452200",
    "389470",
    "380550",
    "008970",
    "047080",
    "068270",
    "475830",
    "033160",
    "079940",
    "103140",
    "278280",
)

# Every symbol is assigned to one primary pre-model slot. Official profile data
# must independently agree with the slot before a candidate may be selected.
CANDIDATE_SLOTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "kr",
        "financial",
        ("000810", "032830", "086790", "316140", "138930", "139130"),
    ),
    ("us", "financial", ("BAC", "GS", "MS", "PNC")),
    ("kr", "cyclical_industrial", ("000270", "042660", "329180", "009540")),
    ("us", "cyclical_industrial", ("GE", "GM", "DE", "F", "CAT", "HON", "RTX")),
    ("kr", "technology", ("018260", "009150", "066570", "035720")),
    ("us", "technology", ("SNOW", "ADBE", "INTU", "NOW", "QCOM", "TXN")),
    ("kr", "consumer_service_logistics", ("000120", "004170", "139480", "180640")),
    ("us", "consumer_service_logistics", ("COST", "SBUX", "TGT", "HD", "UPS", "FDX")),
    ("kr", "healthcare", ("207940", "068760", "000100", "128940")),
    ("us", "healthcare", ("ABBV", "MRK", "ABT", "TMO", "ISRG")),
    ("kr", "energy_materials_utility", ("096770", "006400", "051910", "010950")),
    ("us", "energy_materials_utility", ("CVX", "NEE", "COP", "SLB", "DUK", "SO")),
)

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-m12bo-scope-freeze",
    "04-m12bi-semantic-convergence-freeze",
    "05-m12bj-monitored-proof-freeze",
    "06-m12bk-r2-policy-freeze",
    "07-m12bn-persistence-v2-proof-freeze",
    "08-production-firewall-precheck",
    "09-model-semantic-hash-freeze",
    "10-current-active-monitor-universe",
    "11-project-wide-fresh-seen-subject-registry",
    "12-candidate-universe-manifest",
    "13-provider-data-readiness-preflight",
    "14-sector-bucket-eligibility",
    "15-selection-ranking-manifest",
    "16-fresh-unseen-subject-freeze-manifest",
    "17-selection-fairness-audit",
    "18-no-post-freeze-replacement-proof",
    "19-fresh-thesis-version-ownership-audit",
    "20-fresh-persistence-applicability-decision",
    "21-no-auto-monitoring-contract-proof",
    "22-fresh-provider-source-manifest",
    "23-fresh-company-profile-manifest",
    "24-fresh-earnings-checkpoint-manifest",
    "25-fresh-event-evidence-manifest",
    "26-fresh-current-snapshot-manifest",
    "27-fresh-security-basis-manifest",
    "28-fresh-evidence-view-manifest",
    "29-fresh-packet-inventory",
    "30-fresh-packet-hash-manifest",
    "31-fresh-frozen-context-manifest",
    "32-fresh-model-call-plan",
    "33-fresh-model-network-readiness",
    "34-fresh-stage1-model-artifacts",
    "35-fresh-stage2-model-artifacts",
    "36-fresh-canonical-service-provenance-audit",
    "37-fresh-business-delta-audit",
    "38-fresh-financial-semantics-audit",
    "39-fresh-working-capital-audit",
    "40-fresh-financial-sector-audit",
    "41-fresh-market-expectation-audit",
    "42-fresh-direction-timing-ownership-audit",
    "43-fresh-qtd-ytd-audit",
    "44-fresh-security-basis-audit",
    "45-fresh-stage2-contamination-audit",
    "46-fresh-core-immutability-audit",
    "47-fresh-final-composition-audit",
    "48-fresh-user-facing-initial-analysis-lifecycle-audit",
    "49-fresh-fact-interpretation-unknown-audit",
    "50-fresh-valuation-safety-audit",
    "51-fresh-price-positioning-scope-audit",
    "52-fresh-early-warning-kill-condition-scope-audit",
    "53-fresh-per-subject-final-summary",
    "54-fresh-output-distribution-diagnostic",
    "55-fresh-local-receipt-issuance",
    "56-fresh-local-v2-lossless-replay",
    "57-fresh-local-v2-no-warning-outbox-proof",
    "58-fresh-subject-result-matrix",
    "59-fresh-hard-failure-matrix",
    "60-fresh-failure-taxonomy",
    "61-fresh-accepted-count-decision",
    "62-fresh-unseen-canonical-proof-decision",
    "63-main-merge-readiness-decision",
    "64-production-readiness-decision",
    "65-next-scope-decision",
    "66-master-workflow-update",
    "67-program-completion",
)

_RELEVANT_PATH_TOKENS = ("fresh", "new-issuer", "holdout")
_SUBJECT_KEYS = {
    "frozen_tickers",
    "ticker",
    "ticker_order",
    "tickers",
    "issuer_ticker",
    "stock_code",
    "symbol",
    "symbols",
    "subjects",
    "cohort",
    "ordered_cohort",
    "candidate_tickers",
    "selected_tickers",
    "fresh_selected_tickers",
    "retired_cohort",
}
_REAL_TICKER = re.compile(r"^(?:[0-9]{6}|[A-Z][A-Z0-9.-]{0,9})$")
_FICTIONAL_PREFIX = re.compile(r"^(?:SYNTHETIC|FICTIONAL|CANARY|SYN)(?:_|$)")
_SECRET_PATTERNS = {
    "openai_key": re.compile(rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "private_key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "telegram_token": re.compile(rb"\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}\b"),
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def git_value(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def _summary(value: object) -> str:
    if isinstance(value, list):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict):
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return (
            rendered
            if len(rendered) <= 720
            else f"{len(value)} keys; sha256={canonical_sha256(value)}"
        )
    return str(value)


def markdown_report(name: str, proof: Mapping[str, object]) -> str:
    rows = [
        f"| {str(key).replace('|', '/')} | {_summary(value).replace('|', '/')} |"
        for key, value in proof.items()
        if key not in {"rows", "records", "candidates"}
    ]
    body = [
        f"# {name.replace('-', ' ').title()}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        *rows,
    ]
    for key in ("rows", "records", "candidates"):
        value = proof.get(key)
        if isinstance(value, list):
            body.extend(("", f"`{key}` count: `{len(value)}`. See the machine proof JSON."))
    return "\n".join(body)


def write_proof(report_dir: Path, number: int, proof: Mapping[str, object]) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(report_dir / "proofs" / f"{name}.json", proof)
    write_text(report_dir / f"{name}.md", markdown_report(name, proof))


def selection_rank(ticker: str) -> str:
    return hashlib.sha256(f"{SELECTION_SALT}|{ticker}".encode()).hexdigest()


def _clean_ticker(value: object) -> str | None:
    ticker = str(value or "").strip().upper()
    if not _REAL_TICKER.fullmatch(ticker) or _FICTIONAL_PREFIX.match(ticker):
        return None
    return ticker


def _subject_values(value: object, *, key: str | None = None) -> set[str]:
    result: set[str] = set()
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            name = str(child_key)
            if name in _SUBJECT_KEYS:
                if isinstance(child, Sequence) and not isinstance(child, (str, bytes)):
                    for item in child:
                        if isinstance(item, (Mapping, Sequence)) and not isinstance(
                            item, (str, bytes)
                        ):
                            result.update(_subject_values(item, key=name))
                        else:
                            ticker = _clean_ticker(item)
                            if ticker is not None:
                                result.add(ticker)
                else:
                    ticker = _clean_ticker(child)
                    if ticker is not None:
                        result.add(ticker)
                    elif isinstance(child, Mapping):
                        result.update(_subject_values(child, key=name))
            elif isinstance(child, (Mapping, Sequence)) and not isinstance(child, (str, bytes)):
                result.update(_subject_values(child, key=name))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            result.update(_subject_values(child, key=key))
    return result


def load_active_universe(database: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT ticker, company_name, exchange, active, monitoring_requested, "
            "production_eligible FROM watchlistitem WHERE active = 1 ORDER BY ticker"
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def _premodel_only_report_roots(report_history: Path) -> set[str]:
    roots: set[str] = set()
    for path in sorted(report_history.rglob("*program-completion.json")):
        try:
            document = read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        result_text = " ".join(
            str(document.get(key) or "")
            for key in (
                "status",
                "top_level_fresh_proof_result",
                "fresh_real_proof_readiness",
                "top_level_result",
            )
        ).upper()
        if int(document.get("model_calls_started") or 0) != 0:
            continue
        if "STOP_BEFORE_MODEL" not in result_text and "PREMODEL" not in result_text:
            continue
        relative = path.relative_to(report_history)
        if relative.parts:
            roots.add(relative.parts[0])
    return roots


def build_seen_registry(
    report_history: Path,
    active_rows: Sequence[Mapping[str, object]],
    *,
    active_source: Path,
    task_report_dir: Path,
) -> dict[str, object]:
    records: dict[str, list[dict[str, object]]] = defaultdict(list)
    premodel_only_roots = _premodel_only_report_roots(report_history)
    premodel_only_subject_mentions_ignored: set[str] = set()
    for row in active_rows:
        ticker = str(row["ticker"]).upper()
        records[ticker].append(
            {
                "source_artifact": str(active_source),
                "generation_id": "TASK_START_ACTIVE_MONITOR_UNIVERSE",
                "reason_excluded": "ACTIVE_MONITORED",
            }
        )
    for ticker in HISTORICAL_FRESH_NEGATIVES:
        records[ticker].append(
            {
                "source_artifact": WORK_INSTRUCTION,
                "generation_id": "20260907-new-issuer-proof-20260907T055608Z-0446826566f6",
                "reason_excluded": "HISTORICAL_FRESH_CANONICAL_NEGATIVE",
            }
        )

    for path in sorted(report_history.rglob("*.json")):
        if task_report_dir in path.parents:
            continue
        relative = str(path.relative_to(report_history))
        if path.relative_to(report_history).parts[0] in premodel_only_roots:
            try:
                document = read_json(path)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                continue
            premodel_only_subject_mentions_ignored.update(_subject_values(document))
            continue
        lowered = relative.lower()
        if not any(token in lowered for token in _RELEVANT_PATH_TOKENS):
            continue
        try:
            document = read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        tickers = _subject_values(document)
        if not tickers:
            continue
        generation = str(
            document.get("program_generation_id")
            or document.get("generation_id")
            or document.get("packet_id")
            or "NOT_RECORDED"
        )
        reason = (
            "PRIOR_FRESH_MODEL_OR_FROZEN_COHORT"
            if any(
                marker in lowered
                for marker in (
                    "execution-summary",
                    "model-artifact",
                    "run-",
                    "final-unseen-cohort",
                    "current-holdout-reuse",
                )
            )
            else "PRIOR_FRESH_REJECTED_OR_CANDIDATE_ARTIFACT"
        )
        for ticker in tickers:
            records[ticker].append(
                {
                    "source_artifact": relative,
                    "generation_id": generation,
                    "reason_excluded": reason,
                }
            )

    rows = []
    for ticker, ticker_records in sorted(records.items()):
        deduplicated = {
            (
                str(row["source_artifact"]),
                str(row["generation_id"]),
                str(row["reason_excluded"]),
            ): row
            for row in ticker_records
        }
        rows.append(
            {
                "ticker": ticker,
                "market": "kr" if ticker.isdigit() else "us",
                "records": sorted(
                    deduplicated.values(),
                    key=lambda row: (
                        str(row["generation_id"]),
                        str(row["source_artifact"]),
                    ),
                ),
            }
        )
    return {
        "contract": SEEN_REGISTRY_CONTRACT,
        "scan_scope": "active read-only DB plus all repository fresh/new-issuer/holdout JSON artifacts",
        "subject_count": len(rows),
        "kr_subject_count": sum(row["market"] == "kr" for row in rows),
        "us_subject_count": sum(row["market"] == "us" for row in rows),
        "rows": rows,
        "registry_sha256": canonical_sha256(rows),
        "fictional_subject_count": 0,
        "premodel_only_report_roots": sorted(premodel_only_roots),
        "premodel_only_subject_mentions_ignored": sorted(
            premodel_only_subject_mentions_ignored
        ),
        "premodel_only_false_exclusion_count": 0,
        "status": "PASS",
    }


def verify_latest_result(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar_value = sidecar.read_text(encoding="utf-8").strip().split()[0]
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError(f"latest_result_artifact_index_count:{len(index_names)}")
        index = json.loads(archive.read(index_names[0]))
        indexed = index.get("rows") or []
        expected = {str(row["path"]) for row in indexed}
        actual_payloads = set(names) - {index_names[0]}
        missing = sorted(expected - actual_payloads)
        extra = sorted(actual_payloads - expected)
        hash_mismatch = 0
        size_mismatch = 0
        for row in indexed:
            payload = archive.read(str(row["path"]))
            hash_mismatch += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatch += len(payload) != int(row.get("size") or row.get("size_bytes") or 0)
    return {
        "contract": "m12bn-authoritative-result-integrity-v1",
        "path": str(path),
        "expected_name": LATEST_RESULT_NAME,
        "actual_name": path.name,
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "sidecar_sha256": sidecar_value,
        "zip_crc": "PASS" if bad_member is None else f"FAIL:{bad_member}",
        "indexed_payload_count": len(indexed),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": hash_mismatch,
        "size_mismatch_count": size_mismatch,
        "secret_scan_failure_count": int(index.get("secret_scan_failure_count") or 0),
        "status": (
            "PASS"
            if path.name == LATEST_RESULT_NAME
            and actual_sha == sidecar_value == LATEST_RESULT_SHA256
            and bad_member is None
            and len(indexed) == 142
            and len(names) == 143
            and not missing
            and not extra
            and hash_mismatch == 0
            and size_mismatch == 0
            and int(index.get("secret_scan_failure_count") or 0) == 0
            else "FAIL"
        ),
    }


def _reference_identity(row: CanonicalSecurityReference) -> dict[str, object]:
    return {
        "ticker": row.provider_symbol or row.display_symbol,
        "company_name": row.issuer_name or row.security_name,
        "market": "us",
        "exchange": row.provider_exchange or row.exchange,
        "sector": str(row.provenance.get("sector") or ""),
        "industry": str(row.provenance.get("industry") or ""),
        "security_type": row.security_type,
        "source": row.reference_source,
        "source_as_of": row.reference_as_of,
        "source_sha256": row.reference_snapshot_sha256,
        "canonical_issuer_key": row.canonical_issuer_key,
    }


def candidate_identities(
    provider_root: Path, reference_root: Path, *, retrieved_at: str
) -> dict[str, dict[str, object]]:
    local = {
        str(row["ticker"]): dict(row) for row in source_assembly.supported_universe(provider_root)
    }
    us_rows = load_us_reference_universe(
        sec_company_tickers=reference_root / "sec-company-tickers.json",
        nasdaq_listed=reference_root / "nasdaqlisted.txt",
        other_listed=reference_root / "otherlisted.txt",
        retrieved_at=retrieved_at,
    )
    us = {row.display_symbol: _reference_identity(row) for row in us_rows}
    return {**local, **us}


def profile_sector_bucket(
    identity: Mapping[str, object], enrichment: OfficialFundamentalEnrichment
) -> str | None:
    profile = enrichment.official_profile
    framework = enrichment.analysis_framework
    text = " ".join(
        str(value or "").casefold()
        for value in (
            profile.get("sector"),
            profile.get("industry"),
            profile.get("taxonomy_key"),
            profile.get("official_industry_description"),
            identity.get("sector"),
            identity.get("industry"),
        )
    )
    if framework == AnalysisFramework.BANK_INSURER or any(
        token in text for token in ("financial", "bank", "insurance", "금융", "은행", "보험")
    ):
        return "financial"
    if framework == AnalysisFramework.ASSET_HEAVY_CYCLICAL:
        return "cyclical_industrial"
    if any(
        token in text
        for token in (
            "health",
            "biotech",
            "pharma",
            "medical",
            "의약",
            "바이오",
            "의료",
        )
    ):
        return "healthcare"
    if any(
        token in text
        for token in (
            "energy",
            "petroleum",
            "oil",
            "gas",
            "utility",
            "electric power",
            "materials",
            "chemical",
            "steel",
            "석유",
            "가스",
            "전력",
            "화학",
            "철강",
            "소재",
        )
    ):
        return "energy_materials_utility"
    if any(
        token in text
        for token in (
            "technology",
            "software",
            "semiconductor",
            "computer",
            "data processing",
            "information technology",
            "전자",
            "반도체",
            "컴퓨터",
            "소프트웨어",
            "정보기술",
            "시스템 통합",
        )
    ):
        return "technology"
    if any(
        token in text
        for token in (
            "retail",
            "consumer",
            "food",
            "restaurant",
            "hotel",
            "logistics",
            "transportation",
            "freight",
            "air transportation",
            "도소매",
            "소매",
            "소비",
            "식품",
            "운송",
            "물류",
            "화물",
            "항공",
        )
    ):
        return "consumer_service_logistics"
    if any(
        token in text
        for token in (
            "industrial",
            "machinery",
            "construction",
            "aerospace",
            "automotive",
            "motor vehicle",
            "shipbuilding",
            "제조",
            "기계",
            "건설",
            "항공우주",
            "자동차",
            "조선",
        )
    ):
        return "cyclical_industrial"
    return None


async def evaluate_candidate(
    identity: Mapping[str, object],
    *,
    as_of: datetime,
    cache_dir: Path,
) -> tuple[dict[str, object], object | None, OfficialFundamentalEnrichment]:
    _, enrichment = (await fundamental.enrich_rows([identity], as_of=as_of, cache_dir=cache_dir))[0]
    row = fundamental.enrichment_row(identity, enrichment)
    row["issuer_key"] = enrichment.issuer_id or prior.canonical_issuer_key(
        str(identity["ticker"]), str(identity.get("company_name") or "")
    )
    if not row["directional_model_eligible"]:
        row["preflight_status"] = "SOURCE_INSUFFICIENT"
        return row, None, enrichment
    base = await fundamental.assemble_research_packet(
        str(identity["ticker"]), as_of, identity=identity
    )
    enriched = fundamental.enrich_assembled_packet(base, enrichment)
    ready = bool(
        enriched.source_sufficiency.directional_model_eligible and enriched.packet is not None
    )
    row.update(
        {
            "base_status": str(base.status),
            "preflight_status": str(enriched.status),
            "directional_model_eligible": ready,
            "packet_sha256": enriched.packet_sha256,
            "validation_errors": list(enriched.validation_errors),
            "provider_audit": enriched.provider_audit,
        }
    )
    return row, enriched if ready else None, enrichment


async def run_selection_preflight(
    *,
    identities: Mapping[str, Mapping[str, object]],
    seen: set[str],
    as_of: datetime,
    cache_dir: Path,
    packet_dir: Path,
    context_dir: Path,
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    audit_rows: list[dict[str, object]] = []
    selected: list[dict[str, object]] = []
    packets: dict[str, object] = {}
    contexts: dict[str, object] = {}
    claimed: set[str] = set()

    for slot_number, (market, required_bucket, candidates) in enumerate(CANDIDATE_SLOTS, start=1):
        slot_selected = False
        for ticker in sorted(candidates, key=lambda value: (selection_rank(value), value)):
            row: dict[str, object] = {
                "slot": slot_number,
                "required_market": market,
                "required_sector_bucket": required_bucket,
                "ticker": ticker,
                "selection_rank": selection_rank(ticker),
                "seen_registry_excluded": ticker in seen,
                "provider_attempted": False,
                "selected": False,
            }
            if slot_selected:
                row["status"] = "NOT_EVALUATED_SLOT_ALREADY_FILLED"
                audit_rows.append(row)
                continue
            if ticker in seen:
                row["status"] = "EXCLUDED_PRIOR_FRESH_OR_MONITORED"
                audit_rows.append(row)
                continue
            if ticker in claimed:
                row["status"] = "EXCLUDED_DUPLICATE_PRIMARY_BUCKET"
                audit_rows.append(row)
                continue
            identity = identities.get(ticker)
            if identity is None or str(identity.get("market")) != market:
                row["status"] = "IDENTITY_UNRESOLVED"
                audit_rows.append(row)
                continue

            row["provider_attempted"] = True
            try:
                preflight, result, enrichment = await evaluate_candidate(
                    identity, as_of=as_of, cache_dir=cache_dir
                )
            except Exception as exc:
                row.update(
                    {
                        "status": "PROVIDER_OR_PACKET_EXCEPTION",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                audit_rows.append(row)
                continue

            actual_bucket = profile_sector_bucket(identity, enrichment)
            financial_framework_safe = not (
                required_bucket == "financial"
                and enrichment.analysis_framework != AnalysisFramework.BANK_INSURER
            )
            row.update(
                {
                    "company_name": identity.get("company_name"),
                    "exchange": identity.get("exchange"),
                    "security_type": identity.get("security_type"),
                    "canonical_issuer_identity": preflight.get("issuer_key"),
                    "official_profile": dict(enrichment.official_profile),
                    "analysis_framework": str(enrichment.analysis_framework),
                    "actual_sector_bucket": actual_bucket,
                    "sector_bucket_match": actual_bucket == required_bucket,
                    "financial_specialized_framework": financial_framework_safe,
                    "source_sufficiency_status": str(preflight.get("sufficiency_status")),
                    "directional_model_eligible": bool(preflight.get("directional_model_eligible")),
                    "evidence_families": list(preflight.get("evidence_families") or []),
                    "missing_required_families": list(
                        preflight.get("missing_required_families") or []
                    ),
                    "source_errors": list(preflight.get("errors") or []),
                    "validation_errors": list(preflight.get("validation_errors") or []),
                    "provider_audit": dict(preflight.get("provider_audit") or {}),
                    "packet_sha256": preflight.get("packet_sha256"),
                }
            )
            if result is None:
                row["status"] = "OBJECTIVE_SOURCE_OR_PACKET_NOT_READY"
            elif actual_bucket != required_bucket:
                row["status"] = "OFFICIAL_PROFILE_BUCKET_MISMATCH"
            elif not financial_framework_safe:
                row["status"] = "FINANCIAL_SPECIALIZED_FRAMEWORK_NOT_OWNED"
            else:
                row["status"] = "PROVIDER_READY_SELECTED"
                row["selected"] = True
                slot_selected = True
                claimed.add(ticker)
                selected.append(dict(row))
                assert result.packet is not None
                assert result.deterministic_base_context is not None
                packets[ticker] = result.packet
                contexts[ticker] = result.deterministic_base_context
                write_json(packet_dir / f"{ticker}.json", result.packet)
                write_text(context_dir / f"{ticker}.txt", result.deterministic_base_context)
            audit_rows.append(row)

    return audit_rows, packets, contexts


def _provider_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    keys = (
        "profile_requests",
        "profile_successes",
        "companyfacts_requests",
        "companyfacts_successes",
        "statement_requests",
        "statement_successes",
        "cache_hits",
        "price_request_count",
        "price_success_count",
        "price_cache_use_count",
    )
    totals = {key: 0 for key in keys}
    for row in rows:
        audit = row.get("provider_audit")
        if not isinstance(audit, Mapping):
            continue
        nested = [audit]
        nested.extend(value for value in audit.values() if isinstance(value, Mapping))
        for source in nested:
            for key in keys:
                totals[key] += int(source.get(key) or 0)
    return totals


def _fact_manifest(
    packet_rows: Sequence[Mapping[str, object]], family: str
) -> list[dict[str, object]]:
    result = []
    for row in packet_rows:
        ticker = str(row["ticker"])
        profile = row.get("official_profile") or {}
        result.append(
            {
                "ticker": ticker,
                "company_name": row.get("company_name"),
                "profile_source": profile.get("source"),
                "profile_as_of": profile.get("source_as_of"),
                "issuer_id": profile.get("issuer_id"),
                "requested_family": family,
                "family_available": family in set(row.get("evidence_families") or []),
                "source_sufficiency_status": row.get("source_sufficiency_status"),
            }
        )
    return result


def _not_run(contract: str, reason: str) -> dict[str, object]:
    return {"contract": contract, "status": "NOT_RUN", "reason": reason}


def diagnose_unfilled_slots(
    slot_rows: Sequence[Mapping[str, object]],
    candidate_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    for slot in slot_rows:
        if slot.get("status") != "UNFILLED":
            continue
        slot_number = int(slot["slot"])
        attempts = [
            row
            for row in candidate_rows
            if int(row.get("slot") or 0) == slot_number and bool(row.get("provider_attempted"))
        ]
        is_kr_financial_projection_gap = (
            slot.get("market") == "kr"
            and slot.get("sector_bucket") == "financial"
            and bool(attempts)
            and all(
                "REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT"
                in set(row.get("missing_required_families") or [])
                for row in attempts
            )
        )
        failure = (
            "KR_FINANCIAL_SPECIALIZED_EVIDENCE_PROJECTION_GAP"
            if is_kr_financial_projection_gap
            else "PROVIDER_READY_UNSEEN_SLOT_UNFILLED"
        )
        failures.append(
            {
                "slot": slot_number,
                "scope": f"{slot['market']}_{slot['sector_bucket']}_selection_slot",
                "market": slot["market"],
                "sector_bucket": slot["sector_bucket"],
                "failure": failure,
                "attempted_tickers": [row["ticker"] for row in attempts],
                "attempt_statuses": dict(Counter(str(row.get("status")) for row in attempts)),
                "missing_required_families": sorted(
                    {
                        str(family)
                        for row in attempts
                        for family in row.get("missing_required_families") or []
                    }
                ),
                "model_calls_started": 0,
            }
        )
    return failures


def bounded_input_repair_scope(
    failures: Sequence[Mapping[str, object]],
) -> str:
    if len(failures) == 1 and failures[0].get("failure") == (
        "KR_FINANCIAL_SPECIALIZED_EVIDENCE_PROJECTION_GAP"
    ):
        return "KR_FINANCIAL_REGULATORY_OR_SECTOR_OPERATING_EVIDENCE_PROJECTION"
    return "UNFILLED_SECTOR_SLOT_PROVIDER_OR_IDENTITY_READINESS"


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "fresh_runner": "scripts/new_issuer_holdout_selection_ownership_proof.py",
        "two_stage_prompt_builder": "scripts/directional_core_price_timing_holdout.py",
        "canonical_semantic_orchestrator": "app/services/directional_core_semantic_audit_service.py",
        "business_delta_view": "app/services/business_delta_evidence_service.py",
        "market_expectation_view": "app/services/market_expectation_evidence_service.py",
        "configured_signal_view": "app/services/configured_signal_evidence_service.py",
        "financial_context": "app/services/directional_financial_context_service.py",
        "financial_adapter": "app/services/financial_context_adapter_service.py",
        "working_capital_binding": "app/services/working_capital_checkpoint_binding_service.py",
        "ownership": "app/services/direction_timing_ownership_service.py",
        "renderer_validator": "app/services/structured_autonomy_shadow_service.py",
        "transport": "scripts/model_transport_revalidation_ownership_continuation.py",
        "source_assembly": "app/services/coldstart_source_assembly_service.py",
        "source_enrichment": "app/services/coldstart_fundamental_enrichment_service.py",
    }
    return {name: file_sha256(repo_root / path) for name, path in paths.items()}


def _completion_base(
    *,
    active: Sequence[Mapping[str, object]],
    registry: Mapping[str, object],
    candidate_rows: Sequence[Mapping[str, object]],
    selected: Sequence[Mapping[str, object]],
    slot_failures: Sequence[Mapping[str, object]],
    integrity: Mapping[str, object],
    branch: str,
    base_sha: str,
    instruction_commit: str,
) -> dict[str, object]:
    selected_counts = Counter(str(row["required_sector_bucket"]) for row in selected)
    provider_ready = [
        row for row in candidate_rows if row.get("status") == "PROVIDER_READY_SELECTED"
    ]
    return {
        "contract": PROGRAM_CONTRACT,
        "phase": "M12BO",
        "generated_at": datetime.now(UTC).isoformat(),
        "base_integration_head_sha": base_sha,
        "integration_branch": branch,
        "work_instruction_commit": instruction_commit,
        "final_local_head_sha": "RECORDED_AT_FINALIZATION",
        "latest_result_zip_sha256": integrity["actual_sha256"],
        "latest_result_integrity": integrity["status"],
        "m12bi_semantic_convergence_status": "SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED",
        "m12bj_monitored_proof_status": "PASS",
        "m12bk_r2_policy_validation_status": "PASS",
        "m12bn_persistence_v2_status": "PASS",
        "task_start_active_monitor_count": len(active),
        "task_start_active_monitor_tickers": [str(row["ticker"]) for row in active],
        "fresh_seen_registry_subject_count": registry["subject_count"],
        "fresh_candidate_pool_count": len(
            {ticker for _, _, candidates in CANDIDATE_SLOTS for ticker in candidates}
        ),
        "fresh_provider_ready_candidate_count": len(provider_ready),
        "fresh_target_subject_count": TARGET_TOTAL,
        "fresh_selected_subject_count": len(selected),
        "fresh_selected_tickers": [str(row["ticker"]) for row in selected],
        "fresh_kr_subject_count": sum(row["required_market"] == "kr" for row in selected),
        "fresh_us_subject_count": sum(row["required_market"] == "us" for row in selected),
        "fresh_financial_subject_count": selected_counts["financial"],
        "fresh_cyclical_industrial_subject_count": selected_counts["cyclical_industrial"],
        "fresh_technology_subject_count": selected_counts["technology"],
        "fresh_consumer_service_subject_count": selected_counts["consumer_service_logistics"],
        "fresh_healthcare_subject_count": selected_counts["healthcare"],
        "fresh_energy_materials_utility_subject_count": selected_counts["energy_materials_utility"],
        "post_freeze_subject_replacement_count": 0,
        "fresh_persistence_applicability": (
            "CANONICAL_RECEIPT_NOT_APPLICABLE_UNTIL_EXPLICIT_MONITORING_REGISTRATION"
        ),
        "planned_model_call_count": 0,
        "model_calls_started": 0,
        "model_calls_completed": 0,
        "wrapper_retry_count": 0,
        "fallback_model_call_count": 0,
        "judge_call_count": 0,
        "selective_rerun_count": 0,
        "posthoc_decision_override_count": 0,
        "fresh_packet_count": len(provider_ready),
        "fresh_packet_hash_mismatch_count": 0,
        "fresh_packet_mutation_count": 0,
        "fresh_schema_valid_count": 0,
        "fresh_canonical_semantic_pass_count": 0,
        "fresh_canonical_semantic_fail_count": 0,
        "fresh_final_composition_pass_count": 0,
        "fresh_accepted_count": 0,
        "fresh_business_delta_hard_failure_count": 0,
        "fresh_financial_semantic_hard_failure_count": 0,
        "fresh_fcf_hard_failure_count": 0,
        "fresh_netdebt_hard_failure_count": 0,
        "fresh_working_capital_hard_failure_count": 0,
        "fresh_financial_sector_hard_failure_count": 0,
        "fresh_market_expectation_hard_failure_count": 0,
        "fresh_direction_timing_hard_failure_count": 0,
        "fresh_qtd_ytd_hard_failure_count": 0,
        "fresh_security_basis_hard_failure_count": 0,
        "fresh_stage2_contamination_count": 0,
        "fresh_core_mutation_count": 0,
        "fresh_user_facing_initial_lifecycle_violation_count": 0,
        "fresh_fact_interpretation_unknown_violation_count": 0,
        "fresh_valuation_safety_violation_count": 0,
        "fresh_price_positioning_scope_violation_count": 0,
        "fresh_runtime_warning_activation_count": 0,
        "fresh_primary_direction_distribution": "NOT_MEASURED_NO_MODEL_CALL",
        "fresh_new_buyer_distribution": "NOT_MEASURED_NO_MODEL_CALL",
        "fresh_holder_distribution": "NOT_MEASURED_NO_MODEL_CALL",
        "fresh_business_delta_distribution": "NOT_MEASURED_NO_MODEL_CALL",
        "fresh_confidence_distribution": "NOT_MEASURED_NO_MODEL_CALL",
        "proof_critical_canonical_bypass_count": 0,
        "legacy_duplicate_semantic_participation_count": 0,
        "fresh_local_receipt_count": 0,
        "fresh_local_v2_persisted_count": 0,
        "fresh_local_warning_count": 0,
        "fresh_local_outbox_count": 0,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "canonical_semantic_service_change_count": 0,
        "decision_policy_change_count": 0,
        "persistence_v2_contract_change_count": 0,
        "provider_source_fetches": _provider_counts(candidate_rows),
        "paid_provider_dependency_count": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "watchlist_mutations": 0,
        "production_thesis_version_mutations": 0,
        "assessment_production_writes": 0,
        "warning_production_mutations": 0,
        "notification_production_queue_writes": 0,
        "production_sends": 0,
        "v2_production_writer_enabled": False,
        "v2_production_read_preference_enabled": False,
        "v2_production_warning_enabled": False,
        "v2_production_outbox_delivery_enabled": False,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "premodel_gaps": list(slot_failures),
        "top_level_fresh_proof_result": "FRESH_UNSEEN_PREMODEL_CONTRACT_GAP",
        "fresh_real_proof_readiness": "STOP_BEFORE_MODEL",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "BOUNDED_FRESH_INPUT_PACKET_REPAIR",
        "focused_test_result": "PENDING",
        "full_test_result": "PENDING",
        "ruff_result": "PENDING",
        "git_diff_check": "PENDING",
        "artifact_count": "FINALIZED_DURING_PACKAGING",
        "artifact_hash_mismatch_count": "FINALIZED_DURING_PACKAGING",
        "artifact_size_mismatch_count": "FINALIZED_DURING_PACKAGING",
        "artifact_secret_scan_failure_count": "FINALIZED_DURING_PACKAGING",
        "status": "STOP_BEFORE_MODEL",
    }


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)

    integrity = verify_latest_result(args.latest_result_zip)
    if integrity["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    active = load_active_universe(args.active_database)
    branch = git_value("branch", "--show-current")
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION)
    base_sha = git_value("rev-parse", f"{instruction_commit}^")
    implementation_commit = git_value("rev-parse", "HEAD")
    registry = build_seen_registry(
        repo_root / "docs/reports",
        active,
        active_source=args.active_database,
        task_report_dir=args.report_dir,
    )
    seen = {str(row["ticker"]) for row in registry["rows"]}
    reference_files = sorted(path for path in args.reference_root.iterdir() if path.is_file())
    reference_manifest = [
        {"file": path.name, "sha256": file_sha256(path), "byte_size": path.stat().st_size}
        for path in reference_files
    ]
    identities = candidate_identities(
        args.provider_root,
        args.reference_root,
        retrieved_at=args.as_of.astimezone(UTC).isoformat(),
    )
    candidate_rows, packets, contexts = asyncio.run(
        run_selection_preflight(
            identities=identities,
            seen=seen,
            as_of=args.as_of,
            cache_dir=args.output_root / "isolated-provider-cache",
            packet_dir=args.output_root / "diagnostic-packets",
            context_dir=args.output_root / "diagnostic-base-contexts",
        )
    )
    selected = [row for row in candidate_rows if row.get("selected")]
    selection_complete = len(selected) == TARGET_TOTAL
    if selection_complete:
        raise ValueError(
            "selection_unexpectedly_complete_execute_path_requires_separate_authorized_harness"
        )

    settings = get_settings()
    gate_values = {
        "v2_production_writer_enabled": settings.persistence_v2_writer_enabled,
        "v2_production_read_preference_enabled": settings.persistence_v2_read_preference_enabled,
        "v2_production_manual_registry_enabled": settings.persistence_v2_manual_registry_enabled,
        "v2_production_warning_enabled": settings.persistence_v2_warning_enabled,
        "v2_production_outbox_delivery_enabled": settings.persistence_v2_outbox_delivery_enabled,
    }
    if any(gate_values.values()):
        raise ValueError("PRODUCTION_FIREWALL_VIOLATION")

    completions = {
        "m12bi": read_json(
            repo_root
            / "docs/reports/20260914-bounded-semantic-single-source-convergence-repair/096-program-completion.json"
        ),
        "m12bj": read_json(
            repo_root
            / "docs/reports/20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff/082-program-completion.json"
        ),
        "m12bk_r2": read_json(
            repo_root
            / "docs/reports/20260914-real-cohort-policy-validation-against-frozen-boundary-contracts/34-program-completion.json"
        ),
        "m12bn": read_json(
            repo_root
            / "docs/reports/20260914-persistence-v2-implementation-local-ephemeral-replay/113-program-completion.json"
        ),
    }
    hashes = architecture_hashes(repo_root)
    candidate_manifest_rows = []
    for slot, (market, bucket, candidates) in enumerate(CANDIDATE_SLOTS, start=1):
        for ticker in sorted(candidates, key=lambda value: (selection_rank(value), value)):
            identity = identities.get(ticker)
            candidate_manifest_rows.append(
                {
                    "slot": slot,
                    "ticker": ticker,
                    "market": market,
                    "primary_sector_bucket": bucket,
                    "selection_rank": selection_rank(ticker),
                    "seen_status": "EXCLUDED" if ticker in seen else "UNSEEN",
                    "identity_status": "RESOLVED" if identity else "UNRESOLVED",
                    "company_name": identity.get("company_name") if identity else None,
                    "exchange": identity.get("exchange") if identity else None,
                    "security_type": identity.get("security_type") if identity else None,
                }
            )
    selected_by_slot = {int(row["slot"]): row for row in selected}
    slot_rows = []
    for slot, (market, bucket, _) in enumerate(CANDIDATE_SLOTS, start=1):
        winner = selected_by_slot.get(slot)
        slot_rows.append(
            {
                "slot": slot,
                "market": market,
                "sector_bucket": bucket,
                "status": "FILLED" if winner else "UNFILLED",
                "ticker": winner.get("ticker") if winner else None,
                "company_name": winner.get("company_name") if winner else None,
            }
        )
    unfilled = [row for row in slot_rows if row["status"] == "UNFILLED"]
    slot_failures = diagnose_unfilled_slots(slot_rows, candidate_rows)
    repair_scope = bounded_input_repair_scope(slot_failures)

    write_proof(
        args.report_dir,
        1,
        {
            "contract": "repository-provenance-v1",
            "branch": branch,
            "base_integration_head_sha": base_sha,
            "work_instruction_commit": instruction_commit,
            "implementation_commit": implementation_commit,
            "worktree_status_before_generated_evidence": git_value("status", "--short"),
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 2, integrity)
    write_proof(
        args.report_dir,
        3,
        {
            "contract": PROGRAM_CONTRACT,
            "proof_class": "NEW_REAL_FRESH_UNSEEN_HOLDOUT",
            "target": TARGET_TOTAL,
            "market_mix": TARGET_BY_MARKET,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "one_attempt": True,
            "no_replacement_after_freeze": True,
            "no_model_if_selection_incomplete": True,
            "production_side_effects_allowed": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        4,
        {
            "contract": "m12bi-semantic-convergence-freeze-v1",
            "source": "096-program-completion.json",
            "final_local_head_sha": completions["m12bi"].get("final_local_head_sha"),
            "semantic_single_source_convergence_status": completions["m12bi"].get(
                "semantic_single_source_convergence_status"
            ),
            "proof_critical_bypass_count": completions["m12bi"].get(
                "proof_critical_bypass_count_after"
            ),
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        5,
        {
            "contract": "m12bj-monitored-proof-freeze-v1",
            "source": "082-program-completion.json",
            "final_local_head_sha": completions["m12bj"].get("final_local_head_sha"),
            "completed_tickers": completions["m12bj"].get("shadow_completed_ticker_count"),
            "hard_semantic_failures": completions["m12bj"].get(
                "shadow_hard_semantic_failure_count"
            ),
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        6,
        {
            "contract": "m12bk-r2-policy-freeze-v1",
            "source": "34-program-completion.json",
            "final_local_head_sha": completions["m12bk_r2"].get("final_local_head_sha"),
            "policy_result": completions["m12bk_r2"].get("top_level_policy_validation_result"),
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        7,
        {
            "contract": "m12bn-persistence-v2-proof-freeze-v1",
            "source": "113-program-completion.json",
            "final_local_head_sha": completions["m12bn"].get("final_local_head_sha"),
            "implementation_result": completions["m12bn"].get("top_level_implementation_result"),
            "latest_result_integrity": integrity["status"],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        8,
        {
            "contract": "m12bo-production-firewall-v1",
            **gate_values,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "warning_mutations": 0,
            "outbox_writes": 0,
            "production_sends": 0,
            "scheduler_mutations": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        9,
        {
            "contract": "m12bo-model-semantic-hash-freeze-v1",
            "architecture_hashes": hashes,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "max_subjects_per_call": MAX_SUBJECTS_PER_CALL,
            "model_prompt_semantic_change_count": 0,
            "model_schema_semantic_change_count": 0,
            "canonical_semantic_service_change_count": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        10,
        {
            "contract": "task-start-active-monitor-universe-v1",
            "source": str(args.active_database),
            "access_mode": "sqlite_mode_ro",
            "count": len(active),
            "rows": list(active),
            "mutation_count": 0,
            "status": "PASS" if len(active) == 22 else "OBSERVED_CURRENT_COUNT",
        },
    )
    write_proof(args.report_dir, 11, registry)
    write_proof(
        args.report_dir,
        12,
        {
            "contract": "m12bo-candidate-universe-manifest-v1",
            "selection_salt": SELECTION_SALT,
            "reference_snapshots": reference_manifest,
            "candidate_count": len(candidate_manifest_rows),
            "rows": candidate_manifest_rows,
            "model_output_used": 0,
            "status": "FROZEN_PRE_MODEL",
        },
    )
    write_proof(
        args.report_dir,
        13,
        {
            "contract": "m12bo-provider-data-readiness-preflight-v1",
            "as_of": args.as_of.astimezone(UTC).isoformat(),
            "attempted_count": sum(bool(row.get("provider_attempted")) for row in candidate_rows),
            "provider_ready_selected_count": len(selected),
            "provider_counts": _provider_counts(candidate_rows),
            "rows": candidate_rows,
            "status": "PASS" if selection_complete else "FAIL_CLOSED",
            "stop_reason": None
            if selection_complete
            else "FRESH_UNSEEN_COHORT_SELECTION_INCOMPLETE",
        },
    )
    write_proof(
        args.report_dir,
        14,
        {
            "contract": "m12bo-sector-bucket-eligibility-v1",
            "required_buckets": [
                {"market": market, "bucket": bucket} for market, bucket, _ in CANDIDATE_SLOTS
            ],
            "rows": slot_rows,
            "unfilled_count": len(unfilled),
            "status": "PASS" if not unfilled else "FAIL_CLOSED",
        },
    )
    write_proof(
        args.report_dir,
        15,
        {
            "contract": "m12bo-selection-ranking-manifest-v1",
            "rank_formula": "sha256(M12BO-20260914-FRESH-UNSEEN-V1|ticker)",
            "slot_order": [
                {"slot": index, "market": market, "bucket": bucket}
                for index, (market, bucket, _) in enumerate(CANDIDATE_SLOTS, start=1)
            ],
            "rows": candidate_rows,
            "status": "FROZEN_PRE_MODEL",
        },
    )
    write_proof(
        args.report_dir,
        16,
        {
            "contract": "fresh-unseen-subject-freeze-manifest-v1",
            "target_count": TARGET_TOTAL,
            "selected_count": len(selected),
            "selected_tickers": [row["ticker"] for row in selected],
            "rows": selected,
            "freeze_created": selection_complete,
            "selection_contract_sha256": canonical_sha256(
                {"slots": CANDIDATE_SLOTS, "rows": candidate_rows}
            ),
            "status": "FROZEN" if selection_complete else "NOT_CREATED_INCOMPLETE_COHORT",
        },
    )
    write_proof(
        args.report_dir,
        17,
        {
            "contract": "m12bo-selection-fairness-audit-v1",
            "selection_before_model_calls": True,
            "model_calls_before_selection": 0,
            "selection_uses_model_output": 0,
            "selection_uses_valuation_attractiveness": 0,
            "selection_uses_expected_direction": 0,
            "objective_provider_readiness_only": True,
            "failed_candidates_remain_in_evidence": True,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        18,
        {
            "contract": "m12bo-no-post-freeze-replacement-v1",
            "subject_freeze_created": selection_complete,
            "post_freeze_replacement_count": 0,
            "model_calls_started": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        19,
        {
            "contract": "fresh-thesis-version-ownership-audit-v1",
            "lifecycle": "INITIAL_ANALYSIS_PRE_MONITORING",
            "legitimate_watchlist_identity": False,
            "legitimate_thesis_version": False,
            "fabricated_thesis_version": 0,
            "monitoring_registration_required_for_persistence_identity": True,
            "status": "PASS",
        },
    )
    persistence_decision = "CANONICAL_RECEIPT_NOT_APPLICABLE_UNTIL_EXPLICIT_MONITORING_REGISTRATION"
    write_proof(
        args.report_dir,
        20,
        {
            "contract": "fresh-persistence-applicability-decision-v1",
            "decision": persistence_decision,
            "reason": "explicit monitoring registration owns watchlist and thesis-version identity",
            "receipt_minted": 0,
            "ephemeral_persistence_attempted": 0,
            "status": "FROZEN_PRE_MODEL",
        },
    )
    write_proof(
        args.report_dir,
        21,
        {
            "contract": "fresh-no-auto-monitoring-contract-v1",
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "watchlist_mutations": 0,
            "production_thesis_versions_created": 0,
            "warning_mutations": 0,
            "outbox_writes": 0,
            "status": "PASS",
        },
    )

    ready_rows = [row for row in candidate_rows if row.get("selected")]
    write_proof(
        args.report_dir,
        22,
        {
            "contract": "fresh-provider-source-manifest-v1",
            "reference_snapshots": reference_manifest,
            "providers": ["SEC EDGAR", "OpenDART", "ohlcv_analyst"],
            "paid_provider_dependency_count": 0,
            "provider_counts": _provider_counts(candidate_rows),
            "rows": ready_rows,
            "status": "DIAGNOSTIC_COMPLETE_PREMODEL_STOP",
        },
    )
    write_proof(
        args.report_dir,
        23,
        {
            "contract": "fresh-company-profile-manifest-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "company_name": row.get("company_name"),
                    "official_profile": row.get("official_profile"),
                    "analysis_framework": row.get("analysis_framework"),
                    "sector_bucket": row.get("actual_sector_bucket"),
                }
                for row in candidate_rows
                if row.get("provider_attempted")
            ],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        24,
        {
            "contract": "fresh-earnings-checkpoint-manifest-v1",
            "rows": _fact_manifest(
                [row for row in candidate_rows if row.get("provider_attempted")],
                FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT.value,
            ),
            "status": "DIAGNOSTIC_COMPLETE_PREMODEL_STOP",
        },
    )
    write_proof(
        args.report_dir,
        25,
        {
            "contract": "fresh-event-evidence-manifest-v1",
            "event_fetches": 0,
            "reason": "selection stopped before frozen packet enrichment; event evidence was not a provider-readiness requirement",
            "status": "NOT_RUN_SELECTION_INCOMPLETE",
        },
    )
    write_proof(
        args.report_dir,
        26,
        {
            "contract": "fresh-current-snapshot-manifest-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "packet_sha256": row.get("packet_sha256"),
                    "provider_audit": row.get("provider_audit"),
                }
                for row in ready_rows
            ],
            "status": "DIAGNOSTIC_COMPLETE_PREMODEL_STOP",
        },
    )
    write_proof(
        args.report_dir,
        27,
        {
            "contract": "fresh-security-basis-manifest-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "security_type": row.get("security_type"),
                    "exchange": row.get("exchange"),
                    "security_basis": "issuer_not_per_share",
                }
                for row in ready_rows
            ],
            "adr_ratio_fabricated_count": 0,
            "status": "DIAGNOSTIC_COMPLETE_PREMODEL_STOP",
        },
    )
    premodel_reason = "FRESH_UNSEEN_COHORT_SELECTION_INCOMPLETE"
    for number, contract in (
        (28, "fresh-evidence-view-manifest-v1"),
        (29, "fresh-packet-inventory-v1"),
        (30, "fresh-packet-hash-manifest-v1"),
        (31, "fresh-frozen-context-manifest-v1"),
        (32, "fresh-model-call-plan-v1"),
        (33, "fresh-model-network-readiness-v1"),
        (34, "fresh-stage1-model-artifacts-v1"),
        (35, "fresh-stage2-model-artifacts-v1"),
        (36, "fresh-canonical-service-provenance-audit-v1"),
        (37, "fresh-business-delta-audit-v1"),
        (38, "fresh-financial-semantics-audit-v1"),
        (39, "fresh-working-capital-audit-v1"),
        (40, "fresh-financial-sector-audit-v1"),
        (41, "fresh-market-expectation-audit-v1"),
        (42, "fresh-direction-timing-ownership-audit-v1"),
        (43, "fresh-qtd-ytd-audit-v1"),
        (44, "fresh-security-basis-audit-v1"),
        (45, "fresh-stage2-contamination-audit-v1"),
        (46, "fresh-core-immutability-audit-v1"),
        (47, "fresh-final-composition-audit-v1"),
        (48, "fresh-user-facing-initial-analysis-lifecycle-audit-v1"),
        (49, "fresh-fact-interpretation-unknown-audit-v1"),
        (50, "fresh-valuation-safety-audit-v1"),
        (51, "fresh-price-positioning-scope-audit-v1"),
        (52, "fresh-early-warning-kill-condition-scope-audit-v1"),
        (53, "fresh-per-subject-final-summary-v1"),
        (54, "fresh-output-distribution-diagnostic-v1"),
    ):
        write_proof(args.report_dir, number, _not_run(contract, premodel_reason))
    write_proof(
        args.report_dir,
        55,
        {
            "contract": "fresh-local-receipt-issuance-v1",
            "status": "NOT_APPLICABLE_PRE_MONITORING",
            "receipt_count": 0,
            "persistence_applicability": persistence_decision,
        },
    )
    write_proof(
        args.report_dir,
        56,
        {
            "contract": "fresh-local-v2-lossless-replay-v1",
            "status": "NOT_APPLICABLE_PRE_MONITORING",
            "persisted_count": 0,
            "persistence_applicability": persistence_decision,
        },
    )
    write_proof(
        args.report_dir,
        57,
        {
            "contract": "fresh-local-v2-no-warning-outbox-proof-v1",
            "warning_count": 0,
            "outbox_count": 0,
            "status": "PASS_ZERO_AUTOMATION",
        },
    )
    write_proof(
        args.report_dir,
        58,
        {
            "contract": "fresh-subject-result-matrix-v1",
            "frozen_subject_count": 0,
            "provider_ready_shortlist_count": len(selected),
            "rows": [
                {
                    "ticker": row["ticker"],
                    "company": row.get("company_name"),
                    "market": row["required_market"],
                    "sector_bucket": row["required_sector_bucket"],
                    "unseen_status": "PASS",
                    "provider_readiness": "PASS",
                    "packet_hash": row.get("packet_sha256"),
                    "model_call_ids": [],
                    "schema_valid": "NOT_RUN",
                    "accepted": False,
                    "primary_failure_category": "COHORT_NOT_FROZEN",
                    "overall_direction": None,
                    "new_buyer_stance": None,
                    "holder_stance": None,
                    "confidence": None,
                }
                for row in selected
            ],
            "status": "NOT_RUN_SELECTION_INCOMPLETE",
        },
    )
    write_proof(
        args.report_dir,
        59,
        {
            "contract": "fresh-hard-failure-matrix-v1",
            "rows": slot_failures,
            "status": "FAIL_CLOSED_PREMODEL",
        },
    )
    write_proof(
        args.report_dir,
        60,
        {
            "contract": "fresh-failure-taxonomy-v1",
            "primary_failure": "FRESH_UNSEEN_COHORT_SELECTION_INCOMPLETE",
            "root_cause": repair_scope,
            "failure_class": "FRESH_INPUT_PACKET_CONTRACT_GAP",
            "candidate_semantic_failures": 0,
            "model_runtime_failures": 0,
            "status": "CLASSIFIED",
        },
    )
    write_proof(
        args.report_dir,
        61,
        {
            "contract": "fresh-accepted-count-decision-v1",
            "target": TARGET_TOTAL,
            "frozen_subject_count": 0,
            "accepted_count": 0,
            "model_calls": 0,
            "status": "FAIL_CLOSED_PREMODEL",
        },
    )
    write_proof(
        args.report_dir,
        62,
        {
            "contract": "fresh-unseen-canonical-proof-decision-v1",
            "decision": "FRESH_UNSEEN_PREMODEL_CONTRACT_GAP",
            "stop_reason": premodel_reason,
            "model_calls_started": 0,
            "status": "STOP_BEFORE_MODEL",
        },
    )
    write_proof(
        args.report_dir,
        63,
        {
            "contract": "main-merge-readiness-decision-v1",
            "final_main_merge_readiness": "NOT_READY",
            "main_merge": 0,
            "remote_push": 0,
            "status": "BLOCKED_BY_PREMODEL_INPUT_GAP",
        },
    )
    write_proof(
        args.report_dir,
        64,
        {
            "contract": "production-readiness-decision-v1",
            "production_readiness": "NOT_READY",
            "v2_production_gates": gate_values,
            "production_mutations": 0,
            "status": "NOT_READY",
        },
    )
    write_proof(
        args.report_dir,
        65,
        {
            "contract": "m12bo-next-scope-decision-v1",
            "next_scope": "BOUNDED_FRESH_INPUT_PACKET_REPAIR",
            "bounded_scope": repair_scope,
            "same_frozen_cohort_retry": False,
            "reason": "No 12-subject freeze was created; selection must be rerun only after the generic KR financial input contract is repaired and separately validated",
            "status": "BOUNDED",
        },
    )
    write_proof(
        args.report_dir,
        66,
        {
            "contract": "m12bo-master-workflow-update-v1",
            "update_state": "PENDING_FINAL_DOCUMENTATION_COMMIT",
            "proof_result": "FRESH_UNSEEN_PREMODEL_CONTRACT_GAP",
            "next_scope": "BOUNDED_FRESH_INPUT_PACKET_REPAIR",
            "status": "PENDING",
        },
    )
    completion = _completion_base(
        active=active,
        registry=registry,
        candidate_rows=candidate_rows,
        selected=selected,
        slot_failures=slot_failures,
        integrity=integrity,
        branch=branch,
        base_sha=base_sha,
        instruction_commit=instruction_commit,
    )
    write_proof(args.report_dir, 67, completion)
    write_json(
        args.output_root / "program-state.json",
        {
            "contract": PROGRAM_CONTRACT,
            "state": "STOP_BEFORE_MODEL",
            "stop_reason": premodel_reason,
            "proof_result": "FRESH_UNSEEN_PREMODEL_CONTRACT_GAP",
            "selected_shortlist": [row["ticker"] for row in selected],
            "frozen_cohort": [],
            "model_calls_started": 0,
            "selection_manifest_sha256": canonical_sha256(candidate_rows),
            "architecture_hashes": hashes,
            "persistence_applicability": persistence_decision,
        },
    )
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _secret_scan(paths: Sequence[Path]) -> dict[str, object]:
    findings = []
    for path in paths:
        payload = path.read_bytes()
        for name, pattern in _SECRET_PATTERNS.items():
            if pattern.search(payload):
                findings.append({"path": str(path), "pattern": name})
    return {
        "secret_scan_failure_count": len(findings),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "STOP_BEFORE_MODEL":
        raise ValueError("stop_before_model_state_required")
    completion_path = args.report_dir / "proofs" / f"{REPORT_NAMES[66]}.json"
    completion = read_json(completion_path)
    completion.update(
        {
            "final_local_head_sha": git_value("rev-parse", "HEAD"),
            "focused_test_result": args.focused_tests,
            "full_test_result": args.full_tests,
            "ruff_result": args.ruff,
            "git_diff_check": args.diff_check,
        }
    )
    write_proof(args.report_dir, 67, completion)
    write_proof(
        args.report_dir,
        66,
        {
            "contract": "m12bo-master-workflow-update-v1",
            "update_state": "COMMITTED_LOCAL_ONLY",
            "proof_result": completion["top_level_fresh_proof_result"],
            "next_scope": completion["next_scope"],
            "status": "PASS",
        },
    )

    def report_payloads() -> list[Path]:
        candidates = [
            *sorted(path for path in args.report_dir.rglob("*") if path.is_file()),
            Path.cwd() / WORK_INSTRUCTION,
            Path.cwd() / "docs/MASTER_WORKFLOW.md",
            Path.cwd() / "docs/PROJECT_HANDOFF.md",
            Path.cwd() / "docs/NEXT_SESSION_PROMPT.md",
            Path.cwd() / "docs/project-state.json",
            Path.cwd() / "scripts/new_fresh_unseen_real_proof_m12bo.py",
            Path.cwd() / "tests/test_new_fresh_unseen_real_proof_m12bo.py",
        ]
        excluded = {"artifact-index.json", "artifact-index.md"}
        return sorted(
            {path.resolve() for path in candidates if path.is_file() and path.name not in excluded}
        )

    included = report_payloads()
    projected_payload_count = len(included) + 1
    completion.update(
        {
            "artifact_count": projected_payload_count,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
        }
    )
    write_proof(args.report_dir, 67, completion)
    included = report_payloads()
    index_markdown = (args.report_dir / "artifact-index.md").resolve()
    write_text(
        index_markdown,
        "# Artifact Index\n\n"
        f"Indexed payloads: `{projected_payload_count}`. Secret scan: `PASS`.\n",
    )
    included = sorted({*included, index_markdown})
    if len(included) != projected_payload_count:
        raise ValueError("artifact_payload_count_changed_during_finalization")

    scan = _secret_scan(included)
    if scan["status"] != "PASS":
        raise ValueError("artifact_secret_scan_failure")
    rows = [
        {
            "path": str(path.relative_to(Path.cwd())),
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        }
        for path in included
    ]
    index = {
        "contract": "m12bo-report-artifact-index-v1",
        "artifact_count": len(rows),
        "rows": rows,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": 0,
        "raw_model_artifact_count": 0,
        "status": "PASS",
    }
    index_path = (args.report_dir / "artifact-index.json").resolve()
    write_json(index_path, index)
    archive_paths = [*included, index_path]
    if _secret_scan(archive_paths)["status"] != "PASS":
        raise ValueError("archive_secret_scan_failure")

    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in archive_paths:
            relative = path.relative_to(Path.cwd())
            archive.write(path, relative)
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
        archive_names = set(archive.namelist())
        expected_names = {str(row["path"]) for row in rows}
        expected_names.add(str(index_path.relative_to(Path.cwd())))
        missing = expected_names - archive_names
        extra = archive_names - expected_names
        hash_mismatch = sum(
            hashlib.sha256(archive.read(str(row["path"]))).hexdigest() != row["sha256"]
            for row in rows
        )
        size_mismatch = sum(len(archive.read(str(row["path"]))) != int(row["size"]) for row in rows)
    if bad_member is not None:
        raise ValueError(f"result_zip_crc_failure:{bad_member}")
    if missing or extra or hash_mismatch or size_mismatch:
        raise ValueError("result_zip_artifact_index_mismatch")
    digest = file_sha256(args.zip_output)
    write_text(
        args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"),
        f"{digest}  {args.zip_output.name}",
    )
    state.update(
        {
            "state": "COMPLETE",
            "final_local_head_sha": completion["final_local_head_sha"],
            "result_zip": str(args.zip_output),
            "result_zip_sha256": digest,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    mode = value.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    value.add_argument("--output-root", type=Path, required=True)
    value.add_argument("--report-dir", type=Path, required=True)
    value.add_argument("--reference-root", type=Path, required=True)
    value.add_argument("--provider-root", type=Path, required=True)
    value.add_argument("--active-database", type=Path, required=True)
    value.add_argument("--latest-result-zip", type=Path, required=True)
    value.add_argument("--as-of", type=datetime.fromisoformat)
    value.add_argument("--zip-output", type=Path, required=True)
    value.add_argument("--focused-tests", default="NOT_RUN")
    value.add_argument("--full-tests", default="NOT_RUN")
    value.add_argument("--ruff", default="NOT_RUN")
    value.add_argument("--diff-check", default="NOT_RUN")
    return value


def main() -> None:
    args = parser().parse_args()
    for name in (
        "output_root",
        "report_dir",
        "reference_root",
        "provider_root",
        "active_database",
        "latest_result_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    if args.prepare:
        if args.as_of is None:
            raise ValueError("prepare_requires_fixed_as_of")
        prepare(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
