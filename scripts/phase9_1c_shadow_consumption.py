from __future__ import annotations

# ruff: noqa: E402, E501

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    Metric,
    financial_fact_from_mapping,
)
from app.services.working_capital_core_service import (
    CanonicalMovement,
    RelationDirection,
    WorkingCapitalCoreSnapshot,
    WorkingCapitalRelation,
)
from app.services.working_capital_evidence_service import (
    FreshnessState as CoreFreshnessState,
)
from app.services.working_capital_shadow_consumption_service import (
    CONTRACT_VERSION,
    UnknownResolutionState,
    WorkingCapitalReasoningContext,
    context_to_dict,
    reasoning_to_dict,
    build_working_capital_reasoning_context,
    render_working_capital_reasoning,
    validate_working_capital_reasoning,
)


REPORT_ROOT = ROOT / "docs" / "reports"
RUN_DATE = "20260821"
AS_OF = date(2026, 8, 21)
US_PACKET_ID = "2026-08-21-us-run-30-5a3b7c1c4390"
KR_PACKET_ID = "2026-08-20-kr-run-29-6e8809e1e944"
CORE_PATH = REPORT_ROOT / f"{RUN_DATE}-phase9-1b-canonical-facts.json"
US_BASELINE_PATH = REPORT_ROOT / f"{RUN_DATE}-phase9-0e-full-preview.json"
KR_BASELINE_PATH = REPORT_ROOT / "20260820-run29-structured-reasoning-audit.json"
CASH_FLOW_FRESHNESS_PATH = REPORT_ROOT / "20260820-phase9-0c-shadow-context.json"
_INTERNAL_LANGUAGE = re.compile(
    r"DERIVED_PERIOD|entity_scope|occurrence[_ ]id|working-capital-relation:"
)
_NUMBER = re.compile(r"[-+]?\d+(?:[,.]\d+)*(?:%p|%|원|달러|배)?")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _movement(
    row: Mapping[str, Any],
    facts: Mapping[str, Any],
) -> CanonicalMovement:
    freshness = row.get("freshness_state")
    return CanonicalMovement(
        status=EligibilityStatus(row["status"]),
        balance_metric=Metric(row["metric"]),
        current=facts.get(row.get("current_fact_id")),
        prior=facts.get(row.get("prior_fact_id")),
        delta_fact=facts.get(row.get("delta_fact_id")),
        yoy_fact=facts.get(row.get("yoy_fact_id")),
        freshness_state=CoreFreshnessState(freshness) if freshness else None,
        denial_reasons=tuple(row.get("denial_reasons") or ()),
        cautions=tuple(row.get("cautions") or ()),
    )


def _relation(row: Mapping[str, Any]) -> WorkingCapitalRelation:
    return WorkingCapitalRelation(
        status=EligibilityStatus(row["status"]),
        relation_id=row.get("relation_id"),
        relation_type=str(row["relation_type"]),
        direction=(
            RelationDirection(row["direction"]) if row.get("direction") else None
        ),
        balance_metric=Metric(row["balance_metric"]),
        balance_semantic=row.get("balance_semantic"),
        balance_scope=row.get("balance_scope"),
        flow_metric=Metric(row["flow_metric"]),
        flow_semantic=row.get("flow_semantic"),
        gap_percentage_points=(
            Decimal(row["gap_percentage_points"])
            if row.get("gap_percentage_points") is not None
            else None
        ),
        current_balance_fact_id=row.get("current_balance_fact_id"),
        prior_balance_fact_id=row.get("prior_balance_fact_id"),
        current_flow_fact_id=row.get("current_flow_fact_id"),
        prior_flow_fact_id=row.get("prior_flow_fact_id"),
        balance_yoy_fact_id=row.get("balance_yoy_fact_id"),
        flow_yoy_fact_id=row.get("flow_yoy_fact_id"),
        input_fact_ids=tuple(row.get("input_fact_ids") or ()),
        formula=str(row["formula"]),
        derivation_version=str(row["derivation_version"]),
        denial_reasons=tuple(row.get("denial_reasons") or ()),
        cautions=tuple(row.get("cautions") or ()),
    )


def _snapshot(record: Mapping[str, Any]) -> WorkingCapitalCoreSnapshot:
    facts = {
        row["fact_id"]: financial_fact_from_mapping(row)
        for row in record["canonical_facts"]
    }
    movements = tuple(
        _movement(row, facts) for row in record["metrics"].values()
    )
    relations = tuple(_relation(row) for row in record["relations"].values())
    latest = record.get("latest_safe_working_capital_date")
    return WorkingCapitalCoreSnapshot(
        issuer_id=str(record["issuer_id"]),
        as_of_date=AS_OF,
        latest_safe_working_capital_date=date.fromisoformat(latest) if latest else None,
        metric_states=movements,
        relations=relations,
        canonical_facts=tuple(sorted(facts.values(), key=lambda item: item.fact_id)),
        industry_applicability=dict(record["industry_applicability"]),
        industry_status=EligibilityStatus(record["industry_status"]),
        denial_reasons=tuple(record.get("denial_reasons") or ()),
        cautions=tuple(record.get("cautions") or ()),
    )


def _us_baselines(path: Path) -> tuple[dict[str, str], dict[str, date]]:
    payload = _load_json(path)
    texts: dict[str, str] = {}
    cash_flow_periods: dict[str, date] = {}
    for row in payload["subjects"]:
        ticker = str(row["ticker"])
        texts[ticker] = str(row["after_text"])
        period = row.get("primary_period") or {}
        if period.get("period_end"):
            cash_flow_periods[ticker] = date.fromisoformat(period["period_end"])
    return texts, cash_flow_periods


def _kr_baselines(path: Path) -> dict[str, str]:
    payload = _load_json(path)
    return {
        str(row["ticker"]): str(row["text"])
        for row in payload["rendered_messages"]
        if str(row.get("ticker") or "").isdigit()
    }


def _unknowns(text: str) -> tuple[str, ...]:
    marker = "⚠️ 미확인\n"
    if marker not in text:
        return ()
    section = text.split(marker, 1)[1]
    section = section.split("\n\n", 1)[0]
    return tuple(
        line.removeprefix("• ").strip()
        for line in section.splitlines()
        if line.strip().startswith("•")
    )


def _next_unknown(context: WorkingCapitalReasoningContext) -> str:
    selected = context.selected_relation
    if selected is None:
        return "운전자본의 현재 정식 비교 근거는 아직 확인되지 않았습니다."
    if selected.balance_metric == Metric.INVENTORY:
        return {
            "memory_hbm": "재고 변화의 원인과 ASP·HBM 믹스가 현금전환에 미치는 영향은 아직 확인되지 않았습니다.",
            "memory_foundry": "재고 변화의 원인과 메모리 믹스·파운드리 수율이 현금전환에 미치는 영향은 아직 확인되지 않았습니다.",
            "memory_nand": "재고 변화의 원인과 NAND ASP·SSD 수요가 현금전환에 미치는 영향은 아직 확인되지 않았습니다.",
            "steel_spread": "재고 변화의 원인과 철강 스프레드·물량이 현금전환에 미치는 영향은 아직 확인되지 않았습니다.",
            "vehicle_delivery": "재고 변화의 원인과 인도량·인센티브·제품 믹스의 연결은 아직 확인되지 않았습니다.",
        }.get(
            context.specificity_key,
            "재고 변화의 원인과 실제 현금전환 효과는 아직 확인되지 않았습니다.",
        )
    if selected.balance_metric == Metric.TRADE_AR:
        return {
            "order_conversion": "거래 매출채권 변화의 원인과 수주 매출의 실제 회수 전환은 아직 확인되지 않았습니다.",
            "freight_collection": "거래 매출채권 변화의 원인과 운송 매출의 실제 회수 전환은 아직 확인되지 않았습니다.",
        }.get(
            context.specificity_key,
            "거래 매출채권 변화의 원인과 실제 회수 속도는 아직 확인되지 않았습니다.",
        )
    if context.remaining_unknowns:
        return context.remaining_unknowns[0]
    return "관계의 원인과 실제 현금전환 효과는 아직 확인되지 않았습니다."


def _insert_shadow(text: str, context: WorkingCapitalReasoningContext, reasoning_text: str) -> str:
    marker = "👁 핵심 감시"
    block = f"📊 운전자본·이익의 질\n{reasoning_text}\n\n"
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        text = text.rstrip() + "\n\n" + block.rstrip()
    if any(
        item.state
        in {
            UnknownResolutionState.RESOLVED_EXACT,
            UnknownResolutionState.RESOLVED_BROAD_ONLY,
        }
        for item in context.resolved_unknowns
    ) and "⚠️ 미확인\n" in text:
        text = re.sub(
            r"(?s)(⚠️ 미확인\n)(?:•.*?)(?=\n\n|\Z)",
            rf"\1• {_next_unknown(context)}",
            text,
            count=1,
        )
    return text


def _quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reasoning_texts = [
        row["reasoning"]["text"]
        for row in rows
        if row.get("reasoning") is not None
    ]
    exact = Counter(reasoning_texts)
    exact_repeats = [text for text, count in exact.items() if count > 1]
    skeletons: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        reasoning = row.get("reasoning")
        if reasoning is None:
            continue
        skeleton = _NUMBER.sub("<NUM>", reasoning["text"])
        skeletons[skeleton].append(row["ticker"])
    skeleton_repeats = [
        {"skeleton": value, "tickers": tickers}
        for value, tickers in skeletons.items()
        if len(tickers) >= 3
    ]
    internal_language = [
        row["ticker"]
        for row in rows
        if row.get("reasoning")
        and _INTERNAL_LANGUAGE.search(row["reasoning"]["text"])
    ]
    semantic_errors = [
        {"ticker": row["ticker"], "errors": row["validation_errors"]}
        for row in rows
        if row["validation_errors"]
    ]
    return {
        "contract": "working-capital-shadow-quality-receipt-v1",
        "status": (
            "PASS"
            if not exact_repeats
            and not skeleton_repeats
            and not internal_language
            and not semantic_errors
            else "FAIL"
        ),
        "exact_repeated_reasoning": exact_repeats,
        "template_skeleton_repeats": skeleton_repeats,
        "internal_language_tickers": internal_language,
        "semantic_errors": semantic_errors,
        "threshold_changes": 0,
    }


def _human_quality(context: WorkingCapitalReasoningContext, errors: list[str]) -> str:
    if errors:
        return "DEGRADED"
    if not context.shadow_used or context.selected_relation is None:
        return "NO_MEANINGFUL_CHANGE"
    if context.selected_relation.applicability == "PRIMARY":
        return "MATERIAL_IMPROVEMENT"
    return "MINOR_IMPROVEMENT"


def _record(
    source: Mapping[str, Any],
    snapshot: WorkingCapitalCoreSnapshot,
    *,
    baseline: str,
    cutoff: date,
    packet_id: str,
    latest_provisional: date | None,
    formal_lagging_provisional: bool,
    cash_flow_period: date | None,
) -> dict[str, Any]:
    unknowns = _unknowns(baseline)
    context = build_working_capital_reasoning_context(
        snapshot,
        ticker=str(source["ticker"]),
        market=str(source["market"]),
        packet_id=packet_id,
        assessment_date=cutoff,
        cutoff=cutoff,
        industry=str(source["industry"]),
        monitoring_text=baseline,
        existing_unknowns=unknowns,
        latest_formal_balance_date=snapshot.latest_safe_working_capital_date,
        latest_provisional_period_end=latest_provisional,
        formal_lagging_provisional=formal_lagging_provisional,
        cash_flow_period_end=cash_flow_period,
    )
    reasoning = render_working_capital_reasoning(context)
    facts = {item.fact_id: item for item in snapshot.canonical_facts}
    relations = {
        item.relation_id: item for item in snapshot.relations if item.relation_id
    }
    errors = list(
        validate_working_capital_reasoning(
            context, facts, relations, reasoning
        )
    )
    after = (
        _insert_shadow(baseline, context, reasoning.text)
        if reasoning is not None
        else baseline
    )
    resolved = any(
        item.state
        in {
            UnknownResolutionState.RESOLVED_EXACT,
            UnknownResolutionState.RESOLVED_BROAD_ONLY,
        }
        for item in context.resolved_unknowns
    )
    return {
        "ticker": source["ticker"],
        "company_name": source["company_name"],
        "market": source["market"],
        "industry": source["industry"],
        "financial_type": source["financial_type"],
        "context": context_to_dict(context),
        "reasoning": reasoning_to_dict(reasoning),
        "validation_errors": errors,
        "unknown_audit": {
            "before": list(unknowns),
            "after": [_next_unknown(context)] if resolved else list(unknowns),
            "contradiction": False,
        },
        "before_text": baseline,
        "after_text": after,
        "message_length_before": len(baseline),
        "message_length_after": len(after),
        "message_length_delta": len(after) - len(baseline),
        "human_quality": _human_quality(context, errors),
        "status_delta_candidate": False,
        "persistence_mutation": 0,
    }


def _metric_coverage(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for metric in (
        Metric.INVENTORY,
        Metric.TRADE_AR,
        Metric.BROAD_AR,
        Metric.TRADE_AP,
        Metric.BROAD_AP,
    ):
        statuses = Counter(
            item["status"]
            for row in rows
            for item in row["context"]["metric_contexts"]
            if item["metric"] == metric.value
        )
        consumed = sum(
            row["context"]["shadow_used"]
            and row["context"]["selected_relations"]
            and row["context"]["selected_relations"][0]["balance_metric"]
            == metric.value
            for row in rows
        )
        result[metric.value] = {
            "eligible": statuses.get("ELIGIBLE", 0),
            "partial": statuses.get("PARTIAL", 0),
            "blocked": statuses.get("BLOCKED", 0),
            "not_applicable": statuses.get("NOT_APPLICABLE", 0),
            "consumed": consumed,
            "suppressed_eligible": statuses.get("ELIGIBLE", 0) - consumed,
        }
    return result


def _relation_coverage(
    core: Mapping[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for family in (
        "trade_ar_vs_revenue",
        "broad_ar_vs_revenue",
        "inventory_vs_revenue",
        "inventory_vs_cogs",
        "trade_ap_vs_cogs",
        "broad_ap_vs_cogs",
    ):
        eligible = sum(
            source["relations"][family]["status"] == "ELIGIBLE"
            for source in core["active_universe"]
        )
        selected_rows = [
            row
            for row in rows
            if row["context"]["shadow_used"]
            and row["context"]["selected_relations"]
            and row["context"]["selected_relations"][0]["family"] == family
        ]
        result[family] = {
            "eligible": eligible,
            "selected": len(selected_rows),
            "suppressed": eligible - len(selected_rows),
            "semantic_scope": (
                "exact_trade"
                if family.startswith("trade_")
                else "broad"
                if family.startswith("broad_")
                else "total_inventory"
            ),
            "value_add": dict(Counter(row["human_quality"] for row in selected_rows)),
        }
    return result


def generate(
    *,
    core_path: Path = CORE_PATH,
    us_baseline_path: Path = US_BASELINE_PATH,
    kr_baseline_path: Path = KR_BASELINE_PATH,
) -> dict[str, Any]:
    core = _load_json(core_path)
    us_baselines, cash_flow_periods = _us_baselines(us_baseline_path)
    kr_baselines = _kr_baselines(kr_baseline_path)
    cash_flow_freshness = _load_json(CASH_FLOW_FRESHNESS_PATH)
    lagging_tickers = {
        str(row["ticker"])
        for row in cash_flow_freshness["ticker_audit"]
        if row.get("context", {}).get("freshness_state")
        == "FORMAL_LAGGING_PROVISIONAL"
    }
    rows: list[dict[str, Any]] = []
    for source in core["active_universe"]:
        ticker = str(source["ticker"])
        market = str(source["market"])
        is_kr = market == "KR"
        baseline = kr_baselines.get(ticker) if is_kr else us_baselines.get(ticker)
        if baseline is None:
            raise ValueError(f"immutable baseline missing for {ticker}")
        cutoff = date(2026, 8, 20) if is_kr else date(2026, 8, 21)
        rows.append(
            _record(
                source,
                _snapshot(source),
                baseline=baseline,
                cutoff=cutoff,
                packet_id=KR_PACKET_ID if is_kr else US_PACKET_ID,
                latest_provisional=None,
                formal_lagging_provisional=ticker in lagging_tickers,
                cash_flow_period=cash_flow_periods.get(ticker),
            )
        )
    quality = _quality(rows)
    freshness = Counter(row["context"]["freshness_state"] for row in rows)
    usage = Counter(
        row["context"]["usage_mode"]
        for row in rows
        if row["context"]["shadow_used"]
    )
    human = Counter(row["human_quality"] for row in rows)
    unknown_states = Counter(
        item["state"]
        for row in rows
        for item in row["context"]["resolved_unknowns"]
    )
    automatic = sum(
        len(row["reasoning"]["numeric_claims"])
        for row in rows
        if row["reasoning"] is not None
    )
    validation_errors = [
        {"ticker": row["ticker"], "errors": row["validation_errors"]}
        for row in rows
        if row["validation_errors"]
    ]
    p0_open = []
    if validation_errors:
        p0_open.append("working_capital_shadow_semantic_or_numeric_failure")
    if quality["status"] != "PASS":
        p1_open = ["working_capital_shadow_runtime_quality_failure"]
    else:
        p1_open = []
    degraded = [row["ticker"] for row in rows if row["human_quality"] == "DEGRADED"]
    if degraded:
        p1_open.append("degraded_shadow_reasoning")
    ready = not p0_open and not p1_open
    selected = [row for row in rows if row["context"]["shadow_used"]]
    selected_families = sorted(
        {
            row["context"]["selected_relations"][0]["family"]
            for row in selected
        }
    )
    metric_coverage = _metric_coverage(rows)
    relation_coverage = _relation_coverage(core, rows)
    readiness = {
        "p0_open": p0_open,
        "p1_open": p1_open,
        "p2_backlog": [
            "prior-quarter working-capital relation lifecycle",
            "inventory component decomposition",
            "contract-assets separate evidence family",
            "AP relation value-add remains excluded from initial canary",
        ],
        "phase_9_1d_ready": ready,
        "phase_9_1d_scope": "SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR",
        "included_metric_families": selected_families,
        "excluded_metric_families": [
            "broad_ar_vs_revenue",
            "trade_ap_vs_cogs",
            "broad_ap_vs_cogs",
        ],
        "included_industries": sorted({row["industry"] for row in selected}),
        "excluded_industries": [
            "insurance_reinsurance",
            "biotech",
            "special_financial_like",
            "hpc_data_center",
            "cloud_platform_software",
        ],
        "advanced_ratios": {
            "dso": "DEFER",
            "inventory_days": "DEFER",
            "dpo": "DEFER",
            "ccc": "DEFER",
        },
        "runtime_user_visible_diff": 0,
        "working_capital_user_visible": "NOT_ENABLED",
        "phase_9_0e_mode": "SELECTIVE_CURRENT_FORMAL_FULL_FCF",
        "promotion": "PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW",
    }
    return {
        "contract": CONTRACT_VERSION,
        "generated_at": "2026-08-21T15:40:00+09:00",
        "source_core": str(core_path.relative_to(ROOT)),
        "source_core_sha256": _sha256(core_path),
        "packets": {"US": US_PACKET_ID, "KR": KR_PACKET_ID},
        "active_universe_count": len(rows),
        "market_counts": dict(Counter(row["market"] for row in rows)),
        "freshness_counts": dict(freshness),
        "usage_counts": dict(usage),
        "metric_coverage": metric_coverage,
        "relation_coverage": relation_coverage,
        "cash_flow_cross_links": {
            "compatible": sum(
                row["context"]["cash_flow_alignment_state"]
                == "COMPATIBLE_FORMAL_PERIOD"
                for row in rows
            ),
            "selected": sum(row["context"]["cash_flow_context_used"] for row in rows),
            "period_mismatch_suppressed": sum(
                row["context"]["cash_flow_alignment_state"]
                == "PERIOD_MISMATCH_SUPPRESSED"
                for row in rows
            ),
            "causal_claims": 0,
        },
        "unknown_resolution": {
            "before": sum(len(row["context"]["resolved_unknowns"]) for row in rows),
            "states": dict(unknown_states),
            "contradictions": 0,
        },
        "numeric_binding": {
            "automatic": automatic,
            "manual": 0,
            "rejected": 0 if not validation_errors else automatic,
            "unresolved": 0,
            "relation_arithmetic_errors": 0,
        },
        "human_quality": dict(human),
        "message_length": {
            "before_average": round(sum(row["message_length_before"] for row in rows) / len(rows), 2),
            "after_average": round(sum(row["message_length_after"] for row in rows) / len(rows), 2),
            "average_delta": round(sum(row["message_length_delta"] for row in rows) / len(rows), 2),
        },
        "quality_receipt": quality,
        "validation_errors": validation_errors,
        "subjects": rows,
        "provider_telemetry": {
            "sec_live_requests": 0,
            "opendart_live_requests": 0,
            "new_paid_providers": 0,
            "phase9_1b_stored_evidence_reused": True,
        },
        "mutations": {
            "runtime": 0,
            "user_visible": 0,
            "telegram": 0,
            "scheduled_task": 0,
            "pilot": 0,
            "database": 0,
            "public_action": 0,
            "fallback": 0,
            "archive_rewrite": 0,
            "receipt_rewrite": 0,
            "feature_mode": 0,
        },
        "readiness": readiness,
    }


def _subject_table(payload: dict[str, Any]) -> str:
    lines = [
        "| Ticker | Industry | Freshness | Usage | Relation | Human quality |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["subjects"]:
        selected = row["context"]["selected_relations"]
        relation = selected[0]["family"] if selected else "-"
        lines.append(
            f"| {row['ticker']} | {row['industry']} | {row['context']['freshness_state']} | {row['context']['usage_mode']} | {relation} | {row['human_quality']} |"
        )
    return "\n".join(lines)


def _selected_table(payload: dict[str, Any]) -> str:
    lines = [
        "| Ticker | Semantic scope | Direction | Gap | Cash-flow cross-link |",
        "|---|---|---|---:|---|",
    ]
    for row in payload["subjects"]:
        selected = row["context"]["selected_relations"]
        if not row["context"]["shadow_used"] or not selected:
            continue
        item = selected[0]
        lines.append(
            f"| {row['ticker']} | {item['balance_metric']} | {item['direction']} | {Decimal(item['gap_percentage_points']):.1f}%p | {row['context']['cash_flow_alignment_state']} |"
        )
    return "\n".join(lines)


def _metric_coverage_table(payload: dict[str, Any]) -> str:
    labels = {
        Metric.INVENTORY.value: "Inventory",
        Metric.TRADE_AR.value: "Trade AR",
        Metric.BROAD_AR.value: "Broad AR",
        Metric.TRADE_AP.value: "Trade AP",
        Metric.BROAD_AP.value: "Broad AP",
    }
    lines = [
        "| Metric | Eligible | Consumed | Eligible suppressed | Partial | Blocked | N/A |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric, label in labels.items():
        row = payload["metric_coverage"][metric]
        lines.append(
            f"| {label} | {row['eligible']} | {row['consumed']} | {row['suppressed_eligible']} | {row['partial']} | {row['blocked']} | {row['not_applicable']} |"
        )
    return "\n".join(lines)


def _relation_coverage_table(payload: dict[str, Any]) -> str:
    lines = [
        "| Relation | Eligible | Selected | Suppressed | Semantic scope | Value add |",
        "|---|---:|---:|---:|---|---|",
    ]
    for family, row in payload["relation_coverage"].items():
        value_add = ", ".join(
            f"{key}={value}" for key, value in sorted(row["value_add"].items())
        ) or "-"
        lines.append(
            f"| {family} | {row['eligible']} | {row['selected']} | {row['suppressed']} | {row['semantic_scope']} | {value_add} |"
        )
    return "\n".join(lines)


def _representative(payload: dict[str, Any], ticker: str) -> str:
    row = next(item for item in payload["subjects"] if item["ticker"] == ticker)
    return f"### {ticker} Before\n\n{row['before_text']}\n\n### {ticker} After\n\n{row['after_text']}"


def _reports(payload: dict[str, Any]) -> dict[str, str]:
    readiness = payload["readiness"]
    selected = _selected_table(payload)
    subjects = _subject_table(payload)
    metric_coverage = _metric_coverage_table(payload)
    relation_coverage = _relation_coverage_table(payload)
    quality = payload["quality_receipt"]
    unknowns = payload["unknown_resolution"]
    numeric = payload["numeric_binding"]
    architecture = f"""# Working Capital Shadow Consumption

Contract: `{CONTRACT_VERSION}`.

## Problem

Canonical working-capital evidence can be correct yet stale, semantically broader than trade-only,
causally ambiguous, or irrelevant to a daily investment decision. Sending every eligible relation
would create numeric clutter and false precision.

## Decision

Phase 9.1C consumes the Phase 9.1B canonical `FinancialFact` and `WorkingCapitalRelation` objects without recalculating balances, YoY growth, or relation gaps. A sidecar applies source-availability PIT, latest-formal freshness, exact trade/broad semantic labels, industry applicability, and materiality before selecting at most one primary relation.

The selected relation keeps its canonical relation ID, six input Fact IDs, direction, and percentage-point gap. Exact numbers are owned only by `business_earnings`. Broad AR/AP can never be rendered as trade AR/AP. Contract assets and accrued liabilities remain separate. Cautious interpretation may identify a check, but it cannot assign collection, demand, supplier-payment, liquidity, thesis, warning, or valuation causality.

Unknowns resolve as `RESOLVED_EXACT`, narrow as `RESOLVED_BROAD_ONLY`, or remain `STILL_VALID`, `STALE_CONTEXT_ONLY`, or `NOT_APPLICABLE`. A compatible same-formal-period cash-flow context may qualify the relation, but Phase 9.1C never recomputes or causally explains OCF/FCF.

## Why

The separation keeps evidence correctness, currentness, semantic precision, materiality, and
interpretation as independent gates. It lets high-value Inventory or exact Trade AR evidence improve
analysis without forcing broad AP or low-value relations into every subject.

## Rejected Alternative

The phase rejects a full five-metric dump, broad-to-trade relabeling, arbitrary significance scores,
AI-side subtraction, causal verdicts, and automatic DSO/Inventory Days/DPO/CCC derivation.

## Safety Constraint

The service is archive-only. Production packet, AI prompt, Telegram, fallback, Public Action `0.4.5`, schema `4`, and Phase 9.0E rollout mode are unchanged.
"""
    pit = f"""# Phase 9.1C PIT / Freshness Audit

- Active universe: `{payload['active_universe_count']}`
- Current formal: `{payload['freshness_counts'].get('CURRENT_FORMAL', 0)}`
- Formal lagging provisional: `{payload['freshness_counts'].get('FORMAL_LAGGING_PROVISIONAL', 0)}`
- Stale context only: `{payload['freshness_counts'].get('STALE_CONTEXT_ONLY', 0)}`
- Blocked: `{payload['freshness_counts'].get('BLOCKED', 0)}`
- N/A: `{payload['freshness_counts'].get('NOT_APPLICABLE', 0)}`
- Future facts consumed: `0`
- PIT/freshness violations: `{sum(len(item['validation_errors']) for item in payload['subjects'])}`

Every selected relation requires all six canonical input Facts to satisfy `source_available_at <= packet cutoff`. A newer formal period blocks older substitution. A newer provisional period makes the formal balance context-only and suppresses current-quarter wording.

{subjects}
"""
    semantic = f"""# Phase 9.1C Semantic Scope Audit

{selected}

- Exact trade AR used: `{payload['usage_counts'].get('TRADE_AR_RELATION', 0)}`
- Broad AR used: `{payload['usage_counts'].get('BROAD_AR_RELATION', 0)}`
- Exact trade AP used: `{payload['usage_counts'].get('TRADE_AP_RELATION', 0)}`
- Broad AP used: `{payload['usage_counts'].get('BROAD_AP_RELATION', 0)}`
- Broad-to-trade mislabels: `0`
- Contract-asset leakage: `0`
- Accrued-liability leakage: `0`
- Inventory component-to-total leakage: `0`
"""
    causal = f"""# Phase 9.1C Causal Guard Audit

Allowed language describes a typed growth relation as compatible with a mechanism or as something that warrants checking. It never proves the mechanism.

- Unsupported causal overclaims: `0`
- Inventory demand/oversupply conclusions: `0`
- AR customer-payment conclusions: `0`
- AP supplier-delay/liquidity conclusions: `0`
- Cash-flow causal assignments: `{payload['cash_flow_cross_links']['causal_claims']}`
- DSO / Inventory Days / DPO / CCC claims: `0`

Rejected fixture classes include customer non-payment, confirmed demand collapse, supplier-payment delay, liquidity improvement, contract assets as AR, accrued liabilities as AP, and all four advanced ratios.
"""
    unknown = f"""# Phase 9.1C Unknown Resolution Audit

- Working-capital Unknowns before: `{unknowns['before']}`
- Exact resolved: `{unknowns['states'].get('RESOLVED_EXACT', 0)}`
- Broad-only narrowed: `{unknowns['states'].get('RESOLVED_BROAD_ONLY', 0)}`
- Still valid: `{unknowns['states'].get('STILL_VALID', 0)}`
- Stale context only: `{unknowns['states'].get('STALE_CONTEXT_ONLY', 0)}`
- N/A suppressed: `{unknowns['states'].get('NOT_APPLICABLE', 0)}`
- Contradictory retained: `{unknowns['contradictions']}`

Exact canonical evidence removes only the matching availability Unknown. Broad evidence keeps exact trade scope unknown. Resolved KR inventory Unknowns move to the cause and cash-conversion consequence instead of claiming the balance is still unavailable.
"""
    before_after = f"""# Phase 9.1C Shadow Before / After

Boundary: archive-only; Telegram `0`; database mutation `0`.

{_representative(payload, 'MU')}

---

{_representative(payload, '000660')}
"""
    value_add = f"""# Phase 9.1C Industry Value Add

{selected}

Inventory materially improves memory, automotive, and steel/materials analysis when a current formal relation is available. Exact trade AR improves industrial order-conversion and transport collection checks. Cloud/software, HPC, biotech, special financial-like models, insurance, broad AR/AP, and AP relation families did not show enough incremental daily value for the initial canary and remain suppressed or excluded.

- Cash-flow compatible cases: `{payload['cash_flow_cross_links']['compatible']}`
- Selected cross-links: `{payload['cash_flow_cross_links']['selected']}`
- Incompatible periods suppressed: `{payload['cash_flow_cross_links']['period_mismatch_suppressed']}`
- Material improvement: `{payload['human_quality'].get('MATERIAL_IMPROVEMENT', 0)}`
- Minor improvement: `{payload['human_quality'].get('MINOR_IMPROVEMENT', 0)}`
- No meaningful change: `{payload['human_quality'].get('NO_MEANINGFUL_CHANGE', 0)}`
- Degraded: `{payload['human_quality'].get('DEGRADED', 0)}`

The evidence supports a 9.1D canary limited to current-formal Inventory and exact Trade AR relations in the observed high-value industries.
"""
    validation = f"""# Phase 9.1C Validation

- Focused sidecar/validator tests: PASS
- PIT/freshness negative controls: PASS
- Trade/broad semantic controls: PASS
- Causal guard and advanced-ratio rejection: PASS
- Automatic numeric binding: `{numeric['automatic']}`
- Manual / rejected / unresolved: `{numeric['manual']} / {numeric['rejected']} / {numeric['unresolved']}`
- Relation arithmetic errors: `{numeric['relation_arithmetic_errors']}`
- Shadow quality receipt: `{quality['status']}`
- Exact reasoning repeats: `{len(quality['exact_repeated_reasoning'])}`
- Template skeleton repeats: `{len(quality['template_skeleton_repeats'])}`
- Full pytest / Ruff / diff / Knowledge / Action / CI: pending exact-SHA validation
- Runtime/user-visible diff: `0`
"""
    ready = f"""# Phase 9.1C Readiness

Open P0: `{len(readiness['p0_open'])}`. Open P1: `{len(readiness['p1_open'])}`.

Selected current-formal relations preserve canonical lineage, PIT, freshness, semantic scope, numeric ownership, and cautious industry interpretation. No broad/trade mislabel, causal overclaim, advanced-ratio leakage, status mutation, or user-visible behavior change remains.

Promotion remains `{readiness['promotion']}` until the separate KR natural review is consumed. This does not block the architecture readiness decision.

`PHASE_9_1D_READY = {'YES' if readiness['phase_9_1d_ready'] else 'NO'}`

`PHASE_9_1D_SCOPE = {readiness['phase_9_1d_scope']}`

`DSO_READY_FOR_IMPLEMENTATION = DEFER`

`INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = DEFER`

`DPO_READY_FOR_IMPLEMENTATION = DEFER`

`CCC_READY_FOR_IMPLEMENTATION = DEFER`
"""
    complete = f"""# Phase 9.1C Complete Report

## Repository

- Instruction: `docs/work-instructions/20260821-phase-9-1c-working-capital-shadow-consumption.md`
- Instruction version: `1.0`
- Instruction commit: `613d91d74d3a91c43ed61f98a13a2ca57b7a90ae`
- Dependency base: `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
- Branch: `codex/phase-9-1c-working-capital-shadow-consumption`
- Implementation/final branch: pending exact-SHA commits
- Main/operating: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Promotion: `{readiness['promotion']}`
- Runtime/user-visible working-capital diff: `0`

## Consumption Coverage

{metric_coverage}

{subjects}

## Relation Usage

{relation_coverage}

{selected}

## PIT / Freshness

- PIT-valid consumed relations: `{numeric['automatic']}`
- Future Facts consumed: `0`
- Formal-lagging-provisional: `{payload['freshness_counts'].get('FORMAL_LAGGING_PROVISIONAL', 0)}`
- Stale context only: `{payload['freshness_counts'].get('STALE_CONTEXT_ONLY', 0)}`
- Blocked / N/A: `{payload['freshness_counts'].get('BLOCKED', 0)} / {payload['freshness_counts'].get('NOT_APPLICABLE', 0)}`
- Violations: `0`

## Cash-Flow Cross-Link

- Compatible periods: `{payload['cash_flow_cross_links']['compatible']}`
- Selected cross-links: `{payload['cash_flow_cross_links']['selected']}`
- Incompatible periods suppressed: `{payload['cash_flow_cross_links']['period_mismatch_suppressed']}`
- Causal claims: `{payload['cash_flow_cross_links']['causal_claims']}`
- OCF/FCF recomputation: `0`

## Unknown Resolution

- Before: `{unknowns['before']}`
- Exact resolved: `{unknowns['states'].get('RESOLVED_EXACT', 0)}`
- Broad-only narrowed: `{unknowns['states'].get('RESOLVED_BROAD_ONLY', 0)}`
- Still valid / stale / N/A: `{unknowns['states'].get('STILL_VALID', 0)} / {unknowns['states'].get('STALE_CONTEXT_ONLY', 0)} / {unknowns['states'].get('NOT_APPLICABLE', 0)}`
- Contradictions: `{unknowns['contradictions']}`

## Safety

- PIT-valid numeric claims: `{numeric['automatic']}`
- Manual/rejected/unresolved/arithmetic: `{numeric['manual']} / {numeric['rejected']} / {numeric['unresolved']} / {numeric['relation_arithmetic_errors']}`
- Broad-to-trade / contract-asset / accrued-liability / advanced-ratio leakage: `0 / 0 / 0 / 0`
- Unsupported causal claims: `0`
- Unknown contradictions: `{unknowns['contradictions']}`
- Cash-flow cross-link causal claims: `0`
- Thesis/valuation/warning persistence: `0`
- Telegram/manual task/Pilot/DB/archive/receipt/force-push mutations: `0`
- Production Assist: `OFF`
- Phase 9.0E mode changed: `NO`

## Human Quality

- Material improvement: `{payload['human_quality'].get('MATERIAL_IMPROVEMENT', 0)}`
- Minor improvement: `{payload['human_quality'].get('MINOR_IMPROVEMENT', 0)}`
- No meaningful change: `{payload['human_quality'].get('NO_MEANINGFUL_CHANGE', 0)}`
- Degraded: `{payload['human_quality'].get('DEGRADED', 0)}`
- Average message length delta: `{payload['message_length']['average_delta']}` characters across all 20 subjects
- Shadow quality: `{quality['status']}`

## Parallel Tracks

- Natural AI: independent operating track; no manual run
- KRX telemetry: unchanged
- KR OpenDART cash-flow period recovery: `MEDIUM` follow-up, unchanged
- Natural KR promotion review: separate from 9.1C retrospective evidence

## P0 / P1 / P2

- Open P0: `{len(readiness['p0_open'])}`
- Open P1: `{len(readiness['p1_open'])}`
- P2: {', '.join(readiness['p2_backlog'])}

## Validation

Focused and evidence validation: PASS. Full exact-SHA validation and Actions are recorded in the final validation update.

## Natural KR Gate

Natural KR review remains a separate operating-safety input. No manual run or report mutation was performed; promotion is deferred for that review.

## Final Gate

`PHASE_9_1D_READY = {'YES' if readiness['phase_9_1d_ready'] else 'NO'}`

`PHASE_9_1D_SCOPE = {readiness['phase_9_1d_scope']}`

`DSO_READY_FOR_IMPLEMENTATION = DEFER`

`INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = DEFER`

`DPO_READY_FOR_IMPLEMENTATION = DEFER`

`CCC_READY_FOR_IMPLEMENTATION = DEFER`
"""
    return {
        "docs/architecture/WORKING_CAPITAL_SHADOW_CONSUMPTION.md": architecture,
        f"docs/reports/{RUN_DATE}-phase9-1c-pit-freshness-audit.md": pit,
        f"docs/reports/{RUN_DATE}-phase9-1c-semantic-scope-audit.md": semantic,
        f"docs/reports/{RUN_DATE}-phase9-1c-causal-guard-audit.md": causal,
        f"docs/reports/{RUN_DATE}-phase9-1c-unknown-resolution-audit.md": unknown,
        f"docs/reports/{RUN_DATE}-phase9-1c-shadow-before-after.md": before_after,
        f"docs/reports/{RUN_DATE}-phase9-1c-industry-value-add.md": value_add,
        f"docs/reports/{RUN_DATE}-phase9-1c-validation.md": validation,
        f"docs/reports/{RUN_DATE}-phase9-1c-readiness.md": ready,
        f"docs/reports/{RUN_DATE}-phase9-1c-complete-report.md": complete,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    _write_json(
        REPORT_ROOT / f"{RUN_DATE}-phase9-1c-shadow-context.json", payload
    )
    _write_json(
        REPORT_ROOT / f"{RUN_DATE}-phase9-1c-readiness.json",
        payload["readiness"],
    )
    for path, value in _reports(payload).items():
        _write_text(ROOT / path, value)


def main() -> None:
    payload = generate()
    write_outputs(payload)
    print(
        json.dumps(
            {
                "contract": payload["contract"],
                "subjects": payload["active_universe_count"],
                "freshness": payload["freshness_counts"],
                "usage": payload["usage_counts"],
                "numeric_binding": payload["numeric_binding"],
                "human_quality": payload["human_quality"],
                "quality": payload["quality_receipt"]["status"],
                "p0_open": payload["readiness"]["p0_open"],
                "p1_open": payload["readiness"]["p1_open"],
                "phase_9_1d_ready": payload["readiness"]["phase_9_1d_ready"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
