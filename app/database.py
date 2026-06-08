from collections.abc import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, **({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool} if settings.database_url == "sqlite://" else {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {}))


def _ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    table_columns = {
        "watchlistitem": {"active": "BOOLEAN DEFAULT 1"},
        "event": {
            "raw_summary": "VARCHAR",
            "provider": "VARCHAR DEFAULT 'unknown'",
            "capex_impact_known": "BOOLEAN DEFAULT 0",
            "inventory_risk": "BOOLEAN DEFAULT 0",
            "receivables_risk": "BOOLEAN DEFAULT 0",
        },
        "financialsnapshot": {
            "fcf": "FLOAT",
            "accounts_receivable": "FLOAT",
            "stock_based_compensation": "FLOAT",
            "source": "VARCHAR",
            "provider": "VARCHAR",
            "fs_div": "VARCHAR",
            "sj_div": "VARCHAR",
            "revenue_basis": "VARCHAR",
            "operating_income_basis": "VARCHAR",
            "balance_sheet_basis": "VARCHAR",
            "quality_warnings": "VARCHAR",
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
    SQLModel.metadata.create_all(engine)
    _ensure_sqlite_columns()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
