"""Offline purpose-owner regressions; real captured bytes enter via parent helper."""
from copy import deepcopy
from datetime import datetime

import httpx
import pytest

from app.services import sec_fpi_purpose_evidence_owner as owner
from app.services.bounded_financial_acquisition import sec_base
from app.services.sec_fpi_financial_purpose import classify_document
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from test_sec_fpi_purpose_probe import original, planned, capture  # noqa: F401


DISPOSAL = '''<h2>Report on Disposal of Treasury Shares</h2>
<p>The issuer disposed of a portion of its treasury shares.</p>
<p>Period of Disposal: August 8, 2026 to September 7, 2026.</p>
<p>Type and Number of Disposed Shares: 82 common shares.</p>
<table><tr><th>Disposal Price per Share (Won)</th><th>Aggregate Disposal Price</th></tr>
<tr><td>1,500,000</td><td>123,000,000</td></tr></table>
<p>Treasury Shares Held after the Disposal: 1,625,769 shares.</p>'''
ACQUISITION = '''<h2>Decision on Acquisition of Treasury Shares</h2>
<p>The board approved the acquisition of treasury shares for cancellation.</p>
<p>Number of Treasury Shares to be Acquired: 24,070,000.</p>
<p>Estimated Aggregate Acquisition Value: Won 40,004,340,000,000.</p>
<p>Planned Acquisition Period: August 20, 2026 to November 19, 2026.</p>
<h3>Limit on Treasury Share Acquisition Amount</h3>
<table><tr><th>Limit on distributable profit under the Commercial Act</th><th>Amount</th></tr>
<tr><td>Net assets</td><td>117,318,562,193,943</td></tr>
<tr><td>Retained earnings</td><td>9,867,146,544,188</td></tr>
<tr><td>Total Limit on Treasury Share Acquisition Amount</td><td>89,448,011,686,863</td></tr></table>
<p>The "Limit on distributable profit" was prepared based on the Company's financial statements as of the end of fiscal year 2025.</p>'''
RUMOR = '''<h2>Response to Disclosure Inquiry (Rumors or Media Reports)</h2>
<p>The issuer is reviewing a new factory; no matters have been determined.
The Company will make a further disclosure when details are confirmed.</p>'''
CANCELLATION = '''<h2>Decision on Cancellation of Treasury Shares</h2>
<p>The board approved the cancellation of treasury shares.</p>
<p>Number of Shares to be Cancelled: 24,070,000.</p>
<p>Estimated Aggregate Cancellation Value: Won 40,004,340,000,000.</p>
<p>There will be no change to the Company's capital.</p>'''
RETURNS = '''<h2>Shareholder Return Policy</h2><p>For the policy period,
the Company plans to return over 50% of cumulative Free Cash Flow.</p>
<p>The Company plans to acquire and cancel treasury shares and pay cash dividends.</p>
<p>Cautionary statement regarding forward-looking statements.</p>'''


def schedule(year):
    return f'''<p>The Company plans to hold a conference call for the {year} 3Q earnings results as follows:</p>
<p>1. Agenda</p><p>{year} 3Q Earnings Results</p><p>2. Date and Time</p>
<p>October 28, {year} 9:00 a.m.</p><p>3. Method: Conference Call.</p>
<p>Financial Information &#174; Earnings Release</p>
<p>The materials for the conference call will be available on its website on October 28, {year}.</p>'''


@pytest.fixture
def bound(original, tmp_path):
    def make(body, assets=()):
        one = (*original[:5], original[5][:1])
        plan = planned(one)
        if callable(body):body = body(datetime.fromisoformat(plan['cutoff']).year + 1)
        raw = ('<html><body>' + body + '</body></html>').encode()
        def respond(request):
            if request.url.path.endswith('index.json'):
                return httpx.Response(200, json={'directory': {'name': request.url.path.rsplit('/', 1)[0],
                    'item': [{'name': plan['filings'][0]['primaryDocument']}, *[{'name': n} for n in assets]]}})
            return httpx.Response(200, content=raw, headers={'Content-Type': 'text/html'})
        reader, replay, _ = capture(one, tmp_path, plan=plan, handler=respond)
        index_receipt = next(r for r in reader.receipts if r['stage'] == 'index')
        index = (reader.output / index_receipt['artifact']).read_bytes()
        return raw, index, dict(probe_plan=plan, probe_receipts=reader.receipts,
            source_anchor=original[4], expected_capture_sha256=replay['capture_sha256'], filing=plan['filings'][0])
    return make


def assert_actual_purpose_case(primary, index, *, expected_rationale, **binding):
    """The isolated parent supplies pinned real raw/receipts, not filesystem paths."""
    result = owner.qualify_purpose(primary, index, **binding)
    assert result['classification'] == 'CONFIRMED_NON_FINANCIAL'
    assert result['rationale'] == expected_rationale
    assert result['source_spans'] and result['field_absence_audit']['complete_for_purpose']
    assert owner.validate_purpose(result, primary, index, **binding) == result
    assert result['financial_authority'] is False and result['source_use_eligible'] is False
    assert result['admitted_fact_count'] == 0 and result['native_ready'] is False
    return result


@pytest.mark.parametrize('body,rationale', [
    (schedule, 'FUTURE_EARNINGS_CALL_SCHEDULE_NOT_DELIVERED_RESULTS'),
    (DISPOSAL, 'TREASURY_SHARE_DISPOSAL_CAPITAL_TRANSACTION'),
    (ACQUISITION, 'TREASURY_ACQUISITION_WITH_HISTORICAL_LEGAL_CAP'),
    (RUMOR, 'UNDETERMINED_CORPORATE_EVENT_RUMOR_RESPONSE'),
    (CANCELLATION, 'TREASURY_SHARE_CANCELLATION_CAPITAL_TRANSACTION'),
    (RETURNS, 'PROSPECTIVE_CAPITAL_RETURN_POLICY_NOT_REPORTED_CASH_FLOW'),
])
def test_generic_unseen_issuer_purpose_and_replay_never_economic_use(bound, body, rationale):
    primary, index, kwargs = bound(body)
    before = deepcopy(kwargs)
    result = assert_actual_purpose_case(primary, index, expected_rationale=rationale, **kwargs)
    assert kwargs == before
    assert result['cross_generation_use'].startswith('AUDIT_ONLY')
    assert result['binding']['probe_cutoff'] == kwargs['probe_plan']['cutoff']
    assert result['current_owner_eligible'] is False


@pytest.mark.parametrize('extra', [
    '<p>Revenue for the quarter was USD 100 million.</p>',
    '<p>Operating profit: 30. Net income: 20.</p>',
    '<h3>Unaudited financial statements</h3>',
    '<h3>Statements of operations</h3>',
    '<h3>Financial highlights</h3>',
    '<p>For the three months ended September 30.</p>',
    '<p style="display:none">Quarterly results: revenue 100.</p>',
    '<p>Free cash flow for Q3 was USD 300.</p>',
    '<p>Free cash flow: USD 300 million.</p>',
    '<p>Net assets 99,000 outside the legal cap.</p>',
    '<p>Attached hereto is Exhibit 99.</p>',
    '<script>document.write("Revenue 300")</script>',
    '<p>Rev<span>enue</span>: 300 million.</p>',
    '<p>&#47588;&#52636; 300</p>',
])
def test_whole_content_mixed_or_unparsed_financial_section_cannot_clear(bound, extra):
    primary, index, kwargs = bound(RETURNS + extra)
    result = owner.qualify_purpose(primary, index, **kwargs)
    assert result['classification'] != 'CONFIRMED_NON_FINANCIAL'
    assert not result['field_absence_audit']['complete_for_purpose']


@pytest.mark.parametrize('body', [
    '<h2>Decision on Acquisition of Treasury Shares</h2>',
    ACQUISITION.replace('fiscal year 2025', 'fiscal year 2099'),
    ACQUISITION.replace('Net assets', 'Operating income'),
    ACQUISITION + '<p>Retained earnings 900 in a separate section.</p>',
    schedule(2001),
    '<h2>Earnings Results</h2>',
    RUMOR.replace('no matters have been determined', 'the issuer reports current results'),
])
def test_title_year_and_undefined_financial_section_are_not_whitelists(bound, body):
    primary, index, kwargs = bound(body)
    assert owner.qualify_purpose(primary, index, **kwargs)['classification'] == 'UNKNOWN_UNRESOLVED'


@pytest.mark.parametrize('assets,extra', [
    (('logo.jpg',), '<img src="logo.jpg" alt="LOGO" width="1" height="1">'),
    (('unreferenced.png',), ''),
    (('ex99.htm',), ''),
    ((), '<object data="report.pdf"></object>'),
    ((), '<svg><text>logo</text></svg>'),
    ((), '<iframe srcdoc="&lt;p&gt;Revenue 300&lt;/p&gt;"></iframe>'),
    ((), '<img src="https://example.invalid/logo.jpg" alt="LOGO">'),
])
def test_all_index_assets_and_inline_media_need_actual_inspection(bound, assets, extra):
    primary, index, kwargs = bound(RUMOR + extra, assets)
    result = owner.qualify_purpose(primary, index, **kwargs)
    assert result['classification'] == 'UNKNOWN_UNRESOLVED'
    assert result['unresolved_assets'] and 'MEDIA_CONTENT_UNRESOLVED' in result['denial_reasons']


def media_fixture(primary, index, kwargs, disposition=owner.MEDIA_CLEAR):
    # Synthetic trusted backend event. No real pixel review or provider call.
    event = {'event': 'isolated-test-pixel-inspection', 'whole_asset': True}
    def verify(candidate, **inputs):
        if candidate is not event or inputs['asset_raw'] != b'\xff\xd8\xffsynthetic-image-bytes':
            raise ValueError('unverified_review_event')
        return dict(status='PASS', scope='WHOLE_ASSET_PIXELS', disposition=disposition, reason='Synthetic complete image fixture inspected')
    registry = owner.MediaReviewRegistry(verify)
    url = sec_base(kwargs['probe_plan'], kwargs['filing']) + 'logo.jpg'
    request = dict(method='GET', url=url, params={})
    raw = b'\xff\xd8\xffsynthetic-image-bytes'
    receipt = dict(request_sha256=digest(request), raw_sha256=sha256_bytes(raw), HTTP_status=200, failure_class=None)
    arguments = dict(asset_url=url, filing=kwargs['filing'], primary_sha256=sha256_bytes(primary),
        index_sha256=sha256_bytes(index), probe_capture_sha256=kwargs['expected_capture_sha256'],
        request=request, request_receipt=receipt, review_event=event)
    return registry, raw, arguments


@pytest.mark.parametrize('disposition,expected', [(owner.MEDIA_CLEAR, 'CONFIRMED_NON_FINANCIAL'),
    (owner.MEDIA_FINANCIAL, 'UNKNOWN_UNRESOLVED'), ('UNKNOWN', 'UNKNOWN_UNRESOLVED')])
def test_backend_media_event_capability_and_financial_pixels_gate(bound, disposition, expected):
    primary, index, kwargs = bound(RUMOR, ('logo.jpg',))
    registry, raw, args = media_fixture(primary, index, kwargs, disposition)
    token = registry.record(raw, **args)
    kwargs.update(media_observations=(token,), media_validator=registry.validate)
    result = owner.qualify_purpose(primary, index, **kwargs)
    assert result['classification'] == expected
    assert owner.validate_purpose(result, primary, index, **kwargs) == result
    assert result['media_coverage'][0]['observation']['review_event'] == args['review_event']


def test_review_json_reviewer_hash_and_arbitrary_callback_cannot_issue_media_authority(bound):
    primary, index, kwargs = bound(RUMOR, ('logo.jpg',))
    registry, raw, args = media_fixture(primary, index, kwargs)
    fake = deepcopy(args)
    with pytest.raises(ValueError, match='unverified_review_event'):
        registry.record(raw, **fake)
    label = dict(reviewer='trusted', sha256=sha256_bytes(raw), classification=owner.MEDIA_CLEAR)
    with pytest.raises(ValueError, match='unbound_observation'):
        owner.qualify_purpose(primary, index, **kwargs, media_observations=(label,), media_validator=registry.validate)
    with pytest.raises(ValueError, match='backend_registry'):
        owner.qualify_purpose(primary, index, **kwargs, media_validator=lambda *a, **k: label)


@pytest.mark.parametrize('change', ['raw', 'index', 'receipts', 'plan', 'anchor', 'filing', 'receipt'])
def test_changed_input_or_caller_rehashed_disposition_rejected(bound, change):
    primary, index, kwargs = bound(DISPOSAL)
    result = owner.qualify_purpose(primary, index, **kwargs)
    kwargs = deepcopy(kwargs)
    if change == 'raw':primary += b' '
    elif change == 'index':index += b' '
    elif change == 'receipts':kwargs['probe_receipts'][0]['started_at'] = '2000-01-01T00:00:00+00:00'
    elif change == 'plan':kwargs['probe_plan']['run_id'] = 'reissued-generation'
    elif change == 'anchor':kwargs['source_anchor']['discovery_sha256'] = 'f'*64
    elif change == 'filing':kwargs['filing']['filingDate'] = '2000-01-01'
    else:
        result['financial_authority'] = True
        result['receipt_sha256'] = digest({k: v for k, v in result.items() if k != 'receipt_sha256'})
    with pytest.raises(ValueError):owner.validate_purpose(result, primary, index, **kwargs)


def test_legacy_classifier_output_unchanged_by_opt_in_owner(bound):
    primary, index, kwargs = bound(DISPOSAL)
    plan = {**kwargs['probe_plan'], 'financial_owner_policy': 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'}
    url = sec_base(plan, kwargs['filing']) + kwargs['filing']['primaryDocument']
    before = classify_document(primary, url=url, filing=kwargs['filing'], plan=plan)
    result = owner.qualify_purpose(primary, index, **kwargs)
    assert result['original_classifier'] == before
    assert classify_document(primary, url=url, filing=kwargs['filing'], plan=plan) == before
