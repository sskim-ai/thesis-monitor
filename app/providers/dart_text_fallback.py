from dataclasses import dataclass
from html import unescape
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


def _parse_js_args(args: str) -> list[str]:
    return [part.strip().strip("'\"") for part in re.split(r"\s*,\s*", args) if part.strip()]


def _extract_viewer_params(html: str, receipt_no: str) -> DartViewerParams | None:
    for match in re.finditer(r"viewDoc\(([^)]*)\)", html):
        args = _parse_js_args(match.group(1))
        if len(args) < 6:
            continue
        if args[0] != receipt_no:
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


def _row_value(text: str, labels: tuple[str, ...]) -> str | None:
    lines = [_clean_cell(line) for line in text.splitlines() if _clean_cell(line)]
    for line in lines:
        compact = line.replace(" ", "")
        for label in labels:
            label_compact = label.replace(" ", "")
            if label_compact not in compact:
                continue
            parts = [_clean_cell(part) for part in line.split("|") if _clean_cell(part)]
            for index, part in enumerate(parts):
                if label_compact in part.replace(" ", ""):
                    if index + 1 < len(parts):
                        return parts[index + 1]
                    tail = part.split(label, 1)[-1]
                    if _clean_cell(tail):
                        return _clean_cell(tail)
            return line
    return None


def extract_supply_contract_facts_from_text(text: str) -> list[str]:
    fields = [
        ("contract_name", ("계약명", "판매ㆍ공급계약 내용", "판매·공급계약 내용", "계약내용")),
        ("counterparty", ("계약상대방", "계약상대", "상대방")),
        ("amount", ("계약금액", "계약 금액")),
        ("recent_sales_ratio", ("매출액대비", "최근매출액 대비", "최근 매출액 대비")),
        ("period", ("계약기간", "계약 기간")),
        ("start_date", ("시작일", "계약시작일")),
        ("end_date", ("종료일", "계약종료일")),
        ("region", ("판매ㆍ공급지역", "판매·공급지역", "공급지역")),
    ]
    facts: list[str] = []
    for key, labels in fields:
        value = _row_value(text, labels)
        if value:
            facts.append(f"DART text supply contract fact: {key} = {value}")
    return facts


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
    return [
        f"DART text fallback: source={document.source}, dcm_no={document.dcm_no or 'none'}, length={len(document.text)}",
        f"DART text fallback params: {param_text}",
        f"DART text fallback: found_markers={','.join(found) if found else 'none'}",
        f"DART text fallback snippet: {snippet}",
    ]


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
        return DartDocumentText(text=text, dcm_no=None, source="main") if text.strip() else None

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
        return DartDocumentText(text=text, dcm_no=dcm_no, source="viewer", viewer_params=viewer_params)
    fallback_text = _strip_html(main_html)
    if fallback_text.strip():
        return DartDocumentText(text=fallback_text, dcm_no=dcm_no, source="main", viewer_params=viewer_params)
    return None
