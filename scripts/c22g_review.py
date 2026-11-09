"""Whitelist-only C22G review archives; never include prompts or private logs."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import zipfile
from datetime import datetime,timezone
from scripts.c22g_batch import ROOT, OUT, ARCHIVE, SOURCE_SHA, TICKERS, encoded, digest
from app.services.dated_research_model import load_bound_view, reference_catalog, validate_output

def secret_scan(name,raw):
    assert not name.startswith('/') and '..' not in Path(name).parts
    assert not any(s in name.lower() for s in ('prompt.private','events.private','stderr.private','.env','.sqlite','.db','auth.json'))
    text=raw.decode('utf-8')
    assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bsk-[A-Za-z0-9]{25,}',text),name

def seal(name,files):
    for n,b in files.items():secret_scan(n,b)
    manifest=dict(scheme='SHA256 payload members; MANIFEST excludes itself',files={n:dict(bytes=len(b),sha256=digest(b)) for n,b in sorted(files.items())})
    files=dict(files);files['MANIFEST.json']=encoded(manifest)
    path=OUT/name
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):z.writestr(n,b)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        for n,r in manifest['files'].items():assert len(z.read(n))==r['bytes'] and digest(z.read(n))==r['sha256']
    assert path.stat().st_size<=100_000_000
    path.with_suffix('.zip.sha256').write_text(digest(path.read_bytes())+'  '+name+'\n')
    return dict(filename=name,bytes=path.stat().st_size,sha256=digest(path.read_bytes()),CRC='PASS',memberSHA='PASS')

def blind():
    files={};index={};audits={}
    c22c=ROOT/'maintenance/20261109-c22c/C22C_ALL_DELIVERABLES.zip'
    assert digest(c22c.read_bytes())=='9e0e68559036e71e66758b76eff3507912773e463cec0209016f081e1a8f6782'
    with zipfile.ZipFile(ARCHIVE) as z,zipfile.ZipFile(c22c) as c:
        for n in z.namelist():
            if n.startswith('US_SOURCE_EVIDENCE/'):
                b=z.read(n)
                if '/captures/' in n:
                    receipt=json.loads(b)['receipt']
                    assert receipt['auth'] is False
                    assert not set(receipt['request']['query'])-{'symbol','metric'}
                    assert not any(k.lower() in {'authorization','cookie','set-cookie','x-api-key'} for k in receipt['response_headers'])
                files['SOURCE_EVIDENCE/'+n]=b
        comparisons=json.loads(z.read('COMPARISON_ORIGINALS.json'))
        files['SOURCE_EVIDENCE/FINANCIAL_COMPARISON_CAPTURES.json']=encoded(comparisons)
        for ticker in TICKERS:
            v,b=load_bound_view(ARCHIVE,expected_zip_sha256=SOURCE_SHA,ticker=ticker)
            original=z.read('ORIGINAL_INPUTS/'+ticker+'.json');viewraw=z.read('C22D_V2_INVESTMENT_RESEARCH_INPUTS/'+ticker+'.json')
            cat=reference_catalog(v);base='CASES/'+ticker+'/'
            files[base+'ORIGINAL_INPUT.json']=original;files[base+'RESEARCH_VIEW.json']=viewraw
            files[base+'REFERENCE_CATALOG.json']=encoded(cat)
            cpacket=json.loads(c.read('investment-inputs/'+ticker+'.json'))
            old=json.loads(original)
            assert old['technical']==cpacket['technical']
            financial=[]
            for row in v['financial_observations']:
                f=row['original_fields']; raw_sha=f.get('original_raw_sha256')
                match=[e['evidence'] for e in comparisons if e['ticker']==ticker and e['evidence']['ref']==row['original_ref']]
                evidence=match[0] if match else None
                lineage=[]
                if evidence:
                    deps=evidence['data'].get('field_dependency_receipts',{}).get('comparison',{})
                    for role,field in [('current','current_value'),('comparison','prior_comparable_value')]:
                        lin=deps.get(role,{}).get('lineage')
                        if lin:
                            lineage.append(dict(role=role,lineage=lin,amount_matches_projected=lin.get('amount')==f.get(field)))
                financial.append(dict(ref=row['original_ref'],field=row['field'],source_sha256=row['source_sha'],
                    values_and_semantics=f,original_quality=row['original_quality'],comparison_capture_available=bool(evidence),
                    capture_lineage_checks=lineage,provider_raw_sha256=raw_sha,
                    provider_raw_comparison='NOT_VERIFIED_FROM_PROVIDER_RAW',
                    economic_scale_validity='DATA_QUALITY_REVIEW_REQUIRED',
                    period_and_scale_review='Provider raw/current-prior scale, quarter versus YTD and annual week count need review; no values changed.'))
            valuation=[]
            for row in v['valuation']:
                fact=row['original_fact'];r=dict(original_fact=fact,value=row['value'],source_locator=row['source_locator'])
                source='US_SOURCE_EVIDENCE/raw/'+str(fact.get('raw_sha256'))
                if source in z.namelist() and fact.get('provider')=='finnhub':
                    body=json.loads(z.read(source));r['raw_field_equal']=body['symbol']==ticker and body['metric'][fact['provider_field']]==row['value']
                    assert r['raw_field_equal']
                else:r['raw_field_equal']='NOT_VERIFIED_FROM_PROVIDER_RAW'
                valuation.append(r)
            missing=dict(status='DATA_QUALITY_REVIEW_REQUIRED',source_binding=b,technical_source_sha256=v['input_provenance']['technical_source_sha256'],
                economic_source_sha256=v['input_provenance']['economic_original_source_sha256'],
                original_provider_financial_raw='Not present in the supplied C22D review archive; original financial captures/lineages are included where preserved. No new collection or DB lookup performed.',
                limits=['Projected field equality does not establish economic scale validity.',
                  'Quarter/YTD, unit_scale, 53/52-week definitions and unusually large reported amounts/growth remain unresolved where provider raw is unavailable.',
                  'Dated native evidence and nulls retained; no current-price authority.',
                  'Business cause, market expectations and occurred risk remain subject to their original evidence limits.'],
                source_metadata=old.get('source_and_missing_field_metadata'),missing_original=old['economic'].get('missing_original'),
                missing_history_original=old['economic'].get('missing_history_original'))
            files[base+'PROVENANCE_AND_MISSING.json']=encoded(missing)
            audits[ticker]=dict(as_of=v['as_of'],financial=financial,valuation=valuation,
                financial_count=len(financial),comparison_count=sum(x['role']=='QUANTITATIVE_COMPARISON' for x in v['financial_observations']),
                reference_count=len(cat['refs']),numeric_fact_count=len(cat['numeric_facts']),
                technical_source_equality=True,technical_evidence_rows=len(v['technical']['evidence']),
                technical_context_quality=v['technical']['technical_context_quality'],
                missing_mechanism_count=v['verified_mechanism_count'],market_expectation_sources=v['market_expectations']['source_evidence'],
                occurred_risk_assertion=v['structural_risk']['occurred_risk_assertion'],
                financial_raw_audit_status='DATA_QUALITY_REVIEW_REQUIRED')
            index[ticker]=dict(**b,original_bytes=len(original),research_view_bytes=len(viewraw),
                reference_catalog_sha256=digest(encoded(cat)),preserved_source_provenance=v['input_provenance'],
                C22C_archive_sha256=digest(c22c.read_bytes()),C22C_member='investment-inputs/'+ticker+'.json',
                C22C_member_sha256=digest(c.read('investment-inputs/'+ticker+'.json')))
    assert sum(x['financial_count'] for x in audits.values())==33
    assert sum(x['comparison_count'] for x in audits.values())==9
    files['SOURCE_ARCHIVE_INDEX.json']=encoded(dict(source_zip_sha256=SOURCE_SHA,cases=index))
    files['FINANCIAL_VALUATION_TECHNICAL_AUDIT.json']=encoded(dict(status='DATA_QUALITY_REVIEW_REQUIRED',cases=audits,new_collection=0,values_modified=0))
    files['README_FIRST_BLIND.md']=('''# 먼저 읽을 원본 입력
이 ZIP만 열어 독립 검토를 작성하고 INDEPENDENT_BLIND_ASSESSMENT.md 및 SHA256을 먼저 봉인하세요.
MU/000660/047810/CORZ가 독립 검토 대상입니다. 삼성전자는 이전 의견 노출 사례로 별도 증거 감사하세요.
이 파일은 날짜 명시 연구 입력입니다. 공급자 원문 배율·분기/YTD·53/52주 검증 결손은 DATA_QUALITY_REVIEW_REQUIRED이며 추측으로 수정하지 않았습니다.
원본/연구뷰는 C22D 봉인 bytes 그대로, refs 및 numeric_facts는 기존 reference_catalog 함수 결과 전체입니다.
공급자 금융 원문이 이 봉인에 없는 곳은 comparison capture/lineage까지 제공하며 실물 원문 검증으로 간주하지 않습니다.
NO-SEND. 현재가·등록 투자 Thesis·거래 권한을 제공하지 않습니다.
''').encode()
    return seal('C22G_V2_BLIND_INPUTS_ONLY.zip',files)

def results():
    status=json.loads((OUT/'BATCH_STATUS.json').read_bytes());files={};bindings={};events={};comparison=[]
    prior=ROOT/'maintenance/20261109-c22f-v2/live-once/private-evidence/accepted-BLIND.json'
    if prior.exists():files['CASES/005930/BLIND_ACCEPTED_C22F.json']=prior.read_bytes()
    for r in status['stages']:
        t=r['ticker'];stage=r['stage'];label='ADJ' if stage=='ADJUDICATION' else stage
        d=OUT/'live'/t/stage;base='CASES/'+t+'/'+label+'/'
        if d.exists():
            files[base+'VALIDATION_RECEIPT.json']=(d/'RECEIPT.json').read_bytes()
            for local,target in [('response.json','RESPONSE_RAW.json'),('accepted.json','ACCEPTED.json')]:
                if (d/local).exists():files[base+target]=(d/local).read_bytes()
            if not (d/'response.json').exists():files[base+'NO_RESPONSE.json']=encoded(dict(status='NO_RESPONSE',prompt_sha256=r['prompt_sha256'],failure=r.get('failure_code')))
            v,b=load_bound_view(ARCHIVE,expected_zip_sha256=SOURCE_SHA,ticker=t);cat=reference_catalog(v)
            row=dict(binding=b,catalog=cat,raw_sha256=r.get('response_sha256'),accepted_sha256=r.get('accepted_sha256'))
            if (d/'accepted.json').exists():
                accepted=validate_output((d/'response.json').read_bytes(),view=v,binding=b,stage=stage,catalog=cat)
                assert encoded(accepted)==(d/'accepted.json').read_bytes()
                row['citations']=accepted['citations'];row['axes']={k:accepted[k] for k in ('overall','newbuyer','holder_virtual')}
                comparison.append(dict(ticker=t,stage=stage,axes=row['axes'],adjudication_change_reason=accepted['adjudication_change_reason']))
            bindings[t+'/'+stage]=row;events[t+'/'+stage]=r.get('events',[])
    files['BATCH_STATUS.json']=encoded(status)
    files['BINDINGS_AND_CITATION_AUDIT.json']=encoded(dict(cases=bindings,prior_005930='PRIOR_RESULT_EXPOSED',raw_prior_sha256='5ec650cd61cba3b67c57412bcc53a1d2a156713d376ae75a86d87f4dc938d307',accepted_prior_sha256='d9c6c511bf963bc4149e9a37b579413e92a0696a55a70898e80546fccd779134'))
    files['CLI_EVENTS_AND_USAGE_SAFE.json']=encoded(dict(stages=events,native_HTTP_attempts='UNKNOWN',native_stream_reconnects='UNKNOWN',credits='UNKNOWN',wrapper_retries=0))
    files['BLIND_VS_ADJ_COMPARISON.md']=('# 원문 기준 비교\n\n'+json.dumps(comparison,ensure_ascii=False,indent=2)+'\n').encode()
    files['C22G_V2_BATCH_RESULT.json']=encoded(status)
    files['C22G_V2_BATCH_RESULT.md']=('# C22G v2 연구 배치\n\n'+json.dumps(status,ensure_ascii=False,indent=2)+'\n\nNO-SEND. 모델 수락은 경제적 정확성이나 운영 READY를 뜻하지 않습니다.\n').encode()
    files['README_OPEN_ONLY_AFTER_INDEPENDENT_BLIND.md']=('''# 독립 판단 봉인 후 열기
먼저 BLIND_INPUTS_ONLY ZIP만으로 독립 판단 문서와 SHA256을 확정한 후 이 ZIP을 여세요.
실제 응답 JSON 원문 bytes, 전체 수락 JSON 및 citations를 제공합니다. 요약만으로 대체하지 않았습니다.
005930은 PRIOR_RESULT_EXPOSED입니다. 나머지 사례는 독립 판단 봉인 뒤 대조하세요.
공유 runner/로그인/권한/쿼터/도구/봉인 결함은 전체 중단, 국소 의미 거절은 해당 ADJ만 생략합니다.
금융 원문 배율·기간 검증 결손은 DATA_QUALITY_REVIEW_REQUIRED로 유지하며 모델 수락으로 해소되지 않습니다.
전체 프롬프트, 인증, private 이벤트 본문, 개인 Thesis 및 보유정보를 제외했습니다.
토큰은 관측 이벤트만 제공하며 실제 내부 요청·재시도·과금은 UNKNOWN입니다. NO-SEND, Strict READY 0/22.
''').encode()
    return seal('C22G_V2_MODEL_RESULTS_REVIEW.zip',files)

def control(receipts):
    w=ROOT/'work/thesis-monitor-c22g-v2-20261109'
    files={}
    for n in ['pre-gc-decision.json','PREFLIGHT.json','FOCUSED_TESTS_INITIAL.xml','FOCUSED_TESTS_CORRECTION.xml','FOCUSED_REVIEW_TESTS.xml','ARCHIVE_CHECK.json','BATCH_STATUS.json','BATCH_STARTED.json','GIT_STATE.json','FIRST_FAILURES.json']:
        if (OUT/n).exists():files[n]=(OUT/n).read_bytes()
    for n in ['scripts/c22g_batch.py','scripts/c22g_review.py','tests/test_c22g_batch.py','tests/test_c22g_review.py']:
        files['code/'+n]=(w/n).read_bytes()
    files['CODE.diff']=subprocess.check_output(['git','diff','e9ed74665752bccb60def380b6d9d28416ecaff1','HEAD','--', 'scripts/c22g_batch.py','scripts/c22g_review.py','tests/test_c22g_batch.py','tests/test_c22g_review.py'],cwd=w)
    files['REVIEW_ZIP_BINDINGS.json']=encoded(receipts)
    files['README_PRESERVATION_ONLY_AFTER_BLIND.md']=b'Open only after independent BLIND assessment is sealed. Review ZIPs remain separate and are bound by SHA256 here. No nested prior archives. NO-SEND.\n'
    for n in ('TM_C22G_V2_INDEPENDENT_BLIND_REVIEW_PROTOCOL_20261109.md','TM_C22G_V2_REVIEW_ARCHIVE_CHECK.py'):
        files[n]=(OUT/n).read_bytes()
    return seal('C22G_V2_ALL_DELIVERABLES.zip',files)

if __name__=='__main__':
    import sys
    if '--blind-only' in sys.argv:
        receipt=blind();(OUT/'BLIND_SEAL.json').write_bytes(encoded(receipt));print('INPUT_ARCHIVE_SEALED')
    else:
        receipts=[json.loads((OUT/'BLIND_SEAL.json').read_bytes()),results()]
        spec=importlib.util.spec_from_file_location('checker',OUT/'TM_C22G_V2_REVIEW_ARCHIVE_CHECK.py')
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        audits=[checker.input_audit(OUT/receipts[0]['filename'],ARCHIVE),checker.result_audit(OUT/receipts[1]['filename'])]
        assert all(not a['errors'] for a in audits)
        (OUT/'ARCHIVE_CHECK.json').write_bytes(encoded(dict(status='PASS',audits=audits)))
        receipts.append(control(receipts));(OUT/'SEALS.json').write_bytes(encoded(receipts));print('THREE_ARCHIVES_SEALED')
