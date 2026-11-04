"""Backend-owned replay of a sealed research output, never a new model judgment."""
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from secrets import token_hex
from app.services import vnext_dated_kis_research as dated
from app.services.vnext_kis_multisource import CONTRACT as DATED_CONTRACT
from app.services.vnext_research_store import digest

CONTRACT = 'validated-ai-research-review-v1'
DATA_CONTRACT = 'research-data-state-view-v1'


def data_states(packet):
    refs = {e['ref']: e for e in packet['evidence']
            if e.get('data', {}).get('contract') == DATED_CONTRACT}
    numbers = [n for n in packet['numeric_catalog'] if n.get('ref') in refs]
    source = packet.get('kis_source_status')
    scopes = []
    for n in numbers:
        d = refs[n['ref']]['data']
        scopes.append(dict(metric=n['field'], scope='DATED_RESEARCH_ONLY',
            value=n['value'], unit=n['unit'], capture=n['as_of'],
            forecast_period=d['period'], estimate_date=d['estimate_date'],
            fiscal_inventory=d['fiscal_inventory_as_of'], price_session=d.get('price_session'),
            ref=n['ref'], source_sha=n['source_sha']))
    return dict(contract=DATA_CONTRACT, source_at_retrieval=deepcopy(source),
        dated_numeric=scopes, dated_numeric_count=len(scopes),
        current_fiscal='UNVERIFIED' if scopes else 'NOT_REASSESSED',
        model_in_this_data_preview='OFF', strict_ready=False,
        distinction='Capture-time source status does not revoke separately admitted dated observations',
        packet_sha256=digest(packet))


def render_data_view(product):
    p = product['packet']
    if product['send'] is not False or product['strict_ready'] is not False or p['model'] != 'OFF':
        raise ValueError('data_view_no_send_scope')
    states = data_states(p)
    source = states['source_at_retrieval']
    lines = ['# DATA_PREVIEW_NO_MODEL', '모델을 실행하지 않은 데이터 초안입니다.',
        '원본 캡처 당시 상태: ' + (source['state'] if source else 'INHERITED'),
        '별도 적격 날짜 명시 연구 수치: ' + str(states['dated_numeric_count']),
        '현재 회계목록 완전성: ' + states['current_fiscal'],
        'AI 검토: 이 데이터 초안에는 없음 / Strict Native: 미승인',
        '아래의 원본 상태는 수집 당시 기록이며, 별도 저장된 연구 수치와 다른 축입니다.',
        '', product['preview']]
    return dict(contract=DATA_CONTRACT, kind='DATA_PREVIEW_NO_MODEL', states=states,
                preview='\n'.join(lines), send=False, strict_ready=False)


@dataclass(frozen=True)
class _Receipt:
    registry: str
    key: str
    composite_sha256: str


class ResearchReviewOwner:
    """Only a trusted backend archive bootstrap may construct this capability.

    Public callers supply neither output JSON nor accepted IDs to issue/consume.
    A new process reboots the pinned archive and validates again; old public
    receipts cannot rehydrate ownership. No durable production authority implied.
    """
    def __init__(self, trusted_bootstrap, *, numeric_owner):
        if not callable(trusted_bootstrap):
            raise ValueError('trusted_archive_bootstrap_required')
        self._record = deepcopy(trusted_bootstrap())
        self._numeric_owner = numeric_owner
        self._registry = token_hex(16)
        self._issued = {}
        self._revoked = False

    def revoke(self):
        self._revoked = True
        self._issued.clear()

    def _validate(self, composite):
        if self._revoked:
            raise ValueError('research_review_revoked')
        r = self._record
        p, binding = r['packet'], r['binding']
        if composite != p['composite'] or binding['packet_sha256'] != digest(p):
            raise ValueError('research_review_exact_parent_binding')
        sec = composite['public_security']
        if (binding['canonical_security_id'] != sec['canonical_security_id']
                or binding['evidence_cutoff'] != composite['as_of']):
            raise ValueError('research_review_security_cutoff')
        if any(composite.get(k) is not False for k in
               ('send', 'strict_ready', 'holdings_included', 'user_thesis_included')):
            raise ValueError('research_review_public_scope')
        if binding['schema_sha256'] != digest(dated.schema()) or r['schema'] != dated.schema():
            raise ValueError('research_review_schema_drift')
        if len(r['source_archive']) != 64 or r['price_sources_sha256'] != {
                k: digest(v) for k, v in r['price_source_bytes'].items()}:
            raise ValueError('research_review_source_custody')
        checked = {}
        for stage in ('BLIND', 'ADJUDICATION'):
            saved = r['stages'][stage]
            ledger = [e for e in r['ledger'] if e['stage'] == stage]
            if len(ledger) != 1:
                raise ValueError('research_review_stage_identity')
            e = ledger[0]
            if (e['status'] != 'VALIDATED' or e['exit'] != 0 or not e['runtime']['verified']
                    or e['packet_sha'] != digest(p) or e['output_sha'] != digest(saved['output'])
                    or e['schema_sha'] != binding['schema_sha256']):
                raise ValueError('research_review_execution_binding')
            result = dated.validate_and_render(saved['output'], p, owner=self._numeric_owner,
                price_source_bytes=r['price_source_bytes'])
            if result != saved['validation']:
                raise ValueError('research_review_original_validation_drift')
            checked[stage] = result
        if binding['output_sha256'] != digest(r['stages']['ADJUDICATION']['output']):
            raise ValueError('research_review_adjudication_identity')
        return checked

    def issue(self, composite):
        self._validate(composite)
        key = digest(composite)
        if key not in self._issued:
            self._issued[key] = _Receipt(self._registry, token_hex(16), key)
        return self._issued[key]

    def consume(self, receipt, composite):
        key = digest(composite)
        if (not isinstance(receipt, _Receipt) or receipt is not self._issued.get(key)
                or receipt.registry != self._registry or receipt.composite_sha256 != key):
            raise ValueError('research_review_unissued_or_wrong_registry')
        checked = self._validate(composite)
        r = self._record
        final = checked['ADJUDICATION']['rendered']
        blind = checked['BLIND']['rendered']
        if final['decision'] is not None or final['holdings_included'] or final['user_thesis_included']:
            raise ValueError('research_review_no_strict_or_private_judgment')
        projection = dict(contract=CONTRACT, kind='VALIDATED_AI_RESEARCH_ONLY',
            public_security=deepcopy(composite['public_security']),
            display_name=r['packet']['base']['public_security'].get('company_name',composite['ticker']),
            source_archive=r['source_archive'], binding=deepcopy(r['binding']),
            model_origin=[dict(stage=e['stage'], model=e['model'], effort=e['effort'],
                session=e['runtime']['session'], output_sha=e['output_sha']) for e in r['ledger']],
            evidence_cutoff=composite['as_of'], new_model_calls=0, reused_model_contexts=2,
            verdict=deepcopy(final), numeric_claims=deepcopy(checked['ADJUDICATION']['numeric_claims']),
            dated_scopes=deepcopy(r['packet']['dated_original_scopes']),
            comparison=dict(blind_signal=blind['economic_evidence_signal'],
                adjudication_signal=final['economic_evidence_signal'],
                change=final['review_changes'],
                independent_new_source=False,
                qualification='Second model context reuses the same frozen facts; no independent new counterevidence'),
            holder_scope='HYPOTHETICAL', decision=None, strict_ready=False, send=False,
            economic_truth_verified=False, new_direction_grant=False,
            holdings_included=False, user_thesis_included=False)
        return dict(projection=projection, preview=_render(projection))

    def readable_views(self, receipt, composite, *, post_model_loader=None, persisted_record_ids=()):
        """Retain the old byte-stable product while exposing the human view."""
        from app.services.vnext_readable_research import project
        original = self.consume(receipt, composite)
        if post_model_loader is not None and not callable(post_model_loader):
            raise ValueError('backend_public_reference_loader_required')
        later = post_model_loader() if post_model_loader is not None else None
        return project(original, self._record, post_model_packet=later, persisted_record_ids=persisted_record_ids)


def _render(p):
    v = p['verdict'];sec = p['public_security']
    title = p['display_name']
    lines = [f"# {title} ({sec['ticker']}) | VALIDATED_AI_RESEARCH_ONLY",
        '검증된 과거 AI 연구 결과의 미발송 재사용입니다. 새로운 모델 판단이나 주문 지시가 아닙니다.',
        '증거 cutoff: '+p['evidence_cutoff'],
        '사업 근거: '+v['economic_evidence_signal']+' / 가치평가: '+v['valuation_judgment'],
        '신규 매수: '+v['newbuyer_stance']+' / 가상 보유자(HYPOTHETICAL): '+v['holder_stance'],
        'Strict decision: null / Native ready: false / send: false',
        '', '## 요약',v['summary'],'','## 사업 추세',v['provisional_business_signal']]
    for key in ('economic_drivers_positive','economic_drivers_negative'):
        lines.extend(x['claim'] for x in v[key])
    lines += ['', '## 가치평가와 기준일',v['valuation_expectations'],
        'KIS는 제공사 자체 전망이며 컨센서스가 아닙니다. PER와 FPER 차이는 저평가나 오류의 증명이 아닙니다.']
    for s in p['dated_scopes']:
        lines.append(f"{s['metric']}: {s['exact_value']} / 전망 기간 {s['period']} / 추정 {s['estimate_date']} / 회계목록 {s['fiscal_inventory_as_of']} / 현재 최신성 UNVERIFIED")
        if s.get('price_session'):
            lines.append(f"비수정 완료 종가: {Decimal(s['price_value']):,}원 / 기준일 {s['price_session']}; 조정 차트와 별도")
    lines += ['', '## 신규 매수',*[_label(k,x) for k,x in v['newbuyer'].items()],
        '', '## 가상 보유자',*[_label(k,x) for k,x in v['holder'].items()],
        '', '## 위험과 한계',v['uncertainty'],
        '조정 차트 가격은 과거 참고값이며 비수정 종가와의 동등성이나 실물 주문가격이 입증되지 않았습니다.',
        '현재 유효 지지·무효화 가격·RR·실제 사용자 포지션은 제공되지 않았습니다.',
        '', '## 재검토 차이',p['comparison']['change'],
        'Blind와 Adjudication은 같은 동결 원본을 사용했습니다. 독립적인 추가 원본 반증은 없습니다.',
        '', '## 원본 출처', '봉인 ZIP SHA-256: '+p['source_archive'],
        '입력 SHA-256: '+p['binding']['packet_sha256'],
        '모델 출력 SHA-256: '+p['binding']['output_sha256']]
    lines += [f"{n.get('field',n.get('fact_id'))}: {n['rendered']} | source {n['source_sha']}" for n in p['numeric_claims']]
    return '\n'.join(lines)


def _label(key,value):
    if isinstance(value,str):return key+': '+value
    return key+': '+str(value)
