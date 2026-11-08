"""Explicit dated-source stage review; never renew an old Primary invocation.

Backend callbacks hold source, approval and account authority. Serialized model
output or a receipt hash alone cannot create a stage capability. Economic
validation remains in the original balanced/v4 validators.
"""
from copy import deepcopy
import json
import time

from app.services import vnext_balanced_research as balanced
from app.services.vnext_optional_fy1_research import ReviewOwner
from app.services.vnext_no_send_controller import NoSendController
from app.services.vnext_research_store import digest
from app.services.vnext_execution_profile import ASTRA_XHIGH_V1, SOL_HIGH_V1, SOL_MEDIUM_V1

CONTRACT='BALANCED_STAGE_SCOPED_REVIEW_V1'
ORIGINAL='BALANCED_ORIGINAL_PROMPT_V1'
EXPLICIT='BALANCED_UNISSUED_CONFIDENCE_PROMPT_V2'
POLICY_V2='BALANCED_RESEARCH_POLICY_V2_PROMPT_V1'
DATED_TIMING='DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V1'
DATED_TIMING_V2='DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V2'
DATED_TIMING_V3='DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V3'
UNIFIED='UNIFIED_JUDGMENT_V1'
UNIFIED_AI='UNIFIED_JUDGMENT_V2_AI_OWNED'
UNIFIED_AI_V3='UNIFIED_JUDGMENT_V3_AI_OWNED'
UNIFIED_AI_V3_CITATION='UNIFIED_JUDGMENT_V3_AI_OWNED_CITATION_PROMPT_V1'
UNIFIED_AI_V3_SOL_HIGH='UNIFIED_JUDGMENT_V3_AI_OWNED_SOL_HIGH_PROMPT_V1'
UNIFIED_AI_V3_SOL_MEDIUM='UNIFIED_JUDGMENT_V3_AI_OWNED_SOL_MEDIUM_BLIND_PROMPT_V1'
SOL_VERSIONS=(UNIFIED_AI_V3_SOL_HIGH, UNIFIED_AI_V3_SOL_MEDIUM)
UNIFIED_AI_VERSIONS=(UNIFIED_AI, UNIFIED_AI_V3, UNIFIED_AI_V3_CITATION, *SOL_VERSIONS)
TIMING_V3_EXECUTION_CONTRACT='DATED_TECHNICAL_STAGE_REVIEW_V3'
INPUT_LIMIT=384*1024
OUTPUT_LIMIT=128*1024
SECONDS=600


def _engine(version):
    if version in (UNIFIED, *UNIFIED_AI_VERSIONS):
        from app.services import vnext_unified_judgment
        return vnext_unified_judgment
    if version == DATED_TIMING_V3:
        from app.services import vnext_dated_research_timing_v3
        return vnext_dated_research_timing_v3
    if version in (DATED_TIMING,DATED_TIMING_V2):
        from app.services import vnext_dated_research_timing
        return vnext_dated_research_timing
    if version == POLICY_V2:
        from app.services import vnext_balanced_research_v2
        return vnext_balanced_research_v2
    if version in (ORIGINAL, EXPLICIT):
        return balanced
    raise ValueError('stage_prompt_version')


def output_contract(version):
    return UNIFIED_AI_V3 if version in (UNIFIED_AI_V3_CITATION,*SOL_VERSIONS) else version


def execution_profile(version):
    if version == UNIFIED_AI_V3_SOL_MEDIUM:
        return SOL_MEDIUM_V1
    return SOL_HIGH_V1 if version == UNIFIED_AI_V3_SOL_HIGH else ASTRA_XHIGH_V1


def execution_contract(version):
    if version == UNIFIED_AI_V3_SOL_MEDIUM:
        return 'UNIFIED_STAGE_REVIEW_V3_SOL_61_MEDIUM_BLIND_V1'
    if version == UNIFIED_AI_V3_SOL_HIGH:
        return 'UNIFIED_STAGE_REVIEW_V3_SOL_61_HIGH_V1'
    if version in (UNIFIED_AI_V3_CITATION,UNIFIED_AI_V3_SOL_HIGH):
        return 'UNIFIED_STAGE_REVIEW_V3_AI_OWNED_CITATION_V1'
    if version == UNIFIED_AI_V3:
        return 'UNIFIED_STAGE_REVIEW_V3_AI_OWNED'
    if version == UNIFIED_AI:
        return 'UNIFIED_STAGE_REVIEW_V2_AI_OWNED'
    if version == UNIFIED:
        return 'UNIFIED_STAGE_REVIEW_V1'
    return TIMING_V3_EXECUTION_CONTRACT if version == DATED_TIMING_V3 else CONTRACT


def _v3_prior_version(prior, version):
    if prior is not None and {DATED_TIMING_V3, UNIFIED, *UNIFIED_AI_VERSIONS} & {prior.version, version} and prior.version != version:
        raise ValueError('STAGE_VERSION_MISMATCH_PRECALL')


def prompt(packet,stage,*,knowledge,registry,prior=None,version=ORIGINAL):
    if version == UNIFIED_AI_V3_SOL_MEDIUM and (stage != 'BLIND' or prior is not None):
        raise ValueError('sol_medium_blind_only')
    if version not in (ORIGINAL,EXPLICIT,POLICY_V2,DATED_TIMING,DATED_TIMING_V2,DATED_TIMING_V3,UNIFIED,*UNIFIED_AI_VERSIONS) or stage not in ('BLIND','ADJUDICATION'):
        raise ValueError('stage_prompt_version')
    if version in (DATED_TIMING,DATED_TIMING_V2,DATED_TIMING_V3,UNIFIED) and packet.get('contract')!=_engine(version).CONTRACT:
        raise ValueError('STAGE_VERSION_MISMATCH_PRECALL')
    if version in UNIFIED_AI_VERSIONS and packet.get('contract') != output_contract(version):
        raise ValueError('STAGE_VERSION_MISMATCH_PRECALL')
    extra=dict(version=DATED_TIMING_V2) if version==DATED_TIMING_V2 else {}
    if version in UNIFIED_AI_VERSIONS:extra=dict(version=output_contract(version))
    text=_engine(version).prompt(packet,stage,knowledge=knowledge,registry=registry,prior=prior,**extra)
    if version == UNIFIED_AI_V3_CITATION:
        text+='''
CITATION PROMPT V1: Before final output, check each claim independently.
Every numeric citation ref in a claim's citations must also occur in that same
claim.refs. Copy the exact observation path, value, unit, reporting period and
statement basis. A correct number cited by another claim does not satisfy this
claim's membership rule. Keep numeric facts in structured citations, not prose.
This clarifies unchanged validation; it grants no new source or economic rights.
For a SCOPED_PERIODS Technical Owner, review exactly the supplied role keys,
not absent periods. Do not claim a complete daily/weekly/monthly review from a
partial scope. Two distinct cited metrics are still required for TechnicalReview.
'''
    if version==UNIFIED_AI_V3_SOL_HIGH:
        text+='\nEXECUTION PROFILE: SOL_61_HIGH_EXECUTION_V1; gpt-6.1-sol/high.\nThe unchanged economic-policy ASTRA_ADJ tag is a legacy schema tag, not a runtime identity or an accepted-model receipt. Only the backend two-stage Sol execution Owner can issue SOL_HIGH_ADJ provenance. No source rights are extended.\n'
    if version==UNIFIED_AI_V3_SOL_MEDIUM:
        text+='\nEXECUTION PROFILE: SOL_61_MEDIUM_EXECUTION_V1; gpt-6.1-sol/medium.\nThe unchanged economic-policy ASTRA_ADJ tag is a legacy schema tag, not a runtime identity or an accepted-model receipt. This is a single BLIND stage only, not an adjudicated result or a two-stage Owner. No source rights are extended.\n'
    if version==EXPLICIT:
        text+='''
PROMPT CONTRACT: BALANCED_UNISSUED_CONFIDENCE_PROMPT_V2.
This clarifies unchanged semantic validation, not a new investment rule.
For each of balanced.valuation, balanced.overall, balanced.holder_virtual and
balanced.timing: a NOT_ISSUED or UNRESOLVED state requires confidence exactly
NOT_SEPARATELY_ISSUED. In particular, timing.state=UNRESOLVED cannot have LOW,
MEDIUM or HIGH confidence; overall.stance=NOT_ISSUED has no separate confidence.
Use LOW/MEDIUM/HIGH only when that axis actually issues an eligible judgment.
Do not force an issued judgment merely to avoid the missing-confidence rule.
Keep fundamental business, valuation, timing and VIRTUAL Holder independent.
No unsupported AVOID, optimistic quota, invented numeric fact or source-use
upgrade is allowed. This is research only, not Strict B2 or current completeness.
'''
    if len(text.encode())>INPUT_LIMIT:raise ValueError('stage_input_limit')
    return text


def output_schema(packet,version):
    if version in UNIFIED_AI_VERSIONS:
        return _engine(version).schema(security_id=packet['base']['public_security']['canonical_security_id'],contract=output_contract(version))
    if version in (DATED_TIMING_V2,DATED_TIMING_V3,UNIFIED):
        return _engine(version).schema(security_id=packet['base']['public_security']['canonical_security_id'])
    return _engine(version).schema()


def _stage_request(*,invocation_id,account,packet,stage,version,knowledge,registry,prior):
    if version == UNIFIED_AI_V3_SOL_MEDIUM and (stage != 'BLIND' or prior is not None):
        raise ValueError('sol_medium_blind_only')
    if not invocation_id or not account:raise ValueError('stage_identity_required')
    if stage=='ADJUDICATION' and not isinstance(prior,AcceptedStage):
        raise ValueError('accepted_blind_capability_required')
    if stage=='BLIND' and prior is not None:raise ValueError('blind_has_no_prior')
    _v3_prior_version(prior, version)
    prior_data=prior.snapshot() if prior else None
    if prior and (prior.stage!='BLIND' or prior.packet!=packet):raise ValueError('stage_prior_packet_binding')
    if prior and (prior.version in (DATED_TIMING,DATED_TIMING_V2) or version in (DATED_TIMING,DATED_TIMING_V2)) and prior.version!=version:
        raise ValueError('stage_timing_prompt_version_mismatch')
    if prior and _engine(prior.version) is not _engine(version):raise ValueError('stage_policy_version_mismatch')
    text=prompt(packet,stage,knowledge=knowledge,registry=registry,
                prior=prior_data['output'] if prior else None,version=version)
    request=dict(contract=execution_contract(version),invocation_id=invocation_id,account=account,stage=stage,
        security=packet['base']['public_security'],source_sha=digest(packet),source_as_of=packet['base']['as_of'],
        prompt_version=version,prompt_sha=digest(text.encode()),schema_sha=digest(output_schema(packet,version)),
        prior_stage_sha=digest(prior_data) if prior_data else None,
        model=execution_profile(version).model,effort=execution_profile(version).effort,
        timeout_seconds=SECONDS,input_bytes=INPUT_LIMIT,output_bytes=OUTPUT_LIMIT,retries=0,send=False)
    if version in SOL_VERSIONS:
        request['execution_profile']=execution_profile(version).contract
    return request,text


def _stage_name(request):
    return 'balanced-stage-'+digest({k:request[k] for k in ('invocation_id','account','stage')})[:40]


class AcceptedStage:
    """Trusted backend stage reader with live source and semantic revalidation."""
    def __init__(self,reader,*,packet,stage,version,knowledge,registry,source_loader,
                 prior=None,legacy_blind=False,**validation_inputs):
        if not callable(reader) or not callable(source_loader):
            raise ValueError('trusted_stage_and_source_readers_required')
        if stage=='ADJUDICATION' and not isinstance(prior,AcceptedStage):
            raise ValueError('accepted_blind_capability_required')
        if stage=='BLIND' and prior is not None:raise ValueError('blind_has_no_prior')
        if legacy_blind and (stage!='BLIND' or version!=ORIGINAL):
            raise ValueError('only_original_accepted_blind_importable')
        self.reader=reader;self.packet=deepcopy(packet);self.stage=stage;self.version=version
        self.knowledge=deepcopy(knowledge);self.registry=registry;self.source_loader=source_loader
        self.prior=prior;self.legacy_blind=legacy_blind;self.inputs=validation_inputs
        self.pin=digest(reader());self.revoked=False
        self.snapshot()

    def snapshot(self):
        if self.revoked:raise ValueError('stage_revoked')
        _v3_prior_version(self.prior, self.version)
        data=deepcopy(self.reader());e=data['execution']
        if digest(data)!=self.pin or self.source_loader()!=self.packet:
            raise ValueError('stage_source_or_record_changed')
        previous=self.prior.snapshot()['output'] if self.prior is not None else None
        if self.prior is not None and (self.prior.stage!='BLIND' or self.prior.packet!=self.packet):
            raise ValueError('stage_prior_packet_binding')
        if self.prior is not None and (self.prior.version in (DATED_TIMING,DATED_TIMING_V2) or self.version in (DATED_TIMING,DATED_TIMING_V2)) and self.prior.version!=self.version:
            raise ValueError('stage_timing_prompt_version_mismatch')
        if self.prior is not None and _engine(self.prior.version) is not _engine(self.version):
            raise ValueError('stage_policy_version_mismatch')
        text=prompt(self.packet,self.stage,knowledge=self.knowledge,registry=self.registry,
                    prior=previous,version=self.version)
        if (e.get('stage')!=self.stage or e.get('status')!='VALIDATED' or e.get('exit')!=0
                or not e.get('runtime',{}).get('verified') or not e['runtime'].get('session')
                or e.get('model')!=execution_profile(self.version).model
                or e.get('effort')!=execution_profile(self.version).effort
                or e.get('attempt')!=1 or e.get('retry')!=0 or e.get('packet_sha')!=digest(self.packet)
                or e.get('prompt_sha')!=digest(text.encode()) or e.get('schema_sha')!=digest(output_schema(self.packet,self.version))
                or e.get('output_sha')!=digest(data['output'])):
            raise ValueError('stage_exact_execution_binding')
        if self.version in SOL_VERSIONS and e.get('execution_profile')!=execution_profile(self.version).contract:
            raise ValueError('stage_exact_profile_binding')
        if len(json.dumps(data['output'],ensure_ascii=False).encode())>OUTPUT_LIMIT:
            raise ValueError('stage_output_limit')
        if not self.legacy_blind:
            if (e.get('stage_contract')!=execution_contract(self.version) or e.get('prompt_version')!=self.version
                    or not e.get('invocation_id') or e.get('approved_request_sha')!=e.get('request_sha')
                    or not e.get('request_sha') or not e['started']<=e['ended']<=e['deadline']
                    or not 0<e['deadline']-e['started']<=SECONDS):
                raise ValueError('stage_scope_or_deadline_binding')
        checked=_engine(self.version).validate_and_render(data['output'],self.packet,registry=self.registry,**self.inputs)
        if self.version in (UNIFIED, *UNIFIED_AI_VERSIONS):
            _engine(self.version).validate_transition(data['output'], previous)
        if checked!=data['validation']:raise ValueError('stage_original_validation_drift')
        return data

    def revoke(self):self.revoked=True


class StageReviewOwner(ReviewOwner):
    """Whole result requires two real accepted stages, not a context receipt."""
    def __init__(self,blind,adjudication,*,enabled=False):
        if not enabled:raise ValueError('stage_review_default_off')
        if (not isinstance(blind,AcceptedStage) or not isinstance(adjudication,AcceptedStage)
                or blind.stage!='BLIND' or adjudication.stage!='ADJUDICATION'
                or adjudication.prior is not blind):raise ValueError('bound_two_stage_capabilities_required')
        self.blind=blind;self.adjudication=adjudication
        super().__init__(self._record)

    def _record(self):
        return dict(packet=deepcopy(self.blind.packet),stages=dict(
            BLIND=self.blind.snapshot(),ADJUDICATION=self.adjudication.snapshot()))

    def issue(self):
        record=self._record()
        if self._revoked or digest(record)!=self._pin:raise ValueError('research_review_changed_or_revoked')
        sessions={s['execution']['runtime']['session'] for s in record['stages'].values()}
        if len(sessions)!=2:raise ValueError('stage_distinct_model_contexts_required')
        if self._receipt is None:
            self._receipt=dict(contract=output_contract(self.blind.version) if self.blind.version in UNIFIED_AI_VERSIONS else _engine(self.blind.version).CONTRACT,execution_contract=execution_contract(self.blind.version),
                record_sha256=self._pin,packet_sha256=digest(record['packet']),
                source_label='DATE_LABELED_EXISTING_CAPTURE',original_shared_deadline_claimed=False,
                strict_Core=False,strict_B2=False,send=False)
            if self.blind.version==UNIFIED_AI_V3_SOL_HIGH:
                self._receipt.update(execution_profile=SOL_HIGH_V1.contract,model=SOL_HIGH_V1.model,effort=SOL_HIGH_V1.effort)
        return self._receipt


class StageController(NoSendController):
    """One new approved stage, durable no-retry intent, original journal store."""
    def restore_stage(self,*,invocation_id,account,packet,stage,version,knowledge,registry,
                      source_loader,approval,account_lease,host_scope,host_attempt,prior=None,**inputs):
        """Reconsume an accepted manual-host journal; never invoke or write a stage.

        Only a trusted backend supplies this controller, exact original scope,
        approval and live source owners. Host-result JSON is not an authority.
        Every capability read rechecks this same store and its terminal records.
        """
        if not self.enabled:raise ValueError('stage_controller_default_off')
        if not all(callable(v) for v in (source_loader,approval,account_lease)):
            raise ValueError('stage_backend_authority_required')
        request,_=_stage_request(invocation_id=invocation_id,account=account,packet=packet,
            stage=stage,version=version,knowledge=knowledge,registry=registry,prior=prior)
        if getattr(self,'execution_profile',ASTRA_XHIGH_V1)!=execution_profile(version):raise ValueError('stage_controller_profile_mismatch')
        identity=dict(account_scope=account,security=packet['base']['public_security']['canonical_security_id'],
                      frozen_input_sha256=digest(packet))
        required={'mode','market','session','prior_session','kind','identity','plan_sha256','expires_at'}
        if (not isinstance(host_scope,dict) or set(host_scope)!=required
                or host_scope['mode']!='MANUAL_RESEARCH_CANARY' or host_scope['identity']!=identity
                or host_scope['market']!=packet['base']['public_security']['country'].lower()
                or not isinstance(host_attempt,str) or not host_attempt.startswith('host-')):
            raise ValueError('stage_original_host_scope_required')
        from app.services.vnext_no_send_runner import CONTRACT as HOST_CONTRACT
        one_shot=digest({k:v for k,v in host_scope.items() if k!='expires_at'})
        host_request=dict(contract=HOST_CONTRACT,identity=identity,market=host_scope['market'],
                          session=host_scope['session'],manual_scope_sha256=one_shot)
        if version in SOL_VERSIONS:
            host_request['execution_profile']=execution_profile(version).contract
        grant=dict(contract='ACCEPTED_STAGE_PARENT_RECONSUMPTION_V1',stage_request=deepcopy(request),
                   host_request_sha256=digest(host_request),host_attempt=host_attempt,
                   original_scope_sha256=digest(host_scope),new_model_calls=0,send=False)
        name=_stage_name(request)
        def read_accepted():
            with account_lease():
                if approval(deepcopy(grant)) is not True:raise ValueError('stage_reconsumption_grant_required')
                self._check_host_recovery()
                if self.account_stopped(account):raise ValueError('stage_account_stopped')
                if source_loader()!=packet:raise ValueError('stage_source_changed_before_restore')
                started=self._read(name+'-started',request)
                failed=self._read(name+'-failed',request)
                accepted=self._read(name+'-accepted',request)
                if started!=dict(state='IN_FLIGHT') or failed is not None or accepted is None:
                    raise ValueError('stage_original_accepted_journal_required')
                execution=accepted.get('execution',{})
                if (execution.get('request_sha')!=digest(request) or
                        execution.get('approved_request_sha')!=digest(request) or
                        execution.get('invocation_id')!=invocation_id):
                    raise ValueError('stage_original_request_binding')
                intent=self._read(host_attempt+'-intent',host_request)
                child=self._read(host_attempt+'-child',host_request)
                response=self._read(host_attempt+'-response',host_request)
                end=self._read(host_attempt+'-end',host_request)
                failure=self._read(host_attempt+'-failure',host_request)
                manual_start=self._read('manual-start-'+one_shot[:48],host_request)
                manual=self._read('manual-done-'+one_shot[:48],host_request)
                expected=dict(send=False,input_identity=identity,state='ACCEPTED_RESEARCH_STAGE',
                              stage=stage,record_sha=digest(accepted))
                if (not intent or intent.get('state')!='STARTED' or not child or child.get('state')!='RUNNING'
                        or not manual_start or manual_start.get('state')!='STARTED'
                        or manual_start.get('automatic_retry') is not False
                        or response!=expected or failure is not None or not end or manual!=end
                        or end.get('state')!='COMPLETED_NO_SEND' or end.get('attempt')!=host_attempt
                        or end.get('calendar',{}).get('scope_sha256')!=digest(host_scope)
                        or end.get('request_sha256')!=digest(host_request) or end.get('response')!=expected
                        or end.get('exit')!=0 or end.get('child_pid')!=child.get('pid')
                        or end.get('automatic_retry') is not False or end.get('failure') is not None):
                    raise ValueError('stage_original_completed_host_required')
                return accepted
        return AcceptedStage(read_accepted,packet=packet,stage=stage,version=version,
            knowledge=knowledge,registry=registry,source_loader=source_loader,prior=prior,**inputs)

    def run_stage(self,*,invocation_id,account,packet,stage,version,knowledge,registry,
                  source_loader,approval,account_lease,invoke,prior=None,**inputs):
        if not self.enabled:raise ValueError('stage_controller_default_off')
        if not all(callable(v) for v in (source_loader,approval,account_lease,invoke)):
            raise ValueError('stage_backend_authority_required')
        request,text=_stage_request(invocation_id=invocation_id,account=account,packet=packet,
            stage=stage,version=version,knowledge=knowledge,registry=registry,prior=prior)
        if getattr(self,'execution_profile',ASTRA_XHIGH_V1)!=execution_profile(version):raise ValueError('stage_controller_profile_mismatch')
        if approval(deepcopy(request)) is not True:raise ValueError('explicit_new_stage_grant_required')
        name=_stage_name(request)
        with account_lease():
            if self.account_stopped(account):raise ValueError('stage_account_stopped')
            self._check_host_recovery()
            if source_loader()!=packet:raise ValueError('stage_source_changed_before_call')
            done=self._read(name+'-accepted',request)
            if done is not None:
                return AcceptedStage(lambda:deepcopy(done),packet=packet,stage=stage,version=version,
                    knowledge=knowledge,registry=registry,source_loader=source_loader,prior=prior,**inputs)
            if not self._append(name+'-started',request,dict(state='IN_FLIGHT')):
                raise ValueError('stage_already_attempted_no_retry')
            start=time.time();deadline=start+SECONDS
            try:
                data=invoke(deepcopy(request),text,deadline)
                self._check_host_recovery()
                e=data['execution']
                if (time.time()>deadline or e.get('request_sha')!=digest(request)
                        or e.get('approved_request_sha')!=digest(request)
                        or e.get('invocation_id')!=invocation_id or e.get('deadline')!=deadline
                        or e.get('started',0)<start):raise ValueError('stage_bound_attempt_or_deadline')
                cap=AcceptedStage(lambda:deepcopy(data),packet=packet,stage=stage,version=version,
                    knowledge=knowledge,registry=registry,source_loader=source_loader,prior=prior,**inputs)
                self._append(name+'-accepted',request,cap.snapshot())
                return cap
            except Exception as exc:
                self._append(name+'-failed',request,dict(state='FAILED_NO_RETRY',error_type=type(exc).__name__))
                raise
