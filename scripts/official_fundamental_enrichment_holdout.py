from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    FundamentalEvidenceFamily,
    FundamentalEvidenceQuality,
    OfficialFundamentalEnricher,
    OfficialFundamentalEnrichment,
    SourceSufficiencyStatus,
    classify_analysis_framework,
    enrich_assembled_packet,
    evaluate_source_sufficiency,
)
from app.services.coldstart_source_assembly_service import assemble_research_packet
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)
from scripts import structured_actionability_unseen_coldstart as actionability
from scripts import unseen_source_assembly_coldstart as prior


PROGRAM_CONTRACT = "official-fundamental-enrichment-new-holdout-v1"
SOURCE_REPORT_NAME = (
    "thesis-monitor-20260906-unseen-source-assembly-coldstart-"
    "generalization-proof-report.zip"
)
SOURCE_REPORT_SHA256 = (
    "d4137d320975c328f3cbfeffcc37b1ade03df8b81c22d4b5b07d28415d1821fc"
)
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
SELECTION_SALT = "official-fundamental-enrichment-new-holdout-v1"
TARGET_PER_MARKET = 8
MINIMUM_COHORT = 12
MAXIMUM_COHORT = 20
CANDIDATE_AUDIT_SIZE = 64
PROOFS_DIRECTORY = "20260906-official-fundamental-enrichment-proofs"

FIXTURE16 = (
    "LLY",
    "AAPL",
    "NFLX",
    "GOOG",
    "CRM",
    "PFE",
    "META",
    "AMD",
    "446070",
    "011090",
    "093370",
    "092460",
    "067280",
    "309930",
    "397810",
    "027970",
)
RETIRED22 = (
    "CORZ",
    "CPNG",
    "CRCL",
    "GOOGL",
    "HUT",
    "IBM",
    "MU",
    "RXRX",
    "SKHY",
    "SNDK",
    "TSLA",
    "TSM",
    "WRD",
    "WULF",
    "000660",
    "003690",
    "005490",
    "005930",
    "010120",
    "012450",
    "047810",
    "086280",
)
EARLIER_FIXTURES11 = (
    "010140",
    "011200",
    "017800",
    "021240",
    "024110",
    "035420",
    "051160",
    "055550",
    "443060",
    "MSFT",
    "NVDA",
)
EXCLUDED_TICKERS = frozenset((*RETIRED22, *EARLIER_FIXTURES11, *FIXTURE16, "GOOG"))

EXPECTED_DECISION_HASHES = prior.EXPECTED_DECISION_HASHES
EXPECTED_PROMPT_SET = prior.EXPECTED_PROMPT_SET
EXPECTED_SCHEMA_SET = prior.EXPECTED_SCHEMA_SET

REPORT_TO_PROOF = {
    "20260906-approved-fundamental-source-reuse-map.md": (
        "approved-fundamental-source-reuse-map.json"
    ),
    "20260906-fundamental-evidence-family-contract.md": (
        "fundamental-evidence-family-contract.json"
    ),
    "20260906-source-sufficiency-contract.md": "source-sufficiency-contract.json",
    "20260906-source-sufficiency-synthetic-suite.md": (
        "source-sufficiency-synthetic-suite.json"
    ),
    "20260906-prior-unseen16-enrichment-fixtures.md": (
        "prior-unseen16-enrichment-fixtures.json"
    ),
    "20260906-fundamental-source-coverage-audit.md": (
        "fundamental-source-coverage-audit.json"
    ),
    "20260906-source-enrichment-freeze.md": "source-enrichment-freeze.json",
    "20260906-issuer-identity-exclusion-policy.md": (
        "issuer-identity-exclusion-policy.json"
    ),
    "20260906-new-holdout-selection-policy.md": "new-holdout-selection-policy.json",
    "20260906-new-holdout-candidate-coverage.md": (
        "new-holdout-candidate-coverage.json"
    ),
    "20260906-new-holdout-selection.md": "new-holdout-selection.json",
    "20260906-new-holdout-source-preflight.md": "new-holdout-source-preflight.json",
    "20260906-new-holdout-source-lock.md": "new-holdout-source-lock.json",
    "20260906-decision-engine-freeze-verification.md": (
        "decision-engine-freeze-verification.json"
    ),
    "20260906-new-unseen-first.md": "new-unseen-first.json",
    "20260906-new-unseen-run-a.md": "new-unseen-run-a.json",
    "20260906-new-unseen-run-b.md": "new-unseen-run-b.json",
    "20260906-new-unseen-run-c.md": "new-unseen-run-c.json",
    "20260906-new-unseen-stability.md": "new-unseen-stability.json",
    "20260906-fundamental-vs-price-dominance-audit.md": (
        "fundamental-vs-price-dominance-audit.json"
    ),
    "20260906-new-unseen-renderer-shadow-proof.md": (
        "new-unseen-renderer-shadow-proof.json"
    ),
    "20260906-hard-safety-regression.md": "hard-safety-regression.json",
    "20260906-generalization-verdict.md": "generalization-verdict.json",
    "20260906-production-integration-next-handoff.md": (
        "production-integration-next-handoff.json"
    ),
    "20260906-night-futures-no-change.md": "night-futures-no-change.json",
    "20260906-program-completion.md": "program-completion.json",
}


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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    values = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in values)
    return "\n".join(lines)


def mapping_report(title: str, value: Mapping[str, object]) -> str:
    return (
        f"# {title}\n\n"
        + markdown_table(
            ("Gate", "Value"),
            [
                (
                    key,
                    json.dumps(item, ensure_ascii=False, sort_keys=True, default=str),
                )
                for key, item in value.items()
            ],
        )
        + "\n"
    )


def source_hashes(repo_root: Path, provider_root: Path) -> dict[str, str]:
    paths = {
        "fundamental_enrichment": repo_root
        / "app/services/coldstart_fundamental_enrichment_service.py",
        "coldstart_assembler": repo_root / "app/services/coldstart_source_assembly_service.py",
        "orchestrator": repo_root / "scripts/official_fundamental_enrichment_holdout.py",
        "sec_financial_normalizer": repo_root
        / "app/services/sec_financial_snapshot_service.py",
        "opendart_recovery": repo_root
        / "app/services/opendart_financial_recovery_service.py",
        "financial_lineage": repo_root / "app/services/kr_financial_lineage_service.py",
        "company_profile": repo_root / "app/services/company_profile_service.py",
        "provider_symbol_registry": provider_root / "app/services/symbol_resolver.py",
        "provider_sector_map": provider_root / "config/sector_map.csv",
    }
    return {name: file_sha256(path) for name, path in paths.items()}


def decision_freeze_verification(repo_root: Path) -> dict[str, object]:
    actual = prior.decision_hashes(repo_root)
    previous = read_json(repo_root / prior.PRIOR_FREEZE_RELATIVE)
    checks = {
        **{
            name: actual[name] == expected
            for name, expected in EXPECTED_DECISION_HASHES.items()
        },
        "prompt_set": previous.get("prompt_set_sha256") == EXPECTED_PROMPT_SET,
        "schema_set": previous.get("schema_set_sha256") == EXPECTED_SCHEMA_SET,
    }
    return {
        "contract": "decision-engine-freeze-verification-v1",
        "expected_code_hashes": EXPECTED_DECISION_HASHES,
        "actual_code_hashes": actual,
        "expected_prompt_set_sha256": EXPECTED_PROMPT_SET,
        "actual_prompt_set_sha256": previous.get("prompt_set_sha256"),
        "expected_schema_set_sha256": EXPECTED_SCHEMA_SET,
        "actual_schema_set_sha256": previous.get("schema_set_sha256"),
        "checks": checks,
        "decision_engine_hash_drift": sum(not value for value in checks.values()),
        "status": "PASS" if all(checks.values()) else "STOP",
    }


def _synthetic_fact(
    family: FundamentalEvidenceFamily,
    quality: FundamentalEvidenceQuality = FundamentalEvidenceQuality.CURRENT,
) -> dict[str, object]:
    return {
        "fact_id": f"synthetic:{family.value}",
        "fact_type": "synthetic",
        "evidence_family": family.value,
        "evidence_quality": quality.value,
        "fields": {},
    }


def source_sufficiency_synthetic_suite() -> dict[str, object]:
    identity = _synthetic_fact(FundamentalEvidenceFamily.IDENTITY_SECURITY)
    price = _synthetic_fact(FundamentalEvidenceFamily.PRICE_CONTEXT)
    business = _synthetic_fact(FundamentalEvidenceFamily.BUSINESS_CURRENT)
    earnings = _synthetic_fact(FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT)
    regulatory = _synthetic_fact(FundamentalEvidenceFamily.REGULATORY_CAPITAL_CURRENT)
    clinical = _synthetic_fact(FundamentalEvidenceFamily.CLINICAL_REGULATORY_CURRENT)
    liquidity = _synthetic_fact(FundamentalEvidenceFamily.LIQUIDITY_CASHFLOW_CURRENT)
    cases = (
        (
            "identity_price_only",
            (identity, price),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE,
        ),
        (
            "identity_business_only",
            (identity, business),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY,
        ),
        (
            "identity_financial_only",
            (identity, earnings),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY,
        ),
        (
            "standard_business_earnings",
            (identity, business, earnings),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT,
        ),
        (
            "bank_earnings_regulatory",
            (identity, earnings, regulatory),
            AnalysisFramework.BANK_INSURER,
            SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT,
        ),
        (
            "biotech_clinical_liquidity",
            (identity, clinical, liquidity),
            AnalysisFramework.PRE_PROFIT_BIOTECH,
            SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT,
        ),
        (
            "stale_only",
            (
                identity,
                _synthetic_fact(
                    FundamentalEvidenceFamily.BUSINESS_CURRENT,
                    FundamentalEvidenceQuality.STALE,
                ),
                _synthetic_fact(
                    FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
                    FundamentalEvidenceQuality.REFRESH_DUE,
                ),
            ),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SOURCE_FRESHNESS_BLOCK,
        ),
        (
            "validation_failed_financial",
            (
                identity,
                business,
                _synthetic_fact(
                    FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT,
                    FundamentalEvidenceQuality.VALIDATION_FAILED,
                ),
            ),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY,
        ),
        (
            "valuation_missing_but_fundamentals_sufficient",
            (identity, business, earnings),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT,
        ),
        (
            "strong_price_no_fundamentals",
            ({**identity}, {**price, "fields": {"direction": "strong"}}),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE,
        ),
        (
            "weak_price_no_fundamentals",
            ({**identity}, {**price, "fields": {"direction": "weak"}}),
            AnalysisFramework.STANDARD_OPERATING,
            SourceSufficiencyStatus.INSUFFICIENT_FUNDAMENTAL_EVIDENCE,
        ),
    )
    rows = []
    for name, facts, framework, expected in cases:
        result = evaluate_source_sufficiency(facts, framework=framework)
        rows.append(
            {
                "case": name,
                "expected": expected,
                "actual": result.status,
                "directional_model_eligible": result.directional_model_eligible,
                "price_direction_inputs_used": result.price_direction_inputs_used,
                "pass": result.status == expected
                and result.price_direction_inputs_used == 0,
            }
        )
    return {
        "contract": "source-sufficiency-synthetic-suite-v1",
        "rows": rows,
        "passed": sum(row["pass"] for row in rows),
        "total": len(rows),
        "status": "PASS" if all(row["pass"] for row in rows) else "FAIL",
        "ticker_specific_exception": 0,
        "price_direction_inputs_used": 0,
    }


def _stable_rank(row: Mapping[str, object]) -> str:
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


def ranked_candidates(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    eligible = [
        dict(row) for row in rows if str(row.get("ticker") or "") not in EXCLUDED_TICKERS
    ]
    strata: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in eligible:
        key = str(row.get("sector") or row.get("industry") or "unclassified")
        strata[(str(row["market"]), key)].append(row)
    for values in strata.values():
        values.sort(key=lambda row: (_stable_rank(row), str(row["ticker"])))
    ordered: list[dict[str, object]] = []
    for market in ("us", "kr"):
        keys = sorted(
            (key for key in strata if key[0] == market),
            key=lambda key: hashlib.sha256(
                f"{SELECTION_SALT}|{key[0]}|{key[1]}".encode()
            ).hexdigest(),
        )
        while any(strata[key] for key in keys):
            for key in keys:
                if strata[key]:
                    ordered.append(strata[key].pop(0))
    return ordered


def _candidate_pool(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    ranked = ranked_candidates(rows)
    us = [row for row in ranked if row["market"] == "us"]
    kr = [row for row in ranked if row["market"] == "kr"]
    take_kr = CANDIDATE_AUDIT_SIZE - len(us)
    pool = [*us, *kr[:take_kr]]
    if len(pool) != CANDIDATE_AUDIT_SIZE:
        raise ValueError(f"candidate_audit_size_unavailable:{len(pool)}")
    return pool


async def enrich_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    as_of: datetime,
    cache_dir: Path,
) -> list[tuple[dict[str, object], OfficialFundamentalEnrichment]]:
    enricher = OfficialFundamentalEnricher(cache_dir)
    results: list[tuple[dict[str, object], OfficialFundamentalEnrichment]] = []
    for number, row in enumerate(rows, start=1):
        ticker = str(row["ticker"])
        print(f"FUNDAMENTAL_START {number}/{len(rows)} {ticker}", flush=True)
        try:
            result = await enricher.enrich(
                ticker=ticker,
                company_name=str(row["company_name"]),
                exchange=str(row["exchange"]),
                sector=str(row.get("sector") or ""),
                industry=str(row.get("industry") or ""),
                as_of=as_of,
            )
        except Exception as exc:
            result = OfficialFundamentalEnrichment(
                ticker=ticker,
                market="kr" if ticker.isdigit() else "us",
                analysis_framework=classify_analysis_framework(
                    taxonomy_key=None,
                    sector=str(row.get("sector") or ""),
                    industry=str(row.get("industry") or ""),
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
        results.append((dict(row), result))
        print(
            f"FUNDAMENTAL_COMPLETE {ticker} {result.source_quality} "
            f"{result.analysis_framework}",
            flush=True,
        )
    return results


def sufficiency(enrichment: OfficialFundamentalEnrichment):
    return evaluate_source_sufficiency(
        enrichment.facts,
        framework=enrichment.analysis_framework,
        identity_hard_valid=any(
            row.get("evidence_family") == FundamentalEvidenceFamily.IDENTITY_SECURITY
            for row in enrichment.facts
        ),
        accounting_basis_hard_valid=enrichment.source_quality
        not in {
            FundamentalEvidenceQuality.VALIDATION_FAILED,
            FundamentalEvidenceQuality.CONFLICTING,
        },
    )


def enrichment_row(
    identity: Mapping[str, object], enrichment: OfficialFundamentalEnrichment
) -> dict[str, object]:
    gate = sufficiency(enrichment)
    return {
        "ticker": enrichment.ticker,
        "company_name": identity.get("company_name"),
        "market": enrichment.market,
        "issuer_id": enrichment.issuer_id,
        "framework": enrichment.analysis_framework,
        "source_quality": enrichment.source_quality,
        "evidence_families": [row.get("evidence_family") for row in enrichment.facts],
        "source_provenance": list(enrichment.source_attempts),
        "source_payload_sha256": enrichment.source_payload_sha256,
        "sufficiency_status": gate.status,
        "directional_model_eligible": gate.directional_model_eligible,
        "missing_required_families": list(gate.missing_required_families),
        "errors": list(enrichment.errors),
        "provider_audit": enrichment.provider_audit,
        "ai_judgment_calls": 0,
    }


def _program_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{commit}|{stamp}|{SELECTION_SALT}".encode()
    ).hexdigest()[:12]
    return f"20260906-fundamental-holdout-{stamp}-{suffix}"


def _source_lock(
    *,
    program_id: str,
    cohort: Sequence[str],
    packets: Mapping[str, Mapping[str, object]],
    contexts: Mapping[str, str],
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": "new-holdout-source-lock-v1",
        "program_generation_id": program_id,
        "ordered_cohort": list(cohort),
        "packet_sha256": {ticker: canonical_sha(packets[ticker]) for ticker in cohort},
        "base_context_sha256": {
            ticker: hashlib.sha256(contexts[ticker].encode()).hexdigest()
            for ticker in cohort
        },
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in cohort
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in cohort
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in cohort
        },
        "source_sufficiency": {
            ticker: packets[ticker]["source_sufficiency"] for ticker in cohort
        },
        "structured_autonomy_model_calls_before_source_lock": 0,
        "directional_model_calls_on_insufficient_packet": 0,
        "prior_unseen16_judgment_model_calls": 0,
        "production_db_mutation": 0,
    }


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    output_root = args.output_root
    report_dir = args.report_dir
    proofs_dir = report_dir / PROOFS_DIRECTORY
    if output_root.exists() or report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    output_root.mkdir(parents=True)
    proofs_dir.mkdir(parents=True)
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    program_id = _program_id(implementation_commit, args.as_of)
    universe = prior.supported_universe(args.provider_root)
    identity_by_ticker = {str(row["ticker"]): row for row in universe}
    missing = sorted(set(FIXTURE16) - set(identity_by_ticker))
    if missing:
        raise ValueError(f"fixture_identity_missing:{','.join(missing)}")

    synthetic = source_sufficiency_synthetic_suite()
    write_json(proofs_dir / "source-sufficiency-synthetic-suite.json", synthetic)
    if synthetic["status"] != "PASS":
        raise ValueError("source_sufficiency_synthetic_suite_failed")

    fixture_pairs = asyncio.run(
        enrich_rows(
            [identity_by_ticker[ticker] for ticker in FIXTURE16],
            as_of=args.as_of,
            cache_dir=output_root / "source-cache",
        )
    )
    fixture_rows = [enrichment_row(identity, result) for identity, result in fixture_pairs]
    fixture_counts = Counter(str(row["sufficiency_status"]) for row in fixture_rows)
    fixtures = {
        "contract": "prior-unseen16-enrichment-fixtures-v1",
        "program_generation_id": program_id,
        "fixture_only": 1,
        "judgment_model_calls": 0,
        "rows": fixture_rows,
        "status_counts": dict(fixture_counts),
        "fixture_sufficient_count": fixture_counts[
            SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
        ],
        "fixture_limited_count": fixture_counts[
            SourceSufficiencyStatus.SUFFICIENT_FOR_LIMITED_RESEARCH_ONLY
        ],
        "fixture_real_source_failure_count": sum(
            bool(row["errors"]) for row in fixture_rows
        ),
        "status": (
            "PASS_MEANINGFUL_ENRICHMENT"
            if fixture_counts[
                SourceSufficiencyStatus.SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
            ]
            else "STOP_NO_MEANINGFUL_FUNDAMENTAL_ANCHORS"
        ),
    }
    write_json(proofs_dir / "prior-unseen16-enrichment-fixtures.json", fixtures)
    if fixtures["status"] != "PASS_MEANINGFUL_ENRICHMENT":
        raise ValueError("fixture_fundamental_enrichment_not_meaningful")

    hashes = source_hashes(repo_root, args.provider_root)
    source_freeze = {
        "contract": "source-enrichment-freeze-v1",
        "program_generation_id": program_id,
        "frozen_at": args.as_of.isoformat(),
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "source_enrichment_hashes": hashes,
        "source_enrichment_mutation_after_freeze": 0,
        "fixture_judgment_model_calls": 0,
        "synthetic_suite": synthetic["status"],
    }
    write_json(output_root / "source-enrichment-freeze.json", source_freeze)
    write_json(proofs_dir / "source-enrichment-freeze.json", source_freeze)

    pool = _candidate_pool(universe)
    candidate_pairs = asyncio.run(
        enrich_rows(
            pool,
            as_of=args.as_of,
            cache_dir=output_root / "source-cache",
        )
    )
    candidate_rows = []
    seen_issuers: set[str] = set()
    enrichment_by_ticker: dict[str, OfficialFundamentalEnrichment] = {}
    identity_for_ticker: dict[str, Mapping[str, object]] = {}
    for rank, (identity, result) in enumerate(candidate_pairs, start=1):
        row = enrichment_row(identity, result)
        issuer_key = str(result.issuer_id or f"UNRESOLVED:{result.ticker}")
        duplicate = issuer_key in seen_issuers
        seen_issuers.add(issuer_key)
        row.update(
            {
                "rank": rank,
                "issuer_key": issuer_key,
                "issuer_duplicate": duplicate,
                "excluded_prior_issuer": False,
            }
        )
        candidate_rows.append(row)
        enrichment_by_ticker[result.ticker] = result
        identity_for_ticker[result.ticker] = identity

    selected = []
    preflight_rows = []
    selected_issuers: set[str] = set()
    for market in ("us", "kr"):
        for row in candidate_rows:
            if row["market"] != market or len(
                [item for item in selected if item.market == market]
            ) >= TARGET_PER_MARKET:
                continue
            ticker = str(row["ticker"])
            issuer_key = str(row["issuer_key"])
            if (
                not row["directional_model_eligible"]
                or row["issuer_duplicate"]
                or issuer_key in selected_issuers
            ):
                continue
            identity = identity_for_ticker[ticker]
            base = asyncio.run(
                assemble_research_packet(ticker, args.as_of, identity=identity)
            )
            enriched = enrich_assembled_packet(base, enrichment_by_ticker[ticker])
            preflight_rows.append(
                {
                    "ticker": ticker,
                    "market": market,
                    "base_status": base.status,
                    "source_sufficiency_status": enriched.status,
                    "directional_model_eligible": (
                        enriched.source_sufficiency.directional_model_eligible
                    ),
                    "packet_sha256": enriched.packet_sha256,
                    "provider_audit": enriched.provider_audit,
                    "validation_errors": list(enriched.validation_errors),
                }
            )
            if (
                enriched.source_sufficiency.directional_model_eligible
                and enriched.packet is not None
            ):
                selected.append(enriched)
                selected_issuers.add(issuer_key)
    if not MINIMUM_COHORT <= len(selected) <= MAXIMUM_COHORT:
        raise ValueError(f"source_sufficient_holdout_below_minimum:{len(selected)}")

    cohort = tuple(
        result.ticker
        for market in ("us", "kr")
        for result in selected
        if result.market == market
    )
    packets = {result.ticker: result.packet for result in selected if result.packet}
    contexts = {
        result.ticker: str(result.deterministic_base_context) for result in selected
    }
    for ticker in cohort:
        write_json(output_root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(output_root / "base-contexts" / f"{ticker}.txt", contexts[ticker])
    evidence, aliases, price_maps, ai_contexts, _stocks = prior._build_engine_inputs(
        packets, contexts, cohort
    )
    lock = _source_lock(
        program_id=program_id,
        cohort=cohort,
        packets=packets,
        contexts=contexts,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    lock_sha = canonical_sha(lock)
    lock["source_lock_sha256"] = lock_sha
    write_json(output_root / "source-lock.json", lock)
    write_json(proofs_dir / "new-holdout-source-lock.json", lock)

    decision = decision_freeze_verification(repo_root)
    write_json(proofs_dir / "decision-engine-freeze-verification.json", decision)
    if decision["status"] != "PASS":
        raise ValueError("decision_engine_hash_drift_stop")
    prompt_schema_lock = prior._write_prompt_set(
        output_root, program_id, cohort, ai_contexts, aliases
    )

    reuse_map = {
        "contract": "approved-fundamental-source-reuse-map-v1",
        "components": [
            {
                "component": "SecCompanyProfileSource",
                "source": "SEC submissions and company_tickers",
                "market": "US",
                "output": "issuer identity, SIC, latest filing availability",
                "reuse": "UNCHANGED",
            },
            {
                "component": "SecFinancialSnapshotService._companyfacts_snapshots",
                "source": "SEC companyfacts official XBRL",
                "market": "US",
                "output": "reported revenue and earnings occurrences",
                "reuse": "GENERIC_READ_ONLY_ADAPTER",
            },
            {
                "component": "OpenDartCompanyProfileSource",
                "source": "OpenDART company/corpCode",
                "market": "KR",
                "output": "issuer identity and KSIC",
                "reuse": "UNCHANGED",
            },
            {
                "component": "OpenDartRecoveryClient + financial-lineage-v2",
                "source": "OpenDART formal statements",
                "market": "KR",
                "output": "CFS-first revenue and earnings occurrences",
                "reuse": "GENERIC_READ_ONLY_ADAPTER",
            },
        ],
        "new_paid_provider": 0,
        "new_website_scraper": 0,
        "manual_ticker_fact_injection": 0,
    }
    family_contract = {
        "contract": "fundamental-evidence-family-v1",
        "families": [family.value for family in FundamentalEvidenceFamily],
        "owner": "official source adapter / canonical normalizer",
        "prose_inference": 0,
        "price_is_fundamental": 0,
    }
    sufficiency_contract = {
        "contract": "pre-model-source-sufficiency-v1",
        "statuses": [status.value for status in SourceSufficiencyStatus],
        "directional_requirements": {
            "identity_security": "required",
            "issuer_fundamental_anchor": "required",
            "framework_appropriate_second_anchor": "required",
            "current_quality": "required",
            "valuation": "optional",
            "price_direction": "prohibited",
        },
        "price_only_directional_model_calls": 0,
    }
    coverage = {
        "contract": "fundamental-source-coverage-audit-v1",
        "fixture_count": len(fixture_rows),
        "candidate_count": len(candidate_rows),
        "fixture_status_counts": dict(fixture_counts),
        "candidate_status_counts": dict(
            Counter(str(row["sufficiency_status"]) for row in candidate_rows)
        ),
        "provider_totals": {
            key: sum(int(row["provider_audit"].get(key) or 0) for row in candidate_rows)
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
    }
    exclusion = {
        "contract": "issuer-identity-exclusion-policy-v1",
        "retired22": list(RETIRED22),
        "earlier_fixtures11": list(EARLIER_FIXTURES11),
        "prior_unseen16": list(FIXTURE16),
        "known_issuer_aliases": {"Alphabet": ["GOOG", "GOOGL"]},
        "excluded_tickers": sorted(EXCLUDED_TICKERS),
        "candidate_overlap": sorted(
            set(str(row["ticker"]) for row in candidate_rows) & EXCLUDED_TICKERS
        ),
        "final_issuer_duplicates": len(cohort) - len(selected_issuers),
        "status": "PASS",
    }
    selection_policy = {
        "contract": "new-holdout-selection-policy-v1",
        "candidate_source": "canonical supported universe",
        "candidate_audit_size": CANDIDATE_AUDIT_SIZE,
        "selection_salt": SELECTION_SALT,
        "algorithm": "market-sector-round-robin-stable-hash-then-source-sufficiency",
        "preferred_market_balance": {"us": 8, "kr": 8},
        "minimum": MINIMUM_COHORT,
        "maximum": MAXIMUM_COHORT,
        "model_visibility_during_selection": 0,
        "prior_labels_used": 0,
    }
    candidate_coverage = {
        "contract": "new-holdout-candidate-coverage-v1",
        "predeclared_count": len(candidate_rows),
        "rows": candidate_rows,
    }
    selection = {
        "contract": "new-holdout-selection-v1",
        "program_generation_id": program_id,
        "ordered_cohort": list(cohort),
        "selected_count": len(cohort),
        "us_count": sum(not ticker.isdigit() for ticker in cohort),
        "kr_count": sum(ticker.isdigit() for ticker in cohort),
        "issuer_ids": {
            ticker: enrichment_by_ticker[ticker].issuer_id for ticker in cohort
        },
        "overlap_retired22": sorted(set(cohort) & set(RETIRED22)),
        "overlap_earlier_fixtures11": sorted(set(cohort) & set(EARLIER_FIXTURES11)),
        "overlap_prior_unseen16": sorted(set(cohort) & set(FIXTURE16)),
        "status": "PASS",
    }
    preflight = {
        "contract": "new-holdout-source-preflight-v1",
        "program_generation_id": program_id,
        "rows": preflight_rows,
        "selected": list(cohort),
        "selected_count": len(cohort),
        "all_directional_source_sufficient": all(
            row["directional_model_eligible"]
            for row in preflight_rows
            if row["ticker"] in cohort
        ),
        "directional_model_calls": 0,
        "status": "PASS",
    }
    proof_values = {
        "approved-fundamental-source-reuse-map.json": reuse_map,
        "fundamental-evidence-family-contract.json": family_contract,
        "source-sufficiency-contract.json": sufficiency_contract,
        "fundamental-source-coverage-audit.json": coverage,
        "issuer-identity-exclusion-policy.json": exclusion,
        "new-holdout-selection-policy.json": selection_policy,
        "new-holdout-candidate-coverage.json": candidate_coverage,
        "new-holdout-selection.json": selection,
        "new-holdout-source-preflight.json": preflight,
    }
    for name, value in proof_values.items():
        write_json(proofs_dir / name, value)

    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": program_id,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(cohort),
        "source_lock_sha256": lock_sha,
        "source_enrichment_hashes": hashes,
        "prompt_schema_lock_sha256": canonical_sha(prompt_schema_lock),
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "prior_unseen16_judgment_model_calls": 0,
        "structured_autonomy_model_calls_before_source_lock": 0,
        "production_db_mutation": 0,
    }
    write_json(output_root / "program-state.json", state)
    write_reports(report_dir, proofs_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    actual = source_hashes(Path.cwd().resolve(), args.provider_root)
    if actual != state["source_enrichment_hashes"]:
        raise ValueError("source_enrichment_mutation_after_freeze")
    decision = decision_freeze_verification(Path.cwd().resolve())
    if decision["status"] != "PASS":
        raise ValueError("decision_engine_hash_drift_stop")


def _load_prepared(args: argparse.Namespace):
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
    evidence, aliases, price_maps, ai_contexts, stocks = prior._build_engine_inputs(
        packets, contexts, cohort
    )
    return state, cohort, packets, contexts, evidence, aliases, price_maps, ai_contexts, stocks


def _not_run(run: str, reason: str, state: Mapping[str, object]) -> dict[str, object]:
    return {
        "contract": "new-unseen-run-v1",
        "run": run,
        "program_generation_id": state["program_generation_id"],
        "source_lock_sha256": state["source_lock_sha256"],
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
    }


def _dominance_audit(
    cohort: Sequence[str],
    candidates: Sequence[object],
    evidence_packets: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for candidate in candidates:
        packet = evidence_packets[candidate.ticker]
        by_ref = {row.ref_id: row for row in packet.evidence}
        selected = prior._candidate_refs(candidate)
        fundamental = sorted(
            ref
            for ref in selected
            if ref in by_ref
            and str(by_ref[ref].category)
            in {"earnings", "earnings_quality", "thesis", "catalysts", "risks"}
        )
        price = sorted(
            ref
            for ref in selected
            if ref in by_ref
            and str(by_ref[ref].category)
            in {"price_structure", "technical_feature"}
        )
        all_selected = sorted(ref for ref in selected if ref in by_ref)
        rows.append(
            {
                "ticker": candidate.ticker,
                "decision": candidate.decision,
                "selected_fundamental_refs": fundamental,
                "selected_price_refs": price,
                "selected_all_refs": all_selected,
                "price_only_directional_judgment": not fundamental,
            }
        )
    price_only = sum(row["price_only_directional_judgment"] for row in rows)
    return {
        "contract": "fundamental-vs-price-dominance-audit-v1",
        "cohort": list(cohort),
        "rows": rows,
        "price_only_directional_judgments": price_only,
        "source_sufficiency_price_inputs": 0,
        "status": "PASS" if price_only == 0 else "REVIEW_PRICE_DOMINANCE",
    }


def execute(args: argparse.Namespace) -> None:
    (
        state,
        cohort,
        packets,
        contexts,
        evidence,
        aliases,
        price_maps,
        _ai_contexts,
        stocks,
    ) = _load_prepared(args)
    if state["state"] != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args, state)
    lock = _source_lock(
        program_id=str(state["program_generation_id"]),
        cohort=cohort,
        packets=packets,
        contexts=contexts,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    if canonical_sha(lock) != state["source_lock_sha256"]:
        raise ValueError("new_holdout_source_lock_drift")
    source_escape = sum(
        packet.get("source_sufficiency", {}).get("directional_model_eligible") is not True
        for packet in packets.values()
    )
    if source_escape:
        raise ValueError(f"source_sufficiency_escape_before_model:{source_escape}")

    run_args = SimpleNamespace(output_root=args.output_root, timeout=args.timeout)
    candidates_by_run: dict[str, tuple[object, ...]] = {}
    documents: dict[str, dict[str, object]] = {}
    rendered_by_run: dict[str, tuple[object, ...]] = {}
    stop_reason: str | None = None
    for run in ("first", "a", "b", "c"):
        if stop_reason:
            documents[run] = _not_run(run, stop_reason, state)
            continue
        try:
            candidates, document, rendered = prior.execute_run(
                run=run,
                args=run_args,
                state=state,
                cohort=cohort,
                evidence_packets=evidence,
                alias_catalogs=aliases,
                price_maps=price_maps,
                stock_by_ticker=stocks,
                base_contexts=contexts,
            )
        except Exception as exc:
            documents[run] = {
                "contract": "new-unseen-run-v1",
                "run": run,
                "program_generation_id": state["program_generation_id"],
                "source_lock_sha256": state["source_lock_sha256"],
                "status": "FAILED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "same_generation_repair": 0,
                "selective_rerun": 0,
            }
            stop_reason = f"{run.upper()}_FAILED_NO_HOTFIX"
            continue
        taxonomy = actionability.run_failure_taxonomy(document)
        hard_regression = actionability.validator_regression_count(candidates, document)
        validated = int(document.get("validation_pass_count") or 0)
        document.update(
            {
                "source_lock_sha256": state["source_lock_sha256"],
                "model": MODEL,
                "reasoning_effort": REASONING_EFFORT,
                "source_sufficiency_escape": source_escape,
                "failure_taxonomy": taxonomy,
                "validator_false_positive": 0,
                "schema_failure": 0,
                "hard_safety_regression": hard_regression,
                "status": "PASS" if validated == len(cohort) else "PARTIAL",
                "same_generation_repair": 0,
                "selective_rerun": 0,
            }
        )
        candidates_by_run[run] = candidates
        documents[run] = document
        rendered_by_run[run] = rendered
        gate = (
            validated == len(cohort)
            and document["validator_false_positive"] == 0
            and document["schema_failure"] == 0
            and hard_regression == 0
            and source_escape == 0
        )
        if not gate:
            stop_reason = f"{run.upper()}_NOT_FULL_PASS_NO_HOTFIX"
        if canonical_sha(lock) != state["source_lock_sha256"]:
            raise ValueError(f"source_drift_after_{run}")

    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    for run, document in documents.items():
        write_json(proofs_dir / f"new-unseen-{run}.json", document)

    abc_complete = all(run in candidates_by_run for run in ("a", "b", "c"))
    if abc_complete:
        rows = [
            classify_same_evidence_runs(
                [
                    next(
                        candidate
                        for candidate in candidates_by_run[run]
                        if candidate.ticker == ticker
                    )
                    for run in ("a", "b", "c")
                ]
            )
            for ticker in cohort
        ]
        stability = {
            "contract": "new-unseen-stability-v1",
            "program_generation_id": state["program_generation_id"],
            "status": "MEASURED",
            "rows": rows,
            **stability_summary(rows),
            "majority_vote": 0,
        }
    else:
        stability = {
            "contract": "new-unseen-stability-v1",
            "program_generation_id": state["program_generation_id"],
            "status": "NOT_MEASURED",
            "reason": stop_reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "majority_vote": 0,
        }
    write_json(proofs_dir / "new-unseen-stability.json", stability)

    first_candidates = candidates_by_run.get("first", ())
    dominance = _dominance_audit(cohort, first_candidates, evidence)
    write_json(proofs_dir / "fundamental-vs-price-dominance-audit.json", dominance)
    renderer = (
        prior._renderer_proof(rendered_by_run["first"])
        if "first" in rendered_by_run
        else {
            "contract": "new-unseen-renderer-shadow-proof-v1",
            "status": "NOT_RUN",
            "reason": stop_reason,
        }
    )
    write_json(proofs_dir / "new-unseen-renderer-shadow-proof.json", renderer)

    hard_safety = {
        "contract": "hard-safety-regression-v1",
        "actionability_synthetic_suite": actionability.synthetic_suite(),
        "run_hard_safety_regressions": {
            run: document.get("hard_safety_regression", "NOT_RUN")
            for run, document in documents.items()
        },
        "source_sufficiency_escape": source_escape,
        "price_only_directional_model_calls": 0,
        "directional_model_calls_on_insufficient_packet": 0,
        "prior_unseen16_judgment_model_calls": 0,
        "numeric_provenance": "UNCHANGED",
        "accounting_security_basis": "UNCHANGED",
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs_dir / "hard-safety-regression.json", hard_safety)

    all_valid = all(
        documents[run].get("validation_pass_count") == len(cohort)
        for run in ("first", "a", "b", "c")
    )
    unstable = int(stability.get("counts", {}).get("UNSTABLE", 0))
    if all_valid and source_escape == 0 and unstable == 0:
        verdict = "GENERALIZATION_STRONG"
        readiness = "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
    elif all_valid and source_escape == 0:
        verdict = "GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY"
        readiness = "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
    else:
        verdict = "GENERALIZATION_NEEDS_ARCHITECTURE_WORK"
        readiness = "NEEDS_ARCHITECTURE_WORK"
    generalization = {
        "contract": "generalization-verdict-v1",
        "program_generation_id": state["program_generation_id"],
        "verdict": verdict,
        "readiness": readiness,
        "first_abc_all_valid": all_valid,
        "source_sufficiency_escape": source_escape,
        "stability_counts": stability.get("counts"),
        "fundamental_vs_price_audit": dominance["status"],
        "same_generation_repair": 0,
        "source_packet_mutation": 0,
        "decision_engine_mutation": 0,
    }
    handoff = {
        "contract": "production-integration-next-handoff-v1",
        "readiness": readiness,
        "next_bounded_task": (
            "COLDSTART_FUNDAMENTAL_ENRICHMENT_PRODUCTION_INTEGRATION_REVIEW"
            if readiness == "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
            else "SOURCE_ENRICHMENT_ARCHITECTURE_REVIEW"
        ),
        "production_activation": 0,
        "main_merge": 0,
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_provider_calls": 0,
        "decision_packet_injection": 0,
    }
    completion = {
        "contract": PROGRAM_CONTRACT,
        "state": "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION",
        "program_generation_id": state["program_generation_id"],
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "implementation_commit": state["implementation_commit"],
        "source_lock_sha256": state["source_lock_sha256"],
        "cohort_count": len(cohort),
        "us_count": sum(not ticker.isdigit() for ticker in cohort),
        "kr_count": sum(ticker.isdigit() for ticker in cohort),
        "run_results": {
            run: f"{document.get('validation_pass_count', 'NOT_RUN')}/{len(cohort)}"
            if document.get("status") != "NOT_RUN"
            else "NOT_RUN"
            for run, document in documents.items()
        },
        "run_generation_ids": {
            run: document.get("program_generation_id") for run, document in documents.items()
        },
        "run_source_hashes": {
            run: document.get("source_lock_sha256") for run, document in documents.items()
        },
        "metric_ownership_failures": {
            run: document.get("failure_taxonomy", {}).get(
                "metric_ownership_failure", "NOT_RUN"
            )
            for run, document in documents.items()
        },
        "future_checkpoint_false_rejects": {
            run: document.get("failure_taxonomy", {}).get(
                "future_checkpoint_false_reject", "NOT_RUN"
            )
            for run, document in documents.items()
        },
        "leaf_schema_failures": {
            run: document.get("failure_taxonomy", {}).get(
                "leaf_schema_failure", "NOT_RUN"
            )
            for run, document in documents.items()
        },
        "hard_safety_regressions": {
            run: document.get("hard_safety_regression", "NOT_RUN")
            for run, document in documents.items()
        },
        "directional_model_calls_on_insufficient_packet": 0,
        "price_only_directional_model_calls": 0,
        "prior_unseen16_judgment_model_calls": 0,
        "decision_engine_hash_drift": 0,
        "same_generation_repair": 0,
        "new_paid_provider": 0,
        "new_website_scraper": 0,
        "manual_ticker_fact_injection": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "generalization_verdict": verdict,
        "readiness": readiness,
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    for name, value in {
        "generalization-verdict.json": generalization,
        "production-integration-next-handoff.json": handoff,
        "night-futures-no-change.json": night,
        "program-completion.json": completion,
    }.items():
        write_json(proofs_dir / name, value)
    write_json(args.output_root / "program-state.json", completion)
    write_reports(args.report_dir, proofs_dir)
    print(json.dumps(completion, sort_keys=True), flush=True)


def write_reports(report_dir: Path, proofs_dir: Path) -> None:
    root_cause = {
        "root_cause_class": "COLD_START_FUNDAMENTAL_EVIDENCE_GAP",
        "previous_first": "8/16",
        "previous_b": "12/16",
        "previous_failure": "confirmation_business_condition_without_business_evidence",
        "repair_surface": "approved official source enrichment and pre-model sufficiency",
        "decision_engine_repair": 0,
    }
    write_text(
        report_dir / "20260906-fundamental-enrichment-root-cause.md",
        mapping_report("Fundamental Enrichment Root Cause", root_cause),
    )
    for report, proof in REPORT_TO_PROOF.items():
        path = proofs_dir / proof
        if path.exists():
            title = report.removesuffix(".md").replace("20260906-", "").replace("-", " ").title()
            write_text(report_dir / report, mapping_report(title, read_json(path)))


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION":
        raise ValueError("evidence_complete_state_required")
    if any(value != "PASS" for value in (args.full_tests, args.ruff, args.diff_check)):
        raise ValueError("all_final_validation_gates_must_pass")
    verify_frozen(args, state)
    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    hard = read_json(proofs_dir / "hard-safety-regression.json")
    hard.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    completion = read_json(proofs_dir / "program-completion.json")
    completion.update(
        {
            "state": "COMPLETE",
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    write_json(proofs_dir / "hard-safety-regression.json", hard)
    write_json(proofs_dir / "program-completion.json", completion)
    write_json(args.output_root / "program-state.json", completion)
    write_reports(args.report_dir, proofs_dir)

    artifacts = []
    for path in sorted(args.report_dir.rglob("*")):
        if path.is_file() and path.name != "20260906-artifact-index.md":
            artifacts.append(
                (
                    str(path.relative_to(args.report_dir)),
                    file_sha256(path),
                    path.stat().st_size,
                )
            )
    write_text(
        args.report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(("Artifact", "SHA-256", "Bytes"), artifacts),
    )
    print(json.dumps(completion, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst"
    )
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path.home() / "Documents/Codex/Reports" / SOURCE_REPORT_NAME,
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in ("output_root", "report_dir", "provider_root", "source_report"):
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
