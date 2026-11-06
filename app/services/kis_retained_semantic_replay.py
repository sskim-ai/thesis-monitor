"""Original KIS source/semantic gates over retained bytes, not a fresh plan."""
from datetime import date
import json
from urllib.parse import urlsplit
from app.services.kis_estimate_source_contract import cold_source
from app.services.vnext_research_store import plain,digest
from scripts import kr8_kis_integration as original
from scripts.kis_fy1_semantic_owner import qualify


def retained_fiscal_inventory(context,raw_path):
    """Date projection after original financial acquisition/receipt replay.

    The derived adapter receipt is explicitly dated; original HTTP bytes and
    generation are never rewritten or reissued as a current capture.
    """
    from app.services.bounded_financial_projection import project
    root=plain(context['directory']);raw_path=plain(raw_path)
    if raw_path.parent!=root:
        raise ValueError('FRESH_DART_INVENTORY_RECEIPT_GAP')
    result=project(context['plan'],context['acquisition'],root,context['receipts'],
        **(context.get('project_options') or {}))
    if result!=context['expected_projection']:
        raise ValueError('retained_financial_projection_changed')
    original_receipt=json.loads(plain(raw_path.with_name(raw_path.name.replace('.body','.receipt.json'))).read_bytes())
    request_name=original_receipt['logical_id'].split(':')[-1]+'.plan.json'
    if '/' in request_name or '\\' in request_name:
        raise ValueError('FRESH_DART_INVENTORY_RECEIPT_GAP')
    request=json.loads(plain(root/request_name).read_bytes())
    evidence=original.evidence(raw_path)
    url=urlsplit(request['url']);security=context['security']
    if (original_receipt['artifact']!=raw_path.name or original_receipt['raw_sha256']!=evidence.sha256
            or original_receipt['request_sha256']!=digest(request)
            or original_receipt['plan_sha256']!=context['acquisition']['plan_sha256']
            or request['plan_sha256']!=original_receipt['plan_sha256']
            or request['method']!='GET' or url.scheme!='https'
            or url.netloc!='opendart.fss.or.kr' or url.path!='/api/list.json'
            or request['params']['corp_code']!=security['corp_code']):
        raise ValueError('FRESH_DART_INVENTORY_RECEIPT_GAP')
    adapted=dict(kind='DATED_ORIGINAL_FINANCIAL_RECEIPT_PROJECTION',
        raw_sha256=evidence.sha256,http_status=original_receipt['HTTP_status'],
        request=dict(path=url.path,params=request['params']),
        original_generation=context['plan']['run_id'],
        original_receipt_sha256=digest(original_receipt),original_request_sha256=digest(request),
        current_capture=False)
    inventory,proof=original.normalized_inventory(evidence,adapted,
        code=security['ticker'],corp_code=security['corp_code'])
    return inventory,dict(proof,original_receipt_sha256=digest(original_receipt),
        original_generation=context['plan']['run_id'],source_cutoff=context['plan']['cutoff'],
        original_request_sha256=digest(request),new_HTTP=False,current_owner=False)


def replay_estimates(root,plan,*,inventories=None,static_root=None,static_hashes=None,enabled=False):
    if enabled is not True:
        raise ValueError('kis_retained_semantic_explicit_enable_required')
    root=plain(root)
    source=cold_source(root,plan)
    if len(source['rows'])!=16:
        raise ValueError('kis_retained_estimate_identity_receipts_incomplete')
    definitions=None
    if static_root is not None or static_hashes is not None:
        if static_root is None or not static_hashes:
            raise ValueError('KIS_STATIC_CONTRACT_HASH_GAP')
        definitions=original.semantic_inputs(plain(static_root),static_hashes)
    rows=[]
    for code,security in plan['securities'].items():
        estimate=original.evidence(plain(root/'estimate'/(code+'.body')))
        identity=original.evidence(plain(root/'identity'/(code+'.body')))
        inventory=(inventories or {}).get(code)
        if inventory is not None and definitions is None:
            raise ValueError('KIS_STATIC_CONTRACT_HASH_GAP')
        result=qualify(code,security['corp_code'],estimate,identity,inventory,
            date.fromisoformat(plan['as_of'][:10]),
            definitions['docs'] if definitions else None,
            definitions['controls'] if definitions else ())
        # Protocol/scale still belongs to its original Owner; semantic EPS is
        # not promoted to FPER by this source-only adapter.
        rows.append(dict(ticker=code,result=result,raw_sha256=estimate.sha256,
            original_generation=plan['generation_id'],current_owner_issued=False,
            wire_scale_verified=False,FPER_issued=False))
    return dict(contract='kis-retained-semantic-replay-v1',source=source,rows=rows,
        source_plan_relabelled=False,HTTP=0,current_owner=False,send=False)
