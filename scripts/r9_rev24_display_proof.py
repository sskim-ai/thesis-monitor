"""Offline exact-request and deterministic capture proof from a sealed fixture."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from app.services.market_display_plan import MarketDisplayPlan
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from scripts.r2b_r5_market_adapter import project_sealed_market_context
from scripts.r9_rev11_market_qualification import qualify_markets
from scripts.r9_rev11_models import FreshExecution
from scripts.r9_offline_stage_replay import replay_market
from scripts.sealed_cohort_offline_proof import network_guard
from scripts import r2b_r2_preflight as pre
from scripts import m12ds_r4_r4_market as owner


def run(fixture, output):
    network_guard()
    def read(path):
        return json.loads(path.read_bytes())
    manifest = read(fixture/'fixture-manifest.json')
    for name, row in manifest.items():
        raw = (fixture/name).read_bytes()
        assert sha256_bytes(raw) == row['sha256'] and len(raw) == row['bytes']
    whole = read(fixture/'market-inputs.json')
    coverage = qualify_markets(whole)
    rows = {}
    for market in ('us','kr'):
        old = read(fixture/(market+'-before.json'))
        projected = project_sealed_market_context(whole['packets'][market],whole['seed'],whole['authority_graph'],
            expected_authority_sha256=whole['authority_graph_sha256'])
        assert projected['context'] == old['context'] and projected['schema'] == old['schema']
        assert projected['packet'] == old['packet']
        assert coverage[market]['status'] == 'PASS'
        worker = SimpleNamespace(requests=output/'requests', gen='rev24-offline-probe',
                                 source_gen=whole['seed']['parent_run_id'])
        request = FreshExecution.capture(worker, 'market', dict(market=market,batch=1,subjects=[]),
            projected['context'],projected['schema'],owner.PROMPT)
        request_dir = Path(request['directory'])
        assert read(request_dir/'subject-context.json') == old['context']
        prompt = (request_dir/'prompt.txt').read_text()
        assert prompt == owner.PROMPT+'\nFROZEN_CONTEXT:\n'+json.dumps(old['context'],ensure_ascii=False,sort_keys=True)+'\n'
        synthetic = pre.synthetic_shape_probe(owner.market_schema(projected['context']))
        replay = replay_market(whole,market,synthetic)
        assert replay['status'] == 'PASS' and replay['capture']['production_sends'] == 0
        plan = MarketDisplayPlan.model_validate(replay['accepted']['display_plan'])
        selected = [dict(block=i.block_id,label=i.label,refs=list(i.fact_ids),status=i.status,
                         dates=list(i.observation_dates)) for i in plan.items]
        # The accepted renderer already audits exact text. Also assert period
        # labels survive the final sender-boundary normalization.
        for item in plan.items:
            if item.status == 'AVAILABLE' and item.block_id in {'macro','fx'}:
                assert all(d+' 관측' in replay['capture']['prepared_text'] for d in item.observation_dates)
        rows[market] = dict(status='PASS',directional_context_byte_equivalent=True,
            source_packet_unchanged=True,request_receipt=request,views=projected['views'],
            display_plan=plan.model_dump(mode='json'),selected=selected,
            sender_sha256=replay['capture']['prepared_text_sha256'],
            synthetic_only=True,source_generation=whole['seed']['parent_run_id'])
        durable_json(output/(market+'-proof.json'),rows[market],exclusive=True)
        durable_json(output/(market+'-capture.json'),replay['capture'],exclusive=True)
    result = dict(status='PASS',market_count=2,coverage=coverage,
        directional_input_sha256={m:r['views']['receipt']['directional_context_sha256'] for m,r in rows.items()},
        providers=0,models=0,delivery=0,historical_regression_only=True,
        fixture_manifest_sha256=digest(manifest))
    durable_json(output/'market-display-proof.json',result,exclusive=True)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(run(args.fixture,args.output)['status'],flush=True)


if __name__=='__main__':
    main()
