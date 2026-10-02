"""Archive-only production renderer capture from newly accepted R5 outputs."""
import asyncio
from unittest.mock import patch

from sqlmodel import Session

from app.services.accepted_calibration_message_service import AcceptedMarketCalibration, digest
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.daily_digest_renderer import render_daily_digest
from scripts.m12ds_r4_r1_accepted_capture import stock_plan, numeric_audit
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts import r2b_r2_contract as c
from scripts import m12ds_r4_r4_market as market_owner
from scripts import m12dr_fresh_blind_reproof as p
from scripts.sealed_cohort_offline_proof import network_guard


async def _capture(proof):
    output=proof.root/'messages'
    p.require(not output.exists(),'new_capture_required')
    output.mkdir()
    rows=[]
    proof.packets={m:{'stocks':[d['view']['packet']['stocks'][0] for d in proof.prepared.values()
                               if d['view']['market']==m]} for m in ('us','kr')}

    async def emit(name,text,payload_type,market):
        receipt=await capture_payload(dict(text=text,use_llm=False,type=payload_type,market=market))
        (output/(name+'.txt')).write_text(receipt['prepared_text'])
        p.write(output/'receipts'/(name+'.json'),receipt)
        rows.append(dict(path=name+'.txt',sha256=receipt['prepared_text_sha256'],
                         chunk_count=len(receipt['chunks']),production_sends=0))

    for m in ('us','kr'):
        data=proof.projected[m]
        source=data['packet']['market_context']
        context=market_owner.market_context(data['packet'])
        decision=proof.markets[m]
        p.require(market_owner.validate_market(decision,context)['status']=='PASS','market_revalidation_failed')
        receipt=dict(status='PASS',errors=[],market=m,assessment_date=data['packet']['assessment_date'],
            source_context_sha256=digest(source),decision_sha256=digest(decision),
            numeric_catalog_sha256=digest(context['numeric_catalog']))
        plan=AcceptedMarketCalibration(market=m,assessment_date=data['packet']['assessment_date'],source_context=source,
            decision=decision,acceptance=receipt,acceptance_sha256=digest(receipt),numeric_catalog=context['numeric_catalog'])
        await emit('MARKET_'+m.upper(),render_daily_digest(None,accepted_market=plan),'daily_digest',m)
        p.write(output/'bindings'/('market-'+m+'.json'),plan.model_dump(mode='json'))
    for t,d in proof.prepared.items():
        m=d['view']['market']
        if d['mode']=='UNKNOWN_LIMIT':
            text=c.render_unknown(t,proof.limits['pass-b'][t],recovery=d['recovery'],
                                  capability={k:[] for k in c.DIRECTION_BUCKETS})
        else:
            ep=DecisionEvidencePacket.model_validate(d['view']['evidence_packet'])
            plan=stock_plan(proof,t,ep)
            errors=numeric_audit([plan.decision[k] for k in ('overall_reason','new_buyer_reason','holder_reason')],
                                d['view']['packet']['stocks'][0],t)
            p.require(not errors,'stock_numeric_binding:'+','.join(errors))
            rendered=render_accepted_v2_production(ep,plan)
            p.require(rendered.validation.valid,'stock_renderer_validation')
            text=rendered.text
            p.write(output/'bindings'/(t+'.json'),plan.model_dump(mode='json'))
        await emit(m+'-'+t,text,'stock_review',m)
    p.require(len(rows)==24,'message_count_incomplete')
    p.write(output/'manifest.json',dict(generation_id=proof.gen,messages=rows,total=24,
        unknown_limit_mode_preserved=True,production_sends=0,recipient_intents=0))


def capture(proof):
    proof.verify()
    network_guard()
    def deny(*args,**kwargs):
        raise AssertionError('capture_db_access_forbidden')
    with patch.object(Session,'exec',deny),patch.object(Session,'commit',deny):
        asyncio.run(_capture(proof))
