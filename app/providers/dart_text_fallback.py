from dataclasses import dataclass
from datetime import date
from html import unescape
from html.parser import HTMLParser
import re

import httpx


@dataclass(frozen=True)
class DartViewerParams:
    receipt_no: str
    dcm_no: str
    ele_id: str
    offset: str
    length: str
    dtd: str


@dataclass(frozen=True)
class DartDocumentText:
    text: str
    dcm_no: str | None
    source: str
    viewer_params: DartViewerParams | None = None
    html: str | None = None


@dataclass(frozen=True)
class PreliminaryEarningsFacts:
    facts: list[str]
    period_end: date | None
    reporting_period_source: str | None
    reporting_period_confidence: str
    revenue: float | None
    operating_income: float | None
    net_income: float | None
    owners_parent_net_income: float | None
    operating_margin: float | None
    yoy_growth: float | None
    qoq_growth: float | None
    unit_scale: float
    raw_fields: list[dict[str, object]]
    diagnostics: dict[str, object]


def _strip_html(value: str) -> str:
    value = re.sub(r"</(tr|p|div|li|br)>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</(td|th)>", " | ", value, flags=re.IGNORECASE)
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value


def _clean_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" |\n\t")


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", _clean_cell(value))


def _parse_js_args(args: str) -> list[str]:
    return [part.strip().strip("'\"") for part in re.split(r"\s*,\s*", args) if part.strip()]


def _extract_viewer_params(html: str, receipt_no: str) -> DartViewerParams | None:
    for match in re.finditer(r"viewDoc\(([^)]*)\)", html):
        args = _parse_js_args(match.group(1))
        if len(args) < 6 or args[0] != receipt_no:
            continue
        return DartViewerParams(
            receipt_no=args[0],
            dcm_no=args[1],
            ele_id=args[2],
            offset=args[3],
            length=args[4],
            dtd=args[5],
        )
    return None


def _extract_dcm_no(html: str, receipt_no: str) -> str | None:
    viewer_params = _extract_viewer_params(html, receipt_no)
    if viewer_params:
        return viewer_params.dcm_no
    patterns = [
        rf"viewDoc\(['\"]{re.escape(receipt_no)}['\"]\s*,\s*['\"](\d+)['\"]",
        r"dcmNo['\"]?\s*[:=]\s*['\"]?(\d+)",
        r"dcmNo=(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def _is_placeholder_value(value: str) -> bool:
    cleaned = _clean_cell(value)
    compact = _compact(cleaned)
    if not cleaned:
        return True
    placeholders = {
        "(원)",
        "(%)",
        "시작일",
        "종료일",
        "5.계약기간",
        "3.계약상대",
        "4.판매ㆍ공급지역",
        "4.판매·공급지역",
        "-체결계약명",
        "계약금액",
        "계약금액(원)",
        "매출액대비",
        "매출액대비(%)",
        "최근매출액대비",
        "최근매출액대비(%)",
    }
    if compact in {item.replace(" ", "") for item in placeholders}:
        return True
    non_fact_fragments = (
        "진행과정에서변경될수있습니다",
        "향후계약내용",
        "상기계약금액",
        "상기내용은",
        "본공시사항은",
    )
    return any(fragment in compact for fragment in non_fact_fragments)


def _looks_like_amount(value: str) -> bool:
    if _is_placeholder_value(value):
        return False
    compact = _compact(value)
    has_currency_marker = any(marker in compact for marker in ("원", "KRW", "krw", "USD", "달러", "$"))
    has_large_number = re.search(r"\d{1,3}(,\d{3})+|\d{7,}", compact) is not None
    return has_currency_marker or has_large_number


def _looks_like_ratio(value: str) -> bool:
    if _is_placeholder_value(value):
        return False
    compact = _compact(value)
    return re.fullmatch(r"\d+(\.\d+)?%?", compact) is not None or ("%" in compact and re.search(r"\d", compact) is not None)


def _looks_like_date(value: str) -> bool:
    return re.search(r"20\d{2}[.\-/년]\d{1,2}", _compact(value)) is not None


def _looks_like_date_or_period(value: str) -> bool:
    if _is_placeholder_value(value):
        return False
    compact = _compact(value)
    return _looks_like_date(value) and any(marker in compact for marker in ("부터", "까지", "~", "-"))


def _looks_like_text_fact(value: str) -> bool:
    if _is_placeholder_value(value):
        return False
    compact = _compact(value)
    if len(compact) < 2:
        return False
    return not any(fragment in compact for fragment in ("계약금액", "매출액대비", "계약기간"))


def _candidate_is_valid(field_key: str, value: str) -> bool:
    if field_key == "amount":
        return _looks_like_amount(value)
    if field_key == "recent_sales_ratio":
        return _looks_like_ratio(value)
    if field_key == "period":
        return _looks_like_date_or_period(value)
    if field_key in {"start_date", "end_date"}:
        return _looks_like_date(value)
    return _looks_like_text_fact(value)


def _tokens(text: str) -> list[str]:
    return [_clean_cell(part) for part in text.replace("\n", " | ").split("|") if _clean_cell(part)]


def _token_value(text: str, labels: tuple[str, ...], field_key: str) -> str | None:
    tokens = _tokens(text)
    for index, token in enumerate(tokens):
        token_compact = _compact(token)
        for label in labels:
            label_compact = _compact(label)
            if label_compact not in token_compact:
                continue
            for candidate in tokens[index + 1 : index + 4]:
                if _candidate_is_valid(field_key, candidate):
                    return candidate
    return None


def _row_value(text: str, labels: tuple[str, ...], field_key: str) -> str | None:
    token_match = _token_value(text, labels, field_key)
    if token_match:
        return token_match
    lines = [_clean_cell(line) for line in text.splitlines() if _clean_cell(line)]
    for line in lines:
        compact = line.replace(" ", "")
        for label in labels:
            label_compact = label.replace(" ", "")
            if label_compact not in compact:
                continue
            parts = [_clean_cell(part) for part in line.split("|") if _clean_cell(part)]
            candidates: list[str] = []
            for index, part in enumerate(parts):
                if label_compact in part.replace(" ", ""):
                    candidates.extend(parts[index + 1 :])
                    tail = part.split(label, 1)[-1]
                    if _clean_cell(tail):
                        candidates.append(_clean_cell(tail))
            for candidate in candidates:
                if _candidate_is_valid(field_key, candidate):
                    return candidate
    return None


def _period_from_start_end(text: str) -> str | None:
    start = _token_value(text, ("시작일", "계약시작일"), "start_date")
    end = _token_value(text, ("종료일", "계약종료일"), "end_date")
    if start and end:
        return f"{start} to {end}"
    return None


def extract_supply_contract_facts_from_text(text: str) -> list[str]:
    fields = [
        ("contract_name", ("체결계약명", "계약명", "판매ㆍ공급계약 내용", "판매·공급계약 내용", "계약내용")),
        ("counterparty", ("계약상대방", "계약상대", "상대방")),
        ("amount", ("계약금액(원)", "계약금액", "계약 금액")),
        ("recent_sales_ratio", ("매출액대비(%)", "매출액대비", "최근매출액 대비", "최근 매출액 대비")),
        ("region", ("판매ㆍ공급지역", "판매·공급지역", "공급지역")),
    ]
    facts: list[str] = []
    for key, labels in fields:
        value = _row_value(text, labels, key)
        if value:
            facts.append(f"DART text supply contract fact: {key} = {value}")
    period = _period_from_start_end(text)
    if period:
        facts.append(f"DART text supply contract fact: period = {period}")
    return facts


def _numeric_cell(value: str) -> float | None:
    cleaned = _clean_cell(value).replace(",", "").replace("△", "-")
    cleaned = cleaned.replace("▲", "-").replace("%", "")
    match = re.fullmatch(r"\(?\s*(-?\d+(?:\.\d+)?)\s*\)?", cleaned)
    if not match:
        return None
    number = float(match.group(1))
    return -number if cleaned.startswith("(") and number > 0 else number


def _preliminary_unit_scale(tokens: list[str]) -> float:
    unit_text = next((token for token in tokens if "단위" in token), "")
    compact = _compact(unit_text)
    if "백만원" in compact:
        return 1_000_000.0
    if "억원" in compact:
        return 100_000_000.0
    if "조원" in compact:
        return 1_000_000_000_000.0
    if "천원" in compact:
        return 1_000.0
    return 1.0


def _preliminary_unit_label(tokens: list[str]) -> str | None:
    unit_text = next((token for token in tokens if "단위" in token), None)
    if unit_text is None:
        return None
    match = re.search(r"단위\s*[:：]?\s*([^,|]+)", unit_text)
    return _clean_cell(match.group(1)) if match else _clean_cell(unit_text)


class _DartTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[dict[str, object]] = []
        self._table: dict[str, object] | None = None
        self._row: list[dict[str, object]] | None = None
        self._cell: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table":
            self._table = {"id": attributes.get("id") or f"table-{len(self.tables)}", "rows": []}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = {
                "text": [],
                "rowspan": int(attributes.get("rowspan") or 1),
                "colspan": int(attributes.get("colspan") or 1),
            }
        elif tag == "br" and self._cell is not None:
            self._cell["text"].append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell["text"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._cell["text"] = _clean_cell("".join(self._cell["text"]))
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table["rows"].append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def _expanded_table_rows(rows: list[list[dict[str, object]]]) -> list[list[str]]:
    active: dict[int, tuple[str, int]] = {}
    expanded: list[list[str]] = []
    for source_row in rows:
        cells: dict[int, str] = {}
        next_active: dict[int, tuple[str, int]] = {}
        for column, (text, remaining) in active.items():
            cells[column] = text
            if remaining > 1:
                next_active[column] = (text, remaining - 1)
        column = 0
        for source_cell in source_row:
            while column in cells:
                column += 1
            text = str(source_cell.get("text") or "")
            colspan = int(source_cell.get("colspan") or 1)
            rowspan = int(source_cell.get("rowspan") or 1)
            for offset in range(colspan):
                target = column + offset
                cells[target] = text
                if rowspan > 1:
                    next_active[target] = (text, rowspan - 1)
            column += colspan
        active = next_active
        maximum = max(cells, default=-1)
        expanded.append([cells.get(index, "") for index in range(maximum + 1)])
    return expanded


_PRELIMINARY_METRIC_ALIASES = {
    "매출액": ("매출액", "영업수익", "수익(매출액)"),
    "영업이익": ("영업이익", "영업이익(손실)"),
    "당기순이익": ("당기순이익", "분기순이익", "반기순이익"),
    "지배주주순이익": (
        "지배기업 소유주지분 순이익",
        "지배기업 소유주지분",
        "지배기업 소유주 귀속 당기순이익",
        "지배기업 소유주 귀속 순이익",
        "지배주주순이익",
    ),
}
_CURRENT_RESULT_ALIASES = {"당기실적", "당해실적"}
_CUMULATIVE_RESULT_ALIASES = {"누계실적", "당기누계실적"}


def _canonical_metric_label(value: str) -> str | None:
    compact = _compact(value)
    for label, aliases in _PRELIMINARY_METRIC_ALIASES.items():
        if compact in {_compact(alias) for alias in aliases}:
            return label
    return None


def _semantic_preliminary_table(
    html: str,
    source_receipt_no: str | None,
) -> tuple[
    dict[str, dict[str, float | None]],
    list[dict[str, object]],
    str | None,
    dict[str, object],
]:
    parser = _DartTableParser()
    parser.feed(html)
    diagnostics: dict[str, object] = {
        "parse_method": "flat_token_fallback",
        "semantic_table_found": False,
        "tables_scanned": len(parser.tables),
        "header_index": None,
        "current_column": None,
        "qoq_column": None,
        "yoy_column": None,
        "unit": None,
        "metric_labels_found": [],
    }
    candidates: list[
        tuple[
            int,
            dict[str, dict[str, float | None]],
            list[dict[str, object]],
            str | None,
            dict[str, object],
        ]
    ] = []
    for table_index, table in enumerate(parser.tables):
        rows = _expanded_table_rows(table.get("rows", []))
        header_index = next(
            (
                index
                for index, row in enumerate(rows)
                if any(_compact(cell) in _CURRENT_RESULT_ALIASES for cell in row)
                and any("전기실적" in _compact(cell) for cell in row)
            ),
            None,
        )
        if header_index is None:
            continue
        header_rows = [rows[header_index]]
        for candidate in rows[header_index + 1 : header_index + 4]:
            if any(_canonical_metric_label(cell) for cell in candidate):
                break
            header_rows.append(candidate)
        column_count = max(len(row) for row in header_rows)
        column_headers: list[str] = []
        for column in range(column_count):
            header_parts = [
                row[column]
                for row in header_rows
                if column < len(row) and row[column]
            ]
            column_headers.append(
                _clean_cell(" ".join(dict.fromkeys(header_parts)))
            )
        current_column = next(
            (
                index
                for index, value in enumerate(column_headers)
                if any(alias in _compact(value) for alias in _CURRENT_RESULT_ALIASES)
            ),
            None,
        )
        if current_column is None:
            continue
        current_header = _compact(column_headers[current_column])
        if "증감" in current_header or "증감률" in current_header:
            continue
        qoq_column = next(
            (
                index
                for index, value in enumerate(column_headers)
                if "전기대비" in _compact(value) and "증감" in _compact(value)
            ),
            None,
        )
        yoy_column = next(
            (
                index
                for index, value in enumerate(column_headers)
                if "전년동기대비" in _compact(value) and "증감" in _compact(value)
            ),
            None,
        )
        unit_text = next(
            (cell for row in rows for cell in row if "단위" in cell),
            None,
        )
        unit_label = _preliminary_unit_label([unit_text] if unit_text else [])
        metrics: dict[str, dict[str, float | None]] = {}
        raw_fields: list[dict[str, object]] = []
        data_start = header_index + len(header_rows)
        for row_index, row in enumerate(rows[data_start:], data_start):
            metric = next((_canonical_metric_label(cell) for cell in row if _canonical_metric_label(cell)), None)
            period_marker = next(
                (
                    _compact(cell)
                    for cell in row
                    if _compact(cell)
                    in _CURRENT_RESULT_ALIASES | _CUMULATIVE_RESULT_ALIASES
                ),
                None,
            )
            if metric is None or period_marker is None or current_column >= len(row):
                continue
            values = metrics.setdefault(
                metric,
                {"current": None, "cumulative": None, "qoq": None, "yoy": None},
            )
            current_value = _numeric_cell(row[current_column])
            if period_marker in _CURRENT_RESULT_ALIASES:
                values["current"] = current_value
                if qoq_column is not None and qoq_column < len(row):
                    values["qoq"] = _numeric_cell(row[qoq_column])
                if yoy_column is not None and yoy_column < len(row):
                    values["yoy"] = _numeric_cell(row[yoy_column])
            else:
                values["cumulative"] = current_value
            for column_index, cell in enumerate(row):
                if _numeric_cell(cell) is None:
                    continue
                header_name = (
                    column_headers[column_index]
                    if column_index < len(column_headers)
                    else f"column_{column_index}"
                )
                if period_marker in _CUMULATIVE_RESULT_ALIASES and column_index == current_column:
                    header_name = "당기누계실적"
                raw_fields.append(
                    {
                        "raw_label": metric,
                        "raw_value": cell,
                        "raw_unit": unit_label,
                        "raw_period": (
                            "year_to_date"
                            if period_marker in _CUMULATIVE_RESULT_ALIASES
                            else "single_quarter"
                        ),
                        "raw_column_header": header_name,
                        "source_receipt_no": source_receipt_no,
                        "row_index": row_index,
                        "column_index": column_index,
                        "table_id": table.get("id") or f"table-{table_index}",
                        "parse_method": "html_semantic_table",
                    }
                )
        if metrics:
            score = len(metrics) * 10
            score += 6 if "매출액" in metrics else 0
            score += 6 if "영업이익" in metrics else 0
            score += 3 if "당기순이익" in metrics else 0
            score += 2 if unit_label else 0
            score += 2 if any("전년동기실적" in _compact(value) for value in column_headers) else 0
            revenue = metrics.get("매출액", {}).get("current")
            operating_income = metrics.get("영업이익", {}).get("current")
            net_income = metrics.get("당기순이익", {}).get("current")
            if isinstance(revenue, (int, float)) and revenue > 0:
                if isinstance(operating_income, (int, float)) and abs(operating_income) > revenue:
                    score -= 20
                if isinstance(net_income, (int, float)) and abs(net_income) > revenue:
                    score -= 20
            candidate_diagnostics = {
                "parse_method": "html_semantic_table",
                "semantic_table_found": True,
                "table_id": table.get("id") or f"table-{table_index}",
                "header_index": header_index,
                "header_rows": header_rows,
                "column_headers": column_headers,
                "current_column": current_column,
                "qoq_column": qoq_column,
                "yoy_column": yoy_column,
                "unit": unit_label,
                "metric_labels_found": list(metrics),
                "candidate_score": score,
            }
            candidates.append(
                (score, metrics, raw_fields, unit_label, candidate_diagnostics)
            )
    if candidates:
        candidates.sort(key=lambda candidate: candidate[0], reverse=True)
        _score, metrics, raw_fields, unit_label, selected = candidates[0]
        selected["candidate_count"] = len(candidates)
        return metrics, raw_fields, unit_label, selected
    return {}, [], None, diagnostics


_DATE_PATTERN = r"(20\d{2})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{1,2})"


def _dates_in_text(value: str) -> list[date]:
    dates: list[date] = []
    for match in re.finditer(_DATE_PATTERN, value):
        try:
            dates.append(date(*(int(part) for part in match.groups())))
        except ValueError:
            continue
    return dates


def _quarter_from_text(value: str) -> date | None:
    quarter_match = re.search(r"(20\d{2})\s*년?\s*([1-4])\s*분기", value)
    if quarter_match:
        year, quarter = (int(part) for part in quarter_match.groups())
        month_day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[quarter]
        return date(year, *month_day)
    short_quarter_match = re.search(
        r"(?:['`’]\s*)?(\d{2})\s*[.\-/]?\s*([1-4])\s*[Qq]\b",
        value,
    )
    if short_quarter_match:
        year, quarter = (int(part) for part in short_quarter_match.groups())
        month_day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[quarter]
        return date(2000 + year, *month_day)
    half_match = re.search(r"(20\d{2})\s*년?\s*(상반기|하반기)", value)
    if half_match:
        year = int(half_match.group(1))
        return date(year, 6, 30) if half_match.group(2) == "상반기" else date(year, 12, 31)
    return None


def _period_from_current_text(
    value: str,
) -> tuple[date | None, str | None, str, list[date]]:
    dates = _dates_in_text(value)
    range_marker = bool(
        re.search(
            rf"{_DATE_PATTERN}\s*(?:~|〜|–|—|-|부터)\s*{_DATE_PATTERN}",
            value,
        )
    )
    if (range_marker or len(dates) == 2) and len(dates) >= 2:
        return dates[1], "current_header_date_range", "high", dates
    quarter = _quarter_from_text(value)
    if quarter is not None:
        return quarter, "current_header_quarter", "high", [*dates, quarter]
    if len(dates) == 1:
        return dates[0], "current_row_period", "medium", dates
    return None, None, "unavailable", dates


def _preliminary_period_end(
    tokens: list[str],
) -> tuple[date | None, str | None, str, list[date]]:
    result_indexes = [
        index
        for index, token in enumerate(tokens)
        if _compact(token) in _CURRENT_RESULT_ALIASES
    ]
    for result_index in result_indexes:
        current_tokens: list[str] = []
        for token in tokens[result_index : result_index + 8]:
            compact = _compact(token)
            if token != tokens[result_index] and (
                "전기실적" in compact or "전년동기실적" in compact
            ):
                break
            current_tokens.append(token)
        period, source, confidence, dates = _period_from_current_text(
            " ".join(current_tokens)
        )
        if period is None:
            continue
        if source == "current_header_date_range":
            source = "document_explicit_date_range"
        elif source == "current_header_quarter":
            source = "document_explicit_quarter"
        return period, source, confidence, dates
    return None, None, "unavailable", []


def _preliminary_period_end_from_semantic_header(
    diagnostics: dict[str, object],
) -> tuple[date | None, str | None, str, list[date], list[date]]:
    headers = diagnostics.get("column_headers")
    current_column = diagnostics.get("current_column")
    if not isinstance(headers, list) or not isinstance(current_column, int):
        return None, None, "unavailable", [], []
    if current_column >= len(headers):
        return None, None, "unavailable", [], []
    header = str(headers[current_column])
    period, source, confidence, current_dates = _period_from_current_text(header)
    ignored_dates: list[date] = []
    for index, candidate_header in enumerate(headers):
        if index == current_column:
            continue
        candidate_text = str(candidate_header)
        ignored_dates.extend(_dates_in_text(candidate_text))
        candidate_quarter = _quarter_from_text(candidate_text)
        if candidate_quarter is not None:
            ignored_dates.append(candidate_quarter)
    return period, source, confidence, current_dates, ignored_dates


def _comparison_period_dates(tokens: list[str]) -> list[date]:
    ignored: list[date] = []
    comparison_markers = ("전기실적", "전년동기실적")
    for index, token in enumerate(tokens):
        if not any(marker in _compact(token) for marker in comparison_markers):
            continue
        values: list[str] = []
        for candidate in tokens[index : index + 8]:
            if candidate != token and _compact(candidate) in _CURRENT_RESULT_ALIASES:
                break
            values.append(candidate)
        text = " ".join(values)
        ignored.extend(_dates_in_text(text))
        quarter = _quarter_from_text(text)
        if quarter is not None:
            ignored.append(quarter)
    return list(dict.fromkeys(ignored))


def _preliminary_metric(
    tokens: list[str], aliases: tuple[str, ...]
) -> tuple[float | None, float | None, float | None, float | None]:
    labels = {_compact(alias) for alias in aliases}
    index = next(
        (i for i, token in enumerate(tokens) if _compact(token) in labels),
        None,
    )
    if index is None:
        return None, None, None, None
    tail = tokens[index + 1 : index + 35]
    current_index = next(
        (
            i
            for i, token in enumerate(tail)
            if _compact(token) in _CURRENT_RESULT_ALIASES
        ),
        None,
    )
    if current_index is None:
        return None, None, None, None
    cumulative_index = next(
        (
            i
            for i, token in enumerate(tail[current_index + 1 :], current_index + 1)
            if _compact(token) in _CUMULATIVE_RESULT_ALIASES
        ),
        None,
    )
    current_cells = tail[current_index + 1 : cumulative_index]
    current = next(
        (number for token in current_cells if (number := _numeric_cell(token)) is not None),
        None,
    )
    qoq = None
    yoy = None
    cumulative = None
    if cumulative_index is not None:
        for token in tail[cumulative_index + 1 :]:
            cumulative = _numeric_cell(token)
            if cumulative is not None:
                break
    return current, cumulative, yoy, qoq


def _preliminary_raw_fields(
    tokens: list[str],
    aliases: tuple[str, ...],
    *,
    label: str,
    unit: str | None,
    source_receipt_no: str | None = None,
) -> list[dict[str, object]]:
    labels = {_compact(alias) for alias in aliases}
    index = next(
        (position for position, token in enumerate(tokens) if _compact(token) in labels),
        None,
    )
    if index is None:
        return []
    tail = tokens[index + 1 : index + 35]
    current_index = next(
        (
            position
            for position, token in enumerate(tail)
            if _compact(token) in _CURRENT_RESULT_ALIASES
        ),
        None,
    )
    if current_index is None:
        return []
    cumulative_index = next(
        (
            position
            for position, token in enumerate(tail[current_index + 1 :], current_index + 1)
            if _compact(token) in _CUMULATIVE_RESULT_ALIASES
        ),
        None,
    )
    current_cells = tail[current_index + 1 : cumulative_index]
    raw: list[dict[str, object]] = []
    headers = (
        "당기실적",
        "전기실적",
        "전기대비 증감률",
        "전년동기실적",
        "전년동기대비 증감률",
    )
    numeric_cells = [cell for cell in current_cells if _numeric_cell(cell) is not None]
    for header, cell in zip(headers, numeric_cells, strict=False):
        raw.append(
            {
                "raw_label": label,
                "raw_value": cell,
                "raw_unit": unit,
                "raw_period": "single_quarter",
                "raw_column_header": header,
                "source_receipt_no": source_receipt_no,
                "parse_method": "flat_token_fallback",
            }
        )
    if cumulative_index is not None:
        cumulative_cell = next(
            (
                cell
                for cell in tail[cumulative_index + 1 :]
                if _numeric_cell(cell) is not None
            ),
            None,
        )
        if cumulative_cell is not None:
            raw.append(
                {
                    "raw_label": label,
                    "raw_value": cumulative_cell,
                    "raw_unit": unit,
                    "raw_period": "year_to_date",
                    "raw_column_header": "당기누계실적",
                    "source_receipt_no": source_receipt_no,
                    "parse_method": "flat_token_fallback",
                }
            )
    return raw


def extract_preliminary_earnings_facts_from_text(
    text: str,
    *,
    source_receipt_no: str | None = None,
) -> PreliminaryEarningsFacts:
    plain_text = _strip_html(text) if "<table" in text.lower() else text
    tokens = _tokens(plain_text)
    scale = _preliminary_unit_scale(tokens)
    unit_label = _preliminary_unit_label(tokens)
    (
        period_end,
        reporting_period_source,
        reporting_period_confidence,
        document_period_candidates,
    ) = _preliminary_period_end(tokens)
    semantic, semantic_raw_fields, table_unit, diagnostics = (
        _semantic_preliminary_table(text, source_receipt_no)
        if "<table" in text.lower()
        else (
            {},
            [],
            None,
            {
                "parse_method": "flat_token_fallback",
                "semantic_table_found": False,
                "tables_scanned": 0,
                "header_index": None,
                "current_column": None,
                "qoq_column": None,
                "yoy_column": None,
                "unit": unit_label,
                "metric_labels_found": [],
            },
        )
    )
    if table_unit:
        unit_label = table_unit
        scale = _preliminary_unit_scale([f"단위: {table_unit}"])
    (
        semantic_period_end,
        semantic_period_source,
        semantic_period_confidence,
        current_period_candidates,
        ignored_comparison_dates,
    ) = _preliminary_period_end_from_semantic_header(diagnostics)
    if semantic_period_end is not None:
        period_end = semantic_period_end
        reporting_period_source = semantic_period_source
        reporting_period_confidence = semantic_period_confidence
    elif document_period_candidates:
        current_period_candidates = document_period_candidates
    ignored_comparison_dates = list(
        dict.fromkeys(
            [*ignored_comparison_dates, *_comparison_period_dates(tokens)]
        )
    )
    current_candidate_set = set(current_period_candidates)
    ignored_comparison_dates = [
        value for value in ignored_comparison_dates if value not in current_candidate_set
    ]
    headers = diagnostics.get("column_headers")
    current_column = diagnostics.get("current_column")
    diagnostics["current_result_header"] = (
        str(headers[current_column])
        if isinstance(headers, list)
        and isinstance(current_column, int)
        and current_column < len(headers)
        else None
    )
    diagnostics["reporting_period_source"] = reporting_period_source
    diagnostics["reporting_period_confidence"] = reporting_period_confidence
    diagnostics["reporting_period_end"] = (
        period_end.isoformat() if period_end is not None else None
    )
    diagnostics["current_period_date_candidates"] = [
        value.isoformat() for value in current_period_candidates
    ]
    diagnostics["document_period_date_candidates"] = [
        value.isoformat() for value in document_period_candidates
    ]
    diagnostics["ignored_comparison_period_dates"] = [
        value.isoformat() for value in ignored_comparison_dates
    ]

    def metric_values(label: str, aliases: tuple[str, ...]) -> tuple[float | None, float | None, float | None, float | None]:
        value = semantic.get(label)
        if value:
            return value["current"], value["cumulative"], value["yoy"], value["qoq"]
        if semantic:
            return None, None, None, None
        return _preliminary_metric(tokens, aliases)

    revenue, cumulative_revenue, revenue_yoy, revenue_qoq = metric_values(
        "매출액", _PRELIMINARY_METRIC_ALIASES["매출액"]
    )
    operating_income, cumulative_operating_income, _, _ = metric_values(
        "영업이익", _PRELIMINARY_METRIC_ALIASES["영업이익"]
    )
    net_income, cumulative_net_income, _, _ = metric_values(
        "당기순이익", _PRELIMINARY_METRIC_ALIASES["당기순이익"]
    )
    owners_income, cumulative_owners_income, _, _ = metric_values(
        "지배주주순이익", _PRELIMINARY_METRIC_ALIASES["지배주주순이익"]
    )
    raw_fields = semantic_raw_fields or [
        *_preliminary_raw_fields(
            tokens,
            ("매출액", "영업수익", "수익(매출액)"),
            label="매출액",
            unit=unit_label,
            source_receipt_no=source_receipt_no,
        ),
        *_preliminary_raw_fields(
            tokens,
            ("영업이익", "영업이익(손실)"),
            label="영업이익",
            unit=unit_label,
            source_receipt_no=source_receipt_no,
        ),
        *_preliminary_raw_fields(
            tokens,
            ("당기순이익", "분기순이익", "반기순이익"),
            label="당기순이익",
            unit=unit_label,
            source_receipt_no=source_receipt_no,
        ),
        *_preliminary_raw_fields(
            tokens,
            (
                "지배기업 소유주지분 순이익",
                "지배기업 소유주 귀속 당기순이익",
                "지배주주순이익",
            ),
            label="지배주주순이익",
            unit=unit_label,
            source_receipt_no=source_receipt_no,
        ),
    ]
    for field in raw_fields:
        field["reporting_period_source"] = reporting_period_source
        field["reporting_period_confidence"] = reporting_period_confidence
        field["selected_reporting_period_end"] = (
            period_end.isoformat() if period_end else None
        )
        field["current_period_date_candidates"] = diagnostics[
            "current_period_date_candidates"
        ]
        field["ignored_comparison_period_dates"] = diagnostics[
            "ignored_comparison_period_dates"
        ]
        field["current_result_header"] = diagnostics.get("current_result_header")
        field["selected_header_rows"] = diagnostics.get("header_rows") or []
    quarter = ((period_end.month - 1) // 3 + 1) if period_end else None
    period_label = f"{period_end.year}년 {quarter}분기" if period_end and quarter else "잠정실적"
    basis = (
        "잠정실적; fs_div=CFS; sj_div=IS; "
        f"thstrm_nm={period_label}; unit=KRW; period_scope=single-quarter; "
        "amount_scope=standalone_or_balance; report_code=preliminary"
    )
    facts: list[str] = []
    for label, current, cumulative in (
        ("매출액", revenue, cumulative_revenue),
        ("영업이익", operating_income, cumulative_operating_income),
        ("당기순이익", net_income, cumulative_net_income),
        ("지배주주순이익", owners_income, cumulative_owners_income),
    ):
        if current is not None:
            facts.append(
                f"OpenDART financial fact: {label} = {current * scale:.0f} KRW ({basis})"
            )
        if cumulative is not None:
            facts.append(
                f"OpenDART financial cumulative fact: {label} = {cumulative * scale:.0f} KRW "
                f"({basis.replace('amount_scope=standalone_or_balance', 'amount_scope=cumulative')})"
            )
    operating_margin = (
        operating_income / revenue * 100
        if revenue not in {None, 0} and operating_income is not None
        else None
    )
    return PreliminaryEarningsFacts(
        facts=facts,
        period_end=period_end,
        reporting_period_source=reporting_period_source,
        reporting_period_confidence=reporting_period_confidence,
        revenue=revenue * scale if revenue is not None else None,
        operating_income=operating_income * scale if operating_income is not None else None,
        net_income=net_income * scale if net_income is not None else None,
        owners_parent_net_income=owners_income * scale if owners_income is not None else None,
        operating_margin=operating_margin,
        yoy_growth=revenue_yoy,
        qoq_growth=revenue_qoq,
        unit_scale=scale,
        raw_fields=raw_fields,
        diagnostics=diagnostics,
    )


def _marker_lines(text: str) -> list[str]:
    markers = ("계약상대", "계약금액", "매출액대비", "계약기간", "판매ㆍ공급지역", "체결계약명")
    lines = [_clean_cell(line) for line in text.splitlines() if _clean_cell(line)]
    matched = [line for line in lines if any(marker in line for marker in markers)]
    return matched[:8]


def build_text_diagnostics(document: DartDocumentText | None) -> list[str]:
    if document is None:
        return ["DART text fallback: no document text fetched"]
    compact = document.text.replace(" ", "")
    markers = ["계약상대방", "계약금액", "매출액대비", "계약기간", "판매ㆍ공급계약", "단일판매"]
    found = [marker for marker in markers if marker.replace(" ", "") in compact]
    snippet = _clean_cell(document.text[:500])
    if document.viewer_params:
        params = document.viewer_params
        param_text = (
            f"ele_id={params.ele_id}, offset={params.offset}, "
            f"length={params.length}, dtd={params.dtd}"
        )
    else:
        param_text = "none"
    diagnostics = [
        f"DART text fallback: source={document.source}, dcm_no={document.dcm_no or 'none'}, length={len(document.text)}",
        f"DART text fallback params: {param_text}",
        f"DART text fallback: found_markers={','.join(found) if found else 'none'}",
        f"DART text fallback snippet: {snippet}",
    ]
    diagnostics.extend(f"DART text fallback marker line: {line}" for line in _marker_lines(document.text))
    return diagnostics


async def fetch_dart_document_text(client: httpx.AsyncClient, receipt_no: str) -> DartDocumentText | None:
    main_response = await client.get(
        "https://dart.fss.or.kr/dsaf001/main.do",
        params={"rcpNo": receipt_no},
    )
    main_response.raise_for_status()
    main_html = main_response.text
    viewer_params = _extract_viewer_params(main_html, receipt_no)
    dcm_no = viewer_params.dcm_no if viewer_params else _extract_dcm_no(main_html, receipt_no)
    if not dcm_no:
        text = _strip_html(main_html)
        return (
            DartDocumentText(text=text, dcm_no=None, source="main", html=main_html)
            if text.strip()
            else None
        )

    params = {
        "rcpNo": receipt_no,
        "dcmNo": dcm_no,
        "eleId": viewer_params.ele_id if viewer_params else "0",
        "offset": viewer_params.offset if viewer_params else "0",
        "length": viewer_params.length if viewer_params else "0",
        "dtd": viewer_params.dtd if viewer_params else "dart3.xsd",
    }
    viewer_response = await client.get("https://dart.fss.or.kr/report/viewer.do", params=params)
    viewer_response.raise_for_status()
    text = _strip_html(viewer_response.text)
    if text.strip():
        return DartDocumentText(
            text=text,
            dcm_no=dcm_no,
            source="viewer",
            viewer_params=viewer_params,
            html=viewer_response.text,
        )
    fallback_text = _strip_html(main_html)
    if fallback_text.strip():
        return DartDocumentText(
            text=fallback_text,
            dcm_no=dcm_no,
            source="main",
            viewer_params=viewer_params,
            html=main_html,
        )
    return None
