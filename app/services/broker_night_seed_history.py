"""Attributed broker-chart history, separate from official KRX bar storage."""
from __future__ import annotations

import csv
import fcntl
import hashlib
import io
import json
import os
import re
import tempfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.services.market_session import is_exchange_session_date
from app.services.night_futures_session_mapping_service import (
    KST, NIGHT_SESSION_COMPLETION_TIME, map_latest_completed_krx_night_session,
)

CONTRACT = "broker-night-seed-history-v1"
SOURCE = "USER_BROKER_SCREENSHOT"
COMPARISON = "NIGHT_SAME_CONTRACT_PREVIOUS_TIMEFRAME_CLOSE_NOT_REGULAR_DAY"
TIMEFRAMES = ("DAILY", "WEEKLY", "MONTHLY")
REVISION_CONTRACT = "broker-night-snapshot-revision-v1"


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _number(value):
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("broker_seed_invalid_number") from None
    if not result.is_finite():
        raise ValueError("broker_seed_nonfinite_number")
    return result


def _aware(at):
    if at.utcoffset() is None:
        raise ValueError("broker_seed_aware_cutoff_required")
    return at.astimezone(timezone.utc)


def _next_session(chart_date):
    for offset in range(1, 15):
        candidate = chart_date + timedelta(days=offset)
        if is_exchange_session_date("XKRX", candidate):
            return candidate
    raise ValueError("broker_seed_calendar_unavailable")


def key(bar):
    return (bar["instrument_root"], bar["contract_maturity"], bar["timeframe"],
            bar["broker_chart_date"], bar["source_kind"])


def source_content(bar):
    # An enlarged import file changes its whole-file hash, not an old chart row.
    return {k: v for k, v in bar.items() if k not in {"first_system_available_at", "input_csv_sha256"}}


def parse_seed(raw, *, available_at):
    at = _aware(available_at)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    result, seen = [], set()
    for row in rows:
        timeframe = row["timeframe"]
        if timeframe not in TIMEFRAMES or row["source_kind"] != "USER_BROKER_SCREENSHOT_MANUAL_TRANSCRIPTION":
            raise ValueError("broker_seed_source_or_timeframe")
        if row["comparison_semantic"] != COMPARISON:
            raise ValueError("broker_seed_comparison_semantic")
        if not re.fullmatch(r"\d{4}-\d{2}", row["contract_maturity"]):
            raise ValueError("broker_seed_maturity")
        if not row["instrument_root"] or row["chart_status"] not in ("IN_PROGRESS", "CHART_BAR_DISPLAYED"):
            raise ValueError("broker_seed_identity_or_finality")
        for field in ("screenshot_sha256", "source_zip_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", row[field]):
                raise ValueError("broker_seed_provenance_hash")
        chart = date.fromisoformat(row["broker_chart_date"])
        end = row["calendar_night_end_date"] or None
        trade = row["krx_trade_date_inferred_not_official"] or None
        if timeframe == "DAILY":
            if end != str(chart + timedelta(days=1)) or trade != str(_next_session(chart)):
                raise ValueError("broker_seed_three_dates_mismatch")
        elif end or trade:
            raise ValueError("broker_seed_period_date_inference_forbidden")
        values = {k: _number(row[k]) for k in ("open", "high", "low", "close", "volume")}
        if (any(values[k] <= 0 for k in ("open", "high", "low", "close"))
                or not values["low"] <= min(values["open"], values["close"]) <= max(values["open"], values["close"]) <= values["high"]
                or values["volume"] < 0 or values["volume"] != values["volume"].to_integral_value()):
            raise ValueError("broker_seed_invalid_ohlcv")
        previous = row["previous_same_timeframe_night_close"] or None
        reported = row["pct_vs_previous_same_timeframe_night_close"] or None
        if bool(previous) != bool(reported):
            raise ValueError("broker_seed_incomplete_comparison")
        if previous:
            baseline = _number(previous)
            if baseline <= 0 or abs((values["close"] / baseline - 1) * 100 - _number(reported)) > Decimal("0.0001"):
                raise ValueError("broker_seed_return_formula")
        bar = dict(instrument_root=row["instrument_root"], contract_maturity=row["contract_maturity"],
            timeframe=timeframe, broker_chart_date=str(chart), calendar_night_end_date=end,
            krx_trade_date_inferred_not_official=trade, source_kind=SOURCE,
            original_source_kind=row["source_kind"], screenshot_file=row["screenshot_file"],
            screenshot_sha256=row["screenshot_sha256"], source_zip_sha256=row["source_zip_sha256"],
            input_csv_sha256=sha(raw), input_row_sha256=sha(encoded(row)),
            contract_code_crossmatched_only=row["contract_code_crossmatched_only"],
            **{k: str(v) for k, v in values.items()}, volume_unit="CONTRACTS", price_unit="INDEX_POINTS",
            previous_same_timeframe_night_close=previous,
            pct_vs_previous_same_timeframe_night_close=reported, comparison_semantic=COMPARISON,
            chart_status=row["chart_status"], historical_availability_at_original_session="UNKNOWN",
            original_historical_availability=row["historical_availability_at_original_session"],
            first_system_available_at=at.isoformat(), official_source_authority=False,
            source_capability=row["source_capability"])
        if key(bar) in seen:
            raise ValueError("broker_seed_duplicate_key")
        seen.add(key(bar));result.append(bar)
    if not result:
        raise ValueError("broker_seed_empty_input")
    for group in {(b["instrument_root"], b["contract_maturity"], b["timeframe"]) for b in result}:
        ordered = sorted((b for b in result if key(b)[:3] == group), key=lambda b: b["broker_chart_date"])
        for before, after in zip(ordered, ordered[1:]):
            if after["previous_same_timeframe_night_close"] is not None and _number(after["previous_same_timeframe_night_close"]) != _number(before["close"]):
                raise ValueError("broker_seed_previous_same_period_mismatch")
    return result


def _atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".history-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def load_history(path):
    p = Path(path)
    if p.is_symlink():raise ValueError("broker_seed_symlink")
    if not p.exists():return dict(contract=CONTRACT, bars=[])
    value = json.loads(p.read_bytes())
    if value.get("contract") != CONTRACT or len({key(b) for b in value["bars"]}) != len(value["bars"]):
        raise ValueError("broker_seed_history_contract")
    _versions(value)
    return value


def _versions(history):
    latest = {key(b): (b, sha(encoded(b))) for b in history["bars"]}
    for rev in history.get("revisions", []):
        content = {k:v for k,v in rev.items() if k != "revision_sha256"}
        b = rev["bar"];old = latest.get(key(b))
        if (rev.get("contract") != REVISION_CONTRACT or sha(encoded(content)) != rev["revision_sha256"]
                or old is None or rev["previous_revision_sha256"] != old[1]):
            raise ValueError("broker_seed_revision_chain")
        observed = _aware(datetime.fromisoformat(rev["observed_at"]))
        received = _aware(datetime.fromisoformat(rev["received_at"]))
        available = _aware(datetime.fromisoformat(b["first_system_available_at"]))
        if not observed <= received <= available:
            raise ValueError("broker_seed_revision_time_order")
        latest[key(b)] = (b, rev["revision_sha256"])
    return latest


def commit_seed(*, history_path, raw, available_at=None, revision_metadata=None):
    """One atomic append; an exact reimport does not alter availability or bytes."""
    at = _aware(available_at or datetime.now(timezone.utc))
    incoming = parse_seed(raw, available_at=at)
    path = Path(history_path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("broker_seed_symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent/"history.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        before = path.read_bytes() if path.exists() else None
        current = load_history(path);versions = _versions(current)
        by_key = {k:b for k,(b,_) in versions.items()}
        known = {}
        for b in [*current["bars"], *(r["bar"] for r in current.get("revisions", []))]:
            known.setdefault(key(b),set()).add(sha(encoded(source_content(b))))
        conflicts, new_revisions = [], []
        for b in incoming:
            if key(b) not in by_key or sha(encoded(source_content(b))) in known[key(b)]:continue
            old, previous = versions[key(b)]
            meta = (revision_metadata or {}).get(b["screenshot_sha256"], {})
            progress = b["timeframe"] in ("WEEKLY", "MONTHLY") and old["chart_status"] == b["chart_status"] == "IN_PROGRESS"
            kind = "PROGRESS_SNAPSHOT" if progress else "EXPLICIT_CORRECTION"
            try:
                observed = _aware(datetime.fromisoformat(meta["observed_at"]))
                received = _aware(datetime.fromisoformat(meta["received_at"]))
                if (meta.get("kind") != kind or not meta.get("reason") or meta.get("previous_revision_sha256") != previous
                        or not observed <= received <= at or received <= datetime.fromisoformat(old["first_system_available_at"])
                        or b["screenshot_sha256"] == old["screenshot_sha256"]
                        or (progress and (
                            (b["previous_same_timeframe_night_close"] is None) != (old["previous_same_timeframe_night_close"] is None)
                            or (b["previous_same_timeframe_night_close"] is not None
                                and _number(b["previous_same_timeframe_night_close"]) != _number(old["previous_same_timeframe_night_close"]))
                        ))):
                    raise ValueError("broker_seed_revision_metadata")
            except (KeyError, TypeError, ValueError):
                conflicts.append(b);continue
            original = next(x for x in current["bars"] if key(x)==key(b))
            rev = dict(contract=REVISION_CONTRACT,bar=b,previous_revision_sha256=previous,
                original_first_system_available_at=original["first_system_available_at"],
                observed_at=observed.isoformat(),received_at=received.isoformat(),kind=kind,reason=meta["reason"])
            rev["revision_sha256"] = sha(encoded(rev));new_revisions.append(rev)
        if conflicts:
            quarantine = path.parent/"quarantine"/(sha(raw)+".json")
            if not quarantine.exists():_atomic(quarantine, encoded(dict(contract=CONTRACT, at=at.isoformat(), conflicts=conflicts)))
            return dict(status="QUARANTINED_NO_HISTORY_CHANGE", conflicts=len(conflicts), inserted=0,
                        before_count=len(by_key), after_count=len(by_key), quarantine=str(quarantine))
        additions = [b for b in incoming if key(b) not in by_key]
        if not additions and not new_revisions:
            return dict(status="NOOP", inserted=0, unchanged=len(incoming), conflicts=0,
                        before_count=len(by_key), after_count=len(by_key), history_sha256=sha(before))
        rollback = dict(existed=before is not None, before_sha256=sha(before) if before else None,
                        previous_snapshot=None, rule="Restore only under history.lock after matching committed SHA")
        if before:
            snapshot = path.parent/"snapshots"/(sha(before)+".json")
            if not snapshot.exists():_atomic(snapshot, before)
            rollback["previous_snapshot"] = str(snapshot)
        merged = sorted([*current["bars"], *additions], key=key)
        value = dict(contract=CONTRACT, committed_at=at.isoformat(), bars=merged)
        if current.get("revisions") or new_revisions:
            value["revisions"] = [*current.get("revisions", []), *new_revisions]
        for rev in new_revisions:
            artifact = path.parent/"revisions"/(rev["revision_sha256"]+".json")
            content = encoded(rev)
            if artifact.exists() and artifact.read_bytes()!=content:raise ValueError("broker_seed_revision_artifact_conflict")
            if not artifact.exists():_atomic(artifact,content)
        content = encoded(value);rollback["committed_sha256"] = sha(content)
        _atomic(path.parent/"commits"/(sha(content)+".rollback.json"), encoded(rollback))
        _atomic(path, content)
        return dict(status="COMMITTED", inserted=len(additions), unchanged=len(incoming)-len(additions)-len(new_revisions), conflicts=0,
                    new_revisions=len(new_revisions),before_count=len(by_key), after_count=len(merged), history_sha256=sha(content), rollback=rollback)


def render_broker_history(history, *, instrument_root, contract_maturity, cutoff):
    at = _aware(cutoff)
    if history.get("contract") != CONTRACT:raise ValueError("broker_seed_history_contract")
    lines = [f"{instrument_root} 야간선물 · {contract_maturity} 만기 (증권사 차트)", "SOURCE-ONLY · NO-SEND · 날짜 명시 이력"]
    selected, exclusions = [], []
    _versions(history)
    candidates_by_key = {key(b): (b,sha(encoded(b)),None) for b in history["bars"]
        if datetime.fromisoformat(b["first_system_available_at"])<=at}
    for rev in history.get("revisions", []):
        b=rev["bar"]
        if datetime.fromisoformat(b["first_system_available_at"])<=at:
            candidates_by_key[key(b)]=(b,rev["revision_sha256"],rev)
    mapping=map_latest_completed_krx_night_session(at)
    expected_chart=str(mapping.ui_session_start_date) if mapping else None
    for timeframe, label in zip(TIMEFRAMES, ("일봉", "주봉", "월봉")):
        candidates=[]
        for b,version,revision in candidates_by_key.values():
            if (b["instrument_root"],b["contract_maturity"],b["timeframe"])!=(instrument_root,contract_maturity,timeframe):continue
            chart=date.fromisoformat(b["broker_chart_date"])
            observed=datetime.fromisoformat(revision["observed_at"] if revision else b["first_system_available_at"])
            received=datetime.fromisoformat(revision["received_at"] if revision else b["first_system_available_at"])
            reason=None
            if observed>at or received>at:reason="SNAPSHOT_AFTER_CUTOFF"
            elif chart>at.astimezone(KST).date() or chart>observed.astimezone(KST).date():reason="FUTURE_CHART_DATE"
            elif timeframe=="DAILY" and datetime.combine(date.fromisoformat(b["calendar_night_end_date"]),NIGHT_SESSION_COMPLETION_TIME,KST)>at:reason="NIGHT_NOT_ENDED"
            if reason:
                exclusions.append(dict(key=list(key(b)),reason=reason));continue
            current_period = (b["broker_chart_date"]==expected_chart if timeframe=="DAILY" else
                chart.isocalendar()[:2]==at.astimezone(KST).date().isocalendar()[:2] if timeframe=="WEEKLY" else
                (chart.year,chart.month)==(at.astimezone(KST).year,at.astimezone(KST).month))
            candidates.append(dict(b,revision_sha256=version,source_snapshot_observed_at=observed.isoformat(),
                source_received_at=received.isoformat(),snapshot_time_basis="EXPLICIT_REVISION" if revision else "LEGACY_FIRST_VERIFIED_AVAILABILITY_BOUND",current_period_match=current_period,
                use_scope="DATED_BROKER_CHART_REFERENCE",current_directional=False))
        if not candidates:
            lines.append(label+": 자료 부족");continue
        b = max(candidates, key=lambda b: b["broker_chart_date"]);selected.append(b)
        state = ", 진행중" if b["chart_status"] == "IN_PROGRESS" else ""
        change = b["pct_vs_previous_same_timeframe_night_close"]
        suffix = f" ({_number(change):+.2f}%)" if change is not None else " (동일 주기 비교 자료 부족)"
        lines.append(f"{label} ({b['broker_chart_date']}{state}): {_number(b['close']):,.2f}"+suffix)
    lines.append("수익률은 같은 만기·같은 주기의 직전 야간봉 종가 대비입니다.")
    lines.append("사용자 제공 차트 이력이며, 당시 평가시각 이용 가능성과 공식 현재 자료 사용권은 미확인입니다.")
    return dict(text="\n".join(lines)+"\n", selected=selected, market_judgment=None,
                expected_chart_date=expected_chart,exclusions=exclusions,
                current_directional=False, full_market_parent=False, model_use=False, NO_SEND=True)
