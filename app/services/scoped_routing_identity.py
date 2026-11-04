"""Trusted sealed routing catalog; historical identity is not current source authority."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Literal
import zipfile

from pydantic import Field

from app.models.security import SecurityMaster
from app.services.onboarding_readiness_service import _security_readiness
from app.services.unified_snapshot_contract import ContractModel, digest

SHA = r"^[a-f0-9]{64}$"


class RoutingCatalogPin(ContractModel):
    """Backend-selected audit trust root, never an output-model or request field."""
    archive_sha256: str = Field(pattern=SHA)
    member: str = Field(min_length=1)
    member_sha256: str = Field(pattern=SHA)
    predecessor_control_sha256: str = Field(pattern=SHA)


class ScopedSubject(ContractModel):
    ticker: str = Field(pattern=r"^[A-Z0-9.-]+$")
    market: Literal["kr", "us"]
    security_id: str = Field(min_length=1)
    issuer_id: str = Field(min_length=1)
    venue: Literal["KRX", "KOSPI", "KOSDAQ", "NASDAQ", "NYSE", "AMEX"]
    currency: Literal["KRW", "USD"]


class DetachedRoutingBinding(ContractModel):
    subject: ScopedSubject
    company_id: str
    security_type: str
    issuer_type: str
    source_generation: str
    original_identity_provider: str
    original_identity_quality: str
    record_sha256: str = Field(pattern=SHA)
    catalog_sha256: str = Field(pattern=SHA)
    assurance: Literal["VERIFIED_SEALED_STATIC_BINDING"] = "VERIFIED_SEALED_STATIC_BINDING"
    permitted_use: Literal["OFFLINE_CANONICAL_ROUTING_ONLY"] = "OFFLINE_CANONICAL_ROUTING_ONLY"
    current_identity_authority: Literal[False] = False


class SealedRoutingCatalog:
    """Live backend capability over a separately verified archive.

    The trusted composition root selects the pin. Matching bytes verify historical
    membership, not current official classification, market prices or source-use.
    No public field can turn this routing capability into current identity authority.
    """

    def __init__(self, *, archive: Path, pin: RoutingCatalogPin):
        archive = Path(archive)
        if any(p.is_symlink() for p in (archive, *archive.parents)):
            raise ValueError("scoped_catalog_symlink")
        if archive.stat().st_size > 100_000_000:
            raise ValueError("scoped_catalog_archive_budget")
        with archive.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != pin.archive_sha256:
                raise ValueError("scoped_catalog_archive_identity")
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or any(
                Path(n).is_absolute() or ".." in Path(n).parts for n in names
            ):
                raise ValueError("scoped_catalog_archive_paths")
            if sum(i.file_size for i in z.infolist()) > 256_000_000:
                raise ValueError("scoped_catalog_expansion_budget")
            if z.testzip() is not None:
                raise ValueError("scoped_catalog_crc")
            manifest = json.loads(z.read("manifest.json"))["files"]
            if set(names) != set(manifest) | {"manifest.json"}:
                raise ValueError("scoped_catalog_manifest_membership")
            for name, row in manifest.items():
                raw = z.read(name)
                if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                    raise ValueError("scoped_catalog_manifest_identity")
            raw = z.read(pin.member)
            if hashlib.sha256(raw).hexdigest() != pin.member_sha256:
                raise ValueError("scoped_catalog_member_identity")
            # The archive is already the trust anchor; require its control identity
            # to agree, rather than treating a caller's control label as authority.
            control_line = z.read("review-control-final/result.sha256").decode().splitlines()[0]
            if control_line != "CONTROL_SET_SHA256 " + pin.predecessor_control_sha256:
                raise ValueError("scoped_catalog_control_identity")
        self._raw = raw
        self._pin = pin

    @property
    def pin(self):
        return self._pin

    @property
    def catalog_sha256(self):
        return digest(self._pin.model_dump(mode="json"))

    def bind(self, subject: ScopedSubject, *, at: datetime) -> DetachedRoutingBinding:
        if at.utcoffset() is None:
            raise ValueError("scoped_timezone_required")
        catalog = json.loads(self._raw)
        row = catalog.get(subject.ticker)
        if not row or row.get("role") != "IDENTITY_ONLY_NOT_CURRENT_FINANCIAL_EVIDENCE":
            raise ValueError("scoped_identity_missing_or_not_routing")
        original = row["security"]
        required = ("ticker", "canonical_security_id", "canonical_company_id", "company_name",
            "exchange", "country", "security_type", "issuer_type", "identity_provider",
            "identity_quality", "updated_at", "corp_code" if subject.market == "kr" else "cik")
        if not isinstance(original, dict) or any(not original.get(k) for k in required):
            raise ValueError("scoped_explicit_sealed_identity_fields_required")
        security = SecurityMaster.model_validate(original)
        expected = (
            security.ticker, security.country.lower(), security.canonical_security_id,
            security.corp_code if subject.market == "kr" else security.cik, security.exchange,
            "KRW" if security.country == "KR" else "USD",
        )
        requested = (subject.ticker, subject.market, subject.security_id, subject.issuer_id,
                     subject.venue, subject.currency)
        if expected != requested:
            raise ValueError("scoped_security_issuer_market_venue_mismatch")
        allowed = {"kr": {"KRX", "KOSPI", "KOSDAQ"}, "us": {"NASDAQ", "NYSE", "AMEX"}}
        if subject.venue not in allowed[subject.market]:
            raise ValueError("scoped_venue_country_mismatch")
        valid, _, _ = _security_readiness(
            SimpleNamespace(ticker=subject.ticker, exchange=subject.venue), security, subject.market)
        updated = security.updated_at
        if (not valid or not row.get("source_generation") or updated is None
                or (updated.replace(tzinfo=timezone.utc) if updated.utcoffset() is None else updated) > at):
            raise ValueError("scoped_inherited_identity_owner_denied")
        return DetachedRoutingBinding(subject=subject, company_id=security.canonical_company_id,
            security_type=security.security_type, issuer_type=security.issuer_type,
            source_generation=row["source_generation"],
            original_identity_provider=security.identity_provider,
            original_identity_quality=security.identity_quality,
            record_sha256=digest(original), catalog_sha256=self.catalog_sha256)

    def record(self, binding: DetachedRoutingBinding, *, at: datetime) -> dict:
        if self.bind(binding.subject, at=at) != binding:
            raise ValueError("scoped_routing_receipt_mismatch")
        return json.loads(self._raw)[binding.subject.ticker]["security"]
