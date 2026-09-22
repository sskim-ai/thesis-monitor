from copy import deepcopy
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.services.krx_night_history_service import build_same_contract_timeframes, store_normalized_bar
from app.services.night_futures import NIGHT_COMPARISON_SEMANTIC
from app.services.night_futures_visibility_service import night_futures_user_facing_visibility
from app.services.official_night_market_eligibility_service import ENDPOINT, night_market_eligibility
from app.services.night_futures_session_mapping_service import US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT
from scripts import m12ds_r4_r1_market
from tests.test_krx_night_history_service import _bar


def row():
    bar = _bar(date(2026, 9, 21), contract="FUTURE", maturity="2026-12")
    with TemporaryDirectory() as folder:
        root = Path(folder)
        store_normalized_bar(root, bar)
        frames = build_same_contract_timeframes(root, instrument_root="KOSPI200", reference_date=date(2026, 9, 21),
            daily_baseline_date=date(2026, 9, 18), daily_baseline_close=100)
    return dict(source=ENDPOINT, exchange="XKRX", session_date="2026-09-21", reference_date="2026-09-18",
        reference_date_contract=US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT, session_type="NIGHT",
        reference_session="DAY", finality_valid=True, reference_date_match=True,
        expected_reference_date="2026-09-21", provider_raw_bas_dd="2026-09-21",
        comparison_semantic=NIGHT_COMPARISON_SEMANTIC, fact_id="market:night_futures:1",
        series_code="KRX_KOSPI200_NIGHT_FUT", state="CURRENT_DIRECTIONAL", contract_code="FUTURE",
        night_source_record_id="2026-09-21:NIGHT:FUTURE", reference_source_record_id="2026-09-18:REGULAR:FUTURE",
        night_source_payload_sha256="a"*64, reference_source_payload_sha256="b"*64,
        contract_maturity="2026-12", value=101, reference_price=100, change_value=1, change_pct=1,
        night_timeframes=frames.model_dump(mode="json"))


def gate(value, market="us", assessed="2026-09-22"):
    return night_market_eligibility(value, market=market, assessment_date=assessed, completed_session_date="2026-09-21")


def test_typed_final_pair_eligible_only_for_next_kr_context_in_us_recap():
    result = gate(row())
    assert result["eligible"], result
    assert result["consumer_scopes"] == ["MARKET_AI", "US_MARKET_RENDER"]
    assert not gate(row(), market="kr")["eligible"]
    assert not gate(row(), assessed="2026-09-23")["eligible"]


@pytest.mark.parametrize("key,value", [
    ("source", "https://untrusted.example"), ("finality_valid", False),
    ("contract_maturity", "2026-09"), ("reference_date", "2026-09-17"),
    ("reference_date_contract", "legacy-night-reference-date-contract"),
    ("provider_raw_bas_dd", "2026-09-22"), ("reference_price", 99),
    ("night_source_payload_sha256", "wrong"), ("reference_source_record_id", "another"),
    ("change_pct", 2), ("night_timeframes", None), ("state", "UNAVAILABLE"),
])
def test_failed_source_timing_identity_and_arithmetic_do_not_cross_adapter(key, value):
    source = row()
    source[key] = value
    assert not gate(source)["eligible"]


def test_no_generic_current_directional_intake_relaxation():
    source = row()
    packet = {"market": "us", "assessment_date": "2026-09-22", "market_context": {
        "session": {"assessment_date": "2026-09-22", "latest_completed_regular_session_date": "2026-09-21"},
        "night_futures": [source], "fact_catalog": [
            {"fact_id": source["fact_id"], "fact_type": "night_futures", "as_of_date": "2026-09-21",
             "fields": {k: v for k, v in source.items() if k != "night_timeframes"}},
            {"fact_id": "arbitrary", "fact_type": "macro", "as_of_date": "2026-09-21",
             "fields": {"state": "CURRENT_DIRECTIONAL"}},
        ]}}
    context = m12ds_r4_r1_market.market_context(packet)
    assert context["parity_status"] == "PASS"
    assert set(context["facts"]) == {source["fact_id"]}
    assert night_futures_user_facing_visibility("us", context=packet["market_context"]).visible
    bad = deepcopy(packet)
    bad["market_context"]["night_futures"][0]["value"] = 102
    assert not m12ds_r4_r1_market.market_context(bad)["facts"]
