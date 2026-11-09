"""Read explicit public artifacts only; no live model, network, database or Owner issuance."""
import argparse
import ast
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

from app.services.dated_research_model import encoded, digest, reference_catalog, validate_output, build_prompt
from app.services.dated_research_review_v2 import (
    CONTRACT, ResearchSplit, compact_evidence, comparison_semantics, temporal_record,
    replay_occurrence, replay_context, render_numeric_citations, operating_margin,
)


def run(args):
    def guard(event, detail):
        if event.startswith(('socket.', 'sqlite3.', 'subprocess.', 'os.system')):
            raise RuntimeError('offline_review_denied:' + event)
    sys.addaudithook(guard)
    out = args.output; out.mkdir(parents=True, exist_ok=True)
    def save(name, data):
        (out/name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    def doc(name, text): (out/name).write_text(text + '\n')
    prepared = datetime.now(timezone.utc).isoformat()
    errors = []; artifacts = []
    for directory in args.raw_root:
        for file in sorted(directory.glob('request-*-attempt-1.body')):
            receipt_file = file.with_suffix('.receipt.json')
            plan_file = directory / (file.name.split('-attempt-')[0] + '.plan.json')
            if not receipt_file.exists() or not plan_file.exists():
                continue
            raw = file.read_bytes()
            try: payload = json.loads(raw)
            except (ValueError, UnicodeError): continue  # HTML filing bodies are not companyfacts/JSON rows.
            if not isinstance(payload, dict) or not ('facts' in payload or 'list' in payload): continue
            receipt, request = json.loads(receipt_file.read_bytes()), json.loads(plan_file.read_bytes())
            artifacts.append(dict(path=str(file), raw=raw, payload=payload, receipt=receipt, request=request))
    with zipfile.ZipFile(args.inputs) as inputs, zipfile.ZipFile(args.models) as models:
        index = json.loads(inputs.read('SOURCE_ARCHIVE_INDEX.json'))['cases']
        sidecar = []; times = []; compact_stats = []
        reuse = args.reuse_model_audit
        numeric = json.loads((reuse/'NUMERIC_NO_SEND.json').read_text()) if reuse else {}
        adj = json.loads((reuse/'ADJ_INCREMENTAL_VALUE.json').read_text()) if reuse else []
        preservation = json.loads((reuse/'EXISTING_OUTPUT_PRESERVATION.json').read_text()) if reuse else []
        cases = {}
        for ticker, binding in index.items():
            view_raw = inputs.read(f'CASES/{ticker}/RESEARCH_VIEW.json'); view = json.loads(view_raw)
            assert digest(view_raw) == binding['research_view_sha256']
            catalog = reference_catalog(view)
            assert digest(encoded(catalog)) == binding['reference_catalog_sha256']
            cases[ticker] = view
            for row in view['financial_observations']:
                fields = row['original_fields']; deps = row['original_quality'].get('field_dependency_receipts', {})
                proofs = []; failures = []
                lineages = [(role, deps[role]['lineage']) for role in ('current','comparison') if role in deps]
                wanted = len(lineages) or 1
                for role, lineage in lineages or [('absolute', None)]:
                    matches = []
                    for artifact in artifacts:
                        if lineage and 'concept' in lineage:
                            if artifact['payload'].get('cik') != lineage['issuer_cik']: continue
                        elif lineage:
                            if artifact['request'].get('params', {}).get('corp_code') != str(fields['issuer_id']).split(':')[-1]: continue
                        elif digest(artifact['raw']) != fields.get('original_raw_sha256'): continue
                        try:
                            proof = (replay_occurrence(artifact['raw'], artifact['receipt'], artifact['request'], lineage)
                                if lineage else replay_context(artifact['raw'], artifact['receipt'], artifact['request'], fields))
                            matches.append({**proof, 'role':role, 'path':artifact['path'],
                                'capture_receipt_sha256':digest(encoded(artifact['receipt'])),
                                'request_plan_sha256':artifact['request']['plan_sha256']})
                        except (ValueError, KeyError, TypeError) as exc:
                            failures.append(dict(role=role, path=artifact['path'], reason=str(exc)))
                    if len(matches) == 1: proofs.extend(matches)
                    else: failures.append(dict(role=role, reason='EXACT_RAW_MATCH_COUNT', count=len(matches)))
                replayed = len(proofs) == wanted
                scales = replayed and all(p['period_and_unit_scale_verified'] is True for p in proofs)
                sidecar.append(dict(ticker=ticker, original_ref=row['original_ref'], field=row['field'],
                    original_fields=fields, original_quality=row['original_quality'],
                    sealed_bytes_match=True, provider_original_replay_verified=True if replayed else 'UNKNOWN',
                    verifier='EXACT_RECORDED_PROVIDER_OCCURRENCE_WITH_EXISTING_DART_LINEAGE; NOT_OWNER_REISSUE',
                    period_and_unit_scale_verified=True if scales else 'UNKNOWN',
                    comparison_semantics_verified=comparison_semantics(fields) if lineages else 'UNKNOWN',
                    causal_mechanism_verified='UNKNOWN', raw_replay=proofs,
                    unresolved=[] if replayed else failures, original_owner_grants_unchanged=True,
                    consumer_impact=dict(exact_dated_fact='ORIGINAL_ACCEPTED_SCOPE_PRESERVED',
                        derived_use='RAW_CHECKED_BUT_CONSOLIDATION_OR_INDEPENDENT_QUALITY_REQUIRES_REVIEW' if scales else 'QUARANTINE_DERIVED_USE',
                        causal_direction='HYPOTHESIS_ONLY', strict_native='NO_NEW_GRANT')))
            for row in view['valuation']:
                modes = {mode:temporal_record(row['original_fact'], cutoff=view['as_of'], prepared_at=prepared, mode=mode)
                    for mode in ('POINT_IN_TIME','RETROSPECTIVE_DATED_RESEARCH')}
                times.append(dict(ticker=ticker, ref=row['source_locator'], metric=row['metric'], **modes))
            compact, full = compact_evidence(view)
            assert compact['evidence'] == view and compact['reference_catalog']['numeric_facts'] == full['numeric_facts']
            oldbytes = encoded(dict(evidence=view, reference_catalog=full))
            newbytes = encoded(compact)
            compact_stats.append(dict(ticker=ticker, old_bytes=len(oldbytes), compact_bytes=len(newbytes),
                bytes_removed=len(oldbytes)-len(newbytes), old_payload_sha256=digest(oldbytes),
                proposed_payload_sha256=digest(newbytes), all_refs_preserved=set(full['refs'])==set(compact['reference_catalog']['refs']),
                all_numeric_facts_preserved=True, full_catalog_kept_for_validator=True,
                model_quality_or_latency_proven=False, token_savings='UNMEASURED'))
            stages = {}
            for stage in ('BLIND','ADJ'):
                if reuse: continue
                name = f'CASES/{ticker}/{stage}/ACCEPTED.json'
                if name not in models.namelist(): continue
                raw = models.read(name); output = json.loads(raw)
                validated = validate_output(raw, view=view, binding=binding,
                    stage='BLIND' if stage=='BLIND' else 'ADJUDICATION', catalog=full)
                assert validated == output
                stages[stage] = output
                numeric[f'{ticker}/{stage}'] = render_numeric_citations(output,full,view)
                # Exact V1 validator stays outside the compact transport proposal.
                preservation.append(dict(ticker=ticker,stage=stage,sha256=digest(raw),old_validator='PASS',
                    compact_numeric_coverage=all({k:v for k,v in c.items() if k!='axis'} in compact['reference_catalog']['numeric_facts']
                        for c in output['citations']),auto_migrated_to_v2=False))
            if set(stages) == {'BLIND','ADJ'}:
                blind, adjudicated = stages['BLIND'],stages['ADJ']
                brefs = {r for c in blind['citations'] for r in [c['ref']]}
                arefs = {r for c in adjudicated['citations'] for r in [c['ref']]}
                adj.append(dict(ticker=ticker, new_numeric_refs=sorted(arefs-brefs),
                    new_axis_refs=sorted({r for n in ('overall','newbuyer','holder_virtual') for r in adjudicated[n]['refs']} -
                        {r for n in ('overall','newbuyer','holder_virtual') for r in blind[n]['refs']}),
                    confidence_changes={n:[blind[n]['confidence'],adjudicated[n]['confidence']] for n in
                        ('overall','newbuyer','holder_virtual','valuation','technical_price_structure') if blind[n]['confidence']!=adjudicated[n]['confidence']},
                    changed_falsification_conditions=[s for s in adjudicated['what_changes_mind'] if s not in blind['what_changes_mind']],
                    adjudication_change_reason=adjudicated['adjudication_change_reason'],
                    exact_axis_content_changed=[n for n in ('overall','newbuyer','holder_virtual') if blind[n]!=adjudicated[n]],
                    labels_preserved=all(blind[n]['state']==adjudicated[n]['state'] for n in ('overall','newbuyer','holder_virtual')),
                    interpretation='Content additions, not proof of independent new evidence or cost effectiveness.'))
        assert len(preservation)==9 and len(times)==12 and len(sidecar)==33
        assert sum(len(v) for v in numeric.values()) == 160
        save('C22H_V2_SOURCE_QUALITY_SIDECAR.json', dict(contract=CONTRACT,Owner_issuance=False,facts=sidecar))
        save('TEMPORAL_MAP.json',times); save('COMPACT_COVERAGE.json',compact_stats)
        save('EXISTING_OUTPUT_PRESERVATION.json',preservation); save('NUMERIC_NO_SEND.json',numeric)
        save('ADJ_INCREMENTAL_VALUE.json',adj)
        save('NEWBUYER_RESEARCH_SCHEMA.json',ResearchSplit.model_json_schema())
        margin_rows=[]
        for ticker,view in cases.items():
            found={r['original_fields']['metric']:r for r in view['financial_observations'] if r['role']=='QUANTITATIVE_COMPARISON'}
            if not {'revenue','operating_income'}<=set(found): continue
            operands=[]
            for metric in ('revenue','operating_income'):
                row=found[metric]; fields=row['original_fields']; qa=next(q for q in sidecar if q['original_ref']==row['original_ref'])
                operands.append(dict(issuer_id=fields['issuer_id'], metric=metric, ref=row['original_ref'], value=fields['current_value'],
                    statement_basis=fields['statement_basis'],period_start=fields['period_start'],period_end=fields['period_end'],
                    period_type=fields['period_type'],currency=fields['currency'],unit=fields['currency'],unit_scale=1,
                    raw_verified=qa['provider_original_replay_verified'] is True,
                    scale_verified=qa['period_and_unit_scale_verified'] is True,
                    consolidation_explicitly_proven=all(p.get('consolidation_explicitly_proven') is True for p in qa['raw_replay'])))
            margin_rows.append(dict(ticker=ticker, result=operating_margin(*operands)))
        save('BOUNDED_MARGIN_RECEIPTS.json',margin_rows)
        tree=ast.parse(args.universe.read_text()); universe=next(ast.literal_eval(n.value) for n in tree.body
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UNIVERSE' for t in n.targets))
        with (out/'C22H_V2_GENERALIZATION_GAP_22.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f, fieldnames=['ticker','market','source','technical','economic_facts','valuation','old_model','new_schema','operational_gap']);writer.writeheader()
            for market,tickers in universe.items():
                for ticker in tickers:
                    v=cases.get(ticker)
                    writer.writerow(dict(ticker=ticker,market=market,source='CODE_UNIVERSE_NOT_CURRENT_DB_REGISTRATION',
                        technical='DATED_SOURCE_PRESERVED_66_ROLES_REPORTED_NOT_RERUN',
                        economic_facts=len(v['financial_observations']) if v else 'NOT_INSPECTED_IN_THIS_TASK',
                        valuation=len(v['valuation']) if v else 'NOT_INSPECTED_IN_THIS_TASK',
                        old_model='C22G_OR_C22F_ACCEPTED_PRESERVED' if v else 'NOT_INSPECTED_IN_THIS_TASK',
                        new_schema='OFFLINE_CONTRACT_ONLY_NO_MODEL_OUTPUT',
                        operational_gap='CURRENT_REGISTRATION/OWNER/STAGE/THESIS_NOT_CHECKED; STRICT_READY_0/22'))
        save('OFFLINE_EXECUTION_RECEIPT.json',dict(prepared_at=prepared,financial_HTTP=0,model_subprocess=0,
            DB_read_write=0,send_order=0,service_schedule_changes=0,old_validated_outputs=len(preservation),
            facts=len(sidecar), exact_raw_replayed=sum(r['provider_original_replay_verified'] is True for r in sidecar),
            raw_scale_verified=sum(r['period_and_unit_scale_verified'] is True for r in sidecar),
            independently_verified_causal_mechanisms=0,valuation_time_maps=len(times),
            Strict_READY='0/22',production_integration=False,guard='socket/sqlite/subprocess audit-denied'))
        doc('C22H_V2_ADJ_INCREMENTAL_VALUE.md', '# Offline ADJ content audit\n\n'+'\n\n'.join(
            f"## {r['ticker']}\nNew cited numeric refs: {len(r['new_numeric_refs'])}; new decision refs: {len(r['new_axis_refs'])}; "
            f"confidence changes: {r['confidence_changes']}; labels unchanged: {r['labels_preserved']}.\n"
            f"Rationale: {r['adjudication_change_reason']}\nFalsification additions/rewordings:\n"+'\n'.join('- '+s for s in r['changed_falsification_conditions']) for r in adj)+
            '\n\nNew wording is not necessarily new information. Unchanged labels alone do not establish zero value. No model/cost-performance experiment was run.')
    print(json.dumps(dict(output=str(out),facts=33,outputs=9,citations=160,temporal_maps=12)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('inputs','models','universe','output'): p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--raw-root',type=Path,action='append',required=True)
    p.add_argument('--reuse-model-audit',type=Path,help='Reuse this task completed model-output audit; never rerun models.')
    run(p.parse_args())
