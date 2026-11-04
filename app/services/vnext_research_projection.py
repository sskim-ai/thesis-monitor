"""Replay current public charts into original research features and market children."""
from datetime import date
import json
from pathlib import Path
from app.services.vnext_research_store import digest,encoded
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from app.services.ohlcv_completed_bar_finality_service import annotate_normalized_bar
from app.services.short_history_reference import requirements
from app.services.native_completed_market import select_completed_daily_rows
from app.macro.providers.market import MARKET_SYMBOLS,normalize_market_observation

def derive_research_views(store,run_id):
    identities={r['ticker']:r for r in store.identities()}
    with store.connect() as c:
        as_of=c.execute('SELECT as_of FROM research_run WHERE run_id=?',(run_id,)).fetchone()[0]
        captures=c.execute("SELECT raw_sha,raw_path,receipt_json FROM source_capture WHERE run_id=? AND provider='ChartReplay'",(run_id,)).fetchall()
    selected={}
    for sha,path,receipt in captures:
        raw=Path(path).read_bytes()
        if digest(raw)!=sha:raise ValueError('chart_replay_source_drift')
        data=json.loads(raw);body=data['request_body'];ticker=body['stk_cd']
        identity=next((r for t,r in identities.items() if t.replace('.','-')==ticker),None)
        if (not identity or data['calendar']['as_of']!=as_of or
                (identity['country']=='US')!=('stex_tp' in body)):
            raise ValueError('chart_replay_identity_or_cutoff')
        # The capture key is immutable; a longer resumed extent supersedes only this view.
        key=(identity['ticker'],body.get('upd_stkpc_tp'),data['requested_rows'])
        old=selected.get(key)
        if old is None or len(data['selected'])>len(old[1]['selected']):selected[key]=(sha,data,json.loads(receipt))
    ledger=[]
    for ticker,identity in identities.items():
        periods={};sources=[];cutoff=None;births=[];market_status='NOT_APPLICABLE'
        for (_,adjusted,requested),(sha,data,receipt) in selected.items():
            if data['request_body']['stk_cd']!=ticker.replace('.','-') or adjusted!='1':continue
            timeframe={1000:'daily',700:'weekly',300:'monthly'}.get(requested)
            if not timeframe:continue
            target=date.fromisoformat(data['calendar']['session']);cutoff=target
            raw_rows=data['selected'];prepared=[]
            for row in raw_rows:
                later=any(r['date']>row['date'] for r in raw_rows) or timeframe!='daily' or data['parsed_rows']>data['completed_rows']
                prepared.append(annotate_normalized_bar(row,provider='kiwoom',market=identity['country'],timeframe=timeframe,has_later_chart_row=later))
            periods[timeframe]=prepared;sources.append(sha);births.append(receipt['captured_at'])
            if timeframe=='daily' and ticker in MARKET_SYMBOLS and identity['country']=='US' and data['quality']['valid']:
                try:
                    pair=select_completed_daily_rows(raw_rows,target_session=str(target),count=2)
                    child=normalize_market_observation(dict(periods=dict(daily=pair)),symbol=ticker,source_url='kiwoom:usa06012:sha256:'+sha)
                    store.market_observation(run_id,'US',ticker,sha,dict(strict_native=False,full_market_owner=False,
                        observation=dict(child.__dict__,observed_at=child.observed_at.isoformat()),
                        source_captured_at=receipt['captured_at'],scope='EXISTING_MARKET_COMPONENT_NOT_FULL_MARKET'))
                    market_status='SOURCE_REFERENCE'
                except (ValueError,TypeError) as exc:market_status='REPLAY_DENIED_'+type(exc).__name__
        if not periods:continue
        packet=build_multi_timeframe_feature_packet(ticker=ticker,periods=periods,cutoff=cutoff)
        data=packet.model_dump(mode='json')
        available={f.semantic for f in packet.daily.facts}
        mask=[dict(semantic=name,minimum=n,status='AVAILABLE_REFERENCE' if name in available else 'UNAVAILABLE_OR_HISTORY_LIMIT') for name,n in sorted(requirements().items())]
        raw=encoded(dict(packet=data,sources=sorted(sources),daily_availability=mask,strict_native=False,original_owner_issued=False))
        sha=store.capture(run_id,'TechnicalReferenceReplay',ticker,raw,dict(captured_at=min(births),kind='DERIVED_CURRENT_SOURCE_REFERENCE'))
        store.observation(run_id,ticker,'technical.reference','SOURCE_REFERENCE',sha,dict(strict_native=False,
            source_captured_this_run=True,packet=data,daily_availability=mask,original_owner_issued=False,
            scope='RESEARCH_ONLY_NO_SIGNAL_OR_DIRECTION_GRANT'))
        ledger.append(dict(ticker=ticker,daily_available=len(available),catalog=len(mask),market_child=market_status,
            timeframes={tf:dict(safe=getattr(packet,tf).safe_feature_count,invalid=getattr(packet,tf).invalid_source_row_count,
            completed=getattr(packet,tf).completed_count,unconfirmed=getattr(packet,tf).unconfirmed_count) for tf in ('daily','weekly','monthly')}))
    return ledger
