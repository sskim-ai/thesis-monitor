from __future__ import annotations

import re

from app.services.configured_signal_evidence_service import (
    configured_signal_source_role,
)
from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from app.services.financial_framework_claim_service import financial_frameworks_in_text
from app.services.logical_condition_service import CheckpointMetric


CONTRACT_VERSION = "configured-financial-support-concept-v1"

_EXPLICIT_FREE_CASH_FLOW_LANGUAGE = re.compile(
    r"(?<![A-Za-z0-9_])FCF(?![A-Za-z0-9_])|"
    r"\bfree[ -]cash[ -]flow\b|"
    r"잉여현금흐름",
    re.IGNORECASE,
)
_OCF_PPE_PROXY_LANGUAGE = re.compile(
    r"\bocf\b[^.!?;:\n]{0,40}\bppe\b|"
    r"ocf_less_ppe_capex|"
    r"현금\s*전환\s*대용치|"
    r"cash[- ]conversion\s+proxy",
    re.IGNORECASE,
)


def configured_financial_support_concepts(
    ref: DecisionEvidenceRef,
) -> frozenset[str]:
    """Return bounded financial concepts named by one configured signal.

    This support vocabulary identifies what a configured future condition is
    about. It does not establish that the condition is currently fulfilled.
    """

    if configured_signal_source_role(ref) is None:
        return frozenset()

    evidence_text = f"{ref.label} {ref.statement}"
    concepts = set(financial_frameworks_in_text(evidence_text))
    structured_metrics = (
        ref.logical_condition.metric_refs
        if ref.logical_condition is not None
        else ref.metric_refs
    )
    proxy_only = _OCF_PPE_PROXY_LANGUAGE.search(evidence_text) is not None
    if not proxy_only and CheckpointMetric.FCF in structured_metrics:
        concepts.add("free_cash_flow")
    elif (
        not proxy_only
        and not structured_metrics
        and _EXPLICIT_FREE_CASH_FLOW_LANGUAGE.search(evidence_text) is not None
    ):
        concepts.add("free_cash_flow")
    return frozenset(concepts)
