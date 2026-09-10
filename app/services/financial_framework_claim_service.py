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


class FrameworkReferenceRole(StrEnum):
    ASSERTED_STATE = "ASSERTED_STATE"
    APPLIED_DECISION_FRAMEWORK = "APPLIED_DECISION_FRAMEWORK"
    EXPLICIT_NON_APPLICATION = "EXPLICIT_NON_APPLICATION"
    CONTRASTIVE_REPLACEMENT = "CONTRASTIVE_REPLACEMENT"
    CONTEXT_ONLY_MENTION = "CONTEXT_ONLY_MENTION"
    CONTRADICTORY_MIXED_USE = "CONTRADICTORY_MIXED_USE"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class FrameworkClaim:
    framework: str
    kind: FrameworkClaimKind
    text: str
    field_path: str = ""
    evidence_refs: tuple[str, ...] = ()
    role: FrameworkReferenceRole = FrameworkReferenceRole.UNRESOLVED


_FRAMEWORKS = {
    "net_debt": r"순부채|\b(?:industrial\s+)?net[ -]debt\b",
    "working_capital": r"(?:산업재\s*)?운전자본|\b(?:industrial\s+)?working[ -]capital\b|\bindustrial\s+wc\b",
    "non_operating_interest": r"비영업\s*이자|\bnon[ -]operating\s+interest\b",
}
_TERM = "(?:" + "|".join(_FRAMEWORKS.values()) + ")"
_CLUSTER = re.compile(
    _TERM + r"(?:\s*(?:[·,/]|및|와|과|나|이나|and|or)\s*" + _TERM + r")*",
    re.I,
)
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
    r"(?:an?\s+applicable|the\s+(?:applicable|relevant))\s+framework)|excluded)|"
    r"(?:does|do)\s+not\s+apply)\s*" + _EN_SECTOR + r"\s*$",
    re.I,
)
_EN_PREFIX = re.compile(r"(?:\b(?:do|does)\s+not\s+(?:apply|use|evaluate)|\bexclude)\s*$", re.I)
_EN_OBJECT_END = re.compile(_EN_FRAMEWORK + _EN_SECTOR + r"\s*$", re.I)
_KO_CONTRASTIVE_MARKER = re.compile(
    _NOMINAL_BRIDGE + r"(?P<marker>대신|보다(?:는)?|아니라)\s+"
)
_KO_REPLACEMENT_APPLICATION = re.compile(
    r"(?:(?!하지만|그러나|반면).)+?"
    r"(?:을|를|이|가)?\s*"
    r"(?:본다|봅니다|사용한다|사용합니다|적용한다|적용합니다|적용된다|적용됩니다|"
    r"적용해야\s*(?:한다|합니다)|평가한다|평가합니다|평가해야\s*(?:한다|합니다)|"
    r"적절한\s*(?:평가틀|틀|기준|프레임워크)(?:이다|입니다))\s*$"
)
_SECTOR_VALID_REPLACEMENT = re.compile(
    r"보험\s*인수|인수\s*규율|언더라이팅|규제\s*자본|지급\s*여력|"
    r"자본\s*적정성|건전성|유동성|자산\s*건전성|"
    r"\bunderwriting\b|\bregulatory\s+capital\b|\bsolvency\b|"
    r"\bcapital\s+adequacy\b|\bliquidity\b|\basset\s+quality\b",
    re.I,
)
_EN_INSTEAD_OF_PREFIX = re.compile(
    r"(?:use|evaluate|apply|prefer|consider)\s+.+\s+(?:instead\s+of|rather\s+than)\s*$",
    re.I,
)
_EN_RATHER_THAN_PREFIX = re.compile(r"(?:rather\s+than|not)\s*$", re.I)
_EN_REPLACEMENT_SUFFIX = re.compile(
    r"\s*,?\s*(?:use|evaluate|apply|prefer|consider)\s+.+\s*$",
    re.I,
)
_EN_NOT_BUT_SUFFIX = re.compile(r"\s*but\s+\S.+\s*$", re.I)
_AMBIGUITY = re.compile(r"않|아니|배제|\b(?:not|never|unless|exclude|excluded)\b", re.I)
_UNCERTAIN_APPLICATION = re.compile(
    r"수\s*있(?:다|습니다|음)?|가능성|\b(?:may|might|could)\b",
    re.I,
)
_CONDITIONAL = re.compile(r"경우|라면|한다면|\b(?:if|unless)\b", re.I)
_TEXT_FIELDS = {
    "text",
    "summary",
    "confirmation_business_condition",
    "business_invalidation_condition",
}
_DECISION_PATH_TOKENS = (
    "buy_drivers",
    "sell_drivers",
    "core_investment_judgment",
    "business_reevaluation",
    "material_directional_anchor_basis",
)
_DIRECT_APPLICATION_PATH_TOKENS = (
    "buy_drivers",
    "sell_drivers",
    "material_directional_anchor_basis",
)
_CONTEXT_ONLY_PATH_TOKENS = (
    "historical_context",
    "background_context",
    "context_only",
)
_DECISION_APPLICATION = re.compile(
    r"\b(?:buy|sell|driver|risk|apply|use|framework)\b|"
    r"매수|매도|근거|부담|위험|판단|적용|사용|평가",
    re.I,
)
_METRIC_FRAMEWORK = {
    "net_debt": "net_debt",
    "inventory": "working_capital",
    "inventory_component": "working_capital",
    "trade_accounts_receivable": "working_capital",
    "accounts_receivable_broad": "working_capital",
    "trade_accounts_payable": "working_capital",
    "accounts_payable_broad": "working_capital",
    "current_assets": "working_capital",
    "current_liabilities": "working_capital",
    "contract_assets_context": "working_capital",
    "contract_liabilities_context": "working_capital",
    "working_capital_balance_delta": "working_capital",
}


def _ko_contrastive_replacement(suffix: str) -> bool:
    marker = _KO_CONTRASTIVE_MARKER.match(suffix)
    if marker is None:
        return False
    replacement = suffix[marker.end() :].strip()
    return bool(
        replacement
        and _SECTOR_VALID_REPLACEMENT.search(replacement)
        and _KO_REPLACEMENT_APPLICATION.fullmatch(replacement)
        and _CLUSTER.search(replacement) is None
    )


def _contrastive_replacement_exclusion(*, prefix: str, suffix: str, clause: str) -> bool:
    if _CONDITIONAL.search(clause):
        return False
    if _ko_contrastive_replacement(suffix):
        return True
    if _EN_INSTEAD_OF_PREFIX.fullmatch(prefix):
        return (
            not suffix
            and _CLUSTER.search(prefix) is None
            and _SECTOR_VALID_REPLACEMENT.search(prefix) is not None
        )
    if _EN_RATHER_THAN_PREFIX.fullmatch(prefix):
        replacement = _EN_NOT_BUT_SUFFIX.fullmatch(suffix)
        if prefix.casefold() != "not":
            replacement = _EN_REPLACEMENT_SUFFIX.fullmatch(suffix)
        return (
            replacement is not None
            and _CLUSTER.search(suffix) is None
            and _SECTOR_VALID_REPLACEMENT.search(suffix) is not None
        )
    return False


_APPLICATION_ROLES = frozenset(
    {
        FrameworkReferenceRole.ASSERTED_STATE,
        FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
        FrameworkReferenceRole.CONTRADICTORY_MIXED_USE,
        FrameworkReferenceRole.UNRESOLVED,
    }
)


def framework_reference_is_application(claim: FrameworkClaim) -> bool:
    """Return the shared fail-closed application decision for hard validators."""

    return claim.role in _APPLICATION_ROLES


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
            contrastive_exclusion = _contrastive_replacement_exclusion(
                prefix=prefix,
                suffix=suffix,
                clause=clause,
            )
            excluded = not _CONDITIONAL.search(clause) and (
                contrastive_exclusion
                or (
                    not _AMBIGUITY.search(preceding)
                    and (
                        _KO_EXCLUSION.fullmatch(suffix)
                        or _EN_SUFFIX.fullmatch(suffix)
                        or (_EN_PREFIX.search(prefix) and _EN_OBJECT_END.fullmatch(suffix))
                    )
                )
            )
            kind = (
                FrameworkClaimKind.EXPLICIT_EXCLUSION
                if excluded
                else FrameworkClaimKind.UNCERTAIN_OR_AMBIGUOUS
                if _AMBIGUITY.search(clause) or _UNCERTAIN_APPLICATION.search(clause)
                else FrameworkClaimKind.ASSERTION_OR_APPLICATION
            )
            role = (
                FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
                if contrastive_exclusion
                else FrameworkReferenceRole.EXPLICIT_NON_APPLICATION
                if excluded
                else FrameworkReferenceRole.UNRESOLVED
                if kind == FrameworkClaimKind.UNCERTAIN_OR_AMBIGUOUS
                else FrameworkReferenceRole.ASSERTED_STATE
            )
            for framework, pattern in _FRAMEWORKS.items():
                if re.search(pattern, cluster.group(), re.I):
                    claims.append(
                        FrameworkClaim(
                            framework=framework,
                            kind=kind,
                            text=clause.strip(),
                            role=role,
                        )
                    )
    return tuple(claims)


def candidate_financial_framework_claims(
    candidate: object,
    *,
    metric_by_ref: Mapping[str, str] | None = None,
) -> tuple[FrameworkClaim, ...]:
    payload = candidate.model_dump(mode="json") if hasattr(candidate, "model_dump") else candidate
    claims: list[FrameworkClaim] = []
    metric_by_ref = metric_by_ref or {}

    def scoped_role(
        claim: FrameworkClaim,
        path: str,
        refs: tuple[str, ...],
    ) -> FrameworkReferenceRole:
        if claim.role not in {
            FrameworkReferenceRole.ASSERTED_STATE,
            FrameworkReferenceRole.UNRESOLVED,
        }:
            return claim.role
        folded_path = path.casefold()
        if any(token in folded_path for token in _CONTEXT_ONLY_PATH_TOKENS) and not refs:
            return FrameworkReferenceRole.CONTEXT_ONLY_MENTION
        if claim.role == FrameworkReferenceRole.ASSERTED_STATE and any(
            token in folded_path for token in _DECISION_PATH_TOKENS
        ) and (
            any(token in folded_path for token in _DIRECT_APPLICATION_PATH_TOKENS)
            or _DECISION_APPLICATION.search(claim.text)
            or refs
        ):
            return FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK
        return claim.role

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
                        FrameworkClaim(
                            c.framework,
                            c.kind,
                            c.text,
                            child_path,
                            refs,
                            scoped_role(c, child_path, refs),
                        )
                        for c in financial_framework_claims(value)
                    )
                collect(value, child_path)
            if any(token in path.casefold() for token in _DECISION_PATH_TOKENS):
                raw_refs = item.get("evidence_refs", ())
                refs = (
                    tuple(str(ref) for ref in raw_refs)
                    if isinstance(raw_refs, (list, tuple))
                    else ()
                )
                existing = {(claim.framework, claim.field_path) for claim in claims}
                field_path = f"{path}.evidence_refs" if path else "evidence_refs"
                for ref in refs:
                    framework = _METRIC_FRAMEWORK.get(metric_by_ref.get(ref, ""))
                    if framework and (framework, field_path) not in existing:
                        claims.append(
                            FrameworkClaim(
                                framework=framework,
                                kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
                                text="",
                                field_path=field_path,
                                evidence_refs=(ref,),
                                role=FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
                            )
                        )
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if any(token in path.casefold() for token in _DECISION_PATH_TOKENS):
                for ref in (str(value) for value in item if isinstance(value, str)):
                    framework = _METRIC_FRAMEWORK.get(metric_by_ref.get(ref, ""))
                    if framework:
                        claims.append(
                            FrameworkClaim(
                                framework=framework,
                                kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
                                text="",
                                field_path=path,
                                evidence_refs=(ref,),
                                role=FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
                            )
                        )
            for index, value in enumerate(item):
                collect(value, f"{path}[{index}]")

    collect(payload, "")
    by_framework: dict[str, set[FrameworkReferenceRole]] = {}
    for claim in claims:
        by_framework.setdefault(claim.framework, set()).add(claim.role)
    exclusion_roles = {
        FrameworkReferenceRole.EXPLICIT_NON_APPLICATION,
        FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT,
    }
    application_roles = {
        FrameworkReferenceRole.ASSERTED_STATE,
        FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
    }
    contradictory = {
        framework
        for framework, roles in by_framework.items()
        if roles & exclusion_roles and roles & application_roles
    }
    return tuple(
        FrameworkClaim(
            claim.framework,
            claim.kind,
            claim.text,
            claim.field_path,
            claim.evidence_refs,
            FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
            if claim.framework in contradictory
            else claim.role,
        )
        for claim in claims
    )
