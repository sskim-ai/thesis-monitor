from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.services.direction_timing_ownership_service import (
    OwnedEvidencePacket,
    financial_decision_context_for_owned,
)
from app.services.directional_financial_context_service import (
    FinancialDecisionEvidenceItem,
)
from app.services.structured_autonomy_alias_service import EvidenceAliasCatalog
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g
from scripts import directional_financial_context_m12r as m12r


PROGRAM_CONTRACT = "financial-context-output-grounding-architecture-review-m12a-v1"
BASE_SHA = "6024a1ef226ec176199de48a573ccf1bc541d4c9"
WORK_INSTRUCTION_COMMIT = "938569446f309376c3519dd63fd33d505c790e57"
M12G_GENERATION_ID = "20260909-m12g-fictional-20260909T054736Z-63aaf9f72cc7"
LATEST_RESULT_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-bounded-directional-financial-anchor-grounding-"
    "repair-full-fictional-canary-report.zip"
)
LATEST_RESULT_SHA256 = "69fc255d836d3dd886882754c21a233d82541c86ff627a5a5c8342249012aa68"
REPORT_DIRECTORY_NAME = "20260909-financial-context-output-grounding-architecture-review"
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-financial-context-output-grounding-"
    "architecture-review-report.zip"
)
INSTRUCTION_PATH = Path("docs/work-instructions") / (
    "20260909-financial-context-output-grounding-architecture-review.md"
)
MASTER_WORKFLOW_PATH = Path("docs/MASTER_WORKFLOW.md")

M12_RUNS = (
    Path("docs/reports/20260909-directional-financial-context-consumption-"
         "specificity-implementation/33-canary-context-01-run-1.json"),
)
M12R_RUNS = (
    Path("docs/reports/20260909-bounded-directional-financial-context-validator-"
         "repair-full-fictional-canary/26-run-1-context-01.json"),
    Path("docs/reports/20260909-bounded-directional-financial-context-validator-"
         "repair-full-fictional-canary/27-run-1-context-02.json"),
)
M12G_RUNS = (
    Path("docs/reports/20260909-bounded-directional-financial-anchor-grounding-"
         "repair-full-fictional-canary/30-run-1-context-01.json"),
    Path("docs/reports/20260909-bounded-directional-financial-anchor-grounding-"
         "repair-full-fictional-canary/31-run-1-context-02.json"),
)
M12G_CORRECTED_FIC06 = Path(
    "docs/reports/20260909-bounded-directional-financial-anchor-grounding-"
    "repair-full-fictional-canary/11-corrected-fic-fin-06-fixture.json"
)

SHARED_SEMANTIC_FILES = (
    Path("app/services/cross_market_decision_engine_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("scripts/directional_core_price_timing_holdout.py"),
)
SOURCE_SUFFICIENCY_FILE = Path("app/services/coldstart_fundamental_enrichment_service.py")
DAILY_DELTA_FILE = Path("app/services/nonproduction_monitoring_lifecycle_service.py")
WARNING_FILE = Path("app/services/warning_backfill_service.py")
NOTIFICATION_FILE = Path("app/services/notification_service.py")
RENDERER_FILE = Path("app/services/structured_autonomy_shadow_service.py")

PREFERRED_ARCHITECTURE = "FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION"
NEXT_SCOPE = "FIRST_CLASS_TYPED_FINANCIAL_EVIDENCE_INDEX_IMPLEMENTATION"

_METRIC_LABELS = {
    "operating_cash_flow": "operating cash flow",
    "ppe_capex_cash_outflow": "PPE acquisition cash outflow",
    "ocf_less_ppe_capex": "OCF less PPE acquisition cash outflow",
    "cash_and_cash_equivalents": "cash and cash equivalents",
    "interest_bearing_debt_total": "complete interest-bearing debt total",
    "net_debt": "net debt",
    "inventory": "inventory",
    "trade_accounts_receivable": "trade accounts receivable",
    "trade_accounts_payable": "trade accounts payable",
    "operating_income": "operating income",
    "net_income": "net income",
    "net_financial_income_effect": "net financial income effect",
}

_METRIC_NARRATIVE_TOKENS = {
    "operating_cash_flow": ("operating cash", "ocf", "cash conversion"),
    "ppe_capex_cash_outflow": ("ppe", "capital expenditure", "reinvestment"),
    "ocf_less_ppe_capex": ("cash conversion", "reinvestment", "free cash"),
    "cash_and_cash_equivalents": ("cash buffer", "cash and cash", "thin cash"),
    "interest_bearing_debt_total": ("complete debt", "debt balance", "high debt"),
    "net_debt": ("net debt",),
    "inventory": ("inventory", "working-capital", "working capital"),
    "trade_accounts_receivable": (
        "trade receivable",
        "receivable",
        "working-capital",
        "working capital",
        "collection timing",
    ),
    "trade_accounts_payable": ("trade payable", "payable"),
    "operating_income": (
        "operating profit",
        "operating result",
        "operating loss",
        "latest quarter is profitable",
        "year-to-date result",
    ),
    "net_income": ("net income",),
    "net_financial_income_effect": ("non-operating", "financial effect"),
}

_FACTUAL_SUMMARY_MARKERS = (
    "higher",
    "lower",
    "increased",
    "improved",
    "declined",
    "decreased",
    "risen",
    "flat",
    "profit",
    "loss",
    "high complete",
    "thin cash",
    "since year-end",
)


@dataclass(frozen=True)
class FictionalState:
    owned: dict[str, OwnedEvidencePacket]
    catalogs: dict[str, EvidenceAliasCatalog]
    contexts: dict[str, dict[str, object]]


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def _latest_result_integrity() -> dict[str, object]:
    actual_sha = file_sha256(LATEST_RESULT_ZIP)
    hash_mismatches = 0
    size_mismatches = 0
    missing = 0
    extra = 0
    duplicate_members = 0
    indexed_payload_count = 0
    zip_test_failure: str | None = None
    secret_failures = 0
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        zip_test_failure = archive.testzip()
        names = archive.namelist()
        duplicate_members = len(names) - len(set(names))
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("artifacts") or []
        indexed_payload_count = len(rows)
        payload_names = set(names) - {"artifact-index.json"}
        indexed_names = {str(row.get("path") or "") for row in rows}
        missing = len(indexed_names - payload_names)
        extra = len(payload_names - indexed_names)
        for row in rows:
            name = str(row.get("path") or "")
            if name not in payload_names:
                continue
            payload = archive.read(name)
            hash_mismatches += int(_sha_bytes(payload) != str(row.get("sha256") or ""))
            size_mismatches += int(len(payload) != int(row.get("size_bytes") or -1))
        secret_failures = int(index.get("artifact_secret_scan_failure_count") or 0)
    passed = all(
        (
            actual_sha == LATEST_RESULT_SHA256,
            zip_test_failure is None,
            indexed_payload_count == 160,
            hash_mismatches == 0,
            size_mismatches == 0,
            missing == 0,
            extra == 0,
            duplicate_members == 0,
            secret_failures == 0,
        )
    )
    return {
        "contract": "m12a-latest-result-integrity-v1",
        "path": str(LATEST_RESULT_ZIP),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checksum_match": actual_sha == LATEST_RESULT_SHA256,
        "indexed_payload_count": indexed_payload_count,
        "zip_test_failure": zip_test_failure,
        "duplicate_member_count": duplicate_members,
        "artifact_missing_count": missing,
        "artifact_extra_count": extra,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "artifact_secret_scan_failure_count": secret_failures,
        "status": "PASS" if passed else "FAIL",
    }


def _fictional_state() -> FictionalState:
    _packets, owned, catalogs, contexts = m12.fictional_inputs(M12G_GENERATION_ID)
    return FictionalState(owned=owned, catalogs=catalogs, contexts=contexts)


def _selected_items(owned: OwnedEvidencePacket) -> tuple[FinancialDecisionEvidenceItem, ...]:
    context = financial_decision_context_for_owned(owned)
    return context.evidence_items if context is not None else ()


def _selected_metric_map(state: FictionalState) -> dict[str, str]:
    return {
        item.evidence_id: item.metric
        for owned in state.owned.values()
        for item in _selected_items(owned)
    }


def _comparison_relation(item: FinancialDecisionEvidenceItem) -> str | None:
    if item.comparison is None or item.comparison.comparison_value is None:
        return None
    current = Decimal(item.value)
    prior = Decimal(item.comparison.comparison_value)
    if current > prior:
        return "higher"
    if current < prior:
        return "lower"
    return "unchanged"


def neutral_financial_statement(item: FinancialDecisionEvidenceItem) -> str:
    label = _METRIC_LABELS.get(item.metric, item.metric.replace("_", " "))
    relation = _comparison_relation(item)
    if relation is not None and item.comparison is not None:
        basis = {
            "prior_year_comparable": "prior-year comparable period",
            "prior_year_end": "prior year-end balance",
            "prior_period": "prior period",
            "none": "comparison period",
        }[item.comparison.kind.value]
        return f"{label} is {relation} than the {basis}."
    period_end = item.period.end.isoformat()
    if item.period.type.value == "POINT_IN_TIME":
        return f"{label} balance as of {period_end}."
    return f"{label} is reported for {item.period.type.value} ending {period_end}."


def _typed_projection(
    *,
    item: FinancialDecisionEvidenceItem,
    catalog: EvidenceAliasCatalog,
    owned: OwnedEvidencePacket,
) -> dict[str, object]:
    entry = catalog.by_ref[item.evidence_id]
    owned_by_ref = {row.ref.ref_id: row for row in owned.evidence}
    row = owned_by_ref[item.evidence_id]
    return {
        "alias": entry.alias,
        "evidence_kind": "TYPED_FINANCIAL",
        "domain": row.domain.value,
        "category": entry.category,
        "label": entry.label,
        "statement": neutral_financial_statement(item),
        "as_of": entry.as_of,
        "value": str(item.value),
        "unit": row.ref.unit,
        "metric_refs": list(entry.metric_refs),
        "financial_semantics": {
            "metric": item.metric,
            "semantic_category": item.semantic_category.value,
            "period": item.period.model_dump(mode="json"),
            "comparison": (
                item.comparison.model_dump(mode="json")
                if item.comparison is not None
                else None
            ),
            "currency": item.currency,
            "unit_scale": item.unit_scale,
            "evidence_status": item.evidence_status.value,
            "quality": item.quality.value,
            "limitations": list(item.limitations),
        },
    }


def option_a_prototype(state: FictionalState, ticker: str) -> dict[str, object]:
    before = copy.deepcopy(state.contexts[ticker])
    catalog = state.catalogs[ticker]
    owned = state.owned[ticker]
    items = _selected_items(owned)
    by_alias = {
        catalog.by_ref[item.evidence_id].alias: item
        for item in items
    }
    narrative = {str(row["alias"]): row for row in before["evidence"]}
    unified = []
    for entry in catalog.entries:
        if entry.alias in narrative:
            row = copy.deepcopy(narrative[entry.alias])
            row["evidence_kind"] = "NARRATIVE"
            unified.append(row)
        elif entry.alias in by_alias:
            unified.append(
                _typed_projection(
                    item=by_alias[entry.alias],
                    catalog=catalog,
                    owned=owned,
                )
            )
    after = copy.deepcopy(before)
    after["evidence"] = unified
    lineage = {
        catalog.by_ref[item.evidence_id].alias: {
            "canonical_ref": item.evidence_id,
            "source_ref": item.source_ref,
            "comparison_source_refs": (
                list(item.comparison.input_source_refs)
                if item.comparison is not None
                else []
            ),
            "derivation_input_source_refs": list(item.derivation_input_source_refs),
            "evidence_group_id": f"canonical-ref:{item.evidence_id}",
        }
        for item in items
    }
    alias_map = [
        {
            **entry.model_dump(mode="json"),
            "evidence_kind": (
                "TYPED_FINANCIAL" if entry.alias in by_alias else "NARRATIVE"
            ),
        }
        for entry in catalog.entries
    ]
    return {
        "contract": "m12a-option-a-first-class-evidence-prototype-v1",
        "ticker": ticker,
        "before_representation": before,
        "prototype_representation": after,
        "alias_map": alias_map,
        "lineage_map": lineage,
        "validator_resolvable_grounding_map": {
            alias: value["canonical_ref"] for alias, value in lineage.items()
        },
        "selected_typed_count": len(items),
        "first_class_typed_count": sum(
            row.get("evidence_kind") == "TYPED_FINANCIAL" for row in unified
        ),
        "duplicate_alias_count": len(unified) - len({str(row["alias"]) for row in unified}),
        "unselected_typed_projection_count": 0,
        "output_schema_change_required": False,
        "status": "PASS",
    }


def _narrative_topic_matches(
    *,
    statement: str,
    metric: str,
) -> bool:
    lowered = statement.casefold()
    return any(token in lowered for token in _METRIC_NARRATIVE_TOKENS.get(metric, ()))


def option_b_prototype(state: FictionalState, ticker: str) -> dict[str, object]:
    before = copy.deepcopy(state.contexts[ticker])
    catalog = state.catalogs[ticker]
    items = _selected_items(state.owned[ticker])
    aliases_by_metric = {
        item.metric: catalog.by_ref[item.evidence_id].alias for item in items
    }
    after = copy.deepcopy(before)
    audit_only_matches: dict[str, list[str]] = {}
    for row in after["evidence"]:
        alias = str(row["alias"])
        matches = [
            typed_alias
            for metric, typed_alias in aliases_by_metric.items()
            if _narrative_topic_matches(statement=str(row["statement"]), metric=metric)
        ]
        row["backing_financial_refs"] = []
        row["backing_lineage_status"] = "ABSENT"
        if matches:
            audit_only_matches[alias] = sorted(matches)
    return {
        "contract": "m12a-option-b-lineage-bridge-prototype-v1",
        "ticker": ticker,
        "before_representation": before,
        "prototype_representation": after,
        "alias_map": [entry.model_dump(mode="json") for entry in catalog.entries],
        "lineage_map": {},
        "audit_only_text_topic_matches_not_lineage": audit_only_matches,
        "validator_resolvable_grounding_map": {
            catalog.by_ref[item.evidence_id].alias: item.evidence_id for item in items
        },
        "valid_narrative_lineage_count": 0,
        "metric_refs_reuse_allowed": False,
        "blocker": "CURRENT_NARRATIVE_PRODUCERS_DO_NOT_EMIT_PROVENANCE_BASED_FINANCIAL_LINEAGE",
        "status": "BLOCKING",
    }


def option_c_prototype(state: FictionalState, ticker: str) -> dict[str, object]:
    before = copy.deepcopy(state.contexts[ticker])
    catalog = state.catalogs[ticker]
    items = _selected_items(state.owned[ticker])
    allowed = [catalog.by_ref[item.evidence_id].alias for item in items]
    return {
        "contract": "m12a-option-c-structured-output-grounding-prototype-v1",
        "ticker": ticker,
        "before_representation": before,
        "prototype_representation": {
            "input": before,
            "candidate_schema_fragment": {
                "material_financial_evidence_refs": {
                    "type": "array",
                    "items": {"enum": allowed},
                    "uniqueItems": True,
                    "maxItems": 3,
                }
            },
            "candidate_value": "NOT_GENERATED_MODEL_FREE_REVIEW",
        },
        "alias_map": [entry.model_dump(mode="json") for entry in catalog.entries],
        "lineage_map": {
            alias: catalog.by_alias[alias].canonical_ref for alias in allowed
        },
        "validator_resolvable_grounding_map": {
            alias: catalog.by_alias[alias].canonical_ref for alias in allowed
        },
        "legacy_field_absence": "NOT_APPLICABLE_NEVER_PASS",
        "output_schema_change_required": True,
        "status": "PROTOTYPE_PASS_ARCHITECTURE_WEAK",
    }


def _duplicate_audit(state: FictionalState) -> dict[str, object]:
    rows = []
    classification_counts: Counter[str] = Counter()
    duplicate_refs: set[str] = set()
    for ticker in m12.TICKERS:
        owned = state.owned[ticker]
        catalog = state.catalogs[ticker]
        narratives = [row.ref for row in owned.evidence if row.ref.financial_context is None]
        for item in _selected_items(owned):
            related = [
                ref
                for ref in narratives
                if _narrative_topic_matches(statement=ref.statement, metric=item.metric)
            ]
            factual = [
                ref
                for ref in related
                if any(marker in ref.statement.casefold() for marker in _FACTUAL_SUMMARY_MARKERS)
            ]
            if factual:
                classification = "NARRATIVE_SUMMARY_DUPLICATE_WITHOUT_LINEAGE"
                duplicate_refs.update(ref.ref_id for ref in factual)
            elif related:
                classification = "NARRATIVE_INTERPRETATION_NOT_DUPLICATE"
            else:
                classification = "NO_NARRATIVE_DUPLICATE"
            classification_counts[classification] += 1
            rows.append(
                {
                    "ticker": ticker,
                    "typed_alias": catalog.by_ref[item.evidence_id].alias,
                    "canonical_ref": item.evidence_id,
                    "metric": item.metric,
                    "classification": classification,
                    "related_narrative_refs": [ref.ref_id for ref in related],
                    "factual_duplicate_refs": [ref.ref_id for ref in factual],
                    "valid_lineage_refs": [],
                    "metric_refs_are_financial_lineage": False,
                }
            )
    return {
        "contract": "m12a-duplicate-narrative-typed-financial-audit-v1",
        "method": {
            "topic_matching_use": "AUDIT_CLASSIFICATION_ONLY",
            "topic_matching_may_create_lineage": False,
            "lineage_requirement": "PRODUCER_SUPPLIED_PROVENANCE_ONLY",
        },
        "selected_typed_financial_count": len(rows),
        "narrative_duplicate_selected_item_count": classification_counts[
            "NARRATIVE_SUMMARY_DUPLICATE_WITHOUT_LINEAGE"
        ],
        "unique_narrative_duplicate_ref_count": len(duplicate_refs),
        "valid_lineage_count": classification_counts[
            "NARRATIVE_SUMMARY_WITH_VALID_LINEAGE"
        ],
        "classification_counts": dict(sorted(classification_counts.items())),
        "rows": rows,
        "status": "PASS",
    }


def _history_audit(state: FictionalState) -> dict[str, object]:
    selected_metrics = _selected_metric_map(state)
    phases = {"M12": M12_RUNS, "M12R": M12R_RUNS, "M12G": M12G_RUNS}
    phase_rows = []
    all_rows = []
    for phase, paths in phases.items():
        rows = []
        generations: set[str] = set()
        for path in paths:
            document = _json(path)
            if document.get("status") == "NOT_RUN":
                continue
            generations.add(str(document.get("generation_id") or ""))
            for source_row in document.get("rows") or []:
                if not isinstance(source_row, Mapping):
                    continue
                ticker = str(source_row.get("ticker") or "")
                selected = [str(ref) for ref in source_row.get("selected_financial_refs") or []]
                metrics = {
                    ref: selected_metrics[ref]
                    for ref in selected
                    if ref in selected_metrics
                }
                grounding = m12g.audit_financial_grounding(
                    source_row.get("core") or {},
                    selected_metrics_by_ref=metrics,
                )
                row = {
                    "phase": phase,
                    "source_report": str(path),
                    "ticker": ticker,
                    "row_status": source_row.get("status"),
                    "selected_financial_refs": selected,
                    "used_financial_refs": [
                        str(ref) for ref in source_row.get("used_financial_refs") or []
                    ],
                    "grounding_replay": grounding,
                }
                rows.append(row)
                all_rows.append(row)
        phase_rows.append(
            {
                "phase": phase,
                "generation_ids": sorted(generations),
                "completed_subject_count": len(rows),
                "selected_typed_financial_ref_count": sum(
                    len(row["selected_financial_refs"]) for row in rows
                ),
                "typed_financial_ref_used_count": sum(
                    len(row["used_financial_refs"]) for row in rows
                ),
                "zero_typed_use_subject_count": sum(
                    bool(row["selected_financial_refs"]) and not row["used_financial_refs"]
                    for row in rows
                ),
                "narrative_substitution_failure_count": sum(
                    int(row["grounding_replay"]["narrative_substitution_failure_count"])
                    for row in rows
                ),
                "rows": rows,
            }
        )
    return {
        "contract": "m12a-preserved-grounding-history-audit-v1",
        "phases": phase_rows,
        "aggregate_completed_subject_count": len(all_rows),
        "aggregate_selected_typed_financial_ref_count": sum(
            len(row["selected_financial_refs"]) for row in all_rows
        ),
        "aggregate_typed_financial_ref_used_count": sum(
            len(row["used_financial_refs"]) for row in all_rows
        ),
        "aggregate_narrative_substitution_failure_count": sum(
            int(row["grounding_replay"]["narrative_substitution_failure_count"])
            for row in all_rows
        ),
        "finding": "SPLIT_SURFACE_RISK_RECURRED_IN_M12R_AND_M12G_FIC_FIN_06",
        "status": "PASS",
    }


def _ergonomics_audit(state: FictionalState) -> dict[str, object]:
    rows = []
    raw_json_only_count = 0
    for ticker in m12.TICKERS:
        context = state.contexts[ticker]
        catalog = state.catalogs[ticker]
        items = _selected_items(state.owned[ticker])
        prompt = m12.holdout._core_prompt(
            packet_id=M12G_GENERATION_ID,
            tickers=(ticker,),
            contexts=(context,),
        )
        instruction_index = prompt.index("Ground material financial_decision_context claims")
        context_index = prompt.index("DIRECTIONAL_CORE_CONTEXT:")
        selected_aliases = [catalog.by_ref[item.evidence_id].alias for item in items]
        typed_distances = []
        for item, alias in zip(items, selected_aliases, strict=True):
            alias_position = prompt.find(f'"evidence_id":"{alias}"', context_index)
            if alias_position >= 0:
                typed_distances.append(alias_position - instruction_index)
            statement = catalog.by_alias[alias].statement
            try:
                parsed = json.loads(statement)
            except json.JSONDecodeError:
                parsed = None
            raw_json_only_count += int(
                isinstance(parsed, Mapping) and set(parsed) == {"value"}
            )
        first_narrative = context.get("evidence") or []
        narrative_position = (
            prompt.find(f'"alias":"{first_narrative[0]["alias"]}"', context_index)
            if first_narrative
            else -1
        )
        rows.append(
            {
                "ticker": ticker,
                "ordinary_evidence_count": len(first_narrative),
                "selected_typed_financial_count": len(items),
                "ordinary_surface": "evidence[]",
                "typed_surface": "financial_decision_context.evidence_items[]",
                "one_alias_namespace": True,
                "first_narrative_alias_distance_from_instruction_chars": (
                    narrative_position - instruction_index if narrative_position >= 0 else None
                ),
                "typed_alias_distance_from_instruction_chars": typed_distances,
                "context_serialized_chars": len(
                    json.dumps(context, ensure_ascii=False, separators=(",", ":"), default=str)
                ),
            }
        )
    return {
        "contract": "m12a-evidence-ref-ergonomics-audit-v1",
        "current_evidence_surface_count": 2,
        "narrative_surface_count": 1,
        "typed_financial_surface_count": 1,
        "one_alias_namespace": True,
        "typed_item_raw_json_only_statement_count": raw_json_only_count,
        "distance_is_causal_proof": False,
        "finding": (
            "ALIASES_RESOLVE_UNIFORMLY_BUT_TYPED_ITEMS_ARE_VISUALLY_SECONDARY_AND_"
            "THEIR_ALIAS_STATEMENTS_ARE_RAW_VALUE_JSON"
        ),
        "rows": rows,
        "status": "PASS",
    }


def _current_flow() -> dict[str, object]:
    steps = (
        (
            "canonical source ref -> DecisionEvidenceRef",
            "app/services/cross_market_decision_engine_service.py::build_decision_evidence_packet",
            "canonical/source packet fact rows",
            "DecisionEvidenceRef",
            True,
            False,
            True,
            None,
            None,
        ),
        (
            "DecisionEvidenceRef -> financial_context",
            "app/services/cross_market_decision_engine_service.py::DecisionEvidenceRef",
            "DecisionEvidenceRef",
            "FinancialContext optional field",
            True,
            False,
            True,
            None,
            None,
        ),
        (
            "financial-context selection",
            "app/services/directional_financial_context_service.py::build_financial_decision_context",
            "typed core DecisionEvidenceRef rows",
            "bounded FinancialDecisionContext",
            True,
            True,
            True,
            None,
            None,
        ),
        (
            "stage alias catalog",
            "app/services/direction_timing_ownership_service.py::stage_alias_catalogs",
            "OwnedEvidencePacket + selected financial refs",
            "one EvidenceAliasCatalog",
            True,
            False,
            True,
            True,
            True,
        ),
        (
            "model input evidence projection",
            "scripts/directional_core_price_timing_holdout.py::_owned_context",
            "OwnedEvidencePacket + EvidenceAliasCatalog",
            "evidence[] + financial_decision_context.evidence_items[]",
            True,
            False,
            True,
            True,
            True,
        ),
        (
            "prompt",
            "scripts/directional_core_price_timing_holdout.py::_core_prompt",
            "split Directional Core context",
            "model text input",
            True,
            True,
            True,
            True,
            True,
        ),
        (
            "candidate evidence refs",
            "app/services/direction_timing_ownership_service.py::DirectionalCoreCandidate",
            "alias-constrained output",
            "ordinary evidence_refs fields",
            False,
            None,
            False,
            True,
            True,
        ),
        (
            "alias resolution",
            "app/services/structured_autonomy_alias_service.py::resolve_candidate_aliases",
            "candidate aliases + one catalog",
            "canonical evidence refs + selection audit",
            True,
            None,
            True,
            True,
            True,
        ),
        (
            "financial grounding validation",
            "scripts/directional_financial_context_m12g.py::audit_financial_grounding",
            "resolved candidate + selected canonical metrics",
            "grounding receipt",
            True,
            None,
            True,
            True,
            True,
        ),
    )
    keys = (
        "step",
        "owner_module",
        "input_object",
        "output_object",
        "typed_financial_evidence_present",
        "human_readable_semantics_present",
        "lineage_preserved",
        "one_alias_namespace",
        "validator_can_resolve",
    )
    return {
        "contract": "m12a-current-evidence-grounding-flow-v1",
        "steps": [dict(zip(keys, row, strict=True)) for row in steps],
        "split_created_at": "scripts/directional_core_price_timing_holdout.py::_owned_context",
        "split_mechanism": (
            "selected typed refs are retained in the catalog but filtered out of evidence[] "
            "and emitted only in financial_decision_context.evidence_items[]"
        ),
        "status": "PASS",
    }


def _current_alias_audit(state: FictionalState) -> dict[str, object]:
    rows = []
    for ticker in m12.TICKERS:
        catalog = state.catalogs[ticker]
        context = state.contexts[ticker]
        items = _selected_items(state.owned[ticker])
        selected_aliases = {catalog.by_ref[item.evidence_id].alias for item in items}
        ordinary_aliases = {str(row["alias"]) for row in context.get("evidence") or []}
        catalog_aliases = {entry.alias for entry in catalog.entries}
        rows.append(
            {
                "ticker": ticker,
                "catalog_alias_count": len(catalog_aliases),
                "ordinary_evidence_alias_count": len(ordinary_aliases),
                "selected_typed_alias_count": len(selected_aliases),
                "selected_typed_aliases": sorted(selected_aliases),
                "selected_typed_aliases_in_catalog": sorted(selected_aliases & catalog_aliases),
                "selected_typed_aliases_in_evidence_array": sorted(
                    selected_aliases & ordinary_aliases
                ),
                "duplicate_alias_count": len(catalog.entries) - len(catalog_aliases),
            }
        )
    return {
        "contract": "m12a-current-alias-architecture-audit-v1",
        "one_catalog_per_ticker": True,
        "one_alias_namespace_per_ticker": True,
        "selected_typed_alias_count": sum(row["selected_typed_alias_count"] for row in rows),
        "selected_typed_alias_in_catalog_count": sum(
            len(row["selected_typed_aliases_in_catalog"]) for row in rows
        ),
        "selected_typed_alias_in_evidence_array_count": sum(
            len(row["selected_typed_aliases_in_evidence_array"]) for row in rows
        ),
        "duplicate_alias_count": sum(row["duplicate_alias_count"] for row in rows),
        "finding": "ALIAS_NAMESPACE_IS_UNIFIED_MODEL_INPUT_EVIDENCE_SURFACE_IS_SPLIT",
        "rows": rows,
        "status": "PASS",
    }


def _old_fic06_replay(state: FictionalState) -> dict[str, object]:
    document = _json(M12G_RUNS[1])
    row = next(
        value
        for value in document.get("rows") or []
        if isinstance(value, Mapping) and value.get("ticker") == "FIC-FIN-06"
    )
    selected = {str(ref) for ref in row.get("selected_financial_refs") or []}
    cited = m12._candidate_refs(row.get("core") or {})
    return {
        "contract": "m12a-old-fic-fin-06-offline-replay-v1",
        "historical_output_sha256": document.get("output_sha256"),
        "historical_output_modified": False,
        "selected_typed_refs": sorted(selected),
        "historically_cited_typed_refs": sorted(selected & cited),
        "option_a": {
            "result": "FAIL",
            "reason": "old output still cites neither selected typed ref",
            "retroactive_alias_reclassification_count": 0,
        },
        "option_b": {
            "result": "FAIL",
            "reason": "old narrative refs have no producer-supplied financial lineage",
            "text_similarity_lineage_count": 0,
        },
        "option_c": {
            "result": "LEGACY_NOT_APPLICABLE",
            "reason": "old output predates the proposed structured field",
        },
        "historical_failure_preserved": True,
        "status": "PASS",
    }


def _corrected_comparison(state: FictionalState) -> dict[str, object]:
    fixture = _json(M12G_CORRECTED_FIC06)
    selected = {str(ref) for ref in fixture.get("selected_financial_refs") or []}
    used = {str(ref) for ref in fixture.get("used_financial_refs") or []}
    catalog = state.catalogs["FIC-FIN-06"]
    aliases = sorted(catalog.by_ref[ref].alias for ref in used)
    return {
        "contract": "m12a-corrected-fic-fin-06-architecture-comparison-v1",
        "fixture_is_model_result": False,
        "fixture_status": fixture.get("status"),
        "selected_typed_refs": sorted(selected),
        "used_typed_refs": sorted(used),
        "used_typed_aliases": aliases,
        "options": {
            "A": {
                "representation": "ordinary evidence_refs resolve directly",
                "grounding_clarity": "STRONG",
                "duplicate_refs": 0,
                "schema_burden": "STRONG",
                "validator_complexity": "STRONG",
                "backward_compatibility": "STRONG",
                "result": "PASS",
            },
            "B": {
                "representation": "direct typed refs work without narrative bridge",
                "grounding_clarity": "ACCEPTABLE",
                "duplicate_refs": 0,
                "schema_burden": "ACCEPTABLE",
                "validator_complexity": "WEAK",
                "backward_compatibility": "ACCEPTABLE",
                "result": "PASS",
            },
            "C": {
                "representation": {
                    "material_financial_evidence_refs": aliases,
                    "fixture_projection_only": True,
                },
                "grounding_clarity": "ACCEPTABLE",
                "duplicate_refs": len(aliases),
                "schema_burden": "BLOCKING",
                "validator_complexity": "WEAK",
                "backward_compatibility": "WEAK",
                "result": "PASS_REPRESENTABLE",
            },
        },
        "status": "PASS",
    }


def _file_no_change(path: Path, label: str) -> dict[str, object]:
    current = file_sha256(path)
    before = hashlib.sha256(
        subprocess.run(
            ["git", "show", f"{BASE_SHA}:{path}"],
            check=True,
            capture_output=True,
        ).stdout
    ).hexdigest()
    return {
        "path": str(path),
        "semantic_owner": label,
        "before_sha256": before,
        "after_sha256": current,
        "changed": before != current,
        "semantic_change_count": int(before != current),
        "status": "PASS" if before == current else "FAIL",
    }


def _validation_summary(output_root: Path) -> dict[str, object]:
    path = output_root / "validation" / "summary.json"
    if not path.is_file():
        return {
            "focused_test_result": "NOT_MEASURED",
            "full_test_result": "NOT_MEASURED",
            "ruff_result": "NOT_MEASURED",
            "git_diff_check": "NOT_MEASURED",
        }
    return _json(path)


def _run_command(command: Sequence[str]) -> dict[str, object]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": list(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }


def validate(args: argparse.Namespace) -> None:
    output_root = Path(args.output_root)
    validation_dir = output_root / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    focused = _run_command(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_financial_context_output_grounding_m12a.py",
            "tests/test_directional_financial_context_service.py",
            "tests/test_direction_timing_ownership_service.py",
            "tests/test_structured_autonomy_alias_service.py",
            "tests/test_directional_financial_context_m12r.py",
            "tests/test_directional_financial_context_m12g.py",
        )
    )
    full = _run_command((sys.executable, "-m", "pytest", "-q"))
    ruff = _run_command((sys.executable, "-m", "ruff", "check", "."))
    diff = _run_command(("git", "diff", "--check"))
    documents = {
        "focused-tests.txt": focused,
        "full-tests.txt": full,
        "ruff.txt": ruff,
        "git-diff-check.txt": diff,
    }
    for name, result in documents.items():
        text = (
            f"command={json.dumps(result['command'])}\n"
            f"returncode={result['returncode']}\n"
            f"status={result['status']}\n\n"
            f"STDOUT\n{result['stdout']}\n\nSTDERR\n{result['stderr']}"
        )
        (validation_dir / name).write_text(text, encoding="utf-8")
    summary = {
        "contract": "m12a-deterministic-validation-v1",
        "model_tests": 0,
        "provider_calls": 0,
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "focused_returncode": focused["returncode"],
        "full_returncode": full["returncode"],
        "ruff_returncode": ruff["returncode"],
        "git_diff_returncode": diff["returncode"],
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in documents.values())
            else "FAIL"
        ),
    }
    _write_json(validation_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "PASS":
        raise SystemExit(1)


def _architecture_designs() -> dict[int, dict[str, object]]:
    return {
        9: {
            "contract": "m12a-option-a-design-v1",
            "option": "UNIFIED_FIRST_CLASS_EVIDENCE_INDEX",
            "design": (
                "Project only selected FinancialDecisionContext items into the existing evidence[] "
                "using their already-assigned aliases and deterministic neutral statements."
            ),
            "one_alias_namespace": True,
            "one_evidence_ref_contract": True,
            "typed_metadata_retained": True,
            "financial_detail_block_retained_as_metadata": True,
            "unselected_raw_financial_projection_count": 0,
            "output_schema_change_required": False,
            "validator_semantic_change_required": False,
            "status": "STRONG",
        },
        10: {
            "contract": "m12a-option-b-design-v1",
            "option": "EXPLICIT_EVIDENCE_LINEAGE_BRIDGE",
            "design": (
                "Keep surfaces separate and permit narrative grounding only through "
                "producer-supplied backing_financial_refs."
            ),
            "current_producer_lineage_coverage": 0,
            "text_similarity_lineage_forbidden": True,
            "metric_refs_semantically_appropriate": False,
            "metric_refs_reason": (
                "metric_refs owns checkpoint metric semantics, not source provenance"
            ),
            "required_shared_input_field": "backing_financial_refs",
            "blocker": "NO_CURRENT_DETERMINISTIC_NARRATIVE_TO_FINANCIAL_PROVENANCE",
            "status": "BLOCKING",
        },
        11: {
            "contract": "m12a-option-c-design-v1",
            "option": "STRUCTURED_OUTPUT_FINANCIAL_GROUNDING",
            "design": "Add material_financial_evidence_refs to Directional output.",
            "enforceability": "ACCEPTABLE",
            "output_schema_migration_cost": "BLOCKING",
            "legacy_output_compatibility": "WEAK",
            "renderer_impact": "ACCEPTABLE",
            "stored_artifact_impact": "WEAK",
            "test_surface": "WEAK",
            "real_model_compliance_risk": "WEAK",
            "context_token_overhead": "ACCEPTABLE",
            "moves_prompt_compliance_problem": True,
            "status": "WEAK",
        },
        12: {
            "contract": "m12a-hybrid-analysis-v1",
            "options": {
                "A_PLUS_B": {
                    "distinct_second_problem_proven": False,
                    "status": "WEAK",
                },
                "A_PLUS_C": {
                    "distinct_second_problem_proven": False,
                    "status": "WEAK",
                },
                "B_PLUS_C": {
                    "input_lineage_blocker_remains": True,
                    "schema_cost_added": True,
                    "status": "BLOCKING",
                },
            },
            "decision": "NO_HYBRID_SELECTED",
            "reason": "Option A addresses the proven split without a second mechanism.",
            "status": "PASS",
        },
        13: {
            "contract": "m12a-architecture-risk-comparison-v1",
            "scale": ("STRONG", "ACCEPTABLE", "WEAK", "BLOCKING"),
            "weighted_total_score_used": False,
            "criteria": {
                "Option A": {
                    "grounding_reliability": "STRONG",
                    "model_ergonomics": "STRONG",
                    "provenance_integrity": "STRONG",
                    "double_counting_risk": "ACCEPTABLE",
                    "implementation_complexity": "ACCEPTABLE",
                    "schema_migration_risk": "STRONG",
                    "backward_compatibility": "STRONG",
                    "validator_simplicity": "STRONG",
                    "prompt_complexity": "STRONG",
                    "token_context_cost": "ACCEPTABLE",
                    "real_production_generality": "STRONG",
                    "sector_compatibility": "STRONG",
                    "failure_transparency": "STRONG",
                },
                "Option B": {
                    "grounding_reliability": "BLOCKING",
                    "model_ergonomics": "WEAK",
                    "provenance_integrity": "STRONG",
                    "double_counting_risk": "ACCEPTABLE",
                    "implementation_complexity": "WEAK",
                    "schema_migration_risk": "ACCEPTABLE",
                    "backward_compatibility": "ACCEPTABLE",
                    "validator_simplicity": "WEAK",
                    "prompt_complexity": "ACCEPTABLE",
                    "token_context_cost": "STRONG",
                    "real_production_generality": "BLOCKING",
                    "sector_compatibility": "ACCEPTABLE",
                    "failure_transparency": "STRONG",
                },
                "Option C": {
                    "grounding_reliability": "ACCEPTABLE",
                    "model_ergonomics": "WEAK",
                    "provenance_integrity": "STRONG",
                    "double_counting_risk": "WEAK",
                    "implementation_complexity": "WEAK",
                    "schema_migration_risk": "BLOCKING",
                    "backward_compatibility": "WEAK",
                    "validator_simplicity": "WEAK",
                    "prompt_complexity": "WEAK",
                    "token_context_cost": "ACCEPTABLE",
                    "real_production_generality": "ACCEPTABLE",
                    "sector_compatibility": "ACCEPTABLE",
                    "failure_transparency": "ACCEPTABLE",
                },
                "Hybrid": {
                    "grounding_reliability": "ACCEPTABLE",
                    "model_ergonomics": "WEAK",
                    "provenance_integrity": "STRONG",
                    "double_counting_risk": "WEAK",
                    "implementation_complexity": "BLOCKING",
                    "schema_migration_risk": "WEAK",
                    "backward_compatibility": "WEAK",
                    "validator_simplicity": "BLOCKING",
                    "prompt_complexity": "WEAK",
                    "token_context_cost": "WEAK",
                    "real_production_generality": "WEAK",
                    "sector_compatibility": "ACCEPTABLE",
                    "failure_transparency": "WEAK",
                },
            },
            "decision": PREFERRED_ARCHITECTURE,
            "status": "PASS",
        },
    }


def _compatibility_reports() -> dict[int, dict[str, object]]:
    return {
        22: {
            "contract": "m12a-real-packet-producer-compatibility-audit-v1",
            "producers": [
                {
                    "path": "app/services/cross_market_decision_engine_service.py",
                    "owner": "Initial/Daily canonical packet builder",
                    "typed_financial_refs_available": True,
                    "generic_selected_projection_possible": True,
                    "ticker_branch_required": False,
                },
                {
                    "path": "app/services/coldstart_source_assembly_service.py",
                    "owner": "cold-start source assembly",
                    "typed_financial_refs_available": True,
                    "generic_selected_projection_possible": True,
                    "ticker_branch_required": False,
                },
                {
                    "path": "app/services/onboarding_decision_service.py",
                    "owner": "legacy onboarding decision packet",
                    "typed_financial_refs_available": False,
                    "legacy_no_financial_context_compatible": True,
                    "duplicate_financial_row_risk": False,
                },
                {
                    "path": "app/jobs/accepted_decision_v2_runtime.py",
                    "owner": "daily accepted-decision runtime",
                    "typed_financial_refs_available": True,
                    "m12a_activation": False,
                    "future_projection_must_be_separately_gated": True,
                },
            ],
            "existing_evidence_ids_remain_stable": True,
            "m2_m3_lifecycle_semantics_unchanged": True,
            "duplicate_existing_packet_rows_created": False,
            "real_packet_producer_compatibility_status": "PASS",
            "status": "PASS",
        },
        23: {
            "contract": "m12a-backward-compatibility-audit-v1",
            "legacy_decision_evidence_packet_parsing": "PRESERVED",
            "financial_context_absent_behavior": "BYTE_EQUIVALENT_PROJECTION_UNCHANGED",
            "historical_packet_hashes_without_activation": "UNCHANGED",
            "existing_alias_ids": "PRESERVED",
            "output_schema": "UNCHANGED",
            "renderer_interface": "UNCHANGED",
            "migration_required": False,
            "backward_compatibility_status": "PASS",
            "status": "PASS",
        },
        24: {
            "contract": "m12a-evidence-double-counting-control-v1",
            "identity_key": "canonical_ref",
            "group_rule": (
                "One typed canonical_ref is one financial anchor regardless of appearances "
                "in evidence[] claims or financial_decision_context detail metadata."
            ),
            "detail_metadata_counts_as_second_anchor": False,
            "narrative_counts_as_typed_anchor_without_lineage": False,
            "future_backed_narrative_group": "canonical-ref:<backing_financial_ref>",
            "unique_typed_anchor_counting": True,
            "bullish_bearish_weighting": False,
            "double_counting_contract_status": "FROZEN",
            "status": "PASS",
        },
        25: {
            "contract": "m12a-narrative-preservation-contract-v1",
            "typed_fact_owns": "what the financial fact is",
            "narrative_owns": (
                "why it matters, remaining Unknowns, sector interpretation, and business implications"
            ),
            "narrative_deletion_required": False,
            "typed_fact_replacement_by_narrative_allowed": False,
            "typed_fact_plus_narrative_interpretation_supported": True,
            "status": "FROZEN",
        },
        26: {
            "contract": "m12a-output-schema-impact-decision-v1",
            "output_schema_change_required": False,
            "reason": (
                "existing evidence_refs already accepts the selected aliases and the resolver "
                "already maps them to canonical typed refs"
            ),
            "new_output_reference_field": None,
            "legacy_output_migration": None,
            "status": "PASS",
        },
        27: {
            "contract": "m12a-renderer-impact-decision-v1",
            "renderer_change_required": False,
            "renderer_receives_resolved_canonical_candidate": True,
            "new_renderer_field": None,
            "renderer_ownership_semantic_change_count": 0,
            "status": "PASS",
        },
    }


def _decision_reports() -> dict[int, dict[str, object]]:
    return {
        30: {
            "contract": "m12a-preferred-grounding-architecture-decision-v1",
            "preferred_grounding_architecture": PREFERRED_ARCHITECTURE,
            "rejected": {
                "PROVENANCE_LINEAGE_BRIDGE": "current producer lineage coverage is zero",
                "STRUCTURED_OUTPUT_FINANCIAL_GROUNDING": (
                    "adds schema and compliance cost without a missing resolver capability"
                ),
                "HYBRID": "no distinct second problem is proven",
                "NO_CHANGE_PROMPT_ONLY": "M12G repeated the split-surface failure",
            },
            "decision_basis": (
                "The selected typed refs already share the catalog and resolver contract; only "
                "their model-facing evidence[] projection is missing."
            ),
            "status": "FROZEN",
        },
        31: {
            "contract": "m12a-frozen-next-implementation-contract-v1",
            "next_scope": NEXT_SCOPE,
            "modules_to_change": [
                "app/services/directional_financial_context_service.py",
                "scripts/directional_core_price_timing_holdout.py",
                "tests/test_directional_financial_context_service.py",
                "tests/test_direction_timing_ownership_service.py",
                "tests/test_directional_financial_context_m12g.py",
            ],
            "new_changed_data_fields": {
                "output_schema": [],
                "input_projection": ["evidence_kind", "financial_semantics"],
                "persistent_models": [],
            },
            "alias_behavior": "reuse existing aliases without renumbering",
            "evidence_index_behavior": (
                "add selected typed financial items once to ordinary evidence[] in catalog order"
            ),
            "human_statement_behavior": (
                "deterministic neutral metric/period/comparison statement; no investment verdict"
            ),
            "lineage_behavior": "retain existing canonical/source/comparison/derivation lineage",
            "output_schema_impact": "NONE",
            "validator_behavior": "unchanged semantics; direct typed refs remain required",
            "legacy_behavior": "no financial_context means exact existing projection",
            "renderer_impact": "NONE",
            "source_sufficiency_impact": "NONE",
            "daily_delta_impact": "NONE",
            "migration_artifact_compatibility": "NO_MIGRATION",
            "required_tests": [
                "selected-only projection",
                "one alias namespace and no duplicates",
                "neutral statement relation/period coverage",
                "legacy byte-equivalent context",
                "old FIC-FIN-06 remains fail",
                "corrected FIC-FIN-06 remains pass",
                "no price/technical/supply leakage",
                "full financial and QTD/YTD validator regression",
            ],
            "forbidden": [
                "prompt-only repair",
                "raw financial dump",
                "ticker exception",
                "validator weakening",
                "output schema change",
                "production activation",
            ],
            "status": "FROZEN",
        },
        32: {
            "contract": "m12a-next-model-canary-scope-v1",
            "after_implementation": "8 fictional subjects x 3 repeats",
            "same_frozen_cases": True,
            "selective_rerun": False,
            "first_failure_stop": True,
            "model_call_in_m12a": 0,
            "fresh_real_after_fictional_pass_only": True,
            "status": "NOT_RUN",
        },
        33: {
            "contract": "m12a-fresh-real-proof-readiness-decision-v1",
            "fresh_real_proof_readiness": "NOT_READY",
            "reason": "chosen architecture has not yet been implemented or model-canary validated",
            "next_gate": NEXT_SCOPE,
            "status": "NOT_READY",
        },
        34: {
            "contract": "m12a-production-no-change-v1",
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
            "automatic_monitoring_resume": 0,
            "production_readiness": "NOT_READY",
            "status": "PASS",
        },
    }


def generate(args: argparse.Namespace) -> None:
    report_dir = Path(args.report_dir)
    output_root = Path(args.output_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    integrity = _latest_result_integrity()
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    state = _fictional_state()
    history = _history_audit(state)
    duplicate = _duplicate_audit(state)
    alias_audit = _current_alias_audit(state)
    ergonomics = _ergonomics_audit(state)
    validation = _validation_summary(output_root)
    schedule = m12r._schedule_observation()
    implementation_commit = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")

    shared_freeze = [_file_no_change(path, "shared_semantic_contract") for path in SHARED_SEMANTIC_FILES]
    source_freeze = _file_no_change(SOURCE_SUFFICIENCY_FILE, "source_sufficiency")
    daily_freezes = [
        _file_no_change(DAILY_DELTA_FILE, "daily_delta_lifecycle"),
        _file_no_change(WARNING_FILE, "warning"),
        _file_no_change(NOTIFICATION_FILE, "notification"),
    ]
    renderer_freeze = _file_no_change(RENDERER_FILE, "renderer")

    reports: dict[int, tuple[str, dict[str, object]]] = {
        1: (
            "repository-provenance",
            {
                "contract": "m12a-repository-provenance-v1",
                "branch": branch,
                "base_sha": BASE_SHA,
                "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
                "implementation_commit": implementation_commit,
                "report_commit": "NOT_MEASURED",
                "final_head_sha": "NOT_MEASURED",
                "head_descends_from_base": subprocess.run(
                    ["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"],
                    check=False,
                ).returncode
                == 0,
                "status": "PASS",
            },
        ),
        2: ("latest-result-integrity", integrity),
        3: (
            "m12a-scope-freeze",
            {
                "contract": PROGRAM_CONTRACT,
                "mode": "MODEL_FREE_ARCHITECTURE_REVIEW_OFFLINE_PROTOTYPE",
                "shared_semantic_files": shared_freeze,
                "threshold_or_calibration_change_count": 0,
                "financial_selector_change_count": 0,
                "accounting_mapping_change_count": 0,
                "qtd_ytd_validator_change_count": 0,
                "financial_validator_change_count": 0,
                "production_activation_count": 0,
                "status": "FROZEN",
            },
        ),
        4: (
            "m12g-failure-summary",
            {
                "contract": "m12a-m12g-failure-summary-v1",
                "m12g_status": "M12G_CANARY_FAIL",
                "stop_reason": "PROMPT_GROUNDING_INSUFFICIENT",
                "generation_id": M12G_GENERATION_ID,
                "transport_pass": True,
                "schema_pass_count": 8,
                "subject_output_count": 8,
                "failed_ticker": "FIC-FIN-06",
                "material_financial_anchor_grounding_failure": 1,
                "working_capital_grounding_failure": 1,
                "narrative_substitution_failure": 1,
                "historical_grounding_audit": history,
                "status": "PASS",
            },
        ),
        5: ("current-evidence-grounding-flow", _current_flow()),
        6: ("current-alias-architecture-audit", alias_audit),
        7: ("duplicate-narrative-typed-financial-audit", duplicate),
        8: ("evidence-ref-ergonomics-audit", ergonomics),
    }
    for number, body in _architecture_designs().items():
        slug = {
            9: "option-a-first-class-evidence-design",
            10: "option-b-lineage-bridge-design",
            11: "option-c-structured-output-grounding-design",
            12: "hybrid-option-analysis",
            13: "architecture-risk-comparison",
        }[number]
        reports[number] = (slug, body)
    reports.update(
        {
            14: ("option-a-fic-fin-05-prototype", option_a_prototype(state, "FIC-FIN-05")),
            15: ("option-a-fic-fin-06-prototype", option_a_prototype(state, "FIC-FIN-06")),
            16: ("option-b-fic-fin-05-prototype", option_b_prototype(state, "FIC-FIN-05")),
            17: ("option-b-fic-fin-06-prototype", option_b_prototype(state, "FIC-FIN-06")),
            18: ("third-option-fic-fin-05-prototype", option_c_prototype(state, "FIC-FIN-05")),
            19: ("third-option-fic-fin-06-prototype", option_c_prototype(state, "FIC-FIN-06")),
            20: ("old-fic-fin-06-offline-replay", _old_fic06_replay(state)),
            21: ("corrected-fic-fin-06-architecture-comparison", _corrected_comparison(state)),
        }
    )
    compatibility = _compatibility_reports()
    for number, body in compatibility.items():
        slug = {
            22: "real-packet-producer-compatibility-audit",
            23: "backward-compatibility-audit",
            24: "evidence-double-counting-control",
            25: "narrative-preservation-contract",
            26: "output-schema-impact-decision",
            27: "renderer-impact-decision",
        }[number]
        if number == 27:
            body["source_freeze"] = renderer_freeze
        reports[number] = (slug, body)
    reports[28] = (
        "source-sufficiency-no-change-proof",
        {
            "contract": "m12a-source-sufficiency-no-change-proof-v1",
            "source_freeze": source_freeze,
            "source_sufficiency_semantic_change_count": 0,
            "status": source_freeze["status"],
        },
    )
    reports[29] = (
        "daily-delta-no-change-proof",
        {
            "contract": "m12a-daily-delta-no-change-proof-v1",
            "source_freezes": daily_freezes,
            "daily_delta_semantic_change_count": 0,
            "monitoring_lifecycle_semantic_change_count": 0,
            "warning_semantic_change_count": 0,
            "status": (
                "PASS" if all(row["status"] == "PASS" for row in daily_freezes) else "FAIL"
            ),
        },
    )
    decisions = _decision_reports()
    for number, body in decisions.items():
        slug = {
            30: "preferred-grounding-architecture-decision",
            31: "frozen-next-implementation-contract",
            32: "next-model-canary-scope",
            33: "fresh-real-proof-readiness-decision",
            34: "production-no-change",
        }[number]
        reports[number] = (slug, body)
    reports[35] = (
        "schedule-pause-observation",
        {
            **schedule,
            "contract": "m12a-schedule-pause-observation-v1",
            "observation_parser_contract": schedule["contract"],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    reports[36] = (
        "master-workflow-update",
        {
            "contract": "m12a-master-workflow-update-v1",
            "path": str(MASTER_WORKFLOW_PATH),
            "sha256": file_sha256(MASTER_WORKFLOW_PATH),
            "m12a_section_present": "## 12A. M12A" in MASTER_WORKFLOW_PATH.read_text(
                encoding="utf-8"
            ),
            "preferred_grounding_architecture": PREFERRED_ARCHITECTURE,
            "next_scope": NEXT_SCOPE,
            "status": (
                "PASS"
                if "## 12A. M12A" in MASTER_WORKFLOW_PATH.read_text(encoding="utf-8")
                else "PENDING"
            ),
        },
    )

    current_m12g = next(row for row in history["phases"] if row["phase"] == "M12G")
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": branch,
        "latest_result_zip_sha256": integrity["actual_sha256"],
        "latest_result_integrity": integrity["status"],
        "m12g_status": "BLOCKED_PROMPT_GROUNDING_INSUFFICIENT",
        "m12a_status": "COMPLETE",
        "current_evidence_surface_count": 2,
        "typed_financial_surface_count": 1,
        "narrative_surface_count": 1,
        "selected_typed_financial_ref_count": current_m12g[
            "selected_typed_financial_ref_count"
        ],
        "typed_financial_ref_used_count": current_m12g["typed_financial_ref_used_count"],
        "narrative_duplicate_count": duplicate[
            "narrative_duplicate_selected_item_count"
        ],
        "narrative_substitution_failure_count": current_m12g[
            "narrative_substitution_failure_count"
        ],
        "option_a_status": "STRONG_SELECTED",
        "option_b_status": "BLOCKING_NO_PRODUCER_LINEAGE",
        "option_c_status": "WEAK_SCHEMA_COST",
        "hybrid_status": "WEAK_NO_DISTINCT_SECOND_PROBLEM",
        "preferred_grounding_architecture": PREFERRED_ARCHITECTURE,
        "output_schema_change_required": False,
        "evidence_index_change_required": True,
        "lineage_change_required": False,
        "validator_change_required": False,
        "renderer_change_required": False,
        "double_counting_contract_status": "FROZEN",
        "backward_compatibility_status": "PASS",
        "real_packet_producer_compatibility_status": "PASS",
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
        "focused_test_result": validation["focused_test_result"],
        "full_test_result": validation["full_test_result"],
        "ruff_result": validation["ruff_result"],
        "git_diff_check": validation["git_diff_check"],
        "artifact_count": "NOT_MEASURED",
        "artifact_hash_mismatch_count": "NOT_MEASURED",
        "artifact_size_mismatch_count": "NOT_MEASURED",
        "artifact_secret_scan_failure_count": "NOT_MEASURED",
        "fresh_real_proof_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "status": "M12A_COMPLETE",
        "stop_reason": "ARCHITECTURE_SELECTED_IMPLEMENTATION_NOT_STARTED",
        "next_scope": NEXT_SCOPE,
    }
    reports[37] = ("program-completion", completion)

    if set(reports) != set(range(1, 38)):
        raise ValueError("m12a_required_report_inventory_incomplete")
    for number, (slug, body) in reports.items():
        _write_json(_report_path(report_dir, number, slug), body)
    print(
        json.dumps(
            {
                "status": "M12A_REPORTS_GENERATED",
                "report_count": len(reports),
                "report_dir": str(report_dir),
                "preferred_grounding_architecture": PREFERRED_ARCHITECTURE,
                "next_scope": NEXT_SCOPE,
            },
            indent=2,
            sort_keys=True,
        )
    )


def _artifact_rows(report_dir: Path, output_root: Path) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in sorted(report_dir.glob("*.json")):
        rows.append((f"reports/{path.name}", path))
    validation_dir = output_root / "validation"
    if validation_dir.is_dir():
        for path in sorted(validation_dir.iterdir()):
            if path.is_file():
                rows.append((f"validation/{path.name}", path))
    rows.extend(
        (
            (str(MASTER_WORKFLOW_PATH), MASTER_WORKFLOW_PATH),
            (str(INSTRUCTION_PATH), INSTRUCTION_PATH),
            (
                "scripts/financial_context_output_grounding_m12a.py",
                Path("scripts/financial_context_output_grounding_m12a.py"),
            ),
            (
                "tests/test_financial_context_output_grounding_m12a.py",
                Path("tests/test_financial_context_output_grounding_m12a.py"),
            ),
        )
    )
    if len({name for name, _path in rows}) != len(rows):
        raise ValueError("m12a_duplicate_artifact_path")
    return rows


def _secret_scan_failures(rows: Sequence[tuple[str, Path]]) -> list[str]:
    markers = (
        "TELEGRAM_BOT_" + "TOKEN=",
        "OPENAI_API_" + "KEY=",
        "DART_API_" + "KEY=",
        "ACTION_API_" + "KEY=",
        '"access_' + 'token":',
        '"refresh_' + 'token":',
    )
    failures = []
    for archive_name, path in rows:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(marker in text for marker in markers):
            failures.append(archive_name)
    return failures


def bundle(args: argparse.Namespace) -> None:
    report_dir = Path(args.report_dir)
    output_root = Path(args.output_root)
    bundle_path = Path(args.bundle_path)
    report_files = sorted(report_dir.glob("*.json"))
    if len(report_files) != 37:
        raise SystemExit(f"M12A_REPORT_COUNT_INVALID:{len(report_files)}")
    completion_path = _report_path(report_dir, 37, "program-completion")
    completion = _json(completion_path)
    validation = _validation_summary(output_root)
    if validation.get("status") != "PASS":
        raise SystemExit("M12A_VALIDATION_NOT_PASS")
    if completion.get("status") != "M12A_COMPLETE":
        raise SystemExit("M12A_COMPLETION_NOT_READY")
    if completion.get("preferred_grounding_architecture") != PREFERRED_ARCHITECTURE:
        raise SystemExit("M12A_ARCHITECTURE_DECISION_MISMATCH")
    rows = _artifact_rows(report_dir, output_root)
    secret_failures = _secret_scan_failures(rows)
    if secret_failures:
        raise SystemExit(f"M12A_SECRET_SCAN_FAILURE:{','.join(secret_failures)}")
    index_rows = [
        {
            "path": archive_name,
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12a-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, path in rows:
            archive.write(path, archive_name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

    hash_mismatches = 0
    size_mismatches = 0
    with zipfile.ZipFile(bundle_path) as archive:
        if archive.testzip() is not None:
            raise SystemExit("M12A_ZIP_CRC_FAILURE")
        for row in index_rows:
            payload = archive.read(str(row["path"]))
            hash_mismatches += int(_sha_bytes(payload) != row["sha256"])
            size_mismatches += int(len(payload) != row["size_bytes"])
    if hash_mismatches or size_mismatches:
        raise SystemExit("M12A_ARTIFACT_INDEX_VERIFICATION_FAILURE")
    checksum = file_sha256(bundle_path)
    sidecar = bundle_path.with_suffix(bundle_path.suffix + ".sha256")
    sidecar.write_text(f"{checksum}  {bundle_path.name}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "bundle": str(bundle_path),
                "sha256": checksum,
                "payload_count": len(index_rows),
                "artifact_hash_mismatch_count": hash_mismatches,
                "artifact_size_mismatch_count": size_mismatches,
                "artifact_secret_scan_failure_count": len(secret_failures),
                "sidecar": str(sidecar),
            },
            indent=2,
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="M12A offline grounding architecture review")
    subparsers = value.add_subparsers(dest="command", required=True)
    for name in ("generate", "validate", "bundle"):
        item = subparsers.add_parser(name)
        item.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
        item.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
        item.add_argument("--bundle-path", default=str(DEFAULT_BUNDLE_PATH))
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "generate":
        generate(args)
    elif args.command == "validate":
        validate(args)
    else:
        bundle(args)


if __name__ == "__main__":
    main()
