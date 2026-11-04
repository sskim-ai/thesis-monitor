"""Offline KR ratio processing using original receipt and snapshot validators."""
from datetime import datetime
import json
from pathlib import Path

from app.services.vnext_research_store import digest

POLICY = 'vnext-valuation-replay-v1'


def implementation_identity():
    from app.services import (vnext_legacy_reuse, provider_native_valuation_snapshot,
                              unified_source_policy, vnext_research_store,
                              unified_snapshot_contract, unified_run_artifacts,
                              official_security_identity_service)
    return {Path(p).name: digest(Path(p).read_bytes()) for p in
            (__file__, vnext_legacy_reuse.__file__, provider_native_valuation_snapshot.__file__,
             unified_source_policy.__file__, vnext_research_store.__file__,
             unified_snapshot_contract.__file__, unified_run_artifacts.__file__,
             official_security_identity_service.__file__)}


def replay_valuation(store, run_id, ticker, market_type, *, persist=False):
    from app.services.vnext_legacy_reuse import native_valuation_inputs
    from app.services.provider_native_valuation_snapshot import (
        derive_provider_snapshots,
    )
    securities = [s for s in store.identities() if s['ticker'] == ticker]
    if len(securities) != 1 or securities[0].get('country') != 'KR':
        raise ValueError('registered_kr_identity_required')
    security = securities[0]
    with store.connect() as c:
        run = c.execute('SELECT started_at,as_of FROM research_run WHERE run_id=?', (run_id,)).fetchone()
        timestamps = c.execute('SELECT captured_at FROM source_capture WHERE run_id=? AND provider=?', (run_id, 'Kiwoom')).fetchall()
    if not run:
        raise ValueError('original_run_required')
    if not timestamps:raise ValueError('original_receipts_required')
    cutoff = max(datetime.fromisoformat(t[0]) for t in timestamps)
    inputs = native_valuation_inputs(store,run_id,security,'kiwoom',market_type=market_type,cutoff=cutoff)
    snapshots = [s.model_dump(mode='json') for s in
                 derive_provider_snapshots(inputs, security=security, run_id=run_id)]
    for s in snapshots:
        if persist:
            field = 'valuation.' + s['metric']
            key = digest([run_id, ticker, field, s['raw_sha256']])
            with store.connect() as c:
                old = c.execute('SELECT payload_json FROM research_observation WHERE observation_id=?', (key,)).fetchone()
            if old:
                if json.loads(old[0]).get('snapshot') != s:
                    raise ValueError('existing_valuation_observation_conflict')
                # Preserve original capture flags, time and receipt byte-for-byte.
                continue
            store.observation(run_id, ticker, 'valuation.' + s['metric'],
                              'SOURCE_REFERENCE' if s['display_eligible'] else 'POLICY_DENIED',
                              s['raw_sha256'], dict(snapshot=s, strict_native=False,
                              current_capture=False, source_captured_this_run=False,
                              source_captured_at=s['retrieval_timestamp'], research_only=True,
                              replay_contract=POLICY))
    return dict(contract='vnext-valuation-replay-v1', run_id=run_id, source_as_of=run[1],
                security_sha256=digest(security), ticker=ticker, snapshots=snapshots,
                processing='ORIGINAL_RECEIPT_REPLAY_NOT_NEW_COLLECTION',
                physical_http_attempts=0, strict_native_ready=False, send_allowed=False)
