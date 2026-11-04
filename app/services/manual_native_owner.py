"""Separate manual Native input authority, never an accepted economic receipt.

The live source session, original Market acceptance and complete per-security
admissions are all necessary. A manifest is an audit view, not an issuing API.
"""
from copy import deepcopy
from threading import RLock
from weakref import WeakKeyDictionary

from app.services.prospective_class_c_owner import SCOPE
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE

CONTRACT = "backend-manual-native-input-parent-v1"
_MARKET = WeakKeyDictionary()
_PARENTS = WeakKeyDictionary()
_LOCK = RLock()


def _require(condition, reason):
    if not condition:
        raise ValueError("manual_native_" + reason)


def record_original_market_acceptance(session, request, output):
    """Internal original consumer hook, called only after semantic acceptance."""
    _require(("MARKET", request["batch"]) in session._accepted_batches
        and request in session.captured.get("MARKET", ())
        and digest(session.markets.get(session.market)) == digest(output),
        "original_market_acceptance_required")
    with _LOCK:
        _MARKET[session] = dict(market=session.market, generation_id=session.gen,
            source_generation_id=session.source_gen, source_sha256=digest(session.source),
            batch=request["batch"], request_sha256=digest(request), output_sha256=digest(output))


def original_market_acceptance(session):
    with _LOCK:
        receipt = _MARKET.get(session)
        _require(receipt is not None, "original_market_acceptance_required")
        requests = [r for r in session.captured.get("MARKET", ()) if r.get("batch") == receipt["batch"]]
        _require(len(requests) == 1 and digest(requests[0]) == receipt["request_sha256"]
            and ("MARKET", receipt["batch"]) in session._accepted_batches
            and (session.market, session.gen, session.source_gen) == (
                receipt["market"], receipt["generation_id"], receipt["source_generation_id"])
            and digest(session.source) == receipt["source_sha256"]
            and digest(session.markets.get(session.market)) == receipt["output_sha256"],
            "original_market_acceptance_drift")
        return deepcopy(receipt)


class BackendManualNativeParent:
    def __init__(self):
        raise ValueError("manual_native_backend_issuance_required")

    def _record(self):
        with _LOCK:
            row = _PARENTS.get(self)
            _require(row is not None and not row["closed"], "live_parent_required")
            session = row["source_session"]
            session._guard(verify_sessions=False)
            _require(session._source_owner is row["source_owner"], "source_capability_changed")
            _require(session._state == "PREPARED", "source_not_prepared")
            _require(digest(row["source_owner"].relationship(row["scope"]["market"]))
                == row["relationship_sha256"], "source_relationship_drift")
            for market, receipt in row["market_acceptance"].items():
                stage = session._sessions[market]
                _require(original_market_acceptance(stage) == receipt,
                    "original_market_acceptance_drift")
            for admission in row["admissions"].values():
                admission.verify()
            return row

    @property
    def scope(self):
        return deepcopy(self._record()["scope"])

    @property
    def manifest(self):
        row = self._record()
        return deepcopy(row["manifest"])

    def verify_scope(self, **scope):
        _require(scope == self._record()["scope"], "parent_session_scope_mismatch")

    def verify_consumed_source(self, source):
        row = self._record()
        _require(digest(source) == row["relationship"]["inner_consumed_source_sha256"],
            "consumed_source_relationship_mismatch")

    def request(self, ticker):
        row = self._record()
        _require(ticker in row["admissions"], "request_membership_denied")
        admission = row["admissions"][ticker]
        admission.verify()
        return admission.reference_request.model_copy(deep=True)

    def close(self):
        with _LOCK:
            row = _PARENTS.get(self)
            _require(row is not None, "live_parent_required")
            row["closed"] = True


def issue_manual_native_parents(source_session, admissions):
    """Only a successfully prepared full source session can promote its inputs."""
    from app.services.manual_shadow_source_session import ManualShadowSourceSession
    from app.services.canonical_native_source_owner import CanonicalPreparedSourceOwner
    from app.services.canonical_native_admission import CanonicalNativeAdmission

    _require(type(source_session) is ManualShadowSourceSession, "source_session_required")
    source_session._guard()
    owner = source_session._source_owner
    _require(type(owner) is CanonicalPreparedSourceOwner, "source_capability_required")
    _require(source_session._state == "PREPARED" and source_session._stage_index == 1,
        "accepted_market_before_native_required")
    subjects = {t for ts in UNIVERSE.values() for t in ts}
    _require(set(admissions) == subjects and all(type(a) is CanonicalNativeAdmission
        for a in admissions.values()), "nonempty_exact_cohort_admissions_required")
    receipts = {}
    for market in UNIVERSE:
        stage = source_session._sessions[market]
        receipt = original_market_acceptance(stage)
        _require(receipt["generation_id"] == source_session._generation
            and receipt["source_sha256"] == digest(owner.source(market)),
            "original_market_acceptance_required")
        receipts[market] = deepcopy(receipt)
    for ticker, admission in admissions.items():
        admission.verify()
        _require(admission.source_owner is owner and admission.ticker == ticker,
            "admission_source_membership_mismatch")
    result = {}
    with _LOCK:
        for market, tickers in UNIVERSE.items():
            relationship = owner.relationship(market)
            scope = dict(run_id=source_session._generation, market=market,
                generation_id=source_session._generation,
                source_generation_id=relationship["source_generation_id"],
                snapshot_sha256=relationship["outer_source_envelope_sha256"])
            bindings = {t: dict(
                request_sha256=admissions[t].reference_request.authorization.request_sha256,
                admission_bundle_sha256=digest(admissions[t].registry.bundle.model_dump(mode="json")))
                for t in tickers}
            manifest = dict(contract=CONTRACT, execution_purpose=SCOPE,
                authority_scope="SOURCE_USE_NOT_MODEL_DISPATCH", scope=scope,
                relationship=relationship, market_acceptance=receipts,
                per_security=bindings, source_generation_preserved=True,
                class_c_pins=deepcopy(source_session._frozen["protected_input_hashes"]),
                source_input_sha256=source_session._input_hash,
                code_sha256=digest(source_session._code))
            parent = object.__new__(BackendManualNativeParent)
            _PARENTS[parent] = dict(source_session=source_session, source_owner=owner,
                scope=scope, relationship=relationship, relationship_sha256=digest(relationship),
                market_acceptance=receipts, manifest=manifest,
                admissions={t: admissions[t] for t in tickers}, closed=False)
            result[market] = parent
    for parent in result.values():
        parent._record()
    return result
