"""Offline unavailable-fPER applicability, not a NewBuyer decision path."""
import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.kis_fy1_semantic_owner import SemanticGap
from scripts.kis_no_estimate_owner import validate_assessment

CONTRACT = "CurrentFY1FperPrerequisiteScopeV1"
REQUIREMENT = "newbuyer-unavailable-fper-category-requirements-v2"
PROOF = "CurrentFY1FperEarlyReturnDataflowProofV1"
PREFIX_SHA = "813d5ab617f4977f4578e86ff3e072e6817f84335abd6c1937a411691fc1d484"
CATEGORIES = (
    "SECURITY_IDENTITY", "SECURITY_CLASS_OR_LISTING", "PRICE_TO_SECURITY_BINDING",
    "VALUATION_SECURITY_BASIS", "VALUATION_CURRENCY_BASIS", "SHARE_OR_DENOMINATOR_BASIS",
    "DEPOSITARY_OR_ADR_CONVERSION", "VALUATION_HORIZON_OR_PERIOD",
    "PROVIDER_SECURITY_BINDING", "VALUATION_SOURCE_QUALITY", "BUSINESS_SOURCE_QUALITY",
)
REQUIRED = {
    "SECURITY_IDENTITY": "REQUEST_SECURITY_BINDING_ONLY_NO_RETURNED_ESTIMATE_IDENTITY",
    "PROVIDER_SECURITY_BINDING": "EXACT_REQUEST_RESPONSE_BINDING_ONLY_NO_POSITIVE_SECURITY_SNAPSHOT",
    "VALUATION_SOURCE_QUALITY": "OBSERVED_NORMAL_EMPTY_FIELD_ELIGIBILITY_ONLY",
}


def nonconsumption_proof():
    """Fail closed if the reviewed pre-return dataflow changes, including added calls."""
    path = Path(__file__).with_name("kis_current_fy1_owner.py")
    source = path.read_bytes()
    function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "current_fper")
    prefix = ast.Module(body=function.body[:2], type_ignores=[])
    fingerprint = sha256(ast.dump(prefix, include_attributes=False).encode()).hexdigest()
    if fingerprint != PREFIX_SHA or [a.arg for a in function.args.args] != ["eps", "price", "actions"]:
        raise SemanticGap("SHORT_CIRCUIT_DATAFLOW_CHANGED")
    # The exact reviewed prefix reads only EPS.state and static display metadata.
    # The return's sealing helper is also bound, not assumed side-effect-free.
    helper = Path(__file__).with_name("kis_eps_wire_calibration.py")
    nodes = {n.name: n for n in ast.parse(helper.read_bytes()).body if isinstance(n, ast.FunctionDef)}
    expected = ast.parse('def sealed(value):\n return {**value, "receipt_sha256": digest(value)}\n').body[0]
    if ast.dump(nodes["sealed"], include_attributes=False) != ast.dump(expected, include_attributes=False):
        raise SemanticGap("SHORT_CIRCUIT_SEAL_HELPER_CHANGED")
    return sealed(dict(contract=PROOF, producer_path="scripts/kis_current_fy1_owner.py",
        producer_symbol="current_fper", producer_source_sha256=sha256(source).hexdigest(),
        prefix_ast_sha256=fingerprint, helper_source_sha256=sha256(helper.read_bytes()).hexdigest(),
        line_start=function.lineno, line_end=function.body[1].end_lineno,
        assessed_input_fields=["eps.state"], consumed_value_inputs=[],
        non_consumed_inputs=["price", "actions", "eps.value", "eps.security", "eps.period", "eps.unit", "eps.estdate"],
        branch_result="UNAVAILABLE_EPS", positive_non_consumption_proof=True,
        current_qualified_or_denied_state_owned=False))


def prerequisite_scope(assessment, *, evidence_inputs, old_eps, old_fper):
    validate_assessment(assessment, **evidence_inputs)
    if (assessment["field_decision"] != "NO_RESEARCH_ESTIMATE_AT_RETRIEVAL"
            or not assessment["normal_empty_confirmed"] or not assessment["owner_complete"]
            or old_eps != {"state": "UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE", "value": None}):
        raise SemanticGap("SHORT_CIRCUIT_PREREQUISITE_NOT_OWNED")
    proof = nonconsumption_proof()
    from scripts.kis_current_fy1_owner import current_fper
    if old_fper != current_fper(old_eps, None, None):
        raise SemanticGap("SHORT_CIRCUIT_OLD_FPER_REPRODUCTION_GAP")
    rows = []
    for category in CATEGORIES:
        required = category in REQUIRED
        rows.append(dict(category=category, metric="CURRENT_FY1_FPER",
            prerequisite="KIS_RESEARCH_ESTIMATE_AVAILABLE", prerequisite_owner_ref=assessment["receipt_sha256"],
            prerequisite_decision=assessment["field_decision"], required_on_this_path=required,
            proof_type="CURRENT_TYPED_OWNER" if required else "PRODUCER_SEMANTICS",
            producer_path=proof["producer_path"], producer_symbol=proof["producer_symbol"],
            positive_non_consumption_proof=None if required else proof["receipt_sha256"],
            category_semantics=REQUIRED.get(category, "NOT_CONSUMED_ON_THIS_UNAVAILABLE_METRIC_PATH"),
            reason_code="TYPED_NEGATIVE_OBSERVATION_REQUIRED" if required else "PROVEN_EPS_PREREQUISITE_SHORT_CIRCUIT",
            scope="THIS_UNAVAILABLE_CURRENT_FY1_FPER_ONLY", positive_estimate_identity_granted=False))
    return sealed(dict(contract=CONTRACT, category_requirement_contract=REQUIREMENT,
        security_code=assessment["security_code"], canonical_security_id=assessment["canonical_security_id"],
        source_generation=assessment["source_generation"], prerequisite_owner_ref=assessment["receipt_sha256"],
        old_eps_sha256=digest(old_eps), old_fper_sha256=digest(old_fper), dataflow_proof=proof,
        categories=rows, producer_semantics_current_state_allowed=False, valuation_state_owned=False,
        all_other_paths_unchanged=True))


def validate_scope(scope, assessment, **inputs):
    verified(scope, CONTRACT)
    if scope != prerequisite_scope(assessment, **inputs):
        raise SemanticGap("SHORT_CIRCUIT_SCOPE_REPRODUCTION_GAP")


def apply_to_coverage(previous, assessment, scope, **inputs):
    """Only unresolved cells on the owned unavailable metric may change."""
    verified(previous, previous["contract"])
    validate_scope(scope, assessment, **inputs)
    if (previous["ticker"] != assessment["security_code"]
            or previous["source_generation"] != assessment["source_generation"]
            or previous["canonical_security_id"] != assessment["canonical_security_id"]):
        raise SemanticGap("COVERAGE_PREREQUISITE_IDENTITY_GAP")
    row = deepcopy(previous)
    changed = []
    requirements = {r["category"]: r for r in scope["categories"]}
    targets = [c for c in row["categories"] if c["metric"] == "CURRENT_FY1_FPER"]
    if len(targets) != len(CATEGORIES) or {c["category"] for c in targets} != set(CATEGORIES):
        raise SemanticGap("COVERAGE_CATEGORY_UNIVERSE_GAP")
    for cell in targets:
        if cell["coverage_disposition"] != "UNRESOLVED":
            continue
        before = deepcopy(cell)
        req = requirements[cell["category"]]
        required = req["required_on_this_path"]
        ref = cell["metric_ref"]
        cell.update(required=required, required_for_metric_refs=[ref] if required else [],
            requirement_owner_contract=REQUIREMENT, requirement_proof_kind=req["proof_type"],
            requirement_reason=req["category_semantics"], category_requirement_basis=req["category_semantics"],
            category_semantics=req["category_semantics"], requirement_scope_ref=scope["receipt_sha256"],
            owner_state="DENIED" if cell["category"] == "VALUATION_SOURCE_QUALITY" else "QUALIFIED",
            owner_contract=assessment["contract"], owner_ref=assessment["receipt_sha256"],
            owner_decision_version=assessment["decision_version"],
            owner_field_eligibility=dict(field_eligibility=assessment["field_eligibility"],
                category_semantics=req["category_semantics"], positive_returned_identity=False),
            owner_as_of=assessment["observation_time"], owner_effective_at=None,
            owner_temporal_scope=assessment["temporal_scope"] + ": " + assessment["field_effective_time_disposition"],
            applies_to_metric_refs=[ref] if required else [],
            input_refs=[assessment["receipt_sha256"], assessment["source_receipt_sha256"],
                assessment["raw_sha256"], scope["receipt_sha256"]], input_sha256=digest(assessment),
            coverage_disposition="PROVEN_APPLICABLE", coverage_proof_kind="COMPOSED_TYPED_OWNER",
            missing_fields=[], denial_reason_codes=[], qualification_reason_codes=[],
            not_applicable_to_metric_refs=[], not_applicable_reason_codes=[])
        cell.pop("limitation", None)
        if required:
            key = "denial_reason_codes" if cell["owner_state"] == "DENIED" else "qualification_reason_codes"
            cell[key] = [assessment["decision_reason_code"] if cell["owner_state"] == "DENIED" else req["category_semantics"]]
        else:
            cell.update(owner_state=None, coverage_disposition="PROVEN_NOT_APPLICABLE",
                coverage_proof_kind="PRODUCER_SEMANTICS", owner_contract=CONTRACT,
                owner_ref=scope["receipt_sha256"], owner_decision_version=REQUIREMENT,
                owner_field_eligibility={"semantic_domain_consumed": False},
                owner_as_of=None, owner_temporal_scope="STATIC_NONCONSUMPTION_PLUS_DATED_PREREQUISITE",
                not_applicable_to_metric_refs=[ref], not_applicable_reason_codes=[req["reason_code"]],
                input_refs=[scope["receipt_sha256"], req["positive_non_consumption_proof"], assessment["receipt_sha256"]])
        changed.append(dict(ticker=row["ticker"], metric_ref=ref, category=cell["category"],
            before=before, after=deepcopy(cell), new_owner_ref=cell["owner_ref"],
            why=req["category_semantics"], prerequisite_owner_ref=assessment["receipt_sha256"]))
    unresolved = [c for c in row["categories"] if c["coverage_disposition"] == "UNRESOLVED"]
    row.update(coverage_complete=not unresolved, coverage_incomplete_reasons=unresolved,
        owner_provenance_complete=not unresolved, temporal_provenance_complete=not unresolved,
        decision_provenance_complete=not unresolved, requirement_extension=REQUIREMENT,
        receipt_ref="availability-overlay:"+assessment["receipt_sha256"],
        denied_relevant_valuation_refs=sorted({c["metric_ref"] for c in row["categories"]
            if c["category"] == "VALUATION_SOURCE_QUALITY" and c["owner_state"] == "DENIED"}),
        current_newbuyer_blocker_refs=None, global_valuation_blocker_refs=None)
    row.pop("receipt_sha256")
    return sealed(row), changed


def blocker_census(rows, *, expected_subjects):
    """Offline census, not stance/veto entitlement. Do not infer blockers from gaps."""
    if (not rows or len({r["ticker"] for r in rows}) != len(rows)
            or {r["ticker"] for r in rows} != set(expected_subjects)):
        raise SemanticGap("BLOCKER_CENSUS_COHORT_GAP")
    grouped = {}
    for row in rows:
        verified(row, row["contract"])
        if (not all(row[k] for k in ("coverage_complete", "owner_provenance_complete",
                "temporal_provenance_complete", "decision_provenance_complete"))
                or any(c["coverage_disposition"] == "UNRESOLVED" for c in row["categories"])):
            raise SemanticGap("BLOCKER_CENSUS_COVERAGE_INCOMPLETE")
        for cell in row["categories"]:
            if cell["owner_state"] != "DENIED":
                continue
            if (cell["coverage_disposition"] != "PROVEN_APPLICABLE"
                    or cell["coverage_proof_kind"] == "PRODUCER_SEMANTICS"
                    or cell["missing_fields"] or not cell["denial_reason_codes"]
                    or not all(cell.get(k) for k in ("owner_ref", "owner_contract", "owner_decision_version",
                        "owner_field_eligibility", "owner_as_of", "owner_temporal_scope", "input_refs"))):
                raise SemanticGap("BLOCKER_CENSUS_DENIAL_PROVENANCE_GAP")
            # Deduplicate repeated categories of the exact same denial owner;
            # independently owned metrics/reasons are not guessed equivalent.
            key = digest([row["ticker"], cell["owner_contract"], cell["owner_ref"],
                          cell["scope_level"], sorted(cell["denial_reason_codes"]), cell["input_sha256"]])
            if key not in grouped:
                grouped[key] = dict(blocker_ref="typed-blocker:"+key, blocker_class="CURRENT_OWNER_ELIGIBILITY_DENIAL",
                    ticker=row["ticker"], canonical_security_id=row["canonical_security_id"],
                    source_generation=row["source_generation"], owner_contract=cell["owner_contract"],
                    owner_ref=cell["owner_ref"], category=[], scope_level=cell["scope_level"],
                    affected_metric_refs=[], reason_codes=sorted(cell["denial_reason_codes"]),
                    input_sha256=cell["input_sha256"], activation="NOT_ENABLED",
                    legacy_entitlement_changed=False, blocks_newbuyer_global_resolution=False)
            item = grouped[key]
            item["category"] = sorted(set(item["category"]) | {cell["category"]})
            item["affected_metric_refs"] = sorted(set(item["affected_metric_refs"]) | set(cell["applies_to_metric_refs"]))
    return sealed(dict(contract="OfflineCurrentOwnerBlockerCensusV1", rows=list(grouped.values()),
        current_blocker_count=len(grouped), blocker_census_complete=True,
        coverage_receipt_sha256s=[r["receipt_sha256"] for r in rows], global_blockers_emitted=0,
        legacy_prose_used=False, runtime_enabled=False,
        deduplication="EXACT_OWNER_REASON_SCOPE_INPUT; no guessed cross-owner equivalence"))
