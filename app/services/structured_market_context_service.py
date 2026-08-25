from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.services.market_cross_section_service import MarketCrossSection


STRUCTURED_MARKET_CONTEXT_VERSION = "structured-market-context-v1"
PublicationState = Literal[
    "AVAILABLE_CURRENT",
    "AVAILABLE_PRIOR_SESSION",
    "PUBLICATION_PENDING",
    "PARTIAL",
    "UNAVAILABLE",
]


class StructuredMarketContextEnvelope(BaseModel):
    contract_version: Literal["structured-market-context-v1"] = (
        STRUCTURED_MARKET_CONTEXT_VERSION
    )
    market: Literal["KR", "US"]
    session_date: date
    retrieved_at: datetime
    provider: str
    publication_state: PublicationState
    source_refs: list[str] = Field(default_factory=list)
    source_payload_sha256: str | None = None
    cross_section: MarketCrossSection | None = None
    data_gaps: list[str] = Field(default_factory=list)
    evidence_class: Literal[
        "PRODUCTION_STRUCTURED_EVIDENCE",
        "SUPPLEMENTAL_STRUCTURED_EVIDENCE",
    ] = "PRODUCTION_STRUCTURED_EVIDENCE"

    @model_validator(mode="after")
    def validate_envelope(self) -> "StructuredMarketContextEnvelope":
        if self.retrieved_at.tzinfo is None:
            raise ValueError("structured market retrieval time must be timezone-aware")
        if self.publication_state == "AVAILABLE_CURRENT":
            if self.cross_section is None:
                raise ValueError("available structured context requires a cross-section")
            if self.cross_section.market != self.market:
                raise ValueError("structured market context market mismatch")
            if self.cross_section.session_date != self.session_date:
                raise ValueError("structured market context session mismatch")
        if self.cross_section is not None and (
            self.cross_section.market != self.market
            or self.cross_section.session_date != self.session_date
        ):
            raise ValueError("cross-section identity does not match the envelope")
        return self


def default_structured_market_context_directory() -> Path:
    return Path(get_settings().data_dir) / "market-context" / "structured"


def structured_market_context_path(
    market: str,
    session_date: date,
    *,
    directory: Path | None = None,
) -> Path:
    normalized = market.strip().upper()
    if normalized not in {"KR", "US"}:
        raise ValueError(f"unsupported market: {market}")
    root = directory or default_structured_market_context_directory()
    return root / normalized.lower() / f"{session_date.isoformat()}.json"


def persist_structured_market_context(
    envelope: StructuredMarketContextEnvelope,
    *,
    directory: Path | None = None,
) -> Path:
    path = structured_market_context_path(
        envelope.market,
        envelope.session_date,
        directory=directory,
    )
    payload = envelope.model_dump(mode="json")
    encoded_payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    document = {
        "envelope": payload,
        "envelope_sha256": hashlib.sha256(encoded_payload).hexdigest(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return path


def load_structured_market_context(
    market: str,
    session_date: date,
    *,
    cutoff: datetime,
    directory: Path | None = None,
) -> StructuredMarketContextEnvelope | None:
    if cutoff.tzinfo is None:
        raise ValueError("structured market context cutoff must be timezone-aware")
    path = structured_market_context_path(
        market,
        session_date,
        directory=directory,
    )
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("envelope"), dict):
        raise ValueError("structured market context cache envelope is invalid")
    payload = raw["envelope"]
    encoded_payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if raw.get("envelope_sha256") != hashlib.sha256(encoded_payload).hexdigest():
        raise ValueError("structured market context cache hash mismatch")
    envelope = StructuredMarketContextEnvelope.model_validate(payload)
    if envelope.market != market.strip().upper() or envelope.session_date != session_date:
        raise ValueError("structured market context cache identity mismatch")
    if envelope.retrieved_at > cutoff:
        return None
    return envelope


def load_current_cross_section(
    market: str,
    session_date: date,
    *,
    cutoff: datetime,
    directory: Path | None = None,
) -> MarketCrossSection | None:
    envelope = load_structured_market_context(
        market,
        session_date,
        cutoff=cutoff,
        directory=directory,
    )
    if (
        envelope is None
        or envelope.publication_state != "AVAILABLE_CURRENT"
        or envelope.cross_section is None
    ):
        return None
    section = envelope.cross_section
    if section.quality.freshness != "fresh" or section.as_of > cutoff:
        return None
    return section
