from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Mapping


CONTRACT_VERSION = "us-morning-exact-payload-quality-v1"
MALFORMED_ZERO_CHANGE = re.compile(
    r"(?:변화|변동|차이)\s*없음\s*(?:했|하였)습니다"
)
NO_CHANGE_SEMANTIC = re.compile(
    r"(?:변화|변동|차이)(?:가|는|은)?\s*(?:없|없음)|큰\s+변화\s+없이"
)
GENERIC_MACRO_SUBJECTS = ("거시 지표", "보조 거시 맥락")


@dataclass(frozen=True)
class UsMarketMessageQualityResult:
    contract: str
    payload_sha256: str
    status: str
    errors: tuple[str, ...]
    malformed_zero_change_korean: int
    generic_no_change_macro_section_visible: int
    generic_macro_without_specific_evidence_visible: int
    required_layout_valid: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _section(text: str, heading: str) -> str:
    marker = f"{heading}\n"
    start = text.find(marker)
    if start < 0:
        return ""
    body_start = start + len(marker)
    next_section = text.find("\n\n", body_start)
    return text[body_start:] if next_section < 0 else text[body_start:next_section]


def validate_us_market_message_payload(text: str) -> UsMarketMessageQualityResult:
    errors: list[str] = []
    malformed = int(bool(MALFORMED_ZERO_CHANGE.search(text)))
    if malformed:
        errors.append("malformed_zero_change_korean")

    macro = _section(text, "🌐 보조 시장환경")
    generic_no_change = int(
        bool(macro)
        and bool(NO_CHANGE_SEMANTIC.search(macro))
        and any(subject in macro for subject in GENERIC_MACRO_SUBJECTS)
    )
    if generic_no_change:
        errors.append("generic_no_change_macro_section_visible")

    generic_without_specific = int(
        bool(macro) and any(subject in macro for subject in GENERIC_MACRO_SUBJECTS)
    )
    if generic_without_specific:
        errors.append("generic_macro_without_specific_evidence_visible")

    required = ("📈 주요 지수", "🔎 시장 내부", "📌 다음 확인")
    positions = [text.find(heading) for heading in required]
    layout_valid = all(position >= 0 for position in positions) and positions == sorted(
        positions
    )
    if not layout_valid:
        errors.append("required_layout_invalid")

    unique_errors = tuple(dict.fromkeys(errors))
    return UsMarketMessageQualityResult(
        contract=CONTRACT_VERSION,
        payload_sha256=_sha256_text(text),
        status="PASS" if not unique_errors else "FAIL",
        errors=unique_errors,
        malformed_zero_change_korean=malformed,
        generic_no_change_macro_section_visible=generic_no_change,
        generic_macro_without_specific_evidence_visible=generic_without_specific,
        required_layout_valid=layout_valid,
    )


def quality_result_matches_received_payload(
    quality: UsMarketMessageQualityResult | Mapping[str, object],
    received_payload_sha256: str,
) -> bool:
    payload_sha = (
        quality.payload_sha256
        if isinstance(quality, UsMarketMessageQualityResult)
        else str(quality.get("payload_sha256") or "")
    )
    return bool(received_payload_sha256) and payload_sha == received_payload_sha256
