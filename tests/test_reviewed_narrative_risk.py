"""Synthetic mechanics only. These fixtures cannot establish real review approval.

Run only under the task's protective harness; no provider or model calls.
"""

from datetime import date
import hashlib
import json
from pathlib import Path

import pytest

from app.services import directional_balance_service
from app.services.economic_claim_qualification import EconomicClaimProposal, policy_sha256
from app.services.native_input_admission import BackendAdmissionRegistry, UseAxis
from app.services.reported_economic_claim_consumer import (
    ReportedRoleCandidate,
    reported_role_request,
)
from app.services.reported_fact_owner import BackendReportedFactOwner
from app.services.reviewed_narrative_risk import (
    CONTRACT,
    RULE,
    BackendNarrativeSourceOwner,
    BackendNarrativeRiskClaimPolicy,
    BackendReviewedNarrativeRiskOwner,
    NarrativeRiskReviewDecision,
    NarrativeSpan,
    build_reported_narrative_risk_invocation,
)
from app.services.unified_snapshot_contract import digest
from tests.test_reported_fact_owner import owner_fixture
from tests.test_real_economic_property_owner import parent_for
from tests.test_reviewed_economic_property import issue, reviewed_fixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value).encode()


def sealed_receipt(value):
    body = {k: v for k, v in value.items() if k != "receipt_sha256"}
    return body | {"receipt_sha256": digest(body)}


def source_fixture_args(
    identity="UNSEEN_NARRATIVE", *, market="US", security_type="common_stock", amount=30
):
    _, args = owner_fixture(
        identity, market=market, security_type=security_type, current_amount=amount
    )
    artifacts = dict(args["artifacts"])
    discovery = json.loads(artifacts["discovery"])
    recent = discovery["filings"]["recent"]
    recent.update(reportDate=["2026-06-30"], primaryDocument=["issuer-20260630.htm"])
    artifacts["discovery"] = encoded(discovery)
    dr = json.loads(artifacts["discovery_receipt"])
    dr["raw_sha256"] = sha(artifacts["discovery"])
    artifacts["discovery_receipt"] = encoded(sealed_receipt(dr))
    fact_owner = BackendReportedFactOwner(
        **(
            args
            | dict(
                artifacts=artifacts,
                trusted_artifact_sha256={k: sha(v) for k, v in artifacts.items()},
            )
        )
    )
    accession = recent["accessionNumber"][0]
    selected = {key: values[0] for key, values in recent.items()}
    request = dict(
        method="GET",
        body="",
        headers=[],
        url=f"https://www.sec.gov/Archives/edgar/data/1234/{accession.replace('-', '')}/issuer-20260630.htm",
    )
    paragraphs = (
        b'<p id="risk">Product prices affect margins and cash flows.</p>',
        b'<p id="mechanism">If prices decline, margins and cash flows could decrease.</p>',
        b'<p id="mitigation">Demand and customer contracts may mitigate price pressure.</p>',
        b'<p id="timing">Some contracts were signed after June 30, 2026; entered agreements differ from prospective agreements.</p>',
        b'<p id="coverage">Remaining performance obligations do not equal total contract coverage or future revenue.</p>',
    )
    html = (
        b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>'
        b'<ix:nonNumeric name="dei:EntityCentralIndexKey" contextRef="c1">0000001234</ix:nonNumeric>'
        b'<ix:nonNumeric name="dei:DocumentPeriodEndDate" contextRef="c1" '
        b'format="ixt:date-monthname-day-year-en">June&#160;30, 2026</ix:nonNumeric>'
        b"<p>Multibyte offset witness: \xc3\xa9</p>" + b"".join(paragraphs) + b"</body></html>"
    )
    common = dict(
        generation_id=fact_owner.registration.source_generation_id,
        logical_request_id=f"financial:{identity}:filing1:primary",
        role=f"financial:{identity}",
        parent_receipts={
            f"financial:{identity}:discovery": json.loads(artifacts["discovery_receipt"])[
                "receipt_sha256"
            ]
        },
        descriptor_sha256=sha(b"synthetic-descriptor"),
        plan_sha256=sha(b"synthetic-plan"),
        request_sha256=sha(b"synthetic-planned-request"),
        resolved_request_sha256=digest(request),
    )
    narrative = dict(
        html=html,
        html_receipt=encoded(
            sealed_receipt(
                common
                | dict(
                    status="PASS",
                    raw_sha256=sha(html),
                    source_period="SOURCE_FRAGMENT_PENDING_FINANCIAL_OWNER",
                )
            )
        ),
        html_request=encoded(common | dict(request=request, selected=selected)),
        **{k: artifacts[k] for k in ("discovery", "discovery_receipt", "registration")},
    )
    return dict(
        fact_owner=fact_owner,
        artifacts=narrative,
        trusted_artifact_sha256={k: sha(v) for k, v in narrative.items()},
        source_kind="SYNTHETIC_REVIEW_FIXTURE",
        filing_accession=accession,
    ), paragraphs


def source_fixture(**kwargs):
    args, paragraphs = source_fixture_args(**kwargs)
    return BackendNarrativeSourceOwner(**args), args, paragraphs


def reviewed_args(source, paragraphs):
    a = source.admission
    r = a.registration
    spans = tuple(
        NarrativeSpan(
            category=category,
            start_byte=source._raw.index(raw),
            end_byte=source._raw.index(raw) + len(raw),
            raw_sha256=sha(raw),
        )
        for category, raw in zip(
            ("RISK", "MECHANISM", "MITIGATION", "MITIGATION", "MITIGATION"), paragraphs, strict=True
        )
    )
    review = b"SYNTHETIC_INDEPENDENT_REVIEW_NOT_REAL_AUTHORITY"
    proposal = b"SYNTHETIC_HISTORICAL_CONDITIONAL_RISK_PROPOSAL"
    d = NarrativeRiskReviewDecision(
        review_event_id="synthetic-risk-review",
        reviewer="synthetic-reviewer",
        mandate="R18_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION",
        decision="APPROVE_BOUNDED_EXISTING_POLICY_QUALIFICATION",
        proposal_sha256=sha(proposal),
        independent_review_sha256=sha(review),
        inherited_policy_sha256=sha(Path(directional_balance_service.__file__).read_bytes()),
        source_kind=a.source_kind,
        source_binding_sha256=a.source_binding_sha256,
        source_artifact_sha256=a.source_artifact_sha256,
        source_generation_id=r.source_generation_id,
        owner_execution_generation_id=r.execution_generation_id,
        security_id=r.security_id,
        issuer_id=r.issuer_id,
        facts=a.facts,
        filed=a.filed,
        statement_date=a.statement_date,
        cutoff=a.cutoff,
        spans=spans,
        materiality_basis="INDEPENDENT_CASE_REVIEW_OF_DISCLOSED_RISK_AND_ENTITY_SCALE",
        counterevidence_scope="EXACT_DISCLOSED_MITIGANTS_AND_ORIGINAL_SCALE_FACTS",
        risk_summary="pricing-sensitive margins/cash flows",
        condition_summary="selling prices fall",
        mechanism_summary="margins/cash flows may decline",
        mitigation_summary="demand and contracts may cushion impact",
    )
    raw = d.model_dump_json().encode()
    return dict(
        source_owner=source,
        decision_bytes=raw,
        trusted_decision_sha256=sha(raw),
        review_bytes=review,
        trusted_review_sha256=sha(review),
        proposal_bytes=proposal,
        execution_generation_id="synthetic-r18-consumer",
    ), d


def narrative_fixture(*, mutate=None, **kwargs):
    source, source_args, paragraphs = source_fixture(**kwargs)
    args, decision = reviewed_args(source, paragraphs)
    if mutate:
        mutate(args, decision)
    owner = BackendReviewedNarrativeRiskOwner(**args)
    return owner, args, source_args


def invocation_fixture(**kwargs):
    owner, _, _ = narrative_fixture(**kwargs)
    inv = build_reported_narrative_risk_invocation(
        owner, invocation_id="synthetic-risk-role", assessment_as_of=date(2026, 10, 11)
    )
    scope = inv.request.invocation
    claim = EconomicClaimProposal(
        claim_id="synthetic-risk",
        security_id=scope.security_id,
        generation_id=scope.generation_id,
        source_generation_id=scope.source_generation_id,
        requested_role="SELL_DRIVER",
        interpretation_type="BUSINESS_CAUTION",
        polarity="NEGATIVE",
        uncertainty="LIMITED",
        support_refs=tuple(s.support_ref for s in inv._policy.bundle.supports),
        policy_sha256=policy_sha256(),
    )
    return owner, inv, ReportedRoleCandidate(proposal=claim, confidence="LOW")


def replace_decision(args, decision, **changes):
    raw = decision.model_copy(update=changes).model_dump_json().encode()
    args.update(decision_bytes=raw, trusted_decision_sha256=sha(raw))


def reseal_source(args, *, html=None, receipt_change=None, request_change=None):
    """Synthetic store mutation, used to reach checks beyond the immutable pin."""
    artifacts = dict(args["artifacts"])
    receipt = json.loads(artifacts["html_receipt"])
    resolved = json.loads(artifacts["html_request"])
    if html is not None:
        artifacts["html"] = html
        receipt["raw_sha256"] = sha(html)
    if request_change:
        request_change(resolved)
        receipt["resolved_request_sha256"] = digest(resolved["request"])
        resolved["resolved_request_sha256"] = receipt["resolved_request_sha256"]
    if receipt_change:
        receipt_change(receipt)
    artifacts["html_receipt"] = encoded(sealed_receipt(receipt))
    artifacts["html_request"] = encoded(resolved)
    args.update(
        artifacts=artifacts, trusted_artifact_sha256={k: sha(v) for k, v in artifacts.items()}
    )


@pytest.mark.parametrize(
    "identity,market,kind",
    [
        ("UNSEEN_US", "US", "common_stock"),
        ("UNSEEN_KR", "KR", "common_stock"),
        ("UNSEEN_ADS", "US", "depositary_receipt"),
        ("UNSEEN_FINANCIAL", "US", "common_stock"),
        ("UNSEEN_CYCLICAL", "US", "common_stock"),
        ("UNSEEN_SOURCE_FORWARD", "US", "common_stock"),
        ("UNSEEN_INCOMPLETE", "US", "common_stock"),
    ],
)
def test_generic_synthetic_risk_role_uses_only_original_scale_facts(identity, market, kind):
    owner, inv, candidate = invocation_fixture(identity=identity, market=market, security_type=kind)
    assert type(inv._policy) is BackendNarrativeRiskClaimPolicy
    a = owner.admission
    assert a.contract == CONTRACT and a.review.rule_version == RULE
    assert (
        a.narrative_source.authority == "AUTHENTICATED_HISTORICAL_HTML_NOT_ECONOMIC_QUALIFICATION"
    )
    assert a.review.facts == owner._owner.facts
    assert len(inv._registry.bundle.metrics) == 4
    assert tuple(m.value for m in inv._registry.bundle.metrics) == tuple(
        f.value for f in a.review.facts
    )
    assert all(
        m.input_sha256 == f.occurrence_sha256
        for m, f in zip(inv._registry.bundle.metrics, a.review.facts, strict=True)
    )
    assert tuple(s.property for s in inv._policy.bundle.supports) == (
        "BUSINESS_RISK",
        "COUNTEREVIDENCE",
    )
    parent = parent_for(inv)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        assert packet.role == "SELL_DRIVER" and packet.source_kind == "SYNTHETIC_REVIEW_FIXTURE"
        assert packet.contract == "native-reported-risk-claim-packet-v1"
        assert receipt.contract == "backend-reported-risk-claim-ownership-fact-v2"
        assert not packet.accepted_Core and not packet.complete_economic_Stage2
        assert not parent._registry._accepted
        assert packet.facts == a.review.facts
        assert packet.narrative_span_sha256 == tuple(s.raw_sha256 for s in a.review.spans)
        assert packet.narrative_source_sha256 == a.review.source_artifact_sha256
        assert packet.narrative_admission_sha256 == a.admission_sha256
        assert (
            tuple(row.model_dump(mode="json") for row in packet.narrative_context)
            == inv._policy.narrative_packet_binding()["narrative_context"]
        )
        assert (
            parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, packet)
            == packet
        )
        assert len(packet.claim.text) <= 420
        for term in (
            "Historical filing 2026-08-01",
            "period 2026-06-30",
            "pricing-sensitive",
            "If selling prices fall",
            "margins/cash flows",
            "demand and contracts",
            "forecast and stance not established",
        ):
            assert term in packet.claim.text
    finally:
        parent.close()


@pytest.mark.parametrize(
    "key",
    ["html", "html_receipt", "html_request", "discovery", "discovery_receipt", "registration"],
)
def test_caller_rehash_is_not_a_source_pin(key):
    args, _ = source_fixture_args()
    args["artifacts"] = dict(args["artifacts"], **{key: args["artifacts"][key] + b" "})
    with pytest.raises(ValueError, match="ANCHOR_MISMATCH"):
        BackendNarrativeSourceOwner(**args)


@pytest.mark.parametrize(
    "before,after",
    [
        (b">0000001234<", b">0000009999<"),
        (b"June&#160;30, 2026", b"June&#160;29, 2026"),
        (b'name="dei:DocumentPeriodEndDate"', b'name="other:DocumentPeriodEndDate"'),
        (b'contextRef="c1" format=', b'contextRef="different" format='),
    ],
)
def test_resealed_html_must_independently_match_original_dei_and_period(before, after):
    args, _ = source_fixture_args()
    assert before in args["artifacts"]["html"]
    reseal_source(args, html=args["artifacts"]["html"].replace(before, after))
    with pytest.raises(ValueError, match="DEI"):
        BackendNarrativeSourceOwner(**args)


@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_sha256", "a" * 64),
        ("generation_id", "other-generation"),
        ("status", "FAILED"),
        ("role", "financial:OTHER"),
        ("parent_receipts", {}),
    ],
)
def test_resealed_transport_does_not_change_source_or_parent_identity(field, value):
    args, _ = source_fixture_args()
    reseal_source(args, receipt_change=lambda rec: rec.update({field: value}))
    with pytest.raises(ValueError):
        BackendNarrativeSourceOwner(**args)


@pytest.mark.parametrize("change", ["url", "accession", "document", "period", "form", "filed"])
def test_rehashed_request_cannot_replace_discovery_filing(change):
    args, _ = source_fixture_args()

    def mutation(resolved):
        if change == "url":
            resolved["request"]["url"] += "?caller=1"
        else:
            key = {
                "accession": "accessionNumber",
                "document": "primaryDocument",
                "period": "reportDate",
                "form": "form",
                "filed": "filingDate",
            }[change]
            resolved["selected"][key] = "other"

    reseal_source(args, request_change=mutation)
    with pytest.raises(ValueError, match="DISCOVERY_URL_OR_SELECTED"):
        BackendNarrativeSourceOwner(**args)


def test_independently_rehashed_discovery_cannot_replace_original_fact_lineage():
    args, _ = source_fixture_args()
    changed = dict(args["artifacts"])
    discovery = json.loads(changed["discovery"])
    discovery["filings"]["recent"]["primaryDocument"][0] = "substituted.htm"
    changed["discovery"] = encoded(discovery)
    args.update(artifacts=changed, trusted_artifact_sha256={k: sha(v) for k, v in changed.items()})
    with pytest.raises(ValueError, match="ORIGINAL_REGISTRATION_OR_DISCOVERY"):
        BackendNarrativeSourceOwner(**args)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer", "caller-self-approved"),
        ("source_kind", "REAL_SEALED_SOURCE"),
        ("risk_summary", "a caller-written current prediction"),
        ("source_artifact_sha256", "a" * 64),
        ("review_event_id", "substituted-review"),
    ],
)
def test_public_decision_cannot_fabricate_reviewer_or_meaning(field, value):
    def mutate(args, d):
        args["decision_bytes"] = d.model_copy(update={field: value}).model_dump_json().encode()

    with pytest.raises(ValueError, match="REVIEW_ANCHOR_MISMATCH"):
        narrative_fixture(mutate=mutate)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_kind", "REAL_SEALED_SOURCE"),
        ("source_binding_sha256", "a" * 64),
        ("source_generation_id", "other"),
        ("owner_execution_generation_id", "other"),
        ("statement_date", "2026-06-29"),
        ("cutoff", "2026-09-02"),
        ("issuer_id", "9999"),
        ("inherited_policy_sha256", "a" * 64),
        ("permitted_role", "HOLDER_REASON"),
        ("asserts_realization", True),
        ("asserts_causality", True),
        ("asserts_recurrence", True),
        ("asserts_currentness", True),
        ("asserts_forecast", True),
        ("asserts_stance", True),
        ("active_material_risk_override", True),
        ("allowed_confidences", ("LOW", "HIGH")),
    ],
)
def test_even_backend_repin_cannot_broaden_profile_or_substitute_source(field, value):
    with pytest.raises(ValueError):
        narrative_fixture(mutate=lambda args, d: replace_decision(args, d, **{field: value}))


@pytest.mark.parametrize("key", ["review_bytes", "proposal_bytes"])
def test_review_and_proposal_are_exact_bytes_not_caller_meaning(key):
    def mutate(args, d):
        args[key] += b"changed"

    with pytest.raises(ValueError):
        narrative_fixture(mutate=mutate)


@pytest.mark.parametrize("change", ["offset", "digest", "end", "omission", "category", "duplicate"])
def test_raw_span_offsets_categories_and_required_mitigants(change):
    def mutate(args, d):
        spans = list(d.spans)
        if change == "omission":
            spans = [s for s in spans if s.category != "MITIGATION"]
        elif change == "duplicate":
            spans[2] = spans[0].model_copy(update={"category": "MITIGATION"})
        else:
            update = {
                "offset": {"start_byte": spans[0].start_byte + 1},
                "digest": {"raw_sha256": "a" * 64},
                "end": {"end_byte": 999999},
                "category": {"category": "CAUSAL_PROOF"},
            }[change]
            spans[0] = spans[0].model_copy(update=update)
        replace_decision(args, d, spans=tuple(spans))

    with pytest.raises(ValueError):
        narrative_fixture(mutate=mutate)


def test_spans_use_original_utf8_byte_offsets_not_text_offsets():
    owner, _, source_args = narrative_fixture()
    raw = source_args["artifacts"]["html"]
    for s in owner.admission.review.spans:
        assert sha(raw[s.start_byte : s.end_byte]) == s.raw_sha256
        assert raw.decode().index('<p id="' + s.category.lower()) < s.start_byte


def test_historical_temporal_and_coverage_qualifiers_reach_request_context():
    owner, inv, _ = invocation_fixture()
    binding = inv._policy.narrative_packet_binding()
    context = binding["narrative_context"]
    assert len(context) == len(owner.admission.review.spans) == 5
    assert all(
        set(row) == {"category", "start_byte", "end_byte", "raw_sha256", "text"} for row in context
    )
    text = " ".join(row["text"] for row in context)
    assert "signed after June 30, 2026" in text
    assert "entered agreements differ from prospective agreements" in text
    assert "do not equal total contract coverage or future revenue" in text
    request = reported_role_request(inv)
    assert tuple(row.model_dump(mode="json") for row in request.narrative_context) == context
    changed = dict(context[-1], text="Caller removed the historical limitations")
    inv._reported_role_request_json = request.model_copy(
        update={"narrative_context": (*context[:-1], changed)}
    ).model_dump_json()
    with pytest.raises(ValueError, match="SCHEMA_OR_VALIDATOR"):
        reported_role_request(inv)


def test_oversized_excerpt_is_rejected_without_truncating_qualifiers():
    args, paragraphs = source_fixture_args()
    oversized = b'<p id="risk">' + b"x" * 5001 + b"</p>"
    reseal_source(args, html=args["artifacts"]["html"].replace(paragraphs[0], oversized))
    source = BackendNarrativeSourceOwner(**args)
    args, _ = reviewed_args(source, (oversized, *paragraphs[1:]))
    with pytest.raises(ValueError, match="EXCEEDS_5000"):
        BackendReviewedNarrativeRiskOwner(**args)


def test_excerpt_text_is_deterministic_from_only_admitted_bytes():
    args, paragraphs = source_fixture_args()
    quoted = b'<p id="risk">Prices <b>and</b> margins &amp; cash&#160;flows.</p>'
    reseal_source(args, html=args["artifacts"]["html"].replace(paragraphs[0], quoted))
    source = BackendNarrativeSourceOwner(**args)
    args, decision = reviewed_args(source, (quoted, *paragraphs[1:]))
    assert source.excerpt(decision.spans[0])["text"] == "Prices and margins & cash flows."
    assert source.excerpt(decision.spans[0])["raw_sha256"] == sha(quoted)
    assert BackendReviewedNarrativeRiskOwner(**args).admission.review.spans == decision.spans


@pytest.mark.parametrize(
    "field,value",
    [
        ("filing_accession", "0000001234-26-000999"),
        ("source_generation_id", "other"),
        ("occurrence_ordinal", 9999),
        ("value", 987.654321),
        ("period_end", date(2026, 6, 29)),
    ],
)
def test_review_preserves_exact_original_numeric_facts(field, value):
    def mutate(args, d):
        facts = list(d.facts)
        facts[0] = facts[0].model_copy(update={field: value})
        replace_decision(args, d, facts=tuple(facts))

    with pytest.raises(ValueError, match="ORIGINAL_FACT_SET"):
        narrative_fixture(mutate=mutate)


def test_background_scale_neither_autoapproves_risk_nor_requires_growth():
    source, _, _ = source_fixture(amount=1)
    assert source.admission.authority == "AUTHENTICATED_HISTORICAL_HTML_NOT_ECONOMIC_QUALIFICATION"
    with pytest.raises(ValueError, match="LIVE_REVIEWED"):
        build_reported_narrative_risk_invocation(
            source, invocation_id="not-approved", assessment_as_of=date(2026, 10, 11)
        )
    owner, inv, candidate = invocation_fixture(amount=1)
    claim, _, _ = inv._policy.qualify(candidate.proposal, request=inv.request, invocation=inv)
    assert "conditional disclosure" in claim.text
    assert owner.admission.review.numeric_fact_use == "BACKGROUND_SCALE_NOT_INDEPENDENT_RISK_PROOF"


@pytest.mark.parametrize("target", ["property", "source", "original-fact"])
def test_live_resolution_revocation_reaches_claim_and_packet(target):
    owner, inv, candidate = invocation_fixture()
    parent = parent_for(inv)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        if target == "property":
            owner.revoke(owner.admission)
        elif target == "source":
            owner._source_owner.revoke(owner._source_owner.admission)
        else:
            owner._owner._admitted.pop(owner._source_owner._admissions[0].admission_id)
        with pytest.raises(ValueError):
            inv._policy.qualify(candidate.proposal, request=inv.request, invocation=inv)
        with pytest.raises(ValueError):
            inv._policy.narrative_packet_binding()
        with pytest.raises(ValueError):
            parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, packet)
    finally:
        parent.close()


def test_copied_receipts_are_not_fresh_live_ownership():
    first, _, _ = narrative_fixture()
    second, _, _ = narrative_fixture()
    with pytest.raises(ValueError, match="UNISSUED"):
        second.resolve(first.admission)
    with pytest.raises(ValueError, match="UNISSUED"):
        second._source_owner.resolve(first.admission.narrative_source)
    changed = first.admission.model_copy(update={"admission_id": "copied"})
    with pytest.raises(ValueError, match="UNISSUED"):
        first.resolve(changed)


def test_presealed_review_reuses_stable_source_binding_not_live_capability():
    first, args, _ = narrative_fixture()
    second_source, _, _ = source_fixture()
    source = first.admission.narrative_source
    assert source.source_binding_sha256 == second_source.admission.source_binding_sha256
    assert source.admission_id != second_source.admission.admission_id
    assert source.admission_sha256 != second_source.admission.admission_sha256
    assert (
        source.supporting_fact_admission_sha256
        != second_source.admission.supporting_fact_admission_sha256
    )
    second = BackendReviewedNarrativeRiskOwner(**(args | {"source_owner": second_source}))
    assert second.admission.review == first.admission.review
    assert second.admission.admission_sha256 != first.admission.admission_sha256
    with pytest.raises(ValueError, match="UNISSUED"):
        second.resolve(first.admission)
    with pytest.raises(ValueError, match="UNISSUED"):
        second_source.resolve(source)
    second_source.revoke(second_source.admission)
    with pytest.raises(ValueError, match="REVOKED"):
        second.resolve(second.admission)


@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_role", "BUY_DRIVER"),
        ("requested_role", "DECISIVE_REASON"),
        ("requested_role", "HOLDER_REASON"),
        ("interpretation_type", "BUSINESS_SUPPORT"),
        ("polarity", "POSITIVE"),
        ("uncertainty", "QUALIFIED"),
        ("asserts_causality", True),
        ("asserts_recurrence", True),
        ("asserts_independent_corroboration", True),
        ("consumer", "HOLDER"),
        ("use_axis", "HOLDER_DIRECTION"),
        ("source_generation_id", "other"),
        ("policy_sha256", "a" * 64),
        ("support_refs", ("reviewed-narrative:BUSINESS_RISK",)),
    ],
)
def test_claim_cannot_broaden_reviewed_role_or_drop_mitigation(field, value):
    _, inv, candidate = invocation_fixture()
    with pytest.raises(ValueError):
        inv._policy.qualify(
            candidate.proposal.model_copy(update={field: value}),
            request=inv.request,
            invocation=inv,
        )
    assert not inv._policy._issued


def test_even_correct_numeric_value_cannot_become_narrative_proof():
    _, inv, candidate = invocation_fixture()
    m = inv._registry.bundle.metrics[0]
    proposal = candidate.proposal.model_copy(
        update={"numeric_assertions": ({"evidence_ref": m.metric_ref, "value": m.value},)}
    )
    with pytest.raises(ValueError, match="OUTSIDE_REVIEWED"):
        inv._policy.qualify(proposal, request=inv.request, invocation=inv)


@pytest.mark.parametrize(
    "field,value",
    [
        ("value", 987.654321),
        ("metric_type", "FAKE_NARRATIVE_NUMBER"),
        ("source_artifact_sha256", "a" * 64),
        ("source_provider", "CALLER_PROJECTION"),
        ("caveats", ()),
    ],
)
def test_consistently_rehashed_registry_cannot_change_projection(field, value):
    _, inv, _ = invocation_fixture()
    bundle = inv._registry.bundle
    metric = bundle.metrics[0].model_copy(update={field: value})
    changed = bundle.model_copy(update={"metrics": (metric, *bundle.metrics[1:])})
    with pytest.raises(ValueError):
        registry = BackendAdmissionRegistry(
            changed, expected_bundle_sha256=digest(changed.model_dump(mode="json"))
        )
        inv._policy._verify_property_projection(registry)


def test_no_extra_permission_time_or_confidence_from_reviewed_property():
    _, inv, _ = invocation_fixture()
    m = inv._registry.bundle.metrics[0]
    assert {p.axis for p in m.permissions if p.state == "ALLOWED"} == {
        UseAxis.CORE_VISIBILITY,
        UseAxis.CORE_DIRECTION,
    }
    assert next(t for t in m.temporal if t.field == "metric_as_of").state == "UNKNOWN_NOT_PROVIDED"
    assert all(s.allowed_confidences == ("LOW",) for s in inv._policy.bundle.supports)
    permissions = tuple(
        p.model_copy(
            update=dict(state="ALLOWED", owner_evidence_ref=m.owner_ref + "#/" + p.axis.value)
        )
        for p in m.permissions
    )
    changed = inv._registry.bundle.model_copy(
        update={
            "metrics": (
                m.model_copy(update={"permissions": permissions}),
                *inv._registry.bundle.metrics[1:],
            )
        }
    )
    registry = BackendAdmissionRegistry(
        changed, expected_bundle_sha256=digest(changed.model_dump(mode="json"))
    )
    with pytest.raises(ValueError, match="EXACT_FACT_PROJECTION"):
        inv._policy._verify_property_projection(registry)


def test_assessment_cannot_precede_sealed_review_cutoff():
    owner, _, _ = narrative_fixture()
    with pytest.raises(ValueError, match="NOT_AVAILABLE_AT_ASSESSMENT"):
        build_reported_narrative_risk_invocation(
            owner, invocation_id="wrong-time", assessment_as_of=date(2026, 8, 31)
        )


def test_native_request_binding_and_generic_downgrade_rejection():
    from app.services.native_accepted_ownership import BackendOwnershipRegistry

    owner, inv, _ = invocation_fixture()
    request = reported_role_request(inv)
    assert request.required_role == "SELL_DRIVER"
    assert request.narrative_admission_sha256 == owner.admission.admission_sha256
    store = BackendOwnershipRegistry(offline_reproof=True)
    with pytest.raises(ValueError, match="ROUTE"):
        store.begin(inv, model="fixture", effort="fixture")
    with pytest.raises(ValueError, match="ROUTE"):
        store.begin_claims(inv, model="fixture", effort="fixture")
    inv._reported_role_request_json = request.model_copy(
        update={"narrative_source_sha256": "a" * 64}
    ).model_dump_json()
    with pytest.raises(ValueError, match="SCHEMA_OR_VALIDATOR"):
        reported_role_request(inv)


def test_r17_historical_buy_receipt_remains_distinct_and_unchanged():
    risk, _, _ = invocation_fixture()
    buy, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    try:
        _, receipt, packet = issue(parent, inv, candidate)
        assert buy.admission.contract == "real-economic-property-owner-v1"
        assert (
            packet.contract == "native-reported-economic-claim-packet-v1"
            and packet.role == "BUY_DRIVER"
        )
        assert "Historical reported operating" in packet.claim.text
        assert not hasattr(packet, "narrative_span_sha256")
        risk.revoke(risk.admission)
        assert (
            parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, packet)
            == packet
        )
    finally:
        parent.close()
