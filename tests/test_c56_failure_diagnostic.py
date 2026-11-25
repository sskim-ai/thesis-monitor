"""Source-field diagnostics retain the existing no-send and first-write behavior."""

import asyncio
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.fresh_financial_stock_owner import BusinessMandatorySourceIncomplete
from tests.test_local_failure_diagnostic import execute, offline_diagnostic_only  # noqa: F401


def failure(market='us', ticker='MU'):
    return BusinessMandatorySourceIncomplete(market=market, ticker=ticker,
        mandatory_missing=['numeric_registry:unregistered_fields'] * 2,
        unregistered_fields=[dict(fact_id='chart:2026-11-25',
            field_path='fields.support_invalidation.latest_daily_close',
            value=123.5, provider_payload='SYNTHETIC_PRIVATE_DO_NOT_EXPORT')])


@pytest.mark.parametrize('market,ticker', [('kr', '005930'), ('us', 'MU')])
def test_source_identifiers_and_missing_paths_are_sealed_before_cleanup(tmp_path, market, ticker):
    error = failure(market, ticker)
    assert isinstance(error, ValueError)
    assert str(error) == 'business_mandatory_source_incomplete:numeric_registry:unregistered_fields'
    config = SimpleNamespace(market=market, code_commit='a' * 40)
    try:
        raise error
    except BusinessMandatorySourceIncomplete as exc:
        job._record_local_failure(tmp_path, exc, config=config, session='2026-11-25',
            generation='synthetic-' + market + '-source', before_owner_cleanup=True)
    path = tmp_path / 'failure-diagnostic.json'
    original = path.read_bytes()
    receipt = json.loads(original)
    assert receipt['stable_error_code'] == 'business_mandatory_source_incomplete'
    assert receipt['source_context'] == dict(market=market, ticker=ticker,
        mandatory_missing=['numeric_registry:unregistered_fields'],
        unregistered_fields=[dict(fact_id='chart:2026-11-25',
            field_path='fields.support_invalidation.latest_daily_close')])
    assert receipt['market'] == market and receipt['NO_SEND'] is True
    assert receipt['recorded_before_owner_cleanup'] is True
    assert b'123.5' not in original and b'SYNTHETIC_PRIVATE' not in original
    integrity = json.loads((tmp_path / 'failure-diagnostic-sha256.json').read_bytes())
    assert integrity == dict(file=path.name, bytes=len(original), sha256=sha256(original).hexdigest())
    job._record_local_failure(tmp_path, RuntimeError('SYNTHETIC_CLEANUP'),
        config=config, session='2026-11-25')
    assert path.read_bytes() == original


def test_untyped_exception_cannot_export_matching_prefix_or_context(tmp_path):
    error = ValueError('business_mandatory_source_incomplete:SYNTHETIC_PRIVATE_DO_NOT_EXPORT')
    error.source_context = dict(ticker='SYNTHETIC_PRIVATE_DO_NOT_EXPORT')
    job._record_local_failure(tmp_path, error,
        config=SimpleNamespace(market='us', code_commit='b' * 40), session='2026-11-25')
    raw = (tmp_path / 'failure-diagnostic.json').read_bytes()
    receipt = json.loads(raw)
    assert receipt['stable_error_code'] is None and 'source_context' not in receipt
    assert b'SYNTHETIC_PRIVATE' not in raw


def test_scheduled_cycle_still_stops_and_reraises_original_source_error(tmp_path, monkeypatch):
    error = failure()

    async def cycle(*args):
        raise error

    with pytest.raises(BusinessMandatorySourceIncomplete) as caught:
        asyncio.run(execute(tmp_path, monkeypatch, cycle))
    assert caught.value is error
    output = tmp_path / 'runs/us-2026-11-19'
    terminal = json.loads((output / 'terminal.json').read_bytes())
    assert terminal == dict(status='STOPPED_NO_SEND',
        error_type='BusinessMandatorySourceIncomplete', normal_messages_sent=False)
    receipt = json.loads((output / 'failure-diagnostic.json').read_bytes())
    assert receipt['stable_error_code'] == error.code and receipt['source_context'] == error.source_context
    assert asyncio.run(execute(tmp_path, monkeypatch, cycle))['reason'] == 'SESSION_ALREADY_CONSUMED'
