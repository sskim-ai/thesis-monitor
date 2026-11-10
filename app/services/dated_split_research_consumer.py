"""Offline, opt-in projection of sealed ADJ and split BLIND; no new stance or rights."""
from copy import deepcopy
from decimal import Decimal
import json
import re

from app.services.dated_research_model import digest, encoded, reference_catalog
from app.services.dated_research_review_v2 import (
    render_numeric_citations, source_bound_temporal, split_quality_review, validate_split,
)

CONTRACT = 'C22K_V2_DATED_RESEARCH_CONSUMER'
AXES = ('newbuyer_fundamental_attractiveness', 'newbuyer_entry_timing')


def _prose(text):
    # Do not correct a model sentence or certify free-prose numbers from structured citations.
    if re.search(r'\d', text):
        return dict(text=None, original_text_sha256=digest(text.encode()),
                    withheld_reason='FREE_PROSE_NUMERIC_COVERAGE_NOT_PROVEN')
    return dict(text=text, original_text_sha256=digest(text.encode()))


def _source_sha(ref, catalog, view):
    entry = catalog['refs'][ref]
    if entry['kind'] == 'financial':
        return entry['source_sha256']
    if entry['kind'] == 'valuation_locator_not_owner':
        return entry['original_fact']['raw_sha256']
    if entry['kind'] == 'dated_technical':
        return view['input_provenance']['technical_source_sha256']
    return view['dated_price_structure']['source_sha256']


def _project(citations, catalog, view):
    original = {'citations': citations}
    provenance = render_numeric_citations(original, catalog, view)
    return [dict(**deepcopy(c), source_sha256=_source_sha(c['ref'], catalog, view),
                 provenance=proof) for c, proof in zip(citations, provenance, strict=True)]


def build_message(*, preview_raw, split_raw, prior_raw, prior_receipt, sealed_hashes, display_identity=None):
    """Caller supplies hash-verified members from the two pinned result archives."""
    for key, raw in (('preview', preview_raw), ('split', split_raw), ('prior', prior_raw)):
        if digest(raw) != sealed_hashes[key]:
            raise ValueError('sealed_member_hash_mismatch')
    preview = json.loads(preview_raw); view = preview['source_view']; binding = preview['source_binding']
    split = validate_split(split_raw, view=view, binding=binding, temporal=preview['temporal'])
    prior = json.loads(prior_raw)
    if (prior_receipt['accepted_sha256'] != digest(prior_raw) or
            prior_receipt.get('status') != 'ACCEPTED' or prior_receipt.get('stage') != 'ADJUDICATION'):
        raise ValueError('prior_sealed_acceptance_required')
    if (view['ticker'] != prior['ticker'] or prior['input_digest'] != binding['research_view_sha256'] or
            prior_receipt['research_view_sha256'] != binding['research_view_sha256'] or
            prior['as_of'] != view['as_of'] or any(split[a]['as_of'] != prior['as_of'] for a in AXES)):
        raise ValueError('different_research_view_or_time_join_forbidden')
    if (split['research_mode'] != 'RETROSPECTIVE_DATED_RESEARCH' or prior.get('NO_SEND') is not True or
            prior.get('Strict_NATIVE_STAGE_READY') is not False or split.get('NO_SEND') is not True or
            split.get('Strict_NATIVE_STAGE_READY') is not False or
            prior.get('thesis_comparison') != 'NOT_COMPARED_TO_REGISTERED_THESIS'):
        raise ValueError('research_NO_SEND_scope_required')
    catalog = reference_catalog(view)
    axes = {}
    for name in AXES:
        a = split[name]
        axes[name] = dict(state=a['state'], confidence=a['confidence'], claim_role=a['claim_role'],
            as_of=a['as_of'], refs=deepcopy(a['refs']), statement=_prose(a['statement']),
            pro=[_prose(s) for s in a['pro']], con=[_prose(s) for s in a['con']],
            unknown=[_prose(s) for s in a['unknown']],
            temporal_limitations=[_prose(s) for s in a['temporal_limitations']],
            change_conditions_source='Original axis statement; not newly model-issued',
            independent_economic_support=deepcopy(a['independent_economic_support']))
    valuations = []
    for row in view['valuation']:
        ref = row['source_locator']; f = row['original_fact']; t = preview['temporal'][ref]
        expected = source_bound_temporal(view, ref, mode=split['research_mode'], prepared_at=t['research_prepared_at'])
        if any(t.get(k) != v for k, v in expected.items()):
            raise ValueError('valuation_temporal_source_drift')
        fact = next(x for x in catalog['numeric_facts'] if x['ref'] == ref and x['path'] == 'value')
        valuations.append(dict(metric=row['metric'], fact=deepcopy(fact), source_sha256=_source_sha(ref,catalog,view),
            provider=f['provider'], original_contract=f['contract'], original_state=f.get('state'),
            original_use_limits=deepcopy(expected['original_use_limits']), temporal=expected,
            original_horizon_policy=deepcopy(f.get('horizon_policy')), canonical_horizon=f.get('canonical_horizon'),
            forecast_fiscal_period=f.get('forecast_fiscal_period'), estimate_basis=f.get('estimate_basis'),
            source_cutoff=None, source_cutoff_state='UNKNOWN_NOT_SUBSTITUTED_WITH_RETRIEVAL',
            PIT_available_at_cutoff=False,
            scope='RETROSPECTIVE_ONLY_AVAILABLE_NO_EARLIER_THAN_RECORDED_RETRIEVAL'))
    financial = []
    for row in view['financial_observations']:
        if row['role'] == 'EXCLUDED':
            continue
        f = row['original_fields']
        financial.append(dict(field=row['field'], ref=row['original_ref'], source_sha256=row['source_sha'],
            source_cutoff=row['source_cutoff'], retrieved_at=None, retrieved_at_state='UNKNOWN_IN_BOUND_VIEW',
            period_unit_scale_consolidation_quality='PARTIAL_NOT_NEWLY_RAW_AUDITED',
            observations=[deepcopy(x) for x in catalog['numeric_facts'] if x['ref']==row['original_ref']],
            anomaly_cautions=deepcopy(f.get('anomaly_cautions',[])),
            fiscal_comparability=deepcopy(f.get('fiscal_comparability')),
            limitations=deepcopy(f.get('limitations',[])), quality=deepcopy(row['original_quality'])))
    equity_negative = any(r['field'] == 'financial.equity' or r['field'] == 'financial.stockholders_equity'
        for r in view['financial_observations'] if Decimal(str(r['original_fields'].get('current_value',0))) < 0)
    warnings = ['STRUCTURAL_RISK_UNKNOWN_IS_UNASSESSED_NOT_NO_RISK', 'FINANCIAL_SOURCE_QUALITY_PARTIAL',
                'NO_CURRENT_PRICE_OR_CURRENT_ACTION', 'CONFIDENCE_CALIBRATION_AND_PROSE_TRUTH_NOT_PROVEN']
    if equity_negative and any(v['metric']=='PBR' for v in valuations):
        warnings.append('PBR_VS_NEGATIVE_REPORTED_EQUITY_SCOPE_PERIOD_CONFLICT_UNRESOLVED_NOT_UNDERVALUATION')
    technical = view['technical']; names = [r['content'].get('name') for r in view['business_mechanism']['source_context'] if r.get('content',{}).get('name')]
    identity_name=technical['company_name'];identity_source='ORIGINAL_TECHNICAL_PACKET_LABEL'
    if display_identity is not None:
        if (display_identity.get('ticker')!=view['ticker'] or not display_identity.get('name') or
                not re.fullmatch(r'[a-f0-9]{64}',display_identity.get('source_sha256',''))):
            raise ValueError('display_identity_binding_mismatch')
        identity_name=display_identity['name'];identity_source=display_identity['source_kind']
    if names:identity_name=names[0];identity_source='PUBLIC_PROVIDER_PROFILE'
    periods = {}
    for code, q in technical['technical_context_quality'].items():
        if code not in ('D','W','M'):
            continue
        label = technical['dated_period_labels_and_ends'].get(q['timeframe'],{})
        periods[q['timeframe']] = dict(original_label=q.get('last_completed_bar'),
            completed_period_end=label.get('completed_period_end') or q.get('last_completed_bar'),
            count=q['bar_count'], original_quality=q['status'], current_reasoning_allowed=q['usable_for_current_reasoning'],
            original_cautions=deepcopy(q['reasons']))
    message = dict(contract=CONTRACT, ticker=view['ticker'], company_name=identity_name,
        company_name_source=identity_source, display_identity=deepcopy(display_identity), as_of=view['as_of'],
        research_mode=split['research_mode'], NO_SEND=True, default_OFF=True, Strict_READY='0/22',
        current_price_grant=False, thesis_comparison='NOT_COMPARED_TO_REGISTERED_THESIS',
        binding=deepcopy(binding), sealed_hashes=deepcopy(sealed_hashes),
        prior_panel=dict(scope='PRIOR_C22G_ADJ_RESEARCH_ONLY',stage=prior['stage'],as_of=prior['as_of'],
            overall={**deepcopy(prior['overall']), 'statement':_prose(prior['overall']['statement'])},
            holder_virtual={**deepcopy(prior['holder_virtual']), 'statement':_prose(prior['holder_virtual']['statement'])},
            legacy_newbuyer_comparison_only=dict(state=prior['newbuyer']['state'],source_sha256=sealed_hashes['prior']),
            actual_holdings_or_private_thesis_used=False),
        split_panel=dict(scope='C22J_V3_SPLIT_BLIND_RESEARCH_ONLY',stage='BLIND',axes=axes,
                         citations=_project(split['citations'],catalog,view)),
        prior_citations=_project(prior['citations'],catalog,view),
        valuations=valuations, missing_metrics={k:'자료 부족' for k,aliases in
            {'PER':('PER',),'PBR':('PBR',),'fPER':('FPER','FORWARD_PE'),'FY1_EPS':('FY1_EPS',)}.items()
            if not any(v['metric'] in aliases for v in valuations)},
        financial=financial, technical_periods=periods, native_semantics=deepcopy(technical['native_field_semantics']),
        structural_risk=dict(state=split['structural_risk'],meaning='UNASSESSED_SENTINEL_NOT_RISK_ABSENT' if split['structural_risk']=='UNKNOWN' else 'ORIGINAL_MODEL_STATE'),
        quality_report=split_quality_review(split,view=view), warnings=warnings,
        derived_explanation_scope='CONSUMER_EXPLANATION_DERIVED_NOT_MODEL_ISSUED',
        new_overall_or_holder_issued=False)
    _validate_shape_and_projection(message, view=view)
    return message


def _validate_shape_and_projection(message, *, view):
    if (message['NO_SEND'] is not True or message['default_OFF'] is not True or
            message['Strict_READY'] != '0/22' or message['current_price_grant'] is not False or
            message['new_overall_or_holder_issued'] is not False or message['research_mode']!='RETROSPECTIVE_DATED_RESEARCH'):
        raise ValueError('consumer_scope_violation')
    if digest(encoded(view)) != message['binding']['research_view_sha256'] or view['as_of']!=message['as_of'] or view['ticker']!=message['ticker']:
        raise ValueError('consumer_view_binding_mismatch')
    catalog = reference_catalog(view)
    projected=message['split_panel']['citations']+message['prior_citations']
    projected += [dict(**v['fact'],axis='valuation',source_sha256=v['source_sha256']) for v in message['valuations']]
    for row in message['financial']:
        if row['ref'] not in catalog['refs'] or row['source_sha256']!=_source_sha(row['ref'],catalog,view):
            raise ValueError('financial_projection_source_mismatch')
        projected += [dict(**f,axis='financial',source_sha256=row['source_sha256']) for f in row['observations']]
    for v in message['valuations']:
        t=v['temporal']
        expected=source_bound_temporal(view,v['fact']['ref'],mode=message['research_mode'],prepared_at=t['research_prepared_at'])
        if (v['PIT_available_at_cutoff'] is not False or t!=expected or
                v['original_use_limits']!=expected['original_use_limits']):
            raise ValueError('consumer_valuation_temporal_or_grant_drift')
    for c in projected:
        if c['source_sha256'] != _source_sha(c['ref'],catalog,view):
            raise ValueError('consumer_source_sha_mismatch')
        render_numeric_citations({'citations':[{k:c[k] for k in ('axis','ref','path','value','unit','period','basis')}]},catalog,view)
    if message['structural_risk']['state']=='UNKNOWN' and message['structural_risk']['meaning']!='UNASSESSED_SENTINEL_NOT_RISK_ABSENT':
        raise ValueError('risk_sentinel_must_not_mean_no_risk')
    if message['structural_risk']['state']=='OBSERVED_RISK' and not view['structural_risk']['occurred_risk_assertion']:
        raise ValueError('consumer_unproven_occurred_risk')


def validate_message(message, *, view, source_evidence=None):
    """Publication proof requires caller-loaded immutable seal members, not message-owned hashes."""
    _validate_shape_and_projection(message, view=view)
    if source_evidence is None:
        return dict(state='SOURCE_BOUND_PUBLICATION_NOT_PROVEN', publication_pass=False)
    evidence=deepcopy(source_evidence)
    receipt=evidence.pop('split_receipt',None)
    if (not receipt or receipt.get('state')!='ACCEPTED_PENDING_SUBSTANTIVE_REVIEW' or
            receipt.get('structural_semantic_acceptance') is not True or
            receipt.get('output_sha256')!=digest(evidence['split_raw']) or
            receipt.get('source_binding')!=json.loads(evidence['preview_raw'])['source_binding']):
        raise ValueError('original_split_acceptance_receipt_required')
    # The archive loader pins outer ZIP/member hashes. Never derive evidence from this message.
    expected=build_message(**evidence)
    if digest(encoded(view))!=expected['binding']['research_view_sha256']:
        raise ValueError('publication_source_view_mismatch')
    if encoded(message)!=encoded(expected):
        raise ValueError('source_bound_canonical_publication_mismatch')
    return dict(state='SOURCE_BOUND_PUBLICATION_PASS', publication_pass=True,
                canonical_sha256=digest(encoded(expected)), source_hashes=deepcopy(expected['sealed_hashes']))


def render_message(message):
    """Render only approved structured values and digit-free model prose; never an execution message."""
    m=message
    lines=[f"# {m['company_name']} ({m['ticker']}) — NO-SEND",
        f"원본 연구 기준시각: {m['as_of']} / {m['research_mode']}",
        '과거 날짜의 회고 연구입니다. 현재가격·실시간 매매 판단 없음. 재무 품질 PARTIAL / Strict READY 0/22.',
        '개인 보유·등록 투자논리는 사용하지 않았습니다. NOT_COMPARED_TO_REGISTERED_THESIS.']
    for name,a in m['split_panel']['axes'].items():
        lines += [f"## {name} — {a['state']} / {a['confidence']}",'출처: C22J_V3_SPLIT_BLIND_RESEARCH_ONLY / BLIND']
        for heading,cells in [('판단·변경 조건',[a['statement']]),('찬성 근거',a['pro']),('반대 근거',a['con']),('미확인',a['unknown']),('시점·사용권 주의',a['temporal_limitations'])]:
            lines += ['### '+heading]+['- '+c['text'] for c in cells if c['text']]
            if any(c['text'] is None for c in cells):lines+=['- 원문 숫자 포함 문장은 전수 검증하지 않아 재인용을 생략했습니다. 구조화 사실·원본 SHA를 참조하세요.']
    p=m['prior_panel'];lines += ['## 과거 판단 별도 패널','PRIOR_C22G_ADJ_RESEARCH_ONLY / ADJUDICATION / '+p['as_of'],
        f"Overall: {p['overall']['state']} / Virtual Holder: {p['holder_virtual']['state']}",
        '실제 보유자 판단이 아닙니다. V3에서 새 Overall·Holder를 계산하지 않았습니다.',
        '레거시 NewBuyer(비교 전용): '+p['legacy_newbuyer_comparison_only']['state']]
    for k in ('overall','holder_virtual'):
        if p[k]['statement']['text']:lines += [p[k]['statement']['text']]
    lines += ['## 원본 밸류에이션','기존 계약과 사용권을 유지합니다. 조회시각 이후 이용 가능한 회고 맥락이며 PIT·단독 방향·현재가격 승인이 아닙니다.']
    for v in m['valuations']:
        f=v['fact'];t=v['temporal'];lines += [f"- {v['metric']}: {f['value']} {f['unit']} / {v['provider']} / {f['basis']}",
            f"  조회 {t['retrieved_at']} / 지표 기간 {t['metric_period_end'] or 'UNKNOWN'} / 추정 빈티지 {t['issuer_estimate_vintage'] or 'UNKNOWN'} / 대상 {v['forecast_fiscal_period'] or v['canonical_horizon'] or 'UNKNOWN'} / 가격 기준일 {t['reference_price_as_of'] or 'UNKNOWN'}",
            f"  ref={f['ref']} / SHA={v['source_sha256']} / 원래 계약={v['original_contract']}"]
    lines += [f'- {k}: 자료 부족' for k in m['missing_metrics']]
    lines += ['## 실적·경제 관측','기간·단위·연결범위 추가 원문 감사는 하지 않았습니다. 반복이익·검증된 원인으로 확대하지 않습니다.']
    for row in m['financial']:
        lines += [f"### {row['field']} / ref={row['ref']}", 'SHA='+row['source_sha256'],
            '자료 cutoff='+str(row['source_cutoff'])+' / 조회시각 UNKNOWN']
        for f in row['observations']:
            lines += [f"- {f['path']}: {f['value']} {f['unit']} / {f['period']} / {f['basis']}"]
        lines += ['- 원본 경고: '+c for c in row['anomaly_cautions']]
        if row['fiscal_comparability']:lines += ['- 원본 회계주차: '+json.dumps(row['fiscal_comparability'],ensure_ascii=False)]
    lines += ['## 기술 관측 완료일·반대 신호']
    for name,p in m['technical_periods'].items():lines += [f"- {name}: 원래 라벨 {p['original_label']} / 완료기간 끝 {p['completed_period_end']} / {p['count']}봉 / {p['original_quality']} / 현재 판단 사용 {p['current_reasoning_allowed']}"]
    lines += ['공급자 원생 지표는 재계산하지 않았습니다. 주·월봉 라벨과 완료기간 끝을 구분합니다.']
    lines += ['## 구조화 숫자·출처','|축|ref / path|원본 값|단위|기간|basis|SHA|','|---|---|---|---|---|---|---|']
    for f in m['split_panel']['citations']:
        cells=[f['axis'],f['ref']+' / '+f['path'],str(f['value']),str(f['unit']),f['period'],f['basis'],f['source_sha256']]
        lines.append('|'+ '|'.join(x.replace('|','\\|').replace('\n',' ') for x in cells)+'|')
    lines += ['## 위험·불확실성','V3 structural_risk='+m['structural_risk']['state']+' — 미판단이며 위험 부재가 아닙니다.']
    lines += ['- '+x for x in m['warnings']+m['quality_report']['flags']]
    lines += ['자유서술 숫자·설명 전체의 참/거짓과 신뢰도 보정은 미입증(report-only). 새 모델 판단·발송·주문·현재 사용권은 생성하지 않았습니다.']
    return '\n\n'.join(lines)+'\n'
