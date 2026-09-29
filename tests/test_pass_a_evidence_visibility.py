from copy import deepcopy

import pytest

from scripts.m12cq_two_pass_contract import build_pass_a_subject_context
from scripts.m12da_source_use_contract import canonical_sha256
from scripts.pass_a_evidence_visibility import decide_pass_a_visibility
from tests.test_m12cq_two_pass_policy_shadow import _catalog, _context
from tests.test_m12dk_current_source_authority import inputs, run


@pytest.mark.parametrize("category", ["quality", "context", "earnings", "thesis", "macro"])
@pytest.mark.parametrize("source_ref", ["stock.technical_context", "technical_feature:renamed"])
def test_explicit_family_exclusion_cannot_be_laundered_by_category(category, source_ref):
    row = dict(ref_id="arbitrary-renamed-ref", source_ref=source_ref, category=category)
    record = dict(authority_state="UNRESOLVED", allowed_uses=["CONTEXT"], source_family="unclassified")
    old = deepcopy((row, record))
    args = dict(authority=record, source_authority_contract="source-authority-v1",
                eligible_uses=["CONTEXT"], stage_contract_permits=True)
    first = decide_pass_a_visibility(row, **args)
    assert first == decide_pass_a_visibility(row, **args)
    assert not first.visible_to_pass_a
    assert first.reason_code == "EXPLICIT_FAMILY_PASS_A_EXCLUSION"
    assert canonical_sha256(first.model_dump(mode="json", exclude={"decision_sha256"})) == first.decision_sha256
    assert (row, record) == old


def test_authority_family_exclusion_survives_cosmetic_source_path():
    decision = decide_pass_a_visibility(dict(ref_id="renamed", source_ref="unknown", category="quality"),
        authority=dict(source_family="PRICE_VALUATION_TECHNICAL_EXCLUDED_FROM_PASS_A"),
        source_authority_contract="v1", eligible_uses=["CONTEXT"], stage_contract_permits=True)
    assert not decision.visible_to_pass_a


@pytest.mark.parametrize("source_ref,uses", [
    ("stock.thesis.core_thesis", ["PASS_A_ARCHETYPE"]),
    ("stock.thesis.macro_exposures", ["PASS_A_VALUATION_TIER"]),
    ("stock.fact_catalog.financial_quality:issuer", ["CONTEXT"]),
    ("stock.fact_catalog.working-capital-relation:issuer", ["EARNINGS_QUALITY_CONTEXT"]),
])
def test_approved_uses_survive_explicit_family_intersection(source_ref, uses):
    decision = decide_pass_a_visibility(dict(ref_id="ref", source_ref=source_ref, category="quality"),
        authority=dict(authority_state="RESOLVED"), source_authority_contract="v1",
        eligible_uses=uses, stage_contract_permits=True)
    assert decision.visible_to_pass_a


@pytest.mark.parametrize("overrides", [dict(eligible_uses=[]), dict(stage_contract_permits=False),
                                        dict(current_stage="PASS_B")])
def test_all_intersection_dimensions_required(overrides):
    args = dict(authority=dict(authority_state="RESOLVED"), source_authority_contract="v1",
                eligible_uses=["CONTEXT"], stage_contract_permits=True)
    args.update(overrides)
    assert not decide_pass_a_visibility(dict(ref_id="r", source_ref="stock.thesis.core_thesis"),
                                       **args).visible_to_pass_a


def test_builder_uses_decision_and_keeps_audit_outside_model_view():
    context, catalog = _context(), _catalog()
    quality = next(r for r in context['evidence_packets'][0]['evidence'] if r['ref_id']=='core:quality')
    quality['source_ref'] = 'stock.technical_context'
    before = deepcopy((context, catalog))
    audit = []
    result = build_pass_a_subject_context(context=context, ticker='RENAMED', catalog=catalog,
                                         visibility_audit=audit)
    assert 'core:quality' not in {r['ref_id'] for r in result['eligible_non_price_evidence']}
    assert 'core:thesis' in {r['ref_id'] for r in result['eligible_non_price_evidence']}
    assert next(r for r in audit if r['ref_id']=='core:quality')['reason_code']=='EXPLICIT_FAMILY_PASS_A_EXCLUSION'
    assert 'visibility_audit' not in result and (context, catalog)==before


@pytest.mark.parametrize("path", ['stock.thesis.core_thesis', 'stock.thesis.macro_exposures'])
def test_current_authority_and_independent_preflight_remain_approved(path):
    result = run(inputs((path,)))
    assert result['gate']['receipt']['status']=='PASS'
    assert result['gate']['model_context']['eligible_claim_refs']


def test_family_denied_parent_cannot_hide_in_a_claim():
    context, catalog = _context(), _catalog()
    row = context['evidence_packets'][0]['evidence'][0]
    row['source_ref'] = 'stock.technical_context'
    result = build_pass_a_subject_context(context=context, ticker='RENAMED', catalog=catalog)
    assert not result['eligible_claim_refs']
