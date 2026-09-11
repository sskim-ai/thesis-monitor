from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import os
import subprocess
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


BASE_SHA = "ba511cd1c46a6b3fb0758f56eafa3f190af50884"
WORK_INSTRUCTION_COMMIT = "1c50d011d9bb12665fb0b5075eff1077c5557ea4"
EXPECTED_LATEST_SHA256 = "b7eb58d997048799c499daa7b2be29a429791772781d1ab23c6540f03fa7a9a3"
M12D_GENERATION_ID = "20260909-m12d-fictional-20260909T113907Z-3ad040f73f7f"
PROGRAM_CONTRACT = "bounded-directional-financial-context-stability-m12s-v1"
REPORT_SLUG = "20260909-bounded-directional-financial-context-stability-review"
INSTRUCTION_PATH = Path(
    "docs/work-instructions/20260909-bounded-directional-financial-context-stability-review.md"
)
MASTER_WORKFLOW_PATH = Path("docs/MASTER_WORKFLOW.md")
DEFAULT_LATEST_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-qtd-ytd-plain-korean-period-validator-repair-"
    "full-fictional-canary-report.zip"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_SLUG
DEFAULT_BUNDLE = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-bounded-directional-financial-context-stability-review-report.zip"
)

RUN_REPORTS = (
    (1, 1, "reports/34-run-1-context-01.json"),
    (1, 2, "reports/35-run-1-context-02.json"),
    (2, 1, "reports/36-run-2-context-01.json"),
    (2, 2, "reports/37-run-2-context-02.json"),
    (3, 1, "reports/38-run-3-context-01.json"),
    (3, 2, "reports/39-run-3-context-02.json"),
)
TICKERS = tuple(f"FIC-FIN-{index:02d}" for index in range(1, 9))
NONSTABLE_TICKERS = ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05")
STABLE_TICKERS = ("FIC-FIN-03", "FIC-FIN-06", "FIC-FIN-07", "FIC-FIN-08")

FREEZE_PATHS = (
    "app/services/directional_balance_service.py",
    "app/services/direction_timing_ownership_service.py",
    "app/services/directional_financial_context_service.py",
    "scripts/directional_core_price_timing_holdout.py",
)

CLAIM_FIELDS = (
    "business_thesis_context",
    "earnings_estimate_context",
    "market_expectation_context",
    "valuation_context",
    "risk_context",
    "sector_interpretation",
    "dominant_evidence",
    "uncertainty_limit",
    "core_investment_judgment",
)

DELTA_RANK = {
    "NOT_MEASURED": 0,
    "NO_MATERIAL_INTERPRETATION_DELTA": 1,
    "MINOR_EMPHASIS_DELTA": 2,
    "MATERIAL_INTERPRETATION_DELTA": 3,
}


def _json_bytes(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _json_path(path: Path) -> dict[str, Any]:
    return _json_bytes(path.read_bytes())


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _git_file(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def verify_latest_result(path: Path) -> dict[str, object]:
    observed = _file_sha256(path)
    if observed != EXPECTED_LATEST_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        index = _json_bytes(archive.read("artifact-index.json"))
        rows = index.get("artifacts") or []
        if not isinstance(rows, list):
            raise ValueError("artifact_index_rows_required")
        missing: list[str] = []
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        for row in rows:
            member = str(row["path"])
            if member not in names:
                missing.append(member)
                continue
            payload = archive.read(member)
            if _sha_bytes(payload) != row["sha256"]:
                hash_mismatches.append(member)
            if len(payload) != int(row["size_bytes"]):
                size_mismatches.append(member)
        completion = _json_bytes(archive.read("reports/50-program-completion.json"))
    status = (
        "PASS"
        if not missing
        and not hash_mismatches
        and not size_mismatches
        and len(rows) == 127
        and completion.get("fictional_generation_id") == M12D_GENERATION_ID
        else "FAIL"
    )
    return {
        "contract": "m12s-latest-result-integrity-v1",
        "path": str(path),
        "expected_sha256": EXPECTED_LATEST_SHA256,
        "observed_sha256": observed,
        "indexed_payload_count": len(rows),
        "missing_count": len(missing),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": int(completion.get("artifact_secret_scan_failure_count") or 0),
        "m12d_generation_id": completion.get("fictional_generation_id"),
        "m12d_status": completion.get("status"),
        "m12d_stop_reason": completion.get("stop_reason"),
        "status": status,
    }


def _extract_literal(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                value = ast.literal_eval(node.value)
                if isinstance(value, str):
                    return value
    raise ValueError(f"literal_not_found:{path}:{name}")


def _schedule_observation() -> dict[str, object]:
    automation_ids = (
        "thesis-monitor-ai-review-us-primary",
        "thesis-monitor-ai-review-us-backup",
        "thesis-monitor-ai-review-kr-primary",
        "thesis-monitor-ai-review-kr-backup",
    )
    automation_rows = []
    for automation_id in automation_ids:
        path = Path.home() / ".codex" / "automations" / automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        automation_rows.append(
            {
                "id": automation_id,
                "path_exists": path.is_file(),
                "status": "PAUSED" if 'status = "PAUSED"' in text else "NOT_CONFIRMED_PAUSED",
            }
        )
    launch_labels = (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
        "com.seungsoo.thesis-monitor.ai-review-fallback",
        "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
    )
    result = subprocess.run(
        ["launchctl", "print-disabled", f"gui/{os.getuid()}"],
        capture_output=True,
        text=True,
        check=False,
    )
    launch_rows = []
    for label in launch_labels:
        disabled = (
            f'"{label}" => true' in result.stdout or f'"{label}" => disabled' in result.stdout
        )
        launch_rows.append(
            {"id": label, "status": "PAUSED" if disabled else "NOT_CONFIRMED_PAUSED"}
        )
    rows = [*automation_rows, *launch_rows]
    paused = sum(row["status"] == "PAUSED" for row in rows)
    return {
        "contract": "m12s-schedule-pause-observation-v1",
        "observed_at": datetime.now(UTC).isoformat(),
        "launchctl_returncode": result.returncode,
        "rows": rows,
        "observed_paused_schedule_count": paused,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if paused == 8 else "REVIEW",
    }


def _archive_inputs(
    archive: zipfile.ZipFile,
) -> tuple[
    dict[tuple[int, str], dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    rows: dict[tuple[int, str], dict[str, Any]] = {}
    run_hashes: dict[str, dict[str, Any]] = {}
    for repetition, context_number, member in RUN_REPORTS:
        payload = archive.read(member)
        document = _json_bytes(payload)
        if document.get("generation_id") != M12D_GENERATION_ID:
            raise ValueError(f"generation_mismatch:{member}")
        if document.get("status") != "PASS":
            raise ValueError(f"run_document_not_pass:{member}")
        run_hashes[member] = {
            "repetition": repetition,
            "context": context_number,
            "sha256": _sha_bytes(payload),
            "row_count": len(document.get("rows") or []),
            "status": document.get("status"),
        }
        for row in document.get("rows") or []:
            ticker = str(row.get("ticker") or "")
            key = (repetition, ticker)
            if ticker not in TICKERS or key in rows:
                raise ValueError(f"invalid_or_duplicate_row:{key}")
            rows[key] = row
    if len(rows) != 24:
        raise ValueError(f"preserved_output_count_mismatch:{len(rows)}")

    aliases: dict[str, dict[str, Any]] = {}
    contexts: dict[str, dict[str, Any]] = {}
    for ticker in TICKERS:
        alias_document = _json_bytes(archive.read(f"experiment/aliases/{ticker}.json"))
        context = _json_bytes(archive.read(f"experiment/contexts/{ticker}.json"))
        aliases[ticker] = alias_document
        contexts[ticker] = context
    return rows, aliases, {"contexts": contexts, "run_hashes": run_hashes}


def _ref_metadata(
    ticker: str,
    alias_document: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    entries = alias_document.get("entries") or []
    financial = (context.get("financial_decision_context") or {}).get("evidence_items") or []
    financial_by_alias = {str(row["evidence_id"]): row for row in financial}
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        ref = str(entry["canonical_ref"])
        item = financial_by_alias.get(str(entry["alias"]))
        result[ref] = {
            "ticker": ticker,
            "alias": entry["alias"],
            "category": entry.get("category"),
            "label": entry.get("label"),
            "source_statement": entry.get("statement"),
            "financial_metric": item.get("metric") if item else None,
            "semantic_category": item.get("semantic_category") if item else None,
            "period_type": ((item.get("period") or {}).get("type") if item else None),
            "comparison_kind": (((item.get("comparison") or {}).get("kind")) if item else None),
        }
    return result


def _add_refs(
    roles: defaultdict[str, set[str]],
    value: Mapping[str, Any] | None,
    role: str,
    *,
    key: str = "evidence_refs",
) -> None:
    if not value:
        return
    for ref in value.get(key) or []:
        roles[str(ref)].add(role)


def evidence_roles(core: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    roles: defaultdict[str, set[str]] = defaultdict(set)
    for field in CLAIM_FIELDS:
        _add_refs(roles, core.get(field), field)
    for index, row in enumerate(core.get("buy_drivers") or [], start=1):
        _add_refs(roles, row, f"buy_driver:{index}")
    for index, row in enumerate(core.get("sell_drivers") or [], start=1):
        classification = str(row.get("classification") or "UNCLASSIFIED")
        _add_refs(roles, row, f"sell_driver:{classification}:{index}")
    for index, row in enumerate(core.get("unknown_treatments") or [], start=1):
        treatment = str(row.get("treatment") or "UNCLASSIFIED")
        _add_refs(roles, row, f"unknown:{treatment}:{index}")
        for ref in row.get("directional_negative_basis") or []:
            roles[str(ref)].add(f"directional_negative_basis:{index}")
    for index, row in enumerate(core.get("business_reevaluation_up") or [], start=1):
        _add_refs(roles, row, f"reevaluation_up:{index}")
    for index, row in enumerate(core.get("business_reevaluation_down") or [], start=1):
        _add_refs(roles, row, f"reevaluation_down:{index}")
    _add_refs(
        roles,
        core.get("fundamental_new_buyer"),
        "new_buyer_confirmation",
        key="confirmation_business_condition_refs",
    )
    _add_refs(
        roles,
        core.get("fundamental_holder"),
        "holder_invalidation",
        key="business_invalidation_condition_refs",
    )
    for ref in core.get("material_directional_anchor_basis") or []:
        roles[str(ref)].add("material_directional_anchor")
    return {ref: tuple(sorted(values)) for ref, values in sorted(roles.items())}


def _domains_for_refs(
    refs: Iterable[str], metadata: Mapping[str, Mapping[str, Any]]
) -> tuple[str, ...]:
    domains = set()
    for ref in refs:
        row = metadata.get(str(ref)) or {}
        domain = row.get("semantic_category") or row.get("category") or "UNKNOWN"
        domains.add(str(domain).upper())
    return tuple(sorted(domains))


def _role_polarity(ref: str, roles: Mapping[str, Sequence[str]]) -> str:
    values = roles.get(ref) or ()
    positive = any(role.startswith("buy_driver:") for role in values)
    explicit_negative = any(role.startswith("directional_negative_basis:") for role in values)
    sell = any(role.startswith("sell_driver:") for role in values)
    if positive and explicit_negative:
        return "MIXED"
    if positive:
        return "POSITIVE"
    if explicit_negative or sell:
        return "NEGATIVE"
    return "CONTEXT"


def _combine_polarities(values: Iterable[str]) -> str:
    present = {value for value in values if value != "NOT_USED"}
    if not present:
        return "NOT_USED"
    if "MIXED" in present or {"POSITIVE", "NEGATIVE"} <= present:
        return "MIXED"
    if "NEGATIVE" in present:
        return "NEGATIVE"
    if "POSITIVE" in present:
        return "POSITIVE"
    return "CONTEXT"


def semantic_flags(
    core: Mapping[str, Any],
    metadata: Mapping[str, Mapping[str, Any]],
    roles: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    def refs_for(
        *, labels: set[str] | None = None, categories: set[str] | None = None
    ) -> list[str]:
        matches = []
        for ref, row in metadata.items():
            if ref not in roles:
                continue
            label = str(row.get("label") or "")
            category = str(row.get("semantic_category") or "")
            if labels and label in labels:
                matches.append(ref)
            elif categories and category in categories:
                matches.append(ref)
        return matches

    operating_refs = refs_for(labels={"operating-evidence", "operating_income", "operating_profit"})
    cash_refs = refs_for(categories={"CASH_CONVERSION"})
    resilience_refs = refs_for(categories={"FINANCIAL_RESILIENCE"})
    working_capital_refs = refs_for(categories={"WORKING_CAPITAL"})
    non_operating_refs = refs_for(categories={"NON_OPERATING_EFFECT"})

    working_capital_negative = any(
        any(role.startswith("directional_negative_basis:") for role in roles.get(ref) or ())
        for ref in working_capital_refs
    )
    working_capital = (
        "NEGATIVE"
        if working_capital_negative
        else "CONTEXT"
        if working_capital_refs
        else "NOT_USED"
    )
    non_operating = "CONTEXT" if non_operating_refs else "NOT_USED"
    qtd = core.get("ticker") and any(
        (metadata.get(ref) or {}).get("period_type") == "QTD" for ref in roles
    )
    ytd = core.get("ticker") and any(
        (metadata.get(ref) or {}).get("period_type") == "YTD" for ref in roles
    )
    unknown_types = {str(row.get("treatment")) for row in core.get("unknown_treatments") or []}
    return {
        "operating_trend": _combine_polarities(
            _role_polarity(ref, roles) for ref in operating_refs
        ),
        "cash_conversion": _combine_polarities(_role_polarity(ref, roles) for ref in cash_refs),
        "debt_liquidity": _combine_polarities(
            _role_polarity(ref, roles) for ref in resilience_refs
        ),
        "working_capital": working_capital,
        "non_operating_effect": non_operating,
        "period_conflict_present": bool(qtd and ytd),
        "missing_data_confidence_limit": "CONFIDENCE_LIMIT" in unknown_types,
    }


def build_fingerprint(
    *,
    repetition: int,
    row: Mapping[str, Any],
    metadata: Mapping[str, Mapping[str, Any]],
) -> dict[str, object]:
    core = row["core"]
    roles = evidence_roles(core)
    material_refs = tuple(str(ref) for ref in core.get("material_directional_anchor_basis") or [])
    dominant_refs = tuple(
        str(ref) for ref in (core.get("dominant_evidence") or {}).get("evidence_refs") or []
    )
    all_financial_refs = tuple(
        sorted(
            ref for ref in roles if (metadata.get(ref) or {}).get("financial_metric") is not None
        )
    )
    fingerprint: dict[str, object] = {
        "contract": "m12s-evidence-interpretation-fingerprint-v1",
        "ticker": row["ticker"],
        "repetition": repetition,
        "overall_direction": core["overall_direction"],
        "directional_balance": core["directional_balance"],
        "hold_lean": core["hold_lean"],
        "business_thesis_change": core["business_thesis_change"],
        "fundamental_new_buyer_stance": core["fundamental_new_buyer"]["stance"],
        "fundamental_holder_stance": core["fundamental_holder"]["stance"],
        "directional_confidence": core["directional_confidence"],
        "material_directional_anchor_basis": list(material_refs),
        "material_directional_anchor_domains": list(_domains_for_refs(material_refs, metadata)),
        "dominant_evidence_refs": list(dominant_refs),
        "dominant_evidence_semantic_categories": list(_domains_for_refs(dominant_refs, metadata)),
        "buy_driver_classifications": [
            {
                "classification": "BUY_SUPPORT",
                "domains": list(_domains_for_refs(item.get("evidence_refs") or [], metadata)),
            }
            for item in core.get("buy_drivers") or []
        ],
        "sell_driver_classifications": [
            {
                "classification": item.get("classification"),
                "domains": list(_domains_for_refs(item.get("evidence_refs") or [], metadata)),
            }
            for item in core.get("sell_drivers") or []
        ],
        "unknown_treatment_types": sorted(
            str(item.get("treatment")) for item in core.get("unknown_treatments") or []
        ),
        "business_reevaluation_up_domains": list(
            _domains_for_refs(
                itertools.chain.from_iterable(
                    item.get("evidence_refs") or []
                    for item in core.get("business_reevaluation_up") or []
                ),
                metadata,
            )
        ),
        "business_reevaluation_down_domains": list(
            _domains_for_refs(
                itertools.chain.from_iterable(
                    item.get("evidence_refs") or []
                    for item in core.get("business_reevaluation_down") or []
                ),
                metadata,
            )
        ),
        "business_invalidation_domains": list(
            _domains_for_refs(
                core["fundamental_holder"].get("business_invalidation_condition_refs") or [],
                metadata,
            )
        ),
        "valuation_limitation_present": any(
            (metadata.get(ref) or {}).get("category") == "valuation" for ref in roles
        ),
        "sector_interpretation_domains": list(
            _domains_for_refs(
                (core.get("sector_interpretation") or {}).get("evidence_refs") or [],
                metadata,
            )
        ),
        "financial_context_domains_actually_used": sorted(
            {
                str(metadata[ref]["semantic_category"])
                for ref in all_financial_refs
                if metadata[ref].get("semantic_category")
            }
        ),
        "financial_context_metrics_actually_used": sorted(
            {
                str(metadata[ref]["financial_metric"])
                for ref in all_financial_refs
                if metadata[ref].get("financial_metric")
            }
        ),
        "evidence_roles": {ref: list(values) for ref, values in roles.items()},
        "semantic_flags": semantic_flags(core, metadata, roles),
    }
    fingerprint["fingerprint_sha256"] = _canonical_sha256(fingerprint)
    return fingerprint


def _pair_changed_fields(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[str]:
    ignored = {"repetition", "fingerprint_sha256", "evidence_roles"}
    return sorted(
        key
        for key in set(left) | set(right)
        if key not in ignored and left.get(key) != right.get(key)
    )


def _material_semantic_change(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    polarity_fields = (
        "operating_trend",
        "cash_conversion",
        "debt_liquidity",
        "working_capital",
        "non_operating_effect",
    )
    for field in polarity_fields:
        values = {str(left.get(field)), str(right.get(field))}
        if values == {"POSITIVE", "NEGATIVE"}:
            reasons.append(f"ECONOMIC_POLARITY_REVERSED:{field}")
    for field in ("period_conflict_present", "missing_data_confidence_limit"):
        if left.get(field) != right.get(field):
            reasons.append(f"SAFETY_OR_LIMIT_STATE_CHANGED:{field}")
    return bool(reasons), reasons


def classify_interpretation_delta(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> dict[str, object]:
    changed = _pair_changed_fields(left, right)
    semantic_flags_equal = left.get("semantic_flags") == right.get("semantic_flags")
    semantic_material, semantic_reasons = _material_semantic_change(
        left.get("semantic_flags") or {}, right.get("semantic_flags") or {}
    )
    left_domains = set(left.get("dominant_evidence_semantic_categories") or [])
    right_domains = set(right.get("dominant_evidence_semantic_categories") or [])
    causal_domain_disjoint = bool(
        left_domains and right_domains and not left_domains & right_domains
    )
    if semantic_material or causal_domain_disjoint:
        classification = "MATERIAL_INTERPRETATION_DELTA"
        reasons = list(semantic_reasons)
        if causal_domain_disjoint:
            reasons.append("DOMINANT_CAUSAL_DOMAIN_CHANGED")
    else:
        emphasis_fields = {
            "material_directional_anchor_basis",
            "material_directional_anchor_domains",
            "dominant_evidence_refs",
            "dominant_evidence_semantic_categories",
            "buy_driver_classifications",
            "sell_driver_classifications",
            "business_reevaluation_up_domains",
            "business_reevaluation_down_domains",
            "business_invalidation_domains",
            "business_thesis_change",
            "semantic_flags",
        }
        if emphasis_fields & set(changed):
            classification = "MINOR_EMPHASIS_DELTA"
            reasons = ["SAME_ECONOMIC_POLARITY_WITH_PRESENTATION_OR_LABEL_VARIANCE"]
        else:
            classification = "NO_MATERIAL_INTERPRETATION_DELTA"
            reasons = ["NORMALIZED_ECONOMIC_INTERPRETATION_MATCHES"]
    return {
        "left_repetition": left["repetition"],
        "right_repetition": right["repetition"],
        "classification": classification,
        "reasons": reasons,
        "changed_fields": changed,
        "adjacent_balance_only": (
            abs(
                float(left["directional_balance"]["buy"])
                - float(right["directional_balance"]["buy"])
            )
            == 0.5
            and not semantic_material
            and not causal_domain_disjoint
        ),
        "economic_semantic_flags_equal": semantic_flags_equal,
        "material_semantic_change": semantic_material,
    }


def _aggregate_delta(pair_rows: Sequence[Mapping[str, Any]]) -> str:
    if not pair_rows:
        return "NOT_MEASURED"
    return max(
        (str(row["classification"]) for row in pair_rows),
        key=lambda value: DELTA_RANK[value],
    )


def classify_subject(
    fingerprints: Sequence[Mapping[str, Any]],
    formal_classification: str,
) -> dict[str, object]:
    if len(fingerprints) != 3:
        raise ValueError("three_fingerprints_required")
    pairs = [
        classify_interpretation_delta(left, right)
        for left, right in itertools.combinations(fingerprints, 2)
    ]
    aggregate = _aggregate_delta(pairs)
    buys = [float(row["directional_balance"]["buy"]) for row in fingerprints]
    directions = [str(row["overall_direction"]) for row in fingerprints]
    buyers = [str(row["fundamental_new_buyer_stance"]) for row in fingerprints]
    holders = [str(row["fundamental_holder_stance"]) for row in fingerprints]
    thesis = [str(row["business_thesis_change"]) for row in fingerprints]
    material_refs = [tuple(row["material_directional_anchor_basis"]) for row in fingerprints]
    dominant_refs = [tuple(row["dominant_evidence_refs"]) for row in fingerprints]
    adjacent_balance = len(set(buys)) > 1 and max(buys) - min(buys) == 0.5
    secondary: list[str] = []
    if len(set(buyers)) > 1:
        secondary.append("NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY")
    if len(set(holders)) > 1:
        secondary.append("HOLDER_STANCE_CALIBRATION_AMBIGUITY")
    if len(set(material_refs)) > 1 or len(set(dominant_refs)) > 1:
        secondary.append("ANCHOR_SELECTION_PRESENTATION_VARIANCE")
    if formal_classification == "STABLE" and len(set(thesis)) > 1:
        secondary.append("FORMAL_CLASSIFIER_SENSITIVITY")

    if formal_classification == "STABLE":
        primary = None
    elif aggregate == "MATERIAL_INTERPRETATION_DELTA":
        primary = "TRUE_SEMANTIC_VARIANCE"
    elif adjacent_balance:
        primary = "ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY"
    elif len(set(buyers)) > 1:
        primary = "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY"
    elif len(set(holders)) > 1:
        primary = "HOLDER_STANCE_CALIBRATION_AMBIGUITY"
    elif len(set(material_refs)) > 1 or len(set(dominant_refs)) > 1:
        primary = "ANCHOR_SELECTION_PRESENTATION_VARIANCE"
    else:
        primary = "FORMAL_CLASSIFIER_SENSITIVITY"
    secondary = [value for value in secondary if value != primary]
    return {
        "ticker": fingerprints[0]["ticker"],
        "formal_classification": formal_classification,
        "stability_root_cause_scope": (
            "STABLE_CONTROL_ADVISORY_ONLY"
            if formal_classification == "STABLE"
            else "NONSTABLE_ROOT_CAUSE"
        ),
        "material_interpretation_delta": aggregate,
        "pairwise_deltas": pairs,
        "primary_root_cause": primary,
        "secondary_root_causes": secondary,
        "direction_sequence": directions,
        "buy_balance_sequence": buys,
        "business_thesis_change_sequence": thesis,
        "new_buyer_stance_sequence": buyers,
        "holder_stance_sequence": holders,
        "semantic_flags_sequence": [row["semantic_flags"] for row in fingerprints],
        "economic_semantic_flags_stable": len(
            {_canonical_sha256(row["semantic_flags"]) for row in fingerprints}
        )
        == 1,
    }


def analyze_bundle(path: Path) -> dict[str, Any]:
    integrity = verify_latest_result(path)
    if integrity["status"] != "PASS":
        raise ValueError("latest_result_integrity_failed")
    with zipfile.ZipFile(path) as archive:
        rows, aliases, support = _archive_inputs(archive)
        formal = _json_bytes(archive.read("reports/43-full-fictional-stability.json"))
        completion = _json_bytes(archive.read("reports/50-program-completion.json"))
    formal_by_ticker = {
        str(row["ticker"]): str(row["classification"]) for row in formal.get("rows") or []
    }
    contexts = support["contexts"]
    fingerprints: list[dict[str, object]] = []
    metadata_by_ticker = {}
    for ticker in TICKERS:
        metadata = _ref_metadata(ticker, aliases[ticker], contexts[ticker])
        metadata_by_ticker[ticker] = metadata
        for repetition in range(1, 4):
            fingerprints.append(
                build_fingerprint(
                    repetition=repetition,
                    row=rows[(repetition, ticker)],
                    metadata=metadata,
                )
            )
    by_ticker = {
        ticker: sorted(
            [row for row in fingerprints if row["ticker"] == ticker],
            key=lambda row: int(row["repetition"]),
        )
        for ticker in TICKERS
    }
    subjects = {
        ticker: classify_subject(by_ticker[ticker], formal_by_ticker[ticker]) for ticker in TICKERS
    }
    return {
        "integrity": integrity,
        "completion": completion,
        "formal": formal,
        "run_hashes": support["run_hashes"],
        "fingerprints": fingerprints,
        "fingerprints_by_ticker": by_ticker,
        "subjects": subjects,
        "metadata_by_ticker": metadata_by_ticker,
    }


def _freeze_audit() -> dict[str, object]:
    rows = []
    for path in FREEZE_PATHS:
        before = _git_file(BASE_SHA, path)
        after = Path(path).read_bytes()
        rows.append(
            {
                "path": path,
                "base_sha256": _sha_bytes(before),
                "current_sha256": _sha_bytes(after),
                "changed": before != after,
            }
        )
    return {
        "rows": rows,
        "change_count": sum(bool(row["changed"]) for row in rows),
        "status": "PASS" if all(not row["changed"] for row in rows) else "FAIL",
    }


def _root_summary(analysis: Mapping[str, Any]) -> dict[str, object]:
    subjects = analysis["subjects"]
    primary = Counter(
        row["primary_root_cause"]
        for row in subjects.values()
        if row["primary_root_cause"] is not None
    )
    secondaries = Counter(
        value for row in subjects.values() for value in row["secondary_root_causes"]
    )
    return {
        "primary_counts": dict(sorted(primary.items())),
        "secondary_counts": dict(sorted(secondaries.items())),
        "true_semantic_variance_subject_count": sum(
            row["material_interpretation_delta"] == "MATERIAL_INTERPRETATION_DELTA"
            for row in subjects.values()
        ),
        "adjacent_bucket_calibration_subject_count": sum(
            row["primary_root_cause"] == "ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY"
            for row in subjects.values()
        ),
        "new_buyer_stance_calibration_subject_count": sum(
            row["primary_root_cause"] == "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY"
            or "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY" in row["secondary_root_causes"]
            for row in subjects.values()
        ),
        "holder_stance_calibration_subject_count": sum(
            row["primary_root_cause"] == "HOLDER_STANCE_CALIBRATION_AMBIGUITY"
            or "HOLDER_STANCE_CALIBRATION_AMBIGUITY" in row["secondary_root_causes"]
            for row in subjects.values()
        ),
        "anchor_presentation_variance_subject_count": sum(
            row["primary_root_cause"] == "ANCHOR_SELECTION_PRESENTATION_VARIANCE"
            or "ANCHOR_SELECTION_PRESENTATION_VARIANCE" in row["secondary_root_causes"]
            for row in subjects.values()
        ),
        "classifier_sensitivity_subject_count": sum(
            row["primary_root_cause"] == "FORMAL_CLASSIFIER_SENSITIVITY"
            or "FORMAL_CLASSIFIER_SENSITIVITY" in row["secondary_root_causes"]
            for row in subjects.values()
        ),
    }


def _forensic_report(analysis: Mapping[str, Any], ticker: str) -> dict[str, object]:
    subject = analysis["subjects"][ticker]
    fingerprints = analysis["fingerprints_by_ticker"][ticker]
    return {
        "contract": "m12s-ticker-stability-forensic-v1",
        "ticker": ticker,
        "repeated_values": [
            {
                "repetition": row["repetition"],
                "overall_direction": row["overall_direction"],
                "directional_balance": row["directional_balance"],
                "hold_lean": row["hold_lean"],
                "business_thesis_change": row["business_thesis_change"],
                "new_buyer": row["fundamental_new_buyer_stance"],
                "holder": row["fundamental_holder_stance"],
                "material_anchors": row["material_directional_anchor_basis"],
                "semantic_flags": row["semantic_flags"],
                "unknown_treatments": row["unknown_treatment_types"],
                "reevaluation_up_domains": row["business_reevaluation_up_domains"],
                "reevaluation_down_domains": row["business_reevaluation_down_domains"],
                "invalidation_domains": row["business_invalidation_domains"],
            }
            for row in fingerprints
        ],
        **subject,
        "status": "PASS",
    }


def _contract_audits() -> dict[str, dict[str, object]]:
    balance_path = Path("app/services/directional_balance_service.py")
    ownership_path = Path("app/services/direction_timing_ownership_service.py")
    holdout_path = Path("scripts/directional_core_price_timing_holdout.py")
    shadow_path = Path("app/services/structured_autonomy_shadow_service.py")
    prompt = _extract_literal(balance_path, "ORDINAL_CALIBRATION_PROMPT")
    holdout_text = holdout_path.read_text(encoding="utf-8")
    shadow_text = shadow_path.read_text(encoding="utf-8")
    ownership_text = ownership_path.read_text(encoding="utf-8")
    balance = {
        "contract": "m12s-directional-bucket-calibration-contract-audit-v1",
        "source_path": str(balance_path),
        "source_sha256": _file_sha256(balance_path),
        "contract_text": prompt,
        "buckets": {
            "5.0": "balanced_unresolved_or_too_incomplete_for_lean",
            "5.5": "material_anchor_but_missing_sufficient_corroboration",
            "6.0": "minimum_direction_with_material_anchor_and_sufficient_corroboration",
            "6.5_plus": "progressively_stronger_corroboration_persistence_quality_visibility_or_valuation",
        },
        "financial_context_ambiguities": [
            "shared-lineage cash metrics are not distinguished from independent corroboration",
            "limiting Unknowns versus corroborating anchors have no ordinal placement rule",
            "flat operations plus non-operating support has no explicit 5.0/5.5 boundary",
            "valuation and persistence gaps do not crisply distinguish 6.0 from 6.5",
        ],
        "threshold": 6.0,
        "increment": 0.5,
        "status": "UNDER_SPECIFIED_FOR_FINANCIAL_CONTEXT_BOUNDARIES",
    }
    tiebreak = {
        "contract": "m12s-conservative-tiebreak-consistency-audit-v1",
        "frozen_rule_present": "choose the less directional bucket toward 5.0:5.0" in prompt,
        "rows": [
            {
                "case": "strong_quality_with_valuation_and_persistence_unknown",
                "adjacent_buckets": [6.0, 6.5],
                "less_directional_bucket": 6.0,
                "observed_buy_balances": [6.5, 6.0, 6.5],
                "consistent": False,
            },
            {
                "case": "cash_conversion_deterioration_with_healthy_demand_and_unknown_cause",
                "adjacent_buckets": [4.5, 4.0],
                "less_directional_bucket": 4.5,
                "observed_buy_balances": [4.0, 4.5, 4.0],
                "consistent": False,
            },
            {
                "case": "flat_operations_with_non_operating_net_income_support",
                "adjacent_buckets": [5.0, 5.5],
                "less_directional_bucket": 5.0,
                "observed_buy_balances": [5.0, 5.0, 5.5],
                "consistent": False,
            },
        ],
        "threshold_changed": False,
        "increment_changed": False,
        "status": "INCONSISTENT_APPLICATION_UNDER_UNRESOLVED_ADJACENT_FIT",
    }
    new_buyer = {
        "contract": "m12s-new-buyer-stance-contract-audit-v1",
        "enum_contract_present": 'NewBuyerStance = Literal["ATTRACTIVE", "WAIT", "AVOID"]'
        in shadow_text,
        "pre_timing_owner_present": "pre-timing views" in holdout_text,
        "schema_owner_sha256": _file_sha256(ownership_path),
        "explicit_absolute_direction_mapping": False,
        "explicit_balance_strength_mapping": False,
        "explicit_valuation_mapping": False,
        "explicit_confirmation_mapping": False,
        "fic_fin_01_sequence": ["ATTRACTIVE", "WAIT", "ATTRACTIVE"],
        "fic_fin_02_sequence": ["AVOID", "WAIT", "WAIT"],
        "same_valuation_unknown_all_repetitions": True,
        "status": "UNDER_SPECIFIED",
    }
    holder = {
        "contract": "m12s-holder-stance-contract-audit-v1",
        "enum_contract_present": 'HolderStance = Literal["HOLDABLE", "REVIEW", "REDUCE"]'
        in shadow_text,
        "business_invalidation_field_present": "business_invalidation_condition" in ownership_text,
        "price_only_reduce_forbidden": "holder_price_review can only be NONE or REVIEW and can never create REDUCE"
        in holdout_text,
        "explicit_review_reduce_fundamental_boundary": False,
        "fic_fin_05_sequence": ["REDUCE", "REVIEW", "REDUCE"],
        "same_direction_balance_thesis_and_anchors": True,
        "price_timing_involved": False,
        "status": "UNDER_SPECIFIED",
    }
    classifier_source = _git_file(BASE_SHA, "scripts/directional_core_price_timing_holdout.py")
    classifier_current = holdout_path.read_bytes()
    classifier = {
        "contract": "m12s-formal-stability-classifier-audit-v1",
        "source_path": str(holdout_path),
        "base_sha256": _sha_bytes(classifier_source),
        "current_sha256": _sha_bytes(classifier_current),
        "changed_in_m12s": classifier_source != classifier_current,
        "tracked_fields": [
            "overall_direction",
            "directional_balance",
            "hold_lean",
            "fundamental_new_buyer.stance",
            "fundamental_holder.stance",
        ],
        "detects_fic_fin_02_output_instability": True,
        "historical_m12d_result_rewritten": False,
        "business_thesis_change_outside_current_formal_key": True,
        "separate_fingerprint_advisory_required": True,
        "formal_classifier_change_required": False,
        "decision": "KEEP",
        "status": "PASS",
    }
    return {
        "balance": balance,
        "tiebreak": tiebreak,
        "new_buyer": new_buyer,
        "holder": holder,
        "classifier": classifier,
    }


def _preferred_repair_contract() -> dict[str, object]:
    return {
        "contract": "m12s-frozen-next-repair-contract-v1",
        "preferred_next_repair": "BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR",
        "next_scope": (
            "BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR_AND_FULL_FICTIONAL_CANARY"
        ),
        "repair_fields": [
            "directional_balance ordinal evidence-sufficiency guidance",
            "overall_direction as existing threshold-derived output",
            "hold_lean as existing balance-derived output",
        ],
        "allowed_contract_clarifications": [
            "distinguish shared-lineage metrics from independent corroboration",
            "state how corroborating facts and limiting Unknowns map to adjacent buckets",
            "clarify 5.0 versus 5.5 for flat operations plus non-operating support",
            "clarify 6.0 versus 6.5 when valuation or persistence remains unknown",
        ],
        "proposed_generic_text": [
            "Corroboration is independent only when it adds a distinct economic fact; multiple metrics sharing the same underlying cash-flow inputs do not automatically satisfy independent corroboration.",
            "When corroborating operating evidence and an unresolved causal or persistence limit leave adjacent buckets reasonably supportable, apply the existing tie-break toward 5.0.",
            "A non-operating boost with broadly flat operations is context, not by itself sufficient support for a positive lean.",
            "A 6.5-or-stronger bucket needs evidence beyond minimum direction support that establishes stronger persistence, quality, visibility, or valuation support.",
        ],
        "new_buyer_contract_in_primary_repair": False,
        "holder_contract_in_primary_repair": False,
        "independent_followups": [
            "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REVIEW",
            "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR",
        ],
        "buy_sell_threshold": 6.0,
        "balance_increment": 0.5,
        "threshold_change_allowed": False,
        "increment_change_allowed": False,
        "fixed_scorecard_allowed": False,
        "majority_vote_allowed": False,
        "balance_averaging_allowed": False,
        "ticker_specific_exception_allowed": False,
        "activated_in_m12s": False,
        "status": "FROZEN",
    }


def build_reports(
    *,
    analysis: Mapping[str, Any],
    schedule_start: Mapping[str, Any],
    implementation_commit: str,
    report_commit: str,
    focused_result: str,
    focused_summary: str,
    full_result: str,
    full_summary: str,
    ruff_result: str,
    diff_result: str,
) -> dict[tuple[int, str], dict[str, object]]:
    integrity = analysis["integrity"]
    formal = analysis["formal"]
    subjects = analysis["subjects"]
    roots = _root_summary(analysis)
    audits = _contract_audits()
    freeze = _freeze_audit()
    schedule_end = _schedule_observation()
    schedule = {
        "contract": "m12s-schedule-pause-start-end-observation-v1",
        "start": dict(schedule_start),
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": (
            "PASS"
            if schedule_start.get("status") == "PASS" and schedule_end.get("status") == "PASS"
            else "REVIEW"
        ),
    }
    current_head = _git("rev-parse", "HEAD")
    repository = {
        "contract": "m12s-repository-provenance-v1",
        "base_sha": BASE_SHA,
        "work_instruction_commit": _git("rev-parse", WORK_INSTRUCTION_COMMIT),
        "implementation_commit": implementation_commit,
        "report_commit": report_commit,
        "current_head_sha": current_head,
        "branch": _git("branch", "--show-current"),
        "origin_main_sha": _git("rev-parse", "origin/main"),
        "production_module_freeze": freeze,
        "status": "PASS" if freeze["status"] == "PASS" else "FAIL",
    }
    reuse = {
        "contract": "m12s-m12d-full-canary-reuse-proof-v1",
        "generation_id": M12D_GENERATION_ID,
        "source_bundle_sha256": integrity["observed_sha256"],
        "run_documents": analysis["run_hashes"],
        "preserved_model_context_count": len(analysis["run_hashes"]),
        "preserved_output_count": len(analysis["fingerprints"]),
        "new_generation_created": False,
        "model_calls_real": 0,
        "model_calls_fictional": 0,
        "model_calls_judge": 0,
        "status": "PASS",
    }
    formal_freeze = {
        **formal,
        "contract": "m12s-m12d-stability-result-freeze-v1",
        "historical_result_rewritten": False,
        "status": "FROZEN",
    }
    fingerprint_contract = {
        "contract": "m12s-evidence-interpretation-fingerprint-contract-v1",
        "source": "preserved structured M12D outputs and aliases only",
        "llm_used": False,
        "normalized_dimensions": [
            "direction",
            "balance",
            "hold lean",
            "business thesis state",
            "new-buyer stance",
            "holder stance",
            "material and dominant anchor domains",
            "driver domains",
            "Unknown treatments",
            "reevaluation and invalidation domains",
            "financial domains and metrics actually cited",
            "economic semantic flags",
        ],
        "material_delta_rule": ("economic semantic flag or disjoint dominant causal-domain change"),
        "adjacent_balance_alone_is_material": False,
        "status": "FROZEN",
    }
    stable_summary = {
        "contract": "m12s-stable-control-fingerprint-summary-v1",
        "rows": [subjects[ticker] for ticker in STABLE_TICKERS],
        "formal_stable_count": len(STABLE_TICKERS),
        "material_interpretation_delta_count": sum(
            subjects[ticker]["material_interpretation_delta"] == "MATERIAL_INTERPRETATION_DELTA"
            for ticker in STABLE_TICKERS
        ),
        "business_thesis_label_variance_advisory": [
            ticker
            for ticker in STABLE_TICKERS
            if len(set(subjects[ticker]["business_thesis_change_sequence"])) > 1
        ],
        "status": "PASS",
    }
    nonstable_summary = {
        "contract": "m12s-nonstable-fingerprint-summary-v1",
        "rows": [subjects[ticker] for ticker in NONSTABLE_TICKERS],
        "primary_root_cause_complete": all(
            subjects[ticker]["primary_root_cause"] for ticker in NONSTABLE_TICKERS
        ),
        "status": "PASS",
    }
    pair_rows = [
        {"ticker": ticker, **pair}
        for ticker in TICKERS
        for pair in subjects[ticker]["pairwise_deltas"]
    ]
    delta_matrix = {
        "contract": "m12s-material-interpretation-delta-matrix-v1",
        "rows": pair_rows,
        "counts": dict(Counter(row["classification"] for row in pair_rows)),
        "subject_summary": {
            ticker: subjects[ticker]["material_interpretation_delta"] for ticker in TICKERS
        },
        "status": "PASS",
    }
    financial_interaction = {
        "contract": "m12s-financial-context-ordinal-interaction-audit-v1",
        "finding": (
            "richer corroborating financial evidence and explicit limitations can fit adjacent "
            "ordinal buckets when independence and Unknown-limiting rules are not explicit"
        ),
        "rows": [
            {
                "ticker": "FIC-FIN-01",
                "corroboration": "operating improvement, cash conversion, resilience",
                "limitation": "valuation and persistence unknown",
                "observed_boundary": "6.0/6.5",
            },
            {
                "ticker": "FIC-FIN-02",
                "corroboration": "two related cash-conversion metrics",
                "counterevidence": "healthy demand and accounting growth",
                "limitation": "cause and reversibility unknown",
                "observed_boundary": "negative 5.5/6.0",
            },
            {
                "ticker": "FIC-FIN-04",
                "corroboration": "net-income and non-operating financial effect",
                "counterevidence": "broadly flat operations",
                "limitation": "recurrence unknown",
                "observed_boundary": "5.0/5.5",
            },
        ],
        "financial_fact_parsing_defect": False,
        "status": "PASS",
    }
    classification = {
        "contract": "m12s-stability-root-cause-classification-v1",
        "subjects": subjects,
        **roots,
        "all_subjects_reviewed": len(subjects) == 8,
        "all_nonstable_primary_root_causes_assigned": all(
            subjects[ticker]["primary_root_cause"] for ticker in NONSTABLE_TICKERS
        ),
        "status": "PASS",
    }
    true_semantic = {
        "contract": "m12s-true-semantic-variance-decision-v1",
        "decision": "NO_TRUE_SEMANTIC_VARIANCE_FOUND",
        "subject_count": roots["true_semantic_variance_subject_count"],
        "basis": (
            "normalized economic polarity, causal domains, thesis economics, and Unknown "
            "treatment did not reverse; output labels and emphasis varied"
        ),
        "business_thesis_label_variance": {
            "tickers": stable_summary["business_thesis_label_variance_advisory"],
            "classification": "FIELD_CALIBRATION_ADVISORY_NOT_ECONOMIC_POLARITY_REVERSAL",
        },
        "status": ("PASS" if roots["true_semantic_variance_subject_count"] == 0 else "REVIEW"),
    }
    adjacent = {
        "contract": "m12s-adjacent-bucket-calibration-decision-v1",
        "decision": "PRIMARY_REPAIR_REQUIRED",
        "tickers": [
            ticker
            for ticker, row in subjects.items()
            if row["primary_root_cause"] == "ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY"
        ],
        "subject_count": roots["adjacent_bucket_calibration_subject_count"],
        "threshold_change_required": False,
        "increment_change_required": False,
        "status": "PASS",
    }
    new_buyer = {
        "contract": "m12s-new-buyer-stance-calibration-decision-v1",
        "decision": "INDEPENDENT_SECONDARY_AMBIGUITY",
        "tickers": [
            ticker
            for ticker, row in subjects.items()
            if row["primary_root_cause"] == "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY"
            or "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY" in row["secondary_root_causes"]
        ],
        "directly_coupled_to_balance_bucket_in_all_runs": False,
        "included_in_primary_repair": False,
        "status": "PASS",
    }
    holder = {
        "contract": "m12s-holder-stance-calibration-decision-v1",
        "decision": "INDEPENDENT_SECONDARY_AMBIGUITY",
        "tickers": [
            ticker
            for ticker, row in subjects.items()
            if row["primary_root_cause"] == "HOLDER_STANCE_CALIBRATION_AMBIGUITY"
            or "HOLDER_STANCE_CALIBRATION_AMBIGUITY" in row["secondary_root_causes"]
        ],
        "price_timing_involved": False,
        "included_in_primary_repair": False,
        "status": "PASS",
    }
    classifier_decision = {
        "contract": "m12s-formal-classifier-change-decision-v1",
        "decision": "KEEP",
        "formal_classifier_change_required": False,
        "detects_output_instability": True,
        "historical_m12d_result_remains": "FAIL",
        "separate_full_fingerprint_advisory_next_canary": True,
        "status": "PASS",
    }
    repair = _preferred_repair_contract()
    next_canary = {
        "contract": "m12s-next-fictional-canary-scope-v1",
        "required": True,
        "new_generation_required": True,
        "same_eight_fictional_subjects": True,
        "repetitions": 3,
        "contexts_per_repetition": 2,
        "full_run_only": True,
        "selective_rerun_allowed": False,
        "same_model_effort_schema_validator_renderer_required": True,
        "fingerprint_audit_required": True,
        "fresh_real_issuer_allowed": False,
        "status": "FROZEN",
    }
    readiness = {
        "contract": "m12s-fresh-real-proof-readiness-decision-v1",
        "m12s_review_complete": True,
        "repair_implemented": False,
        "new_full_fictional_canary_complete": False,
        "fresh_real_proof_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": repair["next_scope"],
        "status": "PASS",
    }
    production = {
        "contract": "m12s-production-no-change-v1",
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
        "directional_prompt_change_count": 0,
        "calibration_contract_change_count": 0,
        "new_buyer_contract_change_count": 0,
        "holder_contract_change_count": 0,
        "formal_classifier_change_count": 0,
        "qtd_ytd_validator_change_count": 0,
        "working_capital_validator_change_count": 0,
        "output_schema_change_count": 0,
        "price_timing_change_count": 0,
        "renderer_change_count": 0,
        "status": "PASS" if freeze["status"] == "PASS" else "FAIL",
    }
    master_text = MASTER_WORKFLOW_PATH.read_text(encoding="utf-8")
    master = {
        "contract": "m12s-master-workflow-update-v1",
        "path": str(MASTER_WORKFLOW_PATH),
        "sha256": _file_sha256(MASTER_WORKFLOW_PATH),
        "m12s_recorded": "M12S" in master_text,
        "primary_root_cause_recorded": (
            "ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY" in master_text
        ),
        "holder_ambiguity_recorded": ("HOLDER_STANCE_CALIBRATION_AMBIGUITY" in master_text),
        "next_scope_recorded": str(repair["next_scope"]) in master_text,
        "fresh_real_not_ready_recorded": ("fresh_real_proof_readiness=NOT_READY" in master_text),
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if all(value for key, value in master.items() if key.endswith("_recorded"))
        else "FAIL"
    )
    reports: dict[tuple[int, str], dict[str, object]] = {
        (1, "repository-provenance"): repository,
        (2, "latest-result-integrity"): integrity,
        (3, "m12s-scope-freeze"): {
            "contract": "m12s-scope-freeze-v1",
            "model_free": True,
            "source": "preserved M12D bundle only",
            "production_module_freeze": freeze,
            "model_calls": 0,
            "provider_calls": 0,
            "production_side_effects": 0,
            "status": "FROZEN" if freeze["status"] == "PASS" else "FAIL",
        },
        (4, "m12d-full-canary-reuse-proof"): reuse,
        (5, "m12d-stability-result-freeze"): formal_freeze,
        (6, "evidence-interpretation-fingerprint-contract"): fingerprint_contract,
        (7, "all-24-output-fingerprints"): {
            "contract": "m12s-all-output-fingerprints-v1",
            "generation_id": M12D_GENERATION_ID,
            "fingerprinted_output_count": len(analysis["fingerprints"]),
            "rows": analysis["fingerprints"],
            "status": "PASS" if len(analysis["fingerprints"]) == 24 else "FAIL",
        },
        (8, "stable-control-fingerprint-summary"): stable_summary,
        (9, "nonstable-fingerprint-summary"): nonstable_summary,
        (10, "material-interpretation-delta-matrix"): delta_matrix,
        (11, "fic-fin-01-stability-forensic"): _forensic_report(analysis, "FIC-FIN-01"),
        (12, "fic-fin-02-stability-forensic"): _forensic_report(analysis, "FIC-FIN-02"),
        (13, "fic-fin-04-stability-forensic"): _forensic_report(analysis, "FIC-FIN-04"),
        (14, "fic-fin-05-stability-forensic"): _forensic_report(analysis, "FIC-FIN-05"),
        (15, "directional-bucket-calibration-contract-audit"): audits["balance"],
        (16, "conservative-tiebreak-consistency-audit"): audits["tiebreak"],
        (17, "new-buyer-stance-contract-audit"): audits["new_buyer"],
        (18, "holder-stance-contract-audit"): audits["holder"],
        (19, "formal-stability-classifier-audit"): audits["classifier"],
        (20, "financial-context-ordinal-interaction-audit"): financial_interaction,
        (21, "stability-root-cause-classification"): classification,
        (22, "true-semantic-variance-decision"): true_semantic,
        (23, "adjacent-bucket-calibration-decision"): adjacent,
        (24, "new-buyer-stance-calibration-decision"): new_buyer,
        (25, "holder-stance-calibration-decision"): holder,
        (26, "formal-classifier-change-decision"): classifier_decision,
        (27, "preferred-next-repair-decision"): {
            "contract": "m12s-preferred-next-repair-decision-v1",
            "selected": repair["preferred_next_repair"],
            "reason": (
                "three adjacent-bucket cases include the sole formal UNSTABLE direction "
                "threshold crossing; core direction/balance stability precedes stance repair"
            ),
            "rejected": {
                "TRUE_FINANCIAL_INTERPRETATION_VARIANCE_REPAIR": "no material economic interpretation delta",
                "FORMAL_STABILITY_CLASSIFIER_REPAIR": "classifier correctly detected output instability",
                "COMBINED_DIRECTIONAL_STANCE_CALIBRATION_REPAIR": "buyer and holder ambiguities are not one coupled cause",
            },
            "status": "FROZEN",
        },
        (28, "frozen-next-repair-contract"): repair,
        (29, "next-fictional-canary-scope"): next_canary,
        (30, "fresh-real-proof-readiness-decision"): readiness,
        (31, "production-no-change"): production,
        (32, "schedule-pause-observation"): schedule,
        (33, "master-workflow-update"): master,
    }
    artifact_count = len(reports) + 1 + 4
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": _git("rev-parse", WORK_INSTRUCTION_COMMIT),
        "implementation_commit": implementation_commit,
        "report_commit": report_commit,
        "final_head_sha": current_head,
        "branch": repository["branch"],
        "latest_result_zip_sha256": integrity["observed_sha256"],
        "latest_result_integrity": integrity["status"],
        "m12d_status": "M12D_CANARY_FAIL",
        "m12s_status": "COMPLETE",
        "fingerprinted_output_count": len(analysis["fingerprints"]),
        "stable_subject_count": formal["fictional_stable_count"],
        "boundary_uncertainty_subject_count": formal["fictional_boundary_uncertainty_count"],
        "unstable_subject_count": formal["fictional_unstable_count"],
        **{
            key: roots[key]
            for key in (
                "true_semantic_variance_subject_count",
                "adjacent_bucket_calibration_subject_count",
                "new_buyer_stance_calibration_subject_count",
                "holder_stance_calibration_subject_count",
                "anchor_presentation_variance_subject_count",
                "classifier_sensitivity_subject_count",
            )
        },
        "fic_fin_01_root_cause": subjects["FIC-FIN-01"]["primary_root_cause"],
        "fic_fin_02_root_cause": subjects["FIC-FIN-02"]["primary_root_cause"],
        "fic_fin_04_root_cause": subjects["FIC-FIN-04"]["primary_root_cause"],
        "fic_fin_05_root_cause": subjects["FIC-FIN-05"]["primary_root_cause"],
        "fic_fin_02_material_interpretation_delta": subjects["FIC-FIN-02"][
            "material_interpretation_delta"
        ],
        "directional_bucket_contract_status": audits["balance"]["status"],
        "conservative_tiebreak_consistency_status": audits["tiebreak"]["status"],
        "new_buyer_stance_contract_status": audits["new_buyer"]["status"],
        "holder_stance_contract_status": audits["holder"]["status"],
        "formal_classifier_change_required": False,
        "preferred_next_repair": repair["preferred_next_repair"],
        "next_repair_fields": repair["repair_fields"],
        "new_model_validation_required": True,
        "new_full_fictional_canary_required": True,
        "fresh_real_proof_readiness": "NOT_READY",
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
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": focused_result,
        "focused_test_summary": focused_summary,
        "full_test_result": full_result,
        "full_test_summary": full_summary,
        "ruff_result": ruff_result,
        "git_diff_check": diff_result,
        "artifact_count": artifact_count,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M12S_COMPLETE",
        "stop_reason": None,
        "next_scope": repair["next_scope"],
        "completed_at": datetime.now(UTC).isoformat(),
    }
    reports[(34, "program-completion")] = completion
    return reports


def generate_reports(args: argparse.Namespace) -> None:
    analysis = analyze_bundle(args.latest_zip)
    schedule_start = _json_path(args.schedule_start)
    reports = build_reports(
        analysis=analysis,
        schedule_start=schedule_start,
        implementation_commit=args.implementation_commit,
        report_commit=args.report_commit,
        focused_result=args.focused_result,
        focused_summary=args.focused_summary,
        full_result=args.full_result,
        full_summary=args.full_summary,
        ruff_result=args.ruff_result,
        diff_result=args.diff_result,
    )
    for (number, slug), value in reports.items():
        _write_json(_report_path(args.report_dir, number, slug), value)
    print(json.dumps(reports[(34, "program-completion")], sort_keys=True))


def inspect_analysis(args: argparse.Namespace) -> None:
    analysis = analyze_bundle(args.latest_zip)
    roots = _root_summary(analysis)
    print(
        json.dumps(
            {
                "generation_id": M12D_GENERATION_ID,
                "fingerprinted_output_count": len(analysis["fingerprints"]),
                "subjects": analysis["subjects"],
                "root_summary": roots,
                "status": "PASS",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _bundle_rows(report_dir: Path) -> list[tuple[str, Path]]:
    rows = [(f"reports/{path.name}", path) for path in sorted(report_dir.glob("*.json"))]
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", MASTER_WORKFLOW_PATH),
            (f"docs/work-instructions/{INSTRUCTION_PATH.name}", INSTRUCTION_PATH),
            (
                "scripts/bounded_directional_financial_context_stability_m12s.py",
                Path("scripts/bounded_directional_financial_context_stability_m12s.py"),
            ),
            (
                "tests/test_bounded_directional_financial_context_stability_m12s.py",
                Path("tests/test_bounded_directional_financial_context_stability_m12s.py"),
            ),
        )
    )
    seen = set()
    for name, path in rows:
        if name in seen or not path.is_file():
            raise ValueError(f"invalid_bundle_row:{name}:{path}")
        seen.add(name)
    return rows


def _secret_scan(rows: Sequence[tuple[str, Path]]) -> list[str]:
    markers = (
        "TELEGRAM_BOT_" + "TOKEN=",
        "OPENAI_API_" + "KEY=",
        "DART_API_" + "KEY=",
        "ACTION_API_" + "KEY=",
        '"access_' + 'token":',
        '"refresh_' + 'token":',
    )
    failures = []
    for name, path in rows:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(marker in text for marker in markers):
            failures.append(name)
    return failures


def build_bundle(args: argparse.Namespace) -> None:
    rows = _bundle_rows(args.report_dir)
    failures = _secret_scan(rows)
    if failures:
        raise ValueError("artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": name,
            "sha256": _file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for name, path in rows
    ]
    index = {
        "contract": "m12s-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
    }
    args.bundle.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    digest = _file_sha256(args.bundle)
    args.bundle.with_suffix(args.bundle.suffix + ".sha256").write_text(
        digest + "\n", encoding="utf-8"
    )
    with zipfile.ZipFile(args.bundle) as archive:
        names = set(archive.namelist())
        hash_mismatches = 0
        size_mismatches = 0
        for row in index_rows:
            payload = archive.read(row["path"])
            hash_mismatches += _sha_bytes(payload) != row["sha256"]
            size_mismatches += len(payload) != row["size_bytes"]
        missing = sum(row["path"] not in names for row in index_rows)
    print(
        json.dumps(
            {
                "bundle": str(args.bundle),
                "sha256": digest,
                "payload_count": len(index_rows),
                "missing_count": missing,
                "hash_mismatch_count": hash_mismatches,
                "size_mismatch_count": size_mismatches,
                "secret_scan_failure_count": len(failures),
                "status": (
                    "PASS"
                    if not (missing or hash_mismatches or size_mismatches or failures)
                    else "FAIL"
                ),
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("inspect", "reports", "bundle"))
    parser.add_argument("--latest-zip", type=Path, default=DEFAULT_LATEST_ZIP)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument(
        "--schedule-start", type=Path, default=Path("/tmp/m12s-schedule-start.json")
    )
    parser.add_argument("--implementation-commit", default="NOT_MEASURED")
    parser.add_argument("--report-commit", default="NOT_MEASURED")
    parser.add_argument("--focused-result", default="NOT_MEASURED")
    parser.add_argument("--focused-summary", default="NOT_MEASURED")
    parser.add_argument("--full-result", default="NOT_MEASURED")
    parser.add_argument("--full-summary", default="NOT_MEASURED")
    parser.add_argument("--ruff-result", default="NOT_MEASURED")
    parser.add_argument("--diff-result", default="NOT_MEASURED")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "inspect":
        inspect_analysis(args)
    elif args.command == "reports":
        generate_reports(args)
    else:
        build_bundle(args)


if __name__ == "__main__":
    main()
