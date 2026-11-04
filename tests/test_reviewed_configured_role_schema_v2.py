"""Actual native schema and live reference checks, never candidate acceptance."""
from dataclasses import replace

import pytest

from app.services import reviewed_configured_composition as owner
from app.services.reviewed_fixture_authority import build_reviewed_owned_fixture
from scripts.reviewed_configured_role_schema_v2 import configured_role_schema_v2
from scripts.reviewed_configured_semantic_adapter_v1 import configured_schema_v1

SUBJECTS = tuple(f"FIC-FIN-{i:02d}" for i in range(1, 5))
GENERATION = "m12at-deterministic-preflight"


def children():
    return {
        subject: owner.build_reviewed_configured_composition(
            build_reviewed_owned_fixture("financial:" + subject, generation=GENERATION),
            recipe_id=GENERATION + ":" + subject, consumer=owner.SCHEMA_CONSUMER,
        ) for subject in SUBJECTS
    }


def reference_values(schema, fragment):
    """Follow emitted field links, not field-name guesses or merged subjects."""
    if isinstance(fragment, list):
        return set().union(*(reference_values(schema, x) for x in fragment))
    if not isinstance(fragment, dict):
        return set()
    if "$ref" in fragment:
        prefix = "#/$defs/"
        assert fragment["$ref"].startswith(prefix)
        return reference_values(schema, schema["$defs"][fragment["$ref"][len(prefix):]])
    if "enum" in fragment:
        return set(fragment["enum"])
    return set().union(*(reference_values(schema, x) for x in fragment.values()))


def expanded_field(schema, fragment, *, future=None, reference=False):
    """Resolve actual links; alter only previously future-bearing ref enums."""
    if isinstance(fragment, list):
        return [expanded_field(schema, x, future=future, reference=reference) for x in fragment]
    if not isinstance(fragment, dict):
        return fragment
    if "$ref" in fragment:
        prefix = "#/$defs/"
        assert fragment["$ref"].startswith(prefix)
        resolved = {**schema["$defs"][fragment["$ref"][len(prefix):]],
                    **{k: v for k, v in fragment.items() if k != "$ref"}}
        return expanded_field(schema, resolved, future=future, reference=reference)
    result = {}
    for key, value in fragment.items():
        if key == "properties":
            result[key] = {
                name: expanded_field(schema, item, future=future,
                    reference=name == "evidence_refs" or name.endswith("_basis"))
                for name, item in value.items()
            }
        elif key == "enum" and reference and future is not None:
            configured = {"P01", "P02", "P03"}
            result[key] = [x for x in value if x not in configured]
            if configured.intersection(value):
                result[key].extend(future)
        else:
            result[key] = expanded_field(schema, value, future=future, reference=reference)
    return result


@pytest.mark.parametrize("subject", SUBJECTS)
def test_each_native_subject_schema_enforces_exact_role_intersections(subject):
    issued = children()
    before = {k: v.parent.model_dump_json() for k, v in issued.items()}
    schema = configured_role_schema_v2(issued)
    choices = schema["properties"]["candidates"]["items"]["anyOf"]
    old = configured_schema_v1(issued)
    old_choices = old["properties"]["candidates"]["items"]["anyOf"]
    assert len(choices) == 4
    choice = next(c for c in choices if c["properties"]["ticker"]["const"] == subject)
    fields = choice["properties"]
    old_fields = next(c for c in old_choices
                      if c["properties"]["ticker"]["const"] == subject)["properties"]
    assert fields.keys() == old_fields.keys()
    expected = {
        "business_reevaluation_up": ("P01", "P02"),
        "business_reevaluation_down": ("P01", "P02"),
        "risk_context": ("P02", "P03"),
    }
    for field, allowed in expected.items():
        assert reference_values(schema, fields[field]) & {"P01", "P02", "P03"} == set(allowed)
    for field in fields:
        reference = field == "evidence_refs" or field.endswith("_basis")
        assert expanded_field(schema, fields[field], reference=reference) == expanded_field(
            old, old_fields[field], future=expected.get(field, ()), reference=reference,
        ), field
    assert {k: v.parent.model_dump_json() for k, v in issued.items()} == before
    assert all(v.production_eligible is False for v in issued.values())


@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("index,field", [
    (0, "risk_context"), (2, "business_reevaluation_up"),
    (2, "business_reevaluation_down"), (1, "buy_drivers"),
])
def test_live_reference_checker_rejects_prohibited_roles_before_any_acceptance(subject, index, field):
    current = children()[subject]
    item = {"text": "Unfulfilled prospective condition", "evidence_refs": [current.configured_rows[index].ref_id]}
    candidate = {"ticker": subject, field: item if field == "risk_context" else [item]}
    before = set(owner._ISSUED)
    with pytest.raises(ValueError, match="future_role_forbidden|prospective_only"):
        owner.validate_composed_reference_use(current, candidate, consumer=owner.SCHEMA_CONSUMER)
    assert set(owner._ISSUED) == before


@pytest.mark.parametrize("subject", SUBJECTS)
def test_old_enum_membership_is_not_live_role_authority(subject):
    issued = children()
    old = configured_schema_v1(issued)
    choice = next(c for c in old["properties"]["candidates"]["items"]["anyOf"]
                  if c["properties"]["ticker"]["const"] == subject)
    assert "P03" in reference_values(old, choice["properties"]["business_reevaluation_down"])
    current = issued[subject]
    with pytest.raises(ValueError, match="future_role_forbidden"):
        owner.validate_composed_reference_use(current, {
            "ticker": subject, "business_reevaluation_down": [{
                "text": "Unfulfilled condition", "evidence_refs": [current.configured_rows[2].ref_id],
            }],
        }, consumer=owner.SCHEMA_CONSUMER)


@pytest.mark.parametrize("mutation", ["missing_subject", "copied_child", "revoked", "wrong_consumer"])
def test_schema_requires_exact_live_issued_children(mutation):
    issued = children()
    current = issued[SUBJECTS[0]]
    if mutation == "missing_subject":
        issued.pop(SUBJECTS[-1])
    elif mutation == "copied_child":
        issued[SUBJECTS[0]] = replace(current)
    elif mutation == "revoked":
        owner.revoke_reviewed_configured_composition(current)
    else:
        issued[SUBJECTS[0]] = owner.build_reviewed_configured_composition(
            current.parent, recipe_id=current.recipe_id, consumer=owner.MODEL_VIEW_CONSUMER)
    with pytest.raises(ValueError):
        configured_role_schema_v2(issued)


def test_schema_success_does_not_create_model_candidate_consumer_authority():
    issued = children()
    schema = configured_role_schema_v2(issued)
    assert len(schema["properties"]["candidates"]["items"]["anyOf"]) == 4
    before = set(owner._ISSUED)
    for current in issued.values():
        with pytest.raises(ValueError, match="consumer_forbidden"):
            owner.verify_reviewed_configured_composition(
                current, consumer="M12AT_MODEL_CANDIDATE_ACCEPTANCE_V1",
            )
        with pytest.raises(ValueError, match="consumer_forbidden"):
            owner.build_reviewed_configured_composition(
                current.parent, recipe_id=current.recipe_id,
                consumer="M12AT_MODEL_CANDIDATE_ACCEPTANCE_V1",
            )
    assert set(owner._ISSUED) == before
