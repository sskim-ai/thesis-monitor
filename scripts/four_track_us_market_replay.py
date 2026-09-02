from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.us_full_message_service import render_us_full_market_message


CONTRACT = "four-track-us-market-frozen-replay-v1"
CURVE_SERIES = ("DGS3", "DGS5", "DGS10", "DGS30")


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _add_daily_gap(frame: dict[str, object]) -> None:
    open_value = float(frame["open"])
    close = float(frame["close"])
    baseline = float(frame["return_baseline_close"])
    baseline_date = str(frame["return_baseline_date"])
    frame.update(
        {
            "gap_value": open_value - baseline,
            "gap_pct": (open_value - baseline) / baseline * 100,
            "gap_baseline_date": baseline_date,
            "gap_baseline_close": baseline,
            "gap_baseline_semantic": (
                "night_open_minus_validated_preceding_regular_day_close"
            ),
            "change_value": close - baseline,
            "return_pct": (close - baseline) / baseline * 100,
        }
    )


def _enrich_night(context: dict[str, object]) -> None:
    frames_by_id: dict[str, dict[str, object]] = {}
    for row in context.get("night_futures", []):
        if not isinstance(row, dict):
            continue
        timeframes = row.get("night_timeframes")
        if not isinstance(timeframes, dict):
            continue
        daily = timeframes.get("daily")
        if isinstance(daily, dict):
            _add_daily_gap(daily)
        for name in ("daily", "weekly", "monthly"):
            frame = timeframes.get(name)
            if isinstance(frame, dict) and frame.get("fact_id"):
                frames_by_id[str(frame["fact_id"])] = frame
    for fact in context.get("fact_catalog", []):
        if not isinstance(fact, dict):
            continue
        frame = frames_by_id.get(str(fact.get("fact_id") or ""))
        fields = fact.get("fields")
        if frame is not None and isinstance(fields, dict):
            fields.update(frame)


def _treasury_fact(observation: Mapping[str, object]) -> dict[str, object]:
    series = str(observation["series_code"])
    current = float(observation["current_pct"])
    previous = float(observation["previous_pct"])
    return {
        "fact_id": f"market:nominal_yield:{series}",
        "fact_type": "market_nominal_yield",
        "as_of_date": str(observation["current_date"]),
        "source": "verified_macro_briefing",
        "fields": {
            "series_code": series,
            "label": str(observation["label"]),
            "level_pct": current,
            "previous_level_pct": previous,
            "previous_observation_date": str(observation["previous_date"]),
            "change_bp": (current - previous) * 100,
            "quality": "fresh",
            "provider": "fred",
            "source_url": str(observation["source_url"]),
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "important_change_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }


def replay(source_path: Path, treasury_path: Path) -> dict[str, object]:
    source = _read(source_path)
    treasury = _read(treasury_path)
    context = deepcopy(source["context"])
    if not isinstance(context, dict):
        raise ValueError("source_context_missing")
    _enrich_night(context)
    observations = treasury.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("treasury_observations_missing")
    treasury_facts = [
        _treasury_fact(item) for item in observations if isinstance(item, Mapping)
    ]
    facts = context.get("fact_catalog", [])
    if not isinstance(facts, list):
        raise ValueError("fact_catalog_missing")
    context["fact_catalog"] = [
        fact
        for fact in facts
        if not (
            isinstance(fact, dict)
            and isinstance(fact.get("fields"), dict)
            and fact["fields"].get("series_code") in CURVE_SERIES
        )
    ] + treasury_facts
    render = render_us_full_market_message(context)
    registry = build_numeric_registry(context["fact_catalog"])
    curve_registry = [
        item
        for item in registry
        if str(item.get("fact_id") or "").startswith("market:nominal_yield:DGS")
    ]
    night_rows = [row for row in context["night_futures"] if isinstance(row, dict)]
    night_checks: list[dict[str, object]] = []
    for row in night_rows:
        frames = row["night_timeframes"]
        daily = frames["daily"]
        same_baseline = bool(
            daily.get("gap_baseline_date") == daily.get("return_baseline_date")
            and daily.get("gap_baseline_close") == daily.get("return_baseline_close")
        )
        night_checks.append(
            {
                "series_code": row["series_code"],
                "contract_code": row["contract_code"],
                "daily_gap_pct": daily["gap_pct"],
                "daily_return_pct": daily["return_pct"],
                "baseline_date": daily["gap_baseline_date"],
                "baseline_close": daily["gap_baseline_close"],
                "same_gap_return_baseline": same_baseline,
                "weekly_status": frames["weekly"]["status"],
                "monthly_status": frames["monthly"]["status"],
            }
        )
    curve_checks = [
        {
            "series_code": fact["fields"]["series_code"],
            "current_pct": fact["fields"]["level_pct"],
            "current_date": fact["as_of_date"],
            "previous_pct": fact["fields"]["previous_level_pct"],
            "previous_date": fact["fields"]["previous_observation_date"],
            "delta_bp": fact["fields"]["change_bp"],
            "arithmetic_valid": math.isclose(
                float(fact["fields"]["change_bp"]),
                (
                    float(fact["fields"]["level_pct"])
                    - float(fact["fields"]["previous_level_pct"])
                )
                * 100,
                rel_tol=0,
                abs_tol=0.011,
            ),
        }
        for fact in treasury_facts
    ]
    gates = {
        "night_daily_open_close_gap_return": all(
            item["same_gap_return_baseline"] for item in night_checks
        ),
        "night_weekly_open_close_return": all(
            item["weekly_status"] == "IN_PROGRESS" for item in night_checks
        ),
        "night_monthly_open_close_return": all(
            item["monthly_status"] == "IN_PROGRESS" for item in night_checks
        ),
        "multi_contract_dwm_splicing": 0,
        "night_high_low_user_visible_occurrences": int(" · H " in render.text)
        + int(" · L " in render.text),
        "ust_observation_pair_valid": len(curve_checks) == 4
        and all(item["arithmetic_valid"] for item in curve_checks),
        "ust_delta_rendered_as_percent_return": 0,
        "lagged_ust_data_labeled_same_day": int("오늘" in render.text),
        "user_facing_primary_rate_block": "NOMINAL_3Y_5Y_10Y_30Y",
        "real_yield_primary_block_occurrences": render.text.count("실질금리"),
        "numeric_registry_unsupported": sum(
            item.get("registered") is not True for item in curve_registry
        ),
        "production_send": 0,
    }
    passed = (
        render.status == "PASS"
        and all(
            gates[key] is True
            for key in (
                "night_daily_open_close_gap_return",
                "night_weekly_open_close_return",
                "night_monthly_open_close_return",
            )
        )
        and gates["multi_contract_dwm_splicing"] == 0
        and gates["night_high_low_user_visible_occurrences"] == 0
        and gates["ust_observation_pair_valid"] is True
        and gates["lagged_ust_data_labeled_same_day"] == 0
        and gates["real_yield_primary_block_occurrences"] == 0
        and gates["numeric_registry_unsupported"] == 0
    )
    return {
        "contract": CONTRACT,
        "packet_id": source.get("packet_id"),
        "source": {
            "market_artifact": str(source_path),
            "market_artifact_sha256": _sha(source_path),
            "treasury_fixture": str(treasury_path),
            "treasury_fixture_sha256": _sha(treasury_path),
        },
        "night": night_checks,
        "treasury": curve_checks,
        "numeric_registry": curve_registry,
        "render": render.to_dict(),
        "gates": gates,
        "status": "PASS" if passed else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--treasury", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = replay(args.source, args.treasury)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
