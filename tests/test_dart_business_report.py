import pytest

from app.services.dart_business_report import parse_dart_business_report


def table(rows):
    return "<TABLE>" + "".join("<TR>" + "".join(row) + "</TR>" for row in rows) + "</TABLE>"


def td(text, attrs=""):
    return f"<TD {attrs}>{text}</TD>"


def th(text, attrs=""):
    return f"<TH {attrs}>{text}</TH>"


def report(content, after="", end="20260930"):
    return f'''<DOCUMENT><DOCUMENT-NAME ACODE="11013">분기보고서</DOCUMENT-NAME>
<COMPANY-NAME AREGCIK="12345678">시험기업</COMPANY-NAME><BODY><COVER>
<P>제 7 기</P><TU AUNIT="PERIODFROM" AUNITVALUE="20260101"></TU>
<TU AUNIT="PERIODTO" AUNITVALUE="{end}"></TU></COVER>
<SECTION-1><TITLE>II. 사업의 내용</TITLE><SECTION-2><TITLE>1. 사업의 개요</TITLE>
{content}</SECTION-2></SECTION-1>{after}</BODY></DOCUMENT>'''.encode()


def parse(body):
    return parse_dart_business_report(body, corp_code="12345678", report_code="11014")


def sales(unit="백만원", value="(1,230)", extra=""):
    return ("<P>사업부문별 누적 연결 매출 세부내역은 다음과 같습니다.</P>"
            + table([[td("(단위 : " + unit + ")")]]) + table([
                [th("구분", 'ROWSPAN="2"'), th("제7기 3분기", 'COLSPAN="2"'), th("제6기", 'ROWSPAN="2"')],
                [th("금액"), th("비중(%)")],
                [td("시험사업"), td(value), td("17.2"), td("9021")],
                [td("합계"), td("7081"), td("100"), td("50000")],
            ]) + extra)


def test_merged_headers_unit_sibling_negative_and_prior_annual():
    d = parse(report(sales()))
    assert [(r["metric"], r["value"], r["unit"], r["unit_scale"], r["scope"], r["subject"]) for r in d["numbers"]] == [
        ("business_revenue", -1230, "KRW", 10**6, "consolidated", "시험사업"),
        ("business_revenue_share", 17.2, "pct", 1, "consolidated", "시험사업"),
    ]
    assert all((r["period_role"], r["period_start"], r["period_end"]) ==
               ("report_to_date", "2026-01-01", "2026-09-30") for r in d["numbers"])


@pytest.mark.parametrize("amount", ["", "-", "미확정", "산출 중", "1,23", "12%"])
def test_missing_or_malformed_number_is_never_backfilled(amount):
    rows = parse(report(sales(value=amount)))["numbers"]
    assert [r["metric"] for r in rows] == ["business_revenue_share"]


def test_mixed_currency_and_unitless_amount_rejected():
    for unit in ("원, USD", "수량", ""):
        assert all(r["metric"] != "business_revenue" for r in parse(report(sales(unit)))["numbers"])


def test_unrelated_units_are_never_inherited_after_an_intervening_data_table():
    data = sales().replace(table([[td("(단위 : 백만원)")]]),
                           table([[td("(단위 : 백만원)")]]) + table([[td("다른 표"), td("완료")]]))
    assert not parse(report(data))["numbers"]


def test_fiscal_identity_period_and_no_dtd():
    run = report(sales())
    for body in (run.replace(b"12345678", b"00000000"), run.replace(b"20260930", b"20260630"),
                 b'<!DOCTYPE foo SYSTEM "file:///absent">' + run):
        with pytest.raises(ValueError):
            parse(body)


def test_irregular_text_and_malformed_table_do_not_hide_following_scoped_notes():
    bad = "<P>R&D 역량과 <성장요인>에 힘입어 사업부 매출이 성장했습니다.</P>"
    bad += "<TABLE><TR><TD>의미가 없는 깨진 행</TABLE>" + sales()
    notes = """<SECTION-1><TITLE>III. 재무에 관한 사항</TITLE>
    <SECTION-2><TITLE>3. 연결재무제표 주석</TITLE><TABLE-GROUP>
    <TITLE>부문별 보고 (연결)</TITLE><P>이번 분기 수익성은 일회성 수익의 영향으로 개선되었습니다.</P>
    </TABLE-GROUP></SECTION-2><SECTION-2><TITLE>5. 재무제표 주석</TITLE>
    <TABLE-GROUP><TITLE>영업부문정보</TITLE><P>회사는 생산설비 증설을 계획하고 있습니다.</P></TABLE-GROUP>
    </SECTION-2></SECTION-1>"""
    d = parse(report(bad, notes))
    assert {r["scope"] for r in d["texts"]} == {"business_section", "consolidated", "separate"}
    assert any(r["classification"] == "MANAGEMENT_OUTLOOK_OR_ESTIMATE" for r in d["texts"])
    assert d["numbers"] and d["numbers"][0]["scope"] == "consolidated"


def test_ragged_grid_rejected_without_borrowing_an_adjacent_header():
    ambiguous = sales().replace('<TD >17.2</TD>', '')
    assert parse(report(ambiguous))["numbers"] == []


def test_same_table_comparative_period_and_context_basis_require_agreement():
    meta = table([[td("당분기"), td("(단위 : 천원)")]])
    def fact(context, value):
        return f'<TE ACONTEXT="{context}" ACODE="dart_OperatingIncomeLoss">{value}</TE>'
    def xblr(one, two):
        return table([
            [th(""), th("보고부문", 'COLSPAN="2"')],
            [th(""), th("제품사업", 'COLSPAN="2"')],
            [th(""), th("3개월"), th("누적")],
            [td("영업이익"), fact(one, "(25)"), fact(two, "80")]
        ])
    prefix = '<SECTION-1><TITLE>III. 재무에 관한 사항</TITLE><SECTION-2><TITLE>연결재무제표 주석</TITLE><TITLE>영업부문정보 (연결)</TITLE>'
    suffix = '</SECTION-2></SECTION-1>'
    q = "CFY2026dTQQ_ifrs-full_ConsolidatedMember_ifrs-full_SegmentsAxis_Entity"
    a = q.replace("dTQQ", "dTQA")
    d = parse(report("", prefix + meta + xblr(q, a) + suffix))
    assert {(r["value"], r["period_start"], r["period_role"]) for r in d["numbers"]} == {
        (-25, "2026-07-01", "single_quarter"), (80, "2026-01-01", "report_to_date")}
    for first, second in [(a, q), (q.replace("2026", "2025"), a.replace("Consolidated","Separate"))]:
        assert not parse(report("", prefix + meta + xblr(first, second) + suffix))["numbers"]


def test_subsidiary_title_and_actor_survive_same_paragraph_switch():
    p = ("<P>[장비부문]당사는 다양한 장비를 생산하고 있습니다."
         "[기타부문]가상물류는 식품과 원재료의 내륙 운송을 운영합니다."
         "당분기 매출과 영업이익은 물량 증가에 힘입어 크게 성장했습니다.</P>")
    result = parse(report(p))
    excerpt = next(r["excerpt"] for r in result["texts"] if "물량 증가" in r["excerpt"])
    assert "기타부문" in excerpt and "가상물류" in excerpt and "장비부문" not in excerpt


def test_compound_contract_subtotals_cannot_be_used_as_a_whole_payment():
    def contract(amount):
        data = table([[td(k), td(v)] for k,v in [
            ("계약상대방","구매처"),("계약내용","제품도입 및 공급 계약"),
            ("총계약금액","320억원"),("지급금액",amount)]])
        return parse(report("<P>품목 : 라이선스 계약</P>" + data))
    negative = contract("[품목1] 계약금: 2억원 총 7억원 [품목2] 계약금: 2억원 총 7억원")
    assert [r["metric"] for r in negative["numbers"]] == ["contract_stated_total"]
    true_total = contract("계약금 5억원, 중도금 7억원, 총 12억원")
    assert {r["metric"]: r["value"] for r in true_total["numbers"]} == {
        "contract_stated_total": 320, "contract_payments_made": 12}


def test_immediately_preceding_business_unit_names_entity_in_order_row():
    owner = "■ 서비스부문 : ㈜가상정보통신"
    data = table([[th("품목"), th("수주잔고 금액")], [td("공급계약"), td("8")]])
    result = parse(report(f"<P>{owner}</P>" + table([[td("(기준일 : 2026.09.30) (단위 : 억원)")]]) + data))
    assert result["numbers"][0]["subject"] == owner + " / 공급계약"


def test_projected_sales_table_is_not_reported_as_realized():
    data = sales().replace("사업부문별 누적 연결 매출", "사업부문별 예상 누적 연결 매출")
    assert not parse(report(data))["numbers"]
