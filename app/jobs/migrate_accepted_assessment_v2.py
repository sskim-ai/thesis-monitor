from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, MetaData, Table, create_engine, inspect, select

from app.models.accepted_assessment import (
    PERSISTENCE_V2_METADATA,
    PERSISTENCE_V2_TABLE_NAMES,
    PERSISTENCE_V2_TABLES,
    assessment_source_registry_v2,
)
from app.schemas.accepted_assessment_v2 import PersistenceSourceDomain
from app.services.accepted_assessment_persistence_service import (
    require_local_ephemeral_engine,
)
from app.services.assessment_source_registry_service import classify_legacy_assessment
from app.services.canonical_acceptance_receipt_service import canonical_sha256


MIGRATION_CONTRACT = "persistence-v2-forward-only-local-migration-v1"
MIGRATION_STRATEGY = "FORWARD_ONLY_DATA_PRESERVING"


@dataclass(frozen=True)
class PersistenceV2MigrationResult:
    contract: str
    strategy: str
    tables_created: tuple[str, ...]
    table_count: int
    legacy_registry_inserted: int
    legacy_registry_total: int
    schema_signature: str
    production_gate: str


def persistence_v2_schema_snapshot(engine: Engine) -> dict[str, object]:
    inspector = inspect(engine)
    rows: dict[str, object] = {}
    existing = set(inspector.get_table_names())
    for table_name in PERSISTENCE_V2_TABLE_NAMES:
        if table_name not in existing:
            rows[table_name] = {"missing": True}
            continue
        rows[table_name] = {
            "columns": [
                {
                    "name": row["name"],
                    "type": str(row["type"]),
                    "nullable": bool(row["nullable"]),
                    "primary_key": bool(row.get("primary_key")),
                }
                for row in inspector.get_columns(table_name)
            ],
            "indexes": sorted(
                (
                    {
                        "name": row.get("name"),
                        "column_names": row.get("column_names") or [],
                        "unique": bool(row.get("unique")),
                    }
                    for row in inspector.get_indexes(table_name)
                ),
                key=lambda item: str(item["name"]),
            ),
            "unique_constraints": sorted(
                (
                    {
                        "name": row.get("name"),
                        "column_names": row.get("column_names") or [],
                    }
                    for row in inspector.get_unique_constraints(table_name)
                ),
                key=lambda item: str(item["name"]),
            ),
            "foreign_keys": sorted(
                (
                    {
                        "name": row.get("name"),
                        "constrained_columns": row.get("constrained_columns") or [],
                        "referred_table": row.get("referred_table"),
                        "referred_columns": row.get("referred_columns") or [],
                    }
                    for row in inspector.get_foreign_keys(table_name)
                ),
                key=lambda item: (
                    str(item["referred_table"]),
                    str(item["constrained_columns"]),
                ),
            ),
            "check_constraints": sorted(
                (
                    {"name": row.get("name"), "sqltext": row.get("sqltext")}
                    for row in inspector.get_check_constraints(table_name)
                ),
                key=lambda item: str(item["name"]),
            ),
        }
    return {
        "contract": "persistence-v2-schema-introspection-v1",
        "tables": rows,
    }


def run_local_v2_migration(
    engine: Engine,
    *,
    allow_local_ephemeral: bool = False,
    classified_at: datetime | None = None,
) -> PersistenceV2MigrationResult:
    require_local_ephemeral_engine(engine, explicitly_enabled=allow_local_ephemeral)
    before = set(inspect(engine).get_table_names())
    PERSISTENCE_V2_METADATA.create_all(
        engine,
        tables=list(PERSISTENCE_V2_TABLES),
        checkfirst=True,
    )
    after = set(inspect(engine).get_table_names())
    created = tuple(sorted((after - before).intersection(PERSISTENCE_V2_TABLE_NAMES)))
    inserted = 0
    inspector = inspect(engine)
    if inspector.has_table("thesisassessment"):
        legacy = Table("thesisassessment", MetaData(), autoload_with=engine)
        with engine.begin() as connection:
            ids = tuple(connection.execute(select(legacy.c.id)).scalars())
            for assessment_id in ids:
                inserted += int(
                    classify_legacy_assessment(
                        connection,
                        assessment_id=int(assessment_id),
                        source_domain=PersistenceSourceDomain.LEGACY_UNVERIFIED,
                        classified_at=classified_at or datetime.now(UTC),
                    )
                )
    with engine.connect() as connection:
        total = connection.execute(
            select(assessment_source_registry_v2.c.legacy_assessment_id)
        ).all()
    snapshot = persistence_v2_schema_snapshot(engine)
    missing = [
        name
        for name, value in snapshot["tables"].items()
        if isinstance(value, dict) and value.get("missing")
    ]
    if missing:
        raise RuntimeError("persistence_v2_migration_missing_tables:" + ",".join(missing))
    return PersistenceV2MigrationResult(
        contract=MIGRATION_CONTRACT,
        strategy=MIGRATION_STRATEGY,
        tables_created=created,
        table_count=len(PERSISTENCE_V2_TABLE_NAMES),
        legacy_registry_inserted=inserted,
        legacy_registry_total=len(total),
        schema_signature=canonical_sha256(snapshot),
        production_gate="DISABLED_EXPLICIT_LOCAL_ONLY",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local-only Persistence V2 migration")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--allow-local-ephemeral", action="store_true")
    args = parser.parse_args()
    if not args.database_url.startswith("sqlite"):
        parser.error("only an explicitly authorized local SQLite URL is allowed")
    engine = create_engine(
        args.database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    result = run_local_v2_migration(
        engine,
        allow_local_ephemeral=args.allow_local_ephemeral,
    )
    print(json.dumps(asdict(result), sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
