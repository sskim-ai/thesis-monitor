"""Exact sealed Market projection and fairness audit, with no model route."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from unittest.mock import patch
import zipfile

from sqlmodel import Session

from app.services.unified_snapshot_contract import digest
from scripts import r2b_r5_market_adapter as adapter
from scripts import r2b_r4_preflight as r4
from scripts import r2b_r2_preflight as stocks
from scripts import r2b_r1_offline_closure as r1
from scripts import r2b_sealed_blind_preflight as io
from scripts.sealed_cohort_offline_proof import network_guard

R4_SHA = 'fda4d4fdbe007df116b800de217ec3b85fd89e7bf61b4c08844a9daf2f9c1698'


def _verified_report(path):
    adapter.require(io.sha(path.read_bytes()) == R4_SHA, 'r4_report_hash_mismatch')
    with zipfile.ZipFile(path) as archive:
        manifest_name = 'verified-v2-closeout/bundle-manifest.json'
        manifest = json.loads(archive.read(manifest_name))
        adapter.require(len(manifest) == 37 and set(archive.namelist()) ==
            {'verified-v2-closeout/' + n for n in manifest} | {manifest_name}, 'r4_manifest_coverage')
        for name, row in manifest.items():
            raw = archive.read('verified-v2-closeout/' + name)
            adapter.require(io.sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'r4_manifest_integrity')
    return dict(sha256=R4_SHA, manifest_entries=37, missing=0, mismatches=0)


def _leaf_types(value, path='$'):
    if isinstance(value, dict):
        return {k: v for name, child in value.items() for k,v in _leaf_types(child,path+'.'+name).items()}
    if isinstance(value, list):
        if not value:
            return {path+'[]': ['empty']}
        merged = {}
        for item in value:
            for key, types in _leaf_types(item,path+'[]').items():
                merged[key] = sorted(set(merged.get(key,[])) | set(types))
        return merged
    return {path: [type(value).__name__]}


def run(args):
    network = network_guard()
    args.output.mkdir(parents=True, exist_ok=False)
    allowed = [args.source_zip, args.blind_zip, args.r4_zip, args.receipt]
    if args.historical:
        allowed += [args.historical / (m+'-packet.json') for m in ('us','kr')]
    audit = stocks.SourceReadAudit(allowed, [p.parent for p in allowed] +
        [Path('/tmp/codex-remote-attachments'), Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs',
         Path('/Users/sskim/Codex/thesis-monitor/data'), Path('/Users/sskim/Codex/ohlcv-analyst/data')])
    sys.addaudithook(audit)
    def save(name,value):
        io.save(args.output,name,value)
    save('market-consumer-contract-inventory.json', adapter.contract_inventory())
    save('r4-result-identity.json', _verified_report(args.r4_zip))
    save('fairness-receipt.json', r4.verify_receipt(args.receipt.read_bytes()))
    manifest = io.read_verified_archive(args.source_zip, io.SOURCE_ZIP_SHA)
    with zipfile.ZipFile(args.source_zip) as archive:
        combined = json.loads(archive.read('whole-1/combined-full-source-packet.json'))
        for name, expected in r1.SOURCE_HASHES.items():
            adapter.require(digest(json.loads(archive.read('whole-1/'+name))) == expected, 'source_hash_drift')
    adapter.require(io.sha(args.blind_zip.read_bytes()) == r1.BLIND_SHA, 'blind_source_hash_mismatch')
    with zipfile.ZipFile(args.blind_zip) as archive:
        for market in ('us','kr'):
            item = json.loads(archive.read('BLIND_SOURCE_REVIEW/markets/'+market+'.json'))
            adapter.require(item['market_sources'] == combined['packets'][market]['market_sources'], 'blind_market_material_change')
        for name,key in [('publication-context','publication_context'),('night-futures','night'),('optional-denials','optional_denials')]:
            adapter.require(json.loads(archive.read('BLIND_SOURCE_REVIEW/'+name+'.json')) == combined['authority_graph'][key],
                            'blind_market_material_change')
    save('market-blind-view-materiality-audit.json',dict(status='PASS', new_economic_source_facts=0,
        independent_assessment_content_read=False, source_blind_zip_sha256=r1.BLIND_SHA,
        comparison='Exact market/publication/night/denial source equality; no assessment/template content read'))
    markets, matrix, history, leaves = {}, {}, {}, {}
    def deny(*args,**kwargs):
        raise AssertionError('production_db_cache_read_forbidden')
    from app.services import ai_review_service as live
    with patch.object(Session,'exec',deny), patch.object(live,'load_current_cross_section',deny), \
            patch.object(live,'load_structured_market_context',deny):
        for market in ('us','kr'):
            source = combined['packets'][market]
            kwargs = dict(expected_authority_sha256=r1.SOURCE_HASHES['full-source-authority-graph.json'])
            first = adapter.project_sealed_market_context(source, combined['seed'],combined['authority_graph'],**kwargs)
            second = adapter.project_sealed_market_context(source, combined['seed'],combined['authority_graph'],**kwargs)
            adapter.require(first == second, 'market_projection_nondeterministic')
            schema = stocks.schema_check(first['schema'])
            markets[market] = dict(status='PASS' if first['receipt']['numeric_alias_binding']['status']=='PASS' else 'BLOCKED',
                context_sha256=digest(first['context']), schema=schema,
                eligible_refs=first['context']['request_eligible_refs'], suppressed_refs=first['context']['suppressed_refs'],
                fact_catalog_sha256=first['receipt']['fact_catalog_sha256'],
                numeric_registry_sha256=first['receipt']['numeric_registry_sha256'],
                coverage_sha256=first['receipt']['coverage_sha256'], deterministic_twice=True)
            save(market+'-projection.json',first)
            src = first['packet']['market_context']
            matrix[market] = [dict(consumer_path='market_context.fact_catalog['+f['fact_id']+']',
                source_refs=first['receipt']['source_refs'][f['fact_id']], source_period=f['as_of_date'],
                output_sha256=digest(f), output_fields=f['fields'],
                transformation_owner='market_intelligence_service/night_futures',
                authority_sha256=kwargs['expected_authority_sha256'],
                projection_status='DETERMINISTIC_DERIVED',
                coverage_state='ELIGIBLE' if f['fact_id'] in first['context']['facts'] else 'SUPPRESSED_BY_CURRENT_CONSUMER',
                numeric_registry=[r for r in src['numeric_registry'] if r['fact_id']==f['fact_id']])
                for f in src['fact_catalog']]
            matrix[market] += [dict(consumer_path='market_context.'+k, output_sha256=digest(v),
                projection_status='EXPLICIT_UNAVAILABLE' if k=='optional_denials' else 'DETERMINISTIC_DERIVED',
                source_refs=['market_sources/component','publication_context','night_and_publication_context','optional_denials'],
                transformation_owner='existing native owners', output_type=type(v).__name__)
                for k,v in src.items() if k!='fact_catalog']
            leaves[market]=dict(source_context_shape=_leaf_types(src),consumer_request_shape=_leaf_types(first['context']),
                numeric_alias_bindings=first['receipt']['numeric_alias_binding'],
                numeric_field_denials=first['receipt']['numeric_field_denials'],
                consumer_owner='scripts.m12ds_r4_r4_market',
                required_fact_fields=['fact_id','fact_type','as_of_date','fields'],
                conditional_fields='Per typed fact/adapter/registry owner; numeric paths require registry or exact night owner',
                optional_denials_in_source=src['optional_denials'],
                absence_in_model='suppressed_refs/parity_matrix reasons; no optional numeric substitute')
            if args.historical:
                old = json.loads((args.historical/(market+'-packet.json')).read_bytes())
                old_context = old['market_context']
                history[market] = dict(historical_input_sha256=digest(old), old_shape=_leaf_types(old_context),
                    new_shape=_leaf_types(src), shared_root_keys=sorted(set(old_context)&set(src)),
                    omitted_not_current_consumer_required=sorted(set(old_context)-set(src)),
                    new_audit_only_keys=sorted(set(src)-set(old_context)), values_spliced=0,
                    current_schema_acceptance=schema['dialect']['status'])
    ready = sum(r['status']=='PASS' for r in markets.values())
    save('sealed-market-producer-consumer-parity-matrix.json',matrix)
    save('historical-shape-parity-audit.json',history)
    save('market-consumer-leaf-contract-and-denials.json',leaves)
    save('isolation-determinism.json',dict(network=network, production_db_cache_reads=0,
        forbidden_entry_points_patched=True, repeat_count=2, exact_equality=True))
    save('source-read-audit.json',audit.receipt())
    save('summary.json',dict(status='PASS' if ready==2 else 'BLOCKED', Market=ready,
        generation_id='20260928-r2b-r5-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        implementation=io.git('rev-parse','HEAD'), source_hashes=r1.SOURCE_HASHES,
        source_manifest_entries=len(manifest), markets=markets, model_calls=dict(Market=0,Core=0,A=0,B=0),
        whole_cohort_binding='NOT_YET_ISSUED', provider_refresh=0, independent_assessment_content_read=False))
    print(json.dumps(dict(Market=ready, model_calls=0, source_refresh=0)),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-zip','blind-zip','r4-zip','receipt','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--historical',type=Path)
    run(parser.parse_args())
