"""Fictional sealed-source fixtures with explicit request/finality provenance."""
from datetime import datetime, timedelta

from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL
from app.services.market_session import preceding_exchange_session_date
from app.services.night_futures_session_mapping_service import resolve_us_morning_night_reference_date
from app.services.unified_snapshot_contract import digest


def night_fixture(observed='2026-09-27T08:00:00+00:00', *, run='test', case='empty'):
    when = datetime.fromisoformat(observed)
    clock = resolve_us_morning_night_reference_date(when)
    expected = clock.expected_reference_date
    session = preceding_exchange_session_date('XKRX', expected) if case == 'stale' else expected
    reference = preceding_exchange_session_date('XKRX', session)
    final = clock.session_clock_finality == 'FINAL_BY_06_00_KST'
    row = dict(series_code='KRX_KOSPI200_NIGHT_FUT', category='kr_night_futures',
        value=110, previous_value=100, change_value=10, change_pct=10, market_session='kr_night',
        observed_at=f'{session}T06:00:00+09:00', quality_status='fresh' if final else 'unfinalized',
        source_url=KRX_FUTURES_DAILY_URL, raw_payload=dict(instrument='KOSPI200', product='KOSPI200',
            contract_code='SYNTHETIC', session_basis_contract='night-futures-session-basis-v1',
            exchange='XKRX', session_type='NIGHT', session_date=str(session),
            session_close=f'{session}T06:00:00+09:00', reference_session='DAY',
            reference_date=str(reference), reference_price=100, current_session_price=110,
            comparison_semantic='completed_night_close_minus_immediately_preceding_day_close',
            night_source_record_id=f'{session}:NIGHT:SYNTHETIC',
            reference_source_record_id=f'{reference}:DAY:SYNTHETIC',
            night_source_payload_sha256='a'*64, reference_source_payload_sha256='b'*64,
            expected_reference_date=str(expected), expected_latest_session_date=str(expected),
            provider_raw_bas_dd=str(session), finality_valid=final,
            reference_date_match=session == expected, session_freshness='fresh' if final else 'unfinalized'))
    receipts, statuses, hashes = [], [], {}
    for day in (expected, preceding_exchange_session_date('XKRX', expected)):
        artifact = f'raw/night:{day}.json'
        sha = 'a'*64 if day == expected else 'b'*64
        hashes[artifact] = sha
        receipts.append(dict(run_id=run, acquisition_id=run+':night', provider='krx_night_futures',
            artifact=artifact, artifact_sha256=sha, http_status=200, outcome='HTTP_RESPONSE',
            requested_at=observed, received_at=(when+timedelta(seconds=1)).isoformat(),
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd':day.strftime('%Y%m%d')})))
        statuses.append(dict(query_date=str(day), http_status=200, raw_payload_sha256=sha))
    value = dict(provider='krx_night_futures', observations=[] if case == 'empty' else [row],
        telemetry=dict(reference_date_contract=clock.contract, expected_reference_date=str(expected),
            expected_latest_session_date=str(expected), finality_valid=final,
            queried_dates=[s['query_date'] for s in statuses], date_statuses=statuses))
    return dict(observed_at=observed, original_run_id=run, original_acquisition_id=run+':night',
        original_receipts=receipts, source_hashes=hashes, value=value, value_sha256=digest(value))
