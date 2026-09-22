"""Diagnostic capture of existing market renderers; not an accepted R4 AI result."""
from __future__ import annotations

import argparse
import asyncio
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sys

from scripts.m12ds_r4_source_preflight import helpers


def digest(data):
    return hashlib.sha256(data).hexdigest()


async def capture_payload(payload, max_chars=None):
    """Replace only the external chunk effect, retaining production prepare/split/send."""
    import httpx
    from app.services.notification_service import TelegramChunkResult, TelegramNotifier

    if payload.get('use_llm') is not False:
        raise ValueError('offline_capture_requires_no_llm')
    chunks, prepared = [], []

    def reject_network(_request):
        raise RuntimeError('CAPTURE_NETWORK_FORBIDDEN')

    class CaptureNotifier(TelegramNotifier):
        async def prepare_text(self, value):
            result = await super().prepare_text(value)
            prepared.append(result)
            return result

        async def _send_chunk(self, _client, text):
            chunks.append(text)
            return TelegramChunkResult(message_id=None)

    notifier = CaptureNotifier(transport=httpx.MockTransport(reject_network))
    updates = {'notification_dry_run': False, 'telegram_bot_token': '', 'telegram_chat_id': ''}
    if max_chars is not None:
        updates['telegram_message_max_chars'] = max_chars
    notifier.settings = notifier.settings.model_copy(update=updates)
    await notifier.send(payload)
    if prepared != [payload['text']] or not chunks:
        raise ValueError('payload_fidelity_failed')
    return {'prepared_text': prepared[0], 'chunks': chunks,
            'source_payload_sha256': digest(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()),
            'prepared_text_sha256': digest(prepared[0].encode()),
            'chunk_sha256': [digest(t.encode()) for t in chunks],
            'prepare_owner': 'TelegramNotifier.prepare_text', 'payload_builder_owner': 'TelegramNotifier.send',
            'chunk_owner': 'TelegramNotifier.build_chunks', 'send_boundary_owner': 'TelegramNotifier._send_chunk',
            'sink_invocations': len(chunks), 'network_requests': 0,
            'production_recipient_intents': 0, 'production_sends': 0}


def night_trace(root, packets, inputs, rendered, captures):
    from app.services.night_futures_visibility_service import night_futures_user_facing_visibility

    probe = helpers.read_json(root / 'source/night-probe.json')
    canonical = helpers.read_json(root / 'source/night-provider.json')['observations']
    raw_rows = json.loads((root / 'source/night-raw-row-index.json').read_bytes())
    result = []
    for observation in probe['observations']:
        product = observation['product']
        fact = next(r for r in canonical if r['raw_payload']['product'] == product)
        raw = next(r for r in raw_rows if r['row_identity'] == observation['night_source_record_id']
                   and r['response_sha256'] == observation['night_source_payload_sha256'])
        baseline = next(r for r in raw_rows if r['row_identity'] == observation['reference_source_record_id']
                        and r['response_sha256'] == observation['reference_source_payload_sha256'])
        field = next(r for r in packets['us']['market_context']['night_futures'] if r['series_code'] == fact['series_code'])
        context_fact = next(r for r in packets['us']['market_context']['fact_catalog'] if r['fact_id'] == field['fact_id'])
        label = product
        matched = [line for chunk in captures['us']['chunks'] for line in chunk.splitlines() if label in line]
        raw_ohlc = {k: raw['raw_row'].get(k) for k in ('TDD_OPNPRC', 'TDD_HGPRC', 'TDD_LWPRC', 'TDD_CLSPRC', 'ACC_TRDVOL')}
        canonical_daily = fact['raw_payload']['night_timeframes']['daily']
        numeric_line = any(f"{fact['value']:,.2f}" in line and f"{fact['change_pct']:+.2f}%" in line for line in matched)
        result.append({'product': product, 'raw_row_identity': raw['row_identity'], 'raw_response_sha256': raw['response_sha256'],
            'raw_ohlcv': raw_ohlc, 'raw_owner': 'app.jobs.probe_krx_night_futures',
            'canonical_owner': 'app.macro.providers.krx.KrxNightFuturesProvider',
            'canonical_observation_sha256': digest(json.dumps(fact, sort_keys=True).encode()),
            'canonical_daily': canonical_daily, 'canonical_daily_ohlc_present': True,
            'contract_code': observation['contract_code'], 'contract_maturity': observation['maturity'],
            'night_reference_date': observation['session_date'], 'finality_valid': observation['finality_valid'],
            'baseline_row_identity': baseline['row_identity'], 'baseline_raw_sha256': baseline['response_sha256'],
            'baseline_date': observation['reference_date'], 'baseline_session': observation['reference_session'],
            'baseline_close': observation['reference_price'], 'night_close': observation['night_close'],
            'change_value': observation['point_change'], 'change_pct': observation['change_pct'],
            'formula': '(night_close - immediately_preceding_same_contract_regular_close) / regular_close * 100',
            'context_fact': context_fact, 'context_owner': 'app.services.ai_review_service',
            'context_night_timeframes_present': field.get('night_timeframes') is not None,
            'reference_date_contract_in_packet': field.get('reference_date_contract'),
            'model_input_owner': 'scripts.m12ds_r3_market.market_context',
            'model_input_eligible': field['fact_id'] in inputs['us']['facts'],
            'model_input_hash': digest(json.dumps(inputs['us'], sort_keys=True).encode()),
            'model_inference': 'NOT_RUN_SOURCE_GATE_BLOCKED',
            'renderer_owner': 'app.services.us_full_message_service.render_us_full_market_message',
            'renderer_selected': field['fact_id'] in rendered.night_fact_ids,
            'exact_captured_substrings': matched, 'formatted_numeric_match': numeric_line,
            'us_transport_chunk_sha256': captures['us']['chunk_sha256'],
            'kr_duplicate_present': label in captures['kr']['prepared_text'],
            'placement': 'US recap of 2026-09-21 with latest final night context for KR 2026-09-22; not KR 2026-09-21 close',
            'visibility_suppression': night_futures_user_facing_visibility('us').suppression_reason,
            'input_suppression': [r for r in inputs['us']['parity_matrix'] if r['ref'] == field['fact_id']],
            'status': 'FAIL_EXPECTED_AVAILABLE_FACT_NOT_RENDERED' if not matched else 'PARTIAL_DIAGNOSTIC_NOT_ACCEPTED_AI_E2E'})
    return {'status': 'FAIL' if any(not r['exact_captured_substrings'] for r in result) else 'INCOMPLETE',
            'reason': 'expected_available_official_facts_suppressed_and_accepted_market_inference_not_run', 'products': result,
            'snapshot_preserved': True, 'posthoc_text_editing': False}


async def run(root, name):
    if Path(name).name != name:
        raise ValueError('diagnostic_name_must_be_basename')
    output = root / name
    if output.exists():
        raise ValueError('new_diagnostic_output_required')
    data = root / 'private/isolated-data'
    os.environ.update(THESIS_MONITOR_ENV_FILE='/dev/null', DATA_DIR=str(data),
        DATABASE_URL=f'sqlite:///{data / "thesis_monitor.sqlite3"}', NOTIFICATION_DRY_RUN='true',
        TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', TELEGRAM_TEST_CHAT_ID='')
    from sqlmodel import Session, create_engine
    from app.services.daily_digest import build_daily_digest
    from app.services.daily_digest_renderer import render_daily_digest
    from app.services.us_full_message_service import render_us_full_market_message
    from scripts.m12ds_r3_market import market_context

    def offline(event, _args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
            raise RuntimeError('OFFLINE_DIAGNOSTIC_BOUNDARY')

    sys.addaudithook(offline)
    database = data / 'thesis_monitor.sqlite3'
    before = helpers.sha256_file(database)
    packets = {m: helpers.read_json(root / f'private/current-packets/{m}.json') for m in ('us', 'kr')}
    input_packets = {m: helpers.read_json(root / f'snapshot/{m}-packet.json') for m in packets}
    inputs = {m: market_context(input_packets[m]) for m in packets}
    rendered = render_us_full_market_message(packets['us']['market_context'])
    sessions = helpers.read_json(root / 'report/current-market-sessions.json')
    engine = create_engine(f'sqlite:///file:{database}?mode=ro&uri=true')
    with Session(engine) as session:
        kr_digest = build_daily_digest(session, date.fromisoformat(sessions['kr']['latest_completed_regular_session_date']),
            market_scope='kr', market_context=packets['kr']['market_context'])
        kr_text = render_daily_digest(kr_digest, include_stock_details=False)
    texts = {'us': rendered.text, 'kr': kr_text}
    captures = {}
    for market, text in texts.items():
        captures[market] = await capture_payload({'text': text, 'use_llm': False, 'type': 'daily_digest', 'market': market})
        path = output / f'captures/market/{market}.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
        for index, chunk in enumerate(captures[market]['chunks'], 1):
            # Exact bytes are written without adding a trailing newline.
            path = output / f'captures/transport/{market}-{index:02d}.txt'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(chunk.encode())
        helpers.write_json(output / f'inputs/{market}-market.json', inputs[market])
    trace = night_trace(root, packets, inputs, rendered, captures)
    helpers.write_json(output / 'night-futures-e2e-trace.json', trace)
    helpers.write_json(output / 'capture-sink-trace.json', {'scope': 'EXISTING_MARKET_RENDERER_DIAGNOSTIC_ONLY',
        'accepted_r4_message_count': 0, 'diagnostic_market_messages': 2, 'expected_messages': 24,
        'missing_stocks': sorted(s['ticker'] for p in packets.values() for s in p['stocks']),
        'rows': {m: {k: v for k, v in r.items() if k not in ('prepared_text', 'chunks')} for m, r in captures.items()},
        'production_send': 0, 'production_recipient_intent': 0, 'model_calls': 0})
    helpers.write_json(output / 'message-quality-audit.json', {'status': 'INCOMPLETE',
        'accepted_r4_messages': 0, 'expected': 24, 'diagnostic_markets': 2,
        'reason': 'CRCL_source_gate_prevents_fresh_R3_Core_A_B_and_stock_messages',
        'us_renderer_status': rendered.status, 'us_renderer_errors': rendered.validation_errors,
        'kr_renderer': 'app.services.daily_digest_renderer.render_daily_digest',
        'kr_legacy_portfolio_counts_are_not_fresh_R3_decisions': True,
        'all_numeric_claims_bound': False, 'stock_quality_not_run': True,
        'posthoc_text_editing': False, 'production_db_access': False})
    if helpers.sha256_file(database) != before:
        raise ValueError('diagnostic_readonly_database_changed')
    helpers.write_json(output / 'isolation.json', {'isolated_db_unchanged': True, 'network_calls': 0,
        'model_calls': 0, 'production_db_access': False, 'production_recipient_intents': 0})
    print(json.dumps({'diagnostic_market_messages': 2, 'accepted_r4_messages': 0,
        'us_renderer': rendered.status, 'night_e2e': trace['status'], 'model_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--name', default='diagnostic')
    args = parser.parse_args()
    asyncio.run(run(args.root.resolve(), args.name))
