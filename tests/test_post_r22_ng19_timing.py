"""One diagnostic pilot, excluded from the final Native closure node census.

Uses the existing synthetic in-memory SQLite/MockTransport fixture, never an
operating DB or network. The outer harness owns the 180/300-second wall budget.
"""
import time

from app.services.canonical_native_admission import (
    CanonicalNativeAdmission, CanonicalToNativeAdmissionProducer,
)
from app.services.canonical_native_source_owner import prepare_owned_monitoring_source
from app.services.unified_stock_acquisition import UNIVERSE
from tests.ng19_timing import emit, observe_original_calls, span
from tests.test_post_r22_ng18_manual_native import original_source_args


def test_corz_original_source_producer_timing(tmp_path, record_property):
    owner = None
    durations = {}
    emit("diagnostic_start", node="test_corz_original_source_producer_timing",
         final_census=False, full_cohort=22, b2_enabled=False)
    try:
        with observe_original_calls("ng19-p0-corz"):
            started = time.monotonic_ns()
            with span("owner_fixture", subjects=22):
                args = original_source_args(tmp_path / "synthetic")
            durations["owner_fixture_ns"] = time.monotonic_ns() - started
            started = time.monotonic_ns()
            with span("whole_source", subjects=22):
                source, owner = prepare_owned_monitoring_source(enabled=True, **args)
            durations["whole_source_ns"] = time.monotonic_ns() - started
            expected = {ticker for tickers in UNIVERSE.values() for ticker in tickers}
            assert len(expected) == 22 and set(source["stocks"]) == set(source["prepared"]) == expected
            started = time.monotonic_ns()
            with span("producer", ticker="CORZ", market="us"):
                admission = CanonicalToNativeAdmissionProducer(owner).produce_source_inputs(
                    "CORZ", request_id="ng19-p0:CORZ")
            durations["producer_ns"] = time.monotonic_ns() - started
            assert type(admission) is CanonicalNativeAdmission
            assert admission.ticker == "CORZ" and admission.source_owner is owner
        record_property("ng19_p0", dict(durations, status="PRODUCER_RETURNED_ONLY",
            final_census=False, manual_parent_proven=False, original_consumer_proven=False,
            fixture_provenance="EXISTING_SYNTHETIC_ORIGINAL_SOURCE", b2_enabled=False))
        emit("diagnostic_completed", status="PRODUCER_RETURNED_ONLY", **durations)
    finally:
        if owner is not None:
            with span("source_owner_close"):
                owner.close()
