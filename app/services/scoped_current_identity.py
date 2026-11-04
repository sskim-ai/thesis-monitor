"""Detached SEC owner replay, never a current-identity or dispatch grant.

The backend reader is a trusted composition-root capability, not a request field.
It must verify original sealed plan/request/receipt custody before returning bytes.
Hashes below detect mismatches; they do not authenticate a caller-made receipt.
No production reader or complete current listing/ETF owner is installed here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field

from app.models.security import SecurityMaster
from app.services import official_security_identity_service as sec_owner
from app.services.scoped_routing_identity import ScopedSubject, SealedRoutingCatalog
from app.services.scoped_source_plan import (
    R22ScopedSourcePlanV1, ScopedConfig, validate_scoped_structure,
)
from app.services.unified_snapshot_contract import ContractModel, digest

MAX_SEC_DOCUMENT_BYTES = 4_000_000
SHA = r"^[a-f0-9]{64}$"
ROOT = Path(__file__).resolve().parents[2]
OWNER_FILES = (
    "app/services/scoped_current_identity.py",
    "app/services/sealed_financial_identity_reader.py",
    "app/services/official_security_identity_service.py",
    "app/services/security_identity_service.py",
    "app/models/security.py",
)


@dataclass(frozen=True)
class ScopedCompilationInputs:
    """Backend-selected inputs used to replay the unchanged R30 compiler."""
    config: ScopedConfig
    catalog: SealedRoutingCatalog
    generation_id: str
    at: datetime
    code_sha: str
    provider_config_sha256: str


class IdentityFreshnessPolicy(ContractModel):
    # Explicit task policy, not proof that an issuer/listing is still current.
    maximum_capture_age_seconds: int = Field(ge=1, le=31_536_000, strict=True)
    maximum_filing_age_days: int = Field(ge=0, le=3660, strict=True)


class SecCoverReference(ContractModel):
    subject: ScopedSubject
    source_generation_id: str = Field(min_length=1, max_length=160)
    source_plan_sha256: str = Field(pattern=SHA)
    logical_request_id: str = Field(min_length=1, max_length=200)
    receipt_sha256: str = Field(pattern=SHA)


class SecCoverCapture(ContractModel):
    reference: SecCoverReference
    raw: bytes = Field(min_length=1, max_length=MAX_SEC_DOCUMENT_BYTES)
    raw_sha256: str = Field(pattern=SHA)
    request_sha256: str = Field(pattern=SHA)
    issuer_cik: str = Field(pattern=r"^\d{10}$")
    filing_accession: str = Field(pattern=r"^\d{10}-\d{2}-\d{6}$")
    source_url: str
    source_form: Literal["10-K", "10-Q", "10-K/A", "10-Q/A", "20-F", "20-F/A"]
    source_as_of: date
    source_date_kind: Literal["SEC_FILING_DATE"] = "SEC_FILING_DATE"
    source_run_started_at: datetime
    requested_at: datetime
    received_at: datetime


class IdentityEvidenceUnavailable(ValueError):
    """Only these semantic reader denials may become ordinary missing receipts."""

    def __init__(self, reason):
        if reason not in {"REFERENCE_MISMATCH", "CAPTURE_MISSING", "CAPTURE_INVALID"}:
            raise ValueError("unsupported_identity_reader_denial")
        super().__init__(reason)


class TrustedIdentityReader(ABC):
    """Inject only from trusted backend code; never deserialize a reader.

    Resolve the reference against independently pinned original evidence, verify
    source generation, issuer, selected filing, request, final receipt and bytes,
    and enforce maximum_bytes BEFORE loading. Preserve original source clocks.
    Return None for a missing receipt. Do not fetch, consult a DB, or manufacture
    metadata from the requested reference. Implementations are outside this patch.
    Only IdentityEvidenceUnavailable is caught. Permission, filesystem, integrity
    and unexpected reader failures propagate to the caller's hard-stop handling.
    Even a reader replay success cannot issue current admission in this module.
    """

    @abstractmethod
    def read_sec_cover(self, reference: SecCoverReference, *, maximum_bytes: int) -> SecCoverCapture | None:
        raise NotImplementedError


class MissingReceipt(ContractModel):
    role: str
    receipt_type: Literal[
        "SEC_SECURITY_CLASSIFICATION", "OFFICIAL_CURRENT_LISTING", "LISTING_CURRENCY",
        "CORPORATE_ACTION_BASIS", "KR_ISSUER_SECURITY_LINK", "ETF_CLASSIFICATION",
        "MARKET_INSTRUMENT_IDENTITY", "INDEX_SOURCE_IDENTITY",
    ]
    reason: Literal[
        "OWNER_NOT_IMPLEMENTED", "REFERENCE_MISSING", "BACKEND_UNAVAILABLE",
        "CAPTURE_MISSING", "CAPTURE_INVALID",
        "REFERENCE_MISMATCH", "RAW_HASH_MISMATCH", "CLOCK_NAIVE",
        "SOURCE_TIME_ORDER", "SOURCE_GENERATION_CLOCK_MISMATCH", "FILING_STALE",
        "CAPTURE_STALE", "SEC_DOCUMENT_IDENTITY_MISMATCH", "ISSUER_MISMATCH",
        "SEC_OWNER_REJECTED", "SEC_CLASSIFICATION_MISMATCH", "OWNER_CONFLICT",
    ]


class SecOwnerReplay(ContractModel):
    reference: SecCoverReference
    claim: Literal["SEC_FILED_CLASSIFICATION_REPLAY_ONLY"] = "SEC_FILED_CLASSIFICATION_REPLAY_ONLY"
    source_as_of: date
    requested_at: datetime
    received_at: datetime
    raw_sha256: str
    request_sha256: str
    filing_accession: str
    source_url: str
    security_type: str
    share_class: str | None
    issuer_type: str
    exchange: str
    issuer_name: str
    sealed_issuer_names: tuple[str, ...]
    identity_discrepancies: tuple[Literal["ISSUER_NAME_DIFFERS_FROM_SEALED_RECORD"], ...]
    owner_action: str
    owner_result_sha256: str
    current_identity_authority: Literal[False] = False


class ScopedCurrentIdentityReview(ContractModel):
    contract: Literal["scoped-current-identity-review-v1"] = "scoped-current-identity-review-v1"
    status: Literal["NOT_ADMITTED"] = "NOT_ADMITTED"
    plan_sha256: str
    review_generation_id: str
    cutoff: datetime
    freshness: IdentityFreshnessPolicy
    partial_authority: tuple[SecOwnerReplay, ...]
    missing_receipts: tuple[MissingReceipt, ...] = Field(min_length=1)
    owner_files: tuple[tuple[str, str], ...]
    current_identity_authority: Literal[False] = False
    dispatch_allowed: Literal[False] = False
    source_use: Literal["NOT_ADMITTED"] = "NOT_ADMITTED"

    @property
    def review_sha256(self):
        return digest(self.model_dump(mode="json"))


class _Denied(ValueError):
    pass


def _utc(value):
    if value.utcoffset() is None:
        raise _Denied("CLOCK_NAIVE")
    return value.astimezone(timezone.utc)


def _replay_sec(capture, reference, security, *, compilation, cutoff, freshness):
    if not isinstance(capture, SecCoverCapture):
        raise _Denied("CAPTURE_INVALID")
    # Revalidate even model_copy/model_construct output from the backend.
    try:
        capture = SecCoverCapture.model_validate(capture.model_dump())
    except ValueError as exc:
        raise _Denied("CAPTURE_INVALID") from exc
    if capture.reference != reference:
        raise _Denied("REFERENCE_MISMATCH")
    if hashlib.sha256(capture.raw).hexdigest() != capture.raw_sha256:
        raise _Denied("RAW_HASH_MISMATCH")
    started, requested, received = map(_utc, (
        capture.source_run_started_at, capture.requested_at, capture.received_at))
    if not started <= requested <= received <= cutoff or capture.source_as_of > requested.date():
        raise _Denied("SOURCE_TIME_ORDER")
    if (reference.source_generation_id == compilation.generation_id
            and started != _utc(compilation.at)):
        raise _Denied("SOURCE_GENERATION_CLOCK_MISMATCH")
    if (cutoff - received).total_seconds() > freshness.maximum_capture_age_seconds:
        raise _Denied("CAPTURE_STALE")
    if (cutoff.date() - capture.source_as_of).days > freshness.maximum_filing_age_days:
        raise _Denied("FILING_STALE")
    subject = reference.subject
    if (subject.market != "us" or not re.fullmatch(r"\d{10}", subject.issuer_id)
            or capture.issuer_cik != subject.issuer_id):
        raise _Denied("ISSUER_MISMATCH")
    url = urlsplit(capture.source_url)
    prefix = f"/Archives/edgar/data/{int(subject.issuer_id)}/{capture.filing_accession.replace('-', '')}/"
    filename = url.path.removeprefix(prefix)
    if (url.scheme != "https" or url.netloc != "www.sec.gov" or url.query or url.fragment
            or not url.path.startswith(prefix) or not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*\.html?", filename)):
        raise _Denied("SEC_DOCUMENT_IDENTITY_MISMATCH")
    html = capture.raw.decode("utf-8")
    # The original parser takes CIK as metadata; independently require raw DEI CIK.
    contexts = sec_owner._inline_xbrl_facts(html)
    ciks = {str(row["EntityCentralIndexKey"]).strip().zfill(10)
            for row in contexts.values() if row.get("EntityCentralIndexKey")}
    if ciks != {subject.issuer_id}:
        raise _Denied("ISSUER_MISMATCH")
    evidence = sec_owner.parse_sec_cover_page_identity(html, ticker=subject.ticker,
        source_url=capture.source_url, filing_accession=capture.filing_accession,
        filing_date=capture.source_as_of.isoformat(), cik=capture.issuer_cik)
    sealed_names = tuple(dict.fromkeys(str(security[k]) for k in ("company_name", "legal_name")
                                     if security.get(k)))
    names = {" ".join(name.split()).casefold() for name in sealed_names}
    discrepancies = (() if " ".join(evidence.issuer_name.split()).casefold() in names
                     else ("ISSUER_NAME_DIFFERS_FROM_SEALED_RECORD",))
    # Inferred historical names are audit data, not authority over the SEC owner.
    if (evidence.exchange != subject.venue
            or (security.get("share_class") and evidence.share_class != security["share_class"])):
        raise _Denied("SEC_CLASSIFICATION_MISMATCH")
    reconciliation = sec_owner.OfficialSecurityIdentityService().plan(
        SecurityMaster.model_validate(security), evidence)
    if reconciliation["action"] == "conflict_no_write_existing_authoritative":
        raise _Denied("OWNER_CONFLICT")
    return SecOwnerReplay(reference=reference, source_as_of=capture.source_as_of,
        requested_at=capture.requested_at, received_at=capture.received_at,
        raw_sha256=capture.raw_sha256, request_sha256=capture.request_sha256,
        filing_accession=capture.filing_accession, source_url=capture.source_url,
        security_type=evidence.security_type, share_class=evidence.share_class,
        issuer_type=evidence.issuer_type, exchange=evidence.exchange,
        issuer_name=evidence.issuer_name, sealed_issuer_names=sealed_names,
        identity_discrepancies=discrepancies,
        owner_action=reconciliation["action"], owner_result_sha256=digest(reconciliation))


def review_scoped_current_identity(plan, *, compilation: ScopedCompilationInputs,
        reader: TrustedIdentityReader | None, sec_sources: tuple[SecCoverReference, ...],
        cutoff: datetime, freshness: IdentityFreshnessPolicy, enabled: bool = False):
    """Rebuild R30 structure and replay partial SEC authority; never issue admission.

    sec_sources are locators, not grants. Original source generation may differ
    from this review's generation, but must match the backend's sealed evidence.
    Old captures retain original clocks and must satisfy explicit freshness bounds.
    """
    if enabled is not True:
        raise ValueError("scoped_current_identity_feature_off")
    cutoff = _utc(cutoff)
    if cutoff < _utc(compilation.at):
        raise ValueError("scoped_identity_cutoff_before_plan")
    if reader is not None and not isinstance(reader, TrustedIdentityReader):
        raise TypeError("trusted_identity_reader_capability_required")
    freshness = IdentityFreshnessPolicy.model_validate(freshness.model_dump())
    plan = R22ScopedSourcePlanV1.model_validate(
        plan.model_dump(mode="json") if isinstance(plan, R22ScopedSourcePlanV1) else plan)
    validate_scoped_structure(plan, config=compilation.config, catalog=compilation.catalog,
        generation_id=compilation.generation_id, at=compilation.at, code_sha=compilation.code_sha,
        provider_config_sha256=compilation.provider_config_sha256, enabled=True)
    if len(sec_sources) > len(plan.identities):
        raise ValueError("scoped_sec_reference_bound")
    references = {}
    subjects = {b.subject.ticker: b.subject for b in plan.identities}
    for raw_ref in sec_sources:
        ref = SecCoverReference.model_validate(raw_ref.model_dump())
        if (ref.subject.market != "us" or subjects.get(ref.subject.ticker) != ref.subject
                or ref.subject.ticker in references):
            raise ValueError("scoped_sec_reference_scope_or_duplicate")
        references[ref.subject.ticker] = ref
    missing, partial = [], []

    def gap(role, kind, reason="OWNER_NOT_IMPLEMENTED"):
        missing.append(MissingReceipt(role=role, receipt_type=kind, reason=reason))

    for binding in plan.identities:
        subject = binding.subject
        role = "stock:" + subject.ticker
        for kind in ("OFFICIAL_CURRENT_LISTING", "LISTING_CURRENCY", "CORPORATE_ACTION_BASIS"):
            gap(role, kind)
        if subject.market == "kr":
            gap(role, "KR_ISSUER_SECURITY_LINK")
            continue
        reference = references.get(subject.ticker)
        if reference is None:
            gap(role, "SEC_SECURITY_CLASSIFICATION", "REFERENCE_MISSING")
            continue
        if reader is None:
            gap(role, "SEC_SECURITY_CLASSIFICATION", "BACKEND_UNAVAILABLE")
            continue
        try:
            capture = reader.read_sec_cover(reference, maximum_bytes=MAX_SEC_DOCUMENT_BYTES)
        except IdentityEvidenceUnavailable as exc:
            gap(role, "SEC_SECURITY_CLASSIFICATION", str(exc))
            continue
        if capture is None:
            gap(role, "SEC_SECURITY_CLASSIFICATION", "CAPTURE_MISSING")
            continue
        security = compilation.catalog.record(binding, at=compilation.at)
        try:
            partial.append(_replay_sec(capture, reference, security, compilation=compilation,
                cutoff=cutoff, freshness=freshness))
        except _Denied as exc:
            gap(role, "SEC_SECURITY_CLASSIFICATION", str(exc))
        except (ValueError, TypeError, KeyError):
            gap(role, "SEC_SECURITY_CLASSIFICATION", "SEC_OWNER_REJECTED")
    for pair in plan.price_pairs:
        if pair.instrument_kind == "INDEX":
            gap(pair.role, "INDEX_SOURCE_IDENTITY")
        elif pair.instrument_kind == "ETF_PROXY":
            for kind in ("ETF_CLASSIFICATION", "LISTING_CURRENCY", "CORPORATE_ACTION_BASIS"):
                gap(pair.role, kind)
    for symbol in plan.us_market_symbols:
        gap("us_market:" + symbol, "MARKET_INSTRUMENT_IDENTITY")
    owners = tuple((name, hashlib.sha256((ROOT / name).read_bytes()).hexdigest()) for name in OWNER_FILES)
    return ScopedCurrentIdentityReview(plan_sha256=plan.plan_sha256,
        review_generation_id=compilation.generation_id, cutoff=cutoff, freshness=freshness,
        partial_authority=tuple(partial), missing_receipts=tuple(missing), owner_files=owners)
