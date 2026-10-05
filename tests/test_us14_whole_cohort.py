from copy import deepcopy
from pathlib import Path

import pytest

from app.services.auxiliary_issuer_financial_owner import AuxiliaryIssuerDependency
from app.services.bounded_financial_stock_owner import replay_issuer_source
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fresh_publication_replay import replay_fresh_publications
from app.services.unified_full_source_cohort import FreshUSSourceRunSeed, compose_full_source, auxiliary_issuer_binding
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE
from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
from scripts.r2b_r9_full_fresh_requalification import fresh_authority_inputs, prepare_fresh_subject
from scripts.r9_offline_stage_replay import replay_stages, replay_market
from scripts.r2b_r5_market_adapter import project_sealed_market_context
from scripts import r2b_r2_preflight as pre
from scripts import m12ds_r4_r4_market as market_owner
from tests.test_r9_rev10_common_cohort import common_cohort
from tests.rev10_stage_fixtures import synthetic_outputs


def us_cohort(root):
    args, all_inputs = common_cohort(root)
    inputs = {t: i for t, i in all_inputs.items() if t in UNIVERSE['us']}
    raw = inputs['CORZ']['technical_inputs']['plan'].model_dump(mode='json')
    raw.update(contract='one-shot-us14-source-acquisition-v1', reads=[r for r in raw['reads'] if r['market'] == 'us'])
    plan = StockPlan.model_validate(raw)
    plan_hash = digest(plan.model_dump(mode='json'))
    for i in inputs.values():
        tech = i['technical_inputs']
        tech['plan'] = plan
        for r in tech['receipts'].values():
            r['plan_sha256'] = plan_hash
        tech['expected_hashes'].update(plan=plan_hash, receipts=digest(tech['receipts']))
        from app.services.completed_price_state import bind_source
        # Narrowing the stock plan changes the numeric owner's plan binding.
        i['technical_inputs'] = bind_source(tech, source=tech['completed_price_source'], artifacts={},
            security=i['financial_inputs']['plan']['security'])
    target = inputs['SKHY']['financial_inputs']
    bridge = target['issuer_business']
    source = bridge['source_inputs']
    source = {k: v for k, v in source.items() if k not in {'baseline', 'local_seed'}}
    source['dependency'] = AuxiliaryIssuerDependency(run_id=plan.run_id, cutoff=plan.frozen_at,
        source_plan_sha256=digest(source['plan']), official_identity_sha256=digest(bridge['official_identity'])).model_dump(mode='json')
    bridge.update(source_inputs=source, source_result_sha256=digest(replay_issuer_source(source, target_plan=target['plan'])))
    stocks = {t: assemble_fresh_stock(**i) for t, i in inputs.items()}
    args['stock_inputs'] = {t: dict(fresh_financial_binding=i) for t, i in inputs.items()}
    args['authority_inputs'] = {t: fresh_authority_inputs(stocks[t], i) for t, i in inputs.items()}
    args['market_inputs'] = {'us': args['market_inputs']['us']}
    args['version_set'] = {k: v for k, v in args['version_set'].items() if k.endswith('local-us.json')}
    args['optional_denials'] = {}
    args['issuer_bridge'] = stocks['SKHY']['issuer_business_bridge']
    publications = args['fresh_context_inputs']['publications']
    publications['market_scope'] = 'US14_ONLY'
    registry = WholeSourceCodeOwnerRegistry.freeze(Path(__file__).resolve().parents[1], profile='fresh_us14')
    args['composition_metadata'].update(code_owner_registry=registry.model_dump(mode='json'), code_fingerprints=registry.fingerprints)
    seed = args['seed'].model_dump(mode='json')
    seed.update(**registry.seed_bindings, universe_sha256=digest({'us': UNIVERSE['us']}),
        attempts={'us': seed['attempts']['us']}, attempt_hashes={'us': seed['attempt_hashes']['us']},
        run_acquisitions={**seed['run_acquisitions'], 'stock': plan_hash, 'publications': digest(replay_fresh_publications(**publications))},
        class_c_version_set_sha256=digest(args['version_set']), stock_cohort_hashes={'us': digest(stocks)},
        optional_denial_set_sha256=digest({}), skhy_issuer_bridge_sha256=digest(args['issuer_bridge']),
        fresh_stock_owner_set_sha256=digest({t: digest(dict(technical_plan=plan.model_dump(mode='json'),
            financial_plan=i['financial_inputs']['plan'])) for t, i in inputs.items()}),
        auxiliary_issuer_set_sha256=digest(auxiliary_issuer_binding(args['stock_inputs'])))
    args['seed'] = FreshUSSourceRunSeed(**seed)
    return args, inputs


def test_us14_seed_whole_source_and_real_fifteen_message_offline_capture(tmp_path):
    args, inputs = us_cohort(tmp_path)
    first = compose_full_source(**args)
    second = compose_full_source(**args)
    assert digest(first) == digest(second)
    assert set(first['packets']) == {'us'}
    assert set(first['authority_graph']['auxiliary_issuers']) == {'000660'}
    assert first['seed']['scope'] == 'US14_ONLY'
    from scripts.fresh_source_only_export import project_us14_cohort, project_cohort
    exported = project_us14_cohort(first, generation_id=args['seed'].parent_run_id, whole_source_sha256=digest(first))
    assert exported['audit']['stock_count'] == 14 and exported['audit']['market_count'] == 1
    with pytest.raises(ValueError, match='whole_identity'):
        project_cohort(first, generation_id=args['seed'].parent_run_id, whole_source_sha256=digest(first))
    captures = {}
    projected = project_sealed_market_context(first['packets']['us'], first['seed'], first['authority_graph'],
        expected_authority_sha256=first['authority_graph_sha256'])
    raw = pre.synthetic_shape_probe(market_owner.market_schema(projected['context']))
    captures['MARKET_US'] = replay_market(first, 'us', raw)['capture']
    for ticker, i in inputs.items():
        result = prepare_fresh_subject(i, execution_generation_id=args['seed'].parent_run_id)
        outputs = synthetic_outputs(result, args['seed'].parent_run_id, i['technical_inputs']['local_seed'])
        proof = replay_stages(result, args['seed'].parent_run_id, outputs)
        assert proof['status'] == 'PASS'
        captures[ticker] = proof['capture']
    assert len(captures) == 15 and '000660' not in captures and 'MARKET_KR' not in captures
    assert all(r['production_sends'] == r['network_requests'] == 0 for r in captures.values())
    for mutation in ('aux', 'primary', 'plan'):
        bad = deepcopy(args)
        if mutation == 'aux':
            bad['seed'] = bad['seed'].model_copy(update={'auxiliary_issuer_set_sha256': '0'*64})
        elif mutation == 'primary':
            bad['stock_inputs']['000660'] = bad['stock_inputs']['SKHY']
        else:
            bad['stock_inputs']['SKHY']['fresh_financial_binding']['technical_inputs']['plan'] = (
                bad['stock_inputs']['SKHY']['fresh_financial_binding']['technical_inputs']['plan'].model_copy(
                    update={'contract': 'one-shot-stock-source-acquisition-v1'}))
        with pytest.raises(ValueError, match='us14_'):
            compose_full_source(**bad)
