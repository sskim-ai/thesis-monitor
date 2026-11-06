"""Dated inspection of original Market components; not a Market grant issuer.

The original Cold owns raw/receipt/normalization verification. This consumer
exposes that verified value without reconstructing a live handoff or supplying
missing publication, night, production or economic authority.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path

from app.services.unified_snapshot_contract import digest

CONTRACT = 'dated-market-component-reference-v1'


def read_dated_component(bundle_path, *, expected_sha256, enabled=False):
    if enabled is not True:
        raise ValueError('dated_market_component_reference_disabled')
    from app.services.current_scoped_source_results import _root, _read
    from app.services.market_component_execution import cold_component

    path = Path(bundle_path).absolute()
    parent = _root(path.parent)
    raw = _read(parent, path.name, expected_sha256)
    bundle = json.loads(raw)
    # Cold replays original response-selected pages and the original semantic
    # aggregate Owner. A saved Cold JSON receipt is not ingress authority.
    cold = cold_component(bundle)
    market = bundle['market']
    root = _root(Path(bundle['root']).parent / (market + '-market'))
    value_bytes = _read(root, 'aggregate-value.json')
    receipt = json.loads(_read(root, 'aggregate.json'))
    value = json.loads(value_bytes)
    original = bundle['owner_proof']
    if (hashlib.sha256(value_bytes).hexdigest() != receipt['artifact_sha256']
            or digest(value) != original['value_sha256']
            or receipt['run_id'] != cold['generation_id']
            or receipt['market'] != market):
        raise ValueError('dated_market_component_value_binding')
    query = datetime.fromisoformat(bundle['cutoff'])
    if query.utcoffset() is None or receipt['session'] > query.date().isoformat():
        raise ValueError('dated_market_component_session_binding')
    return dict(contract=CONTRACT, scope='DATED_SOURCE_INSPECTION_NOT_MARKET_CONTEXT',
        market=market, completed_session=receipt['session'], query_as_of=bundle['cutoff'],
        source_generation=cold['generation_id'], original_bundle_sha256=expected_sha256,
        original_component_sha256=cold['component_sha256'], value_sha256=digest(value),
        value=value, original_cold_status=cold['status'], current_capture=False,
        live_handoff_restored=False, sealed_research_market_context=False,
        full_market_parent=False, economic_use=False, direction_use=False,
        native_use=False, send=False, new_owner_issued=False)


def render_reference(reference):
    """A deterministic source-inspection preview, never an investment message."""
    if (reference.get('contract') != CONTRACT
            or reference.get('scope') != 'DATED_SOURCE_INSPECTION_NOT_MARKET_CONTEXT'
            or digest(reference['value']) != reference['value_sha256']
            or any(reference.get(k) is not False for k in (
                'current_capture', 'live_handoff_restored', 'sealed_research_market_context',
                'full_market_parent', 'economic_use', 'direction_use', 'native_use', 'send', 'new_owner_issued'))):
        raise ValueError('dated_market_reference_render_scope_or_hash')
    return '\n'.join((
        '# Dated Market source reference (NO-SEND)',
        'Market: ' + reference['market'].upper(),
        'Completed session: ' + reference['completed_session'],
        'Original query time: ' + reference['query_as_of'],
        'Source generation: ' + reference['source_generation'],
        'Original Cold: ' + reference['original_cold_status'],
        'Scope: source inspection only; NOT a sealed research Market context,',
        'production Full Market Parent, current price or investment direction.',
        'Missing original roles remain missing; no causal or risk judgment is generated.',
        'Verified value SHA-256: ' + reference['value_sha256'],
        '',
    ))
