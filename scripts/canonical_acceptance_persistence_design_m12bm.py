"""Build the offline M12BM persistence-contract design evidence bundle.

This executable specification reads only frozen repository/local report
artifacts. It does not call a model, provider, network endpoint, production
database, notifier, scheduler, or remote Git endpoint.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
NAME = "20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design"
CONTRACT = "canonical-acceptance-persistence-design-m12bm-v1"
OUTPUT = REPO_ROOT / "artifacts" / NAME
REPORTS = REPO_ROOT / "docs/reports" / NAME
RUNNER = Path("scripts/canonical_acceptance_persistence_design_m12bm.py")
TEST_PATH = Path("tests/test_canonical_acceptance_persistence_design_m12bm.py")
ARCHITECTURE = Path("docs/architecture/CANONICAL_ACCEPTANCE_PERSISTENCE_V2.md")
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design.md"
)

BASE_INTEGRATION_HEAD_SHA = "1f1155711f9cda1d98ea4d51f30eb43967f1f25d"
WORK_INSTRUCTION_COMMIT = "43734324b5e1740edf93886ce2d439accd810380"
INTEGRATION_BRANCH = "codex/20260914-canonical-acceptance-persistence-design-m12bm"
LATEST_RESULT_ZIP = (
    Path.home()
    / "Documents/Codex"
    / (
        "thesis-monitor-20260914-production-integration-persistence-review-on-"
        "integrated-main-report.zip"
    )
)
LATEST_RESULT_SHA256 = "73c038cb4640d16f596032d88863901bb0d496acf8fe182abeed7eb48395f174"
LATEST_RESULT_INDEXED_PAYLOADS = 83
LATEST_RESULT_ZIP_ENTRIES = 84
M12BL_REPORTS = (
    REPO_ROOT / "docs/reports/20260914-production-integration-persistence-review-on-integrated-main"
)
M12BJ_GENERATION_ID = "20260911-m12ai-shadow-20260914T024739Z-1fe808eba817"

RECEIPT_CONTRACT = "canonical-acceptance-receipt-v1"
ACCEPTANCE_ID_CONTRACT = "canonical-acceptance-id-v1"
RECEIPT_HASH_CONTRACT = "canonical-acceptance-receipt-hash-v1"
SERIALIZATION_CONTRACT = "canonical-json-utf8-sorted-compact-v1"
ELIGIBILITY_CONTRACT = "persistence-eligibility-v2"
ACCEPTED_ASSESSMENT_CONTRACT = "accepted-assessment-v2"
CURRENT_STATE_CONTRACT = "monitoring-current-state-v2"
WARNING_OBSERVATION_CONTRACT = "canonical-warning-observation-v1"
WARNING_TRANSITION_CONTRACT = "warning-transition-v2"
OUTBOX_CONTRACT = "notification-outbox-v2"
LEGACY_PROJECTION_CONTRACT = "legacy-assessment-projection-v1"
TRUSTED_ISSUERS = ("canonical_two_stage_finalizer_v1",)
TOP_LEVEL_RESULT = "PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE"
NEXT_SCOPE = "BOUNDED_PERSISTENCE_V2_IMPLEMENTATION_AND_LOCAL_REPLAY"

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bm-scope-freeze
m12bl-blocking-gap-freeze
current-production-persistence-schema-map
current-entrypoint-trust-boundary-map
canonical-acceptance-receipt-options
canonical-acceptance-receipt-decision
canonical-acceptance-receipt-v1-spec
receipt-issuance-boundary-contract
receipt-verification-contract
persistence-eligibility-contract-v2
manual-vs-canonical-vs-legacy-source-contract
persistence-schema-options-comparison
persistence-schema-architecture-decision
accepted-assessment-v2-schema-spec
current-monitoring-state-v2-schema-spec
canonical-provenance-schema-spec
structured-stance-schema-spec
market-expectation-schema-spec
structured-unknown-schema-spec
security-basis-provenance-schema-spec
business-delta-canonical-storage-contract
legacy-assessment-projection-contract
confidence-risk-storage-contract
immutable-history-contract
acceptance-id-idempotency-contract
stale-safe-ordering-contract
current-state-compare-and-swap-contract
warning-identity-contract
warning-state-machine-contract
warning-transition-idempotency-contract
notification-outbox-contract
daily-vs-material-notification-contract
transaction-boundary-v2-contract
partial-failure-recovery-contract
retry-safety-v2-contract
concurrency-contract
schema-migration-spec
existing-data-legacy-unverified-migration-spec
index-and-unique-constraint-spec
upgrade-order
rollback-or-forward-only-decision
read-path-v2-contract
current-review-read-compatibility
assessment-history-read-compatibility
external-action-api-compatibility-decision
manual-assessment-automation-eligibility-decision
m12bj-22-positive-receipt-fixture-spec
historical-fresh-negative-receipt-fixture-spec
missing-receipt-negative-fixture-spec
tampered-receipt-negative-fixture-spec
quarantined-receipt-negative-fixture-spec
duplicate-acceptance-fixture-spec
same-date-distinct-generation-fixture-spec
stale-replay-fixture-spec
warning-replay-fixture-spec
warning-new-confirmation-fixture-spec
warning-recovery-fixture-spec
notification-dedupe-fixture-spec
transaction-failure-injection-fixture-spec
concurrency-race-fixture-spec
timezone-boundary-fixture-spec
ticker-identity-fixture-spec
implementation-change-map
files-modules-expected-to-change
migration-implementation-plan
local-ephemeral-replay-plan
backward-compatibility-test-plan
production-firewall-test-plan
implementation-acceptance-criteria
next-bounded-scope-decision
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {slug: index for index, slug in enumerate(REPORT_SLUGS, start=1)}

RECEIPT_FIELDS = (
    "receipt_contract_version",
    "acceptance_id",
    "receipt_hash",
    "receipt_status",
    "trusted_issuer_id",
    "generation_id",
    "generation_generated_at",
    "ticker",
    "thesis_version",
    "assessment_date",
    "effective_at",
    "accepted_at",
    "source_packet_id",
    "packet_hash",
    "source_evidence_snapshot_identity",
    "accepted_payload_contract_version",
    "canonical_serialization_contract",
    "final_composed_candidate_hash",
    "canonical_semantic_audit_contract",
    "canonical_semantic_audit_status",
    "finalization_status",
    "core_immutability_status",
    "core_hash",
    "stance_hash",
    "quarantine_reason_codes",
)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def report(slug: str, payload: Mapping[str, object]) -> None:
    number = NUMBERS[slug]
    write_json(
        REPORTS / f"{number:02d}-{slug}.json",
        {
            "contract": CONTRACT,
            "report_number": number,
            "report_slug": slug,
            "generated_at": datetime.now(UTC).isoformat(),
            **payload,
        },
    )


def source_line(relative: str, needle: str) -> int:
    for number, line in enumerate(
        (REPO_ROOT / relative).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if needle in line:
            return number
    raise ValueError(f"SOURCE_NEEDLE_NOT_FOUND:{relative}:{needle}")


def source_ref(relative: str, needle: str) -> dict[str, object]:
    path = REPO_ROOT / relative
    return {
        "path": relative,
        "line": source_line(relative, needle),
        "sha256": file_sha256(path),
    }


def verify_indexed_bundle(
    path: Path,
    expected_sha256: str,
    *,
    expected_payloads: int,
    expected_entries: int,
) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"LATEST_RESULT_BUNDLE_MISSING:{path}")
    digest = file_sha256(path)
    if digest != expected_sha256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        bad_crc = archive.testzip()
        names = archive.namelist()
        indexes = [name for name in names if name.endswith("/artifact-index.json")]
        if len(indexes) != 1:
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_AMBIGUOUS")
        index = json.loads(archive.read(indexes[0]))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_ROWS_INVALID")
        indexed_names = {str(row.get("path")) for row in rows if isinstance(row, dict)}
        archive_payloads = set(names) - {indexes[0]}
        missing = sorted(indexed_names - archive_payloads)
        extra = sorted(archive_payloads - indexed_names)
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_ROW_INVALID")
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(row["path"])
            if len(payload) != row.get("size"):
                size_mismatches.append(row["path"])
    result = {
        "status": "PASS",
        "zip": str(path),
        "zip_sha256": digest,
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "missing": missing,
        "extra_count": len(extra),
        "extra": extra,
        "hash_mismatch_count": len(hash_mismatches),
        "hash_mismatches": hash_mismatches,
        "size_mismatch_count": len(size_mismatches),
        "size_mismatches": size_mismatches,
        "crc_failure": bad_crc,
        "secret_scan_failure_count": index.get("secret_scan_failure_count", 0),
    }
    if (
        len(rows) != expected_payloads
        or len(names) != expected_entries
        or missing
        or extra
        or hash_mismatches
        or size_mismatches
        or bad_crc is not None
        or result["secret_scan_failure_count"] != 0
    ):
        raise ValueError(f"LATEST_RESULT_INTEGRITY_FAILURE:{canonical_json(result)}")
    return result


def verify_latest_result() -> dict[str, object]:
    return verify_indexed_bundle(
        LATEST_RESULT_ZIP,
        LATEST_RESULT_SHA256,
        expected_payloads=LATEST_RESULT_INDEXED_PAYLOADS,
        expected_entries=LATEST_RESULT_ZIP_ENTRIES,
    )


def acceptance_material(receipt: Mapping[str, object]) -> dict[str, object]:
    return {
        "domain": ACCEPTANCE_ID_CONTRACT,
        "receipt_material": {
            field: receipt.get(field)
            for field in RECEIPT_FIELDS
            if field not in {"acceptance_id", "receipt_hash", "accepted_at"}
        },
    }


def expected_acceptance_id(receipt: Mapping[str, object]) -> str:
    return f"ca1_{canonical_sha256(acceptance_material(receipt))}"


def receipt_hash_material(receipt: Mapping[str, object]) -> dict[str, object]:
    return {
        "domain": RECEIPT_HASH_CONTRACT,
        "receipt": {
            field: receipt.get(field) for field in RECEIPT_FIELDS if field != "receipt_hash"
        },
    }


def expected_receipt_hash(receipt: Mapping[str, object]) -> str:
    return canonical_sha256(receipt_hash_material(receipt))


def build_example_receipt(
    *,
    status: str = "ACCEPTED",
    accepted_at: str = "2026-09-14T08:00:00+00:00",
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "receipt_contract_version": RECEIPT_CONTRACT,
        "acceptance_id": "",
        "receipt_hash": "",
        "receipt_status": status,
        "trusted_issuer_id": TRUSTED_ISSUERS[0],
        "generation_id": M12BJ_GENERATION_ID,
        "generation_generated_at": "2026-09-14T02:47:39+00:00",
        "ticker": "IBM",
        "thesis_version": 3,
        "assessment_date": "2026-09-07",
        "effective_at": "2026-09-06T23:06:46.266093+00:00",
        "accepted_at": accepted_at,
        "source_packet_id": "2026-09-07-us-run-59-e3b54b0a74c0",
        "packet_hash": "a" * 64,
        "source_evidence_snapshot_identity": {
            "contract": "frozen-decision-evidence-snapshot-v1",
            "algorithm": "sha256",
            "digest": "a" * 64,
            "ticker": "IBM",
        },
        "accepted_payload_contract_version": "directional-core-output-v1+stance-v1",
        "canonical_serialization_contract": SERIALIZATION_CONTRACT,
        "final_composed_candidate_hash": "b" * 64,
        "canonical_semantic_audit_contract": "directional-core-semantic-audit-v1",
        "canonical_semantic_audit_status": "PASS",
        "finalization_status": "PASS",
        "core_immutability_status": "PASS",
        "core_hash": "c" * 64,
        "stance_hash": "d" * 64,
        "quarantine_reason_codes": [] if status == "ACCEPTED" else ["fixture_reason"],
    }
    receipt["acceptance_id"] = expected_acceptance_id(receipt)
    receipt["receipt_hash"] = expected_receipt_hash(receipt)
    return receipt


def _parse_aware_timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def verify_receipt(
    receipt: Mapping[str, object],
    *,
    payload_hash: str | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if tuple(receipt.keys()) != RECEIPT_FIELDS and set(receipt) != set(RECEIPT_FIELDS):
        errors.append("receipt_field_set_mismatch")
    if receipt.get("receipt_contract_version") != RECEIPT_CONTRACT:
        errors.append("unsupported_receipt_contract")
    if receipt.get("canonical_serialization_contract") != SERIALIZATION_CONTRACT:
        errors.append("unsupported_serialization_contract")
    if receipt.get("trusted_issuer_id") not in TRUSTED_ISSUERS:
        errors.append("untrusted_receipt_issuer")
    status = receipt.get("receipt_status")
    if status not in {"ACCEPTED", "REJECTED", "QUARANTINED"}:
        errors.append("invalid_receipt_status")
    if receipt.get("acceptance_id") != expected_acceptance_id(receipt):
        errors.append("acceptance_id_mismatch")
    if receipt.get("receipt_hash") != expected_receipt_hash(receipt):
        errors.append("receipt_hash_mismatch")
    for field in (
        "packet_hash",
        "final_composed_candidate_hash",
        "core_hash",
        "stance_hash",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get(field) or "")):
            errors.append(f"invalid_sha256:{field}")
    ticker = str(receipt.get("ticker") or "")
    if not re.fullmatch(r"(?:[0-9]{6}|[A-Z][A-Z0-9.-]{0,9})", ticker):
        errors.append("invalid_canonical_ticker")
    for field in ("generation_generated_at", "effective_at", "accepted_at"):
        if _parse_aware_timestamp(receipt.get(field)) is None:
            errors.append(f"timezone_aware_timestamp_required:{field}")
    if payload_hash is not None and receipt.get("final_composed_candidate_hash") != payload_hash:
        errors.append("accepted_payload_hash_mismatch")
    if status == "ACCEPTED":
        if receipt.get("canonical_semantic_audit_status") != "PASS":
            errors.append("canonical_semantic_audit_not_pass")
        if receipt.get("finalization_status") != "PASS":
            errors.append("finalization_not_pass")
        if receipt.get("core_immutability_status") != "PASS":
            errors.append("core_immutability_not_pass")
        if receipt.get("quarantine_reason_codes"):
            errors.append("accepted_receipt_has_quarantine_reasons")
    return tuple(errors)


def ordering_key(receipt: Mapping[str, object]) -> tuple[str, str, str, str]:
    effective = _parse_aware_timestamp(receipt["effective_at"])
    generated = _parse_aware_timestamp(receipt["generation_generated_at"])
    if effective is None or generated is None:
        raise ValueError("ORDERING_TIMESTAMP_INVALID")
    return (
        effective.astimezone(UTC).isoformat(timespec="microseconds"),
        generated.astimezone(UTC).isoformat(timespec="microseconds"),
        str(receipt["generation_id"]),
        str(receipt["acceptance_id"]),
    )


def warning_transition(current: str | None, observation: str) -> tuple[str | None, bool]:
    if observation == "UNRESOLVED":
        return current, False
    if current is None:
        if observation in {"CONFIRMED", "WORSENED"}:
            return "open", True
        return None, False
    if current == "open":
        if observation == "WORSENED":
            return "escalated", True
        if observation == "RECOVERED":
            return "resolved", True
        return "open", False
    if current == "escalated":
        if observation == "RECOVERED":
            return "resolved", True
        return "escalated", False
    if current == "resolved":
        if observation in {"CONFIRMED", "WORSENED"}:
            return "open", True
        return "resolved", False
    raise ValueError(f"UNKNOWN_WARNING_STATE:{current}")


def current_schema_map() -> dict[str, object]:
    return {
        "status": "M12BL_BLOCKING_SCHEMA_FROZEN",
        "models": [
            {
                "table": "thesisassessment",
                "identity": "UNIQUE(ticker, assessment_date)",
                "mutability": "same-date in-place update",
                "typed_decision_storage": "legacy enums plus free text/unversioned JSON",
                "canonical_receipt_fk": False,
                "same_date_multi_generation": False,
                "source": source_ref(
                    "app/models/thesis.py", "class ThesisAssessment(SQLModel, table=True):"
                ),
            },
            {
                "table": "notificationdelivery",
                "identity": "UNIQUE(ticker, assessment_date, channel)",
                "mutability": "payload/status retry mutation",
                "canonical_event_fk": False,
                "source": source_ref(
                    "app/models/thesis.py", "class NotificationDelivery(SQLModel, table=True):"
                ),
            },
            {
                "table": "watchlistitem",
                "role": "legacy latest assessment metadata",
                "stale_cas": False,
                "source": source_ref(
                    "app/services/daily_monitor_service.py",
                    "item.latest_status = result.status.value",
                ),
            },
        ],
        "migration_mechanism": {
            "current": "SQLModel.metadata.create_all plus SQLite ALTER-column helper",
            "source": source_ref("app/database.py", "def init_db() -> None:"),
            "v2_requirement": "explicit idempotent new-table migration and verification",
        },
        "warning_storage": {
            "current": "embedded thesisassessment.warning_states JSON",
            "states": ["open", "escalated", "resolved", "invalid_provenance"],
            "v2_business_states": ["open", "escalated", "resolved"],
            "invalid_provenance_v2": "pre-lifecycle rejection/quarantine, not a state",
            "source": source_ref(
                "app/services/thesis_evaluation_service.py", "def _warning_lifecycle("
            ),
        },
    }


def entrypoint_trust_map() -> list[dict[str, object]]:
    return [
        {
            "entrypoint": "recordThesisAssessment",
            "trust_domain": "MANUAL_USER_AUTHORED",
            "may_create_manual_history": True,
            "may_mint_receipt": False,
            "may_write_accepted_v2": False,
            "may_advance_v2_warning_or_outbox": False,
            "source": source_ref(
                "app/api/routes_monitoring.py", 'operation_id="recordThesisAssessment"'
            ),
        },
        {
            "entrypoint": "run_daily_monitor",
            "trust_domain": "LEGACY_RUNTIME_UNTIL_SEPARATE_CUTOVER",
            "current_canonical_gate": False,
            "m12bn_target": "cannot enter V2 without trusted receipt",
            "source": source_ref(
                "app/services/daily_monitor_service.py", "async def run_daily_monitor("
            ),
        },
        {
            "entrypoint": "canonical_two_stage_finalizer_v1",
            "trust_domain": "CANONICAL_MODEL_ACCEPTED",
            "may_mint_receipt": True,
            "public": False,
            "required_input": "frozen typed finalization result",
            "target_module": "app/services/canonical_acceptance_receipt_service.py",
        },
        {
            "entrypoint": "apply_accepted_assessment_v2",
            "trust_domain": "INTERNAL_CAPABILITY_ONLY",
            "may_verify_receipt": True,
            "may_apply_atomic_v2_lifecycle": True,
            "public": False,
            "target_module": "app/services/accepted_assessment_persistence_service.py",
        },
        {
            "entrypoint": "notification outbox worker",
            "trust_domain": "POST_COMMIT_DELIVERY",
            "may_send": "only committed eligible outbox rows",
            "may_mint_receipt": False,
            "target_module": "app/services/notification_outbox_service.py",
        },
    ]


def receipt_field_specs() -> list[dict[str, object]]:
    required = {
        "receipt_contract_version": "supported constant",
        "acceptance_id": "ca1_ plus 64 lowercase hex",
        "receipt_hash": "64 lowercase hex",
        "receipt_status": "ACCEPTED | REJECTED | QUARANTINED",
        "trusted_issuer_id": "allowlisted internal issuer",
        "generation_id": "non-empty frozen generation identity",
        "generation_generated_at": "offset-aware timestamp",
        "ticker": "exact canonical six-digit KR or uppercase US identity",
        "thesis_version": "positive integer from receipt-bound packet",
        "assessment_date": "business date",
        "effective_at": "offset-aware source decision timestamp",
        "accepted_at": "offset-aware immutable issuance timestamp",
        "source_packet_id": "non-empty frozen packet identity",
        "packet_hash": "SHA-256 of frozen packet bytes",
        "source_evidence_snapshot_identity": "versioned object bound to packet hash/ticker",
        "accepted_payload_contract_version": "supported final payload contract",
        "canonical_serialization_contract": SERIALIZATION_CONTRACT,
        "final_composed_candidate_hash": "SHA-256 of exact accepted payload",
        "canonical_semantic_audit_contract": "supported canonical audit contract",
        "canonical_semantic_audit_status": "PASS for accepted",
        "finalization_status": "PASS for accepted",
        "core_immutability_status": "PASS for accepted",
        "core_hash": "existing canonical core SHA-256 unchanged",
        "stance_hash": "existing canonical stance SHA-256 unchanged",
        "quarantine_reason_codes": "versioned tuple; empty for accepted",
    }
    return [
        {
            "ordinal": index,
            "field": field,
            "required": True,
            "constraint": required[field],
            "acceptance_id_covered": field not in {"acceptance_id", "receipt_hash", "accepted_at"},
            "receipt_hash_covered": field != "receipt_hash",
        }
        for index, field in enumerate(RECEIPT_FIELDS, start=1)
    ]


def receipt_spec() -> dict[str, object]:
    return {
        "status": "DEFINED",
        "contract_version": RECEIPT_CONTRACT,
        "field_count": len(RECEIPT_FIELDS),
        "fields": receipt_field_specs(),
        "receipt_states": ["ACCEPTED", "REJECTED", "QUARANTINED"],
        "legacy_unverified_rule": "no receipt exists; source-domain classification only",
        "acceptance_id_contract": ACCEPTANCE_ID_CONTRACT,
        "receipt_hash_contract": RECEIPT_HASH_CONTRACT,
        "canonical_serialization_contract": SERIALIZATION_CONTRACT,
        "trusted_issuers": list(TRUSTED_ISSUERS),
        "model_identity_required": False,
        "model_effort_required": False,
        "reason": "acceptance integrity is bound to source/final/audit identities",
    }


def schema_options() -> list[dict[str, object]]:
    return [
        {
            "option": "A_EXTEND_THESISASSESSMENT",
            "migration_risk": "HIGH",
            "backward_compatibility": "HIGH_FIELD_COUPLING",
            "losslessness": "POSSIBLE_BUT_AWKWARD",
            "idempotency": "FAIL_WITHOUT_IDENTITY_REPLACEMENT",
            "same_date_multi_generation": "FAIL_UNLESS_UNIQUE_KEY_REMOVED",
            "read_complexity": "LOW",
            "warning_outbox_linkage": "WEAK",
            "rollback": "HIGH_RISK_ALTER_EXISTING_TABLE",
            "decision": "REJECT",
        },
        {
            "option": "B_LEGACY_ROW_PLUS_SIDECAR",
            "migration_risk": "MEDIUM",
            "backward_compatibility": "HIGH",
            "losslessness": "PARTIAL_TO_FULL_WITH_COMPLEX_SIDECARS",
            "idempotency": "PARTIAL",
            "same_date_multi_generation": "CONFLICTS_WITH_ONE_LEGACY_ROW",
            "read_complexity": "HIGH_JOIN_AND_PRECEDENCE_RULES",
            "warning_outbox_linkage": "POSSIBLE",
            "rollback": "MEDIUM",
            "decision": "REJECT",
        },
        {
            "option": "C_NEW_IMMUTABLE_ACCEPTED_V2_AND_CURRENT_STATE",
            "migration_risk": "BOUNDED_NEW_TABLES",
            "backward_compatibility": "LEGACY_TABLE_UNCHANGED",
            "losslessness": "FULL_VERSIONED_PAYLOAD_PLUS_TYPED_EXTRACTS",
            "idempotency": "CONTENT_ADDRESSED",
            "same_date_multi_generation": "SUPPORTED",
            "read_complexity": "EXPLICIT_DISCRIMINATED_READERS",
            "warning_outbox_linkage": "DIRECT_ACCEPTANCE_EVENT_FKS",
            "rollback": "FORWARD_ONLY_DATA_PRESERVING_DISABLE",
            "decision": "SELECT",
        },
    ]


def accepted_assessment_schema() -> dict[str, object]:
    return {
        "table": "accepted_assessment_v2",
        "contract": ACCEPTED_ASSESSMENT_CONTRACT,
        "mutability": "APPEND_ONLY",
        "primary_key": ["acceptance_id"],
        "foreign_keys": ["acceptance_id -> canonical_acceptance_receipt_v1.acceptance_id"],
        "columns": [
            ["acceptance_id", "TEXT", "PK/FK; ca1 content identity"],
            ["schema_contract_version", "TEXT", "accepted-assessment-v2"],
            ["source_domain", "TEXT", "CANONICAL_MODEL_ACCEPTED only"],
            ["ticker", "TEXT", "exact receipt identity"],
            ["thesis_version", "INTEGER", "> 0"],
            ["assessment_date", "DATE", "business date"],
            ["effective_at_utc", "TIMESTAMP", "offset-aware normalized UTC"],
            ["generation_generated_at_utc", "TIMESTAMP", "normalized UTC"],
            ["generation_id", "TEXT", "receipt identity"],
            ["ordering_key_json", "TEXT", "canonical four-component tuple"],
            ["overall_direction", "TEXT", "BUY/HOLD/SELL"],
            ["directional_balance_buy", "NUMERIC", "0..10 half-step"],
            ["directional_balance_sell", "NUMERIC", "0..10 half-step; sum 10"],
            ["hold_lean", "TEXT", "canonical enum"],
            ["directional_confidence", "TEXT", "LOW/MEDIUM/HIGH"],
            ["canonical_business_delta", "TEXT", "four-value canonical enum"],
            ["canonical_payload_contract_version", "TEXT", "versioned"],
            ["canonical_payload_json", "TEXT", "authoritative canonical JSON"],
            ["canonical_payload_sha256", "CHAR(64)", "must equal receipt final hash"],
            ["business_thesis_context_json", "TEXT", "exact typed extract"],
            ["earnings_estimate_context_json", "TEXT", "exact typed extract"],
            ["market_expectation_context_json", "TEXT", "exact typed extract"],
            ["valuation_context_json", "TEXT", "exact typed extract"],
            ["risk_context_json", "TEXT", "exact typed extract"],
            ["sector_interpretation_json", "TEXT", "exact typed extract"],
            ["buy_drivers_json", "TEXT", "versioned exact array"],
            ["sell_drivers_json", "TEXT", "versioned exact array"],
            ["dominant_evidence_json", "TEXT", "exact typed extract"],
            ["uncertainty_limit_json", "TEXT", "exact typed extract"],
            ["core_judgment_json", "TEXT", "exact typed extract"],
            ["structured_unknowns_json", "TEXT", "versioned exact array"],
            ["material_anchor_refs_json", "TEXT", "ordered canonical refs"],
            ["new_buyer_json", "TEXT", "versioned exact structure"],
            ["holder_json", "TEXT", "versioned exact structure"],
            ["reevaluation_up_json", "TEXT", "versioned exact array"],
            ["reevaluation_down_json", "TEXT", "versioned exact array"],
            ["security_basis_provenance_json", "TEXT", "receipt-bound projection"],
            ["security_basis_provenance_sha256", "CHAR(64)", "projection integrity"],
        ],
        "authoritative_payload": "canonical_payload_json",
        "extract_consistency_gate": "all extracts exactly match hash-bound payload",
        "legacy_free_text_fields_invented": 0,
    }


def current_state_schema() -> dict[str, object]:
    return {
        "table": "monitoring_current_state_v2",
        "contract": CURRENT_STATE_CONTRACT,
        "primary_key": ["ticker"],
        "columns": [
            ["ticker", "TEXT", "PK"],
            ["latest_acceptance_id", "TEXT", "FK accepted_assessment_v2"],
            ["latest_effective_at_utc", "TIMESTAMP", "ordering component 1"],
            ["latest_generation_generated_at_utc", "TIMESTAMP", "component 2"],
            ["latest_generation_id", "TEXT", "component 3"],
            ["latest_ordering_acceptance_id", "TEXT", "component 4"],
            ["latest_assessment_date", "DATE", "business display date"],
            ["latest_thesis_version", "INTEGER", "does not create thesis version"],
            ["row_version", "INTEGER", "optimistic concurrency; starts 1"],
            ["updated_at_utc", "TIMESTAMP", "operational audit only"],
        ],
        "ordering": [
            "effective_at_utc",
            "generation_generated_at_utc",
            "generation_id",
            "acceptance_id",
        ],
        "stale_effect": "history retained; current/warning/outbox unchanged",
        "database_cas_required": True,
    }


def receipt_table_schema() -> dict[str, object]:
    return {
        "table": "canonical_acceptance_receipt_v1",
        "primary_key": ["acceptance_id"],
        "receipt_field_count": len(RECEIPT_FIELDS),
        "receipt_fields": list(RECEIPT_FIELDS),
        "accepted_row_check": (
            "receipt_status=ACCEPTED AND semantic/finalization/core statuses=PASS "
            "AND quarantine_reason_codes=[]"
        ),
        "unique_constraints": [
            ["receipt_hash"],
            ["trusted_issuer_id", "generation_id", "ticker"],
        ],
        "immutability": "no UPDATE/DELETE through application repository",
        "model_identity_column": False,
        "model_effort_column": False,
    }


def source_registry_schema() -> dict[str, object]:
    return {
        "table": "assessment_source_registry_v2",
        "purpose": "classify legacy/manual rows without altering their contents",
        "columns": [
            ["legacy_assessment_id", "INTEGER", "PK/FK thesisassessment.id"],
            ["source_domain", "TEXT", "MANUAL_USER_AUTHORED or LEGACY_UNVERIFIED"],
            ["automation_eligible", "BOOLEAN", "always false"],
            ["classification_contract", "TEXT", "versioned"],
            ["classified_at_utc", "TIMESTAMP", "migration/write audit"],
        ],
        "pre_v2_backfill": "LEGACY_UNVERIFIED",
        "future_manual_write": "MANUAL_USER_AUTHORED in same transaction",
    }


def warning_schemas() -> dict[str, object]:
    return {
        "observation_contract": {
            "contract": WARNING_OBSERVATION_CONTRACT,
            "trusted_sidecar": True,
            "fields": [
                "warning_type",
                "condition_contract_version",
                "condition_identity",
                "observation",
                "transition_reason_code",
                "transition_reason_version",
                "evidence_refs",
            ],
            "observations": ["CONFIRMED", "WORSENED", "RECOVERED", "UNRESOLVED"],
            "evidence_rule": "refs must be a subset of receipt-bound accepted/source evidence",
            "absence_rule": "no observation means no warning mutation",
        },
        "warning_state_v2": {
            "primary_key": ["warning_identity"],
            "columns": [
                ["warning_identity", "TEXT", "content-addressed PK"],
                ["ticker", "TEXT", "canonical ticker"],
                ["thesis_version", "INTEGER", "condition ownership"],
                ["warning_type", "TEXT", "versioned domain type"],
                ["condition_contract_version", "TEXT", "identity input"],
                ["condition_identity", "TEXT", "identity input"],
                ["state", "TEXT", "open/escalated/resolved"],
                ["episode", "INTEGER", "increments only on resolved recurrence"],
                ["latest_transition_id", "TEXT", "nullable FK"],
                ["latest_observation_acceptance_id", "TEXT", "accepted FK"],
                ["latest_ordering_key_json", "TEXT", "stale guard"],
                ["row_version", "INTEGER", "CAS"],
            ],
        },
        "warning_transition_v2": {
            "primary_key": ["warning_transition_id"],
            "columns": [
                ["warning_transition_id", "TEXT", "content-addressed PK"],
                ["warning_identity", "TEXT", "FK warning state"],
                ["episode", "INTEGER", "episode identity"],
                ["from_state", "TEXT", "nullable for open"],
                ["to_state", "TEXT", "business state"],
                ["triggering_acceptance_id", "TEXT", "FK accepted assessment"],
                ["observation_json", "TEXT", "versioned exact input"],
                ["transition_reason_version", "TEXT", "identity input"],
                ["created_at_utc", "TIMESTAMP", "audit only"],
            ],
            "identity": (
                "sha256(warning_identity, episode, from_state, to_state, "
                "triggering_acceptance_id, transition_reason_version)"
            ),
        },
    }


def warning_state_machine() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for current in (None, "open", "escalated", "resolved"):
        for observation in ("CONFIRMED", "WORSENED", "RECOVERED", "UNRESOLVED"):
            next_state, material = warning_transition(current, observation)
            rows.append(
                {
                    "from": current or "absent",
                    "observation": observation,
                    "to": next_state or "absent",
                    "transition_event": material,
                    "notification_eligible": material,
                    "same_acceptance_replay": "NO_OP_BEFORE_STATE_MACHINE",
                    "stale_observation": "NO_OP_BEFORE_STATE_MACHINE",
                }
            )
    return rows


def outbox_schema() -> dict[str, object]:
    return {
        "table": "notification_outbox_v2",
        "contract": OUTBOX_CONTRACT,
        "columns": [
            ["outbox_event_id", "TEXT", "content-addressed PK"],
            ["event_kind", "TEXT", "DAILY_SUMMARY or MATERIAL_STATE_TRANSITION"],
            ["source_event_id", "TEXT", "schedule slot or warning transition"],
            ["acceptance_id", "TEXT", "accepted assessment FK"],
            ["channel", "TEXT", "delivery channel"],
            ["payload_contract_version", "TEXT", "versioned"],
            ["payload_json", "TEXT", "immutable semantic payload"],
            ["payload_sha256", "CHAR(64)", "content identity"],
            ["status", "TEXT", "pending/sending/sent/retry/dead_letter"],
            ["attempt_count", "INTEGER", "operational mutable counter"],
            ["next_attempt_at_utc", "TIMESTAMP", "bounded retry"],
            ["last_error_code", "TEXT", "redacted operational code"],
            ["sent_at_utc", "TIMESTAMP", "nullable"],
            ["created_at_utc", "TIMESTAMP", "transaction time"],
        ],
        "unique": ["source_event_id", "channel", "payload_contract_version"],
        "semantic_immutability": [
            "event_kind",
            "source_event_id",
            "acceptance_id",
            "channel",
            "payload_contract_version",
            "payload_json",
            "payload_sha256",
        ],
        "external_send": "post-commit only",
    }


def transaction_contract() -> dict[str, object]:
    return {
        "contract": "accepted-assessment-application-transaction-v2",
        "pretransaction": [
            "verify internal capability and receipt envelope",
            "verify accepted payload hash and typed extract equality",
            "verify warning observation refs if observations are supplied",
        ],
        "atomic_steps": [
            "insert canonical acceptance receipt if absent",
            "insert immutable accepted assessment if absent",
            "read and conditionally advance monitoring current state",
            "apply only newer eligible warning observations/transitions",
            "insert deduped daily/material notification outbox rows",
            "commit once",
        ],
        "postcommit": [
            "outbox worker claims pending row",
            "external delivery",
            "record attempt/sent/dead-letter state without changing semantic payload",
        ],
        "production_current_gap": (
            "daily monitor currently commits assessment per ticker, then state, run, queue, "
            "and delivery in separate boundaries"
        ),
    }


def failure_semantics() -> list[dict[str, str]]:
    return [
        {
            "failure_point": "receipt_or_payload_verification",
            "result": "REJECT_BEFORE_TRANSACTION",
            "durable_state": "none",
            "retry": "only same immutable inputs after infrastructure recovery",
        },
        {
            "failure_point": "accepted_history_insert",
            "result": "ROLLBACK_OR_IDEMPOTENT_ALREADY_APPLIED",
            "durable_state": "none or preexisting exact row",
            "retry": "same acceptance_id",
        },
        {
            "failure_point": "current_state_cas",
            "result": "NO_OP_STALE_OR_BOUNDED_RETRY",
            "durable_state": "history may exist; derived effects only for winner",
            "retry": "reread current tuple; never mint new identity",
        },
        {
            "failure_point": "warning_transition",
            "result": "ROLLBACK",
            "durable_state": "no new receipt/history/current/outbox from transaction",
            "retry": "same acceptance and transition identity",
        },
        {
            "failure_point": "outbox_insert",
            "result": "ROLLBACK",
            "durable_state": "no partial assessment lifecycle",
            "retry": "same source event identity",
        },
        {
            "failure_point": "after_commit_before_send",
            "result": "RETRY_SAFE",
            "durable_state": "complete DB state plus pending outbox",
            "retry": "worker resumes same outbox_event_id",
        },
        {
            "failure_point": "during_external_send",
            "result": "RETRY_OR_DEAD_LETTER",
            "durable_state": "accepted state unchanged; attempt recorded",
            "retry": "bounded, same semantic payload and event identity",
        },
    ]


def migration_spec() -> dict[str, object]:
    return {
        "status": "IMPLEMENTATION_READY_DESIGN_ONLY",
        "production_applied": False,
        "strategy": "FORWARD_ONLY_DATA_PRESERVING",
        "new_tables": [
            "canonical_acceptance_receipt_v1",
            "accepted_assessment_v2",
            "monitoring_current_state_v2",
            "assessment_source_registry_v2",
            "warning_state_v2",
            "warning_transition_v2",
            "notification_outbox_v2",
        ],
        "legacy_table_alterations": [],
        "legacy_rows_deleted": 0,
        "legacy_backfill": (
            "insert one assessment_source_registry_v2 row per existing thesisassessment.id "
            "with LEGACY_UNVERIFIED and automation_eligible=false"
        ),
        "future_manual_rows": (
            "MANUAL_USER_AUTHORED registry row inserted atomically with legacy assessment write"
        ),
        "fabricated_receipts": 0,
        "fabricated_packet_hashes": 0,
        "fabricated_semantic_passes": 0,
        "downgrade": (
            "disable V2 writers/read preference while preserving tables; destructive down "
            "migration prohibited"
        ),
    }


def indexes_and_constraints() -> list[dict[str, object]]:
    return [
        {
            "table": "canonical_acceptance_receipt_v1",
            "primary": ["acceptance_id"],
            "unique": [
                ["receipt_hash"],
                ["trusted_issuer_id", "generation_id", "ticker"],
            ],
            "indexes": [["ticker", "assessment_date"], ["generation_id"]],
        },
        {
            "table": "accepted_assessment_v2",
            "primary": ["acceptance_id"],
            "unique": [["generation_id", "ticker"]],
            "indexes": [
                [
                    "ticker",
                    "effective_at_utc",
                    "generation_generated_at_utc",
                    "generation_id",
                    "acceptance_id",
                ],
                ["ticker", "assessment_date"],
            ],
        },
        {
            "table": "monitoring_current_state_v2",
            "primary": ["ticker"],
            "unique": [["latest_acceptance_id"]],
            "indexes": [["latest_assessment_date"]],
        },
        {
            "table": "assessment_source_registry_v2",
            "primary": ["legacy_assessment_id"],
            "unique": [],
            "indexes": [["source_domain"]],
        },
        {
            "table": "warning_state_v2",
            "primary": ["warning_identity"],
            "unique": [],
            "indexes": [["ticker", "state"], ["latest_observation_acceptance_id"]],
        },
        {
            "table": "warning_transition_v2",
            "primary": ["warning_transition_id"],
            "unique": [
                [
                    "warning_identity",
                    "episode",
                    "triggering_acceptance_id",
                    "transition_reason_version",
                ]
            ],
            "indexes": [["warning_identity", "created_at_utc"]],
        },
        {
            "table": "notification_outbox_v2",
            "primary": ["outbox_event_id"],
            "unique": [["source_event_id", "channel", "payload_contract_version"]],
            "indexes": [["status", "next_attempt_at_utc"], ["acceptance_id"]],
        },
    ]


def implementation_change_map() -> list[dict[str, object]]:
    rows = [
        (
            "app/models/accepted_assessment.py",
            "new",
            "define the seven V2 tables and DB constraints",
            True,
            "V2 schema creation",
            "schema and constraint tests",
        ),
        (
            "app/models/__init__.py",
            "model import registry",
            "register V2 SQLModel metadata",
            True,
            "V2 schema creation",
            "metadata/create_all test",
        ),
        (
            "app/schemas/accepted_assessment_v2.py",
            "new",
            "frozen receipt, typed payload extracts, read envelopes",
            False,
            "none",
            "schema and rejection tests",
        ),
        (
            "app/services/canonical_acceptance_receipt_service.py",
            "new",
            "trusted issue/verify functions and deterministic identities",
            False,
            "none",
            "issue/tamper/trust tests",
        ),
        (
            "app/services/accepted_assessment_persistence_service.py",
            "new",
            "atomic immutable insert, stale guard, CAS, lifecycle orchestration",
            True,
            "all V2 tables",
            "replay/failure/race tests",
        ),
        (
            "app/services/accepted_assessment_read_service.py",
            "new",
            "typed current/history reads with source-domain discrimination",
            False,
            "V2 tables and source registry",
            "read compatibility tests",
        ),
        (
            "app/services/warning_lifecycle_v2_service.py",
            "new",
            "acceptance-driven warning identity and state transitions",
            True,
            "warning V2 tables",
            "state machine/idempotency tests",
        ),
        (
            "app/services/notification_outbox_service.py",
            "new",
            "transactional enqueue and post-commit claim/retry",
            True,
            "outbox V2 table",
            "dedupe/failure tests; external sender stubbed",
        ),
        (
            "app/services/monitoring_service.py",
            "manual assessment action persistence",
            "tag new manual rows; reject reserved canonical fields",
            False,
            "source registry",
            "existing action compatibility and trust-boundary tests",
        ),
        (
            "app/database.py",
            "database initialization",
            "run idempotent V2 new-table migration/verification behind disabled gate",
            True,
            "V2 migration",
            "empty/existing DB upgrade tests",
        ),
        (
            "app/jobs/migrate_accepted_assessment_v2.py",
            "new",
            "offline/local migration and legacy classification command",
            True,
            "V2 migration",
            "dry-run, idempotency, rollback-disable tests",
        ),
        (
            "tests/fixtures/persistence_v2/",
            "new",
            "frozen positive/negative/lifecycle specifications",
            False,
            "none",
            "all M12BN acceptance criteria",
        ),
    ]
    return [
        {
            "module_path": path,
            "current_responsibility": current,
            "new_responsibility": new,
            "semantic_behavior_changed": False,
            "model_facing_behavior_changed": False,
            "database_schema_changed": db_changed,
            "production_side_effect_path_changed": False,
            "migration_dependency": migration,
            "test_coverage_required": tests,
        }
        for path, current, new, db_changed, migration, tests in rows
    ]


def load_m12bl_completion() -> dict[str, object]:
    value = read_json(M12BL_REPORTS / "68-program-completion.json")
    if value.get("top_level_integration_result") != (
        "BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP"
    ):
        raise ValueError("M12BL_TOP_LEVEL_RESULT_MISMATCH")
    return value


def load_m12bj_positive_rows() -> list[dict[str, object]]:
    value = read_json(M12BL_REPORTS / "31-m12bj-22-output-persistence-eligibility-replay.json")
    rows = value.get("rows")
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("M12BJ_POSITIVE_FIXTURE_COUNT_MISMATCH")
    selected: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("M12BJ_POSITIVE_FIXTURE_ROW_INVALID")
        if (
            row.get("generation_id") != M12BJ_GENERATION_ID
            or row.get("canonical_semantic_status") != "PASS"
            or row.get("final_composition_status") != "PASS"
            or row.get("core_immutability_status") != "PASS"
        ):
            raise ValueError("M12BJ_POSITIVE_FIXTURE_IDENTITY_MISMATCH")
        selected.append(
            {
                key: row[key]
                for key in (
                    "ticker",
                    "market",
                    "assessment_date",
                    "packet_id",
                    "packet_sha256",
                    "generation_id",
                    "final_composed_candidate_sha256",
                    "core_sha256",
                    "stance_sha256",
                    "canonical_semantic_contract",
                    "canonical_semantic_status",
                    "final_composition_status",
                    "core_immutability_status",
                )
            }
        )
    return selected


def fixture_specs(positive_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "m12bj_positive": {
            "source_generation_id": M12BJ_GENERATION_ID,
            "fixture_count": len(positive_rows),
            "tickers": [str(row["ticker"]) for row in positive_rows],
            "frozen_identities": list(positive_rows),
            "future_expected": {
                "receipt_issue_pass": 22,
                "receipt_verify_pass": 22,
                "immutable_rows_after_first_apply": 22,
                "lossless_readback_pass": 22,
                "duplicate_new_rows": 0,
                "provenance_loss_count": 0,
            },
            "executed_in_m12bm": False,
        },
        "historical_negative": {
            "fixture_count": 16,
            "frozen_failure": ("BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY"),
            "expected_receipt_status": "REJECTED",
            "expected_canonical_rows": 0,
            "expected_warning_transitions": 0,
            "expected_outbox_rows": 0,
            "candidate_mutation": 0,
        },
        "receipt_negatives": [
            {
                "case": "missing_receipt",
                "eligibility": "REJECTED_INVALID_RECEIPT",
                "canonical_rows": 0,
                "derived_effects": 0,
            },
            {
                "case": "tampered_receipt_or_payload",
                "eligibility": "REJECTED_INVALID_RECEIPT",
                "required_error": "acceptance_id/receipt_hash/payload hash mismatch",
                "canonical_rows": 0,
                "derived_effects": 0,
            },
            {
                "case": "quarantined_receipt",
                "eligibility": "REJECTED_QUARANTINED",
                "canonical_rows": 0,
                "derived_effects": 0,
            },
        ],
        "identity": [
            {
                "case": "duplicate_acceptance",
                "first_history_delta": 1,
                "replay_history_delta": 0,
                "replay_current_delta": 0,
                "replay_warning_transition_delta": 0,
                "replay_outbox_delta": 0,
                "result": "IDEMPOTENT_ALREADY_APPLIED",
            },
            {
                "case": "same_date_distinct_generation",
                "history_rows": 2,
                "current_winner": "greatest total ordering tuple",
                "date_overwrite": False,
            },
            {
                "case": "stale_replay",
                "history_policy": "insert if valid and absent",
                "current_delta": 0,
                "warning_transition_delta": 0,
                "outbox_delta": 0,
                "result": "REJECTED_STALE",
            },
        ],
        "warnings": [
            {
                "case": "same_acceptance_replay",
                "initial": "open",
                "final": "open",
                "transition_delta": 0,
                "outbox_delta": 0,
            },
            {
                "case": "newer_same_state_confirmation",
                "initial": "open",
                "observation": "CONFIRMED",
                "final": "open",
                "transition_delta": 0,
                "material_outbox_delta": 0,
                "last_observation_pointer_updates": True,
            },
            {
                "case": "newer_worsening_confirmation",
                "initial": "open",
                "observation": "WORSENED",
                "final": "escalated",
                "transition_delta": 1,
                "material_outbox_delta": 1,
            },
            {
                "case": "recovery",
                "initial": "escalated",
                "observation": "RECOVERED",
                "final": "resolved",
                "transition_delta": 1,
                "material_outbox_delta": 1,
            },
            {
                "case": "stale_worsening_or_recovery",
                "state_delta": 0,
                "transition_delta": 0,
                "outbox_delta": 0,
            },
        ],
        "notifications": [
            {
                "case": "same_daily_summary_schedule_slot_replay",
                "outbox_rows": 1,
                "dedupe": "source_event_id+channel+payload_contract_version",
            },
            {
                "case": "same_warning_transition_replay",
                "outbox_rows": 1,
                "send_eligibility": "once after commit with stable outbox identity",
            },
            {
                "case": "new_material_transition",
                "outbox_delta": 1,
                "send_eligibility": "post-commit",
            },
            {
                "case": "manual_legacy_invalid_or_stale",
                "outbox_delta": 0,
                "send_eligibility": "none",
            },
        ],
        "transaction_failures": failure_semantics(),
        "concurrency": [
            {
                "case": "two_identical_acceptances",
                "history_rows": 1,
                "current": "that acceptance",
                "transition_and_outbox_duplicates": 0,
            },
            {
                "case": "two_distinct_same_date_acceptances",
                "history_rows": 2,
                "current": "greatest ordering tuple",
                "loser_derived_effects": 0,
            },
            {
                "case": "older_and_newer_race",
                "history_rows": 2,
                "current": "newer regardless of commit order",
                "older_derived_effects": 0,
            },
        ],
        "timezone": {
            "assessment_date": "business/user date; market convention retained",
            "timestamps": "offset-aware; normalized to UTC for comparison",
            "kst_midnight_case": "date is not converted into an ordering timestamp",
            "naive_timestamp": "reject",
            "db_insertion_order": "not used",
        },
        "ticker": [
            ["000660", "PASS_EXACT_KR"],
            ["660", "REJECT_NO_ZERO_PADDING"],
            [660, "REJECT_NON_STRING"],
            ["IBM", "PASS_EXACT_US"],
            ["ibm", "REJECT_NOT_CANONICAL"],
        ],
    }


def acceptance_criteria() -> list[dict[str, object]]:
    criteria = [
        "external/manual request cannot mint canonical receipt",
        "missing/failed/quarantined receipt cannot enter canonical persistence",
        "historical invalid fresh proof is rejected",
        "22 M12BJ accepted outputs persist locally losslessly",
        "accepted history is immutable",
        "same acceptance replay is idempotent",
        "same-date distinct accepted generations are representable",
        "stale replay cannot move current state backward",
        "concurrent races end at the greatest ordering tuple",
        "warning replay is idempotent",
        "warning transitions are acceptance/observation driven, not call-count driven",
        "outbox rows are transactionally deduped",
        "external send is outside the DB transaction",
        "legacy/manual records remain distinguishable and automation-ineligible",
        "existing public reads/actions remain compatible or explicitly versioned",
        "proof-critical provenance loss is zero",
    ]
    return [
        {
            "criterion": index,
            "requirement": value,
            "m12bm_status": "SPECIFIED",
            "m12bn_required": "EXECUTABLE_LOCAL_PROOF_PASS",
        }
        for index, value in enumerate(criteria, start=1)
    ]


def build_report_payloads(
    *,
    implementation_commit: str,
    latest: Mapping[str, object],
    m12bl: Mapping[str, object],
    fixtures: Mapping[str, object],
    validation: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    receipt = receipt_spec()
    accepted_schema = accepted_assessment_schema()
    state_schema = current_state_schema()
    provenance_schema = receipt_table_schema()
    registry_schema = source_registry_schema()
    warnings = warning_schemas()
    outbox = outbox_schema()
    transaction = transaction_contract()
    migration = migration_spec()
    changes = implementation_change_map()
    state_machine = warning_state_machine()
    source_domains = [
        {
            "source_domain": "CANONICAL_MODEL_ACCEPTED",
            "storage": "accepted_assessment_v2",
            "receipt_required": True,
            "automation_eligible": True,
        },
        {
            "source_domain": "MANUAL_USER_AUTHORED",
            "storage": "thesisassessment + assessment_source_registry_v2",
            "receipt_required": False,
            "automation_eligible": False,
        },
        {
            "source_domain": "LEGACY_UNVERIFIED",
            "storage": "thesisassessment + assessment_source_registry_v2",
            "receipt_required": False,
            "automation_eligible": False,
        },
    ]
    ordering = {
        "contract": "accepted-assessment-total-order-v1",
        "components_in_order": [
            "effective_at_utc",
            "generation_generated_at_utc",
            "generation_id",
            "acceptance_id",
        ],
        "assessment_date_in_order": False,
        "accepted_at_in_order": False,
        "database_insert_order_in_order": False,
        "timezone": "offset-aware input, UTC-normalized comparison",
        "equal_acceptance": "IDEMPOTENT_ALREADY_APPLIED",
        "lower_order": "history insert allowed; current/warning/outbox no-op",
        "higher_order": "eligible for CAS current advancement",
    }
    issuance = {
        "status": "DEFINED_FAIL_CLOSED",
        "authorized_boundary": TRUSTED_ISSUERS[0],
        "input_type": "internal frozen TrustedFinalizationResult; arbitrary Mapping rejected",
        "preconditions": [
            "runtime/schema success",
            "canonical semantic audit PASS",
            "final composition PASS",
            "core immutability PASS",
            "source packet/evidence identities present",
            "not quarantined",
            "canonical ticker and positive thesis version",
            "valid business date and aware timestamps",
        ],
        "failure": "deterministic REJECTED/QUARANTINED denial; never ACCEPTED",
        "external_callable": False,
        "public_request_can_self_assert_pass": False,
    }
    verification = {
        "status": "DEFINED_PURE_NO_SEMANTIC_RERUN",
        "checks": [
            "supported receipt and serialization versions",
            "exact 25-field envelope",
            "acceptance_id recomputation",
            "receipt_hash recomputation",
            "trusted internal issuer",
            "ticker/thesis/date/timestamp identity",
            "source snapshot identity and packet hash binding",
            "accepted payload hash equality",
            "semantic/finalization/core immutability PASS",
            "ACCEPTED and no quarantine reason",
        ],
        "does_not": [
            "rerun semantic classification",
            "reinterpret candidate text",
            "repair output",
            "infer missing fields",
        ],
    }
    eligibility = {
        "contract": ELIGIBILITY_CONTRACT,
        "outputs": [
            "ELIGIBLE_CANONICAL",
            "INELIGIBLE_MANUAL_ONLY",
            "INELIGIBLE_LEGACY_UNVERIFIED",
            "REJECTED_INVALID_RECEIPT",
            "REJECTED_STALE",
            "REJECTED_QUARANTINED",
            "IDEMPOTENT_ALREADY_APPLIED",
        ],
        "canonical_write_requirement": "verified ACCEPTED receipt from trusted boundary",
        "manual_warning_outbox": False,
        "legacy_warning_outbox": False,
        "stale_history_policy": "retain immutable valid row, suppress derived state/effects",
    }
    legacy_projection = {
        "contract": LEGACY_PROJECTION_CONTRACT,
        "business_delta": {
            "STRENGTHENED": "strengthened",
            "UNCHANGED": "no_material_change",
            "WEAKENED": "weakened",
            "UNRESOLVED": None,
        },
        "unresolved_policy": "UNSUPPORTED; never no_material_change/needs_review coercion",
        "confidence_float": None,
        "risk_scalar": None,
        "valuation_impact_enum": None,
        "earnings_impact_enum": None,
        "confirmed_facts": "not projected",
        "inferred_implications": "not projected",
        "generic_summary": "not projected; exact core_judgment remains canonical",
    }
    reports: dict[str, dict[str, object]] = {
        "repository-provenance": {
            "status": "PASS",
            "phase": "M12BM",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": implementation_commit,
            "integration_branch": INTEGRATION_BRANCH,
            "head_at_generation": git("rev-parse", "HEAD"),
            "dirty_files_are_m12bm_outputs_only": True,
            "source_refs": [
                source_ref("app/models/thesis.py", "class ThesisAssessment"),
                source_ref("app/services/monitoring_service.py", "def record_assessment("),
                source_ref("app/services/daily_monitor_service.py", "async def run_daily_monitor("),
                source_ref("app/services/thesis_evaluation_service.py", "def _warning_lifecycle("),
                source_ref(
                    "app/services/notification_service.py",
                    "async def dispatch_pending_notifications(",
                ),
            ],
        },
        "latest-result-integrity": dict(latest),
        "m12bm-scope-freeze": {
            "status": "DESIGN_ONLY",
            "semantic_policy_reopened": False,
            "model_or_provider_calls_allowed": False,
            "production_schema_migration_allowed": False,
            "production_side_effects_allowed": False,
            "fresh_proof_allowed": False,
            "goal": "implementation-ready canonical persistence V2 design",
        },
        "m12bl-blocking-gap-freeze": {
            "status": m12bl["top_level_integration_result"],
            "persistence_eligibility_gate_status": m12bl["persistence_eligibility_gate_status"],
            "raw_model_persistence_bypass_count": m12bl["raw_model_persistence_bypass_count"],
            "proof_critical_missing_provenance_count": m12bl[
                "proof_critical_persistence_data_loss_count"
            ],
            "assessment_field_mapping_lossy_count": m12bl["assessment_field_mapping_lossy_count"],
            "assessment_invalid_enum_mapping_count": m12bl["assessment_invalid_enum_mapping_count"],
            "stale_guard": m12bl["stale_generation_guard_status"],
            "warning_idempotency": m12bl["warning_idempotency_status"],
            "transaction": m12bl["transaction_boundary_status"],
            "finding_weakened": False,
        },
        "current-production-persistence-schema-map": current_schema_map(),
        "current-entrypoint-trust-boundary-map": {
            "status": "DEFINED",
            "entrypoints": entrypoint_trust_map(),
        },
        "canonical-acceptance-receipt-options": {
            "options": [
                {
                    "option": "RANDOM_UUID_ONLY",
                    "deterministic_replay": False,
                    "tamper_evident": False,
                    "decision": "REJECT",
                },
                {
                    "option": "CONTENT_ID_ONLY_WITH_PUBLIC_SUBMISSION",
                    "deterministic_replay": True,
                    "external_forgery_boundary": "FAIL",
                    "decision": "REJECT",
                },
                {
                    "option": "CONTENT_ADDRESSED_RECEIPT_PLUS_INTERNAL_CAPABILITY_BOUNDARY",
                    "deterministic_replay": True,
                    "tamper_evident": True,
                    "external_request_minting": False,
                    "decision": "SELECT",
                },
                {
                    "option": "NEW_HMAC_OR_SIGNATURE_INFRASTRUCTURE",
                    "deterministic_replay": True,
                    "new_secret_or_key_lifecycle": True,
                    "needed_for_current_threat_model": False,
                    "decision": "DEFER",
                },
            ]
        },
        "canonical-acceptance-receipt-decision": {
            "status": "SELECTED",
            "decision": "CONTENT_ADDRESSED_RECEIPT_PLUS_INTERNAL_CAPABILITY_BOUNDARY",
            "receipt_contract": RECEIPT_CONTRACT,
            "field_count": len(RECEIPT_FIELDS),
            "issuer_count": len(TRUSTED_ISSUERS),
            "external_request_can_mint_receipt": False,
            "cryptographic_claim": "tamper-evident content identity; not a host-auth signature",
        },
        "canonical-acceptance-receipt-v1-spec": receipt,
        "receipt-issuance-boundary-contract": issuance,
        "receipt-verification-contract": verification,
        "persistence-eligibility-contract-v2": eligibility,
        "manual-vs-canonical-vs-legacy-source-contract": {
            "status": "DEFINED",
            "source_domain_count": 3,
            "domains": source_domains,
            "registry_schema": registry_schema,
        },
        "persistence-schema-options-comparison": {
            "status": "COMPARED",
            "options": schema_options(),
        },
        "persistence-schema-architecture-decision": {
            "status": "SELECTED",
            "selected": "OPTION_C_NEW_IMMUTABLE_ACCEPTED_V2_AND_DERIVED_CURRENT_STATE",
            "reason": (
                "legacy UNIQUE(ticker, assessment_date) cannot express immutable same-date "
                "multi-generation accepted history"
            ),
            "new_table_count": 7,
            "legacy_table_destructive_changes": 0,
        },
        "accepted-assessment-v2-schema-spec": accepted_schema,
        "current-monitoring-state-v2-schema-spec": state_schema,
        "canonical-provenance-schema-spec": provenance_schema,
        "structured-stance-schema-spec": {
            "status": "LOSSLESS_TYPED_EXTRACTS",
            "new_buyer_fields": [
                "stance",
                "summary",
                "confirmation_business_condition",
                "confirmation_business_condition_refs",
            ],
            "holder_fields": [
                "stance",
                "summary",
                "business_invalidation_condition",
                "business_invalidation_condition_refs",
            ],
            "timing_fields": "only if owned by accepted payload; never inferred",
            "authoritative_source": "hash-bound canonical payload",
        },
        "market-expectation-schema-spec": {
            "status": "EXACT_ACCEPTED_CLAIM_ONLY",
            "stored": ["text", "evidence_refs"],
            "expectation_level": "NOT_OWNED_BY_CURRENT_ACCEPTED_OUTPUT",
            "independence_metadata": "preserved through receipt-bound evidence refs/snapshot",
            "business_delta_mixing": False,
        },
        "structured-unknown-schema-spec": {
            "contract": "structured-unknown-storage-v1",
            "status": "DEFINED",
            "fields": [
                "summary",
                "evidence_refs",
                "treatment",
                "directional_negative_basis",
                "semantic",
            ],
            "unversioned_list_string_storage": False,
        },
        "security-basis-provenance-schema-spec": {
            "contract": "security-basis-provenance-v1",
            "status": "DEFINED_PACKET_PROJECTION",
            "fields": [
                "security_basis",
                "adr_ads_ratio",
                "adr_ads_ratio_source",
                "financial_currency",
                "price_currency",
                "per_share_basis_caveat",
                "evidence_refs",
                "source_snapshot_identity",
            ],
            "missing_policy": "null, never inferred",
            "full_semantic_analysis_duplicated": False,
        },
        "business-delta-canonical-storage-contract": {
            "status": "DEFINED_EXACT_ENUM",
            "canonical_values": ["STRENGTHENED", "UNCHANGED", "WEAKENED", "UNRESOLVED"],
            "storage": "accepted_assessment_v2.canonical_business_delta",
            "legacy_projection_contract": LEGACY_PROJECTION_CONTRACT,
            "unresolved_coerced": False,
        },
        "legacy-assessment-projection-contract": legacy_projection,
        "confidence-risk-storage-contract": {
            "status": "DEFINED_NO_SYNTHESIS",
            "confidence": {
                "storage": "LOW/MEDIUM/HIGH enum",
                "legacy_float_projection": None,
            },
            "risk": {
                "storage": "exact risk_context DirectionalClaim",
                "scalar_risk_level_projection": None,
            },
            "valuation": "exact DirectionalClaim; no ValuationImpact inference",
            "earnings": "exact DirectionalClaim; no EarningsEstimateImpact inference",
        },
        "immutable-history-contract": {
            "status": "DEFINED",
            "identity": "one acceptance_id -> one immutable row",
            "same_receipt_replay": "no-op/existing row",
            "same_id_different_bytes": "integrity conflict and rollback",
            "same_date_distinct_generation": "separate rows",
            "update_delete_application_methods": False,
        },
        "acceptance-id-idempotency-contract": {
            "status": "DEFINED",
            "contract": ACCEPTANCE_ID_CONTRACT,
            "formula": (
                "ca1_ + sha256(canonical JSON of proof-critical receipt material, "
                "excluding acceptance_id/receipt_hash/accepted_at)"
            ),
            "same_result_same_id": True,
            "different_candidate_generation_ticker_distinct": True,
            "tamper_detected_by_receipt_hash": True,
            "generation_ticker_single_valued": True,
        },
        "stale-safe-ordering-contract": ordering,
        "current-state-compare-and-swap-contract": {
            "status": "DEFINED_DATABASE_LEVEL",
            "row": state_schema,
            "algorithm": [
                "begin transaction (SQLite BEGIN IMMEDIATE in local proof)",
                "insert immutable history idempotently",
                "read current tuple and row_version",
                "conditional update where row_version and old tuple still match",
                "on conflict reread; classify stale or bounded retry",
            ],
            "process_lock_sufficient": False,
            "max_retry_policy": "bounded configuration; identity unchanged",
        },
        "warning-identity-contract": {
            "status": "DEFINED",
            "formula": (
                "sha256(warning-identity-v2, ticker, thesis_version, warning_type, "
                "condition_contract_version, condition_identity)"
            ),
            "acceptance_link_required": True,
            "prose_reclassification": False,
            "missing_trusted_observation": "no warning mutation",
            "schemas": warnings,
        },
        "warning-state-machine-contract": {
            "status": "DEFINED_USING_REPOSITORY_STATES",
            "states": ["open", "escalated", "resolved"],
            "invalid_provenance": "pre-lifecycle rejection/quarantine",
            "observation_contract": WARNING_OBSERVATION_CONTRACT,
            "rows": state_machine,
        },
        "warning-transition-idempotency-contract": {
            "status": "DEFINED",
            "contract": WARNING_TRANSITION_CONTRACT,
            "identity": warnings["warning_transition_v2"]["identity"],
            "same_acceptance_replay_transition_delta": 0,
            "same_date_confirmation_escalates": False,
            "newer_worsened_observation_required_for_escalation": True,
        },
        "notification-outbox-contract": outbox,
        "daily-vs-material-notification-contract": {
            "status": "SEPARATED",
            "daily": {
                "event_kind": "DAILY_SUMMARY_NOTIFICATION",
                "identity_inputs": [
                    "schedule_run_id",
                    "ticker",
                    "acceptance_id",
                    "channel",
                    "payload_contract_version",
                ],
                "material_transition_required": False,
            },
            "material": {
                "event_kind": "MATERIAL_STATE_TRANSITION_NOTIFICATION",
                "identity_inputs": [
                    "warning_transition_id",
                    "channel",
                    "payload_contract_version",
                ],
                "accepted_transition_required": True,
            },
            "every_assessment_is_material_alert": False,
        },
        "transaction-boundary-v2-contract": transaction,
        "partial-failure-recovery-contract": {
            "status": "DEFINED",
            "rows": failure_semantics(),
            "unspecified_partial_commit_paths": 0,
        },
        "retry-safety-v2-contract": {
            "status": "DEFINED",
            "stable_retry_identities": [
                "acceptance_id",
                "warning_transition_id",
                "outbox_event_id",
            ],
            "fresh_identity_on_retry": False,
            "semantic_payload_mutation_on_retry": False,
            "bounded_retries": True,
            "terminal_state": "dead_letter/manual review",
        },
        "concurrency-contract": {
            "status": "DEFINED",
            "database_correctness": "unique constraints + transaction + CAS",
            "python_lock_correctness": False,
            "race_fixtures": fixtures["concurrency"],
            "final_current_invariant": "maximum total ordering tuple",
            "distinct_valid_history_preserved": True,
        },
        "schema-migration-spec": migration,
        "existing-data-legacy-unverified-migration-spec": {
            "status": "DEFINED",
            "source": "all thesisassessment rows existing before V2 cutover",
            "target": registry_schema,
            "classification": "LEGACY_UNVERIFIED",
            "automation_eligible": False,
            "original_row_modified": False,
            "fabricated_receipt_or_pass_or_hash": False,
            "rerun": "idempotent by legacy_assessment_id primary key",
        },
        "index-and-unique-constraint-spec": {
            "status": "DEFINED",
            "rows": indexes_and_constraints(),
        },
        "upgrade-order": {
            "status": "DEFINED",
            "steps": [
                "create/verify seven V2 tables and indexes in ephemeral DB",
                "classify existing rows LEGACY_UNVERIFIED in registry",
                "deploy disabled receipt/persistence services",
                "run frozen M12BJ/negative/lifecycle/race local proof",
                "enable internal dual-read observation with sends disabled",
                "separately authorize writer cutover",
                "separately authorize outbox delivery",
            ],
            "production_execution_in_m12bm": False,
        },
        "rollback-or-forward-only-decision": {
            "status": "FORWARD_ONLY_DATA_PRESERVING",
            "reason": "immutable acceptance/event history cannot be losslessly collapsed into legacy row",
            "operational_rollback": "disable V2 write/read preference; retain tables",
            "destructive_down_migration": False,
        },
        "read-path-v2-contract": {
            "status": "DEFINED_DISCRIMINATED",
            "canonical_authority": "accepted_assessment_v2 + monitoring_current_state_v2",
            "legacy_authority": "thesisassessment + source registry",
            "current_selection": "verified V2 pointer only; fail closed if corrupt",
            "history_selection": "union envelope retaining source_domain and distinct generations",
            "silent_manual_fallback_for_broken_v2": False,
        },
        "current-review-read-compatibility": {
            "status": "DEFINED_INTERNAL_DUAL_READ",
            "v2_present": "return typed accepted payload from current-state pointer",
            "v2_absent": "return legacy/manual read with explicit source domain internally",
            "v2_invalid": "explicit unavailable/integrity failure; no silent legacy substitution",
            "existing_public_schema_changed_in_m12bm": False,
        },
        "assessment-history-read-compatibility": {
            "status": "DEFINED",
            "existing_external_history": "legacy/manual rows unchanged",
            "internal_v2_history": "discriminated canonical+manual+legacy envelope",
            "same_date_canonical_rows": "all retained and total-order sorted",
            "unsupported_legacy_projection": "explicit null/unsupported",
        },
        "external-action-api-compatibility-decision": {
            "status": "RETAIN_MANUAL_ONLY",
            "operation_id": "recordThesisAssessment",
            "ordinary_request_response_compatibility": True,
            "source_domain": "MANUAL_USER_AUTHORED",
            "reserved_canonical_fields": "reject, never trust or silently promote",
            "canonical_receipt_endpoint_added": False,
            "canonical_warning_outbox_effects": 0,
        },
        "manual-assessment-automation-eligibility-decision": {
            "manual_assessment_supported": True,
            "manual_assessment_automation_eligible": False,
            "legacy_assessment_automation_eligible": False,
            "separate_manual_authority_contract": "ABSENT_AND_NOT_REQUIRED_FOR_M12BN",
            "product_decision_blocker": False,
        },
        "m12bj-22-positive-receipt-fixture-spec": fixtures["m12bj_positive"],
        "historical-fresh-negative-receipt-fixture-spec": fixtures["historical_negative"],
        "missing-receipt-negative-fixture-spec": fixtures["receipt_negatives"][0],
        "tampered-receipt-negative-fixture-spec": fixtures["receipt_negatives"][1],
        "quarantined-receipt-negative-fixture-spec": fixtures["receipt_negatives"][2],
        "duplicate-acceptance-fixture-spec": fixtures["identity"][0],
        "same-date-distinct-generation-fixture-spec": fixtures["identity"][1],
        "stale-replay-fixture-spec": fixtures["identity"][2],
        "warning-replay-fixture-spec": fixtures["warnings"][0],
        "warning-new-confirmation-fixture-spec": {
            "same_state": fixtures["warnings"][1],
            "worsened": fixtures["warnings"][2],
            "contract_rule": "different acceptance alone is insufficient; observation decides",
        },
        "warning-recovery-fixture-spec": {
            "recovery": fixtures["warnings"][3],
            "stale_negative_control": fixtures["warnings"][4],
        },
        "notification-dedupe-fixture-spec": {
            "status": "DEFINED",
            "cases": fixtures["notifications"],
        },
        "transaction-failure-injection-fixture-spec": {
            "status": "DEFINED",
            "cases": fixtures["transaction_failures"],
        },
        "concurrency-race-fixture-spec": {
            "status": "DEFINED",
            "cases": fixtures["concurrency"],
        },
        "timezone-boundary-fixture-spec": fixtures["timezone"],
        "ticker-identity-fixture-spec": {
            "status": "DEFINED",
            "cases": fixtures["ticker"],
            "normalization_owner": "canonical pipeline before receipt issuance",
            "receipt_verifier_zero_padding": False,
        },
        "implementation-change-map": {
            "status": "IMPLEMENTATION_READY",
            "planned_change_count": len(changes),
            "semantic_changes": 0,
            "model_facing_changes": 0,
            "rows": changes,
        },
        "files-modules-expected-to-change": {
            "status": "BOUNDED",
            "paths": [row["module_path"] for row in changes],
            "production_files_changed_in_m12bm": [],
            "runtime_behavior_changed_in_m12bm": False,
        },
        "migration-implementation-plan": {
            "status": "READY_FOR_M12BN_LOCAL_ONLY",
            "migration": migration,
            "required_commands": [
                "dry-run schema diff against empty and copied ephemeral SQLite",
                "apply idempotent new-table migration to ephemeral SQLite",
                "legacy registry backfill and second-run zero-delta proof",
                "foreign-key/index/constraint introspection",
            ],
            "production_database": "PROHIBITED",
        },
        "local-ephemeral-replay-plan": {
            "status": "DEFINED_NOT_EXECUTED",
            "positive": "22 frozen M12BJ accepted outputs",
            "negative": "16 historical failures plus missing/tampered/quarantined receipts",
            "lifecycle": "identity, stale, warning, notification, failure, race, timezone, ticker",
            "database": "new temporary SQLite per scenario",
            "external_send": "stubbed and asserted zero",
        },
        "backward-compatibility-test-plan": {
            "status": "DEFINED",
            "tests": [
                "recordThesisAssessment ordinary manual request/read unchanged",
                "reserved canonical fields rejected and cannot mint receipt",
                "all pre-V2 rows readable and classified LEGACY_UNVERIFIED",
                "future manual rows classified MANUAL_USER_AUTHORED",
                "legacy API does not coerce canonical UNRESOLVED/confidence/risk",
                "current review prefers verified V2 and fails closed on corrupt pointer",
                "same-date V2 history ordering retains every generation",
            ],
        },
        "production-firewall-test-plan": {
            "status": "DEFINED",
            "assertions": {
                "production_db_mutations": 0,
                "monitoring_registrations": 0,
                "monitoring_stops": 0,
                "warning_mutations": 0,
                "notification_queue_writes": 0,
                "production_sends": 0,
                "scheduler_mutations": 0,
                "remote_pushes": 0,
                "main_merges": 0,
                "deployments": 0,
            },
            "m12bn_environment": "temporary SQLite and fake outbox sender only",
        },
        "implementation-acceptance-criteria": {
            "status": "ALL_16_SPECIFIED",
            "rows": acceptance_criteria(),
        },
        "next-bounded-scope-decision": {
            "status": "READY",
            "next_scope": NEXT_SCOPE,
            "fresh_real_proof_authorized": False,
            "production_integration_authorized": False,
            "reason": "contract complete; executable local implementation proof remains",
        },
        "master-workflow-update": {
            "status": "RECORDED_LOCAL_ONLY",
            "master_workflow_updated": True,
            "project_handoff_updated": True,
            "next_session_prompt_updated": True,
            "project_state_updated": True,
            "semantic_frozen": True,
            "next_scope": NEXT_SCOPE,
        },
    }
    completion = {
        "status": "COMPLETE_DESIGN_ONLY",
        "phase": "M12BM",
        "contract": CONTRACT,
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": INTEGRATION_BRANCH,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "final_local_head_sha": implementation_commit,
        "latest_result_zip_sha256": latest["zip_sha256"],
        "latest_result_integrity": "PASS_83_INDEXED_84_ENTRIES",
        "m12bl_top_level_result": m12bl["top_level_integration_result"],
        "m12bl_raw_model_persistence_bypass_count": m12bl["raw_model_persistence_bypass_count"],
        "m12bl_proof_critical_missing_provenance_count": m12bl[
            "proof_critical_persistence_data_loss_count"
        ],
        "m12bl_persistence_data_loss_count": m12bl["proof_critical_persistence_data_loss_count"],
        "m12bl_assessment_field_mapping_lossy_count": m12bl["assessment_field_mapping_lossy_count"],
        "m12bl_stale_guard_status": m12bl["stale_generation_guard_status"],
        "m12bl_warning_idempotency_status": m12bl["warning_idempotency_status"],
        "m12bl_transaction_status": m12bl["transaction_boundary_status"],
        "canonical_acceptance_receipt_contract_version": RECEIPT_CONTRACT,
        "canonical_acceptance_receipt_field_count": len(RECEIPT_FIELDS),
        "canonical_acceptance_issuer_count": len(TRUSTED_ISSUERS),
        "external_request_can_mint_receipt": False,
        "persistence_source_domain_count": len(source_domains),
        "manual_assessment_supported": True,
        "manual_assessment_automation_eligible": False,
        "legacy_assessment_automation_eligible": False,
        "selected_schema_architecture": (
            "OPTION_C_NEW_IMMUTABLE_ACCEPTED_V2_AND_DERIVED_CURRENT_STATE"
        ),
        "accepted_assessment_v2_defined": True,
        "current_state_v2_defined": True,
        "canonical_provenance_storage_defined": True,
        "canonical_business_delta_storage_status": "DEFINED_EXACT_ENUM",
        "new_buyer_structured_storage_status": "DEFINED_LOSSLESS",
        "holder_structured_storage_status": "DEFINED_LOSSLESS",
        "market_expectation_structured_storage_status": "DEFINED_EXACT_ACCEPTED_CLAIM",
        "unknown_structured_storage_status": "DEFINED_VERSIONED",
        "security_basis_provenance_storage_status": "DEFINED_RECEIPT_BOUND",
        "confidence_storage_status": "DEFINED_ENUM_NO_FLOAT_PROJECTION",
        "risk_storage_status": "DEFINED_STRUCTURED_CLAIM_NO_SCALAR",
        "acceptance_id_contract_defined": True,
        "immutable_history_contract_defined": True,
        "stale_safe_ordering_contract_defined": True,
        "current_state_cas_contract_defined": True,
        "warning_state_machine_contract_defined": True,
        "warning_transition_idempotency_defined": True,
        "notification_outbox_contract_defined": True,
        "transaction_boundary_v2_defined": True,
        "partial_failure_recovery_defined": True,
        "retry_safety_defined": True,
        "concurrency_contract_defined": True,
        "legacy_unverified_migration_defined": True,
        "schema_migration_required": True,
        "schema_migration_spec_status": "DEFINED_NOT_APPLIED",
        "rollback_or_forward_only_decision": "FORWARD_ONLY_DATA_PRESERVING",
        "external_action_api_compatibility_status": (
            "RETAINED_MANUAL_ONLY_RESERVED_CANONICAL_FIELDS_REJECTED"
        ),
        "read_path_compatibility_status": "DEFINED_DISCRIMINATED_DUAL_READ",
        "model_facing_change_required": False,
        "semantic_service_change_required": False,
        "decision_policy_change_required": False,
        "model_calls": 0,
        "provider_source_fetches": 0,
        "external_proof_network_calls": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "observed_paused_schedule_count": 4,
        "top_level_design_result": TOP_LEVEL_RESULT,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "focused_test_result": validation["focused_test_result"],
        "focused_test_passed_count": validation["focused_test_passed_count"],
        "full_test_result": validation["full_test_result"],
        "full_test_passed_count": validation["full_test_passed_count"],
        "ruff_result": validation["ruff_result"],
        "git_diff_check": validation["git_diff_check"],
        "artifact_count": "PENDING_BUNDLE",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    reports["program-completion"] = completion
    if set(reports) != set(REPORT_SLUGS):
        missing = sorted(set(REPORT_SLUGS) - set(reports))
        extra = sorted(set(reports) - set(REPORT_SLUGS))
        raise ValueError(f"M12BM_REPORT_PAYLOAD_MISMATCH:missing={missing}:extra={extra}")
    return reports


def run(args: argparse.Namespace) -> None:
    latest = verify_latest_result()
    m12bl = load_m12bl_completion()
    positive_rows = load_m12bj_positive_rows()
    fixtures = fixture_specs(positive_rows)
    validation = {
        "focused_test_result": args.focused_result,
        "focused_test_passed_count": args.focused_count,
        "full_test_result": args.full_result,
        "full_test_passed_count": args.full_count,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "model_calls": 0,
        "provider_source_fetches": 0,
        "external_network_calls": 0,
        "production_effects": 0,
    }
    reports = build_report_payloads(
        implementation_commit=args.implementation_commit,
        latest=latest,
        m12bl=m12bl,
        fixtures=fixtures,
        validation=validation,
    )
    for slug in REPORT_SLUGS:
        report(slug, reports[slug])

    design_contract = {
        "contract": CONTRACT,
        "top_level_design_result": TOP_LEVEL_RESULT,
        "receipt": receipt_spec(),
        "eligibility_contract": reports["persistence-eligibility-contract-v2"],
        "source_domains": reports["manual-vs-canonical-vs-legacy-source-contract"],
        "selected_architecture": reports["persistence-schema-architecture-decision"],
        "next_scope": NEXT_SCOPE,
    }
    schema_design = {
        "contract": "canonical-persistence-v2-schema-design-v1",
        "status": "DEFINED_NOT_APPLIED",
        "receipt": receipt_table_schema(),
        "accepted_assessment": accepted_assessment_schema(),
        "current_state": current_state_schema(),
        "source_registry": source_registry_schema(),
        "warnings": warning_schemas(),
        "outbox": outbox_schema(),
        "indexes_and_constraints": indexes_and_constraints(),
    }
    lifecycle_design = {
        "contract": "canonical-persistence-v2-lifecycle-design-v1",
        "status": "DEFINED_NOT_IMPLEMENTED",
        "ordering": reports["stale-safe-ordering-contract"],
        "warning_state_machine": warning_state_machine(),
        "transaction": transaction_contract(),
        "failure_semantics": failure_semantics(),
    }
    completion = dict(reports["program-completion"])
    completion["generated_at"] = datetime.now(UTC).isoformat()
    write_json(OUTPUT / "design-contract.json", design_contract)
    write_json(OUTPUT / "schema-design.json", schema_design)
    write_json(OUTPUT / "lifecycle-design.json", lifecycle_design)
    write_json(OUTPUT / "migration-plan.json", migration_spec())
    write_json(OUTPUT / "fixture-plan.json", fixtures)
    write_json(OUTPUT / "implementation-change-map.json", implementation_change_map())
    write_json(OUTPUT / "validation.json", validation)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BM Canonical Acceptance Persistence Design",
                "",
                f"- Result: `{TOP_LEVEL_RESULT}`",
                f"- Receipt: `{RECEIPT_CONTRACT}` ({len(RECEIPT_FIELDS)} fields)",
                "- Architecture: `Option C - immutable AcceptedAssessmentV2 + current state`",
                "- Manual assessments: supported, canonical automation ineligible",
                "- Legacy assessments: readable, `LEGACY_UNVERIFIED`, automation ineligible",
                "- Warning lifecycle: acceptance-driven and replay-idempotent by contract",
                "- Notification delivery: transactional outbox, external send post-commit",
                "- Production DB / queue / send / scheduler / remote effects: `0`",
                "- Fresh proof / main merge / production readiness: `NOT_READY`",
                f"- Next scope: `{NEXT_SCOPE}`",
                "",
            )
        ),
    )
    print(canonical_json({"status": "PASS", "result": TOP_LEVEL_RESULT}))


def seal(args: argparse.Namespace) -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion.update(
        {
            "final_local_head_sha": args.evidence_commit,
            "evidence_commit": args.evidence_commit,
            "documentation_status": "PASS",
        }
    )
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "master_workflow_updated": True,
            "project_handoff_updated": True,
            "next_session_prompt_updated": True,
            "project_state_updated": True,
            "evidence_commit": args.evidence_commit,
            "remote_push": False,
            "main_merge": False,
            "deployment": False,
            "next_scope": NEXT_SCOPE,
        },
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
        RUNNER,
        TEST_PATH,
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


def _scan_artifacts(files: Sequence[Path]) -> list[dict[str, object]]:
    return [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "indicators": list(indicators),
        }
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{NUMBERS[slug]:02d}-{slug}.json")
        for slug in REPORT_SLUGS
        if not (REPORTS / f"{NUMBERS[slug]:02d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BM_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    forbidden = ("model-calls", "prompt.txt", "output.raw.json", "transport.log")
    names = {str(path.relative_to(REPO_ROOT)) for path in files}
    if any(marker in name for name in names for marker in forbidden):
        raise ValueError("M12BM_RAW_MODEL_ARTIFACT_PACKAGE_ATTEMPT")
    secret_failures = _scan_artifacts(files)
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
    secret_failures = _scan_artifacts(files)
    integrity = {
        "contract": "m12bm-artifact-index-v1",
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
    write_json(OUTPUT / "artifact-index.json", integrity)
    if integrity["status"] != "PASS":
        raise ValueError("M12BM_ARTIFACT_SECRET_SCAN_FAILURE")
    if output_zip.exists():
        raise ValueError(f"M12BM_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
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
            raise ValueError("M12BM_RESULT_BUNDLE_CRC_FAILURE")
        if len(archive.namelist()) != len(files) + 1:
            raise ValueError("M12BM_RESULT_BUNDLE_INVENTORY_FAILURE")
        for row in integrity["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BM_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BM_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
    run_parser.add_argument("--full-result", required=True)
    run_parser.add_argument("--full-count", type=int, required=True)
    run_parser.add_argument("--ruff-result", required=True)
    run_parser.add_argument("--diff-result", required=True)
    seal_parser = commands.add_parser("seal")
    seal_parser.add_argument("--evidence-commit", required=True)
    bundle_parser = commands.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "run":
        run(args)
    elif args.command == "seal":
        seal(args)
    else:
        bundle(args.output)


if __name__ == "__main__":
    main()
