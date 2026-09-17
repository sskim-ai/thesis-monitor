from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import traceback
import zipfile
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REQUIRED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
EXPECTED_RUNTIME_TREE_SHA256 = (
    "c0a48acb3acdbd1dff940924f38c177bfecfd07df7cda0d3bddf86424c1f1062"
)
EXPECTED_POPULATION = {
    "us": (
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
    ),
    "kr": (
        "000660",
        "003690",
        "005490",
        "005930",
        "010120",
        "012450",
        "047810",
        "086280",
    ),
}
HUMAN_STOCK_FIELDS = (
    "ticker",
    "company_name",
    "business_model",
    "company_profile",
    "industry",
    "sector",
    "revenue_sources",
    "thesis",
    "current_price_context",
    "price_and_positioning",
    "technical_context",
    "valuation",
    "cash_flow_user_visible",
    "working_capital_user_visible",
    "unknowns",
    "data_cautions",
    "evidence",
    "fact_catalog",
    "numeric_registry",
    "market_transmission",
)
BANNED_EXACT_KEYS = {
    "decision",
    "new_buyer",
    "new_buyer_axis",
    "new_buyer_result",
    "holder",
    "holder_axis",
    "holder_result",
    "directional_balance",
    "overall_maturity",
    "driver_maturity",
    "recommendation",
    "model_summary",
    "accepted_decision_id",
}
BANNED_KEY_FRAGMENTS = (
    "ai_verdict",
    "model_recommendation",
)


class SmokeFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SmokeFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SmokeFailure(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _is_banned_key(key: object) -> bool:
    normalized = str(key).lower()
    return normalized in BANNED_EXACT_KEYS or any(
        fragment in normalized for fragment in BANNED_KEY_FRAGMENTS
    )


def facts_only(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): facts_only(child)
            for key, child in value.items()
            if not _is_banned_key(key)
        }
    if isinstance(value, list):
        return [facts_only(child) for child in value]
    return value


def banned_key_paths(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _is_banned_key(key):
                found.append(child_path)
            found.extend(banned_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(banned_key_paths(child, f"{path}[{index}]"))
    return found


def human_review_files(
    *,
    collection_root: Path,
    generation_id: str,
) -> dict[str, object]:
    human = collection_root / "human-review"
    require(not human.exists(), "human_review_already_exists")
    human.mkdir(parents=True)
    index_rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        packet_path = collection_root / "inputs/current-packets" / f"{market}.json"
        packet = read_json(packet_path)
        market_context = packet.get("market_context")
        market_map = market_context if isinstance(market_context, dict) else {}
        market_payload = facts_only(
            {
                "contract": "m12cm-market-facts-only-v1",
                "generation_id": generation_id,
                "market": market,
                "assessment_date": packet.get("assessment_date"),
                "generated_at": packet.get("generated_at"),
                "packet_id": packet.get("packet_id"),
                "source_packet_sha256": sha256_file(packet_path),
                "session": market_map.get("session"),
                "coverage": market_map.get("coverage"),
                "current_observation_fact_ids": market_map.get(
                    "current_observation_fact_ids"
                ),
                "key_change_fact_ids": market_map.get("key_change_fact_ids"),
                "required_market_fact_ids": market_map.get("required_market_fact_ids"),
                "fact_catalog": market_map.get("fact_catalog"),
                "numeric_registry": market_map.get("numeric_registry"),
                "data_cautions": market_map.get("data_cautions"),
                "market_unknowns": market_map.get("market_unknowns"),
                "night_futures": market_map.get("night_futures"),
                "night_futures_audit": market_map.get("night_futures_audit"),
                "adapter_context": market_map.get("adapter_context"),
            }
        )
        market_json = human / f"{market.upper()}_MARKET_FACTS_ONLY.json"
        write_json(market_json, market_payload)
        write_text(
            human / f"{market.upper()}_MARKET_FACTS_ONLY.md",
            "\n".join(
                (
                    f"# {market.upper()} Market Facts Only",
                    "",
                    f"- Assessment date: {packet.get('assessment_date')}",
                    f"- Packet: {packet.get('packet_id')}",
                    f"- Source packet SHA-256: `{sha256_file(packet_path)}`",
                    f"- Fact catalog rows: {len(market_map.get('fact_catalog') or [])}",
                    f"- Current observation refs: {len(market_map.get('current_observation_fact_ids') or [])}",
                    f"- Cautions: {len(market_map.get('data_cautions') or [])}",
                    "",
                    "The adjacent JSON is the frozen source/evidence surface for independent review.",
                    "It intentionally contains no current AI stock verdict or model recommendation.",
                )
            ),
        )
        for stock in packet.get("stocks") or []:
            require(isinstance(stock, dict), f"{market}_stock_not_object")
            ticker = str(stock.get("ticker") or "")
            require(bool(ticker), f"{market}_ticker_missing")
            payload = facts_only(
                {
                    "contract": "m12cm-monitored-stock-facts-only-v1",
                    "generation_id": generation_id,
                    "market": market,
                    "assessment_date": packet.get("assessment_date"),
                    "packet_id": packet.get("packet_id"),
                    "source_packet_sha256": sha256_file(packet_path),
                    "facts": {
                        key: stock.get(key)
                        for key in HUMAN_STOCK_FIELDS
                        if key in stock
                    },
                }
            )
            path = human / "stocks" / f"{market}-{ticker}.json"
            write_json(path, payload)
            index_rows.append(
                {
                    "market": market,
                    "ticker": ticker,
                    "relative_path": str(path.relative_to(human)),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
    index = {
        "contract": "m12cm-monitored-stock-facts-only-index-v1",
        "generation_id": generation_id,
        "subject_count": len(index_rows),
        "subjects": index_rows,
        "excluded_sensitive_fields": sorted(BANNED_EXACT_KEYS),
    }
    write_json(human / "MONITORED_STOCK_FACTS_ONLY_INDEX.json", index)
    files = sorted(path for path in human.rglob("*") if path.is_file())
    violations = {
        str(path.relative_to(human)): banned_key_paths(read_json(path))
        for path in files
        if path.suffix == ".json"
    }
    violations = {key: value for key, value in violations.items() if value}
    require(not violations, "human_review_banned_key_leak")
    manifest = {
        "contract": "m12cm-human-review-freeze-manifest-v1",
        "generation_id": generation_id,
        "frozen_before_first_model_call": True,
        "file_count": len(files),
        "files": [
            {
                "relative_path": str(path.relative_to(human)),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
        "banned_key_violation_count": 0,
        "status": "PASS",
        "frozen_at": datetime.now(UTC).isoformat(),
    }
    write_json(collection_root / "human-review-freeze-manifest.json", manifest)
    return manifest


def verify_human_freeze(collection_root: Path, manifest: Mapping[str, object]) -> None:
    human = collection_root / "human-review"
    for row in manifest.get("files") or []:
        require(isinstance(row, Mapping), "human_manifest_row_invalid")
        path = human / str(row["relative_path"])
        require(path.is_file(), "human_review_file_missing_after_model")
        require(sha256_file(path) == row["sha256"], "human_review_changed_after_model")


def zip_tree(source: Path, destination: Path) -> dict[str, object]:
    files = sorted(path for path in source.rglob("*") if path.is_file())
    manifest = {
        "contract": "m12cm-sealed-ai-verdict-manifest-v1",
        "self_exclusion": "sealed-manifest.json is excluded from its own file list",
        "file_count": len(files),
        "files": [
            {
                "relative_path": str(path.relative_to(source)),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }
    write_json(source / "sealed-manifest.json", manifest)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))
    temporary.replace(destination)
    return {
        "path": destination.name,
        "sha256": sha256_file(destination),
        "size": destination.stat().st_size,
        "nested_file_count": len(files) + 1,
        "manifest_file_count": len(files),
    }


def v4_preflight(m12ch_root: Path) -> dict[str, object]:
    from app.services.accepted_decision_v2_runtime_service import (
        STAGE2_MODEL_OUTPUT_CONTRACT,
        AcceptedV2FundamentalCoreBatch,
        AcceptedV2ProductionContext,
        accepted_v2_production_prompt,
        accepted_v2_stage2_output_schema,
    )

    market_root = m12ch_root / "formal-generation/us"
    context = AcceptedV2ProductionContext.model_validate(
        read_json(market_root / "context.json")
    )
    trusted = AcceptedV2FundamentalCoreBatch.model_validate(
        read_json(market_root / "trusted-fundamental-core-batch.json")
    )
    raw = read_json(market_root / "batch-01.output.json")
    subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
    core_by_ticker = {row.ticker: row for row in trusted.cores}
    selected_cores = tuple(core_by_ticker[ticker] for ticker in subjects)
    schema = accepted_v2_stage2_output_schema(
        context,
        subjects=subjects,
        fundamental_cores=selected_cores,
    )
    prompt = accepted_v2_production_prompt(
        context,
        subjects=subjects,
        fundamental_cores=selected_cores,
    )
    maturity = schema["$defs"]["DriverEvidenceMaturity"]
    properties = maturity["properties"]
    payload = deepcopy(raw)
    payload["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT
    for candidate in payload["candidates"]:
        for row in candidate["driver_maturity"]:
            for field in (
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "as_of",
                "provenance_status",
            ):
                row.pop(field, None)
    def maturity_schema_errors(candidate_payload: Mapping[str, object]) -> list[str]:
        errors: list[str] = []
        allowed = set(properties)
        required = set(maturity["required"])
        for candidate_index, candidate in enumerate(candidate_payload.get("candidates") or []):
            if not isinstance(candidate, Mapping):
                errors.append(f"candidates/{candidate_index}:type")
                continue
            for row_index, row in enumerate(candidate.get("driver_maturity") or []):
                path = f"candidates/{candidate_index}/driver_maturity/{row_index}"
                if not isinstance(row, Mapping):
                    errors.append(f"{path}:type")
                    continue
                for field in sorted(required - set(row)):
                    errors.append(f"{path}/{field}:required")
                if maturity.get("additionalProperties") is False:
                    for field in sorted(set(row) - allowed):
                        errors.append(f"{path}/{field}:additionalProperties")
                for field in ("supporting_claim_refs", "contradicting_claim_refs"):
                    values = row.get(field)
                    field_schema = properties[field]
                    if not isinstance(values, list):
                        errors.append(f"{path}/{field}:type")
                        continue
                    minimum = field_schema.get("minItems")
                    maximum = field_schema.get("maxItems")
                    if isinstance(minimum, int) and len(values) < minimum:
                        errors.append(f"{path}/{field}:minItems")
                    if isinstance(maximum, int) and len(values) > maximum:
                        errors.append(f"{path}/{field}:maxItems")
                    enum = set(field_schema.get("items", {}).get("enum") or [])
                    for index, value in enumerate(values):
                        if enum and value not in enum:
                            errors.append(f"{path}/{field}/{index}:enum")
        return sorted(errors)

    baseline_errors = maturity_schema_errors(payload)
    negative = deepcopy(payload)
    negative["candidates"][0]["driver_maturity"][0]["supporting_claim_refs"] = []
    negative_errors = maturity_schema_errors(negative)
    rule_matches = [
        paragraph
        for paragraph in prompt.split("\n\n")
        if "For every driver_maturity row" in paragraph
        and "supporting_claim_refs" in paragraph
    ]
    support = properties["supporting_claim_refs"]
    contradiction = properties["contradicting_claim_refs"]
    result = {
        "contract": "m12cm-stage2-v4-preflight-v1",
        "active_raw_contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "representative_source_generation": (
            "20260917-uskr22-m12ch-20260917T000529Z-65611727332a"
        ),
        "actual_runtime_schema_path_used": True,
        "supporting_claim_refs_required": "supporting_claim_refs"
        in maturity["required"],
        "supporting_claim_refs_min_items": support.get("minItems"),
        "contradicting_claim_refs_required": "contradicting_claim_refs"
        in maturity["required"],
        "contradicting_claim_refs_min_items": contradiction.get("minItems"),
        "runtime_owned_fields_exposed": sorted(
            field
            for field in (
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "as_of",
                "provenance_status",
            )
            if field in properties
        ),
        "prompt_rule_count": len(rule_matches),
        "prompt_requires_same_ticker_support": (
            len(rule_matches) == 1 and "at least one exact same-ticker" in rule_matches[0]
        ),
        "prompt_forbids_unsupported_driver": (
            len(rule_matches) == 1 and "do not emit that driver" in rule_matches[0]
        ),
        "prompt_allows_empty_contradiction": (
            len(rule_matches) == 1
            and "contradicting_claim_refs may be empty" in rule_matches[0]
        ),
        "prompt_forbids_claim_identity_repair": (
            len(rule_matches) == 1
            and "never create, alter, approximate, shorten, infer, split, or repair one"
            in rule_matches[0]
        ),
        "prompt_distinguishes_relative_relation_from_absolute_polarity": (
            len(rule_matches) == 1
            and "supporting/contradicting is relative" in rule_matches[0]
        ),
        "baseline_schema_error_count": len(baseline_errors),
        "baseline_schema_errors": baseline_errors,
        "empty_support_schema_error_count": len(negative_errors),
        "empty_support_rejected_by_min_items": any(
            error.endswith(":minItems") for error in negative_errors
        ),
        "empty_support_schema_errors": negative_errors,
        "schema_sha256": canonical_sha256(schema),
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
    }
    result["status"] = (
        "PASS"
        if result["active_raw_contract"] == "v2-accepted-stage2-model-output-v4"
        and result["supporting_claim_refs_required"]
        and result["supporting_claim_refs_min_items"] == 1
        and result["contradicting_claim_refs_required"]
        and result["contradicting_claim_refs_min_items"] is None
        and not result["runtime_owned_fields_exposed"]
        and result["prompt_requires_same_ticker_support"]
        and result["prompt_forbids_unsupported_driver"]
        and result["prompt_allows_empty_contradiction"]
        and result["prompt_forbids_claim_identity_repair"]
        and result["prompt_distinguishes_relative_relation_from_absolute_polarity"]
        and result["baseline_schema_error_count"] == 0
        and result["empty_support_rejected_by_min_items"]
        else "FAIL"
    )
    return result


def raw_stage2_structure(output: Path, catalog_path: Path) -> dict[str, object]:
    payload = read_json(output)
    catalog = read_json(catalog_path)
    owner_by_ref = {
        str(row["claim_ref"]): str(row["ticker"])
        for row in catalog.get("maturity_atomic_claims") or []
        if isinstance(row, dict)
    }
    rows: list[dict[str, object]] = []
    for candidate in payload.get("candidates") or []:
        require(isinstance(candidate, dict), "stage2_candidate_not_object")
        ticker = str(candidate.get("ticker") or "")
        for maturity in candidate.get("driver_maturity") or []:
            require(isinstance(maturity, dict), "stage2_maturity_not_object")
            supporting = tuple(str(ref) for ref in maturity.get("supporting_claim_refs") or [])
            contradicting = tuple(
                str(ref) for ref in maturity.get("contradicting_claim_refs") or []
            )
            refs = (*supporting, *contradicting)
            rows.append(
                {
                    "ticker": ticker,
                    "supporting_count": len(supporting),
                    "contradicting_count": len(contradicting),
                    "zero_supporting": not supporting,
                    "unknown_claim_count": sum(ref not in owner_by_ref for ref in refs),
                    "cross_ticker_claim_count": sum(
                        owner_by_ref.get(ref) not in {None, ticker} for ref in refs
                    ),
                    "overlap_count": len(set(supporting) & set(contradicting)),
                    "duplicate_claim_count": (
                        len(supporting)
                        - len(set(supporting))
                        + len(contradicting)
                        - len(set(contradicting))
                    ),
                    "model_authored_source_ref_count": sum(
                        int(field in maturity)
                        for field in (
                            "supporting_evidence_refs",
                            "contradicting_evidence_refs",
                        )
                    ),
                    "model_authored_as_of_count": int("as_of" in maturity),
                    "model_authored_provenance_status_count": int(
                        "provenance_status" in maturity
                    ),
                }
            )
    result = {
        "candidate_count": len(payload.get("candidates") or []),
        "maturity_row_count": len(rows),
        "supporting_claim_cardinality": dict(
            sorted(Counter(int(row["supporting_count"]) for row in rows).items())
        ),
        "contradicting_claim_cardinality": dict(
            sorted(Counter(int(row["contradicting_count"]) for row in rows).items())
        ),
        "zero_supporting_count": sum(bool(row["zero_supporting"]) for row in rows),
        "unknown_claim_count": sum(int(row["unknown_claim_count"]) for row in rows),
        "cross_ticker_claim_count": sum(
            int(row["cross_ticker_claim_count"]) for row in rows
        ),
        "overlap_count": sum(int(row["overlap_count"]) for row in rows),
        "duplicate_claim_count": sum(
            int(row["duplicate_claim_count"]) for row in rows
        ),
        "model_authored_source_ref_count": sum(
            int(row["model_authored_source_ref_count"]) for row in rows
        ),
        "model_authored_as_of_count": sum(
            int(row["model_authored_as_of_count"]) for row in rows
        ),
        "model_authored_provenance_status_count": sum(
            int(row["model_authored_provenance_status_count"]) for row in rows
        ),
        "per_ticker_maturity_row_count": dict(
            sorted(Counter(str(row["ticker"]) for row in rows).items())
        ),
    }
    result["status"] = (
        "PASS"
        if result["maturity_row_count"] > 0
        and all(
            result[field] == 0
            for field in (
                "zero_supporting_count",
                "unknown_claim_count",
                "cross_ticker_claim_count",
                "overlap_count",
                "duplicate_claim_count",
                "model_authored_source_ref_count",
                "model_authored_as_of_count",
                "model_authored_provenance_status_count",
            )
        )
        else "FAIL"
    )
    return result


def materialized_stage2_structure(
    *,
    market: str,
    candidates: tuple[object, ...],
    cores: tuple[object, ...],
) -> dict[str, object]:
    from app.services.accepted_decision_v2_runtime_service import (
        accepted_v2_maturity_atomic_claim_catalog,
    )

    core_by_ticker = {str(getattr(core, "ticker")): core for core in cores}
    ticker_rows: list[dict[str, object]] = []
    provenance = Counter()
    parity_failures = 0
    row_count = 0
    for candidate in candidates:
        ticker = str(getattr(candidate, "ticker"))
        catalog = accepted_v2_maturity_atomic_claim_catalog(core_by_ticker[ticker])
        catalog_by_ref = {row.claim_ref: row for row in catalog}
        candidate_rows = tuple(getattr(candidate, "driver_maturity"))
        candidate_failures = 0
        for maturity in candidate_rows:
            row_count += 1
            provenance[str(maturity.provenance_status)] += 1
            for side in ("supporting", "contradicting"):
                claim_refs = tuple(getattr(maturity, f"{side}_claim_refs"))
                projected: list[str] = []
                for claim_ref in claim_refs:
                    for source_ref in catalog_by_ref[claim_ref].parent_source_refs:
                        if source_ref not in projected:
                            projected.append(source_ref)
                if tuple(projected) != tuple(
                    getattr(maturity, f"{side}_evidence_refs")
                ):
                    candidate_failures += 1
        parity_failures += candidate_failures
        ticker_rows.append(
            {
                "market": market,
                "ticker": ticker,
                "maturity_row_count": len(candidate_rows),
                "runtime_projected_source_ref_parity": (
                    "PASS" if candidate_failures == 0 else "FAIL"
                ),
            }
        )
    return {
        "market": market,
        "candidate_count": len(candidates),
        "maturity_row_count": row_count,
        "runtime_projected_source_ref_parity_failure_count": parity_failures,
        "provenance_status_counts": dict(sorted(provenance.items())),
        "rows": ticker_rows,
        "status": "PASS" if parity_failures == 0 else "FAIL",
    }


async def run(args: argparse.Namespace) -> None:
    collection_root = args.collection_root.resolve()
    isolated_data = collection_root / "isolated-data"
    require(isolated_data.is_dir(), "isolated_data_missing")
    require(
        read_json(collection_root / "current-us-market-smoke.json").get("status")
        == "PASS",
        "us_market_smoke_not_pass",
    )
    require(
        read_json(collection_root / "current-kr-market-smoke.json").get("status")
        == "PASS",
        "kr_market_smoke_not_pass",
    )
    fixture = read_json(
        collection_root
        / "krx-night-kospi200-historical-acceptance-regression.json"
    )
    require(
        fixture.get("overall_fixture_verdict")
        in {
            "EXACT_PARITY_WITH_DATE_MAPPING",
            "EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE",
            "SOURCE_NOT_YET_AVAILABLE",
        },
        "krx_fixture_not_acceptable",
    )
    integrity = read_json(collection_root / "source-base-runtime-integrity.json")
    require(integrity.get("status") == "PASS", "runtime_integrity_not_pass")
    require(
        integrity.get("runtime_tree_sha256") == EXPECTED_RUNTIME_TREE_SHA256,
        "runtime_tree_hash_drift",
    )
    head = git("rev-parse", "HEAD")
    require(head == args.expected_head, "harness_head_drift")
    require(not git("status", "--porcelain"), "worktree_not_clean")
    require(
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", REQUIRED_RUNTIME_BASE, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0,
        "runtime_base_not_ancestor",
    )

    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
    os.environ["DATA_DIR"] = str(isolated_data)
    os.environ["DATABASE_URL"] = f"sqlite:///{isolated_data / 'thesis_monitor.sqlite3'}"
    os.environ["NOTIFICATION_DRY_RUN"] = "true"
    os.environ["NOTIFICATION_RECIPIENT_CLASS"] = "test"
    os.environ["AI_REVIEW_MODE"] = "shadow"
    os.environ["PERSISTENCE_V2_WRITER_ENABLED"] = "false"
    os.environ["PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED"] = "false"

    from app.jobs import accepted_decision_v2_runtime as runtime
    from app.services.accepted_decision_v2_runtime_service import (
        REASONING_EFFORT,
        REASONING_MODEL,
        STAGE2_MODEL_OUTPUT_CONTRACT,
        AcceptedV2FundamentalCoreBatch,
        AcceptedV2ProductionArtifactV2,
        AcceptedV2ProductionBatchOutputV2,
        load_accepted_v2_production_artifact,
        validate_accepted_v2_fundamental_core,
        validate_accepted_v2_fundamental_core_batch_scope,
        validate_accepted_v2_production_output,
    )
    from scripts import m12ch_full22_reproof as m12ch
    from scripts import v2_production_cutover_preflight as preflight

    require(REASONING_MODEL == "gpt-5.6-sol", "configured_model_drift")
    require(REASONING_EFFORT == "xhigh", "configured_effort_drift")
    preflight_result = v4_preflight(args.m12ch_root.resolve())
    write_json(collection_root / "m12cl-v4-preflight.json", preflight_result)
    require(preflight_result["status"] == "PASS", "m12cl_v4_preflight_failed")
    require(
        STAGE2_MODEL_OUTPUT_CONTRACT == "v2-accepted-stage2-model-output-v4",
        "active_stage2_contract_drift",
    )
    now_utc = datetime.now(UTC)
    generation_id = (
        f"{now_utc.astimezone(KST):%Y%m%d}-m12cm-current-v4-smoke-"
        f"{now_utc:%Y%m%dT%H%M%SZ}-{head[:12]}"
    )
    human_manifest = human_review_files(
        collection_root=collection_root,
        generation_id=generation_id,
    )

    packets = {
        market: collection_root / "inputs/current-packets" / f"{market}.json"
        for market in ("us", "kr")
    }
    deterministic = {
        market: collection_root / "inputs/deterministic" / f"{market}.json"
        for market in ("us", "kr")
    }
    contexts = []
    packet_payloads: dict[str, dict[str, Any]] = {}
    for market in ("us", "kr"):
        packet = read_json(packets[market])
        context = await preflight._context(
            packets[market],
            claim_id=f"m12cj-{market}-{generation_id}",
        )
        expected_tickers = tuple(
            read_json(collection_root / "monitored-population-snapshot.json")[
                "markets"
            ][market]["tickers"]
        )
        require(
            tuple(context.selected_subjects) == expected_tickers,
            f"{market}_context_population_drift",
        )
        require(
            tuple(context.selected_subjects) == EXPECTED_POPULATION[market],
            f"{market}_expected_population_drift",
        )
        contexts.append(context)
        packet_payloads[market] = packet

    planned_calls = sum(
        2
        * (
            (len(context.selected_subjects) + runtime.V2_REASONING_BATCH_SIZE - 1)
            // runtime.V2_REASONING_BATCH_SIZE
        )
        for context in contexts
    )
    require(planned_calls == 16, "planned_call_count_not_16")
    staging = collection_root / ".sealed-ai-work"
    require(not staging.exists(), "sealed_staging_already_exists")
    staging.mkdir()
    freeze = {
        "contract": "m12cm-current-monitored-stock-input-freeze-v1",
        "generation_id": generation_id,
        "harness_commit": head,
        "required_runtime_base": REQUIRED_RUNTIME_BASE,
        "runtime_tree_sha256": integrity["runtime_tree_sha256"],
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "active_stage2_contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "batch_size": runtime.V2_REASONING_BATCH_SIZE,
        "planned_model_call_count": planned_calls,
        "model_retry": 0,
        "wrapper_retry": 0,
        "fallback_model": 0,
        "judge": 0,
        "repair_model": 0,
        "schema_repair_model": 0,
        "selective_rerun": 0,
        "hotfix_after_first_call": 0,
        "markets": {
            context.market: {
                "packet_id": context.packet_id,
                "packet_file_sha256": sha256_file(packets[context.market]),
                "canonical_source_packet_sha256": context.source_packet_sha256,
                "deterministic_sha256": sha256_file(deterministic[context.market]),
                "subject_count": len(context.selected_subjects),
                "subjects": list(context.selected_subjects),
            }
            for context in contexts
        },
        "human_review_manifest_sha256": sha256_file(
            collection_root / "human-review-freeze-manifest.json"
        ),
        "frozen_at": datetime.now(UTC).isoformat(),
    }
    write_json(collection_root / "model-input-contract-freeze.json", freeze)
    write_json(staging / "input-freeze.json", freeze)

    call_rows: list[dict[str, object]] = []
    stage2_raw_batches: list[dict[str, object]] = []
    summary: dict[str, object] = {
        "contract": "m12cm-current-monitored-stock-v4-smoke-v1",
        "generation_id": generation_id,
        "status": "RUNNING",
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "subject_count": sum(len(context.selected_subjects) for context in contexts),
        "planned_model_call_count": planned_calls,
        "model_calls_started": 0,
        "model_calls_completed": 0,
        "accepted_count": 0,
        "native_readback_count": 0,
        "stage2_raw_contract_accepted_count": 0,
        "stage2_materialized_candidate_count": 0,
        "maturity_row_count": 0,
        "zero_supporting_count": 0,
        "runtime_projected_source_ref_parity_failure_count": 0,
    }
    original_invoke = preflight._invoke_signed_in_codex
    original_output_class = preflight.AcceptedV2ProductionBatchOutput
    runtime.V2_TRANSPORT_ATTEMPT_LIMIT = 1
    preflight.V2_BATCH_SCHEMA_REPAIR_LIMIT = 0
    preflight.AcceptedV2ProductionBatchOutput = AcceptedV2ProductionBatchOutputV2

    def forbidden_repair(*args: object, **kwargs: object) -> str:
        del args, kwargs
        raise SmokeFailure("model_repair_path_forbidden_by_m12cm")

    preflight.accepted_v2_production_repair_prompt = forbidden_repair
    preflight.accepted_v2_production_batch_schema_repair_prompt = forbidden_repair

    context_by_market = {context.market: context for context in contexts}

    def tracked_invoke(**kwargs: Any) -> dict[str, object]:
        output = Path(kwargs["output"])
        prompt = Path(kwargs["prompt"])
        schema = Path(kwargs["schema"])
        market, stage, batch = m12ch.call_key(output)
        context = context_by_market[market]
        subjects = context.selected_subjects[
            (batch - 1) * runtime.V2_REASONING_BATCH_SIZE : batch
            * runtime.V2_REASONING_BATCH_SIZE
        ]
        row: dict[str, object] = {
            "ordinal": len(call_rows) + 1,
            "market": market,
            "stage": stage,
            "batch": batch,
            "subjects": list(subjects),
            "prompt_sha256": sha256_file(prompt),
            "schema_sha256": sha256_file(schema),
            "status": "STARTED",
            "started_at": datetime.now(UTC).isoformat(),
        }
        call_rows.append(row)
        summary["model_calls_started"] = int(summary["model_calls_started"]) + 1
        write_json(collection_root / "model-call-ledger-structural.json", {"calls": call_rows})
        print(
            f"START {row['ordinal']}/{planned_calls} {market} {stage} batch={batch}",
            flush=True,
        )
        receipt = original_invoke(**kwargs)
        require(int(receipt.get("transport_attempts") or 0) == 1, "transport_retry_detected")
        row.update(
            {
                "status": "OUTPUT_CREATED",
                "output_sha256": sha256_file(output),
                "transport_attempts": receipt.get("transport_attempts"),
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        summary["model_calls_completed"] = int(summary["model_calls_completed"]) + 1
        raw = output.parent / "raw-response-freeze" / output.name
        raw.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, raw)
        require(sha256_file(raw) == sha256_file(output), "raw_output_freeze_mismatch")
        if stage == "FUNDAMENTAL_CORE":
            parsed = AcceptedV2FundamentalCoreBatch.model_validate(read_json(output))
            errors = validate_accepted_v2_fundamental_core_batch_scope(
                parsed,
                context,
                subjects=subjects,
            )
            require(not errors, f"{market}_core_batch_scope_invalid")
            ownership = {item.ticker: item for item in context.evidence_ownership}
            semantic = {
                core.ticker: list(
                    validate_accepted_v2_fundamental_core(core, ownership[core.ticker])
                )
                for core in parsed.cores
            }
            require(not any(semantic.values()), f"{market}_core_semantic_invalid")
            frozen = output.parent / "core-stage-freeze" / f"core-batch-{batch:02d}.json"
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output, frozen)
        else:
            raw_audit = m12ch.stage2_raw_contract_audit(output)
            require(raw_audit["status"] == "PASS", f"{market}_stage2_raw_contract_invalid")
            catalog = output.parent / f"batch-{batch:02d}.ref-catalog.json"
            require(not m12ch.exact_ref_errors(output, catalog), f"{market}_exact_ref_invalid")
            structure = raw_stage2_structure(output, catalog)
            require(structure["status"] == "PASS", f"{market}_stage2_v4_structure_invalid")
            stage2_raw_batches.append(
                {
                    "market": market,
                    "batch": batch,
                    "subjects": list(subjects),
                    **structure,
                }
            )
            summary["stage2_raw_contract_accepted_count"] = int(
                summary["stage2_raw_contract_accepted_count"]
            ) + int(structure["candidate_count"])
        row["status"] = "PASS"
        write_json(collection_root / "model-call-ledger-structural.json", {"calls": call_rows})
        print(
            f"COMPLETE {row['ordinal']}/{planned_calls} {market} {stage} batch={batch}",
            flush=True,
        )
        return receipt

    preflight._invoke_signed_in_codex = tracked_invoke
    terminal_error: BaseException | None = None
    artifacts: list[object] = []
    structural_rows: list[dict[str, object]] = []
    materialized_batches: list[dict[str, object]] = []
    try:
        for context in contexts:
            market_dir = staging / context.market
            market_dir.mkdir()
            write_json(market_dir / "context.json", context.model_dump(mode="json"))
            generated = preflight._codex_batch(
                context,
                output_dir=market_dir,
                timeout=args.timeout,
                state_namespace=f"m12cj:{generation_id}:{context.market}",
            )
            require(
                isinstance(generated, AcceptedV2ProductionBatchOutputV2),
                f"{context.market}_normalized_output_not_v2",
            )
            trusted = m12ch.trusted_batch_from_freezes(
                context=context,
                market_dir=market_dir,
            )
            require(
                tuple(generated.fundamental_cores) == tuple(trusted.cores),
                f"{context.market}_independent_core_copy_mismatch",
            )
            materialized_structure = materialized_stage2_structure(
                market=context.market,
                candidates=tuple(generated.candidates),
                cores=tuple(trusted.cores),
            )
            require(
                materialized_structure["status"] == "PASS",
                f"{context.market}_source_ref_projection_parity_failed",
            )
            materialized_batches.append(materialized_structure)
            trusted_path = market_dir / "trusted-fundamental-core-batch.json"
            candidate_path = market_dir / "candidate-output.json"
            write_json(trusted_path, trusted.model_dump(mode="json"))
            write_json(candidate_path, generated.model_dump(mode="json"))
            artifact = validate_accepted_v2_production_output(
                context,
                generated,
                trusted_fundamental_core_batch=trusted,
            )
            require(
                isinstance(artifact, AcceptedV2ProductionArtifactV2),
                f"{context.market}_artifact_not_v2",
            )
            require(
                artifact.status == "PASS"
                and artifact.ready_count == len(context.selected_subjects)
                and artifact.not_ready_count == 0,
                f"{context.market}_artifact_not_fully_accepted",
            )
            artifact_path = market_dir / "accepted-artifact.json"
            write_json(artifact_path, artifact.model_dump(mode="json"))
            loaded = load_accepted_v2_production_artifact(
                artifact_path,
                packet=packet_payloads[context.market],
                claim_id=context.claim_id,
                trusted_fundamental_core_batch=trusted,
            )
            require(
                canonical_sha256(loaded.model_dump(mode="json"))
                == canonical_sha256(artifact.model_dump(mode="json")),
                f"{context.market}_artifact_readback_mismatch",
            )
            native = m12ch.native_delivery_readback(
                output_root=market_dir,
                packet=packet_payloads[context.market],
                artifact=artifact,
                trusted_core=trusted,
            )
            require(native["status"] == "PASS", f"{context.market}_native_readback_failed")
            for ticker in context.selected_subjects:
                structural_rows.append(
                    {
                        "market": context.market,
                        "ticker": ticker,
                        "core_status": "PASS",
                        "stage2_status": "PASS",
                        "accepted_status": "PASS",
                        "native_readback_status": "PASS",
                        "capture_status": "PENDING",
                        "packet_id": context.packet_id,
                        "source_packet_sha256": context.source_packet_sha256,
                        "accepted_artifact_sha256": sha256_file(artifact_path),
                    }
                )
            artifacts.append(artifact)
        messages = preflight._production_payloads(
            artifacts,
            (deterministic["us"], deterministic["kr"]),
        )
        require(len(messages) == len(structural_rows), "composed_message_count_drift")
        for row in structural_rows:
            row["capture_status"] = "PASS"
        write_json(staging / "production-equivalent-capture-payloads.json", {"messages": messages})
        capture = {
            "contract": "m12cm-isolated-capture-sink-v1",
            "message_count": len(messages),
            "rows": [
                {
                    "ticker": row["ticker"],
                    "rendered_sha256": row["rendered_sha256"],
                    "exact_payload_captured": True,
                }
                for row in messages
            ],
            "test_sink_invocations": 0,
            "production_send": 0,
            "status": "PASS",
        }
        write_json(collection_root / "capture-sink-trace.json", capture)
        summary.update(
            {
                "status": "PASS",
                "accepted_count": len(structural_rows),
                "native_readback_count": len(structural_rows),
                "capture_count": len(messages),
                "stage2_materialized_candidate_count": sum(
                    int(row["candidate_count"]) for row in materialized_batches
                ),
                "maturity_row_count": sum(
                    int(row["maturity_row_count"]) for row in materialized_batches
                ),
                "zero_supporting_count": sum(
                    int(row["zero_supporting_count"]) for row in stage2_raw_batches
                ),
                "runtime_projected_source_ref_parity_failure_count": sum(
                    int(row["runtime_projected_source_ref_parity_failure_count"])
                    for row in materialized_batches
                ),
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        summary.update(
            {
                "status": "FAIL",
                "safe_error_type": type(exc).__name__,
                "safe_error_code": str(exc).split(":", 1)[0],
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        write_text(staging / "failure-traceback.txt", traceback.format_exc())
    finally:
        preflight._invoke_signed_in_codex = original_invoke
        preflight.AcceptedV2ProductionBatchOutput = original_output_class

    write_json(staging / "structural-summary.json", summary)
    if not (collection_root / "capture-sink-trace.json").is_file():
        write_json(
            collection_root / "capture-sink-trace.json",
            {
                "contract": "m12cm-isolated-capture-sink-v1",
                "message_count": 0,
                "rows": [],
                "test_sink_invocations": 0,
                "production_send": 0,
                "status": "NOT_REACHED_STREAM_HARD_FAILURE",
            },
        )
    write_json(
        collection_root / "monitored-stock-smoke-structural-matrix.json",
        {
            "contract": "m12cm-monitored-stock-smoke-structural-matrix-v1",
            "generation_id": generation_id,
            "subject_count": len(structural_rows),
            "rows": structural_rows,
            "ai_verdict_labels_included": False,
            "status": summary["status"],
        },
    )
    raw_totals = {
        field: sum(int(row[field]) for row in stage2_raw_batches)
        for field in (
            "candidate_count",
            "maturity_row_count",
            "zero_supporting_count",
            "unknown_claim_count",
            "cross_ticker_claim_count",
            "overlap_count",
            "duplicate_claim_count",
            "model_authored_source_ref_count",
            "model_authored_as_of_count",
            "model_authored_provenance_status_count",
        )
    }
    support_cardinality: Counter[int] = Counter()
    contradiction_cardinality: Counter[int] = Counter()
    per_ticker_rows: Counter[str] = Counter()
    for batch in stage2_raw_batches:
        support_cardinality.update(
            {
                int(key): int(value)
                for key, value in batch["supporting_claim_cardinality"].items()  # type: ignore[union-attr]
            }
        )
        contradiction_cardinality.update(
            {
                int(key): int(value)
                for key, value in batch["contradicting_claim_cardinality"].items()  # type: ignore[union-attr]
            }
        )
        per_ticker_rows.update(batch["per_ticker_maturity_row_count"])  # type: ignore[arg-type]
    projection_failures = sum(
        int(row["runtime_projected_source_ref_parity_failure_count"])
        for row in materialized_batches
    )
    provenance_counts: Counter[str] = Counter()
    for row in materialized_batches:
        provenance_counts.update(row["provenance_status_counts"])  # type: ignore[arg-type]
    stage2_status = (
        "PASS"
        if len(stage2_raw_batches) == 8
        and raw_totals["candidate_count"] == 22
        and all(
            raw_totals[field] == 0
            for field in (
                "zero_supporting_count",
                "unknown_claim_count",
                "cross_ticker_claim_count",
                "overlap_count",
                "duplicate_claim_count",
                "model_authored_source_ref_count",
                "model_authored_as_of_count",
                "model_authored_provenance_status_count",
            )
        )
        and projection_failures == 0
        else "FAIL"
    )
    write_json(
        collection_root / "stage2-v4-structural-matrix.json",
        {
            "contract": "m12cm-stage2-v4-structural-matrix-v1",
            "generation_id": generation_id,
            "verdict_labels_included": False,
            "completed_batch_count": len(stage2_raw_batches),
            **raw_totals,
            "supporting_claim_cardinality": dict(sorted(support_cardinality.items())),
            "contradicting_claim_cardinality": dict(
                sorted(contradiction_cardinality.items())
            ),
            "per_ticker_maturity_row_count": dict(sorted(per_ticker_rows.items())),
            "runtime_projected_source_ref_parity_failure_count": projection_failures,
            "provenance_status_counts": dict(sorted(provenance_counts.items())),
            "batches": stage2_raw_batches,
            "materialized_markets": materialized_batches,
            "status": stage2_status,
        },
    )
    write_json(
        collection_root / "model-call-ledger-structural.json",
        {
            "contract": "m12cm-model-call-ledger-structural-v1",
            "generation_id": generation_id,
            "reasoning_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "planned_call_count": planned_calls,
            "started_call_count": summary["model_calls_started"],
            "completed_call_count": summary["model_calls_completed"],
            "model_retry_count": 0,
            "wrapper_retry_count": 0,
            "repair_call_count": 0,
            "fallback_model_call_count": 0,
            "judge_call_count": 0,
            "calls": call_rows,
        },
    )
    verify_human_freeze(collection_root, human_manifest)
    sealed_path = collection_root / "sealed-ai-verdicts.zip"
    sealed = zip_tree(staging, sealed_path)
    write_json(collection_root / "sealed-ai-verdicts.zip.sha256.json", sealed)
    shutil.rmtree(staging)
    verify_human_freeze(collection_root, human_manifest)
    write_json(
        collection_root / "accepted-readback-capture-structural-identity.json",
        {
            "contract": "m12cm-accepted-readback-capture-identity-v1",
            "generation_id": generation_id,
            "subject_count": len(structural_rows),
            "accepted_count": sum(row["accepted_status"] == "PASS" for row in structural_rows),
            "native_readback_count": sum(
                row["native_readback_status"] == "PASS" for row in structural_rows
            ),
            "capture_count": sum(row["capture_status"] == "PASS" for row in structural_rows),
            "rows": structural_rows,
            "verdict_labels_included": False,
            "status": summary["status"],
        },
    )
    write_json(
        collection_root / "blind-review-separation-audit.json",
        {
            "contract": "m12cm-blind-review-separation-audit-v1",
            "generation_id": generation_id,
            "facts_only_frozen_before_call_1": True,
            "facts_only_file_count": human_manifest["file_count"],
            "facts_only_hash_mismatch_count_after_model": 0,
            "facts_only_banned_key_violation_count": 0,
            "sealed_ai_archive": sealed,
            "sealed_staging_removed": not staging.exists(),
            "unsealed_raw_core_output_count": len(
                list(collection_root.glob("**/core-batch-*.output.json"))
            ),
            "unsealed_raw_stage2_output_count": len(
                list(collection_root.glob("**/batch-*.output.json"))
            ),
            "per_ticker_decision_labels_in_top_level_structural_outputs": 0,
            "new_buyer_labels_in_top_level_structural_outputs": 0,
            "holder_labels_in_top_level_structural_outputs": 0,
            "directional_balance_in_top_level_structural_outputs": 0,
            "human_ai_comparison": "NOT_PERFORMED",
            "status": "PASS",
        },
    )
    write_json(
        collection_root / "model-smoke-structural-summary.json",
        {
            **summary,
            "sealed_ai_verdicts": sealed,
            "per_subject_verdicts_included": False,
            "decision_distribution_included": False,
            "human_review_unchanged_after_model": True,
        },
    )
    if terminal_error is not None:
        raise SmokeFailure("current_monitored_stock_smoke_not_closed") from terminal_error
    require(int(summary["model_calls_started"]) == planned_calls, "model_call_start_count_drift")
    require(
        int(summary["model_calls_completed"]) == planned_calls,
        "model_call_complete_count_drift",
    )
    require(summary["accepted_count"] == 22, "accepted_subject_count_drift")
    require(summary["native_readback_count"] == 22, "native_readback_count_drift")
    require(summary["capture_count"] == 22, "capture_count_drift")
    require(stage2_status == "PASS", "stage2_v4_structural_matrix_not_pass")
    print(
        json.dumps(
            {
                "status": "PASS",
                "generation_id": generation_id,
                "subjects": len(structural_rows),
                "model_calls": summary["model_calls_completed"],
                "sealed_zip_sha256": sealed["sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--m12ch-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
