from datetime import date, timedelta

import pytest

from app.services.issuer_fiscal_week_policy import extract_policy, annual_comparability


def document(issuer="123", weekday="Thursday", month="August", day=31,
             current_end="2026-09-03", prior_end="2025-08-28"):
    def context(key, end, weeks):
        start = date.fromisoformat(end) - timedelta(days=weeks * 7 - 1)
        return (f'<x:context id="{key}"><x:entity><x:identifier scheme="http://www.sec.gov/CIK">'
                f'{issuer}</x:identifier></x:entity><x:period><x:startDate>{start}</x:startDate>'
                f'<x:endDate>{end}</x:endDate></x:period></x:context>')
    return (f'<html xmlns:x="http://www.xbrl.org/2003/instance"><p>'
            f'Our fiscal year is the 52- or 53-week period ending on the {weekday} closest to {month} {day}. '
            'Fiscal 2026 contained 53 weeks and fiscal 2025 and 2024 each contained 52 weeks.</p>'
            + context("a", current_end, 53) + context("b", prior_end, 52) + '</html>').encode()


FILING = dict(form="10-K", accessionNumber="fictional-filing", reportDate="2026-09-03")


def pair(issuer="123", current_end="2026-09-03", prior_end="2025-08-28"):
    def row(end, weeks):
        return dict(issuer=str(issuer).zfill(10), metric="revenue", semantic="statement_revenue",
                    statement_basis="consolidated", currency="USD", unit="USD", unit_scale=1,
                    formal_state="FORMAL", period_role="ANNUAL", source_document_id=FILING["accessionNumber"],
                    period_start=(date.fromisoformat(end)-timedelta(days=weeks*7-1)).isoformat(),
                    period_end=end)
    return row(current_end, 53), row(prior_end, 52)


@pytest.mark.parametrize("issuer", ["123", "987654", "3456789"])
@pytest.mark.parametrize("calendar", [
    ("Thursday", "August", 31, "2026-09-03", "2025-08-28"),
    ("Friday", "June", 30, "2026-07-03", "2025-06-27"),
])
def test_source_declared_calendar_reuses_exact_contexts_generically(issuer, calendar):
    weekday, month, day, current, prior = calendar
    proof = extract_policy(document(issuer, weekday, month, day, current, prior), issuer=issuer, filing=FILING)
    assert proof["status"] == "PROVEN"
    assert all(row["source_contexts"] for row in proof["years"])
    result = annual_comparability(*pair(issuer, current, prior), proof)
    assert result["current_weeks"] == 53 and result["prior_weeks"] == 52
    assert result["quality_reason_codes"] == ["FISCAL_WEEK_COUNT_DIFFERENCE"]
    assert result["value_adjustment"] is None


@pytest.mark.parametrize("mutation", [
    "wrong_issuer", "no_context", "dimension", "wrong_duration", "wrong_namespace",
    "no_years", "no_rule", "conflicting_rule", "conflicting_year", "duplicate_id",
])
def test_missing_or_conflicting_source_cannot_create_calendar_authority(mutation):
    raw = document()
    if mutation == "wrong_issuer":
        raw = raw.replace(b">123<", b">456<")
    elif mutation == "no_context":
        raw = raw.split(b"<x:context")[0] + b"</html>"
    elif mutation == "dimension":
        raw = raw.replace(b"</x:entity>", b"<x:segment>segment</x:segment></x:entity>")
    elif mutation == "wrong_duration":
        raw = raw.replace(b"2025-08-29", b"2025-08-30").replace(b"2024-08-30", b"2024-08-31")
    elif mutation == "wrong_namespace":
        raw = raw.replace(b"http://www.xbrl.org/2003/instance", b"https://untrusted.invalid/instance")
    elif mutation == "no_years":
        raw = raw.replace(b"contained", b"approximately contained")
    elif mutation == "no_rule":
        raw = raw.replace(b"closest", b"after")
    elif mutation == "conflicting_rule":
        raw = raw.replace(b"</p>", b"Our fiscal year is the 52- or 53-week period ending on the Friday closest to August 31.</p>")
    elif mutation == "conflicting_year":
        raw = raw.replace(b"</p>", b"Fiscal 2026 contained 52 weeks.</p>")
    elif mutation == "duplicate_id":
        raw = raw.replace(b'id="b"', b'id="a"')
    proof = extract_policy(raw, issuer="123", filing=FILING)
    assert proof["status"] == "UNPROVEN"
    assert annual_comparability(*pair(), proof) is None


def test_old_duration_tolerance_is_not_introduced():
    proof = extract_policy(document(), issuer="123", filing=FILING)
    current, prior = pair()
    current["period_start"] = "2025-08-30"
    assert annual_comparability(current, prior, proof) is None


@pytest.mark.parametrize("mutation", [
    "instant", "forever", "split_period", "misplaced_identifier",
    "nested_identifier", "nested_start", "nested_end",
])
def test_malformed_xbrl_context_structure_is_not_calendar_evidence(mutation):
    raw = document()
    if mutation == "instant":
        raw = raw.replace(b"</x:period>", b"<x:instant>2026-09-03</x:instant></x:period>")
    elif mutation == "forever":
        raw = raw.replace(b"</x:period>", b"<x:forever></x:forever></x:period>")
    elif mutation == "split_period":
        raw = raw.replace(b"</x:startDate>", b"</x:startDate></x:period><x:period>")
    elif mutation == "misplaced_identifier":
        raw = raw.replace(b"<x:entity>", b"<x:entity><x:wrapper>").replace(
            b"</x:entity>", b"</x:wrapper></x:entity>")
    else:
        key = {"nested_identifier": "identifier", "nested_start": "startDate", "nested_end": "endDate"}[mutation]
        if key == "identifier":
            raw = raw.replace(b">123</x:identifier>", b"><x:instant>123</x:instant></x:identifier>")
        else:
            raw = raw.replace(("<x:" + key + ">").encode(), ("<x:" + key + "><x:instant>").encode())
            raw = raw.replace(("</x:" + key + ">").encode(), ("</x:instant></x:" + key + ">").encode())
    proof = extract_policy(raw, issuer="123", filing=FILING)
    assert proof["status"] == "UNPROVEN"
    assert annual_comparability(*pair(), proof) is None


@pytest.mark.parametrize("conflict", ["year", "end", "duplicate_context"])
def test_mixed_grammar_ambiguity_cannot_fall_back_to_legacy_authority(conflict):
    legacy = ("Fiscal year 2026 was comprised of 53 weeks and ended on September 3, 2026. "
              "Fiscal year 2025 was comprised of 52 weeks and ended on August 28, 2025.")
    raw = document().replace(b"</p>", legacy.encode() + b"</p>")
    if conflict == "year":
        raw = raw.replace(b"2026 contained 53", b"2026 contained 52")
    elif conflict == "end":
        raw = raw.replace(b"ended on September 3", b"ended on September 2")
    else:
        raw = raw.replace(b'id="b"', b'id="a"')
    proof = extract_policy(raw, issuer="123", filing=FILING)
    assert proof["status"] == "UNPROVEN"
    assert annual_comparability(*pair(), proof) is None
