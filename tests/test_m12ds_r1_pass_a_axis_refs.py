from copy import deepcopy

import pytest

from test_m12dj_source_authority_preflight import fixture
from scripts.m12cq_two_pass_contract import build_pass_a_subject_context
from scripts.m12cr_shadow_contract import future_pass_a_batch_schema
from scripts.m12cs_r1_provider_schema import project_provider_wire_schema
from scripts.m12ds_r1_pass_a_axis_refs import pass_a_axis_refs


def bound(uses=None, **kwargs):
    inputs = fixture(grant=True, parent_uses=uses, **kwargs)
    context = build_pass_a_subject_context(
        context={"evidence_packets": [{"ticker": inputs["ticker"], "evidence": inputs["source_packet"]["decision_evidence"]}]},
        ticker=inputs["ticker"], catalog=inputs["catalog"],
        source_use_view=inputs["projection"], source_use_binding=inputs["binding"],
        source_use_expectation=inputs["expectation"], source_generation_id=inputs["source_generation_id"],
        execution_generation_id=inputs["execution_generation_id"], require_source_use=True,
    )
    return context, dict(catalog=inputs["catalog"], chain=inputs,
                        source_metadata=inputs["source_packet"]["decision_evidence"],
                        source_generation_id=inputs["source_generation_id"], execution_generation_id=inputs["execution_generation_id"])


def schema(context, inputs):
    return future_pass_a_batch_schema(subjects=[context["ticker"]], subject_contexts={context["ticker"]: context},
                                     source_use_inputs={context["ticker"]: inputs})


@pytest.mark.parametrize("ticker", ["RENAMED", "UNSEEN"])
def test_archetype_only_kept_but_every_resolved_tier_removed(ticker):
    context, inputs = bound([["CONTEXT", "PASS_A_ARCHETYPE"]], ticker=ticker)
    original = deepcopy((context, inputs))
    axes = pass_a_axis_refs(context, inputs)
    assert axes["archetype"] == ["claim:renamed"] and axes["tier"] == []
    branches = schema(context, inputs)["properties"]["classifications"]["properties"][ticker]["anyOf"]
    assert len(branches) == 1
    assert branches[0]["properties"]["valuation_regime_tier"]["const"] == "UNRESOLVED"
    assert branches[0]["properties"]["tier_supporting_claim_refs"]["maxItems"] == 0
    assert (context, inputs) == original


@pytest.mark.parametrize("uses", [["CONTEXT", "PASS_A_VALUATION_TIER"], ["CONTEXT"]])
def test_empty_archetype_has_explicit_dependency_not_fabricated_support(uses):
    context, inputs = bound([uses])
    axes = pass_a_axis_refs(context, inputs)
    assert axes["archetype"] == []
    assert axes["tier"] == (["claim:renamed"] if "PASS_A_VALUATION_TIER" in uses else [])
    with pytest.raises(ValueError, match="BRANCH_REPRESENTATION_DEPENDENCY"):
        schema(context, inputs)


def test_restrictive_parent_intersection_not_dropped():
    rows = [{"ref_id": f"source:{n}", "category": "thesis", "label": "neutral", "statement": "Observed demand."} for n in (1, 2)]
    context, inputs = bound([["PASS_A_ARCHETYPE", "PASS_A_VALUATION_TIER"], ["PASS_A_ARCHETYPE"]], rows=rows)
    assert pass_a_axis_refs(context, inputs)["tier"] == []
    assert inputs["chain"]["projection"]["claim_records"]["claim:renamed"]["parent_source_refs"] == ["source:1", "source:2"]


@pytest.mark.parametrize("mutation", ["subject", "source_generation", "execution_generation", "metadata", "permission", "unknown", "model_view", "consumed_view"])
def test_current_binding_rejects_identity_and_digest_drift(mutation):
    context, inputs = bound()
    if mutation == "subject":
        context["ticker"] = "OTHER"
    elif mutation == "source_generation":
        inputs["source_generation_id"] = "stale"
    elif mutation == "execution_generation":
        inputs["execution_generation_id"] = "wrong"
    elif mutation == "metadata":
        inputs["source_metadata"][0]["statement"] = "changed"
    elif mutation == "permission":
        inputs["chain"]["projection"]["permission_derivation_sha256"] = "wrong"
    elif mutation == "unknown":
        context["eligible_claim_refs"].append("claim:unknown")
    elif mutation == "model_view":
        context["source_use_projection"]["claim_permissions"][0]["allowed_uses"].append("INVENTED")
    else:
        context["accepted_fundamental_claims"][0]["text"] = "changed"
    with pytest.raises(ValueError):
        schema(context, inputs)


def test_bound_schema_cannot_fall_back_to_unbound_shared_refs():
    context, _ = bound()
    with pytest.raises(ValueError, match="current_source_input_required"):
        future_pass_a_batch_schema(subjects=[context["ticker"]], subject_contexts={context["ticker"]: context})


def test_consumed_view_uses_its_existing_unicode_digest_owner():
    context, inputs = bound(rows=[{"ref_id": "source:unicode", "category": "thesis",
                                 "label": "\uc0ac\uc5c5", "statement": "\uc218\uc694 \ud655\uc778"}])
    assert pass_a_axis_refs(context, inputs)["archetype"] == ["claim:renamed"]


def test_provider_refs_keep_effective_enum_semantics_and_local_uniqueness():
    context, inputs = bound()
    internal = schema(context, inputs)
    wire, _ = project_provider_wire_schema(internal)
    for original, projected in zip(internal["properties"]["classifications"]["properties"]["RENAMED"]["anyOf"],
                                   wire["properties"]["classifications"]["properties"]["RENAMED"]["anyOf"], strict=True):
        for field in ("archetype_supporting_claim_refs", "tier_supporting_claim_refs"):
            left, right = original["properties"][field], projected["properties"][field]
            items = right["items"]
            if "$ref" in items:
                items = wire["$defs"][items["$ref"].split("/")[-1]]
            assert left["items"].get("enum") == items.get("enum")
            assert left["maxItems"] == right["maxItems"]
            assert left["uniqueItems"] is True
            assert "uniqueItems" not in right
