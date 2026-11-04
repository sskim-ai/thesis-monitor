"""Manual isolated daily replay entrypoint, default no-send and no model calls.

Authority remains with original refresh, Composite and research-review owners.
The controller persists append-only cycle receipts; it does not open a network,
start a service, grant current data rights or reconstruct an accepted AI receipt.
"""
from copy import deepcopy
import json
from zoneinfo import ZoneInfo
from app.services.vnext_daily_delta import completed_session
from app.services.unified_runtime_v2 import scheduled_slots
from app.services.vnext_research_store import digest
from app.services.vnext_public_refresh_ingestion import ingest
from app.services.vnext_research_ingestion import AppendResearchStore, current_identity
from app.services.vnext_composite_research import CompositeView
from app.services.vnext_optional_fy1_research import ReviewOwner
from app.services.vnext_research_v3 import evidence_contract
from app.services.vnext_incremental_replay import SealedPublicReplay, release_inventory

CONTRACT = 'isolated-daily-research-controller-v1'
STAGES = ('business', 'valuation', 'timing')
MODEL_CONTRACT = 'vnext-economic-timing-research-v4'


def slot_state(market, at):
    session=completed_session(market,at)
    local=at.astimezone(ZoneInfo('Asia/Seoul'))
    slots=scheduled_slots(market,local.date())
    phase=next((name for name,stamp in reversed(list(zip(('COLLECT','RECOVER','FINAL'),slots))) if at>=stamp),None)
    return dict(market=market,session=session,phase=phase if session else None,
                cycle_group=digest([market,session]) if session else None,
                pending_only=session is None or phase is None,send=False,
                reason='NO_COMPLETED_SESSION' if session is None else 'BEFORE_FIRST_SLOT' if phase is None else 'MANUAL_REPLAY_ONLY')


def stage_of(field):
    if field.startswith('financial.'):
        return 'business'
    if field.startswith('valuation.'):
        return 'valuation'
    return 'timing'


class UseRegistry:
    """Live parent-owned scoped revocations. Public JSON cannot grant a use."""
    def __init__(self):
        self._revoked = set()

    def revoke(self, security, source_sha, use='PUBLIC_RESEARCH_REFERENCE_ONLY',
               source_generation='*', field='*', scope='SOURCE'):
        if not all(isinstance(v,str) and v for v in (security,source_sha,use,source_generation,field)) or scope!='SOURCE':
            raise ValueError('explicit_source_revocation_scope_required')
        self._revoked.add((security, source_sha, use, source_generation, field, scope))

    def revoked(self, security, evidence):
        use=evidence.get('allowed_use','PUBLIC_RESEARCH_REFERENCE_ONLY')
        sources=[(evidence['source_sha'],evidence.get('original_run',evidence.get('source_generation','*')))]
        proof=evidence.get('provenance',{})
        sources += [(d['raw_sha256'],d['run_id']) for d in proof.get('dependencies',[])+proof.get('dependency_closure',[])]
        return any(sec==security and sha==h and u==use and gen in ('*',g)
                   and f in ('*',evidence.get('field'))
                   for sec,sha,u,gen,f,_ in self._revoked for h,g in sources)

    def fingerprint(self):
        return digest(sorted(self._revoked))

    def denials(self):
        return sorted(self._revoked)


def stage_state(packet, registration, registry):
    """Called on cold, original-owner-verified Composite bytes, not request JSON."""
    if not isinstance(registry, UseRegistry):
        raise ValueError('live_scoped_use_registry_required')
    sec=packet['public_security']; security=sec['canonical_security_id']
    from app.services.vnext_composite_research import PUBLIC_ID
    if any(sec.get(k)!=registration['security'].get(k) for k in PUBLIC_ID):
        raise ValueError('stage_registration_identity_mismatch')
    contracts=evidence_contract(packet)
    entries=[]
    for e in packet['evidence']:
        status=('REVOKED' if registry.revoked(security,e) else
                'QUALITY_DENIED' if e['data'].get('quality_valid') is False else
                'SHORT_HISTORY' if e['status']=='SHORT_HISTORY' else
                'VALID_LAST_QUALIFIED_RESEARCH' if contracts[e['ref']]['eligible'] else
                'EMPTY_CURRENT' if e['data'].get('state')=='CURRENT_SOURCE_EMPTY_AT_RETRIEVAL' else
                'NOT_CHECKED' if e['status']=='NOT_ATTEMPTED' else
                'MISSING' if e['status']=='MISSING_SOURCE' else 'DENIED')
        entries.append(dict(ref=e['ref'],field=e['field'],stage=stage_of(e['field']),state=status,
            raw_sha=e['source_sha'],source_generation=e['original_run'],as_of=e['reviewed_at'],
            receipt=e['provenance']['original_receipt_sha256'],scope=e['scope'],data=e['data'],
            use=e.get('allowed_use'),lineage=contracts[e['ref']]['lineage_group']))
    result={}
    for stage in STAGES:
        fields=[e for e in entries if e['stage']==stage]
        eligible=[e for e in fields if e['state']=='VALID_LAST_QUALIFIED_RESEARCH']
        if stage=='business':
            enough=bool(eligible)
        elif stage=='valuation':
            enough=bool(eligible)
        else:
            # Narrow price display does not authorize technical entry/stop claims.
            closes={e['data'].get('calendar',{}).get('session') for e in eligible if e['field']=='completed_close'}
            charts={e['data'].get('calendar',{}).get('session') for e in eligible if e['field']=='ohlcv.adjusted_daily'}
            enough=bool((closes&charts)-{None})
            attachment=packet.get('price_attachment',{})
            from app.services.vnext_timeframe_views import CONTRACT as VIEW_CONTRACT
            if (attachment.get('timeframe_view_policy')==VIEW_CONTRACT and
                    attachment.get('status') in ('DATED_CHART_REFERENCE','DATED_TIMEFRAME_REFERENCE')):
                admitted_views=attachment.get('timeframe_views',{})
                enough=enough or any(v['session'] in closes and v['permitted_indicators'] and
                    not any(registry.revoked(security,e) for e in packet['evidence']
                            if e['source_sha']==v['parent_raw_sha256'])
                    for v in admitted_views.values())
                fields=fields+[dict(field='technical.contiguous_view',ref='view:'+v['consumer_input_sha256'],
                    state=('REVOKED' if any(registry.revoked(security,e) for e in packet['evidence']
                        if e['source_sha']==v['parent_raw_sha256']) else 'VALID_LAST_QUALIFIED_RESEARCH'),
                    view_sha256=v['consumer_input_sha256'],timeframe=tf,
                    permitted_indicators=v['permitted_indicators'],strict_direction=False)
                    for tf,v in sorted(admitted_views.items())]
        effective=dict(security=registration['security'],registration_version=registration['registration_version'],
            model_contract=MODEL_CONTRACT,model='gpt-6-astra',effort='xhigh',stage=stage,fields=fields)
        result[stage]=dict(signature=digest(effective),fields=fields,source_eligible=enough,
            reason='BOUNDED_DATED_RESEARCH_ONLY' if enough else 'STAGE_WAIT_SOURCE',
            source_current=False,live_model_admitted=False,strict_direction=False)
    return result


def stage_actions(previous, current):
    result={}
    for stage in STAGES:
        old=previous.get(stage,{});cur=current[stage]
        dirty=old.get('signature')!=cur['signature']
        has_revoked=any(e['state']=='REVOKED' for e in cur['fields'])
        action=('REUSE_VALID_PRIOR' if not dirty else
                'CHANGED_NOT_ADMITTED' if cur['source_eligible'] else
                'REVOKED_DEPENDENCY' if has_revoked else 'STAGE_WAIT_SOURCE')
        result[stage]=dict(dirty=dirty,source_eligible=cur['source_eligible'],
            inference_admitted=False,action=action,reason=cur['reason'],actual_model_calls=0,
            revoked_fields=[e['ref'] for e in cur['fields'] if e['state']=='REVOKED'],
            prior_verdict_reusable=None,model_dependency_status='NOT_CHECKED')
    return result


def _counts(store):
    with store.connect() as c:
        return {t:c.execute('SELECT count(*) FROM '+t).fetchone()[0]
                for t in ('research_run','source_capture','research_observation','research_meta')}


def _journal(store, key, request, result):
    with store.atomic_job(key,request) as cell:
        if cell['previous']:
            if cell['previous']['result']!=result:
                raise ValueError('cycle_result_idempotency_conflict')
        cell['result']=result


def _persistent_registry(store, registry):
    """Monotone deny ledger; a restart cannot forget a scoped revocation."""
    with store.connect() as c:
        receipts=c.execute('SELECT value FROM research_meta WHERE key LIKE ?',
            ('vnext-runtime-v1:job:scope-revocation-%',)).fetchall()
    known=set()
    for (raw,) in receipts:
        receipt=json.loads(raw)
        if receipt['status']!='COMMITTED':raise ValueError('revocation_journal_not_committed')
        for scope in receipt['result']['scopes']:
            known.add(tuple(scope));registry.revoke(*scope)
    new=set(registry.denials())-known
    if new:
        scopes=[list(s) for s in sorted(new)]
        _journal(store,'scope-revocation-'+digest(scopes)[:40],dict(scopes=scopes),dict(scopes=scopes))


def compact_message(code, session, checked, actions, *, audit_ref, event_kind='COLD_REUSE_SAME_DIGEST'):
    """Project validated text only. No stance or numeric values are synthesized."""
    if checked and checked.get('balanced_contract') in ('RESEARCH_BALANCED_DECISION_V1','RESEARCH_BALANCED_POLICY_V2'):
        if checked['balanced_contract'] == 'RESEARCH_BALANCED_POLICY_V2':
            from app.services.vnext_balanced_research_v2 import render
        else:
            from app.services.vnext_balanced_research import render
        if not all(v.get('prior_verdict_reusable') is True for v in actions.values()):
            raise ValueError('balanced_whole_verdict_reuse_required')
        if checked['balanced']['projection']['security']['ticker'] != code:
            raise ValueError('balanced_message_security_mismatch')
        return render(checked) + '\nAudit: ' + audit_ref + '\n'
    rendered=checked['rendered'] if checked else {}
    lines=[f'# {code} | {session}', '미발송 연구 요약 · 원래 분석 시점 유지 · 실제 보유정보 미사용']
    names={'business':'사업','valuation':'가치평가','timing':'가격·시점'}
    changed=[names[k] for k,v in actions.items() if v['dirty']]
    if event_kind not in ('COLD_REUSE_SAME_DIGEST','ORIGINAL_NEW_SOURCE_AND_PRIMARY_GENERATION'):
        raise ValueError('unknown_research_event_kind')
    unchanged=('이번 조회는 동일 입력의 재시작 검증입니다. 원래 수집·분석 시점은 유지됩니다.' if checked else
               '입력 변화 없음. 기존 AI 판단의 현재 사용 가능 여부는 별도 검증.')
    event_text=('원래 실행에서 새 원본과 새 AI 연구 분석을 생성했습니다. 이 표시는 새 재수집을 뜻하지 않습니다.'
                if event_kind=='ORIGINAL_NEW_SOURCE_AND_PRIMARY_GENERATION' else ', '.join(changed) if changed else unchanged)
    lines+=['변경: '+event_text]
    if rendered and actions['business']['action']=='REUSE_VALID_PRIOR' and actions['business'].get('prior_verdict_reusable') is not False:
        lines+=['사업: '+rendered['provisional_business_signal'], '반론·위험: '+rendered['counterevidence']]
    else:
        lines+=['사업: 현재 사용할 수 있는 AI 판단 없음 ('+actions['business']['model_dependency_status']+').']
    if rendered and actions['valuation']['action']=='REUSE_VALID_PRIOR' and actions['valuation'].get('prior_verdict_reusable') is not False:
        lines+=['가치평가: '+rendered['valuation_expectations']]
    if rendered and all(v['action']=='REUSE_VALID_PRIOR' for v in actions.values()):
        lines+=['신규 매수자: '+rendered['newbuyer']['assessment'],
                '가상 보유자: '+rendered['holder']['assessment'],
                '판단 변경 근거: '+rendered['missing_next_fact']]
    else:
        lines+=['신규 매수자·가상 보유자: 변경 입력에 대한 새 AI 판단은 미실행.']
    lines+=['감사 원문: '+audit_ref]
    return '\n\n'.join(lines)+'\n'


def run_cycle(config, *, owner, as_of, phase, frozen, registry, previous=None,
              fail_after_append=False, dependency_resolver=None):
    """One app entrypoint: owned replay -> append -> cold view -> reuse/stub.

    `frozen` is a backend resolver returning original ReviewOwner, packet, and
    message bytes. No serialized receipt is accepted. This version deliberately
    supports isolated execution only; enabling production is a separate change.
    """
    if config.environment!='test' or config.mode!='write':
        raise ValueError('isolated_replay_only_no_shared_database_write')
    if not isinstance(owner,SealedPublicReplay) or not isinstance(registry,UseRegistry):
        raise ValueError('live_parent_capabilities_required')
    if phase not in ('COLLECT','RECOVER','FINAL') or not callable(frozen):
        raise ValueError('cycle_phase_or_frozen_backend')
    b=owner.batch();store=AppendResearchStore(config);before=_counts(store)
    _persistent_registry(store,registry)
    # Recheck actual source semantics before any accepted observation is appended.
    source_proofs={code:owner.verify_subject(code) for code in b['registrations']}
    intent=dict(contract=CONTRACT,batch=owner.pin,as_of=as_of,registrations=b['registrations'])
    key=digest(intent)
    _journal(store,'intent-'+key[:40],intent,dict(status='PRECOMMIT',send=False))
    # Preserve original run IDs, acquisition times and receipts; no NG relabel.
    ingest(config,owner=owner.owner,job_id='source-'+owner.pin[:40],approved_batch_sha256=owner.pin)
    after_append=_counts(store)
    if fail_after_append:
        raise RuntimeError('injected_crash_after_original_append')
    view=CompositeView(store,as_of=as_of)
    rows={};errors={};historical_views={}
    for code in sorted(b['registrations']):
        try:
            registration=current_identity(store,code)
            if registration!=b['registrations'][code]:raise ValueError('cycle_registration_changed')
            source_proof=source_proofs[code]
            packet=view.packet(code)
            current=stage_state(packet,registration,registry)
            # Existing frozen outputs must be backed by every same owned field.
            model_owner,model_packet,message,audit_ref=frozen(code)
            if not isinstance(model_owner,ReviewOwner):raise ValueError('original_live_research_owner_required')
            base=model_packet['base']
            if base['public_security']['canonical_security_id']!=packet['public_security']['canonical_security_id']:
                raise ValueError('frozen_model_security_mismatch')
            historical_runs=tuple(r['run_id'] for r in base['source_runs'] if r['run_id'] in view.runs)
            historical_key=(base['as_of'],historical_runs)
            if historical_key not in historical_views:
                historical_views[historical_key]=CompositeView(store,as_of=base['as_of'],run_ids=list(historical_runs))
            recorded={e['record_id']:e for e in historical_views[historical_key].packet(code)['evidence']}
            for e in base['evidence']:
                if e['field'].startswith('valuation.') and e['data'].get('contract')=='kis-reviewed-multisource-research-v1':
                    continue
                if e['record_id'] not in recorded or recorded[e['record_id']]!=e:
                    raise ValueError('cold_source_and_frozen_model_evidence_mismatch')
            baseline=stage_state(base,registration,UseRegistry()) if previous is None else previous.get(code,{})
            actions=stage_actions(baseline,current)
            checked=None
            dependency=dict(status='PRIOR_RESULT_DEPENDENCY_UNVERIFIED',reusable=False)
            if dependency_resolver is not None:
                from app.services.vnext_model_dependencies import WholeVerdictDependencies
                bound=WholeVerdictDependencies(model_owner,registration=registration,
                    prompts=dependency_resolver(code))
                dependency=bound.review(packet,registry=registry,registration=registration)
                if dependency['reusable']:
                    checked=bound.consume(packet,registry=registry,registration=registration)
            for action in actions.values():
                action.update(prior_verdict_reusable=dependency['reusable'],model_dependency_status=dependency['status'])
            sessions=[e['data'].get('calendar',{}).get('session') for e in packet['evidence'] if e['field']=='completed_close']
            session=next((x for x in sessions if x),None)
            text=compact_message(code,session,checked,actions,audit_ref=audit_ref)
            subject=dict(security=packet['public_security'],registration_version=registration['registration_version'],
                session=session,source_proof=source_proof,composite_sha256=digest(packet),stages=current,actions=actions,
                model_dependency=dependency,
                raw_live_new=False,model_new=0,model_reused=bool(checked and all(x['action']=='REUSE_VALID_PRIOR' for x in actions.values())),
                frozen_message_sha256=digest(message),message=text,message_sha256=digest(text),
                source_as_of=packet['as_of'],original_model_as_of=base['as_of'],send=False,strict_ready=False,
                private_thesis_included=False,holdings_included=False)
            # Fingerprint excludes slot and replay wall clock; same cycle is one message.
            msgkey=digest([CONTRACT,registration['security']['country'],session,registration['registration_version'],
                           owner.pin,registry.fingerprint(),{s:v['signature'] for s,v in current.items()},subject['message_sha256']])
            _journal(store,'message-'+msgkey[:40],dict(fingerprint=msgkey),dict(message_sha256=subject['message_sha256'],send=False))
            rows[code]=subject
        except (ValueError,KeyError,TypeError) as exc:
            errors[code]=dict(first_blocker=str(exc),type=type(exc).__name__,send=False,model_new=0)
    with store.connect() as c:
        prior_release=c.execute('SELECT value FROM research_meta WHERE key=?',
            ('vnext-runtime-v1:job:release-'+owner.pin[:40],)).fetchone()
    old_events=[] if prior_release is None else [dict(event_id=x) for x in json.loads(prior_release[0])['result']['event_ids']]
    discovery=release_inventory(owner,previous=old_events)
    _journal(store,'release-'+owner.pin[:40],dict(batch=owner.pin),dict(event_ids=sorted({e['event_id'] for e in discovery['events']}),
        state='SEALED_INVENTORY_PENDING_CURRENT_DISCOVERY',send=False))
    _journal(store,'cycle-'+digest([key,registry.fingerprint()])[:40],dict(intent=intent,revocations=registry.fingerprint()),
        dict(status='COMPLETE' if not errors else 'SCOPED_ERRORS',messages={k:v['message_sha256'] for k,v in rows.items()},errors=errors,send=False))
    after=_counts(store)
    return dict(contract=CONTRACT,phase=phase,cycle_key=key,subjects=rows,errors=errors,
        actual_inserts={k:after[k]-before[k] for k in before},source_inserts={k:after_append[k]-before[k] for k in before},
        release_inventory=discovery,trace=['ORIGINAL_REVIEWED_SOURCE','INCREMENTAL_SEALED_REPLAY','APPEND_COMMITTED',
            'COLD_COMPOSITE','STAGE_OWNER_ADMISSION','ORIGINAL_MODEL_REUSE_OR_STUB','NO_SEND_MESSAGE'],
        new_AI_messages=0,financial_HTTP=0,shared_DB_writes=0,scheduler_active=False,send=False,
        execution_mode='SEALED_PUBLIC_OFFLINE_REPLAY_NOT_LIVE_CYCLE')
