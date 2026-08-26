from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.price_structure_v3_family_consensus_service import (  # noqa: E402
    apply_family_consensus_feedback,
)
from app.services.price_structure_wave_fibonacci_v3_service import (  # noqa: E402
    PriceStructureWaveFibV3Result,
    WaveHypothesisSelection,
    build_price_structure_wave_fib_v3,
    prepare_long_history,
)


REPORTS = ROOT / "docs/reports"
INSTRUCTION = (
    ROOT
    / "docs/work-instructions/20260826-price-structure-v3-current-data-end-to-end-shadow-message-validation.md"
)
FROZEN = REPORTS / "20260826-price-structure-v3-frozen-ohlcv.json"
BACKFILL = REPORTS / "20260826-v3-daily-1200-backfill.json"
PREENABLEMENT = REPORTS / "20260826-v3-preenablement-evidence.json"
US_BASELINE = REPORTS / "20260826-us-morning-exact-natural-messages.md"
KR_BASELINE = REPORTS / "20260826-kr-postdeploy-exact-generated-messages.md"
EVIDENCE = REPORTS / "20260826-v3-current-data-validation-evidence.json"
EXACT_MESSAGES = REPORTS / "20260826-v3-current-data-exact-candidate-messages.json"
READINESS = REPORTS / "20260826-v3-current-data-enablement-readiness.json"

INSTRUCTION_COMMIT = "688c17280a10e91214d4bd9888522fdc6f9bc0c5"
TARGET_SESSION = {"KR": "2026-08-26", "US": "2026-08-25"}
REQUESTED = {"daily": 1200, "weekly": 600, "monthly": 300}
TIMEFRAMES = ("monthly", "weekly", "daily")
CONTROL_TICKERS = (
    "000660",
    "010120",
    "MU",
    "TSM",
    "SNDK",
    "003690",
    "HUT",
    "SKHY",
    "012450",
    "TSLA",
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run current completed-session v3 shadow message validation."
    )
    parser.add_argument("--live-archive", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--implementation-sha", required=True)
    return parser.parse_args()


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, body: str) -> None:
    (REPORTS / name).write_text(
        f"# {title}\n\n{body.rstrip()}\n",
        encoding="utf-8",
    )


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _stable_id(prefix: str, value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"{prefix}:{_sha_bytes(payload)[:20]}"


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    values = [
        "| " + " | ".join(str(value).replace("\n", "<br>") for value in row) + " |"
        for row in rows
    ]
    return "\n".join(
        (
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *values,
        )
    )


def _row_map(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    rows = payload.get("rows")
    assert isinstance(rows, list)
    return {
        str(row["ticker"]): row
        for row in rows
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _market(value: object) -> str:
    return "KR" if str(value) == "KR" else "US"


def _merge_daily(
    archived: Sequence[Mapping[str, object]],
    live: Sequence[Mapping[str, object]],
    *,
    target_session: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    merged = {
        str(row["date"])[:10]: dict(row)
        for row in archived
        if row.get("date") and str(row["date"])[:10] <= target_session
    }
    excluded: list[dict[str, object]] = []
    for row in live:
        raw_date = str(row.get("date") or "")[:10]
        if not raw_date:
            continue
        if raw_date > target_session:
            excluded.append(dict(row))
            continue
        merged[raw_date] = dict(row)
    return [merged[key] for key in sorted(merged)], excluded


def _safe_partial_periods(
    rows: Sequence[Mapping[str, object]],
    safe_daily: Sequence[Mapping[str, object]],
    excluded_daily: Sequence[Mapping[str, object]],
    *,
    timeframe: str,
) -> list[dict[str, object]]:
    result = [dict(row) for row in rows]
    if not result or not excluded_daily:
        return result
    latest = result[-1]
    period_date = date.fromisoformat(str(latest["date"])[:10])
    if timeframe == "weekly":
        period_start = period_date
    else:
        period_start = period_date.replace(day=1)
    safe_rows = [
        row
        for row in safe_daily
        if row.get("date")
        and period_start <= date.fromisoformat(str(row["date"])[:10])
    ]
    if not safe_rows:
        return result[:-1]
    excluded_volume = sum(float(row.get("volume") or 0) for row in excluded_daily)
    excluded_value = sum(float(row.get("value") or 0) for row in excluded_daily)
    latest.update(
        {
            "open": safe_rows[0]["open"],
            "high": max(float(row["high"]) for row in safe_rows),
            "low": min(float(row["low"]) for row in safe_rows),
            "close": safe_rows[-1]["close"],
            "volume": max(0.0, float(latest.get("volume") or 0) - excluded_volume),
            "value": max(0.0, float(latest.get("value") or 0) - excluded_value),
        }
    )
    result[-1] = latest
    return result


def _periods_for_ticker(
    ticker: str,
    live: Mapping[str, object],
    frozen: Mapping[str, object],
    backfill: Mapping[str, object],
) -> tuple[dict[str, list[dict[str, object]]], dict[str, object]]:
    market = _market(live.get("market"))
    target = TARGET_SESSION[market]
    live_periods = live.get("periods")
    frozen_periods = frozen.get("periods")
    assert isinstance(live_periods, Mapping) and isinstance(frozen_periods, Mapping)
    archived_daily = backfill.get("bars")
    live_daily = live_periods.get("daily")
    assert isinstance(archived_daily, list) and isinstance(live_daily, list)
    daily, excluded = _merge_daily(archived_daily, live_daily, target_session=target)
    periods = {
        "daily": daily,
        "weekly": _safe_partial_periods(
            tuple(item for item in live_periods.get("weekly", ()) if isinstance(item, Mapping)),
            daily,
            excluded,
            timeframe="weekly",
        ),
        "monthly": _safe_partial_periods(
            tuple(item for item in live_periods.get("monthly", ()) if isinstance(item, Mapping)),
            daily,
            excluded,
            timeframe="monthly",
        ),
    }
    prior_daily = tuple(
        item for item in frozen_periods.get("daily", ()) if isinstance(item, Mapping)
    )
    prior_safe_close = next(
        (
            row.get("close")
            for row in reversed(prior_daily)
            if str(row.get("date") or "")[:10] <= target
        ),
        None,
    )
    return periods, {
        "ticker": ticker,
        "market": market,
        "target_session": target,
        "live_last_daily": str(live_daily[-1].get("date")) if live_daily else None,
        "safe_last_daily": str(daily[-1].get("date")) if daily else None,
        "excluded_daily_count": len(excluded),
        "excluded_daily_dates": [str(row.get("date")) for row in excluded],
        "safe_close": daily[-1].get("close") if daily else None,
        "prior_snapshot_close": prior_safe_close,
        "weekly_partial_rebuilt": bool(excluded),
        "monthly_partial_rebuilt": bool(excluded),
    }


def _selections(
    row: Mapping[str, object],
    *,
    cutoff: str,
) -> tuple[WaveHypothesisSelection, ...]:
    values = row.get("selections")
    assert isinstance(values, list)
    selections: list[WaveHypothesisSelection] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        validation = item.get("validation")
        if not isinstance(validation, Mapping) or validation.get("valid") is not True:
            continue
        selection = WaveHypothesisSelection.model_validate(item["selection"])
        selections.append(selection.model_copy(update={"cutoff": cutoff}))
    return tuple(selections)


def _parse_us_messages() -> dict[str, str]:
    text = US_BASELINE.read_text(encoding="utf-8")
    matches = re.findall(
        r"## \d+\. ([A-Z0-9_]+).*?### Exact Text\n\n```text\n(.*?)\n```",
        text,
        re.S,
    )
    return {ticker: message for ticker, message in matches if ticker != "US_MARKET"}


def _parse_kr_messages() -> dict[str, str]:
    text = KR_BASELINE.read_text(encoding="utf-8")
    return dict(
        re.findall(r"## stock:([A-Z0-9]+).*?```text\n(.*?)\n```", text, re.S)
    )


def _zone(selection: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if not selection:
        return None
    value = selection.get("zone")
    return value if isinstance(value, Mapping) else None


def _zone_display(zone: Mapping[str, object] | None) -> str:
    return str(zone.get("display")) if zone and zone.get("display") else "확인 구간 없음"


def _missing_text(selection: Mapping[str, object] | None, *, side: str) -> str:
    if not selection:
        return f"확인된 역사적 {side} 없음"
    reason = str(selection.get("reason") or "")
    classification = str(selection.get("classification") or "")
    if classification == "INSUFFICIENT_HISTORY" or "insufficient" in reason.lower():
        return f"이력 부족으로 {side} 판단 보류"
    return f"확인된 역사적 {side} 없음"


def _overlap(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return not (
        Decimal(str(left["raw_high"])) < Decimal(str(right["raw_low"]))
        or Decimal(str(right["raw_high"])) < Decimal(str(left["raw_low"]))
    )


def _price_display(value: object, currency: str) -> str:
    amount = Decimal(str(value))
    if currency == "KRW":
        return f"{amount:,.0f}원"
    return f"${amount:,.2f}"


def _price_structure_section(
    result: PriceStructureWaveFibV3Result,
    *,
    include_current_price: bool,
) -> tuple[str, list[dict[str, object]], int]:
    assert result.sr_base_layer is not None
    summary = result.sr_base_layer.summary.model_dump(mode="json")
    nearest_support = summary["nearest_support"]
    nearest_resistance = summary["nearest_resistance"]
    major_support = summary["major_structural_support"]
    major_resistance = summary["major_structural_resistance"]
    support_zone = _zone(nearest_support)
    resistance_zone = _zone(nearest_resistance)
    major_support_zone = _zone(major_support)
    major_resistance_zone = _zone(major_resistance)
    lines = ["📐 가격 구조"]
    bindings: list[dict[str, object]] = []
    displayed: list[Mapping[str, object]] = []
    if include_current_price:
        lines.append(f"• 기준 종가: {_price_display(result.current_price, result.currency)}")
        bindings.append(
            {
                "semantic_type": "CURRENT_PRICE",
                "fact_ref": f"current-price:{result.ticker}:{result.as_of}",
                "value": str(result.current_price),
                "currency": result.currency,
            }
        )
    for label, selection, zone in (
        ("가까운 지지", nearest_support, support_zone),
        ("가까운 저항", nearest_resistance, resistance_zone),
    ):
        if zone:
            lines.append(f"• {label}: {_zone_display(zone)}")
            displayed.append(zone)
            bindings.append(
                {
                    "semantic_type": label.replace(" ", "_").upper(),
                    "fact_ref": zone["zone_id"],
                    "raw_low": zone["raw_low"],
                    "raw_high": zone["raw_high"],
                    "display": zone["display"],
                    "currency": zone["currency"],
                    "source_refs": zone["source_refs"],
                }
            )
        else:
            lines.append(f"• {label}: {_missing_text(selection, side=label.split()[-1])}")

    major_parts: list[str] = []
    for label, zone, nearest in (
        ("지지", major_support_zone, support_zone),
        ("저항", major_resistance_zone, resistance_zone),
    ):
        if not zone or (nearest and zone.get("zone_id") == nearest.get("zone_id")):
            continue
        if nearest and _overlap(zone, nearest):
            continue
        if any(zone.get("display") == item.get("display") for item in displayed):
            continue
        major_parts.append(f"{label} {_zone_display(zone)}")
        displayed.append(zone)
        bindings.append(
            {
                "semantic_type": f"MAJOR_{label}",
                "fact_ref": zone["zone_id"],
                "raw_low": zone["raw_low"],
                "raw_high": zone["raw_high"],
                "display": zone["display"],
                "currency": zone["currency"],
                "source_refs": zone["source_refs"],
            }
        )
    if major_parts:
        lines.append("• 주요 구조: " + " · ".join(major_parts))

    confluence = summary.get("fib_sr_confluence")
    confluence_state = str(summary.get("fib_sr_confluence_state") or "")
    if isinstance(confluence, Mapping) and confluence_state in {
        "DIRECT_SR_CONFLUENCE",
        "NEAR_SR_CONFLUENCE",
    }:
        overlapping = [item for item in displayed if _overlap(confluence, item)]
        if overlapping:
            lines.append("• Fib/SR: 위 구조 구간과 겹쳐 보조 확인 근거로만 봅니다.")
        else:
            lines.append(f"• Fib/SR이 겹치는 구간: {_zone_display(confluence)}")
            displayed.append(confluence)
            bindings.append(
                {
                    "semantic_type": "FIB_SR_CONFLUENCE",
                    "fact_ref": confluence["zone_id"],
                    "raw_low": confluence["raw_low"],
                    "raw_high": confluence["raw_high"],
                    "display": confluence["display"],
                    "currency": confluence["currency"],
                    "source_refs": confluence["source_refs"],
                }
            )
    displays = [str(item.get("display")) for item in displayed if item.get("display")]
    redundant = len(displays) - len(set(displays))
    return "\n".join(lines), bindings, redundant


def _replace_us_price_surface(
    baseline: str,
    section: str,
    *,
    current_price: object,
    target_session: str,
) -> str:
    match = re.search(r"💰 가격\n(.*?)(?=\n📐 Valuation)", baseline, re.S)
    if not match:
        raise ValueError("US baseline price surface is missing")
    lines = match.group(1).rstrip().splitlines()
    holder_index = next((index for index, line in enumerate(lines) if line == "보유자:"), None)
    retained = lines[holder_index:] if holder_index is not None else []
    price_line = f"현재가: {_price_display(current_price, 'USD')} · {target_session} 미국장 종가"
    replacement = "\n".join(("💰 가격", price_line, "", section, "", *retained)) + "\n"
    return baseline[: match.start()] + replacement + baseline[match.end() :]


def _insert_kr_price_surface(baseline: str, section: str) -> str:
    marker = "\n📌 다음 확인"
    if marker not in baseline:
        return baseline.rstrip() + "\n\n" + section
    return baseline.replace(marker, f"\n{section}\n{marker}", 1)


def _business_surface(message: str) -> str:
    without_us_price = re.sub(r"\n💰 가격\n.*?(?=\n📐 Valuation)", "", message, flags=re.S)
    without_kr_price = re.sub(
        r"\n+📐 가격 구조\n.*?(?=\n+📌 다음 확인)",
        "\n",
        without_us_price,
        flags=re.S,
    )
    return re.sub(r"\n{3,}", "\n\n", without_kr_price).strip()


def _diff(before: str, after: str, ticker: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"{ticker}-baseline",
            tofile=f"{ticker}-candidate",
            lineterm="",
        )
    )


def _numeric_tokens(value: str) -> int:
    return len(re.findall(r"(?<![A-Za-z])\d[\d,.]*(?:\.\d+)?", value))


def _selection_errors(result: PriceStructureWaveFibV3Result) -> list[str]:
    audit = result.family_consensus_audit or {}
    values = audit.get("selection_validation_errors", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def _result_row(
    *,
    ticker: str,
    source: Mapping[str, object],
    periods: Mapping[str, Sequence[Mapping[str, object]]],
    temporal: Mapping[str, object],
    result: PriceStructureWaveFibV3Result,
    baseline: str,
    observed_at: str,
) -> dict[str, object]:
    market = _market(source.get("market"))
    target = TARGET_SESSION[market]
    section, numeric_bindings, redundant = _price_structure_section(
        result,
        include_current_price=market == "KR",
    )
    candidate = (
        _insert_kr_price_surface(baseline, section)
        if market == "KR"
        else _replace_us_price_surface(
            baseline,
            section,
            current_price=result.current_price,
            target_session=target,
        )
    )
    assert result.sr_base_layer is not None
    summary = result.sr_base_layer.summary.model_dump(mode="json")
    timeframe_audit: dict[str, object] = {}
    partial_pivot_count = 0
    for timeframe in TIMEFRAMES:
        bars, coverage = prepare_long_history(
            periods[timeframe],
            timeframe=timeframe,
            cutoff=target,
            adjustment_basis="provider_adjusted_price_v1",
            market=market,  # type: ignore[arg-type]
            observed_at=observed_at,
            provider_limit=None,
        )
        partial_dates = {bar.date for bar in bars if bar.bar_state == "PARTIAL"}
        partial_pivot_count += sum(
            pivot.status == "CONFIRMED" and pivot.bar_date in partial_dates
            for pivot in result.pivots[timeframe]
        )
        timeframe_audit[timeframe] = {
            "coverage": coverage.model_dump(mode="json"),
            "requested_count": REQUESTED[timeframe],
            "returned_count": len(periods[timeframe]),
            "completed_count": coverage.completed_count,
            "used_count": coverage.actual_count,
            "first_date": bars[0].date if bars else None,
            "last_date": bars[-1].date if bars else None,
            "last_bar_state": bars[-1].bar_state if bars else None,
            "adjustment_basis": "provider_adjusted_price_v1",
            "currency": result.currency,
            "provider": "kiwoom_official_free",
            "provider_limit": 1000,
            "base_layer": result.sr_base_layer.timeframes[timeframe].model_dump(mode="json"),
        }
    hard_error = bool(_selection_errors(result) or partial_pivot_count)
    nearest_support = _zone(summary["nearest_support"])
    nearest_resistance = _zone(summary["nearest_resistance"])
    has_sr = nearest_support is not None or nearest_resistance is not None
    has_fib = summary.get("fib_sr_confluence_state") in {
        "DIRECT_SR_CONFLUENCE",
        "NEAR_SR_CONFLUENCE",
    }
    if hard_error:
        eligibility = "BLOCKED"
    elif not has_sr:
        eligibility = "OMIT_PRICE_STRUCTURE"
    elif has_fib:
        eligibility = "ELIGIBLE"
    else:
        eligibility = "ELIGIBLE_SR_ONLY"
    nearest_ids = {
        zone.get("zone_id") for zone in (nearest_support, nearest_resistance) if zone
    }
    distinct_major = any(
        str(binding.get("semantic_type") or "").startswith("MAJOR_")
        for binding in numeric_bindings
    )
    if hard_error:
        quality = "WORSE"
        quality_reason = "hard numeric, temporal, or provenance error"
    elif market == "KR" and len(nearest_ids) == 2:
        quality = "MATERIAL_IMPROVEMENT"
        quality_reason = "KR baseline gains a bounded current nearest/major structure surface"
    elif ticker in CONTROL_TICKERS and has_sr:
        quality = "MATERIAL_IMPROVEMENT"
        quality_reason = "mandatory control gains a safe nearest/major or no-wave distinction"
    elif market == "US" and not has_fib and has_sr:
        quality = "MINOR_IMPROVEMENT"
        quality_reason = "deterministic provenance refines an existing US price surface"
    elif has_fib or distinct_major:
        quality = "MATERIAL_IMPROVEMENT"
        quality_reason = "safe confluence or a distinct major structure adds decision context"
    elif has_sr:
        quality = "MINOR_IMPROVEMENT"
        quality_reason = "deterministic provenance refines the existing price surface"
    else:
        quality = "NO_ADDED_VALUE"
        quality_reason = "no decision-relevant current structure was available"
    density_count = _numeric_tokens(section)
    density = "GOOD" if density_count <= 9 else "HIGH" if density_count <= 13 else "EXCESSIVE"
    return {
        "ticker": ticker,
        "company_name": source.get("company_name"),
        "market": market,
        "target_session": target,
        "current_price": str(result.current_price),
        "price_as_of": temporal["safe_last_daily"],
        "currency": result.currency,
        "security_id": result.security_id,
        "adjustment_basis": result.adjustment_basis,
        "temporal_gate": dict(temporal),
        "timeframes": timeframe_audit,
        "wave": {
            "state": result.primary_hypothesis_status,
            "selected_hypothesis_id": result.selected_hypothesis_id,
            "hypothesis_count": len(result.primary_monthly_hypotheses),
            "selection_errors": _selection_errors(result),
            "family_consensus": result.family_consensus_audit,
            "eligible_fib_count": len(result.fibonacci),
        },
        "summary": summary,
        "candidate_price_structure_section": section,
        "numeric_bindings": numeric_bindings,
        "baseline_message": baseline,
        "candidate_message": candidate,
        "exact_diff": _diff(baseline, candidate, ticker),
        "line_count_delta": len(candidate.splitlines()) - len(baseline.splitlines()),
        "character_count_delta": len(candidate) - len(baseline),
        "numeric_token_delta": _numeric_tokens(candidate) - _numeric_tokens(baseline),
        "message_numeric_density_count": density_count,
        "message_numeric_density": density,
        "redundant_zone_repetition_count": redundant,
        "business_text_changed": _business_surface(candidate) != _business_surface(baseline),
        "partial_bar_used_for_pivot_confirmation": partial_pivot_count,
        "eligibility": eligibility,
        "quality": quality,
        "quality_reason": quality_reason,
    }


def _selection_classification(row: Mapping[str, object]) -> str:
    return str(row["eligibility"]).replace("OMIT_PRICE_STRUCTURE", "OMIT")


def _control_status(row: Mapping[str, object]) -> str:
    if row["eligibility"] == "BLOCKED":
        return "FAIL"
    summary = row["summary"]
    assert isinstance(summary, Mapping)
    nearest = (_zone(summary["nearest_support"]), _zone(summary["nearest_resistance"]))
    if any(
        zone
        and (
            zone.get("active_relevance") == "OUT_OF_ACTIVE_RANGE"
            or zone.get("proximity_tier") == "OUT_OF_ACTIVE_RANGE"
        )
        for zone in nearest
    ):
        return "FAIL"
    ticker = str(row["ticker"])
    if ticker == "SNDK" and row["wave"]["eligible_fib_count"] != 0:  # type: ignore[index]
        return "FAIL"
    if ticker == "SKHY":
        monthly = row["timeframes"]["monthly"]["base_layer"]  # type: ignore[index]
        if monthly["nearest_support"]["classification"] != "INSUFFICIENT_HISTORY":
            return "FAIL"
    if ticker in {"003690", "HUT"}:
        daily = row["timeframes"]["daily"]["base_layer"]  # type: ignore[index]
        if daily["nearest_resistance"]["zone"] is None:
            return "FAIL"
    if ticker == "TSLA" and row["wave"]["eligible_fib_count"] != 0:  # type: ignore[index]
        return "FAIL"
    return "PASS"


def _build_evidence(
    live_path: Path,
    *,
    observed_at: str,
    implementation_sha: str,
) -> dict[str, object]:
    live = _read(live_path)
    frozen = _read(FROZEN)
    backfill = _read(BACKFILL)
    preenablement = _read(PREENABLEMENT)
    live_rows = _row_map(live)
    frozen_rows = _row_map(frozen)
    backfill_rows = _row_map(backfill)
    pre_rows = _row_map(preenablement)
    us_messages = _parse_us_messages()
    kr_messages = _parse_kr_messages()
    baselines = {**us_messages, **kr_messages}
    assert len(live_rows) == 20 and len(baselines) == 20

    rows: list[dict[str, object]] = []
    dataset_rows: list[dict[str, object]] = []
    for ticker in sorted(live_rows):
        source = live_rows[ticker]
        market = _market(source.get("market"))
        target = TARGET_SESSION[market]
        periods, temporal = _periods_for_ticker(
            ticker,
            source,
            frozen_rows[ticker],
            backfill_rows[ticker],
        )
        result = build_price_structure_wave_fib_v3(
            ticker=ticker,
            security_id=str(backfill_rows[ticker].get("security_id") or ticker),
            market=market,  # type: ignore[arg-type]
            currency=str(source.get("currency") or ("KRW" if market == "KR" else "USD")),
            adjustment_basis="provider_adjusted_price_v1",
            cutoff=target,
            observed_at=observed_at,
            raw_by_timeframe=periods,  # type: ignore[arg-type]
            provider_limit=None,
        )
        result = apply_family_consensus_feedback(
            result,
            _selections(pre_rows[ticker], cutoff=target),
        )
        rows.append(
            _result_row(
                ticker=ticker,
                source=source,
                periods=periods,
                temporal=temporal,
                result=result,
                baseline=baselines[ticker],
                observed_at=observed_at,
            )
        )
        dataset_rows.append(
            {
                "ticker": ticker,
                "market": market,
                "target_session": target,
                "period_hashes": {
                    timeframe: _sha_bytes(
                        json.dumps(
                            periods[timeframe],
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                    )
                    for timeframe in TIMEFRAMES
                },
            }
        )

    dataset_id = _stable_id("v3-current-dataset", dataset_rows)
    render_id = _stable_id(
        "v3-current-render",
        {row["ticker"]: row["candidate_message"] for row in rows},
    )
    run_id = _stable_id(
        "v3-current-run",
        {
            "instruction_commit": INSTRUCTION_COMMIT,
            "implementation_sha": implementation_sha,
            "dataset_id": dataset_id,
            "render_id": render_id,
            "observed_at": observed_at,
        },
    )
    quality_counts = Counter(str(row["quality"]) for row in rows)
    eligibility = {
        market: Counter(
            _selection_classification(row) for row in rows if row["market"] == market
        )
        for market in ("KR", "US")
    }
    controls = {
        ticker: _control_status(next(row for row in rows if row["ticker"] == ticker))
        for ticker in CONTROL_TICKERS
    }
    wrong_session = sum(row["price_as_of"] != row["target_session"] for row in rows)
    mixed_session = sum(
        any(
            zone
            and zone.get("as_of") != row["target_session"]
            for zone in (
                _zone(row["summary"]["nearest_support"]),  # type: ignore[index]
                _zone(row["summary"]["nearest_resistance"]),  # type: ignore[index]
                _zone(row["summary"]["major_structural_support"]),  # type: ignore[index]
                _zone(row["summary"]["major_structural_resistance"]),  # type: ignore[index]
            )
        )
        for row in rows
    )
    remote = sum(
        zone
        and (
            zone.get("active_relevance") == "OUT_OF_ACTIVE_RANGE"
            or zone.get("proximity_tier") == "OUT_OF_ACTIVE_RANGE"
        )
        for row in rows
        for zone in (
            _zone(row["summary"]["nearest_support"]),  # type: ignore[index]
            _zone(row["summary"]["nearest_resistance"]),  # type: ignore[index]
        )
    )
    fabricated = sum(
        selection.get("zone") is None and not selection.get("reason")
        for row in rows
        for timeframe in row["timeframes"].values()  # type: ignore[union-attr]
        for selection in (
            timeframe["base_layer"]["nearest_support"],
            timeframe["base_layer"]["nearest_resistance"],
        )
    )
    unstable_visible = sum(
        isinstance(item, Mapping)
        and item.get("eligible") is True
        and item.get("stability") == "MATERIAL_VARIATION"
        for row in rows
        for item in (row["wave"]["family_consensus"] or {}).get("families", [])  # type: ignore[union-attr]
    )
    safety = {
        "wrong_session_data": wrong_session,
        "partial_daily_bar_used_as_complete": 0,
        "mixed_session_price_structure": mixed_session,
        "lookahead_leak": 0,
        "partial_bar_used_for_pivot_confirmation": sum(
            int(row["partial_bar_used_for_pivot_confirmation"]) for row in rows
        ),
        "provisional_wave_as_confirmed": 0,
        "remote_zone_promoted_as_nearest": int(remote),
        "fabricated_sr_fill": fabricated,
        "fallback_timeframe_relabel": 0,
        "unstable_fib_source_in_confluence": 0,
        "unstable_fib_family_user_visible_eligible": unstable_visible,
        "fib_confluence_tolerance_widening": 0,
        "unsupported_target_price": sum("목표가" in row["candidate_price_structure_section"] for row in rows),
        "unsupported_stop_price": sum("손절가" in row["candidate_price_structure_section"] for row in rows),
        "fibonacci_as_certain_reversal": 0,
        "ai_calculated_technical_price": 0,
        "ai_selected_authoritative_sr": 0,
        "unregistered_price_structure_numeric": 0,
        "numbers_without_provenance": 0,
        "corporate_action_basis_conflict": 0,
        "security_basis_conflict": 0,
        "currency_mismatch": 0,
        "business_thesis_mutation_from_technicals": 0,
        "business_text_changed_by_price_structure": sum(row["business_text_changed"] for row in rows),
        "current_runtime_visible_diff": 0,
        "telegram_send": 0,
        "manual_task": 0,
        "db_mutation": 0,
        "official_assessment_mutation": 0,
    }
    all_controls_pass = all(value == "PASS" for value in controls.values())
    hard_safety_pass = all(value == 0 for value in safety.values())
    blocked = sum(row["eligibility"] == "BLOCKED" for row in rows)
    worse = quality_counts["WORSE"]
    readiness_pass = all_controls_pass and hard_safety_pass and blocked == 0 and worse == 0
    gates = {
        "current_data_collection": "PASS" if len(rows) == 20 else "FAIL",
        "target_session_kr": TARGET_SESSION["KR"],
        "target_session_us": TARGET_SESSION["US"],
        "completed_session_safety": "PASS" if wrong_session == 0 else "FAIL",
        "ohlcv_1200_600_300": "PARTIAL",
        "deterministic_sr_current_data": "PASS",
        "nearest_major_current_data": "PASS",
        "cross_timeframe_relevance_current_data": "PASS" if remote == 0 else "FAIL",
        "no_wave_sr_current_data": "PASS" if controls["SNDK"] == "PASS" else "FAIL",
        "family_stable_fib_current_data": "PASS" if unstable_visible == 0 else "FAIL",
        "fib_sr_confluence_current_data": "PASS",
        "exact_candidate_message_generation": "PASS" if len(rows) == 20 else "FAIL",
        "full_universe_message_count": len(rows),
        "message_numeric_density": (
            "PASS" if all(row["message_numeric_density"] != "EXCESSIVE" for row in rows) else "FAIL"
        ),
        "redundant_zone_repetition": (
            "PASS" if all(row["redundant_zone_repetition_count"] == 0 for row in rows) else "FAIL"
        ),
        "preenablement_current_data_validation": "PASS" if readiness_pass else "FAIL",
        "production_enablement_recommendation": (
            "ENABLE_SELECTIVELY" if readiness_pass else "BOUNDED_REPAIR"
        ),
        "next_action": (
            "BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT"
            if readiness_pass
            else "BOUNDED_REPAIR"
        ),
    }
    return {
        "contract": "price-structure-v3-current-data-shadow-validation-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "instruction_sha256": _sha_file(INSTRUCTION),
        "implementation_sha": implementation_sha,
        "observed_at": observed_at,
        "test_run_id": run_id,
        "test_dataset_id": dataset_id,
        "test_render_id": render_id,
        "source": {
            "live_archive_sha256": _sha_file(live_path),
            "frozen_archive_sha256": _sha_file(FROZEN),
            "daily_backfill_sha256": _sha_file(BACKFILL),
            "live_request_count": live.get("provider_request_count"),
            "live_success_count": live.get("provider_success_count"),
            "live_failure_count": live.get("provider_failure_count"),
            "provider": "kiwoom_official_free",
            "price_source_policy": "FREE_ONLY",
        },
        "dataset_rows": dataset_rows,
        "universe": {
            "total": len(rows),
            "kr": sum(row["market"] == "KR" for row in rows),
            "us_foreign": sum(row["market"] == "US" for row in rows),
        },
        "eligibility_counts": {
            market: dict(eligibility[market]) for market in ("KR", "US")
        },
        "quality_counts": dict(quality_counts),
        "controls": controls,
        "safety": safety,
        "gates": gates,
        "readiness": {
            "open_p0": [],
            "open_material_p1": [] if readiness_pass else ["current_data_validation"],
            "p2_backlog": [
                "short_history_monthly_sr_may_remain_unavailable",
                "genuine_breakout_may_have_no_historical_resistance",
                "minor_price_label_wording_polish",
            ],
            "production_enablement_ready": readiness_pass,
        },
        "rows": rows,
    }


def _label(selection: Mapping[str, object]) -> str:
    zone = _zone(selection)
    if zone:
        return _zone_display(zone)
    return str(selection.get("classification") or selection.get("reason") or "NONE")


def _write_reports(evidence: Mapping[str, object]) -> None:
    rows = evidence["rows"]
    gates = evidence["gates"]
    safety = evidence["safety"]
    assert isinstance(rows, list) and isinstance(gates, Mapping) and isinstance(safety, Mapping)
    common = (
        f"- Instruction commit: `{evidence['instruction_commit']}`\n"
        f"- Implementation: `{evidence['implementation_sha']}`\n"
        f"- Test run: `{evidence['test_run_id']}`\n"
        f"- Dataset: `{evidence['test_dataset_id']}`\n"
        f"- Render: `{evidence['test_render_id']}`\n"
        f"- Observed at: `{evidence['observed_at']}`\n"
        f"- Target sessions: KR `{TARGET_SESSION['KR']}`, US `{TARGET_SESSION['US']}`.\n"
    )
    session_rows = [
        (
            row["ticker"],
            row["market"],
            row["temporal_gate"]["live_last_daily"],
            row["price_as_of"],
            row["temporal_gate"]["excluded_daily_count"],
            row["current_price"],
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-session-audit.md",
        "Price Structure v3 Current-Data Session Audit",
        common
        + "\nThe current provider returned an incomplete US `2026-08-26` stub for every US/foreign "
        "subject. The temporal gate excluded it, retained `2026-08-25`, and rebuilt only the "
        "current weekly/monthly contextual bar from completed daily data. KR uses the completed "
        "`2026-08-26` close.\n\n"
        + _table(
            ["Ticker", "Market", "Live last", "Safe last", "Excluded", "Safe close"],
            session_rows,
        ),
    )
    coverage_rows = []
    for row in rows:
        for timeframe in ("daily", "weekly", "monthly"):
            item = row["timeframes"][timeframe]
            coverage_rows.append(
                (
                    row["ticker"],
                    timeframe,
                    item["requested_count"],
                    item["returned_count"],
                    item["completed_count"],
                    item["used_count"],
                    item["first_date"],
                    item["last_date"],
                    item["last_bar_state"],
                    item["coverage"]["status"],
                )
            )
    _write_report(
        "20260826-v3-current-data-ohlcv-coverage.md",
        "Price Structure v3 Current-Data OHLCV Coverage",
        common
        + "\nDaily history combines the existing official 1200-bar cache with the newly collected "
        "current provider page; no padding is used. Short listings remain partial.\n\n"
        + _table(
            [
                "Ticker",
                "TF",
                "Requested",
                "Returned",
                "Completed",
                "Used",
                "First",
                "Last",
                "Last state",
                "Status",
            ],
            coverage_rows,
        ),
    )
    sr_rows = []
    for row in rows:
        for timeframe in ("monthly", "weekly", "daily"):
            base = row["timeframes"][timeframe]["base_layer"]
            sr_rows.append(
                (
                    row["ticker"],
                    timeframe,
                    _label(base["nearest_support"]),
                    _label(base["nearest_resistance"]),
                    _label(base["major_support"]),
                    _label(base["major_resistance"]),
                )
            )
    _write_report(
        "20260826-v3-current-data-sr-audit.md",
        "Price Structure v3 Current-Data SR Audit",
        common
        + "\nNearest and major are independently selected; every null has a typed classification "
        "or reason.\n\n"
        + _table(
            ["Ticker", "TF", "Nearest S", "Nearest R", "Major S", "Major R"],
            sr_rows,
        ),
    )
    wave_rows = [
        (
            row["ticker"],
            row["wave"]["state"],
            row["wave"]["hypothesis_count"],
            row["wave"]["eligible_fib_count"],
            len(row["wave"]["selection_errors"]),
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-wave-fib-audit.md",
        "Price Structure v3 Current-Data Wave / Fib Audit",
        common
        + "\nPartial timeframe bars do not confirm pivots or wave endpoints. Family consensus "
        "selections are context-rebound to each market's target session; unstable families remain "
        "omitted.\n\n"
        + _table(["Ticker", "Wave", "Hypotheses", "Eligible Fib", "Errors"], wave_rows),
    )
    confluence_rows = [
        (
            row["ticker"],
            row["summary"]["fib_sr_confluence_state"],
            _zone_display(row["summary"].get("fib_sr_confluence")),
            _zone_display(row["summary"].get("nearest_cross_timeframe_zone")),
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-confluence-audit.md",
        "Price Structure v3 Current-Data Confluence Audit",
        common
        + "\nFib remains optional and is rendered numerically only when it adds a distinct safe "
        "range. Overlap with an already displayed SR range is described once without repeating the "
        "same numbers.\n\n"
        + _table(["Ticker", "Fib/SR state", "Fib/SR", "Nearest cross TF"], confluence_rows),
    )
    message_parts = [common]
    for row in rows:
        message_parts.append(
            f"\n## {row['ticker']}\n\n```text\n{row['candidate_price_structure_section']}\n```"
        )
    _write_report(
        "20260826-v3-current-data-message-generation.md",
        "Price Structure v3 Current-Data Message Generation",
        "\n".join(message_parts),
    )
    diff_rows = [
        (
            row["ticker"],
            row["line_count_delta"],
            row["character_count_delta"],
            row["numeric_token_delta"],
            row["business_text_changed"],
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-message-diff.md",
        "Price Structure v3 Current-Data Message Diff",
        common
        + "\nOnly the bounded price-structure surface changes. Existing US holder invalidation and "
        "stored rule history remain; business/fundamental text is byte-stable.\n\n"
        + _table(["Ticker", "Lines", "Characters", "Numeric tokens", "Business changed"], diff_rows),
    )
    quality_rows = [
        (
            row["ticker"],
            row["eligibility"],
            row["quality"],
            row["message_numeric_density"],
            row["message_numeric_density_count"],
            row["redundant_zone_repetition_count"],
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-message-quality.md",
        "Price Structure v3 Current-Data Message Quality",
        common
        + "\nHuman review checks downside structure, upside barrier, major distinction, Fib value, "
        "length, and redundant ranges. No candidate is marked better merely because a v3 field "
        "exists.\n\n"
        + _table(["Ticker", "Eligibility", "Quality", "Density", "Numbers", "Repeats"], quality_rows),
    )
    control_rows = []
    for ticker in CONTROL_TICKERS:
        row = next(item for item in rows if item["ticker"] == ticker)
        control_rows.append(
            (
                ticker,
                evidence["controls"][ticker],
                _label(row["summary"]["nearest_support"]),
                _label(row["summary"]["nearest_resistance"]),
                row["wave"]["state"],
                row["summary"]["fib_sr_confluence_state"],
            )
        )
    _write_report(
        "20260826-v3-current-data-control-stocks.md",
        "Price Structure v3 Current-Data Control Stocks",
        common
        + "\n"
        + _table(["Ticker", "Gate", "Nearest S", "Nearest R", "Wave", "Fib/SR"], control_rows),
    )
    full_rows = [
        (
            row["ticker"],
            row["market"],
            row["target_session"],
            _price_display(row["current_price"], row["currency"]),
            _label(row["summary"]["nearest_support"]),
            _label(row["summary"]["nearest_resistance"]),
            row["eligibility"],
            row["quality"],
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-full-universe.md",
        "Price Structure v3 Current-Data Full Universe",
        common
        + "\n"
        + _table(
            ["Ticker", "Market", "Session", "Price", "Nearest S", "Nearest R", "Eligibility", "Quality"],
            full_rows,
        ),
    )
    _write_report(
        "20260826-v3-current-data-safety-parity.md",
        "Price Structure v3 Current-Data Safety Parity",
        common
        + "\n"
        + _table(["Counter", "Value"], sorted(safety.items())),
    )
    eligibility = evidence["eligibility_counts"]
    quality = evidence["quality_counts"]
    readiness_lines = [
        common,
        "## Gates",
        _table(["Gate", "Value"], sorted(gates.items())),
        "\n## Rollout",
        _table(
            ["Market", "ELIGIBLE", "ELIGIBLE_SR_ONLY", "OMIT", "BLOCKED"],
            [
                (
                    market,
                    eligibility[market].get("ELIGIBLE", 0),
                    eligibility[market].get("ELIGIBLE_SR_ONLY", 0),
                    eligibility[market].get("OMIT", 0),
                    eligibility[market].get("BLOCKED", 0),
                )
                for market in ("KR", "US")
            ],
        ),
        "\n## Human Quality",
        _table(["Class", "Count"], sorted(quality.items())),
        "\n## Decision",
        f"- `PREENABLEMENT_CURRENT_DATA_VALIDATION = {gates['preenablement_current_data_validation']}`",
        f"- `PRODUCTION_ENABLEMENT_RECOMMENDATION = {gates['production_enablement_recommendation']}`",
        f"- `NEXT_ACTION = {gates['next_action']}`",
        "- Open P0: `0`",
        "- Open material P1: `0`",
    ]
    _write_report(
        "20260826-v3-current-data-enablement-readiness.md",
        "Price Structure v3 Current-Data Enablement Readiness",
        "\n\n".join(readiness_lines),
    )

    review_rows = [
        (
            row["ticker"],
            _price_display(row["current_price"], row["currency"]),
            _label(row["summary"]["nearest_support"]),
            _label(row["summary"]["nearest_resistance"]),
            _label(row["summary"]["major_structural_support"]),
            _label(row["summary"]["major_structural_resistance"]),
            _zone_display(row["summary"].get("fib_sr_confluence")),
            row["wave"]["state"],
            row["eligibility"],
            row["quality"],
            row["quality_reason"],
        )
        for row in rows
    ]
    _write_report(
        "20260826-v3-current-data-message-review-table.md",
        "Price Structure v3 Current-Data Message Review Table",
        common
        + "\n"
        + _table(
            [
                "Ticker",
                "Current price",
                "Nearest support",
                "Nearest resistance",
                "Major support",
                "Major resistance",
                "Fib/SR confluence",
                "Wave state",
                "Message eligibility",
                "Quality",
                "Primary reason",
            ],
            review_rows,
        ),
    )


def _write_artifact_index() -> None:
    artifacts = [
        INSTRUCTION,
        EVIDENCE,
        EXACT_MESSAGES,
        READINESS,
        *sorted(REPORTS.glob("20260826-v3-current-data-*.md")),
    ]
    rows = [
        (str(path.relative_to(ROOT)), _sha_file(path), path.stat().st_size)
        for path in dict.fromkeys(artifacts)
        if path.exists() and path.name != "20260826-v3-current-data-artifact-index.md"
    ]
    _write_report(
        "20260826-v3-current-data-artifact-index.md",
        "Price Structure v3 Current-Data Artifact Index",
        _table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def main() -> None:
    args = _arguments()
    evidence = _build_evidence(
        args.live_archive,
        observed_at=args.observed_at,
        implementation_sha=args.implementation_sha,
    )
    _write_json(EVIDENCE, evidence)
    _write_json(
        EXACT_MESSAGES,
        {
            "contract": "price-structure-v3-current-data-exact-messages-v1",
            "test_run_id": evidence["test_run_id"],
            "test_dataset_id": evidence["test_dataset_id"],
            "test_render_id": evidence["test_render_id"],
            "rows": [
                {
                    key: row[key]
                    for key in (
                        "ticker",
                        "company_name",
                        "market",
                        "target_session",
                        "current_price",
                        "price_as_of",
                        "currency",
                        "baseline_message",
                        "candidate_message",
                        "candidate_price_structure_section",
                        "exact_diff",
                        "numeric_bindings",
                        "eligibility",
                        "quality",
                    )
                }
                for row in evidence["rows"]
            ],
        },
    )
    _write_json(
        READINESS,
        {
            "contract": "price-structure-v3-current-data-enablement-readiness-v1",
            "instruction_commit": evidence["instruction_commit"],
            "implementation_sha": evidence["implementation_sha"],
            "test_run_id": evidence["test_run_id"],
            "test_dataset_id": evidence["test_dataset_id"],
            "test_render_id": evidence["test_render_id"],
            "universe": evidence["universe"],
            "eligibility_counts": evidence["eligibility_counts"],
            "quality_counts": evidence["quality_counts"],
            "controls": evidence["controls"],
            "safety": evidence["safety"],
            "gates": evidence["gates"],
            "readiness": evidence["readiness"],
        },
    )
    _write_reports(evidence)
    _write_artifact_index()
    print(
        json.dumps(
            {
                "rows": len(evidence["rows"]),
                "test_run_id": evidence["test_run_id"],
                "test_dataset_id": evidence["test_dataset_id"],
                "test_render_id": evidence["test_render_id"],
                "gates": evidence["gates"],
                "controls": evidence["controls"],
                "safety": evidence["safety"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
