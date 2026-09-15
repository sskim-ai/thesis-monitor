from __future__ import annotations

from scripts import fictional_aggregate_context_boundary_m12bc as program


def _row(
    ticker: str,
    repetition: int,
    *,
    direction: str = "HOLD",
    business_delta: str = "UNCHANGED",
    buyer: str = "WAIT",
    holder: str = "REVIEW",
    buy: float = 5.0,
    sell: float = 5.0,
) -> dict[str, object]:
    return {
        "ticker": ticker,
        "repetition": repetition,
        "core": {
            "overall_direction": direction,
            "business_thesis_change": business_delta,
            "fundamental_new_buyer": {"stance": buyer},
            "fundamental_holder": {"stance": holder},
            "directional_balance": {"buy": buy, "sell": sell},
            "hold_lean": None,
            "directional_confidence": "MEDIUM",
        },
    }


def test_report_slugs_are_unique_and_complete() -> None:
    assert len(program.REPORT_SLUGS) == len(set(program.REPORT_SLUGS))
    assert program.REPORT_SLUGS[0] == "m12bb-frozen-generation-provenance"
    assert program.REPORT_SLUGS[-1] == "program-completion"


def test_frozen_diagnostic_variance_is_measured_not_blocking() -> None:
    rows = []
    tickers = [f"FIC-FIN-{number:02d}" for number in range(1, 9)]
    for repetition in range(1, 4):
        for ticker in tickers:
            if ticker == "FIC-FIN-01":
                rows.append(
                    _row(
                        ticker,
                        repetition,
                        direction="BUY",
                        business_delta="STRENGTHENED",
                        holder="HOLDABLE",
                        buy=6.0 if repetition == 1 else 6.5,
                        sell=4.0 if repetition == 1 else 3.5,
                    )
                )
            elif ticker == "FIC-FIN-05":
                rows.append(
                    _row(
                        ticker,
                        repetition,
                        direction="SELL" if repetition == 1 else "HOLD",
                        buyer="AVOID" if repetition == 1 else "WAIT",
                        buy=4.0 if repetition == 1 else 4.5,
                        sell=6.0 if repetition == 1 else 5.5,
                    )
                )
            else:
                rows.append(_row(ticker, repetition))
    result = program._diagnostics(rows)
    assert result["status"] == "MEASURED"
    assert result["readiness_blocking"] is False
    assert result["primary_direction_unstable_subject_count"] == 1
    assert result["business_delta_unstable_subject_count"] == 0
    assert result["new_buyer_unstable_subject_count"] == 1
    assert result["holder_unstable_subject_count"] == 0
    assert result["same_direction_calibration_variance_subject_count"] == 2
    assert result["fic_fin_05_direction_values"] == ["SELL", "HOLD", "HOLD"]
    assert result["fic_fin_05_new_buyer_values"] == ["AVOID", "WAIT", "WAIT"]
    assert result["fic_fin_05_holder_values"] == ["REVIEW", "REVIEW", "REVIEW"]


def test_model_facing_ast_surfaces_unchanged_from_m12bb_base() -> None:
    result = program._semantic_surface_audit()
    assert result["status"] == "PASS"
    assert result["semantic_change_count"] == 0


def test_completion_value_uses_first_present_alias() -> None:
    assert program._completion_value({"legacy": 4}, "current", "legacy") == 4
    assert program._completion_value({}, "missing", default="NOT_MEASURED") == (
        "NOT_MEASURED"
    )
