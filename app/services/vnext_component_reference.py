"""Immutable accounting references, not rehydrated Owner capabilities.

Manual reviewed pins authorize custody reads only. Original projection, quality,
period and accounting checks are replayed before joining a current public view.
"""
import copy
import json
import re
from pathlib import Path

from app.services.vnext_research_store import digest, plain
from app.services.vnext_composite_research import ALLOWED, PUBLIC_ID, instant
from app.services.vnext_historical_price_reference import load_pinned_archive

CONTRACT = 'vnext-source-bound-component-reference-v1'
INPUT = 'vnext-component-reference-inputs-v1'
USE = 'RESEARCH_REFERENCE_ONLY'


def _pinned(path, expected, maximum=16*1024**2):
    p = plain(path)
    if (not p.is_file() or p.stat().st_nlink != 1 or p.stat().st_size > maximum or
            set(expected) != {'sha256','bytes'} or p.stat().st_size != expected['bytes']):
        raise ValueError('component_input_size_or_path')
    b = p.read_bytes()
    if digest(b) != expected['sha256']:
        raise ValueError('component_input_pin')
    return b


def load_reference(manifest_path, manifest_sha256):
    p = plain(manifest_path)
    if not re.fullmatch('[0-9a-f]{64}', manifest_sha256 or '') or p.stat().st_size > 256*1024:
        raise ValueError('component_manifest_pin_required')
    b = p.read_bytes()
    if digest(b) != manifest_sha256:
        raise ValueError('component_manifest_pin')
    m = json.loads(b)
    if m.get('contract') != INPUT:
        raise ValueError('component_input_contract')
    archived = load_pinned_archive(**m['archive'])
    old = json.loads(archived['packet_bytes'])
    root = plain(m['capture_directory'])
    files = m['files']
    required = {'frozen-plan.json','acquisition.json','original-receipts.json','projection.json'}
    if not required <= set(files) or len(files)>100:
        raise ValueError('component_capture_domain')
    loaded = {}
    for name, pin in files.items():
        if name not in required and not re.fullmatch(r'request-\d+\.plan\.json|request-\d+-attempt-\d+\.body',name):
            raise ValueError('component_capture_filename')
        loaded[name] = _pinned(root/name, pin)
    plan = json.loads(loaded['frozen-plan.json'])
    receipts = json.loads(loaded['original-receipts.json'])
    for r in receipts:
        name = r['logical_id'].split(':')[-1]
        if name+'.plan.json' not in loaded or (not r.get('failure_class') and r.get('artifact') not in loaded):
            raise ValueError('component_unpinned_capture_dependency')
    snapshots = {}
    if len(m['comparison_sources'])>8:
        raise ValueError('component_snapshot_domain')
    for row in m['comparison_sources']:
        raw = _pinned(row['path'],row['pin'])
        snapshots[row['pin']['sha256']] = raw
    ctx = dict(plan=plan, acquisition=json.loads(loaded['acquisition.json']), directory=root,
               receipts=receipts, expected_projection=json.loads(loaded['projection.json']),
               security=plan['security'], project_options={'field_semantics': True},
               comparison_source_bytes=snapshots)
    return dict(original=old, archived_bytes=archived['packet_bytes'], original_context=ctx,
                custody=dict(manifest_sha256=manifest_sha256,archive=archived['custody'],
                             input_pins=files, authority='CUSTODY_ONLY_NOT_OWNER'))


def project(packet, reference):
    from datetime import date
    from app.models.financial import FinancialSnapshot
    from app.services.financial_observation_quality_service import build_reported_observation_quality, digest as quality_digest
    from app.services.reported_comparison_facts import comparative_facts
    from app.services.vnext_component_facts import TOTAL,verified_account_facts,select_account_family
    if (digest(reference['archived_bytes'])!=reference['custody']['archive']['member_sha256'] or
            json.loads(reference['archived_bytes'])!=reference['original']):
        raise ValueError('component_historical_bytes_changed')
    old = copy.deepcopy(reference['original'])
    prior = old.pop('operating_components')
    actual=prior
    identity = packet['public_security']; historical = old['public_security']
    keys = ('canonical_security_id','canonical_company_id','ticker','country','exchange','security_type','issuer_type','corp_code')
    if (any(identity.get(k) != actual['security'].get(k) for k in keys) or
            any(identity.get(k) != historical[k] for k in keys if k in historical) or
            packet['ticker'] != old['case'] or packet['model'] != 'OFF' or packet['send'] is not False or
            packet['strict_ready'] is not False or packet['holdings_included'] is not False or
            packet['user_thesis_included'] is not False):
        raise ValueError('component_identity_or_public_scope')
    if any(actual.get(k) is not False for k in ('strict_native','investment_direction_grant','valuation_denominator_grant','recurrence_verified')):
        raise ValueError('component_historical_authority')
    ctx = reference['original_context']
    plan=ctx['plan']
    if plan['provider']!='opendart' or plan['security']!=actual['security'] or plan['run_id']!=actual['source_generation']:
        raise ValueError('component_original_plan')
    if actual['source_generation'] not in {r['run_id'] for r in packet['source_runs']}:
        raise ValueError('component_generation')
    if instant(actual['source_cutoff']) > instant(packet['as_of']) or instant(old['as_of']) > instant(packet['as_of']):
        raise ValueError('component_after_cutoff')
    evidence = [e for e in packet['evidence'] if e['field']=='financial.operating_income']
    previous = next(e for e in old['evidence'] if e['field']=='financial.operating_income')
    if len(evidence)!=1:
        raise ValueError('component_current_source_missing')
    e=evidence[0]
    if (e['status'] not in ALLOWED or e['allowed_use']!='PUBLIC_RESEARCH_REFERENCE_ONLY' or
            e['direction_allowed'] is not False or e['data']['fields']!=previous['data']['fields']):
        raise ValueError('component_selected_quality_or_use')
    snapshot=json.loads(ctx['comparison_source_bytes'][e['source_sha']])
    if digest(ctx['comparison_source_bytes'][e['source_sha']])!=e['source_sha']:
        raise ValueError('component_snapshot_bytes')
    qualified=[]
    for bundle in snapshot['projection']['quality_bundles']:
        inputs=bundle['source_inputs']
        if quality_digest(inputs)!=bundle['source_inputs_sha256'] or inputs['formal']['provider']!='opendart':
            raise ValueError('component_quality_input')
        quality=build_reported_observation_quality(formal=FinancialSnapshot.model_validate(inputs['formal']),
            preliminary=FinancialSnapshot.model_validate(inputs['preliminary']) if inputs.get('preliminary') else None,
            ticker=inputs['ticker'],cutoff=date.fromisoformat(inputs['cutoff']))
        if quality!=bundle['quality']:
            raise ValueError('component_quality_replay')
        qualified.extend(comparative_facts(quality,ticker=packet['ticker'],issuer_id=e['data']['fields']['issuer_id']))
    from app.services.vnext_composite_research import public_data
    if not any(public_data(e['field'],dict(fact=f))==e['data'] for f in qualified):
        raise ValueError('component_quality_fact')
    raw_shas={f['source_sha'] for f in actual['facts']}
    if len(raw_shas)!=1 or not raw_shas <= {d['raw_sha256'] for d in e['provenance']['dependencies']}:
        raise ValueError('component_source_dependency')
    receipt=next(r for r in ctx['receipts'] if digest(r)==actual['source_receipt_sha'])
    if (receipt.get('failure_class') or receipt.get('revoked') or
            receipt.get('HTTP_status')!=200 or receipt.get('provider_status')!='000'):
        raise ValueError('component_capture_receipt_denied')
    directory=plain(ctx['directory'])
    request_name=receipt['logical_id'].split(':')[-1]+'.plan.json'
    if request_name not in reference['custody']['input_pins'] or receipt['artifact'] not in reference['custody']['input_pins']:
        raise ValueError('component_receipt_domain')
    request=json.loads(_pinned(directory/request_name,reference['custody']['input_pins'][request_name]))
    body=_pinned(directory/receipt['artifact'],reference['custody']['input_pins'][receipt['artifact']])
    if (digest(body)!=receipt['raw_sha256'] or quality_digest(request)!=receipt['request_sha256'] or
            quality_digest(plan)!=receipt['plan_sha256'] or request['plan_sha256']!=receipt['plan_sha256'] or
            request['logical_id']!=receipt['logical_id'] or request['params'].get('fs_div')!='CFS'):
        raise ValueError('component_original_capture_binding')
    f=e['data']['fields']
    if f['statement_basis']!='consolidated' or f['issuer_id']!='DART:'+plan['issuer']:
        raise ValueError('component_issuer_basis')
    schema=select_account_family(json.loads(body),provider=plan['provider'],statement_basis=f['statement_basis'])
    if schema['status']!='CANDIDATE_REQUIRES_REPLAY':
        raise ValueError(schema['reason'])
    reproduced=verified_account_facts(json.loads(body),plan=plan,request=request,fields=f,raw_sha=receipt['raw_sha256'])
    if reproduced!=prior['facts']:
        raise ValueError('component_original_fact_replay')
    facts=[f for f in actual['facts'] if f['account_id']!=TOTAL]
    totals=[f for f in actual['facts'] if f['account_id']==TOTAL]
    if len(facts)!=6 or {f['role'] for f in totals}!={'current','comparison'}:
        raise ValueError('component_comparable_pair')
    return dict(contract=CONTRACT,status=USE,consumer='VNEXT_COMPOSITE_ECONOMIC_EXPLANATION',
                security={k:identity[k] for k in PUBLIC_ID if k in identity},facts=facts,totals=totals,
                account_source_sha=next(iter(raw_shas)),original_source_generation=actual['source_generation'],
                original_source_cutoff=actual['source_cutoff'],source_receipt_sha=actual['source_receipt_sha'],
                captured_at=receipt['vnext_source_birth']['captured_at'],reference_reviewed_at=e['provenance']['captured_at'],
                quality_receipt_sha=e['data']['quality_receipt_sha256'],
                original_comparison_sha=previous['source_sha'],selected_comparison_sha=e['source_sha'],
                source_ref=e['ref'],lineage_group=e['lineage_group'],independent_lineages=1,
                reconciliation_pass=True,original_owner_not_reissued=True,current_owner_status='NOT_ISSUED_CURRENT_CONTEXT',
                no_FY1_EPS_PER_PBR=True,no_margin_denominator=True,not_strict_direction=True,
                recurrence_verified=False,causality_verified=False,current_collection=False,
                custody=reference['custody'],input_sha256=digest(packet))


def catalog(att):
    rows=[]
    for f in att['facts']:
        row=dict(ref=att['source_ref'],field='operating_component.'+f['account_id'],path=f['role'],
                 value=f['value'],unit=f['currency'],basis='CONSOLIDATED_SINGLE_QUARTER_RESEARCH_REFERENCE_ONLY',
                 as_of=f['period_start']+'/'+f['period_end'],source_sha=f['source_sha'],
                 lineage_group=att['lineage_group'],occurrence=f['occurrence'])
        rows.append(dict(row,catalog_id='c'+digest(row)[:24]))
    return rows


def attach(packet, reference):
    from app.services.vnext_composite_research import numeric_catalog
    if packet.get('component_reference') or packet.get('historical_price_reference'):
        raise ValueError('component_attachment_already_present_or_incompatible')
    result=dict(packet,component_reference=project(packet,reference))
    result['numeric_catalog']=numeric_catalog(result)
    return result
