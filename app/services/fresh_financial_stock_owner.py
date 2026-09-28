"""Fresh raw acquisition -> comparison/quality/valuation -> existing stock view."""

from copy import deepcopy
from datetime import datetime

from app.services import bounded_financial_stock_owner as financial
from app.services.canonical_business_quality_owner import derive_fresh
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.current_fresh_valuation import derive_current_valuation
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.fresh_source_run_contract import reject_current_carryin, validate_local_seed
from app.services.packet_owned_technical_context_service import PacketOwnedTechnicalContext
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_owner import assemble_stock


def assemble_fresh_stock(*, technical_inputs, financial_inputs):
    """Rebuild all owners; never accept a caller's prebuilt stock or quality."""
    tech, fin = dict(technical_inputs), dict(financial_inputs)
    if set(fin) - {'plan', 'acquisition', 'directory', 'receipts', 'field_semantics', 'issuer_business'}:
        raise ValueError('fresh_financial_input_owner_unrecognized')
    plan, fp = tech['plan'], fin['plan']
    validate_local_seed(tech['local_seed'])
    reject_current_carryin(fp)
    if (fp['run_id'] != plan.run_id or fp['cutoff'] != plan.frozen_at.isoformat()
            or fp['ticker'] != tech['ticker'] or fp.get('retained_subjects')):
        raise ValueError('fresh_financial_stock_generation_mismatch')
    if tech.get('financial') is not None or tech.get('event_source') is not None:
        raise ValueError('fresh_stock_no_parent_mutable_input')
    tech.update(financial=None, fresh_financial_pending=True)
    if tech['expected_hashes']['financial'] != digest(None):
        raise ValueError('fresh_stock_pending_financial_identity_mismatch')
    # Financial receipts bind immutable raw responses and request plans in the
    # existing projector. Additionally enforce availability in this generation.
    for receipt in fin['receipts']:
        times = [datetime.fromisoformat(receipt[key]) for key in ('started_at', 'finished_at')]
        if any(at.utcoffset() is None for at in times) or not plan.frozen_at <= times[0] <= times[1]:
            raise ValueError('fresh_financial_receipt_predates_generation')
    baseline = assemble_stock(**tech)
    result = financial.assemble(baseline=baseline, local_seed=tech['local_seed'], **fin)
    facts = [f for f in result['packet']['stocks'][0]['fact_catalog']
             if 'canonical:' + f['fact_id'] in result['comparative_fact_refs']]
    bridge = result.get('issuer_business_bridge')
    if bridge:
        # Native source must itself be reassembled, not a previously stored
        # bridge output. Both plans and source receipt epochs are bound above.
        source_inputs = fin['issuer_business']['source_inputs']
        if source_inputs['plan']['run_id'] != plan.run_id:
            raise ValueError('fresh_bridge_source_generation_mismatch')
        source_result = financial.assemble(**source_inputs)
        projection = source_result['projection']
        source_ticker = source_inputs['plan']['ticker']
    else:
        projection, source_ticker = result['projection'], fp['ticker']
    quality = derive_fresh(projection=projection, facts=facts, ticker=fp['ticker'],
        security_id=fp['security']['canonical_security_id'], run_id=plan.run_id,
        source_ticker=source_ticker, bridge=bridge)
    packet = deepcopy(result['packet'])
    stock = packet['stocks'][0]
    stock['fact_catalog'].append(quality['fact'])
    stock['numeric_registry'] = financial.build_shadow_numeric_registry(stock['fact_catalog'])
    # Issuer business bridges deliberately cannot supply a security denominator.
    valuation_projection = result['projection']
    if bridge:
        valuation = None
        valuation_denial = 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    else:
        valuation = derive_current_valuation(ticker=fp['ticker'], run_id=plan.run_id,
            security=fp['security'], price=stock['current_price_context'], projection=valuation_projection)
        valuation_denial = None
    stock['current_valuation_view'] = valuation.model_dump(mode='json') if valuation else None
    stock['current_valuation_denial'] = valuation_denial
    evidence = build_decision_evidence_packet(packet=packet, stock=stock,
        technical_context=PacketOwnedTechnicalContext.model_validate(stock['technical_context']))
    owned = build_owned_evidence_packet(evidence, stock=stock)
    qref = quality['receipt']['canonical_ref']
    if qref not in {r.ref_id for r in evidence.evidence}:
        raise ValueError('fresh_quality_typed_ref_missing')
    missing = list(result['mandatory_missing'])
    if result['acquisition_denials']:
        missing.append('fresh_financial_acquisition:source_denied')
    if valuation is None:
        missing.append('current_valuation_view:' + valuation_denial)
    if quality['receipt']['state'] in {'denied', 'unknown'}:
        missing.append('fresh_financial_quality:' + quality['receipt']['state'])
    packet['source_time_domains'] = dict(scope='FRESH_CURRENT_RUN', run_id=plan.run_id,
        started_at=plan.frozen_at.isoformat(), financial_plan_sha256=digest(fp))
    # Packet metadata participates in the evidence identity, so build it only
    # after all deterministic source owners have completed.
    evidence = build_decision_evidence_packet(packet=packet, stock=stock,
        technical_context=PacketOwnedTechnicalContext.model_validate(stock['technical_context']))
    owned = build_owned_evidence_packet(evidence, stock=stock)
    graph = {**baseline['source_graph'], **result['financial_source_graph'],
             quality['fact']['fact_id']: dict(fact_sha256=digest(quality['fact']),
                 ticker=fp['ticker'], source='current_financial_quality',
                 receipt_sha256=quality['receipt']['receipt_sha256'])}
    return {**result, 'contract': 'fresh-financial-stock-owner-v1',
        'status': 'BLOCKED' if missing else 'PASS', 'mandatory_missing': sorted(set(missing)),
        'packet': packet, 'packet_sha256': digest(packet) if not missing else None,
        'diagnostic_packet_sha256': digest(packet), 'evidence_packet': evidence.model_dump(mode='json'),
        'ownership': owned.model_dump(mode='json'), 'source_graph': graph,
        'quality_view': quality, 'valuation_view': stock['current_valuation_view'],
        'input_hashes': {**result['input_hashes'], 'technical_owner': digest(baseline),
                         'quality': digest(quality), 'valuation': digest(stock['current_valuation_view'])},
        'fresh_run_id': plan.run_id, 'complete_source_adapter_qualified': False}
