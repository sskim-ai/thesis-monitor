"""Read bounded business evidence from DART's locally irregular report XML."""
from __future__ import annotations

import bisect
import calendar
import html
import re
from datetime import date
from typing import NamedTuple

from app.services.dart_business_tables import project_table

# Only DART tags are interpreted. Plain comparisons, raw ampersands and Korean
# angle-bracket labels in prose do not alter the document hierarchy.
_TAG = re.compile(r"</?(?:P|SPAN|BR|SUP|SUB|B|U|I)(?=[\s/>])[^<>]*>", re.I)
_SECTION = re.compile(r"<(/?)SECTION-([12])(?=[\s>])[^<>]*>")
_TITLE = re.compile(r"\s*<TITLE(?:\s[^<>]*)?>(.*?)</TITLE>", re.S)
_NOTE = re.compile(r"<TITLE(?:\s[^<>]*)?>(.*?)</TITLE>", re.S)
_RELEVANT_NOTE = re.compile("영업부문|사업부문|부문별|고객과의계약|수주계약|영업수익|매출액|고객별")
_BLOCK = re.compile(r"<(P|TABLE)(?=[\s>])[^<>]*>|</(P|TABLE)>")
_ROW = re.compile(r"<TR(?=[\s>])[^<>]*>((?:(?!<TR(?=[\s>])).)*?)</TR>", re.S)
_CELL = re.compile(r"<(T[DHUE])(?=[\s>])([^<>]*)>(.*?)</\1>", re.S)
_ATTR = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_TOPICS = (
    ("one_off", r"일회[성적].{0,7}(수익|손익|비용|이익|손실|매출|요인)|기저효과"),
    ("structure", r"단일\s*영업부문|최고영업의사결정자"),
    ("productivity", r"가동률.{0,25}산[정출]|생산\s*가능시간|수율.{0,20}(개선|하락)"),
    ("order", r"수주잔고|수주잔액|순증감액|신규수주"),
    ("profitability", r"수익성|영업[이손]익|이익률|원가율|품목구성|제품\s*믹스"),
    ("capacity", r"증설|생산능력|설비투자|가동률"),
    ("development", r"임상.{0,20}(완료|진행|승인)|기술이전|판매허가"),
    ("competition", r"시장점유율|기술력|경쟁우위|진입장벽|경쟁력"),
    ("growth", r"물량|신규\s*고객|매출|영업수익|수수료수익|보험손익|전력판매|공사수익"),
    ("risk", r"환율\s*변동|원재료\s*가격|위험|지급여력"),
)
_TOPICS = [(key, re.compile(rx)) for key, rx in _TOPICS]
_OUTLOOK = re.compile(r"예상|계획|전망|예정|목표|기대|추진할|예측|하고자|가능할|것으로\s*(보|판단)|(?:할|될|갈|질)\s*것|\s*수\s*있|가능성|겠습니다|추진전략|추진하고|가정할")
_CAUSAL = re.compile(r"영향|기인|때문|에\s*따[라른]|힘입|에\s*따른|에\s*의해|원인|일회성|덕분|기여|반영")
_REPORTED = re.compile(r"증가|감소|개선|하락|성장|상승|확대|축소|개시|완료|체결|변동")
_LIMIT = re.compile(r"비공개|영업비밀|기재하지|보안관계|산출\s*중")
_NOTE_TEXT = re.compile(r"^(?:[※*]|주\s*\d{0,2}\s*[).:])|별도재무제표 기준|부가가치세|VAT|영업비밀|보안관계")


def plain(raw):
    return " ".join(html.unescape(_TAG.sub(" ", raw)).split())


class Cell(NamedTuple):
    text: str
    line: int
    tag: str
    context: str
    fact: str


def _cover(doc, corp_code, report_code):
    header = doc.partition("<BODY")[0]
    identity = re.findall(r'<COMPANY-NAME\b([^<>]*)>', header)
    form = re.findall(r'<DOCUMENT-NAME\b([^<>]*)>', header)
    forms = {"11011": ("11011", 12), "11012": ("11012", 6), "11013": ("11013", 3),
             "11014": ("11013", 9)}
    if (not re.fullmatch(r"\d{8}", corp_code) or len(identity) != 1 or
            dict(_ATTR.findall(identity[0])).get("AREGCIK") != corp_code or
            report_code not in forms or len(form) != 1 or
            dict(_ATTR.findall(form[0])).get("ACODE") != forms[report_code][0]):
        raise ValueError("dart_report_header_identity")
    cover = re.search(r"<COVER>(.*?)</COVER>", doc, re.S)
    if not cover:
        raise ValueError("dart_report_cover_missing")
    dates = {}
    for attrs in re.findall(r"<TU\s+([^<>]*)>", cover[1]):
        vals = dict(_ATTR.findall(attrs))
        key = vals.get("AUNIT")
        if key in ("PERIODFROM", "PERIODTO"):
            if key in dates or not re.fullmatch(r"\d{8}", vals.get("AUNITVALUE", "")):
                raise ValueError("dart_report_period_ambiguous")
            value = vals["AUNITVALUE"]
            dates[key] = date(int(value[:4]), int(value[4:6]), int(value[6:]))
    start, end = dates.get("PERIODFROM"), dates.get("PERIODTO")
    if (not start or not end or start.day != 1 or end.day != calendar.monthrange(end.year, end.month)[1]
            or (end.year - start.year) * 12 + end.month - start.month + 1 != forms[report_code][1]):
        raise ValueError("dart_report_period_mismatch")
    terms = set(re.findall(r"제\s*(\d+)\s*기", cover[1]))
    return start.isoformat(), end.isoformat(), next(iter(terms)) if len(terms) == 1 else None


def _areas(doc):
    chapter, sub, start = "", "", 0
    for cut in _SECTION.finditer(doc):
        if chapter and cut.start() > start:
            yield chapter, sub, start, cut.start()
        if not cut[1]:
            title = _TITLE.match(doc, cut.end())
            name = plain(title[1]) if title else ""
        else:
            name, title = "", None
        if cut[2] == "1":
            chapter, sub = name, ""
        else:
            sub = name
        start = title.end() if title is not None else cut.end()


def _blocks(doc, start, stop):
    # Report templates do not nest data TABLEs. Discard an unfinished table at
    # the next one rather than consuming rows from both into a synthetic grid.
    table = para = None
    for tag in _BLOCK.finditer(doc, start, stop):
        if tag[1] == "TABLE":
            table, para = tag.start(), None
        elif tag[2] == "TABLE" and table is not None:
            yield "table", table, tag.end()
            table = None
        elif table is None and tag[1] == "P":
            para = tag.end()
        elif table is None and tag[2] == "P" and para is not None:
            yield "text", para, tag.start()
            para = None


def _grid(raw, offset, lineno):
    rows, pending = [], {}
    for row_match in _ROW.finditer(raw):
        row = {c: cell for c, (left, cell) in pending.items()}
        pending = {c: (left - 1, cell) for c, (left, cell) in pending.items() if left > 1}
        col = 0
        body = row_match[1]
        cells = list(_CELL.finditer(body))
        if len(cells) != len(re.findall(r'<T[DHUE](?=[\s>])', body)):
            return []
        for match in cells:
            while col in row:
                col += 1
            attr = dict(_ATTR.findall(match[2]))
            rs, cs = attr.get("ROWSPAN", "1"), attr.get("COLSPAN", "1")
            if (not rs.isdecimal() or not cs.isdecimal() or len(rs) > 3 or len(cs) > 2
                    or not 1 <= int(rs) <= 200 or not 1 <= int(cs) <= 64 or col + int(cs) > 80):
                return []
            cell = Cell(plain(match[3]), lineno(offset + row_match.start(1) + match.start()),
                        match[1], attr.get("ACONTEXT", ""), attr.get("ACODE", ""))
            for c in range(col, col + int(cs)):
                if c in row:
                    return []
                row[c] = cell
                if int(rs) > 1:
                    pending[c] = (int(rs) - 1, cell)
            col += int(cs)
        if not row or set(row) != set(range(len(row))):
            return []
        rows.append([row[c] for c in range(len(row))])
    if (pending or not rows or len({len(row) for row in rows}) != 1
            or len(rows) != len(re.findall(r"<TR(?=[\s>])", raw))):
        return []
    return rows


# A report can switch from the parent to a named subsidiary mid-paragraph.
# Keep an explicit nearby heading and subject alongside its original sentence.
_SCOPE_MARKER = re.compile(r"\[[^\[\]\n]{1,64}\]")
_SOURCE_SUBJECT = re.compile(
    r"^(?:(?:당사(?:의)?\s*)?(?:주요\s*)?(?:종속(?:회사|기업)|자회사)(?:인)?\s*)?"
    r"((?:㈜|\(주\))?[^\W\d_][\w&·ㆍ]{1,28}?)(?:은|는)\s+")
_HEADING = re.compile(r"^[■●◆]\s*[^.]{1,100}$|^(?:[가-힣]\.\s*)[^.]{1,45}(?:부문|사업)$")


def source_heading(text):
    text = text.strip()
    if (_SCOPE_MARKER.fullmatch(text) or _HEADING.fullmatch(text)
            or re.fullmatch(r"\[[^]]{1,60}\]\s*(?:대상|해당)회사\s*[:：]\s*.{1,60}", text)):
        return text
    return ""


def _sentences(raw, heading=""):
    offset = 0
    named = ""
    for chunk in re.split(r"</?SPAN(?=[\s>])[^<>]*>|<BR\s*/?>|\n", raw, flags=re.I):
        pos = raw.find(chunk, offset) if chunk else offset
        offset = pos + len(chunk)
        content = plain(chunk)
        label = source_heading(content)
        if label:
            heading, named = label, ""
            continue
        for sentence in re.split(r"(?<=[다요음임됨함][.!?])\s*|(?<=[.!?])\s+(?!\d)", content):
            marker = _SCOPE_MARKER.match(sentence)
            if marker:
                heading, named = marker[0], ""
            lead = sentence[marker.end():] if marker else sentence
            explicit = _SOURCE_SUBJECT.match(lead)
            if explicit and (marker or explicit.start(1) or re.match(r"[A-Z㈜(]", explicit[1])):
                named = explicit[0].strip()[:-1]
            prefix = " ".join(s for s in (heading, named) if s and s not in sentence)
            if 18 <= len(sentence) <= 350 and len(prefix) + len(sentence) <= 347:
                yield sentence, pos, prefix


def _text_candidate(sentence, section, scope, line, prefix):
    matched = [topic for topic, rx in _TOPICS if rx.search(sentence)]
    if (not matched or re.search(r"(참조|참고)하시|다음과 같", sentence) and "structure" not in matched
            or not re.search(r"(다[.?!]?|함[.]?|음[.]?|되었습니다[.]?|입니다[.]?)$", sentence)):
        return None
    if re.search(r"재무적 성과에 영향을 미치는 잠재적 위험|위험관리의 목적|위험을 회피할 목적", sentence):
        return None
    topic = matched[0]
    classification = "COMPANY_REPORTED_OBSERVATION"
    if _OUTLOOK.search(sentence):
        classification = "MANAGEMENT_OUTLOOK_OR_ESTIMATE"
    elif _LIMIT.search(sentence):
        classification = "DISCLOSURE_LIMIT"
    elif _CAUSAL.search(sentence) or re.search(r"경쟁력|경쟁우위|산정|산출|평가합니다", sentence):
        classification = "MANAGEMENT_EXPLANATION"
    score = (10 + min(3, len(matched)) + 6 * bool(_REPORTED.search(sentence))
             + 6 * bool(_CAUSAL.search(sentence)) - 8 * (classification == "MANAGEMENT_OUTLOOK_OR_ESTIMATE")
             + 30 * (topic in ("one_off", "structure", "productivity"))
             + 14 * ("순증감액" in sentence) + 5 * bool(re.search(r"당사|당분기|당기|당반기|지난해|전년|당사의|기록|시현", sentence))
             + 5 * bool(re.search(r"인해|회복|증감|물량|전년|신규\s*(거래|계약|수주)", sentence))
             - 8 * bool(re.search(r"환경에 노출|파생상품|하는 산업|통계|국내총생산|한국경제", sentence)))
    return score, topic, dict(section=section, scope=scope, line=line, source_text=sentence,
                              classification=classification, excerpt=f"{prefix} — {sentence}" if prefix else sentence)


def _scoped(doc, chapter, sub, start, stop):
    if re.match(r"II\s*\.", chapter) and "사업" in chapter:
        yield sub or chapter, "business_section", start, stop
    elif re.match(r"III\s*\.", chapter) and "주석" in sub:
        scope = "consolidated" if "연결" in sub else "separate"
        title, begin = sub, start
        for note in _NOTE.finditer(doc, start, stop):
            if _RELEVANT_NOTE.search(title.replace(" ", "")):
                yield title, scope, begin, note.start()
            title, begin = plain(note[1]), note.end()
        if _RELEVANT_NOTE.search(title.replace(" ", "")):
            yield title, scope, begin, stop


def _notes(text):
    parts = [s for s in re.split(r"(?<=다\.)\s+|(?<=니다\.)", text) if _NOTE_TEXT.search(s.strip())]
    return [s.strip() for s in parts if 3 <= len(s.strip()) <= 220][:2]


def _select(candidates, limit):
    selected, seen = [], set()
    contracts = 0
    for score, key, obj in sorted(candidates, key=lambda x: -x[0]):
        if key in seen:
            continue
        if obj.get("classification") == "CONTRACT_TERMS":
            if contracts == 3:
                continue
            contracts += 1
        seen.add(key)
        selected.append(obj)
        if len(selected) == limit:
            break
    return selected


def parse_dart_business_report(xml: bytes, *, corp_code: str, report_code: str) -> dict:
    doc = xml.decode("utf-8-sig")
    if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", doc, re.I):
        raise ValueError("dart_report_doctype")
    start, end, term = _cover(doc, corp_code, report_code)
    newlines = [m.start() for m in re.finditer(r"\n", doc)]
    def lineno(pos):
        return bisect.bisect_left(newlines, pos) + 1
    texts, numbers, sections = [], [], []
    for chapter, sub, begin, stop in _areas(doc):
        if not re.match(r"I[IV]*\s*\.", chapter):
            continue
        if sub and ("주석" in sub or chapter.startswith("II.") or chapter.startswith("IV.")):
            sections.append(dict(chapter=chapter, title=sub, line=lineno(begin)))
        for section, scope, a, b in _scoped(doc, chapter, sub, begin, stop):
            previous = []
            blocks = list(_blocks(doc, a, b))
            for i, (kind, p, q) in enumerate(blocks):
                raw = doc[p:q]
                if kind == "text":
                    if not plain(raw):
                        continue
                    lead = source_heading(previous[-1]) if previous else ""
                    for sentence, rel, prefix in _sentences(raw, lead):
                        row = _text_candidate(sentence, section, scope, lineno(p + rel), prefix)
                        if row:
                            texts.append(row)
                    previous = (previous + [plain(raw)])[-2:]
                    continue
                rows = _grid(raw, p, lineno)
                if not rows:
                    previous = []
                    continue
                if scope != "business_section":
                    for row in rows:
                        for cell in dict.fromkeys(row):
                            if len(cell.text) < 35 or not cell.tag == "TE":
                                continue
                            for sentence, _, prefix in _sentences(cell.text):
                                candidate = _text_candidate(sentence, section, scope, cell.line, prefix)
                                if candidate:
                                    score, topic, obj = candidate
                                    texts.append((score + (5 if scope == "consolidated" else -4), topic, obj))
                head = " ".join(dict.fromkeys(cell.text for row in rows for cell in row)) if len(rows) <= 2 else ""
                if len(head) <= 220 and "단위" in head and not re.search(r"\d[,.]\d{3}", head):
                    previous.append(head)
                    continue
                notes = []
                for k, x, y in blocks[i+1:i+4]:
                    chunk = doc[x:y]
                    if k == "text":
                        content = plain(chunk)
                        if not content:
                            continue
                        notes = _notes(content)
                    elif len(chunk) < 6000:
                        content = " ".join(dict.fromkeys(c.text for r in _grid(chunk, x, lineno) for c in r))
                        notes = _notes(content)
                    break
                text_rows, numeric_rows = project_table(rows, section, scope, previous, notes, start, end, term,
                                                        next((s for s in reversed(previous) if source_heading(s)), ""))
                texts.extend(text_rows)
                numbers.extend(numeric_rows)
                previous = []
    if not sections:
        raise ValueError("dart_report_sections_missing")
    return dict(period_start=start, period_end=end, sections=sections,
                texts=_select(texts, 8), numbers=_select(numbers, 12))
