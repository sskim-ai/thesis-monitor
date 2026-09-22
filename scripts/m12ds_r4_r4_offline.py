"""Recorded facts-only regression; never substitute these diagnostics for fresh proof."""
import argparse
from pathlib import Path

from app.services.market_numeric_claim_service import final_market_numeric_audit, render_typed_market_facts
from scripts.m12dr_offline_source_closure import read, write, sha
from scripts.m12ds_r4_r3_offline import run as foreign_audit
from scripts.m12ds_r4_r4_market import market_context, numeric_boundary


def run(baseline, source_audit, market_baseline, output):
    foreign_audit(baseline,source_audit,output)
    rows=[]
    for market in ('us','kr'):
        path=market_baseline/'snapshot'/f'{market}-packet.json'
        packet=read(path)
        context=market_context(packet)
        catalog=context['numeric_catalog']
        check=numeric_boundary(context,packet['market_context'])
        text=render_typed_market_facts(catalog,packet['market_context'])+'\n\n정성 해석'
        audit=final_market_numeric_audit(text,catalog,packet['market_context'],'정성 해석')
        row=dict(market=market,status='PASS' if check['status']==audit['status']=='PASS' else 'FAIL',
                 source_sha256=sha(path),catalog=catalog,numeric_audit=audit,
                 historical_facts_only=True,model_output_used=False,accepted_capture=False)
        write(output/f'{market}-numeric-recorded-facts.json',row)
        rows.append(row)
    receipt=read(output/'receipt.json')
    receipt['market_numeric_recorded_facts']={r['market']:r['status'] for r in rows}
    foreign=read(output/'recorded-foreign-route.json')
    selected=[c['current']['lineage']['occurrence'] for c in foreign['comparative_observations']]
    write(output/'foreign-boundary-document-class.json',dict(
        boundaries=[r['statement_boundary'] for r in selected],
        document_classes=[r.get('document_evidence_class') for r in selected],
        authoritative_prior=foreign['prior_version_authority']))
    if not all(r['status']=='PASS' for r in rows):
        receipt['status']='FAIL'
    write(output/'receipt.json',receipt)
    print('R4-R4 recorded facts-only closure: '+receipt['status'],flush=True)
    if receipt['status']!='PASS':
        raise ValueError('recorded_facts_closure_failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('baseline','source-audit','market-baseline','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    run(args.baseline,args.source_audit,args.market_baseline,args.output)
