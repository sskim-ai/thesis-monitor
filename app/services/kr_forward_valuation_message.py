"""Typed KR valuation rows; immutable detailed base, no post-render patching."""
from decimal import Decimal
from typing import Literal

from app.services.detailed_stock_message_service import (
    DetailedStockMessagePlan, DetailedUnknownMessagePlan, DetailedRow,
    detailed_render, _row, _render_rows,
)
from app.services.kr_forward_valuation_context import KrForwardValuationView, forward_states, forward_bindings
from app.services.unified_snapshot_contract import ContractModel, digest


class KrForwardMessagePlan(ContractModel):
    contract: Literal['accepted-kr-forward-valuation-message-v1'] = 'accepted-kr-forward-valuation-message-v1'
    base: DetailedStockMessagePlan | DetailedUnknownMessagePlan
    forward: KrForwardValuationView
    rows: tuple[DetailedRow, ...]
    acceptance_sha256: str


def valuation_rows(view):
    view=KrForwardValuationView.model_validate(view)
    bindings=forward_bindings(view)
    rows=[]
    for item in forward_states(view):
        metric=item['metric']
        binding=bindings.get(metric)
        if binding:
            value=Decimal(item['value'])
            text=f'{value:,.2f}배' if metric!='FY1_EPS' else f'{value:,f}원'
        else:
            text='N/M' if item['state']=='NOT_MEANINGFUL' else '자료 없음'
        label=item['label']+': '+text
        if item['estimate_date']:
            label+=' · KIS Research '+item['estimate_date']+' 추정'
        if item['price_date']:
            label+=' · '+item['price_date']+' 정규장 종가 기준'
        rows.append(_row('valuation',metric,label,
            facts=(item['fact_ref'],) if binding else (),
            hashes=(digest(view.model_dump(mode='json')),item['input_receipt_sha256']),
            numeric=(binding['registry']['fact_id']+':'+binding['registry']['field_path'],) if binding else (),
            formatting='kr-fy1-distinct-current-research-valuation-v1'))
    return rows


def build_plan(packet, base, forward):
    forward=KrForwardValuationView.model_validate(forward)
    detailed_render(packet,base)
    if (packet.ticker!=forward.native.ticker or base.valuation!=forward.native
            or base.source_generation_id!=forward.native.run_id):
        raise ValueError('kr_forward_render_source_binding_gap')
    # Keep the existing PER/PBR rows byte-identical. Replace only generic fPER.
    rows=tuple(r for r in base.rows if not (r.section=='valuation' and r.row_id=='valuation:fPER'))
    if len(rows)!=len(base.rows)-1:
        raise ValueError('kr_forward_generic_fper_row_not_unique')
    rows=(*rows,*valuation_rows(forward))
    receipt=digest(dict(base=base.model_dump(mode='json'),forward=forward.model_dump(mode='json'),
        rows=[r.model_dump(mode='json') for r in rows]))
    return KrForwardMessagePlan(base=base,forward=forward,rows=rows,acceptance_sha256=receipt)


def render(packet, plan):
    expected=build_plan(packet,plan.base,plan.forward)
    if expected!=plan:
        raise ValueError('kr_forward_render_plan_drift')
    return detailed_render(packet,plan.base).model_copy(update={'text':_render_rows(packet,plan.rows)})


def audit(text, packet, plan):
    if render(packet,plan).text!=text:
        raise ValueError('kr_forward_post_render_mutation')
    return dict(status='PASS',acceptance_sha256=plan.acceptance_sha256,
        exact_sender_text_sha256=digest(text),post_hoc_sections=0)
