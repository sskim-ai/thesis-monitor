"""Current parent-owned applicability of historical purpose, never raw freshness.

The control plane supplies the original live Class-C owner. Public receipts are
audit data, not reconstruction credentials. Provider-specific raw/quality owners
remain authoritative and historical reconciliation v1 stays diagnostic only.

Capabilities and downgrade tombstones live only in the trusted parent process.
Restart requires a new registration parent and original-input replay; serialized
receipts cannot restore authority. This module is not a durable ownership store.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import hmac
import json
import secrets
from weakref import WeakKeyDictionary

from app.services.unified_snapshot_contract import digest, encoded

CONTRACT = 'CURRENT_SOURCE_PURPOSE_WINDOW_INTAKE_V1'
POLICY = 'CURRENT_PARENT_FIELD_LOCAL_PURPOSE_APPLICABILITY_V1'
_PARENTS = WeakKeyDictionary()
_INTAKES = WeakKeyDictionary()
_PROJECTIONS = WeakKeyDictionary()
_CURRENT_PLANS = set()
_IDENTITY = ('canonical_company_id', 'canonical_security_id', 'cik', 'corp_code',
             'issuer_type', 'security_type', 'ordinary_share_identifier', 'adr_ratio', 'exchange')
_FILING = ('form', 'accessionNumber', 'primaryDocument', 'filingDate', 'reportDate')


def _now():
    return datetime.now(timezone.utc)


def source_family(plan):
    security = plan['security']
    if (digest(security) != plan['identity_sha256'] or plan['ticker'] != security['ticker']
            or not all(security.get(k) for k in ('canonical_company_id', 'canonical_security_id', 'identity_provider'))):
        raise ValueError('current_financial_canonical_identity_mismatch')
    forms = {f.split('/')[0] for f in plan['forms']}
    if plan['provider'] == 'sec_edgar' and plan['market'] == 'us':
        if str(security.get('cik') or '').zfill(10) != plan['issuer']:
            raise ValueError('current_financial_provider_issuer_mismatch')
        kind = security.get('issuer_type')
        if kind == 'domestic_us' and forms == {'10-Q', '10-K'}:
            return 'SEC_DOMESTIC'
        if kind in {'foreign_private_issuer', 'adr'} and forms == {'6-K', '20-F'}:
            return 'SEC_FPI'
    elif (plan['provider'] == 'opendart' and plan['market'] == 'kr'
          and forms == {'11013', '11012', '11014', '11011'}):
        if security.get('corp_code') != plan['issuer']:
            raise ValueError('current_financial_provider_issuer_mismatch')
        return 'OPENDART'
    raise ValueError('UNSUPPORTED_SOURCE_FAMILY')


class CurrentFinancialParent:
    __slots__ = ('__weakref__',)


class CurrentPurposeIntake:
    __slots__ = ('__weakref__',)


def _registered(owner, plan):
    from app.services.prospective_class_c_owner import _state, require_generation, apply_prospective_owner
    require_generation(owner, plan['run_id'])
    document, receipt = _state(owner)
    document = apply_prospective_owner(document, original=document, owner=owner)
    if (receipt['cutoff'] != plan['cutoff'] or receipt['market'] != plan['market']
            or plan['ticker'] not in receipt['bindings']
            or not all(r['eligible'] for r in document['roles'].values())):
        raise ValueError('current_financial_registration_scope_mismatch')
    records = [r['record'] for c in document['roles'].values() for r in c['records']
               if r['table'] == 'securitymaster' and r['record']['ticker'] == plan['ticker']]
    if not records or any(any(r.get(k) != plan['security'].get(k) for k in _IDENTITY) for r in records):
        raise ValueError('current_financial_registered_identity_mismatch')
    return receipt


def issue_parent(*, registration_owner, plan):
    """Trusted orchestrator boundary; membership does not itself admit a fact."""
    family = source_family(plan)
    receipt = _registered(registration_owner, plan)
    parent = CurrentFinancialParent()
    _PARENTS[parent] = (registration_owner, deepcopy(plan), secrets.token_bytes(32),
        dict(contract='current-financial-parent-v1', source_family=family,
             issuer_canonical_id=plan['security']['canonical_company_id'],
             security_canonical_id=plan['security']['canonical_security_id'],
             provider=plan['provider'], provider_issuer=plan['issuer'], run_id=plan['run_id'],
             cutoff=plan['cutoff'], expires_at=receipt['expires_at'], issued_at=_now().isoformat(),
             source_plan_sha256=digest(plan), registration_receipt_sha256=digest(receipt),
             scope='FINANCIAL_SOURCE_INTAKE_ONLY_NOT_NATIVE_OR_DIRECTION'))
    _CURRENT_PLANS.add(digest(plan))
    return parent


def resolve_parent(parent, *, plan=None):
    if type(parent) is not CurrentFinancialParent or parent not in _PARENTS:
        raise ValueError('current_financial_live_parent_required')
    owner, original, _, receipt = _PARENTS[parent]
    registration = _registered(owner, original)
    if (_now() >= datetime.fromisoformat(receipt['expires_at'])
            or digest(registration) != receipt['registration_receipt_sha256']
            or plan is not None and digest(plan) != receipt['source_plan_sha256']):
        raise ValueError('current_financial_parent_expired_or_plan_changed')
    return deepcopy(receipt)


def revoke_parent(parent):
    resolve_parent(parent)
    del _PARENTS[parent]


def validate_current_capture(parent, *, plan, acquisition, directory, receipts):
    from app.services.bounded_financial_projection import verify_capture
    receipt = resolve_parent(parent, plan=plan)
    verify_capture(plan, acquisition, directory, receipts)
    cutoff, expiry = (datetime.fromisoformat(receipt[k]) for k in ('cutoff', 'expires_at'))
    if not receipts:
        raise ValueError('CURRENT_SOURCE_CAPTURE_PENDING')
    for row in receipts:
        start, end = (datetime.fromisoformat(row[k]) for k in ('started_at', 'finished_at'))
        if (start.utcoffset() is None or end.utcoffset() is None or not cutoff <= start <= end <= _now()
                or end >= expiry):
            raise ValueError('CURRENT_SOURCE_CAPTURE_PENDING')
    return receipt


def project_current(parent, *, plan, acquisition, directory, receipts, **options):
    """Original projector replay held by the live parent, not caller quality JSON."""
    from app.services.bounded_financial_projection import project
    plan, acquisition, receipts = deepcopy((plan, acquisition, receipts))
    # Opaque capabilities are intentionally kept by reference, never serialized.
    options = dict(options)

    def build():
        validate_current_capture(parent, plan=plan, acquisition=acquisition, directory=directory, receipts=receipts)
        return project(plan, acquisition, directory, receipts, **options)

    projection = build()
    _PROJECTIONS.setdefault(parent, {})[digest(projection)] = (build, digest(plan), digest(acquisition), deepcopy(plan))
    return projection


def require_legacy_scope(*, projection, facts, plan=None):
    """Plan tombstones survive revocation; facts do not define request scope.

    This guard is not legacy authorization. The selected-owner boundary also
    requires original producer replay and exact issued-selection lookup. A
    separately verified historical plan may legitimately contain identical facts.
    """
    fields = projection.get('fpi_purpose', {}).get('selection', {}).get('fields', {})
    if (plan is not None and digest(plan) in _CURRENT_PLANS
            or projection.get('plan_sha256') in _CURRENT_PLANS
            or projection.get('current_purpose_intake') is not None
            or projection.get('source_completeness', {}).get('current_purpose_applicability_sha256')
            or any(row.get('current_purpose_applicability') for row in fields.values())):
        raise ValueError('selected_financial_current_route_cannot_downgrade')


def require_current_projection(parent, projection, facts, *, plan=None, acquisition=None):
    from app.services.bounded_financial_stock_owner import reported_comparisons
    resolve_parent(parent, plan=plan)
    record = _PROJECTIONS.get(parent, {}).get(digest(projection))
    if record is None:
        raise ValueError('current_financial_original_projection_required')
    build, plan_sha, acquisition_sha, original = record
    if (build() != projection or plan is not None and digest(plan) != plan_sha
            or acquisition is not None and digest(acquisition) != acquisition_sha):
        raise ValueError('current_financial_original_projection_changed')
    expected, _ = reported_comparisons(original, projection)
    if expected != facts:
        raise ValueError('current_financial_original_comparisons_mismatch')


def issue_intake(*, parent, plan, acquisition, directory, receipts,
                 historical_plan, reconciliation):
    """Only SEC FPI has this purpose adapter; domestic and DART use their owners."""
    from app.services.bounded_financial_projection import _raw
    from app.services.sec_fpi_financial_purpose import candidate_inventory
    from app.services.sec_fpi_purpose_reconciliation import resolve as resolve_historical
    if source_family(plan) != 'SEC_FPI' or source_family(historical_plan) != 'SEC_FPI':
        raise ValueError('current_purpose_wrong_source_family')
    plan, acquisition, receipts, historical_plan = deepcopy((plan, acquisition, receipts, historical_plan))
    if (plan['issuer'] != historical_plan['issuer']
            or any(plan['security'].get(k) != historical_plan['security'].get(k) for k in _IDENTITY)):
        raise ValueError('current_purpose_original_identity_mismatch')

    def build():
        parent_receipt = validate_current_capture(parent, plan=plan, acquisition=acquisition,
                                                  directory=directory, receipts=receipts)
        review = resolve_historical(reconciliation, plan=historical_plan)
        if (datetime.fromisoformat(review['auxiliary_cutoff']) > datetime.fromisoformat(plan['cutoff'])
                or datetime.fromisoformat(review['original_cutoff']) > datetime.fromisoformat(plan['cutoff'])):
            raise ValueError('current_purpose_future_historical_review')
        discovery = [r for r in receipts if r['stage'] == 'discovery' and not r['failure_class']]
        if len(discovery) != 1:
            raise ValueError('current_purpose_current_discovery_required')
        payload = json.loads(_raw(directory, discovery[0]['artifact'], receipts))
        if str(payload.get('cik', '')).zfill(10) != plan['issuer']:
            raise ValueError('current_purpose_discovery_issuer_mismatch')
        inventory = candidate_inventory(payload, plan)
        current_filings = inventory['candidates']
        old_catalog = review['original_candidate_plan']
        # Audit completeness is retained independently of field-local supersession.
        for old in old_catalog['candidates'] + old_catalog['outside_bound']:
            filing = old.get('filing', old)
            if not any(all(filing.get(k) == row.get(k) for k in _FILING) for row in current_filings):
                raise ValueError('current_purpose_original_inventory_dropped')
        for row in review['records']:
            filing = row['binding']['filing']
            if not any(all(filing.get(k) == v.get(k) for k in _FILING) for v in current_filings):
                raise ValueError('current_purpose_reviewed_occurrence_changed')
        result = dict(contract=CONTRACT, policy=POLICY, policy_sha256=digest(POLICY),
            parent=parent_receipt, source_family='SEC_FPI', provider='sec_edgar',
            current_plan_sha256=digest(plan), current_acquisition_sha256=digest(acquisition),
            current_receipts_sha256=digest(receipts), current_inventory=inventory,
            original_generation=review['original_generation'], original_cutoff=review['original_cutoff'],
            auxiliary_generation=review['auxiliary_generation'], auxiliary_cutoff=review['auxiliary_cutoff'],
            original_reconciliation_sha256=review['receipt_sha256'],
            original_candidate_plan=old_catalog, records=review['records'],
            scope='FIELD_LOCAL_PURPOSE_APPLICABILITY_ONLY', financial_authority=False,
            source_history_exhausted=False, valuation_eligible=False, direction_eligible=False)
        result['receipt_sha256'] = digest(result)
        return result

    frozen = build()
    key = _PARENTS[parent][2]
    signature = hmac.new(key, encoded(frozen), hashlib.sha256).hexdigest()
    capability = CurrentPurposeIntake()
    _INTAKES[capability] = (parent, build, frozen, signature)
    return capability


def resolve(capability, *, plan=None, acquisition=None, receipts=None):
    if type(capability) is not CurrentPurposeIntake or capability not in _INTAKES:
        raise ValueError('current_purpose_live_capability_required')
    parent, build, frozen, signature = _INTAKES[capability]
    resolve_parent(parent, plan=plan)
    current = build()
    if current != frozen or not hmac.compare_digest(signature,
            hmac.new(_PARENTS[parent][2], encoded(current), hashlib.sha256).hexdigest()):
        raise ValueError('current_purpose_source_or_policy_drift')
    for value, key in ((acquisition, 'current_acquisition_sha256'), (receipts, 'current_receipts_sha256')):
        if value is not None and digest(value) != current[key]:
            raise ValueError('current_purpose_capture_binding_mismatch')
    return {**deepcopy(current), 'backend_signature': signature}


def revoke_intake(capability):
    resolve(capability)
    del _INTAKES[capability]


def require_projection(capability, projection):
    receipt = resolve(capability)
    if projection.get('current_purpose_intake') != receipt:
        raise ValueError('current_purpose_projection_binding_mismatch')
    return receipt
