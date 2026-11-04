"""Opt-in, as-of technical interpretation. Never current or investment Timing."""
from copy import deepcopy
from decimal import Decimal
import json
import re
import time
from typing import Literal
from uuid import uuid4

from app.services.vnext_dated_technical_owner import DatedTechnicalOwner, TARGETS
from app.services.vnext_dated_technical_appendix import DISPLAY, MINIMUM
from app.services.vnext_research_store import digest
from app.services.vnext_research_v3 import Strict

PURPOSE = 'AS_OF_DATE_TECHNICAL_RESEARCH_TIMING_V1'
PARTIAL_PURPOSE = 'AS_OF_DATE_TECHNICAL_RESEARCH_SCOPED_PERIODS_V1'
CONSUMER = 'vnext_dated_research_timing'
CONTRACT = 'RESEARCH_TIMING_ONLY_V1'
PROMPT_VERSION = 'DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V1'
IDENTITY_PROMPT_VERSION = 'DATED_TECHNICAL_RESEARCH_TIMING_PROMPT_V2'
ENABLED_BY_DEFAULT = False
PROHIBITED = ['CURRENT_PRICE', 'RTH_SETTLED_CLOSE', 'TIMING', 'VALUATION',
    'BUY', 'SELL', 'OVERALL', 'HOLDER', 'NEWBUYER', 'STRICT_NATIVE', 'SEND', 'ORDER', 'PRICE_ZONE']


def _scope(parent, security, cutoff, timeframes=None):
    roles, facts = {}, []
    selected = tuple(TARGETS) if timeframes is None else timeframes
    for tf in selected:
        kw = dict(security=security, timeframe=tf, cutoff=cutoff)
        receipt = parent.issue(**kw)
        value = parent.consume(receipt, **kw)
        if (value['basis'] != 'adjusted_close' or value['source_kind'] != 'NATIVE'
                or any(value[k] for k in ('current_price','strict_native','economic_direction','send'))):
            raise ValueError('research_timing_parent_scope')
        roles[tf] = dict(as_of=value['effective_analysis_as_of'], rows=len(value['rows']),
            first_bar=value['rows'][0]['date'], last_bar=value['rows'][-1]['date'],
            rows_sha256=value['rows_sha256'], basis=value['basis'],
            parent_receipt_sha256=digest(value), sources=value['sources'],
            source_views=value['source_views'], conflicts=value['conflicts'])
        for fact in value['features']['facts']:
            if fact['semantic'] not in DISPLAY:
                continue
            if fact['minimum_history'] > len(value['rows']):
                raise ValueError('research_timing_minimum_history')
            item = dict(timeframe=tf, period_end=value['effective_analysis_as_of'],
                basis=value['basis'], parent_receipt_sha256=digest(value),
                source_sha256=[s['source_sha256'] for s in value['sources']],
                page_sha256=sorted({p for s in value['sources'] for p in s['page_sha256']}),
                source_independence='SAME_PROVIDER_CORRELATED_TECHNICAL_MEASURES',
                fact=deepcopy(fact))
            item['ref'] = 'dated-' + digest(item)[:32]
            facts.append(item)
    return dict(purpose=PURPOSE if selected == tuple(TARGETS) else PARTIAL_PURPOSE, consumer=CONSUMER, security=deepcopy(security),
        cutoff=cutoff, roles=roles, facts=facts, currency='NOT_QUALIFIED',
        adjustment='PROVIDER_ADJUSTED_BASIS_NOT_INDEPENDENT_CORPORATE_ACTION_PROOF',
        prohibited=PROHIBITED, current_price=False, formal_timing=False, strict_ready=False, send=False)


class DatedResearchTimingOwner:
    """Independent purpose grant over a live original technical capability."""
    def __init__(self, parent, *, enabled=False, ttl_seconds=1800, clock=time.monotonic, timeframes=None):
        if type(parent) is not DatedTechnicalOwner or not 0 < ttl_seconds <= 3600:
            raise ValueError('research_timing_live_parent_required')
        self.parent, self.enabled, self.clock = parent, enabled, clock
        selected = tuple(TARGETS) if timeframes is None else tuple(timeframes)
        if not selected or selected != tuple(tf for tf in TARGETS if tf in selected):
            raise ValueError('research_timing_exact_period_scope')
        self.timeframes = selected
        self.purpose = PURPOSE if selected == tuple(TARGETS) else PARTIAL_PURPOSE
        self.issuer = str(uuid4())
        self.expires = clock()+ttl_seconds
        self.revoked = False
        self._issued = {}

    def revoke(self):
        self.revoked = True

    def issue(self, *, security, cutoff, consumer=CONSUMER, use=None):
        if not self.enabled or self.revoked or self.clock() >= self.expires:
            raise ValueError('research_timing_disabled_expired_or_revoked')
        use = self.purpose if use is None else use
        if consumer != CONSUMER or use != self.purpose:
            raise ValueError('research_timing_consumer_or_use')
        scope = _scope(self.parent, security, cutoff, self.timeframes)
        key = digest([security, cutoff, consumer, use])
        if key in self._issued:
            receipt, sealed, prior = self._issued[key]
            if scope != prior or digest(receipt) != sealed:
                raise ValueError('research_timing_source_or_receipt_changed')
            return receipt
        receipt = dict(contract=self.purpose, consumer=consumer, use=use, issuer=self.issuer,
            nonce=str(uuid4()), expires_monotonic=self.expires, scope_sha256=digest(scope),
            security=deepcopy(security), cutoff=cutoff, prohibited=PROHIBITED,
            current_price=False, formal_timing=False, strict_ready=False, send=False)
        self._issued[key] = (receipt, digest(receipt), scope)
        return receipt

    def consume(self, receipt, *, security, cutoff, consumer=CONSUMER, use=None):
        use = self.purpose if use is None else use
        issued = self.issue(security=security, cutoff=cutoff, consumer=consumer, use=use)
        if receipt is not issued:
            raise ValueError('research_timing_unissued_or_wrong_registry')
        return deepcopy(self._issued[digest([security, cutoff, consumer, use])][2])


def attach(economic_packet, *, timing_owner, registry, cutoff):
    from app.services.vnext_balanced_research import project
    if type(timing_owner) is not DatedResearchTimingOwner:
        raise ValueError('research_timing_live_owner_required')
    base = economic_packet['base']
    security = base['public_security']
    receipt = timing_owner.issue(security=security, cutoff=cutoff)
    scope = timing_owner.consume(receipt, security=security, cutoff=cutoff)
    p = project(economic_packet, registry=registry)
    # Only source-backed dated business/valuation context. Old judgments and
    # unrelated recent prices must not leak into a blind technical experiment.
    evidence = [e for e in p['evidence'] if e['eligible'] and e['layer'] in
                ('ECONOMIC_OBSERVATION', 'VALUATION_CONTEXT')]
    return dict(contract=CONTRACT, base=dict(public_security=deepcopy(security),
        as_of=base['as_of'], run_id=base['run_id']), economic_packet_sha256=digest(economic_packet),
        economic_context=evidence, technical=scope, authority_scope_sha256=digest(scope),
        preserved_axes=['NewBuyerFundamental','HolderVirtual','Overall','Valuation'],
        not_current=True, no_send=True)


class Citation(Strict):
    ref: str
    timeframe: Literal['daily','weekly','monthly']
    period_end: str
    metric: str
    value: str
    unit: str
    formula: str
    source_sha256: list[str]
    interpretation: str


class PeriodReview(Strict):
    timeframe: Literal['daily','weekly','monthly']
    as_of: str
    state: Literal['FAVORABLE','MIXED','CAUTIOUS','UNRESOLVED']
    refs: list[str]
    reasoning: str


class ResearchTiming(Strict):
    contract: Literal['RESEARCH_TIMING_ONLY_V1']
    security_id: str
    state: Literal['FAVORABLE','MIXED','CAUTIOUS','UNRESOLVED']
    confidence: Literal['LOW','MEDIUM','HIGH','NOT_SEPARATELY_ISSUED']
    summary: str
    citations: list[Citation]
    periods: list[PeriodReview]
    conflicts: str
    uncertainty: str
    change_condition: str
    economic_separation: str
    current_price_qualified: Literal[False]
    investment_axes_changed: Literal[False]
    no_send: Literal[True]


def schema(*, security_id=None):
    return _schema(ResearchTiming, security_id=security_id)


def _schema(model, *, security_id=None):
    value = model.model_json_schema()
    def walk(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                node['required'] = list(node.get('properties', {}))
                node['additionalProperties'] = False
            for v in node.values(): walk(v)
        elif isinstance(node, list):
            for v in node: walk(v)
    walk(value)
    if security_id is not None:
        if not isinstance(security_id,str) or not security_id:
            raise ValueError('research_timing_canonical_security_required')
        value['properties']['security_id']['const'] = security_id
    return value


def _prose(text):
    # Numerical assertions belong to source-bound citations, not free prose.
    if (not text.strip() or re.search(r'\d|\{\{|\}\}|\b(?:BUY|SELL|ATTRACTIVE|AVOID|WAIT_FOR_ZONE|FAVORABLE_NOW|KRW|USD)\b|[\u20a9$]', text, re.I)
            or any(s in text for s in ('매수하','매도하','목표가','원화','달러 가격','현재가','지지 가격','저항 가격'))):
        raise ValueError('research_timing_unbound_or_forbidden_prose')


DATED_AUTHORITY_DENIAL = (
    '각기 다른 완료기간에 한정한 역사적 정성 평가이며 기존 타이밍·신규 진입자·보유자·종합·가치평가 '
    '판단이나 현재가 판단의 권한을 부여하지 않는다.')


def _summary_prose(text):
    # Only this exact, final standalone disclaimer is exempt from lexical denial.
    # The preceding technical prose still has the original restrictions.
    suffix = '. ' + DATED_AUTHORITY_DENIAL
    if text.endswith(suffix):
        prefix = text[:-len(DATED_AUTHORITY_DENIAL)]
        compact = re.sub(r'\s+', '', prefix)
        if re.search(r'권한|승인|허가|부여|고지|거짓|아니|부정|틀리|취소|무효|철회|그러나|하지만|불구|반대로|'
                     r'\b(?:not|false|grant|authorize|permission)\b', prefix+' '+compact, re.I):
            raise ValueError('research_timing_unbound_or_forbidden_prose')
        _prose(prefix)
        _prose(compact)
    else:
        _prose(text)


def validate_and_render(value, packet, *, registry, timing_owner, economic_loader, **unused):
    return _validate_and_render(value, packet, registry=registry, timing_owner=timing_owner,
        economic_loader=economic_loader, model=ResearchTiming, packet_builder=attach,
        contract=CONTRACT, prose=_prose, summary_prose=_summary_prose)


def _validate_and_render(value, packet, *, registry, timing_owner, economic_loader,
                         model, packet_builder, contract, prose, summary_prose):
    """Shared evidence checks; each version owns its schema and prose policy."""
    parsed = model.model_validate(value).model_dump(mode='json')
    if parsed != value:
        raise ValueError('research_timing_exact_types')
    if not callable(economic_loader):
        raise ValueError('research_timing_original_source_loader_required')
    current = packet_builder(economic_loader(), timing_owner=timing_owner, registry=registry,
                     cutoff=packet['technical']['cutoff'])
    if current != packet:
        raise ValueError('research_timing_exact_packet')
    if value['security_id'] != packet['base']['public_security']['canonical_security_id']:
        raise ValueError('research_timing_security')
    if (value['state']=='UNRESOLVED') != (value['confidence']=='NOT_SEPARATELY_ISSUED'):
        raise ValueError('research_timing_confidence')
    catalog = {r['ref']:r for r in packet['technical']['facts']}
    citations = value['citations']
    if len(citations) < 2 or len({c['ref'] for c in citations}) != len(citations):
        raise ValueError('research_timing_two_distinct_citations')
    metrics = set()
    for c in citations:
        if c['ref'] not in catalog:
            raise ValueError('research_timing_unissued_fact')
        r = catalog[c['ref']]; f = r['fact']
        expected = dict(timeframe=r['timeframe'], period_end=r['period_end'], metric=f['semantic'],
            value=str(f['value']), unit=f['unit'], formula=f['formula'], source_sha256=r['source_sha256'])
        if any(c[k] != v for k,v in expected.items()):
            raise ValueError('research_timing_numeric_source_binding')
        if not Decimal(c['value']).is_finite():
            raise ValueError('research_timing_nonfinite')
        metrics.add(c['metric']); prose(c['interpretation'])
    if len(metrics) < 2:
        raise ValueError('research_timing_two_distinct_metrics')
    periods = value['periods']
    expected_periods = (set(packet['technical']['roles'])
        if packet['technical']['purpose'] == PARTIAL_PURPOSE else set(TARGETS))
    if len(periods)!=len(expected_periods) or {p['timeframe'] for p in periods}!=expected_periods:
        raise ValueError('research_timing_all_periods_required')
    cited = {c['ref'] for c in citations}
    for p in periods:
        role = packet['technical']['roles'][p['timeframe']]
        if p['as_of']!=role['as_of'] or not p['refs'] or len(set(p['refs']))!=len(p['refs']):
            raise ValueError('research_timing_period_binding')
        if any(r not in cited or catalog[r]['timeframe']!=p['timeframe'] for r in p['refs']):
            raise ValueError('research_timing_period_reference')
        prose(p['reasoning'])
    for key in ('summary','conflicts','uncertainty','change_condition','economic_separation'):
        (summary_prose if key=='summary' else prose)(value[key])
    lines = [f"# {packet['base']['public_security']['ticker']} | {contract}",
        'NOT_CURRENT / NO_SEND / currency NOT_QUALIFIED',
        f"새 연구용 기술 판단: {value['state']} | confidence {value['confidence']}", value['summary'],
        '', '| 기간 | 기준일 | 연구 상태 | 이유 |', '|---|---|---|---|']
    lines += [f"| {p['timeframe']} | {p['as_of']} | {p['state']} | {p['reasoning']} |" for p in periods]
    lines += ['', '| 근거 | 값·원본 단위 | 기간 종료 | 공식 | 해석 |', '|---|---|---|---|---|']
    lines += [f"| {c['timeframe']}/{c['metric']} | {c['value']} {c['unit']} | {c['period_end']} | {c['formula']} | {c['interpretation']} |" for c in citations]
    for c in citations:
        lines += [f"- ref `{c['ref']}` / source `{','.join(c['source_sha256'])}`"]
    lines += ['', '기간 간 충돌: '+value['conflicts'], '불확실성: '+value['uncertainty'],
        '변경 조건: '+value['change_condition'], '사업·가치평가와 분리: '+value['economic_separation'],
        '지표는 같은 공급자 계보의 상관된 관측이며 독립적인 경제적 보강이 아닙니다.',
        '기존 NewBuyerFundamental / HolderVirtual / Overall / Valuation은 변경하지 않았습니다.']
    return dict(contract=contract, rendered='\n'.join(lines), timing=deepcopy(value),
        packet_sha256=digest(packet), citations_verified=len(citations),
        independent_economic_sources=False, current_price=False, formal_timing=False,
        investment_axes_changed=False, strict_ready=False, send=False)


def prompt(packet, stage, *, knowledge, registry, prior=None, version=PROMPT_VERSION):
    if version not in (PROMPT_VERSION,IDENTITY_PROMPT_VERSION):
        raise ValueError('research_timing_prompt_version')
    if stage not in ('BLIND','ADJUDICATION') or (stage=='BLIND' and prior is not None):
        raise ValueError('research_timing_stage')
    if stage=='ADJUDICATION' and prior is None:
        raise ValueError('research_timing_prior_required')
    text = '''You are performing dated technical research only, not investment advice or an order decision.
Use the exact RESEARCH_TIMING_ONLY_V1 JSON schema. Korean qualitative prose.
Interpret actual momentum, trend and volatility as of the independently dated daily,
weekly and monthly periods. Do not force opposite labels or a favorable result.
FAVORABLE/MIXED/CAUTIOUS/UNRESOLVED are historical qualitative technical states only.
They are not original Timing, NewBuyer, Holder, Overall, valuation or current-price authority.
No currency, price zone, target price, BUY/SELL, trade instruction or current quote.
For UNRESOLVED confidence must be NOT_SEPARATELY_ISSUED, otherwise LOW/MEDIUM/HIGH.
Use at least two DISTINCT technical metrics, and review all three timeframes.
For EACH cited fact copy ref, timeframe, period_end, metric=fact.semantic,
value=exact STRING form of fact.value, unit, formula and source_sha256 exactly.
Every period.refs must refer to a citation in that same period, with its exact as_of.
Citations must be integrated into your actual qualitative reasoning, not an unused appendix.
All free prose (including interpretation) must be nonempty and contain NO numeric digits;
numeric values, metric names with digits and dates belong ONLY in structured citation/period fields.
Do not calculate extra ratios or import unbound numbers. Treat indicators as correlated
same-provider measures, not independent financial corroboration. Discuss weekly/monthly
conflicts and insufficient history. Preserve separate economic/valuation context and its
source dates; it cannot authorize investment direction. Missing support is uncertainty,
not an automatic negative business conclusion. State what new evidence could change the view.
No tools, file access, network, past model results or user thesis. Output JSON only.
'''
    public = deepcopy(packet)
    # Keep the exact source/engine definitions while omitting large exclusion
    # inventories from the prompt; their hashes remain in the bound packet.
    for role in public['technical']['roles'].values():
        role['source_views'] = [{k:v for k,v in s.items() if k not in ('excluded_incomplete','excluded_latest_unsettled')}
                                for s in role['source_views']]
    text += '\nSTAGE: '+stage+'\nPUBLIC_INPUT:\n'+json.dumps(public,ensure_ascii=False,sort_keys=True)
    if prior is not None:
        text += '\nNEW_ACCEPTED_BLIND_ONLY:\n'+json.dumps(prior,ensure_ascii=False,sort_keys=True)
    if version==IDENTITY_PROMPT_VERSION:
        canonical=packet['base']['public_security']['canonical_security_id']
        schema(security_id=canonical)
        text += ('\nPROMPT CONTRACT: '+IDENTITY_PROMPT_VERSION+'.\n'
            'Copy PUBLIC_INPUT.base.public_security.canonical_security_id exactly into output.security_id.\n'
            'Do not use the ticker, issuer name, display label, shortened ID or a normalized substitute.\n'
            'The security_id JSON schema const binds the same exact string: '+json.dumps(canonical,ensure_ascii=False)+'.\n'
            'This is an output identity requirement only; no source or investment use rights are added.\n')
    if len(text.encode())>384*1024:
        raise ValueError('research_timing_input_limit')
    return text
