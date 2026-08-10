import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment


def _data_root() -> Path:
    root = Path(get_settings().data_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_data_layout() -> None:
    root = _data_root()
    for child in ("theses", "history", "runs", "macro"):
        (root / child).mkdir(parents=True, exist_ok=True)


def _atomic_json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        handle.write("\n")
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def export_thesis(thesis: InvestmentThesis) -> None:
    ensure_data_layout()
    payload = {
        "ticker": thesis.ticker,
        "version": thesis.version,
        "core_thesis": thesis.core_thesis,
        "time_horizon": thesis.time_horizon,
        "thesis_drivers": json.loads(thesis.thesis_drivers),
        "validation_metrics": json.loads(thesis.validation_metrics),
        "market_expectations": json.loads(thesis.market_expectations),
        "valuation_framework": json.loads(thesis.valuation_framework),
        "multiple_expansion_signals": json.loads(thesis.multiple_expansion_signals),
        "multiple_compression_signals": json.loads(thesis.multiple_compression_signals),
        "strengthen_signals": json.loads(thesis.strengthen_signals),
        "weaken_signals": json.loads(thesis.weaken_signals),
        "invalidation_signals": json.loads(thesis.invalidation_signals),
        "price_rules": json.loads(thesis.price_rules),
        "macro_exposures": json.loads(thesis.macro_exposures),
        "status": thesis.status,
        "source": thesis.source,
        "created_at": thesis.created_at,
    }
    _atomic_json_write(_data_root() / "theses" / f"{thesis.ticker}.json", payload)


def export_assessment_history(session: Session, ticker: str) -> None:
    ensure_data_layout()
    assessments = session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == ticker)
        .order_by(ThesisAssessment.assessment_date, ThesisAssessment.id)
    ).all()
    path = _data_root() / "history" / f"{ticker}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        for assessment in assessments:
            payload = {
                "ticker": assessment.ticker,
                "thesis_version": assessment.thesis_version,
                "assessment_date": assessment.assessment_date,
                "status": assessment.status,
                "score": assessment.score,
                "confidence": assessment.confidence,
                "summary": assessment.summary,
                "business_thesis_change": assessment.business_thesis_change,
                "valuation_change": assessment.valuation_change,
                "earnings_estimate_impact": assessment.earnings_estimate_impact,
                "new_confirmed_facts": json.loads(assessment.confirmed_facts),
                "background_confirmed_facts": json.loads(assessment.background_confirmed_facts),
                "inferred_implications": json.loads(assessment.inferred_implications),
                "unknowns": json.loads(assessment.unknowns),
                "confirmed_warnings": json.loads(assessment.confirmed_warnings),
                "new_warnings": json.loads(assessment.new_warnings),
                "open_warnings": json.loads(assessment.open_warnings),
                "warning_states": json.loads(assessment.warning_states),
                "watch_items": json.loads(assessment.watch_items),
                "used_event_fingerprints": json.loads(assessment.used_event_fingerprints),
                "new_buyer_view": assessment.new_buyer_view,
                "holder_view": assessment.holder_view,
                "price_view": assessment.price_view,
                "risk_level": assessment.risk_level,
                "daily_change_severity": assessment.daily_change_severity,
                "structural_risk_level": assessment.structural_risk_level,
                "assessment_state": assessment.assessment_state,
                "market_session": assessment.market_session,
                "new_buyer_price_view": assessment.new_buyer_price_view,
                "holder_price_view": assessment.holder_price_view,
                "evidence": json.loads(assessment.evidence),
                "price_context": json.loads(assessment.price_context),
                "valuation_snapshot": json.loads(assessment.valuation_snapshot),
                "valuation_context": json.loads(assessment.valuation_context),
                "thesis_snapshot": json.loads(assessment.thesis_snapshot),
                "created_at": assessment.created_at,
            }
            handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def export_monitor_run(run: MonitorRun) -> None:
    ensure_data_layout()
    payload = {
        "run_date": run.run_date,
        "run_type": run.run_type,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "ticker_count": run.ticker_count,
        "success_count": run.success_count,
        "failure_count": run.failure_count,
        "details": json.loads(run.details),
    }
    _atomic_json_write(_data_root() / "runs" / f"{run.run_date}.json", payload)


def export_macro_briefing(briefing: MacroBriefing) -> None:
    payload = {
        "briefing_date": briefing.briefing_date,
        "briefing_type": briefing.briefing_type,
        "as_of": briefing.as_of,
        "headline": briefing.headline,
        "market_summary": json.loads(briefing.market_summary),
        "regime_summary": json.loads(briefing.regime_summary),
        "today_calendar": json.loads(briefing.today_calendar),
        "macro_theses": json.loads(briefing.macro_theses),
        "ticker_impacts": json.loads(briefing.ticker_impacts),
        "data_quality": json.loads(briefing.data_quality),
        "kakao_text": briefing.kakao_text,
        "status": briefing.status,
        "market_session": briefing.market_session,
        "assessment_state": briefing.assessment_state,
        "created_at": briefing.created_at,
    }
    _atomic_json_write(
        _data_root() / "macro" / "briefings" / f"{briefing.briefing_date}.json",
        payload,
    )
