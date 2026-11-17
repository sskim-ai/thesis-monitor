"""Regression for exact B subject/context scope with a typed limitation."""
import pytest

from app.services.model_execution_plan import CohortSubject, FrozenCohort
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE


def test_b_capture_keeps_only_frozen_ordinary_subjects(tmp_path, monkeypatch):
    instant = "2026-11-17T09:00:00+00:00"
    names = UNIVERSE["us"]
    cohort = FrozenCohort("fixture", "source", "2026-11-16", instant, instant,
        tuple(CohortSubject("us", name, "SEC:" + name, instant, digest(name)) for name in names),
        (("us", digest("fixture-owner")),), digest("fixture-scope"), limitation_subjects=("SKHY",))
    session = object.__new__(ProductionMonitoringSession)
    monkeypatch.setattr(session, "_verify_native_source", lambda: None)
    session._manual_source_owner = None
    session._frozen_cohort = cohort
    session.market = "us"
    session.limitation_subjects = frozenset(cohort.limitation_subjects)
    session.source = {"valuation_contexts": {name: None for name in names}}
    session.requests = tmp_path
    session.gen, session.source_gen = cohort.run_id, cohort.source_generation

    batch = next(row for row in session.decision_batch_topology() if row["batch"] == 3)
    assert batch["subjects"] == ["MU", "RXRX"]
    schema = {
        "type": "object", "properties": {"answer": {"type": "string"}},
        "required": ["answer"], "additionalProperties": False,
    }
    context = {"MU": {}, "RXRX": {}}
    for subjects in (["MU"], ["MU", "SKHY"], ["MU", "RXRX", "SKHY"]):
        with pytest.raises(ValueError, match="production_request_subject_scope"):
            session.capture("pass-b", dict(batch, subjects=subjects), context, schema, "fixture")
    for altered in ({"MU": {}}, {**context, "SKHY": {}}):
        with pytest.raises(ValueError, match="production_pass_b_context_scope"):
            session.capture("pass-b", batch, altered, schema, "fixture")
    for stage in ("core", "pass-a"):
        with pytest.raises(ValueError, match="production_request_subject_scope"):
            session.capture(stage, batch, context, schema, "fixture")
    request = session.capture("pass-b", batch, context, schema, "fixture")
    session.captured = {"B": [request]}
    session.verify_model_build("B", request)
    session._accepted_batches = set()
    session.sealed = tmp_path / "sealed"
    with pytest.raises(ValueError, match="production_internal_schema_or_request_drift"):
        session.accept("B", request, {"answer": "valid", "SKHY": {"spurious": True}})
    assert not session._accepted_batches
