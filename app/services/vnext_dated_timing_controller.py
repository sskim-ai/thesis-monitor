"""Separate NO-SEND journal consumer; never the daily investment outbox."""
from copy import deepcopy
from app.services.vnext_balanced_stage_review import StageController, StageReviewOwner, DATED_TIMING, DATED_TIMING_V2, DATED_TIMING_V3, _engine
from app.services.vnext_dated_research_timing import DatedResearchTimingOwner, CONTRACT
from app.services import vnext_dated_research_timing_v3 as timing_v3
from app.services.vnext_research_store import digest


def outbox_key(packet):
    contract = packet['contract']
    if contract not in (CONTRACT, timing_v3.CONTRACT):
        raise ValueError('timing_outbox_contract')
    return 'dated-timing-outbox-' + digest(dict(contract=contract, packet=digest(packet)))[:40]


class DatedTimingController(StageController):
    def finalize_timing(self, *, packet, owner, timing_owner):
        if (not self.enabled or type(owner) is not StageReviewOwner or
                type(timing_owner) is not DatedResearchTimingOwner):
            raise ValueError('timing_outbox_live_owners_required')
        if (owner.blind.version not in (DATED_TIMING,DATED_TIMING_V2,DATED_TIMING_V3)
                or owner.adjudication.version!=owner.blind.version):
            raise ValueError('timing_outbox_version')
        self._check_host_recovery()
        kwargs=dict(security=packet['base']['public_security'],cutoff=packet['technical']['cutoff'])
        scope=timing_owner.consume(timing_owner.issue(**kwargs),**kwargs)
        if scope!=packet['technical'] or digest(scope)!=packet['authority_scope_sha256']:
            raise ValueError('timing_outbox_scope')
        receipt=owner.issue();value=owner.consume(receipt,packet=packet)
        contract = _engine(owner.blind.version).CONTRACT
        if packet['contract']!=contract or value['contract']!=contract or value['current_price'] or value['send'] or value['formal_timing']:
            raise ValueError('timing_outbox_noninvestment_only')
        result=dict(state='DATED_RESEARCH_NO_SEND',rendered=value['rendered'],
            validation=value,validated_receipt=dict(receipt),current_price=False,
            formal_timing=False,strict_ready=False,send=False)
        if owner.blind.version == DATED_TIMING_V3:
            notice = timing_v3.authority_notice(packet, value)
            if value.get('authority_notice') != notice or value['rendered'].count(notice['text']) != 1:
                raise ValueError('V3_BACKEND_NOTICE_SCOPE_MISMATCH')
            result['authority_notice'] = deepcopy(notice)
        request=dict(contract=contract,packet_sha256=digest(packet))
        self._append(outbox_key(packet),request,result)
        return result
