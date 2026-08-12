import json
import re
from html import unescape
from html.parser import HTMLParser
from datetime import date, datetime, timezone

import httpx
from sqlmodel import Session, select

from app.models.financial import FinancialSnapshot
from app.models.security import ProviderResponseCache, SecurityMaster
from app.services.provider_telemetry_service import ProviderTelemetryService


_CONCEPTS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "net_income": ("ProfitLoss",),
    "owners_parent_net_income": ("NetIncomeLoss",),
    "common_net_income": ("NetIncomeLossAvailableToCommonStockholdersBasic",),
    "diluted_eps": ("EarningsPerShareDiluted",),
    "common_equity": ("StockholdersEquity",),
    "common_shares_outstanding": ("CommonStockSharesOutstanding",),
    "diluted_shares": ("WeightedAverageNumberOfDilutedSharesOutstanding",),
    "common_dividends": ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends"),
    "buybacks": ("PaymentsForRepurchaseOfCommonStock",),
    "equity_issuance": ("ProceedsFromStockOptionsExercised", "ProceedsFromIssuanceOfCommonStock"),
    "other_comprehensive_income": ("OtherComprehensiveIncomeLossNetOfTax",),
}
_IFRS_CONCEPTS = {
    "revenue": ("Revenue",),
    "net_income": ("ProfitLoss",),
    "owners_parent_net_income": ("ProfitLossAttributableToOwnersOfParent",),
    "common_net_income": (),
    "diluted_eps": ("DilutedEarningsLossPerShare",),
    "common_equity": ("EquityAttributableToOwnersOfParent", "Equity"),
    "common_shares_outstanding": ("NumberOfSharesOutstanding",),
    "diluted_shares": ("WeightedAverageNumberOfSharesOutstandingDiluted",),
    "common_dividends": ("DividendsPaid",),
    "buybacks": ("PaymentsToAcquireOrRedeemEntitysShares",),
    "equity_issuance": ("ProceedsFromIssuingShares",),
    "other_comprehensive_income": ("OtherComprehensiveIncome",),
}
_UNITS = {
    "diluted_eps": ("USD/shares", "USD / shares"),
    "common_shares_outstanding": ("shares",),
    "diluted_shares": ("shares",),
}
_NUMBER_WORDS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "ten": 10.0,
}


def _strip_html(value: str) -> str:
    value = re.sub(
        r"<script.*?</script>|<style.*?</style>",
        " ",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    value = re.sub(r"</(?:tr|p|div|li|br)>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</(?:td|th)>", " | ", value, flags=re.IGNORECASE)
    value = unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"[ \t\r\f\v]+", " ", value)


def _foreign_period_end(text: str) -> date | None:
    patterns = (
        r"(?:quarter|period)\s+ended\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})",
        r"for\s+the\s+(?:first|second|third|fourth)\s+quarter\s+ended\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        try:
            return datetime.strptime(match.group(1), "%B %d, %Y").date()
        except ValueError:
            continue
    return None


def _scaled_financial_field(text: str, label: str) -> tuple[float | None, str | None, str | None]:
    match = re.search(
        rf"(?P<label>{label})\s+(?:was|were|of|totaled|reached)?\s*"
        r"(?P<currency>NT\$|US\$|RMB|CNY|TWD|\$)?\s*"
        r"(?P<value>[\d,.]+)\s*(?P<scale>billion|million)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None, None
    value = float(match.group("value").replace(",", ""))
    value *= 1_000_000_000 if match.group("scale").lower() == "billion" else 1_000_000
    currency = (match.group("currency") or "").upper()
    currency = "TWD" if currency == "NT$" else "USD" if currency in {"US$", "$"} else currency
    return value, currency or None, re.sub(r"\s+", " ", match.group("label")).strip()


def _scaled_financial(text: str, label: str) -> tuple[float | None, str | None]:
    value, currency, _source_label = _scaled_financial_field(text, label)
    return value, currency


def _currency_code(token: object) -> str | None:
    value = str(token or "").strip().upper()
    if value == "NT$":
        return "TWD"
    if value in {"US$", "$"}:
        return "USD"
    return value or None


_EPS_BASIS_PATTERN = (
    r"(?:ADS|ADR)(?:\s+units?)?|American\s+Depositary\s+Shares?|"
    r"ordinary\s+shares?|common\s+shares?"
)


def _eps_security_basis(value: object) -> str:
    text = str(value or "").lower()
    if re.search(r"\b(?:ads|adr)(?:\s+units?)?\b|american\s+depositary\s+shares?", text):
        return "depositary_security"
    if re.search(r"\b(?:ordinary|common)\s+shares?\b", text):
        return "ordinary_share"
    return "unknown"


_EPS_ADJACENT_METRIC_PATTERN = re.compile(
    r"\b(?:cash\s+dividend|dividend|distribution|revenue|operating\s+income|"
    r"income\s+from\s+operations|net\s+income|book\s+value|cash\s+flow|capex)\b",
    flags=re.IGNORECASE,
)


def _foreign_eps_semantic_segment(text: str, start: int, limit: int = 260) -> str:
    """Return the EPS sentence plus an immediately attached parenthetical equivalent."""
    window = text[start : start + limit]
    depth = 0
    index = 0
    while index < len(window):
        char = window[index]
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        if depth == 0 and char in ";|!?":
            window = window[:index]
            break
        if depth == 0 and char == ".":
            decimal_point = (
                index > 0
                and index + 1 < len(window)
                and window[index - 1].isdigit()
                and window[index + 1].isdigit()
            )
            if not decimal_point:
                window = window[:index]
                break
        if depth == 0 and char == "\n":
            remainder = window[index + 1 :]
            if remainder.lstrip().startswith("("):
                index += 1
                continue
            window = window[:index]
            break
        index += 1
    metric_boundary = _EPS_ADJACENT_METRIC_PATTERN.search(window, pos=1)
    if metric_boundary:
        window = window[: metric_boundary.start()]
    return window.strip()


def _foreign_eps_candidates(text: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    label_pattern = re.compile(
        r"diluted\s+(?:earnings\s+per\s+share|EPS)"
        rf"(?P<basis>\s+per\s+(?:{_EPS_BASIS_PATTERN}))?"
        r"(?:\s+(?:of|was|were|is)|\s*[:=])?\s*"
        r"(?P<currency>NT\$|US\$|RMB|CNY|TWD|USD|\$)?\s*"
        r"(?P<value>[\d,.]+)",
        flags=re.IGNORECASE,
    )
    explicit_basis_pattern = re.compile(
        r"(?P<currency>NT\$|US\$|RMB|CNY|TWD|USD|\$)?\s*"
        r"(?P<value>[\d,.]+)\s+per\s+"
        rf"(?P<basis>(?:{_EPS_BASIS_PATTERN}))",
        flags=re.IGNORECASE,
    )
    for label in re.finditer(
        r"diluted\s+(?:earnings\s+per\s+share|EPS)", text, flags=re.IGNORECASE
    ):
        window = _foreign_eps_semantic_segment(text, label.start())
        direct = label_pattern.search(window)
        if direct:
            candidates.append(
                {
                    "value": float(direct.group("value").replace(",", "").rstrip(".")),
                    "currency": _currency_code(direct.group("currency")),
                    "security_basis": _eps_security_basis(direct.group("basis")),
                    "source_label": re.sub(r"\s+", " ", direct.group(0)).strip(),
                    "parse_method": "sec_foreign_release",
                    "representation_type": "primary_eps",
                }
            )
        for explicit in explicit_basis_pattern.finditer(window):
            candidates.append(
                {
                    "value": float(explicit.group("value").replace(",", "").rstrip(".")),
                    "currency": _currency_code(explicit.group("currency")),
                    "security_basis": _eps_security_basis(explicit.group("basis")),
                    "source_label": re.sub(r"\s+", " ", explicit.group(0)).strip(),
                    "parse_method": "sec_foreign_release",
                    "representation_type": "security_equivalent",
                }
            )
    unique: list[dict[str, object]] = []
    seen: set[tuple[float, str | None, str]] = set()
    for candidate in candidates:
        key = (
            float(candidate["value"]),
            candidate.get("currency") if isinstance(candidate.get("currency"), str) else None,
            str(candidate.get("security_basis") or "unknown"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _security_is_depositary(security: SecurityMaster | None) -> bool:
    if security is None:
        return False
    security_type = security.security_type.strip().lower().replace("-", "_").replace(" ", "_")
    return (
        security.issuer_type.strip().lower() == "adr"
        or bool(security.adr_identifier)
        or security_type
        in {
            "adr",
            "ads",
            "depositary_receipt",
            "depositary_security",
            "american_depositary_receipt",
            "american_depositary_share",
        }
    )


def _select_foreign_eps_candidate(
    candidates: list[dict[str, object]],
    *,
    is_depositary_security: bool,
) -> dict[str, object] | None:
    if not candidates:
        return None
    priorities = (
        ("depositary_security", "ordinary_share", "unknown")
        if is_depositary_security
        else ("ordinary_share", "unknown")
    )
    for basis in priorities:
        selected = next(
            (candidate for candidate in candidates if candidate.get("security_basis") == basis),
            None,
        )
        if selected is not None:
            return selected
    return None


class _ForeignTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._cell is not None:
            assert self._row is not None
            self._row.append(re.sub(r"\s+", " ", " ".join(self._cell)).strip())
            self._cell = None
        elif tag.lower() == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None


def _header_matches_period(header: str, period_end: date) -> bool:
    quarter = (period_end.month - 1) // 3 + 1
    year = str(period_end.year)
    short_year = year[-2:]
    normalized = re.sub(r"[^a-z0-9]", "", header.lower())
    quarter_word = {1: "first", 2: "second", 3: "third", 4: "fourth"}[quarter]
    return any(
        token in normalized
        for token in (
            f"{quarter}q{short_year}",
            f"q{quarter}{short_year}",
            f"{quarter}q{year}",
            f"q{quarter}{year}",
            f"{quarter_word}quarter{year}",
        )
    )


def _foreign_table_unit(text: str) -> tuple[str | None, float | None, str | None]:
    match = re.search(
        r"unit\s*[:：]?\s*(NT\$|US\$|USD|TWD|RMB|CNY|\$)\s*(million|billion)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None, None
    scale_name = match.group(2).lower()
    scale = 1_000_000_000.0 if scale_name == "billion" else 1_000_000.0
    return _currency_code(match.group(1)), scale, re.sub(r"\s+", " ", match.group(0)).strip()


def _parse_foreign_operating_income_table(
    html: str,
    period_end: date | None,
) -> dict[str, object] | None:
    if period_end is None:
        return None
    for table_match in re.finditer(r"<table\b.*?</table>", html, flags=re.IGNORECASE | re.DOTALL):
        parser = _ForeignTableParser()
        parser.feed(table_match.group(0))
        current_column: int | None = None
        current_header: str | None = None
        for row in parser.rows:
            for index, cell in enumerate(row):
                if _header_matches_period(cell, period_end):
                    current_column = index
                    current_header = cell
                    break
            if current_column is not None:
                break
        if current_column is None:
            continue
        prefix = _strip_html(html[max(0, table_match.start() - 600) : table_match.start()])
        currency, scale, unit_label = _foreign_table_unit(prefix)
        if scale is None:
            continue
        for row in parser.rows:
            if not row or current_column >= len(row):
                continue
            row_label = re.sub(r"\s+", " ", row[0]).strip()
            normalized_label = row_label.lower()
            if "margin" in normalized_label or not re.fullmatch(
                r"(?:operating income|income from operations|operating profit)",
                normalized_label,
            ):
                continue
            raw_value = row[current_column]
            value_match = re.search(r"\(?\s*([\d,]+(?:\.\d+)?)\s*\)?", raw_value)
            if not value_match or "%" in raw_value:
                continue
            value = float(value_match.group(1).replace(",", "")) * scale
            if raw_value.strip().startswith("("):
                value *= -1
            return {
                "value": value,
                "currency": currency,
                "unit_scale": scale,
                "unit_label": unit_label,
                "row_label": row_label,
                "current_column": current_header,
                "raw_value": raw_value,
                "parse_method": "sec_foreign_html_table",
            }
    return None


def _parse_foreign_financial_release(text: str) -> dict[str, object] | None:
    plain_with_boundaries = _strip_html(text)
    plain = re.sub(r"\s+", " ", plain_with_boundaries).strip()
    period_end = _foreign_period_end(plain)
    revenue, currency, revenue_label = _scaled_financial_field(
        plain, r"(?:consolidated\s+)?(?:net\s+)?revenue"
    )
    table_operating_income = _parse_foreign_operating_income_table(text, period_end)
    operating_income, operating_currency, operating_income_label = _scaled_financial_field(
        plain, r"(?:consolidated\s+)?(?:operating\s+income|income\s+from\s+operations)"
    )
    net_income, income_currency, net_income_label = _scaled_financial_field(
        plain, r"(?:consolidated\s+)?net\s+income"
    )
    common_net_income, common_income_currency, common_income_label = _scaled_financial_field(
        plain,
        r"(?:net\s+income|profit)\s+(?:attributable|available)\s+to\s+"
        r"(?:the\s+)?common\s+(?:shareholders|stockholders)",
    )
    owners_parent_net_income, parent_income_currency, parent_income_label = _scaled_financial_field(
        plain,
        r"(?:net\s+income|profit)\s+attributable\s+to\s+"
        r"(?:owners|shareholders|equity\s+holders)\s+of\s+(?:the\s+)?parent",
    )
    eps_candidates = _foreign_eps_candidates(plain_with_boundaries)
    primary_eps = eps_candidates[0] if eps_candidates else None
    margin_match = re.search(
        r"operating\s+margin(?:\s+for\s+the\s+quarter)?\s+(?:was|of)?\s*([\d.]+)%",
        plain,
        flags=re.IGNORECASE,
    )
    if period_end is None or all(
        value is None
        for value in (
            revenue,
            operating_income,
            net_income,
            common_net_income,
            owners_parent_net_income,
        )
    ):
        return None
    if revenue is not None and net_income is not None and abs(net_income) > revenue:
        return None
    operating_margin = float(margin_match.group(1)) if margin_match else None
    operating_income_source = "reported_prose" if operating_income is not None else None
    operating_income_metadata = table_operating_income or {}
    if table_operating_income is not None:
        operating_income = float(table_operating_income["value"])
        operating_currency = (
            str(table_operating_income.get("currency"))
            if table_operating_income.get("currency")
            else None
        )
        operating_income_label = str(table_operating_income.get("row_label") or "") or None
        operating_income_source = "reported_table"
    elif operating_income is None and revenue is not None and operating_margin is not None:
        operating_income = revenue * operating_margin / 100
        operating_currency = currency
        operating_income_source = "derived_from_reported_revenue_and_operating_margin"
    return {
        "period_end": period_end.isoformat(),
        "revenue": revenue,
        "revenue_source_label": revenue_label,
        "operating_income": operating_income,
        "operating_income_source_label": operating_income_label,
        "operating_income_source": operating_income_source,
        "operating_income_currency": operating_currency,
        "operating_income_current_column": operating_income_metadata.get("current_column"),
        "operating_income_unit_label": operating_income_metadata.get("unit_label"),
        "operating_income_unit_scale": operating_income_metadata.get("unit_scale"),
        "operating_income_raw_value": operating_income_metadata.get("raw_value"),
        "operating_income_parse_method": operating_income_metadata.get("parse_method"),
        "net_income": net_income,
        "net_income_source_label": net_income_label,
        "common_net_income": common_net_income,
        "common_net_income_source_label": common_income_label,
        "owners_parent_net_income": owners_parent_net_income,
        "owners_parent_net_income_source_label": parent_income_label,
        "diluted_eps": float(primary_eps["value"]) if primary_eps else None,
        "eps_currency": primary_eps.get("currency") if primary_eps else None,
        "eps_security_basis": primary_eps.get("security_basis", "unknown")
        if primary_eps
        else "unknown",
        "eps_candidates": eps_candidates,
        "operating_margin": operating_margin,
        "currency": (
            currency
            or operating_currency
            or income_currency
            or common_income_currency
            or parent_income_currency
        ),
    }


def _looks_like_financial_release(text: str) -> bool:
    plain = re.sub(r"\s+", " ", _strip_html(text)).lower()
    markers = (
        "financial results",
        "quarter ended",
        "revenue",
        "net income",
        "earnings per share",
        "balance sheet",
        "cash flow",
    )
    return sum(marker in plain for marker in markers) >= 2


def _linked_documents(html: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for href, label in re.findall(
        r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        clean_label = re.sub(r"\s+", " ", _strip_html(label)).strip()
        if re.search(
            r"press\s+release|earnings|financial|results|quarterly",
            clean_label,
            flags=re.IGNORECASE,
        ):
            links.append((href, clean_label))
    return links


def _adr_ratio_from_text(text: str) -> float | None:
    """Return ordinary shares represented by one ADR/ADS."""
    plain = re.sub(r"\s+", " ", _strip_html(text))
    match = re.search(
        r"(?:each|one)\s+(?:ADS|American\s+Depositary\s+Share).*?represents?\s+"
        r"(one|two|three|four|five|ten|\d+(?:\.\d+)?)\s+"
        r"(?:Class\s+[A-Z]\s+)?(?:ordinary|common)\s+shares?",
        plain,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    token = match.group(1).lower()
    return _NUMBER_WORDS.get(token) or float(token)


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _facts(payload: dict[str, object], field: str) -> list[dict[str, object]]:
    taxonomy = payload.get("facts", {})
    if not isinstance(taxonomy, dict):
        return []
    taxonomies = (("us-gaap", _CONCEPTS[field]), ("ifrs-full", _IFRS_CONCEPTS[field]))
    for taxonomy_name, concepts in taxonomies:
        taxonomy_facts = taxonomy.get(taxonomy_name, {})
        if not isinstance(taxonomy_facts, dict):
            continue
        for concept in concepts:
            raw = taxonomy_facts.get(concept)
            if not isinstance(raw, dict):
                continue
            units = raw.get("units", {})
            if not isinstance(units, dict):
                continue
            preferred = _UNITS.get(field, ("USD", "TWD", "CNY"))
            for unit in preferred:
                entries = units.get(unit)
                if isinstance(entries, list) and entries:
                    return [
                        {**item, "_unit": unit, "_concept": concept, "_taxonomy": taxonomy_name}
                        for item in entries
                        if isinstance(item, dict)
                    ]
            for unit, entries in units.items():
                if isinstance(entries, list) and entries:
                    return [
                        {**item, "_unit": unit, "_concept": concept, "_taxonomy": taxonomy_name}
                        for item in entries
                        if isinstance(item, dict)
                    ]
    return []


def _duration_days(item: dict[str, object]) -> int:
    start = _parse_date(item.get("start"))
    end = _parse_date(item.get("end"))
    return (end - start).days if start and end else 9999


def _period_entries(payload: dict[str, object]) -> list[dict[str, object]]:
    candidates = [
        *_facts(payload, "diluted_eps"),
        *_facts(payload, "net_income"),
        *_facts(payload, "owners_parent_net_income"),
        *_facts(payload, "common_net_income"),
        *_facts(payload, "revenue"),
    ]
    periods: dict[tuple[int, str, date, date], dict[str, object]] = {}
    for item in candidates:
        fy = item.get("fy")
        fp = str(item.get("fp", ""))
        filed = _parse_date(item.get("filed"))
        end = _parse_date(item.get("end"))
        if not isinstance(fy, int) or fp not in {"Q1", "Q2", "Q3", "FY"} or not filed or not end:
            continue
        if str(item.get("form", "")) not in {"10-Q", "10-K", "20-F", "6-K"}:
            continue
        periods[(fy, fp, filed, end)] = item
    return list(periods.values())


def _select_fact(
    entries: list[dict[str, object]],
    fy: int,
    fp: str,
    filed: date,
    end: date,
) -> dict[str, object] | None:
    candidates = [
        item
        for item in entries
        if item.get("fy") == fy
        and str(item.get("fp", "")) == fp
        and _parse_date(item.get("filed")) == filed
        and _parse_date(item.get("end")) == end
        and isinstance(item.get("val"), (int, float))
    ]
    if not candidates:
        return None
    selected = (
        max(candidates, key=_duration_days) if fp == "FY" else min(candidates, key=_duration_days)
    )
    if fp != "FY" and _duration_days(selected) > 130:
        return None
    return selected


def _select_value(
    entries: list[dict[str, object]],
    fy: int,
    fp: str,
    filed: date,
    end: date,
) -> float | None:
    selected = _select_fact(entries, fy, fp, filed, end)
    return float(selected["val"]) if selected else None


def _select_instant_fact(
    entries: list[dict[str, object]], filed: date, end: date
) -> dict[str, object] | None:
    candidates = [
        item
        for item in entries
        if _parse_date(item.get("end")) == end
        and (_parse_date(item.get("filed")) or date.max) <= filed
        and isinstance(item.get("val"), (int, float))
    ]
    if not candidates:
        return None
    selected = max(candidates, key=lambda item: _parse_date(item.get("filed")) or date.min)
    return selected


def _select_instant_value(entries: list[dict[str, object]], filed: date, end: date) -> float | None:
    selected = _select_instant_fact(entries, filed, end)
    return float(selected["val"]) if selected else None


def _unit_currency(unit: object) -> str | None:
    token = str(unit or "").strip().upper().replace(" ", "")
    match = re.match(r"^(USD|TWD|CNY|RMB|KRW)(?:/|$)", token)
    if not match:
        return None
    return "CNY" if match.group(1) == "RMB" else match.group(1)


_INCOME_ATTRIBUTION = {
    "net_income": "total_or_including_nci",
    "owners_parent_net_income": "owners_parent",
    "common_net_income": "common_shareholders",
}


def _companyfacts_snapshots(
    payload: dict[str, object],
    ticker: str,
) -> list[FinancialSnapshot]:
    facts = {field: _facts(payload, field) for field in _CONCEPTS}
    built: list[FinancialSnapshot] = []
    for period in _period_entries(payload):
        fy = int(period["fy"])
        fp = str(period["fp"])
        filed = _parse_date(period.get("filed"))
        end = _parse_date(period.get("end"))
        if filed is None or end is None:
            continue
        period_type = {"Q1": "Q1", "Q2": "H1", "Q3": "Q3", "FY": "FY"}[fp]
        row = FinancialSnapshot(
            ticker=ticker.upper(),
            period=f"{fy}-{fp}",
            period_type=period_type,
            fiscal_year=fy,
            period_scope="annual" if fp == "FY" else "single-quarter",
            is_cumulative=fp == "FY",
            financial_period_end=end,
            financials_as_of=end,
            filing_date=filed,
            reported_date=filed,
            source="SEC Company Facts",
            provider="sec_companyfacts",
            quality_warnings=(
                "foreign issuer filing coverage is partial; ADR ratio and currency mapping required"
                if str(period.get("form", "")) in {"20-F", "6-K"}
                else None
            ),
        )
        selected_facts: dict[str, dict[str, object] | None] = {}
        for field in (
            "revenue",
            "net_income",
            "owners_parent_net_income",
            "common_net_income",
            "diluted_eps",
        ):
            selected_facts[field] = _select_fact(facts[field], fy, fp, filed, end)
            selected = selected_facts[field]
            setattr(row, field, float(selected["val"]) if selected else None)
        row.eps = row.diluted_eps
        selected_facts["common_equity"] = _select_instant_fact(facts["common_equity"], filed, end)
        row.common_equity = (
            float(selected_facts["common_equity"]["val"])
            if selected_facts["common_equity"]
            else None
        )
        row.owners_parent_equity = row.common_equity
        selected_facts["common_shares_outstanding"] = _select_instant_fact(
            facts["common_shares_outstanding"], filed, end
        )
        row.common_shares_outstanding = (
            float(selected_facts["common_shares_outstanding"]["val"])
            if selected_facts["common_shares_outstanding"]
            else None
        )
        selected_facts["diluted_shares"] = _select_fact(facts["diluted_shares"], fy, fp, filed, end)
        row.diluted_shares = (
            float(selected_facts["diluted_shares"]["val"])
            if selected_facts["diluted_shares"]
            else None
        )
        if row.common_shares_outstanding is None:
            row.common_shares_outstanding = row.diluted_shares
        financial_fact = next(
            (
                selected_facts.get(field)
                for field in (
                    "revenue",
                    "net_income",
                    "owners_parent_net_income",
                    "common_net_income",
                    "common_equity",
                )
                if selected_facts.get(field)
            ),
            None,
        )
        row.currency = _unit_currency(financial_fact.get("_unit")) if financial_fact else None
        row.raw_financial_fields = json.dumps(
            [
                {
                    "field": field,
                    "unit": selected.get("_unit"),
                    "currency": _unit_currency(selected.get("_unit")),
                    "security_basis": "unknown",
                    "source": "sec_companyfacts",
                    "concept": selected.get("_concept"),
                    "taxonomy": selected.get("_taxonomy"),
                    "attribution": _INCOME_ATTRIBUTION.get(field),
                }
                for field, selected in selected_facts.items()
                if selected is not None
            ]
        )
        if fp == "FY":
            row.cumulative_revenue = row.revenue
            row.cumulative_net_income = row.net_income
            row.cumulative_diluted_eps = row.diluted_eps
            row.common_dividends = _select_value(facts["common_dividends"], fy, fp, filed, end)
            row.dividends = row.common_dividends
            row.buybacks = _select_value(facts["buybacks"], fy, fp, filed, end)
            row.equity_issuance = _select_value(facts["equity_issuance"], fy, fp, filed, end)
            row.other_comprehensive_income = _select_value(
                facts["other_comprehensive_income"], fy, fp, filed, end
            )
        built.append(row)

    by_year: dict[int, list[FinancialSnapshot]] = {}
    for row in built:
        by_year.setdefault(row.fiscal_year or 0, []).append(row)
    for year_rows in by_year.values():
        annual = next((row for row in year_rows if row.period_type == "FY"), None)
        quarters = [row for row in year_rows if row.period_type != "FY"]
        if annual and len(quarters) == 3:
            for field in (
                "revenue",
                "net_income",
                "owners_parent_net_income",
                "common_net_income",
                "diluted_eps",
            ):
                annual_value = getattr(annual, field)
                quarter_values = [getattr(row, field) for row in quarters]
                if annual_value is not None and all(value is not None for value in quarter_values):
                    setattr(
                        annual,
                        field,
                        float(annual_value) - sum(float(value) for value in quarter_values),
                    )
            annual.eps = annual.diluted_eps
            annual.period_scope = "single-quarter"
            annual.is_cumulative = False
            annual.normalization_method = "FY minus Q1-Q3 standalone by semantic field"
    return built


class SecFinancialSnapshotService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport
        self._ticker_ciks: dict[str, str] | None = None

    async def _resolve_cik(self, client: httpx.AsyncClient, ticker: str) -> str | None:
        if self._ticker_ciks is None:
            response = await client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
            payload = response.json()
            self._ticker_ciks = (
                {
                    str(item.get("ticker", "")).upper(): str(item.get("cik_str", "")).zfill(10)
                    for item in payload.values()
                    if isinstance(item, dict) and item.get("ticker") and item.get("cik_str")
                }
                if isinstance(payload, dict)
                else {}
            )
        return self._ticker_ciks.get(ticker.upper())

    async def _scan_foreign_filings(self, client: httpx.AsyncClient, cik: str) -> dict[str, object]:
        response = await client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        response.raise_for_status()
        payload = response.json()
        recent = payload.get("filings", {}).get("recent", {}) if isinstance(payload, dict) else {}
        forms = recent.get("form", []) if isinstance(recent, dict) else []
        accessions = recent.get("accessionNumber", []) if isinstance(recent, dict) else []
        primary_documents = recent.get("primaryDocument", []) if isinstance(recent, dict) else []
        filing_dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
        candidates: list[dict[str, object]] = []
        parsed_statement: dict[str, object] | None = None
        adr_ratio: float | None = None
        adr_ratio_source: str | None = None
        fetched_documents = 0
        exhibit_documents = 0
        six_k_count = 0
        for form, accession, primary, filing_date in zip(
            forms, accessions, primary_documents, filing_dates, strict=False
        ):
            if form not in {"6-K", "20-F"}:
                continue
            if form == "6-K":
                if six_k_count >= 5:
                    continue
                six_k_count += 1
            accession_path = str(accession).replace("-", "")
            base_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}"
            index_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/index.json"
            )
            index_response = await client.get(index_url)
            index_response.raise_for_status()
            items = index_response.json().get("directory", {}).get("item", [])
            exhibits = []
            for item in items if isinstance(items, list) else []:
                name = str(item.get("name", ""))
                lowered = name.lower()
                if not re.search(r"(?:ex-?99|earn|result|release|financial)", lowered):
                    continue
                exhibits.append(
                    {
                        "name": name,
                        "url": f"{base_url}/{name}",
                    }
                )
            primary_url = f"{base_url}/{primary}"
            primary_response = await client.get(primary_url)
            primary_response.raise_for_status()
            fetched_documents += 1
            primary_text = primary_response.text
            if form == "20-F" and adr_ratio is None:
                adr_ratio = _adr_ratio_from_text(primary_text)
                if adr_ratio is not None:
                    adr_ratio_source = primary_url
            linked = _linked_documents(primary_text)
            known_urls = {str(item["url"]) for item in exhibits}
            for href, label in linked:
                linked_url = str(httpx.URL(primary_url).join(href))
                if linked_url in known_urls:
                    continue
                exhibits.append({"name": label, "url": linked_url})
                known_urls.add(linked_url)
            parsed_here: dict[str, object] | None = None
            financial_candidate = _looks_like_financial_release(primary_text)
            if form in {"6-K", "20-F"}:
                parsed_here = _parse_foreign_financial_release(primary_text)
                for exhibit in exhibits:
                    try:
                        exhibit_response = await client.get(str(exhibit["url"]))
                        exhibit_response.raise_for_status()
                    except httpx.HTTPError:
                        continue
                    fetched_documents += 1
                    exhibit_documents += 1
                    if adr_ratio is None:
                        adr_ratio = _adr_ratio_from_text(exhibit_response.text)
                        if adr_ratio is not None:
                            adr_ratio_source = str(exhibit["url"])
                    financial_candidate = financial_candidate or _looks_like_financial_release(
                        exhibit_response.text
                    )
                    parsed_here = parsed_here or _parse_foreign_financial_release(
                        exhibit_response.text
                    )
                    if parsed_here:
                        parsed_here.update(
                            {
                                "filing_date": str(filing_date),
                                "source_filing_id": str(accession),
                                "source_url": str(exhibit["url"]),
                            }
                        )
                        break
            if parsed_here:
                parsed_here.setdefault("filing_date", str(filing_date))
                parsed_here.setdefault("source_filing_id", str(accession))
                parsed_here.setdefault("source_url", primary_url)
            candidates.append(
                {
                    "form": form,
                    "accession": accession,
                    "filing_date": filing_date,
                    "primary_document": primary,
                    "primary_document_fetched": True,
                    "linked_exhibits": exhibits,
                    "parsing_attempted": True,
                    "statement_parsed": bool(parsed_here),
                    "financial_table_found": bool(parsed_here),
                    "parsing_result": (
                        "parsed"
                        if parsed_here
                        else "validation_failed"
                        if financial_candidate
                        else "not_financial_exhibit"
                    ),
                }
            )
            if parsed_here and parsed_statement is None:
                parsed_statement = parsed_here
            if six_k_count >= 5 and any(item.get("form") == "20-F" for item in candidates):
                break
        parsing_results = {str(item.get("parsing_result")) for item in candidates}
        overall_parsing_result = (
            "parsed"
            if parsed_statement
            else "validation_failed"
            if "validation_failed" in parsing_results
            else "not_financial_exhibit"
            if candidates
            else "filing_not_found"
        )
        latest_filing = candidates[0] if candidates else None
        latest_parsed_filing = next(
            (item for item in candidates if item.get("statement_parsed")),
            None,
        )
        return {
            "filing_discovery_coverage": "full" if candidates else "unavailable",
            "document_fetch_coverage": "full" if fetched_documents else "unavailable",
            "exhibit_discovery_coverage": "full" if exhibit_documents else "partial",
            "statement_parsing_coverage": "full" if parsed_statement else "partial",
            "filing_discovered": bool(candidates),
            "statement_parsing_attempted": bool(candidates),
            "parsing_result": overall_parsing_result,
            "any_statement_parsed": bool(parsed_statement),
            "latest_filing_parse_result": (
                str(latest_filing.get("parsing_result") or "unavailable")
                if latest_filing
                else "unavailable"
            ),
            "latest_financial_statement_period": (
                str(parsed_statement.get("period_end"))
                if parsed_statement and parsed_statement.get("period_end")
                else None
            ),
            "latest_financial_statement_filing_date": (
                str(latest_parsed_filing.get("filing_date")) if latest_parsed_filing else None
            ),
            "parsed_statement": parsed_statement,
            "adr_ratio": adr_ratio,
            "adr_ratio_source": adr_ratio_source,
            "filings": candidates,
        }

    @staticmethod
    def _upsert_foreign_preliminary_snapshot(
        session: Session,
        ticker: str,
        parsed: dict[str, object],
    ) -> int:
        period_end = _parse_date(parsed.get("period_end"))
        filing_date = _parse_date(parsed.get("filing_date"))
        source_filing_id = str(parsed.get("source_filing_id") or "") or None
        if period_end is None or filing_date is None:
            return 0
        existing = session.exec(
            select(FinancialSnapshot).where(
                FinancialSnapshot.ticker == ticker.upper(),
                FinancialSnapshot.snapshot_type == "preliminary_earnings",
                FinancialSnapshot.source_filing_id == source_filing_id,
            )
        ).first()
        row = existing or FinancialSnapshot(
            ticker=ticker.upper(),
            period=f"{period_end.year}-Q{((period_end.month - 1) // 3) + 1}",
            snapshot_type="preliminary_earnings",
            source_filing_id=source_filing_id,
        )
        row.source_event_date = filing_date
        row.period_type = f"Q{((period_end.month - 1) // 3) + 1}"
        row.fiscal_year = period_end.year
        row.period_scope = "single-quarter"
        row.financials_as_of = period_end
        row.financial_period_end = period_end
        row.filing_date = filing_date
        row.reported_date = filing_date
        row.source = str(parsed.get("source_url") or "SEC 6-K exhibit")
        row.provider = "sec_foreign_filing"
        row.currency = str(parsed.get("currency") or "") or None
        row.unit_scale = 1.0
        row.reporting_period_source = "foreign_release_explicit_period"
        row.reporting_period_confidence = "high"
        row.revenue = parsed.get("revenue") if isinstance(parsed.get("revenue"), float) else None
        row.operating_income = (
            parsed.get("operating_income")
            if isinstance(parsed.get("operating_income"), float)
            else None
        )
        row.net_income = (
            parsed.get("net_income") if isinstance(parsed.get("net_income"), float) else None
        )
        row.common_net_income = (
            parsed.get("common_net_income")
            if isinstance(parsed.get("common_net_income"), float)
            else None
        )
        row.owners_parent_net_income = (
            parsed.get("owners_parent_net_income")
            if isinstance(parsed.get("owners_parent_net_income"), float)
            else None
        )
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == ticker.upper())
        ).first()
        eps_candidates = [
            item
            for item in parsed.get("eps_candidates", [])
            if isinstance(item, dict) and isinstance(item.get("value"), (int, float))
        ]
        if not eps_candidates and isinstance(parsed.get("diluted_eps"), (int, float)):
            eps_candidates = [
                {
                    "value": float(parsed["diluted_eps"]),
                    "currency": parsed.get("eps_currency"),
                    "security_basis": parsed.get("eps_security_basis") or "unknown",
                    "source_label": parsed.get("diluted_eps_source_label"),
                    "parse_method": "sec_foreign_release",
                    "representation_type": "primary_eps",
                }
            ]
        selected_eps = (
            _select_foreign_eps_candidate(
                eps_candidates,
                is_depositary_security=_security_is_depositary(security),
            )
            if security is not None
            else eps_candidates[0]
            if eps_candidates
            else None
        )
        row.diluted_eps = float(selected_eps["value"]) if selected_eps else None
        row.eps = row.diluted_eps
        raw_fields: list[dict[str, object]] = []
        for field in (
            "revenue",
            "operating_income",
            "net_income",
            "common_net_income",
            "owners_parent_net_income",
        ):
            value = getattr(row, field)
            if value is None:
                continue
            raw_fields.append(
                {
                    "field": field,
                    "value": value,
                    "currency": (
                        parsed.get("operating_income_currency")
                        if field == "operating_income"
                        else row.currency
                    ),
                    "source_label": parsed.get(f"{field}_source_label"),
                    "attribution": (
                        "common_shareholders"
                        if field == "common_net_income"
                        else "owners_parent"
                        if field == "owners_parent_net_income"
                        else "total"
                        if field == "net_income"
                        else None
                    ),
                    "source": "sec_foreign_filing",
                    "parse_method": (
                        parsed.get("operating_income_parse_method")
                        if field == "operating_income"
                        else "sec_foreign_release"
                    )
                    or "sec_foreign_release",
                    "current_column_header": (
                        parsed.get("operating_income_current_column")
                        if field == "operating_income"
                        else None
                    ),
                    "raw_unit": (
                        parsed.get("operating_income_unit_label")
                        if field == "operating_income"
                        else None
                    ),
                    "unit_scale": (
                        parsed.get("operating_income_unit_scale")
                        if field == "operating_income"
                        else None
                    ),
                    "raw_value": (
                        parsed.get("operating_income_raw_value")
                        if field == "operating_income"
                        else None
                    ),
                }
            )
        if selected_eps is not None:
            raw_fields.append(
                {
                    "field": "diluted_eps",
                    "value": row.diluted_eps,
                    "currency": selected_eps.get("currency"),
                    "security_basis": selected_eps.get("security_basis") or "unknown",
                    "source_label": selected_eps.get("source_label"),
                    "representation_type": selected_eps.get("representation_type"),
                    "selected_for_valuation": True,
                    "source": "sec_foreign_filing",
                    "parse_method": selected_eps.get("parse_method") or "sec_foreign_release",
                }
            )
        for candidate in eps_candidates:
            if candidate is selected_eps:
                continue
            raw_fields.append(
                {
                    "field": "diluted_eps_alternate",
                    "value": candidate.get("value"),
                    "currency": candidate.get("currency"),
                    "security_basis": candidate.get("security_basis") or "unknown",
                    "source_label": candidate.get("source_label"),
                    "representation_type": candidate.get("representation_type"),
                    "selected_for_valuation": False,
                    "source": "sec_foreign_filing",
                    "parse_method": candidate.get("parse_method") or "sec_foreign_release",
                }
            )
        row.raw_financial_fields = json.dumps(raw_fields)
        row.operating_margin = (
            parsed.get("operating_margin")
            if isinstance(parsed.get("operating_margin"), float)
            else None
        )
        row.revenue_basis = "foreign issuer earnings release"
        row.operating_income_basis = str(
            parsed.get("operating_income_source") or "not disclosed in parsed release"
        )
        row.balance_sheet_basis = "not available in preliminary release"
        row.quality_warnings = (
            "preliminary foreign filing; balance sheet and cash flow are not inferred"
        )
        session.add(row)
        session.flush()
        return 1

    async def refresh(
        self,
        session: Session,
        ticker: str,
        user_agent: str,
    ) -> int:
        telemetry = ProviderTelemetryService()
        headers = {"User-Agent": user_agent, "Accept": "application/json"}
        companyfacts_started = datetime.now(timezone.utc)
        async with httpx.AsyncClient(
            timeout=20.0, headers=headers, transport=self.transport
        ) as client:
            cik = await self._resolve_cik(client, ticker)
            if not cik:
                telemetry.record(
                    session,
                    provider="sec_edgar",
                    endpoint="companyfacts",
                    ticker=ticker,
                    started_at=companyfacts_started,
                    status="unavailable",
                    error_reason="cik_not_found",
                )
                return 0
            response = await client.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
            response.raise_for_status()
            payload = response.json()
            telemetry.record(
                session,
                provider="sec_edgar",
                endpoint="companyfacts",
                ticker=ticker,
                started_at=companyfacts_started,
                status="success",
            )
            foreign_started = datetime.now(timezone.utc)
            try:
                exhibit_coverage = await self._scan_foreign_filings(client, cik)
                is_full = exhibit_coverage.get("statement_parsing_coverage") == "full"
                telemetry.record(
                    session,
                    provider="sec_edgar",
                    endpoint="foreign_filings",
                    ticker=ticker,
                    started_at=foreign_started,
                    status="success" if is_full else "partial",
                    error_reason=None if is_full else "foreign_filing_partial",
                )
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                exhibit_coverage = {
                    "filing_discovered": False,
                    "statement_parsing_attempted": True,
                    "filing_discovery_coverage": "partial",
                    "document_fetch_coverage": "partial",
                    "exhibit_discovery_coverage": "partial",
                    "statement_parsing_coverage": "partial",
                    "any_statement_parsed": False,
                    "latest_filing_parse_result": "document_fetch_failed",
                    "latest_financial_statement_period": None,
                    "latest_financial_statement_filing_date": None,
                    "reason": "foreign_filing_partial",
                }
                telemetry.record(
                    session,
                    provider="sec_edgar",
                    endpoint="foreign_filings",
                    ticker=ticker,
                    started_at=foreign_started,
                    status="partial",
                    error_type=type(exc).__name__,
                    error_reason="foreign_filing_partial",
                )
        cache = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "sec_edgar",
                ProviderResponseCache.ticker == ticker.upper(),
                ProviderResponseCache.data_type == "foreign_6k_exhibits",
            )
        ).first() or ProviderResponseCache(
            provider="sec_edgar",
            ticker=ticker.upper(),
            data_type="foreign_6k_exhibits",
        )
        cache.status = "success" if exhibit_coverage.get("filing_discovered") else "partial"
        cache.payload = json.dumps(exhibit_coverage)
        cache.fetched_at = datetime.now(timezone.utc)
        cache.last_success_at = (
            cache.fetched_at if cache.status == "success" else cache.last_success_at
        )
        cache.last_error = None if cache.status == "success" else "foreign_filing_partial"
        session.add(cache)
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == ticker.upper())
        ).first()
        ratio = exhibit_coverage.get("adr_ratio")
        if security is not None and isinstance(ratio, (int, float)) and ratio > 0:
            security.adr_ratio = float(ratio)
            security.adr_ratio_source = str(
                exhibit_coverage.get("adr_ratio_source") or "SEC filing"
            )
            security.adr_ratio_as_of = datetime.now(timezone.utc).date()
            session.add(security)
        preliminary_count = 0
        parsed_statement = exhibit_coverage.get("parsed_statement")
        if isinstance(parsed_statement, dict):
            preliminary_count = self._upsert_foreign_preliminary_snapshot(
                session, ticker, parsed_statement
            )
        if not isinstance(payload, dict) or not isinstance(payload.get("facts"), dict):
            return preliminary_count
        built = _companyfacts_snapshots(payload, ticker)

        updated = 0
        for row in built:
            existing = session.exec(
                select(FinancialSnapshot).where(
                    FinancialSnapshot.ticker == row.ticker,
                    FinancialSnapshot.provider == "sec_companyfacts",
                    FinancialSnapshot.filing_date == row.filing_date,
                    FinancialSnapshot.period_type == row.period_type,
                    FinancialSnapshot.fiscal_year == row.fiscal_year,
                )
            ).first()
            if existing is None:
                session.add(row)
            else:
                for field in row.model_fields:
                    if field not in {"id", "created_at"}:
                        setattr(existing, field, getattr(row, field))
                session.add(existing)
            updated += 1
        session.flush()
        return updated + preliminary_count
