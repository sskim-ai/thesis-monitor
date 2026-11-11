"""Pure cohort/topology compilation. Hashes bind plans; they grant no source rights."""
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import json
import re

from app.services.unified_snapshot_contract import digest, encoded
from app.services.vnext_execution_profile import SOL_HIGH_V1

CONTRACT = 'dynamic-cohort-model-execution-plan-v1'


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('model_plan_sha_required')
    return value


def _instant(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('model_cohort_aware_time_required')
    return result.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class CohortSubject:
    market: str
    ticker: str
    security_id: str
    available_at: str
    owner_subject_sha256: str


@dataclass(frozen=True)
class FrozenCohort:
    run_id: str
    source_generation: str
    assessment_date: str
    effective_at: str
    cutoff: str
    subjects: tuple[CohortSubject, ...]
    source_owner_bindings: tuple[tuple[str, str], ...]
    feature_scope_sha256: str
    planning_only: bool = True

    def __post_init__(self):
        if not self.run_id or not self.source_generation or type(self.planning_only) is not bool:
            raise ValueError('model_cohort_identity_required')
        date.fromisoformat(self.assessment_date)
        object.__setattr__(self, 'effective_at', _instant(self.effective_at))
        object.__setattr__(self, 'cutoff', _instant(self.cutoff))
        if self.effective_at > self.cutoff:
            raise ValueError('model_cohort_effective_after_cutoff')
        if self.assessment_date > self.cutoff[:10]:
            raise ValueError('model_cohort_future_assessment')
        rows = []
        for row in self.subjects:
            if type(row) is not CohortSubject or row.market not in ('us', 'kr') or not row.ticker or not row.security_id:
                raise ValueError('model_cohort_subject_identity')
            available = _instant(row.available_at)
            if available > self.cutoff:
                raise ValueError('model_cohort_future_availability')
            _sha(row.owner_subject_sha256)
            rows.append(CohortSubject(row.market, row.ticker, row.security_id, available, row.owner_subject_sha256))
        if (len({(r.market, r.ticker) for r in rows}) != len(rows)
                or len({r.security_id for r in rows}) != len(rows)):
            raise ValueError('model_cohort_duplicate_security')
        object.__setattr__(self, 'subjects', tuple(sorted(rows, key=lambda r: (r.market, r.ticker, r.security_id))))
        bindings = tuple(sorted(self.source_owner_bindings))
        if len(dict(bindings)) != len(bindings) or set(dict(bindings)) != {r.market for r in rows}:
            raise ValueError('model_cohort_owner_market_coverage')
        for _, pin in bindings:
            _sha(pin)
        object.__setattr__(self, 'source_owner_bindings', bindings)
        _sha(self.feature_scope_sha256)

    def to_dict(self):
        return json.loads(encoded(asdict(self)))

    @property
    def sha256(self):
        return digest(self.to_dict())

    @property
    def market_subjects(self):
        return {m: tuple(r.ticker for r in self.subjects if r.market == m)
                for m in ('us', 'kr') if any(r.market == m for r in self.subjects)}

    def verify_source_owner(self, owner):
        """Only the existing original live owner can admit a runtime cohort."""
        from app.services.canonical_native_source_owner import CanonicalPreparedSourceOwner
        if self.planning_only or type(owner) is not CanonicalPreparedSourceOwner:
            raise ValueError('TYPED_GAP_REGISTERED_COHORT_SOURCE_OWNER_REQUIRED')
        for market, subjects in self.market_subjects.items():
            relation = owner.relationship(market)
            if (digest(relation) != dict(self.source_owner_bindings)[market]
                    or relation['generation_id'] != self.run_id
                    or relation['source_generation_id'] != self.source_generation
                    or set(relation['subjects']) != set(subjects)):
                raise ValueError('model_cohort_original_owner_scope_drift')
            for row in (r for r in self.subjects if r.market == market):
                original = owner.resolve_subject(row.ticker)
                # Canonical identities must come from the verified source, not UI tickers.
                def identities(value):
                    if isinstance(value, dict):
                        for key, cell in value.items():
                            if key == 'canonical_security_id' and isinstance(cell, str):
                                yield cell
                            else:
                                yield from identities(cell)
                    elif isinstance(value, (tuple, list)):
                        for cell in value:
                            yield from identities(cell)
                if (set(identities(original)) != {row.security_id}
                        or relation['subject_sha256'][row.ticker] != row.owner_subject_sha256
                        or _instant(original['cutoff']) != self.cutoff
                        or row.available_at != _instant(original['cutoff'])):
                    raise ValueError('TYPED_GAP_REGISTERED_CANONICAL_ID_OR_SOURCE_TIME')


@dataclass(frozen=True)
class PlannedModelSlot:
    slot_id: str
    market: str
    stage: str
    batch_id: int | None
    subjects: tuple[str, ...]
    security_ids: tuple[str, ...]
    source_generation: str
    cohort_sha256: str
    execution_profile: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class ModelExecutionPlan:
    cohort: FrozenCohort
    topology: str
    slots: tuple[PlannedModelSlot, ...]
    execution_profile: str = SOL_HIGH_V1.contract

    def to_dict(self):
        return dict(contract=CONTRACT, cohort=self.cohort.to_dict(), topology=self.topology,
                    execution_profile=self.execution_profile, slots=json.loads(encoded([asdict(s) for s in self.slots])))

    @property
    def sha256(self):
        return digest(self.to_dict())

    def validate(self):
        expected = compile_model_plan(self.cohort, topology=self.topology)
        if expected.to_dict() != self.to_dict():
            raise ValueError('model_stage_plan_drift_or_missing_slot')

    def slot(self, slot_id):
        rows = [s for s in self.slots if s.slot_id == slot_id]
        if len(rows) != 1:
            raise ValueError('model_plan_slot_unknown_or_duplicate')
        return rows[0]

    @classmethod
    def from_dict(cls, value):
        raw = dict(value['cohort'])
        raw['subjects'] = tuple(CohortSubject(**s) for s in raw['subjects'])
        raw['source_owner_bindings'] = tuple(tuple(b) for b in raw['source_owner_bindings'])
        result = compile_model_plan(FrozenCohort(**raw), topology=value['topology'])
        if result.to_dict() != value:
            raise ValueError('model_stage_plan_drift_or_missing_slot')
        return result


def compile_model_plan(cohort, *, topology):
    if type(cohort) is not FrozenCohort or topology not in ('CANONICAL_PRODUCTION', 'SPLIT_RESEARCH'):
        raise ValueError('explicit_frozen_cohort_and_topology_required')
    from app.services.canonical_monitoring_helpers import _batch_topology
    slots = []
    def add(market, stage, batch, subjects, dependencies):
        securities = tuple(next(r.security_id for r in cohort.subjects if (r.market, r.ticker) == (market, t)) for t in subjects)
        row = dict(market=market, stage=stage, batch_id=batch, subjects=tuple(subjects), security_ids=securities,
                   source_generation=cohort.source_generation, cohort_sha256=cohort.sha256,
                   execution_profile=SOL_HIGH_V1.contract, dependencies=tuple(dependencies))
        slot = PlannedModelSlot(slot_id=digest(row), **row)
        slots.append(slot)
        return slot.slot_id
    batches = _batch_topology(cohort=cohort)
    for market, subjects in cohort.market_subjects.items():
        market_id = add(market, 'MARKET', None, (), ())
        if topology == 'SPLIT_RESEARCH':
            for ticker in subjects:
                blind = add(market, 'BLIND', None, (ticker,), (market_id,))
                add(market, 'ADJUDICATION', None, (ticker,), (blind,))
        else:
            previous = (market_id,)
            for stage in ('CORE', 'A', 'B'):
                previous = tuple(add(market, stage, row['batch'], row['subjects'], previous)
                    for row in batches if row['market'] == market)
            for ticker in subjects:
                add(market, 'B2', None, (ticker,), previous)
    result = ModelExecutionPlan(cohort, topology, tuple(slots))
    if topology == 'CANONICAL_PRODUCTION' and len(slots) != len(cohort.market_subjects) + 3*len(batches) + len(cohort.subjects):
        raise ValueError('model_plan_formula_registry_mismatch')
    return result


def validate_slot_scope(plan, scope):
    plan.validate()
    slot = plan.slot(scope['slot_id'])
    expected = dict(plan_sha256=plan.sha256, cohort_sha256=plan.cohort.sha256,
        slot_id=slot.slot_id, market=slot.market, stage=slot.stage, batch_id=slot.batch_id,
        subjects=list(slot.subjects), security_ids=list(slot.security_ids),
        source_generation=slot.source_generation, execution_profile=slot.execution_profile,
        payload_sha256=_sha(scope['payload_sha256']), build_receipt_sha256=_sha(scope['build_receipt_sha256']),
        dependency_outputs=scope['dependency_outputs'])
    if (scope != expected or not isinstance(scope['dependency_outputs'], dict)
            or set(scope['dependency_outputs']) != set(slot.dependencies)):
        raise ValueError('model_worker_slot_scope_drift')
    for value in scope['dependency_outputs'].values():
        _sha(value)
