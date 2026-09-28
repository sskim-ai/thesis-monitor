"""Replay explicitly supplied synthetic outputs through real post-model owners.

No model, source acquisition, delivery or persistence entry point. The fixture
generator is separate; this validator never fills an invalid output for it.
"""
import asyncio
from types import SimpleNamespace

from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.detailed_stock_message_service import build_detailed_plan, build_unknown_plan, final_detailed_audit
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_contract as c
from scripts import r2b_r2_preflight as pre
from scripts.m12ds_r2_ranges import materialize_ranges
from scripts.m12ds_r4_r1_accepted_capture import stock_plan
from scripts.m12ds_r4_offline_capture import capture_payload


def core_inputs(result, generation, raw):
    data = result['prepared']
    t = result['stock']['ticker']
    src = data['core_input']
    schema = c.schemas.core_schema({t: src})
    c._require(not pre.owner.validate_json_schema({'cores': {t: raw}}, schema), 'offline_core_schema')
    core = c.policy.materialize_core(t, raw, src['metadata'], src['authority'], src['frozen_fact_fields'])
    cat, sub, chain = pre.subject_inputs(data['view'], data['source_authority'], data['view_receipt'],
                                       generation=generation, atomic=core['atomic_claims'])
    gate = pre.a_input(data['view'], cat, sub, chain, data['source_authority'])
    c._require(gate['receipt']['status'] == 'PASS', 'offline_a_input')
    ctx = gate['model_context']
    schema_a = pre.owner.future_pass_a_batch_schema(subjects=[t], subject_contexts={t: ctx},
        source_use_inputs={t: dict(catalog=cat, chain=chain, source_metadata=sub['decision_evidence'],
            source_generation_id=chain['source_generation_id'], execution_generation_id=generation)})
    return dict(core=core, cat=cat, sub=sub, chain=chain, a_context=ctx, core_schema=schema, a_schema=schema_a)


def a_inputs(result, state, raw):
    t = result['stock']['ticker']
    c._require(not pre.owner.validate_json_schema(raw, state['a_schema']), 'offline_a_schema')
    rows, receipt = pre.owner.materialize_future_pass_a(raw, subjects=[t], subject_contexts={t: state['a_context']})
    c._require(receipt['status'] == 'PASS' and len(rows) == 1 and rows[0]['ticker'] == t,
               'offline_a_materialization:' + str(receipt))
    c._require(pre.owner.pass_a_output_leak_scan(raw)['status'] == 'PASS', 'offline_a_leakage')
    chain = state['chain']
    identity = dict(generation_id=chain['execution_generation_id'], packet_id='offline-phase-a:' + t,
                    market=result['stock']['market'], assessment_date=result['stock']['packet']['assessment_date'])
    envelope = pre.owner.PassABatchOutput.model_validate(dict(
        contract='m12cq-pass-a-archetype-regime-v1', **identity, classifications=rows))
    semantic = pre.owner.validate_pass_a_batch(envelope, expected_identity=identity, subjects=[t],
        subject_contexts={t: state['a_context']}, source_catalogs={t: state['cat']},
        source_use_views={t: chain['projection']}, source_use_bindings={t: chain['binding']},
        source_use_expectations={t: chain['expectation']}, source_metadata_by_ticker={t: state['sub']['decision_evidence']},
        source_generation_id=chain['source_generation_id'], execution_generation_id=chain['execution_generation_id'],
        require_source_use=True)
    c._require(semantic['status'] == 'PASS', 'offline_a_batch_semantic:' + str(semantic))
    cap = c.policy.axis_capability(state['core'], state['chain'], state['cat'], state['sub']['decision_evidence'])
    ctx, entries, valuation = pre.b_input(result['prepared']['view'], state['cat'], state['sub'], state['chain'], rows[0], cap)
    ctx['r2_core_effects'] = state['core']['effects']
    return dict(**state, a=rows[0], a_receipt=dict(materialization=receipt, semantic=semantic), cap=cap, b_context=ctx, entries=entries,
                ranges=valuation, b_schema=c.decision_schema('EVIDENCE_BASED', cap, valuation, entries, {}))


def replay_stages(result, generation, outputs):
    """Every accepted row is rebuilt; no receipt status supplied by the caller."""
    data, stock = result['prepared'], result['stock']
    t = stock['ticker']
    ep = DecisionEvidencePacket.model_validate(stock['evidence_packet'])
    valuation = CurrentValuationView.model_validate(stock['valuation_view'])
    schemas, accepted, stage_receipts = {}, {}, {}
    if data['mode'] == 'UNKNOWN_LIMIT':
        for stage in ('core', 'a', 'b'):
            c.validate_unknown(outputs[stage], mode=data['mode'], recovery=data['recovery'],
                               capability={k: [] for k in c.DIRECTION_BUCKETS})
        accepted = outputs
        plan = build_unknown_plan(source_stock=stock, source_authority=result['authority'],
            local_seed=outputs['local_seed'], decision=outputs['b'], execution_generation_id=generation, valuation=valuation)
    else:
        state = a_inputs(result, core_inputs(result, generation, outputs['core']), outputs['a'])
        c._require(not pre.owner.validate_json_schema(outputs['b'], state['b_schema']), 'offline_b_schema')
        row, receipt = c.validate_decision(outputs['b'], mode=data['mode'], cap=state['cap'],
                                           valuation=state['ranges'], recovery={})
        c._require(receipt['status'] == 'PASS', 'offline_b_policy:' + str(receipt))
        entries = materialize_ranges(state['ranges'], state['entries'], row['tactical_choice'])
        proof = SimpleNamespace(POLICY=c.policy, DETAILED_PRESENTATION=True, source_gen=stock['fresh_run_id'],
            gen=generation, brows={t: row}, entries={t: entries}, cores={t: state['core']}, chains={t: state['chain']},
            catalogs={t: state['cat']}, subjects={t: state['sub']}, caps={t: state['cap']}, ranges={t: state['ranges']},
            arows={t: state['a']}, bctx={t: state['b_context']}, fresh_stocks={t: stock})
        calibrated = stock_plan(proof, t, ep)
        plan = build_detailed_plan(packet=ep, accepted=calibrated, source_stock=stock,
            core=state['core'], pass_a=state['a'], valuation=valuation)
        schemas = {s: digest(state[s + '_schema']) for s in ('core', 'a', 'b')}
        accepted = dict(core=state['core'], a=state['a'], b=row)
        stage_receipts = dict(a=state['a_receipt'], b=receipt)
    rendered = render_accepted_v2_production(ep, plan)
    c._require(rendered.validation.valid, 'offline_detailed_validation')
    captured = asyncio.run(capture_payload(dict(type='stock_review', market=stock['market'], ticker=t,
                                              text=rendered.text, use_llm=False)))
    c._require(captured['prepared_text'] == rendered.text and captured['production_sends'] == 0
               and captured['network_requests'] == 0, 'offline_capture_boundary')
    audit = final_detailed_audit(captured['prepared_text'], ep, plan)
    c._require(audit['status'] == 'PASS', 'offline_detailed_audit')
    return dict(status='PASS', ticker=t, generation_id=generation, source_generation_id=stock['fresh_run_id'],
        source_sha256=digest(stock), mode=data['mode'], raw_outputs=outputs, accepted_outputs=accepted,
        schemas=schemas, stage_receipts=stage_receipts, detailed_plan=plan.model_dump(mode='json'),
        capture=captured, audit=audit, synthetic_only=True, external_model_calls=0)


def replay_market(whole, market, output):
    from scripts.r2b_r5_market_adapter import project_sealed_market_context
    from scripts import m12ds_r4_r4_market as owner
    from app.services.market_display_plan import build_display_plan
    from app.services.accepted_calibration_message_service import AcceptedMarketCalibration
    from app.services.daily_digest_renderer import render_daily_digest
    projected = project_sealed_market_context(whole['packets'][market], whole['seed'], whole['authority_graph'],
                                              expected_authority_sha256=whole['authority_graph_sha256'])
    packet, context = projected['packet'], projected['context']
    c._require(not pre.owner.validate_json_schema(output, owner.market_schema(context)), 'offline_market_schema')
    semantic = owner.validate_market(output, context)
    c._require(semantic['status'] == 'PASS', 'offline_market_semantic:' + str(semantic))
    source = packet['market_context']
    c._require(owner.numeric_boundary(context, source)['status'] == 'PASS', 'offline_market_numeric')
    display = build_display_plan(source, market=market, assessment_date=packet['assessment_date'],
                                 eligible_refs=context['request_eligible_refs'])
    receipt = dict(status='PASS', errors=[], market=market, assessment_date=packet['assessment_date'],
        source_context_sha256=digest(source), decision_sha256=digest(output),
        numeric_catalog_sha256=digest(context['numeric_catalog']), display_plan_sha256=digest(display.model_dump(mode='json')))
    accepted = AcceptedMarketCalibration(market=market, assessment_date=packet['assessment_date'],
        source_context=source, decision=output, acceptance=receipt, acceptance_sha256=digest(receipt),
        numeric_catalog=context['numeric_catalog'], display_plan=display)
    text = render_daily_digest(None, accepted_market=accepted)
    captured = asyncio.run(capture_payload(dict(type='daily_digest', market=market, text=text, use_llm=False)))
    c._require(captured['prepared_text'] == text and captured['production_sends'] == 0
               and captured['network_requests'] == 0, 'offline_market_sender')
    return dict(status='PASS', market=market, projected=projected, accepted=accepted.model_dump(mode='json'),
                capture=captured, semantic=semantic, schema_sha256=digest(owner.market_schema(context)))
