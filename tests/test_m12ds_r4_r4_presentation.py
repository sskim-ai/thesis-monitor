from copy import deepcopy

import pytest

from app.services.accepted_calibration_message_service import calibration_render, digest
from app.services.sec_foreign_statement_boundary_service import document_evidence_class
from tests.test_accepted_decision_v2_runtime import _packet
from tests.test_m12ds_r4_r1_production_calibration import plan_for


def test_reviewed_document_is_not_preliminary_or_annual_audit():
    html = '''<h2>Independent Auditors' Review Report</h2><p>We have reviewed the accompanying consolidated
    financial statements under Interim Financial Reporting.</p>'''
    receipt=document_evidence_class(html)
    assert receipt['evidence_class']=='AUDITOR_REVIEWED_INTERIM_STATEMENT'
    assert not receipt['annual_audit_claim']
    assert document_evidence_class('<p>Preliminary results</p>') is None
    assert document_evidence_class("<h2>Independent Auditors' Review Report</h2>") is None


def bound_plan(currency='KRW', quote=None):
    packet=_packet()
    plan=plan_for(packet)
    entries=dict(tactical_watch_low=12345.67,tactical_watch_high=23456.78,
                 tactical_currency=currency,tactical_watch_basis='owned-price-structure',tactical_watch_status='RESOLVED')
    receipt=deepcopy(plan.acceptance)
    receipt['entries_sha256']=digest(entries)
    if quote:
        receipt['quote_context_sha256']=digest(quote)
    return packet,plan.model_copy(update=dict(entries=entries,quote_context=quote,acceptance=receipt,acceptance_sha256=digest(receipt)))


def test_krw_display_only_rounding_usd_unchanged():
    packet,plan=bound_plan()
    before=deepcopy(plan.entries)
    assert '12,346 ~ 23,457 KRW' in calibration_render(packet,plan).text
    assert plan.entries==before
    packet,plan=bound_plan('USD')
    assert '12,345.67 ~ 23,456.78 USD' in calibration_render(packet,plan).text


def test_owned_asof_preserves_basis_without_invented_finality():
    packet=_packet()
    quote=dict(contract='current-price-context-v1',availability='ready',as_of_date=packet.assessment_date,
               price_basis='adjusted_close')
    packet,plan=bound_plan(quote=quote)
    assert f'가격 자료 기준: {packet.assessment_date} · 조정 종가' in calibration_render(packet,plan).text
    assert '장중' not in calibration_render(packet,plan).text
    changed=deepcopy(quote)
    changed['as_of_date']='2099-01-01'
    packet,plan=bound_plan(quote=changed)
    with pytest.raises(ValueError,match='quote_asof'):
        calibration_render(packet,plan)
    packet,plan=bound_plan()
    assert '가격 자료 기준:' not in calibration_render(packet,plan).text


def test_quote_binding_cannot_be_mutated_after_acceptance():
    quote=dict(contract='current-price-context-v1',availability='ready',as_of_date=_packet().assessment_date,
               price_basis='intraday')
    packet,plan=bound_plan(quote=quote)
    assert '장중 관측' in calibration_render(packet,plan).text
    with pytest.raises(ValueError,match='identity_or_validation'):
        calibration_render(packet,plan.model_copy(update=dict(quote_context={**quote,'price_basis':'close'})))
