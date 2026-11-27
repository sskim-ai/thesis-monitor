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
from app.services.production_b2_execution import parse_authorization
from app.services.unavailable_price_valuation import parse_view, shadow_request_context
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as market_owner


def source_only_message(owner, handle):
    """Explicit unsent review route; never an accepted investment message."""
    from app.services.source_only_report import render_source_only_report

    return render_source_only_report(owner, handle)


def market_message(session, *, sector_taxonomy_version=None, macro_display_capture=None,
                   fx_observations=(),fx_source_policy=None,fx_cutoff=None,ecos_fx_body=None,ecos_fx_prior=(),
                   allow_partition=False):
    if macro_display_capture is not None:
        raise ValueError('sealed_macro_capture_offline_source_only_not_current_owner')
    data = session.projected[session.market]
    packet, context = data['packet'], data['context']
    output = session.markets[session.market]
    source = packet['market_context']
    if (market_owner.validate_market(output, context)['status'] != 'PASS'
            or market_owner.numeric_boundary(context, source)['status'] != 'PASS'):
        raise ValueError('production_market_render_owner_gap')
    display = build_display_plan(source, market=session.market, assessment_date=packet['assessment_date'],
        eligible_refs=context['request_eligible_refs'], display_view=data['views']['display'],
        sector_taxonomy_version=sector_taxonomy_version, macro_display_capture=macro_display_capture,
        fx_observations=fx_observations,fx_source_policy=fx_source_policy,fx_cutoff=fx_cutoff,
        ecos_fx_body=ecos_fx_body,ecos_fx_prior=ecos_fx_prior)
    receipt = dict(status='PASS', errors=[], market=session.market, assessment_date=packet['assessment_date'],
        source_context_sha256=digest(source), decision_sha256=digest(output),
        numeric_catalog_sha256=digest(context['numeric_catalog']), display_plan_sha256=digest(display.model_dump(mode='json')))
    plan = AcceptedMarketCalibration(market=session.market, assessment_date=packet['assessment_date'],
        source_context=source, decision=output, acceptance=receipt, acceptance_sha256=digest(receipt),
        numeric_catalog=context['numeric_catalog'], display_plan=display)
    message = dict(message_id='MARKET_'+session.market.upper(), generation_id=session.gen,
        text=render_daily_digest(None, accepted_market=plan), plan_sha256=digest(plan.model_dump(mode='json')))
    if session.market == 'us':
        from app.services.selected_news_rate_limit import disclose
        subjects=set(session.fresh_stocks)
        message = disclose(message, [s.get('event_view', {}) for s in session.fresh_stocks.values()],
            expected_count=len(subjects),allow_partition=allow_partition)
    return message


def stock_message(session, ticker, b2_row, *, execution_profile=None, include_summary=False):
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
    entry_context = shadow_request_context(session.bctx[ticker], source)
    plan = build_detailed_plan_v2(packet=packet, base=base, b2_request=request, entry_context=entry_context,
        b2_result=b2_row['result'], authorization=parse_authorization(b2_row['authorization'], execution_profile=execution_profile))
    message = dict(message_id=ticker, **render_detailed_v2(packet, plan, entry_context=entry_context))
    if include_summary:
        from app.services.monitoring_summary import accepted_stock_summary
        message['summary_row'] = accepted_stock_summary(packet, plan, entry_context)
    if session.market == 'us':
        context = getattr(session, 'projected', {}).get('us', {}).get('context', {})
        if market_owner.excluded_night_narrative_errors(message, context, fields=('text',)):
            raise ValueError('production_stock_excluded_night_narrative')
        from app.services.selected_news_rate_limit import disclose
        message = disclose(message, [source.get('event_view', {})], expected_count=1,allow_partition=include_summary)
    return message


def limitation_message(session, ticker, *, include_summary=False):
    from app.services.detailed_stock_message_service import build_unknown_plan, detailed_render
    from app.services.selected_news_rate_limit import disclose

    decision = session.limitation_decision(ticker)
    prepared = session.prepared[ticker]
    source = session.fresh_stocks[ticker]
    packet = DecisionEvidencePacket.model_validate(source['evidence_packet'])
    plan = build_unknown_plan(source_stock=source, source_authority=prepared['source_authority'],
        local_seed=session.limitation_seed(ticker), decision=decision, execution_generation_id=session.gen,
        valuation=parse_view(source['valuation_view']), context_only_display=True)
    rendered = detailed_render(packet, plan)
    if rendered.ticker != ticker or not rendered.validation.valid:
        raise ValueError('production_limitation_render_reject')
    message = dict(message_id=ticker, generation_id=session.gen,
        decision_mode='UNKNOWN_LIMIT', text=rendered.text, plan_sha256=plan.acceptance_sha256,
        limitation_decision_sha256=digest(decision))
    if include_summary:
        from app.services.detailed_stock_message_service import reference_price_display
        message['summary_row'] = dict(ticker=ticker, status='UNKNOWN_LIMIT',
            price=reference_price_display(plan.valuation.price,plan.valuation.currency) if plan.valuation.price is not None else '미확보',
            plan_sha256=plan.acceptance_sha256)
    return disclose(message, [source.get('event_view', {})], expected_count=1,allow_partition=include_summary)
