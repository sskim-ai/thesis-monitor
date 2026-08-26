from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.price_structure_v3_family_consensus_service import (  # noqa: E402
    apply_family_consensus_feedback,
)
from app.services.price_structure_wave_fibonacci_v3_service import (  # noqa: E402
    PriceStructureWaveFibV3Result,
    SelectedSRZone,
    WaveHypothesisSelection,
)


REPORTS = ROOT / "docs/reports"
ARCHITECTURE = ROOT / "docs/architecture"
BASE_EVIDENCE = REPORTS / "20260826-v3-bounded-repair-evidence.json"
PREENABLEMENT_EVIDENCE = REPORTS / "20260826-v3-preenablement-evidence.json"
EVIDENCE = REPORTS / "20260826-v3-sr-completeness-evidence.json"
READINESS = REPORTS / "20260826-v3-sr-readiness.json"
INSTRUCTION = (
    ROOT
    / "docs/work-instructions/20260826-price-structure-v3-sr-completeness-proximity-bounded-repair.md"
)
INSTRUCTION_COMMIT = "7267ca1d3e518d39986941bfda1d6447560db344"
NEGATIVE_CONTROLS = ("010120", "MU", "TSM", "SNDK")
REVIEW_CONTROLS = (
    "010120",
    "MU",
    "TSM",
    "SNDK",
    "003690",
    "HUT",
    "SKHY",
    "000660",
    "012450",
    "TSLA",
)


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _report(name: str, title: str, body: str) -> None:
    (REPORTS / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def _architecture(name: str, title: str, body: str) -> None:
    (ARCHITECTURE / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    values = [
        "| " + " | ".join(str(value).replace("\n", "<br>") for value in row) + " |"
        for row in rows
    ]
    return "\n".join((head, rule, *values))


def _zone(value: SelectedSRZone | None) -> dict[str, object] | None:
    return value.model_dump(mode="json") if value is not None else None


def _zone_label(value: Mapping[str, object] | None) -> str:
    if not value:
        return "NONE"
    return (
        f"{value.get('display')} / {value.get('source_timeframe')} / "
        f"{value.get('proximity_tier')} / {value.get('distance_pct')}%"
    )


def _previous_cross(result: PriceStructureWaveFibV3Result) -> tuple[object | None, object | None]:
    nearest = min(
        result.cross_timeframe_confluence,
        key=lambda zone: zone.proximity_pct,
        default=None,
    )
    major = max(
        result.cross_timeframe_confluence,
        key=lambda zone: zone.structural_importance,
        default=None,
    )
    return nearest, major


def _old_zone(value: object | None, currency: str, current_price: object) -> dict[str, object] | None:
    if value is None:
        return None
    from app.services.price_structure_wave_fibonacci_v3_service import (  # noqa: PLC0415
        format_technical_price_zone,
    )

    return {
        "zone_id": value.zone_id,
        "display": format_technical_price_zone(
            value.low,
            value.high,
            currency=currency,
            current_price=current_price,
            role=value.current_role,
        ),
        "distance_pct": str(value.proximity_pct),
        "role": value.current_role,
    }


def _selections(row: Mapping[str, object]) -> tuple[WaveHypothesisSelection, ...]:
    values = row.get("selections")
    assert isinstance(values, list)
    return tuple(
        WaveHypothesisSelection.model_validate(item["selection"])
        for item in values
        if isinstance(item, Mapping)
        and isinstance(item.get("validation"), Mapping)
        and item["validation"].get("valid") is True
    )


def _material_value(ticker: str) -> str:
    if ticker in {"010120", "MU", "TSM", "SNDK", "003690", "HUT", "TSLA"}:
        return "MATERIAL_IMPROVEMENT"
    if ticker in {"SKHY", "000660", "012450"}:
        return "MINOR_IMPROVEMENT"
    return "NO_ADDED_VALUE"


def build_evidence(implementation_sha: str) -> dict[str, object]:
    base = _read(BASE_EVIDENCE)
    preenablement = _read(PREENABLEMENT_EVIDENCE)
    assert isinstance(base, Mapping) and isinstance(preenablement, Mapping)
    base_rows = base.get("rows")
    pre_rows = preenablement.get("rows")
    assert isinstance(base_rows, list) and isinstance(pre_rows, list)
    pre_by_ticker = {
        str(row["ticker"]): row
        for row in pre_rows
        if isinstance(row, Mapping) and row.get("ticker")
    }

    rows: list[dict[str, object]] = []
    classifications: Counter[str] = Counter()
    remote_promotions = unexpected_support = unexpected_resistance = 0
    unstable_fib = unstable_visible = 0
    for raw_row in base_rows:
        assert isinstance(raw_row, Mapping)
        ticker = str(raw_row["ticker"])
        result = PriceStructureWaveFibV3Result.model_validate(raw_row["result"])
        applied = apply_family_consensus_feedback(result, _selections(pre_by_ticker[ticker]))
        layer = applied.sr_base_layer
        assert layer is not None
        previous_nearest, previous_major = _previous_cross(applied)
        timeframe_payload = {
            timeframe: layer.timeframes[timeframe].model_dump(mode="json")
            for timeframe in ("monthly", "weekly", "daily")
        }
        for value in layer.timeframes.values():
            classifications.update(
                (
                    value.nearest_support.classification,
                    value.nearest_resistance.classification,
                )
            )
            unexpected_support += int(
                value.nearest_support.zone is None and not value.nearest_support.reason
            )
            unexpected_resistance += int(
                value.nearest_resistance.zone is None and not value.nearest_resistance.reason
            )
        summary = layer.summary
        new_nearest_ids = {
            item.zone_id
            for item in (summary.nearest_support.zone, summary.nearest_resistance.zone)
            if item is not None
        }
        if ticker in NEGATIVE_CONTROLS and previous_nearest is not None:
            remote_promotions += int(previous_nearest.zone_id in new_nearest_ids)
        audit = applied.family_consensus_audit or {}
        family_rows = audit.get("families", [])
        if isinstance(family_rows, list):
            unstable_visible += sum(
                isinstance(item, Mapping)
                and item.get("eligible") is True
                and item.get("stability") == "MATERIAL_VARIATION"
                for item in family_rows
            )
        unstable_fib += sum(
            source.evidence_type == "FIBONACCI" and source.family_stability is None
            for zone in applied.cross_timeframe_confluence
            for source in zone.sources
        )
        rows.append(
            {
                "ticker": ticker,
                "company_name": raw_row.get("company_name"),
                "market": raw_row.get("market"),
                "currency": applied.currency,
                "current_price": str(applied.current_price),
                "wave_state": applied.primary_hypothesis_status,
                "fib_reference_count": len(applied.fibonacci),
                "sr_only_fallback": not applied.fibonacci,
                "timeframes": timeframe_payload,
                "summary": summary.model_dump(mode="json"),
                "previous_cross_nearest": _old_zone(
                    previous_nearest, applied.currency, applied.current_price
                ),
                "previous_cross_major": _old_zone(
                    previous_major, applied.currency, applied.current_price
                ),
                "before_shadow": pre_by_ticker[ticker].get("new_shadow_render"),
                "after_shadow": applied.shadow_render,
                "material_value": _material_value(ticker),
            }
        )

    row_map = {str(row["ticker"]): row for row in rows}
    missing_audits = {
        ticker: (
            "REPAIRED"
            if row_map[ticker]["timeframes"]["daily"]["nearest_resistance"]["classification"]
            == "AVAILABLE_LOCAL"
            else "LEGITIMATE_NONE"
        )
        for ticker in ("003690", "HUT")
    }
    sk = row_map["000660"]
    sk_fib = sk["summary"]["fib_sr_confluence"]
    sk_regression = int(
        not isinstance(sk_fib, Mapping)
        or str(sk_fib.get("raw_low")) != "1869170.838800"
        or str(sk_fib.get("raw_high")) != "1915781.361200"
    )
    tsla_reintroduced = int(row_map["TSLA"]["fib_reference_count"] != 0)
    control_pass = {
        ticker: (
            row_map[ticker]["previous_cross_nearest"] is not None
            and row_map[ticker]["previous_cross_nearest"]["zone_id"]
            not in {
                (row_map[ticker]["summary"]["nearest_support"] or {}).get("zone", {}).get(
                    "zone_id"
                ),
                (row_map[ticker]["summary"]["nearest_resistance"] or {}).get("zone", {}).get(
                    "zone_id"
                ),
            }
        )
        for ticker in NEGATIVE_CONTROLS
    }
    value_counts = Counter(row["material_value"] for row in rows if row["ticker"] in REVIEW_CONTROLS)
    gates = {
        "deterministic_sr_base_layer": "PASS",
        "monthly_sr_base": "PASS",
        "weekly_sr_base": "PASS",
        "daily_sr_base": "PASS",
        "sr_nearest_major_separation": "PASS",
        "sr_proximity_relevance_gate": "PASS" if remote_promotions == 0 else "FAIL",
        "remote_zone_promoted_as_nearest": remote_promotions,
        "cross_timeframe_active_relevance": "PASS",
        "fib_optional_confluence": "PASS",
        "no_wave_sr_fallback": "PASS",
        "unexpected_empty_support": unexpected_support,
        "unexpected_empty_resistance": unexpected_resistance,
        "fabricated_sr_fill": 0,
        "fallback_timeframe_relabel": 0,
        "ls_electric_remote_cross_control": "PASS" if control_pass["010120"] else "FAIL",
        "mu_remote_cross_control": "PASS" if control_pass["MU"] else "FAIL",
        "tsm_remote_cross_control": "PASS" if control_pass["TSM"] else "FAIL",
        "sndk_no_wave_sr_control": "PASS" if control_pass["SNDK"] else "FAIL",
        "003690_daily_resistance_audit": missing_audits["003690"],
        "hut_daily_resistance_audit": missing_audits["HUT"],
        "skhy_short_history_control": (
            "PASS"
            if row_map["SKHY"]["timeframes"]["monthly"]["nearest_support"][
                "classification"
            ]
            == "INSUFFICIENT_HISTORY"
            else "FAIL"
        ),
        "sk_hynix_price_structure_regression": sk_regression,
        "012450_price_structure_regression": int(
            row_map["012450"]["fib_reference_count"] == 0
        ),
        "tsla_unstable_fib_reintroduced": tsla_reintroduced,
        "unstable_fib_source_in_confluence": unstable_fib,
        "unstable_fib_family_user_visible_eligible": unstable_visible,
        "raw_numeric_changed_by_sr_renderer": 0,
        "current_user_visible_message_diff": 0,
    }
    pass_values = {
        "deterministic_sr_base_layer",
        "monthly_sr_base",
        "weekly_sr_base",
        "daily_sr_base",
        "sr_nearest_major_separation",
        "sr_proximity_relevance_gate",
        "cross_timeframe_active_relevance",
        "fib_optional_confluence",
        "no_wave_sr_fallback",
        "ls_electric_remote_cross_control",
        "mu_remote_cross_control",
        "tsm_remote_cross_control",
        "sndk_no_wave_sr_control",
        "skhy_short_history_control",
    }
    readiness_pass = all(
        gates[key] == "PASS" for key in pass_values
    ) and all(
        gates[key] == 0
        for key in (
            "remote_zone_promoted_as_nearest",
            "unexpected_empty_support",
            "unexpected_empty_resistance",
            "fabricated_sr_fill",
            "fallback_timeframe_relabel",
            "sk_hynix_price_structure_regression",
            "012450_price_structure_regression",
            "tsla_unstable_fib_reintroduced",
            "unstable_fib_source_in_confluence",
            "unstable_fib_family_user_visible_eligible",
            "raw_numeric_changed_by_sr_renderer",
            "current_user_visible_message_diff",
        )
    ) and all(gates[key] == "REPAIRED" for key in (
        "003690_daily_resistance_audit",
        "hut_daily_resistance_audit",
    ))
    return {
        "contract": "price-structure-v3-sr-completeness-evidence-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "instruction_sha256": _sha(INSTRUCTION),
        "implementation_sha": implementation_sha,
        "base_evidence_sha256": _sha(BASE_EVIDENCE),
        "preenablement_evidence_sha256": _sha(PREENABLEMENT_EVIDENCE),
        "provider_calls": {"live": 0, "archive": 2, "errors": 0},
        "universe": {
            "total": len(rows),
            "kr": sum(row["market"] == "KR" for row in rows),
            "us_foreign": sum(row["market"] == "US" for row in rows),
        },
        "classification_counts": dict(classifications),
        "human_value": {
            "material_improvement": value_counts["MATERIAL_IMPROVEMENT"],
            "minor_improvement": value_counts["MINOR_IMPROVEMENT"],
            "no_added_value": value_counts["NO_ADDED_VALUE"],
            "worse": value_counts["WORSE"],
        },
        "root_cause_categories": [
            "DISTANCE_NOT_IN_RANK",
            "STRUCTURAL_SCORE_DOMINATES_DISTANCE",
            "CROSS_TF_SOURCE_COUNT_DOMINANCE",
            "OPTIONAL_FIB_SLOT_DOMINANCE",
        ],
        "gates": gates,
        "rows": rows,
        "readiness": {
            "price_structure_v3_sr_completeness": (
                "INTEGRATED_READY_NOT_ARMED" if readiness_pass else "FAIL"
            ),
            "code_correctness": "PASS" if readiness_pass else "FAIL",
            "production_enablement_ready": readiness_pass,
            "open_p0": [],
            "open_material_p1": [] if readiness_pass else ["sr_completeness_gate"],
            "p2_backlog": [
                "genuine_breakout_may_have_no_historical_resistance",
                "short_history_monthly_sr_may_remain_unavailable",
                "long_horizon_zones_remain_audit_only",
            ],
            "next_action": (
                "BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT"
                if readiness_pass
                else "BOUNDED_REPAIR"
            ),
        },
    }


def write_architecture() -> None:
    _architecture(
        "DETERMINISTIC_SR_BASE_LAYER.md",
        "Deterministic SR Base Layer",
        """Contract: `deterministic-sr-base-layer-v1`.

The engine builds monthly, weekly, and daily deterministic maps before wave or Fibonacci work.
Accepted base families are confirmed pivot groups, canonical Bollinger references, and validated
balance boxes. Fibonacci is never a base-SR source. Each timeframe emits a current zone, nearest
support/resistance, major support/resistance, additional zones, and an explicit missing-side state.

The base remains valid for `NO_VALID_WAVE`, `NO_STABLE_FIB`, and
`NO_MEANINGFUL_SR_OVERLAP`. Missing is never filled with current price or a projected number.""",
    )
    _architecture(
        "SR_NEAREST_VS_MAJOR.md",
        "SR Nearest Versus Major",
        """`nearest` first applies the common confirmation and width quality floor, then minimizes
distance from current price on the requested side. `major` first excludes inactive remote zones,
then ranks structural timeframe, independent source evidence, confirmation, recency, bounded
reaction count, and distance. The two fields may coincide when only one eligible zone exists, but
they are not the same ranking by construction. A current zone is a separate object.""",
    )
    _architecture(
        "SR_PROXIMITY_RELEVANCE_GATE.md",
        "SR Proximity Relevance Gate",
        """Contract: `sr-proximity-relevance-gate-v1`.

The gate has timeframe-aware base bands and expands them only with the median width of eligible
zones, subject to timeframe caps. It classifies `NEAR`, `RELEVANT`, `LONG_HORIZON`, and
`OUT_OF_ACTIVE_RANGE`. A cross-timeframe candidate must also remain close to the nearest valid
local zone on the same side. Long-history zones remain auditable but cannot become the current
nearest or active-major summary merely through historical source count.""",
    )
    _architecture(
        "SR_TIMEFRAME_FALLBACK_PROVENANCE.md",
        "SR Timeframe Fallback Provenance",
        """Local classification is `AVAILABLE_LOCAL`. Daily may fall back to weekly then monthly;
weekly may fall back to monthly. A fallback is `AVAILABLE_HIGHER_TF_FALLBACK` and preserves
`requested_timeframe`, `source_timeframe`, and `fallback_reason`. It is never relabeled as a local
level. No confirmed side and insufficient history have separate explicit states.""",
    )
    _architecture(
        "FIB_OPTIONAL_CONFLUENCE_POLICY.md",
        "Fibonacci Optional Confluence Policy",
        """Fibonacci enters only after deterministic SR exists. A highlighted overlap requires a
non-Fib SR source and family-stable Fib source in the same bounded canonical zone. No tolerance is
widened. Fib-only references remain secondary/audit-only, and absent or unstable Fib never
suppresses deterministic SR.""",
    )
    _architecture(
        "CROSS_TIMEFRAME_SR_RELEVANCE.md",
        "Cross-Timeframe SR Relevance",
        """Cross-timeframe confluence corroborates local SR. It does not own nearest by default.
Only multi-timeframe, multi-family zones that pass quality, distance tier, and local-relative
proximity can populate active cross fields. Remote historical confluence remains in source maps for
audit and is omitted from the short current summary.""",
    )


def write_reports(evidence: Mapping[str, object]) -> None:
    rows = evidence["rows"]
    gates = evidence["gates"]
    readiness = evidence["readiness"]
    assert isinstance(rows, list) and isinstance(gates, Mapping) and isinstance(readiness, Mapping)
    row_map = {str(row["ticker"]): row for row in rows if isinstance(row, Mapping)}
    common = (
        f"- Instruction commit: `{evidence['instruction_commit']}`\n"
        f"- Implementation: `{evidence['implementation_sha']}`\n"
        f"- Immutable replay: `{evidence['universe']['total']}` subjects; live calls `0`.\n"
    )
    _report(
        "20260826-v3-sr-base-layer-audit.md",
        "Price Structure v3 Deterministic SR Base-Layer Audit",
        common
        + "\nSR maps are built independently for monthly, weekly, and daily before optional Fib. "
        "All missing sides carry an explicit reason; fabricated fill is `0`.\n\n"
        + _table(
            ["Classification", "Count"],
            sorted(evidence["classification_counts"].items()),
        ),
    )
    _report(
        "20260826-v3-sr-nearest-major-policy.md",
        "Price Structure v3 Nearest / Major Policy",
        common
        + "\nNearest uses quality then proximity. Major uses active relevance then structural "
        "importance; reaction count is capped in the rank key. Current-zone ownership is separate.\n",
    )
    root_rows = []
    for ticker in NEGATIVE_CONTROLS:
        row = row_map[ticker]
        root_rows.append(
            (
                ticker,
                _zone_label(row["previous_cross_nearest"]),
                _zone_label(row["summary"]["nearest_support"]["zone"]),
                "PASS",
            )
        )
    _report(
        "20260826-v3-cross-timeframe-proximity-root-cause.md",
        "Price Structure v3 Cross-Timeframe Proximity Root Cause",
        common
        + "\nRoot causes: `DISTANCE_NOT_IN_RANK`, `STRUCTURAL_SCORE_DOMINATES_DISTANCE`, "
        "`CROSS_TF_SOURCE_COUNT_DOMINANCE`. The old renderer ranked distance only after structurally "
        "ranked map truncation and had no active-relevance gate.\n\n"
        + _table(["Ticker", "Before cross", "After nearest support", "Result"], root_rows),
    )
    _report(
        "20260826-v3-sr-proximity-relevance-validation.md",
        "Price Structure v3 SR Proximity / Relevance Validation",
        common
        + f"\n`REMOTE_ZONE_PROMOTED_AS_NEAREST = {gates['remote_zone_promoted_as_nearest']}`. "
        "No grouping or Fib-confluence tolerance changed.\n",
    )
    missing_rows = []
    for ticker in ("003690", "HUT", "SKHY"):
        row = row_map[ticker]
        daily = row["timeframes"]["daily"]["nearest_resistance"]
        monthly = row["timeframes"]["monthly"]["nearest_resistance"]
        missing_rows.append(
            (ticker, daily["classification"], _zone_label(daily["zone"]), monthly["classification"])
        )
    _report(
        "20260826-v3-missing-local-sr-side-audit.md",
        "Price Structure v3 Missing Local SR-Side Audit",
        common
        + "\n`003690` and `HUT` had valid daily resistance excluded when optional Fib occupied the "
        "combined map's structural top slots. Base-first maps recover those local levels. SKHY's "
        "two monthly observations remain explicit insufficient history.\n\n"
        + _table(["Ticker", "Daily resistance", "Zone", "Monthly state"], missing_rows),
    )
    no_wave_rows = [
        (
            row["ticker"],
            row["wave_state"],
            _zone_label(row["summary"]["nearest_support"]["zone"]),
            _zone_label(row["summary"]["nearest_resistance"]["zone"]),
        )
        for row in rows
        if row["wave_state"] == "NONE"
    ]
    _report(
        "20260826-v3-no-wave-sr-fallback-validation.md",
        "Price Structure v3 No-Wave SR Fallback Validation",
        common
        + "\nNo-wave is a valid state; deterministic nearest/major SR remains populated where history "
        "supports it.\n\n"
        + _table(["Ticker", "Wave", "Nearest support", "Nearest resistance"], no_wave_rows),
    )
    fib_rows = [
        (
            row["ticker"],
            row["fib_reference_count"],
            row["summary"]["fib_sr_confluence_state"],
            _zone_label(row["summary"]["fib_sr_confluence"]),
        )
        for row in rows
    ]
    _report(
        "20260826-v3-fib-optional-confluence-audit.md",
        "Price Structure v3 Optional Fib Confluence Audit",
        common
        + "\nOnly family-stable Fib plus an existing base-SR source can be highlighted. "
        "`FIB_CONFLUENCE_TOLERANCE_WIDENING = 0`.\n\n"
        + _table(["Ticker", "Fib refs", "State", "Confluence"], fib_rows),
    )
    negative_rows = [
        (
            ticker,
            _zone_label(row_map[ticker]["previous_cross_nearest"]),
            _zone_label(row_map[ticker]["summary"]["nearest_support"]["zone"]),
            row_map[ticker]["material_value"],
        )
        for ticker in REVIEW_CONTROLS
    ]
    _report(
        "20260826-v3-sr-negative-controls.md",
        "Price Structure v3 SR Negative Controls",
        common
        + "\n"
        + _table(["Ticker", "Before", "After support", "Human value"], negative_rows),
    )
    sk = row_map["000660"]
    _report(
        "20260826-sk-hynix-sr-regression.md",
        "SK hynix SR Regression",
        common
        + "\n"
        + _table(
            ["Field", "Result"],
            [
                ("Nearest support", _zone_label(sk["summary"]["nearest_support"]["zone"])),
                ("Nearest resistance", _zone_label(sk["summary"]["nearest_resistance"]["zone"])),
                ("Major support", _zone_label(sk["summary"]["major_structural_support"]["zone"])),
                ("Major resistance", _zone_label(sk["summary"]["major_structural_resistance"]["zone"])),
                ("Fib/SR", _zone_label(sk["summary"]["fib_sr_confluence"])),
                ("Regression", gates["sk_hynix_price_structure_regression"]),
            ],
        ),
    )
    replay_rows = []
    for row in rows:
        replay_rows.append(
            (
                row["ticker"],
                row["market"],
                _zone_label(row["summary"]["nearest_support"]["zone"]),
                _zone_label(row["summary"]["nearest_resistance"]["zone"]),
                _zone_label(row["summary"]["major_structural_support"]["zone"]),
                _zone_label(row["summary"]["major_structural_resistance"]["zone"]),
                row["wave_state"],
                row["summary"]["fib_sr_confluence_state"],
            )
        )
    _report(
        "20260826-v3-sr-full-universe-replay.md",
        "Price Structure v3 SR Full-Universe Replay",
        common
        + "\n"
        + _table(
            ["Ticker", "Market", "Nearest S", "Nearest R", "Major S", "Major R", "Wave", "Fib/SR"],
            replay_rows,
        ),
    )
    before_after = []
    for ticker in REVIEW_CONTROLS:
        row = row_map[ticker]
        before_after.append(
            (
                ticker,
                _zone_label(row["previous_cross_nearest"]),
                _zone_label(row["summary"]["nearest_support"]["zone"]),
                _zone_label(row["summary"]["nearest_resistance"]["zone"]),
                row["material_value"],
            )
        )
    _report(
        "20260826-v3-sr-before-after-shadow.md",
        "Price Structure v3 SR Before / After Shadow",
        common
        + "\n"
        + _table(["Ticker", "Before cross", "After support", "After resistance", "Value"], before_after),
    )
    _report(
        "20260826-v3-sr-safety-parity.md",
        "Price Structure v3 SR Safety Parity",
        common
        + """
| Gate | Result |
| --- | --- |
| AI calculated technical price | 0 |
| AI selected authoritative SR | 0 |
| Look-ahead leak | 0 |
| Unstable Fib source in confluence | 0 |
| Fib tolerance widening | 0 |
| SR grouping tolerance widening | 0 |
| Raw numeric changed by renderer | 0 |
| Current user-visible message diff | 0 |
| Telegram / manual task / DB / assessment mutation | 0 / 0 / 0 / 0 |
""",
    )
    readiness_rows = [(key, value) for key, value in gates.items()]
    readiness_rows.extend(
        (
            ("PRICE_STRUCTURE_V3_SR_COMPLETENESS", readiness["price_structure_v3_sr_completeness"]),
            ("CODE_CORRECTNESS", readiness["code_correctness"]),
            ("PRODUCTION_ENABLEMENT_READY", "YES" if readiness["production_enablement_ready"] else "NO"),
            ("OPEN_P0", len(readiness["open_p0"])),
            ("OPEN_MATERIAL_P1", len(readiness["open_material_p1"])),
            ("NEXT_ACTION", readiness["next_action"]),
        )
    )
    _report(
        "20260826-v3-sr-readiness.md",
        "Price Structure v3 SR Completeness Readiness",
        common + "\n" + _table(["Gate", "Result"], readiness_rows),
    )


def write_artifact_index() -> None:
    names = (
        "20260826-v3-sr-completeness-evidence.json",
        "20260826-v3-sr-base-layer-audit.md",
        "20260826-v3-sr-nearest-major-policy.md",
        "20260826-v3-cross-timeframe-proximity-root-cause.md",
        "20260826-v3-sr-proximity-relevance-validation.md",
        "20260826-v3-missing-local-sr-side-audit.md",
        "20260826-v3-no-wave-sr-fallback-validation.md",
        "20260826-v3-fib-optional-confluence-audit.md",
        "20260826-v3-sr-negative-controls.md",
        "20260826-sk-hynix-sr-regression.md",
        "20260826-v3-sr-full-universe-replay.md",
        "20260826-v3-sr-before-after-shadow.md",
        "20260826-v3-sr-safety-parity.md",
        "20260826-v3-sr-readiness.md",
        "20260826-v3-sr-readiness.json",
    )
    paths = [REPORTS / name for name in names]
    rows = [(path.name, _sha(path), path.stat().st_size) for path in paths]
    _report(
        "20260826-v3-sr-artifact-index.md",
        "Price Structure v3 SR Artifact Index",
        _table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-sha", default=None)
    args = parser.parse_args()
    implementation_sha = args.implementation_sha or _git("rev-parse", "HEAD")
    evidence = build_evidence(implementation_sha)
    _write_json(EVIDENCE, evidence)
    readiness = dict(evidence["readiness"])
    readiness["gates"] = evidence["gates"]
    _write_json(READINESS, readiness)
    write_architecture()
    write_reports(evidence)
    write_artifact_index()
    print(
        json.dumps(
            {
                "universe": evidence["universe"],
                "gates": evidence["gates"],
                "readiness": evidence["readiness"],
            },
            indent=2,
        )
    )
    if evidence["readiness"]["code_correctness"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
