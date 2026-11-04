"""Default-off, same-parent source replay and native validation; no dispatch.

Pins describe bytes, not authority. Only live prospective capabilities and the
original source/Market/native owners can admit a session. B2 is not enabled.
"""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
from threading import Lock
from weakref import WeakKeyDictionary

from app.services.canonical_monitoring_source import prepare_monitoring_source
from app.services.canonical_source_replay import stock_inputs
from app.services.production_monitoring_session import ProductionMonitoringSession, STAGE_NAMES
from app.services.prospective_class_c_owner import ProspectiveOwner, SCOPE, require_generation
from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_full_source_cohort import FreshFullSourceRunSeed
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.whole_source_code_owner_registry import (
    WholeSourceCodeOwnerRegistry, verify_fresh_code_identity,
)
from scripts.r2b_r5_market_adapter import project_sealed_market_context
from scripts.r9_rev11_market_qualification import qualify_markets
from scripts.r9_rev11_replay import replay_twice

CONTRACT = "manual-shadow-source-session-v1"
_PID = os.getpid()
_REPO = Path(__file__).resolve().parents[2]
_CLAIMED = WeakKeyDictionary()
_CLAIM_LOCK = Lock()
_SESSION_CODE_PATHS = (
    "app/services/manual_shadow_source_session.py",
    "app/services/canonical_native_source_owner.py",
    "app/services/canonical_native_admission.py",
    "app/services/manual_native_owner.py",
    "app/services/canonical_monitoring_source.py",
    "app/services/canonical_source_replay.py",
    "app/services/production_monitoring_session.py",
    "app/services/prospective_class_c_owner.py",
    "app/services/reported_business_projection.py",
    "app/services/cross_market_decision_engine_service.py",
    "app/services/direction_timing_ownership_service.py",
    "app/services/fundamental_input_policy.py",
    "app/services/unified_full_source_cohort.py",
    "app/services/unified_snapshot_contract.py",
    "app/services/unified_source_policy.py",
    "app/services/unified_stock_acquisition.py",
    "app/services/whole_source_code_owner_registry.py",
    "scripts/r2b_r5_market_adapter.py",
    "scripts/r9_rev11_replay.py",
    "scripts/m12ds_r2_judgment_policy.py",
    "scripts/m12ds_r2_schemas.py",
    "docs/operations/UNIFIED_ACQUISITION_CLASSES.json",
)


def _require(condition, reason):
    if not condition:
        raise ValueError("manual_shadow_" + reason)


def _plain_path(path):
    path = Path(path).absolute()
    _require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink_denied")
    _require(path == path.resolve(), "noncanonical_path")
    return path


def code_fingerprints():
    """Finite original owner registry and explicit session contract, including WIP.

    This checks code identity, not real-source or current private-read authority.
    Importing this default-off adapter performs no source inventory reads.
    """
    result = {}
    for profile in ("fresh", "fresh_kr8", "fresh_us14"):
        result.update(WholeSourceCodeOwnerRegistry.freeze(_REPO, profile=profile).fingerprints)
    for name in _SESSION_CODE_PATHS:
        path = _plain_path(_REPO / name)
        result[name] = sha256(path.read_bytes()).hexdigest()
    return result


def _source_integrity(root, pins):
    _require(isinstance(pins, dict) and pins, "source_inventory_required")
    directories = {"": set()}
    for name in pins:
        relative = PurePosixPath(name)
        _require(not relative.is_absolute() and ".." not in relative.parts
                 and relative.as_posix() == name, "source_path_invalid")
        _require(relative.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}
                 and not any(part.startswith(".env") for part in relative.parts),
                 "database_or_environment_source_denied")
        for index, part in enumerate(relative.parts):
            parent = "/".join(relative.parts[:index])
            directories.setdefault(parent, set()).add(part)
    _plain_path(root)
    _require(root.is_dir() and pins, "source_inventory_required")
    # Reject unexpected names without inspecting their metadata or contents.
    for name, expected_names in sorted(directories.items()):
        directory = _plain_path(root / name)
        _require(directory.is_dir(), "nonregular_source_denied")
        _require(set(os.listdir(directory)) == expected_names, "source_inventory_drift")
    for name, expected in pins.items():
        path = _plain_path(root / name)
        _require(path.is_file() and path.stat().st_nlink == 1, "nonregular_source_denied")
        _require(sha256(path.read_bytes()).hexdigest() == expected, "source_bytes_drift")


def _business_stock_inputs(root, frozen, policy, outcome, **owners):
    inputs, errors = stock_inputs(root, frozen, policy, outcome, **owners)
    for item in inputs.values():
        item["reported_comparison_business"] = True
    # The original aggregate reader otherwise materializes missing files.
    for market in UNIVERSE:
        for name in ("aggregate.json", "aggregate-value.json"):
            _require((root / "markets" / market / name).is_file(),
                     "presealed_market_materialization_required")
    return inputs, errors


class ManualShadowSourceSession:
    """One full-cohort run; caller retains responsibility for later dispatch review.

    source_file_sha256 must pin the complete, already-captured source directory.
    output_root must be a new, disjoint task directory. Neither path is a DB.
    No handle is serialized, deep-copied, reconstructed or issued here.
    """

    def __init__(self, root, *, output_root, frozen, outcome, policy,
                 prospective_owners, source_file_sha256, expected_code_fingerprints,
                 enabled=False, native_admission_enabled=False):
        _require(type(enabled) is bool and enabled, "disabled")
        _require(type(native_admission_enabled) is bool, "explicit_native_admission_gate_required")
        self._native_admission_enabled = native_admission_enabled
        self._source_owner = None
        self._native_parents = {}
        _require(os.getpid() == _PID, "parent_pid_changed")
        _require(type(policy) is UnifiedSourcePolicy, "source_policy_required")
        _require(set(prospective_owners) == set(UNIVERSE)
                 and all(type(o) is ProspectiveOwner for o in prospective_owners.values()),
                 "exact_live_market_owners_required")
        _require(frozen.get("execution_purpose") == SCOPE
                 and frozen.get("generation_id") and not frozen.get("scope"), "full_manual_scope_required")
        for owner in prospective_owners.values():
            require_generation(owner, frozen["generation_id"], purpose=SCOPE)
        self._pid = os.getpid()
        self._generation = frozen["generation_id"]
        self._owners = dict(prospective_owners)
        self._owner_identity = tuple((m, o) for m, o in sorted(self._owners.items()))
        self._root, self._output = _plain_path(root), _plain_path(output_root)
        _require(not self._output.exists() and not self._output.is_relative_to(self._root)
                 and not self._root.is_relative_to(self._output), "new_disjoint_output_required")
        self._frozen, self._outcome = deepcopy(frozen), deepcopy(outcome)
        self._policy = policy
        self._source_pins = deepcopy(source_file_sha256)
        self._code = deepcopy(expected_code_fingerprints)
        self._initial_code = code_fingerprints()
        for market in UNIVERSE:
            name = "class-c/local-" + market + ".json"
            _require(self._source_pins.get(name)
                     and self._frozen.get("protected_input_hashes", {}).get(name) == self._source_pins[name],
                     "class_c_independent_pin_required")
        self._input_hash = self._input_digest()
        self._state = "NEW"
        self._sessions = {}
        self._session_hashes = {}
        self._requests = {}
        self._accepted = set()
        self._stage_index = 0
        self._guard()

    def _input_digest(self):
        return digest(dict(root=str(self._root), output=str(self._output), generation=self._generation,
            frozen=self._frozen, outcome=self._outcome, providers=sorted(self._policy.allowed_providers),
            source_pins=self._source_pins, code=self._code,
            native_admission_enabled=self._native_admission_enabled))

    def _guard(self, *, verify_sessions=True):
        _require(os.getpid() == self._pid == _PID, "parent_pid_changed")
        _require(self._state not in {"BLOCKED", "CLOSED"}, "session_terminal")
        _require(tuple(sorted(self._owners.items())) == self._owner_identity, "owner_handle_changed")
        for owner in self._owners.values():
            require_generation(owner, self._generation, purpose=SCOPE)
        _require(self._input_digest() == self._input_hash, "frozen_input_drift")
        _require(self._code == self._initial_code == code_fingerprints(), "code_policy_schema_drift")
        _source_integrity(self._root, self._source_pins)
        _plain_path(self._output)
        if verify_sessions:
            for market, session in self._sessions.items():
                _require(self._session_digest(session) == self._session_hashes[market], "native_state_drift")

    @staticmethod
    def _session_digest(session):
        fields = ("source", "prepared", "fresh_stocks", "projected", "cores", "arows", "brows",
                  "markets", "chains", "catalogs", "subjects", "caps", "ranges", "entries", "actx",
                  "bctx", "limits", "stage_manifests", "captured", "gen", "source_gen", "market")
        return digest(dict(values={key: getattr(session, key) for key in fields},
            root=str(session.root), accepted=sorted(session._accepted_batches),
            manual_source_owner=id(session._manual_source_owner),
            native_owner_parent=id(session._native_owner_parent),
            native_parent_scope=session._native_parent_scope,
            native_source_content_sha256=session._native_source_content_sha256))

    def prepare(self):
        self._guard()
        _require(not self._output.exists(), "new_disjoint_output_required")
        with _CLAIM_LOCK:
            _require(self._state == "NEW", "prepare_once_only")
            for owner in self._owners.values():
                _require(self._generation not in _CLAIMED.get(owner, set()), "owner_run_already_claimed")
            for owner in self._owners.values():
                _CLAIMED.setdefault(owner, set()).add(self._generation)
            self._state = "PREPARING"
        try:
            args, whole, replay = replay_twice(self._root, self._frozen, self._outcome, self._policy,
                prospective_owners=self._owners, stock_reader=_business_stock_inputs)
            _require(type(args["seed"]) is FreshFullSourceRunSeed
                     and args["seed"].parent_run_id == self._generation
                     and args["seed"].proof_mode == "AD_HOC_LIVE_SOURCE_PROOF", "fresh_seed_required")
            _require(replay["replay_equal"] is True and replay["first_sha256"] == replay["second_sha256"]
                     == digest(whole), "original_two_pass_identity_required")
            registry = verify_fresh_code_identity(_REPO, metadata=args["composition_metadata"],
                code_sha256=args["seed"].code_config_sha256,
                authority_sha256=args["seed"].source_authority_contract_sha256)
            identity = replay["code_owner_registry_identity"]
            _require(identity["status"] == "PASS" and identity["per_file_sha256"] == registry.fingerprints
                     and all(identity[k] == registry.sha256 for k in (
                         "aggregate_registry_sha256", "seed_registry_sha256", "producer_registry_sha256",
                         "consumer_registry_sha256", "replay1_registry_sha256", "replay2_registry_sha256")),
                     "original_registry_identity_required")
            _require(set(whole["packets"]) == set(UNIVERSE)
                     and all(set(whole["packets"][m]["stocks"]) == set(ts) for m, ts in UNIVERSE.items()),
                     "exact_full_cohort_required")
            markets = qualify_markets(whole)
            _require(set(markets) == set(UNIVERSE) and all(
                r["status"] == r["view_replay"]["status"] == "PASS" for r in markets.values()),
                "original_market_qualification_required")
            local_seeds = {t: i["fresh_financial_binding"]["technical_inputs"]["local_seed"]
                           for t, i in args["stock_inputs"].items()}
            valuation = {t: calibration_context(s["valuation_view"]) for packet in whole["packets"].values()
                         for t, s in packet["stocks"].items()}
            _require(digest(valuation) == replay["valuation_b_context_sha256"], "valuation_replay_drift")
            self._guard()
            source_args = dict(whole=whole, local_seeds=local_seeds,
                valuation_contexts=valuation, generation=self._generation, coverage=None, census=None,
                market_projector=project_sealed_market_context)
            if self._native_admission_enabled:
                from app.services.canonical_native_source_owner import prepare_owned_monitoring_source
                source, self._source_owner = prepare_owned_monitoring_source(enabled=True, **source_args)
            else:
                source = prepare_monitoring_source(**source_args)
            expected = {t for ts in UNIVERSE.values() for t in ts}
            _require(set(source["prepared"]) == set(source["stocks"]) == expected
                     and all(r["mode"] == "EVIDENCE_BASED" for r in source["prepared"].values()),
                     "strict_evidence_based_cohort_required")
            self._guard()
            _require(not self._output.exists(), "new_disjoint_output_required")
            sessions = {}
            for market, subjects in UNIVERSE.items():
                scoped = {**source, "markets": {market: source["markets"][market]}}
                for key in ("prepared", "stocks", "valuation_contexts"):
                    scoped[key] = {t: source[key][t] for t in subjects}
                sessions[market] = ProductionMonitoringSession(self._output / market, market=market,
                    generation_id=self._generation, source_generation_id=self._generation, source=scoped,
                    manual_native_v1=self._native_admission_enabled, manual_source_owner=self._source_owner)
            self._sessions = sessions
            self._session_hashes = {m: self._session_digest(s) for m, s in sessions.items()}
            self._guard()
            self._state = "PREPARED"
            return dict(contract=CONTRACT, status="SOURCE_PREPARED_NOT_LAUNCH_AUTHORIZED",
                generation_id=self._generation, replay=deepcopy(replay),
                market_qualification_sha256=digest(markets), source_sha256=digest(source),
                code_sha256=digest(self._code), b2="BLOCKED_NO_COVERAGE_CENSUS_OWNERS",
                provider_calls=0, model_calls=0)
        except Exception:
            self._state = "BLOCKED"
            raise

    def admit_native(self):
        """Admit existing Core-visible inputs, not economic roles or dispatch."""
        self._guard()
        _require(self._native_admission_enabled and self._source_owner is not None,
                 "native_admission_feature_disabled")
        _require(self._state == "PREPARED" and self._stage_index == 1,
                 "accepted_market_before_native_required")
        _require(not self._native_parents, "native_parent_already_issued")
        from app.services.canonical_native_admission import CanonicalToNativeAdmissionProducer, CanonicalNativeGap
        from app.services.manual_native_owner import issue_manual_native_parents
        producer = CanonicalToNativeAdmissionProducer(self._source_owner)
        admissions, gaps = {}, {}
        for tickers in UNIVERSE.values():
            for ticker in tickers:
                result = producer.produce_source_inputs(ticker,
                    request_id=self._generation + ":core:" + ticker)
                if isinstance(result, CanonicalNativeGap):
                    gaps[ticker] = result.model_dump(mode="json")
                else:
                    admissions[ticker] = result
        if gaps:
            return dict(status="NATIVE_ADMISSION_GAP", gaps=gaps,
                        admitted_subjects=sorted(admissions), parent_issued=False)
        parents = issue_manual_native_parents(self, admissions)
        try:
            for market, parent in parents.items():
                self._sessions[market].attach_manual_native_parent(parent)
        except Exception:
            for parent in parents.values():
                parent.close()
            self._state = "BLOCKED"
            raise
        self._native_parents = parents
        self._session_hashes = {m: self._session_digest(s) for m, s in self._sessions.items()}
        self._guard()
        return dict(status="NATIVE_INPUT_ADMITTED_NOT_MODEL_DISPATCH_AUTHORIZED",
                    manifests={m: p.manifest for m, p in parents.items()})

    def _stage_guard(self, stage, market):
        self._guard()
        _require(self._state == "PREPARED", "source_not_prepared")
        _require(market in self._sessions and self._stage_index < len(STAGE_NAMES)
                 and stage == tuple(STAGE_NAMES)[self._stage_index], "global_model_stage_order")

    def build(self, stage, market):
        self._stage_guard(stage, market)
        _require((stage, market) not in self._requests, "stage_already_built")
        session = self._sessions[market]
        try:
            requests = session.build(stage)
            if stage in {"MARKET", "CORE"}:
                session.freeze_stage(STAGE_NAMES[stage], requests)
            self._requests[stage, market] = deepcopy(requests)
            self._session_hashes[market] = self._session_digest(session)
            self._guard()
            return deepcopy(requests)
        except Exception:
            self._state = "BLOCKED"
            raise

    def accept(self, stage, market, request, output):
        self._stage_guard(stage, market)
        _require(request in self._requests.get((stage, market), ()), "request_not_built")
        key = (stage, market, request["batch"])
        _require(key not in self._accepted, "response_already_accepted")
        session = self._sessions[market]
        try:
            session.accept(stage, deepcopy(request), deepcopy(output))
            self._session_hashes[market] = self._session_digest(session)
            self._guard()
            self._accepted.add(key)
            if all((stage, m) in self._requests and all(
                (stage, m, r["batch"]) in self._accepted for r in self._requests[stage, m]) for m in UNIVERSE):
                self._stage_index += 1
            return dict(contract=CONTRACT, stage=stage, market=market, batch=request["batch"],
                        status="ACCEPTED_UNSENT", output_sha256=digest(output))
        except Exception:
            self._state = "BLOCKED"
            raise

    def b2_request(self, ticker):
        self._guard()
        raise ValueError("manual_shadow_b2_coverage_census_owners_required")

    def close(self):
        for parent in self._native_parents.values():
            parent.close()
        if self._source_owner is not None:
            self._source_owner.close()
        self._state = "CLOSED"
        self._sessions.clear()
        self._owners.clear()
