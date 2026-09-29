"""Finite SEC/OpenDART slots compiled before any source response is available."""
import httpx

from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, wire_identity
from app.services.sealed_opendart_contract import opendart_headers
from app.services.sealed_response_binding import ResponseBinding
from app.services.unified_snapshot_contract import digest, encoded


def financial_slots(policy, *, owner, owner_sha256, config_sha256):
    p = policy
    prefix = 'financial:' + p['ticker']
    result = []
    def add(suffix, operation, url, *, params=None, rule=None):
        key = prefix + ':' + suffix
        headers = ({'User-Agent': 'PLAN_CREDENTIAL', 'Accept': 'application/json'}
                   if p['market'] == 'us' else opendart_headers())
        if p['market'] == 'kr':
            params = dict(params or {}, crtfc_key='PLAN_CREDENTIAL')
        req = httpx.Request('GET', url, params=params, headers=headers)
        result.append(FreshRequestDescriptor(generation_id=p['run_id'], logical_request_id=key,
            provider=p['provider'], source_family='financial', role_id=prefix, market=p['market'],
            subject=p['ticker'], endpoint_operation=operation,
            request_json=wire_identity(req, ('PLAN_CREDENTIAL',)), target_period=p['cutoff'][:10],
            mandatory=True, group_id=key, page_ordinal=1, max_pages=1, document_ordinal=1,
            max_documents=1, timeout_seconds=p['timeout_seconds'],
            transient_retry_max=p['maximum_retries_per_request'], raw_path=f'raw/{key}/source.body',
            normalizer=owner, consumer_role=prefix, owner_sha256=owner_sha256,
            config_identity_sha256=config_sha256, response_binding=rule))
        return key
    def binding(kind, parents, **kw):
        return ResponseBinding(kind=kind, parents=parents, policy_json=encoded(p).decode(),
                               policy_sha256=digest(p), **kw)
    if p['market'] == 'us':
        discovery = add('discovery', 'discovery', f'https://data.sec.gov/submissions/CIK{p["issuer"]}.json')
        add('companyfacts', 'companyfacts', f'https://data.sec.gov/api/xbrl/companyfacts/CIK{p["issuer"]}.json')
        for ordinal in range(1, p['limits']['current'] + p['limits']['prior'] + 1):
            base = f'https://www.sec.gov/Archives/edgar/data/{int(p["issuer"])}/000000000000000000/'
            if p['limits']['indexes_per_filing']:
                index = add(f'filing{ordinal}:index', 'index', base + 'index.json',
                    rule=binding('SEC_INDEX', (discovery,), selection_ordinal=ordinal))
            primary = add(f'filing{ordinal}:primary', 'document', base + 'primary.htm',
                rule=binding('SEC_PRIMARY', (discovery,), selection_ordinal=ordinal))
            for exhibit in range(1, p['limits']['linked_exhibits'] + 1):
                add(f'filing{ordinal}:exhibit{exhibit}', 'document', base + f'exhibit{exhibit}.htm',
                    rule=binding('SEC_EXHIBIT', (discovery, index, primary),
                                 selection_ordinal=ordinal, item_ordinal=exhibit))
    else:
        parents = []
        for page in range(1, p['limits']['discovery'] + 1):
            params = dict(corp_code=p['issuer'], bgn_de=p['begin'].replace('-', ''),
                end_de=p['cutoff'][:10].replace('-', ''), pblntf_ty='A', last_reprt_at='N', page_count=100, page_no=page)
            parents.append(add('discovery' + str(page), 'discovery', 'https://opendart.fss.or.kr/api/list.json',
                params=params, rule=binding('DART_NEXT_PAGE', tuple(parents)) if page == 2 else None))
        for ordinal in range(1, p['limits']['current'] + p['limits']['prior'] + 1):
            for basis in ('CFS', 'OFS'):
                add(f'filing{ordinal}:{basis}', 'statement', 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json',
                    params=dict(corp_code=p['issuer'], bsns_year='0000', reprt_code='00000', fs_div=basis),
                    rule=binding('DART_STATEMENT', tuple(parents), selection_ordinal=ordinal, basis=basis))
    if len(result) != p['maximum_logical_requests']:
        raise ValueError('financial_slot_budget_parity')
    return tuple(result)
