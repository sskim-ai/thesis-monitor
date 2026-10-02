"""Explicit opt-in source policy; no settings or production registration."""

from dataclasses import dataclass
from collections.abc import Mapping


def source_identity(value: str) -> str:
    return "".join(c for c in value.casefold() if c.isalnum())


def prohibited_provider(value: str) -> bool:
    identity = source_identity(value)
    return (
        identity.startswith(("alphavantage", "massive", "mock"))
        or identity in {"polygon", "polygonio"}
    )


@dataclass(frozen=True)
class UnifiedSourcePolicy:
    """Closed, caller-declared provider set applies equally to calls and cache."""

    allowed_providers: frozenset[str]

    def permits(self, provider: str | None) -> bool:
        return bool(provider) and not prohibited_provider(provider) and source_identity(
            provider
        ) in {source_identity(p) for p in self.allowed_providers}

    def require(self, provider: str | None) -> None:
        if not self.permits(provider):
            raise ValueError("source_provider_not_authorized")

    def check_lineage(self, value: object) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"provider", "source_provider", "upstream_provider",
                           "provider_name", "selected_source_provider", "identity_provider"}:
                    self.require(child if isinstance(child, str) else None)
                else:
                    self.check_lineage(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                self.check_lineage(child)
