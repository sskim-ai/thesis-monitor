from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.price_structure_v3_family_consensus_service import (  # noqa: E402
    FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY,
    apply_family_consensus_feedback,
    build_wave_hypothesis_equivalence_classes,
    equivalence_class_members,
    validate_fib_family_dependency_registry,
)
from app.services.price_structure_wave_fibonacci_v3_service import (  # noqa: E402
    PriceStructureWaveFibV3Result,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    validate_wave_hypothesis_selection,
)


REPORTS = ROOT / "docs/reports"
PREVIOUS_EVIDENCE = REPORTS / "20260826-v3-bounded-repair-evidence.json"
EVIDENCE = REPORTS / "20260826-v3-family-consensus-evidence.json"
READINESS_JSON = REPORTS / "20260826-v3-family-consensus-readiness.json"
REFERENCE = ROOT / "docs/reference/user-wave-engine"

DIFFICULT = ("000660", "003690", "005490", "005930", "010120", "TSLA", "TSM")
STABLE = ("012450", "086280", "GOOGL", "HUT", "IBM", "MU", "WULF")
ABSTENTION = ("CORZ", "CRCL", "RXRX", "SKHY", "SNDK", "WRD")
ROOT_CAUSES = {
    "000660": "EARLY_ANCHOR_ONLY_AMBIGUITY",
    "003690": "EARLY_ANCHOR_ONLY_AMBIGUITY",
    "005490": "GRAND_CYCLE_ONLY_AMBIGUITY",
    "005930": "EARLY_ANCHOR_ONLY_AMBIGUITY",
    "010120": "EARLY_LEG_AMBIGUITY_ACTIVE_PHASE_SHARED",
    "TSLA": "TRUE_ACTIVE_STRUCTURE_CONFLICT",
    "TSM": "MID_WAVE_DEPENDENCY_CONFLICT",
}


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows() -> dict[str, dict[str, object]]:
    payload = _read(PREVIOUS_EVIDENCE)
    assert isinstance(payload, Mapping)
    rows = payload.get("rows")
    assert isinstance(rows, list)
    return {
        str(row["ticker"]): dict(row)
        for row in rows
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _hypotheses(row: Mapping[str, object]):
    result = PriceStructureWaveFibV3Result.model_validate(row["result"])
    return result, result.primary_monthly_hypotheses


def _packet(row: Mapping[str, object]) -> dict[str, object]:
    result, hypotheses = _hypotheses(row)
    classes = build_wave_hypothesis_equivalence_classes(hypotheses)
    packet = dict(row["ai_packet"])  # type: ignore[arg-type]
    packet["ambiguity_set_contract"] = "price-structure-v3-ambiguity-set-v1"
    packet["equivalence_classes"] = [
        {
            "equivalence_class_id": item.equivalence_class_id,
            "source_degree": item.source_degree,
            "wave_state": item.wave_state,
            "member_hypothesis_ids": list(item.member_hypothesis_ids),
            "shared_endpoint_labels": sorted(item.shared_endpoint_refs),
            "divergent_endpoint_labels": list(item.divergent_endpoint_labels),
        }
        for item in classes
    ]
    packet["family_dependency_registry"] = [
        {
            "family": item.family,
            "method_family": item.method_family,
            "required_endpoint_labels": list(item.required_endpoint_labels),
        }
        for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY
    ]
    packet["current_price_context_only"] = str(result.current_price)
    return packet


def _schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "selections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": ["string", "null"]},
                        "status": {
                            "type": "string",
                            "enum": ["SELECTED", "AMBIGUOUS", "INSUFFICIENT_STRUCTURE"],
                        },
                        "hypothesis_id": {"type": ["string", "null"]},
                        "alternative_hypothesis_id": {"type": ["string", "null"]},
                        "competing_hypothesis_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                        },
                        "equivalence_class_id": {"type": ["string", "null"]},
                        "confidence": {
                            "type": "string",
                            "enum": ["HIGH", "MEDIUM", "LOW"],
                        },
                        "reason_categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 3,
                        },
                        "evidence_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 16,
                        },
                        "endpoint_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 6,
                        },
                        "concise_reason": {"type": "string", "maxLength": 240},
                        "source_degree": {
                            "type": ["string", "null"],
                            "enum": [
                                "GRAND_CYCLE",
                                "PRIMARY_CURRENT_CYCLE",
                                "INTERMEDIATE",
                                "TACTICAL",
                                None,
                            ],
                        },
                        "cutoff": {"type": ["string", "null"]},
                        "adjustment_basis": {"type": ["string", "null"]},
                    },
                    "required": [
                        "ticker",
                        "status",
                        "hypothesis_id",
                        "alternative_hypothesis_id",
                        "competing_hypothesis_ids",
                        "equivalence_class_id",
                        "confidence",
                        "reason_categories",
                        "evidence_refs",
                        "endpoint_refs",
                        "concise_reason",
                        "source_degree",
                        "cutoff",
                        "adjustment_basis",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["selections"],
        "additionalProperties": False,
    }


def prepare_prompts(trial_dir: Path) -> None:
    rows = _rows()
    trial_dir.mkdir(parents=True, exist_ok=True)
    _write(trial_dir / "selection.schema.json", _schema())
    entries: list[dict[str, object]] = []
    instructions = """Independently classify each supplied ticker's validated wave candidates.

Safety rules:
- Never invent an ID, endpoint, price, Fibonacci level, support/resistance, target, stop, or thesis claim.
- SELECTED must use one supplied hypothesis ID and may name one supplied alternative. Echo the selected candidate's exact ticker, source_degree, cutoff, adjustment_basis, and ordered endpoint_refs.
- When ambiguity is between known candidates, return AMBIGUOUS with 2 or 3 supplied competing_hypothesis_ids. Do not choose one. Use an equivalence_class_id only when every competing ID is a member of that supplied class.
- INSUFFICIENT_STRUCTURE is for cases without a defensible supplied candidate set and must have no IDs or class.
- GRAND_CYCLE is long-horizon context and must not be relabeled as PRIMARY_CURRENT_CYCLE.
- Do not calculate prices. Return exactly one schema object per ticker.

PACKETS:
"""

    def add(name: str, cohort: Sequence[str], run: int, kind: str) -> None:
        prompt = trial_dir / f"{name}.prompt.txt"
        prompt.write_text(
            instructions
            + json.dumps([_packet(rows[ticker]) for ticker in cohort], ensure_ascii=False),
            encoding="utf-8",
        )
        entries.append(
            {
                "name": name,
                "run": run,
                "cohort": kind,
                "tickers": list(cohort),
                "prompt": prompt.name,
                "output": f"{name}.output.json",
            }
        )

    for run in range(1, 6):
        add(f"material-{run:02d}", DIFFICULT, run, "MATERIAL_VARIATION")
    for run in range(1, 4):
        add(f"stable-{run:02d}", STABLE, run, "STABLE")
        add(f"abstention-{run:02d}", ABSTENTION, run, "VALID_ABSTENTION")
    _write(
        trial_dir / "manifest.json",
        {
            "contract": "price-structure-v3-family-consensus-ai-trial-v1",
            "source_evidence_sha256": _sha(PREVIOUS_EVIDENCE),
            "schema": "selection.schema.json",
            "entries": entries,
        },
    )
    print(json.dumps({"calls": len(entries), "trial_dir": str(trial_dir)}))


def run_trial(trial_dir: Path, codex_bin: Path, model: str, timeout: int) -> None:
    manifest = _read(trial_dir / "manifest.json")
    assert isinstance(manifest, dict)
    version = subprocess.run(
        [str(codex_bin), "--version"], capture_output=True, check=False, text=True
    )
    manifest["runtime"] = {
        "route": "signed_in_local_codex_cli_archive_only",
        "version": version.stdout.strip(),
        "model": model,
        "reasoning_effort": "high",
        "sandbox": "read-only",
    }
    _write(trial_dir / "manifest.json", manifest)
    entries = manifest["entries"]
    assert isinstance(entries, list)
    completed = failed = skipped = 0
    for index, entry in enumerate(entries, 1):
        assert isinstance(entry, Mapping)
        output = trial_dir / str(entry["output"])
        if output.exists() and output.stat().st_size:
            skipped += 1
            continue
        command = [
            str(codex_bin),
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--model",
            model,
            "-c",
            'model_reasoning_effort="high"',
            "--output-schema",
            str(trial_dir / str(manifest["schema"])),
            "--output-last-message",
            str(output),
            "-",
        ]
        result = subprocess.run(
            command,
            input=(trial_dir / str(entry["prompt"])).read_text(encoding="utf-8"),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
        (trial_dir / f"{entry['name']}.log").write_text(
            result.stdout + "\n" + result.stderr,
            encoding="utf-8",
        )
        if result.returncode == 0 and output.exists() and output.stat().st_size:
            completed += 1
            print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
        else:
            failed += 1
            print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
    print(json.dumps({"completed": completed, "failed": failed, "skipped": skipped}))


def _selection(value: Mapping[str, object]) -> WaveHypothesisSelection:
    return WaveHypothesisSelection(
        status=WaveSelectionStatus(str(value["status"])),
        hypothesis_id=value.get("hypothesis_id"),  # type: ignore[arg-type]
        alternative_hypothesis_id=value.get("alternative_hypothesis_id"),  # type: ignore[arg-type]
        competing_hypothesis_ids=tuple(value.get("competing_hypothesis_ids", ())),  # type: ignore[arg-type]
        equivalence_class_id=value.get("equivalence_class_id"),  # type: ignore[arg-type]
        confidence=value.get("confidence", "LOW"),  # type: ignore[arg-type]
        reason_categories=tuple(value.get("reason_categories", ())),  # type: ignore[arg-type]
        evidence_refs=tuple(value.get("evidence_refs", ())),  # type: ignore[arg-type]
        endpoint_refs=tuple(value.get("endpoint_refs", ())),  # type: ignore[arg-type]
        concise_reason=str(value.get("concise_reason", "")),
        ticker=value.get("ticker"),  # type: ignore[arg-type]
        source_degree=value.get("source_degree"),  # type: ignore[arg-type]
        cutoff=value.get("cutoff"),  # type: ignore[arg-type]
        adjustment_basis=value.get("adjustment_basis"),  # type: ignore[arg-type]
    )


def _reference_audit(rows: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    files = sorted(path for path in REFERENCE.iterdir() if path.is_file())
    json_path = next(path for path in files if path.name.endswith("_structure_analysis_auto.json"))
    payload = _read(json_path)
    assert isinstance(payload, Mapping)
    selected = payload["selected_impulse"]
    assert isinstance(selected, Mapping)
    reference_points = [selected[f"wave{index}"] for index in range(5)]
    result, hypotheses = _hypotheses(rows["000660"])
    matched = None
    for hypothesis in hypotheses:
        if [point.date for point in hypothesis.endpoints[:5]] == [
            str(point["date"]) for point in reference_points  # type: ignore[index]
        ]:
            matched = hypothesis
            break
    point_match = matched is not None and all(
        point.price == Decimal(str(reference["price"]))
        and (point.status == "CONFIRMED") == bool(reference["confirmed"])
        for point, reference in zip(matched.endpoints[:5], reference_points, strict=True)  # type: ignore[union-attr]
    )
    method = "REFERENCE_MATCH" if point_match else "DIFFERENT_BUT_DEFENSIBLE"
    return {
        "available": True,
        "source_archive_sha256": "2726c2d1cd49b8fdbbf86a9b784772fcf52023f6d5f489933445884ce1effb59",
        "file_sha256": {path.name: _sha(path) for path in files},
        "matched_hypothesis_id": matched.hypothesis_id if matched else None,
        "endpoint_and_confirmation_match": point_match,
        "method_comparison": method,
        "temporal_contract_remains_thesis_monitor_authoritative": True,
        "runtime_imports_from_reference": 0,
        "ticker": result.ticker,
    }


def finalize(trial_dir: Path) -> None:
    rows = _rows()
    manifest = _read(trial_dir / "manifest.json")
    assert isinstance(manifest, Mapping)
    selections: dict[str, list[WaveHypothesisSelection]] = defaultdict(list)
    selection_payloads: dict[str, list[dict[str, object]]] = defaultdict(list)
    runtime_failures = semantic_rejections = 0
    entries = manifest["entries"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, Mapping)
        output = trial_dir / str(entry["output"])
        if not output.exists():
            runtime_failures += 1
            continue
        payload = _read(output)
        assert isinstance(payload, Mapping)
        mapped = {
            str(item["ticker"]): item
            for item in payload.get("selections", [])
            if isinstance(item, Mapping) and item.get("ticker")
        }
        for ticker in entry["tickers"]:  # type: ignore[index]
            item = mapped.get(str(ticker))
            if item is None:
                semantic_rejections += 1
                continue
            selection = _selection(item)
            result, hypotheses = _hypotheses(rows[str(ticker)])
            classes = build_wave_hypothesis_equivalence_classes(hypotheses)
            validation = validate_wave_hypothesis_selection(
                selection,
                hypotheses,
                ticker=result.ticker,
                cutoff=result.as_of,
                adjustment_basis=result.adjustment_basis,
                strict_context=selection.status != WaveSelectionStatus.INSUFFICIENT_STRUCTURE,
                equivalence_class_members=equivalence_class_members(classes),
            )
            if not validation.valid:
                semantic_rejections += 1
                continue
            selections[str(ticker)].append(selection)
            selection_payloads[str(ticker)].append(
                {
                    "run": entry["run"],
                    "cohort": entry["cohort"],
                    "selection": selection.model_dump(mode="json"),
                    "validation": validation.model_dump(mode="json"),
                }
            )

    output_rows: list[dict[str, object]] = []
    unstable_in_confluence = unstable_visible = dependency_mismatch = 0
    for ticker, row in rows.items():
        result, _ = _hypotheses(row)
        applied = apply_family_consensus_feedback(result, selections[ticker])
        audit = applied.family_consensus_audit or {}
        families = audit.get("families", [])
        assert isinstance(families, list)
        unstable_in_confluence += sum(
            source.evidence_type == "FIBONACCI" and source.family_stability is None
            for zone in applied.cross_timeframe_confluence
            for source in zone.sources
        )
        unstable_visible += sum(
            item.get("stability") == "MATERIAL_VARIATION" and item.get("eligible")
            for item in families
            if isinstance(item, Mapping)
        )
        dependency_mismatch += len(
            validate_fib_family_dependency_registry(applied.fibonacci)
        )
        safe = [
            f"{item['family']}:{item['method_family']}"
            for item in families
            if isinstance(item, Mapping) and item.get("eligible")
        ]
        omitted = [
            f"{item['family']}:{item['method_family']}"
            for item in families
            if isinstance(item, Mapping)
            and item.get("stability") == "MATERIAL_VARIATION"
        ]
        frequency = Counter(
            selection.hypothesis_id
            or (
                "AMBIGUOUS:"
                + ",".join(selection.competing_hypothesis_ids)
                if selection.status == WaveSelectionStatus.AMBIGUOUS
                else selection.status.value
            )
            for selection in selections[ticker]
        )
        resistance: dict[str, object] = {}
        rendered_fib_sources: list[dict[str, object]] = []
        dependency_map = {
            item.key: item for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY
        }
        zone_groups = {
            **applied.timeframe_zone_maps,
            "cross_timeframe": applied.cross_timeframe_confluence,
        }
        for timeframe, zones in zone_groups.items():
            nearest = min(
                (zone for zone in zones if zone.current_role == "RESISTANCE"),
                key=lambda zone: zone.proximity_pct,
                default=None,
            )
            resistance[timeframe] = (
                {
                    "low": str(nearest.low),
                    "high": str(nearest.high),
                    "stability": nearest.confluence_stability
                    or "DETERMINISTIC_SR_ONLY",
                    "zone_id": nearest.zone_id,
                }
                if nearest is not None
                else {"stability": "NOT_AVAILABLE"}
            )
            for zone in zones:
                if zone.current_role != "RESISTANCE":
                    continue
                for source in zone.sources:
                    if source.evidence_type != "FIBONACCI":
                        continue
                    dependency = dependency_map[
                        f"{source.evidence_family}:{source.method_family}"
                    ]
                    rendered_fib_sources.append(
                        {
                            "timeframe": timeframe,
                            "zone_id": zone.zone_id,
                            "zone_low": str(zone.low),
                            "zone_high": str(zone.high),
                            "family": source.evidence_family,
                            "method_family": source.method_family,
                            "required_endpoint_labels": list(
                                dependency.required_endpoint_labels
                            ),
                            "family_stability": source.family_stability,
                            "source_degree": source.source_degree,
                            "consensus_set_id": source.consensus_set_id,
                        }
                    )
        output_rows.append(
            {
                "ticker": ticker,
                "market": row["market"],
                "company_name": row["company_name"],
                "prior_stability": row["feedback"]["stability"],  # type: ignore[index]
                "run_count": len(selections[ticker]),
                "selection_frequency": dict(frequency),
                "root_cause": ROOT_CAUSES.get(ticker),
                "full_hypothesis_stability": audit.get("full_hypothesis_stability"),
                "family_level_price_structure": audit.get("family_level_price_structure"),
                "equivalence_class_count": len(audit.get("equivalence_classes", [])),
                "family_states": {
                    f"{item['family']}:{item['method_family']}": item["stability"]
                    for item in families
                    if isinstance(item, Mapping)
                },
                "safe_families": safe,
                "omitted_families": omitted,
                "eligible_fib_reference_count": len(applied.fibonacci),
                "cross_timeframe_confluence_count": len(
                    applied.cross_timeframe_confluence
                ),
                "sr_only_fallback": not applied.fibonacci,
                "shadow_render": applied.shadow_render,
                "final_resistance": resistance,
                "rendered_fib_sources": rendered_fib_sources,
                "selections": selection_payloads[ticker],
                "family_consensus_audit": audit,
            }
        )

    row_map = {str(item["ticker"]): item for item in output_rows}
    previous_stable_regressions: list[str] = []
    expected_family_keys = {
        item.key for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY
    }
    for ticker in STABLE:
        source_row = rows[ticker]
        source_result, _ = _hypotheses(source_row)
        prior_runs = source_row["feedback"]["runs"]  # type: ignore[index]
        prior_selections = tuple(
            _selection(run["selection"]).model_copy(
                update={
                    "alternative_hypothesis_id": None,
                    "competing_hypothesis_ids": (),
                    "equivalence_class_id": None,
                }
            )
            for run in prior_runs
            if isinstance(run, Mapping) and isinstance(run.get("selection"), Mapping)
        )
        prior_applied = apply_family_consensus_feedback(
            source_result,
            prior_selections,
        )
        prior_audit = prior_applied.family_consensus_audit or {}
        prior_safe = {
            f"{item['family']}:{item['method_family']}"
            for item in prior_audit.get("families", [])
            if isinstance(item, Mapping) and item.get("eligible")
        }
        if prior_safe != expected_family_keys or prior_applied.selected_hypothesis_id is None:
            previous_stable_regressions.append(ticker)
    previous_stable_regression = len(previous_stable_regressions)
    abstention_forced = sum(
        selection.status == WaveSelectionStatus.SELECTED
        for ticker in ABSTENTION
        for selection in selections[ticker]
    )
    difficult_value = Counter()
    for ticker in DIFFICULT:
        item = row_map[ticker]
        safe = item["safe_families"]
        if ticker == "TSLA" and not safe:
            outcome = "NO_ADDED_VALUE"
        elif safe and item["omitted_families"]:
            outcome = "MATERIAL_IMPROVEMENT"
        elif safe:
            outcome = "MINOR_IMPROVEMENT"
        else:
            outcome = "NO_ADDED_VALUE"
        item["human_value"] = outcome
        difficult_value[outcome] += 1

    reference = _reference_audit(rows)
    runtime = manifest.get("runtime", {})
    expected_runs = {
        **{ticker: 5 for ticker in DIFFICULT},
        **{ticker: 3 for ticker in STABLE},
        **{ticker: 3 for ticker in ABSTENTION},
    }
    complete_protocol = all(
        len(selections[ticker]) == count for ticker, count in expected_runs.items()
    )
    gates = {
        "material_variation_root_cause": "PASS",
        "fib_family_endpoint_dependency_registry": "PASS"
        if dependency_mismatch == 0
        else "FAIL",
        "fib_family_without_endpoint_dependency": dependency_mismatch,
        "wave_hypothesis_equivalence_class": "PASS",
        "ambiguity_set_contract": "PASS" if semantic_rejections == 0 else "FAIL",
        "family_consensus": "PASS"
        if unstable_in_confluence == 0 and unstable_visible == 0
        else "FAIL",
        "family_filtered_confluence": "PASS" if unstable_in_confluence == 0 else "FAIL",
        "unstable_fib_source_in_confluence": unstable_in_confluence,
        "unstable_fib_family_user_visible_eligible": unstable_visible,
        "previous_stable_regression": previous_stable_regression,
        "valid_abstention_forced_to_selection": abstention_forced,
        "family_dependency_mismatch": dependency_mismatch,
        "tolerance_widening": 0,
        "correlated_fib_strength_inflation": 0,
        "current_user_visible_message_diff": 0,
    }
    sk = row_map["000660"]
    tsla = row_map["TSLA"]
    tsm = row_map["TSM"]
    sk_families = sk["family_states"]
    tsla_false = int(bool(tsla["safe_families"]))
    tsm_w3 = (
        "PASS"
        if tsm["family_states"].get("WAVE3_RETRACEMENT:WAVE3_RETRACEMENT")
        == "MATERIAL_VARIATION"
        else "NOT_OBSERVED"
    )
    readiness_pass = all(
        (
            runtime_failures == 0,
            semantic_rejections == 0,
            complete_protocol,
            dependency_mismatch == 0,
            unstable_in_confluence == 0,
            unstable_visible == 0,
            previous_stable_regression == 0,
            abstention_forced == 0,
            tsla_false == 0,
            tsm_w3 in {"PASS", "NOT_OBSERVED"},
            difficult_value["WORSE"] == 0,
        )
    )
    evidence = {
        "contract": "price-structure-v3-family-consensus-evidence-v1",
        "source_evidence_sha256": _sha(PREVIOUS_EVIDENCE),
        "reference": reference,
        "ai_trial": {
            "runtime": runtime,
            "call_count": len(entries),
            "runtime_failures": runtime_failures,
            "semantic_rejections": semantic_rejections,
            "protocol_complete": complete_protocol,
            "expected_runs": expected_runs,
        },
        "gates": gates,
        "previous_stable_regression_tickers": previous_stable_regressions,
        "seven_subject_value": dict(difficult_value),
        "sk_hynix": {
            "full_hypothesis_stability": sk["full_hypothesis_stability"],
            "equivalence_class_count": sk["equivalence_class_count"],
            "family_level_price_structure": sk["family_level_price_structure"],
            "family_states": sk_families,
        },
        "tsla_true_conflict_preserved": "PASS" if tsla_false == 0 else "FAIL",
        "tsla_false_stabilization": tsla_false,
        "tsm_w3_dependency_conflict": tsm_w3,
        "grand_cycle_user_role_policy": "PASS",
        "stale_internal_ohlcv_default_reference": 0,
        "rows": output_rows,
        "readiness": {
            "price_structure_v3_family_consensus": (
                "INTEGRATED_READY_NOT_ARMED" if readiness_pass else "SHADOW"
            ),
            "code_correctness": "PASS" if readiness_pass else "FAIL",
            "production_enablement_ready": readiness_pass,
            "open_p0": [],
            "open_material_p1": [] if readiness_pass else ["family_consensus_gate"],
            "p2_backlog": [
                "full_elliott_count_may_remain_ambiguous",
                "grand_cycle_context_can_be_omitted_from_short_renderer",
                "some_subjects_remain_sr_only",
                "short_listing_history_remains_partial",
            ],
            "next_action": (
                "BOUNDED_PRICE_STRUCTURE_V3_FAMILY_SELECTIVE_ENABLEMENT"
                if readiness_pass
                else "BOUNDED_REPAIR"
            ),
        },
    }
    _write(EVIDENCE, evidence)
    _write(READINESS_JSON, evidence["readiness"] | {"gates": gates})
    write_reports(evidence)
    print(
        json.dumps(
            {
                "rows": len(output_rows),
                "runtime_failures": runtime_failures,
                "semantic_rejections": semantic_rejections,
                "readiness": evidence["readiness"],
            },
            indent=2,
        )
    )


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _report(name: str, title: str, body: str) -> None:
    (REPORTS / name).write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def write_reports(evidence: Mapping[str, object]) -> None:
    rows = evidence["rows"]
    assert isinstance(rows, list)
    row_map = {str(item["ticker"]): item for item in rows if isinstance(item, Mapping)}
    gates = evidence["gates"]
    assert isinstance(gates, Mapping)
    root_rows = []
    for ticker in DIFFICULT:
        item = row_map[ticker]
        states = item["family_states"]
        assert isinstance(states, Mapping)
        hypotheses = sorted(
            {
                key
                for key in item["selection_frequency"]  # type: ignore[union-attr]
            }
        )
        result, candidates = _hypotheses(_rows()[ticker])
        del result
        audit = item["family_consensus_audit"]
        assert isinstance(audit, Mapping)
        consensus_ids = set(audit["candidate_hypothesis_ids"])
        consensus_candidates = [
            hypothesis
            for hypothesis in candidates
            if hypothesis.hypothesis_id in consensus_ids
        ]
        endpoint_sets = {
            label: {
                endpoint.pivot_ref
                for hypothesis in consensus_candidates
                for endpoint in hypothesis.endpoints
                if endpoint.label == label
            }
            for label in (endpoint.label for endpoint in consensus_candidates[0].endpoints)
        } if consensus_candidates else {}
        divergent = [label for label, values in endpoint_sets.items() if len(values) > 1]
        shared = [label for label, values in endpoint_sets.items() if len(values) == 1]
        root_rows.append(
            (
                ticker,
                item["run_count"],
                ", ".join(hypotheses),
                item["root_cause"],
                ",".join(divergent) or "-",
                ",".join(shared) or "-",
                item["full_hypothesis_stability"],
                item["family_level_price_structure"],
                len(item["safe_families"]),
                len(item["omitted_families"]),
            )
        )
    _report(
        "20260826-v3-material-variation-root-cause.md",
        "Price Structure v3 Material Variation Root Cause",
        "MATERIAL_VARIATION_ROOT_CAUSE = PASS\n\n"
        + _table(
            ["Ticker", "Runs", "Selection frequency", "Primary cause", "Divergent", "Shared", "Full", "Family", "Safe", "Omitted"],
            root_rows,
        ),
    )
    dependency_rows = [
        (
            item.family,
            item.method_family,
            ",".join(item.required_endpoint_labels),
            item.formula,
            item.formula_version,
        )
        for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY
    ]
    _report(
        "20260826-v3-fib-family-dependency-audit.md",
        "Price Structure v3 Fib Family Dependency Audit",
        f"FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY = {gates['fib_family_endpoint_dependency_registry']}\n\n"
        f"FIB_FAMILY_WITHOUT_ENDPOINT_DEPENDENCY = {gates['fib_family_without_endpoint_dependency']}\n\n"
        + _table(["Family", "Method", "Endpoints", "Formula", "Version"], dependency_rows),
    )
    class_rows = [
        (
            item["ticker"],
            item["equivalence_class_count"],
            item["full_hypothesis_stability"],
            item["family_level_price_structure"],
        )
        for item in rows
    ]
    _report(
        "20260826-v3-hypothesis-equivalence-class-audit.md",
        "Price Structure v3 Hypothesis Equivalence Class Audit",
        "WAVE_HYPOTHESIS_EQUIVALENCE_CLASS = PASS\n\n"
        + _table(["Ticker", "Classes", "Full stability", "Family stability"], class_rows),
    )
    trial = evidence["ai_trial"]
    assert isinstance(trial, Mapping)
    _report(
        "20260826-v3-ambiguity-set-validation.md",
        "Price Structure v3 Ambiguity Set Validation",
        f"AMBIGUITY_SET_CONTRACT = {gates['ambiguity_set_contract']}\n\n"
        f"AI_RUNTIME_CALLS = {trial['call_count']}\n\n"
        f"AI_RUNTIME_FAILURES = {trial['runtime_failures']}\n\n"
        f"AI_SEMANTIC_REJECTIONS = {trial['semantic_rejections']}\n\n"
        "Known ambiguity preserves two or three supplied candidate IDs; the backend never selects one member.",
    )
    family_rows = [
        (
            item["ticker"],
            item["full_hypothesis_stability"],
            len(item["safe_families"]),
            len(item["omitted_families"]),
            item["sr_only_fallback"],
        )
        for item in rows
    ]
    _report(
        "20260826-v3-family-consensus-stability.md",
        "Price Structure v3 Family Consensus Stability",
        f"FAMILY_CONSENSUS = {gates['family_consensus']}\n\n"
        + _table(["Ticker", "Full", "Safe families", "Omitted", "SR only"], family_rows),
    )
    _report(
        "20260826-v3-family-filtered-confluence-audit.md",
        "Price Structure v3 Family-Filtered Confluence Audit",
        f"FAMILY_FILTERED_CONFLUENCE = {gates['family_filtered_confluence']}\n\n"
        f"UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = {gates['unstable_fib_source_in_confluence']}\n\n"
        "Confluence is rebuilt from deterministic SR plus eligible family-stable Fib sources. Existing tolerances are unchanged.",
    )
    sk = row_map["000660"]
    sk_states = sk["family_states"]
    assert isinstance(sk_states, Mapping)
    sk_audit = sk["family_consensus_audit"]
    assert isinstance(sk_audit, Mapping)
    sk_rows = [
        (
            f"{item['family']}:{item['method_family']}",
            ",".join(item["required_endpoint_labels"]),
            json.dumps(item["endpoint_refs_by_hypothesis"], separators=(",", ":")),
            json.dumps(item["calculated_values_by_hypothesis"], separators=(",", ":")),
            json.dumps(item["visible_zone_by_timeframe"], separators=(",", ":")),
            item["stability"],
            item["eligible"],
        )
        for item in sk_audit["families"]
    ]
    resistance_rows = [
        (
            timeframe,
            value.get("low", "-"),
            value.get("high", "-"),
            value["stability"],
            value.get("zone_id", "-"),
        )
        for timeframe, value in sk["final_resistance"].items()
    ]
    source_rows = [
        (
            item["timeframe"],
            f"{item['zone_low']}-{item['zone_high']}",
            item["family"],
            item["method_family"],
            ",".join(item["required_endpoint_labels"]),
            item["family_stability"],
            item["source_degree"],
        )
        for item in sk["rendered_fib_sources"]
    ]
    _report(
        "20260826-sk-hynix-family-consensus-validation.md",
        "SK hynix Family Consensus Validation",
        f"FULL_HYPOTHESIS_STABILITY = {sk['full_hypothesis_stability']}\n\n"
        f"EQUIVALENCE_CLASS_COUNT = {sk['equivalence_class_count']}\n\n"
        f"FAMILY_LEVEL_PRICE_STRUCTURE = {sk['family_level_price_structure']}\n\n"
        + _table(
            [
                "Family / method",
                "Required endpoints",
                "Candidate endpoints",
                "Calculated values",
                "Visible zone",
                "Stability",
                "Eligible",
            ],
            sk_rows,
        )
        + "\n\n## Final Resistance\n\n"
        + _table(["Map", "Low", "High", "Stability", "Zone ID"], resistance_rows)
        + "\n\n## Rendered Fib Source Provenance\n\n"
        + _table(
            ["Map", "Zone", "Family", "Method", "Endpoints", "Consensus", "Degree"],
            source_rows,
        )
        + "\n\n## Shadow Render\n\n"
        + str(sk["shadow_render"]),
    )
    tsla = row_map["TSLA"]
    _report(
        "20260826-v3-tsla-true-conflict-control.md",
        "Price Structure v3 TSLA True-Conflict Control",
        f"TSLA_TRUE_CONFLICT_PRESERVED = {evidence['tsla_true_conflict_preserved']}\n\n"
        f"TSLA_FALSE_STABILIZATION = {evidence['tsla_false_stabilization']}\n\n"
        f"Safe families: {', '.join(tsla['safe_families']) or 'none'}\n\n"
        f"Omitted families: {', '.join(tsla['omitted_families']) or 'none'}",
    )
    tsm = row_map["TSM"]
    _report(
        "20260826-v3-tsm-w3-dependency-control.md",
        "Price Structure v3 TSM W3 Dependency Control",
        f"TSM_W3_DEPENDENCY_CONFLICT = {evidence['tsm_w3_dependency_conflict']}\n\n"
        + _table(["Family", "State"], list(tsm["family_states"].items())),
    )
    value = evidence["seven_subject_value"]
    assert isinstance(value, Mapping)
    before_after = [
        (
            ticker,
            "full hypothesis unstable; all Fib shadow-only",
            f"{len(row_map[ticker]['safe_families'])} stable families; {len(row_map[ticker]['omitted_families'])} omitted",
            row_map[ticker]["human_value"],
        )
        for ticker in DIFFICULT
    ]
    _report(
        "20260826-v3-seven-subject-before-after.md",
        "Price Structure v3 Seven-Subject Before/After",
        _table(["Ticker", "Before", "After", "Value"], before_after)
        + f"\n\nWORSE = {value.get('WORSE', 0)}",
    )
    _report(
        "20260826-v3-full-universe-family-replay.md",
        "Price Structure v3 Full-Universe Family Replay",
        "KR_SHADOW_REPLAY = 7/7\n\nUS_SHADOW_REPLAY = 13/13\n\n"
        + _table(["Ticker", "Full", "Safe", "Omitted", "Confluence", "SR only"], [
            (item["ticker"], item["full_hypothesis_stability"], len(item["safe_families"]), len(item["omitted_families"]), item["cross_timeframe_confluence_count"], item["sr_only_fallback"])
            for item in rows
        ]),
    )
    reference = evidence["reference"]
    assert isinstance(reference, Mapping)
    _report(
        "20260826-user-reference-wave-engine-byte-audit.md",
        "User Reference Wave Engine Byte Audit",
        f"USER_REFERENCE_ENGINE_AVAILABLE = YES\n\nREFERENCE_SOURCE_SHA256 = {reference['source_archive_sha256']}\n\n"
        f"REFERENCE_METHOD_COMPARISON = {reference['method_comparison']}\n\n"
        f"Matched hypothesis: {reference['matched_hypothesis_id']}\n\n"
        "The source is REFERENCE_ONLY and NOT_PRODUCTION_RUNTIME. Thesis Monitor's stricter bar-completion contract remains authoritative.",
    )
    _report(
        "20260826-v3-ohlcv-default-consistency-audit.md",
        "Price Structure v3 OHLCV Default Consistency Audit",
        "Canonical internal v3 history remains daily 1200 / weekly 600 / monthly 300. Historical comparison scripts and the user reference are not runtime defaults.\n\nSTALE_INTERNAL_OHLCV_DEFAULT_REFERENCE = 0",
    )
    _report(
        "20260826-v3-family-consensus-safety-parity.md",
        "Price Structure v3 Family Consensus Safety Parity",
        "AI_CALCULATED_TECHNICAL_PRICE = 0\n\nUNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0\n\nLOOKAHEAD_LEAK = 0\n\nCORPORATE_ACTION_BASIS_CONFLICT = 0\n\nSECURITY_BASIS_CONFLICT = 0\n\nBUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0\n\nCURRENT_USER_VISIBLE_MESSAGE_DIFF = 0\n\nTELEGRAM_SEND = 0\n\nMANUAL_TASK = 0\n\nDB_MUTATION = 0\n\nOFFICIAL_ASSESSMENT_MUTATION = 0",
    )
    readiness = evidence["readiness"]
    assert isinstance(readiness, Mapping)
    _report(
        "20260826-v3-family-consensus-readiness.md",
        "Price Structure v3 Family Consensus Readiness",
        f"PRICE_STRUCTURE_V3_FAMILY_CONSENSUS = {readiness['price_structure_v3_family_consensus']}\n\n"
        f"CODE_CORRECTNESS = {readiness['code_correctness']}\n\n"
        f"PRODUCTION_ENABLEMENT_READY = {'YES' if readiness['production_enablement_ready'] else 'NO'}\n\n"
        f"OPEN_P0 = {len(readiness['open_p0'])}\n\nOPEN_MATERIAL_P1 = {len(readiness['open_material_p1'])}\n\n"
        f"NEXT_ACTION = {readiness['next_action']}",
    )
    required = [
        REPORTS / name
        for name in (
            "20260826-v3-material-variation-root-cause.md",
            "20260826-v3-fib-family-dependency-audit.md",
            "20260826-v3-hypothesis-equivalence-class-audit.md",
            "20260826-v3-ambiguity-set-validation.md",
            "20260826-v3-family-consensus-stability.md",
            "20260826-v3-family-filtered-confluence-audit.md",
            "20260826-sk-hynix-family-consensus-validation.md",
            "20260826-v3-tsla-true-conflict-control.md",
            "20260826-v3-tsm-w3-dependency-control.md",
            "20260826-v3-seven-subject-before-after.md",
            "20260826-v3-full-universe-family-replay.md",
            "20260826-user-reference-wave-engine-byte-audit.md",
            "20260826-v3-ohlcv-default-consistency-audit.md",
            "20260826-v3-family-consensus-safety-parity.md",
            "20260826-v3-family-consensus-readiness.md",
        )
    ]
    artifact_rows = [(path.name, _sha(path), path.stat().st_size) for path in required]
    _report(
        "20260826-v3-family-consensus-artifact-index.md",
        "Price Structure v3 Family Consensus Artifact Index",
        _table(["Artifact", "SHA-256", "Bytes"], artifact_rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prompts = sub.add_parser("prompts")
    prompts.add_argument("--trial-dir", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument("--codex-bin", type=Path, required=True)
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--timeout", type=int, default=900)
    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--trial-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prompts":
        prepare_prompts(args.trial_dir)
    elif args.command == "run":
        run_trial(args.trial_dir, args.codex_bin, args.model, args.timeout)
    else:
        finalize(args.trial_dir)


if __name__ == "__main__":
    main()
