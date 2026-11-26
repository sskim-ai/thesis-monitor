from datetime import date, datetime
from types import SimpleNamespace
import asyncio

import pytest

from app.jobs.unified_market_snapshot import LocalUsOneShot, latest_one_shot_us_session, run_registered
from app.services.unified_market_run import prepared_session_for_day


def test_closed_regular_day_does_not_drop_configured_completed_session():
    cutoff = datetime.fromisoformat('2026-11-27T00:10:00+09:00')
    target = date(2026, 11, 25)
    slot = LocalUsOneShot(tag='us-20261127-12345678', scheduled_at=cutoff, target_session=target)
    cfg = SimpleNamespace(market='us', one_shot=slot)
    assert latest_one_shot_us_session(cutoff, one_shot_tag=slot.tag, config=cfg) == target
    assert prepared_session_for_day('us', cutoff.date(), cutoff=cutoff) is None
    assert prepared_session_for_day('us', cutoff.date(), cutoff=cutoff, configured_us_session=target) == target
    for market, day, proposed in (('us',cutoff.date(),date(2026,11,26)), ('us',date(2026,11,26),target),
                                  ('kr',cutoff.date(),target)):
        with pytest.raises(ValueError):
            prepared_session_for_day(market, day, cutoff=cutoff, configured_us_session=proposed)


def test_wrong_frozen_generation_rejected_before_source(monkeypatch):
    import app.services.production_source_backend as backend
    def forbidden(*args, **kwargs):
        pytest.fail('no Source acquisition permitted')
    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', forbidden)
    cutoff = datetime.fromisoformat('2026-11-27T00:10:00+09:00')
    slot = LocalUsOneShot(tag='us-20261127-12345678', scheduled_at=cutoff, target_session=date(2026,11,25))
    ledger = SimpleNamespace(identity={'master_id':'other'})
    source = dict(frozen=dict(frozen_at=cutoff.isoformat(), selected_market='us',master_id='other'),run_ledger=ledger)
    with pytest.raises(ValueError,match='configured_us_one_shot_frozen_source_mismatch'):
        asyncio.run(run_registered(None, source=source, model=dict(run_ledger=ledger),
                                  mode='LIVE_NO_SEND', configured_us_one_shot=slot))
