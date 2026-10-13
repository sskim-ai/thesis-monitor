"""Explicit, hash-bound production protocol configuration; no historical roots."""
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_run_artifacts import durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest

SHA = r"^[a-f0-9]{64}$"


class ProtocolFile(ContractModel):
    path: str
    sha256: str = Field(pattern=SHA)
    purpose: Literal["PUBLIC_PROTOCOL", "PROTOCOL_CONTROL", "IDENTITY_ROUTING_ONLY"]

    def read(self):
        path = Path(self.path)
        if (not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
                or {"Reports", "tests", "fixtures"}.intersection(path.parts)):
            raise ValueError("production_protocol_path_not_deployed")
        raw = path.read_bytes()
        if sha256_bytes(raw) != self.sha256:
            raise ValueError("production_protocol_hash_mismatch")
        return raw


class ProductionSourceConfiguration(ContractModel):
    contract: Literal["production-source-configuration-v1"] = "production-source-configuration-v1"
    database_path: str
    native_owner_root: str
    native_python: str
    completed_close: ProtocolFile
    issuer_identity: ProtocolFile
    kr_listing_routing: ProtocolFile
    kis_protocols: dict[str, ProtocolFile]

    @model_validator(mode="after")
    def explicit_roots(self):
        for raw in (self.database_path, self.native_owner_root, self.native_python):
            path = Path(raw)
            if (not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents))
                    or {"Reports", "tests", "fixtures"}.intersection(path.parts)):
                raise ValueError("production_runtime_path_not_deployed")
        if not self.kis_protocols or any(Path(n).name != n or n in {".", ".."} for n in self.kis_protocols):
            raise ValueError("production_kis_protocol_names_invalid")
        if self.completed_close.purpose != "PUBLIC_PROTOCOL" or self.kr_listing_routing.purpose != "IDENTITY_ROUTING_ONLY":
            raise ValueError("production_static_role_invalid")
        return self

    def seal_protocols(self, root, market):
        """Only declared public/static inputs are copied, never old result packs."""
        from app.services.kiwoom_completed_close_owner import OFFICIAL_SPEC_SHA256
        root = Path(root)
        files = {"official-security-identity.json": self.issuer_identity}
        if market == "us":
            if self.completed_close.sha256 != OFFICIAL_SPEC_SHA256:
                raise ValueError("production_completed_close_protocol_not_qualified")
            files["completed-close-documentation.json"] = self.completed_close
        elif market == "kr":
            files["kr-list-routing.json"] = self.kr_listing_routing
            files.update({"kis/" + n: p for n, p in self.kis_protocols.items()})
        else:
            raise ValueError("production_market_invalid")
        for name, item in files.items():
            durable_bytes(root / "static" / name, item.read(), exclusive=True)
        return {n: dict(sha256=p.sha256, purpose=p.purpose) for n, p in files.items()}

    @property
    def identity(self):
        return digest(self.model_dump(mode="json"))
