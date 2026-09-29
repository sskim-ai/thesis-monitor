"""Intersect existing source use, explicit family visibility, and A-stage shape."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from scripts.m12da_source_use_contract import canonical_sha256
from scripts.m12dk_current_source_authority import CONTRACT, POLICY_SHA256, family_rule, policy


class PassAVisibleEvidenceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: Literal["pass-a-visible-evidence-v1"] = "pass-a-visible-evidence-v1"
    ref_id: str
    source_ref: str
    source_family: str
    authority_state: str
    allowed_uses: tuple[str, ...]
    evidence_category: str
    current_stage: str
    explicit_family_visibility: str
    source_authority_contract: str | None
    source_family_policy_contract: str = CONTRACT
    source_family_policy_sha256: str = POLICY_SHA256
    stage_contract_permits: bool
    visible_to_pass_a: bool
    reason_code: str
    decision_sha256: str


def decide_pass_a_visibility(
    row: Mapping[str, object],
    *,
    authority: Mapping[str, object] | None,
    source_authority_contract: str | None,
    eligible_uses: Sequence[str],
    stage_contract_permits: bool,
    current_stage: str = "PASS_A",
    legacy_without_source_use: bool = False,
) -> PassAVisibleEvidenceDecision:
    """No authority grants: explicit family denials always dominate category aliases."""
    rule = family_rule(row)
    record = authority or {}
    denied_families = {r["id"] for r in policy()["family_rules"]
                       if r.get("pass_a_model_visible") is False}
    excluded = bool(rule and rule.get("pass_a_model_visible") is False) or (
        record.get("source_family") in denied_families
    )
    family = str(rule["id"] if rule else record.get("source_family") or "UNKNOWN")
    if record.get("source_family") in denied_families:
        family = str(record["source_family"])
    classification = "EXPLICITLY_EXCLUDED" if excluded else (
        "EXISTING_FAMILY_AUTHORITY_INTERSECTION" if rule else "EXISTING_SOURCE_AUTHORITY_INTERSECTION"
    )
    uses = tuple(sorted(set(str(u) for u in eligible_uses)))
    if current_stage != "PASS_A":
        reason = "WRONG_STAGE"
    elif excluded:
        reason = "EXPLICIT_FAMILY_PASS_A_EXCLUSION"
    elif not stage_contract_permits:
        reason = "PASS_A_STAGE_CONTRACT_EXCLUSION"
    elif not uses and not legacy_without_source_use:
        reason = "NO_AUTHORIZED_PASS_A_CONTEXT_USE"
    else:
        reason = "PASS_A_INTERSECTION_ALLOWED"
    payload = dict(contract="pass-a-visible-evidence-v1", ref_id=str(row.get("ref_id") or ""),
        source_ref=str(row.get("source_ref") or ""), source_family=family,
        authority_state=str(record.get("authority_state") or "LEGACY_NO_SOURCE_USE"),
        allowed_uses=uses, evidence_category=str(row.get("category") or ""),
        current_stage=current_stage, explicit_family_visibility=classification,
        source_authority_contract=source_authority_contract,
        source_family_policy_contract=CONTRACT, source_family_policy_sha256=POLICY_SHA256,
        stage_contract_permits=stage_contract_permits,
        visible_to_pass_a=reason == "PASS_A_INTERSECTION_ALLOWED", reason_code=reason)
    return PassAVisibleEvidenceDecision(**payload, decision_sha256=canonical_sha256(payload))
