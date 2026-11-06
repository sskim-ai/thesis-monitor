"""Trusted-backend fresh identity reader, not a serialized authority format."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime,timezone
import json
from pathlib import Path
import hashlib

from app.models.security import SecurityMaster
from app.services.unified_snapshot_contract import digest


@dataclass(frozen=True)
class FreshIdentityObservation:
    security_json: str
    provider: str
    received_at: datetime
    raw_sha256: str
    owner_receipt_sha256: str
    classification: str


class FreshRegisteredIdentityReader(ABC):
    """Inject only from trusted backend custody; re-run the original Owner.

    Implementations verify actual same-campaign HTTP receipts and raw bytes,
    then re-enter the original SEC or exact Kiwoom identity validator. They
    never return user/model supplied claimed validation results.
    """
    @abstractmethod
    def read(self, original: SecurityMaster) -> FreshIdentityObservation:
        raise NotImplementedError


class FreshIdentityUnavailable(ValueError):
    """Semantic absence only; permission/integrity errors must propagate."""
    def __init__(self,reason):
        if reason not in {'ORIGINAL_IDENTITY_OWNER_DENIED','FRESH_CAPTURE_MISSING'}:
            raise ValueError('unsupported_fresh_identity_absence')
        super().__init__(reason)


def resolve(reader,original,*,not_before):
    if not isinstance(reader,FreshRegisteredIdentityReader):
        raise ValueError('backend_fresh_identity_reader_required')
    observed=reader.read(original)
    if (type(observed) is not FreshIdentityObservation
            or observed.provider not in {'sec_official_identity','kiwoom'}
            or observed.classification!='QUALIFIED_EXACT_SECURITY'
            or observed.received_at.utcoffset() is None
            or not not_before<=observed.received_at<=datetime.now(timezone.utc)
            or any(len(s)!=64 or any(c not in '0123456789abcdef' for c in s)
                for s in (observed.raw_sha256,observed.owner_receipt_sha256))):
        raise ValueError('fresh_identity_original_owner_and_clock_required')
    current=SecurityMaster.model_validate(json.loads(observed.security_json))
    # New public provider classification cannot replace registration membership,
    # issuer linkage, or manufacture any original registration quality flag.
    keys=('ticker','canonical_security_id','canonical_company_id','exchange','country','cik','corp_code')
    if any(getattr(current,k)!=getattr(original,k) for k in keys):
        raise ValueError('fresh_identity_registered_core_conflict')
    if (current.identity_quality!=original.identity_quality
            or current.identity_provider!=original.identity_provider
            or current.updated_at!=original.updated_at):
        raise ValueError('fresh_identity_registration_flags_unchanged_required')
    if current.model_dump(mode='json')!=original.model_dump(mode='json'):
        raise ValueError('fresh_identity_all_registration_metadata_unchanged_required')
    implementation=Path(reader.read.__func__.__code__.co_filename)
    if not implementation.is_file() or implementation.is_symlink():
        raise ValueError('fresh_identity_backend_source_required')
    proof=dict(contract='fresh-official-source-intake-identity-v1',provider=observed.provider,
        received_at=observed.received_at.isoformat(),raw_sha256=observed.raw_sha256,
        owner_receipt_sha256=observed.owner_receipt_sha256,public_identity_sha256=digest(json.loads(observed.security_json)),
        reader_code_sha256=hashlib.sha256(implementation.read_bytes()).hexdigest(),
        resolver_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_only=True,production=False,financial_use=False,per_share_use=False)
    return current,proof
