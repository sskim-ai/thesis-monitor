"""Read-only production schedule ownership; no scheduler or runtime mutation."""
from __future__ import annotations

from datetime import date, datetime, time
from hashlib import sha256
from pathlib import Path
import plistlib
import tomllib
from zoneinfo import ZoneInfo

import exchange_calendars


KST = ZoneInfo("Asia/Seoul")
NY = ZoneInfo("America/New_York")
CONTRACT = "m12ds-r6-r2-production-market-cutoff-audit-v1"
COLLECTORS = {"daily": "US", "kr-close": "KR"}


def session_at(cutoff: datetime, market: str) -> dict:
    if cutoff.tzinfo is None or market not in {"US", "KR"}:
        raise ValueError("aware_cutoff_and_known_market_required")
    zone = NY if market == "US" else KST
    name = "XNYS" if market == "US" else "XKRX"
    local = cutoff.astimezone(zone)
    calendar = exchange_calendars.get_calendar(name)
    try:
        current = calendar.is_session(local.date())
        target = calendar.date_to_session(local.date(), direction="previous")
        close = calendar.session_close(target).to_pydatetime()
        if local < close:
            target = calendar.previous_session(target)
        completed_close = calendar.session_close(target).to_pydatetime()
        if current:
            today = calendar.date_to_session(local.date())
            opened = calendar.session_open(today).to_pydatetime()
            closed = calendar.session_close(today).to_pydatetime()
            state = "PRE_OPEN" if local < opened else "INTRADAY" if local < closed else "POST_CLOSE"
        else:
            state = "NON_SESSION"
    except (ValueError, IndexError, TypeError) as exc:
        raise ValueError("exchange_calendar_cutoff_unresolved") from exc
    return {
        "scheduled_kst": cutoff.astimezone(KST).isoformat(),
        "exchange_local": local.isoformat(),
        "exchange_timezone": zone.key,
        "calendar": name,
        "regular_session_state": state,
        "intended_completed_session": target.date().isoformat(),
        "completed_session_close": completed_close.astimezone(zone).isoformat(),
        "after_hours_may_still_be_active": market == "US" and state == "POST_CLOSE" and local.hour < 20,
        "schedule_is_not_source_finality": True,
    }


def calendar_times(payload: dict) -> list[tuple[int, int]]:
    rows = payload.get("StartCalendarInterval")
    rows = [rows] if isinstance(rows, dict) else rows
    if not isinstance(rows, list) or not rows:
        raise ValueError("calendar_schedule_missing")
    values = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"Hour", "Minute"}:
            raise ValueError("unsupported_calendar_schedule")
        hour, minute = row["Hour"], row["Minute"]
        if type(hour) is not int or type(minute) is not int or not 0 <= hour < 24 or not 0 <= minute < 60:
            raise ValueError("invalid_calendar_time")
        values.append((hour, minute))
    if len(values) != len(set(values)):
        raise ValueError("duplicate_calendar_time")
    return sorted(values)


def task_time(rule: str) -> tuple[int, int]:
    items = rule.removeprefix("RRULE:").split(";")
    fields = dict(item.split("=", 1) for item in items)
    if len(fields) != len(items) or set(fields) != {"FREQ", "BYHOUR", "BYMINUTE"} or fields["FREQ"] != "DAILY":
        raise ValueError("unsupported_task_schedule")
    result = (int(fields["BYHOUR"]), int(fields["BYMINUTE"]))
    calendar_times({"StartCalendarInterval": {"Hour": result[0], "Minute": result[1]}})
    return result


def schedule_receipt(repo: Path, home: Path, run_date: date) -> dict:
    rows = []
    for label, market in COLLECTORS.items():
        name = f"com.seungsoo.thesis-monitor.{label}.plist"
        owned_path = repo / "ops" / name
        installed_path = home / "Library/LaunchAgents" / name
        owned_raw, installed_raw = owned_path.read_bytes(), installed_path.read_bytes()
        owned, installed = plistlib.loads(owned_raw), plistlib.loads(installed_raw)
        for key in ("Label", "ProgramArguments", "WorkingDirectory", "StartCalendarInterval"):
            if owned.get(key) != installed.get(key):
                raise ValueError(f"installed_schedule_owner_mismatch:{name}:{key}")
        if f"app.jobs.monitor_daily --market {market.lower()}" not in " ".join(owned["ProgramArguments"]):
            raise ValueError("collector_command_owner_mismatch")
        rows.append({
            "kind": "SOURCE_COLLECTOR", "market": market,
            "repository_path": str(owned_path.relative_to(repo)),
            "repository_sha256": sha256(owned_raw).hexdigest(),
            "installed_path": str(installed_path),
            "installed_sha256": sha256(installed_raw).hexdigest(),
            "owner_parity": True,
            "cutoffs": [session_at(datetime.combine(run_date, time(*t), KST), market)
                        for t in calendar_times(owned)],
        })
    for market in ("US", "KR"):
        for role in ("primary", "backup"):
            path = home / ".codex/automations" / f"thesis-monitor-ai-review-{market.lower()}-{role}" / "automation.toml"
            raw = path.read_bytes()
            task = tomllib.loads(raw.decode())
            if task.get("timezone") not in (None, KST.key):
                raise ValueError("task_timezone_owner_mismatch")
            t = task_time(task["rrule"])
            rows.append({"kind": "AI_TASK", "market": market, "role": role,
                "name": task["name"], "status": task["status"], "source_path": str(path),
                "source_sha256": sha256(raw).hexdigest(),
                "timezone_owner": "docs/operations/SCHEDULED_TASK_CONTRACTS.md + host local timezone",
                "cutoffs": [session_at(datetime.combine(run_date, time(*t), KST), market)],
                "does_not_refresh_claimed_packet": True})
    for label, kind in (("ai-review-fallback", "FALLBACK"), ("ai-review-delivery-retry", "DELIVERY_RETRY")):
        path = repo / "ops" / f"com.seungsoo.thesis-monitor.{label}.plist"
        installed = home / "Library/LaunchAgents" / path.name
        raw = path.read_bytes()
        p, live = plistlib.loads(raw), plistlib.loads(installed.read_bytes())
        if any(p.get(k) != live.get(k) for k in ("StartCalendarInterval", "ProgramArguments", "WorkingDirectory")):
            raise ValueError("installed_backup_owner_mismatch")
        rows.append({"kind": kind, "repository_path": str(path.relative_to(repo)),
            "source_sha256": sha256(raw).hexdigest(), "installed_sha256": sha256(installed.read_bytes()).hexdigest(),
            "scheduled_local_times": [f"{h:02d}:{m:02d}" for h, m in calendar_times(p)],
            "uses_persisted_packet_or_payload": True})
    return {"contract": CONTRACT, "status": "RESOLVED_CONFIGURED_SCHEDULE",
        "timezone": KST.key, "run_date": run_date.isoformat(), "rows": rows,
        "fresh_collection_cutoff_owner": "actual acquisition timestamp, never scheduled time substituted into later response",
        "source_availability_at_scheduled_cutoff_proven": False,
        "scheduler_mutations": 0, "model_calls": 0}
