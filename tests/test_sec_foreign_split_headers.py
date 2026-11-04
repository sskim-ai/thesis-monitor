"""Explicit column-owned FPI periods and units, independent of issuer identity."""
import pytest

from app.services.sec_foreign_comparison_service import period_from_headers
from app.services.sec_foreign_statement_boundary_service import statement_boundaries


@pytest.mark.parametrize('headers', [
    ['Period Ended June 30', '2026'],
    ['2026', 'Three months'],
    ['Period Ended June 30', '2026', '2025', 'Three months'],
    ['Period Ended June 30', '2026', 'Three months', 'Six months'],
    ['Period Ended June 30', 'Period Ended March 31', '2026', 'Three months'],
    ['Period Ended June 29', '2026', 'Three months'],
    ['Second quarter of 2026'],
])
def test_split_period_requires_exact_column_evidence(headers):
    assert period_from_headers(headers)['period_start'] is None


@pytest.mark.parametrize('unit,expected', [
    ('In millions of Korean won, except per share information', 'PASS'),
    ('W', 'FAIL'),
    ('In millions of Korean won; in thousands of Korean won', 'FAIL'),
    ('In millions of Korean won; in millions of US dollars', 'FAIL'),
])
def test_explicit_header_units_no_currency_or_scale_guess(unit, expected):
    html = f'<p>Consolidated Interim Statements of Comprehensive Income</p><table><tr><td>{unit}</td></tr><tr><td>Revenue</td><td>123</td></tr></table>'
    assert statement_boundaries(html)[0]['status'] == expected


@pytest.mark.parametrize('amount', ['123', '2026', '$123', '(123)'])
def test_body_footnote_cannot_supply_header_unit(amount):
    html = f'<p>Consolidated Interim Statements of Comprehensive Income</p><table><tr><td></td><td>Three months ended June 30, 2026</td></tr><tr><td>Revenue</td><td>{amount}</td></tr><tr><td>In millions of Korean won</td></tr></table>'
    assert statement_boundaries(html)[0]['status'] == 'FAIL'


@pytest.mark.parametrize('year,duration,start', [('2023', 'Three months', '2023-04-01'),
    ('2024', 'Six months', '2024-01-01')])
def test_same_column_split_period(year, duration, start):
    result = period_from_headers(['Period Ended June 30', year, duration])
    assert result['period_start'] == start
    assert result['period_end'] == year + '-06-30'
