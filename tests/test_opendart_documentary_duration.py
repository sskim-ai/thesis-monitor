"""Synthetic custody/semantic boundaries; real sealed replay is task evidence.

Fixture pins simulate the trusted capture composition root. A matching hash is
not official-source authority, and these fixtures never qualify a real issuer.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import zipfile

import pytest

from app.services.opendart_documentary_duration import (
    DocumentaryDurationInput, load_admitted_documentary_capture,
    reconcile_documentary_duration,
)
from app.services.opendart_financial_recovery_service import (
    FIELD_SPECS, promote_recovered_fields, select_basis_occurrence,
)
from test_opendart_financial_recovery_service import _filing, _rows

TITLE = '\uc5f0\uacb0 \ud604\uae08\ud750\ub984\ud45c'
LABEL = '\uc601\uc5c5\ud65c\ub3d9\uc73c\ub85c \uc778\ud55c \ud604\uae08\ud750\ub984'
MEMBERS = {k:k for k in ('index_raw','index_receipt','section_raw','section_receipt')}


def wire(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True).encode()


def stamp(raw):
    return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())


def case(ticker='UNSEEN',corp='00123456',value='700'):
    f=replace(_filing(),ticker=ticker,corp_code=corp)
    sec=dict(ticker=ticker,corp_code=corp,country='KR',canonical_security_id='KR:'+ticker,
             canonical_company_id='DART:'+corp)
    row=dict(corp_code=corp,rcept_no=f.receipt_no,reprt_code='11012',bsns_year='2026',
        sj_div='CF',account_id='ifrs-full_CashFlowsFromUsedInOperatingActivities',
        account_nm=LABEL,account_detail='-',thstrm_amount=value,frmtrm_q_amount='100',currency='KRW')
    q=dict(rcpNo=f.receipt_no,dcmNo='12345',eleId='23',offset='800',length='1000',tocNo='23',dtd='dart4.xsd')
    node=dict(q,text='2-4. '+TITLE)
    index=(f'<span onclick="openCorpInfoNew(\'{corp}\', \'winCorpInfo\', \'/dsae001/selectPopup.ax\');"></span>'
        f'<button onclick="openPdfDownload(\'{f.receipt_no}\', \'12345\');"></button>'
        f'<option selected value="rcpNo={f.receipt_no}"></option><script>var node1 = {{}};'+
        ''.join(f'node1[\'{k}\'] = {json.dumps(v,ensure_ascii=False)};' for k,v in node.items())+'</script>')
    period=lambda y:f'\uc81c {y-2000} \uae30 \ubc18\uae30 {y}.01.01 \ubd80\ud130 {y}.06.30 \uae4c\uc9c0'
    tr=lambda cells:'<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>'
    section='<table>'+''.join(tr([c]) for c in [TITLE,period(2026),period(2025),'(\ub2e8\uc704 : \uc6d0)'])+'</table>'
    section+='<table>'+tr(['','\uc81c 26 \uae30 \ubc18\uae30','\uc81c 25 \uae30 \ubc18\uae30'])
    section+=tr([LABEL,value,'100'])+tr(['Working capital','-300','-100'])+'</table>'
    receipt=lambda path,params,start,end:dict(method='GET',HTTP_status=200,error=None,follow_redirects=False,
        credentials_used=False,retries=0,source_owner_issued=False,response_headers={'content-type':'text/html; charset=utf-8'},
        authorization_sha256='a'*64,started_at=start,finished_at=end,source_generation='document-generation',
        url='https://dart.fss.or.kr'+path,params=params)
    ir=receipt('/dsaf001/main.do',dict(rcpNo=f.receipt_no),'2026-10-31T08:00:00Z','2026-10-31T08:00:01Z')
    sr=receipt('/report/viewer.do',q,'2026-10-31T08:01:00Z','2026-10-31T08:01:01Z')
    sr['parent']=dict(relationship='ORIGINAL_DART_LITERAL_INDEX_NODE',title=node['text'])
    return dict(filing=f,security=sec,row=row,index=index,section=section,ir=ir,sr=sr,
        generation='execution-generation',cutoff='2026-10-31T09:00:00Z',source_cutoff='2026-10-26T00:00:00Z')


def seal(tmp_path,c,*,after=None):
    data={k:c[k[:-4]].encode() for k in ('index_raw','section_raw')}
    ir,sr=deepcopy(c['ir']),deepcopy(c['sr'])
    for r,k in ((ir,'index_raw'),(sr,'section_raw')):
        r.update(body_bytes=len(data[k]),body_sha256=sha256(data[k]).hexdigest())
    sr['parent'].update(bytes=ir['body_bytes'],sha256=ir['body_sha256'])
    if after:after(ir,sr)
    data.update(index_receipt=wire(ir),section_receipt=wire(sr))
    p=tmp_path/'synthetic-admitted.zip'
    with zipfile.ZipFile(p,'w') as z:
        for k,b in data.items():z.writestr(k,b)
        z.writestr('manifest.json',wire(dict(members={k:stamp(b) for k,b in data.items()})))
    return load_admitted_documentary_capture(archive=p,admitted_archive_sha256=sha256(p.read_bytes()).hexdigest(),
        members=MEMBERS,security=c['security'],execution_generation=c['generation'],review_cutoff=c['cutoff'])


def resolve(c,h,raw=None):
    spec=FIELD_SPECS['operating_cash_flow']
    selected=select_basis_occurrence([c['row']],spec,basis='CFS')
    return reconcile_documentary_duration(selected,spec,c['filing'],h,security=c['security'],
        original_raw=raw or wire(dict(status='000',list=[c['row']])),source_generation='api-generation',
        source_cutoff=c['source_cutoff'])


@pytest.mark.parametrize('ticker,corp,value',[('UNSEEN','00123456','700'),('OTHER','00987654','-700'),('ZERO','00876543','0')])
def test_generic_exact_h1_through_original_owner(tmp_path,ticker,corp,value):
    c=case(ticker,corp,value);h=seal(tmp_path,c)
    before=promote_recovered_fields(c['filing'],{'CFS':[c['row']]})
    assert before['fields']['operating_cash_flow']['reason']=='structured_cash_flow_period_ambiguous'
    actual=promote_recovered_fields(c['filing'],{'CFS':[c['row']]},documentary_input=h,
        documentary_context=dict(security=c['security'],original_raw=wire(dict(status='000',list=[c['row']])),
            source_generation='api-generation',source_cutoff=c['source_cutoff']))
    f=actual['fields']['operating_cash_flow']['lineage'];p=f['documentary_reconciliation']
    assert f['amount']==int(value) and f['amount_period_type']=='year_to_date_cumulative'
    assert (f['amount_period_start'],f['amount_period_end'])==('2026-01-01','2026-06-30')
    assert 'xbrl_context_ref' not in f and p['current_qualified'] is False
    assert p['counterevidence_rows'][0]['current']=='-300'
    assert p['cells'][1]['value']=='100' and p['independent_corroboration'] is False
    assert promote_recovered_fields(c['filing'],{'CFS':[c['row']]})==before


MUTATIONS=[
    'wrong_corp','wrong_security','wrong_company','wrong_filing','wrong_report','wrong_section',
    'wrong_document','wrong_parent','cover','missing_raw','raw_amount','raw_duplicate','unit','scale',
    'label','duplicate_row','duplicate_table','start','end','columns','ofs','correction','future_filing',
    'missing_date','external','redirect','revoked','superseded','source_spoof','execution_generation',
    'source_generation','captured_future','capture_order','receipt_hash','receipt_bytes','receipt_method',
    'receipt_status','receipt_type','receipt_authorization','missing_header','zero_corruption',
    'negative_corruption','decimal_rounding','duplicate_index','wrong_index_company','parent_receipt',
]


@pytest.mark.parametrize('mutation',MUTATIONS)
def test_exact_boundary_rejects(tmp_path,mutation):
    c=case();after=None;raw=None
    if mutation=='wrong_corp':c['row']['corp_code']='00999999'
    elif mutation=='wrong_security':c['filing']=replace(c['filing'],ticker='OTHER')
    elif mutation=='wrong_company':c['security']['canonical_company_id']=''
    elif mutation=='wrong_filing':c['row']['rcept_no']='20260814000002'
    elif mutation=='wrong_report':c['filing']=replace(c['filing'],report_code='11013')
    elif mutation=='wrong_section':c['sr']['params']['eleId']='24'
    elif mutation=='wrong_document':c['sr']['params']['dcmNo']='99999'
    elif mutation=='wrong_parent':c['sr']['parent']['title']='cover'
    elif mutation=='cover':c['section']='<p>Cover only</p>'
    elif mutation=='missing_raw':raw=b'{"status":"000","list":[]}'
    elif mutation=='raw_amount':raw=wire(dict(status='000',list=[dict(c['row'],thstrm_amount='701')]))
    elif mutation=='raw_duplicate':raw=wire(dict(status='000',list=[c['row'],c['row']]))
    elif mutation=='unit':c['row']['currency']='USD'
    elif mutation=='scale':c['section']=c['section'].replace('\ub2e8\uc704 : \uc6d0','\ub2e8\uc704 : \ubc31\ub9cc\uc6d0')
    elif mutation=='label':c['section']=c['section'].replace(LABEL,'Cash generated')
    elif mutation=='duplicate_row':c['section']=c['section'].replace('</table>','<tr><td>'+LABEL+'</td><td>700</td><td>100</td></tr></table>')
    elif mutation=='duplicate_table':c['section']+=c['section']
    elif mutation=='start':c['section']=c['section'].replace('2026.01.01','2026.04.01')
    elif mutation=='end':c['section']=c['section'].replace('2026.06.30','2026.06.29')
    elif mutation=='columns':c['section']=c['section'].replace('<td>700</td><td>100</td>','<td>100</td><td>700</td>')
    elif mutation=='ofs':c['section']=c['section'].replace(TITLE,'\ubcc4\ub3c4 \ud604\uae08\ud750\ub984\ud45c')
    elif mutation=='correction':c['filing']=replace(c['filing'],correction=True)
    elif mutation=='future_filing':c['source_cutoff']='2026-08-13T00:00:00Z'
    elif mutation=='missing_date':c['source_cutoff']=''
    elif mutation=='external':c['sr']['url']='https://example.com/report/viewer.do'
    elif mutation=='redirect':c['sr']['follow_redirects']=True
    elif mutation in ('revoked','superseded'):c['sr'][mutation]=True
    elif mutation=='source_spoof':c['sr']['source_owner_issued']=True
    elif mutation=='execution_generation':c['generation']='api-generation'
    elif mutation=='source_generation':c['sr']['source_generation']='wrong-generation'
    elif mutation=='captured_future':c['cutoff']='2026-10-30T00:00:00Z'
    elif mutation=='capture_order':c['sr']['started_at']='2026-10-31T07:00:00Z'
    elif mutation=='receipt_hash':after=lambda ir,sr:sr.update(body_sha256='0'*64)
    elif mutation=='receipt_bytes':after=lambda ir,sr:sr.update(body_bytes=1)
    elif mutation=='receipt_method':c['sr']['method']='POST'
    elif mutation=='receipt_status':c['sr']['HTTP_status']=302
    elif mutation=='receipt_type':c['sr']['response_headers']['content-type']='application/json'
    elif mutation=='receipt_authorization':c['sr']['authorization_sha256']='b'*64
    elif mutation=='missing_header':c['section']=c['section'].replace('2026.01.01','')
    elif mutation=='zero_corruption':c['section']=c['section'].replace('<td>700</td>','<td>0</td>')
    elif mutation=='negative_corruption':c['section']=c['section'].replace('<td>700</td>','<td>-700</td>')
    elif mutation=='decimal_rounding':c['section']=c['section'].replace('<td>700</td>','<td>700.000001</td>')
    elif mutation=='duplicate_index':c['index']=c['index'].replace('</script>',c['index'][c['index'].index('var node1'):])
    elif mutation=='wrong_index_company':c['index']=c['index'].replace('00123456','00999999')
    elif mutation=='parent_receipt':after=lambda ir,sr:sr['parent'].update(sha256='0'*64)
    with pytest.raises(ValueError):resolve(c,seal(tmp_path,c,after=after),raw)


def test_no_json_authority_immutable_handle_and_changed_seal(tmp_path):
    c=case();h=seal(tmp_path,c)
    with pytest.raises(ValueError,match='trusted_capture'):resolve(c,{'receipt_sha256':'a'*64})
    with pytest.raises(ValueError,match='trusted_capture'):
        DocumentaryDurationInput(None,'a','b',{}, {},'x','y')
    with pytest.raises(AttributeError):h._generation='different'
    (tmp_path/'synthetic-admitted.zip').write_bytes(b'caller replacement')
    with pytest.raises(ValueError,match='admitted_seal_changed'):resolve(c,h)


def test_failure_does_not_contaminate_other_fields(tmp_path):
    c=case();rows=_rows();rows['CFS'].append(c['row']);before=promote_recovered_fields(c['filing'],rows)
    c['section']='<p>Cover</p>'
    after=promote_recovered_fields(c['filing'],rows,documentary_input=seal(tmp_path,c),
        documentary_context=dict(security=c['security'],original_raw=wire(dict(status='000',list=rows['CFS'])),
            source_generation='api-generation',source_cutoff=c['source_cutoff']))
    for metric,original in before['fields'].items():
        if metric!='operating_cash_flow':assert after['fields'][metric]==original
    assert after['fields']['operating_cash_flow']['lineage'] is None


def test_sec_exact_context_extension_opt_in(monkeypatch,tmp_path):
    from test_vnext_cfbs_context import case as sec_case
    from app.services.vnext_financial_reuse import replay_reported_context, verify_reported_context
    args,payload=sec_case(monkeypatch,tmp_path)
    instant=deepcopy(payload['facts']['us-gaap']['Assets']['units']['USD'][0])
    for concept in ('StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
                    'MinorityInterest','CashAndCashEquivalentsAtCarryingValue'):
        payload['facts']['us-gaap'][concept]={'units':{'USD':[dict(instant,val=10)]}}
    original=replay_reported_context(**args)
    assert replay_reported_context(**args,extended_sec_fields=False)==original
    extended=replay_reported_context(**args,extended_sec_fields=True)
    assert len(extended['facts'])==len(original['facts'])+3
    for f in extended['facts']:
        assert verify_reported_context(f,args['security'])
        assert f['fields']['direction_allowed'] is False
        assert f['fields']['consolidation_explicitly_proven'] is False
