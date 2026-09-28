"""Receipt derived from raw-source and post-model replay, never a PASS flag."""
from pathlib import Path
import json

from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_run_artifacts import sha256_bytes
from scripts.r9_offline_stage_replay import replay_stages, replay_market

GATES = ('event_archetype_gate', 'denied_quality_gate', 'valuation_matrix_gate',
         'aggregate_whole_source_gate', 'replay_twice_gate', 'Market2_gate', 'Core22_gate',
         'A22_gate', 'B22_gate', 'exact24_gate')


def code_fingerprints():
    root = Path(__file__).resolve().parents[1]
    # Include transitive owners and policy/schema code, not only the controller.
    return {str(p.relative_to(root)): sha256_bytes(p.read_bytes())
            for directory in ('app', 'scripts') for p in sorted((root / directory).rglob('*.py'))}


def root_gate(proof=None):
    states = {key: dict(status='NOT_PROVEN', reasons=['RAW_REPLAY_INPUTS_NOT_SUPPLIED']) for key in GATES}
    artifacts, errors = {}, []
    code = code_fingerprints()
    if proof is not None:
        if not isinstance(proof, dict) or set(proof) != {'whole_source_inputs', 'stock_outputs', 'market_outputs', 'code_fingerprints'}:
            raise ValueError('phase_a_exact_replay_inputs_required_not_status_receipt')
        if proof['code_fingerprints'] != code:
            raise ValueError('phase_a_current_code_policy_schema_drift')
        args = {**proof['whole_source_inputs'], 'market_inputs': {
            m: dict(v) for m, v in proof['whole_source_inputs']['market_inputs'].items()}}
        if not isinstance(args['seed'], FreshFullSourceRunSeed):
            raise ValueError('phase_a_fresh_source_seed_required')
        expected = {t for ts in UNIVERSE.values() for t in ts}
        if set(proof['stock_outputs']) != expected or set(proof['market_outputs']) != {'us', 'kr'}:
            raise ValueError('phase_a_exact_whole_cohort_outputs_required')
        # Only registered owner factories may interpret market raw evidence.
        # Do not run a callback supplied in an arbitrary Python proof object.
        from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
        for m, source in args['market_inputs'].items():
            native = source['native_aggregate']
            role = native['role']
            if m == 'us':
                from app.config import get_settings
                owner = us_market_aggregate_owner(role=role,
                    source_url=get_settings().ohlcv_base_url.rstrip('/') + '/ohlcv', policy=native['policy'])
            else:
                from app.services.unified_kiwoom_observer import KiwoomRead
                reads = [KiwoomRead.model_validate(r) for r in json.loads(
                    (native['root'] / 'plan.json').read_bytes())['reads']]
                retries = {r.max_requests_per_page for r in reads}
                if len(retries) != 1:
                    raise ValueError('phase_a_kiwoom_plan_retry_mismatch')
                owner = kiwoom_aggregate_owner(role=role, observed_at=native['item'].received_at,
                    max_pages=max(r.max_pages for r in reads), max_requests_per_page=next(iter(retries)), policy=native['policy'])
            source['native_aggregate'] = {**native, 'owners': {role.owner: owner}}
        try:
            whole = compose_full_source(**args)
            second = compose_full_source(**args)
            if whole != second:
                raise ValueError('phase_a_whole_replay_drift')
            artifacts['whole_source'] = whole
            states['aggregate_whole_source_gate'] = dict(status='PASS', output_sha256=digest(whole))
            states['replay_twice_gate'] = dict(status='PASS', first_sha256=digest(whole), second_sha256=digest(second))
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(dict(stage='aggregate_whole_source_gate', reason=str(exc)))
            whole = None
        stocks, cases, markets = {}, {}, {}
        if whole is not None:
            from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
            for m, ts in UNIVERSE.items():
                for t in ts:
                    inputs = args['stock_inputs'][t]['fresh_financial_binding']
                    try:
                        result = prepare_fresh_subject(inputs, execution_generation_id=args['seed'].parent_run_id)
                        if result['stock'] != whole['packets'][m]['stocks'][t]:
                            raise ValueError('phase_a_stage_source_not_same_aggregate')
                        raw = proof['stock_outputs'][t]
                        if result['prepared']['mode'] == 'UNKNOWN_LIMIT' and raw.get('local_seed') != inputs['technical_inputs']['local_seed']:
                            raise ValueError('phase_a_unknown_local_seed_mismatch')
                        cases[t] = replay_stages(result, args['seed'].parent_run_id, raw)
                        stocks[t] = result['stock']
                    except (ValueError, KeyError, TypeError) as exc:
                        errors.append(dict(stage='stock_stages', ticker=t, reason=str(exc)))
            for m in ('us', 'kr'):
                try:
                    markets[m] = replay_market(whole, m, proof['market_outputs'][m])
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(dict(stage='Market2_gate', market=m, reason=str(exc)))
        artifacts.update(stock_stages=cases, market_stages=markets)
        if set(cases) == expected:
            for key in ('Core22_gate', 'A22_gate', 'B22_gate'):
                states[key] = dict(status='PASS', subjects={t: digest(cases[t]) for t in sorted(cases)})
            scopes = {digest(s['packet']['source_time_domains'].get('business_window')) for s in stocks.values()}
            if len(scopes) != 1 or next(iter(scopes)) == digest(None):
                states['aggregate_whole_source_gate'] = dict(status='BLOCKED', reasons=['COMMON_AVAILABILITY_WINDOW_NOT_PROVEN'])
            else:
                from datetime import datetime
                window = next(iter(stocks.values()))['packet']['source_time_domains']['business_window']
                context = args['fresh_context_inputs']
                if (context['publications']['as_of'] != datetime.fromisoformat(window['source_query_cutoff'])
                        or context['night']['observed_at'] != context['publications']['as_of']
                        or context['publications']['acquisition_cutoff'] != datetime.fromisoformat(window['business_availability_cutoff'])
                        or context['night']['acquisition_cutoff'] != context['publications']['acquisition_cutoff']):
                    states['aggregate_whole_source_gate'] = dict(status='BLOCKED', reasons=['COMMON_QUERY_ASOF_OR_AVAILABILITY_MISMATCH'])
            kinds = {s.get('event_view', {}).get('receipt', {}).get('acquisition_class') for s in stocks.values()}
            qualities = {s['quality_view']['receipt']['state'] for s in stocks.values()}
            modes = {p['mode'] for p in cases.values()}
            bridges = [t for t, s in stocks.items() if s.get('issuer_business_bridge')]
            archetypes = dict(fresh_event='FRESH_CURRENT_RUN' in kinds, persisted_event='PERSISTED_SOURCE_RECHECK' in kinds,
                limited='UNKNOWN_LIMIT' in modes, normal='EVIDENCE_BASED' in modes, issuer_bridge=bool(bridges),
                sec=any(s['market'] == 'us' and s['comparative_fact_refs'] for s in stocks.values()),
                dart=any(s['market'] == 'kr' and s['comparative_fact_refs'] for s in stocks.values()),
                fpi=any(args['stock_inputs'][t]['fresh_financial_binding']['financial_inputs']['plan']['security']['issuer_type'] == 'foreign_private_issuer'
                        and s['comparative_fact_refs'] and cases[t]['mode'] == 'EVIDENCE_BASED' for t, s in stocks.items()),
                insurance=any('insurancerevenue' in str(f.get('semantic', '')).lower()
                              for s in stocks.values() for f in s['projection']['fields']),
                clean_quality='verified_usable' in qualities,
                caution_or_denied_quality=bool({'caution_usable', 'denied'} & qualities),
                denied_quality='denied' in qualities)
            states['event_archetype_gate'] = dict(status='PASS' if all(archetypes.values()) else 'BLOCKED', coverage=archetypes)
            states['denied_quality_gate'] = dict(status='PASS' if 'denied' in qualities else 'BLOCKED', states=sorted(qualities))
            from scripts.r9_valuation_matrix import replay_matrix
            try:
                matrix = replay_matrix(stocks, {t: i['fresh_financial_binding'] for t, i in args['stock_inputs'].items()})
                artifacts['valuation_matrix'] = matrix
                states['valuation_matrix_gate'] = dict(status='PASS', receipt_sha256=digest(matrix))
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(dict(stage='valuation_matrix_gate', reason=str(exc)))
        if set(markets) == {'us', 'kr'}:
            states['Market2_gate'] = dict(status='PASS', receipts={m: digest(r) for m, r in markets.items()})
        if set(cases) == expected and set(markets) == {'us', 'kr'}:
            states['exact24_gate'] = dict(status='PASS', payloads={**{t: r['capture']['prepared_text_sha256'] for t, r in cases.items()},
                **{'MARKET_' + m: r['capture']['prepared_text_sha256'] for m, r in markets.items()}})
    for error in errors:
        if error['stage'] in states:
            states[error['stage']] = dict(status='BLOCKED', reasons=[error['reason']])
    blockers = {key: value for key, value in states.items() if value['status'] != 'PASS'}
    receipt = dict(contract='r9-rev10-phase-a-root-gate-v1', gates=states, blockers=blockers,
        code_policy_schema_sha256=digest(code), artifact_hashes={k: digest(v) for k, v in artifacts.items()},
        dispatch_allowed=not blockers, errors=errors,
        status='PASS' if not blockers else 'R2B_R9_REV10_PREFLIGHT_CONTRACT_GAP',
        provider_calls=0, model_calls=0, production_side_effects=0)
    receipt['receipt_sha256'] = digest(receipt)
    return receipt, artifacts
