from copy import deepcopy
import os

import pytest

from app.services import canonical_native_source_owner as original
from app.services.confirmed_sector_taxonomy import PROVIDERS
from app.services.daily_sector_observations import sector_observations
from app.services.model_execution_plan import CohortSubject, FrozenCohort
from app.services.scoped_monitoring_research import ScopedPreparedResearchOwner, _acceptance
from app.services.unified_snapshot_contract import digest


@pytest.mark.parametrize('observed,session,provider,day,reason', [
    ('2026-11-12T00:00:00+00:00', 'us_regular', PROVIDERS['us'], '2026-11-12', None),
    ('2026-11-12T21:00:00+00:00', 'us_regular', PROVIDERS['us'], '2026-11-12', None),
    ('2026-11-12T00:00:00+00:00', 'us_pre', PROVIDERS['us'], '2026-11-12', 'OBSERVATION_SESSION_MISMATCH'),
    ('2026-11-12T00:00:01+00:00', 'us_regular', PROVIDERS['us'], '2026-11-12', 'OBSERVATION_SESSION_MISMATCH'),
    ('2026-11-12T00:00:00+00:00', 'us_regular', 'other', '2026-11-12', 'OBSERVATION_SESSION_MISMATCH'),
    ('2026-11-11T00:00:00+00:00', 'us_regular', PROVIDERS['us'], '2026-11-12', 'OBSERVATION_SESSION_MISMATCH'),
])
def test_sector_bar_label_not_a_general_midnight_exception(observed, session, provider, day, reason):
    fact = dict(fact_id='sector', fact_type='market_sector', source=provider, as_of_date=day,
        fields=dict(observed_at=observed, market_session=session, series_code='XLE', return_pct=1.83))
    registry = {('sector', 'fields.return_pct'): dict(value=1.83, unit='pct')}
    retained = deepcopy(fact)
    rows, audit = sector_observations([fact], registry, market='us', completed=day)
    assert bool(rows) is (reason is None)
    if reason:
        assert audit[0]['reason'] == reason
    else:
        assert audit[0]['category'] == 'US_BROAD_SECTOR'
    assert audit[0]['directional_authority_added'] is False
    assert fact == retained


def test_cohort_single_validation_keeps_original_checks_and_detached_data(monkeypatch):
    cutoff = '2026-11-13T06:24:18+00:00'
    tickers = ('AAA', 'BBB')
    source = dict(source_generation_id='source', stocks={t:dict(market='us',
        packet=dict(generated_at=cutoff, canonical_security_id='US:'+t)) for t in tickers},
        prepared={t:dict(source_authority=dict(example=t)) for t in tickers})
    row = dict(source=source, source_sha256=digest(source), pid=os.getpid(), closed=False,
        market='us', subjects=tickers, generation_id='cycle', outer_sha256=digest('outer'),
        registration_sha256=digest('registration'), registration_capture_receipt_sha256=digest('capture'),
        request_plan_sha256=digest('plan'), accepted_at=cutoff, registration_cutoff=cutoff)
    row['acceptance'] = _acceptance(row)
    row['acceptance_sha256'] = digest(row['acceptance'])
    handle = object.__new__(ScopedPreparedResearchOwner)
    monkeypatch.setitem(original._OWNERS, handle, row)
    calls = []
    monkeypatch.setattr(original, 'verified_owned_packet_view', lambda stock: calls.append(stock))
    relation = handle.relationship('us')
    cohort = FrozenCohort('cycle', 'source', '2026-11-13', cutoff, cutoff,
        tuple(CohortSubject('us', t, 'US:'+t, cutoff, relation['subject_sha256'][t]) for t in tickers),
        (('us',digest(relation)),), digest('feature'), planning_only=False)
    relation_bulk, bulk = handle.resolve_cohort('us')
    assert relation_bulk == relation and bulk == {t:handle.resolve_subject(t) for t in tickers}
    bulk['AAA']['stock']['packet']['canonical_security_id'] = 'changed in detached copy'
    calls.clear()
    cohort.verify_source_owner(handle)
    assert len(calls) == len(tickers)
    source['stocks']['AAA']['packet']['canonical_security_id'] = 'drift'
    with pytest.raises(ValueError, match='source_content_drift'):
        cohort.verify_source_owner(handle)
    handle.close()
    with pytest.raises(ValueError, match='live_source_owner_required'):
        cohort.verify_source_owner(handle)
