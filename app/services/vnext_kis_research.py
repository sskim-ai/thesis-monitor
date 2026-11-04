"""Existing KIS Owners to research observations; no network or new valuation rule."""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from app.services.vnext_research_store import digest
from scripts.kis_current_fy1_owner import eps_receipt, current_fper, calendar_receipt

CONTRACT = 'kis-owner-research-snapshot-v1'


def credentials_from_settings(settings):
    """Use the supplied original Settings capability; no fallback file scanning."""
    from scripts.kis_estimate_capability_probe import Credentials, ProbeStop
    key = getattr(settings, 'kis_app_key', None)
    secrets = [getattr(settings, k, None) for k in ('kis_app_secret', 'kis_secret_app_key')]
    if key is None or not hasattr(key, 'get_secret_value'):
        raise ProbeStop('LOCAL_KIS_SETTINGS_NEEDS_USER_ACTION')
    values = {s.get_secret_value() for s in secrets if s is not None and hasattr(s, 'get_secret_value')}
    if not key.get_secret_value() or len(values) != 1 or not next(iter(values)):
        raise ProbeStop('LOCAL_KIS_SETTINGS_NEEDS_USER_ACTION')
    return Credentials(key.get_secret_value(), values.pop())


def owner_snapshots(capsule, *, security):
    """Recompute original EPS/price/action authority, preserving exact decimals.

    The capsule enters only via the trusted reviewed-capture callback and the
    append journal. Serialized ownership hashes alone are not ingress authority.
    """
    row = capsule['owner_row'];eps = row['eps'];price = row['price']
    at = datetime.fromisoformat(capsule['qualification_as_of'])
    if (security['country'] != 'KR' or security['exchange'] not in ('KRX','KOSPI','KOSDAQ')
        or security['security_type'].lower() not in ('common stock','common_stock')
        or security['issuer_type'].lower() in ('ads','adr','unknown')
        or row['security_code'] != security['ticker'] or capsule['security'] != security
        or not capsule['source_generation'] or at.tzinfo is None
        or price['canonical_security_id'] != security['canonical_security_id']
        or datetime.fromisoformat(price['calendar_owner_receipt']['as_of']) > at
        or calendar_receipt(at.isoformat())['latest_completed_session'] != price['session_date']):
        raise ValueError('kis_owner_security_or_qualification_scope')
    value = eps_receipt(eps)
    recomputed = current_fper(eps, price, row['action'])
    if recomputed != row['current_fper'] or recomputed['state'] != 'QUALIFIED':
        raise ValueError('kis_original_owner_reproduction_or_eligibility')
    if eps['period'] != recomputed['fy1_period'] or not eps['period'].endswith('E'):
        raise ValueError('kis_forecast_period_mismatch')
    sources = set(capsule['sources'])
    required = {eps['estimate_sha256'], eps['security']['source_sha256'], price['raw_response_sha256']}
    def add_sources(value):
        if isinstance(value,dict):
            required.update(value.get('source_hashes', []))
            for v in value.values():add_sources(v)
        elif isinstance(value,list):
            for v in value:add_sources(v)
    add_sources(row['action'])
    if not required <= sources:
        raise ValueError('kis_original_sources_missing')
    queried = datetime.fromisoformat(eps['query_time'])
    if queried > at or queried.date() != at.date():
        raise ValueError('kis_capture_not_current_qualification_session')
    common = dict(contract=CONTRACT,canonical_security_id=security['canonical_security_id'],
        requested_security_id=security['ticker'],source_generation=capsule['source_generation'],
        original_owner_record_sha256=digest(row),period=eps['period'],estimate_date=eps['estdate'],
        price_session=price['session_date'],retrieval_timestamp=eps['query_time'],
        qualification_as_of=capsule['qualification_as_of'],display_eligible=True,
        source_kind='KIS_HOUSE_RESEARCH_NOT_CONSENSUS',allowed_use='PUBLIC_RESEARCH_REFERENCE_ONLY',
        strict_native=False,direction_allowed=False,provider_native_PER=False,
        share_unit_guard=row['action']['receipt_sha256'],source_age_days=recomputed['source_age_days'],
        caveat='Capture freshness is not estimate freshness. Original share-unit guard and estimate date remain binding.')
    return [dict(common,metric=metric,value=float(Decimal(exact)),exact_value=exact,unit=unit,metric_semantic=semantic,
                 source_sha256=sha) for metric,exact,unit,semantic,sha in (
        ('FY1_EPS',str(value),'KRW_PER_SHARE','KIS_HOUSE_FY1_EPS',eps['estimate_sha256']),
        ('FPER',recomputed['display_value'],'multiple','KIS_UNADJUSTED_CLOSE_DIVIDED_BY_FY1_EPS',price['raw_response_sha256']))]


def reviewed_batch(reviewed_capture, *, expected_digest, security, cutoff):
    if not callable(reviewed_capture):
        raise ValueError('backend_kis_owner_replay_capability_required')
    batch = deepcopy(reviewed_capture())
    if digest(batch) != expected_digest or batch['security'] != security:
        raise ValueError('kis_reviewed_capture_or_identity_changed')
    capsule = batch['capsule'];run = batch['run']
    if (capsule['source_generation'] != run['run_id'] or capsule['security'] != security
        or datetime.fromisoformat(capsule['qualification_as_of']) != datetime.fromisoformat(cutoff)
        or not 2 <= len(batch['captures']) <= 32):
        raise ValueError('kis_current_generation_or_capture_bound')
    seen, requests = set(), set()
    for item in batch['captures']:
        raw = item['raw'].encode();sha = digest(raw);r = item['receipt']
        if (item['request_key'] in requests or len(raw)>2*1024**2 or sha != r.get('raw_sha256')
            or r.get('run_id') != run['run_id'] or r.get('auth') is not False
            or r.get('raw_birth') != 'CURRENT_HTTP' or r.get('status') != 200
            or item['provider'] not in ('KIS','OpenDART') or r.get('provider') != item['provider']
            or r.get('request_key') != item['request_key'] or digest(r['request']) != item['request_key']
            or not datetime.fromisoformat(run['started_at']) <= datetime.fromisoformat(r['captured_at']) <= datetime.fromisoformat(cutoff)):
            raise ValueError('kis_original_capture_receipt_binding')
        # Original receipts must already be credential-free public projections.
        from scripts.kis_estimate_capability_probe import scan
        scan(raw, [], auth_fields=True)
        scan(__import__('json').dumps(r).encode(), [], auth_fields=True)
        seen.add(sha)
        requests.add(item['request_key'])
    if seen != set(capsule['sources']):
        raise ValueError('kis_source_manifest_mismatch')
    return batch, owner_snapshots(capsule, security=security)
