"""Opt-in V3: model technical prose and backend authority notice are separate."""
from copy import deepcopy
import json
import re
from typing import Literal

from app.services import vnext_dated_research_timing as legacy
from app.services.vnext_research_store import digest

CONTRACT = 'RESEARCH_TIMING_ONLY_V3'
PROMPT_VERSION = 'DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V3'
ENABLED_BY_DEFAULT = False
NOTICE_VERSION = 'DATED_TECHNICAL_BACKEND_AUTHORITY_NOTICE_V1'
NOTICE_TEXT = (
    '이 결과는 날짜가 명시된 역사적 기술 연구입니다. 현재가격·정규장 확정종가·정식 Timing·'
    '신규매수·보유·종합 방향·가치평가 판단 및 발송/주문 권한을 부여하지 않습니다.')
NOTICE_SHA256 = digest(NOTICE_TEXT.encode())


class ResearchTimingV3(legacy.ResearchTiming):
    contract: Literal['RESEARCH_TIMING_ONLY_V3']
    current_price: Literal[False]
    formal_timing: Literal[False]
    strict_ready: Literal[False]
    send: Literal[False]


def attach(economic_packet, *, timing_owner, registry, cutoff):
    packet = legacy.attach(economic_packet, timing_owner=timing_owner, registry=registry, cutoff=cutoff)
    packet['contract'] = CONTRACT
    return packet


def schema(*, security_id=None):
    if not isinstance(security_id, str) or not security_id:
        raise ValueError('research_timing_canonical_security_required')
    return legacy._schema(ResearchTimingV3, security_id=security_id)


def _technical_prose(text):
    # Compaction is rejection-only. Model text is never rewritten or exempted.
    compact = re.sub(r'\s+', '', text)
    if (any(term in compact for term in ('권한','고지','면책','허용','승인','허가','사용권',
            '현재가','현재가격','정규장확정종가','정식Timing','매수','매도','목표가',
            '적정가','가격구간','지지가격','저항가격','종합방향','발송','주문'))
            or re.search(r'authority|permission|disclaimer|authoriz|grant|currentprice|'
                         r'settledclose|\b(?:BUY|SELL|ORDER|APPROVED)\b', text+' '+compact, re.I)):
        raise ValueError('MODEL_AUTHORITY_NOTICE_IN_PROSE')
    legacy._prose(text)
    legacy._prose(compact)


def authority_notice(packet, checked):
    """Called only after the original live Owner and semantic checks succeed."""
    scope = packet['technical']
    value = checked['timing']
    if (packet['contract'] != CONTRACT or checked['contract'] != CONTRACT
            or digest(scope) != packet['authority_scope_sha256']
            or checked['packet_sha256'] != digest(packet)
            or any(scope[k] for k in ('current_price','formal_timing','strict_ready','send'))
            or any(checked[k] for k in ('current_price','formal_timing','strict_ready','send','investment_axes_changed'))
            or any(value[k] for k in ('current_price','formal_timing','strict_ready','send',
                                     'current_price_qualified','investment_axes_changed'))
            or value['no_send'] is not True or packet['no_send'] is not True or packet['not_current'] is not True):
        raise ValueError('V3_BACKEND_NOTICE_SCOPE_MISMATCH')
    return dict(version=NOTICE_VERSION, text=NOTICE_TEXT, text_sha256=NOTICE_SHA256,
        packet_sha256=digest(packet), authority_scope_sha256=digest(scope),
        current_price_qualified=False, investment_axes_changed=False, no_send=True,
        formal_timing=False, strict_ready=False, send=False)


def validate_and_render(value, packet, *, registry, timing_owner, economic_loader, **unused):
    try:
        checked = legacy._validate_and_render(value, packet, registry=registry, timing_owner=timing_owner,
            economic_loader=economic_loader, model=ResearchTimingV3, packet_builder=attach,
            contract=CONTRACT, prose=_technical_prose, summary_prose=_technical_prose)
    except ValueError as exc:
        if str(exc).startswith(('research_timing_numeric_', 'research_timing_unissued_',
                'research_timing_two_distinct_', 'research_timing_period_', 'research_timing_all_periods_')):
            raise ValueError('SOURCE_CITATION_MISMATCH: '+str(exc)) from exc
        raise
    notice = authority_notice(packet, checked)
    checked['authority_notice'] = notice
    checked['rendered'] += '\n\n' + notice['text']
    return checked


def prompt(packet, stage, *, knowledge, registry, prior=None):
    if packet.get('contract') != CONTRACT:
        raise ValueError('V3_PACKET_CONTRACT_MISMATCH')
    if stage not in ('BLIND','ADJUDICATION') or (stage=='BLIND' and prior is not None):
        raise ValueError('research_timing_stage')
    if stage=='ADJUDICATION' and (prior is None or prior.get('contract')!=CONTRACT):
        raise ValueError('STAGE_VERSION_MISMATCH_PRECALL')
    canonical = packet['base']['public_security']['canonical_security_id']
    schema(security_id=canonical)
    text = '''PROMPT CONTRACT: DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V3.
Use the exact RESEARCH_TIMING_ONLY_V3 JSON schema and Korean qualitative prose.
Write only technical evidence explanations in summary, conflicts, uncertainty,
change_condition, economic_separation, citations[].interpretation and periods[].reasoning.
The backend ALONE renders the fixed authority restriction notice AFTER validation.
DO NOT write, paraphrase, translate, negate, append or discuss an authority notice,
disclaimer or permissions in any free-prose field. Do not write current-price denials.
All prose must be nonempty with NO digits, currency, price zones, target prices,
BUY/SELL, trade instructions, orders or investment direction assertions.
Interpret momentum, trend and volatility at independently dated daily/weekly/monthly
periods. FAVORABLE/MIXED/CAUTIOUS/UNRESOLVED are historical technical states.
Do not force favorable or opposing labels. UNRESOLVED requires confidence
NOT_SEPARATELY_ISSUED; other states use LOW/MEDIUM/HIGH.
Copy PUBLIC_INPUT.base.public_security.canonical_security_id EXACTLY as security_id;
never substitute a ticker, name, abbreviation or normalized identity.
Review all three timeframes with each exact as_of. Cite at least two DISTINCT metrics.
Each citation must copy ref, timeframe, period_end, metric=fact.semantic, value as
the exact STRING form of fact.value, unit, formula and source_sha256.
Every period.refs must reference a citation from that same timeframe.
Numerals, dates and metric names containing digits belong only in structured fields.
Do not invent numbers or compute unsupported ratios. Explain actual evidence,
cross-timeframe conflicts, uncertainty, history limits and change conditions.
Indicators are correlated same-provider measurements, not independent financial proof.
economic_separation explains the distinct business/valuation evidence dates and
limitations only, WITHOUT permission/disclaimer language or any investment stance.
Missing financial verification is uncertainty, not proof of a negative business outcome.
current_price_qualified, current_price, formal_timing, strict_ready,
investment_axes_changed and send must be false; no_send must be true.
No tools, files, network, old model judgments or private thesis. Output JSON only.
'''
    public = deepcopy(packet)
    for role in public['technical']['roles'].values():
        role['source_views'] = [{k:v for k,v in s.items() if k not in ('excluded_incomplete','excluded_latest_unsettled')}
                                for s in role['source_views']]
    text += '\nSTAGE: '+stage+'\nPUBLIC_INPUT:\n'+json.dumps(public,ensure_ascii=False,sort_keys=True)
    if prior is not None:
        text += '\nNEW_ACCEPTED_BLIND_ONLY:\n'+json.dumps(prior,ensure_ascii=False,sort_keys=True)
    if len(text.encode()) > 384*1024:
        raise ValueError('research_timing_input_limit')
    return text
