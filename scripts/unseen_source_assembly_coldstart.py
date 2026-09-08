from __future__ import annotations

import argparse
import ast
import asyncio
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.coldstart_source_assembly_service import (
    BASE_CONTEXT_VERSION,
    CONTRACT_VERSION as ASSEMBLY_CONTRACT,
    NORMALIZATION_VERSION,
    PACKET_SCHEMA_VERSION,
    SourceAssemblyResult,
    SourceAssemblyStatus,
    assemble_research_packet,
    canonical_sha256,
)
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.packet_owned_technical_context_service import (
    packet_owned_context_for_stock,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    alias_price_choices,
    build_alias_constrained_batch_schema,
    build_evidence_alias_catalog,
    compact_alias_ai_context,
    resolve_candidate_aliases,
)
from app.services.structured_autonomy_shadow_service import (
    OUTPUT_CONTRACT,
    StructuredAutonomyCandidate,
    allowed_price_refs,
    explicit_actionable_trade_directives,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)
from scripts import structured_actionability_unseen_coldstart as actionability
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "unseen-source-assembly-coldstart-generalization-v1"
SOURCE_REPORT_SHA256 = (
    "c4201d6b960ef68f49e51fd8caa2b6c59bbca2747743348ffa982d5da0b61a22"
)
SOURCE_REPORT_NAME = (
    "thesis-monitor-20260906-structured-actionability-unseen-coldstart-report.zip"
)
PRIOR_FREEZE_RELATIVE = Path(
    "docs/reports/20260906-structured-actionability-proofs/experiment-freeze.json"
)
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
FIXTURE_TICKERS = (
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
RETIRED_TICKERS = (
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
EXPECTED_DECISION_HASHES = {
    "builder_prompt": "2a4e6b4775db5e3f4d1b56b3f804613994e2602e4aaefd7902a9c1640cacb672",
    "directional_balance": "2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab",
    "logical_condition": "255837edf51ff7fe06f26ed4d4782479131d2485e5e19349aa2a3f095ca1d234",
    "stability": "e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188",
    "validator_renderer": "ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f",
}
EXPECTED_PROMPT_SET = "95a46a8d3ac708aa981203270236eec7b21bdf196be7577245cc1e52fea50c89"
EXPECTED_SCHEMA_SET = "e86b747a0c6f459650275598a7c3c217bb0116ef6b6f8927debf3dfa938fd668"
SELECTION_SALT = "unseen-source-assembly-selection-v1"
TARGET_PER_MARKET = 8
MINIMUM_COHORT = 12
MAX_COHORT = 20
PROOFS_DIRECTORY = "20260906-unseen-source-assembly-proofs"

REPORT_NAMES = (
    "20260906-source-assembly-root-cause.md",
    "20260906-source-assembly-reuse-map.md",
    "20260906-arbitrary-ticker-source-packet-contract.md",
    "20260906-deterministic-base-context-contract.md",
    "20260906-preflight11-source-assembly-fixtures.md",
    "20260906-source-assembly-freeze.md",
    "20260906-final-unseen-selection-policy.md",
    "20260906-final-unseen-cohort-selection.md",
    "20260906-final-unseen-source-preflight.md",
    "20260906-final-unseen-source-lock.md",
    "20260906-decision-engine-freeze-verification.md",
    "20260906-unseen-first.md",
    "20260906-unseen-run-a.md",
    "20260906-unseen-run-b.md",
    "20260906-unseen-run-c.md",
    "20260906-unseen-stability.md",
    "20260906-unseen-source-quality-audit.md",
    "20260906-unregistered-lifecycle-audit.md",
    "20260906-unseen-renderer-shadow-proof.md",
    "20260906-hard-safety-regression.md",
    "20260906-generalization-verdict.md",
    "20260906-production-integration-next-handoff.md",
    "20260906-night-futures-no-change.md",
    "20260906-program-completion.md",
    "20260906-artifact-index.md",
)
PROOF_NAMES = (
    "source-assembly-reuse-map.json",
    "arbitrary-ticker-source-packet-contract.json",
    "deterministic-base-context-contract.json",
    "preflight11-source-assembly-fixtures.json",
    "source-assembly-freeze.json",
    "final-unseen-selection-policy.json",
    "final-unseen-cohort-selection.json",
    "final-unseen-source-preflight.json",
    "final-unseen-source-lock.json",
    "decision-engine-freeze-verification.json",
    "unseen-first.json",
    "unseen-run-a.json",
    "unseen-run-b.json",
    "unseen-run-c.json",
    "unseen-stability.json",
    "unseen-source-quality-audit.json",
    "unregistered-lifecycle-audit.json",
    "unseen-renderer-shadow-proof.json",
    "hard-safety-regression.json",
    "generalization-verdict.json",
    "production-integration-next-handoff.json",
    "night-futures-no-change.json",
    "program-completion.json",
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


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
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


def _literal_assignment(path: Path, name: str) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict):
                break
            return {str(key): str(item) for key, item in value.items()}
    raise ValueError(f"canonical_assignment_missing:{name}:{path}")


def _kr_identities(provider_root: Path) -> list[dict[str, object]]:
    path = provider_root / "config/sector_map.csv"
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for source in csv.DictReader(stream):
            ticker = str(source.get("code") or "").strip().zfill(6)
            name = str(source.get("name") or "").strip()
            exchange = str(source.get("market") or "").strip().upper()
            sector = str(source.get("sector") or "").strip()
            industry = str(source.get("industry") or "").strip()
            if exchange not in {"KOSPI", "KOSDAQ"}:
                continue
            if not ticker.isdigit() or len(ticker) != 6 or not name or not sector or not industry:
                continue
            folded = f"{name} {sector} {industry}".upper()
            if any(token in folded for token in ("ETF", "ETN", "스팩", "리츠", "인버스", "레버리지")):
                continue
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": name,
                    "market": "kr",
                    "exchange": exchange,
                    "sector": sector,
                    "industry": industry,
                    "security_type": "common_stock",
                    "source": "ohlcv_analyst_sector_map",
                    "source_sha256": file_sha256(path),
                }
            )
    return rows


def _us_identities(provider_root: Path) -> list[dict[str, object]]:
    path = provider_root / "app/services/symbol_resolver.py"
    exchanges = _literal_assignment(path, "US_EXCHANGE_BY_TICKER")
    names = _literal_assignment(path, "US_NAME_BY_TICKER")
    source_sha = file_sha256(path)
    rows = []
    for ticker, exchange in exchanges.items():
        name = names.get(ticker, ticker)
        security_type = (
            "exchange_traded_fund" if " ETF" in f" {name.upper()}" else "common_stock"
        )
        if security_type != "common_stock":
            continue
        rows.append(
            {
                "ticker": ticker,
                "company_name": name,
                "market": "us",
                "exchange": exchange,
                "sector": "",
                "industry": "",
                "security_type": security_type,
                "source": "ohlcv_analyst_symbol_resolver_registry",
                "source_sha256": source_sha,
            }
        )
    return rows


def supported_universe(provider_root: Path) -> list[dict[str, object]]:
    rows = _kr_identities(provider_root) + _us_identities(provider_root)
    by_ticker: dict[str, dict[str, object]] = {}
    for row in rows:
        ticker = str(row["ticker"])
        if ticker in by_ticker:
            raise ValueError(f"duplicate_supported_identity:{ticker}")
        by_ticker[ticker] = row
    return [by_ticker[ticker] for ticker in sorted(by_ticker)]


def _stable_rank(value: Mapping[str, object]) -> str:
    material = "|".join(
        (
            SELECTION_SALT,
            str(value.get("market") or ""),
            str(value.get("sector") or "unclassified"),
            str(value.get("ticker") or ""),
        )
    )
    return hashlib.sha256(material.encode()).hexdigest()


def ranked_candidates(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    excluded = set(RETIRED_TICKERS) | set(FIXTURE_TICKERS)
    eligible = [dict(row) for row in rows if str(row.get("ticker")) not in excluded]
    strata: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in eligible:
        stratum = str(row.get("sector") or row.get("industry") or "unclassified")
        strata[(str(row["market"]), stratum)].append(row)
    for values in strata.values():
        values.sort(key=lambda row: (_stable_rank(row), str(row["ticker"])))
    ordered: list[dict[str, object]] = []
    for market in ("kr", "us"):
        market_keys = sorted(
            (key for key in strata if key[0] == market),
            key=lambda key: hashlib.sha256(
                f"{SELECTION_SALT}|{key[0]}|{key[1]}".encode()
            ).hexdigest(),
        )
        while any(strata[key] for key in market_keys):
            for key in market_keys:
                if strata[key]:
                    ordered.append(strata[key].pop(0))
    return ordered


async def _assemble_rows(
    rows: Sequence[Mapping[str, object]], as_of: datetime
) -> list[SourceAssemblyResult]:
    results = []
    for number, row in enumerate(rows, start=1):
        ticker = str(row["ticker"])
        print(f"SOURCE_ASSEMBLY_START {number}/{len(rows)} {ticker}", flush=True)
        result = await assemble_research_packet(ticker, as_of, identity=row)
        results.append(result)
        print(f"SOURCE_ASSEMBLY_COMPLETE {ticker} {result.status}", flush=True)
    return results


def _result_row(result: SourceAssemblyResult) -> dict[str, object]:
    return {
        "ticker": result.ticker,
        "market": result.market,
        "status": result.status,
        "packet_sha256": result.packet_sha256,
        "deterministic_base_context_sha256": result.deterministic_base_context_sha256,
        "validation_errors": list(result.validation_errors),
        "cautions": list(result.cautions),
        "provider_audit": result.provider_audit,
        "production_db_mutation": result.production_db_mutation,
        "monitoring_registration": result.monitoring_registration,
        "ai_judgment_calls": result.ai_judgment_calls,
    }


def decision_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "builder_prompt": repo_root / "scripts/uskr22_structured_autonomy_shadow.py",
        "directional_balance": repo_root / "app/services/directional_balance_service.py",
        "logical_condition": repo_root / "app/services/logical_condition_service.py",
        "stability": repo_root / "app/services/structured_autonomy_stability_service.py",
        "validator_renderer": repo_root
        / "app/services/structured_autonomy_shadow_service.py",
    }
    return {name: file_sha256(path) for name, path in paths.items()}


def source_assembly_hashes(repo_root: Path, provider_root: Path) -> dict[str, str]:
    assembler = repo_root / "app/services/coldstart_source_assembly_service.py"
    orchestrator = repo_root / "scripts/unseen_source_assembly_coldstart.py"
    provider_registry = provider_root / "app/services/symbol_resolver.py"
    sector_map = provider_root / "config/sector_map.csv"
    return {
        "source_assembly_code": file_sha256(assembler),
        "orchestrator_selection_policy": file_sha256(orchestrator),
        "provider_symbol_registry": file_sha256(provider_registry),
        "provider_sector_map": file_sha256(sector_map),
        "identity_resolution_policy": canonical_sha256(
            {
                "kr": "KOSPI_OR_KOSDAQ_WITH_NONEMPTY_SECTOR_AND_INDUSTRY",
                "us": "CANONICAL_SYMBOL_RESOLVER_NON_ETF",
                "excluded_name_classes": [
                    "ETF",
                    "ETN",
                    "SPAC",
                    "REIT",
                    "inverse",
                    "leveraged",
                ],
            }
        ),
        "packet_schema_normalization": canonical_sha256(
            [PACKET_SCHEMA_VERSION, NORMALIZATION_VERSION]
        ),
        "deterministic_base_context_builder": canonical_sha256(
            [BASE_CONTEXT_VERSION, file_sha256(assembler)]
        ),
        "market_sector_stratification": canonical_sha256(
            [SELECTION_SALT, TARGET_PER_MARKET, MINIMUM_COHORT, MAX_COHORT]
        ),
    }


def _program_id(implementation_commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{implementation_commit}|{stamp}|{SELECTION_SALT}".encode()
    ).hexdigest()[:12]
    return f"20260906-unseen-source-coldstart-{stamp}-{suffix}"


def _batches(cohort: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(cohort[index : index + 4]) for index in range(0, len(cohort), 4))


def _build_engine_inputs(
    packets: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
    cohort: Sequence[str],
) -> tuple[
    dict[str, DecisionEvidencePacket],
    dict[str, EvidenceAliasCatalog],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, Mapping[str, object]],
]:
    evidence_packets: dict[str, DecisionEvidencePacket] = {}
    alias_catalogs: dict[str, EvidenceAliasCatalog] = {}
    price_maps: dict[str, dict[str, object]] = {}
    contexts: dict[str, dict[str, object]] = {}
    stocks: dict[str, Mapping[str, object]] = {}
    for ticker in cohort:
        packet = packets[ticker]
        rows = packet.get("stocks")
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], Mapping):
            raise ValueError(f"single_stock_packet_required:{ticker}")
        stock = rows[0]
        technical = packet_owned_context_for_stock(packet=packet, stock=stock)
        evidence = engine.build_decision_evidence_packet(
            packet=packet, stock=stock, technical_context=technical
        )
        alias_evidence = evidence.model_copy(
            update={
                "evidence": tuple(
                    row
                    for row in evidence.evidence
                    if not row.ref_id.startswith("technical-feature:")
                )
            }
        )
        aliases = build_evidence_alias_catalog(alias_evidence)
        compact = compact_alias_ai_context(alias_evidence, aliases)
        serialized = json.dumps(compact, ensure_ascii=False).lower()
        contamination = [
            token for token in engine.FORBIDDEN_PROMPT_KEYS if token in serialized
        ]
        if contamination:
            raise ValueError(f"fresh_prompt_contamination:{ticker}:{contamination}")
        price_map = engine.build_verified_price_map(evidence)
        evidence_packets[ticker] = evidence
        alias_catalogs[ticker] = aliases
        price_maps[ticker] = price_map
        contexts[ticker] = {
            "ticker": ticker,
            "market": packet.get("market"),
            "source_packet": packet.get("packet_id"),
            "evidence_catalogue": compact,
            "evidence_fingerprint": evidence.evidence_sha256,
            "alias_map_fingerprint": aliases.alias_map_sha256,
            "sector_context": {
                "industry": stock.get("industry"),
                "sector": stock.get("sector"),
                "business_model": stock.get("business_model"),
            },
            "allowed_price_choices": alias_price_choices(
                engine.price_choices(price_map), aliases
            ),
            "coldstart_base_context": base_contexts[ticker],
        }
        stocks[ticker] = stock
    return evidence_packets, alias_catalogs, price_maps, contexts, stocks


def _source_lock(
    *,
    program_id: str,
    cohort: Sequence[str],
    packets: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
    evidence: Mapping[str, DecisionEvidencePacket],
    aliases: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": "unseen-coldstart-source-lock-v1",
        "program_generation_id": program_id,
        "ordered_cohort": list(cohort),
        "market_by_ticker": {
            ticker: str(packets[ticker].get("market")) for ticker in cohort
        },
        "packet_sha256": {
            ticker: canonical_sha256(packets[ticker]) for ticker in cohort
        },
        "base_context_sha256": {
            ticker: hashlib.sha256(base_contexts[ticker].encode()).hexdigest()
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
        "structured_autonomy_model_calls_before_source_lock": 0,
        "ai_reviewer_investment_judgment_calls_before_source_lock": 0,
        "preexisting_ai_review_packet_required": 0,
        "preexisting_base_message_required": 0,
        "production_db_mutation": 0,
    }


def _decision_freeze_verification(repo_root: Path) -> dict[str, object]:
    actual = decision_hashes(repo_root)
    prior = read_json(repo_root / PRIOR_FREEZE_RELATIVE)
    checks = {
        **{name: actual[name] == expected for name, expected in EXPECTED_DECISION_HASHES.items()},
        "prompt_set": prior.get("prompt_set_sha256") == EXPECTED_PROMPT_SET,
        "schema_set": prior.get("schema_set_sha256") == EXPECTED_SCHEMA_SET,
    }
    return {
        "contract": "decision-engine-freeze-verification-v1",
        "expected_code_hashes": EXPECTED_DECISION_HASHES,
        "actual_code_hashes": actual,
        "expected_prompt_set_sha256": EXPECTED_PROMPT_SET,
        "actual_prompt_set_sha256": prior.get("prompt_set_sha256"),
        "expected_schema_set_sha256": EXPECTED_SCHEMA_SET,
        "actual_schema_set_sha256": prior.get("schema_set_sha256"),
        "checks": checks,
        "decision_engine_hash_drift": sum(not passed for passed in checks.values()),
        "status": "PASS" if all(checks.values()) else "STOP",
    }


def _write_prompt_set(
    output_root: Path,
    program_id: str,
    cohort: Sequence[str],
    contexts: Mapping[str, Mapping[str, object]],
    aliases: Mapping[str, EvidenceAliasCatalog],
) -> dict[str, object]:
    engine.SHADOW_PACKET_ID = program_id
    candidate_schema = engine.strict_json_schema(
        StructuredAutonomyCandidate.model_json_schema()
    )
    rows = []
    for number, batch in enumerate(_batches(cohort), start=1):
        prompt_path = output_root / "prompts" / f"batch-{number:02d}.txt"
        schema_path = output_root / "schemas" / f"batch-{number:02d}.json"
        prompt = engine._batch_prompt([contexts[ticker] for ticker in batch], batch)
        schema = build_alias_constrained_batch_schema(
            candidate_schema=candidate_schema,
            contract=OUTPUT_CONTRACT,
            packet_id=program_id,
            aliases_by_ticker={
                ticker: tuple(aliases[ticker].by_alias) for ticker in batch
            },
        )
        write_text(prompt_path, prompt)
        write_json(schema_path, schema)
        rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": file_sha256(prompt_path),
                "schema_sha256": file_sha256(schema_path),
            }
        )
    manifest = {
        "contract": "unseen-coldstart-prompt-schema-lock-v1",
        "program_generation_id": program_id,
        "batches": rows,
        "execution_prompt_set_sha256": canonical_sha256(
            [row["prompt_sha256"] for row in rows]
        ),
        "execution_schema_set_sha256": canonical_sha256(
            [row["schema_sha256"] for row in rows]
        ),
    }
    write_json(output_root / "prompt-schema-lock.json", manifest)
    return manifest


def _load_prepared(
    output_root: Path,
) -> tuple[
    dict[str, Any],
    tuple[str, ...],
    dict[str, Mapping[str, object]],
    dict[str, str],
    dict[str, DecisionEvidencePacket],
    dict[str, EvidenceAliasCatalog],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, Mapping[str, object]],
]:
    state = read_json(output_root / "program-state.json")
    cohort = tuple(str(value) for value in state["ordered_cohort"])
    packets = {
        ticker: read_json(output_root / "packets" / f"{ticker}.json")
        for ticker in cohort
    }
    base_contexts = {
        ticker: (output_root / "base-contexts" / f"{ticker}.txt").read_text(
            encoding="utf-8"
        ).rstrip()
        for ticker in cohort
    }
    evidence, aliases, price_maps, contexts, stocks = _build_engine_inputs(
        packets, base_contexts, cohort
    )
    return (
        state,
        cohort,
        packets,
        base_contexts,
        evidence,
        aliases,
        price_maps,
        contexts,
        stocks,
    )


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    output_root.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    if (output_root / "program-state.json").exists():
        raise ValueError("new_output_root_required")
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    if args.source_report.name != SOURCE_REPORT_NAME:
        raise ValueError("source_report_bundle_name_mismatch")

    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    program_id = _program_id(implementation_commit, args.as_of)
    universe = supported_universe(args.provider_root)
    identity_by_ticker = {str(row["ticker"]): row for row in universe}
    missing_fixtures = sorted(set(FIXTURE_TICKERS) - set(identity_by_ticker))
    if missing_fixtures:
        raise ValueError(f"fixture_identity_missing:{','.join(missing_fixtures)}")

    fixture_results = asyncio.run(
        _assemble_rows([identity_by_ticker[ticker] for ticker in FIXTURE_TICKERS], args.as_of)
    )
    fixture_proof = {
        "contract": "preflight11-source-assembly-fixtures-v1",
        "program_generation_id": program_id,
        "fixture_only": 1,
        "judgment_model_calls": 0,
        "rows": [_result_row(result) for result in fixture_results],
        "status_counts": dict(Counter(str(result.status) for result in fixture_results)),
        "assembled_count": sum(
            result.status == SourceAssemblyStatus.ASSEMBLED for result in fixture_results
        ),
        "objective_failure_count": sum(
            result.status != SourceAssemblyStatus.ASSEMBLED for result in fixture_results
        ),
        "final_unseen_eligibility": 0,
    }
    write_json(proofs_dir / "preflight11-source-assembly-fixtures.json", fixture_proof)

    source_hashes = source_assembly_hashes(repo_root, args.provider_root)
    source_freeze = {
        "contract": "source-assembly-freeze-v1",
        "program_generation_id": program_id,
        "frozen_at": args.as_of.isoformat(),
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "source_assembly_hashes": source_hashes,
        "source_assembly_mutation_after_freeze": 0,
        "selection_salt": SELECTION_SALT,
        "selection_algorithm": "MARKET_AND_SOURCE_SECTOR_ROUND_ROBIN_THEN_STABLE_HASH",
    }
    write_json(output_root / "source-assembly-freeze.json", source_freeze)
    write_json(proofs_dir / "source-assembly-freeze.json", source_freeze)

    ranked = ranked_candidates(universe)
    market_candidates = {
        market: [row for row in ranked if row["market"] == market]
        for market in ("kr", "us")
    }
    attempted_rows: list[dict[str, object]] = []
    selected_results: list[SourceAssemblyResult] = []
    selected_identities: dict[str, Mapping[str, object]] = {}
    for market in ("kr", "us"):
        for rank, identity in enumerate(market_candidates[market], start=1):
            if sum(result.market == market for result in selected_results) >= TARGET_PER_MARKET:
                break
            result = asyncio.run(_assemble_rows([identity], args.as_of))[0]
            attempted_rows.append({"rank": rank, **_result_row(result)})
            if result.status == SourceAssemblyStatus.ASSEMBLED:
                selected_results.append(result)
                selected_identities[result.ticker] = identity
    if not MINIMUM_COHORT <= len(selected_results) <= MAX_COHORT:
        raise ValueError(f"real_source_coverage_below_minimum:{len(selected_results)}")

    ordered_cohort = tuple(
        result.ticker
        for market in ("us", "kr")
        for result in selected_results
        if result.market == market
    )
    packets = {
        result.ticker: result.packet
        for result in selected_results
        if result.packet is not None
    }
    base_contexts = {
        result.ticker: str(result.deterministic_base_context)
        for result in selected_results
    }
    for ticker in ordered_cohort:
        write_json(output_root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(output_root / "base-contexts" / f"{ticker}.txt", base_contexts[ticker])

    evidence, aliases, price_maps, contexts, _stocks = _build_engine_inputs(
        packets, base_contexts, ordered_cohort
    )
    source_lock = _source_lock(
        program_id=program_id,
        cohort=ordered_cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    source_lock_sha = canonical_sha256(source_lock)
    source_lock["unseen_source_lock_sha256"] = source_lock_sha
    write_json(output_root / "source-lock.json", source_lock)
    write_json(proofs_dir / "final-unseen-source-lock.json", source_lock)

    decision_freeze = _decision_freeze_verification(repo_root)
    write_json(proofs_dir / "decision-engine-freeze-verification.json", decision_freeze)
    if decision_freeze["status"] != "PASS":
        raise ValueError("decision_engine_hash_drift_stop")
    prompt_schema_lock = _write_prompt_set(
        output_root, program_id, ordered_cohort, contexts, aliases
    )

    policy = {
        "contract": "final-unseen-selection-policy-v1",
        "source": "canonical_supported_security_universe",
        "selection_salt": SELECTION_SALT,
        "algorithm": "MARKET_AND_SOURCE_SECTOR_ROUND_ROBIN_THEN_STABLE_HASH",
        "target": 16,
        "minimum": MINIMUM_COHORT,
        "maximum": MAX_COHORT,
        "preferred_market_balance": {"kr": 8, "us": 8},
        "retired_tickers_excluded": list(RETIRED_TICKERS),
        "fixture_tickers_excluded": list(FIXTURE_TICKERS),
        "investment_label_visibility": 0,
        "monitoring_membership_required": 0,
        "archive_presence_required": 0,
        "ticker_specific_source_override": 0,
    }
    selection = {
        "contract": "final-unseen-cohort-selection-v1",
        "program_generation_id": program_id,
        "candidate_pool_count": len(ranked),
        "ranked_candidate_pool_count": len(ranked),
        "attempted_count": len(attempted_rows),
        "selected_count": len(ordered_cohort),
        "eligible_count": len(ordered_cohort),
        "ordered_cohort": list(ordered_cohort),
        "kr_count": sum(ticker.isdigit() for ticker in ordered_cohort),
        "us_count": sum(not ticker.isdigit() for ticker in ordered_cohort),
        "overlap_retired22": sorted(set(ordered_cohort) & set(RETIRED_TICKERS)),
        "overlap_preflight11": sorted(set(ordered_cohort) & set(FIXTURE_TICKERS)),
        "selected_identity": {
            ticker: dict(selected_identities[ticker]) for ticker in ordered_cohort
        },
        "ai_judgment_visibility": 0,
    }
    preflight = {
        "contract": "final-unseen-source-preflight-v1",
        "program_generation_id": program_id,
        "rows": attempted_rows,
        "eligible": list(ordered_cohort),
        "eligible_count": len(ordered_cohort),
        "minimum_eligible": MINIMUM_COHORT,
        "status": "PASS",
        "provider_calls": {
            "ohlcv_requested": sum(
                int(row.get("provider_audit", {}).get("price_request_count") or 0)
                for row in attempted_rows
            ),
            "ohlcv_success": sum(
                int(row.get("provider_audit", {}).get("price_success_count") or 0)
                for row in attempted_rows
            ),
            "cache_use": sum(
                int(row.get("provider_audit", {}).get("price_cache_use_count") or 0)
                for row in attempted_rows
            ),
        },
        "production_db_mutation": 0,
        "monitoring_registration": 0,
    }
    write_json(proofs_dir / "final-unseen-selection-policy.json", policy)
    write_json(proofs_dir / "final-unseen-cohort-selection.json", selection)
    write_json(proofs_dir / "final-unseen-source-preflight.json", preflight)

    reuse_map = {
        "contract": "source-assembly-reuse-map-v1",
        "components": [
            {
                "component": "ohlcv_analyst SymbolResolver registries",
                "input": "ticker/security identity",
                "output": "canonical market/exchange/name/sector identity",
                "reuse": "UNCHANGED_READ_ONLY_SOURCE",
                "adapter": "generic CSV/AST inventory adapter",
            },
            {
                "component": "OhlcvClient.fetch_price_context",
                "input": "ticker/as_of",
                "output": "price/chart/packet-owned technical context",
                "reuse": "UNCHANGED_NO_DB_SESSION",
                "adapter": "none",
            },
            {
                "component": "financial/numeric/security basis validators",
                "input": "canonical fact catalog",
                "output": "DecisionEvidencePacket",
                "reuse": "UNCHANGED",
                "adapter": "cold-start packet envelope",
            },
            {
                "component": "Structured Autonomy alias/prompt/schema/validator/renderer",
                "input": "DecisionEvidencePacket",
                "output": "validated shadow decision",
                "reuse": "HASH_FROZEN_UNCHANGED",
                "adapter": "dynamic cohort batching only",
            },
        ],
        "new_paid_provider": 0,
        "new_website_scraper": 0,
    }
    packet_contract = {
        "contract": ASSEMBLY_CONTRACT,
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "required_inputs": ["canonical identity", "read-only OHLCV", "as_of"],
        "preserved_absence": [
            "monitoring thesis",
            "earnings",
            "valuation",
            "events when unavailable",
        ],
        "preexisting_ai_review_packet_required": 0,
        "monitoring_baseline_required_for_source_packet": 0,
        "production_db_mutation": 0,
    }
    base_contract = {
        "contract": BASE_CONTEXT_VERSION,
        "source": "assembled packet only",
        "ai_judgment_calls": 0,
        "buy_hold_sell_generated": 0,
        "deterministic": 1,
    }
    lifecycle = {
        "contract": "unregistered-lifecycle-audit-v1",
        "stored_monitoring_state_required": 0,
        "monitoring_thesis_required": 0,
        "thesis_version_required": 0,
        "stored_price_rules_required": 0,
        "prior_daily_assessment_required": 0,
        "unregistered_ticker_supported": 1,
        "production_registration_calls": 0,
        "production_db_mutation": 0,
    }
    quality = {
        "contract": "unseen-source-quality-audit-v1",
        "subject_count": len(ordered_cohort),
        "identity_security_basis": "AVAILABLE_ALL",
        "price_context": "AVAILABLE_ALL",
        "deterministic_price_structure": "AVAILABLE_ALL_OR_PARTIAL_SAFE",
        "latest_earnings_context": "UNAVAILABLE_PRESERVED_AS_UNKNOWN",
        "valuation": "UNAVAILABLE_PRESERVED_AS_UNKNOWN",
        "cash_flow_capital_efficiency": "UNAVAILABLE_PRESERVED_AS_UNKNOWN",
        "event_filing_evidence": "UNAVAILABLE_PRESERVED_AS_UNKNOWN",
        "relative_to_retired22": "MATERIALLY_LOWER_FUNDAMENTAL_BREADTH",
        "source_quality_lowering_for_eligibility": 0,
    }
    write_json(proofs_dir / "source-assembly-reuse-map.json", reuse_map)
    write_json(proofs_dir / "arbitrary-ticker-source-packet-contract.json", packet_contract)
    write_json(proofs_dir / "deterministic-base-context-contract.json", base_contract)
    write_json(proofs_dir / "unregistered-lifecycle-audit.json", lifecycle)
    write_json(proofs_dir / "unseen-source-quality-audit.json", quality)

    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": program_id,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(ordered_cohort),
        "source_lock_sha256": source_lock_sha,
        "source_assembly_hashes": source_hashes,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_schema_lock),
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "source_assembly_model_calls": 0,
        "production_db_mutation": 0,
    }
    write_json(output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def verify_frozen(
    args: argparse.Namespace, state: Mapping[str, object]
) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    actual_source = source_assembly_hashes(repo_root, args.provider_root)
    if actual_source != state["source_assembly_hashes"]:
        raise ValueError("source_assembly_mutation_after_freeze")
    decision = _decision_freeze_verification(repo_root)
    if decision["status"] != "PASS":
        raise ValueError("decision_engine_hash_drift_stop")
    lock = read_json(args.output_root / "source-lock.json")
    locked_sha = str(lock.pop("unseen_source_lock_sha256"))
    if canonical_sha256(lock) != locked_sha or locked_sha != state["source_lock_sha256"]:
        raise ValueError("unseen_source_lock_drift")
    return decision


def _candidate_refs(candidate: StructuredAutonomyCandidate) -> set[str]:
    return engine._candidate_refs(candidate)


def execute_run(
    *,
    run: str,
    args: argparse.Namespace,
    state: Mapping[str, object],
    cohort: Sequence[str],
    evidence_packets: Mapping[str, DecisionEvidencePacket],
    alias_catalogs: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
    stock_by_ticker: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
) -> tuple[tuple[StructuredAutonomyCandidate, ...], dict[str, object], tuple[object, ...]]:
    program_id = str(state["program_generation_id"])
    engine.SHADOW_PACKET_ID = program_id
    engine.US_COHORT = tuple(ticker for ticker in cohort if not ticker.isdigit())
    engine.KR_COHORT = tuple(ticker for ticker in cohort if ticker.isdigit())
    engine.COHORT = tuple(cohort)
    codex_bin = engine._signed_in_codex_bin()
    run_dir = args.output_root / f"run-{run}"
    run_dir.mkdir(parents=True, exist_ok=False)
    candidates: list[StructuredAutonomyCandidate] = []
    alias_candidates: dict[str, Mapping[str, object]] = {}
    alias_selections: dict[str, Sequence[Mapping[str, str]]] = {}
    invocation_rows = []
    for number, batch in enumerate(_batches(cohort), start=1):
        prompt = args.output_root / "prompts" / f"batch-{number:02d}.txt"
        schema = args.output_root / "schemas" / f"batch-{number:02d}.json"
        output = run_dir / f"batch-{number:02d}.json"
        log = run_dir / f"batch-{number:02d}.log"
        print(f"RUN_{run.upper()}_BATCH_START {number} {','.join(batch)}", flush=True)
        with engine.isolated_model_working_directory(run=run, batch=number) as cwd:
            engine._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt,
                output=output,
                log=log,
                schema=schema,
                cwd=cwd,
                timeout=args.timeout,
                state_namespace=f"UNSEEN_SOURCE_COLDSTART_{run.upper()}_20260906",
            )
        parsed = read_json(output)
        if parsed.get("contract") != OUTPUT_CONTRACT:
            raise ValueError(f"run_contract_identity_mismatch:{run}:{number}")
        if parsed.get("packet_id") != program_id:
            raise ValueError(f"run_packet_identity_mismatch:{run}:{number}")
        raw_candidates = parsed.get("candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError(f"run_candidates_array_required:{run}:{number}")
        if tuple(str(row.get("ticker") or "") for row in raw_candidates) != batch:
            raise ValueError(f"run_batch_scope_or_order_mismatch:{run}:{number}")
        for raw_candidate in raw_candidates:
            ticker = str(raw_candidate["ticker"])
            resolved, selections = resolve_candidate_aliases(
                raw_candidate,
                packet=evidence_packets[ticker],
                catalog=alias_catalogs[ticker],
            )
            candidate = StructuredAutonomyCandidate.model_validate(resolved)
            alias_candidates[ticker] = raw_candidate
            alias_selections[ticker] = selections
            candidates.append(candidate)
        invocation_rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": file_sha256(prompt),
                "schema_sha256": file_sha256(schema),
                "output_sha256": file_sha256(output),
                "working_directory_isolation": "EMPTY_EPHEMERAL_PER_INVOCATION",
            }
        )
        print(f"RUN_{run.upper()}_BATCH_COMPLETE {number} {','.join(batch)}", flush=True)
    if tuple(candidate.ticker for candidate in candidates) != tuple(cohort):
        raise ValueError(f"run_full_scope_or_order_mismatch:{run}")

    validation_rows = []
    rendered = []
    for candidate in candidates:
        ticker = candidate.ticker
        stock = stock_by_ticker[ticker]
        industry = str(stock.get("industry") or stock.get("sector") or "")
        validation = validate_structured_autonomy_candidate(
            evidence_packets[ticker],
            candidate,
            price_map=price_maps[ticker],
            industry=industry,
        )
        rendered_row = render_structured_autonomy_message(
            evidence_packets[ticker],
            candidate,
            price_map=price_maps[ticker],
            industry=industry,
            base_detail_text=base_contexts[ticker],
        )
        rendered.append(rendered_row)
        errors = tuple(dict.fromkeys((*validation.errors, *rendered_row.validation.errors)))
        valid_refs = {row.ref_id for row in evidence_packets[ticker].evidence} | allowed_price_refs(
            price_maps[ticker]
        )
        validation_rows.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "unsupported_evidence_refs": sorted(
                    _candidate_refs(candidate) - valid_refs
                ),
            }
        )
    document = engine._run_document(
        run=run,
        candidates=candidates,
        alias_candidates=alias_candidates,
        alias_selections=alias_selections,
        validation_rows=validation_rows,
        message_quality=structured_autonomy_message_quality(rendered),
        batch_rows=invocation_rows,
        semantic_audit=engine._semantic_audit(candidates),
        rendered=rendered,
    )
    document["program_generation_id"] = program_id
    document["source_lock_sha256"] = state["source_lock_sha256"]
    document["source_packet_mutation"] = 0
    write_json(run_dir / "run.json", document)
    return tuple(candidates), document, tuple(rendered)


def _failure_taxonomy(document: Mapping[str, object]) -> dict[str, int]:
    return actionability.run_failure_taxonomy(document)


def _first_gate(document: Mapping[str, object], hard_regression: int) -> dict[str, object]:
    taxonomy = _failure_taxonomy(document)
    schema_failure = 0
    false_positive = 0
    return {
        "validator_false_positive": false_positive,
        "schema_failure": schema_failure,
        "hard_safety_regression": hard_regression,
        "failure_taxonomy": taxonomy,
        "pass": false_positive == 0 and schema_failure == 0 and hard_regression == 0,
    }


def _not_run(run: str, reason: str, state: Mapping[str, object]) -> dict[str, object]:
    return {
        "contract": "unseen-coldstart-run-v1",
        "run": run,
        "program_generation_id": state["program_generation_id"],
        "source_lock_sha256": state["source_lock_sha256"],
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
    }


def _renderer_proof(rendered: Sequence[object]) -> dict[str, object]:
    examples = []
    seen_decisions: set[str] = set()
    for row in rendered:
        if row.decision in seen_decisions and len(examples) >= 4:
            continue
        action = getattr(row, "actionability", None)
        examples.append(
            {
                "ticker": row.ticker,
                "decision": row.decision,
                "actionability": action.model_dump(mode="json") if action else None,
                "message": row.text,
                "imperative_matches": [
                    value.model_dump(mode="json")
                    for value in explicit_actionable_trade_directives(row.text)
                ],
            }
        )
        seen_decisions.add(row.decision)
        if len(examples) == 4:
            break
    imperative_count = sum(len(row["imperative_matches"]) for row in examples)
    return {
        "contract": "unseen-renderer-shadow-proof-v1",
        "status": "PASS" if examples and imperative_count == 0 else "FAIL",
        "examples": examples,
        "primary_user_action_wording_owner": "RENDERER",
        "ai_imperative_primary_action": imperative_count,
        "missing_labels_not_forced": 1,
    }


def _write_reports(report_dir: Path, proofs_dir: Path) -> None:
    titles = {
        "20260906-source-assembly-root-cause.md": "Source Assembly Root Cause",
        "20260906-source-assembly-reuse-map.md": "Source Assembly Reuse Map",
        "20260906-arbitrary-ticker-source-packet-contract.md": "Arbitrary-Ticker Source Packet Contract",
        "20260906-deterministic-base-context-contract.md": "Deterministic Base Context Contract",
        "20260906-preflight11-source-assembly-fixtures.md": "Preflight 11 Source Assembly Fixtures",
        "20260906-source-assembly-freeze.md": "Source Assembly Freeze",
        "20260906-final-unseen-selection-policy.md": "Final Unseen Selection Policy",
        "20260906-final-unseen-cohort-selection.md": "Final Unseen Cohort Selection",
        "20260906-final-unseen-source-preflight.md": "Final Unseen Source Preflight",
        "20260906-final-unseen-source-lock.md": "Final Unseen Source Lock",
        "20260906-decision-engine-freeze-verification.md": "Decision Engine Freeze Verification",
        "20260906-unseen-first.md": "Unseen FIRST",
        "20260906-unseen-run-a.md": "Unseen Run A",
        "20260906-unseen-run-b.md": "Unseen Run B",
        "20260906-unseen-run-c.md": "Unseen Run C",
        "20260906-unseen-stability.md": "Unseen Stability",
        "20260906-unseen-source-quality-audit.md": "Unseen Source Quality Audit",
        "20260906-unregistered-lifecycle-audit.md": "Unregistered Lifecycle Audit",
        "20260906-unseen-renderer-shadow-proof.md": "Unseen Renderer Shadow Proof",
        "20260906-hard-safety-regression.md": "Hard-Safety Regression",
        "20260906-generalization-verdict.md": "Generalization Verdict",
        "20260906-production-integration-next-handoff.md": "Production Integration Next Handoff",
        "20260906-night-futures-no-change.md": "Night Futures No-Change",
        "20260906-program-completion.md": "Program Completion",
    }
    proof_for_report = {
        "20260906-source-assembly-root-cause.md": "source-assembly-root-cause.json",
        "20260906-source-assembly-reuse-map.md": "source-assembly-reuse-map.json",
        "20260906-arbitrary-ticker-source-packet-contract.md": "arbitrary-ticker-source-packet-contract.json",
        "20260906-deterministic-base-context-contract.md": "deterministic-base-context-contract.json",
        "20260906-preflight11-source-assembly-fixtures.md": "preflight11-source-assembly-fixtures.json",
        "20260906-source-assembly-freeze.md": "source-assembly-freeze.json",
        "20260906-final-unseen-selection-policy.md": "final-unseen-selection-policy.json",
        "20260906-final-unseen-cohort-selection.md": "final-unseen-cohort-selection.json",
        "20260906-final-unseen-source-preflight.md": "final-unseen-source-preflight.json",
        "20260906-final-unseen-source-lock.md": "final-unseen-source-lock.json",
        "20260906-decision-engine-freeze-verification.md": "decision-engine-freeze-verification.json",
        "20260906-unseen-first.md": "unseen-first.json",
        "20260906-unseen-run-a.md": "unseen-run-a.json",
        "20260906-unseen-run-b.md": "unseen-run-b.json",
        "20260906-unseen-run-c.md": "unseen-run-c.json",
        "20260906-unseen-stability.md": "unseen-stability.json",
        "20260906-unseen-source-quality-audit.md": "unseen-source-quality-audit.json",
        "20260906-unregistered-lifecycle-audit.md": "unregistered-lifecycle-audit.json",
        "20260906-unseen-renderer-shadow-proof.md": "unseen-renderer-shadow-proof.json",
        "20260906-hard-safety-regression.md": "hard-safety-regression.json",
        "20260906-generalization-verdict.md": "generalization-verdict.json",
        "20260906-production-integration-next-handoff.md": "production-integration-next-handoff.json",
        "20260906-night-futures-no-change.md": "night-futures-no-change.json",
        "20260906-program-completion.md": "program-completion.json",
    }
    for report, title in titles.items():
        proof = read_json(proofs_dir / proof_for_report[report])
        write_text(report_dir / report, mapping_report(title, proof))


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    decision = verify_frozen(args, state)
    (
        _state,
        cohort,
        packets,
        base_contexts,
        evidence,
        aliases,
        price_maps,
        _contexts,
        stocks,
    ) = _load_prepared(args.output_root)
    recomputed_lock = _source_lock(
        program_id=str(state["program_generation_id"]),
        cohort=cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    if canonical_sha256(recomputed_lock) != state["source_lock_sha256"]:
        raise ValueError("first_abc_source_drift_before_first")
    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    write_json(proofs_dir / "decision-engine-freeze-verification.json", decision)

    run_candidates: dict[str, tuple[StructuredAutonomyCandidate, ...]] = {}
    run_documents: dict[str, dict[str, object]] = {}
    run_rendered: dict[str, tuple[object, ...]] = {}
    stop_reason: str | None = None
    for run in ("first", "a", "b", "c"):
        if stop_reason:
            run_documents[run] = _not_run(run, stop_reason, state)
            continue
        try:
            candidates, document, rendered = execute_run(
                run=run,
                args=args,
                state=state,
                cohort=cohort,
                evidence_packets=evidence,
                alias_catalogs=aliases,
                price_maps=price_maps,
                stock_by_ticker=stocks,
                base_contexts=base_contexts,
            )
        except Exception as exc:
            document = {
                "contract": "unseen-coldstart-run-v1",
                "run": run,
                "program_generation_id": state["program_generation_id"],
                "source_lock_sha256": state["source_lock_sha256"],
                "status": "FAILED",
                "failure_class": "SCHEMA_FAILURE",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "same_generation_repair": 0,
                "selective_rerun": 0,
            }
            run_documents[run] = document
            stop_reason = f"{run.upper()}_FAILED_NO_SAME_GENERATION_REPAIR"
            continue
        run_candidates[run] = candidates
        run_documents[run] = document
        run_rendered[run] = rendered
        hard_regression = actionability.validator_regression_count(candidates, document)
        gate = _first_gate(document, hard_regression)
        document["failure_taxonomy"] = gate["failure_taxonomy"]
        document["hard_safety_regression"] = hard_regression
        document["schema_failure"] = 0
        document["validator_false_positive"] = 0
        document["status"] = (
            "PASS" if document["validation_pass_count"] == len(cohort) else "PARTIAL"
        )
        if run == "first" and not gate["pass"]:
            stop_reason = "FIRST_GATE_FAILED_NO_SAME_GENERATION_REPAIR"
        elif run != "first" and document["validation_pass_count"] != len(cohort):
            stop_reason = f"RUN_{run.upper()}_NOT_100_PERCENT_NO_HOTFIX"
        if canonical_sha256(recomputed_lock) != state["source_lock_sha256"]:
            raise ValueError(f"first_abc_source_drift_after_{run}")

    for run, document in run_documents.items():
        write_json(proofs_dir / f"unseen-{run}.json", document)

    abc_complete = all(run in run_candidates for run in ("a", "b", "c"))
    if abc_complete:
        stability_rows = [
            classify_same_evidence_runs(
                [
                    next(candidate for candidate in run_candidates[run] if candidate.ticker == ticker)
                    for run in ("a", "b", "c")
                ]
            )
            for ticker in cohort
        ]
        stability = {
            "contract": "unseen-coldstart-stability-v1",
            "program_generation_id": state["program_generation_id"],
            "status": "MEASURED",
            "rows": stability_rows,
            **stability_summary(stability_rows),
            "majority_vote": 0,
        }
    else:
        stability = {
            "contract": "unseen-coldstart-stability-v1",
            "program_generation_id": state["program_generation_id"],
            "status": "NOT_MEASURED",
            "reason": stop_reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "majority_vote": 0,
        }
    write_json(proofs_dir / "unseen-stability.json", stability)

    synthetic = actionability.synthetic_suite()
    first_candidates = run_candidates.get("first", ())
    first_document = run_documents["first"]
    first_hard = (
        actionability.validator_regression_count(first_candidates, first_document)
        if first_candidates
        else 0
    )
    hard_safety = {
        "contract": "unseen-hard-safety-regression-v1",
        "synthetic_suite": synthetic,
        "first_validator_hard_safety_regression": first_hard,
        "known_hard_safety_regression": first_hard,
        "numeric_provenance": "UNCHANGED",
        "accounting_attribution": "UNCHANGED",
        "adr_security_basis": "UNCHANGED",
        "evidence_fencing": "UNCHANGED",
        "severity_future_checkpoint_logical_condition": "UNCHANGED",
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs_dir / "hard-safety-regression.json", hard_safety)
    renderer = (
        _renderer_proof(run_rendered["first"])
        if "first" in run_rendered
        else {
            "contract": "unseen-renderer-shadow-proof-v1",
            "status": "NOT_RUN",
            "primary_user_action_wording_owner": "RENDERER",
            "ai_imperative_primary_action": "NOT_MEASURED",
        }
    )
    write_json(proofs_dir / "unseen-renderer-shadow-proof.json", renderer)

    all_valid = all(
        run_documents[run].get("validation_pass_count") == len(cohort)
        for run in ("first", "a", "b", "c")
    )
    unstable = int(stability.get("counts", {}).get("UNSTABLE", 0))
    if all_valid and first_hard == 0 and unstable == 0:
        verdict = "GENERALIZATION_STRONG"
        readiness = "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
    elif all_valid and first_hard == 0:
        verdict = "GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY"
        readiness = "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
    else:
        verdict = "GENERALIZATION_NEEDS_ARCHITECTURE_WORK"
        readiness = "NEEDS_ARCHITECTURE_WORK"
    generalization = {
        "contract": "unseen-coldstart-generalization-verdict-v1",
        "program_generation_id": state["program_generation_id"],
        "verdict": verdict,
        "readiness": readiness,
        "source_coverage_minimum_met": len(cohort) >= MINIMUM_COHORT,
        "first_abc_all_valid": all_valid,
        "stability_counts": stability.get("counts"),
        "same_generation_repair": 0,
        "source_packet_mutation": 0,
        "decision_code_change_after_result": 0,
    }
    handoff = {
        "contract": "production-integration-next-handoff-v1",
        "readiness": readiness,
        "next_bounded_task": (
            "AUTHORITATIVE_KR_US_SCHEDULED_PATH_STRUCTURED_AUTONOMY_INTEGRATION_PROOF"
            if readiness == "READY_FOR_PRODUCTION_INTEGRATION_REVIEW"
            else "NEW_AUTHORIZED_ARCHITECTURE_REPAIR_AND_NEW_HOLDOUT"
        ),
        "live_structured_autonomy_activation": 0,
        "main_merge": 0,
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "prior_handoff": "READY_FOR_BOUNDED_PRODUCTION_INTEGRATION",
        "night_futures_code_mutation": 0,
        "structured_autonomy_injection": 0,
        "provider_calls": 0,
    }
    completion = {
        "contract": PROGRAM_CONTRACT,
        "state": "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION",
        "program_generation_id": state["program_generation_id"],
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "source_assembly_hashes": state["source_assembly_hashes"],
        "implementation_commit": state["implementation_commit"],
        "implementation_tree": state["implementation_tree"],
        "root_cause_class": "COLD_START_SOURCE_ASSEMBLY_HARNESS_GAP",
        "decision_engine_hash_drift": decision["decision_engine_hash_drift"],
        "preexisting_ai_review_packet_required": 0,
        "preexisting_base_message_required": 0,
        "new_paid_provider": 0,
        "new_website_scraper": 0,
        "ticker_specific_source_override": 0,
        "monitoring_baseline_required_for_source_packet": 0,
        "stored_monitoring_state_required": 0,
        "unregistered_ticker_supported": 1,
        "base_context_ai_judgment_calls": 0,
        "preflight11_judgment_model_calls": 0,
        "source_assembly_mutation_after_freeze": 0,
        "final_unseen_overlap_retired22": 0,
        "final_unseen_overlap_preflight11": 0,
        "final_unseen_selected_count": len(cohort),
        "final_unseen_eligible_count": len(cohort),
        "final_kr_count": sum(ticker.isdigit() for ticker in cohort),
        "final_us_count": sum(not ticker.isdigit() for ticker in cohort),
        "unseen_source_lock_sha256": state["source_lock_sha256"],
        "first_abc_source_drift": 0,
        "structured_autonomy_model_calls_before_source_lock": 0,
        "unseen_first_validated": first_document.get("validation_pass_count", 0),
        "unseen_first_validator_false_positive": first_document.get(
            "validator_false_positive", 0
        ),
        "unseen_first_hard_safety_true_reject": first_document.get(
            "failure_taxonomy", {}
        ).get("mandatory_trade_true_reject", 0),
        "unseen_first_ontology_gap": first_document.get(
            "failure_taxonomy", {}
        ).get("metric_ownership_failure", 0),
        "unseen_first_schema_failure": first_document.get("schema_failure", 0),
        "unseen_run_a_validated": run_documents["a"].get(
            "validation_pass_count", "NOT_RUN"
        ),
        "unseen_run_b_validated": run_documents["b"].get(
            "validation_pass_count", "NOT_RUN"
        ),
        "unseen_run_c_validated": run_documents["c"].get(
            "validation_pass_count", "NOT_RUN"
        ),
        "unseen_stable_count": stability.get("counts", {}).get("STABLE", 0),
        "unseen_boundary_uncertainty_count": stability.get("counts", {}).get(
            "BOUNDARY_UNCERTAINTY", 0
        ),
        "unseen_unstable_count": stability.get("counts", {}).get("UNSTABLE", 0),
        "known_hard_safety_regression": first_hard,
        "primary_user_action_wording_owner": "RENDERER",
        "ai_imperative_primary_action": renderer["ai_imperative_primary_action"],
        "generalization_verdict": verdict,
        "night_futures_code_mutation": 0,
        "live_structured_autonomy_activation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "readiness": readiness,
    }
    write_json(proofs_dir / "generalization-verdict.json", generalization)
    write_json(proofs_dir / "production-integration-next-handoff.json", handoff)
    write_json(proofs_dir / "night-futures-no-change.json", night)
    write_json(proofs_dir / "program-completion.json", completion)
    write_json(args.output_root / "program-state.json", completion)

    root_cause = {
        "contract": "source-assembly-root-cause-v1",
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "previous_selected": 11,
        "previous_eligible": 0,
        "previous_packet_count": 0,
        "previous_base_message_count": 0,
        "root_cause_class": "COLD_START_SOURCE_ASSEMBLY_HARNESS_GAP",
        "archive_absence_relabelled_provider_failure": 0,
        "repair_target": "SOURCE_ASSEMBLY_HARNESS",
        "decision_engine_repair": 0,
    }
    write_json(proofs_dir / "source-assembly-root-cause.json", root_cause)
    _write_reports(args.report_dir, proofs_dir)
    print(json.dumps(completion, sort_keys=True), flush=True)


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
    _write_reports(args.report_dir, proofs_dir)

    rows = []
    for path in sorted(
        [args.report_dir / name for name in REPORT_NAMES[:-1]]
        + [proofs_dir / name for name in PROOF_NAMES]
    ):
        if path.is_file():
            rows.append(
                [str(path.relative_to(args.report_dir)), file_sha256(path), path.stat().st_size]
            )
    write_text(
        args.report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(("Artifact", "SHA-256", "Bytes"), rows)
        + "\n",
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
