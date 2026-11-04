"""Current-session rendering through accepted Market, business and valuation owners."""
from app.services.accepted_calibration_message_service import AcceptedMarketCalibration
from app.services.accepted_stock_plan import stock_plan
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.daily_digest_renderer import render_daily_digest
from app.services.detailed_stock_message_service import build_detailed_plan
from app.services.detailed_stock_message_v2 import build_detailed_plan_v2, render_detailed_v2
from app.services.kr_forward_valuation_context import calibration_context
from app.services.kr_forward_valuation_message import build_plan as build_kr_plan
from app.services.market_display_plan import build_display_plan
from app.services.production_b2_execution import ProductionB2ExecutionAuthorizationV1
from app.services.unavailable_price_valuation import parse_view
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as market_owner


def source_only_message(owner, handle):
    """Explicit unsent review route; never an accepted investment message."""
    from app.services.source_only_report import render_source_only_report

    return render_source_only_report(owner, handle)


def market_message(session):
    data = session.projected[session.market]
    packet, context = data['packet'], data['context']
    output = session.markets[session.market]
    source = packet['market_context']
    if (market_owner.validate_market(output, context)['status'] != 'PASS'
            or market_owner.numeric_boundary(context, source)['status'] != 'PASS'):
        raise ValueError('production_market_render_owner_gap')
    display = build_display_plan(source, market=session.market, assessment_date=packet['assessment_date'],
        eligible_refs=context['request_eligible_refs'], display_view=data['views']['display'])
    receipt = dict(status='PASS', errors=[], market=session.market, assessment_date=packet['assessment_date'],
        source_context_sha256=digest(source), decision_sha256=digest(output),
        numeric_catalog_sha256=digest(context['numeric_catalog']), display_plan_sha256=digest(display.model_dump(mode='json')))
    plan = AcceptedMarketCalibration(market=session.market, assessment_date=packet['assessment_date'],
        source_context=source, decision=output, acceptance=receipt, acceptance_sha256=digest(receipt),
        numeric_catalog=context['numeric_catalog'], display_plan=display)
    return dict(message_id='MARKET_'+session.market.upper(), generation_id=session.gen,
        text=render_daily_digest(None, accepted_market=plan), plan_sha256=digest(plan.model_dump(mode='json')))


def stock_message(session, ticker, b2_row):
    source = session.fresh_stocks[ticker]
    packet = DecisionEvidencePacket.model_validate(source['evidence_packet'])
    base = build_detailed_plan(packet=packet, accepted=stock_plan(session, ticker, packet), source_stock=source,
        core=session.cores[ticker], pass_a=session.arows[ticker], valuation=parse_view(source['valuation_view']))
    if session.market == 'kr':
        forward = session.source.get('forward_views', {}).get(ticker)
        if forward is None or calibration_context(forward) != session.valuation_context(ticker):
            raise ValueError('production_kr_forward_render_owner_gap')
        base = build_kr_plan(packet, base, forward)
    request = session.b2_request(ticker)
    plan = build_detailed_plan_v2(packet=packet, base=base, b2_request=request,
        b2_result=b2_row['result'], authorization=ProductionB2ExecutionAuthorizationV1.model_validate(b2_row['authorization']))
    return dict(message_id=ticker, **render_detailed_v2(packet, plan))
