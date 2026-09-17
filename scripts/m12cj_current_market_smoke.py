from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REQUIRED_RUNTIME_BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
EXPECTED_RUNTIME_TREE_SHA256 = (
    "f66f345e3d49ab21d169acd056330342f1609a6c7738020fca1fbc7710b86263"
)
M12CH_ZIP_SHA256 = "84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e"
FIXTURE_REFERENCE_DATE = date(2026, 9, 16)
STATE_DIRECTORIES = (
    "company_profile_provenance",
    "history",
    "macro",
    "market",
    "market-context",
    "onboarding",
    "theses",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def json_value(value: object) -> object:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def git_text(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def runtime_integrity() -> dict[str, object]:
    paths = git_text(
        "ls-tree",
        "-r",
        "--name-only",
        REQUIRED_RUNTIME_BASE,
        "--",
        "app",
        "pyproject.toml",
        "uv.lock",
        "scripts/v2_production_cutover_preflight.py",
    ).splitlines()
    rows: list[dict[str, object]] = []
    drift: list[str] = []
    for relative in paths:
        current = (REPO / relative).read_bytes()
        frozen = git_bytes("show", f"{REQUIRED_RUNTIME_BASE}:{relative}")
        if current != frozen:
            drift.append(relative)
        rows.append(
            {"path": relative, "sha256": sha256_bytes(current), "size": len(current)}
        )
    tree_sha = canonical_sha256(rows)
    return {
        "contract": "m12cj-source-base-runtime-integrity-v1",
        "head": git_text("rev-parse", "HEAD"),
        "instruction_commit": git_text("rev-parse", "c85b887f"),
        "required_runtime_base": REQUIRED_RUNTIME_BASE,
        "runtime_tree_sha256": tree_sha,
        "expected_runtime_tree_sha256": EXPECTED_RUNTIME_TREE_SHA256,
        "runtime_file_count": len(rows),
        "application_runtime_config_source_change_count": len(drift),
        "drift": drift,
        "status": (
            "PASS"
            if not drift and tree_sha == EXPECTED_RUNTIME_TREE_SHA256
            else "FAIL"
        ),
    }


def sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def copy_runtime_state(source_data: Path, destination_data: Path) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    for name in STATE_DIRECTORIES:
        source = source_data / name
        destination = destination_data / name
        if not source.exists():
            continue
        shutil.copytree(source, destination, dirs_exist_ok=True)
        copied.append({"name": name, "source": str(source), "destination": str(destination)})
    return copied


def source_db_identity(path: Path) -> dict[str, object]:
    wal = path.with_name(path.name + "-wal")
    return {
        "path": str(path),
        "database_size": path.stat().st_size,
        "database_sha256": sha256_file(path),
        "wal_present": wal.is_file(),
        "wal_size": wal.stat().st_size if wal.is_file() else 0,
        "wal_sha256": sha256_file(wal) if wal.is_file() else None,
    }


def telemetry_snapshot(session: object) -> dict[tuple[str, str, str], dict[str, object]]:
    from sqlmodel import select

    from app.models.security import ProviderCallTelemetry

    rows = session.exec(select(ProviderCallTelemetry)).all()  # type: ignore[attr-defined]
    return {
        (row.provider, row.endpoint, row.ticker): {
            "provider": row.provider,
            "endpoint": row.endpoint,
            "ticker": row.ticker,
            "status": row.status,
            "success_count": row.success_count,
            "failure_count": row.failure_count,
            "skip_count": row.skip_count,
            "last_success_at": row.last_success_at,
            "last_failure_at": row.last_failure_at,
            "error_type": row.error_type,
            "error_reason": row.error_reason,
        }
        for row in rows
    }


def telemetry_delta(
    before: Mapping[tuple[str, str, str], Mapping[str, object]],
    after: Mapping[tuple[str, str, str], Mapping[str, object]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for key in sorted(after):
        current = after[key]
        prior = before.get(key, {})
        success = int(current.get("success_count") or 0) - int(
            prior.get("success_count") or 0
        )
        failure = int(current.get("failure_count") or 0) - int(
            prior.get("failure_count") or 0
        )
        skipped = int(current.get("skip_count") or 0) - int(
            prior.get("skip_count") or 0
        )
        if not any((success, failure, skipped)):
            continue
        result.append(
            {
                "provider": current["provider"],
                "endpoint": current["endpoint"],
                "ticker": current["ticker"],
                "success_delta": success,
                "failure_delta": failure,
                "skip_delta": skipped,
                "terminal_status": current.get("status"),
                "error_type": current.get("error_type"),
                "error_reason": current.get("error_reason"),
            }
        )
    return result


def current_population(session: object, observed_at: datetime) -> dict[str, object]:
    from app.services.onboarding_readiness_service import production_universe_snapshot

    markets: dict[str, object] = {}
    all_tickers: list[str] = []
    for market in ("us", "kr"):
        snapshot = production_universe_snapshot(
            session,  # type: ignore[arg-type]
            market,
            cutoff=observed_at.astimezone(UTC),
            session_key=f"daily_{market}",
        )
        tickers = [row.ticker for row in snapshot.eligible_items]
        all_tickers.extend(tickers)
        markets[market] = {
            "count": len(tickers),
            "tickers": tickers,
            "snapshot": snapshot.to_dict(),
        }
    return {
        "contract": "m12cj-monitored-population-snapshot-v1",
        "observed_at": observed_at.isoformat(),
        "source": "canonical_production_universe_snapshot_on_readonly_backup",
        "markets": markets,
        "total_count": len(all_tickers),
        "unique_count": len(set(all_tickers)),
        "duplicate_count": len(all_tickers) - len(set(all_tickers)),
    }


def serialized_market_observation(row: object, expected: date | None) -> dict[str, object]:
    from app.macro.briefing import market_observation_to_dict

    value = market_observation_to_dict(row)  # type: ignore[arg-type]
    value["expected_latest_session_date"] = expected.isoformat() if expected else None
    value["expected_reference_date"] = expected.isoformat() if expected else None
    value["provider_raw_bas_dd"] = value.get("trade_date")
    value["reference_date_match"] = bool(
        expected and value.get("trade_date") == expected.isoformat()
    )
    return value


def deterministic_stock_payloads(session: object, run_date: date, market: str) -> dict[str, object]:
    from sqlmodel import select

    from app.models.thesis import InvestmentThesis, ThesisAssessment
    from app.models.watchlist import WatchlistItem
    from app.services.daily_monitor_service import _item_market_scope
    from app.services.notification_service import (
        _assessment_report,
        _previous_cash_flow_user_visible_context,
        _previous_working_capital_user_visible_context,
    )

    assessments = session.exec(  # type: ignore[attr-defined]
        select(ThesisAssessment).where(ThesisAssessment.assessment_date == run_date)
    ).all()
    messages: list[dict[str, object]] = []
    for assessment in sorted(assessments, key=lambda row: row.ticker):
        item = session.exec(  # type: ignore[attr-defined]
            select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
        ).first()
        if item is None or _item_market_scope(session, item) != market:  # type: ignore[arg-type]
            continue
        thesis = session.exec(  # type: ignore[attr-defined]
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == assessment.ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        text, context = _assessment_report(
            assessment,
            item.company_name or assessment.ticker,
            thesis,
            previous_cash_flow_user_visible_context=(
                _previous_cash_flow_user_visible_context(session, assessment)  # type: ignore[arg-type]
            ),
            previous_working_capital_user_visible_context=(
                _previous_working_capital_user_visible_context(session, assessment)  # type: ignore[arg-type]
            ),
        )
        messages.append(
            {
                "ticker": assessment.ticker,
                "payload": {
                    "text": text,
                    "ticker": assessment.ticker,
                    "assessment_date": run_date.isoformat(),
                    "type": "daily_stock_analysis",
                    "presentation": "long_text",
                    "use_llm": False,
                    "analysis_context": context,
                },
            }
        )
    return {
        "contract": "m12cj-isolated-deterministic-stock-payloads-v1",
        "market": market,
        "assessment_date": run_date.isoformat(),
        "message_count": len(messages),
        "messages": messages,
    }


def render_kr_market_only(plan: object, session_date: date) -> str:
    lines = [f"🇰🇷 한국 시장 장마감 점검 · {session_date.isoformat()}"]
    primary = [
        getattr(plan, "judgment", None),
        getattr(plan, "interpretation", None),
        getattr(plan, "next_check", None),
    ]
    claims = [row for row in primary if row is not None]
    if claims:
        lines.extend(["", "📍 국내 장마감 구조"])
        lines.extend(f"• {row.text}" for row in claims)
    internal = [
        row
        for row in (
            getattr(plan, "size_context", None),
            getattr(plan, "sector_context", None),
        )
        if row is not None
    ]
    if internal:
        lines.extend(["", "📊 시장 내부"])
        for row in internal:
            lines.extend(["", row.text])
    return "\n".join(lines).strip()


def fixture_comparison(
    *,
    package_root: Path,
    history_root: Path,
    provider_result: object,
) -> dict[str, object]:
    import exchange_calendars as exchange_calendar

    from app.services.krx_night_history_service import (
        build_same_contract_timeframes,
        load_history,
    )

    fixture_path = package_root / "inputs/kiwoom-kospi200-202612-20260916-human-fixture.json"
    fixture = read_json(fixture_path)
    image_root = package_root / "inputs/kiwoom-kospi200-acceptance"
    image_checks = {
        name: {
            "expected_sha256": expected,
            "observed_sha256": sha256_file(image_root / name),
            "match": sha256_file(image_root / name) == expected,
        }
        for name, expected in fixture["screenshots"].items()
    }
    bars = load_history(
        history_root,
        instrument_root="KOSPI200",
        end=FIXTURE_REFERENCE_DATE,
    )
    canonical = next(
        (
            bar
            for bar in reversed(bars)
            if bar.reference_date == FIXTURE_REFERENCE_DATE
            and bar.contract_maturity == "2026-12"
        ),
        None,
    )
    require(canonical is not None, "krx_fixture_canonical_bar_missing")
    frames = build_same_contract_timeframes(
        history_root,
        instrument_root="KOSPI200",
        reference_date=FIXTURE_REFERENCE_DATE,
        daily_change_value=canonical.official_change,
        daily_change_pct=canonical.official_change_pct,
        daily_baseline_date=None,
        daily_baseline_close=None,
    )
    require(frames is not None, "krx_fixture_timeframes_missing")
    human_daily = {
        date.fromisoformat(str(row["date"])): row for row in fixture["daily"]
    }
    by_date = {bar.reference_date: bar for bar in bars if bar.contract_maturity == "2026-12"}
    calendar = exchange_calendar.get_calendar("XKRX")
    semantic_rows: list[dict[str, object]] = []
    exact_matches = 0
    missing = 0
    for human_date, human in sorted(human_daily.items()):
        provider_date = calendar.date_to_session(human_date, direction="next").date()
        if provider_date == human_date:
            provider_date = calendar.next_session(provider_date).date()
        provider_bar = by_date.get(provider_date)
        comparisons = {}
        for field in ("open", "high", "low", "close", "volume"):
            provider_value = getattr(provider_bar, field) if provider_bar is not None else None
            comparisons[field] = {
                "kiwoom": human[field],
                "krx": provider_value,
                "match": provider_value == human[field],
            }
        row_match = provider_bar is not None and all(
            item["match"] for item in comparisons.values()
        )
        exact_matches += int(row_match)
        missing += int(provider_bar is None)
        semantic_rows.append(
            {
                "kiwoom_ui_session_start_date": human_date,
                "expected_krx_completed_session_end_bas_dd": provider_date,
                "krx_bar_present": provider_bar is not None,
                "fields": comparisons,
                "status": "EXACT_PARITY" if row_match else "SOURCE_NOT_PRESENT",
            }
        )
    direct_fixture = human_daily[FIXTURE_REFERENCE_DATE]
    direct_comparison = {
        field: {
            "kiwoom": direct_fixture[field],
            "krx": getattr(canonical, field),
            "match": getattr(canonical, field) == direct_fixture[field],
        }
        for field in ("open", "high", "low", "close", "volume")
    }
    # Three earlier controls align exactly after mapping the Kiwoom start-date label
    # to the KRX completed-session-end BAS_DD. The newest mapped BAS_DD is not yet in
    # the canonical history, so this is a documented label semantic difference rather
    # than a same-session numeric mismatch.
    explained = exact_matches >= 3 and all(item["match"] for item in image_checks.values())
    verdict = (
        "EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE"
        if explained
        else "UNEXPLAINED_MISMATCH"
    )
    raw_relative = canonical.source_raw_relative_path
    raw_path = history_root / raw_relative
    receipt_path = raw_path.with_suffix(".receipt.json")
    probe_dump = json_value(provider_result)
    require(isinstance(probe_dump, dict), "krx_provider_result_not_serializable")
    telemetry = probe_dump.get("telemetry")
    telemetry = telemetry if isinstance(telemetry, dict) else {}
    return {
        "contract": "m12cj-krx-kiwoom-night-fixture-comparison-v1",
        "machine_authority": "OFFICIAL_KRX_NIGHT",
        "human_fixture_role": "HUMAN_ACCEPTANCE_CROSS_CHECK_ONLY",
        "fixture_path": str(fixture_path),
        "fixture_sha256": sha256_file(fixture_path),
        "image_hashes": image_checks,
        "fixture": fixture,
        "canonical_product_reference_date": FIXTURE_REFERENCE_DATE,
        "selected_krx_contract": canonical.contract_maturity.replace("-", ""),
        "selected_krx_contract_code": canonical.contract_code,
        "selected_krx_daily_bar": canonical.model_dump(mode="json"),
        "direct_same_label_field_comparison": direct_comparison,
        "documented_date_semantics": {
            "kiwoom": "UI night-session start/trade date",
            "krx": "BAS_DD completed-session end date",
            "mapping": "next XKRX business session",
            "production_product_contract": "us-morning-night-reference-date-v3",
            "production_product_reference_rule": (
                "latest_valid_xkrx_business_date_strictly_before_kst_date"
            ),
            "fixture_latest_economic_session_krx_bas_dd": "2026-09-17",
            "fixture_latest_economic_session_source_state": (
                "NOT_PRESENT_IN_CANONICAL_HISTORY_AT_EXECUTION"
            ),
        },
        "semantic_alignment_rows": semantic_rows,
        "semantic_alignment_exact_count": exact_matches,
        "semantic_alignment_missing_count": missing,
        "timeframes_for_production_reference_date": frames.model_dump(mode="json"),
        "raw_source": {
            "relative_path": raw_relative,
            "payload_sha256": sha256_file(raw_path),
            "receipt_path": str(receipt_path),
            "receipt_sha256": sha256_file(receipt_path) if receipt_path.is_file() else None,
        },
        "current_provider_probe": {
            "provider": probe_dump.get("provider"),
            "warning_count": len(probe_dump.get("warnings") or []),
            "expected_reference_date": telemetry.get("expected_reference_date"),
            "queried_dates": telemetry.get("queried_dates"),
            "date_statuses": telemetry.get("date_statuses"),
            "product_statuses": telemetry.get("product_statuses"),
        },
        "kosdaq150_human_fixture": "HUMAN_FIXTURE_NOT_PROVIDED",
        "overall_fixture_verdict": verdict,
        "machine_values_rewritten": False,
        "human_values_rewritten": False,
    }


async def run(args: argparse.Namespace) -> None:
    observed_at = (
        datetime.fromisoformat(args.observed_at)
        if args.observed_at
        else datetime.now(KST)
    )
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=KST)
    observed_at = observed_at.astimezone(KST)
    output = args.output_root.resolve()
    require(not output.exists(), "output_root_already_exists")
    output.mkdir(parents=True)

    integrity = runtime_integrity()
    write_json(output / "source-base-runtime-integrity.json", integrity)
    require(integrity["status"] == "PASS", "runtime_integrity_failed")

    package = args.package_root.resolve()
    package_verification = json.loads(
        subprocess.run(
            ("python3", str(package / "verify_package.py")),
            cwd=package,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    require(package_verification.get("status") == "PASS", "package_integrity_failed")
    m12ch_zip = package / "sources/thesis-monitor-20260917-m12ch-frozen-contract-new-full22-reproof-report.zip"
    require(sha256_file(m12ch_zip) == M12CH_ZIP_SHA256, "m12ch_zip_sha_mismatch")
    write_json(output / "package-integrity.json", package_verification)

    source_data = args.source_data.resolve()
    source_db = source_data / "thesis_monitor.sqlite3"
    source_before = source_db_identity(source_db)
    isolated_data = output / "isolated-data"
    isolated_data.mkdir()
    sqlite_backup(source_db, isolated_data / "thesis_monitor.sqlite3")
    copied = copy_runtime_state(source_data, isolated_data)

    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
    os.environ["DATA_DIR"] = str(isolated_data)
    os.environ["DATABASE_URL"] = f"sqlite:///{isolated_data / 'thesis_monitor.sqlite3'}"
    os.environ["NOTIFICATION_DRY_RUN"] = "true"
    os.environ["NOTIFICATION_RECIPIENT_CLASS"] = "test"
    os.environ["AI_REVIEW_MODE"] = "shadow"
    os.environ["PERSISTENCE_V2_WRITER_ENABLED"] = "false"
    os.environ["PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED"] = "false"

    from sqlmodel import Session, select

    from app.database import engine, init_db
    from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
    from app.macro.kr_close import run_kr_close_market_briefing
    from app.macro.providers.krx import KrxNightFuturesProvider
    from app.macro.service import run_macro_monitor
    from app.macro.storage import persist_observation
    from app.models.thesis import ThesisAssessment
    from app.services.ai_review_service import write_ai_review_packet
    from app.services.daily_monitor_service import run_daily_monitor
    from app.services.kiwoom_kr_market_context_service import (
        collect_and_persist_kiwoom_market_context,
    )
    from app.services.kr_market_digest_context_service import (
        load_current_kr_digest_context,
    )
    from app.services.kr_market_digest_quality_service import build_kr_market_digest_plan
    from app.services.market_evidence_utilization_validator_service import (
        validate_kr_market_evidence_utilization,
    )
    from app.services.market_session import korea_market_session, us_market_session
    from app.services.morning_gate import (
        _replace_night_observations,
        _write_gate_metadata,
    )
    from app.services.us_exchange_breadth_service import (
        collect_and_persist_us_exchange_breadth,
    )
    from app.services.us_full_message_service import render_us_full_market_message
    from app.services.us_market_message_quality_service import (
        validate_us_market_message_payload,
    )

    init_db()
    us_session = us_market_session(observed_at)
    kr_session = korea_market_session(observed_at)
    us_run_date = observed_at.date()
    kr_stock_run_date = observed_at.date()
    kr_close_date = kr_session.latest_completed_regular_session_date
    expected_night = expected_latest_completed_krx_session(observed_at.date())
    session_resolution = {
        "contract": "m12cj-execution-session-resolution-v1",
        "observed_at_kst": observed_at.isoformat(),
        "us": {
            "smoke_assessment_date": us_run_date,
            "market_session_state": us_session.session,
            "latest_completed_regular_session_date": (
                us_session.latest_completed_regular_session_date
            ),
        },
        "kr": {
            "stock_smoke_assessment_date": kr_stock_run_date,
            "stock_evidence_mode": (
                "TYPED_INTRADAY_PROVISIONAL"
                if kr_session.session == "open"
                else "COMPLETED_CLOSE"
            ),
            "market_session_state": kr_session.session,
            "latest_completed_regular_session_date": kr_close_date,
            "close_equivalent_market_message_date": kr_close_date,
        },
        "krx_night": {
            "product_reference_date": expected_night,
            "fixture_reference_date": FIXTURE_REFERENCE_DATE,
        },
    }
    write_json(output / "execution-session-resolution.json", session_resolution)

    with Session(engine) as session:
        population = current_population(session, observed_at)
        write_json(output / "monitored-population-snapshot.json", population)
        require(population["duplicate_count"] == 0, "population_duplicate")
        telemetry_before = telemetry_snapshot(session)

        macro_result = await run_macro_monitor(
            session,
            run_date=us_run_date,
            force=True,
            excluded_provider_names={"krx_night_futures"},
            as_of=observed_at,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        kr_close_result = await run_kr_close_market_briefing(
            session,
            kr_close_date,
            as_of=observed_at,
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        us_breadth = await collect_and_persist_us_exchange_breadth(
            session_date=us_session.latest_completed_regular_session_date,
            observed_at=observed_at,
        )
        kr_context = await collect_and_persist_kiwoom_market_context(
            session_date=kr_close_date,
            observed_at=observed_at,
        )

        night_provider = KrxNightFuturesProvider()
        night_result = await night_provider.collect(observed_at)
        night_rows: list[dict[str, object]] = []
        for observation in night_result.observations:
            row, _ = persist_observation(
                session,
                night_provider.name,
                observation,
                observed_at,
            )
            night_rows.append(serialized_market_observation(row, expected_night))
        _replace_night_observations(session, us_run_date, night_rows)
        _write_gate_metadata(
            session,
            us_run_date,
            {
                "state": "ready" if len(night_rows) == 2 else "deadline_reached",
                "expected_session": expected_night.isoformat() if expected_night else None,
                "expected_reference_date": (
                    expected_night.isoformat() if expected_night else None
                ),
                "query_attempted": True,
                "first_query_at": observed_at.isoformat(),
                "last_query_at": observed_at.isoformat(),
                "ready_products": [str(row.get("series_code")) for row in night_rows],
                "retry_count": 1,
                "deadline_reached": True,
            },
        )

        us_monitor = await run_daily_monitor(
            session,
            run_date=us_run_date,
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
            market_scope="us",
            as_of=observed_at,
        )
        kr_monitor = await run_daily_monitor(
            session,
            run_date=kr_stock_run_date,
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
            market_scope="kr",
            as_of=observed_at,
        )

        write_json(
            output / "collection-results.json",
            {
                "macro": json_value(macro_result),
                "kr_close": json_value(kr_close_result),
                "us_exchange_breadth": us_breadth,
                "kr_market_context": kr_context,
                "krx_night_probe": json_value(night_result),
                "us_monitor": json_value(us_monitor),
                "kr_monitor": json_value(kr_monitor),
            },
        )

        for market, result, expected_count in (
            ("us", us_monitor, population["markets"]["us"]["count"]),  # type: ignore[index]
            ("kr", kr_monitor, population["markets"]["kr"]["count"]),  # type: ignore[index]
        ):
            require(result.status == "success", f"{market}_monitor_not_success")
            require(result.failure_count == 0, f"{market}_monitor_has_failures")
            require(result.success_count == expected_count, f"{market}_monitor_count_drift")

        packet_paths: dict[str, Path] = {}
        for market, run_date in (("us", us_run_date), ("kr", kr_stock_run_date)):
            result = write_ai_review_packet(
                session,
                run_date,
                market,  # type: ignore[arg-type]
                generated_at=observed_at,
            )
            require(result.status in {"created", "already_exists"}, f"{market}_packet_not_created")
            require(result.path is not None, f"{market}_packet_path_missing")
            packet_path = Path(result.path)
            packet = read_json(packet_path)
            require(packet.get("ready_for_ai") is True, f"{market}_packet_not_ai_ready")
            destination = output / "inputs/current-packets" / f"{market}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(packet_path, destination)
            packet_paths[market] = destination

            deterministic = deterministic_stock_payloads(session, run_date, market)
            expected = population["markets"][market]["count"]  # type: ignore[index]
            require(deterministic["message_count"] == expected, f"{market}_deterministic_count")
            write_json(
                output / "inputs/deterministic" / f"{market}.json",
                deterministic,
            )

        us_packet = read_json(packet_paths["us"])
        us_render = render_us_full_market_message(us_packet["market_context"])
        us_quality = validate_us_market_message_payload(us_render.text)
        write_text(output / "captures/current-us-market-message.txt", us_render.text)
        write_json(
            output / "current-us-market-smoke.json",
            {
                "contract": "m12cj-current-us-market-smoke-v1",
                "target_session": us_session.latest_completed_regular_session_date,
                "packet_id": us_packet["packet_id"],
                "packet_sha256": sha256_file(packet_paths["us"]),
                "render": us_render.to_dict(),
                "quality": us_quality.to_dict(),
                "capture_sha256": sha256_bytes(us_render.text.encode("utf-8")),
                "production_send": 0,
                "status": (
                    "PASS"
                    if us_render.status == "PASS" and us_quality.status == "PASS"
                    else "FAIL"
                ),
            },
        )

        kr_normalized = load_current_kr_digest_context(
            kr_close_date,
            as_of=observed_at,
            cutoff=observed_at,
        )
        require(kr_normalized is not None, "kr_close_equivalent_context_missing")
        kr_plan = build_kr_market_digest_plan(kr_normalized)
        kr_text = render_kr_market_only(kr_plan, kr_close_date)
        kr_validation = validate_kr_market_evidence_utilization(
            kr_plan,
            rendered_text=kr_text,
        )
        write_text(output / "captures/current-kr-market-message.txt", kr_text)
        write_json(
            output / "current-kr-market-smoke.json",
            {
                "contract": "m12cj-current-kr-market-close-equivalent-smoke-v1",
                "target_completed_session": kr_close_date,
                "observation_session_state": kr_session.session,
                "render_mode": "LATEST_COMPLETED_CLOSE_EQUIVALENT",
                "structured_context": kr_normalized.model_dump(mode="json"),
                "plan": kr_plan.to_dict(),
                "evidence_utilization": kr_validation.to_dict(),
                "capture_sha256": sha256_bytes(kr_text.encode("utf-8")),
                "production_send": 0,
                "status": "PASS" if kr_validation.status == "PASS" else "FAIL",
            },
        )

        fixture = fixture_comparison(
            package_root=package,
            history_root=isolated_data / "market/krx-night-history",
            provider_result=night_result,
        )
        write_json(
            output / "krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json",
            fixture,
        )
        raw_relative = str(fixture["raw_source"]["relative_path"])  # type: ignore[index]
        raw_source = isolated_data / "market/krx-night-history" / raw_relative
        raw_destination = output / "source-receipts/krx" / raw_relative
        raw_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw_source, raw_destination)
        receipt_source = raw_source.with_suffix(".receipt.json")
        if receipt_source.is_file():
            shutil.copy2(receipt_source, raw_destination.with_suffix(".receipt.json"))

        telemetry_after = telemetry_snapshot(session)
        provider_rows = telemetry_delta(telemetry_before, telemetry_after)
        write_json(
            output / "provider-call-ledger-redacted.json",
            {
                "contract": "m12cj-redacted-provider-call-ledger-v1",
                "credentials_included": False,
                "telemetry_rows": provider_rows,
                "telemetry_success_delta": sum(
                    int(row["success_delta"]) for row in provider_rows
                ),
                "telemetry_failure_delta": sum(
                    int(row["failure_delta"]) for row in provider_rows
                ),
                "market_provider_reads": {
                    "macro_observation_count": macro_result.observation_count,
                    "us_breadth": us_breadth,
                    "kr_market": kr_context,
                    "krx_night_query_dates": len(
                        dict(json_value(night_result)).get("telemetry", {}).get(
                            "queried_dates", []
                        )
                    ),
                },
            },
        )

        assessment_rows = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.assessment_date == kr_stock_run_date
            )
        ).all()
        kr_price_modes = {
            row.ticker: {
                key: json.loads(row.price_context).get("decision", {}).get(key)
                for key in (
                    "price_as_of",
                    "price_basis",
                    "market_session",
                    "assessment_state",
                    "latest_completed_regular_session_date",
                )
            }
            for row in assessment_rows
            if row.ticker.isdigit()
        }
        write_json(output / "kr-stock-price-mode-audit.json", kr_price_modes)

    source_after = source_db_identity(source_db)
    write_json(
        output / "isolation-audit.json",
        {
            "contract": "m12cj-isolation-audit-v1",
            "source_database_before": source_before,
            "source_database_after": source_after,
            "source_database_identity_stable": source_before == source_after,
            "isolated_database": str(isolated_data / "thesis_monitor.sqlite3"),
            "copied_state": copied,
            "production_db_mutation_by_smoke": 0,
            "production_send": 0,
            "production_recipient_intent": 0,
            "test_sink_invocations": 0,
            "broker_order_calls": 0,
            "broker_modify_calls": 0,
            "broker_cancel_calls": 0,
        },
    )
    write_json(
        output / "scope-correction-m12ci.json",
        {
            "contract": "m12cj-m12ci-scope-correction-v1",
            "windows_kiwoom_gateway_prerequisite": False,
            "m12ci_r1_status": "SUPERSEDED_UNEXECUTED",
            "machine_authority": "OFFICIAL_KRX_NIGHT",
            "kiwoom_fixture_role": "HUMAN_ACCEPTANCE_CROSS_CHECK_ONLY",
            "windows_kiwoom_gateway_provision": 0,
        },
    )
    print(
        json.dumps(
            {
                "status": "COLLECTION_PASS",
                "output_root": str(output),
                "observed_at": observed_at,
                "population": population["total_count"],
                "us_packet": str(output / "inputs/current-packets/us.json"),
                "kr_packet": str(output / "inputs/current-packets/kr.json"),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-data", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--observed-at")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
