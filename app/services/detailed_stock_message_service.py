"""Opt-in accepted detailed stock rendering. No post-render enrichment.

Rows select immutable source/claim fields; callers cannot supply replacement
prose, labels or numbers. Rebuilding the plan is the final acceptance check.
"""

from datetime import date
import math
from typing import Literal

from pydantic import Field, model_validator

from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan, calibration_render
from app.services.current_fresh_valuation import CurrentValuationView
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
    _require(len(set((r.section, r.owner, r.ref, r.field_path) for r in selections)) == len(selections),
             'detailed_duplicate_row_selection')
    prices = [f for f in stock['fact_catalog'] if f['fact_type'] == 'price'
              and f.get('fields', {}).get('current_price') == quote['current_price']]
    _require(len(prices) == 1, 'detailed_current_price_owner_not_unique')
    mandatory_price = RowSelection(section='price', owner='source_numeric', ref=prices[0]['fact_id'],
                                    field_path='fields.current_price')
    effective_selections = selections if mandatory_price in selections else (*selections, mandatory_price)
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
    _require({m.metric for m in valuation.metrics} == {'PER', 'PBR', 'fPER'}
             and len(valuation.metrics) == 3, 'detailed_valuation_section_incomplete')
    for metric in valuation.metrics:
        _require(not metric.overall_direction_use, 'detailed_valuation_direction_misuse')
        # Qualified multiples will need a source-owned denominator registry.
        # The current reported-business collector cannot supply that authority.
        _require(metric.status == 'UNAVAILABLE' and metric.value is None
                 and not metric.display_eligible and bool(metric.denial_reason), 'detailed_unqualified_multiple')
        rows.append(_row('valuation', metric.metric, metric.metric + ': 판단 자료 부족',
            hashes=(digest(valuation.model_dump(mode='json')),), formatting='current-valuation-unavailable-v1'))
    rows.sort(key=lambda r: SECTION_ORDER.index(r.section))
    receipt = dict(contract='detailed-stock-acceptance-v1', ticker=packet.ticker,
        source_generation_id=accepted.source_generation_id, execution_generation_id=accepted.execution_generation_id,
        evidence_packet_sha256=digest(packet.model_dump(mode='json')), source_stock_sha256=digest(source),
        calibration_sha256=digest(accepted.model_dump(mode='json')), core_sha256=digest(core), pass_a_sha256=digest(pass_a),
        valuation_sha256=digest(valuation.model_dump(mode='json')),
        selections_sha256=digest([r.model_dump(mode='json') for r in selections]),
        rows_sha256=digest([r.model_dump(mode='json') for r in rows]))
    return DetailedStockMessagePlan(ticker=packet.ticker, source_generation_id=accepted.source_generation_id,
        execution_generation_id=accepted.execution_generation_id, evidence_packet_sha256=receipt['evidence_packet_sha256'],
        source_stock_sha256=receipt['source_stock_sha256'], accepted_calibration=accepted, source_stock=source,
        core=core, pass_a=pass_a, valuation=valuation, selections=selections, rows=tuple(rows),
        acceptance=receipt, acceptance_sha256=digest(receipt))


def detailed_render(packet, plan):
    expected = build_detailed_plan(packet=packet, accepted=plan.accepted_calibration,
        source_stock=plan.source_stock, core=plan.core, pass_a=plan.pass_a, valuation=plan.valuation,
        selections=plan.selections)
    _require(expected == plan, 'detailed_acceptance_plan_mismatch')
    original = calibration_render(packet, plan.accepted_calibration)
    lines = [f'{packet.company_name}({packet.ticker})']
    for section in SECTION_ORDER:
        selected = [r for r in plan.rows if r.section == section]
        if not selected:
            continue
        lines.append('')
        if section in HEADINGS:
            lines.append(HEADINGS[section])
        lines.extend(r.text for r in selected)
    return original.model_copy(update={'text': '\n'.join(lines)})


def final_detailed_audit(text, packet, plan):
    _require(text == detailed_render(packet, plan).text, 'detailed_post_render_mutation')
    return dict(status='PASS', acceptance_sha256=plan.acceptance_sha256,
                exact_sender_text_sha256=digest(text), post_hoc_sections=0)
