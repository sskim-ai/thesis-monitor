import csv
import io
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.services import broker_night_seed_history as history

AT = datetime(2026, 11, 11, 6, tzinfo=timezone.utc)
SEED = Path(__file__).parent/"fixtures/c22w_broker_night_seed.csv"


def seed():return SEED.read_bytes()


def changed(field, value, index=0):
    rows = list(csv.DictReader(io.StringIO(seed().decode("utf-8-sig"))))
    rows[index][field] = value
    out = io.StringIO();writer = csv.DictWriter(out, fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    return out.getvalue().encode()


def test_57_provenance_and_timeframe_counts():
    bars = history.parse_seed(seed(), available_at=AT)
    assert {tf:sum(b["timeframe"]==tf for b in bars) for tf in history.TIMEFRAMES} == {"DAILY":34,"WEEKLY":18,"MONTHLY":5}
    assert len({history.key(b) for b in bars}) == len({b["screenshot_sha256"] for b in bars}) == 57
    assert all(b["source_kind"] == "USER_BROKER_SCREENSHOT" and not b["official_source_authority"] for b in bars)
    assert all(b["input_csv_sha256"] == history.sha(seed()) for b in bars)


def test_calendar_three_dates_and_no_wm_inference():
    bars = history.parse_seed(seed(), available_at=AT)
    friday = next(b for b in bars if b["timeframe"] == "DAILY" and b["broker_chart_date"] == "2026-11-06")
    assert friday["calendar_night_end_date"] == "2026-11-07"
    assert friday["krx_trade_date_inferred_not_official"] == "2026-11-09"
    assert all(b["calendar_night_end_date"] is None and b["krx_trade_date_inferred_not_official"] is None for b in bars if b["timeframe"] != "DAILY")
    with pytest.raises(ValueError, match="three_dates"):history.parse_seed(changed("calendar_night_end_date", "2026-09-19"), available_at=AT)


def test_direct_period_returns_and_progress():
    bars = history.parse_seed(seed(), available_at=AT)
    doc = history.render_broker_history(dict(contract=history.CONTRACT,bars=bars),instrument_root="KOSPI200",contract_maturity="2026-12",cutoff=AT)
    assert all(x in doc["text"] for x in ("-2.77%", "+0.31%", "-8.60%"))
    assert [b["chart_status"] for b in doc["selected"]] == ["CHART_BAR_DISPLAYED","IN_PROGRESS","IN_PROGRESS"]
    with pytest.raises(ValueError, match="return_formula"):history.parse_seed(changed("previous_same_timeframe_night_close", "100", index=1), available_at=AT)


def test_message_chart_dates_only_audit_dates_retained():
    bars = history.parse_seed(seed(), available_at=AT)
    doc = history.render_broker_history(dict(contract=history.CONTRACT,bars=bars),instrument_root="KOSPI200",contract_maturity="2026-12",cutoff=AT)
    assert all(x in doc["text"] for x in ("2026-11-10", "2026-11-09", "2026-11-02"))
    assert all(x not in doc["text"] for x in ("2026-11-11", "BAS_DD", "KRX 거래일", "종료일"))
    assert doc["selected"][0]["krx_trade_date_inferred_not_official"] == "2026-11-11"


def test_atomic_commit_exact_reimport_and_no_availability_reset(tmp_path):
    path = tmp_path/"broker-seed-v1/history.json"
    first = history.commit_seed(history_path=path,raw=seed(),available_at=AT);before = path.read_bytes()
    second = history.commit_seed(history_path=path,raw=seed(),available_at=AT+timedelta(days=1))
    assert first["inserted"] == 57 and first["before_count"] == 0 and first["after_count"] == 57
    assert second["status"] == "NOOP" and second["unchanged"] == 57 and path.read_bytes() == before
    assert first["rollback"]["existed"] is False
    rows = list(csv.DictReader(io.StringIO(seed().decode("utf-8-sig"))))
    new = dict(rows[0],contract_maturity="2027-03");rows.append(new)
    out = io.StringIO();writer = csv.DictWriter(out,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    incremental = history.commit_seed(history_path=path,raw=out.getvalue().encode(),available_at=AT+timedelta(days=2))
    assert incremental["inserted"] == 1 and incremental["unchanged"] == 57 and incremental["after_count"] == 58
    assert incremental["rollback"]["previous_snapshot"]


def test_conflict_quarantine_leaves_entire_history_unchanged(tmp_path):
    path = tmp_path/"broker-seed-v1/history.json"
    history.commit_seed(history_path=path,raw=seed(),available_at=AT);before = path.read_bytes()
    result = history.commit_seed(history_path=path,raw=changed("screenshot_sha256", "f"*64),available_at=AT)
    assert result["status"] == "QUARANTINED_NO_HISTORY_CHANGE" and result["inserted"] == 0
    assert path.read_bytes() == before and Path(result["quarantine"]).exists()


def test_pit_no_backdate_and_empty_optional_panel(tmp_path):
    path = tmp_path/"history.json";history.commit_seed(history_path=path,raw=seed(),available_at=AT)
    stored = history.load_history(path)
    doc = history.render_broker_history(stored,instrument_root="KOSPI200",contract_maturity="2026-12",cutoff=AT-timedelta(seconds=1))
    assert len(doc["selected"]) == 0 and doc["text"].count("자료 부족") == 3
    assert all(b["historical_availability_at_original_session"] == "UNKNOWN" for b in stored["bars"])
    assert doc["NO_SEND"] and not doc["full_market_parent"]


def test_official_lane_untouched_and_no_kosdaq_or_maturity_spill(tmp_path):
    official = tmp_path/"daily/official.json";official.parent.mkdir();official.write_bytes(b"official-source")
    path = tmp_path/"broker-seed-v1/history.json";history.commit_seed(history_path=path,raw=seed(),available_at=AT)
    assert official.read_bytes() == b"official-source"
    stored = history.load_history(path)
    assert {(b["instrument_root"], b["contract_maturity"]) for b in stored["bars"]} == {("KOSPI200","2026-12")}
    assert not history.render_broker_history(stored,instrument_root="KOSDAQ150",contract_maturity="2026-12",cutoff=AT)["selected"]


def test_bad_ohlcv_or_source_hash_never_creates_store(tmp_path):
    path = tmp_path/"history.json"
    for field, value in (("high","1"),("screenshot_sha256","bad"),("volume","NaN")):
        with pytest.raises(ValueError):history.commit_seed(history_path=path,raw=changed(field,value),available_at=AT)
    assert not path.exists()


def test_failed_replace_keeps_previous_committed_file(tmp_path, monkeypatch):
    path = tmp_path/"history.json";history.commit_seed(history_path=path,raw=seed(),available_at=AT);before = path.read_bytes()
    real_replace = history.os.replace
    def deny_only_history(source, destination):
        if Path(destination) == path:raise OSError("simulated pre-commit interruption")
        return real_replace(source,destination)
    monkeypatch.setattr(history.os,"replace",deny_only_history)
    # A different, valid logical instrument appends rather than overwriting rows.
    raw = seed().replace(b"KOSPI200,2026-12",b"KOSPI200,2027-03")
    with pytest.raises(OSError):history.commit_seed(history_path=path,raw=raw,available_at=AT)
    assert path.read_bytes() == before
