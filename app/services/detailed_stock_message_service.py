"""Opt-in accepted detailed stock rendering. No post-render enrichment.

Rows select immutable source/claim fields; callers cannot supply replacement
prose, labels or numbers. Rebuilding the plan is the final acceptance check.
"""

from datetime import date
import math
from typing import Literal

from pydantic import Field, model_validator

from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan, calibration_render
from app.services.accepted_decision_v2_service import AcceptedRenderValidationResult
from app.services.current_fresh_valuation import CurrentValuationView, valuation_numeric_bindings
from app.services.unified_snapshot_contract import ContractModel, digest

SECTION_ORDER = ('judgment', 'reevaluation', 'thesis_state', 'core', 'business',
                 'warnings', 'monitoring', 'price', 'flow', 'valuation')
HEADINGS = {'reevaluation': '재평가 조건', 'thesis_state': '투자 논리 상태', 'core': '핵심 판단',
            'business': '사업·실적', 'warnings': '기존 경고', 'monitoring': '핵심 모니터링',
            'price': '현재 가격 구조', 'flow': '수급·포지셔닝', 'valuation': 'Valuation'}
Section = Literal['judgment', 'reevaluation', 'thesis_state', 'core', 'business',
                  'warnings', 'monitoring', 'price', 'flow', 'valuation']


class RowSelection(ContractModel):
    section: Literal['reevaluation', 'business', 'warnings', 'monitoring', 'price', 'flow']
    owner: Literal['core_claim', 'source_numeric']
    ref: str = Field(min_length=1)
    field_path: str | None = None

    @model_validator(mode='after')
    def exact_owner_shape(self):
        if (self.owner == 'source_numeric') != bool(self.field_path):
            raise ValueError('detailed_row_owner_field_path_mismatch')
        return self


class DetailedRow(ContractModel):
    row_id: str
    section: Section
    text: str
    source_fact_ids: tuple[str, ...]
    source_hashes: tuple[str, ...]
    numeric_registry_keys: tuple[str, ...] = ()
    formatting_contract: str
    visibility: Literal['VISIBLE'] = 'VISIBLE'
    acceptance_sha256: str


class DetailedStockMessagePlan(ContractModel):
    contract: Literal['accepted-detailed-stock-message-v1'] = 'accepted-detailed-stock-message-v1'
    ticker: str
    source_generation_id: str
    execution_generation_id: str
    evidence_packet_sha256: str
    source_stock_sha256: str
    accepted_calibration: AcceptedDetailedCalibrationPlan
    core: dict
    pass_a: dict
    source_stock: dict
    valuation: CurrentValuationView
    selections: tuple[RowSelection, ...]
    rows: tuple[DetailedRow, ...]
    acceptance: dict
    acceptance_sha256: str


class DetailedUnknownMessagePlan(ContractModel):
    contract: Literal['accepted-detailed-unknown-message-v1'] = 'accepted-detailed-unknown-message-v1'
    ticker: str
    source_generation_id: str
    execution_generation_id: str
    source_stock: dict
    source_authority: dict
    local_seed: dict
    decision: dict
    valuation: CurrentValuationView
    rows: tuple[DetailedRow, ...]
    acceptance: dict
    acceptance_sha256: str


class RenderedDetailedUnknown(ContractModel):
    contract: Literal['accepted-detailed-unknown-render-v1'] = 'accepted-detailed-unknown-render-v1'
    ticker: str
    decision_mode: Literal['UNKNOWN_LIMIT'] = 'UNKNOWN_LIMIT'
    accepted_decision: Literal['OBSERVE'] = 'OBSERVE'
    accepted_directional_balance: None = None
    text: str
    validation: AcceptedRenderValidationResult


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _safe_prose(text, refs):
    from app.services.accepted_decision_v2_service import _EXACT_NUMBER, _INTERNAL_LABEL_LANGUAGE, _ORDER_LANGUAGE
    _require(isinstance(text, str) and bool(text.strip()), 'detailed_empty_model_text')
    _require(not (_EXACT_NUMBER.search(text) or _INTERNAL_LABEL_LANGUAGE.search(text)
                  or _ORDER_LANGUAGE.search(text)), 'detailed_unbound_number_or_internal_language')
    _require(not any(ref and ref in text for ref in refs), 'detailed_internal_ref_leak')
    _require(not any(len(token) == 64 and all(c in '0123456789abcdef' for c in token)
                     for token in text.split()), 'detailed_hash_leak')
    return text


def _row(section, key, text, *, facts=(), hashes=(), numeric=(), formatting='accepted-model-text-v1'):
    values = dict(row_id=section + ':' + key, section=section, text=text, source_fact_ids=tuple(facts),
        source_hashes=tuple(hashes), numeric_registry_keys=tuple(numeric), formatting_contract=formatting,
        visibility='VISIBLE')
    return DetailedRow(**values, acceptance_sha256=digest(values))


def section_coverage(rows):
    owners = dict(judgment='accepted_three_axis_or_whole_decision_limit',
        reevaluation='accepted_structured_condition', thesis_state='current_accepted_state_materializer',
        core='accepted_decision', business='accepted_business_claim', warnings='current_display_approved_warning',
        monitoring='accepted_structured_checkpoint', price='fresh_numeric_registry',
        flow='fresh_numeric_registry_or_explicit_unavailable', valuation='current_security_valuation_view')
    result = {}
    for section in SECTION_ORDER:
        selected = [r for r in rows if r.section == section]
        value = dict(owner=owners[section], rows=[r.row_id for r in selected],
            state='OWNED_ROWS' if selected else 'OMITTED_NO_ACCEPTED_CURRENT_OWNER',
            input_contracts=sorted({r.formatting_contract for r in selected}),
            visibility_rule='MANDATORY' if section in {'judgment', 'core', 'price', 'valuation'}
                else 'ONLY_BOUND_ACCEPTED_ROWS',
            omitted_reason=None if selected else 'NO_BOUND_ACCEPTED_ROW_FROM_CURRENT_OWNER',
            row_source_bindings={r.row_id: dict(fact_ids=list(r.source_fact_ids), hashes=list(r.source_hashes),
                                               numeric_keys=list(r.numeric_registry_keys)) for r in selected})
        value['acceptance_sha256'] = digest(value)
        result[section] = value
    return result


def _valuation_rows(valuation):
    _require({m.metric for m in valuation.metrics} == {'PER', 'PBR', 'fPER'}
             and len(valuation.metrics) == 3, 'detailed_valuation_section_incomplete')
    rows = []
    bindings = valuation_numeric_bindings(valuation)
    for metric in valuation.metrics:
        _require(not metric.overall_direction_use, 'detailed_valuation_direction_misuse')
        # Re-validate even model_copy objects before emitting any exact number.
        type(metric).model_validate(metric.model_dump(mode='json'))
        _require(metric.numerator == valuation.price, 'detailed_valuation_numerator_mismatch')
        text = ('판단 자료 부족' if metric.status == 'UNAVAILABLE' else 'N/M'
                if metric.status == 'NOT_MEANINGFUL' else f'{metric.value:,.2f}배')
        if metric.native_snapshot is not None and metric.display_eligible:
            snapshot = metric.native_snapshot
            label = ('Kiwoom' if snapshot.provider == 'kiwoom' else
                     'Finnhub TTM' if snapshot.metric == 'PER' else 'Finnhub quarterly')
            text += f' · {label} snapshot'
        bound = bindings.get(metric.metric)
        rows.append(_row('valuation', metric.metric, metric.metric + ': ' + text,
            facts=(bound['fact']['fact_id'],) if bound else (),
            hashes=(digest(valuation.model_dump(mode='json')), *metric.input_hashes)
                + ((digest(bound['fact']), digest(bound['registry'])) if bound else ()),
            numeric=(bound['registry']['fact_id'] + ':' + bound['registry']['field_path'],)
                if bound else (), formatting='current-valuation-typed-state-v1'))
    return rows


def build_unknown_plan(*, source_stock, source_authority, local_seed, decision,
                       execution_generation_id, valuation):
    from scripts.r2b_r2_preflight import preflight_subject
    from scripts.r2b_r2_contract import DIRECTION_BUCKETS, validate_unknown
    source = source_stock
    _require(source['contract'] == 'fresh-financial-stock-owner-v1', 'detailed_fresh_owner_required')
    stock = source['packet']['stocks'][0]
    _require(source['packet_sha256'] == digest(source['packet']), 'detailed_packet_binding_mismatch')
    readiness, prepared = preflight_subject(source, source_authority, local_seed,
        generation=execution_generation_id, cutoff=source['packet']['generated_at'])
    _require(readiness['status'] == 'PASS' and prepared['mode'] == 'UNKNOWN_LIMIT',
             'detailed_unknown_not_source_qualified')
    check = validate_unknown(decision, mode=prepared['mode'], recovery=prepared['recovery'],
                             capability={k: [] for k in DIRECTION_BUCKETS})
    _require(valuation.model_dump(mode='json') == source['valuation_view']
             and valuation.ticker == source['ticker'] and valuation.run_id == source['fresh_run_id']
             and valuation.price_context_sha256 == digest(stock['current_price_context']),
             'detailed_valuation_source_mismatch')
    rows = [
        _row('judgment', 'limit', 'AI 분석 판단: OBSERVE\n판단 균형: 판단 자료 부족\n판단 확신도: 판단 자료 부족\n신규 매수자: OBSERVE\n보유자: OBSERVE',
             hashes=(digest(check),), formatting='whole-decision-limit-v1'),
        _row('core', 'limit', '방향 판단에 사용할 사업 증거가 부족합니다. 중립 의견이나 보유 권고를 뜻하지 않습니다.',
             hashes=(digest(check),), formatting='whole-decision-limit-v1')]
    labels = {'QUALIFIED_FINANCIAL_LINEAGE': '기간·기업 기준과 출처 연결이 검증된 정식 재무 공시',
              'COMPARABLE_FINANCIAL_OBSERVATION': '기간·기업·통화·연결 기준이 일치하는 비교 재무 수치',
              'VERIFIED_BUSINESS_EVENT': '공식 원문으로 확인된 사업 성과'}
    for key in decision['required_next_evidence']:
        recovery = prepared['recovery'][key]
        _require(recovery['kind'] in labels, 'detailed_unowned_recovery_label')
        rows.append(_row('reevaluation', key, labels[recovery['kind']],
            hashes=(digest(recovery),), formatting='source-recovery-catalog-v1'))
    quote = stock['current_price_context']
    prices = [f for f in stock['fact_catalog'] if f['fact_type'] == 'price'
              and f.get('fields', {}).get('current_price') == quote['current_price']]
    _require(len(prices) == 1, 'detailed_current_price_owner_not_unique')
    rows.append(_numeric(RowSelection(section='price', owner='source_numeric', ref=prices[0]['fact_id'],
                                      field_path='fields.current_price'), source))
    rows.append(_row('flow', 'unavailable', '자료 부족', hashes=(digest(source),), formatting='explicit-unavailable-v1'))
    rows.extend(_valuation_rows(valuation))
    rows.sort(key=lambda r: SECTION_ORDER.index(r.section))
    receipt = dict(contract='detailed-unknown-acceptance-v1', source_stock_sha256=digest(source),
        source_authority_sha256=digest(source_authority), local_seed_sha256=digest(local_seed),
        decision_sha256=digest(decision), preflight_sha256=digest(readiness),
        valuation_sha256=digest(valuation.model_dump(mode='json')), execution_generation_id=execution_generation_id,
        rows_sha256=digest([r.model_dump(mode='json') for r in rows]), section_coverage=section_coverage(rows))
    return DetailedUnknownMessagePlan(ticker=source['ticker'], source_generation_id=source['fresh_run_id'],
        execution_generation_id=execution_generation_id, source_stock=source, source_authority=source_authority,
        local_seed=local_seed, decision=decision, valuation=valuation, rows=tuple(rows),
        acceptance=receipt, acceptance_sha256=digest(receipt))


def _numeric(selection, source):
    stock = source['packet']['stocks'][0]
    matches = [f for f in stock['fact_catalog'] if f['fact_id'] == selection.ref]
    _require(len(matches) == 1, 'detailed_numeric_fact_not_unique')
    fact = matches[0]
    node = source['source_graph'].get(selection.ref)
    _require(node and node['fact_sha256'] == digest(fact), 'detailed_source_graph_mismatch')
    _require(fact.get('ticker', stock['ticker']) == stock['ticker'], 'detailed_wrong_ticker')
    rows = [r for r in stock['numeric_registry'] if r['fact_id'] == selection.ref
            and r['field_path'] == selection.field_path]
    _require(len(rows) == 1 and rows[0].get('registered') and rows[0].get('prose_allowed'),
             'detailed_numeric_registry_not_display_eligible')
    reg = rows[0]
    value = fact
    for token in selection.field_path.split('.'):
        value = value[token]
    _require(not isinstance(value, bool) and isinstance(value, (float, int)) and math.isfinite(value)
             and value == reg['value'], 'detailed_numeric_value_mismatch')
    allowed_types = {'business': {'earnings', 'earnings_comparison'},
                     'price': {'price', 'chart_timeframe', 'chart_structure'},
                     'flow': {'investor_flow', 'chart_timeframe', 'positioning'}}
    _require(fact['fact_type'] in allowed_types.get(selection.section, set()), 'detailed_numeric_section_ownership')
    if selection.section in {'price', 'flow'}:
        quote = stock['current_price_context']
        _require(str(fact['as_of_date']) == str(quote['as_of_date']), 'detailed_stale_price_or_flow')
        _require(source['fresh_run_id'] == source['packet']['source_time_domains']['run_id'],
                 'detailed_old_price_or_flow_generation')
    labels = reg.get('approved_labels', [])
    _require(labels and isinstance(labels[0], str), 'detailed_numeric_label_unowned')
    label = labels[0]
    unit = reg['unit']
    # Formatting follows the canonical registry's unit; never a price currency
    # copied onto an issuer financial amount or an ad-hoc currency conversion.
    precision = 0 if unit in {'KRW', 'shares', 'count'} else 2
    text = f'{label}: {value:,.{precision}f} {unit}'
    return _row(selection.section, selection.ref + ':' + selection.field_path, text,
        facts=(selection.ref,), hashes=(digest(fact), digest(node), digest(reg)),
        numeric=(selection.ref + ':' + selection.field_path,), formatting='canonical-registry-unit-v1')


def build_detailed_plan(*, packet, accepted, source_stock, core, pass_a, valuation, selections=()):
    """Only accepted Core/A/B and current source owners can populate rows."""
    _require(isinstance(accepted, AcceptedDetailedCalibrationPlan), 'detailed_accepted_stage_provenance_required')
    calibration_render(packet, accepted)
    source = source_stock
    stock = source['packet']['stocks'][0]
    _require(source['status'] == 'PASS' and source['contract'] == 'fresh-financial-stock-owner-v1',
             'detailed_fresh_owner_required')
    _require(source['fresh_run_id'] == accepted.source_generation_id
             and stock['ticker'] == packet.ticker == source['ticker'], 'detailed_source_identity_mismatch')
    _require(source['packet_sha256'] == digest(source['packet'])
             and source['evidence_packet'] == packet.model_dump(mode='json'), 'detailed_packet_binding_mismatch')
    _require(valuation.model_dump(mode='json') == source['valuation_view']
             and valuation.ticker == packet.ticker and valuation.run_id == accepted.source_generation_id,
             'detailed_valuation_source_mismatch')
    quote = stock['current_price_context']
    _require(valuation.price_context_sha256 == digest(quote)
             and valuation.price_session.isoformat() == quote['as_of_date']
             and valuation.price == quote['current_price'], 'detailed_current_price_mismatch')
    _require(date.fromisoformat(quote['as_of_date']) <= date.fromisoformat(str(packet.assessment_date)),
             'detailed_future_price')
    _require(core.get('binding_sha256') == digest({'atomic': core['atomic_claims'], 'effects': core['effects']}),
             'detailed_core_binding_mismatch')
    lineage = {c['claim_ref']: tuple(c['parent_source_refs']) for c in core['atomic_claims']}
    _require(lineage == accepted.claim_lineage, 'detailed_accepted_core_lineage_mismatch')
    claims = {c['claim_ref']: c for c in core['atomic_claims']}
    _require(len(claims) == len(core['atomic_claims']), 'detailed_duplicate_claim')
    allowed = {r.ref_id for r in packet.evidence}
    _require(all(refs and set(refs) <= allowed for refs in lineage.values()), 'detailed_claim_source_unbound')
    # The selected Pass-A result must be the one consumed by the accepted B.
    provenance = accepted.stage_provenance or {}
    _require(provenance.get('pass_a_sha256') == digest(pass_a)
             and provenance.get('core_sha256') == digest(core)
             and provenance.get('pass_b_sha256') == digest(accepted.decision)
             and provenance.get('fresh_stock_sha256') == digest(source)
             and bool(provenance.get('pass_b_input_sha256')), 'detailed_pass_a_binding_missing')
    refs = set(lineage) | allowed
    decision = accepted.decision
    rows = []
    owned_refs = tuple(sorted({r for values in lineage.values() for r in values}))
    score = decision['directional_buy_score']
    rows.append(_row('judgment', 'axes', '\n'.join([
        'AI 분석 판단: ' + decision['overall_direction'],
        f'판단 균형: BUY {score:.1f} : SELL {10-score:.1f}',
        '판단 확신도: ' + {'HIGH': '높음', 'MEDIUM': '중간', 'LOW': '낮음'}[decision['confidence']],
        '증거 성숙도: 판단 자료 부족',
        '신규 매수자: ' + {'ATTRACTIVE': 'BUY', 'WAIT': 'WAIT', 'AVOID': 'AVOID'}[decision['new_buyer']],
        '보유자: ' + {'HOLDABLE': 'HOLD', 'REVIEW': 'REVIEW', 'REDUCE': 'REDUCE'}[decision['holder']],
        _safe_prose(decision['new_buyer_reason'], refs), _safe_prose(decision['holder_reason'], refs)]),
        facts=owned_refs, hashes=(accepted.acceptance_sha256,), formatting='accepted-three-axis-v1'))
    rows.append(_row('core', 'reason', _safe_prose(decision['overall_reason'], refs),
        facts=owned_refs, hashes=(digest(core), accepted.acceptance_sha256)))
    selections = tuple(RowSelection.model_validate(r) for r in selections)
    automatic = []
    selected_claims = {r.ref for r in selections if r.owner == 'core_claim'}
    for ref in (*decision['supporting_refs'], *decision['contradicting_refs'], *decision['reevaluation_refs']):
        if ref in selected_claims:
            continue
        _require(ref in claims, 'detailed_unaccepted_claim')
        effect = core['effects'][ref]['effect']
        if effect.startswith('DIRECTIONAL_'):
            automatic.append(RowSelection(section='business', owner='core_claim', ref=ref))
        elif effect == 'REEVALUATION_CONDITION':
            automatic.append(RowSelection(section='reevaluation', owner='core_claim', ref=ref))
        selected_claims.add(ref)
    _require(len(set((r.section, r.owner, r.ref, r.field_path) for r in selections)) == len(selections),
             'detailed_duplicate_row_selection')
    prices = [f for f in stock['fact_catalog'] if f['fact_type'] == 'price'
              and f.get('fields', {}).get('current_price') == quote['current_price']]
    _require(len(prices) == 1, 'detailed_current_price_owner_not_unique')
    mandatory_price = RowSelection(section='price', owner='source_numeric', ref=prices[0]['fact_id'],
                                    field_path='fields.current_price')
    effective_selections = (*selections, *automatic)
    if mandatory_price not in effective_selections:
        effective_selections = (*effective_selections, mandatory_price)
    for selected in effective_selections:
        if selected.owner == 'source_numeric':
            rows.append(_numeric(selected, source))
            continue
        _require(selected.ref in claims and selected.field_path is None, 'detailed_unaccepted_claim')
        claim = claims[selected.ref]
        effect = core['effects'][selected.ref]['effect']
        if selected.section in {'reevaluation', 'monitoring'}:
            _require(effect == 'REEVALUATION_CONDITION' and claim['claim'].get('logical_condition'),
                     'detailed_checkpoint_type_mismatch')
        else:
            _require(selected.section == 'business' and effect.startswith('DIRECTIONAL_'),
                     'detailed_claim_section_mismatch')
        rows.append(_row(selected.section, selected.ref, _safe_prose(claim['claim']['text'], refs),
            facts=lineage[selected.ref], hashes=(digest(claim), digest(core))))
    _require(sum(r.section == 'monitoring' for r in rows) in {0, 2, 3, 4}, 'detailed_monitoring_cardinality')
    if not any(r.section == 'flow' for r in rows):
        rows.append(_row('flow', 'unavailable', '자료 부족', hashes=(digest(source),),
                         formatting='explicit-unavailable-v1'))
    rows.extend(_valuation_rows(valuation))
    rows.sort(key=lambda r: SECTION_ORDER.index(r.section))
    receipt = dict(contract='detailed-stock-acceptance-v1', ticker=packet.ticker,
        source_generation_id=accepted.source_generation_id, execution_generation_id=accepted.execution_generation_id,
        evidence_packet_sha256=digest(packet.model_dump(mode='json')), source_stock_sha256=digest(source),
        calibration_sha256=digest(accepted.model_dump(mode='json')), core_sha256=digest(core), pass_a_sha256=digest(pass_a),
        valuation_sha256=digest(valuation.model_dump(mode='json')),
        selections_sha256=digest([r.model_dump(mode='json') for r in selections]),
        rows_sha256=digest([r.model_dump(mode='json') for r in rows]), section_coverage=section_coverage(rows))
    return DetailedStockMessagePlan(ticker=packet.ticker, source_generation_id=accepted.source_generation_id,
        execution_generation_id=accepted.execution_generation_id, evidence_packet_sha256=receipt['evidence_packet_sha256'],
        source_stock_sha256=receipt['source_stock_sha256'], accepted_calibration=accepted, source_stock=source,
        core=core, pass_a=pass_a, valuation=valuation, selections=selections, rows=tuple(rows),
        acceptance=receipt, acceptance_sha256=digest(receipt))


def detailed_render(packet, plan):
    if isinstance(plan, DetailedUnknownMessagePlan):
        expected = build_unknown_plan(source_stock=plan.source_stock, source_authority=plan.source_authority,
            local_seed=plan.local_seed, decision=plan.decision, execution_generation_id=plan.execution_generation_id,
            valuation=plan.valuation)
        _require(expected == plan and packet.model_dump(mode='json') == plan.source_stock['evidence_packet'],
                 'detailed_unknown_acceptance_plan_mismatch')
        return RenderedDetailedUnknown(ticker=plan.ticker, text=_render_rows(packet, plan.rows),
                                        validation={'valid': True, 'errors': []})
    expected = build_detailed_plan(packet=packet, accepted=plan.accepted_calibration,
        source_stock=plan.source_stock, core=plan.core, pass_a=plan.pass_a, valuation=plan.valuation,
        selections=plan.selections)
    _require(expected == plan, 'detailed_acceptance_plan_mismatch')
    original = calibration_render(packet, plan.accepted_calibration)
    return original.model_copy(update={'text': _render_rows(packet, plan.rows)})


def _render_rows(packet, rows):
    lines = [f'{packet.company_name}({packet.ticker})', f'판단 기준일: {packet.assessment_date}']
    for section in SECTION_ORDER:
        selected = [r for r in rows if r.section == section]
        if not selected:
            continue
        lines.append('')
        if section in HEADINGS:
            lines.append(HEADINGS[section])
        lines.extend(r.text for r in selected)
    return '\n'.join(lines)


def final_detailed_audit(text, packet, plan):
    _require(text == detailed_render(packet, plan).text, 'detailed_post_render_mutation')
    return dict(status='PASS', acceptance_sha256=plan.acceptance_sha256,
                exact_sender_text_sha256=digest(text), post_hoc_sections=0)
