"""Exact code identity shared by whole-source producers, consumers and replay.

Roles describe code ownership only; they grant no source-use authority.
The legacy profile preserves the original four-file persisted-source contract.
"""
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_run_artifacts import sha256_bytes

VERSION = "whole-source-code-owner-registry-v1"
SEMANTIC_ID = "whole-source-code-identity"
Profile = Literal["fresh", "fresh_kr8", "fresh_us14", "legacy"]

# The only inventory. The final flag selects the pre-fresh legacy contract.
_OWNER_SPECS = (
    ("app/services/bounded_financial_projection.py", "financial_projection", False),
    ("app/services/bounded_financial_stock_owner.py", "stock_financial_owner", False),
    ("app/services/canonical_business_quality_owner.py", "financial_quality", False),
    ("app/services/current_effective_technical.py", "current_effective_technical", False),
    ("app/services/current_fresh_valuation.py", "fresh_valuation", False),
    ("app/services/provider_native_valuation_snapshot.py", "provider_native_valuation_snapshot", False),
    ("app/services/provider_native_valuation_acquisition.py", "provider_native_valuation_acquisition", False),
    ("app/services/provider_valuation_calibration_context.py", "provider_valuation_calibration_context", False),
    ("app/services/fresh_event_carrier.py", "fresh_event", False),
    ("app/services/fresh_financial_stock_owner.py", "fresh_stock_financial_owner", False),
    ("app/services/fpi_filing_document_graph.py", "filing_purpose_and_slot_owner", False),
    ("app/services/fresh_publication_replay.py", "publication_macro", False),
    ("app/services/fresh_valuation_capability.py", "valuation_capability", False),
    ("app/services/latest_published_fx.py", "latest_published_fx", False),
    ("app/services/market_display_view.py", "market_display_permission", False),
    ("app/services/market_display_plan.py", "market_display_materialization", False),
    ("app/services/persisted_business_event_owner.py", "persisted_event", True),
    ("app/services/selected_financial_owner.py", "selected_financial_owner", False),
    ("app/services/security_valuation_basis.py", "security_valuation_basis", False),
    ("app/services/sec_logical_cell_reference.py", "sec_logical_reference_structure", False),
    ("app/services/unified_full_source_cohort.py", "full_source_composition", True),
    ("app/services/unified_sealed_context.py", "sealed_context", True),
    ("app/services/unified_stock_event_input.py", "stock_event_input", False),
    ("scripts/m12dr_financial_source_authority.py", "financial_source_authority", True),
    ("scripts/r2b_r5_market_adapter.py", "market_source_projection", False),
    ("scripts/r9_rev11_market_qualification.py", "market_display_qualification", False),
    ("scripts/r9_offline_stage_replay.py", "market_capture_binding", False),
)
_KR8_OWNER_SPECS = (
    ("scripts/kr8_fy1_models.py", "kr8_model_scope_and_visibility", False),
    ("app/services/kr_forward_valuation_context.py", "kr8_forward_valuation_context", False),
    ("app/services/kr_forward_valuation_message.py", "kr8_forward_valuation_renderer", False),
    ("scripts/kr8_source_scope.py", "kr8_acquisition_scope", False),
    ("scripts/kr8_kis_integration.py", "kr8_fresh_kis_integration", False),
    ("scripts/kis_output3_protocol_owner.py", "kis_fy1_protocol_owner", False),
    ("scripts/kis_fy1_semantic_owner.py", "kis_fiscal_security_owner", False),
    ("scripts/kis_current_fy1_owner.py", "kis_current_fy1_fper_owner", False),
    ("scripts/kis_exact_action_guard.py", "kis_exact_security_action_owner", False),
)
_US14_OWNER_SPECS = (
    ('app/services/auxiliary_issuer_financial_owner.py', 'auxiliary_issuer_only', False),
    ('scripts/us14_source_scope.py', 'us14_acquisition_scope', False),
    ('scripts/us14_models.py', 'us14_model_and_capture_scope', False),
    ('scripts/fresh_source_only_export.py', 'us14_source_only_export', False),
)


def _specs(profile):
    if profile not in ("fresh", "fresh_kr8", "fresh_us14", "legacy"):
        raise ValueError("whole_source_registry_profile_unknown")
    specs = _OWNER_SPECS + (_KR8_OWNER_SPECS if profile == "fresh_kr8" else _US14_OWNER_SPECS if profile == 'fresh_us14' else ())
    return {path: role for path, role, legacy in specs if profile != "legacy" or legacy}


def _file_hash(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
        raise ValueError("whole_source_registry_unsafe_path")
    root = Path(root).resolve()
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("whole_source_registry_symlink")
    if not current.is_file() or not current.resolve().is_relative_to(root):
        raise ValueError("whole_source_registry_missing_file")
    return sha256_bytes(current.read_bytes())


class WholeSourceCodeOwner(ContractModel):
    path: str
    role: str
    mandatory: Literal[True] = True
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    registry_version: Literal["whole-source-code-owner-registry-v1"] = VERSION
    semantic_registry_id: Literal["whole-source-code-identity"] = SEMANTIC_ID


class WholeSourceCodeOwnerRegistry(ContractModel):
    registry_version: Literal["whole-source-code-owner-registry-v1"] = VERSION
    semantic_registry_id: Literal["whole-source-code-identity"] = SEMANTIC_ID
    profile: Profile = "fresh"
    entries: tuple[WholeSourceCodeOwner, ...]

    @model_validator(mode="after")
    def exact_inventory(self):
        paths = [entry.path for entry in self.entries]
        expected = _specs(self.profile)
        if len(paths) != len(set(paths)):
            raise ValueError("whole_source_registry_duplicate_path")
        if set(paths) != set(expected):
            raise ValueError("whole_source_registry_exact_set_mismatch")
        if any(entry.role != expected[entry.path] for entry in self.entries):
            raise ValueError("whole_source_registry_role_mismatch")
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda entry: entry.path)))
        return self

    @classmethod
    def freeze(cls, root, *, profile: Profile = "fresh"):
        return cls(profile=profile, entries=tuple(
            WholeSourceCodeOwner(path=path, role=role, file_sha256=_file_hash(root, path))
            for path, role in _specs(profile).items()))

    @property
    def fingerprints(self):
        return {entry.path: entry.file_sha256 for entry in self.entries}

    @property
    def sha256(self):
        return digest(self.model_dump(mode="json"))

    @property
    def seed_bindings(self):
        return dict(code_config_sha256=self.sha256, source_authority_contract_sha256=self.sha256)

    def verify(self, root, *, fingerprints, expected_sha256, profile: Profile = "fresh"):
        current = type(self).freeze(root, profile=profile)
        if (self != current or fingerprints != current.fingerprints
                or expected_sha256 != current.sha256):
            raise ValueError("whole_source_code_contract_identity_mismatch")
        return current


def verify_fresh_code_identity(root, *, metadata, code_sha256, authority_sha256, profile="fresh"):
    registry = WholeSourceCodeOwnerRegistry.model_validate(metadata.get("code_owner_registry"))
    verified = registry.verify(root, fingerprints=metadata.get("code_fingerprints"),
                               expected_sha256=code_sha256, profile=profile)
    if authority_sha256 != verified.sha256:
        raise ValueError("whole_source_code_contract_identity_mismatch")
    return verified


def replay_identity_receipt(root, *, seed, metadata, first, second):
    profile = {'KR8_ONLY':'fresh_kr8', 'US14_ONLY':'fresh_us14'}.get(getattr(seed,'scope',None),'fresh')
    registry = verify_fresh_code_identity(root, metadata=metadata,
        code_sha256=seed.code_config_sha256, authority_sha256=seed.source_authority_contract_sha256, profile=profile)
    identities = dict(seed_registry_sha256=seed.code_config_sha256,
        producer_registry_sha256=registry.sha256, consumer_registry_sha256=registry.sha256)
    for label, replay in (("replay1", first), ("replay2", second)):
        contract = replay["authority_graph"]["source_contract"]
        replay_registry = verify_fresh_code_identity(root, metadata=contract,
            code_sha256=replay["seed"]["code_config_sha256"],
            authority_sha256=replay["seed"]["source_authority_contract_sha256"], profile=profile)
        identities[label + "_registry_sha256"] = replay_registry.sha256
    if set(identities.values()) != {registry.sha256}:
        raise ValueError("whole_source_registry_replay_identity_mismatch")
    return dict(registry_version=registry.registry_version, registry=registry.model_dump(mode="json"),
        paths=list(registry.fingerprints), per_file_sha256=registry.fingerprints,
        aggregate_registry_sha256=registry.sha256, **identities, status="PASS")
