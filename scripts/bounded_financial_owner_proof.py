"""Explicit offline baseline / freeze / one-shot acquisition / offline replay CLI."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import shutil
import socket
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings
from app.services.bounded_financial_acquisition import (
    BoundedReader, AcquisitionDenied, SystemicStop, RETAINED, collect, make_plan,
)
from app.services.bounded_financial_stock_owner import assemble, validate
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.unified_event_union_proof import git, snapshot, prove as event_prove

BASE = '35fe0ce35160bb5199f2c8db00c927ff78ea9c0a'


def read(root, name):
    return json.loads((root / name).read_bytes())


def save(root, name, value):
    durable_json(root / name, value, exclusive=True)


def offline():
    def deny(*args, **kwargs):
        raise RuntimeError('financial_proof_network_forbidden')
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = deny


def baseline(args, root):
    offline()
    for name in ('event-plan.json', 'business-cutoff.json', 'security-records.json'):
        durable_bytes(args.output / name, (args.r4 / name).read_bytes(), exclusive=True)
    for name in ('class-c', 'acquisition'):
        shutil.copytree(args.r4 / name, args.output / name)
    event_prove(SimpleNamespace(output=args.output, corpus=args.corpus, r1_bundle=args.r1_bundle,
                               proof_tag='proof-before'), root)
    matrix = read(args.output, 'proof-before/22-subject-matrix.json')
    checks = {r['ticker']: read(args.output, 'proof-before/assembled/' + r['ticker'] + '.json') ==
              read(args.r4, 'proof-final/assembled/' + r['ticker'] + '.json') for r in matrix}
    if not all(checks.values()):
        raise ValueError('baseline_replay_changed')
    save(args.output, 'offline-baseline-proof.json', {'status':'PASS', 'subjects':checks, 'network_calls':0})


def freeze(args, root):
    offline()
    if git(root, 'status', '--porcelain'):
        raise ValueError('clean_implementation_commit_required')
    validation = read(args.output, 'pre-network-validation.json')
    if validation['head'] != git(root, 'rev-parse', 'HEAD') or any(v['returncode'] for v in validation['commands'].values()):
        raise ValueError('exact_sha_full_validation_required')
    if not validation['skip_xfail_identity_unchanged'] or read(args.output, 'offline-baseline-proof.json')['status'] != 'PASS':
        raise ValueError('offline_gate_failed')
    ids = {r['ticker']:r for r in read(args.r4, 'security-records.json')}
    now = datetime.now(ZoneInfo('Asia/Seoul'))
    run = 'r5-rev2-' + now.strftime('%Y%m%dT%H%M%S%z')
    entries = [make_plan(ids[t], market=m, cutoff=now, run_id=run) for m, ts in UNIVERSE.items() for t in ts if t not in RETAINED]
    if len(entries) != 19 or Counter(r['market'] for r in entries) != {'us':13,'kr':6}:
        raise ValueError('exact_blocked_cohort_required')
    state = snapshot(root, args.operating)
    plan = {'run_id':run, 'cutoff':now.isoformat(), 'base':BASE, 'code_sha':state['head'],
        'instruction_sha':'2e1f77acb4daa96957231f211d4dbce4b1d4c28c',
        'config_fingerprint':state['config'], 'entries':entries,
        'retained_without_recollection':sorted(RETAINED), 'side_effect_policy':'SOURCE_ONLY_PRIVATE_STAGING',
        'budgets': {provider:{'subjects':sum(e['provider']==provider for e in entries),
            'planned_logical_requests':sum(e['planned_logical_requests'] for e in entries if e['provider']==provider),
            'theoretical_max_logical':sum(e['maximum_logical_requests'] for e in entries if e['provider']==provider),
            'theoretical_max_attempts':sum(e['maximum_HTTP_attempts'] for e in entries if e['provider']==provider),
            'planned_pagination':sum(e['limits']['discovery'] for e in entries if e['provider']==provider),
            'maximum_pagination':sum(e['limits']['discovery'] for e in entries if e['provider']==provider),
            'planned_documents':0,
            'maximum_documents':sum((e['limits']['current']+e['limits']['prior'])*e['limits']['documents_per_filing'] for e in entries if e['provider']==provider),
            'planned_retries':0} for provider in ('sec_edgar','opendart')},
        'Alpha_calls':0, 'model_calls':0, 'news_calls':0, 'OHLCV_calls':0}
    save(args.output, 'financial-acquisition-plan.json', plan)
    raw_sha = sha256_bytes((args.output/'financial-acquisition-plan.json').read_bytes())
    durable_bytes(args.output/'financial-acquisition-plan.json.sha256', (raw_sha+'  financial-acquisition-plan.json\n').encode(), exclusive=True)
    save(args.output, 'pre-network-gate.json', {'status':'PASS','plan_sha256':raw_sha,'code_sha':state['head'],
        'validation_sha256':sha256_bytes((args.output/'pre-network-validation.json').read_bytes()),
        'maximum_logical_requests':sum(e['maximum_logical_requests'] for e in entries),
        'maximum_attempts':sum(e['maximum_HTTP_attempts'] for e in entries)})
    print(json.dumps(plan['budgets']), flush=True)


async def acquire(args, root):
    plan = read(args.output, 'financial-acquisition-plan.json')
    gate = read(args.output, 'pre-network-gate.json')
    if gate['plan_sha256'] != sha256_bytes((args.output/'financial-acquisition-plan.json').read_bytes()):
        raise ValueError('plan_drift')
    if git(root, 'status', '--porcelain') or git(root,'rev-parse','HEAD') != plan['code_sha']:
        raise ValueError('code_drift')
    settings = Settings(_env_file=args.operating / '.env')
    if not settings.opendart_api_key or not settings.sec_user_agent:
        raise ValueError('existing_provider_configuration_missing')
    if snapshot(root,args.operating)['config'] != plan['config_fingerprint']:
        raise ValueError('config_drift')
    save(args.output, 'financial-dispatch-once.json', {'plan_sha256':gate['plan_sha256'], 'started':datetime.now(ZoneInfo('Asia/Seoul')).isoformat()})
    rows, stopped = [], None
    def guard():
        if git(root,'rev-parse','HEAD')!=plan['code_sha'] or git(root,'status','--porcelain'):
            raise SystemicStop('code_drift')
        from scripts.unified_stock_source_plan import state as source_state
        if source_state(root,args.operating)['config'] != plan['config_fingerprint']:
            raise SystemicStop('configuration_drift')
    for entry in plan['entries']:
        directory = args.output / 'financial-acquisition' / entry['ticker']
        reader = BoundedReader(entry, directory, api_key=settings.opendart_api_key if entry['provider']=='opendart' else None,
                               user_agent=settings.sec_user_agent if entry['provider']=='sec_edgar' else None,guard=guard)
        state = {'ticker':entry['ticker'],'provider':entry['provider'],'status':'NOT_ATTEMPTED','reason':stopped}
        try:
            if stopped:
                save(directory, 'result.json', state)
                rows.append(state)
                continue
            output = await collect(reader)
            state.update(status='CAP_EXHAUSTED' if output['denials'] else 'ACQUIRED', output=output)
        except SystemicStop as exc:
            stopped = str(exc)
            state.update(status='SYSTEMIC_STOP',reason=stopped)
        except (AcquisitionDenied, ValueError, KeyError, TypeError, httpx.HTTPError) as exc:
            state.update(status='DENIED',reason=str(exc) if isinstance(exc, AcquisitionDenied) else type(exc).__name__)
        finally:
            if 'output' not in state and hasattr(reader, 'output_state'):
                state['output'] = reader.output_state
                state['output']['denials'].append(state.get('reason') or 'ACQUISITION_INCOMPLETE')
            state.update(logical_requests=reader.logical, HTTP_attempts=reader.attempts,
                retries=reader.attempts-reader.logical, stage_counts=reader.stage_counts)
            if state['status'] != 'NOT_ATTEMPTED':
                save(directory,'receipts.json',reader.receipts)
                save(directory,'result.json',state)
                rows.append(state)
                print(entry['ticker'],state['status'],reader.logical,reader.attempts,state.get('reason'),flush=True)
    save(args.output,'financial-acquisition-results.json',{'rows':rows,'systemic_stop':stopped,
        'finished':datetime.now(ZoneInfo('Asia/Seoul')).isoformat()})


def prove(args, root):
    offline()
    plan = read(args.output,'financial-acquisition-plan.json')
    entries = {e['ticker']:e for e in plan['entries']}
    matrix = []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            old = read(args.output,'proof-before/assembled/'+ticker+'.json')
            if ticker in RETAINED:
                result, row = old, {'ticker':ticker,'market':market,'status':old['status'],'retained_exact':True,
                    'packet_sha256':old['packet_sha256'],'direction_eligible':'RETAINED_ORIGINAL_AUTHORITY'}
            else:
                directory = args.output/'financial-acquisition'/ticker
                acquisition = read(directory,'result.json')
                row = {'ticker':ticker,'market':market,'acquisition_status':acquisition['status'], 'acquisition_reason':acquisition.get('reason')}
                try:
                    if not acquisition.get('output'):
                        raise ValueError('NO_ACQUIRED_DOCUMENTS')
                    inputs = dict(baseline=old,plan=entries[ticker],acquisition=acquisition['output'],directory=directory,
                        receipts=read(directory,'receipts.json'),local_seed=read(args.output,'class-c/local-'+market+'.json'))
                    result = assemble(**inputs)
                    validate(result, **inputs)
                    row.update({k:result[k] for k in ('status','packet_sha256','mandatory_missing','observed_business_cardinality','acquisition_denials','comparison_denials')})
                    row.update(context_eligible=result['projection']['context_eligible'],
                               direction_eligible=result['projection']['direction_eligible'], comparative_refs=result['comparative_fact_refs'])
                except (ValueError,KeyError,TypeError) as exc:
                    result = {'ticker':ticker,'status':'BLOCKED','reason':type(exc).__name__+':'+str(exc)}
                    row.update(status='BLOCKED',exact_blocker=result['reason'],packet_sha256=None,direction_eligible=False)
            save(args.output,'proof-final/assembled/'+ticker+'.json',result)
            matrix.append(row)
            print(ticker,row['status'],row.get('direction_eligible'),flush=True)
    save(args.output,'proof-final/22-subject-matrix.json',matrix)
    save(args.output,'proof-final/offline-replay-receipt.json',{'network_calls':0,'controls_exact':True,'subjects':len(matrix),
        'model_calls':0,'rendered_messages':0,'Telegram':0,'production_DB_writes':0,'scheduler_mutation':0})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['baseline','freeze','acquire','prove'])
    for key in ('output','r4','corpus','r1-bundle','operating'):
        p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if args.mode=='acquire':
        asyncio.run(acquire(args,root))
    else:
        {'baseline':baseline,'freeze':freeze,'prove':prove}[args.mode](args,root)


if __name__=='__main__':
    main()
