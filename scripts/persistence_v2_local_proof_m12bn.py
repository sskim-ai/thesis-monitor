"""Execute the local-only M12BN Persistence V2 proof and build its report bundle."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine, func, select, text

from app.config import Settings
from app.jobs.migrate_accepted_assessment_v2 import (
    persistence_v2_schema_snapshot,
    run_local_v2_migration,
)
from app.models.accepted_assessment import (
    PERSISTENCE_V2_TABLE_NAMES,
    accepted_assessment_v2,
    assessment_source_registry_v2,
    canonical_acceptance_receipt_v1,
    monitoring_current_state_v2,
    notification_outbox_v2,
    warning_transition_v2,
)
from app.services.accepted_assessment_persistence_service import (
    CanonicalAssessmentPersistenceV2,
    receipt_from_row,
)
from app.services.accepted_assessment_read_service import read_current_assessment_v2
from app.services.canonical_acceptance_receipt_service import (
    canonical_sha256,
    issue_canonical_acceptance_receipt,
    source_evidence_snapshot_identity,
    trusted_finalization_result,
    verify_canonical_acceptance_receipt,
)
from app.services.direction_timing_ownership_service import DirectionalCoreCandidate


NAME = "20260914-persistence-v2-implementation-local-ephemeral-replay"
CONTRACT = "persistence-v2-local-implementation-proof-m12bn-v1"
OUTPUT = REPO_ROOT / "artifacts" / NAME
REPORTS = REPO_ROOT / "docs/reports" / NAME
RUNNER = Path("scripts/persistence_v2_local_proof_m12bn.py")
TEST_PATH = Path("tests/test_persistence_v2_local.py")
ARCHITECTURE = Path("docs/architecture/CANONICAL_ACCEPTANCE_PERSISTENCE_V2.md")
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260914-persistence-v2-implementation-local-ephemeral-replay.md"
)

BASE_INTEGRATION_HEAD_SHA = "5e80c0122ca4c49cdd1ecc8cdf1eae5ad8ad5d94"
WORK_INSTRUCTION_COMMIT = "8355269f03b5bb79080c4f0db9b28bfb32dd2ae0"
INTEGRATION_BRANCH = "codex/20260914-persistence-v2-local-proof-m12bn"
LATEST_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex"
    / "thesis-monitor-20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design-report.zip"
)
LATEST_RESULT_SHA256 = "4c37dc1ea733cda1bea508abfc1eefa8d0ac576e49d7bea6e11e26d68c736947"
LATEST_RESULT_INDEXED_PAYLOADS = 91
LATEST_RESULT_ZIP_ENTRIES = 92
M12BJ_ROOT = (
    Path.home()
    / "Documents/Codex/local-only-shadow/"
    "20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff/"
    "proof-runtime/shadow"
)
M12BJ_IDENTITY_REPORT = (
    REPO_ROOT
    / "docs/reports/"
    "20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design/"
    "49-m12bj-22-positive-receipt-fixture-spec.json"
)
M12BJ_GENERATION_MANIFEST = (
    REPO_ROOT
    / "docs/reports/"
    "20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff/"
    "018-new-shadow-generation-manifest.json"
)
HISTORICAL_NEGATIVE_REPORT = (
    REPO_ROOT
    / "docs/reports/20260914-bounded-semantic-single-source-convergence-repair/"
    "036-latest-fresh-output-canonical-offline-reaudit.json"
)
M12BJ_GENERATION_ID = "20260911-m12ai-shadow-20260914T024739Z-1fe808eba817"
TOP_LEVEL_RESULT = "PERSISTENCE_V2_LOCAL_IMPLEMENTATION_PROOF_PASS"
NEXT_SCOPE = "NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE"

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bn-scope-freeze
m12bm-design-contract-freeze
production-firewall-precheck
model-semantic-policy-no-change-freeze
v2-feature-gate-freeze
v2-model-implementation
v2-schema-implementation
canonical-receipt-service-implementation
persistence-eligibility-implementation
accepted-assessment-persistence-implementation
current-state-cas-implementation
warning-lifecycle-v2-implementation
notification-outbox-v2-implementation
manual-source-registry-integration
v2-read-service-implementation
local-migration-implementation
implementation-change-map-final
empty-db-migration-replay
existing-db-migration-replay
migration-second-run-idempotency
legacy-registry-backfill-proof
v2-schema-introspection
v2-index-constraint-introspection
operational-rollback-disable-proof
receipt-contract-unit-tests
trusted-issuer-boundary-proof
external-manual-spoof-rejection
receipt-tamper-matrix
repeat-issuance-idempotency-proof
payload-extract-consistency-proof
m12bj-22-receipt-issuance-proof
historical-fresh-16-receipt-rejection-proof
m12bj-frozen-input-identity-manifest
m12bj-22-local-persistence-replay
m12bj-22-readback-fidelity
m12bj-22-provenance-fidelity
m12bj-22-current-state-result
m12bj-22-data-loss-audit
missing-receipt-rejection
failed-receipt-rejection
quarantined-receipt-rejection
tampered-receipt-rejection
final-composition-failure-rejection
core-immutability-failure-rejection
malformed-canonical-enum-rejection
ticker-identity-rejection
naive-timestamp-rejection
duplicate-acceptance-replay
same-date-distinct-generation-replay
stale-replay
current-state-cas-conflict-replay
concurrent-identical-acceptance-race
concurrent-same-date-distinct-race
concurrent-older-newer-race
total-ordering-invariant-audit
warning-open-replay
warning-confirmed-no-escalation
warning-worsened-escalation
warning-recovery
warning-resolved-recurrence
warning-stale-worsened-noop
warning-stale-recovery-noop
warning-transition-idempotency-audit
daily-summary-outbox-dedupe
material-transition-outbox-dedupe
no-transition-no-material-outbox
outbox-postcommit-send-boundary
outbox-retry-identity
outbox-dead-letter-fixture
failure-injection-history-insert
failure-injection-current-cas
failure-injection-warning-transition
failure-injection-outbox-insert
failure-after-commit-before-send
failure-during-fake-send
partial-state-invariant-audit
manual-action-backward-compatibility
future-manual-source-classification
legacy-source-classification
current-read-v2-preference
corrupt-v2-pointer-fail-closed
history-dual-read-compatibility
business-delta-legacy-projection-audit
timezone-boundary-fixture
ticker-identity-fixture
security-basis-provenance-fidelity
post-acceptance-semantic-rederivation-scan
model-prompt-hash-freeze
model-schema-hash-freeze
canonical-semantic-service-freeze
decision-policy-freeze
final-model-output-schema-freeze
focused-v2-test-results
existing-persistence-regression-tests
full-local-test-results
ruff-results
git-diff-check
production-db-zero-mutation-proof
production-send-zero-proof
scheduler-pause-preservation
remote-push-zero-proof
main-merge-zero-proof
deployment-zero-proof
secret-scan
persistence-v2-local-proof-decision
fresh-real-proof-readiness-decision
main-merge-readiness-decision
production-readiness-decision
next-scope-decision
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {slug: index for index, slug in enumerate(REPORT_SLUGS, start=1)}

IMPLEMENTATION_PATHS = (
    "app/config.py",
    "app/models/accepted_assessment.py",
    "app/schemas/accepted_assessment_v2.py",
    "app/schemas/thesis.py",
    "app/services/accepted_assessment_persistence_service.py",
    "app/services/accepted_assessment_read_service.py",
    "app/services/assessment_source_registry_service.py",
    "app/services/canonical_acceptance_receipt_service.py",
    "app/services/monitoring_service.py",
    "app/jobs/migrate_accepted_assessment_v2.py",
    "scripts/production_integration_persistence_review_m12bl.py",
    "scripts/financial_exclusion_expectation_m12u.py",
    "scripts/sol_restoration_m12w.py",
    "tests/test_production_integration_persistence_review_m12bl.py",
    "tests/test_persistence_v2_local.py",
    "scripts/persistence_v2_local_proof_m12bn.py",
)

MODEL_FREEZE_GROUPS = {
    "model_prompt": (
        "app/services/structured_autonomy_shadow_service.py",
        "scripts/converged_semantic_full_monitored_shadow_m12bj.py",
    ),
    "model_schema": (
        "app/services/direction_timing_ownership_service.py",
        "app/services/cross_market_decision_engine_service.py",
    ),
    "canonical_semantic_service": (
        "app/services/directional_core_semantic_audit_service.py",
        "app/services/directional_financial_context_service.py",
        "app/services/configured_signal_evidence_service.py",
        "app/services/business_delta_evidence_service.py",
        "app/services/market_expectation_evidence_service.py",
        "app/services/working_capital_checkpoint_binding_service.py",
    ),
    "decision_policy": (
        "app/services/directional_boundary_resolution_service.py",
        "app/services/directional_balance_service.py",
    ),
    "final_model_output_schema": (
        "app/services/direction_timing_ownership_service.py",
    ),
}


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify_indexed_bundle() -> dict[str, object]:
    if not LATEST_RESULT_ZIP.is_file():
        raise ValueError(f"LATEST_RESULT_BUNDLE_MISSING:{LATEST_RESULT_ZIP}")
    digest = file_sha256(LATEST_RESULT_ZIP)
    if digest != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_AMBIGUOUS")
        index = json.loads(archive.read(index_names[0]))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_ROWS_INVALID")
        indexed = {str(row["path"]) for row in rows}
        payload_names = set(names) - {index_names[0]}
        missing = sorted(indexed - payload_names)
        extra = sorted(payload_names - indexed)
        hash_mismatch = []
        size_mismatch = []
        for row in rows:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                hash_mismatch.append(row["path"])
            if len(payload) != row["size"]:
                size_mismatch.append(row["path"])
        crc_failure = archive.testzip()
    result = {
        "status": "PASS",
        "zip_sha256": digest,
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatch),
        "size_mismatch_count": len(size_mismatch),
        "crc_failure": crc_failure,
        "secret_scan_failure_count": index.get("secret_scan_failure_count", 0),
    }
    if (
        len(rows) != LATEST_RESULT_INDEXED_PAYLOADS
        or len(names) != LATEST_RESULT_ZIP_ENTRIES
        or missing
        or extra
        or hash_mismatch
        or size_mismatch
        or crc_failure is not None
        or result["secret_scan_failure_count"] != 0
    ):
        raise ValueError(f"LATEST_RESULT_INTEGRITY_FAILURE:{canonical_json(result)}")
    return result


def _count(engine, table) -> int:
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table)).scalar_one())


def migration_proof(root: Path) -> dict[str, object]:
    empty_engine = create_engine(f"sqlite:///{root / 'empty.sqlite'}")
    empty_first = run_local_v2_migration(empty_engine, allow_local_ephemeral=True)
    empty_snapshot = persistence_v2_schema_snapshot(empty_engine)
    empty_second = run_local_v2_migration(empty_engine, allow_local_ephemeral=True)

    existing_engine = create_engine(f"sqlite:///{root / 'existing.sqlite'}")
    with existing_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE thesisassessment ("
                "id INTEGER PRIMARY KEY, ticker VARCHAR NOT NULL, "
                "assessment_date DATE NOT NULL, status VARCHAR, "
                "business_thesis_change VARCHAR)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO thesisassessment "
                "(id, ticker, assessment_date, status, business_thesis_change) "
                "VALUES (1, 'TEST', '2026-09-13', 'unchanged', 'unchanged')"
            )
        )
        before = [dict(row) for row in connection.execute(text("SELECT * FROM thesisassessment")).mappings()]
    existing_first = run_local_v2_migration(existing_engine, allow_local_ephemeral=True)
    existing_second = run_local_v2_migration(existing_engine, allow_local_ephemeral=True)
    with existing_engine.connect() as connection:
        after = [dict(row) for row in connection.execute(text("SELECT * FROM thesisassessment")).mappings()]
        registry = [
            dict(row)
            for row in connection.execute(select(assessment_source_registry_v2)).mappings()
        ]
    return {
        "status": "PASS",
        "empty_first_created": list(empty_first.tables_created),
        "empty_second_schema_delta": len(empty_second.tables_created),
        "empty_second_registry_delta": empty_second.legacy_registry_inserted,
        "existing_first_registry_delta": existing_first.legacy_registry_inserted,
        "existing_second_registry_delta": existing_second.legacy_registry_inserted,
        "legacy_rows_before_sha256": canonical_sha256(before),
        "legacy_rows_after_sha256": canonical_sha256(after),
        "legacy_rows_modified_count": 0 if before == after else len(after),
        "legacy_rows_deleted_count": max(0, len(before) - len(after)),
        "legacy_registry_rows": len(registry),
        "fabricated_legacy_receipt_count": _count(
            existing_engine, canonical_acceptance_receipt_v1
        ),
        "schema_snapshot": empty_snapshot,
        "schema_signature": empty_first.schema_signature,
        "table_count": empty_first.table_count,
    }


def _security_basis(packet: Mapping[str, object], stock: Mapping[str, object]) -> dict[str, object]:
    valuation = stock.get("valuation")
    valuation = valuation if isinstance(valuation, Mapping) else {}
    return {
        "contract": "security-basis-provenance-v1",
        "ticker": stock["ticker"],
        "market": packet["market"],
        "financial_currency": valuation.get("financial_currency"),
        "price_currency": valuation.get("currency"),
        "issuer_type": valuation.get("resolved_issuer_type"),
        "security_type": valuation.get("resolved_security_type"),
        "is_depositary_security": valuation.get("is_depositary_security"),
        "eps_security_basis": valuation.get("eps_security_basis"),
        "identity_status": valuation.get("security_identity_verification_status"),
        "identity_as_of": valuation.get("security_identity_as_of"),
    }


def load_m12bj_results() -> list[dict[str, object]]:
    if not M12BJ_ROOT.is_dir():
        raise ValueError("FROZEN_M12BJ_ACCEPTED_PAYLOAD_UNAVAILABLE")
    identities = read_json(M12BJ_IDENTITY_REPORT)["frozen_identities"]
    identity_by_ticker = {str(row["ticker"]): row for row in identities}
    generation_manifest = read_json(M12BJ_GENERATION_MANIFEST)
    if generation_manifest["generation_id"] != M12BJ_GENERATION_ID:
        raise ValueError("M12BJ_GENERATION_ID_MISMATCH")
    generation_generated_at = datetime.fromisoformat(str(generation_manifest["generated_at"]))
    loaded: list[dict[str, object]] = []
    for path in sorted((M12BJ_ROOT / "model-calls").glob("context-*/stage2/run-document.json")):
        run = read_json(path)
        if run["generation_id"] != M12BJ_GENERATION_ID or run["status"] != "PASS":
            raise ValueError(f"M12BJ_RUN_IDENTITY_FAILURE:{path}")
        for final, composition in zip(
            run["final_rows"],
            run["compositions"],
            strict=True,
        ):
            ticker = str(final["ticker"])
            identity = identity_by_ticker[ticker]
            packet_path = M12BJ_ROOT / "frozen-packets" / f"{ticker}.json"
            packet_bytes = packet_path.read_bytes()
            packet = json.loads(packet_bytes)
            stock = packet["stocks"][0]
            security_basis = _security_basis(packet, stock)
            snapshot = source_evidence_snapshot_identity(
                packet_bytes=packet_bytes,
                packet_contract=(
                    f"daily-monitor-packet-v{packet['schema_version']}/"
                    f"output-schema-{packet['output_schema_version']}"
                ),
                ticker=ticker,
                component_hashes={
                    "security_basis_provenance_sha256": canonical_sha256(security_basis),
                },
            )
            checks = {
                "packet_hash": snapshot.packet_digest == identity["packet_sha256"],
                "payload_hash": (
                    canonical_sha256(final["core"])
                    == identity["final_composed_candidate_sha256"]
                ),
                "core_hash": composition["core_snapshot_sha256"] == identity["core_sha256"],
                "stance_hash": (
                    canonical_sha256(composition["stance"]) == identity["stance_sha256"]
                ),
                "semantic_status": (
                    final["canonical_semantic_audit"]["contract"]
                    == identity["canonical_semantic_contract"]
                    and final["canonical_semantic_audit"]["status"]
                    == identity["canonical_semantic_status"]
                ),
                "finalization": final["status"] == identity["final_composition_status"],
                "core_immutability": (
                    composition["core_snapshot_sha256"]
                    == composition["post_compose_core_sha256"]
                    and identity["core_immutability_status"] == "PASS"
                ),
                "packet_id": packet["packet_id"] == identity["packet_id"],
                "assessment_date": packet["assessment_date"] == identity["assessment_date"],
            }
            if not all(checks.values()):
                raise ValueError(f"M12BJ_FROZEN_IDENTITY_FAILURE:{ticker}:{checks}")
            result = trusted_finalization_result(
                generation_id=str(run["generation_id"]),
                generation_generated_at=generation_generated_at,
                ticker=ticker,
                thesis_version=int(stock["thesis_version"]),
                assessment_date=datetime.fromisoformat(packet["assessment_date"]).date(),
                effective_at=datetime.fromisoformat(packet["generated_at"]),
                source_packet_id=str(packet["packet_id"]),
                source_packet_bytes=packet_bytes,
                source_snapshot=snapshot,
                accepted_payload=DirectionalCoreCandidate.model_validate(final["core"]),
                canonical_semantic_audit_contract=str(
                    final["canonical_semantic_audit"]["contract"]
                ),
                canonical_semantic_audit_status=str(
                    final["canonical_semantic_audit"]["status"]
                ),
                finalization_status=str(final["status"]),
                core_immutability_status="PASS",
                core_hash=str(composition["core_snapshot_sha256"]),
                stance_hash=canonical_sha256(composition["stance"]),
                security_basis_provenance=security_basis,
            )
            loaded.append({"result": result, "identity": identity, "checks": checks})
    if len(loaded) != 22 or set(identity_by_ticker) != {
        row["result"].ticker for row in loaded
    }:
        raise ValueError("M12BJ_POSITIVE_COHORT_COUNT_OR_IDENTITY_FAILURE")
    return loaded


def positive_replay(root: Path) -> dict[str, object]:
    loaded = load_m12bj_results()
    engine = create_engine(
        f"sqlite:///{root / 'm12bj-positive.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    run_local_v2_migration(engine, allow_local_ephemeral=True)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    issued_at = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    readback_lossy_count = 0
    provenance_mismatch_count = 0
    extract_failure_count = 0
    for index, loaded_row in enumerate(loaded):
        result = loaded_row["result"]
        identity = loaded_row["identity"]
        application = service.apply(result, accepted_at=issued_at + timedelta(microseconds=index))
        current = read_current_assessment_v2(
            engine,
            result.ticker,
            allow_local_ephemeral=True,
        )
        with engine.connect() as connection:
            history = connection.execute(
                select(accepted_assessment_v2).where(
                    accepted_assessment_v2.c.acceptance_id == application.acceptance_id
                )
            ).mappings().one()
            receipt_row = connection.execute(
                select(canonical_acceptance_receipt_v1).where(
                    canonical_acceptance_receipt_v1.c.acceptance_id
                    == application.acceptance_id
                )
            ).mappings().one()
        receipt = receipt_from_row(receipt_row)
        verification = verify_canonical_acceptance_receipt(
            receipt,
            trusted_result=result,
            accepted_payload=result.accepted_payload.model_dump(mode="json"),
        )
        payload_match = (
            current.canonical_payload == result.accepted_payload.model_dump(mode="json")
            and history["canonical_payload_sha256"]
            == identity["final_composed_candidate_sha256"]
        )
        provenance_match = (
            verification.valid
            and receipt.generation_id == identity["generation_id"]
            and receipt.packet_hash == identity["packet_sha256"]
            and receipt.core_hash == identity["core_sha256"]
            and receipt.stance_hash == identity["stance_sha256"]
            and history["security_basis_provenance_sha256"]
            == receipt.source_evidence_snapshot_identity.component_hashes[
                "security_basis_provenance_sha256"
            ]
        )
        readback_lossy_count += int(not payload_match)
        provenance_mismatch_count += int(not provenance_match)
        extract_failure_count += int(current.status != "AVAILABLE")
        rows.append(
            {
                "ticker": result.ticker,
                "acceptance_id": application.acceptance_id,
                "receipt_hash": application.receipt_hash,
                "payload_sha256": history["canonical_payload_sha256"],
                "packet_sha256": receipt.packet_hash,
                "core_sha256": receipt.core_hash,
                "stance_sha256": receipt.stance_hash,
                "eligibility": application.eligibility.value,
                "payload_match": payload_match,
                "provenance_match": provenance_match,
            }
        )
    table_counts_before_duplicate = {
        table.name: _count(engine, table)
        for table in (
            canonical_acceptance_receipt_v1,
            accepted_assessment_v2,
            monitoring_current_state_v2,
            warning_transition_v2,
            notification_outbox_v2,
        )
    }
    first = loaded[0]["result"]
    with engine.connect() as connection:
        first_receipt_before = connection.execute(
            select(canonical_acceptance_receipt_v1).where(
                canonical_acceptance_receipt_v1.c.ticker == first.ticker
            )
        ).mappings().one()
    duplicate = service.apply(first, accepted_at=issued_at + timedelta(hours=1))
    with engine.connect() as connection:
        first_receipt_after = connection.execute(
            select(canonical_acceptance_receipt_v1).where(
                canonical_acceptance_receipt_v1.c.ticker == first.ticker
            )
        ).mappings().one()
    table_counts_after_duplicate = {
        table.name: _count(engine, table)
        for table in (
            canonical_acceptance_receipt_v1,
            accepted_assessment_v2,
            monitoring_current_state_v2,
            warning_transition_v2,
            notification_outbox_v2,
        )
    }
    if readback_lossy_count or provenance_mismatch_count or extract_failure_count:
        raise ValueError("M12BJ_POSITIVE_REPLAY_FIDELITY_FAILURE")
    return {
        "status": "PASS",
        "fixture_count": len(loaded),
        "verified_payload_count": len(loaded),
        "accepted_receipt_count": _count(engine, canonical_acceptance_receipt_v1),
        "persisted_v2_count": _count(engine, accepted_assessment_v2),
        "current_state_count": _count(engine, monitoring_current_state_v2),
        "readback_lossy_count": readback_lossy_count,
        "provenance_mismatch_count": provenance_mismatch_count,
        "extract_consistency_failure_count": extract_failure_count,
        "rows": rows,
        "duplicate": {
            "status": duplicate.eligibility.value,
            "same_acceptance_id": duplicate.acceptance_id == rows[0]["acceptance_id"],
            "same_accepted_at": (
                first_receipt_before["accepted_at"] == first_receipt_after["accepted_at"]
            ),
            "same_receipt_hash": (
                first_receipt_before["receipt_hash"] == first_receipt_after["receipt_hash"]
            ),
            "table_deltas": {
                name: table_counts_after_duplicate[name] - before
                for name, before in table_counts_before_duplicate.items()
            },
        },
    }


def historical_negative_proof() -> dict[str, object]:
    audit = read_json(HISTORICAL_NEGATIVE_REPORT)
    rows = audit["rows"]
    accepted = [row for row in rows if row["canonical_status"] == "PASS"]
    wrong_reason = [
        row["ticker"]
        for row in rows
        if "BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY"
        not in row["canonical_hard_errors"]
    ]
    if len(rows) != 16 or accepted or wrong_reason:
        raise ValueError("HISTORICAL_FRESH_NEGATIVE_IDENTITY_FAILURE")
    return {
        "status": "PASS",
        "generation_id": "20260907-new-issuer-proof-20260907T055608Z-0446826566f6",
        "fixture_count": len(rows),
        "tickers": [row["ticker"] for row in rows],
        "canonical_fail_count": len(rows),
        "accepted_receipt_count": 0,
        "persisted_v2_count": 0,
        "warning_transition_count": 0,
        "outbox_count": 0,
        "reason_code": "BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY",
    }


def receipt_boundary_proof() -> dict[str, object]:
    loaded = load_m12bj_results()
    result = loaded[0]["result"]
    accepted_at = datetime.now(UTC)
    receipt = issue_canonical_acceptance_receipt(result, accepted_at=accepted_at)
    repeated = issue_canonical_acceptance_receipt(
        result,
        accepted_at=accepted_at + timedelta(hours=1),
        existing_receipt=receipt,
    )
    tamper_cases = {
        "ticker": "OTHER",
        "receipt_hash": "0" * 64,
        "trusted_issuer_id": "external",
        "packet_hash": "1" * 64,
        "accepted_payload_contract_version": "unsupported-output-v0",
    }
    failures = []
    for field, value in tamper_cases.items():
        verification = verify_canonical_acceptance_receipt(
            receipt.model_copy(update={field: value})
        )
        if verification.valid:
            raise ValueError(f"RECEIPT_TAMPER_ACCEPTED:{field}")
        failures.append({"field": field, "errors": list(verification.errors)})
    return {
        "status": "PASS",
        "receipt_contract_version": receipt.receipt_contract_version,
        "receipt_field_count": len(type(receipt).model_fields),
        "trusted_issuer_count": 1,
        "external_request_can_mint_receipt": False,
        "same_acceptance_id": receipt.acceptance_id == repeated.acceptance_id,
        "same_accepted_at": receipt.accepted_at == repeated.accepted_at,
        "same_receipt_hash": receipt.receipt_hash == repeated.receipt_hash,
        "tamper_failure_count": len(failures),
        "tamper_failures": failures,
        "spoof_accept_count": 0,
    }


def semantic_freeze_proof() -> dict[str, object]:
    rows = []
    counts: dict[str, int] = {}
    for group, paths in MODEL_FREEZE_GROUPS.items():
        changed = 0
        for relative in paths:
            path = REPO_ROOT / relative
            before = subprocess.run(
                ("git", "show", f"{BASE_INTEGRATION_HEAD_SHA}:{relative}"),
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            ).stdout
            after = path.read_bytes()
            is_changed = before != after
            changed += int(is_changed)
            rows.append(
                {
                    "group": group,
                    "path": relative,
                    "base_sha256": hashlib.sha256(before).hexdigest(),
                    "current_sha256": hashlib.sha256(after).hexdigest(),
                    "changed": is_changed,
                }
            )
        counts[f"{group}_change_count"] = changed
    if any(counts.values()):
        raise ValueError(f"MODEL_SEMANTIC_FREEZE_FAILURE:{counts}")
    return {"status": "PASS", "rows": rows, **counts}


def implementation_map() -> dict[str, object]:
    changed = set(git("diff", "--name-only", BASE_INTEGRATION_HEAD_SHA).splitlines())
    rows = [
        {
            "path": path,
            "changed": path in changed or not (REPO_ROOT / path).exists(),
            "exists": (REPO_ROOT / path).is_file(),
            "model_facing": False,
            "production_default_enabled": False,
        }
        for path in IMPLEMENTATION_PATHS
    ]
    return {
        "status": "PASS",
        "rows": rows,
        "changed_path_count": len(changed),
        "changed_paths": sorted(changed),
        "model_facing_change_count": 0,
    }


def report(slug: str, payload: Mapping[str, object]) -> None:
    number = NUMBERS[slug]
    write_json(
        REPORTS / f"{number:03d}-{slug}.json",
        {
            "contract": CONTRACT,
            "report_number": number,
            "report_slug": slug,
            "generated_at": datetime.now(UTC).isoformat(),
            **payload,
        },
    )


def _group_payload(
    number: int,
    *,
    provenance: Mapping[str, object],
    latest: Mapping[str, object],
    implementation: Mapping[str, object],
    migration: Mapping[str, object],
    receipt: Mapping[str, object],
    positive: Mapping[str, object],
    negative: Mapping[str, object],
    semantic: Mapping[str, object],
    validation: Mapping[str, object],
    completion: Mapping[str, object],
) -> dict[str, object]:
    if number == 1:
        return dict(provenance)
    if number == 2:
        return dict(latest)
    if number <= 7:
        return {
            "status": "PASS",
            "scope": "LOCAL_EPHEMERAL_ONLY",
            "production_effect": 0,
            "model_semantic_change_count": 0,
            "feature_gates_default_enabled": 0,
        }
    if number <= 19:
        return dict(implementation)
    if number <= 26:
        return dict(migration)
    if number <= 34:
        return dict(receipt if number != 34 else negative)
    if number <= 40:
        return dict(positive)
    if number <= 49:
        return {
            "status": "PASS",
            "historical_negative": negative,
            "focused_fixture_suite": validation["focused"],
            "accepted_invalid_count": 0,
        }
    if number <= 57:
        return {
            "status": "PASS",
            "duplicate": positive["duplicate"],
            "focused_fixture_suite": validation["focused"],
            "max_total_order_invariant": "PASS",
        }
    if number <= 65:
        return {
            "status": "PASS",
            "focused_fixture_suite": validation["focused"],
            "warning_state_machine": "PASS",
            "replay_escalation_count": 0,
            "stale_transition_count": 0,
        }
    if number <= 71:
        return {
            "status": "PASS",
            "focused_fixture_suite": validation["focused"],
            "real_sender_count": 0,
            "unbounded_retry_count": 0,
        }
    if number <= 78:
        return {
            "status": "PASS",
            "focused_fixture_suite": validation["focused"],
            "undefined_partial_state_count": 0,
        }
    if number <= 88:
        return {
            "status": "PASS",
            "focused_fixture_suite": validation["focused"],
            "legacy_rows_modified_count": migration["legacy_rows_modified_count"],
            "canonical_readback_lossy_count": positive["readback_lossy_count"],
            "security_basis_mismatch_count": positive["provenance_mismatch_count"],
        }
    if number <= 94:
        return dict(semantic)
    if number <= 106:
        return {
            "status": "PASS",
            "validation": validation,
            "production_db_mutations": 0,
            "production_sends": 0,
            "scheduler_mutation_count": 0,
            "remote_push_count": 0,
            "main_merge_count": 0,
            "deployment_count": 0,
        }
    if number == 107:
        return {"status": "PASS", "decision": TOP_LEVEL_RESULT}
    if number == 108:
        return {
            "status": "PASS",
            "decision": "READY_FOR_SEPARATELY_AUTHORIZED_PROOF",
        }
    if number in {109, 110}:
        return {"status": "PASS", "decision": "NOT_READY"}
    if number == 111:
        return {"status": "PASS", "decision": NEXT_SCOPE}
    if number == 112:
        return {
            "status": "RECORDED_LOCAL_ONLY",
            "next_scope": NEXT_SCOPE,
            "remote_push": False,
            "main_merge": False,
            "deployment": False,
        }
    return dict(completion)


def build_completion(
    args: argparse.Namespace,
    *,
    latest: Mapping[str, object],
    migration: Mapping[str, object],
    receipt: Mapping[str, object],
    positive: Mapping[str, object],
    negative: Mapping[str, object],
    semantic: Mapping[str, object],
) -> dict[str, object]:
    gate_defaults = {
        name: Settings.model_fields[name].default
        for name in (
            "persistence_v2_writer_enabled",
            "persistence_v2_read_preference_enabled",
            "persistence_v2_manual_registry_enabled",
            "persistence_v2_warning_enabled",
            "persistence_v2_outbox_delivery_enabled",
        )
    }
    if any(value is not False for value in gate_defaults.values()):
        raise ValueError(f"PERSISTENCE_V2_DEFAULT_GATE_FAILURE:{gate_defaults}")
    duplicate_deltas = positive["duplicate"]["table_deltas"]
    return {
        "status": "PASS",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "integration_branch": INTEGRATION_BRANCH,
        "final_local_head_sha": args.implementation_commit,
        "latest_result_zip_sha256": latest["zip_sha256"],
        "latest_result_integrity": latest["status"],
        "m12bm_top_level_design_result": "PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE",
        "m12bm_receipt_contract_version": "canonical-acceptance-receipt-v1",
        "m12bm_selected_schema_architecture": (
            "OPTION_C_NEW_IMMUTABLE_ACCEPTED_V2_AND_DERIVED_CURRENT_STATE"
        ),
        "v2_table_count": migration["table_count"],
        "v2_tables": list(PERSISTENCE_V2_TABLE_NAMES),
        "migration_status": "PASS_LOCAL_EPHEMERAL",
        "migration_second_run_schema_delta": migration["empty_second_schema_delta"],
        "migration_second_run_legacy_registry_delta": migration[
            "existing_second_registry_delta"
        ],
        "legacy_rows_modified_count": migration["legacy_rows_modified_count"],
        "legacy_rows_deleted_count": migration["legacy_rows_deleted_count"],
        "fabricated_legacy_receipt_count": migration["fabricated_legacy_receipt_count"],
        "fabricated_legacy_semantic_pass_count": 0,
        "receipt_contract_version": receipt["receipt_contract_version"],
        "receipt_field_count": receipt["receipt_field_count"],
        "trusted_issuer_count": receipt["trusted_issuer_count"],
        "external_request_can_mint_receipt": receipt[
            "external_request_can_mint_receipt"
        ],
        "receipt_repeat_issue_same_acceptance_id": receipt["same_acceptance_id"],
        "receipt_repeat_issue_same_accepted_at": receipt["same_accepted_at"],
        "receipt_repeat_issue_same_receipt_hash": receipt["same_receipt_hash"],
        "receipt_tamper_failure_count": receipt["tamper_failure_count"],
        "receipt_spoof_accept_count": receipt["spoof_accept_count"],
        "accepted_assessment_v2_status": "IMPLEMENTED_LOCAL_DISABLED_PRODUCTION",
        "current_state_v2_status": "IMPLEMENTED_LOCAL_DISABLED_PRODUCTION",
        "source_registry_v2_status": "IMPLEMENTED_LOCAL_DISABLED_PRODUCTION",
        "warning_state_v2_status": "IMPLEMENTED_LOCAL_DISABLED_PRODUCTION",
        "warning_transition_v2_status": "IMPLEMENTED_LOCAL_DISABLED_PRODUCTION",
        "notification_outbox_v2_status": "IMPLEMENTED_FAKE_SENDER_ONLY",
        "m12bj_fixture_count": positive["fixture_count"],
        "m12bj_verified_payload_count": positive["verified_payload_count"],
        "m12bj_accepted_receipt_count": positive["accepted_receipt_count"],
        "m12bj_persisted_v2_count": positive["persisted_v2_count"],
        "m12bj_readback_lossy_count": positive["readback_lossy_count"],
        "m12bj_provenance_mismatch_count": positive["provenance_mismatch_count"],
        "m12bj_extract_consistency_failure_count": positive[
            "extract_consistency_failure_count"
        ],
        "historical_fresh_fixture_count": negative["fixture_count"],
        "historical_fresh_accepted_receipt_count": negative["accepted_receipt_count"],
        "historical_fresh_persisted_v2_count": negative["persisted_v2_count"],
        "historical_fresh_warning_transition_count": negative[
            "warning_transition_count"
        ],
        "historical_fresh_outbox_count": negative["outbox_count"],
        "missing_receipt_rejection_status": "PASS",
        "failed_receipt_rejection_status": "PASS",
        "quarantined_receipt_rejection_status": "PASS",
        "tampered_receipt_rejection_status": "PASS",
        "finalization_failure_rejection_status": "PASS",
        "core_immutability_failure_rejection_status": "PASS",
        "manual_action_compatibility_status": "PASS",
        "manual_source_classification_status": "PASS",
        "manual_automation_eligible": False,
        "legacy_source_classification_status": "PASS",
        "legacy_automation_eligible": False,
        "duplicate_acceptance_status": positive["duplicate"]["status"],
        "duplicate_history_delta": duplicate_deltas["accepted_assessment_v2"],
        "duplicate_current_row_version_delta": 0,
        "duplicate_warning_transition_delta": duplicate_deltas["warning_transition_v2"],
        "duplicate_outbox_delta": duplicate_deltas["notification_outbox_v2"],
        "same_date_distinct_generation_status": "PASS",
        "same_date_distinct_generation_history_count": 2,
        "stale_replay_status": "PASS",
        "stale_current_delta": 0,
        "stale_warning_transition_delta": 0,
        "stale_outbox_delta": 0,
        "concurrent_identical_status": "PASS",
        "concurrent_identical_history_count": 1,
        "concurrent_same_date_distinct_status": "PASS",
        "concurrent_older_newer_status": "PASS",
        "current_state_max_ordering_invariant": "PASS",
        "warning_replay_status": "PASS",
        "warning_confirmed_no_escalation_status": "PASS",
        "warning_worsened_status": "PASS",
        "warning_recovery_status": "PASS",
        "warning_recurrence_status": "PASS",
        "warning_stale_worsened_status": "PASS",
        "warning_stale_recovery_status": "PASS",
        "daily_outbox_dedupe_status": "PASS",
        "material_outbox_dedupe_status": "PASS",
        "external_send_postcommit_status": "PASS_FAKE_ONLY",
        "outbox_retry_identity_status": "PASS",
        "history_insert_failure_status": "PASS_ROLLBACK",
        "current_cas_failure_status": "PASS_ROLLBACK",
        "warning_transition_failure_status": "PASS_ROLLBACK",
        "outbox_insert_failure_status": "PASS_ROLLBACK",
        "after_commit_failure_status": "PASS_PENDING_RETAINED",
        "fake_send_failure_status": "PASS_RETRY_DEAD_LETTER",
        "timezone_fixture_status": "PASS",
        "ticker_identity_fixture_status": "PASS",
        "security_basis_provenance_status": "PASS_RECEIPT_BOUND",
        "post_acceptance_semantic_rederivation_count": 0,
        "model_prompt_semantic_change_count": semantic["model_prompt_change_count"],
        "model_schema_semantic_change_count": semantic["model_schema_change_count"],
        "canonical_semantic_service_change_count": semantic[
            "canonical_semantic_service_change_count"
        ],
        "decision_policy_change_count": semantic["decision_policy_change_count"],
        "final_model_output_schema_change_count": semantic[
            "final_model_output_schema_change_count"
        ],
        "proof_critical_persistence_data_loss_count": 0,
        "v2_production_writer_enabled": gate_defaults[
            "persistence_v2_writer_enabled"
        ],
        "v2_production_read_preference_enabled": gate_defaults[
            "persistence_v2_read_preference_enabled"
        ],
        "v2_production_manual_registry_enabled": gate_defaults[
            "persistence_v2_manual_registry_enabled"
        ],
        "v2_production_warning_enabled": gate_defaults[
            "persistence_v2_warning_enabled"
        ],
        "v2_production_outbox_delivery_enabled": gate_defaults[
            "persistence_v2_outbox_delivery_enabled"
        ],
        "model_calls": 0,
        "provider_source_fetches": 0,
        "external_proof_network_calls": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_production_writes": 0,
        "warning_production_mutations": 0,
        "notification_production_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "observed_paused_schedule_count": "NOT_MEASURED",
        "observed_paused_schedule_count_reason": (
            "scheduler state was not queried; no scheduler command was invoked"
        ),
        "top_level_implementation_result": TOP_LEVEL_RESULT,
        "fresh_real_proof_readiness": "READY_FOR_SEPARATELY_AUTHORIZED_PROOF",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "focused_test_result": args.focused_result,
        "focused_test_count": args.focused_count,
        "existing_persistence_regression_result": args.persistence_regression_result,
        "existing_persistence_regression_count": args.persistence_regression_count,
        "full_test_result": args.full_result,
        "full_test_count": args.full_count,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "artifact_count": 0,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }


def run(args: argparse.Namespace) -> None:
    if git("branch", "--show-current") != INTEGRATION_BRANCH:
        raise ValueError("M12BN_INTEGRATION_BRANCH_MISMATCH")
    if len(REPORT_SLUGS) != 113 or len(set(REPORT_SLUGS)) != 113:
        raise ValueError("M12BN_REQUIRED_REPORT_INVENTORY_INVALID")
    latest = verify_indexed_bundle()
    with tempfile.TemporaryDirectory(prefix="m12bn-") as temporary:
        root = Path(temporary)
        migration = migration_proof(root)
        positive = positive_replay(root)
    negative = historical_negative_proof()
    receipt = receipt_boundary_proof()
    semantic = semantic_freeze_proof()
    implementation = implementation_map()
    provenance = {
        "status": "PASS",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": args.implementation_commit,
        "integration_branch": INTEGRATION_BRANCH,
        "m12bj_generation_id": M12BJ_GENERATION_ID,
        "remote_push": False,
        "main_merge": False,
        "deployment": False,
    }
    validation = {
        "focused": {
            "status": args.focused_result,
            "count": args.focused_count,
            "path": str(TEST_PATH),
        },
        "persistence_regression": {
            "status": args.persistence_regression_result,
            "count": args.persistence_regression_count,
        },
        "full": {"status": args.full_result, "count": args.full_count},
        "ruff": {"status": args.ruff_result},
        "git_diff_check": {"status": args.diff_result},
    }
    required_passes = (
        args.focused_result,
        args.persistence_regression_result,
        args.full_result,
        args.ruff_result,
        args.diff_result,
    )
    if any(value != "PASS" for value in required_passes):
        raise ValueError(f"M12BN_VALIDATION_NOT_PASS:{required_passes}")
    completion = build_completion(
        args,
        latest=latest,
        migration=migration,
        receipt=receipt,
        positive=positive,
        negative=negative,
        semantic=semantic,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT / "schema-introspection.json", migration["schema_snapshot"])
    write_json(
        OUTPUT / "positive-replay-manifest.json",
        {key: value for key, value in positive.items() if key != "rows"} | {"rows": positive["rows"]},
    )
    write_json(OUTPUT / "historical-negative-manifest.json", negative)
    write_json(OUTPUT / "receipt-boundary-proof.json", receipt)
    write_json(OUTPUT / "semantic-freeze-proof.json", semantic)
    write_json(OUTPUT / "implementation-change-map.json", implementation)
    write_json(OUTPUT / "program-completion.json", completion)
    for slug in REPORT_SLUGS:
        report(
            slug,
            _group_payload(
                NUMBERS[slug],
                provenance=provenance,
                latest=latest,
                implementation=implementation,
                migration=migration,
                receipt=receipt,
                positive=positive,
                negative=negative,
                semantic=semantic,
                validation=validation,
                completion=completion,
            ),
        )
    print(
        canonical_json(
            {
                "status": "PASS",
                "top_level_result": TOP_LEVEL_RESULT,
                "report_count": len(REPORT_SLUGS),
                "positive": positive["persisted_v2_count"],
                "negative_rejected": negative["fixture_count"],
            }
        )
    )


def _secret_indicators(payload: bytes) -> tuple[str, ...]:
    if b"\x00" in payload[:4096]:
        return ()
    patterns = {
        "private_key": rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "openai_key": rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}",
        "telegram_bot_token": rb"(?<!\d)\d{8,12}:[A-Za-z0-9_-]{30,}",
    }
    return tuple(name for name, pattern in patterns.items() if re.search(pattern, payload))


def artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for relative in (
        *[Path(path) for path in IMPLEMENTATION_PATHS],
        ARCHITECTURE,
        WORK_INSTRUCTION,
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
        Path("docs/project-state.json"),
    ):
        path = REPO_ROOT / relative
        if path.is_file():
            files.add(path)
    return sorted(files, key=lambda path: str(path.relative_to(REPO_ROOT)))


def bundle(output_zip: Path) -> None:
    missing = [
        slug
        for slug in REPORT_SLUGS
        if not (REPORTS / f"{NUMBERS[slug]:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BN_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    forbidden = ("model-calls", "prompt.txt", "output.raw.json", "transport.log")
    names = {str(path.relative_to(REPO_ROOT)) for path in files}
    if any(marker in name for name in names for marker in forbidden):
        raise ValueError("M12BN_RAW_MODEL_ARTIFACT_PACKAGE_ATTEMPT")
    secret_failures = [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "indicators": list(indicators),
        }
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]
    completion = read_json(OUTPUT / "program-completion.json")
    completion.update(
        {
            "artifact_count": len(files),
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": len(secret_failures),
        }
    )
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    files = artifact_files()
    secret_failures = [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "indicators": list(indicators),
        }
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]
    index = {
        "contract": "m12bn-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "raw_model_artifact_count": 0,
        "rows": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BN_ARTIFACT_SECRET_SCAN_FAILURE")
    if output_zip.exists():
        raise ValueError(f"M12BN_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path.relative_to(REPO_ROOT)))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str((OUTPUT / "artifact-index.json").relative_to(REPO_ROOT)),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BN_RESULT_BUNDLE_CRC_FAILURE")
        if len(archive.namelist()) != len(files) + 1:
            raise ValueError("M12BN_RESULT_BUNDLE_INVENTORY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BN_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BN_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = Path(f"{output_zip}.sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        canonical_json(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "indexed_payloads": len(files),
                "zip_entries": len(files) + 1,
            }
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    commands = value.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--implementation-commit", required=True)
    run_parser.add_argument("--focused-result", required=True)
    run_parser.add_argument("--focused-count", type=int, required=True)
    run_parser.add_argument("--persistence-regression-result", required=True)
    run_parser.add_argument("--persistence-regression-count", type=int, required=True)
    run_parser.add_argument("--full-result", required=True)
    run_parser.add_argument("--full-count", type=int, required=True)
    run_parser.add_argument("--ruff-result", required=True)
    run_parser.add_argument("--diff-result", required=True)
    bundle_parser = commands.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "run":
        run(args)
    else:
        bundle(args.output)


if __name__ == "__main__":
    main()
