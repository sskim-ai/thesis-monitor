from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Iterable
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


@dataclass(frozen=True)
class XbrlContext:
    context_id: str
    entity_identifier: str | None
    period_type: str
    period_start: date | None
    period_end: date | None
    dimensions: tuple[tuple[str, str], ...]
    statement_basis: str | None


@dataclass(frozen=True)
class XbrlFact:
    taxonomy_element: str
    context_ref: str
    unit_ref: str | None
    value: str
    context: XbrlContext


def _local_name(value: str) -> str:
    return value.rsplit("}", maxsplit=1)[-1]


def _date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError:
        return None


def _basis_from_dimensions(dimensions: Iterable[tuple[str, str]]) -> str | None:
    values = " ".join(f"{axis} {member}" for axis, member in dimensions).lower()
    consolidated = any(term in values for term in ("consolidated", "consolidation", "연결"))
    separate = any(term in values for term in ("separate", "individual", "별도", "개별"))
    if consolidated == separate:
        return None
    return "consolidated" if consolidated else "separate"


def parse_xbrl_document(xml: bytes) -> tuple[list[XbrlContext], list[XbrlFact]]:
    """Parse XBRL with a real XML parser; unsupported or ambiguous context stays unknown."""
    root = ElementTree.fromstring(xml)
    contexts: dict[str, XbrlContext] = {}
    for element in root.iter():
        if _local_name(element.tag) != "context":
            continue
        context_id = str(element.attrib.get("id") or "")
        if not context_id:
            continue
        identifier = next(
            (
                child.text.strip()
                for child in element.iter()
                if _local_name(child.tag) == "identifier" and child.text
            ),
            None,
        )
        dimensions = tuple(
            sorted(
                (
                    str(child.attrib.get("dimension") or ""),
                    str(child.text or "").strip(),
                )
                for child in element.iter()
                if _local_name(child.tag) in {"explicitMember", "typedMember"}
            )
        )
        instant = next(
            (
                _date(child.text)
                for child in element.iter()
                if _local_name(child.tag) == "instant"
            ),
            None,
        )
        start = next(
            (
                _date(child.text)
                for child in element.iter()
                if _local_name(child.tag) == "startDate"
            ),
            None,
        )
        end = next(
            (
                _date(child.text)
                for child in element.iter()
                if _local_name(child.tag) == "endDate"
            ),
            None,
        )
        contexts[context_id] = XbrlContext(
            context_id=context_id,
            entity_identifier=identifier,
            period_type="instant" if instant else "duration" if start and end else "unknown",
            period_start=instant or start,
            period_end=instant or end,
            dimensions=dimensions,
            statement_basis=_basis_from_dimensions(dimensions),
        )

    facts: list[XbrlFact] = []
    for element in root.iter():
        context_ref = element.attrib.get("contextRef")
        if not context_ref or context_ref not in contexts:
            continue
        value = str(element.text or "").strip()
        if not value:
            continue
        facts.append(
            XbrlFact(
                taxonomy_element=element.tag,
                context_ref=context_ref,
                unit_ref=element.attrib.get("unitRef"),
                value=value,
                context=contexts[context_ref],
            )
        )
    return list(contexts.values()), facts


def parse_xbrl_archive(payload: bytes) -> tuple[list[XbrlContext], list[XbrlFact]]:
    contexts: list[XbrlContext] = []
    facts: list[XbrlFact] = []
    try:
        with ZipFile(BytesIO(payload)) as archive:
            names = sorted(
                name
                for name in archive.namelist()
                if name.lower().endswith((".xbrl", ".xml"))
            )
            for name in names:
                try:
                    document_contexts, document_facts = parse_xbrl_document(
                        archive.read(name)
                    )
                except ElementTree.ParseError:
                    continue
                contexts.extend(document_contexts)
                facts.extend(document_facts)
    except BadZipFile as error:
        raise ValueError("OpenDART XBRL response is not a valid archive") from error
    if not facts:
        raise ValueError("OpenDART XBRL archive has no parseable facts")
    return contexts, facts


def reconcile_xbrl_fact(
    facts: Iterable[XbrlFact],
    *,
    taxonomy_element: str,
    period_start: date,
    period_end: date,
    unit_ref: str,
    statement_basis: str,
) -> XbrlFact | None:
    """Return only a unique exact XBRL occurrence; never use first-match fallback."""
    matches = [
        fact
        for fact in facts
        if _local_name(fact.taxonomy_element) == _local_name(taxonomy_element)
        and fact.context.period_start == period_start
        and fact.context.period_end == period_end
        and fact.unit_ref == unit_ref
        and fact.context.statement_basis == statement_basis
    ]
    identities = {
        (
            fact.taxonomy_element,
            fact.context_ref,
            fact.unit_ref,
            fact.value,
        )
        for fact in matches
    }
    return matches[0] if len(matches) == 1 and len(identities) == 1 else None
