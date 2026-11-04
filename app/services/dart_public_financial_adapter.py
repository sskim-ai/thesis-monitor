"""Opt-in DART HTML diagnostics feeding unchanged financial quality denials.

This is not an OpenDART capture issuer or an economic-use owner. Public index
binding and explicit table observations remain separate from source admission.
"""
from datetime import date, datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from urllib.parse import parse_qs, urlparse

from app.models.financial import FinancialSnapshot
from app.services.sec_foreign_comparison_service import (
    StatementTables, amount, clean, grid, period_from_headers,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = "dart-public-html-financial-candidate-v1"
SOURCE = "DART_OFFICIAL_PUBLIC_HTML"
_FIELDS = {"매출액": "revenue", "수익(매출액)": "revenue", "영업이익": "operating_income"}
_VIEWER_KEYS = {"rcpNo", "dcmNo", "eleId", "offset", "length", "dtd", "tocNo"}
_NUMBER = r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?"


class _DartTables(StatementTables):
    """Require explicit table structure before the shared parser builds cells."""
    parents = {"table": {None}, "thead": {"table"}, "tbody": {"table"},
        "tfoot": {"table"}, "colgroup": {"table"}, "caption": {"table"},
        "tr": {"table", "thead", "tbody", "tfoot"}, "td": {"tr"}, "th": {"tr"}}

    def __init__(self):
        super().__init__()
        self.structure = []

    def handle_starttag(self, tag, attrs):
        if tag in self.parents:
            parent = self.structure[-1] if self.structure else None
            if parent not in self.parents[tag] or len(dict(attrs)) != len(attrs):
                raise ValueError("DART_TABLE_SHAPE_AMBIGUOUS")
            self.structure.append(tag)
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.parents:
            if not self.structure or self.structure.pop() != tag:
                raise ValueError("DART_TABLE_SHAPE_AMBIGUOUS")
        super().handle_endtag(tag)


def _query(url, path):
    p = urlparse(url)
    if (p.scheme != "https" or p.hostname != "dart.fss.or.kr" or p.path != path
            or p.username or p.password or p.port or p.fragment):
        raise ValueError("DART_OFFICIAL_ORIGIN_REQUIRED")
    q = parse_qs(p.query, keep_blank_values=True)
    if any(len(v) != 1 for v in q.values()):
        raise ValueError("DART_QUERY_AMBIGUOUS")
    return {k: v[0] for k, v in q.items()}


def _received(raw, receipt, url):
    """Integrity of a pre-admitted public receipt, not a new capture authority."""
    redirect_fields = {"redirects", "no_redirect"} & receipt.keys()
    no_redirect = bool(redirect_fields) and all(
        receipt[k] is (k == "no_redirect") for k in redirect_fields)
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= 2 * 1024**2
            or receipt.get("method") != "GET" or receipt.get("url") != url
            or receipt.get("exit") != 0 or not no_redirect
            or receipt.get("credentials") is not False or receipt.get("proxy") is not False
            or receipt.get("status_lines") != ["HTTP/1.1 200 OK"]
            or receipt.get("body") != {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}):
        raise ValueError("DART_PUBLIC_RECEIPT_MISMATCH")
    return raw.decode("utf-8", errors="strict")


class _Index(HTMLParser):
    def __init__(self):
        super().__init__()
        self.corp_codes, self.selected, self.pdf, self.scripts = [], [], [], []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self.in_script = True
        call = a.get("onclick", "")
        corp = re.fullmatch(r"openCorpInfoNew\('([0-9]{8})',\s*'winCorpInfo',\s*'/dsae001/selectPopup.ax'\);?", call)
        if tag == "span" and corp:
            self.corp_codes.append(corp[1])
        pdf = re.fullmatch(r"openPdfDownload\('([0-9]{14})',\s*'([0-9]+)'\);?", call)
        if tag == "button" and pdf:
            self.pdf.append((pdf[1], pdf[2]))
        if tag == "option" and "selected" in a:
            self.selected.append(a.get("value"))

    def handle_data(self, value):
        if self.in_script:
            self.scripts.append(value)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False


def bind_public_index(*, index_raw, index_receipt, section_raw, section_receipt,
                      corp_code, source_generation, index_generation):
    iq = _query(index_receipt["url"], "/dsaf001/main.do")
    sq = _query(section_receipt["url"], "/report/viewer.do")
    if (set(iq) != {"rcpNo"} or set(sq) != _VIEWER_KEYS or iq["rcpNo"] != sq["rcpNo"]
            or not re.fullmatch(r"[0-9]{14}", sq["rcpNo"])
            or any(not sq[k].isdigit() for k in ("dcmNo", "eleId", "offset", "length", "tocNo"))
            or sq["dtd"] != "dart4.xsd" or not source_generation or not index_generation):
        raise ValueError("DART_FILING_SECTION_LOCATOR_MISMATCH")
    index_text = _received(index_raw, index_receipt, index_receipt["url"])
    _received(section_raw, section_receipt, section_receipt["url"])
    node = index_section_membership(index_text, sq, corp_code)
    return dict(contract=CONTRACT, source_kind=SOURCE, corp_code=corp_code,
        filing_id=sq["rcpNo"], document_id=sq["dcmNo"], section=sq["eleId"],
        section_title=node.get("text"), source_url=section_receipt["url"],
        raw_sha256=sha256(section_raw).hexdigest(), index_sha256=sha256(index_raw).hexdigest(),
        source_generation=source_generation, index_generation=index_generation,
        receipt_sha256=digest(section_receipt), index_receipt_sha256=digest(index_receipt),
        binding_scope="PUBLIC_DOCUMENT_ISSUER_LOCATOR_ONLY",
        financial_owner=False, economic_use=False)


def index_section_membership(index_text, sq, corp_code):
    """Literal index membership only; the calling owner must verify custody."""
    index = _Index()
    index.feed(index_text)
    if (not re.fullmatch(r"[0-9]{8}", corp_code) or int(corp_code) == 0
            or index.corp_codes != [corp_code]
            or "rcpNo=" + sq["rcpNo"] not in index.selected
            or index.pdf != [(sq["rcpNo"], sq["dcmNo"])]):
        raise ValueError("DART_ISSUER_FILING_BINDING_PENDING")
    # Parse only DART's literal tree records. Never execute document scripts.
    matches = []
    script = "\n".join(index.scripts)
    for block in re.split(r"\bvar node[0-9]+ = \{\};", script)[1:]:
        pairs = re.findall(r"""node[0-9]+\['([A-Za-z0-9]+)'\]\s*=\s*("(?:[^"\\]|\\.)*")\s*;""", block)
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError("DART_INDEX_NODE_AMBIGUOUS")
            values[key] = json.loads(value)
        if values.get("eleId") == sq["eleId"]:
            matches.append(values)
    if len(matches) != 1 or any(matches[0].get(k) != v for k, v in sq.items()):
        raise ValueError("DART_INDEX_SECTION_MEMBERSHIP_MISMATCH")
    return matches[0]


def field_candidates(*, index_raw, index_receipt, section_raw, section_receipt,
                     corp_code, source_generation, index_generation, cutoff):
    binding = bind_public_index(index_raw=index_raw, index_receipt=index_receipt,
        section_raw=section_raw, section_receipt=section_receipt, corp_code=corp_code,
        source_generation=source_generation, index_generation=index_generation)
    parser = _DartTables()
    parser.feed(section_raw.decode("utf-8"))
    parser.close()
    if (len(parser.tables) != 2 or parser.structure or parser.stack or parser.cell is not None or parser.row is not None
            or any(t["nested"] for t in parser.tables)):
        raise ValueError("DART_TABLE_SHAPE_AMBIGUOUS")
    header, data = [grid(t) for t in parser.tables]
    if (len(header) != 4 or any(len(r) != 1 or not r[0] for r in header)
            or header[0][0]["text"] != "연결 포괄손익계산서"
            or not str(binding["section_title"]).endswith("연결 포괄손익계산서")):
        raise ValueError("DART_CFS_STATEMENT_BOUNDARY_UNQUALIFIED")
    periods, labels = [], []
    for row in header[1:3]:
        text = row[0]["text"]
        m = re.fullmatch(r"(제\s*[0-9]+\s*기\s*반기)\s+(20[0-9]{2}\.[0-9]{2}\.[0-9]{2})\s+부터\s+(20[0-9]{2}\.[0-9]{2}\.[0-9]{2})\s+까지", text)
        if not m:
            raise ValueError("DART_EXPLICIT_PERIOD_HEADER_REQUIRED")
        # This conversion preserves literal dates; it does not infer QTD dates.
        p = period_from_headers([m[2].replace(".", "-") + " to " + m[3].replace(".", "-")])
        if p["period_scope"] != "half-year":
            raise ValueError("DART_HALF_YEAR_HEADER_REQUIRED")
        periods.append(p)
        labels.append(re.sub(r"\s", "", m[1]))
    current, prior = periods
    filed = datetime.strptime(binding["filing_id"][:8], "%Y%m%d").date()
    a, b = date.fromisoformat(current["period_start"]), date.fromisoformat(prior["period_start"])
    ae, be = date.fromisoformat(current["period_end"]), date.fromisoformat(prior["period_end"])
    if (a.year != b.year + 1 or (a.month, a.day, ae.month, ae.day) != (b.month, b.day, be.month, be.day)
            or not ae <= filed <= cutoff):
        raise ValueError("DART_PERIOD_OR_AVAILABILITY_MISMATCH")
    if clean(header[3][0]["text"]) not in {"(단위 : 백만원)", "(단위: 백만원)"}:
        raise ValueError("DART_UNIT_UNQUALIFIED")
    if (len(data) < 3 or any(len(r) != 5 or any(c is None for c in r) for r in data)
            or [re.sub(r"\s", "", c["text"]) for c in data[0][1:]] != [labels[0]] * 2 + [labels[1]] * 2
            or [c["text"] for c in data[1][1:]] != ["3개월", "누적"] * 2):
        raise ValueError("DART_COLUMN_PERIOD_AMBIGUOUS")
    found, occurrences = set(), []
    for ri, row in enumerate(data[2:], 2):
        label = re.sub(r"\s*\(주[0-9, ]+\)\s*$", "", row[0]["text"]).strip()
        metric = _FIELDS.get(label)
        if not metric:
            continue
        if metric in found or any(c["colspan"] != 1 or c["rowspan"] != 1 for c in row):
            raise ValueError("DART_FIELD_DUPLICATE_OR_MERGED")
        found.add(metric)
        for ci, cell in enumerate(row[1:], 1):
            if not re.fullmatch(rf"(?:-?{_NUMBER}|\({_NUMBER}\))", cell["text"]):
                raise ValueError("DART_AMOUNT_UNQUALIFIED")
            value = amount(cell["text"])
            if value is None:
                raise ValueError("DART_AMOUNT_UNQUALIFIED")
            role = "current" if ci <= 2 else "comparison"
            ytd = ci in {2, 4}
            period = periods[0 if role == "current" else 1]
            occurrences.append(dict(provider="dart_public_html", source_kind=SOURCE,
                corp_code=corp_code, filing_id=binding["filing_id"], document_id=binding["document_id"],
                section=binding["section"], source_sha256=binding["raw_sha256"],
                table=1, row=ri, column=ci, metric=metric, field_label=row[0]["text"],
                account_id=None, statement_basis="CFS", fiscal_report_type="half_year",
                period_start=period["period_start"] if ytd else None,
                period_end=period["period_end"] if ytd else None,
                period_role="YTD" if ytd else "QTD", comparison_role=role,
                source_reported_unit="백만원", normalized_currency="KRW", unit_scale=1000000,
                amount_raw=cell["text"], amount_normalized=str(value * 1000000),
                period_context_source=dict(table=0, row=1 if role == "current" else 2,
                    raw_text=header[1 if role == "current" else 2][0]["text"]),
                period_status="EXPLICIT_YTD_HEADER" if ytd else "FIELD_PERIOD_NOT_ORIGIN_QUALIFIED",
                eligibility="DIAGNOSTIC_ONLY", source_use=[], economic_direction=False))
    if found != {"revenue", "operating_income"}:
        raise ValueError("DART_REQUIRED_LABEL_MISSING")
    return dict(contract=CONTRACT, binding=binding, cutoff=cutoff.isoformat(),
        statement_periods=periods, occurrences=occurrences,
        financial_owner=False, source_use=[], production_dispatch_enabled=False,
        hard_denials=["ORIGINAL_OPENDART_RECEIPT_UNAVAILABLE",
            "DART_HTML_FIELD_OWNER_NOT_IMPLEMENTED", "FIELD_PERIOD_NOT_ORIGIN_QUALIFIED"])


def original_quality_diagnostic(candidate, *, ticker):
    """Execute the real original quality/comparison gate without fake API rows."""
    from app.services.bounded_financial_stock_owner import reported_comparisons
    from scripts.m12dr_financial_source_authority import source_quality

    if candidate.get("contract") != CONTRACT or candidate["binding"]["source_kind"] != SOURCE:
        raise ValueError("DART_HTML_CANDIDATE_TYPE_REQUIRED")
    binding = candidate["binding"]
    filed = datetime.strptime(binding["filing_id"][:8], "%Y%m%d").date()
    formal = FinancialSnapshot(ticker=ticker, period="HTML_DIAGNOSTIC",
        source="DART_OFFICIAL_PUBLIC_HTML", provider="dart_public_html",
        source_filing_id=binding["filing_id"], filing_date=filed,
        financial_period_end=date.fromisoformat(candidate["statement_periods"][0]["period_end"]),
        currency="KRW", unit_scale=1, fs_div="CFS", snapshot_type="html_candidate",
        raw_financial_fields=json.dumps(candidate["occurrences"], ensure_ascii=False),
        created_at=datetime.combine(filed, datetime.min.time(), timezone.utc))
    inputs = dict(formal=formal.model_dump(mode="json"), preliminary=None,
        ticker=ticker, cutoff=candidate["cutoff"])
    bundle = dict(source_inputs=inputs, source_inputs_sha256=digest(inputs))
    quality = source_quality(bundle)
    bundle["quality"] = quality
    facts, denied = reported_comparisons(
        dict(market="kr", issuer=binding["corp_code"], ticker=ticker),
        dict(quality_bundles=[bundle]))
    if quality["status"] != "FAIL" or facts:
        raise ValueError("UNREVIEWED_HTML_FINANCIAL_OWNER_CHANGE")
    return dict(candidate_sha256=digest(candidate), quality=quality, facts=facts,
        comparison_denials=denied, status="ORIGINAL_OWNER_DENIED_UNADAPTED_HTML",
        source_use=[], accepted_financial_owner=False)
