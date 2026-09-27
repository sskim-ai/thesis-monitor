"""Reassemble all current securities exclusively from a verified sealed cohort."""
from datetime import date
import json
from pathlib import Path
import sys

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, load_owned_role
from app.services.unified_stock_anomaly_scope import materialize_source_components
from app.services.versioned_business_stock_owner import bind_current_stock
from app.services.unified_stock_owner import validate_assembled
from scripts.sealed_cohort_offline_proof import network_guard
from scripts.unified_stock_owner_proof import POLICY
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12dr_offline_source_closure import context
from scripts.m12dr_financial_source_authority import build_source_authority
from scripts.m12dk_current_source_authority import freeze_current_source_binding


def cohort_composition_gate(matrix):
    expected = {(m, t) for m, ts in UNIVERSE.items() for t in ts}
    if len(matrix) != len(expected) or {(r['market'], r['ticker']) for r in matrix} != expected:
        raise ValueError('whole_source_exact_cohort_required')
    blocked = [r['ticker'] for r in matrix if r['status'] != 'PASS' or not r.get('packet_sha256')
               or not r.get('authority_sha256') or r.get('authority_errors')]
    return {'eligible': not blocked, 'blocked_subjects': blocked,
            'reason': 'ALL_COMPONENTS_PASS' if not blocked else 'CURRENT_STOCK_OR_AUTHORITY_INCOMPLETE',
            'whole_source_artifacts_produced': False}


def current_stock_inputs(corpus, plan, local, ticker, policy=POLICY):
    receipts, artifacts, roles = {}, {}, {}
    for ordinal, entry in enumerate(plan.reads, 1):
        if entry.subject != ticker:
            continue
        path = corpus / 'stock-acquisition' / f'role-{ordinal:03d}.receipt.json'
        receipt = json.loads(path.read_bytes())
        roles[entry.role] = load_owned_role(plan, entry, receipt, path.parent)
        receipts[entry.role] = receipt
        for name in [receipt['normalized_artifact'], *[p['artifact'] for p in receipt['pages']]]:
            artifacts[name] = (path.parent / name).read_bytes()
    entry = next(e for e in plan.reads if e.subject == ticker)
    components = materialize_source_components(ticker=ticker, market=entry.market,
        cutoff=date.fromisoformat(entry.latest_completed_session),
        observed_at=plan.frozen_at.isoformat(), roles=roles)
    financial = json.loads((corpus / f'class-c/financial-{ticker}.json').read_bytes())
    hashes = {k: digest(v) for k, v in dict(local=local, financial=financial,
        components=components, receipts=receipts, plan=plan.model_dump(mode='json')).items()}
    return dict(plan=plan, ticker=ticker, receipts=receipts, artifacts=artifacts,
        local_seed=local, financial=financial, components=components,
        expected_hashes=hashes, policy=policy)


def replay(corpus, output, *, persisted_events=None):
    counts = network_guard()
    def read(path):
        return json.loads(path.read_bytes())
    def save(name, value):
        durable_json(output / name, value, exclusive=True)
    acquisition = read(corpus / 'rev8-full-source-acquisition-plan.json')
    plan = StockPlan.model_validate(acquisition['stock_plan'])
    versions = {t: (corpus / f'class-c/business-versioned-{t}.json').read_bytes()
                for ts in UNIVERSE.values() for t in ts}
    locals_ = {m: read(corpus / f'class-c/local-{m}.json') for m in UNIVERSE}
    matrix = []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            inputs = current_stock_inputs(corpus, plan, locals_[market], ticker)
            receipts, components = inputs['receipts'], inputs['components']
            row = {'ticker': ticker, 'market': market, 'attempt_id': acquisition['market_attempts'][market],
                'price_receipts_sha256': digest(receipts), 'fresh_price_roles': sorted(receipts),
                'current_price_eligible': components['current_price_eligible'],
                'technical_state': components['technical_status'], 'old_price_consumed': False}
            try:
                event_inputs = (persisted_events or {}).get(ticker)
                if event_inputs is None:
                    bound = bind_current_stock(stock_inputs=inputs, versions=versions,
                        version_hashes=acquisition['class_c_versions'], local_seeds=list(locals_.values()))
                else:
                    from app.services.persisted_business_event_owner import bind_persisted_event
                    from app.services.unified_source_policy import UnifiedSourcePolicy
                    inputs['policy'] = UnifiedSourcePolicy(
                        POLICY.allowed_providers | {event_inputs['policy_provider']})
                    event_inputs = {k: v for k, v in event_inputs.items() if k != 'policy_provider'}
                    event_inputs['policy'] = inputs['policy']
                    bound = bind_persisted_event(stock_inputs=inputs, event_inputs=event_inputs)
                result = bound['result']
                version_inputs = dict(ticker=ticker, versions=versions,
                    version_hashes=acquisition['class_c_versions'], local_seeds=list(locals_.values()),
                    cutoff=plan.frozen_at, policy=POLICY)
                row['assembled_validation_pass'] = validate_assembled(result, expected_result_sha256=digest(result),
                    versioned_business_inputs=version_inputs)
                if result['status'] == 'PASS':
                    packet, ep = result['packet'], result['evidence_packet']
                    generation = acquisition['proof_run_id']
                    cat = build_subject_catalog(context=context(packet, generation), ticker=ticker, atomic_claims=[])
                    metadata = [r for r in ep['evidence'] if r['ref_id'] in cat['all_evidence_refs']]
                    authority = build_source_authority(quality_bundles={}, issuer_bindings={},
                        versioned_business_inputs=version_inputs,
                        persisted_event_inputs=event_inputs,
                        ticker=ticker, source_generation_id=generation, source_packet=packet,
                        evidence_packet=ep, catalog=cat, source_metadata=metadata,
                        frozen_binding=freeze_current_source_binding(source_generation_id=generation,
                            source_packet=packet, evidence_packet=ep))
                    save('authority/' + ticker + '.json', authority)
                    errors = [r for r in authority['family_receipts'] if r['errors']]
                    row.update(authority_sha256=digest(authority), authority_errors=errors)
                save('stocks/' + ticker + '.json', bound)
                row.update({k: result[k] for k in ('status', 'mandatory_missing', 'packet_sha256')})
                row.update(binding_kind=bound['binding_kind'], business_version_sha256=(
                    bound['business_version']['version_sha256'] if event_inputs is None
                    else digest(result['persisted_event_receipt'])),
                    business_refs=[r['ref_id'] for r in result['observed_business_union'] if r['status'] == 'PASS'],
                    fresh_price_technical_unchanged=bound.get('fresh_price_technical_unchanged', True))
            except (ValueError, KeyError, TypeError) as exc:
                row.update(status='BLOCKED', mandatory_missing=[str(exc)], packet_sha256=None)
            matrix.append(row)
            print(ticker, row['status'], row['mandatory_missing'], flush=True)
    save('22-current-stock-matrix.json', matrix)
    save('whole-composition-gate.json', cohort_composition_gate(matrix))
    save('network-counters.json', counts)
    return matrix


if __name__ == '__main__':
    replay(Path(sys.argv[1]), Path(sys.argv[2]))
