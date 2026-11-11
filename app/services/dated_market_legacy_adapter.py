"""Dated component display using the existing canonical selector, never a Parent."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import zipfile
from math import isfinite
from app.services.unified_snapshot_contract import digest
from app.services.market_display_plan import build_display_plan, render_display_plan, final_display_audit, US_SECTORS
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.kr_market_digest_quality_service import is_kr_sector_return_row


def component_sector_source(reference):
    """Internal projection after original Cold/custody checks, not JSON ingress."""
    if (reference.get('scope')!='DATED_SOURCE_INSPECTION_NOT_MARKET_CONTEXT'
            or reference.get('original_cold_status')!='ORIGINAL_COMPONENT_OWNER_COLD_PASS_NOT_FULL_PARENT'
            or digest(reference['value'])!=reference['value_sha256'] or reference['full_market_parent'] is not False):
        raise ValueError('dated_sector_original_component_required')
    market=reference['market'];session=reference['completed_session'];facts=[];identities=set();source_refs=set();basis={}
    if market not in {'us','kr'}:raise ValueError('dated_sector_market')
    values=reference['value']['observations' if market=='us' else 'sectors']
    for row in values:
        if market=='us':
            identity=row['series_code'];scope='US'
            if identity not in US_SECTORS:continue
            if (row['unit']!='usd' or row['market_session']!='us_regular' or row['observed_at'][:10]!=session
                    or row['raw_payload'].get('return_basis')!='same_response_adjacent_adjusted_regular_closes'):
                raise ValueError('dated_sector_adjusted_session_or_unit')
            fields=dict(series_code=identity,sector=identity,return_pct=row['change_pct'],currency='USD',quality='verified')
            metric='adjusted_etf_price_proxy'
        else:
            identity=row.get('sector_code');scope=row.get('market_scope')
            if scope not in {'KOSPI','KOSDAQ'} or not is_kr_sector_return_row(market_scope=scope,name=row['sector']):continue
            if row.get('taxonomy')!='kiwoom-sector-index-v1' or row.get('metric_role') not in {'actual_sector_breadth','sector_price_proxy'}:
                raise ValueError('dated_sector_taxonomy_or_basis')
            if row.get('listed_count') is not None and row['listed_count']<=0:continue
            if not row.get('source_ref') or session not in row['source_ref']:
                raise ValueError('dated_sector_ref_session')
            if row['source_ref'] in source_refs:raise ValueError('dated_sector_duplicate_source_ref')
            source_refs.add(row['source_ref'])
            fields=deepcopy(row);fields['quality']='verified';metric=row['metric_role']
        if not identity or (scope,identity) in identities:raise ValueError('dated_sector_duplicate_identity')
        identities.add((scope,identity))
        value=fields['return_pct']
        if value is None:continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value):
            raise ValueError('dated_sector_return_invalid')
        if scope in basis and basis[scope]!=metric:raise ValueError('dated_sector_mixed_metric_role')
        basis[scope]=metric
        facts.append(dict(fact_id='dated-sector:'+scope+':'+identity,fact_type='market_sector' if market=='us' else 'market_cross_section_sector',
            as_of_date=session,fields=fields))
    return dict(session=dict(market=market,assessment_date=session,latest_completed_regular_session_date=session),
        fact_catalog=facts,numeric_registry=build_numeric_registry(facts))


def _render_component_sectors(reference):
    source=component_sector_source(reference);market=reference['market'];session=reference['completed_session']
    refs=[f['fact_id'] for f in source['fact_catalog']]
    plan=build_display_plan(source,market=market,assessment_date=session,eligible_refs=refs)
    narrative='시장 판단은 발급하지 않습니다.'
    full_text=render_display_plan(plan,source,narrative)
    audit=final_display_audit(full_text,plan,source,narrative)
    if audit['status']!='PASS':raise ValueError('dated_sector_final_numeric_binding')
    sectors=[i for i in plan.items if i.block_id=='sectors']
    text='\n\n'.join(i.text for i in sectors)+'\n'
    return dict(contract='dated-canonical-sector-display-v1',market=market,session=session,scope='UNVERIFIED_REFERENCE_PROJECTION_NOT_AUTHORITY',
        source_sha256=reference['original_bundle_sha256'],component_sha256=reference['original_component_sha256'],
        source_view=source,selected_items=[i.model_dump(mode='json') for i in sectors],
        canonical_full_display_audit=audit,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        full_market_parent=False,market_judgment=None,NO_SEND=True,default_enabled=False)


def verify_component_sector_text(text, reference):
    expected=_render_component_sectors(reference)
    if text!=expected['text']:raise ValueError('dated_sector_final_text_changed')
    return expected['text_sha256']


def render_retained_component_sectors(*, archive_path, archive_sha256, reference_path, market, enabled=False, taxonomy_version=None):
    """Backend-selected C22M custody seal; reuse its Cold, not a supplied PASS.

    Hash selection belongs to the local composition root, never a model ledger
    or HTTP request. This is dated replay only and cannot restore a live Parent.
    """
    if enabled is not True:raise ValueError('dated_legacy_preview_default_off')
    archive=Path(archive_path);reference_file=Path(reference_path)
    for path in (archive,reference_file):
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('dated_legacy_preview_symlink')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=archive_sha256:
        raise ValueError('dated_legacy_custody_seal_hash')
    with zipfile.ZipFile(archive) as z:
        for name in ('PINNED_ORIGINAL_INPUTS.json','INDEPENDENT_PROCESS_VERIFICATION.json'):
            manifest=json.loads(z.read('MANIFEST.json'))['files'];raw=z.read(name)
            if hashlib.sha256(raw).hexdigest()!=manifest[name]['sha256'] or len(raw)!=manifest[name]['bytes']:
                raise ValueError('dated_legacy_custody_member_hash')
        pins=json.loads(z.read('PINNED_ORIGINAL_INPUTS.json'));proof=json.loads(z.read('INDEPENDENT_PROCESS_VERIFICATION.json'))
    if market not in {'us','kr'} or not any(r['market']==market and r['source_only'] for r in proof['field_checks']):
        raise ValueError('dated_legacy_original_cold_not_proven')
    items=[b for b in pins['market_bundles'] if b['market']==market]
    if len(items)!=1:raise ValueError('dated_legacy_custody_bundle_ambiguous')
    pin=items[0];path=Path(pin['path'])
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('dated_legacy_bundle_symlink')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('dated_legacy_original_bundle_changed')
    bundle=json.loads(raw);reference=json.loads(reference_file.read_bytes())
    if (reference['market']!=market or bundle['market']!=market
            or reference['original_bundle_sha256']!=pin['sha256']
            or reference['original_component_sha256']!=bundle['owner_proof']['component_sha256']
            or reference['value_sha256']!=bundle['owner_proof']['value_sha256']
            or digest(reference['value'])!=reference['value_sha256']):
        raise ValueError('dated_legacy_reference_original_value_binding')
    if taxonomy_version is None:
        result=_render_component_sectors(reference)
    elif taxonomy_version == 'sector-universe-user-confirmed-v2':
        from app.services.confirmed_sector_taxonomy import render_confirmed_sectors
        result=render_confirmed_sectors(reference)
    else:
        raise ValueError('dated_sector_unknown_version')
    result.update(scope='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY',custody_seal_sha256=archive_sha256)
    return result


def render_night_dwm_preview(source, *, assessment_date, eligible_refs):
    """Canonical typed night only; no legacy daily fallback or new numbers."""
    from app.services.market_numeric_claim_service import numeric_catalog
    catalog=numeric_catalog(source,market='us',assessment_date=assessment_date,eligible_refs=eligible_refs)
    night=[c for c in catalog['claims'] if c['claim_type']=='OFFICIAL_NIGHT']
    if len(night)>1:raise ValueError('dated_night_ambiguous_source')
    if not night:
        text='한국 야간선물\n일: 자료 부족\n주: 자료 부족\n월: 자료 부족\n'
        return dict(state='PARTIAL_NIGHT_UNAVAILABLE',text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),suppressed=catalog['suppressed'],NO_SEND=True,full_market_parent=False)
    claim=night[0];frames=claim['metadata']['timeframes']
    complete=all(frames[k]['status']=='FINAL' and frames[k]['quality']=='VALID' for k in ('daily','weekly','monthly'))
    text=claim['rendered_text']+'\n'
    return dict(state='DATED_DWM_COMPLETE' if complete else 'PARTIAL_DWM_EXPLICIT_PERIODS',text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        claim=claim,NO_SEND=True,full_market_parent=False,market_judgment=None)
