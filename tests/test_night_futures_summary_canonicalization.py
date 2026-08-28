from __future__ import annotations

from app.services.night_futures import (
    NIGHT_COMPARISON_SEMANTIC,
    NIGHT_FUTURES_SESSION_BASIS_CONTRACT,
    canonicalize_night_futures_market_summary,
    night_futures_context_row,
    summarize_night_futures,
)


def _row(
    series_code: str,
    *,
    session: str = "2026-08-27",
    expected: str = "2026-08-27",
) -> dict[str, object]:
    is_kospi = "KOSPI200" in series_code
    current = 1080.35 if is_kospi else 1417.8
    reference = 1073.5 if is_kospi else 1425.1
    change = current - reference
    contract = "A0169000" if is_kospi else "A0669000"
    return {
        "series_code": series_code,
        "category": "kr_night_futures",
        "value": current,
        "change_value": change,
        "change_pct": change / reference * 100,
        "quality_status": "fresh" if session == expected else "stale",
        "session_freshness": "fresh" if session == expected else "stale",
        "expected_latest_session_date": expected,
        "session_date": session,
        "trade_date": session,
        "contract_code": contract,
        "exchange": "XKRX",
        "market_session": "kr_night",
        "session_type": "NIGHT",
        "reference_session": "DAY",
        "reference_date": "2026-08-26",
        "reference_price": reference,
        "current_session_price": current,
        "comparison_semantic": NIGHT_COMPARISON_SEMANTIC,
        "retrieved_at": f"{session}T06:01:00+09:00",
        "source_url": "https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd",
        "session_basis_contract": NIGHT_FUTURES_SESSION_BASIS_CONTRACT,
        "night_source_record_id": f"{session}:NIGHT:{contract}",
        "reference_source_record_id": f"2026-08-26:DAY:{contract}",
        "night_source_payload_sha256": "a" * 64,
        "reference_source_payload_sha256": "b" * 64,
    }


def test_stale_raw_summary_numbers_cannot_bypass_empty_canonical_gate() -> None:
    market = {
        "items": [
            "S&P +0.7%",
            "KOSPI200 야간선물 +1.2%",
            "KOSDAQ150 야간선물 +0.8%",
        ],
        "observations": [
            _row(
                "KRX_KOSPI200_NIGHT_FUT",
                session="2026-08-27",
                expected="2026-08-28",
            ),
            _row(
                "KRX_KOSDAQ150_NIGHT_FUT",
                session="2026-08-27",
                expected="2026-08-28",
            ),
        ],
        "night_futures_gate": {
            "query_attempted": True,
            "expected_session": "2026-08-28",
            "ready_products": [],
            "state": "deadline_reached",
        },
    }

    canonical = canonicalize_night_futures_market_summary(market)

    assert canonical["items"] == ["S&P +0.7%"]
    assert summarize_night_futures(canonical).items == []


def test_summary_projection_matches_canonical_fact_value_session_and_state() -> None:
    rows = [
        _row("KRX_KOSPI200_NIGHT_FUT"),
        _row("KRX_KOSDAQ150_NIGHT_FUT"),
    ]
    market = {
        "items": ["S&P +0.7%", "KOSPI200 야간선물 +9.9%"],
        "observations": rows,
        "night_futures_gate": {
            "query_attempted": True,
            "expected_session": "2026-08-27",
            "ready_products": [row["series_code"] for row in rows],
            "state": "ready",
        },
    }

    canonical = canonicalize_night_futures_market_summary(market)
    projected = [item for item in canonical["items"] if isinstance(item, dict)]
    summary = summarize_night_futures(canonical)

    assert len(projected) == len(summary.items) == 2
    assert [item["fact_id"] for item in projected] == [
        "market:night_futures:1",
        "market:night_futures:2",
    ]
    assert [item["field_path"] for item in projected] == [
        "fields.change_pct",
        "fields.change_pct",
    ]
    assert [item["value"] for item in projected] == [
        item.change_pct for item in summary.items
    ]
    assert {item["session"] for item in projected} == {"2026-08-27"}
    assert {item["state"] for item in projected} == {"CURRENT_DIRECTIONAL"}


def test_partial_kosdaq_availability_preserves_fact_identity_two() -> None:
    row = _row("KRX_KOSDAQ150_NIGHT_FUT")
    market = {
        "observations": [row],
        "night_futures_gate": {
            "query_attempted": True,
            "expected_session": "2026-08-27",
            "ready_products": ["KRX_KOSDAQ150_NIGHT_FUT"],
            "state": "deadline_reached",
        },
    }

    summary = summarize_night_futures(market)
    context = night_futures_context_row(summary.items[0])

    assert context["fact_id"] == "market:night_futures:2"
    assert context["field_path"] == "fields.change_pct"
    assert context["state"] == "CURRENT_DIRECTIONAL"
