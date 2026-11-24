"""Diagnose saved night responses with current code; never collect or accept them.

The original generation is read only. History required by the existing
materializer is reconstructed in an automatically removed temporary directory.
An unrecorded request ends replay; it is never filled with an invented response.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import httpx

from app.jobs.probe_krx_night_futures import (
    KRX_FUTURES_DAILY_URL, KST, fetch_live_probe, parse_krx_futures_payloads,
)
from app.macro.providers.krx import materialize_night_probe
from app.services.unified_snapshot_contract import digest


class RecordedPrefixExhausted(RuntimeError):
    """The saved request prefix ends before the current probe does."""


def _read(root, relative):
    path = root / relative
    if (Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError('night_saved_path_outside_source')
    return path.read_bytes()


def _json(root, relative):
    return json.loads(_read(root, relative))


def failure(stage, exc):
    """Keep a code location and a known code token, never arbitrary error text."""
    message = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ''
    code = (message if re.fullmatch(r'(?:night_|krx_|same_contract_)[a-z0-9_]{1,100}', message)
            else type(exc).__name__)
    frame = None
    trace = exc.__traceback__
    while trace is not None:
        path = Path(trace.tb_frame.f_code.co_filename)
        if 'app' in path.parts or 'scripts' in path.parts:
            frame = dict(file=path.name, function=trace.tb_frame.f_code.co_name, line=trace.tb_lineno)
        trace = trace.tb_next
    return dict(stage=stage, error_class=type(exc).__name__, stable_error_code=code,
                application_frame=frame)


def read_capture(root):
    frozen = _json(root, 'production-frozen-source-plan.json')
    at = datetime.fromisoformat(frozen['frozen_at'])
    if at.utcoffset() is None:
        raise ValueError('night_saved_timezone_required')
    descriptors = {d['logical_request_id']: d for d in frozen['plan']['descriptors']}
    paths = sorted((root / 'night/probe').glob('receipt-*.json'))
    if not 1 <= len(paths) <= 7:
        raise ValueError('night_saved_receipts_unavailable_or_unbounded')
    receipts, bodies = [], {}
    for index, path in enumerate(paths):
        row = _json(root, str(path.relative_to(root)))
        day = (at.astimezone(KST).date() - timedelta(days=index)).strftime('%Y%m%d')
        key = row['sealed_logical_id']
        descriptor = descriptors[key]
        final = _json(root, 'dispatch/receipts/' + key + '/final.json')
        if (row['run_id'] != frozen['generation_id'] or row['provider'] != 'krx_night_futures'
                or row['outcome'] != 'HTTP_RESPONSE' or row['http_status'] != 200
                or row['request'] != dict(method='GET', route=KRX_FUTURES_DAILY_URL, params={'basDd': day})
                or descriptor['provider'] != 'krx_night_futures'
                or descriptor['consumer_role'] != key or not key.startswith('night:KOSPI200:')
                or row['artifact'] != descriptor['raw_path']
                or final['status'] != 'PASS'
                or row['sealed_final_receipt_sha256'] != final['receipt_sha256']
                or digest({k: v for k, v in final.items() if k != 'receipt_sha256'}) != final['receipt_sha256']):
            raise ValueError('night_saved_receipt_binding_mismatch')
        body = _read(root, 'dispatch/' + row['artifact'])
        sha = hashlib.sha256(body).hexdigest()
        if sha != row['artifact_sha256'] or sha != final['raw_sha256']:
            raise ValueError('night_saved_body_hash_mismatch')
        if not at <= datetime.fromisoformat(row['requested_at']) <= datetime.fromisoformat(row['received_at']):
            raise ValueError('night_saved_receipt_time_mismatch')
        if row['artifact'] in bodies:
            raise ValueError('night_saved_duplicate_artifact')
        bodies[row['artifact']] = body
        receipts.append(row)
    phase_path = root / 'phase-night.json'
    phase = _json(root, 'phase-night.json') if phase_path.is_file() else {}
    return frozen, at, receipts, bodies, phase


def _probe_summary(probe):
    return dict(status=probe.status, parser_status=probe.parser_status,
        canonicalization_status=probe.canonicalization_status,
        night_session_usable=probe.night_session_usable, session_freshness=probe.session_freshness,
        expected_reference_date=str(probe.expected_reference_date) if probe.expected_reference_date else None,
        source_date=str(probe.source_date) if probe.source_date else None,
        queried_dates=[d.isoformat() for d in probe.queried_dates],
        returned_business_dates=[d.isoformat() for d in probe.returned_business_dates],
        row_count=probe.row_count, parsed_row_count=probe.parsed_row_count,
        observations=[{key: row.model_dump(mode='json').get(key) for key in (
            'product', 'contract_code', 'maturity', 'session_date', 'reference_date',
            'night_close', 'regular_close', 'point_change', 'change_pct',
            'reference_date_match', 'finality_valid')} for row in probe.observations])


class SavedResponses(httpx.AsyncBaseTransport):
    def __init__(self, receipts, bodies):
        self.receipts, self.bodies, self.used = receipts, bodies, 0
        self.unrecorded_query_date = None

    async def handle_async_request(self, request):
        if self.used == len(self.receipts):
            self.unrecorded_query_date = request.url.params.get('basDd')
            raise RecordedPrefixExhausted()
        row = self.receipts[self.used]
        if (request.method != 'GET' or str(request.url.copy_with(query=None)) != KRX_FUTURES_DAILY_URL
                or dict(request.url.params) != row['request']['params']):
            raise RuntimeError('night_saved_replay_request_mismatch')
        self.used += 1
        return httpx.Response(200, content=self.bodies[row['artifact']], request=request)


def inspect(source_root):
    root = Path(source_root).absolute()
    report = dict(contract='saved-night-inspection-v1', source_root=str(root),
        purpose='CURRENT_CODE_DIAGNOSTIC_NOT_SOURCE_OR_MODEL_ACCEPTANCE', status='FAILED',
        original_failure_cause_confirmed=False,
        financial_http_calls=0, model_calls=0, production_db_calls=0, source_acceptances=0,
        source_files_modified=0, stages={})
    stage = 'read_saved_capture'
    try:
        frozen, at, receipts, bodies, phase = read_capture(root)
        report.update(generation_id=frozen['generation_id'], observed_at=at.isoformat(),
            original_phase={k: phase.get(k) for k in ('status', 'error_class')},
            original_failure_note='C46 inner exception detail was not recorded; current replay is a separate result.',
            recorded_response_count=len(receipts), recorded_body_bytes=sum(map(len, bodies.values())),
            recorded_requests=[dict(query_date=r['request']['params']['basDd'], http_status=r['http_status'],
                body_sha256=r['artifact_sha256'], logical_request_id=r['sealed_logical_id']) for r in receipts])
        report['stages'][stage] = dict(status='PASS')
        stage = 'parse_recorded_subset'
        payloads = {datetime.strptime(r['request']['params']['basDd'], '%Y%m%d').date():
                    json.loads(bodies[r['artifact']]) for r in receipts}
        hashes = {datetime.strptime(r['request']['params']['basDd'], '%Y%m%d').date():
                  r['artifact_sha256'] for r in receipts}
        parsed = parse_krx_futures_payloads(payloads, fetched_at=at,
            queried_dates=list(payloads), payload_sha256_by_date=hashes)
        report['stages'][stage] = dict(status='PASS', value=_probe_summary(parsed))
        stage = 'replay_current_probe'
        transport = SavedResponses(receipts, bodies)
        try:
            probe = asyncio.run(fetch_live_probe(run_date=at.astimezone(KST).date(), observation_time=at,
                api_key='offline-saved-capture', transport=transport, max_lookback_days=7))
        except RecordedPrefixExhausted:
            report.update(status='INCOMPLETE_SAVED_CAPTURE')
            report['stages'][stage] = dict(status='RECORDED_PREFIX_EXHAUSTED',
                recorded_responses_consumed=transport.used, unrecorded_query_date=transport.unrecorded_query_date)
            return report
        report['stages'][stage] = dict(status='PASS', recorded_responses_consumed=transport.used,
            unused_recorded_responses=len(receipts)-transport.used, value=_probe_summary(probe))
        stage = 'materialize_current_daily_weekly_monthly'
        # This is a diagnostic of verified saved capture bytes, not a new live call.
        probe.live_source = True
        with TemporaryDirectory(prefix='c52-saved-night-') as temporary:
            value = materialize_night_probe(probe, history_directory=Path(temporary), night_end_dates=True)
        report['stages'][stage] = dict(status='PASS',
            observations=[dict(series_code=row.series_code, value=row.value, previous_value=row.previous_value,
                change_value=row.change_value, change_pct=row.change_pct, quality_status=row.quality_status,
                session_date=row.raw_payload.get('session_date'), reference_date=row.raw_payload.get('reference_date'),
                contract_code=row.raw_payload.get('contract_code'),
                timeframes=row.raw_payload.get('night_timeframes')) for row in value.observations])
        report['status'] = 'CURRENT_CODE_REPLAY_COMPLETE'
    except Exception as exc:
        report['stages'][stage] = dict(status='FAILED', failure=failure(stage, exc))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.source_root.resolve()):
        parser.error('--output must be outside the saved source generation')
    report = inspect(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], output=str(args.output), financial_http_calls=0, model_calls=0)))
    return 0 if report['status'] == 'CURRENT_CODE_REPLAY_COMPLETE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
