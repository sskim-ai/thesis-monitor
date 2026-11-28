"""Project only report cells with identifiable dimensions, period and unit."""
from __future__ import annotations

import re
from datetime import date

_AMOUNT = re.compile(r"[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_SCALE = {"조원": 10**12, "억원": 10**8, "백만원": 10**6, "천원": 1000, "원": 1,
          "백만달러": 10**6, "천달러": 1000, "달러": 1, "USD": 1}
_MONEY = "|".join(_SCALE)
_HEADER_WORDS = re.compile(r"구분|품목|영업부문|사업부문|해당회사|제\d+기|당분기|기초|사업$")
_DATE = re.compile(r"(20\d\d)[.년/-]\s*(\d{1,2})[.월/-]\s*(\d{1,2})\s*일?")
_ORDER_METRICS = (("이월수주잔액", "opening_backlog"), ("당기수주금액", "new_orders"),
                  ("순증감액", "net_order_change"), ("수주잔고", "closing_backlog"))
_SUBJECT_HEADERS = {"구분", "사업", "품목", "제품", "사업부문", "부문", "해당회사", "계열사명", "회사명", "서비스"}
_PRODUCT = {"생산능력": "production_capacity", "생산실적": "production_output", "가동률": "utilization_rate"}


def compact(text):
    return re.sub(r"\s+", "", text)


def _numeric(raw):
    value = compact(raw).replace("−", "-")
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    if not _AMOUNT.fullmatch(value):
        return None
    digits = value.replace(",", "")
    if len(digits) > 16:
        return None
    return float(digits) if "." in digits else int(digits)


def _unit(label):
    clean = compact(label)
    match = re.search(r"단위[:：]([^\)）]+)", clean)
    if not match:
        return None
    items = re.findall(_MONEY, match[1])
    # Do not silently select KRW from a multi-currency or mixed-quantity table.
    residual = re.sub(_MONEY + r"|[%％,·/]", "", match[1])
    if len(items) == 1 and not residual:
        u = items[0]
        return ("USD" if "달러" in u or u == "USD" else "KRW", _SCALE[u])
    if match[1].strip(" ,") == "배치":
        return ("배치", 1)
    return None


def _current(header, term, start, end):
    h = compact(header)
    if re.search(r"전기|전분기|전년|전반기|예상|계획|추정|전망|목표", h):
        return False
    years = set(re.findall(r"(20\d\d)(?:년|\.)", h))
    terms = set(re.findall(r"제(\d+)기", h))
    if (terms and terms != {term}) or (years and years != {end[:4]}):
        return False
    months = (int(end[:4]) - int(start[:4])) * 12 + int(end[5:7]) - int(start[5:7]) + 1
    quarters = {int(q) for q in re.findall(r"([1-4])분기", h)}
    if quarters and quarters != {months // 3}:
        return False
    return bool(terms or years or re.search("당분기|당반기|당기", h))


def _date_values(text):
    result = set()
    for y, m, d in _DATE.findall(text):
        try:
            result.add(date(int(y), int(m), int(d)).isoformat())
        except ValueError:
            return {"invalid"}
    return result


def _role(header, context, start, end, annual_neighbors):
    h = compact(header)
    months = (int(end[:4])-int(start[:4]))*12 + int(end[5:7])-int(start[5:7])+1
    dates = _date_values(h)
    if dates and (end not in dates or not dates.issubset({start, end})):
        return None
    if "누적" in h or (not re.search(r"3개월|당분기(?!누적)", h) and "누적" in context):
        return "report_to_date", start, end
    if "3개월" in h or months == 3:
        last = date.fromisoformat(end)
        q = (last.year*12 + last.month-1) - 2
        return "single_quarter", date(q//12, q%12+1, 1).isoformat(), end
    if dates == {start, end}:
        return "report_to_date", start, end
    if months == 12 and not re.search(r"분기|반기", h):
        return "full_year", start, end
    if annual_neighbors and re.search(r"[1-4]분기|반기", h):
        return "report_to_date", start, end
    return None


def _header_rows(rows):
    n = 0
    while n < len(rows) and all(c.tag == "TH" for c in rows[n]):
        n += 1
    if n:
        return n
    first = [compact(c.text) for c in rows[0]]
    if not any(_HEADER_WORDS.fullmatch(s) for s in first):
        return 0
    merged = len(set(rows[0])) < len(rows[0])
    if merged and len(rows) > 1 and any(compact(c.text) in ("금액", "수량", "비중") for c in rows[1]):
        return 2
    return 1


def _number(metric, subject, value, units, raw_unit, period, cell, header, row_header,
            section, scope, notes):
    return dict(metric=metric, subject=subject, value=value, unit=units[0], unit_scale=units[1],
                unit_label=raw_unit, period_role=period[0], period_start=period[1], period_end=period[2],
                row_header=row_header, column_header=header, line=cell.line, section=section,
                scope=scope, notes=notes, classification="REPORTED_TABLE_VALUE",
                source_text=f"{row_header} | {header} | {cell.text}")


def _contracts(rows, section, scope, prior, end):
    if len(rows[0]) != 2:
        return [], []
    fields = {compact(r[0].text): r[1] for r in rows}
    if (len(fields) != len(rows) or "계약내용" not in fields or
            not ("계약상대방" in fields and ("총계약금액" in fields or "총계약금" in fields))):
        return [], []
    title = next((p for p in reversed(prior) if re.search(r"(품목|계약명)\s*[:：]", p) and len(p) <= 100), "")
    if not title:
        return [], []
    subject = re.split(r"(?:품목|계약명)\s*[:：]", title)[-1].strip()
    numeric = []
    for labels, metric in [(("총계약금액", "총계약금"), "contract_stated_total"),
                           (("지급금액",), "contract_payments_made"),
                           (("수취금액", "수령금액"), "contract_payments_received")]:
        key = next((k for k in labels if k in fields), None)
        if not key:
            continue
        cell = fields[key]
        v = compact(cell.text)
        if metric == "contract_stated_total":
            m = re.fullmatch(r"(" + _AMOUNT.pattern + r")(" + _MONEY + r")", v)
        else:
            if re.search(r"예정|조건부|예상|계획|가능|한도", v):
                continue
            total = r"(?:누적|합계|총)(" + _AMOUNT.pattern + r")(" + _MONEY + r")"
            totals = list(re.finditer(total, v))
            if len(totals) != 1 or totals[0].end() != len(v) or re.search(r"\[[^]]+\]", v):
                continue
            m = totals[0]
        if m:
            u = _unit("단위:" + m[2])
            value = _numeric(m[1])
            if u is not None and value is not None:
                obj = _number(metric, subject, value, u, m[2], ("point_in_time", end, end),
                              cell, key, subject, section, scope, [])
                numeric.append(obj)
    texts = []
    context = [f"{k}: {fields[k].text}" for k in ("계약상대방", "계약내용", "개발진행경과", "계약조건") if k in fields]
    excerpt = subject + " — " + " / ".join(context)
    if len(excerpt) <= 350:
        texts.append((52 + len(numeric)*12 + 4*bool(re.search(r"임상\s*[1-4]상", excerpt)), ("contract_terms", subject), dict(section=section, scope=scope,
                      line=fields["계약내용"].line, classification="CONTRACT_TERMS", excerpt=excerpt, source_text=excerpt)))
    return texts, [(52 + len(numeric)*12, (r["metric"], subject, scope), r) for r in numeric]


def project_table(rows, section, scope, prior, notes, start, end, term, owner_heading):
    texts, numbers = _contracts(rows, section, scope, prior, end)
    n = _header_rows(rows)
    if not 0 < n < len(rows):
        return texts, numbers
    headers = [" / ".join(dict.fromkeys(r[c].text for r in rows[:n] if r[c].text))
               for c in range(len(rows[0]))]
    h = [compact(v) for v in headers]
    local = compact(" ".join(prior))
    caption = next((s for s in reversed(prior) if "단위" not in s), "")
    if re.search(r"예상|계획|전망|목표|추정", caption) and len(caption) <= 110:
        return texts, numbers
    labels = [s for s in prior if "단위" in s and len(s) <= 220]
    raw_unit = labels[-1] if len(labels) == 1 else ""
    units = _unit(raw_unit)
    if scope == "business_section":
        basis = " ".join([*prior, *headers[:2], *notes])
        separate = re.search(r"별도(재무제표)?\s*기준|지배회사의 내용", basis)
        consolidated = re.search(r"연결\s*(매출|기준)|^연결$|(?:^|\s)연결\s*/", basis)
        if bool(separate) != bool(consolidated):
            scope = "separate" if separate else "consolidated"
    dates = _date_values(raw_unit)
    order_headers = any(re.search("수주잔고|이월수주잔액", s) for s in h)
    described_order = "수주잔고" in local and "기말잔고" in local
    first_col = {compact(row[0].text) for row in rows[n:]}
    revenue = (bool(re.search(r"(?:부문별|사업별|제품별|서비스별|품목별).{0,12}매출|매출.{0,5}세부내역", local))
               or ("서비스별영업현황" in local and "영업수익" in first_col))
    annual_neighbors = any(re.fullmatch(r"(?:20\d\d년도?\(?)?제\d+기\)?(?:/금액)?", s)
                           for s in h if not _current(s, term, start, end))
    for row in rows[n:]:
        row_label = row[0].text.strip("- ").strip()
        if not row_label or len(row_label) > 80 or re.search("합계|소계|총계", compact(row_label)):
            continue
        for c, cell in enumerate(row):
            header = h[c]
            raw = compact(cell.text)
            current = _current(header, term, start, end)
            if current and re.fullmatch(r"산출중|산정중|미확정|비공개", raw):
                text = f"{row_label} ({headers[c]}): {cell.text}"
                texts.append((72 + int("비율" in row_label), "pending", dict(section=section, scope=scope,
                              line=cell.line, classification="DISCLOSURE_LIMIT", excerpt=text, source_text=text)))
                continue
            val = _numeric(raw.rstrip("%％"))
            if val is None or cell in row[:c]:
                continue
            metric, subject, cell_unit, period, score = None, row_label, units, None, 0
            if scope in ("consolidated", "separate") and cell.context and units and units[0] in ("KRW","USD"):
                # Notes with only "당분기" may denote either 3 or 9 months.
                # Use the selected cell's explicit XBRL current duration context.
                current_basis = re.match(r"CFY(\d{4})dTQ([AQ])_", cell.context)
                dim = "_ConsolidatedMember_" if scope == "consolidated" else "_SeparateMember_"
                if (not current_basis or current_basis[1] != end[:4] or dim not in cell.context
                        or "보고부문" not in header or "전분기" in local or "전기" in local):
                    continue
                if cell.fact == "ifrs-full_Revenue" and compact(row_label) in ("매출액","수익","영업수익"):
                    metric = "business_revenue"
                elif cell.fact == "dart_OperatingIncomeLoss" and compact(row_label) in ("영업이익","영업손익","영업이익(손실)"):
                    metric = "business_operating_profit"
                else:
                    continue
                trace = headers[c].split(" / ")
                after = trace[trace.index("보고부문") + 1:] if "보고부문" in trace else []
                dims = [s for s in after if s not in ("3개월","누적")]
                if len(dims) != 1 or re.search(r"합계|조정|제거", dims[0]):
                    continue
                subject = dims[0]
                accumulated = current_basis[2] == "A"
                if ("누적" in trace and not accumulated) or ("3개월" in trace and accumulated):
                    continue
                period = _role("누적" if accumulated else "3개월", "", start, end, False)
                score = 54 + 2*accumulated + 1*(metric=="business_operating_profit") - 10*(scope=="separate")
            elif order_headers or described_order:
                if not units or units[0] not in ("KRW", "USD") or "금액" not in header or "수량" in header:
                    continue
                metric = next((m for token, m in _ORDER_METRICS if token in header), None)
                if "기납품액" in header and "금액" in header:
                    # This heading can also be lifetime deliveries. Admit the
                    # period flow only in an explicitly reconciled rollforward.
                    flows = {}
                    for j, dim in enumerate(h):
                        for label in ("이월수주잔액", "당기수주금액", "수주잔고"):
                            if label in dim and "금액" in dim and "수량" not in dim:
                                flows[label] = _numeric(row[j].text)
                    if len(flows) == 3 and all(v is not None for v in flows.values()):
                        if flows["이월수주잔액"] + flows["당기수주금액"] - val == flows["수주잔고"]:
                            metric = "delivered_orders"
                if described_order and not metric:
                    metric = "closing_backlog" if "기말" in header else "opening_backlog" if "기초" in header else None
                if not metric:
                    continue
                local_date = _date_values(header)
                anchor = start if metric == "opening_backlog" else end
                if (local_date and local_date != {anchor}) or (dates and dates != {end}) or not (local_date or dates):
                    continue
                if metric in ("opening_backlog", "closing_backlog"):
                    period = ("point_in_time", anchor, anchor)
                else:
                    period = ("report_to_date", start, end)
                parts = [r.text for j,r in enumerate(row) if h[j] in _SUBJECT_HEADERS and r.text
                         and "참조" not in r.text and len(r.text) <= 90]
                if not parts:
                    continue
                subject = " / ".join(dict.fromkeys(parts))
                if owner_heading and owner_heading not in subject:
                    subject = owner_heading + " / " + subject
                # Retain different economic roles for each disclosed entity before
                # selecting a long list containing only closing balances.
                score = 48 + 2*(scope == "separate")
            elif current:
                period = _role(header, local, start, end, annual_neighbors)
                if not period:
                    continue
                if compact(row_label) in _PRODUCT:
                    metric = _PRODUCT[compact(row_label)]
                    if metric == "utilization_rate":
                        if not raw.endswith(("%","％")):
                            continue
                        cell_unit = ("pct", 1)
                    elif not units or units[0] != "배치":
                        continue
                    score = 60
                elif revenue and row_label not in ("영업수익", "매출", "매출액"):
                    # In a multi-dimensional product/geography table, row[0]
                    # alone would misattribute domestic/export detail to a segment.
                    if any(not re.search(r"제\d+기|20\d\d년|당분기|당기", hdr) for hdr in h[1:c]):
                        continue
                    if "비중" in header and (re.search("[%％]", header + raw_unit + raw)):
                        metric, cell_unit = "business_revenue_share", ("pct", 1)
                    elif "금액" in header and units and units[0] in ("KRW","USD") and not raw.endswith(("%","％")):
                        metric = "business_revenue"
                    score = 54 + 4 * bool("누적" in local)
            if not metric or not period or not cell_unit or len(subject) > 140:
                continue
            if cell_unit[0] != "pct" and raw.endswith(("%","％")):
                continue
            if metric.endswith("_share") and not 0 <= val <= 100:
                continue
            extra = notes.copy()
            if metric in _PRODUCT.values():
                extra = [s for s in prior if "가동률" in s and len(s)<=220][:1] + extra
            obj = _number(metric, subject, val, cell_unit, raw_unit, period, cell,
                          headers[c], row_label if cell.context else subject, section, scope, extra[:2])
            numbers.append((score, (metric, subject, scope, period), obj))
    return texts, numbers
