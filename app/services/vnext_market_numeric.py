"""Original ka20009 signed-field semantics, not FullMarket authority."""
import json
from datetime import date,datetime
from app.services.vnext_research_store import digest
from app.services.kiwoom_kr_market_context_service import (
    _absolute_float,_signed_float,KiwoomKrMarketContextService,MARKETS,
)
from app.services.kiwoom_consumed_page_contract import read_dependencies

def market_catalog(packet,raw_sources):
    rows=[]
    for e in packet['evidence']:
        if not e['field'].endswith(':ka20009') or e['status']!='SOURCE_REFERENCE':continue
        market=e['field'].split(':')[0]
        if market not in MARKETS:raise ValueError('unregistered_market_index')
        raw=raw_sources.get(e['source_sha'])
        if raw is None or digest(raw)!=e['source_sha']:raise ValueError('market_raw_binding')
        b=json.loads(raw);d=e['data'];session=date.fromisoformat(d['calendar']['session'])
        deps=read_dependencies('ka20009',[b],session=session,continuation=[False])
        original=KiwoomKrMarketContextService._completed_history_row(history=b,session_date=session,observed_at=datetime.fromisoformat(d['calendar']['as_of']))
        if original!=d['row']:raise ValueError('market_original_row_drift')
        for key,method,unit,kind in (('cur_prc_n',_absolute_float,'index','level'),('flu_rt_n',_signed_float,'percent','return')):
            n=dict(fact_id=e['ref'],field_path='/data/row/'+key,value=method(original[key]),unit=unit,
                basis='ORIGINAL_KA20009_ABSOLUTE_LEVEL_SIGNED_RETURN',as_of=str(session),source_sha=e['source_sha'],
                market_label=market,observation_kind=kind,original_text=original[key],dependency_paths=deps['paths'])
            n['catalog_id']='c'+digest(n)[:16];rows.append(n)
    return rows
