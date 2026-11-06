"""Opt-in original US cohort close capture, never chart or ACTIVE authority."""
import json
from types import SimpleNamespace

from app.services.completed_price_state import required_source_slot
from app.services.scoped_source_plan import ScopedPriceCaptureSelection
from app.services.unified_stock_acquisition import UNIVERSE

CONTRACT = 'pending-scoped-completed-close-parent-v1'
PURPOSE = 'SCOPED_COMPLETED_CLOSE_ONLY_PENDING'


def requirements(config, wire):
    selection = config.capture_selection
    subjects = config.subjects
    if (type(selection) is not ScopedPriceCaptureSelection
            or selection.contract != 'scoped-price-capture-selection-v1'
            or wire['stock_reads'] or selection.market_contexts
            or {s.market for s in subjects} != {'us'}
            or {s.ticker for s in subjects} != set(UNIVERSE['us'])
            or set(selection.close_security_ids) != {s.security_id for s in subjects}):
        raise ValueError('pending_close_exact_registered_us_cohort_required')
    plan = wire['request_plan']
    target = next(s.target.isoformat() for s in wire['sessions'] if s.market == 'us')
    # The original explicit price selection uses registered exact venues. It
    # emits no exchange-discovery binding; no discovery response is fabricated.
    expected = {'kiwoom:auth'} | {'completed_close:' + s.ticker for s in subjects}
    if (len(plan.descriptors) != len(expected)
            or {d.logical_request_id for d in plan.descriptors} != expected
            or any(d.transient_retry_max != 0 for d in plan.descriptors)):
        raise ValueError('pending_close_exact_original_descriptor_graph_required')
    auth = next(d for d in plan.descriptors if d.logical_request_id == 'kiwoom:auth')
    auth_wire = json.loads(auth.request_json)
    auth_body = json.loads(auth_wire['body'])
    if (auth.endpoint_operation != 'credential_exchange' or auth.response_binding is not None
            or not auth.mandatory or auth.consumer_role != 'kiwoom:credential_exchange'
            or auth.max_transport_attempts != 1 or auth.provider != 'kiwoom'
            or auth.market != 'global' or auth_wire['method'] != 'POST'
            or auth_wire['url'] != 'https://api.kiwoom.com/oauth2/token'
            or set(auth_body) != {'grant_type','appkey','secretkey'}
            or auth_body['grant_type'] != 'client_credentials'):
        raise ValueError('pending_close_original_auth_slot_required')
    rows = []
    for s in subjects:
        read = SimpleNamespace(subject=s.ticker,
            exchange={'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}[s.venue],
            latest_completed_session=target)
        d = required_source_slot(plan, read)
        if d is None or d.max_transport_attempts != 1 or s.currency != 'USD':
            raise ValueError('pending_close_original_mandatory_slot_required')
        rows.append(dict(security_id=s.security_id, session=target))
    return tuple(rows)


def validate_worker_command(handoff, stock, templates, command):
    """Narrow child command gate in addition to parent's original sealed DAG."""
    if (handoff.get('scope') != PURPOSE or handoff.get('contract') != CONTRACT
            or stock['reads'] or set(command) != {'market_wire'}):
        raise PermissionError('PENDING_CLOSE_ONLY_COMMAND_SCOPE')
    action = command['market_wire']
    template = templates[action['logical_id']]
    if (template['endpoint_operation'] not in {'credential_exchange','usa20590'}
            or not template['mandatory'] or template.get('response_binding') is not None
            or template['generation_id'] != stock['run_id']):
        raise PermissionError('PENDING_CLOSE_ONLY_EXACT_TEMPLATE_REQUIRED')
    # Existing Worker below checks the entire resolved wire and parent RPC
    # enforces request identity, authentication and physical limits again.
    wire = json.loads(action['request_json'])
    if wire != json.loads(template['request_json']):
        raise PermissionError('PENDING_CLOSE_ONLY_WIRE_IDENTITY')
    return True
