"""Legal-issuer candidate resolution; source candidates are not use grants.

v1 callers keep their existing contract. The v2 auxiliary path replays the
original financial owner and the REV6 identity bridge, without ticker dispatch.
"""
from datetime import date, datetime
import json
import re
from typing import Literal
from urllib.parse import parse_qs, urlparse

from pydantic import Field

from app.services.auxiliary_issuer_financial_owner import _assemble
from app.services.issuer_business_bridge import identity_bridge
from app.services.unified_snapshot_contract import ContractModel, digest


class IssuerSourceRegistration(ContractModel):
    legal_issuer_id: str = Field(min_length=1)
    canonical_company_id: str = Field(min_length=1)
    cik: str | None = Field(default=None, pattern=r"^[0-9]{1,10}$")
    corp_code: str | None = Field(default=None, pattern=r"^[0-9]{8}$")
    effective_from: date
    effective_through: date
    state: Literal["ACTIVE", "REVOKED"]


class GenericIssuerDependency(ContractModel):
    contract: Literal["auxiliary-issuer-only-v2"] = "auxiliary-issuer-only-v2"
    role: Literal["AUXILIARY_ISSUER_ONLY"] = "AUXILIARY_ISSUER_ONLY"
    primary_subject: str = Field(min_length=1)
    auxiliary_issuer_security: str = Field(min_length=1)
    purpose: Literal["SHARED_ISSUER_BUSINESS_FINANCIAL_EVIDENCE"] = "SHARED_ISSUER_BUSINESS_FINANCIAL_EVIDENCE"
    run_id: str = Field(min_length=1)
    cutoff: datetime
    source_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    official_identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    user_message_eligible: Literal[False] = False
    model_subject_eligible: Literal[False] = False
    valuation_eligible: Literal[False] = False
    technical_eligible: Literal[False] = False


def candidates(*, security, registration, cutoff):
    """Backend registration is input to discovery, never evidence of a fact."""
    reg = IssuerSourceRegistration.model_validate(registration)
    if (cutoff.utcoffset() is None or reg.state != "ACTIVE"
            or not reg.effective_from <= cutoff.date() <= reg.effective_through):
        raise ValueError("issuer_registration_expired_or_revoked")
    if (security.get("canonical_company_id") != reg.canonical_company_id
            or not security.get("canonical_security_id")):
        raise ValueError("issuer_registration_identity")
    for field in ("cik", "corp_code"):
        value, registered = security.get(field), getattr(reg, field)
        if value and (not registered or str(value).zfill(10 if field == "cik" else 8) !=
                      registered.zfill(10 if field == "cik" else 8)):
            raise ValueError("issuer_provider_identifier_conflict")
    providers = []
    if reg.cik and int(reg.cik):
        providers.append(dict(provider="SEC", issuer_id=reg.cik.zfill(10),
            source_type="DIRECT_SEC_CANDIDATE", format="SEC_ORIGINAL"))
    if reg.corp_code and int(reg.corp_code):
        providers.append(dict(provider="DART", issuer_id=reg.corp_code,
            source_type="DIRECT_DART_CANDIDATE", format="OPENDART_JSON_OR_PUBLIC_DOCUMENT"))
    if not providers:
        raise ValueError("issuer_official_identifier_missing")
    return dict(contract="legal-issuer-source-candidates-v1",
        legal_issuer_id=reg.legal_issuer_id, security_id=security["canonical_security_id"],
        candidates=providers, authority="DISCOVERY_ONLY_NOT_FACT_OR_USE",
        direction=False, per_share=False, valuation=False, price=False, B2=False)


def validate_locator(*, provider, issuer_id, filing_id, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment or parsed.port:
        raise ValueError("official_locator_invalid")
    if provider == "DART":
        query = parse_qs(parsed.query, keep_blank_values=True)
        if (not re.fullmatch(r"[0-9]{8}", issuer_id) or int(issuer_id) == 0
                or not re.fullmatch(r"[0-9]{14}", filing_id)
                or parsed.hostname != "dart.fss.or.kr"
                or parsed.path not in {"/report/viewer.do", "/dsaf001/main.do"}
                or query.get("rcpNo") != [filing_id]):
            raise ValueError("dart_locator_filing_mismatch")
    elif provider == "SEC":
        if (not re.fullmatch(r"[0-9]{1,10}", issuer_id) or not int(issuer_id)
                or not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", filing_id)
                or parsed.hostname != "www.sec.gov" or parsed.query
                or not parsed.path.startswith(
                    f"/Archives/edgar/data/{int(issuer_id)}/{filing_id.replace('-', '')}/")
                or ".." in parsed.path or "%" in parsed.path):
            raise ValueError("sec_locator_issuer_filing_mismatch")
    else:
        raise ValueError("unsupported_official_provider")
    return dict(provider=provider, issuer_id=issuer_id, filing_id=filing_id,
        url=url, authority="LOCATOR_ONLY_NOT_FINANCIAL_OWNERSHIP")


def require_original_financial_format(*, provider, content_type):
    if provider == "DART" and content_type != "OPENDART_ORIGINAL_JSON":
        raise ValueError("DART_PUBLIC_HTML_FIELD_OWNER_ADAPTER_MISSING")
    if provider == "SEC" and content_type not in {"SEC_COMPANYFACTS_JSON", "SEC_ORIGINAL_FILING"}:
        raise ValueError("SEC_ORIGINAL_FORMAT_REQUIRED")
    if provider not in {"DART", "SEC"}:
        raise ValueError("unsupported_official_provider")


def assemble_generic_issuer(*, plan, acquisition, directory, receipts,
                            dependency, target_plan, official, dart_rows,
                            dart_receipt, registration, field_semantics=True):
    dep = GenericIssuerDependency.model_validate(dependency)
    if (plan["ticker"] != plan["security"]["ticker"]
            or target_plan["ticker"] != target_plan["security"]["ticker"]):
        raise ValueError("issuer_subject_label_mismatch")
    resolved = candidates(security=plan["security"], registration=registration,
        cutoff=dep.cutoff)
    if not any(row["provider"] == "DART" and row["issuer_id"] == plan["issuer"]
               for row in resolved["candidates"]):
        raise ValueError("registered_issuer_provider_not_selected")
    if digest(target_plan["security"]) != target_plan["identity_sha256"]:
        raise ValueError("target_plan_identity")
    bridge = identity_bridge(target=target_plan["security"], source=plan["security"],
        official=official, expected_official_sha256=dep.official_identity_sha256,
        dart_rows=dart_rows, dart_receipt=dart_receipt, cutoff=dep.cutoff.isoformat())
    if bridge["status"] != "PASS":
        raise ValueError("issuer_original_identity_bridge_denied:" + ",".join(bridge["errors"]))
    if dart_receipt not in receipts:
        raise ValueError("issuer_discovery_receipt_membership")
    # Re-read discovery through the original capture receipt, not caller rows.
    from app.services.bounded_financial_projection import _raw, verify_capture
    verify_capture(plan, acquisition, directory, receipts)
    discovery = json.loads(_raw(directory, dart_receipt["artifact"], receipts))
    if discovery.get("list") != dart_rows:
        raise ValueError("issuer_discovery_raw_membership")
    result = _assemble(plan=plan, acquisition=acquisition, directory=directory,
        receipts=receipts, dep=dep, target_plan=target_plan, field_semantics=field_semantics)
    result["contract"] = "auxiliary-issuer-financial-owner-v2"
    result["identity_bridge"] = bridge
    result["source_candidates"] = resolved
    result["scope"] = "issuer_business_only"
    result["economic_direction_granted"] = False
    result["source_use_authority"] = "ORIGINAL_COMPARISON_OWNER_ONLY_NOT_NATIVE"
    result["result_sha256"] = digest(result)
    return result
