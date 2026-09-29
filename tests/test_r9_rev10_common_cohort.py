import json
from pathlib import Path

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fresh_publication_replay import replay_fresh_publications
from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from app.services.unified_sealed_context import replay_night
from app.services.unified_source_composition import _resolve
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from scripts.r2b_r9_full_fresh_requalification import fresh_authority_inputs, prepare_fresh_subject
from scripts.r9_phase_a_gate import root_gate, code_fingerprints
from tests.rev10_cohort_fixtures import stocks, markets, night, START, QUERY, RUN, POLICY_ALL
from tests.rev10_stage_fixtures import synthetic_outputs
from tests.test_r9_rev8_fresh_publications import publication_sources
from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry


def common_cohort(root):
    inputs, market = stocks(root / 'stocks'), markets(root / 'markets')
    publications = publication_sources(START, RUN, as_of=QUERY)
    publications['policy'] = POLICY_ALL
    night_inputs = night(root / 'night-history')
    pub, night_value = replay_fresh_publications(**publications), replay_night(**night_inputs)
    rows = {t: assemble_fresh_stock(**i) for t, i in inputs.items()}
    native = {}
    for m, arg in market.items():
        n = arg['native_aggregate']
        native[m] = dict(run_id=RUN, attempt_id=n['attempt_id'], attempt_started_at=START.isoformat(),
                         cutoff=n['cutoff'].isoformat(), component=_resolve(**n))
    versions = {f'class-c/local-{m}.json': sha256_bytes(encoded(inputs[ts[0]]['technical_inputs']['local_seed']) + b'\n')
                for m, ts in UNIVERSE.items()}
    repo = Path(__file__).resolve().parents[1]
    inventory = json.loads((repo / 'docs/operations/UNIFIED_ACQUISITION_CLASSES.json').read_bytes())
    registry = WholeSourceCodeOwnerRegistry.freeze(repo)
    denials = dict(kr_market_investor_flows=dict(status='OPTIONAL_UNAVAILABLE', value=None,
        denial='SYNTHETIC_NOT_SELECTED', run_id=RUN))
    bridge = rows['SKHY']['issuer_business_bridge']
    persisted = {t: r['event_view']['receipt'] for t, r in rows.items()
                 if r.get('event_view', {}).get('receipt', {}).get('acquisition_class') == 'PERSISTED_SOURCE_RECHECK'}
    plan = inputs['CORZ']['technical_inputs']['plan']
    binding = {t: digest(dict(technical_plan=plan.model_dump(mode='json'), financial_plan=i['financial_inputs']['plan']))
               for t, i in inputs.items()}
    seed = FreshFullSourceRunSeed(proof_mode='AD_HOC_LIVE_SOURCE_PROOF',
        packet_scope='LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION', parent_run_id=RUN, started_at=START,
        source_policy_sha256=digest(sorted(POLICY_ALL.allowed_providers)), inventory_sha256=digest(inventory),
        **registry.seed_bindings, universe_sha256=digest(UNIVERSE),
        attempts={m: n['attempt_id'] for m, n in native.items()}, attempt_hashes={m: digest(n) for m, n in native.items()},
        run_acquisitions=dict(stock=digest(plan.model_dump(mode='json')), publications=digest(pub), night=night_value['value_sha256']),
        class_c_version_set_sha256=digest(versions), stock_cohort_hashes={m: digest({t: rows[t] for t in ts}) for m, ts in UNIVERSE.items()},
        night_publication_receipt_sha256=digest(dict(probe=night_value['original_receipts'], history=[])),
        optional_denial_set_sha256=digest(denials), skhy_issuer_bridge_sha256=digest(bridge),
        persisted_event_evidence_sha256=digest(persisted),
        fresh_stock_owner_set_sha256=digest(binding))
    args = dict(seed=seed, market_inputs=market, stock_inputs={t: dict(fresh_financial_binding=i) for t, i in inputs.items()},
        authority_inputs={t: fresh_authority_inputs(rows[t], i) for t, i in inputs.items()}, version_set=versions,
        optional_denials=denials, issuer_bridge=bridge, composition_metadata=dict(inventory=inventory,
            allowed_providers=sorted(POLICY_ALL.allowed_providers), code_fingerprints=registry.fingerprints,
            code_owner_registry=registry.model_dump(mode="json")),
        fresh_context_inputs=dict(publications=publications, night=night_inputs))
    return args, inputs


def test_all22_common_generation_whole_source_replay_and_stages(tmp_path):
    args, inputs = common_cohort(tmp_path)
    first = compose_full_source(**args)
    stock_outputs, market_outputs = {}, {}
    from scripts.r2b_r5_market_adapter import project_sealed_market_context
    from scripts import r2b_r2_preflight as pre
    from scripts import m12ds_r4_r4_market as owner
    for market in ('us', 'kr'):
        projected = project_sealed_market_context(first['packets'][market], first['seed'], first['authority_graph'],
                                                  expected_authority_sha256=first['authority_graph_sha256'])
        raw = pre.synthetic_shape_probe(owner.market_schema(projected['context']))
        market_outputs[market] = raw
    for t, i in inputs.items():
        result = prepare_fresh_subject(i, execution_generation_id=RUN)
        raw = synthetic_outputs(result, RUN, i['technical_inputs']['local_seed'])
        stock_outputs[t] = raw
    proof = dict(whole_source_inputs=args, stock_outputs=stock_outputs, market_outputs=market_outputs,
                 code_fingerprints=code_fingerprints())
    receipt, artifacts = root_gate(proof)
    from app.services.unified_run_artifacts import durable_json
    durable_json(tmp_path / 'phase-a-gate.json', receipt, exclusive=True)
    assert receipt['status'] == 'PASS', (receipt['blockers'], receipt['errors'])
    assert receipt['dispatch_allowed'] is True
    assert len(artifacts['stock_stages']) == 22
    assert len(artifacts['market_stages']) == 2
