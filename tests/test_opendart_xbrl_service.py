from __future__ import annotations

from datetime import date
from io import BytesIO
from zipfile import ZipFile

import pytest

from app.services.opendart_xbrl_service import (
    parse_xbrl_archive,
    parse_xbrl_document,
    reconcile_xbrl_fact,
)


XBRL = b"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:ifrs="http://xbrl.ifrs.org/taxonomy/2024-03-27/ifrs-full"
      xmlns:dart="http://dart.fss.or.kr/taxonomy">
  <context id="duration-cfs">
    <entity><identifier scheme="corp">00126380</identifier>
      <segment><xbrldi:explicitMember dimension="dart:StatementBasisAxis">dart:ConsolidatedMember</xbrldi:explicitMember></segment>
    </entity>
    <period><startDate>2026-04-01</startDate><endDate>2026-06-30</endDate></period>
  </context>
  <context id="instant-cfs">
    <entity><identifier scheme="corp">00126380</identifier>
      <segment><xbrldi:explicitMember dimension="dart:StatementBasisAxis">dart:ConsolidatedMember</xbrldi:explicitMember></segment>
    </entity>
    <period><instant>2026-06-30</instant></period>
  </context>
  <ifrs:Revenue contextRef="duration-cfs" unitRef="KRW">171000000000000</ifrs:Revenue>
  <ifrs:Equity contextRef="instant-cfs" unitRef="KRW">100000000000000</ifrs:Equity>
</xbrl>"""


def test_xbrl_parser_preserves_duration_instant_dimension_and_unit() -> None:
    contexts, facts = parse_xbrl_document(XBRL)

    assert {item.period_type for item in contexts} == {"duration", "instant"}
    revenue = next(item for item in facts if item.taxonomy_element.endswith("Revenue"))
    assert revenue.context.period_start == date(2026, 4, 1)
    assert revenue.context.period_end == date(2026, 6, 30)
    assert revenue.context.statement_basis == "consolidated"
    assert revenue.unit_ref == "KRW"


def test_xbrl_reconciliation_requires_unique_exact_context() -> None:
    _contexts, facts = parse_xbrl_document(XBRL)

    exact = reconcile_xbrl_fact(
        facts,
        taxonomy_element="Revenue",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 6, 30),
        unit_ref="KRW",
        statement_basis="consolidated",
    )
    mismatch = reconcile_xbrl_fact(
        facts,
        taxonomy_element="Revenue",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        unit_ref="KRW",
        statement_basis="consolidated",
    )

    assert exact is not None
    assert mismatch is None
    assert reconcile_xbrl_fact(
        [*facts, exact],
        taxonomy_element="Revenue",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 6, 30),
        unit_ref="KRW",
        statement_basis="consolidated",
    ) is None


def test_xbrl_archive_uses_zip_and_rejects_invalid_payload() -> None:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("instance.xbrl", XBRL)

    contexts, facts = parse_xbrl_archive(payload.getvalue())

    assert contexts
    assert facts
    with pytest.raises(ValueError, match="valid archive"):
        parse_xbrl_archive(b"not-a-zip")
