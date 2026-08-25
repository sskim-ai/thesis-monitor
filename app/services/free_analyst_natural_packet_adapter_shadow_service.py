from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass

from app.services.ai_analyst_vnext_shadow_service import (
    _content_lines,
    parse_rendered_message,
)


CONTRACT_VERSION = "free-analyst-natural-packet-adapter-shadow-v1"

_HEADING_MAP = {
    "🎯 핵심": "🎯 핵심 판단",
    "📅 오늘/근접 일정": "📌 다음 확인",
}
_HEADING_PREFIXES = (
    "🎯 ",
    "🔎 ",
    "📈 ",
    "💰 ",
    "📊 ",
    "📐 ",
    "⚠️ ",
    "📌 ",
    "👁 ",
    "🧭 ",
    "💡 ",
    "🔄 ",
    "🌙 ",
    "📅 ",
)


@dataclass(frozen=True)
class AdapterEvidenceRef:
    production_ref: str
    common_ref: str
    section_key: str
    text_sha256: str


@dataclass(frozen=True)
class SectionNormalization:
    line_number: int
    original_heading: str
    normalized_heading: str


@dataclass(frozen=True)
class NaturalPacketAdapterResult:
    contract: str
    benchmark_id: str
    status: str
    original_sha256: str
    normalized_sha256: str
    original_text: str
    normalized_text: str
    section_normalizations: tuple[SectionNormalization, ...]
    evidence_ref_map: tuple[AdapterEvidenceRef, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_fingerprint(value: str) -> str:
    content = "\n".join(
        line
        for line in value.splitlines()
        if not line.strip().startswith(_HEADING_PREFIXES)
    )
    return _sha256_text(content)


def _evidence_ref_map(
    normalized_text: str,
    *,
    original_sha256: str,
) -> tuple[AdapterEvidenceRef, ...]:
    parsed = parse_rendered_message(normalized_text)
    refs: list[AdapterEvidenceRef] = []
    metadata_count = 0
    for line in _content_lines(parsed.preamble):
        metadata_count += 1
        refs.append(
            AdapterEvidenceRef(
                production_ref=(
                    f"natural-message:{original_sha256}:metadata:{metadata_count:02d}"
                ),
                common_ref=f"evidence:metadata:{metadata_count:02d}",
                section_key="metadata",
                text_sha256=_sha256_text(line),
            )
        )
    section_counts: Counter[str] = Counter()
    for section in parsed.sections:
        section_counts[section.key] += 1
        ordinal = section_counts[section.key]
        refs.append(
            AdapterEvidenceRef(
                production_ref=(
                    f"natural-message:{original_sha256}:{section.key}:{ordinal:02d}"
                ),
                common_ref=f"evidence:{section.key}:{ordinal:02d}",
                section_key=section.key,
                text_sha256=_sha256_text(section.body),
            )
        )
    return tuple(refs)


def normalize_us_natural_packet(
    natural_message: str,
    *,
    benchmark_id: str,
) -> NaturalPacketAdapterResult:
    """Normalize production headings without changing natural-message content."""
    original = natural_message.strip()
    lines = original.splitlines()
    normalized_lines: list[str] = []
    changes: list[SectionNormalization] = []
    for line_number, line in enumerate(lines, start=1):
        replacement = _HEADING_MAP.get(line.strip())
        if replacement is None:
            normalized_lines.append(line)
            continue
        normalized_lines.append(replacement)
        changes.append(
            SectionNormalization(
                line_number=line_number,
                original_heading=line.strip(),
                normalized_heading=replacement,
            )
        )
    normalized = "\n".join(normalized_lines)
    errors: list[str] = []
    if _content_fingerprint(original) != _content_fingerprint(normalized):
        errors.append("natural_packet_content_mutated")
    parsed = parse_rendered_message(normalized)
    section_keys = {section.key for section in parsed.sections}
    if "core" not in section_keys:
        errors.append("natural_packet_core_section_unresolved")
    original_sha256 = _sha256_text(original)
    evidence_refs = _evidence_ref_map(
        normalized,
        original_sha256=original_sha256,
    )
    common_refs = [item.common_ref for item in evidence_refs]
    production_refs = [item.production_ref for item in evidence_refs]
    if len(common_refs) != len(set(common_refs)):
        errors.append("common_evidence_ref_collision")
    if len(production_refs) != len(set(production_refs)):
        errors.append("production_evidence_ref_collision")
    if not evidence_refs:
        errors.append("natural_packet_evidence_empty")
    return NaturalPacketAdapterResult(
        contract=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        status="PASS" if not errors else "FAIL",
        original_sha256=original_sha256,
        normalized_sha256=_sha256_text(normalized),
        original_text=original,
        normalized_text=normalized,
        section_normalizations=tuple(changes),
        evidence_ref_map=evidence_refs,
        errors=tuple(errors),
    )


def validate_natural_packet_adapter_result(
    result: NaturalPacketAdapterResult,
) -> tuple[str, ...]:
    errors = list(result.errors)
    if result.original_sha256 != _sha256_text(result.original_text):
        errors.append("original_sha_mismatch")
    if result.normalized_sha256 != _sha256_text(result.normalized_text):
        errors.append("normalized_sha_mismatch")
    if _content_fingerprint(result.original_text) != _content_fingerprint(
        result.normalized_text
    ):
        errors.append("natural_packet_content_mutated")
    expected = _evidence_ref_map(
        result.normalized_text,
        original_sha256=result.original_sha256,
    )
    if result.evidence_ref_map != expected:
        errors.append("evidence_ref_map_incomplete_or_mismatched")
    if len({item.common_ref for item in result.evidence_ref_map}) != len(
        result.evidence_ref_map
    ):
        errors.append("common_evidence_ref_collision")
    if len({item.production_ref for item in result.evidence_ref_map}) != len(
        result.evidence_ref_map
    ):
        errors.append("production_evidence_ref_collision")
    return tuple(dict.fromkeys(errors))
