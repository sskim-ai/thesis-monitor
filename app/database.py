from collections.abc import Generator
from contextlib import suppress
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


settings = get_settings()


def _ensure_data_directory() -> None:
    if settings.database_url.startswith("sqlite:///./data/"):
        Path(settings.data_dir).mkdir(parents=True, exist_ok=True)


def _sqlite_engine_kwargs() -> dict[str, object]:
    if settings.database_url == "sqlite://":
        return {"connect_args": {"check_same_thread": False, "timeout": 30}, "poolclass": StaticPool}
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False, "timeout": 30}}
    return {}


_ensure_data_directory()
engine = create_engine(settings.database_url, **_sqlite_engine_kwargs())


@event.listens_for(engine, "connect")
def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA busy_timeout=30000")
    with suppress(Exception):
        cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def _ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    table_columns = {
        "watchlistitem": {
            "active": "BOOLEAN DEFAULT 1",
            "latest_status": "VARCHAR",
            "latest_assessment_date": "DATE",
            "latest_valuation_context": "VARCHAR",
            "latest_earnings_estimate_impact": "VARCHAR",
        },
        "event": {
            "raw_summary": "VARCHAR",
            "provider": "VARCHAR DEFAULT 'unknown'",
            "margin_quality_review": "BOOLEAN DEFAULT 0",
            "financial_statement_basis_warning": "BOOLEAN DEFAULT 0",
            "capex_impact_known": "BOOLEAN DEFAULT 0",
            "inventory_risk": "BOOLEAN DEFAULT 0",
            "receivables_risk": "BOOLEAN DEFAULT 0",
            "revenue": "FLOAT",
            "operating_income": "FLOAT",
            "net_income": "FLOAT",
            "operating_margin": "FLOAT",
            "yoy_growth": "FLOAT",
            "qoq_growth": "FLOAT",
            "capex_amount": "FLOAT",
            "financing_amount": "FLOAT",
            "dilution_amount": "FLOAT",
            "guidance_changed": "BOOLEAN DEFAULT 0",
            "material_customer_change": "BOOLEAN DEFAULT 0",
            "operating_cash_flow_impact_known": "BOOLEAN DEFAULT 0",
        },
        "financialsnapshot": {
            "fcf": "FLOAT",
            "accounts_receivable": "FLOAT",
            "stock_based_compensation": "FLOAT",
            "source": "VARCHAR",
            "provider": "VARCHAR",
            "period_type": "VARCHAR",
            "fs_div": "VARCHAR",
            "sj_div": "VARCHAR",
            "revenue_basis": "VARCHAR",
            "operating_income_basis": "VARCHAR",
            "balance_sheet_basis": "VARCHAR",
            "quality_warnings": "VARCHAR",
        },
        "thesisassessment": {
            "thesis_snapshot": "VARCHAR DEFAULT '{}'",
            "valuation_context": "TEXT DEFAULT '{}'",
            "business_thesis_change": "VARCHAR",
            "valuation_change": "VARCHAR",
            "earnings_estimate_impact": "VARCHAR",
            "market_expectation_assessment": "TEXT DEFAULT '{}'",
            "confirmed_facts": "TEXT DEFAULT '[]'",
            "background_confirmed_facts": "TEXT DEFAULT '[]'",
            "inferred_implications": "TEXT DEFAULT '[]'",
            "unknowns": "TEXT DEFAULT '[]'",
            "confirmed_warnings": "TEXT DEFAULT '[]'",
            "new_warnings": "TEXT DEFAULT '[]'",
            "open_warnings": "TEXT DEFAULT '[]'",
            "open_confirmed_warnings": "TEXT DEFAULT '[]'",
            "persistent_watch_risks": "TEXT DEFAULT '[]'",
            "warning_states": "TEXT DEFAULT '[]'",
            "watch_items": "TEXT DEFAULT '[]'",
            "used_event_fingerprints": "TEXT DEFAULT '[]'",
            "daily_change_severity": "VARCHAR DEFAULT 'none'",
            "structural_risk_level": "VARCHAR DEFAULT 'normal'",
            "assessment_state": "VARCHAR DEFAULT 'final'",
            "market_session": "VARCHAR DEFAULT 'unknown'",
            "new_buyer_price_view": "TEXT DEFAULT ''",
            "holder_price_view": "TEXT DEFAULT ''",
            "valuation_snapshot": "TEXT DEFAULT '{}'",
        },
        "investmentthesis": {
            "macro_exposures": "VARCHAR DEFAULT '[]'",
            "thesis_drivers": "TEXT DEFAULT '[]'",
            "validation_metrics": "TEXT DEFAULT '[]'",
            "price_rules": "TEXT DEFAULT '{}'",
            "market_expectations": "TEXT DEFAULT '{}'",
            "valuation_framework": "TEXT DEFAULT '{}'",
            "multiple_expansion_signals": "TEXT DEFAULT '[]'",
            "multiple_compression_signals": "TEXT DEFAULT '[]'",
        },
        "macrothesis": {
            "today_signal": "VARCHAR DEFAULT 'neutral'",
            "today_signal_strength": "VARCHAR DEFAULT 'none'",
            "today_signal_evidence": "TEXT DEFAULT '[]'",
            "today_signal_rationale": "TEXT DEFAULT ''",
            "today_signal_date": "DATE",
        },
        "macroregimeassessment": {
            "market_session": "VARCHAR DEFAULT 'unknown'",
            "assessment_state": "VARCHAR DEFAULT 'final'",
        },
        "macrobriefing": {
            "market_session": "VARCHAR DEFAULT 'unknown'",
            "assessment_state": "VARCHAR DEFAULT 'final'",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in table_columns.items():
            existing = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
            }
            if not existing:
                continue
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )


def init_db() -> None:
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _ensure_sqlite_columns()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
