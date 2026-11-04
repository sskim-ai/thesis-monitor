"""Whole-verdict input custody, distinct from field-local data eligibility.

The existing two-context Owner has no separately accepted business/timing outputs.
Never splice its prose into a new verdict. Prompt inputs, including uncited facts,
remain dependencies of its entire output. This module makes no model calls.
"""
from copy import deepcopy
import json
from app.services.vnext_research_store import digest
from app.services.vnext_optional_fy1_research import ReviewOwner

CONTRACT='whole-verdict-input-dependency-v1'


def _prompt_input(raw):
    # Parse the original JSON envelope, not prose citations or issuer narratives.
    text=raw.decode('utf-8'); decoder=json.JSONDecoder()
    for i,char in enumerate(text):
        if char!='{':continue
        try:value,_=decoder.raw_decode(text[i:])
        except json.JSONDecodeError:continue
        if isinstance(value,dict) and set(value)=={'$text_dictionary','$data'}:
            from app.services.vnext_research_v3 import prompt_text_decode,prompt_table_decode
            value=prompt_table_decode(prompt_text_decode(value))
        if isinstance(value,dict) and {'stage','packet','source_contracts','blind','original_knowledge'}<=value.keys():
            return value
    raise ValueError('original_prompt_envelope_not_found')


def _source_refs(value):
    refs=set()
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('source_sha','source_sha256','raw_sha256','original_raw_sha256','lineage_sha256') and isinstance(v,str) and len(v)==64:
                refs.add(v)
            refs.update(_source_refs(v))
    elif isinstance(value,list):
        for v in value:refs.update(_source_refs(v))
    elif isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value):
        refs.add(value)
    return refs


def _input_fields(packet):
    # Ignore storage bookkeeping, but never actual source/period/use/data identity.
    return {(e['field'],tuple(e['scope'])):dict(field=e['field'],scope=e['scope'],
        source_sha=e['source_sha'],original_run=e['original_run'],status=e['status'],
        data=e['data'],allowed_use=e.get('allowed_use'),direction_allowed=e.get('direction_allowed'),
        original_receipt_sha256=e['provenance']['original_receipt_sha256']) for e in packet['evidence']}


class WholeVerdictDependencies:
    def __init__(self,owner,*,registration,prompts):
        if not isinstance(owner,ReviewOwner) or set(prompts)!={'BLIND','ADJUDICATION'}:
            raise ValueError('original_owner_and_prompt_bytes_required')
        record=owner.dependency_record();base=record['packet']['base']
        if any(base['public_security'].get(k)!=v for k,v in registration['security'].items() if k in base['public_security']):
            raise ValueError('model_dependency_registration_identity')
        contexts={}
        for stage,data in record['stages'].items():
            raw=prompts[stage];e=data['execution']
            if not isinstance(raw,bytes) or digest(raw)!=e.get('prompt_sha'):
                raise ValueError('model_dependency_prompt_digest')
            envelope=_prompt_input(raw)
            if envelope['packet']!=base or envelope['stage']!=stage:
                raise ValueError('model_dependency_original_input')
            expected=None if stage=='BLIND' else record['stages']['BLIND']['output']
            if envelope['blind']!=expected:
                raise ValueError('model_dependency_blind_adjudication_binding')
            contexts[stage]=dict(model_run=e['runtime']['session'],prompt_sha256=digest(raw),
                output_sha256=e['output_sha'],schema_sha256=e['schema_sha'],model=e['model'],effort=e['effort'])
        self.owner=owner;self.record=record;self.registration=deepcopy(registration)
        self.pin=digest(record);self.base=deepcopy(base)
        self.graph=dict(contract=CONTRACT,granularity='WHOLE_VERDICT_NOT_INDEPENDENT_STAGE_SIGNATURES',
            original_owner_receipt=deepcopy(owner.issue()),model_contract=record['packet']['contract'],
            model_record_sha256=self.pin,packet_sha256=digest(record['packet']),contexts=contexts,
            security=base['public_security'],registration_version=registration['registration_version'],
            source_inputs=list(_input_fields(base).values()),all_input_source_refs=sorted(_source_refs(record['packet'])),
            attachment_sha256=digest({k:v for k,v in record['packet'].items() if k!='base'}),
            price_attachment_sha256=digest(base.get('price_attachment')),
            downstream=['business','valuation','timing','NewBuyer','HYPOTHETICAL_HOLDER'],
            private_holdings=False,independently_signed_subresults=[])

    def review(self,current,*,registry,registration):
        from app.services.vnext_daily_research import UseRegistry
        from app.services.vnext_composite_research import PUBLIC_ID
        if not isinstance(registry,UseRegistry):raise ValueError('live_revocation_registry_required')
        if digest(self.owner.dependency_record())!=self.pin:raise ValueError('model_dependency_record_drift')
        if registration!=self.registration or any(
                current['public_security'].get(k)!=registration['security'].get(k) or
                self.base['public_security'].get(k)!=registration['security'].get(k)
                for k in PUBLIC_ID):
            raise ValueError('model_dependency_current_identity')
        security=current['public_security']['canonical_security_id']
        revoked=[e['ref'] for e in self.base['evidence'] if registry.revoked(security,e)]
        # Supplemental attachments may not have field identities. A matching deny
        # cannot be proved unrelated, so fail closed for this whole verdict only.
        base_refs={e['source_sha'] for e in self.base['evidence']}
        for sec,sha,use,generation,field,scope in registry.denials():
            if sec==security and sha in set(self.graph['all_input_source_refs'])-base_refs:
                revoked.append('attachment:'+sha)
        changed=_input_fields(current)!=_input_fields(self.base)
        # Optional display enrichment is an input change, never a new identity
        # or permission to reuse a verdict with missing prompt information.
        changed |= current['public_security']!=self.base['public_security']
        changed |= any(current.get(k)!=self.base.get(k) for k in
            ('price_attachment','reference_bundle','component_reference','research_financial_reference'))
        status=('REVOKED_DEPENDENCY' if revoked else 'MODEL_INPUT_CHANGED' if changed else 'REUSE_VALID_PRIOR')
        return dict(status=status,reusable=status=='REUSE_VALID_PRIOR',revoked_dependencies=revoked,
            graph_sha256=digest(self.graph),revocation_fingerprint=registry.fingerprint(),
            independent_subresult_reuse=False,new_model_calls=0,whole_verdict=True)

    def consume(self,current,*,registry,registration,part='WHOLE_VERDICT'):
        if part!='WHOLE_VERDICT':raise ValueError('monolithic_verdict_split_forbidden')
        if not self.review(current,registry=registry,registration=registration)['reusable']:
            raise ValueError('prior_model_dependency_not_reusable')
        return self.owner.consume(self.owner.issue(),packet=self.record['packet'])
