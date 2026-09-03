from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

import pytest

from app.services.structured_autonomy_alias_service import (
    alias_price_choices,
    build_alias_constrained_batch_schema,
    build_evidence_alias_catalog,
    compact_alias_ai_context,
    resolve_candidate_aliases,
)
from app.services.structured_autonomy_shadow_service import StructuredAutonomyCandidate
from tests.test_structured_autonomy_shadow_service import _candidate, _packet


def _alias_candidate() -> tuple[dict[str, object], object]:
    packet = _packet()
    catalog = build_evidence_alias_catalog(packet)
    by_ref = {entry.canonical_ref: entry.alias for entry in catalog.entries}

    def replace(value: object, key: str | None = None) -> object:
        if isinstance(value, Mapping):
            return {str(child_key): replace(child, str(child_key)) for child_key, child in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if key == "evidence_refs" or (key and key.endswith("_basis")):
                return [by_ref[str(child)] for child in value]
            return [replace(child, key) for child in value]
        return value

    raw = replace(_candidate().model_dump(mode="json"))
    assert isinstance(raw, dict)
    return raw, catalog


def test_alias_map_is_deterministic_under_provider_reordering() -> None:
    packet = _packet()
    reversed_packet = packet.model_copy(update={"evidence": tuple(reversed(packet.evidence))})

    first = build_evidence_alias_catalog(packet)
    second = build_evidence_alias_catalog(reversed_packet)

    assert first.entries == second.entries
    assert first.alias_map_sha256 == second.alias_map_sha256
    assert len(first.by_alias) == len(first.entries)
    assert len(first.by_ref) == len(first.entries)


def test_alias_context_and_price_choices_do_not_expose_canonical_refs() -> None:
    packet = _packet()
    catalog = build_evidence_alias_catalog(packet)
    context = compact_alias_ai_context(packet, catalog)
    choices = alias_price_choices(
        {
            "allowed_confirmation_levels": [
                {"level": 112.0, "basis_ref": "ref:price"}
            ]
        },
        catalog,
    )
    serialized = json.dumps({"context": context, "choices": choices}, sort_keys=True)

    assert "ref:price" not in serialized
    assert choices["allowed_confirmation_levels"][0]["basis_alias"].startswith("E")


def test_dynamic_schema_constrains_every_reference_array_to_subject_aliases() -> None:
    catalog = build_evidence_alias_catalog(_packet())
    aliases = [entry.alias for entry in catalog.entries]
    schema = build_alias_constrained_batch_schema(
        candidate_schema=StructuredAutonomyCandidate.model_json_schema(),
        contract="contract",
        packet_id="packet",
        aliases_by_ticker={"TEST": aliases},
    )

    alias_definition = schema["$defs"]["T1_EvidenceAlias"]
    assert alias_definition["enum"] == aliases
    assert schema["properties"]["candidates"]["items"]["anyOf"][0]["properties"][
        "ticker"
    ]["const"] == "TEST"

    reference_items: list[object] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            properties = value.get("properties")
            if isinstance(properties, dict):
                for name, child in properties.items():
                    if name == "evidence_refs" or name.endswith("_basis"):
                        reference_items.append(child["items"])
                    collect(child)
            for key, child in value.items():
                if key != "properties":
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(schema)
    assert reference_items
    assert all(item == {"$ref": "#/$defs/T1_EvidenceAlias"} for item in reference_items)


def test_alias_resolution_restores_canonical_refs_and_records_lineage() -> None:
    raw, catalog = _alias_candidate()

    resolved, selections = resolve_candidate_aliases(
        raw,
        packet=_packet(),
        catalog=catalog,
    )

    assert StructuredAutonomyCandidate.model_validate(resolved) == _candidate()
    assert selections
    assert all(row["selected_alias"].startswith("E") for row in selections)
    assert all(row["canonical_ref"].startswith("ref:") for row in selections)


def test_alias_resolution_rejects_nonexistent_and_wrong_owner_aliases() -> None:
    raw, catalog = _alias_candidate()
    raw["core_judgment"]["evidence_refs"] = ["E999"]
    with pytest.raises(ValueError, match="nonexistent_evidence_alias"):
        resolve_candidate_aliases(raw, packet=_packet(), catalog=catalog)

    with pytest.raises(ValueError, match="cross_subject_evidence_alias"):
        resolve_candidate_aliases(
            _alias_candidate()[0],
            packet=_packet(),
            catalog=catalog.model_copy(update={"ticker": "OTHER"}),
        )
    with pytest.raises(ValueError, match="cross_market_evidence_alias"):
        resolve_candidate_aliases(
            _alias_candidate()[0],
            packet=_packet(),
            catalog=catalog.model_copy(update={"market": "kr"}),
        )
    with pytest.raises(ValueError, match="cross_generation_evidence_alias"):
        resolve_candidate_aliases(
            _alias_candidate()[0],
            packet=_packet(),
            catalog=catalog.model_copy(update={"generation": "other-packet"}),
        )


def test_alias_resolution_rejects_canonical_content_drift() -> None:
    raw, catalog = _alias_candidate()
    packet = _packet()
    first = packet.evidence[0].model_copy(update={"statement": "mutated evidence"})
    drifted = packet.model_copy(update={"evidence": (first, *packet.evidence[1:])})

    with pytest.raises(ValueError, match="canonical_evidence_content_fingerprint_mismatch"):
        resolve_candidate_aliases(raw, packet=drifted, catalog=catalog)
