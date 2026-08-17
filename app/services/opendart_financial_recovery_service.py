from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Iterable, Mapping

import httpx

from app.services.kr_financial_lineage_service import (
    FINANCIAL_LINEAGE_VERSION,
    growth_lineage_compatible,
    homogeneous_financial_lineage,
    opendart_field_lineage,
)
from app.services.opendart_xbrl_service import (
    XbrlFact,
    parse_xbrl_archive,
    reconcile_xbrl_fact,
)


RECOVERY_CONTRACT = "opendart-authoritative-recovery-v1"
LIST_ENDPOINT = "https://opendart.fss.or.kr/api/list.json"
STATEMENT_ENDPOINT = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
XBRL_ENDPOINT = "https://opendart.fss.or.kr/api/fnlttXbrl.xml"

REPORT_CODES = {
    "1분기보고서": "11013",
    "반기보고서": "11012",
    "3분기보고서": "11014",
    "사업보고서": "11011",
}


@dataclass(frozen=True)
class FieldSpec:
    logical_field: str
    account_ids: tuple[str, ...]
    account_aliases: tuple[str, ...]
    statement_types: tuple[str, ...]
    source_column: str = "thstrm_amount"
    xbrl_period_required: bool = False


FIELD_SPECS = {
    "revenue": FieldSpec(
        "revenue",
        ("ifrs-full_revenue",),
        ("매출", "매출액", "수익(매출액)", "영업수익"),
        ("IS", "CIS"),
    ),
    "operating_income": FieldSpec(
        "operating_income",
        ("dart_operatingincomeloss",),
        ("영업이익", "영업이익(손실)"),
        ("IS", "CIS"),
    ),
    "net_income": FieldSpec(
        "net_income",
        ("ifrs-full_profitloss",),
        (
            "당기순이익",
            "당기순이익(손실)",
            "분기순이익",
            "반기순이익",
            "연결당기순이익",
        ),
        ("IS", "CIS"),
    ),
    "assets": FieldSpec(
        "assets",
        ("ifrs-full_assets",),
        ("자산총계",),
        ("BS",),
    ),
    "equity": FieldSpec(
        "equity",
        ("ifrs-full_equity",),
        ("자본총계",),
        ("BS",),
    ),
    "inventory": FieldSpec(
        "inventory",
        ("ifrs-full_inventories",),
        ("재고자산",),
        ("BS",),
    ),
    "operating_cash_flow": FieldSpec(
        "operating_cash_flow",
        ("ifrs-full_cashflowsfromusedinoperatingactivities",),
        ("영업활동현금흐름", "영업활동으로 인한 현금흐름"),
        ("CF",),
        xbrl_period_required=True,
    ),
}

CAPEX_COMPONENTS = {
    "ifrs-full_purchaseofpropertyplantandequipmentclassifiedasinvestingactivities": (
        "property_plant_and_equipment"
    ),
    "ifrs-full_purchaseofintangibleassetsclassifiedasinvestingactivities": (
        "intangible_assets"
    ),
    "dart_purchaseofintangibleassetsotherthangoodwill": "intangible_assets",
}


@dataclass(frozen=True)
class Filing:
    ticker: str
    corp_code: str
    company_name: str
    receipt_no: str
    report_name: str
    receipt_date: date
    business_year: int
    report_code: str
    correction: bool


@dataclass(frozen=True)
class BasisSelection:
    status: str
    basis: str
    row: dict[str, object] | None
    candidates: tuple[dict[str, object], ...]
    reason: str | None = None


def _number(value: object) -> float | None:
    text = str(value or "").replace(",", "").strip()
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _date(value: object) -> date:
    text = str(value or "")
    return date.fromisoformat(f"{text[:4]}-{text[4:6]}-{text[6:8]}")


def report_code(report_name: str) -> str | None:
    compact = report_name.replace(" ", "")
    direct = next(
        (code for name, code in REPORT_CODES.items() if name in compact), None
    )
    if direct is not None:
        return direct
    if "분기보고서" not in compact:
        return None
    month_match = re.search(r"20\d{2}[.\-/](\d{1,2})", compact)
    if month_match and int(month_match.group(1)) >= 9:
        return "11014"
    return "11013"


def filing_from_row(
    row: Mapping[str, object], *, ticker: str, corp_code: str
) -> Filing | None:
    name = str(row.get("report_nm") or "")
    code = report_code(name)
    try:
        receipt_date = _date(row.get("rcept_dt"))
    except ValueError:
        return None
    if code is None or not row.get("rcept_no"):
        return None
    year_match = re.search(r"(20\d{2})", name)
    year = int(year_match.group(1)) if year_match else receipt_date.year
    return Filing(
        ticker=ticker,
        corp_code=corp_code,
        company_name=str(row.get("corp_name") or ticker),
        receipt_no=str(row["rcept_no"]),
        report_name=name,
        receipt_date=receipt_date,
        business_year=year,
        report_code=code,
        correction="정정" in name,
    )


def authoritative_filings(
    rows: Iterable[Mapping[str, object]],
    *,
    ticker: str,
    corp_code: str,
    limit: int = 1,
) -> tuple[list[Filing], list[Filing]]:
    filings = [
        filing
        for row in rows
        if (filing := filing_from_row(row, ticker=ticker, corp_code=corp_code))
    ]
    grouped: dict[tuple[int, str], list[Filing]] = {}
    for filing in filings:
        grouped.setdefault((filing.business_year, filing.report_code), []).append(filing)
    selected = [
        max(
            values,
            key=lambda item: (
                item.receipt_date,
                item.correction,
                item.receipt_no,
            ),
        )
        for values in grouped.values()
    ]
    selected.sort(key=lambda item: (item.receipt_date, item.receipt_no), reverse=True)
    return selected[:limit], sorted(
        filings, key=lambda item: (item.receipt_date, item.receipt_no), reverse=True
    )


def _identity(row: Mapping[str, object], source_column: str) -> tuple[str, ...]:
    return tuple(
        str(row.get(key) or "")
        for key in (
            "rcept_no",
            "fs_div",
            "sj_div",
            "account_id",
            "account_nm",
            "account_detail",
            "ord",
            source_column,
            "currency",
        )
    )


def select_basis_occurrence(
    rows: Iterable[Mapping[str, object]], spec: FieldSpec, *, basis: str
) -> BasisSelection:
    normalized = [
        {**row, "fs_div": str(row.get("fs_div") or basis).upper()}
        for row in rows
        if str(row.get("fs_div") or basis).upper() == basis
        and str(row.get("sj_div") or "").upper() in spec.statement_types
        and _number(row.get(spec.source_column)) is not None
    ]
    exact = [
        row
        for row in normalized
        if str(row.get("account_id") or "").lower() in spec.account_ids
    ]
    candidates = exact or [
        row
        for row in normalized
        if str(row.get("account_nm") or "").strip() in spec.account_aliases
    ]
    if not candidates:
        return BasisSelection("missing", basis, None, (), "source_row_missing")
    for statement_type in spec.statement_types:
        preferred = [
            row
            for row in candidates
            if str(row.get("sj_div") or "").upper() == statement_type
        ]
        if preferred:
            candidates = preferred
            break
    unique = {_identity(row, spec.source_column): row for row in candidates}
    if len(unique) != 1:
        return BasisSelection(
            "ambiguous",
            basis,
            None,
            tuple(unique.values()),
            "multiple_source_occurrences",
        )
    row = next(iter(unique.values()))
    if spec.xbrl_period_required:
        return BasisSelection(
            "needs_xbrl",
            basis,
            None,
            (row,),
            "structured_cash_flow_period_ambiguous",
        )
    return BasisSelection("selected", basis, row, (row,))


def select_field_occurrence(
    rows_by_basis: Mapping[str, list[dict[str, object]]], spec: FieldSpec
) -> BasisSelection:
    cfs = select_basis_occurrence(rows_by_basis.get("CFS", []), spec, basis="CFS")
    if cfs.status != "missing":
        return cfs
    return select_basis_occurrence(rows_by_basis.get("OFS", []), spec, basis="OFS")


def _lineage(
    row: Mapping[str, object],
    spec: FieldSpec,
    filing: Filing,
    source_column: str,
    *,
    selected: bool = True,
) -> dict[str, object]:
    return opendart_field_lineage(
        row,
        logical_field=spec.logical_field,
        report_code=filing.report_code,
        source_column=source_column,
        selected=selected,
        requested_fs_div=str(row.get("fs_div") or ""),
    )


def _growth(
    current: Mapping[str, object], comparison: Mapping[str, object]
) -> float | None:
    current_value = _number(current.get("amount"))
    comparison_value = _number(comparison.get("amount"))
    if current_value is None or comparison_value in {None, 0}:
        return None
    return (current_value / comparison_value - 1) * 100


def _xbrl_period(filing: Filing, statement_type: str) -> tuple[date, date]:
    month = {"11013": 3, "11012": 6, "11014": 9, "11011": 12}[filing.report_code]
    end = date(filing.business_year, month, 31 if month in {3, 12} else 30)
    if statement_type == "BS":
        return end, end
    return date(filing.business_year, 1, 1), end


def reconcile_selection_with_xbrl(
    selection: BasisSelection,
    spec: FieldSpec,
    filing: Filing,
    facts: Iterable[XbrlFact],
) -> dict[str, object] | None:
    if len(selection.candidates) != 1:
        return None
    row = selection.candidates[0]
    account_id = str(row.get("account_id") or "")
    if not account_id:
        return None
    period_start, period_end = _xbrl_period(filing, str(row.get("sj_div") or ""))
    basis = "consolidated" if selection.basis == "CFS" else "separate"
    match = reconcile_xbrl_fact(
        facts,
        taxonomy_element=account_id.split("_", maxsplit=1)[-1],
        period_start=period_start,
        period_end=period_end,
        unit_ref="KRW",
        statement_basis=basis,
    )
    if match is None or _number(match.value) != _number(row.get(spec.source_column)):
        return None
    lineage = _lineage(row, spec, filing, spec.source_column)
    lineage.update(
        {
            "amount_period_type": (
                "point_in_time"
                if period_start == period_end
                else "full_year"
                if filing.report_code == "11011"
                else "year_to_date_cumulative"
            ),
            "amount_period_start": period_start.isoformat(),
            "amount_period_end": period_end.isoformat(),
            "lineage_verified": True,
            "quality_state": "verified_usable",
            "denial_reason": None,
            "xbrl_context_ref": match.context_ref,
            "xbrl_taxonomy_element": match.taxonomy_element,
            "xbrl_reconciled": True,
        }
    )
    return lineage


def promote_recovered_fields(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    *,
    blocked_fields: Iterable[str] = (),
    xbrl_facts: Iterable[XbrlFact] = (),
) -> dict[str, object]:
    blocked = set(blocked_fields)
    fields: dict[str, dict[str, object]] = {}
    xbrl_attempts = 0
    xbrl_resolved = 0
    for name, spec in FIELD_SPECS.items():
        selection = select_field_occurrence(rows_by_basis, spec)
        lineage = (
            _lineage(selection.row, spec, filing, spec.source_column)
            if selection.status == "selected" and selection.row is not None
            else None
        )
        if selection.status in {"ambiguous", "needs_xbrl"} and selection.candidates:
            xbrl_attempts += 1
            lineage = reconcile_selection_with_xbrl(
                selection, spec, filing, xbrl_facts
            )
            xbrl_resolved += lineage is not None
        if lineage is not None and name in blocked:
            lineage = {
                **lineage,
                "lineage_verified": False,
                "quality_state": "denied",
                "denial_reason": "unresolved_prior_financial_quality_conflict",
            }
        fields[name] = {
            "status": (
                "verified_usable"
                if lineage is not None and lineage.get("lineage_verified") is True
                else "denied"
                if lineage is not None and lineage.get("quality_state") == "denied"
                else "unknown"
            ),
            "selection_status": selection.status,
            "selection_basis": selection.basis,
            "candidate_count": len(selection.candidates),
            "reason": (
                lineage.get("denial_reason") if lineage is not None else selection.reason
            ),
            "lineage": lineage,
            "value": lineage.get("amount") if lineage is not None else None,
        }

        if lineage is not None and spec.statement_types[0] in {"IS", "CIS"}:
            row = selection.row or selection.candidates[0]
            comparison = _lineage(
                row, spec, filing, "frmtrm_q_amount", selected=False
            )
            comparison["selected_for_canonical"] = True
            compatible = growth_lineage_compatible(
                lineage, comparison, comparison_type="yoy"
            )
            fields[name]["yoy"] = {
                "status": "verified_usable" if compatible else "unknown",
                "value": _growth(lineage, comparison) if compatible else None,
                "current_lineage": lineage,
                "comparison_lineage": comparison,
                "reason": None if compatible else "current_comparison_lineage_not_comparable",
            }

    revenue = fields["revenue"].get("lineage")
    operating = fields["operating_income"].get("lineage")
    margin_compatible = bool(
        isinstance(revenue, dict)
        and isinstance(operating, dict)
        and homogeneous_financial_lineage((revenue, operating))
    )
    revenue_value = _number(fields["revenue"].get("value"))
    operating_value = _number(fields["operating_income"].get("value"))
    fields["operating_margin"] = {
        "status": "verified_usable" if margin_compatible and revenue_value else "unknown",
        "value": (
            operating_value / revenue_value * 100
            if margin_compatible and revenue_value and operating_value is not None
            else None
        ),
        "dependency_lineages": [revenue, operating],
        "reason": None if margin_compatible and revenue_value else "margin_dependency_basis_mismatch",
    }
    capex_components: list[dict[str, object]] = []
    for basis, rows in rows_by_basis.items():
        for row in rows:
            account_id = str(row.get("account_id") or "").lower()
            classification = CAPEX_COMPONENTS.get(account_id)
            if classification is None or str(row.get("sj_div") or "") != "CF":
                continue
            component_lineage = _lineage(
                row,
                FieldSpec(
                    "capex_component",
                    (account_id,),
                    (),
                    ("CF",),
                    xbrl_period_required=True,
                ),
                filing,
                "thstrm_amount",
                selected=False,
            )
            capex_components.append(
                {
                    "classification": classification,
                    "classification_confidence": "taxonomy_exact",
                    "basis": basis,
                    "account_id": row.get("account_id"),
                    "account_name": row.get("account_nm"),
                    "amount": _number(row.get("thstrm_amount")),
                    "currency": row.get("currency"),
                    "lineage": component_lineage,
                    "aggregation_eligible": False,
                    "reason": "cash_flow_period_requires_unique_xbrl_context",
                }
            )
    return {
        "contract": RECOVERY_CONTRACT,
        "financial_lineage_contract": FINANCIAL_LINEAGE_VERSION,
        "filing": filing.__dict__,
        "fields": fields,
        "capex_components": capex_components,
        "xbrl": {"attempts": xbrl_attempts, "resolved": xbrl_resolved},
    }


class OpenDartRecoveryClient:
    def __init__(
        self,
        api_key: str,
        cache_dir: Path,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 20.0,
    ) -> None:
        self._api_key = api_key
        self.cache_dir = cache_dir
        self._transport = transport
        self._timeout = timeout
        self.provider_calls = 0
        self.xbrl_cache_hits = 0

    async def _json(
        self, client: httpx.AsyncClient, endpoint: str, params: dict[str, object]
    ) -> dict[str, object]:
        self.provider_calls += 1
        response = await client.get(endpoint, params={"crtfc_key": self._api_key, **params})
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") == "013":
            return {**payload, "list": []}
        if payload.get("status") not in {None, "000"}:
            raise ValueError(f"OpenDART status {payload.get('status')}: {payload.get('message')}")
        return payload

    async def discover(
        self,
        *,
        ticker: str,
        corp_code: str,
        begin: date,
        end: date,
        limit: int = 1,
    ) -> tuple[list[Filing], list[Filing]]:
        rows: list[dict[str, object]] = []
        page = 1
        async with httpx.AsyncClient(
            timeout=self._timeout, transport=self._transport
        ) as client:
            while True:
                payload = await self._json(
                    client,
                    LIST_ENDPOINT,
                    {
                        "corp_code": corp_code,
                        "bgn_de": begin.strftime("%Y%m%d"),
                        "end_de": end.strftime("%Y%m%d"),
                        "pblntf_ty": "A",
                        "last_reprt_at": "N",
                        "page_count": 100,
                        "page_no": page,
                    },
                )
                rows.extend(
                    item for item in payload.get("list", []) if isinstance(item, dict)
                )
                total = int(payload.get("total_page") or page)
                if page >= total:
                    break
                page += 1
        return authoritative_filings(
            rows, ticker=ticker, corp_code=corp_code, limit=limit
        )

    async def statements(self, filing: Filing) -> dict[str, list[dict[str, object]]]:
        output: dict[str, list[dict[str, object]]] = {}
        async with httpx.AsyncClient(
            timeout=self._timeout, transport=self._transport
        ) as client:
            for basis in ("CFS", "OFS"):
                payload = await self._json(
                    client,
                    STATEMENT_ENDPOINT,
                    {
                        "corp_code": filing.corp_code,
                        "bsns_year": filing.business_year,
                        "reprt_code": filing.report_code,
                        "fs_div": basis,
                    },
                )
                rows = [
                    {**item, "fs_div": item.get("fs_div") or basis}
                    for item in payload.get("list", [])
                    if isinstance(item, dict)
                    and str(item.get("rcept_no") or filing.receipt_no)
                    == filing.receipt_no
                ]
                output[basis] = rows
                raw = _canonical_json_bytes(
                    {
                        "contract": RECOVERY_CONTRACT,
                        "ticker": filing.ticker,
                        "corp_code": filing.corp_code,
                        "rcept_no": filing.receipt_no,
                        "fs_div": basis,
                        "request_date": date.today().isoformat(),
                        "response_sha256": _sha256_bytes(_canonical_json_bytes(payload)),
                        "rows": rows,
                    }
                )
                _atomic_write(
                    self.cache_dir
                    / filing.ticker
                    / filing.receipt_no
                    / f"{basis}.json",
                    raw + b"\n",
                )
        return output

    async def xbrl_facts(self, filing: Filing) -> tuple[list[XbrlFact], str]:
        path = self.cache_dir / filing.ticker / filing.receipt_no / "xbrl.zip"
        if path.exists():
            self.xbrl_cache_hits += 1
            payload = path.read_bytes()
        else:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                self.provider_calls += 1
                response = await client.get(
                    XBRL_ENDPOINT,
                    params={
                        "crtfc_key": self._api_key,
                        "rcept_no": filing.receipt_no,
                        "reprt_code": filing.report_code,
                    },
                )
                response.raise_for_status()
                payload = response.content
            _atomic_write(path, payload)
            _atomic_write(
                path.with_suffix(".metadata.json"),
                _canonical_json_bytes(
                    {
                        "contract": RECOVERY_CONTRACT,
                        "rcept_no": filing.receipt_no,
                        "response_sha256": _sha256_bytes(payload),
                    }
                )
                + b"\n",
            )
        _contexts, facts = parse_xbrl_archive(payload)
        return facts, _sha256_bytes(payload)

    async def recover_filing(
        self,
        filing: Filing,
        *,
        blocked_fields: Iterable[str] = (),
    ) -> dict[str, object]:
        rows = await self.statements(filing)
        recovered = promote_recovered_fields(
            filing, rows, blocked_fields=blocked_fields
        )
        if recovered["xbrl"]["attempts"]:
            try:
                facts, archive_sha = await self.xbrl_facts(filing)
            except (httpx.HTTPError, ValueError):
                recovered["xbrl"].update(
                    {"provider_call_failed": True, "archive_sha256": None}
                )
            else:
                recovered = promote_recovered_fields(
                    filing,
                    rows,
                    blocked_fields=blocked_fields,
                    xbrl_facts=facts,
                )
                recovered["xbrl"].update(
                    {"provider_call_failed": False, "archive_sha256": archive_sha}
                )
        recovered["provider_calls"] = self.provider_calls
        recovered["xbrl_cache_hits"] = self.xbrl_cache_hits
        recovered["raw_cache_root"] = str(
            self.cache_dir / filing.ticker / filing.receipt_no
        )
        return recovered
