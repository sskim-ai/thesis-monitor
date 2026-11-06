"""Opt-in authentic valuation facts for analysis, not Native/direction grants.

Source factories re-enter original receipt/parser paths on every consumption.
Historical protocol calibration establishes units, not estimate freshness.
"""
from copy import deepcopy
from datetime import date,datetime
from decimal import Decimal
import calendar,json,zipfile
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict,model_validator
from app.services.vnext_research_store import digest,encoded,plain
from app.services.vnext_composite_research import CompositeView,PUBLIC_ID,instant

CONTRACT='VALUATION_ANALYSIS_FACT_V1'
SCOPE='OVERALL_CONTEXT_NEWBUYER_HOLDER_VALUATION_NOT_STANDALONE_DIRECTION'


class ValuationAnalysisFact(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    contract: Literal['VALUATION_ANALYSIS_FACT_V1']=CONTRACT
    metric: Literal['PER','PBR','FPER','FY1_EPS']
    ticker: str
    canonical_security_id: str
    provider: str
    value: float
    exact_value: str
    unit: str
    metric_semantic: str
    source_generation: str
    raw_sha256: str
    source_receipt_sha256: str
    retrieval_timestamp: str
    forecast_fiscal_period: str | None=None
    estimate_vintage: str | None=None
    estimated: bool=False
    scale_proof_sha256: str | None=None
    basis: str
    caution: str
    display_eligible: Literal[True]=True
    analysis_scope: Literal['OVERALL_CONTEXT_NEWBUYER_HOLDER_VALUATION_NOT_STANDALONE_DIRECTION']=SCOPE
    overall_direction_use: Literal[False]=False
    formal_native: Literal[False]=False
    send: Literal[False]=False

    @model_validator(mode='after')
    def valid(self):
        n=Decimal(self.exact_value)
        if not n.is_finite() or float(n)!=self.value or not self.basis:
            raise ValueError('analysis_value_basis')
        instant(self.retrieval_timestamp)
        if any(len(s)!=64 or any(c not in '0123456789abcdef' for c in s)
               for s in (self.raw_sha256,self.source_receipt_sha256)):
            raise ValueError('analysis_original_hash')
        if self.metric in ('PER','PBR','FPER') and n<=0:raise ValueError('analysis_nonpositive_ratio')
        if self.metric=='FY1_EPS' and (self.unit!='KRW_PER_SHARE' or not self.estimated
                or not self.forecast_fiscal_period or not self.scale_proof_sha256):
            raise ValueError('analysis_eps_unit_period_scale')
        return self


def calibration_from_archive(path,expected_sha256):
    from scripts.kis_fy1_semantic_owner import Documentation,Evidence
    from scripts.kis_output3_protocol_owner import _protocol
    raw=plain(path).read_bytes()
    if digest(raw)!=expected_sha256:raise ValueError('analysis_calibration_archive_changed')
    with zipfile.ZipFile(path) as z:
        manifest=json.loads(z.read('result/bundle-manifest.json'))
        def member(n):
            b=z.read('result/'+n)
            if manifest[n]!={'bytes':len(b),'sha256':digest(b)}:
                raise ValueError('analysis_calibration_member_changed')
            return b
        historical=json.loads(member('kis-plan.json'));items={}
        for name in ('estimate-docs.json','protocol.json'):
            b=member('static/kis/'+name)
            if digest(b)!=historical['static_hashes'][name]:raise ValueError('analysis_calibration_plan_changed')
            items[name]=b
    docs=Documentation(Evidence(items['estimate-docs.json'],digest(items['estimate-docs.json'])))
    protocol=json.loads(items['protocol.json']);_protocol(protocol,docs)
    return docs,protocol


def parse_analyst_eps(*,ticker,security,estimate,identity,receipt,generation,as_of,docs,protocol):
    """Narrow product policy. No renewed filing/activation or formal FY1 claim."""
    import re
    from scripts.kis_fy1_semantic_owner import LAYOUT,period_pattern
    from scripts.kis_output3_protocol_owner import _protocol,partial_binding
    from scripts.kis_eps_wire_calibration import number,decimal_string,valid_full_layout
    if estimate.get('rt_cd')!='0' or identity.get('rt_cd')!='0':raise ValueError('analysis_provider_quality')
    if not estimate.get('output3'):raise ValueError('analysis_no_forecast')
    represented=(estimate.get('output1') or {}).get('sht_cd','')
    normalized=represented[1:] if re.fullmatch('A[0-9]{6}',represented) else represented
    short=(identity.get('output') or {}).get('shtn_pdno')
    if normalized!=ticker or short!=ticker or security['ticker']!=ticker:
        raise ValueError('analysis_security_contradiction')
    _protocol(protocol,docs)
    periods=period_pattern(estimate);actual=max(p[:2] for p in periods if not p[2])
    when=date.fromisoformat(as_of[:10]);candidates=[]
    for i,(year,month,marker) in enumerate(periods):
        end=date(year,month,calendar.monthrange(year,month)[1])
        if marker=='E' and (year,month)>actual and end>=when:candidates.append(i)
    if not candidates:raise ValueError('analysis_no_applicable_FY1')
    column=candidates[0];rows=estimate['output3']
    if valid_full_layout(rows):index=LAYOUT.index('EPS')
    else:
        from scripts.kis_fy1_semantic_owner import Evidence
        partial=partial_binding(Evidence(encoded(estimate),digest(encoded(estimate))),docs,protocol)
        if partial['state']!='QUALIFIED':raise ValueError('analysis_ambiguous_EPS_row')
        index=partial['row_index']
    n=number(rows[index][f'data{column+1}'])
    if n is None:raise ValueError('analysis_missing_EPS')
    exact=decimal_string(n*number(protocol['factors']['EPS']))
    vintage=datetime.strptime(estimate['output1']['estdate'],'%Y%m%d').date()
    acquired=instant(receipt['ended_at'])
    if vintage>acquired.date() or acquired>instant(as_of):raise ValueError('analysis_future_estimate')
    return ValuationAnalysisFact(metric='FY1_EPS',ticker=ticker,
        canonical_security_id=security['canonical_security_id'],provider='KIS',value=float(Decimal(exact)),
        exact_value=exact,unit='KRW_PER_SHARE',metric_semantic='KIS_ANALYST_FY1_EPS',
        source_generation=generation,raw_sha256=receipt['raw_sha256'],source_receipt_sha256=digest(receipt),
        retrieval_timestamp=receipt['ended_at'],forecast_fiscal_period=estimate['output4'][column]['dt'],
        estimate_vintage=vintage.isoformat(),estimated=True,scale_proof_sha256=protocol['receipt_sha256'],
        basis='KIS_RETURNED_ANNUAL_LABELS_AND_ORIGINAL_CALIBRATED_OUTPUT3_EPS',
        caution='Dated KIS analyst estimate, not actual earnings/company guidance; source capture is not estimate vintage.')


class AnalysisSource:
    def __init__(self,read):self._read=read
    def read(self):return self._read()


def kis_source(*,root,plan,calibration_archive,calibration_sha256,as_of):
    root=plain(root);frozen=deepcopy(plan)
    def read():
        from app.services.kis_estimate_source_contract import cold_source
        proof=cold_source(root,frozen)
        if len(proof['rows'])!=16:raise ValueError('analysis_KIS_source_incomplete')
        docs,protocol=calibration_from_archive(calibration_archive,calibration_sha256)
        facts=[];denials=[]
        for ticker,security in frozen['securities'].items():
            estimate=json.loads(plain(root/'estimate'/(ticker+'.body')).read_bytes())
            identity=json.loads(plain(root/'identity'/(ticker+'.body')).read_bytes())
            receipt=json.loads(plain(root/'estimate'/(ticker+'-receipt.json')).read_bytes())
            try:fact=parse_analyst_eps(ticker=ticker,security=security,estimate=estimate,identity=identity,
                receipt=receipt,generation=frozen['generation_id'],as_of=as_of,docs=docs,protocol=protocol)
            except (ValueError,KeyError) as exc:denials.append(dict(ticker=ticker,reason=str(exc)));continue
            facts.append(fact)
        return frozen['securities'],facts,denials
    return AnalysisSource(read)


def _native_fact(data,security,generation):
    return ValuationAnalysisFact(metric='FPER' if data['metric']=='FORWARD_PE' else data['metric'],
        ticker=security['ticker'],canonical_security_id=security['canonical_security_id'],
        provider=data['provider'],value=data['value'],exact_value=str(data['value']),
        unit=data.get('unit','multiple'),metric_semantic=data['metric_semantic'],source_generation=generation,
        raw_sha256=data['raw_sha256'],source_receipt_sha256=data['snapshot_sha256'],
        retrieval_timestamp=data['retrieval_timestamp'],basis=data.get('basis') or data['metric_semantic'],
        caution='Provider-native ratio with original as-of/denominator limitations; no standalone direction or current-price grant.')


def matched_fper(eps,*,original_eps=None,price=None,actions=None):
    """Use original price/action arithmetic only for an exactly matching EPS.

    Never derive a close or a share basis from a provider ratio. Missing support
    denies this metric alone, not the authentic EPS or atomic PER/PBR facts.
    """
    from scripts.kis_current_fy1_owner import current_fper
    if type(eps) is not ValuationAnalysisFact or eps.metric!='FY1_EPS':
        raise ValueError('analysis_typed_EPS_required')
    if Decimal(eps.exact_value)<=0:return dict(state='NOT_MEANINGFUL',value=None)
    if original_eps is None or price is None or actions is None:
        return dict(state='UNAVAILABLE_MATCHED_UNADJUSTED_CLOSE_AND_SHARE_BASIS',value=None)
    if (original_eps.get('estimate_sha256')!=eps.raw_sha256 or original_eps.get('security_code')!=eps.ticker
            or original_eps.get('period')!=eps.forecast_fiscal_period
            or Decimal(str(original_eps.get('value')))!=Decimal(eps.exact_value)):
        raise ValueError('analysis_original_EPS_price_match_required')
    return current_fper(original_eps,price,actions)


def native_cold_source(*,root,replay_sha256):
    def read():
        from app.vnext_worker import cold_registered_valuation_source
        result=cold_registered_valuation_source(root,expected_replay_sha256=replay_sha256)
        data=json.loads(plain(Path(root)/'original-replay.json').read_bytes())
        securities={s['ticker']:s for s in data['securities']};facts=[]
        for row in result['rows']:
            for m in row['metrics']:
                if m['display_eligible']:facts.append(_native_fact(m,securities[row['ticker']],data['frozen']['generation_id']))
        return securities,facts,[]
    return AnalysisSource(read)


def dated_native_source(bundle):
    def read():
        from app.services.dated_capture_research import dated_archive_view
        view=dated_archive_view(bundle,enabled=True);base=view.packet(bundle.ticker)
        s=base['public_security']
        facts=[_native_fact(e['data'],s,e['original_run']) for e in base['evidence']
               if e['field'].startswith('valuation.') and e['data'].get('display_eligible')]
        return {s['ticker']:s},facts,[]
    return AnalysisSource(read)


class AnalysisView(CompositeView):
    """Original Composite packet/catalog; only this opt-in view accepts new facts."""
    def __init__(self,*,sources,ticker,as_of,enabled=False):
        if enabled is not True or not sources or any(type(s) is not AnalysisSource for s in sources):
            raise ValueError('analysis_explicit_source_required')
        self.sources=tuple(sources);self.ticker=ticker;self.as_of=instant(as_of).isoformat();self.cutoff=instant(as_of)
        self.reported_context=False;self.registration_admission=None;self.valuation_analysis_owner=self
        identities=[];facts=[];self.denials=[]
        for source in self.sources:
            securities,values,denials=source.read();self.denials+=denials
            if ticker in securities:identities.append({k:securities[ticker].get(k) for k in PUBLIC_ID})
            facts.extend(f for f in values if f.ticker==ticker)
        if not identities or any(s!=identities[0] for s in identities):raise ValueError('analysis_source_identity_conflict')
        self.identities={ticker:identities[0]};self.runs={};self.proofs={};rows=[]
        for f in facts:
            if instant(f.retrieval_timestamp)>self.cutoff:raise ValueError('analysis_future_source')
            d=f.model_dump(mode='json');run=f.source_generation;sha=f.raw_sha256
            self.runs[run]=dict(run_id=run,started_at=f.retrieval_timestamp,as_of=f.retrieval_timestamp,status='ORIGINAL_SOURCE_ANALYSIS')
            self.proofs[(run,sha)]=dict(capture_id=f.source_receipt_sha256,run_id=run,origin_run=run,
                provider=f.provider,raw_sha256=sha,receipt_sha256=f.source_receipt_sha256,
                captured_at=f.retrieval_timestamp,available_at=f.retrieval_timestamp,
                receipt_kind='ORIGINAL_SOURCE_ANALYSIS_NOT_RECOLLECTED',dependencies=[])
            rows.append((digest(d),run,ticker,'valuation.'+f.metric,'SOURCE_REFERENCE',sha,
                encoded(dict(snapshot=d,strict_native=False)).decode()))
        if len({r[3] for r in rows})!=len(rows):raise ValueError('analysis_duplicate_metric_owner')
        self.rows=tuple(rows);self.snapshot_sha=digest(dict(rows=self.rows,proofs=list(self.proofs.values())))

    def _check(self):
        other=AnalysisView(sources=self.sources,ticker=self.ticker,as_of=self.as_of,enabled=True)
        if other.snapshot_sha!=self.snapshot_sha:raise ValueError('analysis_source_changed')

    def source(self,run,sha,capture_id=None):
        self._check();p=self.proofs.get((run,sha))
        if p is None or capture_id is not None and p['capture_id']!=capture_id:raise ValueError('analysis_source_receipt_missing')
        return deepcopy(p)

    def verify_snapshot(self,security,data):
        self._check();ValuationAnalysisFact.model_validate(data)
        if security!=self.identities[self.ticker] or not any(json.loads(r[6])['snapshot']==data for r in self.rows):
            raise ValueError('analysis_fact_not_source_bound')

    def packet(self,ticker):
        self._check();packet=super().packet(ticker)
        packet['run_id']='ANALYSIS_VIEW:'+self.snapshot_sha
        packet['source_generations_reissued']=False
        return packet

    def unified_premodel(self,*,registry,contract=None):
        from app.services.vnext_codex_research import numeric_catalog
        from app.services.vnext_optional_fy1_research import attach
        from app.services.vnext_unified_judgment import build_bundle,CONTRACT as DEFAULT
        base=self.packet(self.ticker);base['numeric_catalog']=numeric_catalog(base)
        return build_bundle(attach(base),registry=registry,contract=contract or DEFAULT,valuation_analysis_owner=self)

    def context(self,security):
        self._check()
        if security['canonical_security_id']!=self.identities[self.ticker]['canonical_security_id']:
            raise ValueError('analysis_context_wrong_security')
        facts=[json.loads(r[6])['snapshot'] for r in self.rows]
        return dict(contract=CONTRACT,analysis_usable=True,facts=facts,
            axes={a:deepcopy(facts) for a in ('Overall','NewBuyer','Holders')},
            standalone_direction=False,formal_native=False,strict_ready=False,send=False)
