"""Typed official final-night context. Never a generic market-row override."""

from datetime import date
from math import isclose, isfinite
import re

from app.services.market_session import preceding_exchange_session_date
from app.services.night_futures import (
    NIGHT_COMPARISON_SEMANTIC, NIGHT_FUTURES_FACT_IDS, _validated_timeframes,
)
from app.services.night_futures_session_mapping_service import US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT


CONTRACT = "official-krx-night-market-consumption-v1"
ENDPOINT = "https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd"


def night_catalog_matches(fact, row):
    """Native packet embeds DWM; the historical split layout stores it beside fields."""
    fields = fact.get('fields')
    if not isinstance(fields, dict):
        return False
    expected = row if 'night_timeframes' in fields else {k:v for k,v in row.items() if k!='night_timeframes'}
    # Match the actual packet producer's projection, including omitted empty fields.
    from app.services.ai_review_service import _public_value
    return fields in (expected, _public_value(expected)) and fact.get('fact_id') == row.get('fact_id')


def night_market_eligibility(row, *, market, assessment_date, completed_session_date):
    errors = []
    try:
        assessed = date.fromisoformat(str(assessment_date))
        completed = date.fromisoformat(str(completed_session_date))
        session = date.fromisoformat(str(row["session_date"]))
        reference = date.fromisoformat(str(row["reference_date"]))
        expected = preceding_exchange_session_date("XKRX", assessed)
        if market != "us" or completed >= assessed or session != expected:
            errors.append("night_target_session_unresolved")
        if (row.get("source") != ENDPOINT or row.get("exchange") != "XKRX"
                or row.get("reference_date_contract") != US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT
                or row.get("session_type") != "NIGHT" or row.get("reference_session") != "DAY"
                or row.get("finality_valid") is not True or row.get("reference_date_match") is not True
                or str(row.get("expected_reference_date")) != str(expected)
                or str(row.get("provider_raw_bas_dd")) != str(session)
                or row.get("comparison_semantic") != NIGHT_COMPARISON_SEMANTIC
                or reference != preceding_exchange_session_date("XKRX", session)
                or row.get("fact_id") != NIGHT_FUTURES_FACT_IDS.get(row.get("series_code"))
                or row.get("state") != "CURRENT_DIRECTIONAL"):
            errors.append("night_official_identity_or_finality_unverified")
        code = row["contract_code"]
        if (row.get("night_source_record_id") != f"{session}:NIGHT:{code}"
                or row.get("reference_source_record_id") != f"{reference}:REGULAR:{code}"
                or any(not re.fullmatch(r"[0-9a-f]{64}", str(row.get(k, ""))) for k in (
                    "night_source_payload_sha256", "reference_source_payload_sha256"))):
            errors.append("night_raw_identity_unverified")
        price, baseline, delta, pct = [row[k] for k in ("value", "reference_price", "change_value", "change_pct")]
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
                for v in (price, baseline, delta, pct)) or baseline <= 0
                or not isclose(price - baseline, delta, abs_tol=1e-8)
                or not isclose(delta / baseline * 100, pct, abs_tol=1e-6)):
            errors.append("night_reference_arithmetic_invalid")
        frames = _validated_timeframes(row.get("night_timeframes"), series_code=row["series_code"],
                                       contract_code=code, session_date=session, close=price)
        if frames is None:
            errors.append("night_typed_timeframes_missing_or_invalid")
        else:
            daily = frames.daily
            if (frames.contract_maturity != row.get("contract_maturity")
                    or any(f.contract_maturity != frames.contract_maturity for f in (daily, frames.weekly, frames.monthly))
                    or daily.status != "FINAL" or daily.quality != "VALID"
                    or daily.return_baseline_date != reference or daily.return_baseline_close != baseline
                    or daily.return_baseline_semantic != NIGHT_COMPARISON_SEMANTIC
                    or daily.return_pct is None or not isclose(daily.return_pct, pct, abs_tol=1e-6)
                    or row["night_source_payload_sha256"] not in daily.source_raw_sha256):
                errors.append("night_typed_baseline_or_quality_mismatch")
    except (KeyError, TypeError, ValueError, OverflowError):
        errors.append("night_typed_input_invalid")
    return {"contract": CONTRACT, "eligible": not errors, "errors": sorted(set(errors)),
            "structured_state": "UNAVAILABLE" if errors else "CURRENT_DIRECTIONAL",
            "today_signal_eligible": not errors, "target_market": market,
            "target_scope": "NEXT_KR_REGULAR_CONTEXT_IN_US_RECAP" if not errors else None,
            "consumer_scopes": ["MARKET_AI", "US_MARKET_RENDER"] if not errors else []}
