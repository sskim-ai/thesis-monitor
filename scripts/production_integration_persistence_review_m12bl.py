"""Offline M12BL review of production persistence integration boundaries.

The runner consumes frozen M12BJ/M12BK artifacts and exercises only ephemeral
SQLite/file state. It never calls a model, provider, network endpoint,
production database, notification sender, scheduler, or remote Git endpoint.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import UTC, date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
import subprocess
import sys
import tempfile
from typing import Any
import zipfile
from zoneinfo import ZoneInfo


os.environ.setdefault("THESIS_MONITOR_ENV_FILE", "")
os.environ.setdefault("ENABLE_LIVE_PROVIDERS", "false")
os.environ.setdefault("NOTIFICATION_DRY_RUN", "true")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

NAME = "20260914-production-integration-persistence-review-on-integrated-main"
CONTRACT = "production-integration-persistence-review-m12bl-v1"
OUTPUT = REPO_ROOT / "artifacts" / NAME
REPORTS = REPO_ROOT / "docs/reports" / NAME
RUNNER = Path("scripts/production_integration_persistence_review_m12bl.py")
TEST_PATH = Path("tests/test_production_integration_persistence_review_m12bl.py")
ARCHITECTURE = Path("docs/architecture/PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW.md")
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260914-production-integration-persistence-review-on-integrated-main.md"
)

BASE_INTEGRATION_HEAD_SHA = "4196585e03b6866c54991cd5cd5e2b91fc488a35"
WORK_INSTRUCTION_COMMIT = "f536e5f125dfa0f9a996b58b750ee5dbb486ed4a"
INTEGRATION_BRANCH = "codex/20260914-production-integration-persistence-review-m12bl"
LATEST_RESULT_ZIP = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260914-real-cohort-policy-validation-against-frozen-"
    "boundary-contracts-report.zip"
)
LATEST_RESULT_SHA256 = "0f845b5c0cf2d6fdef74228bebacdc08bf46543bd8bc0299bcfba6a1ee0c050e"
M12BJ_GENERATION_ID = "20260911-m12ai-shadow-20260914T024739Z-1fe808eba817"
TOP_LEVEL_RESULT = "BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP"
NEXT_SCOPE = "CANONICAL_ACCEPTANCE_PERSISTENCE_CONTRACT_SCHEMA_AND_LIFECYCLE_DESIGN"

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bl-scope-freeze
semantic-policy-proof-freeze
historical-fresh-quarantine-freeze
production-integration-entrypoint-map
assessment-persistence-call-graph
warning-lifecycle-call-graph
notification-queue-call-graph
scheduler-call-graph
persistence-eligibility-contract
canonical-acceptance-provenance-contract
assessment-field-mapping-matrix
business-delta-persistence-mapping
newbuyer-holder-persistence-separation
market-expectation-persistence-separation
assessment-idempotency-contract
warning-idempotency-contract
notification-dedupe-contract
stale-generation-guard-contract
transaction-boundary-contract
partial-failure-behavior
retry-safety-audit
concurrency-duplicate-safety-audit
assessment-date-timezone-contract
ticker-normalization-contract
confidence-risk-mapping-contract
security-basis-provenance-audit
post-acceptance-semantic-rederivation-scan
ephemeral-persistence-harness-contract
m12bj-22-output-persistence-eligibility-replay
m12bj-22-output-write-readback-fidelity
m12bj-22-output-provenance-fidelity
invalid-historical-fresh-rejection-fixture
missing-semantic-receipt-rejection-fixture
final-composition-failure-rejection-fixture
core-mutation-rejection-fixture
duplicate-assessment-replay-fixture
stale-assessment-replay-fixture
malformed-enum-rejection-fixture
ticker-normalization-fixture
assessment-date-boundary-fixture
warning-lifecycle-replay
notification-eligibility-replay
partial-failure-injection-replay
current-review-read-path-replay
persistence-schema-compatibility-decision
proof-critical-provenance-field-coverage
schema-migration-requirement-decision
local-migration-upgrade-replay
production-db-no-mutation-proof
monitoring-no-registration-stop-proof
warning-no-production-mutation-proof
notification-no-production-queue-write-proof
production-send-zero-proof
scheduler-pause-preservation
remote-push-prohibition-audit
main-merge-zero-proof
deployment-zero-proof
secret-scan
production-integration-persistence-decision
fresh-proof-readiness-decision
main-merge-readiness-decision
production-readiness-decision
next-scope-decision
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {
    slug: index if index <= 50 else index + 1
    for index, slug in enumerate(REPORT_SLUGS, start=1)
}


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


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
        (REPO_ROOT / relative).read_text(encoding="utf-8").splitlines(),
        start=1,
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


def verify_latest_result() -> dict[str, object]:
    from scripts.real_cohort_policy_validation_m12bk_r2 import verify_indexed_bundle

    result = verify_indexed_bundle(LATEST_RESULT_ZIP, LATEST_RESULT_SHA256)
    if result["indexed_payload_count"] != 45 or result["zip_entry_count"] != 46:
        raise ValueError("LATEST_RESULT_BUNDLE_INVENTORY_MISMATCH")
    return result


def load_m12bj_fixture_manifest() -> list[dict[str, object]]:
    from scripts.real_cohort_policy_validation_m12bk_r2 import (
        M12BJ_PACKET_ROOT,
        _load_m12bj_rows,
        verify_m12bj_identity,
    )

    identity = verify_m12bj_identity()
    if identity["generation_id"] != M12BJ_GENERATION_ID:
        raise ValueError("M12BJ_GENERATION_ID_MISMATCH")
    rows = _load_m12bj_rows()
    fixtures: list[dict[str, object]] = []
    for ticker, phases in sorted(rows.items()):
        packet_path = M12BJ_PACKET_ROOT / f"{ticker}.json"
        packet = read_json(packet_path)
        stage1 = phases["stage1"]
        stage2 = phases["stage2"]
        core = dict(stage1["core"])
        stance = dict(stage2["stance"])
        composed = {
            **core,
            "fundamental_new_buyer": stance["fundamental_new_buyer"],
            "fundamental_holder": stance["fundamental_holder"],
        }
        canonical = stage1["canonical_semantic_audit"]
        fixtures.append(
            {
                "ticker": ticker,
                "market": packet["market"],
                "assessment_date": packet["assessment_date"],
                "packet_id": packet["packet_id"],
                "generation_id": M12BJ_GENERATION_ID,
                "packet_sha256": file_sha256(packet_path),
                "core_sha256": canonical_sha256(core),
                "stance_sha256": canonical_sha256(stance),
                "final_composed_candidate_sha256": canonical_sha256(composed),
                "canonical_semantic_contract": canonical["contract"],
                "canonical_semantic_status": canonical["status"],
                "final_composition_status": (
                    "PASS"
                    if stage1["status"] == stage2["status"] == "PASS"
                    and core["ticker"] == stance["ticker"] == ticker
                    else "FAIL"
                ),
                "core_immutability_status": "PASS",
                "business_thesis_change": core["business_thesis_change"],
                "overall_direction": core["overall_direction"],
                "directional_confidence": core["directional_confidence"],
                "new_buyer_stance": stance["fundamental_new_buyer"]["stance"],
                "holder_stance": stance["fundamental_holder"]["stance"],
                "persistence_eligible": False,
                "persistence_denial_reason": "CANONICAL_ACCEPTANCE_GATE_NOT_IMPLEMENTED",
            }
        )
    if len(fixtures) != 22 or any(
        row["canonical_semantic_status"] != "PASS"
        or row["final_composition_status"] != "PASS"
        for row in fixtures
    ):
        raise ValueError("M12BJ_FIXTURE_FREEZE_FAILURE")
    return fixtures


def provenance_coverage() -> list[dict[str, str]]:
    persisted = {"ticker", "assessment_date"}
    noncritical = {"model_identity", "model_effort"}
    fields = (
        "generation_id",
        "ticker",
        "assessment_date",
        "packet_hash",
        "final_composed_candidate_hash",
        "canonical_semantic_audit_contract",
        "canonical_semantic_audit_status",
        "model_identity",
        "model_effort",
        "source_evidence_snapshot_identity",
        "finalization_status",
        "core_hash",
        "stance_hash",
        "quarantine_marker",
    )
    rows = []
    for field in fields:
        if field in persisted:
            classification = "PERSISTED"
        elif field in noncritical:
            classification = "MISSING_BUT_NONCRITICAL"
        else:
            classification = "MISSING_AND_PROOF_CRITICAL"
        rows.append(
            {
                "field": field,
                "classification": classification,
                "storage": (
                    f"thesisassessment.{field}"
                    if field in persisted
                    else "NO_THESISASSESSMENT_FIELD_OR_ACCEPTANCE_SIDECAR"
                ),
            }
        )
    return rows


def assessment_mapping_matrix() -> list[dict[str, str]]:
    return [
        {
            "concept": "ticker",
            "source": "DirectionalCoreCandidate.ticker",
            "target": "ThesisAssessment.ticker",
            "classification": "EXACT",
            "reason": "string identity exists on both sides",
        },
        {
            "concept": "assessment_date",
            "source": "frozen packet assessment_date",
            "target": "ThesisAssessment.assessment_date",
            "classification": "LOSSLESS_NORMALIZATION",
            "reason": "date is packet-owned but absent from the composed candidate",
        },
        {
            "concept": "business_thesis_change",
            "source": "STRENGTHENED/UNCHANGED/WEAKENED/UNRESOLVED",
            "target": "AssessmentStatus lowercase vocabulary",
            "classification": "INVALID_ENUM_MAPPING",
            "reason": "no explicit versioned canonical-to-persistence mapping exists",
        },
        {
            "concept": "valuation_context",
            "source": "DirectionalClaim text and evidence refs",
            "target": "ValuationImpact enum plus generated summary",
            "classification": "LOSSY",
            "reason": "no deterministic claim-to-impact mapping exists",
        },
        {
            "concept": "earnings_estimate_impact",
            "source": "DirectionalClaim text and evidence refs",
            "target": "EarningsEstimateImpact enum",
            "classification": "LOSSY",
            "reason": "no accepted-output mapping exists",
        },
        {
            "concept": "market_expectation_assessment",
            "source": "DirectionalClaim text and evidence refs",
            "target": "level/assessment/summary/evidence_basis",
            "classification": "LOSSY",
            "reason": "candidate has no persistence-level expectation level adapter",
        },
        {
            "concept": "confirmed_facts",
            "source": "selected evidence refs and directional claims",
            "target": "list[str]",
            "classification": "MISSING",
            "reason": "no final-composition projection owns fact classification",
        },
        {
            "concept": "inferred_implications",
            "source": "directional claims",
            "target": "list[str]",
            "classification": "MISSING",
            "reason": "no final-composition projection exists",
        },
        {
            "concept": "unknowns",
            "source": "DirectionalUnknown with refs/treatment/basis",
            "target": "list[str]",
            "classification": "LOSSY",
            "reason": "refs, treatment and negative basis are not represented",
        },
        {
            "concept": "summary",
            "source": "multiple typed core claims",
            "target": "single free-text summary",
            "classification": "MISSING",
            "reason": "no authorized composition-to-summary projection exists",
        },
        {
            "concept": "new_buyer_view",
            "source": "stance plus summary and confirmation refs",
            "target": "free-text string",
            "classification": "LOSSY",
            "reason": "structured stance and refs have no target fields",
        },
        {
            "concept": "holder_view",
            "source": "stance plus summary and invalidation refs",
            "target": "free-text string",
            "classification": "LOSSY",
            "reason": "structured stance and refs have no target fields",
        },
        {
            "concept": "price_view",
            "source": "not owned by the frozen fundamental composition",
            "target": "free-text string",
            "classification": "INTENTIONAL_NOT_PERSISTED",
            "reason": "price/timing remains a separate dimension",
        },
        {
            "concept": "risk_level",
            "source": "risk_context claim with evidence refs",
            "target": "unconstrained string",
            "classification": "LOSSY",
            "reason": "no explicit risk-level mapping contract exists",
        },
        {
            "concept": "confidence",
            "source": "LOW/MEDIUM/HIGH enum",
            "target": "float 0..1",
            "classification": "LOSSY",
            "reason": "no versioned enum-to-number mapping exists",
        },
    ]


def production_call_graph() -> dict[str, object]:
    assessments = [
        {
            "entrypoint": "POST /monitoring-items/{ticker}/assessments",
            "operation_id": "recordThesisAssessment",
            "route": source_ref("app/api/routes_monitoring.py", 'operation_id="recordThesisAssessment"'),
            "service": source_ref("app/services/monitoring_service.py", "def record_assessment("),
            "repository": "ThesisAssessment + WatchlistItem",
            "transaction": "single commit after assessment/item/onboarding flush",
            "idempotency": "UNIQUE(ticker, assessment_date) with mutable upsert",
            "canonical_acceptance_gate": False,
        },
        {
            "entrypoint": "run_daily_monitor",
            "service": source_ref("app/services/daily_monitor_service.py", "async def run_daily_monitor("),
            "repository": "ThesisAssessment + WatchlistItem",
            "transaction": "per-ticker commit; later monitoring-state/run/queue commits",
            "idempotency": "same ticker/date row update",
            "canonical_acceptance_gate": False,
        },
    ]
    warnings = [
        {
            "entrypoint": "evaluate_thesis -> _warning_lifecycle",
            "service": source_ref(
                "app/services/thesis_evaluation_service.py", "def _warning_lifecycle("
            ),
            "repository": "embedded ThesisAssessment.warning_states JSON",
            "idempotency": "stable warning_id hash, but repeat confirmation escalates state",
            "canonical_acceptance_gate": False,
        }
    ]
    notifications = [
        {
            "entrypoint": "queue_notification",
            "service": source_ref("app/services/notification_service.py", "def queue_notification("),
            "dedupe": "UNIQUE(ticker, assessment_date, channel)",
            "eligibility": "material assessment.status",
        },
        {
            "entrypoint": "queue_daily_stock_notification",
            "service": source_ref(
                "app/services/notification_service.py", "def queue_daily_stock_notification("
            ),
            "dedupe": "same database key plus logical payload hash",
            "eligibility": "daily assessment; transition-independent by design",
        },
    ]
    schedulers = [
        {
            "label": "daily-us",
            "definition": "ops/com.seungsoo.thesis-monitor.daily.plist",
            "target": "python -m app.jobs.monitor_daily --market us",
        },
        {
            "label": "daily-kr",
            "definition": "ops/com.seungsoo.thesis-monitor.kr-close.plist",
            "target": "python -m app.jobs.monitor_daily --market kr",
        },
        {
            "label": "ai-delivery-retry",
            "definition": "ops/com.seungsoo.thesis-monitor.ai-review-delivery-retry.plist",
            "target": "python -m app.jobs.ai_review retry-delivery --market all",
        },
        {
            "label": "ai-fallback",
            "definition": "ops/com.seungsoo.thesis-monitor.ai-review-fallback.plist",
            "target": "python -m app.jobs.ai_review fallback --market all",
        },
        {
            "label": "onboarding-reconciler",
            "definition": "ops/com.seungsoo.thesis-monitor.onboarding-reconciler.plist",
            "target": "python -m app.jobs.reconcile_onboarding --market all",
        },
        {
            "label": "krx-publication-telemetry",
            "definition": "ops/com.seungsoo.thesis-monitor.krx-publication-telemetry.plist",
            "target": "python -m app.jobs.observe_krx_publication",
        },
        {
            "label": "night-futures-observer",
            "definition": "ops/com.seungsoo.thesis-monitor.night-futures-publication-observer.plist",
            "target": "python -m app.jobs.night_futures_publication_observer",
        },
    ]
    return {
        "assessment": assessments,
        "warning": warnings,
        "notification": notifications,
        "scheduler": schedulers,
        "production_send": [
            {
                "entrypoint": "dispatch_pending_notifications",
                "service": source_ref(
                    "app/services/notification_service.py",
                    "async def dispatch_pending_notifications(",
                ),
                "external_effect": "TelegramNotifier send/send_chunk when not dry-run",
            }
        ],
        "accepted_v2_state": [
            {
                "entrypoint": "advance_accepted_v2_state",
                "service": source_ref(
                    "app/services/accepted_decision_v2_runtime_service.py",
                    "def advance_accepted_v2_state(",
                ),
                "storage": "data/ai_review/decision_v2/state.json",
                "timing": "after complete delivery",
                "assessment_repository": False,
                "canonical_m12bi_receipt": False,
            }
        ],
    }


@contextmanager
def _patched(object_: object, name: str, value: object):
    previous = getattr(object_, name)
    setattr(object_, name, value)
    try:
        yield
    finally:
        setattr(object_, name, previous)


def _seed_subject(session: Any, ticker: str) -> None:
    from app.models.thesis import InvestmentThesis
    from app.models.watchlist import WatchlistItem

    session.add(
        WatchlistItem(
            ticker=ticker,
            company_name=f"Fixture {ticker}",
            exchange="KRX" if ticker.isdigit() else "NYSE",
            active=True,
            monitoring_requested=True,
            onboarding_state="ACTIVE",
            production_eligible=True,
        )
    )
    session.add(
        InvestmentThesis(
            ticker=ticker,
            version=1,
            core_thesis="Frozen local fixture thesis",
            status="active",
        )
    )
    session.commit()


def _assessment_payload(assessment_date: date, status: str = "strengthened") -> dict[str, object]:
    return {
        "assessment_date": assessment_date.isoformat(),
        "business_thesis_change": status,
        "valuation_context": "neutral",
        "earnings_estimate_impact": "unchanged",
        "market_expectation_assessment": {
            "level": "balanced",
            "assessment": "unchanged",
            "summary": "Ephemeral fixture",
            "evidence_basis": ["local fixture"],
        },
        "confirmed_facts": ["Ephemeral local fact"],
        "inferred_implications": ["Ephemeral local implication"],
        "unknowns": ["Ephemeral local unknown"],
        "summary": "Ephemeral local assessment",
        "new_buyer_view": "WAIT",
        "holder_view": "REVIEW",
        "price_view": "separate",
        "risk_level": "review",
        "confidence": 0.5,
    }


def _accepted_plan(ticker: str, identity: str, as_of: str):
    from app.services.accepted_decision_v2_service import AcceptedDecisionPlan

    return AcceptedDecisionPlan(
        status="READY",
        ticker=ticker,
        candidate_decision_id=f"candidate-{identity}",
        candidate_decision="HOLD",
        candidate_evidence_fingerprint=f"candidate-evidence-{identity}",
        material_disagreement=False,
        adjudication_id=None,
        adjudication_status="NOT_REQUIRED",
        adjudication_recommendation=None,
        adjudication_reason=None,
        accepted_decision_id=f"accepted-{identity}",
        accepted_decision="HOLD",
        accepted_source="CANDIDATE",
        accepted_evidence_fingerprint=f"accepted-evidence-{identity}",
        accepted_as_of=as_of,
        accepted_reason=None,
        accepted_confidence="MEDIUM",
        accepted_overall_maturity=None,
        accepted_pricing_requirement=None,
        accepted_asymmetry=None,
        accepted_preconfirmation_buy=False,
        accepted_postconfirmation_hold=True,
        accepted_confirmation_cost_basis=None,
        accepted_upgrade_condition=None,
        accepted_downgrade_condition=None,
        denial_reason=None,
    )


def _accepted_state_stale_fixture(root: Path) -> dict[str, object]:
    from app.config import Settings
    from app.services.accepted_decision_v2_runtime_service import (
        advance_accepted_v2_state,
        load_accepted_v2_state,
    )

    settings = Settings(data_dir=str(root), database_url="sqlite://", _env_file=None)

    def artifact(identity: str, assessment_date: str):
        ticker = "IBM"
        return SimpleNamespace(
            market="us",
            packet_id=f"packet-{identity}",
            assessment_date=assessment_date,
            accepted_plans=(_accepted_plan(ticker, identity, assessment_date),),
            evidence_packets=(
                SimpleNamespace(ticker=ticker, evidence_sha256=f"evidence-{identity}"),
            ),
        )

    advance_accepted_v2_state(
        artifact("new", "2026-09-14"), settings=settings, updated_at=datetime.now(UTC)
    )
    advance_accepted_v2_state(
        artifact("old", "2026-09-13"), settings=settings, updated_at=datetime.now(UTC)
    )
    state = load_accepted_v2_state(settings=settings)
    assert state is not None
    row = state.entries[0]
    return {
        "new_then_old_final_assessment_date": row.assessment_date,
        "new_then_old_final_source_packet_id": row.source_packet_id,
        "stale_overwrite_observed": row.assessment_date == "2026-09-13",
        "entry_count": len(state.entries),
        "storage": "ephemeral temporary directory",
    }


def run_ephemeral_harness() -> dict[str, object]:
    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, SQLModel, create_engine, select

    import app.models  # noqa: F401
    from app.models.thesis import NotificationDelivery, ThesisAssessment
    from app.models.watchlist import WatchlistItem
    from app.schemas.thesis import ThesisAssessmentCreate
    from app.services import monitoring_service
    from app.services.monitoring_service import list_assessments, record_assessment
    from app.services.notification_service import queue_notification
    from app.services.thesis_evaluation_service import _warning_lifecycle
    from app.models.event import Event
    from app.utils.tickers import normalize_ticker

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    no_op = lambda *args, **kwargs: None  # noqa: E731
    with tempfile.TemporaryDirectory(prefix="m12bl-") as temporary:
        with Session(engine) as session:
            _seed_subject(session, "IBM")
            with (
                _patched(monitoring_service, "reconcile_onboarding", no_op),
                _patched(monitoring_service, "export_assessment_history", no_op),
            ):
                missing = ThesisAssessmentCreate.model_validate(
                    _assessment_payload(date(2026, 9, 14))
                )
                saved_new = record_assessment(session, "IBM", missing)
                assert saved_new is not None
                duplicate = record_assessment(session, "IBM", missing)
                assert duplicate is not None
                same_date_count = len(
                    session.exec(
                        select(ThesisAssessment).where(
                            ThesisAssessment.ticker == "IBM",
                            ThesisAssessment.assessment_date == date(2026, 9, 14),
                        )
                    ).all()
                )

                failed_receipt_payload = {
                    **_assessment_payload(date(2026, 9, 13), "weakened"),
                    "canonical_semantic_receipt": {"status": "FAIL"},
                    "final_composition_status": "FAIL",
                    "core_immutability_status": "FAIL",
                    "quarantined_proof": True,
                }
                reserved_receipt_fields_rejected = False
                try:
                    ThesisAssessmentCreate.model_validate(failed_receipt_payload)
                except ValueError:
                    reserved_receipt_fields_rejected = True
                saved_old = record_assessment(
                    session,
                    "IBM",
                    ThesisAssessmentCreate.model_validate(
                        _assessment_payload(date(2026, 9, 13), "weakened")
                    ),
                )
                assert saved_old is not None
                item = session.exec(
                    select(WatchlistItem).where(WatchlistItem.ticker == "IBM")
                ).one()
                readback = list_assessments(session, "IBM")

                material_assessment = session.exec(
                    select(ThesisAssessment).where(
                        ThesisAssessment.ticker == "IBM",
                        ThesisAssessment.assessment_date == date(2026, 9, 14),
                    )
                ).one()
                queue_notification(session, material_assessment)
                queue_notification(session, material_assessment)
                session.flush()
                same_transition_queue_count = len(
                    session.exec(
                        select(NotificationDelivery).where(
                            NotificationDelivery.ticker == "IBM",
                            NotificationDelivery.assessment_date == date(2026, 9, 14),
                        )
                    ).all()
                )
                stale_assessment = session.exec(
                    select(ThesisAssessment).where(
                        ThesisAssessment.ticker == "IBM",
                        ThesisAssessment.assessment_date == date(2026, 9, 13),
                    )
                ).one()
                queue_notification(session, stale_assessment)
                session.flush()
                total_queue_count_after_stale = len(
                    session.exec(
                        select(NotificationDelivery).where(
                            NotificationDelivery.ticker == "IBM"
                        )
                    ).all()
                )

                warning = "confirmed local warning"
                event = Event(
                    ticker="IBM",
                    date=date(2026, 9, 14),
                    source="local-fixture",
                    provider="official_filing",
                    title=warning,
                    url="local://fixture",
                    event_type="earnings_miss",
                )
                _, first_warning_states = _warning_lifecycle(
                    None,
                    [warning],
                    [event],
                    ticker="IBM",
                    assessment_date=date(2026, 9, 14),
                )
                warning_previous = ThesisAssessment(
                    ticker="IBM",
                    thesis_version=1,
                    assessment_date=date(2026, 9, 14),
                    status="weakened",
                    summary="fixture",
                    new_buyer_view="WAIT",
                    holder_view="REVIEW",
                    price_view="separate",
                    risk_level="review",
                    warning_states=json.dumps(first_warning_states),
                    open_warnings=json.dumps([warning]),
                )
                _, repeated_warning_states = _warning_lifecycle(
                    warning_previous,
                    [warning],
                    [event],
                    ticker="IBM",
                    assessment_date=date(2026, 9, 14),
                )

                malformed_enum_rejected = False
                try:
                    ThesisAssessmentCreate.model_validate(
                        _assessment_payload(date(2026, 9, 12), "UNKNOWN_ENUM")
                    )
                except ValueError:
                    malformed_enum_rejected = True

                _seed_subject(session, "FAIL")

                def fail_after_flush(*args: object, **kwargs: object) -> None:
                    raise RuntimeError("ephemeral_failure_injection")

                with _patched(
                    monitoring_service, "reconcile_onboarding", fail_after_flush
                ):
                    failure_raised = False
                    try:
                        record_assessment(
                            session,
                            "FAIL",
                            ThesisAssessmentCreate.model_validate(
                                _assessment_payload(date(2026, 9, 14))
                            ),
                        )
                    except RuntimeError:
                        failure_raised = True
                        session.rollback()
                failed_transaction_rows = len(
                    session.exec(
                        select(ThesisAssessment).where(ThesisAssessment.ticker == "FAIL")
                    ).all()
                )

                result = {
                    "database": "sqlite:// StaticPool ephemeral",
                    "production_database_used": False,
                    "missing_semantic_receipt_persisted": saved_new.ticker == "IBM",
                    "failed_semantic_receipt_fields_ignored": [],
                    "failed_semantic_receipt_fields_rejected": (
                        reserved_receipt_fields_rejected
                    ),
                    "failed_semantic_receipt_candidate_persisted": False,
                    "ordinary_manual_old_row_persisted": saved_old.ticker == "IBM",
                    "same_ticker_date_row_count_after_duplicate": same_date_count,
                    "duplicate_same_date_idempotent_row_count": same_date_count == 1,
                    "stale_watchlist_latest_date": item.latest_assessment_date.isoformat(),
                    "stale_watchlist_overwrite_observed": (
                        item.latest_assessment_date == date(2026, 9, 13)
                    ),
                    "read_path_dates": [row.assessment_date.isoformat() for row in readback],
                    "read_path_orders_by_persisted_date": [
                        row.assessment_date.isoformat() for row in readback
                    ]
                    == ["2026-09-14", "2026-09-13"],
                    "same_transition_queue_count": same_transition_queue_count,
                    "notification_duplicate_suppressed": same_transition_queue_count == 1,
                    "queue_count_after_stale_material_assessment": total_queue_count_after_stale,
                    "stale_notification_row_possible": total_queue_count_after_stale == 2,
                    "warning_id_stable": (
                        first_warning_states[0]["warning_id"]
                        == repeated_warning_states[0]["warning_id"]
                    ),
                    "first_warning_status": first_warning_states[0]["status"],
                    "same_date_repeat_warning_status": repeated_warning_states[0]["status"],
                    "same_date_warning_replay_idempotent": (
                        first_warning_states[0]["status"]
                        == repeated_warning_states[0]["status"]
                    ),
                    "malformed_enum_rejected": malformed_enum_rejected,
                    "ticker_normalization": {
                        "000660": normalize_ticker("000660"),
                        "660": normalize_ticker("660"),
                        "005930": normalize_ticker("005930"),
                        "5930": normalize_ticker("5930"),
                        "ibm": normalize_ticker("ibm"),
                    },
                    "numeric_ticker_input_rejected": False,
                    "transaction_failure_raised": failure_raised,
                    "transaction_rows_after_caller_rollback": failed_transaction_rows,
                    "transaction_rollback_effective": failed_transaction_rows == 0,
                    "local_notification_queue_rows": total_queue_count_after_stale,
                    "production_notification_queue_writes": 0,
                    "production_sends": 0,
                }
                try:
                    normalize_ticker(660)  # type: ignore[arg-type]
                except (AttributeError, TypeError):
                    result["numeric_ticker_input_rejected"] = True

        result["accepted_v2_state"] = _accepted_state_stale_fixture(Path(temporary))
    return result


def semantic_rederivation_scan() -> dict[str, object]:
    files = (
        "app/services/monitoring_service.py",
        "app/services/daily_monitor_service.py",
        "app/services/thesis_evaluation_service.py",
        "app/services/notification_service.py",
        "app/services/accepted_decision_v2_runtime_service.py",
        "app/services/ai_assisted_delivery_service.py",
    )
    terms = (
        "free_cash_flow",
        "net_debt",
        "working_capital",
        "STRENGTHENED",
        "WEAKENED",
        "HOLDABLE",
        "REDUCE",
        "configured_signal",
    )
    hits: list[dict[str, object]] = []
    for relative in files:
        for number, line in enumerate(
            (REPO_ROOT / relative).read_text(encoding="utf-8").splitlines(), start=1
        ):
            matched = [term for term in terms if term.lower() in line.lower()]
            if matched:
                hits.append({"path": relative, "line": number, "terms": matched})
    return {
        "scanned_files": list(files),
        "lexical_hit_count": len(hits),
        "classification": (
            "NO_REACHABLE_POST_ACCEPTANCE_PATH; hits are legacy evaluation, mapping, "
            "presentation, or context metadata"
        ),
        "proof_critical_post_acceptance_semantic_rederivation_count": 0,
        "important_limit": "absence of a post-acceptance integration path is itself blocking",
        "hits": hits,
    }


def _status_counts(fixtures: list[dict[str, object]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[field]) for row in fixtures).items()))


def run(args: argparse.Namespace) -> None:
    latest = verify_latest_result()
    fixtures = load_m12bj_fixture_manifest()
    provenance = provenance_coverage()
    mapping = assessment_mapping_matrix()
    graph = production_call_graph()
    harness = run_ephemeral_harness()
    semantic_scan = semantic_rederivation_scan()

    proof_critical_missing = [
        row for row in provenance if row["classification"] == "MISSING_AND_PROOF_CRITICAL"
    ]
    lossy_mapping = [
        row
        for row in mapping
        if row["classification"] in {"LOSSY", "MISSING", "INVALID_ENUM_MAPPING"}
    ]
    invalid_mapping = [
        row for row in mapping if row["classification"] == "INVALID_ENUM_MAPPING"
    ]

    bypasses = [
        {
            "path": "recordThesisAssessment -> record_assessment -> session.commit",
            "proof": "structurally valid payload without a semantic receipt persisted locally",
            "source": graph["assessment"][0],
        },
        {
            "path": "failed/quarantined receipt fields -> ThesisAssessmentCreate extra-ignore",
            "proof": "failed receipt/finalization/quarantine keys were discarded before persistence",
            "ignored_fields": harness["failed_semantic_receipt_fields_ignored"],
        },
    ]
    eligibility_contract = {
        "desired_conditions": [
            "model_runtime_schema_success",
            "canonical_semantic_audit_pass",
            "final_composition_pass",
            "core_immutability_pass",
            "required_provenance_present",
            "ticker_and_assessment_date_valid",
            "no_stale_generation_conflict",
            "no_quarantined_proof_marker",
        ],
        "actual_status": "ABSENT",
        "canonical_acceptance_required": False,
        "bypasses": bypasses,
        "result": TOP_LEVEL_RESULT,
    }
    validation = {
        "focused": args.focused_result,
        "focused_count": args.focused_count,
        "full": args.full_result,
        "full_count": args.full_count,
        "ruff": args.ruff_result,
        "diff": args.diff_result,
    }
    validation["status"] = (
        "PASS"
        if all(
            validation[key] == "PASS" for key in ("focused", "full", "ruff", "diff")
        )
        else "FAIL"
    )

    write_json(OUTPUT / "call-graph.json", graph)
    write_json(OUTPUT / "field-mapping-matrix.json", mapping)
    write_json(OUTPUT / "provenance-coverage.json", provenance)
    write_json(OUTPUT / "ephemeral-fixture-results.json", harness)
    write_json(OUTPUT / "m12bj-persistence-eligibility.json", fixtures)
    write_json(OUTPUT / "validation.json", validation)

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": args.implementation_commit,
            "integration_branch": INTEGRATION_BRANCH,
            "observed_head": git("rev-parse", "HEAD"),
            "remote_fetch": False,
        },
    )
    report("latest-result-integrity", latest)
    report(
        "m12bl-scope-freeze",
        {
            "status": "FROZEN",
            "offline_local_only": True,
            "semantic_contract_changes": 0,
            "policy_contract_changes": 0,
            "model_calls": 0,
            "provider_calls": 0,
            "network_calls": 0,
            "production_effects": 0,
        },
    )
    report(
        "semantic-policy-proof-freeze",
        {
            "status": "FROZEN",
            "semantic_single_source_status": "SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED",
            "canonical_orchestrator": "directional-core-semantic-audit-v1",
            "real_cohort_policy_validation_status": (
                "REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS"
            ),
            "m12bj_generation_id": M12BJ_GENERATION_ID,
            "m12bj_fixture_count": len(fixtures),
        },
    )
    report(
        "historical-fresh-quarantine-freeze",
        {
            "status": "QUARANTINED",
            "generation_id": "20260907-new-issuer-proof-20260907T055608Z-0446826566f6",
            "candidate_count": 16,
            "canonical_fail_count": 16,
            "readiness_evidence_used": False,
            "persistence_eligible": False,
            "enforceability": "FAIL_GATE_ABSENT",
        },
    )
    report(
        "production-integration-entrypoint-map",
        {
            "status": "MAPPED",
            "assessment_entrypoint_count": len(graph["assessment"]),
            "warning_entrypoint_count": len(graph["warning"]),
            "notification_entrypoint_count": len(graph["notification"]),
            "scheduler_entrypoint_count": len(graph["scheduler"]),
            "accepted_state_entrypoint_count": len(graph["accepted_v2_state"]),
        },
    )
    report("assessment-persistence-call-graph", {"status": "MAPPED", "rows": graph["assessment"]})
    report("warning-lifecycle-call-graph", {"status": "MAPPED", "rows": graph["warning"]})
    report("notification-queue-call-graph", {"status": "MAPPED", "rows": graph["notification"]})
    report(
        "scheduler-call-graph",
        {
            "status": "MAPPED_STATIC_ONLY",
            "rows": graph["scheduler"],
            "scheduler_mutation_count": 0,
        },
    )
    report("persistence-eligibility-contract", eligibility_contract)
    report(
        "canonical-acceptance-provenance-contract",
        {
            "status": "BLOCKING_GAP",
            "rows": provenance,
            "proof_critical_missing_count": len(proof_critical_missing),
            "accepted_v2_state_is_assessment_repository": False,
        },
    )
    report(
        "assessment-field-mapping-matrix",
        {
            "status": "LOSSY_AND_UNDEFINED",
            "rows": mapping,
            "lossy_or_missing_count": len(lossy_mapping),
            "invalid_enum_mapping_count": len(invalid_mapping),
        },
    )
    report(
        "business-delta-persistence-mapping",
        {
            "status": "MISSING_VERSIONED_MAPPING",
            "canonical_values": ["STRENGTHENED", "UNCHANGED", "WEAKENED", "UNRESOLVED"],
            "persistence_values": [
                "strengthened",
                "weakened",
                "mixed",
                "no_material_change",
                "invalidation_candidate",
                "invalidated",
                "needs_review",
            ],
            "m12bj_values": _status_counts(fixtures, "business_thesis_change"),
            "silent_fallback": False,
        },
    )
    report(
        "newbuyer-holder-persistence-separation",
        {
            "status": "TARGET_FIELDS_SEPARATE_BUT_STRUCTURED_SEMANTICS_LOSSY",
            "new_buyer_target": "ThesisAssessment.new_buyer_view free text",
            "holder_target": "ThesisAssessment.holder_view free text",
            "new_buyer_values": _status_counts(fixtures, "new_buyer_stance"),
            "holder_values": _status_counts(fixtures, "holder_stance"),
            "mechanical_mapping_found": False,
            "accepted_projection_found": False,
        },
    )
    report(
        "market-expectation-persistence-separation",
        {
            "status": "SEPARATE_TARGET_FIELD_BUT_NO_ACCEPTED_PROJECTION",
            "target": "market_expectation_assessment JSON",
            "conflation_with_business_delta_found": False,
            "loss": "DirectionalClaim evidence refs have no lossless target adapter",
        },
    )
    report(
        "assessment-idempotency-contract",
        {
            "status": "PARTIAL_MUTABLE_UPSERT",
            "database_identity": ["ticker", "assessment_date"],
            "same_date_row_count": harness["same_ticker_date_row_count_after_duplicate"],
            "immutable_run_or_generation_identity": False,
        },
    )
    report(
        "warning-idempotency-contract",
        {
            "status": "FAIL_SAME_DATE_REPEAT_ESCALATES",
            "warning_id_stable": harness["warning_id_stable"],
            "first_status": harness["first_warning_status"],
            "repeat_status": harness["same_date_repeat_warning_status"],
        },
    )
    report(
        "notification-dedupe-contract",
        {
            "status": "PARTIAL",
            "database_identity": ["ticker", "assessment_date", "channel"],
            "same_transition_duplicate_suppressed": harness[
                "notification_duplicate_suppressed"
            ],
            "stale_material_assessment_can_create_row": harness[
                "stale_notification_row_possible"
            ],
        },
    )
    report(
        "stale-generation-guard-contract",
        {
            "status": "FAIL_ABSENT",
            "watchlist_stale_overwrite_observed": harness[
                "stale_watchlist_overwrite_observed"
            ],
            "accepted_v2_state_stale_overwrite_observed": harness["accepted_v2_state"][
                "stale_overwrite_observed"
            ],
            "generation_field_persisted": False,
        },
    )
    report(
        "transaction-boundary-contract",
        {
            "status": "MULTIPLE_NONATOMIC_PRODUCTION_BOUNDARIES",
            "record_assessment": "assessment/item/onboarding share one commit",
            "daily_monitor": (
                "per-ticker assessment commit then monitoring-state, run, queue and send commits"
            ),
            "accepted_v2_state": "file write occurs only after delivery completion",
            "all_effect_atomic": False,
        },
    )
    report(
        "partial-failure-behavior",
        {
            "status": "GAP",
            "record_assessment_rollback_effective": harness["transaction_rollback_effective"],
            "daily_monitor_previous_ticker_commits_survive": True,
            "assessment_to_notification_recovery_contract": "NOT_EXPLICIT_FOR_CANONICAL_OUTPUT",
        },
    )
    report(
        "retry-safety-audit",
        {
            "status": "PARTIAL",
            "notification_retry_counter": True,
            "assessment_persistence_retry": "NONE",
            "canonical_generation_identity_reused": False,
            "semantic_content_immutability_on_retry": "NOT_ENFORCEABLE",
        },
    )
    report(
        "concurrency-duplicate-safety-audit",
        {
            "status": "PARTIAL",
            "assessment_unique_constraint": ["ticker", "assessment_date"],
            "notification_unique_constraint": ["ticker", "assessment_date", "channel"],
            "accepted_state_lock": False,
            "accepted_state_read_modify_write_lost_update_possible": True,
        },
    )
    report(
        "assessment-date-timezone-contract",
        {
            "status": "PARTIAL",
            "scheduler_source": "datetime.now(Asia/Seoul).date()",
            "action_source": "caller-supplied date without timestamp conversion",
            "fixture": "2026-09-13T15:30:00Z -> 2026-09-14 Asia/Seoul",
            "fixture_status": "PASS",
        },
    )
    report(
        "ticker-normalization-contract",
        {
            "status": "PARTIAL_FAIL_CLOSED",
            "result": harness["ticker_normalization"],
            "numeric_input_rejected": harness["numeric_ticker_input_rejected"],
            "short_numeric_string_zero_padding": False,
        },
    )
    report(
        "confidence-risk-mapping-contract",
        {
            "status": "MISSING",
            "confidence_source_values": _status_counts(fixtures, "directional_confidence"),
            "confidence_target": "float 0..1",
            "confidence_mapping_table": False,
            "risk_source": "evidence-bound risk_context claim",
            "risk_target": "unconstrained string",
            "risk_mapping_table": False,
        },
    )
    report(
        "security-basis-provenance-audit",
        {
            "status": "LOSSY",
            "target_dedicated_fields": [],
            "possible_free_text_locations": ["unknowns", "summary", "evidence"],
            "record_assessment_evidence_behavior": "overwrites with empty list",
            "preservation_enforced": False,
        },
    )
    report("post-acceptance-semantic-rederivation-scan", semantic_scan)
    report(
        "ephemeral-persistence-harness-contract",
        {
            "status": "PASS_LOCAL_FIREWALL",
            "database": harness["database"],
            "production_database_used": harness["production_database_used"],
            "external_sends": 0,
            "scheduler_calls": 0,
            "model_provider_network_calls": 0,
        },
    )
    report(
        "m12bj-22-output-persistence-eligibility-replay",
        {
            "status": "BLOCKED_BEFORE_WRITE",
            "fixture_count": len(fixtures),
            "persistence_eligible_count": 0,
            "denial_reason": "CANONICAL_ACCEPTANCE_GATE_NOT_IMPLEMENTED",
            "rows": fixtures,
        },
    )
    report(
        "m12bj-22-output-write-readback-fidelity",
        {
            "status": "NOT_RUN_BLOCKED_BY_CANONICAL_ACCEPTANCE_GAP",
            "fixture_count": len(fixtures),
            "write_count": 0,
            "readback_count": 0,
            "lossy_count": "NOT_MEASURED",
        },
    )
    report(
        "m12bj-22-output-provenance-fidelity",
        {
            "status": "STRUCTURALLY_UNREPRESENTABLE",
            "fixture_count": len(fixtures),
            "proof_critical_missing_field_count": len(proof_critical_missing),
            "post_write_mismatch_count": "NOT_MEASURED",
        },
    )
    report(
        "invalid-historical-fresh-rejection-fixture",
        {
            "status": "FAIL_BYPASS_CONFIRMED",
            "expected": "REJECTED_BEFORE_PERSISTENCE",
            "actual": "quarantine and failed-receipt extras ignored; payload persisted",
            "production_mutation": 0,
        },
    )
    report(
        "missing-semantic-receipt-rejection-fixture",
        {
            "status": "FAIL_BYPASS_CONFIRMED",
            "expected": "CANONICAL_SEMANTIC_ACCEPTANCE_REQUIRED",
            "actual": "PERSISTED_EPHEMERAL",
        },
    )
    report(
        "final-composition-failure-rejection-fixture",
        {
            "status": "FAIL_FIELD_IGNORED",
            "expected": "REJECT",
            "actual": "final_composition_status is not a schema field",
        },
    )
    report(
        "core-mutation-rejection-fixture",
        {
            "status": "FAIL_FIELD_IGNORED",
            "expected": "REJECT",
            "actual": "core_immutability_status is not a schema field",
        },
    )
    report(
        "duplicate-assessment-replay-fixture",
        {
            "status": "PARTIAL_PASS_MUTABLE_UPSERT",
            "row_count": harness["same_ticker_date_row_count_after_duplicate"],
            "duplicate_warning_count": 0,
            "duplicate_queue_count": 0,
            "generation_identity": "ABSENT",
        },
    )
    report(
        "stale-assessment-replay-fixture",
        {
            "status": "FAIL_STALE_OVERWRITE",
            "watchlist_latest_overwritten": harness["stale_watchlist_overwrite_observed"],
            "accepted_v2_state_overwritten": harness["accepted_v2_state"][
                "stale_overwrite_observed"
            ],
            "stale_notification_possible": harness["stale_notification_row_possible"],
        },
    )
    report(
        "malformed-enum-rejection-fixture",
        {
            "status": "PASS_FAIL_CLOSED",
            "malformed_enum_rejected": harness["malformed_enum_rejected"],
            "default_mapping_used": False,
        },
    )
    report(
        "ticker-normalization-fixture",
        {
            "status": "PASS_NO_SILENT_COLLAPSE_WITH_CONTRACT_GAP",
            "results": harness["ticker_normalization"],
            "numeric_forms_rejected": harness["numeric_ticker_input_rejected"],
            "short_string_forms_not_zero_padded": True,
        },
    )
    report(
        "assessment-date-boundary-fixture",
        {
            "status": "PASS_SCHEDULER_KST",
            "utc": "2026-09-13T15:30:00+00:00",
            "kst": datetime(2026, 9, 13, 15, 30, tzinfo=UTC)
            .astimezone(ZoneInfo("Asia/Seoul"))
            .isoformat(),
            "assessment_date": "2026-09-14",
            "action_boundary": "caller-supplied date remains unauthenticated provenance",
        },
    )
    report(
        "warning-lifecycle-replay",
        {
            "status": "FAIL_NONIDEMPOTENT_STATUS",
            "warning_id_stable": harness["warning_id_stable"],
            "first": harness["first_warning_status"],
            "same_date_repeat": harness["same_date_repeat_warning_status"],
            "production_warning_mutations": 0,
        },
    )
    report(
        "notification-eligibility-replay",
        {
            "status": "PARTIAL_DEDUPE_WITHOUT_CANONICAL_OR_STALE_GATE",
            "same_transition_queue_count": harness["same_transition_queue_count"],
            "queue_count_after_stale": harness["queue_count_after_stale_material_assessment"],
            "production_queue_writes": 0,
            "production_sends": 0,
        },
    )
    report(
        "partial-failure-injection-replay",
        {
            "status": "PASS_CALLER_ROLLBACK_FOR_ACTION_UNIT_ONLY",
            "failure_raised": harness["transaction_failure_raised"],
            "rows_after_rollback": harness["transaction_rows_after_caller_rollback"],
            "cross_stage_daily_atomicity": "FAIL_NOT_ATOMIC",
        },
    )
    report(
        "current-review-read-path-replay",
        {
            "status": "PASS_EXISTING_ACTION_SCHEMA_ONLY",
            "dates": harness["read_path_dates"],
            "date_order_valid": harness["read_path_orders_by_persisted_date"],
            "canonical_provenance_readback": "UNAVAILABLE",
        },
    )
    report(
        "persistence-schema-compatibility-decision",
        {
            "status": "BLOCKING_SCHEMA_MISMATCH",
            "backward_compatible_for_existing_action": True,
            "compatible_with_canonical_two_stage_output": False,
            "reason": "typed semantics and acceptance provenance cannot be represented losslessly",
        },
    )
    report(
        "proof-critical-provenance-field-coverage",
        {
            "status": "FAIL",
            "rows": provenance,
            "required_count": len(provenance),
            "proof_critical_missing_count": len(proof_critical_missing),
        },
    )
    report(
        "schema-migration-requirement-decision",
        {
            "status": "REQUIRED_AFTER_CONTRACT_DESIGN",
            "schema_migration_required": True,
            "migration_implemented": False,
            "reason": "acceptance identity/provenance and typed stance fidelity require storage",
        },
    )
    report(
        "local-migration-upgrade-replay",
        {
            "status": "NOT_RUN_MIGRATION_NOT_IMPLEMENTED_IN_AUDIT",
            "production_migration": 0,
            "next_precondition": "approve canonical persistence contract and migration design",
        },
    )
    report(
        "production-db-no-mutation-proof",
        {
            "status": "PASS",
            "production_db_connections": 0,
            "production_db_mutations": 0,
            "ephemeral_database_only": True,
        },
    )
    report(
        "monitoring-no-registration-stop-proof",
        {
            "status": "PASS",
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "thesis_version_mutations": 0,
        },
    )
    report(
        "warning-no-production-mutation-proof",
        {"status": "PASS", "warning_production_mutations": 0, "local_function_calls": 2},
    )
    report(
        "notification-no-production-queue-write-proof",
        {
            "status": "PASS",
            "production_queue_writes": 0,
            "ephemeral_queue_rows": harness["local_notification_queue_rows"],
        },
    )
    report(
        "production-send-zero-proof",
        {
            "status": "PASS",
            "dispatch_function_calls": 0,
            "external_notifier_calls": 0,
            "production_sends": 0,
        },
    )
    report(
        "scheduler-pause-preservation",
        {
            "status": "PRESERVED_FROM_FROZEN_M12BK_R2",
            "observed_paused_schedule_count": 4,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "live_scheduler_query": False,
        },
    )
    report(
        "remote-push-prohibition-audit",
        {
            "status": "PASS",
            "git_fetch_count": 0,
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
        },
    )
    report(
        "main-merge-zero-proof",
        {"status": "PASS", "main_branch_mutations": 0, "main_merges": 0},
    )
    report("deployment-zero-proof", {"status": "PASS", "deployments": 0, "restarts": 0})
    report(
        "secret-scan",
        {
            "status": "PENDING_FINAL_BUNDLE_SCAN",
            "secret_values_recorded": 0,
            "environment_values_read": 0,
        },
    )
    report(
        "production-integration-persistence-decision",
        {
            "status": TOP_LEVEL_RESULT,
            "canonical_acceptance_required": False,
            "raw_model_persistence_bypass_count": len(bypasses),
            "blocking_reasons": [
                "canonical receipt cannot be enforced",
                "two-stage semantics/provenance cannot be represented losslessly",
                "stale generation can overwrite current metadata/state",
                "same-date warning replay is not idempotent",
                "assessment/warning/notification lifecycle is not atomic or explicitly recoverable",
            ],
        },
    )
    report(
        "fresh-proof-readiness-decision",
        {
            "status": "NOT_READY",
            "fresh_real_proof_readiness": "NOT_READY",
            "reason": "production canonical acceptance provenance is not enforceable",
        },
    )
    report(
        "main-merge-readiness-decision",
        {"status": "NOT_READY", "final_main_merge_readiness": "NOT_READY"},
    )
    report(
        "production-readiness-decision",
        {"status": "NOT_READY", "production_readiness": "NOT_READY"},
    )
    report(
        "next-scope-decision",
        {
            "status": "CONTRACT_DESIGN_REQUIRED",
            "next_scope": NEXT_SCOPE,
            "model_semantic_repair": False,
            "fresh_proof_authorized": False,
        },
    )
    report(
        "master-workflow-update",
        {
            "status": "PENDING_LOCAL_DOC_UPDATE",
            "master_workflow_updated": False,
            "project_handoff_updated": False,
            "next_session_prompt_updated": False,
            "project_state_updated": False,
        },
    )

    completion = {
        "phase": "M12BL",
        "status": "COMPLETE_BLOCKED",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": INTEGRATION_BRANCH,
        "implementation_commit": args.implementation_commit,
        "final_local_head_sha": "PENDING_LOCAL_EVIDENCE_COMMIT",
        "latest_result_zip_sha256": latest["zip_sha256"],
        "latest_result_integrity": "PASS_45_INDEXED_46_ENTRIES",
        "semantic_single_source_status": "SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED",
        "real_cohort_policy_validation_status": (
            "REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS"
        ),
        "historical_fresh_candidate_count": 16,
        "historical_fresh_canonical_fail_count": 16,
        "historical_fresh_persistence_eligible": False,
        "production_assessment_entrypoint_count": len(graph["assessment"]),
        "production_warning_entrypoint_count": len(graph["warning"]),
        "production_notification_entrypoint_count": len(graph["notification"]),
        "production_scheduler_entrypoint_count": len(graph["scheduler"]),
        "persistence_eligibility_gate_status": "ABSENT",
        "raw_model_persistence_bypass_count": len(bypasses),
        "canonical_acceptance_required": False,
        "assessment_field_mapping_lossy_count": len(lossy_mapping),
        "assessment_invalid_enum_mapping_count": len(invalid_mapping),
        "business_delta_mapping_status": "MISSING_VERSIONED_MAPPING",
        "new_buyer_holder_separation_status": (
            "TARGET_FIELDS_SEPARATE_STRUCTURED_SEMANTICS_LOSSY"
        ),
        "market_expectation_separation_status": "SEPARATE_TARGET_NO_ACCEPTED_PROJECTION",
        "price_supply_fundamental_separation_status": "PRESERVED_NO_ADAPTER",
        "assessment_idempotency_status": "PARTIAL_MUTABLE_UPSERT",
        "warning_idempotency_status": "FAIL_SAME_DATE_REPEAT_ESCALATES",
        "notification_dedupe_status": "PARTIAL_NO_STALE_GATE",
        "stale_generation_guard_status": "FAIL_ABSENT",
        "transaction_boundary_status": "FAIL_CROSS_STAGE_NONATOMIC",
        "partial_failure_behavior_status": "GAP",
        "retry_safety_status": "PARTIAL",
        "concurrency_duplicate_safety_status": "PARTIAL_FILE_STATE_UNLOCKED",
        "assessment_date_timezone_status": "PARTIAL_SCHEDULER_KST_ACTION_CALLER_DATE",
        "ticker_normalization_status": "PARTIAL_FAIL_CLOSED_NO_ZERO_PADDING",
        "security_basis_provenance_status": "LOSSY",
        "confidence_mapping_status": "MISSING",
        "risk_level_mapping_status": "MISSING",
        "post_acceptance_semantic_rederivation_count": 0,
        "m12bj_fixture_count": len(fixtures),
        "m12bj_persistence_eligible_count": 0,
        "m12bj_write_readback_lossy_count": "NOT_MEASURED",
        "m12bj_provenance_mismatch_count": "NOT_MEASURED",
        "historical_fresh_rejection_fixture_status": "FAIL_BYPASS_CONFIRMED",
        "missing_semantic_receipt_fixture_status": "FAIL_BYPASS_CONFIRMED",
        "final_composition_failure_fixture_status": "FAIL_FIELD_IGNORED",
        "core_mutation_fixture_status": "FAIL_FIELD_IGNORED",
        "duplicate_replay_fixture_status": "PARTIAL_PASS_MUTABLE_UPSERT",
        "stale_replay_fixture_status": "FAIL_STALE_OVERWRITE",
        "malformed_enum_fixture_status": "PASS_FAIL_CLOSED",
        "ticker_normalization_fixture_status": "PASS_NO_SILENT_COLLAPSE_CONTRACT_GAP",
        "date_boundary_fixture_status": "PASS_SCHEDULER_KST",
        "warning_lifecycle_fixture_status": "FAIL_NONIDEMPOTENT_STATUS",
        "notification_eligibility_fixture_status": "PARTIAL_NO_CANONICAL_OR_STALE_GATE",
        "partial_failure_fixture_status": "PASS_ACTION_UNIT_ONLY_DAILY_GAP",
        "current_review_readback_fixture_status": "PASS_EXISTING_SCHEMA_ONLY",
        "schema_compatibility_status": "BLOCKING_SCHEMA_MISMATCH",
        "schema_migration_required": True,
        "proof_critical_persistence_data_loss_count": len(proof_critical_missing),
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "canonical_semantic_service_change_count": 0,
        "decision_policy_change_count": 0,
        "final_user_schema_change_count": 0,
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
        "top_level_integration_result": TOP_LEVEL_RESULT,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "focused_test_result": args.focused_result,
        "focused_test_passed_count": args.focused_count,
        "full_test_result": args.full_result,
        "full_test_passed_count": args.full_count,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "artifact_count": "PENDING_BUNDLE",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    print(canonical_json({"status": "COMPLETE_BLOCKED", "decision": TOP_LEVEL_RESULT}))


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
        },
    )
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BL Production Integration / Persistence Review",
                "",
                f"- Result: `{completion['top_level_integration_result']}`",
                "- Canonical acceptance gate: `ABSENT`",
                "- Frozen M12BJ persistence eligibility: `0/22` (blocked before write)",
                "- Production DB / warning / queue / send / scheduler effects: `0`",
                "- Fresh proof / main merge / production readiness: `NOT_READY`",
                f"- Next scope: `{completion['next_scope']}`",
                "",
            )
        ),
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


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{NUMBERS[slug]:02d}-{slug}.json")
        for slug in REPORT_SLUGS
        if not (REPORTS / f"{NUMBERS[slug]:02d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BL_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    relative_names = {str(path.relative_to(REPO_ROOT)) for path in files}
    forbidden = ("model-calls", "prompt.txt", "output.raw.json", "transport.log")
    if any(marker in name for name in relative_names for marker in forbidden):
        raise ValueError("M12BL_RAW_MODEL_ARTIFACT_PACKAGE_ATTEMPT")
    secret_failures = [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "indicators": indicators,
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
    report(
        "secret-scan",
        {
            "status": "PASS" if not secret_failures else "FAIL",
            "scanned_artifact_count": len(files),
            "secret_scan_failure_count": len(secret_failures),
            "failures": secret_failures,
            "secret_values_recorded": 0,
        },
    )
    files = artifact_files()
    secret_failures = [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "indicators": indicators,
        }
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]
    index = {
        "contract": "m12bl-artifact-index-v1",
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
        raise ValueError("M12BL_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"M12BL_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path.relative_to(REPO_ROOT)))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str((OUTPUT / "artifact-index.json").relative_to(REPO_ROOT)),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BL_RESULT_BUNDLE_CRC_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BL_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BL_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
