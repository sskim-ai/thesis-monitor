"""R4 source-only projection and exact existing-provider issuer bindings."""
import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path

from scripts.m12dr_offline_source_closure import context, read, write, sha
from scripts.m12da_source_use_contract import canonical_sha256
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12dk_current_source_authority import freeze_current_source_binding
from scripts.m12dp_observed_business_coverage import evaluate_cohort
from app.services.ai_review_service import validate_market_packet_session_parity

STOCK_FIELDS = ('ticker', 'company_name', 'industry', 'sector', 'business_model', 'revenue_sources',
    'company_profile', 'knowledge_routing', 'chart_knowledge_routing', 'thesis_version', 'thesis',
    'evidence', 'valuation', 'price_and_positioning', 'chart_context', 'data_cautions', 'fact_catalog',
    'numeric_registry', 'current_price_context', 'technical_context', 'cash_flow_user_visible',
    'working_capital_user_visible')
PACKET_FIELDS = ('packet_id', 'market', 'assessment_date', 'generated_at', 'schema_version',
    'analysis_policy_version', 'output_schema_version', 'structure_algorithm_version', 'knowledge', 'chart_knowledge')
MARKET_FIELDS = ('session', 'coverage', 'fact_catalog', 'numeric_registry', 'current_observation_fact_ids',
    'reference_fact_ids', 'prior_market_session_fact_ids', 'data_cautions', 'night_futures',
    'night_futures_audit', 'night_futures_cautions', 'adapter_context', 'fx', 'macro_temporal_eligibility')
BANNED = {'previous_assessment', 'deterministic_assessment', 'prior_accepted', 'latest_assessment',
    'monitoring_state', 'runtime_specificity_plan', 'industry_reasoning_plan', 'state_grounding_requirements',
    'accepted_decision_id', 'directional_balance', 'buy_drivers', 'sell_drivers', 'balance_summary',
    'archetype_rationale', 'tier_rationale', 'decisive_reason', 'holder_axis', 'new_buyer_axis', 'overall_axis',
    'model_summary', 'ai_verdict', 'model_recommendation', 'accepted_plan', 'frozen_pass_a_classification',
    'previous_decision', 'ai_entry_recommendation', 'buy_sell_balance', 'overall_maturity', 'driver_maturity',
    'model_scores', 'model_score', 'ai_score', 'decision_label', 'recommendation'}


def clean(value, path='$', removed=None):
    removed = removed if removed is not None else []
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key.lower() in BANNED or key.lower().startswith(('ai_verdict', 'model_recommendation')):
                removed.append(path + '.' + key)
            else:
                result[key] = clean(item, path + '.' + key, removed)
        return result
    if isinstance(value, list):
        return [clean(v, f'{path}[{i}]', removed) for i, v in enumerate(value)]
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            return json.dumps(clean(json.loads(value), path + ':encoded', removed), ensure_ascii=False, sort_keys=True)
        except (ValueError, TypeError):
            pass
    return value


async def identities(root):
    ROOT = root
    import httpx
    from app.config import get_settings
    from app.providers.filings import _resolve_opendart_company
    from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService
    path = ROOT / 'report/issuer-security-binding.json'
    if path.exists():
        raise ValueError('issuer_mapping_already_frozen')
    settings = get_settings()
    population = read(ROOT / 'report/monitored-population.json')
    generation = read(ROOT / 'report/source-freeze.json')['generation_id']
    rows = []
    owner = SecFinancialSnapshotService()
    logging.getLogger('httpx').setLevel(logging.CRITICAL)
    logging.getLogger('httpcore').setLevel(logging.CRITICAL)
    async with httpx.AsyncClient(timeout=20, headers={'User-Agent': settings.sec_user_agent or '', 'Accept': 'application/json'}) as client:
        for market in ('us', 'kr'):
            for ticker in sorted(population['markets'][market]['tickers']):
                row = {'contract': 'm12dp-existing-provider-issuer-binding-v1', 'ticker': ticker,
                    'source_generation_id': generation, 'market': market,
                    'observed_at': datetime.now(timezone.utc).isoformat(), 'model_calls': 0,
                    'security_denominator_inferred': False}
                try:
                    if market == 'us':
                        row.update(owner='SecFinancialSnapshotService._resolve_cik', provider='sec_edgar')
                        cik = await owner._resolve_cik(client, ticker)
                        if not cik or len(cik) != 10 or not cik.isdigit():
                            raise ValueError('official_ticker_cik_unresolved')
                        row.update(issuer_id='CIK:' + cik, source_url='https://www.sec.gov/files/company_tickers.json',
                            source_record={'ticker': ticker, 'cik': cik}, status='PASS')
                    else:
                        row.update(owner='OpenDARTProvider._resolve_opendart_company', provider='opendart')
                        company = await _resolve_opendart_company(settings.opendart_api_key, ticker)
                        if not company or company.stock_code != ticker:
                            raise ValueError('official_stock_corp_unresolved')
                        row.update(issuer_id='DART:' + company.corp_code,
                            source_url='https://opendart.fss.or.kr/api/corpCode.xml',
                            source_record={'ticker': company.stock_code, 'corp_code': company.corp_code,
                                'corp_name': company.corp_name, 'modify_date': company.modify_date}, status='PASS')
                except Exception as exc:
                    row.update(status='FAIL', error_type=type(exc).__name__)
                row['binding_sha256'] = canonical_sha256(row)
                rows.append(row)
    write(path, {'generation_id': generation, 'rows': rows, 'source_owner_invocations': len(rows),
        'controller_retries': 0, 'production_mutations': 0})
    print(json.dumps({'issuer_pass': sum(r['status'] == 'PASS' for r in rows), 'subjects': len(rows)}))


def project(root):
    ROOT = root
    complete = read(ROOT / 'report/collection-complete.json')
    if not complete['production_db_unchanged'] or complete['packet_markets'] != ['kr', 'us']:
        raise ValueError('complete_isolated_collection_required')
    if (ROOT / 'snapshot').exists():
        raise ValueError('source_projection_already_frozen')
    generation = read(ROOT / 'report/source-freeze.json')['generation_id']
    population = read(ROOT / 'report/monitored-population.json')
    removals, manifest, parity_rows = [], [], []
    for market in ('us', 'kr'):
        raw_path = ROOT / f'private/current-packets/{market}.json'
        raw = read(raw_path)
        parity_rows.append(validate_market_packet_session_parity(raw))
        safe = {k: deepcopy(raw[k]) for k in PACKET_FIELDS if k in raw}
        safe['stocks'] = []
        for stock in raw['stocks']:
            item = {k: deepcopy(stock[k]) for k in STOCK_FIELDS if k in stock}
            item['thesis'].pop('persistent_risks', None)
            for field in ('fact_catalog', 'numeric_registry'):
                item[field] = [r for r in item.get(field, []) if not str(r.get('fact_id', '')).startswith('monitoring:')]
            safe['stocks'].append(clean(item, path=stock['ticker'], removed=removals))
        if sorted(s['ticker'] for s in safe['stocks']) != sorted(population['markets'][market]['tickers']):
            raise ValueError('source_population_mismatch')
        safe['market_context'] = clean({k: deepcopy(raw['market_context'][k]) for k in MARKET_FIELDS
                                       if k in raw['market_context']}, removed=removals)
        write(ROOT / f'snapshot/{market}-packet.json', safe)
        write(ROOT / f'snapshot/{market}-context.json', context(safe, generation))
        manifest.append({'market': market, 'raw_sha256': sha(raw_path),
            'projected_sha256': sha(ROOT / f'snapshot/{market}-packet.json')})
    write(ROOT / 'report/current-session-parity.json', {'status': 'PASS' if all(r['status'] == 'PASS' for r in parity_rows) else 'FAIL', 'rows': parity_rows})
    write(ROOT / 'report/source-snapshot-manifest.json', {'generation_id': generation, 'rows': manifest})
    write(ROOT / 'report/facts-only-leakage-audit.json', {'removed_paths': removals, 'prior_model_outputs_read': False})
    bindings = {r['ticker']: r for r in read(ROOT / 'report/issuer-security-binding.json')['rows']}
    inputs = []
    for market in ('us', 'kr'):
        packet = read(ROOT / f'snapshot/{market}-packet.json')
        ctx = read(ROOT / f'snapshot/{market}-context.json')
        for ticker in sorted(ctx['selected_subjects']):
            cat = build_subject_catalog(context=ctx, ticker=ticker, atomic_claims=[])
            ep = next(r for r in ctx['evidence_packets'] if r['ticker'] == ticker)
            metadata = [r for r in ep['evidence'] if r['ref_id'] in cat['all_evidence_refs']]
            inputs.append(dict(ticker=ticker, source_generation_id=generation, source_packet=packet,
                evidence_packet=ep, catalog=cat, source_metadata=metadata,
                frozen_binding=freeze_current_source_binding(source_generation_id=generation, source_packet=packet, evidence_packet=ep),
                issuer_binding=bindings[ticker], expected_issuer_binding_sha256=canonical_sha256(bindings[ticker])))
    files = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'snapshot').glob('*.json'))}
    files['report/issuer-security-binding.json'] = sha(ROOT / 'report/issuer-security-binding.json')
    write(ROOT / 'report/coverage-input-freeze.json', {'source_generation_id': generation, 'files': files})
    result = evaluate_cohort(inputs, expected_subjects=sorted(bindings))
    write(ROOT / 'report/observed-business-source-coverage-matrix.json', result)
    print(json.dumps({'source_ready_before_quality': result['ready_count'], 'active': result['active_count'],
                     'session_parity': [r['status'] for r in parity_rows]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('identities', 'project'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    os.environ.update(THESIS_MONITOR_ENV_FILE='/Users/sskim/Codex/thesis-monitor/.env',
        DATA_DIR=str(root / 'private/isolated-data'),
        DATABASE_URL=f'sqlite:///{root}/private/isolated-data/thesis_monitor.sqlite3',
        NOTIFICATION_DRY_RUN='true', TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='',
        TELEGRAM_TEST_CHAT_ID='', PERSISTENCE_V2_WRITER_ENABLED='false',
        PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED='false')
    asyncio.run(identities(root)) if args.mode == 'identities' else project(root)
