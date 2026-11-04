"""TEST-ONLY synthetic custody and SEC markup; no real identity is admitted.

These tests replay the actual SEC parser and pure reconciliation owner. They do
not validate a real archive or constitute an official/current identity receipt.
"""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import hashlib
import zipfile

import pytest

from app.services import scoped_current_identity as module
from app.services.scoped_routing_identity import RoutingCatalogPin, ScopedSubject, SealedRoutingCatalog
from app.services.scoped_source_plan import HistoryCounts, ScopedConfig, compile_scoped_source_plan
from app.services.unified_snapshot_contract import encoded
from app.services.unified_stock_acquisition import ROLES


AT = datetime(2026, 10, 18, 0, tzinfo=timezone.utc)
CUTOFF = AT + timedelta(minutes=1)
STARTED = AT - timedelta(days=1)


def sec_html(*, ticker="TESTCO", name="TEST ONLY INDUSTRIES INC", cik="0000000123",
             title="Common Stock", exchange="Nasdaq Global Select Market"):
    fields = {"TradingSymbol": ticker, "EntityRegistrantName": name,
        "EntityCentralIndexKey": cik, "Security12bTitle": title, "SecurityExchangeName": exchange}
    return ("<html>" + "".join(
        f'<ix:nonNumeric name="dei:{key}" contextRef="cover">{value}</ix:nonNumeric>'
        for key, value in fields.items()) + "</html>").encode()


class TestOnlyReader(module.TrustedIdentityReader):
    __test__ = False

    def __init__(self, reference, capture):
        self.reference, self.capture = reference, capture
        self.calls = []

    def read_sec_cover(self, reference, *, maximum_bytes):
        self.calls.append(reference)
        if reference != self.reference:
            raise module.IdentityEvidenceUnavailable("REFERENCE_MISMATCH")
        assert maximum_bytes == module.MAX_SEC_DOCUMENT_BYTES
        return self.capture


@pytest.fixture
def case(tmp_path):
    security = dict(ticker="TESTCO", canonical_company_id="test-only-company",
        canonical_security_id="test-only-security", company_name="TEST ONLY INDUSTRIES INC",
        legal_name="TEST ONLY INDUSTRIES INC", exchange="NASDAQ", country="US",
        cik="0000000123", security_type="common_stock", share_class=None,
        issuer_type="domestic_us", identity_provider="fixture", identity_quality="inferred",
        updated_at="2026-10-01T00:00:00+00:00")
    member = "static/security-lineage.json"
    files = {member: encoded({"TESTCO": dict(security=security,
        role="IDENTITY_ONLY_NOT_CURRENT_FINANCIAL_EVIDENCE", source_generation="test-only-history")}),
        "review-control-final/result.sha256": b"CONTROL_SET_SHA256 " + b"a" * 64 + b"\n"}
    manifest = {n: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) for n, raw in files.items()}
    archive = tmp_path / "test-only-routing.zip"
    with zipfile.ZipFile(archive, "x") as output:
        for name, raw in files.items():
            output.writestr(name, raw)
        output.writestr("manifest.json", encoded(dict(files=manifest)))
    catalog = SealedRoutingCatalog(archive=archive, pin=RoutingCatalogPin(
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), member=member,
        member_sha256=hashlib.sha256(files[member]).hexdigest(), predecessor_control_sha256="a" * 64))
    subject = ScopedSubject(ticker="TESTCO", market="us", security_id="test-only-security",
        issuer_id="0000000123", venue="NASDAQ", currency="USD")
    counts = HistoryCounts(**{role: 300 for role in ROLES})
    compilation = module.ScopedCompilationInputs(
        config=ScopedConfig(subjects=(subject,), kr_history=counts, us_history=counts, kr_max_pages=3),
        catalog=catalog, generation_id="test-only-review", at=AT, code_sha="b" * 40,
        provider_config_sha256="c" * 64)
    plan = compile_scoped_source_plan(**compilation.__dict__, enabled=True)
    reference = module.SecCoverReference(subject=subject, source_generation_id="test-only-original-source",
        source_plan_sha256="d" * 64, logical_request_id="test-document-003", receipt_sha256="e" * 64)
    raw = sec_html()
    capture = module.SecCoverCapture(reference=reference, raw=raw,
        raw_sha256=hashlib.sha256(raw).hexdigest(), request_sha256="f" * 64,
        issuer_cik="0000000123", filing_accession="0000000123-26-000001",
        source_url="https://www.sec.gov/Archives/edgar/data/123/000000012326000001/test.htm",
        source_form="10-Q", source_as_of=date(2026, 10, 16), source_run_started_at=STARTED,
        requested_at=STARTED + timedelta(seconds=1), received_at=STARTED + timedelta(seconds=2))
    return dict(plan=plan, compilation=compilation, reader=TestOnlyReader(reference, capture),
        sec_sources=(reference,), cutoff=CUTOFF,
        freshness=module.IdentityFreshnessPolicy(maximum_capture_age_seconds=3 * 86400,
            maximum_filing_age_days=30), enabled=True)


def failures(result):
    return {gap.reason for gap in result.missing_receipts if gap.receipt_type == "SEC_SECURITY_CLASSIFICATION"}


def test_original_owners_called_but_current_admission_remains_denied(case, monkeypatch):
    parser = module.sec_owner.parse_sec_cover_page_identity
    owner = module.sec_owner.OfficialSecurityIdentityService.plan
    calls = []

    def parse(*args, **kwargs):
        calls.append("original_parser")
        return parser(*args, **kwargs)

    def reconcile(self, *args, **kwargs):
        calls.append("original_owner")
        return owner(self, *args, **kwargs)

    monkeypatch.setattr(module.sec_owner, "parse_sec_cover_page_identity", parse)
    monkeypatch.setattr(module.sec_owner.OfficialSecurityIdentityService, "plan", reconcile)
    before = case["plan"].model_dump(mode="json")
    result = module.review_scoped_current_identity(**case)
    assert calls == ["original_parser", "original_owner"]
    assert result.status == "NOT_ADMITTED" and not result.dispatch_allowed
    assert not result.current_identity_authority and result.source_use == "NOT_ADMITTED"
    assert len(result.partial_authority) == 1 and not failures(result)
    replay = result.partial_authority[0]
    assert replay.claim == "SEC_FILED_CLASSIFICATION_REPLAY_ONLY"
    assert replay.owner_action == "apply_authoritative_identity"
    assert replay.reference.source_generation_id == "test-only-original-source"
    assert result.review_generation_id == "test-only-review"
    assert replay.source_as_of == date(2026, 10, 16)
    assert replay.received_at == case["reader"].capture.received_at
    assert case["plan"].model_dump(mode="json") == before
    assert case["plan"].identities[0].original_identity_quality == "inferred"
    assert "app/services/sealed_financial_identity_reader.py" in dict(result.owner_files)


def test_exact_missing_owners_and_full_market_dependencies(case):
    result = module.review_scoped_current_identity(**case)
    stock = {g.receipt_type for g in result.missing_receipts if g.role == "stock:TESTCO"}
    assert stock == {"OFFICIAL_CURRENT_LISTING", "LISTING_CURRENCY", "CORPORATE_ACTION_BASIS"}
    assert {g.role for g in result.missing_receipts if g.receipt_type == "MARKET_INSTRUMENT_IDENTITY"} == {
        "us_market:" + symbol for symbol in case["plan"].us_market_symbols}
    assert sum(g.receipt_type == "MARKET_INSTRUMENT_IDENTITY" for g in result.missing_receipts) == 22
    assert sum(g.receipt_type == "INDEX_SOURCE_IDENTITY" for g in result.missing_receipts) == 2
    assert {g.role for g in result.missing_receipts if g.receipt_type == "ETF_CLASSIFICATION"} == {
        "us:ETF_PROXY:SPY", "us:ETF_PROXY:QQQ"}


@pytest.mark.parametrize("enabled", [False, 1, "true", None])
def test_default_off_before_reader(case, enabled):
    case["enabled"] = enabled
    with pytest.raises(ValueError, match="feature_off"):
        module.review_scoped_current_identity(**case)
    assert not case["reader"].calls


def test_omitted_enable_is_off(case):
    del case["enabled"]
    with pytest.raises(ValueError, match="feature_off"):
        module.review_scoped_current_identity(**case)


@pytest.mark.parametrize("field,value,reason", [
    ("raw_sha256", "0" * 64, "RAW_HASH_MISMATCH"),
    ("issuer_cik", "0000000999", "ISSUER_MISMATCH"),
    ("source_url", "https://example.invalid/test.htm", "SEC_DOCUMENT_IDENTITY_MISMATCH"),
    ("filing_accession", "0000000123-26-000002", "SEC_DOCUMENT_IDENTITY_MISMATCH"),
    ("requested_at", STARTED.replace(tzinfo=None), "CLOCK_NAIVE"),
    ("received_at", CUTOFF + timedelta(seconds=1), "SOURCE_TIME_ORDER"),
    ("requested_at", CUTOFF, "SOURCE_TIME_ORDER"),
    ("source_as_of", date(2026, 10, 19), "SOURCE_TIME_ORDER"),
    ("source_as_of", date(2020, 1, 1), "FILING_STALE"),
])
def test_exact_document_and_clock_failures(case, field, value, reason):
    case["reader"].capture = case["reader"].capture.model_copy(update={field: value})
    result = module.review_scoped_current_identity(**case)
    assert not result.partial_authority and reason in failures(result)


def test_stale_retrieval_is_not_freshened_by_review_time(case):
    case["freshness"] = module.IdentityFreshnessPolicy(
        maximum_capture_age_seconds=60, maximum_filing_age_days=30)
    result = module.review_scoped_current_identity(**case)
    assert failures(result) == {"CAPTURE_STALE"}


@pytest.mark.parametrize("changes,reason", [
    ({"ticker": "OTHER"}, "SEC_OWNER_REJECTED"),
    ({"cik": "0000000999"}, "ISSUER_MISMATCH"),
    ({"exchange": "New York Stock Exchange"}, "SEC_CLASSIFICATION_MISMATCH"),
    ({"title": "Exchange Traded Fund Units"}, "SEC_OWNER_REJECTED"),
])
def test_rehashed_wrong_raw_cannot_supply_missing_authority(case, changes, reason):
    raw = sec_html(**changes)
    case["reader"].capture = case["reader"].capture.model_copy(update={
        "raw": raw, "raw_sha256": hashlib.sha256(raw).hexdigest()})
    result = module.review_scoped_current_identity(**case)
    assert not result.partial_authority and failures(result) == {reason}


@pytest.mark.parametrize("name", ["Test Only Industries, Inc.", "ANOTHER ISSUER LABEL"])
def test_inferred_name_difference_is_audited_not_an_owner_bypass(case, name, monkeypatch):
    raw = sec_html(name=name)
    case["reader"].capture = case["reader"].capture.model_copy(update={
        "raw": raw, "raw_sha256": hashlib.sha256(raw).hexdigest()})
    owner = module.sec_owner.OfficialSecurityIdentityService.plan
    calls = []

    def reconcile(self, *args, **kwargs):
        calls.append("original_owner")
        return owner(self, *args, **kwargs)

    monkeypatch.setattr(module.sec_owner.OfficialSecurityIdentityService, "plan", reconcile)
    result = module.review_scoped_current_identity(**case)
    assert calls == ["original_owner"]
    replay = result.partial_authority[0]
    assert replay.issuer_name == name
    assert replay.sealed_issuer_names == ("TEST ONLY INDUSTRIES INC",)
    assert replay.identity_discrepancies == ("ISSUER_NAME_DIFFERS_FROM_SEALED_RECORD",)
    assert not replay.current_identity_authority and result.status == "NOT_ADMITTED"


@pytest.mark.parametrize("field,value", [
    ("source_generation_id", "relabeled-current"), ("source_plan_sha256", "0" * 64),
    ("logical_request_id", "different-request"), ("receipt_sha256", "0" * 64),
])
def test_reference_must_match_backend_custody(case, field, value):
    case["sec_sources"] = (case["sec_sources"][0].model_copy(update={field: value}),)
    assert failures(module.review_scoped_current_identity(**case)) == {"REFERENCE_MISMATCH"}


def test_capture_reference_must_match_requested_reference(case):
    wrong = case["sec_sources"][0].model_copy(update={"source_generation_id": "wrong"})
    case["reader"].capture = case["reader"].capture.model_copy(update={"reference": wrong})
    assert failures(module.review_scoped_current_identity(**case)) == {"REFERENCE_MISMATCH"}


def test_same_generation_requires_original_frozen_clock(case):
    reference = case["sec_sources"][0].model_copy(update={
        "source_generation_id": case["compilation"].generation_id})
    case["sec_sources"] = (reference,)
    case["reader"].reference = reference
    case["reader"].capture = case["reader"].capture.model_copy(update={"reference": reference})
    assert failures(module.review_scoped_current_identity(**case)) == {"SOURCE_GENERATION_CLOCK_MISMATCH"}


@pytest.mark.parametrize("failure", [PermissionError("boundary"), OSError("corruption"),
    RuntimeError("unexpected"), ValueError("capture_integrity_mismatch")])
def test_reader_hard_stops_propagate(case, failure, monkeypatch):
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(case["reader"], "read_sec_cover", fail)
    with pytest.raises(type(failure), match=str(failure)):
        module.review_scoped_current_identity(**case)


def test_missing_backend_and_capture_are_explicit(case):
    reader = case["reader"]
    case["reader"] = None
    assert failures(module.review_scoped_current_identity(**case)) == {"BACKEND_UNAVAILABLE"}
    case["reader"] = reader
    reader.capture = None
    assert failures(module.review_scoped_current_identity(**case)) == {"CAPTURE_MISSING"}
    case["sec_sources"] = ()
    assert failures(module.review_scoped_current_identity(**case)) == {"REFERENCE_MISSING"}


def test_public_payload_is_not_a_reader_capability(case):
    case["reader"] = {"authoritative": True, "receipt_sha256": "a" * 64}
    with pytest.raises(TypeError, match="capability_required"):
        module.review_scoped_current_identity(**case)


def test_plan_cannot_be_rehashed_into_admission(case):
    data = case["plan"].model_dump(mode="json")
    data["owner_files_json"] = "{}"
    case["plan"] = data
    with pytest.raises(ValueError, match="canonical_replay_mismatch"):
        module.review_scoped_current_identity(**case)
    assert not case["reader"].calls


def test_duplicate_and_wrong_subject_references_rejected(case):
    reference = case["sec_sources"][0]
    case["sec_sources"] = (reference, reference)
    with pytest.raises(ValueError, match="reference_bound"):
        module.review_scoped_current_identity(**case)
    wrong = reference.subject.model_copy(update={"ticker": "SPY"})
    case["sec_sources"] = (reference.model_copy(update={"subject": wrong}),)
    with pytest.raises(ValueError, match="reference_scope"):
        module.review_scoped_current_identity(**case)


def test_cutoff_and_compilation_identity_fail_before_reader(case):
    with pytest.raises(ValueError, match="cutoff_before_plan"):
        module.review_scoped_current_identity(**{**case, "cutoff": AT - timedelta(seconds=1)})
    with pytest.raises(ValueError, match="CLOCK_NAIVE"):
        module.review_scoped_current_identity(**{**case, "cutoff": CUTOFF.replace(tzinfo=None)})
    case["compilation"] = replace(case["compilation"], generation_id="wrong-review")
    with pytest.raises(ValueError, match="canonical_replay_mismatch"):
        module.review_scoped_current_identity(**case)
    assert not case["reader"].calls


def test_result_cannot_issue_positive_current_authority(case):
    result = module.review_scoped_current_identity(**case)
    assert result.review_sha256 == module.review_scoped_current_identity(**case).review_sha256
    for field, value in (("status", "ADMITTED"), ("dispatch_allowed", True),
                         ("current_identity_authority", True), ("source_use", "GRANTED")):
        with pytest.raises(ValueError):
            module.ScopedCurrentIdentityReview.model_validate({**result.model_dump(), field: value})


def test_unknown_reader_semantic_failure_is_not_silently_downgraded():
    with pytest.raises(ValueError, match="unsupported_identity_reader_denial"):
        module.IdentityEvidenceUnavailable("permission_error")
