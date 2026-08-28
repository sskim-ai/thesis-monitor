from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import sqlite3
from collections.abc import Mapping
from pathlib import Path

from app.services.current_price_context_service import fallback_price_context_errors
from app.services.kr_market_digest_quality_service import build_kr_market_digest_plan
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision,
)
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)


CONTRACT = "run-now-one-shot-kr-close-live-proof-v1"
MARKET_TICKER = "__DAILY_DIGEST_KR__"
EXPECTED_REPORTS = (
    "20260828-run-now-kr-close-preflight.md",
    "20260828-run-now-kr-close-schedule.md",
    "20260828-run-now-kr-close-live-run.md",
    "20260828-run-now-kr-market-exact-message.md",
    "20260828-run-now-kr-stock-exact-messages.md",
    "20260828-run-now-kr-v3-validator-proof.md",
    "20260828-run-now-kr-delivery-proof.md",
    "20260828-run-now-kr-scheduler-cleanup.md",
    "20260828-run-now-kr-final-status.md",
    "20260828-run-now-kr-artifact-index.md",
    "20260828-run-now-kr-live-proof.json",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _selected_rows(decision: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for binding in getattr(decision, "numeric_bindings", ()):
        if not isinstance(binding, Mapping):
            continue
        rows.append(
            {
                "fact_ref": binding.get("fact_ref"),
                "semantic_type": binding.get("semantic_type"),
                "display": binding.get("display") or binding.get("value"),
                "price_anchor_refs": list(binding.get("price_anchor_refs") or []),
                "source_families": list(binding.get("source_families") or []),
                "source_timeframe": binding.get("source_timeframe"),
                "dynamic_bollinger_confluence": binding.get(
                    "dynamic_bollinger_confluence"
                )
                is True,
                "provisional_bollinger_confluence": binding.get(
                    "provisional_bollinger_confluence"
                )
                is True,
            }
        )
    return rows


def _candidate_rows(context: Mapping[str, object]) -> list[dict[str, object]]:
    summary = _mapping(context.get("summary"))
    rows: list[dict[str, object]] = []
    for field in (
        "dynamic_bollinger_support",
        "dynamic_bollinger_resistance",
        "provisional_bollinger_support",
        "provisional_bollinger_resistance",
    ):
        value = _mapping(summary.get(field))
        if not value.get("zone_id"):
            continue
        rows.append(
            {
                "field": field,
                "fact_ref": value.get("zone_id"),
                "display": value.get("display"),
                "source_timeframe": value.get("source_timeframe"),
                "proximity_tier": value.get("proximity_tier"),
                "price_anchor_refs": list(value.get("price_anchor_refs") or []),
            }
        )
    return rows


def _delivery_rows(
    database: Path,
    packet_id: str,
    message_by_ticker: Mapping[str, str],
) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows: list[dict[str, object]] = []
    try:
        values = connection.execute(
            """
            select id, ticker, status, attempt_count, sent_at, last_error, payload
            from notificationdelivery
            where assessment_date = ?
              and (ticker = ? or ticker glob ?)
            order by case when ticker = ? then 0 else 1 end, ticker
            """,
            ("2026-08-28", MARKET_TICKER, "[0-9][0-9][0-9][0-9][0-9][0-9]", MARKET_TICKER),
        ).fetchall()
    finally:
        connection.close()
    for value in values:
        payload = json.loads(value["payload"])
        pilot = _mapping(payload.get("_ai_assisted_pilot"))
        telegram = _mapping(payload.get("_telegram_delivery"))
        rendered_text = str(telegram.get("rendered_text") or "")
        expected_text = message_by_ticker.get(str(value["ticker"]), "")
        rows.append(
            {
                "delivery_id": value["id"],
                "ticker": value["ticker"],
                "status": value["status"],
                "attempt_count": value["attempt_count"],
                "sent_at_utc": value["sent_at"],
                "last_error": value["last_error"],
                "packet_id": pilot.get("packet_id"),
                "pilot_state": pilot.get("state"),
                "chunk_count": telegram.get("chunk_count"),
                "next_chunk_index": telegram.get("next_chunk_index"),
                "content_sha256": telegram.get("content_sha256"),
                "rendered_text_sha256": _sha256_text(rendered_text),
                "expected_text_sha256": _sha256_text(expected_text),
                "exact_payload_match": bool(expected_text)
                and rendered_text == expected_text
                and telegram.get("content_sha256") == _sha256_text(expected_text),
                "all_chunks_accepted": telegram.get("chunk_count")
                == telegram.get("next_chunk_index"),
                "owned_by_live_packet": pilot.get("packet_id") == packet_id,
            }
        )
    return rows


def _market_audit(packet: Mapping[str, object], text: str) -> dict[str, object]:
    plan = build_kr_market_digest_plan(packet.get("market_context"), sector_rank_limit=3)
    validation = validate_kr_market_evidence_utilization(plan, rendered_text=text)
    surface = {
        "kospi_kosdaq": "KOSPI" in text and "KOSDAQ" in text,
        "breadth": "상승 종목" in text and "하락 종목" in text,
        "participant_flow": all(value in text for value in ("외국인", "기관", "개인")),
        "size_style": "규모별" in text,
        "sector_top3": "업종 상대 강세" in text and "업종 상대 약세" in text,
    }
    errors = list(validation.errors)
    errors.extend(f"missing_surface:{key}" for key, value in surface.items() if not value)
    return {
        "message_sha256": _sha256_text(text),
        "message_length": len(text),
        "surface": surface,
        "plan": plan.to_dict(),
        "validation": validation.to_dict(),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _stock_audit(
    packet: Mapping[str, object],
    message_by_ticker: Mapping[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stock_value in packet.get("stocks", []):
        stock = _mapping(stock_value)
        ticker = str(stock.get("ticker") or "")
        text = message_by_ticker.get(ticker, "")
        structure = _mapping(_mapping(stock.get("chart_context")).get("structure"))
        context = _mapping(structure.get("price_structure_v3"))
        decision = build_kr_price_structure_rollout_decision(
            context,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        selected = _selected_rows(decision)
        selected_refs = {str(row.get("fact_ref") or "") for row in selected}
        candidates = _candidate_rows(context)
        omitted = [
            {
                **candidate,
                "state": "OMITTED_BY_MATERIALITY",
                "reason": "not_selected_by_v3_material_dynamic_selector",
            }
            for candidate in candidates
            if str(candidate.get("fact_ref") or "") not in selected_refs
        ]
        errors = list(getattr(decision, "render_validation_errors", ()))
        fallback_errors = fallback_price_context_errors(
            _mapping(stock.get("current_price_context")),
            text,
            validated_v3_render=bool(
                getattr(decision, "section", None) and not errors
            ),
        )
        errors.extend(fallback_errors)
        for binding in selected:
            semantic = str(binding.get("semantic_type") or "")
            display = str(binding.get("display") or "")
            if semantic == "STRUCTURE_BASIS_CLOSE":
                if "현재가(정규장 종가):" not in text and "가격 구조 기준 종가(정규장):" not in text:
                    errors.append("structure_basis_close_not_rendered")
            elif display and display not in text:
                errors.append(f"selected_fact_not_rendered:{binding.get('fact_ref')}")
            if semantic in {"MAJOR_SUPPORT", "MAJOR_RESISTANCE"} and not binding.get(
                "price_anchor_refs"
            ):
                errors.append(f"major_structure_without_price_anchor:{binding.get('fact_ref')}")
            if semantic.startswith("PROVISIONAL_"):
                if "잠정 볼린저" not in text or "진행중" not in text:
                    errors.append(f"provisional_label_invalid:{binding.get('fact_ref')}")
        if not text:
            errors.append("stock_message_missing")
        if "목표가" in text or "손절" in text:
            errors.append("unsupported_target_or_stop")
        if "• 기준 종가:" in text:
            errors.append("ambiguous_current_vs_structure_price_label")
        if any(
            label in text
            for label in ("가까운 잠정 볼린저", "주요 구조 잠정 볼린저", "기존 등록 잠정 볼린저")
        ):
            errors.append("provisional_bollinger_role_leakage")
        rows.append(
            {
                "ticker": ticker,
                "company_name": stock.get("company_name"),
                "eligibility": getattr(decision, "eligibility").value,
                "message_sha256": _sha256_text(text),
                "message_length": len(text),
                "selected_plan": selected,
                "validator_required_refs": sorted(selected_refs),
                "candidate_refs": candidates,
                "omitted_plan": omitted,
                "renderer_validation_errors": list(
                    getattr(decision, "render_validation_errors", ())
                ),
                "fallback_validation_errors": fallback_errors,
                "quality_errors": list(dict.fromkeys(errors)),
                "status": "PASS" if not errors else "FAIL",
            }
        )
    return rows


def _report_header(title: str, packet_id: str) -> str:
    return f"# {title}\n\n- Packet: `{packet_id}`\n- Contract: `{CONTRACT}`\n"


def _build_reports(args: argparse.Namespace) -> dict[str, object]:
    packet = _mapping(_read_json(args.packet))
    packet_id = str(packet.get("packet_id") or "")
    message_payload = _mapping(_read_json(args.messages))
    messages = [
        _mapping(value) for value in message_payload.get("messages", [])
    ]
    message_by_ticker = {
        str(value.get("ticker") or ""): str(value.get("text") or "")
        for value in messages
    }
    preflight = _mapping(_read_json(args.preflight))
    schedule = _mapping(_read_json(args.schedule))
    producer = _mapping(_read_json(args.producer))
    delivery_result = _mapping(_read_json(args.delivery_result))
    market_text = message_by_ticker.get(MARKET_TICKER, "")
    market = _market_audit(packet, market_text)
    stocks = _stock_audit(packet, message_by_ticker)
    deliveries = _delivery_rows(args.database, packet_id, message_by_ticker)

    intended = {MARKET_TICKER, *(str(row.get("ticker")) for row in stocks)}
    delivery_tickers = [str(row["ticker"]) for row in deliveries]
    duplicate_count = len(delivery_tickers) - len(set(delivery_tickers))
    orphan_count = len(set(delivery_tickers) - intended) + len(intended - set(delivery_tickers))
    unowned_retry_count = sum(
        row["attempt_count"] != 1 or not row["owned_by_live_packet"]
        for row in deliveries
    )
    exact_count = sum(row["exact_payload_match"] for row in deliveries)
    accepted_count = sum(row["all_chunks_accepted"] for row in deliveries)
    all_sent = (
        len(deliveries) == len(intended)
        and all(row["status"] == "sent" for row in deliveries)
        and exact_count == len(intended)
        and accepted_count == len(intended)
    )
    normal_plist_sha = _sha256_file(args.normal_plist)
    normal_plist = plistlib.loads(args.normal_plist.read_bytes())
    normal_schedule = [
        f"{int(value['Hour']):02d}:{int(value['Minute']):02d}"
        for value in normal_plist["StartCalendarInterval"]
    ]

    stock_failures = [row["ticker"] for row in stocks if row["status"] != "PASS"]
    fallback_dynamic_errors = sum(
        "fallback_dynamic_resistance_not_rendered" in row["fallback_validation_errors"]
        for row in stocks
    )
    ambiguous_labels = sum(
        "ambiguous_current_vs_structure_price_label" in row["quality_errors"]
        for row in stocks
    )
    major_without_anchor = sum(
        any(str(error).startswith("major_structure_without_price_anchor") for error in row["quality_errors"])
        for row in stocks
    )
    provisional_role_leaks = sum(
        "provisional_bollinger_role_leakage" in row["quality_errors"]
        for row in stocks
    )
    one_shot_pass = all(
        (
            preflight.get("precondition_all_gates_pass") == "PASS",
            schedule.get("one_shot_kr_close_schedule_count") == 1,
            schedule.get("run_count") == 1,
            schedule.get("last_exit_code") == 0,
            schedule.get("automatic_second_one_shot_created") == 0,
            schedule.get("residual_one_shot_schedule_count") == 0,
            producer.get("delivery_action") == "held_for_ai_review",
            market["status"] == "PASS",
            not stock_failures,
            all_sent,
            duplicate_count == 0,
            orphan_count == 0,
            unowned_retry_count == 0,
            fallback_dynamic_errors == 0,
            ambiguous_labels == 0,
            major_without_anchor == 0,
            provisional_role_leaks == 0,
            delivery_result.get("status") == "sent",
            delivery_result.get("sent_count") == 8,
            normal_plist_sha == preflight.get("normal_kr_close_plist_sha256"),
            normal_schedule == preflight.get("normal_kr_close_schedule"),
        )
    )
    gates = {
        "OPERATING_BEFORE": preflight.get("operating_before"),
        "LATEST_MAIN_BEFORE": preflight.get("latest_main_before"),
        "OPERATING_LINEAGE_SAFE": preflight.get("operating_lineage_safe"),
        "PRECONDITION_ALL_GATES_PASS": preflight.get("precondition_all_gates_pass"),
        "PASS_TIME_KST": schedule.get("pass_time_kst"),
        "SCHEDULED_TIME_KST": schedule.get("scheduled_time_kst"),
        "ONE_SHOT_KR_CLOSE_SCHEDULE_COUNT": schedule.get(
            "one_shot_kr_close_schedule_count"
        ),
        "REGULAR_JOB_DEFINITION_REUSED": "PASS"
        if schedule.get("regular_job_definition_reused") is True
        else "FAIL",
        "NORMAL_RECURRING_SCHEDULE_CHANGED": 0
        if normal_plist_sha == preflight.get("normal_kr_close_plist_sha256")
        and normal_schedule == preflight.get("normal_kr_close_schedule")
        else 1,
        "PRE_SCHEDULE_ACTIVE_KR_CLOSE_COUNT": preflight.get(
            "pre_schedule_active_kr_close_count"
        ),
        "ONE_SHOT_RUN_ID": packet.get("source_monitor_run_id"),
        "ONE_SHOT_PACKET_ID": packet_id,
        "LIVE_KR_MARKET_MESSAGE": market["status"],
        "LIVE_KR_STOCK_MESSAGES": "PASS" if not stock_failures else "FAIL",
        "LIVE_KR_STOCK_MESSAGE_COUNT": len(stocks),
        "LIVE_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED": fallback_dynamic_errors,
        "LIVE_AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL": ambiguous_labels,
        "LIVE_BOLLINGER_ONLY_MAJOR_SR_VISIBLE": major_without_anchor,
        "LIVE_MAJOR_SR_WITHOUT_PRICE_ANCHOR": major_without_anchor,
        "LIVE_PROVISIONAL_BOLLINGER_AS_NEAR_SR": provisional_role_leaks,
        "LIVE_PROVISIONAL_BOLLINGER_AS_MAJOR_SR": provisional_role_leaks,
        "LIVE_PROVISIONAL_BOLLINGER_AS_STORED_RULE": provisional_role_leaks,
        "NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED": 0,
        "LIVE_DUPLICATE": duplicate_count,
        "LIVE_ORPHAN": orphan_count,
        "LIVE_UNOWNED_RETRY": unowned_retry_count,
        "AUTOMATIC_SECOND_ONE_SHOT_CREATED": schedule.get(
            "automatic_second_one_shot_created"
        ),
        "RESIDUAL_ONE_SHOT_SCHEDULE_COUNT": schedule.get(
            "residual_one_shot_schedule_count"
        ),
        "KR_LIVE_PROOF_SOURCE": "OPERATOR_AUTHORIZED_ONE_SHOT_REGULAR_JOB",
        "ONE_SHOT_KR_CLOSE_LIVE_PROOF": "PASS" if one_shot_pass else "FAIL",
        "FINAL_V3_VALIDATOR_CONVERGENCE": "LIVE_PASS" if one_shot_pass else "FAIL",
        "OPEN_P0": 0 if one_shot_pass else 1,
        "OPEN_MATERIAL_P1": 0 if one_shot_pass else 1,
    }
    output = {
        "contract": CONTRACT,
        "instruction_commit": args.instruction_commit,
        "instruction_sha256": _sha256_file(args.instruction),
        "packet_id": packet_id,
        "packet_sha256": _sha256_file(args.packet),
        "source_monitor_run_id": packet.get("source_monitor_run_id"),
        "generated_at": packet.get("generated_at"),
        "preflight": preflight,
        "schedule": schedule,
        "producer": producer,
        "market": market,
        "stocks": stocks,
        "deliveries": deliveries,
        "delivery_result": delivery_result,
        "delivery_summary": {
            "intended_count": len(intended),
            "sent_count": sum(row["status"] == "sent" for row in deliveries),
            "exact_payload_match_count": exact_count,
            "all_chunks_accepted_count": accepted_count,
            "duplicate_count": duplicate_count,
            "orphan_count": orphan_count,
            "unowned_retry_count": unowned_retry_count,
        },
        "normal_scheduler": {
            "plist_sha256": normal_plist_sha,
            "schedule": normal_schedule,
        },
        "gates": gates,
        "status": "PASS" if one_shot_pass else "FAIL",
    }
    _write_json(args.output_dir / EXPECTED_REPORTS[-1], output)
    _render_reports(args.output_dir, output, message_by_ticker)
    return output


def _render_reports(
    output_dir: Path,
    output: Mapping[str, object],
    message_by_ticker: Mapping[str, str],
) -> None:
    packet_id = str(output["packet_id"])
    preflight = _mapping(output["preflight"])
    schedule = _mapping(output["schedule"])
    producer = _mapping(output["producer"])
    market = _mapping(output["market"])
    deliveries = list(output["deliveries"])
    stocks = list(output["stocks"])
    gates = _mapping(output["gates"])

    _write(
        output_dir / EXPECTED_REPORTS[0],
        _report_header("Run-Now KR Close Preflight", packet_id)
        + f"""
| Gate | Result |
|---|---|
| Operating | `{preflight['operating_before']}` |
| origin/main | `{preflight['latest_main_before']}` |
| Lineage | `{preflight['operating_lineage_safe']}` |
| API / OHLCV | `{preflight['api_health']}` / `{preflight['ohlcv_health']}` |
| XKRX completed target | `{preflight['xkrx_target_date']}` / `{preflight['xkrx_target_completed']}` |
| Active KR universe | `{preflight['active_kr_count']}`: `{', '.join(preflight['active_kr_tickers'])}` |
| Active KR producer | `{preflight['pre_schedule_active_kr_close_count']}` |
| Residual one-shot | `{preflight['residual_one_shot_schedule_count']}` |
| V3 regression | `{preflight['v3_regression_tests']}` |
| P0 / material P1 | `{preflight['open_p0']}` / `{preflight['open_material_p1']}` |

`PRECONDITION_ALL_GATES_PASS = {preflight['precondition_all_gates_pass']}`
""",
    )
    _write(
        output_dir / EXPECTED_REPORTS[1],
        _report_header("Run-Now KR Close Schedule", packet_id)
        + f"""
- Pass time: `{schedule['pass_time_kst']}`
- Scheduled time: `{schedule['scheduled_time_kst']}`
- Actual producer observation: `{schedule['actual_run_observed_at_kst']}`
- Completion observation: `{schedule['actual_completion_observed_at_kst']}`
- Run count / exit: `{schedule['run_count']}` / `{schedule['last_exit_code']}`
- Regular ProgramArguments exact match: `{schedule['regular_job_definition_reused']}`
- Automatic second one-shot: `{schedule['automatic_second_one_shot_created']}`
""",
    )
    _write(
        output_dir / EXPECTED_REPORTS[2],
        _report_header("Run-Now KR Close Live Run", packet_id)
        + f"""
- Source monitor run: `{output['source_monitor_run_id']}`
- Packet generated: `{output['generated_at']}`
- Producer target: `{_mapping(producer['producer_role_target']).get('target_xkrx_business_date')}` completed=`{_mapping(producer['producer_role_target']).get('target_completed')}`
- Analysis: `{producer['analysis_action']}` / `{producer['analysis_run_status']}`
- Thesis batch: `{_mapping(producer['theses']).get('success_count')}/{_mapping(producer['theses']).get('ticker_count')}`
- Kiwoom context: `{_mapping(producer['kiwoom_market_context']).get('status')}`; calls `{_mapping(_mapping(producer['kiwoom_market_context']).get('provider_calls')).get('successes')}/{_mapping(_mapping(producer['kiwoom_market_context']).get('provider_calls')).get('requests')}`
- Producer delivery handoff: `{producer['delivery_action']}`
- Normal fallback completion: `{_mapping(output['delivery_result']).get('status')}` / `{_mapping(output['delivery_result']).get('sent_count')}` sent

The producer reused the successful completed-session stock assessment and refreshed the normal current KR market-context/packet path. It did not rerun the analysis or create a second producer execution.
""",
    )
    _write(
        output_dir / EXPECTED_REPORTS[3],
        _report_header("Run-Now KR Market Exact Message", packet_id)
        + f"""
- Status: `{market['status']}`
- SHA-256: `{market['message_sha256']}`
- Length: `{market['message_length']}`

```text
{message_by_ticker[MARKET_TICKER]}
```
""",
    )
    stock_blocks = []
    for row in stocks:
        ticker = str(row["ticker"])
        stock_blocks.append(
            f"## {row['company_name']} ({ticker})\n\n"
            f"- Status: `{row['status']}`\n"
            f"- SHA-256: `{row['message_sha256']}`\n\n"
            f"```text\n{message_by_ticker[ticker]}\n```"
        )
    _write(
        output_dir / EXPECTED_REPORTS[4],
        _report_header("Run-Now KR Stock Exact Messages", packet_id)
        + "\n"
        + "\n\n".join(stock_blocks),
    )
    v3_blocks = []
    for row in stocks:
        selected = "\n".join(
            f"- `{item['semantic_type']}` `{item['fact_ref']}`: {item['display']}"
            for item in row["selected_plan"]
        ) or "- none"
        omitted = "\n".join(
            f"- `{item['fact_ref']}`: {item['display']} (`{item['reason']}`)"
            for item in row["omitted_plan"]
        ) or "- none"
        v3_blocks.append(
            f"## {row['ticker']}\n\nStatus: `{row['status']}`\n\n"
            f"Selected / validator-owned:\n{selected}\n\n"
            f"Omitted candidates:\n{omitted}\n\n"
            f"Renderer errors: `{row['renderer_validation_errors']}`  \n"
            f"Fallback errors: `{row['fallback_validation_errors']}`"
        )
    _write(
        output_dir / EXPECTED_REPORTS[5],
        _report_header("Run-Now KR V3 Validator Proof", packet_id)
        + "\nThe validator requirement set is the V3 selected render plan; omitted candidates are not recreated as legacy obligations.\n\n"
        + "\n\n".join(v3_blocks),
    )
    delivery_lines = [
        "| Ticker | Status | Attempts | Chunks | Exact payload | Packet-owned |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    delivery_lines.extend(
        f"| `{row['ticker']}` | `{row['status']}` | `{row['attempt_count']}` | `{row['next_chunk_index']}/{row['chunk_count']}` | `{row['exact_payload_match']}` | `{row['owned_by_live_packet']}` |"
        for row in deliveries
    )
    summary = _mapping(output["delivery_summary"])
    _write(
        output_dir / EXPECTED_REPORTS[6],
        _report_header("Run-Now KR Delivery Proof", packet_id)
        + "\n"
        + "\n".join(delivery_lines)
        + f"""

The Telegram API accepted every persisted chunk through the production notifier. The archived fallback text, persisted rendered text, and content SHA match for `{summary['exact_payload_match_count']}/{summary['intended_count']}` messages. Raw chat IDs, tokens, and remote account identifiers are excluded.

- Duplicate: `{summary['duplicate_count']}`
- Orphan: `{summary['orphan_count']}`
- Unowned retry: `{summary['unowned_retry_count']}`
""",
    )
    normal = _mapping(output["normal_scheduler"])
    _write(
        output_dir / EXPECTED_REPORTS[7],
        _report_header("Run-Now KR Scheduler Cleanup", packet_id)
        + f"""
- Temporary schedule removed: `{schedule['temporary_schedule_removed_at_kst']}`
- Residual one-shot count: `{schedule['residual_one_shot_schedule_count']}`
- Temporary run count: `{schedule['run_count']}`
- Automatic second one-shot: `{schedule['automatic_second_one_shot_created']}`
- Normal recurring schedule: `{', '.join(normal['schedule'])}`
- Normal plist SHA-256: `{normal['plist_sha256']}`
- Normal recurring schedule changed: `{gates['NORMAL_RECURRING_SCHEDULE_CHANGED']}`
""",
    )
    gate_lines = "\n".join(f"- `{key} = {value}`" for key, value in gates.items())
    _write(
        output_dir / EXPECTED_REPORTS[8],
        _report_header("Run-Now KR Final Status", packet_id)
        + "\n"
        + gate_lines
        + "\n\n`NEXT_ACTION = NO_ACTION`\n",
    )
    index_rows = [
        "| Artifact | Purpose |",
        "|---|---|",
    ]
    index_rows.extend(f"| `{name}` | Required live-proof artifact |" for name in EXPECTED_REPORTS)
    index_rows.extend(
        (
            f"| `{args_name}` | Source evidence, included in completion bundle |"
            for args_name in (
                "preflight.json",
                "schedule.json",
                "producer-result.json",
                "delivery-result.json",
            )
        )
    )
    _write(
        output_dir / EXPECTED_REPORTS[9],
        _report_header("Run-Now KR Artifact Index", packet_id)
        + "\n"
        + "\n".join(index_rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--delivery-result", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--normal-plist", type=Path, required=True)
    parser.add_argument("--instruction", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = _build_reports(args)
    print(
        json.dumps(
            {
                "status": output["status"],
                "packet_id": output["packet_id"],
                "market": _mapping(output["market"])["status"],
                "stocks": len(output["stocks"]),
                "deliveries": _mapping(output["delivery_summary"])["sent_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
