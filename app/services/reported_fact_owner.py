"""Opt-in sealed SEC fact admission; never a ticker-to-investment policy.

The backend creates this capability from independently sealed acquisition bytes
and registration ownership. Request callers receive receipts, not the registry.
Same-process hostile Python and durable production transport are outside this
in-memory capability boundary. No live service imports this module by default.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
import secrets
from typing import Literal

from pydantic import Field

from app.services.economic_interpretation_policy import ReportedComparisonInput, ReportedStatementInput
from app.services.native_input_admission import Closed, Identity, SHA, UseState
from app.services.sec_business_field_quality_service import reported_comparison_quality, sha
from app.services.unified_snapshot_contract import digest

CONTRACT = "backend-sealed-reported-fact-owner-v1"
POLICY = "sec-business-field-quality-v1:reported-comparison-only"
AXES = ("DISPLAY", "CORE_CONTEXT", "CORE_DIRECTION", "OVERALL_DIRECTION", "HOLDER_CONTEXT",
        "HOLDER_DIRECTION", "NEWBUYER_CONTEXT", "NEWBUYER_DIRECTION")


class RegisteredIssuerBinding(Closed):
    security_id: Identity
    ticker: Identity
    issuer_id: Identity
    market: Identity
    exchange: Identity
    security_type: Identity
    registration_owner_ref: Identity
    registration_artifact_sha256: SHA
    source_generation_id: Identity
    execution_generation_id: Identity
    cutoff: date


class FactUseGrant(Closed):
    axis: Literal["DISPLAY", "CORE_CONTEXT", "CORE_DIRECTION", "OVERALL_DIRECTION", "HOLDER_CONTEXT",
                  "HOLDER_DIRECTION", "NEWBUYER_CONTEXT", "NEWBUYER_DIRECTION"]
    state: UseState
    policy_ref: Identity | None


class ReportedFact(Closed):
    security_id: Identity
    ticker: Identity
    issuer_id: Identity
    execution_generation_id: Identity
    source_generation_id: Identity
    filing_accession: Identity
    filing_form: Literal["10-Q", "10-K", "20-F", "6-K"]
    filed: date
    field: Literal["revenue", "operating_income"]
    concept: Identity
    taxonomy: Identity
    occurrence_ordinal: int = Field(ge=0)
    occurrence_sha256: SHA
    source_row_identity: SHA
    value: float = Field(allow_inf_nan=False, strict=True)
    period_start: date
    period_end: date
    duration_days: int = Field(gt=0)
    currency: Identity
    statement_basis: Literal["sec_companyfacts_entity_wide"] = "sec_companyfacts_entity_wide"
    share_basis: Literal["NOT_PER_SHARE"] = "NOT_PER_SHARE"
    raw_source_sha256: SHA
    normalized_source_sha256: SHA
    discovery_source_sha256: SHA


class FactAdmission(Closed):
    contract: Literal["backend-sealed-reported-fact-owner-v1"] = CONTRACT
    admission_id: Identity
    fact: ReportedFact
    owner_ref: Identity
    owner_evidence_sha256: SHA
    policy_version: Literal["sec-business-field-quality-v1:reported-comparison-only"] = POLICY
    grants: tuple[FactUseGrant, ...]
    admission_sha256: SHA


class ReportedPolicyResult(Closed):
    policy_version: Literal["sec-business-field-quality-v1:reported-comparison-only"] = POLICY
    security_id: Identity
    execution_generation_id: Identity
    source_generation_id: Identity
    supporting_admission_ids: tuple[Identity, Identity]
    supporting_admission_sha256: tuple[SHA, SHA]
    source_owner_sha256: SHA
    factual_direction: Literal["UP", "DOWN", "FLAT"]
    delta: float = Field(allow_inf_nan=False)
    growth_pct: float | None = Field(allow_inf_nan=False)
    qualification: Literal["QUALIFIED_FACT_COMPARISON_ONLY"] = "QUALIFIED_FACT_COMPARISON_ONLY"
    economic_interpretation: Literal["REPORTED_PERIOD_CHANGE_ONLY"] = "REPORTED_PERIOD_CHANGE_ONLY"
    permitted_core_roles: tuple[()] = ()
    materiality: Literal["MATERIALITY_POLICY_AUTHORITY_GAP"] = "MATERIALITY_POLICY_AUTHORITY_GAP"
    causal_relevance: Literal["NOT_ESTABLISHED_BY_FACT_AUTHENTICITY"] = "NOT_ESTABLISHED_BY_FACT_AUTHENTICITY"
    counterevidence_synthesis: Literal["POLICY_AUTHORITY_GAP"] = "POLICY_AUTHORITY_GAP"
    confidence_ceiling: None = None
    confidence_state: Literal["ECONOMIC_CONFIDENCE_NOT_AUTHORIZED"] = "ECONOMIC_CONFIDENCE_NOT_AUTHORIZED"
    interpretation_sha256: SHA


class BackendReportedFactOwner:
    """Backend-only constructor; raw anchors must come from sealed owner storage.

    No method accepts a caller-provided 'approved' flag or capsule digest as
    authority. Every admitted claim is matched against raw SEC occurrences and
    a backend-held exact comparison. A new registry cannot resolve old receipts.
    DISPLAY is the existing field-quality prose eligibility, not a Core grant.
    """

    def __init__(self, *, registration: RegisteredIssuerBinding, artifacts: dict[str, bytes],
                 trusted_artifact_sha256: dict[str, str], comparison: ReportedComparisonInput):
        required = {"companyfacts", "discovery", "companyfacts_receipt", "discovery_receipt", "registration"}
        if set(artifacts) != required or set(trusted_artifact_sha256) != required:
            raise ValueError("EXACT_BACKEND_SOURCE_ANCHORS_REQUIRED")
        parsed = {}
        for name in sorted(required):
            if type(artifacts[name]) is not bytes:
                raise ValueError("EXACT_SOURCE_BYTES_REQUIRED")
            if hashlib.sha256(artifacts[name]).hexdigest() != trusted_artifact_sha256[name]:
                raise ValueError("INDEPENDENT_SOURCE_ANCHOR_MISMATCH")
            parsed[name] = json.loads(artifacts[name])
        registration = RegisteredIssuerBinding.model_validate(registration.model_dump(mode="json"))
        comparison = ReportedComparisonInput.model_validate(comparison.model_dump(mode="json"))
        raw, discovery = (parsed[k] for k in ("companyfacts", "discovery"))
        r = registration
        records = parsed["registration"]["roles"]["security_identity"]["records"]
        matching = [item["record"] for item in records
                    if item["record"].get("canonical_security_id") == r.security_id]
        if len(matching) != 1:
            raise ValueError("EXACT_REGISTERED_SECURITY_REQUIRED")
        reg = matching[0]
        if (reg["canonical_security_id"], reg["ticker"], str(int(reg["cik"]))) != (
                r.security_id, r.ticker, str(int(r.issuer_id))):
            raise ValueError("REGISTERED_SECURITY_ISSUER_MISMATCH")
        if trusted_artifact_sha256["registration"] != r.registration_artifact_sha256:
            raise ValueError("REGISTRATION_OWNER_ARTIFACT_MISMATCH")
        if (reg["security_type"], reg["exchange"].upper(), reg["country"].upper()) != (
                r.security_type, r.exchange.upper(), r.market.upper()):
            raise ValueError("REGISTERED_SECURITY_BASIS_MISMATCH")
        if str(int(raw["cik"])) != str(int(r.issuer_id)) or str(int(discovery["cik"])) != str(int(r.issuer_id)):
            raise ValueError("OFFICIAL_ISSUER_MISMATCH")
        pairs = list(zip(discovery["tickers"], discovery["exchanges"], strict=True))
        if (r.ticker, r.exchange.upper()) not in [(t, e.upper()) for t, e in pairs]:
            raise ValueError("OFFICIAL_SECURITY_EXCHANGE_BINDING_MISSING")
        for source in ("companyfacts", "discovery"):
            receipt = parsed[source+"_receipt"]
            if (receipt["status"] != "PASS" or receipt["raw_sha256"] != trusted_artifact_sha256[source]
                    or receipt["generation_id"] != r.source_generation_id
                    or receipt["logical_request_id"] != f"financial:{r.ticker}:{source}"
                    or receipt["role"] != f"financial:{r.ticker}"):
                raise ValueError("ACQUISITION_OWNER_GENERATION_MISMATCH")
        if (comparison.security_id, comparison.ticker, comparison.generation_id,
                comparison.source_generation_id, comparison.cutoff) != (
                r.security_id, r.ticker, r.execution_generation_id, r.source_generation_id, r.cutoff):
            raise ValueError("COMPARISON_SECURITY_GENERATION_MISMATCH")
        if set(comparison.source_artifact_sha256) != {sha(raw)}:
            raise ValueError("COMPARISON_SOURCE_IDENTITY_MISMATCH")
        # Rebuild the existing field-quality projection from sealed raw bytes.
        # Rehashing a selected occurrence must not hide another conflicting one.
        from app.services.sec_financial_snapshot_service import _companyfacts_snapshots

        projected = _companyfacts_snapshots(raw, r.ticker)
        for statement in (comparison.formal, comparison.comparison):
            matches = [p for p in projected if (p.source_filing_id, p.filing_date,
                p.financial_period_end, p.period_scope) == (statement.source_filing_id,
                statement.filing_date, statement.financial_period_end, statement.period_scope)]
            if len(matches) != 1:
                raise ValueError("INDEPENDENT_STATEMENT_PROJECTION_MISSING_OR_CONFLICTING")
            independent = ReportedStatementInput(**{k:getattr(matches[0],k)
                                                    for k in ReportedStatementInput.model_fields})
            if independent != statement:
                raise ValueError("INDEPENDENT_STATEMENT_PROJECTION_MISMATCH")
        quality = reported_comparison_quality(formal=comparison.formal, comparison=comparison.comparison,
                                             ticker=r.ticker, cutoff=r.cutoff)
        if quality["status"] != "PASS":
            raise ValueError("COMPARISON_QUALITY_NOT_QUALIFIED")
        recent = discovery["filings"]["recent"]
        self._facts = {}
        for side, statement in (("current", comparison.formal), ("comparison", comparison.comparison)):
            fields = json.loads(statement.raw_financial_fields)
            for observation in quality["comparative_observations"]:
                field = observation["metric"]
                matches = [f for f in fields if f.get("field") == field]
                if len(matches) != 1:
                    raise ValueError("EXACT_RAW_FACT_WITNESS_REQUIRED")
                w = matches[0]
                ordinal = w["source_row_ordinal"]
                if type(ordinal) is not int or ordinal < 0:
                    raise ValueError("INVALID_OCCURRENCE_ORDINAL")
                occurrence = raw["facts"][w["taxonomy"]][w["concept"]]["units"][w["unit"]][ordinal]
                enriched = dict(occurrence, _unit=w["unit"], _concept=w["concept"],
                                _taxonomy=w["taxonomy"], _source_row_ordinal=ordinal)
                if (sha(raw) != w["source_payload_sha256"]
                        or sha(dict(cik=raw["cik"], field=field, occurrence=enriched)) != w["source_row_identity"]
                        or occurrence["val"] != w["source_reported_value"]
                        or occurrence["accn"] != w["source_document_id"]
                        or occurrence["form"] != w["source_document_type"]
                        or occurrence["filed"] != w["source_filing_date"]
                        or occurrence["start"] != w["period_start"] or occurrence["end"] != w["period_end"]
                        or w["currency"] != w["unit"] or str(w["issuer_cik"]) != str(raw["cik"])):
                    raise ValueError("RAW_FACT_OCCURRENCE_BINDING_MISMATCH")
                indices = [i for i,a in enumerate(recent["accessionNumber"]) if a == occurrence["accn"]]
                if len(indices) != 1:
                    raise ValueError("OFFICIAL_FILING_ACCESSION_MISSING_OR_CONFLICTING")
                idx = indices[0]
                if (recent["form"][idx], recent["filingDate"][idx]) != (occurrence["form"], occurrence["filed"]):
                    raise ValueError("OFFICIAL_FILING_BASIS_MISMATCH")
                start, end, filed = (date.fromisoformat(occurrence[k]) for k in ("start", "end", "filed"))
                if not start < end <= filed <= r.cutoff or (end-start).days != w["duration_days"]:
                    raise ValueError("FACT_TEMPORAL_BINDING_MISMATCH")
                self._facts[(side, field)] = ReportedFact(
                    security_id=r.security_id, ticker=r.ticker, issuer_id=r.issuer_id,
                    execution_generation_id=r.execution_generation_id, source_generation_id=r.source_generation_id,
                    filing_accession=occurrence["accn"], filing_form=occurrence["form"], filed=filed,
                    field=field, concept=w["concept"], taxonomy=w["taxonomy"], occurrence_ordinal=ordinal,
                    occurrence_sha256=digest(occurrence), source_row_identity=w["source_row_identity"],
                    value=occurrence["val"], period_start=start, period_end=end, duration_days=(end-start).days,
                    currency=w["currency"], raw_source_sha256=trusted_artifact_sha256["companyfacts"],
                    normalized_source_sha256=sha(raw), discovery_source_sha256=trusted_artifact_sha256["discovery"])
        self._registration = r
        self._quality = quality
        self._owner_sha = digest(dict(registration=r.model_dump(mode="json"), artifacts=trusted_artifact_sha256,
                                      quality=quality["receipt_sha256"], contract=CONTRACT))
        self._admitted = {}
        self._interpretations = {}

    @property
    def facts(self):
        return tuple(self._facts.values())

    @property
    def registration(self):
        return RegisteredIssuerBinding.model_validate(self._registration.model_dump(mode="json"))

    def admit(self, value: ReportedFact) -> FactAdmission:
        value = ReportedFact.model_validate(value.model_dump(mode="json"))
        if value not in self._facts.values():
            raise ValueError("UNADMITTED_FACT_CAPSULE")
        grants = tuple(FactUseGrant(axis=a, state=UseState.ALLOWED if a == "DISPLAY" else UseState.UNSPECIFIED,
                                   policy_ref=POLICY if a == "DISPLAY" else None) for a in AXES)
        payload = dict(admission_id=secrets.token_hex(32), fact=value, owner_ref=CONTRACT,
                       owner_evidence_sha256=self._owner_sha, grants=grants)
        admission = FactAdmission(**payload, admission_sha256=digest(dict(
            fact=value.model_dump(mode="json"), owner=self._owner_sha,
            grants=[g.model_dump(mode="json") for g in grants], admission_id=payload["admission_id"])))
        self._admitted[admission.admission_id] = admission.model_dump_json()
        return admission

    def resolve(self, admission: FactAdmission, *, axis: str, security_id: str,
                execution_generation_id: str, source_generation_id: str) -> ReportedFact:
        if not isinstance(admission, FactAdmission):
            raise ValueError("ISSUED_FACT_ADMISSION_REQUIRED")
        if self._admitted.get(admission.admission_id) != admission.model_dump_json():
            raise ValueError("UNISSUED_OR_CHANGED_FACT_ADMISSION")
        fact = admission.fact
        if (security_id, execution_generation_id, source_generation_id) != (
                fact.security_id, fact.execution_generation_id, fact.source_generation_id):
            raise ValueError("FACT_REQUEST_IDENTITY_MISMATCH")
        if not any(g.axis == axis and g.state == UseState.ALLOWED for g in admission.grants):
            raise ValueError("FACT_USE_GRANT_MISSING")
        return fact

    def compare(self, current: FactAdmission, prior: FactAdmission) -> ReportedPolicyResult:
        r = self._registration
        for a in (current, prior):
            self.resolve(a, axis="DISPLAY", security_id=r.security_id,
                         execution_generation_id=r.execution_generation_id, source_generation_id=r.source_generation_id)
        match = next((o for o in self._quality["comparative_observations"] if
            o["current"]["lineage"]["source_row_identity"] == current.fact.source_row_identity and
            o["comparison"]["lineage"]["source_row_identity"] == prior.fact.source_row_identity), None)
        if match is None:
            raise ValueError("EXACT_COMPARISON_MEMBERSHIP_REQUIRED")
        body = dict(security_id=r.security_id, execution_generation_id=r.execution_generation_id,
            source_generation_id=r.source_generation_id,
            supporting_admission_ids=(current.admission_id, prior.admission_id),
            supporting_admission_sha256=(current.admission_sha256, prior.admission_sha256),
            source_owner_sha256=self._owner_sha,
            factual_direction={"higher":"UP", "lower":"DOWN", "unchanged":"FLAT"}[match["direction"]],
            delta=match["delta"], growth_pct=match["growth_pct"])
        result = ReportedPolicyResult(**body, interpretation_sha256=digest(dict(policy=POLICY, **body)))
        self._interpretations[result.interpretation_sha256] = result.model_dump_json()
        return result

    def verify_interpretation(self, result: ReportedPolicyResult):
        if self._interpretations.get(result.interpretation_sha256) != result.model_dump_json():
            raise ValueError("UNISSUED_OR_CHANGED_INTERPRETATION")
        for ref in result.supporting_admission_ids:
            if ref not in self._admitted:
                raise ValueError("INTERPRETATION_FACT_OWNER_MISSING")
        return result

    def authorize_interpretation(self, result, *, axis, security_id, execution_generation_id,
                                 source_generation_id):
        result = self.verify_interpretation(result)
        facts = []
        for ref in result.supporting_admission_ids:
            admission = FactAdmission.model_validate_json(self._admitted[ref])
            facts.append(self.resolve(admission, axis=axis, security_id=security_id,
                execution_generation_id=execution_generation_id, source_generation_id=source_generation_id))
        if axis.endswith("DIRECTION") and not result.permitted_core_roles:
            raise ValueError("ECONOMIC_ROLE_POLICY_AUTHORITY_GAP")
        return tuple(facts)
