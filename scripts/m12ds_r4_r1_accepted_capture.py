"""Bind accepted R3 results to production owners, replacing only outbound effects."""
import asyncio
import sys
from types import SimpleNamespace

from app.services.accepted_calibration_message_service import (
    AcceptedCalibrationPlan, AcceptedMarketCalibration, digest,
)
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.daily_digest_renderer import render_daily_digest
from app.services.us_full_message_service import _night_timeframe_block, render_us_full_market_message
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.m12ds_r4_r1_market import market_context, validate_market
from scripts import m12dr_fresh_blind_reproof as p
from scripts.m12cj_current_market_smoke import source_db_identity


def numeric_audit(texts, source, prefix):
    from app.services.ai_review_service import _validate_numeric_claims
    proxy = SimpleNamespace(core_judgment=SimpleNamespace(text=texts[0]),
        market_context=SimpleNamespace(text='\n'.join(texts[1:])),
        market_assumptions=SimpleNamespace(text=''), numeric_claims=[], facts_used=[],
        unknowns=[], important_changes=[], portfolio_transmission=[], next_checks=[])
    return _validate_numeric_claims(prefix, proxy, source.get('numeric_registry'),
                                   source.get('fact_catalog'), source)


def stock_plan(proof, ticker, ep):
    row, entries = proof.brows[ticker], proof.entries[ticker]
    cap = proof.POLICY.axis_capability(proof.cores[ticker], proof.chains[ticker],
        proof.catalogs[ticker], proof.subjects[ticker]['decision_evidence'])
    p.require(cap == proof.caps[ticker], 'CAPTURE_CAPABILITY_DRIFT')
    check = proof.POLICY.validate_decision(row, cap, proof.ranges[ticker])
    p.require(check['status'] == 'PASS', 'CAPTURE_POLICY_NOT_ACCEPTED')
    lineage = {c['claim_ref']: tuple(c['parent_source_refs']) for c in proof.cores[ticker]['atomic_claims']}
    receipt = dict(status='PASS', errors=[], ticker=ticker, source_generation_id=proof.source_gen,
        execution_generation_id=proof.gen, evidence_packet_sha256=digest(ep.model_dump(mode='json')),
        decision_sha256=digest(row), entries_sha256=digest(entries), claim_lineage_sha256=digest(lineage))
    quote = None
    if getattr(proof, 'TYPED_PRESENTATION', False):
        stock = next(s for packet in proof.packets.values() for s in packet['stocks'] if s['ticker']==ticker)
        candidate = stock.get('current_price_context')
        if candidate and candidate.get('availability') == 'ready' and any(entries.get(k) is not None for k in ('fundamental_entry_low','tactical_watch_low')):
            quote = candidate
            receipt['quote_context_sha256'] = digest(quote)
    return AcceptedCalibrationPlan(ticker=ticker, source_generation_id=proof.source_gen,
        execution_generation_id=proof.gen, evidence_packet_sha256=receipt['evidence_packet_sha256'],
        decision=row, entries=entries, claim_lineage=lineage, acceptance=receipt, acceptance_sha256=digest(receipt), quote_context=quote)


async def capture_all(proof):
    proof.verify()
    output = proof.root / 'accepted-capture'
    p.require(not output.exists(), 'NEW_CAPTURE_REQUIRED')
    before = source_db_identity(p.OPERATING / 'data/thesis_monitor.sqlite3')

    def offline(event, _args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
            raise RuntimeError('ACCEPTED_CAPTURE_OFFLINE_ONLY')
    sys.addaudithook(offline)
    captures, errors, audit = {}, [], []

    async def emit(name, text, kind, market):
        receipt = await capture_payload(dict(text=text, use_llm=False, type=kind, market=market))
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(receipt['prepared_text'].encode())
        for index, chunk in enumerate(receipt['chunks'], 1):
            path = output / 'transport' / (name.replace('/', '-') + f'.chunk-{index:02d}.txt')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(chunk.encode())
        captures[name] = receipt

    for market in ('us', 'kr'):
        packet, row = proof.packets[market], proof.markets[market]
        try:
            owner = getattr(proof,'MARKET_OWNER',None)
            context = owner.market_context(packet) if owner else market_context(packet)
            valid = owner.validate_market(row,context) if owner else validate_market(row,context)
            p.require(valid['status'] == 'PASS', 'MARKET_NOT_ACCEPTED')
            numeric_errors = (owner.numeric_boundary(context,packet['market_context'])['errors'] if context.get('numeric_catalog')
                else numeric_audit([row[k] for k in ('breadth_state', 'leadership',
                'flows_or_participation', 'rates_or_macro_context')], packet['market_context'], 'market_review'))
            p.require(not numeric_errors, 'MARKET_NUMERIC_BINDING:' + ','.join(numeric_errors))
            receipt = dict(status='PASS', errors=[], market=market, assessment_date=packet['assessment_date'],
                source_context_sha256=digest(packet['market_context']), decision_sha256=digest(row))
            if context.get('numeric_catalog'):
                receipt['numeric_catalog_sha256'] = digest(context['numeric_catalog'])
            plan = AcceptedMarketCalibration(market=market, assessment_date=packet['assessment_date'],
                source_context=packet['market_context'], decision=row, acceptance=receipt, acceptance_sha256=digest(receipt),
                numeric_catalog=context.get('numeric_catalog'))
            text = render_daily_digest(None, accepted_market=plan)
            await emit(f'MARKET_{market.upper()}.txt', text, 'daily_digest', market)
            if plan.numeric_catalog:
                from app.services.market_numeric_claim_service import render_typed_market_facts, final_market_numeric_audit
                prefix = render_typed_market_facts(plan.numeric_catalog,plan.source_context)+'\n\n'
                p.require(text.startswith(prefix),'MARKET_TYPED_RENDER_PREFIX_DRIFT')
                numeric = final_market_numeric_audit(text,plan.numeric_catalog,plan.source_context,text[len(prefix):])
                p.require(numeric['status']=='PASS','MARKET_FINAL_NUMERIC_AUDIT')
                p.write(output / f'bindings/market-{market}-numeric.json',dict(receipt=numeric,catalog=plan.numeric_catalog))
            p.write(output / f'bindings/market-{market}.json', plan.model_dump(mode='json'))
            audit.append(dict(subject='MARKET_' + market.upper(), status='PASS', exact_output=True))
        except (ValueError, KeyError) as exc:
            errors.append(dict(subject='MARKET_' + market.upper(), error=str(exc)))
    for market, context in proof.contexts.items():
        for ep in context.evidence_packets:
            try:
                plan = stock_plan(proof, ep.ticker, ep)
                source = next(s for s in proof.packets[market]['stocks'] if s['ticker'] == ep.ticker)
                numeric_errors = numeric_audit([plan.decision[k] for k in ('overall_reason',
                    'new_buyer_reason', 'holder_reason')], source, ep.ticker)
                p.require(not numeric_errors, 'STOCK_NUMERIC_BINDING:' + ','.join(numeric_errors))
                rendered = render_accepted_v2_production(ep, plan)
                await emit(f'STOCKS/{market}-{ep.ticker}.txt', rendered.text, 'stock_review', market)
                p.write(output / f'bindings/{market}-{ep.ticker}.json', plan.model_dump(mode='json'))
                audit.append(dict(subject=ep.ticker, status='PASS', exact_axes=True,
                    synthetic_maturity=False, synthetic_change_conditions=False))
            except (ValueError, KeyError) as exc:
                errors.append(dict(subject=ep.ticker, error=str(exc)))
    night = night_trace(proof, captures)
    p.write(output / 'night-futures-e2e-trace.json', night)
    after = source_db_identity(p.OPERATING / 'data/thesis_monitor.sqlite3')
    isolation = dict(status='PASS' if before == after else 'FAIL', production_db_before=before,
        production_db_after=after, production_db_unchanged=before == after, production_send=0,
        production_recipient_intent=0, production_decision_writes=0, production_warning_writes=0,
        scheduler_changes=0, notification_changes=0, broker_actions=0)
    p.write(output / 'production-isolation.json', isolation)
    p.write(output / 'message-quality-audit.json', dict(status='PASS' if not errors and len(captures) == 24 else 'FAIL',
        rows=audit, errors=errors, accepted_messages=len(captures), expected_messages=24,
        human_review='PENDING', production_owners=['render_accepted_v2_production', 'render_daily_digest'],
        post_capture_text_edits=0))
    p.write(output / 'capture-sink-trace.json', {k: {f: v for f, v in r.items() if f not in ('prepared_text', 'chunks')}
                                               for k, r in captures.items()})
    (output / 'ALL_MESSAGES.md').write_text('\n\n'.join('# ' + name + '\n\n' + row['prepared_text']
                                                       for name, row in captures.items()))
    p.write(output / 'manifest.json', dict(generation_id=proof.gen, source_generation_id=proof.source_gen,
        messages=[dict(path=name, sha256=row['prepared_text_sha256']) for name, row in captures.items()]))


def night_trace(proof, captures):
    source = proof.root.parent
    canonical = p.read(source / 'source/night-provider.json')['observations']
    raw = p.read(source / 'source/night-raw-row-index.json')
    context = proof.MARKET_OWNER.market_context(proof.packets['us']) if hasattr(proof,'MARKET_OWNER') else market_context(proof.packets['us'])
    output = render_us_full_market_message(proof.packets['us']['market_context'])
    records = []
    for fact in canonical:
        meta = fact['raw_payload']
        row = next(r for r in proof.packets['us']['market_context']['night_futures'] if r['series_code'] == fact['series_code'])
        selected = _night_timeframe_block(row, series=fact['series_code'])
        ref = row['fact_id']
        matches = [r for r in raw if r['row_identity'] == meta['night_source_record_id']
                   and r['response_sha256'] == meta['night_source_payload_sha256']]
        captured = captures.get('MARKET_US.txt', {}).get('prepared_text', '')
        exact = selected[0] if selected else ''
        passed = bool(len(matches) == 1 and ref in context['facts'] and selected
            and set(selected[1]) <= set(output.night_fact_ids) and exact in captured
            and selected[0] not in captures.get('MARKET_KR.txt', {}).get('prepared_text', '')
            and context['facts'][ref]['night_timeframes'] == row['night_timeframes'])
        numeric_claims = [c for c in (context.get('numeric_catalog') or {}).get('claims',[]) if c['claim_type']=='OFFICIAL_NIGHT'
                          and c['metadata']['row_sha256']==digest(row)]
        if context.get('numeric_catalog'):
            passed = passed and len(numeric_claims)==1 and numeric_claims[0]['rendered_text'] in captured
        records.append(dict(status='PASS' if passed else 'FAIL', product=meta['product'],
            raw_rows=matches, raw_owner='probe_krx_night_futures', canonical=fact,
            canonical_sha256=digest(fact), serialized=row, serialized_sha256=digest(row),
            adapter=context['facts'].get(ref), model_input_sha256=digest(context),
            accepted_market_output_sha256=digest(proof.markets['us']),
            model_consumption_mode='AVAILABLE_TO_ACCEPTED_MARKET_CONTEXT',
            renderer_owner='render_typed_market_facts' if context.get('numeric_catalog') else 'render_us_full_market_message',
            typed_numeric_claims=numeric_claims, exact_captured_substring=exact if exact in captured else None,
            prepared_sha256=captures.get('MARKET_US.txt', {}).get('prepared_text_sha256')))
    return dict(status='PASS' if len(records) == 2 and all(r['status'] == 'PASS' for r in records) else 'FAIL', products=records)


def capture(proof):
    asyncio.run(capture_all(proof))
