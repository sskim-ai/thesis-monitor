from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    FrozenModel,
)


CONTRACT_VERSION = "structured-autonomy-evidence-alias-v1"
_REFERENCE_FIELDS = {"evidence_refs", "directional_negative_basis"}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evidence_content_sha256(ref: DecisionEvidenceRef) -> str:
    return _canonical_sha256(ref.model_dump(mode="json"))


class EvidenceAliasEntry(FrozenModel):
    alias: str
    canonical_ref: str
    content_sha256: str
    ticker: str
    market: str
    generation: str
    category: str
    label: str
    statement: str
    as_of: str | None


class EvidenceAliasCatalog(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    market: str
    generation: str
    evidence_fingerprint: str
    entries: tuple[EvidenceAliasEntry, ...] = Field(min_length=1)
    alias_map_sha256: str

    @property
    def by_alias(self) -> dict[str, EvidenceAliasEntry]:
        return {entry.alias: entry for entry in self.entries}

    @property
    def by_ref(self) -> dict[str, EvidenceAliasEntry]:
        return {entry.canonical_ref: entry for entry in self.entries}


def build_evidence_alias_catalog(
    packet: DecisionEvidencePacket,
    *,
    excluded_ref_prefixes: Sequence[str] = (),
) -> EvidenceAliasCatalog:
    rows = [
        ref
        for ref in packet.evidence
        if not any(ref.ref_id.startswith(prefix) for prefix in excluded_ref_prefixes)
    ]
    if not rows:
        raise ValueError(f"empty_evidence_alias_catalog:{packet.ticker}")
    if len({ref.ref_id for ref in rows}) != len(rows):
        raise ValueError(f"duplicate_canonical_evidence_ref:{packet.ticker}")

    ordered = sorted(
        ((evidence_content_sha256(ref), ref.ref_id, ref) for ref in rows),
        key=lambda row: (row[0], row[1]),
    )
    width = max(2, len(str(len(ordered))))
    entries = tuple(
        EvidenceAliasEntry(
            alias=f"E{index:0{width}d}",
            canonical_ref=ref.ref_id,
            content_sha256=content_sha,
            ticker=packet.ticker,
            market=packet.market,
            generation=packet.packet_id,
            category=ref.category.value,
            label=ref.label,
            statement=ref.statement,
            as_of=ref.as_of,
        )
        for index, (content_sha, _ref_id, ref) in enumerate(ordered, start=1)
    )
    identity = [
        {
            "alias": entry.alias,
            "canonical_ref": entry.canonical_ref,
            "content_sha256": entry.content_sha256,
            "ticker": entry.ticker,
            "market": entry.market,
            "generation": entry.generation,
        }
        for entry in entries
    ]
    return EvidenceAliasCatalog(
        ticker=packet.ticker,
        market=packet.market,
        generation=packet.packet_id,
        evidence_fingerprint=packet.evidence_sha256,
        entries=entries,
        alias_map_sha256=_canonical_sha256(identity),
    )


def compact_alias_ai_context(
    packet: DecisionEvidencePacket,
    catalog: EvidenceAliasCatalog,
) -> dict[str, object]:
    _validate_catalog_owner(packet, catalog)
    by_ref = {ref.ref_id: ref for ref in packet.evidence}
    return {
        "contract": packet.contract,
        "packet_id": packet.packet_id,
        "ticker": packet.ticker,
        "company_name": packet.company_name,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "horizon": packet.horizon,
        "reasoning_grade": packet.reasoning_grade,
        "backend_reasoning_effort": packet.backend_reasoning_effort,
        "evidence": [
            {
                "alias": entry.alias,
                "category": entry.category,
                "label": entry.label,
                "statement": entry.statement,
                "as_of": entry.as_of,
                "value": (
                    str(by_ref[entry.canonical_ref].value)
                    if by_ref[entry.canonical_ref].value is not None
                    else None
                ),
                "unit": by_ref[entry.canonical_ref].unit,
                "numeric_prose_eligible": by_ref[
                    entry.canonical_ref
                ].numeric_prose_eligible,
            }
            for entry in catalog.entries
        ],
        "prohibited_claims": packet.prohibited_claims,
        "technical_context_id": packet.technical_context_id,
        "technical_context_status": packet.technical_context_status,
        "technical_context_quality": packet.technical_context_quality,
        "data_quality_cautions": packet.data_quality_cautions,
    }


def alias_price_choices(
    value: Mapping[str, object],
    catalog: EvidenceAliasCatalog,
) -> dict[str, object]:
    by_ref = catalog.by_ref

    def transform(item: object) -> object:
        if isinstance(item, Mapping):
            result: dict[str, object] = {}
            for key, child in item.items():
                if key == "basis_ref":
                    canonical_ref = str(child)
                    if canonical_ref not in by_ref:
                        raise ValueError(
                            f"price_basis_missing_from_alias_catalog:{catalog.ticker}:{canonical_ref}"
                        )
                    result["basis_alias"] = by_ref[canonical_ref].alias
                else:
                    result[str(key)] = transform(child)
            return result
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            return [transform(child) for child in item]
        return item

    transformed = transform(value)
    if not isinstance(transformed, dict):
        raise TypeError("price_choices_object_required")
    return transformed


def _is_reference_field(name: str) -> bool:
    return name in _REFERENCE_FIELDS or name.endswith("_basis")


def _namespace_schema_refs(value: object, prefix: str) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str) and child.startswith("#/$defs/"):
                result[key] = "#/$defs/" + prefix + child.removeprefix("#/$defs/")
            else:
                result[key] = _namespace_schema_refs(child, prefix)
        return result
    if isinstance(value, list):
        return [_namespace_schema_refs(child, prefix) for child in value]
    return value


def _constrain_reference_fields(value: object, alias_definition: str) -> None:
    if not isinstance(value, dict):
        if isinstance(value, list):
            for child in value:
                _constrain_reference_fields(child, alias_definition)
        return
    properties = value.get("properties")
    if isinstance(properties, dict):
        for name, child in properties.items():
            if _is_reference_field(str(name)) and isinstance(child, dict):
                child["items"] = {"$ref": f"#/$defs/{alias_definition}"}
            else:
                _constrain_reference_fields(child, alias_definition)
    for key, child in value.items():
        if key != "properties":
            _constrain_reference_fields(child, alias_definition)


def build_alias_constrained_batch_schema(
    *,
    candidate_schema: Mapping[str, object],
    contract: str,
    packet_id: str,
    aliases_by_ticker: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    if not aliases_by_ticker:
        raise ValueError("aliases_by_ticker_required")
    root_defs: dict[str, object] = {}
    candidates: list[dict[str, object]] = []
    for index, (ticker, aliases) in enumerate(aliases_by_ticker.items(), start=1):
        if not aliases or len(set(aliases)) != len(aliases):
            raise ValueError(f"invalid_alias_choices:{ticker}")
        prefix = f"T{index}_"
        alias_definition = f"{prefix}EvidenceAlias"
        scoped = copy.deepcopy(dict(candidate_schema))
        source_defs = scoped.pop("$defs", {})
        scoped = _namespace_schema_refs(scoped, prefix)
        source_defs = _namespace_schema_refs(source_defs, prefix)
        _constrain_reference_fields(scoped, alias_definition)
        _constrain_reference_fields(source_defs, alias_definition)
        properties = scoped.get("properties")
        if not isinstance(properties, dict) or not isinstance(properties.get("ticker"), dict):
            raise ValueError("candidate_ticker_schema_missing")
        properties["ticker"] = {
            "const": ticker,
            "title": "Ticker",
            "type": "string",
        }
        for name, definition in source_defs.items():
            root_defs[prefix + str(name)] = definition
        root_defs[alias_definition] = {
            "enum": list(aliases),
            "type": "string",
        }
        candidates.append(scoped)

    return {
        "$defs": root_defs,
        "additionalProperties": False,
        "properties": {
            "contract": {"const": contract, "type": "string"},
            "packet_id": {"const": packet_id, "type": "string"},
            "candidates": {
                "items": {"anyOf": candidates},
                "minItems": len(candidates),
                "maxItems": len(candidates),
                "type": "array",
            },
        },
        "required": ["contract", "packet_id", "candidates"],
        "title": "AliasConstrainedStructuredAutonomyBatch",
        "type": "object",
    }


def _validate_catalog_owner(
    packet: DecisionEvidencePacket,
    catalog: EvidenceAliasCatalog,
) -> None:
    if catalog.ticker != packet.ticker:
        raise ValueError("cross_subject_evidence_alias")
    if catalog.market != packet.market:
        raise ValueError("cross_market_evidence_alias")
    if catalog.generation != packet.packet_id:
        raise ValueError("cross_generation_evidence_alias")


def resolve_candidate_aliases(
    raw_candidate: Mapping[str, Any],
    *,
    packet: DecisionEvidencePacket,
    catalog: EvidenceAliasCatalog,
) -> tuple[dict[str, Any], tuple[dict[str, str], ...]]:
    _validate_catalog_owner(packet, catalog)
    if str(raw_candidate.get("ticker") or "") != packet.ticker:
        raise ValueError("cross_subject_candidate_alias_resolution")
    current_refs = {ref.ref_id: ref for ref in packet.evidence}
    by_alias = catalog.by_alias
    selections: list[dict[str, str]] = []

    def resolve(value: object, *, key: str | None = None, path: str = "") -> object:
        if isinstance(value, Mapping):
            return {
                str(child_key): resolve(
                    child,
                    key=str(child_key),
                    path=f"{path}.{child_key}" if path else str(child_key),
                )
                for child_key, child in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if key is not None and _is_reference_field(key):
                resolved: list[str] = []
                for index, child in enumerate(value):
                    alias = str(child)
                    entry = by_alias.get(alias)
                    if entry is None:
                        raise ValueError(
                            f"nonexistent_evidence_alias:{packet.ticker}:{alias}"
                        )
                    if entry.ticker != packet.ticker:
                        raise ValueError("cross_subject_evidence_alias")
                    if entry.market != packet.market:
                        raise ValueError("cross_market_evidence_alias")
                    if entry.generation != packet.packet_id:
                        raise ValueError("cross_generation_evidence_alias")
                    current = current_refs.get(entry.canonical_ref)
                    if current is None:
                        raise ValueError("canonical_evidence_ref_missing")
                    if evidence_content_sha256(current) != entry.content_sha256:
                        raise ValueError("canonical_evidence_content_fingerprint_mismatch")
                    resolved.append(entry.canonical_ref)
                    selections.append(
                        {
                            "path": f"{path}[{index}]",
                            "selected_alias": alias,
                            "canonical_ref": entry.canonical_ref,
                            "content_sha256": entry.content_sha256,
                        }
                    )
                return resolved
            return [
                resolve(child, key=key, path=f"{path}[{index}]")
                for index, child in enumerate(value)
            ]
        return value

    result = resolve(raw_candidate)
    if not isinstance(result, dict):
        raise TypeError("resolved_candidate_object_required")
    return result, tuple(selections)
