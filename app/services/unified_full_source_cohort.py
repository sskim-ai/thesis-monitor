"""Whole-source composition over existing independently replayed owners.

This does not accept a caller's PASS flag as source authority. Market components
are replayed by unified_source_composition and stock authority by its existing
stock/financial builders. No network or production registration lives here.
"""

from typing import Literal
from app.services.canonical_source_composition import SourceRunBinding


from app.services.unified_stock_acquisition import UNIVERSE


class FullSourceRunSeed(SourceRunBinding):
    contract: Literal["full-source-run-seed-v1"] = "full-source-run-seed-v1"
    proof_mode: Literal["AD_HOC_LIVE_SOURCE_PROOF", "SCHEDULED_ELIGIBLE_PROOF"]
    packet_scope: Literal["LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION"]

    @property
    def fresh_mode(self):
        return isinstance(self, FreshFullSourceRunSeed)

    @property
    def us_only(self):
        return isinstance(self, FreshUSSourceRunSeed)

    @property
    def kr_only(self):
        return isinstance(self, FreshKRSourceRunSeed)

    @property
    def cohort_metadata(self):
        return dict(contract="full-source-cohort-v1", model_dispatch_qualified=False,
                    production_dispatch_enabled=False)


class FreshFullSourceRunSeed(FullSourceRunSeed):
    """Opt-in extension; legacy run-seed serialization remains byte-compatible."""
    fresh_stock_owner_set_sha256: str


class FreshKRSourceRunSeed(FreshFullSourceRunSeed):
    scope: Literal["KR8_ONLY"] = "KR8_ONLY"

    @property
    def universe(self):
        return {"kr": UNIVERSE["kr"]}


class FreshUSSourceRunSeed(FreshFullSourceRunSeed):
    scope: Literal['US14_ONLY'] = 'US14_ONLY'
    topology: Literal['US14_WITH_DECLARED_AUXILIARY_ISSUER_V1'] = 'US14_WITH_DECLARED_AUXILIARY_ISSUER_V1'
    auxiliary_issuer_set_sha256: str

    @property
    def universe(self):
        return {'us':UNIVERSE['us']}


from app.services.canonical_source_composition import auxiliary_issuer_binding  # noqa: E402,F401


from app.services.canonical_source_composition import compose_source_owners as compose_full_source  # noqa: E402,F401
