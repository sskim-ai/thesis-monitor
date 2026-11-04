"""Original canonical source preparation with a live extraction capability.

Digests bind distinct domains; they do not grant economic use. This capability
does not authorize model dispatch, a current Class-C cycle or Native direction.
Trusted in-process Python composition is the boundary, not hostile Python.
"""
from copy import deepcopy
import os
from threading import RLock
from weakref import WeakKeyDictionary

from app.services.canonical_monitoring_source import prepare_monitoring_source
from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE

CONTRACT = "canonical-prepared-source-owner-v1"
_OWNERS = WeakKeyDictionary()
_LOCK = RLock()


def _require(condition, reason):
    if not condition:
        raise ValueError("canonical_native_" + reason)


def _scoped(source, market):
    result = {**deepcopy(source), "markets": {market: deepcopy(source["markets"][market])}}
    for key in ("stocks", "prepared", "valuation_contexts"):
        result[key] = {t: deepcopy(source[key][t]) for t in UNIVERSE[market]}
    return result


class CanonicalPreparedSourceOwner:
    def __init__(self):
        raise ValueError("canonical_native_backend_issuance_required")

    def _record(self):
        with _LOCK:
            row = _OWNERS.get(self)
            _require(row is not None and not row["closed"], "live_source_owner_required")
            _require(row["pid"] == os.getpid(), "source_parent_pid_mismatch")
            _require(digest(row["source"]) == row["source_sha256"], "source_content_drift")
            for stock in row["source"]["stocks"].values():
                verified_owned_packet_view(stock)
            return row

    def source(self, market=None):
        row = self._record()
        if market is None:
            return deepcopy(row["source"])
        _require(market in UNIVERSE, "market_not_owned")
        return _scoped(row["source"], market)

    def relationship(self, market):
        row = self._record()
        inner = self.source(market)
        return dict(contract=CONTRACT, market=market,
            generation_id=row["generation_id"],
            source_generation_id=inner["source_generation_id"],
            subjects=list(UNIVERSE[market]),
            outer_source_envelope_sha256=row["outer_sha256"],
            prepared_source_sha256=row["source_sha256"],
            inner_consumed_source_sha256=digest(inner),
            subject_sha256={t: digest(dict(stock=inner["stocks"][t],
                prepared=inner["prepared"][t])) for t in UNIVERSE[market]})

    def resolve_subject(self, ticker):
        row = self._record()
        _require(ticker in row["source"]["stocks"], "subject_not_owned")
        stock = row["source"]["stocks"][ticker]
        prepared = row["source"]["prepared"][ticker]
        market = stock["market"]
        relationship = self.relationship(market)
        return dict(stock=deepcopy(stock), prepared=deepcopy(prepared),
            source_authority=deepcopy(prepared["source_authority"]), market=market,
            generation_id=row["generation_id"],
            source_generation_id=row["source"]["source_generation_id"],
            cutoff=stock["packet"]["generated_at"],
            outer_source_envelope_sha256=row["outer_sha256"],
            inner_consumed_source_sha256=relationship["inner_consumed_source_sha256"],
            source_relationship_sha256=digest(relationship))

    def close(self):
        with _LOCK:
            row = _OWNERS.get(self)
            _require(row is not None, "live_source_owner_required")
            row["closed"] = True


def prepare_owned_monitoring_source(*, enabled=False, **kwargs):
    """No alternate parser: issue only after every original canonical preflight."""
    _require(enabled is True, "source_feature_disabled")
    from app.services.canonical_market_projection import project_production_market_context
    from scripts.r2b_r5_market_adapter import project_sealed_market_context
    _require(kwargs.get("market_projector", project_production_market_context) in (
        project_production_market_context, project_sealed_market_context), "original_market_projector_required")
    whole = kwargs["whole"]
    _require(set(whole["packets"]) == set(UNIVERSE) and all(
        set(whole["packets"][m]["stocks"]) == set(ts) for m, ts in UNIVERSE.items()),
        "exact_full_cohort_required")
    source = prepare_monitoring_source(**kwargs)
    subjects = {t for ts in UNIVERSE.values() for t in ts}
    _require(set(source["stocks"]) == set(source["prepared"]) == subjects
        and set(source["markets"]) == set(UNIVERSE), "exact_full_cohort_required")
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            stock, prepared = source["stocks"][ticker], source["prepared"][ticker]
            verified_owned_packet_view(stock)
            _require(stock["ticker"] == ticker and stock["market"] == market
                and prepared["mode"] == "EVIDENCE_BASED"
                and stock["fresh_run_id"] == source["source_generation_id"]
                and prepared["initial_chain"]["source_generation_id"] == source["source_generation_id"]
                and prepared["initial_chain"]["execution_generation_id"] == kwargs["generation"]
                and prepared["view_receipt"]["raw_source_sha256"] == digest(stock),
                "original_subject_scope_required")
    handle = object.__new__(CanonicalPreparedSourceOwner)
    with _LOCK:
        _OWNERS[handle] = dict(source=deepcopy(source), source_sha256=digest(source),
            outer_sha256=digest(whole), generation_id=kwargs["generation"],
            pid=os.getpid(), closed=False)
    handle._record()
    return source, handle
