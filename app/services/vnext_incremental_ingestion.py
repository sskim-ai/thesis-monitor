"""Owner-reviewed daily deltas into the existing isolated append/cold route.

No network, registration mutation, model, scheduler or shared-DB permission is
created here. Original captures and their birth times are never relabelled.
"""
from copy import deepcopy
from datetime import datetime
import json
from app.services.vnext_research_store import digest,encoded
from app.services.vnext_public_refresh_ingestion import ReviewedPublicRefresh,ingest,CONTRACT as REFRESH
from app.services.vnext_incremental_replay import SealedPublicReplay,merge_daily,capture_occurrence
from app.services.vnext_research_ingestion import AppendResearchStore,current_identity
from app.services.vnext_composite_research import CompositeView,instant
from app.services.vnext_public_capture import target_session

CONTRACT='owned-incremental-daily-research-v1'
PRICE_FIELDS={'completed_close','ohlcv.adjusted_daily'}


def _caps(batch):
    return {(c['run_id'],c['raw_sha']):c for c in batch['captures']}


def replay_merge(bundle,prior,tail):
    """Cold reproof over exact parent CAS, never caller-rehashed projections."""
    if (tail.get('kind') != 'CURRENT_CHART_REPLAY' or
            tail.get('contract') == CONTRACT or
            prior.get('contract') == CONTRACT and prior['basis'] != bundle['basis'] or
            any(p['request_body'].get(k) != bundle['request_body'].get(k)
                for p in (prior, tail) for k in ('stk_cd','stex_tp','upd_stkpc_tp','exrt_tp')) or
            any(p['calendar']['calendar'] != bundle['basis']['calendar'] for p in (prior,tail)) or
            prior['calendar']['session'] > tail['calendar']['session'] or
            tail['calendar'] != bundle['calendar']):
        raise ValueError('delta_parent_basis_or_time_mismatch')
    expected=merge_daily(prior['selected'],tail['selected'],market=bundle['market'],
        session=bundle['calendar']['session'],previous_basis=bundle['basis'],tail_basis=bundle['basis'],
        requested_rows=bundle['requested_rows'],correction_reason=bundle['correction_reason'])
    if (bundle['contract']!=CONTRACT or expected!=bundle['merge'] or
        bundle['selected']!=expected['rows'] or
        prior['request_body']['stk_cd']!=bundle['request_body']['stk_cd'] or
        tail['request_body']['stk_cd']!=bundle['request_body']['stk_cd']):
        raise ValueError('delta_original_merge_projection_mismatch')
    return expected


class DailyDeltaOwner:
    """Trusted bootstrap supplies original replay capabilities, not request JSON."""
    def __init__(self,prior,current,*,as_of,parser_root=None,parser_pins=None,correction_reason=None):
        if not isinstance(prior,SealedPublicReplay) or not isinstance(current,SealedPublicReplay):
            raise ValueError('original_daily_owner_capabilities_required')
        self.prior=prior;self.current=current;self.as_of=as_of
        self.parser_root=parser_root;self.parser_pins=parser_pins
        self.correction_reason=correction_reason;self._revoked=False
        self._pin=digest(self.batch())

    def revoke(self):self._revoked=True

    def batch(self):
        if self._revoked:raise ValueError('delta_owner_revoked')
        old,new=self.prior.batch(),self.current.batch()
        if not 0<len(new['registrations'])<=2 or len(new['runs'])!=1:
            raise ValueError('bounded_daily_delta_scope')
        if any(o['field'] not in PRICE_FIELDS for o in new['observations']):
            raise ValueError('daily_delta_field_scope')
        if {r['run_id'] for r in old['runs']}&{r['run_id'] for r in new['runs']}:
            raise ValueError('separate_source_generation_required')
        oldcaps,newcaps=_caps(old),_caps(new);out=deepcopy(new)
        oldbirth=max(instant(c['receipt']['captured_at']) for c in old['captures'])
        born=[c for c in new['captures'] if c['receipt'].get('raw_birth')=='CURRENT_HTTP']
        if not born or any(instant(c['receipt']['captured_at'])<=oldbirth or
            instant(c['receipt']['captured_at'])>instant(self.as_of) for c in born):
            raise ValueError('independent_later_capture_required')
        for code,registration in new['registrations'].items():
            if old['registrations'].get(code)!=registration:raise ValueError('delta_registration_mismatch')
            self.prior.verify_subject(code);self.current.verify_subject(code)
            market=registration['security']['country'];target,_=target_session(market.lower(),datetime.fromisoformat(self.as_of))
            previous=[o for o in old['observations'] if o['ticker']==code and o['field'] in PRICE_FIELDS]
            latest=max(o['payload']['calendar']['session'] for o in previous)
            if str(target)<latest or str(target)==latest and not self.correction_reason:
                raise ValueError('new_completed_session_or_explicit_correction_required')
            for o in [o for o in out['observations'] if o['ticker']==code]:
                p=o['payload'];cap=newcaps[o['run_id'],o['source_sha']]
                if p['calendar']['session']!=str(target):raise ValueError('delta_completed_session_mismatch')
                captured_target,_=target_session(market.lower(),datetime.fromisoformat(cap['receipt']['captured_at']))
                if captured_target!=target:raise ValueError('delta_capture_before_session_close')
                if p.get('source_captured_at')!=cap['receipt']['captured_at']:
                    raise ValueError('delta_original_capture_time_mismatch')
                if o['field']=='completed_close':
                    # Existing original close validator was re-entered above.
                    if market=='US' and cap not in born:raise ValueError('independent_original_close_receipt_required')
                    if market=='US':
                        request=json.loads(cap['receipt']['request']['body'])
                        exchange={'NYSE':'NY','NASDAQ':'ND','AMEX':'NA'}.get(registration['security']['exchange'])
                        if not exchange or request.get('stex_tp')!=exchange:raise ValueError('delta_close_exchange_binding')
                    continue
                if self.parser_root is None or self.parser_pins is None:
                    raise ValueError('original_chart_parser_capability_required')
                from app.services.vnext_price_capture import parse_original
                tail=json.loads(cap['raw']);parsed=[]
                request=tail['request_body']
                if request.get('upd_stkpc_tp')!=('1' if p['adjusted'] else '0'):
                    raise ValueError('delta_request_adjustment_binding')
                if market=='US' and request.get('stex_tp')!={'NYSE':'NY','NASDAQ':'ND','AMEX':'NA'}.get(registration['security']['exchange']):
                    raise ValueError('delta_chart_exchange_binding')
                for page in tail['pages']:
                    parent=capture_occurrence(new['captures'],o['run_id'],page['raw_sha256'],
                        captured_at=page['captured_at'],request_body=request)
                    if parent not in born:raise ValueError('new_chart_original_page_required')
                    parsed.extend(parse_original(json.loads(parent['raw']),market.lower(),'daily',self.parser_root,self.parser_pins)['rows'])
                dates=[r['date'] for r in parsed]
                if len(dates)!=len(set(dates)) or dates not in (sorted(dates),sorted(dates,reverse=True)):
                    raise ValueError('delta_page_order_or_duplicates')
                selected=sorted((r for r in parsed if r['date']<=str(target)),key=lambda r:r['date'])[-tail['requested_rows']:]
                if selected!=tail['selected']:raise ValueError('delta_original_parser_projection')
                candidates=[x for x in previous if x['field']==o['field']]
                prior=max(candidates,key=lambda x:(x['payload']['calendar']['session'],
                    instant(oldcaps[x['run_id'],x['source_sha']]['receipt']['captured_at']))) if candidates else None
                if prior is None:raise ValueError('incremental_prior_chart_missing')
                priorraw=json.loads(oldcaps[prior['run_id'],prior['source_sha']]['raw'])
                if prior['payload']['adjusted']!=p['adjusted']:raise ValueError('delta_adjustment_changed')
                basis=dict(security=registration['security']['canonical_security_id'],currency='KRW' if market=='KR' else 'USD',
                    adjusted=p['adjusted'],calendar=p['calendar']['calendar'],role='daily')
                merge=merge_daily(priorraw['selected'],selected,market=market,session=str(target),
                    previous_basis=basis,tail_basis=basis,requested_rows=priorraw['requested_rows'],correction_reason=self.correction_reason)
                bundle=dict(contract=CONTRACT,market=market,calendar=p['calendar'],basis=basis,
                    request_body=tail['request_body'],requested_rows=priorraw['requested_rows'],
                    selected=merge['rows'],merge=merge,correction_reason=self.correction_reason,
                    parents=[dict(run_id=prior['run_id'],raw_sha256=prior['source_sha']),
                             dict(run_id=o['run_id'],raw_sha256=o['source_sha'])],
                    source_generation_kind='INDEPENDENT_CAPTURE_DELTA_NOT_SEALED_SPLIT',strict_native=False)
                raw=encoded(bundle).decode();sha=digest(raw.encode());run=o['run_id'];key=digest(bundle['parents'])
                out['captures'].append(dict(run_id=run,provider='IncrementalDailyReplay',request_key=key,
                    capture_id=digest([run,'IncrementalDailyReplay',key]),raw=raw,raw_sha=sha,
                    receipt=dict(captured_at=cap['receipt']['captured_at'],kind='DERIVED_CROSS_GENERATION_DELTA',strict_native=False)))
                o.update(source_sha=sha,observation_id=digest([run,code,o['field'],sha]),
                    status='SOURCE_REFERENCE' if merge['status']=='MERGED_RESEARCH_WINDOW' else
                        'SHORT_HISTORY' if merge['status']=='SHORT_HISTORY' else 'POLICY_DENIED')
                o['payload']=dict(p,rows=merge['merged_rows'],requested_rows=priorraw['requested_rows'],
                    selected_rows=merge['rows'] if merge['quality']['valid'] else [],quality_valid=merge['quality']['valid'],
                    reason=merge['status'],source_captured_at=cap['receipt']['captured_at'])
        if not out['observations']:raise ValueError('delta_observation_required')
        if hasattr(self,'_pin') and digest(out)!=self._pin:raise ValueError('delta_owner_input_drift')
        return out


def ingest_delta(config,*,owner,fail_after_append=False):
    from app.services.vnext_daily_research import _counts,_journal
    if config.environment!='test' or config.mode!='write':raise ValueError('isolated_delta_only_shared_not_authorized')
    if not isinstance(owner,DailyDeltaOwner):raise ValueError('live_delta_owner_required')
    b=owner.batch();store=AppendResearchStore(config);before=_counts(store)
    # All prior parents must already exist; never re-import a sealed full batch.
    prior=owner.prior.batch();view=CompositeView(store,as_of=owner.as_of,tickers=list(b['registrations']))
    for code,registration in b['registrations'].items():
        if current_identity(store,code)!=registration:raise ValueError('delta_current_registration')
    needed={(o['run_id'],o['source_sha']) for o in prior['observations']
            if o['ticker'] in b['registrations'] and o['field'] in PRICE_FIELDS}
    for c in (c for c in prior['captures'] if (c['run_id'],c['raw_sha']) in needed):
        proof=view.source(c['run_id'],c['raw_sha'])
        if proof['original_receipt_sha256']!=digest(c['receipt']):raise ValueError('delta_prior_receipt_mismatch')
    key=digest(dict(contract=CONTRACT,batch=digest(b),registrations=b['registrations']))
    _journal(store,'delta-intent-'+key[:40],dict(key=key),dict(state='PRECOMMIT',send=False))
    result=ingest(config,owner=ReviewedPublicRefresh(owner.batch),job_id='delta-source-'+key[:40],approved_batch_sha256=digest(b))
    if fail_after_append:raise RuntimeError('injected_delta_crash_after_commit')
    cold=CompositeView(AppendResearchStore(config),as_of=owner.as_of,tickers=list(b['registrations']))
    packets={code:cold.packet(code) for code in b['registrations']}
    for o in b['observations']:
        if not any(e['record_id']==o['observation_id'] for e in packets[o['ticker']]['evidence']):
            raise ValueError('delta_not_selected_by_cold_consumer')
    _journal(store,'delta-terminal-'+key[:40],dict(key=key),dict(state='COLD_READ_VERIFIED',
        packets={k:digest(v) for k,v in packets.items()},send=False))
    after=_counts(store)
    return dict(contract=CONTRACT,cycle_key=key,result=result,packets=packets,
        actual_inserts={k:after[k]-before[k] for k in before},shared_DB_writes=0,
        source_generation_kind='INDEPENDENT_CAPTURE_DELTA_NOT_SEALED_SPLIT',
        real_network_proof='REQUIRES_TASK_PHYSICAL_LEDGER_NOT_INFERRED_FROM_RECEIPT_JSON')


def run_delta_cycle(config,*,owner,registry,phase,dependency_owners=None):
    from app.services.vnext_daily_research import stage_state,stage_actions,_persistent_registry,_journal,_counts
    if phase not in ('COLLECT','RECOVER','FINAL'):raise ValueError('delta_cycle_phase')
    if config.environment!='test' or config.mode!='write':raise ValueError('isolated_delta_only_shared_not_authorized')
    store=AppendResearchStore(config);before=_counts(store);_persistent_registry(store,registry)
    b=owner.batch();codes=list(b['registrations']);oldruns=[r['run_id'] for r in owner.prior.batch()['runs']]
    prior=CompositeView(store,as_of=owner.as_of,run_ids=oldruns,tickers=codes)
    initial={code:stage_state(prior.packet(code),b['registrations'][code],registry) for code in codes}
    result=ingest_delta(config,owner=owner);subjects={}
    for code,packet in result['packets'].items():
        registration=b['registrations'][code];stages=stage_state(packet,registration,registry)
        actions=stage_actions(initial[code],stages)
        dep=(dependency_owners or {}).get(code)
        model=dep.review(packet,registry=registry,registration=registration) if dep else dict(status='PRIOR_RESULT_DEPENDENCY_UNVERIFIED',reusable=False)
        checked=dep.consume(packet,registry=registry,registration=registration) if model['reusable'] else None
        for action in actions.values():action.update(prior_verdict_reusable=model['reusable'],model_dependency_status=model['status'])
        session=next(e['data']['calendar']['session'] for e in packet['evidence'] if e['field'] in PRICE_FIELDS)
        from app.services.vnext_daily_research import compact_message
        text=compact_message(code,session,checked,actions,audit_ref='original retained verdict; not rewritten')
        text+='\nSource event: '+session+'; new source generation '+b['runs'][0]['run_id']+'.\n'
        text+='\nNo new AI judgment; no send; hypothetical Holder only.\n'
        revision=digest([result['cycle_key'],registration['registration_version'],registry.fingerprint(),
                         {s:v['signature'] for s,v in stages.items()},model,digest(text)])
        _journal(store,'delta-message-'+revision[:40],dict(revision=revision),dict(message_sha256=digest(text),send=False))
        subjects[code]=dict(stages=stages,actions=actions,model=model,message=text,message_sha256=digest(text),
            source_session=session,source_generation=b['runs'][0]['run_id'],strict_ready=False,new_AI=0)
    after=_counts(store)
    return dict(result,subjects=subjects,phase=phase,total_inserts={k:after[k]-before[k] for k in before},
        actual_model_calls=0,send=False,scheduler=False)
