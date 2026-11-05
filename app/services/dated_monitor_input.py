"""Read-only, no-grant preview of previously sealed indicator projections."""
import gzip
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

from app.services.unified_snapshot_contract import digest

CONTRACT = 'dated-monitor-input-v1'
DENIED = ('CURRENT_PRODUCTION_SOURCE', 'FULL_MARKET_PARENT',
          'MARKET_RESEARCH_MODEL_PASS', 'AI_TECHNICAL_SIGNAL', 'NATIVE',
          'STRICT_READY', 'SEND')
ROLES = {'adjusted_daily': ('daily', True),
         'adjusted_weekly': ('weekly', True),
         'adjusted_monthly': ('monthly', True),
         'unadjusted_weekly_valuation': ('weekly', False)}


def read_pinned(path, expected):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('dated_symlink_denied')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('dated_source_bytes_changed')
    return raw


def read_projection(record, metadata):
    value = json.loads(gzip.decompress(read_pinned(record['path'], record['sha256'])))
    p, identity = value['projection'], value['identity']
    if digest(p) != record['projection_sha256'] or value['projection_sha256'] != digest(p):
        raise ValueError('dated_projection_digest_changed')
    role = record['role']
    timeframe, adjusted = ROLES[role]
    expected = dict(ticker=record['ticker'], role=role, timeframe=timeframe,
                    adjusted=adjusted, basis='ADJUSTED_CHART' if adjusted else 'UNADJUSTED_CHART',
                    contract='historical-original-indicator-projection-v1')
    if any(p[k] != v for k, v in expected.items()):
        raise ValueError('dated_projection_role_identity_changed')
    for key, other in [('generation', 'generation'), ('observed_at', 'observed_at'),
                       ('original_raw_sha', 'raw_sha256'), ('original_rows_sha', 'rows'),
                       ('algorithm_sha', 'algorithm_sha'), ('adapter_sha', 'adapter_sha')]:
        if p[key] != identity[other]:
            raise ValueError('dated_original_identity_changed')
    read = identity['read']
    if any(read[k] != p[v] for k, v in [('subject', 'ticker'), ('role', 'role'),
            ('timeframe', 'timeframe'), ('adjusted', 'adjusted'),
            ('canonical_security_id', 'security_id'), ('market', 'market'),
            ('latest_completed_session', 'target_session')]):
        raise ValueError('dated_source_descriptor_changed')
    if any(p[k] is not False for k in ('current_eligibility', 'technical_signal', 'valuation_use', 'native_use')):
        raise ValueError('dated_authority_escalation')
    if p['quote_finality'] != 'NOT_CLAIMED':
        raise ValueError('dated_finality_escalation')
    moment = datetime.fromisoformat(p['observed_at'])
    if moment.utcoffset() is None:
        raise ValueError('dated_observation_timezone_required')
    date.fromisoformat(p['target_session'])
    checks = {'ticker': p['ticker'], 'role': role, 'market': p['market'],
              'price_basis': p['basis'], 'source_generation': p['generation'],
              'observed_at': p['observed_at'], 'cache_sha256': record['sha256'],
              'calculation_sha': digest(p), 'last_valid_as_of': p['last_valid_as_of'],
              'normalized_usable_rows': str(p['valid_bars']),
              'invalid_rows': str(len(p['invalid_rows']))}
    if any(str(metadata[k]) != str(v) for k, v in checks.items()):
        raise ValueError('dated_sealed_metadata_changed')
    if p['bars']:
        if p['bars'][-1]['date'] != p['last_valid_as_of']:
            raise ValueError('dated_latest_bar_changed')
        if set(p['bars'][-1]['indicators']) != set(p['latest_availability']):
            raise ValueError('dated_indicator_fields_changed')
    return p


def preview(projections, markets):
    keys = [(p['security_id'], p['role']) for p in projections]
    subjects = {p['security_id'] for p in projections}
    if len(projections) != 88 or len(set(keys)) != 88 or len(subjects) != 22:
        raise ValueError('dated_22_by_4_required')
    for subject in subjects:
        if {r for s, r in keys if s == subject} != set(ROLES):
            raise ValueError('dated_role_set_incomplete')
    if set(markets) != {'kr', 'us'}:
        raise ValueError('dated_two_markets_required')
    return dict(contract=CONTRACT, scope='HISTORICAL_TECHNICAL_REFERENCE',
                authority={key: False for key in DENIED}, markets=markets,
                roles=[{k: v for k, v in p.items() if k != 'bars'} | {
                    'latest_cached_bar': p['bars'][-1] if p['bars'] else None}
                       for p in projections],
                cross_generation=True, grants_issued=0,
                economic_packet='NOT_ISSUED', source_only_inherited_from='C4')
