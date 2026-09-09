"""Bounded assertion/exclusion scope for industrial financial framework claims."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum


class FrameworkClaimKind(StrEnum):
    ASSERTION_OR_APPLICATION = "ASSERTION_OR_APPLICATION"
    EXPLICIT_EXCLUSION = "EXPLICIT_EXCLUSION"
    UNCERTAIN_OR_AMBIGUOUS = "UNCERTAIN_OR_AMBIGUOUS"


@dataclass(frozen=True)
class FrameworkClaim:
    framework: str
    kind: FrameworkClaimKind
    text: str
    field_path: str = ""
    evidence_refs: tuple[str, ...] = ()


_FRAMEWORKS = {
    "net_debt": r"순부채|\b(?:industrial\s+)?net[ -]debt\b",
    "working_capital": r"(?:산업재\s*)?운전자본|\b(?:industrial\s+)?working[ -]capital\b|\bindustrial\s+wc\b",
    "non_operating_interest": r"비영업\s*이자|\bnon[ -]operating\s+interest\b",
}
_TERM = "(?:" + "|".join(_FRAMEWORKS.values()) + ")"
_CLUSTER = re.compile(_TERM + r"(?:\s*(?:[·,/]|및|와|과|and)\s*" + _TERM + r")*", re.I)
_NOMINAL_BRIDGE = (
    r"(?:(?:의|은|는|이|가|을|를|으로|로|도|만)\s*|"
    r"(?:등|일반|영업기업|기업|산업재|해당|이|금융업종|금융업|업종|핵심|"
    r"평가틀|틀|기준|프레임워크|분석|평가|모형|체계)\s*)*"
)
_KO_EXCLUSION = re.compile(
    _NOMINAL_BRIDGE + r"(?:(?:적용|사용|평가|활용|해당)\s*하지\s*않(?:는다|습니다|음)|"
    r"(?:(?:적용|평가|사용)\s*)?대상(?:이|은)\s*아니(?:다|며)|"
    r"배제(?:한다|합니다)|아니(?:다|며|라고\s*명시한다))\s*$"
)
_EN_FRAMEWORK = r"(?:(?:frameworks?|approach|criteria|analysis|metrics?)\s*)?"
_EN_SECTOR = r"(?:(?:to|for|in)\s+(?:the\s+)?(?:banks?|insurers?|insurance|financial\s+sector|this\s+sector))?"
_EN_SUFFIX = re.compile(
    _EN_FRAMEWORK + r"(?:(?:is|are)\s+(?:not\s+(?:applicable|applied|used|"
    r"(?:an?\s+applicable|the\s+relevant)\s+framework)|excluded)|"
    r"(?:does|do)\s+not\s+apply)\s*" + _EN_SECTOR + r"\s*$",
    re.I,
)
_EN_PREFIX = re.compile(r"(?:\b(?:do|does)\s+not\s+(?:apply|use|evaluate)|\bexclude)\s*$", re.I)
_EN_OBJECT_END = re.compile(_EN_FRAMEWORK + _EN_SECTOR + r"\s*$", re.I)
_AMBIGUITY = re.compile(r"않|아니|배제|\b(?:not|never|unless|exclude|excluded)\b", re.I)
_CONDITIONAL = re.compile(r"경우|라면|한다면|\b(?:if|unless)\b", re.I)
_TEXT_FIELDS = {
    "text",
    "summary",
    "confirmation_business_condition",
    "business_invalidation_condition",
}


def financial_framework_claims(text: str) -> tuple[FrameworkClaim, ...]:
    normalized = unicodedata.normalize("NFKC", text)
    claims = []
    # Only a directly governed nominal framework phrase can receive an exemption.
    # Remaining occurrences, clauses and fields are independently fail-closed.
    for clause in re.split(r"[.!?;。\n]+", normalized):
        for cluster in _CLUSTER.finditer(clause):
            prefix = clause[: cluster.start()].strip()
            suffix = clause[cluster.end() :].strip()
            exclusion_prefix = _EN_PREFIX.search(prefix)
            preceding = prefix[: exclusion_prefix.start()] if exclusion_prefix else prefix
            excluded = (
                not _CONDITIONAL.search(clause)
                and not _AMBIGUITY.search(preceding)
                and (
                    _KO_EXCLUSION.fullmatch(suffix)
                    or _EN_SUFFIX.fullmatch(suffix)
                    or (_EN_PREFIX.search(prefix) and _EN_OBJECT_END.fullmatch(suffix))
                )
            )
            kind = (
                FrameworkClaimKind.EXPLICIT_EXCLUSION
                if excluded
                else FrameworkClaimKind.UNCERTAIN_OR_AMBIGUOUS
                if _AMBIGUITY.search(clause)
                else FrameworkClaimKind.ASSERTION_OR_APPLICATION
            )
            for framework, pattern in _FRAMEWORKS.items():
                if re.search(pattern, cluster.group(), re.I):
                    claims.append(
                        FrameworkClaim(framework=framework, kind=kind, text=clause.strip())
                    )
    return tuple(claims)


def candidate_financial_framework_claims(candidate: object) -> tuple[FrameworkClaim, ...]:
    payload = candidate.model_dump(mode="json") if hasattr(candidate, "model_dump") else candidate
    claims: list[FrameworkClaim] = []

    def collect(item: object, path: str) -> None:
        if isinstance(item, Mapping):
            for key, value in item.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in _TEXT_FIELDS and isinstance(value, str):
                    ref_key = f"{key}_refs" if key.endswith("condition") else "evidence_refs"
                    raw_refs = item.get(ref_key, ())
                    refs = (
                        tuple(str(ref) for ref in raw_refs)
                        if isinstance(raw_refs, (list, tuple))
                        else ()
                    )
                    claims.extend(
                        FrameworkClaim(c.framework, c.kind, c.text, child_path, refs)
                        for c in financial_framework_claims(value)
                    )
                collect(value, child_path)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for index, value in enumerate(item):
                collect(value, f"{path}[{index}]")

    collect(payload, "")
    return tuple(claims)
